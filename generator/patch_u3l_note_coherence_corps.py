#!/usr/bin/env python3
"""
patch_u3l_note_coherence_corps.py — Ourrassol 2098 (U3l, 11 novembre 2026)

Défaut : dans la fiche d'instance écrite par inject_custom_events.py, la section
« ## Note de cohérence » du CORPS recopiait la version YAML de la note (guillemets
simples extérieurs, apostrophes doublées, retours à la ligne repliés). Le gabarit
utilisait le même marqueur {note} dans le frontmatter et dans le corps.
Correctif : le corps reçoit le texte brut sur une ligne ({note_md}) ; le frontmatter
ne change pas.

Dry-run par défaut ; --apply pour écrire (sauvegarde .bak_u3l). Idempotent.
À lancer depuis la racine du vault.
"""
import py_compile
import shutil
import sys
from pathlib import Path

APPLY = "--apply" in sys.argv
F = Path("generator/inject_custom_events.py")

A1 = '## Note de cohérence\n{note}\n""".format('
N1 = '## Note de cohérence\n{note_md}\n""".format('
A2 = '        note=yaml_scalar(instance_data.get("note_coherence") or ""),\n'
N2 = A2 + '        note_md=" ".join(str(instance_data.get("note_coherence") or "").split()),   # U3l : texte brut pour le corps\n'

t = F.read_text(encoding="utf-8")
if N1 in t and N2 in t:
    sys.exit("= déjà appliqué")
for a in (A1, A2):
    if t.count(a) != 1:
        sys.exit(f"✗ ancre introuvable ou multiple ({t.count(a)}) :\n{a}")
print("+ modification prévue")
if APPLY:
    shutil.copy2(F, str(F) + ".bak_u3l")
    F.write_text(t.replace(A1, N1).replace(A2, N2), encoding="utf-8")
    py_compile.compile(str(F), doraise=True)
    print("✓ écrit (sauvegarde .bak_u3l), py_compile OK")
else:
    print("(dry-run : rien écrit ; relancer avec --apply)")
