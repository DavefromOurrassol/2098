#!/usr/bin/env python3
"""
check_overlay_portion_coherence.py — Ourrassol 2098
=====================================================

Diagnostic LECTURE SEULE (même doctrine que les autres check_*_coherence.py
du pipeline géographie) : croise le texte narratif `portion` de
`origine_reelle` (dans geographie/{scenario}.md) avec les polygones GeoJSON
custom dessinés à la main (gui/static/geo_overlays/{scenario}.geojson), pour
détecter la dérive entre les deux — le texte édité sans redessiner le
polygone, ou l'inverse.

PRINCIPE
--------
Chaque feature d'un overlay porte un champ `properties.portion_source` :
une copie figée du texte `portion` au moment où le polygone a été dessiné
(voir convention dans le patch app.js — un formulaire de création
d'overlay devrait toujours pré-remplir ce champ depuis le `portion` actuel
de la zone). Ce script compare ce texte figé au `portion` ACTUEL de la
fiche — s'ils diffèrent, quelqu'un a édité l'un sans toucher à l'autre.

CE QUE CE SCRIPT DÉTECTE (3 cas)
---------------------------------
1. DÉRIVE : un overlay existe, son portion_source ne correspond plus au
   portion actuel de origine_reelle pour ce pays/cette zone.
2. OVERLAY ORPHELIN : un overlay référence un zone_slug qui n'existe plus
   dans geographie/{scenario}.md (zone renommée/fusionnée/supprimée), ou
   un pays qui n'apparaît plus dans l'origine_reelle de cette zone.
3. PORTION SANS OVERLAY : une zone a un `portion` non-null dans
   origine_reelle mais aucun overlay ne couvre ce couple (zone, pays) —
   pas forcément un problème (l'overlay est un plus, pas une obligation),
   affiché en INFO plutôt qu'en ⚠ WARNING.

Ce script n'écrit jamais rien — correction toujours manuelle (retoucher
le texte ou redessiner le polygone), cohérent avec la doctrine "diagnostic
pur, lecture seule" déjà appliquée aux 5 check_*_coherence.py existants.

USAGE
-----
    python3 check_overlay_portion_coherence.py --scenario fortress_world
    python3 check_overlay_portion_coherence.py --all
    python3 check_overlay_portion_coherence.py --all --quiet   # résumé seul
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"
# Corrigé le 23 sept 2026 : ce chemin était calculé relativement au dossier
# du SCRIPT (Path(__file__).parent / "static" / ...), donc juste seulement si
# le script vivait dans gui/. Lancé depuis une copie dans generator/, il
# cherchait generator/static/geo_overlays/, ne trouvait rien et annonçait
# "Aucun overlay" en silence. Désormais ancré sur la racine du vault, comme
# GEOGRAPHIE_DIR.
GUI_OVERLAYS_DIR = VAULT_ROOT / "gui" / "static" / "geo_overlays"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def load_zones(scenario):
    """Charge toutes les zones (tous niveaux) de geographie/{scenario}.md."""
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if not m:
        return []
    fm = yaml.safe_load(m.group(1)) or {}
    return fm.get("zones") or []


def load_overlays(scenario):
    """Charge le FeatureCollection d'overlays custom.

    Retourne None si le fichier est absent ou invalide -- l'appelant traite
    alors le scénario comme "zéro overlay" et continue quand même la
    vérification des textes portion (voir check_scenario)."""
    path = GUI_OVERLAYS_DIR / f"{scenario}.geojson"
    if not path.exists():
        print(f"  ℹ Aucun fichier overlay ({path}) -- traité comme 0 overlay.")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  ✗ geojson invalide ({path.name}) : {e}")
        return None


def index_portions(zones):
    """slug -> {pays: [portion_texte, ...]} à partir de origine_reelle.

    Liste plutôt que valeur unique (corrigé le 23 sept 2026) : un même pays
    présent DEUX fois dans l'origine_reelle d'une zone (cas réel :
    France x2 dans zone_euro_sud/fortress_world) était écrasé par le
    dict -- la première entrée disparaissait du diagnostic sans aucun
    signal."""
    idx = {}
    for z in zones:
        slug = z.get("slug")
        if not slug:
            continue
        par_pays = {}
        for o in z.get("origine_reelle") or []:
            if isinstance(o, dict) and o.get("entite"):
                par_pays.setdefault(o["entite"], []).append(o.get("portion"))
        idx[slug] = par_pays
    return idx


# ---------------------------------------------------------------------------
# Diagnostic
# ---------------------------------------------------------------------------

def check_scenario(scenario, quiet=False):
    zones = load_zones(scenario)
    if zones is None:
        print(f"\n=== {scenario} ===\n  ✗ geographie/{scenario}.md introuvable — ignoré")
        return 0, 0, 0, 0

    print(f"\n=== {scenario} ===")
    overlays = load_overlays(scenario)

    # Corrigé le 23 sept 2026 : sortait ici avec "rien à vérifier" quand le
    # fichier overlay manquait -- donc sautait la vérification des portions
    # sans overlay, précisément le cas où elle compte le plus (tous les
    # tracés perdus = tous les textes portion orphelins, et le script
    # annonçait 0 problème).
    if overlays is None:
        overlays = {"features": []}

    zones_by_slug = {z.get("slug"): z for z in zones if z.get("slug")}
    portions = index_portions(zones)

    nb_derives = 0
    nb_orphelins = 0
    nb_sans_overlay = 0

    nb_doublons_internes = 0
    couples_avec_overlay = set()  # (slug, pays) couverts par au moins un overlay

    # Même pays listé plusieurs fois dans l'origine_reelle d'UNE zone --
    # invisible pour diagnostiquer_doublons_pays_entier.py (qui compare
    # des racines N1 distinctes). Toujours affiché, même en --quiet.
    for slug, par_pays in portions.items():
        for pays, liste in par_pays.items():
            if len(liste) > 1:
                nom = zones_by_slug.get(slug, {}).get("nom", slug)
                print(f"  ⚠ DOUBLON INTERNE : '{nom}' ({slug}) liste {pays} "
                      f"{len(liste)} fois dans origine_reelle :")
                for t in liste:
                    print(f"      - portion : {t!r}")
                nb_doublons_internes += 1

    for feature in overlays.get("features", []):
        props = feature.get("properties", {}) or {}
        slug = props.get("zone_slug")
        pays = props.get("pays")
        portion_source = props.get("portion_source")

        if not slug or not pays:
            print(f"  ⚠ Feature sans zone_slug/pays exploitable : {props}")
            continue

        couples_avec_overlay.add((slug, pays))

        if slug not in zones_by_slug:
            print(f"  ⚠ ORPHELIN : overlay référence la zone '{slug}' "
                  f"(pays: {pays}) — cette zone n'existe plus dans "
                  f"geographie/{scenario}.md")
            nb_orphelins += 1
            continue

        if pays not in portions.get(slug, {}):
            print(f"  ⚠ ORPHELIN : overlay '{slug}'/{pays} — ce pays n'est "
                  f"plus dans l'origine_reelle de cette zone")
            nb_orphelins += 1
            continue

        # Plusieurs entrées possibles (doublon interne) : cohérent si
        # L'UNE d'elles correspond au texte figé du polygone.
        textes_actuels = portions[slug][pays]
        src = (portion_source or "").strip()
        if not any(src == (t or "").strip() for t in textes_actuels):
            print(f"  ⚠ DÉRIVE sur '{slug}' ({pays}) :")
            print(f"      polygone dessiné pour : {portion_source!r}")
            for t in textes_actuels:
                print(f"      texte actuel          : {t!r}")
            nb_derives += 1

    if not quiet:
        for slug, par_pays in portions.items():
            for pays, liste in par_pays.items():
              for portion in liste:
                if portion and (slug, pays) not in couples_avec_overlay:
                    nom = zones_by_slug.get(slug, {}).get("nom", slug)
                    print(f"  ℹ INFO : '{nom}' a une portion sur {pays} "
                          f"({portion!r}) sans overlay dessiné — pas un "
                          f"problème, juste une zone qui pourrait en profiter.")
                    nb_sans_overlay += 1

    if nb_derives == 0 and nb_orphelins == 0:
        print(f"  ✓ {len(couples_avec_overlay)} overlay(s) cohérent(s) avec le texte narratif.")

    return nb_derives, nb_orphelins, nb_sans_overlay, nb_doublons_internes


def main():
    parser = argparse.ArgumentParser(
        description="Vérifie la cohérence entre le texte 'portion' (origine_reelle) "
                     "et les overlays GeoJSON dessinés à la main — diagnostic pur, "
                     "lecture seule."
    )
    parser.add_argument("--scenario", choices=SCENARIOS, help="Un seul scénario")
    parser.add_argument("--all", action="store_true", help="Les 6 scénarios")
    parser.add_argument("--quiet", action="store_true",
                         help="Masque les INFO 'portion sans overlay' (garde seulement "
                              "dérives et orphelins)")
    args = parser.parse_args()

    if not args.scenario and not args.all:
        sys.exit("Précise --scenario {nom} ou --all.")

    print("=" * 60)
    print("OURRASSOL 2098 — Cohérence portion (texte) / overlays (dessin)")
    print("=" * 60)

    targets = SCENARIOS if args.all else [args.scenario]
    total_derives = total_orphelins = total_sans_overlay = total_doublons = 0

    for scenario in targets:
        d, o, s, dbl = check_scenario(scenario, quiet=args.quiet)
        total_doublons += dbl
        total_derives += d
        total_orphelins += o
        total_sans_overlay += s

    print("\n" + "=" * 60)
    print(f"Résumé : {total_derives} dérive(s), {total_orphelins} orphelin(s), "
          f"{total_doublons} doublon(s) interne(s)"
          + ("" if args.quiet else f", {total_sans_overlay} portion(s) sans overlay"))
    print("=" * 60)

    sys.exit(1 if (total_derives or total_orphelins or total_doublons) else 0)


if __name__ == "__main__":
    main()
