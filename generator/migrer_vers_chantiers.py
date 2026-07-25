#!/usr/bin/env python3
"""
migrer_vers_chantiers.py — Ourrassol 2098 (P24 étape C, point 4.2 du handoff fusion)

Migration UNE FOIS de l'historique des 3 anciens fichiers de suivi séparés
vers chantiers_geographie.yaml (module chantiers.py), sans rien perdre :

  1. patron_spatial_suspectes.yaml -> chantiers type="zone_suspecte"
     Mapping statut :
       a_traiter            -> a_traiter
       en_attente_c2        -> a_traiter
       accepte_tel_quel     -> ignore
       corrige_manuellement -> traite
       corrige_via_c2       -> traite

  2. zones_manquantes.yaml -> chantiers type="pays_sans_zone"
     Mapping statut :
       blanc_intentionnel -> ignore
       (tout le reste, y compris statut absent) -> a_traiter
     Format historique jamais vu non vide sur ce vault (fichier observé
     vide le 25 juillet 2026) -- lecture volontairement tolérante
     (accepte `pays` ou `cible` comme nom de champ) et jamais silencieuse
     sur une entrée qu'elle ne sait pas interpréter.

  3. zones_proposees_topdown_{scenario}.yaml (x6, si présents) -> attache
     leur `proposition` au chantier déjà migré correspondant, avec
     proposition_approuvee = leur `valide` (true/false). Tourne APRÈS 1 et
     2 (le chantier cible doit déjà exister).

RÈGLES DE SÉCURITÉ
-------------------
- N'écrase JAMAIS un chantier déjà présent dans chantiers_geographie.yaml --
  délègue tout le dédoublonnage à chantiers.ajouter_chantier()/
  mettre_a_jour_chantier(). Un chantier déjà connu (par exemple créé
  aujourd'hui par check_patron_spatial_coherence.py --write-chantiers, ou
  déjà pourvu d'une proposition/déjà appliqué par generer_zones_topdown.py)
  n'est jamais retouché par cette migration.
- Étape 3 : n'attache une proposition legacy que si le chantier cible est
  encore `a_traiter` ET n'a pas déjà de `proposition` -- jamais d'écrasement
  d'un travail plus récent par une proposition legacy potentiellement
  périmée.
- --dry-run par défaut (aucune écriture, juste un aperçu) -- --apply pour
  écrire réellement, cohérent avec le principe review-avant-apply du reste
  du pipeline. En dry-run, l'étape 3 peut afficher "chantier absent" pour
  des cas que les étapes 1/2 créeraient si --apply était passé -- normal,
  le dry-run ne simule pas les écritures des étapes précédentes.
- Entrées non mappables (champ statut inconnu, structure inattendue) :
  jamais ignorées silencieusement -- imprimées pour vérification manuelle.
- Les 3 fichiers legacy ne sont PAS supprimés par ce script (décision
  actée au §5 du handoff -- gardés comme filet de sécurité).

USAGE
-----
    python3 migrer_vers_chantiers.py            # aperçu (dry-run)
    python3 migrer_vers_chantiers.py --apply     # écrit pour de vrai
"""

import argparse
from pathlib import Path

import yaml

import chantiers

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
NEED_ACTION = VAULT_ROOT / "documentation" / "need_action"

SUSPECTES_FILE = NEED_ACTION / "patron_spatial_suspectes.yaml"
MANQUANTES_FILE = NEED_ACTION / "zones_manquantes.yaml"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

MAPPING_STATUT_ZONE_SUSPECTE = {
    "a_traiter": "a_traiter",
    "en_attente_c2": "a_traiter",
    "accepte_tel_quel": "ignore",
    "corrige_manuellement": "traite",
    "corrige_via_c2": "traite",
}

STATUTS_PAYS_SANS_ZONE_IGNORE = {"blanc_intentionnel"}


def _review_file(scenario: str) -> Path:
    return NEED_ACTION / f"zones_proposees_topdown_{scenario}.yaml"


