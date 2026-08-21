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
import unicodedata
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

# ── Retry sur longueur hors plage (ajouté le 10 août 2026) ──
# Décision explicite avec David (chantier "dérive du LLM sur la longueur
# réelle des articles", backlog Partie 1 point 1) : le renforcement du
# prompt seul (contrainte répétée en fin de consigne) n'a pas suffi --
# taux d'incohérence mesuré à 94,4% sur un batch de test post-renforcement,
# avec un biais systématique vers le dépassement. Un seul seuil de
# déclenchement : écart <= 40% de la borne dépassée = accepté tel quel,
# pas de retry. Au-delà, UN SEUL retry, avec rappel explicite de l'écart
# mesuré (pas juste "recommence"). Pas de nouvelle vérification après le
# retry -- le résultat du 2e essai est accepté quoi qu'il arrive, pour
# borner le coût/temps (chaque retry double le temps de génération pour
# l'article concerné).
RETRY_DEVIATION_THRESHOLD = 0.40


# ─────────────────────────────────────────
# VALIDATION LONGUEUR
# ─────────────────────────────────────────

def _parse_longueur_bornes(longueur_label):
    """Extrait (lo, hi) depuis une chaîne du type "600 à 900 mots".
    Retourne None si le format n'est pas reconnu (pas de crash --
    dégradation silencieuse, pas de retry possible dans ce cas)."""
    m = re.match(r"^\s*(\d+)\s*à\s*(\d+)\s*mots?\s*$", longueur_label or "")
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _count_words(text):
    """Même méthode de comptage que audit_longueur_articles.py, pour que
    la mesure faite ici et celle de l'audit externe restent comparables."""
    return len(re.findall(r"\b\w+\b", text, re.UNICODE))


def _deviation_ratio(wc, bornes):
    """Écart relatif à la borne violée (0.0 si dans la plage). Ex. :
    900 mots pour une plage 600-900 -> 0.0 (dans la plage, borne incluse).
    1200 mots pour 600-900 -> (1200-900)/900 = 0.333 (33,3% au-dessus de
    la borne haute)."""
    lo, hi = bornes
    if wc < lo:
        return (lo - wc) / lo
    if wc > hi:
        return (wc - hi) / hi
    return 0.0


