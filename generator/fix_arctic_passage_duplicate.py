#!/usr/bin/env python3
"""
fix_arctic_passage_duplicate.py

Chantier backlog #3 (BACKLOG_MASTER_9_AOUT.md) — fusion du doublon
d'entité arctic_passage_authority / autorite_passage_arctique.

Ce script NE TOUCHE PAS :
  - les fiches entités/instances de autorite_passage_arctique elles-mêmes
    (entites/autorite_passage_arctique.md,
     instances/autorite_passage_arctique_breakdown.md)
    → à supprimer ensuite via undo_custom.py --generalisation yes
  - les champs `zone: autorite_passage_arctique` (référence géographique,
    hors scope de ce chantier — voir note du 14 août)
  - geographie/breakdown.md (idem, référence de zone)

Ce script réécrit UNIQUEMENT les références à l'entité en alliance/
opposition dans instances/*.md, sous deux formes :
  - liste YAML simple :   - autorite_passage_arctique_breakdown
  - wikilink Markdown :   - [[autorite_passage_arctique_breakdown]]

remplacées respectivement par :
  - arctic_passage_authority_breakdown
  - [[arctic_passage_authority_breakdown]]

Dry-run par défaut (aucune écriture). --execute pour appliquer.
Backup .bak créé avant toute écriture (même convention que les autres
scripts du pipeline : undo_custom.py, fix_alliances_oppositions.py...).

Usage :
    python3 fix_arctic_passage_duplicate.py --vault-root .
    python3 fix_arctic_passage_duplicate.py --vault-root . --execute
"""

import argparse
import re
from pathlib import Path

OLD_SLUG = "autorite_passage_arctique_breakdown"
NEW_SLUG = "arctic_passage_authority_breakdown"

# Pattern 1 : entrée de liste YAML simple, ex. "- autorite_passage_arctique_breakdown"
# (ancrée en début de ligne après indentation, pas de crochets, pas de "zone:")
PATTERN_YAML_LIST = re.compile(
    r"^(?P<prefix>[ \t]*-[ \t]+)" + re.escape(OLD_SLUG) + r"(?P<suffix>[ \t]*)$",
    re.MULTILINE,
)

# Pattern 2 : wikilink Markdown, ex. "- [[autorite_passage_arctique_breakdown]]"
PATTERN_WIKILINK = re.compile(
    r"\[\[" + re.escape(OLD_SLUG) + r"\]\]"
)


def find_target_files(vault_root: Path):
    """Scanne instances/*.md à la recherche de références au slug fantôme."""
    instances_dir = vault_root / "instances"
    if not instances_dir.exists():
        raise SystemExit(f"Dossier introuvable : {instances_dir}")

    targets = []
    for md_file in sorted(instances_dir.glob("*.md")):
        if md_file.name.startswith(OLD_SLUG):
            # On ne touche jamais la fiche du doublon lui-même —
            # elle sera supprimée par undo_custom.py, pas réécrite.
            continue
        text = md_file.read_text(encoding="utf-8")
        if OLD_SLUG in text:
            targets.append(md_file)
    return targets


def rewrite_content(text: str):
    """Applique les deux substitutions, renvoie (nouveau_texte, nb_changements)."""
    n1 = len(PATTERN_YAML_LIST.findall(text))
    text = PATTERN_YAML_LIST.sub(
        lambda m: m.group("prefix") + NEW_SLUG + m.group("suffix"), text
    )
    n2 = len(PATTERN_WIKILINK.findall(text))
    text = PATTERN_WIKILINK.sub(f"[[{NEW_SLUG}]]", text)
    return text, n1 + n2


def main():
    parser = argparse.ArgumentParser(
        description="Migre les références alliance/opposition de "
                    "autorite_passage_arctique_breakdown vers "
                    "arctic_passage_authority_breakdown (fusion doublon, backlog #3)."
    )
    parser.add_argument("--vault-root", default=".",
                         help="Racine du vault (défaut : répertoire courant)")
    parser.add_argument("--execute", action="store_true",
                         help="Applique les modifications (sinon dry-run)")
    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    targets = find_target_files(vault_root)

    if not targets:
        print("Aucune fiche instances/*.md ne référence "
              f"'{OLD_SLUG}'. Rien à faire.")
        return

    print(f"{'[DRY-RUN] ' if not args.execute else ''}"
          f"{len(targets)} fiche(s) à modifier :\n")

    total_changes = 0
    for md_file in targets:
        text = md_file.read_text(encoding="utf-8")
        new_text, n_changes = rewrite_content(text)
        total_changes += n_changes

        print(f"  {md_file.relative_to(vault_root)} — {n_changes} référence(s)")

        if args.execute and new_text != text:
            bak_path = md_file.with_suffix(md_file.suffix + ".bak")
            bak_path.write_text(text, encoding="utf-8")
            md_file.write_text(new_text, encoding="utf-8")

    print(f"\nTotal : {total_changes} référence(s) sur {len(targets)} fiche(s).")

    if not args.execute:
        print("\nAucune écriture effectuée (dry-run). "
              "Relancer avec --execute pour appliquer "
              "(backup .bak créé automatiquement).")
    else:
        print("\nModifications appliquées. Backups .bak créés à côté de "
              "chaque fiche modifiée.")
        print("\nÉtape suivante : supprimer l'archétype fantôme avec")
        print(f"  python3 undo_custom.py --slug autorite_passage_arctique "
              f"--type entity --generalisation yes           # dry-run")
        print(f"  python3 undo_custom.py --slug autorite_passage_arctique "
              f"--type entity --generalisation yes --execute")
        print("\nPuis valider :")
        print("  python3 validate.py --verbose")


if __name__ == "__main__":
    main()
