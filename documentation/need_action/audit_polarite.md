# Audit polarité des impacts sur variables

Entrées analysées : 511

## Répartition

- **A** delta < 0 et polarite -1 -> effet POSITIF (double négatif, suspect) : 141 (instance 52, événement 89)
- **B** delta < 0 et polarite +1 -> effet négatif (signe dans delta) : 0
- **C** delta > 0 et polarite -1 -> effet négatif (signe dans polarite) : 121 (instance 14, signal 6, événement 101)
- **D** delta > 0 et polarite +1 -> effet positif : 249 (instance 124, signal 12, événement 113)
- **Z** delta = 0 -> aucun effet : 0

## Cas A — double négatif (141)

| Source | Fichier | Scénario | Variable | delta | polarite | Effet appliqué | Note |
|---|---|---|---|---|---|---|---|
| instance | alpha47_fortress_world.md | fortress_world | systemes_productifs_travail | -8 | -1 | +8 |  |
| instance | anton_vasko_fortress_world.md | fortress_world | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | aurelio_stahl_reference.md | reference | technologie_information | -10 | -1 | +10 |  |
| instance | aymeric_de_valfort_fortress_world.md | fortress_world | geopolitique_conflits | -8 | -1 | +8 |  |
| instance | deepfield_institute_breakdown.md | breakdown | demographie_mobilite_humaine | -8 | -1 | +8 |  |
| instance | deepfield_institute_breakdown.md | breakdown | gouvernance_institutions | -10 | -1 | +10 |  |
| instance | deepfield_institute_breakdown.md | breakdown | sante_biotechnologies | -5 | -1 | +5 |  |
| instance | deepfield_institute_new_sustainability.md | new_sustainability | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | deepfield_institute_reference.md | reference | demographie_mobilite_humaine | -10 | -1 | +10 |  |
| instance | deepfield_institute_reference.md | reference | gouvernance_institutions | -8 | -1 | +8 |  |
| instance | elias_mork_reference.md | reference | gouvernance_institutions | -10 | -1 | +10 |  |
| instance | ergo_wian_sovereign_holdings_breakdown.md | breakdown | gouvernance_institutions | -6 | -1 | +6 |  |
| instance | ergo_wian_sovereign_holdings_breakdown.md | breakdown | organisation_territoires | -5 | -1 | +5 |  |
| instance | ergo_wian_sovereign_holdings_breakdown.md | breakdown | systeme_economique_redistribution | -8 | -1 | +8 |  |
| instance | ergo_wian_sovereign_holdings_eco_communalism.md | eco_communalism | gouvernance_institutions | -8 | -1 | +8 |  |
| instance | ergo_wian_sovereign_holdings_eco_communalism.md | eco_communalism | systeme_economique_redistribution | -5 | -1 | +5 |  |
| instance | ergo_wian_sovereign_holdings_policy_reform.md | policy_reform | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | ergo_wian_sovereign_holdings_policy_reform.md | policy_reform | systeme_economique_redistribution | -8 | -1 | +8 |  |
| instance | ergo_wian_sovereign_holdings_reference.md | reference | gouvernance_institutions | -15 | -1 | +15 |  |
| instance | ergo_wian_sovereign_holdings_reference.md | reference | systeme_economique_redistribution | -12 | -1 | +12 |  |
| instance | guilhelma_fortress_world.md | fortress_world | geopolitique_conflits | -5 | -1 | +5 |  |
| instance | holdfast_breakdown.md | breakdown | gouvernance_institutions | -3 | -1 | +3 |  |
| instance | holdfast_breakdown.md | breakdown | organisation_territoires | -5 | -1 | +5 |  |
| instance | holdfast_fortress_world.md | fortress_world | gouvernance_institutions | -3 | -1 | +3 |  |
| instance | holdfast_fortress_world.md | fortress_world | organisation_territoires | -5 | -1 | +5 |  |
| instance | holdfast_new_sustainability.md | new_sustainability | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | holdfast_reference.md | reference | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | holdfast_reference.md | reference | systeme_economique_redistribution | -8 | -1 | +8 |  |
| instance | hyphan_raghavan_new_sustainability.md | new_sustainability | gouvernance_institutions | -3 | -1 | +3 |  |
| instance | ilse_varga_holm_breakdown.md | breakdown | geopolitique_conflits | -5 | -1 | +5 |  |
| instance | ilse_varga_holm_eco_communalism.md | eco_communalism | energie_ressources_critiques | -5 | -1 | +5 |  |
| instance | ilse_varga_holm_fortress_world.md | fortress_world | geopolitique_conflits | -5 | -1 | +5 |  |
| instance | kaspar_lind_reference.md | reference | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | kaspar_lind_reference.md | reference | technologie_information | -3 | -1 | +3 |  |
| instance | kindling_eco_communalism.md | eco_communalism | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | kindling_eco_communalism.md | eco_communalism | technologie_information | -3 | -1 | +3 |  |
| instance | kindling_reference.md | reference | gouvernance_institutions | -6 | -1 | +6 |  |
| instance | kindling_reference.md | reference | technologie_information | -8 | -1 | +8 |  |
| instance | la_garde_du_seuil_fortress_world.md | fortress_world | valeurs_culture_tempo_sociale | -5 | -1 | +5 |  |
| instance | les_dedoubles_fortress_world.md | fortress_world | geopolitique_conflits | -5 | -1 | +5 |  |
| instance | les_dedoubles_fortress_world.md | fortress_world | gouvernance_institutions | -6 | -1 | +6 |  |
| instance | maelys_okonkwo_policy_reform.md | policy_reform | gouvernance_institutions | -8 | -1 | +8 |  |
| instance | meridian_assembly_breakdown.md | breakdown | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | meridian_assembly_breakdown.md | breakdown | technologie_information | -3 | -1 | +3 |  |
| instance | mouvement_de_reconquete_europeenne_fortress_world.md | fortress_world | demographie_mobilite_humaine | -10 | -1 | +10 |  |
| instance | nadia_ferreira_sato_new_sustainability.md | new_sustainability | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | raimon_fortress_world.md | fortress_world | organisation_territoires | -5 | -1 | +5 |  |
| instance | raised_hands_breakdown.md | breakdown | gouvernance_institutions | -3 | -1 | +3 |  |
| instance | the_lattice_policy_reform.md | policy_reform | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | the_tidewater_canon_eco_communalism.md | eco_communalism | gouvernance_institutions | -5 | -1 | +5 |  |
| instance | the_tidewater_canon_reference.md | reference | gouvernance_institutions | -15 | -1 | +15 |  |
| instance | the_tidewater_canon_reference.md | reference | systeme_economique_redistribution | -12 | -1 | +12 |  |
| événement | accord_carbone_amazonie_blocs_new_sustainability.md | new_sustainability | geopolitique_conflits | -6 | -1 | +6 |  |
| événement | accord_carbone_amazonie_blocs_policy_reform.md | policy_reform | energie_ressources_critiques | -5 | -1 | +5 |  |
| événement | accord_carbone_amazonie_blocs_policy_reform.md | policy_reform | geopolitique_conflits | -9 | -1 | +9 |  |
| événement | accord_carbone_amazonie_blocs_reference.md | reference | energie_ressources_critiques | -4 | -1 | +4 |  |
| événement | accord_carbone_amazonie_blocs_reference.md | reference | geopolitique_conflits | -7 | -1 | +7 |  |
| événement | communes_rust_belt_zones_libres_breakdown.md | breakdown | gouvernance_institutions | -7 | -1 | +7 |  |
| événement | communes_rust_belt_zones_libres_eco_communalism.md | eco_communalism | gouvernance_institutions | -10 | -1 | +10 |  |
| événement | communes_rust_belt_zones_libres_fortress_world.md | fortress_world | gouvernance_institutions | -7 | -1 | +7 |  |
| événement | conflit_israel_iran_2026_breakdown.md | breakdown | demographie_mobilite_humaine | -7 | -1 | +7 |  |
| événement | conflit_israel_iran_2026_breakdown.md | breakdown | energie_ressources_critiques | -8 | -1 | +8 |  |
| événement | conflit_israel_iran_2026_breakdown.md | breakdown | gouvernance_institutions | -5 | -1 | +5 |  |
| événement | conflit_israel_iran_2026_eco_communalism.md | eco_communalism | demographie_mobilite_humaine | -9 | -1 | +9 |  |
| événement | conflit_israel_iran_2026_eco_communalism.md | eco_communalism | energie_ressources_critiques | -12 | -1 | +12 |  |
| événement | conflit_israel_iran_2026_eco_communalism.md | eco_communalism | geopolitique_conflits | -8 | -1 | +8 |  |
| événement | conflit_israel_iran_2026_fortress_world.md | fortress_world | demographie_mobilite_humaine | -11 | -1 | +11 |  |
| événement | conflit_israel_iran_2026_fortress_world.md | fortress_world | energie_ressources_critiques | -14 | -1 | +14 |  |
| événement | conflit_israel_iran_2026_fortress_world.md | fortress_world | gouvernance_institutions | -8 | -1 | +8 |  |
| événement | conflit_israel_iran_2026_new_sustainability.md | new_sustainability | demographie_mobilite_humaine | -4 | -1 | +4 |  |
| événement | conflit_israel_iran_2026_new_sustainability.md | new_sustainability | energie_ressources_critiques | -10 | -1 | +10 |  |
| événement | conflit_israel_iran_2026_new_sustainability.md | new_sustainability | geopolitique_conflits | -8 | -1 | +8 |  |
| événement | conflit_israel_iran_2026_policy_reform.md | policy_reform | demographie_mobilite_humaine | -5 | -1 | +5 |  |
| événement | conflit_israel_iran_2026_policy_reform.md | policy_reform | energie_ressources_critiques | -10 | -1 | +10 |  |
| événement | conflit_israel_iran_2026_policy_reform.md | policy_reform | geopolitique_conflits | -8 | -1 | +8 |  |
| événement | conflit_israel_iran_2026_reference.md | reference | energie_ressources_critiques | -10 | -1 | +10 |  |
| événement | conflit_israel_iran_2026_reference.md | reference | gouvernance_institutions | -8 | -1 | +8 |  |
| événement | crise_gouvernance_amazonie_breakdown.md | breakdown | climat_environnement_global | -12 | -1 | +12 |  |
| événement | crise_gouvernance_amazonie_breakdown.md | breakdown | gouvernance_institutions | -8 | -1 | +8 |  |
| événement | crise_gouvernance_amazonie_breakdown.md | breakdown | organisation_territoires | -10 | -1 | +10 |  |
| événement | crise_gouvernance_amazonie_eco_communalism.md | eco_communalism | climat_environnement_global | -8 | -1 | +8 |  |
| événement | crise_gouvernance_amazonie_fortress_world.md | fortress_world | climat_environnement_global | -18 | -1 | +18 |  |
| événement | crise_gouvernance_amazonie_fortress_world.md | fortress_world | gouvernance_institutions | -12 | -1 | +12 |  |
| événement | crise_gouvernance_amazonie_fortress_world.md | fortress_world | organisation_territoires | -10 | -1 | +10 |  |
| événement | crise_gouvernance_amazonie_new_sustainability.md | new_sustainability | climat_environnement_global | -4 | -1 | +4 |  |
| événement | crise_gouvernance_amazonie_policy_reform.md | policy_reform | climat_environnement_global | -8 | -1 | +8 |  |
| événement | crise_gouvernance_amazonie_reference.md | reference | climat_environnement_global | -8 | -1 | +8 |  |
| événement | crise_gouvernance_amazonie_reference.md | reference | gouvernance_institutions | -7 | -1 | +7 |  |
| événement | crise_gouvernance_amazonie_reference.md | reference | organisation_territoires | -6 | -1 | +6 |  |
| événement | crue_exceptionnelle_congo_eco_communalism.md | eco_communalism | climat_environnement_global | -5 | -1 | +5 |  |
| événement | crue_exceptionnelle_congo_eco_communalism.md | eco_communalism | demographie_mobilite_humaine | -15 | -1 | +15 |  |
| événement | emeutes_algorithme_sao_paulo_breakdown.md | breakdown | gouvernance_institutions | -8 | -1 | +8 |  |
| événement | emeutes_algorithme_sao_paulo_breakdown.md | breakdown | organisation_territoires | -10 | -1 | +10 |  |
| événement | emeutes_algorithme_sao_paulo_fortress_world.md | fortress_world | gouvernance_institutions | -12 | -1 | +12 |  |
| événement | emeutes_algorithme_sao_paulo_fortress_world.md | fortress_world | organisation_territoires | -10 | -1 | +10 |  |
| événement | emeutes_algorithme_sao_paulo_fortress_world.md | fortress_world | technologie_information | -8 | -1 | +8 |  |
| événement | emeutes_algorithme_sao_paulo_policy_reform.md | policy_reform | technologie_information | -10 | -1 | +10 |  |
| événement | emeutes_algorithme_sao_paulo_reference.md | reference | gouvernance_institutions | -8 | -1 | +8 |  |
| événement | encheres_terres_rares_groenland_breakdown.md | breakdown | energie_ressources_critiques | -8 | -1 | +8 |  |
| événement | encheres_terres_rares_groenland_breakdown.md | breakdown | gouvernance_institutions | -10 | -1 | +10 |  |
| événement | encheres_terres_rares_groenland_breakdown.md | breakdown | organisation_territoires | -7 | -1 | +7 |  |
| événement | encheres_terres_rares_groenland_eco_communalism.md | eco_communalism | energie_ressources_critiques | -8 | -1 | +8 |  |
| événement | encheres_terres_rares_groenland_eco_communalism.md | eco_communalism | gouvernance_institutions | -7 | -1 | +7 |  |
| événement | encheres_terres_rares_groenland_fortress_world.md | fortress_world | gouvernance_institutions | -12 | -1 | +12 |  |
| événement | encheres_terres_rares_groenland_policy_reform.md | policy_reform | geopolitique_conflits | -8 | -1 | +8 |  |
| événement | exode_midwest_grands_lacs_breakdown.md | breakdown | energie_ressources_critiques | -10 | -1 | +10 |  |
| événement | exode_midwest_grands_lacs_breakdown.md | breakdown | gouvernance_institutions | -12 | -1 | +12 |  |
| événement | exode_midwest_grands_lacs_breakdown.md | breakdown | organisation_territoires | -15 | -1 | +15 |  |
| événement | exode_midwest_grands_lacs_eco_communalism.md | eco_communalism | climat_environnement_global | -8 | -1 | +8 |  |
| événement | exode_midwest_grands_lacs_eco_communalism.md | eco_communalism | energie_ressources_critiques | -10 | -1 | +10 |  |
| événement | exode_midwest_grands_lacs_eco_communalism.md | eco_communalism | gouvernance_institutions | -12 | -1 | +12 |  |
| événement | exode_midwest_grands_lacs_fortress_world.md | fortress_world | gouvernance_institutions | -10 | -1 | +10 |  |
| événement | exode_midwest_grands_lacs_fortress_world.md | fortress_world | organisation_territoires | -14 | -1 | +14 |  |
| événement | exode_midwest_grands_lacs_new_sustainability.md | new_sustainability | climat_environnement_global | -3 | -1 | +3 |  |
| événement | exode_midwest_grands_lacs_policy_reform.md | policy_reform | climat_environnement_global | -8 | -1 | +8 |  |
| événement | exode_midwest_grands_lacs_policy_reform.md | policy_reform | organisation_territoires | -10 | -1 | +10 |  |
| événement | exode_midwest_grands_lacs_reference.md | reference | climat_environnement_global | -5 | -1 | +5 |  |
| événement | exode_midwest_grands_lacs_reference.md | reference | demographie_mobilite_humaine | -12 | -1 | +12 |  |
| événement | exode_midwest_grands_lacs_reference.md | reference | gouvernance_institutions | -8 | -1 | +8 |  |
| événement | exode_midwest_grands_lacs_reference.md | reference | organisation_territoires | -10 | -1 | +10 |  |
| événement | grand_forum_sahel_numerique_breakdown.md | breakdown | gouvernance_institutions | -8 | -1 | +8 |  |
| événement | grand_forum_sahel_numerique_breakdown.md | breakdown | organisation_territoires | -6 | -1 | +6 |  |
| événement | ils_ont_noye_les_archives_a_milwaukee_basse_le_reg_breakdown.md | breakdown | technologie_information | -20 | -1 | +20 |  |
| événement | incident_passage_arctique_breakdown.md | breakdown | climat_environnement_global | -4 | -1 | +4 |  |
| événement | incident_passage_arctique_breakdown.md | breakdown | energie_ressources_critiques | -10 | -1 | +10 |  |
| événement | incident_passage_arctique_breakdown.md | breakdown | frontieres_du_systeme | -6 | -1 | +6 |  |
| événement | incident_passage_arctique_breakdown.md | breakdown | organisation_territoires | -7 | -1 | +7 |  |
| événement | incident_passage_arctique_policy_reform.md | policy_reform | energie_ressources_critiques | -8 | -1 | +8 |  |
| événement | incident_passage_arctique_reference.md | reference | energie_ressources_critiques | -8 | -1 | +8 |  |
| événement | insurrection_rust_belt_breakdown.md | breakdown | gouvernance_institutions | -10 | -1 | +10 |  |
| événement | insurrection_rust_belt_breakdown.md | breakdown | technologie_information | -6 | -1 | +6 |  |
| événement | insurrection_rust_belt_eco_communalism.md | eco_communalism | gouvernance_institutions | -10 | -1 | +10 |  |
| événement | insurrection_rust_belt_fortress_world.md | fortress_world | gouvernance_institutions | -10 | -1 | +10 |  |
| événement | nairobi_biorevenu_pilote_2094_reference.md | reference | systemes_productifs_travail | -6 | -1 | +6 |  |
| événement | nairobi_biorevenu_pilote_2094_reference.md | reference | valeurs_culture_tempo_sociale | -7 | -1 | +7 |  |
| événement | secession_great_lakes_compact_breakdown.md | breakdown | gouvernance_institutions | -10 | -1 | +10 |  |
| événement | secession_great_lakes_compact_fortress_world.md | fortress_world | gouvernance_institutions | -14 | -1 | +14 |  |
| événement | secession_great_lakes_compact_new_sustainability.md | new_sustainability | geopolitique_conflits | -5 | -1 | +5 |  |
| événement | secession_great_lakes_compact_reference.md | reference | gouvernance_institutions | -14 | -1 | +14 |  |
| événement | submersion_tuvalu_acte_fondateur_new_sustainability.md | new_sustainability | climat_environnement_global | -3 | -1 | +3 |  |
| événement | submersion_tuvalu_acte_fondateur_policy_reform.md | policy_reform | organisation_territoires | -10 | -1 | +10 |  |

## Fichiers utilisant les deux conventions B et C (0)

Le signe est porté tantôt par delta, tantôt par polarite dans une même fiche.

Aucun.
