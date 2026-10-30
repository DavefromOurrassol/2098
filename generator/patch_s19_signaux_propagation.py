"""
patch_s19_signaux_propagation.py — Ourrassol 2098 (S19, 30 octobre 2026)

Décision du 30 oct : les signaux faibles se propagent par la matrice
(propagation_via_matrice: true), puisqu'un signal faible transforme par
combinaison. Effet mesuré sur les 10 signaux existants : 1,1 point au plus.

Modifie generator/inject_custom_signals.py :
  1. exemple JSON du prompt : false -> true
  2. consigne du prompt : « false SAUF SI… » -> « toujours true »
  3. défauts du code (écriture de la fiche, développement) : False -> True

Usage (depuis la racine du vault) :
  python3 patch_s19_signaux_propagation.py            # aperçu, rien n'est écrit
  python3 patch_s19_signaux_propagation.py --apply    # écrit, avec .bak
"""

import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/inject_custom_signals.py")

REMPLACEMENTS = [
    (
        "exemple JSON",
        '  "propagation_via_matrice": false,\n',
        '  "propagation_via_matrice": true,\n',
    ),
    (
        "consigne",
        '"propagation_via_matrice" : false SAUF SI ce signal touche une dynamique\n'
        "véritablement structurelle et durable (rare pour un signal faible) — en\n"
        "cas de doute, false.\n",
        '"propagation_via_matrice" : toujours true (règle du 30 octobre 2026 : un\n'
        "signal faible transforme par combinaison, son effet se diffuse donc dans\n"
        "le réseau des variables ; le moteur en limite l'ampleur).\n",
    ),
    (
        "défaut écriture fiche",
        'str(bool(imp.get("propagation_via_matrice", False))).lower()',
        'str(bool(imp.get("propagation_via_matrice", True))).lower()',
    ),
    (
        "défaut développement",
        '"propagation_via_matrice": bool(develop.get("propagation_via_matrice", False))',
        '"propagation_via_matrice": bool(develop.get("propagation_via_matrice", True))',
    ),
]


def main():
    appliquer = "--apply" in sys.argv
    if not CIBLE.exists():
        sys.exit(f"Introuvable : {CIBLE} (lancer depuis la racine du vault)")
    texte = CIBLE.read_text(encoding="utf-8")
    nouveau = texte
    erreurs = 0
    for nom, avant, apres in REMPLACEMENTS:
        n = nouveau.count(avant)
        if n == 1:
            nouveau = nouveau.replace(avant, apres)
            print(f"  ✓ {nom}")
        elif nouveau.count(apres) >= 1 and n == 0:
            print(f"  · {nom} : déjà appliqué")
        else:
            print(f"  ⚠ {nom} : trouvé {n} fois (attendu 1), rien changé")
            erreurs += 1
    if erreurs:
        sys.exit("Arrêt : au moins un remplacement ambigu ou absent, fichier non modifié.")
    if nouveau == texte:
        print("Rien à faire.")
        return
    if not appliquer:
        print("Aperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CIBLE, CIBLE.with_suffix(".py.bak"))
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"Écrit : {CIBLE} (sauvegarde {CIBLE.name}.bak)")


if __name__ == "__main__":
    main()
