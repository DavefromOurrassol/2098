"""
generate.py
-----------
Point d'entrée unique du générateur d'articles Ourrassol 2098.

Deux modes (ajoutés/restructurés le 2 août 2026) :

  semi_guide (défaut, comportement historique inchangé)
      Un seul scénario (config.yaml : scenario), sélection automatique
      des instances/événements/signaux par pertinence + rotation à
      mémoire, titre suggéré éditable, zone éditable.

  forcer
      Un élément précis (entité/événement/signal) choisi, l'article est
      systématiquement construit autour de lui (mode "sujet_central" --
      pas de variante "ingrédient" dans ce mode, contrairement à la
      version précédente de cette fonctionnalité : la distinction n'a
      plus lieu d'être dans cette architecture, voir échange du
      2 août 2026). Scénarios = "tous" (= tous ceux où l'élément existe
      réellement, pas les 6 sans distinction) ou une liste choisie,
      restreinte à ce qui est disponible. Titre TOUJOURS laissé à l'IA
      (jamais éditable dans ce mode). Un article est généré et sauvegardé
      PAR scénario retenu.

Usage :
    python3 generate.py
    python3 generate.py --dry-run
    python3 generate.py --mode forcer --forcer-type instance \
        --forcer-slug <slug> --forcer-scenarios tous
    python3 generate.py --mode forcer --forcer-type signal \
        --forcer-slug <slug> --forcer-scenarios breakdown policy_reform

Lit config.yaml, orchestre tous les modules et sauvegarde le ou les
article(s) dans le dossier articles/ du vault Obsidian. Les flags CLI
(GUI) surchargent les blocs correspondants de config.yaml s'ils sont
présents -- CLI prioritaire, cohérent avec l'usage GUI où ces champs
sont pilotés par le panneau, pas édités à la main dans config.yaml.
"""

import argparse
import os
import random
import sys
import yaml


