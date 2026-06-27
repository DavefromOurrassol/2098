#!/usr/bin/env python3
"""
requeue_needs_review.py — Ourrassol 2098
=========================================

Remet les entrées de needs_review.yaml dans queue.yaml pour une nouvelle
tentative via create_entities_and_instances.py.

USAGE
-----
    python3 requeue_needs_review.py --dry-run
    python3 requeue_needs_review.py
"""

import argparse
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
NEEDS_REVIEW_PATH = VAULT_ROOT / "entites_custom" / "needs_review.yaml"
QUEUE_PATH = VAULT_ROOT / "entites_custom" / "queue.yaml"


def main():
    parser = argparse.ArgumentParser(
        description="Remet les entrées needs_review.yaml dans queue.yaml."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche sans écrire")
    args = parser.parse_args()

    if not NEEDS_REVIEW_PATH.exists():
        print(f"[ERREUR] {NEEDS_REVIEW_PATH} non trouvé")
        return

    data = yaml.safe_load(NEEDS_REVIEW_PATH.read_text(encoding="utf-8")) or {}
    entries = data.get("needs_review", [])

    if not entries:
        print("needs_review.yaml vide — rien à faire.")
        return

    # Extraire les idées
    ideas = []
    for entry in entries:
        idea = entry.get("idea")
        if idea:
            ideas.append(idea)

    print(f"→ {len(ideas)} entrées trouvées dans needs_review.yaml")

    # Charger la queue existante
    existing = []
    if QUEUE_PATH.exists():
        try:
            q = yaml.safe_load(QUEUE_PATH.read_text(encoding="utf-8")) or {}
            existing = q.get("queue", []) or []
        except Exception:
            pass

    # Dédupliquer sur _slug_corrige ou nom
    existing_keys = {
        e.get("_slug_corrige", e.get("nom", "")).lower()
        for e in existing
    }
    new_ideas = [
        i for i in ideas
        if i.get("_slug_corrige", i.get("nom", "")).lower() not in existing_keys
    ]
    skipped = len(ideas) - len(new_ideas)

    print(f"  Nouvelles entrées à ajouter : {len(new_ideas)}")
    if skipped:
        print(f"  Ignorées (déjà dans queue) : {skipped}")

    if not new_ideas:
        print("Rien à ajouter.")
        return

    if not args.dry_run:
        all_entries = existing + new_ideas
        QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        QUEUE_PATH.write_text(
            yaml.dump({"queue": all_entries}, allow_unicode=True,
                      default_flow_style=False, sort_keys=False),
            encoding="utf-8"
        )
        print(f"✓ {len(new_ideas)} entrées ajoutées à {QUEUE_PATH}")
        print("\n→ Lancer :")
        print("  python3 create_entities_and_instances.py  (mode custom)")
    else:
        print("(dry-run) rien écrit")


if __name__ == "__main__":
    main()
