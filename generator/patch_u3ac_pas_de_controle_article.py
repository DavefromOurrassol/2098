#!/usr/bin/env python3
"""
patch_u3ac_pas_de_controle_article.py — Ourrassol 2098 (14 novembre 2026)
Suite de U3aa. Le fait imposé « [ARTICLE] » (la citation) est contrôlé par l'IA sur un récit que
U3aa remplace par la description d'hypothèse : il est jugé « non respecté », déclenche deux
réécritures inutiles (écrasées aussitôt) et un ⚠ trompeur (test du 14 nov.). Correctif dans
verifier_contraintes : quand U3aa s'applique, le fait issu de l'article n'est plus contrôlé.
Les autres faits imposés (reste, change, zone, contrainte hors article) le sont toujours ; sans
autre fait, plus aucun appel IA de contrôle. Nécessite U3aa déjà appliqué.

Usage (racine du vault) :
    python3 generator/patch_u3ac_pas_de_controle_article.py            # dry-run
    python3 generator/patch_u3ac_pas_de_controle_article.py --apply    # écrit (.bak_u3ac)
"""
import argparse, py_compile, shutil, sys, tempfile
from pathlib import Path

CIBLE = Path("generator/inject_custom_events.py")
ANCRE = '''    faits = [f for f in _faits_du_scenario(idea, scenario)
             if (f.get("sort") or "contrainte") in SORTS_CONTROLES_S30]
    if not faits:
        return []
'''
NOUVEAU = '''    faits = [f for f in _faits_du_scenario(idea, scenario)
             if (f.get("sort") or "contrainte") in SORTS_CONTROLES_S30]
    if FICHE_DEPUIS_ARTICLE_U3AA and str(idea.get("description") or "").strip():   # U3ac
        # le texte est celui de l'hypothèse (U3aa) : le fait tiré de l'article n'est plus à contrôler
        faits = [f for f in faits if not _fait_de_article_u3w(f["fait"], scenario)]
    if not faits:
        return []
'''

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not CIBLE.exists():
        sys.exit(f"{CIBLE} introuvable : lancer depuis la racine du vault.")
    src = CIBLE.read_text(encoding="utf-8")
    if "U3ac" in src:
        sys.exit("U3ac déjà appliqué : rien à faire.")
    if "U3aa" not in src:
        sys.exit("Abandon : appliquer d'abord patch_u3aa_fiche_depuis_article.py.")
    if src.count(ANCRE) != 1:
        sys.exit(f"Abandon, rien écrit : ancre trouvée {src.count(ANCRE)} fois (attendu 1).")
    neuf = src.replace(ANCRE, NOUVEAU)
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "inject_custom_events.py"; t.write_text(neuf, encoding="utf-8")
        try: py_compile.compile(str(t), doraise=True)
        except py_compile.PyCompileError as e: sys.exit(f"Abandon, ne compile pas : {e}")
    print(" · verifier_contraintes : le fait [ARTICLE] n'est plus contrôlé quand U3aa s'applique")
    if not a.apply:
        print("\nDry-run : le résultat compile, rien n'est écrit. Relancer avec --apply."); return
    sauv = CIBLE.with_name(CIBLE.name + ".bak_u3ac")
    shutil.copy2(CIBLE, sauv); CIBLE.write_text(neuf, encoding="utf-8")
    py_compile.compile(str(CIBLE), doraise=True)
    print(f"\nÉcrit : {CIBLE} (sauvegarde : {sauv.name}). py_compile OK.")

if __name__ == "__main__":
    main()
