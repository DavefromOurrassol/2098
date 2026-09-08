#!/usr/bin/env python3
"""
detect_basculements_narratifs.py — Ourrassol 2098
====================================================

Diagnostic en lecture seule (aucune écriture par défaut, sauf --md) --
chantier "Suite narrative des événements", extension "détection de
basculements" (5 septembre 2026).

CONTEXTE
--------
Après avoir abandonné le rattrapage rétroactif d'evenements_cites (voir
detect_evenements_cites_retroactif.py -- aucun article ancien ne
développait un événement custom comme sujet central), la question
posée par David a changé : plutôt que de chercher des articles liés à
des événements DÉJÀ enregistrés, repérer des articles qui décrivent un
BASCULEMENT narratif -- aggravation, amélioration, déblocage, blocage,
émergence de crise -- qui pourrait mériter de devenir un nouvel
événement custom (via "Promouvoir un événement"), qu'il corresponde ou
non à un événement déjà connu.

Vérifié avant de construire cet outil (5 septembre 2026) : aucun champ
structuré du frontmatter (tension_level, scenario_state) ne varie dans
le temps -- ce sont des réglages statiques du scénario entier, lus une
fois depuis scenarios/{slug}.md (voir loader.py::load_scenario()), pas
recalculés par article. variables_pilotes ne liste que des NOMS de
variables, jamais de niveau numérique. Aucune donnée gratuite et fiable
n'existe donc pour détecter un basculement -- seule la lecture du texte
peut le révéler.

PORTÉE (décisions actées avec David, 5 septembre 2026)
--------------------------------------------------------
- Volume : tout le corpus (200+ articles, tous scénarios) par défaut.
- Granularité : le CHAPO seul (pas le corps complet) -- moins fiable
  qu'une lecture intégrale, mais un chapo est écrit pour résumer
  l'essentiel, et ça permet de traiter tout le corpus en UN SEUL appel
  LLM PAR SCÉNARIO (tous les chapos du scénario dans un même prompt),
  plutôt qu'un appel par article -- 6 appels au lieu de 200+.
- Sortie : un rapport simple à parcourir à la main (pas de création
  automatique d'événement, pas de lien pré-rempli vers "Promouvoir un
  événement" -- David décide lui-même quoi faire de chaque candidat).

USAGE
-----
    python3 detect_basculements_narratifs.py
        # tout le corpus, rapport console

    python3 detect_basculements_narratifs.py --scenario new_sustainability

    python3 detect_basculements_narratifs.py --md
        # écrit aussi le rapport dans documentation/basculements_narratifs.md

    python3 detect_basculements_narratifs.py --json
"""

import argparse
import json
import os
from datetime import datetime

from edition_utils import MOIS_FR
from audit_inventaire_articles import scanner_tout, VAULT_ROOT
from inject_custom_events import call_claude_json, get_client

DOCUMENTATION_DIR = os.path.join(VAULT_ROOT, "documentation")
RAPPORT_MD_PATH = os.path.join(DOCUMENTATION_DIR, "basculements_narratifs.md")
# Cache persistant (6 septembre 2026, intégration GUI onglet Articles) --
# écrit à CHAQUE exécution, indépendamment de --md/--json (qui restent des
# sorties optionnelles). Chemin RELATIF au dossier d'exécution du script
# (pipeline_dir, "generator/") -- PAS sous VAULT_ROOT (le vault Obsidian,
# un dossier différent dans ce projet). Corrigé le 6 septembre après un
# premier essai réel où le GUI affichait "Détection jamais lancée" malgré
# un script qui tournait sans erreur : la route Flask /api/articles/
# basculements lit pipeline_dir/state/basculements_narratifs.json (même
# convention que /api/edition/active et state/editions.json), donc le
# fichier doit être écrit là, pas dans le vault.
STATE_DIR = "state"
CACHE_PATH = os.path.join(STATE_DIR, "basculements_narratifs.json")

TYPES_BASCULE = [
    "aggravation", "amelioration", "deblocage", "blocage", "emergence_crise", "autre",
]


def _construire_prompt_scenario(scenario, articles):
    """Un seul appel LLM pour TOUS les chapos d'un scénario, triés
    chronologiquement (déjà fait par scanner_tout()) -- le LLM voit la
    progression complète et peut repérer un vrai changement de
    trajectoire entre deux dates, pas juste un chapo isolé."""
    lignes = []
    for a in articles:
        date_str = ("{} {} {}".format(a["_jour"], MOIS_FR[a["_mois"]], a["_annee"])
                    if a["_annee"] is not None else "(date non reconnue)")
        lignes.append("- [{}] fichier: {} | slug: {} | chapo: {}".format(
            date_str, a["fichier"], a["slug"], a["chapo"] or "(vide)"
        ))
    return "\n".join(lignes)


