# Handoff — Ourrassol 2098
*Consolidé le 4 juillet 2026 — vue d'ensemble projet + état de la session du jour*

---

## 1. Qu'est-ce qu'Ourrassol 2098

Simulateur de presse fictive et système de worldbuilding spéculatif situé en 2098, construit sur un vault Obsidian + un pipeline Python/Flask + API LLM (Anthropic Claude et Mistral). Six scénarios géopolitiques (`breakdown`, `fortress_world`, `new_sustainability`, `eco_communalism`, `policy_reform`, `reference`) partagent un même socle de variables, d'entités et d'événements, mais divergent narrativement.

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
8. **Rate limiting (429)** en cours de `--review`. Fix : délai de 8s entre batches dans les deux boucles (mode direct et mode `--review`).
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
**Décision associée (remplace la piste envisagée en P2quater)** : le provider et le modèle par défaut **restent `mistral` / `mistral-small`**, malgré la fiabilité géographique moindre notée en bugs #3 et §Points de vigilance. `claude-sonnet-4-6` reste disponible dans le sélecteur pour un choix ponctuel (carte/coverage) mais n'est pas le défaut global.

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
**Fix recommandé** (pas encore appliqué au dépôt) :
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
**Fix final retenu** : retry **purement réactif** centralisé dans `llm_client.py` (`call_llm()`), le point d'entrée unique utilisé par les 13 scripts du pipeline — aucune pause préventive, seulement une attente croissante (15s/30s/45s) et jusqu'à 4 tentatives automatiques **si et seulement si** l'erreur contient "429". S'adapte automatiquement à n'importe quel palier de compte (Free ou Scale) sans changer une ligne de code. Le fix local dans `create_entities_and_instances.py` a été retiré (redondant).
**Testé** : simulation de 2 échecs 429 puis succès (retry fonctionne, 3 appels réels) ; simulation d'une erreur non-429 (remonte immédiatement, aucun délai inutile). Confirmé en conditions réelles : sur le run suivant, 0 erreur 429/clé API sur 19 tentatives — tous les échecs restants sont de vrais échecs de contenu (voir bug #18).

