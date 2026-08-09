#!/usr/bin/env python3
"""
fix_annee_debut_placeholder.py — Ourrassol 2098
================================================

Corrige spécifiquement le champ `annee_debut` sur les fiches instances déjà
`officialise_enrichi` qui sont restées bloquées à la valeur de placeholder
2026, SANS toucher aux autres champs déjà écrits.

CONTEXTE (diagnostic du 7 août 2026, point 1.2 du backlog)
------------------------------------------------------------
Deux causes distinctes, aujourd'hui corrigées à la source (generate_
instances.py, create_entities_and_instances.py, enrich_minimal.py) mais
qui laissent 477/710 fiches (67%) figées à annee_debut=2026 sur le vault
existant :
  1. officialize_alliances.py écrit annee_debut=2026 EN DUR (aucun appel
     LLM) au moment de créer la fiche officialise_minimal — un placeholder
     explicitement marqué "à développer en phase 2".
  2. enrich_minimal.py (la "phase 2") ne redemandait jamais annee_debut au
     LLM — son schéma de sortie ne contenait pas ce champ. Une fiche créée
     par le chemin 1 restait donc bloquée à 2026 même après enrichissement
     complet.
  3. Séparément, generate_instances.py/create_entities_and_instances.py
     montraient "annee_debut": 2026 comme valeur D'EXEMPLE littérale dans
     le schéma JSON envoyé au LLM — biais d'ancrage probable sur une partie
     des 477 (impossible à distinguer du cas 1 a posteriori, d'où le
     réexamen LLM sur les 477 dans leur ensemble plutôt qu'un tri par
     origine).

IMPORTANT — 2026 n'est pas toujours une erreur : une entité "émergente"/
"transition" peut légitimement avoir démarré proche de 2026. Ce script ne
force donc PAS une nouvelle valeur — il demande au LLM de réexaminer
annee_debut à la lumière du contexte narratif déjà écrit (age_historique,
generation, etat_temporel, role_dans_scenario, tensions_narratives) et de
CONFIRMER 2026 si c'est cohérent, ou de proposer une année plus ancienne
si le profil narratif (résiduel/post-effondrement/mythifié/déclinant)
l'exige. Aucun autre champ n'est regénéré ni modifié.

COHÉRENCE VAULT (ajouté après retour de David, 7 août 2026) : 2026 est
littéralement aujourd'hui — une entité confirmée à cette date doit donc
être un prolongement plausible de ce qui existe réellement aujourd'hui, pas
une pure invention déconnectée. Le script injecte donc aussi
etat_du_monde_reel.md (même fichier que generate_instances.py/
create_entities_and_instances.py/enrich_minimal.py, à remplir manuellement)
et instruit le LLM à ne PAS confirmer 2026 si le profil narratif de la
fiche contredit clairement l'état réel actuel — il propose alors une année
plus lointaine où cette divergence devient plausible comme évolution
future.

USAGE — COMMENCER PAR ESTIMER LE COÛT AVANT UN RUN COMPLET
------------------------------------------------------------
    # 1. Test à vide, aucun appel LLM, juste pour voir combien de fiches sont concernées
    python3 fix_annee_debut_placeholder.py --scenario policy_reform --dry-run --limit 3

    # 2. Un scénario complet, en dry-run
    python3 fix_annee_debut_placeholder.py --scenario policy_reform --dry-run

    # 3. Un scénario complet, pour de vrai
    python3 fix_annee_debut_placeholder.py --scenario policy_reform

    # 4. Tous les scénarios
    python3 fix_annee_debut_placeholder.py --all

PRÉREQUIS
---------
    pip install pyyaml --break-system-packages
    À placer dans le même dossier que enrich_minimal.py / fix_alliances_
    oppositions.py (même dépendance à llm_client.py, même convention
    VAULT_ROOT = dossier parent).
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
# Configuration (mêmes conventions que fix_alliances_oppositions.py)
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
INSTANCES_DIR = VAULT_ROOT / "instances"
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
REPORT_PATH = NEED_ACTION_DIR / "fix_annee_debut_placeholder.md"
REGISTRE_PATH = GENERATOR_DIR / "registre_evenements.md"
ETAT_MONDE_PATH = GENERATOR_DIR / "etat_du_monde_reel.md"

SCENARIOS = [
    "breakdown",
    "fortress_world",
    "new_sustainability",
    "eco_communalism",
    "policy_reform",
    "reference",
]

PLACEHOLDER_VALUE = 2026
MAX_FIX_ATTEMPTS = 2
TRANSIENT_RETRIES = 3
TRANSIENT_BACKOFF_SECONDS = 5

# ---------------------------------------------------------------------------
# Chronologie réelle du scénario (ajouté après retour de David, 7 août 2026)
# ---------------------------------------------------------------------------
#
# Première version de ce script ne donnait au LLM aucun repère concret :
# juste des catégories qualitatives (age_historique/generation), sans année
# réelle à quoi les rattacher. Deuxième version appelait snapshot.py::
# build_signal_trajectory pour obtenir des jalons datés, mais ce calcul
# ignore les événements custom (evenements/ + event_instances/) et duplique
# un calcul déjà fait ailleurs. registre_evenements.md (généré et tenu à
# jour par inject_custom_events.py/inject_custom_signals.py à chaque
# injection) est la source la plus complète et la plus simple : un tableau
# déjà chronologique par scénario, signaux ET événements custom réunis. On
# le lit ici en lecture seule (jamais réécrit par ce script), avec le même
# format de parsing que get_registre_excerpt_for_variables() dans
# inject_custom_events.py/inject_custom_signals.py (colonnes : type | date
# | source | variable(s) | pilote | evenement_cle).

_registre_cache = None


def _read_registre_text():
    global _registre_cache
    if _registre_cache is None:
        _registre_cache = REGISTRE_PATH.read_text(encoding="utf-8") if REGISTRE_PATH.exists() else ""
    return _registre_cache


def _parse_registre_table(scen_body):
    """Même logique que parse_registre_table() dans inject_custom_events.py
    /inject_custom_signals.py — ne pas dupliquer un format de parsing
    différent qui divergerait silencieusement si le registre change.
    Détecte la ligne séparatrice par son contenu (uniquement '|', '-',
    espaces) plutôt que par un préfixe figé "|---" -- le registre réel
    l'écrit "| --------- | --------- | ..." (espace après le premier
    pipe), que startswith("|---") ne reconnaît pas."""
    rows = []
    table_started = False
    separator_re = re.compile(r"^\|[\s\-|]+$")
    for line in scen_body.split("\n"):
        if not table_started and line.startswith("|") and separator_re.match(line):
            table_started = True
            continue
        if table_started and line.startswith("|"):
            cols = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cols)
        elif table_started and not line.startswith("|"):
            break
    return rows


_timeline_cache = {}

_etat_monde_cache = None


def load_etat_monde_reel():
    """
    Charge etat_du_monde_reel.md (ajouté le 7 août 2026, audit point 1.2,
    suite au retour de David : le vault doit rester cohérent dans son
    ensemble entre le contenu existant et les nouvelles données — pas
    seulement au moment de la création, mais aussi au moment du
    réexamen/rattrapage). Même fichier partagé que generate_instances.py/
    create_entities_and_instances.py/enrich_minimal.py — voir
    generate_instances.py pour le commentaire complet. Mis en cache pour
    la durée du run.
    """
    global _etat_monde_cache
    if _etat_monde_cache is not None:
        return _etat_monde_cache
    if not ETAT_MONDE_PATH.exists():
        _etat_monde_cache = "(etat_du_monde_reel.md absent — aucun ancrage réel disponible, se fier uniquement au profil narratif choisi)"
        return _etat_monde_cache
    text = ETAT_MONDE_PATH.read_text(encoding="utf-8").strip()
    _etat_monde_cache = text if text else "(etat_du_monde_reel.md présent mais vide — pas encore rempli)"
    return _etat_monde_cache


def load_scenario_timeline_summary(scenario_slug):
    """
    Retourne un résumé texte des jalons du scénario extraits de
    registre_evenements.md, pour ancrage dans le prompt LLM. Mis en cache
    par scénario pour la durée du run.

    Retenus : tous les évènements custom (type=evenement — datés
    précisément, nommés, souvent les plus significatifs pour ancrer une
    entité) + les signaux pilotes (pilote=oui — structurants pour le
    scénario). Les signaux non-pilotes sont omis pour ne pas noyer le
    prompt (74 signaux uniques × 6 scénarios dans le registre complet).
    """
    if scenario_slug in _timeline_cache:
        return _timeline_cache[scenario_slug]

    registre_text = _read_registre_text()
    if not registre_text:
        _timeline_cache[scenario_slug] = "(registre_evenements.md introuvable ou vide)"
        return _timeline_cache[scenario_slug]

    parts = re.split(r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text)
    body = None
    for i in range(1, len(parts), 2):
        if parts[i] == scenario_slug:
            body = parts[i + 1]
            break

    if body is None:
        _timeline_cache[scenario_slug] = f"(aucune section '## {scenario_slug}' trouvée dans le registre)"
        return _timeline_cache[scenario_slug]

    lines = []
    for cols in _parse_registre_table(body):
        if len(cols) < 6:
            continue
        type_, date, source, variables, pilote, evenement_cle = cols[:6]
        if type_ == "evenement" or pilote.strip().lower() == "oui":
            lines.append(f"- [{type_}] {date} : {evenement_cle}")

    if not lines:
        summary = "(aucun jalon événement/signal-pilote trouvé pour ce scénario)"
    else:
        summary = "\n".join(lines[:40])  # plafond raisonnable, évite un prompt démesuré

    _timeline_cache[scenario_slug] = summary
    return summary


# ---------------------------------------------------------------------------
# Rapport (même esprit que reset_conflict_reports() — tronqué en tête de
# run réel, jamais en dry-run, pour ne refléter que le dernier run)
# ---------------------------------------------------------------------------

_report_reset_this_run = False


def reset_report() -> None:
    global _report_reset_this_run
    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = f"{datetime.now():%Y-%m-%d %H:%M}"
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# annee_debut réexaminées — état au run du {timestamp}\n\n")
    _report_reset_this_run = True


def append_report(scenario: str, lines: list) -> None:
    if not lines:
        return
    with open(REPORT_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n## {scenario}\n\n")
        for line in lines:
            f.write(f"- {line}\n")


# ---------------------------------------------------------------------------
# Parsing / patch frontmatter (même style que fix_alliances_oppositions.py)
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


def patch_annee_debut_frontmatter(raw_frontmatter_block, nouvelle_annee):
    """
    Remplace UNIQUEMENT la clé annee_debut dans le bloc frontmatter brut
    (texte), en laissant tous les autres champs strictement intacts —
    même logique que patch_alliances_oppositions_frontmatter() dans
    fix_alliances_oppositions.py, appliquée à un scalaire plutôt qu'à une
    liste. Ajoute aussi (ou met à jour) un marqueur de revue
    `annee_debut_verifiee: true` — voir write_annee_debut_patch() pour le
    correctif du 8 août 2026 que ce marqueur résout.
    """
    new_line = f"annee_debut: {nouvelle_annee}"
    pattern = re.compile(r"(?m)^annee_debut:.*$")
    if pattern.search(raw_frontmatter_block):
        result = pattern.sub(new_line, raw_frontmatter_block, count=1)
    else:
        result = raw_frontmatter_block.rstrip("\n") + f"\n{new_line}\n"

    marker_pattern = re.compile(r"(?m)^annee_debut_verifiee:.*$")
    marker_line = "annee_debut_verifiee: true"
    if marker_pattern.search(result):
        result = marker_pattern.sub(marker_line, result, count=1)
    else:
        result = result.rstrip("\n") + f"\n{marker_line}\n"
    return result


def write_annee_debut_patch(path, nouvelle_annee):
    """Applique le patch frontmatter et réécrit le fichier."""
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)", raw, re.DOTALL)
    if not m:
        raise ValueError(f"Frontmatter introuvable dans {path}")
    prefix, fm_block, marker, body = m.groups()
    new_fm_block = patch_annee_debut_frontmatter(fm_block, nouvelle_annee)
    new_raw = f"{prefix}{new_fm_block}{marker}{body}"
    path.write_text(new_raw, encoding="utf-8")


# ---------------------------------------------------------------------------
# Découverte des fiches concernées
# ---------------------------------------------------------------------------

def find_target_fiches(scenario, slug_filter=None):
    """Fiches officialise_enrichi avec annee_debut == 2026 (candidates
    placeholder — voir docstring du module pour le raisonnement).

    Ignore les fiches déjà marquées `annee_debut_verifiee: true` — bug
    corrigé le 8 août 2026 : une fiche CONFIRMÉE à 2026 (valeur légitime,
    pas un placeholder) n'était jamais réécrite sur disque, donc rien ne
    la distinguait d'une fiche jamais traitée. Chaque relance de `--all`
    retraitait indéfiniment les mêmes fiches déjà confirmées (35/38 sur
    un run réel), consommant des appels LLM pour rien. Le marqueur rend
    le script réellement idempotent, pas seulement en apparence.
    """
    result = []
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, body = parse_md(path)
        if fm.get("statut") != "officialise_enrichi":
            continue
        if slug_filter and fm.get("slug", path.stem) != slug_filter:
            continue
        if fm.get("annee_debut") != PLACEHOLDER_VALUE:
            continue
        if fm.get("annee_debut_verifiee") is True:
            continue
        result.append({"path": path, "fm": fm, "body": body})
    return result


# ---------------------------------------------------------------------------
# Prompt ciblé — annee_debut UNIQUEMENT
# ---------------------------------------------------------------------------

def build_targeted_prompt(fiche, scenario, timeline_summary):
    fm = fiche["fm"]
    slug = fm.get("slug", fiche["path"].stem)
    name = fm.get("name", slug)

    system_prompt = """Tu es l'assistant de worldbuilding du projet Ourrassol 2098.
