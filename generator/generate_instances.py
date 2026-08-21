#!/usr/bin/env python3
"""
generate_instances.py — Ourrassol 2098
=========================================

Génère les instances par scénario (instances/{slug}_{scenario}.md)
pour des entités déjà créées (entites/{slug}.md), qu'elles soient
anciennes, créées en mode custom ou en mode auto par create_entity.py
— seconde brique du futur script unifié
create_entities_and_instances.py.

LOGIQUE PAR ENTITÉ
-------------------
Pour chaque entité traitée, le script lit sa fiche dans entites/ :

  - Si le frontmatter contient un `scenario_ref` (entité créée en mode
    custom par create_entity.py) : l'instance de CE scénario reprend
    TELLES QUELLES les valeurs `role_ref`/`etat_ref` — le LLM n'est pas
    appelé pour ce scénario précis, le rôle et l'état sont des
    contraintes dures déjà fixées par l'utilisateur. Seuls les champs
    narratifs complémentaires (description journalistique, tensions...)
    sont générés par le LLM, en respectant ce rôle/état imposés.
    Les AUTRES scénarios de cette même entité restent entièrement
    libres (aucune contrainte de cohérence biographique).

  - Si le frontmatter ne contient PAS de `scenario_ref` (entité
    ancienne ou créée en mode auto) : tous les scénarios sont
    entièrement libres, exactement comme l'ancien generate_entities.py.

Ce script ne crée AUCUNE nouvelle entité — il ne fait que peupler les
instances d'entités déjà existantes dans entites/.

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...

USAGE
-----
    python3 generate_instances.py                       # toutes les entités, tous les scénarios manquants
    python3 generate_instances.py --entity le_temoin     # une seule entité
    python3 generate_instances.py --scenario breakdown   # un seul scénario, toutes entités
    python3 generate_instances.py --force                # régénère même si l'instance existe déjà
    python3 generate_instances.py --dry-run              # affiche sans rien écrire
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from instance_generation_common import (
    SCENARIOS, VALID_VARS, VALID_TRAJECTOIRE, TRAJECTOIRE_INACTIVES, SLUG_PATTERN,
    parse_md, get_client, call_claude_json, build_instance_prompt,
    validate_instance, clean_relations, write_instance_file,
    process_entity_scenario, instance_exists, load_instances_in_scenario,
    load_scenario_context, load_variables_states, load_etat_monde_reel,
    load_scenario_timeline_summary, detect_registre_leakage,
)

# ---------------------------------------------------------------------------
# Configuration propre à ce script (le reste — constantes partagées,
# construction de prompt, appel LLM, validation, écriture fichier — vit
# désormais dans instance_generation_common.py, voir ce module pour le
# détail. Factorisation faite le 9 août 2026, en préalable au chantier
# trajectoire, après découverte que ce fichier et create_entities_and_
# instances.py avaient ~20 fonctions dupliquées ayant déjà divergé — voir
# instance_generation_common.py pour le détail des divergences trouvées.)
# ---------------------------------------------------------------------------

from pathlib import Path

ENTITES_DIR = Path(__file__).resolve().parent.parent / "entites"


def load_all_entities():
    """Charge toutes les fiches entites/*.md (hors _entities_list.json)."""
    entities = {}
    if not ENTITES_DIR.exists():
        return entities
    for path in sorted(ENTITES_DIR.glob("*.md")):
        fm, _ = parse_md(path)
        slug = fm.get("slug", path.stem)
        if fm.get("type") != "entity":
            continue
        entities[slug] = fm
    return entities

def generate_all(filter_entity=None, filter_scenario=None, force=False, dry_run=False,
                  ancrage_temporel="libre"):
    print("\n" + "=" * 60)
    print("OURRASSOL 2098 — Génération des instances")
    print("=" * 60)
    if ancrage_temporel == "recent":
        print("Mode ANCRAGE RÉCENT actif : les nouvelles instances seront "
              "forcées à émerger dans les 1-3 prochaines années, ancrées "
              "dans etat_du_monde_reel.md plutôt que dans la chronologie "
              "du scénario.")

    entities = load_all_entities()
    if filter_entity:
        entities = {k: v for k, v in entities.items() if k == filter_entity}
        if not entities:
            print(f"✗ Entité '{filter_entity}' introuvable dans entites/.")
            return

    scenarios_to_process = [filter_scenario] if filter_scenario else list(SCENARIOS)

    print(f"\n{len(entities)} entité(s) à traiter, "
          f"{len(scenarios_to_process)} scénario(s) chacune.\n")

    client = get_client()
    total_created, total_skipped, total_errors = 0, 0, 0

    for slug_entite, entity_fm in entities.items():
        entity_scenarios = entity_fm.get("scenarios_instances", []) or []
        scenarios_for_this_entity = [
            s for s in scenarios_to_process if s in entity_scenarios
        ]
        if not scenarios_for_this_entity:
            continue

        print(f"\n=== {entity_fm.get('name', slug_entite)} ===")
        for scenario in scenarios_for_this_entity:
            outcome = process_entity_scenario(
                client, entity_fm, scenario, force=force, dry_run=dry_run,
                ancrage_temporel=ancrage_temporel,
                log_prefix=f"  → {slug_entite} ×",
            )
            if outcome["status"] == "created":
                total_created += 1
            elif outcome["status"] == "skipped":
                total_skipped += 1
            elif outcome["status"] in ("error", "needs_review"):
                total_errors += 1
            time.sleep(0.3)

    print(f"\n{'=' * 60}")
    print(f"✓ {total_created} instance(s) créée(s) | "
          f"{total_skipped} déjà existante(s) | {total_errors} erreur(s)")
    if dry_run:
        print("(mode --dry-run : rien n'a été écrit sur disque)")
    print("=" * 60)

    # Correctif du 16 août 2026 : contrairement à create_entities_and_
    # instances.py (mode custom) et inject_custom_events.py, ce script
    # n'enchaînait jamais le cycle post-injection (extract_localisation →
    # review_localisation --auto-resolve → validate.py), laissant les
    # instances backfillées ici sans localisation tant que David ne le
    # lançait pas à la main. Trouvé en questionnant pourquoi une instance
    # régénérée via ce script n'avait pas de localisation contrairement à
    # celles créées via le mode custom.
    if not dry_run and total_created > 0:
        run_post_injection_cycle()


def run_post_injection_cycle():
    """
    Lance automatiquement le cycle post-injection :
      extract_localisation.py → review_localisation.py --auto-resolve → validate.py
    Appelé après chaque backfill réussi (hors dry-run) — copie identique
    de la fonction du même nom dans create_entities_and_instances.py et
    inject_custom_events.py (code dupliqué à dessein, pas factorisé, pour
    rester cohérent avec la convention déjà en place sur les deux autres
    scripts plutôt que d'introduire un import croisé entre eux).
    """
    generator_dir = Path(__file__).resolve().parent
    steps = [
        ("extract_localisation", [sys.executable, str(generator_dir / "extract_localisation.py")]),
        ("review_localisation",  [sys.executable, str(generator_dir / "review_localisation.py"), "--auto-resolve"]),
        ("validate",             [sys.executable, str(generator_dir / "validate.py")]),
    ]

    print("\n" + "═" * 60)
    print("CYCLE POST-INJECTION")
    print("═" * 60)

    for name, cmd in steps:
        print(f"\n→ {' '.join(cmd[1:])}")
        result = subprocess.run(cmd, cwd=str(generator_dir))
        if result.returncode != 0:
            print(f"  [WARN] {name} s'est terminé avec le code {result.returncode}.")
            print("  → Vérifiez manuellement avant de continuer.")
            break
    else:
        print("\n✓ Cycle post-injection terminé.")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Génère les instances par scénario pour les entités d'Ourrassol 2098"
    )
    parser.add_argument("--entity", type=str,
                         help="Traiter uniquement cette entité (slug)")
    parser.add_argument("--scenario", type=str, choices=SCENARIOS,
                         help="Traiter uniquement ce scénario")
    parser.add_argument("--force", action="store_true",
                         help="Régénère même si l'instance existe déjà")
    parser.add_argument("--dry-run", action="store_true",
                         help="Appelle le LLM et valide, mais n'écrit rien sur disque")
    parser.add_argument(
        "--ancrage-temporel", choices=["libre", "recent"], default="libre",
        help="'libre' (défaut) : comportement inchangé, priorité aux jalons "
             "du scénario. 'recent' : force les nouvelles instances à "
             "émerger dans les 1-3 prochaines années, ancrées dans "
             "etat_du_monde_reel.md plutôt que dans un jalon lointain."
    )
    args = parser.parse_args()

    generate_all(
        filter_entity=args.entity,
        filter_scenario=args.scenario,
        force=args.force,
        dry_run=args.dry_run,
        ancrage_temporel=args.ancrage_temporel,
    )


if __name__ == "__main__":
    main()
