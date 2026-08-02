---
type: documentation
titre: Pipeline Ourrassol 2098 — Récapitulatif
date_maj: 2026-06-25
---

# Pipeline Ourrassol 2098 — Récapitulatif

Vue d'ensemble du pipeline complet. Mis à jour après la session du 25 juin 2026 (P2 inject_custom_events, P3 validate.py cohérence narrative, P5 undo_custom.py).

---

## 1. Génération d'articles

### Fichiers à configurer

**`generator/config.yaml`** — un seul article
```yaml
scenario: reference
thematique: sciences_technologies
article:
  titre_suggere: ""
  angle_specifique: ""
  longueur: auto
```

**`generator/config_series.yaml`** — plusieurs articles
```yaml
scenario: reference
thematiques:
  - politique
  - sciences_technologies
articles_par_thematique: 1
longueur: auto
```

### Commandes

```bash
python3 generate.py --dry-run
python3 generate.py
python3 generate_series.py --dry-run
python3 generate_series.py [--scenario NOM]
```

### Ce que fait le pipeline à chaque génération
1. Charge la thématique (`loader.load_thematique`)
2. Construit le snapshot du monde (`snapshot.build_snapshot`)
3. Assemble le prompt complet (`prompt_builder.build_prompt`) avec filtrage géographique
4. Appelle l'API (`api.generate_article`), sauvegarde dans `articles/{scenario}/`

---

## 2. Le prompt assemblé

| Section | Source | Toujours présente ? |
|---|---|---|
| Monde 2098 | snapshot (scénario) | Oui |
| Géographie de ce monde | `geographie/{scenario}.md` | Si fichier existe |
| État des variables | snapshot + variables | Oui |
| Tensions systémiques | snapshot | Oui |
| Trajectoire 2025→2098 | snapshot + `trajectory_usage.json` | Oui |
| Entités canoniques | snapshot (`filtered_instances`) | Si instances existent |
| Consigne de rédaction | thématique + config | Oui |

**Filtrage géographique** : section "Ancrage de cet article" en tête, zones des instances vedettes + leurs parents, plafond `thematique.echelle`.

---

## 3. Géographie du monde

Fichiers : `geographie/{scenario}.md`

### État au 25 juin 2026

| Scénario | Enrichi |
|---|---|
| reference | ✓ N1+N2 |
| eco_communalism | ✓ N1+N2+N3 |
| breakdown | ✓ N1+N2+N3 |
| fortress_world | ✓ N1+N2+N3 |
| new_sustainability | ✓ N1+N2+N3 |
| policy_reform | ✓ N1+N2+N3 |

### Commandes

```bash
python3 build_geographie_monde.py --scenario NOM [--dry-run]
python3 enrich_geographie_recursive.py --scenario NOM [--dry-run] | --all
python3 fix_lieux_residuels.py --scenario NOM [--dry-run]
```

---

## 4. Localisation des entités

Champ `localisation` sur chaque fiche riche (instance non-minimale + event_instance) :

```yaml
localisation:
  zone: slug_zone_existante
  lieu: texte_libre
  type_lieu: ville | region | infrastructure | site_strategique
```

Trois états : `extrait` | `vide` (transnationale) | `review_manuelle`

### Commandes

```bash
python3 extract_localisation.py [--dry-run] [--scenario NOM] [--slug SLUG] [--force] [--report-only]
python3 review_localisation.py [--auto-resolve] [--dry-run] [--scenario NOM]
```

---

## 5. Injections custom

Trois pipelines parallèles : `{type}_custom/queue.yaml` → script → `processed.yaml` (succès) ou `needs_review.yaml` (échec après 2 corrections).

### Entités (`create_entities_and_instances.py`)

```bash
python3 create_entities_and_instances.py [--dry-run]
```

Modes au lancement :
- **`custom`** : traite `entites_custom/queue.yaml`. Champs : `nom`, `category`, `role`, `etat`, `scenario_ref`, `scenario_hint`.
- **`auto`** : N entités inventées par Claude, pas de contrôle géographique.

### Événements (`inject_custom_events.py`)

```bash
python3 inject_custom_events.py [--dry-run]
```

Queue : `evenements_custom/queue.yaml`. Champs : `id`, `description`, `portee`, `date_approximative`, `intensite`, `scenarios`, `variables_hint(_count)`, `acteurs_hint(_count)`, `source`.

