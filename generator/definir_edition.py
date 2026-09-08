#!/usr/bin/env python3
"""
definir_edition.py — Ourrassol 2098
=====================================

Configure/avance le mois de parution actif (state/editions.json)
indépendamment de tout lancement de série -- ajouté le 2 septembre
2026 à la demande de David, chantier "Éditions datées" (point 3).
Terminologie "mois de parution" retenue le même jour (préférée à
"édition", jugée ambiguë -- lue comme "modifier" plutôt que "numéro
du journal").

Avant cet outil, la SEULE façon de faire avancer le mois de parution
était de lancer un vrai lot via generate_series.py/generate_manual.py
-- pas de moyen de simplement dire "on passe à septembre" sans générer
des articles dans la foulée. Cet outil comble ce trou : il ne fait QUE
déplacer le pointeur de mois de parution, aucun article n'est généré,
aucun appel LLM.

Usage :
    python3 definir_edition.py --annee 2098 --mois 9
    python3 definir_edition.py --statut          # affiche le mois de parution actif sans le changer

Effet sur les autres scripts, une fois le mois de parution défini ici :
  - generate.py (article isolé) le suit automatiquement (lecture seule)
  - generate_series.py/generate_manual.py l'utilisent par défaut si
    annee_edition/mois_edition sont absents de config_series.yaml
    (peuvent toujours être surchargés explicitement dans ce fichier
    pour un lot ponctuel sur un mois différent)
"""
import argparse

from edition_utils import definir_edition_active, lire_edition_active, MOIS_FR


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annee", type=int, default=None, help="Année (ex. 2098)")
    parser.add_argument("--mois", type=int, default=None, help="Mois, 1-12")
    parser.add_argument("--statut", action="store_true",
                         help="Affiche le mois de parution actif sans le modifier")
    args = parser.parse_args()

    if args.statut:
        active = lire_edition_active()
        if active:
            print("Mois de parution actif : {} {} (n°{})".format(
                MOIS_FR[active["mois"]], active["annee"], active["numero"]
            ))
        else:
            print("Aucun mois de parution défini pour l'instant.")
        return

    if not args.annee or not args.mois:
        print("[erreur] --annee et --mois requis (ou --statut pour juste consulter).")
        raise SystemExit(1)
    if not (1 <= args.mois <= 12):
        print("[erreur] --mois hors plage [1-12] : {}".format(args.mois))
        raise SystemExit(1)

    precedent = lire_edition_active()
    numero = definir_edition_active(args.annee, args.mois)

    if precedent:
        print("Mois de parution : {} {} (n°{}) → {} {} (n°{})".format(
            MOIS_FR[precedent["mois"]], precedent["annee"], precedent["numero"],
            MOIS_FR[args.mois], args.annee, numero
        ))
    else:
        print("Mois de parution défini : {} {} (n°{})".format(
            MOIS_FR[args.mois], args.annee, numero
        ))


if __name__ == "__main__":
    main()