Tu réexamines UNE seule donnée chronologique (annee_debut) d'une entité déjà
bien décrite, en te basant sur son profil narratif existant ET sur la
chronologie réelle du scénario.
Tes réponses sont UNIQUEMENT du JSON valide, sans aucun texte avant ou après.
Ne mets pas de backticks ni de balises markdown autour du JSON."""

    user_prompt = f"""TÂCHE : Réexaminer annee_debut pour cette entité, scénario {scenario}.

Cette fiche est déjà entièrement enrichie. Le contenu ci-dessous est fourni
comme CONTEXTE uniquement — ne le modifie pas, ne le régénère pas.

═══════════════════════════════════════════════════
FICHE (contexte, déjà rédigée)
═══════════════════════════════════════════════════
slug: {slug}
name: {name}
role_dans_scenario: {fm.get("role_dans_scenario", "")}
tensions_narratives: {fm.get("tensions_narratives", "")}
description_journalistique: {fm.get("description_journalistique", "")}
etat_temporel: {fm.get("etat_temporel", "")}
age_historique: {fm.get("age_historique", "")}
generation: {fm.get("generation", "")}
type_relation_dominante: {fm.get("type_relation_dominante", "")}
annee_debut actuelle : {PLACEHOLDER_VALUE} (valeur de création, possiblement
jamais retouchée — voir CONSIGNE ci-dessous)

