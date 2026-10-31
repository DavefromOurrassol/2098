#!/usr/bin/env python3
"""
patch_s24b_bloc_tronque.py — S24, 31 oct 2026 (suite de patch_s24_bloc_metadonnees.py)

Bloc ===METADONNEES_PUBLICATION=== tronqué (pas de marqueur de fin ET champ(s)
manquant(s)) : les champs partiels sont jetés, pour que generate_article()
déclenche le retry ciblé des métadonnées (il n'agit que si chapo, tags et
image_prompt sont tous vides). Sans ce correctif, un chapô coupé net était
publié tel quel.

Prérequis : patch_s24_bloc_metadonnees.py déjà appliqué.

Usage (depuis la racine du projet) :
  python3 generator/patch_s24b_bloc_tronque.py           # aperçu
  python3 generator/patch_s24b_bloc_tronque.py --apply   # applique (.bak créé)
  option : --fichier <chemin>  (défaut : generator/api.py)
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

MARQUE = "Correctif du 31 oct 2026 (S24b)"

REMPLACEMENTS = [
    (
        "repérage du marqueur de fin absent",
        '''    if not re.search(r"===FIN_METADONNEES===", m.group(0), re.IGNORECASE):
        print("[api] [WARN] Bloc métadonnées sans marqueur de fin "
              "(réponse tronquée ?) — pris jusqu'à la fin du texte.")
''',
        '''    fin_absente = not re.search(r"===FIN_METADONNEES===", m.group(0), re.IGNORECASE)
    if fin_absente:
        print("[api] [WARN] Bloc métadonnées sans marqueur de fin "
              "(réponse tronquée ?) — pris jusqu'à la fin du texte.")
''',
    ),
    (
        "champs partiels jetés si bloc tronqué",
        '''                  ) if type_diffusion == "oral" else ""
              ))

    return clean_text, meta
''',
        '''                  ) if type_diffusion == "oral" else ""
              ))

    # ''' + MARQUE + ''' : bloc tronqué (sans fin ET incomplet) ->
    # champs partiels jetés, pour que generate_article() lance le retry
    # ciblé (qui n'agit que si chapo/tags/image_prompt sont tous vides).
    if fin_absente and not champs_attendus_ok:
        print("[api] [WARN] Bloc tronqué : champs partiels ignorés, "
              "retry ciblé des métadonnées attendu.")
        for k in meta:
            meta[k] = [] if k == "tags" else ""

    return clean_text, meta
''',
    ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fichier", default=os.path.join("generator", "api.py"))
    args = ap.parse_args()

    if not os.path.exists(args.fichier):
        sys.exit("Fichier introuvable : {}".format(args.fichier))
    with open(args.fichier, encoding="utf-8") as f:
        src = f.read()

    if MARQUE in src:
        print("Déjà appliqué : rien à faire.")
        return
    if "Correctif du 31 oct 2026 (S24)" not in src:
        sys.exit("Appliquer d'abord patch_s24_bloc_metadonnees.py.")

    for nom, old, new in REMPLACEMENTS:
        n = src.count(old)
        if n != 1:
            sys.exit("ÉCHEC « {} » : {} occurrence(s) au lieu de 1. "
                     "Rien n'a été modifié.".format(nom, n))
        src = src.replace(old, new)
        print("OK  {}".format(nom))

    if not args.apply:
        print("\nAperçu seulement. Relancer avec --apply.")
        return

    bak = "{}.bak_{}".format(args.fichier, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(args.fichier, bak)
    with open(args.fichier, "w", encoding="utf-8") as f:
        f.write(src)
    print("\nAppliqué. Sauvegarde : {}".format(bak))


if __name__ == "__main__":
    main()
