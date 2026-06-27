name: <nom_variable>
type: systemic_variable
slug: <slug_variable>

# ───────────────────────
# 1. IDENTITÉ SYSTÉMIQUE
# ───────────────────────

description: >
  <description longue de la variable, rôle dans le système global>

role: >
  <rôle fonctionnel dans le système global>

domain:
  - <domaine_1>
  - <domaine_2>
  - <domaine_3>

variable_type: <moteur | reactive | structurel | régulateur>
global_influence_level: <1-5>

# ───────────────────────
# 2. POSITION DANS LE SYSTÈME
# ───────────────────────

influences:
  - <variable_1>
  - <variable_2>

influenced_by:
  - <variable_1>
  - <variable_2>

bidirectional_links:
  - <variable_1>
  - <variable_2>

sub_variables:

  - name: <sub_variable_1>
    role: >
      <rôle de la sous-variable>
    trend: <up | down | unstable | accelerating | saturating>
    links:
      - <variable>

  - name: <sub_variable_2>
    role: >
      <rôle>
    trend: <trend>
    links:
      - <variable>

# ───────────────────────
# 3. DYNAMIQUE INTERNE
# ───────────────────────

direction: <up | down | oscillating>
intensity: <low | medium | high | very_high>
inertia: <low | medium | high>
speed: <slow | medium | fast | very_fast>

trends:
  - <tendance_1>
  - <tendance_2>

past_dynamics:
  - <dynamique_historique_1>
  - <dynamique_historique_2>

snapshot:

  summary: >
    <état actuel synthétique>

  tensions:
    - <tension_1>
    - <tension_2>

  constraints:
    - <contrainte_1>
    - <contrainte_2>

  forces_attractives:
    - <force_1>
    - <force_2>

  forces_repulsives:
    - <force_1>
    - <force_2>

# ───────────────────────
# 4. STRUCTURE CAUSALE
# ───────────────────────

forces_attractives:
  - <cause_positive_1>
  - <cause_positive_2>

forces_repulsives:
  - <cause_negative_1>
  - <cause_negative_2>

constraints:
  - <contrainte_1>
  - <contrainte_2>

tensions:
  - <tension_1>
  - <tension_2>

# ───────────────────────
# 5. RUPTURES
# ───────────────────────

ruptures:

  technological:
    core:
      - <rupture_tech_core_1>
      - <rupture_tech_core_2>

    extended:
      - <rupture_tech_extended_1>

  systemic:
    core:
      - <rupture_systemic_core_1>
      - <rupture_systemic_core_2>

    extended:
      - <rupture_systemic_extended_1>

  political_social:
    core:
      - <rupture_social_core_1>
      - <rupture_social_core_2>

    extended:
      - <rupture_social_extended_1>

# ───────────────────────
# 6. INDICATEURS
# ───────────────────────

indicators:

  primary:
    - <indicateur_1>
    - <indicateur_2>

  secondary:
    - <indicateur_1>
    - <indicateur_2>

  systemic:
    - <indicateur_1>
    - <indicateur_2>

# ───────────────────────
# 7. SIGNAUX FAIBLES
# ───────────────────────

signals:

  technological:
    - <signal_tech_1>

  geopolitical:
    - <signal_geo_1>

  social:
    - <signal_social_1>

  environmental:
    - <signal_env_1>

  cognitive_cultural:
    - <signal_culturel_1>

# ───────────────────────
# 8. ÉTATS POSSIBLES
# ───────────────────────

states:

  reference:
    level: <0-100>
    volatility: <0-100>
    state_logic: >
      <description état de référence>
    dominant_dynamics:
      - <dynamique_1>
    system_role_shift:
      - <rôle système>
    coupling_intensity:
      <variable_1>: <0-100>

  policy_reform:
    level: <0-100>
    volatility: <0-100>
    state_logic: >
      <description>
    dominant_dynamics:
      - <dynamique>

  breakdown:
    level: <0-100>
    volatility: <0-100>
    state_logic: >
      <description>

  fortress_world:
    level: <0-100>
    volatility: <0-100>
    state_logic: >
      <description>

  eco_communalism:
    level: <0-100>
    volatility: <0-100>
    state_logic: >
      <description>

  new_sustainability:
    level: <0-100>
    volatility: <0-100>
    state_logic: >
      <description>

# ───────────────────────
# 9. SCÉNARIOS
# ───────────────────────

scenario_mapping:

  dominant_scenarios:
    - <scenario>

  reinforcing_scenarios:
    - <scenario>

  constrained_scenarios:
    - <scenario>

# ───────────────────────
# 10. NARRATIF SYSTÉMIQUE
# ───────────────────────

narrative:

  summary: >
    <résumé global>

  dynamics: >
    <dynamique globale>

  interpretation: >
    <lecture systémique>

  implications: >
    <conséquences globales>

# ───────────────────────
# 11. MÉTADONNÉES DE SIMULATION
# ───────────────────────

simulation:
  volatility: <low|medium|high|very_high>
  predictability: <low|medium|high>
  uncertainty_level: <low|medium|high|very_high>
  tipping_point_risk: <low|medium|high>
  systemic_criticality: <1-5>
  resilience: <1-5>
  adaptability: <1-5>