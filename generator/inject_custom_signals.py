#!/usr/bin/env python3
"""
inject_custom_signals.py — Ourrassol 2098
==========================================

Injecte des "signaux faibles custom" (idées fournies par l'utilisateur,
souvent inspirées de l'actualité) dans les fiches variables du vault,
en suivant le même format que les signaux développés lors du chantier
"section 7 -> section 12" (voir brief_section7_vers_12.md).

PRINCIPE
--------
1. Tu remplis `signaux_custom/queue.yaml` avec une liste d'idées en
   langage naturel (voir exemple plus bas / README).
2. Tu lances :  python3 inject_custom_signals.py
3. Pour chaque idée, le script :
     - appelle le LLM (étape 1) pour choisir la/les variable(s) cible(s),
       la catégorie, et un slug snake_case pour le signal
     - appelle le LLM (étape 2) pour rédiger le bloc YAML signal_to_state
       (6 scénarios) + l'annotation section 7, en s'appuyant sur le
       state_logic de la fiche variable et le registre des événements
     - valide mécaniquement le résultat (comptage de mots, fenêtres de
       dates, collisions) — purement Python, aucun appel API
     - si la validation échoue, rappelle le LLM (étape 3, correction
       ciblée) jusqu'à 2 fois
     - injecte le bloc validé dans variables/{slug}.md (sections 7 et 12)
     - régénère registre_evenements.md
     - écrit une fiche d'audit dans signaux_custom/{signal_slug}.md
     - déplace l'idée de queue.yaml vers processed.yaml
       (ou needs_review.yaml si la validation échoue malgré les retries)

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...

USAGE
-----
    python3 inject_custom_signals.py            # traite toute la queue
    python3 inject_custom_signals.py --dry-run  # appelle le LLM, valide,
                                                  # affiche le résultat,
                                                  # mais n'écrit rien sur disque
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from llm_client import call_llm  # tier structured_strict — canonique/référencé


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
VARIABLES_DIR = VAULT_ROOT / "variables"
REGISTRE_PATH = Path(__file__).resolve().parent / "registre_evenements.md"
SIGNAUX_CUSTOM_DIR = VAULT_ROOT / "signaux_custom"
QUEUE_PATH = SIGNAUX_CUSTOM_DIR / "queue.yaml"
PROCESSED_PATH = SIGNAUX_CUSTOM_DIR / "processed.yaml"
NEEDS_REVIEW_PATH = SIGNAUX_CUSTOM_DIR / "needs_review.yaml"


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

PILOTS = [
    "geopolitique_conflits",
    "energie_ressources_critiques",
    "organisation_territoires",
    "climat_environnement_global",
    "systemes_productifs_travail",
]


# ---------------------------------------------------------------------------
# Lecture des fiches variables
# ---------------------------------------------------------------------------

def read_variable_file(slug):
    path = VARIABLES_DIR / f"{slug}.md"
    return path.read_text(encoding="utf-8")


def split_frontmatter(content):
    """Retourne (frontmatter_dict, body_str).

    Les fiches utilisent la syntaxe Obsidian [[lien]] dans le frontmatter
    (ex: coupling_intensity: { [[geopolitique_conflits]]: 90 }), ce qui
    n'est pas du YAML valide tel quel -> on retire les doubles crochets
    avant le parsing.
    """
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    raw_fm = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    fm = yaml.safe_load(raw_fm) or {}
    return fm, m.group(2)


def extract_section(content, number, next_number=None):
    """Extrait le texte de la section '## {number}. ...' jusqu'à la
    section suivante ('## {next_number}.' ou EOF si non fourni)."""
    start_pat = re.compile(rf"^##\s*{number}\.\s.*$", re.MULTILINE)
    m_start = start_pat.search(content)
    if not m_start:
        return ""
    start = m_start.end()
    if next_number is not None:
        end_pat = re.compile(rf"^##\s*{next_number}\.\s", re.MULTILINE)
        m_end = end_pat.search(content, start)
        end = m_end.start() if m_end else len(content)
    else:
        end = len(content)
    return content[start:end].strip()


def build_variables_summary():
    """Construit un résumé condensé des 12 variables (pour l'étape 1) :
    name, variable_type, domain, sub_variables, state_logic par scénario."""
    chunks = []
    for slug in VALID_VARS:
        content = read_variable_file(slug)
        fm, _ = split_frontmatter(content)
        domain = ", ".join(fm.get("domain", []))
        sub_vars = fm.get("sub_variables", []) or []
        sub_vars_str = "; ".join(
            f"{sv.get('name')} ({sv.get('role', '')})" for sv in sub_vars
        )
        states = fm.get("states", {}) or {}
        state_logics = []
        for scen in SCENARIOS:
            sl = (states.get(scen, {}) or {}).get("state_logic", "").strip()
            sl = re.sub(r"\s+", " ", sl)
            if sl:
                state_logics.append(f"    - {scen}: {sl}")
        chunk = (
            f"### {slug}\n"
            f"  type: {fm.get('variable_type', '')}\n"
            f"  domain: {domain}\n"
            f"  sub_variables: {sub_vars_str}\n"
            f"  state_logic:\n" + "\n".join(state_logics)
        )
        chunks.append(chunk)
    return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Registre des événements
# ---------------------------------------------------------------------------

def read_registre_text():
    if not REGISTRE_PATH.exists():
        return ""
    return REGISTRE_PATH.read_text(encoding="utf-8")


def parse_registre_table(scen_body):
    """Parse les lignes '| type | date | source | variable(s) | pilote | evenement_cle |'
    (nouveau format 6 colonnes) d'une section de scénario, retourne une
    liste de listes de colonnes."""
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


def get_existing_windows_for_variable(registre_text, variable_slug):
    """Retourne {scenario: set(date)} pour les signaux/événements déjà
    présents pour cette variable dans le registre.

    Pour les événements (type=evenement), "variable(s)" peut contenir
    plusieurs slugs séparés par ", " — on matche si variable_slug en
    fait partie.
    """
    result = {scen: set() for scen in SCENARIOS}
    parts = re.split(
        r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text
    )
    for i in range(1, len(parts), 2):
        scen = parts[i]
        body = parts[i + 1]
        for cols in parse_registre_table(body):
            if len(cols) < 6:
                continue
            row_vars = [v.strip() for v in cols[3].split(",")]
            if variable_slug in row_vars:
                result[scen].add(cols[1])
    return result


def get_all_evenements(registre_text):
    """Retourne l'ensemble (lowercase) de tous les evenement_cle du
    registre (signaux ET événements custom confondus)."""
    events = set()
    parts = re.split(
        r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text
    )
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        for cols in parse_registre_table(body):
            if len(cols) >= 6:
                events.add(cols[5].strip().lower())
    return events


# ---------------------------------------------------------------------------
# Appels LLM
# ---------------------------------------------------------------------------

def get_client():
    """Conservé pour compatibilité — retourne None, call_claude_json n'en a plus besoin."""
    return None


def call_claude_json(client, system, user_content, max_tokens=3000):
    """Appelle le LLM, exige une réponse JSON pure, la parse et la retourne."""
    text = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
        task_tier="structured_strict",
    ).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