def _charger_yaml(path: Path, cle: str) -> list:
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        print(f"  ✗ {path.name} : YAML invalide, ignoré ({e})")
        return []
    return data.get(cle) or []


# ---------------------------------------------------------------------------
# 1. patron_spatial_suspectes.yaml -> zone_suspecte
# ---------------------------------------------------------------------------

def migrer_zones_suspectes(apply: bool) -> dict:
    entrees = _charger_yaml(SUSPECTES_FILE, "zones_suspectes")
    print(f"\n=== {SUSPECTES_FILE.name} ({len(entrees)} entrée(s)) ===")
    stats = {"crees": 0, "deja_connus": 0, "non_mappables": 0}

    for e in entrees:
        scenario = e.get("scenario")
        slug = e.get("slug")
        if not scenario or not slug:
            print(f"  ✗ entrée sans scenario/slug, ignorée : {e}")
            stats["non_mappables"] += 1
            continue

        statut_legacy = e.get("statut", "a_traiter")
        statut_nouveau = MAPPING_STATUT_ZONE_SUSPECTE.get(statut_legacy)
        if statut_nouveau is None:
            print(f"  ✗ {scenario}/{slug!r} : statut legacy inconnu {statut_legacy!r}, "
                  f"non mappé -- à traiter manuellement")
            stats["non_mappables"] += 1
            continue

        deja = chantiers.get_chantier(scenario, slug)
        if deja is not None:
            print(f"  · {scenario}/{slug!r} : déjà présent dans "
                  f"{chantiers.CHANTIERS_FILE.name} (statut actuel : {deja['statut']!r}) -- "
                  f"pas retouché")
            stats["deja_connus"] += 1
            continue

        print(f"  + {scenario}/{slug!r} : {statut_legacy!r} -> {statut_nouveau!r}")
        stats["crees"] += 1
        if apply:
            chantiers.ajouter_chantier(
                scenario=scenario, type_="zone_suspecte", cible=slug,
                probleme=e.get("raison", ""), source_diagnostic="patron_spatial",
            )
            champs = {}
            if statut_nouveau != chantiers.STATUT_DEFAUT:
                champs["statut"] = statut_nouveau
            if e.get("date_detection"):
                champs["date_detection"] = e["date_detection"]
            if champs:
                chantiers.mettre_a_jour_chantier(scenario, slug, **champs)

    return stats


# ---------------------------------------------------------------------------
# 2. zones_manquantes.yaml -> pays_sans_zone
# ---------------------------------------------------------------------------

def migrer_pays_sans_zone(apply: bool) -> dict:
    entrees = _charger_yaml(MANQUANTES_FILE, "zones_manquantes")
    print(f"\n=== {MANQUANTES_FILE.name} ({len(entrees)} entrée(s)) ===")
    stats = {"crees": 0, "deja_connus": 0, "non_mappables": 0}

    for e in entrees:
        scenario = e.get("scenario")
        # nom de champ non figé (jamais vu non vide) -- tolère les deux variantes.
        cible = e.get("pays") or e.get("cible")
        if not scenario or not cible:
            print(f"  ✗ entrée sans scenario/pays exploitable, ignorée : {e}")
            stats["non_mappables"] += 1
            continue

        statut_legacy = e.get("statut", "a_traiter")
        statut_nouveau = "ignore" if statut_legacy in STATUTS_PAYS_SANS_ZONE_IGNORE else "a_traiter"

        deja = chantiers.get_chantier(scenario, cible)
        if deja is not None:
            print(f"  · {scenario}/{cible!r} : déjà présent (statut actuel : "
                  f"{deja['statut']!r}) -- pas retouché")
            stats["deja_connus"] += 1
            continue

        print(f"  + {scenario}/{cible!r} : {statut_legacy!r} -> {statut_nouveau!r}")
        stats["crees"] += 1
        if apply:
            chantiers.ajouter_chantier(
                scenario=scenario, type_="pays_sans_zone", cible=cible,
                probleme=e.get("raison") or f"{cible!r} sans zone cohérente "
                                             f"(migré depuis {MANQUANTES_FILE.name})",
                source_diagnostic="zones_coherence",
            )
            champs = {}
            if statut_nouveau != chantiers.STATUT_DEFAUT:
                champs["statut"] = statut_nouveau
            if e.get("date_detection"):
                champs["date_detection"] = e["date_detection"]
            if champs:
                chantiers.mettre_a_jour_chantier(scenario, cible, **champs)

    return stats


