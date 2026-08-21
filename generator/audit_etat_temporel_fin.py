#!/usr/bin/env python3
"""
Audit ponctuel (8 août 2026, adapté le 9 août au chantier trajectoire) —
vérifie la cohérence entre trajectoire et annee_fin sur toutes les
instances du vault.

Constat de départ (question de David, 8 août 2026, en clôture du chantier
annee_debut) : le schéma JSON envoyé au LLM lors de la création d'une
instance montre "annee_fin": null codé en dur comme exemple, juste à côté
du champ de position narrative — sans lien structurel entre les deux. La
seule consigne existante ("annee_fin reste null sauf raison narrative
explicite") ne mentionne jamais cette position. Aucune validation ne
vérifie la cohérence entre les deux champs. Mesure faite pendant le
chantier annee_debut : seulement 2/710 fiches du vault ont annee_fin
renseignée.

Ce script chiffre précisément le problème : combien de fiches ont une
trajectoire qui, narrativement, implique presque toujours une fin
(transformé, disparu, historique, mythifié) mais dont annee_fin reste
vide malgré tout ?

MISE À JOUR 9 AOÛT 2026 : adapté au chantier de fusion trajectoire (voir
SPEC_CHANTIER_TRAJECTOIRE.md) — lisait auparavant etat_temporel/age_
historique (schéma disparu du vault depuis la migration). Lit désormais
trajectoire + est_clandestin. TRAJECTOIRE_INACTIVES importée de
validate.py plutôt que redéfinie localement, pour ne pas recréer une
troisième source de vérité comme celle qui existait avant la fusion
(INACTIVE_ETATS/ETAT_INACTIFS/hardcode C4, unifiées le 9 août 2026).

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

from validate import TRAJECTOIRE_INACTIVES

GENERATOR_DIR = Path(__file__).resolve().parent
DEFAULT_INSTANCES_DIR = GENERATOR_DIR.parent / "instances"

# Trajectoires où narrativement l'entité a cessé d'exister/d'opérer sous
# cette forme à un moment donné — annee_fin devrait, dans la plupart des
# cas, être renseignée. Réutilise TRAJECTOIRE_INACTIVES (validate.py) —
# une seule source de vérité, cf. note de mise à jour ci-dessus.
TRAJECTOIRES_AVEC_FIN_ATTENDUE = TRAJECTOIRE_INACTIVES


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
    trajectoire_counter = Counter()
    # Pour chaque trajectoire "avec fin attendue" : combien ont annee_fin
    # renseignée vs vide.
    coherent = Counter()      # trajectoire "avec fin attendue" + annee_fin renseignée
    incoherent = Counter()    # trajectoire "avec fin attendue" + annee_fin VIDE
    exemples_incoherents = {traj: [] for traj in TRAJECTOIRES_AVEC_FIN_ATTENDUE}

    # Cas inverse, plus rare mais à signaler : trajectoire encore "active"
    # (hors TRAJECTOIRES_AVEC_FIN_ATTENDUE) avec quand même une annee_fin
    # renseignée (contradiction possible, ou fin future planifiée
    # narrativement — pas forcément une erreur).
    active_avec_fin = []

    for fname in sorted(os.listdir(instances_dir)):
        if not fname.endswith(".md"):
            continue
        total += 1
        filepath = os.path.join(instances_dir, fname)
        fm = parse_frontmatter(filepath)

        trajectoire = fm.get("trajectoire") or "(absent)"
        trajectoire_counter[trajectoire] += 1

        annee_fin = fm.get("annee_fin")
        fin_renseignee = annee_fin is not None and annee_fin != ""

        if trajectoire in TRAJECTOIRES_AVEC_FIN_ATTENDUE:
            if fin_renseignee:
                coherent[trajectoire] += 1
            else:
                incoherent[trajectoire] += 1
                exemples_incoherents[trajectoire].append({
                    "slug": fm.get("slug", fname),
                    "scenario": fm.get("scenario", "?"),
                    "annee_debut": fm.get("annee_debut", "?"),
                    "est_clandestin": fm.get("est_clandestin", "?"),
                })
        elif trajectoire not in ("(absent)",) and fin_renseignee:
            if len(active_avec_fin) < 10:
                active_avec_fin.append(fm.get("slug", fname))

    print("=" * 60)
    print("AUDIT trajectoire / annee_fin — {} fiches scannées".format(total))
    print("=" * 60)
    print()
    print("-- Distribution de trajectoire --")
    for trajectoire, count in trajectoire_counter.most_common():
        print("  {} : {}".format(trajectoire, count))
    print()

    total_avec_fin_attendue = sum(trajectoire_counter[t] for t in TRAJECTOIRES_AVEC_FIN_ATTENDUE)
    total_incoherent = sum(incoherent.values())
    print("-- Cohérence trajectoire <-> annee_fin --")
    print(
        "  Fiches avec une trajectoire impliquant normalement une fin "
        "(transformé/disparu/historique/mythifié) : {}".format(total_avec_fin_attendue)
    )
    print("    ... dont annee_fin renseignée (cohérent)      : {}".format(sum(coherent.values())))
    print("    ... dont annee_fin VIDE (incohérence probable) : {}".format(total_incoherent))
    print()
    if total_avec_fin_attendue:
        taux = 100 * total_incoherent / total_avec_fin_attendue
        print("  Taux d'incohérence sur ces trajectoires : {:.1f}%".format(taux))
    print()

    for trajectoire in TRAJECTOIRES_AVEC_FIN_ATTENDUE:
        if incoherent[trajectoire]:
            print("  {} : {} fiche(s) sans annee_fin".format(trajectoire, incoherent[trajectoire]))
            for info in exemples_incoherents[trajectoire]:
                print(
                    "    - {} (scenario={}, annee_debut={}, est_clandestin={})".format(
                        info["slug"], info["scenario"], info["annee_debut"], info["est_clandestin"]
                    )
                )

    if active_avec_fin:
        print()
        print(
            "-- Cas inverse (informatif, pas forcément une erreur) : "
            "trajectoire encore active avec annee_fin quand même renseignée --"
        )
        for s in active_avec_fin:
            print("  - {}".format(s))


if __name__ == "__main__":
    main()
