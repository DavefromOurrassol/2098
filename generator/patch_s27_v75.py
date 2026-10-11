#!/usr/bin/env python3
"""
patch_s27_v75.py — Ourrassol 2098 (S27, 10 octobre 2026)
=========================================================

Simulateur « et si ? » v7.4 -> v7.5 : avec `carte: non`, aucune zone ne disparaît.
Constat du test peste_pulmonaire_2043 (rupture) : 7 zones passées au statut
`disparu` alors que l'hypothèse est sans effet territorial ; une zone disparue
est un changement de carte déguisé (ses pays y restent rattachés).

1. Consigne IA : avec `carte: non`, interdiction du statut `disparu` pour une zone.
2. Filtre mécanique : toute proposition de statut `disparu` est écartée
   (listée dans les écartées), comme les propositions de carte.

Fichier : generator/simuler_et_si.py (.bak_v75)

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v75.py            # aperçu
    python3 generator/patch_s27_v75.py --apply    # écrit

Les réponses IA en cache sont revérifiées à chaque lecture : relancer le
simulateur SANS --refaire suffit pour appliquer le filtre (aucun appel payant).
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"

REMPLACEMENTS = [
    ("version", 'VERSION = "v7.4"', 'VERSION = "v7.5"'),

    ("consigne : pas de zone disparue",
     '''"\\"geographie\\": [] (aucun rattachement, aucune nouvelle zone, aucune partition).\\n")''',
     '''"\\"geographie\\": [] (aucun rattachement, aucune nouvelle zone, aucune partition), "
                      "et aucune zone ne passe au statut disparu (en_declin au plus).\\n")'''),

    ("filtre mécanique : statut disparu",
     '''            out[sc]["geographie"] = []
        if out[sc].get("geographie") and sc not in hyp["geographie"]:''',
     '''            out[sc]["geographie"] = []
        # V7.5 : une zone disparue est un changement de carte déguisé.
        if not hyp.get("carte", True) and out[sc].get("zones_statut"):
            disparues = [z for z in out[sc]["zones_statut"] if z.get("apres") == "disparu"]
            if disparues:
                out[sc]["ecartees"] = (out[sc].get("ecartees") or []) + [
                    f"statut de zone : {z['zone']} → disparu écarté, hypothèse sans effet territorial (`carte: non`)"
                    for z in disparues]
                out[sc]["zones_statut"] = [z for z in out[sc]["zones_statut"] if z.get("apres") != "disparu"]
        if out[sc].get("geographie") and sc not in hyp["geographie"]:'''),
]


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7.4 -> v7.5.")
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon : aperçu)")
    args = ap.parse_args()
    if not SIMU.exists():
        sys.exit(f"✗ Fichier introuvable : {SIMU}")
    simu = SIMU.read_text(encoding="utf-8")
    if 'VERSION = "v7.5"' in simu:
        sys.exit("✗ Patch déjà appliqué (v7.5). Rien à faire.")
    if 'VERSION = "v7.4"' not in simu:
        sys.exit("✗ La v7.4 n'est pas installée : appliquer d'abord patch_s27_v74.py.")
    erreurs = []
    print("simuler_et_si.py :")
    for libelle, ancien, nouveau in REMPLACEMENTS:
        n = simu.count(ancien)
        if n != 1:
            erreurs.append(f"{libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        simu = simu.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    try:
        compile(simu, str(SIMU), "exec")
    except SyntaxError as e:
        erreurs.append(f"simuler_et_si.py ne compilerait pas : {e}")
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    shutil.copy(SIMU, SIMU.with_name(SIMU.name + ".bak_v75"))
    SIMU.write_text(simu, encoding="utf-8")
    print("→ écrit : generator/simuler_et_si.py (sauvegarde simuler_et_si.py.bak_v75)")
    print("\nSimulateur passé en v7.5.")


if __name__ == "__main__":
    main()
