#!/usr/bin/env python3
"""
scan_geographie_complet.py — Ourrassol 2098

Orchestrateur : lance dans l'ordre check_zones_coherence.py,
check_type_entite_coherence.py, check_origine_reelle_coherence.py,
check_conventions_territoires.py et check_patron_spatial_coherence.py
(P24 étape C.1, ajouté le 25 juillet), puis affiche un résumé consolidé.
N'importe pas leur code -- chaque script reste indépendant, utilisable seul
comme avant (entrée sidebar GUI intacte), ce script se contente de les
appeler en sous-processus dans l'ordre où ils ont du sens : cohérence
structurelle d'abord, puis le trou de données qui peut fausser les
suivants (voir check_type_entite_coherence.py), puis le garde-fou fin
zone-par-zone, puis l'audit cross-scénario des territoires ambigus, puis
enfin le contrôle de cohérence narrative patron spatial (les trois
derniers sont complémentaires, pas redondants : le garde-fou compare une
zone à sa propre chaîne de parenté, l'audit territoires compare le même
territoire entre scénarios, le contrôle patron spatial compare une zone à
la logique narrative de SON scénario -- voir check_patron_spatial_
coherence.py pour le détail).

HARMONISATION --write-chantiers (25 juillet 2026, point 4.3 du handoff
fusion chantiers_geographie.yaml)
------------------------------------------------------------------------
Depuis la migration de check_zones_coherence.py, check_origine_reelle_
coherence.py et check_patron_spatial_coherence.py vers le module partagé
chantiers.py, les trois exposent le MÊME flag --write-chantiers (écrit
dans chantiers_geographie.yaml, fichier unique du pipeline géographie).
Cet orchestrateur expose désormais un seul --write-chantiers, propagé aux
étapes 1, 3 et 5 -- remplace les anciens --write-suspectes (étape 5 seule)
et --write-zones-manquantes (étape 3 seule), qui ne correspondent plus à
aucun flag réel des scripts sous-jacents depuis leur migration. Au passage,
l'étape 1 gagne une propagation d'écriture qu'elle n'avait jamais eue --
avant cette harmonisation, --write-suspectes ne couvrait que l'étape 5, et
un pays totalement absent détecté en étape 1 n'était jamais suivi sans
relancer check_zones_coherence.py à la main avec son propre --write-
chantiers.

6e étape optionnelle (--generer-propositions-topdown, ajoutée le 25
juillet, P24 étape C) : propage vers generer_zones_topdown.py
--review-topdown -- génère des propositions pour les chantiers
`a_traiter` de chantiers_geographie.yaml (pays sans zone ET zones
suspectes, les deux types désormais couverts puisque chantiers.py les
unifie). Volontairement APRÈS les étapes 1/3/5 pour qu'un chantier tout
juste ajouté dans CE run (via --write-chantiers) soit immédiatement
éligible. Coûte de vrais appels LLM -- jamais lancé par défaut, comme
--resolve-llm. --apply-topdown N'EST JAMAIS propagé ici et ne le sera
jamais : appliquer automatiquement à la suite d'un --review-topdown dans
le même run contournerait le geste de review humain (proposition_
approuvee: false → true) qui est tout le sens de ce workflow -- et de
toute façon n'appliquerait rien, puisque rien n'aurait encore été
approuvé. --apply-topdown reste une commande volontairement séparée,
lancée à la main une fois la review faite.

N'écrit jamais rien dans le vault par défaut. --write-chantiers écrit
dans chantiers_geographie.yaml (jamais dans geographie/ lui-même, lecture
seule pour ces 3 scripts) ; --apply-type-entite propage le --apply de
check_type_entite_coherence.py (backup .bak automatique, voir ce
script) ; --resolve-llm propage le flag correspondant de check_origine_
reelle_coherence.py ; --no-cache-patron-spatial propage --no-cache à
check_patron_spatial_coherence.py. Chaque flag reste un geste explicite,
comme dans les scripts sous-jacents.

USAGE
-----
    python3 scan_geographie_complet.py --all
    python3 scan_geographie_complet.py --scenario breakdown
    python3 scan_geographie_complet.py --all --apply-type-entite --resolve-llm
    python3 scan_geographie_complet.py --all --write-chantiers --generer-propositions-topdown
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]


def executer(script: str, args: list) -> str:
    """Lance un script du dossier en sous-processus, affiche sa sortie en
    direct (stdout+stderr mêlés dans l'ordre), retourne la sortie complète
    pour en extraire la ligne de résumé ensuite. Un script qui échoue
    (ex. zones_pays.json introuvable) n'interrompt pas les suivants --
    chaque étape est indépendante, comme si on les lançait à la main."""
    resultat = subprocess.run(
        [sys.executable, script] + args,
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
    )
    sortie = resultat.stdout + resultat.stderr
    print(sortie)
    return sortie


def derniere_ligne_utile(sortie: str) -> str:
    """Ligne de résumé -- par convention les scripts terminent tous par
    une bordure '===' puis une ligne "Terminé — ...", donc on cherche
    depuis la fin la dernière ligne contenant "Terminé" plutôt que la toute
    dernière ligne (qui est la bordure de fermeture, pas le résumé)."""
    lignes = [l.strip() for l in sortie.split("\n") if l.strip()]
    for l in reversed(lignes):
        if "Terminé" in l:
            return l
    return lignes[-1] if lignes else "(pas de sortie)"


def main():
    parser = argparse.ArgumentParser(
        description="Lance les 5 scripts de diagnostic géographie en séquence, "
                     "avec résumé consolidé. Lecture seule sauf flags explicites."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", help="Scénario unique")
    group.add_argument("--all", action="store_true", help="Les 6 scénarios")
    parser.add_argument(
        "--apply-type-entite", action="store_true",
        help="Propage --apply à check_type_entite_coherence.py (corrige, backup .bak)."
    )
    parser.add_argument(
        "--resolve-llm", action="store_true",
        help="Propage --resolve-llm à check_origine_reelle_coherence.py."
    )
    parser.add_argument(
        "--write-chantiers", action="store_true",
        help="Propage --write-chantiers aux étapes 1 (check_zones_coherence.py), "
             "3 (check_origine_reelle_coherence.py) et 5 (check_patron_spatial_"
             "coherence.py) -- écrit les nouveaux chantiers détectés dans "
             "chantiers_geographie.yaml. Remplace les anciens --write-suspectes/"
             "--write-zones-manquantes, désormais un seul flag pour les 3 étapes "
             "depuis leur migration vers chantiers.py."
    )
    parser.add_argument(
        "--no-cache-patron-spatial", action="store_true",
        help="Propage --no-cache à check_patron_spatial_coherence.py (repaie l'appel LLM)."
    )
    parser.add_argument(
        "--generer-propositions-topdown", action="store_true",
        help="6e étape optionnelle : lance generer_zones_topdown.py --review-topdown "
             "(P24 étape C.3) -- génère une proposition pour chaque chantier "
             "`a_traiter` de chantiers_geographie.yaml (pays sans zone + zones "
             "suspectes). Coûte de vrais appels LLM, jamais lancé par défaut. "
             "N'applique jamais rien (pas de --apply-topdown ici) -- la review "
             "reste un geste séparé, volontairement."
    )
    args = parser.parse_args()

    if args.scenario and args.scenario not in SCENARIOS:
        print(f"✗ Scénario inconnu : {args.scenario}")
        print(f"  Scénarios valides : {', '.join(SCENARIOS)}")
        sys.exit(1)

    cible = ["--all"] if args.all else ["--scenario", args.scenario]

    print("#" * 60)
    print("  SCAN GÉOGRAPHIE COMPLET — 5 étapes"
          + (" + génération top-down" if args.generer_propositions_topdown else ""))
    print("#" * 60)

    resumes = []

    print("\n" + "▶" * 3 + " Étape 1/5 — check_zones_coherence.py")
    args_zones = cible + (["--write-chantiers"] if args.write_chantiers else [])
    sortie = executer("check_zones_coherence.py", args_zones)
    resumes.append(("check_zones_coherence.py", derniere_ligne_utile(sortie)))

    print("\n" + "▶" * 3 + " Étape 2/5 — check_type_entite_coherence.py")
    args_type_entite = cible + (["--apply"] if args.apply_type_entite else [])
    sortie = executer("check_type_entite_coherence.py", args_type_entite)
    resumes.append(("check_type_entite_coherence.py", derniere_ligne_utile(sortie)))

    print("\n" + "▶" * 3 + " Étape 3/5 — check_origine_reelle_coherence.py")
    args_origine = cible[:]
    if args.resolve_llm:
        args_origine.append("--resolve-llm")
    if args.write_chantiers:
        args_origine.append("--write-chantiers")
    sortie = executer("check_origine_reelle_coherence.py", args_origine)
    resumes.append(("check_origine_reelle_coherence.py", derniere_ligne_utile(sortie)))

    print("\n" + "▶" * 3 + " Étape 4/5 — check_conventions_territoires.py")
    if not args.all:
        print("  · N'a de sens qu'avec --all -- la notion de \"varie entre scénarios\" "
              "suppose plusieurs scénarios à comparer. Résultat ci-dessous non significatif.")
    sortie = executer("check_conventions_territoires.py", cible)
    resumes.append(("check_conventions_territoires.py", derniere_ligne_utile(sortie)))

    print("\n" + "▶" * 3 + " Étape 5/5 — check_patron_spatial_coherence.py")
    args_patron_spatial = cible[:]
    if args.no_cache_patron_spatial:
        args_patron_spatial.append("--no-cache")
    if args.write_chantiers:
        args_patron_spatial.append("--write-chantiers")
    sortie = executer("check_patron_spatial_coherence.py", args_patron_spatial)
    resumes.append(("check_patron_spatial_coherence.py", derniere_ligne_utile(sortie)))

    if args.generer_propositions_topdown:
        print("\n" + "▶" * 3 + " Étape 6/6 — generer_zones_topdown.py --review-topdown")
        if not args.write_chantiers:
            print("  · Lancé sans --write-chantiers aux étapes 1/3/5 -- seuls les "
                  "chantiers déjà `a_traiter` avant ce run seront repris, pas ceux "
                  "tout juste détectés dans ce même run.")
        args_topdown = ["--review-topdown"] + cible
        sortie = executer("generer_zones_topdown.py", args_topdown)
        resumes.append(("generer_zones_topdown.py --review-topdown", derniere_ligne_utile(sortie)))

    print("\n" + "#" * 60)
    print("  RÉSUMÉ CONSOLIDÉ")
    print("#" * 60)
    for nom, ligne in resumes:
        print(f"  [{nom}]")
        print(f"    {ligne}")

    if not args.apply_type_entite:
        print("\n  · check_type_entite_coherence.py lancé sans --apply-type-entite "
              "(aperçu seul, rien corrigé)")
    if not args.all:
        print("  · check_conventions_territoires.py non significatif en mode --scenario "
              "(relancer avec --all pour un vrai résultat)")
    if not args.no_cache_patron_spatial:
        print("  · check_patron_spatial_coherence.py a pu servir des résultats en cache "
              "(relancer avec --no-cache-patron-spatial pour forcer un nouvel appel LLM)")
    if args.generer_propositions_topdown:
        print("  · generer_zones_topdown.py : propositions attachées aux chantiers "
              "(chantiers_geographie.yaml, proposition_approuvee: false), RIEN appliqué "
              "au vault -- relire et approuver à la main, puis lancer "
              "generer_zones_topdown.py --apply-topdown séparément.")


if __name__ == "__main__":
    main()
