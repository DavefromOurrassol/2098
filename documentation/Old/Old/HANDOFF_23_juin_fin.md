# HANDOFF — 23 juin 2026 (fin de session)

---

## Ce qui a été fait aujourd'hui

### Audit du vault — état réel vs handoff
- Constat : `enrich_geographie_recursive.py` était déjà terminé sur les 6 scénarios (N1+N2+N3 présents partout).
- Constat : `extract_localisation.py` avait déjà tourné sur les instances custom.
- Constat : 3 fiches YAML cassées (`:` non quotés) avaient été corrigées manuellement dans Obsidian.

### Corrections `inject_custom_events.py` (CLOS)
Quatre bugs corrigés :
1. **`NoneType + int`** — `polarite: null` → `or 1` / `or 0` sur tous les champs arithmétiques.
2. **`Extra data`** — parser JSON remplacé par `json.JSONDecoder().raw_decode()`.
3. **YAML cassé sur `:`** — ajout de `yaml_scalar()` via `yaml.dump()`.
4. **Slug non-déterministe** — slug imposé depuis `idea['id']`, Claude ne le génère plus.

### Nettoyage des doublons (CLOS — session du jour)
Supprimés : `exode_midwest_canicule_2044`, `forum_agadez_charte_souverainete_numerique`, `great_lakes_compact_secession_eau`, `groenland_encheres_terres_rares_2041`, `saisie_convoi_arctique_nat`, `soulèvement_favelas_numeriques_sao_paulo`, `tuvalu_submersion_droit_post_territorial`, `urgence_ecologique_bassin_amazonien`, `occupation_zones_libres_rust_belt`, `secession_grands_lacs_eau`, `sao_paulo_soulèvement_anti_algorithmique`

### `rebuild_processed.py` — nouveau script (CLOS)
Reconstruit `processed.yaml` depuis les fichiers réels. 10 entrées dans `processed.yaml`.

### État validate.py en fin de session
- **0 erreurs, 0 avertissements**
- 463 entités, 561 instances, 178 fiches riches
- 23 archétypes d'événements, 43 instances d'événements
- 0 sans localisation, 0 review_manuelle

---

## Ce qu'on fait à la prochaine session (priorités)

### Priorité 1 — Nettoyer les nouveaux doublons et compléter l'injection

Un dernier run (avec l'ancien script, avant dépôt du fix slug) a créé de nouveaux doublons. À supprimer en premier :

```bash
# Doublons à supprimer (garder le slug = id de la queue)
rm ../evenements/tuvalu_submersion_souverainete_flottante.md ../event_instances/tuvalu_submersion_souverainete_flottante_new_sustainability.md
rm ../evenements/groenland_encheres_terres_rares.md ../event_instances/groenland_encheres_terres_rares_breakdown.md
rm ../evenements/secession_grands_lacs_eau_douce.md ../event_instances/secession_grands_lacs_eau_douce_breakdown.md
rm ../evenements/forum_agadez_souverainete_numerique.md ../event_instances/forum_agadez_souverainete_numerique_eco_communalism.md
rm ../evenements/exode_midwest_desertification_2044.md ../event_instances/exode_midwest_desertification_2044_breakdown.md
rm ../evenements/saisie_convoi_passage_nordouest.md ../event_instances/saisie_convoi_passage_nordouest_fortress_world.md
rm ../evenements/urgence_ecologique_amazonie_2047.md ../event_instances/urgence_ecologique_amazonie_2047_breakdown.md
rm ../evenements/communes_rust_belt_zones_libres.md ../event_instances/communes_rust_belt_zones_libres_breakdown.md
```

Vérifier les slugs qui restent correspondent bien aux `id` de la queue :
```bash
ls ../evenements/ | grep -v ".DS_Store" | grep -v "arrestation\|conflit\|effondrement\|election"
```

Puis déposer le nouveau `inject_custom_events.py` (slug déterministe), remettre la queue et relancer :
```bash
echo "needs_review:" > ../evenements_custom/needs_review.yaml
# déposer queue.yaml dans evenements_custom/
python3 inject_custom_events.py
python3 extract_localisation.py
python3 review_localisation.py --auto-resolve
python3 validate.py
```

### Priorité 2 — Fix `processed.yaml` partiel dans `inject_custom_events.py`
Quand un événement réussit sur certains scénarios mais échoue sur d'autres, il va entièrement dans `needs_review` sans tracer les scénarios réussis. À corriger dans le script.

---

## État des événements géo (fin de session)

| Événement (slug queue) | Scénarios attendus | Instances présentes |
|---|---|---|
| `crise_gouvernance_amazonie` | 6 | 1 |
| `emeutes_algorithme_sao_paulo` | breakdown, fortress_world, policy_reform, reference | 1 |
| `accord_carbone_amazonie_blocs` | new_sustainability, policy_reform, reference | 1 |
| `secession_great_lakes_compact` | breakdown, fortress_world, new_sustainability, reference | 1 |
| `exode_midwest_grands_lacs` | 6 | 1 |
| `insurrection_rust_belt` | breakdown, fortress_world, eco_communalism | 1 |
| `encheres_terres_rares_groenland` | 6 | 1 |
| `incident_passage_arctique` | fortress_world, policy_reform, reference, breakdown | 1 |
| `submersion_tuvalu_acte_fondateur` | new_sustainability, policy_reform, reference | 1 |
| `grand_forum_sahel_numerique` | eco_communalism, new_sustainability, breakdown | 1 |

---

## Fichiers livrés aujourd'hui (à déposer dans le vault)

`generator/` :
- `inject_custom_events.py` *(mis à jour — 4 bugs corrigés, slug déterministe)*
- `rebuild_processed.py` *(nouveau — script one-shot)*

`evenements_custom/` :
- `queue.yaml` *(10 événements géo prêts à injecter — disponible dans les outputs)*

---

## Bugs connus en attente

1. **`inject_custom_events.py` — `processed.yaml` non mis à jour si un scénario échoue** : priorité 2.
2. **`note_coherence` avec `:` dans les fiches existantes** : `validate.py` section 7 les détecte, à corriger manuellement si signalés.

---

## Backlog complet

| # | Chantier | Statut |
|---|---|---|
| 1 | Nettoyer doublons + compléter injection 10 événements géo | 🔴 Priorité 1 |
| 2 | Fix `processed.yaml` partiel dans `inject_custom_events.py` | 🔴 Priorité 2 |
| 3 | `validate.py` — cohérence narrative post-injection | 🟡 À coder |
| 4 | `validate.py` — appel `review_localisation` automatique | 🟡 À coder |
| 5 | `undo_custom.py` — rollback injections custom | 🟡 À coder |
| 6 | Mode `auto-balanced` `create_entities_and_instances.py` | 🟡 À coder |
| 7 | Mode `auto-balanced` `inject_custom_events.py` | 🟡 À coder |
| 8 | Chantier `restructure` | 🟢 Débloqué, à démarrer |
| 9 | Enrichissement 426 fiches `officialise_minimal` | 🟢 Gros chantier |
