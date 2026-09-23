#!/usr/bin/env python3
"""
diagnostiquer_doublons_pays_entier.py

Diagnostic (et nettoyage optionnel) des pays ayant plusieurs memberships
"pays entier" simultanés dans origine_reelle -- classe de bug identique au
"Doublon Turquie" corrigé le 12 septembre 2026 dans creer_zone_n1(), mais
qui touchait déjà le vault AVANT ce fix et n'a jamais été nettoyé
rétroactivement (le fix empêche la récidive future, ne corrige rien
d'existant). Cas trouvé le 13 septembre sur la Belgique (espace_nordique_
arctique + zone_euro_sud toutes deux "pays entier") via le nouveau panneau
GUI "zones d'appartenance" -- suspecté par David comme un effet de bord
des outils de dessin de zone (S11 et l'ancien flux overlay).

Doctrine : DIAGNOSTIC SEUL par défaut (aucune écriture). Le nettoyage
n'écrit qu'avec --nettoyer --pays "X" --garder <slug> --execute -- sans
--execute, tout est dry-run (même garde-fou que retirer_pays_des_autres_
zones() dans zone_repository.py, réutilisée ici telle quelle, aucune
nouvelle logique d'écriture n'est ajoutée par ce script).

Un pays a un "pays entier" en double si au moins DEUX zones RACINES niveau 1
DISTINCTES (pas liées en parent/enfant -- une sous-zone niveau 2/3 hérite
normalement le territoire de sa zone niveau 1, ce n'est jamais un doublon)
le référencent toutes deux comme "pays_entier" (aucun tracé overlay ne
justifie l'entrée). Un partage légitime (type France : 1 pays_entier +
overlay(s) ailleurs) n'est jamais signalé -- seul le cas >= 2 racines N1
en conflit (structurellement impossible/non voulu) est un doublon.

Fix (13 sept, deux tours) : la première version (a) relisait tout le
vault une fois par pays trouvé (très lent sur un vault de plusieurs
centaines de pays/entités) et (b) traitait toute entité de origine_reelle
comme un "pays" comparable, sans tenir compte de la hiérarchie parent/
enfant -- résultat, la quasi-totalité des ~200 zones du vault fortress_world
remontait en "doublon" alors qu'il s'agissait de sous-zones niveau 2/3
héritant normalement de leur racine (ex. "Plaine de Pannonie" sous
"Zone Euro Sud"), ou d'entités qui ne sont pas des pays du tout (villes --
"Bruxelles", "Moscou" --, régions fictives -- "Balkans occidentaux",
"Midwest américain" -- forcément absentes de zones_pays.json puisque ce
fichier ne référence QUE les pays souverains). Ce script ne lit plus
qu'une fois chaque fichier, et ne compare que des zones racines niveau 1
n'ayant AUCUN lien de parenté entre elles.

zones_pays.json est utilisé comme référence pour suggérer lequel des deux
memberships racine N1 est probablement le bon à garder, UNIQUEMENT pour
les entités reconnues comme pays réels (présentes dans pays_liste) --
affichage seulement, décision humaine requise avant tout --execute.

Usage :
    python3 diagnostiquer_doublons_pays_entier.py --scenario fortress_world
    python3 diagnostiquer_doublons_pays_entier.py --scenario fortress_world --json
    python3 diagnostiquer_doublons_pays_entier.py --scenario fortress_world \
        --nettoyer --pays Belgique --garder zone_euro_sud            # dry-run
    python3 diagnostiquer_doublons_pays_entier.py --scenario fortress_world \
        --nettoyer --pays Belgique --garder zone_euro_sud --execute  # écrit
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))  # zone_repository.py + app.py dans gui/

from zone_repository import ZoneRepository, ZoneRepositoryError, _normalise_pays, _tokens_entite


def _repo() -> ZoneRepository:
    from app import load_config  # import local, même pattern que routes_carte.py::_repo()
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    gui_dir = Path(__file__).parent
    return ZoneRepository(vault_root, gui_dir)


def _resoudre_entite(entite: str, pays_reconnus_norm: dict, affectation_officielle: dict):
    """Reconnaît une entité composée (ex. "Danemark / Groenland") en la
    découpant avec _tokens_entite() -- même fonction que celle déjà
    utilisée ailleurs dans zone_repository.py pour ce cas précis (14
    juillet 2026), pour ne pas réinventer une logique de tokenisation à
    côté qui divergerait.

    Retourne (reconnue: bool, slug_officiel: str|None). slug_officiel
    n'est renvoyé que si TOUS les tokens sont des pays reconnus ET
    pointent, dans zones_pays.json, vers la MÊME zone pour ce scénario --
    sinon None (soit un token n'est pas un pays reconnu, soit les pays
    composant l'entité sont narrativement répartis différemment, ce qui
    est un cas à traiter à la main, pas à deviner)."""
    tokens = _tokens_entite(entite) or [entite]
    noms_bruts, slugs = [], set()
    for t in tokens:
        raw = pays_reconnus_norm.get(_normalise_pays(t))
        if raw is None:
            return False, None  # au moins un token n'est pas un pays reconnu
        noms_bruts.append(raw)
        slugs.add(affectation_officielle.get(raw))
    if len(slugs) == 1:
        return True, next(iter(slugs))
    return True, None  # reconnue, mais les pays composants divergent -- ambigu, laissé de côté


def scanner_doublons(repo: ZoneRepository, scenario: str) -> list:
    """Une seule lecture de fortress_world.md/geo_overlays/zones_pays.json
    (voir docstring module pour le fix de perf et de faux positifs)."""
    zones = repo.load_all_zones(scenario)
    paires_overlay = repo._paires_overlay(scenario)
    zp = repo._load_zones_pays()
    affectation_officielle = zp.get(scenario, {})
    pays_reconnus_norm = {_normalise_pays(p): p for p in zp.get("pays_liste", [])}

    by_slug = {z.get("slug"): z for z in zones}

    def racine_n1_slug(slug):
        """Équivalent local de resolve_root_n1(), sans reconstruire by_slug
        à chaque appel (déjà construit une fois ci-dessus)."""
        vus = set()
        courant = by_slug.get(slug)
        while courant is not None:
            s = courant.get("slug")
            if s in vus:
                return None
            vus.add(s)
            if int(courant.get("niveau", 1)) == 1:
                return s
            courant = by_slug.get(courant.get("parent"))
        return None

    # entite -> {racine_n1_slug -> meilleure entrée pays_entier trouvée sous
    # cette racine (peu importe qu'elle vienne de la racine elle-même ou
    # d'une sous-zone -- une seule ligne par racine dans le rapport, la
    # hiérarchie interne à une racine n'est jamais un doublon)}
    par_entite: dict = {}
    for z in zones:
        slug = z.get("slug")
        racine = racine_n1_slug(slug)
        if racine is None:
            continue  # cycle/orpheline détectée par ailleurs (diagnostiquer_zones_invisibles.py)
        for o in (z.get("origine_reelle") or []):
            if not isinstance(o, dict) or not o.get("entite"):
                continue
            entite = o["entite"]
            n = _normalise_pays(entite)
            is_overlay = (slug, n) in paires_overlay
            if is_overlay:
                continue  # un overlay n'est jamais un membership "pays entier"
            racines = par_entite.setdefault(entite, {})
            # Garde la première trouvée par racine -- si plusieurs zones
            # SOUS LA MÊME racine référencent l'entité (racine + sous-zones),
            # une seule ligne suffit, ce n'est de toute façon pas comparé
            # entre elles.
            racines.setdefault(racine, {
                "slug": slug, "nom": z.get("nom"), "niveau": z.get("niveau", 1),
                "portion": o.get("portion"), "description": z.get("description"),
            })

    doublons = []
    for entite, racines in sorted(par_entite.items()):
        if len(racines) < 2:
            continue  # une seule racine N1 -> pas de conflit, quel que soit le nombre de sous-zones dessous
        est_pays_reconnu, pays_officiel = _resoudre_entite(entite, pays_reconnus_norm, affectation_officielle)
        memberships = [
            {**info, "racine_slug": racine_slug,
             "racine_nom": by_slug.get(racine_slug, {}).get("nom", racine_slug),
             "correspond_a_zones_pays_json": bool(pays_officiel) and racine_slug == pays_officiel}
            for racine_slug, info in racines.items()
        ]
        doublons.append({
            "entite": entite,
            "est_pays_reconnu": est_pays_reconnu,
            "memberships_racines_n1": memberships,
            "slug_zones_pays_json": pays_officiel,
        })
    return doublons


def formater_rapport_texte(doublons: list, scenario: str) -> str:
    if not doublons:
        return f"Aucun doublon 'pays entier' entre racines N1 distinctes détecté sur {scenario}."

    pays_reels = [d for d in doublons if d["est_pays_reconnu"]]
    autres = [d for d in doublons if not d["est_pays_reconnu"]]

    lignes = []
    if pays_reels:
        lignes.append(f"{len(pays_reels)} PAYS RÉELS avec des racines N1 en conflit sur {scenario} "
                       f"(prioritaire -- affecte la couleur de base de la carte) :\n")
        for d in pays_reels:
            lignes.append(f"● {d['entite']}")
            for m in d["memberships_racines_n1"]:
                marque = "  <- correspond à zones_pays.json" if m["correspond_a_zones_pays_json"] else "  <- ne correspond PAS à zones_pays.json (résidu probable)"
                sous_zone = f" (via sous-zone {m['nom']}, niveau {m['niveau']})" if m["slug"] != m["racine_slug"] else ""
                portion_note = f" [texte portion non vide : {m['portion'][:60]}...]" if m.get("portion") else ""
                lignes.append(f"   - {m['racine_nom']} ({m['racine_slug']}){sous_zone}{marque}{portion_note}")
            if not d["slug_zones_pays_json"]:
                lignes.append("   ⚠ entité composée (plusieurs pays) dont les pays constitutifs sont "
                               "assignés à des zones DIFFÉRENTES dans zones_pays.json -- aucun côté n'est "
                               "confirmé, à trancher à la main (--nettoyer-auto laissera ce cas de côté)")
            lignes.append("")

    if autres:
        lignes.append(f"{len(autres)} entités NON reconnues comme pays souverains (villes, régions fictives -- "
                       f"non comparables à zones_pays.json, à valider narrativement plutôt qu'à 'nettoyer' "
                       f"automatiquement) :\n")
        for d in autres:
            lignes.append(f"● {d['entite']}")
            for m in d["memberships_racines_n1"]:
                sous_zone = f" (via sous-zone {m['nom']}, niveau {m['niveau']})" if m["slug"] != m["racine_slug"] else ""
                portion_note = f"\n     portion : {m['portion']}" if m.get("portion") else "\n     (pas de texte portion)"
                lignes.append(f"   - {m['racine_nom']} ({m['racine_slug']}){sous_zone}{portion_note}")
            lignes.append("")

    return "\n".join(lignes)


def nettoyer_auto(repo: ZoneRepository, scenario: str, dry_run: bool) -> dict:
    """Nettoie automatiquement UNIQUEMENT les pays réels dont le conflit a
    exactement UNE racine correspondant à zones_pays.json (cas non
    ambigu -- garde celle-là, retire l'autre). Toute entité non reconnue
    comme pays souverain, ou dont AUCUNE/PLUSIEURS racines matchent
    zones_pays.json, est explicitement laissée de côté (statut "ignore")
    -- décision humaine requise pour ces cas-là, ce script ne devine
    jamais. Retourne aussi, pour chaque nettoyage réel, les textes
    `portion` retirés (pour ne rien perdre si une portion mérite d'être
    redessinée un jour en overlay -- voir --rapport-portions)."""
    doublons = scanner_doublons(repo, scenario)
    traites, ignores = [], []
    for d in doublons:
        if not d["est_pays_reconnu"]:
            ignores.append({"entite": d["entite"], "raison": "entité non reconnue comme pays souverain"})
            continue
        matches = [m for m in d["memberships_racines_n1"] if m["correspond_a_zones_pays_json"]]
        if len(matches) != 1:
            ignores.append({"entite": d["entite"], "raison": f"{len(matches)} correspondance(s) zones_pays.json (attendu : 1)"})
            continue
        garder = matches[0]["racine_slug"]
        resultat = repo.retirer_doublons_pays_entier(scenario, d["entite"], garder, dry_run=dry_run)
        portions_retirees = [
            {"racine_nom": m["racine_nom"], "racine_slug": m["racine_slug"], "portion": m["portion"]}
            for m in d["memberships_racines_n1"]
            if m["racine_slug"] != garder and m.get("portion")
        ]
        traites.append({"entite": d["entite"], "garde": garder, "resultat": resultat,
                         "portions_retirees": portions_retirees})
    return {"traites": traites, "ignores": ignores}


def formater_rapport_portions_md(traites: list, scenario: str) -> str:
    lignes = [f"# Textes `portion` retirés lors du nettoyage automatique -- {scenario}\n",
              "Conservés ici pour référence -- ces descriptions étaient probablement "
              "destinées à un overlay dont le tracé n'a jamais été enregistré. À "
              "redessiner via le panneau unique si le contenu narratif doit être gardé.\n"]
    for t in traites:
        for p in t["portions_retirees"]:
            lignes.append(f"## {t['entite']} -- retiré de {p['racine_nom']} ({p['racine_slug']})\n")
            lignes.append(p["portion"] + "\n")
    return "\n".join(lignes)


# ── Intégration GUI (14 sept 2026, chantier "onglet Chantiers") ───────────────
#
# --write-chantiers écrit chantiers_geographie.yaml directement plutôt que
# d'exécuter quoi que ce soit -- réimplémentation locale de l'écriture YAML
# (pas d'import de generator/chantiers.py : gui/ et generator/ restent deux
# codebases séparées, ce script vit dans gui/ à côté de zone_repository.py/
# app.py, même convention documentée dans app.py pour _charger_chantiers()/
# _sauver_chantiers() et dans zone_repository.py pour _tokens_entite()).
# Le schéma d'entrée (id, scenario, type, cible, ...) et le type
# "doublon_pays_entier" sont documentés dans generator/chantiers.py -- à
# garder en synchro si ce schéma évolue là-bas.
#
# Champ d'application volontairement restreint aux cas non ambigus (mêmes
# critères que nettoyer_auto()) : un pays reconnu (présent dans
# zones_pays.json) avec EXACTEMENT une racine correspondante. Les entités
# non reconnues comme pays souverains et les cas ambigus (0 ou plusieurs
# correspondances) ne sont JAMAIS écrits automatiquement -- aucune façon
# fiable de calculer une proposition sans zones_pays.json comme référence,
# et l'expérience du 14 sept (Mourmansk, "Inde-Corée du Sud (nœud
# eurasiatique du Pacte)", entités composées type "Nairobi, Kenya") montre
# que ces cas exigent une lecture narrative humaine, pas une règle
# mécanique -- écrire un chantier avec une proposition dessus créerait
# précisément le risque de clic accidentel qu'on cherche à éviter.
#
# Chaque proposition inclut un `contexte_narratif` (premiers ~220
# caractères de la description de la zone retirée) pour permettre de juger
# à l'écran, sans ouvrir geographie/{scenario}.md, si le conflit est un
# vrai doublon ou un rattachement narratif volontaire (cf. bug #6, Corée
# du Sud/inde_corree_noeud_pacte -- ce cas précis n'apparaît de toute
# façon jamais ici : sa racine N1 est la même que celle conservée, donc
# déjà fusionnée en amont par scanner_doublons()).

LONGUEUR_CONTEXTE_NARRATIF = 220


def _slugifier_chantier(texte: str) -> str:
    """Même logique que chantiers.py::_slugifier() côté generator/ --
    dupliquée ici plutôt qu'importée (séparation de codebase, voir
    ci-dessus). À garder en synchro si l'algorithme change là-bas."""
    nfkd = unicodedata.normalize("NFKD", texte)
    sans_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", sans_accents.lower()).strip("_")


