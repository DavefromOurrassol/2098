#!/usr/bin/env python3
"""
inject_custom_events.py — Ourrassol 2098
==========================================

Injecte des "événements custom" (idées fournies par l'utilisateur) dans
le vault, en créant un archétype (evenements/{slug}.md) et une instance
par scénario sélectionné (event_instances/{slug}_{scenario}.md) — même
résultat que create_event.py, mais en mode batch/non-interactif, calqué
sur le pipeline d'inject_custom_signals.py.

PRINCIPE
--------
1. Tu remplis `evenements_custom/queue.yaml` avec une liste d'idées
   d'événements (description, portée, date, intensité...).
2. Tu lances :  python3 inject_custom_events.py
3. Pour chaque idée, le script :
     - sélectionne les variables impactées (si non imposées) et un slug
       d'événement (étape 1, appel API)
     - pour chaque scénario sélectionné : génère l'instance (étape 2,
       appel API), en s'appuyant sur le contexte du scénario, les
       niveaux des variables, le registre des événements (anti-collision
       partagée avec les signaux), et la liste des instances d'entités
       déjà existantes pour ce scénario (pour des acteurs cohérents)
     - valide mécaniquement le résultat (deltas dans une plage
       raisonnable, variables valides, acteurs correspondant à des
       instances réelles, JSON complet) — purement Python
     - si la validation échoue, rappelle Claude (étape 3, correction
       ciblée) jusqu'à 2 fois
     - injecte l'archétype (1ère fois seulement) + chaque instance
       validée
     - met à jour registre_evenements.md (type=evenement)
     - déplace l'idée de queue.yaml vers processed.yaml
       (ou needs_review.yaml si la validation échoue malgré les retries)

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...
    Le registre doit être au format 6 colonnes — lancer
    migrate_registre.py une seule fois avant la première utilisation
    si ce n'est pas déjà fait.

USAGE
-----
    python3 inject_custom_events.py            # traite toute la queue
    python3 inject_custom_events.py --dry-run  # appelle Claude, valide,
                                                 # affiche le résultat,
                                                 # mais n'écrit rien sur disque
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

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
VARIABLES_DIR = VAULT_ROOT / "variables"
SCENARIOS_DIR = VAULT_ROOT / "scenarios"
INSTANCES_DIR = VAULT_ROOT / "instances"
EVENEMENTS_DIR = VAULT_ROOT / "evenements"
EVENT_INSTANCES_DIR = VAULT_ROOT / "event_instances"
REGISTRE_PATH = Path(__file__).resolve().parent / "registre_evenements.md"
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"
EVENEMENTS_CUSTOM_DIR = VAULT_ROOT / "evenements_custom"
QUEUE_PATH = EVENEMENTS_CUSTOM_DIR / "queue.yaml"
PROCESSED_PATH = EVENEMENTS_CUSTOM_DIR / "processed.yaml"
NEEDS_REVIEW_PATH = EVENEMENTS_CUSTOM_DIR / "needs_review.yaml"


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

VALID_PORTEES = ["locale", "regionale", "continentale", "globale"]
VALID_INTENSITES = ["faible", "modérée", "forte", "majeure"]
VALID_TYPES_EVENEMENTS = [
    "technological", "systemic", "political_social", "cultural", "environmental",
]

MAX_DELTA_LEVEL = 25  # delta_level absolu maximum jugé raisonnable par variable


# ---------------------------------------------------------------------------
# Lecture des fiches variables / scénarios / instances
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
    """Résumé condensé des 12 variables pour l'étape 1 (sélection)."""
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
        "trajectory": fm.get("trajectory", ""),
        "tension_level": fm.get("tension_level", ""),
        "political_regime": fm.get("political_regime", ""),
        "transformation_speed": fm.get("transformation_speed", ""),
        "dominant_variables": fm.get("dominant_variables", []) or [],
        "summary": summary,
    }


def load_variables_levels(scenario):
    levels = {}
    for var in VALID_VARS:
        fm, _ = parse_md(VARIABLES_DIR / f"{var}.md")
        states = fm.get("states", {}) or {}
        if scenario in states and isinstance(states[scenario], dict):
            levels[var] = states[scenario].get("level", 50)
    return levels


def load_available_actors(scenario):
    """Liste les instances d'entités existantes pour ce scénario
    (slug, name, role court) — pour que les acteurs choisis par Claude
    soient cohérents avec le lore déjà établi plutôt qu'inventés."""
    actors = []
    if not INSTANCES_DIR.exists():
        return actors
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, _ = parse_md(path)
        slug = fm.get("slug", path.stem)
        name = fm.get("name", slug)
        role = str(fm.get("role_dans_scenario", "")).strip()
        role_short = re.sub(r"\s+", " ", role)[:120]
        actors.append({"slug": slug, "name": name, "role": role_short})
    return actors


# ---------------------------------------------------------------------------
# Registre des événements (partagé avec inject_custom_signals.py)
# ---------------------------------------------------------------------------

def read_registre_text():
    if not REGISTRE_PATH.exists():
        return ""
    return REGISTRE_PATH.read_text(encoding="utf-8")


def parse_registre_table(scen_body):
    rows = []
    table_started = False
    for line in scen_body.split("\n"):
        if line.startswith("|---"):
            table_started = True
            continue
        if table_started and line.startswith("|"):
            cols = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cols)
        elif table_started and not line.startswith("|"):
            break
    return rows


