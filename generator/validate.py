"""
validate.py
-----------
Vérifie la cohérence complète de la base Ourrassol 2098 avant génération.

Usage :
    python3 validate.py              # validation complète
    python3 validate.py --fix        # corrige les problèmes mineurs automatiquement
    python3 validate.py --report     # génère un rapport détaillé en markdown

Vérifie :
    1. Nomenclature — slugs, références, noms de fichiers
    2. Cohérence systémique — levels, états, trajectoires
    3. Cohérence des entités/instances — relations, injections
    4. Cohérence thématique — variables, formats
    5. Références croisées — wikilinks cassés
    6. Matrice d'influence — edges, valeurs
    7. Événements — archétypes, instances, cohérence temporelle
"""

import os
import re
import sys
import json
import yaml
import argparse
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

VAULT_PATH = "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098"

PATHS = {
    "scenarios":        os.path.join(VAULT_PATH, "scenarios"),
    "variables":        os.path.join(VAULT_PATH, "variables"),
    "thematiques":      os.path.join(VAULT_PATH, "thematiques"),
    "entites":          os.path.join(VAULT_PATH, "entites"),
    "instances":        os.path.join(VAULT_PATH, "instances"),
    "evenements":       os.path.join(VAULT_PATH, "evenements"),
    "event_instances":  os.path.join(VAULT_PATH, "event_instances"),
    "influence_matrix": os.path.join(VAULT_PATH, "influence_matrix.md"),
}

VALID_VARS = [
    "systeme_economique_redistribution", "gouvernance_institutions",
    "geopolitique_conflits", "valeurs_culture_tempo_sociale",
    "organisation_territoires", "sante_biotechnologies",
    "frontieres_du_systeme", "technologie_information",
    "climat_environnement_global", "energie_ressources_critiques",
    "demographie_mobilite_humaine", "systemes_productifs_travail",
]

VALID_SCENARIOS = [
    "fortress_world", "new_sustainability", "breakdown",
    "eco_communalism", "policy_reform", "reference"
]

VALID_CATEGORIES = [
    "humain", "organisation", "institution", "mouvement",
    "infrastructure", "réseau", "système", "hybride", "autre",
    "entreprise", "IA", "média"
]

VALID_ETAT_TEMPOREL = [
    "actif", "disparu", "transformé", "clandestin", "historique", "mythifié"
]

VALID_ZONES_GEOGRAPHIQUES = [
    "locale", "urbaine", "nationale", "régionale", "continentale",
    "globale", "orbital",
]

VALID_ECHELLE = [
    "locale", "urbaine", "nationale", "régionale", "continentale", "globale",
]

GEOGRAPHIE_DIR = os.path.join(VAULT_PATH, "geographie")
NEED_ACTION_DIR = os.path.join(VAULT_PATH, "documentation", "need_action")
REVIEW_REPORT   = os.path.join(NEED_ACTION_DIR, "localisation_review.md")

GENERATOR_DIR         = os.path.join(VAULT_PATH, "generator")
LAST_VALIDATED_PATH   = os.path.join(GENERATOR_DIR, "last_validated.json")
NARRATIVE_ISSUES_PATH = os.path.join(NEED_ACTION_DIR, "narrative_issues.yaml")

VALID_AGE_HISTORIQUE = [
    "émergent", "marginal", "ascendant", "dominant",
    "mature", "déclinant", "résiduel", "mythifié"
]

VALID_FORMATS = [
    "breve", "brève",
    "analyse",
    "reportage",
    "chronique",
    "editorial", "éditorial",
    "informatif",
    "narratif",
    "utilitaire",
    "réflexif", "reflexif",
]

# Seuils de cohérence
LEVEL_HIGH_THRESHOLD = 70   # niveau "élevé"
LEVEL_LOW_THRESHOLD  = 30   # niveau "faible"

# Mapping état_temporel attendu selon state_of_system
COHERENCE_MAP = {
    "chaotique":   {"actif", "disparu", "clandestin", "résiduel", "transformé"},
    "fragile":     {"actif", "ascendant", "déclinant", "clandestin", "transformé"},
    "instable":    {"actif", "ascendant", "dominant", "clandestin", "transformé"},
    "stable":      {"actif", "dominant", "mature"},
    "resilient":   {"actif", "dominant", "mature", "ascendant"},
    "collapsing":  {"disparu", "clandestin", "résiduel"},
}


# ─────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────

def parse_md(filepath):
    """Parse un fichier .md et retourne frontmatter + body."""
    if not os.path.exists(filepath):
        return None, None, None
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not fm_match:
        return {}, raw, raw
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", fm_match.group(1))
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        fm = {}
    body = fm_match.group(2).strip()
    return fm, body, raw

def list_files(directory, ext=".md"):
    """Liste les fichiers d'un dossier — exclut les templates et fichiers cachés."""
    if not os.path.exists(directory):
        return []
    return [f for f in sorted(os.listdir(directory))
            if f.endswith(ext)
            and not f.startswith("_")
            and not f.startswith(".")
            and "template" not in f.lower()]


# ─────────────────────────────────────────
# RÉSULTATS
# ─────────────────────────────────────────

class ValidationResult:
    def __init__(self):
        self.errors   = []   # problèmes bloquants
        self.warnings = []   # problèmes non bloquants
        self.infos    = []   # informations utiles
        self.fixes    = []   # corrections appliquées

    def error(self, category, fichier, message):
        self.errors.append({
            "category": category,
            "fichier":  fichier,
            "message":  message,
            "type":     "ERROR"
        })

    def warning(self, category, fichier, message):
        self.warnings.append({
            "category": category,
            "fichier":  fichier,
            "message":  message,
            "type":     "WARNING"
        })

    def info(self, category, message):
        self.infos.append({
            "category": category,
            "message":  message,
            "type":     "INFO"
        })

    def fix(self, fichier, message):
        self.fixes.append({
            "fichier": fichier,
            "message": message,
        })

    @property
    def ok(self):
        return len(self.errors) == 0

    def summary(self):
        return "{} erreurs | {} avertissements | {} corrections".format(
            len(self.errors), len(self.warnings), len(self.fixes)
        )


# ─────────────────────────────────────────
# 1. VALIDATION NOMENCLATURE
# ─────────────────────────────────────────

