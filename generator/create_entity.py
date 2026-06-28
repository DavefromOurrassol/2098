#!/usr/bin/env python3
"""
create_entity.py — Ourrassol 2098
====================================

Crée des fiches "entité" (archétypes, entites/{slug}.md) — première
brique du futur script unifié create_entities_and_instances.py (voir
generate_instances.py pour la seconde brique, qui génère les instances
par scénario pour des entités déjà créées).

DEUX MODES, demandés interactivement au lancement :

  custom — tu décris UNE instance précise (nom, catégorie, rôle et état
           dans UN scénario de référence) dans
           entites_custom/queue.yaml. Claude en déduit l'archétype
           (description générale + tension fondamentale intemporelle +
           variables potentielles), cohérent avec cette instance de
           référence. Le rôle et l'état que tu fournis pour le scénario
           de référence sont des CONTRAINTES DURES — Claude ne les
           reformule pas, il construit l'archétype à partir d'eux.

  auto   — tu donnes juste un nombre N. Claude invente N entités
           entièrement nouvelles, complètes et variées.

Dans les deux cas, un garde-fou anti-doublon vérifie le nom/la nature
de chaque entité (custom ou auto) contre les entités déjà existantes
(_entities_list.json, registre permanent — pas juste un cache de
session) avant de créer quoi que ce soit, et rejette/redemande si une
entité trop proche existe déjà.

Ce script ne génère QUE les fiches entités (archétypes). Les instances
par scénario sont générées séparément par generate_instances.py.

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...

USAGE
-----
    python3 create_entity.py
    python3 create_entity.py --dry-run   # affiche sans rien écrire
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

from llm_client import call_llm, LLM_MODEL as MODEL


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
VARIABLES_DIR = VAULT_ROOT / "variables"
SCENARIOS_DIR = VAULT_ROOT / "scenarios"
ENTITES_DIR = VAULT_ROOT / "entites"
ENTITES_LIST_PATH = ENTITES_DIR / "_entities_list.json"
ENTITES_CUSTOM_DIR = VAULT_ROOT / "entites_custom"
QUEUE_PATH = ENTITES_CUSTOM_DIR / "queue.yaml"
PROCESSED_PATH = ENTITES_CUSTOM_DIR / "processed.yaml"
NEEDS_REVIEW_PATH = ENTITES_CUSTOM_DIR / "needs_review.yaml"


MAX_FIX_ATTEMPTS = 2

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

VALID_CATEGORIES = [
    "IA", "organisation", "entreprise", "institution", "infrastructure",
    "réseau", "humain", "système", "hybride", "autre",
]

VALID_ETATS = ["actif", "disparu", "transformé", "clandestin", "historique", "mythifié"]


# ---------------------------------------------------------------------------
# Lecture du contexte (variables / scénarios)
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


def build_variables_summary():
    chunks = []
    for slug in VALID_VARS:
        fm, _ = parse_md(VARIABLES_DIR / f"{slug}.md")
        domain = ", ".join(fm.get("domain", []) or [])
        chunks.append(f"- {slug} (domain: {domain})")
    return "\n".join(chunks)


def load_scenario_context(scenario):
    fm, body = parse_md(SCENARIOS_DIR / f"{scenario}.md")
    summary = ""
    m = re.search(r"\*\*Résumé\*\*\s*\n(.+?)(?=\n\*\*|\n##|\Z)", body, re.DOTALL)
    if m:
        summary = m.group(1).strip()[:250]
    return {
        "state_of_system": fm.get("state_of_system", ""),
        "tension_level": fm.get("tension_level", ""),
        "trajectory": fm.get("trajectory", ""),
        "political_regime": fm.get("political_regime", ""),
        "transformation_speed": fm.get("transformation_speed", ""),
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Registre anti-doublon (_entities_list.json)
# ---------------------------------------------------------------------------

def load_entities_list():
    """Charge le registre permanent des entités déjà créées.

    Contrairement à l'usage d'origine dans generate_entities.py (simple
    cache de session), ce fichier est désormais traité comme la source
    de vérité anti-doublon, mise à jour à chaque entité créée (custom
    ou auto)."""
    if not ENTITES_LIST_PATH.exists():
        return []
    try:
        return json.loads(ENTITES_LIST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_entities_list(entities):
    ENTITES_DIR.mkdir(parents=True, exist_ok=True)
    ENTITES_LIST_PATH.write_text(
        json.dumps(entities, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def append_to_entities_list(entry):
    entities = load_entities_list()
    entities.append(entry)
    save_entities_list(entities)


def build_existing_entities_summary(entities):
    """Résumé condensé des entités existantes, pour le prompt
    anti-doublon (nom, catégorie, tension — suffisant pour repérer une
    redondance sans avoir besoin de tout le texte des fiches)."""
    if not entities:
        return "(aucune entité existante — c'est la première)"
    lines = []
    for e in entities:
        lines.append(
            "- {} (slug: {}, catégorie: {}) — {}".format(
                e.get("nom", "?"), e.get("slug", "?"), e.get("categorie", "?"),
                e.get("tension_fondamentale", "")[:100],
            )
        )
    return "\n".join(lines)


def slugify(text):
    s = text.lower()
    for fr, en in [("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"),
                   ("à", "a"), ("â", "a"), ("ä", "a"), ("ù", "u"),
                   ("û", "u"), ("ü", "u"), ("î", "i"), ("ï", "i"),
                   ("ô", "o"), ("ö", "o"), ("ç", "c")]:
        s = s.replace(fr, en)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


# ---------------------------------------------------------------------------
# Appels Claude
# ---------------------------------------------------------------------------

def get_client():
    """Conservé pour compatibilité — retourne None, call_claude_json n'en a plus besoin."""
    return None


