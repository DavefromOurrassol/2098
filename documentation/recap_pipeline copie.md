---
type: documentation
titre: Pipeline Ourrassol 2098 — Récapitulatif
date_maj: 2026-06-28
---

# Pipeline Ourrassol 2098 — Récapitulatif

Mis à jour après la session du 28 juin 2026 (migration LLM Claude/Mistral via llm_client.py, journaux locaux par zone, lignes éditoriales pro_pouvoir/opposition, date fictive dans noms de fichiers).

---

## 0. Configuration LLM

```bash
# Fournisseur par défaut : Mistral
python3 script.py

# Basculer sur Claude :
LLM_PROVIDER=claude python3 script.py

# Override modèle :
LLM_MODEL=mistral-large-latest python3 script.py
```

Variables dans `~/.zshrc` : `LLM_PROVIDER`, `LLM_MODEL`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`

---

## 1. Génération d'articles

```bash
python3 generate.py [--dry-run]
python3 generate_series.py [--dry-run] [--scenario NOM] [--validate-first]
python3 generate_manual.py prompt|status|save
```

Pipeline : `loader` → `snapshot` → `prompt_builder` (géo + journal local) → `api` → `articles/{scenario}/`

**Nom de fichier** : `YYYYMMDD_HHMMSS_{scenario}_{thematique}_article_{datefictive}.md`

**Ligne éditoriale** : `pro_pouvoir` | `opposition` — défini dans config ou aléatoire en série.

---

## 2. Journaux locaux *(nouveau)*

```bash
python3 generate_journaux.py --scenario NOM [--dry-run]
python3 generate_journaux.py --all [--update]
python3 generate_journaux.py --scenario NOM --ligne opposition
```

Génère `generator/journaux.yaml` — zones N1 uniquement.
Résolution à la génération : édition locale → réseau global → profil hardcodé → défaut.
Warning si zone sans édition : `[WARN][journal] Pas d'édition locale pour zone 'X'...`

---

## 3. Géographie du monde

```bash
python3 build_geographie_monde.py --scenario NOM [--dry-run]
python3 enrich_geographie_recursive.py --scenario NOM [--dry-run] | --all
python3 fix_lieux_residuels.py --scenario NOM [--dry-run]
```

Tous les 6 scénarios enrichis N1+N2+N3 au 25 juin 2026.

---

## 4. Localisation des entités

Champ `localisation` sur chaque fiche riche. Trois états : `extrait` | `vide` | `review_manuelle`.

```bash
python3 extract_localisation.py [--dry-run] [--scenario NOM] [--slug SLUG] [--force] [--report-only]
python3 review_localisation.py [--auto-resolve] [--dry-run] [--scenario NOM]
```

---

## 5. Injections custom — entités

```bash
python3 create_entities_and_instances.py [--dry-run]
```

**Trois modes au lancement :** `custom` | `auto` | `auto-suggest`

Cycle post-injection automatique (si ≥ 1 instance créée) :
```
extract_localisation.py → review_localisation.py --auto-resolve → validate.py
```

---

## 6. Injections custom — événements

```bash
python3 inject_custom_events.py [--dry-run]
```

**Deux modes au lancement :** `custom` | `auto`

---

## 7. Injections custom — signaux faibles

```bash
python3 inject_custom_signals.py [--dry-run]
```

---

## 8. Retrait du lore

```bash
python3 undo_custom.py [--execute]
python3 undo_custom.py --slug SLUG --type TYPE --generalisation yes|no [--execute]
```

| type | generalisation | Supprime |
|---|---|---|
| `event_instance` | `no` | fichier + registre + processed/needs_review |
| `event_instance` | `yes` | archétype + toutes instances tous scénarios |
| `instance` | `no` | fichier + alliances/oppositions même scénario |
| `instance` | `yes` | archétype entité + toutes instances tous scénarios |

---

## 8b. Enrichissement fiches `officialise_minimal`

```bash
python3 enrich_minimal.py --scenario NOM [--dry-run] [--limit N] [--slug SLUG]
python3 enrich_minimal.py --all [--auto-cycle]
```

**Slugs fantômes :**
```bash
python3 extract_phantom_slugs.py [--source enrich|validate|all] [--dry-run]
python3 fix_alliance_suffixes.py [--dry-run] [--verbose] [--scenario NOM]
python3 requeue_needs_review.py
```

---

## 8c. Cycle continu stabilisé

```
create_entities_and_instances.py  (ou inject_custom_events.py)
→ extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
→ generate_journaux.py --all --update   ← si nouvelles zones
→ generate_series.py
```

---

## 9. Validation du vault

```bash
python3 validate.py [-v] [--report] [--localisation] [--narrative]
python3 validate.py --verbose 2>&1 | grep "narrative"
```

9 sections. `last_validated.json` mis à jour si 0 erreurs.

---

## 10. Workflow manuel

```bash
python3 generate_manual.py prompt
python3 generate_manual.py status
python3 generate_manual.py save /tmp/article.txt
```

---

## 11. Scripts one-shot déjà exécutés (ne pas relancer)

`migrate_registre.py`, `officialize_alliances.py`, `fix_impact_scale.py`

---

## 12. Garanties de sécurité communes

- `--dry-run` : simule sans écrire
- Backup `.bak` automatique avant toute écriture
- Validation mécanique avant acceptation
- Zones N1 jamais réécrites par `enrich_geographie_recursive.py`

---

## 13. Backlog (au 28 juin 2026)

| # | Chantier | Statut |
|---|---|---|
| P7 | Chantier `restructure` zones géo | 🟡 Périmètre à finaliser |
| — | Migration Claude/Mistral (`llm_client.py`) | ✅ Livré |
| — | Journaux locaux par zone (`generate_journaux.py`) | ✅ Livré |
| — | Lignes éditoriales pro_pouvoir/opposition | ✅ Livré |
| — | Date fictive dans noms de fichiers | ✅ Livré |
| — | `temperature` configurable dans config.yaml | 🟢 À faire |
| — | `translate_article.py` post-génération | 🟢 À faire (2ème temps) |
| — | GUI Flask + Safari | 🟢 Spec existante |
| — | Trigger auto `generate_journaux.py` post-injection | 🟢 À faire |
| — | Test qualité Mistral sur `enrich_minimal` | 🔵 Optionnel |
| P4 | validate.py appel review_localisation auto | ❌ Won't do |