def _contexte_narratif(description) -> str:
    if not description:
        return ""
    texte = description.strip()
    if len(texte) <= LONGUEUR_CONTEXTE_NARRATIF:
        return texte
    return texte[:LONGUEUR_CONTEXTE_NARRATIF].rsplit(" ", 1)[0] + "…"


def _chantiers_path(repo: ZoneRepository) -> Path:
    return repo.vault_root / "documentation" / "need_action" / "chantiers_geographie.yaml"


def _charger_chantiers_yaml(repo: ZoneRepository) -> list:
    path = _chantiers_path(repo)
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("chantiers") or []


def _sauver_chantiers_yaml(repo: ZoneRepository, chantiers: list) -> None:
    path = _chantiers_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"chantiers": chantiers}, allow_unicode=True,
                        sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def ecrire_chantiers(repo: ZoneRepository, scenario: str, doublons: list) -> dict:
    """
    Un chantier `doublon_pays_entier` par cas non ambigu (voir filtre
    ci-dessus), avec sa proposition déjà attachée -- rien n'est exécuté,
    seule l'écriture de chantiers_geographie.yaml a lieu. Dédoublonné par
    id (scenario__cible_slugifiee, même schéma que ajouter_chantier() côté
    generator/) : ne touche jamais un chantier déjà présent, quel que soit
    son statut -- protège une approbation/rejet déjà en cours dans le GUI.
    """
    chantiers = _charger_chantiers_yaml(repo)
    ids_existants = {c.get("id") for c in chantiers if isinstance(c, dict)}

    ecrits, deja_presents, ignores = [], [], []
    for d in doublons:
        if not d["est_pays_reconnu"]:
            ignores.append({"entite": d["entite"], "raison": "entité non reconnue comme pays souverain"})
            continue
        matches = [m for m in d["memberships_racines_n1"] if m["correspond_a_zones_pays_json"]]
        if len(matches) != 1:
            ignores.append({"entite": d["entite"],
                             "raison": f"{len(matches)} correspondance(s) zones_pays.json (attendu : 1)"})
            continue

        cle = f"{scenario}__{_slugifier_chantier(d['entite'])}"
        if cle in ids_existants:
            deja_presents.append({"entite": d["entite"], "id": cle})
            continue

        garder = matches[0]
        autres = [m for m in d["memberships_racines_n1"] if m["racine_slug"] != garder["racine_slug"]]
        entree = {
            "id": cle,
            "scenario": scenario,
            "type": "doublon_pays_entier",
            "cible": d["entite"],
            "probleme": f"Pays rattaché à {len(d['memberships_racines_n1'])} zones N1 non apparentées (pays_entier)",
            "source_diagnostic": "diagnostiquer_doublons_pays_entier",
            "date_detection": date.today().isoformat(),
            "statut": "a_traiter",
            "proposition": {
                "slug_a_conserver": garder["racine_slug"],
                "zones_a_retirer": [
                    {"slug": m["racine_slug"], "nom": m["racine_nom"],
                     "contexte_narratif": _contexte_narratif(m.get("description"))}
                    for m in autres
                ],
            },
            "proposition_approuvee": False,
            "date_proposition": date.today().isoformat(),
            "date_traitement": None,
        }
        chantiers.append(entree)
        ecrits.append({"entite": d["entite"], "id": cle, "garde": garder["racine_slug"]})

    if ecrits:
        _sauver_chantiers_yaml(repo, chantiers)

    return {"ecrits": ecrits, "deja_presents": deja_presents, "ignores": ignores}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--json", action="store_true", help="Sortie JSON au lieu du rapport texte")
    ap.add_argument("--nettoyer", action="store_true",
                     help="Mode nettoyage ciblé sur UN pays (requiert --pays et --garder)")
    ap.add_argument("--pays", help="Nom exact du pays (tel qu'il apparaît dans origine_reelle) à nettoyer")
    ap.add_argument("--garder", help="Slug de la zone 'pays entier' à conserver -- toutes les AUTRES occurrences pays_entier sont retirées")
    ap.add_argument("--nettoyer-auto", action="store_true",
                     help="Nettoie en lot tous les pays réels dont le conflit a UNE SEULE correspondance zones_pays.json non ambiguë. Les cas ambigus et les entités non-pays sont toujours laissés de côté.")
    ap.add_argument("--rapport-portions",
                     help="Chemin d'un fichier .md où écrire les textes 'portion' retirés par --nettoyer-auto, avant qu'ils ne disparaissent")
    ap.add_argument("--write-chantiers", action="store_true",
                     help="Écrit un chantier 'doublon_pays_entier' (proposition attachée, non exécutée) dans "
                          "chantiers_geographie.yaml pour chaque cas non ambigu -- à approuver/appliquer ensuite "
                          "depuis l'onglet Chantiers du GUI. N'écrit jamais pour une entité non reconnue comme "
                          "pays souverain ou un cas ambigu (plusieurs/aucune correspondance zones_pays.json).")
    ap.add_argument("--execute", action="store_true",
                     help="Sans ce flag, --nettoyer/--nettoyer-auto restent en dry-run (aucune écriture)")
    args = ap.parse_args()

    try:
        repo = _repo()

        if args.write_chantiers:
            doublons = scanner_doublons(repo, args.scenario)
            resultat = ecrire_chantiers(repo, args.scenario, doublons)
            if args.json:
                print(json.dumps(resultat, ensure_ascii=False, indent=2))
            else:
                print(f"Chantiers 'doublon_pays_entier' écrits pour '{args.scenario}' :\n")
                for e in resultat["ecrits"]:
                    print(f"  ✓ {e['entite']} -> proposition : conserver {e['garde']} ({e['id']})")
                if resultat["deja_presents"]:
                    print(f"\n  {len(resultat['deja_presents'])} déjà présent(s) (jamais réécrit) :")
                    for d in resultat["deja_presents"]:
                        print(f"  - {d['entite']} ({d['id']})")
                if resultat["ignores"]:
                    print(f"\n  {len(resultat['ignores'])} laissé(s) de côté (pas de proposition fiable, décision "
                          f"manuelle requise) :")
                    for i in resultat["ignores"]:
                        print(f"  - {i['entite']} : {i['raison']}")
                if not resultat["ecrits"]:
                    print("  (aucun nouveau chantier écrit)")
                print("\n  Rien n'a été exécuté -- approuver puis appliquer depuis l'onglet Chantiers du GUI.")
            return 0

        if args.nettoyer_auto:
            resultat = nettoyer_auto(repo, args.scenario, dry_run=not args.execute)
            if args.json:
                print(json.dumps(resultat, ensure_ascii=False, indent=2))
            else:
                mode = "EXÉCUTÉ" if args.execute else "DRY-RUN (rien écrit -- relancer avec --execute pour appliquer)"
                print(f"[{mode}] Nettoyage automatique sur '{args.scenario}' :\n")
                for t in resultat["traites"]:
                    r = t["resultat"]
                    cle = "zones_nettoyees" if args.execute else "zones_a_nettoyer"
                    retires = r.get(cle, [])
                    n = len(retires)
                    print(f"  ✓ {t['entite']} -> conservé sur {t['garde']} ({n} racine(s) retirée(s))")
                if resultat["ignores"]:
                    print(f"\n  {len(resultat['ignores'])} entité(s) laissée(s) de côté (décision manuelle requise) :")
                    for i in resultat["ignores"]:
                        print(f"  - {i['entite']} : {i['raison']}")
                print("\n  Les entrées overlay (portions réelles, tracé existant) ne sont jamais touchées.")

            if args.rapport_portions:
                contenu = formater_rapport_portions_md(resultat["traites"], args.scenario)
                Path(args.rapport_portions).write_text(contenu, encoding="utf-8")
                print(f"\n  Textes portion retirés sauvegardés dans {args.rapport_portions}")
            return 0

        if args.nettoyer:
            if not args.pays or not args.garder:
                print("Erreur : --nettoyer requiert --pays et --garder", file=sys.stderr)
                return 1
            resultat = repo.retirer_doublons_pays_entier(
                args.scenario, args.pays, args.garder, dry_run=not args.execute
            )
            if args.json:
                print(json.dumps(resultat, ensure_ascii=False, indent=2))
            else:
                mode = "EXÉCUTÉ" if args.execute else "DRY-RUN (rien écrit -- relancer avec --execute pour appliquer)"
                print(f"[{mode}] Nettoyage de '{args.pays}', conservé sur '{args.garder}' :")
                if not args.execute:
                    for zt in resultat.get("zones_a_nettoyer", []):
                        print(f"  - sera retiré de {zt['nom']} ({zt['slug']})")
                    if not resultat.get("zones_a_nettoyer"):
                        print("  (aucune autre occurrence 'pays entier' trouvée -- rien à faire)")
                    if resultat.get("zones_pays_json_sera_corrige"):
                        print(f"  - zones_pays.json sera aussi corrigé (était : {resultat.get('zones_pays_json_avant')})")
                else:
                    for slug in resultat.get("zones_nettoyees", []):
                        print(f"  - retiré de {slug}")
                    if not resultat.get("zones_nettoyees"):
                        print("  (aucune autre occurrence 'pays entier' trouvée -- rien à faire)")
                    if resultat.get("zones_pays_json_corrige"):
                        print("  - zones_pays.json corrigé")
                print("  Les entrées overlay (portions réelles, tracé existant) ne sont jamais touchées par ce nettoyage.")
            return 0

        doublons = scanner_doublons(repo, args.scenario)
        if args.json:
            print(json.dumps({"scenario": args.scenario, "doublons": doublons}, ensure_ascii=False, indent=2))
        else:
            print(formater_rapport_texte(doublons, args.scenario))
        return 0

    except ZoneRepositoryError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
