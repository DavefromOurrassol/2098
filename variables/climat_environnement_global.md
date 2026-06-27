---
name: climat_environnement_global
type: systemic_variable
slug: climat_environnement_global
variable_type: moteur
global_influence_level: 5
domain:
    - ecological
    - economic
    - geopolitical
    - social
    - technological
influences:
    - [[energie_ressources_critiques]]
    - [[demographie_mobilite_humaine]]
    - [[geopolitique_conflits]]
    - [[organisation_territoires]]
    - [[sante_biotechnologies]]
influenced_by:
    - [[energie_ressources_critiques]]
    - [[systeme_economique_redistribution]]
    - [[technologie_information]]
bidirectional_links:
    - [[organisation_territoires]]
sub_variables:
  - name: rechauffement_climatique_global
    role: régulation thermique du système Terre
    trend: up
    links:
      - [[energie_ressources_critiques]]
      - [[geopolitique_conflits]]
  - name: evenements_extremes
    role: perturbations climatiques systémiques
    trend: up
    links:
      - [[organisation_territoires]]
      - [[systemes_productifs_travail]]
  - name: biodiversite_effondrement
    role: stabilité fonctionnelle du vivant
    trend: down
    links:
      - [[sante_biotechnologies]]
      - [[systeme_economique_redistribution]]
  - name: cycles_de_l_eau
    role: régulation hydrologique globale
    trend: unstable
    links:
      - [[energie_ressources_critiques]]
      - [[organisation_territoires]]
  - name: pollution_globale
    role: charge toxique systémique
    trend: up
    links:
      - [[sante_biotechnologies]]
      - [[systeme_economique_redistribution]]

scenario_mapping:
  dominant_scenarios:
    - breakdown
    - policy_reform
  reinforcing_scenarios:
    - fortress_world
    - eco_communalism
  constrained_scenarios:
    - new_sustainability
simulation:
  volatility: high
  predictability: low
  uncertainty_level: high
  tipping_point_risk: high
  systemic_criticality: 5
  resilience: 1
  adaptability: 2
states:

  fortress_world:
    level: 75
    volatility: 80
    state_logic: >
      Climat fortement dégradé mais partiellement stabilisé par zonage territorial et sécurisation des zones habitables.
    coupling_intensity:
      [[frontieres_du_systeme]]: 90
      [[organisation_territoires]]: 90
      [[geopolitique_conflits]]: 80

  new_sustainability:
    level: 35
    volatility: 25
    state_logic: >
      Stabilisation climatique globale relative via coordination mondiale, IA et régénération écologique assistée.
    coupling_intensity:
      [[gouvernance_institutions]]: 90
      [[technologie_information]]: 90
      [[energie_ressources_critiques]]: 60
      [[systeme_economique_redistribution]]: 50

  breakdown:
    level: 95
    volatility: 95
    state_logic: >
      Effondrements écologiques régionaux et basculements irréversibles avec emballement climatique global.
    coupling_intensity:
      [[organisation_territoires]]: 90
      [[geopolitique_conflits]]: 95
      [[systemes_productifs_travail]]: 85
      [[energie_ressources_critiques]]: 95

  eco_communalism:
    level: 55
    volatility: 45
    state_logic: >
      Amélioration écologique locale avec stabilisation partielle par relocalisation et baisse des pressions globales.
    coupling_intensity:
      [[organisation_territoires]]: 85
      [[systemes_productifs_travail]]: 70
      [[systeme_economique_redistribution]]: 55

  policy_reform:
    level: 45
    volatility: 35
    state_logic: >
      Stabilisation partielle grâce à gouvernance globale et technologies d’atténuation, sans inversion du dérèglement.
    coupling_intensity:
      [[gouvernance_institutions]]: 85
      [[technologie_information]]: 80
      [[energie_ressources_critiques]]: 60
      [[systeme_economique_redistribution]]: 50

  reference:
    level: 65
    volatility: 55
    state_logic: >
      Dérèglement climatique structurel continu avec intensification progressive, partiellement amorti par adaptation humaine.
    coupling_intensity:
      [[systeme_economique_redistribution]]: 60
      [[energie_ressources_critiques]]: 70
      [[organisation_territoires]]: 75
      [[geopolitique_conflits]]: 65

