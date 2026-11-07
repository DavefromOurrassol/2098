#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unification « et si ? » — étape 2b : simuler_et_si.py comprend `type: signal`.

Une hypothèse peut déclarer `type: signal` (défaut : evenement). Pour un signal :
force <= 10, 6 scénarios, une force par variable, date entière >= année en cours
(et <= 2097), durée entière, pas de rupture, pas de géographie ni de carte.
Le moteur le simule comme un choc de type « signal » (même demi-vie que le signal
injecté ensuite par inject_custom_signals.py).

    python3 generator/patch_u2b_simuler_signal.py            # dry-run
    python3 generator/patch_u2b_simuler_signal.py --apply    # applique (.bak_u2b)
"""
import py_compile
import shutil
import sys
from pathlib import Path

F = Path("generator/simuler_et_si.py")

EDITS = [
    ("DELTA_MAX_CONSEILLE = 25   # plafond d'un événement custom (inject_custom_events.py)\n",
     "DELTA_MAX_CONSEILLE = 25   # plafond d'un événement custom (inject_custom_events.py)\n"
     "DELTA_MAX_SIGNAL = 10      # plafond d'un signal (inject_custom_signals.py) -- U2b\n"),
    ("    impacts = []\n    for n, imp in enumerate(h.get(\"impacts\") or [], 1):\n",
     "    # U2b : type de l'élément (evenement | signal)\n"
     "    typ = str(h.get(\"type\") or \"evenement\").strip().lower()\n"
     "    if typ not in (\"evenement\", \"signal\"):\n"
     "        erreurs.append(f\"type {h.get('type')!r} inconnu (evenement | signal)\")\n"
     "        typ = \"evenement\"\n"
     "    est_signal = typ == \"signal\"\n"
     "    if est_signal:\n"
     "        if set(scen) != set(SCENARIOS):\n"
     "            erreurs.append(\"un signal couvre toujours les 6 scénarios (scenarios: tous)\")\n"
     "        if date is not None:\n"
     "            plancher = datetime.now().year\n"
     "            if date != int(date) or not plancher <= date <= 2097:\n"
     "                erreurs.append(f\"date {date:g} : un signal commence une année entière entre {plancher} et 2097\")\n"
     "\n"
     "    impacts = []\n    for n, imp in enumerate(h.get(\"impacts\") or [], 1):\n"),
    ("        if force > DELTA_MAX_CONSEILLE:\n",
     "        if est_signal and force > DELTA_MAX_SIGNAL:\n"
     "            erreurs.append(f\"impact {var} : delta_level {force:g} au-dessus du plafond d'un signal \"\n"
     "                           f\"({DELTA_MAX_SIGNAL}) ; au-delà, c'est un événement (type: evenement)\")\n"
     "        elif force > DELTA_MAX_CONSEILLE:\n"),
    ("        impacts.append({\"variable\": var, \"force\": force, \"polarites\": pols, \"duree\": duree})\n",
     "        if est_signal:\n"
     "            if duree != int(duree):\n"
     "                erreurs.append(f\"impact {var} : la durée d'un signal est un nombre entier d'années\")\n"
     "            if any(i[\"variable\"] == var for i in impacts):\n"
     "                erreurs.append(f\"impact {var} déclaré deux fois (un signal a UNE force par variable)\")\n"
     "        impacts.append({\"variable\": var, \"force\": force, \"polarites\": pols, \"duree\": duree})\n"),
    ("    if not carte and geo:\n",
     "    if est_signal:   # U2b : un signal n'a ni carte ni rupture\n"
     "        carte = False\n"
     "        if brut_geo:\n"
     "            erreurs.append(\"un signal n'a pas d'effet territorial : retirer `geographie`\")\n"
     "        if str(h.get(\"mode\") or \"choc\").strip().lower() == \"rupture\":\n"
     "            erreurs.append(\"un signal n'a pas de mode rupture (c'est un événement qui peut en avoir un)\")\n"
     "    if not carte and geo:\n"),
    ("        \"contraintes\": contraintes, \"carte\": carte, \"mode\": mode,\n",
     "        \"contraintes\": contraintes, \"carte\": carte, \"mode\": mode, \"type\": typ,\n"),
    ("        \"nom\": \"[hypothèse] \" + hyp[\"nom\"], \"type\": \"evenement\", \"variable\": imp[\"variable\"],\n"
     "        \"t0\": hyp[\"date\"], \"duree\": imp[\"duree\"], \"via_matrice\": hyp[\"via_matrice\"],\n",
     "        \"nom\": \"[hypothèse] \" + hyp[\"nom\"], \"type\": hyp.get(\"type\", \"evenement\"), \"variable\": imp[\"variable\"],\n"
     "        \"t0\": hyp[\"date\"],\n"
     "        \"duree\": (min(imp[\"duree\"], 2098 - hyp[\"date\"]) if hyp.get(\"type\") == \"signal\" else imp[\"duree\"]),\n"
     "        \"via_matrice\": hyp[\"via_matrice\"],\n"),
    ("    if not hyp.get(\"carte\", True):\n        L.append(\"- **Carte** : élément déclaré",
     "    if hyp.get(\"type\") == \"signal\":\n"
     "        L.append(\"- **Type** : signal (effet mineur, force <= {}, 6 scénarios, sans carte)\".format(DELTA_MAX_SIGNAL))\n"
     "    elif not hyp.get(\"carte\", True):\n        L.append(\"- **Carte** : élément déclaré"),
]


def main():
    if not F.is_file():
        print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(F))
        return 1
    src = F.read_text(encoding="utf-8")
    if "DELTA_MAX_SIGNAL" in src:
        print("Déjà appliqué : rien à faire.")
        return 0
    for i, (ancre, _) in enumerate(EDITS, 1):
        n = src.count(ancre)
        if n != 1:
            print("ERREUR : ancre n°{} trouvée {} fois (attendu : 1). Rien modifié.".format(i, n))
            return 1
    print("{} modifications prévues dans {}.".format(len(EDITS), F))
    if "--apply" not in sys.argv:
        print("Dry-run : rien écrit. Relancer avec --apply pour appliquer.")
        return 0
    new = src
    for ancre, rempl in EDITS:
        new = new.replace(ancre, rempl)
    shutil.copy2(F, str(F) + ".bak_u2b")
    F.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(F), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(str(F) + ".bak_u2b", F)
        print("ERREUR de syntaxe, fichier restauré :\n{}".format(e))
        return 1
    print("Appliqué (sauvegarde .bak_u2b). Syntaxe vérifiée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