def call_claude_json(client, system, user_content, max_tokens=3000):
    text = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
    ).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


# --- Mode custom : déduire l'archétype à partir d'une instance de référence

def step_custom_derive_archetype(client, idea, existing_entities, previous=None, issues=None):
    var_summary = build_variables_summary()
    existing_summary = build_existing_entities_summary(existing_entities)
    sc_ctx = load_scenario_context(idea["scenario_ref"])

    if previous is None:
        task = """TÂCHE : déduis l'archétype intemporel de cette entité à partir de
l'instance de référence ci-dessus (nom, catégorie, rôle, état dans ce
scénario précis). L'archétype doit pouvoir exister, sous des formes
différentes, dans n'importe quel scénario — pas seulement celui de
référence."""
    else:
        issues_txt = "\n".join(f"- {i}" for i in issues)
        task = f"""La proposition précédente a échoué la validation :
{issues_txt}

Voici la proposition précédente :
{json.dumps(previous, ensure_ascii=False, indent=2)}

TÂCHE : corrige UNIQUEMENT les points listés ci-dessus."""

    user_content = f"""Tu dois déduire l'archétype intemporel d'une entité pour le
projet Ourrassol 2098, à partir d'une instance de référence précise
que l'utilisateur a déjà fixée.

## INSTANCE DE RÉFÉRENCE (CONTRAINTES DURES — ne pas reformuler)
- Nom : {idea['nom']}
- Catégorie : {idea['category']}
- Scénario de référence : {idea['scenario_ref']}
- Rôle dans ce scénario : {idea['role']}
- État dans ce scénario : {idea['etat']}

## CONTEXTE DU SCÉNARIO DE RÉFÉRENCE
- État : {sc_ctx['state_of_system']} | Tension : {sc_ctx['tension_level']}/5 | Trajectoire : {sc_ctx['trajectory']}
- Régime : {sc_ctx['political_regime']} | Vitesse : {sc_ctx['transformation_speed']}
- Contexte : {sc_ctx['summary']}

## VARIABLES DISPONIBLES
{var_summary}

## ENTITÉS DÉJÀ EXISTANTES (anti-doublon — ne PAS recréer une variante de l'une d'elles)
{existing_summary}

## CONSIGNE
Si cette entité ressemble fortement à une entité déjà existante
(même fonction systémique, même tension fondamentale), indique-le
explicitement via "doublon_detecte": true et "doublon_slug" plutôt que
de forcer une création.

{task}

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact :
{{
  "description_complete": "description archétypale enrichie, 3-4 lignes — ce que cette entité représente fondamentalement, indépendamment de tout scénario",
  "tension_fondamentale": "le conflit ou la contradiction que cette entité porte en elle, quel que soit le scénario — 1-2 lignes",
  "variables_potentielles": ["slug1", "slug2", "slug3"],
  "doublon_detecte": false,
  "doublon_slug": null
}}
"""
    return call_claude_json(client, "Tu es un assistant de world-building.", user_content)


