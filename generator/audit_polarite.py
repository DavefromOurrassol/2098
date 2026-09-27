#!/usr/bin/env python3
"""
audit_polarite.py — Ourrassol 2098
-----------------------------------
Diagnostic en LECTURE SEULE (aucune écriture dans le vault, aucun appel LLM).

Liste toutes les entrées `impact_sur_variables` du vault et les classe
selon la combinaison de signe entre `delta_level` et `polarite` :

  A  delta < 0  et polarite = -1  -> effet appliqué POSITIF (double négatif, suspect)
  B  delta < 0  et polarite = +1  -> effet appliqué négatif (signe porté par delta)
  C  delta > 0  et polarite = -1  -> effet appliqué négatif (signe porté par polarite)
  D  delta > 0  et polarite = +1  -> effet appliqué positif
  Z  delta = 0                    -> aucun effet

Rappel du calcul (snapshot.py) : delta_appliqué = delta_level × facteur × polarite.
polarite absente = +1 (même défaut que loader.py / snapshot.py).

Sources scannées :
  - event_instances/*.md   frontmatter -> impact_sur_variables
  - instances/*.md         frontmatter -> injection.impact_sur_variables
  - signaux_custom/*.md    bloc ```yaml impact_sur_variables``` (par scénario)

Usage (depuis la racine du vault) :
  python3 generator/audit_polarite.py
  python3 generator/audit_polarite.py --report   # écrit aussi documentation/need_action/audit_polarite.md
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = VAULT_ROOT / "documentation" / "need_action" / "audit_polarite.md"

CATEGORIES = {
    "A": "delta < 0 et polarite -1 -> effet POSITIF (double négatif, suspect)",
    "B": "delta < 0 et polarite +1 -> effet négatif (signe dans delta)",
    "C": "delta > 0 et polarite -1 -> effet négatif (signe dans polarite)",
    "D": "delta > 0 et polarite +1 -> effet positif",
    "Z": "delta = 0 -> aucun effet",
}


def _frontmatter(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if not m:
        return None, raw
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    return yaml.safe_load(fm_str) or {}, raw


def _num(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _categorie(delta, polarite):
    if delta == 0:
        return "Z"
    if delta < 0:
        return "A" if polarite < 0 else "B"
    return "C" if polarite < 0 else "D"


def _entree(source, fichier, scenario, variable, delta_raw, pol_raw, note=""):
    delta = _num(delta_raw, 0.0)
    pol = _num(pol_raw, 1.0) if pol_raw is not None else 1.0
    return {
        "source": source,
        "fichier": fichier,
        "scenario": scenario or "?",
        "variable": variable or "?",
        "delta": delta,
        "polarite": pol,
        "effet": delta * pol,
        "cat": _categorie(delta, pol),
        "note": note,
    }


def scan_event_instances(entrees, erreurs):
    d = VAULT_ROOT / "event_instances"
    if not d.is_dir():
        return
    for path in sorted(d.glob("*.md")):
        if "template" in path.name.lower() or path.name.startswith(("_", ".")):
            continue
        try:
            fm, _ = _frontmatter(path)
        except yaml.YAMLError as e:
            erreurs.append(f"event_instances/{path.name} : YAML illisible ({e.__class__.__name__})")
            continue
        if not fm:
            continue
        note = "impossible: true (non appliqué)" if fm.get("impossible") else ""
        for imp in fm.get("impact_sur_variables") or []:
            if isinstance(imp, dict):
                entrees.append(_entree("événement", path.name, fm.get("scenario"),
                                       imp.get("variable"), imp.get("delta_level"),
                                       imp.get("polarite"), note))


def scan_instances(entrees, erreurs):
    d = VAULT_ROOT / "instances"
    if not d.is_dir():
        return
    for path in sorted(d.glob("*.md")):
        if "template" in path.name.lower() or path.name.startswith(("_", ".")):
            continue
        try:
            fm, _ = _frontmatter(path)
        except yaml.YAMLError as e:
            erreurs.append(f"instances/{path.name} : YAML illisible ({e.__class__.__name__})")
            continue
        if not fm:
            continue
        injection = fm.get("injection") or {}
        if not isinstance(injection, dict):
            continue
        note = "" if injection.get("type") == "custom" else "injection non custom (non appliqué)"
        for imp in injection.get("impact_sur_variables") or []:
            if isinstance(imp, dict):
                entrees.append(_entree("instance", path.name, fm.get("scenario"),
                                       imp.get("variable"), imp.get("delta_level"),
                                       imp.get("polarite"), note))


def scan_signaux(entrees, erreurs):
    d = VAULT_ROOT / "signaux_custom"
    if not d.is_dir():
        return
    for path in sorted(d.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        m = re.search(r"```yaml\nimpact_sur_variables:\n(.*?)\n```", raw, re.DOTALL)
        if not m:
            continue
        try:
            parsed = yaml.safe_load("impact_sur_variables:\n" + m.group(1)) or {}
        except yaml.YAMLError as e:
            erreurs.append(f"signaux_custom/{path.name} : YAML illisible ({e.__class__.__name__})")
            continue
        for bloc in parsed.get("impact_sur_variables") or []:
            if not isinstance(bloc, dict):
                continue
            for scen, data in (bloc.get("scenarios") or {}).items():
                if isinstance(data, dict):
                    entrees.append(_entree("signal", path.name, scen, bloc.get("variable"),
                                           data.get("delta_level"), data.get("polarite")))


def _fmt(x):
    return f"{x:+g}"


def construire_rapport(entrees, erreurs):
    lignes = ["# Audit polarité des impacts sur variables", ""]
    lignes.append(f"Entrées analysées : {len(entrees)}")
    lignes.append("")
    lignes.append("## Répartition")
    lignes.append("")
    for cat, libelle in CATEGORIES.items():
        n = sum(1 for e in entrees if e["cat"] == cat)
        par_source = {}
        for e in entrees:
            if e["cat"] == cat:
                par_source[e["source"]] = par_source.get(e["source"], 0) + 1
        detail = ", ".join(f"{s} {n_}" for s, n_ in sorted(par_source.items()))
        lignes.append(f"- **{cat}** {libelle} : {n}" + (f" ({detail})" if detail else ""))
    lignes.append("")

    suspects = [e for e in entrees if e["cat"] == "A"]
    lignes.append(f"## Cas A — double négatif ({len(suspects)})")
    lignes.append("")
    if suspects:
        lignes.append("| Source | Fichier | Scénario | Variable | delta | polarite | Effet appliqué | Note |")
        lignes.append("|---|---|---|---|---|---|---|---|")
        for e in sorted(suspects, key=lambda x: (x["source"], x["fichier"], x["variable"])):
            lignes.append(
                f"| {e['source']} | {e['fichier']} | {e['scenario']} | {e['variable']} | "
                f"{_fmt(e['delta'])} | {_fmt(e['polarite'])} | {_fmt(e['effet'])} | {e['note']} |"
            )
    else:
        lignes.append("Aucun.")
    lignes.append("")

    fichiers_mixtes = {}
    for e in entrees:
        if e["cat"] in ("B", "C"):
            fichiers_mixtes.setdefault(e["fichier"], set()).add(e["cat"])
    mixtes = sorted(f for f, cats in fichiers_mixtes.items() if cats == {"B", "C"})
    lignes.append(f"## Fichiers utilisant les deux conventions B et C ({len(mixtes)})")
    lignes.append("")
    lignes.append("Le signe est porté tantôt par delta, tantôt par polarite dans une même fiche.")
    lignes.append("")
    lignes.extend(f"- {f}" for f in mixtes) if mixtes else lignes.append("Aucun.")
    lignes.append("")

    if erreurs:
        lignes.append(f"## Fichiers illisibles ({len(erreurs)})")
        lignes.append("")
        lignes.extend(f"- {err}" for err in erreurs)
        lignes.append("")

    return "\n".join(lignes)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true",
                    help="Écrit aussi le rapport dans documentation/need_action/audit_polarite.md")
    args = ap.parse_args()

    entrees, erreurs = [], []
    scan_event_instances(entrees, erreurs)
    scan_instances(entrees, erreurs)
    scan_signaux(entrees, erreurs)

    rapport = construire_rapport(entrees, erreurs)
    print(rapport)

    if args.report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(rapport, encoding="utf-8")
        print(f"\nRapport écrit : {REPORT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
