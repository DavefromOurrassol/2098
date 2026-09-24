---
name: Réseau des Citadelles du Sud-Pacifique (RCSP)
type: instance
slug: holdfast_reference
entite: holdfast
scenario: reference
localisation:
  zone: indo_pacifique_emergent
  lieu: 'Nouvelle-Zélande (Arc Indo-Pacifique)'
  type_lieu: site_strategique

type_dans_scenario: infrastructure

role_dans_scenario: >
  Réseau résiduel de bunkers-cités construits dans les années 2030-2040 par les ultra-riches en Nouvelle-Zélande et dans l'Arc Indo-Pacifique, Holdfast incarne la privatisation extrême de la souveraineté territoriale. En 2098, la plupart de ces enclaves sont abandonnées ou reconverties en bases logistiques pour les consortiums privés, mais quelques-unes persistent comme des micro-territoires autarciques, tolérés par les États voisins en échange de services discrets (stockage de données critiques, relais énergétiques). Leur existence reflète l'échec des institutions collectives à garantir la sécurité dans un monde fragmenté, tout en illustrant la dépendance paradoxale des élites à l'égard des systèmes qu'elles méprisent.

responsabilites: >
  Assurer la survie physique et numérique de leurs résidents (élites économiques, familles souveraines, et leurs employés) via des infrastructures autonomes : fermes verticales, désalinisation, boucliers anti-EMP, et réseaux de communication isolés. Certaines citadelles servent aussi de hubs pour les consortiums privés (ex. stockage de terres rares, maintenance de drones sous-marins). Leur gouvernance interne repose sur des chartes privées, souvent inspirées des modèles corporatistes du début du XXIe siècle, avec une justice expéditive et une exclusion systématique des non-résidents.

impact_local: 3
impact_systemique_global: 2

variables_influencees:
    - systeme_economique_redistribution
    - gouvernance_institutions
    - organisation_territoires

zone_geographique:
    - régionale
    - nationale

zone_systemique:
    - infrastructure
    - gouvernance
    - économie

alliances:
    - consortiums_prives_d_extraction_de_ressources_critiques_reference
    - consortiums_prives_de_gestion_des_donnees_critiques_reference
    - ergo_wian_sovereign_holdings_reference

oppositions:
    - assemblee_territoires_reference
    - banque_des_communs_reference
    - federation_communs_territoriaux_reference

type_relation_dominante: dépendance

annee_debut: 2032
annee_fin: 

trajectoire: résiduel
est_clandestin: false
generation: forteresse

injection:
  type: custom
  annee_injection: 2032
  contexte_injection: >
    Le RCSP a accéléré la fragmentation territoriale en normalisant l'idée de zones souveraines privées, tout en affaiblissant les institutions publiques par son exemple de gouvernance parallèle. Son impact économique est négatif car il a concentré des ressources critiques (eau, énergie, données) entre les mains d'une minorité, mais il a aussi créé un précédent pour des modèles d'autogestion locale dans les zones abandonnées par les États.
  impact_sur_variables:
  - variable: systeme_economique_redistribution
    delta_level: -8
    duree: 25
    polarite: -1
  - variable: gouvernance_institutions
    delta_level: -5
    duree: 20
    polarite: -1
  - variable: organisation_territoires
    delta_level: 6
    duree: 15
    polarite: 1
  propagation:
    via_matrice: false

description_journalistique: >
  En 2098, les 'Citadelles du Sud-Pacifique' ne sont plus que l'ombre de leur ambition originelle : des forteresses high-tech construites pour résister à l'effondrement, aujourd'hui réduites à des villages fantômes ou à des avant-postes logistiques pour les consortiums miniers. Les rares encore habitées, comme la 'Holdfast de Queenstown' ou le 'Dôme de Christchurch', abritent des familles qui refusent de quitter leur bulle de béton et d'acier, tandis que les autres sont devenues des reliques rouillées, pillées par des collectifs de récupérateurs. Leur architecture trahit leur paradoxe : des murs de 3 mètres d'épaisseur pour se protéger du monde, mais des portes dérobées pour négocier avec lui. Les États voisins ferment les yeux, tant que ces enclaves ne menacent pas leurs propres équilibres précaires.

signes_distinctifs: >
  Architecture brutaliste et organique à la fois : dômes géodésiques recouverts de panneaux solaires et de filets de camouflage, tours de communication blindées, et entrées dissimulées sous des faux villages alpins. Les résidents portent des badges biométriques et des combinaisons climatisées, tandis que les employés extérieurs sont cantonnés dans des zones périphériques sous surveillance. Les citadelles abandonnées sont reconnaissables à leurs jardins hydroponiques desséchés et à leurs graffitis en mandarin et en russe, traces des pillards qui les ont vidées.
