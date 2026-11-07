#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unification « et si ? » — étape 2d : et_si_injecter.py injecte aussi un SIGNAL adopté.

Selon le type du dossier : signaux_custom/queue.yaml + inject_custom_signals.py
--idea --json (au lieu de evenements_custom/queue.yaml + inject_custom_events.py).
Pas de liste ④ ni de « Sauter / Inclure » pour un signal (rien à appliquer à la
main : ni carte, ni zones). L'injection d'événement est inchangée.

    python3 generator/patch_u2d_injecter_signal.py            # dry-run
    python3 generator/patch_u2d_injecter_signal.py --apply    # applique (.bak_u2d)
"""
import py_compile
import shutil
import sys
from pathlib import Path

F = Path("generator/et_si_injecter.py")

EDITS = [
    ("    if a.plan:\n        # PATCH_S30_LISTE_SAUTS",
     "    typ = ed.type_dossier(ed.charger().get(hid))   # U2d : evenement | signal\n"
     "    nom_queue = \"signaux_custom/queue.yaml\" if typ == \"signal\" else \"evenements_custom/queue.yaml\"\n"
     "    if a.plan and typ == \"signal\":\n"
     "        print(f\"{hid} est un signal : pas de liste à l'étape ④ (ni carte, ni zones), rien à sauter.\")\n"
     "        return\n"
     "    if a.plan:\n        # PATCH_S30_LISTE_SAUTS"),
    ("    entrees = [x for x in ed._liste_yaml(ed.QUEUE_PATH, \"queue\")\n"
     "               if x.get(\"id\") == hid and x.get(\"source\") == f\"et_si_{hid}\"]\n"
     "    if len(entrees) != 1:\n"
     "        sys.exit(f\"✗ {len(entrees)} entrée(s) adoptée(s) {hid} dans evenements_custom/queue.yaml \"\n"
     "                 f\"(attendu : 1). Une entrée écrite à la main s'injecte par « Injecter des événements ».\")\n",
     "    entrees = [x for x in ed._liste_yaml(ed._chemin_queue(typ), \"queue\")\n"
     "               if x.get(\"id\") == hid and x.get(\"source\") == f\"et_si_{hid}\"]\n"
     "    if len(entrees) != 1:\n"
     "        sys.exit(f\"✗ {len(entrees)} entrée(s) adoptée(s) {hid} dans {nom_queue} \"\n"
     "                 f\"(attendu : 1). Une entrée écrite à la main s'injecte par le bouton d'injection de la queue.\")\n"),
    ("    _, ops = _plan(hid)\n    ecartees = _ecartees(ops, sauter, inclure)\n    if ecartees:\n        entree, retires",
     "    if typ == \"signal\":   # U2d : pas d'étape ④ pour un signal\n"
     "        ops, ecartees = [], set()\n"
     "    else:\n"
     "        _, ops = _plan(hid)\n"
     "        ecartees = _ecartees(ops, sauter, inclure)\n"
     "    if ecartees:\n        entree, retires"),
    ("    cmd = [sys.executable, str(GEN / \"inject_custom_events.py\"),\n"
     "           \"--idea\", json.dumps(entree, ensure_ascii=False, default=str)]\n",
     "    script = \"inject_custom_signals.py\" if typ == \"signal\" else \"inject_custom_events.py\"\n"
     "    cmd = [sys.executable, str(GEN / script),\n"
     "           \"--idea\", json.dumps(entree, ensure_ascii=False, default=str)]\n"
     "    if typ == \"signal\":\n"
     "        cmd.append(\"--json\")\n"),
    ("    if sauter or inclure:   # PATCH_S27_SAUTER : repris par défaut à l'étape ④\n",
     "    if typ == \"signal\":   # U2d : résultat JSON en dernière ligne\n"
     "        try:\n"
     "            res = json.loads(lignes[-1])\n"
     "        except (ValueError, IndexError):\n"
     "            res = {}\n"
     "        if res.get(\"status\") != \"injected\":\n"
     "            print(\"\\n⚠ signal non injecté en totalité (\"\n"
     "                  f\"réussies : {res.get('injected_variables') or 'aucune'}, \"\n"
     "                  f\"en échec : {res.get('failed_variables') or 'voir le motif'}\"\n"
     "                  + (f\" ; {res['reason']}\" if res.get(\"reason\") else \"\") + \"). \"\n"
     "                  \"Détail dans signaux_custom/needs_review.yaml.\")\n"
     "    if sauter or inclure:   # PATCH_S27_SAUTER : repris par défaut à l'étape ④\n"),
    ("    if ed._retirer_de_queue(hid):\n"
     "        print(f\"\\n✓ entrée {hid} retirée de evenements_custom/queue.yaml (sauvegarde queue.yaml.bak_et_si)\")\n",
     "    if ed._retirer_de_queue(hid, typ):\n"
     "        print(f\"\\n✓ entrée {hid} retirée de {nom_queue} (sauvegarde queue.yaml.bak_et_si)\")\n"),
]


def main():
    if not F.is_file():
        print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(F))
        return 1
    src = F.read_text(encoding="utf-8")
    if "U2d" in src:
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
    shutil.copy2(F, str(F) + ".bak_u2d")
    F.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(F), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(str(F) + ".bak_u2d", F)
        print("ERREUR de syntaxe, fichier restauré :\n{}".format(e))
        return 1
    print("Appliqué (sauvegarde .bak_u2d). Syntaxe vérifiée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
