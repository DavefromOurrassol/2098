#!/usr/bin/env python3
"""
fix_alliances_oppositions.py — Ourrassol 2098
================================================

Corrige spécifiquement les champs `alliances`/`oppositions` vides sur les
fiches instances déjà `officialise_enrichi`, SANS toucher aux autres champs
déjà écrits (responsabilites, description_journalistique, signes_distinctifs,
tensions_narratives, localisation, impact_local/global, etc.).

CONTEXTE (diagnostic du 4 août 2026)
-------------------------------------
enrich_minimal.py ne fournit jamais au LLM la liste des instances existantes
du scénario au moment de générer `alliances`/`oppositions` — contrairement à
la géographie, qui dispose de sa propre liste de slugs valides
(build_geographie_summary). Résultat mesuré sur le vault réel :
356/426 fiches officialise_enrichi (83.6%) ont alliances ET oppositions
vides, alors que type_relation_dominante/annee_debut/annee_fin sont
remplis à 100%. Ce n'est pas un signal réel d'absence de relations (voir
le cas consortium_nexus_calcul_policy_reform, dont tensions_narratives
décrit explicitement des rivaux, malgré alliances/oppositions vides) —
c'est une conséquence du prompt d'origine, qui exige des slugs réels sans
jamais donner au LLM la liste sur laquelle piocher.

CE QUE FAIT CE SCRIPT
----------------------
1. PASSE LLM CIBLÉE (par fiche, par scénario)
   - Repère les fiches officialise_enrichi avec alliances ET oppositions
     vides
   - Construit un prompt minimal : contenu déjà enrichi de la fiche
     (role_dans_scenario, responsabilites, tensions_narratives) + LISTE
     RÉELLE des autres instances du scénario (l'ingrédient manquant)
   - Ne redemande QUE alliances/oppositions — aucun autre champ n'est
     regénéré
   - Valide les slugs renvoyés contre la liste fournie (erreur bloquante,
     pas juste un warning, puisque le LLM n'a plus d'excuse pour halluciner)
   - Patch chirurgical du frontmatter (regex ciblée sur les 2 clés, pas de
     réécriture complète du YAML) + ajout/mise à jour de la section
     "## Relations" dans le corps Markdown (cohérence avec le style du
     pipeline d'origine, wikilinks inclus)

2. PASSE DE RÉCIPROCITÉ (locale, sans appel LLM, après la passe 1 ou en
   mode autonome via --reciprocite-seule)
   - Si A cite B en alliance, B doit citer A en retour (idem oppositions)
   - Les conflits (B a déjà classé A dans la catégorie opposée) ne sont
     JAMAIS résolus automatiquement — juste remontés dans un rapport pour
     revue manuelle

USAGE — COMMENCER PAR ESTIMER LE COÛT AVANT UN RUN COMPLET
------------------------------------------------------------
    # 1. Test à vide, aucun appel LLM, juste pour voir combien de fiches sont concernées
    python3 fix_alliances_oppositions.py --scenario policy_reform --dry-run --limit 3

    # 2. Un scénario complet, en dry-run, pour valider le comportement
    python3 fix_alliances_oppositions.py --scenario policy_reform --dry-run

    # 3. Un scénario complet, pour de vrai
    python3 fix_alliances_oppositions.py --scenario policy_reform

    # 4. Tous les scénarios
    python3 fix_alliances_oppositions.py --all

    # 5. Uniquement la passe de réciprocité (si la passe LLM a déjà tourné)
    python3 fix_alliances_oppositions.py --all --reciprocite-seule

    # 6. Passe LLM sans réciprocité automatique (si tu préfères la lancer à part)
    python3 fix_alliances_oppositions.py --all --skip-reciprocite

PRÉREQUIS
---------
    pip install pyyaml --break-system-packages
    À placer dans le même dossier que enrich_minimal.py (même dépendance
    à llm_client.py et même convention VAULT_ROOT = dossier parent).
"""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

import yaml

from llm_client import call_llm


# ---------------------------------------------------------------------------
# Configuration (mêmes conventions que enrich_minimal.py)
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
INSTANCES_DIR = VAULT_ROOT / "instances"
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
CONFLICTS_PATH = NEED_ACTION_DIR / "fix_alliances_conflits_reciprocite.md"
RESOLVED_CONFLICTS_PATH = NEED_ACTION_DIR / "fix_alliances_conflits_reciprocite_resolus.md"

