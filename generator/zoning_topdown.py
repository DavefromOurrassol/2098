#!/usr/bin/env python3
"""
zoning_topdown.py — Ourrassol 2098 (P24 étape C.2)

Fonction cœur du générateur top-down : produit une proposition de zone
(complète pour un pays sans zone, ou révisée pour une zone suspecte)
conforme au schéma validate_zone() de enrich_geographie_recursive.py --
directement compatible avec le body attendu par carte_creer_zone_niveau1()
(gui/app.py) pour le cas pays_sans_zone.

PAS DE LECTURE/ÉCRITURE VAULT ICI -- ce module est une fonction pure (LLM
in, JSON out). La lecture des zones existantes (pour le contexte de
relations/éviter les collisions de slug) et l'écriture (CLI --review/--apply
en C.3, formulaire GUI pré-rempli en C.4) sont la responsabilité de
l'appelant, jamais de ce module.

Deux modes, choisis par `raison` :

  "pays_sans_zone" -- construit une zone niveau 1 complète depuis zéro
  pour un ou plusieurs pays réels sans zone dans ce scénario. Sortie
  compatible telle quelle avec le body JSON de carte_creer_zone_niveau1().

  "zone_suspecte" -- révise UNE zone existante (identifiée par son slug,
  déjà présente dans `zone_existante`) pour aligner sa description/type/
  statut/tensions_internes sur le patron spatial, suite à un signalement
  de check_patron_spatial_coherence.py (C.1). slug/origine_reelle/nom/
  niveau/parent/lieux_emblematiques/sources_attestees sont IMPOSÉS depuis
  la zone existante en sortie (jamais laissés à la discrétion du LLM,
  même si le prompt le lui demande déjà -- vérifié mécaniquement, pas
  seulement demandé, leçon des bugs #18/#34) : ce n'est pas un nouveau
  rattachement géographique, juste une révision de contenu narratif sur
  un sous-ensemble précis de champs. PAS compatible avec
  carte_creer_zone_niveau1() (qui crée toujours du niveau 1 sans parent
  connu) -- aucune route d'écriture n'existe encore pour ce cas, à
  construire en C.3/C.4.

Validation : chaque proposition passe par validate_zone() puis
clean_zone_relations() (enrich_geographie_recursive.py, mêmes fonctions que
le reste du pipeline) avant d'être retournée -- clean_zone_relations()
retire tout slug halluciné dans relations.allies/rivaux (la RÈGLE STRICTE
du prompt seule n'est jamais fiable, cf. leçon bugs #18/#34), les slugs
retirés sont remontés dans `issues`. Rien de tout cela ne garantit jamais
la pertinence narrative -- jugement humain requis avant tout --apply,
comme partout ailleurs dans ce pipeline.

USAGE (test manuel, pas de CLI de production -- C.2 est appelé par C.3/C.4)
----------------------------------------------------------------------------
    python3 zoning_topdown.py --scenario new_sustainability --pays Andorre
    python3 zoning_topdown.py --scenario breakdown \
        --zone-suspecte geneve_bunker_institutions \
        --raison-suspicion "Présence d'institutions internationales résiduelles..."
"""

import json
import re

from llm_client import call_llm
from patrons_spatiaux import patron_spatial_prompt_block
from enrich_geographie_recursive import (
    ZONE_TYPES, ZONE_STATUTS, LIEU_TYPES, TYPE_ENTITE_REELLE,
    validate_zone, clean_zone_relations,
)

# Cohérent avec enrich_geographie_recursive.py -- même nature de tâche
# (génération de zone structurée, canoniquement référencée ensuite dans
# tout le vault).
TASK_TIER = "structured_strict"
MAX_TOKENS = 2000

SCHEMA_JSON = """{
  "slug": "slug_snake_case",
  "nom": "Nom canonique de la zone",
  "type": "une valeur parmi: %(zone_types)s",
  "origine_reelle": [
    {"entite": "Nom du pays/subdivision/ville réelle", "type_entite": "une valeur parmi: %(type_entite)s", "portion": null}
  ],
  "description": "2-3 lignes sur ce qu'est cette zone DANS ce scénario précis",
  "statut": "une valeur parmi: %(zone_statuts)s",
  "tensions_internes": "1-2 lignes, ou chaîne vide si non pertinent",
  "periode_transition": "période approximative, ex: 2031-2045",
  "lieux_emblematiques": [
    {"nom": "Nom du lieu", "type": "une valeur parmi: %(lieu_types)s", "notes": "courte note"}
  ],
  "relations": {"allies": [], "rivaux": []}
}""" % {
    "zone_types": ", ".join(ZONE_TYPES),
    "type_entite": ", ".join(TYPE_ENTITE_REELLE),
    "zone_statuts": ", ".join(ZONE_STATUTS),
    "lieu_types": ", ".join(LIEU_TYPES),
}


