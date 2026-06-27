---
name: valeurs_culture_tempo_sociale
type: systemic_variable
slug: valeurs_culture_tempo_sociale
variable_type: reactive
global_influence_level: 3
domain:
    - social
    - cultural
    - geopolitical
influences:
    - [[gouvernance_institutions]]
    - [[demographie_mobilite_humaine]]
    - [[systeme_economique_redistribution]]
influenced_by:
    - [[technologie_information]]
    - [[gouvernance_institutions]]
    - [[systeme_economique_redistribution]]
bidirectional_links:
    - [[technologie_information]]
    - [[gouvernance_institutions]]
sub_variables:
  - name: systemes_de_valeurs
    role: Cadres moraux structurant les sociétés et leurs normes collectives.
    trend: unstable
    links:
      - [[gouvernance_institutions]]
  - name: religion_et_spiritualite
    role: Cadres symboliques et existentiels organisant le sens collectif.
    trend: up
  - name: rapport_au_temps_social
    role: Perception collective du temps (accélération, rupture, continuité).
    trend: accelerating
    links:
      - [[technologie_information]]
      - [[systemes_productifs_travail]]
  - name: identites_culturelles
    role: Structures d’appartenance collective et identitaire.
    trend: up
    links:
      - [[demographie_mobilite_humaine]]
      - [[geopolitique_conflits]]
  - name: medias_et_recits_collectifs
    role: Production et diffusion des représentations symboliques.
    trend: up
    links:
      - [[technologie_information]]
      - [[systeme_economique_redistribution]]

scenario_mapping:
  dominant_scenarios:
    - reference
  reinforcing_scenarios:
    - policy_reform
  constrained_scenarios:
    - breakdown
    - fortress_world
simulation:
  volatility: low
  predictability: low
  uncertainty_level: medium
  tipping_point_risk: medium
  systemic_criticality: 3
  resilience: 4
  adaptability: 4
