#!/usr/bin/env python3
"""Lecture seule : quelles zones d'un scénario déclarent tels pays dans origine_reelle,
et à quelle zone zones_pays.json les rattache.

Usage (depuis la racine du vault) :
    python3 generator/zones_par_pays.py breakdown Uruguay Argentine Brésil
"""
import json
import sys
import unicodedata
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent


def norm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sc, pays = sys.argv[1], sys.argv[2:]
    cibles = [norm(p) for p in pays]

    t = (VAULT / "geographie" / f"{sc}.md").read_text(encoding="utf-8")
    fm = yaml.safe_load(t.split("\n---", 1)[0].lstrip("-\n"))
    zones = fm.get("zones", fm) if isinstance(fm, dict) else fm
    par_slug = {z["slug"]: z for z in zones}

    def chemin(z):
        out, cur = [], z
        while cur and cur.get("parent"):
            out.append(cur["parent"])
            cur = par_slug.get(cur["parent"])
        return " ← ".join(out) or "—"

    print(f"=== geographie/{sc}.md")
    for z in zones:
        for o in z.get("origine_reelle") or []:
            e = norm(o.get("entite", ""))
            if any(c in e for c in cibles):
                print(f"N{z.get('niveau')}  {z['slug']:42} {o.get('entite')!s:35} "
                      f"portion={o.get('portion')!s:.40}  parents: {chemin(z)}")

    zp = VAULT / "zones_pays.json"
    if not zp.exists():
        zp = next(VAULT.rglob("zones_pays.json"), None)
    if zp:
        data = json.loads(zp.read_text(encoding="utf-8"))
        print(f"\n=== {zp.relative_to(VAULT)}")
        bloc = data.get(sc, data) if isinstance(data, dict) else {}
        for p in pays:
            trouve = [k for k in bloc if norm(k) == norm(p)] if isinstance(bloc, dict) else []
            for k in trouve:
                print(f"  {k:20} → {bloc[k]}")
            if not trouve:
                print(f"  {p:20} → (absent)")


if __name__ == "__main__":
    main()
