#!/usr/bin/env python3
"""
audit_inventaire_event_instances.py — Ourrassol 2098
=======================================================

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) : scanne
TOUS les event_instances du vault (dossier plat `event_instances/`, un
fichier par instance d'événement, nommé `{slug}_{scenario}.md`) et
produit un inventaire complet, fichier par fichier — même modèle que
`audit_inventaire_instances.py` (chantier "GUI Entités/Instances/
Événements/Signaux", 7 septembre 2026), adapté au vocabulaire propre
aux événements (`archetype` au lieu de `entite`, `portee`/`impossible`/
`custom` au lieu de `impact_local`/`trajectoire`).

Pour chaque event_instance, résout aussi le nom de l'archétype
événementiel parent (`archetype` → `evenements/{archetype}.md` → champ
`name`) — même mécanisme de cache mémoire que côté Instances.

Champs capturés par event_instance : fichier, slug, name, archetype,
archetype_name, scenario, type_evenement, portee, date, date_label,
impossible, custom, description, zone, lieu, type_lieu.

USAGE
-----
    # Résumé seul (comptages), console
    python3 audit_inventaire_event_instances.py

    # Détail complet, un scénario
    python3 audit_inventaire_event_instances.py --scenario eco_communalism --detail

    # Export CSV (tous scénarios, une ligne par event_instance)
    python3 audit_inventaire_event_instances.py --csv inventaire.csv

    # Export JSON (pour usage GUI)
    python3 audit_inventaire_event_instances.py --json > inventaire.json
"""

import argparse
import csv
import json
import os
import re
import sys

import yaml

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENT_INSTANCES_DIR = os.path.join(VAULT_ROOT, "event_instances")
EVENEMENTS_DIR = os.path.join(VAULT_ROOT, "evenements")

CHAMPS_CSV = [
    "fichier", "slug", "name", "archetype", "archetype_name", "scenario",
    "type_evenement", "portee", "date", "date_label", "impossible",
    "custom", "description", "zone", "lieu", "type_lieu",
]


