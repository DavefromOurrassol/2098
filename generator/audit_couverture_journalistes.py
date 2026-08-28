#!/usr/bin/env python3
"""
audit_couverture_journalistes.py — Ourrassol 2098

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) : balaie
journaux.yaml et repère, pour chaque combinaison scénario × ligne
éditoriale × zone × thématique, combien de journalistes sont
effectivement éligibles (thématique listée dans leur `thematiques`).

Créé le 23 août 2026, suite au diagnostic sur `bassin_du_congo` /
`petites_annonces_services` (rotation pondérée des journalistes,
22 août) : Samira Benyahia y était la SEULE journaliste éligible sur 6,
expliquant pourquoi deux articles consécutifs avaient la même signature
et un contenu très proche -- pas un bug de rotation, un trou de
couverture dans les données. Ce script généralise le diagnostic à tout
le vault pour prioriser l'enrichissement plutôt que de découvrir les
trous un par un au fil des articles.

Rappel du mécanisme concerné (_select_journaliste_pondere(),
prompt_builder.py, 22 août) : si 0 ou 1 seul journaliste couvre une
thématique donnée pour une zone, aucune rotation n'est possible --
soit repli sur toute la liste de la zone (0 couverture explicite), soit
un seul nom systématique (couverture à 1). Les deux cas sont signalés
séparément ci-dessous, la couverture à 0 étant généralement moins
gênante (au moins une vraie rotation a lieu, juste sans lien thématique)
que la couverture à 1 (toujours le même nom, jamais de rotation du
tout).

Usage :
    python3 audit_couverture_journalistes.py
    python3 audit_couverture_journalistes.py --journaux /chemin/vers/journaux.yaml
    python3 audit_couverture_journalistes.py --seuil 2   # signale aussi la couverture à 2
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


REPORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "audit_couverture_journalistes_report.txt")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--journaux", type=str, default=find_default_journaux_path(),
                         help="Chemin vers journaux.yaml (défaut : generator/journaux.yaml)")
    parser.add_argument("--seuil", type=int, default=1,
                         help="Signale aussi les combinaisons avec ce nombre de "
                              "journalistes éligibles ou moins (défaut : 1 -- "
                              "signale 0 et 1 seulement)")
    parser.add_argument("--report", "-r", action="store_true",
                         help="Écrit le détail complet dans {} (23 août 2026, "
                              "même principe que --report de validate.py) -- "
                              "seul le résumé par scénario reste affiché dans "
                              "le terminal. Sans cette option, tout s'affiche "
                              "dans le terminal comme avant (non-régression).".format(
                                  os.path.basename(REPORT_PATH)))
    args = parser.parse_args()

    if not os.path.isfile(args.journaux):
        print("Fichier introuvable : {}".format(args.journaux))
        print("Relance avec : python3 {} --journaux /chemin/vers/journaux.yaml".format(__file__))
        raise SystemExit(1)

    with open(args.journaux, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # zero_couverture / une_couverture : (scenario, ligne, zone, thematique) -> [noms]
    zero_couverture = []
    sous_seuil = []  # entre 1 (exclu, déjà dans zero/une) et args.seuil inclus
    total_combinaisons = 0
    total_journalistes = 0
    zones_scannees = 0

    for scenario, scenario_data in sorted(data.items()):
        if not isinstance(scenario_data, dict):
            continue
        for ligne, ligne_data in sorted(scenario_data.items()):
            if not isinstance(ligne_data, dict):
                continue
            zones = ligne_data.get("zones", {}) or {}
            for zone_slug, zone_data in sorted(zones.items()):
                zones_scannees += 1
                journalistes = zone_data.get("journalistes", []) or []
                total_journalistes += len(journalistes)

                for thematique in THEMATIQUES_CONNUES:
                    total_combinaisons += 1
                    eligibles = [
                        j.get("nom", "?") for j in journalistes
                        if thematique in (j.get("thematiques") or [])
                    ]
                    n = len(eligibles)

                    if n == 0:
                        zero_couverture.append((scenario, ligne, zone_slug, thematique, len(journalistes)))
                    elif n <= args.seuil:
                        sous_seuil.append((scenario, ligne, zone_slug, thematique, eligibles))

    # 23 août 2026 : détail accumulé dans un buffer plutôt qu'imprimé
    # directement -- permet de router soit vers la console (comportement
    # d'origine, --report absent), soit vers le fichier rapport
    # (--report présent, console limitée au résumé).
    detail = []

    def d(msg=""):
        detail.append(msg)

    d("=" * 70)
    d("AUDIT couverture journalistes — {} zones scannées, {} journalistes, "
      "{} combinaisons zone×thématique".format(
          zones_scannees, total_journalistes, total_combinaisons))
    d("=" * 70)
    d()

    d("-- Couverture À ZÉRO (aucun journaliste éligible -- repli sur toute "
      "la liste de la zone, rotation possible mais sans lien thématique) --")
    d("   {} combinaison(s) sur {} ({:.0f}%)".format(
        len(zero_couverture), total_combinaisons,
        100 * len(zero_couverture) / total_combinaisons if total_combinaisons else 0))
    if zero_couverture:
        par_zone = defaultdict(list)
        for scenario, ligne, zone, thematique, nb_total in zero_couverture:
            par_zone[(scenario, ligne, zone, nb_total)].append(thematique)
        for (scenario, ligne, zone, nb_total), thematiques in sorted(par_zone.items()):
            d("  {} / {} / {} ({} journaliste(s) dans la zone) :".format(
                scenario, ligne, zone, nb_total))
            d("    {}".format(", ".join(sorted(thematiques))))
    d()

    if args.seuil >= 1:
        label = "UN SEUL" if args.seuil == 1 else "≤ {}".format(args.seuil)
        d("-- Couverture à {} journaliste (jamais de rotation possible, "
          "toujours le même nom -- cas exact bassin_du_congo/"
          "petites_annonces_services du 23 août) --".format(label))
        d("   {} combinaison(s)".format(len(sous_seuil)))
        for scenario, ligne, zone, thematique, eligibles in sorted(sous_seuil):
            d("  {} / {} / {} / {} : {}".format(
                scenario, ligne, zone, thematique, ", ".join(eligibles)))
        d()

    # Résumé par scénario -- toujours affiché en console, --report ou non.
    # 23 août 2026 (retour de David : "96% ne parle pas") : un pourcentage
    # brut ne dit rien à qui n'a pas suivi tout le diagnostic -- traduction
    # qualitative ajoutée à côté de chaque chiffre, seuils calibrés sur les
    # cas réels déjà observés (fortress_world à 49% après un premier passage
    # du mode auto = "encore fragile mais nettement amélioré", 96-98% sur
    # les scénarios jamais touchés = "quasiment aucune rotation possible").
    def _label_fragilite(pct):
        if pct == 0:
            return "rotation possible partout"
        elif pct < 20:
            return "bonne couverture, quelques trous isolés"
        elif pct < 50:
            return "couverture partielle, la rotation fonctionne par endroits"
        elif pct < 80:
            return "couverture fragile, la rotation reste limitée sur une bonne partie"
        else:
            return "quasiment aucune rotation possible -- presque toujours le même nom"

    resume = []
    resume.append("-- Résumé par scénario --")
    resume.append("(% = part des combinaisons zone×thématique où la rotation ne peut")
    resume.append(" quasiment jamais s'exercer, faute d'un second journaliste éligible)")
    resume.append("")
    par_scenario_total = defaultdict(int)
    par_scenario_fragile = defaultdict(int)
    for scenario, ligne, zone, thematique, _ in zero_couverture:
        par_scenario_fragile[scenario] += 1
    for scenario, ligne, zone, thematique, _ in sous_seuil:
        par_scenario_fragile[scenario] += 1
    for scenario, scenario_data in data.items():
        if not isinstance(scenario_data, dict):
            continue
        for ligne, ligne_data in scenario_data.items():
            if not isinstance(ligne_data, dict):
                continue
            n_zones = len(ligne_data.get("zones", {}) or {})
            par_scenario_total[scenario] += n_zones * len(THEMATIQUES_CONNUES)
    for scenario in sorted(par_scenario_total):
        total = par_scenario_total[scenario]
        fragile = par_scenario_fragile.get(scenario, 0)
        pct = 100 * fragile / total if total else 0
        resume.append("  {} : {}/{} combinaisons fragiles ({:.0f}%) -- {}".format(
            scenario, fragile, total, pct, _label_fragilite(pct)))

    if args.report:
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(detail))
            f.write("\n")
            f.write("\n".join(resume))
            f.write("\n")
        print("\n".join(resume))
        print()
        print("Détail complet ({} ligne(s) de couverture zéro, {} sous le seuil) "
              "écrit dans : {}".format(len(zero_couverture), len(sous_seuil), REPORT_PATH))
    else:
        print("\n".join(detail))
        print("\n".join(resume))


if __name__ == "__main__":
    main()
