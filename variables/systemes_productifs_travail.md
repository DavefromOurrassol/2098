---
name: systemes_productifs_travail
type: systemic_variable
slug: systemes_productifs_travail
variable_type: moteur
global_influence_level: 4
domain:
    - economic
    - technological
    - social
influences:
    - [[systeme_economique_redistribution]]
    - [[demographie_mobilite_humaine]]
    - [[organisation_territoires]]
    - [[sante_biotechnologies]]
influenced_by:
    - [[energie_ressources_critiques]]
    - [[demographie_mobilite_humaine]]
bidirectional_links:
    - [[technologie_information]]
    - [[systeme_economique_redistribution]]
sub_variables:
  - name: industrie_automatisee
    role: Production industrielle de biens matériels à grande échelle via automatisation et robotisation.
    trend: up
    links:
      - [[energie_ressources_critiques]]
      - [[technologie_information]]
  - name: agriculture_systemes_alimentaires
    role: Production alimentaire mondiale industrialisée et automatisée.
    trend: up
    links:
      - [[climat_environnement_global]]
      - [[energie_ressources_critiques]]
      - [[demographie_mobilite_humaine]]
  - name: emploi_humain
    role: Organisation du travail humain et distribution des revenus.
    trend: down
    links:
      - [[systeme_economique_redistribution]]
      - [[valeurs_culture_tempo_sociale]]
  - name: travail_informel
    role: Activités économiques non formalisées et flexibles.
    trend: unstable
    links:
      - [[demographie_mobilite_humaine]]
      - [[systeme_economique_redistribution]]
  - name: productivite_ia
    role: Optimisation des systèmes productifs par intelligence artificielle.
    trend: up
    links:
      - [[technologie_information]]
      - [[energie_ressources_critiques]]
      - [[systeme_economique_redistribution]]

scenario_mapping:
  dominant_scenarios:
    - new_sustainability
  reinforcing_scenarios:
    - reference
    - policy_reform
  constrained_scenarios:
    - breakdown
    - eco_communalism
simulation:
  volatility: medium
  predictability: medium
  uncertainty_level: medium
  tipping_point_risk: medium
  systemic_criticality: 4
  resilience: 3
  adaptability: 4
states:

  fortress_world:
    level: 85
    volatility: 80
    state_logic: >
      Réorganisation des systèmes productifs en blocs fermés hautement automatisés, contrôlés par des États ou des conglomérats industriels sécurisant leurs capacités de production stratégiques.
    dominant_dynamics:
      - production automatisée centralisée
      - sécurisation des chaînes industrielles critiques
      - relocalisation stratégique sélective
    system_role_shift:
      - outil de souveraineté industrielle et économique
      - variable militarisée et contrôlée
    coupling_intensity:
      [[geopolitique_conflits]]: 90
      [[systeme_economique_redistribution]]: 80
      [[frontieres_du_systeme]]: 75
      [[energie_ressources_critiques]]: 80

  new_sustainability:
    level: 50
    volatility: 30
    state_logic: >
      Système productif hautement automatisé et optimisé par IA, où la production est largement déconnectée du travail humain direct et intégrée dans une logique de régulation globale des ressources.
    dominant_dynamics:
      - automatisation quasi totale des chaînes productives
      - optimisation IA des flux industriels et agricoles
      - réduction structurelle du travail humain
    system_role_shift:
      - infrastructure autonome de production globale
      - stabilisateur technologique du système global
    coupling_intensity:
      [[technologie_information]]: 90
      [[systeme_economique_redistribution]]: 80
      [[energie_ressources_critiques]]: 75
      [[gouvernance_institutions]]: 70

  breakdown:
    level: 95
    volatility: 95
    state_logic: >
      Effondrement du système productif global avec rupture des chaînes logistiques, disparition massive du travail humain structuré et désorganisation des capacités industrielles et agricoles mondiales.
    dominant_dynamics:
      - rupture des chaînes de production globales
      - effondrement de l’emploi de masse
      - désorganisation industrielle systémique
    system_role_shift:
      - contrainte critique dominante du système global
      - facteur de désintégration économique et sociale
    coupling_intensity:
      [[systeme_economique_redistribution]]: 90
      [[geopolitique_conflits]]: 85
      [[energie_ressources_critiques]]: 80
      [[organisation_territoires]]: 75

  eco_communalism:
    level: 45
    volatility: 35
    state_logic: >
      Recomposition locale des systèmes productifs avec réduction de l’industrialisation lourde, montée des circuits courts et relocalisation des activités essentielles.
    dominant_dynamics:
      - production locale et distribuée
      - réduction de la dépendance industrielle globale
      - hybridation faible technologie / résilience locale
    system_role_shift:
      - variable décentralisée et communautaire
      - facteur de résilience territoriale
    coupling_intensity:
      [[organisation_territoires]]: 85
      [[systeme_economique_redistribution]]: 70
      [[energie_ressources_critiques]]: 65

  policy_reform:
    level: 60
    volatility: 45
    state_logic: >
      Transformation contrôlée des systèmes productifs via régulation sociale, redistribution et accompagnement de l’automatisation afin de préserver la stabilité de l’emploi et de la cohésion sociale.
    dominant_dynamics:
      - automatisation encadrée
      - réduction progressive du temps de travail
      - montée des politiques industrielles coordonnées
    system_role_shift:
      - variable régulée par gouvernance institutionnelle
      - stabilisateur des transitions technologiques
    coupling_intensity:
      [[gouvernance_institutions]]: 80
      [[systeme_economique_redistribution]]: 75
      [[technologie_information]]: 70
      [[organisation_territoires]]: 60

  reference:
    level: 70
    volatility: 60
    state_logic: >
      Système productif mondial en transition hybride entre travail humain et automatisation, caractérisé par une montée continue de l’IA industrielle et une réduction progressive du travail humain direct sans rupture complète du modèle salarial.
    dominant_dynamics:
      - automatisation progressive des chaînes de production
      - coexistence humain-machine dans la production
      - fragmentation partielle des chaînes globales
    system_role_shift:
      - moteur productif central du système global
      - interface critique entre technologie, énergie et économie
    coupling_intensity:
      [[systeme_economique_redistribution]]: 80
      [[technologie_information]]: 85
      [[energie_ressources_critiques]]: 75
      [[organisation_territoires]]: 70

