"""
Supprime interzone_corridor_test pour repartir de zéro.

Usage, depuis gui/ :
    python3 supprimer_interzone_test.py --dry-run
    python3 supprimer_interzone_test.py --apply
"""

import argparse
import json
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

try:
    resultat = repo.supprimer_zone_n1("fortress_world", "interzone_corridor_test", dry_run=args.dry_run)
except ZoneRepositoryError as e:
    print("Erreur :", e)
    raise SystemExit(1)

print(json.dumps(resultat, indent=2, ensure_ascii=False))

if args.dry_run:
    print("\n[dry-run] Rien n'a été modifié. Relance avec --apply pour supprimer réellement.")
else:
    print("\nZone supprimée (.bak automatique créé).")
