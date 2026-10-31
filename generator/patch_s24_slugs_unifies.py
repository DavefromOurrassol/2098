#!/usr/bin/env python3
"""
patch_s24_slugs_unifies.py — S24, 31 oct 2026 (étape 1 : code)

Fait déléguer les 9 copies de slugify à generator/slugs.py (module commun,
qui translittère ø, æ, œ, ß, ł…). Chaque fonction garde son nom et sa
signature ; seul son corps devient « return _slugify_commun(...) ».
Le slugify() propre à export_revues.py (URL du site) n'est PAS touché ;
son slug_pipeline() (qui doit égaler api._slugify) l'est.

⚠ À appliquer avec l'étape 2 (migration) avant toute génération : entre les
deux, le code calcule les nouveaux slugs alors que les fichiers ont encore
les anciens.

Prérequis : generator/slugs.py présent.

Usage (depuis la racine du vault) :
  python3 generator/patch_s24_slugs_unifies.py           # aperçu
  python3 generator/patch_s24_slugs_unifies.py --apply   # applique (.bak_s24slug)
"""

import argparse
import ast
import os
import shutil
import sys

GEN = os.path.join(os.getcwd(), "generator")
IMPORT = "from slugs import slugify as _slugify_commun  # S24 (31 oct 2026) : slug commun\n"
CIBLES = [
    ("api.py", "_slugify"),
    ("audit_broken_slugs.py", "slugify_fixed"),
    ("audit_instances_manquantes.py", "slugify_fixed"),
    ("create_entities_and_instances.py", "slugify"),
    ("create_entity.py", "slugify"),
    ("export_revues.py", "slug_pipeline"),
    ("officialize_alliances.py", "slugify"),
    ("promote_ville.py", "slugify_fixed"),
    ("reattribuer_signatures.py", "_slugify"),
    ("rename_journalistes_retroactif.py", "slugify"),
]


def patcher(src, nom_fonction, fichier):
    if IMPORT in src:
        return None, "déjà appliqué"
    arbre = ast.parse(src)
    defs = [n for n in arbre.body if isinstance(n, ast.FunctionDef) and n.name == nom_fonction]
    if len(defs) != 1:
        raise ValueError("{}() trouvée {} fois au niveau module".format(nom_fonction, len(defs)))
    fn = defs[0]
    if not fn.args.args:
        raise ValueError("{}() sans argument".format(nom_fonction))
    arg = fn.args.args[0].arg

    imports = [n for n in arbre.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if not imports:
        raise ValueError("aucun import de niveau module")
    ligne_import = max(n.end_lineno for n in imports)  # insertion après la dernière
    if ligne_import >= fn.lineno:
        raise ValueError("dernier import après la fonction")

    lignes = src.splitlines(True)
    # en-tête (signature, éventuellement sur plusieurs lignes) jusqu'au « : » final
    i, entete = fn.lineno - 1, []
    while True:
        entete.append(lignes[i])
        if lignes[i].split("#")[0].rstrip().endswith(":"):
            break
        i += 1
    corps = ('    """S24 (31 oct 2026) : délègue à slugs.slugify (slug commun du projet,\n'
             '    translittère ø, æ, œ, ß, ł…)."""\n'
             "    return _slugify_commun({})\n".format(arg))
    lignes[fn.lineno - 1:fn.end_lineno] = entete + [corps]
    lignes.insert(ligne_import, IMPORT)
    nouveau = "".join(lignes)
    compile(nouveau, fichier, "exec")
    return nouveau, "OK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(os.path.join(GEN, "slugs.py")):
        sys.exit("generator/slugs.py absent : le déposer d'abord.")
    sys.path.insert(0, GEN)
    from slugs import slugify
    assert slugify("Bjørn Sørensen — Nœuds") == "bjorn_sorensen_noeuds"

    resultats, erreurs = {}, 0
    for fichier, fonction in CIBLES:
        chemin = os.path.join(GEN, fichier)
        if not os.path.exists(chemin):
            print("  ⚠ {:38} absent -- ignoré".format(fichier))
            continue
        try:
            nouveau, etat = patcher(open(chemin, encoding="utf-8").read(), fonction, chemin)
        except (ValueError, SyntaxError) as e:
            print("  ✗ {:38} {}".format(fichier, e))
            erreurs += 1
            continue
        print("  {} {:38} {}()".format("✓" if nouveau else "=", fichier, fonction) +
              ("" if nouveau else "  ({})".format(etat)))
        if nouveau:
            resultats[chemin] = nouveau

    if erreurs:
        sys.exit("\n{} erreur(s) : rien n'a été modifié.".format(erreurs))
    if not args.apply:
        print("\nAperçu seulement ({} fichier(s) à modifier). Relancer avec --apply.".format(len(resultats)))
        return
    for chemin, nouveau in resultats.items():
        shutil.copy2(chemin, chemin + ".bak_s24slug")
        open(chemin, "w", encoding="utf-8").write(nouveau)
    print("\nAppliqué à {} fichier(s) (sauvegardes .bak_s24slug).".format(len(resultats)))


if __name__ == "__main__":
    main()
