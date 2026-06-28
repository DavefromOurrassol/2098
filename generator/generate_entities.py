"""
generate_entities.py
--------------------
Génère automatiquement les entités et leurs instances
pour tous les scénarios via l'API Claude.

Usage :
    # Générer toutes les entités + instances
    python3 generate_entities.py

    # Générer uniquement les entités (sans instances)
    python3 generate_entities.py --entities-only

    # Générer les instances d'une entité spécifique
    python3 generate_entities.py --entity conseil_regulation_algorithmique

    # Générer les instances pour un scénario spécifique
    python3 generate_entities.py --scenario breakdown

Résultat :
    vault/entites/     ← fiches entités .md
    vault/instances/   ← fiches instances .md
"""

import os
import sys
import json
import re
import time
import yaml
import argparse
from datetime import datetime

from llm_client import call_llm, LLM_MODEL as MODEL

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH  = "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098"

PATHS = {
    "scenarios":   os.path.join(VAULT_PATH, "scenarios"),
    "variables":   os.path.join(VAULT_PATH, "variables"),
    "entites":     os.path.join(VAULT_PATH, "entites"),
    "instances":   os.path.join(VAULT_PATH, "instances"),
}


MAX_TOKENS = 4000

VALID_SCENARIOS = [
    "fortress_world", "new_sustainability", "breakdown",
    "eco_communalism", "policy_reform", "reference"
]

VALID_VARS = [
    "systeme_economique_redistribution", "gouvernance_institutions",
    "geopolitique_conflits", "valeurs_culture_tempo_sociale",
    "organisation_territoires", "sante_biotechnologies",
    "frontieres_du_systeme", "technologie_information",
    "climat_environnement_global", "energie_ressources_critiques",
    "demographie_mobilite_humaine", "systemes_productifs_travail",
]


# ─────────────────────────────────────────
# LECTURE DES DONNÉES OBSIDIAN
# ─────────────────────────────────────────

def parse_md_frontmatter(filepath):
    """Parse le frontmatter YAML d'un fichier .md"""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if not fm_match:
        return {}
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", fm_match.group(1))
    try:
        return yaml.safe_load(fm_str) or {}
    except:
        return {}

def load_scenarios_context():
    """Charge le contexte des 6 scénarios"""
    context = {}
    for sc in VALID_SCENARIOS:
        path = os.path.join(PATHS["scenarios"], f"{sc}.md")
        fm   = parse_md_frontmatter(path)
        context[sc] = {
            "state_of_system":           fm.get("state_of_system", ""),
            "trajectory":                fm.get("trajectory", ""),
            "tension_level":             fm.get("tension_level", ""),
            "political_regime":          fm.get("political_regime", ""),
            "dominant_region_structure": fm.get("dominant_region_structure", ""),
            "transformation_speed":      fm.get("transformation_speed", ""),
            "dominant_variables":        fm.get("dominant_variables", []) or [],
        }

        # Extraire le summary depuis le body
        if os.path.exists(path):
            with open(path) as f:
                body = f.read()
            m = re.search(r"##\s+9\.\s+Synthèse.*?\n.*?\*\*Résumé\*\*\s*\n(.+?)(?=\n\*\*|\n##|\Z)",
                         body, re.DOTALL)
            context[sc]["summary"] = m.group(1).strip()[:300] if m else ""

    return context

def load_variables_context():
    """Charge le contexte des 12 variables"""
    context = {}
    for var in VALID_VARS:
        path = os.path.join(PATHS["variables"], f"{var}.md")
        fm   = parse_md_frontmatter(path)
        context[var] = {
            "variable_type":          fm.get("variable_type", ""),
            "global_influence_level": fm.get("global_influence_level", ""),
        }

        # Extraire les state_logic par scénario
        states = fm.get("states", {}) or {}
        context[var]["states"] = {}
        for sc in VALID_SCENARIOS:
            if sc in states and isinstance(states[sc], dict):
                context[var]["states"][sc] = str(states[sc].get("state_logic", ""))[:150]

    return context


# ─────────────────────────────────────────
# PROMPTS DE GÉNÉRATION
# ─────────────────────────────────────────

