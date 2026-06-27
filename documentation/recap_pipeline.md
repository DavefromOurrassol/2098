---
type: documentation
titre: Pipeline Ourrassol 2098 — Récapitulatif
date_maj: 2026-06-27
---

# Pipeline Ourrassol 2098 — Récapitulatif

Mis à jour après la session du 27 juin 2026 (P8 enrich_minimal.py, extract_phantom_slugs.py, fix_alliance_suffixes.py, requeue_needs_review.py, passage Opus→Sonnet, territoire dans VALID_CATEGORIES).

---

## 1. Génération d'articles

```bash
python3 generate.py [--dry-run]
python3 generate_series.py [--dry-run] [--scenario NOM]
python3 generate_manual.py prompt|status|save
```

Pipeline : `loader` → `snapshot` → `prompt_builder` (avec filtrage géo) → `api` → `articles/{scenario}/`

---

## 2. Géographie du monde

```bash
python3 build_geographie_monde.py --scenario NOM [--dry-run]
python3 enrich_geographie_recursive.py --scenario NOM [--dry-run] | --all
python3 fix_lieux_residuels.py --scenario NOM [--dry-run]
```

Tous les 6 scénarios enrichis N1+N2+N3 au 25 juin 2026.

---

## 3. Localisation des entités

Champ `localisation` sur chaque fiche riche. Trois états : `extrait` | `vide` | `review_manuelle`.

```bash
python3 extract_localisation.py [--dry-run] [--scenario NOM] [--slug SLUG] [--force] [--report-only]
python3 review_localisation.py [--auto-resolve] [--dry-run] [--scenario NOM]
```

---

## 4. Injections custom — entités

```bash
python3 create_entities_and_instances.py [--dry-run]
```

**Trois modes au lancement :**

| Mode | Description | Injection |
|---|---|---|
| `custom` | traite `entites_custom/queue.yaml` | oui |
| `auto` | Claude invente N entités, catégorie optionnelle | oui |
| `auto-suggest` | analyse vault + zones absentes → idées dans `queue.yaml` | non — inspection d'abord |

**Mode `auto-suggest`** : charge `geographie/{scenario}.md` pour identifier les zones sans instance, injecte ce bilan dans le prompt Claude. Idées ajoutées à `queue.yaml` sans écrasement.

**Cycle post-injection automatique** (modes `custom` et `auto`, si ≥ 1 instance créée) :
```
extract_localisation.py → review_localisation.py --auto-resolve → validate.py
```

**Anti-doublon** : `_entities_list.json` injecté dans le prompt + validation `doublon_detecte`.

---

## 5. Injections custom — événements

```bash
python3 inject_custom_events.py [--dry-run]
```

**Deux modes au lancement :**

| Mode | Description | Injection |
|---|---|---|
| `custom` | traite `evenements_custom/queue.yaml` | oui |
| `auto` | analyse vault + zones absentes → idées dans `queue.yaml` | non — inspection d'abord |

**Mode `auto`** : analyse géo (zones absentes depuis `geographie/{scenario}.md`), types d'événements peu représentés, variables peu couvertes. Idées ajoutées à `queue.yaml` sans écrasement.

**Comportement `processed.yaml`** (depuis le 25 juin) :
- Succès partiel → `status: partial` + scénarios réussis dans `processed.yaml`, scénarios échoués dans `needs_review.yaml`

**Cycle post-injection automatique** (mode `custom`, si ≥ 1 scénario injecté) : idem entités.

---

## 6. Injections custom — signaux faibles

```bash
python3 inject_custom_signals.py [--dry-run]
```

Queue : `signaux_custom/queue.yaml`.

---

## 7. Retrait du lore (`undo_custom.py`)

```bash
python3 undo_custom.py [--execute]
python3 undo_custom.py --slug SLUG --type TYPE --generalisation yes|no [--execute]
```

Queue : `evenements_custom/undo_queue.yaml`

