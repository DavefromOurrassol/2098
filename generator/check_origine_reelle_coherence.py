#!/usr/bin/env python3
"""
check_origine_reelle_coherence.py — Ourrassol 2098 (P22)
==========================================================

Garde-fou de cohérence géographique : détecte les zones (type ville/
region_administrative dans origine_reelle) dont le pays ne correspond à
aucun pays présent dans la chaîne de parenté (zones ancêtres). C'est le
signal qui aurait détecté les 4 anomalies trouvées le 13 juillet 2026 en
testant P7 (Barcelone-Hub, Corridor ibérique énergétique, Cracovie, Nœud
Mnemos du Bassin Pannonien — cette dernière encore active au moment
d'écrire ce script).

RESTE UN AVERTISSEMENT ACTIONNABLE, JAMAIS UN BLOCAGE DUR (décision du 13
juillet 2026, confirmée par le taux de faux positifs d'une première
heuristique mots-clés : 5 sur 9). Lecture seule PAR DÉFAUT, y compris en
mode --resolve-llm (le LLM ne fait que résoudre un nom de ville en pays, il
n'écrit jamais dans le vault). Seul --write-zones-manquantes écrit dans le
vault, explicitement, sur demande -- jamais par défaut (voir §4 ci-dessous).

RECHERCHE DE CANDIDATS + zones_manquantes.yaml (--write-zones-manquantes)
---------------------------------------------------------------------------
Pour chaque incohérence détectée, le script cherche si une zone N1 déjà
existante du même scénario liste déjà le pays résolu dans son propre
origine_reelle -- un candidat de reparent. S'il n'y en a aucun, c'est le
signe que ce territoire n'a pas de zone cohérente dans ce scénario : une
entrée est ajoutée dans zones_manquantes.yaml (même schéma que
complete_geographie_coverage.py : pays/scenario/statut, + deux champs de
traçabilité optionnels origine/zone_incoherente_a_reparenter), en vue de
P24 étape C (générateur top-down, pas encore construit). Écrite seulement
avec --write-zones-manquantes ; sans ce flag, affichage d'un aperçu.

RÉSOLUTION VILLE/RÉGION -> PAYS, EN CASCADE
--------------------------------------------
  1. Extraction directe : le pays apparaît déjà comme token dans le champ
     `entite` (ex. "Massif Central, France" -> France), y compris via une
     petite table d'alias adjectivaux (ex. "américain" -> États-Unis).
  2. Table statique VILLE_PAYS ci-dessous, pour les noms de ville/région
     bruts sans pays explicite (ex. "Barcelone" -> Espagne). À ENRICHIR
     MANUELLEMENT au fil de l'eau à mesure que le pipeline bottom-up
     introduit de nouvelles villes -- un nom absent de cette table tombe
     simplement en 'non résolu', jamais en fausse alerte.
  3. --resolve-llm : passe LLM en batch (tier structured_strict, voir
     llm_client.py) sur les entrées encore non résolues après 1 et 2.
     Résultat mis en cache dans CACHE_LLM_PATH pour ne jamais repayer la
     même résolution deux fois.

USAGE
-----
    python3 check_origine_reelle_coherence.py --scenario breakdown
    python3 check_origine_reelle_coherence.py --all
    python3 check_origine_reelle_coherence.py --all --resolve-llm
    python3 check_origine_reelle_coherence.py --all --write-zones-manquantes
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from check_zones_coherence import ALIASES as ALIASES_PAYS  # source unique, partagée avec check_zones_coherence.py
from check_zones_coherence import ZONES_MANQUANTES  # même fichier, même schéma que complete_geographie_coverage.py

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
GUI_DIR = VAULT_ROOT / "gui"
ZONES_PAYS = GUI_DIR / "zones_pays.json"
CACHE_LLM_PATH = SCRIPT_DIR / "cache_ville_pays_llm.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

TYPES_A_VERIFIER = ("ville", "region_administrative")

_WIKILINK_KEY = re.compile(r"\[\[([^\]]+)\]\]")

# Alias adjectival/descriptif -> pays. Complète l'extraction directe pour
# les tournures qui ne citent pas le nom du pays tel quel.
ADJECTIFS_PAYS = {
    "américain": "états-unis",
    "américaine": "états-unis",
    "russe": "russie",
}

# Table statique ville/région -> pays (ou liste de pays si intrinsèquement
# transfrontalière). Couvre les noms bruts sans pays explicite dans
# `entite`. À ENRICHIR MANUELLEMENT -- un nom absent tombe en 'non résolu',
# pas en fausse alerte. Voir --resolve-llm pour combler les trous sans
# maintenance manuelle immédiate.
VILLE_PAYS: dict = {
    "almaty": "kazakhstan",
    "amazonie": ["brésil", "pérou", "colombie", "équateur", "bolivie", "venezuela", "guyana", "suriname"],
    "amsterdam": "pays-bas",
    "apennins": "italie",
    "balkans occidentaux": ["serbie", "bosnie-herzégovine", "albanie", "macédoine du nord", "monténégro", "kosovo"],
    "bamako": "mali",
    "bandar abbas": "iran",
    "barcelone": "espagne",
    "bassin de la garonne": "france",
    "bassin du rhin": ["allemagne", "france", "suisse", "pays-bas"],
    "belém": "brésil",
    "bratislava": "slovaquie",
    "brazzaville": "république du congo",
    "bruxelles": "belgique",
    "canada côtier": "canada",
    "casablanca": "maroc",
    "chengdu": "chine",
    "corrèze": "france",
    "cévennes": "france",
    "dakar": "sénégal",
    "gdańsk": "pologne",
    "genève": "suisse",
    "groenland": "danemark",
    "helsinki": "finlande",
    "iqaluit": "canada",
    "kigali": "rwanda",
    "kinshasa": "république démocratique du congo",
    "la haye": "pays-bas",
    "lagos": "nigeria",
    "manaus": "brésil",
    "marges eurasiennes périphériques": None,  # trop vague, même pour la table
    "medellín": "colombie",
    "montréal": "canada",
    "moscou": "russie",
    "nairobi": "kenya",
    "nuuk": ["groenland", "danemark"],  # convention incohérente entre scénarios :
                          # fortress_world traite le Groenland comme entité autonome
                          # de premier rang ("État autonome du Groenland", sources
                          # kalaallit_nunaat...) ; policy_reform semble le rattacher
                          # implicitement au Danemark (aucune entrée "Groenland"
                          # séparée, mais "Danemark" présent dans europe_nord_ouest,
                          # candidat bien plus cohérent pour nuuk_knsf que le bloc
                          # russo-chinois espace_eurasiatique). Résoudre vers les deux
                          # laisse remonter tous les candidats plausibles plutôt que
                          # d'imposer une convention qui ne tient pas partout.
    "ouagadougou": "burkina faso",
    "pays de galles": "royaume-uni",
    "rotterdam": "pays-bas",
    "são paulo": "brésil",
    "séoul": "corée du sud",
    "tampere": "finlande",
    "tbilissi": "géorgie",
    "thunder bay": "canada",
    "valence": "espagne",
    "vallée du rhône": "france",
    "washington d.c.": "états-unis",
    "écosse": "royaume-uni",
}


# ─────────────────────────────────────────
# LECTURE / PARSING
# ─────────────────────────────────────────

def _read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} : frontmatter YAML mal formé (délimiteurs '---' manquants).")
    fm_raw = _WIKILINK_KEY.sub(r'"\1"', parts[1])
    return yaml.safe_load(fm_raw) or {}


def _zones_par_slug(zones: list) -> dict:
    return {z.get("slug"): z for z in zones if isinstance(z, dict) and z.get("slug")}


def _normaliser(nom: str) -> str:
    """Ramène une variante de nom de pays connue à sa forme canonique, via
    la table ALIASES partagée avec check_zones_coherence.py (ex.
    "états-unis d'amérique" -> "états-unis")."""
    nom = nom.strip().lower()
    for canonique, variantes in ALIASES_PAYS.items():
        if nom == canonique or nom in variantes:
            return canonique
    return nom


def _compte_comme_pays(o: dict, pays_liste_norm: set) -> bool:
    """
    Détermine si une entrée origine_reelle doit compter comme un pays.

    Trois variantes trouvées le 14 juillet, sur des cas réels, qui
    disaient toutes la même chose sous des formes différentes :
    1. `type_entite` absent (27+ entrées, ex. "Burkina Faso" listé nu) --
       probable oubli de champ à l'écriture.
    2. `type_entite: region_administrative` structurellement complet mais
       l'entité est quand même une entrée de premier rang dans
       zones_pays.json -- ex. "Polynésie française".
    3. `type_entite: autre` pour la même raison -- ex. "Groenland" sous
       nuuk_forteresse (nuna_capital_siege signalé à tort "sans ancêtre
       pays" alors que le rattachement est manifestement voulu : le nom de
       la zone parente contient "Nuuk", sources_attestees référence
       Kalaallit Nunaat).

    Plutôt que d'ajouter une exception par variante rencontrée, la règle se
    généralise : seul `type_entite: ville` reste JAMAIS compté comme pays,
    quel que soit le nom (une ville reste sous-nationale par construction,
    passe par la table VILLE_PAYS/résolution, pas par une correspondance
    directe à la liste de référence). Tout le reste (pays, region_
    administrative, autre, absent, ou toute future variante non prévue) se
    fie à une correspondance EXACTE avec pays_liste_norm -- pas une simple
    présence de token, pour limiter le risque de faux négatif ("Massif
    Central" ne matchera jamais un pays, "Polynésie française" ou
    "Groenland" matchent l'entrée telle quelle).
    """
    type_e = o.get("type_entite")
    if type_e == "pays":
        return True
    if type_e == "ville":
        return False
    entite_norm = (o.get("entite") or "").lower().strip()
    return entite_norm in pays_liste_norm


def _racine_n1(zone: dict, zones_par_slug: dict) -> dict:
    """
    Remonte la chaîne `parent` jusqu'à la zone racine (niveau 1, parent
    null). C'est CETTE zone qu'il faut chercher dans la liste principale de
    la Carte (qui n'affiche que les N1, voir _scan_n1_zones_with_desc dans
    app.py) -- le parent immédiat d'une zone incohérente peut très bien
    être lui-même une sous-zone (N2/N3), invisible tant qu'on n'a pas
    d'abord ouvert l'arbre de SA propre racine. Anti-cycle : s'arrête si un
    slug est revisité.
    """
    courant = zone
    vus = set()
    while courant is not None:
        slug = courant.get("slug")
        if slug in vus:
            break
        vus.add(slug)
        parent_slug = courant.get("parent")
        if not parent_slug:
            return courant
        parent = zones_par_slug.get(parent_slug)
        if parent is None:
            return courant  # parent référencé mais introuvable -- s'arrête là
        courant = parent
    return courant


def _pays_de_la_chaine_parente(zone: dict, zones_par_slug: dict, pays_liste_norm: set) -> set:
    """Union des pays trouvés dans origine_reelle sur toute la chaîne
    d'ancêtres (parent, grand-parent, ..., racine incluse). Tokenise chaque
    entité pays (parenthèses, virgules, slashes) plutôt que de comparer la
    chaîne brute -- "Russie (Sibérie orientale)" doit être reconnu comme
    "russie" au même titre qu'une entrée "Russie" simple. Compte aussi les
    entrées sans type_entite dont le nom est un pays réel connu (voir
    _compte_comme_pays). Anti-cycle : s'arrête si un slug est revisité."""
    pays_trouves = set()
    courant = zone
    vus = set()
    while courant is not None:
        slug = courant.get("slug")
        if slug in vus:
            break
        vus.add(slug)
        for o in (courant.get("origine_reelle") or []):
            if isinstance(o, dict) and _compte_comme_pays(o, pays_liste_norm):
                for tok in _tokens(o.get("entite") or ""):
                    pays_trouves.add(_normaliser(tok))
        parent_slug = courant.get("parent")
        courant = zones_par_slug.get(parent_slug) if parent_slug else None
    return pays_trouves


