#!/usr/bin/env python3
"""
patch_u4h2_remplacer_grise.py — Ourrassol 2098 (21 nov 2026)

U4h2 : le bouton « Remplacer dans hypotheses.yaml » (U4h) est bien désactivé quand
l'hypothèse chargée n'est pas modifiable, mais la classe yaml-btn-save n'a pas de style
« désactivé » : il paraissait actif. Ajout d'une classe propre au bouton et d'une règle CSS
(une seule fois) : grisé (opacité 0,45) et curseur interdit quand il est désactivé.
Les autres boutons de l'application ne changent pas.

Fichier touché : gui/static/app.js

Usage (depuis la racine du vault) :
    python3 generator/patch_u4h2_remplacer_grise.py           # dry-run
    python3 generator/patch_u4h2_remplacer_grise.py --apply   # écrit (.bak_u4h2)
Après --apply : Cmd-Maj-R (pas besoin de relancer Flask).
"""
import argparse
import shutil
import sys
from pathlib import Path

JS = Path("gui/static/app.js")
TAG = "U4h2"

AVANT = '''  btnRemplacer.disabled = true;
  btnRemplacer.title = '''
APRES = '''  btnRemplacer.disabled = true;
  btnRemplacer.classList.add('u4h-remplacer');   // U4h2 : grisé quand désactivé
  if (!document.getElementById('style-u4h2')) {
    const st = document.createElement('style');
    st.id = 'style-u4h2';
    st.textContent = '.u4h-remplacer:disabled { opacity: 0.45; cursor: not-allowed; }';
    document.head.appendChild(st);
  }
  btnRemplacer.title = '''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not JS.is_file():
        sys.exit(f"✗ {JS} introuvable : lancer depuis la racine du vault")
    texte = JS.read_text(encoding="utf-8")
    if TAG in texte:
        print(f"✓ {TAG} déjà appliqué, rien à faire")
        return
    n = texte.count(AVANT)
    if n != 1:
        sys.exit(f"✗ ancre du bouton « Remplacer » trouvée {n} fois (1 attendue) : U4h appliqué ? Rien n'est écrit")
    nouveau = texte.replace(AVANT, APRES)
    print(f"[{TAG}] {JS} : {len(texte.splitlines())} -> {len(nouveau.splitlines())} lignes")
    if not args.apply:
        print(f"[{TAG}] dry-run : relancer avec --apply pour écrire")
        return
    shutil.copy(JS, JS.with_name(JS.name + ".bak_u4h2"))
    JS.write_text(nouveau, encoding="utf-8")
    print(f"✓ [{TAG}] appliqué (sauvegarde {JS.name}.bak_u4h2). Cmd-Maj-R dans le navigateur.")


if __name__ == "__main__":
    main()
