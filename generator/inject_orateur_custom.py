#!/usr/bin/env python3
"""
inject_orateur_custom.py — Ourrassol 2098

Contrepartie de inject_journaliste_custom.py (23 août 2026) pour les
orateur·rices itinérant·es du registre oral (P21, voir prompt_builder.py
STYLE_ORAL / get_journal_profile()). Deux différences structurelles
avec les journalistes, reflétées ici :

  - Un·e orateur·rice n'a jamais de `thematiques` -- get_journal_profile()
    ne les filtre jamais par thématique (contrairement aux journalistes).
    Il n'y a donc pas de "couverture thématique" à combler : le mode
    auto cible un EFFECTIF minimum par zone, pas une couverture.
  - Les orateur·rices ne sont utilisé·es que sur une zone dont
    `type_diffusion` vaut "oral" ou "mixte" -- en créer sur une zone
    "ecrit" (valeur par défaut) les laisserait inutilisés, le mécanisme
    de sélection ne les tirant jamais dans ce cas.

  --mode manuel : ajoute UN·E orateur·rice précis·e (scénario/ligne/
    zone choisis explicitement), généré·e par LLM avec un nom et un
    profil (communautés desservies, réputation orale) cohérents avec
    le ton déjà établi de l'édition. N'exige pas que type_diffusion
    soit déjà oral/mixte (avertissement non-bloquant sinon) -- David
    peut préparer une zone avant d'activer l'oral.
    --avec-ton-personnel (optionnel, mode manuel uniquement, 29 août
    2026) : enchaîne un ton_personnel juste après la création, via
    set_ton_personnel.py (mêmes garde-fous). Jamais en mode auto.

  --mode auto : scanne UN scénario (--scenario toujours requis, PAS de
    --all multi-scénarios contrairement à inject_journaliste_custom.py
    -- les orateurs sont opt-in par zone via type_diffusion, un
    balayage aveugle sur les 6 scénarios créerait des orateurs sur des
    zones jamais pensées pour l'oral), et pour chaque zone déjà
    oral/mixte n'ayant pas encore l'effectif cible, crée les
    orateur·rices manquant·es par LLM.

  --mode convertir (29 août 2026, P21) : bascule type_diffusion ET
    crée les orateur·rices manquant·es, sur une liste EXPLICITE de
    zones (--zones, format "ligne::zone_slug" chacune) -- jamais un
    balayage automatique de zones à convertir, David choisit toujours
    lui-même la liste (alimentée côté GUI par un scan de candidates en
    lecture seule, zones_candidates_oral dans app.py). Contrairement
    au mode auto, ce mode DÉCIDE où l'oral s'active, donc ne fait
    jamais ce choix seul.

Réutilise load_journaux()/save_journaux()/parse_geographie() de
generate_journaux.py, même fichier de sortie, mêmes conventions.

Sauvegarde automatique horodatée avant toute écriture (même principe
que set_ton_personnel.py et fix_doublons_journalistes.py, 26-29 août
2026) -- save_journaux() n'a aucun filet natif. Absente de
inject_journaliste_custom.py (23 août, avant que cette convention ne
soit établie) -- ajoutée ici pour rester cohérent avec la pratique la
plus récente plutôt qu'avec le fichier copié.

Usage :
    python3 inject_orateur_custom.py --mode manuel \\
        --scenario breakdown --ligne pro_pouvoir \\
        --zone-slug afrique_centrale_australe

    python3 inject_orateur_custom.py --mode manuel \\
        --scenario breakdown --ligne pro_pouvoir \\
        --zone-slug afrique_centrale_australe \\
        --nom "Le Veilleur des Berges" --seniorite 2 \\
        --avec-ton-personnel

    python3 inject_orateur_custom.py --mode auto \\
        --scenario breakdown --cible 2

    python3 inject_orateur_custom.py --mode auto \\
        --scenario breakdown --ligne pro_pouvoir --dry-run

    python3 inject_orateur_custom.py --mode convertir \\
        --scenario breakdown \\
        --zones pro_pouvoir::maghreb_mediterraneen opposition::afrique_de_louest_lagos_sahel \\
        --type-diffusion-cible oral --cible 2
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_journaux import load_journaux, save_journaux, parse_geographie, JOURNAUX_PATH  # noqa: E402
from llm_client import call_llm, resolve_for_tier  # noqa: E402
from set_ton_personnel import _generer_ton_personnel, _contexte_specifique  # noqa: E402

TASK_TIER = "strict"

# Effectif minimum ciblé par zone oral/mixte en mode auto (29 août
# 2026, retour de David -- "2 orateurs mini"). Pas d'équivalent
# MAX_THEMATIQUES_PAR_JOURNALISTE ici : rien à plafonner, il n'y a pas
# de surcharge thématique possible pour un·e orateur·rice.
EFFECTIF_CIBLE_DEFAUT = 2

# Même défaut que les journalistes (22-23 août 2026), pour cohérence
# des données -- explicite plutôt que de compter sur un repli .get().
SENIORITE_DEFAUT = 1

SYSTEM_PROMPT = (
    "Tu es l'assistant de worldbuilding du projet Ourrassol 2098 — "
    "simulateur de presse fictive en 2098. Tu ajoutes un·e "
    "orateur·rice itinérant·e à une communauté déjà établie, qui "
    "prend la parole oralement devant une assemblée (pas un·e "
    "journaliste écrit·e -- voir STYLE_ORAL dans prompt_builder.py). "
    "Réponds UNIQUEMENT avec un JSON valide. Pas de texte avant ou "
    "après. Pas de backticks."
)


def build_prompt(scenario, ligne, zone_slug, zone_data, geo_zone,
                  angle_specifique, nom_impose=None, genre_impose=None):
    orateurs_existants = zone_data.get("orateurs", []) or []
    noms_existants = [o.get("nom", "") for o in orateurs_existants]
    reputations_existantes = [
        o.get("reputation_orale", "") for o in orateurs_existants if o.get("reputation_orale")
    ]

    # Nom/genre imposés -- même principe que inject_journaliste_custom.py
    # (23 août 2026) : si un nom est déjà choisi par l'utilisateur, le
    # LLM ne doit ni l'inventer ni le modifier.
    if nom_impose:
        consigne_nom = (
            "Le nom de l'orateur·rice est déjà fixé par l'utilisateur : "
            "\"{}\". Ne l'invente pas, ne le modifie pas, ne le retourne "
            "pas dans ta réponse (seuls les autres champs sont "
            "attendus).".format(nom_impose)
        )
    else:
        genre_txt = ""
        if genre_impose == "homme":
            genre_txt = " L'orateur doit être un homme."
        elif genre_impose == "femme":
            genre_txt = " L'oratrice doit être une femme."
        consigne_nom = (
            "Invente un nom crédible pour la culture réelle de cette "
            "zone (pas un nom génériquement \"occidental\" par défaut). "
            "Un·e orateur·rice itinérant·e porte souvent un nom "
            "d'usage/un surnom en plus de son nom propre (voir les "
            "orateur·rices déjà existant·es de cette rédaction pour le "
            "registre attendu), différent des noms déjà "
            "utilisés.{}".format(genre_txt)
        )

    description = geo_zone.get("description", "") if geo_zone else ""
    description = (description[:300] + "...") if len(description) > 300 else description

    format_reponse = (
        '{{\n  "communautes_desservies": ["...", "..."],\n  "reputation_orale": "..."\n}}'
        if nom_impose else
        '{{\n  "nom": "...",\n  "communautes_desservies": ["...", "..."],\n  "reputation_orale": "..."\n}}'
    )

    return """Zone : {zone_nom} ({zone_slug}), scénario {scenario}, ligne éditoriale {ligne}
