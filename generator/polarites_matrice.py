#!/usr/bin/env python3
"""
polarites_matrice.py — Ourrassol 2098
--------------------------------------
Étape 5 du chantier "convention unique d'intensité" (27 septembre 2026).

Avec la convention 0 = calme / 100 = crise pour les 12 variables, les
niveaux des 6 scénarios montent et descendent tous ensemble (corrélation
de +0,46 à +0,99 sur les 66 paires) : la crise se propage. Décision de
David (option b) :

  - TOUS les liens de la matrice passent à polarity +1 ("la crise de la
    source aggrave la cible") ...
  - ... SAUF 3 amortisseurs volontaires à -1 (décroissance forcée :
    l'effondrement de l'économie ou de la production réduit la pression
    sur le climat et l'énergie) :
        systeme_economique_redistribution -> climat_environnement_global
        systemes_productifs_travail       -> climat_environnement_global
        systemes_productifs_travail       -> energie_ressources_critiques

Modifie le frontmatter (edges) ET les tableaux du corps de
influence_matrix.md. À lancer APRÈS migrer_echelles.py (refus sinon).

Par défaut : SIMULATION, rien n'est écrit. Avec --appliquer : sauvegarde
unique en .bak_etape5 (jamais écrasée), puis écriture. Idempotent :
marqueur `convention_polarite` dans le frontmatter.

Usage (depuis la racine du vault) :
  python3 generator/polarites_matrice.py              # simulation
  python3 generator/polarites_matrice.py --appliquer  # écriture réelle
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
MARQUEUR = "convention_polarite: intensite_2026-09-27"

AMORTISSEURS = {
    ("systeme_economique_redistribution", "climat_environnement_global"),
    ("systemes_productifs_travail", "climat_environnement_global"),
    ("systemes_productifs_travail", "energie_ressources_critiques"),
}


def polarite_cible(src, tgt):
    return -1 if (src, tgt) in AMORTISSEURS else 1


def trouver_matrice():
    for p in [VAULT_ROOT / "variables" / "influence_matrix.md", VAULT_ROOT / "influence_matrix.md"]:
        if p.exists():
            return p
    trouves = [p for p in VAULT_ROOT.rglob("influence_matrix.md")]
    return trouves[0] if trouves else None


def decouper(raw):
    m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*\n", raw, re.DOTALL)
    if not m:
        return None, raw
    return m.group(1), raw[m.end():]


def charger_yaml(fm_str):
    return yaml.safe_load(re.sub(r"\[\[([^\]]+)\]\]", r"\1", fm_str)) or {}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--appliquer", action="store_true", help="Écrit réellement (avec .bak_etape5)")
    args = ap.parse_args()
    print("=== POLARITÉS MATRICE — {} ===".format("ÉCRITURE RÉELLE" if args.appliquer else "SIMULATION (rien n'est écrit)"))

    path = trouver_matrice()
    if not path:
        print("✗ influence_matrix.md introuvable")
        return 1
    raw = path.read_text(encoding="utf-8")
    fm_str, corps = decouper(raw)
    if fm_str is None:
        print("✗ frontmatter introuvable")
        return 1
    if MARQUEUR.split(":")[0] + ":" in fm_str:
        print(f"✓ {path.name} : déjà traitée (convention_polarite présente), rien à faire.")
        return 0
    if "convention_echelle:" not in fm_str:
        print("✗ migrer_echelles.py n'a pas encore été appliqué sur cette matrice -- lance-le d'abord.")
        return 1

    edges_avant = charger_yaml(fm_str).get("edges", []) or []

    # Frontmatter
    lignes = fm_str.split("\n")
    src = tgt = None
    changes_fm = []
    for i, ligne in enumerate(lignes):
        m = re.match(r"^\s*-\s*source:\s*\[*([a-z_]+)\]*\s*$", ligne)
        if m:
            src, tgt = m.group(1), None
            continue
        m = re.match(r"^\s*target:\s*\[*([a-z_]+)\]*\s*$", ligne)
        if m:
            tgt = m.group(1)
            continue
        m = re.match(r"^(\s*polarity:\s*)(-?1)\s*$", ligne)
        if m and src and tgt:
            voulu = polarite_cible(src, tgt)
            if int(m.group(2)) != voulu:
                lignes[i] = f"{m.group(1)}{voulu}"
                changes_fm.append((src, tgt, int(m.group(2)), voulu))
            src = tgt = None
    fm_str = "\n".join(lignes).rstrip("\n") + "\n" + MARQUEUR + "\n"

    # Corps : tableaux "Liens forts" (| [[src]] | [[tgt]] | w | ± |) et
    # "Détail par variable" (sous ### [[src]] : | [[tgt]] | w | ± |)
    signe = {1: "+", -1: "−"}
    lignes = corps.split("\n")
    src_section = None
    nb_corps = 0
    for i, ligne in enumerate(lignes):
        m = re.match(r"^###\s*\[\[([a-z_]+)\]\]", ligne)
        if m:
            src_section = m.group(1)
            continue
        if re.match(r"^##\s", ligne):
            src_section = None
        if not ligne.startswith("|"):
            continue
        cells = ligne.split("|")
        vals = [c.strip() for c in cells]
        liens = [re.fullmatch(r"\[\[([a-z_]+)\]\]", v) for v in vals]
        idx = [k for k, l in enumerate(liens) if l]
        if len(idx) >= 2 and idx[1] == idx[0] + 1:
            s, t, k = liens[idx[0]].group(1), liens[idx[1]].group(1), idx[1] + 2
        elif len(idx) == 1 and src_section:
            s, t, k = src_section, liens[idx[0]].group(1), idx[0] + 2
        else:
            continue
        if k >= len(vals) or vals[k] not in ("+", "−", "-"):
            continue
        voulu = signe[polarite_cible(s, t)]
        if vals[k] != voulu:
            cells[k] = cells[k].replace(vals[k], voulu, 1)
            lignes[i] = "|".join(cells)
            nb_corps += 1
    corps = "\n".join(lignes)

    # Vérification par relecture
    edges_apres = charger_yaml(fm_str).get("edges", []) or []
    erreurs = [e for e in edges_apres if e["polarity"] != polarite_cible(e["source"], e["target"])]
    nb_neg = sum(1 for e in edges_apres if e["polarity"] == -1)
    if erreurs or len(edges_apres) != len(edges_avant) or nb_neg != len(AMORTISSEURS):
        print(f"✗ vérification échouée ({len(erreurs)} liens incorrects, {nb_neg} liens à -1), rien écrit")
        return 1

    vers_plus = sum(1 for c in changes_fm if c[3] == 1)
    vers_moins = sum(1 for c in changes_fm if c[3] == -1)
    print(f"✓ {path.name} : {len(changes_fm)} liens modifiés dans le frontmatter "
          f"({vers_plus} passent à +1, {vers_moins} passent à -1), {nb_corps} lignes dans les tableaux du corps")
    print(f"  Résultat : {len(edges_apres) - nb_neg} liens à +1, {nb_neg} amortisseurs à -1 :")
    for s, t in sorted(AMORTISSEURS):
        print(f"    {s} -> {t}")

    if args.appliquer:
        bak = path.with_suffix(path.suffix + ".bak_etape5")
        if not bak.exists():
            bak.write_text(raw, encoding="utf-8")
        path.write_text(f"---\n{fm_str}---\n{corps}", encoding="utf-8")
        print(f"  Écrit (sauvegarde : {bak.name}).")
    else:
        print("Relance avec --appliquer pour écrire.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
