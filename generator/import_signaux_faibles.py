#!/usr/bin/env python3
"""
import_signaux_faibles.py — Ourrassol 2098
===========================================

Lit TOUTES les réponses de veille "signaux faibles" rangées dans
documentation/need_action/veille_signaux_reponses/ (une par IA interrogée
avec le prompt d'export_prompt_signaux.py), les FUSIONNE en une seule liste
de candidats, et l'enregistre pour le tri (injecter / écarter).

AUCUN APPEL API — script 100% local, symétrique d'export_prompt_signaux.py.
Ne touche JAMAIS au vault (signaux_custom/, instances…) : l'injection
d'un signal retenu reste une étape séparée (idees_vers_queue.py puis
inject_custom_signals.py), déclenchée par David depuis le tri.

FICHIERS D'ENTRÉE
-----------------
    veille_signaux_reponses/veille_signaux_reponse_<ia>.md
Le suffixe <ia> (claude, chatgpt, mistral…) sert de provenance. Un fichier
sans suffixe reconnaissable garde son nom complet comme provenance.

PARSING TOLÉRANT
----------------
Les IA ne respectent jamais le format à 100 %. Sont acceptés :
  - blocs de code ``` autour de la réponse, texte avant le premier bloc ;
  - clés en gras (**titre** :), en puces (- titre:), accentuées (nouveauté),
    en majuscules ;
  - « ### Signal 3 », « ## SIGNAL 3 », « ### SIGNAL 3 — titre » ;
  - notes écrites « 4/5 » ou « 4 (fort) » ;
  - ancien format « variables: a, b, c » (la 1re devient la principale) ;
  - sources en liste à puces, en liens markdown [texte](url) ou URL nues ;
  - « ### FIN » absent (avertissement, pas bloquant).
Un bloc sans titre ou sans aucune variable valide est rejeté avec motif.

FUSION (décision David 28 sept 2026 : option « a », fusion automatique,
validée ensuite dans l'onglet de tri)
------------------------------------------------------------------------
Deux signaux (d'IA différentes ou non) sont considérés comme le même si :
  - ils partagent au moins une URL de source (hors pages d'accueil nues,
    trop génériques : https://synthmedia.fr/ ne prouve rien), OU
  - leurs titres se ressemblent assez (mots significatifs communs).
Les regroupements sont transitifs. Le signal fusionné garde :
  - la description la plus complète (la plus longue) comme texte principal ;
  - la variable principale majoritaire (égalité → celle du texte principal) ;
  - l'union des sources et des variables secondaires ;
  - les notes de chaque IA ET leur moyenne ;
  - toutes les variantes d'origine (pour pouvoir défaire une fusion
    erronée dans le tri).
Un signal trouvé indépendamment par plusieurs IA est marqué « convergent ».

SORTIES
-------
  state/veille_signaux.json               candidats (statut « a_trier »),
                                          lots précédents conservés
  documentation/need_action/veille_signaux_fusion.md   rapport lisible
Après un import réel, les réponses sont archivées dans
veille_signaux_reponses/archive/<horodatage>/ (évite un double import).

USAGE
-----
    python3 import_signaux_faibles.py --dry-run     # aperçu, rien écrit
    python3 import_signaux_faibles.py               # écriture réelle
    python3 import_signaux_faibles.py --force       # accepte des réponses
                                                    # qui ne sont pas du jour
    python3 import_signaux_faibles.py --seuil-titre 0.5
"""

import argparse
import json
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path
from statistics import mean
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from export_prompt_veille import VARIABLES, format_date_fr, load_sub_variables
from export_prompt_signaux import (HORS_VARIABLES, regles_couverture,
                                   charger_signaux_existants)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
REPONSES_DIR = NEED_ACTION_DIR / "veille_signaux_reponses"
ARCHIVE_DIR = REPONSES_DIR / "archive"
RAPPORT_PATH = NEED_ACTION_DIR / "veille_signaux_fusion.md"

# Même dossier state/ que les autres caches du pipeline : on prend celui
# qui existe (racine du vault ou generator/), la racine par défaut.
_STATE_CANDIDATS = [VAULT_ROOT / "state", GENERATOR_DIR / "state"]
STATE_DIR = next((d for d in _STATE_CANDIDATS if d.is_dir()), _STATE_CANDIDATS[0])
CANDIDATS_PATH = STATE_DIR / "veille_signaux.json"

PREFIXE_FICHIER = "veille_signaux_reponse_"
SEUIL_TITRE_DEFAUT = 0.5
VARIABLES_VALIDES = set(VARIABLES) | {HORS_VARIABLES}


def _table_sous_variables() -> dict:
    """
    Sous-variable → variable parente, lue dans variables/*.md.
    Constat du 28 sept 2026 (3 vraies réponses) : DeepSeek et Mistral
    utilisent des sous-variables comme identifiants (biodiversite_effondrement,
    matieres_premieres_critiques, relations_nord_sud…). Chaque sous-variable
    n'a qu'un parent : on la rattache au lieu de rejeter le signal.
    """
    table = {}
    for parent in VARIABLES:
        for nom, _ in load_sub_variables(parent):
            table.setdefault(nom.strip().lower(), parent)
    return table


SOUS_VARIABLES = _table_sous_variables()


def rattacher(ident: str):
    """Renvoie (variable, sous_variable_d_origine_ou_None)."""
    if ident in VARIABLES_VALIDES:
        return ident, None
    if ident in SOUS_VARIABLES:
        return SOUS_VARIABLES[ident], ident
    return ident, None

MOTS_VIDES = set("""
le la les l un une des de du d et ou en au aux a à dans par pour sur avec sans
son sa ses leur leurs ce cet cette ces qui que quoi dont est sont se s
the of and or in on to for with by an as at from is are its
premier premiere première first new nouveau nouvelle
""".split())

# Clés reconnues → nom canonique. Comparaison sur la forme normalisée
# (minuscules, sans accents, espaces/tirets → _).
ALIAS_CLES = {
    "titre": "titre", "title": "titre",
    "description": "description",
    "observe_le": "observe_le", "observe": "observe_le", "date": "observe_le",
    "lieu": "lieu", "localisation": "lieu",
    "nature": "nature", "type": "nature",
    "variable_principale": "variable_principale",
    "variables_secondaires": "variables_secondaires",
    "variables": "variables",  # ancien format
    "moteur_numerique": "moteur_numerique",
    "pertinence": "pertinence",
    "nouveaute": "nouveaute",
    "impact": "impact",
    "justification": "justification",
    "sources": "sources",
    # Variantes rencontrées en conditions réelles (Gemini, 28 sept 2026) :
    # noms de champs inventés par l'IA au lieu de ceux du prompt.
    "source": "sources", "liens": "sources", "urls": "sources", "url": "sources",
    "date_information": "observe_le", "date_observation": "observe_le",
    "moteur_ia_numerique": "moteur_numerique", "moteur_ia": "moteur_numerique",
    "pourquoi_signal_faible": "pourquoi", "resume": "resume",
    "note_pertinence": "pertinence", "note_nouveaute": "nouveaute", "note_impact": "impact",
}
NOTES = ("pertinence", "nouveaute", "impact")


