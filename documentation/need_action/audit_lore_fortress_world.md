# Audit du lore — fortress_world

*Généré par `audit_lore.py` le 2026-09-25 19:16 — réécrit à chaque run, ne pas éditer. Règles : `documentation/lore_regles.yaml`.*

## Résumé

- Fiches analysées : 151 (+ 16 événements)
- Règles de lore — **erreurs : 0**, à relire : 0
- Quarantaine (fiche active localisée en zone interdite) : 0
- Transnationales localisées dans le texte (info) : 23
- Relations à sens unique : 24 — contradictoires : 0
- Relations inter-scénarios (info) : 2

*Non vérifié ici (voir `validate.py`) : slugs inexistants, relations en texte libre, zone inconnue, type_lieu, wikilinks cassés.*

## 1. Règles de lore — erreurs

Rien à signaler.

## 2. Quarantaine — fiches actives en zone interdite

Rien à signaler.

## 3. Relations contradictoires (A allié de B, B opposé à A)

Rien à signaler.

## 4. Relations à sens unique

- `anton_vasko_fortress_world` cite `administrations_de_controle_frontalier_des_blocs_fortress_world` (oppositions), pas l'inverse
- `raimon_fortress_world` cite `administrations_de_controle_frontalier_des_blocs_fortress_world` (oppositions), pas l'inverse
- `anton_vasko_fortress_world` cite `agences_de_securite_interieure_des_etats_forteresses_fortress_world` (oppositions), pas l'inverse
- `malo_fortress_world` cite `agences_de_securite_interieure_des_etats_forteresses_fortress_world` (oppositions), pas l'inverse
- `raimon_fortress_world` cite `agences_de_securite_interieure_des_etats_forteresses_fortress_world` (oppositions), pas l'inverse
- `malo_fortress_world` cite `bureaux_de_controle_frontalier_des_blocs_fermes_fortress_world` (oppositions), pas l'inverse
- `anton_vasko_fortress_world` cite `cellules_universitaires_dissidentes_des_zones_tampons_fortress_world` (oppositions), pas l'inverse
- `malo_fortress_world` cite `coalitions_des_deplaces_et_apatrides_fortress_world` (alliances), pas l'inverse
- `anton_vasko_fortress_world` cite `coalitions_des_deplaces_et_apatrides_fortress_world` (oppositions), pas l'inverse
- `hyphan_raghavan_fortress_world` cite `ergo_wian_sovereign_holdings_fortress_world` (oppositions), pas l'inverse
- `raimon_fortress_world` cite `la_garde_du_seuil_fortress_world` (alliances), pas l'inverse
- `hyphan_raghavan_fortress_world` cite `les_cycles_fortress_world` (alliances), pas l'inverse
- `anton_vasko_fortress_world` cite `les_recycleurs_fortress_world` (alliances), pas l'inverse
- `hyphan_raghavan_fortress_world` cite `les_recycleurs_fortress_world` (alliances), pas l'inverse
- `malo_fortress_world` cite `les_recycleurs_fortress_world` (alliances), pas l'inverse
- `anton_vasko_fortress_world` cite `milices_privees_de_protection_des_sites_germinaux_fortress_world` (alliances), pas l'inverse
- `malo_fortress_world` cite `milices_privees_de_protection_des_sites_germinaux_fortress_world` (oppositions), pas l'inverse
- `raimon_fortress_world` cite `milices_privees_de_protection_des_sites_germinaux_fortress_world` (oppositions), pas l'inverse
- `hyphan_raghavan_fortress_world` cite `mouvement_de_reconquete_europeenne_fortress_world` (oppositions), pas l'inverse
- `raimon_fortress_world` cite `reseau_des_cartographes_des_zones_grises_fortress_world` (alliances), pas l'inverse
- `malo_fortress_world` cite `reseaux_d_echange_clandestin_inter_zones_fortress_world` (alliances), pas l'inverse
- `raimon_fortress_world` cite `reseaux_d_echange_clandestin_inter_zones_fortress_world` (alliances), pas l'inverse
- `anton_vasko_fortress_world` cite `reseaux_de_contrebande_energetique_transfrontaliere_fortress_world` (alliances), pas l'inverse
- `raimon_fortress_world` cite `tribu_des_cinq_nations_fortress_world` (alliances), pas l'inverse
Correction automatique possible : `python3 generator/fix_alliances_oppositions.py --scenario fortress_world --reciprocite-seule --dry-run` puis sans `--dry-run`.

## 5. Règles de lore — à relire

Rien à signaler.

## 6. Transnationales mais localisées dans le texte (information)

