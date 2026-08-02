# HANDOFF — 23 juin 2026 (fin de session)

---

## État du vault en fin de session

```
Entités       : 463
Instances     : 561
Thématiques   : 20
Fiches riches : 204 (0 sans localisation, 0 review_manuelle)
Archétypes    : 15 événements
Instances evt : 69 événements
Erreurs       : 0
Avertissements: 0
```

---

## Ce qui a été accompli aujourd'hui

### 1. Audit du vault
- `enrich_geographie_recursive.py` était déjà terminé sur les 6 scénarios (N1+N2+N3 présents).
- `extract_localisation.py` avait déjà tourné sur les instances custom.
- 3 fiches YAML cassées avaient été corrigées manuellement dans Obsidian.

### 2. `inject_custom_events.py` — 6 bugs corrigés (CLOS)

| # | Bug | Cause | Fix |
|---|---|---|---|
| 1 | `NoneType + int` (arithmétique) | `polarite/delta_level/duree: null` retourné par Claude | `or 0` / `or 1` sur tous les champs arithmétiques |
| 2 | `Extra data` (JSON) | Claude ajoutait du texte après l'objet JSON | `json.JSONDecoder().raw_decode()` |
| 3 | YAML cassé sur `:` (champ `name`) | Pas de quotation automatique | `yaml_scalar()` via `yaml.dump()` |
| 4 | Slug non-déterministe | Claude inventait un slug différent à chaque run | Slug imposé depuis `idea['id']` |
| 5 | 1 seul scénario injecté | Exception sur scénario 2 remontait et abandonnait tout | `try/except` par scénario dans la boucle |
| 6 | YAML cassé sur `:` (champ `note_coherence`) | `note_coherence` non passé par `yaml_scalar()` | `yaml_scalar()` appliqué à `note_coherence` |
| BONUS | `table_start = None` dans `regenerate_registre` | Registre utilise `| --- |` (espaces) détecté comme `|---` | Détection robuste du séparateur Markdown |

### 3. Nettoyage des doublons (CLOS)
Plusieurs runs ratés avaient créé des archétypes + instances en double. Tous supprimés.

### 4. `rebuild_processed.py` — nouveau script (CLOS)
Reconstruit `processed.yaml` depuis les fichiers réels dans `event_instances/`. 

### 5. Injection des 10 événements géo (CLOS)
Tous les événements géo sont injectés sur leurs scénarios respectifs :

| Événement | Instances |
|---|---|
| `crise_gouvernance_amazonie` | 6 (tous scénarios) |
| `communes_rust_belt_zones_libres` | 3 (breakdown, fortress_world, eco_communalism) |
| `emeutes_algorithme_sao_paulo` | 4 (breakdown, fortress_world, policy_reform, reference) |
| `accord_carbone_amazonie_blocs` | 3 (new_sustainability, policy_reform, reference) |
| `secession_great_lakes_compact` | 4 (breakdown, fortress_world, new_sustainability, reference) |
| `exode_midwest_grands_lacs` | 6 (tous scénarios) |
| `insurrection_rust_belt` | 3 (breakdown, fortress_world, eco_communalism) |
| `encheres_terres_rares_groenland` | 6 (tous scénarios) |
| `incident_passage_arctique` | 4 (breakdown, fortress_world, policy_reform, reference) |
| `submersion_tuvalu_acte_fondateur` | 3 (new_sustainability, policy_reform, reference) |
| `grand_forum_sahel_numerique` | 3 (eco_communalism, new_sustainability, breakdown) |

### 6. Localisation + validate (CLOS)
- `extract_localisation.py` + `review_localisation.py --auto-resolve` sur toutes les nouvelles instances.
- `validate.py` : 0 erreurs, 0 avertissements.

---

## Fichiers livrés aujourd'hui (à déposer dans le vault)

`generator/` :
- `inject_custom_events.py` *(mis à jour — 6 bugs corrigés)*
- `rebuild_processed.py` *(nouveau)*

---

## Todolist — prochaine session

### 🔴 Priorité 1 — Fiches `note_coherence` YAML cassées existantes
6 fiches écrites avant le fix `yaml_scalar(note_coherence)` ont encore un `:` non quoté. Corriger avec :
```bash
python3 -c "
import re
files = [
    '../event_instances/accord_carbone_amazonie_blocs_reference.md',
    '../event_instances/communes_rust_belt_zones_libres_eco_communalism.md',
    '../event_instances/crise_gouvernance_amazonie_new_sustainability.md',
    '../event_instances/crise_gouvernance_amazonie_reference.md',
    '../event_instances/grand_forum_sahel_numerique_eco_communalism.md',
    '../event_instances/secession_great_lakes_compact_fortress_world.md',
]
for f in files:
    text = open(f, encoding='utf-8').read()
    fixed = re.sub(
        r'^(note_coherence: )(.+)$',
        lambda m: m.group(1) + '\"' + m.group(2).strip('\"') + '\"',
        text, flags=re.MULTILINE
    )
    open(f, 'w', encoding='utf-8').write(fixed)
    print('OK:', f.split('/')[-1])
"
python3 validate.py
```

### 🔴 Priorité 2 — `processed.yaml` partiel
Quand un événement réussit sur N scénarios et échoue sur M, il va entièrement en `needs_review` sans tracer les N réussis. À corriger dans `inject_custom_events.py` : écrire dans `processed.yaml` les scénarios réussis même si le statut global est `needs_review`.

### 🟡 Priorité 3 — `validate.py` — cohérence narrative post-injection
Scan des contradictions entre entités après injection d'événements custom. Appel API optionnel. Non codé.

### 🟡 Priorité 4 — `validate.py` — appel `review_localisation` automatique
Intégrer le scan `review_manuelle` dans `validate.py` pour déclencher automatiquement la review. Non codé.

### 🟡 Priorité 5 — `undo_custom.py`
Script de rollback pour les injections custom. Isolé, sans dépendance bloquante. Non codé.

### 🟡 Priorité 6 — Modes `auto-balanced`
- `create_entities_and_instances.py` : analyse déséquilibres géo + génération ciblée
- `inject_custom_events.py` : même principe côté événements
Non codés.

### 🟢 Priorité 7 — Chantier `restructure`
Débloqué depuis que `localisation` existe. Périmètre exact à définir en début de session.

### 🟢 Priorité 8 — Enrichissement 426 fiches `officialise_minimal`
Gros chantier. Débloquerait les niveaux 2-3 géographiques plus denses. Prérequis : enrichissement géo récursif terminé sur tous les scénarios (déjà fait).

---

## Cycle continu stabilisé

Après chaque ajout d'entités ou d'événements :
```
inject_custom_events.py
→ extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
```

---

## Bugs connus résiduels

1. **`note_coherence` avec `:` dans les 6 fiches existantes** — voir Priorité 1.
2. **`processed.yaml` partiel** — voir Priorité 2.
3. **`needs_review.yaml` — doublon `emeutes_algorithme_sao_paulo`** — présent deux fois. Sans impact fonctionnel mais à nettoyer manuellement si besoin.
