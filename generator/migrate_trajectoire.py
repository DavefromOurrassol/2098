#!/usr/bin/env python3
"""
migrate_trajectoire.py — Ourrassol 2098
=========================================

Migre les fiches instances existantes de l'ancien schéma
(`etat_temporel` + `age_historique`) vers le nouveau champ unique
`trajectoire` (axe narratif continu) + `est_clandestin` (booléen
indépendant), suite au chantier de fusion décidé le 9 août 2026.

CONTEXTE
--------
`etat_temporel` (6 valeurs) et `age_historique` (8 valeurs) se
chevauchaient conceptuellement (une entité "transformée" a aussi
nécessairement un "âge") et laissaient possible des incohérences
jamais détectées mécaniquement (ex. `age_historique: ascendant` +
`etat_temporel: transformé` sur une même fiche — trouvé en session le
8 août sur `zones_extractivistes_corridors_eco_communalism`). Fusionnés
en un seul axe :

    émergent → marginal → ascendant → dominant → mature → déclinant
      → résiduel → transformé → disparu → historique → mythifié

`clandestin` sort de l'axe, devient le booléen indépendant
`est_clandestin` (une entité peut désormais être n'importe quelle
position sur l'axe ET clandestine en même temps — impossible avant).

RÈGLES DE MIGRATION (actées avec David le 9 août 2026)
--------------------------------------------------------
Priorité : age_historique explicite et valide > défaut actif/clandestin.

  1. etat_temporel == "transformé" ou "disparu"
     → trajectoire = etat_temporel (inchangé, la position terminale
       prime toujours sur un age_historique éventuellement renseigné —
       décision explicite : l'état ACTUEL de la fiche compte, pas son
       historique, qui reste de toute façon raconté en prose dans le
       corps de la fiche).
     → est_clandestin = False
     → PAS de marqueur trajectoire_migree_par_defaut (ce n'est pas un
       défaut, c'est déjà la valeur réelle du champ).

  2. etat_temporel in ("historique", "mythifié")
     → trajectoire = etat_temporel (inchangé). 0 fiche concernée sur le
       vault au 9 août 2026, cas géré par prudence si la situation change.
     → est_clandestin = False, pas de marqueur (même raisonnement que 1).

  3. etat_temporel in ("actif", "clandestin") ET age_historique déjà
     renseigné avec une valeur reconnue (les 8 valeurs de l'ancien
     age_historique, qui recouvrent 8 des 11 valeurs du nouvel axe)
     → trajectoire = age_historique (mapping 1:1, ce n'est pas un
       défaut, la position reflète un choix déjà fait par le LLM).
     → est_clandestin = (etat_temporel == "clandestin")
     → PAS de marqueur trajectoire_migree_par_defaut.

  4. etat_temporel == "actif" ET age_historique absent/vide/invalide
     (le cas très majoritaire — 657 fiches sur le vault au 9 août 2026)
     → trajectoire = "mature"
     → est_clandestin = False
     → marqueur trajectoire_migree_par_defaut: true (pour pouvoir
       repérer et retravailler ces fiches plus tard sans tout rescanner
       à l'oeil — même logique que annee_debut_verifiee).

  5. etat_temporel == "clandestin" ET age_historique absent/vide/invalide
     (23 fiches au 9 août 2026)
     → trajectoire = "mature"
     → est_clandestin = True
     → marqueur trajectoire_migree_par_defaut: true (même raisonnement
       que le cas 4 — traité comme les "actif" par défaut, décision
       explicite de David).

Dans tous les cas : `etat_temporel` et `age_historique` sont SUPPRIMÉS
du frontmatter une fois la migration faite (décision actée : suppression
immédiate, pas de cohabitation temporaire — le vault est versionné via
Git, un rollback reste possible sans avoir besoin de champs dupliqués
qui sèmeraient la confusion sur lequel fait foi).

IDEMPOTENCE
-----------
Une fiche portant déjà une clé `trajectoire` dans son frontmatter est
considérée migrée et ignorée — comme pour `fix_annee_debut_
placeholder.py`/`annee_debut_verifiee`, chaque relance ne retraite que
ce qui reste à faire.

USAGE
-----
    # 1. Test à vide sur un petit lot, pour vérifier les 3 cas de la
    #    table de migration avant un run complet
    python3 migrate_trajectoire.py --scenario policy_reform --dry-run --limit 3

    # 2. Un scénario complet, en dry-run
    python3 migrate_trajectoire.py --scenario policy_reform --dry-run

    # 3. Un scénario complet, pour de vrai
    python3 migrate_trajectoire.py --scenario policy_reform

    # 4. Tous les scénarios
    python3 migrate_trajectoire.py --all

Aucun appel LLM — migration purement mécanique, donc pas de coût API et
pas de round de test progressif nécessaire comme sur les scripts qui
appellent un LLM ; le dry-run reste recommandé pour vérifier la
répartition des cas avant d'écrire sur disque.

PRÉREQUIS
---------
    pip install pyyaml --break-system-packages
    À placer dans le même dossier que instance_generation_common.py
    (réutilise VALID_TRAJECTOIRE depuis ce module — une seule source de
    vérité, pas de troisième liste dupliquée).
"""

