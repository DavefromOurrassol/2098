#!/usr/bin/env python3
"""
fix_annee_fin_manquant.py — Ourrassol 2098
=============================================

Chantier `annee_fin` (voir BACKLOG_MASTER_9_AOUT.md, Partie 1 point 1).
Corrige rétroactivement les fiches instances dont la `trajectoire` est
terminale (`transformé`/`disparu`/`historique`/`mythifié`) mais dont
`annee_fin` est absente — 28 fiches confirmées sur le vault au 9 août
2026 (audit_etat_temporel_fin.py, taux d'incohérence 93,3% sur cette
sous-population).

CONTEXTE
--------
Diagnostiqué le 8 août (question de David en clôture du chantier
`annee_debut`) : le schéma JSON envoyé au LLM à la création montre
"annee_fin": null comme exemple, sans lien structurel avec la position
narrative de l'entité. Aucune validation ne vérifiait la cohérence entre
les deux jusqu'au correctif C4 de `validate.py` (9 août, chantier
`trajectoire`) — qui détecte le problème mais ne le corrige pas. Ce
script fait la correction.

DIFFÉRENCE AVEC fix_annee_debut_placeholder.py (modèle repris) : pas
besoin d'ancrage sur etat_du_monde_reel.md ici — annee_debut, proche de
2026, devait rester plausible par rapport au monde réel d'aujourd'hui.
annee_fin décrit la fin d'une trajectoire ENTIÈREMENT FICTIVE, à
n'importe quel horizon jusqu'à 2098 — seule la chronologie interne du
scénario (registre_evenements.md) et le contexte narratif déjà écrit sur
la fiche comptent, pas de contrainte de continuité avec le présent réel.

RÈGLE DE PRIORITÉ (décidée avec David le 9 août 2026, même principe que
annee_debut) :
  1. Si un jalon du registre du scénario correspond clairement à la
     transformation/disparition de cette entité (rupture, absorption,
     effondrement mentionné dans tensions_narratives/description_
     journalistique), utiliser l'année de ce jalon.
  2. Sinon, estimer à partir du seul contexte narratif déjà écrit sur la
     fiche — cohérent avec `trajectoire` :
       - "transformé" : l'entité a évolué vers autre chose — annee_fin
         marque ce point de bascule, peut être suivi d'une continuité
         sous une autre forme (pas la fin de l'histoire du scénario).
       - "disparu"/"historique"/"mythifié" : fin plus définitive de
         l'existence active de l'entité sous cette forme.

CONTRAINTE : annee_debut < annee_fin ≤ 2098.

IDEMPOTENCE : plus simple qu'avec annee_debut (pas de valeur placeholder
ambiguë à distinguer d'une valeur confirmée) — une fiche avec annee_fin
déjà renseignée n'est simplement plus candidate. Aucun marqueur
supplémentaire nécessaire.

USAGE
-----
    # 1. Test à vide, aucun appel LLM, juste pour voir combien de fiches
    python3 fix_annee_fin_manquant.py --scenario breakdown --dry-run --limit 3

    # 2. Un scénario complet, en dry-run
    python3 fix_annee_fin_manquant.py --scenario breakdown --dry-run

    # 3. Un scénario complet, pour de vrai
    python3 fix_annee_fin_manquant.py --scenario breakdown

    # 4. Tous les scénarios
    python3 fix_annee_fin_manquant.py --all

PRÉREQUIS
---------
    pip install pyyaml --break-system-packages
    À placer dans le même dossier qu'instance_generation_common.py
    (réutilise parse_md, load_scenario_timeline_summary, call_claude_json
    — une seule source de vérité, pas de troisième copie de ces
    fonctions comme cela avait failli se reproduire ailleurs).
"""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

from instance_generation_common import (
    parse_md,
    load_scenario_timeline_summary,
    get_client,
    call_claude_json,
    TRAJECTOIRE_INACTIVES,
)

# ---------------------------------------------------------------------------
# Configuration (mêmes conventions que fix_annee_debut_placeholder.py)
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
INSTANCES_DIR = VAULT_ROOT / "instances"
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
REPORT_PATH = NEED_ACTION_DIR / "fix_annee_fin_manquant.md"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

