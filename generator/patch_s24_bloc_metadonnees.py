#!/usr/bin/env python3
"""
patch_s24_bloc_metadonnees.py — S24, 31 oct 2026

Corrige l'extraction du bloc ===METADONNEES_PUBLICATION=== dans
generator/api.py :
  1. marqueur de fin ===FIN_METADONNEES=== facultatif : un bloc non fermé
     (oubli du LLM ou réponse tronquée par MAX_TOKENS) était laissé tel quel
     dans le texte publié ; il est désormais pris jusqu'à la fin du texte ;
  2. toutes les occurrences du bloc sont retirées (bloc en double), les
     champs sont lus dans la première ;
  3. avertissement dans la console dans ces deux cas.

Usage (depuis la racine du projet) :
  python3 generator/patch_s24_bloc_metadonnees.py           # aperçu
  python3 generator/patch_s24_bloc_metadonnees.py --apply   # applique (.bak créé)
  option : --fichier <chemin>  (défaut : generator/api.py)
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

REMPLACEMENTS = [
    (
        "regex du bloc (fin facultative)",
        '''_PUBLICATION_META_RE = re.compile(
    r"===METADONNEES_PUBLICATION===\\s*(.*?)\\s*===FIN_METADONNEES===",
    re.DOTALL | re.IGNORECASE
)''',
        '''# Correctif du 31 oct 2026 (S24) : marqueur de fin facultatif. Un bloc
# non fermé (oubli du LLM ou réponse tronquée par MAX_TOKENS, risque accru
# au retry longueur qui réécrit tout l'article) restait entier dans le texte
# publié. Sans marqueur de fin, le bloc court jusqu'à la fin du texte.
_PUBLICATION_META_RE = re.compile(
    r"===METADONNEES_PUBLICATION===\\s*(.*?)\\s*(?:===FIN_METADONNEES===|\\Z)",
    re.DOTALL | re.IGNORECASE
)''',
    ),
    (
        "retrait de toutes les occurrences + avertissements",
        '''    block = m.group(1)
    clean_text = (article_text[:m.start()] + article_text[m.end():]).rstrip()
''',
        '''    block = m.group(1)
    # Correctif du 31 oct 2026 (S24) : toutes les occurrences sont retirées
    # (bloc en double), les champs sont lus dans la première.
    clean_text = _PUBLICATION_META_RE.sub("", article_text).rstrip()
    if not re.search(r"===FIN_METADONNEES===", m.group(0), re.IGNORECASE):
        print("[api] [WARN] Bloc métadonnées sans marqueur de fin "
              "(réponse tronquée ?) — pris jusqu'à la fin du texte.")
    if len(_PUBLICATION_META_RE.findall(article_text)) > 1:
        print("[api] [WARN] Bloc métadonnées présent plusieurs fois — "
              "toutes les occurrences retirées, champs lus dans la première.")
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

    if "Correctif du 31 oct 2026 (S24)" in src:
        print("Déjà appliqué : rien à faire.")
        return

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