# --- Mode auto : génération libre de N entités

def step_auto_generate_entities(client, n, existing_entities, category_hint=None):
    var_summary = build_variables_summary()
    existing_summary = build_existing_entities_summary(existing_entities)
    scenarios_summary = "\n".join(
        f"- {s}: {load_scenario_context(s)['summary'][:120]}" for s in SCENARIOS
    )

    category_txt = ""
    if category_hint:
        category_txt = f"\nContrainte : toutes les entités doivent être de catégorie '{category_hint}'.\n"

    user_content = f"""Tu dois inventer {n} nouvelle(s) entité(s) (archétypes) pour le
projet Ourrassol 2098 — institutions, organisations, mouvements,
infrastructures, IA, personnages individuels, etc. qui pourront être
incarnés différemment dans chacun des 6 scénarios du monde.
{category_txt}
## SCÉNARIOS DU MONDE
{scenarios_summary}

## VARIABLES DISPONIBLES
{var_summary}

## ENTITÉS DÉJÀ EXISTANTES (anti-doublon — ne RECRÉE AUCUNE variante de l'une d'elles)
{existing_summary}

## CONSIGNE
Diversifie les catégories et les tensions fondamentales. Chaque entité
doit avoir une fonction systémique claire et distincte des entités
déjà existantes — pas de répétition thématique (ex: ne propose pas un
2e "oligopole énergétique" si un existe déjà, sauf angle radicalement
différent).

Pour CHAQUE entité, évalue honnêtement si elle est trop proche d'une
entité déjà existante (même fonction systémique, même tension
fondamentale, même niche narrative) — même une proximité partielle
compte. Si c'est le cas, indique-le via "doublon_detecte": true et
"doublon_slug" plutôt que de forcer la proposition ; cette entité sera
écartée du batch, ce n'est pas grave, propose-en une suffisamment
différente à la place dans ta réponse.

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact :
{{
  "entites": [
    {{
      "nom": "Nom de l'entité",
      "category": "{'|'.join(VALID_CATEGORIES)}",
      "description_complete": "description archétypale, 3-4 lignes",
      "tension_fondamentale": "1-2 lignes",
      "variables_potentielles": ["slug1", "slug2", "slug3"],
      "scenarios_instances": ["scenario1", "scenario2"],
      "doublon_detecte": false,
      "doublon_slug": null
    }}
  ]
}}
"""
    return call_claude_json(client, "Tu es un assistant de world-building.", user_content,
                             max_tokens=4000)


# ---------------------------------------------------------------------------
# Validation mécanique
# ---------------------------------------------------------------------------

def validate_archetype(data, existing_entities):
    issues = []

    required = ["description_complete", "tension_fondamentale", "variables_potentielles"]
    for field in required:
        if not data.get(field):
            issues.append(f"Champ requis manquant ou vide : '{field}'")

    variables = data.get("variables_potentielles") or []
    for v in variables:
        if v not in VALID_VARS:
            issues.append(f"Variable inconnue dans variables_potentielles : {v!r}")

    if data.get("doublon_detecte"):
        slug = data.get("doublon_slug", "?")
        issues.append(
            f"Doublon détecté avec l'entité existante '{slug}' — "
            f"reformuler ou abandonner cette idée"
        )

    return issues


