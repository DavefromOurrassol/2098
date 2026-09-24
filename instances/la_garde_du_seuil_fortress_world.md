---
name: Les Gardiens du Miroir — Al-Haras al-ʿAtabah
type: instance
slug: la_garde_du_seuil_fortress_world
entite: la_garde_du_seuil
scenario: fortress_world
localisation:
  zone: al_hima
  lieu: Barcelone reconquise
  type_lieu: ville

type_dans_scenario: organisation

role_dans_scenario: >
  Guerriers légendaires du Califat de Barcelone (Al-Hima), la Garde du Seuil est officiellement présentée comme une élite mystique dotée de pouvoirs surnaturels, garante de l'intégrité territoriale et spirituelle du Califat. En réalité, elle est une force d'élite secrète recrutant exclusivement parmi les Dédoublés — des Porteurs de reflets capables de manipuler des versions alternatives d'eux-mêmes. Son existence même est un secret d'État, protégé par une mythologie soigneusement entretenue pour dissuader les intrusions extérieures et maintenir l'ordre interne. Elle incarne la dualité entre le sacré et le profane, entre la transparence d'un État forteresse et l'opacité d'une caste initiatique.

responsabilites: >
  La Garde assure la sécurité des frontières physiques et symboliques du Califat, en particulier aux points de friction avec les autres blocs (comme les Seuils Kazakhs ou les Zones Grises d'Asie Centrale). Elle traque les infiltrations de Dédoublés non autorisés, contrôle les flux de réfugiés et de contrebandiers, et intervient dans les conflits internes pour éliminer les dissidences perçues comme des menaces à la souveraineté du Califat. Ses membres sont également déployés comme émissaires secrets lors de négociations inter-blocs, où leur réputation de guerriers invincibles sert de levier psychologique.

impact_local: 4
impact_systemique_global: 3

variables_influencees:
    - geopolitique_conflits
    - gouvernance_institutions
    - technologie_information
    - valeurs_culture_tempo_sociale

zone_geographique:
    - nationale
    - régionale

zone_systemique:
    - sécurité
    - gouvernance
    - société

alliances:
    - bloc_eurasiatique_occidental_fortress_world
    - agences_de_securite_interieure_des_etats_forteresses_fortress_world
    - complexes_militaro_industriels_de_gestion_des_ressources_fortress_world
    - nexus_biosyn_division_eurasienne_fortress_world

oppositions:
    - coalitions_des_deplaces_et_apatrides_fortress_world
    - reseaux_de_contrebande_energetique_transfrontaliere_fortress_world
    - cellules_universitaires_dissidentes_des_zones_tampons_fortress_world
    - les_dedoubles_fortress_world

type_relation_dominante: alliance stratégique

annee_debut: 2046
annee_fin: 

trajectoire: mature
est_clandestin: true
generation: forteresse

injection:
  garantie_selection: false
  type: custom
  annee_injection: 2046
  contexte_injection: >
    La Garde du Seuil agit comme un multiplicateur de force pour le Califat de Barcelone, renforçant sa position dans les conflits géopolitiques grâce à sa réputation et ses capacités uniques. Son existence légitime un contrôle autoritaire accru sur les institutions du Califat, tout en érodant la confiance dans les récits culturels alternatifs (d'où l'impact négatif sur valeurs_culture_tempo_sociale). Son influence se propage via la matrice en tant qu'acteur clé des dynamiques de fragmentation et de sécurisation des blocs.
  impact_sur_variables:
  - variable: geopolitique_conflits
    delta_level: 12
    duree: 15
    polarite: 1
  - variable: gouvernance_institutions
    delta_level: 8
    duree: 20
    polarite: 1
  - variable: valeurs_culture_tempo_sociale
    delta_level: -5
    duree: 10
    polarite: -1
  propagation:
    via_matrice: true

description_journalistique: >
  Depuis les ruelles étroites de la Barcelone reconquise jusqu'aux steppes kazakhes, les Gardiens du Miroir hantent les récits des voyageurs et des réfugiés. Vêtus de robes noires brodées de fils d'argent, leurs visages souvent masqués par des miroirs fractals, ils apparaissent aux frontières comme des ombres insaisissables, capables de se multiplier ou de disparaître dans un éclat de lumière. Les autorités du Califat entretiennent soigneusement le mystère : leurs exploits sont célébrés dans des poèmes épiques diffusés par les médias d'État, tandis que leur véritable nature — une élite de Dédoublés formés à maîtriser leurs reflets — reste un secret jalousement gardé. Leur réputation de guerriers invincibles en fait un outil de dissuasion aussi efficace que leurs drones ou leurs murs frontaliers.

signes_distinctifs: >
  Uniformes noirs aux reflets changeants selon l'angle de lumière, souvent ornés de motifs géométriques inspirés des mosaïques andalouses. Leurs armes, des lames courbes ou des dispositifs énergétiques, sont réputées capables de « trancher les réalités ». Les miroirs portatifs qu'ils utilisent comme outils de communication ou d'espionnage sont devenus un symbole de leur pouvoir, à la fois craint et vénéré. Leur emblème, un seuil stylisé encadré de deux mains tendues, est gravé sur les portes des villes du Califat.
retry_signes_distinctifs: non

tensions_narratives: >
  La Garde du Seuil est prise dans une contradiction croissante : plus elle renforce son mythe pour dissuader les ennemis extérieurs, plus elle devient une cible pour les dissidences internes, qui voient en elle un symbole de l'oppression du Califat. Certains Dédoublés non affiliés à la Garde contestent son monopole sur leur « don », accusant ses membres de trahir leur propre nature en servant un régime autoritaire. Par ailleurs, des rumeurs persistantes évoquent des factions au sein même de la Garde, divisées entre ceux qui veulent révéler leur véritable nature pour légitimer leur pouvoir, et ceux qui préfèrent maintenir le secret, au risque de voir leur influence s'éroder face aux nouvelles technologies de surveillance.

date_creation: 2026-09-24
---

# Les Gardiens du Miroir — Al-Haras al-ʿAtabah

## Rôle dans [[fortress_world]]
Guerriers légendaires du Califat de Barcelone (Al-Hima), la Garde du Seuil est officiellement présentée comme une élite mystique dotée de pouvoirs surnaturels, garante de l'intégrité territoriale et spirituelle du Califat. En réalité, elle est une force d'élite secrète recrutant exclusivement parmi les Dédoublés — des Porteurs de reflets capables de manipuler des versions alternatives d'eux-mêmes. Son existence même est un secret d'État, protégé par une mythologie soigneusement entretenue pour dissuader les intrusions extérieures et maintenir l'ordre interne. Elle incarne la dualité entre le sacré et le profane, entre la transparence d'un État forteresse et l'opacité d'une caste initiatique.

## Responsabilités
La Garde assure la sécurité des frontières physiques et symboliques du Califat, en particulier aux points de friction avec les autres blocs (comme les Seuils Kazakhs ou les Zones Grises d'Asie Centrale). Elle traque les infiltrations de Dédoublés non autorisés, contrôle les flux de réfugiés et de contrebandiers, et intervient dans les conflits internes pour éliminer les dissidences perçues comme des menaces à la souveraineté du Califat. Ses membres sont également déployés comme émissaires secrets lors de négociations inter-blocs, où leur réputation de guerriers invincibles sert de levier psychologique.

## Variables influencées
- [[geopolitique_conflits]]
- [[gouvernance_institutions]]
- [[technologie_information]]
- [[valeurs_culture_tempo_sociale]]

## Relations
**Alliés** : [[bloc_eurasiatique_occidental_fortress_world]], [[agences_de_securite_interieure_des_etats_forteresses_fortress_world]], [[complexes_militaro_industriels_de_gestion_des_ressources_fortress_world]], [[nexus_biosyn_division_eurasienne_fortress_world]]
**Opposants** : [[coalitions_des_deplaces_et_apatrides_fortress_world]], [[reseaux_de_contrebande_energetique_transfrontaliere_fortress_world]], [[cellules_universitaires_dissidentes_des_zones_tampons_fortress_world]], [[les_dedoubles_fortress_world]]

## Description journalistique
Depuis les ruelles étroites de la Barcelone reconquise jusqu'aux steppes kazakhes, les Gardiens du Miroir hantent les récits des voyageurs et des réfugiés. Vêtus de robes noires brodées de fils d'argent, leurs visages souvent masqués par des miroirs fractals, ils apparaissent aux frontières comme des ombres insaisissables, capables de se multiplier ou de disparaître dans un éclat de lumière. Les autorités du Califat entretiennent soigneusement le mystère : leurs exploits sont célébrés dans des poèmes épiques diffusés par les médias d'État, tandis que leur véritable nature — une élite de Dédoublés formés à maîtriser leurs reflets — reste un secret jalousement gardé. Leur réputation de guerriers invincibles en fait un outil de dissuasion aussi efficace que leurs drones ou leurs murs frontaliers.

## Tensions narratives
La Garde du Seuil est prise dans une contradiction croissante : plus elle renforce son mythe pour dissuader les ennemis extérieurs, plus elle devient une cible pour les dissidences internes, qui voient en elle un symbole de l'oppression du Califat. Certains Dédoublés non affiliés à la Garde contestent son monopole sur leur « don », accusant ses membres de trahir leur propre nature en servant un régime autoritaire. Par ailleurs, des rumeurs persistantes évoquent des factions au sein même de la Garde, divisées entre ceux qui veulent révéler leur véritable nature pour légitimer leur pouvoir, et ceux qui préfèrent maintenir le secret, au risque de voir leur influence s'éroder face aux nouvelles technologies de surveillance.