---

# climat_environnement_global

## 1. Identité systémique

**Description**
Base biophysique du système Terre conditionnant la stabilité des écosystèmes, des ressources et des sociétés humaines.

**Rôle**
Contrainte structurelle fondamentale et moteur de déséquilibres systémiques globaux.

## 2. Position dans le système

**Influence**
- [[energie_ressources_critiques]]
- [[demographie_mobilite_humaine]]
- [[geopolitique_conflits]]
- [[organisation_territoires]]
- [[sante_biotechnologies]]

**Influencé par**
- [[energie_ressources_critiques]]
- [[systeme_economique_redistribution]]
- [[technologie_information]]

**Liens bidirectionnels**
- [[organisation_territoires]]

## 3. Dynamique interne
- Direction : **up** | Intensité : **very_high** | Inertie : **extremely_high** | Vitesse : **accelerating**

**Tendances**
- augmentation température globale
- multiplication événements extrêmes
- déséquilibre cycles naturels

**Dynamiques passées**
- industrialisation fossile
- urbanisation mondiale
- déforestation massive
- accumulation des pollutions

**Snapshot**
> Dérèglement climatique systémique global avec accélération des événements extrêmes et dégradation continue des écosystèmes.

**tensions**
- stabilité climatique vs instabilité systémique
- adaptation humaine vs dépassement des seuils naturels
- régulation globale vs fragmentation des réponses

**constraints**
- inertie thermique des océans et de l’atmosphère
- effets cumulés irréversibles des émissions passées
- seuils de basculement écologique
- interdépendance des écosystèmes globaux

**forces_attractives**
- régénération écologique
- stabilisation climatique globale
- augmentation résilience territoriale

**forces_repulsives**
- effets cumulatifs irréversibles
- érosion biodiversité
- événements climatiques extrêmes


## 4. Structure causale

**Forces attractives**
- régénération écologique

**Forces répulsives**
- inertie climatique
- surexploitation ressources

**Contraintes**
- inertie thermique
- seuils de basculement

**Tensions**
- adaptation vs dépassement des limites
- naturel vs artificialisation (géo-ingénierie)

## 5. Ruptures

**technological**
_core_
- captation massive CO2 atmosphérique
- geoengineering climatique global
- restauration écologique assistée IA
_extended_
- monitoring climatique global en temps réel
- modification contrôlée cycles hydrologiques

**systemic**
_core_
- basculement climatique non linéaire
- effondrement biomes critiques (forêts, récifs)
_extended_
- désynchronisation cycles naturels
- migrations écologiques massives
- cascades écosystémiques

**political_social**
_core_
- traités climatiques contraignants globaux
- conflits liés à l’habitabilité
_extended_
- zones d’exclusion climatique
- reconfiguration forcée des territoires
- régulation stricte des émissions


## 6. Indicateurs
**primary**
- température moyenne globale ↑
- fréquence événements extrêmes ↑
- perte biodiversité ↑

**secondary**
- fonte des glaces ↑
- stress hydrique ↑
- dégradation sols ↑

**systemic**
- instabilité écosystèmes globaux
- migration climatique



## 7. Signaux faibles
**technological**
- investissements géo-ingénierie
- captation carbone industrielle

**geopolitical**
- tensions sur eau et territoires habitables
- migration climatique transfrontalière

**social**
- relocalisation côtière
- stress urbain climatique

**environmental**
- zones mortes océaniques
- mégafeux saisonniers