# Ces deux rapports étaient jusqu'au 7 août 2026 ouverts en mode "a"
# (append) et n'étaient donc JAMAIS réinitialisés — un fichier accumulait
# indéfiniment l'historique de tous les runs depuis sa création (ex. du 4
# au 7 août dans le vault réel de David), avec pour conséquence un vrai
# bug ergonomique : le GUI affiche ces fichiers tels quels dans le
# panneau de review, sans distinguer un conflit d'il y a 3 jours (déjà
# résolu depuis) d'un conflit du run en cours — l'utilisateur n'a alors
# aucun moyen de savoir si ce qu'il lit est d'actualité.
#
# Correctif (7 août) : `reset_conflict_reports()` tronque explicitement
# les deux fichiers en tête de run (voir son docstring) ; `_write_
# conflict_report()` accumule ensuite les sections des scénarios traités
# dans ce même run. `_files_reset_this_run` (set module-level) trace
# quels chemins ont déjà été réinitialisés au cours du process Python en
# cours — il vit pour la durée de ce process (un run standalone `fix_
# alliances_oppositions.py`, ou un run `enrich_minimal.py` qui importe et
# appelle ces fonctions dans le MÊME process). Le GUI, lui, lance chaque
# run dans un nouveau subprocess via Popen, donc repart toujours d'un set
# vide à chaque clic — comportement voulu.
_files_reset_this_run: set = set()


def reset_conflict_reports() -> None:
    """
    Réinitialise les deux rapports de conflits (détectés et résolus) en
    tête d'un run de réciprocité, pour garantir qu'ils ne reflètent QUE ce
    run — même si aucun scénario traité ne remonte de conflit. Sans cet
    appel explicite, un run "propre" (0 conflit partout) n'écrirait rien
    du tout, laissant un éventuel vieux contenu de run précédent affiché
    indéfiniment dans le GUI comme si c'était toujours d'actualité (bug
    ergonomique réel du 7 août — un fichier accumulé depuis le 4 août
    laissait croire à David que le vault avait "beaucoup de conflits"
    alors qu'il était déjà revenu à 0 depuis plusieurs runs).

    À appeler UNE SEULE FOIS, avant la boucle sur les scénarios, par tout
    point d'entrée qui va appeler reciprocity_pass() et/ou
    resolve_reciprocity_conflicts() pour un ou plusieurs scénarios —
    fix_alliances_oppositions.py::main() et enrich_minimal.py le font
    tous les deux (voir leurs blocs respectifs).
    """
    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = f"{datetime.now():%Y-%m-%d %H:%M}"
    for path in (CONFLICTS_PATH, RESOLVED_CONFLICTS_PATH):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# État au run du {timestamp}\n")
        _files_reset_this_run.add(path)


def _write_conflict_report(path, scenario: str, header_suffix: str, lines: list) -> None:
    """
    Ajoute une section de rapport de conflits (détectés ou résolus) pour
    un scénario. Suppose que `reset_conflict_reports()` a déjà été
    appelée une fois en tête du run — accumule ("a") sans jamais tronquer
    ici, pour ne pas écraser les sections des scénarios déjà traités dans
    le même run.
    """
    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    mode = "a" if path in _files_reset_this_run else "w"  # filet de sécurité si reset_conflict_reports() a été omise
    with open(path, mode, encoding="utf-8") as f:
        f.write(f"\n## {scenario} — {datetime.now():%Y-%m-%d %H:%M}{header_suffix}\n")
        for line in lines:
            f.write(f"- {line}\n")
    _files_reset_this_run.add(path)

SCENARIOS = [
    "breakdown",
    "fortress_world",
    "new_sustainability",
    "eco_communalism",
    "policy_reform",
    "reference",
]

MAX_FIX_ATTEMPTS = 2

# Pannes transitoires de l'API (503, timeout réseau, reset de connexion...) —
# distinctes des erreurs de contenu (JSON invalide/slug incorrect), qui ne
# sont pas transitoires et ne doivent pas être retentées de la même façon.
TRANSIENT_RETRIES = 3
TRANSIENT_BACKOFF_SECONDS = 5


# ---------------------------------------------------------------------------
# Parsing (identique à enrich_minimal.py — même regex de frontmatter)
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


