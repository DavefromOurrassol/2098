#!/usr/bin/env python3
"""
enrich_minimal.py — Ourrassol 2098
====================================

Enrichit les fiches d'instances marquées `statut: officialise_minimal`
en générant via l'API Claude le contenu narratif manquant, puis met
à jour le statut en `officialise_enrichi`.

PRINCIPE
--------
1. Pour chaque fiche `officialise_minimal` d'un scénario donné, le
   script :
     - Charge le contexte : archétype entité, snapshot scénario,
       bible géographique, registre des événements
     - Appelle Claude pour générer tous les champs placeholder
     - Valide mécaniquement le résultat (localisation.zone, type_lieu,
       impact_local/global [0-5], variables_influencees, etat_temporel,
       zone_geographique, alliances/oppositions)
     - En cas d'échec de validation, rappelle Claude (max 2 retries)
     - Écrit la fiche enrichie sur disque (statut: officialise_enrichi)
     - Les fiches en échec après retries vont dans needs_review.yaml

2. Par défaut (mode 2 étapes), le cycle post-injection
   (extract_localisation → review_localisation → validate) n'est PAS
   lancé automatiquement. Utiliser --auto-cycle pour l'activer.

USAGE
-----
    python3 enrich_minimal.py --scenario new_sustainability
    python3 enrich_minimal.py --scenario new_sustainability --dry-run
    python3 enrich_minimal.py --scenario new_sustainability --slug SLUG
    python3 enrich_minimal.py --all
    python3 enrich_minimal.py --all --auto-cycle

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

from llm_client import call_llm, LLM_MODEL as MODEL


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
INSTANCES_DIR = VAULT_ROOT / "instances"
ENTITES_DIR = VAULT_ROOT / "entites"
SCENARIOS_DIR = VAULT_ROOT / "scenarios"
VARIABLES_DIR = VAULT_ROOT / "variables"
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"
REGISTRE_PATH = GENERATOR_DIR / "registre_evenements.md"
ENTITIES_LIST_PATH = ENTITES_DIR / "_entities_list.json"
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
REPORT_PATH = NEED_ACTION_DIR / "enrich_minimal_report.md"
NEEDS_REVIEW_PATH = VAULT_ROOT / "instances_custom" / "needs_review_enrich.yaml"
ENTITES_QUEUE_PATH = VAULT_ROOT / "entites_custom" / "queue.yaml"


MAX_FIX_ATTEMPTS = 2

SCENARIO_DESCRIPTIONS = {
    "breakdown": "effondrement des institutions, fragmentation géopolitique, survie locale",
    "fortress_world": "forteresses climatiques, murs entre zones riches et pauvres, surveillance totale",
    "new_sustainability": "transition écologique réussie, gouvernance mondiale coopérative",
    "eco_communalism": "retour au local, communautés autonomes, décroissance assumée",
    "policy_reform": "réformes institutionnelles progressives, démocratie renforcée",
    "reference": "continuité tendancielle, tensions non résolues, monde fragmenté",
}

SCENARIOS = [
    "breakdown",
    "fortress_world",
    "new_sustainability",
    "eco_communalism",
    "policy_reform",
    "reference",
]

VALID_VARS = [
    "systeme_economique_redistribution",
    "gouvernance_institutions",
    "geopolitique_conflits",
    "valeurs_culture_tempo_sociale",
    "organisation_territoires",
    "sante_biotechnologies",
    "frontieres_du_systeme",
    "technologie_information",
    "climat_environnement_global",
    "energie_ressources_critiques",
    "demographie_mobilite_humaine",
    "systemes_productifs_travail",
]

VALID_ETAT_TEMPOREL = [
    "actif", "disparu", "transformé", "clandestin", "historique", "mythifié"
]

VALID_ZONES_GEOGRAPHIQUES = [
    "locale", "urbaine", "nationale", "régionale", "continentale", "globale", "orbital",
]

VALID_TYPE_LIEU = ["ville", "region", "infrastructure", "site_strategique"]

VALID_AGE_HISTORIQUE = [
    "émergent", "marginal", "ascendant", "dominant",
    "mature", "déclinant", "résiduel", "mythifié"
]

VALID_GENERATION = ["fondateur", "transition", "natif", "post-effondrement"]


# ---------------------------------------------------------------------------
# Parsing utilitaires
# ---------------------------------------------------------------------------

def parse_md(filepath):
    """Parse un fichier .md : retourne (frontmatter_dict, body_str)."""
    if not filepath.exists():
        return {}, ""
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not m:
        return {}, raw
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2).strip()


def yaml_scalar(value):
    """Sérialise une valeur scalaire YAML en quotant les ':' et caractères spéciaux."""
    if value is None:
        return "null"
    dumped = yaml.dump(value, allow_unicode=True, default_flow_style=True).strip()
    if dumped.endswith("\n..."):
        dumped = dumped[:-3].strip()
    return dumped


def load_all_zones(scenario):
    """Charge toutes les zones d'un scénario depuis geographie/{scenario}.md."""
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    if not path.exists():
        return {}
    fm, _ = parse_md(path)
    zones_list = fm.get("zones", []) or []
    return {z["slug"]: z for z in zones_list if isinstance(z, dict) and "slug" in z}


