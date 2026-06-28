# HANDOFF — 28 juin 2026 (fin de session)

---

## État du vault en fin de session

```
Entités       : 571
Instances     : 690
Thématiques   : 20
Fiches riches : 760 (0 sans localisation, 0 review_manuelle)
Archétypes    : 16 événements
Instances evt : 70 événements
Erreurs       : 0
Avertissements: 0
Cohérence narrative : OK
Journaux breakdown  : générés (11 zones N1 × 2 lignes = 22 éditions locales)
```

---

## Ce qui a été accompli aujourd'hui

### 1. Migration LLM — Claude/Mistral (CLOS)

Abstraction complète du fournisseur LLM via `llm_client.py`.
- **Fournisseur par défaut : Mistral** (`mistral-medium-latest`)
- Bascule Claude : `LLM_PROVIDER=claude python3 script.py`
- Override modèle : `LLM_MODEL=mistral-large-latest python3 script.py`
- Variables d'env : `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY` (dans `~/.zshrc`)

**14 scripts migrés** (suppression import anthropic direct, remplacement par `call_llm()`) :
`api.py`, `extract_localisation.py`, `review_localisation.py`, `enrich_minimal.py`,
`extract_phantom_slugs.py`, `create_entities_and_instances.py`, `inject_custom_events.py`,
`inject_custom_signals.py`, `generate_entities.py`, `generate_instances.py`,
`create_entity.py`, `build_geographie_monde.py`, `enrich_geographie_recursive.py`

**Note `enrich_geographie_recursive.py`** : streaming Anthropic remplacé par appel standard.
Surveiller timeouts sur max_tokens=24000 avec Claude si besoin.

### 2. Journaux locaux par zone (CLOS)

Nouveau système éditorial à deux niveaux :
- **Ligne éditoriale** : `pro_pouvoir` | `opposition` (12 profils hardcodés dans `prompt_builder.py`)
- **Éditions locales** : un journal par zone N1 par scénario×ligne (généré via API dans `journaux.yaml`)

**Nouveau script** : `generate_journaux.py`
- Lit les zones N1 de `geographie/{scenario}.md`
- Génère via API : nom du journal, ton local, langue/style
- Produit `generator/journaux.yaml`
- Options : `--scenario NOM | --all`, `--ligne pro_pouvoir|opposition|all`, `--update`, `--dry-run`

**Résolution du profil journal à chaque article** (priorité décroissante) :
1. Édition locale (`journaux.yaml` → zone dominante du snapshot)
2. Réseau global (`journaux.yaml` → `_reseau`)
3. Profil hardcodé (`JOURNAL_PROFILES` dans `prompt_builder.py`)
4. Profil par défaut générique

**Warning** si zone sans édition locale :
```
[WARN][journal] Pas d'édition locale pour zone 'X' / scenario / ligne → fallback réseau global
```

### 3. Évolutions `prompt_builder.py` (CLOS)

- 12 profils éditoriaux dans `JOURNAL_PROFILES` (`{scenario}_{ligne}`)
- Aliases de compatibilité : clés courtes → `pro_pouvoir` (pas de régression)
- `build_system_prompt()` accepte `scenario_slug`, `ligne_editoriale`, `zone_slug`
- `get_journal_profile()` : résolution prioritaire édition locale > réseau > hardcodé > défaut
- `_load_journaux()` + `_JOURNAUX_CACHE` : chargement lazy de `journaux.yaml`

### 4. Évolutions `snapshot.py` (CLOS)

- `_dominant_zone(instances)` : extrait la zone la plus représentée parmi `filtered_instances`
- `zone_slug` ajouté au snapshot → alimenté automatiquement depuis `localisation.zone`

### 5. Évolutions `generate_series.py` (CLOS)

- `import random` ajouté
- Tirage aléatoire `ligne_editoriale` à chaque article si non défini dans `config_series.yaml`
- `ligne_editoriale` injecté dans `article_config`

### 6. Évolutions `generate_manual.py` (CLOS)

