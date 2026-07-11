# Manuel utilisateur complet — Pipeline Ourrassol 2098
*Consolidé le 4 juillet 2026 — couvre `generator/` (35 scripts Python) et `gui/` (Flask)*

Ce manuel classe chaque script par rôle : **modules internes** (jamais lancés seuls), **orchestrateurs**, **pipeline entités/événements**, **pipeline géographie**, **validation**, **scripts one-shot/legacy**, et **GUI Flask**. Pour chaque script exécutable : ce qu'il fait, quand l'utiliser, options CLI, statut (répétable / one-shot / legacy), et intégration GUI ou non.

---

## 0. Vue d'ensemble de l'architecture

```
Ourrassol2098/                          ← racine du vault Obsidian
├── generator/                          ← pipeline Python (35 scripts)
│   ├── config.yaml, config_series.yaml
│   ├── state/ (trajectory_usage.json, manual_progress.json, last_validated.json)
│   ├── entites_custom/ (queue.yaml, needs_review.yaml, processed.yaml)
│   ├── evenements_custom/ (queue.yaml, processed.yaml, undo_queue.yaml)
│   └── signaux_custom/ (queue.yaml)
├── gui/                                ← GUI Flask (app.py + frontend)
│   ├── app.py, config.json, scripts_config.json
│   ├── zones_pays.json (+ .bak)
│   ├── static/ (app.js, style.css, pays_mapping.json)
│   ├── templates/ (index.html)
│   └── logs/ (un .log par run SSE)
├── geographie/{scenario}.md            ← 6 bibles géopolitiques
├── entites/, instances/                ← archétypes / instances d'entités
├── evenements/, event_instances/       ← archétypes / instances d'événements
├── variables/, scenarios/, thematiques/
├── articles/{scenario}/                ← sorties de génération
└── documentation/need_action/          ← rapports générés (impact, needs_review, etc.)
```

