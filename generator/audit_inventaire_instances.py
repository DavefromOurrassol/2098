#!/usr/bin/env python3
"""
audit_inventaire_instances.py — Ourrassol 2098
================================================

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) : scanne
TOUTES les instances du vault (dossier plat `instances/`, un fichier par
instance, nommé `{slug}_{scenario}.md`) et produit un inventaire complet,
fichier par fichier — même esprit que `audit_inventaire_articles.py`
(chantier "GUI Entités/Instances/Événements/Signaux", 7 septembre 2026),
mais sur un dossier plat non subdivisé par scénario : le filtrage par
scénario se fait donc sur le champ frontmatter `scenario`, pas sur
l'arborescence.

Pour chaque instance, résout aussi le nom de l'entité archétype parente
(`entite` → `entites/{entite}.md` → champ `name`) — nécessaire pour que
le panneau de détail GUI affiche l'archétype sans aller-retour réseau
supplémentaire. Résolution mise en cache en mémoire (un seul parsing par
archétype, même s'il a plusieurs instances) : ~200 entités attendues,
donc pas de souci de volume.

Champs capturés par instance : fichier, slug, name, entite,
entite_name, scenario, type_dans_scenario, role_dans_scenario,
impact_local, impact_systemique_global, trajectoire, annee_debut,
annee_fin, zone, transnationale, est_clandestin, generation.

USAGE
-----
    # Résumé seul (comptages), console
    python3 audit_inventaire_instances.py

    # Détail complet, un scénario
    python3 audit_inventaire_instances.py --scenario new_sustainability --detail

    # Export CSV (tous scénarios, une ligne par instance)
    python3 audit_inventaire_instances.py --csv inventaire.csv

    # Export JSON (pour usage GUI)
    python3 audit_inventaire_instances.py --json > inventaire.json
"""

import argparse
import csv
import json
import os
import re
import sys

import yaml

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCES_DIR = os.path.join(VAULT_ROOT, "instances")
ENTITES_DIR = os.path.join(VAULT_ROOT, "entites")

CHAMPS_CSV = [
    "fichier", "slug", "name", "entite", "entite_name", "scenario",
    "type_dans_scenario", "impact_local", "impact_systemique_global",
    "trajectoire", "annee_debut", "annee_fin", "zone", "transnationale",
    "est_clandestin", "generation",
]


def parse_frontmatter(filepath):
    """Même approche que audit_inventaire_articles.py --
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


_ENTITE_NAME_CACHE = {}


def resoudre_nom_entite(slug_entite):
    """Résout entite (slug archétype) -> name affiché, via
    entites/{slug}.md. Mis en cache (un seul parsing par archétype même
    partagé par plusieurs instances). Retourne None si le fichier
    archétype est introuvable ou illisible -- jamais une exception qui
    interromprait tout le scan."""
    if not slug_entite:
        return None
    if slug_entite in _ENTITE_NAME_CACHE:
        return _ENTITE_NAME_CACHE[slug_entite]
    filepath = os.path.join(ENTITES_DIR, f"{slug_entite}.md")
    nom = None
    if os.path.isfile(filepath):
        fm = parse_frontmatter(filepath)
        nom = fm.get("name") or None
    _ENTITE_NAME_CACHE[slug_entite] = nom
    return nom


def scanner_tout(scenario_filter=None):
    """Retourne (instances, non_lisibles) -- instances est une liste de
    dicts (un par fichier), non_lisibles est le nombre de fichiers .md
    trouvés mais dont le frontmatter n'a pas pu être parsé."""
    instances = []
    non_lisibles = 0

    if not os.path.isdir(INSTANCES_DIR):
        return instances, non_lisibles

    for fname in sorted(os.listdir(INSTANCES_DIR)):
        if not fname.endswith(".md") or fname.startswith("_"):
            continue
        filepath = os.path.join(INSTANCES_DIR, fname)
        fm = parse_frontmatter(filepath)
        if not fm:
            non_lisibles += 1
            continue

        scenario = fm.get("scenario", "inconnu")
        if scenario_filter and scenario != scenario_filter:
            continue

        localisation = fm.get("localisation") or {}
        zone = localisation.get("zone") if isinstance(localisation, dict) else None
        entite_slug = fm.get("entite", "") or ""

        instances.append({
            "fichier": fname,
            "slug": fm.get("slug", fname.replace(".md", "")),
            "name": fm.get("name", ""),
            "entite": entite_slug,
            "entite_name": resoudre_nom_entite(entite_slug),
            "scenario": scenario,
            "type_dans_scenario": fm.get("type_dans_scenario", "inconnu"),
            "role_dans_scenario": fm.get("role_dans_scenario", "") or "",
            "impact_local": fm.get("impact_local"),
            "impact_systemique_global": fm.get("impact_systemique_global"),
            "trajectoire": fm.get("trajectoire", "inconnu"),
            "annee_debut": fm.get("annee_debut"),
            "annee_fin": fm.get("annee_fin"),
            "zone": zone or "",
            # Transnationale : localisation.zone vide/null (cf. exemple réel
            # ARDS/eco_communalism, note "transnationale_sans_ancrage") --
            # champ dérivé pour permettre un filtre GUI direct sans que le
            # frontend ait à réinterpréter zone == "" lui-même.
            "transnationale": not bool(zone),
            "est_clandestin": bool(fm.get("est_clandestin", False)),
            "generation": fm.get("generation", "inconnu"),
        })

    instances.sort(key=lambda i: (i["scenario"], i["slug"]))
    return instances, non_lisibles