def load_entities_list():
    """
    Retourne l'ensemble des slugs d'instances connus.
    Fusionne deux sources :
      1. _entities_list.json (registre permanent)
      2. Slugs réels des fichiers instances/*.md (couvre les entités
         créées par officialize_alliances.py ou autres scripts qui ne
         mettent pas à jour _entities_list.json)
    """
    slugs = set()

    # Source 1 : _entities_list.json
    if ENTITIES_LIST_PATH.exists():
        try:
            data = json.loads(ENTITIES_LIST_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for e in data:
                    if isinstance(e, dict) and e.get("slug"):
                        slugs.add(e["slug"])
        except Exception:
            pass

    # Source 2 : fichiers instances/*.md (slugs depuis le frontmatter)
    if INSTANCES_DIR.exists():
        for path in INSTANCES_DIR.glob("*.md"):
            fm, _ = parse_md(path)
            slug = fm.get("slug", "")
            if slug:
                slugs.add(slug)

    return slugs


# ---------------------------------------------------------------------------
# Chargement du contexte
# ---------------------------------------------------------------------------

def load_entite(entite_slug):
    """Charge l'archétype entité."""
    path = ENTITES_DIR / f"{entite_slug}.md"
    if not path.exists():
        return {}
    fm, body = parse_md(path)
    return {"frontmatter": fm, "body": body}


def load_scenario_context(scenario):
    """Charge le contexte narratif du scénario."""
    fm, body = parse_md(SCENARIOS_DIR / f"{scenario}.md")
    summary = ""
    m = re.search(r"\*\*Résumé\*\*\s*\n(.+?)(?=\n\*\*|\n##|\Z)", body, re.DOTALL)
    if m:
        summary = m.group(1).strip()[:400]
    return {
        "state_of_system": fm.get("state_of_system", ""),
        "trajectory": fm.get("trajectory", ""),
        "tension_level": fm.get("tension_level", ""),
        "political_regime": fm.get("political_regime", ""),
        "transformation_speed": fm.get("transformation_speed", ""),
        "dominant_variables": fm.get("dominant_variables", []) or [],
        "summary": summary,
    }


def load_variables_levels(scenario):
    """Charge les niveaux de variables pour ce scénario."""
    levels = {}
    for var in VALID_VARS:
        fm, _ = parse_md(VARIABLES_DIR / f"{var}.md")
        states = fm.get("states", {}) or {}
        if scenario in states and isinstance(states[scenario], dict):
            levels[var] = states[scenario].get("level", 50)
    return levels


def build_geographie_summary(scenario):
    """Résumé condensé de la bible géographique pour le prompt."""
    zones = load_all_zones(scenario)
    if not zones:
        return "(bible géographique non disponible)"
    lines = []
    # N1 d'abord
    n1 = [z for z in zones.values() if not z.get("parent")]
    for z in n1:
        lines.append(f"  N1 | {z['slug']} — {z.get('nom', '?')} ({z.get('statut', '')})")
    # N2/N3
    others = [z for z in zones.values() if z.get("parent")]
    for z in others[:60]:  # limiter la taille du prompt
        lines.append(f"  N{z.get('niveau', '?')} | {z['slug']} — {z.get('nom', '?')} (parent: {z.get('parent', '')})")
    if len(others) > 60:
        lines.append(f"  ... ({len(others) - 60} zones supplémentaires non listées)")
    return "\n".join(lines)


def build_registre_excerpt(scenario, variables_influencees):
    """Extrait pertinent du registre pour le scénario + variables concernées."""
    if not REGISTRE_PATH.exists():
        return "(registre non disponible)"
    text = REGISTRE_PATH.read_text(encoding="utf-8")
    # Chercher la section du scénario
    pattern = rf"## {re.escape(scenario)}\b.*?(?=\n## |\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not m:
        return "(section scénario absente du registre)"
    section = m.group(0)
    lines = section.split("\n")
    # Garder l'en-tête + les lignes qui touchent les variables concernées
    relevant = []
    for line in lines[:5]:  # en-tête tableau
        relevant.append(line)
    for line in lines[5:]:
        if any(v in line for v in (variables_influencees or [])):
            relevant.append(line)
    if len(relevant) > 30:
        relevant = relevant[:30]
        relevant.append("... (tronqué)")
    return "\n".join(relevant)


# ---------------------------------------------------------------------------
# Scan des fiches à enrichir
# ---------------------------------------------------------------------------

def find_minimal_fiches(scenario, slug_filter=None):
    """Retourne la liste des fiches officialise_minimal pour ce scénario."""
    result = []
    if not INSTANCES_DIR.exists():
        return result
    pattern = f"*_{scenario}.md" if scenario else "*.md"
    for path in sorted(INSTANCES_DIR.glob(pattern)):
        fm, body = parse_md(path)
        if fm.get("statut") != "officialise_minimal":
            continue
        if slug_filter and fm.get("slug", path.stem) != slug_filter:
            continue
        result.append({"path": path, "fm": fm, "body": body})
    return result


# ---------------------------------------------------------------------------
# Construction du prompt
# ---------------------------------------------------------------------------

def build_enrich_prompt(fiche, scenario, entite_data, scenario_ctx, var_levels, geo_summary, registre_excerpt):
    """Construit le prompt système + utilisateur pour enrichir une fiche."""
    fm = fiche["fm"]
    slug = fm.get("slug", fiche["path"].stem)
    name = fm.get("name", slug)
    role = fm.get("role_dans_scenario", "")
    variables = fm.get("variables_influencees", []) or []
    type_dans_scenario = fm.get("type_dans_scenario", "")
    annee_debut = fm.get("annee_debut", 2026)
    annee_fin = fm.get("annee_fin", "")
    etat_temporel = fm.get("etat_temporel", "actif")
    age_historique = fm.get("age_historique", "")
    generation = fm.get("generation", "")
    zone_geographique = fm.get("zone_geographique", [])

    entite_fm = entite_data.get("frontmatter", {})
    entite_body = entite_data.get("body", "")[:600]

    system_prompt = """Tu es l'assistant de worldbuilding du projet Ourrassol 2098.
Tu enrichis des fiches d'instances d'entités dans un simulateur de presse fictive set en 2098.
Tes réponses sont UNIQUEMENT du JSON valide, sans aucun texte avant ou après.
Ne mets pas de backticks ni de balises markdown autour du JSON."""

    user_prompt = f"""TÂCHE : Enrichir la fiche instance suivante pour le scénario {scenario}.

═══════════════════════════════════════════════════
FICHE À ENRICHIR
═══════════════════════════════════════════════════
slug: {slug}
name: {name}
type_dans_scenario: {type_dans_scenario}
scenario: {scenario}
role_dans_scenario: {role}
variables_influencees: {variables}
etat_temporel: {etat_temporel}
age_historique: {age_historique}
generation: {generation}
annee_debut: {annee_debut}
annee_fin: {annee_fin or "(non renseigné)"}
zone_geographique actuelle: {zone_geographique}

═══════════════════════════════════════════════════
ARCHÉTYPE ENTITÉ
═══════════════════════════════════════════════════
Nom: {entite_fm.get("name", "?")}
Catégorie: {entite_fm.get("category", "?")}
Description: {entite_fm.get("description", "")[:400]}
Tension fondamentale: {entite_fm.get("tension_fondamentale", "")[:200]}
Variables potentielles: {entite_fm.get("variables_potentielles", [])}

{entite_body}

═══════════════════════════════════════════════════
SCÉNARIO {scenario.upper()}
═══════════════════════════════════════════════════
state_of_system: {scenario_ctx.get("state_of_system", "")}
trajectory: {scenario_ctx.get("trajectory", "")}
tension_level: {scenario_ctx.get("tension_level", "")}
political_regime: {scenario_ctx.get("political_regime", "")}
dominant_variables: {scenario_ctx.get("dominant_variables", [])}
Résumé: {scenario_ctx.get("summary", "")}

Niveaux variables (0-100) :
{chr(10).join(f"  {v}: {lvl}" for v, lvl in var_levels.items())}

═══════════════════════════════════════════════════
GÉOGRAPHIE DU SCÉNARIO (slugs valides)
═══════════════════════════════════════════════════
{geo_summary}

═══════════════════════════════════════════════════
REGISTRE DES ÉVÉNEMENTS (extrait)
═══════════════════════════════════════════════════
{registre_excerpt}

═══════════════════════════════════════════════════
INSTRUCTIONS
═══════════════════════════════════════════════════
Génère un JSON avec EXACTEMENT ces champs :

{{
  "responsabilites": "Texte narratif décrivant les responsabilités concrètes de cette entité dans ce scénario. 2-4 phrases.",
  "description_journalistique": "Texte journalistique comme dans un article de presse de 2098 décrivant cette entité. 2-3 phrases percutantes.",
  "signes_distinctifs": "Ce qui rend cette entité unique et reconnaissable dans ce scénario. 1-2 phrases.",
  "tensions_narratives": "Les conflits, contradictions ou enjeux dramatiques propres à cette entité dans ce scénario. 2-3 phrases.",
  "role_dans_scenario_enrichi": "Version enrichie du rôle (optionnel — laisser null si le rôle actuel est déjà suffisamment développé)",
  "localisation": {{
    "zone": "slug_zone_valide_depuis_la_liste_ci_dessus_ou_null_si_transnationale",
    "lieu": "texte libre ex: São Paulo, ou null",
    "type_lieu": "ville|region|infrastructure|site_strategique ou null"
  }},
  "impact_local": <entier 0-5>,
  "impact_systemique_global": <entier 0-5>,
  "alliances": ["slug_instance_valide", ...],
  "oppositions": ["slug_instance_valide", ...],
  "zone_geographique": ["locale|urbaine|nationale|régionale|continentale|globale|orbital"],
  "type_relation_dominante": "coopération|compétition|neutralité|conflit|dépendance|symbiose"
}}

RÈGLES IMPÉRATIVES :
- localisation.zone DOIT être un slug exact de la liste ci-dessus, ou null si entité transnationale sans ancrage précis
- impact_local et impact_systemique_global : entiers entre 0 et 5 INCLUS
- alliances/oppositions : uniquement des slugs d'instances réelles de ce scénario, ou tableau vide []
- IMPORTANT : chaque slug dans alliances/oppositions DOIT obligatoirement se terminer par _{scenario} (ex: mon_entite_{scenario}). Ne jamais omettre ce suffixe.
- zone_geographique : liste avec au moins une valeur parmi les 7 valeurs autorisées
- Tous les textes en français, cohérents avec l'univers 2098 et le scénario {scenario}
- Respecter l'etat_temporel, l'age_historique et la generation existants
"""
    return system_prompt, user_prompt


# ---------------------------------------------------------------------------
# Appel API
# ---------------------------------------------------------------------------

def get_client():
    """Conservé pour compatibilité — retourne None, call_claude_json n'en a plus besoin."""
    return None


def call_claude_json(client, system, user_content, max_tokens=2000):
    """Appelle le LLM configuré et retourne le contenu JSON parsé."""
    raw = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
    ).strip()
    # Nettoyer les éventuels backticks
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()
    # raw_decode pour ignorer le texte après le JSON
    try:
        data, _ = json.JSONDecoder().raw_decode(raw)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON invalide : {e}\nRaw : {raw[:300]}")