def validate_nomenclature(result):
    """Vérifie que tous les slugs respectent la nomenclature canonique."""

    # Scénarios
    for fname in list_files(PATHS["scenarios"]):
        slug = fname.replace(".md", "")
        if slug not in VALID_SCENARIOS:
            result.error("nomenclature", fname,
                "Fichier scénario '{}' pas dans la liste canonique".format(slug))

    # Variables
    for fname in list_files(PATHS["variables"]):
        slug = fname.replace(".md", "")
        if slug not in VALID_VARS:
            result.error("nomenclature", fname,
                "Fichier variable '{}' pas dans la liste canonique".format(slug))

    # Vérifier les 6 scénarios et 12 variables sont présents
    sc_present  = [f.replace(".md","") for f in list_files(PATHS["scenarios"])]
    var_present = [f.replace(".md","") for f in list_files(PATHS["variables"])]

    for sc in VALID_SCENARIOS:
        if sc not in sc_present:
            result.error("nomenclature", "{}.md".format(sc),
                "Fiche scénario MANQUANTE : {}".format(sc))

    for v in VALID_VARS:
        if v not in var_present:
            result.error("nomenclature", "{}.md".format(v),
                "Fiche variable MANQUANTE : {}".format(v))

    result.info("nomenclature",
        "{}/{} scénarios | {}/{} variables".format(
            len(sc_present), len(VALID_SCENARIOS),
            len(var_present), len(VALID_VARS)
        ))

    # Instances — vérifier le format slug : {entite}_{scenario}
    for fname in list_files(PATHS["instances"]):
        slug = fname.replace(".md", "")
        # Trouver le scénario dans le slug
        sc_found = None
        for sc in VALID_SCENARIOS:
            if slug.endswith("_{}".format(sc)):
                sc_found = sc
                break
        if not sc_found:
            result.warning("nomenclature", fname,
                "Instance '{}' ne se termine pas par un scénario valide".format(slug))
            continue

        # Vérifier que le frontmatter est cohérent
        fm, _, _ = parse_md(os.path.join(PATHS["instances"], fname))
        if fm:
            fm_scenario = fm.get("scenario", "")
            if fm_scenario and fm_scenario != sc_found:
                result.error("nomenclature", fname,
                    "scenario dans frontmatter '{}' ≠ slug '{}'".format(
                        fm_scenario, sc_found))

            fm_slug = fm.get("slug", "")
            if fm_slug and fm_slug != slug:
                result.error("nomenclature", fname,
                    "slug dans frontmatter '{}' ≠ nom du fichier '{}'".format(
                        fm_slug, slug))


# ─────────────────────────────────────────
# 2. VALIDATION SYSTÉMIQUE
# ─────────────────────────────────────────

def validate_systemic(result):
    """Vérifie la cohérence systémique des fiches variables et scénarios."""

    # Charger les state_of_system des scénarios
    scenario_states = {}
    for sc in VALID_SCENARIOS:
        path = os.path.join(PATHS["scenarios"], "{}.md".format(sc))
        fm, _, _ = parse_md(path)
        if fm:
            scenario_states[sc] = fm.get("state_of_system", "")

    # Vérifier les variable_states dans les scénarios
    for sc in VALID_SCENARIOS:
        path = os.path.join(PATHS["scenarios"], "{}.md".format(sc))
        fm, _, _ = parse_md(path)
        if not fm:
            continue

        vs = fm.get("variable_states", {}) or {}
        for var in VALID_VARS:
            if var not in vs:
                result.warning("systemic", "{}.md".format(sc),
                    "variable_state manquant pour '{}'".format(var))
            else:
                level = vs[var].get("level", "") if isinstance(vs[var], dict) else ""
                trend = vs[var].get("trend", "") if isinstance(vs[var], dict) else ""
                if level == "" or level is None:
                    result.warning("systemic", "{}.md".format(sc),
                        "level manquant pour '{}' dans variable_states".format(var))
                if trend not in ("up", "down", "stable", ""):
                    result.warning("systemic", "{}.md".format(sc),
                        "trend invalide '{}' pour '{}'".format(trend, var))

    # Vérifier les states dans les fiches variables
    for var in VALID_VARS:
        path = os.path.join(PATHS["variables"], "{}.md".format(var))
        fm, _, _ = parse_md(path)
        if not fm:
            continue

        states = fm.get("states", {}) or {}
        for sc in VALID_SCENARIOS:
            if sc not in states:
                result.warning("systemic", "{}.md".format(var),
                    "state manquant pour scénario '{}'".format(sc))
            else:
                s = states[sc]
                if not isinstance(s, dict):
                    result.error("systemic", "{}.md".format(var),
                        "state '{}' invalide (pas un dict)".format(sc))
                    continue
                level = s.get("level", "")
                if level == "" or level is None:
                    result.warning("systemic", "{}.md".format(var),
                        "level manquant dans state '{}'".format(sc))
                sl = str(s.get("state_logic", "")).strip()
                if not sl or len(sl) < 20:
                    result.warning("systemic", "{}.md".format(var),
                        "state_logic vide ou trop court dans '{}'".format(sc))


# ─────────────────────────────────────────
# 3. VALIDATION ENTITÉS / INSTANCES
# ─────────────────────────────────────────

