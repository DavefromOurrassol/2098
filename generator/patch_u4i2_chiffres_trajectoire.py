#!/usr/bin/env python3
"""
patch_u4i2_chiffres_trajectoire.py — Ourrassol 2098 (22 novembre 2026)
======================================================================

Suite de U4i (à appliquer APRÈS lui). Test du 22 nov en --dry-run : l'IA a mis
le chiffre de la source dans `evenement_cle` (« 1 adulte américain sur 10 (1 sur
5 chez les moins de 30 ans) consulte… », 19 mots -> variable en needs_review), et
le registre contient déjà un chiffre inventé dans ce champ (« 30% des moins de
30 ans américains suivent ChatwithGod 2027 », signal du 7 nov).

Règle : dans `evolution` et `evenement_cle`, AUCUN chiffre sauf l'année. Les
chiffres vont dans `contexte_injection`, contrôlé par U4i.

Cible : generator/inject_custom_signals.py
  1. CONSIGNE_CHIFFRES complétée (evolution, evenement_cle).
  2. controle_chiffres_trajectoire() : même repérage des nombres que U4i (années,
     noms comme Kharg-9 ou 5G, forces signées ignorés) ; un nombre dans ces deux
     champs = problème de validation -> relance, puis needs_review.
  3. Consigne de la relance : retirer le chiffre, ne pas raccourcir autour.

Usage (depuis la racine du vault) :
    python3 generator/patch_u4i2_chiffres_trajectoire.py           # dry-run
    python3 generator/patch_u4i2_chiffres_trajectoire.py --apply   # écrit (.bak_u4i2)
"""

import argparse
import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/inject_custom_signals.py")
TAG = "u4i2"

R1_ANCIEN = '''    "donne aucun chiffre, n'en écris aucun.\\n"
)
'''
R1_NOUVEAU = '''    "donne aucun chiffre, n'en écris aucun.\\n"
    "Dans `evolution` et `evenement_cle` (4 à 11 mots) : AUCUN chiffre, sauf l'année de "
    "`evenement_cle`. Un chiffre de la source va dans `contexte_injection`, jamais là.\\n"   # U4i2
)
'''

R2_ANCIEN = '''    return issues

# Bornes du champ optionnel'''
R2_NOUVEAU = '''    return issues


def controle_chiffres_trajectoire(yaml_text):
    """U4i2 : `evolution` et `evenement_cle` ne portent aucun chiffre hors l'année.
    Retourne une liste de problèmes (un YAML illisible est signalé ailleurs)."""
    try:
        entree = (yaml.safe_load("signal_to_state:\\n" + str(yaml_text or "")) or {}).get("signal_to_state")[0]
        scenarios = entree.get("scenarios") or {}
    except Exception:  # noqa: BLE001 -- déjà signalé par validate_signal_block()
        return []
    issues = []
    for scen, data in scenarios.items():
        for champ in ("evolution", "evenement_cle"):
            nombres = list(dict.fromkeys(_nombres((data or {}).get(champ))))
            if nombres:
                issues.append(
                    f"[{scen}] {champ} : chiffre(s) {', '.join(nombres)} interdit(s) dans ce champ "
                    f"(seule l'année est permise) -- retirer le chiffre ; il a sa place dans contexte_injection"
                )
    return issues


# Bornes du champ optionnel'''

R3_ANCIEN = '''                issues = list(issues) + controle_chiffres(develop, [idea_text] + contraintes)   # U4i
'''
R3_NOUVEAU = '''                issues = list(issues) + controle_chiffres(develop, [idea_text] + contraintes)   # U4i
                issues += controle_chiffres_trajectoire(yaml_text)   # U4i2
'''

R4_ANCIEN = '''  retire tout chiffre de ce champ.
"""
'''
R4_NOUVEAU = '''  retire tout chiffre de ce champ.
- Si un point concerne un « chiffre interdit » dans `evolution` ou
  `evenement_cle` (U4i2), retire ce chiffre et sa population (« 1 adulte sur
  10 », « 30 % des… ») : garde acteur + action + lieu + année. Ne raccourcis
  pas la phrase en gardant le chiffre.
"""
'''

REMPLACEMENTS = [
    ("1. CONSIGNE_CHIFFRES : evolution et evenement_cle", R1_ANCIEN, R1_NOUVEAU),
    ("2. controle_chiffres_trajectoire()", R2_ANCIEN, R2_NOUVEAU),
    ("3. contrôle branché sur la validation", R3_ANCIEN, R3_NOUVEAU),
    ("4. consigne de la relance de correction", R4_ANCIEN, R4_NOUVEAU),
]


def main():
    ap = argparse.ArgumentParser(description="Patch U4i2 : aucun chiffre hors année dans la trajectoire.")
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon dry-run)")
    args = ap.parse_args()

    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault.")
    texte = CIBLE.read_text(encoding="utf-8")
    if "controle_chiffres(" not in texte:
        sys.exit("✗ U4i n'est pas appliqué : appliquer patch_u4i_chiffres_contraintes.py d'abord.")
    if "controle_chiffres_trajectoire(" in texte:
        sys.exit("✗ U4i2 déjà appliqué : rien à faire.")

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