states:

  fortress_world:
    level: 80
    volatility: 75
    state_logic: >
      Organisation du monde en blocs culturels fermés avec identités fortes, systèmes de valeurs incompatibles et forte instrumentalisation des récits culturels dans les compétitions géopolitiques.
    dominant_dynamics:
      - blocage des échanges culturels globaux
      - durcissement des identités collectives
      - instrumentalisation politique des récits
    system_role_shift:
      - infrastructure de séparation idéologique globale
      - stabilisateur interne des blocs géopolitiques
    coupling_intensity:
      [[geopolitique_conflits]]: 95
      [[frontieres_du_systeme]]: 80
      [[gouvernance_institutions]]: 75
      [[technologie_information]]: 70

  new_sustainability:
    level: 55
    volatility: 45
    state_logic: >
      Système culturel hybride humain-IA stabilisé, où les récits sont co-produits, régulés et adaptés en continu pour maintenir une cohésion minimale globale malgré la diversité des valeurs.
    dominant_dynamics:
      - co-production de récits humains et IA
      - stabilisation algorithmique des tensions culturelles
      - synchronisation partielle des temporalités sociales
    system_role_shift:
      - infrastructure de cohésion cognitive globale
      - régulateur adaptatif des récits collectifs
    coupling_intensity:
      [[technologie_information]]: 90
      [[gouvernance_institutions]]: 80
      [[systeme_economique_redistribution]]: 75
      [[systemes_productifs_travail]]: 70

  breakdown:
    level: 90
    volatility: 95
    state_logic: >
      Effondrement des récits communs et fragmentation extrême des systèmes de valeurs, conduisant à une perte de synchronisation sociale globale et à la polarisation durable des identités culturelles.
    dominant_dynamics:
      - rupture des référentiels culturels partagés
      - polarisation idéologique extrême
      - désynchronisation générationnelle et sociale
    system_role_shift:
      - facteur de désintégration sociale lente mais profonde
      - amplification des fractures systémiques globales
    coupling_intensity:
      [[geopolitique_conflits]]: 85
      [[gouvernance_institutions]]: 80
      [[technologie_information]]: 80
      [[systeme_economique_redistribution]]: 70

  eco_communalism:
    level: 40
    volatility: 30
    state_logic: >
      Recomposition locale des systèmes de valeurs autour de communautés restreintes, avec ralentissement du temps social, sobriété symbolique et retour de récits culturels situés et cohérents à petite échelle.
    dominant_dynamics:
      - relocalisation des récits culturels
      - ralentissement du tempo social
      - stabilisation communautaire des valeurs
    system_role_shift:
      - variable culturelle décentralisée et localisée
      - facteur de cohésion communautaire forte
    coupling_intensity:
      [[organisation_territoires]]: 85
      [[systemes_productifs_travail]]: 65
      [[systeme_economique_redistribution]]: 60

  policy_reform:
    level: 50
    volatility: 40
    state_logic: >
      Tentatives institutionnelles de stabilisation culturelle via régulation des médias, encadrement des plateformes numériques et politiques de cohésion sociale visant à reconstruire des récits communs partiels dans un environnement fragmenté.
    dominant_dynamics:
      - régulation des récits médiatiques et algorithmiques
      - politiques de cohésion culturelle et éducative
      - stabilisation partielle des identités collectives
    system_role_shift:
      - variable partiellement gouvernée et normalisée
      - outil de stabilisation sociale indirecte
    coupling_intensity:
      [[gouvernance_institutions]]: 85
      [[technologie_information]]: 80
      [[systeme_economique_redistribution]]: 70
      [[organisation_territoires]]: 65

  reference:
    level: 60
    volatility: 55
    state_logic: >
      Système culturel global fragmenté mais interconnecté, dominé par une accélération du temps social et une coexistence instable de systèmes de valeurs multiples. Les récits collectifs sont partiellement maintenus via les infrastructures numériques et les médias algorithmiques, mais perdent leur cohérence unifiée.
    dominant_dynamics:
      - fragmentation progressive des systèmes de valeurs
      - accélération du temps social perçu
      - coexistence de récits culturels multiples et instables
    system_role_shift:
      - régulateur lent de cohésion sociale globale
      - stabilisateur partiel des identités collectives
    coupling_intensity:
      [[technologie_information]]: 85
      [[systeme_economique_redistribution]]: 75
      [[systemes_productifs_travail]]: 70
      [[gouvernance_institutions]]: 80

---

# valeurs_culture_tempo_sociale

## 1. Identité systémique

**Description**
Variable structurante des représentations collectives, des systèmes de croyance, des normes sociales et du rapport au temps. Elle conditionne la cohésion sociale, la légitimité des institutions et la stabilité des récits communs dans un contexte de numérisation et d’accélération du temps social.

**Rôle**
Infrastructure cognitive et symbolique des sociétés humaines. Elle régule les valeurs, les identités collectives et la perception du temps, influençant directement la stabilité politique, économique et sociale.

## 2. Position dans le système

**Influence**
- [[gouvernance_institutions]]
- [[demographie_mobilite_humaine]]
- [[systeme_economique_redistribution]]

**Influencé par**
- [[technologie_information]]
- [[gouvernance_institutions]]
- [[systeme_economique_redistribution]]

**Liens bidirectionnels**
- [[technologie_information]]
- [[gouvernance_institutions]]

## 3. Dynamique interne
- Direction : **oscillating** | Intensité : **high** | Inertie : **high** | Vitesse : **slow**

**Tendances**
- fragmentation des systèmes de valeurs
- accélération du temps social perçu
- hyper-individualisation des normes sociales
- montée des identités culturelles multiples
- disparition des récits unifiés
- numérisation des interactions symboliques
- tension tradition vs modernité
- algorithmisation des récits médiatiques

