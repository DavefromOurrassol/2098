#!/usr/bin/env python3
"""
patch_s27_recit.py — Ourrassol 2098 (S27, 10 octobre 2026)

trace_injection.py, récit construit par le script (recit_modele) :
- la liste des variables touchées n'est plus coupée à 200 caractères au
  milieu d'un mot (« climat e. ») : au-delà de 5 variables, « et N autres » ;
- les variables sont écrites par leur nom lisible (champ name/nom de
  variables/<slug>.md), avec accents, au lieu du slug sans underscores.
Sert au simulateur « et si ? » et à trace_injection.py lui-même.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_recit.py --dry-run
    python3 generator/patch_s27_recit.py
Sauvegarde : generator/trace_injection.py.bak_recit. Refuse un second passage.
"""
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "trace_injection.py"
MARQUEUR = "# S27 (10 oct) : nom lisible de la variable"

REMPLACEMENTS = [
    ('''def _libelle_var(v):
    return v.replace("_", " ")
''', '''def _libelle_var(v):
    # S27 (10 oct) : nom lisible de la variable (variables/<slug>.md), en minuscule
    # initiale dans la phrase ; sinon le slug sans underscores.
    label = _label_variable(v)
    if not label or label == v:
        return v.replace("_", " ")
    label = str(label).strip()
    if len(label) > 1 and label[1].isupper():   # sigle : laissé tel quel
        return label
    return label[:1].lower() + label[1:]


def _enumerer(noms, max_n=5):
    """« a, b et c » ; au-delà de max_n : « a, b, c, d, e et N autre(s) »."""
    noms = [n for n in noms if n]
    if len(noms) > max_n:
        reste = len(noms) - max_n
        return ", ".join(noms[:max_n]) + f" et {reste} autre{'s' if reste > 1 else ''}"
    if len(noms) > 1:
        return ", ".join(noms[:-1]) + " et " + noms[-1]
    return noms[0] if noms else ""
'''),
    ('''    phrases = [f"Apparu en {chrono['apparition']:.0f} dans le scénario {sc}, {nom} agit d'abord sur "
               + ", ".join(_libelle_var(r["variable"]) for r in reps if r["mode"] == "direct")[:200] + "."]
''', '''    directes = [_libelle_var(r["variable"]) for r in reps if r["mode"] == "direct"]
    phrases = [f"Apparu en {chrono['apparition']:.0f} dans le scénario {sc}, {nom} agit d'abord sur "
               + (_enumerer(directes) or "le monde") + "."]
'''),
]


def main():
    dry = "--dry-run" in sys.argv
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable")
    src = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in src:
        sys.exit("✗ Patch déjà appliqué : rien à faire.")
    nouveau = src
    for avant, apres in REMPLACEMENTS:
        n = nouveau.count(avant)
        if n != 1:
            sys.exit(f"✗ Ancre trouvée {n} fois (1 attendue) :\n{avant[:100]}")
        nouveau = nouveau.replace(avant, apres)
    try:
        compile(nouveau, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas : {e}")
    print(f"{len(REMPLACEMENTS)} modifications prêtes dans {CIBLE.name} "
          f"({len(src)} → {len(nouveau)} caractères).")
    if dry:
        print("Aperçu seulement (--dry-run) : rien n'est écrit.")
        return
    sauvegarde = CIBLE.with_name(CIBLE.name + ".bak_recit")
    sauvegarde.write_text(src, encoding="utf-8")
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"✓ {CIBLE.name} corrigé (sauvegarde : {sauvegarde.name}).")


if __name__ == "__main__":
    main()