# ---------------------------------------------------------------------------
# Utilitaires texte
# ---------------------------------------------------------------------------

def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte)
                   if unicodedata.category(c) != "Mn")


def norm_cle(cle: str) -> str:
    cle = sans_accents(cle.strip().strip("*_`").strip()).lower()
    return re.sub(r"[\s\-]+", "_", cle)


def mots_significatifs(titre: str) -> set:
    t = sans_accents(titre.lower())
    mots = re.findall(r"[a-z0-9]+", t)
    return {m for m in mots if len(m) > 2 and m not in MOTS_VIDES}


def similarite_titres(a: str, b: str) -> float:
    """Part de mots significatifs communs, rapportée au plus petit titre."""
    ma, mb = mots_significatifs(a), mots_significatifs(b)
    if not ma or not mb:
        return 0.0
    return len(ma & mb) / min(len(ma), len(mb))


URL_RE = re.compile(r"https?://[^\s<>\")\]]+")
# Source tirée d'un extrait de livre fourni en annexe du prompt
# (« - livre: Titre, p. 52 », 28 sept 2026). Stockée comme une source dont
# l'« url » commence par « livre: » : affichée en texte dans le GUI, jamais
# testée en HTTP, jamais utilisée pour rapprocher deux signaux.
LIVRE_RE = re.compile(r"^\s*[-*•]?\s*\**\s*livre\s*\**\s*[:：]\s*(.+?)\s*$", re.I)


def est_source_livre(url: str) -> bool:
    return url.lower().startswith("livre:")


def norm_url(url: str) -> str:
    u = url.strip().rstrip(".,;:)»")
    u = re.sub(r"^https?://", "", u, flags=re.I)
    u = re.sub(r"^(www\.|m\.)", "", u, flags=re.I)
    u = re.sub(r"[?#].*$", "", u)
    return u.rstrip("/").lower()


def url_significative(url_norm: str) -> bool:
    """Une page d'accueil nue (domaine seul) ne prouve pas un doublon ; une
    référence de livre non plus (deux signaux du même chapitre)."""
    return "/" in url_norm and not est_source_livre(url_norm)


def slugifier(texte: str, longueur: int = 60) -> str:
    s = sans_accents(texte.lower())
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:longueur].rstrip("_")


# ---------------------------------------------------------------------------
# Parsing d'une réponse
# ---------------------------------------------------------------------------

def ia_depuis_nom(path: Path) -> str:
    stem = path.stem
    if stem.startswith(PREFIXE_FICHIER) and len(stem) > len(PREFIXE_FICHIER):
        return stem[len(PREFIXE_FICHIER):]
    return stem


IA_LIGNE_RE = re.compile(r"^\s*[-*]?\s*\**\s*ia\s*\**\s*:\s*\**\s*([^\n*]+?)\s*\**\s*$",
                         re.I | re.M)


def ia_depuis_contenu(texte: str):
    """
    Provenance déclarée par l'IA elle-même (ligne « ia: <nom> » demandée en
    tête de réponse, 28 sept 2026) -- cherchée seulement AVANT le premier
    bloc ### SIGNAL, pour ne jamais confondre avec un champ d'un signal.
    None si absente. Normalisée : minuscules, sans accent, _ à la place
    des espaces (« Le Chat » → le_chat).
    """
    m_bloc = ENTETE_SIGNAL_RE.search(texte)
    entete = texte[:m_bloc.start()] if m_bloc else texte[:500]
    m = IA_LIGNE_RE.search(entete)
    if not m:
        return None
    nom = re.sub(r"[^a-z0-9]+", "_", sans_accents(m.group(1).strip().lower())).strip("_")
    return nom or None


CONSULT_RE = re.compile(r"^\s*#{2,4}\s*sources?\s+consult[ée]es?\b[^\n]*$", re.I | re.M)


def parser_consultation(texte: str) -> list:
    """
    Lignes du bloc « ### SOURCES CONSULTÉES » (jusqu'à ### FIN ou la fin).
    Renvoie [{"texte": ligne, "statut": consultee|inaccessible|non_consultee|inconnu}].
    """
    m = CONSULT_RE.search(texte)
    if not m:
        return []
    reste = texte[m.end():]
    fin = FIN_RE.search(reste)
    bloc = reste[:fin.start()] if fin else reste
    res = []
    for ligne in bloc.splitlines():
        l = ligne.strip().lstrip("-*• ").strip()
        if not l:
            continue
        n = sans_accents(l.lower())
        if any(k in n for k in ("inaccessible", "bloque", "payant", "abonnement",
                                "paywall", "introuvable", "erreur")):
            statut = "inaccessible"
        elif "non consult" in n or "pas consult" in n:
            statut = "non_consultee"
        elif "consult" in n:
            statut = "consultee"
        else:
            statut = "inconnu"
        res.append({"texte": l, "statut": statut})
    return res


def rattacher_consultation(consult_par_ia: dict, sources: list) -> list:
    """
    Pour chaque source de départ (sources_signaux_faibles.yaml), le statut
    déclaré par chaque IA. Rattachement d'une ligne à une source par son
    nom (début) ou son domaine. Renvoie [{"nom", "url", "par_ia": {ia: statut}}].
    """
    def dom(url):
        return re.sub(r"^(www\.)", "", norm_url(url).split("/")[0])
    tableau = []
    for s in sources:
        nom = sans_accents((s.get("nom") or "").lower())
        cle_nom = re.split(r"[—(\-]", nom)[0].strip()
        d = dom(s["url"])
        par_ia = {}
        for ia, lignes in consult_par_ia.items():
            for l in lignes:
                t = sans_accents(l["texte"].lower())
                if (cle_nom and len(cle_nom) >= 3 and cle_nom in t) or (d and d in t):
                    par_ia[ia] = l["statut"]
                    break
        tableau.append({"nom": s.get("nom", s["url"]), "url": s["url"], "par_ia": par_ia})
    return tableau


ENTETE_SIGNAL_RE = re.compile(r"^\s*#{2,4}\s*signal\b[^\n]*$", re.I | re.M)
FIN_RE = re.compile(r"^\s*#{2,4}\s*fin\s*$", re.I | re.M)
CLE_VALEUR_RE = re.compile(
    r"^\s*(?:[-*+]\s+)?\**\s*([A-Za-zÀ-ÿ_ \-]{3,30}?)\s*\**\s*:\s*\**\s*(.*)$")


def _note(valeur: str):
    m = re.search(r"[1-5]", valeur or "")
    return int(m.group(0)) if m else None


