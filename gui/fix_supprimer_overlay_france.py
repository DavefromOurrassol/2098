"""
Supprime directement l'overlay France/zone_euro_sud (id
d1c7e23a-b405-4872-aaac-86fe55352dc1) qui n'a pas été retiré via l'interface,
pour raison inconnue. Contourne le bouton, appelle le repository directement.

Usage, depuis gui/ :
    python3 fix_supprimer_overlay_france.py
"""

import json
from pathlib import Path

from zone_repository import ZoneRepository, ZoneRepositoryError

GUI_DIR = Path(__file__).parent
config = json.loads((GUI_DIR / "config.json").read_text(encoding="utf-8"))
vault_root = Path(config["vault_root"])

repo = ZoneRepository(vault_root, GUI_DIR)

OVERLAY_ID = "d1c7e23a-b405-4872-aaac-86fe55352dc1"

try:
    resultat = repo.overlay_supprimer("fortress_world", OVERLAY_ID)
    print("OK ->", resultat)
except ZoneRepositoryError as e:
    print("Erreur :", e)