---

# systemes_productifs_travail

## 1. Identité systémique

**Description**
Variable représentant les systèmes productifs mondiaux (industrie, agriculture, services) et l’organisation du travail humain et automatisé. Elle structure la transformation des ressources en valeur économique et la répartition du travail dans les chaînes de production globales. Elle constitue l’interface centrale entre énergie, technologie, démographie et économie.

**Rôle**
Variable de production fondamentale. Elle organise la création de valeur réelle et la transformation des ressources en biens et services via travail humain et automatisation.

## 2. Position dans le système

**Influence**
- [[systeme_economique_redistribution]]
- [[demographie_mobilite_humaine]]
- [[organisation_territoires]]
- [[sante_biotechnologies]]

**Influencé par**
- [[energie_ressources_critiques]]
- [[demographie_mobilite_humaine]]

**Liens bidirectionnels**
- [[technologie_information]]
- [[systeme_economique_redistribution]]

## 3. Dynamique interne
- Direction : **oscillating** | Intensité : **very_high** | Inertie : **high** | Vitesse : **accelerating**

**Tendances**
- automatisation croissante des tâches productives
- intégration massive de l’IA dans l’industrie et les services
- réduction structurelle du travail humain direct
- fragmentation des chaînes de production globales
- relocalisation stratégique partielle de certaines industries
- augmentation de la productivité par systèmes autonomes
- déclin du travail manuel et répétitif
- hybridation humain-machine dans certains secteurs

**Dynamiques passées**
- révolution industrielle et mécanisation
- industrialisation mondiale des chaînes de production
- urbanisation et salarisation massive
- mondialisation des chaînes de valeur
- délocalisation industrielle vers zones à bas coûts
- automatisation progressive des industries
- intensification de l’agriculture industrielle
- essor du secteur tertiaire
- premières intégrations de l’IA dans la production

**Snapshot**
> Transformation structurelle des systèmes productifs mondiaux vers une automatisation généralisée pilotée par l’IA, réduisant progressivement le travail humain direct et recomposant les chaînes de valeur autour de systèmes autonomes.

**tensions**
- automatisation vs emploi humain
- efficacité vs stabilité sociale
- centralisation vs relocalisation
- productivité vs durabilité
- augmentation humaine vs substitution humaine

**constraints**
- infrastructures industrielles lourdes
- dépendance énergétique des systèmes automatisés
- fragilité des chaînes globales
- résistances sociales et politiques
- déséquilibres de compétences

**forces_attractives**
- productivité élevée
- réduction des coûts
- innovation technologique
- optimisation des chaînes de valeur
- sécurisation de productions critiques

