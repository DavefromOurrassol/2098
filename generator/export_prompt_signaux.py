#!/usr/bin/env python3
"""
export_prompt_signaux.py — Ourrassol 2098
==========================================

Génère un prompt prêt à copier-coller dans n'importe quelle IA disposant
d'un accès web (Claude.ai, ChatGPT, Le Chat, etc.), pour repérer des
SIGNAUX FAIBLES réels (concept d'Igor Ansoff) susceptibles d'alimenter le
monde d'Ourrassol 2098.

AUCUN APPEL API — script 100% local, même principe que
export_prompt_veille.py (mode par défaut décidé par David le 28 sept 2026).
Les sources dotées d'un flux RSS (champ « rss ») sont lues par
veille_rss_api.py : depuis le 29 sept 2026, le prompt les signale comme
déjà lues et oriente l'IA vers les autres sources et l'élargissement.
Recherche web par API : essayée le 29 sept 2026 (Mistral), non retenue.

DIFFÉRENCE AVEC export_prompt_veille.py
---------------------------------------
La veille "état du monde" suit les tendances ÉTABLIES et applique un seuil
de matérialité (n'écrire que ce qui a vraiment changé). Ici c'est l'inverse :
on cherche ce qui est encore marginal, précoce, fragmentaire. Tout ce qui
figure déjà dans etat_du_monde_reel.md est donc fourni au LLM comme
"déjà connu, à NE PAS proposer".

CE QUE LE PROMPT CONTIENT
-------------------------
  - la définition d'un signal faible et ce qui n'en est pas un ;
  - les 12 variables d'Ourrassol avec leurs sous-variables officielles
    (pour le rattachement) + la possibilité "hors_variables" ;
  - le "déjà connu" : paragraphes "Situation actuelle" d'etat_du_monde_reel.md
    et signaux déjà injectés (signaux_custom/*.md) ;
  - les sources de départ (sources_signaux_faibles.yaml, actif: true), avec
    la consigne d'élargir à d'autres sources ;
  - les livres déclarés sans fichier (à joindre à la main). Les PDF/EPUB
    du dossier des livres sont lus à part, par API : veille_livres_api.py ;
  - la grille d'évaluation sur 3 axes (pertinence, nouveauté, impact) ;
  - un format de sortie strict, lu par import_signaux_faibles.py (à venir).

USAGE
-----
    python3 export_prompt_signaux.py
    python3 export_prompt_signaux.py --nb 15
    python3 export_prompt_signaux.py --depuis "juillet 2026"
    python3 export_prompt_signaux.py --dry-run      # affiche sans écrire

Fichier produit : documentation/need_action/veille_signaux_prompt_a_copier.md
Réponses (une par IA interrogée, même prompt) à ranger ensuite dans :
                  documentation/need_action/veille_signaux_reponses/
                  veille_signaux_reponse_<ia>.md  (ex. _claude, _chatgpt)
L'import (à venir) fusionne toutes les réponses du dossier.

PRÉREQUIS
---------
    Dans le même dossier : export_prompt_veille.py (fonctions réutilisées)
    et sources_signaux_faibles.yaml.
"""

import argparse
import re
from datetime import datetime
from pathlib import Path

import yaml


# Réutilisation directe (pas de copie) des fonctions déjà testées de la
# veille "état du monde" : liste ordonnée des variables, lecture des
# sous-variables, extraction des paragraphes "Situation actuelle", date FR.
from export_prompt_veille import (
    VARIABLES,
    ETAT_MONDE_PATH,
    SITUATION_HEADING_RE,
    _section_bounds,
    load_sub_variables,
    format_date_fr,
)


def extraire_situation_complete(contenu: str, slug: str):
    """
    Texte COMPLET de la partie « Situation … et mouvements en cours » d'une
    section, jusqu'à la fin de la section (c'est toujours la dernière partie).

    Correctif du 28 sept 2026 : extract_situation() d'export_prompt_veille.py
    s'arrête au premier sous-titre en gras en début de ligne (« **Mouvement
    de fond identifié en 2026** : … ») -- 4 sections perdaient ainsi leur
    « mouvement de fond » (économie, gouvernance, climat, énergie), soit
    jusqu'à 40 % du texte. Le début du paragraphe, lui, n'est pas tronqué :
    il commence en minuscule parce que le titre en gras faisait office de
    début de phrase. Renvoie (texte sur une ligne, date ou None).
    """
    bornes = _section_bounds(contenu, slug)
    if not bornes:
        return None, None
    section = contenu[bornes[0]:bornes[1]]
    m = SITUATION_HEADING_RE.search(section)
    if not m:
        return None, None
    texte = section[m.end():].strip()
    texte = re.sub(r"\n-{3,}\s*$", "", texte).strip()   # séparateur final « --- »
    texte = " ".join(texte.split())
    return (texte or None), m.group("date")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