def call_claude_fix(client, system, user_content, issues, previous_json, max_tokens=2000):
    """Appelle Claude avec les erreurs de validation pour correction."""
    fix_content = f"""{user_content}

═══════════════════════════════════════════════════
CORRECTION REQUISE
═══════════════════════════════════════════════════
Ta réponse précédente contenait ces erreurs de validation :
{chr(10).join(f"  - {i}" for i in issues)}

JSON précédent :
{json.dumps(previous_json, ensure_ascii=False, indent=2)[:1000]}

Corrige UNIQUEMENT les champs en erreur. Retourne le JSON complet corrigé.
"""
    return call_claude_json(client, system, fix_content, max_tokens)


# ---------------------------------------------------------------------------
# Validation mécanique
# ---------------------------------------------------------------------------

def validate_enriched(data, scenario, zones_dict, entities_set):
    """
    Valide les champs générés par Claude.
    Retourne (errors, warnings) — errors bloquants, warnings informatifs.
    """
    errors = []
    warnings = []

    # Champs texte requis
    for field in ["responsabilites", "description_journalistique", "signes_distinctifs", "tensions_narratives"]:
        val = data.get(field, "")
        if not val or str(val).strip().startswith("(à développer"):
            errors.append(f"Champ '{field}' manquant ou placeholder non remplacé")

    # localisation
    loc = data.get("localisation")
    if loc is None:
        errors.append("Champ 'localisation' absent")
    elif isinstance(loc, dict):
        zone = loc.get("zone")
        if zone and zone != "null" and zone not in zones_dict:
            errors.append(f"localisation.zone '{zone}' n'existe pas dans geographie/{scenario}.md")
        type_lieu = loc.get("type_lieu")
        if type_lieu and type_lieu not in VALID_TYPE_LIEU:
            errors.append(f"localisation.type_lieu '{type_lieu}' invalide (valeurs: {VALID_TYPE_LIEU})")

    # impact_local / impact_systemique_global
    for field in ["impact_local", "impact_systemique_global"]:
        val = data.get(field)
        if val is None:
            errors.append(f"Champ '{field}' absent")
        else:
            try:
                v = int(val)
                if not (0 <= v <= 5):
                    errors.append(f"'{field}' = {v} hors plage [0-5]")
            except (TypeError, ValueError):
                errors.append(f"'{field}' = {val!r} n'est pas un entier")

    # zone_geographique
    zones_geo = data.get("zone_geographique", [])
    if not zones_geo:
        errors.append("'zone_geographique' absent ou vide")
    elif isinstance(zones_geo, list):
        for z in zones_geo:
            z_clean = str(z).strip()
            if z_clean and z_clean not in VALID_ZONES_GEOGRAPHIQUES:
                errors.append(f"zone_geographique '{z_clean}' invalide (valeurs: {VALID_ZONES_GEOGRAPHIQUES})")

    # alliances / oppositions (warnings non bloquants si slug inconnu)
    for field in ["alliances", "oppositions"]:
        slugs = data.get(field, []) or []
        if not isinstance(slugs, list):
            errors.append(f"'{field}' doit être une liste")
            continue
        for s in slugs:
            if not isinstance(s, str):
                continue
            # Vérifier suffixe scénario
            if not s.endswith(f"_{scenario}"):
                warnings.append(f"{field}: '{s}' ne porte pas le suffixe _{scenario}")
            # Vérifier contre entities_list
            if entities_set and s not in entities_set:
                warnings.append(f"{field}: '{s}' non trouvé dans _entities_list.json")

    # type_relation_dominante
    valid_relations = ["coopération", "compétition", "neutralité", "conflit", "dépendance", "symbiose"]
    rel = data.get("type_relation_dominante", "")
    if rel and rel not in valid_relations:
        warnings.append(f"type_relation_dominante '{rel}' non standard (valeurs: {valid_relations})")

    return errors, warnings