def validate_entities(result):
    """Vérifie la cohérence des entités et instances."""

    # Charger les entités
    entities = {}
    for fname in list_files(PATHS["entites"]):
        slug = fname.replace(".md", "")
        fm, _, _ = parse_md(os.path.join(PATHS["entites"], fname))
        if not fm:
            continue
        entities[slug] = fm

        # Vérifier les champs obligatoires
        for field in ["name", "slug", "category"]:
            if not fm.get(field):
                result.error("entities", fname,
                    "champ obligatoire manquant : '{}'".format(field))

        # Vérifier la catégorie
        cat = fm.get("category", "")
        if cat not in VALID_CATEGORIES and cat:
            result.warning("entities", fname,
                "catégorie invalide : '{}'".format(cat))

        # Vérifier les variables potentielles
        vars_pot = fm.get("variables_potentielles", []) or []
        for v in vars_pot:
            v_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(v)).strip()
            if v_clean not in VALID_VARS:
                result.error("entities", fname,
                    "variable_potentielle invalide : '{}'".format(v_clean))

        # Vérifier les scénarios
        scenarios = fm.get("scenarios_instances", []) or []
        for s in scenarios:
            if s not in VALID_SCENARIOS:
                result.error("entities", fname,
                    "scénario invalide dans scenarios_instances : '{}'".format(s))

    result.info("entities", "{} entités chargées".format(len(entities)))

    # Charger les instances
    instances = {}
    instance_slugs = set()
    scenario_states = {}

    # Charger state_of_system des scénarios pour cohérence
    for sc in VALID_SCENARIOS:
        path = os.path.join(PATHS["scenarios"], "{}.md".format(sc))
        fm, _, _ = parse_md(path)
        if fm:
            scenario_states[sc] = fm.get("state_of_system", "")

    for fname in list_files(PATHS["instances"]):
        slug = fname.replace(".md", "")
        fm, _, _ = parse_md(os.path.join(PATHS["instances"], fname))
        if not fm:
            continue
        instances[slug] = fm
        instance_slugs.add(slug)

        # Champs obligatoires
        for field in ["name", "entite", "scenario"]:
            if not fm.get(field):
                result.error("instances", fname,
                    "champ obligatoire manquant : '{}'".format(field))

        # Vérifier que l'entité parente existe
        entite_slug = fm.get("entite", "")
        if entite_slug and entite_slug not in entities:
            result.warning("instances", fname,
                "entité parente '{}' non trouvée dans entites/".format(entite_slug))

        # Vérifier le scénario
        sc = fm.get("scenario", "")
        if sc and sc not in VALID_SCENARIOS:
            result.error("instances", fname,
                "scénario invalide : '{}'".format(sc))

        # Vérifier variables_influencees
        vars_inf = fm.get("variables_influencees", []) or []
        for v in vars_inf:
            v_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(v)).strip()
            if v_clean not in VALID_VARS:
                result.error("instances", fname,
                    "variable_influencee invalide : '{}'".format(v_clean))

        # Vérifier etat_temporel
        etat = fm.get("etat_temporel", "")
        if etat and etat not in VALID_ETAT_TEMPOREL:
            result.warning("instances", fname,
                "etat_temporel invalide : '{}'".format(etat))

        # Vérifier zone_geographique
        zones_geo = fm.get("zone_geographique", []) or []
        for z in zones_geo:
            z_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(z)).strip()
            if z_clean and z_clean not in VALID_ZONES_GEOGRAPHIQUES:
                result.warning("instances", fname,
                    "zone_geographique invalide : '{}'".format(z_clean))

        # Cohérence etat_temporel ↔ state_of_system du scénario
        if sc and sc in scenario_states and etat:
            sys_state = scenario_states[sc]
            expected_etats = COHERENCE_MAP.get(sys_state, set())
            age = fm.get("age_historique", "")
            if expected_etats and etat not in expected_etats and age not in expected_etats:
                result.warning("instances", fname,
                    "etat_temporel '{}' potentiellement incohérent avec "
                    "state_of_system '{}' du scénario '{}'".format(
                        etat, sys_state, sc))

        # Vérifier les injections custom
        injection = fm.get("injection", {}) or {}
        if injection.get("type") == "custom":
            annee = injection.get("annee_injection")
            if annee:
                try:
                    annee_int = int(annee)
                    if not (2025 <= annee_int <= 2097):
                        result.error("instances", fname,
                            "annee_injection {} hors plage [2025-2097]".format(annee_int))
                except (ValueError, TypeError):
                    result.error("instances", fname,
                        "annee_injection invalide : '{}'".format(annee))

            for imp in (injection.get("impact_sur_variables", []) or []):
                v = imp.get("variable", "")
                if v and v not in VALID_VARS:
                    result.error("instances", fname,
                        "variable d'impact invalide : '{}'".format(v))
                delta = imp.get("delta_level", 0)
                if abs(delta) > 50:
                    result.warning("instances", fname,
                        "delta_level {} très élevé pour '{}'".format(delta, v))

        # Vérifier impact values
        for field in ["impact_local", "impact_systemique_global"]:
            val = fm.get(field)
            if val is not None:
                try:
                    v = int(val)
                    if not (0 <= v <= 5):
                        result.warning("instances", fname,
                            "{} hors plage [0-5] : {}".format(field, v))
                except (ValueError, TypeError):
                    result.warning("instances", fname,
                        "{} invalide : '{}'".format(field, val))

    result.info("instances", "{} instances chargées".format(len(instances)))

    # Vérifier les références entre instances (alliances/oppositions)
    # Règle en vigueur depuis le 2026-06-20 (officialisation alliances/oppositions,
    # voir officialize_alliances.py) : toute nouvelle alliance/opposition DOIT
    # référencer un slug d'instance existant. Le texte libre n'est plus autorisé.
    slug_pattern = re.compile(r"^[a-z0-9_]+$")
    for slug, fm in instances.items():
        for rel_field in ["alliances", "oppositions"]:
            refs = fm.get(rel_field, []) or []
            for ref in refs:
                ref_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(ref)).strip()
                if not ref_clean or ref_clean in instance_slugs:
                    continue
                if slug_pattern.match(ref_clean):
                    result.warning("instances", "{}.md".format(slug),
                        "référence {} '{}' ressemble à un slug mais ne correspond "
                        "à aucune instance existante (slug cassé ou instance "
                        "manquante pour ce scénario)".format(rel_field, ref_clean))
                else:
                    result.warning("instances", "{}.md".format(slug),
                        "référence {} en TEXTE LIBRE : '{}' — règle en vigueur : "
                        "toute alliance/opposition doit référencer un slug "
                        "d'instance existant (créer l'entité/instance via "
                        "create_entity.py puis generate_instances.py, ou "
                        "officialize_alliances.py pour un lot)".format(
                            rel_field, ref_clean))



# ─────────────────────────────────────────
# 4b. VALIDATION LOCALISATION
# ─────────────────────────────────────────

