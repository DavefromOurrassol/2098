# Spec — Interface GUI Ourrassol 2098
*Version 2 — mise à jour 28 juin 2026*

## Contexte projet

**Ourrassol 2098** est un simulateur de presse fictif (2098) construit sur un vault Obsidian avec un pipeline de scripts Python. Le développeur travaille sur macOS High Sierra + Python 3, avec VS Code. Il veut remplacer le lancement manuel de scripts dans le terminal par une interface graphique locale. Ordinateur iMAC 2011 High Sierra.

---

## Stack technique retenue

- **Backend** : Flask (Python 3)
- **Frontend** : HTML/CSS/JS servi par Flask
- **Navigateur** : Chrome (localhost)
- **Lancement** : `python3 app.py` dans le terminal, puis ouverture de `localhost:5000`
- **Exécution des scripts** : `subprocess` (appel `python3 script.py --args`)

**Pourquoi Flask et pas PyWebView ou Tkinter** : PyWebView est incompatible avec macOS High Sierra. Tkinter est trop austère. Flask + navigateur donne la qualité visuelle souhaitée sans contrainte de compatibilité.

---

## Structure des fichiers à créer

```
/gui/                          ← dossier à la racine du vault (séparé du pipeline)
  app.py                       ← serveur Flask
  scripts_config.json          ← définition des scripts et leurs options CLI
  config.json                  ← configuration du vault (chemin, scénario par défaut)
  templates/
    index.html                 ← interface principale
  static/
    app.js                     ← logique frontend
    style.css                  ← styles
  logs/                        ← logs sauvegardés par run
```

---

## config.json

Fichier éditable directement dans l'interface GUI (onglet Config).

```json
{
  "vault_root": "/chemin/absolu/vers/le/vault",
  "pipeline_dir": "/chemin/absolu/vers/le/vault/generator",
  "default_scenario": "breakdown",
  "scenarios": [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference"
  ],
  "llm": {
    "provider": "mistral",
    "model_mistral": "mistral-small",
    "model_claude": "claude-sonnet-4-6",
    "available_providers": ["mistral", "claude"],
    "available_models_mistral": [
      "mistral-medium",
      "mistral-large",
      "mistral-tiny"
    ],
    "available_models_claude": [
      "claude-sonnet-4-6",
      "claude-opus-4-6",
      "claude-haiku-4-5-20251001"
    ]
  }
}
```

---

## Sélecteur LLM global (nouveau)

### Principe

Un sélecteur LLM est affiché en **en-tête de la barre latérale**, toujours visible.
Il définit les variables d'environnement `LLM_PROVIDER` et `LLM_MODEL` injectées
dans tous les subprocesses lancés par Flask.

### Composant UI

```
┌─────────────────────────────┐
│ OURRASSOL 2098              │
│                             │
│ LLM : [Mistral ▼] [Medium ▼]│
└─────────────────────────────┘
```

- **Select fournisseur** : `Mistral` | `Claude` (défaut : Mistral)
- **Select modèle** : liste filtrée selon le fournisseur choisi
  - Mistral : `mistral-medium-latest` | `mistral-large-latest` | `mistral-small-latest`
  - Claude : `claude-sonnet-4-6` | `claude-opus-4-6` | `claude-haiku-4-5-20251001`
- **Indicateur de coût** (badge coloré) :
  - 🟢 Mistral Small / Medium — économique
  - 🟡 Mistral Large / Claude Sonnet — standard
  - 🔴 Claude Opus — coûteux
- Le choix est sauvegardé dans `config.json` à chaque modification

### Injection dans les subprocesses

Flask injecte les variables d'environnement dans tous les appels subprocess :

```python
env = os.environ.copy()
env["LLM_PROVIDER"] = config["llm"]["provider"]
env["LLM_MODEL"] = config["llm"]["model_mistral"]  # ou model_claude
subprocess.Popen(cmd, env=env, cwd=pipeline_dir, ...)
```

---

## scripts_config.json

Source de vérité pour tous les scripts. Flask génère les formulaires dynamiquement depuis ce fichier.

### Types d'options supportés