Souvent légitime (une organisation transnationale nomme les zones où elle agit) ; à rattacher seulement si la fiche vit en réalité dans une seule zone.

- `administrations_de_controle_frontalier_des_blocs_fortress_world` — cite : Bloc Atlantique (`bloc_atlantique`)
- `agence_de_regulation_des_detroits_strategiques_ards_fortress_world` — cite : Détroit d'Ormuz (`detroit_ormuz`)
- `coalitions_geopolitiques_d_infiltration_des_modeles_climatiques_fortress_world` — cite : Paris (`paris_hors`)
- `collectifs_d_ingenieurs_dissidents_anti_militarisation_fortress_world` — cite : Bratislava-Secteur Alpha (`bratislava_secteur_alpha`)
- `consortium_des_blocs_solaires_orbitaux_concurrents_fortress_world` — cite : Bloc Atlantique (`bloc_atlantique`)
- `consortiums_de_defense_orbitale_prives_fortress_world` — cite : Bloc Atlantique (`bloc_atlantique`)
- `deepfield_institute_fortress_world` — cite : Pacte des Forteresses Souveraines (`pacte_forteresses_souveraines`)
- `dispositifs_de_surveillance_numerique_souveraine_fortress_world` — cite : Bruxelles-Forteresse (`bruxelles_forteresse`), Tours Nexus-7 (`tours_nexus7`)
- `divisions_concurrentes_nexus_biosyn_fortress_world` — cite : Corridors Gris d'Asie Centrale (`corridors_gris_asie_centrale`), Nexus BioSyn (`nexus_biosyn_division_pacifique`), Tbilissi-Nord (`tbilissi_nord_zone_franche`), Almaty (`almaty_zone_friction`)
- `factions_internes_pro_autarcie_totale_fortress_world` — cite : Midwest Désertifié (`midwest_desertifie`), Zones Industrielles Forteresses (`zone_usines_forteresses_eurasie`)
- `gelecek_meclisi_fortress_world` — cite : Corridors Gris d'Asie Centrale (`corridors_gris_asie_centrale`), Bloc Atlantique (`bloc_atlantique`)
- `instances_aria_concurrentes_des_blocs_rivaux_fortress_world` — cite : Bruxelles-Forteresse (`bruxelles_forteresse`), Genève-Bunker (`geneve_bunker`), Datacenters du Conseil de Calcul Souverain (`datacenters_conseil_eurasiatique`)
- `internationale_des_semenciers_agro_pirates_fortress_world` — cite : Nexus BioSyn (`nexus_biosyn_division_pacifique`), Tbilissi-Nord (`tbilissi_nord_zone_franche`), Marchés Gris de Casablanca-Périphérie (`marches_gris_casablanca`)
- `ironclad_logistics_fortress_world` — cite : Pacte des Forteresses Souveraines (`pacte_forteresses_souveraines`)
- `les_veilleurs_du_fleuve_fortress_world` — cite : Campements des Seuils Fermés (`campements_seuils_fermes`)
- `nexus_biosyn_fortress_world` — cite : Nexus BioSyn (`nexus_biosyn_division_pacifique`)
- `oracle_des_seuils_fortress_world` — cite : Bloc Atlantique (`bloc_atlantique`), Bloc Pacifique Nord (`bloc_pacifique_nord`)
- `populations_des_zones_deficitaires_d_optimisation_fortress_world` — cite : Zones Grises et Tampons (`zones_grises_tampons`), Corridors Gris d'Asie Centrale (`corridors_gris_asie_centrale`), Midwest Désertifié (`midwest_desertifie`)
- `reseaux_de_contrebande_energetique_transfrontaliere_fortress_world` — cite : Corridors Gris d'Asie Centrale (`corridors_gris_asie_centrale`)
- `reseaux_prives_de_securite_aux_frontieres_fortress_world` — cite : Corridors Gris d'Asie Centrale (`corridors_gris_asie_centrale`)
- `systemes_de_scoring_de_productivite_corporative_fortress_world` — cite : Zones Industrielles Forteresses (`zone_usines_forteresses_eurasie`)
- `terrashield_geoengineering_fortress_world` — cite : Amazonie (`amazonie_pacte_vert`)
- `voix_du_dehors_fortress_world` — cite : Tbilissi-Nord (`tbilissi_nord_zone_franche`), Marchés Gris de Casablanca-Périphérie (`marches_gris_casablanca`)

## 7. Relations inter-scénarios (information)

- `armada_logistique_nordique_fortress_world` → `conseil_des_etats_nordiques_integres_reference` (alliances, scénario reference)
- `armada_logistique_nordique_fortress_world` → `consortium_energetique_baltique_reference` (alliances, scénario reference)

