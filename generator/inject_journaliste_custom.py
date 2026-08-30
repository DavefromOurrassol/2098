#!/usr/bin/env python3
"""
inject_journaliste_custom.py — Ourrassol 2098

Deux modes pour combler les trous de couverture thématique d'une
rédaction locale (voir audit_couverture_journalistes.py pour le
diagnostic qui a motivé cet outil, 23 août 2026 -- cas réel
bassin_du_congo/petites_annonces_services, un seul journaliste
éligible sur 6, aucune rotation possible malgré le mécanisme du
22 août) :

  --mode manuel : ajoute UN journaliste précis (scénario/ligne/zone/
    thématiques choisis explicitement), généré par LLM avec un nom et
    un profil cohérents avec le ton déjà établi de l'édition.
    --avec-ton-personnel (optionnel, mode manuel uniquement, 29 août
    2026) : enchaîne un ton_personnel juste après la création, via
    set_ton_personnel.py (mêmes garde-fous). Jamais en mode auto.

  --mode auto : scanne un scénario (toutes zones, ou une ligne
    éditoriale précise), repère les combinaisons zone×thématique sous
    la cible de couverture, et pour chacune choisit intelligemment
    entre :
      a) redistribuer -- ajouter la thématique à un·e journaliste
         existant·e de la zone qui ne la couvre pas déjà (priorité à
         celui/celle qui a le moins de thématiques actuellement),
         SI ça ne le/la fait pas dépasser MAX_THEMATIQUES_PAR_JOURNALISTE
      b) créer -- si tous les journalistes existants de la zone sont
         déjà à ce plafond, générer un nouveau·elle journaliste par LLM
         (comme le mode manuel) plutôt que de surcharger l'existant

Réutilise load_journaux()/save_journaux()/parse_geographie() de
generate_journaux.py (préférence du projet pour les corrections
centralisées) -- même fichier de sortie, mêmes conventions.

Usage :
    python3 inject_journaliste_custom.py --mode manuel \\
        --scenario new_sustainability --ligne pro_pouvoir \\
        --zone-slug afrique_continentale \\
        --thematiques petites_annonces_services,meteo \\
        --avec-ton-personnel

    python3 inject_journaliste_custom.py --mode auto \\
        --scenario new_sustainability --cible 2

    python3 inject_journaliste_custom.py --mode auto \\
        --scenario new_sustainability --ligne pro_pouvoir --dry-run
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_journaux import load_journaux, save_journaux, parse_geographie  # noqa: E402
from llm_client import call_llm, resolve_for_tier  # noqa: E402
from set_ton_personnel import _generer_ton_personnel, _contexte_specifique  # noqa: E402

TASK_TIER = "strict"

THEMATIQUES_CONNUES = [
    "actualites_a_la_une", "politique", "economie_finance", "international",
    "environnement_climat", "sante", "societe", "culture", "musique",
    "sports", "faits_divers", "opinions_editoriaux", "lifestyle_art_de_vivre",
    "education", "histoire_patrimoine", "medias_communication",
    "religion_spiritualite", "petites_annonces_services", "meteo",
    "sciences_technologies",
]

# Plafond au-delà duquel on préfère créer un·e nouveau·elle journaliste
# plutôt que de surcharger un·e existant·e en mode auto (23 août 2026).
# Calibré sur la conception d'origine de generate_journaux.py : 6
# journalistes pour ~20 thématiques, soit une moyenne de ~3-4 chacun --
# ce plafond laisse une marge large (quasi le double) avant de juger
# qu'un·e journaliste est "trop chargé·e" pour rester crédible
# narrativement (un·e journaliste spécialisé qui couvrirait la moitié
# des thématiques du vault perdrait son sens).
MAX_THEMATIQUES_PAR_JOURNALISTE = 6

# Même défaut que celui appliqué le 22 août aux 1740 journalistes
# existants (23 août 2026) -- explicite ici plutôt que de compter sur
# le repli .get("seniorite", ...) du code de rotation, pour que le
# champ soit visible dans journaux.yaml comme pour tous les autres
# (cohérence des données, pas juste équivalence fonctionnelle).
SENIORITE_DEFAUT = 1

SYSTEM_PROMPT = (
    "Tu es l'assistant de worldbuilding du projet Ourrassol 2098 — "
    "simulateur de presse fictive en 2098. Tu ajoutes un·e journaliste "
    "à une rédaction locale déjà établie. Réponds UNIQUEMENT avec un "
    "JSON valide. Pas de texte avant ou après. Pas de backticks."
)


def build_prompt(scenario, ligne, zone_slug, zone_data, geo_zone,
                  thematiques_cibles, angle_specifique,
                  nom_impose=None, genre_impose=None):
    journalistes_existants = zone_data.get("journalistes", []) or []
    dejacouvertes = sorted({
        th for j in journalistes_existants for th in (j.get("thematiques") or [])
    })
    noms_existants = [j.get("nom", "") for j in journalistes_existants]

    if thematiques_cibles:
        consigne_thematiques = (
            "Ce·tte journaliste DOIT couvrir exactement ces thématiques : "
            "{}.".format(", ".join(thematiques_cibles))
        )
    else:
        non_couvertes = [t for t in THEMATIQUES_CONNUES if t not in dejacouvertes]
        # Renforcé (29 août 2026, retour de David après un échec réel :
        # le LLM a inventé des libellés descriptifs libres -- "gestion
        # des citernes d'eau potable", "épidémies insulaires" -- au lieu
        # de piocher dans la liste fermée, et a même mal orthographié
        # "santé" au lieu du slug exact "sante". Le mot "parmi" seul ne
        # suffisait pas à empêcher la dérive -- interdiction explicite +
        # rappel du format slug exact, même principe que les autres
        # garde-fous du projet (consigne seule jamais suffisamment
        # fiable).
        consigne_thematiques = (
            "La rédaction couvre déjà : {}. Choisis 2 à 4 thématiques "
            "COMPLÉMENTAIRES (pas déjà couvertes si possible) -- "
            "EXCLUSIVEMENT parmi cette liste fermée de slugs exacts, "
            "recopiés lettre pour lettre (jamais de majuscule, jamais "
            "d'accent, jamais un libellé que tu inventes toi-même même "
            "s'il te semble plus précis) : {}.".format(
                ", ".join(dejacouvertes) or "(aucune)",
                ", ".join(non_couvertes) or ", ".join(THEMATIQUES_CONNUES),
            )
        )

    # Nom/genre imposés (23 août 2026, retour de David) : si un nom est
    # déjà choisi par l'utilisateur, le LLM ne doit ni l'inventer ni le
    # modifier -- seul le format JSON de réponse change (voir
    # _generer_journaliste). Le genre n'a de sens que si le LLM doit
    # inventer le nom lui-même ; ignoré si nom_impose est fourni.
    if nom_impose:
        consigne_nom = (
            "Le nom du·de la journaliste est déjà fixé par l'utilisateur : "
            "\"{}\". Ne l'invente pas, ne le modifie pas, ne le retourne pas "
            "dans ta réponse (seules les thématiques sont attendues).".format(nom_impose)
        )
    else:
        genre_txt = ""
        if genre_impose == "homme":
            genre_txt = " Le·la journaliste doit être un homme."
        elif genre_impose == "femme":
            genre_txt = " Le·la journaliste doit être une femme."
        consigne_nom = (
            "Invente un nom crédible pour la culture réelle de cette zone "
            "(pas un nom génériquement \"occidental\" par défaut), différent "
            "des noms déjà dans la rédaction.{}".format(genre_txt)
        )

    description = geo_zone.get("description", "") if geo_zone else ""
    description = (description[:300] + "...") if len(description) > 300 else description

    format_reponse = (
        '{{\n  "thematiques": ["...", "..."]\n}}' if nom_impose else
        '{{\n  "nom": "Prénom Nom",\n  "thematiques": ["...", "..."]\n}}'
    )

    return """Zone : {zone_nom} ({zone_slug}), scénario {scenario}, ligne éditoriale {ligne}
