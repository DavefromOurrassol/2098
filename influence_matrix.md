---
name: influence_matrix
type: interaction_matrix
slug: influence_matrix
total_edges: 132
variables_count: 12

# Résumé par variable (outgoing)
variable_stats:
  [[systeme_economique_redistribution]]:
    outgoing_edges: 11
    avg_weight: 0.68
    max_weight: 0.9
    cascade_links: 3
    reinforcing_links: 6
  [[gouvernance_institutions]]:
    outgoing_edges: 11
    avg_weight: 0.66
    max_weight: 0.9
    cascade_links: 1
    reinforcing_links: 6
  [[geopolitique_conflits]]:
    outgoing_edges: 11
    avg_weight: 0.76
    max_weight: 0.95
    cascade_links: 6
    reinforcing_links: 4
  [[valeurs_culture_tempo_sociale]]:
    outgoing_edges: 11
    avg_weight: 0.55
    max_weight: 0.7
    cascade_links: 0
    reinforcing_links: 7
  [[organisation_territoires]]:
    outgoing_edges: 11
    avg_weight: 0.7
    max_weight: 0.85
    cascade_links: 3
    reinforcing_links: 7
  [[sante_biotechnologies]]:
    outgoing_edges: 11
    avg_weight: 0.54
    max_weight: 0.7
    cascade_links: 0
    reinforcing_links: 5
  [[frontieres_du_systeme]]:
    outgoing_edges: 11
    avg_weight: 0.6
    max_weight: 0.8
    cascade_links: 3
    reinforcing_links: 2
  [[technologie_information]]:
    outgoing_edges: 11
    avg_weight: 0.74
    max_weight: 0.9
    cascade_links: 0
    reinforcing_links: 11
  [[climat_environnement_global]]:
    outgoing_edges: 11
    avg_weight: 0.62
    max_weight: 0.8
    cascade_links: 8
    reinforcing_links: 1
  [[energie_ressources_critiques]]:
    outgoing_edges: 11
    avg_weight: 0.68
    max_weight: 0.95
    cascade_links: 7
    reinforcing_links: 2
  [[demographie_mobilite_humaine]]:
    outgoing_edges: 11
    avg_weight: 0.7
    max_weight: 0.8
    cascade_links: 3
    reinforcing_links: 7
  [[systemes_productifs_travail]]:
    outgoing_edges: 11
    avg_weight: 0.75
    max_weight: 0.9
    cascade_links: 3
    reinforcing_links: 8

