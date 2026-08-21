# Manuel utilisateur complet — Pipeline Ourrassol 2098
*Consolidé le 15 juillet 2026, mis à jour le 3 août 2026, 9 août 2026, 10 août 2026, 11 août 2026 (deux fois : clarté des descriptifs le matin, bugs réels + clôture du test navigateur GUI le soir), 12 août 2026, et 13 août 2026 (chantier dimension temporelle codé, chantier cohérence événements custom confirmé en injection réelle, bug `evenement_cle` corrigé) — couvre `generator/` (39+ scripts Python) et `gui/` (Flask)*

Ce manuel classe chaque script par rôle : **modules internes** (jamais lancés seuls), **orchestrateurs**, **pipeline entités/événements**, **pipeline géographie**, **validation**, **scripts one-shot/legacy**, et **GUI Flask**. Pour chaque script exécutable : ce qu'il fait, quand l'utiliser, options CLI, statut (répétable / one-shot / legacy), et intégration GUI ou non.

---

## 0. Vue d'ensemble de l'architecture

```
Ourrassol2098/                          ← racine du vault Obsidian
├── generator/                          ← pipeline Python (35+ scripts)
│   ├── config.yaml, config_series.yaml, journaux.yaml
│   ├── state/ (instance_usage.json, trajectory_usage.json, event_relevance_usage.json, manual_progress.json, last_validated.json)
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
| `prompt_builder.py` | Assemble le prompt complet (system + user) envoyé au LLM pour générer un article, à partir du snapshot, de la thématique et de `config.yaml`. Contient les 12 profils de journaux (2/scénario). Priorité de `zone_slug` inversée le 11 juillet : `config.get('zone_slug') or snapshot.get('zone_slug')`. **Mis à jour le 3 août 2026** — voir §2 (`generate.py`) pour le détail des 2 bugs de zone/badge forcés corrigés, et §2bis ci-dessous pour les 4 ajouts de contenu issus de l'audit de complétude snapshot/variables. **Mis à jour le 10 août 2026** — voir §2ter pour le détail complet : renforcement de la consigne de longueur, transmission de la date fictive au LLM, signature toujours instruite (position + unicité). |
| `api.py` | Envoie le prompt au LLM configuré (tier `strict`, via `llm_client.py`) et sauvegarde l'article généré en `.md` dans `articles/{scenario}/` (ou `articles/` si aucun sous-dossier n'est configuré). Le champ `model:` du frontmatter reflète désormais le tier réellement résolu (`resolve_for_tier()`), pas une variable statique. **Mis à jour le 10 août 2026** — voir §2ter pour le détail complet : retry automatique si la longueur générée dévie de plus de 40% de la plage demandée (nouveaux champs frontmatter `mots_reels`/`retry_longueur`), dossier de sortie enfin respecté (`config["output"]["dossier"]`), translittération correcte des accents dans le nom de fichier. |
| `llm_client.py` | Abstraction unifiée Mistral/Claude/OpenAI. `LLM_PROVIDER`/`LLM_MODEL` (env, override manuel prioritaire). `TASK_TIER_DEFAULTS` + `resolve_for_tier(task_tier)` pour le routing par défaut. Exporte `call_llm(..., task_tier=...)`. |
| `extract_state_logic.py` *(14 juillet)* | Parseur générique `variables/{variable}.md → states.{scenario}.state_logic`. Sanitise les clés wikilink Obsidian (`[[xxx]]`) des blocs `coupling_intensity` avant `yaml.safe_load` (sinon `unhashable key`). Utilisable en CLI (`--json`, `--scenario`) ou en import (`extract_state_logic(path)`). |
| `patrons_spatiaux.py` *(14 juillet)* | Source de vérité du patron spatial par scénario, pour P24 (générateur top-down) et P22 signal 2 (garde-fou étendu). `state_logic`/`state_logic_complementaire` chargés dynamiquement depuis le vault à chaque import via `extract_state_logic.py` (jamais figés en dur) ; `patron_a_respecter`/`a_eviter` écrits à la main dans `_ANALYSE`, à revalider si un scénario change en profondeur. Config : `OURRASSOL_VAULT_ROOT` (env), sinon déduit de l'emplacement du fichier. **Consommé depuis le 15 juillet par `complete_geographie_coverage.py`** (P24 étape B, voir §4) via `patron_spatial_prompt_block()`. |
| `instance_generation_common.py` *(nouveau, 9 août 2026 ; enrichi le 13 août 2026)* | Module partagé factorisant la logique de génération d'UNE instance (construction du prompt, appel LLM, validation, écriture fichier), jusqu'ici dupliquée entre `generate_instances.py` et `create_entities_and_instances.py` — **~20 fonctions dupliquées, dont plusieurs avaient déjà divergé silencieusement** avant la factorisation : `call_claude_json()` (le correctif du 11 juillet sur le NameError `resp` n'existait que dans `create_entities_and_instances.py`), `validate_instance()` (contrôle de plage [0-5] sur les scores d'impact absent côté `generate_instances.py`), `MAX_TOKENS` (`generate_instances.py` resté à 2000, jugé insuffisant, `create_entities_and_instances.py` déjà relevé à 4000 — unifié à 4000). Contient aussi toute la logique du chantier `trajectoire` (voir §3bis) : `VALID_TRAJECTOIRE`, `TRAJECTOIRE_INACTIVES`, construction du prompt avec consigne dédiée à l'axe narratif unique. `process_entity_scenario()` gère le `hard_constraint` (rôle + trajectoire + `est_clandestin` optionnel) pour le mode custom. Les deux scripts appelants gardent leur logique propre (argparse, boucle principale, mode interactif de création côté `create_entities_and_instances.py`) — seule la mécanique partagée vit ici. Trois erreurs de transcription trouvées et corrigées en session lors de la construction de ce module (parsing de wikilinks dans `parse_md()`, algorithme de `_est_ligne_separateur()`/`_parse_registre_table()`, champ lu par `load_variables_states()`) — toutes détectées par diff systématique contre le code source réel avant livraison, aucune n'a atteint le vault. **Ajout du 13 août 2026 (chantier "dimension temporelle", voir §2)** : `TEMPORAL_BANDS` (3 bandes larges — proche 2026-2035, moyen 2036-2060, lointain 2061-2098), `compute_temporal_distribution(year_counts)` (regroupe par bande + détecte les concentrations par année exacte, seuil 12% du total si l'échantillon atteint 15), `format_temporal_summary()`/`format_concentration_warnings()` (lignes de résumé prêtes à insérer dans un prompt LLM). Utilisées symétriquement par `create_entities_and_instances.py` (`annee_debut`) et `inject_custom_events.py` (`date`). Aussi ajouté : `load_registre_text()`, alias public de `_read_registre_text()` pour un accès externe au texte brut du registre. |

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
les jalons historiques (`state/trajectory_usage.json`) **et pour les
événements custom** (`select_relevant_events()`, `state/event_relevance_
usage.json` — même mécanisme du 2 août 2026, jusqu'ici absent de ce
manuel : gap identifié le 10 août 2026 en documentant le nettoyage d'un
test de génération réelle, voir §2ter). **Ces trois fichiers d'état sont
donc TOUJOURS modifiés par une génération réelle** (`dry_run=False`),
quel que soit le script d'entrée (`generate.py`, `generate_series.py`,
GUI) — à restaurer après tout test qui ne doit pas laisser de trace
(`git checkout -- state/instance_usage.json state/trajectory_usage.json
state/event_relevance_usage.json`, ou `git status state/` pour repérer
tout fichier supplémentaire non suivi avant de le supprimer à la main).

**Mode Semi-guidé — revalidé en conditions réelles le 3 août 2026**
(les 7 champs CLI du bug #34/§3.7 du 2 août, y compris `--zone-slug`,
tous confirmés appliqués correctement dans le contenu réel du prompt,
pas seulement l'en-tête `print_header()`). **1 bug annexe trouvé et
corrigé au passage** : le champ `metadata["longueur"]` retourné par
`build_prompt()` (visible en fin de `--dry-run`, section MÉTADONNÉES)
ignorait l'override `config["article"]["longueur"]` et le recalculait
uniquement depuis le `format_dominant` de la thématique — divergence
avec la vraie consigne envoyée au LLM (toujours correcte, elle, via
`build_journalistic_brief()`). Corrigé en dupliquant la même logique de
priorité dans `build_prompt()`. **À vérifier par David** : si ce champ
est réutilisé en aval (frontmatter d'articles sauvegardés, stats), des
fiches publiées avant ce correctif pourraient porter une longueur
affichée incohérente avec leur contenu réel.

## 2bis. Audit de complétude snapshot/variables (3 août 2026)

Demande de David : vérifier que toutes les données calculées par
`snapshot.py`/`loader.py` sont bien utilisées par `prompt_builder.py`,
sans perte de contenu narratif intéressant. Méthode : comparaison champ
par champ (grep systématique de tous les accès `snapshot.get(...)`,
`inst.get(...)`, `ev.get(...)`, `zone.get(...)` dans `prompt_builder.py`)
contre ce que `loader.py`/`snapshot.py` extraient/calculent réellement.

**4 pertes significatives trouvées et corrigées** (`prompt_builder.py`) :
1. **`responsabilites`** (instances) — ajouté dans `build_entities_
   context()`, affiché en entier. Distinct de `description_
   journalistique` (récit d'origine, écrit "de l'extérieur") : décrit ce
   que l'entité FAIT concrètement (actions, leviers, méthodes).
2. **`signes_distinctifs`** (instances) — ajouté au même endroit,
   affiché en entier. Détails concrets/visuels/symboliques qui rendent
   l'entité reconnaissable et citable (slogans, symboles, pratiques).
3. **`realisation`** (événements custom) — ajouté dans
   `build_trajectory_context()`, section "Événements injectés", tronqué
   à 80 caractères comme `consequences`. Décrit comment l'événement
   s'est concrètement déroulé.
4. **Jalons génériques de portée "majeur"** — nouvelle sous-section
   `**Ruptures majeures**` dans `build_trajectory_context()`, affichée
   avant `**Ruptures structurantes**`, plafonnée à 3
   (`MAX_JALONS_RUPTURES_MAJEURES`). Réutilise `snapshot["trajectory_
   majors"]`, calculé par `snapshot.py` mais jamais lu jusque-là — seuls
   les jalons "structurant" étaient affichés, alors que "majeur" est la
   portée la plus significative du classement (3+ variables touchées,
   ou variable pilote + rupture "core").

**Vérifié en conditions réelles** (mode Forcer-instance) : les 4 ajouts
apparaissent correctement, 41 361 caractères de prompt sur ce test (pas
d'explosion notable). **⚠️ Non testé : impact taille en mode Semi-guidé
à 6 entités simultanées** (jusqu'à 6× `responsabilites` + 6× `signes_
distinctifs` en même temps — le vrai cas de charge maximale, jamais
mesuré). Priorité de la prochaine session.

**Trouvailles non traitées, laissées de côté sur décision de David** :
`impact_local`, `zone_geographique` (tags d'échelle), `type_relation_
dominante`, `annee_debut`/`annee_fin`, `age_historique`, `generation`
(instances, jamais utilisés — `type_relation_dominante` jugé le plus
intéressant, compense les listes `alliances`/`oppositions` souvent
vides) ; `constrained_variables` (snapshot, calculé, jamais affiché) ;
champ `type` des zones géographiques (`zone_sinistree` etc., distinct
de `statut`) ; bloc `simulation` sur les fiches variables (probablement
pensé pour du monitoring interne, pas la narration). **`forces_
attractives`/`forces_repulsives` escaladé en chantier à part le 14 août
2026** — ce n'est pas qu'une promesse de docstring jamais tenue :
vérifié sur le vault réel, le contenu existe bel et bien sur les 12
fiches `variables/*.md`, mais en prose Markdown dans le corps de la
fiche (deux sections différentes et non identiques, `## 3. Dynamique
interne` et `## 4. Structure causale`), pas en frontmatter YAML — d'où
l'absence totale d'extraction par `loader.py`. Voir
`BACKLOG_MASTER_9_AOUT.md` Partie 1 point 2 et `HANDOFF_14_AOUT.md` §10
pour le détail complet et la décision de conception à trancher avant
de coder. Détail complet en
§4 de `HANDOFF_3_AOUT.md`.

**Risque structurel identifié, pas un bug actif** : une instance avec
`injection.type == "custom"` non sélectionnée parmi les `filtered_
instances` reste invisible narrativement (seul un nom tronqué apparaît
dans une ligne de delta de "Perturbations custom actives") — aucun
exemple réel rencontré à ce jour (le vault ne semble contenir que des
événements custom), mais le trou de code existe pour le jour où ça
arrive.

**Plafonnement des événements custom et de la géographie** (2 août
2026, passage à l'échelle du vault ; **testé en conditions réelles et 2
bugs annexes corrigés le 3 août 2026**) : les événements custom et la
liste des zones géographiques n'étaient soumis à aucune limite
(contrairement aux instances/signaux) — risque de croissance non
maîtrisée du prompt. Corrigé avec le même principe pour les deux : une
couche large et peu coûteuse qui préserve la vision globale du monde
(résumé une ligne, noms seuls au-delà d'un plafond haut — 25 événements
/ 20 zones), et une couche détaillée filtrée par pertinence + rotation
à mémoire (plafond bas — 8 événements en détail complet, zones
pertinentes toujours en détail sans plafond). Score de pertinence des
événements réutilise le matériau déjà standardisé sur les fiches
(`portee`, amplitude des `impact_sur_variables`) plutôt qu'une nouvelle
heuristique. L'élément forcé (mode Forcer) est toujours garanti présent
dans la couche détaillée, jamais soumis au tri ni à la rotation.

**Test réel du 3 août** (`--dry-run --mode forcer --forcer-type
evenement`, scénario le plus chargé) : les plafonds numériques
eux-mêmes sont corrects du premier coup (comptages exacts vérifiés). Le
test a en revanche débusqué deux résidus du bug #26/§3.8 (zone
d'ancrage) non couverts par la correction du 2 août, tous deux corrigés :
1. **Badge `[FORCÉ]`** jamais affiché sur l'événement forcé dans la
   liste détaillée — `select_relevant_events()` (`loader.py`) plaçait
   bien l'élément forcé en tête mais ne posait jamais la clé
   `"forced": True` que `prompt_builder.py` lit pour le badge. Corrigé.
2. **Zone de l'élément forcé absente de la section géographie
   détaillée** pour un événement/signal forcé (fonctionnait par
   coïncidence pour une instance forcée, qui devient l'unique
   `filtered_instance`) — `build_geographie_context()` calculait
   `zones_pertinentes` uniquement depuis les instances génériques
   auto-sélectionnées, sans connaître la vraie zone forcée. La fonction
   reçoit désormais `config` en paramètre (comme `build_system_prompt()`
   le fait déjà) et ajoute explicitement `config["zone_slug"]` à
   `zones_pertinentes`. Corrigé.

**Plafonds jamais discutés en détail avec David au 3 août** — vault
jugé encore trop jeune pour ajuster les chiffres (8/25/20) sans
arbitraire ; le design en 3 couches absorbe déjà bien la croissance
attendue (seule la liste compacte grossit avec le vault, à coût quasi
nul). À revisiter avec des données réelles une fois le vault plus gros.

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

**Mis à jour le 10 août 2026** : scan de `articles/` rendu récursif
(`glob("**/*.md")` au lieu de `glob("*.md")`) — sinon les articles
générés en série/manuel dans `articles/{scenario}/` (voir §2ter)
devenaient invisibles à ce diagnostic. Testé en isolation seulement
(logique du scan vérifiée), pas en conditions réelles faute d'entités
disponibles pour un test complet en session.

**Mis à jour le 11 août 2026** — clarté de la sortie corrigée suite à un
retour de David en validant cette entrée dans le navigateur (exemple
réel fourni en session) : titre affichant le type technique brut
(`instance`/`evenement`/`signal`) remplacé par un libellé lisible ;
formulation du statut d'origine simplifiée (fini les noms de fichiers
YAML internes affichés tels quels) ; échelle d'impact rendue explicite
(`5/5` plutôt que deux chiffres bruts juxtaposés `5/3`) ; libellé
`"Enrichie le"` remplacé par `"Détails complétés par l'IA le"` ; listes
d'alliances/oppositions enfin lisibles (`_formater_liste_slugs()` détecte
désormais un suffixe de scénario partagé même sans le recevoir en
paramètre explicite — auparavant seul le cas single-call avec `scenario=`
fourni était nettoyé — et convertit le snake_case en texte normal) ; titre
de la section 4 simplifié (`"Aval —"` retiré, jargon pipeline). Testé
fonctionnellement par reconstruction exacte de l'exemple réel fourni par
David (comparaison ligne à ligne), plus 4 cas de non-régression sur
`_formater_liste_slugs()` — dont le cas le plus risqué (slugs de
plusieurs scénarios différents mélangés), confirmé sans perte
d'information (le suffixe reste affiché quand le retirer créerait une
ambiguïté). **Le descriptif GUI de cette entrée a aussi été reformulé en
langage moins technique** (voir §7, addendum du 11 août). Marqué
`gui_verified: true` par David après ce passage. Pas de nouveau test en
conditions réelles sur le vault depuis ces correctifs (le test s'appuie
sur l'exemple déjà fourni, reconstruit fidèlement, pas sur un nouveau
run réel du script).

