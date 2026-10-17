# Banc d'amplitude des chocs (GAIN_CHOCS actuel : 0.25)

Gains comparés : 0.25, 0.4, 0.6. Lecture seule.

## 1. Un choc type (force 10, montée 3 ans, en 2060, persistance normale)

Écart dû au choc sur SA variable : pic (année du pic) → reste en 2098. Médiane des scénarios où la variable n'est pas saturée (niveau sans le choc < 95) ; entre crochets, le nombre de scénarios saturés.

| Variable | gain 0.25 | gain 0.4 | gain 0.6 |
|---|---|---|---|
| systeme_economique_redistribution | +2,2 (2076) → +0,8 [1] | +3,1 (2076) → +1,2 [1] | +3,7 (2077) → +1,6 [1] |
| gouvernance_institutions | +0,3 (2070) → +0,2 | +0,1 (2068) → +0,0 | +0,0 (2066) → +0,0 [1] |
| geopolitique_conflits | +2,1 (2076) → +0,8 [2] | +2,8 (2076) → +1,2 [2] | +2,9 (2076) → +1,8 [2] |
| valeurs_culture_tempo_sociale | +1,8 (2071) → +0,7 [1] | +2,5 (2070) → +0,9 [1] | +2,9 (2070) → +0,7 [1] |
| organisation_territoires | +1,4 (2070) → +0,5 [1] | +1,3 (2068) → +0,3 [1] | +0,9 (2067) → +0,1 [1] |
| sante_biotechnologies | +2,1 (2072) → +0,9 | +3,4 (2072) → +1,4 | +4,9 (2072) → +2,0 |
| frontieres_du_systeme | +2,5 (2079) → +0,4 | +3,7 (2078) → +0,6 | +4,8 (2078) → +0,6 [1] |
| technologie_information | +2,1 (2072) → +0,8 [2] | +2,2 (2072) → +1,0 [2] | +1,6 (2091) → +1,0 [2] |
| climat_environnement_global | +2,0 (2080) → +0,8 [1] | +2,8 (2080) → +1,3 [1] | +3,2 (2082) → +1,9 [1] |
| energie_ressources_critiques | +2,3 (2076) → +0,8 [1] | +3,5 (2076) → +1,2 [1] | +5,5 (2076) → +1,6 [2] |
| demographie_mobilite_humaine | +1,8 (2076) → +0,9 [1] | +2,5 (2077) → +1,5 [1] | +2,8 (2079) → +2,1 [1] |
| systemes_productifs_travail | +2,1 (2072) → +0,9 [2] | +3,2 (2072) → +1,4 [2] | +4,3 (2072) → +1,9 [2] |

## 2. Le monde actuel recalculé avec chaque gain

Écart des niveaux de 2098 à ceux du gain actuel (0.25) : moyenne des |écarts|, plus grand écart, nombre de niveaux qui bougent d'au moins 1 point, et nombre de variables ≥ 99 (saturées).

| Scénario | gain 0.25 | gain 0.4 | gain 0.6 |
|---|---|---|---|
| fortress_world (127 chocs) | moy 0,0, max +0,0, ≥1 pt : 0, ≥99 : 1 | moy 2,0, max +3,1, ≥1 pt : 10, ≥99 : 2 | moy 3,2, max +5,3, ≥1 pt : 10, ≥99 : 3 |
| new_sustainability (84 chocs) | moy 0,0, max +0,0, ≥1 pt : 0, ≥99 : 0 | moy 2,0, max -2,9, ≥1 pt : 11, ≥99 : 0 | moy 3,8, max -5,3, ≥1 pt : 11, ≥99 : 0 |
| breakdown (106 chocs) | moy 0,0, max +0,0, ≥1 pt : 0, ≥99 : 6 | moy 1,1, max +2,9, ≥1 pt : 6, ≥99 : 7 | moy 1,9, max +5,5, ≥1 pt : 6, ≥99 : 9 |
| eco_communalism (80 chocs) | moy 0,0, max +0,0, ≥1 pt : 0, ≥99 : 0 | moy 1,4, max -3,0, ≥1 pt : 7, ≥99 : 0 | moy 2,8, max -5,5, ≥1 pt : 11, ≥99 : 0 |
| policy_reform (95 chocs) | moy 0,0, max +0,0, ≥1 pt : 0, ≥99 : 0 | moy 1,4, max -3,0, ≥1 pt : 6, ≥99 : 0 | moy 2,8, max -5,5, ≥1 pt : 11, ≥99 : 0 |
| reference (126 chocs) | moy 0,0, max +0,0, ≥1 pt : 0, ≥99 : 0 | moy 2,2, max +3,0, ≥1 pt : 11, ≥99 : 0 | moy 3,7, max +5,3, ≥1 pt : 12, ≥99 : 0 |

_Rappel : le mode rupture n'est pas concerné par GAIN_CHOCS ; ce banc ne mesure que les chocs._
