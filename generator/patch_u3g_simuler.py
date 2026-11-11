#!/usr/bin/env python3
"""
patch_u3g_simuler.py — Ourrassol 2098 (11 nov. 2026)

U3g (generator/simuler_et_si.py) :
  1. Un événement daté dans l'année de mesure (ex. 2098.03, mesure « 2098 ») ne fait plus échouer la
     simulation : la mesure est ramenée à la fin de cette année (2098.12). Message sur stderr.
  2. « Fiches à relire » : « Centre », « Tous », « Toutes », « Santé », « Régénératif » rejoignent
     MOTS_GENERIQUES (ils produisaient 47 faux positifs pour « Centre Régénératif du Léman »).

Usage (racine du vault) : python3 generator/patch_u3g_simuler.py [--apply]   (.bak_u3g + py_compile)
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

FICHIER = Path("generator/simuler_et_si.py")

EDITS = [
    (
        '                   "Disparition", "Fin", "Naissance", "Création", "Dissolution"}\n',
        '                   "Disparition", "Fin", "Naissance", "Création", "Dissolution",\n'
        '                   # U3g (11 nov 2026) : mots trop courants dans les fiches du vault\n'
        '                   "Centre", "Tous", "Toutes", "Santé", "Régénératif"}\n',
        "mots génériques ajoutés",
    ),
    (
        '    if args.date < hyp["date"]:\n'
        '        sys.exit(f"✗ --date {args.date:g} antérieure à l\'apparition de l\'hypothèse ({hyp[\'date\']:g}).")\n',
        '    if args.date < hyp["date"] and int(args.date) == int(hyp["date"]):\n'
        '        # U3g : événement daté dans l\'année de mesure (2098.03, mesure 2098) -> fin de cette année\n'
        '        args.date = round(int(hyp["date"]) + 0.12, 2)\n'
        '        print(f"ℹ date de mesure ramenée à la fin de l\'année de l\'apparition : {args.date:g}", file=sys.stderr)\n'
        '    if args.date < hyp["date"]:\n'
        '        sys.exit(f"✗ --date {args.date:g} antérieure à l\'apparition de l\'hypothèse ({hyp[\'date\']:g}).")\n',
        "date de mesure ramenée à la fin de l'année",
    ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    print(f"patch_u3g — mode {'APPLY' if args.apply else 'DRY-RUN'}")
    if not FICHIER.exists():
        print(f"✗ {FICHIER} introuvable (lancer depuis la racine du vault)")
        sys.exit(1)
    texte = FICHIER.read_text(encoding="utf-8")
    nouveau, bloque = texte, False
    for ancien, neuf, nom in EDITS:
        n = nouveau.count(ancien)
        if neuf in nouveau:
            print(f"  · {nom} — déjà appliqué")
        elif n == 1:
            nouveau = nouveau.replace(ancien, neuf)
            print(f"  ✓ {nom}")
        else:
            print(f"  ✗ {nom} — {n} occurrence(s) de l'ancien texte (attendu : 1)")
            bloque = True
    if bloque:
        print("✗ rien n'est écrit.")
        sys.exit(1)
    if nouveau == texte:
        print("Rien à faire.")
        return
    if not args.apply:
        print("[DRY-RUN] 1 fichier serait modifié. Relancer avec --apply.")
        return
    shutil.copy2(FICHIER, str(FICHIER) + ".bak_u3g")
    FICHIER.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(FICHIER), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"✗ py_compile : {e}\n  Restaurer : cp {FICHIER}.bak_u3g {FICHIER}")
        sys.exit(1)
    print(f"  écrit : {FICHIER} (sauvegarde .bak_u3g)")
    print("Terminé. Relancer Flask si le GUI lance le simulateur en processus long.")


if __name__ == "__main__":
    main()
