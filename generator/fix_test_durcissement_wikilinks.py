#!/usr/bin/env python3
"""
fix_test_durcissement_wikilinks.py

Chantier backlog #4 (BACKLOG_MASTER_9_AOUT.md) — nettoyage des 7
wikilinks cassés vers `test_durcissement_policy_reform`, une fiche
supprimée (résidu du 8 août) qui n'existe plus ni dans entites/, ni
dans instances/.

Contrairement au chantier #3 (fusion de doublon), il ne s'agit pas
d'un renommage vers un autre slug : la référence est simplement
retirée, ligne par ligne, dans la section ## Relations des fiches
concernées.

Ce script supprime toute ligne markdown correspondant exactement à
un bullet wikilink vers ce slug (ex. "- [[test_durcissement_policy_reform]]",
avec ou sans texte descriptif après le wikilink sur la même ligne).

Dry-run par défaut (aucune écriture). --execute pour appliquer.
Backup .bak créé avant toute écriture.

Usage :
    python3 fix_test_durcissement_wikilinks.py --vault-root .
    python3 fix_test_durcissement_wikilinks.py --vault-root . --execute
"""

import argparse
import re
from pathlib import Path

DEAD_SLUG = "test_durcissement_policy_reform"

# Ligne bullet contenant le wikilink cassé, où qu'elle soit dans le
# fichier (section ## Relations attendue, mais on ne suppose pas la
# position exacte) — capture toute la ligne, y compris un éventuel
# texte descriptif après le wikilink (ex. "- [[slug]] : opposition mineure").
PATTERN_DEAD_LINE = re.compile(
    r"^[ \t]*-[ \t]*\[\[" + re.escape(DEAD_SLUG) + r"\]\].*\n?",
    re.MULTILINE,
)


def find_target_files(vault_root: Path):
    instances_dir = vault_root / "instances"
    if not instances_dir.exists():
        raise SystemExit(f"Dossier introuvable : {instances_dir}")

    targets = []
    for md_file in sorted(instances_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        if f"[[{DEAD_SLUG}]]" in text:
            targets.append(md_file)
    return targets


def rewrite_content(text: str):
    n = len(PATTERN_DEAD_LINE.findall(text))
    new_text = PATTERN_DEAD_LINE.sub("", text)
    return new_text, n


def main():
    parser = argparse.ArgumentParser(
        description="Retire les wikilinks cassés vers "
                    f"{DEAD_SLUG} (backlog #4)."
    )
    parser.add_argument("--vault-root", default=".",
                         help="Racine du vault (défaut : répertoire courant)")
    parser.add_argument("--execute", action="store_true",
                         help="Applique les modifications (sinon dry-run)")
    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    targets = find_target_files(vault_root)

    if not targets:
        print(f"Aucune fiche instances/*.md ne référence '{DEAD_SLUG}'. "
              "Rien à faire.")
        return

    print(f"{'[DRY-RUN] ' if not args.execute else ''}"
          f"{len(targets)} fiche(s) à modifier :\n")

    total_changes = 0
    for md_file in targets:
        text = md_file.read_text(encoding="utf-8")
        new_text, n_changes = rewrite_content(text)
        total_changes += n_changes

        print(f"  {md_file.relative_to(vault_root)} — "
              f"{n_changes} ligne(s) retirée(s)")

        if args.execute and new_text != text:
            bak_path = md_file.with_suffix(md_file.suffix + ".bak")
            bak_path.write_text(text, encoding="utf-8")
            md_file.write_text(new_text, encoding="utf-8")

    print(f"\nTotal : {total_changes} ligne(s) retirée(s) sur "
          f"{len(targets)} fiche(s).")

    if not args.execute:
        print("\nAucune écriture effectuée (dry-run). "
              "Relancer avec --execute pour appliquer "
              "(backup .bak créé automatiquement).")
    else:
        print("\nModifications appliquées. Backups .bak créés à côté de "
              "chaque fiche modifiée.")
        print("\nValider ensuite :")
        print("  python3 validate.py --verbose")


if __name__ == "__main__":
    main()
