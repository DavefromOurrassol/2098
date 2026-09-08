#!/usr/bin/env python3
"""
audit_inventaire_articles.py — Ourrassol 2098
================================================

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) : scanne
TOUS les articles de TOUS les scénarios (ou d'un seul si --scenario est
fourni) et produit un inventaire complet, fichier par fichier --
contrairement à /api/dashboard (routes_dashboard.py::_stats_articles),
qui scanne déjà tout le vault mais ne conserve que des compteurs
agrégés (total, by_scenario, by_ligne), jamais le détail par article.

Champs capturés par article : fichier, scenario, thematique,
ligne_editoriale, date_evenement, date_publication, slug, chapo,
zone_principale, entites_citees, evenements_cites,
evenements_cites_source.

USAGE
-----
    # Résumé seul (comptages), console
    python3 audit_inventaire_articles.py

    # Détail complet, un scénario
    python3 audit_inventaire_articles.py --scenario new_sustainability --detail

    # Export CSV (tous scénarios, une ligne par article)
    python3 audit_inventaire_articles.py --csv inventaire.csv

    # Export JSON (pour un futur usage GUI/autre script)
    python3 audit_inventaire_articles.py --json > inventaire.json
"""

import argparse
import csv
import json
import os
import re
import sys

import yaml

from edition_utils import parser_date_fictive, MOIS_FR

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(VAULT_ROOT, "articles")

CHAMPS_CSV = [
    "fichier", "scenario", "thematique", "ligne_editoriale",
    "date_evenement", "date_publication", "slug", "chapo",
    "zone_principale", "entites_citees", "evenements_cites",
    "evenements_cites_source", "journaliste_slug", "type_diffusion",
]


