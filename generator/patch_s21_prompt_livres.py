"""
patch_s21_prompt_livres.py — Ourrassol 2098 (S21, 30 octobre 2026)

Durcit le prompt d'extraction de veille_livres_api.py avec deux pièges
relevés à l'usage :
  1. une recommandation de l'auteur n'est pas une observation ;
  2. un grand programme d'État n'est pas marginal.

Le texte est inséré juste après la consigne « seulement des faits observés
qu'il rapporte. », avant les RÈGLES ABSOLUES. Rien d'autre n'est touché.

Usage (depuis la racine du vault) :
  python3 generator/patch_s21_prompt_livres.py            # aperçu
  python3 generator/patch_s21_prompt_livres.py --apply    # écrit, avec .bak
"""

import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/veille_livres_api.py")

ANCRE = (
    '        "seulement des faits observés qu\'il rapporte."\n'
    "    )\n"
)

AJOUT = (
    "    L.append(\"\")\n"
    "    L.append(\n"
    "        \"Deux pièges fréquents (S21) : 1) une recommandation, un appel ou \"\n"
    "        \"une proposition de l'auteur (« il faudrait », « les États \"\n"
    "        \"devraient », « nous proposons ») n'est PAS une observation, même \"\n"
    "        \"précise : écarte-la. 2) Un grand programme d'État, un plan \"\n"
    "        \"national ou un investissement massif déjà annoncé n'est PAS \"\n"
    "        \"marginal : c'est une tendance installée, pas un signal faible. \"\n"
    "        \"Seul un effet inattendu et encore marginal d'un tel programme, \"\n"
    "        \"rapporté dans l'extrait, peut en être un.\"\n"
    "    )\n"
)

MARQUE = "Deux pièges fréquents (S21)"


def main():
    appliquer = "--apply" in sys.argv
    if not CIBLE.exists():
        sys.exit(f"Introuvable : {CIBLE} (lancer depuis la racine du vault)")
    texte = CIBLE.read_text(encoding="utf-8")
    if MARQUE in texte:
        print("  · déjà appliqué, rien à faire.")
        return
    n = texte.count(ANCRE)
    if n != 1:
        sys.exit(f"  ⚠ ancre trouvée {n} fois (attendu 1) : fichier non modifié.")
    nouveau = texte.replace(ANCRE, ANCRE + AJOUT)
    print("  ✓ consigne des deux pièges insérée après « faits observés qu'il rapporte. »")
    if not appliquer:
        print("Aperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CIBLE, CIBLE.with_suffix(".py.bak"))
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"Écrit : {CIBLE} (sauvegarde {CIBLE.name}.bak)")


if __name__ == "__main__":
    main()
