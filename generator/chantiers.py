#!/usr/bin/env python3
"""
chantiers.py — Ourrassol 2098

Module partagé de lecture/écriture de chantiers_geographie.yaml — LE fichier
unique de suivi des problèmes géographiques détectés (zones suspectes,
pays sans zone cohérente), remplaçant depuis le 25 juillet 2026 :
  - patron_spatial_suspectes.yaml (check_patron_spatial_coherence.py)
  - zones_manquantes.yaml (check_origine_reelle_coherence.py)
  - zones_proposees_topdown_{scenario}.yaml x6 (generer_zones_topdown.py)

Motivation : plusieurs fichiers de suivi distincts, un par scénario pour
certains, rendaient impossible d'avoir "une seule liste de ce qui reste à
traiter" -- exactement le problème remonté le 25 juillet. Un seul fichier,
une entrée par problème, la proposition de correction (si générée) vivant
DANS la même entrée plutôt que dans un fichier séparé à croiser par
scenario+slug.

SCHÉMA D'UNE ENTRÉE
--------------------
    id: <scenario>__<cible>              # identifiant stable, voir _id()
    scenario: breakdown
    type: zone_suspecte | pays_sans_zone
    cible: geneve_bunker_institutions    # slug de zone (zone_suspecte)
                                          # ou nom de pays (pays_sans_zone)
    probleme: "texte du diagnostic"
    source_diagnostic: patron_spatial | origine_reelle | zones_coherence
    date_detection: "2026-07-25"
    statut: a_traiter | ignore | traite
    proposition: null | {...zone complète, schéma validate_zone()...}
    proposition_approuvee: false         # true = relu et approuvé, prêt pour --apply-topdown
    date_proposition: null | "2026-07-25"
    date_traitement: null | "2026-07-25"

STATUTS -- volontairement réduits à 3 (simplifié le 25 juillet, les 5
statuts précédents de patron_spatial_suspectes.yaml ajoutaient de la
précision mais pas de la clarté) :
  a_traiter : détecté, personne ne l'a encore tranché -- apparaît dans la
              liste "à traiter" de l'onglet Chantiers du GUI.
  ignore    : examiné, jugé être un choix narratif légitime -- la zone ne
              change pas, mais plus jamais réaffiché.
  traite    : la zone A ÉTÉ MODIFIÉE pour corriger le problème (proposition
              générée puis appliquée, ou édition manuelle) -- peu importe
              comment, le problème d'origine n'existe plus.

RÈGLE D'ÉCRITURE : ne JAMAIS écraser une entrée déjà présente (même clé
`id`) -- seuls `ajouter_chantier()` (n'ajoute que du nouveau) et
`mettre_a_jour_chantier()` (modification explicite d'une entrée précise,
utilisée pour attacher une proposition ou changer un statut) touchent le
fichier. Aucune fonction "tout réécrire" -- même principe que
patron_spatial_suspectes.yaml avant lui : le statut est une décision
humaine (ou une application explicite), jamais recalculé automatiquement.
"""

import re
import unicodedata
from datetime import date
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
CHANTIERS_FILE = VAULT_ROOT / "documentation" / "need_action" / "chantiers_geographie.yaml"

STATUT_DEFAUT = "a_traiter"
STATUTS_VALIDES = {"a_traiter", "ignore", "traite"}
TYPES_VALIDES = {"zone_suspecte", "pays_sans_zone"}


def _slugifier(texte: str) -> str:
    """Normalise `cible` en un fragment d'id stable (minuscules, sans accent,
    espaces -> underscore) -- un nom de pays et un slug de zone doivent tous
    les deux produire un id lisible et stable dans le temps."""
    nfkd = unicodedata.normalize("NFKD", texte)
    sans_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", sans_accents.lower()).strip("_")


def _id(scenario: str, cible: str) -> str:
    return f"{scenario}__{_slugifier(cible)}"


class ChantiersCorrompuError(RuntimeError):
    """Levée quand chantiers_geographie.yaml existe mais est illisible (YAML
    invalide) -- distinct d'un fichier absent/vide, qui est un état normal."""