MAX_FIX_ATTEMPTS = 2
HORIZON_NARRATIF = 2098


# ---------------------------------------------------------------------------
# Découverte des fiches concernées
# ---------------------------------------------------------------------------

def find_target_fiches(scenario, slug_filter=None):
    """Fiches à trajectoire terminale sans annee_fin renseignée."""
    result = []
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, body = parse_md(path)
        if not fm:
            continue
        if slug_filter and fm.get("slug", path.stem) != slug_filter:
            continue
        trajectoire = fm.get("trajectoire", "")
        if trajectoire not in TRAJECTOIRE_INACTIVES:
            continue
        annee_fin = fm.get("annee_fin")
        if annee_fin not in (None, ""):
            continue  # déjà renseignée, idempotence naturelle
        result.append({"path": path, "fm": fm, "body": body})
    return result


# ---------------------------------------------------------------------------
# Prompt ciblé — annee_fin UNIQUEMENT
# ---------------------------------------------------------------------------

def build_targeted_prompt(fiche, scenario, timeline_summary):
    fm = fiche["fm"]
    slug = fm.get("slug", fiche["path"].stem)
    name = fm.get("name", slug)
    trajectoire = fm.get("trajectoire", "")
    annee_debut = fm.get("annee_debut", "?")

    system_prompt = """Tu es l'assistant de worldbuilding du projet Ourrassol 2098.
Tu réexamines UNE seule donnée chronologique (annee_fin) d'une entité déjà
bien décrite, en te basant sur son profil narratif existant ET sur la
chronologie réelle du scénario.
Tes réponses sont UNIQUEMENT du JSON valide, sans aucun texte avant ou après.
Ne mets pas de backticks ni de balises markdown autour du JSON."""

    user_prompt = f"""TÂCHE : Déterminer annee_fin pour cette entité, scénario {scenario}.

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
trajectoire: {trajectoire}
annee_debut: {annee_debut}
annee_fin actuelle : absente (à déterminer)

═══════════════════════════════════════════════════
CHRONOLOGIE RÉELLE DU SCÉNARIO {scenario} (jalons datés majeurs/structurants)
═══════════════════════════════════════════════════
{timeline_summary}

═══════════════════════════════════════════════════
CONSIGNE
═══════════════════════════════════════════════════
Cette entité a une trajectoire "{trajectoire}", ce qui implique
normalement une fin narrative à un moment donné entre annee_debut
({annee_debut}) et {HORIZON_NARRATIF} :
- "transformé" : l'entité a évolué vers autre chose — annee_fin marque ce
  point de bascule (pas nécessairement la fin de son influence, juste la
  fin de CETTE forme précise décrite dans la fiche).
- "disparu"/"historique"/"mythifié" : fin plus définitive de l'existence
  active de l'entité sous cette forme.

PRIORITÉ ABSOLUE : si un jalon de la CHRONOLOGIE RÉELLE ci-dessus
correspond clairement à la transformation/disparition de cette entité
(rupture, absorption, effondrement cohérent avec tensions_narratives/
description_journalistique), utilise l'année de CE jalon plutôt qu'une
estimation libre — c'est la source la plus fiable disponible.

Sinon, estime une année cohérente avec le contexte narratif déjà écrit
sur la fiche (ancienneté implicite, tensions évoquées, rythme du
scénario) — ni artificiellement proche d'annee_debut (une transformation
immédiate est rarement plausible sauf indication contraire explicite),
ni automatiquement collée à {HORIZON_NARRATIF} par défaut.

CONTRAINTE STRICTE : annee_fin DOIT être un entier strictement supérieur
à annee_debut ({annee_debut}) et inférieur ou égal à {HORIZON_NARRATIF}.
{HORIZON_NARRATIF} est la fin de l'horizon narratif du projet tout entier
— aucune date, même une transformation qui semblerait logiquement se
poursuivre au-delà, ne peut être racontée après cette borne. Si ton
raisonnement te pousse au-delà de {HORIZON_NARRATIF} (ex. "N années après
sa création" calculé trop loin, ou une crise qui semble culminer plus
tard), choisis {HORIZON_NARRATIF} lui-même plutôt que de dépasser — une
transformation encore en cours ou tout juste achevée à l'horizon du
projet est une réponse parfaitement valide, pas un compromis dégradé.

Réponds en JSON uniquement :
{{
  "annee_fin": <entier, {annee_debut} < annee_fin <= {HORIZON_NARRATIF} — jamais au-delà, plafonne à {HORIZON_NARRATIF} si besoin>,
  "justification": "<1-2 lignes expliquant le choix — jalon du registre utilisé, ou raisonnement narratif>"
}}"""
    return system_prompt, user_prompt