def _retry_with_length_feedback(prompt_data, wc_precedent, bornes):
    """Un seul nouvel appel LLM, avec la consigne de longueur d'origine
    ré-augmentée d'un rappel explicite et chiffré de l'écart mesuré --
    plus efficace qu'un simple "recommence", cf. décision du 10 août."""
    lo, hi = bornes
    if wc_precedent > hi:
        ecart_pct = round(100 * (wc_precedent - hi) / hi)
        consigne_ecart = (
            "Ta précédente tentative faisait {} mots, soit {}% de trop par rapport "
            "à la borne haute ({} mots). Coupe le texte pour rester entre {} et {} "
            "mots cette fois.".format(wc_precedent, ecart_pct, hi, lo, hi)
        )
    else:
        ecart_pct = round(100 * (lo - wc_precedent) / lo)
        consigne_ecart = (
            "Ta précédente tentative faisait seulement {} mots, soit {}% de moins "
            "que la borne basse ({} mots). Développe davantage le sujet pour "
            "atteindre entre {} et {} mots cette fois.".format(
                wc_precedent, ecart_pct, lo, lo, hi)
        )

    retry_user_prompt = (
        prompt_data["user_prompt"]
        + "\n\n---\n\n"
        + "RETRY — CONSIGNE DE LONGUEUR NON RESPECTÉE AU PREMIER ESSAI\n"
        + consigne_ecart
        + " Réécris l'article en entier depuis le titre (même sujet, même angle, "
          "mêmes contraintes ci-dessus), en respectant cette fois strictement la "
          "longueur demandée."
    )

    print("[api] Longueur hors plage ({} mots, attendu {}-{}, écart {:.0%}) "
          "— retry unique avec rappel explicite...".format(
              wc_precedent, lo, hi, _deviation_ratio(wc_precedent, bornes)))

    article_retry = call_llm(
        system_prompt=prompt_data["system_prompt"],
        user_prompt=retry_user_prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        task_tier=TASK_TIER,
    )
    wc_retry = _count_words(article_retry)
    print("[api] Retry terminé : {} mots (attendu {}-{}).".format(wc_retry, lo, hi))
    return article_retry, wc_retry


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
    # Normaliser la date fictive : "3 février 2098" → "3fevrier2098"
    # Bug corrigé le 10 août 2026 (retour de David) : la regex [^a-z0-9]
    # ne matchait pas les caractères accentués (é, û...) et les
    # supprimait donc silencieusement au lieu de les translittérer —
    # "février" devenait "fvrier". Un passage par unicodedata.normalize
    # (décomposition NFKD, ex. "é" → "e" + accent combinant séparé) avant
    # le filtrage ascii permet de garder la lettre de base et de ne
    # supprimer que le diacritique.
    if date_fictive:
        date_slug = re.sub(r"\s+", "", date_fictive.lower())
        date_slug = unicodedata.normalize("NFKD", date_slug)
        date_slug = date_slug.encode("ascii", "ignore").decode("ascii")
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
        # Traçabilité retry (ajouté le 10 août 2026, chantier longueur) :
        # permet de vérifier l'efficacité du retry directement dans le
        # frontmatter, sans dépendre uniquement d'un re-passage de
        # audit_longueur_articles.py après coup.
        "mots_reels: {}".format(meta.get("mots_reels", "")),
        "retry_longueur: {}".format("oui" if meta.get("retry_longueur") else "non"),
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

    Bug corrigé le 10 août 2026 (retour de David) : le dossier de sortie
    était figé sur ARTICLES_DIR (vault/articles/, racine), sans jamais
    lire config["output"]["dossier"] -- generate_series.py et
    generate_manual.py construisaient pourtant ce champ
    ("articles/{scenario}") et créaient même le sous-dossier pour y
    écrire leur _index.md respectif, mais les articles eux-mêmes
    atterrissaient toujours à la racine, orphelins de leur propre index.
    Voir aussi trace_injection.py et audit_longueur_articles.py, dont le
    scan a dû être rendu récursif en même temps pour ne pas perdre de
    visibilité sur les articles désormais rangés en sous-dossier.
    """
    dossier_config = config.get("output", {}).get("dossier") or "articles"
    output_dir = os.path.join(VAULT_PATH, dossier_config)
    os.makedirs(output_dir, exist_ok=True)

    # Nom du fichier
    nom_config = config.get("output", {}).get("nom_fichier", "auto")
    if nom_config == "auto":
        date_fictive = config.get("article", {}).get("date_fictive", "")
        filename = build_article_filename(snapshot, thematique, article_text, date_fictive)
    else:
        filename = nom_config if nom_config.endswith(".md") else nom_config + ".md"

    # Contenu complet
    content = build_article_md(article_text, snapshot, thematique, prompt_data)

    filepath = os.path.join(output_dir, filename)
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

    # Validation longueur + retry conditionnel (ajouté le 10 août 2026,
    # décision explicite avec David : seuil unique à 40% d'écart, un seul
    # retry maximum, résultat du retry accepté quoi qu'il arrive -- voir
    # RETRY_DEVIATION_THRESHOLD ci-dessus pour le contexte complet).
    bornes = _parse_longueur_bornes(prompt_data["metadata"].get("longueur", ""))
    wc = _count_words(article)
    retry_effectue = False
    if bornes:
        if _deviation_ratio(wc, bornes) > RETRY_DEVIATION_THRESHOLD:
            article, wc = _retry_with_length_feedback(prompt_data, wc, bornes)
            retry_effectue = True
    else:
        print("[api] [WARN] Longueur '{}' non reconnue par _parse_longueur_bornes "
              "— validation/retry ignorés pour cet article.".format(
                  prompt_data["metadata"].get("longueur", "")))

    prompt_data["metadata"]["mots_reels"] = wc
    prompt_data["metadata"]["retry_longueur"] = retry_effectue

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
