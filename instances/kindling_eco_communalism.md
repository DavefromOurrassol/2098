---
name: Les Cendres de Kindling
type: instance
slug: kindling_eco_communalism
entite: kindling
scenario: eco_communalism
localisation:
  zone: null
  lieu: null
  type_lieu: null
  note: transnationale_sans_ancrage

type_dans_scenario: réseau

role_dans_scenario: >
  Réseau mythifié des années 2020-2050, évoqué comme une force accélérationniste ayant précipité l'effondrement des structures globales pré-2060. Dans l'eco-communalisme de 2098, Kindling n'existe plus qu'à travers des récits fragmentaires, des archives cryptées et des légendes locales sur les « saboteurs des nœuds ». Son héritage est à la fois craint (pour son radicalisme) et célébré (pour avoir ouvert la voie à la décentralisation forcée). Les Assemblées Bioterritoriales citent parfois ses méthodes comme un mal nécessaire, tandis que les factions autoritaires locales en font un épouvantail pour justifier leur contrôle.

responsabilites: >
  Historiquement : sabotage des infrastructures critiques (réseaux énergétiques, data centers centralisés), infiltration des institutions pour accélérer leur paralysie, désinformation ciblée pour saper la confiance dans les gouvernances globales. Aujourd'hui : aucune responsabilité active, mais son souvenir influence les politiques de résilience locale (ex. : méfiance envers les grands réseaux, préférence pour les solutions low-tech et redondantes).

impact_local: 2
impact_systemique_global: 1

variables_influencees:
    - gouvernance_institutions
    - technologie_information
    - valeurs_culture_tempo_sociale

zone_geographique:
    - globale

zone_systemique:
    - gouvernance
    - information
    - société

alliances:

oppositions:
    - archives_ouvertes_des_jurisprudences_communales_aojc_eco_communalism
    - assemblee_territoires_eco_communalism
    - factions_autoritaires_locales_identitaires_exclusionnistes_eco_communalism

type_relation_dominante: rivalité

annee_debut: 2028
annee_fin: 2055

trajectoire: mythifié
est_clandestin: true
generation: pré-crise

injection:
  garantie_selection: false
  type: custom
  annee_injection: 2028
  contexte_injection: >
    Les Cendres de Kindling ont accéléré la méfiance envers les institutions centralisées (delta négatif sur gouvernance_institutions) en sabotant leurs infrastructures, tout en forçant une décentralisation des technologies de l'information (delta négatif). Leur héritage mythifié a aussi ancré une culture de la résilience locale et de la sobriété (delta positif sur valeurs_culture_tempo_sociale), en faisant un symbole de la rupture avec l’ancien monde.
  impact_sur_variables:
  - variable: gouvernance_institutions
    delta_level: -5
    duree: 20
    polarite: -1
  - variable: technologie_information
    delta_level: -3
    duree: 15
    polarite: -1
  - variable: valeurs_culture_tempo_sociale
    delta_level: 4
    duree: 30
    polarite: 1
  propagation:
    via_matrice: false

description_journalistique: >
  « Les Cendres de Kindling ? Un fantôme qui hante encore nos archives. Dans les années 2040, ils ont fait sauter des centrales à fusion en Europe de l’Est, piraté les IA de gestion des mégapoles chinoises, et répandu des rumeurs si crédibles que des États entiers ont basculé dans la paranoïa. Aujourd’hui, on en parle comme d’une secte de geeks nihilistes, ou comme des héros qui ont forcé le monde à se réveiller. Les jeunes des Brigades de Restauration Écologique portent parfois des patchs avec leur logo – un feu stylisé en forme de nœud coulant – en signe de rébellion contre les derniers reliquats de centralisation. Mais personne ne sait vraiment qui ils étaient. » — Extrait d’un reportage de *La Tresse Verte*, 2095.

