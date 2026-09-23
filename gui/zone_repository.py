"""
zone_repository.py — Point d'écriture UNIQUE pour toute opération touchant une
zone géographique 2098 (Ourrassol).

Contexte (refonte Carte, 10 sept 2026) : jusqu'ici, chaque opération (renommer,
déplacer, scinder, affecter un pays, personnaliser, dessiner un overlay) avait
sa propre logique de propagation, écrite indépendamment au fil des chantiers
(8-15 juillet, 8-10 septembre). Résultat : trois sources de vérité pour une
même zone, synchronisées à la main, avec des trous à chaque fois qu'une des
trois n'était pas mise à jour (split -> zones_pays.json oublié, corrigé le 15
juillet ; reparent -> zones_pays.json oublié, corrigé sur Nuuk-Forteresse ;
renommer -> overlays oubliés, trouvé le 10 septembre, jamais corrigé avant
cette refonte).

Les trois sources de vérité restent inchangées dans leur FORMAT (rien ne
change côté données déjà présentes dans le vault) :
  1. geographie/{scenario}.md            — frontmatter YAML (slug/nom/niveau/
                                            parent/origine_reelle/couleur/
                                            motif/relations) + corps markdown
  2. zones_pays.json                     — index pays -> zone, dérivé
  3. gui/static/geo_overlays/{scenario}.geojson — tracés dessinés à la main

Ce qui change : plus AUCUNE route Flask n'écrit un de ces trois fichiers
directement. Tout passe par ZoneRepository, qui garantit que les trois
avancent ensemble ou pas du tout.

Convention conservée : chaque méthode publique d'écriture accepte
dry_run=True (aucune écriture, retourne un rapport d'impact) et
dry_run=False (écrit réellement, .bak automatique avant chaque fichier
touché, retourne un résumé). C'est la même doctrine que le code existant
(voir USER_MANUAL_COMPLET.md §7) — la refonte centralise le MÉCANISME, elle
ne change pas le contrat déjà validé par David.
"""

import json
import re
import shutil
import unicodedata
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


# Couleur/motif ne sont éditables QUE sur une zone niveau 1 (décision David,
# 10 sept 2026, point 4 de la refonte) : une sous-zone (niveau 2/3) hérite
# toujours de la couleur/motif de sa racine N1, aucun override possible.
MOTIFS_VALIDES = ["radiation", "flamme", "vague", "crane", "aucun"]

N_PATTERNS = 5          # nombre de motifs génériques distincts (définis côté frontend)

ZONE_TYPES = ["bloc_continental", "union_regionale", "territoire_autonome",
              "territoire_herite", "region", "ville", "infrastructure",
              "site_strategique", "zone_sinistree", "autre"]
ZONE_STATUTS = ["dominant", "stable", "fragmenté", "en_declin", "disparu", "emergent"]
TYPE_ENTITE_REELLE = ["pays", "etat_federe", "province", "region_administrative", "autre"]

_REMAP_PAYS = {
    "états-unis d'amérique": "états-unis",
    "russie (sibérie orientale)": "russie",
    "danemark (groenland)": "danemark",
    "danemark / groenland": "danemark",
    "canada (nunavut)": "canada",
    "norvège (svalbard)": "norvège",
    "brésil (amazonie)": "brésil",
    "suisse (genève)": "suisse",
    "kenya (nairobi)": "kenya",
    "sibérie (entité fédérale russe)": "russie",
    "danemark (groenland inclus)": "danemark",
    "arctique russe (mourmansk)": "russie",
}


def _normalise_pays(s: str) -> str:
    """Normalise un nom de pays pour le matching (identique à l'existant)."""
    return _REMAP_PAYS.get((s or "").lower().strip(), (s or "").lower().strip())


def _tokens_entite(texte: str) -> list:
    """Découpe une chaîne `entite` en tokens comparables à un nom de pays --
    gère virgules, slashes, contenu entre parenthèses. Logique reprise telle
    quelle (validée le 14 juillet 2026, cas Groenland/Danemark)."""
    texte = (texte or "").lower()
    interieur_parentheses = re.findall(r"\(([^)]*)\)", texte)
    texte_sans_parentheses = re.sub(r"\([^)]*\)", "", texte)
    morceaux = [texte_sans_parentheses] + interieur_parentheses
    tokens = []
    for m in morceaux:
        tokens += [t.strip() for t in re.split(r"[,/]", m)]
    return [t for t in tokens if t]


def _entite_references_pays(entite: str, pays_normalises: set) -> bool:
    return any(_normalise_pays(t) in pays_normalises for t in _tokens_entite(entite))


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    """h, s, l dans [0, 1] -> couleur hex (identique à l'existant)."""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


class ZoneRepositoryError(Exception):
    """Erreur métier (zone introuvable, collision de slug, opération invalide
    sur une sous-zone, etc.). Toujours porteuse d'un message directement
    affichable côté GUI — jamais une trace Python brute."""