def patch_alliances_oppositions_frontmatter(raw_frontmatter_block, alliances, oppositions):
    """
    Remplace ou ajoute UNIQUEMENT les clés alliances/oppositions dans le
    bloc frontmatter brut (texte), en laissant tous les autres champs
    strictement intacts (pas de round-trip yaml.dump qui risquerait de
    reformater des champs multi-lignes déjà écrits).
    """

    def render_list(values):
        if not values:
            return " []"
        return "\n" + "\n".join(f"- {v}" for v in values)

    block = raw_frontmatter_block
    for key, values in [("alliances", alliances), ("oppositions", oppositions)]:
        new_line = f"{key}:{render_list(values)}"
        # Une clé de frontmatter YAML top-level suivie de son bloc (liste
        # indentée ou scalaire), jusqu'à la prochaine clé top-level ou la fin.
        pattern = re.compile(
            rf"(?m)^{re.escape(key)}:.*?(?=\n[A-Za-z_][A-Za-z0-9_]*:|\Z)", re.DOTALL
        )
        if pattern.search(block):
            block = pattern.sub(new_line, block, count=1)
        else:
            block = block.rstrip("\n") + f"\n{new_line}\n"
    return block


def patch_relations_section(body, alliances, oppositions):
    """
    Ajoute ou met à jour la section '## Relations' du corps Markdown,
    dans le même style que write_enriched_fiche() (wikilinks [[...]]).
    Insérée avant '## Notes' si présente, sinon en fin de corps.
    Si alliances et oppositions sont vides, ne fait rien (pas de section
    vide ajoutée).
    """
    if not alliances and not oppositions:
        return body

    lines = ["## Relations"]
    if alliances:
        lines.append("**Alliés :**")
        for a in alliances:
            lines.append(f"- [[{a}]]")
    if oppositions:
        lines.append("**Opposants :**")
        for o in oppositions:
            lines.append(f"- [[{o}]]")
    relations_block = "\n".join(lines)

    # Retire une éventuelle ancienne section Relations (cas réciprocité
    # qui tourne une 2e fois sur une fiche déjà patchée une 1re fois)
    body_wo_relations = re.sub(
        r"\n## Relations\n(?:.*?\n)*?(?=\n## |\Z)", "\n", body
    )

    if "## Notes" in body_wo_relations:
        return body_wo_relations.replace(
            "## Notes", f"{relations_block}\n\n## Notes", 1
        )
    return body_wo_relations.rstrip("\n") + f"\n\n{relations_block}\n"


def write_alliances_patch(path, alliances, oppositions):
    """Applique le patch frontmatter + body et réécrit le fichier."""
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)", raw, re.DOTALL)
    if not m:
        raise ValueError(f"Frontmatter introuvable dans {path}")
    prefix, fm_block, marker, body = m.groups()

    new_fm_block = patch_alliances_oppositions_frontmatter(fm_block, alliances, oppositions)
    new_body = patch_relations_section(body, alliances, oppositions)

    new_raw = f"{prefix}{new_fm_block}{marker}{new_body}"
    path.write_text(new_raw, encoding="utf-8")


# ---------------------------------------------------------------------------
# Découverte des fiches concernées + index des instances du scénario
# ---------------------------------------------------------------------------

def find_target_fiches(scenario, slug_filter=None):
    """Fiches officialise_enrichi avec alliances ET oppositions vides."""
    result = []
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, body = parse_md(path)
        if fm.get("statut") != "officialise_enrichi":
            continue
        if slug_filter and fm.get("slug", path.stem) != slug_filter:
            continue
        alliances = fm.get("alliances") or []
        oppositions = fm.get("oppositions") or []
        if alliances or oppositions:
            continue  # déjà remplie, pas concernée par ce script
        result.append({"path": path, "fm": fm, "body": body})
    return result


def build_scenario_instances_index(scenario):
    """
    Index slug -> name de TOUTES les instances existantes du scénario,
    tous statuts confondus (y compris officialise_minimal, pour ne
    jamais proposer un slug qui n'existe pas encore réellement, ni en
    rater un qui existe déjà même sans être encore enrichi).
    """
    index = {}
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, _ = parse_md(path)
        slug = fm.get("slug", path.stem)
        name = fm.get("name", slug)
        index[slug] = name
    return index


