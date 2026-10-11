#!/usr/bin/env python3
"""
patch_s27_v73.py — Ourrassol 2098 (S27, 10 octobre 2026)
=========================================================

Simulateur « et si ? » v7.2 -> v7.3 : discipline de la carte dans la lecture IA.
Constat du test extreme_droite_2034 : le Brésil coupé dans les 6 scénarios,
malgré les faits imposés (« ne déplace pas de frontières »). Cause : l'exemple
« le Nordeste et l'Amazonie » de la consigne de partition (v7) amorçait l'IA.

1. Exemple neutre (« la moitié nord du pays »).
2. Règle : un changement de carte seulement si un territoire change de mains ;
   sinon "geographie": [] (réponse normale).
3. Option `carte: non` dans une hypothèse : l'IA est prévenue, et toute
   proposition de carte est écartée mécaniquement (listée dans les écartées).
   Contradictoire avec un bloc `geographie` manuel -> erreur.
4. hypotheses.yaml : champ documenté en en-tête ; `carte: non` ajouté à
   peste_pulmonaire_2043 et extreme_droite_2034 (si présentes).

Fichiers : generator/simuler_et_si.py (.bak_v73), et_si/hypotheses.yaml (.bak_v73)

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v73.py            # aperçu
    python3 generator/patch_s27_v73.py --apply    # écrit

Après coup : relancer avec --refaire pour que l'IA reçoive la nouvelle consigne
(le cache garde les anciennes réponses, revérifiées au nouveau contrôle).
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"
HYPS = VAULT_ROOT / "et_si" / "hypotheses.yaml"

REMPLACEMENTS_SIMU = [
    ("version", 'VERSION = "v7.2"', 'VERSION = "v7.3"'),

    ("lecture du champ carte",
     '''    norm = {
        "contraintes": contraintes,''',
     '''    # V7.3 : `carte: non` = élément sans effet territorial (choc politique, sanitaire...).
    brut_carte = h.get("carte", True)
    carte = not (brut_carte is False or str(brut_carte).strip().lower() in ("non", "no", "false", "0"))
    if not carte and geo:
        erreurs.append("`carte: non` et un bloc `geographie` rempli se contredisent")
    norm = {
        "contraintes": contraintes, "carte": carte,'''),

    ("bloc carte du prompt",
     '''    user = f"""Monde fictif Ourrassol 2098''',
     '''    bloc_carte = ""
    if not hyp.get("carte", True):
        bloc_carte = ("CET ÉLÉMENT N'A AUCUN EFFET TERRITORIAL : réponds obligatoirement "
                      "\\"geographie\\": [] (aucun rattachement, aucune nouvelle zone, aucune partition).\\n")
    user = f"""Monde fictif Ourrassol 2098'''),

    ("règle : la carte seulement si un territoire change de mains",
     '''Carte : chaque zone liste ses territoires réels ; ne propose pas de rattacher un pays à''',
     '''Carte : ne propose un changement de carte QUE si l'élément fait changer de mains un territoire
(conquête, sécession, annexion, zone rendue inhabitable). Sinon "geographie": [] : c'est la
réponse normale pour la plupart des chocs (politiques, sanitaires, technologiques).
{bloc_carte}Carte : chaque zone liste ses territoires réels ; ne propose pas de rattacher un pays à'''),

    ("exemple neutre de partition",
     "(ex. « le Nordeste et l'Amazonie »)",
     "(ex. « la moitié nord du pays »)"),

    ("filtre mécanique carte: non",
     '''        if out[sc].get("geographie") and sc not in hyp["geographie"]:''',
     '''        if not hyp.get("carte", True) and out[sc].get("geographie"):
            out[sc]["ecartees"] = (out[sc].get("ecartees") or []) + [
                f"carte : {g['pays']} ({g['action']}) écartée, hypothèse sans effet territorial (`carte: non`)"
                for g in out[sc]["geographie"]]
            out[sc]["geographie"] = []
        if out[sc].get("geographie") and sc not in hyp["geographie"]:'''),

    ("mention dans le rapport",
     '''          f"- **Effet mesuré en** : {date_fin:g}"]''',
     '''          f"- **Effet mesuré en** : {date_fin:g}"]
    if not hyp.get("carte", True):
        L.append("- **Carte** : élément déclaré sans effet territorial (`carte: non`), "
                 "aucune proposition de carte retenue")'''),
]

DOC_CARTE = '''#   carte        : optionnel, défaut oui. `carte: non` = élément sans effet territorial
#                  (choc politique, sanitaire, technologique) : la lecture IA ne propose
#                  aucun changement de carte, et toute proposition est écartée.
'''

REMPLACEMENTS_HYPS = [
    ("en-tête : champ carte (obligatoire)",
     "#   contraintes  : optionnel. Liste de faits que la lecture IA doit respecter",
     DOC_CARTE + "#   contraintes  : optionnel. Liste de faits que la lecture IA doit respecter", True),
    ("peste_pulmonaire_2043 : carte: non",
     "  - id: peste_pulmonaire_2043\n", "  - id: peste_pulmonaire_2043\n    carte: non\n", False),
    ("extreme_droite_2034 : carte: non",
     "  - id: extreme_droite_2034\n", "  - id: extreme_droite_2034\n    carte: non\n", False),
]


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7.2 -> v7.3.")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon : aperçu)")
    args = ap.parse_args()
    for f in (SIMU, HYPS):
        if not f.exists():
            sys.exit(f"✗ Fichier introuvable : {f}")
    simu, hyps = SIMU.read_text(encoding="utf-8"), HYPS.read_text(encoding="utf-8")
    if 'VERSION = "v7.3"' in simu or "bloc_carte" in simu:
        sys.exit("✗ Patch déjà appliqué (v7.3). Rien à faire.")
    if 'VERSION = "v7.2"' not in simu:
        sys.exit("✗ La v7.2 n'est pas installée : appliquer d'abord patch_s27_v72.py.")
    erreurs = []
    print("simuler_et_si.py :")
    for libelle, ancien, nouveau in REMPLACEMENTS_SIMU:
        n = simu.count(ancien)
        if n != 1:
            erreurs.append(f"simuler_et_si.py — {libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        simu = simu.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    print("hypotheses.yaml :")
    for libelle, ancien, nouveau, obligatoire in REMPLACEMENTS_HYPS:
        n = hyps.count(ancien)
        if n == 1:
            hyps = hyps.replace(ancien, nouveau)
            print(f"  ✓ {libelle}")
        elif obligatoire:
            erreurs.append(f"hypotheses.yaml — {libelle} : texte attendu trouvé {n} fois (1 attendu)")
        else:
            print(f"  – {libelle} : hypothèse introuvable, ignoré (ajouter `carte: non` à la main)")
    try:
        compile(simu, str(SIMU), "exec")
    except SyntaxError as e:
        erreurs.append(f"simuler_et_si.py ne compilerait pas : {e}")
    try:
        import yaml
        yaml.safe_load(hyps)
    except Exception as e:  # noqa: BLE001
        erreurs.append(f"hypotheses.yaml modifié illisible : {e}")
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    for f, contenu in ((SIMU, simu), (HYPS, hyps)):
        shutil.copy(f, f.with_name(f.name + ".bak_v73"))
        f.write_text(contenu, encoding="utf-8")
        print(f"→ écrit : {f.relative_to(VAULT_ROOT)} (sauvegarde {f.name}.bak_v73)")
    print("\nSimulateur passé en v7.3.")


if __name__ == "__main__":
    main()