def charger_chantiers() -> list:
    """Retourne la liste brute des chantiers (lecture seule).

    Si le fichier existe mais que son contenu YAML est invalide, lève
    ChantiersCorrompuError plutôt que de renvoyer une liste vide -- une
    corruption ne doit JAMAIS être confondue avec "fichier absent/vide",
    sous peine qu'un appel ultérieur à ajouter_chantier()/mettre_a_jour_
    chantier() écrase silencieusement le fichier corrompu avec seulement
    la nouvelle entrée, perdant tout le reste sans aucun message (bug
    trouvé et corrigé le 25 juillet 2026, avant tout test sur le vault
    réel). Un fichier corrompu doit être réparé à la main avant de
    pouvoir écrire quoi que ce soit dedans."""
    if not CHANTIERS_FILE.exists():
        return []
    try:
        data = yaml.safe_load(CHANTIERS_FILE.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ChantiersCorrompuError(
            f"{CHANTIERS_FILE} existe mais son contenu YAML est invalide -- "
            f"refus de continuer pour ne pas risquer d'écraser les données "
            f"existantes. Corriger le fichier à la main avant de relancer : {e}"
        ) from e
    return data.get("chantiers") or []


def _sauver_chantiers(chantiers: list) -> None:
    CHANTIERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHANTIERS_FILE.write_text(
        yaml.safe_dump({"chantiers": chantiers}, allow_unicode=True,
                        sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def ajouter_chantier(scenario: str, type_: str, cible: str, probleme: str,
                      source_diagnostic: str, **extra) -> bool:
    """
    Ajoute un chantier s'il n'existe pas déjà (dédoublonné sur l'id
    scenario+cible) -- ne touche JAMAIS une entrée déjà présente, quel que
    soit son statut. Retourne True si effectivement ajouté, False si déjà
    connu (aucune écriture dans ce cas).

    `**extra` : champs additionnels optionnels propres à un type de
    diagnostic (ex. `zone_incoherente_a_reparenter` pour un chantier
    pays_sans_zone détecté par check_origine_reelle_coherence.py) --
    fusionnés dans l'entrée sans polluer le schéma de base.
    """
    if type_ not in TYPES_VALIDES:
        raise ValueError(f"type invalide : {type_!r} (attendu {TYPES_VALIDES})")

    chantiers = charger_chantiers()
    cle = _id(scenario, cible)
    if any(c.get("id") == cle for c in chantiers if isinstance(c, dict)):
        return False

    entree = {
        "id": cle,
        "scenario": scenario,
        "type": type_,
        "cible": cible,
        "probleme": probleme,
        "source_diagnostic": source_diagnostic,
        "date_detection": date.today().isoformat(),
        "statut": STATUT_DEFAUT,
        "proposition": None,
        "proposition_approuvee": False,
        "date_proposition": None,
        "date_traitement": None,
    }
    entree.update(extra)
    chantiers.append(entree)
    _sauver_chantiers(chantiers)
    return True


def get_chantier(scenario: str, cible: str) -> dict:
    """Retourne l'entrée complète, ou None si inconnue."""
    cle = _id(scenario, cible)
    for c in charger_chantiers():
        if isinstance(c, dict) and c.get("id") == cle:
            return c
    return None


def mettre_a_jour_chantier(scenario: str, cible: str, **champs) -> bool:
    """
    Modifie une entrée déjà existante (identifiée par scenario+cible) --
    utilisé pour attacher une proposition générée (`proposition`,
    `date_proposition`) ou changer le statut (`statut`, `date_traitement`).
    Ne crée jamais une nouvelle entrée -- retourne False si l'id est
    inconnu, sans rien écrire.
    """
    if "statut" in champs and champs["statut"] not in STATUTS_VALIDES:
        raise ValueError(f"statut invalide : {champs['statut']!r} (attendu {STATUTS_VALIDES})")

    chantiers = charger_chantiers()
    cle = _id(scenario, cible)
    trouve = False
    for c in chantiers:
        if isinstance(c, dict) and c.get("id") == cle:
            c.update(champs)
            trouve = True
            break
    if trouve:
        _sauver_chantiers(chantiers)
    return trouve


def chantiers_prets_a_appliquer(scenario: str = None, type_: str = None, cible: str = None) -> list:
    """
    Chantiers en statut `a_traiter`, avec une proposition générée ET
    approuvée (`proposition_approuvee: true`) -- c'est cette liste que
    consomme --apply-topdown (C.3) ou le bouton "Appliquer" du GUI. Une
    proposition générée mais pas encore approuvée n'apparaît jamais ici.

    `cible` (ajouté le 1er août 2026) restreint à un seul chantier précis
    (slug de zone ou nom de pays) -- utilisé par --apply-topdown --cible et
    par /api/chantiers/appliquer côté GUI (id de chantier), pour appliquer
    un chantier isolé plutôt que tout un scénario d'un coup.
    """
    resultat = [
        c for c in charger_chantiers()
        if isinstance(c, dict) and c.get("statut") == STATUT_DEFAUT
        and c.get("proposition") is not None and c.get("proposition_approuvee") is True
    ]
    if scenario:
        resultat = [c for c in resultat if c.get("scenario") == scenario]
    if type_:
        resultat = [c for c in resultat if c.get("type") == type_]
    if cible:
        resultat = [c for c in resultat if c.get("cible") == cible]
    return resultat


def chantiers_eligibles(scenario: str = None, type_: str = None) -> list:
    """
    Chantiers en statut `a_traiter` (jamais `ignore`/`traite`) -- optionnellement
    filtrés par scénario et/ou type. C'est la liste que consultent
    generer_zones_topdown.py (C.3) et l'onglet Chantiers du GUI.
    """
    resultat = [
        c for c in charger_chantiers()
        if isinstance(c, dict) and c.get("statut") == STATUT_DEFAUT
    ]
    if scenario:
        resultat = [c for c in resultat if c.get("scenario") == scenario]
    if type_:
        resultat = [c for c in resultat if c.get("type") == type_]
    return resultat