═══════════════════════════════════════════════════
CHRONOLOGIE RÉELLE DU SCÉNARIO {scenario} (jalons datés majeurs/structurants)
═══════════════════════════════════════════════════
{timeline_summary}

═══════════════════════════════════════════════════
ÉTAT DU MONDE RÉEL (référence factuelle, PAS de la fiction)
═══════════════════════════════════════════════════
{load_etat_monde_reel()}

═══════════════════════════════════════════════════
CONSIGNE
═══════════════════════════════════════════════════
annee_debut={PLACEHOLDER_VALUE} peut être une vraie donnée narrative (une
entité "émergente"/"transition" démarre plausiblement proche de 2026) ou un
simple placeholder de création jamais retouché. Détermine, à partir du
profil ci-dessus (surtout age_historique/generation/etat_temporel), si
{PLACEHOLDER_VALUE} reste cohérent ou s'il faut le corriger :
- Si age_historique/generation évoquent un profil "émergent"/"transition"/
  "pré-crise" récent : {PLACEHOLDER_VALUE} est probablement correct, confirme-le.
- Si le profil est "résiduel"/"post-effondrement"/"mythifié"/"déclinant"/
  "marginal" (ancienneté implicite) : propose une année nettement antérieure
  à 2098, cohérente avec cette ancienneté narrative.