def _load_geo_slugs(scenario):
    """Retourne l'ensemble des slugs de zones valides pour un scénario."""
    import re as _re, yaml as _yaml
    path = os.path.join(GEOGRAPHIE_DIR, "{}.md".format(scenario))
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    m = _re.match(r"^---\s*\n(.*?)\n---", raw, _re.DOTALL)
    if not m:
        return set()
    try:
        data = _yaml.safe_load(m.group(1)) or {}
    except Exception:
        return set()
    zones = data.get("zones", []) or []
    return {z["slug"] for z in zones if isinstance(z, dict) and "slug" in z}


_geo_cache = {}

def _geo_slugs_cached(scenario):
    if scenario not in _geo_cache:
        _geo_cache[scenario] = _load_geo_slugs(scenario)
    return _geo_cache[scenario]


def validate_localisation(result):
    """
    Vérifie le champ localisation sur les fiches riches (instances + event_instances).
    - Présence et structure du champ
    - Slug zone validé contre geographie/{scenario}.md
    - Comptage review_manuelle
    Génère documentation/need_action/localisation_review.md.
    """
    from collections import defaultdict

    review_manuelle = []
    sans_localisation = []
    total_riches = 0

    for dirpath, ftype in [
        (PATHS["instances"],      "instance"),
        (PATHS["event_instances"], "event_instance"),
    ]:
        if not os.path.exists(dirpath):
            continue
        for fname in list_files(dirpath):
            fm, _, _ = parse_md(os.path.join(dirpath, fname))
            if not fm:
                continue

            # Fiches riches uniquement
            if fm.get("statut") == "officialise_minimal":
                continue
            scenario = fm.get("scenario", "")
            if scenario not in VALID_SCENARIOS:
                continue

            total_riches += 1
            loc = fm.get("localisation")

            # Champ absent
            if loc is None:
                sans_localisation.append(fname)
                result.warning("localisation", fname,
                    "champ localisation absent (fiche riche non traitée)")
                continue

            # Champ mal formé
            if not isinstance(loc, dict):
                result.error("localisation", fname,
                    "localisation invalide — doit être un dict YAML")
                continue

            statut = loc.get("statut", "")

            # review_manuelle
            if statut == "review_manuelle":
                review_manuelle.append({
                    "slug":     fm.get("slug", fname.replace(".md", "")),
                    "scenario": scenario,
                    "type":     ftype,
                    "zone":     loc.get("zone") or "(aucune)",
                    "lieu":     loc.get("lieu") or "(aucun)",
                    "type_lieu":loc.get("type_lieu") or "(null)",
                    "note":     loc.get("note") or "",
                })
                continue

            # Vérifier slug zone contre geographie/{scenario}.md
            zone = loc.get("zone")
            if zone:
                valid_slugs = _geo_slugs_cached(scenario)
                if valid_slugs and zone not in valid_slugs:
                    result.error("localisation", fname,
                        "zone '{}' inconnue dans geographie/{}.md".format(zone, scenario))

            # Vérifier type_lieu
            type_lieu = loc.get("type_lieu")
            if type_lieu and type_lieu not in ["ville", "region", "infrastructure", "site_strategique"]:
                result.warning("localisation", fname,
                    "type_lieu invalide : '{}'".format(type_lieu))

    result.info("localisation",
        "{} fiches riches | {} sans localisation | {} review_manuelle".format(
            total_riches, len(sans_localisation), len(review_manuelle)))

    if review_manuelle:
        result.warning("localisation", "—",
            "{} fiche(s) en review_manuelle — voir localisation_review.md".format(
                len(review_manuelle)))

    # Générer localisation_review.md
    _generate_localisation_report(review_manuelle)


def _generate_localisation_report(entries):
    """Génère documentation/need_action/localisation_review.md."""
    from datetime import datetime
    from collections import defaultdict

    os.makedirs(NEED_ACTION_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Localisation — Review manuelle",
        "",
        "_Genere automatiquement par validate.py — {}_".format(now),
        "_Source de verite : etat reel des fiches dans le vault._",
        "",
        "**{} fiche(s) en attente de review.**".format(len(entries)),
        "",
    ]

    if not entries:
        lines.append("OK Aucune fiche en attente.")
    else:
        by_scenario = defaultdict(list)
        for e in entries:
            by_scenario[e["scenario"]].append(e)

        for scenario in VALID_SCENARIOS:
            if scenario not in by_scenario:
                continue
            sc_entries = by_scenario[scenario]
            lines.append("## {} ({})".format(scenario, len(sc_entries)))
            lines.append("")
            for e in sc_entries:
                lines.append("### {}".format(e["slug"]))
                lines.append("- **type** : {}".format(e["type"]))
                lines.append("- **zone candidate** : {}".format(e["zone"]))
                lines.append("- **lieu** : {}".format(e["lieu"]))
                lines.append("- **type_lieu** : {}".format(e["type_lieu"]))
                if e["note"]:
                    lines.append("- **note** : {}".format(e["note"]))
                lines.append("")

    with open(REVIEW_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# ─────────────────────────────────────────
# 4. VALIDATION THÉMATIQUES
# ─────────────────────────────────────────

def validate_thematiques(result):
    """Vérifie la cohérence des fiches thématiques."""

    thema_files = list_files(PATHS["thematiques"])
    result.info("thematiques", "{} thématiques trouvées".format(len(thema_files)))

    for fname in thema_files:
        fm, _, _ = parse_md(os.path.join(PATHS["thematiques"], fname))
        if not fm:
            continue

        slug = fname.replace(".md", "")

        # Vérifier champs obligatoires
        for field in ["name", "slug", "format_dominant"]:
            if not fm.get(field):
                result.warning("thematiques", fname,
                    "champ manquant : '{}'".format(field))

        # Vérifier le format
        fmt = fm.get("format_dominant", "")
        if fmt and fmt not in VALID_FORMATS:
            result.warning("thematiques", fname,
                "format_dominant invalide : '{}'".format(fmt))

        # Vérifier les variables
        for field in ["variables_visibles", "variables_secondaires", "dependances_fortes"]:
            vars_list = fm.get(field, []) or []
            for v in vars_list:
                v_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(v)).strip()
                if v_clean and v_clean not in VALID_VARS:
                    result.error("thematiques", fname,
                        "variable invalide dans '{}' : '{}'".format(field, v_clean))

        # Vérifier echelle
        echelle = fm.get("echelle", "")
        if echelle and echelle not in VALID_ECHELLE:
            result.warning("thematiques", fname,
                "echelle invalide : '{}' (valeurs: {})".format(
                    echelle, "/".join(VALID_ECHELLE)))

        # Vérifier sensibilite_cascades
        sc_val = fm.get("sensibilite_cascades")
        if sc_val is not None:
            try:
                v = int(sc_val)
                if not (0 <= v <= 5):
                    result.warning("thematiques", fname,
                        "sensibilite_cascades hors plage [0-5] : {}".format(v))
            except (ValueError, TypeError):
                result.warning("thematiques", fname,
                    "sensibilite_cascades invalide : '{}'".format(sc_val))


