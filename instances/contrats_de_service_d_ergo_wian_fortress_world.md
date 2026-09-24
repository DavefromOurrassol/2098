---
name: Ergo-Wian Sovereign Labor Contracts (EW-SLC)
type: instance
slug: contrats_de_service_d_ergo_wian_fortress_world
entite: contrats_de_service_d_ergo_wian
scenario: fortress_world
localisation:
  zone: zone_usines_forteresses_eurasie
  lieu: zones industrielles forteresses du bloc eurasiatique occidental
  type_lieu: infrastructure

type_dans_scenario: système

role_dans_scenario: >
  Régime de servitude contractuelle légalisée qui comble le déficit démographique d'Euro-Nord en important une main-d'œuvre captive depuis le Hors. Sous couvert d'opportunités économiques, EW-SLC transforme la précarité des populations périphériques en ressource stratégique pour les blocs vieillissants, créant une dépendance structurelle où les termes du contrat deviennent une prison invisible. Ce système incarne la marchandisation extrême du travail humain, où la survie individuelle est sacrifiée au nom de la stabilité des forteresses.

responsabilites: >
  Recrutement massif de travailleurs dans les zones Hors via des intermédiaires locaux (factions, milices, cartels), gestion des contrats de 5 à 20 ans non résiliables, fourniture de logement et nourriture en échange d'un travail forcé dans les infrastructures critiques d'Euro-Nord (mines, maintenance, logistique arctique). Supervision des quotas de main-d'œuvre par bloc, négociation des termes avec les États-forteresses, et répression des tentatives de fuite ou de rébellion via des milices privées sous contrat.

impact_local: 4
impact_systemique_global: 5

variables_influencees:
    - demographie_mobilite_humaine
    - systemes_productifs_travail
    - geopolitique_conflits
    - gouvernance_institutions

zone_geographique:
    - continentale
    - globale

zone_systemique:
    - économie
    - gouvernance
    - société

alliances:
    - ergo_wian_sovereign_holdings_fortress_world
    - alpha47_fortress_world
    - zone_usines_forteresses_eurasie_fortress_world
    - armada_logistique_nordique_fortress_world
    - cartels_miniers_militarises_subsahariens_fortress_world
    - factions_djihadistes_logistiques_d_asie_centrale_fortress_world

oppositions:
    - alliance_sanitaire_des_populations_exclues_fortress_world
    - coalitions_des_deplaces_et_apatrides_fortress_world
    - mouvement_commun_midwest_fortress_world
    - cellules_universitaires_dissidentes_des_zones_tampons_fortress_world

type_relation_dominante: dépendance

annee_debut: 2046
annee_fin: 

trajectoire: dominant
est_clandestin: false
generation: forteresse

injection:
  garantie_selection: false
  type: custom
  annee_injection: 2046
  contexte_injection: >
    EW-SLC est un pivot systémique qui verrouille la dépendance des blocs vieillissants envers une main-d'œuvre captive, tout en exacerbant les tensions géopolitiques autour du contrôle des flux humains. Son impact sur demographie_mobilite_humaine est négatif car il transforme la mobilité en servitude, tandis qu'il renforce temporairement les systemes_productifs_travail au prix d'une instabilité croissante (geopolitique_conflits).
  impact_sur_variables:
  - variable: demographie_mobilite_humaine
    delta_level: 20
    duree: 25
    polarite: -1
  - variable: systemes_productifs_travail
    delta_level: 15
    duree: 15
    polarite: 1
  - variable: geopolitique_conflits
    delta_level: 10
    duree: 20
    polarite: -1
  propagation:
    via_matrice: true

description_journalistique: >
  Depuis les steppes kazakhes jusqu'aux mines arctiques de Kalaallit Nunaat, les 'Contrats Ergo-Wian' sont devenus le visage légal de l'esclavage moderne. Officiellement, ce sont des 'opportunités de mobilité sociale' pour les populations du Hors ; en réalité, des contrats de 20 ans non résiliables, où le logement insalubre et la ration alimentaire quotidienne servent de salaire. Les intermédiaires locaux – milices centrasiatiques, cartels subsahariens – se disputent le rôle de recruteur, transformant les zones grises en véritables marchés aux esclaves 2.0. Les blocs ferment les yeux : Euro-Nord a besoin de bras pour ses infrastructures vieillissantes, et les travailleurs du Hors n'ont pas le luxe de refuser.

