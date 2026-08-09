#!/usr/bin/env python3
"""
Audit ponctuel (7 août 2026, point 1.2 du backlog) — compte, sur le vault
réel, les fiches instance qui ont au moins une alliance/opposition réelle
mais où type_relation_dominante est ABSENT du frontmatter (par opposition
à explicitement rempli à "neutralité", qu'on ne peut pas distinguer une
fois passé par loader.py::load_instance() -- d'où ce script qui lit le
frontmatter brut, avant tout fallback).

Usage :
    python3 audit_type_relation_dominante.py                    # dossier instances/ par défaut
    python3 audit_type_relation_dominante.py --dossier /chemin/vers/instances

Converti le 8 août 2026 (sys.argv positionnel -> argparse --dossier) pour
cohérence avec le reste du pipeline et intégration au GUI.
"""
import argparse
import os
import re
from pathlib import Path

import yaml

GENERATOR_DIR = Path(__file__).resolve().parent
DEFAULT_INSTANCES_DIR = GENERATOR_DIR.parent / "instances"

def parse_frontmatter(filepath):
    """Extrait uniquement le frontmatter YAML brut, sans aucun fallback --
    reproduit le split utilisé par parse_md_file() dans loader.py (frontmatter
    entre les deux premières lignes '---')."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        print("  ⚠ Erreur YAML dans {} : {}".format(filepath, e))
        return {}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dossier", type=str, default=str(DEFAULT_INSTANCES_DIR),
        help="Dossier instances/ à scanner (défaut : instances/ du vault courant)"
    )
    args = parser.parse_args()
    instances_dir = args.dossier
    if not os.path.isdir(instances_dir):
        print("Dossier introuvable : {}".format(instances_dir))
        print("Relance avec : python3 {} --dossier /chemin/vers/vault/instances".format(__file__))
        raise SystemExit(1)

    total = 0
    avec_relations = 0
    champ_absent = 0
    champ_present_neutralite = 0
    champ_present_autre = 0
    exemples_absent = []

    for fname in sorted(os.listdir(instances_dir)):
        if not fname.endswith(".md"):
            continue
        total += 1
        filepath = os.path.join(instances_dir, fname)
        fm = parse_frontmatter(filepath)

        alliances = fm.get("alliances") or []
        oppositions = fm.get("oppositions") or []
        if not (alliances or oppositions):
            continue
        avec_relations += 1

        if "type_relation_dominante" not in fm:
            champ_absent += 1
            if len(exemples_absent) < 15:
                exemples_absent.append(fm.get("slug", fname))
        else:
            valeur = fm.get("type_relation_dominante")
            if valeur == "neutralité":
                champ_present_neutralite += 1
            else:
                champ_present_autre += 1

    print("=" * 60)
    print("AUDIT type_relation_dominante — {} fiches scannées".format(total))
    print("=" * 60)
    print("Fiches avec au moins 1 alliance/opposition réelle : {}".format(avec_relations))
    print()
    print("  Parmi elles :")
    print("  - type_relation_dominante ABSENT du frontmatter  : {}  <-- cas résiduel ambigu".format(champ_absent))
    print("  - présent, valeur = 'neutralité' (choix réel)    : {}".format(champ_present_neutralite))
    print("  - présent, autre valeur (rivalité/conflit/...)   : {}".format(champ_present_autre))
    print()
    if exemples_absent:
        print("Exemples de fiches concernées (champ absent, jusqu'à 15) :")
        for s in exemples_absent:
            print("  - {}".format(s))

if __name__ == "__main__":
    main()
