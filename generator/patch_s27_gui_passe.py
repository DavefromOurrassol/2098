#!/usr/bin/env python3
"""
patch_s27_gui_passe.py — Ourrassol 2098 (S27, 12 octobre 2026)
==============================================================

Ajoute la case « Passe exhaustive » au formulaire du simulateur « et si ? »
(gui/scripts_config.json, entrée simuler_et_si), juste après « Lecture des
conséquences par l'IA ». Rien d'autre n'est modifié (mise en forme du fichier
conservée à l'identique, vérifiée avant écriture).

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_gui_passe.py --dry-run && python3 generator/patch_s27_gui_passe.py
Sauvegarde gui/scripts_config.json.bak_gui_passe ; refuse un second passage.
Redémarrer Flask ensuite.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent.parent / "gui" / "scripts_config.json"

OPTION = {
    "flag": "--passe-exhaustive",
    "type": "checkbox",
    "label": "Passe exhaustive : relire toutes les fiches (payant)",
    "default": False,
    "description": "⚠️ Relit toutes les instances du scénario et les événements datés après l'hypothèse "
                   "(≈ 0,05 à 0,11 $ par scénario ; lots gardés en cache). Chaque changement est classé "
                   "obligatoire (la fiche devient fausse) ou possible. Les obligatoires entrent dans la liste "
                   "d'application, les 20 possibles prioritaires en étapes facultatives, et les entités les "
                   "plus touchées dans l'entrée d'injection (acteurs_hint). À cocher avec la lecture IA, qui "
                   "lui sert de contexte. « Nouveau tirage » relance aussi la passe.",
    "mode_only": "simuler",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cible", default=str(CIBLE))
    args = ap.parse_args()
    cible = Path(args.cible)
    texte = cible.read_text(encoding="utf-8")
    data = json.loads(texte)
    if json.dumps(data, ensure_ascii=False, indent=2) != texte:
        sys.exit("✗ Mise en forme de scripts_config.json inattendue : rien écrit (la réécriture la changerait).")
    entrees = [e for e in data if e.get("id") == "simuler_et_si"]
    if len(entrees) != 1:
        sys.exit(f"✗ Entrée simuler_et_si trouvée {len(entrees)} fois (1 attendue) : rien écrit.")
    options = entrees[0]["options"]
    if any(o.get("flag") == "--passe-exhaustive" for o in options):
        sys.exit("✗ Case déjà présente : rien à faire.")
    rang = [k for k, o in enumerate(options) if o.get("flag") == "--consequences-ia"]
    if len(rang) != 1:
        sys.exit("✗ Option --consequences-ia introuvable : rien écrit.")
    options.insert(rang[0] + 1, OPTION)
    nouveau = json.dumps(data, ensure_ascii=False, indent=2)
    json.loads(nouveau)
    if args.dry_run:
        print("✓ Case ajoutable après « Lecture des conséquences par l'IA » (dry-run, rien écrit).")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_gui_passe"))
    cible.write_text(nouveau, encoding="utf-8")
    print("✓ Case « Passe exhaustive » ajoutée ; sauvegarde .bak_gui_passe. Redémarrer Flask.")


if __name__ == "__main__":
    main()
