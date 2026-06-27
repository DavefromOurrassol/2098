---
name: Liquidation du Mouvement Commun Américain
type: event_instance
slug: election_parti_commun_americain_fortress_world
archetype: election_parti_commun_americain
scenario: fortress_world
localisation:
  zone: bloc_atlantique
  lieu: États-Unis (Bloc Atlantique)
  type_lieu: region
type_evenement: political_social
portee: continentale
date: 2052
date_label: automne 2052
impossible: false
custom: true
description: >
  Trois ans avant les élections prévues, le Commandement Atlantique classe
  le Mouvement Commun Américain comme organisation subversive. En octobre 2052,
  ses dirigeants sont arrêtés lors d'une opération coordonnée dans 14 villes.
  L'élection de 2055 se tient sans candidat de gauche viable. Le mouvement
  entre dans la clandestinité.
consequences: >
  Radicalisation d'une frange de la gauche américaine. Création de cellules
  clandestines dans les zones abandonnées du Midwest. Le nom "Mouvement Commun"
  devient un symbole de résistance dans les réseaux non certifiés.
realisation: >
  L'élection n'a pas lieu comme prévu — le Commandement Atlantique l'empêche
  en 2052 par dissolution forcée du mouvement. Ce qui devait être une victoire
  électorale devient une répression fondatrice, plus structurante encore
  que la victoire n'aurait pu l'être.
impact_sur_variables:
  - variable: gouvernance_institutions
    delta_level: 5
    duree: 15
    polarite: -1
  - variable: valeurs_culture_tempo_sociale
    delta_level: 8
    duree: 25
    polarite: -1
  - variable: geopolitique_conflits
    delta_level: 5
    duree: 10
    polarite: 1
propagation:
  via_matrice: true
acteurs_impliques: []
note_coherence: >
  Dans fortress_world, la gouvernance autoritaire (level 50) ne tolère pas
  les mouvements politiques alternatifs. La répression préventive est cohérente
  avec le système de scoring citoyen déployé depuis 2046.
date_creation: 2098-01-01
---

# Liquidation du Mouvement Commun Américain

## Réalisation dans [[fortress_world]]
L'élection n'a pas lieu comme prévu — le Commandement Atlantique l'empêche
en 2052 par dissolution forcée du mouvement. Ce qui devait être une victoire
électorale devient une répression fondatrice, plus structurante encore
que la victoire n'aurait pu l'être.

## Description journalistique
Trois ans avant les élections prévues, le Commandement Atlantique classe
le Mouvement Commun Américain comme organisation subversive. En octobre 2052,
ses dirigeants sont arrêtés lors d'une opération coordonnée dans 14 villes.
L'élection de 2055 se tient sans candidat de gauche viable.

## Conséquences
Radicalisation d'une frange de la gauche américaine. Création de cellules
clandestines dans les zones abandonnées du Midwest. Le nom "Mouvement Commun"
devient un symbole de résistance dans les réseaux non certifiés.

## Impact sur les variables
- **gouvernance_institutions** : delta -5 sur 15 ans
- **valeurs_culture_tempo_sociale** : delta -8 sur 25 ans
- **geopolitique_conflits** : delta +5 sur 10 ans

## Acteurs impliqués
_aucun_

## Note de cohérence
Dans fortress_world, la gouvernance autoritaire (level 50) ne tolère pas
les mouvements politiques alternatifs. La répression préventive est cohérente
avec le système de scoring citoyen déployé depuis 2046.
