#!/usr/bin/env python3
"""
rebuild_processed.py — Ourrassol 2098
======================================
Reconstruit les entrées manquantes dans processed.yaml pour les événements
custom géo injectés manuellement (source: rééquilibrage_geo_2026-06)
qui ne sont pas encore tracés dans processed.yaml.

Usage:
    python3 generator/rebuild_processed.py           # affiche + écrit
    python3 generator/rebuild_processed.py --dry-run # affiche seulement
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
EVENT_INSTANCES_DIR = VAULT_ROOT / "event_instances"
EVENEMENTS_DIR = VAULT_ROOT / "evenements"
EVENEMENTS_CUSTOM_DIR = VAULT_ROOT / "evenements_custom"
PROCESSED_PATH = EVENEMENTS_CUSTOM_DIR / "processed.yaml"

# Événements déjà tracés dans processed.yaml (à ne pas dupliquer)
ALREADY_TRACKED_ARCHETYPES = {"conflit_israel_iran_2026"}

# Événements non-custom à ignorer (existaient avant le pipeline)
NON_CUSTOM_SOURCES = {"?", ""}


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def load_processed():
    if not PROCESSED_PATH.exists():
        return []
    data = yaml.safe_load(PROCESSED_PATH.read_text(encoding="utf-8")) or {}
    return data.get("processed", []) or []


def save_processed(items, dry_run=False):
    content = yaml.dump({"processed": items}, allow_unicode=True,
                        sort_keys=False, default_flow_style=False)
    if dry_run:
        print("\n=== processed.yaml résultant (dry-run) ===")
        print(content[:2000], "..." if len(content) > 2000 else "")
    else:
        PROCESSED_PATH.write_text(content, encoding="utf-8")
        print(f"processed.yaml mis à jour ({len(items)} entrées)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Grouper les instances par archétype
    archetypes = {}
    for path in sorted(EVENT_INSTANCES_DIR.glob("*.md")):
        if path.suffix == ".bak" or path.name == ".DS_Store":
            continue
        fm = parse_frontmatter(path)
        if not fm:
            continue
        source = str(fm.get("custom_source", "") or "").strip()
        archetype = str(fm.get("archetype", "") or "").strip()
        scenario = str(fm.get("scenario", "") or "").strip()

        # Ignorer les non-custom et les déjà trackés
        if source in NON_CUSTOM_SOURCES:
            continue
        if archetype in ALREADY_TRACKED_ARCHETYPES:
            continue
        if not archetype or not scenario:
            continue

        if archetype not in archetypes:
            archetypes[archetype] = {"source": source, "instances": []}
        archetypes[archetype]["instances"].append({
            "scenario": scenario,
            "path": path,
            "fm": fm,
        })

    print(f"Archétypes custom non trackés trouvés : {len(archetypes)}")
    for arch, data in archetypes.items():
        scenarios = [i["scenario"] for i in data["instances"]]
        print(f"  {arch} → {scenarios}")

    if not archetypes:
        print("Rien à reconstruire.")
        return

    # Charger processed.yaml existant
    existing = load_processed()
    existing_archetypes = set()
    for entry in existing:
        sel = entry.get("selection", {})
        existing_archetypes.add(sel.get("slug", ""))

    new_entries = []
    for arch, data in archetypes.items():
        if arch in existing_archetypes:
            print(f"  [SKIP] {arch} déjà dans processed.yaml")
            continue

        # Reconstruire une entrée minimale mais valide
        # Chercher l'archétype dans evenements/
        arch_path = EVENEMENTS_DIR / f"{arch}.md"
        arch_fm = parse_frontmatter(arch_path) if arch_path.exists() else {}

        idea = {
            "id": arch,
            "description": str(arch_fm.get("description", arch)).strip(),
            "portee": arch_fm.get("portee", "continentale"),
            "date_approximative": str(arch_fm.get("date_approximative", "2050")),
            "intensite": arch_fm.get("intensite", "forte"),
            "scenarios": [i["scenario"] for i in data["instances"]],
            "variables_hint": arch_fm.get("variables_hint") or [],
            "variables_hint_count": None,
            "acteurs_hint": None,
            "acteurs_hint_count": None,
            "source": data["source"],
        }

        # Extraire variables depuis la première instance
        first_fm = data["instances"][0]["fm"]
        impacts = first_fm.get("impact_sur_variables") or []
        variables = list({
            imp["variable"] for imp in impacts
            if isinstance(imp, dict) and "variable" in imp
        })

        results = []
        for inst in data["instances"]:
            fm = inst["fm"]
            results.append({
                "scenario": inst["scenario"],
                "status": "injected",
                "instance_data": {
                    "nom": fm.get("name", arch),
                    "date": fm.get("date", 2050),
                    "evenement_cle": "",
                    "note_coherence": fm.get("note_coherence", ""),
                },
            })

        entry = {
            "status": "injected",
            "idea": idea,
            "selection": {
                "variables": variables,
                "type_evenement": first_fm.get("type_evenement", "systemic"),
                "slug": arch,
            },
            "results": results,
        }
        new_entries.append(entry)
        print(f"  [ADD] {arch} ({len(results)} scénarios)")

    if not new_entries:
        print("Aucune nouvelle entrée à ajouter.")
        return

    updated = existing + new_entries
    save_processed(updated, dry_run=args.dry_run)
    print(f"\nTerminé. {len(new_entries)} entrées ajoutées, total={len(updated)}.")


if __name__ == "__main__":
    main()
