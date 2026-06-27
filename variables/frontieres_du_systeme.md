---
name: frontieres_du_systeme
type: systemic_variable
slug: frontieres_du_systeme
variable_type: reactive
global_influence_level: 2
domain:
    - technological
    - geopolitical
    - economic
influences:
    - [[technologie_information]]
    - [[systeme_economique_redistribution]]
    - [[geopolitique_conflits]]
influenced_by:
    - [[technologie_information]]
    - [[geopolitique_conflits]]
    - [[energie_ressources_critiques]]
    - [[gouvernance_institutions]]
    - [[systeme_economique_redistribution]]
bidirectional_links:
    - [[technologie_information]]
    - [[geopolitique_conflits]]
    - [[energie_ressources_critiques]]
sub_variables:
  - name: infrastructure_orbitale
    role: Support technologique des activités humaines en orbite terrestre.
    trend: up
    links:
      - [[technologie_information]]
      - [[geopolitique_conflits]]
  - name: exploration_planetaire
    role: Exploration robotique et humaine du système solaire.
    trend: up
    links:
      - [[energie_ressources_critiques]]
      - [[technologie_information]]
  - name: industrie_spatiale
    role: Production et exploitation économique en orbite et hors Terre.
    trend: up
    links:
      - [[systeme_economique_redistribution]]
      - [[technologie_information]]
  - name: colonisation_extraterrestre
    role: Implantation humaine durable hors Terre.
    trend: up
    links:
      - [[demographie_mobilite_humaine]]
      - [[gouvernance_institutions]]
  - name: ressources_spatiales
    role: Exploitation des ressources minérales et énergétiques extra-terrestres.
    trend: up
    links:
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
  volatility: very_high
  predictability: low
  uncertainty_level: very_high
  tipping_point_risk: very_high
  systemic_criticality: 5
  resilience: 1
  adaptability: 2
states:

  fortress_world:
    level: 30
    volatility: 60
    state_logic: >
      L’espace devient un domaine stratégique contrôlé par des blocs géopolitiques fermés. Les infrastructures orbitales sont militarisées et utilisées pour la surveillance et la sécurité des systèmes terrestres.
    dominant_dynamics:
      - souveraineté orbitale fragmentée
      - militarisation des infrastructures spatiales
      - contrôle des communications orbitales
    system_role_shift:
      - extension sécuritaire des États
      - espace comme prolongement stratégique terrestre
    coupling_intensity:
      [[geopolitique_conflits]]: 90
      [[energie_ressources_critiques]]: 50
      [[technologie_information]]: 75
      [[organisation_territoires]]: 70

  new_sustainability:
    level: 80
    volatility: 25
    state_logic: >
      Civilisation multi-orbitale avancée avec industrialisation du système solaire proche, exploitation coordonnée des ressources spatiales et intégration complète de l’espace dans le système économique global.
    dominant_dynamics:
      - économie spatiale mature
      - industrialisation extra-planétaire
      - infrastructures autonomes hors Terre
    system_role_shift:
      - extension structurelle du système humain
      - nouvelle dimension du système global
    coupling_intensity:
      [[technologie_information]]: 90
      [[energie_ressources_critiques]]: 70
      [[systeme_economique_redistribution]]: 80
      [[gouvernance_institutions]]: 75

  breakdown:
    level: 15
    volatility: 90
    state_logic: >
      Fragmentation et militarisation de l’espace proche avec saturation des orbites, conflits orbitaux et effondrement de la coopération internationale. L’expansion spatiale devient chaotique et instable.
    dominant_dynamics:
      - conflits orbitaux
      - syndrome de Kessler partiel
      - fermeture géopolitique de l’espace
    system_role_shift:
      - variable militarisée et fragmentée
      - espace comme zone de conflit
    coupling_intensity:
      [[geopolitique_conflits]]: 95
      [[technologie_information]]: 70
      [[frontieres_du_systeme]]: 85
      [[organisation_territoires]]: 60

  eco_communalism:
    level: 50
    volatility: 30
    state_logic: >
      L’expansion spatiale est principalement scientifique, coopérative et orientée vers la connaissance et la préservation du vivant, avec une faible logique d’exploitation économique.
    dominant_dynamics:
      - exploration scientifique collaborative
      - mutualisation des infrastructures spatiales
      - faible militarisation de l’espace
    system_role_shift:
      - bien commun scientifique global
      - extension non extractive du système humain
    coupling_intensity:
      [[gouvernance_institutions]]: 80
      [[technologie_information]]: 75
      [[climat_environnement_global]]: 40
      [[systeme_economique_redistribution]]: 35

  policy_reform:
    level: 45
    volatility: 35
    state_logic: >
      Développement coordonné de l’économie spatiale sous gouvernance internationale, avec régulation des orbites, mutualisation des coûts et coopération scientifique renforcée.
    dominant_dynamics:
      - coopération internationale spatiale
      - industrialisation orbitale régulée
      - gestion des débris et des orbites
    system_role_shift:
      - variable encadrée par gouvernance globale
      - extension contrôlée du système humain
    coupling_intensity:
      [[gouvernance_institutions]]: 85
      [[technologie_information]]: 80
      [[geopolitique_conflits]]: 50
      [[systeme_economique_redistribution]]: 55

  reference:
    level: 25
    volatility: 40
    state_logic: >
      Expansion spatiale limitée à l’orbite terrestre et aux missions robotiques exploratoires. Le système reste fondamentalement terrestre, avec une dépendance totale aux infrastructures et ressources de la Terre.
    dominant_dynamics:
      - exploration spatiale scientifique limitée
      - économie orbitale émergente mais marginale
      - dépendance structurelle à la Terre
    system_role_shift:
      - variable périphérique d’expansion
      - signal de potentiel futur plus que levier actif
    coupling_intensity:
      [[technologie_information]]: 65
      [[energie_ressources_critiques]]: 40
      [[geopolitique_conflits]]: 45
      [[systeme_economique_redistribution]]: 35

