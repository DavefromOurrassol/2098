#!/usr/bin/env python3
"""
patch_u3bc_alertes_lot.py — Ourrassol 2098 (14 novembre 2026)

Correctif U3bb : le traitement en lot affichait comme « à voir » toute ligne ⚠ de la
sortie d'injection, y compris des messages sans gravité (« zone corrigée : … », en-tête
« AVERTISSEMENTS (1) » de la validation, « nouvelle tentative… » de la relance de
localisation). Seules restent les vraies alertes : injection partielle, fiches encore sans
zone après relance, relance impossible.

  gui/static/app.js seulement. Prérequis : U3bb. Après application : Cmd+Maj+R.

    python3 generator/patch_u3bc_alertes_lot.py            # aperçu
    python3 generator/patch_u3bc_alertes_lot.py --apply
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3bc"
APP_JS = Path("gui/static/app.js")
ANCRE = "      const avert = lignes.filter(x => x.trim().startsWith('⚠'));\n"
REMPL = ("      // U3bc : ignorer les ⚠ sans gravité (corrections automatiques de zone, en-tête de validation, relance en cours)\n"
         "      const avert = lignes.filter(x => x.trim().startsWith('⚠') &&\n"
         "        !/zone corrigée|AVERTISSEMENTS|nouvelle tentative/.test(x));\n")


def _node_check(chemin):
    try:
        r = subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None, "node absent"
    return r.returncode == 0, r.stderr.strip()


def _premiere_erreur(msg):
    lignes = [l for l in msg.splitlines() if l.strip()]
    return " | ".join(l.strip() for l in lignes[:4] if "SyntaxError" in l or l.strip().startswith("("))[:300]


def verifier_js(chemin, original):
    """Ne bloque que sur une erreur NOUVELLE (un vieux node refuse déjà « ||= » dans l'original)."""
    ok, msg = _node_check(chemin)
    if ok:
        return True, "node --check OK"
    if ok is False:
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "original.js"
            copie.write_text(Path(original).read_text(encoding="utf-8"), encoding="utf-8")
            ok0, msg0 = _node_check(copie)
        if ok0 is False and _premiere_erreur(msg) == _premiere_erreur(msg0):
            return True, "node --check refuse une syntaxe déjà présente dans l'original : aucune erreur nouvelle"
        return False, msg[:400]
    t = chemin.read_text(encoding="utf-8")
    ok2 = t.count("{") == t.count("}") and t.count("(") == t.count(")")
    return ok2, "accolades/parenthèses équilibrées (node absent)" if ok2 else "accolades/parenthèses déséquilibrées"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--js", default=str(APP_JS))
    a = ap.parse_args()
    chemin = Path(a.js)
    if not chemin.exists():
        print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
        return 2
    t = chemin.read_text(encoding="utf-8")
    if "U3bb" not in t:
        print("✗ Prérequis U3bb absent de app.js.")
        return 1
    if MARQUEUR in t:
        print(f"✗ {MARQUEUR} déjà appliqué — refus d'un second passage.")
        return 1
    if t.count(ANCRE) != 1:
        print(f"✗ ancre : {t.count(ANCRE)} occurrence(s) au lieu de 1 — rien écrit.")
        return 1
    print("  ✓ app.js : filtre des alertes du lot")
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    bak = chemin.with_name(chemin.name + ".bak_u3bc")
    shutil.copy2(chemin, bak)
    chemin.write_text(t.replace(ANCRE, REMPL, 1), encoding="utf-8")
    ok, msg = verifier_js(chemin, bak)
    if not ok:
        shutil.copy2(bak, chemin)
        print(f"✗ Contrôle de syntaxe app.js échoué, fichier restauré : {msg}")
        return 1
    print(f"  (app.js : {msg})")
    print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})\n\nÀ faire : Cmd+Maj+R dans le navigateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
