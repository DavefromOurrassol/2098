"""
Cherche les entrées origine_reelle qui ont un texte `portion` (décrivant une
couverture PARTIELLE) mais AUCUN masque dessiné actuellement pour ce
pays/zone -- signe probable d'un texte laissé orphelin par une suppression
de masque antérieure à l'ajout du nettoyage automatique (12 sept 2026).

Signale en plus, séparément, les cas où le pays est de toute façon affecté
en ENTIER à cette zone via zones_pays.json (comme la Belgique) -- la
contradiction la plus nette : le texte dit "partiel", les données disent
"le pays entier".

N'écrit rien -- diagnostic seul. Une fois la liste passée en revue, dis à
Claude lesquelles effacer (ou lance le nettoyage groupé s'il en fournit un).

Usage, depuis gui/ :
    python3 diagnostiquer_portions_orphelines.py [scenario]
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
zones = repo.load_all_zones(scenario)
fc = repo.overlays_get(scenario)
overlays_par_zone_pays = {
    (f["properties"].get("zone_slug"), f["properties"].get("pays"))
    for f in fc.get("features", [])
}

zp = repo._load_zones_pays()
sc = zp.get(scenario, {})

trouvees = []
for z in zones:
    slug = z.get("slug")
    for o in (z.get("origine_reelle") or []):
        if not isinstance(o, dict) or not o.get("portion"):
            continue
        pays = o.get("entite")
        a_un_masque = (slug, pays) in overlays_par_zone_pays
        if a_un_masque:
            continue
        pays_entier_ici = sc.get(pays) == slug
        trouvees.append({
            "zone": slug, "pays": pays, "portion": o["portion"],
            "pays_entier_dans_cette_zone": pays_entier_ici,
        })

print(f"{len(trouvees)} texte(s) portion sans masque correspondant.\n")
for t in trouvees:
    marque = "  ⚠ pays ENTIER assigné ici, texte dit pourtant 'partiel'" if t["pays_entier_dans_cette_zone"] else ""
    print(f"- {t['pays']} ({t['zone']}){marque}")
    print(f"    {t['portion'][:100]}")
