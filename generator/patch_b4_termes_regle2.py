#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B4 (suite) — termes_disparition() : le nom de l'entité parente passe aussi par le
retrait de la parenthèse du sigle (évite « Bloc Ressources Eurasiatique » +
« Bloc Ressources Eurasiatique (BRE) » en double).

    python3 generator/patch_b4_termes_regle2.py            # dry-run
    python3 generator/patch_b4_termes_regle2.py --apply    # applique (.bak_b4termes2)
"""
import py_compile
import shutil
import sys
from pathlib import Path

F = Path("generator/appliquer_et_si.py")
ANCRE = '            ajouter((lire_fm(d[1]) if d else {}).get("name"))\n'
NOUVEAU = (
    '            nom_ent = str((lire_fm(d[1]) if d else {}).get("name") or "")\n'
    '            me = _SIGLE_FIN.match(nom_ent)\n'
    '            ajouter(me.group(1) if me else nom_ent)\n'
    '            if me:\n'
    '                ajouter(me.group(2), 2)\n'
)


def main():
    if not F.is_file():
        print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(F))
        return 1
    src = F.read_text(encoding="utf-8")
    if "nom_ent = str(" in src:
        print("Déjà appliqué : rien à faire.")
        return 0
    if "def termes_disparition" not in src:
        print("ERREUR : appliquer d'abord patch_b4_termes_regle.py.")
        return 1
    n = src.count(ANCRE)
    if n != 1:
        print("ERREUR : ancre trouvée {} fois (attendu : 1). Rien modifié.".format(n))
        return 1
    print("1 modification prévue dans {} (nom de l'entité sans sigle + sigle de l'entité).".format(F))
    if "--apply" not in sys.argv:
        print("Dry-run : rien écrit. Relancer avec --apply pour appliquer.")
        return 0
    shutil.copy2(F, str(F) + ".bak_b4termes2")
    F.write_text(src.replace(ANCRE, NOUVEAU), encoding="utf-8")
    try:
        py_compile.compile(str(F), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(str(F) + ".bak_b4termes2", F)
        print("ERREUR de syntaxe, fichier restauré :\n{}".format(e))
        return 1
    print("Appliqué (sauvegarde .bak_b4termes2). Syntaxe vérifiée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
