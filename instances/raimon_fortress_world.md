---
name: Raimon des Cinq Passages
type: instance
slug: raimon_fortress_world
entite: raimon
scenario: fortress_world
localisation:
  zone: tolosa_saint_sernin_du_desert
  lieu: Tolosa — Saint-Sernin-du-Désert
  type_lieu: ville

type_dans_scenario: humain

role_dans_scenario: >
  Fils de Guilhelma, jeune guerrier de la tribu des Cinq Nations à Tolosa — Saint-Sernin-du-Désert, Raimon incarne la mémoire vivante des passages vers les Pyrénées et Al-Hima. Dans un monde où les frontières sont devenues des forteresses, il est l'un des derniers à connaître les chemins oubliés qui relient les blocs fragmentés. Son rôle oscille entre la préservation des savoirs ancestraux de sa tribu et la négociation avec les réseaux clandestins qui dépendent de ces corridors pour survivre. Il est à la fois un gardien des marges et un acteur clé des dynamiques de pouvoir informel, où la maîtrise des flux humains et matériels devient une monnaie d'échange précieuse.

responsabilites: >
  Raimon guide les convois de contrebandiers et de déplacés à travers les zones grises des Pyrénées, évitant les drones de surveillance des blocs et les milices privées. Il cartographie les passages sûrs pour les réseaux de passeurs d'information et de ressources, tout en protégeant les sites sacrés de sa tribu des pillages des complexes militaro-industriels. Il négocie également avec les *Gardiens du Miroir* (Al-Haras al-ʿAtabah) pour sécuriser les accès à Al-Hima, une zone tampon stratégique entre les blocs eurasiatique et atlantique.

impact_local: 4
impact_systemique_global: 2

variables_influencees:
    - geopolitique_conflits
    - demographie_mobilite_humaine
    - organisation_territoires

zone_geographique:
    - régionale

zone_systemique:
    - sécurité
    - infrastructure
    - société

alliances:
    - tribu_des_cinq_nations_fortress_world
    - reseau_des_cartographes_des_zones_grises_fortress_world
    - reseaux_d_echange_clandestin_inter_zones_fortress_world
    - la_garde_du_seuil_fortress_world

oppositions:
    - administrations_de_controle_frontalier_des_blocs_fortress_world
    - agences_de_securite_interieure_des_etats_forteresses_fortress_world
    - milices_privees_de_protection_des_sites_germinaux_fortress_world

type_relation_dominante: symbiose

annee_debut: 2063
annee_fin: 

trajectoire: émergent
est_clandestin: true
generation: forteresse

injection:
  garantie_selection: false
  type: custom
  annee_injection: 2063
  contexte_injection: >
    Raimon des Cinq Passages facilite la mobilité humaine dans un monde où les frontières sont verrouillées, en maintenant des corridors clandestins qui contournent les contrôles des blocs. Son action affaiblit la fragmentation territoriale imposée par les forteresses, tout en renforçant les réseaux de résistance et de survie en marge des systèmes dominants.
  impact_sur_variables:
  - variable: demographie_mobilite_humaine
    delta_level: 8
    duree: 15
    polarite: 1
  - variable: organisation_territoires
    delta_level: -5
    duree: 20
    polarite: -1
  propagation:
    via_matrice: false

description_journalistique: >
  Dans les ruines de Tolosa, où les tours Nexus7 côtoient les vestiges romains, Raimon des Cinq Passages est une légende vivante. Vêtu d'une cape tissée de fibres optiques récupérées, il arpente les sentiers escarpés des Pyrénées avec une assurance qui défie les drones de surveillance des blocs. Les rumeurs disent qu'il connaît chaque faille des frontières, chaque tunnel oublié des anciennes mines, et qu'il a guidé des centaines de déplacés vers les zones libres du Rust Belt. Mais Raimon n'est pas un simple passeur : il est le dernier héritier d'une lignée de gardiens, et sa connaissance des passages est à la fois une arme et un fardeau. Les milices privées le traquent, les réseaux clandestins le courtisent, et sa tribu le considère comme un rempart contre l'effacement de leur mémoire.

signes_distinctifs: >
  Raimon porte toujours un bracelet en métal récupéré, gravé des symboles des Cinq Nations, qui lui sert à la fois de boussole et de talisman. Ses vêtements, faits de tissus hybrides (fibres naturelles et matériaux recyclés des infrastructures abandonnées), le rendent presque invisible dans les zones grises. Il utilise un vieux terminal portable, alimenté par des panneaux solaires artisanaux, pour cartographier les passages en temps réel et communiquer avec les réseaux de contrebandiers.
