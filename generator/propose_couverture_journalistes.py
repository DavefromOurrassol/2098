#!/usr/bin/env python3
"""
propose_couverture_journalistes.py — Ourrassol 2098

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) :
prolonge audit_couverture_journalistes.py (23 août 2026) en proposant
des ajouts concrets pour combler les trous de couverture détectés --
pas d'application automatique, David valide/édite journaux.yaml
lui-même (même principe que needs_review.yaml ailleurs dans ce
pipeline : proposition à valider, pas de décision prise à sa place).

Pour chaque combinaison zone × thématique sous la cible de couverture
(par défaut 2 journalistes minimum), propose d'ajouter cette thématique
à (cible - couverture_actuelle) journaliste(s) de la MÊME zone parmi
ceux qui ne la couvrent pas déjà -- en priorité ceux qui ont le MOINS
de thématiques actuellement (répartit la charge plutôt que de tout
ajouter aux mêmes 1-2 journalistes déjà chargés), départagé par ordre
alphabétique pour un résultat déterministe et reproductible.

Usage :
    python3 propose_couverture_journalistes.py
    python3 propose_couverture_journalistes.py --cible 3
    python3 propose_couverture_journalistes.py --journaux /chemin/vers/journaux.yaml
    python3 propose_couverture_journalistes.py --scenario new_sustainability
"""
import argparse
import os
from collections import defaultdict

import yaml

THEMATIQUES_CONNUES = [
    "actualites_a_la_une", "politique", "economie_finance", "international",
    "environnement_climat", "sante", "societe", "culture", "musique",
    "sports", "faits_divers", "opinions_editoriaux", "lifestyle_art_de_vivre",
    "education", "histoire_patrimoine", "medias_communication",
    "religion_spiritualite", "petites_annonces_services", "meteo",
    "sciences_technologies",
]


def find_default_journaux_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "journaux.yaml")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--journaux", type=str, default=find_default_journaux_path(),
                         help="Chemin vers journaux.yaml (défaut : generator/journaux.yaml)")
    parser.add_argument("--cible", type=int, default=2,
                         help="Nombre minimum de journalistes éligibles visé par "
                              "thématique/zone (défaut : 2 -- permet au moins une "
                              "rotation)")
    parser.add_argument("--scenario", type=str, default=None,
                         help="Limiter aux propositions pour ce scénario "
                              "(défaut : tous)")
    args = parser.parse_args()

    if not os.path.isfile(args.journaux):
        print("Fichier introuvable : {}".format(args.journaux))
        raise SystemExit(1)

    with open(args.journaux, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    total_propositions = 0
    total_zones_concernees = 0

    for scenario, scenario_data in sorted(data.items()):
        if args.scenario and scenario != args.scenario:
            continue
        if not isinstance(scenario_data, dict):
            continue
        for ligne, ligne_data in sorted(scenario_data.items()):
            if not isinstance(ligne_data, dict):
                continue
            zones = ligne_data.get("zones", {}) or {}
            for zone_slug, zone_data in sorted(zones.items()):
                journalistes = zone_data.get("journalistes", []) or []
                if not journalistes:
                    continue

                # Couverture actuelle par thématique dans cette zone
                couverture = defaultdict(list)
                for j in journalistes:
                    for th in (j.get("thematiques") or []):
                        couverture[th].append(j["nom"])

                # Propositions pour cette zone : {thematique: [noms proposés]}
                propositions_zone = {}
                for thematique in THEMATIQUES_CONNUES:
                    actuels = couverture.get(thematique, [])
                    manque = args.cible - len(actuels)
                    if manque <= 0:
                        continue

                    # Candidats : journalistes de la zone qui ne couvrent pas
                    # déjà cette thématique, triés par charge actuelle
                    # croissante (nombre de thématiques déjà couvertes),
                    # puis alphabétique pour un résultat stable.
                    candidats = [
                        j for j in journalistes
                        if thematique not in (j.get("thematiques") or [])
                    ]
                    candidats.sort(key=lambda j: (len(j.get("thematiques") or []), j["nom"]))

                    proposes = [j["nom"] for j in candidats[:manque]]
                    if proposes:
                        propositions_zone[thematique] = (actuels, proposes)

                if not propositions_zone:
                    continue

                total_zones_concernees += 1
                print("=" * 70)
                print("{} / {} / {}".format(scenario, ligne, zone_slug))
                print("=" * 70)
                for thematique, (actuels, proposes) in sorted(propositions_zone.items()):
                    total_propositions += len(proposes)
                    actuels_str = ", ".join(actuels) if actuels else "(aucun)"
                    print("  {} -- couverture actuelle : {}".format(thematique, actuels_str))
                    for nom in proposes:
                        print("    + ajouter '{}' aux thématiques de : {}".format(
                            thematique, nom))
                print()

    print("=" * 70)
    print("RÉSUMÉ : {} ajout(s) proposé(s) sur {} zone(s) concernée(s)".format(
        total_propositions, total_zones_concernees))
    print("=" * 70)
    print()
    print("Aucune écriture effectuée -- ce script ne fait que proposer.")
    print("Pour appliquer, édite journaux.yaml manuellement en ajoutant la ")
    print("thématique concernée à la liste `thematiques:` du/des journaliste(s)")
    print("proposé(s) ci-dessus.")


if __name__ == "__main__":
    main()
