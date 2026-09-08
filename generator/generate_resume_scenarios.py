#!/usr/bin/env python3
"""
generate_resume_scenarios.py — Ourrassol 2098
=================================================

Génère un résumé en prose (2-3 paragraphes, un appel LLM par scénario)
des principaux acteurs et événements de chaque scénario -- demande de
David, 7 septembre 2026. Calqué directement sur detect_basculements_
narratifs.py (même mécanique : sélection déterministe des données à
soumettre au LLM, un seul appel par scénario, cache persistant écrit à
chaque exécution, jamais recalculé automatiquement).

SÉLECTION DES DONNÉES (déterministe, aucun appel LLM à cette étape)
--------------------------------------------------------------------
Réutilise directement scanner_tout() de audit_inventaire_instances.py
et audit_inventaire_event_instances.py (chantier GUI Entités/Instances/
Événements/Signaux, même session) plutôt que de reparser le vault :
- Top instances par score d'impact (impact_local + impact_systemique_
  global, décroissant) -- TOP_N_INSTANCES par scénario.
- Top event_instances par portée (globale > continentale > regionale >
  locale, à portée égale les plus récentes/nombreuses en premier) --
  TOP_N_EVENEMENTS par scénario.

GÉNÉRATION (1 appel LLM par scénario)
--------------------------------------
task_tier="creative_souple" (llm_client.py) -- rédaction libre, pas de
contrainte d'identité tierce à respecter (contrairement à "strict",
qui vise la fidélité à une voix/un personnage). Le prompt fournit la
liste curatée d'acteurs/événements, PAS le texte brut d'articles --
le LLM synthétise depuis des données structurées, pas depuis de la
prose déjà écrite.

USAGE
-----
    python3 generate_resume_scenarios.py
        # tous les scénarios, appelle le LLM 6 fois

    python3 generate_resume_scenarios.py --scenario eco_communalism

    python3 generate_resume_scenarios.py --md
        # écrit aussi documentation/resume_scenarios.md

    python3 generate_resume_scenarios.py --json
"""

import argparse
import json
import os
from datetime import datetime

from audit_inventaire_instances import scanner_tout as scanner_instances
from audit_inventaire_event_instances import scanner_tout as scanner_event_instances
from audit_inventaire_instances import VAULT_ROOT
from llm_client import call_llm

DOCUMENTATION_DIR = os.path.join(VAULT_ROOT, "documentation")
RAPPORT_MD_PATH = os.path.join(DOCUMENTATION_DIR, "resume_scenarios.md")
# Cache persistant, même convention que state/basculements_narratifs.json --
# chemin RELATIF au dossier d'exécution (pipeline_dir/generator/), PAS sous
# VAULT_ROOT. Lu par la route GET, écrit par la route POST (via ce script).
STATE_DIR = "state"
CACHE_PATH = os.path.join(STATE_DIR, "resume_scenarios.json")

TOP_N_INSTANCES = 15
TOP_N_EVENEMENTS = 10

PORTEE_RANG = {"globale": 3, "continentale": 2, "regionale": 1, "locale": 0}


def _top_instances(scenario):
    instances, _ = scanner_instances(scenario_filter=scenario)
    for i in instances:
        i["_score_impact"] = (i.get("impact_local") or 0) + (i.get("impact_systemique_global") or 0)
    instances.sort(key=lambda i: i["_score_impact"], reverse=True)
    return instances[:TOP_N_INSTANCES]


def _top_evenements(scenario):
    event_instances, _ = scanner_event_instances(scenario_filter=scenario)
    event_instances.sort(key=lambda e: PORTEE_RANG.get(e.get("portee"), -1), reverse=True)
    return event_instances[:TOP_N_EVENEMENTS]


def _construire_prompt(scenario, instances, evenements):
    lignes_instances = []
    for i in instances:
        role = (i.get("role_dans_scenario") or "").strip().replace("\n", " ")
        if len(role) > 200:
            role = role[:200] + "…"
        lignes_instances.append("- {} ({}, impact {}+{}) : {}".format(
            i.get("name", "?"), i.get("type_dans_scenario", "?"),
            i.get("impact_local") or 0, i.get("impact_systemique_global") or 0,
            role or "(pas de rôle décrit)"))

    lignes_evenements = []
    for e in evenements:
        desc = (e.get("description") or "").strip().replace("\n", " ")
        if len(desc) > 200:
            desc = desc[:200] + "…"
        date_str = e.get("date_label") or e.get("date") or "?"
        lignes_evenements.append("- {} ({}, portée {}, {}) : {}".format(
            e.get("name", "?"), e.get("type_evenement", "?"), e.get("portee", "?"),
            date_str, desc or "(pas de description)"))

    return (
        "ACTEURS PRINCIPAUX (par score d'impact) :\n{}\n\n"
        "ÉVÉNEMENTS PRINCIPAUX (par portée) :\n{}"
    ).format(
        "\n".join(lignes_instances) or "(aucune instance)",
        "\n".join(lignes_evenements) or "(aucun event_instance)",
    )