| Type | Rendu dans l'interface |
|---|---|
| `checkbox` | Case à cocher avec label + description |
| `select` | Menu déroulant (valeurs fixes ou depuis config) |
| `slug_select` | Menu déroulant peuplé dynamiquement depuis le vault |
| `number` | Input numérique avec min/max/default |
| `text` | Input texte libre |
| `ligne_select` | Select fixe : `pro_pouvoir` \| `opposition` \| aléatoire |

### Champ `requires`

```json
{
  "id": "validate",
  "requires": ["extract_localisation"],
  "requires_message": "extract_localisation devrait tourner avant validate"
}
```

---

### Scripts à intégrer

#### Section "Génération"

**`generate.py`**
- Aucun argument CLI — lit `config.yaml`
- Bouton "Éditer config.yaml" → ouvre un formulaire inline
- Champs : `scenario` (select), `thematique` (select), `ligne_editoriale` (ligne_select),
  `zone_slug` (slug_select filtré par scénario), `longueur` (select), `angle_specifique` (text)
- Option `--dry-run` (checkbox)

**`generate_series.py`**
- Options : `--dry-run`, `--validate-first`, `--scenario` (select)
- Édition inline `config_series.yaml` :
  - `scenario` (select)
  - `ligne_editoriale` (ligne_select — vide = aléatoire)
  - `thematiques` (multi-select chips)
  - `articles_par_thematique` (number)
  - `longueur` (select)
  - `angle_specifique` (text)

**`generate_manual.py`**
- Trois boutons distincts : `prompt` | `status` | `save`
- Pour `save` : input file path
- Affiche l'avancement de la série depuis `state/manual_progress.json`

**`enrich_minimal.py`**
- Options : `--all` (checkbox), `--dry-run`, `--scenario` (select), `--slug` (slug_select),
  `--limit` (number, défaut 10, max 426), `--auto-cycle` (checkbox)

**`validate.py`**
- Options : `--verbose/-v` (checkbox), `--report/-r` (checkbox),
  `--localisation` (checkbox), `--narrative/-n` (checkbox)

**`generate_journaux.py`** *(nouveau)*
- Options :
  - `--scenario` (select) | `--all` (checkbox) — mutuellement exclusifs
  - `--ligne` (select : `pro_pouvoir` | `opposition` | `all`, défaut `all`)
  - `--update` (checkbox — "Zones manquantes seulement")
  - `--dry-run` (checkbox)
- Badge : nombre de journaux déjà générés dans `journaux.yaml`
- Avertissement si `journaux.yaml` absent : "Journaux locaux non générés — lancez ce script"

#### Section "Entités"

**`create_entities_and_instances.py`**
- Options : mode (`custom` | `auto` | `auto-suggest`), `--scenario` (select), `--dry-run`

**`inject_custom_events.py`**
- Options : mode (`custom` | `auto`), `--scenario` (select), `--dry-run`

**`inject_custom_signals.py`**
- Options : `--dry-run`

**`undo_custom.py`**
- Options : source (`undo_queue.yaml` | `--slug direct`), `--slug` (slug_select),
  `--type` (select : `instance` | `event_instance` | `entite` | `event`),
  `--generalisation` (select : `yes` | `no`), `--dry-run` / `--execute`

**`extract_phantom_slugs.py`**
- Options : `--source` (select : `enrich` | `validate` | `all`),
  `--report` (text), `--dry-run`

**`fix_alliance_suffixes.py`**
- Options : `--dry-run`, `--verbose`, `--scenario` (select)

**`requeue_needs_review.py`**
- Aucune option — bouton simple "Lancer"

#### Section "Maintenance"

**`extract_localisation.py`**
- Options : `--dry-run`, `--scenario` (select), `--slug` (slug_select),
  `--force` (checkbox), `--report-only` (checkbox)

**`review_localisation.py`**
- Options : `--auto-resolve` (checkbox), `--dry-run`, `--scenario` (select)

**`build_geographie_monde.py`**
- Options : `--scenario` (select — obligatoire), `--dry-run`

**`enrich_geographie_recursive.py`**
- Options : `--scenario` (select) | `--all` (checkbox), `--dry-run`

