#!/usr/bin/env python3
"""
idees_vers_queue.py — Ourrassol 2098
====================================

Transforme un TEXTE LIBRE (une ou plusieurs idées, écrites comme on les
dirait) en entrées de queue.yaml correctement formatées, pour les signaux
faibles ou les événements custom (27 septembre 2026).

N'ÉCRIT JAMAIS dans queue.yaml : il PROPOSE seulement. L'écriture reste à
un seul endroit, le formulaire GUI "Ajouter à la queue" (/api/yaml/append,
avec ses contrôles), que ce script sert à pré-remplir -- ou un copier-coller
manuel du YAML affiché en mode terminal. Un seul chemin d'écriture vers la
queue, pour ne pas recréer le bug d'écrasement du 11 août
(saveOpenConfigForms()).

Un seul appel LLM (tier structured_strict) découpe le texte en idées et
propose les champs ; ils sont ensuite vérifiés et corrigés MÉCANIQUEMENT ici
(variables existantes, id unique, persistance reconnue, portée/intensité/
date valides pour un événement). Tout ce qui a été corrigé ou reste à
choisir est listé dans "avertissements" -- jamais corrigé en silence.

USAGE
-----
    python3 idees_vers_queue.py --type signal --texte "des prompteurs apparaissent en 2027..."
    python3 idees_vers_queue.py --type evenement --fichier mes_idees.txt
    pbpaste | python3 idees_vers_queue.py --type signal       # texte sur l'entrée standard
    python3 idees_vers_queue.py --type signal --texte "..." --json   # sortie machine (GUI)
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import yaml

from llm_client import call_llm  # tier structured_strict — canonique/référencé
import dynamique as dyn          # niveaux de persistance (module pur)
from inject_custom_signals import (
    SCENARIOS, VALID_VARS, build_variables_summary,
    QUEUE_PATH as SIGNAUX_QUEUE, PROCESSED_PATH as SIGNAUX_PROCESSED,
    NEEDS_REVIEW_PATH as SIGNAUX_NEEDS_REVIEW,
    ANNEE_APPARITION_MIN, ANNEE_APPARITION_MAX,
)

TYPES = ("signal", "evenement")
MAX_VARS = 4

CRITERES_PERSISTANCE = """\
"persistance" = combien de temps l'effet CHIFFRÉ dure après sa montée :
  - "ephemere"   : mode, buzz, scandale, crise vite oubliée
  - "normale"    : tendance qui s'installe puis se dilue en une ou deux générations (cas par défaut)
  - "durable"    : transformation de société qui marque plusieurs générations
  - "permanente" : nouvelle institution, structure de pouvoir ou classe sociale qui
                   existe encore en 2098
