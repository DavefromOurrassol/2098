# Manuel utilisateur complet — Pipeline Ourrassol 2098
*Consolidé le 15 juillet 2026 — couvre `generator/` (39+ scripts Python) et `gui/` (Flask)*

Ce manuel classe chaque script par rôle : **modules internes** (jamais lancés seuls), **orchestrateurs**, **pipeline entités/événements**, **pipeline géographie**, **validation**, **scripts one-shot/legacy**, et **GUI Flask**. Pour chaque script exécutable : ce qu'il fait, quand l'utiliser, options CLI, statut (répétable / one-shot / legacy), et intégration GUI ou non.

---

## 0. Vue d'ensemble de l'architecture

```
Ourrassol2098/                          ← racine du vault Obsidian
├── generator/                          ← pipeline Python (35+ scripts)
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

**Providers LLM et routing par tier (depuis le 11 juillet)** : toutes les tâches passent par `llm_client.py`, qui route vers **Mistral**, **Claude** ou **OpenAI** selon deux mécanismes complémentaires :

1. **Routing par tier** (comportement par défaut) — chaque script passe un `task_tier` à `call_llm()`, résolu automatiquement via `TASK_TIER_DEFAULTS` selon la nature de la tâche :

   | Tier | Modèle par défaut | Usage typique |
   |---|---|---|
   | `strict` | `mistral-large-latest` *(→ `claude-sonnet-5` prévu en prod)* | Identité/fidélité imposée sur sortie longue et créative (articles, journalistes) |
   | `structured_strict` | `mistral-large-latest` | Sortie JSON canonique référencée ailleurs dans le vault (entités, instances, géographie) |
   | `creative_souple` | `mistral-large-latest` | Rédaction/enrichissement libre, sans contrainte d'identité tierce |
   | `volume` | `mistral-small-latest` | Extraction, classification, résolution courte — gros volume, faible enjeu par erreur |

2. **Override manuel** (`LLM_PROVIDER`/`LLM_MODEL` en variable d'environnement, ou toggle GUI "Forcer ce modèle") — priorité absolue sur le tier, pour un test ponctuel sans changer le comportement par défaut. Jamais destiné à un usage permanent (ne pas mettre en `export` fixe dans `.zshrc`).

Retry réactif centralisé sur 429 : aucune pause préventive, s'adapte automatiquement au palier du compte (Free/Scale) pour les trois fournisseurs. Les **18 scripts** du pipeline qui utilisent un LLM sont désormais tous unifiés sous `llm_client.py` (seul `restructure_zones.py` reste hors système, car pas encore codé — voir §4).

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
| `snapshot.py` | Construit le "snapshot" cohérent du monde 2098 pour un scénario : niveaux de variables, cohérence via la matrice d'influence, ruptures/jalons 2025→2098. Calcule aussi `zone_slug` par défaut (`_dominant_zone`, vote majoritaire sur les instances filtrées) — **utilisé seulement en repli**, un `zone_slug` explicite dans `config.yaml` prime toujours dessus depuis le 11 juillet (bug #26). |
| `prompt_builder.py` | Assemble le prompt complet (system + user) envoyé au LLM pour générer un article, à partir du snapshot, de la thématique et de `config.yaml`. Contient les 12 profils de journaux (2/scénario). Priorité de `zone_slug` inversée le 11 juillet : `config.get('zone_slug') or snapshot.get('zone_slug')`. |
| `api.py` | Envoie le prompt au LLM configuré (tier `strict`, via `llm_client.py`) et sauvegarde l'article généré en `.md` dans `articles/`. Le champ `model:` du frontmatter reflète désormais le tier réellement résolu (`resolve_for_tier()`), pas une variable statique. |
| `llm_client.py` | Abstraction unifiée Mistral/Claude/OpenAI. `LLM_PROVIDER`/`LLM_MODEL` (env, override manuel prioritaire). `TASK_TIER_DEFAULTS` + `resolve_for_tier(task_tier)` pour le routing par défaut. Exporte `call_llm(..., task_tier=...)`. |
| `extract_state_logic.py` *(14 juillet)* | Parseur générique `variables/{variable}.md → states.{scenario}.state_logic`. Sanitise les clés wikilink Obsidian (`[[xxx]]`) des blocs `coupling_intensity` avant `yaml.safe_load` (sinon `unhashable key`). Utilisable en CLI (`--json`, `--scenario`) ou en import (`extract_state_logic(path)`). |
| `patrons_spatiaux.py` *(14 juillet)* | Source de vérité du patron spatial par scénario, pour P24 (générateur top-down) et P22 signal 2 (garde-fou étendu). `state_logic`/`state_logic_complementaire` chargés dynamiquement depuis le vault à chaque import via `extract_state_logic.py` (jamais figés en dur) ; `patron_a_respecter`/`a_eviter` écrits à la main dans `_ANALYSE`, à revalider si un scénario change en profondeur. Config : `OURRASSOL_VAULT_ROOT` (env), sinon déduit de l'emplacement du fichier. **Consommé depuis le 15 juillet par `complete_geographie_coverage.py`** (P24 étape B, voir §4) via `patron_spatial_prompt_block()`. |

---

## 1bis. Utilitaires partagés entre scripts de diagnostic géographie

| Fonction | Vit dans | Rôle |
|---|---|---|
| `_tokens()` | `check_origine_reelle_coherence.py` | Découpe une chaîne `entite` en tokens comparables à un nom de pays (gère parenthèses, virgules, slashes). Réutilisée par `check_conventions_territoires.py` et `check_type_entite_coherence.py` (import direct). |
| `_normaliser()` | `check_origine_reelle_coherence.py` | Ramène une variante de nom de pays à sa forme canonique, via `ALIASES` importé de `check_zones_coherence.py` (source unique). |
| `_compte_comme_pays()` | `check_origine_reelle_coherence.py` | Détermine si une entrée `origine_reelle` compte comme un pays : `type_entite: pays` → toujours ; `type_entite: ville` → jamais ; tout le reste (absent, `region_administrative`, `autre`) → si le nom correspond exactement à une entrée de `zones_pays.json`. |

⚠️ **`gui/app.py` ne peut pas importer ces fonctions** (codebase séparée de `generator/`) — `_tokens_entite()`/`_normalise_pays()` dans `app.py` sont des copies fonctionnelles indépendantes, pour le split de zone (§7). Si la logique de tokenisation évolue d'un côté, vérifier si l'autre doit suivre.

---

## 2. Orchestrateurs — génération d'articles

### `generate.py` 🔁 🧩
Point d'entrée unique pour générer **un seul article**. Lit `config.yaml` (scénario, thématique, options), orchestre loader → snapshot → prompt_builder → api, sauvegarde dans `articles/`.
```bash
python3 generate.py
python3 generate.py --dry-run   # géré via sys.argv brut, pas argparse — fonctionne malgré tout
```
`validate_config()` vérifie désormais (11 juillet, bug #26) que `zone_slug` — si fourni dans `config.yaml` — existe réellement dans `journaux.yaml` pour le scénario/ligne éditoriale concernés ; sinon erreur claire listant les zones valides, plutôt qu'une résolution silencieuse vers la mauvaise zone.

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
Pipeline **sans appel API** : construit le prompt du prochain article de la série et l'affiche pour copier/coller dans un chat Claude.ai. Utile pour évaluer le contenu à la main avant d'industrialiser. *(Seul script du pipeline où les mentions "Claude" dans le code sont intentionnelles — ce workflow est spécifiquement pensé pour l'interface de chat Claude.ai, hors abstraction `llm_client.py`.)*
```bash
python3 generate_manual.py prompt          # affiche system+user prompt, avance la série
python3 generate_manual.py status          # état de la série en cours
python3 generate_manual.py save fichier.txt # sauvegarde l'article collé depuis le chat
```
État de rotation dans `state/manual_progress.json` (mode "prévisualisation" par défaut : chaque `prompt` avance sans sauvegarder tant que `save` n'est pas appelé).

### `generate_journaux.py` 🔁 🧩
Génère `journaux.yaml` (éditions locales par zone) depuis les bibles géographiques. Une entrée par zone N1 × ligne éditoriale contient : `nom` (nom du journal), `ton`, `langue_style` (registre culturel/linguistique, vide sauf justification par la zone elle-même), et `journalistes` — une rédaction de **6 journalistes**, chacun couvrant une ou plusieurs des 20 thématiques du projet (toutes couvertes collectivement ; plusieurs thématiques peuvent partager un même journaliste). `prompt_builder.py` choisit automatiquement le bon journaliste selon la thématique de l'article généré, pour une signature cohérente. Tier `strict` depuis le 11 juillet (source de vérité injectée dans tous les articles en aval — une incohérence ici se propage partout).
```bash
python3 generate_journaux.py --scenario NOM   # ou --all
python3 generate_journaux.py --ligne pro_pouvoir|opposition|all
python3 generate_journaux.py --update             # n'ajoute que les zones manquantes
python3 generate_journaux.py --fill-journalistes  # complète uniquement le champ "journalistes" des zones qui ne l'ont pas encore, sans toucher à nom/ton/langue_style
python3 generate_journaux.py --dry-run
```
⚠️ Lots de 3 zones par appel, `max_tokens=8000`. Fallback silencieux sur échec de lot : écrit quand même une entrée (vide pour `--update`, ou laisse `journalistes: []` pour `--fill-journalistes` sans toucher au reste). Après tout run partiellement échoué avec `--update` (pas `--fill-journalistes`), lancer `clean_fallback_journaux.py` avant de relancer.

### `check_journaux_coherence.py` 🔁 🗄️ — diagnostic pur
Compare les zones N1 réelles de la géographie aux entrées de `journaux.yaml`, dans les deux sens (manquantes/orphelines), pour les 6 scénarios × 2 lignes. Aucune écriture.
```bash
python3 check_journaux_coherence.py
```

### `clean_fallback_journaux.py` 🔁 🗄️
Retire de `journaux.yaml` les entrées placeholder laissées par le fallback silencieux de `generate_journaux.py --update` en cas d'échec de lot (signature : `nom` commence par "Édition ", `ton`/`langue_style` vides). À lancer avant de relancer `--update` après un run partiellement échoué.
```bash
cp journaux.yaml journaux.yaml.bak
python3 clean_fallback_journaux.py
```

---

## 3. Pipeline entités & événements custom

### `create_entities_and_instances.py` 🔁 🧩 — **script recommandé actuel**
Fusion de `create_entity.py` + `generate_instances.py` (les deux anciens scripts restent en archive). Crée une entité **et** génère automatiquement ses instances dans le même run. Tier `structured_strict`.

**Trois modes**, sélectionnables sans blocage depuis le GUI depuis le 11 juillet (`--mode`) :

- **custom** — décrit une instance précise dans `entites_custom/queue.yaml` (champs : `nom`, `category`, `role`, `etat`, `scenario_ref`, `scenario_hint`, `zone_hint` — fonctionnel mais pas encore documenté dans `QUEUE_TEMPLATE`, `source`). Le LLM déduit l'archétype, crée l'entité, puis enchaîne la génération des instances (scénario de référence contraint, les autres libres selon `scenario_hint`, ou les 6 par défaut).
- **auto** — génère et **injecte directement** N entités nouvelles dans le vault. `--scenario` accepte plusieurs valeurs (contrainte dure, prompt + filtre en sortie garanti) : `--scenario eco_communalism breakdown` limite les entités générées à exactement ces scénarios au lieu des 6 par défaut.
- **auto-suggest** — analyse les déséquilibres du vault, propose N idées, les **ajoute seulement à `entites_custom/queue.yaml`** (à valider/injecter ensuite en mode custom). `--scenario` y est une orientation de prompt, pas une contrainte dure appliquée en code.

```bash
python3 create_entities_and_instances.py --mode custom
python3 create_entities_and_instances.py --mode auto --n 3 --category humain --scenario eco_communalism breakdown
python3 create_entities_and_instances.py --mode auto-suggest --n 5 --scenario policy_reform
python3 create_entities_and_instances.py --dry-run
```
`--mode` omis en CLI direct → redemandé interactivement (compatibilité conservée). `--n` sans valeur en mode `auto`/`auto-suggest` → redemandé interactivement en CLI, mais **doit** être fourni depuis le GUI (valeur par défaut 3 pré-remplie dans le formulaire) pour éviter un blocage silencieux (pas de stdin connecté au sous-processus GUI).

Auto-lance en fin de run le cycle post-injection (`extract_localisation → review_localisation --auto-resolve → validate.py`) si au moins une entité/instance a été créée.

### `inject_custom_events.py` 🔁 🧩
Injecte des événements custom fournis par l'utilisateur dans `evenements_custom/queue.yaml` : crée l'archétype (`evenements/{slug}.md`) + une instance par scénario sélectionné (`event_instances/{slug}_{scenario}.md`). Tier `structured_strict`.

**Deux modes**, sélectionnables sans blocage depuis le GUI (`--mode`) :
- **custom** — traite le contenu actuel de `evenements_custom/queue.yaml` et injecte dans le vault. Champs : `id`, `description`, `portee`, `date_approximative`, `intensite`, `scenarios`, `variables_hint`, `variables_hint_count` (plafond appliqué en filtre dur depuis le 11 juillet, défaut 2), `acteurs_hint`, `acteurs_hint_count` (pas encore plafonné en filtre dur), `zone_hint` (fonctionnel, non documenté dans `QUEUE_TEMPLATE`), `source`.
- **auto** — analyse la couverture du vault, génère N idées, les **ajoute seulement à `queue.yaml`** (équivalent fonctionnel du mode `auto-suggest` des entités — pas d'injection directe). `--scenario` y est une orientation, pas une contrainte dure.

```bash
python3 inject_custom_events.py --mode custom
python3 inject_custom_events.py --mode auto --n 3 --scenario breakdown
python3 inject_custom_events.py --dry-run
```
`main()` écrit séparément dans `processed.yaml` (statut `partial` si succès partiel) et `needs_review.yaml`.

### `inject_custom_signals.py` 🔁 🧩
Injecte des signaux faibles custom (`signaux_custom/queue.yaml`) dans les fiches variables, au format `signal_to_state` (6 scénarios) + annotation section 7. Validation mécanique (comptage de mots, fenêtres de dates, collisions), jusqu'à 2 retries. Tier `structured_strict`.
```bash
python3 inject_custom_signals.py
python3 inject_custom_signals.py --dry-run
```

### `enrich_minimal.py` 🔁 🧩
Enrichit les fiches `statut: officialise_minimal` via le LLM (génère `responsabilites`, `description_journalistique`, `tensions_narratives`, `localisation`, impacts, `alliances`/`oppositions`, etc.), avec validation bloquante (2 retries). Tier `creative_souple` pour l'enrichissement principal, tier `volume` pour la sous-tâche de génération de rôles d'entités fantômes.
```bash
python3 enrich_minimal.py --scenario NOM       # ou --all, ou --slug SLUG
python3 enrich_minimal.py --dry-run
python3 enrich_minimal.py --limit N
python3 enrich_minimal.py --auto-cycle         # enchaîne extract_phantom_slugs (+ wave 2 via validate --verbose)
```
Sorties : `enrich_minimal_report.md`, `needs_review_enrich.yaml`. Coût estimé pour les 426 fiches restantes (P8) : ~$37 (estimation faite sur Claude — à recalculer, le script tourne maintenant sur `mistral-large-latest` par défaut).

### `extract_phantom_slugs.py` 🔁 🧩
Lit `enrich_minimal_report.md` et/ou une sortie `validate.py --verbose`, génère les rôles manquants via le LLM (tier `volume`), alimente `entites_custom/queue.yaml` (batches de 5, dédupliqués).
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
Rétro-construit la bible géopolitique plate d'un scénario à partir du contenu narratif existant (instances, événements custom), pour servir de référentiel et éviter la dérive de nomenclature (ex. 33 variantes de "bloc eurasien" trouvées avant ce script). Tier `structured_strict`.
```bash
python3 build_geographie_monde.py --scenario NOM   # ou --all
python3 build_geographie_monde.py --dry-run
python3 build_geographie_monde.py --force           # régénère tout le fichier (écrase)
```

### `enrich_geographie_recursive.py` 🔁 🧩 — **étape 2**
Ajoute un maillage hiérarchique de sous-zones (profondeur libre) sous les zones N1 déjà construites par l'étape 1. **Principe additif** : ne touche jamais aux zones déjà présentes, ne fait qu'ajouter. Tier `structured_strict`.
```bash
python3 enrich_geographie_recursive.py --scenario NOM   # ou --all
python3 enrich_geographie_recursive.py --dry-run
```

### `complete_geographie_coverage.py` 🔁 🧩 — **étape 3, workflow obligatoire review→apply**
Garantit que chaque pays de `zones_pays.json` a une zone N1 dans chaque scénario. Pour chaque pays sans zone : le LLM choisit "absorber" (zone existante) ou "nouvelle_zone". Batch de 12 pays. Tier `structured_strict` — migré vers `llm_client.py` le 11 juillet (avait auparavant sa propre implémentation directe des SDK, hors routing/retry centralisé ; délai fixe de 8s entre batches retiré à la même occasion, rate limiting désormais purement réactif).

**Garde-fou de patron spatial** *(15 juillet, P24 étape B)* : le prompt de proposition inclut désormais `patron_spatial_prompt_block(scenario)` (`patrons_spatiaux.py`, P24 étape A) — logique territoriale du scénario + patrons à respecter/éviter. Le LLM peut ajouter un champ optionnel `avertissement_patron_spatial` sur une affectation en cas de doute réel, visible dans `coverage_proposals_{scenario}.yaml` pour la validation manuelle ; jamais un motif de rejet automatique. Zéro coût LLM supplémentaire (même appel).

**Écriture `zones_pays.json` immédiate** *(15 juillet)* : auparavant différée à la toute fin d'un traitement `--all`, désormais écrite juste après chaque scénario traité (`_write_zones_pays()`) — évite une désynchronisation si le script est interrompu en cours de route sur plusieurs scénarios.
```bash
python3 complete_geographie_coverage.py --scenario NOM --review   # génère coverage_proposals_NOM.yaml, n'écrit rien
# → valider dans VS Code, mettre valide:false sur les propositions incohérentes ; un avertissement_patron_spatial n'est pas un rejet automatique
python3 complete_geographie_coverage.py --scenario NOM --apply    # écrit dans la fiche + zones_pays.json (immédiatement)
python3 complete_geographie_coverage.py --all [--dry-run]
```
⚠️ Ne jamais interrompre un run en cours. Ne jamais enchaîner `--apply` sur plusieurs scénarios sans relecture intermédiaire du fichier de propositions.

### `extract_localisation.py` 🔁 🧩
Extrait le champ `localisation` (zone/lieu/type_lieu) sur les fiches riches (hors `officialise_minimal`) + toutes les `event_instances`. Trois issues : lieu trouvé, transnational (vide assumé), ou ambigu (`statut: review_manuelle`). Tier `volume`.
```bash
python3 extract_localisation.py --dry-run
python3 extract_localisation.py
python3 extract_localisation.py --scenario NOM
python3 extract_localisation.py --slug SLUG
python3 extract_localisation.py --force          # retraite les fiches déjà faites
python3 extract_localisation.py --report-only
```

### `review_localisation.py` 🔁 🧩
Review interactive des fiches `statut: review_manuelle`, une par une : `[V]` valider la suggestion, `[C]` choisir une autre zone, `[0]` vide assumé, `[S]` skip. Tier `volume`.
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

### `check_origine_reelle_coherence.py` 🔁 🗄️ — **diagnostic pur, lecture seule sauf `--write-zones-manquantes`** *(14 juillet, P22 signal 1)*
Garde-fou de cohérence géographique : compare le pays d'une zone `ville`/`region_administrative` à l'union des pays de toute sa lignée d'ancêtres. Avertissement seul, jamais de blocage. Résolution ville→pays en cascade (extraction directe → alias adjectival → table statique `VILLE_PAYS` → `--resolve-llm`, tier `structured_strict`, cache dans `cache_ville_pays_llm.json`). Pour chaque incohérence : cherche un candidat de reparent parmi les zones N1 du scénario, et la racine N1 à ouvrir dans la Carte (peut différer du parent immédiat). Tableau récapitulatif markdown généré en fin de run, prêt à copier dans le backlog.
```bash
python3 check_origine_reelle_coherence.py --scenario NOM
python3 check_origine_reelle_coherence.py --all
python3 check_origine_reelle_coherence.py --all --resolve-llm
python3 check_origine_reelle_coherence.py --all --write-zones-manquantes   # écrit dans zones_manquantes.yaml si aucun candidat
```
État au 14 juillet : 0 incohérence sur les 6 scénarios.

### `check_type_entite_coherence.py` 🔁 🗄️ *(14 juillet, P26)*
Détecte (et corrige avec `--apply`) les entrées `origine_reelle` sans `type_entite` du tout — oubli de champ à l'écriture, masque des cas pour `check_origine_reelle_coherence.py`. Édition ligne-à-ligne du texte brut (pas de re-dump YAML complet) pour ne toucher que les lignes concernées. Backup `.bak` automatique avec `--apply`.
```bash
python3 check_type_entite_coherence.py --all                # aperçu, lecture seule
python3 check_type_entite_coherence.py --all --apply         # corrige, backup .bak
```
État au 14 juillet : 0 entrée sans `type_entite` sur les 6 scénarios, après `--apply`.

### `check_conventions_territoires.py` 🔁 🗄️ — **diagnostic pur, lecture seule** *(14 juillet, P27)*
Distinct de `check_origine_reelle_coherence.py` : au lieu de comparer une zone à sa chaîne de parenté, compare un même territoire ambigu (dépendance/collectivité, table `TERRITOIRES_AMBIGUS` à enrichir manuellement) **entre les 6 scénarios**. Vérifie la conformité à la convention décidée le 14 juillet : un territoire dépendant/autonome est toujours distinct de son pays souverain réel quand il apparaît dans un scénario — sauf exception narrative explicitement actée pour un scénario donné. N'a de sens qu'avec `--all` (comparaison entre scénarios).
```bash
python3 check_conventions_territoires.py --all
```
**P27 clos le 15 juillet.** Des 11 cas détectés le 14 juillet (Groenland ×3, Écosse ×3, Pays de Galles ×5) : 1 traité par split (Écosse/`breakdown`), 2 réglés par réaffectation directe ou déjà corrects (Groenland/`breakdown` et `eco_communalism`), 8 acceptés tels quels comme exceptions narratives (Royaume-Uni resté politiquement uni dans `breakdown` pour Angleterre+Galles, et entièrement dans `fortress_world`) ou décision explicite de clôture. Ce script continuera donc à signaler ces 8 cas comme "non conformes" à la convention générale — c'est attendu, pas un bug ni un oubli. Détail complet au backlog, P27.

### `scan_geographie_complet.py` 🔁 🗄️ — **orchestrateur** *(14 juillet)*
Lance en séquence les 4 scripts de diagnostic géographie ci-dessus (`check_zones_coherence.py` → `check_type_entite_coherence.py` → `check_origine_reelle_coherence.py` → `check_conventions_territoires.py`), en sous-processus indépendants (pas d'import — un `sys.exit()` d'un script ne tue jamais les autres), résumé consolidé à la fin. Chaque script reste utilisable seul (entrée sidebar GUI intacte). Aucune écriture par défaut.
```bash
python3 scan_geographie_complet.py --all
python3 scan_geographie_complet.py --all --apply-type-entite --resolve-llm --write-zones-manquantes
```

### Restructuration de zones — P7, dans l'onglet Carte (pas un script séparé)
**Correction d'une confusion documentaire** : ce manuel décrivait auparavant `restructure_zones.py` comme un script `generator/` "planifié, pas encore codé". C'est inexact depuis le 13 juillet — P7 a été construit directement dans l'onglet Carte du GUI (`gui/app.py`/`app.js`), pas comme script séparé. L'entrée fantôme correspondante dans `scripts_config.json` (section maintenance) peut être retirée. Détail complet du workflow en §7 (rename, reparent, split).

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
| `officialize_alliances.py` | Phase 1 du chantier alliances/oppositions : dédupliquer sémantiquement les mentions en texte libre et les convertir en slugs réels. `--limit`, `--resume`. Migré vers `llm_client.py` le 11 juillet (tier `structured_strict`) — n'était plus câblé en dur sur Claude/`ANTHROPIC_API_KEY`. | 🪦 One-shot (chantier terminé), garder pour référence si de nouvelles fiches en texte libre apparaissent |
| `fix_impact_scale.py` | Corrige rétroactivement `impact_local`/`impact_systemique_global` hors [0-5] (résidu d'un bug de prompt de `generate_entities.py`). Migré vers `llm_client.py` le 11 juillet (tier `structured_strict`), même raison qu'`officialize_alliances.py`. | 🪦 One-shot, déjà exécuté |
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

### Sélecteur LLM et routing par tier (mis à jour le 11 juillet)
Le sélecteur Fournisseur/Modèle de la sidebar **ne définit plus le modèle actif en permanence** — depuis le passage au routing par tier, chaque script résout son propre modèle selon le tier de la tâche (`llm_client.py::TASK_TIER_DEFAULTS`), indépendamment de ce sélecteur.

Une case à cocher **"Forcer ce modèle pour le prochain lancement"** apparaît sous le sélecteur :
- **Décochée (par défaut)** — aucun override envoyé, chaque script utilise son tier normalement. Le sélecteur devient purement informatif.
- **Cochée** — `force_llm_override: true` transmis à `POST /api/run`, `app.py` injecte alors `LLM_PROVIDER`/`LLM_MODEL` dans l'environnement du sous-processus, écrasant le tier pour ce run précis.

Le toggle est **sticky** : reste actif jusqu'à ce qu'il soit décoché manuellement (pas de reset automatique après un run). En contrepartie, un **bandeau d'alerte permanent orange** apparaît en haut de la zone principale tant qu'il est actif, sur tous les onglets, avec le modèle forcé affiché en clair et un bouton "Désactiver" intégré. Jamais persisté (ni `localStorage`, ni `config.json`) — remis à zéro à chaque rechargement de page.

La carte dashboard correspondante s'appelle désormais **"Modèle si forcé"** (renommée depuis "LLM actif", qui n'était plus exact une fois le routing par tier en place).

### Formulaires multi-modes (`mode_select`) — filtrage par onglet et notes contextuelles
Pour les scripts à plusieurs modes (`create_entities`, `inject_events`), le formulaire GUI n'affiche que les champs pertinents à l'onglet actuellement sélectionné :
- Chaque option CLI peut porter `mode_only: "auto"` ou `mode_only: ["auto", "auto-suggest"]` dans `scripts_config.json` — masqué automatiquement si l'onglet actif ne correspond pas.
- Le panneau de formulaire YAML guidé (`config_fields`, ex. le formulaire `queue.yaml` du mode Custom) porte un `config_fields_mode` similaire au niveau du script.
- Chaque choix de `mode_select` peut aussi porter une **note contextuelle** (`choices[].note`), affichée dans un petit bandeau sous les onglets Mode — utile pour rappeler qu'un mode "auto" propose des idées dans une queue à valider plutôt que d'injecter directement (cas d'`auto-suggest` pour les entités, et du mode `auto` d'`inject_custom_events.py`).

Nouveau type de champ générique **`multi_select`** (chips cliquables), utilisable aussi bien dans `config_fields` (déjà existant) que dans les `options` CLI classiques (ajouté le 11 juillet) — sert par exemple à `--scenario` du mode `auto` de `create_entities` (plusieurs scénarios sélectionnables, transmis en `nargs='+'` côté script).

### Structure des fichiers `gui/` (P5)
`app.py` reste le point d'entrée, mais n'est plus monolithique : `/api/dashboard` et ses 8 fonctions de calcul de stats (`_stats_articles`, `_stats_instances`, `_stats_entites`, `_stats_journaux`, `_stats_enrichissement`, `_stats_thematiques`, `_stats_zones`, `_count_review_items`) vivent désormais dans **`gui/routes_dashboard.py`**, un Blueprint Flask enregistré via `app.register_blueprint(dashboard_bp)` juste après la création de `app`. Objectif : ce bloc était régulièrement écrasé par erreur lors de patches sur d'autres parties de `app.py` (carte, coverage) du simple fait de sa position au milieu du fichier. Toutes les autres routes restent dans `app.py`.
⚠️ Non vérifié au 11 juillet : cohérence de `routes_dashboard.py` avec le renommage "Modèle si forcé" ci-dessus (fichier non disponible pendant cette session — voir backlog P18).

### Sidebar (`scripts_config.json`) — scripts lançables en un clic
**Section génération** : `enrich_minimal`, `generate_journaux`, `validate`, `generate`, `generate_series`, `generate_manual`.
**Section entités** : `create_entities`, `inject_events`, `inject_signals`, `extract_phantom_slugs`, `fix_alliance_suffixes`, `requeue_needs_review`, `undo_custom`.
**Section maintenance** : `extract_localisation`, `review_localisation`, `build_geographie`, `enrich_geographie`, `complete_geographie_coverage`, `restructure_zones` (⚠️ script pas encore codé, entrée présente mais échouera si lancée).

Chaque entrée définit ses options (checkbox/select/number/slug_select/multi_select), ses dépendances (`requires`) et les fichiers YAML associés affichables dans le panneau de review. Vérification systématique faite le 11 juillet (backlog P6, clos) : chaque `flag` déclaré ici croisé avec l'`argparse` réel du script Python correspondant — 2 flags fantômes trouvés et supprimés (`--scenario` sur `create_entities`/`inject_events`, jamais lus par les scripts avant d'y être réintroduits avec un vrai rôle).

### Routes API principales
| Route | Méthode | Rôle |
|---|---|---|
| `/` | GET | Sert `templates/index.html` (SPA) |
| `/api/config` | GET/POST | Lit/écrit `config.json`. Le POST préserve les clés `llm.available_*` via une vraie fusion de dicts imbriqués (bug #21 du handoff) |
| `/api/scripts` | GET | Liste des scripts configurés (sidebar) |
| `/api/script/<id>` | GET | Détail d'un script (options, requires) |
| `/api/yaml` | GET/POST | Lecture/écriture d'un fichier YAML du vault (éditeur GUI, `.bak` auto). Résout les chemins relatifs par rapport à **`vault_root`** |
| `/api/yaml/form` | POST | Écriture structurée via formulaire (ex. queue.yaml) |
| `/api/yaml/append` | POST | Ajoute une entrée à un YAML existant (bouton "Ajouter à la queue"). Protégé contre le double-clic depuis le 11 juillet — bouton désactivé pendant l'appel, réactivé en `finally` |
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
| `/api/dashboard` | GET | Statistiques du vault (compteurs fiches, cohérence). Vit dans `gui/routes_dashboard.py` (Blueprint Flask) |
| `/api/review` | GET | Panneau de review des fiches en attente. Cherche dans `vault_root` |
| `/api/run` | POST | Lance un script en sous-processus, retourne un `run_id`. Body : `{script_id, args, force_llm_override}` — `force_llm_override` (bool, défaut absent=false) contrôle l'injection de `LLM_PROVIDER`/`LLM_MODEL` depuis le 11 juillet |
| `/api/stream/<run_id>` | GET | SSE — flux de logs en direct du run |
| `/api/stop/<run_id>` | POST | Arrête un run en cours |
| `/api/status` | GET | État global (runs actifs, etc.) |

### Onglet Carte — workflow détaillé

**À quoi ça sert** : affecter un pays à une zone N1 d'un scénario, en visualisant l'impact narratif avant de confirmer — pensé pour un pays à la fois (contrairement à `complete_geographie_coverage.py`, pensé pour du traitement en masse).

**Workflow pas à pas :**
1. Ouvrir le GUI (`http://localhost:5000`), onglet **🗺️ Carte**
2. Choisir le scénario en haut
3. Cliquer sur un pays sur la carte (gris = non affecté, coloré = déjà affecté)
4. Dans le panneau latéral, deux options :
   - **Sélection manuelle** d'une zone N1 existante dans la légende
   - **"Demander une proposition (LLM)"** — le modèle configuré propose une zone avec justification