**`restructure_zones.py`** *(P7 — à implémenter)*
- Options : opération (`rename` | `reparent` | `split` | `merge`),
  zone source (slug_select zones), cible/nouveau nom, `--dry-run`

---

## Interface — structure générale

### Barre latérale (gauche, fixe)

```
OURRASSOL 2098
──────────────
LLM : [Mistral ▼] [Medium ▼]  🟢
──────────────
📊 Tableau de bord
──────────────
GÉNÉRATION
  ✨ Enrich minimal    [426]
  🗞 Generate journaux [badge: nb journaux]
  🛡 Validate          [0]
  📄 Generate
  📋 Generate series
  ✍️  Generate manual
──────────────
ENTITÉS
  👥 Create entities
  ⚡ Inject events
  📡 Inject signals
  🔍 Extract phantom slugs
  🔧 Fix alliance suffixes
  🔁 Requeue needs review
  ↩  Undo custom
──────────────
MAINTENANCE
  📍 Extract localisation
  ✅ Review localisation
  🌍 Build géographie
  🗺  Enrich géographie
  🗂  Restructure zones
──────────────
🔍 Revue       [badge orange si items]
⚙️  Config
```

### Zone principale (droite)

Divisée en deux colonnes :
- **Colonne gauche (300px)** — formulaire d'options du script sélectionné
- **Colonne droite (flex)** — panneau de log

---

## Onglet Tableau de bord

### Stats à afficher

**Fournisseur LLM actif**
- Nom du fournisseur + modèle actif
- Indicateur de coût (badge coloré)

**Articles créés**
- Nombre total dans `vault/articles/`
- Répartition par scénario
- Répartition par ligne éditoriale (`pro_pouvoir` / `opposition`) — nouveau
- Source : frontmatter `ligne_editoriale` des articles

**Journaux locaux** *(nouveau)*
- Nombre d'éditions générées dans `journaux.yaml` par scénario
- Badge "À générer" si `journaux.yaml` absent ou incomplet

**Thématiques couvertes**
- 20 catégories avec compteur d'articles

**Géographie couverte**
- Zones avec compteur d'instances

**Statut enrichissement**
- `officialise_minimal` restantes / `officialise_enrichi` complétées

**Badge revue**
- Compteur total items en attente → lien onglet Revue

---

## Onglet Revue

Agrège trois sources :
1. `needs_review.yaml` — événements en échec partiel
2. `needs_review_enrich.yaml` — instances avec warnings enrichissement
3. `localisation_review.md` — entrées `review_manuelle`

Affichage par item : slug, scénario, source (badge), type d'erreur, chemin fichier.

---

## Onglet Config

Formulaire d'édition de `config.json` avec :
- Champ texte `vault_root`
- Champ texte `pipeline_dir`
- Select `default_scenario`
- **Section LLM** *(nouveau)* :
  - Select fournisseur par défaut (`mistral` | `claude`)
  - Select modèle Mistral par défaut
  - Select modèle Claude par défaut
- Bouton "Sauvegarder"
- Bouton "Tester le chemin"

---

## Exécution des scripts

### Règles
- Un seul script à la fois — bouton Lancer désactivé si un script tourne
- Bouton Stop — `process.terminate()`
- Répertoire de travail : `pipeline_dir`
- **Variables LLM injectées** dans tous les subprocesses : `LLM_PROVIDER`, `LLM_MODEL`

### Streaming du log (Server-Sent Events)

Coloration :
- `✓` ou `OK` → vert
- `⚠` ou `WARNING` ou `[WARN]` → orange
- `ERROR` ou `✗` → rouge
- `[llm]` → bleu (ligne de stats tokens)
- `[WARN][journal]` → orange avec icône journal

### Sauvegarde des logs

`/gui/logs/{script_id}_{YYYYMMDD_HHMMSS}.log`

---

## Menu déroulant `ligne_select` *(nouveau)*

Type spécial pour la ligne éditoriale :

```json
{
  "flag": "--ligne",
  "type": "ligne_select",
  "label": "Ligne éditoriale",
  "choices": [
    {"value": "pro_pouvoir", "label": "Pro pouvoir"},
    {"value": "opposition",  "label": "Opposition"},
    {"value": "",            "label": "Aléatoire (série)"}
  ],
  "default": "pro_pouvoir"
}
```

