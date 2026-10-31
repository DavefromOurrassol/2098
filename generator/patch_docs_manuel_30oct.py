"""
patch_docs_manuel_30oct.py — Ourrassol 2098 (30 octobre 2026)

Corrige sur place les passages de USER_MANUAL_COMPLET.md rendus faux par la
session du 30 oct (rien d'autre n'est touché) :
  1. §3 inject_custom_signals.py : propagation_via_matrice « recommandé à
     false » -> toujours true ;
  2. §3ter moteur : « (défaut des signaux faibles) » -> plus le cas ;
  3. §3quater veille_livres_api.py : mention de la consigne des deux pièges ;
  4. §7 routes API : /api/yaml/append garde l'en-tête de la file.

Usage (depuis la racine du vault) :
  python3 generator/patch_docs_manuel_30oct.py            # aperçu
  python3 generator/patch_docs_manuel_30oct.py --apply    # écrit, avec .bak
"""

import shutil
import sys
from pathlib import Path

CIBLE = Path("documentation/USER_MANUAL_COMPLET.md")

REMPLACEMENTS = [
    (
        "§3 inject_custom_signals.py",
        "  et une `polarite` ±1 **par scénario** ; `propagation_via_matrice` recommandé à\n"
        "  `false`.",
        "  et une `polarite` ±1 **par scénario** ; `propagation_via_matrice` toujours\n"
        "  `true` depuis le 30 oct 2026 (consigne et défaut du code ; le signal se\n"
        "  diffuse dans le réseau, voir §3ter).",
    ),
    (
        "§3ter moteur",
        "- Un choc `propagation_via_matrice: false` n'agit que sur sa variable (défaut des\n"
        "  signaux faibles).",
        "- Un choc `propagation_via_matrice: false` n'agit que sur sa variable. Les\n"
        "  signaux faibles sont tous à `true` depuis le 30 oct 2026 (effet mesuré :\n"
        "  1,1 point au plus ; référence `documentation/niveaux_avant_s19_signaux.json`).",
    ),
    (
        "§3quater veille_livres_api.py",
        "  `livre: <titre>, p. N — « citation exacte »`) ; 3) signal rejeté si la page n'a pas",
        "  `livre: <titre>, p. N — « citation exacte »` ; consigne : une recommandation\n"
        "  de l'auteur n'est pas une observation, un grand programme d'État n'est pas\n"
        "  marginal) ; 3) signal rejeté si la page n'a pas",
    ),
    (
        "§7 /api/yaml/append",
        "formulaire, ajout à une file. |",
        "formulaire, ajout à une file (l'en-tête de commentaires de la file est conservé). |",
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
        elif n == 0 and apres in nouveau:
            print(f"  · {nom} : déjà appliqué")
        else:
            print(f"  ⚠ {nom} : trouvé {n} fois (attendu 1)")
            erreurs += 1
    if erreurs:
        sys.exit("Arrêt : fichier non modifié.")
    if nouveau == texte:
        print("Rien à faire.")
        return
    if not appliquer:
        print("Aperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CIBLE, CIBLE.with_suffix(".md.bak"))
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"Écrit : {CIBLE} (sauvegarde {CIBLE.name}.bak)")


if __name__ == "__main__":
    main()
