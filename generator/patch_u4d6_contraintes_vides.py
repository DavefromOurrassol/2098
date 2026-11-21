#!/usr/bin/env python3
"""
patch_u4d6_contraintes_vides.py — Ourrassol 2098 (21 nov 2026)

U4d6 : ✨ Proposer retire les « contraintes » qui ne disent rien : une date seule
(« En 2058. », « vers 2058 », « 2058.03 ») ou la ligne « Scénarios : … » de l'idée,
que l'IA recopie parfois comme fait imposé (Zéro-R, 21 nov). Chaque retrait est
signalé par un avertissement. La date et les scénarios restent dans le bloc.

Fichier touché : generator/hypothese_depuis_texte.py (normaliser_proposition)

Usage (depuis la racine du vault) :
    python3 generator/patch_u4d6_contraintes_vides.py           # dry-run
    python3 generator/patch_u4d6_contraintes_vides.py --apply   # écrit (.bak_u4d6)
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/hypothese_depuis_texte.py")
TAG = "U4d6"

AVANT = '''    contraintes = [" ".join(str(c).split()) for c in contraintes if str(c).strip()][:4]
    if contraintes:
        h["contraintes"] = contraintes
'''

APRES = '''    contraintes = [" ".join(str(c).split()) for c in contraintes if str(c).strip()]
    gardees = []   # U4d6 : une date seule ou la ligne « Scénarios : … » n'est pas un fait imposé
    for c in contraintes:
        if re.fullmatch(r"(?i)(en|vers|dès|d[eè]s|à partir de|d'ici)?\\s*\\d{4}(\\.\\d{1,2})?\\s*\\.?", c) \\
                or re.match(r"(?i)sc[ée]narios?\\s*:", c):
            av.append(f"contrainte sans fait retirée : {c!r}")
        else:
            gardees.append(c)
    contraintes = gardees[:4]
    if contraintes:
        h["contraintes"] = contraintes
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault")
    texte = CIBLE.read_text(encoding="utf-8")
    if "# U4d6" in texte:
        sys.exit(f"✓ {TAG} déjà appliqué, rien à faire")
    n = texte.count(AVANT)
    if n != 1:
        sys.exit(f"✗ ancre « contraintes de normaliser_proposition() » trouvée {n} fois (1 attendue) : rien n'est écrit")
    nouveau = texte.replace(AVANT, APRES)
    print(f"[{TAG}] {CIBLE} : contraintes réduites à une date ou à « Scénarios : … » retirées")
    print(f"[{TAG}] {len(texte.splitlines())} -> {len(nouveau.splitlines())} lignes")
    if not args.apply:
        print(f"[{TAG}] dry-run : relancer avec --apply pour écrire")
        return
    bak = CIBLE.with_name(CIBLE.name + ".bak_u4d6")
    shutil.copy(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(CIBLE), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy(bak, CIBLE)
        sys.exit(f"✗ syntaxe invalide, fichier restauré : {e}")
    print(f"✓ [{TAG}] appliqué (sauvegarde {bak.name})")


if __name__ == "__main__":
    main()
