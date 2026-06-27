#!/usr/bin/env python3
"""
undo_custom.py — Ourrassol 2098
================================

Retire des entités, instances, événements ou event_instances du lore,
avec gestion des dépendances et backup automatique.

USAGE
-----
    python3 undo_custom.py              # dry-run depuis undo_queue.yaml
    python3 undo_custom.py --execute    # supprime réellement
    python3 undo_custom.py --slug mon_evenement_breakdown --type event_instance --generalisation no
    python3 undo_custom.py --slug mon_entite --type instance --generalisation yes --execute

QUEUE
-----
Fichier evenements_custom/undo_queue.yaml :

    undo:
      - type: event_instance
        slug: mon_evenement_breakdown
        generalisation: no
      - type: instance
        slug: mon_entite_reference
        generalisation: yes

TYPES
-----
    event_instance  : retire le fichier event_instance + registre
    instance        : retire le fichier instance + références alliances/oppositions
    event           : (alias generalisation:yes sur event_instance) archétype + toutes instances
    entite          : (alias generalisation:yes sur instance) archétype + toutes instances

GENERALISATION
--------------
    no  : retire uniquement le fichier ciblé + ses dépendances directes
    yes : remonte à l'archétype et retire tout (toutes instances/event_instances,
          tous scénarios)
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR       = Path(__file__).resolve().parent
EVENEMENTS_DIR      = VAULT_ROOT / "evenements"
EVENT_INSTANCES_DIR = VAULT_ROOT / "event_instances"
ENTITES_DIR         = VAULT_ROOT / "entites"
INSTANCES_DIR       = VAULT_ROOT / "instances"
REGISTRE_PATH       = GENERATOR_DIR / "registre_evenements.md"
EVENEMENTS_CUSTOM_DIR = VAULT_ROOT / "evenements_custom"
UNDO_QUEUE_PATH     = EVENEMENTS_CUSTOM_DIR / "undo_queue.yaml"
PROCESSED_PATH      = EVENEMENTS_CUSTOM_DIR / "processed.yaml"
NEEDS_REVIEW_PATH   = EVENEMENTS_CUSTOM_DIR / "needs_review.yaml"
LAST_VALIDATED_PATH  = GENERATOR_DIR / "last_validated.json"
ENTITIES_LIST_PATH   = ENTITES_DIR / "_entities_list.json"

VALID_SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def parse_md_fm(filepath):
    """Retourne le frontmatter dict d'un fichier .md, ou {}."""
    p = Path(filepath)
    if not p.exists():
        return {}
    raw = p.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---", raw, re.DOTALL)
    if not m:
        return {}
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        return yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        return {}


def backup_file(path):
    """Crée un backup .bak du fichier."""
    src = Path(path)
    if not src.exists():
        return None
    bak = src.with_suffix(src.suffix + ".bak")
    shutil.copy2(src, bak)
    return bak


def remove_file(path, dry_run, report):
    """Backup + suppression d'un fichier."""
    p = Path(path)
    if not p.exists():
        report.append(f"  [SKIP] {p.name} — introuvable")
        return
    if dry_run:
        report.append(f"  [DRY] Supprimerait : {p}")
    else:
        bak = backup_file(p)
        p.unlink()
        report.append(f"  [DEL] {p.name} → backup {bak.name}")


def load_yaml_list(path, key):
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return data.get(key, []) or []
    except Exception:
        return []


def save_yaml_list(path, items, key):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {key: items}
    p.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8"
    )


def reset_last_validated(dry_run, report):
    if dry_run:
        report.append(f"  [DRY] Resetterait last_validated.json")
        return
    if LAST_VALIDATED_PATH.exists():
        LAST_VALIDATED_PATH.unlink()
        report.append(f"  [DEL] last_validated.json resetté")


# ---------------------------------------------------------------------------
# _entities_list.json
# ---------------------------------------------------------------------------

def remove_from_entities_list(base_slug, dry_run, report):
    """Retire l'entrée correspondant à base_slug dans entites/_entities_list.json."""
    import json
    p = ENTITIES_LIST_PATH
    if not p.exists():
        return
    try:
        entities = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return

    filtered = [e for e in entities if e.get("slug") != base_slug]
    removed = len(entities) - len(filtered)

    if removed == 0:
        return

    if dry_run:
        report.append(f"  [DRY] Retirerait '{base_slug}' de _entities_list.json")
    else:
        backup_file(p)
        p.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")
        report.append(f"  [JSON] '{base_slug}' retiré de _entities_list.json")


# ---------------------------------------------------------------------------
# Registre
# ---------------------------------------------------------------------------

