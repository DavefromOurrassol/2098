#!/usr/bin/env python3
"""
patch_u4d4_wild_cards_scenarios.py — Ourrassol 2098 (U4d4, 15 novembre 2026)
============================================================================

Constat de David (15 nov) : toutes les wild cards proposées par ⚡ portaient sur
« tous » les scénarios. La consigne disait « "tous" ou une liste », et l'exemple
JSON montrait "tous" : l'IA le recopiait.

  - Consigne : choisir les scénarios où la rupture a du sens (1 à 4 le plus souvent) ;
    « tous » seulement si elle frappe vraiment le monde entier, au plus une idée sur
    trois ; varier d'une idée à l'autre ; dire pourquoi ces scénarios.
  - Exemple JSON : une liste au lieu de "tous", plus le champ "pourquoi_scenarios".
  - La raison affichée sous chaque carte ajoute « Scénarios : … » (le pourquoi).

USAGE (depuis la racine du vault)
    python3 generator/patch_u4d4_wild_cards_scenarios.py            # dry-run
    python3 generator/patch_u4d4_wild_cards_scenarios.py --apply
Sauvegarde .bak_u4d4. Pas de relance de Flask. Exige U4d.
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

CHEMIN = Path.cwd() / "generator" / "suggerer_lacunes.py"
TAG = "U4d4"

REMP = [
    ("consigne : choix des scénarios",
     '''- "scenarios" : "tous" ou une liste de scénarios ; une même rupture peut frapper plusieurs mondes, chacun
  l'absorbant à sa façon.
''',
     '''- "scenarios" (U4d4) : la LISTE des scénarios où cette rupture a du sens, d'après leur logique (1 à 4 le plus
  souvent). "tous" seulement si elle frappe vraiment le monde entier, et au plus pour une idée sur trois.
  Varie les scénarios d'une idée à l'autre. "pourquoi_scenarios" : une phrase qui justifie ce choix.
'''),
    ("exemple JSON",
     '''{{"wild_cards": [{{"titre": "...", "description": "...", "date": 2061, "scenarios": "tous",
  "improbable": "...", "bouscule": "..."}}]}}"""
''',
     '''{{"wild_cards": [{{"titre": "...", "description": "...", "date": 2061,
  "scenarios": ["new_sustainability", "eco_communalism"], "pourquoi_scenarios": "...",
  "improbable": "...", "bouscule": "..."}}]}}"""
'''),
    ("raison : pourquoi ces scénarios",
     '''            f"Bouscule : {' '.join(str(i.get('bouscule') or '').split())}" if i.get("bouscule") else "") if x)
''',
     '''            f"Bouscule : {' '.join(str(i.get('bouscule') or '').split())}" if i.get("bouscule") else "",
            f"Scénarios : {' '.join(str(i.get('pourquoi_scenarios') or '').split())}"
            if i.get("pourquoi_scenarios") else "") if x)   # U4d4
'''),
]


def main():
    a = argparse.ArgumentParser(description="U4d4 : wild cards, choix des scénarios.")
    a.add_argument("--apply", action="store_true")
    x = a.parse_args()
    if not CHEMIN.exists():
        sys.exit("✗ generator/suggerer_lacunes.py introuvable : lancer depuis la racine du vault")
    texte = CHEMIN.read_text(encoding="utf-8")
    if TAG in texte:
        sys.exit(f"✗ {TAG} déjà appliqué")
    erreurs = []
    for libelle, avant, apres in REMP:
        n = texte.count(avant)
        if n != 1:
            erreurs.append(f"[{libelle}] passage trouvé {n} fois (attendu 1) — U4d appliqué ?")
            continue
        texte = texte.replace(avant, apres)
    if erreurs:
        sys.exit("✗ Rien n'est écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(texte)
    try:
        py_compile.compile(f.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ syntaxe invalide après patch, rien n'est écrit\n{e}")
    finally:
        Path(f.name).unlink(missing_ok=True)
    print(f"generator/suggerer_lacunes.py : {len(REMP)} modification(s)")
    for libelle, _, _ in REMP:
        print(f"  · {libelle}")
    if not x.apply:
        print("\nDRY-RUN : syntaxe vérifiée sur copie, rien n'est écrit. Relancer avec --apply.")
        return
    shutil.copy2(CHEMIN, CHEMIN.with_name(CHEMIN.name + ".bak_u4d4"))
    CHEMIN.write_text(texte, encoding="utf-8")
    print("\n✓ U4d4 appliqué (sauvegarde .bak_u4d4). Pas de relance de Flask.")


if __name__ == "__main__":
    main()
