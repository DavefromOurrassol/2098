#!/usr/bin/env python3
"""
patch_s27_checklist_au_passe.py — 24 octobre 2026 (S27, point 9).

La check-list de l'étape ⑤ (et_si_<id>_reste_a_faire.md, appliquer_et_si.py)
gagne une section « Fiches des entités disparues (au passé) » : une case par
entité devenue « disparu », avec la commande fiche_au_passe.py (aperçu, un appel
IA, puis --apply). Cas d'origine : Genève et Mourmansk, fiches restées au présent.

Cible : generator/appliquer_et_si.py (sauvegarde .bak_s27_au_passe).
Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_checklist_au_passe.py
"""

import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_S27_AU_PASSE"
CIBLE = Path(__file__).resolve().parent / "appliquer_et_si.py"

ANCIEN = ("        # Règle de lore (brouillon)\n"
          "        disparues = [o for o in mes_ops if o[\"genre\"] == \"trajectoire\" and o.get(\"apres\") == \"disparu\" and faites(o)]\n")
NOUVEAU = ANCIEN + (
    "        if disparues:   # PATCH_S27_AU_PASSE : la phase 4 change la trajectoire, pas le texte\n"
    "            L += [\"### Fiches des entités disparues (au passé)\", \"\"]\n"
    "            for o in disparues:\n"
    "                case(f\"`instances/{o['instance']}.md` est-elle encore écrite au présent ? \"\n"
    "                     f\"`python3 generator/fiche_au_passe.py --slug {o['instance']}` (aperçu, un appel IA), relire \"\n"
    "                     f\"`documentation/need_action/fiche_au_passe_{o['instance']}.md`, puis la même commande avec \"\n"
    "                     \"`--apply`.\")\n"
    "            L.append(\"\")\n")


def main() -> int:
    if not CIBLE.exists():
        print(f"✗ Fichier introuvable : {CIBLE}")
        return 1
    texte = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        print("✗ Patch déjà appliqué (marqueur présent) — rien fait.")
        return 1
    if not (Path(__file__).resolve().parent / "fiche_au_passe.py").exists():
        print("✗ Poser d'abord generator/fiche_au_passe.py — rien fait.")
        return 1
    n = texte.count(ANCIEN)
    if n != 1:
        print(f"✗ {n} occurrence(s) du point d'insertion au lieu d'une — rien écrit.")
        return 1
    texte = texte.replace(ANCIEN, NOUVEAU)
    try:
        compile(texte, str(CIBLE), "exec")
    except SyntaxError as e:
        print(f"✗ Le fichier patché ne compile pas ({e}) — rien écrit.")
        return 1
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s27_au_passe"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché ; sauvegarde .bak_s27_au_passe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
