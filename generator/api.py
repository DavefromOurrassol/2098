"""
api.py
------
Envoie le prompt au LLM configuré et sauvegarde l'article généré.

Reçoit :
  - prompt_data : dict construit par prompt_builder.py
  - snapshot    : dict construit par snapshot.py
  - config      : dict depuis config.yaml

Retourne :
  - article     : str — texte de l'article généré
  - filepath    : str — chemin du fichier .md sauvegardé

Fournisseur actif : résolu via le tier "strict" (llm_client.TASK_TIER_DEFAULTS),
sauf override manuel LLM_PROVIDER/LLM_MODEL.
"""

import os
import re
import json
from datetime import datetime

from llm_client import call_llm, resolve_for_tier
from loader import VAULT_PATH


# ─────────────────────────────────────────
# CONFIGURATION API
# ─────────────────────────────────────────

MAX_TOKENS    = 4000
TEMPERATURE   = 1.0   # Créativité maximale pour la rédaction

# Tier LLM pour la rédaction d'articles : identité journal + journaliste
# imposée sur une sortie longue et créative — voir llm_client.TASK_TIER_DEFAULTS.
TASK_TIER     = "strict"

# Dossier de sortie des articles
ARTICLES_DIR  = os.path.join(VAULT_PATH, "articles")


# ─────────────────────────────────────────
# APPEL API
# ─────────────────────────────────────────

def call_claude(prompt_data):
    """
    Envoie le prompt au LLM configuré.
    Retourne le texte de l'article généré.
    """
    provider, model = resolve_for_tier(TASK_TIER)
    print("\n[api] Envoi au LLM ({} — {}, tier={})...".format(provider, model, TASK_TIER))

    article = call_llm(
        system_prompt=prompt_data["system_prompt"],
        user_prompt=prompt_data["user_prompt"],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        task_tier=TASK_TIER,
    )

    print("[api] Article généré : {} caractères".format(len(article)))

    return article


# ─────────────────────────────────────────
# SAUVEGARDE
# ─────────────────────────────────────────

def build_article_filename(snapshot, thematique, article_text, date_fictive=None):
    """
    Construit le nom du fichier de l'article.
    Format : YYYYMMDD_HHMMSS_scenario_thematique_article_datefictive.md
    """
    import re
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    scenario   = snapshot["scenario_slug"]
    thema      = thematique.get("slug", "article")
    # Normaliser la date fictive : "3 janvier 2098" → "3janvier2098"
    if date_fictive:
        date_slug = re.sub(r"\s+", "", date_fictive.lower())
        date_slug = re.sub(r"[^a-z0-9]", "", date_slug)
    else:
        date_slug = ""
    suffix = "_{}".format(date_slug) if date_slug else ""
    return "{}_{}_{}_article{}.md".format(timestamp, scenario, thema, suffix)


def build_article_md(article_text, snapshot, thematique, prompt_data):
    """
    Construit le fichier .md final avec frontmatter + article.
    Inclut les métadonnées de génération pour traçabilité.
    """
    meta = prompt_data["metadata"]
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Frontmatter YAML
    frontmatter_lines = [
        "---",
        "type: generated_article",
        "date_generation: {}".format(now),
        "scenario: {}".format(meta["scenario"]),
        "thematique: {}".format(meta["thematique"]),
        "format: {}".format(meta["format"]),
        "longueur: {}".format(meta["longueur"]),
        "model: {}/{}".format(*resolve_for_tier(TASK_TIER)),
        "ligne_editoriale: {}".format(meta.get("ligne_editoriale", "pro_pouvoir")),
        "scenario_state: {}".format(snapshot["scenario"]["state_of_system"]),
        "tension_level: {}".format(snapshot["scenario"]["tension_level"]),
        "variables_pilotes:",
    ]
    for v in snapshot.get("pilot_variables", []):
        frontmatter_lines.append("  - {}".format(v))
    frontmatter_lines.append("---")
    frontmatter_lines.append("")

    return "\n".join(frontmatter_lines) + article_text


def save_article(article_text, snapshot, thematique, prompt_data, config):
    """
    Sauvegarde l'article dans le vault Obsidian.
    Retourne le chemin du fichier créé.
    """
    os.makedirs(ARTICLES_DIR, exist_ok=True)

    # Nom du fichier
    nom_config = config.get("output", {}).get("nom_fichier", "auto")
    if nom_config == "auto":
        date_fictive = config.get("article", {}).get("date_fictive", "")
        filename = build_article_filename(snapshot, thematique, article_text, date_fictive)
    else:
        filename = nom_config if nom_config.endswith(".md") else nom_config + ".md"

    # Contenu complet
    content = build_article_md(article_text, snapshot, thematique, prompt_data)

    filepath = os.path.join(ARTICLES_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("[api] Article sauvegardé : {}".format(filepath))
    return filepath


# ─────────────────────────────────────────
# FONCTION PRINCIPALE
# ─────────────────────────────────────────

def generate_article(prompt_data, snapshot, thematique, config):
    """
    Fonction principale — appelle le LLM et sauvegarde l'article.

    Args:
        prompt_data : dict — depuis prompt_builder.py
        snapshot    : dict — depuis snapshot.py
        thematique  : dict — depuis loader.py
        config      : dict — depuis config.yaml

    Retourne :
        {
          "article"  : str  — texte brut de l'article
          "filepath" : str  — chemin du fichier sauvegardé
        }
    """
    # Appel LLM
    article = call_claude(prompt_data)

    # Sauvegarde
    filepath = save_article(article, snapshot, thematique, prompt_data, config)

    return {
        "article":  article,
        "filepath": filepath,
    }


# ─────────────────────────────────────────
# TEST RAPIDE
# ─────────────────────────────────────────

if __name__ == "__main__":
    from loader      import load_thematique
    from snapshot    import build_snapshot
    from prompt_builder import build_prompt

    print("=== Test api.py ===\n")
    _p, _m = resolve_for_tier(TASK_TIER)
    print("Tier : {} → Fournisseur : {} | Modèle : {}".format(TASK_TIER, _p, _m))

    # Config de test
    config_test = {
        "scenario":   "breakdown",
        "thematique": "actualites_a_la_une",
        "article": {
            "titre_suggere":    "",
            "angle_specifique": "",
            "longueur":         "breve",
        },
        "output": {
            "dossier":     "articles/",
            "nom_fichier": "auto",
        }
    }

    # Pipeline complet
    thematique  = load_thematique("actualites_a_la_une")
    snapshot    = build_snapshot("breakdown", thematique=thematique)
    prompt_data = build_prompt(snapshot, thematique, config_test)

    result = generate_article(prompt_data, snapshot, thematique, config_test)

    print("\n" + "="*60)
    print("ARTICLE GÉNÉRÉ")
    print("="*60)
    print(result["article"])
    print("\n" + "="*60)
    print("Fichier : {}".format(result["filepath"]))