def remove_from_registre(event_slug, scenario, dry_run, report):
    """Retire les lignes de type=evenement pour event_slug dans registre_evenements.md."""
    if not REGISTRE_PATH.exists():
        return

    text = REGISTRE_PATH.read_text(encoding="utf-8")
    lines = text.split("\n")
    new_lines = []
    removed = 0
    for line in lines:
        # Ligne de table événement : | evenement | date | slug | ... |
        if line.startswith("|") and "evenement" in line and event_slug in line:
            # Vérifier scénario si fourni
            if scenario is None or True:  # on retire toutes occurrences du slug
                removed += 1
                if dry_run:
                    report.append(f"  [DRY] Retirerait ligne registre : {line.strip()[:80]}")
                continue
        new_lines.append(line)

    if removed > 0 and not dry_run:
        REGISTRE_PATH.write_text("\n".join(new_lines), encoding="utf-8")
        report.append(f"  [REG] {removed} ligne(s) retirée(s) du registre pour '{event_slug}'")


# ---------------------------------------------------------------------------
# processed.yaml / needs_review.yaml
# ---------------------------------------------------------------------------

def remove_from_processed(slug, dry_run, report):
    """Retire toute entrée concernant slug dans processed.yaml et needs_review.yaml."""
    for path, key in [(PROCESSED_PATH, "processed"), (NEEDS_REVIEW_PATH, "needs_review")]:
        items = load_yaml_list(path, key)
        filtered = []
        removed = 0
        for item in items:
            idea = item.get("idea", {}) if isinstance(item, dict) else {}
            item_id = idea.get("id", "") if idea else ""
            # Matcher sur l'id ou les scénarios injectés
            injected = item.get("injected_scenarios", []) if isinstance(item, dict) else []
            failed = item.get("failed_scenarios", []) if isinstance(item, dict) else []
            # Slug de base (sans suffixe scénario)
            base_slug = re.sub(r"_(" + "|".join(VALID_SCENARIOS) + r")$", "", slug)
            if item_id == base_slug or item_id == slug:
                removed += 1
                if dry_run:
                    report.append(f"  [DRY] Retirerait entrée '{item_id}' de {path.name}")
                continue
            filtered.append(item)
        if removed > 0 and not dry_run:
            save_yaml_list(path, filtered, key)
            report.append(f"  [YAML] {removed} entrée(s) retirée(s) de {path.name}")


# ---------------------------------------------------------------------------
# Nettoyage alliances/oppositions
# ---------------------------------------------------------------------------

def remove_alliance_refs(instance_slug, scenario, dry_run, report):
    """Retire les références à instance_slug dans alliances/oppositions des autres instances."""
    if not INSTANCES_DIR.exists():
        return
    pattern = re.compile(
        r"^(\s*-\s*)" + re.escape(f"[[{instance_slug}]]") + r"\s*$",
        re.MULTILINE
    )
    pattern2 = re.compile(
        r"^(\s*-\s*)" + re.escape(instance_slug) + r"\s*$",
        re.MULTILINE
    )
    for fname in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        if fname.stem == instance_slug:
            continue
        text = fname.read_text(encoding="utf-8")
        new_text = pattern.sub("", text)
        new_text = pattern2.sub("", new_text)
        if new_text != text:
            if dry_run:
                report.append(f"  [DRY] Retirerait réf '{instance_slug}' dans {fname.name}")
            else:
                backup_file(fname)
                fname.write_text(new_text, encoding="utf-8")
                report.append(f"  [REF] Référence retirée de {fname.name}")


# ---------------------------------------------------------------------------
# Résolution des slugs
# ---------------------------------------------------------------------------

def resolve_event_instance(slug, generalisation):
    """
    Retourne la liste des fichiers event_instance à supprimer et l'archétype éventuel.
    """
    targets = []
    archetype = None

    if generalisation == "yes":
        # Trouver le slug de base (sans suffixe scénario)
        base = re.sub(r"_(" + "|".join(VALID_SCENARIOS) + r")$", "", slug)
        archetype = EVENEMENTS_DIR / f"{base}.md"
        for sc in VALID_SCENARIOS:
            p = EVENT_INSTANCES_DIR / f"{base}_{sc}.md"
            if p.exists():
                targets.append((p, sc, base))
    else:
        # Slug exact
        sc_found = None
        for sc in VALID_SCENARIOS:
            if slug.endswith(f"_{sc}"):
                sc_found = sc
                break
        base = re.sub(r"_(" + "|".join(VALID_SCENARIOS) + r")$", "", slug)
        p = EVENT_INSTANCES_DIR / f"{slug}.md"
        targets.append((p, sc_found, base))

    return targets, archetype


