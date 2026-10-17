#!/usr/bin/env python3
"""
patch_s27_reste_titre.py — Ourrassol 2098 (S27, 17 octobre 2026)
================================================================

appliquer_et_si.py, check-list « reste à faire » : le titre d'un article sans
champ `titre` dans son frontmatter est lu dans le texte (premier titre « # »,
sinon première ligne non vide), au lieu d'afficher le nom du fichier.
À appliquer après patch_s27_reste_a_faire.py. Sauvegarde .bak_reste_titre.
Refuse un second passage.

USAGE (depuis la racine du vault)
    python3 generator/patch_s27_reste_titre.py
"""

import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "appliquer_et_si.py"
MARQUEUR = "def _titre_article("
ANCRE_1 = "def _articles_concernes(sc, entites, zones):\n"
NOUVEAU_1 = r'''def _titre_article(fm, corps, defaut):
    """Titre d'un article : frontmatter, sinon premier « # » du texte, sinon première ligne non vide."""
    if fm.get("titre") or fm.get("title"):
        return str(fm.get("titre") or fm.get("title")).strip()
    lignes = [l.strip() for l in corps.split("\n") if l.strip()]
    for l in lignes:
        if re.match(r"^#\s+", l):
            return re.sub(r"^#\s+", "", l).strip()
    if lignes:
        return re.sub(r"^[#*\s]+|[*\s]+$", "", lignes[0]) or defaut
    return defaut


def _articles_concernes(sc, entites, zones):
'''
ANCRE_2 = '            titre = fm.get("titre") or fm.get("title") or p.stem\n'
NOUVEAU_2 = '            titre = _titre_article(fm, d[3], p.stem)\n'


def main():
    texte = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit("✗ patch déjà appliqué : rien fait.")
    if "def ecrire_reste_a_faire(" not in texte:
        sys.exit("✗ appliquer d'abord patch_s27_reste_a_faire.py : rien fait.")
    for a in (ANCRE_1, ANCRE_2):
        if texte.count(a) != 1:
            sys.exit(f"✗ ancre trouvée {texte.count(a)} fois au lieu d'une : rien fait.\n{a}")
    texte = texte.replace(ANCRE_1, NOUVEAU_1).replace(ANCRE_2, NOUVEAU_2)
    compile(texte, str(CIBLE), "exec")
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_reste_titre"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} modifié (2 remplacements), sauvegarde .bak_reste_titre")


if __name__ == "__main__":
    main()
