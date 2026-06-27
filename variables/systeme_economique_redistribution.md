---
name: systeme_economique_redistribution
type: systemic_variable
slug: systeme_economique_redistribution
variable_type: relais
global_influence_level: 5
domain:
    - economic
    - social
    - technological
    - political
influences:
    - [[demographie_mobilite_humaine]]
    - [[technologie_information]]
    - [[gouvernance_institutions]]
    - [[geopolitique_conflits]]
    - [[energie_ressources_critiques]]
    - [[sante_biotechnologies]]
    - [[frontieres_du_systeme]]
    - [[organisation_territoires]]
influenced_by:
    - [[systemes_productifs_travail]]
    - [[technologie_information]]
    - [[gouvernance_institutions]]
    - [[geopolitique_conflits]]
    - [[energie_ressources_critiques]]
bidirectional_links:
    - [[technologie_information]]
    - [[gouvernance_institutions]]
    - [[geopolitique_conflits]]
sub_variables:
  - name: systemes_financiers_globaux
    role: circulation mondiale du capital et des flux financiers
    trend: up
  - name: inegalites_redistribution
    role: distribution des richesses et écarts de patrimoine
    trend: up
  - name: croissance_economique
    role: expansion de la production mondiale de valeur
    trend: unstable
  - name: systemes_redistribution
    role: mécanismes de correction des déséquilibres économiques
    trend: unstable
  - name: economie_plateformes
    role: structuration numérique des échanges économiques
    trend: up


scenario_mapping:
  dominant_scenarios:
    - new_sustainability
    - breakdown
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
    level: 60
    volatility: 55
    state_logic: >
      Économie de blocs fermés avec protectionnisme systémique, nationalisation des ressources stratégiques et fragmentation des échanges mondiaux en circuits régionaux contrôlés.
    dominant_dynamics:
      - protectionnisme systémique des blocs
      - nationalisation des ressources stratégiques
      - fragmentation monétaire régionale
    system_role_shift:
      - instrument de puissance des blocs fermés
      - outil de contrôle redistributif autoritaire
    coupling_intensity:
      [[geopolitique_conflits]]: 80
      [[energie_ressources_critiques]]: 75
      [[gouvernance_institutions]]: 70

  new_sustainability:
    level: 65
    volatility: 30
    state_logic: >
      Économie régulée et redistribuée à l'échelle globale, combinant marchés encadrés, fiscalité universelle et mécanismes de redistribution technologique et énergétique.
    dominant_dynamics:
      - redistribution globale régulée
      - fiscalité universelle sur le capital
      - marchés encadrés par gouvernance IA
    system_role_shift:
      - vecteur de stabilisation sociale globale
      - outil de transition redistributive
    coupling_intensity:
      [[gouvernance_institutions]]: 85
      [[technologie_information]]: 75
      [[systemes_productifs_travail]]: 70

  eco_communalism:
    level: 35
    volatility: 25
    state_logic: >
      Économies locales relocalisées avec circuits courts, monnaies territoriales et systèmes d'échange non marchands dominants, réduisant drastiquement l'intégration économique globale.
    dominant_dynamics:
      - relocalisation des circuits économiques
      - monnaies territoriales et échanges directs
      - démonétisation partielle des besoins essentiels
    system_role_shift:
      - support des communautés autonomes
      - outil de résilience locale
    coupling_intensity:
      [[organisation_territoires]]: 80
      [[valeurs_culture_tempo_sociale]]: 70
      [[systemes_productifs_travail]]: 75

  breakdown:
    level: 95
    volatility: 95
    state_logic: >
      Crises financières systémiques globales avec fragmentation des marchés, effondrement de la confiance monétaire et rupture des chaînes économiques mondiales.
    dominant_dynamics:
      - effondrement des systèmes financiers
      - fragmentation monétaire globale
      - instabilité économique généralisée
    system_role_shift:
      - contrainte dominante destructrice
      - facteur de désintégration systémique globale
    coupling_intensity:
      [[geopolitique_conflits]]: 90
      [[organisation_territoires]]: 80
      [[energie_ressources_critiques]]: 85
      [[demographie_mobilite_humaine]]: 75

  policy_reform:
    level: 55
    volatility: 40
    state_logic: >
      Stabilisation partielle via régulation financière, politiques redistributives et encadrement des marchés numériques, réduisant les extrêmes systémiques sans modifier la structure globale du capitalisme.
    dominant_dynamics:
      - régulation des flux financiers
      - redistribution partielle des richesses
      - réduction de la volatilité systémique
    system_role_shift:
      - variable partiellement stabilisée par gouvernance
      - outil de correction systémique
    coupling_intensity:
      [[gouvernance_institutions]]: 85
      [[technologie_information]]: 80
      [[geopolitique_conflits]]: 65
      [[systemes_productifs_travail]]: 60

  reference:
    level: 70
    volatility: 60
    state_logic: >
      Système économique global fortement financiarisé, instable mais fonctionnel, caractérisé par une forte concentration du capital, une croissance inégale et une dépendance élevée aux flux financiers mondiaux.
    dominant_dynamics:
      - polarisation des richesses
      - financiarisation algorithmique croissante
      - instabilité cyclique des marchés
    system_role_shift:
      - moteur central de déséquilibres systémiques
      - amplificateur des inégalités globales
    coupling_intensity:
      [[geopolitique_conflits]]: 80
      [[technologie_information]]: 85
      [[energie_ressources_critiques]]: 75
      [[demographie_mobilite_humaine]]: 65

