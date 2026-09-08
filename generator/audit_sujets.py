#!/usr/bin/env python3
"""
audit_sujets.py — Ourrassol 2098
==================================

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) --
chantier "Suite narrative des événements", point B (5 septembre 2026).

Contrairement à audit_sujets_edition.py (qui liste TOUS les sujets d'un
MOIS donné), cet outil fait l'inverse : à partir d'UN sujet (un
événement custom ou une entité), il liste TOUTES ses occurrences à
travers TOUTES les dates du scénario -- pas seulement le mois de
parution actif. Sert à répondre à la question "où ce sujet a-t-il déjà
été traité, et est-ce que je risque de contredire un futur déjà écrit
si je le développe maintenant ?"

PORTÉE ACTUELLE (importante à lire avant utilisation)
------------------------------------------------------
- Entités (`--type entite`) : couvre tous les articles depuis le 21
  août 2026 (champ `entites_citees`, P20) -- fiable et complet sur ce
  qui a été généré depuis.
- Événements (`--type evenement`) : couvre UNIQUEMENT les articles
  générés en mode Forcer sur cet événement depuis le 5 septembre 2026
  (champ `evenements_cites`, chantier "suite narrative"). Le rattrapage
  rétroactif sur les 206 articles antérieurs a été tenté et ABANDONNÉ
  (voir detect_evenements_cites_retroactif.py) -- aucun article ancien
  ne développait un événement comme sujet central, seulement en
  toile de fond. Donc pour un événement jamais forcé depuis le 5
  septembre, cet outil affichera "aucune occurrence" même si
  l'événement est mentionné en passant ailleurs dans le vault -- ce
  n'est pas un bug, c'est la portée volontaire de ce chantier.

Usage :
    # Lister les événements custom disponibles pour un scénario (pour
    # trouver un slug sans fouiller registre_evenements.md à la main)
    python3 audit_sujets.py --scenario new_sustainability --list-evenements

    # Auditer un sujet précis, toutes dates confondues
    python3 audit_sujets.py --scenario new_sustainability \\
        --type evenement --slug accord_carbone_amazonie_blocs_new_sustainability

    python3 audit_sujets.py --scenario fortress_world \\
        --type entite --slug directive_kontinuum_fortress_world

    # Sortie JSON (même convention que audit_sujets_edition.py --json)
    python3 audit_sujets.py --scenario new_sustainability --type evenement \\
        --slug accord_carbone_amazonie_blocs_new_sustainability --json
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
    """Identique à audit_sujets_edition.py -- yaml.safe_load() sur le
    bloc frontmatter, nécessaire pour les champs listes."""
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


def _load_event_name(scenario, slug):
    """Va chercher le nom lisible d'un événement dans sa fiche instance,
    pour un affichage plus parlant que le seul slug. Retourne le slug
    lui-même si la fiche est introuvable ou illisible (jamais bloquant)."""
    filepath = os.path.join(EVENT_INSTANCES_DIR, "{}.md".format(slug))
    if not os.path.isfile(filepath):
        return slug
    fm = parse_frontmatter(filepath)
    return fm.get("name") or slug


def lister_evenements_du_scenario(scenario):
    """Liste tous les événements custom disponibles pour ce scénario,
    quelle que soit leur date -- sert de catalogue pour trouver un slug
    sans fouiller registre_evenements.md à la main (voir --list-evenements).

    Trié CHRONOLOGIQUEMENT sur le champ numérique `date` -- pas sur
    date_label, qui est un texte libre à granularité variable (saison,
    mois, année seule...) et donc non comparable directement. `date`
    est toujours numérique et toujours présent, c'est la seule base
    fiable pour un tri chronologique (trouvé le 5 septembre 2026 : le
    tri par nom de fichier donnait un ordre sans rapport avec la
    chronologie fictive)."""
    if not os.path.isdir(EVENT_INSTANCES_DIR):
        return []
    suffixe = "_{}.md".format(scenario)
    resultats = []
    for fname in sorted(os.listdir(EVENT_INSTANCES_DIR)):
        if not fname.endswith(suffixe):
            continue
        filepath = os.path.join(EVENT_INSTANCES_DIR, fname)
        fm = parse_frontmatter(filepath)
        if not fm:
            continue
        try:
            date_num = float(fm.get("date"))
        except (TypeError, ValueError):
            date_num = None
        resultats.append({
            "slug": fm.get("slug", fname[:-3]),
            "nom": fm.get("name", fname[:-3]),
            "date_label": fm.get("date_label", str(fm.get("date", "?"))),
            "_date_num": date_num,
        })
    # Les dates non numériques (rare, fiche malformée) sont reléguées en
    # fin de liste plutôt que de faire échouer le tri.
    resultats.sort(key=lambda e: (e["_date_num"] is None, e["_date_num"] or 0))
    for e in resultats:
        del e["_date_num"]
    return resultats


def auditer_sujet(scenario, type_sujet, slug):
    """Scanne TOUS les articles de articles/{scenario}/ (toutes dates)
    et retourne ceux qui citent ce sujet, triés chronologiquement selon
    la fiction (date_evenement), avec le nombre d'articles au frontmatter
    illisible/sans date reconnue (transparence -- jamais silencieux)."""
    dossier = find_articles_dir(scenario)
    champ = "evenements_cites" if type_sujet == "evenement" else "entites_citees"

    occurrences = []
    non_dates = 0
    if not os.path.isdir(dossier):
        return occurrences, non_dates

    for fname in sorted(os.listdir(dossier)):
        if not fname.endswith(".md") or fname.startswith("_"):
            continue
        filepath = os.path.join(dossier, fname)
        fm = parse_frontmatter(filepath)
        if not fm:
            continue
        if slug not in (fm.get(champ) or []):
            continue

        parsed = parser_date_fictive(fm.get("date_evenement"))
        if not parsed:
            non_dates += 1
            jour, mois_article, annee_article = None, None, None
        else:
            jour, mois_article, annee_article = parsed

        occurrences.append({
            "fichier": fname,
            "jour": jour,
            "mois": mois_article,
            "annee": annee_article,
            "titre": fm.get("slug", fname.replace(".md", "")),
            "thematique": fm.get("thematique", "?"),
            "chapo": fm.get("chapo", ""),
        })

    # Tri chronologique fictif -- les occurrences sans date reconnue
    # (rares, cf. non_dates) sont reléguées en fin de liste plutôt que
    # de faire échouer le tri.
    occurrences.sort(key=lambda o: (
        o["annee"] is None, o["annee"] or 0, o["mois"] or 0, o["jour"] or 0
    ))
    return occurrences, non_dates


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", required=True,
                         help="Scénario à auditer (ex. new_sustainability)")
    parser.add_argument("--type", choices=["evenement", "entite"], default=None,
                         help="Type de sujet à auditer (requis sauf avec --list-evenements)")
    parser.add_argument("--slug", default=None,
                         help="Slug du sujet à auditer (requis sauf avec --list-evenements)")
    parser.add_argument("--list-evenements", action="store_true",
                         help="Liste les événements custom disponibles pour ce scénario "
                              "(catalogue, pour trouver un slug) au lieu d'auditer un sujet précis.")
    parser.add_argument("--json", action="store_true",
                         help="Sortie JSON sur une seule ligne finale (même convention "
                              "que audit_sujets_edition.py --json).")
    args = parser.parse_args()

    def erreur(message):
        if args.json:
            print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
        else:
            print("[erreur] {}".format(message))
        raise SystemExit(1)

    if args.list_evenements:
        evenements = lister_evenements_du_scenario(args.scenario)
        if args.json:
            print(json.dumps({"ok": True, "scenario": args.scenario,
                               "evenements": evenements}, ensure_ascii=False))
            return
        print("=" * 60)
        print("ÉVÉNEMENTS CUSTOM DISPONIBLES — {} ({})".format(
            args.scenario, len(evenements)))
        print("=" * 60)
        if not evenements:
            print("Aucun événement custom trouvé pour ce scénario.")
            return
        for e in evenements:
            print("  {} — {}".format(e["date_label"], e["nom"]))
            print("    slug : {}".format(e["slug"]))
        return

    if not args.type or not args.slug:
        erreur("--type et --slug sont requis (sauf avec --list-evenements).")

    occurrences, non_dates = auditer_sujet(args.scenario, args.type, args.slug)

    edition_active = lire_edition_active()
    annee_active = edition_active["annee"] if edition_active else None
    mois_active = edition_active["mois"] if edition_active else None

    for o in occurrences:
        if annee_active is not None and o["annee"] is not None:
            o["posterieur_edition_active"] = (o["annee"], o["mois"]) > (annee_active, mois_active)
        else:
            o["posterieur_edition_active"] = None  # indéterminable

    if args.json:
        print(json.dumps({
            "ok": True,
            "scenario": args.scenario,
            "type": args.type,
            "slug": args.slug,
            "edition_active": edition_active,
            "occurrences": occurrences,
            "articles_sans_date_reconnue": non_dates,
        }, ensure_ascii=False))
        return

    nom_affiche = _load_event_name(args.scenario, args.slug) if args.type == "evenement" else args.slug

    print("=" * 60)
    print("AUDIT — {} ({})".format(nom_affiche, args.type))
    print("Scénario : {} | {} occurrence(s)".format(args.scenario, len(occurrences)))
    if edition_active:
        print("Mois de parution actif : {} {}".format(MOIS_FR[mois_active], annee_active))
    else:
        print("Mois de parution actif : aucun défini (aucun signal 'postérieur' possible)")
    print("=" * 60)
    print()

    if not occurrences:
        if args.type == "evenement":
            print("Aucune occurrence -- rappel : seuls les articles générés en mode Forcer "
                  "sur cet événement depuis le 5 septembre 2026 apparaîtront ici (voir portée "
                  "en tête de ce script). Un événement jamais forcé n'aura jamais d'entrée, "
                  "même s'il est mentionné en passant ailleurs dans le vault.")
        else:
            print("Aucune occurrence trouvée pour cette entité dans articles/{}/.".format(
                args.scenario))
        return

    for o in occurrences:
        date_str = ("{} {} {}".format(o["jour"], MOIS_FR[o["mois"]], o["annee"])
                    if o["annee"] is not None else "(date non reconnue)")
        flag = ""
        if o["posterieur_edition_active"] is True:
            flag = "  ⚠ POSTÉRIEUR AU MOIS DE PARUTION ACTIF -- risque d'incohérence temporelle"
        print("[{}] {} ({}){}".format(date_str, o["titre"], o["thematique"], flag))
        if o["chapo"]:
            print("  → chapo : {}".format(o["chapo"]))
        print("  → fichier : {}".format(o["fichier"]))
        print()

    if non_dates:
        print("-" * 60)
        print("({} article(s) citant ce sujet ignoré(s) -- date_evenement absente ou "
              "format non reconnu)".format(non_dates))


if __name__ == "__main__":
    main()
