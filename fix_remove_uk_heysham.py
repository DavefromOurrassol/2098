#!/usr/bin/env python3
"""
fix_remove_uk_heysham.py

Retire l'entrée "- entite: Royaume-Uni" de l'origine_reelle de la zone
Zone Interdite de Heysham (slug: zone_interdite_heysham) dans
geographie/fortress_world.md.

Cause du bug : cette entrée réaffectait silencieusement "Royaume-Uni" à
cette zone dans zones_pays.json à chaque resynchronisation, écrasant
toute désaffectation manuelle faite via le GUI (bouton "Désaffecter").

Usage :
  python3 fix_remove_uk_heysham.py                # dry-run
  python3 fix_remove_uk_heysham.py --apply         # applique + .bak

Convention : lancé depuis la racine du vault.
"""

import argparse
import shutil
from pathlib import Path

TARGET_FILE = "geographie/fortress_world.md"

# Bloc exact à repérer, tel que confirmé par David (sed -n '2670,2695p')
BLOCK_START_MARKER = "  origine_reelle:\n  - entite: France\n    type_entite: pays\n    portion: null\n  - entite: Angleterre\n    type_entite: pays\n    portion: null\n  - entite: Pays de Galles\n  - entite: Royaume-Uni\n"
BLOCK_END_MARKER = "  - entite: Irlande\n  - entite: Belgique\n  - entite: Luxembourg\n"

OLD_BLOCK = BLOCK_START_MARKER + BLOCK_END_MARKER
NEW_BLOCK = (
    "  origine_reelle:\n"
    "  - entite: France\n"
    "    type_entite: pays\n"
    "    portion: null\n"
    "  - entite: Angleterre\n"
    "    type_entite: pays\n"
    "    portion: null\n"
    "  - entite: Pays de Galles\n"
    "  - entite: Irlande\n"
    "  - entite: Belgique\n"
    "  - entite: Luxembourg\n"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                         help="Applique la modification (sinon dry-run)")
    args = parser.parse_args()

    path = Path(TARGET_FILE)
    if not path.exists():
        print(f"[ERREUR] Fichier introuvable : {path} (lance depuis la racine du vault)")
        return

    text = path.read_text(encoding="utf-8")

    count = text.count(OLD_BLOCK)
    if count == 0:
        print("[ERREUR] Bloc attendu introuvable tel quel dans le fichier.")
        print("Le formatage a peut-être légèrement changé depuis le sed fourni.")
        print("Aucune modification faite — vérifie manuellement les lignes ~2678-2686.")
        return
    if count > 1:
        print(f"[ERREUR] Bloc trouvé {count} fois — pas assez spécifique pour un remplacement sûr.")
        print("Aucune modification faite.")
        return

    print("[OK] Bloc trouvé exactement une fois.")
    print()
    print("Avant :")
    print(OLD_BLOCK)
    print("Après :")
    print(NEW_BLOCK)

    if args.apply:
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
        new_text = text.replace(OLD_BLOCK, NEW_BLOCK)
        path.write_text(new_text, encoding="utf-8")
        print()
        print(f"[APPLIQUÉ] {path} modifié, backup : {bak}")
        print("Pense à relancer regenerate_zones_pays.py --dry-run pour vérifier")
        print("que zones_pays.json redevient cohérent, puis redémarrer Flask entièrement.")
    else:
        print()
        print("Dry-run terminé. Relance avec --apply pour écrire réellement.")


if __name__ == "__main__":
    main()
