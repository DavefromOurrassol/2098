---
name: demographie_mobilite_humaine
type: systemic_variable
slug: demographie_mobilite_humaine
variable_type: relais
global_influence_level: 4
domain:
    - social
    - economic
    - geopolitical
influences:
    - [[systeme_economique_redistribution]]
    - [[gouvernance_institutions]]
    - [[geopolitique_conflits]]
    - [[valeurs_culture_tempo_sociale]]
    - [[organisation_territoires]]
    - [[sante_biotechnologies]]
influenced_by:
    - [[climat_environnement_global]]
    - [[systemes_productifs_travail]]
    - [[energie_ressources_critiques]]
    - [[geopolitique_conflits]]
    - [[organisation_territoires]]
    - [[systeme_economique_redistribution]]
bidirectional_links:
    - [[organisation_territoires]]
    - [[geopolitique_conflits]]
    - [[systeme_economique_redistribution]]
sub_variables:
  - name: population_globale
    role: masse démographique mondiale
    trend: stable
    links:
      - [[energie_ressources_critiques]]
      - [[systeme_economique_redistribution]]
      - [[climat_environnement_global]]
  - name: migrations_internationales
    role: redistribution des populations
    trend: up
    links:
      - [[geopolitique_conflits]]
      - [[climat_environnement_global]]
      - [[systemes_productifs_travail]]
  - name: urbanisation
    role: concentration spatiale humaine
    trend: unstable
    links:
      - [[organisation_territoires]]
      - [[systeme_economique_redistribution]]
      - [[climat_environnement_global]]
  - name: structure_familiale
    role: organisation sociale de base
    trend: unstable
    links:
      - [[valeurs_culture_tempo_sociale]]
      - [[systeme_economique_redistribution]]
  - name: mobilite_humaine_globale
    role: circulation des individus
    trend: up
    links:
      - [[technologie_information]]
      - [[geopolitique_conflits]]
      - [[systemes_productifs_travail]]

scenario_mapping:
  dominant_scenarios:
    - breakdown
    - fortress_world
    - new_sustainability
  reinforcing_scenarios:
    - policy_reform
    - eco_communalism
  constrained_scenarios:
    - reference
simulation:
  volatility: medium
  predictability: medium
  uncertainty_level: medium
  tipping_point_risk: medium
  systemic_criticality: 4
  resilience: 2
  adaptability: 3
