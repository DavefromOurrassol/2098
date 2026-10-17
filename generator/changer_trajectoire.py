#!/usr/bin/env python3
"""
changer_trajectoire.py — Ourrassol 2098 (S27, 13 octobre 2026)
==============================================================

Change la `trajectoire` d'une ou plusieurs instances (instances/<slug>.md),
en ne modifiant que la ligne `trajectoire:` du frontmatter (et `annee_fin:`
si demandé ; --ecraser-annee-fin remplace aussi une date déjà remplie).
Refuse une fiche dont la trajectoire actuelle n'est pas celle
annoncée. Aucune fiche n'est écrite si l'une d'elles est refusée.

--annee-fin N : remplit `annee_fin` (seulement si elle est vide ou null) pour
les fiches qui passent à une trajectoire terminale (transformé, disparu,
historique, mythifié). Une annee_fin déjà remplie n'est jamais écrasée.

USAGE
    python3 generator/changer_trajectoire.py --changer slug=avant:apres [--changer ...] [--annee-fin 2076]           # aperçu
    python3 generator/changer_trajectoire.py --changer slug=avant:apres [--changer ...] [--annee-fin 2076] --apply   # écrit (.bak_traj)
"""

import argparse
import re
import shutil
import sys
import unicodedata
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent
TRAJECTOIRES = ["émergent", "marginal", "ascendant", "dominant", "mature", "déclinant",
                "résiduel", "transformé", "disparu", "historique", "mythifié"]
TERMINALES = {"transformé", "disparu", "historique", "mythifié"}


def plie(s):
    s = unicodedata.normalize("NFKD", str(s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def canon(v):
    return {plie(t): t for t in TRAJECTOIRES}.get(plie(v))


def traiter(slug, avant, apres, annee_fin, ecraser=False):
    """Retourne (chemin, nouveau texte, lignes de rapport) ou lève ValueError."""
    p = VAULT / "instances" / f"{slug}.md"
    if not p.exists():
        raise ValueError(f"{slug} : fiche instances/{slug}.md introuvable")
    texte = p.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", texte, re.S)
    if not m:
        raise ValueError(f"{slug} : frontmatter introuvable")
    fm_lignes = m.group(2).split("\n")
    idx = [i for i, l in enumerate(fm_lignes) if re.match(r"^trajectoire:", l)]
    if len(idx) != 1:
        raise ValueError(f"{slug} : {len(idx)} ligne(s) `trajectoire:` au premier niveau (attendu 1)")
    actuelle = re.sub(r"^trajectoire:\s*", "", fm_lignes[idx[0]]).strip().strip("'\"")
    if canon(actuelle) != avant:
        raise ValueError(f"{slug} : trajectoire actuelle {actuelle!r}, pas {avant!r}")
    fm_lignes[idx[0]] = f"trajectoire: {apres}"
    rapport = [f"  {slug} : {actuelle} → {apres}"]

    if annee_fin is not None and apres in TERMINALES:
        idx_f = [i for i, l in enumerate(fm_lignes) if re.match(r"^annee_fin:", l)]
        if len(idx_f) > 1:
            raise ValueError(f"{slug} : plusieurs lignes `annee_fin:`")
        if idx_f:
            val = re.sub(r"^annee_fin:\s*", "", fm_lignes[idx_f[0]]).strip()
            if val in ("", "null", "~", "None"):
                fm_lignes[idx_f[0]] = f"annee_fin: {annee_fin}"
                rapport.append(f"    annee_fin : {val or '(vide)'} → {annee_fin}")
            elif ecraser and val != str(annee_fin):
                fm_lignes[idx_f[0]] = f"annee_fin: {annee_fin}"
                rapport.append(f"    annee_fin : {val} → {annee_fin} (écrasée)")
            else:
                rapport.append(f"    annee_fin déjà remplie ({val}) : gardée")
        else:
            fm_lignes.insert(idx[0] + 1, f"annee_fin: {annee_fin}")
            rapport.append(f"    annee_fin ajoutée : {annee_fin}")

    fm_txt = "\n".join(fm_lignes)
    try:
        fm = yaml.safe_load(re.sub(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]", r"\1", fm_txt)) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"{slug} : frontmatter illisible après modification ({e})")
    if fm.get("trajectoire") != apres:
        raise ValueError(f"{slug} : relecture inattendue ({fm.get('trajectoire')!r})")
    inj = (fm.get("injection") or {}).get("type") if isinstance(fm.get("injection"), dict) else None
    if inj == "custom":
        rapport.append("    ⚠ instance custom : ne régénérer qu'avec generate_instances.py --injection-custom")
    if fm.get("exclure_articles") or fm.get("priorite_forcee"):
        rapport.append("    ⚠ marqueur exclure_articles / priorite_forcee : à reposer après toute régénération")
    nouveau = m.group(1) + fm_txt + m.group(3) + texte[m.end():]
    return p, nouveau, rapport


def main():
    ap = argparse.ArgumentParser(description="Change la trajectoire d'instances (aperçu par défaut).")
    ap.add_argument("--changer", action="append", required=True, metavar="slug=avant:apres")
    ap.add_argument("--annee-fin", type=int, default=None)
    ap.add_argument("--ecraser-annee-fin", action="store_true",
                    help="avec --annee-fin : remplace aussi une annee_fin déjà remplie")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    a_ecrire, erreurs, rapport = [], [], []
    for c in a.changer:
        mm = re.match(r"^\s*([a-z0-9_]+)\s*=\s*([^:]+):(.+)$", c)
        if not mm:
            erreurs.append(f"{c!r} : format attendu slug=avant:apres")
            continue
        slug, avant, apres = mm.group(1), canon(mm.group(2)), canon(mm.group(3))
        if not avant or not apres:
            erreurs.append(f"{c!r} : trajectoire inconnue ({' | '.join(TRAJECTOIRES)})")
            continue
        try:
            p, nouveau, r = traiter(slug, avant, apres, a.annee_fin, a.ecraser_annee_fin)
            a_ecrire.append((p, nouveau))
            rapport += r
        except ValueError as e:
            erreurs.append(str(e))

    print(("ÉCRITURE" if a.apply else "APERÇU (rien écrit)") + f" — {len(a_ecrire)} fiche(s)")
    print("\n".join(rapport) or "  (aucune)")
    if erreurs:
        print("\n✗ Refusé :")
        print("\n".join(f"  {e}" for e in erreurs))
        sys.exit("✗ Rien n'est écrit tant qu'une fiche est refusée.")
    if not a.apply:
        print("Relancer avec --apply pour écrire (sauvegarde .bak_traj).")
        return
    for p, nouveau in a_ecrire:
        bak = p.with_name(p.name + ".bak_traj")
        if not bak.exists():
            shutil.copy2(p, bak)
        p.write_text(nouveau, encoding="utf-8")
    print(f"✓ {len(a_ecrire)} fiche(s) écrite(s).")


if __name__ == "__main__":
    main()