- Si le profil est "ascendant"/"dominant"/"mature" : une valeur intermédiaire
  est probablement plus cohérente que {PLACEHOLDER_VALUE}.
ATTENTION — CONFUSION À ÉVITER (ajoutée le 8 août 2026, après un échec réel
sur "union_africaine_resilience_reference", proposé à annee_debut=2002) :
annee_debut décrit TOUJOURS quand LA VERSION FICTIVE de cette entité,
telle que décrite dans CETTE fiche, est née dans le scénario — jamais la
date de fondation d'une organisation RÉELLE du monde d'aujourd'hui dont
le nom ou le rôle pourrait s'en inspirer (ex. si cette fiche évoque une
réforme/résilience/successeur d'une institution réelle existante, n'utilise
JAMAIS l'année de fondation de cette institution réelle — seule compte la
date où LA FICTION a commencé, obligatoirement entre 2026 et 2098). Si le
nom de l'entité rappelle une organisation réelle existante, ignore
complètement sa date de fondation réelle pour cette question.
PRIORITÉ ABSOLUE : si un jalon de la CHRONOLOGIE RÉELLE ci-dessus correspond
clairement à la naissance/l'origine de cette entité (ex. rupture, crise,
bascule mentionnée dans role_dans_scenario/tensions_narratives), utilise
l'année de CE jalon plutôt qu'une estimation libre — c'est la source la plus
fiable disponible, plus fiable que ton propre jugement qualitatif seul.
COHÉRENCE AVEC L'ÉTAT DU MONDE RÉEL (resserrée le 8 août 2026, après test
réel — la bande graduée jusqu'à 50 ans exigeait un ancrage réel même pour
des dates déjà bien justifiées par un jalon de scénario construit
sérieusement, ce qui créait une friction inutile sans gain de qualité
réel) :
  - 2026-2036 (0-10 ans) : DOIT être un prolongement direct et nommé d'un
    organisme, mouvement, technologie ou tendance CITÉ EXPLICITEMENT dans
    l'ÉTAT DU MONDE RÉEL ci-dessus — ancrage_reel OBLIGATOIRE.
  - 2036-2098 (10 ans et plus) : l'ÉTAT DU MONDE RÉEL sert de toile de
    fond, pas de contrainte directe — ancrage_reel OPTIONNEL. Si tu
    identifies un lien plausible même lointain, mentionne-le ; sinon,
    laisse le champ à null plutôt que d'en inventer un.