# Edges complets
edges:
  - source: [[systeme_economique_redistribution]]
    target: [[gouvernance_institutions]]
    weight: 0.8
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: reinforcing

  - source: [[systeme_economique_redistribution]]
    target: [[geopolitique_conflits]]
    weight: 0.75
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[systeme_economique_redistribution]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.55
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: reinforcing

  - source: [[systeme_economique_redistribution]]
    target: [[organisation_territoires]]
    weight: 0.65
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[systeme_economique_redistribution]]
    target: [[sante_biotechnologies]]
    weight: 0.4
    polarity: 1
    lag: 3
    nonlinearity: low
    temporal_weight: 0.4
    feedback_role: delayed

  - source: [[systeme_economique_redistribution]]
    target: [[frontieres_du_systeme]]
    weight: 0.5
    polarity: 1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.7
    feedback_role: balancing

  - source: [[systeme_economique_redistribution]]
    target: [[technologie_information]]
    weight: 0.85
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[systeme_economique_redistribution]]
    target: [[climat_environnement_global]]
    weight: 0.6
    polarity: -1
    lag: 4
    nonlinearity: high
    temporal_weight: 0.7
    feedback_role: cascade

  - source: [[systeme_economique_redistribution]]
    target: [[energie_ressources_critiques]]
    weight: 0.85
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: cascade

  - source: [[systeme_economique_redistribution]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.65
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[systeme_economique_redistribution]]
    target: [[systemes_productifs_travail]]
    weight: 0.9
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[gouvernance_institutions]]
    target: [[systeme_economique_redistribution]]
    weight: 0.8
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: reinforcing

  - source: [[gouvernance_institutions]]
    target: [[geopolitique_conflits]]
    weight: 0.9
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: cascade

  - source: [[gouvernance_institutions]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.6
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: reinforcing

  - source: [[gouvernance_institutions]]
    target: [[organisation_territoires]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[gouvernance_institutions]]
    target: [[sante_biotechnologies]]
    weight: 0.55
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: delayed

  - source: [[gouvernance_institutions]]
    target: [[frontieres_du_systeme]]
    weight: 0.45
    polarity: 1
    lag: 3
    nonlinearity: high
    temporal_weight: 0.6
    feedback_role: balancing

  - source: [[gouvernance_institutions]]
    target: [[technologie_information]]
    weight: 0.9
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[gouvernance_institutions]]
    target: [[climat_environnement_global]]
    weight: 0.5
    polarity: 1
    lag: 4
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: delayed

  - source: [[gouvernance_institutions]]
    target: [[energie_ressources_critiques]]
    weight: 0.55
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: balancing

  - source: [[gouvernance_institutions]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[gouvernance_institutions]]
    target: [[systemes_productifs_travail]]
    weight: 0.65
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[geopolitique_conflits]]
    target: [[systeme_economique_redistribution]]
    weight: 0.75
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[geopolitique_conflits]]
    target: [[gouvernance_institutions]]
    weight: 0.9
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[geopolitique_conflits]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.65
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: reinforcing

  - source: [[geopolitique_conflits]]
    target: [[organisation_territoires]]
    weight: 0.85
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[geopolitique_conflits]]
    target: [[sante_biotechnologies]]
    weight: 0.5
    polarity: -1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: delayed

  - source: [[geopolitique_conflits]]
    target: [[frontieres_du_systeme]]
    weight: 0.8
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[geopolitique_conflits]]
    target: [[technologie_information]]
    weight: 0.85
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[geopolitique_conflits]]
    target: [[climat_environnement_global]]
    weight: 0.65
    polarity: -1
    lag: 4
    nonlinearity: high
    temporal_weight: 0.7
    feedback_role: cascade

  - source: [[geopolitique_conflits]]
    target: [[energie_ressources_critiques]]
    weight: 0.95
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: cascade

  - source: [[geopolitique_conflits]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.75
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[geopolitique_conflits]]
    target: [[systemes_productifs_travail]]
    weight: 0.7
    polarity: -1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: reinforcing

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[systeme_economique_redistribution]]
    weight: 0.55
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: reinforcing

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[gouvernance_institutions]]
    weight: 0.6
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: reinforcing

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[geopolitique_conflits]]
    weight: 0.6
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: reinforcing

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[organisation_territoires]]
    weight: 0.55
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[sante_biotechnologies]]
    weight: 0.5
    polarity: 1
    lag: 3
    nonlinearity: low
    temporal_weight: 0.4
    feedback_role: delayed

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[frontieres_du_systeme]]
    weight: 0.45
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: balancing

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[technologie_information]]
    weight: 0.7
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[climat_environnement_global]]
    weight: 0.4
    polarity: 1
    lag: 4
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: delayed

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[energie_ressources_critiques]]
    weight: 0.4
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: balancing

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[valeurs_culture_tempo_sociale]]
    target: [[systemes_productifs_travail]]
    weight: 0.6
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[organisation_territoires]]
    target: [[systeme_economique_redistribution]]
    weight: 0.65
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[organisation_territoires]]
    target: [[gouvernance_institutions]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[organisation_territoires]]
    target: [[geopolitique_conflits]]
    weight: 0.85
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[organisation_territoires]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.55
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[organisation_territoires]]
    target: [[sante_biotechnologies]]
    weight: 0.6
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: reinforcing

  - source: [[organisation_territoires]]
    target: [[frontieres_du_systeme]]
    weight: 0.6
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: balancing

  - source: [[organisation_territoires]]
    target: [[technologie_information]]
    weight: 0.75
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[organisation_territoires]]
    target: [[climat_environnement_global]]
    weight: 0.7
    polarity: -1
    lag: 4
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[organisation_territoires]]
    target: [[energie_ressources_critiques]]
    weight: 0.7
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[organisation_territoires]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.75
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[organisation_territoires]]
    target: [[systemes_productifs_travail]]
    weight: 0.8
    polarity: 1
    lag: 1
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: reinforcing

  - source: [[sante_biotechnologies]]
    target: [[systeme_economique_redistribution]]
    weight: 0.4
    polarity: 1
    lag: 3
    nonlinearity: low
    temporal_weight: 0.4
    feedback_role: delayed

  - source: [[sante_biotechnologies]]
    target: [[gouvernance_institutions]]
    weight: 0.55
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: reinforcing

  - source: [[sante_biotechnologies]]
    target: [[geopolitique_conflits]]
    weight: 0.5
    polarity: -1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: delayed

  - source: [[sante_biotechnologies]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.5
    polarity: 1
    lag: 3
    nonlinearity: low
    temporal_weight: 0.4
    feedback_role: delayed

  - source: [[sante_biotechnologies]]
    target: [[organisation_territoires]]
    weight: 0.6
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: reinforcing

  - source: [[sante_biotechnologies]]
    target: [[frontieres_du_systeme]]
    weight: 0.5
    polarity: 1
    lag: 3
    nonlinearity: high
    temporal_weight: 0.7
    feedback_role: balancing

  - source: [[sante_biotechnologies]]
    target: [[technologie_information]]
    weight: 0.65
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[sante_biotechnologies]]
    target: [[climat_environnement_global]]
    weight: 0.5
    polarity: 1
    lag: 4
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: delayed

  - source: [[sante_biotechnologies]]
    target: [[energie_ressources_critiques]]
    weight: 0.45
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: balancing

  - source: [[sante_biotechnologies]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[sante_biotechnologies]]
    target: [[systemes_productifs_travail]]
    weight: 0.6
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[frontieres_du_systeme]]
    target: [[systeme_economique_redistribution]]
    weight: 0.5
    polarity: 1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.7
    feedback_role: balancing

  - source: [[frontieres_du_systeme]]
    target: [[gouvernance_institutions]]
    weight: 0.45
    polarity: 1
    lag: 3
    nonlinearity: high
    temporal_weight: 0.6
    feedback_role: balancing

  - source: [[frontieres_du_systeme]]
    target: [[geopolitique_conflits]]
    weight: 0.8
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[frontieres_du_systeme]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.45
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: balancing

  - source: [[frontieres_du_systeme]]
    target: [[organisation_territoires]]
    weight: 0.6
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: balancing

  - source: [[frontieres_du_systeme]]
    target: [[sante_biotechnologies]]
    weight: 0.5
    polarity: 1
    lag: 3
    nonlinearity: high
    temporal_weight: 0.7
    feedback_role: balancing

  - source: [[frontieres_du_systeme]]
    target: [[technologie_information]]
    weight: 0.6
    polarity: 1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[frontieres_du_systeme]]
    target: [[climat_environnement_global]]
    weight: 0.75
    polarity: -1
    lag: 4
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[frontieres_du_systeme]]
    target: [[energie_ressources_critiques]]
    weight: 0.7
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[frontieres_du_systeme]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.55
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: balancing

  - source: [[frontieres_du_systeme]]
    target: [[systemes_productifs_travail]]
    weight: 0.65
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[systeme_economique_redistribution]]
    weight: 0.85
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[gouvernance_institutions]]
    weight: 0.9
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[geopolitique_conflits]]
    weight: 0.85
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.7
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[organisation_territoires]]
    weight: 0.75
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[sante_biotechnologies]]
    weight: 0.65
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[frontieres_du_systeme]]
    weight: 0.6
    polarity: 1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[climat_environnement_global]]
    weight: 0.55
    polarity: 1
    lag: 3
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[energie_ressources_critiques]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.65
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[technologie_information]]
    target: [[systemes_productifs_travail]]
    weight: 0.9
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[climat_environnement_global]]
    target: [[systeme_economique_redistribution]]
    weight: 0.6
    polarity: -1
    lag: 4
    nonlinearity: high
    temporal_weight: 0.7
    feedback_role: cascade

  - source: [[climat_environnement_global]]
    target: [[gouvernance_institutions]]
    weight: 0.5
    polarity: 1
    lag: 4
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: delayed

  - source: [[climat_environnement_global]]
    target: [[geopolitique_conflits]]
    weight: 0.65
    polarity: -1
    lag: 4
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[climat_environnement_global]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.4
    polarity: 1
    lag: 4
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: delayed

  - source: [[climat_environnement_global]]
    target: [[organisation_territoires]]
    weight: 0.7
    polarity: -1
    lag: 4
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[climat_environnement_global]]
    target: [[sante_biotechnologies]]
    weight: 0.5
    polarity: -1
    lag: 4
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: cascade

  - source: [[climat_environnement_global]]
    target: [[frontieres_du_systeme]]
    weight: 0.75
    polarity: -1
    lag: 4
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[climat_environnement_global]]
    target: [[technologie_information]]
    weight: 0.55
    polarity: 1
    lag: 3
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: reinforcing

  - source: [[climat_environnement_global]]
    target: [[energie_ressources_critiques]]
    weight: 0.6
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[climat_environnement_global]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.8
    polarity: -1
    lag: 3
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[climat_environnement_global]]
    target: [[systemes_productifs_travail]]
    weight: 0.75
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[energie_ressources_critiques]]
    target: [[systeme_economique_redistribution]]
    weight: 0.85
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: cascade

  - source: [[energie_ressources_critiques]]
    target: [[gouvernance_institutions]]
    weight: 0.55
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[energie_ressources_critiques]]
    target: [[geopolitique_conflits]]
    weight: 0.95
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: cascade

  - source: [[energie_ressources_critiques]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.4
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: balancing

  - source: [[energie_ressources_critiques]]
    target: [[organisation_territoires]]
    weight: 0.7
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[energie_ressources_critiques]]
    target: [[sante_biotechnologies]]
    weight: 0.45
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.5
    feedback_role: balancing

  - source: [[energie_ressources_critiques]]
    target: [[frontieres_du_systeme]]
    weight: 0.7
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[energie_ressources_critiques]]
    target: [[technologie_information]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[energie_ressources_critiques]]
    target: [[climat_environnement_global]]
    weight: 0.6
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[energie_ressources_critiques]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.7
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[energie_ressources_critiques]]
    target: [[systemes_productifs_travail]]
    weight: 0.85
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[demographie_mobilite_humaine]]
    target: [[systeme_economique_redistribution]]
    weight: 0.65
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[demographie_mobilite_humaine]]
    target: [[gouvernance_institutions]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[demographie_mobilite_humaine]]
    target: [[geopolitique_conflits]]
    weight: 0.75
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[demographie_mobilite_humaine]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[demographie_mobilite_humaine]]
    target: [[organisation_territoires]]
    weight: 0.75
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[demographie_mobilite_humaine]]
    target: [[sante_biotechnologies]]
    weight: 0.7
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[demographie_mobilite_humaine]]
    target: [[frontieres_du_systeme]]
    weight: 0.55
    polarity: 1
    lag: 3
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: balancing

  - source: [[demographie_mobilite_humaine]]
    target: [[technologie_information]]
    weight: 0.65
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[demographie_mobilite_humaine]]
    target: [[climat_environnement_global]]
    weight: 0.8
    polarity: -1
    lag: 3
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[demographie_mobilite_humaine]]
    target: [[energie_ressources_critiques]]
    weight: 0.7
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[demographie_mobilite_humaine]]
    target: [[systemes_productifs_travail]]
    weight: 0.8
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: reinforcing

  - source: [[systemes_productifs_travail]]
    target: [[systeme_economique_redistribution]]
    weight: 0.9
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: reinforcing

  - source: [[systemes_productifs_travail]]
    target: [[gouvernance_institutions]]
    weight: 0.65
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[systemes_productifs_travail]]
    target: [[geopolitique_conflits]]
    weight: 0.7
    polarity: -1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: cascade

  - source: [[systemes_productifs_travail]]
    target: [[valeurs_culture_tempo_sociale]]
    weight: 0.6
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[systemes_productifs_travail]]
    target: [[organisation_territoires]]
    weight: 0.8
    polarity: 1
    lag: 1
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: reinforcing

  - source: [[systemes_productifs_travail]]
    target: [[sante_biotechnologies]]
    weight: 0.6
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.6
    feedback_role: reinforcing

  - source: [[systemes_productifs_travail]]
    target: [[frontieres_du_systeme]]
    weight: 0.65
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: reinforcing

  - source: [[systemes_productifs_travail]]
    target: [[technologie_information]]
    weight: 0.9
    polarity: 1
    lag: 1
    nonlinearity: high
    temporal_weight: 1.0
    feedback_role: reinforcing

  - source: [[systemes_productifs_travail]]
    target: [[climat_environnement_global]]
    weight: 0.75
    polarity: -1
    lag: 2
    nonlinearity: high
    temporal_weight: 0.8
    feedback_role: cascade

  - source: [[systemes_productifs_travail]]
    target: [[energie_ressources_critiques]]
    weight: 0.85
    polarity: -1
    lag: 1
    nonlinearity: high
    temporal_weight: 0.9
    feedback_role: cascade

  - source: [[systemes_productifs_travail]]
    target: [[demographie_mobilite_humaine]]
    weight: 0.8
    polarity: 1
    lag: 2
    nonlinearity: medium
    temporal_weight: 0.7
    feedback_role: reinforcing

