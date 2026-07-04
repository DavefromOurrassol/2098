# Handoff — GUI Ourrassol 2098
*Session du 29 juin 2026*

---

## Lancement

```bash
# Via l'appli bureau (double-clic sur Ourrassol 2098.app)
# ou depuis le terminal :
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py
# → http://localhost:5000 dans Chrome
```

---

## Chemins configurés (config.json)

```json
{
  "vault_root":     "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/",
  "pipeline_dir":   "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/generator/",
  "default_scenario": "reference"
}
```

---

## État des fichiers GUI

```
gui/
  app.py                  ← serveur Flask complet (routes + exécution scripts)
  config.json             ← configuration vault + LLM (avec available_models_*)
  scripts_config.json     ← définition des 18 scripts + yaml_files
  templates/index.html    ← layout HTML
  static/style.css        ← light theme
  static/app.js           ← logique frontend
  .env                    ← clés API (MISTRAL_API_KEY, ANTHROPIC_API_KEY)
  start.sh                ← script lancement terminal
  Ourrassol2098.applescript ← appli bureau AppleScript
  logs/                   ← logs des runs
```

---

## Phases livrées

| Phase | Statut | Notes |
|---|---|---|
| 1 — Squelette Flask | ✅ | |
| 2 — Sélecteur LLM | ✅ | Modèles Mistral : mistral-small/medium/large (sans -latest) |
| 3 — Formulaires dynamiques | ✅ | Tous types d'options |
| 4 — Exécution + streaming | ✅ | SSE stdout, Stop, logs sauvegardés |
| 5 — Dashboard stats réelles | ✅ | 8 cartes + tableau thématiques |
| 6 — Onglet Revue | ✅ | 3 sources parsées |
| YAML viewer/editor | ✅ | Lecture + édition avec backup .bak |
| slug_select | ✅ | Scan vault réel |
| Clés API via .env | ✅ | Chargé au démarrage Flask |
| Appli bureau AppleScript | ✅ | Ouvre Terminal + Chrome |

---

## Bugs résolus cette session

| Bug | Fix |
|---|---|
| Flask ne démarrait pas | Bloc `if __name__ == "__main__"` manquant |
| `run_script` retournait None (500) | Corps de la fonction manquant après reconstruction |
| `available_models_*` perdus à la sauvegarde | Route POST préserve maintenant les clés `available_*` |
| Modèle LLM vide dans dashboard et sidebar | `config.json` corrigé avec les listes complètes |
| Articles mentionnant des zones hors cible | `prompt_builder.py` : contrainte géographique ajoutée dans les consignes finales |
| MISTRAL_API_KEY non transmise aux subprocesses | Chargement `.env` dans `app.py` au démarrage |

---

## Prochaine session — priorité

### 1. Formulaires guidés YAML (nouvelle feature)
Remplacer le YAML viewer/editor textarea brut par des formulaires avec menus déroulants pour les valeurs autorisées. Trois YAMLs à couvrir :

**config.yaml** (generate.py) — champs :
- `scenario` → select (6 scénarios)
- `thematique` → select (20 thématiques)
- `ligne_editoriale` → select (pro_pouvoir / opposition)
- `zone_slug` → slug_select zones N1
- `article.longueur` → select
- `article.angle_specifique` → text libre

**config_series.yaml** (generate_series.py) — champs :
- `scenario` → select
- `thematiques` → multi-select (20 thématiques)
- `articles_par_thematique` → number
- `longueur` → select
- `ligne_editoriale` → select + option aléatoire
- `angle_specifique` → text libre

**queue.yaml** (create_entities / inject_events) — structure plus complexe, à analyser depuis le fichier réel

⚠️ Avant de coder : demander à David les contenus réels de ces 3 fichiers via `cat` dans le terminal.

### 2. Vérifier le streaming end-to-end
Tester `validate.py --dry-run` et `enrich_minimal.py --limit 2 --dry-run` depuis le GUI pour confirmer que le log SSE fonctionne correctement avec les vraies clés.

### 3. scripts_config.json — vérification
Certaines options peuvent ne pas correspondre exactement aux vrais scripts. À croiser avec les fichiers sources si des erreurs apparaissent au lancement.

---

## Architecture backend (routes disponibles)

| Route | Méthode | Description |
|---|---|---|
| `/api/config` | GET/POST | Config (POST préserve available_*) |
| `/api/scripts` | GET | Liste des scripts |
| `/api/script/<id>` | GET | Config d'un script |
| `/api/yaml` | GET/POST | Lecture/écriture YAML (backup .bak) |
| `/api/slugs` | GET | Slugs dynamiques vault |
| `/api/dashboard` | GET | Stats complètes |
| `/api/review` | GET | Items en revue |
| `/api/run` | POST | Lance un script |
| `/api/stream/<run_id>` | GET | SSE streaming stdout |
| `/api/stop/<run_id>` | POST | Stop subprocess |
| `/api/status` | GET | État run actif |

---

## Fichiers pipeline modifiés (hors gui/)

| Fichier | Modification | Emplacement |
|---|---|---|
| `prompt_builder.py` | Contrainte géographique zone_slug dans consignes finales | `generator/` |

