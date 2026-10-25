#!/usr/bin/env python3
"""
appliquer_matrice_validee.py -- S28 : reporte les poids validés dans l'Atelier
de la matrice (25 oct 2026) dans influence_matrix.md.

Lit matrice_validee.csv (colonnes source, cible, poids_valide) et réécrit
influence_matrix.md :
  - chaque arête garde sa polarité, son lag, sa nonlinearity, son
    temporal_weight et son feedback_role ; seul `weight` change ;
  - une arête validée à 0 est retirée (le moteur l'ignorerait de toute façon) ;
  - total_edges, variable_stats et les tableaux du corps (résumé, liens forts,
    détail par variable) sont recalculés depuis les arêtes : aucune copie ne
    peut diverger.

Aperçu par défaut (rien écrit) ; --apply écrit, avec sauvegarde .bak_s28.

Usage (depuis la racine du vault) :
  python3 generator/appliquer_matrice_validee.py documentation/matrice_validee.csv
  python3 generator/appliquer_matrice_validee.py documentation/matrice_validee.csv --apply
"""
import argparse
import csv
import re
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
GEN = ICI if (ICI / "dynamique.py").exists() else ICI / "generator"
VAULT = GEN.parent

CHAMPS = ("weight", "polarity", "lag", "nonlinearity", "temporal_weight", "feedback_role")
RE_EDGE = re.compile(
    r"  - source: \[\[(\w+)\]\]\n    target: \[\[(\w+)\]\]\n"
    r"    weight: ([\d.]+)\n    polarity: (-?1)\n    lag: (\d+)\n"
    r"    nonlinearity: (\w+)\n    temporal_weight: ([\d.]+)\n    feedback_role: (\w+)\n")


def trouver_matrice():
    for p in sorted(VAULT.rglob("influence_matrix.md")):
        if "_a_supprimer" not in p.parts and ".bak" not in p.name:
            return p
    sys.exit("✗ influence_matrix.md introuvable.")


def fmt(x):
    """0.8 -> 0.8, 1.0 -> 1.0, 0.75 -> 0.75 (même écriture que le fichier d'origine)."""
    return repr(round(float(x), 2))


def lire_aretes(fm):
    aretes = []
    for m in RE_EDGE.finditer(fm):
        s, t, w, p, lag, nl, tw, fb = m.groups()
        aretes.append({"source": s, "target": t, "weight": float(w), "polarity": int(p),
                       "lag": int(lag), "nonlinearity": nl, "temporal_weight": float(tw),
                       "feedback_role": fb})
    return aretes


