#!/usr/bin/env python3
"""
patch_u3r_statistiques_citations_tronquees.py — Ourrassol 2098 (U3r, 11 novembre 2026)
======================================================================================
Extracteur d'événements : deux nouveaux motifs d'écart dans motif_non_evenement() (U3p) :
  - citation tronquée : elle contient « [...] », « […] » ou « … » (l'IA a recollé des
    morceaux de phrases ; la citation ne peut pas être exacte) ;
  - statistique de tendance : un verbe d'évolution chiffrée (« augmente de 22 », « a bondi de »,
    « a chuté de »…) accompagné d'une durée (« depuis 2040 », « en une décennie »,
    « en 10 ans »). Une évolution chiffrée sans durée (« la bourse a chuté de 30 % le 8 mars »)
    reste un événement.

Modifie generator/extraire_evenements_article.py (1 modification). Exige U3p appliqué.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3r_statistiques_citations_tronquees.py            # dry-run
  python3 generator/patch_u3r_statistiques_citations_tronquees.py --apply    # applique (.bak_u3r)
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "extraire_evenements_article.py"
TAG = "u3r"

ANCRE = "    # 1. année postérieure à l'article écrite dans la description\n"
NOUVEAU = '''    # 0. U3r : citation tronquée (passages recollés) ou statistique de tendance
    if _re.search(r"\\[\\s*(\\.\\.\\.|…)\\s*\\]|…|\\.\\.\\.", str(citation or "")):
        return "citation tronquée ([...] ou …) : passages recollés"
    if (_re.search(r" (augment\\w*|bondi|chute\\w*|baiss\\w*|progress\\w*|diminu\\w*|doubl\\w*|tripl\\w*) (de )?\\d", desc_n)
            and (" depuis " in desc_n or _re.search(r" en (une decennie|dix ans|\\d+ ans) ", desc_n))):
        return "statistique de tendance (évolution chiffrée sur une durée), pas un événement"
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ introuvable : {CIBLE}")
    src = CIBLE.read_text(encoding="utf-8")
    if "statistique de tendance" in src:
        print("= déjà appliqué, rien à faire")
        return
    if "def motif_non_evenement" not in src:
        sys.exit("✗ U3p n'est pas appliqué (motif_non_evenement absent)")
    n = src.count(ANCRE)
    if n != 1:
        sys.exit(f"✗ ancre trouvée {n} fois (attendu 1)")
    nouveau = src.replace(ANCRE, NOUVEAU + ANCRE)
    print(f"{CIBLE.name} : 1 modification prévue (+{len(nouveau.splitlines()) - len(src.splitlines())} lignes)")
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
