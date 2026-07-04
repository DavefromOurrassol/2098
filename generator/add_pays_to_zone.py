#!/usr/bin/env python3
"""
add_pays_to_zone.py — Ourrassol 2098
=====================================

Ajoute un ou plusieurs pays à l'origine_reelle d'une zone existante, dans une
fiche geographie/{scenario}.md. Ne crée jamais de zone, ne modifie que
l'origine_reelle de la zone ciblée. Sauvegarde .bak avant écriture.

Usage typique : rattacher un pays à sa vraie zone N1 quand il n'était présent
que dans une sous-zone (cf. check_zones_coherence.py).

USAGE
-----
    python3 add_pays_to_zone.py --scenario reference --zone union_africaine_resilience \\
        --pays Mali Niger Tchad Soudan
"""

import argparse
import shutil
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", required=True, help="Scénario cible (ex. reference)")
    parser.add_argument("--zone", required=True, help="Slug de la zone cible (doit déjà exister)")
    parser.add_argument("--pays", required=True, nargs="+", help="Un ou plusieurs pays à ajouter")
    parser.add_argument("--dry-run", action="store_true", help="Affiche ce qui serait fait, n'écrit rien")
    args = parser.parse_args()

    geo_file = GEO_DIR / f"{args.scenario}.md"
    if not geo_file.exists():
        print(f"✗ Fiche introuvable : {geo_file}")
        sys.exit(1)

    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---")
    if len(parts) < 3:
        print(f"✗ Format inattendu (pas de frontmatter)")
        sys.exit(1)

    fm = yaml.safe_load(parts[1]) or {}
    zones = fm.get("zones") or []

    target = next((z for z in zones if isinstance(z, dict) and z.get("slug") == args.zone), None)
    if target is None:
        print(f"✗ Zone '{args.zone}' introuvable dans {geo_file.name}")
        sys.exit(1)

    niveau = target.get("niveau", 1)
    if niveau != 1:
        print(f"⚠ Attention : '{args.zone}' est niveau {niveau}, pas niveau 1.")
        reponse = input("Continuer quand même ? [o/N] ")
        if reponse.lower() != "o":
            print("Annulé.")
            sys.exit(0)

    origine = target.get("origine_reelle") or []
    existing = {o.get("entite", "").lower().strip() for o in origine if isinstance(o, dict)}

    ajoutes, deja_presents = [], []
    for pays in args.pays:
        if pays.lower().strip() in existing:
            deja_presents.append(pays)
        else:
            ajoutes.append(pays)
            origine.append({"entite": pays, "type_entite": "pays", "portion": None})

    print(f"Zone cible : {args.zone} ({target.get('nom', '')}) — niveau {niveau}")
    if deja_presents:
        print(f"  ~ Déjà présents (ignorés) : {', '.join(deja_presents)}")
    if ajoutes:
        print(f"  + À ajouter : {', '.join(ajoutes)}")
    else:
        print("  Rien à faire — tous les pays étaient déjà présents.")
        sys.exit(0)

    if args.dry_run:
        print("\n(--dry-run : aucune écriture effectuée)")
        sys.exit(0)

    target["origine_reelle"] = origine

    # Backup avant écriture
    backup_path = geo_file.with_suffix(".md.bak")
    shutil.copy2(geo_file, backup_path)
    print(f"  Backup : {backup_path.name}")

    # Un seul yaml.dump sur le frontmatter complet — voir complete_geographie_coverage.py
    # pour l'historique de ce choix (évite la corruption d'indentation).
    fm_ordered = {k: v for k, v in fm.items() if k != "zones"}
    fm_ordered["zones"] = zones
    fm_str = yaml.dump(
        fm_ordered, allow_unicode=True, sort_keys=False,
        default_flow_style=False, indent=2,
    ).rstrip()
    body = "---".join(parts[2:])
    content = f"---\n{fm_str}\n---{body}"
    geo_file.write_text(content, encoding="utf-8")

    print(f"  ✓ Écrit dans {geo_file.name}")


if __name__ == "__main__":
    main()