### 18. `mistral-small` peu fiable sur un choix contraint (`variables_potentielles`)
**Symptôme** : sur un lot de 19 idées retraitées après le fix #17, **18 sur 19** ont échoué avec des `variables_potentielles` invalides — le LLM invente des noms de variables plausibles (`no_man_land_geopolitique`, `territoire_fragmenté_sans_autorite_centrale`...) au lieu de choisir dans la liste réelle.
**Vérifié : ce n'est pas un bug de prompt.** `build_variables_summary()` (`create_entities_and_instances.py`) transmet bien la liste exacte des slugs valides avec leur domaine (`- climat_environnement_global (domain: ...)`) — le référentiel correct est fourni. C'est un problème de fiabilité du modèle sur une tâche à choix fermé, même avec la liste sous les yeux et des instructions explicites — même famille de symptôme que le bug #3 (raisonnement géographique) déjà documenté pour `mistral-small`.
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
**Cause identifiée** : la fiche géographique du Bassin du Congo a pour allié `amazonie_pacte_viva` (`relations.allies`). Le contexte monde (`build_world_context`, `prompt_builder.py`) inclut des événements globaux du scénario (dont le Traité de Belém, déjà vu en détail dans cette session) indépendamment de la zone traitée — légitime pour la culture générale du journaliste, mais le LLM a confondu "information sur le monde" avec "propriété de ma zone", import ant des lieux et marqueurs culturels amazoniens dans un article censé se dérouler au Congo. `build_system_prompt()` n'avait aucune règle explicite sur la langue de rédaction ni sur la non-transposition d'éléments d'une entité extérieure.
**Fix appliqué (`prompt_builder.py`)** : deux règles ajoutées aux "règles absolues" du prompt système — (1) rédaction exclusivement en français, noms propres étrangers volontaires exceptés ; (2) un allié/rival/événement extérieur ne fait jamais partie de la zone traitée, ses lieux/langue/marqueurs culturels ne doivent jamais y être transposés sauf interaction explicite.
**Résultat partiel** : la règle 1 (langue) a fonctionné sur le run suivant — article entièrement en français. La règle 2 (non-transposition) **n'a pas suffi** : un nouvel article sur la même zone a quand même mentionné "São Paulo — Fragments Algorithmiques", une entité brésilienne sans rapport. Même famille de limite que les bugs #3/#18 : `mistral-small` ne respecte pas de façon fiable une contrainte explicite de ce type. Piste non tranchée en fin de session : basculer sur Claude pour la génération d'articles dans les zones à alliances actives, ou accepter le risque compte tenu du volume (~90M tokens estimés pour la phase articles).
**Découverte associée, cause distincte** : le nom du journal lui-même ("Yaripã: A Voz da Floresta", identique sur 2 articles générés à des moments différents) n'est pas régénéré par le LLM à chaque article — il est stocké une fois dans `generator/journaux.yaml` par `generate_journaux.py` et réutilisé tel quel. Ce script a son propre prompt, séparé de `prompt_builder.py`, non couvert par le fix ci-dessus. Son prompt donnait en exemple **littéralement "portugais"** comme valeur possible pour `langue_style`, sans lien avec l'identité réelle de la zone — le modèle a pris l'exemple au pied de la lettre. Confirmé : `build_prompt()` (`generate_journaux.py`) ne transmet pas `relations.allies` à ce stade, donc cette contamination-là est indépendante de l'alliance Amazônia Viva, purement un mauvais exemple dans le prompt.
**Fix appliqué (`generate_journaux.py`)** : prompt réécrit — ancrage explicite sur la description/statut/tensions de la zone elle-même (jamais une zone alliée), rédaction en français pour tous les champs, `langue_style` réservé aux cas où la description de la zone le justifie explicitement (héritage colonial/migratoire documenté), exemple biaisé retiré.
**Reste à faire** : pas d'option CLI pour régénérer une seule zone — contournement : supprimer l'entrée `congo_bassin_du_fleuve` de `journaux.yaml` (ligne `pro_pouvoir`, vérifier aussi `opposition`) puis relancer `generate_journaux.py --scenario eco_communalism --update` pour la regénérer avec le prompt corrigé.
**Effet de bord noté, non traité** : incohérence numérique interne détectée dans le 2e article (titre "cent vingt-six saisons" vs corps "quatre-vingt-dixième hiver") — défaut d'attention du modèle sur un détail chiffré, sans lien avec la contamination linguistique. Aucun mécanisme du pipeline (`validate.py` inclus) ne vérifie la cohérence interne du texte libre d'un article généré — seulement les instances/événements structurés.

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
**Reste à faire (prochaine session)** : vérifier `--all --fill-journalistes --dry-run` confirme bien "rien à faire" partout, inspecter une rédaction générée pour en juger la qualité, puis regénérer un article sur une zone déjà testée (Bassin du Congo / `sante`) pour confirmer que la signature apparaît et correspond au bon journaliste de la thématique.

---

## 4. Points de vigilance permanents

