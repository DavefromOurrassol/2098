#!/usr/bin/env python3
"""
audit_metadonnees_publication.py — Ourrassol 2098
====================================================

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) : mesure
sur l'ensemble du vault le taux réel d'articles avec chapo/tags/
image_prompt vides -- le bloc ===METADONNEES_PUBLICATION=== que le LLM
doit produire en fin de génération (voir prompt_builder.py,
build_journalistic_brief() ; extraction dans api.py,
_extract_publication_metadata()).

CONTEXTE (30 août 2026, backlog point 2)
-----------------------------------------------------------------
Le seul chiffre disponible jusqu'ici (~7%, 3/41) vient d'un échantillon
repéré EN MARGE d'un autre chantier (batch de volume P25, 22 août) --
pas d'une mesure systématique. Deux articles sur ces trois partageaient
la thématique `religion_spiritualite`, hypothèse non tranchée (signal
réel ou coïncidence sur un tout petit échantillon). Ce script mesure le
vrai taux sur tout le vault, avec ventilation par thématique/scénario/
type_diffusion, sur le même modèle qu'audit_longueur_articles.py
(9 août 2026) -- même séquence : mesurer avant de corriger.

Différence de parsing avec audit_longueur_articles.py : ce script utilise
`yaml.safe_load()` sur le bloc frontmatter plutôt que le parseur ligne à
ligne de l'audit longueur, volontairement, car `tags` est une liste YAML
multi-lignes (`tags:\n  - x\n  - y`) -- un parseur ligne à ligne qui
ignore les lignes commençant par un espace ou un tiret (comme celui de
l'audit longueur) ne peut jamais la lire correctement, il ne verrait que
la clé `tags:` avec une valeur vide, qu'elle soit remplie ou non.

Usage :
    python3 audit_metadonnees_publication.py                  # articles/ par défaut
    python3 audit_metadonnees_publication.py --dossier /chemin/vers/articles
"""
import argparse
import os
import re
from collections import Counter

import yaml


def find_default_articles_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "articles")


