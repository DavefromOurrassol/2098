#!/usr/bin/env python3
"""
audit_inventaire_signaux.py — Ourrassol 2098
================================================

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) : scanne
TOUS les signaux faibles du vault (dossier plat `signaux_custom/`) et
produit un inventaire complet -- dernier des 3 types du chantier "GUI
Entités/Instances/Événements/Signaux" (7 septembre 2026), le plus
différent structurellement des deux précédents.

Particularité par rapport à audit_inventaire_instances.py/audit_
inventaire_event_instances.py : le frontmatter d'un signal N'A PAS de
champ `scenario` -- le rattachement aux scénarios vit dans un bloc YAML
imbriqué au milieu du CORPS Markdown, sous le titre `## Trajectoire
injectée` (clé `signal_to_state[].scenarios`, une entrée par scénario
narratif). Une section `## Impact chiffré` (clé `impact_sur_variables
[].scenarios`, deltas numériques annee_injection/duree/delta_level/
polarite) existe sur CERTAINS signaux seulement -- optionnelle,
contrairement à Trajectoire injectée qui est la source fiable pour
filtrer par scénario côté GUI (vérifié sur 2 exemples réels le 7
septembre : un signal sans aucune section Impact chiffré, un autre avec).

Champs capturés par signal : fichier, slug, source, categorie,
variables_cibles, statut, description (texte de la section "Idée
source"), scenarios (dérivé de Trajectoire injectée, union des clés sur
toutes les entrées signal_to_state), trajectoire (détail complet par
entrée -- une par variable cible -- de evolution/date_bascule/
evenement_cle par scénario, pour affichage GUI ; pas exporté en CSV, structure
imbriquée), a_impact_chiffre (bool), entrees_trajectoire (nombre
d'entrées signal_to_state -- NORMAL d'en avoir plusieurs :
inject_custom_signals.py écrit une entrée par variable cible du signal,
avec une trajectoire narrative distincte par variable (confirmé en
lisant process_idea()/write_custom_fiche(), 7 septembre 2026 -- PAS un
artefact de duplication comme d'abord supposé). Le signal réel à
surveiller est plutôt un ÉCART entre entrees_trajectoire et le nombre de
variables_cibles : ça signalerait une injection partielle (une variable
serait passée en needs_review côté pipeline sans que la fiche
signaux_custom/ le reflète autrement).

USAGE
-----
    # Résumé seul (comptages), console
    python3 audit_inventaire_signaux.py

    # Détail complet, un scénario
    python3 audit_inventaire_signaux.py --scenario eco_communalism --detail

    # Export CSV (une ligne par signal)
    python3 audit_inventaire_signaux.py --csv inventaire.csv

    # Export JSON (pour usage GUI)
    python3 audit_inventaire_signaux.py --json > inventaire.json
"""

import argparse
import csv
import json
import os
import re
import sys

import yaml

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNAUX_DIR = os.path.join(VAULT_ROOT, "signaux_custom")

# README.md documente le dossier, ce n'est pas un fichier de données --
# exclu explicitement (pas seulement par préfixe "_", comme pour les
# autres types), même motif que le faux signal repéré par scan_
# frontmatter_casse.py le 7 septembre.
FICHIERS_EXCLUS = {"README.md"}

CHAMPS_CSV = [
    "fichier", "slug", "source", "categorie", "variables_cibles",
    "statut", "description", "scenarios", "a_impact_chiffre", "entrees_trajectoire",
]