- **Rate limiting Mistral (Free plan : 1 RPS / 60 RPM / 500K TPM)** : géré depuis le 4 juillet par un retry réactif centralisé dans `llm_client.py` (bug #17), actif pour tous les scripts du pipeline. Aucune action manuelle nécessaire, mais les runs peuvent être lents sur de gros lots avec ce palier — passage en plan Scale envisageable si le volume de travail augmente (voir estimation tokens/coût de la session).
- **`mistral-small` peu fiable sur les tâches à choix contraint ou de discipline contextuelle** (bug #3 géographie, bug #18 variables_potentielles, bug #20 contamination langue/culture entre zones alliées — confirmé non résolu même avec une règle de prompt explicite) — basculer ponctuellement sur `claude-sonnet-4-6`/`claude-sonnet-5` (ou désormais `openai`/`gpt-5.5`, ajouté le 5 juillet) via `LLM_PROVIDER`/`LLM_MODEL` ou le sélecteur GUI, sans changer le défaut global (`mistral`).
- **3 fournisseurs LLM disponibles** depuis le 5 juillet : `mistral` (défaut), `claude`, `openai` — tous passent par `llm_client.py`, bénéficient automatiquement du retry centralisé (bug #17) et du sélecteur GUI générique (bug #21). Ajouter un 4e fournisseur un jour ne nécessite qu'une fonction `_call_xxx()` sur le même modèle, aucune autre modification ailleurs dans le code.

- **`pipeline_dir` vs `vault_root`** dans `app.py` : `geographie/`, `entites_custom/`, `evenements_custom/`, `signaux_custom/`, `instances_custom/` vivent tous à `vault_root`, jamais dans `pipeline_dir` (`generator/`). Cause récurrente de bugs — a touché la carte (§3), le panneau Review (bug #15) et 9 des 11 routes `/api/yaml*` (bug #16) en une seule journée. Réflexe à adopter pour tout nouveau chemin ajouté dans `app.py` ou `scripts_config.json` : vérifier dans le script générateur concerné où `VAULT_ROOT` pointe réellement avant de supposer `pipeline_dir`.
- **Clé API** : `Illegal header value b'Bearer '` = variable d'env non chargée dans le terminal courant → `source ~/.zshrc`. Le GUI n'est pas concerné (charge `.env` lui-même). Les trois clés (`MISTRAL_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) doivent toutes vivre dans `~/.zshrc` — `ANTHROPIC_API_KEY` traînait dans `.bash_profile` (non lu par zsh, fonctionnait par chance) avant d'être dupliquée dans `.zshrc` le 6 juillet.
- **Après tout remplacement d'`app.py`, toujours redémarrer Flask** (`lsof -ti:5000 | xargs kill -9` puis relancer) — un simple remplacement du fichier sur disque ne suffit pas, contrairement aux scripts `generator/` relus à chaque lancement. Cause du bug #23 (sauvegarde "muette" sur Generate series, aucun bug de code).
- **`complete_geographie_coverage.py`** a été patché plusieurs fois le 4 juillet (fixes #1, #5, #6, #8, #9 tous dans ce fichier) — vérifier en début de prochaine session que la version en place contient bien le fix #9 le plus récent (`grep -c "nouvelles_zones_ce_batch" complete_geographie_coverage.py` doit renvoyer ≥ 2). Utilise son propre délai fixe de 8s (indépendant du fix #17) — pas encore migré vers le retry centralisé de `llm_client.py`, mais toujours fonctionnel (voir P13 du backlog).
- David privilégie la simplicité : éviter l'accumulation de scripts ponctuels quand une solution plus générale (ou l'onglet Carte) peut couvrir le même besoin.

---

## 5. Prochaine session — ordre recommandé

1. Vérifier `generate_journaux.py --all --fill-journalistes --dry-run` confirme "rien à faire" partout (rédactions de 6 journalistes livrées le 6 juillet), inspecter une rédaction pour en juger la qualité.
2. Regénérer un article de test (Bassin du Congo / `eco_communalism` / `sante` — celui du bug #20) pour confirmer que la signature du journaliste apparaît et correspond à la bonne thématique.
3. Reprendre P3 : **Create entities (custom)** et **Inject events (custom)** — 2 tests restants sur les 4 prévus (Generate et Generate series validés).
4. `check_zones_coherence.py --all` — réflexe de fin de session après tout travail touchant aux entités/géographie.
5. Traiter `communes_rust_belt` si pas encore fait (voir P12 du backlog).
6. Envisager de migrer `complete_geographie_coverage.py` vers le retry centralisé de `llm_client.py` (bug #17) plutôt que son délai fixe de 8s (P13 du backlog).
7. Reprendre le reste du backlog : P6/P11 (vérification `scripts_config.json` + intégration `check_zones_coherence.py` au GUI), P7 (restructure zones, pas encore codé), P8 (enrichissement des 426 fiches, ~$37 estimé).