---

# Matrice d'influence

> Graphe causal du système monde — 132 arêtes dirigées entre 12 variables.

## Résumé par variable

| Variable | Edges sortants | Poids moy. | Cascades | Renforcants |
|---|---|---|---|---|
| [[systeme_economique_redistribution]] | 11 | 0.68 | 3 | 6 |
| [[gouvernance_institutions]] | 11 | 0.66 | 1 | 6 |
| [[geopolitique_conflits]] | 11 | 0.76 | 6 | 4 |
| [[valeurs_culture_tempo_sociale]] | 11 | 0.55 | 0 | 7 |
| [[organisation_territoires]] | 11 | 0.7 | 3 | 7 |
| [[sante_biotechnologies]] | 11 | 0.54 | 0 | 5 |
| [[frontieres_du_systeme]] | 11 | 0.6 | 3 | 2 |
| [[technologie_information]] | 11 | 0.74 | 0 | 11 |
| [[climat_environnement_global]] | 11 | 0.62 | 8 | 1 |
| [[energie_ressources_critiques]] | 11 | 0.68 | 7 | 2 |
| [[demographie_mobilite_humaine]] | 11 | 0.7 | 3 | 7 |
| [[systemes_productifs_travail]] | 11 | 0.75 | 3 | 8 |

## Liens forts (weight ≥ 0.80 et temporal_weight ≥ 0.8)

