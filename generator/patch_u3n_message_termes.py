#!/usr/bin/env python3
"""
patch_u3n_message_termes.py — Ourrassol 2098 (U3n, 11 novembre 2026)

Défaut : « Aucun pays ni nom propre à chercher » s'affichait aussi quand des termes ÉTAIENT
cherchés mais qu'aucune fiche ne les citait. Désormais :
  - termes extraits, aucune fiche ne les cite -> « Aucune fiche ne cite les termes cherchés (…) »
  - aucun terme extrait                       -> message d'origine inchangé
Le motif ne parle plus d'« hypothèse mondiale » (vrai aussi pour une hypothèse locale).

Dry-run par défaut ; --apply pour écrire (sauvegarde .bak_u3n). Idempotent.
À lancer depuis la racine du vault.
"""
import py_compile
import shutil
import sys
from pathlib import Path

APPLY = "--apply" in sys.argv
F = Path("generator/simuler_et_si.py")

ANCIEN = '''        _etape(E, "Fiches à relire", "Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche",
               motif="une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, "
'''
NEUF = '''        _etape(E, "Fiches à relire",
               (f"Aucune fiche ne cite les termes cherchés ({', '.join(sorted(termes)[:8])}"
                + (" …" if len(termes) > 8 else "") + ") : la recherche par mots ne trouve rien")   # U3n
               if termes else
               "Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche",
               motif="une hypothèse peut contredire des fiches sans les nommer : relecture IA ci-dessous, "
'''

t = F.read_text(encoding="utf-8")
if NEUF in t:
    sys.exit("= déjà appliqué")
if t.count(ANCIEN) != 1:
    sys.exit(f"✗ ancre introuvable ou multiple ({t.count(ANCIEN)})")
print("+ modification prévue")
if APPLY:
    shutil.copy2(F, str(F) + ".bak_u3n")
    F.write_text(t.replace(ANCIEN, NEUF), encoding="utf-8")
    py_compile.compile(str(F), doraise=True)
    print("✓ écrit (sauvegarde .bak_u3n), py_compile OK")
else:
    print("(dry-run : rien écrit ; relancer avec --apply)")