# ---------------------------------------------------------------------------
# Écriture de la fiche enrichie
# ---------------------------------------------------------------------------

def write_enriched_fiche(path, original_fm, original_body, enriched_data, dry_run=False):
    """
    Réécrit la fiche avec les données enrichies.
    Conserve tous les champs existants, remplace/ajoute les champs enrichis.
    """
    fm = dict(original_fm)

    # Mise à jour du statut
    fm["statut"] = "officialise_enrichi"

    # Champs texte enrichis
    for field in ["responsabilites", "description_journalistique", "signes_distinctifs", "tensions_narratives"]:
        val = enriched_data.get(field)
        if val:
            fm[field] = str(val).strip()

    # role_dans_scenario optionnel
    role_enrichi = enriched_data.get("role_dans_scenario_enrichi")
    if role_enrichi and str(role_enrichi).strip() and str(role_enrichi).strip() != "null":
        fm["role_dans_scenario"] = str(role_enrichi).strip()

    # localisation
    loc = enriched_data.get("localisation")
    if isinstance(loc, dict):
        zone = loc.get("zone")
        if zone == "null" or zone == "":
            zone = None
        lieu = loc.get("lieu")
        if lieu == "null" or lieu == "":
            lieu = None
        type_lieu = loc.get("type_lieu")
        if type_lieu == "null" or type_lieu == "":
            type_lieu = None
        fm["localisation"] = {
            "zone": zone,
            "lieu": lieu,
            "type_lieu": type_lieu,
        }

    # impact scores
    for field in ["impact_local", "impact_systemique_global"]:
        val = enriched_data.get(field)
        if val is not None:
            try:
                fm[field] = int(val)
            except (TypeError, ValueError):
                pass

    # alliances / oppositions
    for field in ["alliances", "oppositions"]:
        val = enriched_data.get(field)
        if isinstance(val, list):
            fm[field] = val

    # zone_geographique
    zg = enriched_data.get("zone_geographique")
    if isinstance(zg, list) and zg:
        fm["zone_geographique"] = zg

    # type_relation_dominante
    rel = enriched_data.get("type_relation_dominante")
    if rel:
        fm["type_relation_dominante"] = rel

    # Reconstruire le body Markdown
    name = fm.get("name", fm.get("slug", ""))
    scenario = fm.get("scenario", "")
    entite_slug = fm.get("entite", "")

    body_lines = [
        f"# {name}",
        "",
        f"## Rôle dans [[{scenario}]]",
        fm.get("role_dans_scenario", "").strip(),
        "",
        "## Responsabilités",
        fm.get("responsabilites", "").strip(),
        "",
        "## Description journalistique",
        fm.get("description_journalistique", "").strip(),
        "",
        "## Signes distinctifs",
        fm.get("signes_distinctifs", "").strip(),
        "",
        "## Tensions narratives",
        fm.get("tensions_narratives", "").strip(),
        "",
        "## Variables influencées",
    ]
    for v in fm.get("variables_influencees", []) or []:
        body_lines.append(f"- [[{v}]]")

    alliances = fm.get("alliances", []) or []
    oppositions = fm.get("oppositions", []) or []
    if alliances or oppositions:
        body_lines.append("")
        body_lines.append("## Relations")
        if alliances:
            body_lines.append("**Alliés :**")
            for a in alliances:
                body_lines.append(f"- [[{a}]]")
        if oppositions:
            body_lines.append("**Opposants :**")
            for o in oppositions:
                body_lines.append(f"- [[{o}]]")

    body_lines.append("")
    body_lines.append("## Notes")
    body_lines.append(f"Fiche enrichie depuis officialise_minimal le {datetime.now().strftime('%Y-%m-%d')}.")

    new_body = "\n".join(body_lines)

    # Sérialiser le frontmatter
    fm_str = yaml.dump(
        fm,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )

    content = f"---\n{fm_str}---\n\n{new_body}\n"

    if not dry_run:
        path.write_text(content, encoding="utf-8")

    return content


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