def build_entities_prompt(scenarios_ctx, variables_ctx):
    """Construit le prompt pour générer la liste des entités"""

    scenarios_text = ""
    for sc, data in scenarios_ctx.items():
        scenarios_text += f"\n**{sc}**\n"
        scenarios_text += f"- État : {data['state_of_system']} | Tension : {data['tension_level']}/5 | Trajectoire : {data['trajectory']}\n"
        scenarios_text += f"- Régime : {data['political_regime']} | Structure : {data['dominant_region_structure']}\n"
        if data['summary']:
            scenarios_text += f"- Contexte : {data['summary'][:200]}\n"
        scenarios_text += f"- Variables dominantes : {', '.join(data['dominant_variables'])}\n"

    variables_text = ""
    for var, data in variables_ctx.items():
        variables_text += f"- **{var}** (type: {data['variable_type']}, influence: {data['global_influence_level']}/5)\n"

    prompt = f"""Tu es un expert en worldbuilding pour un projet de simulation prospective : Ourrassol 2098.

Tu dois générer une liste de 20 entités archétypales cohérentes avec 6 mondes possibles en 2098.

## LES 6 SCÉNARIOS
{scenarios_text}

## LES 12 VARIABLES DU SYSTÈME
{variables_text}

## CONSIGNE

Génère exactement 20 entités réparties ainsi :
- 5 institutions / organisations politiques
- 4 organisations économiques / entreprises
- 3 infrastructures / systèmes technologiques
- 3 mouvements sociaux / culturels / religieux
- 3 personnages humains emblématiques
- 2 médias / réseaux d'information

Règles :
- Noms crédibles en 2098 — ni trop actuels ni trop SF
- Chaque entité doit avoir des incarnations RADICALEMENT différentes selon les scénarios
- Couvrir l'ensemble des 12 variables
- Répondre en JSON uniquement, sans texte autour

Format JSON :
{{
  "entites": [
    {{
      "nom": "Nom Canonique",
      "slug": "slug_entite",
      "categorie": "institution|organisation|infrastructure|réseau|humain|mouvement|média",
      "description": "Description archétypale — 2 lignes max.",
      "tension_fondamentale": "Le conflit qu'elle incarne en une ligne.",
      "variables_potentielles": ["variable_1", "variable_2", "variable_3"],
      "scenarios": ["scenario_1", "scenario_2"]
    }}
  ]
}}"""

    return prompt


def build_instance_prompt(entite, scenario, scenario_ctx, variables_ctx):
    """Construit le prompt pour générer une instance spécifique"""

    # État des variables influencées dans ce scénario
    vars_context = ""
    for var in entite.get("variables_potentielles", []):
        if var in variables_ctx and scenario in variables_ctx[var]["states"]:
            state = variables_ctx[var]["states"][scenario]
            vars_context += f"\n- **{var}** dans {scenario} : {state}"

    sc = scenario_ctx[scenario]

    prompt = f"""Tu es un expert en worldbuilding pour Ourrassol 2098.

Génère l'instance de l'entité "{entite['nom']}" dans le scénario "{scenario}".

## ENTITÉ ARCHÉTYPE
- Nom : {entite['nom']}
- Catégorie : {entite['categorie']}
- Description : {entite['description']}
- Tension fondamentale : {entite['tension_fondamentale']}

## SCÉNARIO {scenario.upper()}
- État : {sc['state_of_system']} | Tension : {sc['tension_level']}/5 | Trajectoire : {sc['trajectory']}
- Régime : {sc['political_regime']} | Vitesse : {sc['transformation_speed']}
- Variables dominantes : {', '.join(sc['dominant_variables'])}
{f"- Contexte : {sc['summary']}" if sc['summary'] else ""}

## ÉTAT DES VARIABLES INFLUENCÉES DANS CE SCÉNARIO
{vars_context if vars_context else "Non défini"}

## CONSIGNE

Génère une instance cohérente avec ce scénario. L'instance DOIT refléter l'état
du monde — si le scénario est chaotique, l'institution est fragmentée ou disparue.
Si le scénario est stable, elle peut être dominante ou mature.

Le nom de l'instance peut être identique à l'entité, une variante, ou radicalement
différent selon le monde.

Réponds en JSON uniquement :
{{
  "nom": "Nom de l'instance dans ce scénario",
  "type_dans_scenario": "IA|organisation|entreprise|institution|infrastructure|réseau|humain|système|hybride|autre",
  "role_dans_scenario": "Rôle narratif et systémique détaillé (3-5 lignes)",
  "responsabilites": "Actions concrètes exercées dans ce monde (2-3 lignes)",
  "impact_local": 0,
  "impact_systemique_global": 0,
  "variables_influencees": ["variable_1", "variable_2"],
  "zone_geographique": ["locale|urbaine|nationale|régionale|continentale|globale"],
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


# ─────────────────────────────────────────
# GÉNÉRATION VIA API
# ─────────────────────────────────────────

def call_claude(prompt, max_tokens=MAX_TOKENS):
    """Appelle le LLM configuré et retourne le JSON parsé"""
    text = call_llm(
        system_prompt="",
        user_prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.0,
    ).strip()

    # Nettoyer les balises markdown si présentes
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON invalide : {e}")
        print(f"  Réponse brute : {text[:200]}")
        return None


# ─────────────────────────────────────────
# GÉNÉRATION DES FICHIERS OBSIDIAN
# ─────────────────────────────────────────

def write_entity_file(entite):
    """Génère la fiche entité .md"""
    os.makedirs(PATHS["entites"], exist_ok=True)

    slug     = entite["slug"]
    filepath = os.path.join(PATHS["entites"], f"{slug}.md")

    # Construire le tableau des instances
    instance_rows = ""
    for sc in VALID_SCENARIOS:
        if sc in entite.get("scenarios", []):
            instance_rows += f"| [[{sc}]] | [[{slug}_{sc}]] | | |\n"
        else:
            instance_rows += f"| [[{sc}]] | — | — | — |\n"

    vars_yaml = "\n".join(f"  - {v}" for v in entite.get("variables_potentielles", []))
    scenarios_yaml = "\n".join(f"  - {s}" for s in entite.get("scenarios", []))

    content = f"""---
