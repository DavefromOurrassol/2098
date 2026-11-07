#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unification « et si ? » — étape 2e (2/2) : et_si_statut.py (panneau « Parcours ») connaît les signaux.

Pour un signal : pas d'alerte « passe exhaustive » ni « fichier d'opérations » (rien à appliquer :
ni carte, ni zones), alerte d'injection renvoyant à signaux_custom/needs_review.yaml, et une fois
injecté le parcours est terminé (étape 6 : la frise affiche les 5 étapes faites). Le champ
« type » est ajouté à la sortie JSON. Aucun changement pour un événement.

    python3 generator/patch_u2e2_statut_signal.py            # dry-run
    python3 generator/patch_u2e2_statut_signal.py --apply    # applique (.bak_u2e2)
"""
import py_compile
import shutil
import sys
from pathlib import Path

F = Path("generator/et_si_statut.py")

EDITS = [
    ("    st = ed.statut(hid, d)\n    ops = APP_DIR",
     "    st = ed.statut(hid, d)\n    typ = ed.type_dossier(d)   # U2e : evenement | signal\n    ops = APP_DIR"),
    ("        etape = 5 if applique else 4\n",
     "        etape = 6 if typ == \"signal\" else (5 if applique else 4)   # U2e : un signal n'a ni ④ ni ⑤\n"),
    ("        alertes.append(f\"statut « {st} » : voir evenements_custom/needs_review.yaml, ou annuler la décision\")",
     "        alertes.append(f\"statut « {st} » : voir \"\n"
     "                       + (\"signaux_custom\" if typ == \"signal\" else \"evenements_custom\")\n"
     "                       + \"/needs_review.yaml, ou annuler la décision\")"),
    ("        if not sim.get(\"passe\") and etape <= 2:\n",
     "        if not sim.get(\"passe\") and etape <= 2 and typ != \"signal\":\n"),
    ("        if not ops.exists() and etape <= 4 and not applique:\n",
     "        if not ops.exists() and etape <= 4 and not applique and typ != \"signal\":\n"),
    ("        \"id\": hid, \"statut\": st, \"etape\": etape,",
     "        \"id\": hid, \"type\": typ, \"statut\": st, \"etape\": etape,"),
]


def main():
    if not F.is_file():
        print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(F))
        return 1
    src = F.read_text(encoding="utf-8")
    if "U2e" in src:
        print("Déjà appliqué : rien à faire.")
        return 0
    if "def type_dossier" not in (F.parent / "et_si_dossiers.py").read_text(encoding="utf-8"):
        print("ERREUR : appliquer d'abord patch_u2c_adopter_signal.py.")
        return 1
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
    shutil.copy2(F, str(F) + ".bak_u2e2")
    F.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(F), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(str(F) + ".bak_u2e2", F)
        print("ERREUR de syntaxe, fichier restauré :\n{}".format(e))
        return 1
    print("Appliqué (sauvegarde .bak_u2e2). Syntaxe vérifiée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