def validate_response(data, annee_debut):
    issues = []
    try:
        annee_fin = int(data.get("annee_fin"))
    except (TypeError, ValueError):
        issues.append(f"annee_fin invalide ou manquante : {data.get('annee_fin')!r}")
        return issues, None

    if not (annee_debut < annee_fin <= HORIZON_NARRATIF):
        issues.append(
            f"annee_fin={annee_fin} hors plage valide "
            f"({annee_debut} < annee_fin <= {HORIZON_NARRATIF})"
        )
    return issues, annee_fin


# ---------------------------------------------------------------------------
# Patch frontmatter (même style que fix_annee_debut_placeholder.py)
# ---------------------------------------------------------------------------

def patch_annee_fin_frontmatter(raw_frontmatter_block, nouvelle_annee):
    """Remplace/ajoute UNIQUEMENT la clé annee_fin, laisse tout le reste
    strictement intact."""
    new_line = f"annee_fin: {nouvelle_annee}"
    pattern = re.compile(r"(?m)^annee_fin:.*$")
    if pattern.search(raw_frontmatter_block):
        return pattern.sub(new_line, raw_frontmatter_block, count=1)
    return raw_frontmatter_block.rstrip("\n") + f"\n{new_line}\n"


def write_annee_fin_patch(path, nouvelle_annee):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)", raw, re.DOTALL)
    if not m:
        raise ValueError(f"Frontmatter introuvable dans {path}")
    prefix, fm_block, marker, body = m.groups()
    new_fm_block = patch_annee_fin_frontmatter(fm_block, nouvelle_annee)
    path.write_text(f"{prefix}{new_fm_block}{marker}{body}", encoding="utf-8")


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

def reset_report():
    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        f"# annee_fin corrigées — état au run du {datetime.now():%Y-%m-%d %H:%M}\n\n",
        encoding="utf-8",
    )


def append_report(scenario, lines):
    if not lines:
        return
    with REPORT_PATH.open("a", encoding="utf-8") as f:
        f.write(f"\n## {scenario}\n\n")
        for line in lines:
            f.write(f"- {line}\n")


# ---------------------------------------------------------------------------
# Traitement d'une fiche / d'un scénario
# ---------------------------------------------------------------------------

