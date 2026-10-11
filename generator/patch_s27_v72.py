#!/usr/bin/env python3
"""
patch_s27_v72.py — Ourrassol 2098 (S27, 10 octobre 2026)
=========================================================

Deux corrections repérées sur le test « peste pulmonaire » (10 oct) :

1. gui/zone_repository.py (rapport d'impact de la Carte, réutilisé par le
   simulateur) : le nom du pays était cherché comme une simple sous-chaîne.
   « Inde » était trouvé dans « indépendants » (50 faux positifs). Recherche
   désormais en mot entier, dans les trois endroits : mentions dans les fiches,
   lignes du registre, sous-zones orphelines. Conséquence assumée : un adjectif
   (« iraniennes ») n'est plus compté comme une mention du pays. (.bak_mots)

2. generator/simuler_et_si.py v7.1 -> v7.2 : le modèle de réponse JSON donné à
   l'IA laissait croire qu'une partie de partition porte à la fois `zone` et
   `nouvelle_zone` (deux partitions écartées en eco_communalism). Modèle
   réécrit avec deux exemples distincts + consigne explicite. (.bak_v72)

Rappel : redémarrer Flask après coup (zone_repository.py est chargé par le GUI).

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v72.py            # aperçu
    python3 generator/patch_s27_v72.py --apply    # écrit
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
REPO = VAULT_ROOT / "gui" / "zone_repository.py"
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"

FONCTION_MOT = r'''def _mot_present(mot_plie: str, texte_plie: str):
    """Recherche en MOT ENTIER (textes déjà passés par _fold) : « inde » ne doit
    pas être trouvé dans « independants ». Retourne le match (ou None)."""
    if not mot_plie:
        return None
    return re.search(r"(?<![a-z0-9])" + re.escape(mot_plie) + r"(?![a-z0-9])", texte_plie)


'''

FICHIERS = [
    (REPO, ".bak_mots", "def _mot_present", [
        ("fonction _mot_present",
         "@dataclass\nclass GeoFile:",
         FONCTION_MOT + "@dataclass\nclass GeoFile:"),
        ("mentions dans les fiches",
         '''                folded_raw = _fold(raw)
                if pays_folded in folded_raw:
                    idx = folded_raw.find(pays_folded)''',
         '''                folded_raw = _fold(raw)
                trouve = _mot_present(pays_folded, folded_raw)
                if trouve:
                    idx = trouve.start()'''),
        ("lignes du registre",
         '''                if stripped.startswith("|") and pays_folded in _fold(stripped):''',
         '''                if stripped.startswith("|") and _mot_present(pays_folded, _fold(stripped)):'''),
        ("sous-zones orphelines",
         '''                    if pays_folded in _fold(entite):''',
         '''                    if _mot_present(pays_folded, _fold(entite)):'''),
    ]),
    (SIMU, ".bak_v72", 'VERSION = "v7.2"', [
        ("version", 'VERSION = "v7.1"', 'VERSION = "v7.2"'),
        ("modèle JSON des parties",
         '''                  "parties": [{{"zone": "slug (ou nouvelle_zone comme ci-dessus)", "portion": "..."}}],''',
         '''                  "parties": [{{"zone": "slug d'une zone existante", "portion": "..."}},
                              {{"nouvelle_zone": {{"slug": "...", "nom": "...", "type": "...", "statut": "..."}}, "portion": "..."}}],'''),
        ("consigne : zone OU nouvelle_zone",
         "zone, ni dans deux zones d'un même bloc (une zone et sa sous-zone).",
         '''zone, ni dans deux zones d'un même bloc (une zone et sa sous-zone).
Chaque partie porte SOIT "zone" (zone existante) SOIT "nouvelle_zone", jamais les deux.'''),
    ]),
]


def main():
    ap = argparse.ArgumentParser(description="S27 v7.2 : recherche en mot entier + modèle de partition.")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon : aperçu)")
    args = ap.parse_args()
    resultats, erreurs = [], []
    for chemin, bak, marqueur, remplacements in FICHIERS:
        if not chemin.exists():
            sys.exit(f"✗ Fichier introuvable : {chemin}")
        texte = chemin.read_text(encoding="utf-8")
        if marqueur in texte:
            sys.exit(f"✗ Patch déjà appliqué ({chemin.name} contient {marqueur!r}). Rien à faire.")
        print(f"{chemin.name} :")
        for libelle, ancien, nouveau in remplacements:
            n = texte.count(ancien)
            if n != 1:
                erreurs.append(f"{chemin.name} — {libelle} : texte attendu trouvé {n} fois (1 attendu)")
                continue
            texte = texte.replace(ancien, nouveau)
            print(f"  ✓ {libelle}")
        try:
            compile(texte, str(chemin), "exec")
        except SyntaxError as e:
            erreurs.append(f"{chemin.name} ne compilerait pas : {e}")
        resultats.append((chemin, bak, texte))
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    for chemin, bak, texte in resultats:
        shutil.copy(chemin, chemin.with_name(chemin.name + bak))
        chemin.write_text(texte, encoding="utf-8")
        print(f"→ écrit : {chemin.relative_to(VAULT_ROOT)} (sauvegarde {chemin.name}{bak})")
    print("\nSimulateur passé en v7.2. Redémarrer Flask (zone_repository.py modifié).")


if __name__ == "__main__":
    main()
