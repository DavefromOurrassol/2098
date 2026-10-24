#!/usr/bin/env python3
"""Scan en lecture seule des doublons probables d'instances, par scénario.

Usage (depuis la racine du vault) :
    python3 generator/scan_doublons_lore.py [--seuil 0.85] [--scenario X] [--md FICHIER]

Ne modifie rien. Relève :
  A. paires de noms identiques ou proches dans un même scénario ;
  B. fiches alliées / opposées à elles-mêmes ;
  C. même cible à la fois en alliances et en oppositions.
"""
import argparse
import difflib
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent
INSTANCES = VAULT / "instances"
SLUG_RE = re.compile(r"[a-z0-9_]+")
MOTS_VIDES = {"le", "la", "les", "de", "du", "des", "d", "l", "et", "en", "a",
              "au", "aux", "the", "of"}


def frontmatter(path):
    txt = path.read_text(encoding="utf-8", errors="replace")
    if not txt.startswith("---"):
        return None
    fin = txt.find("\n---", 3)
    if fin < 0:
        return None
    try:
        data = yaml.safe_load(txt[3:fin])
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def norm(nom):
    s = unicodedata.normalize("NFKD", str(nom)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return " ".join(m for m in s.split() if m not in MOTS_VIDES)


def base(nom):
    return norm(re.split(r"\s+[—–-]\s+|\s*\(", str(nom))[0])


def slugs_de(valeur):
    """Extrait les slugs d'une liste d'alliances/oppositions, quel que soit le format."""
    out = set()
    if not valeur:
        return out
    items = valeur if isinstance(valeur, list) else [valeur]
    for it in items:
        if isinstance(it, dict):
            it = it.get("slug") or it.get("instance") or it.get("cible") or next(iter(it.values()), "")
        s = str(it).strip().strip("[]").split("|")[0].strip()
        if SLUG_RE.fullmatch(s):
            out.add(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seuil", type=float, default=0.85)
    ap.add_argument("--scenario")
    ap.add_argument("--md", help="écrire aussi le rapport dans ce fichier")
    a = ap.parse_args()

    fiches = []
    illisibles = 0
    for p in sorted(INSTANCES.glob("*.md")):
        if p.name.startswith("_"):
            continue
        fm = frontmatter(p)
        if not fm:
            illisibles += 1
            continue
        sc = fm.get("scenario")
        if a.scenario and sc != a.scenario:
            continue
        loc = fm.get("localisation") or {}
        fiches.append({
            "slug": fm.get("slug") or p.stem,
            "name": fm.get("name") or "",
            "scenario": sc,
            "type": fm.get("type_dans_scenario") or "",
            "zone": (loc.get("zone") if isinstance(loc, dict) else "") or "",
            "all": slugs_de(fm.get("alliances")),
            "opp": slugs_de(fm.get("oppositions")),
        })

    lignes = []
    out = lignes.append
    par_sc = defaultdict(list)
    for f in fiches:
        par_sc[f["scenario"]].append(f)

    total_a = 0
    out("## A. Noms identiques ou proches (même scénario)\n")
    for sc in sorted(par_sc, key=str):
        lst = par_sc[sc]
        paires = []
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                x, y = lst[i], lst[j]
                bx, by = base(x["name"]), base(y["name"])
                if not bx or not by:
                    continue
                ratio = difflib.SequenceMatcher(None, bx, by).ratio()
                if bx == by or ratio >= a.seuil:
                    meme_zone = x["zone"] and x["zone"] == y["zone"]
                    paires.append((bx == by, ratio, meme_zone, x, y))
        if not paires:
            continue
        paires.sort(key=lambda t: (not t[0], not t[2], -t[1]))
        out(f"### {sc} — {len(paires)} paire(s)")
        for ident, ratio, mz, x, y in paires:
            tag = "IDENTIQUE" if ident else f"{ratio:.2f}"
            z = "même zone" if mz else f"zones {x['zone'] or '—'} / {y['zone'] or '—'}"
            out(f"- [{tag}] {x['slug']}  ↔  {y['slug']}  ({z} ; {x['type']} / {y['type']})")
            out(f"    « {x['name']} » / « {y['name']} »")
        out("")
        total_a += len(paires)

    out("## B. Auto-références\n")
    total_b = 0
    for f in fiches:
        for champ in ("all", "opp"):
            if f["slug"] in f[champ]:
                out(f"- {f['slug']} : se cite dans {'alliances' if champ == 'all' else 'oppositions'}")
                total_b += 1
    out("")

    out("## C. Même cible en alliances ET oppositions\n")
    total_c = 0
    for f in fiches:
        for cible in sorted(f["all"] & f["opp"]):
            out(f"- {f['slug']} → {cible}")
            total_c += 1
    out("")

    resume = (f"Instances lues : {len(fiches)} (illisibles : {illisibles}) | "
              f"A paires proches : {total_a} | B auto-références : {total_b} | "
              f"C conflits alliance/opposition : {total_c}")
    texte = "\n".join(lignes) + "\n" + resume + "\n"
    print(texte)
    if a.md:
        Path(a.md).write_text(f"# Scan doublons lore\n\n{texte}", encoding="utf-8")
        print(f"Rapport écrit : {a.md}")


if __name__ == "__main__":
    sys.exit(main())