FORMAT_RULES = """\
RÈGLES DE FORMAT (calibrées sur le chantier section 7 -> section 12) :
- `evolution` et `evenement_cle` : ~7 mots en moyenne, MINIMUM 4 mots,
  MAXIMUM 11 mots. Phrases courtes et percutantes, pas de longues
  descriptions.
- `evenement_cle` : inclut une année précise à la fin (ex: "... 2051"),
  SAUF pour les scénarios eco_communalism où l'absence d'année est
  acceptée (mouvements/chartes/réseaux sans date précise), en cohérence
  avec le style déjà présent dans la fiche.
- `date_bascule` : fenêtre temporelle "AAAA-AAAA", l'année de
  `evenement_cle` doit être DANS cette fenêtre.
- Les `evolution` doivent être cohérentes avec le `state_logic` de la
  section 8 du scénario correspondant (ex: si breakdown dit
  "effondrement des systèmes de santé", l'évolution d'un nouveau signal
  santé doit aller dans ce sens).
- Réutiliser intelligemment la géographie/factions déjà établies dans le
  registre (Detroit-Sud, Lagos-Est, Lagos-Mumbai-Jakarta, Carthage-Nord,
  Bloc Atlantique, Bloc Sibérien, Bloc Eurasiatique, Alliance Pacifique,
  Réseau des Assemblées Bioterritoriales...) quand c'est pertinent, sans
  forcer.
- Pas de nom d'`evenement_cle` identique ou quasi-identique à un
  événement déjà présent dans le registre fourni.
- Pas de fenêtre `date_bascule` strictement identique, pour le même
  scénario, à une fenêtre déjà utilisée par une AUTRE variable/signal —
  privilégier une fenêtre voisine mais distincte.
"""