# ─────────────────────────────────────────
# 5. VALIDATION RÉFÉRENCES CROISÉES
# ─────────────────────────────────────────

def validate_cross_references(result):
    """Vérifie les wikilinks et références croisées."""

    all_slugs = set(VALID_VARS) | set(VALID_SCENARIOS)

    # Slugs des entités et instances
    if os.path.exists(PATHS["entites"]):
        for f in list_files(PATHS["entites"]):
            all_slugs.add(f.replace(".md", ""))
    if os.path.exists(PATHS["instances"]):
        for f in list_files(PATHS["instances"]):
            all_slugs.add(f.replace(".md", ""))
    if os.path.exists(PATHS["thematiques"]):
        for f in list_files(PATHS["thematiques"]):
            all_slugs.add(f.replace(".md", ""))

    # Vérifier les wikilinks dans toutes les instances
    if os.path.exists(PATHS["instances"]):
        for fname in list_files(PATHS["instances"]):
            _, body, _ = parse_md(os.path.join(PATHS["instances"], fname))
            if not body:
                continue
            wikilinks = re.findall(r"\[\[([^\]]+)\]\]", body)
            for link in wikilinks:
                link_clean = link.strip()
                if link_clean and link_clean not in all_slugs:
                    result.warning("cross_references", fname,
                        "wikilink cassé : [[{}]]".format(link_clean))

    result.info("cross_references",
        "{} slugs dans le référentiel".format(len(all_slugs)))


# ─────────────────────────────────────────
# 6. VALIDATION MATRICE D'INFLUENCE
# ─────────────────────────────────────────

def validate_matrix(result):
    """Vérifie la matrice d'influence."""

    fm, _, _ = parse_md(PATHS["influence_matrix"])
    if not fm:
        result.error("matrix", "influence_matrix.md",
            "Fichier matrice introuvable ou invalide")
        return

    edges = fm.get("edges", []) or []
    result.info("matrix", "{} edges dans la matrice".format(len(edges)))

    seen_pairs = set()
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            result.error("matrix", "influence_matrix.md",
                "Edge #{} invalide (pas un dict)".format(i))
            continue

        source = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(edge.get("source", ""))).strip()
        target = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(edge.get("target", ""))).strip()

        if source not in VALID_VARS:
            result.error("matrix", "influence_matrix.md",
                "Edge #{} source invalide : '{}'".format(i, source))
        if target not in VALID_VARS:
            result.error("matrix", "influence_matrix.md",
                "Edge #{} target invalide : '{}'".format(i, target))

        # Doublons
        pair = (source, target)
        if pair in seen_pairs:
            result.warning("matrix", "influence_matrix.md",
                "Doublon détecté : {} → {}".format(source, target))
        else:
            seen_pairs.add(pair)

        # Valeurs
        weight = edge.get("weight", 0)
        if not (0 <= float(weight) <= 1):
            result.warning("matrix", "influence_matrix.md",
                "weight hors plage [0-1] pour {} → {} : {}".format(
                    source, target, weight))

        polarity = edge.get("polarity")
        if polarity not in (1, -1):
            result.warning("matrix", "influence_matrix.md",
                "polarity invalide pour {} → {} : {}".format(
                    source, target, polarity))

    # Vérifier 12×11 = 132 edges
    expected = len(VALID_VARS) * (len(VALID_VARS) - 1)
    if len(seen_pairs) != expected:
        result.warning("matrix", "influence_matrix.md",
            "Nombre d'edges : {} (attendu : {})".format(
                len(seen_pairs), expected))


# ─────────────────────────────────────────
# 7. VALIDATION ÉVÉNEMENTS
# ─────────────────────────────────────────