def _liste_variables(valeur: str) -> list:
    if not valeur:
        return []
    morceaux = re.split(r"[,;/]|\s+et\s+", valeur)
    res = []
    for m in morceaux:
        m = norm_cle(m.strip().strip("[]`*"))
        if m and m not in ("vide", "aucune", "aucun", "none", "-"):
            res.append(m)
    return res


def parser_bloc(texte: str) -> dict:
    champs = {}
    sources = []
    dans_sources = False
    derniere_cle = None
    for ligne in texte.splitlines():
        brut = ligne.strip()
        if not brut or brut.startswith("```"):
            continue
        m = CLE_VALEUR_RE.match(ligne)
        cle = ALIAS_CLES.get(norm_cle(m.group(1))) if m else None
        if cle:
            dans_sources = (cle == "sources")
            derniere_cle = cle
            if cle == "sources":
                ml = LIVRE_RE.match(m.group(2))
                if ml:
                    sources.append((f"livre: {ml.group(1)}", ""))
                else:
                    sources.extend(URL_RE.findall(m.group(2)))
            else:
                champs[cle] = m.group(2).strip().strip("*").strip()
            continue
        if dans_sources:
            ml = LIVRE_RE.match(brut)
            if ml:
                sources.append((f"livre: {ml.group(1)}", ""))
                continue
            for url in URL_RE.findall(brut):
                # Nom du média : ce qui suit l'URL après un tiret, sinon rien.
                reste = brut.split(url, 1)[1]
                nom = re.sub(r"^[\s—–\-:)\]]+", "", reste).strip()
                sources.append((url, nom))
            continue
        # Une ligne « clé : valeur » avec une clé inconnue n'est PAS une
        # continuation du champ précédent (constat Gemini 28 sept 2026 :
        # « date_information : … » se collait au titre) : elle est ignorée.
        if m and re.fullmatch(r"[A-Za-zÀ-ÿ_]{3,30}", m.group(1).strip().strip("*")):
            derniere_cle = None
            continue
        # Ligne de continuation (l'IA a coupé un champ sur plusieurs lignes).
        if derniere_cle and derniere_cle != "sources" and derniere_cle in champs:
            champs[derniere_cle] += " " + brut
    # Normalisation des sources en (url, nom).
    vues, propres = set(), []
    for s in sources:
        url, nom = (s, "") if isinstance(s, str) else s
        url = url.rstrip(".,;:)»")
        cle = norm_url(url)
        if cle in vues:
            continue
        vues.add(cle)
        propres.append({"url": url, "nom": nom})
    champs["sources"] = propres
    return champs


def parser_reponse(texte: str, ia: str):
    """Renvoie (signaux_valides, rejets, avertissements)."""
    avert = []
    fins = list(FIN_RE.finditer(texte))
    if not fins:
        avert.append("ligne « ### FIN » absente (réponse peut-être tronquée)")
        corps = texte
    else:
        # Coupe au DERNIER « ### FIN » et retire les autres (constat du
        # 28 sept 2026 : Gemini met un « ### FIN » après chaque signal -- en
        # coupant au premier, on ne lisait que le premier signal).
        corps = FIN_RE.sub("", texte[:fins[-1].start()])
        if len(fins) > 1:
            avert.append(f"{len(fins)} lignes « ### FIN » (une seule attendue, à la fin) : "
                         "toutes ignorées sauf la dernière")

    # Le bloc « ### SOURCES CONSULTÉES » (compte rendu de consultation des
    # sources de départ, 28 sept 2026) n'appartient à aucun signal : on le
    # retire du corps pour que ses URL ne s'ajoutent pas au dernier signal.
    m_consult = CONSULT_RE.search(corps)
    if m_consult:
        corps = corps[:m_consult.start()]

    entetes = list(ENTETE_SIGNAL_RE.finditer(corps))
    if not entetes:
        return [], [], avert + ["aucun bloc « ### SIGNAL » trouvé"]

    signaux, rejets = [], []
    for i, m in enumerate(entetes):
        fin_bloc = entetes[i + 1].start() if i + 1 < len(entetes) else len(corps)
        c = parser_bloc(corps[m.end():fin_bloc])
        num = i + 1

        # Variables : nouveau format, sinon ancien (« variables: a, b »).
        principale = norm_cle(c.get("variable_principale", "").strip("[]`*"))
        secondaires = _liste_variables(c.get("variables_secondaires", ""))
        if not principale and c.get("variables"):
            anciennes = _liste_variables(c["variables"])
            if anciennes:
                principale, secondaires = anciennes[0], anciennes[1:]
        rattachees = []
        principale, origine = rattacher(principale)
        if origine:
            rattachees.append(f"{origine} → {principale}")
        sec2 = []
        for v in secondaires:
            v2, origine = rattacher(v)
            if origine:
                rattachees.append(f"{origine} → {v2}")
            sec2.append(v2)
        inconnues = [v for v in [principale] + sec2
                     if v and v not in VARIABLES_VALIDES]
        secondaires = []
        for v in sec2:
            if v in VARIABLES_VALIDES and v != principale and v not in secondaires:
                secondaires.append(v)
        secondaires = secondaires[:2]

        motifs = []
        if not c.get("titre"):
            motifs.append("titre absent")
        if principale not in VARIABLES_VALIDES:
            motifs.append(f"variable principale invalide ({principale or 'absente'})")
        if motifs:
            rejets.append({"ia": ia, "numero": num,
                           "titre": c.get("titre", ""), "motifs": motifs})
            continue

        notes = {k: _note(c.get(k, "")) for k in NOTES}
        # Champs de repli quand l'IA a utilisé ses propres noms : résumé si
        # pas de description, « pourquoi signal faible » si pas de justification.
        if not c.get("description") and c.get("resume"):
            c["description"] = c["resume"]
        if not c.get("justification") and c.get("pourquoi"):
            c["justification"] = c["pourquoi"]
        moteur = sans_accents(c.get("moteur_numerique", "")).lower()
        nature = sans_accents(c.get("nature", "")).lower()
        sig = {
            "ia": ia,
            "numero": num,
            "titre": c["titre"],
            "description": c.get("description", ""),
            "observe_le": c.get("observe_le", ""),
            "lieu": c.get("lieu", ""),
            "nature": "evenement" if "even" in nature else "signal",
            "variable_principale": principale,
            "variables_secondaires": secondaires,
            "moteur_numerique": (True if moteur.startswith("oui")
                                 else False if moteur.startswith("non")
                                 else None),
            "notes": notes,
            "justification": c.get("justification", ""),
            "sources": c["sources"],
        }
        a = []
        if rattachees:
            a.append("sous-variables rattachées à leur parent : " + ", ".join(rattachees))
        if inconnues:
            a.append("variables inconnues ignorées : " + ", ".join(inconnues))
        manq = [k for k, v in notes.items() if v is None]
        if len(manq) == len(NOTES):
            a.append("aucune note (pertinence/nouveauté/impact) : score 0, à évaluer toi-même")
        elif manq:
            a.append("note(s) illisible(s) : " + ", ".join(manq))
        if not c["sources"]:
            a.append("aucune URL de source")
        if sig["moteur_numerique"] is None:
            a.append("moteur_numerique absent")
        sig["avertissements"] = a
        signaux.append(sig)
    return signaux, rejets, avert