def step1_select_variable(client, idea_text, variable_hint=None, variable_hint_count=None):
    summary = build_variables_summary()

    # variable_hint accepte : None, une chaîne unique, ou une liste de slugs.
    if variable_hint is None:
        hints = []
    elif isinstance(variable_hint, str):
        hints = [variable_hint]
    else:
        hints = list(variable_hint)
    hints = [h for h in hints if h in VALID_VARS]

    max_vars = variable_hint_count if variable_hint_count else 2
    max_vars = max(1, min(4, max_vars))

    if hints:
        hint_txt = (
            f"\nL'utilisateur impose déjà {'la variable' if len(hints) == 1 else 'les variables'} "
            f"suivante{'s' if len(hints) > 1 else ''} comme cible{'s' if len(hints) > 1 else ''} : "
            f"{', '.join(hints)}.\n"
            f"Tu DOIS les inclure dans ta réponse. Tu peux en ajouter d'autres si "
            f"pertinent, dans la limite du plafond ci-dessous.\n"
        )
    else:
        hint_txt = ""

    user_content = f"""Voici une idée de "signal faible" (observation de l'actualité
réelle) à intégrer dans le simulateur de presse fictive Ourrassol 2098 :

IDÉE :
{idea_text}
{hint_txt}
Voici un résumé condensé des 12 variables systémiques du système
(domain, sous-variables, state_logic par scénario) :

{summary}

TÂCHE :
1. Choisis entre 1 et {max_vars} variable{'s' if max_vars > 1 else ''} cible{'s' if max_vars > 1 else ''}
   parmi les 12 — privilégie 2 par défaut (un signal touche presque toujours
   plusieurs systèmes), monte au-delà de 2 (jusqu'à {max_vars}) seulement si
   l'idée est clairement structurante (ex: une crise qui percute climat +
   énergie + géopolitique simultanément), et descends à 1 seulement si
   l'idée est vraiment locale à un seul domaine.
   {"Les variables imposées listées ci-dessus comptent dans ce plafond." if hints else ""}
2. Détermine la catégorie : technological | geopolitical | social |
   environmental | cognitive_cultural.
3. Propose un identifiant `signal_slug` en snake_case, sans accents,
   court (3-5 mots), qui décrit le signal (ex: chatbots_therapeutes_remboursement).

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact :
{{"variables": ["slug1"], "categorie": "social", "signal_slug": "..."}}
"""
    return call_claude_json(client, "Tu es un assistant de world-building.", user_content)


