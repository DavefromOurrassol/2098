"""Diagnostic ponctuel : journaux.yaml vs geographie/{scenario}.md — à lancer depuis generator/"""
import re, yaml

SCENARIOS = ["breakdown", "fortress_world", "new_sustainability", "eco_communalism", "policy_reform", "reference"]
LIGNES = ["pro_pouvoir", "opposition"]

def get_zones_n1(scenario):
    with open(f"../geographie/{scenario}.md", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return set()
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    fm = yaml.safe_load(fm_str) or {}
    return {z["slug"] for z in fm.get("zones", []) if z.get("niveau") == 1}

with open("journaux.yaml", encoding="utf-8") as f:
    journaux = yaml.safe_load(f) or {}

total_manquants = 0
total_orphelins = 0
for scenario in SCENARIOS:
    zones_reelles = get_zones_n1(scenario)
    for ligne in LIGNES:
        zones_journaux = set(journaux.get(scenario, {}).get(ligne, {}).get("zones", {}).keys())
        manquants = zones_reelles - zones_journaux
        orphelins = zones_journaux - zones_reelles
        if manquants or orphelins:
            print(f"=== {scenario} / {ligne} ===")
            if manquants:
                print(f"  ⚠ {len(manquants)} zone(s) N1 sans journal : {sorted(manquants)}")
                total_manquants += len(manquants)
            if orphelins:
                print(f"  ⚠ {len(orphelins)} entrée(s) orpheline(s) dans journaux.yaml : {sorted(orphelins)}")
                total_orphelins += len(orphelins)

print()
if total_manquants == 0 and total_orphelins == 0:
    print("✓ journaux.yaml parfaitement cohérent avec la géographie actuelle des 6 scénarios.")
else:
    print(f"Total : {total_manquants} manquant(s), {total_orphelins} orphelin(s).")