---

# systeme_economique_redistribution

## 1. Identité systémique

**Description**
Système global d’allocation des ressources, de production de valeur et de redistribution des richesses.

**Rôle**
Infrastructure centrale de circulation de la valeur économique conditionnant stabilité sociale, inégalités, croissance et capacité d’adaptation du système global.

## 2. Position dans le système

**Influence**
- [[demographie_mobilite_humaine]]
- [[technologie_information]]
- [[gouvernance_institutions]]
- [[geopolitique_conflits]]
- [[energie_ressources_critiques]]
- [[sante_biotechnologies]]
- [[frontieres_du_systeme]]
- [[organisation_territoires]]

**Influencé par**
- [[systemes_productifs_travail]]
- [[technologie_information]]
- [[gouvernance_institutions]]
- [[geopolitique_conflits]]
- [[energie_ressources_critiques]]

**Liens bidirectionnels**
- [[technologie_information]]
- [[gouvernance_institutions]]
- [[geopolitique_conflits]]

## 3. Dynamique interne
- Direction : **up** | Intensité : **very_high** | Inertie : **high** | Vitesse : **fast**

**Tendances**
- financiarisation algorithmique
- polarisation des richesses
- croissance inégale mondiale
- montée des économies de plateformes
- automatisation des flux économiques
- désynchronisation économie réelle / financière
- instabilité cyclique des marchés

**Dynamiques passées**
- capitalisme industriel
- mondialisation commerciale et financière
- libéralisation économique
- crises financières systémiques
- financiarisation de l’économie réelle
- montée des plateformes numériques
- explosion des marchés globaux

**Snapshot**
> Transformation du système économique mondial vers une automatisation algorithmique des flux financiers, combinée à une polarisation structurelle des richesses et une instabilité systémique persistante.

**tensions**
- efficacité des marchés vs régulation
- accumulation de richesse vs redistribution
- économie réelle vs économie financière
- centralisation monétaire vs fragmentation économique
- croissance vs stagnation structurelle

**constraints**
- inertie des institutions financières globales
- dépendance aux systèmes monétaires existants
- instabilité cyclique des marchés
- déséquilibres structurels de richesse
- interdépendance des économies nationales

**forces_attractives**
- efficacité des marchés
- innovation financière
- optimisation des flux de capital
- croissance potentielle
- automatisation des échanges

**forces_repulsives**
- inégalités structurelles
- instabilité financière
- spéculation excessive
- fragmentation économique
- fragilité systémique globale


## 4. Structure causale

**Forces attractives**
- innovation financière
- optimisation des marchés
- automatisation économique
- croissance potentielle

**Forces répulsives**
- inégalités croissantes
- instabilité financière
- fragmentation monétaire
- déconnexion économie réelle / virtuelle

**Contraintes**
- dépendance infrastructures financières héritées
- cycles économiques instables
- inertie institutionnelle globale
- interdépendance systémique

**Tensions**
- régulation vs marché libre
- redistribution vs accumulation
- réel vs financier
- centralisation vs fragmentation
- croissance vs stagnation

## 5. Ruptures

**technological**
_core_
- ia_financiere_totale
- monnaies_programmables
- automatisation_marches
- economie_predictive
_extended_
- finance_autonome_decentralisee
- allocation_temps_reel
- disparition_intermediaires_financiers

**systemic**
_core_
- effondrement_systeme_financier_global
- fragmentation_monetaire
- desintermediation_totale
_extended_
- blocs_economiques_separes
- crise_monetaire_synchronisee

**political_social**
_core_
- revenu_universel
- controle_etatique_economie
- fiscalite_automatique
_extended_
- redistribution_algorithmique
- planification_economique_assistee_ia


