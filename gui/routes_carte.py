"""
routes_carte.py — Blueprint Flask, couche HTTP fine au-dessus de
zone_repository.ZoneRepository.

Remplace l'ensemble des routes /api/carte/* précédemment codées directement
dans gui/app.py (P7 restructuration, overlays, affectation de pays,
personnalisation). Toute la logique métier vit dans zone_repository.py --
ce fichier ne fait que : parser le JSON/query string de la requête, appeler
la méthode du repository correspondante, et traduire les
ZoneRepositoryError en réponses HTTP avec le bon code.

Enregistrement dans gui/app.py (même patron que routes_dashboard.py,
déjà en place pour /api/dashboard) :

    from routes_carte import carte_bp
    app.register_blueprint(carte_bp)

Simplification assumée par cette refonte (David, 10 sept 2026 -- "libre de
renommer/restructurer les routes") : les anciennes paires d'endpoints
impact_X / X (impact_renommage_zone + renommer_zone, impact_reparent_zone +
reparent_zone, impact_split_zone + split_zone) sont fusionnées en un seul
endpoint par opération, avec un flag "dry_run" dans le corps JSON -- ce
contrat existe déjà nativement dans chaque méthode du repository, maintenir
deux routes HTTP séparées n'apportait rien de plus.

Routes volontairement PAS encore portées ici (prochain lot, hors scope de
cette étape) : /api/carte/generer_zone_topdown, /api/carte/creer_zone_vide
(route sœur de dessiner_zone_complete/proposer, migrée le 14 sept -- voir
plus bas), zones_manquantes_enrichissement et les routes d'enrichissement
LLM associées, /api/zones/lookup, /api/zones/manquantes, /api/zones/recheck.
Ces routes restent pour l'instant dans app.py, inchangées.

Correction du 14 septembre 2026 : ce docstring listait encore /api/carte/
propose, /api/carte/impact et /api/carte/dessiner_zone_complete/proposer
comme non portées -- obsolète, les deux premières étaient déjà migrées
sans que ce commentaire soit mis à jour (dette de documentation trouvée en
marge de la migration de la troisième, ce jour-là).
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from flask import Blueprint, jsonify, request

from zone_repository import ZoneRepository, ZoneRepositoryError

carte_bp = Blueprint("carte", __name__)

# 14 sept 2026 -- jusqu'à N appels LLM (un par pays overlay, ~5-10s chacun)
# + chargement Natural Earth (~5-10s) -- même ordre de grandeur que
# TIMEOUT_RESUME_SCENARIOS (app.py).
TIMEOUT_DESSIN_ZONE_COMPLETE = 600


def _repo() -> ZoneRepository:
    """Construit un ZoneRepository à partir de config.json. Import local de
    load_config (défini dans app.py) pour éviter un import circulaire au
    chargement du module -- même pattern que routes_dashboard.py."""
    from app import load_config
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    gui_dir = Path(__file__).parent
    return ZoneRepository(vault_root, gui_dir)


# Sous-chaînes de message d'erreur métier qui doivent renvoyer 409 (conflit)
# plutôt que 404 (introuvable) -- toute ZoneRepositoryError non reconnue ici
# retombe sur 404, cohérent avec le comportement précédent (la plupart des
# erreurs métier de ce module sont des "zone/pays introuvable").
_CONFLIT_SUBSTRINGS = ("existe déjà", "Cycle détecté", "propre parent",
                       "déjà rattachée", "viderait complètement", "Rien à renommer",
                       "sous-zone(s) encore")


def _handle(fn):
    """Exécute fn() (aucun argument) et traduit les erreurs en réponse JSON.
    ZoneRepositoryError -> 404 ou 409 selon le message (voir
    _CONFLIT_SUBSTRINGS). Toute autre exception -> 500, message inclus
    (même comportement défensif que l'ancien carte_assign)."""
    try:
        return jsonify(fn())
    except ZoneRepositoryError as e:
        msg = str(e)
        code = 409 if any(s in msg for s in _CONFLIT_SUBSTRINGS) else 404
        return jsonify({"error": msg}), code
    except Exception as e:  # défensif -- ne doit normalement jamais arriver
        return jsonify({"error": str(e)}), 500


# ── Lecture ──────────────────────────────────────────────────────────────

@carte_bp.route("/api/carte/affectations", methods=["GET"])
def affectations():
    scenario = request.args.get("scenario", "").strip()
    if not scenario:
        return jsonify({"error": "scenario requis"}), 400
    return _handle(lambda: _repo().affectations(scenario))


@carte_bp.route("/api/carte/zones_par_pays", methods=["GET"])
def zones_par_pays():
    """Toutes les zones référençant ce pays dans leur origine_reelle,
    avec type (pays_entier/overlay) et texte portion -- alimente le
    panneau pays quand il est réparti sur plusieurs zones (13 sept 2026)."""
    scenario = request.args.get("scenario", "").strip()
    pays = request.args.get("pays", "").strip()
    if not scenario or not pays:
        return jsonify({"error": "scenario et pays requis"}), 400
    return _handle(lambda: {"pays": pays, "zones": _repo().zones_portant_un_pays(scenario, pays)})


@carte_bp.route("/api/carte/zones_toutes", methods=["GET"])
def zones_toutes():
    scenario = request.args.get("scenario", "").strip()
    if not scenario:
        return jsonify({"error": "scenario requis"}), 400
    return _handle(lambda: {"zones": _repo().zones_toutes(scenario)})


@carte_bp.route("/api/carte/overlays", methods=["GET"])
def overlays_get():
    scenario = request.args.get("scenario", "").strip()
    if not scenario:
        return jsonify({"error": "scenario requis"}), 400
    return _handle(lambda: _repo().overlays_get(scenario))


@carte_bp.route("/api/carte/rechercher_zone", methods=["GET"])
def rechercher_zone():
    scenario = request.args.get("scenario", "").strip()
    q = request.args.get("q", "").strip()
    if not scenario or not q:
        return jsonify({"error": "scenario et q requis"}), 400
    if len(q) < 2:
        return jsonify({"error": "q trop court (minimum 2 caractères)"}), 400
    return _handle(lambda: {"scenario": scenario, "q": q,
                            "resultats": _repo().rechercher_zone(scenario, q)})


@carte_bp.route("/api/carte/arbre_zone", methods=["GET"])
def arbre_zone():
    scenario = request.args.get("scenario", "").strip()
    slug = request.args.get("slug", "").strip()
    if not scenario or not slug:
        return jsonify({"error": "scenario et slug requis"}), 400

    def _do():
        arbre = _repo().arbre_zone(scenario, slug)
        if arbre is None:
            raise ZoneRepositoryError(f"Zone '{slug}' introuvable dans '{scenario}'")
        return {"arbre": arbre}

    return _handle(_do)


# ── Écriture : restructuration de zones (P7) ────────────────────────────
#
# Ces trois opérations restaurent EXACTEMENT le contrat historique en deux
# routes (impact_X = aperçu seul, X = application réelle inconditionnelle)
# pour rester compatibles avec l'app.js actuel, qui appelle toujours les
# deux séparément et n'envoie jamais de `dry_run`. Le jour où carte.js est
# réécrit, ces 6 routes pourront être fusionnées en 3 (un seul endpoint par
# opération avec un flag dry_run explicite) -- reporté pour ne pas casser
# l'usage réel en attendant.

@carte_bp.route("/api/carte/impact_renommage_zone", methods=["POST"])
def impact_renommage_zone():
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    ancien_slug = data.get("ancien_slug", "").strip()
    nouveau_slug = (data.get("nouveau_slug") or "").strip()
    if not scenario or not ancien_slug:
        return jsonify({"error": "scenario et ancien_slug requis"}), 400
    return _handle(lambda: _repo().rename(
        scenario, ancien_slug, nouveau_slug or ancien_slug, None, dry_run=True
    ))


@carte_bp.route("/api/carte/renommer_zone", methods=["POST"])
def renommer_zone():
    """Body JSON : { scenario, ancien_slug, nouveau_slug, nouveau_nom? }.
    Applique TOUJOURS réellement (contrat historique -- l'aperçu se fait
    via impact_renommage_zone avant cet appel, côté client)."""
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    ancien_slug = data.get("ancien_slug", "").strip()
    nouveau_slug = data.get("nouveau_slug", "").strip()
    nouveau_nom = (data.get("nouveau_nom") or "").strip() or None

    if not scenario or not ancien_slug or not nouveau_slug:
        return jsonify({"error": "scenario, ancien_slug, nouveau_slug requis"}), 400
    if not re.match(r"^[a-z0-9_]+$", nouveau_slug):
        return jsonify({"error": "nouveau_slug : lettres minuscules, chiffres, underscores uniquement"}), 400

    return _handle(lambda: _repo().rename(scenario, ancien_slug, nouveau_slug, nouveau_nom, dry_run=False))


@carte_bp.route("/api/carte/impact_reparent_zone", methods=["POST"])
def impact_reparent_zone():
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug = data.get("slug", "").strip()
    nouveau_parent_slug = (data.get("nouveau_parent_slug") or "").strip() or None
    if not scenario or not slug:
        return jsonify({"error": "scenario et slug requis"}), 400
    return _handle(lambda: _repo().reparent(scenario, slug, nouveau_parent_slug, dry_run=True))


@carte_bp.route("/api/carte/reparent_zone", methods=["POST"])
def reparent_zone():
    """Applique TOUJOURS réellement (contrat historique)."""
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug = data.get("slug", "").strip()
    nouveau_parent_slug = (data.get("nouveau_parent_slug") or "").strip() or None
    if not scenario or not slug:
        return jsonify({"error": "scenario et slug requis"}), 400
    return _handle(lambda: _repo().reparent(scenario, slug, nouveau_parent_slug, dry_run=False))


@carte_bp.route("/api/carte/impact_split_zone", methods=["POST"])
def impact_split_zone():
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug_source = data.get("slug_source", "").strip()
    pays_a_extraire = data.get("pays_a_extraire") or []
    cible = data.get("cible") or {}
    if not scenario or not slug_source or not pays_a_extraire:
        return jsonify({"error": "scenario, slug_source, pays_a_extraire requis"}), 400
    return _handle(lambda: _repo().split(scenario, slug_source, pays_a_extraire, cible, dry_run=True))


@carte_bp.route("/api/carte/split_zone", methods=["POST"])
def split_zone():
    """Applique TOUJOURS réellement (contrat historique)."""
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug_source = data.get("slug_source", "").strip()
    pays_a_extraire = data.get("pays_a_extraire") or []
    cible = data.get("cible") or {}
    if not scenario or not slug_source or not pays_a_extraire:
        return jsonify({"error": "scenario, slug_source, pays_a_extraire requis"}), 400
    return _handle(lambda: _repo().split(scenario, slug_source, pays_a_extraire, cible, dry_run=False))


@carte_bp.route("/api/carte/personnaliser_zone", methods=["POST"])
def personnaliser_zone():
    """
    Body JSON : { scenario, slug, couleur?: "#rrggbb"|null, motif?: "..."|null,
                  hachures?: true|false }
    Au moins un de couleur/motif/hachures requis. Écrit directement (pas de
    dry_run -- même doctrine que l'existant). 409 si `slug` n'est pas niveau 1
    (point 4 de la refonte : plus de couleur/motif/hachures propres sur une
    sous-zone).
    """
    data = request.get_json() or {}
    scenario = (data.get("scenario") or "").strip()
    slug = (data.get("slug") or "").strip()
    if not scenario or not slug:
        return jsonify({"error": "scenario et slug requis"}), 400
    if "couleur" not in data and "motif" not in data and "hachures" not in data:
        return jsonify({"error": "au moins un de couleur/motif/hachures requis"}), 400

    kwargs = {}
    if "couleur" in data:
        kwargs["couleur"] = data.get("couleur")
    if "motif" in data:
        kwargs["motif"] = data.get("motif")
    if "hachures" in data:
        kwargs["hachures"] = bool(data.get("hachures"))

    def _do():
        try:
            return _repo().personnaliser(scenario, slug, **kwargs)
        except ZoneRepositoryError as e:
            # Cas spécial : "n'est pas niveau 1" doit remonter en 409 (conflit
            # de règle métier), pas 404 (zone introuvable) -- seul cas de ce
            # module où le message ne matche aucune substring de
            # _CONFLIT_SUBSTRINGS telle quelle.
            if "niveau 1" in str(e):
                raise ZoneRepositoryError(f"CONFLIT::{e}")
            raise

    try:
        return jsonify(_do())
    except ZoneRepositoryError as e:
        msg = str(e)
        if msg.startswith("CONFLIT::"):
            return jsonify({"error": msg[len("CONFLIT::"):]}), 409
        code = 409 if any(s in msg for s in _CONFLIT_SUBSTRINGS) else 404
        return jsonify({"error": msg}), code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Écriture : affectation pays ──────────────────────────────────────────

@carte_bp.route("/api/carte/assign", methods=["POST"])
def assign():
    """
    Body JSON : {
      pays, scenario, action: "absorber"|"creer",
      zone_slug (si absorber), nouvelle_zone: {slug, nom, description} (si creer)
    }
    """
    data = request.get_json() or {}
    pays = data.get("pays", "").strip()
    scenario = data.get("scenario", "").strip()
    action = data.get("action", "").strip()

    if not pays or not scenario or action not in ("absorber", "creer"):
        return jsonify({"error": "pays, scenario, action (absorber|creer) requis"}), 400

    return _handle(lambda: _repo().assign_pays(
        scenario, pays, action,
        zone_slug=data.get("zone_slug"), nouvelle_zone=data.get("nouvelle_zone"),
    ))


@carte_bp.route("/api/carte/desaffecter", methods=["POST"])
def desaffecter():
    """Body JSON : { pays, scenario } -- remet zones_pays.json à null."""
    data = request.get_json() or {}
    pays = data.get("pays", "").strip()
    scenario = data.get("scenario", "").strip()
    if not pays or not scenario:
        return jsonify({"error": "pays et scenario requis"}), 400
    return _handle(lambda: _repo().desaffecter(scenario, pays))


# ── Écriture : overlays ──────────────────────────────────────────────────

@carte_bp.route("/api/carte/overlays/creer", methods=["POST"])
def overlays_creer():
    """
    Body JSON : { scenario, zone_slug, pays, geometry (GeoJSON), portion? }
    Découpage à la volée : si `pays` n'est pas encore dans origine_reelle
    de `zone_slug`, l'entrée y est créée automatiquement.
    """
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    zone_slug = data.get("zone_slug", "").strip()
    pays = data.get("pays", "").strip()
    geometry = data.get("geometry")
    portion = (data.get("portion") or "").strip() or None

    if not scenario or not zone_slug or not pays or not geometry:
        return jsonify({"error": "scenario, zone_slug, pays, geometry requis"}), 400

    return _handle(lambda: _repo().overlay_creer(scenario, zone_slug, pays, geometry, portion))


@carte_bp.route("/api/carte/overlays/supprimer", methods=["POST"])
def overlays_supprimer():
    """Body JSON : { scenario, id }."""
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    feature_id = data.get("id", "").strip()
    if not scenario or not feature_id:
        return jsonify({"error": "scenario, id requis"}), 400
    return _handle(lambda: _repo().overlay_supprimer(scenario, feature_id))


@carte_bp.route("/api/carte/villes", methods=["GET"])
def villes():
    """
    Sert le fichier statique villes_principales.json (précalculé par
    extraire_villes_principales.py à partir de Natural Earth) -- capitales,
    mégapoles, et villes de plus d'1M d'habitants par défaut. Géographie
    réelle, indépendante du scénario -- pas de paramètre scenario ici.
    """
    path = Path(__file__).parent / "static" / "villes_principales.json"
    if not path.exists():
        return jsonify({"error": "villes_principales.json introuvable -- "
                                  "lance extraire_villes_principales.py --apply d'abord"}), 404
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


# ── Écriture : création d'une zone niveau 1 (formulaire manuel ou top-down) ─

@carte_bp.route("/api/carte/creer_zone_niveau1", methods=["POST"])
def creer_zone_niveau1():
    """
    Body JSON : { scenario, slug, nom, type, statut,
                  origine_reelle: [{entite, type_entite, portion?}, ...],
                  description?, tensions_internes?, periode_transition?,
                  lieux_emblematiques?, relations?, sources_attestees? }

    Après écriture réussie, tente en best-effort un appel à
    generator/reparenter_sous_zones_orphelines.py (sous-processus, timeout
    court, codebase séparée de gui/) -- un échec de cette étape secondaire
    n'affecte jamais le résultat de la création elle-même, déjà actée.
    """
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug = data.get("slug", "").strip()
    nom = data.get("nom", "").strip()
    type_zone = data.get("type", "").strip()
    statut = data.get("statut", "").strip()
    origine_reelle = data.get("origine_reelle") or []

    if not scenario or not slug or not nom or not type_zone or not statut:
        return jsonify({"error": "scenario, slug, nom, type, statut requis"}), 400

    def _do():
        resultat = _repo().creer_zone_n1(
            scenario, slug, nom, type_zone, statut, origine_reelle,
            description=(data.get("description") or "").strip(),
            tensions_internes=(data.get("tensions_internes") or "").strip(),
            periode_transition=data.get("periode_transition"),
            lieux_emblematiques=data.get("lieux_emblematiques"),
            relations=data.get("relations"),
            sources_attestees=data.get("sources_attestees"),
        )

        sous_zones_reparentees = []
        try:
            from app import load_config
            cfg = load_config()
            pipeline_dir = Path(cfg.get("pipeline_dir", ""))
            proc = subprocess.run(
                [sys.executable, "reparenter_sous_zones_orphelines.py",
                 "--scenario", scenario, "--zone-cible", slug, "--json"],
                cwd=pipeline_dir, capture_output=True, text=True,
                timeout=15, stdin=subprocess.DEVNULL,
            )
            sortie = proc.stdout.strip()
            if sortie:
                payload = json.loads(sortie.splitlines()[-1])
                if payload.get("ok"):
                    sous_zones_reparentees = payload.get("reparentees", [])
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, IndexError):
            pass  # best-effort -- la création de la zone a déjà réussi

        resultat["sous_zones_reparentees"] = sous_zones_reparentees
        return resultat

    return _handle(_do)