Si le role_dans_scenario/description_journalistique de cette fiche décrit
une origine qui contredit clairement l'état du monde réel (ex. une
institution réelle présentée comme réformée/dissoute alors qu'elle existe
toujours sous sa forme actuelle), NE confirme PAS une année dans la bande
0-10 ans — propose plutôt une année plus lointaine où cette divergence
devient plausible comme évolution future, et mentionne cette tension dans
ta justification.
Renseigne le champ "ancrage_reel" : une phrase courte et concrète nommant
explicitement l'organisme/mouvement/tendance réel(le) de l'ÉTAT DU MONDE
RÉEL dont cette entité descend ou s'inspire directement. CE CHAMP EST
OBLIGATOIRE si l'annee_debut retenue < 2036, MÊME si cette année vient d'un
jalon de la chronologie du scénario — laisse-le à null si l'année retenue
>= 2036 et qu'aucun lien réel pertinent ne te vient naturellement.
ATTENTION — CONFUSION FRÉQUENTE À ÉVITER : "ancrage_reel" doit citer un
élément de la section ÉTAT DU MONDE RÉEL (des faits du monde d'aujourd'hui,
2026, obtenus par recherche web) — JAMAIS un jalon de la CHRONOLOGIE RÉELLE
DU SCÉNARIO (qui, malgré son nom, est un événement FICTIF propre à ce
scénario, pas un fait du monde réel). Exemple à NE PAS FAIRE : si tu utilises
le jalon "Traité mondial sur l'eau (2038)" pour choisir l'année, ne mets
PAS "Traité mondial sur l'eau" dans ancrage_reel — ce jalon est fictif, pas
un ancrage réel. Cherche plutôt, dans l'ÉTAT DU MONDE RÉEL, un fait
authentique de 2026 en lien avec le rôle de cette entité (ex. une tension
institutionnelle réelle déjà documentée, une organisation existante, un
mouvement social en cours).
Ne change JAMAIS annee_debut sans justification tirée du profil ci-dessus,
d'un jalon de la chronologie, ou d'une incohérence avec l'état du monde réel
— ce n'est pas un champ à randomiser.