def validate_auto_entity(entity, existing_entities, existing_names_in_batch):
    issues = []
    required = ["nom", "category", "description_complete", "tension_fondamentale"]
    for field in required:
        if not entity.get(field):
            issues.append(f"Champ requis manquant ou vide : '{field}'")

    if entity.get("category") not in VALID_CATEGORIES:
        issues.append(f"Catégorie invalide : {entity.get('category')!r}")

    nom = entity.get("nom", "")
    slug = slugify(nom)
    existing_slugs = {e.get("slug") for e in existing_entities}
    if slug in existing_slugs:
        issues.append(f"Slug '{slug}' déjà utilisé par une entité existante")
    if slug in existing_names_in_batch:
        issues.append(f"Slug '{slug}' déjà utilisé par une autre entité de ce même batch")

    variables = entity.get("variables_potentielles") or []
    for v in variables:
        if v not in VALID_VARS:
            issues.append(f"Variable inconnue : {v!r}")

    scenarios = entity.get("scenarios_instances") or []
    for s in scenarios:
        if s not in SCENARIOS:
            issues.append(f"Scénario inconnu : {s!r}")

    if entity.get("doublon_detecte"):
        doublon_slug = entity.get("doublon_slug", "?")
        issues.append(
            f"Doublon détecté avec l'entité existante '{doublon_slug}' — "
            f"cette entité doit être reformulée ou écartée"
        )

    return issues


# ---------------------------------------------------------------------------
# Écriture des fichiers
# ---------------------------------------------------------------------------

def write_entity_file(name, slug, category, description, tension,
                       variables, scenarios, custom_source=None,
                       scenario_ref=None, role_ref=None, etat_ref=None):
    ENTITES_DIR.mkdir(parents=True, exist_ok=True)

    vars_yaml = "\n".join(f"  - {v}" for v in variables)
    scenarios_yaml = "\n".join(f"  - {s}" for s in scenarios)

    instance_rows = ""
    for sc in SCENARIOS:
        if sc in scenarios:
            instance_rows += f"| [[{sc}]] | [[{slug}_{sc}]] | | |\n"
        else:
            instance_rows += f"| [[{sc}]] | — | — | — |\n"

    extra_fm = f"custom_source: {custom_source}\n" if custom_source else ""

    # Champs présents UNIQUEMENT pour les entités custom — leur présence
    # (ou absence) dans le frontmatter est le signal que
    # generate_instances.py utilise pour savoir s'il doit traiter un
    # scénario comme contrainte dure (role/etat imposés tels quels) ou
    # laisser toutes les instances entièrement libres (entités
    # anciennes ou créées en mode auto : ces champs sont simplement
    # absents).
    if scenario_ref:
        role_ref_clean = (role_ref or "").strip().replace("\n", " ")
        extra_fm += f"scenario_ref: {scenario_ref}\n"
        extra_fm += f"role_ref: >\n  {role_ref_clean}\n"
        extra_fm += f"etat_ref: {etat_ref}\n"

    content = f"""---
name: {name}
type: entity
slug: {slug}
category: {category}
description: >
  {description.strip()}
tension_fondamentale: >
  {tension.strip()}
variables_potentielles:
{vars_yaml}
scenarios_instances:
{scenarios_yaml}
date_creation: {datetime.now().strftime("%Y-%m-%d")}
{extra_fm}---

# {name}

## Description archétypale
{description.strip()}

## Tension fondamentale
{tension.strip()}

## Instances par scénario
| Scénario | Instance | État | Rôle |
|---|---|---|---|
{instance_rows}
"""
    path = ENTITES_DIR / f"{slug}.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Gestion de la queue (mode custom)
# ---------------------------------------------------------------------------

def load_yaml_list(path, key="queue"):
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get(key, []) or []


def append_yaml_list(path, item, key="processed"):
    items = load_yaml_list(path, key=key)
    items.append(item)
    ENTITES_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump({key: items}, allow_unicode=True, sort_keys=False),
                     encoding="utf-8")


