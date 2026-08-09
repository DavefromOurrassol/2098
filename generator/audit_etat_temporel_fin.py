#!/usr/bin/env python3
"""
Audit ponctuel (8 août 2026) — vérifie la cohérence entre etat_temporel et
annee_fin sur toutes les instances du vault.

Constat de départ (question de David, 8 août 2026, en clôture du chantier
annee_debut) : le schéma JSON envoyé au LLM lors de la création d'une
instance montre "annee_fin": null codé en dur comme exemple, juste à côté
de "etat_temporel": "actif|disparu|transformé|clandestin|historique|
mythifié" — sans lien structurel entre les deux. La seule consigne
existante ("annee_fin reste null sauf raison narrative explicite") ne
mentionne jamais etat_temporel. Aucune validation ne vérifie la cohérence
entre les deux champs. Mesure faite pendant le chantier annee_debut :
seulement 2/710 fiches du vault ont annee_fin renseignée.

Ce script chiffre précisément le problème : combien de fiches ont un
etat_temporel qui, narrativement, implique presque toujours une fin
(disparu, transformé, historique, mythifié) mais dont annee_fin reste
vide malgré tout ?

Usage :
    python3 audit_etat_temporel_fin.py                    # dossier instances/ par défaut
    python3 audit_etat_temporel_fin.py --dossier /chemin/vers/instances
"""
import argparse
import os
import re
from pathlib import Path

import yaml
from collections import Counter

GENERATOR_DIR = Path(__file__).resolve().parent
DEFAULT_INSTANCES_DIR = GENERATOR_DIR.parent / "instances"

# États où l'absence de fin est normale (l'entité existe toujours au
# moment le plus tardif où elle est décrite/référencée).
ETATS_SANS_FIN_ATTENDUE = {"actif", "clandestin"}

# États où narrativement l'entité a cessé d'exister/d'opérer sous cette
# forme à un moment donné — annee_fin devrait, dans la plupart des cas,
# être renseignée pour ces états.
ETATS_AVEC_FIN_ATTENDUE = {"disparu", "transformé", "historique", "mythifié"}


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
    etat_counter = Counter()
    # Pour chaque etat_temporel "avec fin attendue" : combien ont annee_fin
    # renseignée vs vide.
    coherent = Counter()      # etat "avec fin attendue" + annee_fin renseignée
    incoherent = Counter()    # etat "avec fin attendue" + annee_fin VIDE
    exemples_incoherents = {etat: [] for etat in ETATS_AVEC_FIN_ATTENDUE}

    # Cas inverse, plus rare mais à signaler : etat "actif" avec quand
    # même une annee_fin renseignée (contradiction possible, ou fin
    # future planifiée narrativement — pas forcément une erreur).
    actif_avec_fin = []

    for fname in sorted(os.listdir(instances_dir)):
        if not fname.endswith(".md"):
            continue
        total += 1
        filepath = os.path.join(instances_dir, fname)
        fm = parse_frontmatter(filepath)

        etat = fm.get("etat_temporel") or "(absent)"
        etat_counter[etat] += 1

        annee_fin = fm.get("annee_fin")
        fin_renseignee = annee_fin is not None and annee_fin != ""

        if etat in ETATS_AVEC_FIN_ATTENDUE:
            if fin_renseignee:
                coherent[etat] += 1
            else:
                incoherent[etat] += 1
                exemples_incoherents[etat].append({
                    "slug": fm.get("slug", fname),
                    "scenario": fm.get("scenario", "?"),
                    "annee_debut": fm.get("annee_debut", "?"),
                    "age_historique": fm.get("age_historique", "?"),
                })
        elif etat == "actif" and fin_renseignee:
            if len(actif_avec_fin) < 10:
                actif_avec_fin.append(fm.get("slug", fname))

    print("=" * 60)
    print("AUDIT etat_temporel / annee_fin — {} fiches scannées".format(total))
    print("=" * 60)
    print()
    print("-- Distribution de etat_temporel --")
    for etat, count in etat_counter.most_common():
        print("  {} : {}".format(etat, count))
    print()

    total_avec_fin_attendue = sum(etat_counter[e] for e in ETATS_AVEC_FIN_ATTENDUE)
    total_incoherent = sum(incoherent.values())
    print("-- Cohérence etat_temporel <-> annee_fin --")
    print(
        "  Fiches avec un état impliquant normalement une fin "
        "(disparu/transformé/historique/mythifié) : {}".format(total_avec_fin_attendue)
    )
    print("    ... dont annee_fin renseignée (cohérent)      : {}".format(sum(coherent.values())))
    print("    ... dont annee_fin VIDE (incohérence probable) : {}".format(total_incoherent))
    print()
    if total_avec_fin_attendue:
        taux = 100 * total_incoherent / total_avec_fin_attendue
        print("  Taux d'incohérence sur ces états : {:.1f}%".format(taux))
    print()

    for etat in ETATS_AVEC_FIN_ATTENDUE:
        if incoherent[etat]:
            print("  {} : {} fiche(s) sans annee_fin".format(etat, incoherent[etat]))
            for info in exemples_incoherents[etat]:
                print(
                    "    - {} (scenario={}, annee_debut={}, age_historique={})".format(
                        info["slug"], info["scenario"], info["annee_debut"], info["age_historique"]
                    )
                )

    if actif_avec_fin:
        print()
        print(
            "-- Cas inverse (informatif, pas forcément une erreur) : "
            "'actif' avec annee_fin quand même renseignée --"
        )
        for s in actif_avec_fin:
            print("  - {}".format(s))


if __name__ == "__main__":
    main()