Réponds en JSON uniquement :
{{
  "annee_debut": <entier entre 2026 et 2098>,
  "ancrage_reel": "<phrase courte nommant l'élément réel dont cette entité descend, OBLIGATOIRE si annee_debut < 2036, sinon null/optionnel>",
  "justification": "1 phrase expliquant pourquoi cette valeur (jalon utilisé si applicable, ou pourquoi {PLACEHOLDER_VALUE} est confirmé)"
}}
"""
    return system_prompt, user_prompt


def call_llm_json(system, user_content, max_tokens=400):
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


def call_llm_json_resilient(system, user_content, max_tokens=400):
    """Absorbe les pannes transitoires de l'API (503, timeout...) avec un
    backoff — voir fix_alliances_oppositions.py::call_llm_json_resilient
    pour le même mécanisme."""
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


def _normalize_for_matching(text):
    """Normalise un texte pour la comparaison n-gram : minuscules, retire
    la ponctuation, espaces multiples réduits à un seul."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_registre_leakage(ancrage_reel_text, min_shingle=6):
    """
    Détecte si ancrage_reel recopie (même reformulé légèrement) un jalon de
    la CHRONOLOGIE RÉELLE DU SCÉNARIO (fictive, malgré son nom) plutôt que
    de citer un fait authentique de l'ÉTAT DU MONDE RÉEL. Ajouté le 8 août
    2026 : la consigne en prose seule ne suffisait pas — testé en
    conditions réelles par David sur la fiche AMMC, le LLM continuait de
    recycler le nom du jalon fictif ("Traité mondial sur l'eau et la
    sécurité hydrique") sous une justification habillée pour paraître
    réelle, malgré un avertissement explicite dans le prompt. Garde-fou
    mécanique : recherche de séquences de 6 mots consécutifs identiques
    entre ancrage_reel et le registre complet — un tel chevauchement est
    hautement improbable par hasard, donc presque toujours révélateur
    d'un jalon fictif recopié plutôt que d'un fait réel indépendamment
    formulé. Seuil relevé de 4 à 6 mots le 8 août 2026 après un faux
    positif réel : "de l'agence internationale" (4 mots) matchait à la
    fois la vraie AIE (Agence Internationale de l'Énergie, citée
    légitimement depuis l'ÉTAT DU MONDE RÉEL) et un jalon fictif
    totalement différent ("Agence Internationale de la Fusion", 2045,
    registre new_sustainability) — 6 mots réduit ce risque de collision
    sur des tournures administratives génériques.

    Renvoie la séquence détectée (pour message d'erreur explicite), ou
    None si aucun chevauchement suspect.
    """
    # Comparaison par TUPLES DE MOTS (pas de sous-chaîne de caractères) —
    # correctif du 8 août 2026 : la version précédente (recherche de
    # sous-chaîne sur texte joint par espaces) produisait un faux positif
    # sur la vraie AIE ("...internationale de l'Énergie") à cause d'un
    # chevauchement de CARACTÈRES avec un jalon fictif sans rapport
    # ("...internationale de la Fusion") — "de l" est un préfixe littéral
    # de "de la", donc matchait à tort même si "l" et "la" sont deux mots
    # différents. La comparaison par tuples élimine structurellement ce
    # type de faux positif : deux séquences ne matchent que si TOUS leurs
    # mots sont identiques un par un, jamais par chevauchement partiel.
    registre_words = _normalize_for_matching(_read_registre_text()).split()
    registre_shingles = set()
    for i in range(len(registre_words) - min_shingle + 1):
        registre_shingles.add(tuple(registre_words[i:i + min_shingle]))

    ancrage_words = _normalize_for_matching(ancrage_reel_text).split()
    for i in range(len(ancrage_words) - min_shingle + 1):
        shingle = tuple(ancrage_words[i:i + min_shingle])
        if shingle in registre_shingles:
            return " ".join(shingle)
    return None


