#!/usr/bin/env python3
"""
patch_u3ag_etape5.py — Ourrassol 2098 (14 novembre 2026)
Panneau « Et si ? », étape ⑤ : elle n'a pas « disparu », elle apparaît seulement après
« Appliquer » (et_si_statut.py : étape 5 si le journal d'application existe, sinon 4). Le panneau
ne l'expliquait pas. Deux retouches de texte, sans changer la logique :
  1. gui/static/app.js : à l'étape ④ (rien appliqué encore), le résumé dit que l'étape ⑤
     « À faire à la main » apparaîtra après « Appliquer ».
  2. generator/et_si_statut.py : l'alerte « simulation sans passe exhaustive : cocher Lecture IA et
     Passe exhaustive » contredisait le manuel (Lecture IA inutile pour un simple événement
     d'article) : elle devient une information, plus un ordre.

Usage (racine du vault) :
    python3 generator/patch_u3ag_etape5.py            # dry-run
    python3 generator/patch_u3ag_etape5.py --apply    # écrit (.bak_u3ag)
Recharger la page du GUI après --apply.
"""
import argparse, py_compile, shutil, subprocess, sys, tempfile
from pathlib import Path

JS = Path("gui/static/app.js")
ST = Path("generator/et_si_statut.py")

A_JS = "      : (e.operations ? '' : 'Fichier des opérations absent : resimuler avant d\\'appliquer.');\n"
N_JS = ("      : (e.operations ? (e.etape === 4 && typeCourant !== 'signal'   // U3ag\n"
        "          ? 'Pas encore appliquée. L\\'étape ⑤ « À faire à la main » apparaîtra après « Appliquer ».' : '')\n"
        "        : 'Fichier des opérations absent : resimuler avant d\\'appliquer.');\n")
A_ST = ('            alertes.append("simulation sans passe exhaustive : cocher « Lecture IA » et « Passe exhaustive »")\n')
N_ST = ('            alertes.append("simulation sans passe exhaustive : à cocher (avec « Lecture IA ») seulement si "   # U3ag\n'
        '                           "l\'événement doit toucher des fiches existantes ; inutile pour un simple événement d\'article")\n')

def une_fois(src, ancre, nouveau, nom):
    if src.count(ancre) != 1:
        sys.exit(f"Abandon, rien écrit ({nom}) : ancre trouvée {src.count(ancre)} fois (attendu 1).")
    return src.replace(ancre, nouveau)

def node_ok(texte):
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "app.js"; t.write_text(texte, encoding="utf-8")
        try:
            return subprocess.run(["node", "--check", str(t)], capture_output=True).returncode == 0
        except FileNotFoundError:
            return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for c in (JS, ST):
        if not c.exists():
            sys.exit(f"{c} introuvable : lancer depuis la racine du vault.")
    sj, ss = JS.read_text(encoding="utf-8"), ST.read_text(encoding="utf-8")
    if "U3ag" in sj or "U3ag" in ss:
        sys.exit("U3ag déjà appliqué : rien à faire.")
    nj, ns = une_fois(sj, A_JS, N_JS, JS.name), une_fois(ss, A_ST, N_ST, ST.name)
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "et_si_statut.py"; t.write_text(ns, encoding="utf-8")
        try: py_compile.compile(str(t), doraise=True)
        except py_compile.PyCompileError as e: sys.exit(f"Abandon, et_si_statut.py ne compile pas : {e}")
    if node_ok(sj) is False:
        print(" · node ne valide pas le fichier d'origine (version trop ancienne) : syntaxe JS non vérifiée")
    elif node_ok(nj) is False:
        sys.exit("Abandon : erreur de syntaxe JavaScript dans le résultat, rien n'est écrit.")
    print(" · app.js : résumé de l'étape ④ (annonce de l'étape ⑤)")
    print(" · et_si_statut.py : alerte « passe exhaustive » reformulée")
    if not a.apply:
        print("\nDry-run : les résultats sont valides, rien n'est écrit. Relancer avec --apply."); return
    for c, neuf in ((JS, nj), (ST, ns)):
        sauv = c.with_name(c.name + ".bak_u3ag")
        shutil.copy2(c, sauv); c.write_text(neuf, encoding="utf-8")
        print(f"Écrit : {c} (sauvegarde : {sauv.name}).")
    py_compile.compile(str(ST), doraise=True)

if __name__ == "__main__":
    main()
