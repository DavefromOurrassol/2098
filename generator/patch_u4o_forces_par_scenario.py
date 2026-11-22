#!/usr/bin/env python3
"""
patch_u4o_forces_par_scenario.py — Ourrassol 2098 (22 novembre 2026)
====================================================================

B9 wild cards, reste a) : forces par scénario dans ✨ Proposer. Le moteur, la
normalisation et la vérification acceptent depuis U4f (15 nov) un `delta_level`
en dictionnaire par scénario pour TOUT événement, mais le prompt ne l'expliquait
qu'aux wild cards : pour un événement ordinaire, l'IA donnait toujours une seule
force, même quand l'élément frappe un monde bien plus qu'un autre.

Cible : generator/hypothese_depuis_texte.py
  1. Prompt (règle générale) : un dictionnaire par scénario est permis quand
     l'intensité diffère NETTEMENT d'un scénario à l'autre, limité aux scénarios
     de l'hypothèse, avec la raison dans "justification" ; sinon un seul nombre ;
     un signal a toujours un seul nombre.
  2. normaliser_proposition() : pour un SIGNAL, un dictionnaire de forces est
     ramené à sa plus forte valeur, avec un ⚠ (inject_custom_signals.py exige
     une force par variable, identique dans les 6 scénarios).

Usage (depuis la racine du vault) :
    python3 generator/patch_u4o_forces_par_scenario.py           # dry-run
    python3 generator/patch_u4o_forces_par_scenario.py --apply   # écrit (.bak_u4o)
"""

import argparse
import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/hypothese_depuis_texte.py")
TAG = "u4o"

REMPLACEMENTS = [
    ("prompt : force par scénario expliquée",
     '  - "delta_level" = FORCE, entier de 1 à {FORCE_MAX} ({FORCE_MAX} = choc majeur et mondial\n'
     '    sur ce domaine ; 5 = effet secondaire net).\n',
     '  - "delta_level" = FORCE, entier de 1 à {FORCE_MAX} ({FORCE_MAX} = choc majeur et mondial\n'
     '    sur ce domaine ; 5 = effet secondaire net).\n'
     '    Si l\'élément touche plusieurs scénarios avec une intensité NETTEMENT différente (un monde\n'
     '    où ce domaine est déjà fragile, un autre qui l\'encaisse), "delta_level" peut être un\n'
     '    dictionnaire par scénario, limité aux scénarios de l\'hypothèse\n'
     '    ({{"breakdown": 18, "policy_reform": 8}}) : dis pourquoi dans "justification". Sinon, un\n'
     '    seul nombre (pas d\'écart inventé). Un signal a toujours UN seul nombre.\n'),
    ("normalisation : un signal garde une seule force",
     '        dl = imp.get("delta_level")\n'
     '        if isinstance(dl, dict):   # U4f : force par scénario\n',
     '        dl = imp.get("delta_level")\n'
     '        if est_signal and isinstance(dl, dict):   # U4o : un signal a UNE force par variable\n'
     '            nums = [abs(float(v)) for v in dl.values() if isinstance(v, (int, float))]\n'
     '            av.append(f"{var} : un signal a une seule force -> la plus forte des valeurs proposées "\n'
     '                      f"({max(nums):g})" if nums else f"{var} : forces par scénario illisibles")\n'
     '            dl = max(nums) if nums else None\n'
     '        if isinstance(dl, dict):   # U4f : force par scénario\n'),
]


def main():
    ap = argparse.ArgumentParser(description="Patch U4o : forces par scénario dans ✨ Proposer.")
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon dry-run)")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault.")
    texte = CIBLE.read_text(encoding="utf-8")
    if "Un signal a toujours UN seul nombre" in texte:
        sys.exit("✗ U4o déjà appliqué : rien à faire.")
    nouveau, ok = texte, True
    for nom, ancien, neuf in REMPLACEMENTS:
        n = nouveau.count(ancien)
        if n != 1:
            print(f"✗ {nom} : ancre trouvée {n} fois (attendu 1)")
            ok = False
            continue
        nouveau = nouveau.replace(ancien, neuf)
        print(f"✓ {nom}")
    if not ok:
        sys.exit("✗ Patch non appliqué (fichier différent de celui attendu).")
    try:
        compile(nouveau, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas : {e}")
    print("✓ Le fichier patché compile.")
    if not args.apply:
        print("\n(dry-run) Rien n'est écrit. Relancer avec --apply.")
        return
    shutil.copy(CIBLE, CIBLE.with_name(CIBLE.name + f".bak_{TAG}"))
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"\n→ {CIBLE} patché (sauvegarde {CIBLE.name}.bak_{TAG}).")


if __name__ == "__main__":
    main()
