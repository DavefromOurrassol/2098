"""
audit_lieu_zone.py -- S23, 3 octobre 2026. Lecture seule.

Pour chaque article généré après une date donnée (défaut : 2026-08-25,
après les correctifs de zone/signature), affiche zone_principale (slug +
nom lisible depuis geographie/{scenario}.md) et le début du premier
vrai paragraphe (après titre, date, signature), pour comparer à l'œil
le lieu de l'article à sa zone.

Usage (depuis generator/) : python3 audit_lieu_zone.py [--depuis 2026-08-25]
"""
import argparse
import functools
import glob
import re

import yaml

import prompt_builder as pb

pb._load_geographie = functools.lru_cache(None)(pb._load_geographie)


def nom_zone(sc, slug):
    if not slug:
        return "(aucune)"
    for z in pb._load_geographie(sc):
        if z.get("slug") == slug:
            return z.get("nom", slug)
    return "?? inconnue dans geographie/{}.md".format(sc)


def premier_paragraphe(corps):
    for l in corps.split("\n"):
        s = l.strip().strip("*_").strip()
        if len(s) < 80:      # titre, date, signature, intertitres
            continue
        if s.startswith("#") or s.startswith("==="):
            continue
        return s[:160]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depuis", default="2026-08-25")
    args = ap.parse_args()
    lignes = []
    for f in glob.glob("../articles/*/*.md"):
        if f.endswith("_index.md"):
            continue
        t = open(f, encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        d = str(fm.get("date_generation", ""))[:10]
        if d <= args.depuis:
            continue
        sc = f.split("/")[2]
        z = fm.get("zone_principale") or ""
        lignes.append((d, sc, z, nom_zone(sc, z), premier_paragraphe(t[m.end():])))
    for d, sc, z, nz, p in sorted(lignes):
        print("{} {} | {} ({})\n    {}".format(d, sc, nz, z, p))


if __name__ == "__main__":
    main()