def _pays_des_zones_n1(zones: list, pays_liste_norm: set) -> dict:
    """Pour chaque zone N1 (niveau 1) du scénario, l'ensemble normalisé des
    pays présents dans son origine_reelle -- même logique de tokenisation/
    normalisation/tolérance aux type_entite manquants que
    _pays_de_la_chaine_parente (voir _compte_comme_pays), mais sans remonter
    de chaîne : chaque N1 est regardée isolément."""
    resultat = {}
    for z in zones:
        if not isinstance(z, dict) or z.get("niveau", 1) != 1:
            continue
        slug = z.get("slug")
        if not slug:
            continue
        pays = set()
        for o in (z.get("origine_reelle") or []):
            if isinstance(o, dict) and _compte_comme_pays(o, pays_liste_norm):
                for tok in _tokens(o.get("entite") or ""):
                    pays.add(_normaliser(tok))
        resultat[slug] = pays
    return resultat


def chercher_candidats(pays_possibles_norm: set, pays_n1: dict) -> list:
    """Retourne les slugs de zones N1 dont l'origine_reelle contient au
    moins un des pays résolus pour la zone incohérente. Liste vide si
    aucune zone N1 existante ne convient -- c'est le signal d'entrée pour
    P24 étape C (générer une nouvelle zone), voir zones_manquantes.yaml."""
    return sorted(
        slug for slug, pays in pays_n1.items()
        if pays_possibles_norm & pays
    )


