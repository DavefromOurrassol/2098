#!/usr/bin/env python3
"""
patch_u4q_veille_date.py — Ourrassol 2098 (22 novembre 2026)
============================================================

B9, veille : la date d'observation devient une date IMPOSÉE.

Jusqu'ici, l'onglet 🔭 Veille signaux faibles écrivait seulement « Observé en … »
dans le texte envoyé à l'IA (✨ Envoyer vers « et si ? ») ; l'IA restait libre de
choisir une autre date. Désormais, l'année (et le mois pour un événement, si la
date d'observation est de la forme 2026-03) est aussi envoyée comme date imposée,
par le même chemin que l'onglet Articles (U3c) : appliquer_imposes() la pose
après la réponse de l'IA et signale l'écart (« date imposée : … (l'IA proposait …) »).

Décision conservée : un signal reste borné à 2026-2097 (bornes déjà appliquées
par appliquer_imposes). Sans date d'observation lisible, rien ne change.

Un seul fichier : gui/static/app.js. Après --apply : Cmd-Maj-R ; pas de relance de Flask.

Usage (depuis la racine du vault) :
    python3 generator/patch_u4q_veille_date.py           # dry-run
    python3 generator/patch_u4q_veille_date.py --apply   # écrit (.bak_u4q)
"""

import argparse
import shutil
import sys
from pathlib import Path

TAG = "u4q"

REMPLACEMENTS = {
    Path("gui/static/app.js"): [
        ("1. fonction _veilleDateObservation()",
         "function renderVeillePanel() {\n",
         "// U4q : date d'observation -> date imposée (année ; année.mois pour un événement\n"
         "// si la date est de la forme 2026-03). '' si aucune année lisible.\n"
         "function _veilleDateObservation(c, type) {\n"
         "  const m = String(c.observe_le || '').match(/\\b(2\\d{3})(?:[-./](\\d{1,2}))?\\b/);\n"
         "  if (!m) return '';\n"
         "  const an = parseInt(m[1], 10);\n"
         "  const mo = m[2] ? parseInt(m[2], 10) : 0;\n"
         "  if (type === 'evenement' && mo >= 1 && mo <= 12) return Math.round((an + mo / 100) * 100) / 100;\n"
         "  return an;\n"
         "}\n"
         "\n"
         "function renderVeillePanel() {\n"),
        ("2. ✨ Envoyer vers « et si ? » : date d'observation imposée",
         "        body: JSON.stringify({ texte, type: action === 'proposer' ? type : '' }),\n",
         "        body: JSON.stringify({ texte, type: action === 'proposer' ? type : '',\n"
         "          ...(action === 'proposer' && _veilleDateObservation(c, type) !== ''   // U4q\n"
         "            ? { date: _veilleDateObservation(c, type) } : {}) }),\n"),
    ],
}


def main():
    ap = argparse.ArgumentParser(description="Patch U4q : date d'observation de la veille imposée.")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon dry-run)")
    args = ap.parse_args()
    manquants = [str(f) for f in REMPLACEMENTS if not f.is_file()]
    if manquants:
        sys.exit("✗ introuvable(s) : " + ", ".join(manquants) + " (lancer depuis la racine du vault)")
    if "_veilleDateObservation" in Path("gui/static/app.js").read_text(encoding="utf-8"):
        sys.exit("✗ U4q déjà appliqué : rien à faire.")
    a_ecrire, ok = {}, True
    for chemin, rempl in REMPLACEMENTS.items():
        texte = chemin.read_text(encoding="utf-8")
        for nom, ancien, neuf in rempl:
            n = texte.count(ancien)
            if n != 1:
                print(f"✗ {chemin} : {nom} — ancre trouvée {n} fois (attendu 1)")
                ok = False
                continue
            texte = texte.replace(ancien, neuf)
            print(f"✓ {chemin} : {nom}")
        a_ecrire[chemin] = texte
    if not ok:
        sys.exit("✗ Patch non appliqué : aucun fichier n'a été modifié.")
    print("✓ Toutes les ancres trouvées.")
    if not args.apply:
        print("\n(dry-run) Rien n'est écrit. Relancer avec --apply.")
        return
    for chemin, texte in a_ecrire.items():
        shutil.copy(chemin, chemin.with_name(chemin.name + f".bak_{TAG}"))
        chemin.write_text(texte, encoding="utf-8")
        print(f"→ {chemin} écrit (sauvegarde {chemin.name}.bak_{TAG})")
    print("\nSuite : Cmd-Maj-R dans le navigateur (app.js). Pas de relance de Flask.")


if __name__ == "__main__":
    main()
