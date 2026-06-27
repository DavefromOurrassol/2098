---
type: documentation
titre: Ourrassol 2098 — Manuel complet des scripts
date_maj: 2026-06-27
---

# Ourrassol 2098 — Manuel complet des scripts

Référence exhaustive de tous les scripts du pipeline. Toutes les commandes se lancent depuis `generator/`.

---

## Table des matières

1. [Génération d'articles](#génération-darticles)
2. [Géographie](#géographie)
3. [Localisation](#localisation)
4. [Entités et instances](#entités-et-instances)
5. [Événements custom](#événements-custom)
6. [Signaux faibles custom](#signaux-faibles-custom)
7. [Retrait du lore](#retrait-du-lore)
8. [Validation](#validation)
9. [Modules internes](#modules-internes)
10. [Scripts one-shot](#scripts-one-shot)

---

## Génération d'articles

### `generate.py`
Génère un seul article selon `config.yaml`.

```bash
python3 generate.py           # génère l'article
python3 generate.py --dry-run # affiche le prompt sans appel API
```

**Config** : `generator/config.yaml`
```yaml
scenario: reference
thematique: sciences_technologies
article:
  titre_suggere: ""
  angle_specifique: ""
  longueur: auto
```

**Sortie** : `articles/{scenario}/{date}_{thematique}.md`

---

### `generate_series.py`
Génère une série d'articles pour plusieurs thématiques.

```bash
python3 generate_series.py
python3 generate_series.py --dry-run
python3 generate_series.py --scenario breakdown
python3 generate_series.py --validate-first
```

**Config** : `generator/config_series.yaml`
```yaml
scenario: reference
thematiques:
  - politique
  - sciences_technologies
articles_par_thematique: 1
longueur: auto
```

---

### `generate_manual.py`
Workflow sans appel API — génère le prompt à copier dans un chat Claude.

```bash
python3 generate_manual.py prompt              # affiche le prompt
python3 generate_manual.py status             # avancement X/N
python3 generate_manual.py save /tmp/art.txt  # sauvegarde l'article
```

**État** : `generator/state/manual_progress.json`

---

### `generate_entities.py`
Génère automatiquement les archétypes entités pour toutes les thématiques via l'API.

```bash
python3 generate_entities.py
```

⚠️ Script de génération en masse — à utiliser avec précaution sur un vault déjà peuplé.

---

### `generate_instances.py`
Génère les instances par scénario pour des entités déjà créées.

```bash
python3 generate_instances.py
python3 generate_instances.py --entity mon_entite
python3 generate_instances.py --scenario breakdown
python3 generate_instances.py --force      # réécrit les instances existantes
python3 generate_instances.py --dry-run
```

---

## Géographie

### `build_geographie_monde.py`
Étape 1 — crée le squelette géographique niveau 1 d'un scénario.

```bash
python3 build_geographie_monde.py --scenario reference --dry-run
python3 build_geographie_monde.py --scenario reference
python3 build_geographie_monde.py --all
python3 build_geographie_monde.py --scenario reference --force  # réécrit
```

**Sortie** : `geographie/{scenario}.md`

À lancer **une seule fois** par scénario. Additif, jamais destructeur sur les zones existantes.

---

### `enrich_geographie_recursive.py`
Étape 2 — enrichit les bibles monde avec des sous-zones (niveaux 2 et 3).

```bash
python3 enrich_geographie_recursive.py --scenario reference --dry-run
python3 enrich_geographie_recursive.py --scenario reference
python3 enrich_geographie_recursive.py --all
```

Relançable à volonté — additif, les zones existantes ne sont jamais réécrites.

**Après chaque enrichissement** :
```bash
python3 extract_localisation.py
python3 review_localisation.py --auto-resolve
```

---

### `fix_lieux_residuels.py`
Nettoie les doublons de zones laissés par une version antérieure de `enrich_geographie_recursive.py`.

```bash
python3 fix_lieux_residuels.py --scenario reference --dry-run
python3 fix_lieux_residuels.py --scenario reference
python3 fix_lieux_residuels.py --all
```

---

## Localisation

### `extract_localisation.py`
Extrait le champ `localisation` (zone / lieu / type_lieu) sur les fiches riches du vault.

```bash
python3 extract_localisation.py               # traite toutes les fiches sans localisation
python3 extract_localisation.py --dry-run     # simulation — appel API, pas d'écriture
python3 extract_localisation.py --scenario reference   # un seul scénario
python3 extract_localisation.py --slug nexcore_reference  # une seule fiche
python3 extract_localisation.py --force       # retraite les fiches déjà traitées
python3 extract_localisation.py --report-only # génère le rapport sans extraire
```

**Trois états de localisation** :
- `extrait` — zone trouvée et validée
- `vide` — entité transnationale (`zone: null`)
- `review_manuelle` — ambigu, jamais deviné silencieusement

**Rapport** : `documentation/need_action/localisation_review.md`

---

### `review_localisation.py`
Review des fiches marquées `statut: review_manuelle`.

```bash
python3 review_localisation.py                         # interactif fiche par fiche
python3 review_localisation.py --auto-resolve          # Claude tranche seul
python3 review_localisation.py --auto-resolve --dry-run
python3 review_localisation.py --scenario reference
```

**Décisions interactives** : `[V]` valider · `[C]` choisir autre zone · `[0]` vide assumé · `[S]` skip · `[Q]` quitter

---

## Entités et instances

### `create_entities_and_instances.py`
Crée des entités (archétypes) et leurs instances sur tous les scénarios.

```bash
python3 create_entities_and_instances.py
python3 create_entities_and_instances.py --dry-run
```

**Trois modes au lancement :**

#### Mode `custom`
Traite `entites_custom/queue.yaml`. Contrôle total sur nom, catégorie, rôle, scénarios.

```yaml
queue:
  - nom: Le Cartographe Silencieux
    category: humain
    role: >
      Ancien officier de renseignement devenu cartographe clandestin.
      Basé à Tbilissi, opère dans les corridors eurasiens.
    etat: clandestin
    scenario_ref: breakdown
    scenario_hint: null     # null = les 6 scénarios
    source: idee_2026-06
```

- `role` et `etat` sont des **contraintes dures** pour `scenario_ref`
- `scenario_hint: null` = instances pour les 6 scénarios
- Pour un ancrage géographique précis : mentionner le lieu dans `role`

#### Mode `auto`
Donne un nombre N + catégorie optionnelle. Claude invente les entités et les injecte directement. Pas de contrôle géographique.

#### Mode `auto-suggest` *(recommandé pour l'équilibrage géo)*
Analyse la couverture géographique actuelle + zones sans instance (depuis `geographie/{scenario}.md`), génère N idées → écrit dans `entites_custom/queue.yaml` sans injecter.

```
Nombre d'idées à générer ? [défaut: 3] :
Scénario de référence ciblé ? (Entrée pour laisser Claude choisir) :
```

Inspecter `queue.yaml`, puis relancer en mode `custom`.

**Cycle post-injection automatique** (modes `custom` et `auto`, si ≥ 1 instance créée) :
```
extract_localisation.py → review_localisation.py --auto-resolve → validate.py
```

**Anti-doublon** : `_entities_list.json` injecté dans le prompt + réponse `doublon_detecte`.

**Fichiers** : `entites_custom/queue.yaml` → `processed.yaml` (succès) ou `needs_review.yaml` (échec)

---

### `create_entity.py`
Version simplifiée de `create_entities_and_instances.py` — crée uniquement l'archétype entité, sans les instances.

```bash
python3 create_entity.py
python3 create_entity.py --dry-run
```

Modes : `custom` (queue) ou `auto` (N entités inventées).

---

## Événements custom

### `inject_custom_events.py`
Injecte des événements custom dans le vault.

```bash
python3 inject_custom_events.py
python3 inject_custom_events.py --dry-run
```

**Deux modes au lancement :**

#### Mode `custom`
Traite `evenements_custom/queue.yaml`.

```yaml
queue:
  - id: mon_evenement
    description: >
      Description détaillée, avec lieu et acteurs potentiels.
    portee: globale            # locale | regionale | continentale | globale
    date_approximative: "2047"
    intensite: majeure         # faible | modérée | forte | majeure
    scenarios: null            # null = les 6 scénarios | ["sc1", "sc2"]
    variables_hint: [gouvernance_institutions, geopolitique_conflits]
    variables_hint_count: 3
    acteurs_hint: null
    acteurs_hint_count: 2
    source: idee_2026-06
```

⚠️ Si la description contient ":", entourer de guillemets.

#### Mode `auto` *(recommandé pour l'équilibrage géo)*
Analyse la couverture du vault (zones absentes, types peu représentés, variables peu couvertes), génère N idées → écrit dans `evenements_custom/queue.yaml` en ajout sans injection.

```
Nombre d'idées à générer ? [défaut: 3] :
Scénario ciblé ? (Entrée pour laisser Claude choisir) :
```

Inspecter `queue.yaml`, puis relancer en mode `custom`.

**Comportement `processed.yaml`** :
- Succès total → `status: injected`
- Succès partiel → `status: partial` dans `processed.yaml` + scénarios échoués dans `needs_review.yaml`
- Échec total → tout en `needs_review.yaml`

**Cycle post-injection automatique** (mode `custom`, si ≥ 1 scénario injecté) :
```
extract_localisation.py → review_localisation.py --auto-resolve → validate.py
```

---

### `inject_custom_signals.py`
Injecte des signaux faibles custom dans les thématiques.

```bash
python3 inject_custom_signals.py
python3 inject_custom_signals.py --dry-run
```

**Queue** : `signaux_custom/queue.yaml`
```yaml
queue:
  - id: mon_signal
    description: >
      Observation ou tendance émergente.
    source: actualite_2026-06
    variable_hint: sante_biotechnologies
```

---

## Enrichissement minimal

### `enrich_minimal.py`
Enrichit les fiches `officialise_minimal` via l'API Claude. Génère tous les champs narratifs placeholder.

```bash
python3 enrich_minimal.py --scenario new_sustainability        # un scénario
python3 enrich_minimal.py --scenario new_sustainability --dry-run
python3 enrich_minimal.py --scenario new_sustainability --limit 3   # essai sur N fiches
python3 enrich_minimal.py --scenario new_sustainability --slug SLUG # une seule fiche
python3 enrich_minimal.py --all                                # tous les scénarios
python3 enrich_minimal.py --all --auto-cycle                   # + cycle post-run auto
```

**Champs générés** : `responsabilites`, `description_journalistique`, `signes_distinctifs`, `tensions_narratives`, `localisation`, `impact_local`, `impact_systemique_global`, `alliances`, `oppositions`, `zone_geographique`, `type_relation_dominante`.

**Validation mécanique bloquante** (2 retries) : `localisation.zone` vs bible géo, `type_lieu` 4 valeurs, `impact` [0-5], `zone_geographique` 7 valeurs. Warnings non bloquants : alliances/oppositions vs `_entities_list.json` + scan `instances/*.md`.

**Reprise** : `statut: officialise_enrichi` — les fiches déjà enrichies sont skippées.

**Sorties** : `documentation/need_action/enrich_minimal_report.md` + `instances_custom/needs_review_enrich.yaml`.

**Slugs fantômes** : en fin de run, génère automatiquement les entrées queue pour les slugs alliances/oppositions non trouvés (vague 1). Avec `--auto-cycle` : + vague 2 depuis `validate --verbose` après le cycle post-injection.

---

### `extract_phantom_slugs.py`
Extrait les slugs fantômes alliances/oppositions et génère `entites_custom/queue.yaml` avec rôles générés via API.

```bash
python3 extract_phantom_slugs.py                        # all sources, écrit queue.yaml
python3 extract_phantom_slugs.py --source enrich        # depuis enrich_minimal_report.md
python3 extract_phantom_slugs.py --source validate      # depuis validate.py --verbose
python3 extract_phantom_slugs.py --source all           # les deux combinées (défaut)
python3 extract_phantom_slugs.py --dry-run              # affiche sans écrire
python3 extract_phantom_slugs.py --report PATH          # rapport alternatif
```

Corrige automatiquement les suffixes scénario manquants. Déduplication sur `_slug_corrige`.

---

### `fix_alliance_suffixes.py`
Corrige les slugs sans suffixe scénario dans les champs `alliances`/`oppositions` des fiches instances. Aucun appel API — correction purement mécanique.

```bash
python3 fix_alliance_suffixes.py --dry-run --verbose
python3 fix_alliance_suffixes.py
python3 fix_alliance_suffixes.py --scenario fortress_world
```

---

### `requeue_needs_review.py`
Remet les entrées de `entites_custom/needs_review.yaml` dans `queue.yaml` pour une nouvelle tentative.

```bash
python3 requeue_needs_review.py --dry-run
python3 requeue_needs_review.py
```

---

## Retrait du lore

### `undo_custom.py`
Retire proprement entités, instances, événements ou event_instances du lore.

```bash
python3 undo_custom.py                           # dry-run depuis undo_queue.yaml
python3 undo_custom.py --execute                 # supprime réellement
python3 undo_custom.py --slug SLUG --type TYPE --generalisation yes|no
python3 undo_custom.py --slug SLUG --type TYPE --generalisation yes|no --execute
```

**Queue** : `evenements_custom/undo_queue.yaml`
```yaml
undo:
  - type: event_instance   # | instance | event | entite
    slug: mon_slug
    generalisation: no     # | yes
```

**Types disponibles :**

| type | alias de |
|---|---|
| `event_instance` | — |
| `instance` | — |
| `event` | event_instance + generalisation: yes |
| `entite` | instance + generalisation: yes |

**Comportement `generalisation` :**

| generalisation | Supprime |
|---|---|
| `no` | fichier ciblé + dépendances directes (registre, alliances/oppositions) |
| `yes` | archétype + toutes instances/event_instances tous scénarios + dépendances |

**Garanties** :
- Dry-run par défaut — `--execute` pour écrire réellement
- Backup `.bak` automatique avant toute suppression
- `last_validated.json` resetté
- `_entities_list.json` nettoyé
- Queue vidée après `--execute`

**Vérifier la suppression** :
```bash
grep -r "chaine_du_slug" ../instances/ ../entites/ ../event_instances/ ../evenements/
```

**Cycle post-undo** :
```bash
python3 undo_custom.py --execute
python3 validate.py
```

---

### `rebuild_processed.py`
Reconstruit `processed.yaml` depuis les fichiers réels dans `event_instances/`.

```bash
python3 rebuild_processed.py --dry-run
python3 rebuild_processed.py
```

À utiliser si `processed.yaml` est désynchronisé avec les fichiers réels.

---

## Validation

### `validate.py`
Vérifie la cohérence complète du vault en 9 sections.

```bash
python3 validate.py                  # validation complète
python3 validate.py -v               # détail avertissements terminal
python3 validate.py --verbose        # identique à -v
python3 validate.py --report         # génère validation_report.md (Obsidian)
python3 validate.py --localisation   # scan localisation uniquement
python3 validate.py --narrative      # force scan cohérence narrative
python3 validate.py --verbose 2>&1 | grep "narrative"   # warnings narratifs uniquement
```

**9 sections :**

| # | Section | Description |
|---|---|---|
| 1 | Nomenclature | Slugs, fichiers, noms |
| 2 | Cohérence systémique | Levels, états, trajectoires |
| 3 | Entités/instances | Relations, injections, échelles |
| 4 | Thématiques | Formats, variables, `echelle` |
| 5 | Localisation | Champ localisation, slug zone, review_manuelle |
| 6 | Références croisées | Wikilinks cassés |
| 7 | Matrice d'influence | Edges, valeurs |
| 8 | Événements | Archétypes, instances, YAML cassé |
| 9 | Cohérence narrative | Acteurs inactifs, overflow delta, cohérence dates |

**Section 9 — Cohérence narrative** :
- Conditionnel : tourne si event_instances modifiées depuis `generator/last_validated.json`
- `--narrative` pour forcer
- Whitelist acteurs inactifs : `age_historique` ∈ `{résiduel, mythifié}`
- Overflow delta : seuil `[-20, 130]` (au-delà = probable erreur de saisie)
- Vérifications instances : `annee_debut` absent, `annee_fin` incohérente, `etat_temporel` vs `annee_fin`
- Rapport → `documentation/need_action/narrative_issues.yaml`

**`last_validated.json`** mis à jour si 0 erreurs en fin de run.

---

## Modules internes

Ces scripts sont des modules utilisés par les autres — ne pas lancer directement.

### `loader.py`
Lit et parse les fichiers `.md` du vault. Expose `load_thematique()`, `load_all_variables()`, etc.

### `snapshot.py`
Construit le snapshot cohérent du monde pour un scénario donné (variables, tensions, trajectoire, instances filtrées).

### `prompt_builder.py`
Assemble le prompt complet envoyé à Claude, avec filtrage géographique et section "Ancrage de cet article".

### `api.py`
Envoie le prompt à l'API Claude et sauvegarde l'article généré.

---

## Scripts one-shot

Ces scripts ont déjà été exécutés — **ne pas relancer**.

### `migrate_registre.py`
Migration `registre_evenements.md` de l'ancien format 5 colonnes vers le format hybride 6 colonnes actuel.

### `officialize_alliances.py`
Conversion des alliances/oppositions en texte libre → slugs réels. Options : `--dry-run`, `--limit N`, `--resume`.

### `fix_impact_scale.py`
Correction rétroactive des `impact_local` / `impact_systemique_global` hors plage [0-5] dans les instances.

---

## Cycles standards

### Cycle post-injection (automatique)
Lancé automatiquement par `create_entities_and_instances.py`, `inject_custom_events.py` et `enrich_minimal.py` après toute injection réussie :
```
extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
```

### Cycle post-undo (manuel)
```
undo_custom.py --execute
→ validate.py
```

### Cycle d'enrichissement géographique
```
enrich_geographie_recursive.py --all
→ extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
```

### Cycle de rééquilibrage géographique
```
create_entities_and_instances.py  (mode auto-suggest)
→ [inspecter queue.yaml]
→ create_entities_and_instances.py  (mode custom)
→ [cycle post-injection automatique]

inject_custom_events.py  (mode auto)
→ [inspecter queue.yaml]
→ inject_custom_events.py  (mode custom)
→ [cycle post-injection automatique]
```