---

# frontieres_du_systeme

## 1. Identité systémique

**Description**
Variable représentant l’extension potentielle du système humain au-delà de la Terre. Elle structure la capacité de la civilisation à développer des infrastructures orbitales, exploiter des ressources extra-terrestres et étendre progressivement son espace d’action au-delà des contraintes planétaires actuelles.

**Rôle**
Variable de frontière. Elle définit l’horizon d’expansion physique, technologique et civilisationnelle du système global.

## 2. Position dans le système

**Influence**
- [[technologie_information]]
- [[systeme_economique_redistribution]]
- [[geopolitique_conflits]]

**Influencé par**
- [[technologie_information]]
- [[geopolitique_conflits]]
- [[energie_ressources_critiques]]
- [[gouvernance_institutions]]
- [[systeme_economique_redistribution]]

**Liens bidirectionnels**
- [[technologie_information]]
- [[geopolitique_conflits]]
- [[energie_ressources_critiques]]

## 3. Dynamique interne
- Direction : **up** | Intensité : **medium** | Inertie : **high** | Vitesse : **nonlinear**

**Tendances**
- baisse continue du coût d’accès à l’espace
- multiplication des satellites et infrastructures orbitales
- montée des acteurs privés du spatial
- industrialisation de l’orbite terrestre
- exploration robotique du système solaire
- retour des programmes lunaires et martiens
- structuration d’une économie orbitale
- développement de projets de ressources spatiales

**Dynamiques passées**
- exploration maritime et expansion terrestre
- révolution scientifique et compréhension de l’espace
- course à l’espace USA-URSS
- premiers satellites artificiels
- missions lunaires habitées
- exploration robotique du système solaire
- internationalisation de l’espace (ISS)
- privatisation du secteur spatial
- développement des lanceurs réutilisables
- essor des constellations satellitaires

**Snapshot**
> Extension progressive du système humain vers l’espace proche avec industrialisation de l’orbite terrestre, montée des acteurs privés et émergence d’une économie spatiale encore fragile mais accélérée. La dynamique reste contrainte par les coûts, la physique et la compétition géopolitique.