def validate_targeted(data):
    errors = []
    val = data.get("annee_debut")
    annee_debut_val = None
    try:
        annee_debut_val = int(val)
        if not (2026 <= annee_debut_val <= 2098):
            if annee_debut_val < 2026:
                errors.append(
                    f"annee_debut hors plage [2026-2098] : {val!r} — "
                    f"probable confusion avec la date de fondation réelle "
                    f"d'une organisation existante dont cette entité "
                    f"s'inspire (ex. Union Africaine réelle fondée en "
                    f"2002) ; annee_debut doit décrire l'origine de LA "
                    f"VERSION FICTIVE de ce scénario, pas de l'organisation "
                    f"réelle — recalcule une année entre 2026 et 2098"
                )
            else:
                errors.append(f"annee_debut hors plage [2026-2098] : {val!r}")
    except (TypeError, ValueError):
        errors.append(f"annee_debut invalide (doit être un entier) : {val!r}")

    # Traçabilité, resserrée le 8 août 2026 après test réel (demande de
    # David) : obligatoire seulement dans les 10 prochaines années
    # (annee_debut < 2036) — au-delà, un jalon de scénario déjà construit
    # sérieusement (via signal_to_state) suffit à justifier la date sans
    # exiger un lien réel explicite en plus. Le contrôle anti-recyclage du
    # registre s'applique quand même si le champ est rempli, même de façon
    # optionnelle au-delà de 2036.
    if annee_debut_val is not None:
        ancrage = (data.get("ancrage_reel") or "").strip()
        if annee_debut_val < 2036 and not ancrage:
            errors.append(
                f"ancrage_reel manquant ou vide alors que annee_debut "
                f"({annee_debut_val}) < 2036 — traçabilité avec l'état du "
                f"monde réel requise dans les 10 prochaines années"
            )
        elif ancrage:
            # Contrôle qualité appliqué dès que le champ est rempli, même
            # optionnellement (au-delà de 2036) — s'il est renseigné, autant
            # qu'il ne recycle pas un jalon fictif du registre.
            leaked = detect_registre_leakage(ancrage)
            if leaked:
                errors.append(
                    f"ancrage_reel semble recopier un jalon fictif du "
                    f"registre du scénario plutôt qu'un fait authentique "
                    f"de l'état du monde réel (séquence détectée : "
                    f"{leaked!r}) — cite un élément vérifiable de 2026, "
                    f"pas un événement fictif du scénario"
                )

    return errors


# ---------------------------------------------------------------------------
# Traitement d'une fiche
# ---------------------------------------------------------------------------

