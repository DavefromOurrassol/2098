#!/usr/bin/env python3
"""
et_si_statut.py — Ourrassol 2098 (S27, refonte du panneau, 17 octobre 2026)
==========================================================================

État du parcours d'une hypothèse « et si ? » pour le panneau du GUI :
statut (et_si_dossiers.py), simulation, décision, fichier des opérations de la
phase 4, journal d'application, check-list, et l'étape en cours :
    1 tester · 2 décider · 3 injecter · 4 appliquer · 5 à la main
Lecture seule, aucun appel IA.

USAGE
    python3 generator/et_si_statut.py --id <hypothèse> [--json]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
VAULT = GEN.parent
sys.path.insert(0, str(GEN))
import et_si_dossiers as ed  # noqa: E402

APP_DIR = GEN / "state" / "et_si_application"
NEED_ACTION = VAULT / "documentation" / "need_action"


def hypothese_modifiee(hid):
    """Même contrôle que simuler_et_si.py --dossiers (empreinte du bloc tel qu'écrit)."""
    try:
        r = subprocess.run([sys.executable, str(GEN / "simuler_et_si.py"), "--dossiers"], cwd=GEN,
                           capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    bloc, dedans = [], False
    for ligne in r.stdout.splitlines():
        if ligne.startswith("- "):
            dedans = ligne.startswith(f"- {hid} :")
        elif dedans:
            bloc.append(ligne)
    return any("hypothèse modifiée" in l for l in bloc)


def etat(hid):
    d = ed.charger().get(hid) or {}
    sim, dec = d.get("simulation") or {}, d.get("decision") or {}
    st = ed.statut(hid, d)
    ops = APP_DIR / f"{hid}.json"
    journal = APP_DIR / f"{hid}.applique.json"
    checklist = NEED_ACTION / f"et_si_{hid}_reste_a_faire.md"
    alertes = []

    applique = None
    if journal.exists():
        try:
            applique = json.loads(journal.read_text(encoding="utf-8")).get("date")
        except (OSError, ValueError):
            applique = "?"

    modifiee = hypothese_modifiee(hid) if sim else False
    applique = None
    if journal.exists():
        try:
            applique = json.loads(journal.read_text(encoding="utf-8")).get("date")
        except (OSError, ValueError):
            applique = "?"

    # Étape en cours. Avant l'adoption, une simulation périmée ou partielle renvoie à ① ;
    # après, seule l'alerte reste (la décision doit rester visible pour pouvoir l'annuler).
    if not sim:
        etape = 1
    elif st in ("simulé", "rejeté"):
        etape = 1 if (modifiee or not sim.get("complet")) else 2
    elif st == "adopté, en attente d'injection":
        etape = 3
    elif st == "injecté":
        etape = 5 if applique else 4
    else:
        etape = 3   # injecté partiellement, à revoir, absent de la queue : traiter l'injection
        alertes.append(f"statut « {st} » : voir evenements_custom/needs_review.yaml, ou annuler la décision")

    if sim:
        if modifiee:
            alertes.append("hypothèse modifiée depuis la simulation : la resimuler"
                           + (" (puis annuler la décision et adopter de nouveau)" if etape > 2 else ""))
        if not sim.get("complet") and etape <= 2:
            alertes.append("simulation limitée à " + ", ".join(sim.get("scenarios") or []) +
                           " : relancer sans « Scénario »")
        if not sim.get("passe") and etape <= 2:
            alertes.append("simulation sans passe exhaustive : cocher « Lecture IA » et « Passe exhaustive »")
        if not ops.exists() and etape <= 4 and not applique:
            alertes.append("pas de fichier d'opérations (simulation antérieure à v8.19) : la phase 4 "
                           "demandera une nouvelle simulation")

    rapport = sim.get("rapport")
    if not rapport and (NEED_ACTION / f"et_si_{hid}.md").exists():
        rapport = f"documentation/need_action/et_si_{hid}.md"
    return {
        "id": hid, "statut": st, "etape": etape, "alertes": alertes,
        "simulation": {"date": sim.get("date"), "version": sim.get("version"),
                       "complet": sim.get("complet"), "passe": sim.get("passe"),
                       "rapport": rapport} if sim else None,
        "decision": {"statut": dec.get("statut"), "date": dec.get("date"), "motif": dec.get("motif"),
                     "portee": (dec.get("entree") or {}).get("portee"),
                     "intensite": (dec.get("entree") or {}).get("intensite")} if dec else None,
        "operations": ops.exists(),
        "applique": applique,
        "checklist": f"documentation/need_action/{checklist.name}" if checklist.exists() else None,
    }


def main():
    ap = argparse.ArgumentParser(description="État du parcours d'une hypothèse (lecture seule).")
    ap.add_argument("--id", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    e = etat(a.id.strip())
    if a.json:
        print(json.dumps(e, ensure_ascii=False))
        return
    print(f"{e['id']} : {e['statut']} — étape {e['etape']}")
    for x in e["alertes"]:
        print(f"  ⚠ {x}")


if __name__ == "__main__":
    main()