import argparse
import re
from pathlib import Path

import yaml

from instance_generation_common import VALID_TRAJECTOIRE

# ---------------------------------------------------------------------------
# Configuration (mêmes conventions que fix_annee_debut_placeholder.py)
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
INSTANCES_DIR = VAULT_ROOT / "instances"
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
REPORT_PATH = NEED_ACTION_DIR / "migrate_trajectoire_report.md"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

# Les 8 valeurs de l'ancien age_historique — sous-ensemble de
# VALID_TRAJECTOIRE (qui en compte 11, avec transformé/disparu/historique
# en plus, propres à l'ancien etat_temporel).
OLD_AGE_HISTORIQUE_VALUES = {
    "émergent", "marginal", "ascendant", "dominant",
    "mature", "déclinant", "résiduel", "mythifié",
}

TERMINAL_UNCHANGED = {"transformé", "disparu", "historique", "mythifié"}


# ---------------------------------------------------------------------------
# Parsing / patch frontmatter (mêmes conventions que les autres scripts)
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


def decide_migration(fm):
    """Applique la table de migration (voir docstring du module) à un
    frontmatter déjà chargé. Retourne (trajectoire, est_clandestin,
    marqueur_defaut: bool, cas: str) — cas est juste pour le rapport.
    """
    etat = (fm.get("etat_temporel") or "").strip()
    age = (fm.get("age_historique") or "").strip()

    if etat in TERMINAL_UNCHANGED:
        return etat, False, False, f"terminal_inchange({etat})"

    if etat in ("actif", "clandestin"):
        est_clandestin = (etat == "clandestin")
        if age in OLD_AGE_HISTORIQUE_VALUES:
            return age, est_clandestin, False, f"age_historique_explicite({age})"
        return "mature", est_clandestin, True, f"defaut_mature(etat={etat or '(absent)'})"

    # etat_temporel absent ou valeur inconnue — cas résiduel non prévu par
    # la table (0 attendu sur le vault au 9 août 2026, mais on ne veut pas
    # planter dessus). Traité comme le cas par défaut le plus prudent :
    # mature + marqueur, jamais clandestin par défaut (on ne l'invente pas
    # sans info), à charge pour needs_review de le signaler pour relecture.
    return "mature", False, True, f"cas_non_prevu(etat={etat or '(absent)'!r}, age={age or '(absent)'!r})"


def patch_trajectoire_frontmatter(raw_frontmatter_block, trajectoire, est_clandestin, marqueur_defaut):
    """Remplace/ajoute trajectoire + est_clandestin, retire etat_temporel
    et age_historique, et pose (ou ne pose pas) le marqueur
    trajectoire_migree_par_defaut — sur le bloc frontmatter BRUT (texte),
    en laissant tous les autres champs strictement intacts. Même logique
    que patch_annee_debut_frontmatter() dans fix_annee_debut_
    placeholder.py, étendue à plusieurs champs à la fois.
    """
    result = raw_frontmatter_block

    # Retire les deux anciens champs (suppression immédiate, décidée le
    # 9 août 2026 — le vault est versionné, pas besoin de cohabitation).
    result = re.sub(r"(?m)^etat_temporel:.*\n?", "", result)
    result = re.sub(r"(?m)^age_historique:.*\n?", "", result)

    # trajectoire
    traj_line = f"trajectoire: {trajectoire}"
    traj_pattern = re.compile(r"(?m)^trajectoire:.*$")
    if traj_pattern.search(result):
        result = traj_pattern.sub(traj_line, result, count=1)
    else:
        result = result.rstrip("\n") + f"\n{traj_line}\n"

    # est_clandestin
    clandestin_line = f"est_clandestin: {str(est_clandestin).lower()}"
    clandestin_pattern = re.compile(r"(?m)^est_clandestin:.*$")
    if clandestin_pattern.search(result):
        result = clandestin_pattern.sub(clandestin_line, result, count=1)
    else:
        result = result.rstrip("\n") + f"\n{clandestin_line}\n"

    # marqueur — posé UNIQUEMENT si migration par défaut, jamais sinon
    # (une fiche migrée depuis un age_historique explicite ou déjà
    # terminale ne doit pas porter ce marqueur — ce n'est pas un défaut).
    marker_pattern = re.compile(r"(?m)^trajectoire_migree_par_defaut:.*$")
    if marqueur_defaut:
        marker_line = "trajectoire_migree_par_defaut: true"
        if marker_pattern.search(result):
            result = marker_pattern.sub(marker_line, result, count=1)
        else:
            result = result.rstrip("\n") + f"\n{marker_line}\n"
    else:
        # Au cas où une fiche aurait déjà ce marqueur d'un run précédent
        # incohérent — on ne le laisse pas traîner si ce run-ci détermine
        # que ce n'est pas (ou plus) un cas par défaut.
        result = marker_pattern.sub("", result)

    return result