def calculer_resume(instances):
    resume = {
        "total": len(instances),
        "by_scenario": {},
        "by_type_dans_scenario": {},
        "by_trajectoire": {},
        "by_generation": {},
        "transnationales": 0,
        "clandestines": 0,
        "entite_introuvable": 0,
    }
    for i in instances:
        resume["by_scenario"][i["scenario"]] = resume["by_scenario"].get(i["scenario"], 0) + 1
        resume["by_type_dans_scenario"][i["type_dans_scenario"]] = (
            resume["by_type_dans_scenario"].get(i["type_dans_scenario"], 0) + 1)
        resume["by_trajectoire"][i["trajectoire"]] = resume["by_trajectoire"].get(i["trajectoire"], 0) + 1
        resume["by_generation"][i["generation"]] = resume["by_generation"].get(i["generation"], 0) + 1
        if i["transnationale"]:
            resume["transnationales"] += 1
        if i["est_clandestin"]:
            resume["clandestines"] += 1
        if i["entite"] and i["entite_name"] is None:
            resume["entite_introuvable"] += 1
    return resume


DOCUMENTATION_DIR = os.path.join(VAULT_ROOT, "documentation")
RAPPORT_MD_PATH = os.path.join(DOCUMENTATION_DIR, "inventaire_instances.md")