def get_registre_excerpt_for_variables(registre_text, variables, scenario):
    """Filtre le registre aux lignes concernant les variables données,
    pour le scénario en cours — anti-collision ciblée pour l'étape 2."""
    lines_out = []
    parts = re.split(r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text)
    for i in range(1, len(parts), 2):
        scen = parts[i]
        if scen != scenario:
            continue
        body = parts[i + 1]
        for cols in parse_registre_table(body):
            if len(cols) < 6:
                continue
            row_vars = [v.strip() for v in cols[3].split(",")]
            if any(v in row_vars for v in variables):
                lines_out.append("| " + " | ".join(cols) + " |")
    return "\n".join(lines_out)


def get_all_evenements(registre_text):
    events = set()
    parts = re.split(r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text)
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        for cols in parse_registre_table(body):
            if len(cols) >= 6:
                events.add(cols[5].strip().lower())
    return events


def regenerate_registre_with_event(scenario, event_slug, variables, date, evenement_cle):
    """Ajoute une ligne type=evenement au registre pour ce scénario."""
    registre_text = read_registre_text()
    parts = re.split(r"(\n## (?:" + "|".join(SCENARIOS) + r")\n)", registre_text)
    output = [parts[0]]

    for i in range(1, len(parts), 2):
        header = parts[i]
        body = parts[i + 1]
        scen = header.strip().replace("## ", "")

        lines = body.split("\n")
        table_start = None
        for idx, l in enumerate(lines):
            stripped = l.strip()
            is_separator = (
                stripped.startswith('|---')
                or stripped.startswith('| ---')
                or (stripped.startswith('|') and '---' in stripped and stripped.replace('|','').replace('-','').replace(' ','').replace(':','') == '')
            )
            if is_separator:
                table_start = idx
                break

        if table_start is None:
            # Pas de table trouvée pour ce scénario — on ne peut pas injecter
            raise ValueError(f"Pas de table trouvée dans le registre pour le scénario {scen!r}")

        rows = []
        end_idx = len(lines)
        for idx in range(table_start + 1, len(lines)):
            l = lines[idx]
            if not l.startswith("|"):
                end_idx = idx
                break
            cols = [c.strip() for c in l.strip("|").split("|")]
            rows.append(cols)

        if scen == scenario:
            rows.append([
                "evenement", str(date), event_slug, ", ".join(variables),
                "—", evenement_cle,
            ])

        def date_key(row):
            try:
                return int(row[1].split("-")[0])
            except Exception:
                return 9999

        rows.sort(key=date_key)

        new_table_lines = ["| " + " | ".join(r) + " |" for r in rows]
        new_body_lines = lines[: table_start + 1] + new_table_lines + lines[end_idx:]
        output.append(header)
        output.append("\n".join(new_body_lines))

    new_content = "".join(output)

    all_rows = []
    parts2 = re.split(r"\n## (" + "|".join(SCENARIOS) + r")\n", new_content)
    for i in range(1, len(parts2), 2):
        all_rows.extend(parse_registre_table(parts2[i + 1]))

    signal_rows = sum(1 for r in all_rows if len(r) >= 1 and r[0] == "signal")
    evenement_rows = sum(1 for r in all_rows if len(r) >= 1 and r[0] == "evenement")
    unique_signals = signal_rows // len(SCENARIOS)

    new_content = re.sub(
        r"Total : \d+ entrées \(\d+ signaux uniques × 6 scénarios( \+ \d+ entrées d'événements custom)?\)\.",
        "Total : {} entrées ({} signaux uniques × 6 scénarios + {} entrées d'événements custom).".format(
            signal_rows + evenement_rows, unique_signals, evenement_rows
        ),
        new_content,
    )
    REGISTRE_PATH.write_text(new_content, encoding="utf-8")


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
    # Extraire le premier objet JSON valide (robustesse si Claude ajoute du texte après)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Tentative via raw_decode : extrait le premier objet JSON et ignore le reste
        try:
            obj, _ = json.JSONDecoder().raw_decode(text)
            return obj
        except json.JSONDecodeError:
            # Dernier recours : chercher le premier {...} complet
            m = re.search(r"(\{.*\})", text, re.DOTALL)
            if m:
                return json.loads(m.group(1))
            raise


def step1_select_variables_and_type(client, idea, variables_hint, variables_hint_count):
    summary = build_variables_summary()

    hints = variables_hint or []
    hints = [h for h in hints if h in VALID_VARS]
    max_vars = variables_hint_count if variables_hint_count else 2
    max_vars = max(1, min(4, max_vars))

    hint_txt = ""
    if hints:
        hint_txt = (
            f"\nL'utilisateur impose déjà ces variables comme impactées : "
            f"{', '.join(hints)}. Tu DOIS les inclure. Tu peux en ajouter "
            f"d'autres si pertinent, dans la limite du plafond ci-dessous.\n"
        )

    user_content = f"""Voici une idée d'événement à intégrer dans le simulateur de
presse fictive Ourrassol 2098 :

DESCRIPTION :
{idea['description']}

PORTÉE : {idea['portee']}
DATE APPROXIMATIVE : {idea['date_approximative']}
INTENSITÉ : {idea['intensite']}
{hint_txt}
Voici les 12 variables systémiques du système (avec leur domaine) :
{summary}

TÂCHE :
1. Choisis entre 1 et {max_vars} variables impactées par cet événement
   (privilégie 2 par défaut, plus si l'événement est clairement structurant).
2. Détermine le type d'événement parmi : {", ".join(VALID_TYPES_EVENEMENTS)}.
Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact :
{{"variables": ["slug1"], "type_evenement": "political_social"}}
"""
    return call_claude_json(client, "Tu es un assistant de world-building.", user_content)


