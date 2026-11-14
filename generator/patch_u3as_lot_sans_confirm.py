#!/usr/bin/env python3
"""
patch_u3as_lot_sans_confirm.py — Ourrassol 2098 (14 novembre 2026)

Correctif U3ar : le bouton « Traiter en lot » ne faisait rien si le navigateur
bloquait la boîte de confirmation (confirm). La confirmation est retirée ; un
message « Lot démarré » s'affiche aussitôt.
Prérequis : U3ar. Après application : Cmd+Maj+R.

    python3 generator/patch_u3as_lot_sans_confirm.py            # aperçu
    python3 generator/patch_u3as_lot_sans_confirm.py --apply
"""
import argparse, shutil, sys
from pathlib import Path

JS = Path("gui/static/app.js")
ANCRE = ("      if (!confirm(`Traiter ${cartes.filter(c => !c.fait).length} idée(s) : un appel IA chacune. "
         "Les blocs sans problème seront ajoutés à hypotheses.yaml. Continuer ?`)) return;\n")
REMPL = ("      resume.style.color = '';   // U3as\n"
         "      resume.textContent = `⏳ Lot démarré : ${cartes.filter(c => !c.fait).length} idée(s), un appel IA chacune (quelques minutes). Les blocs sans problème sont ajoutés à hypotheses.yaml.`;\n")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    ap.add_argument("--js", default=str(JS)); a = ap.parse_args()
    p = Path(a.js)
    if not p.exists():
        print(f"✗ Introuvable : {p}"); return 2
    t = p.read_text(encoding="utf-8")
    if "U3ar" not in t:
        print("✗ Prérequis U3ar absent."); return 1
    if "U3as" in t:
        print("✗ U3as déjà appliqué."); return 1
    if t.count(ANCRE) != 1:
        print(f"✗ ancre : {t.count(ANCRE)} occurrence(s) au lieu de 1 — rien écrit."); return 1
    print("  ✓ app.js : confirmation retirée")
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply."); return 0
    bak = p.with_name(p.name + ".bak_u3as"); shutil.copy2(p, bak)
    p.write_text(t.replace(ANCRE, REMPL, 1), encoding="utf-8")
    print(f"✓ Écrit : {p} (sauvegarde : {bak.name})\nÀ faire : Cmd+Maj+R.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
