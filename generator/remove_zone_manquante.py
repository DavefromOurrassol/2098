import yaml
from pathlib import Path

path = Path("/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/documentation/need_action/zones_manquantes.yaml")

data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
entries = data.get("zones_manquantes", [])

avant = len(entries)
entries = [
    e for e in entries
    if not (e.get("pays") == "Arctique" and e.get("scenario") == "policy_reform")
]
apres = len(entries)

data["zones_manquantes"] = entries

path.write_text(
    yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
    encoding="utf-8",
)

print(f"Entrées avant : {avant}, après : {apres}")
