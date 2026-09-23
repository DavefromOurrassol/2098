#!/usr/bin/env python3
"""
rename_zone_interzone.py

Renomme la zone "Interzone" (slug interzone) en "Zone Euro Sud"
(slug zone_euro_sud) dans tout le vault Ourrassol 2098.

Fichiers concernés (recensés par grep le 9 sept 2026) :
  - geographie/fortress_world.md          (définition source : nom + slug)
  - zones_pays.json                       (23 entrées "Pays": "interzone")
  - documentation/need_action/impact_bascule_{bulgarie,italie,moldavie}_fortress_world.md
  - documentation/BACKLOG_ACTIF.md        (--include-doc pour le toucher)
  - documentation/HANDOFF_8_SEPTEMBRE.md  (--include-doc pour le toucher, désactivé
                                            par défaut : c'est un journal de session,
                                            réécrire l'historique est discutable)

Usage :
  python3 rename_zone_interzone.py                  # dry-run (aucune écriture)
  python3 rename_zone_interzone.py --apply           # applique + .bak
  python3 rename_zone_interzone.py --apply --include-doc  # + doc historique

Convention : lancé depuis la racine du vault (là où se trouve zones_pays.json).
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

OLD_NAME = "Interzone"
NEW_NAME = "Zone Euro Sud"
OLD_SLUG = "interzone"
NEW_SLUG = "zone_euro_sud"

TARGET_FILES_CORE = [
    "geographie/fortress_world.md",
    "zones_pays.json",
    "documentation/need_action/impact_bascule_bulgarie_fortress_world.md",
    "documentation/need_action/impact_bascule_italie_fortress_world.md",
    "documentation/need_action/impact_bascule_moldavie_fortress_world.md",
]

TARGET_FILES_DOC = [
    "documentation/BACKLOG_ACTIF.md",
    "documentation/HANDOFF_8_SEPTEMBRE.md",
]


def backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, bak)
    return bak


def rename_in_text(text: str) -> tuple[str, int]:
    """
    Remplace le nom affiché (respecte la casse "Interzone" -> "Zone Euro Sud")
    et le slug (interzone -> zone_euro_sud) partout dans le texte.
    Retourne (nouveau_texte, nb_remplacements).
    """
    count = 0

    def repl_name(m):
        nonlocal count
        count += 1
        return NEW_NAME

    def repl_slug(m):
        nonlocal count
        count += 1
        return NEW_SLUG

    # 1) Nom affiché exact "Interzone" (casse capitalisée) -> "Zone Euro Sud"
    text, n1 = re.subn(r"\bInterzone\b", NEW_NAME, text)
    count += n1

    # 2) Slug en minuscules "interzone" -> "zone_euro_sud"
    #    (couvre les clés JSON, les valeurs de "zone:", "slug:", les mentions en
    #    minuscules dans le corps du texte, etc.)
    text, n2 = re.subn(r"\binterzone\b", NEW_SLUG, text)
    count += n2

    return text, count


def process_file(path: Path, apply: bool) -> int:
    if not path.exists():
        print(f"  [SKIP] introuvable : {path}")
        return 0

    original = path.read_text(encoding="utf-8")
    new_text, n = rename_in_text(original)

    if n == 0:
        print(f"  [OK]  0 occurrence : {path}")
        return 0

    print(f"  [{'APPLY' if apply else 'DRY-RUN'}] {n} occurrence(s) : {path}")

    if apply:
        backup(path)
        path.write_text(new_text, encoding="utf-8")

    return n


def validate_json(path: Path):
    """Vérifie que zones_pays.json reste un JSON valide après écriture."""
    try:
        json.loads(path.read_text(encoding="utf-8"))
        print(f"  [OK]  JSON valide après modification : {path}")
    except json.JSONDecodeError as e:
        print(f"  [ERREUR] JSON invalide après modification : {path} -> {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                         help="Applique les modifications (sinon dry-run)")
    parser.add_argument("--include-doc", action="store_true",
                         help="Touche aussi BACKLOG_ACTIF.md et HANDOFF_8_SEPTEMBRE.md")
    args = parser.parse_args()

    targets = list(TARGET_FILES_CORE)
    if args.include_doc:
        targets += TARGET_FILES_DOC

    print(f"Mode : {'APPLICATION RÉELLE (.bak créés)' if args.apply else 'DRY-RUN (aucune écriture)'}")
    print(f"Fichiers doc historiques : {'inclus' if args.include_doc else 'exclus (--include-doc pour les inclure)'}")
    print()

    total = 0
    for rel in targets:
        total += process_file(Path(rel), args.apply)

    print()
    print(f"Total : {total} occurrence(s) sur {len(targets)} fichier(s) ciblé(s)")

    if args.apply:
        zp = Path("zones_pays.json")
        if zp.exists():
            validate_json(zp)
        print()
        print("Terminé. Fichiers .bak créés à côté de chaque fichier modifié.")
        print("Pense à redémarrer Flask entièrement si le serveur tourne.")
    else:
        print()
        print("Dry-run terminé. Relance avec --apply pour écrire réellement.")


if __name__ == "__main__":
    main()
