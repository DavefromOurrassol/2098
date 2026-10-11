#!/usr/bin/env python3
"""
patch_s27_v791.py — Ourrassol 2098 (S27, 10 octobre 2026)
==========================================================

Simulateur « et si ? » v7.9 -> v7.9.1 (finitions du contrôle des relations) :
1. Les corrections automatiques d'une relation ne sont listées que si la
   relation est finalement GARDÉE (avant : listées aussi pour une relation
   écartée ensuite, ex. « déjà présente »).
2. Grammaire : « … sont des zones » quand les deux slugs sont des zones.

Fichier : generator/simuler_et_si.py (.bak_v791). Aucun appel payant :
relancer sans --refaire suffit.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v791.py            # aperçu
    python3 generator/patch_s27_v791.py --apply    # écrit
"""

import argparse
import shutil
import sys
from pathlib import Path

SIMU = Path(__file__).resolve().parent.parent / "generator" / "simuler_et_si.py"

REMPLACEMENTS = [
    ("version", 'VERSION = "v7.9"', 'VERSION = "v7.9.1"'),
    ("corrections propres à la relation",
     '''        # zone employée comme entité signalée clairement.
        def _entite(slug):''',
     '''        # zone employée comme entité signalée clairement.
        corr_r = []   # V7.9.1 : listées seulement si la relation est gardée
        def _entite(slug):'''),
    ("complément de slug",
     '''                corrigees.append(f"relation : {slug!r} complété en {cands[0]!r}")''',
     '''                corr_r.append(f"relation : {slug!r} complété en {cands[0]!r}")'''),
    ("grammaire zones",
     '''                ecartees.append(f"relation {r.get('a')} / {r.get('b')} : {', '.join(map(repr, zones_vues))} "
                                f"est une zone (une relation relie deux entités)")''',
     '''                ecartees.append(f"relation {r.get('a')} / {r.get('b')} : {' et '.join(map(repr, zones_vues))} "
                                f"{'sont des zones' if len(zones_vues) > 1 else 'est une zone'} "
                                f"(une relation relie deux entités)")'''),
    ("action absente",
     '''            corrigees.append(f"relation {a['slug']} / {b['slug']} : action absente -> nouvelle")''',
     '''            corr_r.append(f"relation {a['slug']} / {b['slug']} : action absente -> nouvelle")'''),
    ("renforcée",
     '''            corrigees.append(f"relation {a['slug']} / {b['slug']} : renforcée -> nouvelle (absente du vault)")''',
     '''            corr_r.append(f"relation {a['slug']} / {b['slug']} : renforcée -> nouvelle (absente du vault)")'''),
    ("corrections ajoutées à la relation gardée",
     '''        rel.append({"a": a["slug"], "a_nom": a.get("name"), "b": b["slug"], "b_nom": b.get("name"),''',
     '''        corrigees.extend(corr_r)
        rel.append({"a": a["slug"], "a_nom": a.get("name"), "b": b["slug"], "b_nom": b.get("name"),'''),
]


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7.9 -> v7.9.1.")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not SIMU.exists():
        sys.exit(f"✗ Fichier introuvable : {SIMU}")
    txt = SIMU.read_text(encoding="utf-8")
    if 'VERSION = "v7.9.1"' in txt:
        sys.exit("✗ Patch déjà appliqué (v7.9.1). Rien à faire.")
    if 'VERSION = "v7.9"' not in txt:
        sys.exit("✗ La v7.9 n'est pas installée : appliquer d'abord patch_s27_v79.py.")
    erreurs = []
    print("simuler_et_si.py :")
    for libelle, ancien, nouveau in REMPLACEMENTS:
        n = txt.count(ancien)
        if n != 1:
            erreurs.append(f"{libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        txt = txt.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    try:
        compile(txt, str(SIMU), "exec")
    except SyntaxError as e:
        erreurs.append(f"ne compilerait pas : {e}")
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    shutil.copy(SIMU, SIMU.with_name(SIMU.name + ".bak_v791"))
    SIMU.write_text(txt, encoding="utf-8")
    print("→ écrit : generator/simuler_et_si.py (sauvegarde simuler_et_si.py.bak_v791)")
    print("\nSimulateur passé en v7.9.1.")


if __name__ == "__main__":
    main()
