#!/usr/bin/env python3
"""
scan_frontmatter_casse.py — diagnostic ponctuel, PAS un outil du pipeline
============================================================================

Scanne tous les .md de entites/, instances/, evenements/, event_instances/,
signaux_custom/ à la recherche de frontmatters YAML qui ne parsent pas
(yaml.safe_load() échoue) -- typiquement des valeurs non quotées contenant
un ": " (deux-points suivi d'espace), qui casse le parsing YAML puisque
c'est interprété comme un nouveau séparateur clé/valeur.

Ne modifie rien. Affiche : dossier, fichier, message d'erreur YAML.

USAGE
-----
    python3 scan_frontmatter_casse.py
"""

import os
import re
import yaml

VAULT_ROOT = os.path.dirname(os.path.abspath(__file__))
# Si lancé depuis generator/, remonter d'un niveau -- sinon, dossier courant.
if os.path.basename(VAULT_ROOT) == "generator":
    VAULT_ROOT = os.path.dirname(VAULT_ROOT)

DOSSIERS = ["entites", "instances", "evenements", "event_instances", "signaux_custom"]


def check_fichier(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not m:
        return "regex frontmatter ne matche pas (pas de bloc --- ... --- en début de fichier)"
    try:
        yaml.safe_load(m.group(1))
        return None
    except yaml.YAMLError as e:
        return str(e).replace("\n", " ")


def main():
    total_scannes = 0
    total_casses = 0
    for dossier in DOSSIERS:
        chemin = os.path.join(VAULT_ROOT, dossier)
        if not os.path.isdir(chemin):
            print(f"(dossier {dossier}/ introuvable, ignoré)")
            continue
        fichiers = sorted(f for f in os.listdir(chemin) if f.endswith(".md") and not f.startswith("_"))
        casses_dossier = []
        for fname in fichiers:
            total_scannes += 1
            erreur = check_fichier(os.path.join(chemin, fname))
            if erreur:
                total_casses += 1
                casses_dossier.append((fname, erreur))
        print(f"\n{dossier}/ -- {len(fichiers)} fichier(s) scanné(s), {len(casses_dossier)} cassé(s)")
        for fname, erreur in casses_dossier:
            print(f"  ✗ {fname}")
            print(f"      {erreur}")

    print(f"\n{'=' * 60}")
    print(f"TOTAL : {total_casses} fichier(s) cassé(s) sur {total_scannes} scanné(s)")


if __name__ == "__main__":
    main()
