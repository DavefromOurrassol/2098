#!/usr/bin/env python3
"""
fix_name_non_quote.py — correction ponctuelle, PAS un outil du pipeline
==========================================================================

Corrige la ligne `name: ...` d'un fichier frontmatter quand elle contient
un ": " non échappé qui casse le parsing YAML (cas trouvé le 7 septembre
2026 sur evenements/incident_passage_arctique.md et
evenements/helios_bse_active_le_protocole_ombre_les_coupures_.md).

Ne touche QUE la ligne `name:` -- entoure sa valeur de guillemets doubles
(en échappant les guillemets internes déjà présents, s'il y en a). Crée
un .bak avant toute écriture. Affiche un diff avant/après et demande
confirmation, sauf avec --apply.

USAGE
-----
    # Aperçu seul, aucune écriture
    python3 fix_name_non_quote.py evenements/incident_passage_arctique.md

    # Applique réellement (après vérification de l'aperçu)
    python3 fix_name_non_quote.py evenements/incident_passage_arctique.md --apply
"""

import argparse
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fichier", help="Chemin du fichier .md à corriger")
    parser.add_argument("--apply", action="store_true",
                         help="Applique réellement la correction (sinon, aperçu seul)")
    args = parser.parse_args()

    with open(args.fichier, "r", encoding="utf-8") as f:
        lignes = f.readlines()

    ligne_name_idx = None
    for idx, ligne in enumerate(lignes):
        if ligne.startswith("name:"):
            ligne_name_idx = idx
            break

    if ligne_name_idx is None:
        print("Aucune ligne 'name:' trouvée en début de fichier -- rien à faire.")
        sys.exit(1)

    ancienne_ligne = lignes[ligne_name_idx]
    valeur = ancienne_ligne[len("name:"):].strip()

    if valeur.startswith('"') and valeur.endswith('"'):
        print("La valeur est déjà entre guillemets -- rien à faire.")
        sys.exit(0)

    valeur_echappee = valeur.replace('"', '\\"')
    nouvelle_ligne = f'name: "{valeur_echappee}"\n'

    print("--- Ligne actuelle ---")
    print(ancienne_ligne.rstrip("\n"))
    print("--- Ligne corrigée ---")
    print(nouvelle_ligne.rstrip("\n"))

    if not args.apply:
        print("\n(Aperçu seul -- relance avec --apply pour écrire réellement.)")
        return

    backup_path = args.fichier + ".bak"
    shutil.copy2(args.fichier, backup_path)
    print(f"\nSauvegarde créée : {backup_path}")

    lignes[ligne_name_idx] = nouvelle_ligne
    with open(args.fichier, "w", encoding="utf-8") as f:
        f.writelines(lignes)
    print(f"Fichier corrigé : {args.fichier}")


if __name__ == "__main__":
    main()