### `generate_series.py` 🔁 🧩
Génère une **série d'articles** sur plusieurs thématiques avec cohérence temporelle, pilotée par `config_series.yaml`.
```bash
python3 generate_series.py                    # utilise config_series.yaml
python3 generate_series.py --dry-run          # sans appel API
python3 generate_series.py --scenario breakdown
python3 generate_series.py --validate-first   # valide la base avant de générer
```
Sortie : `articles/{scenario}/` + `articles/{scenario}/_index.md`.

**Bug corrigé le 10 août 2026** — jusque-là, malgré ce chemin de sortie
correctement construit ici, les articles eux-mêmes atterrissaient à la
racine de `articles/` (voir §2ter point 7) : `save_article()` dans
`api.py` ignorait le champ de configuration correspondant. `_index.md`
se retrouvait donc seul dans le sous-dossier, sans les articles qu'il
indexe. Corrigé et vérifié en conditions réelles — le sous-dossier
contient désormais bien les deux.

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

## 2ter. Chantier longueur/qualité des articles générés (10 août 2026)

*Suite directe du point ouvert le 9 août ("Dérive du LLM sur la longueur
réelle des articles", voir `BACKLOG_MASTER_9_AOUT.md` Partie 4 pour
l'historique complet). Session dense : diagnostic, 8 correctifs distincts
(certains en 2 itérations), tests réels sur un vrai batch de génération.
Explications volontairement détaillées et sans jargon — section pensée
pour rester compréhensible même sans avoir suivi la session en direct.*

### Contexte : pourquoi cette section existe

Le 9 août, un audit (`audit_longueur_articles.py`) avait révélé que
**70,4% des articles générés ont une longueur réelle hors de la plage
demandée** à la génération (ex. un article censé faire 600-900 mots qui
en fait 1257, ou un autre censé faire 700-1000 qui n'en fait que 322).
Cette section documente l'investigation complète qui a suivi, et tout ce
qui a été corrigé au passage — car en creusant ce seul sujet, plusieurs
autres bugs indépendants sont apparus (date, signature, dossier de
sortie).

### 1. Diagnostic initial — pourquoi le LLM ne respecte pas la longueur

Lecture du code réel (`prompt_builder.py`, `api.py`) : la consigne de
longueur n'apparaissait qu'**une seule fois**, tôt dans le prompt envoyé
au LLM, au milieu d'une dizaine d'autres lignes de métadonnées (format,
style, niveau émotionnel, échelle...). Le bloc final juste avant
l'écriture de l'article — "Contraintes impératives", la seule liste
explicitement qualifiée de stricte — ne la reprenait jamais. De plus,
**aucune vérification n'existait après la génération** : l'article du
LLM était sauvegardé tel quel, sans compter les mots ni comparer à la
consigne.

### 2. Premier correctif — renforcement du prompt (insuffisant seul)

**Fichier : `prompt_builder.py`, fonction `build_journalistic_brief()`.**
La consigne de longueur est désormais répétée dans le bloc "Contraintes
impératives", avec une formulation dure : *"ne t'arrête pas avant la
borne basse, ne dépasse pas la borne haute — contrainte dure, pas une
indication approximative"*.

**Testé en conditions réelles, résultat négatif** : un batch de test
isolé (18 articles) a donné un taux d'incohérence de **94,4%** — pire
que la référence du 9 août (70,4%), avec un biais net vers le dépassement
(17 articles trop longs sur 17 incohérents, aucun trop court). Conclusion :
le renforcement du prompt seul ne suffit pas — le LLM ne semble pas
"oublier" la consigne, il la traite comme secondaire face à d'autres
pressions du prompt (développer le sujet, couvrir tous les angles
listés...). Le correctif reste en place (il ne fait pas de mal), mais le
vrai correctif est le retry (point 6 ci-dessous).

### 3. Deuxième correctif — la date fictive n'était jamais transmise au LLM

**Symptôme signalé par David** : la date dans le nom de fichier (ex.
`..._22aot2098.md`) ne correspondait jamais à la date réellement écrite
dans l'article, et presque tous les articles convergeaient vers la même
date ("12 octobre 2098").

**Cause réelle** : `generate.py`/`generate_series.py` calculent bien une
date différente par article (pour espacer une série dans le temps), mais
cette date ne servait **qu'à construire le nom du fichier** — jamais
envoyée au LLM, qui recevait seulement l'instruction *"une date crédible
en 2098"*, totalement libre. D'où la convergence : sans aucun repère, le
modèle a tendance à toujours proposer une réponse similaire.

**Fichier : `prompt_builder.py`, fonction `build_journalistic_brief()`.**
La date calculée (`config["article"]["date_fictive"]`) est maintenant
transmise explicitement au LLM, avec instruction de la reprendre telle
quelle — à la fois dans la consigne principale et dans le bloc
"Contraintes impératives".

**Testé en conditions réelles sur 12 articles : 12/12 corrects**, date du
nom de fichier et date dans l'article identiques à chaque fois.

### 4. Troisième correctif — signature manquante ou incohérente (2 itérations)

**Symptôme signalé par David** : certains articles n'avaient aucune
signature en bas, d'autres avaient une signature avec le nom du journal,
d'autres sans.

**Cause réelle (`prompt_builder.py`, fonction `get_journal_profile()`)** :
le profil éditorial d'un article est résolu par 3 chemins possibles
(édition locale d'une zone géographique > réseau global > profil
générique par scénario). Seul le premier chemin fournissait un nom de
journaliste curaté — les deux autres ne le fournissaient jamais, et dans
ce cas, **l'instruction de signer n'était tout simplement pas incluse
dans le prompt**, laissant le LLM libre de signer ou non.

**Itération 1** : une instruction de signature est désormais toujours
donnée, avec un format unifié `"Nom — Journal"` — nom curaté si
disponible, sinon inventé par le LLM lui-même mais au même format.

**Test réel sur ce premier correctif** : 12/12 articles avaient
désormais une signature (contre une présence aléatoire avant). Mais
deux problèmes résiduels sont apparus : la position variait (parfois en
haut sous la date, parfois en bas de l'article), et un article avait la
signature **dupliquée** aux deux endroits, malgré la consigne "une seule
fois".

**Itération 2** (après clarification des usages réels de la presse en
ligne — la signature/byline se met en haut, sous le titre et la date ;
la position "en bas" est plutôt réservée aux tribunes/éditoriaux) : la
position est désormais fixée explicitement en haut, immédiatement sous
la date, et la consigne "une seule fois" reformulée en majuscules avec
interdiction explicite de répétition, reprise à la fois dans les
instructions permanentes (`build_system_prompt()`) et dans le bloc
"Contraintes impératives" (`build_journalistic_brief()`).

**Ce deuxième correctif n'a pas encore été testé en conditions réelles**
— à valider au prochain batch de génération.

### 5. Quatrième correctif — accent supprimé dans le nom de fichier

**Symptôme signalé par David** : des fautes systématiques dans les noms
de fichiers, ex. `fvrier` au lieu de `février`.

**Cause réelle (`api.py`, fonction `build_article_filename()`)** : la
regex qui nettoie la date pour en faire un nom de fichier ne reconnaissait
que les lettres non-accentuées (`a-z0-9`) — tout caractère accentué
(`é`, `û`...) était silencieusement **supprimé** au lieu d'être remplacé
par son équivalent sans accent.

**Correctif** : passage par `unicodedata.normalize()` avant le filtrage,
qui sépare la lettre de base de son accent et ne supprime que
l'accent — `"février"` devient `"fevrier"`, pas `"fvrier"`.

**Testé en conditions réelles sur 12 articles : confirmé corrigé**
(`19fevrier2098`, `5avril2098`, etc.).

### 6. Cinquième correctif — retry automatique si l'article est trop hors plage

**Décision prise avec David** : puisque le renforcement du prompt seul
ne suffit pas (point 2), un mécanisme de re-génération automatique a été
ajouté — mais borné, pour ne pas faire exploser le temps et le coût de
génération.

**Règle retenue** : si l'écart entre la longueur réelle et la plage
demandée dépasse **40%** (par rapport à la borne dépassée, haute ou
basse), l'article est **régénéré une seule fois** — jamais de boucle,
jamais plus d'un essai supplémentaire. En dessous de ce seuil, l'article
est accepté tel quel, même hors plage.

**Comment fonctionne la régénération** : ce n'est **pas** un découpage
mécanique du texte existant. Le premier essai est entièrement jeté, et le
LLM réécrit l'article en entier depuis le titre, avec un message
supplémentaire qui lui indique précisément l'écart mesuré au premier
essai (ex. *"Ta précédente tentative faisait 1300 mots, soit 44% de trop
par rapport à la borne haute (900 mots). Coupe le texte pour rester entre
600 et 900 mots cette fois."*) — un rappel chiffré et concret, plus
efficace qu'une simple répétition de la consigne d'origine.

**Coût** : chaque retry est un deuxième appel LLM complet — double temps
de génération et double coût API pour l'article concerné. C'est
précisément pour limiter cet effet que le seuil est fixé à 40% (pas plus
bas) et le nombre de tentatives à 1 (pas de boucle).

**Fichier : `api.py`.** Nouvelles fonctions : `_parse_longueur_bornes()`
(extrait les bornes numériques depuis le texte "600 à 900 mots"),
`_count_words()`, `_deviation_ratio()` (calcule l'écart), et
`_retry_with_length_feedback()` (construit le message de rappel et relance
l'appel LLM). `generate_article()` orchestre le tout : appel initial,
vérification, retry conditionnel.

**Traçabilité ajoutée** : deux nouveaux champs dans le frontmatter de
chaque article généré —
- `mots_reels` : le nombre de mots effectivement mesuré (après retry
  éventuel).
- `retry_longueur` : `oui`/`non`, indique si un retry a eu lieu pour cet
  article.

Ces deux champs permettent de vérifier directement dans une fiche
d'article si le mécanisme s'est déclenché, sans devoir relancer l'audit
externe.

**Testé en conditions réelles sur 12 articles : le retry s'est déclenché
3 fois** (sur les articles du 3 janvier, du 2 février et du 10 mai
2098 — visible via `retry_longueur: oui` dans leur frontmatter). Dans les
3 cas, le résultat final était soit dans la plage demandée, soit
nettement plus proche qu'un premier essai aurait pu l'être. Sur les 9
articles non retentés, l'écart réel de chacun a été recalculé
manuellement : aucun ne dépassait le seuil de 40% (le plus proche étant à
36,9%) — confirmation que le seuil se déclenche exactement quand prévu,
sans faux négatif observé sur cet échantillon.

**Limite connue de ce test** : échantillon réduit (12 articles, 3
retries) et température de génération élevée (1.0, "créativité
maximale") — un échantillon plus large serait nécessaire pour confirmer
la fiabilité statistique du mécanisme, mais les résultats obtenus jusqu'ici
sont encourageants.

### 7. Sixième correctif — les articles de série n'allaient pas dans leur sous-dossier

**Symptôme signalé par David** : après un lancement de
`generate_series.py`, les articles atterrissaient à la racine de
`articles/`, alors que le script construit un chemin `articles/
{scenario}/` et y écrit son fichier `_index.md`.

**Cause réelle (`api.py`, fonction `save_article()`)** : le dossier de
sortie était figé en dur sur `articles/` (la racine), sans jamais lire le
champ `config["output"]["dossier"]` que `generate_series.py` (et
`generate_manual.py`, qui a le même design) construisait pourtant
correctement. Résultat : l'`_index.md` d'une série se retrouvait seul
dans un sous-dossier, sans les articles qu'il est censé indexer.

**Correctif** : `save_article()` lit désormais ce champ de configuration.
Comportement vérifié sur les 3 cas de figure possibles : génération en
série (sous-dossier respecté), génération à l'unité (racine, comportement
historique inchangé), configuration sans bloc `output` du tout (repli
propre sur la racine).

**Testé en conditions réelles : confirmé** — le batch de 12 articles de
test s'est bien retrouvé dans `articles/policy_reform/`, aux côtés de son
`_index.md`.

### 8. Septième et huitième correctifs — deux outils de lecture rendus aveugles par le correctif précédent

**Piège découvert avant qu'il ne cause un vrai problème** : corriger le
dossier de sortie (point 7) a un effet de bord caché. Deux outils de
lecture seule scannent `articles/` **à plat**, sans jamais descendre
dans les sous-dossiers : `trace_injection.py` (traçabilité d'une
entité/un événement à travers les articles publiés) et
`audit_longueur_articles.py` (l'audit utilisé tout au long de ce
chantier). Tant que le bug du point 7 existait, ce n'était pas un
problème (tous les articles finissaient à la racine, donc toujours
visibles). Une fois corrigé, ces deux outils seraient devenus
**silencieusement aveugles** à tous les articles générés en série ou en
mode manuel — un nouveau bug de traçabilité, pire que l'original.

**Correctifs** :
- `trace_injection.py` : scan rendu récursif (`glob("**/*.md")` au lieu
  de `glob("*.md")`).
- `audit_longueur_articles.py` : scan rendu récursif (`os.walk` au lieu
  de `os.listdir`), affichage par chemin relatif pour distinguer un
  fichier de la racine d'un fichier de sous-dossier, et les fichiers
  `_index.md` (qui ne sont pas des articles) désormais explicitement
  ignorés plutôt que remontés en "non analysable".

**Testé** : `audit_longueur_articles.py` confirmé en conditions réelles
(43 fichiers retrouvés, dont les 12 du sous-dossier `policy_reform/`,
`_index.md` correctement exclu). `trace_injection.py` testé uniquement en
isolation (logique du scan vérifiée), pas en conditions réelles faute
d'entités disponibles pour un test complet en session.

### 9. Nouveau fichier d'état découvert en fin de session

Lors du nettoyage post-test, un troisième fichier d'état non anticipé
est apparu : `state/event_relevance_usage.json` (voir §2 ci-dessus pour
son rôle — rotation à mémoire des événements custom, mécanisme du 2 août
2026, simplement absent de l'inventaire initial de cette session). Ce
n'est pas un nouveau bug, seulement un gap de documentation — corrigé
dans ce manuel (§0, §2).

### Protocole de test pour un futur changement touchant la génération d'articles

À réutiliser tel quel pour tout changement futur sur `prompt_builder.py`/
`api.py`/`generate.py`/`generate_series.py` :

1. **Avant de commencer** : `git status state/` doit afficher "nothing to
   commit" — sinon, les changements en attente seront écrasés par
   l'étape 4.
2. **Dry-run d'abord** : `python3 generate.py --dry-run` sur 1-2
   thématiques, pour vérifier visuellement le prompt assemblé sans
   dépenser le moindre appel API.
3. **Batch réel** : via `generate_series.py` de préférence (plus rapide
   pour obtenir plusieurs échantillons d'un coup) — mettre `longueur:
   auto` dans `config_series.yaml` pour couvrir plusieurs formats en un
   seul run, et augmenter `articles_par_thematique` à 2-3 pour avoir
   assez d'échantillons par catégorie (la génération étant à température
   1.0, un seul échantillon par cas ne suffit pas à distinguer un effet
   réel du bruit statistique).
4. **Nettoyage après test** :
   ```bash
   rm -rf articles/{scenario}/          # ou les fichiers concernés à la racine
   git checkout -- state/instance_usage.json state/trajectory_usage.json \
       state/event_relevance_usage.json
   git status state/                     # doit redevenir "nothing to commit"
   ```
   **Vérifier aussi les fichiers non suivis** (`Untracked files` dans la
   sortie de `git status`) — un nouveau mécanisme de rotation à mémoire
   futur pourrait créer un 4e fichier d'état non anticipé, à supprimer à
   la main puisque `git checkout` ne touche pas les fichiers jamais
   commités.

---

## 3. Pipeline entités & événements custom

### Chantier "dimension temporelle pour la génération automatique" (13 août 2026)
Esquissé le 8 août, portée élargie aux événements le 12 août (voir constat dans la section `inject_custom_events.py` ci-dessous), codé le 13 août. Fonctions partagées ajoutées à `instance_generation_common.py` (voir §1) : `TEMPORAL_BANDS`, `compute_temporal_distribution()`, `format_temporal_summary()`, `format_concentration_warnings()`.

**Granularité à deux niveaux, décision actée avec David** :
- **Bandes larges** (proche 2026-2035 / moyen 2036-2060 / lointain 2061-2098) pour le signal envoyé au LLM à l'étape auto-suggest/auto — actionnable, peu de bruit sur un vault encore modeste en volume.
- **Année exacte** conservée en interne pour la détection de concentration (seuil : une année dépassant 12% du total, seulement si l'échantillon atteint 15 — sous ce seuil jugé trop bruité) — même granularité que celle qui avait révélé la concentration de 22% sur 2041 côté instances avant le correctif `annee_fin` du 8 août.

**Appliqué symétriquement dans les deux pipelines** :
- `create_entities_and_instances.py::analyze_entity_coverage()` — lit désormais `annee_debut` de chaque instance, en plus de la géographie/catégories déjà mesurées.
- `inject_custom_events.py::analyze_vault_coverage()` — lit désormais `date` de chaque event_instance, en plus de la géographie/types/variables déjà mesurés.

Les deux résumés de prompt (`build_entity_analysis_summary()`, `build_auto_analysis_summary()`) affichent désormais une section "Distribution temporelle actuelle" par scénario (bandes larges) suivie, le cas échéant, d'un avertissement de concentration vault-entier (année exacte). Les consignes des deux prompts auto-suggest/auto ont été mises à jour pour : compenser les bandes sous-représentées, éviter de renforcer une année déjà signalée en concentration, et pour toute proposition dans la bande proche (avant 2036) privilégier une idée rattachable à une dynamique réelle documentée plutôt qu'une date arbitraire — l'ancrage précis restant fait à l'étape de développement (déjà en place, voir chantier "cohérence événements custom" ci-dessous côté événements, et le mécanisme `ancrage_reel` du 8 août côté instances).

`inject_custom_signals.py` vérifié : aucun champ `annee_debut`/`date`, non concerné par ce chantier — cohérent avec l'architecture du vault (un signal décrit une évolution par scénario, pas un point temporel unique).

**Testé** : fonctions helper validées unitairement (bandes correctement regroupées, seuil de bruit respecté sur petit échantillon, concentration détectée à 44%/20%/16% sur un cas simulé reproduisant la situation 2041). **Validé par David en dry-run réel** sur le vault le 13 août. Injection réelle non spécifiquement retestée pour ce chantier — le mécanisme ne touche que la sélection/le prompt, pas le chemin d'écriture, risque jugé nul.

---

### `create_entities_and_instances.py` 🔁 🧩 — **script recommandé pour la création d'entité + instances**
Fusion de `create_entity.py` (legacy, archivé) — **PAS** de `generate_instances.py`, qui reste actif et complémentaire (voir §1 et la ligne `generate_instances.py` en §6, corrigée le 9 août 2026 — cette section elle-même contenait la même affirmation erronée jusqu'à cette correction). Crée une entité **et** génère automatiquement ses instances dans le même run. Tier `structured_strict`. Pour backfiller des instances sur une entité **déjà existante** sans en créer une nouvelle, utiliser `generate_instances.py` (entrée GUI "Générer les instances manquantes").

**Trois modes**, sélectionnables sans blocage depuis le GUI depuis le 11 juillet (`--mode`) :

- **custom** — décrit une instance précise dans `entites_custom/queue.yaml` (champs : `nom`, `category`, `role`, `etat`, `scenario_ref`, `scenario_hint`, `zone_hint` — fonctionnel et documenté dans `QUEUE_TEMPLATE`, `source`). **Depuis le 9 août 2026 (chantier `trajectoire`)** : le champ `etat` prend désormais une valeur de l'axe `trajectoire` (11 valeurs : `émergent`/`marginal`/`ascendant`/`dominant`/`mature`/`déclinant`/`résiduel`/`transformé`/`disparu`/`historique`/`mythifié`), plus un champ optionnel `est_clandestin` (`true`/`false`, absent = pas de contrainte) — les deux alimentent le `hard_constraint` de l'instance générée dans le scénario de référence. Nom de champ `etat` conservé tel quel dans l'interface (pas de rupture avec les entrées `queue.yaml` déjà écrites), seule sa liste de valeurs valides a changé. Côté GUI, le menu correspondant (`scripts_config.json`, entrée `create_entities`) a été mis à jour le 9 août pour proposer les 11 valeurs + le nouveau select `est_clandestin`. Le LLM déduit l'archétype, crée l'entité, puis enchaîne la génération des instances (scénario de référence contraint, les autres libres selon `scenario_hint`, ou les 6 par défaut).
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

**Trois correctifs du 11 août 2026 (session soir), trouvés en testant réellement les modes auto-suggest/auto/custom depuis le GUI :**
- **Crash `EOFError` en mode auto-suggest/auto (GUI)** — `run_auto_suggest_mode()` avait 2 `input()` non protégés (nombre d'idées, scénario ciblé), `run_auto_mode()` les 2 mêmes sur ses propres sous-questions (nombre d'entités, catégorie imposée) : seul le choix de `--mode` lui-même avait été protégé le 11 juillet pour ce symptôme, jamais étendu à ces sous-questions. Les 4 `input()` protégés par `sys.stdin.isatty()` — hors terminal interactif (GUI/cron), retombe sur la valeur par défaut déjà prévue dans le code plutôt que de planter (`n` de `run_auto_mode()` fait exception : pas de défaut sensé possible, arrêt propre avec message clair). **Bug de type corrigé au passage** : le repli interactif de `scenario_filter` produisait une chaîne simple, alors que tout le reste du script (`step_auto_suggest_entities`, `args.scenario` en `nargs="+"`) le traite comme une liste — un scénario tapé en CLI pur aurait été itéré caractère par caractère. Corrigé (`scenario_filter = [scenario_raw]`). Testé en conditions réelles : mode auto-suggest relancé après correctif, plus de crash, 5 idées générées avec succès.
- **Silence sur rejet `category`/`scenario_ref` invalide (mode custom)** — `process_custom_idea()` retournait directement sur ces deux rejets précoces sans jamais imprimer, contrairement à tous les autres cas d'échec de la fonction (archétype, instance) qui affichent toujours leur motif. Trouvé sur un cas réel : une entité ("Les Veilleurs des Nappes Phréatiques") disparaissait du log sans aucun message, alors que `needs_review.yaml` contenait bien la raison (`category invalide : 'mouvement'`, hallucination du LLM auto-suggest malgré la contrainte de prompt — le garde-fou lui-même a fonctionné correctement). Corrigé : `print(f"  ✗ Rejetée : {reason}")` ajouté sur les deux cas.

**Chantier "Test navigateur GUI" définitivement clos le 11 août (soir)** : `create_entities` (cycle complet auto-suggest → custom → cycle post-injection), `enrich_minimal` (testé, résultat vide — cohérent avec P8 clos depuis le 27 juin) et `generate_instances` (exercé comme dépendance du cycle post-injection, 21 instances générées) sont désormais les 3 dernières entrées `gui_verified: true` — les 28 entrées du panneau sidebar le sont toutes.

### `inject_custom_events.py` 🔁 🧩
Injecte des événements custom fournis par l'utilisateur dans `evenements_custom/queue.yaml` : crée l'archétype (`evenements/{slug}.md`) + une instance par scénario sélectionné (`event_instances/{slug}_{scenario}.md`). Tier `structured_strict`.

**Deux modes**, sélectionnables sans blocage depuis le GUI (`--mode`) :
- **custom** — traite le contenu actuel de `evenements_custom/queue.yaml` et injecte dans le vault. Champs : `id`, `description`, `portee`, `date_approximative`, `intensite`, `scenarios`, `variables_hint`, `variables_hint_count` (plafond appliqué en filtre dur depuis le 11 juillet, défaut 2), `acteurs_hint`, `acteurs_hint_count` (plafond appliqué en filtre dur depuis le 14 août 2026 — voir `truncate_actors()` plus bas, même principe que `variables_hint_count`), `zone_hint` (fonctionnel et documenté dans `QUEUE_TEMPLATE` depuis le 14 août 2026), `source`.
- **auto** — analyse la couverture du vault, génère N idées, les **ajoute seulement à `queue.yaml`** (équivalent fonctionnel du mode `auto-suggest` des entités — pas d'injection directe). `--scenario` y est une orientation, pas une contrainte dure.

```bash
python3 inject_custom_events.py --mode custom
python3 inject_custom_events.py --mode auto --n 3 --scenario breakdown
python3 inject_custom_events.py --dry-run
```
`main()` écrit séparément dans `processed.yaml` (statut `partial` si succès partiel) et `needs_review.yaml`.

**Chantier cohérence événements custom (12 août 2026)** — diagnostic préalable : contrairement aux instances (`annee_debut`/`annee_fin`), un événement custom n'a qu'un seul champ `date` (année unique) — pas de bande de traçabilité graduée `ancrage_reel` comme sur les instances, et aucun problème de concentration observé sur le vault réel (53 événements, pic max 11% sur une seule année, contre 22% sur 2041 pour les instances avant correctif). Décision : pas besoin de reconstruire pour les événements le mécanisme lourd des instances (bande graduée + anti-recyclage par shingle-matching) — un enrichissement de contexte suffit, cohérent avec la pratique du projet de ne pas construire de garde-fou mécanique pour un problème non observé (voir `--min-shingle` en dur, Partie 2 du backlog).

**Trois changements, tous dans `inject_custom_events.py`, communs aux deux modes** (auto ne fait qu'écrire dans `queue.yaml` — l'injection réelle passe toujours par le mode custom, `process_idea()`, donc un seul point de code à modifier couvre les deux) :
1. **Import de `load_etat_monde_reel()` et `load_scenario_timeline_summary()`** depuis `instance_generation_common.py` (réutilisées telles quelles, aucune duplication — mêmes chemins `REGISTRE_PATH`/`ETAT_MONDE_PATH`, même liste `SCENARIOS`). Avant ce correctif, `inject_custom_events.py` ne chargeait jamais `etat_du_monde_reel.md`, contrairement à la génération d'instances.
2. **Deux nouveaux blocs de contexte** dans le prompt `step2_develop_instance` : `## CHRONOLOGIE RÉELLE DU SCÉNARIO` et `## ÉTAT DU MONDE RÉEL`, plus une règle explicite demandant au LLM de rester cohérent avec les deux — en particulier pour une date proche dans le temps, où une escalade doit s'ancrer sur une tension réellement documentée plutôt que d'être inventée hors-sol. Le garde-fou existant `impossible_dans_scenario` (déjà dans le prompt) reste la soupape si l'événement demandé ne colle vraiment pas au scénario.
3. **Validation mécanique de `zone_hint`** contre `load_all_zones_event(scenario)` (fonction déjà existante, jusque-là utilisée seulement côté mode auto) — refaite à **chaque itération** de la boucle scénarios, initiale et retry inclus (une zone valide dans un scénario ne l'est pas forcément dans un autre, la géographie est propre à chaque scénario). Zone invalide → avertissement console + repli sur "libre" plutôt que transmission telle quelle au LLM.

**Testé en conditions réelles (dry-run)** sur une queue de 5 idées ciblant chacune un mécanisme précis : date proche (2028, escalade géopolitique — `note_coherence` a bien cité les tensions hydriques/infrastructures documentées dans l'état du monde réel), `zone_hint` invalide (warning déclenché comme attendu), `zone_hint` valide (silence, zone bien utilisée comme ancrage), cas de contrôle à date lointaine (non-régression confirmée), et surtout **un même `zone_hint` sur deux scénarios différents** — validé silencieusement sur `eco_communalism`, warning déclenché sur `breakdown` où la zone n'existe pas : preuve que la revalidation se refait bien à chaque itération de la boucle, pas une seule fois en amont. Ce dernier cas a aussi déclenché un vrai retry de validation (variable annoncée non impactée), confirmant que le zone_hint validé est bien réutilisé sur le retry et pas la version brute. **Note de méthode** : `--dry-run` sur ce script appelle réellement le LLM (voir §0, piège transversal du 31 juillet — seule l'écriture disque est sautée), donc ce test porte sur du contenu réellement généré, pas simulé.

**Confirmé en injection réelle (non dry-run) le 13 août 2026** — la même queue de 5 cas rejouée sans `--dry-run` : `zone_invalide_test` et `multi_scenario_zone_test`/`breakdown` ont de nouveau déclenché le warning `zone_hint` attendu (revalidation par scénario confirmée cette fois en écriture réelle, pas seulement en simulation), `escalade_sahel_2028_test` et `zone_valide_test` injectés au premier essai. Deux événements réels hors queue de test (`revolution_travail_sahel_numerique`, `greve_generale_corridors_eurasiens`) injectés avec succès sur tous leurs scénarios cibles le même jour, retries sur acteurs fonctionnant comme prévu. `validate.py` : 0 erreur, 10 avertissements, base valide. Le chemin d'écriture disque de ce chantier est donc définitivement confirmé fonctionnel.

**Bug trouvé au passage le 13 août — `evenement_cle` sans année finale, jamais corrigé par le retry.** Le 5e cas de la queue (`controle_date_lointaine_test`, test de non-régression sur une date lointaine, 2091) a épuisé ses 3 essais de retry sans jamais être injecté. `validate_instance()` exigeait une année en toute fin de `evenement_cle` (`re.search(r"(\d{4})\s*$", ...)`), mais le LLM produisait invariablement le format `"2091 : L'Europe unifie l'horloge..."` (année en tête, suivie d'un `:`) — sur les 3 essais consécutifs, sans jamais converger vers le format attendu, car le message de retry ne précisait pas *où* replacer l'année. Vérifié que la position de l'année dans `evenement_cle` n'a **aucune fonction technique en aval** : `date` est stockée séparément dans sa propre colonne du registre par `regenerate_registre_with_event()`, et `load_scenario_timeline_summary()` préfixe de toute façon sa propre date à l'affichage chronologique — la contrainte de position était une pure convention de style, sans nécessité. **Corrigé** : regex assouplie (`re.search(r"\b(\d{4})\b", ...)`, année à 4 chiffres acceptée n'importe où dans la phrase), prompt et exemple JSON mis à jour en cohérence (ne demandent plus une "année finale"), message d'erreur reformulé (`"sans année (4 chiffres)"`). **Confirmé en conditions réelles** : `controle_date_lointaine_test` relancé avec son idée d'origine (retrouvée dans `needs_review.yaml`, où le champ `idea` complet reste préservé même après le vidage systématique de `queue.yaml` en fin de run) — injecté au premier essai, `validate.py` toujours propre.

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
python3 enrich_minimal.py --skip-reciprocite   # désactive la passe de réciprocité automatique (voir ci-dessous)
python3 enrich_minimal.py --resoudre-conflits  # résout aussi les conflits de réciprocité (opposition prioritaire, voir 7 août ci-dessous)
python3 enrich_minimal.py --resoudre-conflits --bascule-en-opposition  # résolution "forte"
```
Sorties : `enrich_minimal_report.md`, `needs_review_enrich.yaml` (bug de tri des clés YAML corrigé le 2 août 2026 — voir plus bas). **P8 clos** : les 426 fiches `officialise_minimal` d'origine ont toutes été traitées en un seul run le 27 juin 2026 (trace laissée dans chaque fiche, section `## Notes` du corps : *« Fiche enrichie depuis officialise_minimal le 2026-06-27. »*) — confirmé le 2 août 2026 par recomptage sur le vault : zéro fiche `officialise_minimal` restante sur les 6 scénarios. Coût réel non recalculé (script tourne sur `mistral-large-latest` par défaut depuis le 11 juillet, l'estimation initiale de ~$37 avait été faite sur tarif Claude).

**Correctifs du 5 août 2026 (root cause du diagnostic alliances/oppositions du 4 août — voir `fix_alliances_oppositions.py` plus bas) :**
- **Nouvelle section de prompt "AUTRES INSTANCES DU SCÉNARIO (slugs valides)"**, construite par `build_instances_summary(scenario, exclude_slug)` — équivalent de `build_geographie_summary()` mais pour les instances, jusque-là absent. C'est la cause racine du vide massif d'`alliances`/`oppositions` découvert le 4 août : le LLM devait citer des slugs réels sans jamais les voir. Vérifié en conditions réelles sur une fiche de test (8/8 slugs générés confirmés réels dans le vault).
- **Réciprocité automatique en fin de run** — importe et appelle `reciprocity_pass()` de `fix_alliances_oppositions.py` (aucun appel LLM, purement local) pour chaque scénario traité, dès qu'au moins une fiche a été réellement enrichie (pas en `--dry-run`). Désactivable via `--skip-reciprocite`. **Dépendance directe** : `fix_alliances_oppositions.py` doit rester dans le même dossier.
- **Validation `alliances`/`oppositions` durcie partiellement** (`validate_enriched()`, nouveau paramètre `own_slug`) : l'auto-référence (un slug qui se cite lui-même) et le chevauchement alliances/oppositions (même slug dans les deux) sont désormais des erreurs bloquantes qui déclenchent le mécanisme de retry existant. Le warning sur un slug absent de `_entities_list.json` reste volontairement non bloquant — il alimente le pipeline de slugs fantômes (`extract_and_queue_phantoms()`, voir `extract_phantom_slugs.py` juste en dessous), une mécanique volontaire pour capter les références à des entités pas encore créées ; le durcir aurait cassé cette mécanique.
- Les trois correctifs testés unitairement et en conditions réelles (fiche jetable créée, enrichie, réciprocité déclenchée sur 7 fiches réelles du vault, puis nettoyée manuellement après vérification).

**Correctifs du 7 août 2026 — résolution automatique des conflits branchée sur `enrich_minimal.py` :**
- **Import** de `resolve_reciprocity_conflicts()` en plus de `reciprocity_pass()`, depuis `fix_alliances_oppositions.py` (même dépendance directe, doit rester dans le même dossier).
- **Deux nouveaux flags, opt-in, désactivés par défaut** : `--resoudre-conflits` (déclenche la résolution automatique des conflits selon la règle "opposition prioritaire" — une opposition déclarée l'emporte sur une alliance déclarée en cas de contradiction — juste après la passe de réciprocité), `--bascule-en-opposition` (avec le précédent : résolution "forte", ajoute aussi l'entité aux oppositions au lieu de la retirer simplement des alliances).
- **Comportement par défaut strictement inchangé** sans ces flags — la réciprocité continue de simplement détecter et journaliser les conflits comme avant.
- **Portée** : la résolution ne porte que sur les scénarios réellement traités par le run en cours (pas tout le vault), cohérent avec le fonctionnement existant d'`enrich_minimal.py`. `--skip-reciprocite` reste prioritaire — s'il est présent, toute la chaîne s'arrête (réciprocité et résolution), même si `--resoudre-conflits` est aussi précisé.
- Le message de `reciprocity_pass()` est adapté en conséquence (paramètre `resolution_suit`, propagé automatiquement depuis `--resoudre-conflits`) pour éviter d'annoncer un conflit "non résolu automatiquement" juste avant que la résolution ne s'exécute.
- **Testé** : câblage complet vérifié par mocks des fonctions bas niveau (isolant l'orchestration de la logique d'enrichissement elle-même, non touchée) — comportement par défaut inchangé sans flag, activation correcte avec `--resoudre-conflits`, propagation de `--bascule-en-opposition` sur les 6 scénarios via `--all`, et confirmation que `--skip-reciprocite` neutralise bien toute la chaîne y compris la résolution.

**Complément du même jour (7 août, après-coup) — `reset_conflict_reports()`** : bug distinct trouvé après coup (David consultant le rapport `.md` via le GUI, croyant le vault plein de conflits alors qu'il était déjà à 0 — voir Bug #2, détail complet dans l'entrée `fix_alliances_oppositions.py` ci-dessous). `enrich_minimal.py` importe désormais aussi `reset_conflict_reports()`, appelée une seule fois avant la boucle sur les scénarios (inconditionnellement dès qu'un run réel de réciprocité a lieu, pas seulement quand `--resoudre-conflits` est actif — la réciprocité seule écrit déjà dans `CONFLICTS_PATH`). Jamais déclenché en `--dry-run`. Testé : `reset_conflict_reports()` appelée exactement une fois pour tout un run `--all` (pas une fois par scénario), jamais en dry-run.

### `fix_alliances_oppositions.py` — voir entrée dédiée dans la section scripts one-shot/migration plus bas, dont `enrich_minimal.py` dépend désormais pour la réciprocité automatique **et**, depuis le 7 août, la résolution automatique des conflits.

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

## 3bis. Chantier `trajectoire` — fusion etat_temporel + age_historique (9 août 2026)

**Point de départ** : incohérence trouvée sur `zones_extractivistes_
corridors_eco_communalism` (`age_historique: ascendant` +
`etat_temporel: transformé` sur la même fiche — les deux champs se
chevauchaient conceptuellement, une entité "transformée" a
nécessairement un "âge" associé, et rien ne garantissait leur cohérence
mutuelle). `etat_temporel` (6 valeurs) et `age_historique` (8 valeurs)
fusionnés en un seul axe narratif continu :

```
émergent → marginal → ascendant → dominant → mature → déclinant
  → résiduel → transformé → disparu → historique → mythifié
```

`clandestin` sort de l'axe, devient un booléen indépendant
`est_clandestin` — une entité peut désormais être n'importe quelle
position sur l'axe ET clandestine en même temps (impossible avant :
`clandestin` était une valeur d'`etat_temporel` parmi d'autres, exclusive
des autres valeurs).

**Fichiers modifiés** : `loader.py` (schéma), `validate.py`
(`VALID_TRAJECTOIRE`, `TRAJECTOIRE_INACTIVES` — unifie 3 anciennes
définitions divergentes : `INACTIVE_ETATS`, `ETAT_INACTIFS`, et le
hardcode `"disparu"` du check C4, qui rendait invisibles à la validation
les fiches `transformé`/`historique`/`mythifié` sans `annee_fin` — bug
corrigé au passage), `prompt_builder.py` (badge `[TRAJECTOIRE]
[CLANDESTIN]` combinable dans `build_entities_context()`),
`officialize_alliances.py` (template), `enrich_minimal.py` (lecture
contextuelle), `instance_generation_common.py` (voir §1 — cœur de la
génération), `create_entities_and_instances.py`/`generate_instances.py`
(imports uniquement, grâce à la factorisation).

**`TRAJECTOIRE_COHERENCE_MAP`** (`validate.py`) — avertissement doux de
cohérence entre `trajectoire` d'une instance et `state_of_system` de son
scénario. Recalibré deux fois en session après des faux positifs massifs
(oubli d'`émergent` dans toutes les lignes du premier essai → 528
avertissements sur 710 fiches migrées), puis **simplifié sur demande de
David** : ne couvre plus que `resilient`/`collapsing` (les deux seuls
`state_of_system` où le check discrimine vraiment) — `chaotique`/
`fragile`/`instable`/`stable` n'ont plus d'entrée, le check y est donc
silencieux (comportement voulu, pas un oubli).

**`migrate_trajectoire.py`** *(nouveau script, migration ponctuelle
déjà exécutée sur le vault entier)* — mécanique, aucun appel LLM. Règles
de migration (priorité : `age_historique` explicite > défaut) :
`transformé`/`disparu`/`historique`/`mythifié` → inchangé (position
terminale prime toujours) ; `actif`/`clandestin` avec `age_historique`
explicite et valide → mapping 1:1 (pas un défaut, un choix déjà fait) ;
`actif`/`clandestin` sans `age_historique` → `mature` + marqueur
`trajectoire_migree_par_defaut: true` (pour retravail ciblé futur, même
logique que `annee_debut_verifiee`). `etat_temporel`/`age_historique`
supprimés du frontmatter immédiatement après migration (pas de
cohabitation temporaire — vault versionné Git, rollback possible sans
champs dupliqués). **Ne devrait plus jamais être relancé en usage
normal** : one-shot, tout nouveau contenu écrit directement `trajectoire`
via `instance_generation_common.py`. Pas ajouté au GUI pour cette raison.

**`audit_etat_temporel_fin.py`** — corrigé pour lire `trajectoire`
(importe `TRAJECTOIRE_INACTIVES` de `validate.py`, une seule source de
vérité). Sert de point de départ au chantier `annee_fin` (voir §5).

**GUI (`scripts_config.json`)** — entrée `create_entities`, champ
`etat` (mode custom) : 6→11 valeurs (voir §3, mode custom). Nouveau
champ `est_clandestin` (select tri-état `oui`/`non`/vide, car
`hard_constraint.est_clandestin` est `None`/`True`/`False` — un simple
checkbox HTML ne peut pas exprimer "indifférent"). Câblage Python
complet : `_parse_optional_bool()` (nouveau helper), paramètre
`est_clandestin_ref` ajouté à `write_entity_file()` (n'écrit la ligne
que si une contrainte a été explicitement posée) et propagé dans
`process_custom_idea()`.

**Erreurs trouvées et corrigées en session, avant qu'elles n'atteignent
le vault** (repasse systématique diff par diff contre le code source
réel avant livraison de `instance_generation_common.py`) : `parse_md()`
réécrit de mémoire au lieu d'être recopié — aurait cassé le parsing des
wikilinks `[[...]]` dans le frontmatter ; `_est_ligne_separateur()`/
`_parse_registre_table()` avec un algorithme différent de l'original ;
`load_variables_states()` retournant le mauvais champ (`level` au lieu
de `state_logic`) ; `zone_hint` transformé en paramètre explicite non
alimenté par les appelants (aurait cassé sa prise en compte en mode
custom) — corrigé en le lisant en interne depuis `entity_fm.get(
"zone_hint")`, comme dans le code d'origine.

**Vérification finale** : 710 fiches migrées, 0 erreur `validate.py`,
badge GUI testé sur `create_entities_and_instances.py` mode custom (run
réel avec `zone_hint`, `hard_constraint`, entité de test nettoyée après
coup via `undo_custom.py`).

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

### Chantier `annee_fin` (9 août 2026) — clos

28 fiches à `trajectoire` terminale (`transformé`/`disparu`) sans
`annee_fin` renseignée (93,3% d'incohérence sur cette sous-population,
mesuré par `audit_etat_temporel_fin.py`). Corrigé par
**`fix_annee_fin_manquant.py`** *(nouveau script)*, modèle repris de
`fix_annee_debut_placeholder.py` mais **sans ancrage sur `etat_du_monde_
reel.md`** — une date de fin d'entité fictive n'a pas besoin d'être
reliée au monde réel d'aujourd'hui, seulement à la chronologie interne
du scénario (`registre_evenements.md`). Règle de priorité : jalon du
registre en premier si clairement identifiable, sinon estimation depuis
le contexte narratif déjà écrit (`role_dans_scenario`,
`tensions_narratives`, `description_journalistique`). Contrainte stricte
`annee_debut < annee_fin ≤ 2098`.

**Résultat** : 27/28 corrigées directement. 1 cas résistant
(`consortium_helios_new_sustainability`, le LLM proposait
systématiquement `2101` sur plusieurs tentatives et deux runs distincts,
malgré une consigne de plafonnement explicite ajoutée au prompt en cours
de session) — résolu par un **filet de sécurité automatique** ajouté au
script : plafonnement à 2098 si un dépassement persiste après
épuisement des tentatives LLM (jamais utilisé au final sur ce cas
précis, le prompt renforcé a fini par suffire seul). Le filet ne
s'applique JAMAIS si le seul problème est `annee_fin ≤ annee_debut` ou
une valeur non numérique — ces cas restent de vrais échecs à examiner
manuellement.

Concentration observée sur quelques années (2061, 2057, 2053 sur
`breakdown`) vérifiée légitime en examinant le détail des
justifications — chaque jalon du registre est réutilisé par plusieurs
fiches avec un raisonnement narratif distinct et contextualisé à chaque
fois (pas une convergence artificielle du LLM vers une réponse par
défaut).

**Vérification finale** : `audit_etat_temporel_fin.py` → 30/30 fiches
cohérentes (0% d'incohérence). `validate.py` → 0 erreur.

Idempotence naturelle (pas de marqueur nécessaire comme
`annee_debut_verifiee` — une fiche avec `annee_fin` déjà renseignée
n'est simplement plus candidate).

### `audit_longueur_articles.py` *(nouveau, 9 août 2026, section GUI Validation)*

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) : compare
trois informations pour chaque article de `articles/*.md` — longueur
réelle (comptage de mots du corps), champ `format` du frontmatter (nom
de catégorie, ex. `"analyse"` — TOUJOURS dérivé de
`thematique.get("format_dominant")`, jamais de l'override de config), et
champ `longueur` (plage textuelle déjà résolue, ex. `"600 à 900 mots"` —
qui elle tient compte de l'override si un override a été fourni).
Distingue le **Cas A** (format et longueur pointent vers la même plage —
pas d'override, le vrai signal de qualité) du **Cas B** (divergence —
override probable, pas un signe de bug).

**Trois itérations en session pour arriver à un diagnostic fiable** :
v1 cherchait `longueur` comme un nom de catégorie (faux — c'est une
plage textuelle déjà résolue, 100% de faux positifs "étiquette
inconnue") ; v2 corrigé pour parser la plage textuelle directement, mais
mélangeait deux causes différentes dans un seul taux (64,5%) ; v3
(actuelle) sépare Cas A/Cas B — chiffre final fiable : **70,4%
d'incohérence sur les cas analysables (Cas A)**, tous les cas de
divergence observés sur le vault (4, tous `format: brève`) se sont
révélés être le symptôme du bug d'accent ci-dessous, pas de vrais
overrides délibérés.

**Bug de production trouvé en marge de cet audit** — `FORMAT_LONGUEUR`
(`prompt_builder.py`) ne couvrait que les orthographes sans accent
(`breve`, `editorial`, `reflexif`), alors que `VALID_FORMATS`
(`validate.py`) accepte explicitement les deux orthographes pour
chacune. Toute thématique avec `format_dominant: brève` (accentué)
retombait silencieusement sur le filet de secours générique `"300 à 500
mots"` au lieu de sa vraie plage `"200 à 400 mots"`. Corrigé : les 3
variantes accentuées ajoutées à `FORMAT_LONGUEUR`, un seul dict
module-level donc correctif appliqué automatiquement aux deux points
d'usage (`build_journalistic_brief()`, `build_prompt()`).

**Sujet de qualité ouvert le 9 août, en grande partie traité le 10 août**
— le taux de 70,4% (Cas A) a déclenché tout le chantier documenté en
§2ter : renforcement du prompt (insuffisant seul, testé), puis retry
automatique (mécanisme en place, testé positivement sur un échantillon
de 12 articles — 3 retries déclenchés, tous améliorés). Voir §2ter pour
le détail complet, et `BACKLOG_MASTER_9_AOUT.md` Partie 4 pour le
statut actualisé de ce point dans le backlog.

**Mis à jour le 10 août 2026** : scan rendu récursif (`os.walk` au lieu
de `os.listdir`) — sinon les articles générés en série/manuel dans
`articles/{scenario}/` devenaient invisibles à cet audit après le
correctif du dossier de sortie (§2ter point 7). Les fichiers `_index.md`
sont désormais explicitement ignorés (avant, simplement jamais atteints
par un scan non récursif). Affichage par chemin relatif pour distinguer
un fichier de la racine d'un fichier de sous-dossier. Confirmé en
conditions réelles (43 fichiers retrouvés à travers racine et
sous-dossier).

**Mis à jour le 11 août 2026** : validée par David dans le navigateur,
marquée `gui_verified: true` (avec les 3 autres audits — voir §7,
addendum du 11 août).

---

## 6. Scripts one-shot / migration / legacy

Ces scripts ont rempli leur rôle ponctuel ou ont été remplacés — à ne relancer que dans un cas précis documenté ci-dessous, jamais en routine.

| Script | Rôle | Statut |
|---|---|---|
| `create_entity.py` | Ancienne brique 1/2 (création d'entité seule, sans instances). Remplacé par `create_entities_and_instances.py`. | 📦 Legacy — conservé pour référence |
| `generate_instances.py` | **Actif, PAS legacy (corrigé le 9 août 2026)** — génère les instances pour des entités DÉJÀ créées dans `entites/`, sans créer aucune nouvelle entité. Distinct et complémentaire de `create_entities_and_instances.py` (qui crée toujours entité + instances ensemble) — confirmé par une entrée GUI dédiée (`scripts_config.json`, id `generate_instances`, label "Générer les instances manquantes", section `entites_creation`), qui décrit explicitement les deux scripts comme deux fonctions différentes, pas une redondance. Cette ligne du manuel affirmait à tort l'inverse ("fusionnée dans create_entities_and_instances.py") depuis une session antérieure — la modification du 8 août (`--ancrage-temporel`) sur ce fichier était donc légitime, pas une erreur comme d'abord suspecté en session du 9 août avant vérification du GUI. Factorisé le 9 août avec `create_entities_and_instances.py` dans `instance_generation_common.py` (voir §1) — les deux scripts partagent désormais la même logique de génération d'instance, sans duplication. | ✅ Actif |
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
| `fix_alliances_oppositions.py` | **Nouveau (4 août 2026), étendu le 5 et le 7 août.** Corrige le vide structurel de `alliances`/`oppositions` sur les fiches déjà `officialise_enrichi` (diagnostic initial : 356/426 fiches, 83.6%, avaient les deux champs vides — cause racine : `enrich_minimal.py` ne fournit jamais au LLM la liste des instances réelles du scénario au moment de générer ces champs, contrairement à la géographie). Prompt ciblé et minimal (alliances/oppositions UNIQUEMENT, aucun autre champ régénéré), avec la liste réelle des instances du scénario fournie en contexte — ingrédient manquant du prompt d'origine. Patch chirurgical du frontmatter (regex sur 2 clés, pas de réécriture YAML complète) + section `## Relations` ajoutée/mise à jour dans le corps. Deuxième passe locale sans LLM : réciprocité (si A cite B en alliance/opposition, B doit citer A en retour), avec détection de conflits (relation contradictoire des deux côtés). Retry/backoff intégré sur les pannes API transitoires (503, etc.), distinct du mécanisme de correction de contenu.<br><br>**Résolution automatique des conflits (7 août 2026, règle "opposition prioritaire")** : `resolve_reciprocity_conflicts()` — une opposition déclarée l'emporte sur une alliance déclarée en cas de contradiction. Pour chaque conflit détecté, l'entité qui liste l'autre en *opposition* n'est jamais modifiée ; l'entité qui la listait en *alliance* est corrigée (slug retiré de `alliances`, et ajouté aux `oppositions` si `--bascule-en-opposition`). RÉTROACTIF : modifie les fiches déjà en conflit sur disque (sauf `--dry-run`). Chaque résolution journalisée dans `documentation/need_action/fix_alliances_conflits_reciprocite_resolus.md`.<br><br>**Bug #1 trouvé et corrigé en conditions réelles le 7 août — écrasement multi-conflits** : la première version écrivait un patch par conflit traité, en repartant à chaque fois du frontmatter *original* lu en mémoire plutôt que de l'état déjà modifié — une fiche impliquée dans **plusieurs conflits distincts** du même scénario voyait sa dernière résolution traitée écraser silencieusement les précédentes. Découvert après un premier `--apply` réel (73 conflits annoncés résolus, mais 11 paires/22 lignes retrouvées encore en conflit à la revérification `--dry-run`). Corrigé en accumulant toutes les corrections par fiche avant d'écrire (un seul `write_alliances_patch()` par fiche, même pattern déjà utilisé par `reciprocity_pass()`) — reproduit exactement sur mini-vault synthétique (entité en conflit avec deux autres simultanément), confirmé résolu, aucune régression sur le cas à un seul conflit. Deuxième `--apply` relancé sur le vault réel après correction, revérifié par `--dry-run` : 0 conflit restant, vault entièrement cohérent.<br><br>**Bug #2 trouvé et corrigé le 7 août — rapports jamais réinitialisés (confusion GUI)** : `CONFLICTS_PATH` et `RESOLVED_CONFLICTS_PATH` étaient ouverts en mode `"a"` (append) depuis leur création le 4 août — jamais tronqués, ils accumulaient indéfiniment l'historique de TOUS les runs. Découvert quand David, en consultant `fix_alliances_conflits_reciprocite.md` (par le GUI, où le fichier est affiché tel quel dans le panneau de review), a cru le vault plein de conflits alors qu'il était déjà à 0 depuis plusieurs runs — la dernière section du fichier datait en réalité de l'exécution de diagnostic *avant* la correction du Bug #1 (confirmé par la présence du texte "Règle C", terminologie abandonnée depuis). **Correctif** : nouvelle fonction `reset_conflict_reports()`, appelée une seule fois en tête de run (avant la boucle sur les scénarios) par les deux points d'entrée (`fix_alliances_oppositions.py::main()` et `enrich_minimal.py`), qui tronque les deux fichiers à un simple en-tête horodaté ; les écritures par scénario du même run s'accumulent ensuite normalement dessus (`_write_conflict_report()`, tracking via un set module-level `_files_reset_this_run`). Cas limite couvert explicitement : un run où *aucun* scénario n'a de conflit ne déclenche aucune écriture par scénario — sans le reset explicite en tête de run, un vieux fichier périmé serait resté affiché indéfiniment même après un vault redevenu propre. Jamais déclenché en `--dry-run` (les deux points d'entrée gardent l'appel derrière `not args.dry_run`/`not dry_run`). Testé : reproduction exacte du cas réel (vieux contenu périmé simulé + run propre à 0 conflit → fichier ne contient plus que l'en-tête), dry-run confirmé sans écriture, multi-scénarios dans un même run confirmé sans écrasement entre sections. Descriptions GUI des deux entrées (`fix_alliances_oppositions`, `enrich_minimal`) mises à jour en conséquence (voir §7).<br><br>Testé au total : mini-vault synthétique (détection, dry-run sans écriture, résolution conservatrice, non-modification de l'entité opposante, idempotence, cas multi-conflits, reset des rapports), puis en conditions réelles sur le vault complet (146 lignes de conflits bruts → 73 paires uniques, ratio 2:1 exact sur les 5 scénarios concernés — `breakdown` 12, `fortress_world` 11, `new_sustainability` 13, `policy_reform` 13, `reference` 24 ; `eco_communalism` 0 — puis 0 conflit confirmé après correction du Bug #1).<br><br>Message de `reciprocity_pass()` adapté (7 août) : nouveau paramètre `resolution_suit` (défaut `False`, rétrocompatible) — si `True` (passé automatiquement quand `--resoudre-conflits` est actif), le message de conflit affiche "sera résolu automatiquement ci-dessous (opposition prioritaire)" au lieu de "conflit non résolu automatiquement (revue manuelle nécessaire)", pour éviter la confusion entre les deux passes qui s'enchaînent dans le même run.<br><br>Flags CLI : `--scenario`\|`--all`, `--slug`, `--dry-run`, `--limit`, `--reciprocite-seule`, `--skip-reciprocite`, `--resoudre-conflits`, `--bascule-en-opposition` (résolution "forte" : ajoute aussi l'entité aux oppositions au lieu de la retirer simplement des alliances ; par défaut résolution conservatrice, retrait seul). | 🔧 **Ce n'est plus un simple one-shot** — migration initiale terminée et vérifiée le 4 août (vault entier passé de 356/426 fiches vides à 0/426, 563 complétions par réciprocité). Depuis le 5 août, **`enrich_minimal.py` importe directement `reciprocity_pass()`** pour la lancer automatiquement en fin de run. Depuis le 7 août, **`enrich_minimal.py` importe aussi `resolve_reciprocity_conflicts()` et `reset_conflict_reports()`**, la résolution restant activable via les flags opt-in `--resoudre-conflits`/`--bascule-en-opposition` (comportement par défaut inchangé sans eux — voir §3, entrée `enrich_minimal.py`) tandis que le reset des rapports, lui, est inconditionnel dès qu'un run réel de réciprocité a lieu — ce script est donc une dépendance de production à part entière, pas seulement un outil de migration ponctuel. Doit rester dans le même dossier qu'`enrich_minimal.py`. **Intégré au GUI le 7 août** (voir §7) — entrée `fix_alliances_oppositions` ajoutée à `scripts_config.json`, plus les deux nouveaux flags ajoutés à l'entrée `enrich_minimal` existante. Ni l'une ni l'autre testée dans un vrai navigateur à cette date (`gui_verified: false` pour les deux), mais leur fonctionnement (`depends_on`+`advanced` combinés, affichage `.md` dans le panneau de review) avait été vérifié par lecture directe du code source réel d'`app.py`/`app.js` (obtenus en session) — les deux mécanismes confirmés fonctionnels sans ambiguïté. **Mise à jour du 11 août 2026** : `fix_alliances_oppositions` validée par David dans le navigateur, descriptif principal et les 7 options entièrement reformulés en langage moins technique (jargon pipeline "passe LLM"/"rétroactif" clarifié, chemins de fichiers bruts retirés des libellés de rapports — voir §7, addendum du 11 août pour le détail), marquée `gui_verified: true`. `enrich_minimal` reste non testée à ce jour (`gui_verified: false`, pas concernée par cette validation). |
| `build_geographie_monde.py` | Rétro-construit la bible géopolitique plate d'un scénario (étape 1 du chantier géographie). Déjà lancé sur les 6 scénarios, définitifs. | 🪦 **Retiré du sidebar le 26 juillet 2026** — one-shot par scénario, nouvelle règle : plus sa place dans le panneau même pour un `--force` ponctuel. Reste utilisable en CLI directe. |
| `generate_manual.py` | Pipeline sans appel API : affiche le prompt (system+user) du prochain article d'une série pour copier/coller dans un chat externe, avec suivi de rotation multi-articles (`state/manual_progress.json`). | 🪦 **Retiré du sidebar le 31 juillet 2026** — son cas d'usage principal (aperçu de prompt copiable) est couvert par `--dry-run` sur `generate.py`, qui affiche le même contenu sans le mécanisme de rotation de série. Reste utilisable en CLI directe pour le suivi multi-articles. |
| `fix_annee_debut_placeholder.py` | **8 août 2026** *(rangement de gap — ce script existait déjà et était en usage réel, jamais ajouté à ce tableau avant le 9 août)*. Corrige rétroactivement `annee_debut` sur les fiches `officialise_enrichi` bloquées au placeholder 2026 (chantier `annee_debut`, clos le 8 août — voir `BACKLOG_MASTER_9_AOUT.md` Partie 4). Ancrage sur `registre_evenements.md` (chronologie fictive du scénario) ET `etat_du_monde_reel.md` (référence factuelle réelle), avec bande de traçabilité graduée (`ancrage_reel`, obligatoire si `annee_debut < 2036`). Marqueur `annee_debut_verifiee: true` pour l'idempotence. Modèle repris pour `migrate_trajectoire.py` et `fix_annee_fin_manquant.py` ci-dessous. **Mise à jour du 11 août 2026** : descriptif GUI reformulé en langage moins technique (jargon interne retiré — `officialise_enrichi`, `ancrage_reel`, `annee_debut_verifiee` ne sont plus mentionnés dans le texte affiché à l'utilisateur, tout en gardant l'essentiel : ce que ça fait, et la garantie que c'est sans risque à relancer). Validée par David dans le navigateur, marquée `gui_verified: true`. | 🪦 One-shot, chantier clos — ne relancer que si de nouvelles fiches réapparaissent au placeholder 2026 |
| `migrate_trajectoire.py` | **Nouveau, 9 août 2026.** Migre les fiches instances de l'ancien schéma (`etat_temporel`+`age_historique`) vers `trajectoire`+`est_clandestin` (voir §3bis). Purement mécanique, **aucun appel LLM** (contrairement à `fix_annee_debut_placeholder.py`) — les règles de mapping sont entièrement déterministes. Idempotent (skip toute fiche ayant déjà la clé `trajectoire`). | 🪦 One-shot, déjà exécuté sur les 710 fiches du vault — **ne devrait plus jamais être relancé en usage normal**, voir §3bis pour le détail. Pas au GUI, volontairement. |
| `fix_annee_fin_manquant.py` | **Nouveau, 9 août 2026.** Corrige rétroactivement `annee_fin` sur les fiches à `trajectoire` terminale sans date de fin (chantier `annee_fin`, clos le 9 août — voir §5). Modèle repris de `fix_annee_debut_placeholder.py`, sans ancrage sur `etat_du_monde_reel.md`. Filet de sécurité de plafonnement automatique à 2098 en cas de dépassement persistant après épuisement des tentatives LLM. | 🪦 One-shot, chantier clos — ne relancer que si de nouvelles fiches à trajectoire terminale sans `annee_fin` réapparaissent |

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

1. **Entrée fantôme dans la carte INSTANCES du dashboard** — `instance_template.md` (le gabarit du projet, placeholders `<slug_scenario>` etc. jamais remplis, c'est normal) vivait directement dans `instances/`, au milieu des vraies fiches. `_stats_instances()` le comptait comme une 711e instance ; sa valeur `scenario: <slug_scenario>` partait telle quelle dans le JSON du dashboard et le navigateur avalait la balise non échappée, affichant une entrée fantôme `: 1`. Même pollution trouvée dans `_stats_enrichissement()` (le gabarit n'a pas de champ `statut:`, il gonflait silencieusement le seau `"autre"`). **Correctif du 2 août** : exclusion explicite de `instance_template.md` dans les deux fonctions — même filtre déjà présent dans `officialize_alliances.py` (ligne 223) mais absent partout ailleurs à l'époque. **Recommandation structurelle appliquée le 14 août 2026** : `instance_template.md` déplacé hors de `instances/` vers un dossier `templates/` — règle le problème structurellement pour tous les scripts d'un coup, sans besoin d'auditer individuellement `create_entities_and_instances.py`, `enrich_minimal.py` ×2, `extract_phantom_slugs.py`, `fix_impact_scale.py` (l'angle mort qu'ils pouvaient avoir n'existe plus, le fichier n'étant simplement plus dans `instances/`).

2. **Panneau Revue (`/api/review` dans `app.py`) vide malgré des fiches en échec** — `enrich_minimal.py` (`write_needs_review()`) était le seul appel `yaml.dump()` du pipeline sans `sort_keys=False` : PyYAML triait les clés alphabétiquement (`date` avant `slug`), et le parseur maison de `app.py` (`_read_needs_review_yaml()`) ne reconnaissait une nouvelle entrée que via `"- slug:"` en tête de ligne — plus aucune ligne ne matchait, toutes les entrées `needs_review_enrich.yaml` étaient silencieusement ignorées. **Correctif** : `sort_keys=False` ajouté à l'écriture. **Deuxième gap trouvé en creusant** : `/api/review` ne couvrait que 2 des 4 sources possibles de fiches en échec (`needs_review_enrich.yaml`, `evenements_custom/needs_review.yaml`) — `entites_custom/needs_review.yaml` et `signaux_custom/needs_review.yaml` (première clé `status:`, format différent) n'étaient ni lus ni comptés. **Correctif** : deux nouvelles fonctions `_parse_needs_review_entites()`/`_parse_needs_review_signaux()` + généralisation du parseur (`start_marker` optionnel) ; `_count_review_items()` (le badge, dans `routes_dashboard.py`) complété avec les deux mêmes fichiers. La limite du slug générique `(entité)`/`(signal)` restante à cette date a été comblée par un correctif ultérieur du 12 août — voir plus bas dans ce document.

### Sidebar (`scripts_config.json`) — scripts lançables en un clic
**Section génération** : `enrich_minimal`, `generate_journaux`, `validate`, `generate` (deux modes depuis le 2 août 2026 — Semi-guidé/Forcer, voir §2), `generate_series`, `generate_manual`.
**Section entités** : `create_entities`, `inject_events`, `inject_signals`, `extract_phantom_slugs`, `requeue_needs_review`, `undo_custom`, `trace_injection` (nouveau, 2 août 2026 — voir §2).
**Section maintenance** : `extract_localisation`, `review_localisation`, `enrich_geographie` (l'entrée fantôme `restructure_zones` a été retirée, confirmé le 2 août 2026 — voir §4).

Chaque entrée définit ses options (checkbox/select/number/slug_select/multi_select), ses dépendances (`requires`) et les fichiers YAML associés affichables dans le panneau de review. Vérification systématique faite le 11 juillet (backlog P6, clos) : chaque `flag` déclaré ici croisé avec l'`argparse` réel du script Python correspondant — 2 flags fantômes trouvés et supprimés (`--scenario` sur `create_entities`/`inject_events`, jamais lus par les scripts avant d'y être réintroduits avec un vrai rôle).

⚠️ Description "Section génération/entités/maintenance" ci-dessus **périmée** depuis la réorganisation du 12 juillet (8 sections nommées, voir mémoire de session) — à corriger dans une prochaine passe de mise à jour du manuel (dette documentaire connue).

#### `fix_alliances_oppositions.py` — intégré au panneau le 7 août 2026
Jusqu'au 5 août, en CLI-only (backlog historique §1.2) — jamais enregistré dans `scripts_config.json`, alors qu'il était déjà devenu une dépendance de production (import direct de `reciprocity_pass()` par `enrich_minimal.py`). **Intégré réellement le 7 août**, cette fois-ci contre le vrai `scripts_config.json` (upload obtenu, schéma vérifié plutôt que deviné) :

- **Nouvelle entrée `fix_alliances_oppositions`** ajoutée section `entites_nettoyage`, juste après `enrich_minimal`. 9 options (`--all`/`--scenario` en exclusion mutuelle avec `required_one_of`, `--slug`, `--limit`, `--dry-run`, `--reciprocite-seule`, `--skip-reciprocite`, `--resoudre-conflits`, `--bascule-en-opposition`). `--bascule-en-opposition` en `depends_on: "--resoudre-conflits"` + `advanced: true` (repliée sous "Options avancées"), même pattern que le "niveau 2" du 26 juillet (correction implique diagnostic parent). Interaction `--resoudre-conflits`/`--skip-reciprocite` documentée en texte dans la description (pas de mécanisme GUI natif pour une dépendance "sauf si l'autre est cochée").
- **Entrée `enrich_minimal` existante complétée** : les deux mêmes flags `--resoudre-conflits`/`--bascule-en-opposition` ajoutés à ses options (le script les supporte nativement depuis le 7 août — voir §3). Toutes les options d'origine conservées à l'identique, comparaison automatisée confirmée contre le fichier avant/après.
- `yaml_files` des deux entrées pointent vers les deux rapports (`fix_alliances_conflits_reciprocite.md` détectés / `_resolus.md` résolus) — **confirmé, plus une inconnue** : `app.py`/`app.js` obtenus et lus en session le 7 août. `/api/yaml` (`app.py`) lit n'importe quel fichier comme texte brut (`read_text()`, aucun parsing YAML malgré le nom de la route) ; côté front, `loadYamlContent()` fait `viewEl.textContent = data.content` sans vérification d'extension. Le `.md` s'affiche donc normalement, comme n'importe quel autre fichier du panneau.
- **`depends_on` + `advanced` combinés (`--bascule-en-opposition`) — confirmé, plus une inconnue.** Les options `advanced` sont rendues dans un second passage, après toutes les options normales, regroupées sous un `<details>` replié (`renderScriptForm()`). `syncDependsOnParents()` cherche `[data-depends-on]` dans tout `#form-body` sans se soucier de l'imbrication visuelle, donc le lien parent/enfant fonctionne correctement même depuis l'intérieur du repli — vérifié que `--resoudre-conflits` (le parent, une option normale) est bien rendu avant `--bascule-en-opposition` dans l'ordre des `options` des deux entrées, condition nécessaire au bon fonctionnement (le code suppose le parent déjà présent dans le DOM, cf. commentaire du 26 juillet dans `app.js`). **Seule nuance, cosmétique et non bloquante** : l'indentation visuelle prévue pour `depends_on` (bordure + retrait à gauche) s'affichera à l'intérieur du bloc "Options avancées" plutôt que juste sous son parent directement — pas un bug, juste un rendu un peu moins lisible que le cas normal (non-`advanced`) de ce mécanisme.
- Toutes les conventions suivies par déduction sur les entrées `gui_verified: true` existantes (`mutually_exclusive_with` en noms nus, `depends_on`/`required_one_of` avec `--` complet, `source: "config_scenarios"`) confirmées exactes par lecture directe du code — rien à corriger sur ce point.
- **`gui_verified: false` reste néanmoins sur les deux entrées** — la logique est confirmée par lecture de code, mais personne n'a encore cliqué dans un vrai navigateur. Seul test restant : ouvrir concrètement le panneau et cliquer.

**Complément du même jour (7 août, après le Bug #2 — voir §6)** : les deux rapports `.md` affichés par ces `yaml_files` sont maintenant réinitialisés à chaque run réel (`reset_conflict_reports()`), donc le panneau de review affichera systématiquement l'état du dernier run, jamais un historique cumulé périmé. Description de script (`script.description`, affichée en haut du panneau via `form-script-desc`) mise à jour sur les deux entrées pour le préciser explicitement.

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

#### Bugs GUI corrigés le 11 août 2026 (session soir)

- **`queue.yaml` écrasé par un panneau caché** (`saveOpenConfigForms()`, `app.js`) — un run `create_entities` en mode auto-suggest avait bien écrit 5 idées dans `entites_custom/queue.yaml` (confirmé par le log), mais le fichier était retrouvé vide juste après. Cause : `saveOpenConfigForms()` (ajoutée le 31 juillet, voir ci-dessus) sauvegarde tout panneau `.yaml-form-panel` présent dans `#form-body` avant de lancer un script, sans vérifier s'il est pertinent pour le mode actif — un panneau `config_fields_mode` (le formulaire Custom de `create_entities`, réservé à ce mode) reste dans le DOM même caché par un autre mode (`updateModeOnlyVisibility()` ne fait que du `display:none`, jamais un retrait du DOM). Ce panneau, resté ouvert/vu plus tôt dans la session et jamais rempli, a donc été sauvegardé **vide** par-dessus le fichier qu'auto-suggest venait d'écrire. Corrigé : `saveOpenConfigForms()` ignore désormais tout panneau dont le mode déclaré ne correspond pas à l'onglet Mode actif au moment du clic Lancer — même logique que `updateModeOnlyVisibility()`. **Portée potentielle non vérifiée** : `inject_events`/`inject_signals` ont le même mécanisme `config_fields_mode`, même angle mort probable, jamais testé spécifiquement. Testé en conditions réelles : `queue.yaml` retrouve bien son contenu après correctif.
- **Placeholder cassé + réapparition d'une saisie ancienne (champ Angle, `generate.py`)** — deux causes distinctes derrière le même symptôme signalé par David ("Angle : romuva la nouvelle religion en europe" réapparaissant dans le récapitulatif malgré un champ vide à l'écran). **(1) Bug JS réel, pas la cause de la persistance** : `renderOption()` fixait `inp.placeholder = opt.label` (le libellé du champ) au lieu de `opt.placeholder` (le texte d'exemple prévu) — corrigé, `autocomplete="off"` ajouté en prévention sur tous les champs texte générés dynamiquement, bien que confirmé non responsable du symptôme initial. **(2) La vraie cause, pas un bug de code** : un champ texte vide dans le formulaire GUI n'envoie tout simplement pas le flag CLI correspondant (`collectArgs()`, comportement voulu), donc le mode Semi-guidé retombe sur `config.yaml` comme base — qui gardait `angle_specifique: romuva la nouvelle religion en europe` depuis un test d'il y a plusieurs semaines, jamais nettoyé (rien ne l'écrase tant que le champ reste vide côté GUI). Nettoyé manuellement par David (`config.yaml` ligne 44 vidée), confirmé résolu au run suivant.
- **`--zone-slug` proposait des sous-zones sans journal** (`generate.py`, mode Semi-guidé) — repéré sur un run réel : `zone_slug invalide : 'archives_neutres_geneve' n'existe pas dans journaux.yaml`, alors que cette zone existe bien dans `geographie/breakdown.md` mais en tant que sous-zone niveau 2 (`journaux.yaml` n'a jamais qu'une entrée par zone niveau 1). Le menu `--zone-slug` (type `zones_hier`, fonction `_scan_zone_slugs_hier()`) listait toutes les zones tous niveaux confondus sans filtrer sur la présence réelle d'un journal, laissant l'échec se produire seulement au lancement (`validate_config_semi_guide()`) plutôt que d'empêcher la sélection en amont. **Corrigé sans casser les usages légitimes de la hiérarchie complète** (`zone_hint` sur `create_entities`/`inject_events`, qui veut délibérément pouvoir cibler une sous-zone précise) : nouveau type `zones_hier_journal` (`app.py`, fonction `_zones_avec_journal(pipeline_dir, scenario)`) qui filtre sur le contenu réel de `journaux.yaml` (union des deux lignes éditoriales) plutôt que de supposer "niveau 1 = a un journal". `--zone-slug` de `generate.py` bascule sur ce nouveau type dans `scripts_config.json` (description mise à jour), `zones_hier` (l'ancien type) reste inchangé pour `zone_hint`. Vérifié par test unitaire local avant livraison (`geneve_bunker_institutions` passe, `archives_neutres_geneve` non) — **non re-testé en conditions réelles après correctif** (David a confirmé "ça marche" mais aucun nouveau run `generate.py` avec sélection de zone n'a été rejoué pour vérifier de bout en bout dans cette session ; confirmé le 12 août via le chantier signature, voir addendum).

**17 clarifications de descriptifs supplémentaires apportées le même soir** à `scripts_config.json` (au-delà des 3 déjà reformulées le matin, voir addendum "clarté des descriptifs" plus bas) : 8 descriptifs principaux (`enrich_minimal`, `zoning_topdown_test`, `reparenter_sous_zones_orphelines`, `scan_geographie_complet`, `audit_dates_instances`, `audit_etat_temporel_fin`, `audit_longueur_articles`, `audit_type_relation_dominante`) + 9 changements au niveau des options (dev-log daté retiré, noms de fichiers bruts retirés, jargon "N1"/"cache"/"additif" clarifié, libellés `undo_custom --type` rendus lisibles). Vérifié par diff programmatique : 14 entrées touchées, aucune autre altérée.

#### Bug GUI corrigé le 12 août 2026 — panneau Revue, slug/scénario/détail vides sur entités et signaux

**Symptôme signalé par David** : le dashboard affiche 1 item en revue, la
notification de l'onglet Revue confirme "1", mais la ligne du tableau
`ENTITES` affiche `(entité)` / `—` / `—` sur les 3 colonnes (SLUG,
SCÉNARIO, DÉTAIL) au lieu du vrai contenu.

**Cause** : `_read_needs_review_yaml()` est un parseur YAML maison,
ligne par ligne, sans PyYAML — construit à l'origine pour le format
`evenements_custom`/`instances_custom` (marqueur d'entrée `- slug:`/
`- idea:`, champs `scenario:`, `date:`, `failed_scenarios:`, `errors:`
en liste). Le correctif du 2 août avait bien ajouté la prise en charge
des sources `entites_custom`/`signaux_custom` (marqueur `- status:`,
jusque-là complètement absentes du panneau) — mais seulement pour les
faire *apparaître*, jamais pour lire leurs propres champs. Leur
structure réelle (`idea.nom`, `idea.scenario_ref`, `reason:` à plat)
diffère du format d'origine et n'était reconnue par aucune des
branches existantes du parseur : `nom:`, `scenario_ref:` et `reason:`
n'étaient simplement pas des clés que le code savait lire, donc le
placeholder posé à la création de l'entrée (`(entité)`/`(signal)`,
scénario/détail vides) n'était jamais remplacé.

**Premier correctif** : trois nouvelles clés reconnues dans
`_read_needs_review_yaml()` — `nom:` (remplace le placeholder de slug,
seulement s'il est encore un placeholder de la forme `(...)`, pour ne
jamais écraser un slug déjà résolu par une autre branche), `scenario_ref:`
(alimente SCÉNARIO si pas déjà rempli), `reason:` (alimente DÉTAIL si
pas déjà rempli, avec déséchappement naïf des quotes simples doublées
YAML — `''mouvement''` → `'mouvement'`). Testé directement contre le
vrai `needs_review.yaml` fourni par David (extraction isolée de la
fonction) : les 3 champs sortent corrects.

**Deuxième correctif, trouvé en vérifiant la couverture des 3 pipelines
(entités/événements/signaux) suite à une question de David** : les 3
scripts d'injection (`create_entities_and_instances.py`,
`inject_custom_events.py`, `inject_custom_signals.py`) ont chacun un
repli générique identique sur exception imprévue —
`outcome = {"status": "needs_review", "idea": idea, "error": str(e)}`,
une clé **scalaire singulière** (`error:`), distincte de `errors:`
(pluriel, liste, seule forme reconnue jusque-là). Une entrée née de ce
chemin (timeout réseau, erreur API...) sur n'importe lequel des 3
pipelines aurait toujours affiché DÉTAIL vide, même après le premier
correctif. Ajouté : reconnaissance de `error:` scalaire, avec le même
déséchappement de quotes que `reason:`, seulement si le champ n'est pas
déjà rempli (pour ne jamais entrer en conflit avec `reason:` sur une
même entrée). Testé avec un cas simulé (`error: 'ConnectionError:
timeout Mistral API'`).

**Confirmé en conditions réelles dans le navigateur** (pas seulement en
isolation) : l'entrée réelle de David ("Les Veilleurs des Nappes
Phréatiques", `category invalide : 'mouvement'`) s'affiche désormais
avec ses 3 colonnes correctement peuplées.

**Ce qui reste `(entité)`/`(signal)` par design, pas un bug résiduel** :
les formats `entites_custom`/`signaux_custom` (contrairement aux
événements) n'ont un champ `nom` lisible que sur les rejets *après*
sélection de catégorie/rôle par le LLM — un rejet plus précoce (ex.
échec réseau avant même la génération du nom) n'aura simplement rien à
lire ici, ce n'est pas un manque du parseur.

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

### Addendum — chantier `trajectoire` et audit longueur articles (9 août 2026)

Trois changements à `scripts_config.json` cette session, tous non
testés en navigateur (`gui_verified: false`) :

- **Entrée `create_entities`, champ `etat`** (mode custom) — renommé
  label "Trajectoire (contrainte dure)", 11 choix (au lieu des 6
  anciennes valeurs `etat_temporel`). Nouveau champ `est_clandestin`
  inséré juste après (select tri-état `oui`/`non`/vide) — voir §3bis
  pour le détail complet du câblage Python.
- **Entrée `audit_etat_temporel_fin`** — label et description corrigés
  (mentionnaient encore `etat_temporel`, disaient le chantier
  `annee_fin` "pas encore construit" alors qu'il est clos depuis cette
  même session — voir §5).
- **Nouvelle entrée `audit_longueur_articles`** — section `validation`,
  même famille que les 3 audits existants (`--dossier` optionnel comme
  seule option). Voir §5 pour le détail du diagnostic.

Vérification structurelle faite après ces trois changements : diff
programmatique confirmant qu'aucune des 26 autres entrées du fichier
n'a été altérée (comparaison champ par champ contre la version
d'avant-session).

### Addendum — clarté des descriptifs et validation navigateur (11 août 2026)

David a commencé à valider le GUI dans un vrai navigateur (backlog
Partie 1, point désormais renommé "Test navigateur des entrées GUI
modifiées") et a signalé, au fil du test, plusieurs descriptifs trop
techniques pour quelqu'un qui ne lit pas le code — trois entrées de
`scripts_config.json` reformulées en conséquence :

- **`fix_annee_debut_placeholder`** — descriptif ramené à l'essentiel,
  jargon interne retiré (`officialise_enrichi`, `ancrage_reel`,
  `annee_debut_verifiee` ne sont plus mentionnés dans le texte affiché).
- **`trace_injection`** — même traitement, plus un correctif de code sur
  la sortie elle-même (le texte produit par le script, pas seulement le
  descriptif du bouton) — voir §2, entrée `trace_injection.py`, pour le
  détail complet.
- **`fix_alliances_oppositions`** — la plus dense des trois : descriptif
  principal + 7 options + 2 libellés de rapports reformulés. Le
  vocabulaire du projet (alliances, oppositions, scénario, fiche) est
  conservé partout — c'est le jargon d'implémentation ("passe LLM",
  chemins de fichiers bruts affichés tels quels comme libellés) qui a
  été retiré ou reformulé.

**Principe appliqué aux trois** : garder le vocabulaire propre au monde
fictif et au projet (variables, scénarios, entités, alliances...), que
David maîtrise déjà et qui structure tout le vault — mais retirer le
vocabulaire d'implémentation interne (noms de fichiers YAML/JSON,
mécanique de pipeline, termes comme "injection"/"aval"/"rétroactif" sans
explication) qui n'apporte rien à quelqu'un qui clique sur un bouton
sans avoir lu le code.

**10 entrées passées à `gui_verified: true`** après clic réel dans le
navigateur par David : les 4 audits (`audit_dates_instances`,
`audit_etat_temporel_fin`, `audit_longueur_articles`,
`audit_type_relation_dominante`), les 2 entrées de veille
(`export_prompt_veille`, `import_veille_etat_monde`), `trace_injection`,
`fix_annee_debut_placeholder`, `fix_alliances_oppositions`, `generate`.
Vérification structurelle faite après coup (diff programmatique) :
exactement ces 10 entrées modifiées, aucune autre altérée. Restent à
`gui_verified: false` (non concernées par cette passe) : `create_entities`,
`enrich_minimal`, `generate_instances` — voir `BACKLOG_MASTER_9_AOUT.md`
Partie 1 pour le suivi.

### Addendum — session du 11 août 2026 (soir) : clôture du test navigateur GUI

Suite directe de l'addendum ci-dessus, même jour, deuxième session
(voir §2 pour `create_entities_and_instances.py` et §7 pour les bugs
`app.js`/`app.py` — détail complet dans les deux sections concernées,
pas répété ici). Résumé de ce qui change côté `scripts_config.json` :
les 3 dernières entrées (`create_entities`, `enrich_minimal`,
`generate_instances`) passent à leur tour à `gui_verified: true` — **les
28 entrées du panneau sidebar le sont désormais toutes**, chantier
"Test navigateur GUI" (ouvert en continu depuis fin juillet) clos pour
de bon. 17 clarifications de descriptifs supplémentaires (8
descriptifs principaux + 9 options), et `--zone-slug` de `generate.py`
basculé sur le nouveau type `zones_hier_journal`. 4 fichiers livrés :
`create_entities_and_instances.py`, `app.js`, `app.py`,
`scripts_config.json`.

### Addendum — session du 12 août 2026 : cohérence événements custom + validation signature

**1. Validation réelle du correctif signature itération 2** (ouvert
depuis le 10 août, voir §2ter point 4) — un run `generate.py` en
Semi-guidé avec une zone valide (`geneve_bunker_institutions`, passant
le filtre `zones_hier_journal` livré le 11 août soir) a confirmé la
signature apparaissant une seule fois, immédiatement sous la date.
Chantier clos.

**2. Diagnostic `annee_debut`/`ancrage_reel` sur les événements**
(question ouverte depuis le 8 août, voir §2ter et backlog) — mené sur
`inject_custom_events.py`, `fix_annee_debut_placeholder.py`,
`loader.py`, et un dépouillement réel de `registre_evenements.md` (53
événements custom). Conclusions : les événements ont une structure de
date différente des instances (champ `date` unique, pas de bande
`annee_debut`/`annee_fin`) ; aucune dérive de concentration observée
(pic max 11% sur une année, contre 22% pour les instances avant
correctif) ; mais **aucun mécanisme d'ancrage réel n'existait avant
cette session**, ni en mode auto ni en mode custom, et
`analyze_vault_coverage()` (couverture auto des événements) n'a — comme
`analyze_entity_coverage()` pour les entités — aucune dimension
temporelle. Décision prise : pas de mécanisme lourd type `ancrage_reel`
des instances (bande graduée + anti-recyclage), un enrichissement de
contexte suffit — voir point 3.

**3. Nouveau chantier — cohérence événements custom / vault, registre,
géographie, état du monde** (`inject_custom_events.py`) — détail complet
en §2, section `inject_custom_events.py`. Résumé : import des fonctions
`load_etat_monde_reel()`/`load_scenario_timeline_summary()` depuis
`instance_generation_common.py` (réutilisation, pas de duplication),
deux nouveaux blocs de contexte dans le prompt de développement
d'événement, validation mécanique de `zone_hint` contre les zones
réelles du scénario (refaite à chaque itération de la boucle scénarios,
initiale et retry). Couvre les deux modes (auto n'écrit que dans
`queue.yaml`, l'injection réelle passe toujours par le mode custom).
Testé en conditions réelles (dry-run, qui appelle le LLM pour de vrai —
voir piège transversal §0) sur 5 cas ciblés, tous concluants, dont un
test croisé (même `zone_hint` sur deux scénarios) prouvant que la
revalidation se refait bien par scénario. **Non testé en injection
réelle (non dry-run)** — chemin d'écriture non modifié par ce
correctif, risque jugé faible.

**Fichier livré** : `inject_custom_events.py`.

**4. Panneau Revue — slug/scénario/détail vides sur entités et signaux**
(`app.py`, fonction `_read_needs_review_yaml()`) — signalé par David sur
une entrée réelle ("Les Veilleurs des Nappes Phréatiques" affichée comme
`(entité)` / `—` / `—`). Voir §7, sous-section dédiée ci-dessous pour le
détail complet (diagnostic, les deux correctifs, tests).

---

### Addendum — session du 14 août 2026 : recherche exhaustive dans
l'archive, fusion de doublon, encodage cassé, filtre acteurs, bug GUI
`--force`

Session dense partie d'une recherche exhaustive dans l'archive complète
des anciens backlogs/handoffs (méthode et trouvailles détaillées dans
`HANDOFF_14_AOUT.md` §0), enchaînée sur le traitement systématique de
tout ce qui a été retrouvé, puis une revue complète de la Partie 2 du
backlog (points mineurs) avec le code source complet disponible pour la
première fois. Résumé des chantiers les plus substantiels ; le détail
complet de chacun (diagnostic pas à pas, tests, fichiers livrés) est
dans `HANDOFF_14_AOUT.md`.

**1. Encodage portugais cassé dans les slugs — cause racine et
migration.** `slugify()` utilisait une table de remplacement d'accents
**français uniquement** au lieu d'une normalisation Unicode générique —
tout caractère accentué non-français (portugais, espagnol...) tombait
dans le `re.sub` générique suivant et devenait `_` au lieu d'être
translittéré. Trois fichiers concernés, tous corrigés :
`create_entities_and_instances.py`, `create_entity.py` (legacy),
`officialize_alliances.py`. Correctif : normalisation Unicode NFD (même
principe que `_fold()`, déjà utilisée dans `gui/app.py`). Nouveau script
`audit_broken_slugs.py` (lecture seule, réutilisable) pour comparer le
slug enregistré de chaque entité au slug que produirait la fonction
corrigée — sur 590 entités auditées, 18 candidats, seulement 2 vrais
cas confirmés (`rede_paulista_de_distribuic_o_algor_tmica`,
`frente_sert_o_livre`), le reste étant des raccourcissements
volontaires de slug (faux positifs) ou un artefact du script lui-même
sur `entite_template.md` (à corriger si le script est réutilisé
souvent — voir backlog Partie 2). Nouveau script `rename_broken_
slugs.py` (réutilisable) pour la migration proprement dite : renommage
de fichier (archétype + toutes ses instances par scénario) et
réécriture de toutes les références externes — contrairement à une
fusion de doublon (voir point 2 ci-dessous), c'est un vrai renommage
d'une même entité. Exécuté sur les 2 cas confirmés : 11 fichiers
renommés, 322 références réécrites dans 141 fiches, `documentation/`
explicitement exclu de la migration (historique, jamais réécrit —
même principe que pour `entites_custom/processed.yaml` au point 2).
`entites/_entities_list.json` mis à jour par remplacement de texte
ciblé, pas de parse/dump JSON complet, pour préserver le formatage
d'origine. `validate.py --verbose` final : 0 erreur.

**2. Doublon d'entité `arctic_passage_authority` /
`autorite_passage_arctique` — fusionné.** Diagnostic confirmé : vrai
doublon généré automatiquement par `extract_phantom_slugs.py` —
`entites_custom/processed.yaml` contient 3 entrées avec des champs
`_slug_fantome_original`/`_slug_corrige` le prouvant. Un slug fantôme
(probablement une référence de zone géographique, `geographie/
breakdown.md` ligne 2278) a été détecté sans entité correspondante et a
généré une entité indépendante, sans savoir qu'`arctic_passage_
authority` existait déjà pour la même institution — les deux instances
`breakdown` partageaient déjà le même jalon de registre et la même
trajectoire de fragmentation en factions (noté le 9 août). Point hors
scope identifié et volontairement non touché : les champs `zone:
autorite_passage_arctique` (dans les deux instances `breakdown` et dans
`event_instances/incident_passage_arctique_breakdown.md`) et l'entrée
`geographie/breakdown.md:2278` sont des références à une **zone
géographique**, pas à l'entité. Nouveau script `fix_arctic_passage_
duplicate.py` (réutilisable) : 17 fiches migrées, 34 références
alliance/opposition réécrites, puis `undo_custom.py --slug
autorite_passage_arctique --type entite --generalisation yes --execute`
(archétype fantôme + instance supprimés, `_entities_list.json`
nettoyé, `last_validated.json` réinitialisé). `validate.py --verbose`
final : 0 erreur.

**3. Wikilinks cassés `test_durcissement_policy_reform` — nettoyés.** 7
fiches `instances/*.md` de `policy_reform` référençaient encore une
fiche supprimée (résidu du 8 août), une ligne bullet identique
(`- [[test_durcissement_policy_reform]]`) dans la section
`## Relations` de chacune — contrairement au doublon Arctic, pas un
renommage mais une suppression pure de référence morte. Nouveau script
`fix_test_durcissement_wikilinks.py` (réutilisable pour tout futur cas
de wikilink mort similaire) : 7 lignes retirées sur 7 fiches.
`validate.py --verbose` final : 0 erreur, 0 avertissement.

**4. `acteurs_hint_count` (P15) — filtre dur enfin appliqué.**
Diagnostic précis dans `inject_custom_events.py` : la valeur était bien
calculée et bornée (`max(1, min(4, ...))`) mais **jamais transmise** à
`step2_develop_instance()` ni utilisée par `validate_instance()` —
calculée puis jetée sans effet, contrairement à `variables_hint_count`
qui a une vraie troncature dure après coup. Nouvelle fonction
`truncate_actors(instance_data, actors_hint, actors_hint_count,
available_actors)`, appliquée à chaque production d'acteurs par le LLM
(essai initial **et** chaque retry) — même schéma exact que la
troncature `variables` déjà en place : les hints imposés par
l'utilisateur sont toujours préservés en premier (via `dict.fromkeys`
pour dédupliquer sans perdre l'ordre), le reste est coupé au plafond.
Testé unitairement (troncature simple, préservation du hint imposé même
hors tête de liste, non-modification si déjà sous le plafond) — les 3
cas passent. **Pas encore confirmé en conditions réelles** — laissé en
validation au fil de l'eau plutôt que de provoquer un test dédié, même
logique que le chantier "retry longueur des articles" du 10 août.

**5. Duplication `detect_registre_leakage()` — consolidée.** La
fonction (documentée en détail au point 12 ci-dessus, chantier
"Diagnostic `annee_debut`/`ancrage_reel`... corrigé le 8 août") existait
en réalité en **double**, avec deux fonctions dépendantes
(`_read_registre_text()`, `_normalize_for_matching()`) elles aussi
dupliquées, entre `instance_generation_common.py` (module partagé) et
`fix_annee_debut_placeholder.py` (copie indépendante, jamais
factorisée). Vérifié avant de corriger : divergence purement cosmétique
entre les deux copies (docstrings différents, un style de code
différent pour `_read_registre_text()` mais fonctionnellement
équivalent, un `flags=re.UNICODE` explicite mais redondant côté
`fix_annee_debut_placeholder.py` puisque Python 3 traite déjà `\w` en
Unicode par défaut) — aucune divergence fonctionnelle actuelle.
`fix_annee_debut_placeholder.py` importe désormais les trois fonctions
depuis `instance_generation_common.py` au lieu de garder ses propres
copies ; variable de cache locale `_registre_cache` devenue inutile,
retirée. Même pattern de duplication qui avait causé de vraies
divergences fonctionnelles avant la factorisation de juillet/août
(~20 fonctions dupliquées à l'époque, plusieurs avaient déjà divergé
silencieusement) — corrigé avant que ça ne se reproduise ici.

**6. GUI — `--force` du panneau localisation ne rafraîchissait pas le
menu — corrigé (trois causes, trois fichiers).** Chantier retrouvé en
Partie 2 du backlog (« contournable via `--scenario` »), diagnostic bien
plus profond que prévu :

- **Cause 1 (`scripts_config.json`)** — le champ `--slug` (type
  `slug_select`, `slug_type: "fiches_a_localiser"`) de l'entrée
  `extract_localisation` n'avait **aucune déclaration
  `slug_extra_params`** reliant son contenu à `--force`. Seul
  `--scenario` déclenchait un rafraîchissement, via le mécanisme
  générique `data-needs-scenario` (tous les `slug_select` y sont
  abonnés par défaut) — `slug_extra_params` (ajouté le 2 août, voir
  §2ter ou section GUI correspondante) est un mécanisme opt-in, jamais
  branché sur ce champ précis. La description du champ documentait
  elle-même le contournement, preuve que le bug était connu et
  contourné depuis un moment. **Corrigé** : ajout de
  `"slug_extra_params": {"force": "--force"}`, description mise à jour
  (contournement retiré du texte, devenu inutile). Vérifié par diff
  programmatique qu'une seule entrée du fichier a été modifiée.
- **Cause 2 (`app.js`, `lireValeurChamp()`)** — même une fois le
  mécanisme câblé, la fonction utilisée pour lire la valeur du champ
  source lisait `el.value` inconditionnellement. Pour une checkbox HTML
  **sans attribut `value` explicite** (le cas ici, vérifié dans le code
  de rendu du champ `--force`), `.value` renvoie toujours la chaîne
  statique `"on"`, quel que soit l'état coché ou non — deux autres
  fonctions du même fichier (`collectArgs()`, `isFlagActive()`)
  géraient déjà ce cas correctement via `.checked`, `lireValeurChamp()`
  était la seule exception. **Corrigé** : test `el.type === 'checkbox'`
  ajouté, renvoie `'true'`/`'false'` selon `el.checked` dans ce cas.
- **Cause 3 (`app.py`, route `/api/slugs`)** — même avec les deux
  points précédents corrigés, `get_slugs()` et
  `_scan_localisation_candidats()` ne lisaient ni ne transmettaient
  **jamais** le paramètre `force` au sous-processus
  `extract_localisation.py --scan-pending` — silencieusement ignoré
  côté serveur même parfaitement envoyé par le frontend. **Corrigé** :
  lecture de `request.args.get("force", "").lower() == "true"`,
  transmis à `_scan_localisation_candidats(..., force=force)`, qui
  ajoute `--force` à la commande du sous-processus si actif. Vérifié
  séparément que `extract_localisation.py --scan-pending` respectait
  déjà correctement `--force` en interne (`collect_fiches(force=args.
  force)`) — aucun correctif nécessaire côté script lui-même.

**Testé et confirmé en conditions réelles par David dans le navigateur**
— panneau "Repérer la localisation des fiches", case "Retraiter même si
déjà fait" cochée, le menu "Une seule fiche" affiche désormais toutes
les fiches (déjà traitées incluses) sans avoir besoin de toucher
`--scenario`.

**7. `forces_attractives`/`forces_repulsives` — escaladé en chantier
substantiel, non résolu.** Voir §3 (audit de complétude snapshot/
variables) pour la mise à jour du constat initial, et
`BACKLOG_MASTER_9_AOUT.md` Partie 1 point 2 pour la portée complète du
chantier restant à faire — décision de conception à prendre par David
(quelle section du corps Markdown des fiches variables fait foi) avant
tout nouveau code dans `loader.py`/`prompt_builder.py`.

**Fichiers livrés cette session** : `inject_custom_events.py` (deux
correctifs cumulés : documentation `zone_hint` + filtre `acteurs_hint_
count`), `create_entities_and_instances.py`, `create_entity.py`,
`officialize_alliances.py`, `fix_annee_debut_placeholder.py`, `app.js`,
`app.py`, `scripts_config.json`, plus 4 nouveaux scripts d'audit/
migration réutilisables : `fix_arctic_passage_duplicate.py`,
`fix_test_durcissement_wikilinks.py`, `audit_broken_slugs.py`,
`rename_broken_slugs.py`. Détail complet, y compris les chantiers
retrouvés via l'archive et non traités (P17, Bug #27, nettoyage des
fichiers de rotation, décision sur "Les Veilleurs des Nappes
Phréatiques") : `HANDOFF_14_AOUT.md`.
