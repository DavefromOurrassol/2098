#!/usr/bin/env python3
"""
et_si_injecter.py — Ourrassol 2098 (S27, refonte du panneau, 17 octobre 2026)
============================================================================

Injecte UNE hypothèse adoptée, sans traiter le reste de la queue : prend son
entrée dans evenements_custom/queue.yaml (celle écrite par « Adopter » : même
id et source et_si_<id>), la passe à inject_custom_events.py --idea, puis la
retire de la queue (sauvegarde .bak_et_si) — comme le fait le mode custom pour
toute idée traitée. Le résultat est enregistré par inject_custom_events.py dans
processed.yaml / needs_review.yaml, et le cycle post-injection s'enchaîne.

Le bouton « Injecter des événements » (toute la queue) reste disponible ; une
hypothèse ne peut pas être injectée deux fois, puisque son entrée quitte la
queue dès qu'elle est traitée.

--dry-run : appels IA réels, rien n'est écrit, l'entrée reste dans la queue.

USAGE
    python3 generator/et_si_injecter.py --id <hypothèse> [--dry-run]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))
import et_si_dossiers as ed  # noqa: E402

TIMEOUT = 900  # secondes : appels IA par scénario + cycle post-injection


def main():
    ap = argparse.ArgumentParser(description="Injecte une seule hypothèse adoptée.")
    ap.add_argument("--id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    hid = a.id.strip()

    st = ed.statut(hid)
    if st != "adopté, en attente d'injection":
        sys.exit(f"✗ {hid} est « {st} » : seule une hypothèse « adopté, en attente d'injection » "
                 f"peut être injectée ici.")
    entrees = [x for x in ed._liste_yaml(ed.QUEUE_PATH, "queue")
               if x.get("id") == hid and x.get("source") == f"et_si_{hid}"]
    if len(entrees) != 1:
        sys.exit(f"✗ {len(entrees)} entrée(s) adoptée(s) {hid} dans evenements_custom/queue.yaml "
                 f"(attendu : 1). Une entrée écrite à la main s'injecte par « Injecter des événements ».")

    cmd = [sys.executable, str(GEN / "inject_custom_events.py"),
           "--idea", json.dumps(entrees[0], ensure_ascii=False, default=str)]
    if a.dry_run:
        cmd.append("--dry-run")
    print(("SIMULATION (appels IA réels, rien écrit)" if a.dry_run else "INJECTION") + f" — {hid}\n")
    try:
        r = subprocess.run(cmd, cwd=GEN, capture_output=True, text=True, timeout=TIMEOUT,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        sys.exit(f"✗ délai dépassé ({TIMEOUT} s) : vérifier processed.yaml / needs_review.yaml "
                 f"avant de relancer.")
    sortie = (r.stdout + ("\n" + r.stderr if r.stderr.strip() else "")).rstrip()
    lignes = sortie.splitlines()
    alertes = [l for l in lignes if "⚠" in l]
    print("\n".join(lignes[-150:]))
    if alertes:
        print("\nAlertes de l'injection :\n" + "\n".join(f"  {l.strip()}" for l in alertes))

    if a.dry_run:
        print("\n· simulation : l'entrée reste dans la queue.")
        sys.exit(r.returncode)
    if r.returncode != 0:
        sys.exit(f"\n✗ inject_custom_events.py a échoué (code {r.returncode}) : l'entrée reste dans la "
                 f"queue ; vérifier needs_review.yaml avant de relancer.")
    if ed._retirer_de_queue(hid):
        print(f"\n✓ entrée {hid} retirée de evenements_custom/queue.yaml (sauvegarde queue.yaml.bak_et_si)")
    print(f"✓ statut : {ed.statut(hid)}")


if __name__ == "__main__":
    main()