states:

  fortress_world:
    level: 75
    volatility: 80
    state_logic: >
      Contrôle strict des mobilités humaines avec fermeture des frontières, sélection des flux migratoires et segmentation forte des populations entre blocs territoriaux.
    dominant_dynamics:
      - immobilisation forcée de populations
      - migrations hautement contrôlées
      - segmentation des espaces humains
    system_role_shift:
      - variable militarisée et contrôlée
      - outil de sécurité territoriale
    coupling_intensity:
      [[geopolitique_conflits]]: 90
      [[frontieres_du_systeme]]: 85
      [[organisation_territoires]]: 85

  new_sustainability:
    level: 45
    volatility: 30
    state_logic: >
      Optimisation globale des flux migratoires via IA et gouvernance internationale, permettant une répartition plus équilibrée des populations sous contraintes climatiques et économiques.
    dominant_dynamics:
      - migration régulée et anticipée
      - optimisation des flux de population
      - réduction des crises migratoires
    system_role_shift:
      - variable optimisée par systèmes cognitifs
      - instrument d’équilibre systémique global
    coupling_intensity:
      [[gouvernance_institutions]]: 90
      [[technologie_information]]: 85
      [[climat_environnement_global]]: 60
      [[organisation_territoires]]: 65

  breakdown:
    level: 90
    volatility: 95
    state_logic: >
      Crises migratoires massives, déplacements forcés et instabilité sociale généralisée provoquée par effondrements économiques, climatiques et géopolitiques simultanés.
    dominant_dynamics:
      - exodes climatiques massifs
      - migrations forcées et non coordonnées
      - saturation des zones d’accueil
    system_role_shift:
      - variable de rupture systémique
      - amplificateur de conflits multi-niveaux
    coupling_intensity:
      [[geopolitique_conflits]]: 95
      [[organisation_territoires]]: 90
      [[climat_environnement_global]]: 85
      [[systeme_economique_redistribution]]: 80

  eco_communalism:
    level: 40
    volatility: 35
    state_logic: >
      Réduction globale de la mobilité internationale au profit de la relocalisation des populations et stabilisation territoriale par proximité et autonomie locale.
    dominant_dynamics:
      - relocalisation des populations
      - baisse des migrations internationales
      - stabilisation communautaire locale
    system_role_shift:
      - variable stabilisée localement
      - facteur de résilience territoriale
    coupling_intensity:
      [[organisation_territoires]]: 85
      [[systemes_productifs_travail]]: 70
      [[climat_environnement_global]]: 55

  policy_reform:
    level: 50
    volatility: 40
    state_logic: >
      Gestion coordonnée des flux migratoires via gouvernance internationale, réduction des chocs migratoires majeurs et optimisation partielle des mobilités humaines.
    dominant_dynamics:
      - régulation des migrations internationales
      - rééquilibrage progressif des populations
      - stabilisation relative des flux urbains
    system_role_shift:
      - variable pilotée institutionnellement
      - instrument de stabilisation globale
    coupling_intensity:
      [[gouvernance_institutions]]: 85
      [[technologie_information]]: 75
      [[organisation_territoires]]: 65
      [[geopolitique_conflits]]: 45

  reference:
    level: 55
    volatility: 50
    state_logic: >
      Stabilisation démographique globale avec ralentissement de la croissance, mais augmentation des mobilités contraintes liées aux déséquilibres économiques, climatiques et géopolitiques.
    dominant_dynamics:
      - vieillissement structurel global
      - migrations économiques et climatiques modérées
      - polarisation des zones attractives et répulsives
    system_role_shift:
      - variable de redistribution lente mais structurante
      - amplificateur des déséquilibres territoriaux
    coupling_intensity:
      [[climat_environnement_global]]: 65
      [[organisation_territoires]]: 70
      [[geopolitique_conflits]]: 60
      [[systeme_economique_redistribution]]: 60

---

# demographie_mobilite_humaine

## 1. Identité systémique

**Description**
Structure dynamique des populations humaines et de leurs déplacements. Elle conditionne la pression sur les ressources, l’organisation des territoires, la stabilité sociale et les équilibres économiques et politiques globaux.

**Rôle**
Variable relais structurant la répartition spatiale des populations, les flux migratoires, l’urbanisation et les dynamiques démographiques qui relient environnement, économie, territoires et gouvernance.

## 2. Position dans le système

**Influence**
- [[systeme_economique_redistribution]]
- [[gouvernance_institutions]]
- [[geopolitique_conflits]]
- [[valeurs_culture_tempo_sociale]]
- [[organisation_territoires]]
- [[sante_biotechnologies]]

**Influencé par**
- [[climat_environnement_global]]
- [[systemes_productifs_travail]]
- [[energie_ressources_critiques]]
- [[geopolitique_conflits]]
- [[organisation_territoires]]
- [[systeme_economique_redistribution]]

**Liens bidirectionnels**
- [[organisation_territoires]]
- [[geopolitique_conflits]]
- [[systeme_economique_redistribution]]

## 3. Dynamique interne
- Direction : **up** | Intensité : **high** | Inertie : **high** | Vitesse : **linear**

**Tendances**
- ralentissement global de la croissance démographique
- vieillissement structurel dans de nombreuses régions
- augmentation des migrations climatiques et économiques
- pression croissante sur les zones urbaines
- recomposition des structures familiales
- mobilité humaine plus contrainte et plus stratégique
- polarisation démographique entre zones attractives et zones de déclin

