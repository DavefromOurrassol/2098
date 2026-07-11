#!/usr/bin/env python3
"""
extract_phantom_slugs.py — Ourrassol 2098
==========================================

Extrait les slugs fantômes (alliances/oppositions non trouvés dans les
instances réelles) depuis une ou plusieurs sources, génère les rôles via
le LLM, et alimente entites_custom/queue.yaml.

SOURCES
-------
  enrich    : rapport enrich_minimal_report.md
  validate  : sortie de validate.py --verbose (via subprocess ou fichier)
  all       : les deux combinées (défaut)

USAGE
-----
    python3 extract_phantom_slugs.py                        # all, écrit queue.yaml
    python3 extract_phantom_slugs.py --source enrich        # rapport seulement
    python3 extract_phantom_slugs.py --source validate      # validate seulement
    python3 extract_phantom_slugs.py --dry-run              # affiche sans écrire
    python3 extract_phantom_slugs.py --report PATH          # rapport alternatif
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

from llm_client import call_llm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
REPORT_PATH = VAULT_ROOT / "documentation" / "need_action" / "enrich_minimal_report.md"
INSTANCES_DIR = VAULT_ROOT / "instances"
QUEUE_PATH = VAULT_ROOT / "entites_custom" / "queue.yaml"

SCENARIOS = [
    "breakdown",
    "fortress_world",
    "new_sustainability",
    "eco_communalism",
    "policy_reform",
    "reference",
]



SCENARIO_DESCRIPTIONS = {
    "breakdown": "effondrement des institutions, fragmentation géopolitique, survie locale",
    "fortress_world": "forteresses climatiques, murs entre zones riches et pauvres, surveillance totale",
    "new_sustainability": "transition écologique réussie, gouvernance mondiale coopérative",
    "eco_communalism": "retour au local, communautés autonomes, décroissance assumée",
    "policy_reform": "réformes institutionnelles progressives, démocratie renforcée",
    "reference": "continuité tendancielle, tensions non résolues, monde fragmenté",
}


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def slug_to_name(slug, scenario):
    """Convertit un slug en nom propre lisible."""
    if scenario and slug.endswith(f"_{scenario}"):
        base = slug[:-(len(scenario) + 1)]
    else:
        base = slug
    return base.replace("_", " ").strip().title()


def infer_category(slug):
    """Infère grossièrement la catégorie depuis le slug."""
    s = slug.lower()
    if any(w in s for w in ["collectif", "communaute", "mouvement", "faction", "ligue", "front", "reseau", "coalition"]):
        return "organisation"
    if any(w in s for w in ["autorite", "agence", "conseil", "parlement", "bureau", "commission", "comite", "institution"]):
        return "institution"
    if any(w in s for w in ["zone", "district", "enclave", "delta", "vallee", "massif", "corridor", "arctique", "sahel", "rust_belt"]):
        return "territoire"
    if any(w in s for w in ["compagnie", "consortium", "corp", "industries", "holdings"]):
        return "corporation"
    return "organisation"


def deduce_scenario(slug, fallback=None):
    """Déduit le scénario depuis le suffixe du slug, ou retourne le fallback."""
    for sc in SCENARIOS:
        if slug.endswith(f"_{sc}"):
            return sc
    return fallback


def merge_phantoms(a, b):
    """Fusionne deux dicts de phantoms, cumulant les mentions."""
    result = dict(a)
    for key, info in b.items():
        if key in result:
            result[key]["mentions"] += info["mentions"]
        else:
            result[key] = dict(info)
    return result


def load_real_slugs():
    """Charge les slugs réels depuis instances/*.md (nom de fichier)."""
    slugs = set()
    if not INSTANCES_DIR.exists():
        return slugs
    for path in INSTANCES_DIR.glob("*.md"):
        slugs.add(path.stem)
    return slugs


# ---------------------------------------------------------------------------
# Source 1 : enrich_minimal_report.md
# ---------------------------------------------------------------------------

def extract_from_enrich_report(report_path):
    """
    Extrait les slugs fantômes depuis enrich_minimal_report.md.
    Format attendu :
      ### fiche_slug (scenario)
      - ⚠️ alliances: 'slug' non trouvé dans _entities_list.json
    Retourne un dict entry_key -> info.
    """
    if not report_path.exists():
        print(f"  [WARN] Rapport non trouvé : {report_path}")
        return {}

    text = report_path.read_text(encoding="utf-8")
    section_pattern = r'### ([^\n]+) \(([^\)]+)\)\n(.*?)(?=\n### |\Z)'
    sections = re.findall(section_pattern, text, re.DOTALL)
    phantom_pattern = r"⚠️ (alliances|oppositions): '([^']+)' non trouvé"

    raw = {}
    for _fiche_slug, parent_scenario, body in sections:
        for rel_type, slug in re.findall(phantom_pattern, body):
            scenario = deduce_scenario(slug, fallback=parent_scenario)
            key = f"{slug}|{scenario}"
            if key not in raw:
                raw[key] = {
                    "slug": slug,
                    "scenario": scenario,
                    "mentions": 1,
                    "source": "enrich",
                }
            else:
                raw[key]["mentions"] += 1

    print(f"  [enrich]   {len(raw)} slugs fantômes détectés")
    return raw


# ---------------------------------------------------------------------------
# Source 2 : validate.py --verbose
# ---------------------------------------------------------------------------

def extract_from_validate(generator_dir):
    """
    Lance validate.py --verbose et extrait les slugs fantômes.
    Format attendu :
      [INSTANCES] fiche.md — référence alliances 'slug' ressemble à un slug
                             mais ne correspond à aucune instance existante
    Retourne un dict entry_key -> info.
    """
    validate_path = generator_dir / "validate.py"
    if not validate_path.exists():
        print(f"  [WARN] validate.py non trouvé : {validate_path}")
        return {}

    print(f"  → Lancement validate.py --verbose...")
    try:
        result = subprocess.run(
            [sys.executable, str(validate_path), "--verbose"],
            capture_output=True,
            text=True,
            cwd=str(generator_dir),
        )
        output = result.stdout + result.stderr
    except Exception as e:
        print(f"  [WARN] validate.py échoué : {e}")
        return {}

    # Pattern : "référence alliances 'slug' ressemble à un slug mais ne correspond"
    # sur une ligne qui contient aussi le nom de la fiche source
    # Exemple : [INSTANCES] ma_fiche_breakdown.md — référence alliances 'slug_fantome' ressemble...
    line_pattern = re.compile(
        r"(\S+\.md)\s+—\s+référence\s+(alliances|oppositions)\s+'([^']+)'\s+ressemble"
    )

    raw = {}
    for line in output.splitlines():
        m = line_pattern.search(line)
        if not m:
            continue
        fiche_file, rel_type, slug = m.group(1), m.group(2), m.group(3)
        # Déduire le scénario depuis le nom de la fiche source
        parent_scenario = deduce_scenario(fiche_file.replace(".md", ""))
        scenario = deduce_scenario(slug, fallback=parent_scenario)
        key = f"{slug}|{scenario}"
        if key not in raw:
            raw[key] = {
                "slug": slug,
                "scenario": scenario,
                "mentions": 1,
                "source": "validate",
            }
        else:
            raw[key]["mentions"] += 1

    print(f"  [validate] {len(raw)} slugs fantômes détectés")
    return raw


# ---------------------------------------------------------------------------
# Construction des entrées queue
# ---------------------------------------------------------------------------

def build_queue_entries(phantoms, real_slugs):
    """
    Construit les entrées queue.yaml pour les slugs fantômes.
    Exclut les slugs qui existent déjà dans les instances réelles.
    """
    entries = []
    already_real = []

    for entry_key, info in sorted(phantoms.items()):
        slug = info["slug"]
        scenario = info["scenario"]
        has_suffix = any(slug.endswith(f"_{sc}") for sc in SCENARIOS)

        if slug in real_slugs:
            already_real.append(slug)
            continue

        slug_corrige = slug if has_suffix else f"{slug}_{scenario}"
        name = slug_to_name(slug, scenario)

        entry = {
            "nom": name,
            "category": infer_category(slug),
            "role": f"(à définir — entité référencée dans les alliances/oppositions du scénario {scenario})",
            "etat": "actif",
            "scenario_ref": scenario,
            "scenario_hint": [scenario],
            "source": f"phantom_{info.get('source', 'unknown')}_{datetime.now().strftime('%Y-%m-%d')}",
            "_slug_fantome_original": slug,
            "_slug_corrige": slug_corrige,
            "_mentions": info["mentions"],
            "_source": info.get("source", "unknown"),
        }
        if not has_suffix:
            entry["_note"] = f"suffixe _{scenario} ajouté automatiquement"

        entries.append(entry)

    return entries, already_real


# ---------------------------------------------------------------------------
# Génération des rôles via API
# ---------------------------------------------------------------------------

def generate_roles(entries, dry_run=False):
    """Appelle le LLM en lots de 5 pour générer un rôle par entrée."""
    if dry_run:
        return entries

    BATCH_SIZE = 5
    batches = [entries[i:i+BATCH_SIZE] for i in range(0, len(entries), BATCH_SIZE)]
    print(f"  → Génération des rôles via API ({len(batches)} lot(s) de {BATCH_SIZE})...")

    for i, batch in enumerate(batches):
        print(f"    Lot {i+1}/{len(batches)}...")
        items = []
        for idx, e in enumerate(batch):
            sc = e.get("scenario_ref", "reference")
            items.append({
                "index": idx,
                "slug": e.get("_slug_corrige", e.get("_slug_fantome_original", "")),
                "nom": e["nom"],
                "scenario": sc,
                "scenario_desc": SCENARIO_DESCRIPTIONS.get(sc, sc),
                "category": e["category"],
            })

        prompt = f"""Tu es l'assistant de worldbuilding du projet Ourrassol 2098 — simulateur de presse fictive en 2098.
Ces entités ont été référencées dans des alliances/oppositions entre acteurs du monde de 2098.
Pour chacune, génère un rôle concis (2-3 phrases) cohérent avec son nom, sa catégorie et son scénario.
Réponds UNIQUEMENT avec un JSON valide : liste d'objets {{"index": N, "role": "...", "etat": "actif|clandestin|transformé"}}.
Pas de texte avant ou après. Pas de backticks.

Entités :
{json.dumps(items, ensure_ascii=False, indent=2)}"""

        try:
            raw = call_llm(
                system_prompt="",
                user_prompt=prompt,
                max_tokens=2000,
                temperature=0.0,
                task_tier="volume",
            ).strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw).strip()
            results, _ = json.JSONDecoder().raw_decode(raw)
            for r in results:
                idx = r.get("index")
                if idx is not None and 0 <= idx < len(batch):
                    batch[idx]["role"] = r.get("role", batch[idx]["role"])
                    if r.get("etat"):
                        batch[idx]["etat"] = r["etat"]
        except Exception as e:
            print(f"    [WARN] Lot {i+1} échoué : {e} — rôles laissés vides")

    return entries


# ---------------------------------------------------------------------------
# Écriture queue
# ---------------------------------------------------------------------------

def write_queue(entries, dry_run=False):
    """Ajoute les entrées à queue.yaml sans écraser les existantes."""
    existing = []
    if QUEUE_PATH.exists():
        try:
            data = yaml.safe_load(QUEUE_PATH.read_text(encoding="utf-8")) or {}
            existing = data.get("queue", []) or []
        except Exception:
            pass

    existing_slugs = {e.get("_slug_corrige", e.get("_slug_fantome_original", "")) for e in existing}
    new_entries = [e for e in entries if e.get("_slug_corrige", e.get("_slug_fantome_original", "")) not in existing_slugs]
    skipped_dup = len(entries) - len(new_entries)
    all_entries = existing + new_entries

    if not dry_run:
        QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        QUEUE_PATH.write_text(
            yaml.dump({"queue": all_entries}, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    return new_entries, skipped_dup


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extrait les slugs fantômes et génère entites_custom/queue.yaml."
    )
    parser.add_argument(
        "--source",
        choices=["enrich", "validate", "all"],
        default="all",
        help="Source des slugs fantômes (défaut: all)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPORT_PATH,
        help=f"Chemin vers enrich_minimal_report.md (défaut: {REPORT_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche le résultat sans écrire dans queue.yaml",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("OURRASSOL 2098 — Extraction slugs fantômes")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)\n")

    # Extraction selon la source
    phantoms = {}
    print("→ Sources :")

    if args.source in ("enrich", "all"):
        p = extract_from_enrich_report(args.report)
        phantoms = merge_phantoms(phantoms, p)

    if args.source in ("validate", "all"):
        p = extract_from_validate(GENERATOR_DIR)
        phantoms = merge_phantoms(phantoms, p)

    print(f"\n  Total combiné : {len(phantoms)} slugs fantômes uniques")

    # Slugs réels
    real_slugs = load_real_slugs()
    print(f"  Instances réelles dans le vault : {len(real_slugs)}")

    # Construction des entrées
    entries, already_real = build_queue_entries(phantoms, real_slugs)

    if already_real:
        print(f"  Slugs déjà réels (ignorés) : {len(already_real)}")

    # Génération des rôles
    if entries:
        print(f"\n→ Génération des rôles ({len(entries)} entrées)...")
        entries = generate_roles(entries, dry_run=args.dry_run)

    # Suffixes corrigés
    suffix_corriges = [e for e in entries if e.get("_note")]

    print(f"\n{'─' * 60}")
    print(f"RÉSULTAT")
    print(f"{'─' * 60}")
    print(f"  Entrées à queuer : {len(entries)}")
    if suffix_corriges:
        print(f"  Suffixes ajoutés : {len(suffix_corriges)}")
        for e in suffix_corriges:
            print(f"    {e['_slug_fantome_original']} → {e['_slug_corrige']}")

    if not entries:
        print("\nAucune entrée à générer.")
        return

    # Aperçu
    print(f"\n{'─' * 60}")
    print(f"APERÇU (5 premières entrées)")
    print(f"{'─' * 60}")
    for e in entries[:5]:
        print(f"  {e['nom']} ({e.get('scenario_ref', '?')}) [{e.get('_source', '?')}] — {e['category']}")
        print(f"    slug : {e['_slug_corrige']}")
        print(f"    mentions : {e['_mentions']}")
        print()

    # Écriture
    new_entries, skipped_dup = write_queue(entries, dry_run=args.dry_run)

    print(f"{'─' * 60}")
    if args.dry_run:
        print(f"(dry-run) {len(new_entries)} entrées seraient ajoutées à queue.yaml")
    else:
        print(f"✓ {len(new_entries)} entrées ajoutées à {QUEUE_PATH}")
        if skipped_dup:
            print(f"  ({skipped_dup} ignorées — déjà présentes dans queue.yaml)")

    print(f"\n{'─' * 60}")
    print("SUITE RECOMMANDÉE")
    print(f"{'─' * 60}")
    print("1. Inspecter la queue :")
    print(f"   {QUEUE_PATH}")
    print("2. Supprimer les entrées non pertinentes")
    print("3. Lancer :")
    print("   python3 create_entities_and_instances.py  (mode custom)")


if __name__ == "__main__":
    main()