retry_signes_distinctifs: non

tensions_narratives: >
  1) **Légitimité vs. Illégitimité** : Les dernières citadelles survivantes sont-elles des reliques d'un monde révolu, ou les précurseurs d'une nouvelle forme de souveraineté privée ? 2) **Autarcie vs. Dépendance** : Leur survie dépend de leur capacité à rester invisibles, mais aussi de leur intégration discrète dans les réseaux logistiques régionaux. 3) **Héritage toxique** : Les citadelles abandonnées posent des risques environnementaux (déchets radioactifs, batteries au lithium) et sociaux (milices privées reconverties en gangs). 4) **Mémoire sélective** : Les élites qui y ont vécu en sortent-elles transformées, ou reproduisent-elles les mêmes schémas de domination une fois réintégrées dans le monde extérieur ?

date_creation: 2026-09-24
---

# Réseau des Citadelles du Sud-Pacifique (RCSP)

## Rôle dans [[reference]]
Réseau résiduel de bunkers-cités construits dans les années 2030-2040 par les ultra-riches en Nouvelle-Zélande et dans l'Arc Indo-Pacifique, Holdfast incarne la privatisation extrême de la souveraineté territoriale. En 2098, la plupart de ces enclaves sont abandonnées ou reconverties en bases logistiques pour les consortiums privés, mais quelques-unes persistent comme des micro-territoires autarciques, tolérés par les États voisins en échange de services discrets (stockage de données critiques, relais énergétiques). Leur existence reflète l'échec des institutions collectives à garantir la sécurité dans un monde fragmenté, tout en illustrant la dépendance paradoxale des élites à l'égard des systèmes qu'elles méprisent.

## Responsabilités
Assurer la survie physique et numérique de leurs résidents (élites économiques, familles souveraines, et leurs employés) via des infrastructures autonomes : fermes verticales, désalinisation, boucliers anti-EMP, et réseaux de communication isolés. Certaines citadelles servent aussi de hubs pour les consortiums privés (ex. stockage de terres rares, maintenance de drones sous-marins). Leur gouvernance interne repose sur des chartes privées, souvent inspirées des modèles corporatistes du début du XXIe siècle, avec une justice expéditive et une exclusion systématique des non-résidents.

## Variables influencées
- [[systeme_economique_redistribution]]
- [[gouvernance_institutions]]
- [[organisation_territoires]]

## Relations
**Alliés** : [[consortiums_prives_d_extraction_de_ressources_critiques_reference]], [[consortiums_prives_de_gestion_des_donnees_critiques_reference]], [[ergo_wian_sovereign_holdings_reference]]
**Opposants** : [[assemblee_territoires_reference]], [[banque_des_communs_reference]], [[federation_communs_territoriaux_reference]]

## Description journalistique
En 2098, les 'Citadelles du Sud-Pacifique' ne sont plus que l'ombre de leur ambition originelle : des forteresses high-tech construites pour résister à l'effondrement, aujourd'hui réduites à des villages fantômes ou à des avant-postes logistiques pour les consortiums miniers. Les rares encore habitées, comme la 'Holdfast de Queenstown' ou le 'Dôme de Christchurch', abritent des familles qui refusent de quitter leur bulle de béton et d'acier, tandis que les autres sont devenues des reliques rouillées, pillées par des collectifs de récupérateurs. Leur architecture trahit leur paradoxe : des murs de 3 mètres d'épaisseur pour se protéger du monde, mais des portes dérobées pour négocier avec lui. Les États voisins ferment les yeux, tant que ces enclaves ne menacent pas leurs propres équilibres précaires.

## Tensions narratives
1) **Légitimité vs. Illégitimité** : Les dernières citadelles survivantes sont-elles des reliques d'un monde révolu, ou les précurseurs d'une nouvelle forme de souveraineté privée ? 2) **Autarcie vs. Dépendance** : Leur survie dépend de leur capacité à rester invisibles, mais aussi de leur intégration discrète dans les réseaux logistiques régionaux. 3) **Héritage toxique** : Les citadelles abandonnées posent des risques environnementaux (déchets radioactifs, batteries au lithium) et sociaux (milices privées reconverties en gangs). 4) **Mémoire sélective** : Les élites qui y ont vécu en sortent-elles transformées, ou reproduisent-elles les mêmes schémas de domination une fois réintégrées dans le monde extérieur ?
