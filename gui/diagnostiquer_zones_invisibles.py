"""
Cherche les zones niveau 1 qui ne peuvent RIEN afficher sur la carte
actuellement : aucun de leurs pays (origine_reelle) ne gagne l'arbitrage du
calque de base (origine_reelle_index privilégie la première zone trouvée
dans le fichier en cas de pays partagé), ET aucun overlay dessiné pour
compenser. Ces zones existent dans les données mais restent invisibles tant
que personne n'y dessine un tracé.

Usage, depuis gui/ :
    python3 diagnostiquer_zones_invisibles.py [scenario]
"""

import json
import sys
from pathlib import Path

from zone_repository import ZoneRepository, _normalise_pays

GUI_DIR = Path(__file__).parent
config = json.loads((GUI_DIR / "config.json").read_text(encoding="utf-8"))
vault_root = Path(config["vault_root"])

scenario = sys.argv[1] if len(sys.argv) > 1 else "fortress_world"

repo = ZoneRepository(vault_root, GUI_DIR)
zones = repo.load_all_zones(scenario)
n1 = [z for z in zones if int(z.get("niveau", 1)) == 1 and z.get("slug")]

index_frais = repo.origine_reelle_index(scenario)  # pays_normalise -> slug gagnant
fc = repo.overlays_get(scenario)
zones_avec_overlay = {f["properties"].get("zone_slug") for f in fc.get("features", [])}

invisibles = []
for z in n1:
    slug = z.get("slug")
    if slug in zones_avec_overlay:
        continue  # au moins un overlay -- pas invisible
    pays_zone = [o.get("entite") for o in (z.get("origine_reelle") or []) if isinstance(o, dict) and o.get("entite")]
    if not pays_zone:
        continue  # zone sans aucun pays -- hors sujet ici
    gagne_au_moins_un = any(index_frais.get(_normalise_pays(p)) == slug for p in pays_zone)
    if not gagne_au_moins_un:
        invisibles.append({"slug": slug, "nom": z.get("nom"), "pays": pays_zone})

if not invisibles:
    print("Aucune zone invisible trouvée -- toutes les zones N1 ont au moins un overlay "
          "ou gagnent l'arbitrage pour au moins un de leurs pays.")
else:
    print(f"{len(invisibles)} zone(s) N1 actuellement invisible(s) sur la carte :\n")
    for z in invisibles:
        print(f"- {z['nom']} ({z['slug']})")
        print(f"    pays revendiqués : {', '.join(z['pays'])}")
        print(f"    tous perdent l'arbitrage face à une autre zone, et aucun overlay n'existe pour compenser.")