**Dynamiques passées**
- domination des systèmes religieux structurants
- transition vers la modernité et la sécularisation
- diffusion des valeurs industrielles
- mondialisation culturelle
- montée de l’individualisme
- fragmentation des grands récits
- essor des médias de masse puis des réseaux sociaux
- accélération du temps social via le numérique

**Snapshot**
> Système en fragmentation progressive avec accélération du temps social et coexistence de systèmes de valeurs multiples dans un environnement numérique fortement médiatisé et algorithmisé.

**tensions**
- tradition vs modernité
- universalisation vs fragmentation culturelle
- accélération du temps social vs stabilité
- identités locales vs globalisation
- humain vs culture générée par IA

**constraints**
- inertie des traditions culturelles
- influence des plateformes numériques
- saturation informationnelle
- dépendance aux médias globaux
- polarisation des espaces publics

**forces_attractives**
- diversité culturelle
- innovation symbolique
- création de nouveaux récits
- adaptation sociale
- résilience des traditions locales

**forces_repulsives**
- fragmentation des valeurs
- polarisation idéologique
- perte de repères communs
- accélération excessive du temps social
- conflits intergénérationnels


## 4. Structure causale

**Forces attractives**
- cohésion sociale potentielle
- innovation culturelle
- adaptation aux transformations technologiques
- création de récits communs
- résilience identitaire locale

**Forces répulsives**
- fragmentation culturelle
- polarisation idéologique
- perte de repères collectifs
- accélération du temps social
- conflits de valeurs

**Contraintes**
- inertie culturelle
- dépendance aux médias numériques
- saturation informationnelle
- fragmentation des espaces publics

**Tensions**
- tradition vs modernité
- globalisation vs identités locales
- accélération vs stabilité
- humain vs culture automatisée

## 5. Ruptures

**technological**
_core_
- culture generee par ia
- realite augmentee totale
- interfaces cerveau-machine culturelles
- systemes de recommandation totalises
_extended_
- virtualisation complete des experiences sociales
- automatisation des recits symboliques
- hybridation humain-ia des identites culturelles

**systemic**
_core_
- effondrement des recits communs
- polarisation extreme des valeurs
- fragmentation des temporalites sociales
- rupture des identites collectives
_extended_
- coexistence de realites culturelles paralleles
- perte de synchronisation sociale globale
- instabilite durable des normes collectives

**political_social**
_core_
- guerres culturelles globales
- controle des recits
- ingenierie culturelle et symbolique
- retour de structures traditionnelles fortes
_extended_
- fragmentation institutionnelle des valeurs
- manipulation algorithmique des imaginaires
- recomposition autoritaire des normes sociales


## 6. Indicateurs
**primary**
- polarisation culturelle
- acceleration du temps social
- fragmentation des valeurs
- consommation de medias numeriques

**secondary**
- production culturelle par IA
- conflits culturels en ligne
- recomposition des identites
- evolution des recits mediatiques

**systemic**
- synchronisation sociale globale
- stabilite des normes culturelles
- coherence des recits collectifs



## 7. Signaux faibles
**technological**
- essor contenus culturels ia
- automatisation des recits mediatiques
- interfaces culturelles immersives
- systemes de recommandation avances

**geopolitical**
- guerres culturelles transnationales (→ section 12)
- instrumentalisation des identites
- fragmentation des spheres mediatiques

**social**
- communautes identitaires fermees
- desynchronisation generationnelle (→ section 12)
- hyper-individualisation accrue

**environmental**
- acceleration des rythmes de vie urbains (→ section 12)
- pression cognitive continue
- surcharge informationnelle sociale

**cognitive_cultural**
- perte de referentiels communs
- retour de spiritualites hybrides (→ section 12)
- multiplication des narratifs concurrents



## 8. États par scénario
### [[fortress_world]]
- **level** : 80 | **volatility** : 75