5. **"🔍 Évaluer l'impact"** — obligatoire, le bouton de confirmation n'apparaît qu'après. Génère un rapport en lecture seule (sous-zones orphelines, instances/événements liés, mentions textuelles), sauvegardé dans `documentation/need_action/impact_bascule_{pays}_{scenario}.md`
6. Confirmer la bascule

**Cas particulier : Royaume-Uni** — `Royaume-Uni` / `Angleterre` / `Écosse` / `Pays de Galles` correspondent à 4 entrées `pays_liste` pour un seul polygone GBR sur le fond de carte. Un sélecteur intermédiaire apparaît au clic.

**Bouton "🚫 Ignorer"** — marque un pays comme "blanc intentionnel" : il reste dans `zones_manquantes.yaml` avec un statut dédié, mais disparaît de la vue "zones manquantes" du dashboard. Utile pour les pays qu'on ne veut délibérément pas traiter.

**Bandeau diagnostic orange** — `#carte-diagnostic`, conditionnel : ne s'affiche que s'il existe des pays FR sans correspondance trouvée sur le fond de carte Leaflet (noms mal mappés dans `gui/static/pays_mapping.json`). Absence de bandeau = pas de problème de mapping actuellement.

### Restructuration de zones (P7) — rename, reparent, split

Trois opérations distinctes, toutes dans l'arbre des sous-zones (clic sur le nom/pastille d'une zone N1 dans la légende pour l'ouvrir) :

