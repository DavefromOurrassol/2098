# Audit du lore — dernier lancement (2026-10-24 07:47)

Scénarios : breakdown

---

# Audit du lore — breakdown

*Généré par `audit_lore.py` le 2026-10-24 07:47 — réécrit à chaque run, ne pas éditer. Règles : `documentation/lore_regles.yaml`.*

## Résumé

- Fiches analysées : 149 (+ 17 événements)
- Règles de lore — **erreurs : 0**, à relire : 18
- Quarantaine (fiche active localisée en zone interdite) : 0
- Transnationales localisées dans le texte (info) : 6
- Relations à sens unique à corriger : 0 — contradictoires : 0
- Relations inter-scénarios (erreurs) : 0

*Non vérifié ici (voir `validate.py`) : slugs inexistants, relations en texte libre, zone inconnue, type_lieu, wikilinks cassés.*

## 1. Règles de lore — erreurs

Rien à signaler.

## 2. Quarantaine — fiches actives en zone interdite

Rien à signaler.

## 3. Relations contradictoires (A allié de B, B opposé à A)

Rien à signaler.

## 4. Relations à sens unique

Rien à corriger.

## 5. Règles de lore — à relire

**agence_stabilisation_climatique_disparu_2076** — Le Bureau de Coordination d'Urgence Climatique (Résidu AMSC) disparaît en 2076 avec la destruction de Genève (destruction_geneve_2076) : toute mention au présent après 2076 est fausse.
- `agence_stabilisation_climatique_breakdown` (instance, name) — **Résidu AMSC** : « Résidu AMSC — Bureau de Coordination d'Urgence Climatique »
- `agence_stabilisation_climatique_breakdown` (instance, name) — **Bureau de Coordination d'Urgence Climatique** : « Résidu AMSC — Bureau de Coordination d'Urgence Climatique »
- `agence_stabilisation_climatique_breakdown` (instance, localisation.lieu) — **Bureau de Coordination d'Urgence Climatique** : « Genève — tour abritant le Bureau de Coordination d'Urgence Climatique »
- `agence_stabilisation_climatique_breakdown` (instance, description_journalistique) — **Bureau de Coordination d'Urgence Climatique** : « Le Bureau de Coordination d'Urgence Climatique — dernier souffle de l'ancienne AMSC — émettait chaque semaine des « alertes planétaires » en trois langues mortes de la diplomatie internationale. »

**geneve_bunker_institutions_disparu_2076** — Le Résidu de Genève — Le Palais des Fantômes disparaît en 2076 avec la destruction de Genève (destruction_geneve_2076) : toute mention au présent après 2076 est fausse.
- `geneve_bunker_institutions_breakdown` (instance, name) — **Palais des Fantômes** : « Résidu de Genève — Le Palais des Fantômes »

**iran_dans_arc_eurasien_2058** — Depuis le Pacte de Tabriz (2058), l'Iran fait partie de l'Arc Eurasien Central et n'appartient plus à la Zone Golfe Persique–Levant : à relire si la phrase le rattache encore au Golfe après 2058.
- `pacte_tabriz_2058_breakdown` (evenement, realisation) — **Iran + Zone Golfe** : « Après des années d'isolement économique et de blocus énergétique imposé par la Zone Golfe Persique–Levant, l'Iran, exsangue, se tourne vers l'Arc Eurasien Central. »

**tour_bcuc_geneve_disparu_2076** — La Tour BCUC — Le Comptoir des Ruines disparaît en 2076 avec la destruction de Genève (destruction_geneve_2076) : toute mention au présent après 2076 est fausse.
- `destruction_geneve_2076_breakdown` (evenement, description) — **Tour BCUC** : « Les bâtiments des Archives Neutres, de l'Agence de Stabilisation Climatique et de la Tour BCUC s'effondrent sous l'effet des ondes de choc. »
- `destruction_geneve_2076_breakdown` (evenement, description) — **Tour Bcuc** : « Les bâtiments des Archives Neutres, de l'Agence de Stabilisation Climatique et de la Tour BCUC s'effondrent sous l'effet des ondes de choc. »
- `tour_bcuc_geneve_breakdown` (instance, name) — **Tour BCUC** : « Tour Bcuc Genève — Le Comptoir des Ruines »
- `tour_bcuc_geneve_breakdown` (instance, name) — **Tour Bcuc** : « Tour Bcuc Genève — Le Comptoir des Ruines »
- `tour_bcuc_geneve_breakdown` (instance, name) — **Comptoir des Ruines** : « Tour Bcuc Genève — Le Comptoir des Ruines »
- `tour_bcuc_geneve_breakdown` (instance, localisation.lieu) — **Tour BCUC** : « Tour BCUC, Genève »
- `tour_bcuc_geneve_breakdown` (instance, localisation.lieu) — **Tour Bcuc** : « Tour BCUC, Genève »
- `tour_bcuc_geneve_breakdown` (instance, role_dans_scenario) — **Tour BCUC** : « Vestige d'une ancienne institution financière internationale basée à Genève, la Tour Bcuc a fonctionné jusqu'en 2076 comme une structure hybride semi-autonome après l'effondrement des organes de régulation globaux. »
- `tour_bcuc_geneve_breakdown` (instance, role_dans_scenario) — **Tour Bcuc** : « Vestige d'une ancienne institution financière internationale basée à Genève, la Tour Bcuc a fonctionné jusqu'en 2076 comme une structure hybride semi-autonome après l'effondrement des organes de régulation globaux. »
- `tour_bcuc_geneve_breakdown` (instance, responsabilites) — **Tour BCUC** : « La Tour Bcuc émettait des certificats de reconnaissance de dette inter-fragments, tenait un registre des accords économiques passés entre anciennes entités étatiques européennes, et proposait une chambre d'arbitrage informelle pour les liti… »
- `tour_bcuc_geneve_breakdown` (instance, responsabilites) — **Tour Bcuc** : « La Tour Bcuc émettait des certificats de reconnaissance de dette inter-fragments, tenait un registre des accords économiques passés entre anciennes entités étatiques européennes, et proposait une chambre d'arbitrage informelle pour les liti… »
- `tour_bcuc_geneve_breakdown` (instance, description_journalistique) — **Comptoir des Ruines** : « Le Comptoir des Ruines — surnom que lui avaient collé les diplomates de la Ligue Méditerranéenne — émettait ses fameux « certificats Bcuc », ces documents en papier pelure sécurisé que les fragments d'États acceptaient comme base de négocia… »

## 6. Transnationales mais localisées dans le texte (information)

Souvent légitime (une organisation transnationale nomme les zones où elle agit) ; à rattacher seulement si la fiche vit en réalité dans une seule zone.

- `blocs_de_controle_des_couloirs_d_approvisionnement_strategiques_breakdown` — cite : Corridor Oural-Caspien (`corridor_oural_caspien`)
- `enclaves_technologiques_survivantes_breakdown` — cite : Enclaves Finlandaises (`enclaves_finlandaises`)
- `factions_etatiques_residuelles_de_souverainete_hydrique_breakdown` — cite : Kivu Disputé (`kivu_dispute`)
- `flux_migratoires_non_integrables_breakdown` — cite : Arc Sahélo-Méditerranéen (`arc_sahelo_mediterraneen`)
- `milices_contractuelles_des_anciens_etats_membres_breakdown` — cite : Corridor des Lithiums (`corridor_lithium_bouches`)
- `reseau_des_organisations_humanitaires_hors_cadre_onusien_breakdown` — cite : Bassorah (`bassorah_exode`)

## 7. Relations inter-scénarios (erreurs : les scénarios sont des mondes parallèles)

Rien à signaler.

