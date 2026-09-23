"""
Applique une personnalisation couleur/motif sur une zone N1, pour tester
l'héritage vers les sous-zones. Écrit réellement (.bak automatique avant).

Usage, depuis gui/ :
    python3 test_personnaliser.py fortress_world espace_nordique_arctique "#336699"
"""

import json
import sys
from pathlib import Path

from zone_repository import ZoneRepository, ZoneRepositoryError

GUI_DIR = Path(__file__).parent
config = json.loads((GUI_DIR / "config.json").read_text(encoding="utf-8"))
vault_root = Path(config["vault_root"])

if len(sys.argv) < 4:
    print("Usage: python3 test_personnaliser.py <scenario> <slug_zone_n1> <couleur_hex>")
    sys.exit(1)

scenario, slug, couleur = sys.argv[1], sys.argv[2], sys.argv[3]

repo = ZoneRepository(vault_root, GUI_DIR)
try:
    resultat = repo.personnaliser(scenario, slug, couleur=couleur)
    print("OK ->", resultat)
    print(f"\n(.bak créé : geographie/{scenario}.md.bak -- pour annuler, "
          f"remplace le .md par le .bak)")
except ZoneRepositoryError as e:
    print("Erreur :", e)
