import yaml
from pathlib import Path

entite_path = Path("entites/reseau_des_cartographes_des_zones_grises.md")
text = entite_path.read_text(encoding="utf-8")
parts = text.split("---", 2)
fm = yaml.safe_load(parts[1])

slug = fm.get("slug")
scenarios = fm.get("scenarios_instances")

print("slug lu             :", repr(slug))
print("scenarios_instances :", repr(scenarios))
print()

for sc in scenarios:
    attendu = f"instances/{slug}_{sc}.md"
    print(f"  scénario {sc!r} -> chemin attendu : {attendu!r}")
    print(f"    existe (Path.exists()) : {Path(attendu).exists()}")

print()
print("Fichiers réels dans instances/ contenant 'reseau_des_cartographes':")
for p in sorted(Path("instances").glob("*reseau_des_cartographes*")):
    print(" ", repr(p.name))
