"""
Liste tous les overlays du scénario, groupés par pays -- et signale les cas
où un même pays a PLUSIEURS overlays enregistrés (cause probable des
"masques fantômes" : si deux overlays existent pour le même pays dans la
même zone, l'interface actuelle n'affiche qu'un seul bouton "supprimer" à la
fois -- supprimer celui-là laisse l'autre invisible tant que le panneau n'a
pas été rouvert).

Usage, depuis gui/ :
    python3 lister_overlays.py [scenario]
"""

import json
import sys
from pathlib import Path

from zone_repository import ZoneRepository

GUI_DIR = Path(__file__).parent
config = json.loads((GUI_DIR / "config.json").read_text(encoding="utf-8"))
vault_root = Path(config["vault_root"])

scenario = sys.argv[1] if len(sys.argv) > 1 else "fortress_world"

repo = ZoneRepository(vault_root, GUI_DIR)
fc = repo.overlays_get(scenario)
features = fc.get("features", [])

print(f"{len(features)} overlays au total pour {scenario}.\n")

par_pays = {}
par_pays_zone = {}
for f in features:
    p = f["properties"]
    par_pays.setdefault(p.get("pays"), []).append(p)
    par_pays_zone.setdefault((p.get("pays"), p.get("zone_slug")), []).append(p)

for pays, entries in sorted(par_pays.items(), key=lambda kv: kv[0] or ""):
    print(pays)
    for e in entries:
        portion = (e.get("portion_source") or "")[:60]
        doublon = " ⚠ MÊME PAYS+ZONE EN DOUBLE" if len(par_pays_zone[(pays, e.get("zone_slug"))]) > 1 else ""
        print(f"   - id={e['id']}  zone={e['zone_slug']}  portion={portion}{doublon}")

vrais_doublons = {k: v for k, v in par_pays_zone.items() if len(v) > 1}
print("\nVrais doublons (même pays ET même zone en double) :", list(vrais_doublons.keys()) or "aucun")
print("(un pays avec plusieurs overlays pour des zones DIFFÉRENTES -- ex. un pays partagé -- "
      "n'est PAS un doublon, c'est normal.)")