def build_instances_summary(instances_index, exclude_slug):
    """Équivalent de build_geographie_summary() (enrich_minimal.py) mais pour les instances."""
    lines = []
    for slug, name in sorted(instances_index.items(), key=lambda kv: kv[1]):
        if slug == exclude_slug:
            continue
        lines.append(f"  {slug} — {name}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt ciblé (alliances/oppositions UNIQUEMENT)
# ---------------------------------------------------------------------------

def build_targeted_prompt(fiche, scenario, instances_index):
    fm = fiche["fm"]
    slug = fm.get("slug", fiche["path"].stem)
    name = fm.get("name", slug)

    instances_summary = build_instances_summary(instances_index, exclude_slug=slug)
    n_autres = len(instances_index) - (1 if slug in instances_index else 0)

    system_prompt = """Tu es l'assistant de worldbuilding du projet Ourrassol 2098.
Tu identifies les alliances et oppositions d'une entité déjà bien décrite,
en te basant UNIQUEMENT sur les entités réellement listées ci-dessous.
Tes réponses sont UNIQUEMENT du JSON valide, sans aucun texte avant ou après.
Ne mets pas de backticks ni de balises markdown autour du JSON."""

    user_prompt = f"""TÂCHE : Identifier les alliances et oppositions de cette entité, pour le scénario {scenario}.

Cette fiche est déjà entièrement enrichie. Le contenu ci-dessous est fourni
comme CONTEXTE uniquement — ne le modifie pas, ne le régénère pas.

═══════════════════════════════════════════════════
FICHE (contexte, déjà rédigée)
═══════════════════════════════════════════════════
slug: {slug}
name: {name}
role_dans_scenario: {fm.get("role_dans_scenario", "")}
responsabilites: {fm.get("responsabilites", "")}
tensions_narratives: {fm.get("tensions_narratives", "")}
type_relation_dominante (déjà fixé, pour information) : {fm.get("type_relation_dominante", "")}

═══════════════════════════════════════════════════
AUTRES INSTANCES RÉELLES DE CE SCÉNARIO — {n_autres} entités (slugs valides)
═══════════════════════════════════════════════════
{instances_summary}

═══════════════════════════════════════════════════
INSTRUCTIONS
═══════════════════════════════════════════════════
Génère un JSON avec EXACTEMENT ces champs :

{{
  "alliances": ["slug_instance_valide", ...],
  "oppositions": ["slug_instance_valide", ...]
}}

RÈGLES IMPÉRATIVES :
- Choisis UNIQUEMENT des slugs présents dans la liste ci-dessus. N'invente
  jamais un slug, ne devine jamais un nom approché.
- Base-toi sur le contenu réel de la fiche (rôle, responsabilités,
  tensions) pour identifier des relations plausibles et cohérentes avec
  le scénario {scenario} — pas de relations arbitraires ou décoratives.
- Si aucune relation claire ne ressort du contenu fourni, un tableau vide
  est un résultat parfaitement acceptable. Ne force rien pour remplir.
- Une même entité ne peut pas apparaître à la fois dans alliances et dans
  oppositions.
- Reste sélectif : 0 à 5 entrées par champ, en priorisant les relations
  les plus significatives pour la narration de ce scénario.
"""
    return system_prompt, user_prompt


def call_llm_json(system, user_content, max_tokens=1500):
    raw = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
        task_tier="structured_strict",
    ).strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()
    try:
        data, _ = json.JSONDecoder().raw_decode(raw)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON invalide : {e}\nRaw : {raw[:300]}")


def call_llm_json_resilient(system, user_content, max_tokens=1500):
    """
    Comme call_llm_json, mais absorbe les pannes transitoires de l'API
    (503, timeout, connexion refusée...) avec un backoff, au lieu de
    laisser l'exception remonter et tuer tout le run --all. Une erreur
    de CONTENU (JSON invalide) n'est PAS transitoire — elle n'est pas
    retentée ici, elle remonte immédiatement (le mécanisme de correction
    de process_fiche s'en charge séparément, via un nouveau prompt).
    """
    last_error = None
    for attempt in range(1, TRANSIENT_RETRIES + 1):
        try:
            return call_llm_json(system, user_content, max_tokens)
        except ValueError:
            raise  # erreur de contenu : pas transitoire, ne pas retenter ici
        except Exception as e:
            last_error = e
            is_last = attempt == TRANSIENT_RETRIES
            print(f"    [panne API, tentative {attempt}/{TRANSIENT_RETRIES}] {e}")
            if not is_last:
                wait = TRANSIENT_BACKOFF_SECONDS * attempt
                print(f"    [attente {wait}s avant nouvelle tentative]")
                time.sleep(wait)
    raise RuntimeError(f"Panne API persistante après {TRANSIENT_RETRIES} tentatives : {last_error}")


