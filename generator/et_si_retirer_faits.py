#!/usr/bin/env python3
"""
et_si_retirer_faits.py — 23 octobre 2026 (S27.1).

Retire d'une entrée adoptée de evenements_custom/queue.yaml (avant injection)
les faits imposés et les acteurs liés à des propositions écartées : l'entrée
est préparée à partir de toute la lecture IA, et sauter une proposition à
l'étape ④ ne la retire pas du récit que l'injection fera écrire.

Usage (depuis la racine du vault) :
    python3 generator/et_si_retirer_faits.py --id pacte_tabriz_2058 --slugs a_breakdown,b_breakdown
    python3 generator/et_si_retirer_faits.py ... --apply      # sauvegarde queue.yaml.bak_retirer
"""

import argparse
import shutil
import sys
from pathlib import Path

import yaml

QUEUE = Path(__file__).resolve().parent.parent / "evenements_custom" / "queue.yaml"


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--id", required=True)
    a.add_argument("--slugs", required=True, help="slugs séparés par des virgules")
    a.add_argument("--apply", action="store_true")
    args = a.parse_args()
    retirer = {s.strip() for s in args.slugs.split(",") if s.strip()}

    data = yaml.safe_load(QUEUE.read_text(encoding="utf-8")) or {}
    entrees = [e for e in data.get("queue") or [] if isinstance(e, dict) and e.get("id") == args.id]
    if len(entrees) != 1:
        print(f"✗ {len(entrees)} entrée(s) « {args.id} » dans la file au lieu d'une — rien écrit.")
        return 1
    e = entrees[0]
    vus = set()
    for sc, faits in (e.get("faits_imposes") or {}).items():
        garde = []
        for f in faits or []:
            if isinstance(f, dict) and f.get("slug") in retirer:
                vus.add(f["slug"])
                print(f"  − fait ({sc}) : {' '.join(str(f.get('fait')).split())[:110]}")
            else:
                garde.append(f)
        e["faits_imposes"][sc] = garde
    acteurs = e.get("acteurs_hint") or []
    for s in acteurs:
        if s in retirer:
            vus.add(s)
            print(f"  − acteur : {s}")
    e["acteurs_hint"] = [s for s in acteurs if s not in retirer]
    if "acteurs_hint_count" in e:
        e["acteurs_hint_count"] = len(e["acteurs_hint"])
    absents = sorted(retirer - vus)
    if absents:
        print(f"  (introuvables dans l'entrée, sans effet : {', '.join(absents)})")
    if not vus:
        print("✗ rien à retirer — rien écrit.")
        return 1
    if not args.apply:
        print("\nAperçu seulement — relancer avec --apply pour écrire.")
        return 0
    shutil.copy2(QUEUE, QUEUE.with_name("queue.yaml.bak_retirer"))
    QUEUE.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100),
                     encoding="utf-8")
    yaml.safe_load(QUEUE.read_text(encoding="utf-8"))
    print(f"\n✓ entrée {args.id} corrigée (sauvegarde queue.yaml.bak_retirer).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
