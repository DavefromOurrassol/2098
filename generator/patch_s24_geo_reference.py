#!/usr/bin/env python3
"""S24 — geographie/reference.md :
  1. scinde l'entrée groupée « Asie Centrale (Kirghizistan, Tadjikistan, Afghanistan) »
     de zones_grises_globales en trois entrées pays ;
  2. retire « Paraguay (Chaco) » de la sous-zone sertao_nordeste_bresilien.

Usage (depuis la racine du vault) :
    python3 generator/patch_s24_geo_reference.py           # aperçu
    python3 generator/patch_s24_geo_reference.py --apply   # écrit (.bak_s24)
"""
import re
import shutil
import sys
from pathlib import Path

import yaml

P = Path(__file__).resolve().parent.parent / "geographie" / "reference.md"

RE_ASIE = re.compile(
    r"^  - entite: Asie Centrale \(Kirghizistan, Tadjikistan, Afghanistan\)\n"
    r"    type_entite: [^\n]*\n"
    r"    portion: [^\n]*\n", re.M)
RE_CHACO = re.compile(
    r"^  - entite: Paraguay \(Chaco\)\n"
    r"    type_entite: [^\n]*\n"
    r"    portion: [^\n]*\n", re.M)
NOUVEAU_ASIE = "".join(
    f"  - entite: {p}\n    type_entite: pays\n    portion: null\n"
    for p in ("Kirghizistan", "Tadjikistan", "Afghanistan"))


def main():
    apply = "--apply" in sys.argv
    t = P.read_text(encoding="utf-8")
    if "Asie Centrale (Kirghizistan" not in t and "Paraguay (Chaco)" not in t:
        sys.exit("Déjà appliqué — rien fait.")
    na, nc = len(RE_ASIE.findall(t)), len(RE_CHACO.findall(t))
    print(f"Asie Centrale groupée : {na} bloc(s) | Paraguay (Chaco) : {nc} bloc(s)")
    if na != 1 or nc != 1:
        sys.exit("Attendu exactement 1 bloc de chaque — rien fait.")
    t2 = RE_CHACO.sub("", RE_ASIE.sub(NOUVEAU_ASIE, t))
    yaml.safe_load(t2.split("\n---", 1)[0].lstrip("-\n"))  # frontmatter toujours lisible
    if not apply:
        print("Aperçu OK — relancer avec --apply pour écrire.")
        return
    shutil.copy(P, str(P) + ".bak_s24")
    P.write_text(t2, encoding="utf-8")
    print("✓ écrit (sauvegarde reference.md.bak_s24)")


if __name__ == "__main__":
    main()