| Source | Target | Weight | Polarity | Lag | Role |
|---|---|---|---|---|---|
| [[geopolitique_conflits]] | [[energie_ressources_critiques]] | 0.95 | − | 1 | cascade |
| [[energie_ressources_critiques]] | [[geopolitique_conflits]] | 0.95 | − | 1 | cascade |
| [[systeme_economique_redistribution]] | [[systemes_productifs_travail]] | 0.9 | + | 1 | reinforcing |
| [[gouvernance_institutions]] | [[geopolitique_conflits]] | 0.9 | − | 1 | cascade |
| [[gouvernance_institutions]] | [[technologie_information]] | 0.9 | + | 1 | reinforcing |
| [[geopolitique_conflits]] | [[gouvernance_institutions]] | 0.9 | − | 1 | reinforcing |
| [[technologie_information]] | [[gouvernance_institutions]] | 0.9 | + | 1 | reinforcing |
| [[technologie_information]] | [[systemes_productifs_travail]] | 0.9 | + | 1 | reinforcing |
| [[systemes_productifs_travail]] | [[systeme_economique_redistribution]] | 0.9 | + | 1 | reinforcing |
| [[systemes_productifs_travail]] | [[technologie_information]] | 0.9 | + | 1 | reinforcing |
| [[systeme_economique_redistribution]] | [[technologie_information]] | 0.85 | + | 1 | reinforcing |
| [[systeme_economique_redistribution]] | [[energie_ressources_critiques]] | 0.85 | − | 1 | cascade |
| [[geopolitique_conflits]] | [[organisation_territoires]] | 0.85 | − | 1 | cascade |
| [[geopolitique_conflits]] | [[technologie_information]] | 0.85 | + | 1 | reinforcing |
| [[organisation_territoires]] | [[geopolitique_conflits]] | 0.85 | − | 1 | cascade |
| [[technologie_information]] | [[systeme_economique_redistribution]] | 0.85 | + | 1 | reinforcing |
| [[technologie_information]] | [[geopolitique_conflits]] | 0.85 | + | 1 | reinforcing |
| [[energie_ressources_critiques]] | [[systeme_economique_redistribution]] | 0.85 | − | 1 | cascade |
| [[energie_ressources_critiques]] | [[systemes_productifs_travail]] | 0.85 | − | 1 | cascade |
| [[systemes_productifs_travail]] | [[energie_ressources_critiques]] | 0.85 | − | 1 | cascade |
| [[geopolitique_conflits]] | [[frontieres_du_systeme]] | 0.8 | − | 2 | cascade |
| [[frontieres_du_systeme]] | [[geopolitique_conflits]] | 0.8 | − | 2 | cascade |
| [[climat_environnement_global]] | [[demographie_mobilite_humaine]] | 0.8 | − | 3 | cascade |
| [[demographie_mobilite_humaine]] | [[climat_environnement_global]] | 0.8 | − | 3 | cascade |

