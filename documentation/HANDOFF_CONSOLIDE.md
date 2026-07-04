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

---

## 4. Points de vigilance permanents

- **`pipeline_dir` vs `vault_root`** dans `app.py` : `geographie/` vit à `vault_root`, pas dans `pipeline_dir` (`generator/`). Cause récurrente de bugs.
- **Clé API** : `Illegal header value b'Bearer '` = variable d'env non chargée dans le terminal courant → `source ~/.zshrc`. Le GUI n'est pas concerné (charge `.env` lui-même).
- **`mistral-small-latest`** (défaut confirmé) reste moins fiable que Claude en raisonnement géographique (carte, coverage) — basculer ponctuellement sur `claude-sonnet-4-6` ou `claude-sonnet-5` depuis le sélecteur GUI si besoin.
- **`complete_geographie_coverage.py`** a été patché plusieurs fois le 4 juillet (fixes #1, #5, #6, #8, #9 tous dans ce fichier) — vérifier en début de prochaine session que la version en place contient bien le fix #9 le plus récent (`grep -c "nouvelles_zones_ce_batch" complete_geographie_coverage.py` doit renvoyer ≥ 2).
- **Rate limiting** : le délai de 8s entre batches rend les runs plus longs mais plus fiables — ne pas interrompre un `--review`/`--apply` en cours.
- David privilégie la simplicité : éviter l'accumulation de scripts ponctuels quand une solution plus générale (ou l'onglet Carte) peut couvrir le même besoin.

---

## 5. Prochaine session — ordre recommandé

1. Vérification 10 min (voir tête de `BACKLOG_CONSOLIDE.md`) — confirmer le fix #9 en place + `check_zones_coherence.py --all` propre.
2. Décider du modèle LLM par défaut pour carte/coverage (`config.json`) — actuellement encore `mistral-small`.
3. P1bis — documenter l'onglet Carte + coverage dans `user_manual_updated.md` (base fournie : `USER_MANUAL_carte_et_couverture_4juillet.md`, à fusionner avec `USER_MANUAL_COMPLET.md` livré aujourd'hui).
4. P2ter — traiter les 32 pays "sous-zone sans N1" via l'onglet Carte.
5. P11 (optionnel) — intégrer `check_zones_coherence.py` au GUI.
6. Reprendre P3 (tests end-to-end des formulaires guidés) — P2 n'est plus un point de blocage.