def step2_develop_instance(client, idea, event_slug, type_evenement, variables,
                            scenario, registre_excerpt, available_actors,
                            actors_hint, previous=None, issues=None):
    sc_ctx = load_scenario_context(scenario)
    var_levels = load_variables_levels(scenario)

    vars_ctx = "\n".join(
        f"- {v} : level {var_levels.get(v, '?')}" for v in variables
    )

    actors_hint_txt = ""
    if actors_hint:
        actors_hint_txt = (
            f"\nL'utilisateur impose ces acteurs : {', '.join(actors_hint)}. "
            f"Tu DOIS les inclure si leur slug correspond à une instance "
            f"listée ci-dessous.\n"
        )

    actors_list_txt = "\n".join(
        f"  - {a['slug']} ({a['name']}) : {a['role']}" for a in available_actors
    ) or "  (aucune instance d'entité disponible pour ce scénario)"

    if previous is None:
        task = """TÂCHE : génère l'instance de cet événement pour ce scénario,
au format JSON demandé ci-dessous."""
    else:
        issues_txt = "\n".join(f"- {i}" for i in issues)
        task = f"""L'instance précédente a échoué la validation mécanique :
{issues_txt}

Voici l'instance précédente :
{json.dumps(previous, ensure_ascii=False, indent=2)}

TÂCHE : corrige UNIQUEMENT les points listés ci-dessus, en gardant le
reste identique autant que possible."""

    user_content = f"""Tu génères l'instance d'un événement custom pour le projet
Ourrassol 2098, dans le scénario "{scenario}".

## ÉVÉNEMENT
- Slug : {event_slug}
- Type : {type_evenement}
- Portée : {idea['portee']}
- Date approximative : {idea['date_approximative']}
- Intensité : {idea['intensite']}
- Description originale : {idea['description']}
{actors_hint_txt}
## SCÉNARIO {scenario.upper()}
- État : {sc_ctx['state_of_system']} | Tension : {sc_ctx['tension_level']}/5 | Trajectoire : {sc_ctx['trajectory']}
- Régime : {sc_ctx['political_regime']} | Vitesse : {sc_ctx['transformation_speed']}
- Variables dominantes : {", ".join(sc_ctx['dominant_variables'][:4])}
- Contexte : {sc_ctx['summary']}

## NIVEAUX DES VARIABLES IMPACTÉES
{vars_ctx}

## ACTEURS DISPONIBLES (instances d'entités existantes pour ce scénario)
Choisis en priorité parmi ceux-ci pour les acteurs impliqués — n'en
invente un nouveau (texte libre) que si vraiment aucun ne convient :
{actors_list_txt}

## EXTRAIT DU REGISTRE DES ÉVÉNEMENTS (anti-collision, ce scénario, ces variables)
{registre_excerpt or "(aucune entrée existante pour ces variables dans ce scénario)"}

## CONSIGNE

Règles importantes :
- L'événement DOIT être cohérent avec l'état du monde — si le scénario est
  en effondrement, l'événement reflète cet effondrement (peut ne pas se
  produire, se produire différemment, ou avoir des conséquences opposées
  à l'intention originale)
- Le nom peut être identique, une variante, ou radicalement différent
- La date peut varier de +/- 10 ans par rapport à la date approximative
- Les impacts sur les variables doivent être cohérents avec leurs levels
  actuels (pas de delta positif massif sur une variable déjà en
  effondrement), et chaque delta_level doit rester dans la plage
  raisonnable -{MAX_DELTA_LEVEL} à +{MAX_DELTA_LEVEL}
- Le champ "evenement_cle" doit être une phrase courte (4-11 mots) avec
  une année finale, sans collision avec le registre fourni ci-dessus
- Si l'événement est impossible ou absurde dans ce scénario, le dire
  clairement (impossible_dans_scenario: true) et proposer une variante
  plausible quand même

{task}

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact :
{{
  "nom": "Nom de l'événement dans ce scénario",
  "date": 2055,
  "date_label": "description de la date ex: printemps 2055",
  "evenement_cle": "phrase courte 4-11 mots avec annee finale 2055",
  "realisation": "comment l'événement se réalise (ou ne se réalise pas) dans ce monde — 3-5 lignes",
  "description_complete": "description journalistique de l'événement — 3-4 lignes vivantes",
  "consequences": "conséquences à long terme dans ce monde — 2-3 lignes",
  "acteurs": ["slug_instance_existante_ou_texte_libre"],
  "impact_sur_variables": [
    {{"variable": "slug_variable", "delta_level": 15, "duree": 20, "polarite": -1}}
  ],
  "propagation_via_matrice": true,
  "impossible_dans_scenario": false,
  "note_coherence": "pourquoi c'est cohérent avec ce monde — 1 ligne"
}}
"""
    return call_claude_json(client, "Tu es un assistant de world-building.", user_content, max_tokens=2500)


# ---------------------------------------------------------------------------
# Validation mécanique
# ---------------------------------------------------------------------------

