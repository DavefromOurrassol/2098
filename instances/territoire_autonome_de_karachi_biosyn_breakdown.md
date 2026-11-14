---
name: Karachi-BioSyn — La Souche Commune
type: instance
slug: territoire_autonome_de_karachi_biosyn_breakdown
entite: territoire_autonome_de_karachi_biosyn
scenario: breakdown
localisation:
  zone: karachi_biosyn
  lieu: Karachi
  type_lieu: infrastructure

type_dans_scenario: infrastructure

role_dans_scenario: >
  Territoire autogéré né en 2070 dans les ruines du port de Karachi, autour de l'ancienne usine pharmaceutique BioSyn. Les travailleurs et usagers y ont réapproprié les laboratoires pour produire localement médicaments, vaccins et semences en open source, hors brevets et propriété privée. C'est une île d'autonomie sanitaire et productive au cœur du sous-continent indien fragmenté, constamment menacée par les tentatives de récupération des fragments corporatifs et les milices territoriales.

responsabilites: >
  Production collective de médicaments essentiels (antibiotiques, antiviraux, vaccins) à partir de souches bactériennes cultivées sur place ; gestion démocratique des bioreacteurs et laboratoires ; défense armée du périmètre contre les ingérences extérieures ; échange de savoirs et de semences avec d'autres collectifs autogérés via les réseaux de solidarité horizontale.

impact_local: 4
impact_systemique_global: 2

variables_influencees:
    - sante_biotechnologies
    - systemes_productifs_travail
    - organisation_territoires

zone_geographique:
    - urbaine
    - régionale

zone_systemique:
    - infrastructure
    - économie
    - société

alliances:
    - pirates_biologiques_open_source_breakdown
    - collectifs_de_sante_communautaire_autogeree_breakdown
    - reseau_de_recuperation_industrielle_illicite_breakdown
    - front_de_resistance_aux_peages_sur_les_ressources_breakdown
    - cargo_mombasa_crrc_breakdown

oppositions:
    - corporations_de_l_ere_pre_effondrement_a_droits_de_pi_breakdown
    - nexus_biosyn_breakdown
    - enclaves_corporatives_fortifiees_breakdown
    - milices_de_controle_territorial_breakdown
    - reseaux_noirs_pharmaceutiques_breakdown

type_relation_dominante: conflit

annee_debut: 2070
annee_fin: 

trajectoire: émergent
est_clandestin: false
generation: post-effondrement

injection:
  type: custom
  annee_injection: 2070
  contexte_injection: >
    Le Territoire Autonome de Karachi-BioSyn réapproprie une infrastructure pharmaceutique abandonnée pour produire localement des biens essentiels en commun, ce qui réduit la crise sanitaire régionale et restaure un tissu productif autogéré, tout en accentuant la fragmentation territoriale du sous-continent indien post-effondrement par la création d'un nouvel acteur souverain non étatique.
  impact_sur_variables:
  - variable: sante_biotechnologies
    delta_level: 8
    duree: 10
    polarite: -1
  - variable: systemes_productifs_travail
    delta_level: 6
    duree: 15
    polarite: -1
  - variable: organisation_territoires
    delta_level: 5
    duree: 5
    polarite: 1
  propagation:
    via_matrice: false

description_journalistique: >
  En 2098, les journalistes décrivent Karachi-BioSyn comme une cité-atelier coincée entre les carcasses rouillées du vieux port et les tours effondrées de la mégalopole. Depuis 2070, des centaines de familles y vivent dans les anciens entrepôts réaménagés, où des bioreacteurs artisanaux produisent des antibiotiques et des vaccins sans brevet. Les murs portent des graffitis en ourdou : « La vie n'appartient à personne ». Mais chaque cargaison de réactifs chimiques doit passer par les dhows de Mombasa, et les fragments de l'ancienne corporation BioSyn rôdent aux frontières, revendiquant la propriété intellectuelle des souches.

