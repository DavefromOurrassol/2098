#!/usr/bin/env python3
"""
Script ponctuel — revue des chantiers zone_suspecte (backlog #4), 25 sept 2026.

Marque 12 chantiers selon les décisions de David :
  - 11 en `ignore`  (choix narratifs légitimes / faux positifs)
  - 1  en `traite`  (ameriques_multipolaires : proposition déjà appliquée,
                     5 champs identiques à la fiche — seul le statut manquait)

Laisse volontairement en `a_traiter` :
  - policy_reform / peninsule_iberique_cooperative  (#10, Portugal à trancher)
  - reference / bloc_persique_autonome             (#12, à appliquer via GUI)

Passe par chantiers.mettre_a_jour_chantier() (même chemin que le GUI).
Sauvegarde chantiers_geographie.yaml en .bak avant toute écriture.

Usage (depuis la racine du vault) :
  python3 generator/marquer_zones_suspectes_25sept.py            # aperçu
  python3 generator/marquer_zones_suspectes_25sept.py --execute  # écriture
"""
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml  # noqa: E402
import chantiers  # noqa: E402

DECISIONS = [
    # (scenario, cible, statut, justification)
    ("fortress_world", "amazonie_pacte_vert", "ignore",
     "Enclave neutre précaire plausible ; proposition contraire au lore"),
    ("fortress_world", "espace_nordique_arctique", "ignore",
     "Zone Hyphan (Euro-Nord), choix de David ; proposition périmée destructrice"),
    ("fortress_world", "singapour_megapole", "ignore",
     "Cité-forteresse à neutralité armée, conforme"),
    ("fortress_world", "tuvalu_refugies_climatiques", "ignore",
     "Refuge résiduel plausible ; proposition incohérente"),
    ("fortress_world", "al_hima", "ignore",
     "Zone Hyphan, collectivisme voulu"),
    ("new_sustainability", "bloc_eurasien_souverainiste", "ignore",
     "Friction narrative utile ; proposition contredit le nom"),
    ("new_sustainability", "moyen_orient_golfe", "ignore",
     "Faux positif : conflit 2026 = histoire réelle de départ"),
    ("eco_communalism", "inde_bassins_sacres", "ignore",
     "Nuance, pas incohérence"),
    ("eco_communalism", "japon_archipel_resilient", "ignore",
     "Nuance, pas incohérence"),
    ("policy_reform", "espace_eurasiatique", "ignore",
     "Contre-modèle interne conforme à 'coopération non totale'"),
    ("reference", "pacte_des_souverains", "ignore",
     "Décision David 25 sept, pas de proposition"),
    ("reference", "ameriques_multipolaires", "traite",
     "Proposition déjà appliquée (5 champs identiques), statut non mis à jour"),
]


def charger():
    data = yaml.safe_load(chantiers.CHANTIERS_FILE.read_text(encoding="utf-8"))
    items = data.get("chantiers", data) if isinstance(data, dict) else data
    if isinstance(items, dict):
        items = [dict(v, id=k) for k, v in items.items()]
    return items


def trouver(items, scenario, cible):
    return [c for c in items if isinstance(c, dict)
            and c.get("scenario") == scenario and c.get("cible") == cible
            and c.get("type") == "zone_suspecte"]


def main():
    execute = "--execute" in sys.argv
    items = charger()

    print(f"Fichier : {chantiers.CHANTIERS_FILE}")
    print(f"Mode    : {'ÉCRITURE' if execute else 'APERÇU (rien écrit)'}\n")

    erreurs = 0
    for sc, cible, statut, raison in DECISIONS:
        trouves = trouver(items, sc, cible)
        if len(trouves) != 1:
            print(f"  ✗ {sc}/{cible} : {len(trouves)} chantier(s) trouvé(s), attendu 1")
            erreurs += 1
            continue
        actuel = trouves[0].get("statut")
        if actuel != "a_traiter":
            print(f"  ✗ {sc}/{cible} : statut actuel {actuel!r}, attendu 'a_traiter'")
            erreurs += 1
            continue
        print(f"  · {sc:20} {cible:32} a_traiter -> {statut:7} ({raison})")

    if erreurs:
        print(f"\n{erreurs} anomalie(s) — rien écrit. Envoie cette sortie à Claude.")
        sys.exit(1)

    if not execute:
        print(f"\n{len(DECISIONS)} chantier(s) prêts. Relance avec --execute pour écrire.")
        return

    bak = chantiers.CHANTIERS_FILE.with_suffix(".yaml.bak")
    shutil.copy2(chantiers.CHANTIERS_FILE, bak)
    print(f"\nSauvegarde : {bak}")

    aujourd_hui = date.today().isoformat()
    for sc, cible, statut, _ in DECISIONS:
        chantiers.mettre_a_jour_chantier(sc, cible, statut=statut,
                                         date_traitement=aujourd_hui)

    # Relecture de contrôle
    items = charger()
    ok = 0
    for sc, cible, statut, _ in DECISIONS:
        c = trouver(items, sc, cible)[0]
        if c.get("statut") == statut:
            ok += 1
        else:
            print(f"  ✗ relecture {sc}/{cible} : {c.get('statut')!r} au lieu de {statut!r}")
    restants = [f"{c.get('scenario')}/{c.get('cible')}" for c in items
                if isinstance(c, dict) and c.get("type") == "zone_suspecte"
                and c.get("statut") == "a_traiter"]
    print(f"\nRelecture : {ok}/{len(DECISIONS)} statuts conformes.")
    print(f"zone_suspecte encore a_traiter ({len(restants)}) : {', '.join(restants)}")


if __name__ == "__main__":
    main()
