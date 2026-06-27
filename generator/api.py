"""
api.py
------
Envoie le prompt à l'API Claude et sauvegarde l'article généré.

Reçoit :
  - prompt_data : dict construit par prompt_builder.py
  - snapshot    : dict construit par snapshot.py
  - config      : dict depuis config.yaml

Retourne :
  - article     : str — texte de l'article généré
  - filepath    : str — chemin du fichier .md sauvegardé
"""

import os
import re
import json
from datetime import datetime

import anthropic

from loader import VAULT_PATH


# ─────────────────────────────────────────
# CONFIGURATION API
# ─────────────────────────────────────────

MODEL         = "claude-sonnet-4-6"
MAX_TOKENS    = 4000
TEMPERATURE   = 1.0   # Créativité maximale pour la rédaction

# Dossier de sortie des articles
ARTICLES_DIR  = os.path.join(VAULT_PATH, "articles")


# ─────────────────────────────────────────
# APPEL API
# ─────────────────────────────────────────

def call_claude(prompt_data):
    """
    Envoie le prompt à l'API Claude.
    Retourne le texte de l'article généré.
    """
    client = anthropic.Anthropic()

    print("\n[api] Envoi à Claude ({})...".format(MODEL))

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=prompt_data["system_prompt"],
        messages=[
            {
                "role": "user",
                "content": prompt_data["user_prompt"]
            }
        ]
    )

    article = message.content[0].text

    # Stats
    input_tokens  = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    print("[api] Tokens — entrée : {} | sortie : {}".format(
        input_tokens, output_tokens))
    print("[api] Article généré : {} caractères".format(len(article)))

    return article


# ─────────────────────────────────────────
# SAUVEGARDE
# ─────────────────────────────────────────

def build_article_filename(snapshot, thematique, article_text):
    """
    Construit le nom du fichier de l'article.
    Format : YYYYMMDD_HHMMSS_scenario_thematique.md
    """
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    scenario   = snapshot["scenario_slug"]
    thema      = thematique.get("slug", "article")
    return "{}_{}_{}_{}.md".format(timestamp, scenario, thema, "article")


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
        "model: {}".format(MODEL),
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
        filename = build_article_filename(snapshot, thematique, article_text)
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
    Fonction principale — appelle Claude et sauvegarde l'article.

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
    # Appel API
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
