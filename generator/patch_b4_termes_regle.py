#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B4 — Brouillon de règle de lore (étape ⑤) : plusieurs termes par entité disparue.

Avant : `termes` = le nom de la fiche instance tel quel, sigle compris
(« Réseau des Citadelles du Sud-Pacifique (RCSP) ») : un article qui dit « Holdfast »,
« le RCSP » ou « le Réseau des Citadelles du Sud-Pacifique » échappait à l'audit.

Après : `termes` = nom sans la parenthèse du sigle ; sigle (l'audit respecte la casse
des termes en majuscules) ; nom de l'entité parente (entites/<entite>.md, ex. Holdfast).
Doublons ignorés (accents / casse), noms de moins de 4 lettres ignorés (sauf le sigle).

Touche deux fichiers :
  - generator/appliquer_et_si.py : nouvelle fonction termes_disparition() et rubrique
    « Règle de lore (brouillon) » du « reste à faire » ;
  - generator/et_si_main.py : brouillons_regles() (étape ⑤, GUI).

Usage (depuis la racine du vault) :
    python3 generator/patch_b4_termes_regle.py            # dry-run
    python3 generator/patch_b4_termes_regle.py --apply    # applique (.bak_b4termes)
"""
import py_compile
import shutil
import sys
from pathlib import Path

GEN = Path("generator")
F_AP = GEN / "appliquer_et_si.py"
F_MAIN = GEN / "et_si_main.py"
SUFFIXE = ".bak_b4termes"

HELPER = '''
_SIGLE_FIN = re.compile(r"^(.*?)\\s*\\(([A-Z][A-Z0-9&\\-]{1,9})\\)\\s*$")


def termes_disparition(nom, instance, sc):
    """B4 : termes de la règle de lore d'une entité disparue. Nom sans la parenthèse du
    sigle, sigle, nom de l'entité parente (entites/<entite>.md). Sans doublon."""
    termes = []

    def ajouter(t, mini=4):
        t = (t or "").strip()
        if len(t) >= mini and plie(t) not in {plie(x) for x in termes}:
            termes.append(t)

    m = _SIGLE_FIN.match(nom or "")
    ajouter(m.group(1) if m else nom, 1)
    if m:
        ajouter(m.group(2), 2)
    try:
        ent = (fm_de(instance) or {}).get("entite")
        p = VAULT / "entites" / f"{ent}.md" if ent else None
        if p is not None and p.exists():
            d = decoupe(p.read_text(encoding="utf-8"))
            ajouter((lire_fm(d[1]) if d else {}).get("name"))
    except Exception:
        pass
    return termes or [nom]

'''

# (fichier, ancre, remplacement)
EDITS = [
    (F_AP,
     "    return lire_fm(d[1]) if d else None\n\n\n# ---",
     "    return lire_fm(d[1]) if d else None\n" + HELPER + "\n# ---"),
    (F_AP,
     '                      f"  termes: [\\"{nom}\\"]", "  gravite: a_relire",\n',
     '                      "  termes: [" + ", ".join(json.dumps(t, ensure_ascii=False)\n'
     '                                              for t in termes_disparition(nom, o["instance"], sc)) + "]",\n'
     '                      "  gravite: a_relire",\n'),
    (F_MAIN,
     '"gravite": "a_relire", "termes": [nom],\n',
     '"gravite": "a_relire",\n'
     '                           "termes": ap.termes_disparition(nom, o["instance"], sc),\n'),
]


def main():
    appliquer = "--apply" in sys.argv
    sources = {}
    for f in (F_AP, F_MAIN):
        if not f.is_file():
            print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(f))
            return 1
        sources[f] = f.read_text(encoding="utf-8")
    if "def termes_disparition" in sources[F_AP]:
        print("Déjà appliqué : rien à faire.")
        return 0
    for f, ancre, rempl in EDITS:
        n = sources[f].count(ancre)
        if n != 1:
            print("ERREUR : ancre trouvée {} fois dans {} (attendu : 1). Rien modifié.\n---\n{}".format(n, f, ancre))
            return 1
        sources[f] = sources[f].replace(ancre, rempl)
    print("3 modifications prévues :")
    print("  - {} : fonction termes_disparition()".format(F_AP))
    print("  - {} : rubrique « Règle de lore (brouillon) »".format(F_AP))
    print("  - {} : brouillons_regles()".format(F_MAIN))
    if not appliquer:
        print("Dry-run : rien écrit. Relancer avec --apply pour appliquer.")
        return 0
    for f in (F_AP, F_MAIN):
        shutil.copy2(f, str(f) + SUFFIXE)
        f.write_text(sources[f], encoding="utf-8")
    try:
        for f in (F_AP, F_MAIN):
            py_compile.compile(str(f), doraise=True)
    except py_compile.PyCompileError as e:
        for f in (F_AP, F_MAIN):
            shutil.copy2(str(f) + SUFFIXE, f)
        print("ERREUR de syntaxe, fichiers restaurés :\n{}".format(e))
        return 1
    print("Appliqué (sauvegardes *{}). Syntaxe vérifiée.".format(SUFFIXE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