**Dynamiques passées**
- transition démographique mondiale
- forte croissance démographique au XXe siècle
- urbanisation massive et rapide
- migrations coloniales puis post-coloniales
- mondialisation des flux humains
- accélération des mobilités internationales
- inégalités démographiques Nord-Sud
- émergence des mégapoles globales
- structuration des politiques migratoires modernes

**Snapshot**
> Recomposition globale des populations humaines caractérisée par une stabilisation ou fragmentation démographique, une intensification des mobilités contraintes et une polarisation croissante entre zones attractives et zones de déclin sous l’effet combiné du climat, de l’économie et des tensions géopolitiques.

**tensions**
- mobilité vs immobilité
- zones attractives vs zones désertées
- croissance démographique vs vieillissement
- intégration vs fragmentation sociale
- migration libre vs migration contrainte

**constraints**
- limites de capacité des infrastructures urbaines
- pressions climatiques sur l’habitabilité
- contraintes politiques et frontières nationales
- déséquilibres économiques régionaux
- effets inertiels des structures démographiques

**forces_attractives**
- mobilité économique et sociale
- rééquilibrage des populations mondiales
- adaptation aux contraintes climatiques
- innovation culturelle par mélange des populations
- optimisation de la répartition du travail global
- mobilité économique globale
- innovation sociale par mixité
- optimisation territoriale

**forces_repulsives**
- pression sur les infrastructures urbaines
- tensions sociales et identitaires
- déséquilibres territoriaux
- vieillissement et déclin démographique localisé
- crises migratoires non contrôlées
- saturation urbaine
- tensions politiques liées aux migrations


## 4. Structure causale

**Forces attractives**
- rééquilibrage des populations
- adaptation climatique humaine
- mobilité économique globale
- innovation sociale par mixité
- optimisation territoriale

**Forces répulsives**
- crises migratoires
- tensions sociales et politiques
- saturation urbaine
- déclin démographique localisé
- déséquilibres territoriaux

**Contraintes**
- capacités limitées des infrastructures
- contraintes climatiques sur l’habitabilité
- frontières nationales
- inertie démographique
- déséquilibres économiques régionaux

**Tensions**
- mobilité vs immobilité
- attractivité vs déclin territorial
- vieillissement vs renouvellement démographique
- intégration vs fragmentation sociale
- ouverture vs fermeture migratoire

## 5. Ruptures

**technological**
_core_
- biotechnologies influençant la natalité
- biotechnologies influençant la longévité
- IA de gestion des flux migratoires
- systèmes prédictifs de mobilité humaine globale
_extended_
- gouvernance algorithmique des migrations
- optimisation automatisée des flux humains

**systemic**
_core_
- exodes climatiques massifs
- effondrement démographique régional
- rééquilibrage brutal des populations globales
- désurbanisation forcée
- concentration extrême des populations
_extended_
- polarisation démographique mondiale
- recomposition accélérée des espaces habitables

**political_social**
_core_
- politiques migratoires ultra-restrictives
- politiques migratoires ouvertes
- redécoupage des frontières démographiques
- citoyenneté conditionnelle ou mobile
- conflits liés à la pression migratoire
_extended_
- fragmentation des espaces humains
- régionalisation des politiques migratoires


## 6. Indicateurs
**primary**
- flux migratoires internationaux
- taux d’urbanisation
- vieillissement démographique
- croissance démographique régionale

**secondary**
- saturation des infrastructures urbaines
- déséquilibres territoriaux
- pression migratoire aux frontières

**systemic**
- polarisation démographique mondiale
- répartition spatiale des populations
- attractivité différentielle des territoires



## 7. Signaux faibles
**technological**
- essor des systèmes de gestion algorithmique des flux humains (→ gestion_algorithmique_flux_humains)
- développement d’outils prédictifs migratoires (→ outils_predictifs_migratoires)