def parse_frontmatter(filepath):
    """Même approche que audit_sujets.py/audit_sujets_edition.py --
    yaml.safe_load() sur le bloc frontmatter."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not m:
        return {}
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return fm if isinstance(fm, dict) else {}


def _scenarios_disponibles():
    """Liste les sous-dossiers de articles/ -- pas de liste figée des
    scénarios ici (contrairement à d'autres scripts qui ont VALID_
    SCENARIOS importé de loader.py) : cet outil doit fonctionner même
    si un scénario existe sur disque sans être (encore) déclaré ailleurs."""
    if not os.path.isdir(ARTICLES_DIR):
        return []
    return sorted(
        d for d in os.listdir(ARTICLES_DIR)
        if os.path.isdir(os.path.join(ARTICLES_DIR, d))
    )


def scanner_tout(scenario_filter=None):
    """Retourne (articles, non_lisibles) -- articles est une liste de
    dicts (un par fichier), non_lisibles est le nombre de fichiers .md
    trouvés mais dont le frontmatter n'a pas pu être parsé (jamais
    silencieusement ignoré sans compte)."""
    scenarios = [scenario_filter] if scenario_filter else _scenarios_disponibles()
    articles = []
    non_lisibles = 0

    for scenario in scenarios:
        dossier = os.path.join(ARTICLES_DIR, scenario)
        if not os.path.isdir(dossier):
            continue
        for fname in sorted(os.listdir(dossier)):
            if not fname.endswith(".md") or fname.startswith("_"):
                continue
            filepath = os.path.join(dossier, fname)
            fm = parse_frontmatter(filepath)
            if not fm:
                non_lisibles += 1
                continue

            date_evenement = fm.get("date_evenement")
            parsed = parser_date_fictive(date_evenement) if date_evenement else None
            jour, mois, annee = parsed if parsed else (None, None, None)

            articles.append({
                "fichier": fname,
                "scenario": scenario,
                "thematique": fm.get("thematique", "inconnu"),
                "ligne_editoriale": fm.get("ligne_editoriale", "inconnu"),
                "date_evenement": date_evenement or "",
                "date_publication": fm.get("date_publication", ""),
                "slug": fm.get("slug", fname.replace(".md", "")),
                "chapo": fm.get("chapo", ""),
                "zone_principale": fm.get("zone_principale", "inconnu"),
                "entites_citees": fm.get("entites_citees") or [],
                "evenements_cites": fm.get("evenements_cites") or [],
                "evenements_cites_source": fm.get("evenements_cites_source", ""),
                # journaliste_slug/type_diffusion (7 septembre 2026, chantier
                # "Rédaction : détail journaliste") -- permet au GUI de
                # rapprocher un·e journaliste/orateur·rice de ses articles
                # sans avoir à répliquer la formule de slugification côté
                # backend (le rapprochement se fait côté client, par
                # normalisation, voir app.js::_redactionArticlesPourPersonne).
                "journaliste_slug": fm.get("journaliste_slug", "") or "",
                "type_diffusion": fm.get("type_diffusion", "ecrit"),
                "_jour": jour, "_mois": mois, "_annee": annee,
            })

    articles.sort(key=lambda a: (
        a["scenario"], a["_annee"] is None, a["_annee"] or 0,
        a["_mois"] or 0, a["_jour"] or 0
    ))
    return articles, non_lisibles


def calculer_resume(articles):
    resume = {
        "total": len(articles),
        "by_scenario": {},
        "by_thematique": {},
        "by_ligne_editoriale": {},
        "avec_evenement_force": 0,
        "date_non_reconnue": 0,
    }
    for a in articles:
        resume["by_scenario"][a["scenario"]] = resume["by_scenario"].get(a["scenario"], 0) + 1
        resume["by_thematique"][a["thematique"]] = resume["by_thematique"].get(a["thematique"], 0) + 1
        resume["by_ligne_editoriale"][a["ligne_editoriale"]] = (
            resume["by_ligne_editoriale"].get(a["ligne_editoriale"], 0) + 1)
        if a["evenements_cites"]:
            resume["avec_evenement_force"] += 1
        if a["_annee"] is None:
            resume["date_non_reconnue"] += 1
    return resume


DOCUMENTATION_DIR = os.path.join(VAULT_ROOT, "documentation")
RAPPORT_MD_PATH = os.path.join(DOCUMENTATION_DIR, "inventaire_articles.md")


def generer_rapport_md(articles, resume, non_lisibles, scenario_filter):
    """Construit un rapport Markdown complet (résumé + tableau détaillé) --
    natif au vault Obsidian, contrairement au CSV (format étranger,
    nécessite un tableur externe). Toujours ÉCRASÉ à chaque génération --
    c'est un instantané recalculé, pas un document édité à la main
    (même logique que _index.md généré par generate_series.py, mais
    couvrant tout le vault au lieu d'un seul batch)."""
    lignes = []
    lignes.append("# Inventaire des articles{}".format(
        " — {}".format(scenario_filter) if scenario_filter else " — tous scénarios"))
    lignes.append("")
    lignes.append("*Généré automatiquement par `audit_inventaire_articles.py` — "
                   "ce fichier est réécrit à chaque génération, ne pas éditer à la main.*")
    lignes.append("")
    lignes.append("## Résumé")
    lignes.append("")
    lignes.append("- **Total** : {} article(s)".format(resume["total"]))
    if non_lisibles:
        lignes.append("- {} fichier(s) .md illisible(s)/frontmatter invalide, ignoré(s)".format(non_lisibles))
    lignes.append("- Avec au moins un événement custom forcé (`evenements_cites`) : {}".format(
        resume["avec_evenement_force"]))
    lignes.append("- Date non reconnue : {}".format(resume["date_non_reconnue"]))
    lignes.append("")
    lignes.append("**Par scénario**")
    lignes.append("")
    for sc, n in sorted(resume["by_scenario"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(sc, n))
    lignes.append("")
    lignes.append("**Par ligne éditoriale**")
    lignes.append("")
    for l, n in sorted(resume["by_ligne_editoriale"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(l, n))
    lignes.append("")
    lignes.append("**Par thématique**")
    lignes.append("")
    for th, n in sorted(resume["by_thematique"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(th, n))
    lignes.append("")
    lignes.append("## Détail")
    lignes.append("")
    lignes.append("| Date | Scénario | Thématique | Ligne | Slug | Événements cités | Fichier |")
    lignes.append("|---|---|---|---|---|---|---|")
    for a in articles:
        date_str = ("{} {} {}".format(a["_jour"], MOIS_FR[a["_mois"]], a["_annee"])
                    if a["_annee"] is not None else "(non reconnue)")
        evenements = ", ".join(a["evenements_cites"]) if a["evenements_cites"] else "—"
        # Échappement minimal des barres verticales (séparateur de colonne
        # Markdown) dans les champs texte libre -- slug/fichier ne peuvent
        # pas en contenir (générés par le pipeline), donc seul evenements
        # (liste jointe) pourrait théoriquement en avoir un dans un slug
        # custom mal formé -- défensif, coûte rien.
        lignes.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            date_str, a["scenario"], a["thematique"], a["ligne_editoriale"],
            a["slug"], evenements.replace("|", "/"), a["fichier"]))
    lignes.append("")
    return "\n".join(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default=None,
                         help="Limiter à un scénario (défaut : tous).")
    parser.add_argument("--detail", action="store_true",
                         help="Affiche le détail article par article en plus du résumé "
                              "(console uniquement, sans --json).")
    parser.add_argument("--md", action="store_true",
                         help="Écrit le rapport complet en Markdown dans "
                              "documentation/inventaire_articles.md (natif au vault "
                              "Obsidian -- écrasé à chaque génération).")
    parser.add_argument("--csv", metavar="FICHIER", default=None,
                         help="Exporte aussi l'inventaire en CSV (format externe, pour "
                              "tableur -- optionnel, --md est le format recommandé pour "
                              "un usage dans le vault).")
    parser.add_argument("--json", action="store_true",
                         help="Affiche aussi un résumé JSON sur une seule ligne finale "
                              "(même convention que audit_sujets.py --json), en plus de "
                              "--md/--csv si demandés -- pour intégration GUI.")
    args = parser.parse_args()

    articles, non_lisibles = scanner_tout(args.scenario)
    resume = calculer_resume(articles)

    chemin_md = None
    if args.md:
        contenu = generer_rapport_md(articles, resume, non_lisibles, args.scenario)
        os.makedirs(DOCUMENTATION_DIR, exist_ok=True)
        with open(RAPPORT_MD_PATH, "w", encoding="utf-8") as f:
            f.write(contenu)
        chemin_md = RAPPORT_MD_PATH

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CHAMPS_CSV, extrasaction="ignore")
            writer.writeheader()
            for a in articles:
                row = dict(a)
                row["entites_citees"] = "|".join(a["entites_citees"])
                row["evenements_cites"] = "|".join(a["evenements_cites"])
                writer.writerow(row)

    if args.json:
        articles_json = []
        for a in articles:
            a2 = dict(a)
            a2["jour"] = a2.pop("_jour", None)
            a2["mois"] = a2.pop("_mois", None)
            a2["annee"] = a2.pop("_annee", None)
            articles_json.append(a2)
        print(json.dumps({
            "ok": True,
            "resume": resume,
            "articles": articles_json,
            "articles_illisibles": non_lisibles,
            "rapport_md": chemin_md,
            "rapport_csv": args.csv,
        }, ensure_ascii=False))
        return

    if args.md:
        print("Rapport Markdown écrit : {}".format(chemin_md))
    if args.csv:
        print("Export CSV : {}".format(args.csv))
    if args.md or args.csv:
        print("({} articles, {} illisibles ignorés)".format(len(articles), non_lisibles))

    print("=" * 60)
    print("INVENTAIRE ARTICLES{}".format(
        " — {}".format(args.scenario) if args.scenario else " — tous scénarios"))
    print("=" * 60)
    print("Total : {} article(s)".format(resume["total"]))
    if non_lisibles:
        print("({} fichier(s) .md illisible(s)/frontmatter invalide, ignoré(s))".format(non_lisibles))
    print()
    print("Par scénario :")
    for sc, n in sorted(resume["by_scenario"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(sc, n))
    print()
    print("Par ligne éditoriale :")
    for l, n in sorted(resume["by_ligne_editoriale"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(l, n))
    print()
    print("Par thématique :")
    for th, n in sorted(resume["by_thematique"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(th, n))
    print()
    print("Avec au moins un événement custom forcé (evenements_cites) : {}".format(
        resume["avec_evenement_force"]))
    print("Date non reconnue (date_evenement absente/format non standard) : {}".format(
        resume["date_non_reconnue"]))

    if args.detail:
        print()
        print("-" * 60)
        print("DÉTAIL")
        print("-" * 60)
        for a in articles:
            date_str = ("{} {} {}".format(a["_jour"], MOIS_FR[a["_mois"]], a["_annee"])
                        if a["_annee"] is not None else "(date non reconnue)")
            print("[{}] {} — {} ({})".format(date_str, a["scenario"], a["slug"], a["thematique"]))
            if a["evenements_cites"]:
                print("  evenements_cites : {}".format(", ".join(a["evenements_cites"])))
            print("  → {}".format(a["fichier"]))


if __name__ == "__main__":
    main()