QUEUE_TEMPLATE = """\
# entites_custom/queue.yaml
#
# Ajoute ici tes idées d'entités custom, décrites à travers UNE
# instance de référence précise (le scénario où tu l'imagines
# d'abord). Claude en déduira l'archétype intemporel, puis
# generate_instances.py générera les instances pour les autres
# scénarios. Lance ensuite :
#
#   python3 generator/create_entity.py            ← création réelle
#   python3 generator/create_entity.py --dry-run  ← test sans écriture
#
# CHAMPS :
#   nom            : nom de l'entité (personnage, organisation, IA...)
#   category        : IA | organisation | entreprise | institution |
#                     infrastructure | réseau | humain | système |
#                     hybride | autre
#   role            : rôle dans le scénario de référence — CONTRAINTE
#                     DURE, repris tel quel par le script, pas reformulé
#   etat            : état dans le scénario de référence — CONTRAINTE
#                     DURE. Valeurs possibles :
#                     actif | disparu | transformé | clandestin |
#                     historique | mythifié
#   scenario_ref    : le scénario où s'appliquent role/etat ci-dessus
#                     (un seul, parmi : breakdown, fortress_world,
#                     new_sustainability, eco_communalism,
#                     policy_reform, reference)
#   scenario_hint   : liste de TOUS les scénarios à couvrir, y compris
#                     scenario_ref. null = les 6 scénarios par défaut.
#   source          : libre — date, contexte, lien...
#
# EXEMPLE :
#   - nom: Le Cartographe Silencieux
#     category: humain
#     role: >
#       Ancien officier de renseignement devenu cartographe clandestin
#       des zones de non-droit, vendant ses relevés aux plus offrants.
#     etat: clandestin
#     scenario_ref: breakdown
#     scenario_hint: null
#     source: idee_2026-06
#
# Un garde-fou anti-doublon (contre les entités déjà présentes dans
# entites/_entities_list.json) s'applique systématiquement, y compris
# en mode custom.
#
# Les idées traitées sont déplacées vers processed.yaml (succès) ou
# needs_review.yaml (échec après corrections automatiques).
# ──────────────────────────────────────────────────────────────────────────────

queue:
"""


def save_queue_with_template(remaining):
    ENTITES_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    if remaining:
        items_yaml = yaml.dump(remaining, allow_unicode=True,
                               sort_keys=False, default_flow_style=False)
        indented = "\n".join("  " + line for line in items_yaml.splitlines())
        content = QUEUE_TEMPLATE + indented + "\n"
    else:
        content = QUEUE_TEMPLATE + "  [] # ← remplace [] par tes idées\n"
    QUEUE_PATH.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Mode custom — boucle principale
# ---------------------------------------------------------------------------

def process_custom_idea(client, idea, dry_run=False):
    nom = idea.get("nom", "sans_nom")
    category = idea.get("category")
    scenario_ref = idea.get("scenario_ref")
    scenario_hint = idea.get("scenario_hint")

    print(f"\n=== {nom} ===")

    if category not in VALID_CATEGORIES:
        return {"status": "needs_review", "idea": idea,
                "reason": f"category invalide : {category!r}"}
    if scenario_ref not in SCENARIOS:
        return {"status": "needs_review", "idea": idea,
                "reason": f"scenario_ref invalide : {scenario_ref!r}"}

    scenarios = scenario_hint if scenario_hint else list(SCENARIOS)
    scenarios = [s for s in scenarios if s in SCENARIOS]
    if scenario_ref not in scenarios:
        scenarios = [scenario_ref] + scenarios

    existing_entities = load_entities_list()

    print("[1/3] Déduction de l'archétype...")
    previous, issues = None, None
    archetype = step_custom_derive_archetype(client, idea, existing_entities)

    for attempt in range(MAX_FIX_ATTEMPTS + 1):
        print(f"[2/3] Validation (essai {attempt + 1})...")
        issues = validate_archetype(archetype, existing_entities)
        if not issues:
            break
        print("  -> problèmes :")
        for i in issues:
            print(f"     - {i}")
        if attempt < MAX_FIX_ATTEMPTS:
            archetype = step_custom_derive_archetype(
                client, idea, existing_entities, previous=archetype, issues=issues
            )

    if issues:
        return {"status": "needs_review", "idea": idea, "archetype": archetype,
                "issues": issues}

    slug = slugify(nom)
    print("[3/3] Injection...")
    if not dry_run:
        write_entity_file(
            nom, slug, category, archetype["description_complete"],
            archetype["tension_fondamentale"], archetype["variables_potentielles"],
            scenarios, custom_source=idea.get("source"),
            scenario_ref=scenario_ref, role_ref=idea.get("role"), etat_ref=idea.get("etat"),
        )
        append_to_entities_list({
            "nom": nom, "slug": slug, "categorie": category,
            "description": archetype["description_complete"],
            "tension_fondamentale": archetype["tension_fondamentale"],
            "variables_potentielles": archetype["variables_potentielles"],
            "scenarios": scenarios,
        })
    else:
        print(json.dumps(archetype, ensure_ascii=False, indent=2))

    return {
        "status": "injected", "idea": idea, "slug": slug,
        "scenarios": scenarios, "archetype": archetype,
        "scenario_ref": scenario_ref,
        "role_ref": idea.get("role"), "etat_ref": idea.get("etat"),
    }