class EnrichReport:
    def __init__(self):
        self.total = 0
        self.enriched = 0
        self.failed = 0
        self.skipped = 0
        self.needs_review = []
        self.warnings_all = []
        self.start_time = datetime.now()

    def add_enriched(self, slug, scenario, warnings):
        self.total += 1
        self.enriched += 1
        if warnings:
            self.warnings_all.append({"slug": slug, "scenario": scenario, "warnings": warnings})

    def add_failed(self, slug, scenario, errors, last_data):
        self.total += 1
        self.failed += 1
        self.needs_review.append({
            "slug": slug,
            "scenario": scenario,
            "errors": errors,
            "last_data": last_data,
        })

    def add_skipped(self, slug, reason):
        self.total += 1
        self.skipped += 1

    def write(self, dry_run=False):
        NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
        elapsed = (datetime.now() - self.start_time).seconds
        lines = [
            "# Rapport d'enrichissement — officialise_minimal",
            "",
            f"Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')} "
            f"{'(dry-run)' if dry_run else ''}",
            "",
            "## Résumé",
            "",
            f"| Statut | Nombre |",
            f"|---|---|",
            f"| ✅ Enrichies | {self.enriched} |",
            f"| ❌ Échec (needs_review) | {self.failed} |",
            f"| ⏭ Ignorées | {self.skipped} |",
            f"| **Total** | **{self.total}** |",
            "",
            f"Durée : {elapsed}s",
            "",
        ]

        if self.warnings_all:
            lines += [
                "## Avertissements",
                "",
            ]
            for entry in self.warnings_all:
                lines.append(f"### {entry['slug']} ({entry['scenario']})")
                for w in entry["warnings"]:
                    lines.append(f"- ⚠️ {w}")
                lines.append("")

        if self.needs_review:
            lines += [
                "## Fiches en échec",
                "",
                "Ces fiches n'ont pas pu être enrichies après les retries.",
                "Elles sont dans `needs_review_enrich.yaml`.",
                "",
            ]
            for entry in self.needs_review:
                lines.append(f"### {entry['slug']} ({entry['scenario']})")
                for e in entry["errors"]:
                    lines.append(f"- ❌ {e}")
                lines.append("")

        if not dry_run:
            REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
            print(f"\n→ Rapport écrit : {REPORT_PATH}")

        return "\n".join(lines)

    def write_needs_review(self, dry_run=False):
        if not self.needs_review or dry_run:
            return
        NEEDS_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing = []
        if NEEDS_REVIEW_PATH.exists():
            try:
                data = yaml.safe_load(NEEDS_REVIEW_PATH.read_text(encoding="utf-8")) or {}
                existing = data.get("needs_review", [])
            except Exception:
                pass
        new_entries = []
        for entry in self.needs_review:
            new_entries.append({
                "slug": entry["slug"],
                "scenario": entry["scenario"],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "errors": entry["errors"],
            })
        all_entries = existing + new_entries
        content = yaml.dump(
            {"needs_review": all_entries},
            allow_unicode=True,
            default_flow_style=False,
        )
        NEEDS_REVIEW_PATH.write_text(content, encoding="utf-8")
        print(f"→ {len(new_entries)} fiches ajoutées à {NEEDS_REVIEW_PATH}")


# ---------------------------------------------------------------------------
# Traitement d'une fiche
# ---------------------------------------------------------------------------

