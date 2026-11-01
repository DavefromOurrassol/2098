#!/usr/bin/env python3
"""patch_s30_liste_sauts_js.py — Ourrassol 2098, 1er novembre 2026

Complément de patch_s30_liste_sauts.py : à l'étape ③ du panneau « Parcours »,
le bouton « Liste de l'étape ④ » envoyait un corps vide ; il envoie désormais
les champs « Sauter » / « Inclure » de l'étape ③ (tri3()), comme « Simuler
l'injection » et « Injecter ». La liste marque alors ✓ / – et affiche ce qui
sera retiré de l'entrée, sans appel IA.

Usage (depuis la racine du vault) :
    python3 generator/patch_s30_liste_sauts_js.py
Puis recharger la page du GUI (Flask déjà redémarré après patch_s30_liste_sauts.py,
sinon le redémarrer). Idempotent (marqueur PATCH_S30_LISTE_SAUTS_JS) ;
sauvegarde gui/static/app.js.bak_s30listejs.
"""
import shutil
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
JS = VAULT / "gui" / "static" / "app.js"
MARQUEUR = "PATCH_S30_LISTE_SAUTS_JS"
AVANT = "  btnInjListe.addEventListener('click', () => appeler('injecter', 'liste', {}));"
APRES = ("  btnInjListe.addEventListener('click', () => appeler('injecter', 'liste', tri3()));"
         "   // PATCH_S30_LISTE_SAUTS_JS")


def main():
    if not JS.exists():
        sys.exit(f"✗ {JS} introuvable — lancer depuis la racine du vault. Rien fait.")
    src = JS.read_text(encoding="utf-8")
    if MARQUEUR in src:
        print("· déjà appliqué — rien fait.")
        return
    n = src.count(AVANT)
    if n != 1:
        sys.exit(f"✗ ligne attendue trouvée {n} fois (attendu 1) — rien fait.")
    bak = JS.with_name(JS.name + ".bak_s30listejs")
    shutil.copy2(JS, bak)
    JS.write_text(src.replace(AVANT, APRES, 1), encoding="utf-8")
    print(f"✓ gui/static/app.js patché (sauvegarde {bak.name})")
    print("→ Redémarrer Flask entièrement, puis recharger la page.")


if __name__ == "__main__":
    main()