def _slugs_existants(zones_existantes: list) -> set:
    return {z.get("slug") for z in zones_existantes if isinstance(z, dict) and z.get("slug")}


def _contexte_zones_existantes(zones_existantes: list) -> str:
    """Bloc de contexte listant les zones N1 existantes -- nécessaire pour que le
    LLM propose des relations.allies/rivaux réalistes (uniquement des slugs
    existants, même RÈGLE STRICTE que enrich_geographie_recursive.py) et pour
    limiter le risque de collision de slug côté génération (l'anti-collision
    réel reste vérifié mécaniquement après coup, jamais supposé du prompt seul)."""
    if not zones_existantes:
        return "(aucune zone niveau 1 existante dans ce scénario)"
    lignes = [
        f"  - {z.get('slug')} ({z.get('nom')}) : {(z.get('description') or '')[:150]}"
        for z in zones_existantes if isinstance(z, dict) and z.get("slug")
    ]
    return "\n".join(lignes)


def _system_prompt_pays_sans_zone() -> str:
    return f"""Tu es un générateur de zones géopolitiques pour un simulateur de \
worldbuilding (Ourrassol 2098). On te donne le patron spatial narratif d'un scénario \
et un ou plusieurs pays réels qui n'ont actuellement aucune zone dans ce scénario. Ta \
tâche : proposer UNE zone de niveau 1 (parent: null) qui les couvre, en incarnant \
fidèlement le patron spatial du scénario -- pas une zone plausible dans l'absolu, mais \
une réponse à "comment ce patron s'est-il concrétisé dans CETTE région précise, avec \
quelle friction ou réinterprétation locale" (un patron universel ne s'implante jamais \
identiquement partout).

Consignes strictes :
1. "slug" : snake_case, lettres minuscules/chiffres/underscores uniquement, ne doit \
collisionner avec AUCUN slug de la liste des zones existantes ci-dessous.
2. "origine_reelle" : un jeu d'entrées type_entite="pays" pour CHACUN des pays fournis, \
jamais un pays non fourni, jamais un pays manquant.
3. "relations" (allies/rivaux) : UNIQUEMENT des slugs présents dans la liste des zones \
existantes ci-dessous -- jamais un slug inventé. Beaucoup de zones n'ont logiquement \
aucune relation propre, laisse vide dans ce cas plutôt que d'en inventer.
4. Reste conservateur sur "description"/"tensions_internes" -- 2-3 lignes factuelles \
ancrées dans le patron du scénario, pas un roman.

Zones niveau 1 déjà existantes dans ce scénario (contexte, ne pas modifier) :
{{contexte_zones}}

Réponds UNIQUEMENT avec un objet JSON, sans aucun texte autour, au format exact :
{SCHEMA_JSON}"""


def _system_prompt_zone_suspecte() -> str:
    return f"""Tu es un réviseur de cohérence narrative pour un simulateur de \
worldbuilding géopolitique (Ourrassol 2098). On te donne le patron spatial narratif \
d'un scénario, une zone existante dont la description/le type ont été jugés \
incohérents avec ce patron, et la raison précise du signalement. Ta tâche : réviser \
UNIQUEMENT "description", "type", "statut", "tensions_internes" (et "relations" si la \
révision le justifie) pour aligner la zone sur le patron -- en conservant l'esprit de \
la zone (le pays/la région qu'elle couvre, son rôle général dans le scénario), pas en \
la réinventant de zéro.

Consignes strictes :
1. "slug" et "origine_reelle" : recopie EXACTEMENT ceux fournis -- ce n'est pas un \
nouveau rattachement géographique. (Ils seront de toute façon imposés mécaniquement en \
sortie, quoi que tu renvoies ici.)
2. "relations" (allies/rivaux) : UNIQUEMENT des slugs présents dans la liste des zones \
existantes ci-dessous.
3. Ne "corrige" pas plus que ce que la raison du signalement justifie -- si un seul \
aspect de la description pose problème, ne réécris pas le reste sans raison.

Zones niveau 1 existantes dans ce scénario, pour référence des relations (contexte, ne \
pas modifier) :
{{contexte_zones}}

Réponds UNIQUEMENT avec un objet JSON, sans aucun texte autour, au format exact :
{SCHEMA_JSON}"""