# ---------------------------------------------------------------------------
# 3. zones_proposees_topdown_{scenario}.yaml -> attacher proposition
# ---------------------------------------------------------------------------

def migrer_propositions(apply: bool) -> dict:
    stats = {"attachees": 0, "sautees_deja_pourvues": 0, "sautees_chantier_absent": 0}
    for scenario in SCENARIOS:
        review_file = _review_file(scenario)
        if not review_file.exists():
            continue
        propositions = _charger_yaml(review_file, "propositions")
        print(f"\n=== {review_file.name} ({len(propositions)} proposition(s)) ===")

        for p in propositions:
            cible = p.get("cible")
            if not cible:
                print(f"  ✗ proposition sans cible, ignorée (raison : {p.get('raison')})")
                continue

            chantier = chantiers.get_chantier(scenario, cible)
            if chantier is None:
                print(f"  · {scenario}/{cible!r} : aucun chantier correspondant dans "
                      f"{chantiers.CHANTIERS_FILE.name} -- proposition orpheline, pas "
                      f"attachée (migrer d'abord {SUSPECTES_FILE.name}/"
                      f"{MANQUANTES_FILE.name}, ou -- en dry-run -- normal si les étapes "
                      f"1/2 la créeraient avec --apply)")
                stats["sautees_chantier_absent"] += 1
                continue
            if chantier.get("proposition") is not None or chantier.get("statut") != "a_traiter":
                print(f"  · {scenario}/{cible!r} : chantier déjà pourvu d'une proposition ou "
                      f"déjà tranché (statut {chantier['statut']!r}) -- proposition legacy "
                      f"pas attachée, pour ne rien écraser de plus récent")
                stats["sautees_deja_pourvues"] += 1
                continue

            print(f"  + {scenario}/{cible!r} : proposition attachée "
                  f"(proposition_approuvee: {bool(p.get('valide'))})")
            stats["attachees"] += 1
            if apply:
                chantiers.mettre_a_jour_chantier(
                    scenario, cible,
                    proposition=p.get("proposition"),
                    proposition_issues=p.get("issues") or [],
                    proposition_approuvee=bool(p.get("valide")),
                )
    return stats


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migration une fois des 3 anciens fichiers de suivi séparés vers "
                     "chantiers_geographie.yaml, sans rien écraser (point 4.2 du handoff)."
    )
    parser.add_argument("--apply", action="store_true",
                         help="Écrit réellement dans chantiers_geographie.yaml. "
                              "Sans ce flag, aperçu seul (dry-run par défaut).")
    args = parser.parse_args()

    print("=" * 60)
    titre = "  Migration vers chantiers_geographie.yaml"
    print(titre if args.apply else titre + " (aperçu -- rien n'est écrit)")
    print("=" * 60)

    s1 = migrer_zones_suspectes(args.apply)
    s2 = migrer_pays_sans_zone(args.apply)
    s3 = migrer_propositions(args.apply)

    print("\n" + "=" * 60)
    print(f"  zones_suspectes : {s1['crees']} à créer, {s1['deja_connus']} déjà connus, "
          f"{s1['non_mappables']} non mappable(s)")
    print(f"  pays_sans_zone  : {s2['crees']} à créer, {s2['deja_connus']} déjà connus, "
          f"{s2['non_mappables']} non mappable(s)")
    print(f"  propositions    : {s3['attachees']} à attacher, "
          f"{s3['sautees_deja_pourvues']} sautée(s) (déjà pourvues), "
          f"{s3['sautees_chantier_absent']} orpheline(s) (chantier absent)")
    if not args.apply:
        print("\n  Aperçu seul -- relancer avec --apply pour écrire réellement.")
    print("=" * 60)


if __name__ == "__main__":
    main()