def generer_rapport_md(instances, resume, non_lisibles, scenario_filter):
    """Même logique que audit_inventaire_articles.py::generer_rapport_md
    -- toujours ÉCRASÉ à chaque génération, pas un document édité à la
    main."""
    lignes = []
    lignes.append("# Inventaire des instances{}".format(
        " — {}".format(scenario_filter) if scenario_filter else " — tous scénarios"))
    lignes.append("")
    lignes.append("*Généré automatiquement par `audit_inventaire_instances.py` — "
                   "ce fichier est réécrit à chaque génération, ne pas éditer à la main.*")
    lignes.append("")
    lignes.append("## Résumé")
    lignes.append("")
    lignes.append("- **Total** : {} instance(s)".format(resume["total"]))
    if non_lisibles:
        lignes.append("- {} fichier(s) .md illisible(s)/frontmatter invalide, ignoré(s)".format(non_lisibles))
    lignes.append("- Transnationales (sans zone) : {}".format(resume["transnationales"]))
    lignes.append("- Clandestines : {}".format(resume["clandestines"]))
    if resume["entite_introuvable"]:
        lignes.append("- ⚠ Entité archétype parente introuvable : {}".format(resume["entite_introuvable"]))
    lignes.append("")
    lignes.append("**Par scénario**")
    lignes.append("")
    for sc, n in sorted(resume["by_scenario"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(sc, n))
    lignes.append("")
    lignes.append("**Par type dans le scénario**")
    lignes.append("")
    for t, n in sorted(resume["by_type_dans_scenario"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(t, n))
    lignes.append("")
    lignes.append("**Par trajectoire**")
    lignes.append("")
    for t, n in sorted(resume["by_trajectoire"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(t, n))
    lignes.append("")
    lignes.append("## Détail")
    lignes.append("")
    lignes.append("| Scénario | Nom | Entité parente | Type | Trajectoire | Zone | Fichier |")
    lignes.append("|---|---|---|---|---|---|---|")
    for i in instances:
        zone_str = i["zone"] if i["zone"] else "(transnationale)"
        entite_str = i["entite_name"] or i["entite"] or "—"
        lignes.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            i["scenario"], i["name"], entite_str, i["type_dans_scenario"],
            i["trajectoire"], zone_str, i["fichier"]))
    lignes.append("")
    return "\n".join(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default=None,
                         help="Limiter à un scénario (défaut : tous).")
    parser.add_argument("--detail", action="store_true",
                         help="Affiche le détail instance par instance en plus du résumé "
                              "(console uniquement, sans --json).")
    parser.add_argument("--md", action="store_true",
                         help="Écrit le rapport complet en Markdown dans "
                              "documentation/inventaire_instances.md.")
    parser.add_argument("--csv", metavar="FICHIER", default=None,
                         help="Exporte aussi l'inventaire en CSV.")
    parser.add_argument("--json", action="store_true",
                         help="Affiche aussi un résumé JSON sur une seule ligne finale, "
                              "en plus de --md/--csv si demandés -- pour intégration GUI.")
    args = parser.parse_args()

    instances, non_lisibles = scanner_tout(args.scenario)
    resume = calculer_resume(instances)

    chemin_md = None
    if args.md:
        contenu = generer_rapport_md(instances, resume, non_lisibles, args.scenario)
        os.makedirs(DOCUMENTATION_DIR, exist_ok=True)
        with open(RAPPORT_MD_PATH, "w", encoding="utf-8") as f:
            f.write(contenu)
        chemin_md = RAPPORT_MD_PATH

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CHAMPS_CSV, extrasaction="ignore")
            writer.writeheader()
            for i in instances:
                writer.writerow(i)

    if args.json:
        print(json.dumps({
            "ok": True,
            "resume": resume,
            "instances": instances,
            "instances_illisibles": non_lisibles,
            "rapport_md": chemin_md,
            "rapport_csv": args.csv,
        }, ensure_ascii=False))
        return

    if args.md:
        print("Rapport Markdown écrit : {}".format(chemin_md))
    if args.csv:
        print("Export CSV : {}".format(args.csv))
    if args.md or args.csv:
        print("({} instances, {} illisibles ignorées)".format(len(instances), non_lisibles))

    print("=" * 60)
    print("INVENTAIRE INSTANCES{}".format(
        " — {}".format(args.scenario) if args.scenario else " — tous scénarios"))
    print("=" * 60)
    print("Total : {} instance(s)".format(resume["total"]))
    if non_lisibles:
        print("({} fichier(s) .md illisible(s)/frontmatter invalide, ignoré(s))".format(non_lisibles))
    print()
    print("Par scénario :")
    for sc, n in sorted(resume["by_scenario"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(sc, n))
    print()
    print("Par type dans le scénario :")
    for t, n in sorted(resume["by_type_dans_scenario"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(t, n))
    print()
    print("Transnationales (sans zone) : {}".format(resume["transnationales"]))
    print("Clandestines : {}".format(resume["clandestines"]))
    if resume["entite_introuvable"]:
        print("⚠ Entité archétype parente introuvable : {}".format(resume["entite_introuvable"]))

    if args.detail:
        print()
        print("-" * 60)
        print("DÉTAIL")
        print("-" * 60)
        for i in instances:
            zone_str = i["zone"] if i["zone"] else "(transnationale)"
            print("[{}] {} — {} (entité : {})".format(
                i["scenario"], i["name"], i["type_dans_scenario"],
                i["entite_name"] or i["entite"] or "?"))
            print("  zone : {} | trajectoire : {}".format(zone_str, i["trajectoire"]))
            print("  → {}".format(i["fichier"]))


if __name__ == "__main__":
    main()
