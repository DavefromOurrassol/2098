#!/usr/bin/env python3
"""
patch_s28_validate.py -- S28 : validate.py n'exige plus une matrice pleine.

Remplace « exactement 12×11 = 132 edges » par :
  - au plus 132 edges ;
  - aucune variable isolée (au moins un lien sortant et un entrant).

Usage (depuis la racine du vault) :
  python3 generator/patch_s28_validate.py           # aperçu, rien écrit
  python3 generator/patch_s28_validate.py --apply   # écrit (.bak_s28)
"""
import py_compile
import re
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
GEN = ICI if (ICI / "validate.py").exists() else ICI / "generator"
CIBLE = GEN / "validate.py"
MARQUEUR = "Matrice creuse depuis S28"

OLD = '''    # Vérifier 12×11 = 132 edges
    expected = len(VALID_VARS) * (len(VALID_VARS) - 1)
    if len(seen_pairs) != expected:
        result.warning("matrix", "influence_matrix.md",
            "Nombre d'edges : {} (attendu : {})".format(
                len(seen_pairs), expected))
'''
NEW = '''    # Matrice creuse depuis S28 (25 oct 2026) : au plus 12×11 = 132 edges,
    # et aucune variable isolée (au moins un lien sortant et un entrant).
    maximum = len(VALID_VARS) * (len(VALID_VARS) - 1)
    if len(seen_pairs) > maximum:
        result.warning("matrix", "influence_matrix.md",
            "Nombre d'edges : {} (maximum : {})".format(len(seen_pairs), maximum))
    sources = {s for s, _ in seen_pairs}
    cibles = {c for _, c in seen_pairs}
    for v in VALID_VARS:
        if v not in sources or v not in cibles:
            result.warning("matrix", "influence_matrix.md",
                "{} isolée : {}".format(
                    v, "aucun lien sortant" if v not in sources else "aucun lien entrant"))
'''


def main():
    t = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in t:
        sys.exit("✗ Patch déjà appliqué : rien à faire.")
    if t.count(OLD) != 1:
        sys.exit("✗ bloc « 12×11 = 132 edges » introuvable ou en double : rien écrit.")
    # seen_pairs doit contenir des paires (source, cible)
    if not (re.search(r"seen_pairs\.add\(\s*\(\s*source\s*,\s*target\s*\)\s*\)", t)
            or (re.search(r"pair\s*=\s*\(\s*source\s*,\s*target\s*\)", t) and "seen_pairs.add(pair)" in t)):
        sys.exit("✗ seen_pairs ne semble pas contenir des paires (source, target) : rien écrit.")
    nouveau = t.replace(OLD, NEW)
    essai = CIBLE.with_name("_essai_patch_s28.py")
    essai.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(essai), doraise=True)
    except py_compile.PyCompileError as e:
        essai.unlink()
        sys.exit(f"✗ le fichier patché ne compile pas, rien écrit :\n{e}")
    essai.unlink()
    if "--apply" not in sys.argv:
        print("APERÇU : bloc trouvé, seen_pairs conforme, le fichier patché compile. Rien écrit.")
        print("Relancer avec --apply.")
        return
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s28"))
    CIBLE.write_text(nouveau, encoding="utf-8")
    print("✓ validate.py patché (sauvegarde validate.py.bak_s28).")


if __name__ == "__main__":
    main()
