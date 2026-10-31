#!/usr/bin/env python3
"""
patch_s23_profils_reseaux.py — S23, 31 oct 2026

Aligne JOURNAL_PROFILES (prompt_builder.py) sur journaux.yaml /
generate_journaux.RESEAUX :
  1. breakdown_pro_pouvoir : « L'Ordre du Territoire » -> « L'Ordre Zonal »
     (seule divergence de nom entre les trois sources) ;
  2. fortress_world_pro_pouvoir : posture « organe officiel du Bloc
     Atlantique-Méditerranéen » -> « organe officiel du bloc dont relève la
     zone » (au chemin 2, réseau global, cette posture s'appliquait à toutes
     les zones, Asie comprise).

Usage (depuis la racine du vault) :
  python3 generator/patch_s23_profils_reseaux.py           # aperçu
  python3 generator/patch_s23_profils_reseaux.py --apply   # applique (.bak créé)
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

CIBLE = os.path.join("generator", "prompt_builder.py")
REMPLACEMENTS = [
    ("nom breakdown pro_pouvoir",
     '"nom":     "L\'Ordre du Territoire",',
     '"nom":     "L\'Ordre Zonal",  # S23 (31 oct 2026) : aligné sur journaux.yaml'),
    ("posture fortress_world pro_pouvoir",
     '"posture": "organe officiel du Bloc Atlantique-Méditerranéen",',
     '"posture": "organe officiel du bloc dont relève la zone",  # S23 (31 oct 2026) : valable pour tous les blocs'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(CIBLE):
        sys.exit("Lancer depuis la racine du vault ({} introuvable).".format(CIBLE))
    src = open(CIBLE, encoding="utf-8").read()
    if "S23 (31 oct 2026) : aligné sur journaux.yaml" in src:
        print("Déjà appliqué : rien à faire.")
        return
    for nom, old, new in REMPLACEMENTS:
        n = src.count(old)
        if n != 1:
            sys.exit("ÉCHEC « {} » : {} occurrence(s) au lieu de 1. Rien modifié.".format(nom, n))
        src = src.replace(old, new)
        print("OK  {}".format(nom))
    compile(src, CIBLE, "exec")
    if not args.apply:
        print("\nAperçu seulement. Relancer avec --apply.")
        return
    bak = "{}.bak_{}".format(CIBLE, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(CIBLE, bak)
    open(CIBLE, "w", encoding="utf-8").write(src)
    print("\nAppliqué. Sauvegarde : {}".format(bak))


if __name__ == "__main__":
    main()
