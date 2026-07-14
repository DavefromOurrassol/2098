#!/usr/bin/env python3
"""
check_conventions_territoires.py — Ourrassol 2098

Diagnostic distinct de check_origine_reelle_coherence.py : ne compare pas
une zone à sa chaîne de parenté, mais audite, POUR UN MÊME SCÉNARIO,
comment un territoire ambigu (dépendance/collectivité pouvant être cité
seul OU implicitement via son pays souverain réel) est revendiqué à
travers TOUTES les zones N1 -- pas seulement la chaîne d'une zone
incohérente.

Cas qui a motivé ce script (14 juillet 2026) : dans policy_reform, le
Groenland est revendiqué par `espace_eurasiatique` (bloc technocratique
russo-chinois, aucune mention d'Arctique/Groenland dans sa description),
alors que `europe_nord_ouest` (Pays-Bas, Belgique, Danemark, Norvège,
Suède, Islande...) est un bien meilleur candidat narratif ET revendique
déjà le Danemark. check_origine_reelle_coherence.py n'aurait jamais
détecté ça seul : espace_eurasiatique EST dans la liste de référence,
syntaxiquement la revendication est valide. Seule une comparaison entre
zones du MÊME scénario, pas juste la chaîne d'ascendance d'une zone
donnée, révèle l'incohérence.

RESTE UN AVERTISSEMENT, JAMAIS UN BLOCAGE : la décision finale (laisser
tel quel, migrer la revendication) est narrative, pas mécanique. Lecture
seule, ne modifie jamais rien.

Table TERRITOIRES_AMBIGUS à enrichir manuellement au fil de l'eau, comme
VILLE_PAYS dans check_origine_reelle_coherence.py -- un territoire absent
de la table est simplement invisible pour ce diagnostic, jamais une fausse
alerte.

USAGE
-----
    python3 check_conventions_territoires.py --all
    python3 check_conventions_territoires.py --scenario policy_reform
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

from check_origine_reelle_coherence import _tokens, _normaliser, _compte_comme_pays, _WIKILINK_KEY

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
GUI_DIR = VAULT_ROOT / "gui"
ZONES_PAYS = GUI_DIR / "zones_pays.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

# territoire ambigu -> pays souverain réel. À enrichir manuellement -- un
# territoire absent d'ici est simplement invisible pour ce diagnostic.
TERRITOIRES_AMBIGUS = {
    "groenland": "danemark",
    "polynésie française": "france",
    "nouvelle-calédonie": "france",
    "guyane française": "france",
    "écosse": "royaume-uni",
    "pays de galles": "royaume-uni",
}


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} : frontmatter YAML mal formé.")
    fm_raw = _WIKILINK_KEY.sub(r'"\1"', parts[1])
    return yaml.safe_load(fm_raw) or {}


def _zones_n1_revendiquant(zones: list, cible_norm: str, pays_liste_norm: set) -> list:
    """Slugs des zones N1 dont l'origine_reelle revendique `cible_norm`
    (territoire ou souverain), tous type_entite tolérés comme dans
    check_origine_reelle_coherence.py (voir _compte_comme_pays)."""
    resultat = []
    for z in zones:
        if not isinstance(z, dict) or z.get("niveau", 1) != 1:
            continue
        for o in (z.get("origine_reelle") or []):
            if not isinstance(o, dict):
                continue
            if not _compte_comme_pays(o, pays_liste_norm):
                continue
            for tok in _tokens(o.get("entite") or ""):
                if _normaliser(tok) == cible_norm:
                    resultat.append(z.get("slug"))
                    break
    return resultat


def check_scenario(scenario: str, pays_liste_norm: set) -> dict:
    print(f"\n=== {scenario} ===")
    geo_file = GEO_DIR / f"{scenario}.md"
    if not geo_file.exists():
        print(f"  ✗ Fiche introuvable : {geo_file}")
        return {}

    try:
        fm = _read_frontmatter(geo_file)
    except (ValueError, yaml.YAMLError) as e:
        print(f"  ✗ ERREUR DE PARSING YAML : {e}")
        return {}

    zones = fm.get("zones") or []
    statuts = {}  # territoire -> "identique" | "distinct" | "convention_implicite" | "absent"

    for territoire, souverain in TERRITOIRES_AMBIGUS.items():
        zones_territoire = _zones_n1_revendiquant(zones, territoire, pays_liste_norm)
        zones_souverain = _zones_n1_revendiquant(zones, souverain, pays_liste_norm)

        if not zones_territoire and not zones_souverain:
            statuts[territoire] = "absent"
            continue

        if not zones_territoire:
            print(f"  · {territoire.capitalize()} : absent, seul {souverain} présent "
                  f"({', '.join(zones_souverain)}) -- convention implicite")
            statuts[territoire] = "convention_implicite"
            continue

        if set(zones_territoire) == set(zones_souverain):
            print(f"  ✓ {territoire.capitalize()} et {souverain} : même zone "
                  f"({', '.join(zones_territoire)})")
            statuts[territoire] = "identique"
            continue

        print(f"  · {territoire.capitalize()} → {', '.join(zones_territoire) or 'aucune'} "
              f"/ {souverain.capitalize()} → {', '.join(zones_souverain) or 'aucune'} "
              f"-- zones distinctes")
        statuts[territoire] = "distinct"

    return statuts


def main():
    parser = argparse.ArgumentParser(
        description="Audite la cohérence de revendication des territoires ambigus "
                     "(dépendances/collectivités) entre zones d'un même scénario."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", help="Scénario unique")
    group.add_argument("--all", action="store_true", help="Les 6 scénarios")
    args = parser.parse_args()

    if not ZONES_PAYS.exists():
        print(f"✗ {ZONES_PAYS} introuvable.")
        sys.exit(1)
    zones_pays = json.loads(ZONES_PAYS.read_text(encoding="utf-8"))
    pays_liste_norm = {p.lower().strip() for p in zones_pays.get("pays_liste", [])}

    scenarios = SCENARIOS if args.all else [args.scenario]
    if args.scenario and args.scenario not in SCENARIOS:
        print(f"✗ Scénario inconnu : {args.scenario}")
        sys.exit(1)

    print("=" * 60)
    print("  Cohérence des territoires ambigus — geographie/{scenario}.md")
    print("=" * 60)

    statuts_par_scenario = {}
    for s in scenarios:
        statuts_par_scenario[s] = check_scenario(s, pays_liste_norm)

    # ── Agrégation : un territoire n'est un vrai signal que si son statut
    # VARIE entre scénarios. "Toujours distinct" ou "toujours identique"
    # sur tous les scénarios où il apparaît est un choix narratif stable,
    # pas une incohérence -- voir Polynésie française, distincte de la
    # France dans les 6/6 scénarios où elle apparaît : voulu, pas un bug.
    territoires_varie = []
    for territoire in TERRITOIRES_AMBIGUS:
        vus = {
            s: statuts_par_scenario[s].get(territoire)
            for s in scenarios if statuts_par_scenario.get(s)
        }
        statuts_significatifs = {v for v in vus.values() if v in ("identique", "distinct")}
        if len(statuts_significatifs) > 1:
            territoires_varie.append((territoire, vus))

    print("\n" + "=" * 60)
    print("  RÉSUMÉ — territoires dont le traitement VARIE entre scénarios")
    print("=" * 60)
    if not territoires_varie:
        print("  ✓ Aucun -- chaque territoire suivi est traité de façon stable "
              "à travers tous les scénarios où il apparaît.")
    else:
        for territoire, vus in territoires_varie:
            print(f"\n  ⚠ {territoire.capitalize()} (souverain réel : "
                  f"{TERRITOIRES_AMBIGUS[territoire]})")
            for s, statut in vus.items():
                if statut in ("identique", "distinct"):
                    print(f"      {s:<20} {statut}")

    print("\n" + "=" * 60)
    if territoires_varie:
        print(f"  Terminé — {len(territoires_varie)} territoire(s) au traitement "
              f"incohérent entre scénarios (voir résumé ci-dessus).")
    else:
        print("  Terminé — tout est cohérent.")
    print("=" * 60)


if __name__ == "__main__":
    main()
