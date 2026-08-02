---
# ─────────────────────────────────────────
# IDENTITÉ
# ─────────────────────────────────────────
name: <nom_instance>
type: instance
slug: <slug_entite>_<slug_scenario>
entite: <slug_entite>
scenario: <slug_scenario>

# ─────────────────────────────────────────
# NATURE CONTEXTUELLE
# ─────────────────────────────────────────
type_dans_scenario: IA | organisation | entreprise | institution | infrastructure | réseau | humain | système | hybride | autre

role_dans_scenario: >
  <fonction narrative et systémique dans ce scénario>

responsabilites: >
  <actions concrètes exercées dans ce monde>

# ─────────────────────────────────────────
# IMPACT SYSTÉMIQUE
# ─────────────────────────────────────────
impact_local: 0
impact_systemique_global: 0

# ─────────────────────────────────────────
# VARIABLES & SYSTÈME
# ─────────────────────────────────────────
variables_influencees:
  - <variable_1>
  - <variable_2>

# ─────────────────────────────────────────
# ZONES
# ─────────────────────────────────────────
zone_geographique:
  - locale | urbaine | nationale | régionale | continentale | globale

zone_systemique:
  - énergie | IA | gouvernance | économie | information | sécurité | infrastructure | société | cyberspace | orbital

# ─────────────────────────────────────────
# RELATIONS ENTRE INSTANCES
# ─────────────────────────────────────────
alliances:
  - <slug_instance_alliee>

oppositions:
  - <slug_instance_opposee>

type_relation_dominante: coopération | alliance stratégique | dépendance | neutralité | rivalité | conflit | infiltration | symbiose

# ─────────────────────────────────────────
# TEMPS
# ─────────────────────────────────────────
annee_debut: 2026
annee_fin:

etat_temporel: actif | disparu | transformé | clandestin | historique | mythifié

age_historique: émergent | marginal | ascendant | dominant | mature | déclinant | résiduel | mythifié

generation: pré-crise | transition | post-effondrement | IA-native | forteresse | reconstruction | ère cognitive

# ─────────────────────────────────────────
# INJECTION TEMPORELLE (entités custom uniquement)
# ─────────────────────────────────────────
injection:
  type: canonique
  annee_injection:
  contexte_injection: >
  impact_sur_variables:
    - variable:
      delta_level:
      duree:
      polarite:
  propagation:
    via_matrice: false

# ─────────────────────────────────────────
# NARRATIF
# ─────────────────────────────────────────
description_journalistique: >
  <version exploitable directement dans les articles —
  comment un journaliste de 2098 décrirait cette entité>

signes_distinctifs: >
  <éléments visuels, symboliques, stylistiques
  qui rendent cette entité reconnaissable>

tensions_narratives: >
  <conflits, enjeux, trajectoires possibles —
  ce qui rend cette entité narrativement intéressante>

---

# <Nom de l'instance>

## Rôle dans [[<slug_scenario>]]
<description narrative du rôle dans ce monde>

## Relations
**Alliés** : <liste des instances alliées avec [[wikilinks]]>
**Opposants** : <liste des instances opposées avec [[wikilinks]]>

## Variables influencées
<liste avec [[wikilinks]] et description de l'influence>

## Tensions narratives
<développement des tensions pour les articles>
