#!/usr/bin/env python3
"""
regenerate_zones_pays.py — Ourrassol 2098
===========================================

Régénère gui/zones_pays.json à partir des VRAIES fiches geographie/{scenario}.md
(source de vérité), au lieu de faire confiance à l'état existant du fichier.

Pourquoi : get_missing_pays() dans complete_geographie_coverage.py se base sur
zones_pays.json pour savoir quels pays traiter. Si ce fichier contient une
valeur non-null obsolète pour un pays (héritée d'une génération antérieure,
désynchronisée de la fiche réelle), ce pays est silencieusement ignoré par
--review, même s'il n'a en réalité aucune zone dans la fiche. Ce script
élimine ce risque en reconstruisant zones_pays.json depuis zéro à partir des
fiches, avec la même logique de correspondance tolérante aux variantes
narratives que check_zones_coherence.py (ALIASES).

Ne modifie jamais les fiches geographie/*.md — seulement zones_pays.json.
Backup automatique (.json.bak) avant écriture.

USAGE
-----
    python3 regenerate_zones_pays.py --dry-run     # aperçu, aucune écriture
    python3 regenerate_zones_pays.py                # régénère pour de vrai
"""

import argparse
import json
import re
import shutil
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
GUI_DIR = VAULT_ROOT / "gui"
ZONES_PAYS = GUI_DIR / "zones_pays.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

# Même liste que check_zones_coherence.py — garder synchronisées si l'une évolue.
ALIASES = {
    "états-unis": ["états-unis d'amérique"],
    "arctique": ["arctique international"],
}


def _pays_present(pays_norm: str, entites: list):
    """Retourne (slug, niveau) de la première zone correspondante, ou None."""
    variantes_connues = set(ALIASES.get(pays_norm, []))
    for slug, niveau, entites_zone in entites:
        for e in entites_zone:
            e_clean = re.sub(r"\([^)]*\)", "", e).strip().lower()
            if e_clean in variantes_connues:
                return slug, niveau
            tokens = [e_clean] + [t.strip() for t in re.split(r"[,/;]", e_clean)]
            if pays_norm in tokens:
                return slug, niveau
    return None


def build_scenario_mapping(scenario: str, pays_liste: list) -> dict:
    """Retourne {pays: slug_ou_None} pour un scénario, en préférant une
    zone niveau 1 si le pays est mentionné à plusieurs niveaux."""
    geo_file = GEO_DIR / f"{scenario}.md"
    fm = yaml.safe_load(geo_file.read_text(encoding="utf-8").split("---")[1]) or {}
    zones = fm.get("zones") or []

    zones_avec_entites = []
    for z in zones:
        if not isinstance(z, dict):
            continue
        entites = [
            o.get("entite", "") for o in (z.get("origine_reelle") or [])
            if isinstance(o, dict) and o.get("entite")
        ]
        if entites:
            zones_avec_entites.append((z.get("slug", ""), z.get("niveau", 1), entites))

    resultat = {}
    for pays in pays_liste:
        pays_norm = pays.lower().strip()
        best = None
        for slug, niveau, entites in zones_avec_entites:
            if _pays_present(pays_norm, [(slug, niveau, entites)]):
                if best is None or (niveau == 1 and best[1] != 1):
                    best = (slug, niveau)
        resultat[pays] = best[0] if best else None

    return resultat


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Affiche un résumé sans écrire")
    args = parser.parse_args()

    if not ZONES_PAYS.exists():
        print(f"✗ {ZONES_PAYS} introuvable — impossible de récupérer pays_liste.")
        return

    ancien = json.loads(ZONES_PAYS.read_text(encoding="utf-8"))
    pays_liste = ancien.get("pays_liste", [])
    if not pays_liste:
        print("✗ pays_liste vide ou absent de zones_pays.json — abandon.")
        return

    nouveau = {"pays_liste": pays_liste}
    changements_par_scenario = {}

    for scenario in SCENARIOS:
        geo_file = GEO_DIR / f"{scenario}.md"
        if not geo_file.exists():
            print(f"⚠ {scenario} : fiche introuvable, ignoré")
            continue

        mapping = build_scenario_mapping(scenario, pays_liste)
        nouveau[scenario] = mapping

        ancien_scenario = ancien.get(scenario, {})
        diffs = []
        for pays, zone in mapping.items():
            avant = ancien_scenario.get(pays, "—absent—")
            if avant != zone:
                diffs.append((pays, avant, zone))
        changements_par_scenario[scenario] = diffs

    print("=" * 60)
    print("  Régénération zones_pays.json depuis les fiches")
    print("=" * 60)
    total_changements = 0
    for scenario, diffs in changements_par_scenario.items():
        print(f"\n=== {scenario} ({len(diffs)} changement(s)) ===")
        for pays, avant, apres in diffs[:20]:
            print(f"  {pays}: {avant!r} → {apres!r}")
        if len(diffs) > 20:
            print(f"  ... et {len(diffs) - 20} autre(s)")
        total_changements += len(diffs)

    print(f"\nTotal : {total_changements} changement(s) sur {len(SCENARIOS)} scénarios")

    if args.dry_run:
        print("\n(--dry-run : aucune écriture effectuée)")
        return

    backup_path = ZONES_PAYS.with_suffix(".json.bak")
    shutil.copy2(ZONES_PAYS, backup_path)
    print(f"\nBackup : {backup_path}")

    ZONES_PAYS.write_text(json.dumps(nouveau, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ zones_pays.json régénéré : {ZONES_PAYS}")


if __name__ == "__main__":
    main()
