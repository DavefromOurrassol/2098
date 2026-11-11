#!/usr/bin/env python3
"""
patch_u3k_nettoyage_citation.py — Ourrassol 2098 (U3k, 11 novembre 2026)

Complète U3i : la citation de l'article est nettoyée avant de devenir un fait imposé
(guillemets « » extérieurs, astérisques Markdown, espaces doubles retirés), et n'est pas
ajoutée si une contrainte proposée par l'IA la contient déjà (comparaison sans guillemets
ni astérisques).

Dry-run par défaut ; --apply pour écrire (sauvegarde .bak_u3k). Idempotent.
À lancer depuis la racine du vault. Puis redémarrer Flask.
"""
import py_compile
import shutil
import sys
from pathlib import Path

APPLY = "--apply" in sys.argv
F = Path("generator/hypothese_depuis_texte.py")

A1 = """    cit = " ".join(str(imposes.get("citation") or "").split())
"""
N1 = """    cit = " ".join(str(imposes.get("citation") or "").replace("*", "").split()).strip("«» ").strip()   # U3k

    def _plat(s):
        return " ".join(str(s).replace("*", "").replace("«", " ").replace("»", " ").split()).lower()
"""
A2 = """        if cit not in contraintes:
"""
N2 = """        if not any(_plat(cit) in _plat(c) for c in contraintes):   # U3k
"""

t = F.read_text(encoding="utf-8")
if N1 in t and N2 in t:
    sys.exit("= déjà appliqué")
for a in (A1, A2):
    if t.count(a) != 1:
        sys.exit(f"✗ ancre introuvable ou multiple ({t.count(a)}) — U3i appliqué ?\n{a}")
print("+ modification prévue")
if APPLY:
    shutil.copy2(F, str(F) + ".bak_u3k")
    F.write_text(t.replace(A1, N1).replace(A2, N2), encoding="utf-8")
    py_compile.compile(str(F), doraise=True)
    print("✓ écrit (sauvegarde .bak_u3k), py_compile OK — redémarrer Flask")
else:
    print("(dry-run : rien écrit ; relancer avec --apply)")
