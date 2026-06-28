"""
generate_manual.py
-------------------
Pipeline "SANS API" — workflow manuel avec Claude (chat).

Suit la même série que generate_series.py / config_series.yaml
(scénario, thématiques, dates, longueur, injections), mais au lieu
d'appeler l'API Anthropic :

  - construit le snapshot + le prompt pour le PROCHAIN article de la
    série (dry_run=False → met à jour la mémoire de rotation
    state/trajectory_usage.json comme une vraie génération)
  - affiche SYSTEM PROMPT + USER PROMPT à copier dans le chat Claude
    pour évaluer le contenu

MODE PRÉVISUALISATION (par défaut, phase de construction) :
chaque appel à 'prompt' avance automatiquement à l'article suivant
de la série — l'article précédent n'est PAS sauvegardé, juste
marqué "prévisualisé". Pratique pour tester rapidement le contenu
de plusieurs articles à la suite sans gérer de fichiers.

Usage :

    python3 generate_manual.py prompt
    # → copier SYSTEM PROMPT + USER PROMPT dans le chat, lire l'article,
    #   évaluer. Relancer 'prompt' pour passer au suivant.

    python3 generate_manual.py status
    # → voir l'avancement de la série (X/N articles)

SAUVEGARDE OPTIONNELLE (une fois satisfait du contenu) :
si vous voulez conserver un article dans le vault avant de passer
au suivant, collez son texte dans un fichier puis :

    python3 generate_manual.py save /tmp/article.txt
    # → écrit le .md (frontmatter + contenu) dans articles/{scenario}/
    #   et met à jour _index.md. Doit être appelé AVANT le prochain
    #   'prompt' (qui marque sinon l'article courant "prévisualisé").
"""

import os
import random
import sys
import json
from datetime import datetime

import yaml

from loader         import VAULT_PATH, load_thematique
from snapshot       import build_snapshot
from prompt_builder import build_prompt, STATE_DIR


# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

CONFIG_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_series.yaml")
PROGRESS_FILE = os.path.join(STATE_DIR, "manual_progress.json")

# Mêmes dates que generate_series.py, pour rester cohérent si on
# alterne entre les deux workflows sur la même série.
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
    "5 novembre 2098",  "21 novembre 2098",
    "6 décembre 2098",  "22 décembre 2098",
]


# ─────────────────────────────────────────
# ÉTAT DE PROGRESSION
# ─────────────────────────────────────────

def load_progress():
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"completed": [], "pending": None}


def save_progress(progress):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def build_tasks(config):
    """Reconstruit la liste (thematique, date_fictive) — identique à generate_series.py."""
    thematiques = config["thematiques"]
    n_per_thema = config.get("articles_par_thematique", 1)

    tasks = []
    date_index = 0
    for thematique in thematiques:
        for _ in range(n_per_thema):
            date_fictive = DATES_2098[date_index % len(DATES_2098)]
            tasks.append((thematique, date_fictive))
            date_index += 1
    return tasks


# ─────────────────────────────────────────
# SAUVEGARDE DE L'ARTICLE (équivalent api.py, sans anthropic)
# ─────────────────────────────────────────

def build_article_filename(scenario_slug, thematique_slug):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return "{}_{}_{}_{}.md".format(timestamp, scenario_slug, thematique_slug, "article")


def build_article_md(article_text, pending):
    meta = pending["metadata"]
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    frontmatter_lines = [
        "---",
        "type: generated_article",
        "date_generation: {}".format(now),
        "scenario: {}".format(meta["scenario"]),
        "thematique: {}".format(meta["thematique"]),
        "format: {}".format(meta["format"]),
        "longueur: {}".format(meta["longueur"]),
        "model: claude (manuel — chat)",
        "ligne_editoriale: {}".format(pending.get("ligne_editoriale", "pro_pouvoir")),
        "scenario_state: {}".format(pending["state_of_system"]),
        "tension_level: {}".format(pending["tension_level"]),
        "variables_pilotes:",
    ]
    for v in pending.get("pilot_variables", []):
        frontmatter_lines.append("  - {}".format(v))
    frontmatter_lines.append("---")
    frontmatter_lines.append("")

    return "\n".join(frontmatter_lines) + article_text.strip() + "\n"


