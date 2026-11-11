#!/usr/bin/env python3
"""
patch_u3j_selection_panneau.py — Ourrassol 2098 (U3j, 11 novembre 2026)

Défaut : sélectionner du texte à la souris dans le panneau « Articles » (bloc YAML,
description…) vide toute la fiche. Cause : un clic sur le document hors du tableau et du
panneau désélectionne l'article ; or un glissement de souris commencé DANS le panneau
et relâché ailleurs produit un « clic » dont la cible est un ancêtre hors zone.
Correctif : on retient où le bouton a été enfoncé ; si c'était dans le tableau ou le
panneau, le clic n'efface rien.

Dry-run par défaut ; --apply pour écrire (sauvegarde .bak_u3j). Idempotent.
À lancer depuis la racine du vault. Puis Ctrl-Maj-R dans le navigateur.
"""
import shutil
import sys
from pathlib import Path

APPLY = "--apply" in sys.argv

ANCIEN = """    document.addEventListener('click', (e) => {
      if (!ArticlesState.selected) return;
      const tabEl = document.getElementById('tab-articles');
"""
NEUF = """    let mousedownDansZone = false;   // U3j : le glissement de sélection part-il du tableau/panneau ?
    document.addEventListener('mousedown', (e) => {
      mousedownDansZone = e.composedPath().some(el => el.classList &&
        (el.classList.contains('articles-table-wrap') || el.classList.contains('articles-sidebar')));
    });
    document.addEventListener('click', (e) => {
      if (!ArticlesState.selected) return;
      if (mousedownDansZone) return;   // U3j : sélection de texte commencée dans la zone
      const tabEl = document.getElementById('tab-articles');
"""

cands = [p for p in sorted(Path("gui").rglob("app.js")) if "articles-table-wrap" in p.read_text(encoding="utf-8", errors="replace")]
if not cands:
    sys.exit("✗ app.js de la GUI introuvable sous gui/ (lancer depuis la racine du vault)")
js = cands[0]
t = js.read_text(encoding="utf-8")
if NEUF in t:
    sys.exit(f"= {js} : déjà appliqué")
if t.count(ANCIEN) != 1:
    sys.exit(f"✗ ancre introuvable ou multiple ({t.count(ANCIEN)}) dans {js}")
print(f"+ {js} : modification prévue")
if APPLY:
    shutil.copy2(js, str(js) + ".bak_u3j")
    js.write_text(t.replace(ANCIEN, NEUF), encoding="utf-8")
    print(f"✓ {js} écrit (sauvegarde .bak_u3j) — Ctrl-Maj-R dans le navigateur (pas besoin de relancer Flask)")
else:
    print("(dry-run : rien écrit ; relancer avec --apply)")
