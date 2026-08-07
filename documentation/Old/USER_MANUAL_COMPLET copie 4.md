# Manuel utilisateur complet — Pipeline Ourrassol 2098
*Consolidé le 15 juillet 2026 — couvre `generator/` (39+ scripts Python) et `gui/` (Flask)*

Ce manuel classe chaque script par rôle : **modules internes** (jamais lancés seuls), **orchestrateurs**, **pipeline entités/événements**, **pipeline géographie**, **validation**, **scripts one-shot/legacy**, et **GUI Flask**. Pour chaque script exécutable : ce qu'il fait, quand l'utiliser, options CLI, statut (répétable / one-shot / legacy), et intégration GUI ou non.

---

## 0. Vue d'ensemble de l'architecture

```
Ourrassol2098/                          ← racine du vault Obsidian
├── generator/                          ← pipeline Python (35+ scripts)
│   ├── config.yaml, config_series.yaml, journaux.yaml
│   ├── state/ (trajectory_usage.json, manual_progress.json, last_validated.json)
│   ├── entites_custom/ (queue.yaml, needs_review.yaml, processed.yaml)
│   ├── evenements_custom/ (queue.yaml, processed.yaml, undo_queue.yaml)
│   └── signaux_custom/ (queue.yaml, processed.yaml, needs_review.yaml)
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

**Cycle de vie commun aux 3 pipelines custom** — `entites_custom/`, `evenements_custom/`
et `signaux_custom/` suivent le même schéma : `queue.yaml` (entrées à traiter) →
`processed.yaml` (succès, éventuellement statut `partial`) / `needs_review.yaml`
(échec ou ambiguïté à trancher manuellement, retraitable via `requeue_needs_review.py`
pour les entités). `evenements_custom/` a en plus `undo_queue.yaml`, propre à son
mécanisme d'annulation (`undo_custom.py`).

**Providers LLM et routing par tier (depuis le 11 juillet)** : toutes les tâches passent par `llm_client.py`, qui route vers **Mistral**, **Claude** ou **OpenAI** selon deux mécanismes complémentaires :

1. **Routing par tier** (comportement par défaut) — chaque script passe un `task_tier` à `call_llm()`, résolu automatiquement via `TASK_TIER_DEFAULTS` selon la nature de la tâche :

   | Tier | Modèle par défaut | Usage typique |
   |---|---|---|
   | `strict` | `mistral-large-latest` *(→ `claude-sonnet-5` prévu en prod)* | Identité/fidélité imposée sur sortie longue et créative (articles, journalistes) |
   | `structured_strict` | `mistral-large-latest` | Sortie JSON canonique référencée ailleurs dans le vault (entités, instances, géographie) |
   | `creative_souple` | `mistral-large-latest` | Rédaction/enrichissement libre, sans contrainte d'identité tierce |
   | `volume` | `mistral-small-latest` | Extraction, classification, résolution courte — gros volume, faible enjeu par erreur |

2. **Override manuel** (`LLM_PROVIDER`/`LLM_MODEL` en variable d'environnement, ou toggle GUI "Forcer ce modèle") — priorité absolue sur le tier, pour un test ponctuel sans changer le comportement par défaut. Jamais destiné à un usage permanent (ne pas mettre en `export` fixe dans `.zshrc`).

Retry réactif centralisé sur 429 : aucune pause préventive, s'adapte automatiquement au palier du compte (Free/Scale) pour les trois fournisseurs. Les **18 scripts** du pipeline qui utilisent un LLM sont désormais tous unifiés sous `llm_client.py`.

**Convention de statut utilisée ci-dessous :**
- 🔁 **Répétable** — conçu pour être relancé régulièrement, fait partie du flux normal
- 🧩 **GUI** — a une entrée dans `scripts_config.json`, lançable en un clic depuis le sidebar
- 🗄️ **CLI uniquement** — pas encore intégré au GUI
- 🪦 **One-shot / migration** — à lancer une fois, ne devrait plus être relancé
- 📦 **Legacy / archive** — remplacé par un script plus récent, conservé pour référence

**Règle actée le 26 juillet 2026** : 🪦 et 🧩 sont mutuellement exclusifs. Un script one-shot n'a plus sa place dans le panneau GUI, quel que soit l'usage résiduel invoqué (y compris un `--force` ponctuel) — géré uniquement en ligne de commande. Dès qu'un script bascule 🔁→🪦, il sort du sidebar dans la foulée (voir `build_geographie_monde.py`, §4 et §6).

**⚠️ Piège transversal trouvé le 31 juillet 2026 — `--dry-run` n'évite pas toujours l'appel LLM.** Deux familles de comportement coexistent dans le pipeline, sous le même nom de flag :
- **Vrai dry-run** (aucun appel API) : `generate.py`, `generate_series.py`, `generate_journaux.py`, `extract_phantom_slugs.py` — le code vérifie `dry_run` *avant* d'appeler le LLM.
- **Simulation partielle** (appel LLM réel, seule l'écriture disque est sautée) : `create_entities_and_instances.py`, `inject_custom_events.py`, `inject_custom_signals.py`, `enrich_geographie_recursive.py`, `enrich_minimal.py`, `extract_localisation.py`, `review_localisation.py` (ce dernier seulement si `--auto-resolve` est aussi actif) — la dérivation LLM (archétype, variables, zone...) est inconditionnelle dans le code, seule l'écriture finale (`write_*_file`) est protégée par `if not dry_run`.

Toutes les descriptions GUI de `--dry-run` sur ces 7 scripts ont été corrigées en conséquence (`scripts_config.json`) pour prévenir explicitement du coût réel malgré le mot "simulation". `extract_localisation.py` a en plus `--report-only`, qui lui est un vrai zéro-coût (retourne avant tout appel).

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

### `generate.py` 🔁 🧩 — **réécrit le 2 août 2026 : deux modes**
Point d'entrée unique pour générer un ou plusieurs articles. Deux modes,
sélectionnables via `--mode` (CLI) ou l'onglet Mode du GUI :

**Semi-guidé** (comportement historique, inchangé) : un seul scénario
(`config.yaml` ou `--scenario`), sélection automatique des instances par
pertinence thématique — **désormais avec rotation à mémoire** (voir
plus bas) —, zone/titre/angle éditables.

**Forcer** : garantit la présence d'une instance/un événement/un signal
précis dans l'article. L'article est systématiquement construit autour
de lui (angle généré automatiquement, écrase tout angle manuel ; titre
toujours laissé à l'IA, jamais éditable dans ce mode).
```bash
python3 generate.py                                    # semi-guidé, config.yaml
python3 generate.py --dry-run
python3 generate.py --mode forcer --forcer-type instance \
    --forcer-slug oracle_des_seuils --forcer-scenarios tous
python3 generate.py --mode forcer --forcer-type evenement \
    --forcer-slug conflit_israel_iran_2026 --forcer-scenarios breakdown policy_reform \
    --forcer-zone moyen_orient_golfe
```
- `--forcer-scenarios` : `tous` (= tous les scénarios où l'élément
  existe **réellement**, pas les 6 sans distinction) ou une liste de
  scénarios séparés par des espaces (le GUI envoie plusieurs tokens
  `nargs="+"`, pas une chaîne à virgules).
- `--forcer-zone` : si une zone précise est cochée, elle **remplace** le
  choix de scénarios plutôt que de le filtrer en "ET" (une zone
  n'appartient qu'à un seul scénario, donc plus précise) — évite les
  combinaisons impossibles (ex. scénario A coché + zone qui n'existe
  que dans le scénario B → génération bloquée avant le 2 août, résolue
  automatiquement depuis).
- **Un article est généré et sauvegardé par scénario retenu**, avec un
  résumé du lot (réussis/échecs) en fin de run.
- Toute erreur de résolution (élément introuvable pour le scénario/la
  zone demandée, type choisi sans élément sélectionné) arrête proprement
  avec un message explicite plutôt que de générer silencieusement un
  article sans l'élément demandé.

`validate_config_semi_guide()` vérifie (11 juillet, bug #26) que
`zone_slug` — si fourni — existe réellement dans `journaux.yaml` pour le
scénario/ligne éditoriale ; sinon erreur claire listant les zones
valides. `validate_config_forcer()` est une validation allégée
équivalente pour le mode forcer (pas de zone_slug fixe à valider, chaque
article de la boucle utilise la zone propre à l'élément dans son
scénario).

**Rotation à mémoire des instances** (2 août 2026, `loader.py`) : au-delà
de 6 instances candidates pertinentes pour une thématique, les ex-aequo
de score sont départagés par le nombre d'utilisations passées (état
persisté dans `state/instance_usage.json`) plutôt qu'un tri déterministe
pur — évite qu'une instance pertinente mais rarement en tête ne sorte
jamais sur un grand corpus d'articles. Même principe déjà en place pour
les jalons historiques (`state/trajectory_usage.json`).

**Plafonnement des événements custom et de la géographie** (2 août
2026, passage à l'échelle du vault) : les événements custom et la liste
des zones géographiques n'étaient soumis à aucune limite (contrairement
aux instances/signaux) — risque de croissance non maîtrisée du prompt.
Corrigé avec le même principe pour les deux : une couche large et peu
coûteuse qui préserve la vision globale du monde (résumé une ligne, noms
seuls au-delà d'un plafond haut — 25 événements / toutes les zones
pertinentes), et une couche détaillée filtrée par pertinence + rotation
à mémoire (plafond bas — 8 événements en détail complet, 20 zones en
résumé). Score de pertinence des événements réutilise le matériau déjà
standardisé sur les fiches (`portee`, amplitude des
`impact_sur_variables`) plutôt qu'une nouvelle heuristique — même
principe que le score des instances. L'élément forcé (mode Forcer) est
toujours garanti présent dans la couche détaillée, jamais soumis au tri
ni à la rotation. **Pas encore testé en conditions réelles au 2 août
2026** — seulement validé fonctionnellement en sandbox, priorité de la
prochaine session.

### `trace_injection.py` 🔁 🗄️ — **nouveau le 2 août 2026, diagnostic pur**
Reconstitue le parcours complet d'une instance/un événement/un signal :
origine (idée source, date d'injection), propagation dans l'espace
(scénarios, zones — résolues en noms lisibles via `geographie/`) et le
temps (fictif et réel), variables systémiques influencées (résolues en
noms lisibles via `variables/`), réseau relationnel (alliances/
oppositions pour une instance, acteurs impliqués pour un événement), et
usage aval dans les articles publiés (scan texte best-effort).
```bash
python3 trace_injection.py --slug oracle_des_seuils --type instance
python3 trace_injection.py --slug insurrection_rust_belt --type evenement --json
python3 trace_injection.py --slug oracle_des_seuils --type instance --report   # écrit .md + .json
python3 trace_injection.py --list --type instance   # liste les slugs disponibles
```
Résolution tolérante : accepte qu'on lui passe un slug d'instance/
event_instance (entité + suffixe scénario) à la place du slug d'entité/
archétype attendu — dérive automatiquement le bon slug via le champ
`entite:`/`archetype:` de la fiche. Pour un signal, exploite le bloc
`signal_to_state` (déjà présent sur les fiches variables) pour donner
l'évolution complète par scénario (date de bascule, événement clé,
texte narratif), pas seulement une présence binaire.

**GUI** : menu Type (instance/événement/signal) → menu Élément filtré en
cascade (même mécanisme que `undo_custom`), route `/api/trace/<slug>`
dans `app.py` (subprocess + JSON, même pattern que les autres appels
`--json` du pipeline). Testé en conditions réelles par David sur
plusieurs slugs.

### `generate_series.py` 🔁 🧩
Génère une **série d'articles** sur plusieurs thématiques avec cohérence temporelle, pilotée par `config_series.yaml`.
```bash
python3 generate_series.py                    # utilise config_series.yaml
python3 generate_series.py --dry-run          # sans appel API
python3 generate_series.py --scenario breakdown
python3 generate_series.py --validate-first   # valide la base avant de générer
```
Sortie : `articles/{scenario}/` + `articles/{scenario}/_index.md`.

### `generate_manual.py` 🪦 **RETIRÉ DU SIDEBAR (31 juillet 2026)** — voir §6
Pipeline **sans appel API** : construit le prompt du prochain article de la série et l'affiche pour copier/coller dans un chat Claude.ai. Utile pour évaluer le contenu à la main avant d'industrialiser. *(Seul script du pipeline où les mentions "Claude" dans le code sont intentionnelles — ce workflow est spécifiquement pensé pour l'interface de chat Claude.ai, hors abstraction `llm_client.py`.)*
```bash
python3 generate_manual.py prompt          # affiche system+user prompt, avance la série
python3 generate_manual.py status          # état de la série en cours
python3 generate_manual.py save fichier.txt # sauvegarde l'article collé depuis le chat
```
État de rotation dans `state/manual_progress.json` (mode "prévisualisation" par défaut : chaque `prompt` avance sans sauvegarder tant que `save` n'est pas appelé).

⚠️ **Retiré du panneau GUI le 31 juillet 2026** (revue systématique du sidebar) : son seul cas d'usage encore utile — prévisualiser le prompt d'un article sans appeler l'API, pour copier/coller dans un LLM externe — est désormais couvert par la case `--dry-run` de `generate.py` (§2 ci-dessus), qui affiche le même contenu (system + user prompt) sans le mécanisme de rotation de série propre à ce script. Reste utilisable en CLI directe si le suivi multi-articles d'une série redevient utile.

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

### `inject_custom_signals.py` 🔁 🧩 *(mise à jour en profondeur le 26 juillet 2026)*
Injecte des signaux faibles custom (`signaux_custom/queue.yaml`) dans les fiches variables, au format `signal_to_state` (6 scénarios) + annotation section 7. Validation mécanique (comptage de mots, fenêtres de dates, collisions), jusqu'à 2 retries. Tier `structured_strict`.
```bash
python3 inject_custom_signals.py
python3 inject_custom_signals.py --dry-run
```

**Parcours complet d'un signal** (utile pour comprendre l'impact réel) : queue → sélection de variable(s) par le LLM → rédaction par variable (6 scénarios en un seul appel) → validation mécanique → écriture (fiche variable + `registre_evenements.md` + fiche d'audit `signaux_custom/{slug}.md`). Le résultat est ensuite consommé par `prompt_builder.py` au moment de générer un article : chaque signal est classé par `scope` (`majeur`/`structurant`/`local`, calculé dans `snapshot.py::build_signal_trajectory()` selon le nombre de variables partageant le même `evenement_cle` et si une variable pilote est impliquée), et un système de rotation à mémoire évite de toujours citer les mêmes signaux. **Contrairement aux événements custom (`inject_custom_events.py`, Priorité 0, inclus systématiquement), un signal n'a AUCUNE garantie d'apparaître dans un article donné** — c'est une texture de fond, pas un fait garanti. Pour influencer le monde de façon sûre et visible, préférer un événement custom.

**Bug de fond trouvé et corrigé le 26 juillet 2026** — `regenerate_registre()`/`parse_registre_table()` ne reconnaissaient que le format de séparateur de tableau markdown compact (`|---|`), pas une variante réalignée avec des espaces (`| --------- |`, produite par certains éditeurs comme Obsidian). Une seule section du registre (`## breakdown`) avait ce format différent — conséquence : plantage (`TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`) à chaque écriture réelle touchant cette section, invisible en `--dry-run` (qui ne passe jamais par cette fonction). Corrigé avec `_est_ligne_separateur()`, robuste aux deux formats — testé contre le vrai registre de David, les 6 sections se parsent maintenant correctement. Au passage : ajout d'un `.bak` avant l'écriture du registre (seul point d'écriture du pipeline géographie qui n'en avait pas jusque-là).