Ton éditorial déjà établi (à respecter, ne pas réinventer) : {ton}
Registre linguistique déjà établi : {langue_style}
Description de la zone : {description}

Orateur·rices itinérant·es déjà établi·es ({n_existants}) : {noms_existants}
Réputations orales déjà utilisées, à ne pas répéter à l'identique :
{reputations_existantes}

{consigne_nom}

Invente :
- `communautes_desservies` : 1 à 3 groupes/lieux, en LOCUTIONS COURTES
  (5-6 mots maximum chacune, jamais une phrase avec proposition
  relative ou subordonnée) -- exactement le registre des exemples
  réels suivants, à respecter strictement en longueur ET en forme :
  "villages du fleuve", "routes commerçantes", "quartiers du port
  franc". Un lieu/groupe nommé simplement, PAS une description
  narrative de ce lieu.
- `reputation_orale` : une phrase courte décrivant comment cette
  personne est perçue par ses auditoires (ex. "vénérée pour sa mémoire
  des pactes anciens", "récent, mais écouté pour ses nouvelles
  fraîches").
{angle_bloc}
Réponds avec un objet JSON unique :
{format_reponse}""".format(
        zone_nom=zone_data.get("nom", zone_slug),
        zone_slug=zone_slug,
        scenario=scenario,
        ligne=ligne,
        ton=zone_data.get("ton", "") or "(non renseigné)",
        langue_style=zone_data.get("langue_style", "") or "(aucun marqueur particulier)",
        description=description or "(non renseignée)",
        n_existants=len(orateurs_existants),
        noms_existants=", ".join(noms_existants) or "(aucun)",
        reputations_existantes=" / ".join(reputations_existantes) or "(aucune pour l'instant)",
        consigne_nom=consigne_nom,
        angle_bloc=("\nAngle/précision supplémentaire : {}".format(angle_specifique)
                    if angle_specifique else ""),
        format_reponse=format_reponse,
    )


# Garde-fou longueur communautes_desservies (29 août 2026, retour de
# David après un premier test réel : items générés en phrases
# narratives de 16+ mots avec proposition relative, au lieu des
# locutions courtes du vault réel comme "villages du fleuve"). Même
# principe que le garde-fou longueur de set_ton_personnel.py (26
# août) : la consigne seule ("5-6 mots maximum") ne suffit pas de
# façon fiable, un second filet technique avec retry est nécessaire.
# Tolérance à 9 mots plutôt que 6 strict, pour ne pas retenter sur un
# léger dépassement d'un ou deux mots.
MAX_MOTS_COMMUNAUTE = 9


def _generer_orateur(scenario, ligne, zone_slug, zone_data, geo_zone,
                      angle_specifique, nom_impose=None, genre_impose=None,
                      seniorite=SENIORITE_DEFAUT):
    """Jusqu'à deux appels LLM (retry si communautes_desservies trop
    long -- même principe que set_ton_personnel.py). Retourne
    (dict_orateur_ou_None, message).

    Si nom_impose est fourni, le LLM ne génère que communautes_desservies/
    reputation_orale -- le nom final est celui donné par l'utilisateur.
    """
    prompt = build_prompt(scenario, ligne, zone_slug, zone_data, geo_zone,
                           angle_specifique, nom_impose=nom_impose,
                           genre_impose=genre_impose)
    _provider, _model = resolve_for_tier(TASK_TIER)

    derniere_erreur = "raison inconnue"
    for tentative in range(2):
        print("    → LLM ({}, tier={})...".format(_provider, TASK_TIER))
        try:
            raw = call_llm(
                system_prompt=SYSTEM_PROMPT, user_prompt=prompt,
                max_tokens=400, temperature=0.8, task_tier=TASK_TIER,
            ).strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw).strip()
            reponse = json.loads(raw)
        except Exception as e:
            derniere_erreur = "Échec génération LLM : {}".format(e)
            continue

        nom = nom_impose or (reponse.get("nom") or "").strip()
        communautes = [c.strip() for c in (reponse.get("communautes_desservies") or []) if c.strip()]
        reputation = (reponse.get("reputation_orale") or "").strip()
        if not nom or not communautes or not reputation:
            derniere_erreur = (
                "Réponse LLM incomplète (nom={!r}, communautes={!r}, "
                "reputation={!r})".format(
                    nom, reponse.get("communautes_desservies"), reponse.get("reputation_orale"))
            )
            continue

        trop_longues = [c for c in communautes if len(c.split()) > MAX_MOTS_COMMUNAUTE]
        if trop_longues and tentative == 0:
            derniere_erreur = (
                "communaute(s) trop longue(s), forme narrative au lieu "
                "d'une locution courte ({}), retry demandé".format(
                    " / ".join(trop_longues))
            )
            continue

        return {
            "nom": nom,
            "communautes_desservies": communautes,
            "reputation_orale": reputation,
            "seniorite": seniorite,
        }, "OK"

    return None, "Deux tentatives épuisées -- {}".format(derniere_erreur)


def mode_manuel(scenario, ligne, zone_slug, angle_specifique,
                 nom_impose, genre_impose, seniorite, avec_ton_personnel, dry_run):
    journaux = load_journaux()
    zone_data = journaux.get(scenario, {}).get(ligne, {}).get("zones", {}).get(zone_slug)
    if not zone_data:
        print("  ✗ Zone '{}' introuvable dans journaux.yaml pour {}/{} -- "
              "cet outil ajoute un·e orateur·rice à une édition déjà "
              "existante, il n'en crée pas.".format(zone_slug, scenario, ligne))
        sys.exit(1)

    type_diffusion = zone_data.get("type_diffusion", "ecrit")
    if type_diffusion not in ("oral", "mixte"):
        print("  ⚠ Zone en type_diffusion='{}' -- l'orateur·rice ajouté·e "
              "ne sera jamais sélectionné·e tant que la zone ne passe "
              "pas en 'oral' ou 'mixte' dans journaux.yaml (ajout non "
              "bloquant, procède quand même).".format(type_diffusion))

    geo_zones = parse_geographie(scenario) or []
    geo_zone = next((z for z in geo_zones if z.get("slug") == zone_slug), None)
    entree, msg = _generer_orateur(
        scenario, ligne, zone_slug, zone_data, geo_zone,
        angle_specifique, nom_impose=nom_impose, genre_impose=genre_impose,
        seniorite=seniorite,
    )

    if not entree:
        print("  ✗ {}".format(msg))
        sys.exit(1)

    # ton_personnel optionnel (29 août 2026, retour de David) -- mode
    # manuel UNIQUEMENT, jamais en mode auto -- même raisonnement et
    # même réutilisation directe de set_ton_personnel.py que pour
    # inject_journaliste_custom.py (voir ce fichier pour le détail).
    if avec_ton_personnel:
        autres_nuances_zone = [
            e.get("ton_personnel") for _, e in
            [(zone_data.get("journalistes"), j) for j in (zone_data.get("journalistes") or [])] +
            [(zone_data.get("orateurs"), o) for o in (zone_data.get("orateurs") or [])]
            if e.get("ton_personnel")
        ]
        contexte = _contexte_specifique(entree, est_orateur=True)
        valeur_ton, msg_ton = _generer_ton_personnel(
            zone_data, entree["nom"], contexte, autres_nuances_zone
        )
        if valeur_ton:
            entree["ton_personnel"] = valeur_ton
            print("  ✓ ton_personnel : {}".format(valeur_ton))
        else:
            print("  ⚠ ton_personnel non généré ({}) -- {} créé·e quand "
                  "même sans cette nuance.".format(msg_ton, entree["nom"]))

    if dry_run:
        print("  [dry-run] Ajouterait à {}/{}/{} : {} -- dessert {}".format(
            scenario, ligne, zone_slug, entree["nom"],
            ", ".join(entree["communautes_desservies"])))
        return

    zone_data.setdefault("orateurs", []).append(entree)

    backup_path = JOURNAUX_PATH + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(JOURNAUX_PATH, backup_path)
    print("  ✓ Sauvegarde créée : {}".format(backup_path))

    save_journaux(journaux, dry_run=False)
    print("  ✓ Ajouté à {}/{}/{} : {} -- dessert {} ({})".format(
        scenario, ligne, zone_slug, entree["nom"],
        ", ".join(entree["communautes_desservies"]), entree["reputation_orale"]))


def mode_auto(scenario, ligne_filter, cible, dry_run):
    journaux = load_journaux()
    scenario_data = journaux.get(scenario, {})
    if not scenario_data:
        print("  ✗ Scénario '{}' introuvable dans journaux.yaml.".format(scenario))
        sys.exit(1)

    lignes = [ligne_filter] if ligne_filter else ["pro_pouvoir", "opposition"]
    geo_cache = {}
    creations = []  # (ligne, zone_slug, entree)
    zones_eligibles = []  # (ligne, zone_slug) -- déjà oral/mixte, pour le résumé
    zones_deja_cible = []  # (ligne, zone_slug) -- oral/mixte mais déjà à l'effectif cible

    for ligne in lignes:
        ligne_data = scenario_data.get(ligne, {})
        zones = ligne_data.get("zones", {}) or {}

        for zone_slug, zone_data in sorted(zones.items()):
            # Seules les zones déjà oral/mixte sont éligibles -- créer
            # des orateur·rices sur une zone "ecrit" (défaut) les
            # laisserait inutilisé·es, get_journal_profile() ne les
            # tirant jamais dans ce cas.
            type_diffusion = zone_data.get("type_diffusion", "ecrit")
            if type_diffusion not in ("oral", "mixte"):
                continue
            zones_eligibles.append((ligne, zone_slug))

            orateurs = zone_data.get("orateurs", []) or []
            manque = cible - len(orateurs)
            if manque <= 0:
                zones_deja_cible.append((ligne, zone_slug))
                continue

            if scenario not in geo_cache:
                geo_cache[scenario] = {z["slug"]: z for z in (parse_geographie(scenario) or [])}
            geo_zone = geo_cache[scenario].get(zone_slug)

            for _ in range(manque):
                print("  Création nécessaire : {}/{}/{} ({} orateur·rice(s) "
                      "actuellement, cible {})".format(
                          scenario, ligne, zone_slug, len(orateurs), cible))
                entree, msg = _generer_orateur(
                    scenario, ligne, zone_slug, zone_data, geo_zone, None,
                )
                if entree:
                    orateurs.append(entree)
                    zone_data.setdefault("orateurs", orateurs)
                    creations.append((ligne, zone_slug, entree))
                else:
                    print("    ✗ {}".format(msg))

    print()
    print("=" * 70)
    print("RÉSUMÉ -- {} création(s)".format(len(creations)))
    print("=" * 70)
    # Résumé précis (29 août 2026, retour de David) : le message final
    # doit distinguer "aucune zone oral/mixte trouvée" de "toutes les
    # zones oral/mixte sont déjà à l'effectif cible" -- deux causes
    # très différentes que l'ancien message ambigu ne permettait pas
    # de séparer.
    print("  Zones oral/mixte trouvées : {} ({})".format(
        len(zones_eligibles),
        ", ".join("{}/{}".format(l, z) for l, z in zones_eligibles) or "aucune"))
    if zones_deja_cible:
        print("  Déjà à l'effectif cible ({}) : {}".format(
            cible, ", ".join("{}/{}".format(l, z) for l, z in zones_deja_cible)))
    for ligne, zone_slug, entree in creations:
        print("  [création] {}/{}/{} : {} -- dessert {}".format(
            scenario, ligne, zone_slug, entree["nom"],
            ", ".join(entree["communautes_desservies"])))

    if dry_run:
        print()
        print("[dry-run] Rien n'a été écrit sur disque.")
        return

    if not creations:
        print()
        if not zones_eligibles:
            print("Rien à faire -- aucune zone oral/mixte trouvée dans ce "
                  "scénario{}. Vérifie type_diffusion dans journaux.yaml, "
                  "ou passe par --ligne si tu ciblais une seule ligne "
                  "éditoriale.".format(
                      " (ligne {})".format(ligne_filter) if ligne_filter else ""))
        else:
            print("Rien à faire -- les {} zone(s) oral/mixte trouvée(s) "
                  "atteignent déjà l'effectif cible de {} "
                  "orateur·rice(s).".format(len(zones_eligibles), cible))
        return

    backup_path = JOURNAUX_PATH + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(JOURNAUX_PATH, backup_path)
    print()
    print("  ✓ Sauvegarde créée : {}".format(backup_path))

    save_journaux(journaux, dry_run=False)
    print("  ✓ journaux.yaml sauvegardé.")


def mode_convertir(scenario, zones_composites, type_diffusion_cible, cible, dry_run):
    """Bascule type_diffusion sur une liste explicite de zones (format
    "ligne::zone_slug" chacune) ET crée les orateur·rices manquant·es
    pour atteindre l'effectif cible, en une seule commande.

    Conçu pour le multi-select GUI alimenté par _zones_candidates_oral()
    (app.py, 29 août 2026) : David choisit lui-même les zones à
    convertir dans la liste des candidates (celles sans oral/mixte),
    ce mode fait le travail répétitif (bascule + création) sans
    balayage automatique aveugle -- contrairement au mode auto, ce
    mode ne DÉCIDE jamais quelles zones convertir, il exécute
    seulement la liste donnée.
    """
    journaux = load_journaux()
    scenario_data = journaux.get(scenario, {})
    if not scenario_data:
        print("  ✗ Scénario '{}' introuvable dans journaux.yaml.".format(scenario))
        sys.exit(1)
    if not zones_composites:
        print("  ✗ Mode convertir requiert --zones (une ou plusieurs, "
              "format 'ligne::zone_slug', ex. pro_pouvoir::maghreb_mediterraneen).")
        sys.exit(1)

    geo_cache = {}
    creations = []       # (ligne, zone_slug, entree)
    conversions = []     # (ligne, zone_slug, ancien_type_diffusion)
    erreurs = []          # (composite, message)

    for composite in zones_composites:
        if "::" not in composite:
            erreurs.append((composite, "format attendu 'ligne::zone_slug'"))
            continue
        ligne, zone_slug = composite.split("::", 1)
        zone_data = scenario_data.get(ligne, {}).get("zones", {}).get(zone_slug)
        if not zone_data:
            erreurs.append((composite, "zone introuvable pour {}/{}".format(scenario, ligne)))
            continue

        ancien = zone_data.get("type_diffusion", "ecrit")
        zone_data["type_diffusion"] = type_diffusion_cible
        conversions.append((ligne, zone_slug, ancien))
        print("  {}/{}/{} : type_diffusion '{}' -> '{}'".format(
            scenario, ligne, zone_slug, ancien, type_diffusion_cible))

        orateurs = zone_data.get("orateurs", []) or []
        manque = cible - len(orateurs)
        if manque <= 0:
            continue

        if scenario not in geo_cache:
            geo_cache[scenario] = {z["slug"]: z for z in (parse_geographie(scenario) or [])}
        geo_zone = geo_cache[scenario].get(zone_slug)

        for _ in range(manque):
            print("    Création nécessaire ({} orateur·rice(s) "
                  "actuellement, cible {})".format(len(orateurs), cible))
            entree, msg = _generer_orateur(
                scenario, ligne, zone_slug, zone_data, geo_zone, None,
            )
            if entree:
                orateurs.append(entree)
                zone_data.setdefault("orateurs", orateurs)
                creations.append((ligne, zone_slug, entree))
            else:
                print("      ✗ {}".format(msg))

    print()
    print("=" * 70)
    print("RÉSUMÉ -- {} zone(s) convertie(s), {} création(s)".format(
        len(conversions), len(creations)))
    print("=" * 70)
    for ligne, zone_slug, ancien in conversions:
        print("  [conversion] {}/{}/{} : '{}' -> '{}'".format(
            scenario, ligne, zone_slug, ancien, type_diffusion_cible))
    for ligne, zone_slug, entree in creations:
        print("  [création] {}/{}/{} : {} -- dessert {}".format(
            scenario, ligne, zone_slug, entree["nom"],
            ", ".join(entree["communautes_desservies"])))
    if erreurs:
        print("Erreurs :")
        for composite, msg in erreurs:
            print("  {} -- {}".format(composite, msg))

    if dry_run:
        print()
        print("[dry-run] Rien n'a été écrit sur disque.")
        return

    if not conversions:
        print()
        print("Aucune zone convertie -- vérifie le format de --zones.")
        return

    backup_path = JOURNAUX_PATH + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(JOURNAUX_PATH, backup_path)
    print()
    print("  ✓ Sauvegarde créée : {}".format(backup_path))

    save_journaux(journaux, dry_run=False)
    print("  ✓ journaux.yaml sauvegardé.")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", required=True, choices=["manuel", "auto", "convertir"])
    # --scenario toujours requis, contrairement à inject_journaliste_
    # custom.py -- pas de --all ici (29 août 2026, retour de David) :
    # les orateurs sont opt-in par zone, un balayage sur les 6
    # scénarios créerait des orateur·rices sur des zones jamais
    # pensées pour l'oral.
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--ligne", choices=["pro_pouvoir", "opposition"], default=None,
                         help="Mode manuel : requis. Mode auto : optionnel "
                              "(défaut : les deux lignes). Sans effet en mode "
                              "convertir (la ligne est incluse dans --zones).")
    parser.add_argument("--zone-slug", default=None, help="Mode manuel uniquement")
    parser.add_argument("--zones", nargs="+", default=None,
                         help="Mode convertir uniquement -- une ou plusieurs "
                              "zones au format 'ligne::zone_slug' (ex. "
                              "pro_pouvoir::maghreb_mediterraneen), séparées "
                              "par des espaces. Bascule leur type_diffusion "
                              "et crée les orateur·rices manquant·es en une "
                              "seule commande. Alimenté côté GUI par le scan "
                              "de candidates (zones_candidates_oral, app.py) "
                              "-- David choisit lui-même quelles zones "
                              "convertir, jamais un balayage automatique.")
    parser.add_argument("--type-diffusion-cible", choices=["oral", "mixte"], default="oral",
                         help="Mode convertir uniquement -- valeur à appliquer "
                              "aux zones sélectionnées (défaut : oral).")
    parser.add_argument("--nom", default="",
                         help="Mode manuel : nom imposé (optionnel). Si fourni, "
                              "le LLM ne génère que communautes_desservies/"
                              "reputation_orale.")
    parser.add_argument("--genre", choices=["homme", "femme", ""], default="",
                         help="Mode manuel : oriente le LLM sur le genre du "
                              "personnage à inventer -- ignoré si --nom est "
                              "fourni.")
    parser.add_argument("--seniorite", type=int, default=SENIORITE_DEFAUT,
                         help="Mode manuel : poids de la rotation pondérée "
                              "(défaut : {}).".format(SENIORITE_DEFAUT))
    parser.add_argument("--angle-specifique", default="", help="Mode manuel uniquement")
    parser.add_argument("--avec-ton-personnel", action="store_true",
                         help="Mode manuel uniquement -- génère aussi un "
                              "ton_personnel pour cet·te orateur·rice juste "
                              "après sa création (mêmes garde-fous que "
                              "set_ton_personnel.py). Jamais disponible en "
                              "mode auto ou convertir -- la relecture "
                              "individuelle du mode manuel est le point de "
                              "contrôle qui a permis de repérer les dérives "
                              "réelles du 26-29 août sur ce champ.")
    parser.add_argument("--cible", type=int, default=EFFECTIF_CIBLE_DEFAUT,
                         help="Mode auto/convertir : effectif minimum "
                              "d'orateur·rices visé par zone (défaut : "
                              "{})".format(EFFECTIF_CIBLE_DEFAUT))
    parser.add_argument("--dry-run", action="store_true",
                         help="⚠️ Appelle quand même le LLM pour de vrai -- seule "
                              "l'écriture sur disque est court-circuitée.")
    args = parser.parse_args()

    if args.mode == "manuel":
        if not args.ligne or not args.zone_slug:
            print("  ✗ Mode manuel requiert --ligne et --zone-slug (--scenario "
                  "est toujours requis).")
            sys.exit(1)
        mode_manuel(args.scenario, args.ligne, args.zone_slug,
                    args.angle_specifique or None, args.nom.strip() or None,
                    args.genre or None, args.seniorite, args.avec_ton_personnel,
                    args.dry_run)
    elif args.mode == "auto":
        mode_auto(args.scenario, args.ligne, args.cible, args.dry_run)
    else:
        mode_convertir(args.scenario, args.zones, args.type_diffusion_cible,
                        args.cible, args.dry_run)


if __name__ == "__main__":
    main()