def step2_develop(client, idea_text, source, variable_slug, signal_slug, categorie,
                   registre_text, previous=None, issues=None, sibling_events=None):
    content = read_variable_file(variable_slug)
    section7 = extract_section(content, 7, 8)
    section8 = extract_section(content, 8, 9)
    section12 = extract_section(content, 12, None)

    if previous is None:
        task = f"""TÂCHE : rédige le bloc YAML `signal_to_state` pour ce signal,
pour les 6 scénarios ({", ".join(SCENARIOS)}), au format calibré ci-dessous,
ainsi qu'une ligne d'annotation pour la section 7 (catégorie {categorie}).
"""
    else:
        issues_txt = "\n".join(f"- {i}" for i in issues)
        task = f"""Le bloc YAML précédent a échoué la validation mécanique :
{issues_txt}

Voici le bloc précédent :
{previous}

TÂCHE : corrige UNIQUEMENT les points listés ci-dessus, en gardant le
reste identique autant que possible. Si un point concerne un
`evenement_cle` "déjà présent dans le registre", n'essaie PAS de le
reformuler légèrement (changer un mot) : invente un événement RÉELLEMENT
différent (autre lieu, autre acteur, autre nature de fait) pour ce
scénario, tout en restant cohérent avec le `state_logic` de la section 8.
"""

    sibling_block = ""
    if sibling_events:
        sibling_lines = "\n".join(
            f"  - [{scen}] {ev}" for scen, ev in sibling_events.items()
        )
        sibling_block = f"""
--- ⚠️ ÉVÉNEMENTS DÉJÀ ÉCRITS POUR CE MÊME SIGNAL DANS UNE AUTRE VARIABLE ---
Ce signal ({signal_slug}) est aussi développé pour {("d'autres variables" if len(sibling_events) else "une autre variable")}
dans cette même session. Les `evenement_cle` suivants viennent d'être
injectés dans le registre — ils sont INTERDITS pour cette variable :
{sibling_lines}

Écris des `evenement_cle` DIFFÉRENTS pour chaque scénario concerné :
même thème de fond (c'est le même signal réel), mais un fait daté distinct
— un autre lieu, un autre acteur institutionnel, une autre conséquence
concrète — plutôt qu'une reformulation du même événement.
"""

    user_content = f"""Idée source (signal d'actualité, source : {source}) :
{idea_text}

Variable cible : {variable_slug}
Catégorie : {categorie}
Identifiant du signal : {signal_slug}

{FORMAT_RULES}

--- SECTION 7 actuelle (signaux faibles existants) ---
{section7}

--- SECTION 8 actuelle (state_logic par scénario) ---
{section8}

--- SECTION 12 actuelle (signal_to_state existants, pour le style) ---
{section12}

--- EXTRAIT DU REGISTRE DES ÉVÉNEMENTS (anti-collision) ---
{registre_text}
{sibling_block}
{task}

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact
(le champ "signal_to_state_yaml" doit être une chaîne YAML valide,
indentée comme les entrées existantes de la section 12, commençant par
"  - signal: {signal_slug}") :
{{
  "signal_to_state_yaml": "  - signal: {signal_slug}\\n    scenarios:\\n      breakdown:\\n        evolution: ...\\n        date_bascule: AAAA-AAAA\\n        evenement_cle: ... AAAA\\n      ...",
  "section7_annotation": "- description courte du signal (→ signal_custom: {signal_slug}, source: {source})"
}}
"""
    return call_claude_json(client, "Tu es un assistant de world-building.", user_content, max_tokens=4000)


# ---------------------------------------------------------------------------
# Validation mécanique
# ---------------------------------------------------------------------------

