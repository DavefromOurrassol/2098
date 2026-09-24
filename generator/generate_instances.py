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

AJOUTS DU 24 SEPTEMBRE 2026 (pilotage depuis le GUI, une entité + un scénario)
    --role "..."        nouveau rôle imposé pour le scénario de référence de
                        l'entité (remplace role_ref dans la fiche entité)
    --consigne "..."    consigne pour un AUTRE scénario (remplace
                        consignes_scenarios[scénario] dans la fiche entité)
    --injection-custom  conserve le bloc d'impact sur les variables (comme
                        une instance créée en mode custom)
  --role et --consigne exigent --entity et --scenario, et sont ÉCRITS dans la
  fiche entité avant la génération (sauf --dry-run) : une régénération
  ultérieure les retrouvera. Combinés en général avec --force.
"""

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

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

def _mettre_a_jour_fiche_entite(slug, role=None, scenario=None, consigne=None, dry_run=False):
    """Met à jour role_ref et/ou consignes_scenarios[scenario] dans le
    frontmatter de entites/{slug}.md (24 septembre 2026). Réécrit
    uniquement ces deux clés (blocs retirés puis réinsérés en fin de
    frontmatter) ; vérifie que le YAML se relit et que toutes les autres
    clés sont inchangées avant d'écrire. Retourne le frontmatter à jour,
    ou None en cas d'échec (rien n'est écrit)."""
    path = ENTITES_DIR / f"{slug}.md"
    texte = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", texte, re.S)
    if not m:
        print(f"✗ Frontmatter introuvable dans {path.name}")
        return None
    fm_txt = m.group(1)
    fm = yaml.safe_load(fm_txt) or {}
    nouveau = dict(fm)
    if role is not None:
        nouveau["role_ref"] = " ".join(role.split())
    if consigne is not None:
        cons = dict(fm.get("consignes_scenarios") or {})
        cons[scenario] = " ".join(consigne.split())
        nouveau["consignes_scenarios"] = cons

    # Retire les blocs existants de ces deux clés (clé + lignes indentées).
    lignes, garder, dans_bloc = fm_txt.split("\n"), [], False
    for ligne in lignes:
        if re.match(r"^(role_ref|consignes_scenarios):", ligne):
            dans_bloc = ligne.split(":")[0] in (("role_ref",) if role is not None else ()) + \
                        (("consignes_scenarios",) if consigne is not None else ())
            if dans_bloc:
                continue
        elif dans_bloc and (ligne.startswith(" ") or ligne == ""):
            continue
        else:
            dans_bloc = False
        garder.append(ligne)
    ajout = {}
    if role is not None:
        ajout["role_ref"] = nouveau["role_ref"]
    if consigne is not None:
        ajout["consignes_scenarios"] = nouveau["consignes_scenarios"]
    fm_nouveau_txt = "\n".join(garder).rstrip("\n") + "\n" + \
        yaml.dump(ajout, allow_unicode=True, sort_keys=False, width=1000).rstrip("\n")
    relu = yaml.safe_load(fm_nouveau_txt) or {}
    if relu != nouveau:
        print(f"✗ Mise à jour de {path.name} annulée : la relecture ne correspond pas")
        return None
    if dry_run:
        print(f"  (dry-run) fiche {path.name} NON modifiée")
    else:
        path.write_text("---\n" + fm_nouveau_txt + texte[m.end(1):], encoding="utf-8")
        print(f"  ✓ Fiche {path.name} mise à jour ({', '.join(ajout)})")
    return nouveau


def generate_all(filter_entity=None, filter_scenario=None, force=False, dry_run=False,
                  ancrage_temporel="libre", injection_custom=False, fm_override=None):
    print("\n" + "=" * 60)
    print("OURRASSOL 2098 — Génération des instances")
    print("=" * 60)
    if ancrage_temporel == "recent":
        print("Mode ANCRAGE RÉCENT actif : les nouvelles instances seront "
              "forcées à émerger dans les 1-3 prochaines années, ancrées "
              "dans etat_du_monde_reel.md plutôt que dans la chronologie "
              "du scénario.")

    entities = load_all_entities()
    # fm_override : fiche mise à jour en mémoire (--role/--consigne), pour
    # que --dry-run utilise déjà le nouveau rôle/consigne sans rien écrire.
    for slug_o, fm_o in (fm_override or {}).items():
        entities[slug_o] = fm_o
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
                injection_custom=injection_custom,
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
    parser.add_argument("--role", type=str, default=None,
                         help="Nouveau rôle imposé pour le scénario de référence de l'entité "
                              "(écrit dans role_ref). Exige --entity et --scenario = scénario de référence.")
    parser.add_argument("--consigne", type=str, default=None,
                         help="Consigne pour un autre scénario (écrite dans consignes_scenarios). "
                              "Exige --entity et --scenario.")
    parser.add_argument("--injection-custom", action="store_true",
                         help="Conserve le bloc d'impact sur les variables (comme en mode custom).")
    args = parser.parse_args()

    role = (args.role or "").strip() or None
    consigne = (args.consigne or "").strip() or None
    if role or consigne:
        if not (args.entity and args.scenario):
            sys.exit("✗ --role et --consigne exigent --entity et --scenario.")
        entities = load_all_entities()
        fm = entities.get(args.entity)
        if not fm:
            sys.exit(f"✗ Entité '{args.entity}' introuvable dans entites/.")
        if args.scenario not in (fm.get("scenarios_instances") or []):
            sys.exit(f"✗ '{args.scenario}' n'est pas un scénario couvert par {args.entity} "
                     f"({', '.join(fm.get('scenarios_instances') or [])}).")
        ref = fm.get("scenario_ref")
        if role and args.scenario != ref:
            sys.exit(f"✗ --role ne s'applique qu'au scénario de référence ({ref}). "
                     f"Pour {args.scenario}, utiliser --consigne.")
        if consigne and args.scenario == ref:
            sys.exit(f"✗ {ref} est le scénario de référence : utiliser --role, pas --consigne.")
        print(f"Mise à jour de la fiche entité {args.entity}...")
        fm_maj = _mettre_a_jour_fiche_entite(args.entity, role=role, scenario=args.scenario,
                                              consigne=consigne, dry_run=args.dry_run)
        if fm_maj is None:
            sys.exit(1)
        fm_override = {args.entity: fm_maj}
    else:
        fm_override = None
        if not args.force:
            print("  ⚠ Sans --force, une instance déjà existante ne sera pas régénérée.")

    generate_all(
        filter_entity=args.entity,
        filter_scenario=args.scenario,
        force=args.force,
        dry_run=args.dry_run,
        ancrage_temporel=args.ancrage_temporel,
        injection_custom=args.injection_custom,
        fm_override=fm_override,
    )


if __name__ == "__main__":
    main()