def write_trajectoire_patch(path, trajectoire, est_clandestin, marqueur_defaut):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)", raw, re.DOTALL)
    if not m:
        raise ValueError(f"Frontmatter introuvable dans {path}")
    prefix, fm_block, marker, body = m.groups()
    new_fm_block = patch_trajectoire_frontmatter(fm_block, trajectoire, est_clandestin, marqueur_defaut)
    new_raw = f"{prefix}{new_fm_block}{marker}{body}"
    path.write_text(new_raw, encoding="utf-8")


# ---------------------------------------------------------------------------
# Découverte des fiches concernées
# ---------------------------------------------------------------------------

def find_target_fiches(scenario, slug_filter=None):
    """Fiches instances du scénario donné, pas encore migrées (idempotence
    via l'absence de la clé trajectoire)."""
    result = []
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, body = parse_md(path)
        if not fm:
            continue
        if slug_filter and fm.get("slug", path.stem) != slug_filter:
            continue
        if "trajectoire" in fm:
            continue  # déjà migrée
        result.append({"path": path, "fm": fm, "body": body})
    return result


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

def reset_report():
    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    REPORT_PATH.write_text(
        f"# Migration trajectoire — rapport du dernier run\n\n"
        f"Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n",
        encoding="utf-8",
    )


def append_report(scenario, lines):
    with REPORT_PATH.open("a", encoding="utf-8") as f:
        f.write(f"\n## {scenario}\n\n")
        for line in lines:
            f.write(line + "\n")


# ---------------------------------------------------------------------------
# Traitement d'un scénario
# ---------------------------------------------------------------------------

def run_scenario(scenario, slug_filter, dry_run, limit):
    fiches = find_target_fiches(scenario, slug_filter)
    if limit:
        fiches = fiches[:limit]

    if not fiches:
        print(f"  {scenario} : rien à migrer (0 fiche restante)")
        return 0, {}

    print(f"  {scenario} : {len(fiches)} fiche(s) à migrer")
    report_lines = []
    cas_stats = {}

    for fiche in fiches:
        slug = fiche["fm"].get("slug", fiche["path"].stem)
        trajectoire, est_clandestin, marqueur_defaut, cas = decide_migration(fiche["fm"])
        cas_stats[cas.split("(")[0]] = cas_stats.get(cas.split("(")[0], 0) + 1

        marker_txt = " [défaut]" if marqueur_defaut else ""
        clandestin_txt = " [clandestin]" if est_clandestin else ""
        print(f"    → {slug} : trajectoire={trajectoire}{clandestin_txt}{marker_txt} ({cas})")
        report_lines.append(
            f"- **{slug}** : trajectoire=`{trajectoire}`, est_clandestin=`{str(est_clandestin).lower()}`"
            f"{' , trajectoire_migree_par_defaut=`true`' if marqueur_defaut else ''} — cas : {cas}"
        )

        if not dry_run:
            write_trajectoire_patch(fiche["path"], trajectoire, est_clandestin, marqueur_defaut)

    if not dry_run:
        append_report(scenario, report_lines)

    return len(fiches), cas_stats


def main():
    parser = argparse.ArgumentParser(
        description="Migre etat_temporel+age_historique vers trajectoire+est_clandestin (chantier du 9 août 2026)."
    )
    parser.add_argument("--scenario", help="Scénario à traiter (ex: policy_reform)")
    parser.add_argument("--all", action="store_true", help="Traite tous les scénarios")
    parser.add_argument("--slug", help="Traite uniquement une fiche par son slug")
    parser.add_argument("--dry-run", action="store_true", help="N'écrit rien sur disque")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limite le nombre de fiches traitées PAR SCÉNARIO — à utiliser en premier pour vérifier la répartition des cas avant un run complet",
    )
    args = parser.parse_args()

    if not args.scenario and not args.all:
        parser.error("Spécifier --scenario NOM ou --all")

    scenarios_to_run = SCENARIOS if args.all else [args.scenario]

    print("=" * 60)
    print("OURRASSOL 2098 — Migration trajectoire")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)")

    if not args.dry_run:
        reset_report()

    total_migrees = 0
    total_cas_stats = {}
    for scenario in scenarios_to_run:
        if scenario not in SCENARIOS:
            print(f"[WARN] Scénario inconnu : {scenario} — ignoré")
            continue
        n, cas_stats = run_scenario(scenario, args.slug, args.dry_run, args.limit)
        total_migrees += n
        for cas, count in cas_stats.items():
            total_cas_stats[cas] = total_cas_stats.get(cas, 0) + count

    print(f"\n{'═' * 60}")
    print("RÉSUMÉ")
    print(f"{'═' * 60}")
    print(f"  Migrées : {total_migrees}")
    for cas, count in sorted(total_cas_stats.items(), key=lambda x: -x[1]):
        print(f"    - {cas} : {count}")
    if total_migrees and not args.dry_run:
        print(f"  → détail dans {REPORT_PATH}")


if __name__ == "__main__":
    main()