def validate_instance(instance_data, variables, scenario, registre_text, available_actors):
    issues = []

    required = ["nom", "date", "evenement_cle", "realisation",
                "description_complete", "consequences"]
    for field in required:
        if not instance_data.get(field):
            issues.append(f"Champ requis manquant ou vide : '{field}'")

    evenement_cle = str(instance_data.get("evenement_cle", ""))
    wc = len(evenement_cle.split())
    if evenement_cle and (wc < 4 or wc > 11):
        issues.append(f"'evenement_cle' a {wc} mots (attendu 4-11) : {evenement_cle!r}")

    year_match = re.search(r"(\d{4})\s*$", evenement_cle)
    if evenement_cle and not year_match:
        issues.append(f"'evenement_cle' sans année finale : {evenement_cle!r}")

    all_events = get_all_evenements(registre_text)
    if evenement_cle.strip().lower() in all_events:
        issues.append(f"'evenement_cle' déjà présent dans le registre : {evenement_cle!r}")

    impacts = instance_data.get("impact_sur_variables") or []
    if not isinstance(impacts, list):
        issues.append("'impact_sur_variables' doit être une liste")
        impacts = []

    impacted_vars = set()
    for imp in impacts:
        if not isinstance(imp, dict):
            issues.append(f"Entrée impact_sur_variables invalide : {imp!r}")
            continue
        var = imp.get("variable", "")
        if var not in VALID_VARS:
            issues.append(f"Variable inconnue dans impact_sur_variables : {var!r}")
            continue
        impacted_vars.add(var)
        delta = imp.get("delta_level")
        if delta is None:
            delta = 0
        try:
            delta = float(delta)
        except (TypeError, ValueError):
            issues.append(f"[{var}] delta_level non numérique : {imp.get('delta_level')!r}")
            continue
        if abs(delta) > MAX_DELTA_LEVEL:
            issues.append(
                f"[{var}] delta_level={delta} hors plage raisonnable "
                f"(-{MAX_DELTA_LEVEL} à +{MAX_DELTA_LEVEL})"
            )

    missing_vars = set(variables) - impacted_vars
    if missing_vars and not instance_data.get("impossible_dans_scenario"):
        issues.append(
            f"Variables annoncées mais non impactées : {sorted(missing_vars)}"
        )

    valid_actor_slugs = {a["slug"] for a in available_actors}
    acteurs = instance_data.get("acteurs") or []
    for a in acteurs:
        if a not in valid_actor_slugs:
            # Pas bloquant : texte libre accepté, mais signalé pour info
            # si ça ressemble à un slug (snake_case) sans correspondre à
            # une instance réelle -> probable wikilink cassé.
            if re.fullmatch(r"[a-z0-9_]+", a) and a not in valid_actor_slugs:
                issues.append(
                    f"Acteur '{a}' ressemble à un slug d'instance mais ne "
                    f"correspond à aucune instance existante pour {scenario} "
                    f"— utiliser un slug de la liste fournie ou un texte libre"
                )

    return issues


# ---------------------------------------------------------------------------
# Injection — écriture des fichiers
# ---------------------------------------------------------------------------

def yaml_scalar(value):
    """Sérialise une valeur scalaire YAML en s'assurant que les valeurs
    contenant ':' ou d'autres caractères spéciaux sont correctement quotées."""
    dumped = yaml.dump(value, allow_unicode=True, default_flow_style=True).strip()
    # yaml.dump ajoute \n à la fin et des quotes si nécessaire
    if dumped.endswith("\n..."):
        dumped = dumped[:-3].strip()
    return dumped


def write_archetype_file(event_slug, idea, type_evenement, variables, scenarios, display_name=None):
    EVENEMENTS_DIR.mkdir(parents=True, exist_ok=True)

    vars_yaml = "\n".join(f"  - {v}" for v in variables)
    scenarios_yaml = "\n".join(f"  - {s}" for s in scenarios)

    instance_rows = ""
    for sc in SCENARIOS:
        if sc in scenarios:
            instance_rows += f"| [[{sc}]] | [[{event_slug}_{sc}]] | | |\n"
        else:
            instance_rows += f"| [[{sc}]] | — | — | — |\n"

    name = display_name or event_slug.replace("_", " ").capitalize()

    content = f"""---
name: {name}
type: event_archetype
slug: {event_slug}
type_evenement: {type_evenement}
portee: {idea['portee']}
date_approximative: {idea['date_approximative']}
intensite: {idea['intensite']}
description: >
  {idea['description'].strip()}
variables_hint:
{vars_yaml}
scenarios_instances:
{scenarios_yaml}
date_creation: {datetime.now().strftime("%Y-%m-%d")}
custom_source: {idea.get('source', 'actualite')}
---

# {name}

## Description archétypale
{idea['description'].strip()}

## Instances par scénario
| Scénario | Instance | Réalisation | Impact |
|---|---|---|---|
{instance_rows}
"""
    path = EVENEMENTS_DIR / f"{event_slug}.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_instance_file(event_slug, type_evenement, idea, scenario, instance_data):
    EVENT_INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
    slug_instance = f"{event_slug}_{scenario}"

    def yaml_list(lst, n=2):
        if not lst:
            return ""
        pad = "  " * n
        return "\n" + "\n".join(f"{pad}- {i}" for i in lst)

    impacts_yaml = ""
    for imp in (instance_data.get("impact_sur_variables") or []):
        if not isinstance(imp, dict):
            continue
        var = imp.get("variable", "")
        if var not in VALID_VARS:
            continue
        impacts_yaml += "\n  - variable: {}\n    delta_level: {}\n    duree: {}\n    polarite: {}".format(
            var, imp.get("delta_level") or 0, imp.get("duree") or 20, imp.get("polarite") or 1,
        )

    acteurs_yaml = yaml_list(instance_data.get("acteurs", []))
    impossible = instance_data.get("impossible_dans_scenario", False)

    vars_md = "\n".join(
        "- **{}** : delta {:+} sur {} ans".format(
            imp.get("variable", "?"),
            (imp.get("delta_level") or 0) * (imp.get("polarite") or 1),
            imp.get("duree") or 20,
        )
        for imp in (instance_data.get("impact_sur_variables") or [])
        if isinstance(imp, dict) and imp.get("variable") in VALID_VARS
    ) or "_aucun_"

    acteurs_md = "\n".join(
        f"- [[{a}]]" for a in (instance_data.get("acteurs") or [])
    ) or "_aucun_"

    content = """---
name: {nom}
type: event_instance
slug: {slug_instance}""".format(
        nom=yaml_scalar(instance_data.get("nom", event_slug)),
        slug_instance=slug_instance,
    ) + """
archetype: {event_slug}
scenario: {scenario}
type_evenement: {type_evenement}
portee: {portee}
date: {date}
date_label: {date_label}
impossible: {impossible}
custom: true
description: >
  {desc}
consequences: >
  {consequences}
realisation: >
  {realisation}
impact_sur_variables:{impacts_yaml}
propagation:
  via_matrice: {via_matrice}
acteurs_impliques:{acteurs_yaml}
note_coherence: {note}
custom_source: {source}
date_creation: {date_creation}
---

# {nom_md}

## Réalisation dans [[{scenario}]]
{realisation}

## Description journalistique
{desc}

## Conséquences
{consequences}

## Impact sur les variables
{vars_md}

## Acteurs impliqués
{acteurs_md}

## Note de cohérence
{note}
""".format(
        event_slug=event_slug,
        scenario=scenario,
        type_evenement=type_evenement,
        portee=idea["portee"],
        date=instance_data.get("date", idea["date_approximative"]),
        date_label=instance_data.get("date_label", str(idea["date_approximative"])),
        impossible=str(impossible).lower(),
        desc=instance_data.get("description_complete", "").replace("\n", " "),
        consequences=instance_data.get("consequences", "").replace("\n", " "),
        realisation=instance_data.get("realisation", "").replace("\n", " "),
        impacts_yaml=impacts_yaml,
        via_matrice=str(instance_data.get("propagation_via_matrice", True)).lower(),
        acteurs_yaml=acteurs_yaml,
        note=yaml_scalar(instance_data.get("note_coherence") or ""),
        source=idea.get("source", "actualite"),
        date_creation=datetime.now().strftime("%Y-%m-%d"),
        vars_md=vars_md,
        acteurs_md=acteurs_md,
        nom_md=instance_data.get("nom", event_slug),
    )

    path = EVENT_INSTANCES_DIR / f"{slug_instance}.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Gestion de la queue
