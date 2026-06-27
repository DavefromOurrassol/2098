---
name: energie_ressources_critiques
type: systemic_variable
slug: energie_ressources_critiques
variable_type: moteur
global_influence_level: 5
domain:
    - ecological
    - economic
    - geopolitical
    - technological
influences:
    - [[climat_environnement_global]]
    - [[geopolitique_conflits]]
    - [[organisation_territoires]]
influenced_by:
    - [[climat_environnement_global]]
    - [[systemes_productifs_travail]]
    - [[systeme_economique_redistribution]]
    - [[technologie_information]]
    - [[geopolitique_conflits]]
    - [[frontieres_du_systeme]]
bidirectional_links:
    - [[climat_environnement_global]]
    - [[geopolitique_conflits]]
    - [[systeme_economique_redistribution]]
sub_variables:
  - name: systemes_energetiques
    role: production et distribution d’énergie mondiale
    trend: up
  - name: matieres_premieres_critiques
    role: ressources minérales stratégiques (lithium, terres rares, métaux)
    trend: up
  - name: systemes_alimentaires
    role: sécurité alimentaire mondiale et production agricole
    trend: unstable
  - name: chaines_approvisionnement
    role: logistique globale des flux matériels
    trend: up
  - name: infrastructures_energetiques
    role: réseaux physiques de production et distribution énergétique
    trend: up

scenario_mapping:
  dominant_scenarios:
    - fortress_world
    - new_sustainability
  reinforcing_scenarios:
    - policy_reform
    - reference
  constrained_scenarios:
    - breakdown
simulation:
  volatility: high
  predictability: medium
  uncertainty_level: high
  tipping_point_risk: high
  systemic_criticality: 5
  resilience: 2
  adaptability: 3
states:

  fortress_world:
    level: 82
    volatility: 78
    state_logic: >
      Fragmentation du système énergétique en blocs fermés, sécurisation militarisée des ressources et rupture partielle de la mondialisation énergétique.
    dominant_dynamics:
      - nationalisation des ressources critiques
      - blocs énergétiques fermés
      - compétition inter-blocs
    system_role_shift:
      - variable stratégique militarisée
      - outil de souveraineté énergétique
    coupling_intensity:
      [[geopolitique_conflits]]: 92
      [[organisation_territoires]]: 82
      [[frontieres_du_systeme]]: 85

  new_sustainability:
    level: 38
    volatility: 30
    state_logic: >
      Abondance énergétique relative via fusion, optimisation IA et diversification massive des sources, réduisant fortement la contrainte structurelle globale.
    dominant_dynamics:
      - abondance énergétique relative
      - optimisation algorithmique des réseaux
      - stabilisation des marchés énergétiques
    system_role_shift:
      - contrainte fortement atténuée
      - variable intégrée dans optimisation globale
    coupling_intensity:
      [[technologie_information]]: 92
      [[gouvernance_institutions]]: 82
      [[climat_environnement_global]]: 60
      [[systeme_economique_redistribution]]: 52

  breakdown:
    level: 96
    volatility: 97
    state_logic: >
      Crises énergétiques systémiques majeures entraînant ruptures logistiques, effondrements industriels et conflits généralisés pour l’accès aux ressources critiques.
    dominant_dynamics:
      - pénuries globales critiques
      - fragmentation des chaînes logistiques
      - conflits énergétiques ouverts
    system_role_shift:
      - contrainte dominante non stabilisée
      - facteur de désintégration systémique
    coupling_intensity:
      [[geopolitique_conflits]]: 95
      [[organisation_territoires]]: 88
      [[systemes_productifs_travail]]: 92
      [[climat_environnement_global]]: 88

  eco_communalism:
    level: 50
    volatility: 35
    state_logic: >
      Réduction de la pression énergétique globale via relocalisation, sobriété systémique et optimisation locale des ressources.
    dominant_dynamics:
      - relocalisation des systèmes productifs
      - sobriété énergétique
      - circularité territoriale
    system_role_shift:
      - variable partiellement relocalisée
      - contrainte gérée à l’échelle locale
    coupling_intensity:
      [[organisation_territoires]]: 85
      [[systemes_productifs_travail]]: 75
      [[climat_environnement_global]]: 60

  policy_reform:
    level: 58
    volatility: 45
    state_logic: >
      Stabilisation partielle via coordination internationale, régulation des marchés énergétiques et accélération de la transition vers des systèmes plus efficients et résilients.
    dominant_dynamics:
      - gouvernance énergétique coordonnée
      - optimisation des flux globaux
      - réduction des chocs de prix
    system_role_shift:
      - variable partiellement régulée globalement
      - levier de stabilisation macro-systémique
    coupling_intensity:
      [[gouvernance_institutions]]: 85
      [[technologie_information]]: 82
      [[systeme_economique_redistribution]]: 60
      [[climat_environnement_global]]: 65

  reference:
    level: 72
    volatility: 65
    state_logic: >
      Tension structurelle persistante entre demande énergétique croissante et contraintes physiques, géopolitiques et industrielles de l’offre. Le système reste fonctionnel mais sous contrainte permanente.
    dominant_dynamics:
      - tension énergétique structurelle
      - dépendance aux chaînes globales
      - transition incomplète
    system_role_shift:
      - contrainte centrale du système global
      - amplificateur de déséquilibres systémiques
    coupling_intensity:
      [[climat_environnement_global]]: 75
      [[geopolitique_conflits]]: 80
      [[systeme_economique_redistribution]]: 70
      [[organisation_territoires]]: 65