def validate_signal_block(yaml_text, signal_slug, variable_slug, registre_text):
    """Retourne une liste de problèmes (vide si tout est OK)."""
    issues = []

    try:
        parsed = yaml.safe_load("signal_to_state:\n" + yaml_text)
    except yaml.YAMLError as e:
        return [f"YAML invalide : {e}"]

    entries = (parsed or {}).get("signal_to_state") or []
    if not entries:
        return ["Bloc YAML vide ou mal formé (pas d'entrée 'signal_to_state')."]
    entry = entries[0]

    if entry.get("signal") != signal_slug:
        issues.append(
            f"Le champ 'signal' ({entry.get('signal')!r}) ne correspond pas "
            f"au signal_slug attendu ({signal_slug!r})."
        )

    scenarios = entry.get("scenarios") or {}
    missing = set(SCENARIOS) - set(scenarios.keys())
    if missing:
        issues.append(f"Scénarios manquants : {sorted(missing)}")

    existing_windows = get_existing_windows_for_variable(registre_text, variable_slug)
    all_events = get_all_evenements(registre_text)
    new_windows_by_scen = {}

    for scen, data in scenarios.items():
        if scen not in SCENARIOS:
            issues.append(f"Scénario inconnu : {scen}")
            continue

        evolution = (data or {}).get("evolution", "")
        evenement = (data or {}).get("evenement_cle", "")
        date_bascule = (data or {}).get("date_bascule", "")

        for field_name, value in (("evolution", evolution), ("evenement_cle", evenement)):
            wc = len(value.split())
            if wc < 4 or wc > 11:
                issues.append(
                    f"[{scen}] '{field_name}' a {wc} mots "
                    f"(attendu 4-11) : {value!r}"
                )

        m = re.match(r"^(\d{4})-(\d{4})$", date_bascule)
        if not m:
            issues.append(f"[{scen}] date_bascule invalide : {date_bascule!r}")
        else:
            start, end = int(m.group(1)), int(m.group(2))
            year_match = re.search(r"(\d{4})\s*$", evenement)
            if year_match:
                year = int(year_match.group(1))
                if not (start <= year <= end):
                    issues.append(
                        f"[{scen}] année {year} dans evenement_cle hors de "
                        f"date_bascule {date_bascule}"
                    )
            elif scen != "eco_communalism":
                issues.append(
                    f"[{scen}] evenement_cle sans année finale "
                    f"(attendue sauf pour eco_communalism) : {evenement!r}"
                )

        if date_bascule in existing_windows.get(scen, set()):
            issues.append(
                f"[{scen}] fenêtre {date_bascule} déjà utilisée par un "
                f"autre signal de {variable_slug} dans le registre."
            )
        new_windows_by_scen.setdefault(date_bascule, []).append(scen)

        if evenement.strip().lower() in all_events:
            issues.append(
                f"[{scen}] evenement_cle déjà présent dans le registre : "
                f"{evenement!r}"
            )

    for window, scens in new_windows_by_scen.items():
        if len(scens) > 1:
            issues.append(
                f"Fenêtre {window} dupliquée entre plusieurs scénarios "
                f"du même nouveau signal : {scens}"
            )

    return issues


# ---------------------------------------------------------------------------
# Injection dans les fiches variables
# ---------------------------------------------------------------------------

def inject_signal_to_state(variable_slug, yaml_text):
    path = VARIABLES_DIR / f"{variable_slug}.md"
    content = path.read_text(encoding="utf-8")

    # Le bloc section 12 est le DERNIER bloc ```yaml ... ``` du fichier.
    matches = list(re.finditer(r"```yaml\n(.*?)\n```", content, re.DOTALL))
    if not matches:
        raise RuntimeError(f"Aucun bloc ```yaml trouvé dans {variable_slug}.md")
    last = matches[-1]
    block_content = last.group(1)

    if not yaml_text.endswith("\n"):
        yaml_text += "\n"
    new_block_content = block_content.rstrip("\n") + "\n\n" + yaml_text.rstrip("\n")

    new_content = (
        content[: last.start(1)] + new_block_content + content[last.end(1):]
    )
    path.write_text(new_content, encoding="utf-8")


def inject_section7_annotation(variable_slug, annotation_line, signal_slug):
    path = VARIABLES_DIR / f"{variable_slug}.md"
    content = path.read_text(encoding="utf-8")

    section7 = extract_section(content, 7, 8)
    marker = "**custom (signaux d'actualité)**"

    if marker in section7:
        new_section7 = section7.rstrip() + f"\n{annotation_line}"
    else:
        new_section7 = section7.rstrip() + f"\n\n{marker}\n{annotation_line}"

    # Remplace l'ancienne section 7 par la nouvelle, en conservant les
    # titres "## 7." et "## 8." intacts.
    start_pat = re.compile(r"^##\s*7\.\s.*$", re.MULTILINE)
    end_pat = re.compile(r"^##\s*8\.\s", re.MULTILINE)
    m_start = start_pat.search(content)
    m_end = end_pat.search(content, m_start.end())

    new_content = (
        content[: m_start.end()]
        + "\n"
        + new_section7
        + "\n\n"
        + content[m_end.start():]
    )
    path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Régénération du registre