## 6. Indicateurs
**primary**
- volatilite_marches
- inegalites_wealth
- automatisation_financiere

**secondary**
- croissance_inegale
- part_economie_plateformes
- taux_redistribution

**systemic**
- interconnexion_financiere_globale
- instabilite_cyclique
- concentration_capital
- monnaies_numeriques_centrales
- trading_automatise_ia
- finance_autonome

**geopolitical**
- competition_monetaire_globale
- fragmentation_financiere

**social**
- revenu_universel_experiments
- polarisation_patrimoniale

**environmental**
- pression_economique_climat
- finance_verte_strategique

**cognitive_cultural**
- acceptation_ia_economique
- perte_confiance_systeme_financier



## 7. Signaux faibles

**technological**
- automatisation financière algorithmique (→ automatisation_financière_algorithmique, déjà développé)
- domination de l'économie de plateformes (→ economie_plateformes_dominante)

**geopolitical**
- dédollarisation progressive (→ dedollarisation_progressive, déjà développé)
- guerre monétaire entre blocs économiques

**social**
- explosion des inégalités patrimoniales (→ explosion_inegalites_patrimoniales)
- crise des systèmes de retraite et de redistribution

**environmental**
- taxation carbone globale du capital (→ taxation_carbone_globale)
- effondrement de la valeur des actifs fossiles

**cognitive_cultural**
- remise en cause du paradigme croissance/capitalisme (→ remise_en_cause_capitalisme_croissance)
- normalisation du revenu universel

## 8. États par scénario
### [[breakdown]]
- **level** : 95 | **volatility** : 95

Crises financières systémiques globales avec fragmentation des marchés, effondrement de la confiance monétaire et rupture des chaînes économiques mondiales.

**Dynamiques dominantes**
- effondrement des systèmes financiers
- fragmentation monétaire globale
- instabilité économique généralisée

**Rôle système**
- contrainte dominante destructrice
- facteur de désintégration systémique globale

**Couplages**
- [[geopolitique_conflits]] : 90
- [[organisation_territoires]] : 80
- [[energie_ressources_critiques]] : 85
- [[demographie_mobilite_humaine]] : 75

### [[policy_reform]]
- **level** : 55 | **volatility** : 40

Stabilisation partielle via régulation financière, politiques redistributives et encadrement des marchés numériques, réduisant les extrêmes systémiques sans modifier la structure globale du capitalisme.

**Dynamiques dominantes**
- régulation des flux financiers
- redistribution partielle des richesses
- réduction de la volatilité systémique

**Rôle système**
- variable partiellement stabilisée par gouvernance
- outil de correction systémique

**Couplages**
- [[gouvernance_institutions]] : 85
- [[technologie_information]] : 80
- [[geopolitique_conflits]] : 65
- [[systemes_productifs_travail]] : 60

### [[reference]]
- **level** : 70 | **volatility** : 60

Système économique global fortement financiarisé, instable mais fonctionnel, caractérisé par une forte concentration du capital, une croissance inégale et une dépendance élevée aux flux financiers mondiaux.

**Dynamiques dominantes**
- polarisation des richesses
- financiarisation algorithmique croissante
- instabilité cyclique des marchés

**Rôle système**
- moteur central de déséquilibres systémiques
- amplificateur des inégalités globales

**Couplages**
- [[geopolitique_conflits]] : 80
- [[technologie_information]] : 85
- [[energie_ressources_critiques]] : 75
- [[demographie_mobilite_humaine]] : 65


### [[fortress_world]]
- **level** : 60 | **volatility** : 55

Économie de blocs fermés avec protectionnisme systémique, nationalisation des ressources stratégiques et fragmentation des échanges mondiaux en circuits régionaux contrôlés.

**Dynamiques dominantes**
- protectionnisme systémique des blocs
- nationalisation des ressources stratégiques
- fragmentation monétaire régionale

**Rôle système**
- instrument de puissance des blocs fermés
- outil de contrôle redistributif autoritaire

**Couplages**
- [[geopolitique_conflits]] : 80
- [[energie_ressources_critiques]] : 75
- [[gouvernance_institutions]] : 70

### [[new_sustainability]]
- **level** : 65 | **volatility** : 30

Économie régulée et redistribuée à l'échelle globale, combinant marchés encadrés, fiscalité universelle et mécanismes de redistribution technologique et énergétique.

**Dynamiques dominantes**
- redistribution globale régulée
- fiscalité universelle sur le capital
- marchés encadrés par gouvernance IA

**Rôle système**
- vecteur de stabilisation sociale globale
- outil de transition redistributive