def run_custom_mode(client, dry_run):
    queue = load_yaml_list(QUEUE_PATH, key="queue")
    if not queue:
        print(f"Queue vide ({QUEUE_PATH}). Rien à faire.")
        return

    remaining = []
    for idea in queue:
        try:
            outcome = process_custom_idea(client, idea, dry_run=dry_run)
        except Exception as e:
            outcome = {"status": "needs_review", "idea": idea, "error": str(e)}

        if dry_run:
            print(json.dumps(outcome, ensure_ascii=False, indent=2, default=str))
            remaining.append(idea)
            continue

        if outcome["status"] == "injected":
            append_yaml_list(PROCESSED_PATH, outcome, key="processed")
        else:
            append_yaml_list(NEEDS_REVIEW_PATH, outcome, key="needs_review")

    if not dry_run:
        save_queue_with_template(remaining)
        print(f"\nTerminé. Voir {PROCESSED_PATH} et {NEEDS_REVIEW_PATH}.")
        print("→ Lancez ensuite generate_instances.py pour générer les instances.")


# ---------------------------------------------------------------------------
# Mode auto — boucle principale
# ---------------------------------------------------------------------------

def run_auto_mode(client, dry_run):
    raw = input("Combien d'entités générer ? : ").strip()
    try:
        n = int(raw)
    except ValueError:
        print("Nombre invalide.")
        return
    if n < 1:
        print("Le nombre doit être >= 1.")
        return

    category_raw = input(
        "Catégorie imposée (optionnel, Entrée pour libre) [{}] : ".format(
            "|".join(VALID_CATEGORIES)
        )
    ).strip()
    category_hint = category_raw if category_raw in VALID_CATEGORIES else None

    existing_entities = load_entities_list()

    print(f"\n[1/2] Génération de {n} entité(s)...")
    result = step_auto_generate_entities(client, n, existing_entities, category_hint)
    entities = result.get("entites", [])

    print(f"[2/2] Validation et injection...")
    created, rejected = [], []
    seen_in_batch = set()

    for entity in entities:
        issues = validate_auto_entity(entity, existing_entities, seen_in_batch)
        nom = entity.get("nom", "?")
        slug = slugify(nom)

        if issues:
            print(f"  ✗ {nom} :")
            for i in issues:
                print(f"     - {i}")
            rejected.append({"entity": entity, "issues": issues})
            continue

        seen_in_batch.add(slug)
        scenarios = entity.get("scenarios_instances") or list(SCENARIOS)

        print(f"  ✓ {nom} ({entity['category']})")
        if dry_run:
            print(json.dumps(entity, ensure_ascii=False, indent=2))
        if not dry_run:
            write_entity_file(
                nom, slug, entity["category"], entity["description_complete"],
                entity["tension_fondamentale"], entity.get("variables_potentielles", []),
                scenarios,
            )
            append_to_entities_list({
                "nom": nom, "slug": slug, "categorie": entity["category"],
                "description": entity["description_complete"],
                "tension_fondamentale": entity["tension_fondamentale"],
                "variables_potentielles": entity.get("variables_potentielles", []),
                "scenarios": scenarios,
            })
        created.append({"nom": nom, "slug": slug, "scenarios": scenarios})

    print(f"\nTerminé. {len(created)}/{len(entities)} entités créées.")
    if rejected:
        print(f"{len(rejected)} entité(s) rejetée(s) — voir le détail ci-dessus.")
    if created and not dry_run:
        print("→ Lancez ensuite generate_instances.py pour générer les instances.")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Appelle Claude et valide, mais n'écrit rien sur disque.")
    args = parser.parse_args()

    client = get_client()

    mode = input("Mode : custom ou auto ? [custom/auto] : ").strip().lower()
    while mode not in ("custom", "auto"):
        mode = input("Réponds 'custom' ou 'auto' : ").strip().lower()

    if mode == "custom":
        run_custom_mode(client, dry_run=args.dry_run)
    else:
        run_auto_mode(client, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