# ---------------------------------------------------------------------------

def load_yaml_list(path, key="queue"):
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get(key, []) or []


def save_yaml_list(path, items, key="queue"):
    EVENEMENTS_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump({key: items}, allow_unicode=True, sort_keys=False),
                     encoding="utf-8")


def append_yaml_list(path, item, key="processed"):
    items = load_yaml_list(path, key=key)
    items.append(item)
    save_yaml_list(path, items, key=key)


QUEUE_TEMPLATE = """\
# evenements_custom/queue.yaml
#
# Ajoute ici tes idées d'événements custom (observations de l'actualité,
# idées narratives...). Lance ensuite :
#
#   python3 generator/inject_custom_events.py            ← injection réelle
#   python3 generator/inject_custom_events.py --dry-run  ← test sans écriture
#
# CHAMPS :
#   id                    : identifiant court lisible (lettres, chiffres, underscores)
#   description           : l'idée en langage naturel, quelques phrases suffisent
#   portee                : locale | regionale | continentale | globale
#   date_approximative     : année 2025-2097 (peut varier de +/-10 ans par scénario)
#   intensite              : faible | modérée | forte | majeure
#   scenarios              : liste de scénarios à couvrir, ou null pour les 6 par défaut
#                            (valeurs : breakdown, fortress_world, new_sustainability,
#                            eco_communalism, policy_reform, reference)
#   variables_hint         : optionnel. null si tu ne sais pas — Claude choisit
#                            automatiquement. Sinon une variable (chaîne) ou
#                            plusieurs (liste) que tu IMPOSES comme impactées.
#                            Variables disponibles :
#                              systeme_economique_redistribution | gouvernance_institutions
#                              geopolitique_conflits | valeurs_culture_tempo_sociale
#                              organisation_territoires | sante_biotechnologies
#                              frontieres_du_systeme | technologie_information
#                              climat_environnement_global | energie_ressources_critiques
#                              demographie_mobilite_humaine | systemes_productifs_travail
#   variables_hint_count   : optionnel, entier 1-4. Plafond du nombre total de
#                            variables (hint(s) inclus). Défaut : 2.
#   acteurs_hint           : optionnel. null si tu ne sais pas — Claude choisit
#                            parmi les instances d'entités existantes pour
#                            chaque scénario. Sinon un slug d'instance (chaîne)
#                            ou plusieurs (liste) que tu IMPOSES.
#   acteurs_hint_count     : optionnel, entier 1-4. Plafond du nombre total
#                            d'acteurs (hint(s) inclus). Défaut : 2.
#   source                 : libre — date, lien d'article...
#
# EXEMPLE :
#   - id: guerre_israelo_iranienne
#     description: >
#       Conflit armé direct entre Israël et l'Iran, frappes sur les
#       infrastructures nucléaires et pétrolières, risque d'escalade
#       régionale impliquant les puissances du Golfe.
#     portee: globale
#     date_approximative: 2026
#     intensite: majeure
#     scenarios: null
#     variables_hint: [geopolitique_conflits, energie_ressources_critiques]
#     variables_hint_count: null
#     acteurs_hint: null
#     acteurs_hint_count: null
#     source: actualite_2026-06
#
# Les idées traitées sont déplacées vers processed.yaml (succès) ou
# needs_review.yaml (échec après corrections automatiques).
# ──────────────────────────────────────────────────────────────────────────────

queue:
"""