**forces_repulsives**
- destruction d’emplois
- déséquilibres sociaux
- fragilité systémique
- polarisation économique
- dépendance à l’automatisation


## 4. Structure causale

**Forces attractives**
- productivite_systemique
- innovation_technologique
- optimisation_industrielle

**Forces répulsives**
- destruction_emploi
- fragilite_systemique
- polarisation_sociale

**Contraintes**
- infrastructures_lourdes
- dependance_energetique
- inertie_industrielle
- resistances_sociales

**Tensions**
- automatisation vs emploi
- centralisation vs relocalisation
- efficacité vs stabilité sociale
- production vs durabilité
- humain vs machine

## 5. Ruptures

**technological**
_core_
- robotisation_totale
- ia_industrielle_autonome
- impression_3d_industrielle_massive
- agriculture_entierement_automatisee
_extended_
- chaines_production_autonomes_globale
- usines_autoreplicantes
- production_distribuee_ia

**systemic**
_core_
- effondrement_travail_de_masse
- desintermediation_totale_production
- rupture_logistique_globale
_extended_
- reconfiguration_complete_systemes_industriels
- transition_post_travail
- fragmentation_economique_sectorielle

**political_social**
_core_
- revenu_universel
- reduction_massive_temps_travail
- controle_algorithmique_production
_extended_
- protectionnisme_industriel_extreme
- nouvelle_organisation_du_travail
- redistribution_structurelle


## 6. Indicateurs
**primary**
- productivite_industrielle
- taux_automatisation
- emploi_industriel_humain
- part_ia_dans_production

**secondary**
- nombre_usines_autonomes
- relocalisation_industrielle
- transformation_agricole
- fragmentation_chaine_valeur

**systemic**
- dependance_systeme_energetique
- stabilite_chaines_globales
- polarisation_emploi



## 7. Signaux faibles
**technological**
- usines_autonomes_completes
- plateformes_production_ia
- robotisation_services (→ section 12)

**geopolitical**
- relocalisation_industrielle_strategique
- souverainete_production

**social**
- disparition_metiers_intermediaires (→ section 12)
- revenu_universel_experimentations

**environmental**
- automatisation_agricole_massive (→ section 12)
- optimisation_ressources_industrielles

**cognitive_cultural**
- fin_representations_travail_traditionnel
- normalisation_post_travail (→ section 12)



## 8. États par scénario
### [[fortress_world]]
- **level** : 85 | **volatility** : 80

Réorganisation des systèmes productifs en blocs fermés hautement automatisés, contrôlés par des États ou des conglomérats industriels sécurisant leurs capacités de production stratégiques. dominant_dynamics: - production automatisée centralisée - sécurisation des chaînes industrielles critiques - relocalisation stratégique sélective system_role_shift: - outil de souveraineté industrielle et économique - variable militarisée et contrôlée coupling_intensity: geopolitique_conflits: 90 systeme_economique_redistribution: 80 frontieres_systeme: 75 energie_ressources_critiques: 80

**Dynamiques dominantes**
- production automatisée centralisée
- sécurisation des chaînes industrielles critiques
- relocalisation stratégique sélective

**Rôle système**
- outil de souveraineté industrielle et économique
- variable militarisée et contrôlée

**Couplages**
- [[geopolitique_conflits]] : 90
- [[systeme_economique_redistribution]] : 80
- [[frontieres_du_systeme]] : 75
- [[energie_ressources_critiques]] : 80

### [[new_sustainability]]
- **level** : 50 | **volatility** : 30

Système productif hautement automatisé et optimisé par IA, où la production est largement déconnectée du travail humain direct et intégrée dans une logique de régulation globale des ressources. dominant_dynamics: - automatisation quasi totale des chaînes productives - optimisation IA des flux industriels et agricoles - réduction structurelle du travail humain system_role_shift: - infrastructure autonome de production globale - stabilisateur technologique du système global coupling_intensity: technologie_information: 90 systeme_economique_redistribution: 80 energie_ressources_critiques: 75 gouvernance_institutions: 70

**Dynamiques dominantes**
- automatisation quasi totale des chaînes productives
- optimisation IA des flux industriels et agricoles
- réduction structurelle du travail humain

**Rôle système**
- infrastructure autonome de production globale
- stabilisateur technologique du système global

**Couplages**
- [[technologie_information]] : 90
- [[systeme_economique_redistribution]] : 80
- [[energie_ressources_critiques]] : 75
- [[gouvernance_institutions]] : 70