def resolve_instance(slug, generalisation):
    """
    Retourne la liste des fichiers instance à supprimer et l'archétype entité éventuel.
    """
    targets = []
    archetype = None

    if generalisation == "yes":
        base = re.sub(r"_(" + "|".join(VALID_SCENARIOS) + r")$", "", slug)
        archetype = ENTITES_DIR / f"{base}.md"
        for sc in VALID_SCENARIOS:
            p = INSTANCES_DIR / f"{base}_{sc}.md"
            if p.exists():
                targets.append((p, sc, base))
    else:
        sc_found = None
        for sc in VALID_SCENARIOS:
            if slug.endswith(f"_{sc}"):
                sc_found = sc
                break
        p = INSTANCES_DIR / f"{slug}.md"
        targets.append((p, sc_found, slug))

    return targets, archetype


# ---------------------------------------------------------------------------
# Exécution d'un item
# ---------------------------------------------------------------------------

def process_item(item_type, slug, generalisation, dry_run, report):
    report.append(f"\n── {item_type} / {slug} / generalisation={generalisation} ──")

    if item_type in ("event_instance", "event"):
        gen = "yes" if item_type == "event" else generalisation
        targets, archetype = resolve_event_instance(slug, gen)

        for (path, sc, base_slug) in targets:
            remove_file(path, dry_run, report)
            remove_from_registre(base_slug, sc, dry_run, report)

        if archetype:
            remove_file(archetype, dry_run, report)

        base = re.sub(r"_(" + "|".join(VALID_SCENARIOS) + r")$", "", slug)
        remove_from_processed(base, dry_run, report)

    elif item_type in ("instance", "entite"):
        gen = "yes" if item_type == "entite" else generalisation
        targets, archetype = resolve_instance(slug, gen)

        for (path, sc, base_slug) in targets:
            remove_file(path, dry_run, report)
            if sc:
                remove_alliance_refs(path.stem, sc, dry_run, report)

        if archetype:
            remove_file(archetype, dry_run, report)

        base = re.sub(r"_(" + "|".join(VALID_SCENARIOS) + r")$", "", slug)
        remove_from_processed(base, dry_run, report)
        remove_from_entities_list(base, dry_run, report)

    else:
        report.append(f"  [WARN] Type inconnu : '{item_type}' — ignoré")


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def run(items, dry_run):
    report = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode = "DRY-RUN" if dry_run else "EXECUTE"
    report.append(f"undo_custom.py — {now} — mode {mode}")
    report.append(f"{len(items)} item(s) à traiter\n")

    for item in items:
        item_type   = str(item.get("type", "")).strip()
        slug        = str(item.get("slug", "")).strip()
        generalisation = str(item.get("generalisation", "no")).strip().lower()
        if generalisation not in ("yes", "no"):
            generalisation = "no"

        if not item_type or not slug:
            report.append(f"  [SKIP] Item incomplet : {item}")
            continue

        process_item(item_type, slug, generalisation, dry_run, report)

    # Reset last_validated si on a réellement supprimé des fichiers
    reset_last_validated(dry_run, report)

    report.append(f"\n{'═'*60}")
    report.append(f"{'[DRY-RUN] Aucune modification effectuée.' if dry_run else 'Terminé. Lancez validate.py pour vérifier la base.'}")

    print("\n".join(report))

    # Vider la queue si --execute
    if not dry_run and UNDO_QUEUE_PATH.exists():
        save_yaml_list(UNDO_QUEUE_PATH, [], "undo")
        print(f"\nQueue vidée : {UNDO_QUEUE_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description="Retire des entités/événements du lore Ourrassol 2098"
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Supprime réellement (défaut : dry-run)"
    )
    parser.add_argument(
        "--slug", type=str, default=None,
        help="Slug unique à retirer (sans passer par la queue)"
    )
    parser.add_argument(
        "--type", dest="item_type", type=str, default=None,
        choices=["event_instance", "instance", "event", "entite"],
        help="Type de l'item (requis avec --slug)"
    )
    parser.add_argument(
        "--generalisation", type=str, default="no",
        choices=["yes", "no"],
        help="Remonte à l'archétype et supprime tout (défaut : no)"
    )
    args = parser.parse_args()

    dry_run = not args.execute

    if args.slug:
        if not args.item_type:
            sys.exit("--type est requis avec --slug")
        items = [{"type": args.item_type, "slug": args.slug,
                  "generalisation": args.generalisation}]
    else:
        raw = load_yaml_list(UNDO_QUEUE_PATH, "undo")
        if not raw:
            print(f"Queue vide ({UNDO_QUEUE_PATH}). Rien à faire.")
            print("Utilise --slug / --type / --generalisation pour un retrait direct.")
            return
        items = raw

    run(items, dry_run)


if __name__ == "__main__":
    main()
