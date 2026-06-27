# HANDOFF — 25 juin 2026 (fin de session)

---

## État du vault en fin de session

```
Entités       : 463
Instances      : 561
Thématiques   : 20
Fiches riches : 204 (0 sans localisation, 0 review_manuelle)
Archétypes    : 15 événements
Instances evt : 69 événements
Erreurs       : 0
Avertissements: 0
Cohérence narrative : OK
```

---

## Ce qui a été accompli aujourd'hui

### 1. P1 — Fiches `note_coherence` YAML cassées (CLOS)
6 fiches corrigées avant le début de session.

### 2. P2 — `inject_custom_events.py` — `processed.yaml` partiel (CLOS)
`process_idea()` retourne `injected_scenarios` + `failed_scenarios` séparément.
`main()` écrit dans les deux fichiers indépendamment :
- Succès partiel → `status: partial` dans `processed.yaml` + scénarios échoués dans `needs_review.yaml`
- Cas extrême 0 résultats → tout en `needs_review.yaml`

### 3. P3 — `validate.py` — cohérence narrative post-injection (CLOS)
Section 9/9 ajoutée. Sections renumérotées 1→9.

- Scan conditionnel sur mtime `event_instances/` via `generator/last_validated.json`
- Flag `--narrative` / `-n` pour forcer
- **Vérif A** — acteurs : suffixe scénario + `etat_temporel` actif (whitelist `résiduel`/`mythifié`)
- **Vérif B** — delta overflow hors `[-20, 130]`
- **Vérif C** — instances : `annee_debut` absent (C1), `annee_fin` < `annee_debut` (C2), `annee_fin` ≤ 2097 + etat actif (C3), `disparu` sans `annee_fin` (C4)
- Rapport : `documentation/need_action/narrative_issues.yaml`

### 4. P4 — `validate.py` — appel `review_localisation` automatique (WON'T DO)

### 5. P5 — `undo_custom.py` — nouveau script (CLOS + correction)
Retire entités/événements du lore. Interface double : queue YAML ou argument direct.

Queue : `evenements_custom/undo_queue.yaml`
```yaml
undo:
  - type: event_instance   # | instance | event | entite
    slug: mon_slug
    generalisation: no     # | yes
```

Argument direct :
```bash
python3 undo_custom.py --slug mon_slug --type instance --generalisation yes --execute
```

- `generalisation: no` — fichier ciblé + dépendances directes
- `generalisation: yes` — archétype + tout tous scénarios
- Backup `.bak`, dry-run par défaut, `last_validated.json` resetté, queue vidée, **`_entities_list.json` nettoyé**

Cycle post-undo :
```bash
python3 undo_custom.py --execute
python3 validate.py
```

### 6. `inject_custom_events.py` — mode auto (CLOS)
Nouveau mode interactif au lancement (`custom` ou `auto`).

Mode `auto` :
1. Analyse couverture vault : géo, types d'événements, variables, **zones absentes** (depuis `geographie/{scenario}.md`)
2. Génère N idées → ajout dans `evenements_custom/queue.yaml` sans injection
3. Tu inspectes, puis relances en mode `custom`

```bash
python3 inject_custom_events.py
# → custom ou auto ?
# → auto : Nombre d'idées ? | Scénario ciblé ?
```

### 7. `create_entities_and_instances.py` — mode auto-suggest (CLOS)
Nouveau mode `auto-suggest` en plus de `custom` et `auto`.

Mode `auto-suggest` :
1. Analyse couverture instances + **zones absentes** par scénario
2. Génère N idées → ajout dans `entites_custom/queue.yaml` sans injection
3. Tu inspectes, puis relances en mode `custom`

```bash
python3 create_entities_and_instances.py
# → custom, auto ou auto-suggest ?
```

### 8. Cycle post-injection automatique (CLOS)
Les deux scripts (`create_entities_and_instances.py` + `inject_custom_events.py`) lancent automatiquement après une injection réussie (hors dry-run) :

```
extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
```

Via `subprocess`, avec affichage de chaque commande. S'arrête si une étape échoue.

---

## Fichiers livrés aujourd'hui (à déposer dans `generator/`)

- `inject_custom_events.py` *(P2 + mode auto + cycle post-injection)*
- `validate.py` *(P3 — sections 1→9)*
- `undo_custom.py` *(P5 — nouveau + fix _entities_list.json)*
- `create_entities_and_instances.py` *(mode auto-suggest + cycle post-injection)*

---

## Cycle continu stabilisé

Les scripts d'injection lancent désormais le cycle automatiquement.
Si tu lances manuellement :

```
create_entities_and_instances.py  (ou inject_custom_events.py)
→ [cycle auto] extract_localisation.py
→ [cycle auto] review_localisation.py --auto-resolve
→ [cycle auto] validate.py
```

Après suppression :
```
undo_custom.py --execute
→ validate.py  (manuel)
```

---

## Todolist — prochaine session

### 🟡 Priorité 1 — Tester les nouveaux modes en conditions réelles
- `inject_custom_events.py` mode `auto` : vérifier la qualité des idées générées
- `create_entities_and_instances.py` mode `auto-suggest` : idem
- Vérifier que le cycle post-injection s'enchaîne proprement

### 🟢 Priorité 2 — Chantier `restructure`
Débloqué depuis que `localisation` existe. Périmètre exact à définir.

### 🟢 Priorité 3 — Enrichissement 426 fiches `officialise_minimal`
Gros chantier. Débloquerait les niveaux 2-3 géographiques plus denses.

---

## Bugs connus résiduels

Aucun.