def enrich_fiche(client, fiche, scenario, zones_dict, entities_set, dry_run=False):
    """
    Enrichit une fiche officialise_minimal.
    Retourne (success, enriched_data, errors, warnings).
    """
    fm = fiche["fm"]
    slug = fm.get("slug", fiche["path"].stem)
    entite_slug = fm.get("entite", slug.replace(f"_{scenario}", ""))
    variables_influencees = fm.get("variables_influencees", []) or []

    print(f"  → {slug}")

    # Charger le contexte
    entite_data = load_entite(entite_slug)
    scenario_ctx = load_scenario_context(scenario)
    var_levels = load_variables_levels(scenario)
    geo_summary = build_geographie_summary(scenario)
    registre_excerpt = build_registre_excerpt(scenario, variables_influencees)

    system_prompt, user_prompt = build_enrich_prompt(
        fiche, scenario, entite_data, scenario_ctx, var_levels, geo_summary, registre_excerpt
    )

    # Appel initial
    try:
        data = call_claude_json(client, system_prompt, user_prompt)
    except ValueError as e:
        return False, None, [f"Parsing JSON échoué : {e}"], []

    errors, warnings = validate_enriched(data, scenario, zones_dict, entities_set)

    # Retries si erreurs
    attempt = 0
    while errors and attempt < MAX_FIX_ATTEMPTS:
        attempt += 1
        print(f"    [retry {attempt}/{MAX_FIX_ATTEMPTS}] {len(errors)} erreur(s)")
        try:
            data = call_claude_fix(client, system_prompt, user_prompt, errors, data)
        except ValueError as e:
            errors = [f"Parsing JSON échoué à la correction : {e}"]
            break
        errors, warnings = validate_enriched(data, scenario, zones_dict, entities_set)

    if errors:
        print(f"    [ÉCHEC] {len(errors)} erreur(s) persistante(s)")
        for e in errors:
            print(f"      - {e}")
        return False, data, errors, warnings

    # Écrire la fiche
    if not dry_run:
        write_enriched_fiche(fiche["path"], fm, fiche["body"], data, dry_run=False)
        print(f"    ✓ enrichi")
    else:
        print(f"    ✓ (dry-run) validation OK")

    if warnings:
        for w in warnings:
            print(f"    ⚠ {w}")

    return True, data, [], warnings


# ---------------------------------------------------------------------------
# Extraction et queue des slugs fantômes
# ---------------------------------------------------------------------------

def _slug_to_name(slug, scenario):
    """Convertit un slug en nom propre lisible."""
    if scenario and slug.endswith(f"_{scenario}"):
        base = slug[:-(len(scenario) + 1)]
    else:
        base = slug
    return base.replace("_", " ").strip().title()


def _infer_category(slug):
    """Infère grossièrement la catégorie depuis le slug."""
    s = slug.lower()
    if any(w in s for w in ["collectif", "communaute", "mouvement", "faction", "ligue", "front", "reseau", "coalition"]):
        return "organisation"
    if any(w in s for w in ["autorite", "agence", "conseil", "parlement", "bureau", "commission", "comite", "institution"]):
        return "institution"
    if any(w in s for w in ["zone", "district", "enclave", "delta", "vallee", "massif", "corridor", "arctique", "sahel", "rust_belt"]):
        return "territoire"
    if any(w in s for w in ["compagnie", "consortium", "corp", "industries", "holdings"]):
        return "corporation"
    return "organisation"


def _generate_roles_for_phantoms(client, entries):
    """Génère les rôles via API Claude en lots de 20."""
    BATCH_SIZE = 5
    batches = [entries[i:i+BATCH_SIZE] for i in range(0, len(entries), BATCH_SIZE)]
    print(f"  → Génération des rôles ({len(batches)} lot(s))...")

    for i, batch in enumerate(batches):
        print(f"    Lot {i+1}/{len(batches)}...")
        items = []
        for idx, e in enumerate(batch):
            sc = e.get("scenario_ref", "reference")
            items.append({
                "index": idx,
                "slug": e.get("_slug_corrige", e.get("_slug_fantome_original", "")),
                "nom": e["nom"],
                "scenario": sc,
                "scenario_desc": SCENARIO_DESCRIPTIONS.get(sc, sc),
                "category": e["category"],
            })

        prompt = f"""Tu es l'assistant de worldbuilding du projet Ourrassol 2098 — simulateur de presse fictive en 2098.
Ces entités ont été référencées dans des alliances/oppositions entre acteurs du monde de 2098.
Pour chacune, génère un rôle concis (2-3 phrases) cohérent avec son nom, sa catégorie et son scénario.
Réponds UNIQUEMENT avec un JSON valide : liste d'objets {{"index": N, "role": "...", "etat": "actif|clandestin|transformé"}}.
Pas de texte avant ou après. Pas de backticks.

Entités :
{json.dumps(items, ensure_ascii=False, indent=2)}"""

        try:
            raw = call_llm(
                system_prompt="",
                user_prompt=prompt,
                max_tokens=2000,
                temperature=0.0,
            ).strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw).strip()
            results, _ = json.JSONDecoder().raw_decode(raw)
            for r in results:
                idx = r.get("index")
                if idx is not None and 0 <= idx < len(batch):
                    batch[idx]["role"] = r.get("role", batch[idx]["role"])
                    if r.get("etat"):
                        batch[idx]["etat"] = r["etat"]
        except Exception as e:
            print(f"    [WARN] Lot {i+1} échoué : {e} — rôles laissés vides")

    return entries


