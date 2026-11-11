#!/usr/bin/env python3
"""
patch_u3x_filtre_plans_precision.py — Ourrassol 2098 (U3x, 11 novembre 2026)
============================================================================
Suite de U3p / U3r (extraire_evenements_article.py). Constat du 11 nov :
  - faux positif : « Lancement du programme Écoles Résilientes par l'OMS Étendue » (événement
    réel, en place depuis 2089) était écarté comme plan, parce que la règle « s'ouvre sur un
    plan / programme / débat » cherchait le mot dans les quatre premiers mots ;
  - trou : « Réduction de 45 % du taux de mortalité… en une décennie » (statistique) passait.

Corrections :
  1. la règle plan / programme / débat ne s'applique que si la description COMMENCE par ce nom
     (après les articles : « Plan de… », « Le programme… », « Débat sur… ») ;
  2. les noms et verbes de tendance « réduction », « hausse », « croissance », « recul »,
     « grimpe » rejoignent la liste du filtre « statistique de tendance » (toujours accompagnée
     d'une durée : « depuis 2040 », « en une décennie », « en 10 ans »).

Modifie generator/extraire_evenements_article.py (2 modifications). Exige U3p et U3r.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3x_filtre_plans_precision.py            # dry-run
  python3 generator/patch_u3x_filtre_plans_precision.py --apply    # applique (.bak_u3x)
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "extraire_evenements_article.py"
TAG = "u3x"

A1 = (r'    debut = " " + " ".join(desc_n.split()[:4]) + " "' + "\n"
      "    for d in _DEBUT_PLAN:\n"
      "        if d in debut:\n")
N1 = ('    mots = desc_n.split()   # U3x : le nom doit OUVRIR la description (après les articles)\n'
      '    while mots and mots[0] in ("le", "la", "l", "les", "un", "une", "du", "de", "des", "d"):\n'
      "        mots = mots[1:]\n"
      '    debut = " " + " ".join(mots[:3]) + " "\n'
      "    for d in _DEBUT_PLAN:\n"
      "        if debut.startswith(d):\n")

A2 = r"(augment\w*|bondi|chute\w*|baiss\w*|progress\w*|diminu\w*|doubl\w*|tripl\w*)"
N2 = r"(augment\w*|bondi|chute\w*|baiss\w*|progress\w*|diminu\w*|doubl\w*|tripl\w*|reduc\w*|hauss\w*|croiss\w*|recul\w*|grimp\w*)"

REMPLACEMENTS = [("règle plan / programme", A1, N1), ("statistiques de tendance", A2, N2)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ introuvable : {CIBLE}")
    src = CIBLE.read_text(encoding="utf-8")
    if "U3x : le nom doit OUVRIR" in src:
        print("= déjà appliqué, rien à faire")
        return
    if "def motif_non_evenement" not in src or "statistique de tendance" not in src:
        sys.exit("✗ U3p / U3r ne sont pas appliqués")
    for nom, ancre, _ in REMPLACEMENTS:
        n = src.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (attendu 1) : fichier modifié ?")
    nouveau = src
    for _, ancre, rempl in REMPLACEMENTS:
        nouveau = nouveau.replace(ancre, rempl)
    print(f"{CIBLE.name} : {len(REMPLACEMENTS)} modifications prévues "
          f"(+{len(nouveau.splitlines()) - len(src.splitlines())} lignes)")
    if not args.apply:
        print("dry-run : rien écrit. Relancer avec --apply.")
        return
    bak = CIBLE.with_name(CIBLE.name + f".bak_{TAG}")
    shutil.copy2(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    py_compile.compile(str(CIBLE), doraise=True)
    print(f"✓ appliqué ; sauvegarde {bak.name} ; py_compile OK")


if __name__ == "__main__":
    main()