signes_distinctifs: >
  Logo : une flamme en forme de nœud coulant, souvent graffée sur les ruines des data centers des années 2030. Symbolique : le feu purificateur et l’étouffement des systèmes. Archives : fragments de manifestes cryptés circulant sur les réseaux Mnemos, évoquant une « libération par l’effondrement ». Rumeurs : certains prétendent que des membres de Kindling auraient infiltré les premières Assemblées Bioterritoriales pour y semer le chaos.
retry_signes_distinctifs: non

tensions_narratives: >
  1) **Héritage controversé** : Les Gardiens du Territoire voient en Kindling un précurseur de la résilience locale, tandis que les Factions Autoritaires Locales les utilisent pour diaboliser toute velléité de décentralisation. 2) **Archives perdues** : Des collectifs comme les Archives Ouvertes des Jurisprudences Communales tentent de reconstituer leur histoire, mais les documents sont fragmentaires et souvent manipulés. 3) **Réappropriation symbolique** : Des mouvements néo-artisanaux reprennent leur esthétique (feu, nœuds) pour célébrer la « destruction créatrice », au grand dam des anciens survivalistes qui y voient une récupération dangereuse.

date_creation: 2026-09-24
---

# Les Cendres de Kindling

## Rôle dans [[eco_communalism]]
Réseau mythifié des années 2020-2050, évoqué comme une force accélérationniste ayant précipité l'effondrement des structures globales pré-2060. Dans l'eco-communalisme de 2098, Kindling n'existe plus qu'à travers des récits fragmentaires, des archives cryptées et des légendes locales sur les « saboteurs des nœuds ». Son héritage est à la fois craint (pour son radicalisme) et célébré (pour avoir ouvert la voie à la décentralisation forcée). Les Assemblées Bioterritoriales citent parfois ses méthodes comme un mal nécessaire, tandis que les factions autoritaires locales en font un épouvantail pour justifier leur contrôle.

## Responsabilités
Historiquement : sabotage des infrastructures critiques (réseaux énergétiques, data centers centralisés), infiltration des institutions pour accélérer leur paralysie, désinformation ciblée pour saper la confiance dans les gouvernances globales. Aujourd'hui : aucune responsabilité active, mais son souvenir influence les politiques de résilience locale (ex. : méfiance envers les grands réseaux, préférence pour les solutions low-tech et redondantes).

## Variables influencées
- [[gouvernance_institutions]]
- [[technologie_information]]
- [[valeurs_culture_tempo_sociale]]

## Relations
**Alliés** : _aucun défini_
**Opposants** : [[archives_ouvertes_des_jurisprudences_communales_aojc_eco_communalism]], [[assemblee_territoires_eco_communalism]], [[factions_autoritaires_locales_identitaires_exclusionnistes_eco_communalism]]

## Description journalistique
« Les Cendres de Kindling ? Un fantôme qui hante encore nos archives. Dans les années 2040, ils ont fait sauter des centrales à fusion en Europe de l’Est, piraté les IA de gestion des mégapoles chinoises, et répandu des rumeurs si crédibles que des États entiers ont basculé dans la paranoïa. Aujourd’hui, on en parle comme d’une secte de geeks nihilistes, ou comme des héros qui ont forcé le monde à se réveiller. Les jeunes des Brigades de Restauration Écologique portent parfois des patchs avec leur logo – un feu stylisé en forme de nœud coulant – en signe de rébellion contre les derniers reliquats de centralisation. Mais personne ne sait vraiment qui ils étaient. » — Extrait d’un reportage de *La Tresse Verte*, 2095.

## Tensions narratives
1) **Héritage controversé** : Les Gardiens du Territoire voient en Kindling un précurseur de la résilience locale, tandis que les Factions Autoritaires Locales les utilisent pour diaboliser toute velléité de décentralisation. 2) **Archives perdues** : Des collectifs comme les Archives Ouvertes des Jurisprudences Communales tentent de reconstituer leur histoire, mais les documents sont fragmentaires et souvent manipulés. 3) **Réappropriation symbolique** : Des mouvements néo-artisanaux reprennent leur esthétique (feu, nœuds) pour célébrer la « destruction créatrice », au grand dam des anciens survivalistes qui y voient une récupération dangereuse.