---

# energie_ressources_critiques

## 1. Identité systémique

**Description**
Système de production, d’accès et de tension autour des ressources énergétiques, matérielles et alimentaires critiques du système global.

**Rôle**
Base matérielle fondamentale conditionnant la production industrielle, la stabilité géopolitique, la croissance économique et la sécurité des systèmes humains.

## 2. Position dans le système

**Influence**
- [[climat_environnement_global]]
- [[geopolitique_conflits]]
- [[organisation_territoires]]

**Influencé par**
- [[climat_environnement_global]]
- [[systemes_productifs_travail]]
- [[systeme_economique_redistribution]]
- [[technologie_information]]
- [[geopolitique_conflits]]
- [[frontieres_du_systeme]]

**Liens bidirectionnels**
- [[climat_environnement_global]]
- [[geopolitique_conflits]]
- [[systeme_economique_redistribution]]

## 3. Dynamique interne
- Direction : **up** | Intensité : **very_high** | Inertie : **very_high** | Vitesse : **medium_fast**

**Tendances**
- croissance continue de la demande énergétique mondiale
- électrification des usages
- transition énergétique contrainte
- tension sur ressources critiques
- fragmentation géopolitique des chaînes d’approvisionnement
- volatilité des marchés énergétiques
- dépendance persistante aux ressources rares

**Dynamiques passées**
- industrialisation fondée sur charbon et pétrole
- mondialisation énergétique et logistique
- dépendance aux hydrocarbures
- financiarisation des ressources stratégiques
- développement nucléaire civil et militaire
- expansion des renouvelables
- vulnérabilité des chaînes globales

**Snapshot**
> Système matériel mondial sous forte contrainte, marqué par une tension croissante entre demande énergétique et disponibilité des ressources critiques, dans un contexte de fragmentation géopolitique et de transition énergétique incomplète.

**tensions**
- abondance énergétique vs rareté structurelle
- centralisation vs décentralisation énergétique
- sécurité énergétique vs coûts économiques
- transition verte vs dépendance fossile
- globalisation vs fragmentation des chaînes

**constraints**
- limites physiques des ressources
- inertie des infrastructures énergétiques
- dépendance aux chaînes globales
- instabilité géopolitique des zones productrices
- temps long de transformation industrielle

**forces_attractives**
- innovation technologique énergétique
- optimisation des réseaux
- diversification des sources d’énergie
- électrification globale
- efficacité énergétique

**forces_repulsives**
- rareté des ressources critiques
- volatilité des prix
- dépendance géopolitique
- impacts environnementaux
- fragmentation logistique


## 4. Structure causale

**Forces attractives**
- innovation énergétique
- optimisation des systèmes
- diversification des ressources
- transition technologique

**Forces répulsives**
- rareté des ressources
- instabilité géopolitique
- coûts d’extraction croissants
- fragmentation des chaînes logistiques

**Contraintes**
- limites physiques des ressources
- inertie des infrastructures
- dépendance industrielle globale
- instabilité politique des zones critiques

**Tensions**
- croissance vs limites physiques
- sécurité vs dépendance
- centralisation vs relocalisation
- transition vs inertie fossile

## 5. Ruptures

**technological**
_core_
- fusion_nucleaire_operationnelle
- stockage_massif_energie
- substitution_materiaux_critiques
- optimisation_ia_reseaux_energetiques
_extended_
- energie_decentralisee_autonome
- systemes_autoreparateurs_infrastructures
- production_matiere_synthetique

**systemic**
_core_
- penuries_globales_ressources
- chocs_energetiques_systemiques
- effondrement_chain_logistiques
_extended_
- fragmentation_blocs_energetiques
- guerre_ressources_globales