**Couplages**
- [[gouvernance_institutions]] : 85
- [[technologie_information]] : 75
- [[systemes_productifs_travail]] : 70

### [[eco_communalism]]
- **level** : 35 | **volatility** : 25

Économies locales relocalisées avec circuits courts, monnaies territoriales et systèmes d'échange non marchands dominants, réduisant drastiquement l'intégration économique globale.

**Dynamiques dominantes**
- relocalisation des circuits économiques
- monnaies territoriales et échanges directs
- démonétisation partielle des besoins essentiels

**Rôle système**
- support des communautés autonomes
- outil de résilience locale

**Couplages**
- [[organisation_territoires]] : 80
- [[valeurs_culture_tempo_sociale]] : 70
- [[systemes_productifs_travail]] : 75


## 9. Scénarios liés

**Dominants** : [[new_sustainability]], [[breakdown]]
**Renforcés** : [[policy_reform]], [[reference]]
**Contraints** : [[breakdown]]

## 10. Narratif systémique

**Résumé**
Transition du système économique mondial vers une automatisation algorithmique croissante et une polarisation structurelle.

**Dynamiques**
accélération de la financiarisation, montée des plateformes et instabilité cyclique des marchés globaux.

**Interprétation**
bascule progressive vers une économie hybride entre marchés humains et systèmes algorithmiques de décision.

**Implications**
reconfiguration des inégalités, du travail, de la gouvernance et des structures de redistribution à l’échelle mondiale.

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

Évolution des signaux faibles selon le scénario.

