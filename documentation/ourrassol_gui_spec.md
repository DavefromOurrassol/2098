# Spec — Interface GUI Ourrassol 2098

## Contexte projet

**Ourrassol 2098** est un simulateur de presse fictif (2098) construit sur un vault Obsidian avec un pipeline de scripts Python. Le développeur travaille sur macOS High Sierra + Python 3, avec VS Code. Il veut remplacer le lancement manuel de scripts dans le terminal par une interface graphique locale.

---

## Stack technique retenue

- **Backend** : Flask (Python 3)
- **Frontend** : HTML/CSS/JS servi par Flask
- **Navigateur** : Safari (localhost)
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

Le pipeline Python (scripts existants) reste intact dans son propre dossier. Flask pointe vers lui via le chemin défini dans `config.json`.

---

## config.json

Fichier éditable directement dans l'interface GUI (onglet Config).

```json
{
  "vault_root": "/chemin/absolu/vers/le/vault",
  "pipeline_dir": "/chemin/absolu/vers/le/vault/pipeline",
  "default_scenario": "effondrement",
  "scenarios": [
    "effondrement", "resilience", "transition",
    "statu_quo", "rupture", "renaissance"
  ]
}
```

---

## scripts_config.json

Source de vérité pour tous les scripts. Flask génère les formulaires dynamiquement depuis ce fichier. Pour ajouter un script ou un flag, on édite ce JSON — aucune modification du code Python ou HTML requise.

### Structure d'un script

```json
{
  "id": "enrich_minimal",
  "name": "enrich_minimal.py",
  "label": "Enrich minimal",
  "description": "Enrichit les instances officialise_minimal via API Claude",
  "section": "generation",
  "requires": [],
  "options": [
    {
      "flag": "--all",
      "type": "checkbox",
      "label": "Toutes les instances",
      "description": "Traite les 426 instances officialise_minimal"
    },
    {
      "flag": "--dry-run",
      "type": "checkbox",
      "label": "Dry run",
      "description": "Simulation sans écriture"
    },
    {
      "flag": "--scenario",
      "type": "select",
      "label": "Scénario",
      "choices_from": "config.scenarios",
      "allow_empty": true,
      "empty_label": "— tous les scénarios —"
    },
    {
      "flag": "--slug",
      "type": "slug_select",
      "label": "Slug ciblé",
      "slug_type": "instances",
      "filterable_by_scenario": true,
      "description": "Laisse vide pour ignorer"
    },
    {
      "flag": "--limit",
      "type": "number",
      "label": "Limite",
      "default": 10,
      "min": 1,
      "max": 426,
      "description": "Nombre max d'instances à traiter"
    },
    {
      "flag": "--auto-cycle",
      "type": "checkbox",
      "label": "Auto-cycle",
      "description": "Relance la chaîne après enrichissement (extract → review → validate)"
    }
  ]
}
```

### Types d'options supportés

| Type | Rendu dans l'interface |
|------|----------------------|
| `checkbox` | Case à cocher avec label + description |
| `select` | Menu déroulant (valeurs fixes ou depuis config) |
| `slug_select` | Menu déroulant peuplé dynamiquement depuis le vault |
| `number` | Input numérique avec min/max/default |
| `text` | Input texte libre |

### Champ `requires`

