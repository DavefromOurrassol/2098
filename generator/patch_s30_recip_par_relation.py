#!/usr/bin/env python3
"""patch_s30_recip_par_relation.py — Ourrassol 2098, 1er novembre 2026

Défaut relevé au test réel de S30 (chute_holdfast_2072) : dans le bloc
« Réciprocité » de l'aperçu ④, un ajout était classé « complétées par
réciprocité des opérations » dès que la fiche SOURCE de la relation avait été
touchée par une opération. Ainsi l'opposition ancienne RGMS → consortiums de
données (relation à sens unique déjà dans le vault, C4) passait pour un effet
de l'hypothèse, parce que l'opération 12 ajoutait une autre opposition au RGMS.

Correctif (appliquer_et_si.py, afficher_reciprocite) : tri par RELATION. Un
ajout « + <type> `a` » dans la fiche f vient des opérations si a est touchée ET
si la relation a → f n'existait pas dans la fiche de a sur le disque (avant
écriture). Sinon : « HORS hypothèse ». Une fiche peut figurer dans les deux
rubriques. reciprocite_prevue() est inchangée.

Usage (depuis la racine du vault) :
    python3 generator/patch_s30_recip_par_relation.py
Idempotent (marqueur PATCH_S30_RECIP_PAR_RELATION) ; sauvegarde
appliquer_et_si.py.bak_s30recipRel ; contrôle de compilation, restauration si échec.
"""
import py_compile
import shutil
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
CIBLE = GEN / "appliquer_et_si.py"
MARQUEUR = "PATCH_S30_RECIP_PAR_RELATION"

AVANT = '''    touches = {p.stem for p in W.changes()}
    for sc in dict.fromkeys(o["sc"] for o in ops if o["retenue"] and o["genre"] in ("relation", "disparition")):
        ajouts, conflits = reciprocite_prevue(sc, W)
        par_op = {f: v for f, v in ajouts.items()
                  if any(x.split("`")[1] in touches for x in v)}
        anciennes = {f: v for f, v in ajouts.items() if f not in par_op}
'''

APRES = '''    touches = {p.stem for p in W.changes()}
    # PATCH_S30_RECIP_PAR_RELATION : tri par relation, pas par fiche. Un ajout « + <type> `a` »
    # dans f vient des opérations si a est touchée ET si a ne citait pas déjà f (fiche sur disque).
    cache = {}

    def _avant(a, champ):
        if a not in cache:
            try:
                d = decoupe((INSTANCES / f"{a}.md").read_text(encoding="utf-8"))
                cache[a] = (lire_fm(d[1]) if d else None) or {}
            except OSError:
                cache[a] = {}
        v = cache[a].get(champ)
        return [str(x).strip() for x in v if x] if isinstance(v, list) else []

    def _de_op(f, x):
        try:
            a, champ = x.split("`")[1], x.split()[1] + "s"
        except IndexError:
            return False
        return a in touches and f not in _avant(a, champ)

    for sc in dict.fromkeys(o["sc"] for o in ops if o["retenue"] and o["genre"] in ("relation", "disparition")):
        ajouts, conflits = reciprocite_prevue(sc, W)
        par_op, anciennes = {}, {}
        for f, v in ajouts.items():
            for x in v:
                (par_op if _de_op(f, x) else anciennes).setdefault(f, []).append(x)
'''


def main():
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable — lancer depuis la racine du vault. Rien fait.")
    src = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in src:
        print("· déjà appliqué — rien fait.")
        return
    n = src.count(AVANT)
    if n != 1:
        sys.exit(f"✗ bloc de tri trouvé {n} fois (attendu 1) — rien fait.")
    bak = CIBLE.with_name(CIBLE.name + ".bak_s30recipRel")
    shutil.copy2(CIBLE, bak)
    CIBLE.write_text(src.replace(AVANT, APRES, 1), encoding="utf-8")
    try:
        py_compile.compile(str(CIBLE), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, CIBLE)
        sys.exit(f"✗ compilation échouée, fichier restauré : {e}")
    print(f"✓ {CIBLE.name} patché (sauvegarde {bak.name})")


if __name__ == "__main__":
    main()