**political_social**
_core_
- nationalisation_ressources_strategiques
- guerres_energetiques
- controle_consommation_energie
_extended_
- blocs_energetiques_fermes
- rationnement_global


## 6. Indicateurs
**primary**
- demande_energie
- prix_energie
- volatilite_marches

**secondary**
- dependance_importations
- investissements_renouvelables
- tensions_materiaux_critiques

**systemic**
- securite_energetique_globale
- stabilite_chain_logistique
- capacite_production_ressources



## 7. Signaux faibles
**technological**
- stockage_energie_nouvelle_generation (→ section 12)
- fusion_experimentale
- substitution_materiaux

**geopolitical**
- competition_terres_rares
- securisation_ressources_nationales
- relocalisation_industrielle

**social**
- sensibilisation_penurie_energie
- adaptation_sobriete_energetique (→ section 12)

**environmental**
- stress_ecosystemes_extractifs
- degradation_sites_miniers (→ section 12)

**cognitive_cultural**
- conscience_limites_energetiques
- acceptation_transition_contrainte (→ section 12)



## 8. États par scénario
### [[fortress_world]]
- **level** : 82 | **volatility** : 78

Fragmentation du système énergétique en blocs fermés, sécurisation militarisée des ressources et rupture partielle de la mondialisation énergétique.

**Dynamiques dominantes**
- nationalisation des ressources critiques
- blocs énergétiques fermés
- compétition inter-blocs

**Rôle système**
- variable stratégique militarisée
- outil de souveraineté énergétique

**Couplages**
- [[geopolitique_conflits]] : 92
- [[organisation_territoires]] : 82
- [[frontieres_du_systeme]] : 85

### [[new_sustainability]]
- **level** : 38 | **volatility** : 30

Abondance énergétique relative via fusion, optimisation IA et diversification massive des sources, réduisant fortement la contrainte structurelle globale.

**Dynamiques dominantes**
- abondance énergétique relative
- optimisation algorithmique des réseaux
- stabilisation des marchés énergétiques

**Rôle système**
- contrainte fortement atténuée
- variable intégrée dans optimisation globale

**Couplages**
- [[technologie_information]] : 92
- [[gouvernance_institutions]] : 82
- [[climat_environnement_global]] : 60
- [[systeme_economique_redistribution]] : 52

### [[breakdown]]
- **level** : 96 | **volatility** : 97

Crises énergétiques systémiques majeures entraînant ruptures logistiques, effondrements industriels et conflits généralisés pour l’accès aux ressources critiques.

**Dynamiques dominantes**
- pénuries globales critiques
- fragmentation des chaînes logistiques
- conflits énergétiques ouverts

**Rôle système**
- contrainte dominante non stabilisée
- facteur de désintégration systémique

**Couplages**
- [[geopolitique_conflits]] : 95
- [[organisation_territoires]] : 88
- [[systemes_productifs_travail]] : 92
- [[climat_environnement_global]] : 88

### [[eco_communalism]]
- **level** : 50 | **volatility** : 35

Réduction de la pression énergétique globale via relocalisation, sobriété systémique et optimisation locale des ressources.

**Dynamiques dominantes**
- relocalisation des systèmes productifs
- sobriété énergétique
- circularité territoriale

**Rôle système**
- variable partiellement relocalisée
- contrainte gérée à l’échelle locale

**Couplages**
- [[organisation_territoires]] : 85
- [[systemes_productifs_travail]] : 75
- [[climat_environnement_global]] : 60

### [[policy_reform]]
- **level** : 58 | **volatility** : 45

Stabilisation partielle via coordination internationale, régulation des marchés énergétiques et accélération de la transition vers des systèmes plus efficients et résilients.

**Dynamiques dominantes**
- gouvernance énergétique coordonnée
- optimisation des flux globaux
- réduction des chocs de prix

**Rôle système**
- variable partiellement régulée globalement
- levier de stabilisation macro-systémique

**Couplages**
- [[gouvernance_institutions]] : 85
- [[technologie_information]] : 82
- [[systeme_economique_redistribution]] : 60
- [[climat_environnement_global]] : 65

### [[reference]]
- **level** : 72 | **volatility** : 65

Tension structurelle persistante entre demande énergétique croissante et contraintes physiques, géopolitiques et industrielles de l’offre. Le système reste fonctionnel mais sous contrainte permanente.

**Dynamiques dominantes**
- tension énergétique structurelle
- dépendance aux chaînes globales
- transition incomplète

**Rôle système**
- contrainte centrale du système global
- amplificateur de déséquilibres systémiques