Organisation du monde en blocs culturels fermés avec identités fortes, systèmes de valeurs incompatibles et forte instrumentalisation des récits culturels dans les compétitions géopolitiques. dominant_dynamics: - blocage des échanges culturels globaux - durcissement des identités collectives - instrumentalisation politique des récits system_role_shift: - infrastructure de séparation idéologique globale - stabilisateur interne des blocs géopolitiques coupling_intensity: geopolitique_conflits: 95 frontieres_du_systeme: 80 gouvernance_institutions: 75 technologie_information: 70

**Dynamiques dominantes**
- blocage des échanges culturels globaux
- durcissement des identités collectives
- instrumentalisation politique des récits

**Rôle système**
- infrastructure de séparation idéologique globale
- stabilisateur interne des blocs géopolitiques

**Couplages**
- [[geopolitique_conflits]] : 95
- [[frontieres_du_systeme]] : 80
- [[gouvernance_institutions]] : 75
- [[technologie_information]] : 70

### [[new_sustainability]]
- **level** : 55 | **volatility** : 45

Système culturel hybride humain-IA stabilisé, où les récits sont co-produits, régulés et adaptés en continu pour maintenir une cohésion minimale globale malgré la diversité des valeurs. dominant_dynamics: - co-production de récits humains et IA - stabilisation algorithmique des tensions culturelles - synchronisation partielle des temporalités sociales system_role_shift: - infrastructure de cohésion cognitive globale - régulateur adaptatif des récits collectifs coupling_intensity: technologie_information: 90 gouvernance_institutions: 80 systeme_economique_redistribution: 75 systemes_productifs_travail: 70

**Dynamiques dominantes**
- co-production de récits humains et IA
- stabilisation algorithmique des tensions culturelles
- synchronisation partielle des temporalités sociales

**Rôle système**
- infrastructure de cohésion cognitive globale
- régulateur adaptatif des récits collectifs

**Couplages**
- [[technologie_information]] : 90
- [[gouvernance_institutions]] : 80
- [[systeme_economique_redistribution]] : 75
- [[systemes_productifs_travail]] : 70

### [[breakdown]]
- **level** : 90 | **volatility** : 95

Effondrement des récits communs et fragmentation extrême des systèmes de valeurs, conduisant à une perte de synchronisation sociale globale et à la polarisation durable des identités culturelles. dominant_dynamics: - rupture des référentiels culturels partagés - polarisation idéologique extrême - désynchronisation générationnelle et sociale system_role_shift: - facteur de désintégration sociale lente mais profonde - amplification des fractures systémiques globales coupling_intensity: geopolitique_conflits: 85 gouvernance_institutions: 80 technologie_information: 80 systeme_economique_redistribution: 70

**Dynamiques dominantes**
- rupture des référentiels culturels partagés
- polarisation idéologique extrême
- désynchronisation générationnelle et sociale

**Rôle système**
- facteur de désintégration sociale lente mais profonde
- amplification des fractures systémiques globales

**Couplages**
- [[geopolitique_conflits]] : 85
- [[gouvernance_institutions]] : 80
- [[technologie_information]] : 80
- [[systeme_economique_redistribution]] : 70

### [[eco_communalism]]
- **level** : 40 | **volatility** : 30

Recomposition locale des systèmes de valeurs autour de communautés restreintes, avec ralentissement du temps social, sobriété symbolique et retour de récits culturels situés et cohérents à petite échelle. dominant_dynamics: - relocalisation des récits culturels - ralentissement du tempo social - stabilisation communautaire des valeurs system_role_shift: - variable culturelle décentralisée et localisée - facteur de cohésion communautaire forte coupling_intensity: organisation_des_territoires: 85 systemes_productifs_travail: 65 systeme_economique_redistribution: 60

**Dynamiques dominantes**
- relocalisation des récits culturels
- ralentissement du tempo social
- stabilisation communautaire des valeurs