def construire(aretes, ordre, entete_conv):
    """Régénère tout le fichier depuis la liste d'arêtes."""
    par_source = {v: [e for e in aretes if e["source"] == v] for v in ordre}
    out = ["---", "name: influence_matrix", "type: interaction_matrix", "slug: influence_matrix",
           f"total_edges: {len(aretes)}", f"variables_count: {len(ordre)}", "",
           "# Résumé par variable (outgoing)", "variable_stats:"]
    stats = {}
    for v in ordre:
        es = par_source[v]
        ws = [e["weight"] for e in es]
        stats[v] = {
            "outgoing_edges": len(es),
            "avg_weight": round(sum(ws) / len(ws), 2) if ws else 0,
            "max_weight": max(ws) if ws else 0,
            "cascade_links": sum(1 for e in es if e["feedback_role"] == "cascade"),
            "reinforcing_links": sum(1 for e in es if e["feedback_role"] == "reinforcing"),
        }
        out.append(f"  [[{v}]]:")
        for k in ("outgoing_edges", "avg_weight", "max_weight", "cascade_links", "reinforcing_links"):
            val = stats[v][k]
            out.append(f"    {k}: {fmt(val) if isinstance(val, float) else val}")
    out += ["", "# Edges complets", "edges:"]
    blocs = []
    for e in aretes:
        blocs.append("\n".join([
            f"  - source: [[{e['source']}]]", f"    target: [[{e['target']}]]",
            f"    weight: {fmt(e['weight'])}", f"    polarity: {e['polarity']}", f"    lag: {e['lag']}",
            f"    nonlinearity: {e['nonlinearity']}", f"    temporal_weight: {fmt(e['temporal_weight'])}",
            f"    feedback_role: {e['feedback_role']}"]))
    out.append("\n\n".join(blocs))
    out += entete_conv
    out += ["---", "", "# Matrice d'influence", "",
            f"> Graphe causal du système monde — {len(aretes)} arêtes dirigées entre {len(ordre)} variables.",
            "", "## Résumé par variable", "",
            "| Variable | Edges sortants | Poids moy. | Cascades | Renforcants |", "|---|---|---|---|---|"]
    for v in ordre:
        s = stats[v]
        out.append(f"| [[{v}]] | {s['outgoing_edges']} | {fmt(s['avg_weight'])} | {s['cascade_links']} | {s['reinforcing_links']} |")
    pol = lambda e: "+" if e["polarity"] > 0 else "−"
    forts = sorted((e for e in aretes if e["weight"] >= 0.8 and e["temporal_weight"] >= 0.8),
                   key=lambda e: -e["weight"])
    out += ["", "## Liens forts (weight ≥ 0.80 et temporal_weight ≥ 0.8)", "",
            "| Source | Target | Weight | Polarity | Lag | Role |", "|---|---|---|---|---|---|"]
    for e in forts:
        out.append(f"| [[{e['source']}]] | [[{e['target']}]] | {fmt(e['weight'])} | {pol(e)} | {e['lag']} | {e['feedback_role']} |")
    out += ["", "## Détail des edges par variable", ""]
    for v in ordre:
        out += [f"### [[{v}]]", "", "| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |",
                "|---|---|---|---|---|---|---|"]
        for e in sorted(par_source[v], key=lambda e: -e["weight"]):
            out.append(f"| [[{e['target']}]] | {fmt(e['weight'])} | {pol(e)} | {e['lag']} | {e['nonlinearity']} | {fmt(e['temporal_weight'])} | {e['feedback_role']} |")
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Reporte les poids validés dans influence_matrix.md")
    ap.add_argument("csv", help="matrice_validee.csv exporté de l'Atelier")
    ap.add_argument("--apply", action="store_true", help="écrire (sinon aperçu)")
    a = ap.parse_args()

    chemin = trouver_matrice()
    texte = chemin.read_text(encoding="utf-8")
    if not texte.startswith("---\n"):
        sys.exit("✗ en-tête YAML attendu en tête de fichier : rien écrit.")
    fm = texte.split("\n---", 1)[0] + "\n"
    aretes = lire_aretes(fm)
    n_bruts = fm.count("  - source:")
    if not aretes or len(aretes) != n_bruts:
        sys.exit(f"✗ {len(aretes)} arêtes lues sur {n_bruts} blocs : format inattendu, rien écrit.")
    ordre = list(dict.fromkeys(e["source"] for e in aretes))
    entete_conv = [l for l in fm.splitlines() if l.startswith("convention_")]

    valides = {}
    with open(a.csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            valides[(r["source"], r["cible"])] = float(r["poids_valide"])
    cles = {(e["source"], e["target"]) for e in aretes}
    inconnus = set(valides) - cles
    manquants = cles - set(valides)
    if inconnus or manquants:
        sys.exit(f"✗ le CSV ne correspond pas à la matrice ({len(inconnus)} liens inconnus, "
                 f"{len(manquants)} manquants) : rien écrit.")
    for (s, t), w in valides.items():
        if not 0 <= w <= 1:
            sys.exit(f"✗ poids hors de [0, 1] pour {s} → {t} : {w}. Rien écrit.")

    changes, retires = [], []
    nouvelles = []
    for e in aretes:
        w = valides[(e["source"], e["target"])]
        if w == 0:
            retires.append(e)
            continue
        if abs(w - e["weight"]) > 1e-9:
            changes.append((e, w))
        nouvelles.append(dict(e, weight=w))

    print(f"Matrice : {chemin.relative_to(VAULT)}")
    print(f"  arêtes : {len(aretes)} → {len(nouvelles)} ({len(retires)} retirées à 0)")
    print(f"  poids modifiés : {len(changes)} (relevés {sum(1 for e, w in changes if w > e['weight'])}, "
          f"abaissés {sum(1 for e, w in changes if w < e['weight'])})")
    for e in retires:
        print(f"    − {e['source']} → {e['target']} (était {fmt(e['weight'])})")
    paires = [(s, t) for (s, t) in valides if s < t]
    sym = sum(1 for s, t in paires if valides[(s, t)] == valides[(t, s)])
    print(f"  paires symétriques : {sym} / {len(paires)}")
    print(f"  polarités, lags, temporal_weight, feedback_role : inchangés")

    nouveau = construire(nouvelles, ordre, entete_conv)
    verif = lire_aretes(nouveau.split("\n---", 1)[0] + "\n")
    if len(verif) != len(nouvelles):
        sys.exit("✗ relecture du fichier régénéré incohérente : rien écrit.")

    if not a.apply:
        print("\nAPERÇU : rien écrit. Relancer avec --apply pour écrire (sauvegarde .bak_s28).")
        return
    shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_s28"))
    chemin.write_text(nouveau + "\n", encoding="utf-8")
    print(f"\n✓ {chemin.name} réécrit (sauvegarde {chemin.name}.bak_s28).")


if __name__ == "__main__":
    main()
