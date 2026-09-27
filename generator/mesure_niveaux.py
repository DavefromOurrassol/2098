#!/usr/bin/env python3
"""
mesure_niveaux.py — Ourrassol 2098
==================================

Photo des niveaux de 2098 (12 variables × 6 scénarios, après moteur
dynamique) pour comparer AVANT / APRÈS un changement de calibration
(27 septembre 2026, chantier persistance des instances). Lecture seule :
build_snapshot() en dry_run, rien n'est écrit dans le vault.

USAGE
-----
    python3 mesure_niveaux.py --sauver avant.json      # photo avant le changement
    python3 mesure_niveaux.py --comparer avant.json    # après : écarts variable par variable
"""

import argparse
import contextlib
import io
import json
from datetime import datetime

from loader import VALID_SCENARIOS, VALID_VARS
from snapshot import build_snapshot


def mesurer():
    niveaux = {}
    for scen in VALID_SCENARIOS:
        with contextlib.redirect_stdout(io.StringIO()):  # snapshot est bavard
            snap = build_snapshot(scen, dry_run=True)
        niveaux[scen] = {}
        for v in VALID_VARS:
            try:
                niveaux[scen][v] = float(snap["variable_states"][v].get("level"))
            except (TypeError, ValueError, KeyError):
                niveaux[scen][v] = None
    return niveaux


def comparer(avant, apres, seuil):
    total, bouges = 0, 0
    for scen in VALID_SCENARIOS:
        lignes = []
        for v in VALID_VARS:
            a, b = (avant.get(scen) or {}).get(v), (apres.get(scen) or {}).get(v)
            if a is None or b is None:
                continue
            total += 1
            if abs(b - a) >= seuil:
                bouges += 1
                lignes.append((abs(b - a), f"    {v:<36} {a:6.1f} → {b:6.1f}   ({b - a:+.1f})"))
        print(f"\n{scen}" + ("" if lignes else "  — aucun écart"))
        for _, l in sorted(lignes, reverse=True):
            print(l)
    print(f"\n{bouges}/{total} niveaux ont bougé d'au moins {seuil} point.")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sauver", metavar="FICHIER")
    g.add_argument("--comparer", metavar="FICHIER")
    ap.add_argument("--seuil", type=float, default=0.1, help="écart minimal affiché (défaut 0.1)")
    args = ap.parse_args()

    niveaux = mesurer()
    if args.sauver:
        with open(args.sauver, "w", encoding="utf-8") as f:
            json.dump({"date": datetime.now().isoformat(timespec="seconds"), "niveaux": niveaux},
                      f, ensure_ascii=False, indent=2)
        print(f"Photo enregistrée : {args.sauver} ({len(niveaux)} scénarios × {len(VALID_VARS)} variables)")
    else:
        with open(args.comparer, encoding="utf-8") as f:
            avant = json.load(f)["niveaux"]
        comparer(avant, niveaux, args.seuil)


if __name__ == "__main__":
    main()