def validate_events(result):
    """Vérifie la cohérence des archétypes d'événements et de leurs instances."""

    # ── Charger les archétypes
    archetypes = set()
    if os.path.exists(PATHS["evenements"]):
        for fname in list_files(PATHS["evenements"]):
            slug = fname.replace(".md", "")
            archetypes.add(slug)
            fm, _, _ = parse_md(os.path.join(PATHS["evenements"], fname))
            if not fm:
                continue

            # Champs obligatoires
            for field in ["name", "slug", "type_evenement", "date_approximative"]:
                if not fm.get(field):
                    result.warning("events", fname,
                        "champ manquant dans archétype : '{}'".format(field))

            # Type valide
            type_ev = fm.get("type_evenement", "")
            if type_ev and type_ev not in ["technological", "systemic",
                                            "political_social", "cultural",
                                            "environmental"]:
                result.warning("events", fname,
                    "type_evenement invalide : '{}'".format(type_ev))

            # Variables hint valides
            for v in (fm.get("variables_hint", []) or []):
                v_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(v)).strip()
                if v_clean and v_clean not in VALID_VARS:
                    result.error("events", fname,
                        "variable_hint invalide : '{}'".format(v_clean))

    result.info("events", "{} archétypes d'événements".format(len(archetypes)))

    # ── Charger les variable levels par scénario pour vérif cohérence
    var_levels = {}
    for sc in VALID_SCENARIOS:
        var_levels[sc] = {}
        path = os.path.join(PATHS["variables"])
        for var in VALID_VARS:
            vpath = os.path.join(PATHS["variables"], "{}.md".format(var))
            fm_v, _, _ = parse_md(vpath)
            if fm_v:
                states = fm_v.get("states", {}) or {}
                if sc in states and isinstance(states[sc], dict):
                    var_levels[sc][var] = states[sc].get("level", 50)

    # ── Charger les slugs d'instances pour vérif acteurs
    instance_slugs = set()
    if os.path.exists(PATHS["instances"]):
        for f in list_files(PATHS["instances"]):
            instance_slugs.add(f.replace(".md", ""))

    # ── Valider les event_instances
    event_instance_count = 0
    if os.path.exists(PATHS["event_instances"]):
        for fname in list_files(PATHS["event_instances"]):
            slug = fname.replace(".md", "")
            path = os.path.join(PATHS["event_instances"], fname)

            # Détection YAML cassé (valeurs avec ":" non quotées)
            try:
                with open(path, encoding="utf-8") as _f:
                    _raw = _f.read()
                _fm_match = re.match(r"^---\s*\n(.*?)\n---", _raw, re.DOTALL)
                if _fm_match:
                    import yaml as _yaml
                    _yaml.safe_load(_fm_match.group(1))
            except Exception as _e:
                result.error("events", fname,
                    "YAML invalide (probablement un ':' non quoté dans un champ name/description) : {}".format(
                        str(_e)[:120]))

            fm, body, _ = parse_md(path)
            if not fm:
                continue
            event_instance_count += 1

            # 1. Slug cohérent avec le scénario
            sc_found = None
            for sc in VALID_SCENARIOS:
                if slug.endswith("_{}".format(sc)):
                    sc_found = sc
                    break
            if not sc_found:
                result.warning("events", fname,
                    "slug '{}' ne se termine pas par un scénario valide".format(slug))
            else:
                # Vérifier cohérence slug ↔ frontmatter scenario
                fm_sc = fm.get("scenario", "")
                if fm_sc and fm_sc != sc_found:
                    result.error("events", fname,
                        "scenario frontmatter '{}' ≠ slug '{}'".format(fm_sc, sc_found))

            # 2. Archétype référencé existe
            archetype_ref = fm.get("archetype", "")
            if archetype_ref and archetype_ref not in archetypes:
                result.warning("events", fname,
                    "archétype '{}' non trouvé dans evenements/".format(archetype_ref))

            # 3. Champs obligatoires
            for field in ["name", "scenario", "date"]:
                if not fm.get(field) and fm.get(field) != 0:
                    result.error("events", fname,
                        "champ obligatoire manquant : '{}'".format(field))

            # 4. Date dans la plage valide
            date = fm.get("date")
            if date is not None:
                try:
                    d = int(date)
                    if not (2025 <= d <= 2097):
                        result.error("events", fname,
                            "date {} hors plage [2025-2097]".format(d))
                except (ValueError, TypeError):
                    result.error("events", fname,
                        "date invalide : '{}'".format(date))

            # 5. Variables dans VALID_VARS et delta cohérent
            sc = fm.get("scenario", "")
            impacts = fm.get("impact_sur_variables", []) or []
            for imp in impacts:
                if not isinstance(imp, dict):
                    continue
                var = re.sub(r"\[\[([^\]]+)\]\]", r"\1",
                             str(imp.get("variable", ""))).strip()
                if var and var not in VALID_VARS:
                    result.error("events", fname,
                        "variable d'impact invalide : '{}'".format(var))
                    continue

                # Cohérence delta ↔ level
                delta    = imp.get("delta_level", 0)
                polarite = imp.get("polarite", 1)
                delta_reel = delta * polarite

                if sc and var and sc in var_levels and var in var_levels[sc]:
                    level = float(var_levels[sc].get(var, 50) or 50)
                    new_level = max(0, min(100, level + delta_reel))

                    # Delta trop fort dans le mauvais sens
                    if abs(delta_reel) > 40:
                        result.warning("events", fname,
                            "delta {:+} très élevé sur {} (level {} → {})".format(
                                delta_reel, var, int(level), int(new_level)))

            # 6. Acteurs impliqués existent dans instances/
            acteurs = fm.get("acteurs_impliques", []) or []
            for acteur in acteurs:
                a_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(acteur)).strip()
                if a_clean and a_clean not in instance_slugs:
                    result.warning("events", fname,
                        "acteur '{}' non trouvé dans instances/".format(a_clean))

            # 7. Wikilinks dans le body
            if body:
                wikilinks = re.findall(r"\[\[([^\]]+)\]\]", body)
                all_slugs = archetypes | instance_slugs | set(VALID_VARS) | set(VALID_SCENARIOS)
                for link in wikilinks:
                    link_clean = link.strip()
                    if link_clean and link_clean not in all_slugs:
                        result.warning("events", fname,
                            "wikilink cassé : [[{}]]".format(link_clean))

    result.info("events", "{} instances d'événements".format(event_instance_count))

def print_results(result, verbose=False):
    sep = "─" * 60

    print("\n" + "═" * 60)
    print("VALIDATION — OURRASSOL 2098")
    print("═" * 60)
    print()

    # Infos
    if result.infos:
        print("📊 INVENTAIRE")
        print(sep)
        for info in result.infos:
            print("  [{}] {}".format(info["category"].upper(), info["message"]))
        print()

    # Erreurs
    if result.errors:
        print("❌ ERREURS ({})".format(len(result.errors)))
        print(sep)
        for err in result.errors:
            print("  [{}] {} — {}".format(
                err["category"].upper(), err["fichier"], err["message"]
            ))
        print()

    # Avertissements
    if result.warnings:
        print("⚠️  AVERTISSEMENTS ({})".format(len(result.warnings)))
        print(sep)
        # Grouper par catégorie
        by_cat = {}
        for w in result.warnings:
            by_cat.setdefault(w["category"], []).append(w)
        for cat, warns in by_cat.items():
            print("  [{}] {} avertissements".format(cat.upper(), len(warns)))
            if verbose:
                for w in warns:
                    print("    {} — {}".format(w["fichier"], w["message"]))
        print()

    # Corrections
    if result.fixes:
        print("🔧 CORRECTIONS APPLIQUÉES ({})".format(len(result.fixes)))
        print(sep)
        for fix in result.fixes:
            print("  {} — {}".format(fix["fichier"], fix["message"]))
        print()

    # Résumé
    print("═" * 60)
    status = "✓ BASE VALIDE" if result.ok else "✗ ERREURS DÉTECTÉES"
    print("{} — {}".format(status, result.summary()))
    print("═" * 60)


