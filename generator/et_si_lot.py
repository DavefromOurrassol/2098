#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
et_si_lot.py (U3bb) — liste, pour le GUI, les hypothèses d'ENTITÉ avec leur statut,
afin de les adopter puis de les injecter en lot. Lecture seule : n'écrit rien.

  python3 generator/et_si_lot.py --lister --json
Sortie : {"ok": true, "entites": [{"id","nom","categorie","scenario_ref","annee_debut","statut"}]}
(statut : vérifié · rejeté · adopté, en attente d'injection · injecté)
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

GEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))
import et_si_dossiers as ed  # noqa: E402


def lister():
    try:
        data = yaml.safe_load(ed.HYPOTHESES_PATH.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        return {"ok": False, "error": f"hypotheses.yaml illisible : {e}"}
    dossiers = ed.charger()
    sortie = []
    for h in data.get("hypotheses") or []:
        if not isinstance(h, dict) or str(h.get("type") or "").strip().lower() != "entite":
            continue
        hid = str(h.get("id"))
        sortie.append({"id": hid, "nom": " ".join(str(h.get("nom") or hid).split()),
                       "categorie": h.get("categorie"), "scenario_ref": h.get("scenario_ref"),
                       "annee_debut": h.get("annee_debut"),
                       "statut": ed.statut(hid, dossiers.get(hid) or {})})
    return {"ok": True, "entites": sortie}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--lister", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = lister() if a.lister else {"ok": False, "error": "action attendue : --lister"}
    if a.json:
        print(json.dumps(res, ensure_ascii=False, default=str))
    elif res.get("ok"):
        for e in res["entites"]:
            print(f"{e['id']:45s} {e['statut']:34s} {e.get('annee_debut') or '-'}  {e['nom']}")
    else:
        print("✗", res.get("error"))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