def save_queue_with_template(remaining):
    EVENEMENTS_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    if remaining:
        items_yaml = yaml.dump(remaining, allow_unicode=True,
                               sort_keys=False, default_flow_style=False)
        indented = "\n".join("  " + line for line in items_yaml.splitlines())
        content = QUEUE_TEMPLATE + indented + "\n"
    else:
        content = QUEUE_TEMPLATE + "  [] # ← remplace [] par tes idées\n"
    QUEUE_PATH.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

def process_idea(client, idea, dry_run=False):
    idea_id = idea.get("id", "sans_id")
    variables_hint = idea.get("variables_hint")
    if isinstance(variables_hint, str):
        variables_hint = [variables_hint]
    variables_hint_count = idea.get("variables_hint_count")

    actors_hint = idea.get("acteurs_hint")
    if isinstance(actors_hint, str):
        actors_hint = [actors_hint]
    actors_hint_count = idea.get("acteurs_hint_count") or 2
    actors_hint_count = max(1, min(4, actors_hint_count))

    scenarios = idea.get("scenarios") or list(SCENARIOS)
    scenarios = [s for s in scenarios if s in SCENARIOS]

    print(f"\n=== {idea_id} ===")
    print("[1/4] Sélection de variables + type...")
    selection = step1_select_variables_and_type(
        client, idea, variables_hint, variables_hint_count
    )
    variables = [v for v in selection["variables"] if v in VALID_VARS]
    type_evenement = selection.get("type_evenement", "systemic")
    # Slug imposé depuis l'id de la queue — Claude ne l'invente plus
    event_slug = re.sub(r"[^a-z0-9_]", "_", idea_id.lower().strip())
    print(f"  -> variables={variables} type={type_evenement} slug={event_slug}")

    if not variables:
        return {"status": "needs_review", "reason": "aucune variable valide proposée",
                "idea": idea, "selection": selection}

    registre_text = read_registre_text()
    results = []
    archetype_written = False

    for scenario in scenarios:
        try:
            print(f"[2/4] Développement pour {scenario}...")
            available_actors = load_available_actors(scenario)
            registre_excerpt = get_registre_excerpt_for_variables(
                registre_text, variables, scenario
            )

            previous, issues = None, None
            instance_data = step2_develop_instance(
                client, idea, event_slug, type_evenement, variables, scenario,
                registre_excerpt, available_actors, actors_hint,
            )

            for attempt in range(MAX_FIX_ATTEMPTS + 1):
                print(f"[3/4] Validation (essai {attempt + 1})...")
                issues = validate_instance(
                    instance_data, variables, scenario, registre_text, available_actors
                )
                if not issues:
                    break
                print("  -> problèmes :")
                for i in issues:
                    print(f"     - {i}")
                if attempt < MAX_FIX_ATTEMPTS:
                    instance_data = step2_develop_instance(
                        client, idea, event_slug, type_evenement, variables, scenario,
                        registre_excerpt, available_actors, actors_hint,
                        previous=instance_data, issues=issues,
                    )

            if issues:
                results.append({
                    "scenario": scenario, "status": "needs_review",
                    "issues": issues, "instance_data": instance_data,
                })
                continue

            print("[4/4] Injection...")
            if not dry_run:
                if not archetype_written:
                    write_archetype_file(event_slug, idea, type_evenement, variables,
                                          scenarios, display_name=instance_data.get("nom"))
                    archetype_written = True
                write_instance_file(event_slug, type_evenement, idea, scenario, instance_data)
                regenerate_registre_with_event(
                    scenario, event_slug, variables,
                    instance_data.get("date", idea["date_approximative"]),
                    instance_data["evenement_cle"],
                )
                registre_text = read_registre_text()
            else:
                print(json.dumps(instance_data, ensure_ascii=False, indent=2))

            results.append({"scenario": scenario, "status": "injected",
                             "instance_data": instance_data})

        except Exception as e:
            print(f"  [ERREUR scénario {scenario}] {e}")
            results.append({
                "scenario": scenario, "status": "needs_review",
                "issues": [str(e)], "instance_data": {},
            })

    injected = [r for r in results if r["status"] == "injected"]
    failed   = [r for r in results if r["status"] != "injected"]
    overall  = "needs_review" if failed else "injected"
    return {
        "status": overall,
        "idea": idea,
        "selection": selection,
        "results": results,
        "injected_scenarios": [r["scenario"] for r in injected],
        "failed_scenarios":   [r["scenario"] for r in failed],
    }



# =============================================================================
# MODE AUTO — analyse du vault + génération d'idées d'événements
# =============================================================================

def load_all_zones_event(scenario):
    """Charge toutes les zones d'un scénario depuis geographie/{scenario}.md."""
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    if not path.exists():
        return {}
    fm, _ = parse_md(path)
    zones_list = fm.get("zones", []) or []
    return {z["slug"]: z for z in zones_list if isinstance(z, dict) and "slug" in z}


