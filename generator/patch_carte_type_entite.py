#!/usr/bin/env python3
"""
patch_carte_type_entite.py — 23 octobre 2026 (hors S27, bug noté le 19 oct).

Le bouton de la Carte (ZoneRepository.assign_pays, « absorber » et « créer »)
écrivait toujours `type_entite: pays`, même quand le territoire portait un autre
type dans sa zone d'origine (Écosse : `region_administrative`). Désormais, le
type déjà présent dans la fiche est repris (zone N1 en priorité, puis toute
zone) ; `pays` reste la valeur par défaut si le territoire n'apparaissait nulle
part.

Cible : gui/zone_repository.py (sauvegarde .bak_carte_type_entite).
Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_carte_type_entite.py
"""

import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_CARTE_TYPE_ENTITE"
CIBLE = Path(__file__).resolve().parent.parent / "gui" / "zone_repository.py"

REMPLACEMENTS = [
    # 1. Méthode utilitaire, juste avant assign_pays.
    (
        "    # ── AFFECTER un pays (clic sur la carte) ────────────────────────────\n\n"
        "    def assign_pays(",
        "    # ── AFFECTER un pays (clic sur la carte) ────────────────────────────\n\n"
        "    @staticmethod\n"
        "    def _type_entite_origine(zones: list, pays: str) -> str:\n"
        "        \"\"\"PATCH_CARTE_TYPE_ENTITE (23 oct 2026) : type_entite que `pays`\n"
        "        porte déjà dans la fiche (zones N1 d'abord, puis toute zone), pour ne\n"
        "        pas le réécrire en « pays » lors d'une réaffectation (cas Écosse,\n"
        "        region_administrative). « pays » si aucune entrée n'existe.\"\"\"\n"
        "        for z in sorted(zones, key=lambda z: int(z.get(\"niveau\") or 1) != 1):\n"
        "            for o in (z.get(\"origine_reelle\") or []):\n"
        "                if (isinstance(o, dict) and o.get(\"entite\") == pays\n"
        "                        and o.get(\"type_entite\") in TYPE_ENTITE_REELLE):\n"
        "                    return o[\"type_entite\"]\n"
        "        return \"pays\"\n\n"
        "    def assign_pays(",
    ),
    # 2. Type relu AVANT que le pays soit retiré des autres zones.
    (
        "        gf = self._load_geo(scenario)\n"
        "        zones = gf.zones\n\n"
        "        if action == \"absorber\":",
        "        gf = self._load_geo(scenario)\n"
        "        zones = gf.zones\n"
        "        type_origine = self._type_entite_origine(zones, pays)  # PATCH_CARTE_TYPE_ENTITE\n\n"
        "        if action == \"absorber\":",
    ),
    # 3. Branche « absorber ».
    (
        "                origine.append({\"entite\": pays, \"type_entite\": \"pays\", \"portion\": None})",
        "                origine.append({\"entite\": pays, \"type_entite\": type_origine, \"portion\": None})",
    ),
    # 4. Branche « créer ».
    (
        "                \"origine_reelle\": [{\"entite\": pays, \"type_entite\": \"pays\", \"portion\": None}],",
        "                \"origine_reelle\": [{\"entite\": pays, \"type_entite\": type_origine, \"portion\": None}],",
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
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_carte_type_entite"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché (4 remplacements) ; sauvegarde .bak_carte_type_entite")
    print("  Redémarrer Flask pour que la Carte prenne le correctif.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
