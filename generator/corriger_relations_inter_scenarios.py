#!/usr/bin/env python3
"""
corriger_relations_inter_scenarios.py — Ourrassol 2098 (25 sept 2026)
=======================================================================

Corrige les alliances/oppositions qui pointent vers une instance d'un AUTRE
scénario (erreurs de génération repérées par audit_lore.py, contrôle
« relations inter-scénarios »).

Pour chaque relation `X_{autre_scenario}` d'une fiche du scénario S :
  - si `X_S` existe (même entité dans le bon scénario), n'est pas la fiche
    elle-même et n'est pas déjà dans l'une de ses deux listes
      -> REMPLACÉE par `X_S` (l'intention est conservée)
  - sinon -> RETIRÉE

AUCUNE exception (décision David, 26 sept 2026) : les scénarios sont des
mondes parallèles, une relation vers un autre scénario est toujours une
erreur. Les 2 alliés `_reference` de la NAT, conservés le 25 sept, ne le
sont plus ; l'option --garder a été retirée.

Écriture via fix_alliances_oppositions.write_alliances_patch() (frontmatter
+ section « ## Relations »), .bak par fiche ; une fiche qui n'a plus aucune
relation voit sa section « ## Relations » retirée (write_alliances_patch ne
le fait pas).

Usage (depuis la racine du vault) :
  python3 generator/corriger_relations_inter_scenarios.py --all                # aperçu
  python3 generator/corriger_relations_inter_scenarios.py --all --execute      # écriture
  python3 generator/corriger_relations_inter_scenarios.py --scenario breakdown
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_alliances_oppositions import (  # noqa: E402
    INSTANCES_DIR, SCENARIOS, parse_md, write_alliances_patch,
)

def scenario_de(ref, sauf):
    return next((s for s in SCENARIOS if s != sauf and ref.endswith(f"_{s}")), None)


def planifier(scenario):
    fiches = {}
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, _ = parse_md(path)
        if fm and fm.get("scenario", scenario) == scenario:
            fiches[fm.get("slug", path.stem)] = (path, fm)
    plan, journal = {}, []
    for slug, (path, fm) in fiches.items():
        al = [str(x) for x in fm.get("alliances") or []]
        op = [str(x) for x in fm.get("oppositions") or []]
        change = False
        for champ, liste in (("alliances", al), ("oppositions", op)):
            for ref in list(liste):
                autre = scenario_de(ref, scenario)
                if not autre:
                    continue
                base = ref[: -len(autre) - 1]
                candidat = f"{base}_{scenario}"
                i = liste.index(ref)
                if candidat in fiches and candidat != slug and candidat not in al + op:
                    liste[i] = candidat
                    journal.append(f"  ↻ {slug} ({champ}) : {ref} → {candidat}")
                else:
                    raison = ("équivalent absent" if candidat not in fiches else
                              "équivalent = la fiche elle-même" if candidat == slug else
                              "équivalent déjà présent")
                    del liste[i]
                    journal.append(f"  − {slug} ({champ}) : {ref} retiré ({raison})")
                change = True
        if change:
            plan[path] = (al, op)
    return plan, journal


def ecrire(path, al, op):
    shutil.copy2(path, path.with_suffix(".md.bak"))
    write_alliances_patch(path, al, op)
    if not al and not op:
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^(---\s*\n.*?\n---\s*\n)(.*)", raw, re.DOTALL)
        corps = re.sub(r"\n## Relations\n(?:.*?\n)*?(?=\n## |\Z)", "\n", m.group(2))
        path.write_text(m.group(1) + corps, encoding="utf-8")
    fm, _ = parse_md(path)
    return (fm.get("alliances") or []) == al and (fm.get("oppositions") or []) == op


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scenario", choices=SCENARIOS)
    g.add_argument("--all", action="store_true")
    ap.add_argument("--execute", action="store_true", help="Écrit (sinon aperçu)")
    args = ap.parse_args()

    print(f"Mode : {'ÉCRITURE' if args.execute else 'APERÇU (rien écrit)'}")
    total_r = total_f = 0
    for sc in (SCENARIOS if args.all else [args.scenario]):
        plan, journal = planifier(sc)
        print(f"\n=== {sc} : {len(journal)} relation(s), {len(plan)} fiche(s)")
        print("\n".join(journal) if journal else "  (rien)")
        total_r += len(journal)
        total_f += len(plan)
        if args.execute:
            for path, (al, op) in plan.items():
                if not ecrire(path, al, op):
                    print(f"  ✗ relecture non conforme : {path.name} (restaurer le .bak)")
    print(f"\nTotal : {total_r} relation(s) corrigée(s) sur {total_f} fiche(s)"
          + ("" if args.execute else " — relance avec --execute pour écrire"))


if __name__ == "__main__":
    main()
