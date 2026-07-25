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

N'écrit jamais rien dans le vault par défaut. --apply-type-entite propage
le --apply de check_type_entite_coherence.py (backup .bak automatique, voir
ce script) ; --resolve-llm et --write-zones-manquantes propagent les flags
correspondants de check_origine_reelle_coherence.py ; --no-cache-patron-
spatial propage --no-cache à check_patron_spatial_coherence.py. Chaque flag
reste un geste explicite, comme dans les scripts sous-jacents.

USAGE
-----
    python3 scan_geographie_complet.py --all
    python3 scan_geographie_complet.py --scenario breakdown
    python3 scan_geographie_complet.py --all --apply-type-entite --resolve-llm
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
        "--write-zones-manquantes", action="store_true",
        help="Propage --write-zones-manquantes à check_origine_reelle_coherence.py."
    )
    parser.add_argument(
        "--no-cache-patron-spatial", action="store_true",
        help="Propage --no-cache à check_patron_spatial_coherence.py (repaie l'appel LLM)."
    )
    parser.add_argument(
        "--write-suspectes", action="store_true",
        help="Propage --write-suspectes à check_patron_spatial_coherence.py (écrit les "
             "nouvelles zones suspectes dans patron_spatial_suspectes.yaml)."
    )
    args = parser.parse_args()

    if args.scenario and args.scenario not in SCENARIOS:
        print(f"✗ Scénario inconnu : {args.scenario}")
        print(f"  Scénarios valides : {', '.join(SCENARIOS)}")
        sys.exit(1)

    cible = ["--all"] if args.all else ["--scenario", args.scenario]

    print("#" * 60)
    print("  SCAN GÉOGRAPHIE COMPLET — 5 étapes")
    print("#" * 60)

    resumes = []

    print("\n" + "▶" * 3 + " Étape 1/5 — check_zones_coherence.py")
    sortie = executer("check_zones_coherence.py", cible)
    resumes.append(("check_zones_coherence.py", derniere_ligne_utile(sortie)))

    print("\n" + "▶" * 3 + " Étape 2/5 — check_type_entite_coherence.py")
    args_type_entite = cible + (["--apply"] if args.apply_type_entite else [])
    sortie = executer("check_type_entite_coherence.py", args_type_entite)
    resumes.append(("check_type_entite_coherence.py", derniere_ligne_utile(sortie)))

    print("\n" + "▶" * 3 + " Étape 3/5 — check_origine_reelle_coherence.py")
    args_origine = cible[:]
    if args.resolve_llm:
        args_origine.append("--resolve-llm")
    if args.write_zones_manquantes:
        args_origine.append("--write-zones-manquantes")
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
    if args.write_suspectes:
        args_patron_spatial.append("--write-suspectes")
    sortie = executer("check_patron_spatial_coherence.py", args_patron_spatial)
    resumes.append(("check_patron_spatial_coherence.py", derniere_ligne_utile(sortie)))

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


if __name__ == "__main__":
    main()
