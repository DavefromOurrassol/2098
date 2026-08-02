#!/usr/bin/env python3
"""
fix_lieux_emblematiques_format.py — Ourrassol 2098
====================================================

One-shot de migration (31 juillet 2026) : normalise à la source le champ
`lieux_emblematiques` de chaque zone dans geographie/{scenario}.md.

CONTEXTE
--------
Un audit du 31 juillet 2026 a montré que 195 entrées lieux_emblematiques
sur les 6 fichiers geographie/*.md sont de simples chaînes ("Delhi (Citadelle
Autonome)") au lieu du dict structuré {"nom": ..., "type": ..., "notes": ...}
attendu par tout le reste du pipeline (build_geographie_monde.py,
zoning_topdown.py, enrich_geographie_recursive.py, fix_lieux_residuels.py).
Cause probable : ces zones N1 ont été générées par une version antérieure
de build_geographie_monde.py, avant l'adoption du format dict actuel, puis
jamais retouchées depuis (elles sont traitées comme "contexte fixe" par
enrich_geographie_recursive.py).

Un correctif défensif a déjà été posé le même jour dans
enrich_geographie_recursive.py (normalisation à la volée, à chaque lecture)
et dans fix_lieux_residuels.py (tolérance de format) -- ce script-ci va plus
loin en corrigeant une bonne fois pour toutes les fichiers sources eux-mêmes,
pour que plus aucun script du pipeline (actuel ou futur) n'ait besoin de
gérer ce cas particulier.

CE QUE FAIT CE SCRIPT
----------------------
Pour chaque scénario : relit geographie/{scenario}.md (via les mêmes
fonctions que enrich_geographie_recursive.py, donc AUCUNE divergence de
format avec ce que produit déjà le pipeline), convertit chaque entrée
lieux_emblematiques de type chaîne en {"nom": <chaîne>, "type": "",
"notes": ""}, puis réécrit le fichier avec le même rendu Markdown que le
pipeline utilise déjà. AUCUN appel LLM, AUCUNE nouvelle zone ajoutée --
uniquement une correction mécanique de format. Sauvegarde .bak automatique
avant toute écriture réelle (même mécanisme que write_geographie_file).

CE QUE CE SCRIPT NE FAIT PAS
------------------------------
Ne tente pas de déduire/enrichir `type` ou `notes` pour les lieux migrés --
ces champs restent vides. Si tu veux enrichir ces informations plus tard
(catégoriser chaque lieu en ville/région/infrastructure/site_strategique,
ajouter une note de contexte), ce sera un chantier séparé, probablement
via LLM -- pas fait ici pour garder ce script strictement mécanique et
sans coût.

USAGE
-----
    python3 fix_lieux_emblematiques_format.py --scenario NOM
    python3 fix_lieux_emblematiques_format.py --all
    python3 fix_lieux_emblematiques_format.py --all --dry-run
"""

import argparse

from enrich_geographie_recursive import (
    SCENARIOS,
    load_existing_geographie,
    write_geographie_file,
)


def count_string_entries(zones):
    """Compte les entrées lieux_emblematiques qui étaient des chaînes AVANT
    normalisation -- appelé sur une copie non normalisée pour le rapport."""
    count = 0
    for zone in zones:
        for lieu in (zone.get("lieux_emblematiques") or []):
            if not isinstance(lieu, dict):
                count += 1
    return count


def process_scenario(scenario, dry_run):
    print(f"\n=== {scenario} ===")

    # load_existing_geographie() normalise déjà lieux_emblematiques en
    # interne (_normalize_lieux_emblematiques, ajouté le 31 juillet 2026) --
    # donc `zones` est TOUJOURS propre en sortie. Pour savoir combien
    # d'entrées ont réellement été corrigées, on doit le mesurer AVANT que
    # cette normalisation s'applique -- d'où la relecture manuelle ci-dessous
    # plutôt que de se fier à un compteur interne à la fonction importée.
    import re
    import yaml
    from enrich_geographie_recursive import GEOGRAPHIE_DIR, parse_md

    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    if not path.exists():
        print(f"  ✗ {path} n'existe pas -- ignoré")
        return 0

    fm_raw, _ = parse_md(path)
    zones_avant = fm_raw.get("zones") or []
    n_malformees = count_string_entries(zones_avant)

    if n_malformees == 0:
        print("  Aucune entrée à corriger -- déjà propre.")
        return 0

    print(f"  {n_malformees} entrée(s) lieux_emblematiques à normaliser")

    # Relecture via la fonction officielle du pipeline -- garantit un format
    # de sortie strictement identique à ce que produirait un run normal
    # de enrich_geographie_recursive.py.
    zones, vue_ensemble = load_existing_geographie(scenario)

    if dry_run:
        print(f"  [dry-run] {n_malformees} entrée(s) seraient normalisées, "
              f"rien n'est écrit.")
        return n_malformees

    # nb_nouvelles=0 : aucune zone ajoutée, seule la normalisation de format
    # est appliquée. write_geographie_file crée automatiquement un .bak
    # avant d'écraser le fichier existant.
    result_path = write_geographie_file(scenario, zones, vue_ensemble,
                                         nb_nouvelles=0, dry_run=False)
    print(f"  ✓ Écrit : {result_path} ({n_malformees} entrée(s) normalisée(s))")
    return n_malformees


def main():
    parser = argparse.ArgumentParser(
        description="Normalise le format de lieux_emblematiques dans "
                     "geographie/{scenario}.md (chaîne -> dict)."
    )
    parser.add_argument("--scenario", choices=SCENARIOS,
                         help="Un seul scénario")
    parser.add_argument("--all", action="store_true",
                         help="Tous les scénarios")
    parser.add_argument("--dry-run", action="store_true",
                         help="Affiche ce qui serait corrigé, sans écrire")
    args = parser.parse_args()

    if not args.scenario and not args.all:
        parser.error("Préciser --scenario NOM ou --all")

    scenarios = SCENARIOS if args.all else [args.scenario]

    print("=" * 60)
    print("OURRASSOL 2098 — Normalisation format lieux_emblematiques")
    print("=" * 60)
    if args.dry_run:
        print("MODE DRY-RUN : aucune écriture sur disque, aucun appel LLM\n")
    else:
        print("Aucun appel LLM dans ce script -- correction mécanique "
              "uniquement.\n")

    total = 0
    for scenario in scenarios:
        total += process_scenario(scenario, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    if args.dry_run:
        print(f"TOTAL : {total} entrée(s) seraient normalisées sur "
              f"{len(scenarios)} scénario(s).")
    else:
        print(f"TOTAL : {total} entrée(s) normalisée(s) sur "
              f"{len(scenarios)} scénario(s).")
    print("=" * 60)


if __name__ == "__main__":
    main()
