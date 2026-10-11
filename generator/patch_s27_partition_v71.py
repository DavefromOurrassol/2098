#!/usr/bin/env python3
"""
patch_s27_partition_v71.py — Ourrassol 2098 (S27, 10 octobre 2026)
====================================================================

Simulateur « et si ? » v7 -> v7.1 : une partition dont deux parties ont la
même zone racine de niveau 1 n'en est pas une (le territoire ne change pas
de mains). Cas réel : États-Unis coupés entre bloc_atlantique et sa propre
sous-zone midwest_desertifie (fortress_world, 10 oct).

  - Saisie manuelle (hypotheses.yaml) : erreur dans le rapport.
  - Proposition de l'IA : écartée au contrôle.
  - Consigne IA : une contestation interne relève des relations / entités.

Fichier modifié : generator/simuler_et_si.py (.bak_v71)

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_partition_v71.py            # aperçu
    python3 generator/patch_s27_partition_v71.py --apply    # écrit

Exige la v7 (patch_s27_partition.py déjà appliqué). Refuse un second passage.
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"
MARQUEUR = "def _racine_n1"

FONCTION_RACINE = r'''def _racine_n1(slug, by_slug):
    """V7.1 : zone racine de niveau 1 d'une zone (elle-même si niveau 1 ou
    inconnue). Anti-cycle."""
    vus = set()
    while slug in by_slug and slug not in vus:
        vus.add(slug)
        z = by_slug[slug] or {}
        if (z.get("niveau") or 1) == 1 or not z.get("parent"):
            return slug
        slug = z["parent"]
    return slug


'''

REMPLACEMENTS = [
    ("version", 'VERSION = "v7"', 'VERSION = "v7.1"'),

    ("fonction _racine_n1",
     "def normaliser_partition(op, ou, erreurs):",
     FONCTION_RACINE + "def normaliser_partition(op, ou, erreurs):"),

    ("contrôle de racine dans evaluer_partition",
     "    # Zones actuelles de niveau 1 qui ne reçoivent aucune partie : quittées.",
     '''    # V7.1 : deux parties sous la même zone de niveau 1 = pas de changement de contrôle.
    racines = {}
    for p in parties:
        r = p["cible"] if p["nouvelle"] else _racine_n1(p["cible"], by_slug)
        racines.setdefault(r, []).append(str(p["numero"]))
    for r, nums in racines.items():
        if len(nums) > 1:
            erreurs.append(f"parties {' et '.join(nums)} : même zone de niveau 1 ({r}) — le territoire "
                           f"ne change pas de mains, ce n'est pas une partition")

    # Zones actuelles de niveau 1 qui ne reçoivent aucune partie : quittées.'''),

    ("contrôle de racine sur les propositions de l'IA",
     '''            if part is None or inconnues:
                ecartees += errs or [f"carte : partition de {pays}, zone(s) inconnue(s) {inconnues}"]
                continue''',
     '''            if part is None or inconnues:
                ecartees += errs or [f"carte : partition de {pays}, zone(s) inconnue(s) {inconnues}"]
                continue
            racines = [p["nouvelle_zone"]["slug"] if p["nouvelle_zone"] else _racine_n1(p["zone"], by_zone)
                       for p in part["parties"]]
            if len(set(racines)) != len(racines):
                ecartees.append(f"carte : partition de {pays} écartée, deux parties dans la même zone de "
                                f"niveau 1 (contestation interne, pas un changement de contrôle)")
                continue'''),

    ("consigne IA",
     "(ex. « le Nordeste et l'Amazonie »). Deux parties ne vont jamais dans la même zone.",
     '''(ex. « le Nordeste et l'Amazonie »). Une partition = un territoire qui passe sous un autre
contrôle ; une contestation sociale ou politique à l'intérieur d'un bloc n'en est pas une
(propose-la en relations ou en nouvelles entités). Deux parties ne vont jamais dans la même
zone, ni dans deux zones d'un même bloc (une zone et sa sous-zone).'''),
]


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7 -> v7.1.")
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon : aperçu)")
    args = ap.parse_args()
    if not SIMU.exists():
        sys.exit(f"✗ Fichier introuvable : {SIMU}")
    texte = SIMU.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit("✗ Patch déjà appliqué (_racine_n1 présent). Rien à faire.")
    if "def normaliser_partition" not in texte:
        sys.exit("✗ La v7 n'est pas installée : appliquer d'abord patch_s27_partition.py.")
    print("Contrôle des emplacements :")
    erreurs = []
    for libelle, ancien, nouveau in REMPLACEMENTS:
        n = texte.count(ancien)
        if n != 1:
            erreurs.append(f"{libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        texte = texte.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    try:
        compile(texte, str(SIMU), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier modifié ne compilerait pas ({e}) : rien n'est écrit.")
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    shutil.copy(SIMU, SIMU.with_name(SIMU.name + ".bak_v71"))
    SIMU.write_text(texte, encoding="utf-8")
    print(f"→ écrit : {SIMU.relative_to(VAULT_ROOT)} (sauvegarde {SIMU.name}.bak_v71)")
    print("\nSimulateur passé en v7.1.")


if __name__ == "__main__":
    main()
