#!/usr/bin/env python3
"""
patch_u3ao_liste_entite.py — Ourrassol 2098 (14 novembre 2026)

Cosmétique (vu dans le GUI) : une entité s'affichait « … (None) » dans la liste
des hypothèses, faute de date. Maintenant « … (entité) » ; événements et
signaux inchangés.

  simuler_et_si.py : --lister --json ajoute le champ `type` de chaque hypothèse ;
  gui/app.py       : l'étiquette de la liste utilise « (entité) » pour une entité.

Après application : redémarrer Flask (app.py).

Usage (depuis la racine du vault) :
    python3 generator/patch_u3ao_liste_entite.py            # aperçu
    python3 generator/patch_u3ao_liste_entite.py --apply    # écrit
Sauvegarde .bak_u3ao ; refuse un second passage ; py_compile (restauration si échec).
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

MARQUEUR = "U3ao"
SIM = Path("generator/simuler_et_si.py")
APP = Path("gui/app.py")

SIM_REMPL = [(
    "type dans --lister --json",
    '                          "date": h.get("date"), "erreurs": err, "statut": st})\n',
    '                          "date": h.get("date"), "erreurs": err, "statut": st,\n'
    '                          "type": str(h.get("type") or "evenement")})   # U3ao\n',
)]
APP_REMPL = [(
    "étiquette « (entité) »",
    '''                labels[h["id"]] = (f"{h.get('nom')} ({h.get('date')})"
                                   + (" ⚠ invalide" if h.get("erreurs") else ""))
''',
    '''                _quand = "entité" if h.get("type") == "entite" else h.get("date")   # U3ao
                labels[h["id"]] = (f"{h.get('nom')} ({_quand})"
                                   + (" ⚠ invalide" if h.get("erreurs") else ""))
''',
)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--sim", default=str(SIM))
    ap.add_argument("--app", default=str(APP))
    a = ap.parse_args()
    prepares = []
    for chemin, remp in ((Path(a.sim), SIM_REMPL), (Path(a.app), APP_REMPL)):
        if not chemin.exists():
            print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
            return 2
        texte = chemin.read_text(encoding="utf-8")
        if MARQUEUR in texte:
            print(f"✗ {MARQUEUR} déjà appliqué dans {chemin.name} — refus d'un second passage.")
            return 1
        nouveau = texte
        for libelle, ancre, rempl in remp:
            n = nouveau.count(ancre)
            if n != 1:
                print(f"✗ {chemin.name} : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
                return 1
            nouveau = nouveau.replace(ancre, rempl, 1)
            print(f"  ✓ {chemin.name} : {libelle}")
        prepares.append((chemin, texte, nouveau))
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, _, apres in prepares:
        bak = chemin.with_name(chemin.name + ".bak_u3ao")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(apres, encoding="utf-8")
    try:
        for chemin, _ in baks:
            py_compile.compile(str(chemin), doraise=True)
    except py_compile.PyCompileError as e:
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)
        print(f"✗ py_compile a échoué, fichiers restaurés : {e}")
        return 1
    for chemin, bak in baks:
        print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})")
    print("\nÀ faire : redémarrer Flask (app.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