# ---------------------------------------------------------------------------

def _all_rows(registre_text):
    """Retourne toutes les lignes (listes de colonnes) du registre,
    tous scénarios confondus — utilisé pour recompter les totaux par type."""
    rows = []
    parts = re.split(r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text)
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        rows.extend(parse_registre_table(body))
    return rows


def regenerate_registre(variable_slug, signal_slug, entry, pilote):
    registre_text = read_registre_text()
    parts = re.split(r"(\n## (?:" + "|".join(SCENARIOS) + r")\n)", registre_text)
    output = [parts[0]]
    pilote_str = "oui" if pilote else "non"
    total_rows = 0

    for i in range(1, len(parts), 2):
        header = parts[i]
        body = parts[i + 1]
        scen = header.strip().replace("## ", "")

        lines = body.split("\n")
        table_start = None
        for idx, l in enumerate(lines):
            if l.startswith("|---"):
                table_start = idx
                break

        rows = []
        end_idx = len(lines)
        for idx in range(table_start + 1, len(lines)):
            l = lines[idx]
            if not l.startswith("|"):
                end_idx = idx
                break
            cols = [c.strip() for c in l.strip("|").split("|")]
            rows.append(cols)

        scen_data = entry["scenarios"][scen]
        rows.append([
            "signal", scen_data["date_bascule"], signal_slug, variable_slug,
            pilote_str, scen_data["evenement_cle"],
        ])

        def date_debut(row):
            try:
                return int(row[1].split("-")[0])
            except Exception:
                return 9999

        rows.sort(key=date_debut)
        total_rows += len(rows)

        new_table_lines = ["| " + " | ".join(r) + " |" for r in rows]
        new_body_lines = lines[: table_start + 1] + new_table_lines + lines[end_idx:]
        output.append(header)
        output.append("\n".join(new_body_lines))

    new_content = "".join(output)
    signal_rows = sum(
        1 for r in _all_rows(new_content) if len(r) >= 1 and r[0] == "signal"
    )
    evenement_rows = sum(
        1 for r in _all_rows(new_content) if len(r) >= 1 and r[0] == "evenement"
    )
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
# Fiche d'audit signaux_custom/
# ---------------------------------------------------------------------------

def write_custom_fiche(signal_slug, idea_text, source, variables, categorie, yaml_text):
    SIGNAUX_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    path = SIGNAUX_CUSTOM_DIR / f"{signal_slug}.md"
    content = f"""---
slug: {signal_slug}
source: {source}
categorie: {categorie}
variables_cibles: {variables}
statut: injected
---

## Idée source

{idea_text.strip()}

## Trajectoire injectée

```yaml
signal_to_state:
{yaml_text.rstrip()}
```
"""
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Gestion de la queue
# ---------------------------------------------------------------------------

def load_yaml_list(path, key="queue"):
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get(key, []) or []


def save_yaml_list(path, items, key="queue"):
    SIGNAUX_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump({key: items}, allow_unicode=True, sort_keys=False),
                     encoding="utf-8")


def append_yaml_list(path, item, key="processed"):
    items = load_yaml_list(path, key=key)
    items.append(item)
    save_yaml_list(path, items, key=key)


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

