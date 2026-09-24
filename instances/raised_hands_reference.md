---
name: Mains Levées (Raised Hands - The Lattice)
type: instance
slug: raised_hands_reference
entite: raised_hands
scenario: reference
localisation:
  zone: ameriques_multipolaires
  lieu: The Lattice (cités-relais)
  type_lieu: infrastructure

type_dans_scenario: organisation

role_dans_scenario: >
  Mouvement émergent de résidents précaires des villes de The Lattice (Amériques Multipolaires) réclamant des élections et un droit de vote pour les clients-contractants. Toléré mais surveillé, ses meneurs risquent la résiliation de leur contrat de résidence, c'est-à-dire l'expulsion. Il incarne la lutte pour l'inclusion démocratique dans un système où la gouvernance est segmentée entre citoyens à part entière et résidents sous contrat, dont le statut juridique les prive de représentation politique.

responsabilites: >
  Organiser des manifestations pacifiques, des campagnes de sensibilisation et des actions juridiques pour contester les clauses d'exclusion politique des contrats de résidence. Documenter les cas de répression (expulsions, résiliations de contrats) et les porter devant les tribunaux hybrides des cités-relais. Négocier avec les administrations locales pour obtenir des droits symboliques (consultations publiques, comités de quartier) en attendant une réforme systémique.

impact_local: 3
impact_systemique_global: 2

variables_influencees:
    - gouvernance_institutions
    - valeurs_culture_tempo_sociale
    - systeme_economique_redistribution

zone_geographique:
    - urbaine
    - régionale

zone_systemique:
    - gouvernance
    - société

alliances:
    - collectifs_de_journalisme_embarque_reference
    - conseil_de_geneve_pour_les_droits_biosociaux_reference
    - mouvement_pour_la_libre_circulation_des_personnes_et_des_donnees_reference
    - voix_du_dehors_reference

oppositions:
    - administrations_hybrides_des_cites_relais_peripheriques_reference
    - consortiums_prives_de_gestion_des_donnees_critiques_reference
    - plateformes_centralisees_de_narration_officielle_reference

type_relation_dominante: conflit

annee_debut: 2039
annee_fin: 

trajectoire: émergent
est_clandestin: false
generation: transition

injection:
  garantie_selection: false
  type: custom
  annee_injection: 2039
  contexte_injection: >
    Les *Mains Levées* agissent comme un catalyseur de la fragmentation institutionnelle de The Lattice en exposant les limites d'un système qui exclut une partie croissante de sa population de la participation politique. Leur lutte accélère la prise de conscience des inégalités structurelles (systeme_economique_redistribution) et force les régimes hybrides à adapter leurs discours ou leurs méthodes de répression (gouvernance_institutions). Leur impact culturel (valeurs_culture_tempo_sociale) est immédiat : ils redéfinissent la citoyenneté comme un droit à conquérir plutôt qu'un statut octroyé, influençant d'autres mouvements précaires à l'échelle régionale.
  impact_sur_variables:
  - variable: gouvernance_institutions
    delta_level: 8
    duree: 15
    polarite: 1
  - variable: valeurs_culture_tempo_sociale
    delta_level: 6
    duree: 10
    polarite: 1
  - variable: systeme_economique_redistribution
    delta_level: 4
    duree: 20
    polarite: 1
  propagation:
    via_matrice: false

description_journalistique: >
  Depuis 2039, les rues des cités-relais de The Lattice résonnent des slogans des *Mains Levées*, un mouvement qui a transformé la colère des résidents précaires en une revendication politique structurée. Vêtus de gilets fluorescents marqués d'un poing levé stylisé, ses membres organisent des sit-ins devant les centres administratifs, brandissant des contrats de résidence annotés de rouge pour dénoncer les clauses d'exclusion politique. Leur dernière action coup de poing ? Une « élection fantôme » organisée en parallèle des scrutins officiels, où les clients-contractants ont voté symboliquement pour des candidats fictifs, leurs bulletins projetés en temps réel sur les façades des tours de bureaux. Les images, diffusées via les réseaux mesh locaux, ont fait le tour des plateformes d'information indépendantes, forçant les autorités à réagir — entre tolérance contrainte et répression ciblée.

signes_distinctifs: >
  Le symbole du mouvement est un poing levé dont les doigts se transforment en flèches pointant vers le haut, stylisé en circuit imprimé pour évoquer la contractualisation algorithmique des vies. Les membres portent souvent des brassards ou des écussons luminescents affichant leur « score de résidence » (un chiffre calculé à partir de leur ancienneté, de leur contribution économique et de leur « conformité sociale »), détourné en outil de mobilisation. Leurs manifestations mêlent codes visuels des luttes syndicales traditionnelles et esthétique cyberpunk, avec des projections holographiques de contrats déchirés flottant au-dessus des foules.
