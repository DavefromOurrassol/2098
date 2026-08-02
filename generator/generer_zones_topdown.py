#!/usr/bin/env python3
"""
generer_zones_topdown.py — Ourrassol 2098 (P24 étape C.3)

CLI batch pour le générateur top-down (C.2, zoning_topdown.py) : génère une
proposition pour chaque chantier éligible de chantiers_geographie.yaml
(pays sans zone + zones suspectes non tranchées), l'attache à l'entrée
correspondante, puis applique les propositions relues et approuvées.

MIGRATION CHANTIERS.PY (25 juillet 2026)
-----------------------------------------
Depuis cette date, ce script ne détecte plus rien lui-même et ne possède
plus son propre fichier de review séparé -- il lit/écrit exclusivement via
le module partagé chantiers.py (chantiers_geographie.yaml, UN SEUL fichier
pour tout le pipeline géographie) :

  - --review-topdown consomme chantiers.chantiers_eligibles(scenario,
    type_=...) au lieu de détecter les pays orphelins en dur
    (_pays_sans_zone(), supprimée) ou de lire patron_spatial_suspectes.yaml
    (_zones_suspectes_eligibles(), supprimée). La proposition générée est
    attachée à l'entrée existante via chantiers.mettre_a_jour_chantier(...,
    proposition=..., date_proposition=...) -- PLUS de fichier
    zones_proposees_topdown_{scenario}.yaml séparé.
  - --apply-topdown consomme chantiers.chantiers_prets_a_appliquer()
    (statut a_traiter + proposition non nulle + proposition_approuvee:
    true) au lieu de lire un fichier de review avec valide: true. Après
    application réussie, l'entrée passe à statut="traite" via
    chantiers.mettre_a_jour_chantier(...).

CONSÉQUENCE IMPORTANTE : --review-topdown ne fait plus AUCUNE détection --
il ne traite que ce qui existe déjà comme chantier dans
chantiers_geographie.yaml. Lancer d'abord (avec --write-chantiers) :
check_zones_coherence.py / check_origine_reelle_coherence.py (pays sans
zone) et check_patron_spatial_coherence.py (zones suspectes) pour peupler
les chantiers, PUIS ce script pour leur générer une proposition.

La logique d'écriture elle-même (_appliquer_pays_sans_zone,
_appliquer_zone_suspecte, l'appel à reparenter_sous_zones_orphelines.py)
est INCHANGÉE -- seule la source de lecture/écriture des chantiers a
changé. En particulier _appliquer_zone_suspecte ne touche plus
patron_spatial_suspectes.yaml (le fichier legacy reste en lecture pour
compat mais n'est plus jamais écrit par ce script) : la progression du
statut de suivi passe intégralement par chantiers.py désormais.

ÉCRITURE (--apply-topdown) : duplique consciemment la logique d'écriture
de carte_creer_zone_niveau1()/zones_pays.json (gui/app.py) pour le cas
pays_sans_zone -- generator/ et gui/ restent deux codebases séparées, sans
import croisé (point de vigilance déjà établi pour _tokens_entite() dans
app.py).

USAGE
-----
    python3 generer_zones_topdown.py --review-topdown --scenario new_sustainability
    python3 generer_zones_topdown.py --review-topdown --all
    python3 generer_zones_topdown.py --review-topdown --all --source pays_sans_zone
    python3 generer_zones_topdown.py --review-topdown --all --source zones_suspectes
    python3 generer_zones_topdown.py --review-topdown --all --force
    python3 generer_zones_topdown.py --apply-topdown --scenario new_sustainability
    python3 generer_zones_topdown.py --apply-topdown --all
    python3 generer_zones_topdown.py --apply-topdown --scenario new_sustainability --cible barcelone_hub
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

from zoning_topdown import generer_zone_topdown
from reparenter_sous_zones_orphelines import reparenter_sous_zones_orphelines
import chantiers

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
GUI_DIR = VAULT_ROOT / "gui"
ZONES_PAYS = GUI_DIR / "zones_pays.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

# Mapping argument CLI (pluriel, historique) -> valeur `type` de chantiers.py
SOURCE_VERS_TYPES = {
    "pays_sans_zone": ["pays_sans_zone"],
    "zones_suspectes": ["zone_suspecte"],
    "both": ["pays_sans_zone", "zone_suspecte"],
}


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


# ---------------------------------------------------------------------------
# --review-topdown
# ---------------------------------------------------------------------------

def reviewer_scenario(scenario: str, source: str, force: bool = False) -> int:
    print(f"\n=== {scenario} ===")
    try:
        _, zones, _ = _lire_geo(scenario)
    except (FileNotFoundError, ValueError) as e:
        print(f"  ✗ {e}")
        return 0
    zones_n1 = _zones_n1(zones)
    zones_par_slug = {z.get("slug"): z for z in zones_n1}

    generees = 0
    for type_ in SOURCE_VERS_TYPES[source]:
        label = "pays sans zone" if type_ == "pays_sans_zone" else "zone(s) suspecte(s)"
        eligibles = chantiers.chantiers_eligibles(scenario=scenario, type_=type_)

        if not force:
            deja_proposees = [c for c in eligibles if c.get("proposition") is not None]
            if deja_proposees:
                print(f"  · {len(deja_proposees)} chantier(s) {type_} déjà pourvu(s) d'une "
                      f"proposition non approuvée -- pas régénéré(s) (--force pour écraser)")
            eligibles = [c for c in eligibles if c.get("proposition") is None]

        print(f"  · {len(eligibles)} {label} à traiter")

        for c in eligibles:
            cible = c["cible"]

            if type_ == "pays_sans_zone":
                print(f"    - génération pour {cible!r}...")
                try:
                    proposition, issues = generer_zone_topdown(
                        scenario, "pays_sans_zone", pays=[cible], zones_existantes=zones_n1,
                    )
                except (ImportError, EnvironmentError, RuntimeError, ValueError) as e:
                    print(f"      ✗ échec de génération : {e}")
                    continue
            else:
                zone = zones_par_slug.get(cible)
                if zone is None:
                    print(f"    · {cible!r} suivi dans {chantiers.CHANTIERS_FILE.name} mais "
                          f"introuvable dans {scenario} -- ignoré")
                    continue
                print(f"    - révision pour {cible!r}...")
                try:
                    proposition, issues = generer_zone_topdown(
                        scenario, "zone_suspecte", zone_existante=zone,
                        raison_suspicion=c.get("probleme", ""),
                        zones_existantes=zones_n1,
                    )
                except (ImportError, EnvironmentError, RuntimeError, ValueError) as e:
                    print(f"      ✗ échec de génération : {e}")
                    continue

            chantiers.mettre_a_jour_chantier(
                scenario, cible,
                proposition=proposition,
                proposition_issues=issues,
                proposition_approuvee=False,
                date_proposition=chantiers.date.today().isoformat(),
            )
            generees += 1
            if issues:
                print(f"      ⚠ {len(issues)} problème(s) de validation, à relire attentivement")

    if not generees:
        print("  ✓ Rien à proposer")
    else:
        print(f"  ✓ {generees} proposition(s) écrite(s) dans {chantiers.CHANTIERS_FILE.name} "
              f"(proposition_approuvee: false -- relire et approuver avant --apply-topdown)")
    return generees


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

    # Propagation des sous-zones orphelines (P24 étape C, ajouté le 25 juillet
    # suite au cas réel valence_tours_rirec/Espagne) -- appelée maintenant que
    # la zone cible existe réellement sur disque (reparenter_sous_zones_
    # orphelines() lit le fichier tel qu'écrit, ne travaille jamais sur un état
    # en mémoire). Fonction partagée, réutilisée telle quelle par le GUI en
    # sous-processus -- voir reparenter_sous_zones_orphelines.py.
    reparentees = reparenter_sous_zones_orphelines(scenario, slug)
    if reparentees:
        print(f"    ✓ {len(reparentees)} sous-zone(s) suivie(s) automatiquement : "
              f"{', '.join(reparentees)}")

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
    qui a changé pour un diff minimal). La progression du statut de suivi
    (-> "traite") est déléguée à l'appelant via chantiers.mettre_a_jour_
    chantier() depuis la migration du 25 juillet 2026 -- cette fonction ne
    touche plus patron_spatial_suspectes.yaml."""
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


