#!/usr/bin/env python3
"""
extraire_echelles.py — Ourrassol 2098
--------------------------------------
Diagnostic en LECTURE SEULE (aucune écriture dans le vault, aucun appel LLM).

Pour chacune des 12 fiches variables/*.md, affiche le `level` et le début du
`state_logic` dans chacun des 6 scénarios, triés du level le plus bas au plus
haut. Sert à définir ce que signifient 0 et 100 pour chaque variable
(convention "intensité", décidée le 27 septembre 2026).

Usage (depuis la racine du vault) :
  python3 generator/extraire_echelles.py > echelles.txt
"""

import re
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
VARIABLES_DIR = VAULT_ROOT / "variables"
NB_MOTS = 25


def lire_frontmatter(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if not m:
        return {}
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    return yaml.safe_load(fm_str) or {}


def main():
    fiches = sorted(p for p in VARIABLES_DIR.glob("*.md")
                    if not p.name.startswith(("_", ".")) and "template" not in p.name.lower())
    for path in fiches:
        try:
            fm = lire_frontmatter(path)
        except yaml.YAMLError as e:
            print(f"\n### {path.stem} : YAML illisible ({e.__class__.__name__})")
            continue
        if fm.get("type") != "systemic_variable":
            continue
        states = fm.get("states") or {}
        lignes = []
        for scen, st in states.items():
            st = st or {}
            logic = re.sub(r"\s+", " ", str(st.get("state_logic", ""))).strip()
            mots = logic.split()
            extrait = " ".join(mots[:NB_MOTS]) + (" …" if len(mots) > NB_MOTS else "")
            lignes.append((st.get("level", "?"), scen, extrait))
        lignes.sort(key=lambda x: (x[0] if isinstance(x[0], (int, float)) else 999))

        print(f"\n### {path.stem}")
        for level, scen, extrait in lignes:
            print(f"  [{level:>3}] {scen:<19} {extrait}")


if __name__ == "__main__":
    main()