## Détail des edges par variable

### [[systeme_economique_redistribution]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[systemes_productifs_travail]] | 0.9 | + | 1 | high | 0.9 | reinforcing |
| [[technologie_information]] | 0.85 | + | 1 | high | 1.0 | reinforcing |
| [[energie_ressources_critiques]] | 0.85 | − | 1 | high | 1.0 | cascade |
| [[gouvernance_institutions]] | 0.8 | + | 2 | medium | 0.7 | reinforcing |
| [[geopolitique_conflits]] | 0.75 | + | 1 | high | 0.9 | cascade |
| [[organisation_territoires]] | 0.65 | + | 2 | medium | 0.6 | reinforcing |
| [[demographie_mobilite_humaine]] | 0.65 | + | 3 | medium | 0.6 | reinforcing |
| [[climat_environnement_global]] | 0.6 | − | 4 | high | 0.7 | cascade |
| [[valeurs_culture_tempo_sociale]] | 0.55 | + | 3 | medium | 0.5 | reinforcing |
| [[frontieres_du_systeme]] | 0.5 | + | 2 | high | 0.7 | balancing |
| [[sante_biotechnologies]] | 0.4 | + | 3 | low | 0.4 | delayed |

### [[gouvernance_institutions]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[geopolitique_conflits]] | 0.9 | − | 1 | high | 1.0 | cascade |
| [[technologie_information]] | 0.9 | + | 1 | high | 1.0 | reinforcing |
| [[systeme_economique_redistribution]] | 0.8 | + | 2 | medium | 0.7 | reinforcing |
| [[organisation_territoires]] | 0.7 | + | 2 | medium | 0.6 | reinforcing |
| [[demographie_mobilite_humaine]] | 0.7 | + | 2 | medium | 0.6 | reinforcing |
| [[systemes_productifs_travail]] | 0.65 | + | 2 | medium | 0.6 | reinforcing |
| [[valeurs_culture_tempo_sociale]] | 0.6 | + | 3 | medium | 0.5 | reinforcing |
| [[sante_biotechnologies]] | 0.55 | + | 2 | medium | 0.5 | delayed |
| [[energie_ressources_critiques]] | 0.55 | + | 3 | medium | 0.5 | balancing |
| [[climat_environnement_global]] | 0.5 | + | 4 | medium | 0.6 | delayed |
| [[frontieres_du_systeme]] | 0.45 | + | 3 | high | 0.6 | balancing |

