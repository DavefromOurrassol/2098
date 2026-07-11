"""Retire les entrées placeholder (fallback sur échec API) de journaux.yaml — à lancer depuis generator/"""
import yaml

with open("journaux.yaml", encoding="utf-8") as f:
    journaux = yaml.safe_load(f) or {}

removed = []
for scenario, lignes in journaux.items():
    for ligne, data in lignes.items():
        zones = data.get("zones", {})
        to_remove = [
            slug for slug, z in zones.items()
            if z.get("nom", "").startswith("Édition ") and not z.get("ton") and not z.get("langue_style")
        ]
        for slug in to_remove:
            del zones[slug]
            removed.append(f"{scenario}/{ligne}/{slug}")

print(f"{len(removed)} entrée(s) placeholder retirée(s) :")
for r in removed:
    print(" -", r)

with open("journaux.yaml", "w", encoding="utf-8") as f:
    yaml.dump(journaux, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
print("\njournaux.yaml réécrit sans les placeholders.")