**Collision de fenêtre temporelle — rétrogradée de blocage à avertissement (26 juillet)** : si un signal réutilise la même `date_bascule` qu'un AUTRE signal déjà existant sur la même variable, ce n'est plus qu'un avertissement console (`⚠ [avertissement, non bloquant]`), plus un blocage. Le registre existe pour éviter les doublons *accidentels* (voir son en-tête), pas pour interdire à deux signaux réellement indépendants de coexister sur la même période — rien n'empêche narrativement deux causes distinctes de coïncider dans le temps pour la même variable. Reste bloquant en revanche le cas de collision **interne au même nouveau signal** (deux scénarios du signal qu'on est en train de créer partageant la même fenêtre) — celui-là est un vrai signe de bug de génération, pas une coïncidence légitime.

**Cohérence thématique avec les signaux existants (26 juillet)** — jusqu'ici la section 12 de la fiche variable était montrée au LLM "pour le style" uniquement, sans consigne de cohérence. Ajouté :
- `_signaux_thematiquement_proches()` : repérage lexical par mots-clés partagés entre l'idée et les signaux déjà en section 12 (mots de 5+ lettres, hors mots vides français — pas de la vraie sémantique, aucune infra d'embeddings ici). Exclut le signal en cours de génération de ses propres résultats.
- Champ **obligatoire** dans la réponse JSON du LLM : `signaux_existants_consideres` — doit expliciter comment il s'est positionné par rapport aux signaux proches repérés (complémentaire / conséquence / tension assumée), ou dire explicitement qu'il n'en a trouvé aucun. Rendu vérifiable dans la fiche d'audit (nouvelle section "## Cohérence avec les signaux existants") plutôt que silencieux.
- Limite assumée : un filet lexical, pas sémantique — rate les reformulations sans mot commun, la relecture humaine reste la vraie vérification finale.

**`zone_hint` ajouté puis reconçu le 26 juillet** — n'existait pas du tout jusqu'ici, contrairement à `inject_custom_events.py`. Première version : même mécanisme que `inject_custom_events.py` (sélecteur de zone 2098, `zones_hier`). **Abandonnée le même soir** après un échange avec David : une zone 2098 est par nature propre à un seul scénario (nom narratif, découpage différent d'un scénario à l'autre), et le sélecteur GUI ne pouvait de toute façon afficher que les zones du scénario par défaut de la Config — aucune garantie de pertinence pour un signal qui couvre toujours les 6 scénarios en un seul appel.
- **Reconçu en champ texte libre pour un lieu réel de 2026** (pays, région, ville — ex. "Norvège") plutôt qu'un slug de zone 2098 : un pays réel existe à l'identique dans les 6 scénarios, seule son appartenance à tel ou tel bloc change. Le prompt demande désormais au LLM d'identifier lui-même, pour chaque scénario (via la section 8, `state_logic`), à quelle zone/bloc ce lieu correspond — la correspondance peut légitimement différer d'un scénario à l'autre.
- Consigne de cohérence conservée : si l'idée source mentionne elle-même un lieu différent du `zone_hint` choisi, le lieu de l'idée source reste prioritaire.
- **Limite acceptée telle quelle** : reste une consigne de prompt, jamais une vérification mécanique — la relecture humaine de la fiche générée reste la seule protection réelle.
- **Pas de champ "intensité"** (décision explicite, 26 juillet) : contrairement à un événement (un seul niveau d'intensité global), un signal décrit une évolution *par scénario* — pas d'équivalent structurel à ajouter.

**Bugs GUI associés, côté formulaire d'ajout à la queue** (`app.js`, tous scripts à file d'attente confondus — voir §7) : validation de champs requis absente (`_appendYamlQueue()`), et mode "Édition brute" qui affichait un instantané périmé du fichier. Voir détail dans "Bugs GUI corrigés le 26 juillet 2026" (§7).

**Trois bugs de plus, trouvés le 27 juillet en testant le `zone_hint` reconçu sur un cas réel (idée Sahel, `essai_zone_hint_sahel`) :**
- **Hallucination "Scénario inconnu"** : le LLM a une fois ajouté une 7e clé à `scenarios`, littéralement nommée comme la variable cible elle-même (`geopolitique_conflits:` en plus des 6 scénarios), avec son propre bloc évolution/date/événement. Le contrôle qui l'a détecté existait déjà (`validate_signal_block`), mais aucune consigne de correction dédiée n'existait pour ce cas. Corrigé des deux côtés : règle explicite ajoutée à `FORMAT_RULES` (les 6 clés exactes, jamais le nom de la variable), et consigne de correction dédiée si ça se reproduit malgré tout.
- **Plafond `variable_hint_count` jamais vérifié mécaniquement** : `step1_select_variable()` a retourné 3 variables alors que le plafond par défaut est 2 — la consigne n'était qu'un texte de prompt, jamais recontrôlée après coup. Corrigé : troncature mécanique après l'appel LLM, en gardant toujours en priorité la ou les variables imposées par `variable_hint`.
- **`section7_annotation` sans le texte "signal_custom:"** : le LLM a une fois écrit `(→ {slug}, source: ...)` en sautant le préfixe `signal_custom: ` attendu — résultat : la ligne d'annotation devenait invisible à `undo_custom.py --type signal`, qui la cherche via ce préfixe exact (voir plus bas). Corrigé côté prompt (consigne renforcée, "MOT POUR MOT") et côté `undo_custom.py` (détection tolérante aux deux formats).

**✅ Validé de bout en bout le 27 juillet** — après cette série de correctifs, un test complet sur une idée réelle (irrigation solaire + tensions hydriques, `zone_hint: Sahel`) est allé jusqu'au bout sur 2 variables, `status: injected` dans `processed.yaml`, sans passer par `needs_review.yaml`. Confirmation qualitative en plus de la confirmation mécanique : les 6 scénarios du signal généré incarnent bien le Sahel différemment selon la logique de chaque scénario (effondrement en `breakdown`, contrôle militarisé en `fortress_world`, gestion technocratique en `new_sustainability`, autogestion en `eco_communalism`, régulation institutionnelle en `policy_reform`, tension interétatique classique en `reference`) plutôt que de répéter le même contexte générique six fois — c'était l'objectif initial du `zone_hint` reconçu, confirmé atteint.

### `enrich_minimal.py` 🔁 🧩
Enrichit les fiches `statut: officialise_minimal` via le LLM (génère `responsabilites`, `description_journalistique`, `tensions_narratives`, `localisation`, impacts, `alliances`/`oppositions`, etc.), avec validation bloquante (2 retries). Tier `creative_souple` pour l'enrichissement principal, tier `volume` pour la sous-tâche de génération de rôles d'entités fantômes.
```bash
python3 enrich_minimal.py --scenario NOM       # ou --all, ou --slug SLUG
python3 enrich_minimal.py --dry-run
python3 enrich_minimal.py --limit N
python3 enrich_minimal.py --auto-cycle         # enchaîne extract_phantom_slugs (+ wave 2 via validate --verbose)
```
Sorties : `enrich_minimal_report.md`, `needs_review_enrich.yaml` (bug de tri des clés YAML corrigé le 2 août 2026 — voir plus bas). **P8 clos** : les 426 fiches `officialise_minimal` d'origine ont toutes été traitées en un seul run le 27 juin 2026 (trace laissée dans chaque fiche, section `## Notes` du corps : *« Fiche enrichie depuis officialise_minimal le 2026-06-27. »*) — confirmé le 2 août 2026 par recomptage sur le vault : zéro fiche `officialise_minimal` restante sur les 6 scénarios. Coût réel non recalculé (script tourne sur `mistral-large-latest` par défaut depuis le 11 juillet, l'estimation initiale de ~$37 avait été faite sur tarif Claude).

### `extract_phantom_slugs.py` 🔁 🧩
Lit `enrich_minimal_report.md` et/ou une sortie `validate.py --verbose`, génère les rôles manquants via le LLM (tier `volume`), alimente `entites_custom/queue.yaml` (batches de 5, dédupliqués).
```bash
python3 extract_phantom_slugs.py                   # source=all (défaut)
python3 extract_phantom_slugs.py --source enrich|validate
python3 extract_phantom_slugs.py --dry-run
python3 extract_phantom_slugs.py --report PATH
```