### [[geopolitique_conflits]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[energie_ressources_critiques]] | 0.95 | − | 1 | high | 1.0 | cascade |
| [[gouvernance_institutions]] | 0.9 | − | 1 | high | 1.0 | reinforcing |
| [[organisation_territoires]] | 0.85 | − | 1 | high | 0.9 | cascade |
| [[technologie_information]] | 0.85 | + | 1 | high | 1.0 | reinforcing |
| [[frontieres_du_systeme]] | 0.8 | − | 2 | high | 0.9 | cascade |
| [[systeme_economique_redistribution]] | 0.75 | − | 2 | high | 0.8 | cascade |
| [[demographie_mobilite_humaine]] | 0.75 | − | 2 | high | 0.8 | cascade |
| [[systemes_productifs_travail]] | 0.7 | − | 2 | medium | 0.7 | reinforcing |
| [[valeurs_culture_tempo_sociale]] | 0.65 | + | 3 | medium | 0.5 | reinforcing |
| [[climat_environnement_global]] | 0.65 | − | 4 | high | 0.7 | cascade |
| [[sante_biotechnologies]] | 0.5 | − | 3 | medium | 0.5 | delayed |

### [[valeurs_culture_tempo_sociale]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[technologie_information]] | 0.7 | + | 1 | high | 0.9 | reinforcing |
| [[demographie_mobilite_humaine]] | 0.7 | + | 2 | medium | 0.6 | reinforcing |
| [[gouvernance_institutions]] | 0.6 | + | 3 | medium | 0.5 | reinforcing |
| [[geopolitique_conflits]] | 0.6 | + | 3 | medium | 0.5 | reinforcing |
| [[systemes_productifs_travail]] | 0.6 | + | 2 | medium | 0.6 | reinforcing |
| [[systeme_economique_redistribution]] | 0.55 | + | 3 | medium | 0.5 | reinforcing |
| [[organisation_territoires]] | 0.55 | + | 2 | medium | 0.6 | reinforcing |
| [[sante_biotechnologies]] | 0.5 | + | 3 | low | 0.4 | delayed |
| [[frontieres_du_systeme]] | 0.45 | + | 3 | medium | 0.5 | balancing |
| [[climat_environnement_global]] | 0.4 | + | 4 | medium | 0.6 | delayed |
| [[energie_ressources_critiques]] | 0.4 | + | 3 | medium | 0.5 | balancing |

### [[organisation_territoires]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[geopolitique_conflits]] | 0.85 | − | 1 | high | 0.9 | cascade |
| [[systemes_productifs_travail]] | 0.8 | + | 1 | medium | 0.7 | reinforcing |
| [[technologie_information]] | 0.75 | + | 1 | high | 1.0 | reinforcing |
| [[demographie_mobilite_humaine]] | 0.75 | + | 2 | medium | 0.6 | reinforcing |
| [[gouvernance_institutions]] | 0.7 | + | 2 | medium | 0.6 | reinforcing |
| [[climat_environnement_global]] | 0.7 | − | 4 | high | 0.8 | cascade |
| [[energie_ressources_critiques]] | 0.7 | − | 2 | high | 0.8 | cascade |
| [[systeme_economique_redistribution]] | 0.65 | + | 2 | medium | 0.6 | reinforcing |
| [[sante_biotechnologies]] | 0.6 | + | 2 | medium | 0.5 | reinforcing |
| [[frontieres_du_systeme]] | 0.6 | − | 2 | high | 0.8 | balancing |
| [[valeurs_culture_tempo_sociale]] | 0.55 | + | 2 | medium | 0.6 | reinforcing |

