#!/usr/bin/env python3
"""
patch_u4j_polarites_couvertes.py — Ourrassol 2098 (22 novembre 2026)
====================================================================

B9 « forces par scénario dans ✨ Proposer », volet polarités. Constat du 22 nov
(Zéro-R, new_sustainability + policy_reform) : l'IA a donné une polarité aux 6
scénarios, dont 4 hors de l'hypothèse ; ✨ Proposer les gardait (et complétait
même une polarité manquante à 1 pour les 6). Bruit à nettoyer à la main.

Le simulateur ne lit la polarité QUE pour les scénarios de l'hypothèse
(verifier_hypothese : `for s in scen`) : un dictionnaire limité à ces
scénarios est valide.

Cible : generator/hypothese_depuis_texte.py
  1. Prompt : un dictionnaire de polarités couvre SEULEMENT les scénarios de
     l'hypothèse (les 6 si « tous ») ; un seul nombre si le sens est le même.
  2. normaliser_proposition() : polarités hors des scénarios de l'hypothèse
     retirées (une ⚠ unique les nomme) ; une polarité manquante n'est complétée
     que pour les scénarios couverts ; un seul sens -> un seul nombre (déjà fait).

Usage (depuis la racine du vault) :
    python3 generator/patch_u4j_polarites_couvertes.py           # dry-run
    python3 generator/patch_u4j_polarites_couvertes.py --apply   # écrit (.bak_u4j)
"""

import argparse
import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/hypothese_depuis_texte.py")
TAG = "u4j"

REMPLACEMENTS = [
    ("1a. prompt wild card : delta_level par scénario",
     '(comme polarite, les 6 "',
     '(comme polarite, seulement les "'),
    ("1b. prompt wild card : suite de la phrase",
     'f"scénarios) : {se.WILD_CARD_FORCE[0]}',
     'f"scénarios de l\'hypothèse) : {se.WILD_CARD_FORCE[0]}'),
    ("1c. prompt : règle générale des polarités",
     '...}} couvrant les 6 scénarios.\n',
     '...}} couvrant SEULEMENT les scénarios de l\'hypothèse (les 6 si "tous") ; si le sens\n'
     '    est le même partout, un seul nombre.\n'),
    ("2a. compteur des polarités hors hypothèse",
     '    impacts, vues = [], set()\n',
     '    impacts, vues = [], set()\n'
     '    hors_pol = set()   # U4j : polarités données hors des scénarios de l\'hypothèse\n'),
    ("2b. polarités limitées aux scénarios couverts",
     '''        if isinstance(pol, dict):
            pol = {s: (1 if str(v).strip().lstrip("+") == "1" else -1) for s, v in pol.items() if s in se.SCENARIOS}
            manquants = [s for s in se.SCENARIOS if s not in pol]
''',
     '''        if isinstance(pol, dict):
            couverts_pol = list(se.SCENARIOS) if scen == "tous" else list(scen)   # U4j
            hors_pol.update(s for s in pol if s in se.SCENARIOS and s not in couverts_pol)
            pol = {s: (1 if str(v).strip().lstrip("+") == "1" else -1) for s, v in pol.items() if s in couverts_pol}
            manquants = [s for s in couverts_pol if s not in pol]
'''),
    ("2c. avertissement unique",
     '    if len(impacts) > MAX_IMPACTS:\n',
     '    if hors_pol:   # U4j\n'
     '        av.append("polarités données pour des scénarios hors de l\'hypothèse, retirées : "\n'
     '                  + ", ".join(s for s in se.SCENARIOS if s in hors_pol))\n'
     '    if len(impacts) > MAX_IMPACTS:\n'),
]


def main():
    ap = argparse.ArgumentParser(description="Patch U4j : polarités limitées aux scénarios de l'hypothèse.")
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon dry-run)")
    args = ap.parse_args()

    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault.")
    texte = CIBLE.read_text(encoding="utf-8")
    if "hors_pol" in texte:
        sys.exit("✗ U4j déjà appliqué : rien à faire.")

    nouveau = texte
    ok = True
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
    bak = CIBLE.with_name(CIBLE.name + f".bak_{TAG}")
    shutil.copy(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"\n→ {CIBLE} patché (sauvegarde {bak.name}).")


if __name__ == "__main__":
    main()