def _fold(s: str) -> str:
    """Normalisation insensible à la casse/accents (recherche substring)."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()


@dataclass
class GeoFile:
    """État en mémoire d'une fiche geographie/{scenario}.md le temps d'une
    opération : texte brut complet (pour le .bak), frontmatter parsé, corps
    markdown brut (parts[2], jamais reparsé — modifié par regex ciblée)."""
    path: Path
    raw: str
    fm: dict
    body: str

    @property
    def zones(self) -> list:
        return self.fm.setdefault("zones", [])


class ZoneRepository:
    """
    Usage :
        repo = ZoneRepository(vault_root, gui_dir)
        rapport = repo.rename(scenario, "interzone", "zone_euro_sud",
                               "Zone Euro Sud", dry_run=True)
        # ... afficher le rapport, demander confirmation ...
        resultat = repo.rename(scenario, "interzone", "zone_euro_sud",
                                "Zone Euro Sud", dry_run=False)

    Aucune méthode ne prend de dépendance sur Flask (pas de `request`, pas de
    `jsonify`) — les routes du Blueprint routes_carte.py restent une fine
    couche HTTP au-dessus de cette classe, testable en dehors du serveur.
    """

    def __init__(self, vault_root: Path, gui_dir: Path):
        self.vault_root = Path(vault_root)
        self.gui_dir = Path(gui_dir)

    # ── chemins ──────────────────────────────────────────────────────────

    def _geo_path(self, scenario: str) -> Path:
        return self.vault_root / "geographie" / f"{scenario}.md"

    def _zones_pays_path(self) -> Path:
        return self.gui_dir / "zones_pays.json"

    def _overlay_path(self, scenario: str) -> Path:
        return self.gui_dir / "static" / "geo_overlays" / f"{scenario}.geojson"

    # ── lecture / écriture bas niveau (chaque fichier a son propre .bak) ──

    def _load_geo(self, scenario: str) -> GeoFile:
        path = self._geo_path(scenario)
        if not path.exists():
            raise ZoneRepositoryError(f"Fiche géographie introuvable : {path}")
        raw = path.read_text(encoding="utf-8")
        parts = raw.split("---", 2)
        if len(parts) < 3:
            raise ZoneRepositoryError(
                "Format de fiche géographie inattendu (frontmatter manquant)"
            )
        fm = yaml.safe_load(parts[1]) or {}
        return GeoFile(path=path, raw=raw, fm=fm, body=parts[2])

    def _save_geo(self, gf: GeoFile) -> None:
        bak = gf.path.with_suffix(gf.path.suffix + ".bak")
        bak.write_text(gf.raw, encoding="utf-8")
        new_fm = yaml.dump(gf.fm, allow_unicode=True, sort_keys=False,
                            default_flow_style=False)
        gf.path.write_text("---\n" + new_fm + "---" + gf.body, encoding="utf-8")

    def _load_zones_pays(self) -> dict:
        path = self._zones_pays_path()
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_zones_pays(self, zp: dict) -> None:
        path = self._zones_pays_path()
        if path.exists():
            shutil.copy(path, path.with_suffix(path.suffix + ".bak"))
        path.write_text(json.dumps(zp, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_overlays(self, scenario: str) -> dict:
        path = self._overlay_path(scenario)
        if not path.exists():
            return {"type": "FeatureCollection", "features": []}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ZoneRepositoryError(f"geojson invalide ({path.name}) : {e}")

    def _save_overlays(self, scenario: str, fc: dict) -> None:
        path = self._overlay_path(scenario)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.copy(path, path.with_suffix(".geojson.bak"))
        path.write_text(json.dumps(fc, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_instances_touchees(self, scenario: str, slug: str) -> list:
        """Scanne instances/ + event_instances/ pour ce scénario :
        localisation.zone == slug. Lecture seule (utilisée par rename en
        dry_run ET en apply — l'écriture réelle est faite par
        _rename_instances)."""
        touches = []
        for dossier in ("instances", "event_instances"):
            d = self.vault_root / dossier
            if not d.exists():
                continue
            for f in d.glob("*.md"):
                try:
                    raw = f.read_text(encoding="utf-8")
                except OSError:
                    continue
                parts = raw.split("---", 2)
                if len(parts) < 3:
                    continue
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    continue
                if fm.get("scenario") != scenario:
                    continue
                loc = fm.get("localisation") or {}
                if loc.get("zone") != slug:
                    continue
                touches.append({
                    "path": f, "fm": fm, "body_after_fm": parts[2],
                    "slug": fm.get("slug", f.stem), "type": fm.get("type", dossier),
                })
        return touches

    # ── helpers zone (lecture pure, aucune écriture) ───────────────────────

    @staticmethod
    def _find(zones: list, slug: str) -> Optional[dict]:
        return next((z for z in zones if z.get("slug") == slug), None)

    @staticmethod
    def _enfants_directs(zones: list, slug: str) -> list:
        return [z for z in zones if z.get("parent") == slug]

    def resolve_root_n1(self, zones: list, slug: str) -> Optional[dict]:
        """Remonte la chaîne `parent` jusqu'à la racine niveau 1 d'une zone
        (elle-même si elle est déjà niveau 1). Anti-cycle : s'arrête si un
        slug est revisité. Utilisé pour l'héritage couleur/motif (point 4 de
        la refonte, 10 sept) — une sous-zone n'a plus de couleur propre, elle
        emprunte celle de cette racine."""
        by_slug = {z.get("slug"): z for z in zones}
        courant = self._find(zones, slug)
        vus = set()
        while courant is not None:
            s = courant.get("slug")
            if s in vus:
                break
            vus.add(s)
            if int(courant.get("niveau", 1)) == 1:
                return courant
            courant = by_slug.get(courant.get("parent"))
        return None

    def couleur_motif_effectifs(self, zones: list, slug: str) -> tuple:
        """(couleur, motif) réellement appliqués à `slug` — toujours ceux de
        la racine N1, jamais un override sur la sous-zone elle-même (voir
        resolve_root_n1). Retourne (None, None) si la zone ou sa racine sont
        introuvables — l'appelant retombe alors sur le calcul automatique
        (roue de teintes)."""
        racine = self.resolve_root_n1(zones, slug)
        if racine is None:
            return None, None
        return racine.get("couleur"), racine.get("motif")

    # ── RENOMMER (P7) — premier cas remis à plat par la refonte ────────────
    #
    # Fix structurel de cette refonte : la version précédente de rename ne
    # touchait que (1) geographie/{scenario}.md, (2) zones_pays.json et les
    # fiches instances/event_instances — jamais (3) les overlays dessinés,
    # d'où le tracé orphelin trouvé le 10 septembre sur Interzone -> Zone
    # Euro Sud (1 feature sur 8 restée avec l'ancien slug). Cette version
    # ajoute la migration des features overlay comme quatrième étape,
    # systématique, plus jamais un cas particulier oublié.

    @staticmethod
    def _rename_body_text(body: str, old_slug: str, new_slug: str,
                           old_nom: Optional[str] = None,
                           new_nom: Optional[str] = None) -> tuple:
        """Renomme dans le corps markdown (hors frontmatter) : wikilinks
        "sous [[old_slug]]" des enfants directs, le header de la zone si le
        nom change, les lignes **Rivaux**/**Alliés** (texte brut, pas des
        wikilinks — relations.allies/rivaux peut référencer n'importe quelle
        zone du scénario, pas seulement les enfants directs). Logique
        identique à l'implémentation validée le 12 juillet 2026, reprise
        telle quelle (pas de raison de la retoucher, jamais mise en cause
        par aucun bug relevé depuis)."""
        changed = False

        pattern_sous = re.compile(r"sous \[\[" + re.escape(old_slug) + r"\]\]")
        new_body, n = pattern_sous.subn(f"sous [[{new_slug}]]", body)
        if n:
            changed = True
            body = new_body

        if old_nom and new_nom and old_nom != new_nom:
            header_pattern = re.compile(
                r"^(#{1,6}) " + re.escape(old_nom) + r"( — sous \[\[.+?\]\])?$",
                re.MULTILINE
            )
            new_body2, n2 = header_pattern.subn(
                lambda m: f"{m.group(1)} {new_nom}{m.group(2) or ''}", body
            )
            if n2:
                changed = True
                body = new_body2

        relations_pattern = re.compile(r"^(\*\*(?:Rivaux|Alliés)\*\* : .*)$", re.MULTILINE)
        slug_boundary = re.compile(r"(?<![a-z0-9_])" + re.escape(old_slug) + r"(?![a-z0-9_])")

        def _sub_relations_line(m):
            nonlocal changed
            line, n3 = slug_boundary.subn(new_slug, m.group(1))
            if n3:
                changed = True
            return line

        body = relations_pattern.sub(_sub_relations_line, body)
        return body, changed

    def _rename_overlays(self, scenario: str, old_slug: str, new_slug: str,
                          dry_run: bool) -> list:
        """Migre toute feature overlay taguée `zone_slug: old_slug` vers
        `new_slug`. C'est l'étape qui manquait avant cette refonte."""
        fc = self._load_overlays(scenario)
        touches = [f for f in fc.get("features", [])
                   if f.get("properties", {}).get("zone_slug") == old_slug]
        if not dry_run and touches:
            for f in touches:
                f["properties"]["zone_slug"] = new_slug
            self._save_overlays(scenario, fc)
        return [f.get("properties", {}).get("id") for f in touches]

    def _rename_instances(self, scenario: str, old_slug: str, new_slug: str,
                           dry_run: bool) -> list:
        touches = self._load_instances_touchees(scenario, old_slug)
        if not dry_run:
            for t in touches:
                fm = t["fm"]
                loc = fm.get("localisation") or {}
                loc["zone"] = new_slug
                fm["localisation"] = loc
                new_fm = yaml.dump(fm, allow_unicode=True, sort_keys=False,
                                    default_flow_style=False)
                t["path"].write_text("---\n" + new_fm + "---" + t["body_after_fm"],
                                      encoding="utf-8")
        return [{"slug": t["slug"], "type": t["type"]} for t in touches]

    def rename(self, scenario: str, old_slug: str, new_slug: str,
               new_nom: Optional[str] = None, dry_run: bool = True) -> dict:
        """
        Renomme une zone (slug et/ou nom affiché), en propageant vers LES
        QUATRE stores concernés : frontmatter (zone elle-même + enfants +
        relations + wikilinks du corps), zones_pays.json, overlays
        dessinés, fiches instances/event_instances.

        dry_run=True  : n'écrit rien, retourne un rapport d'impact complet.
        dry_run=False : applique réellement (.bak avant chaque fichier
                        touché), retourne un résumé des compteurs.

        Lève ZoneRepositoryError si la zone source n'existe pas ou si
        new_slug est déjà pris par une autre zone du même scénario.
        """
        gf = self._load_geo(scenario)
        zones = gf.zones
        target = self._find(zones, old_slug)
        if not target:
            raise ZoneRepositoryError(f"Zone '{old_slug}' introuvable dans {scenario}")
        if new_slug != old_slug and self._find(zones, new_slug):
            raise ZoneRepositoryError(f"Le slug '{new_slug}' existe déjà dans ce scénario")
        # Le no-op n'est une erreur qu'à l'application réelle -- un dry_run
        # avec nouveau_slug omis (aperçu d'impact avant d'avoir choisi le
        # nouveau nom) doit rester valide, pas être rejeté prématurément.
        if not dry_run and old_slug == new_slug and not new_nom:
            raise ZoneRepositoryError("Rien à renommer : slug et nom inchangés")

        old_nom = target.get("nom")
        enfants = self._enfants_directs(zones, old_slug)
        zones_relations_liees = [
            z.get("slug") for z in zones
            if isinstance(z.get("relations"), dict) and (
                old_slug in (z["relations"].get("allies") or []) or
                old_slug in (z["relations"].get("rivaux") or [])
            )
        ]

        if dry_run:
            instances_liees = self._load_instances_touchees(scenario, old_slug)
            zp = self._load_zones_pays()
            pays_lies = [p for p, s in zp.get(scenario, {}).items() if s == old_slug]
            fc = self._load_overlays(scenario)
            overlays_lies = [
                f.get("properties", {}).get("id") for f in fc.get("features", [])
                if f.get("properties", {}).get("zone_slug") == old_slug
            ]
            return {
                "zone": {"slug": old_slug, "nom": old_nom,
                         "niveau": target.get("niveau"), "parent": target.get("parent")},
                "enfants_directs": [{"slug": e.get("slug"), "nom": e.get("nom")} for e in enfants],
                "zones_relations_liees": zones_relations_liees,
                "instances_liees": [{"slug": i["slug"], "type": i["type"]} for i in instances_liees],
                "pays_zones_pays_json": pays_lies,
                "overlays_lies": overlays_lies,
                "rien_detecte": not (enfants or zones_relations_liees or instances_liees
                                      or pays_lies or overlays_lies),
            }

        # ── application réelle ──
        for z in zones:
            rel = z.get("relations")
            if not isinstance(rel, dict):
                continue
            for cle in ("allies", "rivaux"):
                lst = rel.get(cle)
                if isinstance(lst, list) and old_slug in lst:
                    rel[cle] = [new_slug if s == old_slug else s for s in lst]

        target["slug"] = new_slug
        if new_nom:
            target["nom"] = new_nom
        for e in enfants:
            e["parent"] = new_slug

        new_body, body_maj = self._rename_body_text(gf.body, old_slug, new_slug, old_nom, new_nom)
        gf.body = new_body
        self._save_geo(gf)

        instances_touchees = self._rename_instances(scenario, old_slug, new_slug, dry_run=False)

        zp = self._load_zones_pays()
        sc = zp.get(scenario, {})
        pays_touches = [p for p, s in sc.items() if s == old_slug]
        for p in pays_touches:
            sc[p] = new_slug
        zp[scenario] = sc
        if pays_touches:
            self._save_zones_pays(zp)

        overlays_touches = self._rename_overlays(scenario, old_slug, new_slug, dry_run=False)

        return {
            "ok": True,
            "nouveau_slug": new_slug,
            "enfants_maj": len(enfants),
            "zones_relations_maj": len(zones_relations_liees),
            "body_maj": body_maj,
            "instances_maj": len(instances_touchees),
            "pays_maj": len(pays_touches),
            "overlays_maj": len(overlays_touches),
        }

    # ── PERSONNALISER (couleur/motif) — restreint aux zones niveau 1 ───────
    #
    # Point 4 de la refonte : les sous-zones n'ont plus de couleur/motif
    # propre. Toute tentative de personnaliser une zone niveau 2/3 est
    # rejetée explicitement (avant, c'était silencieusement accepté et
    # simplement jamais affiché — source de confusion, cf. bug "Appliqué
    # mais rien ne change" du 10 septembre, dont la vraie cause était une
    # autre confusion mais qui aurait pu être ce cas-ci).

    def personnaliser(self, scenario: str, slug: str,
                       couleur: Optional[str] = "__unset__",
                       motif: Optional[str] = "__unset__",
                       hachures: Optional[bool] = None) -> dict:
        """
        couleur/motif : passer None efface explicitement le champ (retour à
        l'automatique) ; passer "__unset__" (défaut) laisse le champ
        inchangé. hachures : True/False pour activer/désactiver les hachures
        génériques (désactivées par défaut sur toute nouvelle zone -- voir
        zones_n1_colorees) ; None (défaut) laisse le champ inchangé. Lève
        ZoneRepositoryError si `slug` n'est pas niveau 1.
        """
        if couleur == "__unset__" and motif == "__unset__" and hachures is None:
            raise ZoneRepositoryError("Au moins un de couleur/motif/hachures requis")
        if couleur not in ("__unset__", None) and not re.match(r"^#[0-9a-fA-F]{6}$", couleur):
            raise ZoneRepositoryError(f"Couleur invalide (attendu #rrggbb) : {couleur!r}")
        if motif not in ("__unset__", None) and motif not in MOTIFS_VALIDES:
            raise ZoneRepositoryError(f"Motif invalide : {motif!r} (valides : {MOTIFS_VALIDES})")

        gf = self._load_geo(scenario)
        zone_obj = self._find(gf.zones, slug)
        if zone_obj is None:
            raise ZoneRepositoryError(f"Zone introuvable dans {scenario} : {slug!r}")
        if int(zone_obj.get("niveau", 1)) != 1:
            raise ZoneRepositoryError(
                f"'{slug}' est une sous-zone (niveau {zone_obj.get('niveau')}) — "
                "couleur/motif/hachures ne se définissent que sur une zone niveau 1, "
                "les sous-zones héritent automatiquement de leur racine."
            )

        if couleur != "__unset__":
            if couleur is None:
                zone_obj.pop("couleur", None)
            else:
                zone_obj["couleur"] = couleur
        if motif != "__unset__":
            if motif is None:
                zone_obj.pop("motif", None)
            else:
                zone_obj["motif"] = motif
        if hachures is not None:
            zone_obj["hachures"] = bool(hachures)

        self._save_geo(gf)
        return {"ok": True, "slug": slug, "couleur": zone_obj.get("couleur"),
                "motif": zone_obj.get("motif"), "hachures": zone_obj.get("hachures", False)}

    # ── COUVERTURE PAYS — résolution pour le rendu carte (point 1) ─────────
    #
    # Fix structurel du bug "motif du pays visible sous l'overlay" (point 1
    # de la refonte) : avant, le frontend recevait séparément la couleur
    # pays-entier (zones_pays.json) ET la liste d'overlays, et devait
    # lui-même décider comment les superposer -- d'où la fuite visuelle
    # quand l'ordre des couches/l'opacité n'étaient pas exactement right.
    # Cette méthode calcule, CÔTÉ SERVEUR, une réponse déjà désambiguïsée :
    # pour un pays donné, soit il est couvert par un overlay (et alors le
    # rendu pays-entier ne doit RIEN dessiner à cet endroit), soit il ne
    # l'est pas (rendu pays-entier normal). Le frontend n'a plus à trancher.

    def couverture_carte(self, scenario: str) -> dict:
        """
        Retourne {
          "pays_masques": {nom_pays: [zone_slug, ...]},   # pays ayant au
              moins un overlay -- le rendu "pays entier" doit les exclure
          "overlays": [...],                               # features brutes,
              chacune avec la couleur/motif déjà résolus (couleur_effective/
              motif_effectif)
        }

        Fix (12 sept 2026) : la couleur effective d'un overlay est résolue
        via zones_n1_colorees() -- la MÊME fonction qui calcule la couleur du
        calque "pays entier" (roue de teintes automatique si pas de couleur
        personnalisée) -- et non plus via le champ brut `couleur` de la
        fiche zone (qui vaut None pour toute zone non personnalisée). Avant
        ce fix, une zone sans couleur manuelle affichait sa vraie couleur
        calculée sur son territoire "pays entier", mais un bleu générique de
        secours sur ses portions overlay -- même zone, deux couleurs
        différentes selon la couche.
        """
        gf = self._load_geo(scenario)
        zones = gf.zones
        fc = self._load_overlays(scenario)
        features = fc.get("features", [])

        couleurs_n1 = {z["slug"]: z for z in self.zones_n1_colorees(scenario)}

        pays_masques: dict = {}
        overlays_resolus = []
        for f in features:
            props = f.get("properties", {})
            slug = props.get("zone_slug")
            pays = props.get("pays")
            if not slug or not pays:
                continue
            pays_masques.setdefault(pays, []).append(slug)

            racine = self.resolve_root_n1(zones, slug)
            racine_slug = racine.get("slug") if racine else None
            zone_coloree = couleurs_n1.get(racine_slug)
            couleur = zone_coloree["color"] if zone_coloree else None
            motif = zone_coloree["motif"] if zone_coloree else None

            overlays_resolus.append({
                **f,
                "properties": {**props, "couleur_effective": couleur, "motif_effectif": motif},
            })

        return {"pays_masques": pays_masques, "overlays": overlays_resolus}

    # ── LECTURE : arbre, recherche, coloriage carte ─────────────────────
    #
    # Ces méthodes ne modifient jamais rien -- reprises dans le repository
    # pour que routes_carte.py (Blueprint HTTP) reste une couche fine,
    # sans logique de lecture dupliquée entre app.py et ce module.

    def load_all_zones(self, scenario: str) -> list:
        """Charge TOUTES les zones (tous niveaux) de la fiche
        geographie/{scenario}.md. Liste vide si la fiche n'existe pas
        (contrairement aux autres méthodes, ne lève pas -- utilisé par des
        routes de recherche/navigation qui doivent rester tolérantes)."""
        try:
            gf = self._load_geo(scenario)
        except ZoneRepositoryError:
            return []
        return gf.zones

    @staticmethod
    def chemin_vers_racine(zone: dict, by_slug: dict) -> list:
        """Chemin complet de la racine N1 jusqu'à `zone` (incluse), sous
        forme de liste [{slug, nom, niveau}, ...]. Anti-cycle : s'arrête si
        un slug est revisité."""
        chemin = []
        courant = zone
        vus = set()
        while courant is not None:
            slug = courant.get("slug")
            if slug in vus:
                break
            vus.add(slug)
            chemin.append({"slug": slug, "nom": courant.get("nom"), "niveau": courant.get("niveau")})
            parent_slug = courant.get("parent")
            courant = by_slug.get(parent_slug) if parent_slug else None
        return list(reversed(chemin))

    @staticmethod
    def build_zone_tree(zones: list, root_slug: str) -> Optional[dict]:
        """Arbre imbriqué {slug, nom, niveau, type, statut, origine_reelle,
        couleur, motif, enfants:[...]} à partir de la liste plate. `couleur`/
        `motif` restent bruts ici (pas résolus par héritage) -- c'est
        volontairement le rôle de couleur_motif_effectifs()/couverture_carte(),
        cette méthode-ci sert la visualisation de l'arbre lui-même (savoir SI
        une zone a une valeur propre, pas seulement sa valeur effective)."""
        by_parent: dict = {}
        for z in zones:
            p = z.get("parent")
            if p:
                by_parent.setdefault(p, []).append(z)
        by_slug = {z.get("slug"): z for z in zones}

        def _node(slug):
            z = by_slug.get(slug)
            if not z:
                return None
            enfants = [_node(c.get("slug")) for c in by_parent.get(slug, [])]
            return {
                "slug": z.get("slug"), "nom": z.get("nom"), "niveau": z.get("niveau"),
                "type": z.get("type"), "statut": z.get("statut"),
                "origine_reelle": z.get("origine_reelle") or [],
                "couleur": z.get("couleur"), "motif": z.get("motif"),
                "hachures": bool(z.get("hachures")),
                "enfants": [e for e in enfants if e is not None],
            }

        return _node(root_slug)

    def rechercher_zone(self, scenario: str, q: str) -> list:
        """Recherche une zone par nom ou slug, tous niveaux, insensible à la
        casse/accents. Chaque résultat porte son chemin racine N1 -> zone."""
        zones = self.load_all_zones(scenario)
        by_slug = {z.get("slug"): z for z in zones if z.get("slug")}
        q_fold = _fold(q)
        resultats = []
        for z in zones:
            slug, nom = str(z.get("slug", "")), str(z.get("nom", ""))
            if q_fold in _fold(nom) or q_fold in _fold(slug):
                resultats.append({"slug": slug, "nom": nom, "niveau": z.get("niveau"),
                                  "chemin": self.chemin_vers_racine(z, by_slug)})
        resultats.sort(key=lambda r: (r["niveau"] if isinstance(r["niveau"], int) else 1, r["nom"] or ""))
        return resultats

    def arbre_zone(self, scenario: str, slug: str) -> Optional[dict]:
        return self.build_zone_tree(self.load_all_zones(scenario), slug)

    def zones_toutes(self, scenario: str) -> list:
        """Liste plate {slug, nom, niveau}, tous niveaux, triée par nom --
        pour peupler une liste déroulante fiable (dessin d'overlay, etc.)."""
        zones = self.load_all_zones(scenario)
        result = [{"slug": z.get("slug"), "nom": z.get("nom", z.get("slug")), "niveau": z.get("niveau", 1)}
                  for z in zones if z.get("slug")]
        result.sort(key=lambda z: z["nom"] or "")
        return result

    def _paires_overlay(self, scenario: str) -> set:
        """Ensemble de couples (zone_slug, pays_normalise) pour lesquels un
        tracé overlay existe dans geo_overlays/{scenario}.geojson.

        Sert à distinguer une entrée origine_reelle "pays entier" (vrai
        rattachement complet, via assign_pays) d'une entrée créée
        uniquement pour porter un tracé overlay/portion (via
        overlay_creer -- voir cette méthode : elle ajoute une entrée
        origine_reelle structurellement identique à un pays entier quand
        le pays n'y était pas déjà, sans marqueur distinctif)."""
        fc = self._load_overlays(scenario)
        paires = set()
        for f in fc.get("features", []):
            props = f.get("properties", {})
            slug, pays = props.get("zone_slug"), props.get("pays")
            if slug and pays:
                paires.add((slug, _normalise_pays(pays)))
        return paires

    def origine_reelle_index(self, scenario: str) -> dict:
        """Index pays_normalise -> slug_zone à jour, calculé directement
        depuis origine_reelle (pas depuis le fallback zones_pays.json).
        Priorité aux zones N1 si un pays apparaît dans plusieurs niveaux.

        Fix (13 sept 2026, bug France/Zone Interdite de Heysham) : une
        entrée origine_reelle backée UNIQUEMENT par un tracé overlay
        (portion) est exclue de cet index -- elle ne doit jamais faire
        gagner "pays entier" à sa zone sur la couche de base de la carte
        (affectations()/app.js `CarteState.affectations[pays]`), sous
        peine de colorier tout le pays alors que seule une portion a été
        dessinée. Les vrais rattachements pays-entier (assign_pays, pas
        d'overlay associé) restent, eux, comptabilisés normalement."""
        zones = self.load_all_zones(scenario)
        paires_overlay = self._paires_overlay(scenario)
        index, index_non_n1 = {}, {}
        for z in zones:
            niveau = z.get("niveau", 1)
            slug = z.get("slug")
            for o in (z.get("origine_reelle") or []):
                if not isinstance(o, dict):
                    continue
                n = _normalise_pays(o.get("entite", ""))
                if not n:
                    continue
                if (slug, n) in paires_overlay:
                    continue
                (index if niveau == 1 else index_non_n1).setdefault(n, slug)
        for n, slug in index_non_n1.items():
            index.setdefault(n, slug)
        return index

    def zones_n1_colorees(self, scenario: str) -> list:
        """
        Zones niveau 1 uniquement, avec couleur/motif résolus (custom sinon
        roue de teintes). Simplification structurelle de cette refonte :
        avant (_scan_zones_carte), les zones niveau 2/3 référencées par un
        overlay entraient DANS la même roue de teintes que les N1, avec deux
        conséquences gênantes -- (a) leur couleur se décalait à chaque
        ajout/suppression d'overlay ailleurs dans le scénario, (b) une
        sous-zone pouvait recevoir une couleur propre alors que le point 4
        de la refonte dit qu'elle n'en a plus. Depuis couverture_carte()
        (qui résout la couleur de CHAQUE overlay par héritage N1via
        couleur_motif_effectifs), la roue de teintes n'a plus besoin de
        porter que les zones N1 -- plus stable, et cohérent avec l'héritage.
        """
        zones = self.load_all_zones(scenario)
        n1 = [z for z in zones if int(z.get("niveau", 1)) == 1 and z.get("slug")]
        n1.sort(key=lambda z: z["slug"])
        n = len(n1)
        result = []
        for i, z in enumerate(n1):
            hue = (i / n) if n else 0
            lightness = 0.50 if i % 2 == 0 else 0.42
            couleur = z.get("couleur") or _hsl_to_hex(hue, 0.60, lightness)
            motif = z.get("motif")
            # pattern : hachures génériques, DÉSACTIVÉES PAR DÉFAUT (12 sept
            # 2026, sur demande de David) -- avant, activées automatiquement
            # dès que le scénario dépassait PATTERN_THRESHOLD zones N1, sans
            # option pour les désactiver. Depuis : off par défaut sur toute
            # zone, activable explicitement zone par zone via
            # personnaliser(hachures=True) -- champ `hachures` en frontmatter.
            pattern = (i % N_PATTERNS) if (z.get("hachures") and not motif) else None
            result.append({
                "slug": z.get("slug"), "nom": str(z.get("nom", z.get("slug"))).strip(),
                "description": str(z.get("description", "")).strip(),
                "niveau": 1, "color": couleur, "motif": motif, "pattern": pattern,
            })
        return result

    def affectations(self, scenario: str) -> dict:
        """
        Réponse complète pour rendre la carte : pays_liste (référence),
        affectation de chaque pays (index frais > fallback zones_pays.json),
        zones N1 coloriées, et la couverture overlay déjà résolue (point 1
        -- le frontend n'a plus à décider comment superposer, voir
        couverture_carte()).
        """
        zp = self._load_zones_pays()
        pays_liste = zp.get("pays_liste", [])
        fresh_index = self.origine_reelle_index(scenario)
        scenario_fallback = zp.get(scenario, {})

        affectations = {}
        for pays in pays_liste:
            n = _normalise_pays(pays)
            affectations[pays] = fresh_index.get(n) or scenario_fallback.get(pays)

        return {
            "scenario": scenario,
            "pays_liste": pays_liste,
            "affectations": affectations,
            "zones_n1": self.zones_n1_colorees(scenario),
            "couverture": self.couverture_carte(scenario),
        }

    def overlays_get(self, scenario: str) -> dict:
        """FeatureCollection brute des overlays d'un scénario (lecture
        seule) -- alias public de _load_overlays."""
        return self._load_overlays(scenario)

    # ── DIAGNOSTIC / RÉPARATION : pays dupliqué entre plusieurs zones ──────
    #
    # Cas trouvé le 12 septembre (Turquie) : la route (ancienne, hors refonte)
    # de création de zone top-down ajoute le pays à la nouvelle zone et
    # resynchronise zones_pays.json, mais NE RETIRE PAS le pays de
    # l'origine_reelle de son ancienne zone -- contrairement à assign_pays()
    # qui fait ce ménage. Résultat : le pays apparaît dans DEUX zones N1 à la
    # fois, et origine_reelle_index()/affectations() (qui priorisent la
    # première zone trouvée dans l'ordre du fichier) peuvent renvoyer
    # l'ancienne zone au lieu de la nouvelle, malgré un zones_pays.json
    # correct. Ce n'est PAS toujours un bug (le partage France entre Zone
    # Euro Sud et Zone Interdite de Heysham est un choix narratif assumé) --
    # cette méthode ne s'utilise donc jamais automatiquement, uniquement
    # sur demande explicite pour un cas identifié comme réellement erroné.

    def zones_portant_un_pays(self, scenario: str, pays: str) -> list:
        """Liste toutes les zones (tous niveaux) dont l'origine_reelle
        référence `pays`, avec le détail par zone -- pour diagnostiquer un
        doublon (usage historique) ET pour l'affichage GUI d'un pays coupé
        en plusieurs zones (13 sept 2026, demande de David : le panneau
        d'un pays doit montrer toutes ses zones d'appartenance quand il en
        a plusieurs).

        `type` vaut "pays_entier" (vrai rattachement complet) ou "overlay"
        (portion, backée par un tracé dans geo_overlays/{scenario}.geojson)
        -- même distinction que celle introduite dans origine_reelle_index()."""
        n = _normalise_pays(pays)
        zones = self.load_all_zones(scenario)
        paires_overlay = self._paires_overlay(scenario)
        resultats = []
        for z in zones:
            slug = z.get("slug")
            for o in (z.get("origine_reelle") or []):
                if isinstance(o, dict) and _normalise_pays(o.get("entite", "")) == n:
                    resultats.append({
                        "slug": slug, "nom": z.get("nom"), "niveau": z.get("niveau"),
                        "type": "overlay" if (slug, n) in paires_overlay else "pays_entier",
                        "portion": o.get("portion"),
                    })
                    break  # une seule entrée par couple (zone, pays) attendue
        return resultats

    def retirer_pays_des_autres_zones(self, scenario: str, pays: str,
                                       slug_a_conserver: str, dry_run: bool = True) -> dict:
        """
        Retire `pays` de l'origine_reelle de TOUTE zone du scénario SAUF
        `slug_a_conserver`, et s'assure que zones_pays.json pointe bien
        `pays` vers `slug_a_conserver`. À utiliser uniquement quand un
        doublon a été identifié comme une erreur (pas un partage narratif
        volontaire).
        """
        gf = self._load_geo(scenario)
        zones = gf.zones
        if not self._find(zones, slug_a_conserver):
            raise ZoneRepositoryError(f"Zone '{slug_a_conserver}' introuvable dans {scenario}")

        n = _normalise_pays(pays)
        zones_touchees = []
        for z in zones:
            if z.get("slug") == slug_a_conserver:
                continue
            origine = z.get("origine_reelle")
            if not isinstance(origine, list):
                continue
            reste = [o for o in origine
                     if not (isinstance(o, dict) and _normalise_pays(o.get("entite", "")) == n)]
            if len(reste) != len(origine):
                zones_touchees.append({"slug": z.get("slug"), "nom": z.get("nom")})
                if not dry_run:
                    z["origine_reelle"] = reste

        zp = self._load_zones_pays()
        sc = zp.get(scenario, {})
        zones_pays_json_avant = sc.get(pays)
        zones_pays_json_a_corriger = zones_pays_json_avant != slug_a_conserver

        if dry_run:
            return {
                "pays": pays, "slug_conserve": slug_a_conserver,
                "zones_a_nettoyer": zones_touchees,
                "zones_pays_json_avant": zones_pays_json_avant,
                "zones_pays_json_sera_corrige": zones_pays_json_a_corriger,
                "rien_a_faire": not zones_touchees and not zones_pays_json_a_corriger,
            }

        if zones_touchees:
            self._save_geo(gf)
        if zones_pays_json_a_corriger:
            sc[pays] = slug_a_conserver
            zp[scenario] = sc
            self._save_zones_pays(zp)

        return {
            "ok": True, "pays": pays, "slug_conserve": slug_a_conserver,
            "zones_nettoyees": [z["slug"] for z in zones_touchees],
            "zones_pays_json_corrige": zones_pays_json_a_corriger,
        }

    def retirer_doublons_pays_entier(self, scenario: str, pays: str,
                                      slug_a_conserver: str, dry_run: bool = True) -> dict:
        """
        Nettoyage ciblé du bug "doublon pays entier" (13 sept 2026, cas
        Belgique/espace_nordique_arctique+zone_euro_sud, même famille que
        le Doublon Turquie du 12 sept). Contrairement à
        retirer_pays_des_autres_zones() -- trop large pour ce cas, testée
        et rejetée (elle retire AUSSI les overlays légitimes du pays dans
        d'autres zones, ce qui laisse en plus un masque orphelin dans
        geo_overlays/{scenario}.geojson) -- cette méthode ne retire QUE les
        entrées classées "pays_entier" (aucun tracé overlay ne les
        justifie) dans les zones autres que `slug_a_conserver`. Les entrées
        "overlay" (portion, tracé réel dans geo_overlays) sont TOUJOURS
        préservées, quelle que soit la zone.

        Filtre de lignée (14 sept 2026, bug trouvé sur Corée du Sud/
        policy_reform -- inde_corree_noeud_pacte, sous-zone niveau 2 de
        espace_eurasiatique, retirée à tort en même temps que
        zone_pacifique_industrielle, racine N1 non apparentée) : une zone
        dont la racine N1 est la même que celle de `slug_a_conserver` n'est
        jamais touchée, même si son slug diffère -- c'est un rattachement
        narratif hérité de la même branche, pas un doublon concurrent.
        Même principe que le filtre parent/enfant de
        diagnostiquer_doublons_pays_entier.py (v1 -> v2), jusqu'ici absent
        de cette méthode d'écriture.

        Garde-fou zones_pays.json (14 sept 2026, bug #5 du handoff du
        13 sept) : la synchronisation de zones_pays.json (index pays ->
        zone) n'a de sens que pour un vrai pays. Auparavant, la méthode
        écrivait `sc[pays] = slug_a_conserver` sans condition, ce qui
        créait une clé parasite dans zones_pays.json pour toute entité
        hors `pays_liste` (villes, régions fictives, entités composées
        type "Danemark / Groenland", "Balkans occidentaux") --
        contournement mis en place via retirer_entree_parasite_zones_
        pays.py, non corrigé à la racine jusqu'ici. Même principe que
        creer_zone_n1() : résolution de `pays` contre `zones_pays.json
        ["pays_liste"]` (normalisation via _normalise_pays), la
        synchronisation zones_pays.json n'a lieu que sur match exact.
        """
        gf = self._load_geo(scenario)
        zones = gf.zones
        if not self._find(zones, slug_a_conserver):
            raise ZoneRepositoryError(f"Zone '{slug_a_conserver}' introuvable dans {scenario}")

        by_slug = {z.get("slug"): z for z in zones}
        racine_conservee = self._zone_niveau1_ancestor(by_slug, slug_a_conserver)

        n = _normalise_pays(pays)
        paires_overlay = self._paires_overlay(scenario)
        zones_touchees = []
        for z in zones:
            slug = z.get("slug")
            if slug == slug_a_conserver:
                continue
            # Sous-zone (ou racine) de la même branche N1 que slug_a_conserver --
            # jamais un doublon, toujours préservée.
            if racine_conservee and self._zone_niveau1_ancestor(by_slug, slug) == racine_conservee:
                continue
            origine = z.get("origine_reelle")
            if not isinstance(origine, list):
                continue
            # Ne retire que les entrées "pays_entier" (pas d'overlay associé) --
            # une entrée backée par un tracé overlay reste intouchée, même
            # dans une zone différente de slug_a_conserver.
            reste = [o for o in origine
                     if not (isinstance(o, dict)
                             and _normalise_pays(o.get("entite", "")) == n
                             and (slug, n) not in paires_overlay)]
            if len(reste) != len(origine):
                zones_touchees.append({"slug": slug, "nom": z.get("nom")})
                if not dry_run:
                    z["origine_reelle"] = reste

        zp = self._load_zones_pays()
        sc = zp.get(scenario, {})
        index_norm_vers_canonique = {_normalise_pays(p): p for p in zp.get("pays_liste", [])}
        pays_canonique = index_norm_vers_canonique.get(n)
        zones_pays_json_avant = sc.get(pays_canonique) if pays_canonique else None
        zones_pays_json_a_corriger = bool(pays_canonique) and zones_pays_json_avant != slug_a_conserver

        if dry_run:
            return {
                "pays": pays, "slug_conserve": slug_a_conserver,
                "zones_a_nettoyer": zones_touchees,
                "zones_pays_json_avant": zones_pays_json_avant,
                "zones_pays_json_sera_corrige": zones_pays_json_a_corriger,
                "rien_a_faire": not zones_touchees and not zones_pays_json_a_corriger,
            }

        if zones_touchees:
            self._save_geo(gf)
        if zones_pays_json_a_corriger:
            sc[pays_canonique] = slug_a_conserver
            zp[scenario] = sc
            self._save_zones_pays(zp)

        return {
            "ok": True, "pays": pays, "slug_conserve": slug_a_conserver,
            "zones_nettoyees": [z["slug"] for z in zones_touchees],
            "zones_pays_json_corrige": zones_pays_json_a_corriger,
        }

    # ── DÉPLACER (reparent) ─────────────────────────────────────────────
    #
    # Logique métier identique à l'existant (validé depuis le 13 juillet,
    # fix zones_pays.json du 8 septembre inclus). Ajout de cette refonte :
    # nettoyage couleur/motif quand une zone N1 personnalisée est rétrogradée
    # en sous-zone -- avant, le champ restait en mémoire morte dans le YAML,
    # invisible mais jamais nettoyé (couleur_motif_effectifs() l'ignore déjà
    # via resolve_root_n1, mais autant ne pas laisser de champ mort dans les
    # données : cohérent avec le point 4, une sous-zone n'a plus de couleur
    # propre, y compris dans le fichier lui-même).

    @staticmethod
    def _zone_niveau1_ancestor(by_slug: dict, slug: str) -> Optional[str]:
        seen = set()
        current = by_slug.get(slug)
        while current and current.get("niveau", 1) != 1:
            if current.get("slug") in seen:
                return None
            seen.add(current.get("slug"))
            current = by_slug.get(current.get("parent"))
        return current.get("slug") if current else None

    @staticmethod
    def _zone_descendants(zones: list, root_slug: str) -> list:
        by_parent: dict = {}
        for z in zones:
            p = z.get("parent")
            if p:
                by_parent.setdefault(p, []).append(z)
        result = []

        def _walk(slug):
            result.append(slug)
            for child in by_parent.get(slug, []):
                _walk(child.get("slug"))

        _walk(root_slug)
        return result

    @staticmethod
    def _zone_header_regex(nom):
        return re.compile(r"^(#{1,6}) " + re.escape(nom) + r"( — sous \[\[.+?\]\])?$", re.MULTILINE)

    def _reparent_body_text(self, body, slug, nouveau_parent_slug, sous_arbre_by_slug):
        changed = False
        for s, z in sous_arbre_by_slug.items():
            nom = z.get("nom")
            niveau = z.get("niveau")
            if not nom or not niveau:
                continue
            new_hashes = "#" * (niveau + 2)

            def _repl(m, s=s, new_hashes=new_hashes):
                nonlocal changed
                suffix = m.group(2) or ""
                if s == slug:
                    suffix = f" — sous [[{nouveau_parent_slug}]]" if nouveau_parent_slug else ""
                changed = True
                return f"{new_hashes} {nom}{suffix}"

            body = self._zone_header_regex(nom).sub(_repl, body)
        return body, changed

    def reparent(self, scenario: str, slug: str,
                 nouveau_parent_slug: Optional[str], dry_run: bool = True) -> dict:
        """
        Déplace une zone (et son sous-arbre) vers un nouveau parent.
        nouveau_parent_slug=None : promotion en zone niveau 1 autonome.
        Lève ZoneRepositoryError sur : zone/parent introuvable, cycle,
        parent inchangé.
        """
        gf = self._load_geo(scenario)
        zones = gf.zones
        by_slug = {z.get("slug"): z for z in zones}

        target = by_slug.get(slug)
        if not target:
            raise ZoneRepositoryError(f"Zone '{slug}' introuvable")

        devient_racine = not nouveau_parent_slug
        nouveau_parent = None
        if not devient_racine:
            if slug == nouveau_parent_slug:
                raise ZoneRepositoryError("Une zone ne peut pas devenir son propre parent")
            nouveau_parent = by_slug.get(nouveau_parent_slug)
            if not nouveau_parent:
                raise ZoneRepositoryError(f"Nouveau parent '{nouveau_parent_slug}' introuvable")

        ancien_parent_slug = target.get("parent")
        if (devient_racine and ancien_parent_slug is None) or \
           (not devient_racine and ancien_parent_slug == nouveau_parent_slug):
            raise ZoneRepositoryError("Cette zone est déjà rattachée à ce parent")

        sous_arbre_slugs = self._zone_descendants(zones, slug)
        if not devient_racine and nouveau_parent_slug in sous_arbre_slugs:
            raise ZoneRepositoryError(
                f"Cycle détecté : '{nouveau_parent_slug}' est un descendant de '{slug}'"
            )

        ancien_niveau = target.get("niveau") or 1
        nouveau_niveau_racine = 1 if devient_racine else (nouveau_parent.get("niveau") or 1) + 1
        delta = nouveau_niveau_racine - ancien_niveau
        devient_sous_zone = ancien_niveau == 1 and nouveau_niveau_racine != 1

        if dry_run:
            pays_impactes = []
            if devient_sous_zone:
                zp = self._load_zones_pays()
                sc = zp.get(scenario, {})
                nouvel_ancetre_preview = self._zone_niveau1_ancestor(by_slug, nouveau_parent_slug)
                pays_impactes = [
                    {"pays": p, "nouvelle_zone": nouvel_ancetre_preview}
                    for p, z in sc.items() if z == slug
                ]
            couleur_motif_perdus = bool(devient_sous_zone and (target.get("couleur") or target.get("motif")))
            return {
                "zone": {"slug": slug, "nom": target.get("nom"), "niveau": ancien_niveau,
                         "ancien_parent": ancien_parent_slug},
                "nouveau_parent": {"slug": nouveau_parent_slug, "nom": nouveau_parent.get("nom"),
                                    "niveau": nouveau_parent.get("niveau")} if not devient_racine else None,
                "devient_racine": devient_racine,
                "nouveau_niveau_zone": nouveau_niveau_racine,
                "changement_de_profondeur": delta != 0,
                "descendants_impactes": [
                    {"slug": s, "nom": by_slug[s].get("nom"),
                     "ancien_niveau": by_slug[s].get("niveau"),
                     "nouveau_niveau": (by_slug[s].get("niveau") or 1) + delta}
                    for s in sous_arbre_slugs if s != slug
                ],
                "pays_zones_pays_json_impactes": pays_impactes,
                "couleur_motif_perdus": couleur_motif_perdus,
            }

        ancien_nom = target.get("nom")
        for s in sous_arbre_slugs:
            z = by_slug[s]
            z["niveau"] = (z.get("niveau") or 1) + delta
        target["parent"] = None if devient_racine else nouveau_parent_slug

        # Point 4 : une zone rétrogradée de N1 vers sous-zone perd sa
        # couleur/motif propres -- elle héritera désormais de sa nouvelle
        # racine N1 comme n'importe quelle autre sous-zone.
        if devient_sous_zone:
            target.pop("couleur", None)
            target.pop("motif", None)

        sous_arbre_by_slug = {s: by_slug[s] for s in sous_arbre_slugs}
        new_body, body_maj = self._reparent_body_text(
            gf.body, slug, nouveau_parent_slug if not devient_racine else None, sous_arbre_by_slug
        )
        gf.body = new_body
        self._save_geo(gf)

        pays_zones_pays_json = []
        if devient_sous_zone:
            nouvel_ancetre = self._zone_niveau1_ancestor(by_slug, slug)
            zp = self._load_zones_pays()
            sc = zp.get(scenario, {})
            pays_zones_pays_json = [p for p, z in sc.items() if z == slug]
            if pays_zones_pays_json:
                for p in pays_zones_pays_json:
                    sc[p] = nouvel_ancetre
                zp[scenario] = sc
                self._save_zones_pays(zp)

        return {
            "ok": True, "ancien_nom": ancien_nom, "nouveau_niveau": nouveau_niveau_racine,
            "devient_racine": devient_racine,
            "changement_de_profondeur": delta != 0,
            "descendants_maj": len(sous_arbre_slugs) - 1, "body_maj": body_maj,
            "pays_zones_pays_json_maj": pays_zones_pays_json,
        }

    # ── SCINDER (split) ─────────────────────────────────────────────────
    #
    # Logique métier identique à l'existant. Ajout de cette refonte : les
    # overlays dessinés référençant zone_slug=slug_source ET un des pays
    # extraits migrent automatiquement vers la zone cible -- gap potentiel
    # du même type que le bug de rename du 10 septembre, jamais observé en
    # pratique mais corrigé par construction plutôt qu'attendu.

    def split(self, scenario: str, slug_source: str, pays_a_extraire: list,
              cible: dict, dry_run: bool = True) -> dict:
        gf = self._load_geo(scenario)
        zones = gf.zones
        source = self._find(zones, slug_source)
        if not source:
            raise ZoneRepositoryError(f"Zone '{slug_source}' introuvable dans {scenario}")

        pays_normalises = {_normalise_pays(p) for p in pays_a_extraire}
        origine = source.get("origine_reelle") or []
        a_extraire = [o for o in origine if isinstance(o, dict)
                      and _entite_references_pays(o.get("entite") or "", pays_normalises)]
        restantes = [o for o in origine if o not in a_extraire]

        if not a_extraire:
            raise ZoneRepositoryError(
                f"Aucune entrée de origine_reelle de '{slug_source}' ne référence "
                f"{', '.join(pays_a_extraire)}"
            )
        if not restantes:
            raise ZoneRepositoryError(
                f"Le split viderait complètement origine_reelle de '{slug_source}' -- "
                "au moins une entrée doit rester"
            )

        enfants_a_suivre, enfants_restants = [], []
        for e in zones:
            if e.get("parent") != slug_source:
                continue
            e_origine = e.get("origine_reelle") or []
            lie = any(isinstance(o, dict) and _entite_references_pays(o.get("entite") or "", pays_normalises)
                      for o in e_origine)
            (enfants_a_suivre if lie else enfants_restants).append(e)

        mode = cible.get("mode")
        if mode == "nouvelle_zone_n1":
            cible_slug = (cible.get("slug") or "").strip()
            cible_nom = (cible.get("nom") or "").strip()
            cible_type = (cible.get("type") or "").strip()
            cible_statut = (cible.get("statut") or "").strip()
            cible_description = (cible.get("description") or "").strip()
            if not cible_slug or not cible_nom or not cible_type or not cible_statut:
                raise ZoneRepositoryError("cible.slug, nom, type, statut requis pour une nouvelle zone niveau 1")
            if not re.match(r"^[a-z0-9_]+$", cible_slug):
                raise ZoneRepositoryError("cible.slug : lettres minuscules, chiffres, underscores uniquement")
            if cible_type not in ZONE_TYPES:
                raise ZoneRepositoryError(f"cible.type invalide, doit être parmi : {', '.join(ZONE_TYPES)}")
            if cible_statut not in ZONE_STATUTS:
                raise ZoneRepositoryError(f"cible.statut invalide, doit être parmi : {', '.join(ZONE_STATUTS)}")
            if self._find(zones, cible_slug):
                raise ZoneRepositoryError(f"Le slug '{cible_slug}' existe déjà dans ce scénario")
            cible_info = {"mode": mode, "slug": cible_slug, "nom": cible_nom, "type": cible_type,
                          "statut": cible_statut, "description": cible_description}
            cible_zone = None
        elif mode == "zone_existante":
            slug_existant = (cible.get("slug_existant") or "").strip()
            cible_zone = self._find(zones, slug_existant)
            if not cible_zone:
                raise ZoneRepositoryError(f"Zone cible '{slug_existant}' introuvable dans {scenario}")
            if cible_zone.get("niveau", 1) != 1:
                raise ZoneRepositoryError(
                    f"'{slug_existant}' n'est pas une zone niveau 1 -- le split ne cible que des zones N1"
                )
            if slug_existant == slug_source:
                raise ZoneRepositoryError("La zone cible ne peut pas être la zone source")
            cible_info = {"mode": mode, "slug": slug_existant, "nom": cible_zone.get("nom")}
        else:
            raise ZoneRepositoryError("cible.mode doit être 'nouvelle_zone_n1' ou 'zone_existante'")

        if dry_run:
            zp = self._load_zones_pays()
            sc = zp.get(scenario, {})
            pays_zones_pays_json = [
                p for p, s in sc.items() if s == slug_source and _normalise_pays(p) in pays_normalises
            ]
            return {
                "source": {"slug": slug_source, "nom": source.get("nom"),
                           "origine_reelle_avant": origine, "origine_reelle_apres": restantes},
                "entites_extraites": a_extraire,
                "enfants_qui_suivront": [{"slug": e.get("slug"), "nom": e.get("nom")} for e in enfants_a_suivre],
                "enfants_qui_restent": [{"slug": e.get("slug"), "nom": e.get("nom")} for e in enfants_restants],
                "cible": cible_info,
                "pays_zones_pays_json": pays_zones_pays_json,
            }

        source["origine_reelle"] = restantes
        if mode == "nouvelle_zone_n1":
            zones.append({
                "slug": cible_info["slug"], "nom": cible_info["nom"], "niveau": 1,
                "type": cible_info["type"], "parent": None,
                "origine_reelle": a_extraire, "description": cible_info["description"],
                "statut": cible_info["statut"], "tensions_internes": "",
                "periode_transition": None, "evenement_transition": None,
                "lieux_emblematiques": [], "relations": {"allies": [], "rivaux": []},
                "sources_attestees": [],
            })
        else:
            existantes = cible_zone.get("origine_reelle") or []
            cible_zone["origine_reelle"] = existantes + [o for o in a_extraire if o not in existantes]

        for e in enfants_a_suivre:
            e["parent"] = cible_info["slug"]

        new_body = gf.body
        if mode == "nouvelle_zone_n1":
            new_body = new_body.rstrip("\n") + f"\n\n### {cible_info['nom']}\n{cible_info['description']}\n"
        gf.body = new_body
        self._save_geo(gf)

        zp = self._load_zones_pays()
        sc = zp.get(scenario, {})
        pays_touches = [p for p, s in sc.items() if s == slug_source and _normalise_pays(p) in pays_normalises]
        for p in pays_touches:
            sc[p] = cible_info["slug"]
        zp[scenario] = sc
        if pays_touches:
            self._save_zones_pays(zp)

        # Overlays : toute portion déjà dessinée sur slug_source pour un des
        # pays extraits suit vers la cible (fix structurel de cette refonte).
        fc = self._load_overlays(scenario)
        overlays_touches = []
        for f in fc.get("features", []):
            props = f.get("properties", {})
            if props.get("zone_slug") == slug_source and _normalise_pays(props.get("pays", "")) in pays_normalises:
                props["zone_slug"] = cible_info["slug"]
                overlays_touches.append(props.get("id"))
        if overlays_touches:
            self._save_overlays(scenario, fc)

        return {
            "ok": True, "slug_source": slug_source,
            "origine_reelle_source_restante": len(restantes),
            "entites_deplacees": len(a_extraire), "cible": cible_info,
            "enfants_reparentes_automatiquement": [e.get("slug") for e in enfants_a_suivre],
            "enfants_restes_sous_source": [e.get("slug") for e in enfants_restants],
            "pays_zones_pays_json_maj": pays_touches,
            "overlays_maj": overlays_touches,
        }

    # ── AFFECTER un pays (clic sur la carte) ────────────────────────────

    def assign_pays(self, scenario: str, pays: str, action: str,
                     zone_slug: Optional[str] = None,
                     nouvelle_zone: Optional[dict] = None) -> dict:
        """
        action="absorber" : ajoute `pays` à l'origine_reelle de `zone_slug`
        (zone existante), en le retirant de toute autre zone au passage.
        action="creer" : crée une nouvelle zone N1 avec `pays` comme seule
        entrée origine_reelle. Écrit directement (pas de dry_run -- c'est
        l'usage existant, un simple clic + choix, pas une opération
        structurelle comme rename/reparent/split qui méritent un aperçu).
        """
        if action not in ("absorber", "creer"):
            raise ZoneRepositoryError("action doit être 'absorber' ou 'creer'")

        gf = self._load_geo(scenario)
        zones = gf.zones

        if action == "absorber":
            if not zone_slug:
                raise ZoneRepositoryError("zone_slug requis pour absorber")
            target = self._find(zones, zone_slug)
            if not target:
                raise ZoneRepositoryError(f"Zone '{zone_slug}' introuvable dans la fiche")
            for z in zones:
                if z is target:
                    continue
                origine = z.get("origine_reelle")
                if isinstance(origine, list):
                    z["origine_reelle"] = [o for o in origine
                                            if not (isinstance(o, dict) and o.get("entite") == pays)]
            origine = target.setdefault("origine_reelle", [])
            if not any(isinstance(o, dict) and o.get("entite") == pays for o in origine):
                origine.append({"entite": pays})
            final_slug = zone_slug
        else:
            nz = nouvelle_zone or {}
            slug = str(nz.get("slug", "")).strip()
            nom = str(nz.get("nom", "")).strip()
            description = str(nz.get("description", "")).strip()
            if not slug or not nom:
                raise ZoneRepositoryError("nouvelle_zone.slug et .nom requis")
            if self._find(zones, slug):
                raise ZoneRepositoryError(f"Le slug '{slug}' existe déjà")
            for z in zones:
                origine = z.get("origine_reelle")
                if isinstance(origine, list):
                    z["origine_reelle"] = [o for o in origine
                                            if not (isinstance(o, dict) and o.get("entite") == pays)]
            zones.append({"slug": slug, "nom": nom, "niveau": 1, "parent": None,
                          "description": description, "origine_reelle": [{"entite": pays}]})
            final_slug = slug

        self._save_geo(gf)

        zp = self._load_zones_pays()
        zp.setdefault(scenario, {})[pays] = final_slug
        self._save_zones_pays(zp)

        self._purger_zone_manquante(scenario, pays)

        return {"ok": True, "zone": final_slug}

    def _purger_zone_manquante(self, scenario: str, pays: str) -> None:
        """Retire (pays, scenario) de zones_manquantes.yaml s'il y est --
        même comportement que l'existant, best-effort (ne bloque jamais
        assign_pays si ce fichier est absent ou illisible)."""
        try:
            log_path = self.vault_root / "documentation" / "need_action" / "zones_manquantes.yaml"
            if not log_path.exists():
                return
            existing = yaml.safe_load(log_path.read_text(encoding="utf-8")) or {}
            entries = existing.get("zones_manquantes", [])
            entries = [e for e in entries if not (e.get("pays") == pays and e.get("scenario") == scenario)]
            existing["zones_manquantes"] = entries
            log_path.write_text(
                yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),
                encoding="utf-8"
            )
        except (OSError, yaml.YAMLError):
            pass

    def marquer_pays_ignore(self, scenario: str, pays: str) -> dict:
        """Marque un pays comme blanc intentionnel (statut
        'blanc_intentionnel') dans zones_manquantes.yaml -- crée l'entrée si
        elle n'existe pas encore."""
        log_path = self.vault_root / "documentation" / "need_action" / "zones_manquantes.yaml"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if log_path.exists():
            existing = yaml.safe_load(log_path.read_text(encoding="utf-8")) or {}
        entries = existing.get("zones_manquantes", [])
        trouve = False
        for e in entries:
            if e.get("pays") == pays and e.get("scenario") == scenario:
                e["statut"] = "blanc_intentionnel"
                trouve = True
        if not trouve:
            entries.append({"pays": pays, "scenario": scenario, "statut": "blanc_intentionnel"})
        existing["zones_manquantes"] = entries
        log_path.write_text(
            yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8"
        )
        return {"ok": True}

    # ── APERÇU D'IMPACT avant bascule d'un pays (lecture seule) ────────
    #
    # Scanne instances/event_instances/registre_evenements pour signaler tout
    # ce qui pourrait être affecté narrativement par le changement de zone
    # d'un pays -- n'écrit jamais sur les fiches, seulement un rapport
    # markdown de référence dans documentation/need_action/ (best-effort).

    def _scan_instances_events(self, scenario: str, pays_folded: str, zone_slugs_liees: set) -> tuple:
        instances_liees, mentions_texte = [], []
        for dossier in ("instances", "event_instances"):
            d = self.vault_root / dossier
            if not d.exists():
                continue
            for f in d.glob("*.md"):
                try:
                    raw = f.read_text(encoding="utf-8")
                except OSError:
                    continue
                parts = raw.split("---")
                fm = {}
                if len(parts) >= 2:
                    try:
                        fm = yaml.safe_load(parts[1]) or {}
                    except yaml.YAMLError:
                        fm = {}
                if fm.get("scenario") != scenario:
                    continue
                slug = fm.get("slug", f.stem)
                zone = (fm.get("localisation") or {}).get("zone")
                if zone in zone_slugs_liees:
                    instances_liees.append({"slug": slug, "zone": zone, "type": fm.get("type", dossier)})
                folded_raw = _fold(raw)
                if pays_folded in folded_raw:
                    idx = folded_raw.find(pays_folded)
                    extrait = raw[max(0, idx - 60):idx + 60].replace("\n", " ").strip()
                    mentions_texte.append({"slug": slug, "type": fm.get("type", dossier), "extrait": f"…{extrait}…"})
        return instances_liees[:100], mentions_texte[:50]

    def _scan_registre_evenements(self, scenario: str, pays_folded: str) -> list:
        reg_path = self.vault_root / "documentation" / "registre_evenements.md"
        if not reg_path.exists():
            reg_path = self.vault_root / "registre_evenements.md"
            if not reg_path.exists():
                return []
        hits, section = [], None
        try:
            for line in reg_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("## "):
                    section = stripped[3:].strip()
                    continue
                if section != scenario:
                    continue
                if stripped.startswith("|") and pays_folded in _fold(stripped):
                    hits.append(stripped)
        except OSError:
            pass
        return hits[:30]

    def impact_bascule_pays(self, scenario: str, pays: str, action: str,
                             zone_slug: Optional[str] = None,
                             nouvelle_zone: Optional[dict] = None) -> dict:
        """Rapport d'impact en lecture seule avant une bascule de zone pour
        un pays (utilisé par le clic simple sur un pays -- pas de dry_run
        séparé ici, cette méthode EST le dry-run ; l'application réelle se
        fait via assign_pays()). N'écrit rien sur les fiches -- seulement le
        rapport lui-même, en best-effort, dans documentation/need_action/."""
        zones = self.load_all_zones(scenario)
        pays_folded = _fold(pays)

        ancienne_zone = None
        for z in zones:
            for o in (z.get("origine_reelle") or []):
                if isinstance(o, dict) and o.get("entite") == pays:
                    ancienne_zone = z.get("slug")
                    break
            if ancienne_zone:
                break

        cible_slug = zone_slug if action == "absorber" else (nouvelle_zone or {}).get("slug", "")

        sous_zones_orphelines = []
        if ancienne_zone:
            descendants = set(self._zone_descendants(zones, ancienne_zone)) - {ancienne_zone}
            by_slug = {z.get("slug"): z for z in zones}
            for slug in descendants:
                z = by_slug.get(slug)
                if not z:
                    continue
                for o in (z.get("origine_reelle") or []):
                    entite = o.get("entite", "") if isinstance(o, dict) else ""
                    if pays_folded in _fold(entite):
                        sous_zones_orphelines.append({
                            "slug": slug, "nom": z.get("nom", slug),
                            "niveau": z.get("niveau"), "origine": entite,
                        })
                        break

        zone_slugs_liees = set()
        if ancienne_zone:
            zone_slugs_liees |= set(self._zone_descendants(zones, ancienne_zone))
        if cible_slug:
            zone_slugs_liees |= set(self._zone_descendants(zones, cible_slug))

        instances_liees, mentions_texte = self._scan_instances_events(scenario, pays_folded, zone_slugs_liees)
        registre_hits = self._scan_registre_evenements(scenario, pays_folded)

        rapport = {
            "pays": pays, "scenario": scenario,
            "ancienne_zone": ancienne_zone, "nouvelle_zone": cible_slug,
            "sous_zones_orphelines": sous_zones_orphelines,
            "instances_liees": instances_liees,
            "mentions_texte": mentions_texte,
            "registre_hits": registre_hits,
            "rien_detecte": not (sous_zones_orphelines or instances_liees or mentions_texte or registre_hits),
        }

        try:
            out_dir = self.vault_root / "documentation" / "need_action"
            out_dir.mkdir(parents=True, exist_ok=True)
            slug_pays = re.sub(r"[^a-z0-9]+", "_", _fold(pays)).strip("_")
            out_path = out_dir / f"impact_bascule_{slug_pays}_{scenario}.md"
            lignes = [
                f"# Rapport d'impact — {pays} ({scenario})", "",
                f"Bascule évaluée : `{ancienne_zone or '—'}` → `{cible_slug or '—'}`", "",
                f"## Sous-zones potentiellement orphelines ({len(sous_zones_orphelines)})",
            ]
            for sz in sous_zones_orphelines:
                lignes.append(f"- `{sz['slug']}` ({sz['nom']}, niveau {sz['niveau']}) — origine : {sz['origine']}")
            lignes.append(f"\n## Instances/événements liés structurellement ({len(instances_liees)})")
            for it in instances_liees:
                lignes.append(f"- `{it['slug']}` — zone : {it['zone']}")
            lignes.append(f"\n## Mentions textuelles de « {pays} » ({len(mentions_texte)})")
            for m in mentions_texte:
                lignes.append(f"- `{m['slug']}` — {m['extrait']}")
            lignes.append(f"\n## Registre des événements ({len(registre_hits)})")
            for r in registre_hits:
                lignes.append(f"- {r}")
            out_path.write_text("\n".join(lignes) + "\n", encoding="utf-8")
            rapport["rapport_path"] = str(out_path)
        except OSError:
            pass

        return rapport

    def desaffecter(self, scenario: str, pays: str) -> dict:
        """Retire complètement `pays` de la zone qui le réclame -- de son
        origine_reelle (toute zone, tout niveau), de tout overlay dessiné
        pour lui, ET de zones_pays.json.

        Fix (12 sept 2026) : avant, seul zones_pays.json était remis à zéro
        -- mais l'affichage carte priorise origine_reelle (la source la
        plus fiable) sur ce fallback, donc le pays réapparaissait affecté
        malgré la désaffectation, tant que son entrée narrative existait
        encore. Ce n'était pas un bug introduit par la refonte : le même
        write-only-zones_pays.json existait déjà avant, simplement masqué
        par l'ancien calcul d'affichage qui, lui, ne consultait pas
        origine_reelle en priorité."""
        gf = self._load_geo(scenario)
        zones_nettoyees = []
        for z in gf.zones:
            origine = z.get("origine_reelle")
            if not isinstance(origine, list):
                continue
            reste = [o for o in origine if not (isinstance(o, dict) and o.get("entite") == pays)]
            if len(reste) != len(origine):
                z["origine_reelle"] = reste
                zones_nettoyees.append(z.get("slug"))
        if zones_nettoyees:
            self._save_geo(gf)

        fc = self._load_overlays(scenario)
        avant = len(fc.get("features", []))
        fc["features"] = [f for f in fc.get("features", [])
                          if f.get("properties", {}).get("pays") != pays]
        overlays_retires = avant - len(fc["features"])
        if overlays_retires:
            self._save_overlays(scenario, fc)

        zp = self._load_zones_pays()
        sc = zp.get(scenario, {})
        if pays not in sc and not zones_nettoyees:
            raise ZoneRepositoryError(f"'{pays}' n'apparaît nulle part dans {scenario}")
        ancienne_zone = sc.get(pays)
        sc[pays] = None
        zp[scenario] = sc
        self._save_zones_pays(zp)

        return {
            "ok": True, "pays": pays, "ancienne_zone": ancienne_zone,
            "zones_origine_reelle_nettoyees": zones_nettoyees,
            "overlays_retires": overlays_retires,
        }

    # ── CRÉER une zone niveau 1 (formulaire manuel ou top-down) ─────────
    #
    # Fix structurel de cette refonte (cas Turquie, 12 sept 2026) : l'ancien
    # code créait la nouvelle zone et resynchronisait zones_pays.json, mais
    # ne retirait JAMAIS le pays de l'origine_reelle d'une zone où il se
    # trouvait déjà -- laissant le pays dupliqué dans deux zones N1 à la
    # fois. Cette version fait le même ménage que split()/assign_pays() :
    # tout pays de la nouvelle origine_reelle est retiré de toute AUTRE zone
    # qui le référençait avant.

    def creer_zone_n1(self, scenario: str, slug: str, nom: str, type_zone: str,
                       statut: str, origine_reelle: list, description: str = "",
                       tensions_internes: str = "", periode_transition=None,
                       lieux_emblematiques: Optional[list] = None,
                       relations: Optional[dict] = None,
                       sources_attestees: Optional[list] = None) -> dict:
        """Écrit toujours directement (pas de dry_run -- même doctrine que
        personnaliser/assign_pays : un geste de création, pas une
        restructuration prévisualisable comme rename/reparent/split)."""
        if not re.match(r"^[a-z0-9_]+$", slug):
            raise ZoneRepositoryError("slug : lettres minuscules, chiffres, underscores uniquement")
        if type_zone not in ZONE_TYPES:
            raise ZoneRepositoryError(f"type invalide, doit être parmi : {', '.join(ZONE_TYPES)}")
        if statut not in ZONE_STATUTS:
            raise ZoneRepositoryError(f"statut invalide, doit être parmi : {', '.join(ZONE_STATUTS)}")
        if not origine_reelle:
            raise ZoneRepositoryError("origine_reelle requis (au moins une entrée)")
        for o in origine_reelle:
            if not o.get("entite") or o.get("type_entite") not in TYPE_ENTITE_REELLE:
                raise ZoneRepositoryError(
                    f"origine_reelle invalide : {o!r} (type_entite doit être parmi "
                    f"{', '.join(TYPE_ENTITE_REELLE)})"
                )

        gf = self._load_geo(scenario)
        zones = gf.zones
        if self._find(zones, slug):
            raise ZoneRepositoryError(f"Le slug '{slug}' existe déjà dans ce scénario")

        # Ménage : retirer chaque entité de la nouvelle origine_reelle de
        # toute autre zone qui la référencerait déjà (le fix de fond).
        pays_normalises = {
            _normalise_pays(o["entite"]) for o in origine_reelle if o.get("type_entite") == "pays"
        }
        zones_nettoyees = []
        if pays_normalises:
            for z in zones:
                z_origine = z.get("origine_reelle")
                if not isinstance(z_origine, list):
                    continue
                reste = [
                    o for o in z_origine
                    if not (isinstance(o, dict)
                            and _entite_references_pays(o.get("entite") or "", pays_normalises))
                ]
                if len(reste) != len(z_origine):
                    zones_nettoyees.append(z.get("slug"))
                    z["origine_reelle"] = reste

        nouvelle_zone = {
            "slug": slug, "nom": nom, "niveau": 1, "type": type_zone, "parent": None,
            "origine_reelle": origine_reelle, "description": description, "statut": statut,
            "tensions_internes": tensions_internes, "periode_transition": periode_transition,
            "evenement_transition": None, "lieux_emblematiques": lieux_emblematiques or [],
            "relations": relations or {"allies": [], "rivaux": []},
            "sources_attestees": sources_attestees or [],
        }
        zones.append(nouvelle_zone)
        gf.body = gf.body.rstrip("\n") + f"\n\n### {nom}\n{description}\n"
        self._save_geo(gf)

        pays_synchronises = []
        zp = self._load_zones_pays()
        sc = zp.get(scenario, {})
        index_norm_vers_canonique = {_normalise_pays(p): p for p in zp.get("pays_liste", [])}
        for o in origine_reelle:
            if o.get("type_entite") != "pays":
                continue
            canonique = index_norm_vers_canonique.get(_normalise_pays(o.get("entite", "")))
            if canonique:
                sc[canonique] = slug
                pays_synchronises.append(canonique)
        if pays_synchronises:
            zp[scenario] = sc
            self._save_zones_pays(zp)

        return {
            "ok": True, "slug": slug, "nom": nom,
            "pays_zones_pays_json": pays_synchronises,
            "zones_nettoyees_du_doublon": zones_nettoyees,
        }

    # ── SUPPRIMER une zone niveau 1 ─────────────────────────────────────
    #
    # Aucune opération de suppression n'existait avant cette refonte (rename/
    # reparent/split/personnaliser, jamais delete) -- ajoutée le 12 sept 2026
    # à la demande de David (repartir de zéro sur interzone_corridor_test).
    # Bloque si la zone a des sous-zones (pas de suppression en cascade
    # silencieuse -- il faut d'abord les déplacer ou les supprimer
    # explicitement, même doctrine prudente que le reste du repository).
    # Ne touche PAS au corps markdown (le texte narratif éventuel sous cette
    # zone reste dans le fichier, à nettoyer à la main si besoin -- purement
    # cosmétique, sans effet sur aucune fonctionnalité).

    def supprimer_zone_n1(self, scenario: str, slug: str, dry_run: bool = True) -> dict:
        """Supprime une zone (n'importe quel niveau -- voir fix ci-dessous),
        avec nettoyage des enfants bloquants, relations, zones_pays.json et
        overlays associés.

        Fix (13 sept 2026, cas Casablanca-Périphérie) : cette méthode
        refusait initialement toute zone de niveau != 1 ("nouvelle capacité"
        du 12 sept, pensée pour le cas Interzone Corridor, une zone racine).
        Le nom est resté (contrat des routes existantes), mais la
        restriction de niveau a été retirée -- rien dans la logique
        ci-dessous (recherche d'enfants directs, nettoyage relations/
        zones_pays.json/overlays) n'est spécifique à une zone racine, et le
        même geste est désormais nécessaire pour une sous-zone niveau 2/3
        (le blocage sur enfants restants s'applique de la même façon, quel
        que soit le niveau de la zone supprimée)."""
        gf = self._load_geo(scenario)
        zones = gf.zones
        target = self._find(zones, slug)
        if not target:
            raise ZoneRepositoryError(f"Zone '{slug}' introuvable dans {scenario}")

        enfants = self._enfants_directs(zones, slug)
        if enfants and not dry_run:
            raise ZoneRepositoryError(
                f"Impossible de supprimer '{slug}' : {len(enfants)} sous-zone(s) encore "
                f"rattachée(s) ({', '.join(e.get('slug') for e in enfants)}) -- déplace-les "
                "ou supprime-les d'abord."
            )

        zones_relations_liees = [
            z.get("slug") for z in zones
            if isinstance(z.get("relations"), dict) and (
                slug in (z["relations"].get("allies") or []) or
                slug in (z["relations"].get("rivaux") or [])
            )
        ]

        zp = self._load_zones_pays()
        sc = zp.get(scenario, {})
        pays_a_desaffecter = [p for p, s in sc.items() if s == slug]

        fc = self._load_overlays(scenario)
        overlays_a_supprimer = [
            f["properties"]["id"] for f in fc.get("features", [])
            if f.get("properties", {}).get("zone_slug") == slug
        ]

        if dry_run:
            return {
                "zone": {"slug": slug, "nom": target.get("nom")},
                "enfants_bloquants": [{"slug": e.get("slug"), "nom": e.get("nom")} for e in enfants],
                "zones_relations_liees": zones_relations_liees,
                "pays_a_desaffecter": pays_a_desaffecter,
                "overlays_a_supprimer": len(overlays_a_supprimer),
                "peut_supprimer": not enfants,
            }

        for z in zones:
            rel = z.get("relations")
            if not isinstance(rel, dict):
                continue
            for cle in ("allies", "rivaux"):
                lst = rel.get(cle)
                if isinstance(lst, list) and slug in lst:
                    rel[cle] = [s for s in lst if s != slug]

        gf.zones[:] = [z for z in zones if z.get("slug") != slug]
        self._save_geo(gf)

        if pays_a_desaffecter:
            for p in pays_a_desaffecter:
                sc[p] = None
            zp[scenario] = sc
            self._save_zones_pays(zp)

        if overlays_a_supprimer:
            fc["features"] = [f for f in fc.get("features", [])
                              if f.get("properties", {}).get("zone_slug") != slug]
            self._save_overlays(scenario, fc)

        return {
            "ok": True, "slug": slug,
            "zones_relations_nettoyees": len(zones_relations_liees),
            "pays_desaffectes": pays_a_desaffecter,
            "overlays_supprimes": len(overlays_a_supprimer),
        }

    # ── OVERLAYS : créer / supprimer ────────────────────────────────────

    def overlay_creer(self, scenario: str, zone_slug: str, pays: str,
                       geometry: dict, portion: Optional[str] = None) -> dict:
        """Ajoute un polygone custom. Si `pays` n'est pas encore dans
        origine_reelle de `zone_slug`, l'entrée y est créée (découpage à la
        volée, comportement identique à l'existant). Écrit directement
        (pas de dry_run -- même doctrine que personnaliser/assign_pays :
        c'est un geste de dessin, pas une restructuration)."""
        gf = self._load_geo(scenario)
        zone_obj = self._find(gf.zones, zone_slug)
        if zone_obj is None:
            raise ZoneRepositoryError(f"zone '{zone_slug}' introuvable dans geographie/{scenario}.md")

        origine = zone_obj.setdefault("origine_reelle", [])
        entry = next((o for o in origine if o.get("entite") == pays), None)
        origine_reelle_creee = False
        if entry:
            portion_source = entry.get("portion")
        else:
            origine.append({"entite": pays, "type_entite": "pays", "portion": portion})
            portion_source = portion
            origine_reelle_creee = True
            self._save_geo(gf)

        fc = self._load_overlays(scenario)
        feature = {
            "type": "Feature",
            "properties": {"id": str(uuid.uuid4()), "zone_slug": zone_slug,
                           "pays": pays, "portion_source": portion_source},
            "geometry": geometry,
        }
        fc.setdefault("features", []).append(feature)
        self._save_overlays(scenario, fc)

        return {"feature": feature, "total_features": len(fc["features"]),
                "origine_reelle_creee": origine_reelle_creee}

    def overlay_supprimer(self, scenario: str, feature_id: str) -> dict:
        """Retire le masque (le tracé dessiné).

        Fix (13 sept 2026, cas Pays-Bas/Zone Interdite de Heysham) : le
        correctif du 12 sept se contentait de vider le texte `portion`
        associé, en laissant l'entrée `origine_reelle` du pays en place
        (avec `portion: null`). Or une entrée sans overlay ET sans texte
        est structurellement IDENTIQUE à un vrai rattachement "pays
        entier" (voir origine_reelle_index()/_paires_overlay()) -- chaque
        suppression de masque recréait donc, de fait, un nouveau doublon
        pays-entier comme celui déjà nettoyé sur la Belgique. Le vrai fix :
        retirer l'entrée `origine_reelle` ELLE-MÊME (pas seulement son
        texte) quand plus AUCUN autre masque ne couvre ce couple
        (zone, pays) après suppression -- un pays affecté à une zone
        UNIQUEMENT via overlay n'a aucune raison d'y rester listé une fois
        son dernier tracé supprimé. Cas particulier géré : si un autre
        masque distinct existe encore pour le même (zone, pays) --
        plusieurs polygones pour un pays découpé en plusieurs morceaux
        dans la même zone -- l'entrée origine_reelle est conservée
        (légitimement toujours backée par un tracé)."""
        fc = self._load_overlays(scenario)
        features = fc.get("features", [])
        supprime = next((f for f in features if f.get("properties", {}).get("id") == feature_id), None)
        if supprime is None:
            raise ZoneRepositoryError(f"id '{feature_id}' introuvable")

        fc["features"] = [f for f in features if f.get("properties", {}).get("id") != feature_id]
        self._save_overlays(scenario, fc)

        props = supprime.get("properties", {})
        zone_slug, pays = props.get("zone_slug"), props.get("pays")
        origine_reelle_retiree = False
        if zone_slug and pays:
            n = _normalise_pays(pays)
            autre_masque_restant = any(
                f.get("properties", {}).get("zone_slug") == zone_slug
                and _normalise_pays(f.get("properties", {}).get("pays", "")) == n
                for f in fc["features"]
            )
            if not autre_masque_restant:
                gf = self._load_geo(scenario)
                zone_obj = self._find(gf.zones, zone_slug)
                if zone_obj:
                    origine = zone_obj.get("origine_reelle") or []
                    reste = [o for o in origine
                             if not (isinstance(o, dict) and _normalise_pays(o.get("entite", "")) == n)]
                    if len(reste) != len(origine):
                        zone_obj["origine_reelle"] = reste
                        origine_reelle_retiree = True
                        self._save_geo(gf)

        return {"supprime": True, "total_features": len(fc["features"]),
                "origine_reelle_retiree": origine_reelle_retiree}