### [[sante_biotechnologies]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[demographie_mobilite_humaine]] | 0.7 | + | 2 | medium | 0.6 | reinforcing |
| [[technologie_information]] | 0.65 | + | 1 | high | 0.9 | reinforcing |
| [[organisation_territoires]] | 0.6 | + | 2 | medium | 0.5 | reinforcing |
| [[systemes_productifs_travail]] | 0.6 | + | 2 | medium | 0.6 | reinforcing |
| [[gouvernance_institutions]] | 0.55 | + | 2 | medium | 0.5 | reinforcing |
| [[geopolitique_conflits]] | 0.5 | − | 3 | medium | 0.5 | delayed |
| [[valeurs_culture_tempo_sociale]] | 0.5 | + | 3 | low | 0.4 | delayed |
| [[frontieres_du_systeme]] | 0.5 | + | 3 | high | 0.7 | balancing |
| [[climat_environnement_global]] | 0.5 | + | 4 | medium | 0.6 | delayed |
| [[energie_ressources_critiques]] | 0.45 | + | 3 | medium | 0.5 | balancing |
| [[systeme_economique_redistribution]] | 0.4 | + | 3 | low | 0.4 | delayed |

### [[frontieres_du_systeme]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[geopolitique_conflits]] | 0.8 | − | 2 | high | 0.9 | cascade |
| [[climat_environnement_global]] | 0.75 | − | 4 | high | 0.8 | cascade |
| [[energie_ressources_critiques]] | 0.7 | − | 2 | high | 0.9 | cascade |
| [[systemes_productifs_travail]] | 0.65 | + | 2 | medium | 0.7 | reinforcing |
| [[organisation_territoires]] | 0.6 | − | 2 | high | 0.8 | balancing |
| [[technologie_information]] | 0.6 | + | 2 | high | 0.9 | reinforcing |
| [[demographie_mobilite_humaine]] | 0.55 | + | 3 | medium | 0.6 | balancing |
| [[systeme_economique_redistribution]] | 0.5 | + | 2 | high | 0.7 | balancing |
| [[sante_biotechnologies]] | 0.5 | + | 3 | high | 0.7 | balancing |
| [[gouvernance_institutions]] | 0.45 | + | 3 | high | 0.6 | balancing |
| [[valeurs_culture_tempo_sociale]] | 0.45 | + | 3 | medium | 0.5 | balancing |

### [[technologie_information]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[gouvernance_institutions]] | 0.9 | + | 1 | high | 1.0 | reinforcing |
| [[systemes_productifs_travail]] | 0.9 | + | 1 | high | 1.0 | reinforcing |
| [[systeme_economique_redistribution]] | 0.85 | + | 1 | high | 1.0 | reinforcing |
| [[geopolitique_conflits]] | 0.85 | + | 1 | high | 1.0 | reinforcing |
| [[organisation_territoires]] | 0.75 | + | 1 | high | 1.0 | reinforcing |
| [[valeurs_culture_tempo_sociale]] | 0.7 | + | 1 | high | 0.9 | reinforcing |
| [[energie_ressources_critiques]] | 0.7 | + | 2 | high | 0.9 | reinforcing |
| [[sante_biotechnologies]] | 0.65 | + | 1 | high | 0.9 | reinforcing |
| [[demographie_mobilite_humaine]] | 0.65 | + | 2 | medium | 0.6 | reinforcing |
| [[frontieres_du_systeme]] | 0.6 | + | 2 | high | 0.9 | reinforcing |
| [[climat_environnement_global]] | 0.55 | + | 3 | high | 0.8 | reinforcing |

### [[climat_environnement_global]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[demographie_mobilite_humaine]] | 0.8 | − | 3 | high | 0.8 | cascade |
| [[frontieres_du_systeme]] | 0.75 | − | 4 | high | 0.8 | cascade |
| [[systemes_productifs_travail]] | 0.75 | − | 2 | high | 0.8 | cascade |
| [[organisation_territoires]] | 0.7 | − | 4 | high | 0.8 | cascade |
| [[geopolitique_conflits]] | 0.65 | − | 4 | high | 0.8 | cascade |
| [[systeme_economique_redistribution]] | 0.6 | − | 4 | high | 0.7 | cascade |
| [[energie_ressources_critiques]] | 0.6 | − | 2 | high | 0.9 | cascade |
| [[technologie_information]] | 0.55 | + | 3 | high | 0.8 | reinforcing |
| [[gouvernance_institutions]] | 0.5 | + | 4 | medium | 0.6 | delayed |
| [[sante_biotechnologies]] | 0.5 | − | 4 | medium | 0.6 | cascade |
| [[valeurs_culture_tempo_sociale]] | 0.4 | + | 4 | medium | 0.6 | delayed |