SOURCES_PATH = GENERATOR_DIR / "sources_signaux_faibles.yaml"
PROMPT_OUTPUT_PATH = NEED_ACTION_DIR / "veille_signaux_prompt_a_copier.md"
# Plusieurs IA peuvent être interrogées avec le même prompt : chaque réponse
# va dans son propre fichier, nommé d'après l'IA (le suffixe sert de
# provenance à l'import, qui fusionne toutes les réponses du dossier).
REPONSES_DIR_REL = "documentation/need_action/veille_signaux_reponses"
REPONSE_MODELE = "veille_signaux_reponse_<ia>.md"

# Règles de couverture (décision David, 28 sept 2026) : un premier essai a
# donné 8 signaux sur 11 tirés par l'IA/le numérique. Plafonds calculés
# à partir de --nb (pour 10 : 2 par variable, 8 variables, 3 numériques).
MAX_PAR_VARIABLE = 2
PART_VARIABLES_COUVERTES = 0.8
PART_MAX_NUMERIQUE = 0.3

# Les fiches d'audit des signaux peuvent se trouver à la racine du vault ou
# dans generator/ selon l'historique du projet : on regarde les deux.
SIGNAUX_DIRS = [VAULT_ROOT / "signaux_custom", GENERATOR_DIR / "signaux_custom"]

NB_DEFAUT = 10

# Candidats des veilles précédentes (state/veille_signaux.json, écrit par
# import_signaux_faibles.py) : fournis au LLM comme « déjà repérés » pour
# qu'il cherche du neuf (décision David 28 sept 2026). Même règle de
# dossier state/ que l'import. Plafonné pour ne pas gonfler le prompt.
# Mémoire des pages de livres déjà envoyées (rotation, livres_veille.py) :
# même règle de dossier state/ que les candidats.
def memoire_livres_path() -> Path:
    for d in (VAULT_ROOT / "state", GENERATOR_DIR / "state"):
        if d.exists():
            return d / "livres_veille.json"
    return VAULT_ROOT / "state" / "livres_veille.json"


STATE_CANDIDATS = [VAULT_ROOT / "state" / "veille_signaux.json",
                   GENERATOR_DIR / "state" / "veille_signaux.json"]
MAX_CANDIDATS_VUS = 150


def regles_couverture(nb: int):
    """(max par variable principale, nb min de variables, max signaux numériques)."""
    min_vars = min(len(VARIABLES), max(1, round(nb * PART_VARIABLES_COUVERTES)))
    max_num = max(1, round(nb * PART_MAX_NUMERIQUE))
    return MAX_PAR_VARIABLE, min_vars, max_num
LONGUEUR_RESUME_SIGNAL = 220  # caractères par signal déjà injecté

HORS_VARIABLES = "hors_variables"


# ---------------------------------------------------------------------------
# Lecture des entrées
# ---------------------------------------------------------------------------

def charger_sources(path: Path):
    """
    Lit sources_signaux_faibles.yaml. Renvoie (sources_actives, livres_actifs).
    Une source sans url, ou marquée actif: false, est ignorée.
    """
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    sources = []
    for s in data.get("sources") or []:
        if not isinstance(s, dict) or not s.get("url"):
            continue
        if s.get("actif") is False:
            continue
        sources.append(s)

    livres = []
    for b in data.get("livres") or []:
        if not isinstance(b, dict) or not b.get("titre"):
            continue
        if b.get("actif") is False:
            continue
        livres.append(b)

    return sources, livres