- `import random` ajouté
- `ligne_editoriale` tiré aléatoirement ou depuis config dans `cmd_prompt()`
- `ligne_editoriale` sauvegardé dans `progress["pending"]`
- `ligne_editoriale` tracé dans le frontmatter des articles sauvegardés

### 7. Évolutions `generate.py` (CLOS)

- `import random` ajouté
- `DATES_2098` : liste de 20 dates fictives 2098
- Date fictive tirée aléatoirement si absente de `config.yaml`
- Nom de fichier avec date fictive en suffixe

### 8. Évolutions `api.py` (CLOS)

- `build_article_filename()` : suffixe date fictive normalisée
  Ex: `20260628_143022_breakdown_actualites_a_la_une_article_3janvier2098.md`
- `ligne_editoriale` dans le frontmatter des articles générés
- `model: mistral/mistral-medium-latest` ou `model: claude/claude-sonnet-4-6` dans frontmatter

### 9. Configs mises à jour (CLOS)

**`config.yaml`** — nouveaux champs :
```yaml
ligne_editoriale: pro_pouvoir   # pro_pouvoir | opposition
zone_slug: ""                   # optionnel — force une édition locale
```

**`config_series.yaml`** — nouveau champ :
```yaml
ligne_editoriale:               # vide = aléatoire | pro_pouvoir | opposition
```

---

## Fichiers livrés aujourd'hui (à déposer dans `generator/`)

**Nouveaux :**
- `llm_client.py`
- `generate_journaux.py`

**Mis à jour :**
- `api.py`
- `extract_localisation.py`
- `review_localisation.py`
- `enrich_minimal.py`
- `extract_phantom_slugs.py`
- `create_entities_and_instances.py`
- `inject_custom_events.py`
- `inject_custom_signals.py`
- `generate_entities.py`
- `generate_instances.py`
- `create_entity.py`
- `build_geographie_monde.py`
- `enrich_geographie_recursive.py`
- `prompt_builder.py`
- `snapshot.py`
- `generate_series.py`
- `generate_manual.py`
- `generate.py`
- `config.yaml`
- `config_series.yaml`

---

## Cycle continu mis à jour

```
enrich_minimal.py --scenario X [--auto-cycle]
→ extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
→ generate_journaux.py --all --update   ← nouveau (si nouvelles zones)
→ generate_series.py
```

---

## Todolist — prochaine session

### 🟡 Priorité 1 — Chantier `restructure` (P7)
Outil de maintenance pour scinder/fusionner/reparenter/renommer des zones.
Périmètre à confirmer : wikilinks vers slugs de zones ? registre_evenements.md ?

### 🟢 Priorité 2 — `temperature` configurable
Exposer `TEMPERATURE` dans `config.yaml` et `config_series.yaml` pour régler
le degré d'inventivité des articles sans toucher au code.

### 🟢 Priorité 3 — Traduction des articles
Script `translate_article.py` post-génération : article .md en français → version traduite.
À traiter quand le pipeline de génération est stabilisé.

### 🟢 Priorité 4 — GUI Flask
Launcher Flask + Safari (macOS High Sierra). Spec existante : `ourrassol_gui_spec.json`.
Options CLI de tous les scripts mémorisées pour intégration.

### 🟢 Priorité 5 — Trigger automatique `generate_journaux.py`
Intégrer `generate_journaux.py --all --update` dans le cycle post-injection
de `create_entities_and_instances.py` et `inject_custom_events.py`.

### 🔵 Priorité 6 — Migration Mistral complète (optionnel)
Tester la qualité JSON et cohérence narrative de Mistral sur `enrich_minimal --limit 5`
avant de lancer `--all`. Comparer avec Claude sur les mêmes fiches.

---

## Notes coûts API

- Migration vers Mistral par défaut : économie estimée ~6-10x vs Sonnet
- `generate_journaux.py --all` : ~22 journaux × 6 scénarios = 132 appels (lots de 5)
  → estimation $0.50-1.00 sur Mistral Medium
- Cumul sessions : ~$72 (avant cette session)
- Recommandation : vérifier console après `generate_journaux.py --all`