def _parser_reponse(texte: str) -> dict:
    """Parse la réponse JSON du LLM, tolère les fences ```json``` accidentelles.
    Lève ValueError plutôt que de retourner un résultat vide en silence --
    contrairement à C.1 (un diagnostic d'avertissement), une génération de zone
    qui échoue à parser doit être visiblement un échec pour l'appelant, jamais
    traitée comme "rien à proposer"."""
    nettoye = texte.strip()
    nettoye = re.sub(r"^```(?:json)?\s*", "", nettoye)
    nettoye = re.sub(r"\s*```$", "", nettoye)
    try:
        return json.loads(nettoye)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse LLM non-JSON : {e}\nTexte reçu (tronqué) : {texte[:500]}")


def generer_zone_topdown(scenario: str, raison: str, *, pays: list = None,
                          zone_existante: dict = None, raison_suspicion: str = None,
                          zones_existantes: list = None) -> tuple:
    """
    Fonction cœur de P24 étape C.2. Retourne (proposition: dict, issues: list) --
    issues est la sortie de validate_zone() (enrich_geographie_recursive.py),
    liste vide si structurellement valide. Ne garantit jamais la pertinence
    narrative -- jugement humain requis avant tout --apply.

    Ne touche jamais au vault. L'appelant (C.3 CLI ou C.4 GUI) fournit
    `zones_existantes` (zones niveau 1 déjà lues depuis
    geographie/{scenario}.md) et applique la proposition lui-même.

    raison == "pays_sans_zone" : `pays` requis (liste non vide de noms de pays réels).
    raison == "zone_suspecte"  : `zone_existante` et `raison_suspicion` requis.
    """
    zones_existantes = zones_existantes or []
    contexte_zones = _contexte_zones_existantes(zones_existantes)
    slugs_existants = _slugs_existants(zones_existantes)

    if raison == "pays_sans_zone":
        if not pays:
            raise ValueError("raison='pays_sans_zone' requiert `pays` (liste non vide).")
        system_prompt = _system_prompt_pays_sans_zone().replace("{contexte_zones}", contexte_zones)
        user_prompt = (
            f"{patron_spatial_prompt_block(scenario)}\n\n"
            f"Pays sans zone à couvrir : {', '.join(pays)}"
        )
    elif raison == "zone_suspecte":
        if not zone_existante or not raison_suspicion:
            raise ValueError("raison='zone_suspecte' requiert `zone_existante` et `raison_suspicion`.")
        system_prompt = _system_prompt_zone_suspecte().replace("{contexte_zones}", contexte_zones)
        user_prompt = (
            f"{patron_spatial_prompt_block(scenario)}\n\n"
            f"Zone existante à réviser :\n{json.dumps(zone_existante, ensure_ascii=False, indent=2)}\n\n"
            f"Raison du signalement (check_patron_spatial_coherence.py) :\n{raison_suspicion}"
        )
    else:
        raise ValueError(f"raison inconnue : {raison!r} (attendu 'pays_sans_zone' ou 'zone_suspecte')")

    texte = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=MAX_TOKENS,
        temperature=0.0,
        task_tier=TASK_TIER,
    )
    proposition_brute = _parser_reponse(texte)

    if raison == "pays_sans_zone":
        proposition = proposition_brute
        # Anti-collision slug : imposé mécaniquement, pas seulement demandé au prompt.
        if proposition.get("slug") in slugs_existants:
            proposition["slug"] = f"{proposition.get('slug')}_topdown"
        proposition["niveau"] = 1
        proposition["parent"] = None
        proposition.setdefault("evenement_transition", None)
        proposition.setdefault("sources_attestees", [])
        proposition.setdefault("promu_depuis", None)
    else:
        # zone_suspecte : on part de la zone existante en entier (tous les champs
        # structurels préservés par défaut), et on n'accepte du LLM que les champs
        # explicitement révisables -- imposé mécaniquement, pas seulement demandé.
        proposition = dict(zone_existante)
        champs_revisables = {"description", "type", "statut", "tensions_internes", "relations"}
        for champ in champs_revisables:
            if champ in proposition_brute:
                proposition[champ] = proposition_brute[champ]

    # Nettoyage mécanique des relations.allies/rivaux : ne garde que des slugs
    # réellement présents dans zones_existantes, jamais soi-même -- la RÈGLE
    # STRICTE du prompt (uniquement des slugs existants) n'est jamais fiable
    # seule, même leçon que le slug/origine_reelle forcés ci-dessus. Réutilise
    # clean_zone_relations() (enrich_geographie_recursive.py) plutôt que d'en
    # écrire une variante.
    all_zones_by_slug = {z.get("slug"): z for z in zones_existantes if isinstance(z, dict) and z.get("slug")}
    [proposition], dropped = clean_zone_relations(all_zones_by_slug, [proposition])
    issues = validate_zone(proposition)
    for own_slug, field, item in dropped:
        issues.append(f"relation invalide retirée : {field}={item!r} (slug inexistant, sur {own_slug!r})")
    return proposition, issues