def parse_frontmatter(filepath_content):
    """Même approche que les autres audits -- yaml.safe_load() sur le
    bloc frontmatter. Prend le contenu déjà lu (pas un chemin), pour ne
    lire le fichier qu'une fois puisqu'on doit aussi parser le corps."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", filepath_content, re.DOTALL)
    if not m:
        return {}, ""
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}, m.group(2)
    return (fm if isinstance(fm, dict) else {}), m.group(2)


def extraire_section(corps, titre):
    """Isole le texte d'une section '## {titre}' jusqu'au prochain titre
    '## ' (ou la fin du corps). Retourne None si le titre n'existe pas
    -- une section absente n'est PAS une erreur (Impact chiffré est
    optionnelle), contrairement à un frontmatter illisible."""
    pattern = r"## {}\n(.*?)(?=\n## |\Z)".format(re.escape(titre))
    m = re.search(pattern, corps, re.DOTALL)
    return m.group(1) if m else None


def extraire_bloc_yaml(texte_section):
    """Isole le premier bloc ```yaml ... ``` dans une section et le
    parse. Retourne None si la section ne contient pas de bloc yaml
    (ne devrait pas arriver sur les sections concernées, mais défensif
    -- même esprit que le reste des audits, jamais de crash sur une
    anomalie de données)."""
    if texte_section is None:
        return None
    m = re.search(r"```yaml\n(.*?)\n```", texte_section, re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None


def scanner_tout(scenario_filter=None):
    """Retourne (signaux, non_lisibles). non_lisibles compte les
    fichiers dont le FRONTMATTER ne parse pas -- une section Trajectoire
    injectée absente ou un bloc yaml cassé ne compte PAS comme illisible
    (traité comme scenarios=[] / a_impact_chiffre=False), le frontmatter
    seul reste la donnée minimale exploitable."""
    signaux = []
    non_lisibles = 0

    if not os.path.isdir(SIGNAUX_DIR):
        return signaux, non_lisibles

    for fname in sorted(os.listdir(SIGNAUX_DIR)):
        if not fname.endswith(".md") or fname.startswith("_") or fname in FICHIERS_EXCLUS:
            continue
        filepath = os.path.join(SIGNAUX_DIR, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        fm, corps = parse_frontmatter(content)
        if not fm:
            non_lisibles += 1
            continue

        section_idee = extraire_section(corps, "Idée source")
        description = (section_idee or "").strip()

        section_trajectoire = extraire_section(corps, "Trajectoire injectée")
        trajectoire_brute = extraire_bloc_yaml(section_trajectoire)

        scenarios = set()
        entrees_trajectoire = 0
        trajectoire = []  # liste d'entrées (une par variable cible) : {scenario: {evolution, date_bascule, evenement_cle}}
        if isinstance(trajectoire_brute, dict):
            entries = trajectoire_brute.get("signal_to_state") or []
            if isinstance(entries, list):
                entrees_trajectoire = len(entries)
                for entree in entries:
                    if isinstance(entree, dict):
                        sc = entree.get("scenarios") or {}
                        if isinstance(sc, dict):
                            scenarios.update(sc.keys())
                            trajectoire.append(sc)

        section_impact = extraire_section(corps, "Impact chiffré")
        impact = extraire_bloc_yaml(section_impact)
        a_impact_chiffre = isinstance(impact, dict) and bool(impact.get("impact_sur_variables"))

        scenarios_liste = sorted(scenarios)
        if scenario_filter and scenario_filter not in scenarios_liste:
            continue

        signaux.append({
            "fichier": fname,
            "slug": fm.get("slug", fname.replace(".md", "")),
            "source": fm.get("source", "inconnu"),
            "categorie": fm.get("categorie", "inconnu"),
            "variables_cibles": fm.get("variables_cibles") or [],
            "statut": fm.get("statut", "inconnu"),
            "description": description,
            "scenarios": scenarios_liste,
            "trajectoire": trajectoire,
            "a_impact_chiffre": a_impact_chiffre,
            "entrees_trajectoire": entrees_trajectoire,
        })
    signaux.sort(key=lambda s: s["slug"])
    return signaux, non_lisibles


def calculer_resume(signaux):
    resume = {
        "total": len(signaux),
        "by_categorie": {},
        "by_statut": {},
        "by_scenario": {},
        "avec_impact_chiffre": 0,
        "sans_scenario_rattache": 0,
        "entrees_incoherentes": 0,
    }
    for s in signaux:
        resume["by_categorie"][s["categorie"]] = resume["by_categorie"].get(s["categorie"], 0) + 1
        resume["by_statut"][s["statut"]] = resume["by_statut"].get(s["statut"], 0) + 1
        for sc in s["scenarios"]:
            resume["by_scenario"][sc] = resume["by_scenario"].get(sc, 0) + 1
        if s["a_impact_chiffre"]:
            resume["avec_impact_chiffre"] += 1
        if not s["scenarios"]:
            resume["sans_scenario_rattache"] += 1
        # Normal d'avoir plusieurs entrées signal_to_state (une par
        # variable cible, voir docstring en tête de fichier) -- ce qui
        # serait anormal, c'est un ÉCART avec le nombre de
        # variables_cibles déclarées (signe d'injection partielle).
        if s["entrees_trajectoire"] != len(s["variables_cibles"]):
            resume["entrees_incoherentes"] += 1
    return resume


DOCUMENTATION_DIR = os.path.join(VAULT_ROOT, "documentation")
RAPPORT_MD_PATH = os.path.join(DOCUMENTATION_DIR, "inventaire_signaux.md")


def generer_rapport_md(signaux, resume, non_lisibles, scenario_filter):
    lignes = []
    lignes.append("# Inventaire des signaux faibles{}".format(
        " — {}".format(scenario_filter) if scenario_filter else " — tous scénarios"))
    lignes.append("")
    lignes.append("*Généré automatiquement par `audit_inventaire_signaux.py` — "
                   "ce fichier est réécrit à chaque génération, ne pas éditer à la main.*")
    lignes.append("")
    lignes.append("## Résumé")
    lignes.append("")
    lignes.append("- **Total** : {} signal(aux)".format(resume["total"]))
    if non_lisibles:
        lignes.append("- {} fichier(s) .md illisible(s)/frontmatter invalide, ignoré(s)".format(non_lisibles))
    lignes.append("- Avec Impact chiffré : {}".format(resume["avec_impact_chiffre"]))
    if resume["sans_scenario_rattache"]:
        lignes.append("- ⚠ Sans scénario rattaché (Trajectoire injectée absente/vide) : {}".format(
            resume["sans_scenario_rattache"]))
    if resume["entrees_incoherentes"]:
        lignes.append("- ⚠ Nombre d'entrées `signal_to_state` ≠ nombre de `variables_cibles` "
                      "(injection probablement partielle) : {}".format(resume["entrees_incoherentes"]))
    lignes.append("")
    lignes.append("**Par catégorie**")
    lignes.append("")
    for c, n in sorted(resume["by_categorie"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(c, n))
    lignes.append("")
    lignes.append("**Par statut**")
    lignes.append("")
    for s, n in sorted(resume["by_statut"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(s, n))
    lignes.append("")
    lignes.append("**Par scénario rattaché**")
    lignes.append("")
    for sc, n in sorted(resume["by_scenario"].items(), key=lambda x: -x[1]):
        lignes.append("- {} — {}".format(sc, n))
    lignes.append("")
    lignes.append("## Détail")
    lignes.append("")
    for s in signaux:
        scenarios_str = ", ".join(s["scenarios"]) if s["scenarios"] else "—"
        lignes.append("### {}".format(s["slug"]))
        lignes.append("")
        lignes.append("- **Catégorie** : {} | **Statut** : {} | **Impact chiffré** : {}".format(
            s["categorie"], s["statut"], "oui" if s["a_impact_chiffre"] else "non"))
        lignes.append("- **Scénarios** : {}".format(scenarios_str))
        if s["description"]:
            lignes.append("- **Idée source** : {}".format(s["description"]))
        lignes.append("- Fichier : `{}`".format(s["fichier"]))
        lignes.append("")
    return "\n".join(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default=None,
                         help="Limiter aux signaux rattachés à un scénario (défaut : tous).")
    parser.add_argument("--detail", action="store_true",
                         help="Affiche le détail signal par signal en plus du résumé "
                              "(console uniquement, sans --json).")
    parser.add_argument("--md", action="store_true",
                         help="Écrit le rapport complet en Markdown dans "
                              "documentation/inventaire_signaux.md.")
    parser.add_argument("--csv", metavar="FICHIER", default=None,
                         help="Exporte aussi l'inventaire en CSV.")
    parser.add_argument("--json", action="store_true",
                         help="Affiche aussi un résumé JSON sur une seule ligne finale, "
                              "en plus de --md/--csv si demandés -- pour intégration GUI.")
    args = parser.parse_args()

    signaux, non_lisibles = scanner_tout(args.scenario)
    resume = calculer_resume(signaux)

    chemin_md = None
    if args.md:
        contenu = generer_rapport_md(signaux, resume, non_lisibles, args.scenario)
        os.makedirs(DOCUMENTATION_DIR, exist_ok=True)
        with open(RAPPORT_MD_PATH, "w", encoding="utf-8") as f:
            f.write(contenu)
        chemin_md = RAPPORT_MD_PATH

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CHAMPS_CSV, extrasaction="ignore")
            writer.writeheader()
            for s in signaux:
                row = dict(s)
                row["variables_cibles"] = "|".join(s["variables_cibles"])
                row["scenarios"] = "|".join(s["scenarios"])
                writer.writerow(row)

    if args.json:
        print(json.dumps({
            "ok": True,
            "resume": resume,
            "signaux": signaux,
            "signaux_illisibles": non_lisibles,
            "rapport_md": chemin_md,
            "rapport_csv": args.csv,
        }, ensure_ascii=False))
        return

    if args.md:
        print("Rapport Markdown écrit : {}".format(chemin_md))
    if args.csv:
        print("Export CSV : {}".format(args.csv))
    if args.md or args.csv:
        print("({} signaux, {} illisibles ignorés)".format(len(signaux), non_lisibles))

    print("=" * 60)
    print("INVENTAIRE SIGNAUX FAIBLES{}".format(
        " — {}".format(args.scenario) if args.scenario else " — tous scénarios"))
    print("=" * 60)
    print("Total : {} signal(aux)".format(resume["total"]))
    if non_lisibles:
        print("({} fichier(s) .md illisible(s)/frontmatter invalide, ignoré(s))".format(non_lisibles))
    print()
    print("Par catégorie :")
    for c, n in sorted(resume["by_categorie"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(c, n))
    print()
    print("Par statut :")
    for s, n in sorted(resume["by_statut"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(s, n))
    print()
    print("Par scénario rattaché :")
    for sc, n in sorted(resume["by_scenario"].items(), key=lambda x: -x[1]):
        print("  {:<25} {}".format(sc, n))
    print()
    print("Avec Impact chiffré : {}".format(resume["avec_impact_chiffre"]))
    if resume["sans_scenario_rattache"]:
        print("⚠ Sans scénario rattaché : {}".format(resume["sans_scenario_rattache"]))
    if resume["entrees_incoherentes"]:
        print("⚠ Entrées signal_to_state ≠ variables_cibles (injection partielle probable) : {}".format(
            resume["entrees_incoherentes"]))

    if args.detail:
        print()
        print("-" * 60)
        print("DÉTAIL")
        print("-" * 60)
        for s in signaux:
            print("[{}] {} — {}".format(s["categorie"], s["slug"], s["statut"]))
            print("  scénarios : {}".format(", ".join(s["scenarios"]) if s["scenarios"] else "(aucun)"))
            print("  variables_cibles : {}".format(", ".join(s["variables_cibles"])))
            if s["description"]:
                print("  idée source : {}".format(s["description"]))
            print("  → {}".format(s["fichier"]))


if __name__ == "__main__":
    main()
