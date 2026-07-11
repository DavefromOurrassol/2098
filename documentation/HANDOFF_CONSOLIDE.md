# Handoff — Ourrassol 2098
*Consolidé le 11 juillet 2026 — vue d'ensemble projet + état des sessions du 4 et du 11 juillet*

---

## 1. Qu'est-ce qu'Ourrassol 2098

Simulateur de presse fictive et système de worldbuilding spéculatif situé en 2098, construit sur un vault Obsidian + un pipeline Python/Flask + API LLM (Mistral, Claude et OpenAI, routés par tier depuis le 11 juillet — voir §3bis). Six scénarios géopolitiques (`breakdown`, `fortress_world`, `new_sustainability`, `eco_communalism`, `policy_reform`, `reference`) partagent un même socle de variables, d'entités et d'événements, mais divergent narrativement.

**Composants principaux :**
- `generator/` — pipeline Python (génération d'articles, entités, événements, géographie, validation)
- `gui/` — interface Flask remplaçant le lancement de scripts en terminal
- Vault Obsidian — source de vérité (fiches `.md` avec frontmatter YAML)
- Repo Git : `DavefromOurrassol/2098`, `.env` gitignored

Voir `USER_MANUAL_COMPLET.md` pour le détail de chaque script, et `BACKLOG_CONSOLIDE.md` pour l'état des chantiers.

---

## 2. Historique du projet (chronologique, résumé)

### Mi-juin 2026 — Construction du pipeline cœur
Écriture de `loader.py`, `snapshot.py`, `prompt_builder.py`, `api.py`, `generate.py`, `generate_series.py`, `generate_manual.py`, `validate.py` (7→9 sections). Modèle archétype/instance pour entités et événements. `llm_client.py` créé pour router Claude/Mistral (13 scripts migrés du SDK Anthropic direct). Système géographique initial : 6 bibles `geographie/{scenario}.md`, zones hiérarchiques N1/N2/N3, `zone_geographique` (7 valeurs dont `orbital`).

### Fin juin 2026 — Couverture géographique + P8 enrichissement
- `complete_geographie_coverage.py` : affectation systématique pays→zone (`--review`/`--apply`).
- `enrich_minimal.py` : enrichissement des 426 fiches `officialise_minimal` (en cours, P8, ~$37 estimé).
- `extract_phantom_slugs.py`, `fix_alliance_suffixes.py`, `requeue_needs_review.py` : outillage autour des slugs fantômes et alliances mal formées.
- Session "25 juin" : fix P2 sur `inject_custom_events.py`, section 9/9 (cohérence narrative) ajoutée à `validate.py`, `undo_custom.py` créé, auto-cycle post-injection ajouté à plusieurs scripts.
- État vault fin de période : 571 entités, 690 instances, 760 fiches riches, 0 erreur, 0 avertissement.

### Fin juin–début juillet 2026 — GUI Flask
Remplacement du lancement terminal par un GUI Flask complet : thème clair, streaming SSE, sidebar piloté par `scripts_config.json`, éditeur YAML avec backups `.bak`, dashboard de stats, panneau de review. Lancement via `start.sh`, alias `ourrassol`, ou `Ourrassol2098.app`.

**Onglet Carte (P1)** livré : 5 routes Flask, frontend Leaflet.js, `pays_mapping.json` (FR→EN), `merge_pays_monde.py` (extension à ~200 pays), palette de couleurs par distribution de teinte uniforme + hachures SVG pour les scénarios à beaucoup de zones. Workflow carte : clic pays → proposition/sélection zone → **évaluation d'impact obligatoire** → confirmation.

### 4 juillet 2026 — Session de débogage intensive (voir §3 ci-dessous)
Neuf bugs identifiés et corrigés sur la carte et `complete_geographie_coverage.py`, dont une corruption YAML affectant potentiellement les 6 scénarios. Un 10e bug (désynchronisation `zones_pays.json`) découvert en creusant après la correction initiale. Couverture géographique des 6 scénarios **confirmée propre** en fin de session.

### 5-6 juillet 2026 — Multi-provider, rate limiting, journalistes
Ajout d'OpenAI comme 3e fournisseur (bug #21), retry centralisé sur 429 (bug #17), fix de fiabilité `mistral-small` sur choix contraints (bug #18) et contamination culturelle inter-zones (bug #20, partiellement corrigé), comblement de la couverture `journaux.yaml` (160 zones), ajout d'une rédaction de 6 journalistes par journal (bug #24).

### 11 juillet 2026 — Routing par tier, bug #26 (cause racine journaliste/journal), P3 clos, gros nettoyage GUI (voir §3bis ci-dessous)
Le doute laissé en suspens le 6 juillet ("la règle 2 [non-transposition culturelle] n'a pas suffi, mistral-small ne respecte pas de façon fiable une contrainte de ce type") a été élucidé : **ce n'était pas un problème de fiabilité modèle**, mais un bug de résolution de zone en amont (bug #26). Requalification des bugs #18/#20 recommandée à la lumière de cette découverte. Session étendue : routing LLM par tier (`llm_client.py`), clôture complète de P3, P13, P6, migration des 2 derniers scripts hors `llm_client.py`, plusieurs bugs GUI corrigés (double-clic, blocages `input()`, override systématique), nettoyage des mentions "Claude" obsolètes sur 18 scripts.

---

## 3. Session du 4 juillet 2026 — détail

**Déclencheur** : légende incohérente sur la carte du scénario `reference` (carte entièrement bleue, légende vide).

### Bugs corrigés
1. **Corruption YAML** dans `geographie/{scenario}.md` — `save_geo_file()` faisait deux `yaml.dump()` séparés puis réindentait manuellement, cassant l'alignement liste/clés. Fix : un seul `yaml.dump(indent=2)`. `reference.md` réparé en urgence via `sed` (60 zones) avant le fix du script.
2. **Prompt LLM incomplet** pour les propositions de zone — le LLM ne voyait jamais la liste des pays déjà affectés à chaque zone. Fix : ajout de cette liste (jusqu'à 10 pays) au prompt de `carte_propose()`.
3. **Modèle sous-dimensionné** — `mistral-small` confabule des erreurs géographiques confiantes. Recommandation (non appliquée dans le code, réglage à faire) : `claude-sonnet-4-6` ou `mistral-large`.
4. **`_build_origine_reelle_index()` fragile** — priorisait le premier slug rencontré dans l'ordre du fichier plutôt que la zone N1. Fix : priorité explicite aux zones N1.
5. **Validation "absorber" trop permissive** — acceptait un slug halluciné coïncidant avec une sous-zone invisible sur la carte. Fix : validation restreinte aux slugs N1 dans `apply_affectations()` et `process_scenario_review()`.
6. **`get_missing_pays()` incomplet** — itérait sur les clés déjà présentes dans `zones_pays.json` au lieu de la `pays_liste` complète. Conséquence : le nombre de pays "manquants" détectés est passé de 36 à 109-114 pour certains scénarios.
7. **Clé API vide** (`Illegal header value b'Bearer '`) — variable d'environnement non chargée dans le terminal courant. Pas un bug de code ; fix utilisateur : `source ~/.zshrc` avant de lancer un script en terminal (le GUI charge `.env` lui-même via `_load_dotenv()`).
8. **Rate limiting (429)** en cours de `--review`. Fix : délai de 8s entre batches dans les deux boucles (mode direct et mode `--review`). *(Retiré le 11 juillet — voir P13, §3bis.)*
9. **Faux rejets sur les groupements de nouvelles zones** — la validation ne connaissait pas les nouvelles zones proposées plus tôt dans le même batch. Fix : suivi des slugs de nouvelles zones au fil du batch, dans les deux fonctions concernées.
10. **Désynchronisation `zones_pays.json` / fiches réelles**, découverte après un `check_zones_coherence.py --all` qui semblait pourtant tout vert — un pays (Arctique) manquant dans le dashboard s'est révélé introuvable dans la fiche. Cause : `zones_pays.json` contenait des valeurs obsolètes pour ~55 pays à travers les 6 scénarios, jamais resynchronisées, invisibles même après le fix #6. Fix en deux parties :
    - `check_zones_coherence.py` amélioré : détecte aussi les pays totalement absents (pas seulement mal classés), avec alias tolérants (`ALIASES`) sans confondre les pays réellement distincts (Guinée ≠ Guinée équatoriale, Congo ≠ RDC, Soudan ≠ Soudan du Sud).
    - Nouveau script `regenerate_zones_pays.py` : reconstruit `zones_pays.json` depuis les fiches (source de vérité). A corrigé 55 désynchronisations en un lancement.

### Fichiers modifiés/créés et déployés
| Fichier | Emplacement | Statut |
|---|---|---|
| `app.py` | `gui/app.py` | ✅ Déployé |
| `complete_geographie_coverage.py` | `generator/` | ✅ Déployé (plusieurs itérations — **vérifier que le fix #9 est bien la version en place**) |
| `check_zones_coherence.py` | `generator/` (nouveau, puis amélioré) | ✅ Créé et mis à jour |
| `regenerate_zones_pays.py` | `generator/` (nouveau) | ✅ Créé |
| `add_pays_to_zone.py` | `generator/` (nouveau) | ✅ Créé — a corrigé les 2 derniers cas résiduels (Arctique, Groenland sur `breakdown`) |

### État final de la couverture géographique — confirmé propre (4 vérifications)
```
breakdown            ✓ 89 zones (36 N1)  — cohérent
fortress_world       ✓ 71 zones (21 N1)  — cohérent
new_sustainability   ✓ 60 zones (15 N1)  — cohérent
eco_communalism      ✓ 87 zones (42 N1)  — cohérent
policy_reform        ✓ 61 zones (15 N1)  — cohérent
reference            ✓ 61 zones (16 N1)  — cohérent
zones_manquantes.yaml ✓ vide
```
Tous les pays de `pays_liste` ont une vraie zone N1 dans les 6 scénarios ; `zones_pays.json` resynchronisé. **Plus rien à reporter sur ce sujet.**

Reste néanmoins : 32 pays présents via une sous-zone narrative mais pas directement affectés à leur bonne granularité N1 (liste détaillée dans `BACKLOG_CONSOLIDE.md`, §P2ter) — distinct des trous corrigés ci-dessus, à traiter via l'onglet Carte (bouton "🚫 Ignorer" ou réaffectation manuelle).

### 11. Mauvais chemin dans `check_session.sh` (check pays mapping)
**Symptôme** : `check pays sauté ([Errno 2] No such file or directory: '.../generator/zones_pays.json')` alors que le script tourne sans erreur par ailleurs.
**Cause** : le check #5 (comparaison `pays_mapping.json` vs `zones_pays.json`) pointait vers `$VAULT_DIR/generator/zones_pays.json`, alors que ce fichier vit dans `gui/` (`$GUI_DIR/zones_pays.json`) — même famille de confusion que le bug récurrent `pipeline_dir`/`vault_root` de `app.py` (§4), cette fois dans le script shell de vérification lui-même. Le check #2 (JSON valide, plus haut dans le même script) utilisait déjà le bon chemin, d'où l'incohérence.
**Fix appliqué** (`sed -i.bak` sur `check_session.sh`) :
```bash
sed -i.bak 's#"\$VAULT_DIR/generator/zones_pays.json"#"$GUI_DIR/zones_pays.json"#' check_session.sh
```
✅ Confirmé en place — les deux occurrences (`static/pays_mapping.json`, `zones_pays.json`) pointent désormais vers `$GUI_DIR`.

### 12. Sélecteur de modèle LLM vide dans le GUI
**Symptôme** : dans le GUI, la case de sélection du modèle LLM existe mais reste vide (aucune option dans le `<select>`).
**Cause** : `refreshModelSelect()` (`app.js`) peuple la liste depuis `llm.available_models_mistral` / `llm.available_models_claude` dans `gui/config.json`. Ces clés n'ont jamais été ajoutées au fichier — seuls `provider`, `model_mistral`, `model_claude` y figuraient. Sans ces tableaux, `models = []` et le `<select>` reste vide, même si la valeur sélectionnée existe bien en config.
**Fix appliqué** : ajout de `available_providers`, `available_models_mistral`, `available_models_claude` dans `gui/config.json`, sans toucher au provider/modèle par défaut actuels.
**Décision associée (remplace la piste envisagée en P2quater)** : le provider et le modèle par défaut **restent `mistral` / `mistral-small`**, malgré la fiabilité géographique moindre notée en bugs #3 et §Points de vigilance. `claude-sonnet-4-6` reste disponible dans le sélecteur pour un choix ponctuel (carte/coverage) mais n'est pas le défaut global. *(Ce sélecteur a été réarchitecturé le 11 juillet en toggle "Forcer ce modèle" — voir §3bis, point 3.)*

**Complément — choix Claude élargi.** Le premier fix ne mettait qu'une seule entrée dans `available_models_claude` (`["claude-sonnet-4-6"]`), donc aucun vrai choix côté Claude malgré le sélecteur peuplé. Modèles Claude actifs vérifiés (juillet 2026) : `claude-sonnet-4-6` (déjà configuré, actif), `claude-sonnet-5` (sorti le 30 juin 2026), `claude-opus-4-8` (le plus capable hors tier Mythos, plus cher), `claude-haiku-4-5-20251001` (rapide/économique). `claude-fable-5` (tier Mythos rendu public) évalué et **volontairement exclu** de la liste — sur-qualité chère ($10/$50 par million de tokens) pour les tâches du pipeline (classification géo, enrichissement narratif), et a connu une interruption de service du 12 au 30 juin 2026 (contrôles export US, rétablie depuis).
Liste retenue dans `gui/config.json` (`llm.available_models_claude`) :
```json
["claude-sonnet-4-6", "claude-sonnet-5", "claude-opus-4-8", "claude-haiku-4-5-20251001"]
```
Défaut inchangé : `claude-sonnet-4-6`.

### 13. `mistral-small` (sans suffixe) — ID de modèle probablement obsolète
**Contexte** : en peuplant le sélecteur de modèle du GUI (bug #12), doute sur la validité de `mistral-small`, valeur par défaut utilisée depuis longtemps dans `gui/config.json` (`llm.model_mistral`) et `generator/llm_client.py` (`_DEFAULT_MODELS["mistral"]`).
**Vérification faite** (`curl https://api.mistral.ai/v1/models` avec la vraie clé du compte) — liste réelle des modèles small/large disponibles sur le compte :
```
magistral-small-2509, magistral-small-latest
mistral-large-2512, mistral-large-latest
mistral-small-2506, mistral-small-2603, mistral-small-latest
voxtral-small-2507, voxtral-small-latest
```
**Constat** : `mistral-small` (sans suffixe) **n'apparaît pas** dans cette liste — seul `mistral-small-latest` (ou une version datée `-2506`/`-2603`) est un ID reconnu aujourd'hui. `mistral-large-latest`, lui, est confirmé valide.
**Hypothèse** : si les générations Mistral fonctionnent depuis longtemps malgré ça, `LLM_MODEL` est probablement positionné ailleurs (variable d'environnement) plutôt que par le défaut du code, ou le SDK tolère un alias legacy côté serveur — non garanti dans la durée.
**Fix recommandé (appliqué depuis)** :
- `gui/config.json` → `llm.model_mistral: "mistral-small-latest"`, `llm.available_models_mistral: ["mistral-small-latest", "mistral-large-latest"]`
- `generator/llm_client.py` → `_DEFAULT_MODELS["mistral"] = "mistral-small-latest"`

### 14. `/api/config` (POST) effaçait les `available_*` à chaque sauvegarde
**Symptôme** : après avoir peuplé `available_models_mistral`/`available_models_claude` (bug #12) et les avoir testés une première fois, le choix de modèle Mistral a disparu (`model_mistral` repassé à `""`) dès qu'un changement de provider/modèle a été fait depuis le GUI.
**Cause** : dans `update_config()` (`app.py`), la boucle générique `for key, value in data.items(): if key in cfg: cfg[key] = value` traite `"llm"` comme une clé normale et **remplace tout `cfg["llm"]`** par `data["llm"]` (qui ne contient que `provider`/`model_mistral`/`model_claude` — le frontend ne connaît jamais les `available_*`). Le calcul de `preserved = {...}` censé sauvegarder les `available_*` avant réécriture arrivait **après** cet écrasement dans le code original — donc lisait un `cfg["llm"]` déjà vidé. La sauvegarde était un no-op silencieux.
**Fix appliqué** : déplacement du calcul de `preserved_llm` avant la boucle générique, dans `update_config()`. Confirmé fonctionnel — le choix de modèle Mistral survit désormais à un changement de provider depuis le GUI.
```python
preserved_llm = {k: v for k, v in cfg.get("llm", {}).items() if k.startswith("available_")}
for key, value in data.items():
    if key in cfg:
        cfg[key] = value
if "llm" in data:
    for k, v in preserved_llm.items():
        cfg["llm"].setdefault(k, v)
```
*(Remplacé le 21 du même mois par une fusion générique des dicts imbriqués — voir bug #21. Devenu inutile aussi le 11 juillet : `run_script()` n'injecte plus `LLM_PROVIDER`/`LLM_MODEL` systématiquement, voir §3bis point 2.)*

### 15. Panneau "Review" et compteur dashboard cherchaient dans le mauvais dossier
**Contexte** : en vérifiant P9 (nettoyage `evenements_custom`), question posée sur le risque pour les entités/instances/signaux custom — a mené à un contrôle de `/api/review`.
**Symptôme** : le panneau Review du GUI et le compteur `review_count` du dashboard ne remontaient jamais rien, même quand du contenu réel existait dans le vault.
**Cause** : `get_review()` (route `/api/review`) et ses 3 fonctions (`_parse_needs_review_enrich`, `_parse_needs_review_events`, `_parse_localisation_review`), ainsi que `_count_review_items()` du dashboard (`routes_dashboard.py`, bug #5), cherchaient toutes dans `pipeline_dir` (= `generator/`). Or les 3 fichiers concernés vivent tous à la racine du vault :
- `instances_custom/needs_review_enrich.yaml` (écrit par `enrich_minimal.py`)
- `evenements_custom/needs_review.yaml` (écrit par `inject_custom_events.py`)
- `documentation/need_action/localisation_review.md` (écrit par `extract_localisation.py`/`review_localisation.py`)
**Fix appliqué** : les 4 fonctions prennent désormais `vault_root` au lieu de `pipeline_dir`. Testé en réel (Flask booté, faux `needs_review.yaml` au format PyYAML exact) : `/api/review` retrouve l'item, `review_count` remonte correctement. Confirmé ensuite sur le vrai vault : fichier événements vide (`needs_review:` sans entrée) → `0` légitime.

### 16. `/api/yaml` (GET/POST/form/append) résolvait tout par rapport à `pipeline_dir` — 9 chemins sur 11 cassés dans `scripts_config.json`
**Découverte** : en poussant la vérification du bug #15 à tous les fichiers `yaml_files` déclarés dans `scripts_config.json`, constat que les 4 routes de lecture/écriture YAML (`get_yaml`, `save_yaml`, `save_yaml_form`, `append_yaml_queue`) résolvaient **toutes** les chemins relatifs par rapport à `pipeline_dir`, avec une sécurité (`target.relative_to(pipeline_dir)`) qui interdisait structurellement d'atteindre les dossiers `entites_custom/`, `evenements_custom/`, `signaux_custom/`, `instances_custom/` — tous à la racine du vault, pas dans `generator/`.
**Ampleur** : 9 des 11 entrées `yaml_files` de `scripts_config.json` étaient affectées (racine fausse, dossier manquant, ou — pour `validate` — nom de fichier entièrement faux : `needs_review.yaml` déclaré alors que `validate.py` écrit `documentation/need_action/narrative_issues.yaml`). Seules `generate` et `generate_series`/`generate_manual` (fichiers réellement dans `generator/`) étaient correctes.
**Hypothèse confirmée pour l'origine du bug #10/P9** : l'entrée `inject_events` (`evenements_custom/queue.yaml`, résolue à tort dans `generator/`) explique probablement le dossier orphelin `generator/evenements_custom/` retrouvé et supprimé en P9 — toute tentative d'ajout via le formulaire GUI y aurait écrit, dans un fichier jamais lu par `inject_custom_events.py`.
**Fix appliqué** :
- `app.py` : les 4 fonctions résolvent désormais par rapport à `vault_root` (qui contient `generator/` un niveau plus bas, donc les chemins déjà corrects n'ont eu besoin que d'un préfixe `generator/`).
- `scripts_config.json` : 9 entrées corrigées —
  | Script | Avant | Après |
  |---|---|---|
  | `enrich_minimal` | `needs_review_enrich.yaml` | `instances_custom/needs_review_enrich.yaml` |
  | `validate` | `needs_review.yaml` | `documentation/need_action/narrative_issues.yaml` |
  | `generate` | `config.yaml` | `generator/config.yaml` |
  | `generate_series` | `config_series.yaml` | `generator/config_series.yaml` |
  | `generate_manual` | `config_series.yaml`, `state/manual_progress.json` | `generator/config_series.yaml`, `generator/state/manual_progress.json` |
  | `create_entities` | `entites_custom/queue.yaml` | inchangé (déjà correct) |
  | `inject_events` | `evenements_custom/queue.yaml` | inchangé (déjà correct) |
  | `inject_signals` | `signaux_custom/queue.yaml` | inchangé (déjà correct) |
  | `extract_phantom_slugs` | `needs_review_enrich.yaml` | `instances_custom/needs_review_enrich.yaml` |
  | `requeue_needs_review` | `needs_review.yaml` | `entites_custom/needs_review.yaml` |
  | `undo_custom` | `undo_queue.yaml` | `evenements_custom/undo_queue.yaml` |
**Testé en réel** : accès `entites_custom/queue.yaml` et `generator/config.yaml` tous deux `200` ; tentative de sortie du vault (`../../../etc/passwd`) toujours bloquée en `403` — la sécurité n'a pas régressé, son périmètre est juste devenu le vault entier plutôt que `generator/` seul.
**Conséquence positive découverte au passage** : `requeue_needs_review` affiche désormais du contenu réel — de vraies créations d'entités custom en échec, invisibles jusqu'ici. Voir P12 du backlog pour le traitement. Les autres cas testés (`undo_custom`, `enrich_minimal`, `extract_phantom_slugs`, `validate`) sont légitimement vides/absents — rien d'anormal, juste des chantiers pas encore relancés (P8 notamment).

### 17. Rate limiting Mistral (429) sur `create_entities_and_instances.py` — fix centralisé dans `llm_client.py`
**Contexte** : en traitant P12 (retraitement des entités custom en échec), rate limit 429 systématique après 1-2 appels — compte Mistral en plan Free (vérifié via la console : **1 RPS / 60 RPM / 500 000 TPM**). Chaque appel du pipeline fait ~28 000 tokens en entrée ; avec 500K TPM, la marge réelle est d'environ 17-18 appels/minute, bien en-deçà de ce qu'un traitement par lot enchaîne naturellement.
**Premier essai (insuffisant)** : ajout d'une pause fixe + retry local dans `create_entities_and_instances.py` uniquement (5s entre idées, retry 3x sur 429). Fonctionnait partiellement mais ne protégeait qu'un seul script, et une pause fixe pénaliserait inutilement un compte à palier plus large (ex. Scale, 2M TPM).
**Fix final retenu** : retry **purement réactif** centralisé dans `llm_client.py` (`call_llm()`), le point d'entrée unique utilisé par les scripts du pipeline (18/18 depuis le 11 juillet — voir §3bis) — aucune pause préventive, seulement une attente croissante (15s/30s/45s) et jusqu'à 4 tentatives automatiques **si et seulement si** l'erreur contient "429". S'adapte automatiquement à n'importe quel palier de compte (Free ou Scale) sans changer une ligne de code. Le fix local dans `create_entities_and_instances.py` a été retiré (redondant).
**Testé** : simulation de 2 échecs 429 puis succès (retry fonctionne, 3 appels réels) ; simulation d'une erreur non-429 (remonte immédiatement, aucun délai inutile). Confirmé en conditions réelles : sur le run suivant, 0 erreur 429/clé API sur 19 tentatives — tous les échecs restants sont de vrais échecs de contenu (voir bug #18).

### 18. `mistral-small` peu fiable sur un choix contraint (`variables_potentielles`)
**Symptôme** : sur un lot de 19 idées retraitées après le fix #17, **18 sur 19** ont échoué avec des `variables_potentielles` invalides — le LLM invente des noms de variables plausibles (`no_man_land_geopolitique`, `territoire_fragmenté_sans_autorite_centrale`...) au lieu de choisir dans la liste réelle.
**Vérifié : ce n'est pas un bug de prompt.** `build_variables_summary()` (`create_entities_and_instances.py`) transmet bien la liste exacte des slugs valides avec leur domaine (`- climat_environnement_global (domain: ...)`) — le référentiel correct est fourni. C'est un problème de fiabilité du modèle sur une tâche à choix fermé, même avec la liste sous les yeux et des instructions explicites — même famille de symptôme que le bug #3 (raisonnement géographique) déjà documenté pour `mistral-small`.
**⚠️ À requalifier (11 juillet)** : ce diagnostic reste globalement valide (revu le 11 juillet sur un test séparé — voir §3bis point 8, même symptôme reproduit sur `mistral-large` cette fois, sur les `variables_potentielles` en mode auto). Mais il ne faut plus le lire comme une explication automatique de tout écart de contrainte observé dans le pipeline — le bug #26 (§3bis point 1) a montré qu'un problème visuellement identique peut en fait être un bug de code en amont, sans lien avec la fiabilité du modèle. Toujours vérifier le code avant de conclure à une limite du LLM.
**Sous-produit utile de ce lot d'échecs** : 7 des 18 se sont aussi révélées être de vrais doublons avec des entités déjà existantes (slugs parfois différents du nom recherché — ex. "Communes Rust Belt" chevauche `federation_des_communs_territoriaux`, pas un slug évident).
**Recommandation appliquée (cohérente avec la décision déjà prise pour la carte, bug #3)** : basculer ponctuellement sur un modèle plus fiable pour ce traitement précis, sans changer le défaut global (`mistral-small-latest` reste le défaut du projet — décision P2quater) :
```bash
export LLM_PROVIDER=claude
export LLM_MODEL=claude-sonnet-4-6
python3 create_entities_and_instances.py
```
Coût négligeable au vu du volume restant (~11 idées).
**Résultat final** : les 11 dernières idées ont toutes réussi avec Claude — `needs_review.yaml` confirmé vide en fin de session. P12 quasi clos (voir backlog).

### 19. `_entities_list.json` (registre anti-doublon) accumulait des doublons — 645 entrées pour 571 slugs uniques
**Découvert** : en investiguant `communes_rust_belt` (finalement déjà correct dans sa fiche `.md` — `needs_review.yaml` était simplement périmé, même famille de désync que les bugs #10/#15/#16), inspection du vrai `_entities_list.json` fourni par David.
**Constat** : `append_to_entities_list()` (`create_entities_and_instances.py`) ajoutait chaque nouvelle entrée par un simple `.append()`, **sans jamais vérifier si le slug existait déjà**. Résultat : 42 slugs dupliqués, dont `rust_belt_communes_libres` en **4 exemplaires** (descriptions différentes à chaque fois) et `nairobi_crrc` en **6 exemplaires**.
**Impact réel, pas que cosmétique** : `build_existing_entities_summary()` affiche la liste **telle quelle** au LLM dans son contexte "entités déjà existantes" — donc pour un slug dupliqué 4 fois, le LLM voyait 4 lignes quasi-identiques mais formulées différemment. Ça gonfle inutilement le prompt (aggrave la pression sur le rate limit, bug #17) et peut brouiller le jugement de doublon du modèle (4 variantes du même concept peuvent lire comme 4 entités distinctes).
**Fix appliqué** : `append_to_entities_list()` fait désormais un **update-or-insert** — retire toute entrée existante du même slug avant d'ajouter la nouvelle, au lieu d'empiler. Testé : un slug déjà dupliqué en base se retrouve ramené à 1 seule entrée (la plus récente) dès qu'il est retouché.
**Nettoyage ponctuel** : fichier `_entities_list.json` dédoublonné une fois (645 → 571, dernière occurrence conservée par slug), livré prêt à remplacer (avec `.bak` recommandé avant écrasement).
**Non corrigé, volontairement** : `create_entity.py` (legacy, superseded) a exactement le même bug dans sa propre copie de `append_to_entities_list()` — pas patché, ce script n'est plus censé être relancé en routine. À garder en tête si jamais il est relancé malgré tout.

### 20. Contamination linguistique/culturelle entre zones alliées — génération d'articles et de journaux
**Contexte** : premier vrai test de P3 (formulaire Generate). Article généré pour la zone Bassin du Congo (`eco_communalism`) entièrement en **portugais**, citant un poème en "traduction Nheengatu" (langue indigène brésilienne réelle), mentionnant Belém et le peuple tupinambá — aucun rapport avec le Congo.
**Cause identifiée** : la fiche géographique du Bassin du Congo a pour allié `amazonie_pacte_viva` (`relations.allies`). Le contexte monde (`build_world_context`, `prompt_builder.py`) inclut des événements globaux du scénario (dont le Traité de Belém, déjà vu en détail dans cette session) indépendamment de la zone traitée — légitime pour la culture générale du journaliste, mais le LLM a confondu "information sur le monde" avec "propriété de ma zone", important des lieux et marqueurs culturels amazoniens dans un article censé se dérouler au Congo. `build_system_prompt()` n'avait aucune règle explicite sur la langue de rédaction ni sur la non-transposition d'éléments d'une entité extérieure.
**Fix appliqué (`prompt_builder.py`)** : deux règles ajoutées aux "règles absolues" du prompt système — (1) rédaction exclusivement en français, noms propres étrangers volontaires exceptés ; (2) un allié/rival/événement extérieur ne fait jamais partie de la zone traitée, ses lieux/langue/marqueurs culturels ne doivent jamais y être transposés sauf interaction explicite.
**Résultat partiel (6 juillet)** : la règle 1 (langue) a fonctionné sur le run suivant — article entièrement en français. La règle 2 (non-transposition) **semblait** ne pas suffire : un nouvel article sur la même zone a quand même mentionné "São Paulo — Fragments Algorithmiques", une entité brésilienne sans rapport.
**⚠️ Requalifié le 11 juillet — cause racine réelle = bug #26, pas (uniquement) une limite du modèle.** En creusant un test de régénération sur cette même zone (Bassin du Congo/`sante`), la cause principale de la contamination observée les 6 et 11 juillet s'est révélée être un bug de code (`zone_slug` mal résolu, voir bug #26 en §3bis) — le journal et le contenu narratif provenaient de deux mécanismes de sélection de zone totalement découplés. Après correction du bug #26, un article régénéré sur exactement la même configuration (Bassin du Congo/`sante`/`mistral-large`) a produit un résultat cohérent : journal "Lokole ya Ebale", journaliste "Aline Moke", contenu entièrement ancré au Congo, mention de l'allié amazonien limitée à une interaction narrative explicite et légitime (délégué venu à une assemblée commune) — conforme à la règle 2 telle qu'écrite. **Il n'est donc plus certain que la règle 2 ait jamais réellement échoué** ; les deux runs cités comme preuve d'échec (6 et 11 juillet, avant fix) souffraient très probablement du bug #26 sous-jacent. Un test plus poussé sur `mistral-small` avec le pipeline corrigé reste à faire pour confirmer si un vrai problème de fiabilité modèle subsiste une fois la cause de code éliminée (voir backlog, item de suivi).
**Découverte associée, cause distincte, non remise en cause par ce qui précède** : le nom du journal lui-même ("Yaripã: A Voz da Floresta", identique sur 2 articles générés à des moments différents) n'est pas régénéré par le LLM à chaque article — il est stocké une fois dans `generator/journaux.yaml` par `generate_journaux.py` et réutilisé tel quel. Ce nom est en réalité celui de la zone **`amazonie_pacte_viva`** dans `journaux.yaml` (confirmé le 11 juillet) — donc les deux runs cités ici avaient bel et bien résolu `zone_slug` vers la mauvaise zone (Amazonie au lieu du Congo), exactement le mécanisme du bug #26.
**Fix appliqué (`generate_journaux.py`, 6 juillet, toujours valide)** : prompt réécrit — ancrage explicite sur la description/statut/tensions de la zone elle-même (jamais une zone alliée), rédaction en français pour tous les champs, `langue_style` réservé aux cas où la description de la zone le justifie explicitement (héritage colonial/migratoire documenté), exemple biaisé retiré.
**Effet de bord noté, non traité** : incohérence numérique interne détectée dans un article (titre "cent vingt-six saisons" vs corps "quatre-vingt-dixième hiver") — défaut d'attention du modèle sur un détail chiffré, sans lien avec la contamination linguistique ni le bug #26. Aucun mécanisme du pipeline (`validate.py` inclus) ne vérifie la cohérence interne du texte libre d'un article généré — seulement les instances/événements structurés.

### 21. Sélecteur de modèle GUI et sauvegarde config codés en dur pour 2 providers seulement — cassé à l'ajout d'OpenAI
**Contexte** : ajout d'OpenAI comme 3e fournisseur LLM (`llm_client.py`, sur le même schéma que Mistral/Claude — nouvelle fonction `_call_openai`, modèle par défaut `gpt-5.5`, bénéficie automatiquement du retry centralisé du bug #17 sans code supplémentaire). Une fois ajouté au sélecteur GUI, le choix "openai" affichait quand même les modèles Claude.
**Cause** : `refreshModelSelect()` et `saveLLM()` (`static/app.js`) avaient un `if (provider === 'mistral') ... else ...` codé en dur — tout provider qui n'est pas explicitement "mistral" retombe sur la branche Claude par défaut.
**Fix appliqué** : les deux fonctions construisent désormais les clés dynamiquement (`available_models_${provider}`, `model_${provider}`) — fonctionne pour n'importe quel provider ajouté à `available_providers`, sans code spécifique à écrire à chaque nouveau fournisseur.
**Effet de bord découvert et corrigé en même temps** : l'ancien `saveLLM()` envoyait systématiquement `model_mistral` ET `model_claude` ensemble à chaque sauvegarde — un contournement (non documenté) du fait que `update_config()` (`app.py`) remplaçait tout le dict `llm` au lieu de le fusionner. En rendant `saveLLM()` générique (n'envoie que le provider actif), ce contournement disparaît et aurait fait perdre `model_mistral`/`model_claude` à chaque changement de provider. **Fix remplacé à la racine** : `update_config()` fait maintenant une vraie fusion des dicts imbriqués (`cfg[key].update(value)` si les deux côtés sont des dict) au lieu d'un remplacement complet — ce qui rend obsolète et remplace le fix ciblé du bug #14 (qui ne protégeait que les clés `available_*`).
**Testé** : POST `{llm: {provider: "openai", model_openai: "gpt-5.5"}}` sur une config avec `model_mistral`/`model_claude`/`available_*` déjà présents → tous préservés, `model_openai` ajouté, `provider` mis à jour. Confirmé aussi côté OpenAI : retry sur 429 fonctionne via le mécanisme centralisé, sans code dédié.

### 22. Deux paramètres OpenAI incompatibles avec GPT-5.x, découverts en conditions réelles + piège du fallback silencieux
**Contexte** : chantier de comblement de la couverture `journaux.yaml` (160 zones N1 sans journal sur les 6 scénarios, 0 orphelin — trou de couverture jamais comblé depuis la génération initiale fin juin, sans lien avec une corruption). Lancé avec `generate_journaux.py --all --update` sous OpenAI/GPT-5.5.
**Bug 1 — `max_tokens` rejeté** : `Error code: 400 — Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.` GPT-5.x exige `max_completion_tokens`. Fix appliqué dans `_call_openai()` (`llm_client.py`).
**Bug 2 — `temperature` personnalisée rejetée** : une fois le bug 1 corrigé, nouvel échec — `Unsupported value: 'temperature' does not support 0.7 with this model. Only the default (1) value is supported.` GPT-5.x n'accepte que sa température par défaut (1), aucune valeur explicite. Fix : `temperature` n'est plus transmis du tout par `_call_openai()`, laissant l'API appliquer son défaut — indépendant de ce que l'appelant demande. Explique pourquoi le tout premier test OpenAI (génération d'article via `generate.py`/`api.py`, `TEMPERATURE = 1.0` en dur) avait fonctionné du premier coup par pure coïncidence, alors que `generate_journaux.py` (`temperature=0.7` en dur) échouait systématiquement.
**Piège découvert en cours de route, à connaître pour la suite** : `generate_journals_for_zones()` (`generate_journaux.py`) a un fallback silencieux sur tout échec de lot — il écrit quand même une entrée par zone (`"nom": "Édition {zone}"`, `ton`/`langue_style` vides) plutôt que de laisser la zone manquante. Conséquence concrète vécue deux fois cette session : les 32 lots ont échoué (clé API manquante d'abord, puis les 2 bugs ci-dessus), et **journaux.yaml s'est retrouvé avec 160 entrées placeholder vides** qu'un `--update` ultérieur ne retente jamais (la zone n'est plus "manquante" à ses yeux, juste vide). Un script ponctuel (`clean_fallback_journaux.py`, livré dans cette session, signature : `nom` commence par "Édition " + `ton`/`langue_style` vides) a dû être relancé deux fois entre les tentatives pour purger ces placeholders avant de pouvoir réessayer proprement.
**Résultat final** : les 160 zones comblées en un seul run réussi (32/32 lots), confirmé par `check_journaux_coherence.py` (0 manquant, 0 orphelin sur les 6 scénarios). Coût réel mesuré : ~58 000 tokens, ≈ $0,92.
**Non traité, à garder en tête** : le fallback silencieux de `generate_journaux.py` n'écrit aucun avertissement distinctif dans `journaux.yaml` lui-même (pas de marqueur genre `_fallback: true`) — seul le log terminal signale l'échec au moment du run. Si ce log n'est pas conservé, rien ne permet de redistinguer plus tard un "Édition X" fallback d'un vrai profil pauvre généré par le LLM. À améliorer un jour si ça pose problème (ajouter un marqueur explicite plutôt que de compter sur le pattern de nom).

### 23. P3 test 2 (Generate series) — sauvegarde "muette" causée par Flask non redémarré, pas un bug de code
**Contexte** : test end-to-end du formulaire Generate series (6 juillet). Sélection `policy_reform` / `politique`+`société` / `breve`, clic Sauvegarder → message vert "✓ Sauvegardé", mais `config_series.yaml` restait identique aux valeurs par défaut du projet, et le run suivant a utilisé ces valeurs par défaut (`breakdown`, 6 thématiques, `auto`) au lieu du choix réel.
**Diagnostic mené, tout innocenté un par un** : payload réseau du navigateur correct (`path` et `fields` conformes) ; `_update_yaml_fields()`/`_replace_yaml_key()` rejoué à l'identique en isolation sur le vrai fichier → fonctionne parfaitement ; `app.py` déployé confirmé identique (diff) à la dernière version corrigée ; aucun fichier `config_series.yaml` égaré ailleurs dans le vault ; test end-to-end de la vraie route Flask avec le vrai payload → fonctionne parfaitement aussi.
**Cause réelle** : Flask tournait encore avec l'ancienne version d'`app.py` en mémoire — remplacer le fichier sur disque ne suffit pas, `app.py` n'est chargé qu'au démarrage du process (contrairement aux scripts `generator/`, relus à chaque lancement). Un redémarrage complet (`kill` + relance) a résolu le problème immédiatement, confirmé par relecture du fichier après un nouvel essai.
**Aucun fix de code nécessaire** — c'est un rappel opérationnel, pas un bug : **après tout remplacement d'`app.py`, toujours redémarrer Flask avant de tester**, même si le fichier semble correct sur disque.
**P3 test 2 validé après ce correctif** : série de 2 articles générée avec succès (`policy_reform`/`politique`+`societe`/`breve`, 0 erreur). Avertissements `[WARN][journal] Pas d'édition locale pour zone 'X'` observés pour des lieux précis (sous-zones, pas des zones N1) — comportement de repli attendu, pas une anomalie.

### 24. Nouvelle fonctionnalité : rédaction de journalistes par thématique — troncature JSON à corriger en cours de route
**Fonctionnalité ajoutée (6 juillet)**, à la demande de David : chaque journal (`journaux.yaml`) porte désormais une rédaction de **6 journalistes**, chacun couvrant une ou plusieurs des 20 thématiques du projet (toutes couvertes collectivement). `generate_journaux.py` génère ce champ `journalistes: [{nom, thematiques}, ...]` en même temps que `nom`/`ton`/`langue_style` (même appel LLM, ne peut pas se désynchroniser). `prompt_builder.py` sélectionne automatiquement le bon journaliste selon la thématique de l'article en cours (`thematique["slug"]`, transmis depuis `build_prompt()`), avec repli sur le premier de la liste si aucun ne correspond exactement, et silence complet (pas de signature) si la rédaction est vide — testé sur les 4 cas de figure sans erreur.
**Nouveau mode `--fill-journalistes`** : complète uniquement le champ `journalistes` des zones déjà présentes qui ne l'ont pas encore, sans jamais toucher à `nom`/`ton`/`langue_style` — permet de rattraper les 290 entrées créées avant l'ajout du champ sans tout régénérer.
**Bug rencontré au premier lancement (OpenAI/GPT-5.5)** : tous les lots de 5 zones échouaient avec `Expecting value: line 1 column 1 (char 0)` — le JSON était tronqué, chaque lot atteignant exactement le plafond `max_tokens=2000` configuré. La rédaction de 6 journalistes par zone alourdit beaucoup la sortie JSON attendue par rapport à l'ancien champ à un seul nom.
**Fix appliqué** : `max_tokens` 2000 → 8000, taille de lot 5 → 3 zones (marge de sécurité supplémentaire, des lots de seulement 1-2 zones étant déjà montés à ~1900 tokens).
**Résultat, confirmé** : 96 lots sur 96 réussis après le fix, aucun `[WARN]`. Contrairement au piège du bug #22, le fallback de `process_scenario_fill_journalistes()` ne touche qu'au champ `journalistes` sur l'entrée existante — un échec de lot laisse juste `journalistes: []` (retenté automatiquement au prochain `--fill-journalistes`), sans jamais corrompre `nom`/`ton`/`langue_style` déjà corrects. Aucun nettoyage de placeholder nécessaire cette fois, contrairement au 5 juillet.
**Coût réel mesuré** : ≈ 292 000 tokens (110k entrée + 182k sortie), ≈ $6 — plus cher que le premier passage (~$0,92, un seul nom par zone) mais cohérent avec le volume de contenu supplémentaire (rédaction complète au lieu d'un nom).
**Suite donnée le 11 juillet** : voir bug #26 ci-dessous — la vérification prévue ("regénérer un article sur Bassin du Congo/`sante` pour confirmer signature + thématique") a révélé un bug de code sans lien avec cette fonctionnalité elle-même, qui fonctionne correctement une fois `zone_slug` bien résolu en amont.

---

## 3bis. Session du 11 juillet 2026 — détail

**Déclencheurs successifs** : (1) vérification prévue de la fonctionnalité journaliste (bug #24) ; (2) demande de routing LLM par tier pour arbitrer coût/fiabilité par type de tâche ; (3) série de tests GUI end-to-end pour clore P3.

### 25. Nouvelle fonctionnalité — routing LLM par tier (`llm_client.py`)
**Demande initiale** : pouvoir affecter des modèles différents selon le type de tâche (identité imposée, sortie structurée canonique, contenu créatif libre, volume/extraction), sans dupliquer la logique de sélection de provider à chaque script.
**Implémentation** : `TASK_TIER_DEFAULTS` (dict `{tier: {provider, model}}`) + `resolve_for_tier(task_tier)` dans `llm_client.py`. `call_llm(..., task_tier=...)` reste rétrocompatible (comportement du tier `volume` si omis). Priorité absolue conservée pour l'override manuel (`LLM_PROVIDER`/`LLM_MODEL` positionnés explicitement en variable d'environnement) — permet toujours un test ponctuel sans toucher au tier system.
**4 tiers définis** :
| Tier | Modèle par défaut (11 juillet) | Exemples de scripts |
|---|---|---|
| `strict` | `mistral-large-latest` *(→ `claude-sonnet-5` prévu au passage en prod, une ligne à changer)* | `api.py` (rédaction d'articles), `generate_journaux.py` |
| `structured_strict` | `mistral-large-latest` | `create_entity.py`, `generate_entities.py`, `generate_instances.py`, `create_entities_and_instances.py`, `inject_custom_events.py`, `inject_custom_signals.py`, `build_geographie_monde.py`, `enrich_geographie_recursive.py`, `complete_geographie_coverage.py`, `fix_impact_scale.py`, `officialize_alliances.py` |
| `creative_souple` | `mistral-large-latest` | `enrich_minimal.py` (appel principal) |
| `volume` | `mistral-small-latest` | `extract_localisation.py`, `review_localisation.py`, `extract_phantom_slugs.py`, `enrich_minimal.py` (sous-tâche L.918) |
**18 points d'appel migrés au total** sur la session (15 dans un premier temps, puis `complete_geographie_coverage.py`, `fix_impact_scale.py`, `officialize_alliances.py` — voir points 4 et 9 ci-dessous). Reste hors système : `restructure_zones.py` (n'existe pas encore sur disque, P7).

### 26. Bug racine du problème journaliste/journal incohérent — `zone_slug` invalide + priorité inversée dans `prompt_builder.py`
**Point de départ** : vérification prévue du bug #24 — régénération d'un article Bassin du Congo/`sante` pour confirmer la signature. Résultat : journal et journaliste **toujours incohérents** (byline "Yaripã — A Voz da Floresta", signature absente ou "Yara Tikuna"), reproduit à l'identique sur `mistral-small` **et** `mistral-large` — signal fort que ce n'était pas un problème de fiabilité modèle (les deux runs ont produit exactement le même résultat "faux" de façon déterministe).
**Investigation** : `nom: "Yaripã: A Voz da Floresta"` s'est révélé être le vrai nom de journal de la zone **`amazonie_pacte_viva`** (alliée du Congo) dans `journaux.yaml` — pas une invention du modèle. Le modèle avait *correctement* suivi les instructions ; c'est l'instruction elle-même qui pointait vers la mauvaise zone.
**Cause racine, en deux parties** :
1. `config.yaml` contenait `zone_slug: bassin_congo_ressources` — un slug **inexistant** (le vrai est `congo_bassin_du_fleuve`, un parmi 42 zones pour `eco_communalism`/`pro_pouvoir`). `generate.py::validate_config()` ne vérifiait alors ni l'existence ni la validité de `zone_slug`.
2. Même en corrigeant ce slug, `prompt_builder.py` (L.1405) calculait `zone_slug = snapshot.get('zone_slug') or config.get('zone_slug')` — la zone **auto-calculée** par `_dominant_zone()` (vote majoritaire sur les instances filtrées par pertinence thématique **scénario-wide**, sans lien avec la géographie voulue) prenait systématiquement le pas sur le choix explicite de `config.yaml`, dès qu'elle retournait une valeur non-vide (quasi toujours le cas).
**Fix appliqué (3 parties)** :
- `config.yaml` : `zone_slug` corrigé → `congo_bassin_du_fleuve`.
- `prompt_builder.py` : priorité inversée → `zone_slug = config.get('zone_slug') or snapshot.get('zone_slug')` — un choix humain explicite prime désormais sur l'heuristique automatique, qui ne sert plus que de repli.
- `generate.py::validate_config()` : vérifie désormais que `zone_slug` (si fourni) existe bien dans `journaux.yaml` pour le scénario/ligne éditoriale concernés, avec une erreur claire listant les zones valides sinon — ce type de typo ne peut plus passer inaperçu.
**Test de confirmation réussi** : article régénéré sur la même configuration (Bassin du Congo/`sante`/`mistral-large`) → journal "Lokole ya Ebale", journaliste "Aline Moke", contenu entièrement cohérent avec le Congo, mention de l'allié amazonien limitée à une interaction narrative explicite et légitime (voir aussi bug #27 ci-dessous pour un défaut narratif mineur relevé sur ce même run).
**Conséquence sur les bugs #18/#20 du 4-6 juillet** : à requalifier, voir notes ajoutées directement dans ces entrées plus haut (§3). Ce n'est pas une infirmation totale — le bug #18 (variables_potentielles) s'est effectivement reproduit à l'identique le 11 juillet sur un cas sans lien avec le zone_slug (voir point 8 ci-dessous) — mais un signal clair qu'il faut toujours exclure un bug de code avant de conclure à une limite de fiabilité du modèle.

### 27. Incohérence de plausibilité logistique — mineure, en observation
**Contexte** : détecté sur l'article de confirmation du bug #26 (Bassin du Congo/`sante`).
**Symptôme** : un délégué du Pacte Amazônia Viva (zone alliée située en Amazonie, donc un autre continent) est décrit comme "venu en pirogue depuis Kisangani" — un trajet purement local au bassin du Congo, sans mention de la traversée intercontinentale attendue pour un personnage censé venir d'ailleurs.
**Distinct du bug #26** : pas une erreur de résolution de zone (le zone_slug est correct sur ce run) — une décision narrative du modèle au moment de l'écriture. La consigne existante sur la non-contamination culturelle (`prompt_builder.py`, règle 2 du bug #20) est respectée à la lettre : l'interaction avec l'allié est explicite (assemblée de bassin), donc la mention elle-même est légitime — mais la consigne ne couvre pas la plausibilité du trajet/moyen de transport d'un personnage distant.
**Décision prise** : ne pas modifier `build_system_prompt()` dans l'immédiat — observer si ce type d'incohérence se reproduit sur d'autres tests avant d'ajouter une consigne dédiée à la cohérence géographique des déplacements inter-zones. À ajouter au backlog comme point de suivi.

### 28. GUI — `run_script()` forçait systématiquement `LLM_PROVIDER`/`LLM_MODEL`, neutralisant le routing par tier
**Découvert** : test de génération depuis le GUI juste après la mise en place du routing par tier (point 25) — log affichant `mistral-small-latest` malgré un tier `strict` résolu en interne vers `mistral-large-latest`.
**Cause** : `run_script()` (`app.py`) injectait inconditionnellement `LLM_PROVIDER`/`LLM_MODEL` dans l'environnement de **chaque** script lancé depuis le GUI, à partir de `gui/config.json` (`llm.provider`/`llm.model_mistral`) — indépendamment du fait que cette valeur ait été choisie exprès pour ce run ou qu'elle traîne juste comme défaut. Comme l'override manuel a toujours priorité absolue sur le tier (par design, voir point 25), ça neutralisait le routing pour absolument tout ce qui passe par le GUI, en permanence.
**Fix appliqué** : override seulement si `force_llm_override: true` est explicitement présent dans le body `POST /api/run`. Par défaut (absent), aucune variable n'est injectée — le tier system s'applique normalement.
**Complément GUI (frontend)** : nouveau toggle **"Forcer ce modèle"** dans la sidebar, sous le sélecteur LLM — voir point 3 ci-dessous pour le détail.

### 29. Toggle GUI "Forcer ce modèle" — version sticky avec bandeau d'alerte
**Itération 1** : case à cocher simple, se redécochait automatiquement après chaque run consommé — sûr par défaut, mais pénible pour enchaîner plusieurs runs forcés (recocher à chaque fois).
**Itération 2 (retenue)**, à la demande de David : le toggle reste actif jusqu'à ce que l'utilisateur le décoche lui-même ("sticky"). En contrepartie, un **bandeau d'alerte permanent orange** (`#llm-force-banner`) apparaît en haut de la zone principale, visible sur tous les onglets tant que le forçage est actif, affichant le fournisseur/modèle forcé en clair + un bouton "Désactiver" intégré.
État jamais persisté (ni `localStorage`, ni `config.json`) — décision de session, remise à zéro à chaque rechargement de page, cohérent avec le principe déjà appliqué pour `LLM_PROVIDER`/`LLM_MODEL` en CLI (override ponctuel, jamais une valeur permanente dans `.zshrc`).
Carte dashboard renommée **"LLM actif" → "Modèle si forcé"** — l'ancien libellé prétendait à un seul modèle actif en permanence, ce qui n'est plus vrai par défaut depuis le routing par tier. *(Non vérifié : cohérence de `routes_dashboard.py` avec ce renommage — fichier non fourni pendant la session, voir backlog.)*

### 30. Scripts multi-modes bloqués sur `input()` en lancement GUI (`create_entities_and_instances.py`, `inject_custom_events.py`)
**Symptôme** : lancement depuis le GUI en mode `custom` → `unrecognized arguments: custom` (argparse). Cause plus profonde derrière l'erreur immédiate : même en corrigeant l'argument, ces deux scripts demandaient leur mode (`custom`/`auto`/`auto-suggest`) via un `input()` interactif — incompatible avec `subprocess.Popen()` (`app.py`) qui ne connecte aucun stdin, provoquant un blocage silencieux garanti.
**Fix appliqué** : `--mode` ajouté à l'argparse des deux scripts (fallback `input()` conservé si `--mode` omis, pour l'usage CLI direct sans rien casser). `app.js::collectArgs()` corrigé en parallèle : le `mode_select` envoyait la valeur brute (`"custom"`) sans flag ; il envoie désormais `["--mode", valeur]`.
**Poussé plus loin en cours de session** : les modes `auto`/`auto-suggest` de ces deux scripts avaient chacun 2 `input()` supplémentaires non couverts (nombre d'entités/idées, catégorie ou scénario ciblé) — même blocage, corrigés de la même façon (`--n`, `--category`, `--scenario` ajoutés à l'argparse des deux scripts, avec des valeurs par défaut sûres côté GUI pour `--n` afin qu'il soit toujours transmis).
**Nouvelle fonctionnalité au passage** : `--scenario` du mode `auto` de `create_entities_and_instances.py` accepte désormais **plusieurs** scénarios (`nargs='+'`, ex. `--scenario eco_communalism breakdown`) — contrainte dure garantie par prompt + filtre en sortie, sémantique alignée sur `scenario_hint` du mode custom. Le GUI expose ça via un nouveau type de champ générique `multi_select` (chips cliquables), ajouté à `renderOption()`/`collectArgs()` dans `app.js`, réutilisable pour tout futur besoin de multi-sélection en dehors des `config_fields` YAML.

### 31. Vérification systématique `scripts_config.json` vs code Python réel (P6, clos)
**Méthode** : croisement automatisé des `flag` déclarés côté GUI avec les `add_argument()` réels de chaque script correspondant, sur les 19 entrées de `scripts_config.json`.
**Résultats** :
- 2 flags fantômes trouvés et supprimés : `--scenario` sur `create_entities` et sur `inject_events`, jamais lus par les scripts correspondants (auraient provoqué un `unrecognized arguments` au premier usage). *(Note : `--scenario` a été réintroduit ensuite avec un vrai rôle sur `create_entities` — voir point 4.)*
- `zone_hint` (`create_entities`, `inject_events`) confirmé **fonctionnel** malgré son absence de documentation dans `QUEUE_TEMPLATE` des deux scripts — ancrage géographique explicite injecté dans le prompt de génération d'instance, résolu dynamiquement depuis le vault (`zones_hier`), pas de risque de typo comme `zone_slug` (bug #26) puisqu'il n'y a pas de saisie manuelle libre.
- Tous les `config_fields` (formulaires `queue.yaml`) vérifiés lus correctement sur `create_entities`, `inject_events`, `inject_signals`, `generate`, `generate_series`.
- `restructure_zones.py` confirmé absent du disque (attendu, P7 non codé).
- Faux positif écarté : `generate.py --dry-run` est géré via `sys.argv` brut plutôt qu'`argparse` — fonctionne malgré tout, juste invisible à une détection basée sur `add_argument()`.

### 32. Bug de code — reliquat `resp.stop_reason`/`resp.usage` d'avant la migration `llm_client.py`
**Découvert** : `NameError: name 'resp' is not defined` sur un run réel (`create_entities_and_instances.py`, mode auto).
**Cause** : `call_claude_json()` (dans `create_entities_and_instances.py` **et** `build_geographie_monde.py`) référençait encore un objet `resp` (réponse brute du SDK Anthropic, avec `.stop_reason`/`.usage.output_tokens`) dans ses deux chemins d'erreur les plus rares (réponse vide, JSON introuvable après tous les filets de sécurité) — reliquat du code d'avant la migration vers `llm_client.py`, qui ne retourne qu'une chaîne de texte. Invisible depuis la migration car ces chemins d'erreur n'avaient jamais été déclenchés jusqu'à ce jour.
**Fix appliqué (les deux fichiers)** : remplacement par une heuristique de longueur (`len(text) >= max_tokens * 3`, ~3-4 caractères/token en français) pour détecter une troncature probable, faute de pouvoir encore lire le `stop_reason` réel.
**Même correctif appliqué préventivement** en migrant `fix_impact_scale.py` et `officialize_alliances.py` (voir point 9) — ils avaient le même reliquat, jamais déclenché non plus.

### 33. Bouton GUI "Ajouter à la queue" — pas de garde-fou anti double-clic
**Symptôme rapporté** : "je demande une entité mais le Flask en crée 2".
**Cause** : `POST /api/yaml/append` n'était protégé par aucun état "en cours" — un double-clic (accidentel, ou réseau un peu lent) envoyait deux requêtes qui ajoutaient chacune la même entrée à `queue.yaml`, avant que la première réponse ne réinitialise le formulaire.
**Fix appliqué (`app.js`)** : le bouton est désormais désactivé dès le clic (`btnSave.disabled = true`), réactivé dans un bloc `finally` une fois la requête terminée (succès ou échec) — un second clic pendant l'envoi est simplement ignoré.

### 34. `variables_hint_count`/`--n` — consignes de prompt non appliquées en filtre dur (2 occurrences, même famille que le bug #26)
**Occurrence 1 — `create_entities_and_instances.py`, mode auto** : demandé `--n 1`, reçu 5 entités ; les 5 rejetées en cascade car chacune proposait des `variables_potentielles` entièrement inventées plutôt que puisées dans `VALID_VARS` (reproduction du bug #18, cette fois sur `mistral-large`). Fix : prompt renforcé (interdiction explicite d'inventer un slug, répétition du nombre exact demandé) + troncature dure du nombre d'entités en sortie (`entities[:n]`) si le LLM en renvoie plus que demandé.
**Occurrence 2 — `inject_custom_events.py`, `variables_hint_count`** : plafond par défaut de 2 documenté et présent dans le prompt ("choisis entre 1 et {max_vars}"), mais jamais vérifié après réception — un test réel a renvoyé 4 variables au lieu de 2. Fix : troncature dure en sortie, en préservant en priorité les variables explicitement imposées par l'utilisateur (`variables_hint`) avant de compléter avec les choix du LLM jusqu'au plafond.
**Point similaire noté mais non corrigé (mineur)** : `acteurs_hint_count` (même script) n'est pas non plus appliqué en filtre dur sur le *nombre* d'acteurs — mais la validation qualitative des slugs d'acteurs proposés fonctionne bien (testé OK, aucun acteur invalide accepté). Risque jugé moindre qu'un dépassement de plafond puisqu'un acteur en texte libre est explicitement toléré par le schéma, contrairement à une variable qui doit être un slug exact.

### 35. Migration complète des 2 derniers scripts hors `llm_client.py` — `fix_impact_scale.py`, `officialize_alliances.py`
**Constat** : ces deux scripts (tous deux classés "one-shot" dans `USER_MANUAL_COMPLET.md`, mais toujours potentiellement relançables) étaient les 2 seuls du pipeline encore câblés en dur sur le SDK Anthropic direct (`claude-sonnet-4-6`, `ANTHROPIC_API_KEY` obligatoire), donc hors routing par tier et hors retry centralisé (bug #17).
**Migration effectuée** : tier `structured_strict` pour les deux (champs canoniques référencés ailleurs — matrice d'influence pour l'un, noms d'entités dédupliqués pour l'autre). Même correctif que le point 8 appliqué en migrant (reliquat `resp` retiré).
**Conséquence** : les 18 scripts du pipeline utilisant un LLM sont désormais tous unifiés sous `llm_client.py`. Seul `restructure_zones.py` reste hors système, mais uniquement parce qu'il n'existe pas encore sur disque (P7).

### 36. Nettoyage des mentions "Claude" obsolètes dans les docstrings/logs (18 scripts)
**Déclencheur** : contradiction repérée par David dans un log collé — `review_localisation.py --auto-resolve` affichait *"résolution automatique par Claude"* juste au-dessus d'un appel `[llm] Mistral (mistral-small-latest)...`.
**Balayage systématique** effectué sur les 18 scripts migrés vers `llm_client.py` : toutes les mentions "Claude" dans les docstrings, `print()`, textes d'aide `--help` remplacées par "le LLM"/"au LLM" (accord grammatical fait à la main, pas un remplacement automatique naïf).
**2 exceptions volontaires, non touchées** : `llm_client.py` (mentions légitimes, config réelle du fournisseur) et `generate_manual.py` (workflow "SANS API" — copier-coller manuel dans le chat Claude.ai, "Claude" y est exact et intentionnel, pas un reliquat).
**Vérifié** : tous les fichiers compilent, `grep -ln "Claude" *.py` ne remonte plus que ces deux exceptions.

### 37. Notes contextuelles par mode dans le GUI (UX)
**Contexte** : confusion possible entre les modes `auto` (injecte directement dans le vault) et `auto-suggest`/`auto` orienté-suggestion (n'ajoute que des idées à `queue.yaml`, à valider ensuite en mode `custom`) — même ambiguïté relevée sur `create_entities_and_instances.py` et `inject_custom_events.py`.
**Ajout** : chaque choix de `mode_select` dans `scripts_config.json` peut désormais porter un champ `note` optionnel, affiché dans un petit bandeau bleu sous les onglets Mode, mis à jour au clic. Mécanisme générique (`renderModeSelect()`/`app.js`), déjà rempli pour les deux scripts concernés.

---

## 4. Points de vigilance permanents

- **Routing LLM par tier** (depuis le 11 juillet) : `llm_client.py::TASK_TIER_DEFAULTS` fait foi pour le modèle utilisé par défaut selon le type de tâche. Le tier `strict` (rédaction d'articles, génération des journalistes) est actuellement sur `mistral-large-latest`, phase de test délibérée — repasser sur `claude-sonnet-5` au moment du passage en production (une seule ligne à changer). L'override manuel (`LLM_PROVIDER`/`LLM_MODEL` en variable d'environnement, ou le toggle GUI "Forcer ce modèle") garde toujours la priorité absolue sur le tier, pour un test ponctuel sans rien changer au comportement par défaut.
- **Toujours vérifier le code avant de conclure à une limite de fiabilité du LLM.** Le bug #26 a montré qu'un symptôme qui ressemble exactement à une hallucination ou un non-respect de consigne (contamination culturelle, journal incohérent) peut en réalité être un bug de résolution de données en amont, reproductible à l'identique sur deux modèles différents. Le fait qu'un même "échec" apparaisse de façon déterministe sur plusieurs runs/modèles est un signal fort qu'il ne s'agit *pas* d'une hallucination.
- **Consignes de prompt ("contrainte", "RÈGLE STRICTE"...) ne sont jamais auto-appliquées** — vérifier systématiquement qu'un filtre dur existe en sortie pour toute contrainte réellement critique (nombre d'éléments, slugs valides, scénario unique...). Plusieurs occurrences trouvées le 11 juillet (bugs #18/#34) où la consigne était bien écrite dans le prompt mais jamais vérifiée après réception de la réponse.
- **Rate limiting Mistral (Free plan : 1 RPS / 60 RPM / 500K TPM)** : géré depuis le 4 juillet par un retry réactif centralisé dans `llm_client.py` (bug #17), actif pour les 18 scripts du pipeline utilisant un LLM (100% de couverture depuis le 11 juillet). Aucune action manuelle nécessaire, mais les runs peuvent être lents sur de gros lots avec ce palier — passage en plan Scale envisageable si le volume de travail augmente.
- **3 fournisseurs LLM disponibles** : `mistral` (défaut hors override), `claude`, `openai` — tous passent par `llm_client.py`. Ajouter un 4e fournisseur ne nécessite qu'une fonction `_call_xxx()` sur le même modèle, aucune autre modification ailleurs dans le code.
- **`pipeline_dir` vs `vault_root`** dans `app.py` : `geographie/`, `entites_custom/`, `evenements_custom/`, `signaux_custom/`, `instances_custom/` vivent tous à `vault_root`, jamais dans `pipeline_dir` (`generator/`). Cause récurrente de bugs — a touché la carte, le panneau Review (bug #15) et 9 des 11 routes `/api/yaml*` (bug #16) en une seule journée. Réflexe à adopter pour tout nouveau chemin ajouté dans `app.py` ou `scripts_config.json` : vérifier dans le script générateur concerné où `VAULT_ROOT` pointe réellement avant de supposer `pipeline_dir`.
- **Clé API** : `Illegal header value b'Bearer '` = variable d'env non chargée dans le terminal courant → `source ~/.zshrc`. Le GUI n'est pas concerné (charge `.env` lui-même). Les trois clés (`MISTRAL_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) doivent toutes vivre dans `~/.zshrc`, même si un seul fournisseur est utilisé au quotidien — le jour où le tier `strict` bascule vers Claude en prod, la clé doit déjà être en place sans qu'on ait à y repenser.
- **Après tout remplacement d'`app.py`, toujours redémarrer Flask** (`lsof -ti:5000 | xargs kill -9` puis relancer) — un simple remplacement du fichier sur disque ne suffit pas, contrairement aux scripts `generator/` relus à chaque lancement. Cause du bug #23 (sauvegarde "muette" sur Generate series, aucun bug de code).
- **`scripts_config.json` : formulaire filtré par mode** depuis le 11 juillet (`mode_only`/`config_fields_mode`) — vérifier que tout nouveau champ ajouté à un script multi-modes porte bien le bon `mode_only`, sinon il restera visible sur tous les onglets (confusion vécue avec `scenario_ref`/`--scenario` avant le fix).
- David privilégie la simplicité : éviter l'accumulation de scripts ponctuels quand une solution plus générale (routing par tier, mécanisme `mode_only` générique, etc.) peut couvrir le même besoin durablement.

---

## 5. Prochaine session — ordre recommandé

1. **`routes_dashboard.py`** — vérifier la cohérence avec le renommage "LLM actif" → "Modèle si forcé" (bug #28) ; fichier non fourni pendant la session du 11 juillet, pas vérifié.
2. **`QUEUE_TEMPLATE`** (`entites_custom/queue.yaml` et `evenements_custom/queue.yaml`) — documenter le champ `zone_hint`, confirmé fonctionnel mais absent de la doc en tête de fichier (bug #31).
3. **Bug #27** (plausibilité logistique inter-zones) — observer s'il se reproduit sur d'autres tests avant de renforcer `build_system_prompt()`.
4. **Test de suivi bug #18/#26** — relancer une génération d'article sur `mistral-small` (pas seulement `mistral-large`) avec le pipeline désormais corrigé, pour confirmer si un vrai problème de fiabilité modèle subsiste une fois la cause de code (bug #26) éliminée, ou si le diagnostic du 4-6 juillet doit être révisé plus largement.
5. Reprendre le reste du backlog : P7 (restructure zones, pas encore codé), P8 (enrichissement des 426 fiches, ~$37 estimé).
6. Quand le passage en production sera décidé : basculer le tier `strict` sur `claude-sonnet-5` dans `TASK_TIER_DEFAULTS` (une ligne).