def process_fiche(client, fiche, scenario, dry_run):
    fm = fiche["fm"]
    slug = fm.get("slug", fiche["path"].stem)
    annee_debut = fm.get("annee_debut")
    try:
        annee_debut = int(annee_debut)
    except (TypeError, ValueError):
        return {"status": "error", "slug": slug,
                "error": f"annee_debut absente/invalide ({annee_debut!r}) — corriger le chantier annee_debut d'abord"}

    timeline_summary = load_scenario_timeline_summary(scenario)
    system_prompt, user_prompt = build_targeted_prompt(fiche, scenario, timeline_summary)

    last_issues = []
    last_data = None
    for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
        try:
            data = call_claude_json(client, system_prompt, user_prompt)
        except Exception as e:
            last_issues = [str(e)]
            time.sleep(3)
            continue

        issues, annee_fin = validate_response(data, annee_debut)
        if not issues:
            justification = data.get("justification", "")
            if not dry_run:
                write_annee_fin_patch(fiche["path"], annee_fin)
            return {
                "status": "fixed", "slug": slug, "annee_fin": annee_fin,
                "justification": justification, "attempts": attempt,
            }
        last_issues = issues
        last_data = data

    # Filet de sécurité (ajouté le 9 août 2026, après un cas réel —
    # consortium_helios_new_sustainability — où le LLM proposait 2101 de
    # façon parfaitement stable sur plusieurs tentatives et deux runs
    # distincts, malgré une consigne de plafonnement explicite dans le
    # prompt : ancrage narratif spécifique à la fiche, pas un aléa que de
    # nouveaux tirages LLM résoudraient. Plafonne automatiquement à
    # HORIZON_NARRATIF UNIQUEMENT si le seul problème est un dépassement
    # (jamais si annee_fin <= annee_debut ou valeur non numérique — ces
    # cas restent des échecs à examiner manuellement, un dépassement de
    # l'horizon n'a rien d'un signal d'incohérence de fond, juste une
    # question de degré).
    if last_data is not None:
        try:
            proposed = int(last_data.get("annee_fin"))
            if proposed > HORIZON_NARRATIF and annee_debut < HORIZON_NARRATIF:
                justification = (
                    f"{last_data.get('justification', '')} [Plafonné automatiquement à "
                    f"{HORIZON_NARRATIF} — le LLM proposait {proposed} de façon stable sur "
                    f"{MAX_FIX_ATTEMPTS} tentative(s), dépassant l'horizon narratif du projet.]"
                )
                if not dry_run:
                    write_annee_fin_patch(fiche["path"], HORIZON_NARRATIF)
                return {
                    "status": "fixed", "slug": slug, "annee_fin": HORIZON_NARRATIF,
                    "justification": justification, "attempts": MAX_FIX_ATTEMPTS,
                    "clamped": True,
                }
        except (TypeError, ValueError):
            pass

    return {"status": "error", "slug": slug, "error": "; ".join(last_issues)}


def run_scenario(scenario, slug_filter, dry_run, limit):
    fiches = find_target_fiches(scenario, slug_filter)
    if limit:
        fiches = fiches[:limit]

    if not fiches:
        print(f"  {scenario} : rien à corriger (0 fiche restante)")
        return 0, 0

    print(f"  {scenario} : {len(fiches)} fiche(s) à traiter")
    client = get_client()
    report_lines = []
    n_ok, n_fail = 0, 0

    for fiche in fiches:
        slug = fiche["fm"].get("slug", fiche["path"].stem)
        print(f"    → {slug}...", end=" ", flush=True)
        outcome = process_fiche(client, fiche, scenario, dry_run)

        if outcome["status"] == "fixed":
            n_ok += 1
            clamp_flag = " [PLAFONNÉ AUTO]" if outcome.get("clamped") else ""
            print(f"✓ annee_fin={outcome['annee_fin']}{clamp_flag}")
            print(f"       └─ {outcome['justification']}")
            report_lines.append(
                f"**{slug}** : annee_fin=`{outcome['annee_fin']}` — {outcome['justification']}"
            )
        else:
            n_fail += 1
            print(f"✗ ({outcome['error']})")
            report_lines.append(f"**{slug}** : ❌ ÉCHEC — {outcome['error']}")

    if not dry_run:
        append_report(scenario, report_lines)

    return n_ok, n_fail


def main():
    parser = argparse.ArgumentParser(
        description="Corrige rétroactivement annee_fin sur les fiches à trajectoire terminale sans date de fin."
    )
    parser.add_argument("--scenario", help="Scénario à traiter (ex: breakdown)")
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
    print("OURRASSOL 2098 — Correction annee_fin manquante")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)")

    if not args.dry_run:
        reset_report()

    total_ok, total_fail = 0, 0
    for scenario in scenarios_to_run:
        if scenario not in SCENARIOS:
            print(f"[WARN] Scénario inconnu : {scenario} — ignoré")
            continue
        n_ok, n_fail = run_scenario(scenario, args.slug, args.dry_run, args.limit)
        total_ok += n_ok
        total_fail += n_fail

    print(f"\n{'═' * 60}")
    print("RÉSUMÉ")
    print(f"{'═' * 60}")
    print(f"  Corrigées : {total_ok}")
    print(f"  Échecs    : {total_fail}")
    if total_ok and not args.dry_run:
        print(f"  → détail dans {REPORT_PATH}")


if __name__ == "__main__":
    main()