def analyze_vault_coverage():
    """
    Analyse la couverture actuelle du vault :
    - Distribution géographique des event_instances (zone → count par scénario)
    - Zones absentes (0 event_instance) par scénario
    - Distribution par type d'événement par scénario
    - Variables les moins couvertes par scénario
    - Liste des evenement_cle existants (anti-doublon)
    """
    geo_coverage  = {}
    geo_absent    = {}
    type_coverage = {}
    var_coverage  = {}
    existing_cles = []

    for sc in SCENARIOS:
        geo_coverage[sc] = {}
        type_coverage[sc] = {}
        var_coverage[sc] = {v: 0 for v in VALID_VARS}

    if EVENT_INSTANCES_DIR.exists():
        for path in sorted(EVENT_INSTANCES_DIR.glob("*.md")):
            fm, _ = parse_md(path)
            sc = fm.get("scenario", "")
            if sc not in SCENARIOS:
                continue
            loc = fm.get("localisation") or {}
            if isinstance(loc, dict):
                zone = loc.get("zone") or "inconnue"
                geo_coverage[sc][zone] = geo_coverage[sc].get(zone, 0) + 1
            t = fm.get("type_evenement", "inconnu")
            type_coverage[sc][t] = type_coverage[sc].get(t, 0) + 1
            impacts = fm.get("impact_sur_variables", []) or []
            for imp in impacts:
                if isinstance(imp, dict):
                    var = imp.get("variable", "")
                    if var in var_coverage[sc]:
                        var_coverage[sc][var] += 1
            cle = fm.get("evenement_cle", "")
            if cle:
                existing_cles.append(cle)

    # Zones absentes
    for sc in SCENARIOS:
        all_zones = load_all_zones_event(sc)
        covered = set(geo_coverage[sc].keys())
        geo_absent[sc] = [slug for slug in all_zones if slug not in covered]

    return {
        "geo_coverage":  geo_coverage,
        "geo_absent":    geo_absent,
        "type_coverage": type_coverage,
        "var_coverage":  var_coverage,
        "existing_cles": existing_cles,
    }


def build_auto_analysis_summary(coverage, scenario_filter=None):
    """Construit le résumé textuel de l'analyse pour le prompt Claude."""
    lines = []

    scenarios = [scenario_filter] if scenario_filter else SCENARIOS

    lines.append("## Couverture géographique actuelle (event_instances)")
    for sc in scenarios:
        geo = coverage["geo_coverage"].get(sc, {})
        if geo:
            top = sorted(geo.items(), key=lambda x: -x[1])[:5]
            lines.append(f"  {sc}: " + ", ".join(f"{z}({n})" for z, n in top))
        else:
            lines.append(f"  {sc}: (aucune)")

    lines.append("")
    lines.append("## Zones sans aucun événement (à couvrir en priorité)")
    for sc in scenarios:
        absent = coverage["geo_absent"].get(sc, [])
        if absent:
            lines.append(f"  {sc}: " + ", ".join(absent[:20]))
            if len(absent) > 20:
                lines.append(f"    ... et {len(absent) - 20} autres")
        else:
            lines.append(f"  {sc}: (toutes les zones ont au moins un événement)")

    lines.append("")
    lines.append("## Couverture par type d'événement")
    for sc in scenarios:
        tc = coverage["type_coverage"].get(sc, {})
        if tc:
            lines.append(f"  {sc}: " + ", ".join(f"{t}({n})" for t, n in sorted(tc.items())))
        else:
            lines.append(f"  {sc}: (aucun)")

    lines.append("")
    lines.append("## Variables les moins couvertes (top 4 par scénario)")
    for sc in scenarios:
        vc = coverage["var_coverage"].get(sc, {})
        least = sorted(vc.items(), key=lambda x: x[1])[:4]
        lines.append(f"  {sc}: " + ", ".join(f"{v}({n})" for v, n in least))

    return "\n".join(lines)


def build_scenarios_summary_for_auto(scenario_filter=None):
    """Résumé des scénarios pour le prompt auto."""
    scenarios = [scenario_filter] if scenario_filter else SCENARIOS
    lines = []
    for sc in scenarios:
        ctx = load_scenario_context(sc)
        lines.append(
            f"- {sc}: {ctx['state_of_system']} | tension {ctx['tension_level']}/5 | "
            f"trajectoire {ctx['trajectory']} | {ctx['summary'][:150]}"
        )
    return "\n".join(lines)


def step_auto_generate_ideas(client, n, coverage, scenario_filter=None):
    """
    Appelle Claude pour générer N idées d'événements contextualisées
    en fonction des déséquilibres détectés dans le vault.
    Retourne une liste d'idées au format queue.yaml.
    """
    analysis = build_auto_analysis_summary(coverage, scenario_filter)
    scenarios_summary = build_scenarios_summary_for_auto(scenario_filter)
    var_summary = build_variables_summary()

    scenario_instruction = ""
    if scenario_filter:
        scenario_instruction = f"\nContrainte : les événements doivent impacter le scénario '{scenario_filter}' (ils peuvent aussi impacter d'autres scénarios si cohérent)."

    existing_cles_txt = "\n".join(f"- {c}" for c in coverage["existing_cles"][:50])
    if not existing_cles_txt:
        existing_cles_txt = "(aucun événement existant)"

    user_content = f"""Tu dois proposer {n} idée(s) d'événements custom pour le projet Ourrassol 2098.
Ces idées seront écrites dans queue.yaml pour être inspectées et injectées en mode custom.

## ANALYSE DES DÉSÉQUILIBRES DU VAULT
{analysis}

## SCÉNARIOS DU MONDE
{scenarios_summary}

## VARIABLES DISPONIBLES
{var_summary}

## ÉVÉNEMENTS DÉJÀ EXISTANTS (anti-doublon — ne pas recréer)
{existing_cles_txt}
{scenario_instruction}

## CONSIGNE
- Compense les déséquilibres détectés : couvre les zones géographiques sous-représentées,
  les types d'événements peu présents, les variables peu couvertes.
- Chaque événement doit être cohérent avec les scénarios qu'il impacte.
- Propose des scénarios pertinents pour chaque événement (pas forcément les 6 — seulement
  ceux où l'événement a du sens narrativement).
- Diversifie les types, zones et variables entre les idées proposées.
- Ne recrée pas un événement déjà existant (même thème, même lieu, même période).

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact :
{{
  "idees": [
    {{
      "id": "slug_court_sans_espaces",
      "description": "Description détaillée, 2-4 lignes, avec lieu précis et acteurs potentiels.",
      "portee": "locale|regionale|continentale|globale",
      "date_approximative": "AAAA",
      "intensite": "faible|modérée|forte|majeure",
      "scenarios": ["scenario1", "scenario2"],
      "variables_hint": ["var1", "var2"],
      "variables_hint_count": 3,
      "acteurs_hint": null,
      "acteurs_hint_count": 2,
      "source": "auto_generated_{datetime.now().strftime('%Y-%m')}",
      "rationale": "Pourquoi cet événement comble un déséquilibre du vault (1 ligne)."
    }}
  ]
}}
"""

    result = call_claude_json(client, "Tu es un assistant de world-building pour Ourrassol 2098.", user_content)
    return result.get("idees", [])