# ── Écriture : suppression d'une zone niveau 1 ──────────────────────────────

@carte_bp.route("/api/carte/impact_supprimer_zone", methods=["POST"])
def impact_supprimer_zone():
    data = request.get_json() or {}
    scenario = (data.get("scenario") or "").strip()
    slug = (data.get("slug") or "").strip()
    if not scenario or not slug:
        return jsonify({"error": "scenario et slug requis"}), 400
    return _handle(lambda: _repo().supprimer_zone_n1(scenario, slug, dry_run=True))


@carte_bp.route("/api/carte/supprimer_zone", methods=["POST"])
def supprimer_zone():
    """Applique réellement -- 409 si la zone a encore des sous-zones
    rattachées (pas de suppression en cascade silencieuse)."""
    data = request.get_json() or {}
    scenario = (data.get("scenario") or "").strip()
    slug = (data.get("slug") or "").strip()
    if not scenario or not slug:
        return jsonify({"error": "scenario et slug requis"}), 400
    return _handle(lambda: _repo().supprimer_zone_n1(scenario, slug, dry_run=False))

# ── Lecture/écriture : proposition LLM, ignorer un pays, impact bascule ─────

@carte_bp.route("/api/carte/propose", methods=["POST"])
def propose():
    """
    Propose une affectation de zone pour un pays donné (appel LLM unique).
    Body JSON : { pays, scenario }
    """
    data = request.get_json() or {}
    pays = (data.get("pays") or "").strip()
    scenario = (data.get("scenario") or "").strip()
    if not pays or not scenario:
        return jsonify({"error": "pays et scenario requis"}), 400

    repo = _repo()
    zones_n1 = repo.zones_n1_colorees(scenario)
    fresh_index = repo.origine_reelle_index(scenario)
    zone_to_pays = {}
    for pays_norm, slug in fresh_index.items():
        zone_to_pays.setdefault(slug, []).append(pays_norm)

    zones_desc = "\n".join(
        f"- {z['slug']} ({z['nom']}) : {z['description'][:300]}"
        + (f" [pays déjà affectés : {', '.join(sorted(zone_to_pays[z['slug']])[:10])}]"
           if z['slug'] in zone_to_pays else "")
        for z in zones_n1
    ) or "(aucune zone existante)"

    prompt = f"""Tu travailles sur l'univers narratif spéculatif "Ourrassol 2098", scénario "{scenario}".
Voici les zones géopolitiques de niveau 1 (N1) déjà définies pour ce scénario :

{zones_desc}

Le pays réel (2026) "{pays}" n'a pas encore d'affectation à une zone 2098 dans ce scénario.

Réponds UNIQUEMENT en JSON valide (rien avant, rien après), avec ce format exact :
{{
  "zone_existante_recommandee": "slug_de_zone_ou_null",
  "nouvelle_zone_proposee": {{"slug": "nouveau_slug", "nom": "Nom de la zone", "description": "1-2 phrases"}} ou null,
  "justification": "1-3 phrases expliquant le choix, cohérentes avec la logique narrative du scénario"
}}

Recommande une zone existante si "{pays}" y a narrativement sa place. Base ta décision en priorité sur la proximité géographique/continentale avec les pays déjà affectés listés entre crochets (quand ils sont présents) — la description narrative seule peut ne pas mentionner tous les pays membres. Propose une nouvelle zone N1 uniquement si aucune zone existante ne convient géographiquement ni narrativement."""

    try:
        from app import _call_llm_text
        raw_response = _call_llm_text(prompt)
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        proposal = json.loads(cleaned)
        return jsonify({"ok": True, "proposal": proposal})
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500