**Comportement `processed.yaml`** (depuis le 25 juin) :
- Succès partiel → `status: partial` dans `processed.yaml` + scénarios échoués dans `needs_review.yaml`
- Plus de perte silencieuse des scénarios réussis en cas d'échec partiel

### Signaux faibles (`inject_custom_signals.py`)

```bash
python3 inject_custom_signals.py [--dry-run]
```

Queue : `signaux_custom/queue.yaml`.

---

## 6. Retrait du lore (`undo_custom.py`)

Retire proprement entités, instances, événements et event_instances du lore.

```bash
python3 undo_custom.py                          # dry-run depuis undo_queue.yaml
python3 undo_custom.py --execute                # supprime réellement
python3 undo_custom.py --slug SLUG --type TYPE --generalisation yes|no [--execute]
```

**Queue** : `evenements_custom/undo_queue.yaml`
```yaml
undo:
  - type: event_instance   # | instance | event | entite
    slug: mon_slug
    generalisation: no     # | yes
```

**`generalisation: no`** — fichier ciblé + dépendances directes (registre, alliances/oppositions).
**`generalisation: yes`** — archétype + toutes instances/event_instances tous scénarios + dépendances.

**Garanties** : backup `.bak`, dry-run par défaut, `last_validated.json` resetté, queue vidée.

**Cycle post-undo** :
```bash
python3 undo_custom.py --execute
python3 validate.py
```

---

## 7. Cycle continu stabilisé

Après chaque ajout d'entités ou d'événements :
```
create_entities_and_instances.py  (ou inject_custom_events.py)
→ extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
```

Après suppression :
```
undo_custom.py --execute
→ validate.py
```

---

## 8. Validation du vault (`validate.py`)

```bash
python3 validate.py              # 9 sections
python3 validate.py -v           # détail avertissements terminal
python3 validate.py --report     # génère validation_report.md (Obsidian)
python3 validate.py --localisation  # scan localisation uniquement
python3 validate.py --narrative  # force scan cohérence narrative
python3 validate.py --verbose 2>&1 | grep "narrative"  # warnings narratifs uniquement
```

**9 sections** :
1. Nomenclature
2. Cohérence systémique
3. Entités/instances
4. Thématiques
5. Localisation → génère `localisation_review.md`
6. Références croisées
7. Matrice d'influence
8. Événements (archétypes, instances, YAML cassé)
9. **Cohérence narrative** (depuis le 25 juin) :
   - Conditionnel : tourne si event_instances modifiées depuis `last_validated.json`
   - Acteurs inactifs dans événements (whitelist `résiduel`/`mythifié`)
   - Delta overflow hors `[-20, 130]`
   - Cohérence `annee_debut`/`annee_fin`/`etat_temporel` sur instances
   - Rapport → `documentation/need_action/narrative_issues.yaml`

---

## 9. Workflow manuel

```bash
python3 generate_manual.py prompt
python3 generate_manual.py status
python3 generate_manual.py save /tmp/article.txt
```

---

## 10. Scripts one-shot déjà exécutés (ne pas relancer)

- **`migrate_registre.py`** : migration registre vers format hybride 6 colonnes
- **`officialize_alliances.py`** : alliances/oppositions texte libre → slugs réels
- **`fix_impact_scale.py`** : correction rétroactive `impact_local`/`impact_systemique_global`

---

## 11. Garanties de sécurité communes

- **`--dry-run`** : appelle l'API mais n'écrit rien
- **Backup `.bak`** automatique avant toute écriture
- **Validation mécanique** : slugs, variables, relations vérifiés avant acceptation
- **Immuabilité** : zones niveau 1 jamais réécrites par l'étape 2

---

## 12. Backlog (au 25 juin 2026)

| # | Chantier | Statut |
|---|---|---|
| P1 | Valider `undo_custom.py` en conditions réelles | 🔴 À faire |
| P2 | Modes `auto-balanced` entités + événements | 🟡 À coder |
| P3 | Chantier `restructure` | 🟢 Débloqué, périmètre à définir |
| P4 | Enrichissement 426 fiches `officialise_minimal` | 🟢 Gros chantier |
| — | P4 validate.py appel review_localisation auto | ❌ Won't do |