**geopolitical**
- augmentation des politiques migratoires restrictives (→ politiques_migratoires_restrictives)
- multiplication des tensions liées aux migrations

**social**
- saturation des grandes métropoles
- recomposition des structures familiales
- relocalisation progressive de populations côtières et rurales

**environmental**
- accélération des migrations climatiques
- pression croissante sur les territoires habitables

**cognitive_cultural**
- évolution des représentations de la mobilité
- montée des débats identitaires liés aux migrations (→ debats_identitaires_migrations)



## 8. États par scénario
### [[fortress_world]]
- **level** : 75 | **volatility** : 80

Contrôle strict des mobilités humaines avec fermeture des frontières, sélection des flux migratoires et segmentation forte des populations entre blocs territoriaux. dominant_dynamics: - immobilisation forcée de populations - migrations hautement contrôlées - segmentation des espaces humains system_role_shift: - variable militarisée et contrôlée - outil de sécurité territoriale coupling_intensity: geopolitique_conflits: 90 frontieres_du_systeme: 85 organisation_territoires: 85

**Dynamiques dominantes**
- immobilisation forcée de populations
- migrations hautement contrôlées
- segmentation des espaces humains

**Rôle système**
- variable militarisée et contrôlée
- outil de sécurité territoriale

**Couplages**
- [[geopolitique_conflits]] : 90
- [[frontieres_du_systeme]] : 85
- [[organisation_territoires]] : 85

### [[new_sustainability]]
- **level** : 45 | **volatility** : 30

Optimisation globale des flux migratoires via IA et gouvernance internationale, permettant une répartition plus équilibrée des populations sous contraintes climatiques et économiques. dominant_dynamics: - migration régulée et anticipée - optimisation des flux de population - réduction des crises migratoires system_role_shift: - variable optimisée par systèmes cognitifs - instrument d’équilibre systémique global coupling_intensity: gouvernance_institutions: 90 technologie_information: 85 climat_environment_global: 60 organisation_territoires: 65

**Dynamiques dominantes**
- migration régulée et anticipée
- optimisation des flux de population
- réduction des crises migratoires

**Rôle système**
- variable optimisée par systèmes cognitifs
- instrument d’équilibre systémique global

**Couplages**
- [[gouvernance_institutions]] : 90
- [[technologie_information]] : 85
- [[climat_environnement_global]] : 60
- [[organisation_territoires]] : 65

### [[breakdown]]
- **level** : 90 | **volatility** : 95

Crises migratoires massives, déplacements forcés et instabilité sociale généralisée provoquée par effondrements économiques, climatiques et géopolitiques simultanés. dominant_dynamics: - exodes climatiques massifs - migrations forcées et non coordonnées - saturation des zones d’accueil system_role_shift: - variable de rupture systémique - amplificateur de conflits multi-niveaux coupling_intensity: geopolitique_conflits: 95 organisation_territoires: 90 climat_environment_global: 85 systeme_economique_redistribution: 80

**Dynamiques dominantes**
- exodes climatiques massifs
- migrations forcées et non coordonnées
- saturation des zones d’accueil

**Rôle système**
- variable de rupture systémique
- amplificateur de conflits multi-niveaux

**Couplages**
- [[geopolitique_conflits]] : 95
- [[organisation_territoires]] : 90
- [[climat_environnement_global]] : 85
- [[systeme_economique_redistribution]] : 80

### [[eco_communalism]]
- **level** : 40 | **volatility** : 35

Réduction globale de la mobilité internationale au profit de la relocalisation des populations et stabilisation territoriale par proximité et autonomie locale. dominant_dynamics: - relocalisation des populations - baisse des migrations internationales - stabilisation communautaire locale system_role_shift: - variable stabilisée localement - facteur de résilience territoriale coupling_intensity: organisation_territoires: 85 systemes_productifs_travail: 70 climat_environment_global: 55

**Dynamiques dominantes**
- relocalisation des populations
- baisse des migrations internationales
- stabilisation communautaire locale