retry_signes_distinctifs: non

tensions_narratives: >
  Le mouvement est tiraillé entre deux stratégies : une frange radicale, menée par d'anciens juristes des cités-relais, pousse à des actions de désobéissance civile ciblant les infrastructures logistiques (blocages de hubs de livraison, piratage des systèmes de résiliation automatique de contrats), tandis qu'une aile modérée privilégie le lobbying auprès des consortiums énergétiques et des plateformes IA, espérant obtenir des droits par la négociation. La répression s'intensifie : plusieurs meneurs ont été expulsés vers des zones grises après des « audits algorithmiques » de leur contrat, déclenchant des vagues de solidarité transfrontalières. Leur plus grand défi ? Éviter la récupération par les blocs souverainistes, qui voient dans leur lutte un levier pour affaiblir The Lattice, tout en résistant à la tentation de la violence face à un système conçu pour les ignorer.

date_creation: 2026-09-24
---

# Mains Levées (Raised Hands - The Lattice)

## Rôle dans [[reference]]
Mouvement émergent de résidents précaires des villes de The Lattice (Amériques Multipolaires) réclamant des élections et un droit de vote pour les clients-contractants. Toléré mais surveillé, ses meneurs risquent la résiliation de leur contrat de résidence, c'est-à-dire l'expulsion. Il incarne la lutte pour l'inclusion démocratique dans un système où la gouvernance est segmentée entre citoyens à part entière et résidents sous contrat, dont le statut juridique les prive de représentation politique.

## Responsabilités
Organiser des manifestations pacifiques, des campagnes de sensibilisation et des actions juridiques pour contester les clauses d'exclusion politique des contrats de résidence. Documenter les cas de répression (expulsions, résiliations de contrats) et les porter devant les tribunaux hybrides des cités-relais. Négocier avec les administrations locales pour obtenir des droits symboliques (consultations publiques, comités de quartier) en attendant une réforme systémique.

## Variables influencées
- [[gouvernance_institutions]]
- [[valeurs_culture_tempo_sociale]]
- [[systeme_economique_redistribution]]

## Relations
**Alliés** : [[collectifs_de_journalisme_embarque_reference]], [[conseil_de_geneve_pour_les_droits_biosociaux_reference]], [[mouvement_pour_la_libre_circulation_des_personnes_et_des_donnees_reference]], [[voix_du_dehors_reference]]
**Opposants** : [[administrations_hybrides_des_cites_relais_peripheriques_reference]], [[consortiums_prives_de_gestion_des_donnees_critiques_reference]], [[plateformes_centralisees_de_narration_officielle_reference]]

## Description journalistique
Depuis 2039, les rues des cités-relais de The Lattice résonnent des slogans des *Mains Levées*, un mouvement qui a transformé la colère des résidents précaires en une revendication politique structurée. Vêtus de gilets fluorescents marqués d'un poing levé stylisé, ses membres organisent des sit-ins devant les centres administratifs, brandissant des contrats de résidence annotés de rouge pour dénoncer les clauses d'exclusion politique. Leur dernière action coup de poing ? Une « élection fantôme » organisée en parallèle des scrutins officiels, où les clients-contractants ont voté symboliquement pour des candidats fictifs, leurs bulletins projetés en temps réel sur les façades des tours de bureaux. Les images, diffusées via les réseaux mesh locaux, ont fait le tour des plateformes d'information indépendantes, forçant les autorités à réagir — entre tolérance contrainte et répression ciblée.

## Tensions narratives
Le mouvement est tiraillé entre deux stratégies : une frange radicale, menée par d'anciens juristes des cités-relais, pousse à des actions de désobéissance civile ciblant les infrastructures logistiques (blocages de hubs de livraison, piratage des systèmes de résiliation automatique de contrats), tandis qu'une aile modérée privilégie le lobbying auprès des consortiums énergétiques et des plateformes IA, espérant obtenir des droits par la négociation. La répression s'intensifie : plusieurs meneurs ont été expulsés vers des zones grises après des « audits algorithmiques » de leur contrat, déclenchant des vagues de solidarité transfrontalières. Leur plus grand défi ? Éviter la récupération par les blocs souverainistes, qui voient dans leur lutte un levier pour affaiblir The Lattice, tout en résistant à la tentation de la violence face à un système conçu pour les ignorer.
