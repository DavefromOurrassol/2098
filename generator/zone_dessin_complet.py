#!/usr/bin/env python3
"""
zone_dessin_complet.py

Outil de dessin de zone complète (S11) -- prend un polygone dessiné à main
levée sur la carte (peu importe les frontières de pays en dessous) et
en déduit automatiquement :
  - les pays ENTIÈREMENT couverts (>= seuil_split) -> candidats à un split
    pays-entier (même résultat que ✂️ Scinder, mais déduit du dessin)
  - les pays PARTIELLEMENT couverts (entre seuil_bruit et seuil_split)
    -> candidats à un overlay (portion du pays)
  - les pays sous seuil_bruit -> classés `ignore_bruit`, non retenus par
    défaut mais remontés au frontend avec leur géométrie (imprécision de
    dessin à main levée présumée, mais pas toujours -- le panneau de
    review permet de les inclure quand même comme overlay, cas réel : une
    petite portion réelle et volontaire d'un pays, remonté par David le
    14 sept 2026). Aucun appel LLM automatique sur ces entrées tant
    qu'elles ne sont pas explicitement incluses (rédaction manuelle du
    texte `portion` dans ce cas, comme pour un overlay normal en échec de
    génération LLM).
  - les "petits pays" absents de world.geo.json (fond de carte de
    l'application) -> signalés comme NON VÉRIFIABLES automatiquement,
    à traiter à la main (David, 9 sept : décision actée -- ne pas planter,
    ne pas ignorer silencieusement, juste signaler)

Doctrine génération/application séparée (même que enrich_zone_manquante.py,
zoning_topdown.py) : CE SCRIPT NE MODIFIE JAMAIS LE VAULT. Il calcule une
PROPOSITION (classification + textes `portion` rédigés par LLM à partir de
l'enrichissement Natural Earth). L'application réelle réutilise les routes
EXISTANTES /api/carte/assign (splits) et /api/carte/overlays/creer
(overlays) -- pas de nouveau mécanisme d'écriture, pour rester cohérent
avec ce qui est déjà testé en conditions réelles.

Sources de frontières -- DÉCISION ACTÉE (9 sept 2026, diagnostic Claude
confirmé par David) :
  - Calcul de couverture pays-entier : world.geo.json (même fond de carte
    que l'app, via gui/static/pays_mapping.json pour la résolution FR->EN)
    -- PAS un Natural Earth admin_0 séparé. pays_mapping.json a été
    manifestement construit contre world.geo.json (noms datés : Swaziland,
    Macedonia) -- utiliser une autre source de frontières créerait un
    désalignement de noms.
  - Désambiguïsation Royaume-Uni/Angleterre/Écosse/Pays de Galles (polygone
    unique partagé dans world.geo.json, piège documenté au 8 sept) :
    Natural Earth ne_10m_admin_1_states_provinces, champ `geonunit`
    (England/Scotland/Wales/Northern Ireland), UNIQUEMENT pour ces 3 clés
    FR (Angleterre/Écosse/Pays de Galles) -- PAS pour "Royaume-Uni" lui-même,
    explicitement EXCLU des candidats automatiques (décision David, 9 sept :
    reste en réaffectation manuelle, comme le cas Heysham).
  - Enrichissement texte (villes/fleuves/régions) : Natural Earth 10m
    (populated_places, rivers_lake_centerlines, admin_1_states_provinces),
    croisées avec l'intersection géométrique de chaque pays retenu.

Seuils (9 sept 2026, proposés par Claude, validés par défaut -- ajustables
en CLI) :
  - SEUIL_SPLIT = 90%  : au-dessus -> pays entier
  - SEUIL_BRUIT = 2%   : en dessous -> ignoré (imprécision de dessin)
  - entre les deux -> overlay

Perf (9 sept 2026, mesuré) : chargement + parsing des 3 couches Natural
Earth (7-39 Mo chacune) fait UNE SEULE FOIS au démarrage, avec un index
spatial STRtree par couche -- un chargement naïf par pays overlay faisait
monter le script à ~26s sur un dessin touchant 8 pays ; avec index unique
réutilisé, largement sous la seconde par pays enrichi.

Usage :
    python3 zone_dessin_complet.py --scenario fortress_world \
        --geometry-file dessin.geojson --json
    python3 zone_dessin_complet.py --scenario fortress_world \
        --geometry-file dessin.geojson --seuil-split 85 --seuil-bruit 3 --json

Mode --json : dernière ligne de stdout = JSON {"ok": bool, "classification": [...], "error": str|null}
Toutes les autres traces (progression, diagnostics) vont sur stderr, jamais
sur stdout, pour ne pas polluer le contrat JSON (même doctrine que les
autres scripts --json du pipeline).
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path

from shapely.geometry import shape, mapping
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

try:
    from llm_client import call_llm
except ImportError:
    call_llm = None  # script utilisable sans LLM (juste la classification) si llm_client.py absent

SYSTEM_PROMPT_PORTION = (
    "Tu rédiges, pour un pipeline de worldbuilding fictionnel (univers "
    "post-effondrement 2098), la description en une phrase de la portion "
    "d'un pays intégrée à une zone géographique fictive. Style : concis, "
    "factuel, ancré sur de vrais noms de lieux (villes, fleuves, régions) "
    "fournis -- jamais une position cardinale vague ('nord', 'sud-ouest') "
    "seule sans contexte. Description géographique neutre, comme une "
    "légende de carte, pas de ton dramatique ni de jugement narratif. "
    "Une seule phrase, 30 mots maximum. Réponds uniquement avec cette "
    "phrase, sans guillemets ni préambule."
)


def generer_portion_llm(zone_nom: str, pays: str, pct: float, enrichissement: dict) -> tuple:
    """Rédige le texte `portion` d'un pays overlay via LLM, à partir des
    noms réels trouvés par enrichissement Natural Earth. Retourne
    (texte|None, erreur|None) -- une erreur LLM sur UN pays ne doit jamais
    faire échouer la classification des autres (isolation par pays, même
    esprit que le reste du pipeline : dry-run, jamais bloquant)."""
    if call_llm is None:
        return None, "llm_client.py introuvable (import échoué)"

    villes = ", ".join(enrichissement["villes"][:8]) or "aucune ville notable trouvée"
    fleuves = ", ".join(enrichissement["fleuves"][:5]) or "aucun"
    regions = ", ".join(enrichissement["regions"][:8]) or "aucune"

    user_prompt = (
        f"Zone fictive : {zone_nom}\n"
        f"Pays concerné : {pays} ({pct:.0f}% de sa surface inclus dans cette zone)\n"
        f"Villes dans la portion : {villes}\n"
        f"Fleuves traversant la portion : {fleuves}\n"
        f"Régions administratives dans la portion : {regions}\n\n"
        f"Rédige la phrase décrivant cette portion."
    )

    try:
        texte = call_llm(
            system_prompt=SYSTEM_PROMPT_PORTION,
            user_prompt=user_prompt,
            max_tokens=150,
            temperature=0.7,
            task_tier="creative_souple",
        )
        return texte.strip(), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


SEUIL_SPLIT_DEFAUT = 90.0
SEUIL_BRUIT_DEFAUT = 2.0

# Alias de noms entre world.geo.json (EN) et pays_mapping.json (EN) --
# découverts le 9 sept 2026 en croisant les deux fichiers réels : ces 2 pays
# sont bien présents dans world.geo.json mais sous un nom légèrement
# différent de celui utilisé dans pays_mapping.json.
ALIASES_EN = {
    "Serbia": "Republic of Serbia",
    "Tanzania": "United Republic of Tanzania",
}

# Désambiguïsation UK -- clé FR -> geonunit Natural Earth admin_1.
# "Royaume-Uni" volontairement absent (décision David 9 sept : exclu des
# candidats automatiques, reste en réaffectation manuelle).
UK_GEONUNIT = {
    "Angleterre": "England",
    "Écosse": "Scotland",
    "Pays de Galles": "Wales",
}
PAYS_UK_EXCLUS_AUTO = {"Royaume-Uni"}

R_TERRE_KM = 6371.0


def log(msg):
    print(msg, file=sys.stderr)


def equal_area_xy(lon, lat, z=None):
    """Projection cylindrique équivalente-surface (Lambert). Préserve les
    ratios d'aire exactement, quelle que soit la position sur le globe --
    c'est tout ce dont on a besoin pour le calcul de couverture (on ne
    projette jamais pour l'affichage, seulement pour comparer des aires)."""
    return (R_TERRE_KM * math.radians(lon), R_TERRE_KM * math.sin(math.radians(lat)))


