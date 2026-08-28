#!/usr/bin/env python3
"""
set_garantie_selection.py — Ourrassol 2098

Active ou désactive injection.garantie_selection sur une fiche
instance existante en injection.type: custom -- patch chirurgical du
frontmatter, aucun appel LLM, ne touche à rien d'autre (contexte_
injection, impact_sur_variables, propagation.via_matrice restent
intacts).

Conçu le 23 août 2026 : injection.type: custom déclenche deux effets
distincts, jusqu'ici indissociables --
  1. Garantie d'inclusion dans filtered_instances
     (_select_with_custom_guarantee, loader.py)
  2. Propagation d'impact sur les variables systémiques
     (apply_custom_injections, snapshot.py -- ne regarde QUE
     injection.type == "custom", jamais ce nouveau flag)
Ce script permet de retirer SEULEMENT le premier effet, en laissant le
second intact. Cas d'usage réel : gelecek_meclisi, injectée en 2047 sur
4 scénarios, devenue quasi-omniprésente (jusqu'à 98% des articles
new_sustainability, diagnostiqué le 23 août 2026) -- la garantie de
présence n'avait plus de raison d'être des décennies plus tard dans la
fiction, mais son effet causal sur la simulation du monde devait être
préservé.

injection.garantie_selection absent = true par défaut (AUCUNE
régression sur les instances custom existantes qui n'ont jamais ce
champ) -- voir loader.py, _est_garanti()/is_custom.

USAGE CLI :
    python3 set_garantie_selection.py --slug gelecek_meclisi_new_sustainability --value false
    python3 set_garantie_selection.py --slug gelecek_meclisi_new_sustainability --value true
"""

import argparse
import re
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
INSTANCES_DIR = VAULT_ROOT / "instances"

_FRONTMATTER_RE = re.compile(r"^(---\n)(.*?\n)(---\n)", re.DOTALL)
_TYPE_CUSTOM_RE = re.compile(r"^  type: custom\n", re.MULTILINE)
_GARANTIE_LINE_RE = re.compile(r"^  garantie_selection:.*\n", re.MULTILINE)


def set_garantie_selection(slug, value, instances_dir=None):
    """
    Active (value=False -- retire la garantie) ou désactive
    (value=True -- restaure le défaut) injection.garantie_selection sur
    la fiche instance `slug`. Refuse si injection.type n'est pas
    "custom" (le flag n'a de sens que dans ce cas).

    Retourne (bool succès, str message).
    """
    if instances_dir is None:
        instances_dir = INSTANCES_DIR

    filepath = Path(instances_dir) / f"{slug}.md"
    if not filepath.exists():
        return False, f"fiche introuvable : {filepath}"

    text = filepath.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return False, f"frontmatter introuvable ou mal formé : {filepath}"

    fm_open, fm_body, fm_close = match.groups()
    rest = text[match.end():]

    if not _TYPE_CUSTOM_RE.search(fm_body):
        return False, (
            f"injection.type n'est pas 'custom' sur {slug} -- "
            f"garantie_selection n'a de sens que sur une instance custom."
        )

    if value is False:
        # value=False = retirer la garantie -> écrire garantie_selection: false
        if _GARANTIE_LINE_RE.search(fm_body):
            fm_body = _GARANTIE_LINE_RE.sub("  garantie_selection: false\n", fm_body)
        else:
            fm_body = _TYPE_CUSTOM_RE.sub(
                "  type: custom\n  garantie_selection: false\n", fm_body, count=1
            )
        msg = f"garantie_selection: false — {slug} (propagation d'impact conservée)"
    else:
        # value=True = restaurer le défaut -> retirer la ligne
        if not _GARANTIE_LINE_RE.search(fm_body):
            return True, f"garantie_selection déjà absent (= true par défaut) — {slug}"
        fm_body = _GARANTIE_LINE_RE.sub("", fm_body)
        msg = f"garantie_selection retiré (= true par défaut) — {slug}"

    new_text = fm_open + fm_body + fm_close + rest
    filepath.write_text(new_text, encoding="utf-8")
    return True, msg


def main():
    parser = argparse.ArgumentParser(
        description="Active/désactive injection.garantie_selection sur une instance custom."
    )
    parser.add_argument("--slug", required=True,
                         help="Slug de l'instance (déjà scénario-suffixé)")
    parser.add_argument("--value", required=True, choices=["true", "false"],
                         help="false = retirer la garantie de présence (garde la "
                              "propagation d'impact), true = restaurer le défaut")
    args = parser.parse_args()

    ok, msg = set_garantie_selection(args.slug, args.value == "true")
    if ok:
        print(f"  ✓ {msg}")
        sys.exit(0)
    else:
        print(f"  ✗ {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
