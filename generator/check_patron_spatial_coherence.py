#!/usr/bin/env python3
"""
check_patron_spatial_coherence.py — Ourrassol 2098 (P24 étape C.1)

Diagnostic distinct des 4 scripts de scan_geographie_complet.py existants :
ceux-ci comparent une zone à sa structure de données (parenté, origine_
reelle, cohérence entre scénarios) -- jamais à la LOGIQUE NARRATIVE du
scénario lui-même. Ce script compare la description/le type de chaque zone
niveau 1 au patron spatial du scénario (patrons_spatiaux.py, P24 étape A) :
une zone peut être dans la bonne région réelle (origine_reelle correcte,
aucune incohérence détectée par check_origine_reelle_coherence.py) tout en
incarnant une logique de gouvernance/organisation incompatible avec son
scénario (ex. une mégapole hégémonique centralisée dans eco_communalism,
une institution supranationale douce dans breakdown).

Signal QUALITATIF, pas structurel -- RESTE UN AVERTISSEMENT, JAMAIS UN
BLOCAGE (même philosophie que check_conventions_territoires.py et le garde-
fou P24 étape B déjà intégré à complete_geographie_coverage.py : un taux de
faux positifs même faible sur ce type de signal rendrait un blocage
automatique risqué). Lecture seule, ne modifie jamais rien.

Comparaison faite EN LOT (un seul appel LLM par scénario, toutes les zones
N1 ensemble) plutôt qu'un appel par zone -- réduit le coût et le risque de
rate limiting sur les scénarios à beaucoup de zones N1. task_tier=
"structured_strict" (sortie JSON canonique, cf. llm_client.py).

Résultat mis en cache localement (documentation/need_action/
patron_spatial_cache.json), keyed sur un hash du contenu réellement soumis
au LLM (patron + zones) -- un rerun sans changement de zone ne repaie
jamais le même appel. Même principe que --resolve-llm dans
check_origine_reelle_coherence.py.

SUIVI DES ZONES SUSPECTES (--write-suspectes)
----------------------------------------------
Sans persistance, les mêmes avertissements réapparaîtraient à l'identique à
chaque run, sans distinguer "jamais examiné" de "déjà tranché" -- même trou
que celui comblé pour zones_manquantes.yaml. --write-suspectes écrit
documentation/need_action/patron_spatial_suspectes.yaml, une entrée par
zone suspecte (scenario, slug, raison, date_detection, statut: a_traiter
par défaut). Aux runs suivants, une zone déjà présente dans ce fichier
n'est JAMAIS réécrite ni son statut modifié par le script -- seules les
zones vraiment nouvelles sont ajoutées. Sans --write-suspectes, aperçu
seul -- rien n'est écrit.

Vocabulaire des statuts (à éditer à la main dans le fichier, comme pour
zones_manquantes.yaml) -- contrairement à P27, aucun outil n'existe encore
pour appliquer une correction : la seule action outillée possible pour une
zone suspecte est le générateur top-down (P24 étape C.2, pas encore
construit), qui prendra justement les zones suspectes de ce fichier comme
une de ses deux sources de déclenchement (l'autre étant les pays sans
zone). D'où le 4e statut ci-dessous, qui a du sens SPÉCIFIQUEMENT pour ce
fichier (aucun équivalent dans zones_manquantes.yaml) :

  a_traiter            (défaut) -- pas encore examiné.
  accepte_tel_quel     -- examiné, jugé être un choix narratif légitime
                          (réinterprétation locale du patron plutôt qu'une
                          vraie contradiction, cf. d'Iribarne/Futuribles
                          cité dans APPROCHE_ZONING_GEOGRAPHIE_SCENARIOS.md)
                          -- aucune action, comme les 8 cas P27 acceptés
                          tels quels.
  corrige_manuellement -- description/type réécrits à la main dans
                          geographie/{scenario}.md pour aligner sur le
                          patron. Pas d'outil pour ça aujourd'hui, juste
                          une édition directe du fichier.
  en_attente_c2        -- jugé être un vrai problème, mais laissé de côté
                          volontairement en attendant que le générateur
                          top-down (C.2) existe, plutôt que de corriger à
                          la main dans l'urgence.

USAGE
-----
    python3 check_patron_spatial_coherence.py --scenario eco_communalism
    python3 check_patron_spatial_coherence.py --all
    python3 check_patron_spatial_coherence.py --all --no-cache
    python3 check_patron_spatial_coherence.py --all --write-suspectes
"""

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

import yaml

