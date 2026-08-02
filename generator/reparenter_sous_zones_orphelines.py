#!/usr/bin/env python3
"""
reparenter_sous_zones_orphelines.py — Ourrassol 2098 (P24 étape C, extension)

Détecte et reparente automatiquement les sous-zones narratives (niveau 2/3)
devenues incohérentes suite au déplacement d'un pays vers une nouvelle zone
niveau 1 -- cas réel qui a motivé ce script (25 juillet 2026) :
`valence_tours_rirec` (Espagne, via la ville "Valence") restée sous
`hub_europeen_regulation` après que l'Espagne a été déplacée vers
`peninsule_iberique_cooperative`. Le mécanisme de suivi déjà existant pour
le split de zone (`_entite_references_pays()`, gui/app.py, P7 étape 4)
n'aurait PAS détecté ce cas : il ne reconnaît que les entités qui SONT
littéralement le nom du pays (ou une variante entre parenthèses), jamais
une ville qui le représente sans le nommer. Ce script réutilise à la place
`resoudre_pays()` (check_origine_reelle_coherence.py), qui passe par la
table VILLE_PAYS -- la même résolution que celle qui a permis à
check_origine_reelle_coherence.py de repérer le cas Valence en premier lieu.

Point clé : les pays "déplacés" sont déduits de l'origine_reelle ACTUELLE de
la zone cible (déjà écrite sur le vault au moment de l'appel) -- pas besoin
de les passer explicitement, la zone cible fait foi. Ça permet à ce script
d'être appelé après coup, sur un vault déjà à jour, aussi bien par un script
Python (import direct, C.3, generator/) que par une route Flask (sous-
processus + JSON, C.4, gui/) -- deux façons d'appeler la même logique,
jamais deux implémentations.

Ne suit que le lien DIRECT (zones dont le PARENT ne représente plus le
pays) -- le sous-arbre de chaque zone trouvée suit ensuite en bloc via
_recalculer_niveaux (transitivité), pas re-vérifié nœud par nœud.

USAGE
-----
    python3 reparenter_sous_zones_orphelines.py --scenario policy_reform --zone-cible peninsule_iberique_cooperative
    python3 reparenter_sous_zones_orphelines.py --scenario policy_reform --zone-cible peninsule_iberique_cooperative --json
"""

import argparse
import json
from pathlib import Path

import yaml

from check_origine_reelle_coherence import resoudre_pays, _charger_cache_llm

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
GUI_DIR = VAULT_ROOT / "gui"
ZONES_PAYS = GUI_DIR / "zones_pays.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]


def _recalculer_niveaux(zones: list, slug_racine: str, niveau_racine: int) -> None:
    """Recalcule récursivement le niveau de `slug_racine` et de tout son
    sous-arbre, en repartant de `niveau_racine` -- même principe que le
    reparent GUI ('le niveau de toute la branche est recalculé si la
    profondeur change'), appliqué ici en lot plutôt qu'un nœud à la fois."""
    def _recurse(slug, niveau):
        z = next((z for z in zones if isinstance(z, dict) and z.get("slug") == slug), None)
        if not z:
            return
        z["niveau"] = niveau
        for enfant in zones:
            if isinstance(enfant, dict) and enfant.get("parent") == slug:
                _recurse(enfant.get("slug"), niveau + 1)
    _recurse(slug_racine, niveau_racine)