Édition locale déjà établie : {edition_nom}
Ton éditorial déjà établi (à respecter, ne pas réinventer) : {ton}
Registre linguistique déjà établi : {langue_style}
Description de la zone : {description}

Rédaction actuelle ({n_existants} journaliste(s)) : {noms_existants}

{consigne_nom} {consigne_thematiques}
{angle_bloc}
Réponds avec un objet JSON unique :
{format_reponse}""".format(
        zone_nom=zone_data.get("nom", zone_slug),
        zone_slug=zone_slug,
        scenario=scenario,
        ligne=ligne,
        edition_nom=zone_data.get("nom", ""),
        ton=zone_data.get("ton", "") or "(non renseigné)",
        langue_style=zone_data.get("langue_style", "") or "(aucun marqueur particulier)",
        description=description or "(non renseignée)",
        n_existants=len(journalistes_existants),
        noms_existants=", ".join(noms_existants) or "(aucun)",
        consigne_nom=consigne_nom,
        consigne_thematiques=consigne_thematiques,
        angle_bloc=("\nAngle/précision supplémentaire : {}".format(angle_specifique)
                    if angle_specifique else ""),
        format_reponse=format_reponse,
    )


def _generer_journaliste(scenario, ligne, zone_slug, zone_data, geo_zone,
                          thematiques_cibles, angle_specifique,
                          nom_impose=None, genre_impose=None, seniorite=SENIORITE_DEFAUT):
    """Jusqu'à deux appels LLM (retry si les thématiques retournées ne
    correspondent à aucun slug connu -- même principe que le garde-fou
    longueur de set_ton_personnel.py, 29 août 2026). Retourne
    (dict_journaliste_ou_None, message).

    Si nom_impose est fourni, le LLM ne génère que les thématiques -- le
    nom final est celui donné par l'utilisateur, jamais celui (absent)
    de la réponse LLM.
    """
    prompt = build_prompt(scenario, ligne, zone_slug, zone_data, geo_zone,
                           thematiques_cibles, angle_specifique,
                           nom_impose=nom_impose, genre_impose=genre_impose)
    _provider, _model = resolve_for_tier(TASK_TIER)

    derniere_erreur = "raison inconnue"
    for tentative in range(2):
        print("    → LLM ({}, tier={})...".format(_provider, TASK_TIER))
        try:
            raw = call_llm(
                system_prompt=SYSTEM_PROMPT, user_prompt=prompt,
                max_tokens=500, temperature=0.7, task_tier=TASK_TIER,
            ).strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw).strip()
            reponse = json.loads(raw)
        except Exception as e:
            derniere_erreur = "Échec génération LLM : {}".format(e)
            continue

        nom = nom_impose or (reponse.get("nom") or "").strip()
        brut = reponse.get("thematiques") or []
        thematiques = [t for t in brut if t in THEMATIQUES_CONNUES]

        if not nom or not thematiques:
            derniere_erreur = (
                "Réponse LLM incomplète ou thématiques hors liste connue "
                "(nom={!r}, thematiques brutes={!r})".format(nom, brut)
            )
            if tentative == 0:
                continue
            return None, derniere_erreur

        return {"nom": nom, "thematiques": thematiques, "seniorite": seniorite}, "OK"

    return None, "Deux tentatives épuisées -- {}".format(derniere_erreur)


def mode_manuel(scenario, ligne, zone_slug, thematiques_cibles, angle_specifique,
                 nom_impose, genre_impose, seniorite, avec_ton_personnel, dry_run):
    journaux = load_journaux()
    zone_data = journaux.get(scenario, {}).get(ligne, {}).get("zones", {}).get(zone_slug)
    if not zone_data:
        print("  ✗ Zone '{}' introuvable dans journaux.yaml pour {}/{} -- "
              "cet outil ajoute un journaliste à une édition déjà existante, "
              "il n'en crée pas.".format(zone_slug, scenario, ligne))
        sys.exit(1)

    # Cas 1 (23 août 2026) : nom ET thématiques fournis -- aucun appel
    # LLM, patch YAML direct. Cas 2 : nom fourni seul -- le LLM ne
    # génère que les thématiques. Cas 3 : nom absent -- comportement
    # d'origine, le LLM génère tout (voir _generer_journaliste).
    if nom_impose and thematiques_cibles:
        entree = {"nom": nom_impose, "thematiques": thematiques_cibles, "seniorite": seniorite}
        msg = "OK"
    else:
        geo_zones = parse_geographie(scenario) or []
        geo_zone = next((z for z in geo_zones if z.get("slug") == zone_slug), None)
        entree, msg = _generer_journaliste(
            scenario, ligne, zone_slug, zone_data, geo_zone,
            thematiques_cibles, angle_specifique,
            nom_impose=nom_impose, genre_impose=genre_impose, seniorite=seniorite,
        )

    if not entree:
        print("  ✗ {}".format(msg))
        sys.exit(1)

    # ton_personnel optionnel (29 août 2026, retour de David) --
    # mode manuel UNIQUEMENT, jamais en mode auto : le point de
    # contrôle qui a permis de repérer les 3 dérives réelles de
    # set_ton_personnel.py (citations verbatim, stéréotypes,
    # dépassement de longueur, 26-29 août) est la relecture
    # individuelle -- un enchaînement en volume sans relecture
    # perdrait ce filet. Réutilise directement _generer_ton_personnel/
    # _contexte_specifique de set_ton_personnel.py (même garde-fous,
    # pas de logique dupliquée). Génère aussi en --dry-run, comme le
    # reste de cet outil (aperçu réel, rien écrit).
    if avec_ton_personnel:
        autres_nuances_zone = [
            e.get("ton_personnel") for _, e in
            [(zone_data.get("journalistes"), j) for j in (zone_data.get("journalistes") or [])] +
            [(zone_data.get("orateurs"), o) for o in (zone_data.get("orateurs") or [])]
            if e.get("ton_personnel")
        ]
        contexte = _contexte_specifique(entree, est_orateur=False)
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
        print("  [dry-run] Ajouterait à {}/{}/{} : {} -- {}".format(
            scenario, ligne, zone_slug, entree["nom"], ", ".join(entree["thematiques"])))
        return

    zone_data.setdefault("journalistes", []).append(entree)
    save_journaux(journaux, dry_run=False)
    print("  ✓ Ajouté à {}/{}/{} : {} -- {}".format(
        scenario, ligne, zone_slug, entree["nom"], ", ".join(entree["thematiques"])))


def mode_auto(scenario, ligne_filter, cible, dry_run):
    journaux = load_journaux()
    scenario_data = journaux.get(scenario, {})
    if not scenario_data:
        print("  ✗ Scénario '{}' introuvable dans journaux.yaml.".format(scenario))
        sys.exit(1)

    lignes = [ligne_filter] if ligne_filter else ["pro_pouvoir", "opposition"]
    geo_cache = {}

    redistributions = []  # (ligne, zone_slug, thematique, nom_journaliste)
    creations = []        # (ligne, zone_slug, thematique(s), entree)

    for ligne in lignes:
        ligne_data = scenario_data.get(ligne, {})
        zones = ligne_data.get("zones", {}) or {}

        for zone_slug, zone_data in sorted(zones.items()):
            journalistes = zone_data.get("journalistes", []) or []
            if not journalistes:
                continue

            couverture = defaultdict(list)
            for j in journalistes:
                for th in (j.get("thematiques") or []):
                    couverture[th].append(j)

            # Thématiques à combler pour cette zone, dans l'ordre du
            # catalogue (déterministe) -- une seule passe, les
            # redistributions décidées plus tôt dans la boucle
            # comptent immédiatement pour les décisions suivantes
            # (évite de surcharger deux fois le même journaliste).
            for thematique in THEMATIQUES_CONNUES:
                actuels = couverture.get(thematique, [])
                manque = cible - len(actuels)
                if manque <= 0:
                    continue

                # a) Tenter la redistribution -- candidats de la zone ne
                # couvrant pas déjà cette thématique, sous le plafond,
                # triés par charge croissante.
                candidats = [
                    j for j in journalistes
                    if thematique not in (j.get("thematiques") or [])
                    and len(j.get("thematiques") or []) < MAX_THEMATIQUES_PAR_JOURNALISTE
                ]
                candidats.sort(key=lambda j: (len(j.get("thematiques") or []), j["nom"]))

                pour_redistribution = candidats[:manque]
                for j in pour_redistribution:
                    j.setdefault("thematiques", []).append(thematique)
                    redistributions.append((ligne, zone_slug, thematique, j["nom"]))
                    manque -= 1

                # b) Ce qui reste après redistribution (plafond atteint
                # partout, ou zone trop petite) -> création d'un·e
                # nouveau·elle journaliste, un par thématique restante
                # pour rester simple et prévisible (pas de fusion de
                # plusieurs thématiques manquantes sur un seul nouveau
                # profil, qui risquerait de sur-spécialiser
                # artificiellement le personnage créé).
                if manque > 0:
                    if scenario not in geo_cache:
                        geo_cache[scenario] = {z["slug"]: z for z in (parse_geographie(scenario) or [])}
                    geo_zone = geo_cache[scenario].get(zone_slug)

                    for _ in range(manque):
                        print("  Création nécessaire : {}/{}/{} -- {}".format(
                            scenario, ligne, zone_slug, thematique))
                        entree, msg = _generer_journaliste(
                            scenario, ligne, zone_slug, zone_data, geo_zone,
                            [thematique], None,
                        )
                        if entree:
                            journalistes.append(entree)
                            couverture[thematique].append(entree)
                            creations.append((ligne, zone_slug, thematique, entree))
                        else:
                            print("    ✗ {}".format(msg))

    print()
    print("=" * 70)
    print("RÉSUMÉ -- {} redistribution(s), {} création(s)".format(
        len(redistributions), len(creations)))
    print("=" * 70)
    for ligne, zone_slug, thematique, nom in redistributions:
        print("  [redistribution] {}/{}/{} : {} -> +{}".format(
            scenario, ligne, zone_slug, nom, thematique))
    for ligne, zone_slug, thematique, entree in creations:
        print("  [création] {}/{}/{} : {} -- {}".format(
            scenario, ligne, zone_slug, entree["nom"], ", ".join(entree["thematiques"])))

    if dry_run:
        print()
        print("[dry-run] Rien n'a été écrit sur disque.")
        return

    if not redistributions and not creations:
        print()
        print("Rien à faire -- toutes les combinaisons zone×thématique "
              "atteignent déjà la cible de {} journaliste(s).".format(cible))
        return

    save_journaux(journaux, dry_run=False)
    print()
    print("  ✓ journaux.yaml sauvegardé.")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", required=True, choices=["manuel", "auto"])
    parser.add_argument("--scenario", default=None,
                         help="Mode manuel : requis. Mode auto : requis SAUF si "
                              "--all est fourni (mutuellement exclusifs).")
    parser.add_argument("--all", action="store_true",
                         help="Mode auto uniquement -- traite les 6 scénarios "
                              "l'un après l'autre plutôt qu'un seul. Mutuellement "
                              "exclusif avec --scenario.")
    parser.add_argument("--ligne", choices=["pro_pouvoir", "opposition"], default=None,
                         help="Mode manuel : requis. Mode auto : optionnel "
                              "(défaut : les deux lignes)")
    parser.add_argument("--zone-slug", default=None, help="Mode manuel uniquement")
    parser.add_argument("--thematiques", nargs="+", choices=THEMATIQUES_CONNUES, default=None,
                         help="Mode manuel : une ou plusieurs thématiques, séparées "
                              "par des espaces (optionnel -- LLM propose si omis)")
    parser.add_argument("--nom", default="",
                         help="Mode manuel : nom imposé (optionnel). Si fourni "
                              "avec --thematiques, aucun appel LLM -- patch YAML "
                              "direct. Si fourni seul, le LLM ne génère que les "
                              "thématiques.")
    parser.add_argument("--genre", choices=["homme", "femme", ""], default="",
                         help="Mode manuel : oriente le LLM sur le genre du "
                              "personnage à inventer -- ignoré si --nom est "
                              "fourni (rien à générer de ce côté).")
    parser.add_argument("--seniorite", type=int, default=SENIORITE_DEFAUT,
                         help="Mode manuel : poids de la rotation pondérée "
                              "(défaut : {}, même convention que les 1740 "
                              "journalistes existants). Plus haut = revient plus "
                              "souvent.".format(SENIORITE_DEFAUT))
    parser.add_argument("--angle-specifique", default="", help="Mode manuel uniquement")
    parser.add_argument("--avec-ton-personnel", action="store_true",
                         help="Mode manuel uniquement -- génère aussi un "
                              "ton_personnel pour cette personne juste après "
                              "sa création (mêmes garde-fous que "
                              "set_ton_personnel.py). Jamais disponible en "
                              "mode auto -- la relecture individuelle du "
                              "mode manuel est le point de contrôle qui a "
                              "permis de repérer les dérives réelles du "
                              "26-29 août sur ce champ.")
    parser.add_argument("--cible", type=int, default=2,
                         help="Mode auto : nombre minimum de journalistes éligibles "
                              "visé par thématique/zone (défaut : 2)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.mode == "manuel":
        if not args.scenario or not args.ligne or not args.zone_slug:
            print("  ✗ Mode manuel requiert --scenario, --ligne et --zone-slug.")
            sys.exit(1)
        mode_manuel(args.scenario, args.ligne, args.zone_slug, args.thematiques,
                    args.angle_specifique or None, args.nom.strip() or None,
                    args.genre or None, args.seniorite, args.avec_ton_personnel,
                    args.dry_run)
    else:
        if args.all and args.scenario:
            print("  ✗ --all et --scenario sont mutuellement exclusifs.")
            sys.exit(1)
        if not args.all and not args.scenario:
            print("  ✗ Mode auto requiert --scenario, ou --all pour traiter les "
                  "6 scénarios d'affilée.")
            sys.exit(1)

        if args.all:
            scenarios = sorted(load_journaux().keys())
            print("  {} scénario(s) à traiter : {}".format(
                len(scenarios), ", ".join(scenarios)))
        else:
            scenarios = [args.scenario]

        for i, scenario in enumerate(scenarios):
            if len(scenarios) > 1:
                print()
                print("### [{}/{}] {} ###".format(i + 1, len(scenarios), scenario))
            mode_auto(scenario, args.ligne, args.cible, args.dry_run)


if __name__ == "__main__":
    main()