@carte_bp.route("/api/carte/ignorer", methods=["POST"])
def ignorer():
    """Marque un pays comme blanc intentionnel pour ce scénario."""
    data = request.get_json() or {}
    pays = (data.get("pays") or "").strip()
    scenario = (data.get("scenario") or "").strip()
    if not pays or not scenario:
        return jsonify({"error": "pays et scenario requis"}), 400
    return _handle(lambda: _repo().marquer_pays_ignore(scenario, pays))


@carte_bp.route("/api/carte/impact", methods=["POST"])
def impact():
    """
    Rapport d'impact en lecture seule pour une bascule de zone (pas
    d'écriture sur les fiches, seulement un rapport de référence).
    Body JSON : { pays, scenario, action: "absorber"|"creer",
                  zone_slug (si absorber), nouvelle_zone (si creer) }
    """
    data = request.get_json() or {}
    pays = (data.get("pays") or "").strip()
    scenario = (data.get("scenario") or "").strip()
    action = (data.get("action") or "").strip()
    if not pays or not scenario:
        return jsonify({"error": "pays et scenario requis"}), 400
    return _handle(lambda: _repo().impact_bascule_pays(
        scenario, pays, action,
        zone_slug=data.get("zone_slug"), nouvelle_zone=data.get("nouvelle_zone"),
    ))


