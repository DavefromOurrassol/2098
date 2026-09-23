"""
Corrige le doublon Turquie (présente dans l'origine_reelle de zone_euro_sud
ET de anatolie_forteresse_eurasiatique). Retire la Turquie de zone_euro_sud,
la garde uniquement dans anatolie_forteresse_eurasiatique, et s'assure que
zones_pays.json est cohérent.

Usage, depuis gui/ :
    python3 fix_doublon_turquie.py --dry-run
    python3 fix_doublon_turquie.py --apply
"""

import argparse
import json
import sys
from pathlib import Path

from zone_repository import ZoneRepository, ZoneRepositoryError

GUI_DIR = Path(__file__).parent
config = json.loads((GUI_DIR / "config.json").read_text(encoding="utf-8"))
vault_root = Path(config["vault_root"])

ap = argparse.ArgumentParser()
grp = ap.add_mutually_exclusive_group(required=True)
grp.add_argument("--dry-run", action="store_true")
grp.add_argument("--apply", action="store_true")
args = ap.parse_args()

repo = ZoneRepository(vault_root, GUI_DIR)

print("=== Zones portant actuellement la Turquie ===")
zones = repo.zones_portant_un_pays("fortress_world", "Turquie")
for z in zones:
    print(f"  - {z['slug']} ({z['nom']})")

try:
    resultat = repo.retirer_pays_des_autres_zones(
        "fortress_world", "Turquie", "anatolie_forteresse_eurasiatique",
        dry_run=args.dry_run
    )
except ZoneRepositoryError as e:
    print(f"\nErreur : {e}")
    sys.exit(1)

print(f"\n=== Résultat ({'dry-run' if args.dry_run else 'appliqué'}) ===")
print(json.dumps(resultat, indent=2, ensure_ascii=False))

if args.dry_run:
    print("\n[dry-run] Rien n'a été modifié. Relance avec --apply pour corriger réellement.")
else:
    fichiers = (["geographie/fortress_world.md"] if resultat.get("zones_nettoyees") else []) \
        + (["zones_pays.json"] if resultat.get("zones_pays_json_corrige") else [])
    print("\nFichiers modifiés (avec .bak automatique) : "
          + (", ".join(fichiers) if fichiers else "aucun (rien n'avait besoin de changer)"))