def _extract_phantoms_from_validate():
    """
    Lance validate.py --verbose et extrait les slugs fantômes alliances/oppositions.
    Retourne un dict key -> info (même format que raw_phantoms dans extract_and_queue_phantoms).
    """
    validate_path = GENERATOR_DIR / "validate.py"
    if not validate_path.exists():
        return {}

    try:
        result = subprocess.run(
            [sys.executable, str(validate_path), "--verbose"],
            capture_output=True,
            text=True,
            cwd=str(GENERATOR_DIR),
        )
        output = result.stdout + result.stderr
    except Exception as e:
        print(f"  [WARN] validate.py échoué : {e}")
        return {}

    line_pattern = re.compile(
        r"(\S+\.md)\s+—\s+référence\s+(alliances|oppositions)\s+'([^']+)'\s+ressemble"
    )
    raw = {}
    for line in output.splitlines():
        m = line_pattern.search(line)
        if not m:
            continue
        fiche_file, _rel_type, slug = m.group(1), m.group(2), m.group(3)
        parent_scenario = None
        for sc in SCENARIOS:
            if fiche_file.replace(".md", "").endswith(f"_{sc}"):
                parent_scenario = sc
                break
        scenario = None
        for sc in SCENARIOS:
            if slug.endswith(f"_{sc}"):
                scenario = sc
                break
        if scenario is None:
            scenario = parent_scenario

        key = f"{slug}|{scenario}"
        if key not in raw:
            raw[key] = {"slug": slug, "scenario": scenario, "mentions": 1,
                        "has_suffix": any(slug.endswith(f"_{sc}") for sc in SCENARIOS)}
        else:
            raw[key]["mentions"] += 1

    return raw