def process_idea(client, idea, dry_run=False):
    idea_id = idea.get("id", "sans_id")
    idea_text = idea["description"]
    source = idea.get("source", "actualite")
    variable_hint = idea.get("variable_hint")
    variable_hint_count = idea.get("variable_hint_count")

    print(f"\n=== {idea_id} ===")
    print("[1/4] Sélection de variable(s)...")
    selection = step1_select_variable(client, idea_text, variable_hint, variable_hint_count)
    variables = [v for v in selection["variables"] if v in VALID_VARS]
    categorie = selection["categorie"]
    signal_slug = selection["signal_slug"]
    print(f"  -> variables={variables} categorie={categorie} signal_slug={signal_slug}")

    if not variables:
        return {"status": "needs_review", "reason": "aucune variable valide proposée",
                "idea": idea, "selection": selection}

    registre_text = read_registre_text()
    results = []
    sibling_events = {}  # {scenario: evenement_cle} déjà validés pour CE signal dans ce run

    for variable_slug in variables:
        print(f"[2/4] Développement pour {variable_slug}...")
        previous, issues = None, None
        develop = step2_develop(
            client, idea_text, source, variable_slug, signal_slug, categorie,
            registre_text, sibling_events=sibling_events,
        )

        for attempt in range(MAX_FIX_ATTEMPTS + 1):
            yaml_text = develop["signal_to_state_yaml"]
            print(f"[3/4] Validation (essai {attempt + 1})...")
            issues = validate_signal_block(yaml_text, signal_slug, variable_slug, registre_text)
            if not issues:
                break
            print("  -> problèmes :")
            for i in issues:
                print(f"     - {i}")
            if attempt < MAX_FIX_ATTEMPTS:
                develop = step2_develop(
                    client, idea_text, source, variable_slug, signal_slug, categorie,
                    registre_text, previous=yaml_text, issues=issues,
                    sibling_events=sibling_events,
                )

        if issues:
            results.append({
                "variable": variable_slug, "status": "needs_review",
                "issues": issues, "yaml_text": yaml_text,
                "annotation": develop["section7_annotation"],
            })
            continue

        print("[4/4] Injection...")
        if not dry_run:
            inject_signal_to_state(variable_slug, yaml_text)
            inject_section7_annotation(variable_slug, develop["section7_annotation"], signal_slug)
            entry = yaml.safe_load("signal_to_state:\n" + yaml_text)["signal_to_state"][0]
            regenerate_registre(variable_slug, signal_slug, entry,
                                 pilote=variable_slug in PILOTS)
            # le registre vient de changer, on relit pour le prochain variable_slug
            registre_text = read_registre_text()
        else:
            print(yaml_text)
            print(develop["section7_annotation"])

        # On retient les evenement_cle de cette variable pour que la/les
        # variable(s) suivante(s) de CE MÊME signal (dans cette boucle) ne
        # les réutilisent pas, même en --dry-run où le registre n'est pas
        # encore mis à jour sur disque.
        entry_for_siblings = yaml.safe_load("signal_to_state:\n" + yaml_text)["signal_to_state"][0]
        for scen, data in entry_for_siblings["scenarios"].items():
            sibling_events[scen] = data["evenement_cle"]

        results.append({"variable": variable_slug, "status": "injected",
                         "yaml_text": yaml_text})

    if not dry_run:
        injected_yaml = "\n".join(
            r["yaml_text"] for r in results if r["status"] == "injected"
        )
        if injected_yaml:
            write_custom_fiche(signal_slug, idea_text, source, variables, categorie,
                                injected_yaml)

    overall = "needs_review" if any(r["status"] != "injected" for r in results) else "injected"
    return {"status": overall, "idea": idea, "selection": selection, "results": results}