# ── S11 : dessiner une zone complète ────────────────────────────────────────
# Migrée depuis app.py le 14 sept 2026 (dette architecturale notée dès la
# refonte du 12 sept -- seule route "Carte" jamais portée ici, laissée de
# côté par prudence sur un outil déjà central et fonctionnel plutôt que par
# oubli). Aucun changement de comportement : même sous-processus, même
# contrat JSON, mêmes codes d'erreur -- seule l'adaptation Blueprint change
# (`_repo()`/`load_config` locaux au lieu des globales de app.py, import
# différé de `load_config` pour éviter l'import circulaire, même pattern
# que `_repo()` en tête de ce fichier). `creer_zone_vide`, route sœur
# utilisée par le même flux frontend (cas d'un dessin sans aucun pays
# atteignant le seuil de split), reste dans app.py -- hors scope de cette
# migration, pas demandée.

@carte_bp.route("/api/carte/dessiner_zone_complete/proposer", methods=["POST"])
def dessiner_zone_complete_proposer():
    """
    Calcule la classification split/overlay/ignoré d'un dessin de zone
    complète (S11) -- appelle generator/zone_dessin_complet.py --json en
    sous-processus. N'ÉCRIT JAMAIS dans le vault (même doctrine que
    /api/carte/generer_enrichissement_zone, resté dans app.py) --
    l'application réelle réutilise /api/carte/assign, /api/carte/
    creer_zone_vide et /api/carte/overlays/creer, appelées séparément par
    le frontend après review humaine dans le panneau.

    Body JSON : {
      "scenario": "fortress_world",
      "zone_nom": "Zone Test",
      "geometry": { "type": "Polygon", "coordinates": [...] },  // GeoJSON standard
      "seuil_split": 90.0,   // optionnel
      "seuil_bruit": 2.0     // optionnel
    }
    """
    from app import load_config
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    gui_dir = Path(__file__).parent
    data = request.get_json() or {}

    scenario = (data.get("scenario") or "").strip()
    zone_nom = (data.get("zone_nom") or "").strip()
    geometry = data.get("geometry")
    seuil_split = data.get("seuil_split", 90.0)
    seuil_bruit = data.get("seuil_bruit", 2.0)

    if not scenario or not zone_nom or not geometry:
        return jsonify({"error": "scenario, zone_nom, geometry requis"}), 400

    world_geojson = gui_dir / "static" / "world_geo.json"
    pays_mapping = gui_dir / "static" / "pays_mapping.json"
    ne_dir = pipeline_dir / "data"

    geometry_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".geojson", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(geometry, tmp)
            geometry_path = tmp.name

        cmd = [
            sys.executable, "zone_dessin_complet.py",
            "--scenario", scenario, "--zone-nom", zone_nom,
            "--geometry-file", geometry_path,
            "--seuil-split", str(seuil_split), "--seuil-bruit", str(seuil_bruit),
            "--world-geojson", str(world_geojson),
            "--pays-mapping", str(pays_mapping),
            "--ne-populated-places", str(ne_dir / "ne_10m_populated_places.geojson"),
            "--ne-rivers", str(ne_dir / "ne_10m_rivers_lake_centerlines.geojson"),
            "--ne-admin1", str(ne_dir / "ne_10m_admin_1_states_provinces.geojson"),
            "--json",
        ]

        try:
            resultat = subprocess.run(
                cmd, cwd=pipeline_dir, capture_output=True, text=True,
                timeout=TIMEOUT_DESSIN_ZONE_COMPLETE, stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            return jsonify({"error": f"Classification expirée après "
                                      f"{TIMEOUT_DESSIN_ZONE_COMPLETE}s"}), 504
        except FileNotFoundError:
            return jsonify({"error": f"zone_dessin_complet.py introuvable "
                                      f"dans {pipeline_dir}"}), 500
    finally:
        if geometry_path:
            try:
                os.unlink(geometry_path)
            except OSError:
                pass

    sortie = resultat.stdout.strip()
    if not sortie:
        return jsonify({"error": f"Aucune sortie du sous-processus "
                                  f"(code {resultat.returncode}) : {resultat.stderr[-800:]}"}), 500
    try:
        payload = json.loads(sortie.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return jsonify({"error": f"Sortie non-JSON du sous-processus : {sortie[-800:]}"}), 500

    if not payload.get("ok"):
        return jsonify({"error": payload.get("error", "Erreur inconnue côté classification")}), 500

    return jsonify(payload)
