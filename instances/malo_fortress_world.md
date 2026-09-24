---
name: Malo des Cycles
type: instance
slug: malo_fortress_world
entite: malo
scenario: fortress_world
localisation:
  zone: paris_hors
  lieu: ruines de Paris
  type_lieu: ville

type_dans_scenario: humain

role_dans_scenario: >
  Ami et compagnon de collecte de Hyphan Raghavan dans les ruines de Paris, Malo incarne la persistance des liens humains et de l'espoir dans un monde fragmenté par les blocs souverains. Il participe activement aux cycles des Recycleurs, une communauté de survie qui récupère et répare les artefacts du monde ancien pour les échanger ou les réutiliser. Son rêve de rejoindre le Califat de Barcelone, perçu comme un havre de stabilité et de liberté, symbolise la tension entre l'ancrage dans la précarité du présent et la quête d'un idéal lointain, souvent inaccessible.

responsabilites: >
  Malo est chargé de la collecte et du tri des matériaux dans les zones interdites de Paris, évitant les patrouilles des agences de sécurité intérieure des blocs. Il participe à l'organisation des échanges avec d'autres réseaux de survie et contribue à la transmission des savoir-faire techniques entre générations de Recycleurs. Son rôle inclut également la négociation avec les contrebandiers et les passeurs d'information pour accéder à des ressources rares ou des nouvelles des autres blocs.

impact_local: 3
impact_systemique_global: 1

variables_influencees:
    - demographie_mobilite_humaine
    - valeurs_culture_tempo_sociale
    - systeme_economique_redistribution

zone_geographique:
    - urbaine
    - locale

zone_systemique:
    - société
    - économie

alliances:
    - hyphan_raghavan_fortress_world
    - les_recycleurs_fortress_world
    - reseaux_d_echange_clandestin_inter_zones_fortress_world
    - coalitions_des_deplaces_et_apatrides_fortress_world

oppositions:
    - agences_de_securite_interieure_des_etats_forteresses_fortress_world
    - bureaux_de_controle_frontalier_des_blocs_fermes_fortress_world
    - milices_privees_de_protection_des_sites_germinaux_fortress_world

type_relation_dominante: coopération

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
    Malo incarne la persistance des mobilités humaines et des valeurs de solidarité malgré le contrôle strict des frontières. Son rôle dans les réseaux de Recycleurs et son rêve de rejoindre le Califat de Barcelone influencent positivement la démographie et les valeurs culturelles en maintenant vivantes des dynamiques de résistance et d'espoir dans un monde fragmenté.
  impact_sur_variables:
  - variable: demographie_mobilite_humaine
    delta_level: 5
    duree: 10
    polarite: 1
  - variable: valeurs_culture_tempo_sociale
    delta_level: 3
    duree: 15
    polarite: 1
  propagation:
    via_matrice: false

description_journalistique: >
  Malo, connu sous le nom de 'Malo des Cycles' dans les ruines de Paris, est une figure discrète mais respectée parmi les Recycleurs. Vêtu d'une combinaison de récupération renforcée de plaques métalliques, il arpente les zones interdites avec une agilité qui trahit des années d'expérience. Son sac, toujours rempli d'outils bricolés et de composants électroniques rares, est une légende parmi les siens. Il parle peu de son passé, mais ceux qui le connaissent savent qu'il rêve du Califat de Barcelone, un mythe qui alimente les conversations nocturnes autour des feux de camp. Son engagement auprès de Hyphan Raghavan, une autre figure emblématique des Cycles, en fait un symbole de résistance et de solidarité dans un monde où les frontières sont devenues des murs infranchissables.

signes_distinctifs: >
  Malo porte toujours un bracelet fabriqué à partir de câbles de fibre optique récupérés, symbole de sa connexion aux réseaux d'information clandestins. Son visage est marqué par une cicatrice en forme de croissant, souvenir d'une rencontre avec une patrouille frontalière. Il utilise une lampe frontale modifiée, alimentée par des batteries solaires bricolées, qui éclaire faiblement les ruines la nuit.