signes_distinctifs: >
  Les contrats sont imprimés sur des tablettes à encre indélébile, scellées par un bracelet biométrique verrouillé à l'arrivée dans les zones de travail. Les travailleurs portent des combinaisons grises marquées 'EW-SLC' en lettres bleues, avec un code-barres unique lié à leur contrat. Les intermédiaires locaux arborent des brassards orange 'Ergo-Wian Accredited Recruiter', symbole de leur alliance avec le système.
retry_signes_distinctifs: non

tensions_narratives: >
  La révolte gronde dans les camps de travail arctiques, où les conditions de vie se dégradent à mesure que les ressources s'épuisent. Les factions du Hors, autrefois alliées, commencent à se retourner contre Ergo-Wian, exigeant une part plus grande des profits. Dans les blocs, des voix dissidentes dénoncent un système qui sape les fondements moraux des forteresses. La question est désormais : jusqu'où les États-forteresses sont-ils prêts à aller pour préserver ce pilier invisible de leur stabilité ?

date_creation: 2026-09-24
---

# Ergo-Wian Sovereign Labor Contracts (EW-SLC)

## Rôle dans [[fortress_world]]
Régime de servitude contractuelle légalisée qui comble le déficit démographique d'Euro-Nord en important une main-d'œuvre captive depuis le Hors. Sous couvert d'opportunités économiques, EW-SLC transforme la précarité des populations périphériques en ressource stratégique pour les blocs vieillissants, créant une dépendance structurelle où les termes du contrat deviennent une prison invisible. Ce système incarne la marchandisation extrême du travail humain, où la survie individuelle est sacrifiée au nom de la stabilité des forteresses.

## Responsabilités
Recrutement massif de travailleurs dans les zones Hors via des intermédiaires locaux (factions, milices, cartels), gestion des contrats de 5 à 20 ans non résiliables, fourniture de logement et nourriture en échange d'un travail forcé dans les infrastructures critiques d'Euro-Nord (mines, maintenance, logistique arctique). Supervision des quotas de main-d'œuvre par bloc, négociation des termes avec les États-forteresses, et répression des tentatives de fuite ou de rébellion via des milices privées sous contrat.

## Variables influencées
- [[demographie_mobilite_humaine]]
- [[systemes_productifs_travail]]
- [[geopolitique_conflits]]
- [[gouvernance_institutions]]

## Relations
**Alliés** : [[ergo_wian_sovereign_holdings_fortress_world]], [[alpha47_fortress_world]], [[zone_usines_forteresses_eurasie_fortress_world]], [[armada_logistique_nordique_fortress_world]], [[cartels_miniers_militarises_subsahariens_fortress_world]], [[factions_djihadistes_logistiques_d_asie_centrale_fortress_world]]
**Opposants** : [[alliance_sanitaire_des_populations_exclues_fortress_world]], [[coalitions_des_deplaces_et_apatrides_fortress_world]], [[mouvement_commun_midwest_fortress_world]], [[cellules_universitaires_dissidentes_des_zones_tampons_fortress_world]]

## Description journalistique
Depuis les steppes kazakhes jusqu'aux mines arctiques de Kalaallit Nunaat, les 'Contrats Ergo-Wian' sont devenus le visage légal de l'esclavage moderne. Officiellement, ce sont des 'opportunités de mobilité sociale' pour les populations du Hors ; en réalité, des contrats de 20 ans non résiliables, où le logement insalubre et la ration alimentaire quotidienne servent de salaire. Les intermédiaires locaux – milices centrasiatiques, cartels subsahariens – se disputent le rôle de recruteur, transformant les zones grises en véritables marchés aux esclaves 2.0. Les blocs ferment les yeux : Euro-Nord a besoin de bras pour ses infrastructures vieillissantes, et les travailleurs du Hors n'ont pas le luxe de refuser.

## Tensions narratives
La révolte gronde dans les camps de travail arctiques, où les conditions de vie se dégradent à mesure que les ressources s'épuisent. Les factions du Hors, autrefois alliées, commencent à se retourner contre Ergo-Wian, exigeant une part plus grande des profits. Dans les blocs, des voix dissidentes dénoncent un système qui sape les fondements moraux des forteresses. La question est désormais : jusqu'où les États-forteresses sont-ils prêts à aller pour préserver ce pilier invisible de leur stabilité ?