---

## Menu déroulant slugs (`slug_select`)

### Sources selon `slug_type`

| Valeur | Source |
|---|---|
| `instances` | Scan `instances/*.md`, frontmatter `slug` |
| `entities` | `_entities_list.json` + scan `instances/*.md` |
| `zones` | `geographie/{scenario}.md` — zones N1 uniquement |
| `zones_all` | `geographie/{scenario}.md` — toutes les zones |

### API Flask

```
GET /api/slugs?type=instances&scenario=breakdown
GET /api/slugs?type=zones&scenario=breakdown
GET /api/slugs?type=instances&scenario=all
```

---

## Lancement de l'application

```bash
cd /chemin/vers/vault/gui
python3 -m pip install flask
python3 app.py
# → ouvrir http://localhost:5000 dans Chrome
```

---

## Todo list d'implémentation

### Phase 1 — Squelette Flask
- [ ] `app.py` : serveur Flask, routes de base, lecture `config.json`
- [ ] `templates/index.html` : layout barre latérale + zone principale
- [ ] `static/style.css` : styles (dark theme)
- [ ] `static/app.js` : navigation entre onglets

### Phase 2 — Sélecteur LLM global *(nouveau)*
- [ ] Composant sélecteur fournisseur + modèle dans la sidebar
- [ ] Sauvegarde dans `config.json` à chaque changement
- [ ] Badge indicateur de coût
- [ ] Injection `LLM_PROVIDER` + `LLM_MODEL` dans tous les subprocesses

### Phase 3 — Formulaires dynamiques
- [ ] Route `GET /api/script/<id>` → config depuis `scripts_config.json`
- [ ] Génération dynamique des formulaires
- [ ] Tous les types : checkbox, select, number, text, ligne_select
- [ ] `slug_select` : peuplement via `GET /api/slugs`
- [ ] Logique `requires` : vérification session + avertissement orange

### Phase 4 — Exécution et streaming
- [ ] Route `POST /run` → subprocess + `run_id`
- [ ] Route `GET /stream/<run_id>` → SSE stdout
- [ ] Route `POST /stop/<run_id>` → terminate
- [ ] Sauvegarde log
- [ ] Coloration lignes log (ok/warn/err/llm/journal)
- [ ] Blocage bouton Lancer si script actif

### Phase 5 — Tableau de bord
- [ ] Route `GET /api/dashboard` → stats vault JSON
- [ ] Stats articles + répartition ligne éditoriale
- [ ] Stats journaux locaux (`journaux.yaml`)
- [ ] Badge revue

### Phase 6 — Onglet Revue
- [ ] Parser `needs_review.yaml`
- [ ] Parser `needs_review_enrich.yaml`
- [ ] Parser `localisation_review.md`
- [ ] Affichage unifié badges source

### Phase 7 — Onglet Config
- [ ] Formulaire lecture/écriture `config.json`
- [ ] Section LLM dans config
- [ ] Validation chemin `pipeline_dir`

### Phase 8 — scripts_config.json complet
- [ ] Intégrer tous les scripts avec options réelles
- [ ] Inclure `generate_journaux.py`, `generate_manual.py`, `generate_series.py`
- [ ] Types `ligne_select` pour les scripts concernés
- [ ] À finaliser après réception vault mis à jour

---

## Notes importantes pour l'implémentation

- Les scripts Python existants **ne doivent pas être modifiés** — Flask est une surcouche pure
- macOS High Sierra : éviter toute dépendance système moderne — Flask + Chrome est suffisant
- Le subprocess doit être lancé avec `cwd=pipeline_dir` pour que les imports relatifs fonctionnent
- `LLM_PROVIDER` et `LLM_MODEL` doivent être injectés dans **tous** les subprocesses sans exception
- `journaux.yaml` est dans `generator/` — Flask le lit directement pour les stats dashboard
- Les zones pour `slug_select` de type `zones` ne retournent que les N1 (filtre `niveau: 1`)