# ---------------------------------------------------------------------------
# Fusion
# ---------------------------------------------------------------------------

def regrouper(signaux: list, seuil_titre: float) -> list:
    """Union-find : renvoie une liste de groupes (listes d'indices)."""
    parent = list(range(len(signaux)))

    def racine(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def unir(i, j):
        ri, rj = racine(i), racine(j)
        if ri != rj:
            parent[rj] = ri

    urls = [{norm_url(s["url"]) for s in sig["sources"]} for sig in signaux]
    urls = [{u for u in us if url_significative(u)} for us in urls]
    for i in range(len(signaux)):
        for j in range(i + 1, len(signaux)):
            if urls[i] & urls[j]:
                unir(i, j)
            elif similarite_titres(signaux[i]["titre"], signaux[j]["titre"]) >= seuil_titre:
                unir(i, j)

    groupes = {}
    for i in range(len(signaux)):
        groupes.setdefault(racine(i), []).append(i)
    return list(groupes.values())


def _majoritaire(valeurs: list, defaut):
    compte = {}
    for v in valeurs:
        compte[v] = compte.get(v, 0) + 1
    if not compte:
        return defaut
    meilleur = max(compte.values())
    gagnants = [v for v, n in compte.items() if n == meilleur]
    return defaut if defaut in gagnants else gagnants[0]


def fusionner(groupe: list) -> dict:
    ref = max(groupe, key=lambda s: len(s["description"]))
    principale = _majoritaire([s["variable_principale"] for s in groupe],
                              ref["variable_principale"])
    secondaires = []
    for s in groupe:
        for v in [s["variable_principale"]] + s["variables_secondaires"]:
            if v != principale and v not in secondaires and v != HORS_VARIABLES:
                secondaires.append(v)
    moteurs = [s["moteur_numerique"] for s in groupe if s["moteur_numerique"] is not None]
    # Égalité oui/non → oui : mieux vaut compter un signal numérique de trop
    # dans le contrôle de couverture que de le laisser passer.
    moteur = (sum(moteurs) * 2 >= len(moteurs)) if moteurs else None

    sources, vues = [], set()
    for s in groupe:
        for src in s["sources"]:
            k = norm_url(src["url"])
            if k not in vues:
                vues.add(k)
                sources.append(src)

    notes_par_ia = {f'{s["ia"]}#{s["numero"]}': s["notes"] for s in groupe}
    moyennes = {}
    for k in NOTES:
        vals = [s["notes"][k] for s in groupe if s["notes"][k] is not None]
        moyennes[k] = round(mean(vals), 1) if vals else None

    ias = sorted({s["ia"] for s in groupe})
    return {
        "titre": ref["titre"],
        "description": ref["description"],
        "observe_le": ref["observe_le"],
        "lieu": ref["lieu"],
        "nature": _majoritaire([s["nature"] for s in groupe], ref["nature"]),
        "variable_principale": principale,
        "variables_secondaires": secondaires,
        "moteur_numerique": moteur,
        "notes": moyennes,
        "notes_par_ia": notes_par_ia,
        "justification": ref["justification"],
        "sources": sources,
        "trouve_par": ias,
        "convergent": len(ias) > 1,
        "fusionne": len(groupe) > 1,
        "variantes": groupe,
        "avertissements": sorted({
            a for s in groupe for a in s["avertissements"]
            # Inutile de signaler un moteur absent chez une IA si une autre l'a donné.
            if not (a == "moteur_numerique absent" and moteur is not None)}),
    }


def racines(texte: str) -> set:
    """Mots significatifs réduits à 5 lettres (décode/décodage/décodé → decod)."""
    return {m[:5] for m in mots_significatifs(texte)}


SEUIL_DEJA_INJECTE = 0.4


def deja_injectes(candidat: dict, existants: list) -> list:
    """
    Signaux de signaux_custom/ qui ressemblent au candidat. Constat du
    28 sept 2026 : DeepSeek a reproposé le décodage du langage des oiseaux,
    déjà injecté (decodage_langage_animaux_ia), malgré la consigne du prompt.
    Signalement seulement : le tri reste humain. Part des racines du signal
    existant (slug + résumé) retrouvées dans le titre + la description.
    """
    texte = racines(candidat["titre"] + " " + candidat["description"])
    proches = []
    for slug, resume in existants:
        r = racines(slug.replace("_", " ") + " " + resume)
        if r and len(r & texte) / len(r) >= SEUIL_DEJA_INJECTE:
            proches.append(slug)
    return proches


def ranger_reponses() -> None:
    """
    Renomme en veille_signaux_reponse_<ia>.md tout fichier de réponse dont la
    ligne « ia: … » indique la provenance mais dont le nom ne correspond pas
    (ex. veille_mistral.md → veille_signaux_reponse_mistral.md), pour qu'il
    apparaisse dans le bon emplacement du GUI (demande David 28 sept 2026).
    Simple renommage, contenu intact -- fait aussi en --dry-run, puisqu'il
    ne change rien à ce qui sera importé. Jamais d'écrasement : si le nom
    cible existe déjà, le fichier garde son nom (avertissement).
    """
    for p in sorted(REPONSES_DIR.glob("*.md")):
        if not p.is_file():
            continue
        try:
            ia = ia_depuis_contenu(p.read_text(encoding="utf-8"))
        except OSError:
            continue
        if not ia:
            continue
        cible = REPONSES_DIR / f"{PREFIXE_FICHIER}{ia}.md"
        if p.name == cible.name:
            continue
        if cible.exists() and cible.read_text(encoding="utf-8").strip():
            print(f"[RANGEMENT] {p.name} (ia: {ia}) garde son nom : {cible.name} existe déjà "
                  "et n'est pas vide (2e réponse de la même IA ?)")
            continue
        if cible.exists():
            cible.unlink()  # emplacement vide laissé par le GUI : on le remplace
        p.rename(cible)
        print(f"[RANGEMENT] {p.name} → {cible.name}")


def charger_candidats_existants():
    """
    Contenu actuel de state/veille_signaux.json. Renvoie (data, erreur) :
    erreur non vide si le fichier existe mais est illisible (on ne rapproche
    alors rien, et l'écriture repartira d'un fichier vide après copie).
    """
    if not CANDIDATS_PATH.exists():
        return {"lots": []}, ""
    try:
        return json.loads(CANDIDATS_PATH.read_text(encoding="utf-8")), ""
    except (json.JSONDecodeError, OSError) as e:
        return {"lots": []}, str(e)


def _urls_candidat(c: dict) -> set:
    return {u for u in (norm_url(s["url"]) for s in c.get("sources", []))
            if url_significative(u)}


def _titres_candidat(c: dict) -> list:
    titres = [c.get("titre", "")]
    titres += [v.get("titre", "") for v in c.get("variantes", [])]
    return [t for t in titres if t]


def _meme_signal(a: dict, b: dict, seuil_titre: float) -> bool:
    """Même règle que la fusion à l'intérieur d'un lot (URL commune ou titres proches)."""
    if _urls_candidat(a) & _urls_candidat(b):
        return True
    return any(similarite_titres(ta, tb) >= seuil_titre
               for ta in _titres_candidat(a) for tb in _titres_candidat(b))


def enrichir_ancien(ancien: dict, nouveau: dict, lot: str) -> None:
    """
    Fusionne un nouveau candidat dans un candidat d'un lot précédent encore
    « à trier » : sources, IA, notes (clés préfixées par le lot pour ne pas
    écraser « claude#3 » d'une veille par « claude#3 » d'une autre),
    variantes. Le texte principal devient le plus complet des deux.
    """
    vues = {norm_url(s["url"]) for s in ancien.get("sources", [])}
    for src in nouveau["sources"]:
        if norm_url(src["url"]) not in vues:
            ancien.setdefault("sources", []).append(src)
            vues.add(norm_url(src["url"]))
    for cle, nt in nouveau["notes_par_ia"].items():
        ancien.setdefault("notes_par_ia", {})[f"{lot}:{cle}"] = nt
    moy = {}
    for k in NOTES:
        vals = [n[k] for n in ancien["notes_par_ia"].values() if n.get(k) is not None]
        moy[k] = round(mean(vals), 1) if vals else None
    ancien["notes"] = moy
    ancien["score"] = score_tri(ancien)
    ias = sorted(set(ancien.get("trouve_par", [])) | set(nouveau["trouve_par"]))
    ancien["trouve_par"] = ias
    ancien["convergent"] = len(ias) > 1
    ancien["fusionne"] = True
    ancien.setdefault("variantes", []).extend(nouveau["variantes"])
    if len(nouveau["description"]) > len(ancien.get("description", "")):
        for k in ("titre", "description", "justification", "observe_le", "lieu"):
            ancien[k] = nouveau[k]
    for v in [nouveau["variable_principale"]] + nouveau["variables_secondaires"]:
        if (v != ancien.get("variable_principale") and v != HORS_VARIABLES
                and v not in ancien.setdefault("variables_secondaires", [])):
            ancien["variables_secondaires"].append(v)
    ancien.setdefault("revu_dans_lots", []).append(lot)


MOTIF_ECART_AUTO = "sources introuvables (écart automatique à l'import)"


def rapprocher_lots_precedents(candidats: list, data: dict, seuil_titre: float, lot: str):
    """
    Compare les candidats du nouveau lot à ceux des lots précédents (décision
    David 28 sept 2026 : les candidats s'additionnent d'une veille à l'autre,
    il faut éviter qu'un même signal revienne) :
      - déjà « à trier »  → fusionné dans l'ancien (pas de nouvelle ligne) ;
      - déjà « écarté » ou « en queue » → ignoré (pas de nouvelle ligne).
    Modifie `data` en place (les anciens enrichis). Renvoie
    (candidats_nouveaux, rapprochements) ; rapprochements = liste de
    (action, nouveau_titre, ancien_id, ancien_titre, ancien_statut).
    """
    anciens = [c for l in data.get("lots", []) for c in l.get("candidats", [])]
    gardes, rapp = [], []
    for c in candidats:
        cible = next((a for a in anciens if _meme_signal(c, a, seuil_titre)), None)
        if cible is None:
            gardes.append(c)
            continue
        statut = cible.get("statut", "a_trier")
        if (statut == "ecarte" and cible.get("motif_ecart") == MOTIF_ECART_AUTO
                and not c.get("sources_douteuses")):
            # Écarté seulement faute de source, et retrouvé cette fois avec
            # une source valable : on le remet à trier (réhabilité).
            enrichir_ancien(cible, c, lot)
            cible["statut"] = "a_trier"
            cible.pop("motif_ecart", None)
            cible["sources_douteuses"] = False
            cible["avertissements"] = [a for a in cible.get("avertissements", [])
                                       if not a.startswith("❌")]
            rapp.append(("réhabilité", c["titre"], cible.get("id"), cible.get("titre"), statut))
        elif statut == "a_trier":
            enrichir_ancien(cible, c, lot)
            rapp.append(("fusionné", c["titre"], cible.get("id"), cible.get("titre"), statut))
        else:
            rapp.append(("ignoré", c["titre"], cible.get("id"), cible.get("titre"), statut))
    return gardes, rapp


# ---------------------------------------------------------------------------
# Vérification des sources (option --verifier-sources, 28 sept 2026)
# ---------------------------------------------------------------------------
# Constat : Gemini a livré 10 signaux dont les URL testées renvoyaient 404 --
# signaux vraisemblablement inventés. Chaque URL est testée depuis la machine
# de David (HEAD, puis GET si le site refuse HEAD). Trois verdicts :
#   ok             : la page répond (2xx/3xx) ;
#   introuvable    : 404/410, ou domaine inexistant -- page absente ;
#   non_verifiable : le site bloque les robots (401/403/429), erreur serveur
#                    ou délai dépassé -- ni preuve d'existence ni d'absence.
# Lecture seule, aucune écriture : fonctionne aussi en --dry-run.

TIMEOUT_URL = 8
NAVIGATEUR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def verifier_url(url: str) -> dict:
    if not re.match(r"^https?://", url, re.I):
        return {"verif": "non_verifiable", "detail": "pas une URL web"}
    dernier = None
    for methode in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=methode, headers={
            "User-Agent": NAVIGATEUR, "Accept": "text/html,*/*;q=0.8"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_URL) as r:
                return {"verif": "ok", "detail": str(r.status)}
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return {"verif": "introuvable", "detail": str(e.code)}
            dernier = str(e.code)  # 403/405/429/5xx : on retente en GET
        except urllib.error.URLError as e:
            raison = str(getattr(e, "reason", e))
            if any(k in raison.lower() for k in ("name or service", "nodename", "getaddrinfo",
                                                 "no address", "not known")):
                return {"verif": "introuvable", "detail": "domaine inexistant"}
            dernier = raison[:60]
        except Exception as e:  # délai dépassé, SSL, connexion coupée…
            dernier = type(e).__name__
    return {"verif": "non_verifiable", "detail": dernier or "?"}


def verifier_livre(ref: str, titres: list) -> dict:
    """Une source « livre: Titre, p. N » est valable si le titre correspond à
    un livre actif de sources_signaux_faibles.yaml (celui dont l'extrait
    était dans le prompt). Sinon l'IA a cité un livre qu'on ne lui a pas
    fourni : traité comme une URL introuvable."""
    cite = ref.split(":", 1)[1]
    cite = re.split(r",\s*(?:p\.|pp\.|page|chap)", cite, flags=re.I)[0].strip(" «»\"'")
    for t in titres:
        a, b = sans_accents(cite.lower()), sans_accents(t.lower())
        if a and (a in b or b in a or similarite_titres(cite, t) >= 0.8):
            return {"verif": "ok", "detail": f"livre fourni : {t}"}
    return {"verif": "introuvable", "detail": "livre absent de la liste fournie"}


def titres_livres_actifs() -> list:
    """Titres des livres fournis dans les prompts : ceux du YAML, plus ceux
    du dossier des livres déjà envoyés (mémoire state/livres_veille.json,
    mode « dépose et oublie » : ces livres n'ont pas d'entrée YAML)."""
    titres = []
    try:
        from export_prompt_signaux import charger_sources, SOURCES_PATH, memoire_livres_path
        from livres_veille import charger_memoire
        _, livres = charger_sources(SOURCES_PATH)
        titres = [b["titre"] for b in livres]
        titres += [m["titre"] for m in charger_memoire(memoire_livres_path()).values()
                   if isinstance(m, dict) and m.get("titre")]
    except Exception:
        pass
    return titres


def verifier_sources(candidats: list) -> dict:
    """Teste toutes les URL des candidats (en parallèle, chaque URL une seule
    fois) et annote chaque source + chaque candidat. Renvoie un bilan."""
    toutes = sorted({s["url"] for c in candidats for s in c["sources"]})
    urls = [u for u in toutes if not est_source_livre(u)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        resultats = dict(zip(urls, pool.map(verifier_url, urls)))
    livres = [u for u in toutes if est_source_livre(u)]
    if livres:
        titres = titres_livres_actifs()
        for u in livres:
            resultats[u] = verifier_livre(u, titres)
    bilan = {"ok": 0, "introuvable": 0, "non_verifiable": 0}
    for v in resultats.values():
        bilan[v["verif"]] += 1
    for c in candidats:
        for src in c["sources"]:
            src.update(resultats.get(src["url"], {}))
        verdicts = [s.get("verif") for s in c["sources"]]
        c["sources_verif"] = {k: verdicts.count(k) for k in bilan}
        if not verdicts:
            c["sources_douteuses"] = True
            c["avertissements"].append("❌ aucune source : signal à vérifier avant tout usage")
        elif "ok" not in verdicts and "introuvable" in verdicts:
            c["sources_douteuses"] = True
            c["avertissements"].append("❌ sources introuvables (404) : signal possiblement "
                                       "inventé par l'IA, à vérifier avant tout usage")
        else:
            c["sources_douteuses"] = False
            if all(est_source_livre(s["url"]) for s in c["sources"]):
                c["avertissements"].append("📖 source livre seule : état actuel du "
                                           "phénomène non vérifié en ligne (4e test)")
            if "introuvable" in verdicts:
                c["avertissements"].append("certaines sources introuvables (404)")
            if "ok" not in verdicts:
                c["avertissements"].append("aucune source vérifiable automatiquement "
                                           "(site bloquant les robots) : à ouvrir à la main")
    return bilan


def score_tri(c: dict) -> float:
    n = c["notes"]
    vals = [v for v in (n["pertinence"], n["nouveaute"], n["impact"]) if v is not None]
    return round(mean(vals), 2) if vals else 0.0


# ---------------------------------------------------------------------------
# Contrôle de couverture (informatif)
# ---------------------------------------------------------------------------

def controle_couverture(candidats: list) -> list:
    """
    Règles d'export_prompt_signaux.py appliquées à la liste fusionnée.
    Informatif : rien n'est rejeté, c'est David qui trie. Les règles ont été
    posées pour UNE réponse ; une fusion de plusieurs IA les dépasse
    naturellement (plus de signaux), d'où le calcul sur le total fusionné.
    """
    nb = len(candidats)
    if not nb:
        return []
    max_var, min_vars, max_num = regles_couverture(nb)
    par_var = {}
    for c in candidats:
        par_var[c["variable_principale"]] = par_var.get(c["variable_principale"], 0) + 1
    msgs = []
    trop = {v: n for v, n in par_var.items() if n > max_var and v != HORS_VARIABLES}
    if trop:
        msgs.append("plus de %d signaux sur : %s" % (
            max_var, ", ".join(f"{v} ({n})" for v, n in sorted(trop.items()))))
    couvertes = len([v for v in par_var if v != HORS_VARIABLES])
    if couvertes < min_vars:
        msgs.append(f"{couvertes} variables couvertes (visé : au moins {min_vars})")
    num = sum(1 for c in candidats if c["moteur_numerique"])
    if num > max_num:
        msgs.append(f"{num} signaux à moteur numérique (visé : au plus {max_num})")
    absentes = [v for v in VARIABLES if v not in par_var]
    if absentes:
        msgs.append("variables sans aucun signal : " + ", ".join(absentes))
    return msgs


# ---------------------------------------------------------------------------
# Rapport markdown
# ---------------------------------------------------------------------------

def construire_rapport(date_str, fichiers, candidats, rejets, avert_fichiers,
                       couverture, rapprochements=(), consultation=(), ias_consult=()) -> str:
    L = [f"# Veille signaux faibles — fusion du {date_str}", ""]
    L.append("Réponses lues : " + ", ".join(
        f"{ia} ({n} signaux)" for ia, n in fichiers))
    nb_conv = sum(1 for c in candidats if c["convergent"])
    L.append(f"Candidats après fusion : {len(candidats)}, dont {nb_conv} "
             "trouvé(s) par plusieurs IA.")
    L.append("")
    if couverture:
        L.append("## Couverture")
        for m in couverture:
            L.append(f"- {m}")
        L.append("")
    if avert_fichiers or rejets:
        L.append("## Problèmes de format")
        for ia, a in avert_fichiers:
            L.append(f"- {ia} : {a}")
        for r in rejets:
            L.append(f"- {r['ia']} signal {r['numero']} rejeté "
                     f"({'; '.join(r['motifs'])}) : {r['titre'] or '(sans titre)'}")
        L.append("")
    if consultation and ias_consult:
        icone = {"consultee": "✅", "inaccessible": "🔒", "non_consultee": "—", "inconnu": "?"}
        L.append("## Sources de départ : consultation déclarée par les IA")
        L.append("")
        L.append("| Source | " + " | ".join(ias_consult) + " |")
        L.append("|---|" + "---|" * len(ias_consult))
        for t in consultation:
            cases = [icone.get(t["par_ia"].get(ia), "·") for ia in ias_consult]
            L.append(f"| {t['nom']} | " + " | ".join(cases) + " |")
        L.append("")
        L.append("✅ consultée · 🔒 inaccessible (abonnement, blocage) · — non consultée · "
                 "· non mentionnée · ? statut illisible")
        L.append("")
    if rapprochements:
        L.append("## Déjà vus dans des veilles précédentes")
        for action, t_new, a_id, a_titre, a_statut in rapprochements:
            L.append(f"- {action} : « {t_new} » ≈ {a_id} « {a_titre} » ({a_statut})")
        L.append("")
    L.append("## Nouveaux candidats (classés par note moyenne)")
    L.append("")
    for c in candidats:
        n = c["notes"]
        conv = " — ⭐ convergent" if c["convergent"] else ""
        douteux = " — ❌ sources douteuses" if c.get("sources_douteuses") else ""
        L.append(f"### {c['id']} — {c['titre']}{conv}{douteux}")
        L.append(f"- Trouvé par : {', '.join(c['trouve_par'])}"
                 + (f" (fusion de {len(c['variantes'])} fiches)" if c["fusionne"] else ""))
        L.append(f"- Notes moyennes : pertinence {n['pertinence']}, "
                 f"nouveauté {n['nouveaute']}, impact {n['impact']} "
                 f"(score {c['score']})")
        if c["fusionne"]:
            for cle, nt in c["notes_par_ia"].items():
                L.append(f"    - {cle} : {nt['pertinence']} / {nt['nouveaute']} / {nt['impact']}")
        L.append(f"- Variable principale : {c['variable_principale']}"
                 + (f" ; secondaires : {', '.join(c['variables_secondaires'])}"
                    if c["variables_secondaires"] else ""))
        moteur = {True: "oui", False: "non", None: "?"}[c["moteur_numerique"]]
        L.append(f"- Nature : {c['nature']} ; moteur numérique : {moteur} ; "
                 f"observé : {c['observe_le']} ; lieu : {c['lieu']}")
        L.append("")
        L.append(c["description"])
        L.append("")
        if c["justification"]:
            L.append(f"*Justification :* {c['justification']}")
            L.append("")
        for s in c["sources"]:
            marque = {"ok": "✅ ", "introuvable": "❌ ", "non_verifiable": "❔ "}.get(s.get("verif"), "")
            L.append(f"- {marque}{s['url']}" + (f" — {s['nom']}" if s["nom"] else ""))
        if c["fusionne"]:
            titres = {v["titre"] for v in c["variantes"]}
            if len(titres) > 1:
                L.append("")
                L.append("*Titres fusionnés :* " + " | ".join(sorted(titres)))
        if c.get("proche_de_signal_injecte"):
            L.append("")
            L.append("🔁 Ressemble à un signal déjà injecté : "
                     + ", ".join(c["proche_de_signal_injecte"]))
        if c["avertissements"]:
            L.append("")
            L.append("⚠ " + " ; ".join(c["avertissements"]))
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche le bilan et le rapport sans rien écrire.")
    parser.add_argument("--force", action="store_true",
                        help="Accepte des réponses qui n'ont pas été modifiées aujourd'hui.")
    parser.add_argument("--verifier-sources", action="store_true",
                        help="Teste chaque URL de source (404 = page absente, "
                             "signal possiblement inventé). Lecture seule.")
    parser.add_argument("--seuil-titre", type=float, default=SEUIL_TITRE_DEFAUT,
                        help=f"Part de mots communs pour fusionner deux titres "
                             f"(défaut {SEUIL_TITRE_DEFAUT}).")
    args = parser.parse_args()

    if not REPONSES_DIR.is_dir():
        print(f"[ERREUR] Dossier introuvable : {REPONSES_DIR}")
        print(f"         Crée-le et ranges-y les réponses ({PREFIXE_FICHIER}<ia>.md).")
        return
    ranger_reponses()
    fichiers = sorted(p for p in REPONSES_DIR.glob("*.md") if p.is_file())
    # Fichiers vides ignorés sans erreur : le GUI propose un emplacement fixe
    # par IA (claude, chatgpt, mistral…), on ne remplit que ceux utilisés.
    vides = [p for p in fichiers if not p.read_text(encoding="utf-8").strip()]
    fichiers = [p for p in fichiers if p not in vides]
    if vides:
        print(f"[INFO] {len(vides)} fichier(s) vide(s) ignoré(s) : "
              + ", ".join(ia_depuis_nom(p) for p in vides))
    if not fichiers:
        print(f"[ERREUR] Aucune réponse remplie dans {REPONSES_DIR}")
        return

    now = datetime.now()
    anciens = [p for p in fichiers
               if datetime.fromtimestamp(p.stat().st_mtime).date() != now.date()]
    if anciens and not args.force:
        print("[ARRÊT] Réponse(s) non modifiée(s) aujourd'hui, peut-être oubliée(s) "
              "d'une veille précédente :")
        for p in anciens:
            d = format_date_fr(datetime.fromtimestamp(p.stat().st_mtime))
            print(f"  - {p.name} ({d})")
        print("         Si c'est volontaire, relance avec --force.")
        return

    tous, rejets, avert_fichiers, bilan_fichiers = [], [], [], []
    consult_par_ia = {}
    ias_vues = {}
    for p in fichiers:
        texte = p.read_text(encoding="utf-8")
        # Provenance : la ligne « ia: … » écrite par l'IA prime sur le nom
        # du fichier (qu'une interface peut avoir choisi elle-même).
        ia_nom, ia_texte = ia_depuis_nom(p), ia_depuis_contenu(texte)
        ia = ia_texte or ia_nom
        if not ia_texte:
            avert_fichiers.append((ia, f"ligne « ia: … » absente de {p.name}, "
                                       "provenance tirée du nom du fichier"))
        elif ia_nom != ia_texte and p.stem.startswith(PREFIXE_FICHIER):
            avert_fichiers.append((ia, f"{p.name} déclare « ia: {ia_texte} » : "
                                       "c'est cette provenance qui est retenue"))
        if ia in ias_vues:
            # Deux réponses de la même IA : suffixe pour que leurs notes ne
            # s'écrasent pas (clés « ia#numéro ») si des signaux fusionnent.
            base, k = ia, 2
            while f"{base}_{k}" in ias_vues:
                k += 1
            ia = f"{base}_{k}"
            avert_fichiers.append((ia, f"2e réponse de {base} ({p.name}) : notée {ia}"))
        ias_vues[ia] = p.name
        sigs, rej, av = parser_reponse(texte, ia)
        consult_par_ia[ia] = parser_consultation(texte)
        # La réponse « livres » (veille_livres_api.py) ne consulte pas les
        # sources web de départ : pas de bloc attendu.
        if not consult_par_ia[ia] and not ia.startswith("livres"):
            av.append("bloc « ### SOURCES CONSULTÉES » absent")
        tous.extend(sigs)
        rejets.extend(rej)
        avert_fichiers.extend((ia, a) for a in av)
        bilan_fichiers.append((ia, len(sigs)))

    groupes = regrouper(tous, args.seuil_titre)
    candidats = [fusionner([tous[i] for i in g]) for g in groupes]
    for c in candidats:
        c["score"] = score_tri(c)

    bilan_sources = None
    if args.verifier_sources:
        nb_urls = len({s["url"] for c in candidats for s in c["sources"]})
        print(f"[SOURCES] vérification de {nb_urls} URL…", flush=True)
        bilan_sources = verifier_sources(candidats)

    # Secondes incluses : deux imports dans la même minute ne doivent pas
    # partager un identifiant de lot (ni un dossier d'archive).
    lot = now.strftime("%Y%m%d_%H%M%S")
    existant, erreur_existant = charger_candidats_existants()
    if erreur_existant:
        print(f"[AVERTISSEMENT] {CANDIDATS_PATH.name} illisible ({erreur_existant}) : "
              "pas de rapprochement avec les veilles précédentes.")
    lus = len(candidats)
    candidats, rapprochements = rapprocher_lots_precedents(
        candidats, existant, args.seuil_titre, lot)
    candidats.sort(key=lambda c: (-c["score"], -len(c["trouve_par"]), c["titre"]))
    for k, c in enumerate(candidats, 1):
        c["id"] = f"{lot}_{k:02d}"
        c["slug_propose"] = slugifier(c["titre"])
        c["statut"] = "a_trier"
        c["lot"] = lot
        # Décision David 28 sept 2026 : un candidat sans source ou dont
        # toutes les sources sont introuvables (--verifier-sources) arrive
        # directement « écarté » -- visible via le filtre, récupérable d'un
        # clic (« Remettre à trier »), jamais supprimé.
        if c.get("sources_douteuses"):
            c["statut"] = "ecarte"
            c["motif_ecart"] = MOTIF_ECART_AUTO

    existants = charger_signaux_existants()
    for c in candidats:
        c["proche_de_signal_injecte"] = deja_injectes(c, existants)
    couverture = controle_couverture(candidats)
    try:
        from export_prompt_signaux import charger_sources, SOURCES_PATH
        sources_depart, _ = charger_sources(SOURCES_PATH)
    except Exception:
        sources_depart = []
    consultation = rattacher_consultation(
        {ia: l for ia, l in consult_par_ia.items() if l}, sources_depart)
    date_str = format_date_fr(now)
    rapport = construire_rapport(date_str, bilan_fichiers, candidats, rejets,
                                 avert_fichiers, couverture, rapprochements,
                                 consultation, sorted(ia for ia, l in consult_par_ia.items() if l))

    # ── Bilan console ────────────────────────────────────────────────────
    print(f"[LU] {len(fichiers)} réponse(s) : " +
          ", ".join(f"{ia} ({n})" for ia, n in bilan_fichiers))
    print(f"[FUSION] {len(tous)} signaux lus → {len(candidats)} candidats "
          f"({sum(1 for c in candidats if c['fusionne'])} fusion(s), "
          f"{sum(1 for c in candidats if c['convergent'])} convergent(s) entre IA)")
    if rejets:
        print(f"[AVERTISSEMENT] {len(rejets)} bloc(s) rejeté(s) :")
        for r in rejets:
            print(f"  - {r['ia']} #{r['numero']} : {'; '.join(r['motifs'])}")
    for ia, a in avert_fichiers:
        print(f"[AVERTISSEMENT] {ia} : {a}")
    if rapprochements:
        nf = sum(1 for r in rapprochements if r[0] == "fusionné")
        print(f"[DÉJÀ VUS] {lus} candidats → {len(candidats)} nouveaux ; "
              f"{nf} fusionné(s) dans un candidat encore à trier, "
              f"{sum(1 for r in rapprochements if r[0] == 'réhabilité')} réhabilité(s), "
              f"{sum(1 for r in rapprochements if r[0] == 'ignoré')} ignoré(s) (déjà écarté ou en queue)")
        for action, t_new, a_id, a_titre, a_statut in rapprochements:
            print(f"  - {action} : « {t_new[:55]} » ≈ {a_id} ({a_statut})")
    if bilan_sources:
        print(f"[SOURCES] {bilan_sources['ok']} OK, {bilan_sources['introuvable']} introuvable(s), "
              f"{bilan_sources['non_verifiable']} non vérifiable(s)")
        douteux = [c for c in candidats if c.get("sources_douteuses")]
        if douteux:
            print(f"[ÉCARTÉS AUTO] {len(douteux)} candidat(s) sans source valable, arrivés "
                  "« écartés » (filtre Statut = écarté dans l'onglet 🔭 pour les revoir) :")
        for c in douteux:
            print(f"  - ❌ {c['id']} ({', '.join(c['trouve_par'])}) « {c['titre'][:60]} »")
    if consultation and any(t["par_ia"] for t in consultation):
        lues = [t for t in consultation if "consultee" in t["par_ia"].values()]
        jamais = [t["nom"] for t in consultation if "consultee" not in t["par_ia"].values()]
        print(f"[SOURCES CONSULTÉES] {len(lues)}/{len(consultation)} sources de départ "
              "consultées par au moins une IA" + (" ; jamais consultées : " + ", ".join(jamais)
                                                  if jamais else ""))
    for m in couverture:
        print(f"[COUVERTURE] {m}")
    for c in candidats:
        if c["proche_de_signal_injecte"]:
            print(f"[DÉJÀ INJECTÉ ?] {c['id']} « {c['titre'][:60]} » ≈ "
                  + ", ".join(c["proche_de_signal_injecte"]))

    if args.dry_run:
        print("\n--- Aperçu du rapport ---\n")
        print(rapport)
        print("\n[dry-run] Rien écrit sur disque.")
        return

    # ── Écriture ─────────────────────────────────────────────────────────
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if CANDIDATS_PATH.exists():
        if erreur_existant:
            bak = CANDIDATS_PATH.with_suffix(".json.illisible.bak")
            shutil.copy2(CANDIDATS_PATH, bak)
            print(f"[AVERTISSEMENT] {CANDIDATS_PATH.name} illisible, copié en {bak.name}, "
                  "repart d'un fichier vide.")
        else:
            shutil.copy2(CANDIDATS_PATH, CANDIDATS_PATH.with_suffix(".json.bak"))
    existant.setdefault("lots", []).append({
        "lot": lot,
        "date": now.isoformat(timespec="seconds"),
        "reponses": [{"ia": ia, "signaux": n} for ia, n in bilan_fichiers],
        "couverture": couverture,
        "rejets": rejets,
        "sources_consultees": consultation,
        "rapprochements": [
            {"action": a, "titre": t, "ancien_id": i, "ancien_titre": at, "ancien_statut": st}
            for a, t, i, at, st in rapprochements],
        "candidats": candidats,
    })
    CANDIDATS_PATH.write_text(json.dumps(existant, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    RAPPORT_PATH.write_text(rapport, encoding="utf-8")

    dest = ARCHIVE_DIR / lot
    dest.mkdir(parents=True, exist_ok=True)
    for p in fichiers:
        shutil.move(str(p), str(dest / p.name))

    print(f"[OK] {len(candidats)} candidats ajoutés (lot {lot}) dans {CANDIDATS_PATH}")
    print(f"[OK] Rapport : {RAPPORT_PATH}")
    print(f"[OK] Réponses archivées dans {dest}")


if __name__ == "__main__":
    main()