def run_auto_mode(client, dry_run):
    """Mode auto : analyse le vault, génère des idées, les ajoute à queue.yaml."""
    raw_n = input("Nombre d'idées à générer ? [défaut: 3] : ").strip()
    try:
        n = int(raw_n) if raw_n else 3
        if n < 1:
            n = 3
    except ValueError:
        n = 3

    scenario_raw = input(
        "Scénario ciblé ? (Entrée pour laisser Claude choisir) [{}] : ".format(
            "|".join(SCENARIOS)
        )
    ).strip()
    scenario_filter = scenario_raw if scenario_raw in SCENARIOS else None

    print("\n[1/2] Analyse de la couverture du vault...")
    coverage = analyze_vault_coverage()

    n_evt = sum(len(v) for v in coverage["type_coverage"].values())
    print(f"  {n_evt} event_instance(s) analysée(s)")
    if scenario_filter:
        print(f"  Filtre scénario : {scenario_filter}")

    print(f"[2/2] Génération de {n} idée(s) d'événements...")
    ideas = step_auto_generate_ideas(client, n, coverage, scenario_filter)

    if not ideas:
        print("Aucune idée générée — vérifier la réponse Claude.")
        return

    # Nettoyer le champ rationale (informatif uniquement, pas dans la queue)
    queue_ideas = []
    for idea in ideas:
        rationale = idea.pop("rationale", "")
        queue_ideas.append(idea)
        print(f"  ✓ {idea.get('id')} — {idea.get('portee')} | {idea.get('date_approximative')} | scénarios: {idea.get('scenarios')}")
        if rationale:
            print(f"    → {rationale}")

    if dry_run:
        print("\n[DRY-RUN] Idées générées (non écrites dans queue.yaml) :")
        print(yaml.dump({"queue": queue_ideas}, allow_unicode=True, default_flow_style=False))
        return

    # Ajouter à la suite de queue.yaml (pas d'écrasement)
    existing = load_yaml_list(QUEUE_PATH, key="queue")
    merged = existing + queue_ideas
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(
        yaml.dump({"queue": merged}, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8"
    )

    print(f"\n{len(queue_ideas)} idée(s) ajoutée(s) à {QUEUE_PATH}")
    print("→ Inspectez queue.yaml, puis relancez en mode custom pour injecter.")


def run_custom_mode(client, dry_run):
    """Mode custom : traite la queue.yaml existante."""
    queue = load_yaml_list(QUEUE_PATH, key="queue")
    if not queue:
        print(f"Queue vide ({QUEUE_PATH}). Rien à faire.")
        print("→ Utilisez le mode auto pour générer des idées, ou remplissez queue.yaml manuellement.")
        return

    remaining = []
    total_injected = 0

    for idea in queue:
        try:
            outcome = process_idea(client, idea, dry_run=dry_run)
        except Exception as e:
            outcome = {"status": "needs_review", "idea": idea, "error": str(e)}

        if dry_run:
            print(json.dumps(outcome, ensure_ascii=False, indent=2, default=str))
            remaining.append(idea)
            continue

        injected_scenarios = outcome.get("injected_scenarios", [])
        failed_scenarios   = outcome.get("failed_scenarios", [])

        if injected_scenarios:
            total_injected += len(injected_scenarios)
            append_yaml_list(PROCESSED_PATH, {
                "idea": outcome["idea"],
                "selection": outcome.get("selection"),
                "injected_scenarios": injected_scenarios,
                "status": "injected" if not failed_scenarios else "partial",
            }, key="processed")

        if failed_scenarios:
            append_yaml_list(NEEDS_REVIEW_PATH, {
                "idea": outcome["idea"],
                "selection": outcome.get("selection"),
                "failed_scenarios": failed_scenarios,
                "results": [r for r in outcome.get("results", [])
                            if r["scenario"] in failed_scenarios],
                "status": "needs_review",
            }, key="needs_review")

        # Cas extrême : 0 résultats (erreur avant la boucle scénarios)
        if not injected_scenarios and not failed_scenarios:
            append_yaml_list(NEEDS_REVIEW_PATH, outcome, key="needs_review")

    if not dry_run:
        save_queue_with_template(remaining)
        print(f"\nTerminé. Voir {PROCESSED_PATH} et {NEEDS_REVIEW_PATH}.")
        if total_injected > 0:
            run_post_injection_cycle()



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
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Appelle Claude et valide, mais n'écrit rien sur disque.")
    args = parser.parse_args()

    print("=" * 60)
    print("OURRASSOL 2098 — Injection événements custom")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)")

    client = get_client()

    mode = input("\nMode : custom ou auto ? [custom/auto] : ").strip().lower()
    while mode not in ("custom", "auto"):
        mode = input("Réponds 'custom' ou 'auto' : ").strip().lower()

    if mode == "custom":
        run_custom_mode(client, dry_run=args.dry_run)
    else:
        run_auto_mode(client, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