from check_origine_reelle_coherence import _WIKILINK_KEY
from patrons_spatiaux import patron_spatial_prompt_block
from llm_client import call_llm

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
CACHE_FILE = VAULT_ROOT / "documentation" / "need_action" / "patron_spatial_cache.json"
SUSPECTES_FILE = VAULT_ROOT / "documentation" / "need_action" / "patron_spatial_suspectes.yaml"

# Statut par défaut d'une zone tout juste détectée -- toute autre valeur
# (mise à la main par David, ex. "accepte_tel_quel"/"corrige") signifie
# "déjà tranchée", cf. docstring du module.
STATUT_DEFAUT = "a_traiter"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

# Tronque les descriptions très longues dans le prompt -- le jugement de
# cohérence n'a pas besoin du texte intégral, et ça limite le coût sur les
# scénarios à beaucoup de zones N1.
MAX_DESCRIPTION_CHARS = 500

SYSTEM_PROMPT = """Tu es un vérificateur de cohérence narrative pour un simulateur de \
worldbuilding géopolitique. On te donne le patron spatial attendu d'un scénario, et la \
liste des zones de premier niveau qui existent dans ce scénario. Ta tâche : repérer les \
zones dont la description ou le type contredit clairement le patron spatial -- pas les \
zones qui l'illustrent imparfaitement ou n'en disent simplement pas assez pour juger.

Sois conservateur : en cas de doute réel, NE PAS signaler. Un faux positif coûte plus \
cher qu'un faux négatif ici -- ce diagnostic sert d'avertissement consulté par un humain, \
jamais de blocage automatique.

Réponds UNIQUEMENT avec un objet JSON, sans aucun texte avant ou après, au format exact :
{"zones_suspectes": [{"slug": "...", "raison": "phrase courte expliquant la contradiction"}]}

Si aucune zone n'est suspecte, réponds {"zones_suspectes": []}."""


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} : frontmatter YAML mal formé.")
    fm_raw = _WIKILINK_KEY.sub(r'"\1"', parts[1])
    return yaml.safe_load(fm_raw) or {}


def _zones_n1(fm: dict) -> list:
    return [
        z for z in (fm.get("zones") or [])
        if isinstance(z, dict) and z.get("niveau", 1) == 1
    ]


def _origine_reelle_resume(zone: dict) -> str:
    entites = [
        o.get("entite", "") for o in (zone.get("origine_reelle") or [])
        if isinstance(o, dict) and o.get("entite")
    ]
    return ", ".join(entites) if entites else "(non renseignée)"


# En dessous de ce nombre de caractères, une description est traitée comme
# absente -- pas assez de matière pour juger une contradiction narrative.
# Trouvé nécessaire le 25 juillet : nouveau_califat_barcelone (new_sustainability)
# flaguée par le LLM sur la seule base du nom/type, faute de description,
# malgré la consigne "en cas de doute réel, NE PAS signaler" -- un placeholder
# "(non renseignée)" laissait encore la porte ouverte à une spéculation nom/
# type. Exclure ces zones EN AMONT est plus fiable qu'une consigne seule.
MIN_DESCRIPTION_CHARS = 20


def _zones_pour_prompt(zones: list) -> tuple:
    """Représentation compacte des zones N1 à soumettre au LLM. Retourne
    (zones_evaluables, zones_sans_description) -- ces dernières ne sont
    jamais envoyées au LLM, faute de matière suffisante pour juger une
    contradiction narrative (voir MIN_DESCRIPTION_CHARS ci-dessus)."""
    evaluables, sans_description = [], []
    for z in zones:
        description = (z.get("description") or "").strip()
        slug = z.get("slug", "?")
        if len(description) < MIN_DESCRIPTION_CHARS:
            sans_description.append(slug)
            continue
        evaluables.append({
            "slug": slug,
            "nom": z.get("nom", "?"),
            "type": z.get("type", "(non renseigné)"),
            "description": description[:MAX_DESCRIPTION_CHARS],
            "origine_reelle": _origine_reelle_resume(z),
        })
    return evaluables, sans_description