**tensions**
- exploration scientifique vs exploitation économique
- coopération internationale vs compétition géopolitique
- espace commun vs appropriation privée
- stabilité orbitale vs saturation des débris
- Terre limitée vs expansion exo-planétaire

**constraints**
- gravité et lois physiques
- coûts énergétiques et économiques élevés
- fragilité des infrastructures orbitales
- saturation des orbites et débris spatiaux
- limites actuelles de propulsion

**forces_attractives**
- accès à de nouvelles ressources
- expansion civilisationnelle
- progrès technologique
- sécurisation long terme de l’humanité
- innovation industrielle spatiale

**forces_repulsives**
- coûts extrêmes
- risques techniques élevés
- fragmentation géopolitique de l’espace
- pollution orbitale
- inégalités d’accès


## 4. Structure causale

**Forces attractives**
- expansion civilisationnelle
- innovation technologique
- accès aux ressources spatiales

**Forces répulsives**
- coûts d’infrastructure
- risques techniques
- fragmentation géopolitique
- saturation orbitale

**Contraintes**
- gravité terrestre
- limites de propulsion
- dépendance technologique
- coûts d’accès élevés
- fragilité orbitale

**Tensions**
- science vs exploitation économique
- coopération vs compétition spatiale
- expansion vs contraintes physiques
- espace commun vs appropriation

## 5. Ruptures

**technological**
_core_
- propulsion avancée (fusion, antimatière, voiles solaires)
- colonisation spatiale autonome
- industrie orbitale massive
- IA spatiale autonome
_extended_
- robots auto-réplicants
- terraformage partiel
- infrastructures extra-planétaires permanentes
- industrialisation complète du système solaire proche

**systemic**
_core_
- syndrome de Kessler
- militarisation de l’espace
- saturation des orbites
- conflits orbitaux
_extended_
- effondrement économique spatial
- fragmentation durable des infrastructures orbitales
- rupture des chaînes logistiques spatiales

**political_social**
_core_
- guerres de souveraineté spatiale
- régulation internationale de l’espace
- privatisation totale de l’espace
_extended_
- traités de colonisation extraterrestre
- accès élitiste à l’espace
- nouvelles gouvernances orbitales


## 6. Indicateurs
**primary**
- nombre de satellites actifs
- coût moyen des lancements
- nombre de lancements annuels
- investissements spatiaux privés

**secondary**
- missions lunaires
- missions martiennes
- infrastructures orbitales
- acteurs spatiaux privés

**systemic**
- densité orbitale
- volume économique spatial
- dépendance aux infrastructures orbitales



## 7. Signaux faibles
**technological**
- minage d’astéroïdes (→ minage_asteroides)
- IA spatiale autonome
- industrialisation orbitale privée (→ industrialisation_orbitale_privee)

**geopolitical**
- compétition spatiale entre puissances
- militarisation des infrastructures orbitales

**social**
- économie spatiale privée émergente
- nouvelles communautés orbitales (→ nouvelles_communautes_orbitales)

**environmental**
- augmentation des débris spatiaux
- saturation des orbites basses

**cognitive_cultural**
- retour du récit civilisationnel spatial (→ retour_recit_civilisationnel_spatial)
- normalisation de la présence humaine hors Terre



## 8. États par scénario
### [[fortress_world]]
- **level** : 30 | **volatility** : 60

L’espace devient un domaine stratégique contrôlé par des blocs géopolitiques fermés. Les infrastructures orbitales sont militarisées et utilisées pour la surveillance et la sécurité des systèmes terrestres.

**Dynamiques dominantes**
- souveraineté orbitale fragmentée
- militarisation des infrastructures spatiales
- contrôle des communications orbitales

**Rôle système**
- extension sécuritaire des États
- espace comme prolongement stratégique terrestre

**Couplages**
- [[geopolitique_conflits]] : 90
- [[energie_ressources_critiques]] : 50
- [[technologie_information]] : 75
- [[organisation_territoires]] : 70

### [[new_sustainability]]
- **level** : 80 | **volatility** : 25

Civilisation multi-orbitale avancée avec industrialisation du système solaire proche, exploitation coordonnée des ressources spatiales et intégration complète de l’espace dans le système économique global.