### [[breakdown]]
- **level** : 95 | **volatility** : 95

Effondrement du système productif global avec rupture des chaînes logistiques, disparition massive du travail humain structuré et désorganisation des capacités industrielles et agricoles mondiales. dominant_dynamics: - rupture des chaînes de production globales - effondrement de l’emploi de masse - désorganisation industrielle systémique system_role_shift: - contrainte critique dominante du système global - facteur de désintégration économique et sociale coupling_intensity: systeme_economique_redistribution: 90 geopolitique_conflits: 85 energie_ressources_critiques: 80 organisation_des_territoires: 75

**Dynamiques dominantes**
- rupture des chaînes de production globales
- effondrement de l’emploi de masse
- désorganisation industrielle systémique

**Rôle système**
- contrainte critique dominante du système global
- facteur de désintégration économique et sociale

**Couplages**
- [[systeme_economique_redistribution]] : 90
- [[geopolitique_conflits]] : 85
- [[energie_ressources_critiques]] : 80
- [[organisation_territoires]] : 75

### [[eco_communalism]]
- **level** : 45 | **volatility** : 35

Recomposition locale des systèmes productifs avec réduction de l’industrialisation lourde, montée des circuits courts et relocalisation des activités essentielles. dominant_dynamics: - production locale et distribuée - réduction de la dépendance industrielle globale - hybridation faible technologie / résilience locale system_role_shift: - variable décentralisée et communautaire - facteur de résilience territoriale coupling_intensity: organisation_des_territoires: 85 systeme_economique_redistribution: 70 energie_ressources_critiques: 65

**Dynamiques dominantes**
- production locale et distribuée
- réduction de la dépendance industrielle globale
- hybridation faible technologie / résilience locale

**Rôle système**
- variable décentralisée et communautaire
- facteur de résilience territoriale

**Couplages**
- [[organisation_territoires]] : 85
- [[systeme_economique_redistribution]] : 70
- [[energie_ressources_critiques]] : 65

### [[policy_reform]]
- **level** : 60 | **volatility** : 45

Transformation contrôlée des systèmes productifs via régulation sociale, redistribution et accompagnement de l’automatisation afin de préserver la stabilité de l’emploi et de la cohésion sociale. dominant_dynamics: - automatisation encadrée - réduction progressive du temps de travail - montée des politiques industrielles coordonnées system_role_shift: - variable régulée par gouvernance institutionnelle - stabilisateur des transitions technologiques coupling_intensity: gouvernance_institutions: 80 systeme_economique_redistribution: 75 technologie_information: 70 organisation_des_territoires: 60

**Dynamiques dominantes**
- automatisation encadrée
- réduction progressive du temps de travail
- montée des politiques industrielles coordonnées

**Rôle système**
- variable régulée par gouvernance institutionnelle
- stabilisateur des transitions technologiques

**Couplages**
- [[gouvernance_institutions]] : 80
- [[systeme_economique_redistribution]] : 75
- [[technologie_information]] : 70
- [[organisation_territoires]] : 60

### [[reference]]
- **level** : 70 | **volatility** : 60

Système productif mondial en transition hybride entre travail humain et automatisation, caractérisé par une montée continue de l’IA industrielle et une réduction progressive du travail humain direct sans rupture complète du modèle salarial. dominant_dynamics: - automatisation progressive des chaînes de production - coexistence humain-machine dans la production - fragmentation partielle des chaînes globales system_role_shift: - moteur productif central du système global - interface critique entre technologie, énergie et économie coupling_intensity: systeme_economique_redistribution: 80 technologie_information: 85 energie_ressources_critiques: 75 organisation_des_territoires: 70

**Dynamiques dominantes**
- automatisation progressive des chaînes de production
- coexistence humain-machine dans la production
- fragmentation partielle des chaînes globales

**Rôle système**
- moteur productif central du système global
- interface critique entre technologie, énergie et économie

**Couplages**
- [[systeme_economique_redistribution]] : 80
- [[technologie_information]] : 85
- [[energie_ressources_critiques]] : 75
- [[organisation_territoires]] : 70



## 9. Scénarios liés

**Dominants** : [[new_sustainability]]
**Renforcés** : [[reference]], [[policy_reform]]
**Contraints** : [[breakdown]], [[eco_communalism]]

## 10. Narratif systémique

**Résumé**
Les systèmes productifs évoluent vers une automatisation généralisée transformant profondément la structure du travail humain.