def _hash_appel(scenario: str, zones_prompt: list) -> str:
    """Hash du contenu réellement soumis au LLM (patron + zones) -- sert de clé de
    cache. Change dès qu'une description/type de zone change, ou que l'analyse du
    patron (patrons_spatiaux.py) évolue -- pas de faux cache-hit silencieux."""
    payload = json.dumps(
        {
            "scenario": scenario,
            "patron": patron_spatial_prompt_block(scenario),
            "zones": zones_prompt,
        },
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _charger_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _sauver_cache(cache: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def _charger_suspectes_existantes() -> dict:
    """Charge le fichier de suivi, keyed (scenario, slug) -> entrée complète.
    Lecture seule -- ne rien modifier ici, seul _ecrire_suspectes() écrit,
    et seulement pour des entrées vraiment nouvelles (voir plus bas)."""
    if not SUSPECTES_FILE.exists():
        return {}
    try:
        data = yaml.safe_load(SUSPECTES_FILE.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    entrees = data.get("zones_suspectes") or []
    return {
        (e.get("scenario"), e.get("slug")): e
        for e in entrees if isinstance(e, dict) and e.get("scenario") and e.get("slug")
    }


def _ecrire_suspectes(existantes: dict, nouvelles: list) -> int:
    """Ajoute au fichier de suivi les zones suspectes qui n'y sont pas déjà --
    ne touche JAMAIS une entrée existante (statut compris), pour ne jamais
    écraser une décision prise à la main par David. Retourne le nombre
    d'entrées effectivement ajoutées (0 si tout était déjà suivi)."""
    toutes = dict(existantes)
    ajoutees = 0
    aujourd_hui = datetime.date.today().isoformat()
    for n in nouvelles:
        cle = (n["scenario"], n["slug"])
        if cle in toutes:
            continue
        toutes[cle] = {
            "scenario": n["scenario"],
            "slug": n["slug"],
            "raison": n["raison"],
            "date_detection": aujourd_hui,
            "statut": STATUT_DEFAUT,
        }
        ajoutees += 1

    if ajoutees:
        SUSPECTES_FILE.parent.mkdir(parents=True, exist_ok=True)
        sortie = {"zones_suspectes": list(toutes.values())}
        SUSPECTES_FILE.write_text(
            yaml.safe_dump(sortie, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
    return ajoutees


def _parser_reponse_llm(texte: str) -> list:
    """Parse la réponse JSON du LLM, tolère des fences ```json``` accidentelles.
    Ne lève jamais d'exception -- une réponse malformée ne doit jamais planter le
    scan complet, juste ne rien signaler pour ce scénario (avertissement, pas
    bloquant, cf. docstring du module)."""
    nettoye = texte.strip()
    if nettoye.startswith("```"):
        nettoye = nettoye.split("```")[1]
        if nettoye.startswith("json"):
            nettoye = nettoye[4:]
        nettoye = nettoye.strip()
    try:
        data = json.loads(nettoye)
    except json.JSONDecodeError:
        print("  ✗ Réponse LLM non-JSON, ignorée pour ce scénario")
        return []
    zones_suspectes = data.get("zones_suspectes")
    if not isinstance(zones_suspectes, list):
        return []
    return [
        z for z in zones_suspectes
        if isinstance(z, dict) and z.get("slug") and z.get("raison")
    ]


def check_scenario(scenario: str, cache: dict, use_cache: bool, suspectes_existantes: dict) -> dict:
    print(f"\n=== {scenario} ===")
    geo_file = GEO_DIR / f"{scenario}.md"
    if not geo_file.exists():
        print(f"  ✗ Fiche introuvable : {geo_file}")
        return {"actives": [], "deja_traitees": []}

    try:
        fm = _read_frontmatter(geo_file)
    except (ValueError, yaml.YAMLError) as e:
        print(f"  ✗ ERREUR DE PARSING YAML : {e}")
        return {"actives": [], "deja_traitees": []}

    zones = _zones_n1(fm)
    if not zones:
        print("  · Aucune zone niveau 1 -- rien à comparer")
        return {"actives": [], "deja_traitees": []}

    zones_prompt, sans_description = _zones_pour_prompt(zones)
    if sans_description:
        print(f"  · {len(sans_description)} zone(s) sans description exploitable, "
              f"exclue(s) du jugement (pas assez de matière) : {', '.join(sans_description)}")
    if not zones_prompt:
        print("  · Aucune zone évaluable après filtrage -- rien à comparer")
        return {"actives": [], "deja_traitees": []}

    cle_cache = _hash_appel(scenario, zones_prompt)

    if use_cache and cle_cache in cache:
        print(f"  · {len(zones_prompt)} zone(s) évaluable(s) -- résultat en cache, aucun appel LLM")
        zones_suspectes = cache[cle_cache]
    else:
        print(f"  · {len(zones_prompt)} zone(s) évaluable(s) -- appel LLM en cours...")
        user_prompt = (
            f"{patron_spatial_prompt_block(scenario)}\n\n"
            f"Zones niveau 1 du scénario '{scenario}' à évaluer :\n"
            f"{json.dumps(zones_prompt, indent=2, ensure_ascii=False)}"
        )
        try:
            reponse = call_llm(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=1500,
                temperature=0.0,
                task_tier="structured_strict",
            )
        except (ImportError, EnvironmentError, RuntimeError) as e:
            print(f"  ✗ Appel LLM impossible : {e}")
            return {"actives": [], "deja_traitees": []}
        zones_suspectes = _parser_reponse_llm(reponse)
        cache[cle_cache] = zones_suspectes

    if not zones_suspectes:
        print("  ✓ Aucune zone suspecte")
        return {"actives": [], "deja_traitees": []}

    slugs_connus = {z["slug"] for z in zones_prompt}
    actives, deja_traitees = [], []
    for zs in zones_suspectes:
        if zs["slug"] not in slugs_connus:
            continue  # slug halluciné par le LLM, ignoré silencieusement
        entree = {"scenario": scenario, "slug": zs["slug"], "raison": zs["raison"]}
        suivi = suspectes_existantes.get((scenario, zs["slug"]))
        if suivi and suivi.get("statut") != STATUT_DEFAUT:
            print(f"  · {zs['slug']} -- déjà tranchée (statut : {suivi.get('statut')})")
            deja_traitees.append(entree)
        else:
            print(f"  ⚠ {zs['slug']} -- {zs['raison']}")
            actives.append(entree)
    return {"actives": actives, "deja_traitees": deja_traitees}


def main():
    parser = argparse.ArgumentParser(
        description="Compare la description/le type de chaque zone niveau 1 au patron "
                     "spatial narratif de son scénario (P24 étape C.1). Avertissement "
                     "seul, jamais de blocage, ne modifie jamais rien dans geographie/."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", help="Scénario unique")
    group.add_argument("--all", action="store_true", help="Les 6 scénarios")
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Ignore le cache local et repaie un appel LLM pour chaque scénario.",
    )
    parser.add_argument(
        "--write-suspectes", action="store_true",
        help="Écrit les zones suspectes nouvelles dans patron_spatial_suspectes.yaml "
             "(statut a_traiter). N'écrase jamais une entrée déjà présente. Sans ce "
             "flag, aperçu seul.",
    )
    args = parser.parse_args()

    scenarios = SCENARIOS if args.all else [args.scenario]
    if args.scenario and args.scenario not in SCENARIOS:
        print(f"✗ Scénario inconnu : {args.scenario}")
        print(f"  Scénarios valides : {', '.join(SCENARIOS)}")
        sys.exit(1)

    print("=" * 60)
    print("  Cohérence patron spatial — geographie/{scenario}.md vs patrons_spatiaux.py")
    print("=" * 60)

    cache = {} if args.no_cache else _charger_cache()
    use_cache = not args.no_cache
    suspectes_existantes = _charger_suspectes_existantes()

    toutes_actives, toutes_deja_traitees = [], []
    for s in scenarios:
        r = check_scenario(s, cache, use_cache, suspectes_existantes)
        toutes_actives += r["actives"]
        toutes_deja_traitees += r["deja_traitees"]

    if not args.no_cache:
        _sauver_cache(cache)

    nouvelles_pour_fichier = [
        e for e in toutes_actives
        if (e["scenario"], e["slug"]) not in suspectes_existantes
    ]
    if args.write_suspectes:
        ajoutees = _ecrire_suspectes(suspectes_existantes, nouvelles_pour_fichier)
        if ajoutees:
            print(f"\n  ✓ {ajoutees} nouvelle(s) entrée(s) ajoutée(s) à {SUSPECTES_FILE} "
                  f"(statut: {STATUT_DEFAUT})")
        else:
            print(f"\n  · Aucune nouvelle entrée -- {SUSPECTES_FILE} déjà à jour")
    elif nouvelles_pour_fichier:
        print(f"\n  · {len(nouvelles_pour_fichier)} zone(s) suspecte(s) pas encore suivie(s). "
              f"Relancer avec --write-suspectes pour les ajouter à {SUSPECTES_FILE} (aperçu) :")
        for e in nouvelles_pour_fichier:
            print(f"      - {e['slug']!r} ({e['scenario']})")

    print("\n" + "=" * 60)
    if toutes_actives:
        print(f"  Terminé — {len(toutes_actives)} zone(s) suspecte(s) active(s) "
              f"(avertissement, aucune modification effectuée).")
        if toutes_deja_traitees:
            print(f"  ({len(toutes_deja_traitees)} zone(s) supplémentaire(s) déjà tranchée(s), "
                  f"voir statut dans {SUSPECTES_FILE.name})")
    elif toutes_deja_traitees:
        print(f"  Terminé — aucune zone suspecte active, "
              f"{len(toutes_deja_traitees)} déjà tranchée(s).")
    else:
        print("  Terminé — aucune zone suspecte détectée.")
    print("=" * 60)


if __name__ == "__main__":
    main()
