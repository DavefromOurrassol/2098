# Registre des événements (signal_to_state + événements custom)

Généré automatiquement — liste tous les `evenement_cle` (signaux) et
toutes les instances d'événements custom existants, par scénario,
triés chronologiquement, pour éviter les collisions de noms/dates/lieux
lors de l'ajout de nouveaux signaux (section 7 → 12) ou de nouveaux
événements custom (evenements/ + event_instances/).

RÈGLE DE LECTURE DE LA COLONNE "date" :
  - type=signal    -> fenêtre "AAAA-AAAA" (date_bascule du signal_to_state)
  - type=evenement -> année unique "AAAA" (date précise de l'instance)

Total : 403 entrées (60 signaux uniques × 6 scénarios + 43 entrées d'événements custom).

## breakdown

| type      | date      | source                                    | variable(s)                                                                                                 | pilote | evenement_cle                                                                |
| --------- | --------- | ----------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------- |
| evenement | 2027 | conflit_israel_iran_2026 | geopolitique_conflits, energie_ressources_critiques, gouvernance_institutions, demographie_mobilite_humaine | — | frappes israéliennes détruisent les puits iraniens 2027 |
| signal | 2035-2055 | emergence_pathogenes_nouveaux | sante_biotechnologies | non | Pandémie H7X de 2043 et effondrement de l'OMS |
| signal | 2036-2055 | robotisation_services | systemes_productifs_travail | oui | réquisition massive des robots de service dans les mégapoles 2050 |
| signal | 2037-2057 | disparition_metiers_intermediaires | systemes_productifs_travail | oui | fermeture de la dernière grande filière de formation intermédiaire 2049 |
| signal | 2038-2056 | automatisation_cognitive | systemes_productifs_travail | oui | chômage structurel à 45% dans les économies avancées 2049 |
| signal | 2038-2056 | discours_effondrement_climatique | climat_environnement_global | oui | manifeste collapsologue mondial diffusé après le Jour Sans Signal 2041 |
| signal | 2038-2056 | explosion_inegalites_patrimoniales | systeme_economique_redistribution | non | rapport confirmant une concentration record du patrimoine mondial 2051 |
| signal | 2038-2057 | guerres_culturelles_transnationales | valeurs_culture_tempo_sociale | non | premiers affrontements identitaires transfrontaliers coordonnés 2049 |
| signal | 2039-2057 | megafeux_saisonniers | climat_environnement_global | oui | perte totale des forêts méditerranéennes lors des feux de 2050 |
| signal | 2039-2058 | systemes_decision_automatises_publics | gouvernance_institutions | non | panne systémique des administrations automatisées pendant trois mois 2051 |
| signal | 2039-2057 | taxation_carbone_globale | systeme_economique_redistribution | non | suspension générale des mécanismes de taxation carbone 2050 |
| signal | 2039-2058 | agents_autonomes_multi_ia | technologie_information | non | incident majeur d'agents IA non coordonnés dans la finance 2050 |
| signal | 2039-2058 | desynchronisation_generationnelle | valeurs_culture_tempo_sociale | non | premières émeutes intergénérationnelles documentées dans les mégapoles 2050 |
| signal | 2040-2058 | militarisation_du_cyberespace | geopolitique_conflits | oui | effondrement des protocoles de non-agression numérique 2049 |
| signal | 2040-2058 | hybridation_ia_culture | valeurs_culture_tempo_sociale | non | prolifération non contrôlée des IA génératives culturelles |
| signal | 2040-2058 | fusion_experimentale | energie_ressources_critiques | oui | effondrement des consortiums de recherche fusion 2051 |
| signal | 2040-2058 | vieillissement_demographique | demographie_mobilite_humaine | non | faillite des systèmes de retraite des pays développés 2050 |
| signal | 2040-2058 | fragmentation_chaines_valeur | systemes_productifs_travail | oui | rupture simultanée de 60% des chaînes d'approvisionnement 2051 |
| signal | 2040-2059 | politiques_migratoires_restrictives | demographie_mobilite_humaine | non | fermeture simultanée de douze frontières majeures 2052 |
| signal | 2040-2059 | crise_confiance_institutions | gouvernance_institutions | non | boycott massif des dernières élections nationales organisées 2052 |
| signal | 2040-2059 | villes_intelligentes_autonomes | organisation_territoires | oui | extinction simultanée des réseaux intelligents de trois mégapoles 2054 |
| signal | 2040-2058 | remise_en_cause_capitalisme_croissance | systeme_economique_redistribution | non | dernier sommet économique mondial centré sur la croissance 2052 |
| signal | 2040-2059 | consommation_energetique_ia | technologie_information | non | fermeture en cascade des centres de données surconsommateurs 2051 |
| signal | 2041-2055 | automatisation_financière_algorithmique | systeme_economique_redistribution | non | effondrement des protocoles de régulation des IA financières |
| signal | 2041-2058 | gouvernance_algorithmique_emergente | gouvernance_institutions | non | effondrement des protocoles de régulation IA institutionnelle |
| signal | 2041-2060 | instabilite_saisonniere | climat_environnement_global | oui | franchissement de cinq points de basculement simultanés 2053 |
| signal | 2041-2060 | outils_predictifs_migratoires | demographie_mobilite_humaine | non | piratage des bases prédictives migratoires de l'Alliance Pacifique 2054 |
| signal | 2041-2059 | ia_militaire_autonome | geopolitique_conflits | oui | premier incident de frappe autonome non autorisée 2052 |
| signal | 2041-2060 | normalisation_conflit_hybride | geopolitique_conflits | oui | abandon officiel de la distinction entre paix et guerre 2053 |
| signal | 2041-2059 | stockage_energie_nouvelle_generation | energie_ressources_critiques | oui | pillage des dépôts de batteries stratégiques à Detroit-Sud 2053 |
| signal | 2041-2060 | acceptation_transition_contrainte | energie_ressources_critiques | oui | discours officiel reconnaissant l'impossibilité du retour à l'abondance 2053 |
| signal | 2041-2060 | transformation_attentes_democratiques | gouvernance_institutions | non | dernière élection nationale considérée comme légitime par l'opinion 2052 |
| signal | 2041-2060 | recomposition_centres_economiques | organisation_territoires | oui | fermeture définitive de la bourse de Lagos-Mumbai-Jakarta 2053 |
| signal | 2041-2059 | automatisation_agricole_massive | systemes_productifs_travail | oui | pannes simultanées des fermes automatisées de trois continents 2052 |
| signal | 2041-2060 | crise_verite_informationnelle | technologie_information | non | abandon officiel de toute vérité factuelle commune 2052 |
| signal | 2041-2059 | acceleration_rythmes_vie_urbains | valeurs_culture_tempo_sociale | non | abolition de facto des horaires sociaux dans les mégapoles 2052 |
| evenement | 2041 | encheres_terres_rares_groenland | energie_ressources_critiques, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | Enchères Groenland déchirent l'ordre mondial 2041 |
| signal | 2042-2058 | tensions_sur_terres_rares | geopolitique_conflits | oui | guerre des minerais d'Afrique centrale 2051 |
| signal | 2042-2060 | inegalites_acces_soins | sante_biotechnologies | non | collapse des mutuelles et assurances santé globales |
| signal | 2042-2059 | concentration_informationnelle | technologie_information | non | collapse du duopole numérique mondial 2051 |
| signal | 2042-2060 | competition_terres_rares | energie_ressources_critiques | oui | guerre des lithium-cobalt en Afrique australe 2052 |
| signal | 2042-2062 | migrations_climatiques | demographie_mobilite_humaine | non | exode climatique de 400 millions de personnes 2055 |
| signal | 2042-2061 | captation_carbone_industrielle | climat_environnement_global | oui | sabotage des installations de capture carbone du Sahara 2055 |
| signal | 2042-2061 | gestion_algorithmique_flux_humains | demographie_mobilite_humaine | non | panne généralisée des systèmes de tri migratoire automatisés 2052 |
| signal | 2042-2060 | militarisation_societes | geopolitique_conflits | oui | instauration de la conscription générale dans les zones de conflit 2053 |
| signal | 2042-2061 | adaptation_sobriete_energetique | energie_ressources_critiques | oui | émeutes de l'énergie dans les mégapoles surpeuplées 2054 |
| signal | 2042-2060 | industrialisation_orbitale_privee | frontieres_du_systeme | non | faillite en chaîne des stations industrielles orbitales privées 2052 |
| signal | 2042-2060 | gouvernance_environnementale_multiniveaux | gouvernance_institutions | non | dissolution du dernier organe mondial de coordination climatique 2053 |
| signal | 2042-2061 | declin_rural_accelere | organisation_territoires | oui | abandon officiel de mille communes rurales 2052 |
| signal | 2042-2060 | economie_plateformes_dominante | systeme_economique_redistribution | non | panne en cascade des grandes plateformes économiques mondiales 2051 |
| signal | 2042-2060 | normalisation_post_travail | systemes_productifs_travail | oui | retour massif au travail de subsistance non rémunéré 2050 |
| signal | 2043-2062 | fatigue_civilisationnelle | valeurs_culture_tempo_sociale | non | mouvement de décrochage sociétal global |
| signal | 2043-2062 | stress_territorial_climatique | organisation_territoires | oui | abandon de cinq mégapoles côtières majeures 2055 |
| signal | 2043-2063 | spatialisation_des_conflits | frontieres_du_systeme | non | premier conflit armé orbital 2055 |
| signal | 2043-2062 | dependance_numerique | technologie_information | non | blackout numérique global de 72 heures 2053 |
| signal | 2043-2062 | stress_hydrique | climat_environnement_global | oui | conflits armés pour les bassins versants 2054 |
| signal | 2043-2062 | debats_identitaires_migrations | demographie_mobilite_humaine | non | vague de pogroms anti-migrants dans les enclaves urbaines 2056 |
| signal | 2043-2061 | conflits_climatiques_armes | geopolitique_conflits | oui | première guerre officiellement qualifiée de climatique à Carthage-Nord 2055 |
| signal | 2043-2062 | degradation_sites_miniers | energie_ressources_critiques | oui | catastrophe de contamination des mines de lithium d'Afrique australe 2056 |
| signal | 2043-2060 | montee_localisme | organisation_territoires | oui | fermeture des frontières communales dans les zones de conflit 2053 |
| signal | 2044-2062 | fragmentation_institutionnelle_regionale | gouvernance_institutions | non | dissolution de facto des Nations Unies 2055 |
| signal | 2044-2063 | megapoles_sous_pression | organisation_territoires | oui | crise urbaine de Lagos-Mumbai-Jakarta 2056 |
| signal | 2044-2063 | relocalisation_cotiere | climat_environnement_global | oui | évacuation forcée de Lagos-Est sous tension armée 2057 |
| signal | 2044-2063 | minage_asteroides | frontieres_du_systeme | non | attaque sur une plateforme de minage d'astéroïdes 2057 |
| signal | 2044-2062 | retour_recit_civilisationnel_spatial | frontieres_du_systeme | non | dernière retransmission publique d'une mission spatiale civile 2056 |
| signal | 2044-2063 | automatisation_decisionnelle | technologie_information | non | sabotage massif des systèmes décisionnels automatisés critiques 2055 |
| signal | 2044-2063 | retour_spiritualites_hybrides | valeurs_culture_tempo_sociale | non | émergence de cultes de survie dans les zones effondrées 2055 |
| evenement | 2044 | exode_midwest_grands_lacs | demographie_mobilite_humaine, organisation_territoires, gouvernance_institutions, climat_environnement_global | — | 18 millions de déplacés déferlent sur les Grands Lacs, 2044 |
| signal | 2045-2065 | medecine_predictive_ia | sante_biotechnologies | non | fermeture des bases médicales prédictives de l'Alliance Pacifique 2058 |
| signal | 2045-2065 | saturation_orbitale | frontieres_du_systeme | non | catastrophe orbitale de 2057 bloquant l'accès spatial |
| signal | 2045-2064 | nouvelles_communautes_orbitales | frontieres_du_systeme | non | rupture de communication avec une station orbitale habitée 2058 |
| evenement | 2047 | crise_gouvernance_amazonie | climat_environnement_global, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | Belém en flammes, le bassin amazonien se fragmente, 2047 |
| signal | 2048-2062 | dedollarisation_progressive | systeme_economique_redistribution | non | abandon du dollar comme devise de réserve globale |
| signal | 2048-2068 | course_biotech_internationale | sante_biotechnologies | non | fuite de souches modifiées du complexe clandestin de Karaganda 2061 |
| signal | 2050-2070 | surveillance_sanitaire_continue | sante_biotechnologies | non | scandale des registres médicaux pillés de Detroit-Sud 2066 |
| signal | 2050-2070 | acceptation_homme_augmente | sante_biotechnologies | non | émeutes anti-augmentés dans les enclaves de Lagos-Est 2063 |
| evenement | 2053 | secession_great_lakes_compact | organisation_territoires, gouvernance_institutions, geopolitique_conflits | — | Chicago-Lacustre proclame le Compact souverain des eaux, 2053 |
| evenement | 2057 | incident_passage_arctique | geopolitique_conflits, frontieres_du_systeme, energie_ressources_critiques | — | Unités nordiques saisissent convoi arctique, 2057 |
| evenement | 2061 | communes_rust_belt_zones_libres | geopolitique_conflits, valeurs_culture_tempo_sociale, gouvernance_institutions, organisation_territoires | — | Rust Belt proclame zones libres algorithme, 2061 |
| evenement | 2061 | insurrection_rust_belt | geopolitique_conflits, valeurs_culture_tempo_sociale, gouvernance_institutions, technologie_information | — | Communes du Rust Belt proclament zones libres de l'algorithme, 2061 |
| evenement | 2061 | grand_forum_sahel_numerique | technologie_information, gouvernance_institutions, organisation_territoires | — | Forum d'Agadez fracturé, Charte disputée par les éclats, 2061 |
| evenement | 2073 | emeutes_algorithme_sao_paulo | gouvernance_institutions, technologie_information, organisation_territoires | — | São Paulo brise l'algorithme fantôme, 2073 |

## fortress_world

| type | date | source | variable(s) | pilote | evenement_cle |
|---|---|---|---|---|---|
| evenement | 2027 | conflit_israel_iran_2026 | geopolitique_conflits, energie_ressources_critiques, gouvernance_institutions, demographie_mobilite_humaine | — | frappes israéliennes sur les sites pétroliers iraniens 2027 |
| signal | 2033-2050 | robotisation_services | systemes_productifs_travail | oui | déploiement des robots de service dans les administrations des blocs 2046 |
| signal | 2034-2050 | automatisation_cognitive | systemes_productifs_travail | oui | déploiement des usines entièrement automatisées des blocs 2045 |
| signal | 2034-2051 | explosion_inegalites_patrimoniales | systeme_economique_redistribution | non | instauration de classes patrimoniales officielles dans les blocs 2046 |
| signal | 2035-2052 | vieillissement_demographique | demographie_mobilite_humaine | non | politiques de natalité forcée et sélection migratoire des blocs |
| signal | 2035-2051 | fragmentation_chaines_valeur | systemes_productifs_travail | oui | programme de réindustrialisation interne des blocs 2046 |
| signal | 2035-2051 | politiques_migratoires_restrictives | demographie_mobilite_humaine | non | charte commune de fermeture migratoire des blocs 2045 |
| signal | 2035-2053 | transformation_attentes_democratiques | gouvernance_institutions | non | sondage confirmant la préférence majoritaire pour la sécurité des blocs 2046 |
| signal | 2035-2052 | villes_intelligentes_autonomes | organisation_territoires | oui | inauguration de la première cité intelligente fermée du Bloc Sibérien 2049 |
| signal | 2035-2052 | taxation_carbone_globale | systeme_economique_redistribution | non | adoption de barèmes carbone distincts par chaque bloc 2048 |
| signal | 2035-2052 | agents_autonomes_multi_ia | technologie_information | non | lancement des agents administratifs autonomes des blocs 2045 |
| signal | 2035-2050 | guerres_culturelles_transnationales | valeurs_culture_tempo_sociale | non | lancement de la doctrine de guerre culturelle des blocs 2045 |
| signal | 2036-2050 | militarisation_du_cyberespace | geopolitique_conflits | oui | création des commandements cyber des blocs 2044 |
| signal | 2036-2051 | hybridation_ia_culture | valeurs_culture_tempo_sociale | non | déploiement des systèmes de production culturelle des blocs |
| signal | 2036-2052 | megafeux_saisonniers | climat_environnement_global | oui | création des zones rouges incendie hors-bloc 2046 |
| signal | 2036-2053 | discours_effondrement_climatique | climat_environnement_global | oui | campagne officielle des blocs sur la fin du monde ancien 2046 |
| signal | 2036-2053 | outils_predictifs_migratoires | demographie_mobilite_humaine | non | déploiement du système de tri prédictif frontalier du Bloc Atlantique 2049 |
| signal | 2036-2052 | militarisation_societes | geopolitique_conflits | oui | instauration du service de sécurité territoriale obligatoire des blocs 2046 |
| signal | 2036-2053 | normalisation_conflit_hybride | geopolitique_conflits | oui | adoption de la doctrine de conflit permanent par les blocs 2046 |
| signal | 2036-2052 | stockage_energie_nouvelle_generation | energie_ressources_critiques | oui | nationalisation des giga-usines de batteries du Bloc Atlantique 2046 |
| signal | 2036-2053 | crise_confiance_institutions | gouvernance_institutions | non | sondage confirmant l'effondrement de la confiance dans les institutions mondiales 2045 |
| signal | 2036-2052 | systemes_decision_automatises_publics | gouvernance_institutions | non | déploiement des administrations entièrement automatisées dans les blocs 2046 |
| signal | 2036-2053 | recomposition_centres_economiques | organisation_territoires | oui | transfert du centre financier mondial vers le Bloc Atlantique 2048 |
| signal | 2036-2053 | remise_en_cause_capitalisme_croissance | systeme_economique_redistribution | non | doctrine officielle de puissance économique des blocs 2047 |
| signal | 2036-2052 | disparition_metiers_intermediaires | systemes_productifs_travail | oui | reconversion forcée des métiers intermédiaires vers les administrations des blocs 2045 |
| signal | 2036-2053 | consommation_energetique_ia | technologie_information | non | rationnement énergétique civil au profit des centres de calcul des blocs |
| signal | 2037-2052 | gouvernance_algorithmique_emergente | gouvernance_institutions | non | déploiement du système de scoring citoyen des blocs 2046 |
| signal | 2037-2052 | fatigue_civilisationnelle | valeurs_culture_tempo_sociale | non | renaissance des mouvements civilisationnels des blocs |
| signal | 2037-2053 | concentration_informationnelle | technologie_information | non | nationalisation des infrastructures numériques des blocs 2047 |
| signal | 2037-2053 | dependance_numerique | technologie_information | non | déploiement des internets de blocs 2048 |
| signal | 2037-2053 | instabilite_saisonniere | climat_environnement_global | oui | création des zones climatiques protégées des blocs 2048 |
| signal | 2037-2053 | competition_terres_rares | energie_ressources_critiques | oui | doctrine de sécurité énergétique des blocs 2047 |
| signal | 2037-2053 | migrations_climatiques | demographie_mobilite_humaine | non | construction du système de barrières des blocs 2048 |
| signal | 2037-2054 | debats_identitaires_migrations | demographie_mobilite_humaine | non | doctrine identitaire officielle du Bloc Sibérien sur la mobilité 2050 |
| signal | 2037-2053 | ia_militaire_autonome | geopolitique_conflits | oui | déploiement d'unités de combat autonomes par la Chambre de Sécurité 2047 |
| signal | 2037-2054 | adaptation_sobriete_energetique | energie_ressources_critiques | oui | instauration des quotas énergétiques par catégorie sociale dans les blocs 2048 |
| signal | 2037-2054 | industrialisation_orbitale_privee | frontieres_du_systeme | non | saisie des stations industrielles privées par le Bloc Atlantique 2048 |
| signal | 2037-2054 | gouvernance_environnementale_multiniveaux | gouvernance_institutions | non | adoption de standards environnementaux distincts par chaque bloc 2047 |
| signal | 2037-2054 | declin_rural_accelere | organisation_territoires | oui | classification des zones rurales hors-bloc comme territoires non prioritaires 2046 |
| signal | 2037-2054 | economie_plateformes_dominante | systeme_economique_redistribution | non | nationalisation des plateformes numériques par le Bloc Atlantique 2045 |
| signal | 2037-2053 | automatisation_agricole_massive | systemes_productifs_travail | oui | nationalisation des fermes automatisées stratégiques par les blocs 2047 |
| signal | 2038-2052 | automatisation_financière_algorithmique | systeme_economique_redistribution | non | nationalisation des infrastructures algorithmiques financières |
| signal | 2038-2054 | fragmentation_institutionnelle_regionale | gouvernance_institutions | non | création de l'Alliance des Blocs Atlantique et Eurasiatique 2048 |
| signal | 2038-2052 | tensions_sur_terres_rares | geopolitique_conflits | oui | création des zones d'exclusion minière des blocs 2047 |
| signal | 2038-2054 | stress_territorial_climatique | organisation_territoires | oui | création des territoires protégés des blocs 2049 |
| signal | 2038-2055 | emergence_pathogenes_nouveaux | sante_biotechnologies | non | incident biologique de Vladivostok 2049 |
| signal | 2038-2053 | inegalites_acces_soins | sante_biotechnologies | non | création des zones sanitaires prioritaires des blocs |
| signal | 2038-2055 | course_biotech_internationale | sante_biotechnologies | non | lancement du programme Biodéfense Eurasia par le Bloc Sibérien 2046 |
| signal | 2038-2055 | surveillance_sanitaire_continue | sante_biotechnologies | non | généralisation des capteurs biométriques obligatoires du Bloc Atlantique 2045 |
| signal | 2038-2055 | spatialisation_des_conflits | frontieres_du_systeme | non | création des commandements spatiaux des blocs 2049 |
| signal | 2038-2054 | stress_hydrique | climat_environnement_global | oui | militarisation des grands fleuves transfrontaliers 2049 |
| signal | 2038-2055 | gestion_algorithmique_flux_humains | demographie_mobilite_humaine | non | mise en service du classement migratoire automatisé du Bloc Eurasiatique 2050 |
| signal | 2038-2055 | conflits_climatiques_armes | geopolitique_conflits | oui | première guerre par procuration pour un territoire climatique viable 2048 |
| signal | 2038-2055 | degradation_sites_miniers | energie_ressources_critiques | oui | classification des zones minières comme zones sacrifiées par les blocs 2049 |
| signal | 2038-2056 | retour_recit_civilisationnel_spatial | frontieres_du_systeme | non | lancement de la doctrine du destin orbital par les blocs 2048 |
| signal | 2038-2055 | montee_localisme | organisation_territoires | oui | campagne identitaire locale officielle des blocs 2047 |
| signal | 2038-2054 | normalisation_post_travail | systemes_productifs_travail | oui | instauration du statut de citoyen productif obligatoire des blocs 2046 |
| signal | 2038-2054 | crise_verite_informationnelle | technologie_information | non | adoption de récits factuels officiels distincts par les blocs 2048 |
| signal | 2038-2053 | desynchronisation_generationnelle | valeurs_culture_tempo_sociale | non | instauration de quotas générationnels dans les administrations des blocs 2048 |
| signal | 2039-2055 | megapoles_sous_pression | organisation_territoires | oui | création des zones urbaines protégées des blocs 2050 |
| signal | 2039-2056 | captation_carbone_industrielle | climat_environnement_global | oui | programme de capture carbone du Bloc Atlantique 2052 |
| signal | 2039-2056 | acceptation_transition_contrainte | energie_ressources_critiques | oui | discours unificateur sur l'autosuffisance énergétique des blocs 2049 |
| signal | 2039-2057 | nouvelles_communautes_orbitales | frontieres_du_systeme | non | reconnaissance des stations orbitales comme territoires officiels des blocs 2050 |
| signal | 2039-2055 | automatisation_decisionnelle | technologie_information | non | déploiement des systèmes décisionnels automatisés des blocs 2049 |
| signal | 2039-2054 | acceleration_rythmes_vie_urbains | valeurs_culture_tempo_sociale | non | instauration des cycles de vie optimisés dans les blocs 2049 |
| signal | 2040-2060 | medecine_predictive_ia | sante_biotechnologies | non | Score de Priorité Sanitaire du Bloc Atlantique 2047 |
| signal | 2040-2058 | acceptation_homme_augmente | sante_biotechnologies | non | cérémonies officielles d'augmentation des cadres du Bloc Atlantique 2050 |
| signal | 2040-2058 | saturation_orbitale | frontieres_du_systeme | non | programme de nettoyage orbital militarisé des blocs |
| signal | 2040-2057 | relocalisation_cotiere | climat_environnement_global | oui | programme de réinstallation côtière du Bloc Atlantique 2051 |
| signal | 2040-2055 | retour_spiritualites_hybrides | valeurs_culture_tempo_sociale | non | adoption d'une spiritualité officielle hybride par les blocs 2050 |
| signal | 2041-2058 | minage_asteroides | frontieres_du_systeme | non | lancement de la première mission minière militarisée d'astéroïde 2051 |
| evenement | 2041 | encheres_terres_rares_groenland | energie_ressources_critiques, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | Nuna Capital ouvre les gisements arctiques aux blocs 2041 |
| signal | 2043-2057 | dedollarisation_progressive | systeme_economique_redistribution | non | création du système monétaire des Blocs de Shanghai |
| evenement | 2044 | exode_midwest_grands_lacs | demographie_mobilite_humaine, organisation_territoires, gouvernance_institutions, climat_environnement_global | — | 18 millions de déplacés convergent vers les Grands Lacs 2044 |
| signal | 2045-2062 | fusion_experimentale | energie_ressources_critiques | oui | premier réacteur à fusion militarisé du Bloc Asiatique 2058 |
| evenement | 2047 | crise_gouvernance_amazonie | climat_environnement_global, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | milices corporatives encerclent Belém, bassin fracturé 2047 |
| evenement | 2051 | secession_great_lakes_compact | organisation_territoires, gouvernance_institutions, geopolitique_conflits | — | Compact des Grands Lacs proclame souveraineté sur les eaux 2051 |
| evenement | 2059 | incident_passage_arctique | geopolitique_conflits, frontieres_du_systeme, energie_ressources_critiques | — | NAT saisit convoi arctique, Groenland saisit tribunal 2059 |
| evenement | 2063 | communes_rust_belt_zones_libres | geopolitique_conflits, valeurs_culture_tempo_sociale, gouvernance_institutions, organisation_territoires | — | Communes du Rust Belt proclament zones libres 2063 |
| evenement | 2063 | insurrection_rust_belt | geopolitique_conflits, valeurs_culture_tempo_sociale, gouvernance_institutions, technologie_information | — | Rust Belt occupe friches industrielles contre l'algorithme 2063 |
| evenement | 2073 | emeutes_algorithme_sao_paulo | gouvernance_institutions, technologie_information, organisation_territoires | — | favelas numériques exposent algorithmes du SPAS 2073 |

## new_sustainability

| type | date | source | variable(s) | pilote | evenement_cle |
|---|---|---|---|---|---|
| evenement | 2026 | conflit_israel_iran_2026 | geopolitique_conflits, energie_ressources_critiques, gouvernance_institutions, demographie_mobilite_humaine | — | frappes Israël-Iran absorbées par la médiation mondiale 2027 |
| signal | 2029-2045 | acceptation_transition_contrainte | energie_ressources_critiques | oui | lancement du récit mondial de la transition comme opportunité 2038 |
| signal | 2029-2045 | villes_intelligentes_autonomes | organisation_territoires | oui | déploiement du réseau mondial de villes intelligentes adaptatives 2039 |
| signal | 2029-2045 | explosion_inegalites_patrimoniales | systeme_economique_redistribution | non | entrée en vigueur de l'impôt mondial sur la fortune 2039 |
| signal | 2029-2045 | normalisation_post_travail | systemes_productifs_travail | oui | adoption du récit mondial de la société post-travail 2039 |
| signal | 2030-2045 | course_biotech_internationale | sante_biotechnologies | non | signature du Pacte de Singapour pour la recherche biotech ouverte 2039 |
| signal | 2030-2046 | fragmentation_chaines_valeur | systemes_productifs_travail | oui | déploiement du système mondial de traçabilité des chaînes 2038 |
| signal | 2030-2046 | discours_effondrement_climatique | climat_environnement_global | oui | publication du manifeste de la transition régénérative 2037 |
| signal | 2030-2046 | politiques_migratoires_restrictives | demographie_mobilite_humaine | non | accord mondial de mobilité régulée remplaçant les quotas unilatéraux 2038 |
| signal | 2030-2046 | stockage_energie_nouvelle_generation | energie_ressources_critiques | oui | commercialisation mondiale des batteries à flux longue durée 2038 |
| signal | 2030-2046 | transformation_attentes_democratiques | gouvernance_institutions | non | adoption du premier référendum permanent assisté par IA 2039 |
| signal | 2030-2046 | recomposition_centres_economiques | organisation_territoires | oui | lancement du réseau mondial des hubs économiques distribués 2040 |
| signal | 2030-2046 | taxation_carbone_globale | systeme_economique_redistribution | non | entrée en vigueur de la taxe carbone mondiale universelle 2038 |
| signal | 2030-2046 | agents_autonomes_multi_ia | technologie_information | non | déploiement du réseau mondial d'agents IA collaboratifs 2038 |
| signal | 2030-2045 | guerres_culturelles_transnationales | valeurs_culture_tempo_sociale | non | création du forum mondial de dialogue interculturel permanent 2038 |
| signal | 2031-2047 | stress_hydrique | climat_environnement_global | oui | Traité mondial sur l'eau et la sécurité hydrique 2038 |
| signal | 2031-2047 | outils_predictifs_migratoires | demographie_mobilite_humaine | non | déploiement de la plateforme mondiale d'anticipation migratoire 2039 |
| signal | 2031-2048 | militarisation_societes | geopolitique_conflits | oui | lancement du programme mondial de démilitarisation civile 2039 |
| signal | 2031-2047 | adaptation_sobriete_energetique | energie_ressources_critiques | oui | lancement de la campagne mondiale pour la sobriété choisie 2039 |
| signal | 2031-2047 | industrialisation_orbitale_privee | frontieres_du_systeme | non | fusion des consortiums orbitaux dans le réseau économique mondial 2039 |
| signal | 2031-2047 | crise_confiance_institutions | gouvernance_institutions | non | publication du premier baromètre mondial de confiance institutionnelle 2039 |
| signal | 2031-2047 | declin_rural_accelere | organisation_territoires | oui | lancement du programme de revitalisation rurale par IA 2039 |
| signal | 2031-2047 | remise_en_cause_capitalisme_croissance | systeme_economique_redistribution | non | adoption mondiale des indicateurs de prosperité post-croissance 2039 |
| signal | 2031-2047 | disparition_metiers_intermediaires | systemes_productifs_travail | oui | lancement du programme mondial de reconversion vers les métiers hybrides 2038 |
| signal | 2031-2047 | consommation_energetique_ia | technologie_information | non | premiers centres de données alimentés à 100% par fusion 2039 |
| signal | 2031-2046 | desynchronisation_generationnelle | valeurs_culture_tempo_sociale | non | lancement du pacte intergénérationnel mondial pour la régénération 2039 |
| signal | 2032-2047 | fragmentation_institutionnelle_regionale | gouvernance_institutions | non | réforme majeure de l'ONU et création du Conseil Climatique Mondial 2039 |
| signal | 2032-2047 | hybridation_ia_culture | valeurs_culture_tempo_sociale | non | Charte mondiale de l'IA créative 2039 |
| signal | 2032-2048 | megapoles_sous_pression | organisation_territoires | oui | programme Villes Régénératives 2040 |
| signal | 2032-2045 | emergence_pathogenes_nouveaux | sante_biotechnologies | non | création du Réseau Mondial de Biosurveillance en 2038 |
| signal | 2032-2048 | surveillance_sanitaire_continue | sante_biotechnologies | non | extension du Réseau Mondial de Biosurveillance aux foyers en 2042 |
| signal | 2032-2048 | spatialisation_des_conflits | frontieres_du_systeme | non | Traité de l'Espace renouvelé et étendu 2040 |
| signal | 2032-2047 | concentration_informationnelle | technologie_information | non | Traité mondial sur la régulation des plateformes numériques 2039 |
| signal | 2032-2047 | dependance_numerique | technologie_information | non | programme mondial de résilience numérique 2039 |
| signal | 2032-2048 | instabilite_saisonniere | climat_environnement_global | oui | déploiement mondial des puits de carbone technologiques 2040 |
| signal | 2032-2047 | competition_terres_rares | energie_ressources_critiques | oui | Fonds Mondial des Ressources Critiques 2040 |
| signal | 2032-2048 | migrations_climatiques | demographie_mobilite_humaine | non | Pacte mondial de gestion des migrations climatiques 2040 |
| signal | 2032-2048 | automatisation_cognitive | systemes_productifs_travail | oui | instauration du revenu universel global 2041 |
| signal | 2032-2047 | ia_militaire_autonome | geopolitique_conflits | oui | ratification du traité d'interdiction des armes autonomes 2040 |
| signal | 2032-2048 | normalisation_conflit_hybride | geopolitique_conflits | oui | lancement de la campagne mondiale pour la paix systémique 2040 |
| signal | 2032-2049 | retour_recit_civilisationnel_spatial | frontieres_du_systeme | non | lancement du récit mondial de la civilisation multi-orbitale 2041 |
| signal | 2032-2048 | systemes_decision_automatises_publics | gouvernance_institutions | non | certification mondiale des systèmes décisionnels publics automatisés 2040 |
| signal | 2032-2048 | economie_plateformes_dominante | systeme_economique_redistribution | non | adoption du statut de bien commun pour les plateformes mondiales 2039 |
| signal | 2033-2048 | gouvernance_algorithmique_emergente | gouvernance_institutions | non | Accord de Séoul sur la gouvernance IA institutionnelle 2040 |
| signal | 2033-2047 | militarisation_du_cyberespace | geopolitique_conflits | oui | Convention de Genève numérique 2040 |
| signal | 2033-2048 | fatigue_civilisationnelle | valeurs_culture_tempo_sociale | non | premier Forum Mondial des Civilisations Régénératives 2041 |
| signal | 2033-2049 | stress_territorial_climatique | organisation_territoires | oui | plan mondial de relocalisation climatique 2041 |
| signal | 2033-2050 | saturation_orbitale | frontieres_du_systeme | non | Agence Mondiale du Trafic Spatial 2041 |
| signal | 2033-2049 | megafeux_saisonniers | climat_environnement_global | oui | déploiement du réseau mondial de détection précoce des feux 2039 |
| signal | 2033-2049 | debats_identitaires_migrations | demographie_mobilite_humaine | non | lancement du forum mondial des identités mobiles 2039 |
| signal | 2033-2049 | gestion_algorithmique_flux_humains | demographie_mobilite_humaine | non | déploiement de la plateforme mondiale de gestion des mobilités 2040 |
| signal | 2033-2049 | conflits_climatiques_armes | geopolitique_conflits | oui | signature du pacte mondial de partage des ressources climatiques 2041 |
| signal | 2033-2049 | degradation_sites_miniers | energie_ressources_critiques | oui | adoption de la norme mondiale de restauration minière 2041 |
| signal | 2033-2049 | nouvelles_communautes_orbitales | frontieres_du_systeme | non | adoption du statut de citoyenneté orbitale universelle 2042 |
| signal | 2033-2049 | robotisation_services | systemes_productifs_travail | oui | généralisation mondiale des robots de service dans le tertiaire 2039 |
| signal | 2033-2048 | crise_verite_informationnelle | technologie_information | non | lancement du système mondial de certification de la réalité 2041 |
| signal | 2034-2050 | captation_carbone_industrielle | climat_environnement_global | oui | mise en service du réseau mondial de capture carbone 2043 |
| signal | 2034-2051 | minage_asteroides | frontieres_du_systeme | non | lancement du programme international de minage d'astéroïdes 2043 |
| signal | 2034-2050 | gouvernance_environnementale_multiniveaux | gouvernance_institutions | non | adoption par le Conseil Climatique Mondial du cadre multi-niveaux 2043 |
| signal | 2034-2050 | montee_localisme | organisation_territoires | oui | lancement du mouvement mondial des cultures glocales 2039 |
| signal | 2034-2050 | automatisation_agricole_massive | systemes_productifs_travail | oui | lancement du programme mondial d'agriculture régénérative automatisée 2040 |
| signal | 2034-2049 | automatisation_decisionnelle | technologie_information | non | certification mondiale des systèmes décisionnels automatisés fiables 2042 |
| signal | 2034-2049 | acceleration_rythmes_vie_urbains | valeurs_culture_tempo_sociale | non | déploiement mondial des horaires adaptatifs urbains pilotés par IA 2042 |
| signal | 2035-2048 | automatisation_financière_algorithmique | systeme_economique_redistribution | non | Accords de Genève sur la régulation des IA financières |
| signal | 2035-2050 | tensions_sur_terres_rares | geopolitique_conflits | oui | Traité de Nairobi sur les minerais stratégiques 2042 |
| signal | 2035-2052 | inegalites_acces_soins | sante_biotechnologies | non | Accord de Lagos sur la santé universelle 2045 |
| signal | 2035-2050 | medecine_predictive_ia | sante_biotechnologies | non | déploiement du Réseau Mondial de Médecine Prédictive en 2044 |
| signal | 2035-2052 | acceptation_homme_augmente | sante_biotechnologies | non | premier Sommet mondial sur l'humain augmenté éthique 2046 |
| signal | 2035-2052 | relocalisation_cotiere | climat_environnement_global | oui | lancement du programme mondial de villes-refuges côtières 2044 |
| signal | 2035-2050 | retour_spiritualites_hybrides | valeurs_culture_tempo_sociale | non | lancement du mouvement spirituel mondial de la régénération 2043 |
| evenement | 2039 | submersion_tuvalu_acte_fondateur | climat_environnement_global, gouvernance_institutions, organisation_territoires, frontieres_du_systeme | — | Tuvalu submergée, Pacifique Sud fonde le droit post-territorial 2039 |
| signal | 2040-2055 | dedollarisation_progressive | systeme_economique_redistribution | non | création du Droit de Tirage Universel 2.0 |
| signal | 2040-2060 | vieillissement_demographique | demographie_mobilite_humaine | non | allongement de l'espérance de vie active à 90 ans |
| evenement | 2041 | encheres_terres_rares_groenland | energie_ressources_critiques, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | Groenland encadre ses terres rares via Traité de Nairobi 2041 |
| evenement | 2044 | exode_midwest_grands_lacs | demographie_mobilite_humaine, organisation_territoires, gouvernance_institutions, climat_environnement_global | — | 18 millions de migrants climatiques convergent vers les Grands Lacs 2044 |
| evenement | 2047 | crise_gouvernance_amazonie | climat_environnement_global, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | Amazônia Viva teste sa souveraineté face aux blocs extractifs 2047 |
| signal | 2048-2065 | fusion_experimentale | energie_ressources_critiques | oui | premier réseau de réacteurs à fusion commercial 2060 |
| evenement | 2051 | secession_great_lakes_compact | organisation_territoires, gouvernance_institutions, geopolitique_conflits | — | Great Lakes Compact obtient autonomie hydrique reconnue 2051 |
| evenement | 2053 | accord_carbone_amazonie_blocs | climat_environnement_global, gouvernance_institutions, geopolitique_conflits, energie_ressources_critiques | — | Amazonie impose sa souveraineté carbone aux blocs mondiaux 2053 |
| evenement | 2062 | grand_forum_sahel_numerique | technologie_information, gouvernance_institutions, organisation_territoires | — | Charte d'Agadez consacre la souveraineté numérique périphérique 2062 |

## eco_communalism

| type | date | source | variable(s) | pilote | evenement_cle |
|---|---|---|---|---|---|
| evenement | 2027 | conflit_israel_iran_2026 | geopolitique_conflits, energie_ressources_critiques, gouvernance_institutions, demographie_mobilite_humaine | — | frappes israélo-iraniennes isolent les bassins vivants 2027 |
| signal | 2035-2055 | spatialisation_des_conflits | frontieres_du_systeme | non | abandon des programmes spatiaux nationaux non essentiels |
| signal | 2035-2053 | saturation_orbitale | frontieres_du_systeme | non | moratoire communautaire sur les lancements commerciaux |
| signal | 2035-2055 | fusion_experimentale | energie_ressources_critiques | oui | abandon communautaire des projets centralisés de fusion |
| signal | 2035-2055 | vieillissement_demographique | demographie_mobilite_humaine | non | renaissance des modèles familiaux élargis et communautaires |
| signal | 2036-2055 | discours_effondrement_climatique | climat_environnement_global | oui | diffusion virale du mouvement des veillées de l'effondrement |
| signal | 2036-2055 | acceptation_transition_contrainte | energie_ressources_critiques | oui | manifeste bioterritorial de la sobriété choisie |
| signal | 2036-2055 | industrialisation_orbitale_privee | frontieres_du_systeme | non | dissolution volontaire des consortiums orbitaux à but lucratif |
| signal | 2036-2055 | villes_intelligentes_autonomes | organisation_territoires | oui | réseau bioterritorial de capteurs urbains low-tech partagés |
| signal | 2036-2055 | explosion_inegalites_patrimoniales | systeme_economique_redistribution | non | généralisation des communs bioterritoriaux remplaçant la propriété privée |
| signal | 2036-2055 | robotisation_services | systemes_productifs_travail | oui | charte bioterritoriale pour des services assurés par des humains |
| signal | 2037-2056 | fragmentation_chaines_valeur | systemes_productifs_travail | oui | mouvement de localisation des chaînes de valeur essentielles |
| signal | 2037-2055 | megafeux_saisonniers | climat_environnement_global | oui | renaissance des pratiques autochtones de brûlage dirigé |
| signal | 2037-2056 | stockage_energie_nouvelle_generation | energie_ressources_critiques | oui | réseau bioterritorial de stockage thermique communautaire |
| signal | 2037-2056 | nouvelles_communautes_orbitales | frontieres_du_systeme | non | fondation de la première communauté orbitale coopérative scientifique |
| signal | 2037-2056 | systemes_decision_automatises_publics | gouvernance_institutions | non | démantèlement volontaire des systèmes décisionnels automatisés locaux |
| signal | 2037-2056 | recomposition_centres_economiques | organisation_territoires | oui | mouvement de relocalisation économique vers les territoires bioterritoriaux |
| signal | 2037-2056 | taxation_carbone_globale | systeme_economique_redistribution | non | charte bioterritoriale de redevabilité écologique directe |
| signal | 2037-2056 | agents_autonomes_multi_ia | technologie_information | non | charte bioterritoriale des assistants IA communautaires |
| signal | 2038-2057 | instabilite_saisonniere | climat_environnement_global | oui | mouvement de régénération écologique territoriale |
| signal | 2038-2056 | stress_hydrique | climat_environnement_global | oui | mouvement mondial de souveraineté hydrique locale |
| signal | 2038-2057 | automatisation_cognitive | systemes_productifs_travail | oui | mouvement néo-artisanal et de l'économie du soin |
| signal | 2038-2057 | outils_predictifs_migratoires | demographie_mobilite_humaine | non | réseau bioterritorial d'anticipation des mobilités locales |
| signal | 2038-2057 | normalisation_conflit_hybride | geopolitique_conflits | oui | diffusion des récits bioterritoriaux de réparation post-conflit |
| signal | 2038-2057 | adaptation_sobriete_energetique | energie_ressources_critiques | oui | charte bioterritoriale de sobriété énergétique partagée |
| signal | 2038-2057 | minage_asteroides | frontieres_du_systeme | non | charte scientifique internationale contre le minage extractif d'astéroïdes |
| signal | 2038-2056 | retour_recit_civilisationnel_spatial | frontieres_du_systeme | non | manifeste pour une présence spatiale sobre et non conquérante |
| signal | 2038-2057 | gouvernance_environnementale_multiniveaux | gouvernance_institutions | non | constitution du réseau des conseils environnementaux bioterritoriaux |
| signal | 2038-2057 | declin_rural_accelere | organisation_territoires | oui | mouvement de retour à la terre bioterritorial |
| signal | 2038-2057 | remise_en_cause_capitalisme_croissance | systeme_economique_redistribution | non | charte fondatrice post-croissance des assemblées bioterritoriales |
| signal | 2038-2057 | consommation_energetique_ia | technologie_information | non | mouvement bioterritorial des modèles IA frugaux |
| signal | 2038-2056 | guerres_culturelles_transnationales | valeurs_culture_tempo_sociale | non | mouvement bioterritorial de désengagement des récits globaux |
| signal | 2039-2058 | competition_terres_rares | energie_ressources_critiques | oui | mouvement de circularité des matériaux critiques |
| signal | 2039-2058 | migrations_climatiques | demographie_mobilite_humaine | non | programme d'accueil des réfugiés climatiques bioterritoriaux |
| signal | 2039-2058 | captation_carbone_industrielle | climat_environnement_global | oui | mouvement de boycott des fermes de capture carbone industrielles |
| signal | 2039-2058 | ia_militaire_autonome | geopolitique_conflits | oui | mouvement de démilitarisation autonome des territoires |
| signal | 2039-2058 | crise_confiance_institutions | gouvernance_institutions | non | généralisation des assemblées de redevabilité locale dans les bioterritoires |
| signal | 2039-2058 | montee_localisme | organisation_territoires | oui | manifeste fondateur du localisme bioterritorial |
| signal | 2039-2058 | economie_plateformes_dominante | systeme_economique_redistribution | non | lancement du réseau coopératif bioterritorial d'échanges numériques |
| signal | 2039-2058 | disparition_metiers_intermediaires | systemes_productifs_travail | oui | mouvement de revalorisation des savoir-faire intermédiaires bioterritoriaux |
| signal | 2039-2058 | crise_verite_informationnelle | technologie_information | non | réseau bioterritorial de vérification communautaire de l'information |
| signal | 2039-2057 | desynchronisation_generationnelle | valeurs_culture_tempo_sociale | non | charte bioterritoriale du mentorat intergénérationnel |
| signal | 2040-2058 | fragmentation_institutionnelle_regionale | gouvernance_institutions | non | création des Assemblées Bioterritioriales Régionales |
| signal | 2040-2060 | tensions_sur_terres_rares | geopolitique_conflits | oui | mouvement de démétallisation des économies locales |
| signal | 2040-2058 | fatigue_civilisationnelle | valeurs_culture_tempo_sociale | non | renaissance des cultures situées et des récits de lieu |
| signal | 2040-2058 | stress_territorial_climatique | organisation_territoires | oui | mouvement global de retour aux territoires vivables |
| signal | 2040-2058 | emergence_pathogenes_nouveaux | sante_biotechnologies | non | reconfiguration des systèmes de santé locaux post-pandémie |
| signal | 2040-2058 | inegalites_acces_soins | sante_biotechnologies | non | mouvement des maisons de santé communautaires |
| signal | 2040-2058 | course_biotech_internationale | sante_biotechnologies | non | création du réseau open-source "Semences et Remèdes" 2049 |
| signal | 2040-2058 | dependance_numerique | technologie_information | non | mouvement de sobriété numérique global |
| signal | 2040-2058 | debats_identitaires_migrations | demographie_mobilite_humaine | non | charte des identités bioterritoriales et de l'accueil |
| signal | 2040-2059 | gestion_algorithmique_flux_humains | demographie_mobilite_humaine | non | mouvement de débranchement des systèmes de gestion migratoire centralisés |
| signal | 2040-2059 | conflits_climatiques_armes | geopolitique_conflits | oui | création des conseils de médiation climatique bioterritoriaux |
| signal | 2040-2059 | degradation_sites_miniers | energie_ressources_critiques | oui | mouvement de réhabilitation bioterritoriale des friches minières |
| signal | 2040-2059 | transformation_attentes_democratiques | gouvernance_institutions | non | généralisation des assemblées délibératives locales comme norme démocratique |
| signal | 2040-2059 | automatisation_agricole_massive | systemes_productifs_travail | oui | mouvement de retour aux pratiques agricoles low-tech bioterritoriales |
| signal | 2041-2060 | megapoles_sous_pression | organisation_territoires | oui | mouvement de décroissance urbaine volontaire |
| signal | 2041-2060 | concentration_informationnelle | technologie_information | non | déploiement mondial des réseaux mesh communautaires |
| signal | 2041-2059 | relocalisation_cotiere | climat_environnement_global | oui | mouvement de retour vers les terres hautes bioterritoriales |
| signal | 2041-2059 | politiques_migratoires_restrictives | demographie_mobilite_humaine | non | dissolution de fait des contrôles migratoires nationaux dans les bioterritoires |
| signal | 2041-2060 | militarisation_societes | geopolitique_conflits | oui | charte des milices civiques non armées des bioterritoires |
| signal | 2041-2060 | normalisation_post_travail | systemes_productifs_travail | oui | manifeste bioterritorial de la contribution choisie |
| signal | 2041-2059 | acceleration_rythmes_vie_urbains | valeurs_culture_tempo_sociale | non | charte bioterritoriale du tempo lent et des cycles naturels |
| evenement | 2041 | encheres_terres_rares_groenland | energie_ressources_critiques, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | Kalaallit Nunaat met aux enchères ses terres rares 2041 |
| signal | 2042-2060 | automatisation_financière_algorithmique | systeme_economique_redistribution | non | mouvement de déconnexion des marchés algorithmiques |
| signal | 2042-2060 | militarisation_du_cyberespace | geopolitique_conflits | oui | mouvement de souveraineté numérique locale |
| signal | 2042-2060 | hybridation_ia_culture | valeurs_culture_tempo_sociale | non | mouvement de réappropriation culturelle locale |
| signal | 2042-2060 | surveillance_sanitaire_continue | sante_biotechnologies | non | charte des maisons de santé sur le consentement sanitaire 2047 |
| signal | 2042-2060 | acceptation_homme_augmente | sante_biotechnologies | non | charte communautaire pour des corps non augmentés 2044 |
| signal | 2042-2061 | automatisation_decisionnelle | technologie_information | non | démantèlement communautaire des systèmes décisionnels automatisés |
| signal | 2043-2062 | gouvernance_algorithmique_emergente | gouvernance_institutions | non | mouvement de déconnexion algorithmique communautaire |
| signal | 2043-2061 | retour_spiritualites_hybrides | valeurs_culture_tempo_sociale | non | fondation des premières communautés spirituelles bioterritoriales |
| evenement | 2044 | exode_midwest_grands_lacs | demographie_mobilite_humaine, organisation_territoires, gouvernance_institutions, climat_environnement_global | — | 18 millions de déracinés déferlent vers les Grands Lacs 2044 |
| signal | 2045-2065 | dedollarisation_progressive | systeme_economique_redistribution | non | mouvement des monnaies bioterritioriales |
| signal | 2045-2065 | medecine_predictive_ia | sante_biotechnologies | non | diffusion des kits de diagnostic communautaire "Santé Sobre" 2052 |
| evenement | 2047 | crise_gouvernance_amazonie | climat_environnement_global, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | Pacte Amazônia Viva déclare souveraineté écologique d'urgence 2047 |
| evenement | 2062 | grand_forum_sahel_numerique | technologie_information, gouvernance_institutions, organisation_territoires | — | Charte d'Agadez consacre les périphéries numériques souveraines 2062 |
| evenement | 2063 | communes_rust_belt_zones_libres | geopolitique_conflits, valeurs_culture_tempo_sociale, gouvernance_institutions, organisation_territoires | — | Friches du Rust Belt proclament zones libres algorithme 2063 |
| evenement | 2063 | insurrection_rust_belt | geopolitique_conflits, valeurs_culture_tempo_sociale, gouvernance_institutions, technologie_information | — | Communes du Rust Belt bannissent gouvernance algorithmique 2063 |
| evenement | 2096 | crue_exceptionnelle_congo | organisation_territoires, climat_environnement_global, demographie_mobilite_humaine, systeme_economique_redistribution | — | Le Congo engloutit les communs fluviaux 2096 |

## policy_reform

| type | date | source | variable(s) | pilote | evenement_cle |
|---|---|---|---|---|---|
| signal | 2025-2041 | explosion_inegalites_patrimoniales | systeme_economique_redistribution | non | adoption de la réforme fiscale internationale sur les grandes fortunes 2035 |
| signal | 2025-2040 | disparition_metiers_intermediaires | systemes_productifs_travail | oui | lancement du plan international de reconversion professionnelle 2033 |
| signal | 2025-2041 | agents_autonomes_multi_ia | technologie_information | non | adoption de la norme mondiale d'auditabilité des agents IA 2033 |
| signal | 2026-2041 | fragmentation_chaines_valeur | systemes_productifs_travail | oui | directive sur la résilience des chaînes d'approvisionnement critiques 2032 |
| signal | 2026-2043 | debats_identitaires_migrations | demographie_mobilite_humaine | non | programme international de dialogue interculturel sur les migrations 2034 |
| signal | 2026-2042 | acceptation_transition_contrainte | energie_ressources_critiques | oui | lancement de la campagne publique de pédagogie énergétique 2033 |
| signal | 2026-2042 | villes_intelligentes_autonomes | organisation_territoires | oui | adoption de la norme internationale des villes intelligentes 2036 |
| signal | 2026-2042 | taxation_carbone_globale | systeme_economique_redistribution | non | accord international sur un prix plancher du carbone 2033 |
| signal | 2026-2042 | consommation_energetique_ia | technologie_information | non | adoption de la norme internationale d'efficacité énergétique de l'IA 2034 |
| signal | 2026-2042 | guerres_culturelles_transnationales | valeurs_culture_tempo_sociale | non | lancement du programme international d'éducation au dialogue interculturel 2033 |
| signal | 2027-2043 | megafeux_saisonniers | climat_environnement_global | oui | création de la force mondiale anti-incendie de l'ONU 2034 |
| signal | 2027-2043 | politiques_migratoires_restrictives | demographie_mobilite_humaine | non | accord-cadre international sur les quotas migratoires négociés 2034 |
| signal | 2027-2043 | normalisation_conflit_hybride | geopolitique_conflits | oui | publication du rapport-cadre sur la gestion du conflit hybride 2034 |
| signal | 2027-2043 | adaptation_sobriete_energetique | energie_ressources_critiques | oui | lancement du plan international de sobriété énergétique 2034 |
| signal | 2027-2043 | industrialisation_orbitale_privee | frontieres_du_systeme | non | adoption du cadre international sur l'industrie orbitale privée 2034 |
| signal | 2027-2044 | retour_recit_civilisationnel_spatial | frontieres_du_systeme | non | lancement de la campagne institutionnelle pour la culture spatiale 2035 |
| signal | 2027-2043 | transformation_attentes_democratiques | gouvernance_institutions | non | lancement de la plateforme mondiale de consultation citoyenne 2034 |
| signal | 2027-2044 | systemes_decision_automatises_publics | gouvernance_institutions | non | adoption de la norme sur la supervision humaine obligatoire 2035 |
| signal | 2027-2043 | recomposition_centres_economiques | organisation_territoires | oui | lancement du programme international de rééquilibrage économique territorial 2035 |
| signal | 2027-2043 | remise_en_cause_capitalisme_croissance | systeme_economique_redistribution | non | adoption du tableau de bord international post-PIB 2035 |
| signal | 2027-2043 | robotisation_services | systemes_productifs_travail | oui | adoption de la charte de transition des métiers de service 2034 |
| signal | 2027-2043 | crise_verite_informationnelle | technologie_information | non | adoption de la norme internationale de certification informationnelle 2035 |
| signal | 2027-2043 | desynchronisation_generationnelle | valeurs_culture_tempo_sociale | non | lancement du programme national de dialogue intergénérationnel 2034 |
| evenement | 2027 | conflit_israel_iran_2026 | geopolitique_conflits, energie_ressources_critiques, gouvernance_institutions, demographie_mobilite_humaine | — | frappes croisées contenues par médiation institutionnelle 2027 |
| signal | 2028-2044 | spatialisation_des_conflits | frontieres_du_systeme | non | Convention de l'Espace sur la limitation des armes orbitales 2036 |
| signal | 2028-2043 | saturation_orbitale | frontieres_du_systeme | non | directive internationale sur les débris orbitaux 2035 |
| signal | 2028-2043 | dependance_numerique | technologie_information | non | directive internationale sur la résilience des infrastructures 2035 |
| signal | 2028-2044 | instabilite_saisonniere | climat_environnement_global | oui | accord climatique de Nairobi 2+ avec mécanismes contraignants 2035 |
| signal | 2028-2043 | stress_hydrique | climat_environnement_global | oui | Convention de Genève sur le droit à l'eau 2035 |
| signal | 2028-2044 | migrations_climatiques | demographie_mobilite_humaine | non | Convention de Genève sur les réfugiés climatiques 2035 |
| signal | 2028-2044 | vieillissement_demographique | demographie_mobilite_humaine | non | grand plan de réforme des retraites de 2035 |
| signal | 2028-2044 | automatisation_cognitive | systemes_productifs_travail | oui | Taxe Tobin sur l'automatisation et fonds de reconversion 2036 |
| signal | 2028-2044 | militarisation_societes | geopolitique_conflits | oui | lancement du programme international de démobilisation civile 2035 |
| signal | 2028-2044 | stockage_energie_nouvelle_generation | energie_ressources_critiques | oui | lancement du fonds international pour le stockage énergétique 2035 |
| signal | 2028-2044 | crise_confiance_institutions | gouvernance_institutions | non | adoption de la charte mondiale de transparence institutionnelle 2035 |
| signal | 2028-2044 | declin_rural_accelere | organisation_territoires | oui | lancement du plan national de revitalisation des territoires ruraux 2034 |
| signal | 2028-2044 | economie_plateformes_dominante | systeme_economique_redistribution | non | adoption de la directive mondiale sur la taxation des plateformes 2034 |
| signal | 2028-2044 | acceleration_rythmes_vie_urbains | valeurs_culture_tempo_sociale | non | adoption de la charte internationale des rythmes urbains soutenables 2035 |
| signal | 2029-2044 | hybridation_ia_culture | valeurs_culture_tempo_sociale | non | traité international sur la propriété intellectuelle et l'IA 2036 |
| signal | 2029-2044 | concentration_informationnelle | technologie_information | non | démantèlement judiciaire des GAFAM 2+ de 2036 |
| signal | 2029-2044 | competition_terres_rares | energie_ressources_critiques | oui | traité OCDE sur les minerais de la transition 2036 |
| signal | 2029-2045 | discours_effondrement_climatique | climat_environnement_global | oui | premier plan national de santé mentale climatique 2034 |
| signal | 2029-2045 | outils_predictifs_migratoires | demographie_mobilite_humaine | non | charte internationale sur l'usage éthique des prédictions migratoires 2036 |
| signal | 2029-2045 | conflits_climatiques_armes | geopolitique_conflits | oui | création du mécanisme international de médiation climatique 2036 |
| signal | 2029-2045 | degradation_sites_miniers | energie_ressources_critiques | oui | création du fonds international de réhabilitation minière 2037 |
| signal | 2029-2045 | nouvelles_communautes_orbitales | frontieres_du_systeme | non | lancement du programme international d'habitats orbitaux partagés 2036 |
| signal | 2029-2045 | gouvernance_environnementale_multiniveaux | gouvernance_institutions | non | signature du cadre de coordination environnementale multi-niveaux 2036 |
| signal | 2029-2045 | montee_localisme | organisation_territoires | oui | adoption du cadre de gouvernance locale participative 2034 |
| signal | 2029-2045 | automatisation_agricole_massive | systemes_productifs_travail | oui | adoption de la directive sur l'automatisation agricole responsable 2035 |
| signal | 2030-2045 | gouvernance_algorithmique_emergente | gouvernance_institutions | non | directive mondiale sur l'IA dans les services publics 2037 |
| signal | 2030-2046 | fragmentation_institutionnelle_regionale | gouvernance_institutions | non | traité de réforme des institutions de Bretton Woods 2037 |
| signal | 2030-2046 | megapoles_sous_pression | organisation_territoires | oui | programme ONU-Habitat de résilience des mégapoles 2037 |
| signal | 2030-2044 | emergence_pathogenes_nouveaux | sante_biotechnologies | non | Traité de Genève sur la sécurité sanitaire globale 2035 |
| signal | 2030-2046 | surveillance_sanitaire_continue | sante_biotechnologies | non | adoption du règlement mondial sur les données de santé 2037 |
| signal | 2030-2046 | captation_carbone_industrielle | climat_environnement_global | oui | protocole international de certification de la capture carbone 2037 |
| signal | 2030-2047 | gestion_algorithmique_flux_humains | demographie_mobilite_humaine | non | norme internationale sur les systèmes algorithmiques migratoires 2035 |
| signal | 2030-2046 | ia_militaire_autonome | geopolitique_conflits | oui | création du registre international des systèmes d'armes autonomes 2037 |
| signal | 2030-2046 | minage_asteroides | frontieres_du_systeme | non | adoption du traité de partage des ressources astéroïdales 2038 |
| signal | 2030-2046 | normalisation_post_travail | systemes_productifs_travail | oui | adoption de la semaine de travail réduite à l'échelle mondiale 2033 |
| signal | 2030-2045 | automatisation_decisionnelle | technologie_information | non | adoption de la norme sur la supervision des décisions automatisées 2037 |
| signal | 2030-2045 | retour_spiritualites_hybrides | valeurs_culture_tempo_sociale | non | adoption du cadre légal de reconnaissance des spiritualités hybrides 2037 |
| signal | 2031-2046 | militarisation_du_cyberespace | geopolitique_conflits | oui | traité sur la limitation des cyberarmes 2038 |
| signal | 2031-2046 | fatigue_civilisationnelle | valeurs_culture_tempo_sociale | non | programme UNESCO de recomposition culturelle post-crise |
| signal | 2031-2047 | stress_territorial_climatique | organisation_territoires | oui | directive internationale d'adaptation territoriale 2038 |
| signal | 2031-2048 | relocalisation_cotiere | climat_environnement_global | oui | fonds mondial pour la relocalisation côtière de l'ONU 2039 |
| signal | 2032-2048 | inegalites_acces_soins | sante_biotechnologies | non | directive OMS sur l'accès équitable aux médicaments essentiels |
| signal | 2032-2048 | course_biotech_internationale | sante_biotechnologies | non | ratification du Traité de Brasília sur la biotech responsable 2043 |
| signal | 2032-2050 | acceptation_homme_augmente | sante_biotechnologies | non | premières assises citoyennes sur l'humain augmenté 2040 |
| signal | 2033-2047 | automatisation_financière_algorithmique | systeme_economique_redistribution | non | traité international sur les marchés algorithmiques |
| signal | 2033-2048 | tensions_sur_terres_rares | geopolitique_conflits | oui | accord OCDE sur la traçabilité des ressources critiques |
| signal | 2034-2048 | medecine_predictive_ia | sante_biotechnologies | non | adoption de la Charte Internationale de la Médecine Prédictive Équitable 2041 |
| signal | 2038-2052 | dedollarisation_progressive | systeme_economique_redistribution | non | réforme du FMI et création du Conseil Monétaire Mondial |
| evenement | 2039 | submersion_tuvalu_acte_fondateur | climat_environnement_global, gouvernance_institutions, organisation_territoires, frontieres_du_systeme | — | dernier conseil souverain de Tuvalu, souveraineté flottante proclamée 2039 |
| signal | 2040-2058 | fusion_experimentale | energie_ressources_critiques | oui | création de l'Agence Internationale de la Fusion 2045 |
| evenement | 2041 | encheres_terres_rares_groenland | energie_ressources_critiques, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | première vente aux enchères terres rares Groenland 2041 |
| evenement | 2044 | exode_midwest_grands_lacs | demographie_mobilite_humaine, organisation_territoires, gouvernance_institutions, climat_environnement_global | — | 18 millions de migrants internes vers les Grands Lacs 2044 |
| evenement | 2047 | crise_gouvernance_amazonie | climat_environnement_global, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | état d'urgence écologique amazonien contesté par milices corporatives 2047 |
| evenement | 2055 | accord_carbone_amazonie_blocs | climat_environnement_global, gouvernance_institutions, geopolitique_conflits, energie_ressources_critiques | — | traité de souveraineté carbone signé à Belém 2055 |
| evenement | 2059 | incident_passage_arctique | geopolitique_conflits, frontieres_du_systeme, energie_ressources_critiques | — | convoi APA saisi par forces NAT dans le Nord-Ouest 2059 |
| evenement | 2073 | emeutes_algorithme_sao_paulo | gouvernance_institutions, technologie_information, organisation_territoires | — | contre-cartographie algorithmique publiée à São Paulo 2073 |

## reference

| type | date | source | variable(s) | pilote | evenement_cle |
|---|---|---|---|---|---|
| signal | 2022-2037 | fragmentation_chaines_valeur | systemes_productifs_travail | oui | troisième crise des semiconducteurs 2029 |
| signal | 2023-2038 | robotisation_services | systemes_productifs_travail | oui | premier déploiement massif de robots dans la restauration 2030 |
| signal | 2023-2037 | agents_autonomes_multi_ia | technologie_information | non | premier déploiement commercial massif d'agents IA autonomes 2030 |
| signal | 2023-2038 | guerres_culturelles_transnationales | valeurs_culture_tempo_sociale | non | première étude mondiale sur la polarisation culturelle médiatique 2030 |
| signal | 2024-2039 | dependance_numerique | technologie_information | non | premières pannes systémiques d'envergure 2030 |
| signal | 2024-2040 | instabilite_saisonniere | climat_environnement_global | oui | première décennie au-dessus de 1.5°C 2031 |
| signal | 2024-2039 | stress_hydrique | climat_environnement_global | oui | première grande crise hydrique régionale documentée 2031 |
| signal | 2024-2040 | migrations_climatiques | demographie_mobilite_humaine | non | premier million de réfugiés climatiques officiellement reconnus 2030 |
| signal | 2024-2038 | vieillissement_demographique | demographie_mobilite_humaine | non | première grande crise de financement des retraites 2031 |
| signal | 2024-2039 | automatisation_cognitive | systemes_productifs_travail | oui | première vague de désindustrialisation cognitive 2031 |
| signal | 2024-2041 | discours_effondrement_climatique | climat_environnement_global | oui | best-seller mondial sur l'effondrement civilisationnel 2030 |
| signal | 2024-2040 | normalisation_conflit_hybride | geopolitique_conflits | oui | première enquête internationale sur la normalisation du conflit hybride 2032 |
| signal | 2024-2040 | acceptation_transition_contrainte | energie_ressources_critiques | oui | premier sondage mondial sur l'acceptation de la transition 2031 |
| signal | 2024-2040 | transformation_attentes_democratiques | gouvernance_institutions | non | premier mouvement citoyen mondial pour la démocratie directe 2032 |
| signal | 2024-2039 | villes_intelligentes_autonomes | organisation_territoires | oui | premier classement mondial des villes intelligentes publié 2032 |
| signal | 2024-2040 | recomposition_centres_economiques | organisation_territoires | oui | premier rapport sur le déclin relatif des centres économiques traditionnels 2032 |
| signal | 2024-2041 | montee_localisme | organisation_territoires | oui | premier sondage mondial sur la montée du localisme 2032 |
| signal | 2024-2040 | explosion_inegalites_patrimoniales | systeme_economique_redistribution | non | premier rapport mondial sur la concentration patrimoniale record 2032 |
| signal | 2024-2041 | economie_plateformes_dominante | systeme_economique_redistribution | non | premier rapport sur la concentration record des plateformes mondiales 2032 |
| signal | 2024-2038 | consommation_energetique_ia | technologie_information | non | premier rapport sur l'empreinte énergétique mondiale de l'IA 2031 |
| signal | 2024-2039 | desynchronisation_generationnelle | valeurs_culture_tempo_sociale | non | premier rapport mondial sur la fracture générationnelle 2031 |
| signal | 2025-2040 | spatialisation_des_conflits | frontieres_du_systeme | non | premier incident spatial militaire non mortel 2032 |
| signal | 2025-2040 | saturation_orbitale | frontieres_du_systeme | non | premier incident critique lié aux débris orbitaux 2031 |
| signal | 2025-2040 | concentration_informationnelle | technologie_information | non | fusion des deux dernières grandes plateformes mondiales 2032 |
| signal | 2025-2040 | competition_terres_rares | energie_ressources_critiques | oui | première crise des terres rares post-Covid 2030 |
| signal | 2025-2041 | megafeux_saisonniers | climat_environnement_global | oui | saison record de mégafeux sur trois continents 2032 |
| signal | 2025-2041 | outils_predictifs_migratoires | demographie_mobilite_humaine | non | premiers systèmes prédictifs migratoires commercialisés aux frontières 2032 |
| signal | 2025-2042 | politiques_migratoires_restrictives | demographie_mobilite_humaine | non | vague de fermetures frontalières en réponse aux crises migratoires 2031 |
| signal | 2025-2041 | militarisation_societes | geopolitique_conflits | oui | premier rapport sur la militarisation croissante des sociétés civiles 2032 |
| signal | 2025-2041 | stockage_energie_nouvelle_generation | energie_ressources_critiques | oui | premiers déploiements commerciaux de stockage longue durée 2032 |
| signal | 2025-2042 | adaptation_sobriete_energetique | energie_ressources_critiques | oui | première campagne nationale de sobriété énergétique obligatoire 2032 |
| signal | 2025-2042 | industrialisation_orbitale_privee | frontieres_du_systeme | non | premier contrat industriel privé en orbite basse 2031 |
| signal | 2025-2041 | retour_recit_civilisationnel_spatial | frontieres_du_systeme | non | dernier lancement habité médiatisé à grande échelle 2032 |
| signal | 2025-2041 | crise_confiance_institutions | gouvernance_institutions | non | premier indice mondial de défiance institutionnelle publié 2032 |
| signal | 2025-2042 | systemes_decision_automatises_publics | gouvernance_institutions | non | premier scandale d'erreur judiciaire algorithmique documenté 2033 |
| signal | 2025-2041 | declin_rural_accelere | organisation_territoires | oui | premier rapport sur la désertification rurale accélérée 2032 |
| signal | 2025-2041 | taxation_carbone_globale | systeme_economique_redistribution | non | premier rapport sur l'échec de la coordination carbone mondiale 2031 |
| signal | 2025-2040 | disparition_metiers_intermediaires | systemes_productifs_travail | oui | premier rapport sur la disparition accélérée des métiers intermédiaires 2030 |
| signal | 2025-2040 | acceleration_rythmes_vie_urbains | valeurs_culture_tempo_sociale | non | premier rapport mondial sur l'accélération des rythmes urbains 2032 |
| signal | 2026-2040 | fragmentation_institutionnelle_regionale | gouvernance_institutions | non | crise de gouvernance multilatérale de 2032 |
| signal | 2026-2040 | hybridation_ia_culture | valeurs_culture_tempo_sociale | non | première crise des droits d'auteur IA globale 2031 |
| signal | 2026-2041 | megapoles_sous_pression | organisation_territoires | oui | première crise de gouvernance d'une mégapole 2033 |
| signal | 2026-2045 | course_biotech_internationale | sante_biotechnologies | non | rapport sur la concentration mondiale de la recherche biotech 2033 |
| signal | 2026-2048 | surveillance_sanitaire_continue | sante_biotechnologies | non | polémique sur les assureurs et les données de santé connectées 2031 |
| signal | 2026-2048 | acceptation_homme_augmente | sante_biotechnologies | non | sondage révélant la fracture générationnelle sur l'augmentation 2034 |
| signal | 2026-2042 | captation_carbone_industrielle | climat_environnement_global | oui | premiers démonstrateurs industriels de capture carbone à grande échelle 2033 |
| signal | 2026-2042 | debats_identitaires_migrations | demographie_mobilite_humaine | non | percée électorale de mouvements anti-migration dans plusieurs pays 2032 |
| signal | 2026-2042 | ia_militaire_autonome | geopolitique_conflits | oui | premier déploiement opérationnel documenté d'une arme autonome 2033 |
| signal | 2026-2043 | conflits_climatiques_armes | geopolitique_conflits | oui | premier conflit armé officiellement attribué au changement climatique 2033 |
| signal | 2026-2043 | degradation_sites_miniers | energie_ressources_critiques | oui | premier rapport mondial sur la dégradation des sites miniers 2033 |
| signal | 2026-2043 | nouvelles_communautes_orbitales | frontieres_du_systeme | non | installation de la première communauté orbitale permanente 2033 |
| signal | 2026-2042 | gouvernance_environnementale_multiniveaux | gouvernance_institutions | non | premier rapport sur les lacunes de la gouvernance environnementale mondiale 2033 |
| signal | 2026-2042 | remise_en_cause_capitalisme_croissance | systeme_economique_redistribution | non | premier débat mondial télévisé sur la fin de la croissance 2032 |
| signal | 2026-2041 | automatisation_agricole_massive | systemes_productifs_travail | oui | premier rapport sur l'impact rural de l'automatisation agricole 2031 |
| signal | 2026-2041 | crise_verite_informationnelle | technologie_information | non | premier sondage mondial confirmant la défiance informationnelle généralisée 2032 |
| evenement | 2026 | conflit_israel_iran_2026 | geopolitique_conflits, energie_ressources_critiques, gouvernance_institutions, demographie_mobilite_humaine | — | Frappes israéliennes sur Fordo déclenchent contre-frappes iraniennes 2026 |
| signal | 2027-2042 | militarisation_du_cyberespace | geopolitique_conflits | oui | première cyberattaque majeure sur infrastructure critique 2033 |
| signal | 2027-2041 | fatigue_civilisationnelle | valeurs_culture_tempo_sociale | non | première décennie perdue de cohésion culturelle 2035 |
| signal | 2027-2042 | stress_territorial_climatique | organisation_territoires | oui | premières migrations climatiques massives documentées 2034 |
| signal | 2027-2044 | relocalisation_cotiere | climat_environnement_global | oui | premier plan municipal de retrait côtier documenté 2034 |
| signal | 2027-2044 | gestion_algorithmique_flux_humains | demographie_mobilite_humaine | non | premier scandale de discrimination algorithmique aux frontières 2032 |
| signal | 2027-2044 | minage_asteroides | frontieres_du_systeme | non | première mission expérimentale de minage d'astéroïde 2035 |
| signal | 2027-2042 | normalisation_post_travail | systemes_productifs_travail | oui | premier débat médiatique mondial sur la fin du travail 2030 |
| signal | 2027-2042 | automatisation_decisionnelle | technologie_information | non | premier scandale judiciaire lié à une décision automatisée 2033 |
| signal | 2028-2042 | gouvernance_algorithmique_emergente | gouvernance_institutions | non | premiers scandales de biais algorithmiques systémiques 2034 |
| signal | 2028-2043 | tensions_sur_terres_rares | geopolitique_conflits | oui | crise des terres rares asiatiques 2038 |
| signal | 2028-2042 | emergence_pathogenes_nouveaux | sante_biotechnologies | non | crise sanitaire régionale non résolue de 2037 |
| signal | 2028-2042 | inegalites_acces_soins | sante_biotechnologies | non | rapport OMS sur la fracture sanitaire mondiale 2035 |
| signal | 2028-2042 | retour_spiritualites_hybrides | valeurs_culture_tempo_sociale | non | premier recensement mondial des spiritualités hybrides émergentes 2035 |
| signal | 2030-2045 | automatisation_financière_algorithmique | systeme_economique_redistribution | non | crise flash-crash globale de 2039 |
| signal | 2030-2050 | medecine_predictive_ia | sante_biotechnologies | non | lancement commercial des premiers bilans prédictifs IA 2036 |
| signal | 2035-2050 | dedollarisation_progressive | systeme_economique_redistribution | non | crise de la dette souveraine de 2041 |
| signal | 2035-2055 | fusion_experimentale | energie_ressources_critiques | oui | premier réacteur à fusion pilote commercial 2052 |
| evenement | 2039 | submersion_tuvalu_acte_fondateur | climat_environnement_global, gouvernance_institutions, organisation_territoires, frontieres_du_systeme | — | Tuvalu submergée, premier État post-territorial naît 2039 |
| evenement | 2041 | encheres_terres_rares_groenland | energie_ressources_critiques, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | Groenland vend ses terres rares aux enchères mondiales 2041 |
| evenement | 2044 | exode_midwest_grands_lacs | demographie_mobilite_humaine, organisation_territoires, gouvernance_institutions, climat_environnement_global | — | 18 millions fuient le Midwest désertifié vers les Lacs 2044 |
| evenement | 2047 | crise_gouvernance_amazonie | climat_environnement_global, geopolitique_conflits, gouvernance_institutions, organisation_territoires | — | Belém, théâtre d'une confrontation souveraineté-milices corporatives 2047 |
| evenement | 2051 | secession_great_lakes_compact | organisation_territoires, gouvernance_institutions, geopolitique_conflits | — | Compact des Grands Lacs proclame sa souveraineté lacustre 2051 |
| evenement | 2055 | accord_carbone_amazonie_blocs | climat_environnement_global, gouvernance_institutions, geopolitique_conflits, energie_ressources_critiques | — | Belém signe le pacte carbone amazonie fracture 2055 |
| evenement | 2059 | incident_passage_arctique | geopolitique_conflits, frontieres_du_systeme, energie_ressources_critiques | — | Convoi arctique saisi, premières armes tirées 2059 |
| evenement | 2073 | emeutes_algorithme_sao_paulo | gouvernance_institutions, technologie_information, organisation_territoires | — | Favelas décodent le SPAAR, soulèvement urbain São Paulo 2073 |
| evenement | 2098 | nairobi_biorevenu_pilote_2098 | sante_biotechnologies, systeme_economique_redistribution, systemes_productifs_travail, gouvernance_institutions, valeurs_culture_tempo_sociale | — | Nairobi lance le bio-revenu universel algorithmique 2098 |