**Dynamiques**
L’intégration de l’IA et de la robotisation accélère la productivité tout en réduisant la place du travail humain direct.

**Interprétation**
Dans la logique Ourrassol, cette variable est un relais majeur de transformation entre technologie et économie, produisant des effets systémiques sur toutes les variables sociales et économiques.

**Implications**
Elle restructure l’économie, la redistribution, la démographie et les systèmes territoriaux en imposant une transition vers des modèles post-travail ou hybrides.

## 11. Métadonnées de simulation
| Paramètre | Valeur |
|---|---|
| volatility | medium |
| predictability | medium |
| uncertainty_level | medium |
| tipping_point_risk | medium |
| systemic_criticality | 4 |
| resilience | 3 |
| adaptability | 4 |

## 12. Trajectoire des signaux 2025 → 2098

Évolution des signaux faibles selon le scénario — comment les précurseurs de 2025 sont devenus des réalités en 2098.

```yaml
signal_to_state:
  - signal: automatisation_cognitive
    scenarios:
      breakdown:
        evolution: effondrement de l'emploi sans filets de sécurité ni reconversion
        date_bascule: 2038-2056
        evenement_cle: chômage structurel à 45% dans les économies avancées 2049
      fortress_world:
        evolution: automatisation au service des appareils productifs des blocs
        date_bascule: 2034-2050
        evenement_cle: déploiement des usines entièrement automatisées des blocs 2045
      new_sustainability:
        evolution: transition vers le travail de sens avec revenu universel
        date_bascule: 2032-2048
        evenement_cle: instauration du revenu universel global 2041
      eco_communalism:
        evolution: rejet de l'automatisation lourde au profit du travail artisanal local
        date_bascule: 2038-2057
        evenement_cle: mouvement néo-artisanal et de l'économie du soin
      policy_reform:
        evolution: régulation de l'automatisation et fonds de reconversion
        date_bascule: 2028-2044
        evenement_cle: Taxe Tobin sur l'automatisation et fonds de reconversion 2036
      reference:
        evolution: disruption progressive sans politique de transition cohérente
        date_bascule: 2024-2039
        evenement_cle: première vague de désindustrialisation cognitive 2031

  - signal: fragmentation_chaines_valeur
    scenarios:
      breakdown:
        evolution: effondrement des chaînes logistiques mondiales et pénuries systémiques
        date_bascule: 2040-2058
        evenement_cle: rupture simultanée de 60% des chaînes d'approvisionnement 2051
      fortress_world:
        evolution: reconstruction des chaînes de valeur à l'intérieur des blocs fermés
        date_bascule: 2035-2051
        evenement_cle: programme de réindustrialisation interne des blocs 2046
      new_sustainability:
        evolution: chaînes de valeur résilientes et tracées par IA globale
        date_bascule: 2030-2046
        evenement_cle: déploiement du système mondial de traçabilité des chaînes 2038
      eco_communalism:
        evolution: relocalisation radicale et circuits courts systémiques
        date_bascule: 2037-2056
        evenement_cle: mouvement de localisation des chaînes de valeur essentielles
      policy_reform:
        evolution: diversification et régulation des chaînes critiques
        date_bascule: 2026-2041
        evenement_cle: directive sur la résilience des chaînes d'approvisionnement critiques 2032
      reference:
        evolution: fragilisation progressive avec crises ponctuelles
        date_bascule: 2022-2037
        evenement_cle: troisième crise des semiconducteurs 2029

  - signal: robotisation_services
    scenarios:
      breakdown:
        evolution: abandon des robots de service reconvertis pour la survie urbaine
        date_bascule: 2036-2055
        evenement_cle: réquisition massive des robots de service dans les mégapoles 2050
      fortress_world:
        evolution: généralisation de la robotisation des services dans les secteurs des blocs
        date_bascule: 2033-2050
        evenement_cle: déploiement des robots de service dans les administrations des blocs 2046
      new_sustainability:
        evolution: intégration complète de la robotisation libérant le travail humain créatif
        date_bascule: 2033-2049
        evenement_cle: généralisation mondiale des robots de service dans le tertiaire 2039
      eco_communalism:
        evolution: rejet de la robotisation des services au profit du lien humain
        date_bascule: 2036-2055
        evenement_cle: charte bioterritoriale pour des services assurés par des humains
      policy_reform:
        evolution: encadrement de la robotisation des services avec garanties de reconversion
        date_bascule: 2027-2043
        evenement_cle: adoption de la charte de transition des métiers de service 2034
      reference:
        evolution: robotisation progressive et inégale des services selon les secteurs
        date_bascule: 2023-2038
        evenement_cle: premier déploiement massif de robots dans la restauration 2030

  - signal: disparition_metiers_intermediaires
    scenarios:
      breakdown:
        evolution: disparition totale des métiers intermédiaires accentuant la polarisation sociale
        date_bascule: 2037-2057
        evenement_cle: fermeture de la dernière grande filière de formation intermédiaire 2049
      fortress_world:
        evolution: absorption des métiers intermédiaires dans l'appareil administratif des blocs
        date_bascule: 2036-2052
        evenement_cle: reconversion forcée des métiers intermédiaires vers les administrations des blocs 2045
      new_sustainability:
        evolution: remplacement des métiers intermédiaires par des rôles hybrides humain-IA accompagnés
        date_bascule: 2031-2047
        evenement_cle: lancement du programme mondial de reconversion vers les métiers hybrides 2038
      eco_communalism:
        evolution: renaissance des métiers intermédiaires sous forme de savoir-faire locaux essentiels
        date_bascule: 2039-2058
        evenement_cle: mouvement de revalorisation des savoir-faire intermédiaires bioterritoriaux
      policy_reform:
        evolution: transformation progressive des métiers intermédiaires via des programmes de reconversion coordonnés
        date_bascule: 2025-2040
        evenement_cle: lancement du plan international de reconversion professionnelle 2033
      reference:
        evolution: déclin régulier des métiers intermédiaires avec reconversions partielles
        date_bascule: 2025-2040
        evenement_cle: premier rapport sur la disparition accélérée des métiers intermédiaires 2030

  - signal: automatisation_agricole_massive
    scenarios:
      breakdown:
        evolution: effondrement de l'agriculture automatisée provoquant des crises alimentaires régionales
        date_bascule: 2041-2059
        evenement_cle: pannes simultanées des fermes automatisées de trois continents 2052
      fortress_world:
        evolution: sécurisation de l'agriculture automatisée comme actif stratégique des blocs
        date_bascule: 2037-2053
        evenement_cle: nationalisation des fermes automatisées stratégiques par les blocs 2047
      new_sustainability:
        evolution: intégration de l'agriculture automatisée dans la régénération écologique mondiale
        date_bascule: 2034-2050
        evenement_cle: lancement du programme mondial d'agriculture régénérative automatisée 2040
      eco_communalism:
        evolution: réduction de l'automatisation agricole au profit de la permaculture locale
        date_bascule: 2040-2059
        evenement_cle: mouvement de retour aux pratiques agricoles low-tech bioterritoriales
      policy_reform:
        evolution: régulation de l'automatisation agricole pour protéger emplois ruraux et écosystèmes
        date_bascule: 2029-2045
        evenement_cle: adoption de la directive sur l'automatisation agricole responsable 2035
      reference:
        evolution: expansion inégale de l'automatisation agricole aux impacts ruraux mixtes
        date_bascule: 2026-2041
        evenement_cle: premier rapport sur l'impact rural de l'automatisation agricole 2031

  - signal: normalisation_post_travail
    scenarios:
      breakdown:
        evolution: effacement du récit post-travail face à l'économie de survie
        date_bascule: 2042-2060
        evenement_cle: retour massif au travail de subsistance non rémunéré 2050
      fortress_world:
        evolution: réservation du récit post-travail aux élites des blocs sécurisés
        date_bascule: 2038-2054
        evenement_cle: instauration du statut de citoyen productif obligatoire des blocs 2046
      new_sustainability:
        evolution: normalisation mondiale du récit post-travail comme nouvelle norme culturelle
        date_bascule: 2029-2045
        evenement_cle: adoption du récit mondial de la société post-travail 2039
      eco_communalism:
        evolution: recadrage du post-travail comme contribution choisie à la vie collective
        date_bascule: 2041-2060
        evenement_cle: manifeste bioterritorial de la contribution choisie
      policy_reform:
        evolution: acceptation progressive du post-travail via la réduction du temps de travail
        date_bascule: 2030-2046
        evenement_cle: adoption de la semaine de travail réduite à l'échelle mondiale 2033
      reference:
        evolution: persistance marginale du récit post-travail dans le débat culturel
        date_bascule: 2027-2042
        evenement_cle: premier débat médiatique mondial sur la fin du travail 2030
```