Permet de définir des prérequis entre scripts. Si le script prérequis n'a pas tourné dans la session courante, un **avertissement orange** s'affiche avant le lancement (non bloquant — l'utilisateur peut forcer).

```json
{
  "id": "validate",
  "requires": ["extract_localisation"],
  "requires_message": "extract_localisation devrait tourner avant validate"
}
```

### Scripts à intégrer

#### Section "Génération"
- `enrich_minimal.py` — options : `--all`, `--dry-run`, `--scenario`, `--slug`, `--limit N`, `--auto-cycle`
- `validate.py` — options : `--scenario`, `--narrative/-n`, `--verbose/-v`, `--report/-r`
- `generate.py` — options : `--scenario`, catégorie thématique (chips multi-select), `--dry-run`

#### Section "Entités"
- `create_entities_and_instances.py` — options : mode (`create` | `auto-suggest`), `--scenario`, `--dry-run`
- `inject_custom_events.py` — options : mode (`inject` | `auto`), `--scenario`, `--dry-run`, post-cycle auto (checkbox)
- `undo_custom.py` — options : source (`undo_queue.yaml` | `--slug direct`), `--slug`, généralisation (`no` | `yes`), `--dry-run` / `--execute`

#### Section "Maintenance"
- `extract_localisation.py` — options : `--scenario`, `--dry-run`, `--force`, `--report-only`, `--slug`
- `restructure_zones.py` (P7 — à implémenter) — options : opération (`rename` | `reparent` | `split` | `merge`), zone source, cible/nouveau nom, `--dry-run`

---

## Exécution des scripts

### Règles
- **Un seul script à la fois** — si un script tourne, le bouton Lancer des autres est désactivé
- **Bouton Stop** — appelle `process.terminate()` sur le subprocess en cours
- **Répertoire de travail** — le subprocess est lancé depuis `pipeline_dir` (défini dans `config.json`)

### Streaming du log (Server-Sent Events)

Flask capture le stdout du subprocess ligne par ligne et le pousse au navigateur via SSE. Le panneau de log dans l'interface affiche les lignes en temps réel avec coloration :

- Ligne contenant `✓` ou `OK` → vert
- Ligne contenant `⚠` ou `WARNING` → orange
- Ligne contenant `ERROR` ou `✗` → rouge
- Reste → texte normal

### Sauvegarde des logs

Chaque run sauvegarde un fichier dans `/gui/logs/` nommé `{script_id}_{YYYYMMDD_HHMMSS}.log`.

### Construction de la commande

Flask reconstruit la commande CLI depuis les valeurs du formulaire :

```python
cmd = ["python3", script["name"]]
for option in selected_options:
    if option["type"] == "checkbox" and checked:
        cmd.append(option["flag"])
    elif option["type"] in ["select", "text", "number", "slug_select"] and value:
        cmd.extend([option["flag"], str(value)])
```

---

## Interface — structure générale

### Barre latérale (gauche, fixe)

```
OURRASSOL 2098
─────────────
📊 Tableau de bord
─────────────
GÉNÉRATION
  ✨ Enrich minimal    [426]
  🛡 Validate          [0]
  📄 Generate
─────────────
ENTITÉS
  👥 Create entities
  ⚡ Inject events
  ↩ Undo custom
─────────────
MAINTENANCE
  📍 Extract localisation
  🗂 Restructure zones
─────────────
🔍 Revue              [badge orange si items]
⚙️  Config
```

Les badges numériques sont calculés au chargement depuis le vault.

### Zone principale (droite)

Divisée en deux colonnes :
- **Colonne gauche (300px)** — formulaire d'options du script sélectionné
- **Colonne droite (flex)** — panneau de log

---

## Onglet Tableau de bord

Données lues au chargement de Flask depuis le vault (lecture fichiers, pas d'appel API).

### Stats à afficher

**Articles créés**
- Nombre total de fichiers dans `vault/articles/`
- Répartition par scénario
- Répartition par date (mois)

**Thématiques couvertes**
- Liste des 20 catégories thématiques avec compteur d'articles par catégorie
- Source : frontmatter `categorie` des fichiers articles

**Géographie couverte**
- Zones géographiques présentes dans les instances (`localisation.zone`)
- Compteur d'instances par zone
- Source : frontmatter des fichiers `instances/*.md`

**Statut enrichissement**
- `officialise_minimal` : X restantes à enrichir
- `officialise_enrichi` : X enrichies
- Source : frontmatter `statut` des fichiers instances

**Badge revue**
- Compteur total d'items en attente (toutes sources confondues)
- Lien cliquable vers l'onglet Revue

---

## Onglet Revue

Agrège trois sources de données, présentées de façon unifiée.

### Sources

**1. `needs_review.yaml`** (dans `pipeline/` ou `evenements_custom/`)
- Événements injectés en échec partiel
- Champs attendus : `slug`, `scenario`, `reason`, `status`

**2. `needs_review_enrich.yaml`** (dans `pipeline/`)
- Instances avec warnings non-bloquants après enrichissement
- Champs attendus : `slug`, `scenario`, `warnings` (liste)

**3. `localisation_review.md`** (dans `pipeline/` ou `documentation/`)
- Entrées avec statut `review_manuelle`
- Parser : lire le frontmatter YAML ou les blocs de liste selon la structure réelle du fichier

### Affichage

Pour chaque item :
- Slug (en gras)
- Scénario
- Source (badge coloré : inject / enrich / localisation)
- Type d'erreur / warning
- Chemin du fichier (copiable)

Pas de bouton "Marquer comme traité" dans la v1 — la résolution se fait dans Obsidian.

---

## Menu déroulant slugs (`slug_select`)

Quand une option est de type `slug_select`, Flask peuple dynamiquement un menu déroulant.

### Comportement
- **Par défaut** : filtré par le scénario sélectionné dans le formulaire (suffixe `_scenarioname`)
- **Option "Tout voir"** : checkbox ou toggle pour afficher tous les slugs sans filtre

### Sources selon `slug_type`

| Valeur | Source |
|--------|--------|
| `instances` | Scan des fichiers `instances/*.md`, lecture du frontmatter `slug` |
| `entities` | Lecture de `_entities_list.json` + scan `instances/*.md` frontmatter |
| `zones` | Lecture de `geographie/{scenario}.md` |

### API Flask

```
GET /api/slugs?type=instances&scenario=effondrement
GET /api/slugs?type=instances&scenario=all
```

Retourne une liste JSON de slugs triés alphabétiquement.

---

## Onglet Config

Formulaire d'édition de `config.json` avec :
- Champ texte pour `vault_root`
- Champ texte pour `pipeline_dir`
- Select pour `default_scenario`
- Bouton "Sauvegarder" → écrit `config.json`
- Bouton "Tester le chemin" → vérifie que `pipeline_dir` existe

---

## Lancement de l'application

```bash
cd /chemin/vers/vault/gui
pip install flask
python3 app.py
# → ouvrir http://localhost:5000 dans Safari
```

---

## Todo list d'implémentation

### Phase 1 — Squelette Flask
- [ ] `app.py` : serveur Flask, routes de base, lecture `config.json`
- [ ] `templates/index.html` : layout barre latérale + zone principale
- [ ] `static/style.css` : styles (dark theme, cohérent avec le prototype)
- [ ] `static/app.js` : navigation entre onglets

### Phase 2 — Formulaires dynamiques
- [ ] Route `GET /api/script/<id>` → retourne la config du script depuis `scripts_config.json`
- [ ] `app.js` : génération dynamique du formulaire depuis la config JSON
- [ ] Tous les types d'options : checkbox, select, number, text
- [ ] `slug_select` : peuplement dynamique via `GET /api/slugs`
- [ ] Logique `requires` : vérification session + affichage avertissement orange

### Phase 3 — Exécution et streaming
- [ ] Route `POST /run` → lance le subprocess, retourne un `run_id`
- [ ] Route `GET /stream/<run_id>` → SSE, stream stdout ligne par ligne
- [ ] Route `POST /stop/<run_id>` → terminate subprocess
- [ ] Sauvegarde log dans `/gui/logs/`
- [ ] Coloration des lignes de log (ok/warn/err)
- [ ] Blocage du bouton Lancer si un script tourne déjà

### Phase 4 — Tableau de bord
- [ ] Route `GET /api/dashboard` → lecture vault, retourne stats JSON
- [ ] Affichage stats : articles, thématiques, géographie, enrichissement
- [ ] Badge revue cliquable

### Phase 5 — Onglet Revue
- [ ] Parser `needs_review.yaml`
- [ ] Parser `needs_review_enrich.yaml`
- [ ] Parser `localisation_review.md` (entrées `review_manuelle`)
- [ ] Affichage unifié avec badges source

### Phase 6 — Onglet Config
- [ ] Formulaire lecture/écriture `config.json`
- [ ] Validation chemin `pipeline_dir`

### Phase 7 — scripts_config.json complet
- [ ] Intégrer tous les scripts avec leurs vraies options
- [ ] À faire après réception du vault mis à jour

---

## Notes importantes pour l'implémentation

- Le vault sera fourni par le développeur pour extraire les vraies valeurs de scénarios, zones, et chemins exacts avant de finaliser `scripts_config.json`
- Les scripts Python existants **ne doivent pas être modifiés** — Flask est une surcouche pure
- macOS High Sierra : éviter toute dépendance système moderne (WebView2, etc.) — Flask + Safari est suffisant
- Le subprocess doit être lancé avec `cwd=pipeline_dir` pour que les imports relatifs des scripts fonctionnent correctement