**Dynamiques dominantes**
- économie spatiale mature
- industrialisation extra-planétaire
- infrastructures autonomes hors Terre

**Rôle système**
- extension structurelle du système humain
- nouvelle dimension du système global

**Couplages**
- [[technologie_information]] : 90
- [[energie_ressources_critiques]] : 70
- [[systeme_economique_redistribution]] : 80
- [[gouvernance_institutions]] : 75

### [[breakdown]]
- **level** : 15 | **volatility** : 90

Fragmentation et militarisation de l’espace proche avec saturation des orbites, conflits orbitaux et effondrement de la coopération internationale. L’expansion spatiale devient chaotique et instable.

**Dynamiques dominantes**
- conflits orbitaux
- syndrome de Kessler partiel
- fermeture géopolitique de l’espace

**Rôle système**
- variable militarisée et fragmentée
- espace comme zone de conflit

**Couplages**
- [[geopolitique_conflits]] : 95
- [[technologie_information]] : 70
- [[frontieres_du_systeme]] : 85
- [[organisation_territoires]] : 60

### [[eco_communalism]]
- **level** : 50 | **volatility** : 30

L’expansion spatiale est principalement scientifique, coopérative et orientée vers la connaissance et la préservation du vivant, avec une faible logique d’exploitation économique.

**Dynamiques dominantes**
- exploration scientifique collaborative
- mutualisation des infrastructures spatiales
- faible militarisation de l’espace

**Rôle système**
- bien commun scientifique global
- extension non extractive du système humain

**Couplages**
- [[gouvernance_institutions]] : 80
- [[technologie_information]] : 75
- [[climat_environnement_global]] : 40
- [[systeme_economique_redistribution]] : 35

### [[policy_reform]]
- **level** : 45 | **volatility** : 35

Développement coordonné de l’économie spatiale sous gouvernance internationale, avec régulation des orbites, mutualisation des coûts et coopération scientifique renforcée.

**Dynamiques dominantes**
- coopération internationale spatiale
- industrialisation orbitale régulée
- gestion des débris et des orbites

**Rôle système**
- variable encadrée par gouvernance globale
- extension contrôlée du système humain

**Couplages**
- [[gouvernance_institutions]] : 85
- [[technologie_information]] : 80
- [[geopolitique_conflits]] : 50
- [[systeme_economique_redistribution]] : 55

### [[reference]]
- **level** : 25 | **volatility** : 40

Expansion spatiale limitée à l’orbite terrestre et aux missions robotiques exploratoires. Le système reste fondamentalement terrestre, avec une dépendance totale aux infrastructures et ressources de la Terre.

**Dynamiques dominantes**
- exploration spatiale scientifique limitée
- économie orbitale émergente mais marginale
- dépendance structurelle à la Terre

**Rôle système**
- variable périphérique d’expansion
- signal de potentiel futur plus que levier actif

**Couplages**
- [[technologie_information]] : 65
- [[energie_ressources_critiques]] : 40
- [[geopolitique_conflits]] : 45
- [[systeme_economique_redistribution]] : 35



## 9. Scénarios liés

**Dominants** : [[new_sustainability]]
**Renforcés** : [[reference]], [[policy_reform]]
**Contraints** : [[breakdown]], [[eco_communalism]]

## 10. Narratif systémique

**Résumé**
Variable de frontière du système humain vers l’espace extra-terrestre.

**Dynamiques**
La baisse des coûts d’accès à l’espace et la privatisation du secteur spatial accélèrent l’industrialisation orbitale et l’émergence d’une économie spatiale.

**Interprétation**
Dans la lecture Ourrassol, cette variable représente la limite externe du système : elle n’agit pas sur les équilibres actuels mais définit les capacités d’expansion future du système humain.

**Implications**
Elle conditionne la trajectoire longue du système global en ouvrant l’accès à de nouvelles ressources, de nouveaux espaces et de nouvelles formes d’organisation civilisationnelle.

## 11. Métadonnées de simulation
| Paramètre | Valeur |
|---|---|
| volatility | very_high |
| predictability | low |
| uncertainty_level | very_high |
| tipping_point_risk | very_high |
| systemic_criticality | 5 |
| resilience | 1 |
| adaptability | 2 |