### [[energie_ressources_critiques]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[geopolitique_conflits]] | 0.95 | − | 1 | high | 1.0 | cascade |
| [[systeme_economique_redistribution]] | 0.85 | − | 1 | high | 1.0 | cascade |
| [[systemes_productifs_travail]] | 0.85 | − | 1 | high | 0.9 | cascade |
| [[organisation_territoires]] | 0.7 | − | 2 | high | 0.8 | cascade |
| [[frontieres_du_systeme]] | 0.7 | − | 2 | high | 0.9 | cascade |
| [[technologie_information]] | 0.7 | + | 2 | high | 0.9 | reinforcing |
| [[demographie_mobilite_humaine]] | 0.7 | − | 2 | high | 0.8 | cascade |
| [[climat_environnement_global]] | 0.6 | − | 2 | high | 0.9 | cascade |
| [[gouvernance_institutions]] | 0.55 | + | 2 | medium | 0.6 | reinforcing |
| [[sante_biotechnologies]] | 0.45 | + | 3 | medium | 0.5 | balancing |
| [[valeurs_culture_tempo_sociale]] | 0.4 | + | 3 | medium | 0.5 | balancing |

### [[demographie_mobilite_humaine]]

| Target | Weight | Polarity | Lag | Nonlinearity | Temporal | Role |
|---|---|---|---|---|---|---|
| [[climat_environnement_global]] | 0.8 | − | 3 | high | 0.8 | cascade |
| [[systemes_productifs_travail]] | 0.8 | + | 2 | medium | 0.7 | reinforcing |
| [[geopolitique_conflits]] | 0.75 | − | 2 | high | 0.8 | cascade |
| [[organisation_territoires]] | 0.75 | + | 2 | medium | 0.6 | reinforcing |
| [[gouvernance_institutions]] | 0.7 | + | 2 | medium | 0.6 | reinforcing |
| [[valeurs_culture_tempo_sociale]] | 0.7 | + | 2 | medium | 0.6 | reinforcing |
| [[sante_biotechnologies]] | 0.7 | + | 2 | medium | 0.6 | reinforcing |
| [[energie_ressources_critiques]] | 0.7 | − | 2 | high | 0.8 | cascade |
| [[systeme_economique_redistribution]] | 0.65 | + | 3 | medium | 0.6 | reinforcing |
| [[technologie_information]] | 0.65 | + | 2 | medium | 0.6 | reinforcing |
| [[frontieres_du_systeme]] | 0.55 | + | 3 | medium | 0.6 | balancing |

### [[systemes_productifs_travail]]

| Target                                | Weight | Polarity | Lag | Nonlinearity | Temporal | Role        |
| ------------------------------------- | ------ | -------- | --- | ------------ | -------- | ----------- |
| [[systeme_economique_redistribution]] | 0.9    | +        | 1   | high         | 0.9      | reinforcing |
| [[technologie_information]]           | 0.9    | +        | 1   | high         | 1.0      | reinforcing |
| [[energie_ressources_critiques]]      | 0.85   | −        | 1   | high         | 0.9      | cascade     |
| [[organisation_territoires]]          | 0.8    | +        | 1   | medium       | 0.7      | reinforcing |
| [[demographie_mobilite_humaine]]      | 0.8    | +        | 2   | medium       | 0.7      | reinforcing |
| [[climat_environnement_global]]       | 0.75   | −        | 2   | high         | 0.8      | cascade     |
| [[geopolitique_conflits]]             | 0.7    | −        | 2   | medium       | 0.7      | cascade     |
| [[gouvernance_institutions]]          | 0.65   | +        | 2   | medium       | 0.6      | reinforcing |
| [[frontieres_du_systeme]]             | 0.65   | +        | 2   | medium       | 0.7      | reinforcing |
| [[valeurs_culture_tempo_sociale]]     | 0.6    | +        | 2   | medium       | 0.6      | reinforcing |
| [[sante_biotechnologies]]             | 0.6    | +        | 2   | medium       | 0.6      | reinforcing |
|                                       |        |          |     |              |          |             |
