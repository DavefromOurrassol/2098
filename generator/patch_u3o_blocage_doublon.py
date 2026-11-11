#!/usr/bin/env python3
"""
patch_u3o_blocage_doublon.py — Ourrassol 2098 (U3o, 11 novembre 2026)

Articles -> « et si ? » : un événement détecté « déjà connu » (présent dans event_instances,
hypotheses.yaml ou cité par l'article) n'est plus seulement signalé : « Proposer » le REFUSE,
sauf si l'auteur coche « créer quand même un doublon (effets cumulés) », case qui n'apparaît
que pour un événement déjà connu et se décoche à chaque nouveau choix.
(Le garde-fou serveur existant reste : une hypothèse de même nom ou de même description est
refusée à l'ajout.)

Dry-run par défaut ; --apply pour écrire (sauvegarde .bak_u3o). Idempotent.
À lancer depuis la racine du vault. Puis Ctrl-Maj-R dans le navigateur.
"""
import shutil
import subprocess
import sys
from pathlib import Path

APPLY = "--apply" in sys.argv

EDITS = [
    ("""  lblForcer.style.display = 'none';
  [btnDetect, etatDetect, listeDetect, lblForcer].forEach(e => zoneDetect.appendChild(e));
""", """  lblForcer.style.display = 'none';
  const [lblDoublon, cbDoublon] = caseOui("créer quand même un doublon (effets cumulés)");   // U3o
  lblDoublon.style.display = 'none';
  [btnDetect, etatDetect, listeDetect, lblForcer, lblDoublon].forEach(e => zoneDetect.appendChild(e));
"""),
    ("""    lblForcer.style.display = (!sig && evChoisi) ? '' : 'none';
""", """    lblForcer.style.display = (!sig && evChoisi) ? '' : 'none';
    lblDoublon.style.display = (!sig && evChoisi && evChoisi.deja_connu) ? '' : 'none';   // U3o
"""),
    ("""        evChoisi = ev; cbForcer.checked = false;
""", """        evChoisi = ev; cbForcer.checked = false; cbDoublon.checked = false;   // U3o
"""),
    ("""    btn.disabled = true;
    etat.style.color = '';
    etat.textContent = 'Appel IA en cours (hypothese_depuis_texte.py)…';
""", """    if (selType.value !== 'signal' && evChoisi && evChoisi.deja_connu && !cbDoublon.checked) {   // U3o
      etat.style.color = '#b03a2e';
      etat.textContent = `✗ « ${evChoisi.deja_connu_nom || evChoisi.deja_connu} » est déjà dans le vault : coche « créer quand même un doublon » si c'est voulu, ou choisis un autre événement.`;
      return;
    }
    btn.disabled = true;
    etat.style.color = '';
    etat.textContent = 'Appel IA en cours (hypothese_depuis_texte.py)…';
"""),
]


def trouver_js():
    for p in sorted(Path("gui").rglob("app.js")):
        if "U3d" in p.read_text(encoding="utf-8", errors="replace"):
            return p
    return None


js = trouver_js()
if js is None:
    sys.exit("✗ app.js de la GUI introuvable sous gui/ (lancer depuis la racine du vault)")
t = js.read_text(encoding="utf-8")
nouveau, n = t, 0
for ancien, neuf in EDITS:
    if neuf in nouveau:
        continue
    if nouveau.count(ancien) != 1:
        sys.exit(f"✗ ancre introuvable ou multiple ({nouveau.count(ancien)}) :\n{ancien}")
    nouveau = nouveau.replace(ancien, neuf)
    n += 1
if n == 0:
    sys.exit("= déjà appliqué")
print(f"+ {js} : {n} modification(s) prévue(s)")
if APPLY:
    shutil.copy2(js, str(js) + ".bak_u3o")
    js.write_text(nouveau, encoding="utf-8")
    print(f"✓ {js} écrit (sauvegarde .bak_u3o) — Ctrl-Maj-R dans le navigateur (Flask : pas de redémarrage)")
else:
    print("(dry-run : rien écrit ; relancer avec --apply)")