def process_fiche(fiche, scenario, timeline_summary, dry_run):
    fm = fiche["fm"]
    slug = fm.get("slug", fiche["path"].stem)
    print(f"  → {slug}")

    system_prompt, user_prompt = build_targeted_prompt(fiche, scenario, timeline_summary)

    try:
        data = call_llm_json_resilient(system_prompt, user_prompt)
    except Exception as e:
        print(f"    [ÉCHEC] {e}")
        return False, None, [str(e)], None

    errors = validate_targeted(data)
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
Corrige et retourne le JSON complet corrigé.
"""
        try:
            data = call_llm_json_resilient(system_prompt, fix_prompt)
        except Exception as e:
            errors = [str(e)]
            break
        errors = validate_targeted(data)

    if errors:
        print(f"    [ÉCHEC PERSISTANT] {len(errors)} erreur(s) :")
        for e in errors:
            print(f"      - {e}")
        return False, data, errors, None

    nouvelle_annee = int(data["annee_debut"])
    justification = data.get("justification", "")
    ancrage_reel = (data.get("ancrage_reel") or "").strip()
    inchangee = nouvelle_annee == PLACEHOLDER_VALUE

    ancrage_suffixe = f" [ancrage réel : {ancrage_reel}]" if ancrage_reel else ""
    if inchangee:
        print(f"    ✓ confirmé à {PLACEHOLDER_VALUE} — {justification}{ancrage_suffixe}")
    else:
        print(f"    ✓ corrigé : {PLACEHOLDER_VALUE} → {nouvelle_annee} — {justification}{ancrage_suffixe}")

    if not dry_run:
        # Correctif du 8 août 2026 : on écrit désormais dans TOUS les cas
        # de succès, pas seulement quand l'année change — write_annee_
        # debut_patch() pose le marqueur annee_debut_verifiee même quand
        # nouvelle_annee == PLACEHOLDER_VALUE (confirmation), ce qui est
        # le seul moyen de rendre cette confirmation visible à find_
        # target_fiches() lors d'un futur run.
        write_annee_debut_patch(fiche["path"], nouvelle_annee)

    report_line = (
        f"**{slug}** : {'confirmé ' + str(PLACEHOLDER_VALUE) if inchangee else f'{PLACEHOLDER_VALUE} → {nouvelle_annee}'} "
        f"— {justification}{ancrage_suffixe}"
    )
    return True, data, [], report_line


# ---------------------------------------------------------------------------
# Boucle par scénario + CLI
# ---------------------------------------------------------------------------

def run_scenario(scenario, slug_filter, dry_run, limit):
    print(f"\n{'═' * 60}")
    print(f"SCÉNARIO : {scenario.upper()}")
    print(f"{'═' * 60}")

    fiches = find_target_fiches(scenario, slug_filter)
    if not fiches:
        print(f"  (aucune fiche concernée — pas de annee_debut={PLACEHOLDER_VALUE} sur officialise_enrichi)")
        return 0, 0, 0

    total_disponibles = len(fiches)
    if limit:
        fiches = fiches[:limit]
        print(f"  {total_disponibles} fiche(s) concernée(s) — traitement limité à {len(fiches)} (--limit)")
    else:
        print(f"  {len(fiches)} fiche(s) concernée(s)")

    n_ok, n_fail, n_corrigees = 0, 0, 0
    report_lines = []
    timeline_summary = load_scenario_timeline_summary(scenario)
    for fiche in fiches:
        slug = fiche["fm"].get("slug", fiche["path"].stem)
        try:
            success, data, errors, report_line = process_fiche(fiche, scenario, timeline_summary, dry_run)
        except Exception as e:
            print(f"    [ÉCHEC INATTENDU] {slug} : {e}")
            success = False
            errors = [str(e)]
            report_line = None
        if success:
            n_ok += 1
            if report_line:
                report_lines.append(report_line)
                if "→" in report_line:
                    n_corrigees += 1
        else:
            n_fail += 1
            # Correctif du 8 août 2026 : avant, un échec persistant ne
            # laissait AUCUNE trace dans le rapport (seulement en console,
            # perdue si le terminal n'est pas gardé) — David a dû demander
            # de recoller la sortie console pour identifier 2 échecs après
            # un run réel. Les échecs sont désormais tracés au même titre
            # que les succès, avec le détail des erreurs de validation.
            errors_txt = "; ".join(errors) if errors else "raison inconnue"
            report_lines.append(f"**{slug}** : ❌ ÉCHEC PERSISTANT — {errors_txt}")

    if not dry_run:
        append_report(scenario, report_lines)

    return n_ok, n_fail, n_corrigees


def main():
    parser = argparse.ArgumentParser(
        description=f"Réexamine annee_debut sur les fiches officialise_enrichi bloquées à {PLACEHOLDER_VALUE}, sans toucher aux autres champs."
    )
    parser.add_argument("--scenario", help="Scénario à traiter (ex: policy_reform)")
    parser.add_argument("--all", action="store_true", help="Traite tous les scénarios")
    parser.add_argument("--slug", help="Traite uniquement une fiche par son slug")
    parser.add_argument("--dry-run", action="store_true", help="N'écrit rien sur disque")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limite le nombre de fiches traitées PAR SCÉNARIO — à utiliser en premier pour estimer le coût réel avant un run complet",
    )
    args = parser.parse_args()

    if not args.scenario and not args.all:
        parser.error("Spécifier --scenario NOM ou --all")

    scenarios_to_run = SCENARIOS if args.all else [args.scenario]

    print("=" * 60)
    print("OURRASSOL 2098 — Réexamen annee_debut (placeholder 2026)")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)")

    if not args.dry_run:
        reset_report()

    total_ok, total_fail, total_corrigees = 0, 0, 0
    for scenario in scenarios_to_run:
        if scenario not in SCENARIOS:
            print(f"[WARN] Scénario inconnu : {scenario} — ignoré")
            continue
        n_ok, n_fail, n_corrigees = run_scenario(scenario, args.slug, args.dry_run, args.limit)
        total_ok += n_ok
        total_fail += n_fail
        total_corrigees += n_corrigees

    print(f"\n{'═' * 60}")
    print("RÉSUMÉ")
    print(f"{'═' * 60}")
    print(f"  Traitées   : {total_ok}")
    print(f"  Corrigées  : {total_corrigees}")
    print(f"  Confirmées : {total_ok - total_corrigees}")
    print(f"  Échecs     : {total_fail}")
    if total_ok and not args.dry_run:
        print(f"  → détail dans {REPORT_PATH}")


if __name__ == "__main__":
    main()