if __name__ == "__main__":
    # Test manuel (par défaut) OU appel machine via --json (P24 étape C.4, GUI en
    # subprocess+JSON -- décision d'architecture actée le 25 juillet : le GUI
    # appelle ce script en sous-processus plutôt qu'un import direct, cohérent
    # avec le pattern déjà utilisé pour tous les scripts du sidebar). Dans les
    # deux cas : ne lit que le vault (jamais d'écriture) pour fournir un
    # contexte de zones réel.
    import argparse
    from pathlib import Path

    import yaml as _yaml

    ap = argparse.ArgumentParser(
        description="Test manuel ou appel machine (--json) de generer_zone_topdown() "
                     "(P24 étape C.2). N'écrit jamais dans le vault."
    )
    ap.add_argument("--scenario", required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pays", nargs="+", help="Mode pays_sans_zone : un ou plusieurs noms de pays.")
    mode.add_argument("--zone-suspecte", help="Mode zone_suspecte : slug de la zone existante à réviser.")
    ap.add_argument("--raison-suspicion", help="Requis avec --zone-suspecte.")
    ap.add_argument(
        "--json", action="store_true",
        help="Sortie machine : UN SEUL objet JSON sur stdout "
             "({\"ok\": true, \"proposition\": {...}, \"issues\": [...]}), rien d'autre. "
             "En cas d'erreur : {\"ok\": false, \"error\": \"...\"} sur stdout, code de "
             "sortie 1 -- jamais de traceback brute pour un appelant machine.",
    )
    args = ap.parse_args()

    def _sortie_erreur_json(message: str):
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
        raise SystemExit(1)

    vault_root = Path(__file__).resolve().parent.parent
    geo_file = vault_root / "geographie" / f"{args.scenario}.md"
    if not geo_file.exists():
        if args.json:
            _sortie_erreur_json(f"Fiche introuvable : {geo_file}")
        raise SystemExit(f"✗ Fiche introuvable : {geo_file}")

    raw = geo_file.read_text(encoding="utf-8")
    fm = _yaml.safe_load(raw.split("---", 2)[1]) or {}
    zones_n1 = [z for z in (fm.get("zones") or []) if isinstance(z, dict) and z.get("niveau", 1) == 1]

    try:
        if args.pays:
            proposition, issues = generer_zone_topdown(
                args.scenario, "pays_sans_zone", pays=args.pays, zones_existantes=zones_n1,
            )
        else:
            if not args.raison_suspicion:
                if args.json:
                    _sortie_erreur_json("--raison-suspicion est requis avec --zone-suspecte")
                ap.error("--raison-suspicion est requis avec --zone-suspecte")
            cible = next((z for z in zones_n1 if z.get("slug") == args.zone_suspecte), None)
            if not cible:
                if args.json:
                    _sortie_erreur_json(f"Zone introuvable dans {args.scenario} : {args.zone_suspecte!r}")
                ap.error(f"Zone introuvable dans {args.scenario} : {args.zone_suspecte!r}")
            proposition, issues = generer_zone_topdown(
                args.scenario, "zone_suspecte", zone_existante=cible,
                raison_suspicion=args.raison_suspicion, zones_existantes=zones_n1,
            )
    except (ImportError, EnvironmentError, RuntimeError, ValueError) as e:
        if args.json:
            _sortie_erreur_json(str(e))
        raise SystemExit(f"✗ {e}")

    if args.json:
        print(json.dumps({"ok": True, "proposition": proposition, "issues": issues}, ensure_ascii=False))
    else:
        print(json.dumps(proposition, indent=2, ensure_ascii=False))
        if issues:
            print("\n⚠ Problèmes de validation (validate_zone) :")
            for i in issues:
                print(f"  - {i}")
        else:
            print("\n✓ Validation OK (validate_zone)")
