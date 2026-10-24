#!/usr/bin/env python3
"""
patch_s27_localisation_territoires.py — 24 octobre 2026 (S27, point 4).

extract_localisation.py choisit la zone d'une fiche d'après la liste des zones
du scénario, réduite au nom et aux 120 premiers caractères de la description :
les TERRITOIRES de chaque zone (origine_reelle) n'y figuraient pas. Après le Pacte
de Tabriz (Iran passé à l'Arc Eurasien Central), les Veilleurs d'Ormuz, basés à
Bandar Abbas (Iran), ont été placés dans la Zone Golfe Persique–Levant, dont la
description parle du Golfe ; rien ne disait à l'IA que l'Iran n'en fait plus partie.

Correctif :
  1. chaque zone de la liste donnée à l'IA porte ses territoires (15 au plus) ;
  2. consigne : la zone choisie doit couvrir le pays du lieu d'après ces
     territoires ; le nom ou la description d'une zone ne suffit pas.

Cible : generator/extract_localisation.py (sauvegarde .bak_s27_territoires).
Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_localisation_territoires.py
"""

import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_S27_TERRITOIRES"
CIBLE = Path(__file__).resolve().parent / "extract_localisation.py"

REMPLACEMENTS = [
    (
        "        desc   = (z.get(\"description\") or \"\")[:120]\n"
        "        lines.append(f\"  - {slug} (niveau {niveau}, parent: {parent}) — {nom} : {desc}\")\n",
        "        desc   = (z.get(\"description\") or \"\")[:120]\n"
        "        # PATCH_S27_TERRITOIRES : territoires de la zone (origine_reelle), 15 au plus.\n"
        "        terr = [str(o.get(\"entite\")) for o in z.get(\"origine_reelle\") or []\n"
        "                if isinstance(o, dict) and o.get(\"entite\")]\n"
        "        terr_txt = (\" | territoires : \" + \", \".join(terr[:15])\n"
        "                    + (f\" (+{len(terr) - 15})\" if len(terr) > 15 else \"\")) if terr else \"\"\n"
        "        lines.append(f\"  - {slug} (niveau {niveau}, parent: {parent}) — {nom} : {desc}{terr_txt}\")\n",
    ),
    (
        "Ne crée JAMAIS un slug de zone qui ne figure pas dans la liste fournie.\"\"\"",
        "Ne crée JAMAIS un slug de zone qui ne figure pas dans la liste fournie.\n"
        "- La zone choisie doit couvrir le pays du lieu d'après ses « territoires » : le nom ou la description\n"
        "  d'une zone ne suffit pas (une zone peut porter le nom d'une région dont un pays est passé à une\n"
        "  autre zone). Si aucune zone ne couvre le pays du lieu, réponds « ambigu ».\"\"\"",
    ),
]


def main() -> int:
    if not CIBLE.exists():
        print(f"✗ Fichier introuvable : {CIBLE}")
        return 1
    texte = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        print("✗ Patch déjà appliqué (marqueur présent) — rien fait.")
        return 1
    for i, (ancien, nouveau) in enumerate(REMPLACEMENTS, 1):
        n = texte.count(ancien)
        if n != 1:
            print(f"✗ Remplacement {i} : {n} occurrence(s) au lieu d'une — rien écrit.")
            return 1
        texte = texte.replace(ancien, nouveau)
    try:
        compile(texte, str(CIBLE), "exec")
    except SyntaxError as e:
        print(f"✗ Le fichier patché ne compile pas ({e}) — rien écrit.")
        return 1
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s27_territoires"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché ({len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_s27_territoires")
    return 0


if __name__ == "__main__":
    sys.exit(main())
