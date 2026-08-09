#!/usr/bin/env python3
"""
Audit ponctuel (7 août 2026, point 1.2 du backlog) — vérifie si annee_debut/
annee_fin sont réellement renseignées dans le frontmatter de toutes les
instances, ou si certaines s'appuient silencieusement sur le fallback de
loader.py (annee_debut -> 2026, annee_fin -> None).

Contrairement à type_relation_dominante (déjà audité, 0 cas résiduel),
annee_debut est un cas plus risqué : son fallback (2026) est une valeur
plausible en soi (année de lancement du projet), donc une fiche où le champ
est absent du frontmatter donnerait "2026" sans que rien ne distingue ça
d'une vraie donnée -- le risque ne se voit pas dans le texte généré,
contrairement à "neutralité" qui aurait été plus repérable.

Usage :
    python3 audit_dates_instances.py                    # dossier instances/ par défaut
    python3 audit_dates_instances.py --dossier /chemin/vers/instances

Converti le 8 août 2026 (sys.argv positionnel -> argparse --dossier) pour
cohérence avec le reste du pipeline et intégration au GUI (une entrée de
type argparse avec un flag optionnel s'y prête directement, un argument
positionnel non).
"""
import argparse
import os
import re
from pathlib import Path

import yaml
from collections import Counter

GENERATOR_DIR = Path(__file__).resolve().parent
DEFAULT_INSTANCES_DIR = GENERATOR_DIR.parent / "instances"

def parse_frontmatter(filepath):
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

    debut_absent = 0
    debut_present_2026 = 0
    debut_present_autre = 0
    debut_valeurs = Counter()

    fin_absent = 0
    fin_present_null = 0
    fin_present_valeur = 0

    exemples_debut_absent = []

    for fname in sorted(os.listdir(instances_dir)):
        if not fname.endswith(".md"):
            continue
        total += 1
        filepath = os.path.join(instances_dir, fname)
        fm = parse_frontmatter(filepath)

        alliances = fm.get("alliances") or []
        oppositions = fm.get("oppositions") or []
        has_relations = bool(alliances or oppositions)
        if has_relations:
            avec_relations += 1

        # annee_debut
        if "annee_debut" not in fm:
            debut_absent += 1
            if len(exemples_debut_absent) < 15:
                exemples_debut_absent.append(fm.get("slug", fname))
        else:
            val = fm.get("annee_debut")
            debut_valeurs[val] += 1
            if val == 2026:
                debut_present_2026 += 1
            else:
                debut_present_autre += 1

        # annee_fin
        if "annee_fin" not in fm:
            fin_absent += 1
        else:
            val = fm.get("annee_fin")
            if val is None:
                fin_present_null += 1
            else:
                fin_present_valeur += 1

    print("=" * 60)
    print("AUDIT annee_debut / annee_fin — {} fiches scannées".format(total))
    print("=" * 60)
    print("Fiches avec au moins 1 alliance/opposition réelle : {}".format(avec_relations))
    print()
    print("-- annee_debut --")
    print("  ABSENT du frontmatter (fallback loader.py -> 2026) : {}  <-- risque silencieux".format(debut_absent))
    print("  Présent, valeur = 2026 (donnée réelle)              : {}".format(debut_present_2026))
    print("  Présent, autre année                                : {}".format(debut_present_autre))
    print()
    print("  Distribution des valeurs réellement présentes (top 10) :")
    for val, count in debut_valeurs.most_common(10):
        print("    {} : {}".format(val, count))
    print()
    print("-- annee_fin --")
    print("  ABSENT du frontmatter (fallback loader.py -> None) : {}".format(fin_absent))
    print("  Présent, valeur = null/vide (relation en cours)    : {}".format(fin_present_null))
    print("  Présent, valeur renseignée (relation terminée)     : {}".format(fin_present_valeur))
    print()
    if exemples_debut_absent:
        print("Exemples de fiches avec annee_debut ABSENT (jusqu'à 15) :")
        for s in exemples_debut_absent:
            print("  - {}".format(s))

if __name__ == "__main__":
    main()
