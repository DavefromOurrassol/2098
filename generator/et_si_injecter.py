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


def _plan(hid):
    """PATCH_S27_SAUTER : (data, ops) de la phase 4 — mêmes numéros qu'à l'étape ④."""
    import appliquer_et_si as ap
    src = ap.APP_DIR / f"{hid}.json"
    if not src.exists():
        sys.exit(f"✗ {src.name} absent : simuler l'hypothèse d'abord.")
    data = json.loads(src.read_text(encoding="utf-8"))
    ops, _ = ap.construire_plan(data)
    return data, ops


def _nombres(s):
    import re
    return {int(x) for x in re.findall(r"\d+", s or "")}


def _ecartees(ops, sauter, inclure):
    """Numéros que l'étape ④ n'appliquera pas : « Sauter », plus les ⚠ non repris par « Inclure »."""
    return {o["n"] for o in ops if o["n"] in sauter
            or (o.get("alerte") and not str(o["alerte"]).startswith("déjà") and o["n"] not in inclure)}


def _retirer_sautees(entree, ops, ecartees):
    """Copie de l'entrée sans les faits imposés ni les acteurs des opérations écartées."""
    import copy
    slugs = {o.get("instance") or o.get("zone") for o in ops
             if o["n"] in ecartees and o["genre"] in ("trajectoire", "disparition", "zone")}
    slugs.discard(None)
    e = copy.deepcopy(entree)
    retires = []
    for sc, faits in (e.get("faits_imposes") or {}).items():
        garde = []
        for f in faits or []:
            if isinstance(f, dict) and f.get("slug") in slugs:
                retires.append(f"fait ({sc}) : {' '.join(str(f.get('fait')).split())[:100]}")
            else:
                garde.append(f)
        e["faits_imposes"][sc] = garde
    acteurs = e.get("acteurs_hint") or []
    retires += [f"acteur : {s}" for s in acteurs if s in slugs]
    e["acteurs_hint"] = [s for s in acteurs if s not in slugs]
    if "acteurs_hint_count" in e:
        e["acteurs_hint_count"] = len(e["acteurs_hint"])
    return e, retires


def main():
    ap = argparse.ArgumentParser(description="Injecte une seule hypothèse adoptée.")
    ap.add_argument("--id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--plan", action="store_true", help="liste numérotée de l'étape ④, sans IA")   # PATCH_S27_SAUTER
    ap.add_argument("--sauter", default="", help="numéros de l'étape ④ à écarter dès l'injection")
    ap.add_argument("--inclure", default="", help="numéros ⚠ de l'étape ④ à garder")
    a = ap.parse_args()
    hid = a.id.strip()
    if a.plan:
        _, ops = _plan(hid)
        print(f"Liste de l'étape ④ — {hid} (mêmes numéros ; « Sauter » ici retire aussi faits et acteurs "
              "de l'injection)\n")
        for o in ops:
            al = (f"  {'·' if str(o['alerte']).startswith('déjà') else '⚠'} {o['alerte']}"
                  if o.get("alerte") else "")
            print(f"  {o['n']:>3}. [{o['sc']}] {o['texte']}{al}")
        return

    st = ed.statut(hid)
    if st != "adopté, en attente d'injection":
        sys.exit(f"✗ {hid} est « {st} » : seule une hypothèse « adopté, en attente d'injection » "
                 f"peut être injectée ici.")
    entrees = [x for x in ed._liste_yaml(ed.QUEUE_PATH, "queue")
               if x.get("id") == hid and x.get("source") == f"et_si_{hid}"]
    if len(entrees) != 1:
        sys.exit(f"✗ {len(entrees)} entrée(s) adoptée(s) {hid} dans evenements_custom/queue.yaml "
                 f"(attendu : 1). Une entrée écrite à la main s'injecte par « Injecter des événements ».")

    entree, sauter, inclure = entrees[0], _nombres(a.sauter), _nombres(a.inclure)   # PATCH_S27_SAUTER
    _, ops = _plan(hid)
    ecartees = _ecartees(ops, sauter, inclure)
    if ecartees:
        entree, retires = _retirer_sautees(entree, ops, ecartees)
        auto = sorted(ecartees - sauter)
        print(f"Écartées à l'étape ④ : {', '.join(map(str, sorted(ecartees)))}"
              + (f" (dont ⚠ par défaut : {', '.join(map(str, auto))} ; « Inclure » pour les garder)" if auto else "")
              + " — "
              + (f"{len(retires)} élément(s) retiré(s) de l'entrée" if retires else "rien à retirer de l'entrée"))
        for r_ in retires:
            print(f"  − {r_}")
        print()
    cmd = [sys.executable, str(GEN / "inject_custom_events.py"),
           "--idea", json.dumps(entree, ensure_ascii=False, default=str)]
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
    if sauter or inclure:   # PATCH_S27_SAUTER : repris par défaut à l'étape ④
        import appliquer_et_si as ap_
        (ap_.APP_DIR / f"{hid}.sauter.json").write_text(json.dumps(
            {"sauter": sorted(sauter), "inclure": sorted(inclure)}, ensure_ascii=False), encoding="utf-8")
        print(f"✓ « Sauter » / « Inclure » gardés pour l'étape ④ : {sorted(sauter)} / {sorted(inclure)}")
    if ed._retirer_de_queue(hid):
        print(f"\n✓ entrée {hid} retirée de evenements_custom/queue.yaml (sauvegarde queue.yaml.bak_et_si)")
    print(f"✓ statut : {ed.statut(hid)}")


if __name__ == "__main__":
    main()