def validate_targeted(data, instances_index, self_slug):
    """Erreurs bloquantes uniquement — le LLM a désormais la liste réelle,
    donc un slug hors liste est une vraie erreur à corriger, pas un simple
    warning comme dans enrich_minimal.py."""
    errors = []
    for field in ["alliances", "oppositions"]:
        slugs = data.get(field, [])
        if not isinstance(slugs, list):
            errors.append(f"'{field}' doit être une liste")
            continue
        for s in slugs:
            if not isinstance(s, str):
                errors.append(f"{field}: entrée non textuelle {s!r}")
            elif s == self_slug:
                errors.append(f"{field}: '{s}' est l'entité elle-même (auto-référence interdite)")
            elif s not in instances_index:
                errors.append(f"{field}: '{s}' n'existe pas dans la liste fournie")
    overlap = set(data.get("alliances") or []) & set(data.get("oppositions") or [])
    if overlap:
        errors.append(f"Slugs présents dans alliances ET oppositions : {sorted(overlap)}")
    return errors


# ---------------------------------------------------------------------------
# Traitement d'une fiche
# ---------------------------------------------------------------------------

def process_fiche(fiche, scenario, instances_index, dry_run):
    fm = fiche["fm"]
    slug = fm.get("slug", fiche["path"].stem)
    print(f"  → {slug}")

    system_prompt, user_prompt = build_targeted_prompt(fiche, scenario, instances_index)

    try:
        data = call_llm_json_resilient(system_prompt, user_prompt)
    except Exception as e:
        print(f"    [ÉCHEC] {e}")
        return False, None, [str(e)]

    errors = validate_targeted(data, instances_index, slug)
    attempt = 0
    while errors and attempt < MAX_FIX_ATTEMPTS:
        attempt += 1
        print(f"    [retry {attempt}/{MAX_FIX_ATTEMPTS}] {len(errors)} erreur(s)")
        fix_prompt = f"""{user_prompt}

═══════════════════════════════════════════════════
CORRECTION REQUISE
═══════════════════════════════════════════════════
{chr(10).join(f"  - {e}" for e in errors)}

JSON précédent : {json.dumps(data, ensure_ascii=False)}
Corrige uniquement les champs en erreur et retourne le JSON complet corrigé.
"""
        try:
            data = call_llm_json_resilient(system_prompt, fix_prompt)
        except Exception as e:
            errors = [str(e)]
            break
        errors = validate_targeted(data, instances_index, slug)

    if errors:
        print(f"    [ÉCHEC PERSISTANT] {len(errors)} erreur(s) :")
        for e in errors:
            print(f"      - {e}")
        return False, data, errors

    alliances = data.get("alliances") or []
    oppositions = data.get("oppositions") or []
    print(f"    ✓ alliances={alliances} oppositions={oppositions}")

    if not dry_run:
        write_alliances_patch(fiche["path"], alliances, oppositions)

    return True, data, []


# ---------------------------------------------------------------------------
# Passe de réciprocité (locale, sans LLM)
# ---------------------------------------------------------------------------

def reciprocity_pass(scenario, dry_run, resolution_suit=False):
    """
    Pour chaque instance du scénario, si A cite B en alliance/opposition,
    B doit citer A en retour. Cette fonction elle-même ne résout jamais
    les conflits (B a déjà classé A dans la catégorie opposée) — elle se
    contente de les détecter et de les consigner dans CONFLICTS_PATH.

    `resolution_suit` sert uniquement à adapter le message affiché : si
    True, la résolution automatique (opposition prioritaire, voir
    resolve_reciprocity_conflicts) va être appelée juste après dans le
    même run, et le message le précise pour éviter de laisser croire que
    les conflits resteront non résolus. Si False (défaut), le message
    reste tel qu'avant : ces conflits nécessitent une revue manuelle.
    """
    print(f"\n{'─' * 60}")
    print(f"PASSE DE RÉCIPROCITÉ — {scenario}")
    print(f"{'─' * 60}")

    fiches = {}
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, body = parse_md(path)
        slug = fm.get("slug", path.stem)
        fiches[slug] = {"path": path, "fm": fm, "body": body}

    additions = {slug: {"alliances": set(), "oppositions": set()} for slug in fiches}
    conflicts = []

    for slug, data in fiches.items():
        fm = data["fm"]
        for field, opposite in [("alliances", "oppositions"), ("oppositions", "alliances")]:
            for target in (fm.get(field) or []):
                if target not in fiches or target == slug:
                    continue  # slug fantôme ou auto-référence, ignoré ici
                target_fm = fiches[target]["fm"]
                already_same = slug in (target_fm.get(field) or [])
                already_opposite = slug in (target_fm.get(opposite) or [])
                if already_same:
                    continue  # déjà réciproque, rien à faire
                if already_opposite:
                    suffixe = (
                        " — sera résolu automatiquement ci-dessous "
                        "(opposition prioritaire sur alliance)"
                        if resolution_suit
                        else " — conflit non résolu automatiquement (revue manuelle nécessaire)"
                    )
                    conflicts.append(
                        f"{slug} classe {target} dans '{field}', mais {target} classe "
                        f"{slug} dans '{opposite}'{suffixe}"
                    )
                    continue
                additions[target][field].add(slug)

    n_added = 0
    for slug, adds in additions.items():
        if not adds["alliances"] and not adds["oppositions"]:
            continue
        fm = fiches[slug]["fm"]
        new_alliances = sorted(set(fm.get("alliances") or []) | adds["alliances"])
        new_oppositions = sorted(set(fm.get("oppositions") or []) | adds["oppositions"])
        n_added += 1
        print(f"  + {slug} : +{len(adds['alliances'])} alliance(s), +{len(adds['oppositions'])} opposition(s)")
        if not dry_run:
            write_alliances_patch(fiches[slug]["path"], new_alliances, new_oppositions)

    print(f"\n  {n_added} fiche(s) complétée(s) par réciprocité")
    if conflicts:
        resume_suffixe = (
            " (résolution automatique — opposition prioritaire — à suivre)"
            if resolution_suit
            else " (non corrigés automatiquement)"
        )
        print(f"  ⚠ {len(conflicts)} conflit(s) détecté(s){resume_suffixe} :")
        for c in conflicts:
            print(f"    - {c}")
        if not dry_run:
            _write_conflict_report(CONFLICTS_PATH, scenario, "", conflicts)

    return n_added, conflicts


