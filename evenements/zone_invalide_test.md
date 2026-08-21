---
name: Test Fantôme des Zones Invalides
type: event_archetype
slug: zone_invalide_test
type_evenement: technological
portee: regionale
date_approximative: 2045
intensite: modérée
description: >
  Cas de test du garde-fou zone_hint — slug de zone volontairement inexistant, pour vérifier que le code l'ignore proprement avec un avertissement plutôt que de le transmettre tel quel au LLM.
variables_hint:
  - organisation_territoires
  - technologie_information
scenarios_instances:
  - breakdown
date_creation: 2026-08-13
custom_source: test_robustesse_12_aout
---

# Test Fantôme des Zones Invalides

## Description archétypale
Cas de test du garde-fou zone_hint — slug de zone volontairement inexistant, pour vérifier que le code l'ignore proprement avec un avertissement plutôt que de le transmettre tel quel au LLM.

## Instances par scénario
| Scénario | Instance | Réalisation | Impact |
|---|---|---|---|
| [[breakdown]] | [[zone_invalide_test_breakdown]] | | |
| [[fortress_world]] | — | — | — |
| [[new_sustainability]] | — | — | — |
| [[eco_communalism]] | — | — | — |
| [[policy_reform]] | — | — | — |
| [[reference]] | — | — | — |

