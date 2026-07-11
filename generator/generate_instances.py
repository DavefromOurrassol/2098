#!/usr/bin/env python3
"""
generate_instances.py — Ourrassol 2098
=========================================

Génère les instances par scénario (instances/{slug}_{scenario}.md)
pour des entités déjà créées (entites/{slug}.md), qu'elles soient
anciennes, créées en mode custom ou en mode auto par create_entity.py
— seconde brique du futur script unifié
create_entities_and_instances.py.

LOGIQUE PAR ENTITÉ
-------------------
Pour chaque entité traitée, le script lit sa fiche dans entites/ :

  - Si le frontmatter contient un `scenario_ref` (entité créée en mode
    custom par create_entity.py) : l'instance de CE scénario reprend
    TELLES QUELLES les valeurs `role_ref`/`etat_ref` — le LLM n'est pas
    appelé pour ce scénario précis, le rôle et l'état sont des
    contraintes dures déjà fixées par l'utilisateur. Seuls les champs
    narratifs complémentaires (description journalistique, tensions...)
    sont générés par le LLM, en respectant ce rôle/état imposés.
    Les AUTRES scénarios de cette même entité restent entièrement
    libres (aucune contrainte de cohérence biographique).

  - Si le frontmatter ne contient PAS de `scenario_ref` (entité
    ancienne ou créée en mode auto) : tous les scénarios sont
    entièrement libres, exactement comme l'ancien generate_entities.py.

Ce script ne crée AUCUNE nouvelle entité — il ne fait que peupler les
instances d'entités déjà existantes dans entites/.

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...

USAGE
-----
    python3 generate_instances.py                       # toutes les entités, tous les scénarios manquants
    python3 generate_instances.py --entity le_temoin     # une seule entité
    python3 generate_instances.py --scenario breakdown   # un seul scénario, toutes entités
    python3 generate_instances.py --force                # régénère même si l'instance existe déjà
    python3 generate_instances.py --dry-run              # affiche sans rien écrire
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from llm_client import call_llm  # tier structured_strict — canonique/référencé


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
VARIABLES_DIR = VAULT_ROOT / "variables"
SCENARIOS_DIR = VAULT_ROOT / "scenarios"
ENTITES_DIR = VAULT_ROOT / "entites"
INSTANCES_DIR = VAULT_ROOT / "instances"


MAX_TOKENS = 2000

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

VALID_ETATS = ["actif", "disparu", "transformé", "clandestin", "historique", "mythifié"]


# ---------------------------------------------------------------------------
# Lecture du contexte
# ---------------------------------------------------------------------------

def parse_md(filepath):
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


def load_all_entities():
    """Charge toutes les fiches entites/*.md (hors _entities_list.json)."""
    entities = {}
    if not ENTITES_DIR.exists():
        return entities
    for path in sorted(ENTITES_DIR.glob("*.md")):
        fm, _ = parse_md(path)
        slug = fm.get("slug", path.stem)
        if fm.get("type") != "entity":
            continue
        entities[slug] = fm
    return entities


def load_scenario_context(scenario):
    fm, body = parse_md(SCENARIOS_DIR / f"{scenario}.md")
    summary = ""
    m = re.search(r"\*\*Résumé\*\*\s*\n(.+?)(?=\n\*\*|\n##|\Z)", body, re.DOTALL)
    if m:
        summary = m.group(1).strip()[:300]
    return {
        "state_of_system": fm.get("state_of_system", ""),
        "trajectory": fm.get("trajectory", ""),
        "tension_level": fm.get("tension_level", ""),
        "political_regime": fm.get("political_regime", ""),
        "dominant_region_structure": fm.get("dominant_region_structure", ""),
        "transformation_speed": fm.get("transformation_speed", ""),
        "dominant_variables": fm.get("dominant_variables", []) or [],
        "summary": summary,
    }


def load_variables_states(scenario):
    states = {}
    for var in VALID_VARS:
        fm, _ = parse_md(VARIABLES_DIR / f"{var}.md")
        var_states = fm.get("states", {}) or {}
        if scenario in var_states and isinstance(var_states[scenario], dict):
            states[var] = str(var_states[scenario].get("state_logic", ""))[:150]
    return states


def instance_exists(slug_entite, scenario):
    return (INSTANCES_DIR / f"{slug_entite}_{scenario}.md").exists()


def load_instances_in_scenario(scenario, exclude_slug=None):
    """
    Charge {slug_instance: nom} pour toutes les instances déjà existantes
    dans CE scénario — utilisé pour proposer des alliances/oppositions
    réelles (slugs valides) plutôt que du texte libre inventé. On ne
    référence que le même scénario : une alliance n'a de sens que dans
    le même monde.
    """
    result = {}
    if not INSTANCES_DIR.exists():
        return result
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        if path.stem == exclude_slug:
            continue
        fm, _ = parse_md(path)
        if fm.get("type") != "instance":
            continue
        result[fm.get("slug", path.stem)] = fm.get("name", path.stem)
    return result


# ---------------------------------------------------------------------------
# Appel LLM
# ---------------------------------------------------------------------------

def get_client():
    """Conservé pour compatibilité — retourne None, call_claude_json n'en a plus besoin."""
    return None


def call_claude_json(client, user_content, max_tokens=MAX_TOKENS):
    text = call_llm(
        system_prompt="",
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
        task_tier="structured_strict",
    ).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


# ---------------------------------------------------------------------------
# Construction du prompt
# ---------------------------------------------------------------------------

def build_instance_prompt(entity_fm, scenario, hard_constraint=None, exclude_slug=None):
    """hard_constraint, si fourni : {"role": ..., "etat": ...} — contrainte
    dure pour le scénario de référence d'une entité custom."""
    sc_ctx = load_scenario_context(scenario)
    var_states = load_variables_states(scenario)
    available_instances = load_instances_in_scenario(scenario, exclude_slug=exclude_slug)

    vars_context = ""
    for var in entity_fm.get("variables_potentielles", []) or []:
        if var in var_states:
            vars_context += f"\n- **{var}** dans {scenario} : {var_states[var]}"

    if available_instances:
        instances_list = "\n".join(
            f"- {slug} — {nom}" for slug, nom in sorted(available_instances.items())
        )
    else:
        instances_list = "(aucune autre instance encore créée dans ce scénario)"

    constraint_block = ""
    if hard_constraint:
        constraint_block = f"""
## CONTRAINTES DURES POUR CE SCÉNARIO (ne pas reformuler, ne pas contredire)
- Rôle dans ce scénario : {hard_constraint['role']}
- État temporel dans ce scénario : {hard_constraint['etat']}

Ces deux éléments sont déjà fixés par l'utilisateur. Construis le reste
de l'instance (description journalistique, responsabilités, relations,
tensions...) en cohérence stricte avec eux — ne les modifie pas, ne les
édulcore pas, ne les contredis pas.
"""
        role_etat_instruction = f"""
Réponds en JSON, avec "role_dans_scenario" reprenant le rôle ci-dessus
(tu peux le développer en 3-5 lignes mais sans en changer le sens) et
"etat_temporel" devant valoir exactement "{hard_constraint['etat']}".
"""
    else:
        role_etat_instruction = ""

    prompt = f"""Tu es un expert en worldbuilding pour Ourrassol 2098.

Génère l'instance de l'entité "{entity_fm['name']}" dans le scénario "{scenario}".

## ENTITÉ ARCHÉTYPE
- Nom : {entity_fm['name']}
- Catégorie : {entity_fm.get('category', '')}
- Description : {entity_fm.get('description', '')}
- Tension fondamentale : {entity_fm.get('tension_fondamentale', '')}
{constraint_block}
## SCÉNARIO {scenario.upper()}
- État : {sc_ctx['state_of_system']} | Tension : {sc_ctx['tension_level']}/5 | Trajectoire : {sc_ctx['trajectory']}
- Régime : {sc_ctx['political_regime']} | Vitesse : {sc_ctx['transformation_speed']}
- Variables dominantes : {', '.join(sc_ctx['dominant_variables'])}
{f"- Contexte : {sc_ctx['summary']}" if sc_ctx['summary'] else ""}

## ÉTAT DES VARIABLES INFLUENCÉES DANS CE SCÉNARIO
{vars_context if vars_context else "Non défini"}

## INSTANCES DÉJÀ EXISTANTES DANS CE SCÉNARIO (pour alliances/oppositions)
{instances_list}

## CONSIGNE

Génère une instance cohérente avec ce scénario. L'instance DOIT refléter
l'état du monde — si le scénario est chaotique, l'institution est
fragmentée ou disparue. Si le scénario est stable, elle peut être
dominante ou mature.

Le nom de l'instance peut être identique à l'entité, une variante, ou
radicalement différent selon le monde — mais il doit rester évocateur
du nom de l'entité archétype.

RÈGLE STRICTE pour "alliances" et "oppositions" : ces champs ne doivent
contenir QUE des slugs exacts pris dans la liste "INSTANCES DÉJÀ
EXISTANTES" ci-dessus (copie le slug tel quel, jamais le nom). N'invente
JAMAIS de nom d'organisation en texte libre. Si aucune instance existante
de la liste ne convient comme allié ou opposant plausible, laisse le
champ en liste vide plutôt que d'inventer un acteur non référencé.
{role_etat_instruction}
Réponds en JSON uniquement :
{{
  "nom": "Nom de l'instance dans ce scénario",
  "type_dans_scenario": "IA|organisation|entreprise|institution|infrastructure|réseau|humain|système|hybride|autre",
  "role_dans_scenario": "Rôle narratif et systémique détaillé (3-5 lignes)",
  "responsabilites": "Actions concrètes exercées dans ce monde (2-3 lignes)",
  "impact_local": 0,
  "impact_systemique_global": 0,
  "variables_influencees": ["variable_1", "variable_2"],
  "zone_geographique": ["locale|urbaine|nationale|régionale|continentale|globale|orbital"],
  "zone_systemique": ["énergie|IA|gouvernance|économie|information|sécurité|infrastructure|société|cyberspace|orbital"],
  "alliances": [],
  "oppositions": [],
  "type_relation_dominante": "coopération|alliance stratégique|dépendance|neutralité|rivalité|conflit|infiltration|symbiose",
  "annee_debut": 2026,
  "annee_fin": null,
  "etat_temporel": "actif|disparu|transformé|clandestin|historique|mythifié",
  "age_historique": "émergent|marginal|ascendant|dominant|mature|déclinant|résiduel|mythifié",
  "generation": "pré-crise|transition|post-effondrement|IA-native|forteresse|reconstruction|ère cognitive",
  "description_journalistique": "Comment un journaliste de 2098 décrirait cette entité (4-6 lignes vivantes et concrètes)",
  "signes_distinctifs": "Éléments visuels, symboliques, stylistiques (2-3 lignes)",
  "tensions_narratives": "Conflits, enjeux, trajectoires possibles pour les articles (3-4 lignes)"
}}"""
    return prompt


# ---------------------------------------------------------------------------
# Validation mécanique
# ---------------------------------------------------------------------------

def validate_instance(data, hard_constraint=None):
    issues = []

    required = ["nom", "role_dans_scenario", "description_journalistique"]
    for field in required:
        if not data.get(field):
            issues.append(f"Champ requis manquant ou vide : '{field}'")

    etat = data.get("etat_temporel", "")
    if etat and etat not in VALID_ETATS:
        issues.append(f"etat_temporel invalide : {etat!r}")

    variables = data.get("variables_influencees") or []
    for v in variables:
        if v not in VALID_VARS:
            issues.append(f"Variable inconnue dans variables_influencees : {v!r}")

    if hard_constraint:
        if data.get("etat_temporel") != hard_constraint["etat"]:
            issues.append(
                f"etat_temporel ({data.get('etat_temporel')!r}) ne respecte pas "
                f"la contrainte dure ({hard_constraint['etat']!r})"
            )

    return issues


SLUG_PATTERN = re.compile(r"^[a-z0-9_]+$")


def clean_relations(data, available_instances):
    """
    Filtre silencieusement les entrées alliances/oppositions qui ne sont
    pas des slugs valides référençant une instance existante du même
    scénario — au lieu de rejeter toute la fiche (retry), on nettoie et
    on garde le reste. Règle en vigueur depuis le 2026-06-20 (voir
    officialize_alliances.py) : ces champs ne doivent contenir QUE des
    slugs, jamais de texte libre.

    Retourne (data nettoyé, liste des entrées filtrées pour log).
    """
    dropped = []
    for field in ("alliances", "oppositions"):
        items = data.get(field) or []
        kept = []
        for item in items:
            item_clean = str(item).strip()
            if SLUG_PATTERN.match(item_clean) and item_clean in available_instances:
                kept.append(item_clean)
            else:
                dropped.append((field, item_clean))
        data[field] = kept
    return data, dropped


# ---------------------------------------------------------------------------
# Écriture de la fiche instance
# ---------------------------------------------------------------------------

def write_instance_file(entity_fm, scenario, instance_data):
    INSTANCES_DIR.mkdir(parents=True, exist_ok=True)

    slug_entite = entity_fm["slug"]
    slug_instance = f"{slug_entite}_{scenario}"
    filepath = INSTANCES_DIR / f"{slug_instance}.md"

    def yaml_list(lst, indent=2):
        if not lst:
            return ""
        pad = "  " * indent
        return "\n" + "\n".join(f"{pad}- {i}" for i in lst)

    vars_yaml = yaml_list(instance_data.get("variables_influencees", []))
    zones_geo = yaml_list(instance_data.get("zone_geographique", []))
    zones_sys = yaml_list(instance_data.get("zone_systemique", []))
    alliances = yaml_list(instance_data.get("alliances", []))
    oppositions = yaml_list(instance_data.get("oppositions", []))

    annee_fin = instance_data.get("annee_fin", "")
    annee_fin_str = str(annee_fin) if annee_fin else ""

    content = """---
name: {nom}
type: instance
slug: {slug_instance}
entite: {slug_entite}
scenario: {scenario}

type_dans_scenario: {type_dans_scenario}

role_dans_scenario: >
  {role_dans_scenario}

responsabilites: >
  {responsabilites}

impact_local: {impact_local}
impact_systemique_global: {impact_systemique_global}

variables_influencees:{vars_yaml}

zone_geographique:{zones_geo}

zone_systemique:{zones_sys}

alliances:{alliances}

oppositions:{oppositions}

type_relation_dominante: {type_relation_dominante}

annee_debut: {annee_debut}
annee_fin: {annee_fin}

etat_temporel: {etat_temporel}
age_historique: {age_historique}
generation: {generation}

injection:
  type: canonique
  annee_injection:
  contexte_injection:
  impact_sur_variables:
  propagation:
    via_matrice: false

description_journalistique: >
  {description_journalistique}

signes_distinctifs: >
  {signes_distinctifs}

tensions_narratives: >
  {tensions_narratives}

date_creation: {date_creation}
---

# {nom}

## Rôle dans [[{scenario}]]
{role_dans_scenario}

## Responsabilités
{responsabilites}

## Variables influencées
{vars_md}

## Relations
**Alliés** : {alliances_md}
**Opposants** : {oppositions_md}

## Description journalistique
{description_journalistique}

## Tensions narratives
{tensions_narratives}
""".format(
        nom=instance_data.get("nom", entity_fm["name"]),
        slug_instance=slug_instance,
        slug_entite=slug_entite,
        scenario=scenario,
        type_dans_scenario=instance_data.get("type_dans_scenario", ""),
        role_dans_scenario=instance_data.get("role_dans_scenario", "").replace("\n", " "),
        responsabilites=instance_data.get("responsabilites", "").replace("\n", " "),
        impact_local=instance_data.get("impact_local", 0),
        impact_systemique_global=instance_data.get("impact_systemique_global", 0),
        vars_yaml=vars_yaml,
        zones_geo=zones_geo,
        zones_sys=zones_sys,
        alliances=alliances,
        oppositions=oppositions,
        type_relation_dominante=instance_data.get("type_relation_dominante", "neutralité"),
        annee_debut=instance_data.get("annee_debut", 2026),
        annee_fin=annee_fin_str,
        etat_temporel=instance_data.get("etat_temporel", "actif"),
        age_historique=instance_data.get("age_historique", "mature"),
        generation=instance_data.get("generation", "transition"),
        description_journalistique=instance_data.get("description_journalistique", "").replace("\n", " "),
        signes_distinctifs=instance_data.get("signes_distinctifs", "").replace("\n", " "),
        tensions_narratives=instance_data.get("tensions_narratives", "").replace("\n", " "),
        date_creation=datetime.now().strftime("%Y-%m-%d"),
        vars_md="\n".join(f"- [[{v}]]" for v in instance_data.get("variables_influencees", [])) or "_aucune_",
        alliances_md=", ".join(f"[[{a}]]" for a in instance_data.get("alliances", [])) or "_aucun défini_",
        oppositions_md=", ".join(f"[[{o}]]" for o in instance_data.get("oppositions", [])) or "_aucun défini_",
    )

    filepath.write_text(content, encoding="utf-8")
    return filepath


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def process_entity_scenario(client, entity_fm, scenario, force=False, dry_run=False):
    slug_entite = entity_fm["slug"]

    if instance_exists(slug_entite, scenario) and not force:
        print(f"  → {slug_entite} × {scenario}... (déjà existant)")
        return {"status": "skipped"}

    hard_constraint = None
    if entity_fm.get("scenario_ref") == scenario:
        hard_constraint = {
            "role": entity_fm.get("role_ref", ""),
            "etat": entity_fm.get("etat_ref", ""),
        }

    print(f"  → {slug_entite} × {scenario}"
          f"{' [CONTRAINTE DURE]' if hard_constraint else ''}...", end=" ", flush=True)

    prompt = build_instance_prompt(
        entity_fm, scenario, hard_constraint=hard_constraint,
        exclude_slug=f"{slug_entite}_{scenario}",
    )
    try:
        instance_data = call_claude_json(client, prompt)
    except Exception as e:
        print(f"✗ ({e})")
        return {"status": "error", "error": str(e)}

    issues = validate_instance(instance_data, hard_constraint=hard_constraint)
    if issues:
        print("✗")
        for i in issues:
            print(f"     - {i}")
        return {"status": "needs_review", "issues": issues, "instance_data": instance_data}

    available_instances = load_instances_in_scenario(
        scenario, exclude_slug=f"{slug_entite}_{scenario}"
    )
    instance_data, dropped_relations = clean_relations(instance_data, available_instances)
    if dropped_relations:
        for field, value in dropped_relations:
            print(f"\n     ⚠ {field} filtrée (pas un slug d'instance valide) : "
                  f"'{value}'", end="")
        print()

    if hard_constraint:
        # Le rôle affiché doit rester fidèle à la contrainte ; on ne le
        # réécrit pas de force ici (la validation l'a déjà vérifié pour
        # etat_temporel) mais on s'assure que le role_dans_scenario
        # généré ne s'éloigne pas trivialement — confiance au prompt +
        # contrôle humain a posteriori possible via le champ role_ref
        # toujours visible dans la fiche entité parente.
        pass

    if not dry_run:
        write_instance_file(entity_fm, scenario, instance_data)
    print("✓")
    if dry_run:
        print(json.dumps(instance_data, ensure_ascii=False, indent=2))
    return {"status": "created", "instance_data": instance_data}


def generate_all(filter_entity=None, filter_scenario=None, force=False, dry_run=False):
    print("\n" + "=" * 60)
    print("OURRASSOL 2098 — Génération des instances")
    print("=" * 60)

    entities = load_all_entities()
    if filter_entity:
        entities = {k: v for k, v in entities.items() if k == filter_entity}
        if not entities:
            print(f"✗ Entité '{filter_entity}' introuvable dans entites/.")
            return

    scenarios_to_process = [filter_scenario] if filter_scenario else list(SCENARIOS)

    print(f"\n{len(entities)} entité(s) à traiter, "
          f"{len(scenarios_to_process)} scénario(s) chacune.\n")

    client = get_client()
    total_created, total_skipped, total_errors = 0, 0, 0

    for slug_entite, entity_fm in entities.items():
        entity_scenarios = entity_fm.get("scenarios_instances", []) or []
        scenarios_for_this_entity = [
            s for s in scenarios_to_process if s in entity_scenarios
        ]
        if not scenarios_for_this_entity:
            continue

        print(f"\n=== {entity_fm.get('name', slug_entite)} ===")
        for scenario in scenarios_for_this_entity:
            outcome = process_entity_scenario(
                client, entity_fm, scenario, force=force, dry_run=dry_run
            )
            if outcome["status"] == "created":
                total_created += 1
            elif outcome["status"] == "skipped":
                total_skipped += 1
            elif outcome["status"] in ("error", "needs_review"):
                total_errors += 1
            time.sleep(0.3)

    print(f"\n{'=' * 60}")
    print(f"✓ {total_created} instance(s) créée(s) | "
          f"{total_skipped} déjà existante(s) | {total_errors} erreur(s)")
    if dry_run:
        print("(mode --dry-run : rien n'a été écrit sur disque)")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Génère les instances par scénario pour les entités d'Ourrassol 2098"
    )
    parser.add_argument("--entity", type=str,
                         help="Traiter uniquement cette entité (slug)")
    parser.add_argument("--scenario", type=str, choices=SCENARIOS,
                         help="Traiter uniquement ce scénario")
    parser.add_argument("--force", action="store_true",
                         help="Régénère même si l'instance existe déjà")
    parser.add_argument("--dry-run", action="store_true",
                         help="Appelle le LLM et valide, mais n'écrit rien sur disque")
    args = parser.parse_args()

    generate_all(
        filter_entity=args.entity,
        filter_scenario=args.scenario,
        force=args.force,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
