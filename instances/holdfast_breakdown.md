---
name: Les Vestiges des Citadelles
type: instance
slug: holdfast_breakdown
entite: holdfast
scenario: breakdown
localisation:
  zone: null
  lieu: null
  type_lieu: null
  note: transnationale_sans_ancrage

type_dans_scenario: infrastructure

role_dans_scenario: >
  Holdfasts mythifiés, ces enclaves fortifiées des années 2020-2050 incarnent le rêve brisé d'une élite se retranchant derrière des murs physiques et politiques pour échapper à l'effondrement. En 2098, elles ne sont plus que des ruines ou des légendes urbaines, évoquées comme symbole d'un monde où la sécurité se payait par l'exclusion. Leur mémoire persiste dans les récits des survivants, souvent idéalisés ou diabolisés, et sert de repoussoir aux nouvelles formes d'organisation collective qui émergent des décombres.

responsabilites: >
  À leur apogée, ces infrastructures assuraient l'autarcie énergétique, alimentaire et sécuritaire de leurs résidents, tout en érigeant des barrières juridiques et physiques pour se soustraire aux lois communes. Leurs archives, partiellement préservées, révèlent des protocoles de gestion de crise aujourd'hui obsolètes, mais aussi des traces de leur dépendance paradoxale aux systèmes qu'elles rejetaient (logistique, énergie, main-d'œuvre extérieure).

impact_local: 2
impact_systemique_global: 1

variables_influencees:
    - organisation_territoires
    - gouvernance_institutions
    - systeme_economique_redistribution

zone_geographique:
    - nationale
    - régionale

zone_systemique:
    - gouvernance
    - infrastructure
    - société

alliances:

oppositions:
    - federation_communs_territoriaux_breakdown
    - communes_rust_belt_breakdown
    - collectifs_du_seuil_breakdown

type_relation_dominante: conflit

annee_debut: 2028
annee_fin: 2065

trajectoire: historique
est_clandestin: false
generation: pré-crise

injection:
  garantie_selection: false
  type: custom
  annee_injection: 2028
  contexte_injection: >
    Les Holdfasts ont accéléré la fragmentation territoriale en normalisant l'idée que des espaces pouvaient être soustraits au contrôle public, affaiblissant durablement la légitimité des institutions communes. Leur existence a aussi creusé les inégalités en privatisant des ressources critiques (eau, énergie, sécurité), rendant toute redistribution ultérieure plus difficile.
  impact_sur_variables:
  - variable: organisation_territoires
    delta_level: -5
    duree: 20
    polarite: -1
  - variable: gouvernance_institutions
    delta_level: -3
    duree: 15
    polarite: -1
  propagation:
    via_matrice: false

description_journalistique: >
  Dans les années 2040, alors que les mégapoles s'effondraient sous le poids des pénuries et des conflits, une poignée d'ultra-riches et de technocrates ont cru pouvoir acheter leur salut en s'enfermant dans des forteresses high-tech. Ces 'Citadelles', comme on les appelait alors, étaient des îlots d'abondance où l'eau coulait à flots, l'électricité ne manquait jamais, et les drones patrouillaient jour et nuit. Aujourd'hui, en 2098, leurs murs lézardés abritent des squats de réfugiés ou des bases pour milices locales. Les rares archives qui en subsistent sont devenues des objets de fascination morbide, comme les reliques d'une époque où l'on croyait encore que la survie était une question de murs et de privilèges.

signes_distinctifs: >
  Architecture brutaliste et high-tech, murs d'enceinte de plusieurs mètres de haut, tours de surveillance automatisées (aujourd'hui rouillées), jardins hydroponiques à l'abandon. Les logos des corporations qui les finançaient (NexCore, Ergo-Wian) sont encore visibles, tagués ou effacés par le temps. Les survivants évoquent des 'portes qui ne s'ouvraient que pour les bons codes', aujourd'hui inutiles.
retry_signes_distinctifs: non

tensions_narratives: >
  Ces vestiges cristallisent les débats sur la responsabilité des élites dans l'effondrement : étaient-elles des boucs émissaires commodes, ou des acteurs clés d'un système qui a sciemment sacrifié le bien commun ? Leur mémoire divise aussi les nouvelles générations : certains y voient un avertissement contre toute forme de repli, d'autres un modèle à réinventer, mais cette fois pour tous. Enfin, la question de leurs archives hante les historiens : que contenaient-elles vraiment, et qui en détient encore les clés ?

date_creation: 2026-09-24
---

# Les Vestiges des Citadelles

## Rôle dans [[breakdown]]
Holdfasts mythifiés, ces enclaves fortifiées des années 2020-2050 incarnent le rêve brisé d'une élite se retranchant derrière des murs physiques et politiques pour échapper à l'effondrement. En 2098, elles ne sont plus que des ruines ou des légendes urbaines, évoquées comme symbole d'un monde où la sécurité se payait par l'exclusion. Leur mémoire persiste dans les récits des survivants, souvent idéalisés ou diabolisés, et sert de repoussoir aux nouvelles formes d'organisation collective qui émergent des décombres.

## Responsabilités
À leur apogée, ces infrastructures assuraient l'autarcie énergétique, alimentaire et sécuritaire de leurs résidents, tout en érigeant des barrières juridiques et physiques pour se soustraire aux lois communes. Leurs archives, partiellement préservées, révèlent des protocoles de gestion de crise aujourd'hui obsolètes, mais aussi des traces de leur dépendance paradoxale aux systèmes qu'elles rejetaient (logistique, énergie, main-d'œuvre extérieure).

## Variables influencées
- [[organisation_territoires]]
- [[gouvernance_institutions]]
- [[systeme_economique_redistribution]]

## Relations
**Alliés** : _aucun défini_
**Opposants** : [[federation_communs_territoriaux_breakdown]], [[communes_rust_belt_breakdown]], [[collectifs_du_seuil_breakdown]]

## Description journalistique
Dans les années 2040, alors que les mégapoles s'effondraient sous le poids des pénuries et des conflits, une poignée d'ultra-riches et de technocrates ont cru pouvoir acheter leur salut en s'enfermant dans des forteresses high-tech. Ces 'Citadelles', comme on les appelait alors, étaient des îlots d'abondance où l'eau coulait à flots, l'électricité ne manquait jamais, et les drones patrouillaient jour et nuit. Aujourd'hui, en 2098, leurs murs lézardés abritent des squats de réfugiés ou des bases pour milices locales. Les rares archives qui en subsistent sont devenues des objets de fascination morbide, comme les reliques d'une époque où l'on croyait encore que la survie était une question de murs et de privilèges.

## Tensions narratives
Ces vestiges cristallisent les débats sur la responsabilité des élites dans l'effondrement : étaient-elles des boucs émissaires commodes, ou des acteurs clés d'un système qui a sciemment sacrifié le bien commun ? Leur mémoire divise aussi les nouvelles générations : certains y voient un avertissement contre toute forme de repli, d'autres un modèle à réinventer, mais cette fois pour tous. Enfin, la question de leurs archives hante les historiens : que contenaient-elles vraiment, et qui en détient encore les clés ?