| type | generalisation | Supprime |
|---|---|---|
| `event_instance` | `no` | fichier + registre + processed/needs_review |
| `event_instance` | `yes` | archétype + toutes instances tous scénarios |
| `instance` | `no` | fichier + alliances/oppositions même scénario |
| `instance` | `yes` | archétype entité + toutes instances tous scénarios |
| `event` | — | alias event_instance + yes |
| `entite` | — | alias instance + yes |

**Garanties** : dry-run par défaut, backup `.bak`, `last_validated.json` resetté, `_entities_list.json` nettoyé, queue vidée.

**Cycle post-undo** :
```bash
python3 undo_custom.py --execute
python3 validate.py
```

---

## 8c. Cycle continu stabilisé

Les scripts d'injection lancent le cycle automatiquement. Si besoin manuel :

```
create_entities_and_instances.py  (ou inject_custom_events.py)
→ extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
```

---

## 8b. Enrichissement fiches `officialise_minimal`

```bash
python3 enrich_minimal.py --scenario NOM [--dry-run] [--limit N] [--slug SLUG]
python3 enrich_minimal.py --all [--auto-cycle]
```

Génère tous les champs placeholder via API Claude. Validation mécanique bloquante (2 retries). Reprise : `statut: officialise_enrichi`. Génère automatiquement les slugs fantômes → `queue.yaml` en fin de run.

**Cycle post-enrichissement** (manuel par défaut) :
```
enrich_minimal.py --scenario X
→ [inspecter enrich_minimal_report.md]
→ extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
```

Avec `--auto-cycle` : cycle lancé automatiquement + extraction vague 2 (validate).

**Slugs fantômes** :
```bash
python3 extract_phantom_slugs.py --source validate    # depuis validate --verbose
python3 extract_phantom_slugs.py --source enrich      # depuis enrich_minimal_report.md
python3 extract_phantom_slugs.py                      # les deux (défaut)
```

**Fix suffixes manquants** (mécanique, sans API) :
```bash
python3 fix_alliance_suffixes.py --dry-run
python3 fix_alliance_suffixes.py
```

**Requeue needs_review** :
```bash
python3 requeue_needs_review.py
```

---

## 9. Validation du vault

```bash
python3 validate.py [-v] [--report] [--localisation] [--narrative]
python3 validate.py --verbose 2>&1 | grep "narrative"
```

**9 sections :**
1. Nomenclature
2. Cohérence systémique
3. Entités/instances
4. Thématiques
5. Localisation → `localisation_review.md`
6. Références croisées
7. Matrice d'influence
8. Événements
9. **Cohérence narrative** (conditionnel sur mtime, `--narrative` pour forcer) :
   - Acteurs inactifs (whitelist `résiduel`/`mythifié`)
   - Delta overflow hors `[-20, 130]`
   - Cohérence `annee_debut`/`annee_fin`/`etat_temporel`
   - Rapport → `narrative_issues.yaml`

`last_validated.json` mis à jour si 0 erreurs.

---

## 10. Workflow manuel

```bash
python3 generate_manual.py prompt
python3 generate_manual.py status
python3 generate_manual.py save /tmp/article.txt
```

---

## 11. Scripts one-shot déjà exécutés (ne pas relancer)

- `migrate_registre.py`, `officialize_alliances.py`, `fix_impact_scale.py`

---

## 12. Garanties de sécurité communes

- `--dry-run` : appelle l'API mais n'écrit rien
- Backup `.bak` automatique avant toute écriture
- Validation mécanique avant acceptation
- Immuabilité : zones N1 jamais réécrites par l'étape 2

---

## 13. Backlog (au 25 juin 2026)

| # | Chantier | Statut |
|---|---|---|
| P6 | Modes auto/auto-suggest | ✅ Livré (auto-suggest + auto) |
| P7 | Chantier `restructure` | 🟡 Périmètre à finaliser |
| P8 | Enrichissement 426 fiches `officialise_minimal` | ✅ Livré |
| — | P4 validate.py appel review_localisation auto | ❌ Won't do |
| — | Passage Opus → Sonnet (api.py, extract_localisation, review_localisation) | ✅ Fait |
| — | `territoire` dans VALID_CATEGORIES (create_entities, validate) | ✅ Fait |
