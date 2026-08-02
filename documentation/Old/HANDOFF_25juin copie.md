# HANDOFF — 25 juin 2026 (fin de session)

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
Cohérence narrative : OK
```

---

## Ce qui a été accompli aujourd'hui

### 1. P1 — Fiches `note_coherence` YAML cassées (CLOS)
6 fiches corrigées manuellement avant le début de session. Vault propre au démarrage.

### 2. P2 — `inject_custom_events.py` — `processed.yaml` partiel (CLOS)

`process_idea()` retourne désormais `injected_scenarios` et `failed_scenarios` séparément.
`main()` écrit dans les deux fichiers indépendamment :

| Résultat | `processed.yaml` | `needs_review.yaml` |
|---|---|---|
| Succès total | `status: injected` + liste scénarios | — |
| Succès partiel | `status: partial` + scénarios réussis | scénarios échoués uniquement |
| Échec total | — | tout l'outcome |
| 0 résultats (exception avant boucle) | — | tout l'outcome |

### 3. P3 — `validate.py` — cohérence narrative post-injection (CLOS)

Nouvelle section 9/9 ajoutée. Sections renumérotées (1→9 au lieu de 1→8).

**Déclenchement conditionnel** :
- Ne tourne que si des `event_instances` ont été modifiées depuis `generator/last_validated.json`
- `last_validated.json` mis à jour si `result.ok` en fin de run
- Flag `--narrative` / `-n` pour forcer le scan

**Vérifications A — acteurs dans event_instances** :
- A1 : suffixe scénario cohérent (ex. `_breakdown`)
- A2 : `etat_temporel` ∉ `{disparu, historique}` — sauf si `age_historique` ∈ `{résiduel, mythifié}` (whitelist narrative)

**Vérifications B — delta overflow** :
- `level + delta_reel` hors `[-20, 130]` → warning (probable erreur de saisie)
- Seuil délibérément large pour ne pas fausser positiver sur `breakdown` (variables naturellement saturées)

**Vérifications C — instances** :
- C1 : `annee_debut` absent → warning
- C2 : `annee_fin` < `annee_debut` → erreur
- C3 : `annee_fin` ≤ 2097 + `etat_temporel` actif → warning
- C4 : `etat_temporel: disparu` sans `annee_fin` → warning

**Rapport** : `documentation/need_action/narrative_issues.yaml`

**Consulter les warnings** :
```bash
python3 validate.py --verbose        # détail terminal
python3 validate.py --report         # génère validation_report.md (Obsidian)
python3 validate.py --verbose 2>&1 | grep "narrative"   # narratif uniquement
```

### 4. P4 — `validate.py` — appel `review_localisation` automatique (WON'T DO)
Le cycle continu existant est suffisant. L'automatiser dans `validate.py` rendrait le comportement moins prévisible sans gain réel.

### 5. P5 — `undo_custom.py` — nouveau script (CLOS)

Retire entités/événements du lore. Interface double : queue YAML ou argument direct.

**Queue** : `evenements_custom/undo_queue.yaml`
```yaml
undo:
  - type: event_instance
    slug: mon_evenement_breakdown
    generalisation: no
  - type: instance
    slug: mon_entite_reference
    generalisation: yes
```

**Argument direct** :
```bash
python3 undo_custom.py --slug mon_evenement_breakdown --type event_instance --generalisation no
python3 undo_custom.py --slug mon_entite --type entite --generalisation yes --execute
```

**Comportement `generalisation`** :

| type | generalisation | Supprime |
|---|---|---|
| `event_instance` | `no` | fichier event_instance + ligne registre + processed/needs_review |
| `event_instance` | `yes` | archétype event + toutes event_instances tous scénarios + registre |
| `instance` | `no` | fichier instance + références alliances/oppositions même scénario |
| `instance` | `yes` | archétype entité + toutes instances tous scénarios + leurs références |
| `event` | — | alias `event_instance` + `generalisation: yes` |
| `entite` | — | alias `instance` + `generalisation: yes` |

**Sécurité** :
- Dry-run par défaut — `--execute` pour écrire réellement
- Backup `.bak` automatique avant toute suppression
- `last_validated.json` resetté après exécution
- Queue vidée après `--execute`

**Cycle post-undo** :
```bash
python3 undo_custom.py --execute
python3 validate.py
```

---

## Fichiers livrés aujourd'hui (à déposer dans `generator/`)

- `inject_custom_events.py` *(mis à jour — P2)*
- `validate.py` *(mis à jour — P3, sections 1→9)*
- `undo_custom.py` *(nouveau — P5)*

---

## Cycle continu stabilisé

Après chaque ajout d'entités ou d'événements :
```
create_entities_and_instances.py  (ou inject_custom_events.py)
→ extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
```

Après suppression d'entités ou d'événements :
```
undo_custom.py --execute
→ validate.py
```

---

## Todolist — prochaine session

### 🟡 Priorité 1 — Valider `undo_custom.py` en conditions réelles
Injecter un événement ou une entité test, puis le retirer avec `undo_custom.py --execute`, vérifier que `validate.py` est propre.

### 🟡 Priorité 2 — Modes `auto-balanced`
- `create_entities_and_instances.py` : analyse déséquilibres géo + génération ciblée
- `inject_custom_events.py` : même principe côté événements

### 🟢 Priorité 3 — Chantier `restructure`
Débloqué depuis que `localisation` existe. Périmètre exact à définir en début de session.

### 🟢 Priorité 4 — Enrichissement 426 fiches `officialise_minimal`
Gros chantier. Débloquerait les niveaux 2-3 géographiques plus denses.

---

## Documentation à mettre à jour

- `manuel_utilisateur.md` — section `undo_custom.py` + `validate.py` options narratives ✅ livré
- `recap_pipeline.md` — section 7 validate.py + section 8 undo_custom.py ✅ livré