def parse_frontmatter(filepath):
    """Contrairement au parseur ligne à ligne d'audit_longueur_articles.py,
    utilise un vrai yaml.safe_load() -- nécessaire pour lire correctement
    `tags` (liste multi-lignes), voir docstring du module."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not m:
        return {}
    fm_text = m.group(1)
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return {}
    return fm if isinstance(fm, dict) else {}


def est_vide(valeur):
    """Vide = absent, chaîne vide/blanche, ou liste vide -- couvre les 3
    formes possibles (chapo/image_prompt en chaîne, tags en liste)."""
    if valeur is None:
        return True
    if isinstance(valeur, str):
        return valeur.strip() == ""
    if isinstance(valeur, list):
        return len(valeur) == 0
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dossier", type=str, default=find_default_articles_dir(),
        help="Dossier articles/ à scanner (défaut : articles/ du vault courant)"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.dossier):
        print("Dossier introuvable : {}".format(args.dossier))
        print("Relance avec : python3 {} --dossier /chemin/vers/vault/articles".format(__file__))
        raise SystemExit(1)

    # Récursif, même raison qu'audit_longueur_articles.py depuis le 10
    # août 2026 -- articles/{scenario}/, pas seulement la racine.
    # _index.md ignoré (pas un article).
    md_files = []
    for root, _dirs, files in os.walk(args.dossier):
        for f in sorted(files):
            if f.endswith(".md") and not f.startswith("_"):
                md_files.append(os.path.relpath(os.path.join(root, f), args.dossier))
    md_files.sort()

    total = 0
    au_moins_un_vide = 0
    chapo_vide = 0
    tags_vide = 0
    image_prompt_vide = 0
    bloc_entierement_absent = 0  # les 3 vides en même temps -- signe que
                                  # ===METADONNEES_PUBLICATION=== n'a
                                  # jamais été trouvé du tout par
                                  # _extract_publication_metadata(),
                                  # distinct d'un champ isolé manquant
                                  # dans un bloc par ailleurs présent.

    thematique_total = Counter()
    thematique_vide = Counter()
    scenario_total = Counter()
    scenario_vide = Counter()
    type_diffusion_total = Counter()
    type_diffusion_vide = Counter()

    exemples_vides = []

    for fname in md_files:
        filepath = os.path.join(args.dossier, fname)
        fm = parse_frontmatter(filepath)
        if not fm:
            continue
        total += 1

        thematique = fm.get("thematique", "?")
        scenario = fm.get("scenario", "?")
        type_diffusion = fm.get("type_diffusion", "ecrit")

        thematique_total[thematique] += 1
        scenario_total[scenario] += 1
        type_diffusion_total[type_diffusion] += 1

        c_vide = est_vide(fm.get("chapo"))
        t_vide = est_vide(fm.get("tags"))
        i_vide = est_vide(fm.get("image_prompt"))

        if c_vide:
            chapo_vide += 1
        if t_vide:
            tags_vide += 1
        if i_vide:
            image_prompt_vide += 1

        if c_vide or t_vide or i_vide:
            au_moins_un_vide += 1
            thematique_vide[thematique] += 1
            scenario_vide[scenario] += 1
            type_diffusion_vide[type_diffusion] += 1
            exemples_vides.append((fname, thematique, scenario, type_diffusion,
                                    c_vide, t_vide, i_vide))

        if c_vide and t_vide and i_vide:
            bloc_entierement_absent += 1

    print("=" * 60)
    print("AUDIT métadonnées publication — {} fichiers scannés".format(total))
    print("=" * 60)
    print()

    if not total:
        print("Aucun article analysable trouvé dans {}".format(args.dossier))
        return

    print("-- Taux global (au moins un des trois champs vide) --")
    print("  {} / {} articles ({:.1f}%)".format(
        au_moins_un_vide, total, 100 * au_moins_un_vide / total))
    print()

    print("-- Détail par champ --")
    print("  chapo vide        : {} ({:.1f}%)".format(chapo_vide, 100 * chapo_vide / total))
    print("  tags vide         : {} ({:.1f}%)".format(tags_vide, 100 * tags_vide / total))
    print("  image_prompt vide : {} ({:.1f}%)".format(image_prompt_vide, 100 * image_prompt_vide / total))
    print()

    print("-- Bloc ===METADONNEES_PUBLICATION=== probablement entièrement absent --")
    print("   (les 3 champs vides simultanément -- distinct d'un champ isolé)")
    print("  {} / {} articles ({:.1f}%)".format(
        bloc_entierement_absent, total, 100 * bloc_entierement_absent / total))
    print()

    if exemples_vides:
        print("-- Détail des articles concernés --")
        for fname, th, sc, td, c, t, i in exemples_vides:
            manquants = ",".join(
                n for n, v in (("chapo", c), ("tags", t), ("image_prompt", i)) if v
            )
            print("  {} : thematique='{}' scenario='{}' type_diffusion='{}' — manquant(s) : {}".format(
                fname, th, sc, td, manquants))
        print()

    print("-- Taux de vide par thématique (trie par taux décroissant, min 2 articles) --")
    lignes = []
    for th, tot in thematique_total.items():
        if tot < 2:
            continue
        vide = thematique_vide.get(th, 0)
        lignes.append((th, vide, tot, 100 * vide / tot))
    for th, vide, tot, taux in sorted(lignes, key=lambda x: -x[3]):
        print("  {} : {}/{} ({:.1f}%)".format(th, vide, tot, taux))
    print()

    print("-- Taux de vide par scénario --")
    for sc, tot in scenario_total.most_common():
        vide = scenario_vide.get(sc, 0)
        print("  {} : {}/{} ({:.1f}%)".format(sc, vide, tot, 100 * vide / tot if tot else 0))
    print()

    print("-- Taux de vide par type_diffusion --")
    for td, tot in type_diffusion_total.most_common():
        vide = type_diffusion_vide.get(td, 0)
        print("  {} : {}/{} ({:.1f}%)".format(td, vide, tot, 100 * vide / tot if tot else 0))


if __name__ == "__main__":
    main()