QUEUE_TEMPLATE = """\
# signaux_custom/queue.yaml
#
# Ajoute ici tes idées de signaux faibles "custom" (observations de l'actualité,
# lectures, intuitions...). Lance ensuite :
#
#   python3 generator/inject_custom_signals.py            ← injection réelle
#   python3 generator/inject_custom_signals.py --dry-run  ← test sans écriture
#
# CHAMPS :
#   id                  : identifiant court lisible (lettres, chiffres, underscores)
#   description         : l'observation en langage naturel, quelques phrases suffisent
#   source              : libre — date, lien d'article, nom d'un livre...
#   variable_hint       : optionnel. Met null si tu ne sais pas — le LLM choisit
#                         automatiquement. Sinon, une variable unique (chaîne) ou
#                         plusieurs (liste) que tu IMPOSES comme cibles ; le LLM
#                         peut en ajouter d'autres si pertinent, dans la limite
#                         de variable_hint_count.
#                         Variables disponibles :
#                           systeme_economique_redistribution | gouvernance_institutions
#                           geopolitique_conflits | valeurs_culture_tempo_sociale
#                           organisation_territoires | sante_biotechnologies
#                           frontieres_du_systeme | technologie_information
#                           climat_environnement_global | energie_ressources_critiques
#                           demographie_mobilite_humaine | systemes_productifs_travail
#   variable_hint_count : optionnel, entier 1-4. Plafond du nombre total de
#                         variables que le LLM peut retourner (hint(s) inclus).
#                         Par défaut : 2. Monte à 3-4 si tu penses que le signal
#                         est vraiment structurant entre plusieurs domaines.
#
# EXEMPLES :
#   - id: mon_signal_2026
#     description: >
#       Plusieurs pays testent des chatbots thérapeutes remboursés par la
#       sécurité sociale, avec débat sur la responsabilité médicale en cas
#       d'erreur de l'IA.
#     source: actualite_2026-06
#     variable_hint: sante_biotechnologies
#     variable_hint_count: null   # garde le défaut (2)
#
#   - id: crise_structurante_2026
#     description: >
#       Une vague de ruptures d'approvisionnement en terres rares déclenche
#       à la fois des tensions diplomatiques et une accélération forcée des
#       politiques de relocalisation industrielle.
#     source: actualite_2026-06
#     variable_hint: [energie_ressources_critiques, geopolitique_conflits]
#     variable_hint_count: 4   # le LLM peut ajouter jusqu'à 2 variables de plus
#
# Les idées traitées sont déplacées vers processed.yaml (succès) ou
# needs_review.yaml (échec après corrections automatiques).
# ──────────────────────────────────────────────────────────────────────────────

queue:
"""


def save_queue_with_template(remaining):
    """Réécrit queue.yaml avec l'en-tête template + les idées restantes.
    Si la queue est vide, le fichier reste prêt à l'emploi avec le template."""
    SIGNAUX_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    if remaining:
        items_yaml = yaml.dump(remaining, allow_unicode=True,
                               sort_keys=False, default_flow_style=False)
        # yaml.dump génère "- id: ...\n  description: ...\n" — on indente de 2
        indented = "\n".join("  " + line for line in items_yaml.splitlines())
        content = QUEUE_TEMPLATE + indented + "\n"
    else:
        content = QUEUE_TEMPLATE + "  [] # ← remplace [] par tes idées\n"
    QUEUE_PATH.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Appelle le LLM et valide, mais n'écrit rien sur disque.")
    args = parser.parse_args()

    queue = load_yaml_list(QUEUE_PATH, key="queue")
    if not queue:
        print(f"Queue vide ({QUEUE_PATH}). Rien à faire.")
        return

    client = get_client()
    remaining = []

    for idea in queue:
        try:
            outcome = process_idea(client, idea, dry_run=args.dry_run)
        except Exception as e:
            outcome = {"status": "needs_review", "idea": idea, "error": str(e)}

        if args.dry_run:
            print(json.dumps(outcome, ensure_ascii=False, indent=2, default=str))
            remaining.append(idea)
            continue

        if outcome["status"] == "injected":
            append_yaml_list(PROCESSED_PATH, outcome, key="processed")
        else:
            append_yaml_list(NEEDS_REVIEW_PATH, outcome, key="needs_review")

    if not args.dry_run:
        save_queue_with_template(remaining)
        print(f"\nTerminé. Voir {PROCESSED_PATH} et {NEEDS_REVIEW_PATH}.")


if __name__ == "__main__":
    main()
