#!/usr/bin/env python3
"""
fix_alliance_suffixes.py — Ourrassol 2098
==========================================

Corrige les slugs sans suffixe scénario dans les champs alliances/oppositions
des fiches instances.

Exemple :
  alliances: [rust_belt_communes_libres]        (incorrect)
  alliances: [rust_belt_communes_libres_fortress_world]  (corrigé)

Le suffixe est déduit du champ `scenario` de la fiche elle-même.
Aucun appel API — correction purement mécanique.

USAGE
-----
    python3 fix_alliance_suffixes.py --dry-run        # affiche sans écrire
    python3 fix_alliance_suffixes.py                  # corrige les fiches
    python3 fix_alliance_suffixes.py --scenario fortress_world
    python3 fix_alliance_suffixes.py --verbose        # détail de chaque correction
"""

import argparse
import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_DIR = VAULT_ROOT / "instances"

SCENARIOS = [
    "breakdown",
    "fortress_world",
    "new_sustainability",
    "eco_communalism",
    "policy_reform",
    "reference",
]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_md(filepath):
    """Parse un fichier .md : retourne (frontmatter_dict, body_str, raw_str)."""
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not m:
        return {}, raw, raw
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2).strip(), raw


# ---------------------------------------------------------------------------
# Correction
# ---------------------------------------------------------------------------

def fix_slug(slug, scenario):
    """
    Si le slug n'a pas de suffixe scénario valide, ajoute _{scenario}.
    Retourne (slug_corrigé, was_fixed).
    """
    slug = str(slug).strip()
    # Nettoyer les wikilinks éventuels
    slug = re.sub(r"\[\[([^\]]+)\]\]", r"\1", slug)

    # Déjà un suffixe valide ?
    for sc in SCENARIOS:
        if slug.endswith(f"_{sc}"):
            return slug, False

    # Ajouter le suffixe
    return f"{slug}_{scenario}", True


def fix_fiche(path, dry_run=False, verbose=False):
    """
    Corrige les slugs sans suffixe dans alliances/oppositions d'une fiche.
    Retourne (n_fixes, details).
    """
    fm, body, raw = parse_md(path)
    scenario = fm.get("scenario", "")

    if not scenario or scenario not in SCENARIOS:
        return 0, []

    corrections = []
    modified = False

    for field in ["alliances", "oppositions"]:
        refs = fm.get(field, []) or []
        if not isinstance(refs, list):
            continue

        new_refs = []
        for ref in refs:
            fixed, was_fixed = fix_slug(str(ref), scenario)
            new_refs.append(fixed)
            if was_fixed:
                corrections.append((field, str(ref).strip(), fixed))
                modified = True

        if modified:
            fm[field] = new_refs

    if not modified:
        return 0, []

    if verbose:
        for field, old, new in corrections:
            print(f"      {field}: '{old}' → '{new}'")

    if not dry_run:
        # Réécrire le frontmatter
        fm_str = yaml.dump(
            fm,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        content = f"---\n{fm_str}---\n\n{body}\n"
        path.write_text(content, encoding="utf-8")

    return len(corrections), corrections


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Corrige les slugs sans suffixe scénario dans alliances/oppositions."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche les corrections sans écrire")
    parser.add_argument("--scenario",
                        help="Limite à un scénario (ex: fortress_world)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Détail de chaque correction")
    args = parser.parse_args()

    print("=" * 60)
    print("OURRASSOL 2098 — Fix suffixes alliances/oppositions")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)\n")

    pattern = f"*_{args.scenario}.md" if args.scenario else "*.md"
    fiches = sorted(INSTANCES_DIR.glob(pattern))
    print(f"→ {len(fiches)} fiche(s) à analyser\n")

    total_fiches = 0
    total_corrections = 0

    for path in fiches:
        n, details = fix_fiche(path, dry_run=args.dry_run, verbose=False)
        if n > 0:
            total_fiches += 1
            total_corrections += n
            status = "(dry-run)" if args.dry_run else "✓"
            print(f"  {status} {path.name} — {n} correction(s)")
            if args.verbose:
                for field, old, new in details:
                    print(f"      {field}: '{old}' → '{new}'")

    print(f"\n{'─' * 60}")
    print(f"RÉSUMÉ")
    print(f"{'─' * 60}")
    print(f"  Fiches modifiées  : {total_fiches}")
    print(f"  Corrections totales : {total_corrections}")

    if not args.dry_run and total_corrections > 0:
        print(f"\n→ Lancer validate.py pour vérifier :")
        print(f"  python3 validate.py")


if __name__ == "__main__":
    main()