def generate_report(result):
    """Génère un rapport markdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Rapport de validation — Ourrassol 2098",
        "Date : {}".format(now),
        "",
        "## Résumé",
        result.summary(),
        "",
        "## Inventaire",
    ]
    for info in result.infos:
        lines.append("- [{}] {}".format(info["category"], info["message"]))

    if result.errors:
        lines.extend(["", "## Erreurs"])
        for err in result.errors:
            lines.append("- **[{}]** `{}` — {}".format(
                err["category"], err["fichier"], err["message"]))

    if result.warnings:
        lines.extend(["", "## Avertissements"])
        for w in result.warnings:
            lines.append("- [{}] `{}` — {}".format(
                w["category"], w["fichier"], w["message"]))

    report_path = os.path.join(VAULT_PATH, "validation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n📄 Rapport sauvegardé : {}".format(report_path))
    return report_path


# ─────────────────────────────────────────
# 8. VALIDATION COHÉRENCE NARRATIVE
# ─────────────────────────────────────────

def _get_last_validated_ts():
    """Retourne le timestamp du dernier run sans erreurs, ou 0.0 si absent."""
    if not os.path.exists(LAST_VALIDATED_PATH):
        return 0.0
    try:
        with open(LAST_VALIDATED_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return float(data.get("timestamp", 0.0))
    except Exception:
        return 0.0


def _update_last_validated():
    """Met à jour last_validated.json avec l'heure courante."""
    os.makedirs(GENERATOR_DIR, exist_ok=True)
    with open(LAST_VALIDATED_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().timestamp(),
            "iso":       datetime.now().isoformat(timespec="seconds"),
        }, f, ensure_ascii=False, indent=2)


def _event_instances_modified_since(ts):
    """True si au moins un fichier dans event_instances/ est plus récent que ts."""
    ei_dir = PATHS["event_instances"]
    if not os.path.exists(ei_dir):
        return False
    for fname in os.listdir(ei_dir):
        if not fname.endswith(".md") or fname.startswith("_"):
            continue
        mtime = os.path.getmtime(os.path.join(ei_dir, fname))
        if mtime > ts:
            return True
    return False


def validate_narrative_coherence(result, force=False):
    """
    Vérifie la cohérence narrative post-injection dans les event_instances :
      A. Acteurs : slug suffixe scénario correct + etat_temporel actif
      B. Variables : overflow level + delta_reel hors [0, 100]

    Ne tourne que si des event_instances ont été modifiées depuis le dernier
    run sans erreurs — ou si force=True (flag --narrative).
    Génère documentation/need_action/narrative_issues.yaml.
    """
    last_ts = _get_last_validated_ts()

    if not force and not _event_instances_modified_since(last_ts):
        result.info("narrative", "Aucune event_instance modifiée depuis la dernière validation — scan ignoré (--narrative pour forcer)")
        return

    # ── Charger les instances : slug → etat_temporel + scenario
    instances_meta = {}  # slug → {"etat_temporel": ..., "scenario": ...}
    if os.path.exists(PATHS["instances"]):
        for fname in list_files(PATHS["instances"]):
            slug = fname.replace(".md", "")
            fm, _, _ = parse_md(os.path.join(PATHS["instances"], fname))
            if fm:
                instances_meta[slug] = {
                    "etat_temporel": fm.get("etat_temporel", ""),
                    "age_historique": fm.get("age_historique", ""),
                    "scenario":      fm.get("scenario", ""),
                }

    # ── Charger les variable levels par scénario
    var_levels = {}
    for sc in VALID_SCENARIOS:
        var_levels[sc] = {}
        for var in VALID_VARS:
            vpath = os.path.join(PATHS["variables"], "{}.md".format(var))
            fm_v, _, _ = parse_md(vpath)
            if fm_v:
                states = fm_v.get("states", {}) or {}
                if sc in states and isinstance(states[sc], dict):
                    var_levels[sc][var] = states[sc].get("level", 50)

    INACTIVE_ETATS = {"disparu", "historique"}

    issues_by_scenario = {}  # scenario → [{"event": ..., "type": ..., "message": ...}]
    total_issues = 0

    ei_dir = PATHS["event_instances"]
    if not os.path.exists(ei_dir):
        result.info("narrative", "Dossier event_instances/ absent — scan ignoré")
        return

    for fname in list_files(ei_dir):
        fm, _, _ = parse_md(os.path.join(ei_dir, fname))
        if not fm:
            continue

        sc = fm.get("scenario", "")
        if sc not in VALID_SCENARIOS:
            continue

        event_slug = fname.replace(".md", "")

        # ── A. Vérification acteurs
        acteurs = fm.get("acteurs_impliques", []) or []
        for acteur_raw in acteurs:
            acteur = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(acteur_raw)).strip()
            if not acteur:
                continue

            # A1 — suffixe scénario cohérent
            if not acteur.endswith("_{}".format(sc)):
                msg = "acteur '{}' ne se termine pas par _{} (mauvais scénario ?)".format(acteur, sc)
                result.warning("narrative", fname, msg)
                issues_by_scenario.setdefault(sc, []).append({
                    "event": event_slug, "type": "acteur_mauvais_scenario", "message": msg
                })
                total_issues += 1

            # A2 — etat_temporel actif
            # Un acteur disparu/historique avec age_historique résiduel ou mythifié
            # est narrativement acceptable (trace passive, référence, symbole).
            RESIDUEL_AGES = {"résiduel", "mythifié"}
            meta = instances_meta.get(acteur)
            if meta:
                etat = meta.get("etat_temporel", "")
                age  = meta.get("age_historique", "")
                if etat in INACTIVE_ETATS and age not in RESIDUEL_AGES:
                    msg = "acteur '{}' a etat_temporel='{}' / age_historique='{}' — inactif dans l'événement".format(
                        acteur, etat, age or "(non défini)")
                    result.warning("narrative", fname, msg)
                    issues_by_scenario.setdefault(sc, []).append({
                        "event": event_slug, "type": "acteur_inactif", "message": msg
                    })
                    total_issues += 1

        # ── B. Vérification overflow delta/level
        impacts = fm.get("impact_sur_variables", []) or []
        for imp in impacts:
            if not isinstance(imp, dict):
                continue
            var = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(imp.get("variable", ""))).strip()
            if not var or var not in VALID_VARS:
                continue
            delta    = imp.get("delta_level", 0) or 0
            polarite = imp.get("polarite", 1) or 1
            delta_reel = delta * polarite

            if sc in var_levels and var in var_levels[sc]:
                level = float(var_levels[sc].get(var, 50) or 50)
                new_level = level + delta_reel
                if new_level < -20 or new_level > 130:
                    msg = "variable '{}' : level {} + delta {:+} = {} (hors [-20, 130] — probable erreur de saisie)".format(
                        var, int(level), int(delta_reel), int(new_level))
                    result.warning("narrative", fname, msg)
                    issues_by_scenario.setdefault(sc, []).append({
                        "event": event_slug, "type": "delta_overflow", "message": msg
                    })
                    total_issues += 1

    # ── C. Validation narrative des instances (annee_debut, annee_fin, etat_temporel)
    ETAT_INACTIFS = {"disparu", "transformé", "historique", "mythifié"}

    if os.path.exists(PATHS["instances"]):
        for fname in list_files(PATHS["instances"]):
            slug = fname.replace(".md", "")
            fm, _, _ = parse_md(os.path.join(PATHS["instances"], fname))
            if not fm:
                continue

            sc = fm.get("scenario", "")
            if sc not in VALID_SCENARIOS:
                continue

            etat       = fm.get("etat_temporel", "")
            annee_debut = fm.get("annee_debut")
            annee_fin   = fm.get("annee_fin")

            # C1 — annee_debut absent
            if not annee_debut:
                msg = "annee_debut absent"
                result.warning("narrative", fname, msg)
                issues_by_scenario.setdefault(sc, []).append({
                    "instance": slug, "type": "annee_debut_absent", "message": msg
                })
                total_issues += 1

            # C2 — annee_fin < annee_debut
            if annee_debut and annee_fin:
                try:
                    if int(annee_fin) < int(annee_debut):
                        msg = "annee_fin ({}) < annee_debut ({})".format(annee_fin, annee_debut)
                        result.error("narrative", fname, msg)
                        issues_by_scenario.setdefault(sc, []).append({
                            "instance": slug, "type": "annee_incoherente", "message": msg
                        })
                        total_issues += 1
                except (ValueError, TypeError):
                    pass

            # C3 — annee_fin ≤ 2097 mais etat_temporel actif
            if annee_fin:
                try:
                    if int(annee_fin) <= 2097 and etat and etat not in ETAT_INACTIFS:
                        msg = "annee_fin={} ≤ 2097 mais etat_temporel='{}' (attendu: disparu/transformé/historique/mythifié)".format(
                            annee_fin, etat)
                        result.warning("narrative", fname, msg)
                        issues_by_scenario.setdefault(sc, []).append({
                            "instance": slug, "type": "etat_incoherent_annee_fin", "message": msg
                        })
                        total_issues += 1
                except (ValueError, TypeError):
                    pass

            # C4 — etat_temporel disparu sans annee_fin
            if etat == "disparu" and not annee_fin:
                msg = "etat_temporel='disparu' mais annee_fin absent"
                result.warning("narrative", fname, msg)
                issues_by_scenario.setdefault(sc, []).append({
                    "instance": slug, "type": "disparu_sans_annee_fin", "message": msg
                })
                total_issues += 1

    # ── Générer le rapport YAML
    _generate_narrative_report(issues_by_scenario, total_issues)

    result.info("narrative",
        "{} problème(s) narratif(s) détecté(s) — voir narrative_issues.yaml".format(total_issues)
        if total_issues else "Cohérence narrative OK (0 problème)")