def generer_resume_scenario(scenario):
    """Retourne {"resume": str, "n_instances": int, "n_evenements": int} --
    ou {"resume": None, "erreur": str} en cas d'échec LLM (jamais de
    résumé inventé par défaut)."""
    instances = _top_instances(scenario)
    evenements = _top_evenements(scenario)
    contexte = _construire_prompt(scenario, instances, evenements)

    system = (
        "Tu rédiges un résumé synthétique en prose (2 à 3 paragraphes) de "
        "l'état d'un scénario de fiction journalistique prospective, à "
        "partir de ses acteurs et événements les plus significatifs. Le "
        "public est l'équipe éditoriale du journal fictif : elle a besoin "
        "d'un repère narratif rapide pour se réorienter dans le scénario, "
        "pas d'un inventaire exhaustif. Dégage les dynamiques et tensions "
        "dominantes plutôt que de lister mécaniquement chaque élément fourni "
        "-- certains éléments peuvent être omis du résumé s'ils sont "
        "secondaires par rapport à la trajectoire d'ensemble. Réponds "
        "uniquement avec le texte du résumé, sans titre ni préambule."
    )
    user = "Scénario : {}\n\n{}".format(scenario, contexte)

    try:
        resume = call_llm(system, user, max_tokens=900, temperature=0.7,
                           task_tier="creative_souple")
    except Exception as e:
        return {"resume": None, "erreur": str(e),
                "n_instances": len(instances), "n_evenements": len(evenements)}

    return {"resume": resume.strip(), "n_instances": len(instances),
            "n_evenements": len(evenements)}


def lire_cache():
    """Lecture seule -- {} si jamais généré. Ne lève jamais d'exception."""
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("resumes_par_scenario", {})
    except Exception:
        return {}


def ecrire_cache(nouveaux_resultats):
    """Fusionne avec le cache existant -- un run --scenario X ne doit
    jamais effacer les résumés déjà en cache pour les autres scénarios."""
    cache = lire_cache()
    maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for scenario, data in nouveaux_resultats.items():
        cache[scenario] = {**data, "generated_at": maintenant}
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({"resumes_par_scenario": cache}, f, ensure_ascii=False, indent=2)
    return cache


def generer_rapport_md(resultats):
    lignes = []
    lignes.append("# Résumés par scénario")
    lignes.append("")
    lignes.append("*Généré automatiquement par `generate_resume_scenarios.py` "
                   "(1 appel LLM par scénario, à partir des acteurs/événements "
                   "les plus impactants) -- réécrit à chaque génération, ne pas "
                   "éditer à la main.*")
    lignes.append("")
    for scenario, data in resultats.items():
        lignes.append("## {}".format(scenario))
        lignes.append("")
        if data.get("resume"):
            lignes.append(data["resume"])
        else:
            lignes.append("*Échec de génération : {}*".format(data.get("erreur", "raison inconnue")))
        lignes.append("")
    return "\n".join(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default=None,
                         help="Limiter à un scénario (défaut : tous les 6).")
    parser.add_argument("--md", action="store_true",
                         help="Écrit aussi documentation/resume_scenarios.md.")
    parser.add_argument("--json", action="store_true",
                         help="Sortie JSON sur une seule ligne finale.")
    args = parser.parse_args()

    scenarios = [args.scenario] if args.scenario else [
        "reference", "breakdown", "fortress_world",
        "new_sustainability", "eco_communalism", "policy_reform",
    ]

    resultats = {}
    for scenario in scenarios:
        if not args.json:
            print("Génération du résumé — {}…".format(scenario))
        resultats[scenario] = generer_resume_scenario(scenario)

    # Cache persistant -- toujours écrit, indépendamment de --md/--json.
    ecrire_cache(resultats)

    chemin_md = None
    if args.md:
        contenu = generer_rapport_md(resultats)
        os.makedirs(DOCUMENTATION_DIR, exist_ok=True)
        with open(RAPPORT_MD_PATH, "w", encoding="utf-8") as f:
            f.write(contenu)
        chemin_md = RAPPORT_MD_PATH

    if args.json:
        print(json.dumps({
            "ok": True,
            "resumes_par_scenario": resultats,
            "rapport_md": chemin_md,
            "cache": CACHE_PATH,
        }, ensure_ascii=False))
        return

    print()
    print("=" * 60)
    print("RÉSUMÉS PAR SCÉNARIO")
    print("=" * 60)
    for scenario, data in resultats.items():
        print("-- {} --".format(scenario))
        if data.get("resume"):
            print(data["resume"])
        else:
            print("[ÉCHEC] {}".format(data.get("erreur", "raison inconnue")))
        print()
    print("Cache mis à jour : {}".format(CACHE_PATH))
    if chemin_md:
        print("Rapport Markdown écrit : {}".format(chemin_md))


if __name__ == "__main__":
    main()