def project(geom):
    return transform(equal_area_xy, geom)


def charger_world_geojson(path: Path) -> dict:
    """EN name -> géométrie shapely (union si plusieurs polygones du même nom)."""
    with open(path, encoding="utf-8") as f:
        world = json.load(f)
    en_to_geom = {}
    for feat in world["features"]:
        name = feat["properties"]["name"]
        geom = shape(feat["geometry"])
        en_to_geom[name] = unary_union([en_to_geom[name], geom]) if name in en_to_geom else geom
    return en_to_geom


def charger_pays_mapping(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resoudre_fr_vers_geom(mapping_fr_en: dict, en_to_geom: dict):
    """FR -> (géométrie, disponible: bool). disponible=False si le pays FR
    existe dans le mapping mais n'a pas de polygone dans world.geo.json
    (~30 petits pays confirmés absents le 9 sept 2026 : Monaco, Vatican,
    Andorre, Singapour, Barbade, Cap-Vert, etc. -- limitation déjà présente
    sur la carte actuelle, pas introduite par cet outil)."""
    resolu = {}
    non_disponible = []
    for fr, en in mapping_fr_en.items():
        if en is None:
            continue  # ex. "Arctique" : pas un pays, mapping vide volontaire
        key = ALIASES_EN.get(en, en)
        geom = en_to_geom.get(key)
        if geom is None:
            non_disponible.append(fr)
        else:
            resolu[fr] = geom
    return resolu, non_disponible


def charger_ne_admin1_geonunit(admin1_features, geonunit: str):
    """Union des géométries Natural Earth admin_1 pour un geonunit donné
    (ex. 'England'), à partir des features déjà chargées en mémoire."""
    geoms = [shape(f["geometry"]) for f in admin1_features
             if f["properties"].get("geonunit") == geonunit]
    if not geoms:
        return None
    return unary_union(geoms)


def reparer_geometrie(geom, contexte=""):
    """Répare une géométrie invalide (typiquement une auto-intersection sur
    un tracé à main levée) via l'idiome Shapely standard .buffer(0), qui
    reconstruit le polygone sans changer sa forme apparente. Ne lève jamais
    d'exception -- log juste un avertissement sur stderr si la réparation
    ne suffit pas, pour rester dans la doctrine "jamais bloquant" du
    script. Sans ça : GEOS refuse toute intersection avec une géométrie
    invalide et lève TopologyException ("side location conflict")."""
    if geom.is_valid:
        return geom
    suffixe = f" ({contexte})" if contexte else ""
    log(f"Géométrie invalide détectée{suffixe} -- réparation via buffer(0)...")
    reparee = geom.buffer(0)
    if not reparee.is_valid:
        log(f"  Attention : la réparation n'a pas suffi{suffixe} -- risque de plantage en aval.")
    return reparee


def couverture_pct(drawn, pays_geom):
    """Retourne (pourcentage de couverture du pays par le dessin, geometry
    d'intersection). Aire calculée en projection équivalente-surface."""
    pays_geom = reparer_geometrie(pays_geom, "géométrie pays")
    inter = drawn.intersection(pays_geom)
    if inter.is_empty:
        return 0.0, inter
    aire_pays = project(pays_geom).area
    if aire_pays <= 0:
        return 0.0, inter
    aire_inter = project(inter).area
    return (aire_inter / aire_pays) * 100.0, inter


def classifier_touches_pays(drawn, fr_to_geom, seuil_split, seuil_bruit,
                             admin1_features):
    """Calcule la couverture pour chaque pays FR dont le polygone
    intersecte le dessin. Applique la désambiguïsation UK à la volée
    (uniquement si le Royaume-Uni est concerné). Retourne une liste de
    dicts {pays, couverture_pct, classification, geometry_geojson}."""
    resultats = []
    drawn_bbox = drawn.bounds

    for pays, geom in fr_to_geom.items():
        if pays in PAYS_UK_EXCLUS_AUTO:
            continue
        gb = geom.bounds
        if gb[2] < drawn_bbox[0] or gb[0] > drawn_bbox[2] or \
           gb[3] < drawn_bbox[1] or gb[1] > drawn_bbox[3]:
            continue
        if not drawn.intersects(geom):
            continue

        # Désambiguïsation UK : si ce pays FR partage le polygone UK,
        # recalculer sa couverture contre son admin_1 propre plutôt que
        # contre le polygone UK entier (piège documenté 8 sept, résolu ici
        # -- voir commentaire d'en-tête).
        if pays in UK_GEONUNIT:
            sub_geom = charger_ne_admin1_geonunit(admin1_features, UK_GEONUNIT[pays])
            if sub_geom is not None:
                geom = sub_geom

        pct, inter = couverture_pct(drawn, geom)
        if pct < seuil_bruit:
            # 14 sept 2026 -- avant, ces portions étaient purement jetées
            # ("imprécision de dessin à main levée" supposée) : aucune trace
            # ne remontait au frontend, aucun moyen de les inclure même
            # volontairement (cas réel remonté par David : une petite
            # portion réelle et voulue d'un pays, pas une imprécision).
            # Conservées désormais sous un type dédié `ignore_bruit`, avec
            # leur géométrie d'intersection (nécessaire si l'utilisateur les
            # force en overlay depuis le panneau de review) -- mais SANS
            # enrichissement Natural Earth ni rédaction LLM automatique de
            # `portion` (voir la boucle plus bas) : par défaut ce sont des
            # candidats à examiner, pas des overlays, pas la peine de
            # consommer un appel LLM pour chacun avant de savoir si
            # l'utilisateur les garde.
            resultats.append({
                "pays": pays,
                "couverture_pct": round(pct, 1),
                "classification": "ignore_bruit",
                "geometry": mapping(inter),
            })
            continue

        classification = "split" if pct >= seuil_split else "overlay"
        resultats.append({
            "pays": pays,
            "couverture_pct": round(pct, 1),
            "classification": classification,
            "geometry": mapping(inter) if classification == "overlay" else None,
        })

    resultats.sort(key=lambda r: -r["couverture_pct"])
    return resultats


class IndexNaturalEarth:
    """Charge les 3 couches Natural Earth UNE SEULE FOIS et construit un
    index spatial (STRtree) par couche -- réutilisé pour tous les pays
    d'un même dessin. Sans ça, un dessin touchant N pays overlay relit et
    reparse ~66 Mo de JSON N fois (mesuré : 26s pour 8 pays avant ce fix,
    contre <1s/pays après)."""

    def __init__(self, populated_places_path: Path, rivers_path: Path, admin1_path: Path):
        t0 = time.time()
        log("Chargement Natural Earth (une seule fois)...")

        with open(populated_places_path, encoding="utf-8") as f:
            pp = json.load(f)
        self._pp_geoms = [shape(f["geometry"]) for f in pp["features"]]
        self._pp_names = [f["properties"].get("NAME") for f in pp["features"]]
        self._pp_tree = STRtree(self._pp_geoms)

        with open(rivers_path, encoding="utf-8") as f:
            riv = json.load(f)
        self._riv_geoms = [shape(f["geometry"]) for f in riv["features"]]
        self._riv_names = [f["properties"].get("name") for f in riv["features"]]
        self._riv_tree = STRtree(self._riv_geoms)

        with open(admin1_path, encoding="utf-8") as f:
            adm = json.load(f)
        self.admin1_features = adm["features"]  # gardé aussi pour la désambiguïsation UK
        self._adm_geoms = [shape(f["geometry"]) for f in adm["features"]]
        self._adm_names = [f["properties"].get("name") for f in adm["features"]]
        self._adm_tree = STRtree(self._adm_geoms)

        log(f"Natural Earth chargé et indexé en {time.time()-t0:.1f}s "
            f"({len(self._pp_geoms)} villes, {len(self._riv_geoms)} fleuves, {len(self._adm_geoms)} régions)")

    def enrichir(self, intersection_geom):
        villes = set()
        for i in self._pp_tree.query(intersection_geom):
            if intersection_geom.contains(self._pp_geoms[i]):
                nom = self._pp_names[i]
                if nom:
                    villes.add(nom)

        fleuves = set()
        for i in self._riv_tree.query(intersection_geom):
            if intersection_geom.intersects(self._riv_geoms[i]):
                nom = self._riv_names[i]
                if nom:
                    fleuves.add(nom)

        regions = set()
        for i in self._adm_tree.query(intersection_geom):
            if intersection_geom.intersects(self._adm_geoms[i]):
                nom = self._adm_names[i]
                if nom:
                    regions.add(nom)

        return {
            "villes": sorted(villes),
            "fleuves": sorted(fleuves),
            "regions": sorted(regions),
        }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--zone-nom", required=True,
                     help="Nom de la zone fictive à créer (contexte donné au LLM pour rédiger les textes portion)")
    ap.add_argument("--sans-llm", action="store_true",
                     help="Ne pas appeler le LLM -- classification seule, portion_proposee reste null (utile pour tester vite sans consommer d'appels API)")
    ap.add_argument("--geometry-file", required=True,
                     help="Fichier GeoJSON du polygone dessiné (Feature ou Polygon brut)")
    ap.add_argument("--seuil-split", type=float, default=SEUIL_SPLIT_DEFAUT)
    ap.add_argument("--seuil-bruit", type=float, default=SEUIL_BRUIT_DEFAUT)
    ap.add_argument("--world-geojson", default="gui/static/world_geo.json",
                     help="Chemin local du fond de carte (à héberger en local plutôt que CDN, voir note livraison)")
    ap.add_argument("--pays-mapping", default="gui/static/pays_mapping.json")
    ap.add_argument("--ne-populated-places", default="generator/data/ne_10m_populated_places.geojson")
    ap.add_argument("--ne-rivers", default="generator/data/ne_10m_rivers_lake_centerlines.geojson")
    ap.add_argument("--ne-admin1", default="generator/data/ne_10m_admin_1_states_provinces.geojson")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        with open(args.geometry_file, encoding="utf-8") as f:
            gj = json.load(f)
        geom_raw = gj["geometry"] if gj.get("type") == "Feature" else gj
        drawn = shape(geom_raw)
        drawn = reparer_geometrie(drawn, "polygone dessiné")

        log("Chargement world.geo.json...")
        en_to_geom = charger_world_geojson(Path(args.world_geojson))
        mapping_fr_en = charger_pays_mapping(Path(args.pays_mapping))
        fr_to_geom, non_disponibles = resoudre_fr_vers_geom(mapping_fr_en, en_to_geom)

        ne_index = IndexNaturalEarth(Path(args.ne_populated_places), Path(args.ne_rivers), Path(args.ne_admin1))

        log(f"Classification ({len(fr_to_geom)} pays résolus, seuil split={args.seuil_split}%, bruit={args.seuil_bruit}%)...")
        classification = classifier_touches_pays(
            drawn, fr_to_geom, args.seuil_split, args.seuil_bruit,
            admin1_features=ne_index.admin1_features,
        )

        avertissement_petits_pays = (
            f"{len(non_disponibles)} petits pays absents de world.geo.json, "
            f"non vérifiables automatiquement si le dessin les concerne "
            f"(à traiter à la main si besoin) : {', '.join(sorted(non_disponibles))}"
        )

        for entry in classification:
            if entry["classification"] == "overlay" and entry["geometry"]:
                inter_geom = shape(entry["geometry"])
                log(f"Enrichissement Natural Earth pour {entry['pays']}...")
                entry["enrichissement"] = ne_index.enrichir(inter_geom)
                if args.sans_llm:
                    entry["portion_proposee"] = None
                    entry["portion_erreur"] = None
                else:
                    log(f"Rédaction LLM de la portion pour {entry['pays']}...")
                    texte, erreur = generer_portion_llm(
                        args.zone_nom, entry["pays"], entry["couverture_pct"], entry["enrichissement"],
                    )
                    entry["portion_proposee"] = texte
                    entry["portion_erreur"] = erreur  # None si tout s'est bien passé

        payload = {
            "ok": True,
            "scenario": args.scenario,
            "seuil_split": args.seuil_split,
            "seuil_bruit": args.seuil_bruit,
            "classification": classification,
            "avertissement_petits_pays": avertissement_petits_pays,
            "petits_pays_non_verifiables": sorted(non_disponibles),
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
