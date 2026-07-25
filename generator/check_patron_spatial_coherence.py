#!/usr/bin/env python3
"""
check_patron_spatial_coherence.py — Ourrassol 2098 (P24 étape C.1)

Diagnostic distinct des 4 autres scripts de scan_geographie_complet.py :
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
BLOCAGE. Lecture seule sur geographie/, ne modifie jamais une fiche.

Comparaison faite EN LOT (un seul appel LLM par scénario, toutes les zones
N1 ensemble). task_tier="structured_strict". Résultat mis en cache
localement (documentation/need_action/patron_spatial_cache.json), keyed
sur un hash du contenu réellement soumis au LLM.

SUIVI (--write-chantiers)
--------------------------
Depuis le 25 juillet 2026, le suivi passe par le module partagé
chantiers.py -- chantiers_geographie.yaml, UN SEUL fichier pour tout le
pipeline géographie (remplace l'ancien patron_spatial_suspectes.yaml,
propre à ce script). --write-chantiers ajoute chaque zone suspecte comme
un chantier type="zone_suspecte" (statut a_traiter par défaut). N'écrase
jamais une entrée déjà présente -- voir chantiers.py pour le détail des
statuts (a_traiter / ignore / traite).

USAGE
-----
    python3 check_patron_spatial_coherence.py --scenario eco_communalism
    python3 check_patron_spatial_coherence.py --all
    python3 check_patron_spatial_coherence.py --all --no-cache
    python3 check_patron_spatial_coherence.py --all --write-chantiers
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

from check_origine_reelle_coherence import _WIKILINK_KEY
from patrons_spatiaux import patron_spatial_prompt_block
from llm_client import call_llm
import chantiers

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
CACHE_FILE = VAULT_ROOT / "documentation" / "need_action" / "patron_spatial_cache.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

# Tronque les descriptions très longues dans le prompt.
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
# absente -- évite qu'une zone sans contenu réel soit jugée sur son nom/type
# seul (cas réel : nouveau_califat_barcelone, 25 juillet 2026).
MIN_DESCRIPTION_CHARS = 20


def _zones_pour_prompt(zones: list) -> tuple:
    """Retourne (zones_evaluables, zones_sans_description)."""
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


def _parser_reponse_llm(texte: str) -> list:
    """Tolère les fences ```json``` accidentelles. Ne lève jamais d'exception --
    une réponse malformée ne doit jamais planter le scan complet."""
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


def check_scenario(scenario: str, cache: dict, use_cache: bool) -> dict:
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
        entree = {"scenario": scenario, "cible": zs["slug"], "probleme": zs["raison"]}
        suivi = chantiers.get_chantier(scenario, zs["slug"])
        if suivi and suivi.get("statut") != chantiers.STATUT_DEFAUT:
            print(f"  · {zs['slug']} -- déjà tranché (statut : {suivi.get('statut')})")
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
        "--write-chantiers", action="store_true",
        help="Ajoute les zones suspectes nouvelles à chantiers_geographie.yaml "
             "(statut a_traiter). N'écrase jamais une entrée déjà présente. Sans "
             "ce flag, aperçu seul.",
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

    toutes_actives, toutes_deja_traitees = [], []
    for s in scenarios:
        r = check_scenario(s, cache, use_cache)
        toutes_actives += r["actives"]
        toutes_deja_traitees += r["deja_traitees"]

    if not args.no_cache:
        _sauver_cache(cache)

    if args.write_chantiers:
        ajoutees = 0
        for e in toutes_actives:
            if chantiers.ajouter_chantier(
                scenario=e["scenario"], type_="zone_suspecte", cible=e["cible"],
                probleme=e["probleme"], source_diagnostic="patron_spatial",
            ):
                ajoutees += 1
        if ajoutees:
            print(f"\n  ✓ {ajoutees} nouveau(x) chantier(s) ajouté(s) à "
                  f"{chantiers.CHANTIERS_FILE} (statut: {chantiers.STATUT_DEFAUT})")
        else:
            print(f"\n  · Aucun nouveau chantier -- {chantiers.CHANTIERS_FILE} déjà à jour")
    elif toutes_actives:
        print(f"\n  · {len(toutes_actives)} zone(s) suspecte(s) pas encore vérifiée(s) "
              f"comme suivie(s). Relancer avec --write-chantiers pour les ajouter à "
              f"{chantiers.CHANTIERS_FILE.name} :")
        for e in toutes_actives:
            print(f"      - {e['cible']!r} ({e['scenario']})")

    print("\n" + "=" * 60)
    if toutes_actives:
        print(f"  Terminé — {len(toutes_actives)} zone(s) suspecte(s) active(s) "
              f"(avertissement, aucune modification effectuée).")
        if toutes_deja_traitees:
            print(f"  ({len(toutes_deja_traitees)} zone(s) supplémentaire(s) déjà tranchée(s), "
                  f"voir statut dans {chantiers.CHANTIERS_FILE.name})")
    elif toutes_deja_traitees:
        print(f"  Terminé — aucune zone suspecte active, "
              f"{len(toutes_deja_traitees)} déjà tranchée(s).")
    else:
        print("  Terminé — aucune zone suspecte détectée.")
    print("=" * 60)


if __name__ == "__main__":
    main()
