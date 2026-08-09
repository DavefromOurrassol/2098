#!/usr/bin/env python3
"""
create_entities_and_instances.py — Ourrassol 2098
=====================================================

Script unifié, fusion de create_entity.py (création des fiches entité,
archétypes) et generate_instances.py (génération des instances par
scénario) — fusion prévue dès le départ (voir HANDOFF du 20 juin),
développés séparément pour itérer plus vite, réunis ici une fois les
deux briques stabilisées.

CHANGEMENT DE COMPORTEMENT PAR RAPPORT AUX DEUX SCRIPTS D'ORIGINE :
les instances sont désormais générées AUTOMATIQUEMENT à la suite de
chaque entité créée, dans le même run — plus besoin de relancer un
second script. Les deux anciens scripts restent dans generator/ à
titre d'archive / référence mais ne sont plus le flux recommandé.

DEUX MODES, demandés interactivement au lancement :

  custom — décris UNE instance précise (nom, catégorie, rôle, état
           dans UN scénario de référence) dans
           entites_custom/queue.yaml. Le LLM déduit l'archétype, crée
           l'entité, PUIS enchaîne automatiquement la génération de
           toutes ses instances (scenario_hint, ou les 6 scénarios par
           défaut) — celle du scenario_ref avec rôle/état imposés en
           contrainte dure, les autres entièrement libres.

  auto   — donne un nombre N. Le LLM invente N entités, chacune avec
           ses scenarios_instances proposés. Chaque entité créée avec
           succès enchaîne automatiquement la génération de ses
           instances dans CES scénarios précis (pas systématiquement
           les 6 — ceux que le LLM a jugés pertinents pour elle).

RÉSILIENCE : si une instance échoue (erreur API, validation rejetée)
pour une entité, le script continue avec les scénarios/entités
suivants plutôt que de tout arrêter — même comportement que l'ancien
generate_instances.py.

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...

USAGE
-----
    python3 create_entities_and_instances.py
    python3 create_entities_and_instances.py --dry-run   # rien n'est écrit
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from llm_client import call_llm  # tier structured_strict — canonique/référencé


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from llm_client import call_llm  # tier structured_strict — canonique/référencé

from instance_generation_common import (
    SCENARIOS, VALID_VARS, VALID_ETATS, SLUG_PATTERN, INSTANCE_MAX_TOKENS,
    parse_md, get_client, call_claude_json, build_instance_prompt,
    validate_instance, clean_relations, write_instance_file,
    process_entity_scenario, instance_exists, load_instances_in_scenario,
    load_scenario_context, load_variables_states, load_etat_monde_reel,
    load_scenario_timeline_summary, detect_registre_leakage,
    _normalize_for_matching,
)


# ---------------------------------------------------------------------------
# Configuration propre à ce script (le reste — constantes partagées,
# construction de prompt, appel LLM, validation, écriture fichier — vit
# désormais dans instance_generation_common.py. Factorisation faite le
# 9 août 2026, en préalable au chantier trajectoire, après découverte que
# ce fichier et generate_instances.py avaient ~20 fonctions dupliquées
# ayant déjà divergé — voir instance_generation_common.py pour le détail.)
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
GENERATOR_DIR = Path(__file__).resolve().parent
VARIABLES_DIR = VAULT_ROOT / "variables"
SCENARIOS_DIR = VAULT_ROOT / "scenarios"
ENTITES_DIR = VAULT_ROOT / "entites"
INSTANCES_DIR = VAULT_ROOT / "instances"
ENTITES_LIST_PATH = ENTITES_DIR / "_entities_list.json"
GEOGRAPHIE_DIR       = VAULT_ROOT / "geographie"
EVENT_INSTANCES_DIR  = VAULT_ROOT / "event_instances"
ENTITES_CUSTOM_DIR   = VAULT_ROOT / "entites_custom"
QUEUE_PATH = ENTITES_CUSTOM_DIR / "queue.yaml"
PROCESSED_PATH = ENTITES_CUSTOM_DIR / "processed.yaml"
NEEDS_REVIEW_PATH = ENTITES_CUSTOM_DIR / "needs_review.yaml"

MAX_FIX_ATTEMPTS = 2

# ---------------------------------------------------------------------------
# Lecture du contexte (variables / scénarios)
# ---------------------------------------------------------------------------

VALID_CATEGORIES = [
    "IA", "organisation", "entreprise", "institution", "infrastructure",
    "réseau", "humain", "système", "hybride", "autre", "média", "territoire",
]



def build_variables_summary():
    chunks = []
    for slug in VALID_VARS:
        fm, _ = parse_md(VARIABLES_DIR / f"{slug}.md")
        domain = ", ".join(fm.get("domain", []) or [])
        chunks.append(f"- {slug} (domain: {domain})")
    return "\n".join(chunks)




def load_entities_list():
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
    """
    Ajoute une entrée au registre anti-doublon (_entities_list.json).

    Fix du 4 juillet (bug #19) : dédoublonne sur `slug` avant d'ajouter —
    l'ancienne version se contentait d'un append brut, ce qui a produit
    645 entrées pour 571 slugs uniques (jusqu'à 6 copies du même slug,
    avec des descriptions différentes à chaque fois). Le résumé montré au
    LLM (build_existing_entities_summary) affichait donc les doublons tels
    quels, gonflant le prompt et brouillant le jugement anti-doublon du modèle.
    Comportement désormais : "update-or-insert" — la nouvelle entrée
    remplace l'ancienne du même slug plutôt que de s'y ajouter.
    """
    entities = load_entities_list()
    slug = entry.get("slug")
    entities = [e for e in entities if e.get("slug") != slug]
    entities.append(entry)
    save_entities_list(entities)


def build_existing_entities_summary(entities):
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
# Appels LLM
# ---------------------------------------------------------------------------



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


def step_auto_fix_entity(client, entity, issues, category_hint=None, scenarios_only=None):
    """Regénère UNE entité rejetée en mode auto, avec feedback ciblé sur
    les problèmes de validation détectés (ex. slug de variable halluciné
    par un simple manque de lettre malgré la consigne stricte de copie à
    l'identique). Ajouté le 8 août 2026 : auparavant, une seule erreur de
    ce type faisait perdre tout le slot du batch sans seconde chance —
    symétrique du mécanisme déjà existant en mode custom
    (step_custom_derive_archetype avec previous/issues)."""
    var_summary = build_variables_summary()
    issues_txt = "\n".join(f"- {i}" for i in issues)

    # Clarification explicite ajoutée le 8 août 2026 : un problème de "Slug
    # déjà utilisé" ne mentionne jamais le mot "nom" dans son message (le
    # slug est un champ dérivé, invisible pour le LLM), donc la consigne
    # générale "ne change rien sauf ce qui est concerné" ne suffisait pas
    # à faire le lien — observé en conditions réelles : le LLM renvoyait le
    # même nom identique deux fois de suite, provoquant l'échec des 2
    # tentatives de correction sur le même problème non résolu.
    if any("Slug '" in i and "déjà utilisé" in i for i in issues):
        issues_txt += (
            "\n\nPRÉCISION IMPORTANTE : le slug est calculé automatiquement "
            "à partir du champ \"nom\" (mise en minuscules, espaces et "
            "accents remplacés). Un problème de \"slug déjà utilisé\" "
            "signifie donc que \"nom\" DOIT changer — même légèrement "
            "(reformulation, synonyme, variante) — pas seulement les autres "
            "champs. Garder le même nom reproduirait exactement la même "
            "collision."
        )

    scenario_instances_hint = (
        json.dumps(scenarios_only, ensure_ascii=False) if scenarios_only
        else '["scenario1", "scenario2"]'
    )

    user_content = f"""Voici une proposition d'entité pour Ourrassol 2098 qui a été
rejetée à la validation :

{json.dumps(entity, ensure_ascii=False, indent=2)}

## PROBLÈME(S) DÉTECTÉ(S)
{issues_txt}

## VARIABLES DISPONIBLES (liste FERMÉE)
{var_summary}

TÂCHE : corrige UNIQUEMENT le(s) problème(s) listé(s) ci-dessus, sans rien
changer d'autre (nom, description, tension, catégorie restent identiques
sauf si le problème les concerne directement). Si le problème porte sur
un slug de variable, choisis le slug valide le plus proche dans la liste
ci-dessus (copié à l'IDENTIQUE, orthographe exacte).

Réponds UNIQUEMENT en JSON, même format que l'original :
{{
  "nom": "...",
  "category": "{'|'.join(VALID_CATEGORIES)}",
  "description_complete": "...",
  "tension_fondamentale": "...",
  "variables_potentielles": ["slug1", "slug2", "slug3"],
  "scenarios_instances": {scenario_instances_hint},
  "doublon_detecte": false,
  "doublon_slug": null
}}
"""
    return call_claude_json(client, "Tu es un assistant de world-building.", user_content)


def step_auto_generate_entities(client, n, existing_entities, category_hint=None, scenarios_only=None):
    var_summary = build_variables_summary()
    existing_summary = build_existing_entities_summary(existing_entities)

    if scenarios_only:
        # Contrainte dure : ne donner que le contexte des scénarios ciblés,
        # pour éviter d'inspirer le LLM avec des mondes qu'il devra de toute
        # façon ignorer.
        scenarios_summary = "\n".join(
            f"- {s}: {load_scenario_context(s)['summary'][:120]}" for s in scenarios_only
        )
    else:
        scenarios_summary = "\n".join(
            f"- {s}: {load_scenario_context(s)['summary'][:120]}" for s in SCENARIOS
        )

    category_txt = ""
    if category_hint:
        category_txt = f"\nContrainte : toutes les entités doivent être de catégorie '{category_hint}'.\n"

    scenario_constraint_txt = ""
    scenario_instances_hint = '["scenario1", "scenario2"]'
    if scenarios_only:
        scenarios_list_txt = ", ".join(f"'{s}'" for s in scenarios_only)
        scenario_constraint_txt = (
            f"\nContrainte dure : ces entités doivent exister dans TOUS les "
            f"scénarios suivants, et uniquement ceux-là : {scenarios_list_txt}. "
            f"\"scenarios_instances\" doit valoir exactement "
            f"{json.dumps(scenarios_only, ensure_ascii=False)} pour chaque "
            f"entité, jamais un autre scénario, ni une liste plus courte ou "
            f"plus longue.\n"
        )
        scenario_instances_hint = json.dumps(scenarios_only, ensure_ascii=False)

    user_content = f"""Tu dois inventer EXACTEMENT {n} nouvelle(s) entité(s) (archétypes) —
ni plus, ni moins — pour le projet Ourrassol 2098 : institutions,
organisations, mouvements, infrastructures, IA, personnages
individuels, etc. qui pourront être incarnés différemment dans chacun
des 6 scénarios du monde.
{category_txt}{scenario_constraint_txt}
## SCÉNARIOS DU MONDE
{scenarios_summary}

## VARIABLES DISPONIBLES (liste FERMÉE — voir consigne ci-dessous)
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

Contrainte dure sur "variables_potentielles" : choisis EXCLUSIVEMENT
parmi les slugs listés dans VARIABLES DISPONIBLES ci-dessus, copiés à
l'IDENTIQUE (orthographe exacte, aucune variation). N'invente JAMAIS
un nouveau slug, même s'il te semble mieux correspondre à l'entité —
si aucune variable existante ne convient parfaitement, choisis les
plus proches disponibles plutôt que d'en inventer une nouvelle.

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact,
avec exactement {n} élément(s) dans "entites" :
{{
  "entites": [
    {{
      "nom": "Nom de l'entité",
      "category": "{'|'.join(VALID_CATEGORIES)}",
      "description_complete": "description archétypale, 3-4 lignes",
      "tension_fondamentale": "1-2 lignes",
      "variables_potentielles": ["slug1", "slug2", "slug3"],
      "scenarios_instances": {scenario_instances_hint},
      "doublon_detecte": false,
      "doublon_slug": null
    }}
  ]
}}
"""
    return call_claude_json(client, "Tu es un assistant de world-building.", user_content,
                             max_tokens=4000)


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
# d'abord). Le LLM en déduira l'archétype intemporel, puis le script
# enchaînera automatiquement la génération des instances pour les
# autres scénarios. Lance ensuite :
#
#   python3 generator/create_entities_and_instances.py
#   python3 generator/create_entities_and_instances.py --dry-run
#
# CHAMPS :
#   nom            : nom de l'entité (personnage, organisation, IA...)
#   category        : IA | organisation | entreprise | institution |
#                     infrastructure | réseau | humain | système |
#                     hybride | autre | média
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
#   zone_hint       : optionnel. null si tu ne sais pas — le LLM choisit
#                     librement l'ancrage géographique. Sinon une zone
#                     (chaîne libre, ex: "Bassin du Congo") que tu IMPOSES
#                     comme lieu d'ancrage de l'entité — injectée
#                     directement dans le prompt de génération.
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
#     zone_hint: null
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


# =============================================================================
# PARTIE 2 — GÉNÉRATION D'INSTANCE (ex generate_instances.py)
# =============================================================================



def generate_instances_for_entity(client, entity_fm, scenarios, dry_run=False,
                                   ancrage_temporel="libre"):
    """Enchaîne la génération de toutes les instances d'UNE entité
    fraîchement créée, sur la liste de scénarios fournie. Continue même
    si une instance échoue (résilience voulue)."""
    stats = {"created": 0, "skipped": 0, "errors": 0}
    print(f"  Instances ({len(scenarios)} scénario(s)) :")
    for scenario in scenarios:
        outcome = process_entity_scenario(client, entity_fm, scenario, dry_run=dry_run,
                                           ancrage_temporel=ancrage_temporel,
                                           log_prefix="    →")
        if outcome["status"] == "created":
            stats["created"] += 1
        elif outcome["status"] == "skipped":
            stats["skipped"] += 1
        else:
            stats["errors"] += 1
        time.sleep(0.3)
    return stats


# =============================================================================
# ORCHESTRATION — mode custom
# =============================================================================

def process_custom_idea(client, idea, dry_run=False, ancrage_temporel="libre"):
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
    archetype = step_custom_derive_archetype(client, idea, existing_entities)
    issues = None
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
    print("[3/3] Injection de l'entité...")
    zone_hint = idea.get("zone_hint") or None

    entity_fm = {
        "name": nom, "slug": slug, "category": category,
        "description": archetype["description_complete"],
        "tension_fondamentale": archetype["tension_fondamentale"],
        "variables_potentielles": archetype["variables_potentielles"],
        "scenario_ref": scenario_ref,
        "role_ref": idea.get("role"),
        "etat_ref": idea.get("etat"),
        "zone_hint": zone_hint,
    }

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

    # Enchaînement automatique : génération des instances pour cette entité
    print(f"[Instances] Génération automatique pour {len(scenarios)} scénario(s)...")
    instance_stats = generate_instances_for_entity(client, entity_fm, scenarios, dry_run=dry_run,
                                                     ancrage_temporel=ancrage_temporel)

    return {
        "status": "injected", "idea": idea, "slug": slug,
        "scenarios": scenarios, "archetype": archetype,
        "scenario_ref": scenario_ref,
        "role_ref": idea.get("role"), "etat_ref": idea.get("etat"),
        "instance_stats": instance_stats,
    }


# NB (4 juillet) : le rate limiting (429) est désormais géré de façon
# centralisée et purement réactive dans llm_client.py (call_llm), qui
# retente automatiquement avec un délai croissant en cas de 429 — pour
# TOUS les scripts du pipeline, pas seulement celui-ci. Pas de pause
# artificielle ajoutée ici : voir llm_client.py pour le détail.
def run_custom_mode(client, dry_run, ancrage_temporel="libre"):
    queue = load_yaml_list(QUEUE_PATH, key="queue")
    if not queue:
        print(f"Queue vide ({QUEUE_PATH}). Rien à faire.")
        return

    remaining = []
    total_instance_stats = {"created": 0, "skipped": 0, "errors": 0}

    for idea in queue:
        try:
            outcome = process_custom_idea(client, idea, dry_run=dry_run,
                                           ancrage_temporel=ancrage_temporel)
        except Exception as e:
            outcome = {"status": "needs_review", "idea": idea, "error": str(e)}

        if dry_run:
            print(json.dumps(
                {k: v for k, v in outcome.items() if k != "instance_stats"},
                ensure_ascii=False, indent=2, default=str
            ))
            remaining.append(idea)
            continue

        if outcome["status"] == "injected":
            stats = outcome.get("instance_stats", {})
            for k in total_instance_stats:
                total_instance_stats[k] += stats.get(k, 0)
            append_yaml_list(PROCESSED_PATH, {
                k: v for k, v in outcome.items() if k != "instance_stats"
            }, key="processed")
        else:
            append_yaml_list(NEEDS_REVIEW_PATH, outcome, key="needs_review")

    if not dry_run:
        save_queue_with_template(remaining)
        print(f"\nTerminé. Voir {PROCESSED_PATH} et {NEEDS_REVIEW_PATH}.")
        print(f"Instances : {total_instance_stats['created']} créée(s) | "
              f"{total_instance_stats['skipped']} déjà existante(s) | "
              f"{total_instance_stats['errors']} erreur(s)")
        if total_instance_stats['created'] > 0:
            run_post_injection_cycle()



# =============================================================================
# MODE AUTO — analyse du vault + génération d'idées → queue.yaml
# =============================================================================

def load_all_zones(scenario):
    """Charge toutes les zones d'un scénario depuis geographie/{scenario}.md."""
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    if not path.exists():
        return {}
    fm, _ = parse_md(path)
    zones_list = fm.get("zones", []) or []
    return {z["slug"]: z for z in zones_list if isinstance(z, dict) and "slug" in z}


def analyze_entity_coverage():
    """
    Analyse la couverture actuelle du vault (entités/instances) :
    - Distribution géographique des instances (zone → count par scénario)
    - Zones absentes (0 instance) par scénario
    - Distribution par catégorie d'entité
    - Entités déjà existantes (anti-doublon)
    """
    geo_coverage  = {}   # scenario → {zone: count}
    geo_absent    = {}   # scenario → [slug_zone sans instance]
    cat_coverage  = {}   # category → count global
    existing_entities = load_entities_list()

    for sc in SCENARIOS:
        geo_coverage[sc] = {}

    if INSTANCES_DIR.exists():
        for path in sorted(INSTANCES_DIR.glob("*.md")):
            fm, _ = parse_md(path)
            sc = fm.get("scenario", "")
            if sc not in SCENARIOS:
                continue
            loc = fm.get("localisation") or {}
            if isinstance(loc, dict):
                zone = loc.get("zone") or "inconnue"
                geo_coverage[sc][zone] = geo_coverage[sc].get(zone, 0) + 1

    # Zones absentes : présentes dans geographie/ mais sans aucune instance
    for sc in SCENARIOS:
        all_zones = load_all_zones(sc)
        covered = set(geo_coverage[sc].keys())
        absent = [slug for slug in all_zones if slug not in covered]
        geo_absent[sc] = absent

    for e in existing_entities:
        cat = e.get("categorie", "autre")
        cat_coverage[cat] = cat_coverage.get(cat, 0) + 1

    return {
        "geo_coverage":       geo_coverage,
        "geo_absent":         geo_absent,
        "cat_coverage":       cat_coverage,
        "existing_entities":  existing_entities,
    }


def build_entity_analysis_summary(coverage, scenario_filter=None):
    """Résumé textuel de l'analyse pour le prompt LLM. scenario_filter : liste
    de scénarios à considérer, ou None pour les 6 par défaut."""
    lines = []
    scenarios = scenario_filter if scenario_filter else SCENARIOS

    lines.append("## Couverture géographique actuelle (instances)")
    for sc in scenarios:
        geo = coverage["geo_coverage"].get(sc, {})
        if geo:
            top = sorted(geo.items(), key=lambda x: -x[1])[:5]
            lines.append(f"  {sc}: " + ", ".join(f"{z}({n})" for z, n in top))
        else:
            lines.append(f"  {sc}: (aucune)")

    lines.append("")
    lines.append("## Zones sans aucune instance (à couvrir en priorité)")
    for sc in scenarios:
        absent = coverage["geo_absent"].get(sc, [])
        if absent:
            lines.append(f"  {sc}: " + ", ".join(absent[:20]))
            if len(absent) > 20:
                lines.append(f"    ... et {len(absent) - 20} autres")
        else:
            lines.append(f"  {sc}: (toutes les zones ont au moins une instance)")

    lines.append("")
    lines.append("## Distribution par catégorie")
    cc = coverage["cat_coverage"]
    if cc:
        lines.append("  " + ", ".join(f"{c}({n})" for c, n in sorted(cc.items(), key=lambda x: -x[1])))
    else:
        lines.append("  (aucune entité)")

    return "\n".join(lines)


def build_scenarios_summary_for_entity_auto(scenario_filter=None):
    """Résumé des scénarios pour le prompt auto entités."""
    scenarios = [scenario_filter] if scenario_filter else SCENARIOS
    lines = []
    for sc in scenarios:
        from pathlib import Path as _Path
        fm, body = parse_md(SCENARIOS_DIR / f"{sc}.md")
        import re as _re
        summary = ""
        m = _re.search(r"\*\*Résumé\*\*\s*\n(.+?)(?=\n\*\*|\n##|\Z)", body, _re.DOTALL)
        if m:
            summary = m.group(1).strip()[:150]
        lines.append(f"- {sc}: {fm.get('state_of_system','')} | tension {fm.get('tension_level','?')}/5 | {summary}")
    return "\n".join(lines)


def step_auto_suggest_entities(client, n, coverage, scenario_filter=None):
    """
    Appelle le LLM pour suggérer N idées d'entités contextualisées
    en fonction des déséquilibres détectés.
    Retourne une liste d'idées au format queue.yaml entités.
    """
    analysis = build_entity_analysis_summary(coverage, scenario_filter)
    existing_entities = coverage["existing_entities"]
    existing_summary  = build_existing_entities_summary(existing_entities)
    var_summary       = build_variables_summary()

    scenario_instruction = ""
    if scenario_filter:
        scenarios_list_txt = ", ".join(f"'{s}'" for s in scenario_filter)
        scenario_instruction = (
            f"\nOrientation (pas une contrainte dure) : privilégie ces "
            f"scénarios comme référence pour les entités proposées : "
            f"{scenarios_list_txt}."
        )

    user_content = f"""Tu dois proposer {n} idée(s) d'entités custom pour le projet Ourrassol 2098.
Ces idées seront écrites dans queue.yaml pour être inspectées et créées en mode custom.

## ANALYSE DES DÉSÉQUILIBRES DU VAULT
{analysis}

## ENTITÉS DÉJÀ EXISTANTES (anti-doublon)
{existing_summary}

## VARIABLES DISPONIBLES
{var_summary}
{scenario_instruction}

## CONSIGNE
- Compense les déséquilibres : couvre les zones géographiques sous-représentées,
  les catégories peu présentes.
- Chaque entité doit avoir une fonction systémique distincte des existantes.
- Propose le scénario de référence le plus cohérent pour chaque entité.
- Pour un ancrage géographique précis, mentionne le lieu dans le champ role.
- Ne recrée pas une entité déjà existante (même fonction, même niche narrative).

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact :
{{
  "entites": [
    {{
      "nom": "Nom de l'entité",
      "category": "{'|'.join(VALID_CATEGORIES)}",
      "role": "Rôle précis dans le scénario de référence, 2-3 lignes, avec lieu géographique explicite.",
      "etat": "{'|'.join(VALID_ETATS)}",
      "scenario_ref": "nom_du_scenario",
      "scenario_hint": null,
      "source": "auto_generated",
      "rationale": "Pourquoi cette entité comble un déséquilibre du vault (1 ligne)."
    }}
  ]
}}
"""
    from datetime import datetime as _dt
    result = call_claude_json(client, "Tu es un assistant de world-building pour Ourrassol 2098.", user_content)
    return result.get("entites", [])


def run_auto_suggest_mode(client, dry_run, n=None, scenario_filter=None):
    """Mode auto-suggest : analyse le vault, génère des idées, les ajoute à queue.yaml."""
    if n is None:
        raw_n = input("Nombre d'idées à générer ? [défaut: 3] : ").strip()
        try:
            n = int(raw_n) if raw_n else 3
            if n < 1:
                n = 3
        except ValueError:
            n = 3

    if scenario_filter is None:
        scenario_raw = input(
            "Scénario de référence ciblé ? (Entrée pour laisser le LLM choisir) [{}] : ".format(
                "|".join(SCENARIOS)
            )
        ).strip()
        scenario_filter = scenario_raw if scenario_raw in SCENARIOS else None

    print("\n[1/2] Analyse de la couverture du vault...")
    coverage = analyze_entity_coverage()
    n_inst = sum(len(v) for v in coverage["geo_coverage"].values())
    print(f"  {n_inst} instance(s) analysée(s) | {len(coverage['existing_entities'])} entité(s) existante(s)")
    if scenario_filter:
        print(f"  Filtre scénario : {scenario_filter}")

    print(f"[2/2] Génération de {n} idée(s) d'entités...")
    ideas = step_auto_suggest_entities(client, n, coverage, scenario_filter)

    if not ideas:
        print("Aucune idée générée — vérifier la réponse du LLM.")
        return

    queue_ideas = []
    for idea in ideas:
        rationale = idea.pop("rationale", "")
        queue_ideas.append(idea)
        print(f"  ✓ {idea.get('nom')} ({idea.get('category')}) — ref: {idea.get('scenario_ref')}")
        if rationale:
            print(f"    → {rationale}")

    if dry_run:
        print("\n[DRY-RUN] Idées générées (non écrites dans queue.yaml) :")
        import yaml as _yaml
        print(_yaml.dump({"queue": queue_ideas}, allow_unicode=True, default_flow_style=False))
        return

    existing = load_yaml_list(QUEUE_PATH, key="queue")
    merged = existing + queue_ideas
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(
        __import__('yaml').dump({"queue": merged}, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8"
    )

    print(f"\n{len(queue_ideas)} idée(s) ajoutée(s) à {QUEUE_PATH}")
    print("→ Inspectez queue.yaml, puis relancez en mode custom pour créer les entités.")


# =============================================================================
# ORCHESTRATION — mode auto
# =============================================================================

def run_auto_mode(client, dry_run, n=None, category_hint=None, scenarios_only=None,
                   ancrage_temporel="libre"):
    if n is None:
        raw = input("Combien d'entités générer ? : ").strip()
        try:
            n = int(raw)
        except ValueError:
            print("Nombre invalide.")
            return
    if n < 1:
        print("Le nombre doit être >= 1.")
        return

    if category_hint is None:
        category_raw = input(
            "Catégorie imposée (optionnel, Entrée pour libre) [{}] : ".format(
                "|".join(VALID_CATEGORIES)
            )
        ).strip()
        category_hint = category_raw if category_raw in VALID_CATEGORIES else None

    existing_entities = load_entities_list()

    print(f"\n[1/2] Génération de {n} entité(s)"
          + (f" (scénarios : {', '.join(scenarios_only)})" if scenarios_only else "") + "...")
    result = step_auto_generate_entities(client, n, existing_entities, category_hint, scenarios_only)
    entities = result.get("entites", [])

    if len(entities) != n:
        print(f"  ⚠ {len(entities)} entité(s) reçue(s) au lieu de {n} demandée(s) "
              f"— troncature au nombre exact demandé.")
        entities = entities[:n]

    print(f"[2/2] Validation, injection et génération des instances...")
    created, rejected = [], []
    seen_in_batch = set()
    total_instance_stats = {"created": 0, "skipped": 0, "errors": 0}

    for entity in entities:
        issues = validate_auto_entity(entity, existing_entities, seen_in_batch)
        nom = entity.get("nom", "?")

        fix_attempts = 0
        while issues and fix_attempts < MAX_FIX_ATTEMPTS:
            print(f"\n  ⚠ {nom} : {len(issues)} problème(s), "
                  f"tentative de correction {fix_attempts + 1}/{MAX_FIX_ATTEMPTS}...")
            for i in issues:
                print(f"     - {i}")
            try:
                entity = step_auto_fix_entity(client, entity, issues, category_hint, scenarios_only)
            except Exception as e:
                print(f"     (échec de la tentative de correction : {e})")
                break
            nom = entity.get("nom", "?")
            issues = validate_auto_entity(entity, existing_entities, seen_in_batch)
            fix_attempts += 1

        slug = slugify(nom)

        if issues:
            print(f"\n  ✗ {nom} :")
            for i in issues:
                print(f"     - {i}")
            rejected.append({"entity": entity, "issues": issues})
            continue

        seen_in_batch.add(slug)
        if scenarios_only:
            # Filtre dur : garantit la contrainte --scenario même si le LLM
            # a ignoré la consigne du prompt (comportement déjà observé sur
            # d'autres tâches contraintes le 11 juillet 2026, cf. bug #26).
            scenarios = list(scenarios_only)
        else:
            scenarios = entity.get("scenarios_instances") or list(SCENARIOS)
            scenarios = [s for s in scenarios if s in SCENARIOS] or list(SCENARIOS)

        print(f"\n  ✓ {nom} ({entity['category']})")
        if dry_run:
            print(json.dumps(entity, ensure_ascii=False, indent=2))

        entity_fm = {
            "name": nom, "slug": slug, "category": entity["category"],
            "description": entity["description_complete"],
            "tension_fondamentale": entity["tension_fondamentale"],
            "variables_potentielles": entity.get("variables_potentielles", []),
        }

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

        # Enchaînement automatique des instances, dans les scénarios
        # proposés par le LLM pour CETTE entité (pas systématiquement les 6)
        instance_stats = generate_instances_for_entity(client, entity_fm, scenarios, dry_run=dry_run,
                                                          ancrage_temporel=ancrage_temporel)
        for k in total_instance_stats:
            total_instance_stats[k] += instance_stats.get(k, 0)

        created.append({"nom": nom, "slug": slug, "scenarios": scenarios})

    print(f"\nTerminé. {len(created)}/{len(entities)} entité(s) créée(s).")
    if rejected:
        print(f"{len(rejected)} entité(s) rejetée(s) — voir le détail ci-dessus.")
    print(f"Instances : {total_instance_stats['created']} créée(s) | "
          f"{total_instance_stats['skipped']} déjà existante(s) | "
          f"{total_instance_stats['errors']} erreur(s)")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Cycle post-injection automatique
# ---------------------------------------------------------------------------

def run_post_injection_cycle():
    """
    Lance automatiquement le cycle post-injection :
      extract_localisation.py → review_localisation.py --auto-resolve → validate.py
    Appelé après chaque injection réussie (hors dry-run).
    """
    generator_dir = Path(__file__).resolve().parent
    steps = [
        ("extract_localisation", [sys.executable, str(generator_dir / "extract_localisation.py")]),
        ("review_localisation",  [sys.executable, str(generator_dir / "review_localisation.py"), "--auto-resolve"]),
        ("validate",             [sys.executable, str(generator_dir / "validate.py")]),
    ]

    print("\n" + "═" * 60)
    print("CYCLE POST-INJECTION")
    print("═" * 60)

    for name, cmd in steps:
        print(f"\n→ {' '.join(cmd[1:])}")
        result = subprocess.run(cmd, cwd=str(generator_dir))
        if result.returncode != 0:
            print(f"  [WARN] {name} s'est terminé avec le code {result.returncode}.")
            print("  → Vérifiez manuellement avant de continuer.")
            break
    else:
        print("\n✓ Cycle post-injection terminé.")


def main():
    parser = argparse.ArgumentParser(
        description="Crée des entités ET leurs instances en un seul run (Ourrassol 2098)"
    )
    parser.add_argument("--dry-run", action="store_true",
                         help="Appelle le LLM et valide, mais n'écrit rien sur disque.")
    parser.add_argument("--mode", choices=("custom", "auto", "auto-suggest"), default=None,
                         help="Mode de fonctionnement. Si omis, demandé interactivement "
                              "(input()) — nécessaire pour un lancement non-interactif "
                              "(GUI Flask, cron) où aucun stdin n'est disponible.")
    parser.add_argument("--n", type=int, default=None,
                         help="Modes auto/auto-suggest uniquement : nombre d'entités/idées "
                              "à générer. Si omis, demandé interactivement.")
    parser.add_argument("--category", choices=VALID_CATEGORIES, default=None,
                         help="Mode auto uniquement : catégorie imposée à toutes les "
                              "entités générées (optionnel, libre si omis).")
    parser.add_argument("--scenario", nargs="+", choices=SCENARIOS, default=None,
                         help="Un ou plusieurs scénarios (espacés). Mode auto : "
                              "contrainte dure — chaque entité générée existera "
                              "dans exactement ces scénarios, prompt + filtre en "
                              "sortie garanti. Mode auto-suggest : orientation "
                              "pour le LLM, pas une contrainte dure appliquée en "
                              "code. Sans effet en mode custom. Omis = les 6 "
                              "scénarios par défaut (mode auto) ou libre choix du "
                              "LLM (mode auto-suggest).")
    parser.add_argument(
        "--ancrage-temporel", choices=["libre", "recent"], default="libre",
        help="'libre' (défaut) : comportement inchangé, priorité aux jalons "
             "du scénario. 'recent' : force les nouvelles instances à "
             "émerger dans les 1-3 prochaines années, ancrées dans "
             "etat_du_monde_reel.md plutôt que dans un jalon lointain. "
             "Sans effet en mode auto-suggest (ne crée pas d'instances)."
    )
    args = parser.parse_args()

    print("=" * 60)
    print("OURRASSOL 2098 — Création entités + instances")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)")

    client = get_client()

    # Bug découvert le 11 juillet 2026 (test GUI "Create entities custom") :
    # le script bloquait indéfiniment sur input() quand lancé depuis app.py
    # (subprocess.Popen sans stdin connecté) — --mode permet de contourner
    # totalement le prompt interactif pour ce cas d'usage.
    mode = args.mode
    if mode is None:
        mode = input("\nMode : custom, auto ou auto-suggest ? [custom/auto/auto-suggest] : ").strip().lower()
        while mode not in ("custom", "auto", "auto-suggest"):
            mode = input("Réponds 'custom', 'auto' ou 'auto-suggest' : ").strip().lower()
    else:
        print(f"\nMode : {mode} (fourni via --mode)")

    if mode == "custom":
        run_custom_mode(client, dry_run=args.dry_run, ancrage_temporel=args.ancrage_temporel)
    elif mode == "auto":
        run_auto_mode(client, dry_run=args.dry_run, n=args.n,
                       category_hint=args.category, scenarios_only=args.scenario,
                       ancrage_temporel=args.ancrage_temporel)
    else:
        run_auto_suggest_mode(client, dry_run=args.dry_run, n=args.n,
                               scenario_filter=args.scenario)


if __name__ == "__main__":
    main()