def _sous_zones_orphelines(zones: list, pays_deplaces_norm: set,
                            pays_liste_norm: set, cache_llm: dict) -> list:
    """Zones (niveau >= 2) dont l'origine_reelle résout vers un des pays
    déplacés, mais dont le parent actuel ne le représente plus (voir
    docstring du module pour le détail)."""
    def _pays_de_zone(z) -> set:
        resultat = set()
        for o in (z.get("origine_reelle") or []):
            if not isinstance(o, dict) or not o.get("entite"):
                continue
            resolus = resoudre_pays(o["entite"], pays_liste_norm, cache_llm)
            resultat.update(resolus if resolus else [o["entite"].lower().strip()])
        return resultat

    par_slug = {z.get("slug"): z for z in zones if isinstance(z, dict) and z.get("slug")}
    orphelines = []
    for z in zones:
        if not isinstance(z, dict) or z.get("niveau", 1) == 1:
            continue
        parent = par_slug.get(z.get("parent"))
        if not parent:
            continue
        if not (_pays_de_zone(z) & pays_deplaces_norm):
            continue
        if _pays_de_zone(parent) & pays_deplaces_norm:
            continue
        orphelines.append(z)
    return orphelines


def scan_candidats(scenario: str) -> list:
    """Balaie toutes les zones niveau 1 d'un scénario et retourne celles qui
    ont ACTUELLEMENT au moins une sous-zone orpheline en attente -- ajouté
    le 31 juillet 2026 suite à une remarque de David : plutôt que de
    proposer les 16 à 42 zones N1 d'un scénario dans le menu --zone-cible
    (la quasi-totalité n'ayant jamais de sous-zone orpheline à traiter), ne
    proposer que celles qui en ont réellement. Lecture seule -- n'écrit
    jamais rien, aucun appel LLM (resoudre_pays() ne consulte que la table
    VILLE_PAYS + un cache déjà peuplé, jamais l'API en direct -- même
    principe que l'appel automatique depuis l'onglet Carte, voir gui/app.py).

    Complexité : une passe _sous_zones_orphelines() par zone N1 (16 à 42
    selon le scénario), chacune parcourant l'ensemble des zones -- reste
    rapide en pratique puisque resoudre_pays() est un simple lookup, pas un
    appel réseau."""
    geo_file = GEO_DIR / f"{scenario}.md"
    if not geo_file.exists():
        raise FileNotFoundError(f"Fiche introuvable : {geo_file}")

    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{geo_file} : frontmatter YAML mal formé.")
    fm = yaml.safe_load(parts[1]) or {}
    zones = fm.get("zones") or []

    pays_liste = []
    if ZONES_PAYS.exists():
        pays_liste = json.loads(ZONES_PAYS.read_text(encoding="utf-8")).get("pays_liste", [])
    pays_liste_norm = {p.lower().strip() for p in pays_liste}

    cache_llm = _charger_cache_llm()

    candidats = []
    for zone_cible in zones:
        if not isinstance(zone_cible, dict) or zone_cible.get("niveau", 1) != 1:
            continue
        pays_deplaces_norm = {
            (o.get("entite") or "").lower().strip()
            for o in zone_cible.get("origine_reelle") or []
            if isinstance(o, dict) and o.get("type_entite") == "pays"
        }
        if not pays_deplaces_norm:
            continue
        orphelines = _sous_zones_orphelines(zones, pays_deplaces_norm, pays_liste_norm, cache_llm)
        if orphelines:
            candidats.append({
                "slug": zone_cible.get("slug"),
                "nom": zone_cible.get("nom", zone_cible.get("slug")),
                "n_orphelines": len(orphelines),
            })
    return candidats


