#!/usr/bin/env python3
"""
patch_s27_v77.py — Ourrassol 2098 (S27, 10 octobre 2026)
=========================================================

Simulateur « et si ? » v7.6 -> v7.7 : entrée GUI (étape 1, sans IA nouvelle).

1. gui/scripts_config.json : entrée « 🔮 Simulateur « et si ? » » (id
   `simuler_et_si`), section entites_nettoyage, juste après « Tracer ».
   Options : hypothèse (--id ; vide = liste des hypothèses), scénario, date,
   lecture IA des conséquences (payant), nouveau tirage (--refaire), récit IA
   (avancé). Le rapport est toujours écrit (--report en argument fixe).
   Fichiers rattachés : et_si/hypotheses.yaml (éditable) et le rapport du
   dernier lancement (lecture seule).
2. generator/simuler_et_si.py : avec --report, écrit aussi
   documentation/need_action/et_si_dernier_lancement.md (copie du rapport),
   affiché dans le panneau.

Fichiers : gui/scripts_config.json (.bak_v77), generator/simuler_et_si.py (.bak_v77)
Après coup : redémarrer Flask.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v77.py            # aperçu
    python3 generator/patch_s27_v77.py --apply    # écrit
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"
CONF = VAULT_ROOT / "gui" / "scripts_config.json"

ENTREE = {
    "id": "simuler_et_si",
    "label": "Simulateur « et si ? »",
    "icon": "🔮",
    "section": "entites_nettoyage",
    "script": "simuler_et_si.py",
    "description": ("Teste une hypothèse de et_si/hypotheses.yaml AVANT toute injection : effet chiffré sur "
                    "les 12 variables (avec et sans l'hypothèse), tensions, aperçu de la carte et, en option, "
                    "lecture des conséquences sur le lore par l'IA. Ne modifie jamais le vault. Laisser "
                    "« Hypothèse » vide pour lister les hypothèses disponibles. Le rapport est écrit dans "
                    "documentation/need_action/et_si_<id>.md (et affiché ci-dessous)."),
    "requires": [],
    "fixed_args": ["--report"],
    "options": [
        {
            "flag": "--id",
            "type": "text",
            "label": "Hypothèse (id)",
            "optional": True,
            "placeholder": "ex : peste_pulmonaire_2043",
            "description": "Identifiant d'une hypothèse de et_si/hypotheses.yaml. Vide = liste des hypothèses "
                           "disponibles, sans rien simuler. Une hypothèse mal remplie est refusée avec la liste "
                           "de ses erreurs."
        },
        {
            "flag": "--scenario",
            "type": "select",
            "label": "Scénario",
            "source": "config_scenarios",
            "default": "",
            "optional": True,
            "description": "Limite la simulation à ce scénario. Vide = tous les scénarios de l'hypothèse."
        },
        {
            "flag": "--date",
            "type": "number",
            "label": "Effet mesuré en",
            "min": 2026,
            "max": 2098,
            "default": 2098,
            "description": "Année à laquelle l'effet est mesuré (pas avant l'apparition de l'hypothèse)."
        },
        {
            "flag": "--consequences-ia",
            "type": "checkbox",
            "label": "Lecture des conséquences par l'IA (payant)",
            "default": False,
            "description": "⚠️ Un appel IA par scénario (≈ 1-2 centimes chacun) : trajectoires d'entités, "
                           "relations, statuts de zone, carte, nouvelles entités, toutes contrôlées. La réponse "
                           "est gardée en cache : relancer la même hypothèse ne coûte rien."
        },
        {
            "flag": "--refaire",
            "type": "checkbox",
            "label": "Nouveau tirage (ignorer le cache)",
            "default": False,
            "depends_on": "--consequences-ia",
            "description": "Refait les appels IA même si la réponse est en cache (la lecture varie d'un tirage "
                           "à l'autre). Payant."
        },
        {
            "flag": "--recit-ia",
            "type": "checkbox",
            "label": "Récit rédigé par l'IA (payant)",
            "default": False,
            "advanced": True,
            "description": "Remplace le récit construit par le script (gratuit) par un récit rédigé par l'IA, "
                           "un appel par scénario."
        }
    ],
    "yaml_files": [
        {"path": "et_si/hypotheses.yaml", "label": "et_si/hypotheses.yaml (hypothèses, mode d'emploi en tête)"},
        {"path": "documentation/need_action/et_si_dernier_lancement.md",
         "label": "Rapport du dernier lancement", "readonly": True}
    ],
    "gui_verified": False
}

REMPLACEMENTS_SIMU = [
    ("version", 'VERSION = "v7.6"', 'VERSION = "v7.7"'),
    ("copie du rapport pour le GUI",
     '''        out.write_text(md, encoding="utf-8")
        print(f"→ Rapport écrit : {out}", file=sys.stderr)''',
     '''        out.write_text(md, encoding="utf-8")
        # V7.7 : copie au nom fixe, affichée dans le panneau GUI.
        (REPORT_DIR / "et_si_dernier_lancement.md").write_text(md, encoding="utf-8")
        print(f"→ Rapport écrit : {out}", file=sys.stderr)'''),
]


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7.6 -> v7.7 (entrée GUI).")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon : aperçu)")
    args = ap.parse_args()
    for f in (SIMU, CONF):
        if not f.exists():
            sys.exit(f"✗ Fichier introuvable : {f}")
    simu, conf_txt = SIMU.read_text(encoding="utf-8"), CONF.read_text(encoding="utf-8")
    if 'VERSION = "v7.7"' in simu:
        sys.exit("✗ Patch déjà appliqué (v7.7). Rien à faire.")
    if 'VERSION = "v7.6"' not in simu:
        sys.exit("✗ La v7.6 n'est pas installée : appliquer d'abord patch_s27_v76.py.")
    erreurs = []
    print("simuler_et_si.py :")
    for libelle, ancien, nouveau in REMPLACEMENTS_SIMU:
        n = simu.count(ancien)
        if n != 1:
            erreurs.append(f"simuler_et_si.py — {libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        simu = simu.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    try:
        compile(simu, str(SIMU), "exec")
    except SyntaxError as e:
        erreurs.append(f"simuler_et_si.py ne compilerait pas : {e}")

    print("scripts_config.json :")
    try:
        conf = json.loads(conf_txt)
    except json.JSONDecodeError as e:
        sys.exit(f"✗ scripts_config.json illisible : {e}")
    if any(e.get("id") == ENTREE["id"] for e in conf):
        erreurs.append("scripts_config.json : une entrée `simuler_et_si` existe déjà")
    else:
        pos = next((i + 1 for i, e in enumerate(conf) if e.get("id") == "trace_injection"), None)
        if pos is None:
            pos = len(conf)
            print("  – entrée « trace_injection » introuvable : ajout en fin de liste")
        conf.insert(pos, ENTREE)
        print(f"  ✓ entrée `simuler_et_si` ajoutée (position {pos + 1}, section entites_nettoyage)")
    nouveau_conf = json.dumps(conf, ensure_ascii=False, indent=2)
    fin = "\n" if conf_txt.endswith("\n") else ""
    nouveau_conf += fin
    json.loads(nouveau_conf)

    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    for f, contenu in ((SIMU, simu), (CONF, nouveau_conf)):
        shutil.copy(f, f.with_name(f.name + ".bak_v77"))
        f.write_text(contenu, encoding="utf-8")
        print(f"→ écrit : {f.relative_to(VAULT_ROOT)} (sauvegarde {f.name}.bak_v77)")
    print("\nSimulateur passé en v7.7. Redémarrer Flask (scripts_config.json modifié).")


if __name__ == "__main__":
    main()