**Rôle système**
- variable stabilisée localement
- facteur de résilience territoriale

**Couplages**
- [[organisation_territoires]] : 85
- [[systemes_productifs_travail]] : 70
- [[climat_environnement_global]] : 55

### [[policy_reform]]
- **level** : 50 | **volatility** : 40

Gestion coordonnée des flux migratoires via gouvernance internationale, réduction des chocs migratoires majeurs et optimisation partielle des mobilités humaines. dominant_dynamics: - régulation des migrations internationales - rééquilibrage progressif des populations - stabilisation relative des flux urbains system_role_shift: - variable pilotée institutionnellement - instrument de stabilisation globale coupling_intensity: gouvernance_institutions: 85 technologie_information: 75 organisation_territoires: 65 geopolitique_conflits: 45

**Dynamiques dominantes**
- régulation des migrations internationales
- rééquilibrage progressif des populations
- stabilisation relative des flux urbains

**Rôle système**
- variable pilotée institutionnellement
- instrument de stabilisation globale

**Couplages**
- [[gouvernance_institutions]] : 85
- [[technologie_information]] : 75
- [[organisation_territoires]] : 65
- [[geopolitique_conflits]] : 45

### [[reference]]
- **level** : 55 | **volatility** : 50

Stabilisation démographique globale avec ralentissement de la croissance, mais augmentation des mobilités contraintes liées aux déséquilibres économiques, climatiques et géopolitiques. dominant_dynamics: - vieillissement structurel global - migrations économiques et climatiques modérées - polarisation des zones attractives et répulsives system_role_shift: - variable de redistribution lente mais structurante - amplificateur des déséquilibres territoriaux coupling_intensity: climat_environment_global: 65 organisation_territoires: 70 geopolitique_conflits: 60 systeme_economique_redistribution: 60

**Dynamiques dominantes**
- vieillissement structurel global
- migrations économiques et climatiques modérées
- polarisation des zones attractives et répulsives

**Rôle système**
- variable de redistribution lente mais structurante
- amplificateur des déséquilibres territoriaux

**Couplages**
- [[climat_environnement_global]] : 65
- [[organisation_territoires]] : 70
- [[geopolitique_conflits]] : 60
- [[systeme_economique_redistribution]] : 60



## 9. Scénarios liés

**Dominants** : [[breakdown]], [[fortress_world]], [[new_sustainability]]
**Renforcés** : [[policy_reform]], [[eco_communalism]]
**Contraints** : [[reference]]

## 10. Narratif systémique

**Résumé**
Variable centrale de répartition et de mobilité des populations, fortement influencée par les contraintes climatiques, économiques et géopolitiques.

**Dynamiques**
La croissance démographique ralentit mais les mobilités humaines augmentent sous l’effet des écarts de développement, du vieillissement, des crises environnementales et des transformations économiques.

**Interprétation**
Dans Ourrassol, cette variable constitue l’interface entre les contraintes biophysiques, les dynamiques territoriales et les systèmes socio-économiques. Elle matérialise les réallocations humaines provoquées par les transformations du système mondial.

**Implications**
Influence directement les territoires, le travail, la santé, la gouvernance, les équilibres géopolitiques et les systèmes culturels en redéfinissant la distribution spatiale des populations.

## 11. Métadonnées de simulation
| Paramètre | Valeur |
|---|---|
| volatility | medium |
| predictability | medium |
| uncertainty_level | medium |
| tipping_point_risk | medium |
| systemic_criticality | 4 |
| resilience | 2 |
| adaptability | 3 |

## 12. Trajectoire des signaux 2025 → 2098

Évolution des signaux faibles selon le scénario — comment les précurseurs de 2025 sont devenus des réalités en 2098.

