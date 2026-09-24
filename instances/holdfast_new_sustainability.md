---
name: Vestiges des Citadelles Holdfast
type: instance
slug: holdfast_new_sustainability
entite: holdfast
scenario: new_sustainability
localisation:
  zone: null
  lieu: null
  type_lieu: null
  note: transnationale_sans_ancrage

type_dans_scenario: infrastructure

role_dans_scenario: >
  Dans les décennies 2020-2050, les Holdfasts étaient des enclaves fortifiées construites par des élites pour se soustraire aux crises systémiques (climatiques, géopolitiques, économiques). En 2098, ces infrastructures ne sont plus que des ruines ou des musées, symboles d'une époque où la privatisation de la souveraineté territoriale était perçue comme une solution viable. Leur mémoire persiste comme un avertissement contre l'exclusion et la fragmentation, souvent évoquée dans les débats sur la gouvernance distribuée et la résilience collective.

responsabilites: >
  À leur apogée, les Holdfasts offraient sécurité physique, autarcie énergétique et alimentaire, et une gouvernance autonome à leurs résidents. Aujourd'hui, leurs vestiges servent de sites archéologiques ou de lieux de mémoire, parfois reconvertis en centres de recherche sur les échecs des modèles élitistes de survie.

impact_local: 1
impact_systemique_global: 1

variables_influencees:
    - gouvernance_institutions
    - systeme_economique_redistribution
    - organisation_territoires

zone_geographique:
    - nationale
    - régionale

zone_systemique:
    - gouvernance
    - infrastructure
    - société

alliances:

oppositions:

type_relation_dominante: conflit

annee_debut: 2028
annee_fin: 2065

trajectoire: historique
est_clandestin: false
generation: pré-crise

injection:
  type: custom
  annee_injection: 2028
  contexte_injection: >
    Les Holdfasts ont affaibli la gouvernance_institutions en sapant la confiance dans les systèmes collectifs pendant leur existence, mais leur échec a ensuite servi de catalyseur pour renforcer les mécanismes de redistribution et de gouvernance partagée dans les décennies suivantes.
  impact_sur_variables:
  - variable: gouvernance_institutions
    delta_level: -5
    duree: 20
    polarite: -1
  - variable: systeme_economique_redistribution
    delta_level: 3
    duree: 15
    polarite: 1
  propagation:
    via_matrice: false

description_journalistique: >
  En 2098, les Holdfasts ne sont plus que des reliques d'un passé révolu. Ces citadelles high-tech, construites dans les années 2030 par des milliardaires et des gouvernements en déroute, promettaient sécurité et autarcie à une élite prête à tout pour échapper aux crises. Aujourd'hui, leurs murs blindés et leurs serres verticales abandonnées sont devenus des attractions touristiques ou des laboratoires à ciel ouvert pour les historiens de l'effondrement. Les jeunes générations les voient comme un symbole de l'égoïsme d'une époque où l'on croyait encore que la survie pouvait être une affaire privée.

signes_distinctifs: >
  Architecture brutaliste et futuriste mêlant béton armé, panneaux solaires intégrés et systèmes de filtration d'air autonomes. Les vestiges portent souvent des graffitis ou des fresques commémorant les mouvements sociaux qui ont contribué à leur déclin. Certains sites conservent des artefacts technologiques de l'époque, comme des drones de surveillance ou des systèmes de gestion algorithmique des ressources.
retry_signes_distinctifs: non

tensions_narratives: >
  Les Holdfasts soulèvent des questions persistantes sur les limites de la gouvernance collective : leur échec a-t-il prouvé que l'exclusion est une impasse, ou simplement que leur modèle était mal conçu ? Certains mouvements souverainistes actuels les citent comme des exemples de 'résilience mal comprise', tandis que les défenseurs des communs y voient la preuve que la sécurité ne peut être garantie que par l'inclusion. Leur mémoire est aussi instrumentalisée dans les débats sur la fiscalité universelle et la redistribution technologique.

date_creation: 2026-09-24
---

# Vestiges des Citadelles Holdfast

## Rôle dans [[new_sustainability]]
Dans les décennies 2020-2050, les Holdfasts étaient des enclaves fortifiées construites par des élites pour se soustraire aux crises systémiques (climatiques, géopolitiques, économiques). En 2098, ces infrastructures ne sont plus que des ruines ou des musées, symboles d'une époque où la privatisation de la souveraineté territoriale était perçue comme une solution viable. Leur mémoire persiste comme un avertissement contre l'exclusion et la fragmentation, souvent évoquée dans les débats sur la gouvernance distribuée et la résilience collective.

## Responsabilités
À leur apogée, les Holdfasts offraient sécurité physique, autarcie énergétique et alimentaire, et une gouvernance autonome à leurs résidents. Aujourd'hui, leurs vestiges servent de sites archéologiques ou de lieux de mémoire, parfois reconvertis en centres de recherche sur les échecs des modèles élitistes de survie.

## Variables influencées
- [[gouvernance_institutions]]
- [[systeme_economique_redistribution]]
- [[organisation_territoires]]

## Relations
**Alliés** : _aucun défini_
**Opposants** : _aucun défini_

## Description journalistique
En 2098, les Holdfasts ne sont plus que des reliques d'un passé révolu. Ces citadelles high-tech, construites dans les années 2030 par des milliardaires et des gouvernements en déroute, promettaient sécurité et autarcie à une élite prête à tout pour échapper aux crises. Aujourd'hui, leurs murs blindés et leurs serres verticales abandonnées sont devenus des attractions touristiques ou des laboratoires à ciel ouvert pour les historiens de l'effondrement. Les jeunes générations les voient comme un symbole de l'égoïsme d'une époque où l'on croyait encore que la survie pouvait être une affaire privée.

## Tensions narratives
Les Holdfasts soulèvent des questions persistantes sur les limites de la gouvernance collective : leur échec a-t-il prouvé que l'exclusion est une impasse, ou simplement que leur modèle était mal conçu ? Certains mouvements souverainistes actuels les citent comme des exemples de 'résilience mal comprise', tandis que les défenseurs des communs y voient la preuve que la sécurité ne peut être garantie que par l'inclusion. Leur mémoire est aussi instrumentalisée dans les débats sur la fiscalité universelle et la redistribution technologique.