**Rôle système**
- variable culturelle décentralisée et localisée
- facteur de cohésion communautaire forte

**Couplages**
- [[organisation_territoires]] : 85
- [[systemes_productifs_travail]] : 65
- [[systeme_economique_redistribution]] : 60

### [[policy_reform]]
- **level** : 50 | **volatility** : 40

Tentatives institutionnelles de stabilisation culturelle via régulation des médias, encadrement des plateformes numériques et politiques de cohésion sociale visant à reconstruire des récits communs partiels dans un environnement fragmenté. dominant_dynamics: - régulation des récits médiatiques et algorithmiques - politiques de cohésion culturelle et éducative - stabilisation partielle des identités collectives system_role_shift: - variable partiellement gouvernée et normalisée - outil de stabilisation sociale indirecte coupling_intensity: gouvernance_institutions: 85 technologie_information: 80 systeme_economique_redistribution: 70 organisation_des_territoires: 65

**Dynamiques dominantes**
- régulation des récits médiatiques et algorithmiques
- politiques de cohésion culturelle et éducative
- stabilisation partielle des identités collectives

**Rôle système**
- variable partiellement gouvernée et normalisée
- outil de stabilisation sociale indirecte

**Couplages**
- [[gouvernance_institutions]] : 85
- [[technologie_information]] : 80
- [[systeme_economique_redistribution]] : 70
- [[organisation_territoires]] : 65

### [[reference]]
- **level** : 60 | **volatility** : 55

Système culturel global fragmenté mais interconnecté, dominé par une accélération du temps social et une coexistence instable de systèmes de valeurs multiples. Les récits collectifs sont partiellement maintenus via les infrastructures numériques et les médias algorithmiques, mais perdent leur cohérence unifiée. dominant_dynamics: - fragmentation progressive des systèmes de valeurs - accélération du temps social perçu - coexistence de récits culturels multiples et instables system_role_shift: - régulateur lent de cohésion sociale globale - stabilisateur partiel des identités collectives coupling_intensity: technologie_information: 85 systeme_economique_redistribution: 75 systemes_productifs_travail: 70 gouvernance_institutions: 80

**Dynamiques dominantes**
- fragmentation progressive des systèmes de valeurs
- accélération du temps social perçu
- coexistence de récits culturels multiples et instables

**Rôle système**
- régulateur lent de cohésion sociale globale
- stabilisateur partiel des identités collectives

**Couplages**
- [[technologie_information]] : 85
- [[systeme_economique_redistribution]] : 75
- [[systemes_productifs_travail]] : 70
- [[gouvernance_institutions]] : 80



## 9. Scénarios liés

**Dominants** : [[reference]]
**Renforcés** : [[policy_reform]]
**Contraints** : [[breakdown]], [[fortress_world]]

## 10. Narratif systémique

**Résumé**
Fragmentation progressive des systèmes de valeurs et accélération du temps social.

**Dynamiques**
Les transformations technologiques et numériques accélèrent la production, la diffusion et la fragmentation des récits culturels.

**Interprétation**
Dans la logique Ourrassol, cette variable agit comme un régulateur lent mais profond de la cohésion systémique globale.

**Implications**
Elle influence la gouvernance, l’économie, la démographie et la stabilité géopolitique via la structuration des normes collectives.

## 11. Métadonnées de simulation
| Paramètre | Valeur |
|---|---|
| volatility | low |
| predictability | low |
| uncertainty_level | medium |
| tipping_point_risk | medium |
| systemic_criticality | 3 |
| resilience | 4 |
| adaptability | 4 |

## 12. Trajectoire des signaux 2025 → 2098

Évolution des signaux faibles selon le scénario — comment les précurseurs de 2025 sont devenus des réalités en 2098.