**cognitive_cultural**
- montée discours effondrement climatique (→ discours_effondrement_climatique)
- adaptation culturelle à l’instabilité



## 8. États par scénario
### [[fortress_world]]
- **level** : 75 | **volatility** : 80

Climat fortement dégradé mais partiellement stabilisé par zonage territorial et sécurisation des zones habitables. coupling_intensity: frontieres_du_systeme: 90 organisation_territoires: 90 geopolitique_conflits: 80

**Couplages**
- [[frontieres_du_systeme]] : 90
- [[organisation_territoires]] : 90
- [[geopolitique_conflits]] : 80

### [[new_sustainability]]
- **level** : 35 | **volatility** : 25

Stabilisation climatique globale relative via coordination mondiale, IA et régénération écologique assistée. coupling_intensity: gouvernance_institutions: 90 technologie_information: 90 energie_ressources_critiques: 60 systeme_economique_redistribution: 50

**Couplages**
- [[gouvernance_institutions]] : 90
- [[technologie_information]] : 90
- [[energie_ressources_critiques]] : 60
- [[systeme_economique_redistribution]] : 50

### [[breakdown]]
- **level** : 95 | **volatility** : 95

Effondrements écologiques régionaux et basculements irréversibles avec emballement climatique global. coupling_intensity: organisation_territoires: 90 geopolitique_conflits: 95 systemes_productifs_travail: 85 energie_ressources_critiques: 95

**Couplages**
- [[organisation_territoires]] : 90
- [[geopolitique_conflits]] : 95
- [[systemes_productifs_travail]] : 85
- [[energie_ressources_critiques]] : 95

### [[eco_communalism]]
- **level** : 55 | **volatility** : 45

Amélioration écologique locale avec stabilisation partielle par relocalisation et baisse des pressions globales. coupling_intensity: organisation_territoires: 85 systemes_productifs_travail: 70 systeme_economique_redistribution: 55

**Couplages**
- [[organisation_territoires]] : 85
- [[systemes_productifs_travail]] : 70
- [[systeme_economique_redistribution]] : 55

### [[policy_reform]]
- **level** : 45 | **volatility** : 35

Stabilisation partielle grâce à gouvernance globale et technologies d’atténuation, sans inversion du dérèglement. coupling_intensity: gouvernance_institutions: 85 technologie_information: 80 energie_ressources_critiques: 60 systeme_economique_redistribution: 50

**Couplages**
- [[gouvernance_institutions]] : 85
- [[technologie_information]] : 80
- [[energie_ressources_critiques]] : 60
- [[systeme_economique_redistribution]] : 50

### [[reference]]
- **level** : 65 | **volatility** : 55

Dérèglement climatique structurel continu avec intensification progressive, partiellement amorti par adaptation humaine. coupling_intensity: systeme_economique_redistribution: 60 energie_ressources_critiques: 70 organisation_territoires: 75 geopolitique_conflits: 65

**Couplages**
- [[systeme_economique_redistribution]] : 60
- [[energie_ressources_critiques]] : 70
- [[organisation_territoires]] : 75
- [[geopolitique_conflits]] : 65



## 9. Scénarios liés

**Dominants** : [[breakdown]], [[policy_reform]]
**Renforcés** : [[fortress_world]], [[eco_communalism]]
**Contraints** : [[new_sustainability]]

## 10. Narratif systémique

**Résumé**
Variable structurante du système Terre conditionnant toutes les autres dynamiques.

**Dynamiques**
Accélération non linéaire du dérèglement climatique global.

**Interprétation**
Limite physique fondamentale du système civilisationnel.

**Implications**
Impact transversal sur énergie, géopolitique, économie et santé globale.

## 11. Métadonnées de simulation
| Paramètre | Valeur |
|---|---|
| volatility | high |
| predictability | low |
| uncertainty_level | high |
| tipping_point_risk | high |
| systemic_criticality | 5 |
| resilience | 1 |
| adaptability | 2 |

