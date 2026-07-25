#!/usr/bin/env python3
"""
generer_zones_topdown.py — Ourrassol 2098 (P24 étape C.3)

CLI batch pour le générateur top-down (C.2, zoning_topdown.py) : détecte les
cas à traiter (pays sans zone + zones suspectes non résolues), génère une
proposition pour chacun, écrit un YAML de review, puis applique les
propositions validées à la main. Même workflow --review/--apply que le
reste du pipeline (coverage_proposals_{scenario}.yaml,
zones_manquantes.yaml, etc.) : rien n'est jamais écrit dans le vault sans
un passage humain explicite entre review et apply.

DEUX SOURCES DE CAS (P24 étape C, périmètre acté le 25 juillet -- les deux
dès le départ) :

  1. Pays sans zone -- même détection que check_zones_coherence.py
     (_pays_present, réutilisée par import). Un pays orphelin = une
     proposition de zone niveau 1 générée de zéro. PAS de regroupement
     automatique de plusieurs pays orphelins dans une même zone -- décision
     éditoriale, à faire à la main en fusionnant deux entrées du YAML de
     review si tu le souhaites.

  2. Zones suspectes -- lues depuis patron_spatial_suspectes.yaml (C.1),
     statut "a_traiter" OU "en_attente_c2" (ce dernier existait justement
     pour "attendre que C.2 existe" -- maintenant que C.2/C.3 existent,
     ces entrées deviennent éligibles). "accepte_tel_quel" et
     "corrige_manuellement" restent définitivement exclus (déjà tranchés).

ÉCRITURE (--apply-topdown) : duplique consciemment la logique d'écriture
de carte_creer_zone_niveau1()/zones_pays.json (gui/app.py) pour le cas
pays_sans_zone -- generator/ et gui/ restent deux codebases séparées, sans
import croisé (point de vigilance déjà établi pour _tokens_entite() dans
app.py). Pour le cas zone_suspecte, écrit une modification en place
(aucune route GUI équivalente n'existe encore) et met à jour le statut de
l'entrée correspondante dans patron_spatial_suspectes.yaml vers
"corrige_via_c2" (nouveau statut, distinct de "corrige_manuellement" --
celui-ci est généré puis validé humainement, pas tapé à la main).

USAGE
-----
    python3 generer_zones_topdown.py --review-topdown --scenario new_sustainability
    python3 generer_zones_topdown.py --review-topdown --all
    python3 generer_zones_topdown.py --review-topdown --all --source pays_sans_zone
    python3 generer_zones_topdown.py --review-topdown --all --source zones_suspectes
    python3 generer_zones_topdown.py --apply-topdown --scenario new_sustainability
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

from check_zones_coherence import _pays_present, ALIASES
from zoning_topdown import generer_zone_topdown

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
GUI_DIR = VAULT_ROOT / "gui"
ZONES_PAYS = GUI_DIR / "zones_pays.json"
NEED_ACTION = VAULT_ROOT / "documentation" / "need_action"
SUSPECTES_FILE = NEED_ACTION / "patron_spatial_suspectes.yaml"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

STATUTS_ELIGIBLES_ZONE_SUSPECTE = {"a_traiter", "en_attente_c2"}
STATUT_APRES_APPLY = "corrige_via_c2"


def _review_file(scenario: str) -> Path:
    return NEED_ACTION / f"zones_proposees_topdown_{scenario}.yaml"


# ---------------------------------------------------------------------------
# Lecture du vault (lecture seule)
# ---------------------------------------------------------------------------

def _lire_geo(scenario: str) -> tuple:
    """Retourne (fm complet, liste zones, chemin fichier). Lève FileNotFoundError
    si la fiche n'existe pas -- laissé remonter volontairement, l'appelant décide."""
    geo_file = GEO_DIR / f"{scenario}.md"
    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{geo_file} : frontmatter YAML mal formé.")
    fm = yaml.safe_load(parts[1]) or {}
    return fm, fm.get("zones") or [], geo_file


def _zones_n1(zones: list) -> list:
    return [z for z in zones if isinstance(z, dict) and z.get("niveau", 1) == 1]


def _pays_sans_zone(scenario: str, pays_liste_original: list) -> list:
    """Même définition que check_zones_coherence.py (étape 2 de son diagnostic) :
    un pays est orphelin s'il n'apparaît dans AUCUNE zone, tous niveaux confondus."""
    _, zones, _ = _lire_geo(scenario)
    entites_toutes = [
        o.get("entite", "") for z in zones
        for o in (z.get("origine_reelle") or [])
        if isinstance(o, dict) and o.get("entite")
    ]
    return [
        p for p in pays_liste_original
        if not _pays_present(p.lower().strip(), entites_toutes)
    ]


def _charger_suspectes() -> list:
    if not SUSPECTES_FILE.exists():
        return []
    try:
        data = yaml.safe_load(SUSPECTES_FILE.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    return data.get("zones_suspectes") or []


def _zones_suspectes_eligibles(scenario: str) -> list:
    """Entrées de patron_spatial_suspectes.yaml pour ce scénario, statut éligible
    (a_traiter ou en_attente_c2), avec la zone complète correspondante attachée
    (None si la zone a disparu du vault depuis -- ignorée, pas plantée)."""
    _, zones, _ = _lire_geo(scenario)
    zones_par_slug = {z.get("slug"): z for z in _zones_n1(zones)}
    resultat = []
    for e in _charger_suspectes():
        if e.get("scenario") != scenario:
            continue
        if e.get("statut") not in STATUTS_ELIGIBLES_ZONE_SUSPECTE:
            continue
        zone = zones_par_slug.get(e.get("slug"))
        if zone is None:
            print(f"  · {e.get('slug')!r} suivi dans patron_spatial_suspectes.yaml "
                  f"mais introuvable dans {scenario} -- ignoré")
            continue
        resultat.append((e, zone))
    return resultat


# ---------------------------------------------------------------------------
# --review-topdown
# ---------------------------------------------------------------------------

def reviewer_scenario(scenario: str, source: str) -> int:
    print(f"\n=== {scenario} ===")
    if not ZONES_PAYS.exists():
        print(f"  ✗ {ZONES_PAYS} introuvable.")
        return 0
    zones_pays = json.loads(ZONES_PAYS.read_text(encoding="utf-8"))
    pays_liste_original = zones_pays.get("pays_liste", [])

    try:
        _, zones, _ = _lire_geo(scenario)
    except (FileNotFoundError, ValueError) as e:
        print(f"  ✗ {e}")
        return 0
    zones_n1 = _zones_n1(zones)

    entrees_yaml = []

    if source in ("pays_sans_zone", "both"):
        orphelins = _pays_sans_zone(scenario, pays_liste_original)
        print(f"  · {len(orphelins)} pays sans zone")
        for pays in orphelins:
            print(f"    - génération pour {pays!r}...")
            try:
                proposition, issues = generer_zone_topdown(
                    scenario, "pays_sans_zone", pays=[pays], zones_existantes=zones_n1,
                )
            except (ImportError, EnvironmentError, RuntimeError, ValueError) as e:
                print(f"      ✗ échec de génération : {e}")
                continue
            entrees_yaml.append({
                "scenario": scenario, "raison": "pays_sans_zone", "cible": pays,
                "issues": issues, "valide": False, "proposition": proposition,
            })
            if issues:
                print(f"      ⚠ {len(issues)} problème(s) de validation, à relire attentivement")

    if source in ("zones_suspectes", "both"):
        eligibles = _zones_suspectes_eligibles(scenario)
        print(f"  · {len(eligibles)} zone(s) suspecte(s) éligible(s) (a_traiter/en_attente_c2)")
        for entree_suivi, zone in eligibles:
            print(f"    - révision pour {zone.get('slug')!r}...")
            try:
                proposition, issues = generer_zone_topdown(
                    scenario, "zone_suspecte", zone_existante=zone,
                    raison_suspicion=entree_suivi.get("raison", ""),
                    zones_existantes=zones_n1,
                )
            except (ImportError, EnvironmentError, RuntimeError, ValueError) as e:
                print(f"      ✗ échec de génération : {e}")
                continue
            entrees_yaml.append({
                "scenario": scenario, "raison": "zone_suspecte", "cible": zone.get("slug"),
                "issues": issues, "valide": False, "proposition": proposition,
            })
            if issues:
                print(f"      ⚠ {len(issues)} problème(s) de validation, à relire attentivement")

    if not entrees_yaml:
        print("  ✓ Rien à proposer")
        return 0

    review_file = _review_file(scenario)
    review_file.parent.mkdir(parents=True, exist_ok=True)
    review_file.write_text(
        yaml.safe_dump({"propositions": entrees_yaml}, allow_unicode=True,
                        sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"  ✓ {len(entrees_yaml)} proposition(s) écrite(s) dans {review_file}")
    print(f"    (valide: false par défaut -- relire et passer à true avant --apply-topdown)")
    return len(entrees_yaml)


# ---------------------------------------------------------------------------
# --apply-topdown
# ---------------------------------------------------------------------------

def _appliquer_pays_sans_zone(scenario: str, proposition: dict) -> None:
    """Duplique consciemment la logique d'écriture de carte_creer_zone_niveau1()
    + de la synchronisation zones_pays.json (gui/app.py) -- generator/ et gui/
    restent deux codebases séparées, sans import croisé (point de vigilance
    établi)."""
    fm, zones, geo_file = _lire_geo(scenario)
    slug = proposition["slug"]
    if any(z.get("slug") == slug for z in zones):
        raise ValueError(f"slug {slug!r} existe déjà dans {scenario} -- collision, "
                          f"pas appliqué (relance --review-topdown pour régénérer)")

    raw = geo_file.read_text(encoding="utf-8")
    bak = geo_file.with_suffix(geo_file.suffix + ".bak")
    bak.write_text(raw, encoding="utf-8")

    zones.append(proposition)
    fm["zones"] = zones
    parts = raw.split("---", 2)
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    new_body = parts[2].rstrip("\n") + f"\n\n### {proposition['nom']}\n{proposition.get('description', '')}\n"
    geo_file.write_text("---\n" + new_fm + "---" + new_body, encoding="utf-8")

    # Synchronisation zones_pays.json -- même principe que _creer_zone_in_zones_pays
    # (gui/app.py), dupliqué ici pour la même raison de séparation de codebase.
    if ZONES_PAYS.exists():
        zp = json.loads(ZONES_PAYS.read_text(encoding="utf-8"))
        pays_liste = zp.get("pays_liste", [])
        index_norm = {p.lower().strip(): p for p in pays_liste}
        sc = zp.get(scenario, {})
        touches = []
        for o in proposition.get("origine_reelle") or []:
            if not isinstance(o, dict) or o.get("type_entite") != "pays":
                continue
            pays_canonique = index_norm.get((o.get("entite") or "").lower().strip())
            if pays_canonique:
                sc[pays_canonique] = slug
                touches.append(pays_canonique)
        if touches:
            zp[scenario] = sc
            ZONES_PAYS.write_text(json.dumps(zp, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"    ✓ zones_pays.json synchronisé pour : {', '.join(touches) or '(aucun pays reconnu)'}")


def _appliquer_zone_suspecte(scenario: str, proposition: dict) -> None:
    """Modifie EN PLACE la zone existante (mêmes champs que zoning_topdown.py
    autorise à réviser : description/type/statut/tensions_internes/relations --
    le reste vient déjà identique de la proposition, mais on ne réécrit que ce
    qui a changé pour un diff minimal). Marque l'entrée correspondante dans
    patron_spatial_suspectes.yaml comme "corrige_via_c2"."""
    fm, zones, geo_file = _lire_geo(scenario)
    slug = proposition["slug"]
    idx = next((i for i, z in enumerate(zones) if isinstance(z, dict) and z.get("slug") == slug), None)
    if idx is None:
        raise ValueError(f"slug {slug!r} introuvable dans {scenario} -- pas appliqué "
                          f"(la zone a peut-être été renommée/supprimée depuis --review-topdown)")

    raw = geo_file.read_text(encoding="utf-8")
    bak = geo_file.with_suffix(geo_file.suffix + ".bak")
    bak.write_text(raw, encoding="utf-8")

    champs_revisables = ("description", "type", "statut", "tensions_internes", "relations")
    for champ in champs_revisables:
        zones[idx][champ] = proposition.get(champ, zones[idx].get(champ))
    fm["zones"] = zones

    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    parts = raw.split("---", 2)
    geo_file.write_text("---\n" + new_fm + "---" + parts[2], encoding="utf-8")

    # Mise à jour du statut de suivi -- jamais un statut décidé par David
    # (accepte_tel_quel/corrige_manuellement) n'est écrasé ici, seule une
    # entrée a_traiter/en_attente_c2 (celle qu'on vient d'appliquer) progresse.
    if SUSPECTES_FILE.exists():
        data = yaml.safe_load(SUSPECTES_FILE.read_text(encoding="utf-8")) or {}
        entrees = data.get("zones_suspectes") or []
        for e in entrees:
            if e.get("scenario") == scenario and e.get("slug") == slug:
                e["statut"] = STATUT_APRES_APPLY
        SUSPECTES_FILE.write_text(
            yaml.safe_dump({"zones_suspectes": entrees}, allow_unicode=True,
                            sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print(f"    ✓ statut mis à jour vers {STATUT_APRES_APPLY!r} dans {SUSPECTES_FILE.name}")


def appliquer_scenario(scenario: str) -> int:
    print(f"\n=== {scenario} ===")
    review_file = _review_file(scenario)
    if not review_file.exists():
        print(f"  · Aucun fichier de review ({review_file.name}) -- rien à appliquer")
        return 0

    data = yaml.safe_load(review_file.read_text(encoding="utf-8")) or {}
    propositions = data.get("propositions") or []
    a_appliquer = [p for p in propositions if p.get("valide")]
    print(f"  · {len(a_appliquer)}/{len(propositions)} proposition(s) marquée(s) valide: true")

    appliquees = 0
    for p in a_appliquer:
        cible = p.get("cible")
        try:
            if p["raison"] == "pays_sans_zone":
                _appliquer_pays_sans_zone(scenario, p["proposition"])
            else:
                _appliquer_zone_suspecte(scenario, p["proposition"])
            print(f"  ✓ appliqué : {cible!r} ({p['raison']})")
            appliquees += 1
        except ValueError as e:
            print(f"  ✗ {cible!r} ({p['raison']}) : {e}")

    return appliquees


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="CLI batch du générateur top-down (P24 étape C.3). "
                     "--review-topdown génère un YAML de propositions (valide: false "
                     "par défaut) ; --apply-topdown écrit dans le vault ce qui a été "
                     "repassé à valide: true à la main."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--review-topdown", action="store_true")
    mode.add_argument("--apply-topdown", action="store_true")
    cible = parser.add_mutually_exclusive_group(required=True)
    cible.add_argument("--scenario", help="Scénario unique")
    cible.add_argument("--all", action="store_true", help="Les 6 scénarios")
    parser.add_argument(
        "--source", choices=["pays_sans_zone", "zones_suspectes", "both"], default="both",
        help="Limite --review-topdown à une seule source de cas (défaut : les deux).",
    )
    args = parser.parse_args()

    if args.scenario and args.scenario not in SCENARIOS:
        print(f"✗ Scénario inconnu : {args.scenario}")
        sys.exit(1)
    scenarios = SCENARIOS if args.all else [args.scenario]

    print("=" * 60)
    if args.review_topdown:
        print("  Générateur top-down — review (P24 étape C.3)")
    else:
        print("  Générateur top-down — apply (P24 étape C.3)")
    print("=" * 60)

    total = 0
    for s in scenarios:
        if args.review_topdown:
            total += reviewer_scenario(s, args.source)
        else:
            total += appliquer_scenario(s)

    print("\n" + "=" * 60)
    if args.review_topdown:
        print(f"  Terminé — {total} proposition(s) au total, écrites en YAML "
              f"(valide: false), rien appliqué au vault.")
    else:
        print(f"  Terminé — {total} proposition(s) appliquée(s) au vault.")
    print("=" * 60)


if __name__ == "__main__":
    main()