def _generate_narrative_report(issues_by_scenario, total_issues):
    """Génère documentation/need_action/narrative_issues.yaml."""
    os.makedirs(NEED_ACTION_DIR, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")

    data = {
        "generated": now,
        "total_issues": total_issues,
        "scenarios": {},
    }

    for sc in VALID_SCENARIOS:
        issues = issues_by_scenario.get(sc, [])
        if issues:
            data["scenarios"][sc] = issues

    with open(NARRATIVE_ISSUES_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ─────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────

def run(verbose=False, report=False, fix=False, localisation_only=False, narrative=False):
    result = ValidationResult()

    # Mode localisation uniquement
    if localisation_only:
        print("\n[validate] Mode --localisation : scan review_manuelle uniquement...")
        validate_localisation(result)
        print_results(result, verbose=verbose)
        if report:
            generate_report(result)
        return result

    print("\n[validate] Démarrage de la validation...")

    print("[validate] 1/9 — Nomenclature...")
    validate_nomenclature(result)

    print("[validate] 2/9 — Cohérence systémique...")
    validate_systemic(result)

    print("[validate] 3/9 — Entités et instances...")
    validate_entities(result)

    print("[validate] 4/9 — Thématiques...")
    validate_thematiques(result)

    print("[validate] 5/9 — Localisation...")
    validate_localisation(result)

    print("[validate] 6/9 — Références croisées...")
    validate_cross_references(result)

    print("[validate] 7/9 — Matrice d'influence...")
    validate_matrix(result)

    print("[validate] 8/9 — Événements...")
    validate_events(result)

    print("[validate] 9/9 — Cohérence narrative post-injection...")
    validate_narrative_coherence(result, force=narrative)

    print_results(result, verbose=verbose)

    if report:
        generate_report(result)

    # Mise à jour du timestamp de référence pour le scan narratif
    if result.ok:
        _update_last_validated()

    return result


# ─────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valide la cohérence de la base Ourrassol 2098"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Affiche le détail de tous les avertissements"
    )
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="Génère un rapport markdown dans le vault"
    )
    parser.add_argument(
        "--fix", "-f",
        action="store_true",
        help="Corrige automatiquement les problèmes mineurs"
    )
    parser.add_argument(
        "--localisation",
        action="store_true",
        help="Lance uniquement la validation localisation + génère localisation_review.md"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Validation complète (équivalent à lancer sans option)"
    )
    parser.add_argument(
        "--narrative", "-n",
        action="store_true",
        help="Force le scan de cohérence narrative même si aucune event_instance n'a changé"
    )
    args = parser.parse_args()

    result = run(verbose=args.verbose, report=args.report, fix=args.fix,
                 localisation_only=args.localisation, narrative=args.narrative)
    sys.exit(0 if result.ok else 1)