signes_distinctifs: >
  Serres stériles installées sur les toits plats des anciens hangars portuaires ; drapeaux blancs frappés d'une double hélice ADN barrée d'une ligne rouge (symbole anti-brevet) ; cheminées des bioreacteurs crachant une vapeur blanche caractéristique ; murs extérieurs couverts de mosaïques de flacons vides recyclés.
retry_signes_distinctifs: non

tensions_narratives: >
  La tension permanente entre l'idéal d'autonomie totale et la dépendance structurelle aux composants électroniques et réactifs importés via les cartels logistiques régionaux ; les raids sporadiques des fragments BioSyn qui revendiquent les brevets des souches originelles ; l'afflux de réfugiés climatiques du delta de l'Indus qui met à l'épreuve la capacité d'accueil du territoire ; la question de savoir si ce modèle de commun productif peut essaimer vers d'autres mégalopoles en ruine ou s'il restera une exception locale condamnée à l'isolement.

date_creation: 2026-11-14
---

# Karachi-BioSyn — La Souche Commune

## Rôle dans [[breakdown]]
Territoire autogéré né en 2070 dans les ruines du port de Karachi, autour de l'ancienne usine pharmaceutique BioSyn. Les travailleurs et usagers y ont réapproprié les laboratoires pour produire localement médicaments, vaccins et semences en open source, hors brevets et propriété privée. C'est une île d'autonomie sanitaire et productive au cœur du sous-continent indien fragmenté, constamment menacée par les tentatives de récupération des fragments corporatifs et les milices territoriales.

## Responsabilités
Production collective de médicaments essentiels (antibiotiques, antiviraux, vaccins) à partir de souches bactériennes cultivées sur place ; gestion démocratique des bioreacteurs et laboratoires ; défense armée du périmètre contre les ingérences extérieures ; échange de savoirs et de semences avec d'autres collectifs autogérés via les réseaux de solidarité horizontale.

## Variables influencées
- [[sante_biotechnologies]]
- [[systemes_productifs_travail]]
- [[organisation_territoires]]

## Relations
**Alliés** : [[pirates_biologiques_open_source_breakdown]], [[collectifs_de_sante_communautaire_autogeree_breakdown]], [[reseau_de_recuperation_industrielle_illicite_breakdown]], [[front_de_resistance_aux_peages_sur_les_ressources_breakdown]], [[cargo_mombasa_crrc_breakdown]]
**Opposants** : [[corporations_de_l_ere_pre_effondrement_a_droits_de_pi_breakdown]], [[nexus_biosyn_breakdown]], [[enclaves_corporatives_fortifiees_breakdown]], [[milices_de_controle_territorial_breakdown]], [[reseaux_noirs_pharmaceutiques_breakdown]]

## Description journalistique
En 2098, les journalistes décrivent Karachi-BioSyn comme une cité-atelier coincée entre les carcasses rouillées du vieux port et les tours effondrées de la mégalopole. Depuis 2070, des centaines de familles y vivent dans les anciens entrepôts réaménagés, où des bioreacteurs artisanaux produisent des antibiotiques et des vaccins sans brevet. Les murs portent des graffitis en ourdou : « La vie n'appartient à personne ». Mais chaque cargaison de réactifs chimiques doit passer par les dhows de Mombasa, et les fragments de l'ancienne corporation BioSyn rôdent aux frontières, revendiquant la propriété intellectuelle des souches.

## Tensions narratives
La tension permanente entre l'idéal d'autonomie totale et la dépendance structurelle aux composants électroniques et réactifs importés via les cartels logistiques régionaux ; les raids sporadiques des fragments BioSyn qui revendiquent les brevets des souches originelles ; l'afflux de réfugiés climatiques du delta de l'Indus qui met à l'épreuve la capacité d'accueil du territoire ; la question de savoir si ce modèle de commun productif peut essaimer vers d'autres mégalopoles en ruine ou s'il restera une exception locale condamnée à l'isolement.