## 12. Trajectoire des signaux 2025 → 2098

Évolution des signaux faibles selon le scénario — comment les précurseurs de 2025 sont devenus des réalités en 2098.

```yaml
signal_to_state:
  - signal: spatialisation_des_conflits
    scenarios:
      breakdown:
        evolution: militarisation chaotique de l'orbite basse et conflits spatiaux
        date_bascule: 2043-2063
        evenement_cle: premier conflit armé orbital 2055
      fortress_world:
        evolution: domination spatiale militarisée par les blocs rivaux
        date_bascule: 2038-2055
        evenement_cle: création des commandements spatiaux des blocs 2049
      new_sustainability:
        evolution: traités de paix spatiale et gouvernance internationale de l'orbite
        date_bascule: 2032-2048
        evenement_cle: Traité de l'Espace renouvelé et étendu 2040
      eco_communalism:
        evolution: désintérêt spatial et focalisation sur la régénération terrestre
        date_bascule: 2035-2055
        evenement_cle: abandon des programmes spatiaux nationaux non essentiels
      policy_reform:
        evolution: régulation internationale du trafic orbital et de la militarisation
        date_bascule: 2028-2044
        evenement_cle: Convention de l'Espace sur la limitation des armes orbitales 2036
      reference:
        evolution: course aux armements spatiaux non régulée
        date_bascule: 2025-2040
        evenement_cle: premier incident spatial militaire non mortel 2032

  - signal: saturation_orbitale
    scenarios:
      breakdown:
        evolution: syndrome de Kessler partiel et perte d'accès orbital
        date_bascule: 2045-2065
        evenement_cle: catastrophe orbitale de 2057 bloquant l'accès spatial
      fortress_world:
        evolution: nettoyage orbital réservé aux blocs dominants
        date_bascule: 2040-2058
        evenement_cle: programme de nettoyage orbital militarisé des blocs
      new_sustainability:
        evolution: programme mondial de dépollution orbitale et régulation du trafic
        date_bascule: 2033-2050
        evenement_cle: Agence Mondiale du Trafic Spatial 2041
      eco_communalism:
        evolution: abandon de l'expansion orbitale et focalisation scientifique
        date_bascule: 2035-2053
        evenement_cle: moratoire communautaire sur les lancements commerciaux
      policy_reform:
        evolution: standards internationaux de durabilité orbitale
        date_bascule: 2028-2043
        evenement_cle: directive internationale sur les débris orbitaux 2035
      reference:
        evolution: saturation croissante sans gouvernance efficace
        date_bascule: 2025-2040
        evenement_cle: premier incident critique lié aux débris orbitaux 2031

  - signal: industrialisation_orbitale_privee
    scenarios:
      breakdown:
        evolution: effondrement des consortiums industriels orbitaux privés sous les conflits
        date_bascule: 2042-2060
        evenement_cle: faillite en chaîne des stations industrielles orbitales privées 2052
      fortress_world:
        evolution: nationalisation des infrastructures industrielles orbitales privées par les blocs
        date_bascule: 2037-2054
        evenement_cle: saisie des stations industrielles privées par le Bloc Atlantique 2048
      new_sustainability:
        evolution: intégration des industries orbitales privées dans l'économie spatiale mondiale coordonnée
        date_bascule: 2031-2047
        evenement_cle: fusion des consortiums orbitaux dans le réseau économique mondial 2039
      eco_communalism:
        evolution: abandon des projets industriels orbitaux privés au profit du collectif scientifique
        date_bascule: 2036-2055
        evenement_cle: dissolution volontaire des consortiums orbitaux à but lucratif
      policy_reform:
        evolution: régulation internationale des activités industrielles orbitales privées
        date_bascule: 2027-2043
        evenement_cle: adoption du cadre international sur l'industrie orbitale privée 2034
      reference:
        evolution: émergence marginale de projets industriels orbitaux privés expérimentaux
        date_bascule: 2025-2042
        evenement_cle: premier contrat industriel privé en orbite basse 2031

  - signal: minage_asteroides
    scenarios:
      breakdown:
        evolution: abandon chaotique des projets de minage d'astéroïdes pour conflits orbitaux
        date_bascule: 2044-2063
        evenement_cle: attaque sur une plateforme de minage d'astéroïdes 2057
      fortress_world:
        evolution: course aux ressources astéroïdales entre blocs militarisés
        date_bascule: 2041-2058
        evenement_cle: lancement de la première mission minière militarisée d'astéroïde 2051
      new_sustainability:
        evolution: exploitation coordonnée des astéroïdes alimentant l'économie spatiale mondiale
        date_bascule: 2034-2051
        evenement_cle: lancement du programme international de minage d'astéroïdes 2043
      eco_communalism:
        evolution: rejet du minage extractif au profit d'échantillonnage scientifique limité
        date_bascule: 2038-2057
        evenement_cle: charte scientifique internationale contre le minage extractif d'astéroïdes
      policy_reform:
        evolution: encadrement international du minage d'astéroïdes selon un partage des bénéfices
        date_bascule: 2030-2046
        evenement_cle: adoption du traité de partage des ressources astéroïdales 2038
      reference:
        evolution: premières missions expérimentales de minage d'astéroïdes à impact limité
        date_bascule: 2027-2044
        evenement_cle: première mission expérimentale de minage d'astéroïde 2035

  - signal: nouvelles_communautes_orbitales
    scenarios:
      breakdown:
        evolution: isolement des communautés orbitales coupées de tout ravitaillement terrestre
        date_bascule: 2045-2064
        evenement_cle: rupture de communication avec une station orbitale habitée 2058
      fortress_world:
        evolution: intégration des communautés orbitales comme territoires officiels des blocs
        date_bascule: 2039-2057
        evenement_cle: reconnaissance des stations orbitales comme territoires officiels des blocs 2050
      new_sustainability:
        evolution: reconnaissance pleine des communautés orbitales dans la citoyenneté mondiale
        date_bascule: 2033-2049
        evenement_cle: adoption du statut de citoyenneté orbitale universelle 2042
      eco_communalism:
        evolution: organisation des communautés orbitales en habitats coopératifs scientifiques restreints
        date_bascule: 2037-2056
        evenement_cle: fondation de la première communauté orbitale coopérative scientifique
      policy_reform:
        evolution: développement encadré des communautés orbitales sous programmes internationaux
        date_bascule: 2029-2045
        evenement_cle: lancement du programme international d'habitats orbitaux partagés 2036
      reference:
        evolution: apparition de premières communautés orbitales permanentes expérimentales et fragiles
        date_bascule: 2026-2043
        evenement_cle: installation de la première communauté orbitale permanente 2033

  - signal: retour_recit_civilisationnel_spatial
    scenarios:
      breakdown:
        evolution: effacement du récit spatial réduit à un âge d'or perdu
        date_bascule: 2044-2062
        evenement_cle: dernière retransmission publique d'une mission spatiale civile 2056
      fortress_world:
        evolution: récupération du récit spatial comme destin manifeste des blocs
        date_bascule: 2038-2056
        evenement_cle: lancement de la doctrine du destin orbital par les blocs 2048
      new_sustainability:
        evolution: intégration du récit spatial au cœur de l'identité civilisationnelle collective
        date_bascule: 2032-2049
        evenement_cle: lancement du récit mondial de la civilisation multi-orbitale 2041
      eco_communalism:
        evolution: recadrage du récit spatial vers une posture de sobriété scientifique
        date_bascule: 2038-2056
        evenement_cle: manifeste pour une présence spatiale sobre et non conquérante
      policy_reform:
        evolution: réhabilitation progressive du récit spatial par la communication scientifique institutionnelle
        date_bascule: 2027-2044
        evenement_cle: lancement de la campagne institutionnelle pour la culture spatiale 2035
      reference:
        evolution: persistance marginale d'un récit spatial nostalgique et confiné
        date_bascule: 2025-2041
        evenement_cle: dernier lancement habité médiatisé à grande échelle 2032
```