def parse_frontmatter(filepath):
    """Même approche que audit_inventaire_instances.py --
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


_ARCHETYPE_NAME_CACHE = {}


def resoudre_nom_archetype(slug_archetype):
    """Résout archetype (slug archétype événementiel) -> name affiché,
    via evenements/{slug}.md. Mis en cache -- un seul parsing par
    archétype même partagé par plusieurs event_instances (jusqu'à 6,
    une par scénario). Retourne None si introuvable/illisible."""
    if not slug_archetype:
        return None
    if slug_archetype in _ARCHETYPE_NAME_CACHE:
        return _ARCHETYPE_NAME_CACHE[slug_archetype]
    filepath = os.path.join(EVENEMENTS_DIR, f"{slug_archetype}.md")
    nom = None
    if os.path.isfile(filepath):
        fm = parse_frontmatter(filepath)
        nom = fm.get("name") or None
    _ARCHETYPE_NAME_CACHE[slug_archetype] = nom
    return nom


def scanner_tout(scenario_filter=None):
    """Retourne (event_instances, non_lisibles) -- event_instances est
    une liste de dicts (un par fichier), non_lisibles est le nombre de
    fichiers .md trouvés mais dont le frontmatter n'a pas pu être
    parsé."""
    event_instances = []
    non_lisibles = 0

    if not os.path.isdir(EVENT_INSTANCES_DIR):
        return event_instances, non_lisibles

    for fname in sorted(os.listdir(EVENT_INSTANCES_DIR)):
        if not fname.endswith(".md") or fname.startswith("_"):
            continue
        filepath = os.path.join(EVENT_INSTANCES_DIR, fname)
        fm = parse_frontmatter(filepath)
        if not fm:
            non_lisibles += 1
            continue

        scenario = fm.get("scenario", "inconnu")
        if scenario_filter and scenario != scenario_filter:
            continue

        localisation = fm.get("localisation") or {}
        zone = localisation.get("zone") if isinstance(localisation, dict) else None
        lieu = localisation.get("lieu") if isinstance(localisation, dict) else None
        type_lieu = localisation.get("type_lieu") if isinstance(localisation, dict) else None
        archetype_slug = fm.get("archetype", "") or ""

        event_instances.append({
            "fichier": fname,
            "slug": fm.get("slug", fname.replace(".md", "")),
            "name": fm.get("name", ""),
            "archetype": archetype_slug,
            "archetype_name": resoudre_nom_archetype(archetype_slug),
            "scenario": scenario,
            "type_evenement": fm.get("type_evenement", "inconnu"),
            "portee": fm.get("portee", "inconnu"),
            "date": fm.get("date"),
            "date_label": fm.get("date_label", "") or "",
            "impossible": bool(fm.get("impossible", False)),
            "custom": bool(fm.get("custom", False)),
            "description": fm.get("description", "") or "",
            "zone": zone or "",
            "lieu": lieu or "",
            "type_lieu": type_lieu or "",
        })

    event_instances.sort(key=lambda i: (i["scenario"], i["slug"]))
    return event_instances, non_lisibles


def calculer_resume(event_instances):
    resume = {
        "total": len(event_instances),
        "by_scenario": {},
        "by_type_evenement": {},
        "by_portee": {},
        "custom": 0,
        "canoniques": 0,
        "impossibles": 0,
        "archetype_introuvable": 0,
    }
    for i in event_instances:
        resume["by_scenario"][i["scenario"]] = resume["by_scenario"].get(i["scenario"], 0) + 1
        resume["by_type_evenement"][i["type_evenement"]] = (
            resume["by_type_evenement"].get(i["type_evenement"], 0) + 1)
        resume["by_portee"][i["portee"]] = resume["by_portee"].get(i["portee"], 0) + 1
        if i["custom"]:
            resume["custom"] += 1
        else:
            resume["canoniques"] += 1
        if i["impossible"]:
            resume["impossibles"] += 1
        if i["archetype"] and i["archetype_name"] is None:
            resume["archetype_introuvable"] += 1
    return resume


DOCUMENTATION_DIR = os.path.join(VAULT_ROOT, "documentation")
RAPPORT_MD_PATH = os.path.join(DOCUMENTATION_DIR, "inventaire_event_instances.md")


def generer_rapport_md(event_instances, resume, non_lisibles, scenario_filter):
    """Même logique que audit_inventaire_instances.py::generer_rapport_md
    -- toujours ÉCRASÉ à chaque génération, pas un document édité à la
    main."""
    lignes = []
    lignes.append("# Inventaire des event_instances{}".format(
        " — {}".format(scenario_filter) if scenario_filter else " — tous scénarios"))
    lignes.append("")
    lignes.append("*Généré automatiquement par `audit_inventaire_event_instances.py` — "
                   "ce fichier est réécrit à chaque génération, ne pas éditer à la main.*")
    lignes.append("")
    lignes.append("## Résumé")
    lignes.append("")
    lignes.append("- **Total** : {} event_instance(s)".format(resume["total"]))
    if non_lisibles:
        lignes.append("- {} fichier(s) .md illisible(s)/frontmatter invalide, ignoré(s)".format(non_lisibles))
    lignes.append("- Custom : {} | Canoniques : {}".format(resume["custom"], resume["canoniques"]))
    lignes.append("- Marqués `impossible` : {}".format(resume["impossibles"]))
    if resume["archetype_introuvable"]:
        lignes.append("- ⚠ Archétype événementiel parent introuvable : {}".format(resume["archetype_introuvable"]))
    lignes.append("")
    lignes.append("**Par scénario**")
    lignes.append("")
    for sc, n in sorted(resume["by_scenario"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(sc, n))
    lignes.append("")
    lignes.append("**Par portée**")
    lignes.append("")
    for p, n in sorted(resume["by_portee"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(p, n))
    lignes.append("")
    lignes.append("**Par type d'événement**")
    lignes.append("")
    for t, n in sorted(resume["by_type_evenement"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(t, n))
    lignes.append("")
    lignes.append("## Détail")
    lignes.append("")
    lignes.append("| Scénario | Nom | Archétype parent | Portée | Date | Custom | Fichier |")
    lignes.append("|---|---|---|---|---|---|---|")
    for i in event_instances:
        archetype_str = i["archetype_name"] or i["archetype"] or "—"
        date_str = i["date_label"] or (str(i["date"]) if i["date"] is not None else "?")
        lignes.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            i["scenario"], i["name"], archetype_str, i["portee"],
            date_str, "oui" if i["custom"] else "non", i["fichier"]))
    lignes.append("")
    return "\n".join(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default=None,
                         help="Limiter à un scénario (défaut : tous).")
    parser.add_argument("--detail", action="store_true",
                         help="Affiche le détail event_instance par event_instance en plus "
                              "du résumé (console uniquement, sans --json).")
    parser.add_argument("--md", action="store_true",
                         help="Écrit le rapport complet en Markdown dans "
                              "documentation/inventaire_event_instances.md.")
    parser.add_argument("--csv", metavar="FICHIER", default=None,
                         help="Exporte aussi l'inventaire en CSV.")
    parser.add_argument("--json", action="store_true",
                         help="Affiche aussi un résumé JSON sur une seule ligne finale, "
                              "en plus de --md/--csv si demandés -- pour intégration GUI.")
    args = parser.parse_args()

    event_instances, non_lisibles = scanner_tout(args.scenario)
    resume = calculer_resume(event_instances)

    chemin_md = None
    if args.md:
        contenu = generer_rapport_md(event_instances, resume, non_lisibles, args.scenario)
        os.makedirs(DOCUMENTATION_DIR, exist_ok=True)
        with open(RAPPORT_MD_PATH, "w", encoding="utf-8") as f:
            f.write(contenu)
        chemin_md = RAPPORT_MD_PATH

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CHAMPS_CSV, extrasaction="ignore")
            writer.writeheader()
            for i in event_instances:
                writer.writerow(i)

    if args.json:
        print(json.dumps({
            "ok": True,
            "resume": resume,
            "event_instances": event_instances,
            "event_instances_illisibles": non_lisibles,
            "rapport_md": chemin_md,
            "rapport_csv": args.csv,
        }, ensure_ascii=False))
        return

    if args.md:
        print("Rapport Markdown écrit : {}".format(chemin_md))
    if args.csv:
        print("Export CSV : {}".format(args.csv))
    if args.md or args.csv:
        print("({} event_instances, {} illisibles ignorées)".format(len(event_instances), non_lisibles))

    print("=" * 60)
    print("INVENTAIRE EVENT_INSTANCES{}".format(
        " — {}".format(args.scenario) if args.scenario else " — tous scénarios"))
    print("=" * 60)
    print("Total : {} event_instance(s)".format(resume["total"]))
    if non_lisibles:
        print("({} fichier(s) .md illisible(s)/frontmatter invalide, ignoré(s))".format(non_lisibles))
    print()
    print("Par scénario :")
    for sc, n in sorted(resume["by_scenario"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(sc, n))
    print()
    print("Par portée :")
    for p, n in sorted(resume["by_portee"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(p, n))
    print()
    print("Custom : {} | Canoniques : {}".format(resume["custom"], resume["canoniques"]))
    print("Marqués impossible : {}".format(resume["impossibles"]))
    if resume["archetype_introuvable"]:
        print("⚠ Archétype événementiel parent introuvable : {}".format(resume["archetype_introuvable"]))

    if args.detail:
        print()
        print("-" * 60)
        print("DÉTAIL")
        print("-" * 60)
        for i in event_instances:
            date_str = i["date_label"] or (str(i["date"]) if i["date"] is not None else "?")
            print("[{}] {} — {} (archétype : {})".format(
                i["scenario"], i["name"], i["portee"],
                i["archetype_name"] or i["archetype"] or "?"))
            print("  date : {} | custom : {} | impossible : {}".format(
                date_str, i["custom"], i["impossible"]))
            print("  → {}".format(i["fichier"]))


if __name__ == "__main__":
    main()
