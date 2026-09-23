"""
Extrait les villes principales de ne_10m_populated_places.geojson (Natural
Earth, ~19 Mo, 7342 villes) vers un petit fichier statique
gui/static/villes_principales.json, servi tel quel par une route Flask --
pas question de faire lire 19 Mo au navigateur à chaque affichage de carte.

Critère de sélection (ajustable via --seuil-population) : capitale
(ADM0CAP=1) OU mégapole/ville mondiale (MEGACITY=1 ou WORLDCITY=1) OU
population >= seuil (1 000 000 par défaut).

Usage, depuis gui/ :
    python3 extraire_villes_principales.py --dry-run
    python3 extraire_villes_principales.py --apply
    python3 extraire_villes_principales.py --apply --seuil-population 500000
"""

import argparse
import json
from pathlib import Path

SOURCE = Path(
    "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/generator/data/ne_10m_populated_places.geojson"
)
DEST = Path(__file__).parent / "static" / "villes_principales.json"


def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    ap.add_argument("--seuil-population", type=int, default=1_000_000)
    ap.add_argument("--source", type=Path, default=SOURCE)
    args = ap.parse_args()

    if not args.source.exists():
        print(f"ERREUR : fichier source introuvable : {args.source}")
        return

    data = json.loads(args.source.read_text(encoding="utf-8"))
    features = data.get("features", [])
    print(f"{len(features)} villes dans le fichier source.")

    retenues = []
    for f in features:
        p = f.get("properties", {})
        pop = p.get("POP_MAX") or 0
        est_capitale = p.get("ADM0CAP") == 1
        est_mega = p.get("MEGACITY") == 1 or p.get("WORLDCITY") == 1
        if not (est_capitale or est_mega or pop >= args.seuil_population):
            continue
        nom = p.get("NAMEASCII") or p.get("NAME")
        if not nom or p.get("LATITUDE") is None or p.get("LONGITUDE") is None:
            continue
        retenues.append({
            "nom": nom,
            "pays": p.get("ADM0NAME"),
            "lat": p.get("LATITUDE"),
            "lon": p.get("LONGITUDE"),
            "population": pop,
            "capitale": est_capitale,
        })

    retenues.sort(key=lambda v: -v["population"])
    print(f"{len(retenues)} villes retenues "
          f"(capitales, mégapoles, ou >= {args.seuil_population:,} habitants).")
    print("Exemples (les 10 plus peuplées) :")
    for v in retenues[:10]:
        print(f"  - {v['nom']} ({v['pays']}) : {v['population']:,}")

    taille = len(json.dumps(retenues, ensure_ascii=False).encode("utf-8"))
    print(f"\nTaille du fichier résultant : ~{taille / 1024:.0f} Ko (contre "
          f"{args.source.stat().st_size / 1024 / 1024:.0f} Mo pour la source)")

    if args.dry_run:
        print("\n[dry-run] Rien n'a été écrit. Relance avec --apply pour créer le fichier.")
        return

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(retenues, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nÉcrit : {DEST}")


if __name__ == "__main__":
    main()
