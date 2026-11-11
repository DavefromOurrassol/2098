#!/usr/bin/env python3
"""
patch_u3q_guillemets_citation.py — Ourrassol 2098 (U3q, 11 novembre 2026)
=========================================================================
Extracteur d'événements : les citations s'affichaient avec des guillemets doublés
(« « … » ») et des astérisques d'italique, parce que l'IA recopie les guillemets
englobants. Le script nettoie désormais la citation :
  - retire les astérisques ;
  - retire les guillemets englobants (« », “ ”, " ") tant qu'ils entourent TOUTE la
    citation (pas ceux qui encadrent seulement un passage interne) ;
la vérification mot pour mot est inchangée (elle ignore déjà la ponctuation).

Modifie generator/extraire_evenements_article.py (2 modifications).

USAGE (depuis la racine du vault)
  python3 generator/patch_u3q_guillemets_citation.py            # dry-run
  python3 generator/patch_u3q_guillemets_citation.py --apply    # applique (.bak_u3q)
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "extraire_evenements_article.py"
TAG = "u3q"

ANCRE_FONCTION = "def extraire(fichier, scenario, annee, mois, racine=RACINE_DEFAUT, _llm=appeler_llm):\n"
FONCTION = '''def _nettoyer_citation(s):
    """U3q : espaces normalisés, sans astérisques, sans guillemets englobant toute la citation."""
    s = " ".join(str(s or "").replace("*", "").split())
    paires = {"«": "»", "“": "”", '"': '"'}
    while len(s) >= 2 and s[0] in paires and s[-1] == paires[s[0]]:
        interieur = s[1:-1]
        profondeur = 0
        englobant = True
        for c in interieur:
            if c in "«“":
                profondeur += 1
            elif c in "»”":
                profondeur -= 1
                if profondeur < 0:   # le guillemet fermant du début est dans le texte : pas englobant
                    englobant = False
                    break
        if not englobant or profondeur != 0:
            break
        s = interieur.strip()
    return s


'''

ANCRE_CIT = '        cit = " ".join(str(ev.get("citation") or "").split())\n'
NOUVEAU_CIT = '        cit = _nettoyer_citation(ev.get("citation"))\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ introuvable : {CIBLE}")
    src = CIBLE.read_text(encoding="utf-8")
    if "_nettoyer_citation" in src:
        print("= déjà appliqué, rien à faire")
        return
    for nom, ancre in (("fonction", ANCRE_FONCTION), ("citation", ANCRE_CIT)):
        n = src.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (attendu 1)")
    nouveau = src.replace(ANCRE_FONCTION, FONCTION + ANCRE_FONCTION).replace(ANCRE_CIT, NOUVEAU_CIT)
    print(f"{CIBLE.name} : 2 modifications prévues (+{len(nouveau.splitlines()) - len(src.splitlines())} lignes)")
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