**Providers LLM** : toutes les tâches passent par `llm_client.py`, qui route vers **Mistral** (défaut, `mistral-small-latest`), **Claude** (`claude-sonnet-4-6`) ou **OpenAI** (`gpt-5.5`, ajouté le 5 juillet) selon `LLM_PROVIDER`/`LLM_MODEL` (env var) ou le réglage GUI (sélecteur générique depuis le 5 juillet, bug #21 — fonctionne pour n'importe quel provider ajouté à `available_providers` sans code spécifique). `mistral-small` reste moins fiable sur le raisonnement géographique (bug #3) et les choix contraints (bug #18, bug #20) — basculer ponctuellement sur Claude/OpenAI pour ce type de tâche, sans changer le défaut global. Retry réactif centralisé sur 429 (bug #17) : aucune pause préventive, s'adapte automatiquement au palier du compte (Free/Scale) pour les trois fournisseurs.

**Convention de statut utilisée ci-dessous :**
- 🔁 **Répétable** — conçu pour être relancé régulièrement, fait partie du flux normal
- 🧩 **GUI** — a une entrée dans `scripts_config.json`, lançable en un clic depuis le sidebar
- 🗄️ **CLI uniquement** — pas encore intégré au GUI
- 🪦 **One-shot / migration** — à lancer une fois, ne devrait plus être relancé
- 📦 **Legacy / archive** — remplacé par un script plus récent, conservé pour référence

---

## 1. Modules internes (jamais lancés directement)

Ces fichiers sont importés par les scripts exécutables ; ils n'ont pas de `__main__` orienté utilisateur.

| Module | Rôle |
|---|---|
| `loader.py` | Lit/parse les fichiers `.md` du vault (frontmatter YAML + corps). Définit `VAULT_PATH`, `PATHS`, `VALID_VARS`, `VALID_SCENARIOS`. Point d'entrée de toute lecture du vault. |
| `snapshot.py` | Construit le "snapshot" cohérent du monde 2098 pour un scénario : niveaux de variables, cohérence via la matrice d'influence, ruptures/jalons 2025→2098. |
| `prompt_builder.py` | Assemble le prompt complet (system + user) envoyé au LLM pour générer un article, à partir du snapshot, de la thématique et de `config.yaml`. Contient les 12 profils de journaux (2/scénario). |
| `api.py` | Envoie le prompt au LLM configuré (Claude ou Mistral, via `llm_client.py`) et sauvegarde l'article généré en `.md` dans `articles/`. |
| `llm_client.py` | Abstraction unifiée Claude/Mistral. `LLM_PROVIDER` (env, défaut `mistral`), `LLM_MODEL` (env, override du modèle par défaut). Exporte `call_llm()`. |

---

## 2. Orchestrateurs — génération d'articles

### `generate.py` 🔁 🧩
Point d'entrée unique pour générer **un seul article**. Lit `config.yaml` (scénario, thématique, options), orchestre loader → snapshot → prompt_builder → api, sauvegarde dans `articles/`.
```bash
python3 generate.py
```
Aucun argument CLI — tout se règle dans `config.yaml`.

### `generate_series.py` 🔁 🧩
Génère une **série d'articles** sur plusieurs thématiques avec cohérence temporelle, pilotée par `config_series.yaml`.
```bash
python3 generate_series.py                    # utilise config_series.yaml
python3 generate_series.py --dry-run          # sans appel API
python3 generate_series.py --scenario breakdown
python3 generate_series.py --validate-first   # valide la base avant de générer
```
Sortie : `articles/{scenario}/` + `articles/{scenario}/_index.md`.

### `generate_manual.py` 🔁 🧩
Pipeline **sans appel API** : construit le prompt du prochain article de la série et l'affiche pour copier/coller dans un chat Claude. Utile pour évaluer le contenu à la main avant d'industrialiser.
```bash
python3 generate_manual.py prompt          # affiche system+user prompt, avance la série
python3 generate_manual.py status          # état de la série en cours
python3 generate_manual.py save fichier.txt # sauvegarde l'article collé depuis le chat
```
État de rotation dans `state/manual_progress.json` (mode "prévisualisation" par défaut : chaque `prompt` avance sans sauvegarder tant que `save` n'est pas appelé).

### `generate_journaux.py` 🔁 🧩
Génère `journaux.yaml` (éditions locales par zone) depuis les bibles géographiques. Une entrée par zone N1 × ligne éditoriale contient : `nom` (nom du journal), `ton`, `langue_style` (registre culturel/linguistique, vide sauf justification par la zone elle-même), et `journalistes` — une rédaction de **6 journalistes**, chacun couvrant une ou plusieurs des 20 thématiques du projet (toutes couvertes collectivement ; plusieurs thématiques peuvent partager un même journaliste). `prompt_builder.py` choisit automatiquement le bon journaliste selon la thématique de l'article généré, pour une signature cohérente.
```bash
python3 generate_journaux.py --scenario NOM   # ou --all
python3 generate_journaux.py --ligne pro_pouvoir|opposition|all
python3 generate_journaux.py --update             # n'ajoute que les zones manquantes
python3 generate_journaux.py --fill-journalistes  # complète uniquement le champ "journalistes" des zones qui ne l'ont pas encore, sans toucher à nom/ton/langue_style
python3 generate_journaux.py --dry-run
```
⚠️ Lots de 3 zones par appel (réduit de 5 le 6 juillet — des lots plus grands tronquaient le JSON avec la rédaction de 6 journalistes), `max_tokens=8000`. Fallback silencieux sur échec de lot : écrit quand même une entrée (vide pour `--update`, ou laisse `journalistes: []` pour `--fill-journalistes` sans toucher au reste) — voir bugs #22/#24 du handoff. Après tout run partiellement échoué avec `--update` (pas `--fill-journalistes`), lancer `clean_fallback_journaux.py` avant de relancer.

### `check_journaux_coherence.py` 🔁 🗄️ — diagnostic pur (livré le 5 juillet)
Compare les zones N1 réelles de la géographie aux entrées de `journaux.yaml`, dans les deux sens (manquantes/orphelines), pour les 6 scénarios × 2 lignes. Aucune écriture.
```bash
python3 check_journaux_coherence.py
```

### `clean_fallback_journaux.py` 🔁 🗄️ — livré le 5 juillet
Retire de `journaux.yaml` les entrées placeholder laissées par le fallback silencieux de `generate_journaux.py --update` en cas d'échec de lot (signature : `nom` commence par "Édition ", `ton`/`langue_style` vides). À lancer avant de relancer `--update` après un run partiellement échoué.
```bash
cp journaux.yaml journaux.yaml.bak
python3 clean_fallback_journaux.py
```

---

## 3. Pipeline entités & événements custom

### `create_entities_and_instances.py` 🔁 🧩 — **script recommandé actuel**
Fusion de `create_entity.py` + `generate_instances.py` (les deux anciens scripts restent en archive). Crée une entité **et** génère automatiquement ses instances dans le même run.
Deux modes interactifs au lancement :
- **custom** — décrit une instance précise dans `entites_custom/queue.yaml` ; Claude déduit l'archétype, crée l'entité, puis enchaîne la génération des instances (scénario de référence contraint, les autres libres).
- **auto** / **auto-suggest** — génération assistée ou automatique de N entités nouvelles.
```bash
python3 create_entities_and_instances.py           # interactif
python3 create_entities_and_instances.py --dry-run
```
Auto-lance en fin de run le cycle post-injection (`extract_localisation → review_localisation --auto-resolve → validate.py`) si au moins une entité/instance a été créée.

### `inject_custom_events.py` 🔁 🧩
Injecte des événements custom fournis par l'utilisateur dans `evenements_custom/queue.yaml` : crée l'archétype (`evenements/{slug}.md`) + une instance par scénario sélectionné (`event_instances/{slug}_{scenario}.md`). Batch/non-interactif.
```bash
python3 inject_custom_events.py             # interactif (modes custom|auto)
python3 inject_custom_events.py --dry-run
```
`main()` écrit séparément dans `processed.yaml` (statut `partial` si succès partiel) et `needs_review.yaml`.

### `inject_custom_signals.py` 🔁 🧩
Injecte des signaux faibles custom (`signaux_custom/queue.yaml`) dans les fiches variables, au format `signal_to_state` (6 scénarios) + annotation section 7. Validation mécanique (comptage de mots, fenêtres de dates, collisions), jusqu'à 2 retries.
```bash
python3 inject_custom_signals.py
python3 inject_custom_signals.py --dry-run
```

### `enrich_minimal.py` 🔁 🧩
Enrichit les fiches `statut: officialise_minimal` via l'API Claude (génère `responsabilites`, `description_journalistique`, `tensions_narratives`, `localisation`, impacts, `alliances`/`oppositions`, etc.), avec validation bloquante (2 retries).
```bash
python3 enrich_minimal.py --scenario NOM       # ou --all, ou --slug SLUG
python3 enrich_minimal.py --dry-run
python3 enrich_minimal.py --limit N
python3 enrich_minimal.py --auto-cycle         # enchaîne extract_phantom_slugs (+ wave 2 via validate --verbose)
```
Sorties : `enrich_minimal_report.md`, `needs_review_enrich.yaml`. Coût estimé pour les 426 fiches restantes (P8) : ~$37.

### `extract_phantom_slugs.py` 🔁 🧩
Lit `enrich_minimal_report.md` et/ou une sortie `validate.py --verbose`, génère les rôles manquants via API, alimente `entites_custom/queue.yaml` (batches de 5, dédupliqués).
```bash
python3 extract_phantom_slugs.py                   # source=all (défaut)
python3 extract_phantom_slugs.py --source enrich|validate
python3 extract_phantom_slugs.py --dry-run
python3 extract_phantom_slugs.py --report PATH
```

### `fix_alliance_suffixes.py` 🔁 🧩
Correction **mécanique, sans API** : ajoute le suffixe `_{scenario}` manquant dans les champs `alliances`/`oppositions`.
```bash
python3 fix_alliance_suffixes.py --dry-run
python3 fix_alliance_suffixes.py
python3 fix_alliance_suffixes.py --scenario fortress_world
python3 fix_alliance_suffixes.py --verbose
```

### `requeue_needs_review.py` 🔁 🧩
Remet les entrées de `entites_custom/needs_review.yaml` dans `queue.yaml` pour une nouvelle tentative.
```bash
python3 requeue_needs_review.py --dry-run
python3 requeue_needs_review.py
```

### `undo_custom.py` 🔁 🧩
Retire proprement des entités/instances/événements/event_instances, avec gestion des dépendances et backup `.bak` automatique. Dry-run par défaut.
```bash
python3 undo_custom.py                       # dry-run depuis evenements_custom/undo_queue.yaml
python3 undo_custom.py --execute
python3 undo_custom.py --slug SLUG --type TYPE --generalisation yes|no [--execute]
```
`generalisation: no` = supprime la fiche ciblée + dépendances directes ; `yes` = supprime l'archétype + toutes ses instances scénario. Réinitialise `last_validated.json`, nettoie `_entities_list.json`.

---

## 4. Pipeline géographie

### `build_geographie_monde.py` 🔁 🧩 — **étape 1**
Rétro-construit la bible géopolitique plate d'un scénario à partir du contenu narratif existant (instances, événements custom), pour servir de référentiel et éviter la dérive de nomenclature (ex. 33 variantes de "bloc eurasien" trouvées avant ce script).
```bash
python3 build_geographie_monde.py --scenario NOM   # ou --all
python3 build_geographie_monde.py --dry-run
python3 build_geographie_monde.py --force           # régénère tout le fichier (écrase)
```

### `enrich_geographie_recursive.py` 🔁 🧩 — **étape 2**
Ajoute un maillage hiérarchique de sous-zones (profondeur libre) sous les zones N1 déjà construites par l'étape 1. **Principe additif** : ne touche jamais aux zones déjà présentes, ne fait qu'ajouter.
```bash
python3 enrich_geographie_recursive.py --scenario NOM   # ou --all
python3 enrich_geographie_recursive.py --dry-run
```

### `complete_geographie_coverage.py` 🔁 🧩 — **étape 3, workflow obligatoire review→apply**
Garantit que chaque pays de `zones_pays.json` a une zone N1 dans chaque scénario. Pour chaque pays sans zone : le LLM choisit "absorber" (zone existante) ou "nouvelle_zone". Batch de 12 pays, délai de 8s entre batches (rate limiting, depuis le 4 juillet).
```bash
python3 complete_geographie_coverage.py --scenario NOM --review   # génère coverage_proposals_NOM.yaml, n'écrit rien
# → valider dans VS Code, mettre valide:false sur les propositions incohérentes
python3 complete_geographie_coverage.py --scenario NOM --apply    # écrit dans la fiche + zones_pays.json
python3 complete_geographie_coverage.py --all [--dry-run]
```
⚠️ Ne jamais interrompre un run en cours (rate limiting). Ne jamais enchaîner `--apply` sur plusieurs scénarios sans relecture intermédiaire du fichier de propositions.

### `extract_localisation.py` 🔁 🧩
Extrait le champ `localisation` (zone/lieu/type_lieu) sur les fiches riches (hors `officialise_minimal`) + toutes les `event_instances`. Trois issues : lieu trouvé, transnational (vide assumé), ou ambigu (`statut: review_manuelle`).
```bash
python3 extract_localisation.py --dry-run
python3 extract_localisation.py
python3 extract_localisation.py --scenario NOM
python3 extract_localisation.py --slug SLUG
python3 extract_localisation.py --force          # retraite les fiches déjà faites
python3 extract_localisation.py --report-only
```

### `review_localisation.py` 🔁 🧩
Review interactive des fiches `statut: review_manuelle`, une par une : `[V]` valider la suggestion, `[C]` choisir une autre zone, `[0]` vide assumé, `[S]` skip.
```bash
python3 review_localisation.py
python3 review_localisation.py --scenario NOM
python3 review_localisation.py --auto-resolve    # mode non-interactif (post-injection auto-cycle)
python3 review_localisation.py --dry-run
```

### `check_zones_coherence.py` 🔁 🗄️ — **diagnostic pur, lecture seule**
Vérifie : (1) parsing YAML valide des fiches `geographie/{scenario}.md`, (2) pays réels totalement absents de toute zone, (3) pays rattachés uniquement à une sous-zone sans N1, (4) entrées obsolètes dans `zones_manquantes.yaml`. Ne modifie jamais rien.
```bash
python3 check_zones_coherence.py --scenario NOM
python3 check_zones_coherence.py --all
```
Réflexe recommandé : lancer `--all` en fin de session, après tout `--apply` ou toute série de bascules sur la carte. Non intégré au GUI (backlog P11).

### `regenerate_zones_pays.py` 🔁 🗄️
Reconstruit intégralement `gui/zones_pays.json` depuis les fiches `geographie/*.md` (source de vérité), avec les mêmes alias tolérants que `check_zones_coherence.py`. À relancer si ce dernier détecte des pays "totalement absents" après un `--apply` qui semblait pourtant tout couvrir (signe de désynchronisation `zones_pays.json` / fiches réelles). Backup `.json.bak` automatique.
```bash
python3 regenerate_zones_pays.py --dry-run
python3 regenerate_zones_pays.py
```

### `add_pays_to_zone.py` 🔁 🗄️
Ajoute un ou plusieurs pays à l'`origine_reelle` d'une zone **existante** (ne crée jamais de zone). Cas d'usage typique : rattacher à sa vraie zone N1 un pays détecté par `check_zones_coherence.py` comme "sous-zone sans N1". Backup `.bak`.
```bash
python3 add_pays_to_zone.py --scenario NOM --zone SLUG_ZONE --pays Mali Niger Tchad
python3 add_pays_to_zone.py ... --dry-run
```

### `merge_pays_monde.py` 🪦 (one-shot, déjà exécuté) 🗄️ — vit dans `gui/`
Étend `zones_pays.json` pour couvrir ~198 pays du monde (au lieu du sous-ensemble initial), sans toucher aux affectations existantes. Backup automatique. Déjà lancé lors de la construction de la carte — à ne relancer que si de nouveaux pays doivent être ajoutés à la liste de référence.
```bash
python3 merge_pays_monde.py
```

### `restructure_zones.py` ⚪ **planifié, pas encore codé (P7)**
Référencé dans `scripts_config.json` (sidebar GUI, section maintenance) mais le fichier n'existe pas encore dans `generator/`. Objectif : split/merge/reparent/rename de zones N1 avec propagation complète (`instance.localisation.zone`, `event_instance.localisation.zone`, `zones_proposees.yaml`, `parent` dans les fiches, wikilinks éventuels, `registre_evenements.md`). Distinct de l'onglet Carte, qui gère déjà les bascules pays→zone individuelles. Questions ouvertes avant codage : présence de wikilinks vers des slugs de zones dans le vault ? `registre_evenements.md` référence-t-il des zones ?

---

## 5. Validation

### `validate.py` 🔁 🧩 — **à lancer avant toute génération**
Vérifie la cohérence complète de la base (9 sections) : nomenclature, cohérence systémique (levels/états/trajectoires), cohérence entités/instances, cohérence thématique, wikilinks cassés, matrice d'influence, événements, et section 9 — **cohérence narrative** (acteurs actifs vs suffixe scénario, delta overflow [-20,130], cohérence des dates d'instances).
```bash
python3 validate.py                 # validation complète
python3 validate.py --verbose / -v  # détail terminal
python3 validate.py --report / -r   # génère validation_report.md (lisible dans Obsidian)
python3 validate.py --localisation  # filtre section localisation
python3 validate.py --narrative / -n # force le scan narratif même si event_instances n'a pas changé
```
Le scan narratif (section 9) est conditionnel par défaut (déclenché seulement si `event_instances/` a changé depuis `state/last_validated.json` — utiliser `-n` pour forcer). Rapport localisé : `documentation/need_action/narrative_issues.yaml`.
Filtrage narratif seul : `python3 validate.py --verbose 2>&1 | grep "narrative"`.

---

## 6. Scripts one-shot / migration / legacy

Ces scripts ont rempli leur rôle ponctuel ou ont été remplacés — à ne relancer que dans un cas précis documenté ci-dessous, jamais en routine.

| Script | Rôle | Statut |
|---|---|---|
| `create_entity.py` | Ancienne brique 1/2 (création d'entité seule, sans instances). Remplacé par `create_entities_and_instances.py`. | 📦 Legacy — conservé pour référence |
| `generate_instances.py` | Ancienne brique 2/2 (génération d'instances pour entités déjà créées). Fusionnée dans `create_entities_and_instances.py`. | 📦 Legacy |
| `generate_entities.py` | Tout premier script de génération d'entités+instances (`--entities-only`, `--entity`, `--scenario`). Antérieur même à `create_entity.py`. | 📦 Legacy, archive historique |
| `migrate_registre.py` | Migration unique de `registre_evenements.md` de l'ancien format 5 colonnes vers le nouveau format hybride 6 colonnes (accueillant aussi les événements custom). | 🪦 One-shot, déjà exécuté |
| `officialize_alliances.py` | Phase 1 du chantier alliances/oppositions : dédupliquer sémantiquement les mentions en texte libre et les convertir en slugs réels. `--limit`, `--resume`. | 🪦 One-shot (chantier terminé), garder pour référence si de nouvelles fiches en texte libre apparaissent |
| `fix_impact_scale.py` | Corrige rétroactivement `impact_local`/`impact_systemique_global` hors [0-5] (résidu d'un bug de prompt de `generate_entities.py`). | 🪦 One-shot, déjà exécuté |
| `fix_lieux_residuels.py` | Nettoie un résidu mécanique de doublons `lieux_emblematiques` laissé par une version antérieure de `enrich_geographie_recursive.py` (avant fix de `dedupe_promoted_lieux`). `--scenario`/`--all`, `--dry-run`. | 🪦 One-shot ponctuel, ne relancer que si le même symptôme (lieu dupliqué sur plusieurs zones) réapparaît |
| `rebuild_processed.py` | Reconstruit les entrées manquantes de `processed.yaml` pour des événements custom géo injectés manuellement (source `rééquilibrage_geo_2026-06`) non tracés. | 🪦 One-shot, déjà exécuté |
| `check_arctique.py` | Snippet de debug ad hoc (grep de "arctique" dans `policy_reform.md`), chemin en dur, pas de CLI. | 📦 Snippet jetable, ne pas industrialiser |
| `remove_zone_manquante.py` | Snippet ad hoc : retire une entrée précise (Arctique/policy_reform) de `zones_manquantes.yaml`, chemin en dur. | 📦 Snippet jetable, déjà exécuté |

---

## 7. GUI Flask — `gui/app.py`

### Lancement
```bash
lsof -ti:5000 | xargs kill -9        # libérer le port si occupé
cd .../Ourrassol2098/gui
python3 app.py                        # ou : ./start.sh / alias `ourrassol` / Ourrassol2098.app
```
`start.sh` (zsh) source `~/.zshrc` (charge `MISTRAL_API_KEY` et autres variables) puis lance `python3 app.py` depuis `gui/`.

Config : `gui/config.json` (`vault_root`, `pipeline_dir`, `default_scenario`, `scenarios`, `llm.provider`/`model_mistral`/`model_claude`). Clés API dans `gui/.env` (gitignored) — chargées manuellement par `_load_dotenv()` au démarrage de `app.py` (pas besoin de `source ~/.zshrc` pour le GUI lui-même, seulement pour les scripts lancés directement en terminal).

### `check_session.sh` 🔁 — smoke-test de fin de session (shell, pas Python)
À lancer depuis `gui/` en fin de session, avant d'écrire le handoff. Ne modifie rien, ne fait qu'auditer :
1. `certifi` installé (bug SSL connu sur le bouton LLM de la carte)
2. JSON valide pour `static/pays_mapping.json` et `zones_pays.json`
3. Port 5000 occupé ou non (Flask lancé ou pas)
4. Si Flask tourne : ping `GET /api/carte/affectations?scenario=...` et vérifie un `200`
5. Pays de `zones_pays.json` absents de `pays_mapping.json` (mapping FR→EN utilisé par la carte)
6. Affiche une **checklist manuelle non automatisable** (4 items : bouton LLM carte testé en vrai, bandeau diagnostic orange lu, hachures de zone vérifiées visuellement sur un scénario à beaucoup de zones N1, rapport d'impact testé sur un cas réel). Consigne intégrée au script : toute ligne non cochée doit être recopiée telle quelle en tête du prochain backlog, pas reformulée.
```bash
./check_session.sh              # scénario de test par défaut : breakdown
./check_session.sh reference    # cible un autre scénario pour le ping de route
```

### Structure des fichiers `gui/` (mise à jour 4 juillet — P5)
`app.py` reste le point d'entrée, mais n'est plus monolithique : `/api/dashboard` et ses 8 fonctions de calcul de stats (`_stats_articles`, `_stats_instances`, `_stats_entites`, `_stats_journaux`, `_stats_enrichissement`, `_stats_thematiques`, `_stats_zones`, `_count_review_items`) vivent désormais dans **`gui/routes_dashboard.py`**, un Blueprint Flask enregistré via `app.register_blueprint(dashboard_bp)` juste après la création de `app`. Objectif : ce bloc était régulièrement écrasé par erreur lors de patches sur d'autres parties de `app.py` (carte, coverage) du simple fait de sa position au milieu du fichier. Toutes les autres routes restent dans `app.py`.

### Sidebar (`scripts_config.json`) — scripts lançables en un clic
**Section génération** : `enrich_minimal`, `generate_journaux`, `validate`, `generate`, `generate_series`, `generate_manual`.
**Section entités** : `create_entities`, `inject_events`, `inject_signals`, `extract_phantom_slugs`, `fix_alliance_suffixes`, `requeue_needs_review`, `undo_custom`.
**Section maintenance** : `extract_localisation`, `review_localisation`, `build_geographie`, `enrich_geographie`, `complete_geographie_coverage`, `restructure_zones` (⚠️ script pas encore codé, entrée présente mais échouera si lancée).

Chaque entrée définit ses options (checkbox/select/number/slug_select), ses dépendances (`requires`) et les fichiers YAML associés affichables dans le panneau de review.

### Routes API principales
| Route | Méthode | Rôle |
|---|---|---|
| `/` | GET | Sert `templates/index.html` (SPA) |
| `/api/config` | GET/POST | Lit/écrit `config.json`. Le POST préserve les clés `llm.available_*` (fix du 4 juillet, bug #14 — l'ordre de préservation était inversé avant) |
| `/api/scripts` | GET | Liste des scripts configurés (sidebar) |
| `/api/script/<id>` | GET | Détail d'un script (options, requires) |
| `/api/yaml` | GET/POST | Lecture/écriture d'un fichier YAML du vault (éditeur GUI, `.bak` auto). Résout les chemins relatifs par rapport à **`vault_root`** (fix du 4 juillet, bug #16 — résolvait avant par rapport à `pipeline_dir`, rendant inatteignables `entites_custom/`, `evenements_custom/`, `signaux_custom/`, `instances_custom/`) |
| `/api/yaml/form` | POST | Écriture structurée via formulaire (ex. queue.yaml). Même fix `vault_root` (bug #16) |
| `/api/yaml/append` | POST | Ajoute une entrée à un YAML existant. Même fix `vault_root` (bug #16) |
| `/api/zones/pays-liste` | GET | Liste complète des pays de référence |
| `/api/zones/manquantes` | GET/POST | Lit/MAJ `documentation/need_action/zones_manquantes.yaml` |
| `/api/zones/recheck` | POST | Relit la fiche géographie à jour, purge les entrées résolues de `zones_manquantes.yaml` |
| `/api/zones/lookup` | GET | Cherche la zone 2098 d'un pays 2026 pour un scénario (confiance haute/moyenne/nulle) |
| `/api/carte/affectations` | GET | Zones N1 (couleurs stables) + affectation de chaque pays, pour la carte Leaflet |
| `/api/carte/propose` | POST | Appel LLM unique : propose une zone pour un pays donné |
| `/api/carte/assign` | POST | Applique la bascule pays→zone (absorber ou créer une nouvelle zone) |
| `/api/carte/ignorer` | POST | Marque un pays "blanc intentionnel" pour le scénario |
| `/api/carte/impact` | POST | Génère le rapport d'impact en lecture seule avant confirmation (obligatoire) |
| `/api/slugs` | GET | Autocomplétion de slugs (pour `slug_select` dans les formulaires) |
| `/api/dashboard` | GET | Statistiques du vault (compteurs fiches, cohérence). Depuis le 4 juillet (P5), vit dans `gui/routes_dashboard.py` (Blueprint Flask), plus dans `app.py` — voir note ci-dessous |
| `/api/review` | GET | Panneau de review des fiches en attente. Cherche dans `vault_root` (fix du 4 juillet, bug #15 — cherchait avant dans `pipeline_dir`, ne remontait jamais rien) |
| `/api/run` | POST | Lance un script en sous-processus, retourne un `run_id` |
| `/api/stream/<run_id>` | GET | SSE — flux de logs en direct du run |
| `/api/stop/<run_id>` | POST | Arrête un run en cours |
| `/api/status` | GET | État global (runs actifs, etc.) |

### Onglet Carte — workflow détaillé
*(fusionné depuis `USER_MANUAL_carte_et_couverture_4juillet.md`, mis à jour avec les correctifs du 4 juillet)*

**À quoi ça sert** : affecter un pays à une zone N1 d'un scénario, en visualisant l'impact narratif avant de confirmer — pensé pour un pays à la fois (contrairement à `complete_geographie_coverage.py`, pensé pour du traitement en masse).

**Workflow pas à pas :**
1. Ouvrir le GUI (`http://localhost:5000`), onglet **🗺️ Carte**
2. Choisir le scénario en haut
3. Cliquer sur un pays sur la carte (gris = non affecté, coloré = déjà affecté)
4. Dans le panneau latéral, deux options :
   - **Sélection manuelle** d'une zone N1 existante dans la légende
   - **"Demander une proposition (LLM)"** — le modèle configuré (voir ci-dessous) propose une zone avec justification
5. **"🔍 Évaluer l'impact"** — obligatoire, le bouton de confirmation n'apparaît qu'après. Génère un rapport en lecture seule (sous-zones orphelines, instances/événements liés, mentions textuelles), sauvegardé dans `documentation/need_action/impact_bascule_{pays}_{scenario}.md`
6. Confirmer la bascule

**Cas particulier : Royaume-Uni** — `Royaume-Uni` / `Angleterre` / `Écosse` / `Pays de Galles` correspondent à 4 entrées `pays_liste` pour un seul polygone GBR sur le fond de carte. Un sélecteur intermédiaire apparaît au clic.

**Bouton "🚫 Ignorer"** — marque un pays comme "blanc intentionnel" : il reste dans `zones_manquantes.yaml` avec un statut dédié, mais disparaît de la vue "zones manquantes" du dashboard. Utile pour les pays qu'on ne veut délibérément pas traiter.

**Bandeau diagnostic orange** — `#carte-diagnostic`, conditionnel : ne s'affiche que s'il existe des pays FR sans correspondance trouvée sur le fond de carte Leaflet (noms mal mappés dans `gui/static/pays_mapping.json`). Absence de bandeau = pas de problème de mapping actuellement.

### Choix du modèle LLM (carte + `complete_geographie_coverage.py`)
Depuis le fix du 4 juillet (bugs #12/#14), le sélecteur de modèle du GUI fonctionne réellement — provider et modèle se choisissent en un clic, sans éditer `config.json` à la main. Défaut confirmé : `mistral` / `mistral-small-latest`.

| Provider | Modèles disponibles dans le sélecteur |
|---|---|
| Mistral | `mistral-small-latest` (défaut), `mistral-large-latest` |
| Claude | `claude-sonnet-4-6` (défaut), `claude-sonnet-5`, `claude-opus-4-8`, `claude-haiku-4-5-20251001` |

`mistral-small-latest` reste moins fiable que Claude sur le raisonnement géographique (confabule parfois avec confiance, cf. bug #3 du handoff) — basculer ponctuellement sur `claude-sonnet-4-6`/`claude-sonnet-5` depuis le sélecteur pour une session carte/coverage si besoin, sans changer le défaut global.

### Résumé des commandes courantes
```bash
# Lancer le GUI
lsof -ti:5000 | xargs kill -9
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py

# Charger la clé API si besoin (scripts lancés en terminal — pas le GUI)
source ~/.zshrc

# Traiter un scénario avec complete_geographie_coverage.py
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/generator"
python3 complete_geographie_coverage.py --scenario NOM --review
code coverage_proposals_NOM.yaml
python3 complete_geographie_coverage.py --scenario NOM --apply

# Vérifier la cohérence
python3 check_zones_coherence.py --all
```

### Bug récurrent connu
Confusion `pipeline_dir` (= `generator/`) vs `vault_root` (racine du vault) dans `app.py` — `geographie/` vit à `vault_root`, pas dans `pipeline_dir`. Vérifier ce point en priorité en cas de nouveau bug carte/coverage. Même famille de confusion trouvée le 4 juillet dans `check_session.sh` (bug #11 du handoff) — toujours vérifier `$GUI_DIR` vs `$VAULT_DIR`/`generator` en cas de chemin suspect.
