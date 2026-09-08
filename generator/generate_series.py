"""
generate_series.py
------------------
Génère une série d'articles pour un scénario donné,
sur plusieurs thématiques, avec cohérence temporelle.

Usage :
    python3 generate_series.py                    # utilise config_series.yaml
    python3 generate_series.py --dry-run          # sans appel API
    python3 generate_series.py --scenario breakdown
    python3 generate_series.py --validate-first   # valide la base avant de générer

Résultat :
    vault/articles/{scenario}/  ← articles générés
    vault/articles/{scenario}/_index.md  ← index de la série
"""

import os
import random
import sys
import yaml
import argparse
import time
from datetime import datetime

from edition_utils import edition_date_to_float, tirer_jour_edition, enregistrer_edition, lire_edition_active

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH  = "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098"
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config_series.yaml")

VALID_SCENARIOS = [
    "fortress_world", "new_sustainability", "breakdown",
    "eco_communalism", "policy_reform", "reference"
]

VALID_THEMATIQUES = [
    "actualites_a_la_une", "politique", "economie_finance",
    "environnement_climat", "sciences_technologies", "societe",
    "culture", "international", "musique", "sports", "faits_divers",
    "opinions_editoriaux", "lifestyle_art_de_vivre", "sante",
    "education", "histoire_patrimoine", "medias_communication",
    "religion_spiritualite", "petites_annonces_services", "meteo",
]

# ─────────────────────────────────────────
# CHARGEMENT CONFIG
# ─────────────────────────────────────────

def load_config():
    """Charge config_series.yaml."""
    if not os.path.exists(CONFIG_PATH):
        print("[erreur] config_series.yaml introuvable : {}".format(CONFIG_PATH))
        print("  Créez-le ou utilisez --scenario et --thematiques")
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config or {}


def validate_config(config):
    """Valide la configuration de la série."""
    errors = []

    scenario = config.get("scenario", "")
    if not scenario:
        errors.append("'scenario' requis dans config_series.yaml")
    elif scenario not in VALID_SCENARIOS:
        errors.append("Scénario invalide : '{}'".format(scenario))

    thematiques = config.get("thematiques", [])
    if not thematiques:
        errors.append("'thematiques' requis (liste non vide)")
    else:
        for t in thematiques:
            if t not in VALID_THEMATIQUES:
                errors.append("Thématique invalide : '{}'".format(t))

    # Ajouté le 2 septembre 2026 (chantier "Éditions datées"), assoupli
    # le même jour à la demande de David : annee_edition/mois_edition
    # sont désormais OPTIONNELS ici -- s'ils sont absents, run() se
    # replie sur l'édition active (state/editions.json, configurable
    # indépendamment via definir_edition.py). S'ils sont présents,
    # validés normalement (permet de surcharger ponctuellement l'édition
    # active pour un lot précis, sans y toucher globalement). Erreur
    # seulement si un seul des deux est fourni (ambigu) ou si mois_edition
    # est hors plage.
    annee_edition = config.get("annee_edition")
    mois_edition  = config.get("mois_edition")
    if bool(annee_edition) != bool(mois_edition):
        errors.append("'annee_edition' et 'mois_edition' doivent être fournis ensemble, "
                       "ou tous les deux absents pour utiliser l'édition active")
    elif mois_edition and not (1 <= int(mois_edition) <= 12):
        errors.append("'mois_edition' hors plage [1-12] : {!r}".format(mois_edition))

    if errors:
        print("[erreur] Problèmes dans config_series.yaml :")
        for e in errors:
            print("  - {}".format(e))
        sys.exit(1)


# ─────────────────────────────────────────
# AFFICHAGE
# ─────────────────────────────────────────

def print_header(config):
    print("\n" + "="*60)
    print("OURRASSOL 2098 — Génération de série")
    print("="*60)
    print("  Scénario     : {}".format(config["scenario"]))
    print("  Thématiques  : {}".format(len(config["thematiques"])))
    for t in config["thematiques"]:
        print("    - {}".format(t))
    print("  Articles/th. : {}".format(config.get("articles_par_thematique", 1)))
    longueur = config.get("longueur", "auto")
    print("  Longueur     : {}".format(longueur))
    print("="*60)


def print_footer(results, output_dir):
    success  = sum(1 for r in results if r["status"] in ("ok", "dry-run"))
    errors   = sum(1 for r in results if r["status"] == "error")
    dry_runs = sum(1 for r in results if r["status"] == "dry-run")

    print("\n" + "="*60)
    print("SÉRIE GÉNÉRÉE")
    if dry_runs:
        print("  ✓ {} prompts assemblés (dry-run) | ✗ {} erreurs".format(
            dry_runs, errors))
    else:
        print("  ✓ {} articles | ✗ {} erreurs".format(success, errors))
    print("  📁 {}".format(output_dir))
    print("="*60)