def reparenter_sous_zones_orphelines(scenario: str, zone_cible_slug: str) -> list:
    """
    Fonction principale, appelée par C.3 (import direct) et par le GUI
    (sous-processus + --json). Lit geographie/{scenario}.md tel qu'il est
    sur disque au moment de l'appel (donc à appeler APRÈS que zone_cible_slug
    ait été réellement écrite, jamais avant), détecte et reparente les
    sous-zones orphelines, écrit avec backup .bak. Retourne la liste des
    slugs reparentés (vide si rien à faire -- écrit alors rien du tout).

    Lève FileNotFoundError / ValueError sur un scénario ou un slug invalide
    -- laissé remonter volontairement, l'appelant décide (CLI : message
    d'erreur ; GUI : converti en JSON {"ok": false, "error": ...}).
    """
    geo_file = GEO_DIR / f"{scenario}.md"
    if not geo_file.exists():
        raise FileNotFoundError(f"Fiche introuvable : {geo_file}")

    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{geo_file} : frontmatter YAML mal formé.")
    fm = yaml.safe_load(parts[1]) or {}
    zones = fm.get("zones") or []

    zone_cible = next((z for z in zones if isinstance(z, dict) and z.get("slug") == zone_cible_slug), None)
    if zone_cible is None:
        raise ValueError(f"Zone cible introuvable dans {scenario} : {zone_cible_slug!r}")

    pays_liste = []
    if ZONES_PAYS.exists():
        pays_liste = json.loads(ZONES_PAYS.read_text(encoding="utf-8")).get("pays_liste", [])
    pays_liste_norm = {p.lower().strip() for p in pays_liste}

    pays_deplaces_norm = {
        (o.get("entite") or "").lower().strip()
        for o in zone_cible.get("origine_reelle") or []
        if isinstance(o, dict) and o.get("type_entite") == "pays"
    }
    if not pays_deplaces_norm:
        return []

    cache_llm = _charger_cache_llm()
    orphelines = _sous_zones_orphelines(zones, pays_deplaces_norm, pays_liste_norm, cache_llm)
    if not orphelines:
        return []

    niveau_enfant = (zone_cible.get("niveau", 1) or 1) + 1
    for z in orphelines:
        z["parent"] = zone_cible_slug
        _recalculer_niveaux(zones, z["slug"], niveau_enfant)

    bak = geo_file.with_suffix(geo_file.suffix + ".bak")
    bak.write_text(raw, encoding="utf-8")
    fm["zones"] = zones
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    geo_file.write_text("---\n" + new_fm + "---" + parts[2], encoding="utf-8")

    return [z["slug"] for z in orphelines]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Détecte et reparente les sous-zones orphelines suite au "
                     "déplacement d'un pays vers zone-cible (déjà écrite sur le vault)."
    )
    ap.add_argument("--scenario", required=True, choices=SCENARIOS)
    ap.add_argument("--zone-cible", required=False,
                     help="Slug de la zone dont l'origine_reelle vient d'être fixée "
                          "(nouvelle création ou reparent manuel). Requis sauf avec "
                          "--scan-candidates.")
    ap.add_argument("--scan-candidates", action="store_true",
                     help="Liste les zones N1 ayant actuellement des sous-zones "
                          "orphelines en attente, sans rien écrire ni exiger de "
                          "--zone-cible.")
    ap.add_argument("--json", action="store_true",
                     help="Sortie machine : un seul objet JSON sur stdout.")
    args = ap.parse_args()

    if args.scan_candidates:
        try:
            candidats = scan_candidats(args.scenario)
        except (FileNotFoundError, ValueError) as e:
            if args.json:
                print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
                raise SystemExit(1)
            raise SystemExit(f"✗ {e}")

        if args.json:
            print(json.dumps({"ok": True, "candidats": candidats}, ensure_ascii=False))
        elif candidats:
            print(f"{len(candidats)} zone(s) candidate(s) :")
            for c in candidats:
                print(f"  - {c['nom']} ({c['slug']}) : {c['n_orphelines']} sous-zone(s) orpheline(s)")
        else:
            print("· Aucune zone candidate — rien à reparenter actuellement.")
        raise SystemExit(0)

    if not args.zone_cible:
        ap.error("--zone-cible est requis (sauf avec --scan-candidates).")

    try:
        reparentees = reparenter_sous_zones_orphelines(args.scenario, args.zone_cible)
    except (FileNotFoundError, ValueError) as e:
        if args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            raise SystemExit(1)
        raise SystemExit(f"✗ {e}")

    if args.json:
        print(json.dumps({"ok": True, "reparentees": reparentees}, ensure_ascii=False))
    elif reparentees:
        print(f"✓ {len(reparentees)} sous-zone(s) reparentée(s) : {', '.join(reparentees)}")
    else:
        print("· Aucune sous-zone orpheline détectée")
