#!/usr/bin/env python3
"""
patch_s27_carte_sous_zones.py — 23 octobre 2026 (S27.1, premier essai réel de carte).

Bug trouvé sur pacte_tabriz_2058 (breakdown) : après avoir rattaché les sous-zones
d'un seul pays (terminal_kharg, isfahan_fordow_ruines), le contrôle final de
appliquer_carte() exigeait que leur origine_reelle porte EXACTEMENT « Iran ». Or
une sous-zone nomme souvent le lieu : « Île de Kharg, Iran », « Ispahan, Iran ».
La simulation, elle, les classe par mots (virgules, parenthèses, barres), comme la
Carte. Le contrôle échouait donc alors que l'opération était juste, et toute la
carte était remise en l'état.

Correctif : le contrôle des sous-zones lit l'entrée par mots (porte_pays_cite),
comme la simulation. Le contrôle de la zone cible (« Iran » ajouté tel quel par
la Carte) et le repérage « déjà appliqué » ne changent pas.

Cible : generator/appliquer_et_si.py (sauvegarde .bak_s27_sous_zones).
Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_carte_sous_zones.py
"""

import shutil
import sys
from pathlib import Path

MARQUEUR = "def porte_pays_cite("
CIBLE = Path(__file__).resolve().parent / "appliquer_et_si.py"

REMPLACEMENTS = [
    (
        "def note_carte(o):",
        "def porte_pays_cite(zone, pays):\n"
        "    \"\"\"PATCH_S27_CARTE_SOUS_ZONES : la zone cite-t-elle `pays` dans une de ses entrées, lue par\n"
        "    mots (« Île de Kharg, Iran », « Détroit d'Ormuz (Oman/Iran) ») comme la simulation et la Carte ?\"\"\"\n"
        "    cherche = plie(pays)\n"
        "    for o in (zone or {}).get(\"origine_reelle\") or []:\n"
        "        if not isinstance(o, dict):\n"
        "            continue\n"
        "        texte = plie(o.get(\"entite\"))\n"
        "        morceaux = [re.sub(r\"\\([^)]*\\)\", \"\", texte)] + re.findall(r\"\\(([^)]*)\\)\", texte)\n"
        "        if any(t.strip() == cherche for m in morceaux for t in re.split(r\"[,/]\", m)):\n"
        "            return True\n"
        "    return False\n"
        "\n\n"
        "def note_carte(o):",
    ),
    (
        "        if (apres.get(s) or {}).get(\"parent\") != cible or not porte_pays(apres.get(s), pays):",
        "        if (apres.get(s) or {}).get(\"parent\") != cible or not porte_pays_cite(apres.get(s), pays):",
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
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s27_sous_zones"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché ({len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_s27_sous_zones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