# ─────────────────────────────────────────
# INDEX DE LA SÉRIE
# ─────────────────────────────────────────

def build_index(config, results, output_dir):
    """Génère un fichier index markdown de la série."""
    scenario   = config["scenario"]
    now        = datetime.now().strftime("%Y-%m-%d %H:%M")
    success    = [r for r in results if r["status"] == "ok"]

    lines = [
        "---",
        "type: article_series_index",
        "scenario: {}".format(scenario),
        "date_generation: {}".format(now),
        "total_articles: {}".format(len(success)),
        "---",
        "",
        "# Index de la série — {} — 2098".format(scenario.upper()),
        "",
        "Généré le {} | {} articles".format(now, len(success)),
        "",
        "## Articles",
        "",
    ]

    for i, r in enumerate(success, 1):
        lines.append("{}. [[{}]] — *{}*".format(
            i,
            os.path.basename(r["filepath"]).replace(".md", ""),
            r["thematique"]
        ))

    index_path = os.path.join(output_dir, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return index_path


# ─────────────────────────────────────────
# GÉNÉRATION D'UN ARTICLE
# ─────────────────────────────────────────

def generate_one(scenario, thematique, config, date_fictive, date_edition, dry_run=False):
    """
    Génère un article pour un scénario + thématique donnés.
    Retourne un dict de résultat.
    """
    from loader         import load_thematique
    from snapshot       import build_snapshot
    from prompt_builder import build_prompt

    # Ligne éditoriale : fixe si définie dans config, aléatoire sinon
    ligne_editoriale_config = config.get("ligne_editoriale", None)
    if ligne_editoriale_config in ("pro_pouvoir", "opposition"):
        ligne_editoriale = ligne_editoriale_config
    else:
        ligne_editoriale = random.choice(["pro_pouvoir", "opposition"])

    # P20 Phase C (21 août 2026) : politique de décision a_une_photo pour
    # une série -- décidée par article, pas globalement pour toute la
    # série (contrairement à ligne_editoriale ci-dessus, qui peut être
    # fixe pour toute la série). Trois valeurs pour "photo_policy" :
    # "toutes" / "aucune" / "aleatoire" (25%, probabilité actée avec
    # David le 21 août 2026). Défaut "aucune" -- comportement historique
    # préservé si photo_policy est absent de config_series.yaml (fichiers
    # de config antérieurs à ce chantier).
    photo_policy = config.get("photo_policy", "aucune")
    if photo_policy == "toutes":
        a_une_photo = True
    elif photo_policy == "aleatoire":
        a_une_photo = random.random() < 0.25
    else:
        a_une_photo = False

    # Config article pour cette entrée
    article_config = {
        "scenario":          scenario,
        "thematique":        thematique,
        "ligne_editoriale":  ligne_editoriale,
        "article": {
            "titre_suggere":    "",
            "angle_specifique": config.get("angle_specifique", ""),
            "longueur":         config.get("longueur", "breve"),
            "date_fictive":     date_fictive,
            "a_une_photo":      a_une_photo,
            # image_credit intentionnellement absent -- reste vide
            # (défaut de build_article_md côté api.py), décision de
            # David le 21 août 2026 : la source se choisit plus tard,
            # par article, avant de lancer generate_images.py -- pas de
            # valeur automatique assignée en série.
        },
        "output": {
            "dossier":     os.path.join("articles", scenario),
            "nom_fichier": "auto",
        },
        "injections": config.get("injections", []),
    }

    try:
        thema_data  = load_thematique(thematique)
        forcer_config = config.get("forcer")
        snapshot    = build_snapshot(scenario, thematique=thema_data, dry_run=dry_run,
                                      forcer_config=forcer_config, date_edition=date_edition)
        if snapshot.get("forcer_erreur"):
            return {"status": "error", "scenario": scenario, "thematique": thematique,
                    "error": "Forçage impossible : {}".format(snapshot["forcer_erreur"])}
        prompt_data = build_prompt(snapshot, thema_data, article_config, dry_run=dry_run)

        if dry_run:
            # Mode dry-run : afficher le prompt sans appeler l'API
            print("\n[dry-run] Prompt assemblé pour {} × {}".format(
                scenario, thematique))
            print("  User prompt : {} caractères".format(
                len(prompt_data["user_prompt"])))
            return {
                "status":     "dry-run",
                "scenario":   scenario,
                "thematique": thematique,
                "filepath":   "",
                "prompt":     prompt_data,
            }

        from api import generate_article
        result = generate_article(prompt_data, snapshot, thema_data, article_config)
        return {
            "status":     "ok",
            "scenario":   scenario,
            "thematique": thematique,
            "filepath":   result["filepath"],
        }

    except Exception as e:
        print("  ✗ Erreur : {}".format(e))
        return {
            "status":     "error",
            "scenario":   scenario,
            "thematique": thematique,
            "filepath":   "",
            "error":      str(e),
        }


# ─────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────

def run(config, dry_run=False, validate_first=False):
    """Pipeline de génération de la série."""

    print_header(config)

    scenario    = config["scenario"]
    thematiques = config["thematiques"]
    n_per_thema = config.get("articles_par_thematique", 1)

    # Validation préalable
    if validate_first:
        print("\n[series] Validation de la base...")
        import validate as val_module
        val_result = val_module.run(verbose=False)
        if not val_result.ok:
            print("[series] ✗ Base invalide — génération annulée.")
            print("  Lancez 'python3 validate.py -v' pour le détail.")
            sys.exit(1)
        print("[series] ✓ Base valide")

    # Préparer le dossier de sortie
    output_dir = os.path.join(VAULT_PATH, "articles", scenario)
    os.makedirs(output_dir, exist_ok=True)

    # Édition active de cette série (2 septembre 2026, chantier "Éditions
    # datées") : un seul mois pour tout le lot -- date_reference partagée
    # par tous les articles (point 2), jour de rédaction tiré à la volée
    # pour chacun, dans ce même mois (remplace le cyclage sur DATES_2098).
    # Assoupli le même jour : si config_series.yaml ne précise pas
    # annee_edition/mois_edition, on se replie sur l'édition active
    # (definir_edition.py) plutôt que d'exiger une saisie explicite à
    # chaque série -- config_series.yaml reste utilisable pour surcharger
    # ponctuellement (lot sur une édition différente de l'active).
    if config.get("annee_edition") and config.get("mois_edition"):
        annee_edition = int(config["annee_edition"])
        mois_edition  = int(config["mois_edition"])
    else:
        edition_active = lire_edition_active()
        if not edition_active:
            print("[erreur] Aucun mois de parution défini et annee_edition/mois_edition absents "
                  "de config_series.yaml.")
            print("  Configurez d'abord un mois de parution : python3 definir_edition.py --annee 2098 --mois 8")
            sys.exit(1)
        annee_edition = edition_active["annee"]
        mois_edition  = edition_active["mois"]
    date_edition  = edition_date_to_float(annee_edition, mois_edition)
    print("[series] Mois de parution : {}/{:02d} (date de référence {})".format(
        annee_edition, mois_edition, date_edition
    ))

    # Construire la liste des articles à générer
    tasks = []
    for thematique in thematiques:
        for _ in range(n_per_thema):
            date_fictive = tirer_jour_edition(annee_edition, mois_edition)
            tasks.append((thematique, date_fictive))

    print("\n[series] {} articles à générer...".format(len(tasks)))

    results = []
    for i, (thematique, date_fictive) in enumerate(tasks, 1):
        print("\n[{}/{}] {} × {} — {}".format(
            i, len(tasks), scenario, thematique, date_fictive
        ))

        result = generate_one(
            scenario, thematique, config, date_fictive, date_edition, dry_run=dry_run
        )
        results.append(result)

        if result["status"] == "ok":
            print("  ✓ Sauvegardé : {}".format(
                os.path.basename(result["filepath"])
            ))
        elif result["status"] == "dry-run":
            print("  ✓ Prompt prêt (dry-run)")

        # Pause pour éviter le rate limiting
        if not dry_run and i < len(tasks):
            time.sleep(1)

    # Générer l'index
    if not dry_run:
        index_path = build_index(config, results, output_dir)
        print("\n[series] Index généré : {}".format(
            os.path.basename(index_path)
        ))

        # Enregistrement dans le registre d'éditions (2 septembre 2026) --
        # seuls les articles réellement sauvegardés comptent (jamais en
        # dry-run). generate_series.py fait partie des deux seuls points
        # d'entrée autorisés à créer/avancer une édition (voir
        # edition_utils.py) -- generate.py ne fait que la lire.
        nb_reussis = sum(1 for r in results if r["status"] == "ok")
        if nb_reussis:
            numero = enregistrer_edition(scenario, annee_edition, mois_edition, nb_articles=nb_reussis)
            print("[series] Mois de parution n°{} mis à jour ({} article(s) ajouté(s))".format(
                numero, nb_reussis
            ))

    print_footer(results, output_dir)
    return results


# ─────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Génère une série d'articles pour Ourrassol 2098"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Assemble les prompts sans appeler l'API"
    )
    parser.add_argument(
        "--validate-first",
        action="store_true",
        help="Valide la base avant de générer"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        choices=VALID_SCENARIOS,
        help="Override le scénario de config_series.yaml"
    )

    args = parser.parse_args()

    # Charger et valider la config
    config = load_config()

    # Override depuis les arguments
    if args.scenario:
        config["scenario"] = args.scenario

    validate_config(config)

    # Lancer la génération
    run(
        config,
        dry_run=args.dry_run,
        validate_first=args.validate_first,
    )