**Couplages**
- [[climat_environnement_global]] : 75
- [[geopolitique_conflits]] : 80
- [[systeme_economique_redistribution]] : 70
- [[organisation_territoires]] : 65



## 9. Scénarios liés

**Dominants** : [[fortress_world]], [[new_sustainability]]
**Renforcés** : [[policy_reform]], [[reference]]
**Contraints** : [[breakdown]]

## 10. Narratif systémique

**Résumé**
Système énergétique mondial sous contrainte structurelle, en transition vers une recomposition profonde des sources, des chaînes d’approvisionnement et des équilibres géopolitiques.

**Dynamiques**
tension croissante entre demande globale, rareté des ressources et transformation technologique lente mais continue.

**Interprétation**
passage d’un régime énergétique globalisé à un système fragmenté, hybride et technologiquement transformé.

**Implications**
reconfiguration des équilibres géopolitiques, économiques et territoriaux autour du contrôle des ressources critiques.

## 11. Métadonnées de simulation
| Paramètre | Valeur |
|---|---|
| volatility | high |
| predictability | medium |
| uncertainty_level | high |
| tipping_point_risk | high |
| systemic_criticality | 5 |
| resilience | 2 |
| adaptability | 3 |

## 12. Trajectoire des signaux 2025 → 2098

Évolution des signaux faibles selon le scénario — comment les précurseurs de 2025 sont devenus des réalités en 2098.

