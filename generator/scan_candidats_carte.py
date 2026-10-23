#!/usr/bin/env python3
"""
scan_candidats_carte.py — 23 octobre 2026 (S27.1), lecture seule.

Cherche, dans les six scénarios, les pays dont le passage d'une zone N1 à une
autre exercerait toute la partie « carte » de la phase 4 et de l'étape ⑤ :
  - S : sous-zones de sa zone qui ne portent que ce pays (rattachement automatique) ;
  - M : sous-zones qui portent ce pays ET d'autres (à répartir à l'étape ⑤) ;
  - V : la zone se viderait (le pays est sa seule entrée « pays entier ») ;
  - J : la zone a des journaux (à garder en exil ou retirer, si elle se vide).
Rien n'est écrit.

Usage (depuis la racine du vault) :
    python3 generator/scan_candidats_carte.py [--top 15]
"""

import argparse
import sys
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VAULT / "gui"))
from zone_repository import ZoneRepository, _normalise_pays, _tokens_entite  # noqa: E402

SCENARIOS = ["breakdown", "fortress_world", "new_sustainability", "eco_communalism",
             "policy_reform", "reference"]


def pays_de(entree, connus):
    """Pays connus (normalisés) cités par une entrée origine_reelle."""
    return {_normalise_pays(t) for t in _tokens_entite(entree.get("entite") or "")} & connus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()
    repo = ZoneRepository(VAULT, VAULT / "gui")
    zp = repo._load_zones_pays()
    connus = {_normalise_pays(p) for p in zp.get("pays_liste", [])}
    canon = {_normalise_pays(p): p for p in zp.get("pays_liste", [])}
    try:
        journaux = yaml.safe_load((VAULT / "generator" / "journaux.yaml").read_text(encoding="utf-8")) or {}
    except OSError:
        journaux = {}

    candidats = []
    for sc in SCENARIOS:
        zones = repo.load_all_zones(sc)
        if not zones:
            continue
        overlay = repo._paires_overlay(sc)
        by = {z.get("slug"): z for z in zones}
        zones_journal = set()
        for ligne in (journaux.get(sc) or {}).values():
            if isinstance(ligne, dict):
                zones_journal |= set((ligne.get("zones") or {}).keys())
        for z in zones:
            if int(z.get("niveau") or 1) != 1:
                continue
            slug = z.get("slug")
            entier = [o for o in z.get("origine_reelle") or [] if isinstance(o, dict)
                      and pays_de(o, connus) and (slug, _normalise_pays(o.get("entite") or "")) not in overlay]
            desc = [by[s] for s in repo._zone_descendants(zones, slug) if s != slug and s in by]
            for o in entier:
                for p in pays_de(o, connus):
                    seul, multi = [], []
                    for d in desc:
                        cites = set().union(*[pays_de(x, connus) for x in d.get("origine_reelle") or []
                                              if isinstance(x, dict)] or [set()])
                        if p in cites:
                            (seul if cites == {p} else multi).append(d.get("nom") or d.get("slug"))
                    vide = len(entier) == 1
                    journal = slug in zones_journal
                    score = (bool(seul) + bool(multi) + vide + (journal and vide))
                    candidats.append((score, len(multi) + len(seul), sc, canon.get(p, p), z.get("nom") or slug,
                                      slug, seul, multi, vide, journal))

    candidats.sort(key=lambda c: (-c[0], -c[1], c[2], c[3]))
    print(f"{len(candidats)} couple(s) pays / zone examinés. Meilleurs candidats (S, M, V, J) :\n")
    for score, _, sc, pays, nom, slug, seul, multi, vide, journal in candidats[:a.top]:
        drap = "".join(x if ok else "·" for x, ok in (("S", seul), ("M", multi), ("V", vide), ("J", journal)))
        print(f"[{drap}] {sc:18s} {pays} — zone « {nom} » ({slug})")
        if seul:
            print(f"        S : {', '.join(seul)}")
        if multi:
            print(f"        M : {', '.join(multi)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