### `fix_alliance_suffixes.py` 🪦 **RETIRÉ DU SIDEBAR (26 juillet 2026)** — voir §6
Correction **mécanique, sans API** : ajoute le suffixe `_{scenario}` manquant dans les champs `alliances`/`oppositions`. Confirmé résolu partout dans le vault (`--dry-run --verbose` : 0 fiche modifiée, 0 correction) le 26 juillet 2026 par David.
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

### `undo_custom.py` 🔁 🧩 *(type `signal` ajouté le 26 juillet 2026)*
Retire proprement des entités/instances/événements/event_instances/**signaux faibles**, avec gestion des dépendances et backup `.bak` automatique. Dry-run par défaut.
```bash
python3 undo_custom.py                       # dry-run depuis evenements_custom/undo_queue.yaml
python3 undo_custom.py --execute
python3 undo_custom.py --slug SLUG --type TYPE --generalisation yes|no [--execute]
python3 undo_custom.py --slug mon_signal --type signal [--execute]   # nouveau
```
`generalisation: no` = supprime la fiche ciblée + dépendances directes ; `yes` = supprime l'archétype + toutes ses instances scénario. Réinitialise `last_validated.json`, nettoie `_entities_list.json`. `generalisation` n'a pas de sens pour le type `signal` (ignoré si fourni — masqué côté GUI via `hide_when`, voir §7).

**Type `signal` (nouveau)** — pipeline entièrement différent des entités/événements ci-dessus (aucune notion d'archétype/instance) :
- `resolve_signal_variables()` : retrouve les fiches variables concernées via `variables_cibles` de la fiche d'audit `signaux_custom/{slug}.md` ; repli sur un scan complet de `variables/*.md` si la fiche est absente.
- `remove_signal_from_variable()` : retire l'annotation section 7 et le(s) bloc(s) section 12 (gère aussi le cas dupliqué par erreur — vu en conditions réelles le 26 juillet, voir `inject_custom_signals.py`).
- `remove_signal_from_registre()` : retrait par correspondance exacte de colonne (pas de sous-chaîne — un slug peut être substring d'un autre) + **recalcul du total en tête de fichier**.
- `remove_signal_fiche_and_logs()` : supprime la fiche d'audit + nettoie `signaux_custom/processed.yaml`/`needs_review.yaml` (dossier distinct de `evenements_custom/`, propre au pipeline signaux).
- **Testé en conditions réelles** le 26 juillet contre les fichiers effectivement modifiés en session (dry-run puis exécution réelle) — résultat identique à un nettoyage fait à la main juste avant.

**Deux bugs supplémentaires trouvés le 27 juillet, en usage réel prolongé (pas en test isolé) :**
- **`resolve_signal_variables()` ratait une variable sur un signal généré en plusieurs runs partiels** — un premier run avait réussi sur une variable puis planté sur la suivante (avant `write_custom_fiche()`), un second run réussi ensuite sur d'autres variables avait bien créé la fiche d'audit, mais avec un `variables_cibles` qui ne couvrait QUE ce second run — la première variable, pourtant bien écrite sur disque, restait invisible à l'outil. Corrigé : `resolve_signal_variables()` croise désormais la fiche d'audit avec un scan direct du registre (`_variables_depuis_registre()`, indépendant de la fiche, reflète tout l'historique d'écriture) — union des deux sources, avec avertissement explicite si le registre révèle une variable absente de la fiche.
- **Bug plus sérieux, provoqué par ce script lui-même** : le regex de retrait du bloc section 12 (`  - signal: {slug}` jusqu'à la prochaine entrée) ne s'arrêtait que sur une autre entrée `- signal: `, jamais sur la fence de fermeture ` ``` `. Conséquence : retirer le **dernier** signal d'un bloc section 12 avalait aussi la fence de fermeture avec lui, cassant le fichier exactement comme le bug de fence manquante d'`inject_custom_signals.py` (même symptôme, cause différente — ici c'est `undo_custom.py` qui casse le fichier, pas un éditeur externe). Repéré parce qu'un fichier déjà réparé une fois s'est retrouvé de nouveau cassé après un nettoyage `--execute`. Corrigé : le lookahead négatif du regex s'arrête maintenant sur `  - signal: ` **et** sur ` ``` ` — testé sur les deux cas (signal en dernière position, signal au milieu du bloc).
- ⚠️ **Point de vigilance pour toute future modification de ce script** : ces deux bugs n'ont été trouvés qu'après plusieurs cycles d'usage réel sur le même signal (queue → échec → nettoyage → re-queue → nouvel échec ailleurs), pas par la suite de tests initiale du 26 juillet. Un script "testé en conditions réelles" une fois ne veut pas dire "à l'abri des cas limites" — les bords de fichier (première/dernière entrée d'un bloc) méritent un test dédié à chaque nouvelle fonction de retrait de contenu structuré.

---

## 4. Pipeline géographie

### `build_geographie_monde.py` 🪦 **RETIRÉ DU SIDEBAR (26 juillet 2026)** — voir §6 — **étape 1**
Rétro-construit la bible géopolitique plate d'un scénario à partir du contenu narratif existant (instances, événements custom), pour servir de référentiel et éviter la dérive de nomenclature (ex. 33 variantes de "bloc eurasien" trouvées avant ce script). Tier `structured_strict`. Déjà lancé sur les 6 scénarios (définitifs, confirmé par David). Nouvelle règle actée le 26 juillet 2026 : un script one-shot n'a plus sa place dans le panneau, même pour un usage `--force` ponctuel -- reste utilisable en CLI directe.
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

**Bug trouvé et corrigé le 31 juillet 2026** — plantait en fin de run réel (`AttributeError: 'str' object has no attribute 'get'`) sur les zones dont `lieux_emblematiques` contient une entrée en simple chaîne au lieu du dict structuré `{"nom": ..., "type": ..., "notes": ...}` attendu. Pas un cas isolé : 195 entrées sur les 6 fichiers `geographie/*.md`, héritées d'une version antérieure de `build_geographie_monde.py`. Corrigé en 3 endroits : normalisation centrale à la lecture (`_normalize_lieux_emblematiques()`, dans `load_existing_geographie()`), tolérance de format dans `dedupe_promoted_lieux()` (pour les `new_zones` proposées par le LLM, hors normalisation) et dans `build_geographie_md()` (+ fix cosmétique : parenthèses vides omises quand `type` est absent). Même tolérance ajoutée par cohérence dans `fix_lieux_residuels.py` (risque réel identifié — chargeur de fichier indépendant, même pattern) et `build_geographie_monde.py` (risque écarté à l'audit, mais rendu identique par cohérence). Voir `fix_lieux_emblematiques_format.py` (§6) pour le nettoyage définitif des fichiers sources.

### `complete_geographie_coverage.py` 🪦 **RETIRÉ DU SIDEBAR (25 juillet 2026)** — voir §6

⚠️ **Ne plus utiliser en routine.** Remplacé par `generer_zones_topdown.py`
(P24 étape C.3, §4 plus bas) qui couvre le même cas d'usage (pays sans
zone) avec en plus la conscience du patron spatial narratif dès la
génération, et une intégration complète à `chantiers_geographie.yaml`
(fichier unique de suivi du pipeline géographie) au lieu de son propre
`coverage_proposals_{scenario}.yaml` isolé. Entrée retirée de
`scripts_config.json` le 25 juillet 2026 (audit du panneau GUI) — script
conservé sur disque pour référence, détail au §6. Description d'origine
ci-dessous conservée pour comprendre le fonctionnement historique si
besoin de comparer avec `generer_zones_topdown.py`.

<details>
<summary>Description d'origine (avant dépréciation)</summary>

**étape 3, workflow obligatoire review→apply** (historique)
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

**Anomalie repérée, non creusée** : pour 5 des 6 scénarios, seule la version
`coverage_proposals_{scenario}.applied.yaml` subsiste (brouillon consommé
normalement). Pour `reference`, `coverage_proposals_reference.yaml` existe
**sans** le suffixe `.applied` — cycle jamais terminé sur ce scénario, ou
fichier dupliqué/mal renommé à un moment donné. Sans impact opérationnel
(script retiré, plus aucun code actif ne lit ces fichiers) ; laissé tel
quel pour l'instant.

</details>

### `extract_localisation.py` 🔁 🧩
Extrait le champ `localisation` (zone/lieu/type_lieu) sur les fiches riches (hors `officialise_minimal`) + toutes les `event_instances`. Trois issues : lieu trouvé, transnational (vide assumé), ou ambigu (`statut: review_manuelle`). Tier `volume`.
```bash
python3 extract_localisation.py --dry-run
python3 extract_localisation.py
python3 extract_localisation.py --scenario NOM
python3 extract_localisation.py --slug SLUG
python3 extract_localisation.py --force          # retraite les fiches déjà faites
python3 extract_localisation.py --report-only
python3 extract_localisation.py --scan-pending   # nouveau, 31 juillet -- voir ci-dessous
python3 extract_localisation.py --scan-pending --json
```

**Nouveau mode `--scan-pending` (31 juillet 2026)** — purement mécanique (`collect_fiches()` ne fait que lire du frontmatter, aucun appel LLM). Liste les fiches qui seraient réellement traitées par un run normal, au lieu de forcer `--slug` à lister toutes les instances sans distinguer celles déjà localisées. Branché côté GUI (`--slug` en `slug_select`) via `gui/app.py::_scan_localisation_candidats()` → `/api/slugs?type=fiches_a_localiser`. **Limite connue** : la case `--force` du panneau ne change pas dynamiquement le contenu du menu (toujours limité aux fiches en attente) — pour retraiter une fiche précise déjà faite, passer par `--scenario` (lot) plutôt que `--slug` (fiche unique).

**Testé en conditions réelles le 31 juillet** — 146 fiches (`breakdown`, `--force`) : 92 extraites, 53 transnationales (vide assumé), 1 ambiguë, 0 erreur. Vérifié explicitement : aucun doublon de bloc `localisation:` généré malgré le retraitement forcé (`inject_localisation()` supprime l'éventuel bloc existant avant d'insérer le nouveau, cas `--force` prévu dans le code — confirmé par `grep -rc "^localisation:"` sur le vault réel, 0 fichier avec plus d'une occurrence).

### `review_localisation.py` 🔁 🧩
Review interactive des fiches `statut: review_manuelle`, une par une : `[V]` valider la suggestion, `[C]` choisir une autre zone, `[0]` vide assumé, `[S]` skip. Tier `volume`.
```bash
python3 review_localisation.py
python3 review_localisation.py --scenario NOM
python3 review_localisation.py --auto-resolve    # mode non-interactif (post-injection auto-cycle)
python3 review_localisation.py --dry-run
```

**⚠️ Bug critique trouvé et corrigé le 31 juillet 2026, côté panneau GUI uniquement.** Le mode par défaut (`--auto-resolve` absent) est interactif (`input()` en boucle, choix au clavier) — mais **tous** les scripts lancés depuis le GUI utilisent `stdin=subprocess.DEVNULL` (décision documentée du 12 juillet, §7). Un `input()` sur stdin DEVNULL lève une `EOFError` non gérée dans `run_review()` : lancé sans cocher la case depuis le panneau, le script aurait planté dès la première fiche. Corrigé dans `scripts_config.json` uniquement (le script Python n'a pas changé, le mode interactif reste entièrement fonctionnel en CLI) : `--auto-resolve` passé de "décochée par défaut, optionnelle" à **cochée par défaut, obligatoire** (`required: true`) — impossible de lancer le mode cassé depuis le GUI. Testé en réel après correctif : 1 fiche résolue, motif cohérent, écriture réussie.

**Section GUI fusionnée le 31 juillet 2026** — la section "Localisation" du sidebar (2 entrées : ce script + `extract_localisation.py`) a été supprimée ; les deux sont maintenant dans "Géographie — diagnostic" (`gui/app.js`, tableau `SECTIONS`, + `scripts_config.json`). Décision éditoriale de David après discussion : ces deux scripts touchent `instances/*.md`/`event_instances/*.md` (pas `geographie/*.md` comme les autres diagnostics géo), donc l'argument "quel fichier ça touche" plaidait pour les garder séparés, mais le flux d'usage enchaîné (géographie → rattachement des fiches) a pesé plus lourd dans la décision finale.

### `check_zones_coherence.py` 🔁 🗄️ 🪦 **RETIRÉ DU SIDEBAR (26 juillet 2026)** — voir §6 — **diagnostic pur, lecture seule sauf `--write-chantiers`/`--marquer-resolus`**
Vérifie : (1) parsing YAML valide des fiches `geographie/{scenario}.md`, (2) pays réels totalement absents de toute zone, (3) pays rattachés uniquement à une sous-zone sans N1, (4) entrées obsolètes parmi les chantiers `pays_sans_zone` de `chantiers_geographie.yaml` (voir §4bis — remplace l'ancien `zones_manquantes.yaml` depuis le 25 juillet 2026).
```bash
python3 check_zones_coherence.py --scenario NOM
python3 check_zones_coherence.py --all
python3 check_zones_coherence.py --all --write-chantiers      # ajoute un chantier pays_sans_zone par pays absent
python3 check_zones_coherence.py --all --marquer-resolus       # passe statut='traite' aux chantiers devenus obsolètes (le pays a déjà une zone N1) -- n'a d'effet qu'avec --all
```
Réflexe recommandé : lancer `--all --write-chantiers` en fin de session, après tout `--apply` ou toute série de bascules sur la carte. Intégré au GUI (sidebar + orchestrateur `scan_geographie_complet.py`, voir plus bas), sélectionnable seul ou combiné.

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

### `check_origine_reelle_coherence.py` 🔁 🗄️ 🪦 **RETIRÉ DU SIDEBAR (26 juillet 2026)** — voir §6 — **diagnostic pur, lecture seule sauf `--write-chantiers`** *(14 juillet, P22 signal 1 — flag renommé le 25 juillet)*
Garde-fou de cohérence géographique : compare le pays d'une zone `ville`/`region_administrative` à l'union des pays de toute sa lignée d'ancêtres. Avertissement seul, jamais de blocage. Résolution ville→pays en cascade (extraction directe → alias adjectival → table statique `VILLE_PAYS` → `--resolve-llm`, tier `structured_strict`, cache dans `cache_ville_pays_llm.json`). Pour chaque incohérence sans candidat de reparent parmi les zones N1 du scénario : ajoute un chantier `pays_sans_zone` dans `chantiers_geographie.yaml` (voir §4bis — remplace l'ancien `zones_manquantes.yaml`). Tableau récapitulatif markdown généré en fin de run, prêt à copier dans le backlog.
```bash
python3 check_origine_reelle_coherence.py --scenario NOM
python3 check_origine_reelle_coherence.py --all
python3 check_origine_reelle_coherence.py --all --resolve-llm
python3 check_origine_reelle_coherence.py --all --write-chantiers   # remplace --write-zones-manquantes depuis le 25 juillet
```
État au 25 juillet : 0 incohérence sur les 124 zones ville/région des 6 scénarios.

### `check_type_entite_coherence.py` 🔁 🗄️ 🪦 **RETIRÉ DU SIDEBAR (26 juillet 2026)** — voir §6 *(14 juillet, P26)*
Détecte (et corrige avec `--apply`) les entrées `origine_reelle` sans `type_entite` du tout — oubli de champ à l'écriture, masque des cas pour `check_origine_reelle_coherence.py`. Édition ligne-à-ligne du texte brut (pas de re-dump YAML complet) pour ne toucher que les lignes concernées. Backup `.bak` automatique avec `--apply`.
```bash
python3 check_type_entite_coherence.py --all                # aperçu, lecture seule
python3 check_type_entite_coherence.py --all --apply         # corrige, backup .bak
```
État au 25 juillet : 1 entrée sans `type_entite` détectée sur `policy_reform` (`ameriques_reformees` / Groenland). **Corrigée le 2 août 2026** (`--scenario policy_reform --apply`, diff chirurgical de 2 lignes, backup `.bak` automatique). Rescan complet des 6 scénarios le même jour : zéro entrée sans `type_entite` restante nulle part dans le vault.

### `check_conventions_territoires.py` 🔁 🗄️ 🪦 **RETIRÉ DU SIDEBAR (26 juillet 2026)** — voir §6 — **diagnostic pur, lecture seule** *(14 juillet, P27)*
Distinct de `check_origine_reelle_coherence.py` : au lieu de comparer une zone à sa chaîne de parenté, compare un même territoire ambigu (dépendance/collectivité, table `TERRITOIRES_AMBIGUS` à enrichir manuellement) **entre les 6 scénarios**. Vérifie la conformité à la convention décidée le 14 juillet : un territoire dépendant/autonome est toujours distinct de son pays souverain réel quand il apparaît dans un scénario — sauf exception narrative explicitement actée pour un scénario donné. N'a de sens qu'avec `--all` (comparaison entre scénarios).
```bash
python3 check_conventions_territoires.py --all
```
**P27 clos le 15 juillet.** Des 11 cas détectés le 14 juillet (Groenland ×3, Écosse ×3, Pays de Galles ×5) : 1 traité par split (Écosse/`breakdown`), 2 réglés par réaffectation directe ou déjà corrects (Groenland/`breakdown` et `eco_communalism`), 8 acceptés tels quels comme exceptions narratives (Royaume-Uni resté politiquement uni dans `breakdown` pour Angleterre+Galles, et entièrement dans `fortress_world`) ou décision explicite de clôture. Ce script continuera donc à signaler ces 8 cas comme "non conformes" à la convention générale — c'est attendu, pas un bug ni un oubli. Détail complet au backlog, P27.
Retest du 25 juillet (`--all`) : toujours 3 territoires non conformes signalés (Groenland, Écosse, Pays de Galles) -- comportement attendu, cf. ci-dessus.

### `check_patron_spatial_coherence.py` 🔁 🗄️ 🪦 **RETIRÉ DU SIDEBAR (26 juillet 2026)** — voir §6 — **diagnostic pur, lecture seule sauf `--write-chantiers`** *(P24 étape C.1, 25 juillet 2026)*
Compare la description/le type de chaque zone niveau 1 au patron spatial narratif de son scénario (`patrons_spatiaux.py`). Signal qualitatif distinct des diagnostics structurels ci-dessus : une zone peut être dans le bon pays (aucune incohérence `origine_reelle`) tout en incarnant une logique de gouvernance incompatible avec son scénario. Comparaison en lot (un appel LLM par scénario), tier `structured_strict`, résultat mis en cache (`patron_spatial_cache.json`, keyé sur un hash du contenu soumis). Avertissement seul, jamais de blocage -- consigne au LLM d'être conservateur (« un faux positif coûte plus cher qu'un faux négatif »). Zones sans description exploitable (< 20 caractères) exclues du jugement plutôt que jugées sur leur nom seul.
```bash
python3 check_patron_spatial_coherence.py --scenario NOM
python3 check_patron_spatial_coherence.py --all
python3 check_patron_spatial_coherence.py --all --no-cache        # force un nouvel appel LLM
python3 check_patron_spatial_coherence.py --all --write-chantiers # ajoute un chantier zone_suspecte par zone suspecte
```
État au 25 juillet : 15 zones suspectes actives sur les 5 scénarios autres que `breakdown` (0 sur `breakdown`) -- toutes enregistrées comme chantiers `a_traiter`, 3 déjà pourvues d'une proposition (`reference`), 1 déjà appliquée et traitée (`europe_occidentale_reconstructee`/`reference`). Note de variance : deux passages `--no-cache` consécutifs le même jour ont donné des listes légèrement différentes sur les cas limites (ex. `pacte_des_souverains` apparu après correction d'`europe_occidentale_reconstructee`) -- propriété du LLM (`temperature=0.0` n'élimine pas toute variance côté API), pas un bug.

---

## 4bis. Chantiers géographie — fusion et migration (P24 étape C, 25 juillet 2026)

**Contexte** : avant cette date, le suivi des problèmes géographiques détectés (zones suspectes, pays sans zone) était éclaté sur plusieurs fichiers séparés (`patron_spatial_suspectes.yaml`, `zones_manquantes.yaml`, `zones_proposees_topdown_{scenario}.yaml` ×6) — impossible d'avoir "une seule liste de ce qui reste à traiter". Fusionné en **un seul fichier**, `documentation/need_action/chantiers_geographie.yaml`, avec un vocabulaire de statuts réduit à 3 valeurs : `a_traiter` (défaut) / `ignore` (choix narratif légitime, ne plus jamais réafficher) / `traite` (zone modifiée, problème réglé).

### `chantiers.py` 🔁 🧩 — **module partagé, jamais lancé seul**
Lecture/écriture de `chantiers_geographie.yaml`. API : `ajouter_chantier()` (dédoublonné par id `scenario__cible_slugifiee`, ne touche jamais une entrée déjà présente), `get_chantier()`, `mettre_a_jour_chantier()` (modifie une entrée existante, ne crée jamais), `chantiers_eligibles()` (statut `a_traiter`, filtrable par scénario/type), `chantiers_prets_a_appliquer()` (statut `a_traiter` + `proposition` non nulle + `proposition_approuvee: true`).

⚠️ **Garde-fou important (bug trouvé et corrigé le 25 juillet, avant tout test réel)** : `charger_chantiers()` lève `ChantiersCorrompuError` si le fichier existe mais contient du YAML invalide, plutôt que de silencieusement renvoyer une liste vide. Sans ce garde-fou, un fichier corrompu (édition manuelle ratée, écriture interrompue) aurait pu être écrasé au prochain `ajouter_chantier()`/`mettre_a_jour_chantier()` avec seulement la nouvelle entrée — perte silencieuse de tout le reste. Un fichier corrompu doit être réparé à la main avant de pouvoir écrire quoi que ce soit dedans.

Schéma d'une entrée : `id`, `scenario`, `type` (`zone_suspecte`|`pays_sans_zone`), `cible` (slug de zone ou nom de pays), `probleme`, `source_diagnostic`, `date_detection`, `statut`, `proposition` (null ou zone complète), `proposition_approuvee` (bool), `date_proposition`, `date_traitement`. Champs additionnels tolérés (`**extra`), ex. `zone_incoherente_a_reparenter` (origine_reelle), `proposition_issues` (generer_zones_topdown.py).

### `migrer_vers_chantiers.py` 🪦 (one-shot, déjà exécuté le 25 juillet) 🗄️
Migration one-shot des 3 anciens fichiers vers `chantiers_geographie.yaml`, sans rien écraser : `patron_spatial_suspectes.yaml` (mapping statut : `a_traiter`/`en_attente_c2`→`a_traiter`, `accepte_tel_quel`→`ignore`, `corrige_manuellement`/`corrige_via_c2`→`traite`), `zones_manquantes.yaml` (`blanc_intentionnel`→`ignore`, sinon `a_traiter`), et `zones_proposees_topdown_{scenario}.yaml` ×6 (attache leur `proposition` au chantier déjà migré, avec `proposition_approuvee` = leur `valide`). N'attache/ne crée jamais rien sur un chantier déjà plus avancé (proposition déjà présente, statut déjà différent de `a_traiter`) -- protège tout travail plus récent d'un écrasement par une donnée legacy périmée.
```bash
python3 migrer_vers_chantiers.py            # aperçu (dry-run par défaut)
python3 migrer_vers_chantiers.py --apply     # écrit pour de vrai
```
**Exécuté le 25 juillet** : 2 chantiers `traite` créés (`geneve_bunker_institutions`/`breakdown`, `nuuk_forteresse`/`fortress_world`, tous deux `corrige_via_c2`), 12 propositions récupérées gratuitement (évite de repayer des appels LLM) sur `fortress_world`/`new_sustainability`/`eco_communalism`/`policy_reform`, 0 orpheline, 0 écrasement. Fichiers legacy conservés sur disque comme filet de sécurité (non supprimés).

### `zoning_topdown.py` 🔁 🧩 — **fonction cœur (P24 étape C.2), double usage**
Fonction pure (LLM in, JSON out) : `generer_zone_topdown(scenario, raison, ...)` génère une zone niveau 1 complète (`raison="pays_sans_zone"`) ou révise une zone existante sur un sous-ensemble de champs (`raison="zone_suspecte"`, seuls `description`/`type`/`statut`/`tensions_internes`/`relations` acceptés du LLM -- `slug`/`origine_reelle` imposés mécaniquement, jamais laissés au LLM). Passe par `validate_zone()`/`clean_zone_relations()` (`enrich_geographie_recursive.py`) avant retour. Ne touche jamais le vault -- lecture/écriture à la charge de l'appelant.

**Double usage du bloc `if __name__ == "__main__"`** (décision actée le 25 juillet) : mode test manuel lisible (sans `--json`, entrée sidebar GUI `zoning_topdown_test`), ET mode machine (`--json`, appelé en sous-processus par l'onglet Carte pour générer une proposition -- PAS un doublon de l'entrée sidebar, deux usages distincts du même fichier).
```bash
python3 zoning_topdown.py --scenario NOM --pays Andorre
python3 zoning_topdown.py --scenario NOM --zone-suspecte SLUG --raison-suspicion "texte"
python3 zoning_topdown.py --scenario NOM --pays Andorre --json   # sortie machine
```

### `generer_zones_topdown.py` 🔁 🧩 — **CLI batch (P24 étape C.3), migré vers chantiers.py le 25 juillet**
`--review-topdown` : génère une proposition (via `zoning_topdown.generer_zone_topdown()`) pour chaque chantier `a_traiter` de `chantiers_geographie.yaml` (type `pays_sans_zone` et/ou `zone_suspecte`, filtrable via `--source`), l'attache à l'entrée existante (`proposition`, `date_proposition`, `proposition_issues`, `proposition_approuvee: false`). Ne régénère PAS un chantier déjà pourvu d'une proposition non approuvée, sauf `--force` explicite -- protège une relecture/édition manuelle en cours.
`--apply-topdown` : consomme `chantiers.chantiers_prets_a_appliquer()` (statut `a_traiter` + proposition + `proposition_approuvee: true`), applique dans le vault (écriture zone complète pour `pays_sans_zone` + sync `zones_pays.json` + propagation des sous-zones orphelines via `reparenter_sous_zones_orphelines.py` ; modification en place des seuls champs révisables pour `zone_suspecte`), puis passe le chantier à `statut: traite`. **`--cible` (ajouté le 1er août 2026)** : restreint l'application à un seul chantier précis (slug de zone ou nom de pays) au lieu de tous les chantiers prêts du scénario -- utilisable uniquement avec `--scenario` (incompatible avec `--all` et `--review-topdown`, validé explicitement en CLI).
```bash
python3 generer_zones_topdown.py --review-topdown --scenario NOM [--source pays_sans_zone|zones_suspectes|both] [--force]
python3 generer_zones_topdown.py --review-topdown --all
python3 generer_zones_topdown.py --apply-topdown --scenario NOM
python3 generer_zones_topdown.py --apply-topdown --all
python3 generer_zones_topdown.py --apply-topdown --scenario NOM --cible barcelone_hub
```
Approbation : `proposition_approuvee: false → true` à la main dans `chantiers_geographie.yaml`, via `chantiers.mettre_a_jour_chantier(scenario, cible, proposition_approuvee=True)` en ligne de commande, ou depuis le 26 juillet via le bouton "Approuver" de l'onglet Chantiers du GUI (§4.5).
Testé et validé en conditions réelles le 25 juillet : diff d'application chirurgical confirmé (`europe_occidentale_reconstructee`/`reference` -- seule la phrase problématique modifiée, aucune fuite des 21 pays gonflés de la proposition dans le vault). `--cible` testé en conditions réelles le 1er août via le bouton "✓ Appliquer ce chantier" de l'onglet Chantiers : chantier ciblé passé à `traite`, confirmé retrouvable via le filtre Statut "Traités" après rafraîchissement (disparition normale de la vue "À traiter" par défaut). **Cas à plusieurs chantiers approuvés simultanément vérifié le 2 août 2026** (données de test synthétiques, 2 chantiers approuvés sur le même scénario) : `--cible` n'affecte que le chantier ciblé, l'autre reste strictement intact (statut, `chantiers_geographie.yaml`, et fichier `geographie/{scenario}.md`) — comportement garanti par le filtrage en amont dans `chantiers_prets_a_appliquer(scenario, cible=...)`.

### `reparenter_sous_zones_orphelines.py` 🔁 🧩 — **P24 étape C, extension du 25 juillet, double usage**
Détecte et reparente les sous-zones (niveau 2/3) dont l'`origine_reelle` résout vers un pays qui vient d'être déplacé vers une nouvelle zone N1, mais dont le parent actuel ne le représente plus (résolution ville→pays via `resoudre_pays()`, `check_origine_reelle_coherence.py` -- détecte des cas que le suivi natif du split GUI, P7, ne reconnaît pas, ex. une ville qui représente un pays sans le nommer). Appelé automatiquement par `generer_zones_topdown.py --apply-topdown` (import direct) ET utilisable seul après un reparent manuel dans l'onglet Carte (sous-processus + `--json`, P24 étape C.4).
```bash
python3 reparenter_sous_zones_orphelines.py --scenario NOM --zone-cible SLUG
python3 reparenter_sous_zones_orphelines.py --scenario NOM --zone-cible SLUG --json
python3 reparenter_sous_zones_orphelines.py --scenario NOM --scan-candidates          # nouveau, 31 juillet
python3 reparenter_sous_zones_orphelines.py --scenario NOM --scan-candidates --json
```

**Nouveau mode `--scan-candidates` (31 juillet 2026)** — lecture seule, aucun appel LLM (`resoudre_pays()` ne consulte que table statique + cache). Liste uniquement les zones N1 ayant *actuellement* au moins une sous-zone orpheline en attente, au lieu de forcer à connaître le bon slug à l'avance parmi les 16 à 42 zones N1 d'un scénario. Branché côté GUI (`--zone-cible` en `slug_select`) via `gui/app.py::_scan_reparent_candidats()` → `/api/slugs?type=zones_a_reparenter` (sous-processus + JSON, tolérant aux échecs, même principe que l'appel automatique post-reparent Carte).

**Bug corrigé le 31 juillet 2026 (`gui/app.py::_scan_zone_slugs`)** — le menu `--zone-cible` (avant l'ajout du scan ci-dessus, pour `slug_type: "zones"`/`"zones_all"`) ne remontait qu'**une seule zone N1** par scénario, peu importe leur nombre réel. Cause : découpage par regex (`re.split` sur `---`) suivi de `.search()` (première correspondance seulement), alors que `geographie/{scenario}.md` n'a que 2 délimiteurs `---` au total (un seul bloc YAML englobant toutes les zones, pas un bloc par zone). Corrigé par un vrai parsing YAML, sur le même principe que `_scan_zone_slugs_hier` juste à côté (qui n'avait pas ce bug).

**Zones à cheval sur deux blocs (transnationales)** — le scan peut légitimement boucler sur un même cas : une sous-zone dont l'`origine_reelle` couvre des pays revendiqués par deux zones N1 différentes reste "orpheline" côté perdant quel que soit le sens du reparent. Pas un bug — cas réels rencontrés et tranchés le 31 juillet : Bassin Caspien (breakdown, Iran vs Kazakhstan/Azerbaïdjan/Turkménistan — tranché), Corridors Migratoires Anatoliens (eco_communalism, Syrie vs Turquie — tranché), Réseau Terrafond des Bassins (eco_communalism, Maghreb vs Europe occidentale — **laissé tel quel**, transnational voulu d'après la description narrative des deux zones). Diagnostic : comparer les pays résolus de la sous-zone orpheline avec ceux de sa cible candidate ET de son parent actuel — si les deux se recoupent, c'est structurel, pas une erreur de saisie.

**Point de vigilance pour tout test futur** : `resoudre_pays()` dépend de `gui/zones_pays.json` (200 pays) pour extraire correctement les pays d'une entité composée (ex. "Mer Caspienne (zone frontalière Russie/Kazakhstan/...)"). Sans ce fichier, la résolution échoue silencieusement sur ces entités et fausse les résultats du scan.

### `scan_geographie_complet.py` 🔁 🗄️ — **orchestrateur, réécrit le 25 juillet (harmonisation + sélection d'étapes)**
Lance en séquence tout ou partie des 5 diagnostics géographie (`check_zones_coherence.py`, `check_type_entite_coherence.py`, `check_origine_reelle_coherence.py`, `check_conventions_territoires.py`, `check_patron_spatial_coherence.py`), en sous-processus indépendants, résumé consolidé à la fin. **Depuis le 26 juillet 2026, ces 5 scripts ne sont plus des entrées individuelles du panneau GUI** (retirées après parité de flags confirmée + tests réels en conditions réelles sur les 4 cases restantes, voir §6) — ils restent utilisables en CLI directe pour un usage ponctuel hors GUI, mais le seul point d'entrée du panneau pour les diagnostics géographie est désormais `scan_geographie_complet` (avec sélection d'étape via `--run-*` pour reproduire l'équivalent d'un lancement individuel).

**Harmonisation `--write-chantiers`** : un seul flag propagé aux étapes 1/3/5 (remplace les anciens `--write-suspectes`/`--write-zones-manquantes`, qui ne correspondaient plus à aucun flag réel des scripts sous-jacents depuis leur migration). Au passage, l'étape 1 gagne une propagation d'écriture qu'elle n'avait jamais eue avant.

**Sélection d'étapes** (nouveau) : `--run-zones`/`--run-type-entite`/`--run-origine-reelle`/`--run-conventions`/`--run-patron-spatial` -- aucun passé = les 5 tournent (comportement historique) ; un ou plusieurs passés = seulement ceux-là. Numérotation et résumé dynamiques (`Étape 1/2`, notes de fin conditionnées à l'étape réellement lancée).

**`--marquer-resolus`** (nouveau) : propage à l'étape 1 (`check_zones_coherence.py`) -- avertit si utilisé sans `--all` (n'a d'effet qu'en mode "tous les scénarios", contrainte du script sous-jacent). Complète la parité de flags entre l'entrée individuelle et l'orchestrateur.

**6e étape optionnelle** `--generer-propositions-topdown` : lance `generer_zones_topdown.py --review-topdown` -- couvre maintenant les deux types de chantiers (pays sans zone ET zones suspectes, unifiés par `chantiers.py`), contre un seul avant la fusion. Coûte de vrais appels LLM, jamais par défaut. N'applique jamais rien.
```bash
python3 scan_geographie_complet.py --all
python3 scan_geographie_complet.py --all --write-chantiers
python3 scan_geographie_complet.py --scenario NOM --run-patron-spatial --no-cache-patron-spatial
python3 scan_geographie_complet.py --all --apply-type-entite --resolve-llm --write-chantiers --generer-propositions-topdown
```
Testé en conditions réelles le 25 juillet sur les 6 scénarios (`--all --write-chantiers`) : propagation confirmée aux 3 étapes concernées, idempotence vérifiée sur double passage.

### Restructuration de zones — P7, dans l'onglet Carte (pas un script séparé)
**Correction d'une confusion documentaire** : ce manuel décrivait auparavant `restructure_zones.py` comme un script `generator/` "planifié, pas encore codé". C'est inexact depuis le 13 juillet — P7 a été construit directement dans l'onglet Carte du GUI (`gui/app.py`/`app.js`), pas comme script séparé. **L'entrée fantôme correspondante dans `scripts_config.json` a été retirée** (confirmé le 2 août 2026 — le panneau compte 18 entrées, aucune trace de `restructure_zones`). Détail complet du workflow en §7 (rename, reparent, split).

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

**Entrée `validate` du panneau GUI testée le 2 août 2026** — RAS. C'était la dernière des 18 entrées du panneau sidebar encore non validée en conditions réelles ; les 18 sont maintenant toutes confirmées.

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
| `fix_lieux_emblematiques_format.py` | **Nouveau (31 juillet 2026)**. Normalise à la source les entrées `lieux_emblematiques` en simple chaîne (au lieu du dict `{"nom", "type", "notes"}` attendu) dans `geographie/*.md` — cause du crash de `enrich_geographie_recursive.py` documenté plus haut. Purement mécanique, aucun appel LLM, `.bak` automatique. `--scenario NOM`\|`--all`, `--dry-run`. Testé en conditions réelles : 195 entrées détectées et normalisées sur les 6 scénarios. | 🪦 One-shot, déjà exécuté sur les 6 scénarios le 31 juillet — ne relancer que si de nouvelles zones en simple chaîne apparaissent (ex. import externe) |
| `rebuild_processed.py` | Reconstruit les entrées manquantes de `processed.yaml` pour des événements custom géo injectés manuellement (source `rééquilibrage_geo_2026-06`) non tracés. | 🪦 One-shot, déjà exécuté |
| `check_arctique.py` | Snippet de debug ad hoc (grep de "arctique" dans `policy_reform.md`), chemin en dur, pas de CLI. | 📦 Snippet jetable, ne pas industrialiser |
| `remove_zone_manquante.py` | Snippet ad hoc : retire une entrée précise (Arctique/policy_reform) de `zones_manquantes.yaml`, chemin en dur. | 📦 Snippet jetable, déjà exécuté |
| `complete_geographie_coverage.py` | Affectait les pays sans zone via LLM, workflow `--review`/`--apply` propre (`coverage_proposals_{scenario}.yaml`), sans intégration à `chantiers_geographie.yaml`. Remplacé par `generer_zones_topdown.py` (P24 étape C.3), qui couvre le même cas avec la conscience du patron spatial et l'intégration au fichier de suivi unique. | 🪦 **Retiré du sidebar le 25 juillet 2026** (audit du panneau GUI), conservé sur disque pour référence — voir détail §4 |
| `check_zones_coherence.py` | Diagnostic géographie (pays sans zone / sous-zone sans N1 / chantiers obsolètes). Toujours utilisable seul en CLI, y compris `--write-chantiers`/`--marquer-resolus`. | 🪦 **Retiré du sidebar le 26 juillet 2026** — parité de flags à 100% avec `scan_geographie_complet --run-zones`, voir §4bis. |
| `check_type_entite_coherence.py` | Diagnostic (et correction `--apply`) des `type_entite` manquants. Toujours utilisable seul en CLI. | 🪦 **Retiré du sidebar le 26 juillet 2026** — parité de flags à 100% avec `scan_geographie_complet --run-type-entite`, voir §4bis. |
| `check_origine_reelle_coherence.py` | Garde-fou de cohérence origine_reelle vs chaîne de parenté (P22 signal 1). Toujours utilisable seul en CLI, y compris `--resolve-llm`/`--write-chantiers`. | 🪦 **Retiré du sidebar le 26 juillet 2026** — parité de flags à 100% avec `scan_geographie_complet --run-origine-reelle`, voir §4bis. |
| `check_conventions_territoires.py` | Vérifie qu'un même territoire ambigu est traité de façon cohérente entre les 6 scénarios (P27). Toujours utilisable seul en CLI. | 🪦 **Retiré du sidebar le 26 juillet 2026** — parité de flags à 100% avec `scan_geographie_complet --run-conventions`, voir §4bis. |
| `check_patron_spatial_coherence.py` | Compare chaque zone N1 au patron spatial narratif de son scénario via LLM (P24 étape C.1). Toujours utilisable seul en CLI, y compris `--no-cache`/`--write-chantiers`. | 🪦 **Retiré du sidebar le 26 juillet 2026** — parité de flags à 100% avec `scan_geographie_complet --run-patron-spatial`, voir §4bis. |
| `fix_alliance_suffixes.py` | Correction mécanique (sans API) du suffixe `_{scenario}` manquant dans les champs `alliances`/`oppositions`. Même famille que `fix_impact_scale.py` ci-dessus. | 🪦 **Retiré du sidebar le 26 juillet 2026** — confirmé résolu partout (`--dry-run --verbose` : 0 correction), conservé sur disque au cas où le symptôme réapparaîtrait après une future génération. |
| `build_geographie_monde.py` | Rétro-construit la bible géopolitique plate d'un scénario (étape 1 du chantier géographie). Déjà lancé sur les 6 scénarios, définitifs. | 🪦 **Retiré du sidebar le 26 juillet 2026** — one-shot par scénario, nouvelle règle : plus sa place dans le panneau même pour un `--force` ponctuel. Reste utilisable en CLI directe. |
| `generate_manual.py` | Pipeline sans appel API : affiche le prompt (system+user) du prochain article d'une série pour copier/coller dans un chat externe, avec suivi de rotation multi-articles (`state/manual_progress.json`). | 🪦 **Retiré du sidebar le 31 juillet 2026** — son cas d'usage principal (aperçu de prompt copiable) est couvert par `--dry-run` sur `generate.py`, qui affiche le même contenu sans le mécanisme de rotation de série. Reste utilisable en CLI directe pour le suivi multi-articles. |

**Audit du panneau GUI (25 juillet 2026)** — deux autres scripts avaient été
soupçonnés de faire doublon avec `generer_zones_topdown.py`/`zoning_topdown.py`
lors du même audit, mais confirmés **légitimement distincts après lecture du
code** et donc conservés dans `scripts_config.json` :
- `zoning_topdown_test` (fichier `zoning_topdown.py`) — expose le même
  fichier que celui appelé en sous-processus `--json` par l'onglet Carte
  (P24 étape C.4), mais en mode lisible pour un test manuel hors Carte.
- `reparenter_sous_zones_orphelines.py` — déjà appelé automatiquement par
  `generer_zones_topdown.py --apply-topdown`, mais aussi utilisable seul
  après un reparent fait à la main dans l'onglet Carte (P7), que le suivi
  de la Carte ne détecte pas toujours (cas réel : `valence_tours_rirec`/Espagne).

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
Cohérence de `routes_dashboard.py` avec le renommage "Modèle si forcé" ci-dessus : vérifiée et clôturée le 13 juillet (backlog P18) — bug bonus #35 trouvé au passage (`import json` manquant cassait tout `/api/dashboard`), corrigé et confirmé par David sur son GUI réel.

**Deux bugs trouvés et corrigés le 2 août 2026, tous deux liés au fichier gabarit `instances/instance_template.md` et au tri des clés YAML :**

1. **Entrée fantôme dans la carte INSTANCES du dashboard** — `instance_template.md` (le gabarit du projet, placeholders `<slug_scenario>` etc. jamais remplis, c'est normal) vit directement dans `instances/`, au milieu des vraies fiches. `_stats_instances()` le comptait comme une 711e instance ; sa valeur `scenario: <slug_scenario>` partait telle quelle dans le JSON du dashboard et le navigateur avalait la balise non échappée, affichant une entrée fantôme `: 1`. Même pollution trouvée dans `_stats_enrichissement()` (le gabarit n'a pas de champ `statut:`, il gonflait silencieusement le seau `"autre"`). **Correctif** : exclusion explicite de `instance_template.md` dans les deux fonctions — même filtre déjà présent dans `officialize_alliances.py` (ligne 223) mais absent partout ailleurs (`create_entities_and_instances.py`, `enrich_minimal.py` ×2, `extract_phantom_slugs.py`, `fix_impact_scale.py` ont potentiellement le même angle mort, non vérifié en détail). **Recommandation structurelle non appliquée** : déplacer `instance_template.md` hors de `instances/` (ex. dossier `templates/`) réglerait le problème pour tous les scripts d'un coup.

2. **Panneau Revue (`/api/review` dans `app.py`) vide malgré des fiches en échec** — `enrich_minimal.py` (`write_needs_review()`) était le seul appel `yaml.dump()` du pipeline sans `sort_keys=False` : PyYAML triait les clés alphabétiquement (`date` avant `slug`), et le parseur maison de `app.py` (`_read_needs_review_yaml()`) ne reconnaissait une nouvelle entrée que via `"- slug:"` en tête de ligne — plus aucune ligne ne matchait, toutes les entrées `needs_review_enrich.yaml` étaient silencieusement ignorées. **Correctif** : `sort_keys=False` ajouté à l'écriture. **Deuxième gap trouvé en creusant** : `/api/review` ne couvrait que 2 des 4 sources possibles de fiches en échec (`needs_review_enrich.yaml`, `evenements_custom/needs_review.yaml`) — `entites_custom/needs_review.yaml` et `signaux_custom/needs_review.yaml` (première clé `status:`, format différent) n'étaient ni lus ni comptés. **Correctif** : deux nouvelles fonctions `_parse_needs_review_entites()`/`_parse_needs_review_signaux()` + généralisation du parseur (`start_marker` optionnel) ; `_count_review_items()` (le badge, dans `routes_dashboard.py`) complété avec les deux mêmes fichiers. Limite connue : les entrées entités/signaux s'affichent avec un slug générique `(entité)`/`(signal)` plutôt que le vrai nom, le parseur ne descendant pas dans le sous-bloc `idea:` imbriqué.

### Sidebar (`scripts_config.json`) — scripts lançables en un clic
**Section génération** : `enrich_minimal`, `generate_journaux`, `validate`, `generate` (deux modes depuis le 2 août 2026 — Semi-guidé/Forcer, voir §2), `generate_series`, `generate_manual`.
**Section entités** : `create_entities`, `inject_events`, `inject_signals`, `extract_phantom_slugs`, `requeue_needs_review`, `undo_custom`, `trace_injection` (nouveau, 2 août 2026 — voir §2).
**Section maintenance** : `extract_localisation`, `review_localisation`, `enrich_geographie` (l'entrée fantôme `restructure_zones` a été retirée, confirmé le 2 août 2026 — voir §4).

Chaque entrée définit ses options (checkbox/select/number/slug_select/multi_select), ses dépendances (`requires`) et les fichiers YAML associés affichables dans le panneau de review. Vérification systématique faite le 11 juillet (backlog P6, clos) : chaque `flag` déclaré ici croisé avec l'`argparse` réel du script Python correspondant — 2 flags fantômes trouvés et supprimés (`--scenario` sur `create_entities`/`inject_events`, jamais lus par les scripts avant d'y être réintroduits avec un vrai rôle).

⚠️ Description "Section génération/entités/maintenance" ci-dessus **périmée** depuis la réorganisation du 12 juillet (8 sections nommées, voir mémoire de session) — à corriger dans une prochaine passe de mise à jour du manuel (dette documentaire connue).

#### Préréglages (`script.presets`) — nouveau type, 25 juillet 2026
Bande d'onglets au-dessus des options d'un script, pour pré-cocher un profil de checkboxes plutôt que tout configurer à la main à chaque lancement. Actuellement seul `scan_geographie_complet` en a un (Léger / À la carte / Maxi), mais le mécanisme est générique, réutilisable pour n'importe quel script à `options` multiples.
- Schéma : `script.presets = {"label": "...", "choices": [{"id", "label", "description", "values": {...}|null, "default": bool}]}`.
- `values` absent (`null`) = préréglage "no-op" (ex. "À la carte") : ne touche à AUCUNE checkbox au clic, laisse l'état courant tel quel — sert justement à permettre une sélection manuelle libre après avoir cliqué dessus.
- `values` présent (même `{}`) = coche exactement les flags listés (`true`), décoche TOUS les autres checkboxes du formulaire (y compris ceux non listés dans `values`) — un préréglage explicite est donc toujours un état complet, jamais un delta.
- Implémenté dans `app.js` par `renderPresets()`/`applyPreset()`, rendu juste avant les options standard dans `renderFormBody()`.
- ⚠️ Piège identifié en le construisant : NE JAMAIS donner la classe CSS `mode-tab` aux boutons de préréglage (utiliser `preset-tab`, classe dédiée) — `collectArgs()` sélectionne `.mode-tab.active` n'importe où dans le formulaire pour construire l'argument `--mode` du mécanisme `mode_select` (`create_entities_and_instances.py` etc.). Réutiliser `mode-tab` pour le style fait passer un préréglage pour un vrai `mode_select` et injecte `--mode None` dans n'importe quel script, y compris ceux qui n'ont pas de `--mode` du tout (planté, script réel : `scan_geographie_complet.py`).
- **"Niveau 2" corrigé et implémenté (26 juillet 2026)** : conception initiale du 25 juillet (griser l'option corrective tant que l'étape parente n'est pas cochée) invalidée par David après un premier essai -- vérifié dans les scripts Python réels (`check_type_entite_coherence.py` etc.) que le diagnostic est toujours obligatoire et tourne dans le même appel que sa correction, donc c'est l'inverse : cocher la correction force le diagnostic parent coché, décocher le diagnostic décoche sa correction. Champ `depends_on` (un seul flag parent désormais, pas de liste OU -- `--write-chantiers` s'en est trouvé exclu, voir plus bas) + paire d'écouteurs `change` posés directement dans `renderOption()`, plus `syncDependsOnParents()` pour rattraper le cas des préréglages (`.checked` posé sans évènement `change` natif). Effet de bord découvert en le construisant : le préréglage Maxi devait aussi cocher explicitement les 5 `--run-*`, sans quoi forcer 3 parents sur 5 aurait déclenché une "sélection partielle" excluant Zones/Conventions du run.

#### Audit du panneau sidebar (25 juillet 2026)
Passage en revue des 27 entrées pour repérer doublons/scripts obsolètes, **toujours vérifié sur le code réel avant toute décision** (2 candidats soupçonnés à tort, corrigés après lecture — voir ci-dessous) :
- **`complete_geographie_coverage` retiré** (27→26 entrées) : confirmé obsolète après lecture complète du fichier — même fonction que `generer_zones_topdown.py` mais pipeline totalement déconnecté de `chantiers_geographie.yaml`. Traçabilité au §6 (tableau legacy) et avertissement sur son entrée au §4.
- **`zoning_topdown_test` et `reparenter_sous_zones_orphelines` conservés** malgré une suspicion initiale de doublon : les deux fichiers ont un double usage réel (import direct + CLI autonome + appel machine `--json` par le GUI), confirmé en lisant le code plutôt qu'en se fiant à l'intuition sur le nom. Descriptions clarifiées dans `scripts_config.json` pour éviter la même fausse alerte plus tard.
- **Les 5 scripts `check_*`/diagnostic** (`check_zones_coherence`, `check_type_entite_coherence`, `check_origine_reelle_coherence`, `check_conventions_territoires`, `check_patron_spatial_coherence`) : parité de flags confirmée avec `scan_geographie_complet` + sélection d'étapes `--run-*` (voir §4bis), David a testé avec succès les 4 cases restantes (Zones, Cohérence pays/zone parente, Conventions, Patron spatial) en plus du cas déjà validé le 25 juillet (`--run-type-entite`) -- **retrait des 5 entrées individuelles du panneau acté et effectué le 26 juillet 2026** (27→26→21 entrées au total avec `complete_geographie_coverage`). Traçabilité au §6 (tableau legacy), scripts restés utilisables en CLI directe.

#### Audit du panneau sidebar, suite (26 juillet 2026)
Demande de David après le retrait des 5 diagnostics : revérifier l'absence de doublons sur les 21 entrées restantes, et voir si la logique de pairing corrigée sur `scan_geographie_complet` (§ ci-dessus, "niveau 2") s'appliquait ailleurs.
- **Aucun nouveau doublon trouvé.** Vérifié en lisant les docstrings/en-têtes de tous les scripts, en particulier les paires a priori suspectes `build_geographie_monde.py`/`enrich_geographie_recursive.py` (étapes 1/2 séquentielles d'un même pipeline, pas un doublon) et `requeue_needs_review.py`/`review_localisation.py` (files d'attente distinctes -- `queue.yaml` du pipeline entités vs champ `localisation` des fiches). Les deux paires déjà tranchées le 25 juillet (`zoning_topdown_test`/Carte, `reparenter_sous_zones_orphelines`/`generer_zones_topdown --apply-topdown`) restées valides.
- **La logique "correction implique diagnostic" (depends_on) ne s'applique nulle part ailleurs** : c'est une forme propre aux orchestrateurs multi-étapes avec correction par étape. `generer_zones_topdown.py` a une paire `--review-topdown`/`--apply-topdown` qui *ressemble* au même schéma mais est en réalité deux alternatives mutuellement exclusives (pas "corriger implique diagnostiquer" -- déjà couvert par `mutually_exclusive_with` + `required_one_of`, aucun changement nécessaire).
- **En creusant, découverte d'une autre forme du même bug de fond** que celui du 26 juillet sur `scan_geographie_complet` (rien ne bloquait le GUI avant un plantage argparse), invisible au premier grep (`mutually_exclusive_with`) car ces cas n'utilisaient pas ce mécanisme :
  - `zoning_topdown_test` (`zoning_topdown.py`) : `--pays`/`--zone-suspecte` est un vrai groupe requis (`add_mutually_exclusive_group(required=True)`) jamais déclaré côté GUI. `--scenario` requis (`required=True`) mais jamais marqué. `--raison-suspicion` requis seulement si `--zone-suspecte` est rempli (`ap.error()` sinon) -- nouveau cas de figure, ni groupe ni simple requis.
  - `reparenter_sous_zones_orphelines.py` : `--scenario` et `--zone-cible` tous deux `required=True`, aucun des deux marqué côté GUI.
  - `undo_custom.py` : `--type` requis seulement si `--slug` est rempli (`sys.exit()` sinon) -- même cas de figure que `--raison-suspicion`.
  - Au passage, découverte que le champ `required: true` existant dans `scripts_config.json` (déjà posé sur `build_geographie --scenario`) était **purement cosmétique** : ajoutait juste un `*` au label dans `renderOption()`, jamais vérifié avant le clic Lancer.
  - Corrigé : `required_one_of` ajouté sur `zoning_topdown_test` ; `required: true` ajouté et **rendu réellement bloquant** (nouvelle fonction `validateRequiredFields()`, appelée au clic Lancer aux côtés de `validateRequiredGroups()`) sur les 3 champs `--scenario`/`--zone-cible` manquants ; nouveau champ `required_if` (flag déclencheur) pour les 2 cas conditionnels (`--raison-suspicion`, `--type`).
- **Identification des scripts "one-shot" parmi les 21 entrées** (demande de David) : passage en revue des docstrings de chaque script, cherchant les cas auto-décrits comme ponctuels/mécaniques plutôt que comme faisant partie du flux normal.
  - `fix_alliance_suffixes.py` : même famille que `fix_impact_scale.py`/`fix_lieux_residuels.py` déjà en legacy (correction mécanique d'un bug de suffixe précis). Vérifié en conditions réelles par David (`--dry-run --verbose` : 0 fiche modifiée, 0 correction) -- **confirmé résolu partout, retiré du sidebar le 26 juillet 2026** (21→20 entrées), traçabilité au §6.
  - `build_geographie_monde.py` : se décrit lui-même comme *"one-shot par scénario, ré-exécutable"*. David confirme les 6 scénarios définitifs (pas de 7e prévu). Reclassé 🔁→🪦, puis **règle actée dans la foulée : 🪦 et sidebar sont désormais mutuellement exclusifs, retiré du panneau le 26 juillet 2026** (20→19 entrées) malgré l'usage `--force` ponctuel encore légitime -- reste utilisable en CLI directe. Cf. légende §0, section "Règle actée le 26 juillet 2026".
  - `extract_phantom_slugs.py` identifié comme cas intermédiaire (déclenché par un rapport en amont, ni one-shot ni vraiment routine) -- laissé tel quel, pas de décision demandée.

#### Bugs GUI corrigés le 25 juillet 2026
- **Sélecteur `--all`/`--scenario` bloqué** : cocher "Tous les scénarios" désactivait le `<select>` "Scénario", mais rien ne le réactivait jamais en décochant ensuite (`renderOption()`, logique `mutually_exclusive_with`). Corrigé dans les deux sens (checkbox → select ET select → checkbox).
- **Valeur périmée dans un `<select>` désactivé** : même zone de code — désactiver le `<select>` ne vidait pas sa valeur ; si un scénario était déjà choisi avant de cocher "Tous les scénarios", `collectArgs()` (qui ne regarde jamais `.disabled`, seulement `.value`) envoyait `--scenario` ET `--all` ensemble, rejeté par le groupe mutuellement exclusif argparse (`scan_geographie_complet.py: error: argument --scenario: not allowed with argument --all`). Corrigé en vidant `other.value` en plus de `other.disabled = true`.

#### Bugs GUI corrigés le 26 juillet 2026
- **Aucun blocage avant un plantage argparse "au moins un requis"** : signalé par David sur `scan_geographie_complet.py` (`error: one of the arguments --scenario --all is required`), généralisé après audit à 9 autres scripts. Nouveau champ `required_one_of` (liste de groupes de flags) + fonction `validateRequiredGroups()`, appelée au clic Lancer, message d'erreur direct dans le panneau de log plutôt qu'un code retour 2 après coup.
- **Champ `required` cosmétique uniquement** et **champ requis conditionnel jamais couvert** : trouvés lors de l'audit "suite" ci-dessus. Nouvelle fonction `validateRequiredFields()` (champ `required`, désormais réellement bloquant, + nouveau champ `required_if`).
- **Validation de champs requis absente sur le formulaire "Ajouter à la queue"** (`_appendYamlQueue()`, découvert en testant `inject_signals` en conditions réelles) : une variable `required` était calculée mais jamais vérifiée avant l'envoi, et le sélecteur qu'elle utilisait ne pouvait de toute façon rien filtrer (`data-optional` jamais posé sur les champs par `_buildFormField()`). Cas réel : une entrée avec la description vide est passée sans encombre, aurait fait planter `inject_custom_signals.py` sur `idea["description"]` (KeyError) au premier traitement. Corrigé : `_markOptional()` pose désormais l'attribut, et la validation bloque réellement l'envoi avec un message listant les champs manquants. Généralisé aux 3 scripts à file d'attente (`create_entities`, `inject_events`, `inject_signals`) en revérifiant dans le code de chacun quels champs sont réellement optionnels (plusieurs étaient marqués requis à tort — voir leurs sections respectives).
- **Mode "Édition brute" affichait un instantané périmé** du fichier (capturé une seule fois à l'ouverture du panneau, jamais rafraîchi) — basculer vers ce mode après un ajout réussi via le formulaire guidé affichait l'ancien contenu, et sauvegarder depuis là écrasait l'ajout récent. Cas réel vécu pendant la session : une entrée bien ajoutée s'est fait écraser de cette façon. Corrigé : rechargement depuis le disque à chaque bascule vers "Édition brute".

#### Nouveaux mécanismes génériques (26 juillet 2026, suite)
En plus de `mode_only`/`depends_on`/`required_one_of`/`required_if` déjà documentés ci-dessus, deux mécanismes ajoutés pour le nouveau type `signal` d'`undo_custom.py` — réutilisables pour un futur script avec le même besoin :
- **`slug_type_field` / `slug_type_map`** (sur une option `slug_select`) : fait dépendre la source des slugs affichés d'un autre champ du formulaire. Exemple (`undo_custom`, champ `--slug`) : `"slug_type_field": "--type", "slug_type_map": {"signal": "signals", "*": "entities"}` — la liste bascule sur les signaux si `--type` vaut "signal", sur les entités sinon (`"*"` = valeur de repli). Câblé par un écouteur `change` global (`app.js`), symétrique à celui déjà existant pour le rechargement par scénario.
- **`hide_when`** (sur n'importe quelle option) : masque tout l'`option-group` selon la valeur courante d'un autre champ. Exemple : `"hide_when": {"field": "--type", "values": ["signal"]}` sur `--generalisation` d'`undo_custom` — n'a pas de sens pour un signal (pas d'archétype séparé), donc disparaît du formulaire plutôt que d'afficher une note "sans effet". Nouvelle fonction `updateHideWhenVisibility()`, même schéma d'appel (rendu initial + à chaque `change` dans le formulaire) que `updateModeOnlyVisibility()`/`syncDependsOnParents()`.
- ⚠️ **Aucun des deux mécanismes n'a été confirmé dans un vrai navigateur** — seule la syntaxe JS a été validée (`node --check`) et la logique relue. À tester en priorité à la prochaine session : sélectionner "signal" dans le menu Type d'`undo_custom` et vérifier que "Fiche cible" bascule bien sur les signaux et qu'"Étendue de l'annulation" disparaît.
- **Confirmé en conditions réelles le 31 juillet 2026** — David a testé ce point en tout début de session de revue systématique du panneau, ça fonctionne comme prévu.
- Le fichier `scripts_config.json` comptait **6 mécanismes de comportement conditionnel distincts** avant cette session (`mode_only`, `depends_on`, `required_one_of`, `required_if`, `slug_type_field`/`slug_type_map`, `hide_when`) — voir le 7e ci-dessous.

#### Nouveaux mécanismes génériques (31 juillet 2026)

- **`"advanced": true`** (sur n'importe quelle option) — 7e mécanisme conditionnel, ajouté après vérification qu'aucun des 6 existants ne couvrait ce besoin précis : regrouper une option à cas d'usage marginal (ex. `--report` sur `extract_phantom_slugs`, un chemin de fichier alternatif que 95% des usages ignorent) sous un bloc `<details>`/`<summary>` "Options avancées", replié par défaut, en bas du formulaire — sans la retirer complètement du panneau. Contrairement à `hide_when` (masque selon la *valeur* d'un autre champ), c'est une préférence d'affichage fixe et non conditionnelle. Implémenté dans `renderFormBody()` (`app.js`) : sépare `script.options` en deux listes (normales / `advanced`), rendu identique via `renderOption()` pour les deux, seule la destination DOM change. CSS minimal ajouté dans `index.html`.
- **Sauvegarde automatique avant "Lancer"** (`saveOpenConfigForms()`, `app.js`) — cas réel vécu par David : un panneau `config_fields` (ex. `generate.py`) rempli à l'écran puis lancé directement sans passer par le bouton "Sauvegarder" séparé faisait tourner le script sur l'ancien `config.yaml` resté sur disque, sans aucun avertissement. Corrigé en sauvegardant automatiquement tout panneau `.yaml-form-panel` ouvert dans `#form-body` juste avant l'exécution, en réutilisant les mêmes fonctions que les boutons manuels (`_saveYamlForm()` pour le formulaire guidé, `/api/yaml` direct pour le mode "Édition brute"). Bloque le lancement avec un message clair si la sauvegarde échoue plutôt que de lancer sur une config non écrite. Portée limitée au script actif (`#form-body` reconstruit à chaque changement de script).
- **Deux nouveaux `slug_type` "scan-then-filter"** — pattern générique introduit deux fois ce jour-là pour éviter de proposer une liste brute (toutes les zones N1, toutes les instances) là où seule une poignée d'éléments sont réellement pertinents : `zones_a_reparenter` (`reparenter_sous_zones_orphelines`, voir §4) et `fiches_a_localiser` (`extract_localisation`, voir §4). Les deux suivent le même schéma : nouveau mode `--scan-*` côté script Python (lecture seule, aucun appel LLM) → nouvelle fonction `_scan_*_candidats()` côté `gui/app.py` (sous-processus + JSON, échec silencieux tolérant) → nouveau cas dans `/api/slugs`. Aucune modification d'`app.js` nécessaire pour ces deux ajouts (`loadSlugsForSelect()` déjà générique sur la valeur de `slug_type`).
- **`yaml_files` erroné corrigé** sur `extract_phantom_slugs` — pointait vers `instances_custom/needs_review_enrich.yaml` (copié par erreur depuis la config d'`enrich_minimal`, où il est légitime), un fichier que ce script ne lit ni n'écrit jamais. Corrigé vers `entites_custom/queue.yaml`, le vrai fichier qu'il écrit, et rendu modifiable (le script recommande lui-même d'aller y supprimer les entrées non pertinentes avant de lancer `create_entities`).
- **Bouton Carte legacy retiré** — `/api/carte/appliquer_zone_topdown_suspecte` (signalé dans un handoff précédent comme jamais migré vers `chantiers.py`) a été rendu inaccessible depuis l'UI : bouton d'entrée "🧭 réviser (patron spatial)" retiré de l'arbre de zones (`app.js`), CSS mort retiré (`index.html`), 3 fonctions du circuit devenues mortes retirées. La route côté serveur (`app.py`) n'a pas été touchée (dormante, pas supprimée) — le flux de génération de proposition top-down reste accessible via l'onglet Chantiers.

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
| `/api/chantiers` | GET | Liste des chantiers géographie, filtrable (voir "Onglet Chantiers" plus bas) |
| `/api/chantiers/generer` | POST | Génère une proposition IA pour un chantier précis |
| `/api/chantiers/approuver` | POST | Approuve/rejette une proposition déjà générée |
| `/api/chantiers/statut` | POST | Change le statut d'un chantier (ignore/traite/a_traiter) |
| `/api/chantiers/appliquer` | POST | Applique en lot les chantiers approuvés d'un scénario (ou tous), ou un seul chantier précis via `id` (ajouté le 1er août 2026) |
| `/api/slugs` | GET | Autocomplétion de slugs (pour `slug_select` dans les formulaires) — types : `instances`, `entities`, `zones`/`zones_all`/`zones_hier`, `signals` (nouveau le 26 juillet, liste `signaux_custom/*.md`) |
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

### Onglet Chantiers — workflow détaillé (point 4.5, livré le 26 juillet 2026)

**À quoi ça sert** : cycle complet de traitement des chantiers géographie (`chantiers_geographie.yaml`, voir §4bis) sans éditer le YAML à la main — lister, générer une proposition IA pour un chantier précis, approuver/rejeter, appliquer, ignorer ou marquer traité manuellement.

**5 nouvelles routes Flask** (`app.py`), toutes lisent/écrivent `chantiers_geographie.yaml` directement (pas d'import de `generator/chantiers.py` — même convention de séparation de codebase que le reste du fichier, voir point de vigilance existant) :
| Route | Méthode | Rôle |
|---|---|---|
| `/api/chantiers` | GET | Liste filtrable (`?scenario=&type=&statut=`, tous optionnels) |
| `/api/chantiers/generer` | POST | Génère une proposition IA pour **un seul** chantier (`{id}`) — sous-processus `zoning_topdown.py --json`, même contrat que `/api/carte/generer_zone_topdown` mais avec la granularité par chantier que `--review-topdown` n'offre pas (lui traite toujours tous les chantiers éligibles d'un coup) |
| `/api/chantiers/approuver` | POST | `{id, approuve: bool}` — bascule `proposition_approuvee`, ne touche jamais au statut |
| `/api/chantiers/statut` | POST | `{id, statut}` — ignore / marque traité manuellement / rouvre |
| `/api/chantiers/appliquer` | POST | `{scenario}` ou `{all: true}` ou `{id}` (granularité fine, ajoutée le 1er août 2026) — délègue à `generer_zones_topdown.py --apply-topdown` en sous-processus (synchrone, pas de LLM ici). Avec `id` : résout `scenario`/`cible` depuis `chantiers_geographie.yaml`, ajoute `--cible` à la commande |

**Granularité "un seul chantier" — ajoutée le 1er août 2026** : `chantiers.chantiers_prets_a_appliquer()` accepte désormais un filtre `cible` optionnel, propagé via le nouveau flag `--cible` de `generer_zones_topdown.py --apply-topdown --scenario` (incompatible avec `--all`/`--review-topdown`, validé en CLI). Côté GUI, `/api/chantiers/appliquer` accepte `{id: "<scenario>__<cible>"}` en plus des deux formats existants. Bouton "✓ Appliquer ce chantier" ajouté par ligne dans `app.js` (visible uniquement si la proposition est approuvée — même condition que `chantiers_prets_a_appliquer()`), avec confirmation avant écriture comme le bouton "Appliquer" global. Testé en conditions réelles le 1er août : chantier ciblé correctement passé à `traite` sans toucher aux autres chantiers approuvés du même scénario.

**Frontend** (`index.html` + `app.js`) : liste groupée par scénario, badges type/statut/approbation, aperçu compact de la proposition générée (nom/slug/type/description, pas le YAML brut complet), boutons d'action contextuels par ligne (Générer/Régénérer, Approuver/Retirer l'approbation, **Appliquer ce chantier** si approuvé, Ignorer, Marquer traité, Rouvrir), bouton "Appliquer" en haut dont le libellé s'adapte au filtre scénario en cours.

**Testé en conditions réelles par David** : cycle complet sur `policy_reform/bloc_souverainiste_non_signataire` (généré, approuvé, appliqué) — succès confirmé, statut repassé à "Traité" après application.

**Trouvaille en creusant, résolue le 31 juillet 2026** : `/api/carte/appliquer_zone_topdown_suspecte` (route Carte existante, cas `zone_suspecte`) écrit encore dans l'ancien `patron_spatial_suspectes.yaml` — jamais migrée vers `chantiers.py` lors de la fusion du 25 juillet. Décision actée le 31 juillet : plutôt que de migrer la route (jugé hors scope), son seul point d'entrée UI a été retiré (bouton "🧭 réviser (patron spatial)" + les 3 fonctions du circuit associé, voir §7 "Nouveaux mécanismes génériques (31 juillet 2026)"). La route elle-même reste sur le serveur, dormante, jamais supprimée par précaution — le flux de génération de proposition top-down reste accessible via l'onglet Chantiers.

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

### Choix du modèle LLM (carte + `generer_zones_topdown.py`)
Le sélecteur de modèle du GUI ne définit un modèle **réellement utilisé** que si le toggle "Forcer ce modèle" est coché (voir plus haut) — sinon la carte et `generer_zones_topdown.py` (remplace `complete_geographie_coverage.py`, retiré du sidebar le 25 juillet 2026, voir §4/§6) suivent leur tier normal (`structured_strict`, `mistral-large-latest` par défaut).

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

# Traiter un scénario avec generer_zones_topdown.py (remplace complete_geographie_coverage.py, retiré du sidebar le 25 juillet 2026)
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/generator"
python3 generer_zones_topdown.py --review-topdown --scenario NOM
# → valider les propositions dans chantiers_geographie.yaml
python3 generer_zones_topdown.py --apply-topdown --scenario NOM

# Vérifier la cohérence
python3 check_zones_coherence.py --all

# Forcer un modèle précis pour un test ponctuel (CLI direct, hors GUI)
LLM_PROVIDER=claude LLM_MODEL=claude-sonnet-5 python3 generate.py
```

### Bug récurrent connu
Confusion `pipeline_dir` (= `generator/`) vs `vault_root` (racine du vault) dans `app.py` — `geographie/` vit à `vault_root`, pas dans `pipeline_dir`. Vérifier ce point en priorité en cas de nouveau bug carte/coverage. Même famille de confusion trouvée le 4 juillet dans `check_session.sh` (bug #11 du handoff) — toujours vérifier `$GUI_DIR` vs `$VAULT_DIR`/`generator` en cas de chemin suspect.
