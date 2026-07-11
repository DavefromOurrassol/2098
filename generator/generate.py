"""
generate.py
-----------
Point d'entrée unique du générateur d'articles Ourrassol 2098.

Usage :
    python3 generate.py

Lit config.yaml, orchestre tous les modules et sauvegarde l'article
dans le dossier articles/ du vault Obsidian.
"""

import os
import random
import sys
import yaml


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
    """Charge et valide config.yaml."""
    if not os.path.exists(CONFIG_PATH):
        print("[erreur] config.yaml introuvable : {}".format(CONFIG_PATH))
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Validation basique
    errors = []

    scenario = config.get("scenario", "")
    if not scenario:
        errors.append("'scenario' est requis dans config.yaml")

    thematique = config.get("thematique", "")
    if not thematique:
        errors.append("'thematique' est requis dans config.yaml")

    if errors:
        print("[erreur] Problèmes dans config.yaml :")
        for e in errors:
            print("  - {}".format(e))
        sys.exit(1)

    return config


# ─────────────────────────────────────────
# VALIDATION DES SLUGS
# ─────────────────────────────────────────

def validate_config(config):
    """Vérifie que les slugs existent dans les listes autorisées."""
    from loader import VALID_SCENARIOS, VALID_VARS

    VALID_THEMATIQUES = [
        "actualites_a_la_une", "politique", "economie_finance",
        "environnement_climat", "sciences_technologies", "societe",
        "culture", "international", "musique", "sports", "faits_divers",
        "opinions_editoriaux", "lifestyle_art_de_vivre", "sante",
        "education", "histoire_patrimoine", "medias_communication",
        "religion_spiritualite", "petites_annonces_services", "meteo",
    ]

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


# ─────────────────────────────────────────
# AFFICHAGE RÉSUMÉ
# ─────────────────────────────────────────

def print_header(config):
    print("\n" + "="*60)
    print("OURRASSOL 2098 — Générateur d'articles")
    print("="*60)
    print("  Scénario   : {}".format(config["scenario"]))
    print("  Thématique : {}".format(config["thematique"]))
    longueur = config.get("article", {}).get("longueur", "breve")
    print("  Longueur   : {}".format(longueur))
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
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────

def run():
    """Pipeline complet de génération."""

    # ── 1. Config
    config     = load_config()
    print_header(config)

    # ── 2. Imports (après validation du chemin)
    from loader         import load_thematique
    from snapshot       import build_snapshot
    from prompt_builder import build_prompt

    # ── 3. Validation
    validate_config(config)

    scenario_slug   = config["scenario"]
    thematique_slug = config["thematique"]

    # ── 4. Chargement thématique
    print("\n[generate] Chargement de la thématique '{}'...".format(thematique_slug))
    thematique = load_thematique(thematique_slug)

    # ── 5. Construction du snapshot
    snapshot = build_snapshot(scenario_slug, thematique=thematique)

    # ── 6. Assemblage du prompt
    dry_run = "--dry-run" in sys.argv

    # Injecter une date fictive aléatoire si non définie dans config.yaml
    if not config.get("article", {}).get("date_fictive"):
        config.setdefault("article", {})["date_fictive"] = random.choice(DATES_2098)

    prompt_data = build_prompt(snapshot, thematique, config, dry_run=dry_run)

    # ── 7. Génération et sauvegarde
    if dry_run:
        print("\n[generate] MODE DRY-RUN — pas d'appel API")
        print("\n--- SYSTEM PROMPT ---")
        print(prompt_data["system_prompt"])
        print("\n--- USER PROMPT (complet) ---")
        print(prompt_data["user_prompt"])
        print("\n--- MÉTADONNÉES ---")
        for k, v in prompt_data["metadata"].items():
            print("  {} : {}".format(k, v))
        print("\n✓ Pipeline complet — prêt pour l'API")
        return {"article": "", "filepath": ""}

    from api import generate_article
    result = generate_article(prompt_data, snapshot, thematique, config)

    # ── 8. Affichage
    print_footer(result)

    return result


# ─────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────

if __name__ == "__main__":
    run()