def _queue_phantoms(client, raw_phantoms, source_label="unknown", dry_run=False):
    """
    Prend un dict raw_phantoms et l'ajoute à entites_custom/queue.yaml.
    Factorisation partagée entre vague 1 (enrich) et vague 2 (validate).
    """
    real_slugs = set()
    if INSTANCES_DIR.exists():
        for p in INSTANCES_DIR.glob("*.md"):
            real_slugs.add(p.stem)

    entries = []
    for key, info in sorted(raw_phantoms.items()):
        slug = info["slug"]
        scenario = info["scenario"]
        has_suffix = any(slug.endswith(f"_{sc}") for sc in SCENARIOS)

        if slug in real_slugs:
            continue

        slug_corrige = slug if has_suffix else f"{slug}_{scenario}"
        name = _slug_to_name(slug, scenario)

        entries.append({
            "nom": name,
            "category": _infer_category(slug),
            "role": f"(à définir — entité référencée dans les alliances/oppositions du scénario {scenario})",
            "etat": "actif",
            "scenario_ref": scenario,
            "scenario_hint": [scenario],
            "source": f"phantom_{source_label}_{datetime.now().strftime('%Y-%m-%d')}",
            "_slug_fantome_original": slug,
            "_slug_corrige": slug_corrige,
            "_mentions": info["mentions"],
            "_source": source_label,
        })

    print(f"  {len(entries)} nouvelles entrées à queuer")

    if not entries:
        return

    if not dry_run:
        entries = _generate_roles_for_phantoms(client, entries)
        existing = []
        if ENTITES_QUEUE_PATH.exists():
            try:
                data = yaml.safe_load(ENTITES_QUEUE_PATH.read_text(encoding="utf-8")) or {}
                existing = data.get("queue", []) or []
            except Exception:
                pass
        existing_slugs = {e.get("_slug_corrige", e.get("_slug_fantome_original", "")) for e in existing}
        new_entries = [e for e in entries if e.get("_slug_corrige", e.get("_slug_fantome_original", "")) not in existing_slugs]
        all_entries = existing + new_entries
        ENTITES_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        ENTITES_QUEUE_PATH.write_text(
            yaml.dump({"queue": all_entries}, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8"
        )
        print(f"  ✓ {len(new_entries)} entrées ajoutées à {ENTITES_QUEUE_PATH}")
    else:
        print(f"  (dry-run) {len(entries)} entrées seraient ajoutées")


def extract_and_queue_phantoms(client, report, dry_run=False):
    """
    Après un run enrich_minimal, extrait les slugs fantômes vague 1
    (depuis warnings du run) et les ajoute à entites_custom/queue.yaml.
    """
    phantom_pattern = re.compile(r"(?:alliances|oppositions): '([^']+)' non trouvé")
    raw_phantoms = {}

    for entry in report.warnings_all:
        fiche_scenario = entry["scenario"]
        for w in entry["warnings"]:
            m = phantom_pattern.search(w)
            if not m:
                continue
            slug = m.group(1)
            scenario = None
            for sc in SCENARIOS:
                if slug.endswith(f"_{sc}"):
                    scenario = sc
                    break
            if scenario is None:
                scenario = fiche_scenario
            key = f"{slug}|{scenario}"
            if key not in raw_phantoms:
                raw_phantoms[key] = {"slug": slug, "scenario": scenario, "mentions": 1}
            else:
                raw_phantoms[key]["mentions"] += 1

    if not raw_phantoms:
        return

    print(f"\n{'─' * 60}")
    print(f"SLUGS FANTÔMES VAGUE 1 (enrich) — {len(raw_phantoms)} détectés")
    print(f"{'─' * 60}")
    _queue_phantoms(client, raw_phantoms, source_label="enrich", dry_run=dry_run)


# ---------------------------------------------------------------------------
# Cycle post-enrichissement
# ---------------------------------------------------------------------------

def run_post_cycle():
    """Lance extract_localisation → review_localisation --auto-resolve → validate."""
    steps = [
        ("extract_localisation", [sys.executable, str(GENERATOR_DIR / "extract_localisation.py")]),
        ("review_localisation",  [sys.executable, str(GENERATOR_DIR / "review_localisation.py"), "--auto-resolve"]),
        ("validate",             [sys.executable, str(GENERATOR_DIR / "validate.py")]),
    ]
    print("\n" + "═" * 60)
    print("CYCLE POST-ENRICHISSEMENT")
    print("═" * 60)
    for name, cmd in steps:
        print(f"\n→ {' '.join(cmd[1:])}")
        result = subprocess.run(cmd, cwd=str(GENERATOR_DIR))
        if result.returncode != 0:
            print(f"  [WARN] {name} s'est terminé avec le code {result.returncode}.")
            print("  → Vérifiez manuellement avant de continuer.")
            break
    else:
        print("\n✓ Cycle post-enrichissement terminé.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_scenario(client, scenario, slug_filter, dry_run, report, limit=None):
    """Traite toutes les fiches officialise_minimal d'un scénario."""
    print(f"\n{'═' * 60}")
    print(f"SCÉNARIO : {scenario.upper()}")
    print(f"{'═' * 60}")

    fiches = find_minimal_fiches(scenario, slug_filter)
    if not fiches:
        msg = f"(aucune fiche officialise_minimal"
        if slug_filter:
            msg += f" avec slug '{slug_filter}'"
        msg += ")"
        print(f"  {msg}")
        return

    total_disponibles = len(fiches)
    if limit:
        fiches = fiches[:limit]
        print(f"  {total_disponibles} fiche(s) disponibles — traitement limité à {len(fiches)} (--limit {limit})")
    else:
        print(f"  {len(fiches)} fiche(s) à enrichir")

    zones_dict = load_all_zones(scenario)
    entities_set = load_entities_list()

    for fiche in fiches:
        fm = fiche["fm"]
        slug = fm.get("slug", fiche["path"].stem)

        # Skip si déjà enrichi (sécurité)
        if fm.get("statut") == "officialise_enrichi":
            report.add_skipped(slug, "déjà enrichi")
            continue

        success, data, errors, warnings = enrich_fiche(
            client, fiche, scenario, zones_dict, entities_set, dry_run
        )

        if success:
            report.add_enriched(slug, scenario, warnings)
        else:
            report.add_failed(slug, scenario, errors, data)


def main():
    parser = argparse.ArgumentParser(
        description="Enrichit les fiches officialise_minimal via l'API Claude."
    )
    parser.add_argument("--scenario", help="Scénario à traiter (ex: new_sustainability)")
    parser.add_argument("--all", action="store_true", help="Traite tous les scénarios")
    parser.add_argument("--slug", help="Traite uniquement une fiche par son slug")
    parser.add_argument("--dry-run", action="store_true",
                        help="Appelle Claude et valide, mais n'écrit rien sur disque")
    parser.add_argument("--auto-cycle", action="store_true",
                        help="Lance automatiquement le cycle post-enrichissement")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limite le nombre de fiches traitées (ex: --limit 3)")
    args = parser.parse_args()

    if not args.scenario and not args.all:
        parser.error("Spécifier --scenario NOM ou --all")

    print("=" * 60)
    print("OURRASSOL 2098 — Enrichissement fiches officialise_minimal")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)")

    client = get_client()
    report = EnrichReport()

    scenarios_to_run = SCENARIOS if args.all else [args.scenario]

    for scenario in scenarios_to_run:
        if scenario not in SCENARIOS:
            print(f"[WARN] Scénario inconnu : {scenario} — ignoré")
            continue
        run_scenario(client, scenario, args.slug, args.dry_run, report, limit=args.limit)

    # Résumé
    print(f"\n{'═' * 60}")
    print(f"RÉSUMÉ")
    print(f"{'═' * 60}")
    print(f"  Enrichies : {report.enriched}")
    print(f"  Échecs    : {report.failed}")
    print(f"  Ignorées  : {report.skipped}")
    print(f"  Total     : {report.total}")

    if not args.dry_run:
        report.write(dry_run=False)
        report.write_needs_review(dry_run=False)
    else:
        print("\n(dry-run — rapport non écrit)")

    # Extraction slugs fantômes vague 1 (depuis warnings du run)
    if report.warnings_all:
        extract_and_queue_phantoms(client, report, dry_run=args.dry_run)

    # Cycle post-enrichissement
    if not args.dry_run and report.enriched > 0:
        if args.auto_cycle:
            run_post_cycle()
            # Extraction slugs fantômes vague 2 (depuis validate après cycle)
            validate_phantoms = _extract_phantoms_from_validate()
            if validate_phantoms:
                print(f"\n{'─' * 60}")
                print(f"SLUGS FANTÔMES VAGUE 2 (validate) — {len(validate_phantoms)} détectés")
                print(f"{'─' * 60}")
                _queue_phantoms(client, validate_phantoms, source_label="validate")
        else:
            print("\n" + "─" * 60)
            print("Cycle post-enrichissement non lancé automatiquement.")
            print("Inspecter le rapport, puis lancer manuellement :")
            print("  python3 extract_localisation.py")
            print("  python3 review_localisation.py --auto-resolve")
            print("  python3 validate.py")
            print("Ou relancer avec --auto-cycle pour automatiser.")
            print("Pour les slugs fantômes vague 2, lancer ensuite :")
            print("  python3 extract_phantom_slugs.py --source validate")


if __name__ == "__main__":
    main()