retry_signes_distinctifs: non

tensions_narratives: >
  La tension centrale autour de Malo réside dans son double rôle de survivant ancré dans la réalité des Cycles et de rêveur aspirant à un ailleurs meilleur. Son amitié avec Hyphan Raghavan, qui partage ce rêve, pourrait les pousser à tenter une traversée périlleuse vers le Califat de Barcelone, mettant en danger leur réseau de survie. Par ailleurs, son engagement auprès des Recycleurs le place en première ligne face à la répression croissante des agences de sécurité des blocs, qui voient dans ces communautés une menace à l'ordre souverain. Son histoire interroge : l'espoir d'un monde meilleur est-il un moteur de résistance ou une illusion dangereuse ?

date_creation: 2026-09-24
exclure_articles: true
---

# Malo des Cycles

## Rôle dans [[fortress_world]]
Ami et compagnon de collecte de Hyphan Raghavan dans les ruines de Paris, Malo incarne la persistance des liens humains et de l'espoir dans un monde fragmenté par les blocs souverains. Il participe activement aux cycles des Recycleurs, une communauté de survie qui récupère et répare les artefacts du monde ancien pour les échanger ou les réutiliser. Son rêve de rejoindre le Califat de Barcelone, perçu comme un havre de stabilité et de liberté, symbolise la tension entre l'ancrage dans la précarité du présent et la quête d'un idéal lointain, souvent inaccessible.

## Responsabilités
Malo est chargé de la collecte et du tri des matériaux dans les zones interdites de Paris, évitant les patrouilles des agences de sécurité intérieure des blocs. Il participe à l'organisation des échanges avec d'autres réseaux de survie et contribue à la transmission des savoir-faire techniques entre générations de Recycleurs. Son rôle inclut également la négociation avec les contrebandiers et les passeurs d'information pour accéder à des ressources rares ou des nouvelles des autres blocs.

## Variables influencées
- [[demographie_mobilite_humaine]]
- [[valeurs_culture_tempo_sociale]]
- [[systeme_economique_redistribution]]

## Relations
**Alliés** : [[hyphan_raghavan_fortress_world]], [[les_recycleurs_fortress_world]], [[reseaux_d_echange_clandestin_inter_zones_fortress_world]], [[coalitions_des_deplaces_et_apatrides_fortress_world]]
**Opposants** : [[agences_de_securite_interieure_des_etats_forteresses_fortress_world]], [[bureaux_de_controle_frontalier_des_blocs_fermes_fortress_world]], [[milices_privees_de_protection_des_sites_germinaux_fortress_world]]

## Description journalistique
Malo, connu sous le nom de 'Malo des Cycles' dans les ruines de Paris, est une figure discrète mais respectée parmi les Recycleurs. Vêtu d'une combinaison de récupération renforcée de plaques métalliques, il arpente les zones interdites avec une agilité qui trahit des années d'expérience. Son sac, toujours rempli d'outils bricolés et de composants électroniques rares, est une légende parmi les siens. Il parle peu de son passé, mais ceux qui le connaissent savent qu'il rêve du Califat de Barcelone, un mythe qui alimente les conversations nocturnes autour des feux de camp. Son engagement auprès de Hyphan Raghavan, une autre figure emblématique des Cycles, en fait un symbole de résistance et de solidarité dans un monde où les frontières sont devenues des murs infranchissables.

## Tensions narratives
La tension centrale autour de Malo réside dans son double rôle de survivant ancré dans la réalité des Cycles et de rêveur aspirant à un ailleurs meilleur. Son amitié avec Hyphan Raghavan, qui partage ce rêve, pourrait les pousser à tenter une traversée périlleuse vers le Califat de Barcelone, mettant en danger leur réseau de survie. Par ailleurs, son engagement auprès des Recycleurs le place en première ligne face à la répression croissante des agences de sécurité des blocs, qui voient dans ces communautés une menace à l'ordre souverain. Son histoire interroge : l'espoir d'un monde meilleur est-il un moteur de résistance ou une illusion dangereuse ?