# ─────────────────────────────────────────
# ÉCRITURE zones_manquantes.yaml (opt-in, --write-zones-manquantes)
# ─────────────────────────────────────────

def _charger_zones_manquantes() -> dict:
    if ZONES_MANQUANTES.exists():
        try:
            return yaml.safe_load(ZONES_MANQUANTES.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            return {}
    return {}


def ajouter_zones_manquantes(incoherences_sans_candidat: list) -> int:
    """
    Ajoute une entrée par incohérence sans candidat N1 dans
    zones_manquantes.yaml, même schéma que complete_geographie_coverage.py
    (pays/scenario/statut) + deux champs de traçabilité optionnels
    (origine, zone_incoherente_a_reparenter) que check_zones_coherence.py
    ignore déjà via .get() -- rétro-compatible.

    Dédoublonne sur (pays, scenario, origine) : ne réécrit jamais une
    entrée déjà présente. Retourne le nombre d'entrées effectivement
    ajoutées.
    """
    data = _charger_zones_manquantes()
    entries = data.setdefault("zones_manquantes", [])
    existantes = {
        (e.get("pays"), e.get("scenario"), e.get("origine"))
        for e in entries if isinstance(e, dict)
    }

    ajoutees = 0
    for inc in incoherences_sans_candidat:
        for pays in inc["pays_resolus"]:
            cle = (pays, inc["scenario"], "check_origine_reelle_coherence")
            if cle in existantes:
                continue
            entries.append({
                "pays": pays,
                "scenario": inc["scenario"],
                "statut": "a_traiter",
                "origine": "check_origine_reelle_coherence",
                "zone_incoherente_a_reparenter": inc["slug"],
            })
            existantes.add(cle)
            ajoutees += 1

    if ajoutees:
        ZONES_MANQUANTES.parent.mkdir(parents=True, exist_ok=True)
        ZONES_MANQUANTES.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return ajoutees


# ─────────────────────────────────────────
# RÉSOLUTION VILLE/RÉGION -> PAYS
# ─────────────────────────────────────────

def _tokens(texte: str) -> list:
    """Découpe une chaîne `entite` en tokens comparables à un nom de pays :
    gère les virgules, les slashes, et le contenu entre parenthèses
    (ex. "Mer Caspienne (zone frontalière Russie/Kazakhstan/...)")."""
    texte = texte.lower()
    interieur_parentheses = re.findall(r"\(([^)]*)\)", texte)
    texte_sans_parentheses = re.sub(r"\([^)]*\)", "", texte)
    morceaux = [texte_sans_parentheses] + interieur_parentheses
    tokens = []
    for m in morceaux:
        tokens += [t.strip() for t in re.split(r"[,/]", m)]
    return [t for t in tokens if t]


def resoudre_pays(entite: str, pays_liste_norm: set, cache_llm: dict = None):
    """
    Tente de résoudre le(s) pays correspondant à une entité ville/région.
    Ordre : extraction directe -> alias adjectival -> table statique ->
    cache LLM (si fourni). Retourne une liste de pays (1 ou plusieurs pour
    une entité intrinsèquement transfrontalière), ou None si non résolu.
    """
    tokens = _tokens(entite)

    # 1. Extraction directe (le pays est déjà écrit dans `entite`)
    trouves = [t for t in tokens if t in pays_liste_norm]
    if trouves:
        return trouves

    # 1bis. Alias adjectival (ex. "midwest américain" -> "états-unis")
    for tok in tokens:
        for adj, pays in ADJECTIFS_PAYS.items():
            if adj in tok and pays in pays_liste_norm:
                return [pays]

    # 2. Table statique (nom brut, ex. "barcelone" -> "espagne")
    entite_norm = entite.lower().strip()
    if entite_norm in VILLE_PAYS:
        valeur = VILLE_PAYS[entite_norm]
        if valeur is None:
            return None  # explicitement trop vague, même pour la table
        return valeur if isinstance(valeur, list) else [valeur]

    # 3. Cache LLM (résolutions déjà obtenues lors d'un run --resolve-llm précédent)
    if cache_llm and entite_norm in cache_llm:
        valeur = cache_llm[entite_norm]
        return valeur if valeur else None

    return None


# ─────────────────────────────────────────
# RÉSOLUTION LLM (batch, optionnelle)
# ─────────────────────────────────────────

def _charger_cache_llm() -> dict:
    if CACHE_LLM_PATH.exists():
        try:
            return json.loads(CACHE_LLM_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _sauver_cache_llm(cache: dict) -> None:
    CACHE_LLM_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def resoudre_via_llm(entites: list) -> dict:
    """
    Résout en un seul appel LLM (tier structured_strict) une liste
    d'entités ville/région non résolues par la cascade locale.
    Retourne {entite_normalisee: [pays,...] | []} -- liste vide si le LLM
    lui-même ne trouve pas de correspondance certaine.
    N'écrit jamais dans le vault ; le résultat est fusionné dans le cache
    par l'appelant.
    """
    from llm_client import call_llm  # import différé : évite la dépendance si --resolve-llm n'est jamais utilisé

    system_prompt = (
        "Tu résous des correspondances ville/région -> pays réel(s) pour un "
        "vérificateur automatique de cohérence géographique. "
        "Réponds UNIQUEMENT avec un objet JSON, sans texte autour ni bloc "
        "de code, au format exact : "
        '{"nom exact fourni": ["pays1", "pays2"]}. '
        "Utilise le français, en minuscules, la forme courante du pays "
        "(ex. 'états-unis', 'russie', 'république démocratique du congo'). "
        "Si une entité est intrinsèquement transfrontalière, liste tous les "
        "pays plausibles. Si tu n'es pas raisonnablement certain, réponds "
        "avec une liste vide pour cette entrée plutôt que de deviner."
    )
    user_prompt = "Entités à résoudre :\n" + "\n".join(f"- {e}" for e in entites)

    reponse = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=2000,
        temperature=0.0,
        task_tier="structured_strict",
    )

    texte = reponse.strip()
    texte = re.sub(r"^```(?:json)?\s*|\s*```$", "", texte.strip())
    try:
        resultat = json.loads(texte)
    except json.JSONDecodeError as e:
        print(f"  ✗ Réponse LLM non parsable en JSON : {e}", file=sys.stderr)
        return {}

    return {
        k.lower().strip(): [str(p).lower().strip() for p in v]
        for k, v in resultat.items()
        if isinstance(v, list)
    }


# ─────────────────────────────────────────
# VÉRIFICATION D'UN SCÉNARIO
# ─────────────────────────────────────────

def check_scenario(scenario: str, pays_liste_norm: set, cache_llm: dict) -> dict:
    """
    Retourne {"incoherences": [...], "non_resolues": [(slug, entite), ...]}
    pour un scénario donné. N'imprime rien elle-même -- affichage centralisé
    dans main() pour pouvoir agréger avant/après --resolve-llm proprement.
    """
    print(f"\n=== {scenario} ===")
    geo_file = GEO_DIR / f"{scenario}.md"
    if not geo_file.exists():
        print(f"  ✗ Fiche introuvable : {geo_file}")
        return {"incoherences": [], "non_resolues": [], "erreur": True}

    try:
        fm = _read_frontmatter(geo_file)
    except (ValueError, yaml.YAMLError) as e:
        print(f"  ✗ ERREUR DE PARSING YAML : {e}")
        return {"incoherences": [], "non_resolues": [], "erreur": True}

    zones = fm.get("zones") or []
    zones_par_slug = _zones_par_slug(zones)
    pays_n1 = _pays_des_zones_n1(zones, pays_liste_norm)

    # Les zones racine (parent: null) N'ONT PAS de chaîne de parenté à
    # valider -- ce garde-fou compare un enfant à ses ancêtres, il n'a pas
    # de sens sur la racine elle-même (voir doc P22 : signal visant les
    # zones rattachées, pas les zones de niveau 1 nouvellement créées).
    a_verifier = [
        z for z in zones
        if isinstance(z, dict)
        and z.get("parent")
        and any(
            isinstance(o, dict) and o.get("type_entite") in TYPES_A_VERIFIER
            for o in (z.get("origine_reelle") or [])
        )
    ]
    print(f"  {len(a_verifier)} zone(s) ville/région à vérifier")

    incoherences = []
    non_resolues = []

    for z in a_verifier:
        entites = [
            o.get("entite", "") for o in (z.get("origine_reelle") or [])
            if isinstance(o, dict) and o.get("type_entite") in TYPES_A_VERIFIER
        ]
        pays_ancetres = _pays_de_la_chaine_parente(z, zones_par_slug, pays_liste_norm)

        for entite in entites:
            pays_possibles = resoudre_pays(entite, pays_liste_norm, cache_llm)
            if pays_possibles is None:
                non_resolues.append((z.get("slug"), entite))
                continue
            pays_possibles_norm = {_normaliser(p) for p in pays_possibles}
            if not (pays_possibles_norm & pays_ancetres):
                candidats = chercher_candidats(pays_possibles_norm, pays_n1)
                racine = _racine_n1(z, zones_par_slug)
                incoherences.append({
                    "scenario": scenario,
                    "slug": z.get("slug"),
                    "nom": z.get("nom"),
                    "entite": entite,
                    "pays_resolus": sorted(pays_possibles_norm),
                    "parent": z.get("parent"),
                    "pays_ancetres": sorted(pays_ancetres),
                    "candidats": candidats,
                    "racine_n1_slug": racine.get("slug"),
                    "racine_n1_nom": racine.get("nom"),
                })

    if incoherences:
        print(f"  ⚠ {len(incoherences)} incohérence(s) origine_reelle vs chaîne de parenté :")
        for inc in incoherences:
            ancetres = ", ".join(inc["pays_ancetres"]) or "aucun"
            print(
                f"      - {inc['slug']!r} ({inc['entite']!r} → "
                f"{', '.join(inc['pays_resolus'])}) sous parent {inc['parent']!r} "
                f"(pays de la chaîne : {ancetres})"
            )
            if inc["candidats"]:
                print(f"          → candidat(s) : {', '.join(inc['candidats'])}")
            else:
                print(f"          → aucun candidat N1 dans ce scénario "
                      f"(territoire sans zone cohérente, voir zones_manquantes.yaml)")
    else:
        print(f"  ✓ Aucune incohérence détectée sur les entrées résolues")

    if non_resolues:
        print(f"  · {len(non_resolues)} entité(s) non résolue(s) (ni extraction directe, ni table statique) :")
        for slug, entite in non_resolues:
            print(f"      - {slug!r} : {entite!r}")

    return {"incoherences": incoherences, "non_resolues": non_resolues, "erreur": False}


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def imprimer_tableau_recapitulatif(resultats: dict) -> None:
    """
    Tableau markdown consolidé de toutes les incohérences trouvées, toutes
    catégories confondues (avec ou sans candidat) -- prêt à coller tel quel
    dans le backlog, sans reformatage manuel à chaque run.
    """
    lignes_corps = []
    for scenario, r in resultats.items():
        for inc in r["incoherences"]:
            pays = ", ".join(p.capitalize() for p in inc["pays_resolus"])
            cas = f"{pays} ({inc['nom'] or inc['slug']})"
            depart = f"`{inc['slug']}` (sous `{inc['parent']}`)"
            racine = f"`{inc['racine_n1_slug']}` ({inc['racine_n1_nom']})" \
                if inc["racine_n1_slug"] != inc["slug"] else "_déjà racine_"
            candidat = ", ".join(f"`{c}`" for c in inc["candidats"]) or "_aucun candidat_"
            lignes_corps.append(f"| {scenario} | {cas} | {depart} | {racine} | {candidat} |")

    if not lignes_corps:
        return

    print("\n=== Tableau récapitulatif (markdown, prêt à copier) ===\n")
    print("| Scénario | Cas problématique | Zone de départ | Racine N1 à ouvrir dans la Carte | Zone candidate |")
    print("|---|---|---|---|---|")
    for l in lignes_corps:
        print(l)


def main():
    parser = argparse.ArgumentParser(
        description="Garde-fou de cohérence origine_reelle vs chaîne de parenté (P22). "
                     "Avertissement uniquement, lecture seule."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", help="Scénario unique à vérifier")
    group.add_argument("--all", action="store_true", help="Vérifier les 6 scénarios")
    parser.add_argument(
        "--resolve-llm", action="store_true",
        help="Tente de résoudre les entités non résolues via un appel LLM en batch "
             "(tier structured_strict), résultat mis en cache."
    )
    parser.add_argument(
        "--write-zones-manquantes", action="store_true",
        help="Écrit dans zones_manquantes.yaml une entrée par incohérence sans "
             "candidat N1 (territoire sans zone cohérente dans ce scénario). "
             "Sans ce flag, le script reste lecture seule et affiche juste un "
             "aperçu de ce qui serait écrit."
    )
    args = parser.parse_args()

    if not ZONES_PAYS.exists():
        print(f"✗ {ZONES_PAYS} introuvable.")
        sys.exit(1)
    zones_pays = json.loads(ZONES_PAYS.read_text(encoding="utf-8"))
    pays_liste_norm = {p.lower().strip() for p in zones_pays.get("pays_liste", [])}

    scenarios = SCENARIOS if args.all else [args.scenario]
    if args.scenario and args.scenario not in SCENARIOS:
        print(f"✗ Scénario inconnu : {args.scenario}")
        print(f"  Scénarios valides : {', '.join(SCENARIOS)}")
        sys.exit(1)

    print("=" * 60)
    print("  Garde-fou origine_reelle — geographie/{scenario}.md")
    print("=" * 60)

    cache_llm = _charger_cache_llm()

    resultats = {s: check_scenario(s, pays_liste_norm, cache_llm) for s in scenarios}

    # ── Passe --resolve-llm : uniquement sur ce qui reste non résolu ──
    toutes_non_resolues = {
        entite for r in resultats.values() for _, entite in r["non_resolues"]
    }
    if args.resolve_llm and toutes_non_resolues:
        print(f"\n=== Résolution LLM ({len(toutes_non_resolues)} entité(s)) ===")
        try:
            nouvelles = resoudre_via_llm(sorted(toutes_non_resolues))
        except (ImportError, EnvironmentError, RuntimeError) as e:
            print(f"  ✗ Résolution LLM impossible : {e}")
            nouvelles = {}

        if nouvelles:
            cache_llm.update(nouvelles)
            _sauver_cache_llm(cache_llm)
            print(f"  ✓ {len(nouvelles)} entité(s) résolue(s), cache mis à jour "
                  f"({CACHE_LLM_PATH})")
            print(f"  Relance le script sans --resolve-llm pour voir le résultat "
                  f"appliqué à la vérification.")
        else:
            print(f"  · Aucune résolution nouvelle obtenue.")

    total_incoherences = sum(len(r["incoherences"]) for r in resultats.values())
    total_non_resolues = len(toutes_non_resolues)
    y_a_erreur = any(r["erreur"] for r in resultats.values())

    # ── Incohérences sans aucun candidat N1 : territoire sans zone cohérente ──
    sans_candidat = [
        inc for r in resultats.values() for inc in r["incoherences"]
        if not inc["candidats"]
    ]
    if sans_candidat:
        print(f"\n=== Incohérences sans candidat N1 ({len(sans_candidat)}) ===")
        if args.write_zones_manquantes:
            ajoutees = ajouter_zones_manquantes(sans_candidat)
            print(f"  ✓ {ajoutees} entrée(s) ajoutée(s) à {ZONES_MANQUANTES} "
                  f"(statut: a_traiter, origine: check_origine_reelle_coherence)")
        else:
            print(f"  · Relancer avec --write-zones-manquantes pour les ajouter à "
                  f"{ZONES_MANQUANTES} (aperçu, rien n'est écrit) :")
            for inc in sans_candidat:
                print(f"      - {inc['slug']!r} ({inc['scenario']}) "
                      f"→ pays : {', '.join(inc['pays_resolus'])}")

    imprimer_tableau_recapitulatif(resultats)

    print("\n" + "=" * 60)
    if y_a_erreur:
        print("  Terminé — des erreurs de lecture ont empêché la vérification complète.")
    elif total_incoherences:
        print(f"  Terminé — {total_incoherences} incohérence(s) à examiner (voir ci-dessus).")
    elif total_non_resolues and not args.resolve_llm:
        print(f"  Terminé — aucune incohérence sur les entrées résolues, "
              f"{total_non_resolues} entité(s) non résolue(s) (relancer avec --resolve-llm).")
    else:
        print("  Terminé — tout est cohérent.")
    print("=" * 60)


if __name__ == "__main__":
    main()