def _parse_cli_args():
    """argparse.parse_known_args() pour ne pas planter sur d'éventuels
    autres flags déjà gérés ailleurs via sys.argv.

    Bug corrigé le 2 août 2026 (retour de David, symptôme : article généré
    avec la thématique d'un essai précédent malgré un menu affichant
    correctement la bonne valeur à l'écran) : lors du passage de
    config_fields vers options pour --thematique/--ligne-editoriale/
    --article-longueur/--article-angle-specifique/--scenario/--zone-slug/
    --article-titre-suggere, seuls les flags --forcer-* avaient été ajoutés
    ici. Les 7 champs préexistants étaient donc envoyés par app.js
    (confirmé correct côté navigateur) mais silencieusement ignorés par
    parse_known_args() (flag inconnu = ignoré, pas d'erreur) -- generate.py
    retombait alors sur les valeurs statiques de config.yaml, jamais mises
    à jour depuis la mise en place de ce mécanisme. Concerne le mode
    semi_guide autant que forcer (--scenario/--zone-slug/
    --article-titre-suggere n'étaient utilisés qu'en semi_guide, mais
    avaient exactement le même trou).
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mode", default=None,
                         choices=[None, "", "semi_guide", "forcer"])
    parser.add_argument("--forcer-type", default=None,
                         choices=[None, "", "instance", "evenement", "signal"])
    parser.add_argument("--forcer-slug", default=None)
    parser.add_argument("--forcer-scenarios", nargs="+", default=None,
                         help="'tous', ou une liste de scénarios séparés par des espaces "
                              "(le GUI envoie --forcer-scenarios breakdown policy_reform en tokens "
                              "séparés, pas une chaîne à virgules -- voir app.js/collectArgs, "
                              "corrigé le 2 août 2026 après lecture du vrai app.js).")
    parser.add_argument("--forcer-zone", nargs="+", default=None)
    # Champs partagés / semi_guide -- ajoutés le 2 août 2026, voir docstring.
    parser.add_argument("--thematique", default=None)
    parser.add_argument("--ligne-editoriale", default=None)
    parser.add_argument("--article-longueur", default=None)
    parser.add_argument("--article-angle-specifique", default=None)
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--zone-slug", default=None)
    parser.add_argument("--article-titre-suggere", default=None)
    args, _ = parser.parse_known_args()
    return args


# ─────────────────────────────────────────
# CHEMINS
# ─────────────────────────────────────────

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")


# Dates fictives 2098 — même liste que generate_series.py
DATES_2098 = [
    "3 janvier 2098",   "17 janvier 2098",
    "2 février 2098",   "19 février 2098",
    "8 mars 2098",      "24 mars 2098",
    "5 avril 2098",     "21 avril 2098",
    "10 mai 2098",      "27 mai 2098",
    "4 juin 2098",      "19 juin 2098",
    "7 juillet 2098",   "23 juillet 2098",
    "6 août 2098",      "22 août 2098",
    "4 septembre 2098", "20 septembre 2098",
    "3 octobre 2098",   "18 octobre 2098",
]


# ─────────────────────────────────────────
# CHARGEMENT CONFIG
# ─────────────────────────────────────────

def load_config():
    """Charge config.yaml (validation minimale -- validate_config() fait
    le reste, différemment selon le mode)."""
    if not os.path.exists(CONFIG_PATH):
        print("[erreur] config.yaml introuvable : {}".format(CONFIG_PATH))
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config.get("thematique"):
        print("[erreur] 'thematique' est requis dans config.yaml")
        sys.exit(1)

    return config


# ─────────────────────────────────────────
# VALIDATION DES SLUGS
# ─────────────────────────────────────────

VALID_THEMATIQUES = [
    "actualites_a_la_une", "politique", "economie_finance",
    "environnement_climat", "sciences_technologies", "societe",
    "culture", "international", "musique", "sports", "faits_divers",
    "opinions_editoriaux", "lifestyle_art_de_vivre", "sante",
    "education", "histoire_patrimoine", "medias_communication",
    "religion_spiritualite", "petites_annonces_services", "meteo",
]


def validate_config_semi_guide(config):
    """Vérifie que les slugs existent dans les listes autorisées --
    validation historique, inchangée, pour le mode semi_guide."""
    from loader import VALID_SCENARIOS

    errors = []

    scenario = config.get("scenario", "")
    if scenario not in VALID_SCENARIOS:
        errors.append("Scénario invalide : '{}'. Valides : {}".format(
            scenario, ", ".join(VALID_SCENARIOS)))

    thematique = config.get("thematique", "")
    if thematique not in VALID_THEMATIQUES:
        errors.append("Thématique invalide : '{}'. Valides : {}".format(
            thematique, ", ".join(VALID_THEMATIQUES)))

    # zone_slug (optionnel) — si fixé manuellement, doit exister dans
    # journaux.yaml pour ce scénario/cette ligne éditoriale, sinon la
    # résolution du journal échoue silencieusement vers un mauvais profil
    # (bug #26, 11 juillet 2026 — zone_slug typo résolu vers une zone alliée
    # sans rapport avec l'article, via le fallback réseau global/dominant_zone).
    zone_slug = config.get("zone_slug")
    if zone_slug and scenario in VALID_SCENARIOS:
        from prompt_builder import _load_journaux
        journaux = _load_journaux()
        ligne = config.get("ligne_editoriale") or "pro_pouvoir"
        zones_dispo = journaux.get(scenario, {}).get(ligne, {}).get("zones", {})
        if zones_dispo and zone_slug not in zones_dispo:
            errors.append(
                "zone_slug invalide : '{}' n'existe pas dans journaux.yaml pour "
                "{}/{}.\n    Zones valides : {}".format(
                    zone_slug, scenario, ligne, ", ".join(sorted(zones_dispo.keys()))
                )
            )

    if errors:
        print("[erreur] Valeurs invalides dans config.yaml :")
        for e in errors:
            print("  - {}".format(e))
        sys.exit(1)


def validate_config_forcer(config, forcer_config):
    """Validation allégée pour le mode forcer -- pas de 'scenario' unique
    à valider (une liste est résolue plus loin), pas de zone_slug fixe
    (chaque article de la boucle utilise la zone propre à l'élément dans
    son scénario)."""
    thematique = config.get("thematique", "")
    if thematique not in VALID_THEMATIQUES:
        print("[erreur] Thématique invalide : '{}'. Valides : {}".format(
            thematique, ", ".join(VALID_THEMATIQUES)))
        sys.exit(1)

    if not forcer_config.get("type") or not forcer_config.get("slug"):
        print("[erreur] Mode 'forcer' sélectionné mais aucun élément choisi "
              "(forcer.type/forcer.slug requis).")
        sys.exit(1)


# ─────────────────────────────────────────
# AFFICHAGE
# ─────────────────────────────────────────

def print_header(config, mode, forcer_config=None):
    print("\n" + "="*60)
    print("OURRASSOL 2098 — Générateur d'articles")
    print("="*60)
    print("  Mode       : {}".format(
        "Forcer un élément" if mode == "forcer" else "Semi-guidé"))
    if mode == "forcer" and forcer_config:
        print("  Élément    : {} ({})".format(forcer_config.get("slug"), forcer_config.get("type")))
    else:
        print("  Scénario   : {}".format(config.get("scenario")))
    print("  Thématique : {}".format(config["thematique"]))
    longueur = config.get("article", {}).get("longueur", "breve")
    print("  Longueur   : {}".format(longueur))
    if mode == "forcer":
        # L'angle est toujours généré automatiquement en mode forcer
        # (forced_angle_directive écrase systématiquement config["article"]
        # ["angle_specifique"] dans prompt_builder.py) -- ne jamais afficher
        # une valeur résiduelle de ce champ ici, ça laisserait croire
        # qu'elle est prise en compte alors qu'elle ne l'est jamais dans
        # ce mode. Corrigé le 2 août 2026 (retour de David : un angle
        # d'un test précédent, laissé dans le champ car masqué mais pas
        # vidé, s'affichait comme si actif).
        print("  Angle      : (généré automatiquement autour de l'élément forcé)")
    else:
        angle = config.get("article", {}).get("angle_specifique", "")
        if angle:
            print("  Angle      : {}".format(angle))
        titre = config.get("article", {}).get("titre_suggere", "")
        if titre:
            print("  Titre      : {}".format(titre))
    print("="*60)


def print_footer(result):
    print("\n" + "="*60)
    print("ARTICLE GÉNÉRÉ")
    print("="*60)
    print(result["article"])
    print("\n" + "="*60)
    print("✓ Sauvegardé : {}".format(result["filepath"]))
    print("="*60 + "\n")


# ─────────────────────────────────────────
# GÉNÉRATION D'UN ARTICLE (une paire scénario × thématique)
# ─────────────────────────────────────────

def _generate_one(scenario_slug, thematique_obj, thematique_slug, config,
                   forcer_config, dry_run):
    """
    Construit le snapshot + prompt + (sauf dry-run) génère et sauvegarde
    UN article pour ce scénario précis. Factorisé le 2 août 2026 pour
    être appelable en boucle par le mode "forcer" (un article par
    scénario retenu) sans dupliquer toute la logique.

    Retourne un dict {"scenario": ..., "result": {...}, "erreur": str|None}.
    """
    from snapshot       import build_snapshot
    from prompt_builder import build_prompt

    snapshot = build_snapshot(scenario_slug, thematique=thematique_obj,
                               dry_run=dry_run, forcer_config=forcer_config)

    if snapshot.get("forcer_erreur"):
        return {"scenario": scenario_slug, "result": None, "erreur": snapshot["forcer_erreur"]}

    article_config = dict(config)
    article_config["scenario"] = scenario_slug
    article_config["article"] = dict(config.get("article") or {})
    if not article_config["article"].get("date_fictive"):
        article_config["article"]["date_fictive"] = random.choice(DATES_2098)

    prompt_data = build_prompt(snapshot, thematique_obj, article_config, dry_run=dry_run)

    if dry_run:
        print("\n--- [{}] SYSTEM PROMPT ---".format(scenario_slug))
        print(prompt_data["system_prompt"])
        print("\n--- [{}] USER PROMPT (complet) ---".format(scenario_slug))
        print(prompt_data["user_prompt"])
        print("\n--- [{}] MÉTADONNÉES ---".format(scenario_slug))
        for k, v in prompt_data["metadata"].items():
            print("  {} : {}".format(k, v))
        return {"scenario": scenario_slug, "result": {"article": "", "filepath": ""}, "erreur": None}

    from api import generate_article
    result = generate_article(prompt_data, snapshot, thematique_obj, article_config)
    return {"scenario": scenario_slug, "result": result, "erreur": None}


# ─────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────

def run():
    """Pipeline complet de génération -- se ramifie en deux modes juste
    après le chargement de la config (voir docstring du module)."""

    config = load_config()
    cli_args = _parse_cli_args()
    dry_run = cli_args.dry_run

    # Application des flags CLI (GUI) sur la config chargée -- corrige le
    # bug du 2 août 2026 (voir docstring de _parse_cli_args) : CLI
    # prioritaire sur config.yaml quand le flag est explicitement fourni
    # (None = non précisé côté CLI, on garde alors la valeur de
    # config.yaml -- utile pour un lancement en CLI direct sans passer
    # par le GUI, qui envoie toujours tous les flags).
    config = dict(config)
    config["article"] = dict(config.get("article") or {})
    if cli_args.thematique is not None:
        config["thematique"] = cli_args.thematique
    if cli_args.ligne_editoriale is not None:
        config["ligne_editoriale"] = cli_args.ligne_editoriale
    if cli_args.scenario is not None:
        config["scenario"] = cli_args.scenario
    if cli_args.zone_slug is not None:
        config["zone_slug"] = cli_args.zone_slug
    if cli_args.article_longueur is not None:
        config["article"]["longueur"] = cli_args.article_longueur
    if cli_args.article_angle_specifique is not None:
        config["article"]["angle_specifique"] = cli_args.article_angle_specifique
    if cli_args.article_titre_suggere is not None:
        config["article"]["titre_suggere"] = cli_args.article_titre_suggere

    mode = cli_args.mode or config.get("mode_generation") or "semi_guide"
    if mode not in ("semi_guide", "forcer"):
        mode = "semi_guide"

    from loader import load_thematique, VALID_SCENARIOS

    # ═══════════════════════════════════════════════════════════════
    # MODE SEMI-GUIDÉ — comportement historique, inchangé
    # ═══════════════════════════════════════════════════════════════
    if mode == "semi_guide":
        print_header(config, mode)
        validate_config_semi_guide(config)

        scenario_slug   = config["scenario"]
        thematique_slug = config["thematique"]

        print("\n[generate] Chargement de la thématique '{}'...".format(thematique_slug))
        thematique = load_thematique(thematique_slug)

        # Pas de forçage en semi_guide -- forcer_config=None
        res = _generate_one(scenario_slug, thematique, thematique_slug, config,
                             forcer_config=None, dry_run=dry_run)

        if res["erreur"]:
            print("\n[erreur] {}".format(res["erreur"]))
            sys.exit(1)

        if dry_run:
            print("\n✓ Pipeline complet — prêt pour l'API")
            return res["result"]

        print_footer(res["result"])
        return res["result"]

    # ═══════════════════════════════════════════════════════════════
    # MODE FORCER — un élément, un ou plusieurs scénarios, un article
    # sauvegardé par scénario retenu
    # ═══════════════════════════════════════════════════════════════
    from loader import resolve_forced_element, scenarios_disponibles_pour_element, zones_disponibles_pour_element

    forcer_config = dict(config.get("forcer") or {})
    if cli_args.forcer_type is not None:
        forcer_config["type"] = cli_args.forcer_type or None
    if cli_args.forcer_slug is not None:
        forcer_config["slug"] = cli_args.forcer_slug or None
    # Mode "sujet_central" toujours, dans cette architecture -- pas de
    # variante "ingrédient" en mode forcer (voir docstring du module).
    forcer_config["mode"] = "sujet_central"

    # Titre suggéré : jamais éditable en mode forcer, l'IA choisit
    # systématiquement -- écrase toute valeur résiduelle de config.yaml.
    config = dict(config)
    config["article"] = dict(config.get("article") or {})
    config["article"]["titre_suggere"] = ""

    validate_config_forcer(config, forcer_config)
    print_header(config, mode, forcer_config)

    thematique_slug = config["thematique"]
    print("\n[generate] Chargement de la thématique '{}'...".format(thematique_slug))
    thematique = load_thematique(thematique_slug)

    # Résolution de la liste de scénarios à traiter
    disponibles = scenarios_disponibles_pour_element(forcer_config["type"], forcer_config["slug"])
    if not disponibles:
        print("\n[erreur] L'élément {!r} ({}) n'est disponible dans aucun scénario.".format(
            forcer_config["slug"], forcer_config["type"]))
        sys.exit(1)

    # --forcer-scenarios arrive en liste depuis le GUI (chips, plusieurs
    # tokens argparse nargs="+") ; peut aussi être une chaîne si fixé à la
    # main dans config.yaml (forcer_scenarios: "breakdown,policy_reform")
    # -- normalisé en liste dans les deux cas.
    if cli_args.forcer_scenarios is not None:
        demande_liste = cli_args.forcer_scenarios
    # Zone(s) demandée(s) -- une zone appartient à UN SEUL scénario, elle
    # est donc plus précise qu'un choix de scénario. Réécrit le 2 août
    # 2026 (retour de David, après un cas réel bloqué en "ET" : scénario
    # coché différent de celui qui contient réellement la zone cochée,
    # résultat impossible). La zone REMPLACE maintenant le choix de
    # scénario au lieu de le filtrer -- le menu Scénarios devient sans
    # effet dès qu'une zone précise est cochée.
    zones_demandees = cli_args.forcer_zone or []
    zones_demandees = [z for z in zones_demandees if z and z.lower() != "tous"]

    if zones_demandees:
        zones_par_scenario = zones_disponibles_pour_element(
            forcer_config["type"], forcer_config["slug"], disponibles
        )
        scenarios_a_traiter = [
            sc for sc in disponibles
            if any(z in zones_demandees for z in zones_par_scenario.get(sc, []))
        ]
        if not scenarios_a_traiter:
            print("\n[erreur] Aucun scénario où {!r} a la zone {} parmi {}.".format(
                forcer_config["slug"], zones_demandees, ", ".join(disponibles)))
            sys.exit(1)
        print("[generate] Zone(s) {} -> {} scénario(s) déterminé(s) directement (choix Scénarios ignoré) : {}".format(
            zones_demandees, len(scenarios_a_traiter), ", ".join(scenarios_a_traiter)))

    else:
        # Pas de zone précise demandée -- le choix de scénarios s'applique
        # normalement (comportement inchangé).
        if cli_args.forcer_scenarios is not None:
            demande_liste = cli_args.forcer_scenarios
        else:
            brut = config.get("forcer_scenarios") or "tous"
            demande_liste = [s.strip() for s in str(brut).split(",") if s.strip()]

        # "tous" prioritaire s'il apparaît, même mélangé à d'autres chips
        # sélectionnées par erreur (les chips n'empêchent pas techniquement
        # de cocher "tous" ET un scénario précis en même temps).
        if not demande_liste or any(s.lower() == "tous" for s in demande_liste):
            scenarios_a_traiter = disponibles
        else:
            invalides = [s for s in demande_liste if s not in disponibles]
            if invalides:
                print("\n[erreur] Scénario(s) demandé(s) indisponible(s) pour {!r} : {}".format(
                    forcer_config["slug"], ", ".join(invalides)))
                print("  Disponibles pour cet élément : {}".format(", ".join(disponibles)))
                sys.exit(1)
            scenarios_a_traiter = demande_liste

    print("\n[generate] Mode forcer — {} scénario(s) à traiter : {}".format(
        len(scenarios_a_traiter), ", ".join(scenarios_a_traiter)))

    # Zone réelle de l'élément forcé, par scénario -- corrige un bug
    # trouvé le 2 août 2026 (retour de David) : la directive "ancré
    # géographiquement dans la zone X" du prompt se basait uniquement sur
    # snapshot["zone_slug"] = _dominant_zone(filtered_instances), calculée
    # à partir des 6 instances auto-sélectionnées GÉNÉRIQUES -- totalement
    # indépendantes de l'élément forcé. Ça fonctionnait par coïncidence
    # pour une instance forcée (filtered_instances devient [l'instance
    # forcée] seule en mode sujet_central, donc sa zone devient
    # "dominante" par construction), mais pas pour un événement forcé
    # (jamais inclus dans filtered_instances). Résultat observé : article
    # sur un événement au Moyen-Orient, mais ancré géographiquement à
    # Genève -- la zone d'une entité totalement sans rapport, auto-
    # sélectionnée par ailleurs. Corrigé en injectant explicitement la
    # vraie zone de l'élément forcé dans config["zone_slug"] pour chaque
    # scénario traité, plutôt que de compter sur ce calcul générique.
    zones_par_scenario_forcees = zones_disponibles_pour_element(
        forcer_config["type"], forcer_config["slug"], scenarios_a_traiter
    )

    resultats = []
    for scenario_slug in scenarios_a_traiter:
        print("\n" + "-"*60)
        print("[generate] → {}".format(scenario_slug))
        print("-"*60)
        config_scenario = dict(config)
        zones_ici = zones_par_scenario_forcees.get(scenario_slug) or []
        if zones_ici:
            config_scenario["zone_slug"] = zones_ici[0]
            print("[generate] Zone d'ancrage pour {} : {}".format(scenario_slug, zones_ici[0]))
        res = _generate_one(scenario_slug, thematique, thematique_slug, config_scenario,
                             forcer_config=forcer_config, dry_run=dry_run)
        resultats.append(res)
        if res["erreur"]:
            print("[erreur] {} : {}".format(scenario_slug, res["erreur"]))
        elif not dry_run:
            print_footer(res["result"])

    # ── Résumé du lot
    ok      = [r for r in resultats if not r["erreur"]]
    echecs  = [r for r in resultats if r["erreur"]]
    print("\n" + "="*60)
    print("RÉSUMÉ DU LOT — mode forcer")
    print("="*60)
    print("  Réussis : {}".format(len(ok)))
    for r in ok:
        if not dry_run:
            print("    ✓ {} → {}".format(r["scenario"], r["result"]["filepath"]))
        else:
            print("    ✓ {} (dry-run, rien écrit)".format(r["scenario"]))
    if echecs:
        print("  Échecs  : {}".format(len(echecs)))
        for r in echecs:
            print("    ✗ {} : {}".format(r["scenario"], r["erreur"]))
    print("="*60 + "\n")

    return resultats


# ─────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────

if __name__ == "__main__":
    run()