```yaml
signal_to_state:
  - signal: automatisation_financière_algorithmique
    scenarios:
      breakdown:
        evolution: dégénération en systèmes financiers autonomes non coordonnés et instables
        date_bascule: 2041-2055
        evenement_cle: effondrement des protocoles de régulation des IA financières
      fortress_world:
        evolution: outils de contrôle économique des blocs fermés
        date_bascule: 2038-2052
        evenement_cle: nationalisation des infrastructures algorithmiques financières
      new_sustainability:
        evolution: intégration dans une gouvernance financière mondiale régulée
        date_bascule: 2035-2048
        evenement_cle: Accords de Genève sur la régulation des IA financières
      eco_communalism:
        evolution: rejet et retour aux échanges directs et monnaies locales
        date_bascule: 2042-2060
        evenement_cle: mouvement de déconnexion des marchés algorithmiques
      policy_reform:
        evolution: encadrement progressif par taxation et régulation sectorielle
        date_bascule: 2033-2047
        evenement_cle: traité international sur les marchés algorithmiques
      reference:
        evolution: dominance croissante instable des marchés algorithmiques
        date_bascule: 2030-2045
        evenement_cle: crise flash-crash globale de 2039

  - signal: dedollarisation_progressive
    scenarios:
      breakdown:
        evolution: effondrement du système monétaire international et chaos des changes
        date_bascule: 2048-2062
        evenement_cle: abandon du dollar comme devise de réserve globale
      fortress_world:
        evolution: émergence de zones monétaires fermées par blocs géopolitiques
        date_bascule: 2043-2057
        evenement_cle: création du système monétaire des Blocs de Shanghai
      new_sustainability:
        evolution: adoption d'une unité de compte globale multi-ancrée
        date_bascule: 2040-2055
        evenement_cle: création du Droit de Tirage Universel 2.0
      eco_communalism:
        evolution: prolifération de monnaies territoriales et systèmes de troc
        date_bascule: 2045-2065
        evenement_cle: mouvement des monnaies bioterritioriales
      policy_reform:
        evolution: gouvernance multilatérale du système monétaire international
        date_bascule: 2038-2052
        evenement_cle: réforme du FMI et création du Conseil Monétaire Mondial
      reference:
        evolution: multipolarité monétaire instable avec tensions récurrentes
        date_bascule: 2035-2050
        evenement_cle: crise de la dette souveraine de 2041

  - signal: explosion_inegalites_patrimoniales
    scenarios:
      breakdown:
        evolution: polarisation extrême entre enclaves fortunées et populations appauvries
        date_bascule: 2038-2056
        evenement_cle: rapport confirmant une concentration record du patrimoine mondial 2051
      fortress_world:
        evolution: stratification patrimoniale organisée selon le statut citoyen des blocs
        date_bascule: 2034-2051
        evenement_cle: instauration de classes patrimoniales officielles dans les blocs 2046
      new_sustainability:
        evolution: réduction significative des inégalités via la fiscalité universelle du capital
        date_bascule: 2029-2045
        evenement_cle: entrée en vigueur de l'impôt mondial sur la fortune 2039
      eco_communalism:
        evolution: dissolution progressive du patrimoine monétaire au profit des communs locaux
        date_bascule: 2036-2055
        evenement_cle: généralisation des communs bioterritoriaux remplaçant la propriété privée
      policy_reform:
        evolution: réduction partielle des inégalités par des réformes fiscales progressives
        date_bascule: 2025-2041
        evenement_cle: adoption de la réforme fiscale internationale sur les grandes fortunes 2035
      reference:
        evolution: creusement continu des inégalités patrimoniales malgré les indignations récurrentes
        date_bascule: 2024-2040
        evenement_cle: premier rapport mondial sur la concentration patrimoniale record 2032

  - signal: taxation_carbone_globale
    scenarios:
      breakdown:
        evolution: échec et abandon des mécanismes de taxation carbone mondiale
        date_bascule: 2039-2057
        evenement_cle: suspension générale des mécanismes de taxation carbone 2050
      fortress_world:
        evolution: fragmentation de la taxation carbone en régimes propres aux blocs
        date_bascule: 2035-2052
        evenement_cle: adoption de barèmes carbone distincts par chaque bloc 2048
      new_sustainability:
        evolution: généralisation de la taxation carbone mondiale comme pilier redistributif
        date_bascule: 2030-2046
        evenement_cle: entrée en vigueur de la taxe carbone mondiale universelle 2038
      eco_communalism:
        evolution: remplacement de la taxation carbone par une redevabilité écologique locale
        date_bascule: 2037-2056
        evenement_cle: charte bioterritoriale de redevabilité écologique directe
      policy_reform:
        evolution: coordination progressive de la taxation carbone entre grandes économies
        date_bascule: 2026-2042
        evenement_cle: accord international sur un prix plancher du carbone 2033
      reference:
        evolution: application partielle et inégale de la taxation carbone mondiale
        date_bascule: 2025-2041
        evenement_cle: premier rapport sur l'échec de la coordination carbone mondiale 2031

  - signal: remise_en_cause_capitalisme_croissance
    scenarios:
      breakdown:
        evolution: effondrement du récit de croissance remplacé par la survie immédiate
        date_bascule: 2040-2058
        evenement_cle: dernier sommet économique mondial centré sur la croissance 2052
      fortress_world:
        evolution: recadrage du récit de croissance comme puissance des blocs
        date_bascule: 2036-2053
        evenement_cle: doctrine officielle de puissance économique des blocs 2047
      new_sustainability:
        evolution: remplacement du PIB par des indicateurs mondiaux de bien-être
        date_bascule: 2031-2047
        evenement_cle: adoption mondiale des indicateurs de prosperité post-croissance 2039
      eco_communalism:
        evolution: rejet fondateur du capitalisme de croissance dans les bioterritoires
        date_bascule: 2038-2057
        evenement_cle: charte fondatrice post-croissance des assemblées bioterritoriales
      policy_reform:
        evolution: complément progressif du récit de croissance par des indicateurs de bien-être
        date_bascule: 2027-2043
        evenement_cle: adoption du tableau de bord international post-PIB 2035
      reference:
        evolution: contestation croissante mais persistance du récit de croissance dominant
        date_bascule: 2026-2042
        evenement_cle: premier débat mondial télévisé sur la fin de la croissance 2032

  - signal: economie_plateformes_dominante
    scenarios:
      breakdown:
        evolution: fragmentation des plateformes économiques mondiales sous les ruptures réseau
        date_bascule: 2042-2060
        evenement_cle: panne en cascade des grandes plateformes économiques mondiales 2051
      fortress_world:
        evolution: cloisonnement des plateformes économiques au sein des écosystèmes numériques des blocs
        date_bascule: 2037-2054
        evenement_cle: nationalisation des plateformes numériques par le Bloc Atlantique 2045
      new_sustainability:
        evolution: régulation des plateformes économiques comme infrastructures d'intérêt public mondial
        date_bascule: 2032-2048
        evenement_cle: adoption du statut de bien commun pour les plateformes mondiales 2039
      eco_communalism:
        evolution: remplacement des plateformes centralisées par des réseaux coopératifs décentralisés
        date_bascule: 2039-2058
        evenement_cle: lancement du réseau coopératif bioterritorial d'échanges numériques
      policy_reform:
        evolution: régulation progressive des plateformes par des réformes antitrust et fiscales
        date_bascule: 2028-2044
        evenement_cle: adoption de la directive mondiale sur la taxation des plateformes 2034
      reference:
        evolution: domination croissante et concentration continue de l'économie de plateformes
        date_bascule: 2024-2041
        evenement_cle: premier rapport sur la concentration record des plateformes mondiales 2032
```