```yaml
signal_to_state:
  - signal: migrations_climatiques
    scenarios:
      breakdown:
        evolution: vagues migratoires massives non gérées et conflits aux frontières
        date_bascule: 2042-2062
        evenement_cle: exode climatique de 400 millions de personnes 2055
      fortress_world:
        evolution: fermeture hermétique des frontières et refoulement systématique
        date_bascule: 2037-2053
        evenement_cle: construction du système de barrières des blocs 2048
      new_sustainability:
        evolution: gestion planifiée et intégrée des migrations climatiques
        date_bascule: 2032-2048
        evenement_cle: Pacte mondial de gestion des migrations climatiques 2040
      eco_communalism:
        evolution: accueil communautaire et relocalisation dans les bioterritoires
        date_bascule: 2039-2058
        evenement_cle: programme d'accueil des réfugiés climatiques bioterritoriaux
      policy_reform:
        evolution: cadre juridique international pour les réfugiés climatiques
        date_bascule: 2028-2044
        evenement_cle: Convention de Genève sur les réfugiés climatiques 2035
      reference:
        evolution: pression croissante sans gouvernance cohérente
        date_bascule: 2024-2040
        evenement_cle: premier million de réfugiés climatiques officiellement reconnus 2030

  - signal: vieillissement_demographique
    scenarios:
      breakdown:
        evolution: effondrement des systèmes de retraite et crise des soins aux ainés
        date_bascule: 2040-2058
        evenement_cle: faillite des systèmes de retraite des pays développés 2050
      fortress_world:
        evolution: sélection démographique et eugénisme de fait dans les blocs
        date_bascule: 2035-2052
        evenement_cle: politiques de natalité forcée et sélection migratoire des blocs
      new_sustainability:
        evolution: société longéviste équilibrée avec biotechnologies anti-âge
        date_bascule: 2040-2060
        evenement_cle: allongement de l'espérance de vie active à 90 ans
      eco_communalism:
        evolution: valorisation des anciens et intergénérationnel communautaire
        date_bascule: 2035-2055
        evenement_cle: renaissance des modèles familiaux élargis et communautaires
      policy_reform:
        evolution: réformes des systèmes de protection sociale pour la longévité
        date_bascule: 2028-2044
        evenement_cle: grand plan de réforme des retraites de 2035
      reference:
        evolution: pression croissante sur les systèmes sociaux sans réforme cohérente
        date_bascule: 2024-2038
        evenement_cle: première grande crise de financement des retraites 2031

  - signal: outils_predictifs_migratoires
    scenarios:
      breakdown:
        evolution: systèmes prédictifs détournés pour trier les populations déplacées
        date_bascule: 2041-2060
        evenement_cle: piratage des bases prédictives migratoires de l'Alliance Pacifique 2054
      fortress_world:
        evolution: ciblage prédictif des flux migratoires par les blocs fermés
        date_bascule: 2036-2053
        evenement_cle: déploiement du système de tri prédictif frontalier du Bloc Atlantique 2049
      new_sustainability:
        evolution: anticipation mondiale des flux migratoires pour une répartition équilibrée
        date_bascule: 2031-2047
        evenement_cle: déploiement de la plateforme mondiale d'anticipation migratoire 2039
      eco_communalism:
        evolution: outils prédictifs communautaires pour anticiper les arrivées locales
        date_bascule: 2038-2057
        evenement_cle: réseau bioterritorial d'anticipation des mobilités locales
      policy_reform:
        evolution: encadrement international des outils prédictifs migratoires par traité
        date_bascule: 2029-2045
        evenement_cle: charte internationale sur l'usage éthique des prédictions migratoires 2036
      reference:
        evolution: adoption inégale des outils prédictifs par les États riches
        date_bascule: 2025-2041
        evenement_cle: premiers systèmes prédictifs migratoires commercialisés aux frontières 2032

  - signal: politiques_migratoires_restrictives
    scenarios:
      breakdown:
        evolution: fermetures unilatérales des frontières et conflits aux points de passage
        date_bascule: 2040-2059
        evenement_cle: fermeture simultanée de douze frontières majeures 2052
      fortress_world:
        evolution: doctrine commune de fermeture migratoire adoptée par les blocs
        date_bascule: 2035-2051
        evenement_cle: charte commune de fermeture migratoire des blocs 2045
      new_sustainability:
        evolution: dissolution progressive des politiques restrictives au profit de quotas négociés
        date_bascule: 2030-2046
        evenement_cle: accord mondial de mobilité régulée remplaçant les quotas unilatéraux 2038
      eco_communalism:
        evolution: obsolescence des politiques nationales restrictives face à la relocalisation
        date_bascule: 2041-2059
        evenement_cle: dissolution de fait des contrôles migratoires nationaux dans les bioterritoires
      policy_reform:
        evolution: assouplissement négocié des politiques migratoires sous supervision internationale
        date_bascule: 2027-2043
        evenement_cle: accord-cadre international sur les quotas migratoires négociés 2034
      reference:
        evolution: durcissement progressif et inégal des politiques migratoires nationales
        date_bascule: 2025-2042
        evenement_cle: vague de fermetures frontalières en réponse aux crises migratoires 2031

  - signal: debats_identitaires_migrations
    scenarios:
      breakdown:
        evolution: violences identitaires généralisées contre les populations déplacées
        date_bascule: 2043-2062
        evenement_cle: vague de pogroms anti-migrants dans les enclaves urbaines 2056
      fortress_world:
        evolution: identité de bloc instrumentalisée pour justifier la fermeture migratoire
        date_bascule: 2037-2054
        evenement_cle: doctrine identitaire officielle du Bloc Sibérien sur la mobilité 2050
      new_sustainability:
        evolution: émergence de récits identitaires post-nationaux apaisant les tensions migratoires
        date_bascule: 2033-2049
        evenement_cle: lancement du forum mondial des identités mobiles 2039
      eco_communalism:
        evolution: réancrage des identités dans l'appartenance bioterritoriale plutôt que nationale
        date_bascule: 2040-2058
        evenement_cle: charte des identités bioterritoriales et de l'accueil
      policy_reform:
        evolution: débats publics encadrés et politiques d'intégration réduisant les tensions
        date_bascule: 2026-2043
        evenement_cle: programme international de dialogue interculturel sur les migrations 2034
      reference:
        evolution: intensification des débats identitaires et montée de mouvements nativistes
        date_bascule: 2026-2042
        evenement_cle: percée électorale de mouvements anti-migration dans plusieurs pays 2032

  - signal: gestion_algorithmique_flux_humains
    scenarios:
      breakdown:
        evolution: systèmes algorithmiques de tri des populations détournés par les milices
        date_bascule: 2042-2061
        evenement_cle: panne généralisée des systèmes de tri migratoire automatisés 2052
      fortress_world:
        evolution: déploiement de systèmes algorithmiques unifiés de tri migratoire par les blocs
        date_bascule: 2038-2055
        evenement_cle: mise en service du classement migratoire automatisé du Bloc Eurasiatique 2050
      new_sustainability:
        evolution: coordination algorithmique mondiale optimisant les mobilités pour l'équilibre collectif
        date_bascule: 2033-2049
        evenement_cle: déploiement de la plateforme mondiale de gestion des mobilités 2040
      eco_communalism:
        evolution: abandon des systèmes algorithmiques centralisés au profit de la coordination locale
        date_bascule: 2040-2059
        evenement_cle: mouvement de débranchement des systèmes de gestion migratoire centralisés
      policy_reform:
        evolution: standardisation internationale des systèmes algorithmiques de gestion migratoire
        date_bascule: 2030-2047
        evenement_cle: norme internationale sur les systèmes algorithmiques migratoires 2035
      reference:
        evolution: déploiement inégal des systèmes algorithmiques migratoires selon les pays
        date_bascule: 2027-2044
        evenement_cle: premier scandale de discrimination algorithmique aux frontières 2032
```
