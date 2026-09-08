#!/usr/bin/env python3
"""
audit_sujets_edition.py — Ourrassol 2098
==========================================

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) : liste
les articles générés pour un mois d'édition donné, avec leurs
métadonnées déjà disponibles (chapo, zone_principale, thématique,
ligne éditoriale -- champs P20, aucun nouveau champ article nécessaire),
et en regard les custom_events déjà injectés pour ce même mois.

CONTEXTE (chantier "Éditions datées", point 4, 2 septembre 2026)
------------------------------------------------------------------
Décidé avec David : la production des custom_events reste manuelle
(Option A) -- David identifie lui-même, dans les articles d'une
édition, ceux qui méritent de devenir des événements durables
(inject_custom_events.py, idée avec `edition_active: true`). Cet outil
ne fait AUCUN jugement de pertinence à sa place -- il se contente de
lui éviter de rouvrir chaque article un par un pour repérer ce qui
reste "matière brute" non injectée.

Usage :
    python3 audit_sujets_edition.py --scenario breakdown
        # édition active (state/editions.json) par défaut
    python3 audit_sujets_edition.py --scenario breakdown --annee 2098 --mois 8
        # édition précise, même si elle n'est plus l'édition active
"""
import argparse
import json
import os
import re

import yaml

from edition_utils import lire_edition_active, parser_date_fictive, MOIS_FR

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENT_INSTANCES_DIR = os.path.join(VAULT_ROOT, "event_instances")


def find_articles_dir(scenario):
    return os.path.join(VAULT_ROOT, "articles", scenario)


def parse_frontmatter(filepath):
    """Même approche que audit_metadonnees_publication.py -- yaml.safe_load()
    sur le bloc frontmatter, nécessaire pour les champs listes (tags)."""
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


def scanner_articles_du_mois(scenario, annee, mois):
    """Retourne la liste des articles de articles/{scenario}/ dont
    date_evenement tombe dans (annee, mois), triés par jour."""
    dossier = find_articles_dir(scenario)
    if not os.path.isdir(dossier):
        return []

    resultats = []
    for fname in sorted(os.listdir(dossier)):
        if not fname.endswith(".md") or fname.startswith("_"):
            continue
        filepath = os.path.join(dossier, fname)
        fm = parse_frontmatter(filepath)
        if not fm:
            continue
        parsed = parser_date_fictive(fm.get("date_evenement"))
        if not parsed:
            continue
        jour, mois_article, annee_article = parsed
        if (annee_article, mois_article) != (annee, mois):
            continue
        resultats.append({
            "fichier": fname,
            "jour": jour,
            "titre": fm.get("slug", fname.replace(".md", "")),
            "thematique": fm.get("thematique", "?"),
            "ligne_editoriale": fm.get("ligne_editoriale", "?"),
            "zone_principale": fm.get("zone_principale", "?"),
            "chapo": fm.get("chapo", ""),
            # Ajouté le 3 septembre 2026 (chantier "Injecter un événement
            # depuis un article") -- sert à pré-remplir acteurs_hint côté
            # GUI, pas utilisé par l'affichage console existant.
            "entites_citees": fm.get("entites_citees") or [],
        })
    resultats.sort(key=lambda a: a["jour"])
    return resultats


def scanner_custom_events_du_mois(scenario, annee, mois):
    """Retourne la liste des custom_events déjà injectés (event_instances/)
    pour ce scénario dont la date (float edition_date_to_float ou entier
    historique) tombe dans ce même mois. Un événement historique en année
    entière simple (pas de composante mois) n'a par construction aucune
    chance de matcher un mois précis -- il n'apparaîtra jamais ici, ce qui
    est le comportement voulu (seuls les événements liés à une édition
    précise sont pertinents pour cet audit)."""
    if not os.path.isdir(EVENT_INSTANCES_DIR):
        return []

    resultats = []
    suffixe = "_{}.md".format(scenario)
    for fname in sorted(os.listdir(EVENT_INSTANCES_DIR)):
        if not fname.endswith(suffixe):
            continue
        filepath = os.path.join(EVENT_INSTANCES_DIR, fname)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            m = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
            fm = yaml.safe_load(m.group(1)) or {} if m else {}
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(fm, dict):
            continue

        date_val = fm.get("date")
        if date_val is None:
            continue
        try:
            date_val = float(date_val)
        except (TypeError, ValueError):
            continue
        annee_ev = int(date_val)
        mois_ev = round((date_val - annee_ev) * 100)
        if (annee_ev, mois_ev) != (annee, mois):
            continue

        resultats.append({
            "fichier": fname,
            "nom": fm.get("name", fm.get("slug", fname.replace(".md", ""))),
            "date_label": fm.get("date_label", str(date_val)),
        })
    return resultats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True,
                         help="Scénario à auditer (ex. breakdown)")
    parser.add_argument("--annee", type=int, default=None,
                         help="Année du mois de parution (défaut : mois de parution actif)")
    parser.add_argument("--mois", type=int, default=None,
                         help="Mois de parution, 1-12 (défaut : mois de parution actif)")
    parser.add_argument("--json", action="store_true",
                         help="Sortie JSON sur une seule ligne finale (même convention "
                              "que extract_localisation.py --json), pour consommation "
                              "par app.py -- écran 'Injecter un événement depuis un "
                              "article' (3 septembre 2026). Désactive l'affichage console "
                              "normal.")
    args = parser.parse_args()

    def erreur(message):
        if args.json:
            print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
        else:
            print("[erreur] {}".format(message))
        raise SystemExit(1)

    if args.annee and args.mois:
        annee, mois = args.annee, args.mois
    elif args.annee or args.mois:
        erreur("--annee et --mois doivent être fournis ensemble.")
    else:
        edition_active = lire_edition_active()
        if not edition_active:
            erreur("Aucun mois de parution défini (state/editions.json absent/vide). "
                   "Précisez --annee et --mois explicitement, ou lancez d'abord "
                   "generate_series.py/generate_manual.py, ou definir_edition.py, pour en créer un.")
        annee, mois = edition_active["annee"], edition_active["mois"]

    articles = scanner_articles_du_mois(args.scenario, annee, mois)
    events = scanner_custom_events_du_mois(args.scenario, annee, mois)
    events_deja_vus = {e["fichier"] for e in events}

    if args.json:
        print(json.dumps({
            "ok": True,
            "scenario": args.scenario,
            "annee": annee,
            "mois": mois,
            "articles": articles,
            "custom_events": events,
        }, ensure_ascii=False))
        return

    print("=" * 60)
    print("MOIS DE PARUTION {} — {} {} ({} article(s))".format(
        args.scenario, MOIS_FR[mois], annee, len(articles)
    ))
    print("=" * 60)
    print()

    if not articles:
        print("Aucun article trouvé pour ce mois de parution dans articles/{}/.".format(args.scenario))
        print("(date_evenement absent, format non reconnu, ou aucun article généré ce mois-ci)")
        return

    for a in articles:
        print("[{} {}] {} ({})".format(a["jour"], MOIS_FR[mois], a["titre"], a["thematique"]))
        if a["chapo"]:
            print("  → chapo : {}".format(a["chapo"]))
        print("  → zone : {} | ligne : {}".format(a["zone_principale"], a["ligne_editoriale"]))
        print()

    print("-" * 60)
    print("Custom_events déjà injectés pour ce mois : {}".format(len(events)))
    print("-" * 60)
    if events:
        for e in events:
            print("  ✓ {} ({})".format(e["nom"], e["date_label"]))
    else:
        print("  Aucun -- rien n'a encore été capturé pour ce mois de parution.")


if __name__ == "__main__":
    main()