Choisis d'après le POINT D'ARRIVÉE décrit par l'utilisateur, pas d'après le point de départ
(ex : "un métier marginal qui devient une caste dirigeante" = permanente)."""


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def slugifier(texte):
    """snake_case ASCII, 60 caractères max."""
    t = unicodedata.normalize("NFKD", str(texte or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")
    return t[:60].rstrip("_")


def _collecter_ids(noeud, ids):
    """Récupère récursivement les `id` des idées (dict avec id + description),
    quelle que soit la structure du fichier (queue brute, ou processed/
    needs_review qui imbriquent l'idée sous "idea")."""
    if isinstance(noeud, dict):
        if "id" in noeud and "description" in noeud:
            ids.add(str(noeud["id"]))
        for v in noeud.values():
            _collecter_ids(v, ids)
    elif isinstance(noeud, list):
        for v in noeud:
            _collecter_ids(v, ids)


def ids_existants(chemins):
    ids = set()
    for p in chemins:
        try:
            if Path(p).exists():
                _collecter_ids(yaml.safe_load(Path(p).read_text(encoding="utf-8")), ids)
        except (OSError, yaml.YAMLError) as e:
            print(f"  ⚠ lecture impossible de {p} : {e}", file=sys.stderr)
    return ids


def chemins_type(type_):
    if type_ == "signal":
        return [SIGNAUX_QUEUE, SIGNAUX_PROCESSED, SIGNAUX_NEEDS_REVIEW]
    from inject_custom_events import QUEUE_PATH, PROCESSED_PATH, NEEDS_REVIEW_PATH
    return [QUEUE_PATH, PROCESSED_PATH, NEEDS_REVIEW_PATH]


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def construire_prompt(type_, texte):
    variables = build_variables_summary()
    communs = f"""Tu aides l'auteur du simulateur de presse fictive Ourrassol 2098 à
transformer ses idées, écrites librement, en entrées structurées pour son pipeline.

TEXTE DE L'UTILISATEUR :
<<<
{texte.strip()}
>>>

RÈGLES :
- Le texte peut contenir UNE ou PLUSIEURS idées distinctes : découpe-le, une entrée par
  idée. N'invente AUCUNE idée absente du texte, ne fusionne pas deux idées différentes.
- "description" : reformule l'idée en 3 à 6 phrases claires, en français, FIDÈLE au texte :
  garde toutes ses étapes et surtout son POINT D'ARRIVÉE (ce que l'idée devient à la fin),
  n'ajoute aucun fait, lieu ou acteur que l'utilisateur n'a pas évoqué.
- "id" : snake_case sans accents, 3 à 5 mots, qui résume l'idée.
- "variables_hint" : entre 1 et {MAX_VARS} variables parmi les 12 ci-dessous (slugs exacts) --
  une par domaine que la TRAJECTOIRE de l'idée touche explicitement (pas les effets
  lointains supposés). Préfère 2-3 ; 1 seulement pour une idée vraiment locale à un domaine.
- "justification" : 1 à 2 phrases, pourquoi ces variables et cette persistance.

{CRITERES_PERSISTANCE}

LES 12 VARIABLES DU SYSTÈME :
{variables}
"""
    if type_ == "signal":
        specifique = """
TYPE D'ENTRÉE : SIGNAL FAIBLE (une tendance qui émerge et évolue différemment dans chacun
des 6 scénarios -- pas un fait daté unique).
- "zone_hint" : UNIQUEMENT si le texte cite explicitement un lieu RÉEL de 2026 (pays,
  région, ville) -- sinon null. Ne déduis jamais un lieu.
- "annee_apparition" : toute année écrite dans le texte pour cette idée, même sans verbe
  (ex : "chine 2049 champion économique" -> 2049 ; "en 2027… puis en 2060…" -> la plus
  ancienne, 2027). null seulement si le texte ne contient AUCUNE année pour cette idée.
  N'invente jamais une date absente du texte.
- "plutot_evenement" : true si l'idée décrit en réalité un fait ponctuel et daté (une
  guerre, un traité, une catastrophe) plutôt qu'une tendance -- sinon false.

Réponds UNIQUEMENT en JSON, sans texte autour :
{"idees": [{"id": "...", "description": "...", "variables_hint": ["slug1", "slug2"],
  "zone_hint": null, "annee_apparition": null, "persistance": "normale", "plutot_evenement": false,
  "justification": "..."}]}
"""
    else:
        specifique = """
TYPE D'ENTRÉE : ÉVÉNEMENT (un fait daté, qui se produit à un moment donné, décliné ensuite
dans chaque scénario).
- "portee" : locale | regionale | continentale | globale
- "date_approximative" : année entière entre 2025 et 2097 ; si le texte n'en donne pas,
  choisis une année plausible et dis-le dans "justification".
- "intensite" : faible | modérée | forte | majeure (la FORCE du choc).
- "scenarios" : null (= les 6), SAUF si le texte restreint explicitement l'idée à certains
  scénarios (slugs : breakdown, fortress_world, new_sustainability, eco_communalism,
  policy_reform, reference).
- Si le texte cite un lieu, garde-le DANS la description (pas de champ séparé).

Réponds UNIQUEMENT en JSON, sans texte autour :
{"idees": [{"id": "...", "description": "...", "portee": "globale", "date_approximative": 2040,
  "intensite": "forte", "scenarios": null, "variables_hint": ["slug1"],
  "persistance": "normale", "justification": "..."}]}
"""
    return communs + specifique


def appeler_llm(prompt):
    texte = call_llm(
        system_prompt="Tu es un assistant de world-building. Tu réponds uniquement en JSON valide.",
        user_prompt=prompt,
        max_tokens=4000,
        temperature=0.0,
        task_tier="structured_strict",
    ).strip()
    texte = re.sub(r"^```(?:json)?\s*", "", texte)
    texte = re.sub(r"\s*```$", "", texte)
    return json.loads(texte)


# ---------------------------------------------------------------------------
# Vérification mécanique
# ---------------------------------------------------------------------------

def normaliser_idee(brut, type_, ids_pris, source):
    """Retourne (entree, avertissements) -- entree = dict prêt pour queue.yaml,
    ou None si l'idée est inutilisable (pas de description)."""
    av = []
    description = str(brut.get("description") or "").strip()
    if not description:
        return None, ["idée ignorée : description vide"]

    # id unique (queue + processed + needs_review + idées déjà proposées ici)
    id_ = slugifier(brut.get("id")) or slugifier(" ".join(description.split()[:5]))
    base, n = id_, 2
    while id_ in ids_pris:
        id_ = f"{base}_{n}"
        n += 1
    if id_ != base:
        av.append(f"id {base!r} déjà utilisé -> renommé {id_!r}")
    ids_pris.add(id_)

    entree = {"id": id_, "description": description}

    # Variables
    vars_brutes = brut.get("variables_hint") or []
    if isinstance(vars_brutes, str):
        vars_brutes = [vars_brutes]
    variables = list(dict.fromkeys(v for v in vars_brutes if v in VALID_VARS))
    inconnues = [v for v in vars_brutes if v not in VALID_VARS]
    if inconnues:
        av.append(f"variable(s) inconnue(s) retirée(s) : {inconnues}")
    if len(variables) > MAX_VARS:
        av.append(f"{len(variables)} variables proposées, gardé les {MAX_VARS} premières")
        variables = variables[:MAX_VARS]
    cle_vars = "variable_hint" if type_ == "signal" else "variables_hint"
    cle_count = "variable_hint_count" if type_ == "signal" else "variables_hint_count"
    if variables:
        entree[cle_vars] = variables
        entree[cle_count] = len(variables)
    else:
        av.append("aucune variable valide : l'IA choisira à l'injection")

    # Champs propres au type
    if type_ == "signal":
        zone = brut.get("zone_hint")
        if zone and str(zone).strip().lower() not in ("null", "none", ""):
            entree["zone_hint"] = str(zone).strip()
        annee = brut.get("annee_apparition")
        if annee in (None, "", "null"):
            # Rattrapage mécanique (27 septembre 2026) : le LLM laisse parfois
            # le champ vide sur un texte très court ("chine 2049 champion
            # économique"). On reprend alors la plus ancienne année plausible
            # écrite dans la description de CETTE idée (pas dans tout le
            # texte, qui peut contenir plusieurs idées), en le signalant.
            annees_texte = [int(a) for a in re.findall(r"\b(20[2-9]\d)\b", description)
                            if ANNEE_APPARITION_MIN <= int(a) <= ANNEE_APPARITION_MAX]
            if annees_texte:
                annee = min(annees_texte)
                av.append(f"année d'apparition {annee} reprise du texte (le LLM ne l'avait pas "
                          f"renseignée) -- à vérifier")
        if annee not in (None, "", "null"):
            try:
                annee = int(str(annee).strip()[:4])
                if not ANNEE_APPARITION_MIN <= annee <= ANNEE_APPARITION_MAX:
                    av.append(f"année d'apparition {annee} hors de "
                              f"{ANNEE_APPARITION_MIN}-{ANNEE_APPARITION_MAX} -> ramenée dans la plage")
                    annee = min(ANNEE_APPARITION_MAX, max(ANNEE_APPARITION_MIN, annee))
                entree["annee_apparition"] = annee
            except (TypeError, ValueError):
                av.append(f"année d'apparition {brut.get('annee_apparition')!r} illisible -- ignorée")
        if brut.get("plutot_evenement") is True:
            av.append("ressemble plutôt à un ÉVÉNEMENT (fait ponctuel daté) qu'à un signal "
                      "-- à envisager avec --type evenement")
    else:
        from inject_custom_events import VALID_PORTEES, VALID_INTENSITES
        portee = str(brut.get("portee") or "").strip().lower()
        if portee in VALID_PORTEES:
            entree["portee"] = portee
        else:
            av.append(f"portée {brut.get('portee')!r} invalide -- à choisir ({', '.join(VALID_PORTEES)})")
        try:
            annee = int(str(brut.get("date_approximative")).strip()[:4])
            if not 2025 <= annee <= 2097:
                av.append(f"date {annee} hors de 2025-2097 -> ramenée dans la plage")
                annee = min(2097, max(2025, annee))
            entree["date_approximative"] = annee
        except (TypeError, ValueError):
            av.append(f"date {brut.get('date_approximative')!r} invalide -- à choisir")
        intensite = str(brut.get("intensite") or "").strip().lower().replace("moderee", "modérée")
        if intensite in VALID_INTENSITES:
            entree["intensite"] = intensite
        else:
            av.append(f"intensité {brut.get('intensite')!r} invalide -- à choisir "
                      f"({', '.join(VALID_INTENSITES)})")
        scen = brut.get("scenarios")
        if isinstance(scen, list) and scen:
            valides = [s for s in scen if s in SCENARIOS]
            if len(valides) != len(scen):
                av.append(f"scénario(s) inconnu(s) retiré(s) : {[s for s in scen if s not in SCENARIOS]}")
            if valides:
                entree["scenarios"] = valides

    # Persistance
    pers = dyn.normaliser_persistance(brut.get("persistance"))
    if pers not in dyn.PERSISTANCE:
        if pers is not None:
            av.append(f"persistance {brut.get('persistance')!r} inconnue -> normale")
        pers = dyn.PERSISTANCE_DEFAUT
    entree["persistance"] = pers

    entree["source"] = source
    return entree, av


def proposer(type_, texte, source=None, _llm=appeler_llm):
    """Point d'entrée réutilisable (CLI et GUI). Retourne une liste de
    {"entree": dict, "justification": str, "avertissements": [str]}."""
    if type_ not in TYPES:
        raise ValueError(f"type inconnu : {type_!r} (attendu : {', '.join(TYPES)})")
    if not texte or not texte.strip():
        raise ValueError("texte vide")
    source = source or "texte_libre_{}".format(datetime.now().strftime("%Y-%m"))

    reponse = _llm(construire_prompt(type_, texte))
    brutes = reponse.get("idees") if isinstance(reponse, dict) else None
    if not isinstance(brutes, list) or not brutes:
        raise ValueError("le LLM n'a proposé aucune idée exploitable")

    ids_pris = ids_existants(chemins_type(type_))
    resultats = []
    for brut in brutes:
        if not isinstance(brut, dict):
            continue
        entree, av = normaliser_idee(brut, type_, ids_pris, source)
        if entree is None:
            continue
        resultats.append({"entree": entree,
                          "justification": str(brut.get("justification") or "").strip(),
                          "avertissements": av})
    if not resultats:
        raise ValueError("aucune idée exploitable après vérification")
    return resultats


# ---------------------------------------------------------------------------
# Sortie terminal
# ---------------------------------------------------------------------------

def afficher(resultats, type_):
    dossier = "signaux_custom" if type_ == "signal" else "evenements_custom"
    print(f"\n# {len(resultats)} idée(s) proposée(s) -- à coller sous `queue:` dans "
          f"{dossier}/queue.yaml (ou à charger dans le formulaire du GUI)\n")
    for r in resultats:
        if r["justification"]:
            print(f"  # Pourquoi : {r['justification']}")
        for a in r["avertissements"]:
            print(f"  # ⚠ {a}")
        bloc = yaml.dump([r["entree"]], allow_unicode=True, sort_keys=False,
                         default_flow_style=False, width=78)
        print("\n".join("  " + ligne for ligne in bloc.splitlines()))
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("USAGE")[0].strip())
    ap.add_argument("--type", choices=TYPES, required=True)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--texte", help="texte libre (sinon --fichier, sinon entrée standard)")
    src.add_argument("--fichier", help="fichier texte contenant la ou les idées")
    ap.add_argument("--source", help="valeur du champ source (défaut : texte_libre_AAAA-MM)")
    ap.add_argument("--json", action="store_true", help="sortie JSON sur une ligne (GUI)")
    args = ap.parse_args()

    if args.texte is not None:
        texte = args.texte
    elif args.fichier:
        texte = Path(args.fichier).read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            print("Colle ton texte puis Ctrl-D :", file=sys.stderr)
        texte = sys.stdin.read()

    try:
        resultats = proposer(args.type, texte, args.source)
    except Exception as e:
        if args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            sys.exit(1)
        raise SystemExit(f"[erreur] {e}")

    if args.json:
        print(json.dumps({"ok": True, "type": args.type, "idees": resultats}, ensure_ascii=False))
    else:
        afficher(resultats, args.type)


if __name__ == "__main__":
    main()