def _idee_source(texte: str) -> str:
    """Premier paragraphe de la section '## Idée source' d'une fiche signal."""
    m = re.search(r"^##\s+Idée source\s*$", texte, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ""
    reste = texte[m.end():]
    fin = re.search(r"^##\s+\S", reste, re.MULTILINE)
    bloc = (reste[:fin.start()] if fin else reste).strip()
    # Premier paragraphe, sur une seule ligne.
    para = bloc.split("\n\n")[0]
    para = " ".join(para.split())
    if len(para) > LONGUEUR_RESUME_SIGNAL:
        coupe = para[:LONGUEUR_RESUME_SIGNAL].rsplit(" ", 1)[0]
        para = coupe + "…"
    return para


def charger_signaux_existants():
    """
    Liste (slug, résumé) des signaux déjà injectés, pour que le LLM ne les
    repropose pas. README.md exclu explicitement (pas un fichier de données).
    """
    vus = {}
    for d in SIGNAUX_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name.lower() == "readme.md" or f.stem in vus:
                continue
            try:
                texte = f.read_text(encoding="utf-8")
            except OSError:
                continue
            vus[f.stem] = _idee_source(texte)
    return sorted(vus.items())


def charger_candidats_vus():
    """
    Titres des candidats déjà repérés par les veilles précédentes, tous
    statuts confondus (à trier, écarté, en queue), les plus récents d'abord,
    dédoublonnés. [] si le fichier n'existe pas ou est illisible.
    """
    chemin = next((c for c in STATE_CANDIDATS if c.exists()), None)
    if chemin is None:
        return []
    try:
        import json
        data = json.loads(chemin.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    vus, res = set(), []
    for lot in reversed(data.get("lots", [])):
        for c in lot.get("candidats", []):
            t = (c.get("titre") or "").strip()
            if t and t.lower() not in vus:
                vus.add(t.lower())
                res.append(t)
    return res[:MAX_CANDIDATS_VUS]


def charger_deja_connu():
    """Paragraphes 'Situation actuelle' d'etat_du_monde_reel.md, par variable."""
    if not ETAT_MONDE_PATH.exists():
        return {}
    contenu = ETAT_MONDE_PATH.read_text(encoding="utf-8")
    res = {}
    for slug in VARIABLES:
        para, date_str = extraire_situation_complete(contenu, slug)
        if para:
            res[slug] = (para, date_str)
    return res


# ---------------------------------------------------------------------------
# Construction du prompt
# ---------------------------------------------------------------------------

def _ligne_source(s: dict) -> str:
    morceaux = [f"- {s.get('nom', s['url'])} — {s['url']}"]
    details = []
    if s.get("langue"):
        details.append(s["langue"])
    if s.get("famille"):
        details.append(s["famille"])
    if s.get("variables"):
        details.append("variables privilégiées : " + ", ".join(s["variables"]))
    if s.get("acces") == "partiel":
        details.append("en partie sous abonnement, lire la partie publique")
    if details:
        morceaux.append(f" ({' ; '.join(details)})")
    return "".join(morceaux)


IA_EXEMPLES = "claude, chatgpt, mistral, deepseek, gemini, perplexity"


def consigne_livraison(ou: str = "ci-dessous") -> list:
    """Lignes de la consigne de livraison, reprises en tête et en fin de prompt."""
    return [
        "- Livre ta réponse sous la forme d'UN SEUL FICHIER téléchargeable au "
        "format Markdown (.md) : artifact, Canvas, pièce jointe ou fichier "
        "généré, selon ce que permet ton interface.",
        f"- Nom EXACT du fichier : {REPONSE_MODELE}, où <ia> est le nom de ton "
        f"assistant, en minuscules, sans espace ni accent ({IA_EXEMPLES}). "
        "Exemple : veille_signaux_reponse_claude.md.",
        "- PREMIÈRE LIGNE du fichier, obligatoire : « ia: <ton nom> », avec "
        "le même nom que dans le nom du fichier (ex. « ia: claude »). Elle "
        "identifie la provenance même si le fichier est renommé.",
        "- Ensuite, UNIQUEMENT les blocs « ### SIGNAL n », puis le bloc "
        "« ### SOURCES CONSULTÉES » (une ligne par source de départ : "
        "consultée, inaccessible ou non consultée, et ce que tu en as tiré), suivis de "
        f"UNE SEULE ligne « ### FIN » tout à la fin, au format décrit {ou}. Aucun autre texte "
        "avant le premier bloc ni après « ### FIN », pas de bloc de code "
        "(```), pas de tableau, pas de résumé.",
        "- Seulement si ton interface ne peut vraiment pas produire de "
        "fichier : réponds dans le chat avec exactement le même contenu, "
        "ligne « ia: … » comprise.",
    ]


# ---------------------------------------------------------------------------
# Blocs communs aux prompts (web à coller, livres par API : veille_livres_api.py)
# ---------------------------------------------------------------------------

def bloc_definition() -> list:
    L = []
    L.append(
        "Définition (au sens strict, d'après Igor Ansoff) : un signal faible "
        "est un phénomène DÉJÀ OBSERVABLE aujourd'hui, encore MARGINAL ou "
        "INCERTAIN, mais dont l'évolution, ou la COMBINAISON avec d'autres "
        "phénomènes, pourrait produire une transformation importante. "
        "Chaque signal proposé doit passer les 3 tests :"
    )
    L.append("  1. Observable : un fait réel, daté et situé (expérience, premier "
             "cas, prototype, loi, pratique) — pas une prédiction ni une opinion ;")
    L.append("  2. Marginal ou incertain AUJOURD'HUI : peu relayé, cantonné à une "
             "niche, un territoire, une communauté, un laboratoire, une première "
             "occurrence, ou dont l'effet reste contesté ;")
    L.append("  3. Potentiel de transformation : par son évolution propre OU par "
             "combinaison avec d'autres phénomènes (dis lesquels dans la "
             "justification).")
    L.append("")
    L.append("Exemples de ce qui compte comme signal faible :")
    L.append("  - une première occurrence (premier procès, premier usage, premier cas) ;")
    L.append("  - une pratique marginale qui se répand dans une communauté ;")
    L.append("  - un résultat de recherche encore peu médiatisé ;")
    L.append("  - un projet de loi, une expérimentation locale, un nouveau vocabulaire ;")
    L.append("  - une anomalie qui contredit une tendance établie.")
    L.append("")
    L.append("Ce qui N'EST PAS un signal faible (à ne PAS proposer) :")
    L.append("  - une tendance déjà installée ou largement commentée ;")
    L.append("  - un gros titre de l'actualité générale ;")
    L.append("  - une statistique, un classement, une part de marché ou un "
             "indicateur agrégé (parts de brevets ou de publications par pays, "
             "taux de collaboration…) : ce sont des MESURES de tendances, pas "
             "des phénomènes. Un signal est une chose précise qui se passe "
             "quelque part : une technologie, une pratique, une expérience, "
             "un acteur, une règle nouvelle ;")
    L.append("  - tout ce qui figure dans la section « DÉJÀ CONNU » ci-dessous.")
    L.append("")
    return L


def bloc_variables() -> list:
    L = []
    # ── Variables ────────────────────────────────────────────────────────
    L.append("## LES 12 VARIABLES DU MONDE D'OURRASSOL")
    L.append("")
    L.append(
        "Rattache chaque signal à une variable principale et au plus deux "
        "secondaires (utilise les identifiants EXACTS). Si un signal "
        "important ne rentre bien dans "
        f"aucune, utilise « {HORS_VARIABLES} » : ne force JAMAIS un signal "
        "dans une case qui ne lui convient pas. Les lignes « · » sont des "
        "sous-variables, là pour t'aider à choisir : ce ne sont PAS des "
        "identifiants, n'utilise que les identifiants des lignes « - »."
    )
    L.append("")
    for slug in VARIABLES:
        L.append(f"- {slug}")
        for nom, role in load_sub_variables(slug):
            label = nom.replace("_", " ")
            L.append(f"    · {label}" + (f" : {role}" if role else ""))
    L.append("")

    return L


def bloc_deja_connu(deja_connu: dict, signaux_existants: list, candidats_vus: list = ()) -> list:
    L = []
    # ── Déjà connu ───────────────────────────────────────────────────────
    L.append("## DÉJÀ CONNU (à ne PAS reproposer)")
    L.append("")
    L.append(
        "Tendances établies déjà suivies par le projet. Un signal qui ne "
        "fait que confirmer ces constats n'est pas nouveau. Un signal qui "
        "les contredit, ou qui en montre une forme inattendue, peut l'être."
    )
    L.append("")
    if deja_connu:
        for slug in VARIABLES:
            if slug not in deja_connu:
                continue
            para, _ = deja_connu[slug]
            L.append(f"### {slug}")
            L.append(para)
            L.append("")
    else:
        L.append("(état du monde indisponible)")
        L.append("")

    L.append("Signaux faibles déjà intégrés au projet (ne pas les reproposer) :")
    if signaux_existants:
        for slug, resume in signaux_existants:
            L.append(f"- {slug}" + (f" : {resume}" if resume else ""))
    else:
        L.append("- (aucun)")
    L.append("")

    if candidats_vus:
        L.append("Signaux déjà repérés par nos veilles précédentes (retenus ou "
                 "non) : ne les repropose pas, même reformulés. Un fait "
                 "réellement NOUVEAU sur l'un d'eux peut être proposé, en le "
                 "disant dans la justification.")
        for t in candidats_vus:
            L.append(f"- {t}")
        L.append("")

    return L


def bloc_evaluation() -> list:
    L = []
    # ── Évaluation ───────────────────────────────────────────────────────
    L.append("## ÉVALUATION (notes entières de 1 à 5)")
    L.append("")
    L.append(
        "- pertinence : force du lien avec la variable principale (pour "
        f"« {HORS_VARIABLES} » : capacité à transformer le monde en "
        "profondeur). 1 = lien lointain, 5 = touche le cœur de la variable."
    )
    L.append(
        "- nouveaute : absence du « déjà connu » et des grands médias. "
        "1 = déjà bien connu, 5 = presque personne n'en parle."
    )
    L.append(
        "- impact : ampleur possible d'ici quelques décennies s'il se "
        "développe. 1 = effet local ou anecdotique, 5 = peut transformer "
        "le monde."
    )
    L.append(
        "Sois exigeant et différencie les notes : un 5 doit rester rare. "
        "La justification explique les trois notes en 1 à 3 phrases."
    )
    L.append("")
    L.append(
        "Précise aussi la nature : « signal » (une évolution qui peut "
        "s'étendre dans la durée) ou « evenement » (un fait ponctuel daté)."
    )
    L.append("")

    return L


def bloc_champs_signal() -> list:
    L = []
    L.append("### SIGNAL 1")
    L.append("titre: [titre court et précis]")
    L.append("description: [ce qui a été observé, où, par qui, et pourquoi c'est un signal faible — 60 à 150 mots]")
    L.append("observe_le: [AAAA-MM, date approximative de l'observation]")
    L.append("lieu: [pays, région ou ville ; « mondial » si pas de lieu]")
    L.append("nature: [signal ou evenement]")
    L.append(f"variable_principale: [1 identifiant, ou {HORS_VARIABLES}]")
    L.append("variables_secondaires: [0 à 2 identifiants séparés par des virgules, ou vide]")
    L.append("moteur_numerique: [oui ou non — oui si l'IA ou le numérique est le moteur du signal]")
    L.append("pertinence: [1-5]")
    L.append("nouveaute: [1-5]")
    L.append("impact: [1-5]")
    L.append("justification: [1 à 3 phrases]")
    return L


def build_prompt(today_str: str, sources: list, livres: list,
                 signaux_existants: list, deja_connu: dict,
                 nb: int, depuis: str = None, candidats_vus: list = ()) -> str:
    # Tout le fichier est le prompt, à coller tel quel dans l'IA (demande
    # David 28 sept 2026) : plus de consigne destinée à David en tête ni de
    # ligne de séparation -- ces rappels sont dans le GUI et la console.
    L = []
    L.append(f"# Veille signaux faibles — {today_str}")
    L.append("")
    # Consigne de livraison renforcée (demande David 28 sept 2026) : un
    # fichier .md, nommé avec le nom de l'IA -- le fichier téléchargé peut
    # alors être déposé tel quel dans veille_signaux_reponses/. Répétée en
    # fin de prompt (rappel_livraison), les IA suivant mieux la dernière
    # consigne lue.
    L.append("## CONSIGNE DE LIVRAISON (IMPORTANT)")
    L.append("")
    L.extend(consigne_livraison())
    L.append("")

    # ── Mission ──────────────────────────────────────────────────────────
    L.append("## MISSION")
    L.append("")
    L.append(
        "Tu fais de la veille pour un projet de fiction spéculative "
        "(« Ourrassol 2098 ») qui imagine l'évolution du monde de "
        "aujourd'hui jusqu'en 2098, selon 6 scénarios. Le projet a besoin "
        "de SIGNAUX FAIBLES réels, observables aujourd'hui, qui pourraient "
        "devenir des transformations majeures dans les décennies à venir."
    )
    L.append("")
    L.extend(bloc_definition())
    if depuis:
        L.append(f"Période à couvrir : depuis {depuis}.")
    else:
        L.append("Période à couvrir : les derniers mois, par priorité les plus récents.")
    L.append("")
    max_var, min_vars, max_num = regles_couverture(nb)
    L.append(
        f"Objectif : environ {nb} signaux, sélectionnés pour leur qualité. "
        "Mieux vaut moins de signaux, mais solides et sourcés, qu'une liste "
        "gonflée. Cherche aussi hors d'Europe et d'Amérique du Nord."
    )
    L.append("")
    L.append("RÈGLES DE COUVERTURE (obligatoires) :")
    L.append(
        "  - Chaque signal a UNE variable principale : le domaine qu'il "
        "TRANSFORME, pas sa cause. Exemple : des centres de données qui "
        "assèchent une ville relèvent de climat_environnement_global (eau), "
        "pas de technologie_information."
    )
    L.append(f"  - Au plus {max_var} signaux par variable principale.")
    L.append(f"  - Au moins {min_vars} variables principales différentes au total.")
    L.append(
        f"  - Au plus {max_num} signaux dont le moteur est l'IA ou le "
        "numérique, toutes variables confondues. La technologie produit "
        "beaucoup de « premières » faciles à trouver : ne te laisse pas "
        "entraîner, cherche activement les autres domaines (démographie, "
        "économie, espace, santé hors technologie, territoires, religion…)."
    )
    L.append(
        "  - Si une règle ne peut pas être tenue faute de bon signal, "
        "respecte-la quand même en proposant moins de signaux."
    )
    L.append("")

    # ── Sources ──────────────────────────────────────────────────────────
    L.append("## SOURCES DE DÉPART")
    L.append("")
    L.append(
        "Commence par ces sources, puis ÉLARGIS librement à d'autres "
        "(publications scientifiques, médias locaux, rapports, forums "
        "spécialisés…). Un signal faible se trouve souvent loin des grands "
        "médias. Chaque signal DOIT citer au moins une source : l'URL exacte "
        "d'une page que tu as réellement consultée, jamais une adresse "
        "reconstituée ou devinée. Les liens sont testés automatiquement à "
        "l'import : un signal sans source, ou dont les liens n'existent pas, "
        "est écarté d'office. Mieux vaut moins de signaux, tous sourcés. "
        "Rends compte de chaque source de départ dans le bloc « ### SOURCES "
        "CONSULTÉES » en fin de réponse (voir le format), y compris celles "
        "que tu n'as pas pu lire (abonnement, blocage) ou qui n'apportaient rien."
    )
    L.append("")
    # Prompt recentré (décision David 29 sept 2026) : les sources dotées d'un
    # flux RSS sont lues automatiquement par veille_rss_api.py. L'IA ne les
    # reçoit plus comme sources de départ, pour passer son temps sur les
    # autres et sur l'élargissement.
    sources_depart = [s for s in sources if not s.get("rss")]
    sources_rss = [s for s in sources if s.get("rss")]
    if sources_depart:
        for s in sources_depart:
            L.append(_ligne_source(s))
    else:
        L.append("(aucune source de départ : cherche librement)")
    L.append("")
    if sources_rss:
        L.append(
            "Sources DÉJÀ LUES automatiquement par ailleurs (leurs articles "
            "récents sont analysés sans toi) : ne passe pas de temps dessus, "
            "et ne les mets pas dans « SOURCES CONSULTÉES ». Un article plus "
            "ancien de l'une d'elles reste utilisable si tu y arrives par une "
            "autre recherche : "
            + ", ".join(s.get("nom", s["url"]) for s in sources_rss) + "."
        )
        L.append("")

    # Livres déclarés dans le YAML sans fichier : à joindre à la main.
    if livres:
        L.append("## AUTRES LIVRES")
        L.append("")
        L.append(
            "Si des fichiers ou extraits sont joints à cette conversation, "
            "exploite-les aussi, avec les 3 tests ci-dessus, et vérifie en "
            "ligne que le phénomène est encore marginal aujourd'hui (un livre "
            "date de son écriture). Pour un signal tiré d'un livre, cite titre "
            "et chapitre/page, plus une URL récente. Livres prévus :"
        )
        for b in livres:
            ligne = f"- {b['titre']}"
            if b.get("auteur"):
                ligne += f" — {b['auteur']}"
            if b.get("annee"):
                ligne += f" ({b['annee']})"
            if b.get("note"):
                ligne += f" : {b['note']}"
            L.append(ligne)
        L.append("")

    L.extend(bloc_variables())
    L.extend(bloc_deja_connu(deja_connu, signaux_existants, candidats_vus))
    L.extend(bloc_evaluation())

    # ── Format ───────────────────────────────────────────────────────────
    L.append("## FORMAT DE SORTIE STRICT")
    L.append("")
    L.append(
        "Rien avant le premier bloc sauf la ligne « ia: … ». Un bloc par signal, numéroté. UNE SEULE "
        "LIGNE par champ (pas de retour à la ligne à l'intérieur d'un champ), "
        "sauf « sources » (une source par ligne, commençant par « - »). "
        "Termine obligatoirement par la ligne « ### FIN », UNE SEULE FOIS, "
        "tout à la fin, après le dernier signal (pas après chaque signal)."
    )
    L.append("")
    L.append("ia: [ton nom en minuscules, ex. claude]")
    L.append("")
    L.extend(bloc_champs_signal())
    L.append("sources:  (OBLIGATOIRE, au moins une URL réellement consultée)")
    L.append("- [URL] — [nom du média ou de l'auteur]")
    L.append("")
    L.append("### SIGNAL 2")
    L.append("[même structure]")
    L.append("")
    L.append("### SOURCES CONSULTÉES")
    L.append("- [nom de la source de départ] : consultée | inaccessible | non consultée — "
             "[ce que tu en as tiré : numéro(s) de signal, « rien de pertinent », ou la raison]")
    L.append("- [une ligne par source de départ, toutes, dans l'ordre de la liste]")
    L.append("")
    L.append("### FIN")
    L.append("")
    L.append("## RAPPEL AVANT DE RÉPONDRE")
    L.append("")
    L.extend(consigne_livraison("ci-dessus"))
    L.append("")

    return "\n".join(L)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nb", type=int, default=NB_DEFAUT,
                        help=f"Nombre de signaux visé (défaut {NB_DEFAUT}).")
    parser.add_argument("--depuis", default=None,
                        help="Période à couvrir, texte libre (ex. « juillet 2026 »).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche le prompt sans écrire le fichier.")
    args = parser.parse_args()

    if args.nb < 1 or args.nb > 50:
        print("[ERREUR] --nb doit être entre 1 et 50.")
        return

    try:
        sources, livres = charger_sources(SOURCES_PATH)
    except FileNotFoundError:
        print(f"[ERREUR] Fichier introuvable : {SOURCES_PATH}")
        return
    except yaml.YAMLError as e:
        print(f"[ERREUR] {SOURCES_PATH.name} illisible (YAML) : {e}")
        return

    # Les livres du dossier documentation/livres/ sont lus par API
    # (veille_livres_api.py), pas dans ce prompt à coller (décision David
    # 28 sept 2026) : restent ici seulement les livres déclarés sans fichier.
    deja_connu = charger_deja_connu()
    signaux = charger_signaux_existants()
    candidats_vus = charger_candidats_vus()
    manquantes = [s for s in VARIABLES if s not in deja_connu]

    if manquantes:
        print("[AVERTISSEMENT] Situation actuelle introuvable dans "
              "etat_du_monde_reel.md pour :")
        for s in manquantes:
            print(f"  - {s}")

    today_str = format_date_fr(datetime.now())
    prompt = build_prompt(today_str, sources, livres, signaux, deja_connu,
                          args.nb, args.depuis, candidats_vus)

    resume = (f"{len(sources)} source(s) active(s), "
              f"{len(signaux)} signal(aux) déjà injecté(s), "
              f"{len(candidats_vus)} candidat(s) de veilles précédentes, "
              f"{len(deja_connu)}/{len(VARIABLES)} variables dans le déjà connu, "
              f"~{len(prompt.split())} mots.")

    if args.dry_run:
        print(prompt)
        print(f"\n[dry-run] {resume} Rien écrit sur disque.")
        return

    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_OUTPUT_PATH.write_text(prompt, encoding="utf-8")
    print(f"[OK] Prompt écrit dans {PROMPT_OUTPUT_PATH}")
    print(f"     {resume}")
    print("     Prochaine étape : copier ce fichier dans une IA avec accès web,")
    print(f"     puis ranger chaque réponse dans")
    print(f"     {REPONSES_DIR_REL}/{REPONSE_MODELE}.")


if __name__ == "__main__":
    main()