retry_signes_distinctifs: non

tensions_narratives: >
  Raimon est tiraillé entre sa loyauté envers sa tribu, qui souhaite préserver les passages comme des sites sacrés, et les réseaux clandestins qui les exploitent pour la contrebande. Sa relation avec les *Gardiens du Miroir* est également fragile : ces derniers voient en lui un allié, mais leur alliance pourrait basculer si les blocs décident de verrouiller définitivement Al-Hima. Enfin, sa mère, Guilhelma, le presse de prendre la tête de la tribu, mais Raimon hésite, conscient que son rôle de passeur est plus crucial que jamais dans un monde en fragmentation.

date_creation: 2026-09-24
exclure_articles: true
---

# Raimon des Cinq Passages

## Rôle dans [[fortress_world]]
Fils de Guilhelma, jeune guerrier de la tribu des Cinq Nations à Tolosa — Saint-Sernin-du-Désert, Raimon incarne la mémoire vivante des passages vers les Pyrénées et Al-Hima. Dans un monde où les frontières sont devenues des forteresses, il est l'un des derniers à connaître les chemins oubliés qui relient les blocs fragmentés. Son rôle oscille entre la préservation des savoirs ancestraux de sa tribu et la négociation avec les réseaux clandestins qui dépendent de ces corridors pour survivre. Il est à la fois un gardien des marges et un acteur clé des dynamiques de pouvoir informel, où la maîtrise des flux humains et matériels devient une monnaie d'échange précieuse.

## Responsabilités
Raimon guide les convois de contrebandiers et de déplacés à travers les zones grises des Pyrénées, évitant les drones de surveillance des blocs et les milices privées. Il cartographie les passages sûrs pour les réseaux de passeurs d'information et de ressources, tout en protégeant les sites sacrés de sa tribu des pillages des complexes militaro-industriels. Il négocie également avec les *Gardiens du Miroir* (Al-Haras al-ʿAtabah) pour sécuriser les accès à Al-Hima, une zone tampon stratégique entre les blocs eurasiatique et atlantique.

## Variables influencées
- [[geopolitique_conflits]]
- [[demographie_mobilite_humaine]]
- [[organisation_territoires]]

## Relations
**Alliés** : [[tribu_des_cinq_nations_fortress_world]], [[reseau_des_cartographes_des_zones_grises_fortress_world]], [[reseaux_d_echange_clandestin_inter_zones_fortress_world]], [[la_garde_du_seuil_fortress_world]]
**Opposants** : [[administrations_de_controle_frontalier_des_blocs_fortress_world]], [[agences_de_securite_interieure_des_etats_forteresses_fortress_world]], [[milices_privees_de_protection_des_sites_germinaux_fortress_world]]

## Description journalistique
Dans les ruines de Tolosa, où les tours Nexus7 côtoient les vestiges romains, Raimon des Cinq Passages est une légende vivante. Vêtu d'une cape tissée de fibres optiques récupérées, il arpente les sentiers escarpés des Pyrénées avec une assurance qui défie les drones de surveillance des blocs. Les rumeurs disent qu'il connaît chaque faille des frontières, chaque tunnel oublié des anciennes mines, et qu'il a guidé des centaines de déplacés vers les zones libres du Rust Belt. Mais Raimon n'est pas un simple passeur : il est le dernier héritier d'une lignée de gardiens, et sa connaissance des passages est à la fois une arme et un fardeau. Les milices privées le traquent, les réseaux clandestins le courtisent, et sa tribu le considère comme un rempart contre l'effacement de leur mémoire.

## Tensions narratives
Raimon est tiraillé entre sa loyauté envers sa tribu, qui souhaite préserver les passages comme des sites sacrés, et les réseaux clandestins qui les exploitent pour la contrebande. Sa relation avec les *Gardiens du Miroir* est également fragile : ces derniers voient en lui un allié, mais leur alliance pourrait basculer si les blocs décident de verrouiller définitivement Al-Hima. Enfin, sa mère, Guilhelma, le presse de prendre la tête de la tribu, mais Raimon hésite, conscient que son rôle de passeur est plus crucial que jamais dans un monde en fragmentation.
