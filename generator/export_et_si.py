#!/usr/bin/env python3
"""
export_et_si.py — Ourrassol 2098 (S27, 11 octobre 2026)

Exporte, en lecture seule, tout ce qu'il faut pour rejouer la passe exhaustive
hors de ta machine (sans appel IA) : pour chaque couple hypothèse / scénario,
l'hypothèse vérifiée, les effets simulés, la lecture IA du simulateur (cache),
les instances, les événements, le scénario et les zones ; plus le cache de la
passe (state/et_si_exhaustif.json).

Usage (depuis la racine du vault) :
    python3 generator/export_et_si.py            # tous les couples déjà passés (présents dans le cache)
    python3 generator/export_et_si.py --couple peste_pulmonaire_2043:breakdown

Écrit generator/state/export_et_si.json. Rien d'autre n'est modifié.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))



def couples_en_cache(cache):
    """Couples hypothèse:scénario dont au moins un lot de la passe est en cache."""
    vus = []
    for cle in cache:
        morceaux = cle.split("::")
        if len(morceaux) >= 3 and morceaux[2][:1].isdigit():
            c = f"{morceaux[0]}:{morceaux[1]}"
            if c not in vus:
                vus.append(c)
    return vus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--couple", action="append", help="hypothese:scenario (répétable)")
    ap.add_argument("--date", type=float, default=2098.0)
    args = ap.parse_args()

    import simuler_et_si as s
    import et_si_exhaustif as es
    import dynamique as dyn
    from loader import (VALID_VARS, load_instances_for_scenario,
                        load_event_instances_for_scenario, load_scenario)

    sortie = {"couples": [], "cache": es._lire_cache()}
    hyps = {h.get("id"): h for h in s.charger_hypotheses()}
    couples = args.couple or couples_en_cache(sortie["cache"])
    print(f"{len(couples)} couple(s) : {', '.join(couples)}", file=sys.stderr)
    for couple in couples:
        hid, sc = couple.split(":")
        if hid not in hyps:
            print(f"✗ hypothèse {hid} introuvable, ignorée", file=sys.stderr)
            continue
        hyp, erreurs, _ = s.verifier_hypothese(hyps[hid], VALID_VARS, dyn)
        if erreurs:
            print(f"✗ {hid} invalide : {erreurs}", file=sys.stderr)
            continue
        effets = (s.simuler_hypothese(hyp, args.date, [sc]).get(sc) or {}).get("effets") or []
        try:
            repo, _ = s.charger_zone_repository()
            zones = repo.load_all_zones(sc)
        except Exception as e:
            print(f"  (zones indisponibles pour {sc} : {e})", file=sys.stderr)
            zones = []
        sortie["couples"].append({
            "hyp": hyp, "scenario": sc, "effets": effets,
            "lecture": es.lecture_en_cache(hyp, sc, effets),
            "instances": load_instances_for_scenario(sc),
            "evenements": load_event_instances_for_scenario(sc),
            "scenario_data": load_scenario(sc),
            "zones": zones,
        })
        print(f"✓ {hid} / {sc}", file=sys.stderr)

    cible = SCRIPT_DIR / "state" / "export_et_si.json"
    cible.write_text(json.dumps(sortie, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"✓ écrit : {cible} ({cible.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