def detecter_basculements_scenario(client, scenario, articles):
    """Retourne une liste de candidats {"fichier", "type_bascule",
    "justification"} pour ce scénario -- [] si aucun candidat ou en cas
    d'échec de parsing (jamais de faux résultat inventé par défaut)."""
    chapos_txt = _construire_prompt_scenario(scenario, articles)

    system = (
        "Tu analyses la chronologie des chapos (résumés) d'un scénario de "
        "fiction journalistique prospective, triés par date. Repère les "
        "articles qui décrivent un vrai BASCULEMENT narratif dans la "
        "trajectoire du scénario -- une aggravation, une amélioration, un "
        "déblocage, un blocage, ou l'émergence d'une crise -- par "
        "opposition à un article qui décrit simplement l'état déjà établi "
        "des choses sans rien faire basculer. Utilise la chronologie pour "
        "juger : un basculement se voit par contraste avec ce qui précède, "
        "pas dans l'absolu. Réponds UNIQUEMENT en JSON, sans texte autour : "
        "{\"candidats\": [{\"fichier\": \"...\", \"type_bascule\": "
        "\"aggravation|amelioration|deblocage|blocage|emergence_crise|autre\", "
        "\"justification\": \"...\"}]} -- liste vide si aucun basculement "
        "net ne se dégage de cette chronologie."
    )
    user = "Chronologie des chapos ({}) :\n{}\n\nQuels articles marquent un vrai basculement ?".format(
        scenario, chapos_txt
    )

    try:
        result = call_claude_json(client, system, user, max_tokens=2000)
        candidats = result.get("candidats", []) or []
    except Exception as e:
        print("  [WARN] Échec détection LLM sur {} : {}".format(scenario, e))
        return []

    fichiers_valides = {a["fichier"] for a in articles}
    valides = []
    for c in candidats:
        if c.get("fichier") not in fichiers_valides:
            # Même garde-fou que detect_evenements_cites_retroactif.py :
            # un fichier halluciné (hors de la liste fournie) est rejeté,
            # jamais silencieusement gardé.
            continue
        if c.get("type_bascule") not in TYPES_BASCULE:
            c["type_bascule"] = "autre"
        valides.append(c)
    return valides


def lire_cache():
    """Lecture seule -- {} si jamais généré. Ne lève jamais d'exception (un
    cache absent/corrompu ne doit jamais faire planter le script)."""
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("resultats_par_scenario", {})
    except Exception:
        return {}


def ecrire_cache(nouveaux_resultats):
    """Fusionne nouveaux_resultats (uniquement les scénarios effectivement
    scannés cette exécution) avec le cache existant -- un run limité à
    --scenario X ne doit jamais effacer les résultats déjà en cache pour
    les autres scénarios. Chaque scénario porte son propre horodatage,
    puisqu'ils peuvent être régénérés à des moments différents."""
    cache = lire_cache()
    maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for scenario, candidats in nouveaux_resultats.items():
        cache[scenario] = {"generated_at": maintenant, "candidats": candidats}
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({"resultats_par_scenario": cache}, f, ensure_ascii=False, indent=2)
    return cache


def generer_rapport_md(resultats_par_scenario, total_articles):
    lignes = []
    lignes.append("# Basculements narratifs détectés")
    lignes.append("")
    lignes.append("*Généré automatiquement par `detect_basculements_narratifs.py` "
                   "(détection sur chapo seul, un appel LLM par scénario) -- "
                   "réécrit à chaque génération, ne pas éditer à la main. "
                   "Rapport à parcourir à la main : aucun événement n'est créé "
                   "automatiquement à partir de ces candidats.*")
    lignes.append("")
    total_candidats = sum(len(v) for v in resultats_par_scenario.values())
    lignes.append("**{} candidat(s) sur {} article(s) scannés.**".format(
        total_candidats, total_articles))
    lignes.append("")
    for scenario, candidats in resultats_par_scenario.items():
        lignes.append("## {} ({} candidat(s))".format(scenario, len(candidats)))
        lignes.append("")
        for c in candidats:
            lignes.append("- **[{}]** `{}`".format(c["type_bascule"], c["fichier"]))
            lignes.append("  {}".format(c["justification"]))
        lignes.append("")
    return "\n".join(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default=None,
                         help="Limiter à un scénario (défaut : tous).")
    parser.add_argument("--md", action="store_true",
                         help="Écrit aussi le rapport dans "
                              "documentation/basculements_narratifs.md (natif au vault).")
    parser.add_argument("--json", action="store_true",
                         help="Sortie JSON sur une seule ligne finale au lieu de "
                              "l'affichage console.")
    args = parser.parse_args()

    articles, non_lisibles = scanner_tout(args.scenario)
    par_scenario = {}
    for a in articles:
        par_scenario.setdefault(a["scenario"], []).append(a)

    client = get_client()
    resultats = {}
    for scenario, arts in par_scenario.items():
        if not args.json:
            print("Scan {} — {} article(s)…".format(scenario, len(arts)))
        resultats[scenario] = detecter_basculements_scenario(client, scenario, arts)

    # Cache persistant -- toujours écrit, indépendamment de --md/--json (voir
    # commentaire sur CACHE_PATH plus haut).
    ecrire_cache(resultats)

    chemin_md = None
    if args.md:
        contenu = generer_rapport_md(resultats, len(articles))
        os.makedirs(DOCUMENTATION_DIR, exist_ok=True)
        with open(RAPPORT_MD_PATH, "w", encoding="utf-8") as f:
            f.write(contenu)
        chemin_md = RAPPORT_MD_PATH

    if args.json:
        print(json.dumps({
            "ok": True,
            "total_articles": len(articles),
            "resultats_par_scenario": resultats,
            "rapport_md": chemin_md,
            "cache": CACHE_PATH,
        }, ensure_ascii=False))
        return

    print()
    print("=" * 60)
    print("BASCULEMENTS NARRATIFS DÉTECTÉS")
    print("=" * 60)
    total_candidats = sum(len(v) for v in resultats.values())
    print("{} candidat(s) sur {} article(s) scannés.".format(total_candidats, len(articles)))
    print("Cache mis à jour : {}".format(CACHE_PATH))
    if chemin_md:
        print("Rapport Markdown écrit : {}".format(chemin_md))
    print()
    for scenario, candidats in resultats.items():
        print("-- {} ({} candidat(s)) --".format(scenario, len(candidats)))
        for c in candidats:
            print("  [{}] {}".format(c["type_bascule"], c["fichier"]))
            print("    {}".format(c["justification"]))
        print()


if __name__ == "__main__":
    main()