name: {entite['nom']}
type: entity
slug: {slug}
category: {entite['categorie']}
description: >
  {entite['description']}
tension_fondamentale: >
  {entite['tension_fondamentale']}
variables_potentielles:
{vars_yaml}
scenarios_instances:
{scenarios_yaml}
date_creation: {datetime.now().strftime("%Y-%m-%d")}
---

# {entite['nom']}

## Description archétypale
{entite['description']}

## Tension fondamentale
{entite['tension_fondamentale']}

## Instances par scénario
| Scénario | Instance | État | Rôle |
|---|---|---|---|
{instance_rows}
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def write_instance_file(entite, scenario, instance_data):
    """Génère la fiche instance .md"""
    os.makedirs(PATHS["instances"], exist_ok=True)

    slug_entite   = entite["slug"]
    slug_instance = f"{slug_entite}_{scenario}"
    filepath      = os.path.join(PATHS["instances"], f"{slug_instance}.md")

    # YAML lists
    def yaml_list(lst, indent=2):
        if not lst:
            return ""
        pad = "  " * indent
        return "\n" + "\n".join(f"{pad}- {i}" for i in lst)

    vars_yaml    = yaml_list(instance_data.get("variables_influencees", []))
    zones_geo    = yaml_list(instance_data.get("zone_geographique", []))
    zones_sys    = yaml_list(instance_data.get("zone_systemique", []))
    alliances    = yaml_list(instance_data.get("alliances", []))
    oppositions  = yaml_list(instance_data.get("oppositions", []))

    annee_fin = instance_data.get("annee_fin", "")
    annee_fin_str = str(annee_fin) if annee_fin else ""

    content = f"""---
name: {instance_data.get('nom', entite['nom'])}
type: instance
slug: {slug_instance}
entite: {slug_entite}
scenario: {scenario}

type_dans_scenario: {instance_data.get('type_dans_scenario', '')}

role_dans_scenario: >
  {instance_data.get('role_dans_scenario', '').replace(chr(10), ' ')}

responsabilites: >
  {instance_data.get('responsabilites', '').replace(chr(10), ' ')}

impact_local: {instance_data.get('impact_local', 0)}
impact_systemique_global: {instance_data.get('impact_systemique_global', 0)}

variables_influencees:{vars_yaml}

zone_geographique:{zones_geo}

zone_systemique:{zones_sys}

alliances:{alliances}

oppositions:{oppositions}

type_relation_dominante: {instance_data.get('type_relation_dominante', 'neutralité')}

annee_debut: {instance_data.get('annee_debut', 2026)}
annee_fin: {annee_fin_str}

etat_temporel: {instance_data.get('etat_temporel', 'actif')}
age_historique: {instance_data.get('age_historique', 'mature')}
generation: {instance_data.get('generation', 'transition')}

injection:
  type: canonique
  annee_injection:
  contexte_injection:
  impact_sur_variables:
  propagation:
    via_matrice: false

description_journalistique: >
  {instance_data.get('description_journalistique', '').replace(chr(10), ' ')}

signes_distinctifs: >
  {instance_data.get('signes_distinctifs', '').replace(chr(10), ' ')}

tensions_narratives: >
  {instance_data.get('tensions_narratives', '').replace(chr(10), ' ')}

date_creation: {datetime.now().strftime("%Y-%m-%d")}
---

# {instance_data.get('nom', entite['nom'])}

## Rôle dans [[{scenario}]]
{instance_data.get('role_dans_scenario', '')}

## Responsabilités
{instance_data.get('responsabilites', '')}

## Variables influencées
{chr(10).join(f'- [[{v}]]' for v in instance_data.get('variables_influencees', []))}

## Relations
**Alliés** : {', '.join(f'[[{a}]]' for a in instance_data.get('alliances', [])) or '_aucun défini_'}
**Opposants** : {', '.join(f'[[{o}]]' for o in instance_data.get('oppositions', [])) or '_aucun défini_'}

## Description journalistique
{instance_data.get('description_journalistique', '')}

## Tensions narratives
{instance_data.get('tensions_narratives', '')}
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


# ─────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────

def generate_all(entities_only=False, filter_entity=None, filter_scenario=None):
    """Pipeline complet de génération"""

    print("\n" + "="*60)
    print("OURRASSOL 2098 — Génération des entités et instances")
    print("="*60)

    # Créer les dossiers
    os.makedirs(PATHS["entites"], exist_ok=True)
    os.makedirs(PATHS["instances"], exist_ok=True)

    # Charger le contexte
    print("\n[1/4] Chargement du contexte Obsidian...")
    scenarios_ctx = load_scenarios_context()
    variables_ctx = load_variables_context()
    print(f"  ✓ {len(scenarios_ctx)} scénarios | {len(variables_ctx)} variables")

    # Générer la liste des entités
    print("\n[2/4] Génération de la liste des entités...")

    # Vérifier si un fichier d'entités existe déjà
    entities_cache = os.path.join(PATHS["entites"], "_entities_list.json")

    if filter_entity and os.path.exists(entities_cache):
        # Charger depuis le cache
        with open(entities_cache) as f:
            entites = json.load(f)
        print(f"  ✓ {len(entites)} entités chargées depuis le cache")
    else:
        # Générer via API
        prompt = build_entities_prompt(scenarios_ctx, variables_ctx)
        result = call_claude(prompt, max_tokens=4000)

        if not result or "entites" not in result:
            print("  ✗ Génération des entités échouée")
            return

        entites = result["entites"]
        print(f"  ✓ {len(entites)} entités générées")

        # Sauvegarder le cache
        with open(entities_cache, "w") as f:
            json.dump(entites, f, ensure_ascii=False, indent=2)

    # Filtrer si demandé
    if filter_entity:
        entites = [e for e in entites if e["slug"] == filter_entity]
        if not entites:
            print(f"  ✗ Entité '{filter_entity}' non trouvée")
            return

    # Écrire les fiches entités
    print("\n[3/4] Écriture des fiches entités...")
    for entite in entites:
        path = write_entity_file(entite)
        print(f"  ✓ {entite['slug']}.md")

    if entities_only:
        print(f"\n✓ {len(entites)} fiches entités créées (mode --entities-only)")
        return

    # Générer les instances
    print(f"\n[4/4] Génération des instances...")
    total_instances = 0
    errors          = 0

    for entite in entites:
        scenarios_to_process = entite.get("scenarios", VALID_SCENARIOS)

        if filter_scenario:
            scenarios_to_process = [s for s in scenarios_to_process if s == filter_scenario]

        for scenario in scenarios_to_process:
            print(f"  → {entite['slug']} × {scenario}...", end=" ", flush=True)

            # Vérifier si l'instance existe déjà
            instance_path = os.path.join(
                PATHS["instances"],
                f"{entite['slug']}_{scenario}.md"
            )
            if os.path.exists(instance_path) and not filter_entity:
                print("(déjà existant)")
                total_instances += 1
                continue

            # Générer via API
            prompt = build_instance_prompt(entite, scenario, scenarios_ctx, variables_ctx)
            result = call_claude(prompt, max_tokens=2000)

            if not result:
                print("✗")
                errors += 1
                continue

            path = write_instance_file(entite, scenario, result)
            print("✓")
            total_instances += 1

            # Pause pour éviter le rate limiting
            time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"✓ {len(entites)} entités | {total_instances} instances | {errors} erreurs")
    print(f"Entités   : {PATHS['entites']}")
    print(f"Instances : {PATHS['instances']}")
    print("="*60)


# ─────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Génère les entités et instances pour Ourrassol 2098"
    )
    parser.add_argument(
        "--entities-only",
        action="store_true",
        help="Génère uniquement les fiches entités sans les instances"
    )
    parser.add_argument(
        "--entity",
        type=str,
        help="Génère uniquement les instances d'une entité spécifique (slug)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        choices=VALID_SCENARIOS,
        help="Génère uniquement les instances d'un scénario spécifique"
    )

    args = parser.parse_args()

    generate_all(
        entities_only=args.entities_only,
        filter_entity=args.entity,
        filter_scenario=args.scenario,
    )
