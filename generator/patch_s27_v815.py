#!/usr/bin/env python3
"""
patch_s27_v815.py — Ourrassol 2098 (S27, simulateur « et si ? » v8.15, 11 octobre 2026)

L'entrée d'injection commune du rapport transmet désormais à
inject_custom_events.py (patch_s27_injection_imposee.py) ce qui a été simulé :
  - impacts_imposes : forces, polarités par scénario et durées de montée ;
  - date_imposee : date de l'hypothèse ;
  - via_matrice_impose : propagation de l'hypothèse.
L'entrée couvre tous les scénarios de l'hypothèse (polarités connues pour
chacun), même si la simulation a été limitée par --scenario.
Mode rupture : seule la date est imposée (l'événement sert au récit, S19).
L'étape « Élément » de la liste devient une vérification, plus une comparaison.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v815.py            # aperçu, n'écrit rien
    python3 generator/patch_s27_v815.py --apply    # écrit (.bak_v815)

Refuse un second passage (VERSION déjà v8.15).
"""

import argparse
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "simuler_et_si.py"

REMPLACEMENTS = [
    ("version",
     'VERSION = "v8.14"',
     'VERSION = "v8.15"'),

    ("étape Élément",
     '''        _etape(E, "Élément", f"Comparer les forces injectées à celles simulées ({cibles})",
               f"event_instances/{hyp['id']}_{sc}.md, bloc impact_sur_variables ; "
               f"python3 generator/trace_injection.py --slug {hyp['id']} --type evenement --scenario {sc}",
               "l'IA de l'injection recalcule les forces : retoucher la fiche si elles s'écartent")
''',
     '''        # V8.15 : forces, date et propagation imposées à l'injection (impacts_imposes).
        _etape(E, "Élément", f"Vérifier que la fiche porte les forces simulées ({cibles})",
               f"event_instances/{hyp['id']}_{sc}.md, bloc impact_sur_variables ; "
               f"python3 generator/trace_injection.py --slug {hyp['id']} --type evenement --scenario {sc}",
               "imposées par l'entrée commune (impacts_imposes, date_imposee) : l'effet doit "
               "correspondre à cette simulation")
'''),

    ("entrée commune",
     '''    entree = {"id": hyp["id"], "description": hyp["description"] or hyp["nom"],
              "portee": "<locale | regionale | continentale | globale>" if geo else "globale",
              "date_approximative": int(hyp["date"]), "intensite": "<à choisir>",
              "persistance": hyp["persistance"] or "permanente", "scenarios": scen,
              "variables_hint": [i["variable"] for i in hyp["impacts"]],
              "variables_hint_count": len(hyp["impacts"]), "source": f"et_si_{hyp['id']}"}
    partiel = [sc for sc in hyp["scenarios"] if sc not in application]
''',
     '''    rupture = hyp.get("mode") == "rupture"
    partiel = [sc for sc in hyp["scenarios"] if sc not in application]
    if not rupture:
        scen = list(hyp["scenarios"])   # V8.15 : polarités connues pour tous les scénarios
    entree = {"id": hyp["id"], "description": hyp["description"] or hyp["nom"],
              "portee": "<locale | regionale | continentale | globale>" if geo else "globale",
              "date_approximative": int(hyp["date"]), "intensite": "<à choisir>",
              "persistance": hyp["persistance"] or "permanente", "scenarios": scen,
              "variables_hint": [i["variable"] for i in hyp["impacts"]],
              "variables_hint_count": len(hyp["impacts"]), "source": f"et_si_{hyp['id']}"}
    # V8.15 : ce qui a été simulé est imposé à l'injection (patch_s27_injection_imposee.py).
    def _nombre(x):
        return int(x) if float(x) == int(x) else x
    entree["date_imposee"] = _nombre(hyp["date"])
    trop_fort = []
    if not rupture:
        entree["impacts_imposes"] = {
            sc: [{"variable": i["variable"], "delta_level": _nombre(i["force"]),
                  "duree": _nombre(i["duree"]), "polarite": i["polarites"][sc]}
                 for i in hyp["impacts"] if sc in i["polarites"]]
            for sc in scen}
        entree["via_matrice_impose"] = bool(hyp["via_matrice"])
        trop_fort = [f"{i['variable']} ({i['force']:g})" for i in hyp["impacts"] if i["force"] > DELTA_MAX_CONSEILLE]
'''),

    ("texte de l'entrée",
     '''    return ["## Liste d'application — injection commune", "",
            ("⚠ Simulation limitée à " + ", ".join(scen) + " : ajouter à `scenarios` les autres scénarios "
             "de l'hypothèse (" + ", ".join(partiel) + ") avant d'injecter.\\n\\n" if partiel else "")
''',
     '''    return ["## Liste d'application — injection commune", "",
            ("⚠ Simulation limitée à " + ", ".join(sc for sc in scen if sc not in partiel)
             + " : l'entrée couvre aussi " + ", ".join(partiel) + ", non simulé(s) dans ce rapport ; "
             "les simuler avant d'injecter, ou les retirer de `scenarios` et de `impacts_imposes`.\\n\\n"
             if partiel and not rupture else "")
            + ("⚠ Simulation limitée à " + ", ".join(scen) + " : ajouter à `scenarios` les autres scénarios "
               "de l'hypothèse (" + ", ".join(partiel) + ") avant d'injecter.\\n\\n" if partiel and rupture else "")
            + ("⚠ Force au-dessus du plafond d'un événement custom (" + str(DELTA_MAX_CONSEILLE) + ") : "
               + ", ".join(trop_fort) + ". L'injection refusera l'entrée : baisser la force et resimuler.\\n\\n"
               if trop_fort else "")
'''),

    ("phrase sur les forces",
     '''            + ("Les forces et polarités simulées ne sont pas transmises : l'injection les recalcule ; "
               "les comparer ensuite scénario par scénario (étape « Élément »)." if hyp.get("mode") != "rupture" else ""), "",
''',
     '''            + ("Forces, polarités, durées, date et propagation de cette simulation sont imposées "
               "(`impacts_imposes`, `date_imposee`, `via_matrice_impose`) : l'IA de l'injection ne les "
               "recalcule pas, elle rédige seulement le récit." if not rupture
               else "Seule la date est imposée (`date_imposee`)."), "",
'''),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon aperçu)")
    args = ap.parse_args()
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable.")
    texte = CIBLE.read_text(encoding="utf-8")
    if 'VERSION = "v8.15"' in texte:
        sys.exit("✗ Patch déjà appliqué (v8.15) : rien n'est fait.")
    if 'VERSION = "v8.14"' not in texte:
        sys.exit("✗ Ce patch s'applique à la v8.14 du simulateur : rien n'est fait.")
    t = texte
    for nom, ancre, nouveau in REMPLACEMENTS:
        n = t.count(ancre)
        if n != 1:
            sys.exit(f"✗ Ancre « {nom} » trouvée {n} fois (attendu 1) : rien n'est écrit.")
        t = t.replace(ancre, nouveau)
    try:
        compile(t, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier modifié ne compilerait pas ({e}) : rien n'est écrit.")
    print(f"Modifications prêtes : {len(REMPLACEMENTS)} remplacements "
          f"({len(texte.splitlines())} → {len(t.splitlines())} lignes).")
    if not args.apply:
        print("Aperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_v815"))
    CIBLE.write_text(t, encoding="utf-8")
    print(f"✓ {CIBLE.name} modifié (sauvegarde : {CIBLE.name}.bak_v815).")


if __name__ == "__main__":
    main()
