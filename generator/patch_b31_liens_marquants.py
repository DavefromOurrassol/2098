#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B3.1 — « Couplages marquants » dans le prompt des articles.

Ajoute, pour chaque variable détaillée de build_variables_context (prompt_builder.py),
une ligne listant les variables les plus fortement couplées à elle dans CE scénario,
d'après coupling_intensity (fiche variable, par scénario). Aucun chiffre n'est
transmis au LLM (le sens du lien n'est pas précisé dans les fiches). Rien ne bouge
dans le moteur ni dans les niveaux.

Usage (depuis la racine du vault) :
    python3 generator/patch_b31_liens_marquants.py            # dry-run : montre l'ajout
    python3 generator/patch_b31_liens_marquants.py --apply    # applique (.bak_b31liens)
"""
import os
import py_compile
import shutil
import sys

CIBLE = os.path.join("generator", "prompt_builder.py")
SAUVEGARDE = CIBLE + ".bak_b31liens"

ANCRE = (
    "        if dynamics:\n"
    "            lines.append(\"- Dynamiques : {}\".format(\" | \".join(str(d) for d in dynamics[:3])))\n"
)

AJOUT = (
    "\n"
    "        # B3.1 — couplages marquants de cette variable dans CE scénario\n"
    "        # (coupling_intensity de la fiche variable : 2 à 4 liens, sens non\n"
    "        # précisé). Pas de chiffre transmis : l'ordre suffit.\n"
    "        coupling = state.get(\"coupling_intensity\") or {}\n"
    "        liens = sorted(\n"
    "            ((k, v) for k, v in coupling.items()\n"
    "             if k in VALID_VARS and k != var_slug),\n"
    "            key=lambda kv: -(kv[1] if isinstance(kv[1], (int, float)) else 0),\n"
    "        )\n"
    "        if liens:\n"
    "            lines.append(\n"
    "                \"- Couplages marquants dans ce scénario : {} (liens les plus \"\n"
    "                \"forts, sens non précisé ; à évoquer seulement si l'article \"\n"
    "                \"croise naturellement ces domaines)\".format(\n"
    "                    \", \".join(k for k, _ in liens[:4])))\n"
)


def main():
    appliquer = "--apply" in sys.argv
    if not os.path.isfile(CIBLE):
        print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(CIBLE))
        return 1
    with open(CIBLE, encoding="utf-8") as f:
        src = f.read()

    if "B3.1 — couplages marquants" in src:
        print("Déjà appliqué : rien à faire.")
        return 0

    n = src.count(ANCRE)
    if n != 1:
        print("ERREUR : ancre trouvée {} fois (attendu : 1). Rien modifié.".format(n))
        return 1

    nouveau = src.replace(ANCRE, ANCRE + AJOUT)
    print("Ajout prévu dans {} (après la ligne « Dynamiques ») :".format(CIBLE))
    print(AJOUT)

    if not appliquer:
        print("Dry-run : rien écrit. Relancer avec --apply pour appliquer.")
        return 0

    shutil.copy2(CIBLE, SAUVEGARDE)
    with open(CIBLE, "w", encoding="utf-8") as f:
        f.write(nouveau)
    try:
        py_compile.compile(CIBLE, doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(SAUVEGARDE, CIBLE)
        print("ERREUR de syntaxe, fichier restauré depuis la sauvegarde :\n{}".format(e))
        return 1
    print("Appliqué. Sauvegarde : {}. Syntaxe vérifiée.".format(SAUVEGARDE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
