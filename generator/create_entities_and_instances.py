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

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
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
INSTANCE_MAX_TOKENS = 4000  # cf. TODO historique : 2000 jugé trop juste

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
    "réseau", "humain", "système", "hybride", "autre", "média", "territoire",
]

VALID_ETATS = ["actif", "disparu", "transformé", "clandestin", "historique", "mythifié"]

SLUG_PATTERN = re.compile(r"^[a-z0-9_]+$")


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
        summary = m.group(1).strip()[:300]
    return {
        "state_of_system": fm.get("state_of_system", ""),
        "tension_level": fm.get("tension_level", ""),
        "trajectory": fm.get("trajectory", ""),
        "political_regime": fm.get("political_regime", ""),
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
    """{slug_instance: nom} pour les instances déjà existantes dans CE
    scénario — utilisé pour proposer de vraies alliances/oppositions
    (slugs valides) plutôt que du texte libre inventé."""
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
# Registre anti-doublon (_entities_list.json)
# ---------------------------------------------------------------------------

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

def get_client():
    """Conservé pour compatibilité — retourne None, call_claude_json n'en a plus besoin."""
    return None


def call_claude_json(client, system, user_content, max_tokens=3000):
    text = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
        task_tier="structured_strict",
    ).strip()

    if not text:
        raise RuntimeError("Réponse LLM vide.")

    candidate = re.sub(r"^```(?:json)?\s*", "", text)
    candidate = re.sub(r"\s*```$", "", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Filet de sécurité : le modèle raisonne parfois en texte libre avant
    # de donner le JSON final malgré la consigne — on cherche le dernier
    # bloc {...} complet plutôt que d'exiger une réponse 100% JSON pure.
    matches = re.findall(r"\{(?:[^{}]|\{[^{}]*\})*\}", text)
    if matches:
        try:
            return json.loads(matches[-1])
        except json.JSONDecodeError:
            pass

    # Bug corrigé le 11 juillet 2026 : ce bloc référençait encore `resp`
    # (objet de réponse brut du SDK Anthropic, d'avant la migration vers
    # llm_client.py) pour distinguer une troncature max_tokens d'un autre
    # échec de parsing JSON. call_llm() ne retourne qu'une chaîne de texte,
    # `resp` n'existe plus — NameError silencieux jamais déclenché jusqu'ici
    # car ce chemin n'est atteint qu'en échec de parsing JSON total. On ne
    # peut plus distinguer les deux cas avec certitude ; heuristique : une
    # réponse proche de max_tokens en longueur est probablement tronquée.
    likely_truncated = len(text) >= max_tokens * 3  # ~3-4 car/token en français
    if likely_truncated:
        raise RuntimeError(
            f"Réponse LLM probablement tronquée (max_tokens={max_tokens}, "
            f"{len(text)} caractères reçus, aucun JSON complet trouvé) — "
            f"texte reçu: {text[:200]!r}"
        )
    raise RuntimeError(f"Aucun JSON exploitable trouvé dans la réponse : {text[:200]!r}")


# =============================================================================
# PARTIE 1 — CRÉATION D'ENTITÉ (ex create_entity.py)
# =============================================================================

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


# =============================================================================
# PARTIE 2 — GÉNÉRATION D'INSTANCE (ex generate_instances.py)
# =============================================================================

def build_instance_prompt(entity_fm, scenario, hard_constraint=None, exclude_slug=None,
                          zone_hint=None):
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

    zone_hint_block = ""
    if zone_hint:
        zone_hint_block = f"""
## ANCRAGE GÉOGRAPHIQUE (hint utilisateur)
L'utilisateur souhaite ancrer cette entité dans la zone : **{zone_hint}**
Tiens-en compte pour la localisation, les responsabilités et le contexte
narratif — mais reste cohérent avec la logique du scénario.
"""

    constraint_block = ""
    role_etat_instruction = ""
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

{zone_hint_block}## ÉTAT DES VARIABLES INFLUENCÉES DANS CE SCÉNARIO
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

RÈGLE STRICTE pour "impact_local" et "impact_systemique_global" : entiers
sur une échelle de 0 à 5 UNIQUEMENT (0 = négligeable, 5 = maximal/dominant).
Jamais une autre échelle (pas de note sur 10, pas de pourcentage sur 100).
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

    for field in ("impact_local", "impact_systemique_global"):
        val = data.get(field)
        try:
            v = int(val)
            if not (0 <= v <= 5):
                issues.append(f"{field} hors plage [0-5] : {val!r} "
                               f"(échelle attendue 0-5, pas 0-10 ni 0-100)")
        except (TypeError, ValueError):
            issues.append(f"{field} invalide (doit être un entier 0-5) : {val!r}")

    if hard_constraint:
        if data.get("etat_temporel") != hard_constraint["etat"]:
            issues.append(
                f"etat_temporel ({data.get('etat_temporel')!r}) ne respecte pas "
                f"la contrainte dure ({hard_constraint['etat']!r})"
            )
    return issues


def clean_relations(data, available_instances):
    """Filtre silencieusement les entrées alliances/oppositions qui ne
    sont pas des slugs valides référençant une instance existante du
    même scénario, plutôt que de rejeter toute la fiche."""
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
    annee_fin_str = instance_data.get("annee_fin")
    annee_fin_str = "" if annee_fin_str is None else str(annee_fin_str)

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


def process_entity_scenario(client, entity_fm, scenario, force=False, dry_run=False):
    """Génère UNE instance pour UNE entité dans UN scénario. Retourne un
    statut sans jamais lever d'exception non gérée — les échecs sont
    capturés ici pour ne pas interrompre la chaîne (résilience voulue)."""
    slug_entite = entity_fm["slug"]

    if instance_exists(slug_entite, scenario) and not force:
        print(f"    → {scenario}... (déjà existant)")
        return {"status": "skipped"}

    hard_constraint = None
    if entity_fm.get("scenario_ref") == scenario:
        hard_constraint = {
            "role": entity_fm.get("role_ref", ""),
            "etat": entity_fm.get("etat_ref", ""),
        }

    print(f"    → {scenario}"
          f"{' [CONTRAINTE DURE]' if hard_constraint else ''}...", end=" ", flush=True)

    prompt = build_instance_prompt(
        entity_fm, scenario, hard_constraint=hard_constraint,
        exclude_slug=f"{slug_entite}_{scenario}",
        zone_hint=entity_fm.get("zone_hint"),
    )
    try:
        instance_data = call_claude_json(client, "Tu es un expert en worldbuilding.",
                                          prompt, max_tokens=INSTANCE_MAX_TOKENS)
    except Exception as e:
        print(f"✗ ({e})")
        return {"status": "error", "error": str(e)}

    issues = validate_instance(instance_data, hard_constraint=hard_constraint)
    if issues:
        print("✗")
        for i in issues:
            print(f"       - {i}")
        return {"status": "needs_review", "issues": issues, "instance_data": instance_data}

    available_instances = load_instances_in_scenario(
        scenario, exclude_slug=f"{slug_entite}_{scenario}"
    )
    instance_data, dropped_relations = clean_relations(instance_data, available_instances)
    if dropped_relations:
        for field, value in dropped_relations:
            print(f"\n       ⚠ {field} filtrée (pas un slug valide) : '{value}'", end="")
        print()

    if not dry_run:
        write_instance_file(entity_fm, scenario, instance_data)
    print("✓")
    if dry_run:
        print(json.dumps(instance_data, ensure_ascii=False, indent=2))
    return {"status": "created", "instance_data": instance_data}


def generate_instances_for_entity(client, entity_fm, scenarios, dry_run=False):
    """Enchaîne la génération de toutes les instances d'UNE entité
    fraîchement créée, sur la liste de scénarios fournie. Continue même
    si une instance échoue (résilience voulue)."""
    stats = {"created": 0, "skipped": 0, "errors": 0}
    print(f"  Instances ({len(scenarios)} scénario(s)) :")
    for scenario in scenarios:
        outcome = process_entity_scenario(client, entity_fm, scenario, dry_run=dry_run)
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
    instance_stats = generate_instances_for_entity(client, entity_fm, scenarios, dry_run=dry_run)

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
def run_custom_mode(client, dry_run):
    queue = load_yaml_list(QUEUE_PATH, key="queue")
    if not queue:
        print(f"Queue vide ({QUEUE_PATH}). Rien à faire.")
        return

    remaining = []
    total_instance_stats = {"created": 0, "skipped": 0, "errors": 0}

    for idea in queue:
        try:
            outcome = process_custom_idea(client, idea, dry_run=dry_run)
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

def run_auto_mode(client, dry_run, n=None, category_hint=None, scenarios_only=None):
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
        instance_stats = generate_instances_for_entity(client, entity_fm, scenarios, dry_run=dry_run)
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
        run_custom_mode(client, dry_run=args.dry_run)
    elif mode == "auto":
        run_auto_mode(client, dry_run=args.dry_run, n=args.n,
                       category_hint=args.category, scenarios_only=args.scenario)
    else:
        run_auto_suggest_mode(client, dry_run=args.dry_run, n=args.n,
                               scenario_filter=args.scenario)


if __name__ == "__main__":
    main()