```yaml
signal_to_state:
  - signal: hybridation_ia_culture
    scenarios:
      breakdown:
        evolution: chaos informationnel et destruction des récits communs
        date_bascule: 2040-2058
        evenement_cle: prolifération non contrôlée des IA génératives culturelles
      fortress_world:
        evolution: IA culturelles au service des récits identitaires des blocs
        date_bascule: 2036-2051
        evenement_cle: déploiement des systèmes de production culturelle des blocs
      new_sustainability:
        evolution: co-création culturelle humain-IA régulée et enrichissante
        date_bascule: 2032-2047
        evenement_cle: Charte mondiale de l'IA créative 2039
      eco_communalism:
        evolution: rejet de l'IA culturelle au profit des expressions locales
        date_bascule: 2042-2060
        evenement_cle: mouvement de réappropriation culturelle locale
      policy_reform:
        evolution: régulation des droits d'auteur et de l'IA créative
        date_bascule: 2029-2044
        evenement_cle: traité international sur la propriété intellectuelle et l'IA 2036
      reference:
        evolution: domination croissante sans régulation cohérente
        date_bascule: 2026-2040
        evenement_cle: première crise des droits d'auteur IA globale 2031

  - signal: fatigue_civilisationnelle
    scenarios:
      breakdown:
        evolution: effondrement des récits collectifs et anomie sociale généralisée
        date_bascule: 2043-2062
        evenement_cle: mouvement de décrochage sociétal global
      fortress_world:
        evolution: réactivation des récits nationalistes et identitaires fermés
        date_bascule: 2037-2052
        evenement_cle: renaissance des mouvements civilisationnels des blocs
      new_sustainability:
        evolution: émergence d'un récit global de transition positive partagé
        date_bascule: 2033-2048
        evenement_cle: premier Forum Mondial des Civilisations Régénératives 2041
      eco_communalism:
        evolution: recomposition de récits locaux forts et cohérents
        date_bascule: 2040-2058
        evenement_cle: renaissance des cultures situées et des récits de lieu
      policy_reform:
        evolution: politiques culturelles publiques de reconstruction du récit commun
        date_bascule: 2031-2046
        evenement_cle: programme UNESCO de recomposition culturelle post-crise
      reference:
        evolution: fragmentation croissante des récits sans rupture totale
        date_bascule: 2027-2041
        evenement_cle: première décennie perdue de cohésion culturelle 2035

  - signal: guerres_culturelles_transnationales
    scenarios:
      breakdown:
        evolution: guerres culturelles transnationales dégénérant en violences identitaires généralisées
        date_bascule: 2038-2057
        evenement_cle: premiers affrontements identitaires transfrontaliers coordonnés 2049
      fortress_world:
        evolution: institutionnalisation des guerres culturelles comme doctrine d'opposition entre blocs
        date_bascule: 2035-2050
        evenement_cle: lancement de la doctrine de guerre culturelle des blocs 2045
      new_sustainability:
        evolution: désamorçage des guerres culturelles via des institutions mondiales de dialogue
        date_bascule: 2030-2045
        evenement_cle: création du forum mondial de dialogue interculturel permanent 2038
      eco_communalism:
        evolution: désengagement des guerres culturelles globales au profit du récit local
        date_bascule: 2038-2056
        evenement_cle: mouvement bioterritorial de désengagement des récits globaux
      policy_reform:
        evolution: atténuation progressive des guerres culturelles via programmes de dialogue encadrés
        date_bascule: 2026-2042
        evenement_cle: lancement du programme international d'éducation au dialogue interculturel 2033
      reference:
        evolution: persistance des guerres culturelles comme trait récurrent du paysage médiatique
        date_bascule: 2023-2038
        evenement_cle: première étude mondiale sur la polarisation culturelle médiatique 2030

  - signal: desynchronisation_generationnelle
    scenarios:
      breakdown:
        evolution: rupture ouverte entre générations sans référentiel temporel commun
        date_bascule: 2039-2058
        evenement_cle: premières émeutes intergénérationnelles documentées dans les mégapoles 2050
      fortress_world:
        evolution: assignation rigide des rôles générationnels dans la hiérarchie des blocs
        date_bascule: 2038-2053
        evenement_cle: instauration de quotas générationnels dans les administrations des blocs 2048
      new_sustainability:
        evolution: resynchronisation générationnelle via des récits et rôles partagés régénératifs
        date_bascule: 2031-2046
        evenement_cle: lancement du pacte intergénérationnel mondial pour la régénération 2039
      eco_communalism:
        evolution: réorganisation des rôles générationnels autour du mentorat communautaire local
        date_bascule: 2039-2057
        evenement_cle: charte bioterritoriale du mentorat intergénérationnel
      policy_reform:
        evolution: atténuation des tensions générationnelles par des programmes de dialogue public
        date_bascule: 2027-2043
        evenement_cle: lancement du programme national de dialogue intergénérationnel 2034
      reference:
        evolution: désynchronisation générationnelle continue malgré des efforts d'atténuation partiels
        date_bascule: 2024-2039
        evenement_cle: premier rapport mondial sur la fracture générationnelle 2031

  - signal: acceleration_rythmes_vie_urbains
    scenarios:
      breakdown:
        evolution: effondrement des rythmes urbains en mode survie permanent
        date_bascule: 2041-2059
        evenement_cle: abolition de facto des horaires sociaux dans les mégapoles 2052
      fortress_world:
        evolution: régimentation des rythmes urbains au service de la productivité des blocs
        date_bascule: 2039-2054
        evenement_cle: instauration des cycles de vie optimisés dans les blocs 2049
      new_sustainability:
        evolution: rééquilibrage des rythmes urbains via une planification adaptative mondiale par IA
        date_bascule: 2034-2049
        evenement_cle: déploiement mondial des horaires adaptatifs urbains pilotés par IA 2042
      eco_communalism:
        evolution: ralentissement radical des rythmes urbains alignés sur les cycles naturels
        date_bascule: 2041-2059
        evenement_cle: charte bioterritoriale du tempo lent et des cycles naturels
      policy_reform:
        evolution: régulation progressive des rythmes urbains par des réformes horaires
        date_bascule: 2028-2044
        evenement_cle: adoption de la charte internationale des rythmes urbains soutenables 2035
      reference:
        evolution: accélération continue des rythmes urbains malgré des mesures partielles
        date_bascule: 2025-2040
        evenement_cle: premier rapport mondial sur l'accélération des rythmes urbains 2032

  - signal: retour_spiritualites_hybrides
    scenarios:
      breakdown:
        evolution: prolifération chaotique de cultes de survie hybrides dans le chaos
        date_bascule: 2044-2063
        evenement_cle: émergence de cultes de survie dans les zones effondrées 2055
      fortress_world:
        evolution: récupération des spiritualités hybrides comme ciment idéologique des blocs
        date_bascule: 2040-2055
        evenement_cle: adoption d'une spiritualité officielle hybride par les blocs 2050
      new_sustainability:
        evolution: intégration des spiritualités hybrides dans un ethos régénératif mondial partagé
        date_bascule: 2035-2050
        evenement_cle: lancement du mouvement spirituel mondial de la régénération 2043
      eco_communalism:
        evolution: ancrage des spiritualités hybrides comme fondement de la vie bioterritoriale
        date_bascule: 2043-2061
        evenement_cle: fondation des premières communautés spirituelles bioterritoriales
      policy_reform:
        evolution: reconnaissance institutionnelle des spiritualités hybrides dans les politiques culturelles
        date_bascule: 2030-2045
        evenement_cle: adoption du cadre légal de reconnaissance des spiritualités hybrides 2037
      reference:
        evolution: diffusion graduelle des spiritualités hybrides comme phénomène culturel de niche
        date_bascule: 2028-2042
        evenement_cle: premier recensement mondial des spiritualités hybrides émergentes 2035
```