```yaml
signal_to_state:
  - signal: competition_terres_rares
    scenarios:
      breakdown:
        evolution: guerres ouvertes pour les ressources énergétiques et minières
        date_bascule: 2042-2060
        evenement_cle: guerre des lithium-cobalt en Afrique australe 2052
      fortress_world:
        evolution: sécurisation militarisée des gisements par les blocs
        date_bascule: 2037-2053
        evenement_cle: doctrine de sécurité énergétique des blocs 2047
      new_sustainability:
        evolution: gouvernance internationale des ressources critiques de la transition
        date_bascule: 2032-2047
        evenement_cle: Fonds Mondial des Ressources Critiques 2040
      eco_communalism:
        evolution: réduction de la demande par sobriété et recyclage systémique
        date_bascule: 2039-2058
        evenement_cle: mouvement de circularité des matériaux critiques
      policy_reform:
        evolution: accords multilatéraux sur la chaîne d'approvisionnement des minerais
        date_bascule: 2029-2044
        evenement_cle: traité OCDE sur les minerais de la transition 2036
      reference:
        evolution: tensions croissantes et recomposition des alliances minières
        date_bascule: 2025-2040
        evenement_cle: première crise des terres rares post-Covid 2030

  - signal: fusion_experimentale
    scenarios:
      breakdown:
        evolution: abandon des programmes de fusion faute de financement et stabilité
        date_bascule: 2040-2058
        evenement_cle: effondrement des consortiums de recherche fusion 2051
      fortress_world:
        evolution: monopolisation de la fusion par un bloc dominant
        date_bascule: 2045-2062
        evenement_cle: premier réacteur à fusion militarisé du Bloc Asiatique 2058
      new_sustainability:
        evolution: déploiement commercial de la fusion comme backbone énergétique
        date_bascule: 2048-2065
        evenement_cle: premier réseau de réacteurs à fusion commercial 2060
      eco_communalism:
        evolution: marginalisation au profit des énergies renouvelables locales sobres
        date_bascule: 2035-2055
        evenement_cle: abandon communautaire des projets centralisés de fusion
      policy_reform:
        evolution: développement coordonné sous gouvernance internationale
        date_bascule: 2040-2058
        evenement_cle: création de l'Agence Internationale de la Fusion 2045
      reference:
        evolution: développement lent et inégal sans déploiement massif
        date_bascule: 2035-2055
        evenement_cle: premier réacteur à fusion pilote commercial 2052

  - signal: stockage_energie_nouvelle_generation
    scenarios:
      breakdown:
        evolution: effondrement des chaînes d'approvisionnement en matériaux de stockage
        date_bascule: 2041-2059
        evenement_cle: pillage des dépôts de batteries stratégiques à Detroit-Sud 2053
      fortress_world:
        evolution: monopolisation des technologies de stockage par les blocs fermés
        date_bascule: 2036-2052
        evenement_cle: nationalisation des giga-usines de batteries du Bloc Atlantique 2046
      new_sustainability:
        evolution: déploiement mondial du stockage longue durée stabilisant les réseaux renouvelables
        date_bascule: 2030-2046
        evenement_cle: commercialisation mondiale des batteries à flux longue durée 2038
      eco_communalism:
        evolution: généralisation de solutions de stockage modulaires et low-tech locales
        date_bascule: 2037-2056
        evenement_cle: réseau bioterritorial de stockage thermique communautaire
      policy_reform:
        evolution: programme international coordonné de déploiement des technologies de stockage
        date_bascule: 2028-2044
        evenement_cle: lancement du fonds international pour le stockage énergétique 2035
      reference:
        evolution: adoption inégale des technologies de stockage selon les régions
        date_bascule: 2025-2041
        evenement_cle: premiers déploiements commerciaux de stockage longue durée 2032

  - signal: adaptation_sobriete_energetique
    scenarios:
      breakdown:
        evolution: rationnement énergétique imposé déclenchant des émeutes urbaines
        date_bascule: 2042-2061
        evenement_cle: émeutes de l'énergie dans les mégapoles surpeuplées 2054
      fortress_world:
        evolution: rationnement énergétique hiérarchisé selon le statut au sein des blocs
        date_bascule: 2037-2054
        evenement_cle: instauration des quotas énergétiques par catégorie sociale dans les blocs 2048
      new_sustainability:
        evolution: adoption volontaire de modes de vie économes soutenus par l'abondance
        date_bascule: 2031-2047
        evenement_cle: lancement de la campagne mondiale pour la sobriété choisie 2039
      eco_communalism:
        evolution: ancrage de la sobriété énergétique comme valeur fondatrice locale
        date_bascule: 2038-2057
        evenement_cle: charte bioterritoriale de sobriété énergétique partagée
      policy_reform:
        evolution: programmes structurés d'efficacité réduisant progressivement la consommation énergétique
        date_bascule: 2027-2043
        evenement_cle: lancement du plan international de sobriété énergétique 2034
      reference:
        evolution: évolution culturelle progressive vers la sobriété face aux pénuries
        date_bascule: 2025-2042
        evenement_cle: première campagne nationale de sobriété énergétique obligatoire 2032

  - signal: degradation_sites_miniers
    scenarios:
      breakdown:
        evolution: multiplication des catastrophes environnementales sur sites miniers abandonnés
        date_bascule: 2043-2062
        evenement_cle: catastrophe de contamination des mines de lithium d'Afrique australe 2056
      fortress_world:
        evolution: création de zones sacrifiées autour des sites miniers des blocs
        date_bascule: 2038-2055
        evenement_cle: classification des zones minières comme zones sacrifiées par les blocs 2049
      new_sustainability:
        evolution: restauration systématique des sites miniers sous normes mondiales
        date_bascule: 2033-2049
        evenement_cle: adoption de la norme mondiale de restauration minière 2041
      eco_communalism:
        evolution: réappropriation et réhabilitation locale des anciens sites miniers
        date_bascule: 2040-2059
        evenement_cle: mouvement de réhabilitation bioterritoriale des friches minières
      policy_reform:
        evolution: fonds internationaux finançant progressivement la réhabilitation des sites miniers
        date_bascule: 2029-2045
        evenement_cle: création du fonds international de réhabilitation minière 2037
      reference:
        evolution: dégradation continue des sites miniers malgré des réhabilitations locales
        date_bascule: 2026-2043
        evenement_cle: premier rapport mondial sur la dégradation des sites miniers 2033

  - signal: acceptation_transition_contrainte
    scenarios:
      breakdown:
        evolution: acceptation résignée de la transition comme condition de survie
        date_bascule: 2041-2060
        evenement_cle: discours officiel reconnaissant l'impossibilité du retour à l'abondance 2053
      fortress_world:
        evolution: récit de souveraineté énergétique imposé par les blocs
        date_bascule: 2039-2056
        evenement_cle: discours unificateur sur l'autosuffisance énergétique des blocs 2049
      new_sustainability:
        evolution: basculement du récit de contrainte vers celui d'opportunité collective
        date_bascule: 2029-2045
        evenement_cle: lancement du récit mondial de la transition comme opportunité 2038
      eco_communalism:
        evolution: appropriation de la transition comme identité fondatrice des bioterritoires
        date_bascule: 2036-2055
        evenement_cle: manifeste bioterritorial de la sobriété choisie
      policy_reform:
        evolution: acceptation publique croissante construite par la communication institutionnelle
        date_bascule: 2026-2042
        evenement_cle: lancement de la campagne publique de pédagogie énergétique 2033
      reference:
        evolution: acceptation partielle et contestée selon les groupes sociaux
        date_bascule: 2024-2040
        evenement_cle: premier sondage mondial sur l'acceptation de la transition 2031
```
