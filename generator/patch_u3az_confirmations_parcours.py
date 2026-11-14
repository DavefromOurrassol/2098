#!/usr/bin/env python3
"""
patch_u3az_confirmations_parcours.py — Ourrassol 2098 (14 novembre 2026)

Dans ton navigateur, les boîtes de confirmation (confirm) semblent bloquées : un clic
sur « Injecter » ne fait rien, sans message. Dans le panneau Parcours, « Injecter » et
« Annuler la décision » passent à une confirmation EN DEUX CLICS : le 1er clic change le
libellé du bouton (« ⚠ Cliquer encore pour … »), le 2e confirme ; sans 2e clic, le bouton
revient à son libellé après 8 secondes. Les autres boutons sont inchangés.

  gui/static/app.js seulement. Après application : Cmd+Maj+R.

    python3 generator/patch_u3az_confirmations_parcours.py            # aperçu
    python3 generator/patch_u3az_confirmations_parcours.py --apply
Sauvegarde .bak_u3az ; refuse un second passage ; contrôle de syntaxe avec restauration.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3az"
APP_JS = Path("gui/static/app.js")

JS_REMPL = [
    (
        "fonction armer2",
        "function buildDecisionHypothese() {\n",
        r"""// U3az : confirmation en deux clics (confirm() peut être bloqué par le navigateur : le clic ne fait alors rien)
function armer2(btn, libelleConfirm) {
  if (btn.dataset.arme) {
    clearTimeout(Number(btn.dataset.arme));
    delete btn.dataset.arme;
    btn.textContent = btn.dataset.libelle;
    return true;
  }
  btn.dataset.libelle = btn.textContent;
  btn.textContent = libelleConfirm;
  btn.dataset.arme = String(setTimeout(() => {
    delete btn.dataset.arme;
    btn.textContent = btn.dataset.libelle;
  }, 8000));
  return false;
}

function buildDecisionHypothese() {
""",
    ),
    (
        "Injecter",
        "    if (!confirm((typeCourant === 'signal' ? 'Injecter ce signal' : 'Injecter cet événement') + ' dans le vault ? (appels IA ; plusieurs minutes)')) return;\n",
        "    if (!armer2(btnInjecter, '⚠ Cliquer encore pour injecter (appels IA, plusieurs minutes)')) return;   // U3az\n",
    ),
    (
        "Annuler la décision",
        "    if (!confirm('Annuler la décision prise sur cette hypothèse ?')) return;\n",
        "    if (!armer2(btnAnnuler, '⚠ Cliquer encore pour annuler la décision')) return;   // U3az\n",
    ),
]


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
    if MARQUEUR in t:
        print(f"✗ {MARQUEUR} déjà appliqué — refus d'un second passage.")
        return 1
    nouveau = t
    for libelle, ancre, rempl in JS_REMPL:
        n = nouveau.count(ancre)
        if n != 1:
            print(f"✗ app.js : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
            return 1
        nouveau = nouveau.replace(ancre, rempl, 1)
        print(f"  ✓ app.js : {libelle}")
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    bak = chemin.with_name(chemin.name + ".bak_u3az")
    shutil.copy2(chemin, bak)
    chemin.write_text(nouveau, encoding="utf-8")
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