## 12. Trajectoire des signaux 2025 → 2098

Évolution des signaux faibles selon le scénario — comment les précurseurs de 2025 sont devenus des réalités en 2098.

```yaml
signal_to_state:
  - signal: instabilite_saisonniere
    scenarios:
      breakdown:
        evolution: emballements climatiques régionaux et basculements irréversibles
        date_bascule: 2041-2060
        evenement_cle: franchissement de cinq points de basculement simultanés 2053
      fortress_world:
        evolution: gestion territoriale des crises climatiques par les blocs
        date_bascule: 2037-2053
        evenement_cle: création des zones climatiques protégées des blocs 2048
      new_sustainability:
        evolution: stabilisation partielle via géo-ingénierie régulée et décarbonation
        date_bascule: 2032-2048
        evenement_cle: déploiement mondial des puits de carbone technologiques 2040
      eco_communalism:
        evolution: adaptation locale et régénération écologique des territoires
        date_bascule: 2038-2057
        evenement_cle: mouvement de régénération écologique territoriale
      policy_reform:
        evolution: politiques d'atténuation et d'adaptation coordonnées
        date_bascule: 2028-2044
        evenement_cle: accord climatique de Nairobi 2+ avec mécanismes contraignants 2035
      reference:
        evolution: dérèglement progressif avec adaptations insuffisantes
        date_bascule: 2024-2040
        evenement_cle: première décennie au-dessus de 1.5°C 2031

  - signal: stress_hydrique
    scenarios:
      breakdown:
        evolution: guerres de l'eau et effondrements agricoles régionaux
        date_bascule: 2043-2062
        evenement_cle: conflits armés pour les bassins versants 2054
      fortress_world:
        evolution: sécurisation militaire des ressources en eau par les blocs
        date_bascule: 2038-2054
        evenement_cle: militarisation des grands fleuves transfrontaliers 2049
      new_sustainability:
        evolution: gestion intégrée des ressources en eau à l'échelle globale
        date_bascule: 2031-2047
        evenement_cle: Traité mondial sur l'eau et la sécurité hydrique 2038
      eco_communalism:
        evolution: gestion communautaire sobre et régénérative de l'eau
        date_bascule: 2038-2056
        evenement_cle: mouvement mondial de souveraineté hydrique locale
      policy_reform:
        evolution: régulation internationale des usages de l'eau
        date_bascule: 2028-2043
        evenement_cle: Convention de Genève sur le droit à l'eau 2035
      reference:
        evolution: tensions croissantes sans gouvernance cohérente
        date_bascule: 2024-2039
        evenement_cle: première grande crise hydrique régionale documentée 2031

  - signal: captation_carbone_industrielle
    scenarios:
      breakdown:
        evolution: abandon des méga-projets de capture carbone industrielle
        date_bascule: 2042-2061
        evenement_cle: sabotage des installations de capture carbone du Sahara 2055
      fortress_world:
        evolution: déploiement de capture carbone réservé aux territoires des blocs
        date_bascule: 2039-2056
        evenement_cle: programme de capture carbone du Bloc Atlantique 2052
      new_sustainability:
        evolution: généralisation mondiale de la capture directe de carbone
        date_bascule: 2034-2050
        evenement_cle: mise en service du réseau mondial de capture carbone 2043
      eco_communalism:
        evolution: rejet des mégaprojets au profit de la régénération des sols
        date_bascule: 2039-2058
        evenement_cle: mouvement de boycott des fermes de capture carbone industrielles
      policy_reform:
        evolution: déploiement encadré de la capture carbone sous contrôle international
        date_bascule: 2030-2046
        evenement_cle: protocole international de certification de la capture carbone 2037
      reference:
        evolution: déploiement partiel et inégal de la capture carbone
        date_bascule: 2026-2042
        evenement_cle: premiers démonstrateurs industriels de capture carbone à grande échelle 2033

  - signal: megafeux_saisonniers
    scenarios:
      breakdown:
        evolution: mégafeux incontrôlables ravageant des régions entières chaque été
        date_bascule: 2039-2057
        evenement_cle: perte totale des forêts méditerranéennes lors des feux de 2050
      fortress_world:
        evolution: sacrifice des zones à risque incendie hors des blocs
        date_bascule: 2036-2052
        evenement_cle: création des zones rouges incendie hors-bloc 2046
      new_sustainability:
        evolution: surveillance par IA et prévention coordonnée des incendies
        date_bascule: 2033-2049
        evenement_cle: déploiement du réseau mondial de détection précoce des feux 2039
      eco_communalism:
        evolution: gestion communautaire du feu et brûlages dirigés
        date_bascule: 2037-2055
        evenement_cle: renaissance des pratiques autochtones de brûlage dirigé
      policy_reform:
        evolution: coordination internationale des moyens de lutte contre les incendies
        date_bascule: 2027-2043
        evenement_cle: création de la force mondiale anti-incendie de l'ONU 2034
      reference:
        evolution: intensification récurrente des feux de forêt sans réponse globale
        date_bascule: 2025-2041
        evenement_cle: saison record de mégafeux sur trois continents 2032

  - signal: relocalisation_cotiere
    scenarios:
      breakdown:
        evolution: exodes côtiers chaotiques et conflits pour les terres intérieures
        date_bascule: 2044-2063
        evenement_cle: évacuation forcée de Lagos-Est sous tension armée 2057
      fortress_world:
        evolution: relocalisation planifiée des populations côtières à l'intérieur des blocs
        date_bascule: 2040-2057
        evenement_cle: programme de réinstallation côtière du Bloc Atlantique 2051
      new_sustainability:
        evolution: programme mondial de relocalisation côtière planifiée et financée
        date_bascule: 2035-2052
        evenement_cle: lancement du programme mondial de villes-refuges côtières 2044
      eco_communalism:
        evolution: retrait volontaire vers des bioregions intérieures organisées localement
        date_bascule: 2041-2059
        evenement_cle: mouvement de retour vers les terres hautes bioterritoriales
      policy_reform:
        evolution: financement international des plans de relocalisation côtière
        date_bascule: 2031-2048
        evenement_cle: fonds mondial pour la relocalisation côtière de l'ONU 2039
      reference:
        evolution: relocalisations côtières graduelles mais sous-financées et inégales
        date_bascule: 2027-2044
        evenement_cle: premier plan municipal de retrait côtier documenté 2034

  - signal: discours_effondrement_climatique
    scenarios:
      breakdown:
        evolution: normalisation du discours collapsologue et résignation généralisée
        date_bascule: 2038-2056
        evenement_cle: manifeste collapsologue mondial diffusé après le Jour Sans Signal 2041
      fortress_world:
        evolution: récupération du discours d'effondrement par la propagande des blocs
        date_bascule: 2036-2053
        evenement_cle: campagne officielle des blocs sur la fin du monde ancien 2046
      new_sustainability:
        evolution: basculement culturel du récit d'effondrement vers la régénération
        date_bascule: 2030-2046
        evenement_cle: publication du manifeste de la transition régénérative 2037
      eco_communalism:
        evolution: appropriation du discours d'effondrement comme fondement du post-croissance
        date_bascule: 2036-2055
        evenement_cle: diffusion virale du mouvement des veillées de l'effondrement
      policy_reform:
        evolution: reconnaissance institutionnelle de l'éco-anxiété comme enjeu de santé publique
        date_bascule: 2029-2045
        evenement_cle: premier plan national de santé mentale climatique 2034
      reference:
        evolution: diffusion croissante des récits d'effondrement dans le débat public
        date_bascule: 2024-2041
        evenement_cle: best-seller mondial sur l'effondrement civilisationnel 2030
```