# ---------------------------------------------------------------------------
# Résolution automatique des conflits (opposition prioritaire sur alliance)
# ---------------------------------------------------------------------------

def find_conflicts(scenario):
    """
    Détecte les conflits de réciprocité actuels sur le scénario, sans rien
    modifier. Réutilise la même définition que reciprocity_pass() : A liste
    B dans `field` (alliances ou oppositions), et B liste A dans le champ
    OPPOSÉ. Chaque paire est dédupliquée (un seul conflit par couple
    d'entités, quel que soit le sens dans lequel il est détecté).

    Retourne (fiches, conflicts) où fiches est l'index slug -> {path, fm,
    body} (réutilisable directement par resolve_reciprocity_conflicts pour
    éviter un second passage disque), et conflicts une liste de dicts
    {"allie_a_corriger": slug, "opposant": slug}.
    """
    fiches = {}
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, body = parse_md(path)
        slug = fm.get("slug", path.stem)
        fiches[slug] = {"path": path, "fm": fm, "body": body}

    conflicts = []
    seen_pairs = set()
    for slug, data in fiches.items():
        fm = data["fm"]
        for ally in (fm.get("alliances") or []):
            if ally not in fiches or ally == slug:
                continue  # slug fantôme ou auto-référence, hors scope ici
            ally_oppositions = fiches[ally]["fm"].get("oppositions") or []
            if slug not in ally_oppositions:
                continue
            pair_key = tuple(sorted([slug, ally]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            conflicts.append({"allie_a_corriger": slug, "opposant": ally})

    return fiches, conflicts


def resolve_reciprocity_conflicts(scenario, dry_run, bascule_en_opposition=False):
    """
    Résout automatiquement les conflits de réciprocité selon la règle "opposition prioritaire" :
    l'opposition l'emporte sur l'alliance. Pour chaque conflit détecté
    (slug A liste B en alliance, B liste A en opposition), la fiche A est
    corrigée : B est retiré de ses `alliances`. La fiche B (celle qui a
    l'opposition) n'est jamais modifiée par cette fonction.

    Si bascule_en_opposition=True, B est en plus ajouté aux `oppositions`
    de A (résolution "forte" : A finit par lister B en opposition, comme
    B le fait déjà envers A). Par défaut (False), B est simplement retiré
    des alliances de A, sans rien ajouter (résolution "conservatrice" —
    ne fabrique pas une opposition que le LLM n'a jamais formulée).

    RÉTROACTIF : cette fonction modifie les fiches déjà existantes sur
    disque (sauf en --dry-run). Elle ne touche PAS aux futures créations
    (ça, c'est déjà géré par le prompt corrigé d'enrich_minimal.py) — elle
    ne fait que nettoyer le stock de conflits déjà présents dans le vault
    au moment où elle est exécutée.

    Chaque résolution est consignée dans RESOLVED_CONFLICTS_PATH pour
    traçabilité et revue manuelle ultérieure possible (le fichier
    frontmatter lui-même n'est pas marqué — patch chirurgical alliances/
    oppositions uniquement, même convention que write_alliances_patch).
    """
    print(f"\n{'─' * 60}")
    print(f"RÉSOLUTION AUTOMATIQUE DES CONFLITS (opposition prioritaire) — {scenario}")
    print(f"{'─' * 60}")

    fiches, conflicts = find_conflicts(scenario)

    if not conflicts:
        print("  Aucun conflit détecté sur ce scénario.")
        return 0, []

    print(f"  {len(conflicts)} conflit(s) détecté(s) :\n")

    # IMPORTANT : accumuler toutes les corrections par slug AVANT d'écrire,
    # plutôt qu'écrire un patch par conflit au fil de l'eau. Une même fiche
    # peut être "allie_a_corriger" dans PLUSIEURS conflits distincts du
    # même scénario (ex. une entité qui liste à tort 2 opposants différents
    # en alliance) — écrire au fil de l'eau en repartant à chaque fois du
    # frontmatter original en mémoire écraserait silencieusement les
    # corrections précédentes sur cette même fiche (bug corrigé le 7 août
    # après un run réel où 11 paires sur 73 avaient été perdues de cette
    # façon). Même pattern de correction que celui déjà utilisé par
    # reciprocity_pass() (dict `additions` accumulé avant écriture).
    to_remove = {}          # slug -> set d'alliés à retirer des alliances
    to_add_opposition = {}  # slug -> set d'alliés à ajouter aux oppositions

    for c in conflicts:
        slug = c["allie_a_corriger"]
        ally = c["opposant"]
        to_remove.setdefault(slug, set()).add(ally)
        if bascule_en_opposition:
            to_add_opposition.setdefault(slug, set()).add(ally)

        action = f"retrait de '{ally}' des alliances de '{slug}'"
        if bascule_en_opposition:
            action += f" + ajout de '{ally}' aux oppositions de '{slug}'"
        print(f"  - {slug} vs {ally} : {action}")

    resolutions = [
        f"{c['allie_a_corriger']} : retrait de '{c['opposant']}' des alliances"
        + (f" + ajout aux oppositions" if bascule_en_opposition else "")
        + f" (conflit : {c['allie_a_corriger']} listait {c['opposant']} en alliance, "
        f"{c['opposant']} liste {c['allie_a_corriger']} en opposition)"
        for c in conflicts
    ]

    affected_slugs = set(to_remove) | set(to_add_opposition)
    for slug in affected_slugs:
        fm = fiches[slug]["fm"]
        removals = to_remove.get(slug, set())
        additions = to_add_opposition.get(slug, set())

        new_alliances = sorted(s for s in (fm.get("alliances") or []) if s not in removals)
        new_oppositions = sorted(set(fm.get("oppositions") or []) | additions)

        if not dry_run:
            write_alliances_patch(fiches[slug]["path"], new_alliances, new_oppositions)

    print(f"\n  {len(conflicts)} conflit(s) résolu(s), {len(affected_slugs)} fiche(s) écrite(s)"
          + (" (dry-run, rien écrit)" if dry_run else ""))

    if not dry_run:
        _write_conflict_report(
            RESOLVED_CONFLICTS_PATH, scenario, " (opposition prioritaire)", resolutions
        )

    return len(conflicts), resolutions


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_scenario(scenario, slug_filter, dry_run, limit):
    print(f"\n{'═' * 60}")
    print(f"SCÉNARIO : {scenario.upper()}")
    print(f"{'═' * 60}")

    fiches = find_target_fiches(scenario, slug_filter)
    if not fiches:
        print("  (aucune fiche concernée — alliances/oppositions déjà remplies, ou aucune fiche officialise_enrichi)")
        return 0, 0

    total_disponibles = len(fiches)
    if limit:
        fiches = fiches[:limit]
        print(f"  {total_disponibles} fiche(s) concernée(s) — traitement limité à {len(fiches)} (--limit)")
    else:
        print(f"  {len(fiches)} fiche(s) concernée(s)")

    instances_index = build_scenario_instances_index(scenario)

    n_ok, n_fail = 0, 0
    for fiche in fiches:
        try:
            success, data, errors = process_fiche(fiche, scenario, instances_index, dry_run)
        except Exception as e:
            # Filet de sécurité : une panne imprévue sur une fiche (I/O,
            # etc.) ne doit jamais interrompre le traitement des suivantes.
            slug = fiche["fm"].get("slug", fiche["path"].stem)
            print(f"    [ÉCHEC INATTENDU] {slug} : {e}")
            success = False
        if success:
            n_ok += 1
        else:
            n_fail += 1

    return n_ok, n_fail


def main():
    parser = argparse.ArgumentParser(
        description="Corrige les alliances/oppositions vides sur les fiches déjà enrichies, sans toucher aux autres champs."
    )
    parser.add_argument("--scenario", help="Scénario à traiter (ex: policy_reform)")
    parser.add_argument("--all", action="store_true", help="Traite tous les scénarios")
    parser.add_argument("--slug", help="Traite uniquement une fiche par son slug")
    parser.add_argument("--dry-run", action="store_true", help="N'écrit rien sur disque")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limite le nombre de fiches traitées PAR SCÉNARIO — à utiliser en premier pour estimer le coût réel avant un run complet",
    )
    parser.add_argument(
        "--reciprocite-seule", action="store_true",
        help="Ne lance QUE la passe de réciprocité (aucun appel LLM)",
    )
    parser.add_argument(
        "--skip-reciprocite", action="store_true",
        help="Ne lance pas la passe de réciprocité après la passe LLM",
    )
    parser.add_argument(
        "--resoudre-conflits", action="store_true",
        help="Après la passe de réciprocité, résout automatiquement les conflits "
             "détectés selon la règle opposition prioritaire (une opposition "
             "déclarée l'emporte sur une alliance déclarée en cas de contradiction). "
             "RÉTROACTIF : modifie les fiches existantes en conflit. Sans effet "
             "si combiné à --dry-run (liste les résolutions qui seraient faites, "
             "n'écrit rien).",
    )
    parser.add_argument(
        "--bascule-en-opposition", action="store_true",
        help="Avec --resoudre-conflits : au lieu de simplement retirer l'entité "
             "des alliances, l'ajoute aussi aux oppositions (résolution 'forte'). "
             "Par défaut, résolution conservatrice : retrait seul, sans ajout.",
    )
    args = parser.parse_args()

    if not args.scenario and not args.all:
        parser.error("Spécifier --scenario NOM ou --all")

    scenarios_to_run = SCENARIOS if args.all else [args.scenario]

    print("=" * 60)
    print("OURRASSOL 2098 — Correction ciblée alliances/oppositions")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)")

    total_ok, total_fail = 0, 0

    if not args.reciprocite_seule:
        for scenario in scenarios_to_run:
            if scenario not in SCENARIOS:
                print(f"[WARN] Scénario inconnu : {scenario} — ignoré")
                continue
            n_ok, n_fail = run_scenario(scenario, args.slug, args.dry_run, args.limit)
            total_ok += n_ok
            total_fail += n_fail

        print(f"\n{'═' * 60}")
        print("RÉSUMÉ PASSE LLM")
        print(f"{'═' * 60}")
        print(f"  Corrigées : {total_ok}")
        print(f"  Échecs    : {total_fail}")

    if not args.skip_reciprocite:
        if not args.dry_run:
            reset_conflict_reports()
        total_added, total_conflicts = 0, 0
        for scenario in scenarios_to_run:
            if scenario not in SCENARIOS:
                continue
            n_added, conflicts = reciprocity_pass(
                scenario, args.dry_run, resolution_suit=args.resoudre_conflits
            )
            total_added += n_added
            total_conflicts += len(conflicts)

        print(f"\n{'═' * 60}")
        print("RÉSUMÉ PASSE RÉCIPROCITÉ")
        print(f"{'═' * 60}")
        print(f"  Fiches complétées : {total_added}")
        print(f"  Conflits détectés : {total_conflicts}")
        if total_conflicts:
            print(f"  → voir {CONFLICTS_PATH}")

        if args.resoudre_conflits:
            total_resolved = 0
            for scenario in scenarios_to_run:
                if scenario not in SCENARIOS:
                    continue
                n_resolved, _ = resolve_reciprocity_conflicts(
                    scenario, args.dry_run, args.bascule_en_opposition
                )
                total_resolved += n_resolved

            print(f"\n{'═' * 60}")
            print("RÉSUMÉ RÉSOLUTION AUTOMATIQUE (opposition prioritaire)")
            print(f"{'═' * 60}")
            print(f"  Conflits résolus : {total_resolved}"
                  + (" (dry-run, rien écrit)" if args.dry_run else ""))
            if total_resolved and not args.dry_run:
                print(f"  → détail dans {RESOLVED_CONFLICTS_PATH}")


if __name__ == "__main__":
    main()
