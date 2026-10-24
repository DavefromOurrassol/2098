#!/usr/bin/env python3
"""
patch_s27_plafond_impact.py — 24 octobre 2026 (S27, point 3).

Création d'instance custom (injection_custom) : quand l'IA donne à une variable
une force au-dessus du plafond (impact_systemique_global × 5), l'instance
échouait en entier. Cas réel, deux fois de suite : Alliance des Ports
Caspiennes (breakdown), impact 2, force 12 pour un plafond de 10 ; l'instance a
dû être créée sans bloc d'impact.

Correctif : avant la validation, une force qui dépasse le plafond est RAMENÉE au
plafond (signe gardé), avec un avertissement à l'écran et une trace dans les
données (`plafond_applique`). Plafond nul (impact 0) : rien n'est ramené, la
validation refuse comme avant.

Cible : generator/instance_generation_common.py (sauvegarde .bak_s27_plafond).
Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_plafond_impact.py
"""

import shutil
import sys
from pathlib import Path

MARQUEUR = "def ramener_au_plafond("
CIBLE = Path(__file__).resolve().parent / "instance_generation_common.py"

AIDE = '''MAX_DELTA_PER_IMPACT_POINT = 5  # plafond = impact_systemique_global * 5 (0-25)


def ramener_au_plafond(data):
    """PATCH_S27_PLAFOND (24 oct 2026) : ramène au plafond (signe gardé) toute force de
    impact_sur_variables qui le dépasse, au lieu de refuser l'instance. Retourne les notes."""
    try:
        plafond = int(data.get("impact_systemique_global", 0)) * MAX_DELTA_PER_IMPACT_POINT
    except (TypeError, ValueError):
        return []
    impacts = data.get("impact_sur_variables")
    if plafond <= 0 or not isinstance(impacts, list):
        return []
    notes = []
    for imp in impacts:
        if not isinstance(imp, dict):
            continue
        try:
            delta = float(imp.get("delta_level"))
        except (TypeError, ValueError):
            continue
        if abs(delta) > plafond:
            imp["delta_level"] = plafond if delta > 0 else -plafond
            notes.append(f"[{imp.get('variable')}] delta_level {delta:g} ramené au plafond {plafond}")
    if notes:
        data["plafond_applique"] = notes
    return notes'''

REMPLACEMENTS = [
    ("MAX_DELTA_PER_IMPACT_POINT = 5  # plafond = impact_systemique_global * 5 (0-25)", AIDE),
    (
        "    issues = validate_instance(instance_data, hard_constraint=hard_constraint,\n",
        "    if injection_custom:   # PATCH_S27_PLAFOND\n"
        "        for note in ramener_au_plafond(instance_data):\n"
        "            print(f\"\\n     ⚠ {note}\", end=\"\")\n"
        "    issues = validate_instance(instance_data, hard_constraint=hard_constraint,\n",
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
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s27_plafond"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché ({len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_s27_plafond")
    return 0


if __name__ == "__main__":
    sys.exit(main())
