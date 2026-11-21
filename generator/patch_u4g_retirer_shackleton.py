#!/usr/bin/env python3
"""
patch_u4g_retirer_shackleton.py — Ourrassol 2098 (21 nov 2026)

Retire de et_si/hypotheses.yaml l'hypothèse `shackleton_platinoides_2052` (wild card
d'essai du 15 nov, simulée, non adoptée ; décision de David le 21 nov : supprimée).
et_si_supprimer.py ne traite que les entités, d'où ce script.

Le bloc retiré va de « - id: shackleton_platinoides_2052 » jusqu'à l'hypothèse
suivante (ou la fin du fichier). Contrôles : le fichier relu doit compter une
hypothèse de moins et ne plus contenir l'id ; sinon retour arrière.
Rien d'autre n'est touché : le rapport
documentation/need_action/et_si_shackleton_platinoides_2052.md et les caches de
generator/state/ restent (archives de l'essai).

Usage (depuis la racine du vault) :
    python3 generator/patch_u4g_retirer_shackleton.py           # dry-run
    python3 generator/patch_u4g_retirer_shackleton.py --apply   # écrit (.bak_u4g)
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

CIBLE = Path("et_si/hypotheses.yaml")
ID = "shackleton_platinoides_2052"
TAG = "U4g"


def ids(texte):
    data = yaml.safe_load(texte) or {}
    return [h.get("id") for h in data.get("hypotheses") or [] if isinstance(h, dict)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault")
    texte = CIBLE.read_text(encoding="utf-8")
    avant = ids(texte)
    if ID not in avant:
        print(f"✓ {ID} absente de {CIBLE} : rien à faire")
        return
    lignes = texte.splitlines(keepends=True)
    debuts = [i for i, l in enumerate(lignes) if re.match(rf"^  - id: {ID}\s*$", l)]
    if len(debuts) != 1:
        sys.exit(f"✗ « - id: {ID} » trouvé {len(debuts)} fois en début de bloc (1 attendu) : rien n'est écrit")
    d = debuts[0]
    f = next((i for i in range(d + 1, len(lignes)) if re.match(r"^  - id: ", lignes[i])), len(lignes))
    while d > 0 and not lignes[d - 1].strip():   # lignes vides qui précèdent le bloc
        d -= 1
    retire = "".join(lignes[d:f])
    nouveau = "".join(lignes[:d]).rstrip("\n") + "\n" + ("\n" + "".join(lignes[f:]) if f < len(lignes) else "")
    apres = ids(nouveau)
    if ID in apres or len(apres) != len(avant) - 1:
        sys.exit(f"✗ contrôle : {len(avant)} -> {len(apres)} hypothèses, id encore présent = {ID in apres} : rien n'est écrit")
    print(f"[{TAG}] {CIBLE} : retrait de {ID} (lignes {d + 1}-{f}, {len(retire.splitlines())} lignes)")
    print(f"[{TAG}] hypothèses : {len(avant)} -> {len(apres)} ; dernière : {apres[-1]}")
    if not args.apply:
        print(f"[{TAG}] dry-run : relancer avec --apply pour écrire")
        return
    bak = CIBLE.with_name(CIBLE.name + ".bak_u4g")
    shutil.copy(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    try:
        relu = ids(CIBLE.read_text(encoding="utf-8"))
        if relu != apres:
            raise ValueError("relecture différente du contrôle")
    except Exception as e:  # noqa: BLE001 -- retour arrière
        shutil.copy(bak, CIBLE)
        sys.exit(f"✗ {e} : fichier restauré")
    print(f"✓ [{TAG}] {ID} retirée (sauvegarde {bak.name})")


if __name__ == "__main__":
    main()