def build_index(config, completed, output_dir):
    scenario = config["scenario"]
    now      = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "---",
        "type: article_series_index",
        "scenario: {}".format(scenario),
        "date_generation: {}".format(now),
        "total_articles: {}".format(len(completed)),
        "---",
        "",
        "# Index de la série — {} — 2098".format(scenario.upper()),
        "",
        "Généré le {} | {} articles".format(now, len(completed)),
        "",
        "## Articles",
        "",
    ]

    for i, r in enumerate(completed, 1):
        lines.append("{}. [[{}]] — *{}* ({})".format(
            i,
            os.path.basename(r["filepath"]).replace(".md", ""),
            r["thematique"],
            r["date_fictive"],
        ))

    index_path = os.path.join(output_dir, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return index_path


# ─────────────────────────────────────────
# COMMANDES
# ─────────────────────────────────────────

def cmd_status(config, progress):
    tasks = build_tasks(config)
    done  = len(progress["completed"])
    total = len(tasks)

    print("="*60)
    print("OURRASSOL 2098 — Génération MANUELLE (sans API)")
    print("="*60)
    print("  Scénario : {}".format(config["scenario"]))
    print("  Articles : {}/{}".format(done, total))
    print("="*60)

    statuts = {
        "ok":        "✓ sauvegardé",
        "previewed": "👁 prévisualisé (non sauvegardé)",
        "skipped":   "— ignoré",
    }

    for i, (thematique, date_fictive) in enumerate(tasks, 1):
        if i <= done:
            statut = statuts.get(progress["completed"][i-1].get("status"), "✓ fait")
        else:
            statut = "—"
        print("  [{}/{}] {} — {} : {}".format(i, total, thematique, date_fictive, statut))


def cmd_prompt(config, progress):
    tasks = build_tasks(config)

    # Phase de construction : pas de sauvegarde -> on avance simplement
    # au prompt suivant à chaque appel (l'éventuel "pending" précédent
    # est considéré comme lu/évalué, pas sauvegardé).
    if progress["pending"]:
        progress["completed"].append({
            **progress["pending"],
            "filepath": None,
            "status": "previewed",
        })
        progress["pending"] = None

    done = len(progress["completed"])
    if done >= len(tasks):
        print("[manual] Série terminée : {}/{} articles prévisualisés.".format(done, len(tasks)))
        print("[manual] Pour repartir de zéro : effacez state/manual_progress.json")
        return

    thematique_slug, date_fictive = tasks[done]

    print("[{}/{}] {} × {} — {}".format(
        done + 1, len(tasks), config["scenario"], thematique_slug, date_fictive
    ))

    # Ligne éditoriale : fixe si définie dans config, aléatoire sinon
    ligne_editoriale_config = config.get("ligne_editoriale", None)
    if ligne_editoriale_config in ("pro_pouvoir", "opposition"):
        ligne_editoriale = ligne_editoriale_config
    else:
        ligne_editoriale = random.choice(["pro_pouvoir", "opposition"])

    article_config = {
        "scenario":          config["scenario"],
        "thematique":        thematique_slug,
        "ligne_editoriale":  ligne_editoriale,
        "article": {
            "titre_suggere":    "",
            "angle_specifique": config.get("angle_specifique", ""),
            "longueur":         config.get("longueur", "auto"),
            "date_fictive":     date_fictive,
        },
        "output": {
            "dossier":     "articles/{}".format(config["scenario"]),
            "nom_fichier": "auto",
        },
        "injections": config.get("injections", []),
    }

    thema_data = load_thematique(thematique_slug)
    snapshot   = build_snapshot(config["scenario"], thematique=thema_data)

    # dry_run=False : met à jour la mémoire de rotation (state/trajectory_usage.json)
    prompt_data = build_prompt(snapshot, thema_data, article_config, dry_run=False)

    print("\n--- SYSTEM PROMPT ---")
    print(prompt_data["system_prompt"])
    print("\n--- USER PROMPT (complet) ---")
    print(prompt_data["user_prompt"])

    # Enregistrer l'état "en attente"
    progress["pending"] = {
        "thematique":      thematique_slug,
        "date_fictive":    date_fictive,
        "scenario":        config["scenario"],
        "ligne_editoriale": ligne_editoriale,
        "metadata":        prompt_data["metadata"],
        "state_of_system": snapshot["scenario"]["state_of_system"],
        "tension_level":   snapshot["scenario"]["tension_level"],
        "pilot_variables": snapshot.get("pilot_variables", []),
    }
    save_progress(progress)

    print("\n" + "="*60)
    print("Copiez les deux blocs ci-dessus dans le chat avec Claude pour")
    print("obtenir l'article et évaluer le contenu.")
    print()
    print("Pour passer au prochain article de la série :")
    print("  python3 generate_manual.py prompt")
    print()
    print("(optionnel) Pour sauvegarder cet article dans le vault :")
    print("  python3 generate_manual.py save <fichier_article.txt>")
    print("="*60)


def cmd_save(config, progress, article_file):
    if not progress["pending"]:
        print("[manual] Aucun article en attente. Lancez d'abord :")
        print("  python3 generate_manual.py prompt")
        return

    if not os.path.exists(article_file):
        print("[manual] Fichier introuvable : {}".format(article_file))
        return

    with open(article_file, "r", encoding="utf-8") as f:
        article_text = f.read()

    if not article_text.strip():
        print("[manual] Le fichier est vide : {}".format(article_file))
        return

    pending  = progress["pending"]
    scenario = pending["scenario"]

    output_dir = os.path.join(VAULT_PATH, "articles", scenario)
    os.makedirs(output_dir, exist_ok=True)

    filename = build_article_filename(scenario, pending["thematique"])
    filepath = os.path.join(output_dir, filename)

    content = build_article_md(article_text, pending)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("[manual] Article sauvegardé : {}".format(filepath))

    progress["completed"].append({
        "thematique":   pending["thematique"],
        "date_fictive": pending["date_fictive"],
        "filepath":     filepath,
        "status":       "ok",
    })
    progress["pending"] = None
    save_progress(progress)

    # Régénérer l'index
    completed_ok = [r for r in progress["completed"] if r.get("status") == "ok"]
    index_path = build_index(config, completed_ok, output_dir)
    print("[manual] Index mis à jour : {}".format(index_path))

    done  = len(progress["completed"])
    tasks = build_tasks(config)
    if done < len(tasks):
        print("\nProchain article : 'python3 generate_manual.py prompt'")
    else:
        print("\n✓ Série terminée ({}/{} articles).".format(done, len(tasks)))


# ─────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    progress = load_progress()
    cmd = sys.argv[1]

    if cmd == "status":
        cmd_status(config, progress)
    elif cmd == "prompt":
        cmd_prompt(config, progress)
    elif cmd == "save":
        if len(sys.argv) < 3:
            print("Usage : python3 generate_manual.py save <fichier_article.txt>")
            return
        cmd_save(config, progress, sys.argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