def appliquer_scenario(scenario: str, cible: str = None) -> int:
    print(f"\n=== {scenario} ===")
    prets = chantiers.chantiers_prets_a_appliquer(scenario=scenario, cible=cible)
    if cible:
        print(f"  · {len(prets)} chantier(s) prêt(s) à appliquer pour cible={cible!r}")
    else:
        print(f"  · {len(prets)} chantier(s) prêt(s) à appliquer (proposition approuvée)")

    appliquees = 0
    for c in prets:
        cible = c["cible"]
        type_ = c["type"]
        proposition = c["proposition"]
        try:
            if type_ == "pays_sans_zone":
                _appliquer_pays_sans_zone(scenario, proposition)
            else:
                _appliquer_zone_suspecte(scenario, proposition)
            chantiers.mettre_a_jour_chantier(
                scenario, cible, statut="traite",
                date_traitement=chantiers.date.today().isoformat(),
            )
            print(f"  ✓ appliqué : {cible!r} ({type_}) -- chantier marqué 'traite'")
            appliquees += 1
        except ValueError as e:
            print(f"  ✗ {cible!r} ({type_}) : {e}")

    return appliquees


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="CLI batch du générateur top-down (P24 étape C.3). "
                     "--review-topdown génère une proposition pour chaque chantier "
                     "éligible de chantiers_geographie.yaml (proposition_approuvee: false "
                     "par défaut) ; --apply-topdown écrit dans le vault les chantiers "
                     "repassés à proposition_approuvee: true à la main."
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
    parser.add_argument(
        "--force", action="store_true",
        help="--review-topdown seulement : régénère aussi les propositions déjà "
             "présentes mais pas encore approuvées. Sans ce flag, un chantier qui a "
             "déjà une proposition en attente d'approbation n'est jamais retouché, "
             "pour ne pas écraser une relecture/édition manuelle en cours.",
    )
    parser.add_argument(
        "--cible",
        help="--apply-topdown --scenario seulement (ajouté le 1er août 2026) : "
             "applique un seul chantier précis (slug de zone ou nom de pays) au "
             "lieu de tous les chantiers prêts du scénario. Incompatible avec "
             "--all (une cible se résout dans un seul scénario à la fois) et "
             "avec --review-topdown (pas de notion de cible unique en review).",
    )
    args = parser.parse_args()

    if args.scenario and args.scenario not in SCENARIOS:
        print(f"✗ Scénario inconnu : {args.scenario}")
        sys.exit(1)
    if args.cible and (args.all or args.review_topdown):
        print("✗ --cible n'est utilisable qu'avec --apply-topdown --scenario "
              "(incompatible avec --all et --review-topdown)")
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
            total += reviewer_scenario(s, args.source, args.force)
        else:
            total += appliquer_scenario(s, cible=args.cible)

    print("\n" + "=" * 60)
    if args.review_topdown:
        print(f"  Terminé — {total} proposition(s) au total, attachée(s) aux chantiers "
              f"({chantiers.CHANTIERS_FILE.name}, proposition_approuvee: false), rien "
              f"appliqué au vault.")
    else:
        print(f"  Terminé — {total} proposition(s) appliquée(s) au vault.")
    print("=" * 60)


if __name__ == "__main__":
    main()