| Opération | Bouton | Ce qu'elle fait | Depuis |
|---|---|---|---|
| **Renommer** | ✏️ sur chaque zone N1 de la légende | Change `slug`/`nom`, propage vers enfants, wikilinks, `relations.allies/rivaux` (n'importe quelle zone du scénario), `instances/*.md`, `zones_pays.json` | 13 juillet |
| **Déplacer** (reparent) | "↗️ déplacer" sur tout nœud non-racine de l'arbre | Bouge une zone **entière** (avec son sous-arbre) vers un nouveau parent. Recalcul du niveau en cascade si la profondeur change. Permet aussi de promouvoir en zone N1 autonome ou de créer une nouvelle zone N1 à la volée | 13 juillet |
| **Scinder** (split) | "✂️ scinder" sur tout nœud ayant plus d'un pays dans son `origine_reelle` (racine incluse) | Extrait un ou plusieurs pays vers une nouvelle zone N1 ou une zone N1 existante, **sans bouger le reste de la zone source**. Les sous-zones dont la propre `origine_reelle` référence aussi le(s) pays extrait(s) suivent automatiquement (détecté, pas décidé manuellement) ; les autres restent en place. Écrit aussi `zones_pays.json` depuis le correctif du 15 juillet (voir note ci-dessous) | 14 juillet |

**Bug corrigé le 15 juillet** : jusque-là, split écrivait bien dans `geographie/{scenario}.md` mais jamais dans `zones_pays.json` (même angle mort que rename avant sa propre correction) — un split réussi côté données ne se reflétait donc pas sur la carte. Corrigé (`_split_zone_in_zones_pays()`), trouvé en traitant le premier vrai cas P27.

**Limite du fond de carte, pas un bug** : même après le correctif ci-dessus, un territoire infra-national (Écosse, Pays de Galles...) ne peut **jamais** s'afficher avec une couleur différente de son pays souverain sur la carte — le fond Leaflet (`world.geo.json`) n'a qu'un seul polygone par pays reconnu par l'ONU, aucune subdivision. Si la carte ne semble pas refléter un split, vérifier `zones_pays.json` directement (`grep` ou `regenerate_zones_pays.py --dry-run`) plutôt que de chercher un bug dans le split.

**Différence rename/reparent/split, en une phrase** : rename change juste le nom/slug d'une zone, reparent déplace une zone entière ailleurs, split coupe une zone en deux et n'en déplace qu'un morceau.

**Split vs le clic sur un pays (`carte_assign`)** : pour un cas simple — un seul pays, une seule écriture, aucune sous-zone concernée — cliquer sur le pays et choisir "créer une nouvelle zone" (mécanisme préexistant, §ci-dessus) suffit et est plus rapide. Split n'apporte une vraie valeur que pour les cas plus complexes : plusieurs formulations du même pays dans la zone source (ex. `"Groenland"` et `"Danemark (Groenland)"`), et/ou des sous-zones à faire suivre.

**Rapport d'impact avant confirmation** — comme pour la bascule pays→zone classique, chaque opération de restructuration affiche un aperçu (`impact_renommage_zone`, `impact_reparent_zone`, `impact_split_zone`) avant d'écrire quoi que ce soit. Backup `.bak` automatique dans tous les cas.

### Rechercher une zone tous niveaux

La légende/liste principale de la Carte n'affiche que les zones **niveau 1** — une zone niveau 2/3 (ex. `delta_rhone_fermes_verticales`) est invisible tant qu'on n'a pas ouvert l'arbre de sa bonne racine N1, qui peut différer de son parent immédiat. Champ de recherche en haut de la sidebar de l'onglet Carte (depuis le 14 juillet) : cherche par nom ou slug, tous niveaux, insensible aux accents/casse. Chaque résultat affiche le chemin complet racine→zone ; au clic, ouvre directement le bon arbre et centre/surligne la zone trouvée.

### Choix du modèle LLM (carte + `complete_geographie_coverage.py`)
Le sélecteur de modèle du GUI ne définit un modèle **réellement utilisé** que si le toggle "Forcer ce modèle" est coché (voir plus haut) — sinon la carte et `complete_geographie_coverage.py` suivent leur tier normal (`structured_strict`, `mistral-large-latest` par défaut).

| Provider | Modèles disponibles dans le sélecteur |
|---|---|
| Mistral | `mistral-small-latest`, `mistral-large-latest` |
| Claude | `claude-sonnet-4-6`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-haiku-4-5-20251001` |

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

# Forcer un modèle précis pour un test ponctuel (CLI direct, hors GUI)
LLM_PROVIDER=claude LLM_MODEL=claude-sonnet-5 python3 generate.py
```

### Bug récurrent connu
Confusion `pipeline_dir` (= `generator/`) vs `vault_root` (racine du vault) dans `app.py` — `geographie/` vit à `vault_root`, pas dans `pipeline_dir`. Vérifier ce point en priorité en cas de nouveau bug carte/coverage. Même famille de confusion trouvée le 4 juillet dans `check_session.sh` (bug #11 du handoff) — toujours vérifier `$GUI_DIR` vs `$VAULT_DIR`/`generator` en cas de chemin suspect.
