# Et si ? — Pandémie de peste pulmonaire

*Simulation du 2026-10-23 18:20 — lecture seule, rien n'a été injecté (simulateur v8.25).*

En 2043, une souche de peste pulmonaire résistante aux antibiotiques se diffuse sur tous les continents et tue un quart de la population mondiale en trois ans. Villes désertées, chaînes de production rompues, frontières fermées, effondrement des systèmes de santé, puis lente recomposition.

**Faits imposés à la lecture IA** :
- La pandémie tue environ 25 % de la population mondiale entre 2043 et 2046, sur tous les continents, plus fortement dans les villes denses.
- Aucun traitement efficace avant le début des années 2050 ; la maladie devient ensuite endémique et contrôlée.
- La population mondiale ne retrouve pas son niveau de 2042 avant la fin du siècle.

- **Apparition** : 2043 · **Persistance** : — (mode **rupture** : l'équilibre du scénario est déplacé pour de bon) · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098
- **Carte** : élément déclaré sans effet territorial (`carte: non`), aucune proposition de carte retenue
- Déclaré : **demographie_mobilite_humaine** — force 25, aggrave ↑, montée sur 3 ans
- Déclaré : **sante_biotechnologies** — force 25, aggrave ↑, montée sur 3 ans
- Déclaré : **systemes_productifs_travail** — force 18, aggrave ↑, montée sur 4 ans
- Déclaré : **systeme_economique_redistribution** — force 15, aggrave ↑, montée sur 5 ans
- Déclaré : **frontieres_du_systeme** — force 15, aggrave ↑, montée sur 3 ans
- Déclaré : **gouvernance_institutions** — force 12, aggrave ↑, montée sur 5 ans
- Déclaré : **organisation_territoires** — force 10, aggrave ↑, montée sur 6 ans
- Déclaré : **climat_environnement_global** — force 5, apaise ↓, montée sur 10 ans
- ⚠ `persistance` sans objet en mode rupture (le déplacement est permanent) : ignorée

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## breakdown

Apparu en 2043 dans le scénario breakdown, Pandémie de peste pulmonaire agit d'abord sur santé biotechnologies, frontières du système, gouvernance institutions, démographie mobilité humaine, organisation territoires et 3 autres. Son effet le plus fort aggrave santé biotechnologies, avec un écart maximal de +13,5 points vers 2046. Par propagation, technologie information réagit à son tour environ 8 ans après l'apparition (+0,6 points au plus fort). En 2098, il en subsiste +10,7 points sur santé biotechnologies.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| sante_biotechnologies | 85,0 → 99,0 | 89,3 | 100,0 | **+10,7** | direct |
| frontieres_du_systeme | 85,0 → 96,4 | 91,4 | 100,0 | **+8,6** | direct |
| gouvernance_institutions | 80,0 → 90,7 | 93,5 | 99,9 | **+6,4** | direct |
| demographie_mobilite_humaine | 90,0 → 99,9 | 96,6 | 100,0 | **+3,4** | direct |
| valeurs_culture_tempo_sociale | 90,0 | 95,4 | 97,5 | **+2,1** | propagé |
| climat_environnement_global | 95,0 → 90,0 | 99,6 | 98,0 | **-1,6** | direct |
| organisation_territoires | 90,0 → 97,6 | 98,6 | 100,0 | **+1,4** | direct |
| systeme_economique_redistribution | 95,0 → 100,0 | 99,3 | 100,0 | **+0,7** | direct |
| energie_ressources_critiques | 96,0 | 99,3 | 99,9 | **+0,6** | propagé |
| systemes_productifs_travail | 95,0 → 100,0 | 99,4 | 100,0 | **+0,6** | direct |

**Repères** :
- sante_biotechnologies (direct) : pic +13,5 vers 2046
- frontieres_du_systeme (direct) : pic +12,3 vers 2066
- gouvernance_institutions (direct) : pic +10,5 vers 2048
- demographie_mobilite_humaine (direct) : pic +8,5 vers 2045

**Tensions** : 42 sans l'hypothèse → 42 avec.

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

La pandémie de peste pulmonaire résistante (2043-2046) accélère brutalement la fragmentation du monde Ourrassol en ciblant les zones urbaines denses et les systèmes de santé déjà fragiles. Elle ne crée pas de nouveaux territoires, mais renforce les logiques de repli régional, de contrôle des flux et de privatisation des ressources critiques. Les entités directement liées aux nœuds logistiques, aux villes-portuaires et aux corridors d'approvisionnement sont les plus touchées, tandis que les zones stables ou émergentes (comme l'Arctique Nordark ou l'Australie) encaissent le choc sans basculer. Le scénario breakdown passe d'une lente désintégration à une crise aiguë, mais évite une apocalypse : la recomposition s'amorce dès les années 2050, avec des acteurs adaptés à un monde où la mobilité humaine et la gouvernance centralisée sont durablement affaiblies. _(ampleur : forte)_

**Trajectoires d'entités**
- Ligue Méditerranéenne des Villes-États Portuaires (`ligue_mediterraneenne_des_villes_etats_portuaires_breakdown`) : émergent → **ascendant** — Les villes-portuaires méditerranéennes deviennent des hubs de survie et de recomposition politique, capitalisant sur leur capacité à contrôler les flux maritimes et à imposer des quarantaines.
- Bloc de Johannesburg (`bloc_de_johannesburg_breakdown`) : émergent → **ascendant** — Johannesburg émerge comme un pôle de stabilité relative en Afrique australe, attirant les flux de réfugiés et les investissements résiduels.
- Conglométrat sino-sibérien Bohai Transit (`conglometrat_sino_siberien_bohai_transit_breakdown`) : émergent → **mature** — Le corridor sino-sibérien se renforce en devenant un axe vital pour les échanges intra-asiatiques, moins dépendant des flux globaux.
- Ligue Hanséatique Baltique — Le Sceau du Gotland (`hanse_baltique_breakdown`) : ascendant → **dominant** — La Ligue Hanséatique Baltique consolide son contrôle sur les ports de la mer Baltique, devenant un acteur clé de la logistique nord-européenne post-pandémie.
- Milices Extractivistes du Bassin du Congo (`milices_extractivistes_du_bassin_du_congo_breakdown`) : émergent → **déclinant** — L'effondrement démographique et les quarantaines réduisent leur capacité à exploiter les ressources du Kivu, les rendant moins centrales.

**Relations**
- opposition nouvelle : Ligue Méditerranéenne des Villes-États Portuaires ↔ Carthage Nord Nexcore — Le Joug du Détroit — La Ligue conteste l'hégémonie de Carthage Nord sur les flux méditerranéens, notamment les contrôles sanitaires et les taxes imposées aux navires.
- opposition nouvelle : Compact des Grands Lacs — Le Mur d'Eau ↔ États Fragmentés Nationalisant les Stocks — Le Compact des Grands Lacs entre en conflit avec les États voisins qui tentent de saisir ses stocks d'eau et de médicaments.
- alliance nouvelle : Kalaallit Nunaat Sovereign Fund — Fonds des Glaces Libérées ↔ Factions Militaires Résiduelles de l'Ex-OTAN Nordique — Le Fonds des Glaces Libérées s'allie avec les factions militaires nordiques pour sécuriser les corridors arctiques et les bases logistiques.
- opposition nouvelle : Bloc de Johannesburg ↔ Milices Extractivistes du Bassin du Congo — Johannesburg tente de limiter l'influence des milices du Kivu sur les routes commerciales vers l'Afrique australe.
- alliance nouvelle : Conglométrat sino-sibérien Bohai Transit ↔ Seigneuries Logistiques Armées — Bohai Transit s'appuie sur les seigneuries logistiques pour sécuriser ses convois en échange de ressources et de protection.
- alliance nouvelle : Front Humanitaire d'Urgence Non Affilié ↔ Communautés Religieuses des Relais Physiques — Les deux entités collaborent pour acheminer des secours et des informations dans les zones sinistrées, malgré leurs différences idéologiques.

**Statut des zones**
- Afrique de l'Ouest – Nœuds Lagos et Sahel (`afrique_de_louest_lagos_sahel`) : fragmenté → **en_declin** — La pandémie décime les populations urbaines de Lagos et du Sahel, affaiblissant durablement les structures politiques et économiques de la région.
- Espace Nord-Américain Fragmenté (`espace_nord_americain_fragmente`) : fragmenté → **en_declin** — Les États-Unis et le Canada subissent un effondrement démographique et institutionnel, accélérant la fragmentation territoriale.
- Zone Golfe Persique–Levant (`zone_golfe_levant`) : fragmenté → **en_declin** — La pandémie aggrave les tensions géopolitiques et économiques dans une région déjà instable, réduisant son influence résiduelle.

**Nouvelles entités plausibles**
- Quarantaines Permanentes du Détroit de Gibraltar (arc_sahelo_mediterraneen) [territoire] : Zone de contrôle sanitaire militarisée entre l'Europe et l'Afrique, verrouillant les flux migratoires et commerciaux. — La pandémie impose la création de zones tampons pour limiter la propagation de la maladie, devenant des entités politiques de facto.
- Réseau des Villes-Sanctuaires Méditerranéennes (arc_sahelo_mediterraneen) [réseau] : Alliance informelle de villes portuaires (Marseille, Barcelone, Tunis) offrant des havres sanitaires et logistiques aux populations déplacées. — Les villes-portuaires s'organisent pour mutualiser leurs ressources médicales et sécuriser leurs accès maritimes.
- Corporation des Bio-Surveillants du Sahel (afrique_de_louest_lagos_sahel) [entreprise] : Entité privée contrôlant les tests, les quarantaines et les passeports sanitaires dans les corridors ouest-africains. — Le vide institutionnel permet à des acteurs privés de monopoliser la gestion sanitaire, devenant des pouvoirs parallèles.

_Propositions écartées au contrôle (4) : trajectoire : carthage_nord_nexcore_breakdown déjà dominant (aucun changement) ; trajectoire : grandes_lacs_compact_eau_breakdown déjà dominant (aucun changement) ; trajectoire : kalaallit_nunaat_sovereign_fund_breakdown déjà dominant (aucun changement) ; statut de zone : geneve_bunker_institutions → disparu écarté, hypothèse sans effet territorial (`carte: non`)_

### Passe exhaustive (IA, toutes les fiches — rien n'est écrit)

160 fiche(s) relue(s) en 11 lot(s).
Verdicts : **3 fiche(s) à corriger**, 137 avec des changements possibles seulement, 20 inchangée(s).

_Contre-lecture des obligatoires : 22 vérifié(s), 3 confirmé(s), 19 rétrogradé(s) en possible._

#### Obligatoire — la fiche devient fausse sans ce changement

**Textes**
- instance Les Fragments NexCore (`nexcore_breakdown`) : « NexCore s'est fragmenté en 2051 lors du collapse des infrastructures numériques mondiales » — contredit par : La pandémie de 2043-2046 a provoqué un effondrement des infrastructures bien avant 2051. — La pandémie a accéléré la rupture des interconnexions globales, rendant la date de 2051 trop tardive pour la fragmentation de NexCore. [lien variable : frontieres_du_systeme (+8.6)]
- instance Os Algoritmos Quebrados — Fragmentos da RPDA (`rede_paulista_de_distribuicao_algoritmica_breakdown`) : « sans mise à jour des données démographiques depuis 2091 » — contredit par : La pandémie de 2043-2046 a tué 25 % de la population mondiale, rendant les données démographiques obsolètes bien avant 2091. — La date de 2091 est fausse : les données sont devenues inutilisables dès 2046. [lien variable : demographie_mobilite_humaine (+3.4)]
- evenement L'Exode des Grands Brûlés — La Déroute du Bureau des Résidus (`exode_midwest_grands_lacs_breakdown`) : « L'été 2044 marque la fin du Midwest habitable » — contredit par : La pandémie de peste pulmonaire (2043-2046) rend impossible la survie dans le Midwest dès 2043, et non 2044. — La pandémie (2043-2046) et ses conséquences (effondrement des systèmes de santé, désertification des villes) rendent le Midwest inhabitable dès 2043, et non 2044. [lien variable : demographie_mobilite_humaine (+3.4), sante_biotechnologies (+10.7)]

#### Possible — conséquence plausible, la fiche reste vraie sans elle

_Rétrogradés d'obligatoire à possible par les contrôles : 21 changement de degré, 9 contre-lecture nuance, 8 lien territoire alors qu'aucun territoire précis n'est touché, 6 contre-lecture aggravation, 5 extrait introuvable dans la fiche, 4 atténue le rôle sans le contredire, 2 contre-lecture omission, 2 contre-lecture chronologie, 1 au conditionnel, 1 élargit le rôle sans le contredire._

**À lire en priorité (20 fiches sur 138)** — choisies et ordonnées par l'IA

- **Brigades Médicales Itinérantes** (`brigades_medicales_itinerantes_breakdown`) — _Effondrement des systèmes de santé formels, nécessité critique des brigades médicales itinérantes_
  - Brigades Médicales Itinérantes (`brigades_medicales_itinerantes_breakdown`) : émergent → **ascendant** — La pandémie détruit les systèmes de santé formels, rendant les brigades médicales itinérantes indispensables et accélérant leur ascension. [lien variable : sante_biotechnologies (+10.7)] _(rétrogradé : changement de degré)_ — contredit : Le rôle décrit les brigades comme 'l'un des derniers filets de soin fonctionnels', mais leur trajectoire reste 'émergent'.
- **Collectifs de Santé Communautaire Autogérée** (`collectifs_de_sante_communautaire_autogeree_breakdown`) — _Remplacement des systèmes de santé publics effondrés par des collectifs autogérés_
  - Collectifs de Santé Communautaire Autogérée (`collectifs_de_sante_communautaire_autogeree_breakdown`) : émergent → **ascendant** — La pandémie de peste pulmonaire résistante a provoqué l'effondrement des systèmes de santé publics, rendant les collectifs de santé communautaires indispensables et incontournables. [lien variable : sante_biotechnologies (+10.7)] _(rétrogradé : changement de degré)_ — contredit : La fiche ne mentionne pas l'impact de la pandémie sur les systèmes de santé, alors que celle-ci les a fait s'effondrer.
  - instance Collectifs de Santé Communautaire Autogérée (`collectifs_de_sante_communautaire_autogeree_breakdown`) : « Dans un contexte de breakdown, ces collectifs pallient l'effondrement des systèmes de santé publics en organisant des soins de base à l'échelle communautaire » — contredit par : La pandémie a provoqué cet effondrement, ce qui n'est pas mentionné dans la fiche. — La fiche doit explicitement lier l'effondrement des systèmes de santé à la pandémie pour rester vraie. [lien variable : sante_biotechnologies (+10.7)] _(rétrogradé : contre-lecture omission)_ — La phrase ne mentionne pas la pandémie comme cause de l'effondrement, mais cela n'est pas contradictoire. La pandémie peut être une cause parmi d'autres.
- **Réseaux Noirs Pharmaceutiques** (`reseaux_noirs_pharmaceutiques_breakdown`) — _Vide pharmaceutique comblé par les réseaux noirs, variable sante_biotechnologies +10.7_
  - Réseaux Noirs Pharmaceutiques (`reseaux_noirs_pharmaceutiques_breakdown`) : émergent → **ascendant** — La pandémie de peste pulmonaire résistante (2043-2046) et l'effondrement des systèmes de santé officiels (variable sante_biotechnologies à +10.7) rendent ces réseaux incontournables pour les populations abandonnées, les faisant passer d'émergents à ascendants. [lien variable : sante_biotechnologies (+10.7)] _(rétrogradé : changement de degré)_ — contredit : La trajectoire 'émergent' devient fausse car l'effondrement des systèmes de santé officiels (variable sante_biotechnologies) rend ces réseaux indispensables et en forte croissance.
  - instance Réseaux Noirs Pharmaceutiques (`reseaux_noirs_pharmaceutiques_breakdown`) : « Dans le scénario breakdown, comblent le vide laissé par l'effondrement des systèmes de santé officiels, devenant paradoxalement des fournisseurs de soins de facto pour des populations abandonnées » — Le rôle de ces réseaux s'élargit naturellement avec la pandémie, mais la phrase reste vraie sans modification. [lien variable : sante_biotechnologies (+10.7)] _(douteux : élargit le rôle sans le contredire)_
- **Pirates Biologiques Open-Source** (`pirates_biologiques_open_source_breakdown`) — _Contournement des infrastructures sanitaires défaillantes, réponse open-source à la crise_
  - Pirates Biologiques Open-Source (`pirates_biologiques_open_source_breakdown`) : émergent → **ascendant** — Leur rôle de contournement des infrastructures sanitaires défaillantes devient central, pas seulement émergent. [lien variable : sante_biotechnologies (+10.7)] _(rétrogradé : changement de degré)_ — contredit : La pandémie de peste pulmonaire résistante rend les solutions biologiques bricolées indispensables, alors que les systèmes officiels sont effondrés.
- **Réseaux de Soigneurs Traditionnels** (`reseaux_de_soigneurs_traditionnels_breakdown`) — _Devenus principale source de soins dans les zones rurales, mobilité humaine réduite_
  - Réseaux de Soigneurs Traditionnels (`reseaux_de_soigneurs_traditionnels_breakdown`) : émergent → **ascendant** — Ils ne comblent plus seulement un vide, mais deviennent la principale source de soins dans les zones rurales. [lien variable : sante_biotechnologies (+10.7)] _(rétrogradé : changement de degré)_ — contredit : La pandémie a détruit les infrastructures médicales formelles, rendant leur rôle de soin de proximité indispensable.
- **Les Bouches de Sfax — Relais de la Faim Juste** (`sfax_relais_bouches_breakdown`) — _Réseau logistique alimentaire dominant, rupture des chaînes d'approvisionnement_
  - Les Bouches de Sfax — Relais de la Faim Juste (`sfax_relais_bouches_breakdown`) : ascendant → **dominant** — La pandémie et ses conséquences (désertification des villes, rupture des chaînes d'approvisionnement) font de ce réseau un acteur dominant pour la survie régionale. [lien variable : demographie_mobilite_humaine (+3.4), sante_biotechnologies (+10.7)] _(rétrogradé : changement de degré)_ — contredit : La trajectoire 'ascendant' devient fausse car la pandémie et l'effondrement des flux (variables demographie_mobilite_humaine et sante_biotechnologies) rendent ce réseau indispensable pour la survie alimentaire et logistique en Méditerranée.
  - instance Les Bouches de Sfax — Relais de la Faim Juste (`sfax_relais_bouches_breakdown`) : « Réseau informel de distribution alimentaire et logistique basé à Sfax, structuré autour de relais humains contrôlant les flux de bouche dans les zones portuaires méditerranéennes en déliquescence » — Leur rôle prend plus de poids avec la pandémie, mais la phrase reste vraie sans modification. [lien variable : demographie_mobilite_humaine (+3.4)] _(douteux : atténue le rôle sans le contredire)_
- **Réseau Logistique Criminel Concurrent** (`reseau_logistique_criminel_concurrent_breakdown`) — _Chaos logistique accru, quasi-État dans les marges post-effondrement_
  - Réseau Logistique Criminel Concurrent (`reseau_logistique_criminel_concurrent_breakdown`) : émergent → **dominant** — La pandémie a accru le chaos logistique, renforçant leur position de quasi-État dans les marges. [lien variable : frontieres_du_systeme (+8.6), systeme_economique_redistribution (+0.7)]
- **Cartels Logistiques Régionaux** (`cartels_logistiques_regionaux_breakdown`) — _Fragmentation des chaînes d'approvisionnement, acteurs logistiques régionaux indispensables_
  - Cartels Logistiques Régionaux (`cartels_logistiques_regionaux_breakdown`) : émergent → **ascendant** — La pandémie accélère la fragmentation des chaînes d'approvisionnement et renforce le rôle des acteurs logistiques régionaux, rendant leur ascension plus probable. [lien variable : frontieres_du_systeme (+8.6), systeme_economique_redistribution (+0.7)]
  - instance Cartels Logistiques Régionaux (`cartels_logistiques_regionaux_breakdown`) : « Dans un scénario de breakdown, elles comblent le vide laissé par l'effondrement des chaînes d'approvisionnement centralisées, devenant des acteurs de pouvoir incontournables mais fragmentant davantage la cohérence territoriale » — Le rôle des cartels logistiques est renforcé par la pandémie, qui accentue l'effondrement des chaînes centralisées. [lien variable : frontieres_du_systeme (+8.6)] _(douteux : élargit le rôle sans le contredire)_
- **Consortiums Logistiques Agro-Corporatifs** (`consortiums_logistiques_agro_corporatifs_breakdown`) — _Rupture des chaînes logistiques agro-corporatives, prédateurs de l'effondrement_
  - Consortiums Logistiques Agro-Corporatifs (`consortiums_logistiques_agro_corporatifs_breakdown`) : émergent → **ascendant** — La pandémie accélère la rupture des chaînes logistiques, ce qui pourrait renforcer leur rôle de prédateurs de l'effondrement et les faire progresser vers une trajectoire ascendante, sans que cela soit obligatoire. [lien variable : frontieres_du_systeme (+8.6), systeme_economique_redistribution (+0.7)]
  - instance Consortiums Logistiques Agro-Corporatifs (`consortiums_logistiques_agro_corporatifs_breakdown`) : « Dans le chaos du breakdown, les Consortiums Logistiques Agro-Corporatifs se repositionnent comme prédateurs de l'effondrement : là où les États reculent et où les chaînes mondiales se rompent, ils tentent d'imposer des monopoles régionaux sur la distribution alimentaire, transformant la dépendance logistique en » — La pandémie rend leur rôle encore plus pertinent, mais la phrase reste vraie sans modification. [lien variable : frontieres_du_systeme (+8.6)] _(douteux : atténue le rôle sans le contredire)_
- **Blocs de Contrôle des Couloirs d'Approvisionnement Stratégiques** (`blocs_de_controle_des_couloirs_d_approvisionnement_strategiques_breakdown`) — _Contrôle des couloirs d'approvisionnement stratégiques, fragmentation logistique accélérée_
  - Blocs de Contrôle des Couloirs d'Approvisionnement Stratégiques (`blocs_de_controle_des_couloirs_d_approvisionnement_strategiques_breakdown`) : émergent → **ascendant** — La pandémie accélère la fragmentation des chaînes logistiques, ce qui peut renforcer le rôle de ces blocs dans le contrôle des flux stratégiques. [lien variable : frontieres_du_systeme (+8.6)]
- **Flux Migratoires Non Intégrables** (`flux_migratoires_non_integrables_breakdown`) — _Crise démographique et logistique sans précédent, saturation des flux migratoires_
  - Flux Migratoires Non Intégrables (`flux_migratoires_non_integrables_breakdown`) : émergent → **dominant** — La pandémie crée une crise démographique et logistique sans précédent, ce qui transforme ces flux migratoires en un vecteur central de l'effondrement des mécanismes de gouvernance territoriale, bien au-delà d'un simple rôle émergent. [lien variable : demographie_mobilite_humaine (+3.4), gouvernance_institutions (+6.4)] _(rétrogradé : changement de degré)_ — contredit : La pandémie tue 25 % de la population mondiale et rompt les chaînes logistiques, ce qui rend les flux migratoires encore plus massifs et ingérables qu'avant 2043.
  - instance Flux Migratoires Non Intégrables (`flux_migratoires_non_integrables_breakdown`) : « les flux migratoires non intégrables saturent successivement les nœuds urbains résiduels, dissolvent les derniers pactes d'accueil régionaux et forcent les entités territoriales encore stables à se militariser » — contredit par : Les villes denses sont les plus touchées par la pandémie (25 % de mortalité), ce qui réduit leur capacité à absorber ces flux migratoires dès 2043-2046. — La phrase suppose que les nœuds urbains résiduels existent encore comme points d'accueil, alors que la pandémie les a déjà fortement affaiblis dès 2043-2046. [lien variable : demographie_mobilite_humaine (+3.4), sante_biotechnologies (+10.7)] _(rétrogradé : atténue le rôle sans le contredire)_
- **ONG de Gestion Migratoire Survivantes** (`ong_de_gestion_migratoire_survivantes_breakdown`) — _Gestion migratoire centrale, effondrement des institutions étatiques_
  - ONG de Gestion Migratoire Survivantes (`ong_de_gestion_migratoire_survivantes_breakdown`) : émergent → **ascendant** — L'effondrement des institutions étatiques et la crise démographique aiguë obligent ces ONG à jouer un rôle central, bien au-delà d'un simple palliatif émergent. [lien variable : demographie_mobilite_humaine (+3.4)] _(rétrogradé : changement de degré)_ — contredit : La pandémie de 2043-2046 tue 25 % de la population mondiale et désorganise les flux migratoires, rendant la gestion des déplacements une priorité critique pour les survivants.
- **Communautés Paysannes Réfugiées** (`communautes_paysannes_refugiees_breakdown`) — _Flux migratoires accrus, pression sur les territoires d'accueil_
  - Communautés Paysannes Réfugiées (`communautes_paysannes_refugiees_breakdown`) : émergent → **ascendant** — La pandémie augmente les flux migratoires et la pression sur les territoires d'accueil, renforçant le rôle des communautés paysannes réfugiées. [lien variable : demographie_mobilite_humaine (+3.4), gouvernance_institutions (+6.4)]
  - instance Communautés Paysannes Réfugiées (`communautes_paysannes_refugiees_breakdown`) : « Dans le scénario breakdown, incarnent la fragmentation des systèmes productifs alimentaires et la pression démographique sur les territoires d'accueil, tout en portant des savoir-faire agricoles menacés de disparition » — contredit par : La pandémie a tué 25 % de la population mondiale, ce qui modifie radicalement la pression démographique et les flux migratoires. — La fiche doit mentionner que la pandémie a amplifié ces dynamiques pour rester vraie. [lien variable : demographie_mobilite_humaine (+3.4)] _(rétrogradé : élargit le rôle sans le contredire)_
- **Milices Agro-Défensives Locales** (`milices_agro_defensives_locales_breakdown`) — _Sécurité territoriale locale, affaiblissement des institutions étatiques_
  - Milices Agro-Défensives Locales (`milices_agro_defensives_locales_breakdown`) : émergent → **ascendant** — La pandémie affaiblit les institutions étatiques et renforce les logiques de contrôle territorial local, élargissant le rôle des milices agro-défensives. [lien variable : gouvernance_institutions (+6.4), organisation_territoires (+1.4)]
  - instance Milices Agro-Défensives Locales (`milices_agro_defensives_locales_breakdown`) : « Ils assurent une forme de sécurité territoriale de substitution là où les institutions ont cédé, contrôlant l'accès aux zones cultivables et aux stocks alimentaires » — La pandémie accélère l'effondrement des institutions, élargissant le rôle des milices comme acteurs de sécurité locale. [lien variable : gouvernance_institutions (+6.4)] _(douteux : élargit le rôle sans le contredire)_
- **Milices d'Accaparement Hydrique** (`milices_d_accaparement_hydrique_breakdown`) — _Contrôle hydrique critique, effondrement des régulations publiques_
  - Milices d'Accaparement Hydrique (`milices_d_accaparement_hydrique_breakdown`) : émergent → **ascendant** — La pandémie a accéléré l'effondrement des régulations hydriques publiques (gouvernance_institutions) et réduit la mobilité humaine, rendant les milices d'accaparement plus indispensables pour contrôler les ressources critiques dans un contexte de pénurie. [lien variable : gouvernance_institutions (+6.4) et demographie_mobilite_humaine (+3.4)]
- **Factions Para-Étatiques Hydriques** (`factions_para_etatiques_hydriques_breakdown`) — _Fragmentation du pouvoir autour des ressources hydriques, mobilité réduite_
  - Factions Para-Étatiques Hydriques (`factions_para_etatiques_hydriques_breakdown`) : émergent → **ascendant** — La pandémie accélère la fragmentation du pouvoir territorial autour des ressources hydriques, ce qui renforce le rôle de ces factions comme acteurs de gouvernance coercitive locale. [lien variable : gouvernance_institutions (+6.4), demographie_mobilite_humaine (+3.4)]
- **Les Confédérations du Seuil Dernier** (`collectifs_du_seuil_breakdown`) — _Doctrine apocalyptique validée, attractivité renforcée dans un monde en crise_
  - Les Confédérations du Seuil Dernier (`collectifs_du_seuil_breakdown`) : ascendant → **dominant** — La pandémie valide leur doctrine apocalyptique et renforce leur attractivité dans un monde en crise, favorisant leur ascension. [lien variable : valeurs_culture_tempo_sociale (+2.1), demographie_mobilite_humaine (+3.4)]
- **Communes Libres du Rust Belt — Les Forges du Commun** (`mouvement_des_communes_du_rust_belt_breakdown`) — _Effondrement des grands employeurs, légitimité accrue des communes autogérées_
  - Communes Libres du Rust Belt — Les Forges du Commun (`mouvement_des_communes_du_rust_belt_breakdown`) : ascendant → **dominant** — La pandémie a accéléré l'effondrement des grands employeurs et des institutions, rendant les communes autogérées du Rust Belt plus attractives et légitimes comme modèles de survie. [lien variable : demographie_mobilite_humaine (+3.4) et gouvernance_institutions (+6.4)]
  - instance Communes Libres du Rust Belt — Les Forges du Commun (`mouvement_des_communes_du_rust_belt_breakdown`) : « Premier mouvement de communes urbaines à avoir atteint une taille critique dans les années 2030 » — La pandémie a pu renforcer leur visibilité comme modèle alternatif, élargissant leur influence culturelle et sociale. [lien variable : valeurs_culture_tempo_sociale (+2.1)] _(douteux : variable touchée seulement par propagation, élargit le rôle sans le contredire, extrait introuvable dans la fiche)_ _(extrait introuvable dans la fiche)_
- **Communes Libres du Rust Belt — Les Forges du Commun** (`communes_rust_belt_breakdown`) — _Effondrement des structures étatiques fédérales, nœuds de résistance locale_
  - Communes Libres du Rust Belt — Les Forges du Commun (`communes_rust_belt_breakdown`) : ascendant → **dominant** — La pandémie accélère l'effondrement des structures étatiques fédérales, ce qui pourrait renforcer leur rôle de nœuds de résistance locale et les faire progresser vers une position dominante, sans que cela soit obligatoire. [lien variable : demographie_mobilite_humaine (+3.4), gouvernance_institutions (+6.4)]
  - instance Communes Libres du Rust Belt — Les Forges du Commun (`communes_rust_belt_breakdown`) : « Après l'effondrement des structures étatiques fédérales, ces communes organisent la survie locale autour de ressources partagées et de milices civiles » — La pandémie rend cet effondrement plus brutal et probable, mais la phrase reste vraie sans modification. [lien variable : gouvernance_institutions (+6.4)] _(douteux : atténue le rôle sans le contredire)_
- **Ligue du Sahel Numérique — Les Nœuds d'Agadez** (`agadez_ligue_sahel_numerique_breakdown`) — _Repli régional renforcé, décentralisation des réseaux de soins traditionnels_
  - Ligue du Sahel Numérique — Les Nœuds d'Agadez (`agadez_ligue_sahel_numerique_breakdown`) : ascendant → **dominant** — La pandémie réduit la mobilité humaine et renforce les logiques de repli régional, ce qui peut accroître l'importance des réseaux décentralisés comme la Ligue du Sahel Numérique pour les communautés isolées. [lien variable : demographie_mobilite_humaine (+3.4)]
  - alliance nouvelle : Ligue du Sahel Numérique — Les Nœuds d'Agadez ↔ Réseaux de Soigneurs Traditionnels — L'effondrement des systèmes de santé formels peut pousser la Ligue à s'allier avec des réseaux de soins traditionnels pour compenser l'absence de structures médicales. [lien variable : sante_biotechnologies (+10.7)]

**Autres fiches avec des changements possibles (118)**
- Les Fantômes des Seuils : trajectoire résiduel → disparu ; texte « Ces entités résiduelles opèrent comme des observatoires… »
- Carthage Nord Nexcore — Le Joug du Détroit : trajectoire dominant → mature ; texte « Il contrôle des infrastructures portuaires et logistiques… »
- Les Venelles — Corridors Eurasiens Convoyage : trajectoire déclinant → résiduel ; alliance rompue avec Brigades Médicales Itinérantes
- Les Enclaves du Nord — Fragments Finlandais : trajectoire déclinant → résiduel
- États Fragmentés Nationalisant les Stocks : trajectoire émergent → ascendant ; opposition nouvelle avec Milices Extractivistes du Bassin du Congo
- Factions Militaires Résiduelles de l'Ex-OTAN Nordique : trajectoire émergent → ascendant
- Factions Sécessionnistes Agrariennes du Désert : trajectoire émergent → ascendant
- Frente Sertão Livre — Les Noeuds du Dedans : trajectoire ascendant → dominant
- Front Humanitaire d'Urgence Non Affilié : trajectoire émergent → ascendant ; texte « Assure une continuité minimale de secours et de… »
- Fronts Populistes Anti-Technocratiques : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, ils incarnent la pression… »
- Résidu de Genève — Le Palais des Fantômes : trajectoire disparu → historique ; texte « Vestige institutionnel de l'ancien système onusien et… »
- Compact des Grands Lacs — Le Mur d'Eau : trajectoire dominant → mature ; texte « Anciennement accord interétatique, il s'est mué en pacte de… »
- Milices de Contrôle Territorial : trajectoire émergent → ascendant ; texte « nées du vide laissé par l'effondrement progressif des États… »
- Réseau des Courriers Nomades Sahélo-Méditerranéens : trajectoire émergent → ascendant
- Réseau des Organisations Humanitaires Hors Cadre Onusien : trajectoire émergent → ascendant
- Réseaux de solidarité horizontale post-effondrement : trajectoire émergent → ascendant
- Seigneuries Logistiques Armées : trajectoire émergent → ascendant
- Tour Bcuc Genève — Le Comptoir des Ruines : trajectoire disparu → historique
- Fragments Terrafond : texte « Ce qui fut la Coopérative Terrafond n'existe plus comme… »
- Les Protocoles Fantômes : texte « Les derniers protocoles de régulation IA ont été abandonnés… »
- Chambre des Recours Algorithmiques — Ce qu'il en reste : trajectoire résiduel → disparu
- Autorité du Passage Arctique — Ce qu'il en reste : trajectoire transformé → disparu
- Amara Diallo-Nkosi : trajectoire résiduel → disparu
- Pacte des Souverains — Ce qui en reste : trajectoire transformé → disparu
- Nordark — Les Terres du Dessous : trajectoire ascendant → dominant
- Cités-États Sécessionistes : trajectoire émergent → ascendant
- Les Racines de l'Aube : trajectoire résiduel → marginal ; texte « Ce réseau clandestin et décentralisé agit comme un… »
- Collectif des Climatologues Sans État : trajectoire émergent → ascendant
- Collectif Hackers Décroissance-Infrastructure : trajectoire émergent → ascendant
- Collectifs de Gardiens-Archivistes Itinérants : trajectoire émergent → ascendant
- Collectifs de Hackers Archivistes des Interstices Réseaux : trajectoire émergent → ascendant
- Collectifs de Réparation Énergétique : trajectoire émergent → ascendant
- Communautés Religieuses des Relais Physiques : trajectoire émergent → ascendant
- Communautés Rurales Autogérées des Nœuds de Survie : trajectoire émergent → ascendant
- communautés rurales autonomes : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, les communautés rurales… »
- Communes Libres du Rust Belt — Les Forges du Commun : trajectoire ascendant → dominant ; texte « Zones échappant à tout contrôle institutionnel résiduel,… » ; texte « Dans les carcasses rouillées des aciéries de Pittsburgh et… »
- Compagnies de Géo-Ingénierie Privées Sans Mandat : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, elles incarnent la… »
- Consortium Énergétique Oural-Caspien : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, le Consortium Énergétique… »
- Corporations de l'Ère Pré-Effondrement à Droits de PI : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, elles bloquent ou monnayent… »
- Les Bouches du Lithium — Corridor Minier des Andes Brisées : trajectoire résiduel → marginal ; texte « Les flux d'approvisionnement y sont erratiques, négociés au… »
- Les Mères des Eaux — Delta Mekong Racines : trajectoire ascendant → dominant ; texte « Ces communautés de survie ont rompu avec les institutions… »
- Diaspora Tech Sahel : trajectoire émergent → ascendant
- Administration Résiduelle de Mourmansk — Le Bastion du Détroit Gelé : trajectoire résiduel → marginal ; alliance rompue avec Ligue Hanséatique Baltique — Le Sceau du Gotland
- Elias Mørk — Le Nœud de Bergen : trajectoire ascendant → dominant ; texte « Ancien expert en systèmes énergétiques critiques pour les… »
- Enclaves Agro-Communautaires Autonomes : trajectoire émergent → ascendant
- Enclaves Corporatives Fortifiées : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, incarnent la substitution des… »
- Enclaves Industrielles de Bergen-Tromsø : trajectoire émergent → marginal
- Enclaves Industrielles du Corridor Oural-Caspien : trajectoire émergent → marginal
- Enclaves Technologiques Survivantes : trajectoire émergent → ascendant
- Ergo-Wian Sovereign Fragments : trajectoire résiduel → marginal ; texte « Dans le chaos du *Breakdown*, les vestiges d'Ergo-Wian… »
- États-Fragments en Guerre pour les Stations Atmosphériques : trajectoire émergent → ascendant
- Factions Énergétiques Héritières des Pactes ABS : trajectoire émergent → ascendant
- Factions Étatiques Résiduelles de Souveraineté Hydrique : trajectoire émergent → ascendant
- Factions Propagandistes des Archives : trajectoire émergent → ascendant
- Fédération Russe Résiduelle — District de Mourmansk : trajectoire émergent → résiduel
- Front de Résistance aux Péages sur les Ressources : trajectoire émergent → ascendant
- Front des Blocs Régionaux du Récit des Conflits-Ressources : trajectoire émergent → ascendant
- Front Techno-Reconstructionniste : trajectoire émergent → ascendant ; texte « Dans un scénario breakdown dominé par la fragmentation… »
- Gelecek Meclisi — Les Échos du Demain : trajectoire émergent → ascendant ; texte « Dans le chaos de la fragmentation post-effondrement,… »
- Gouvernements de Forteresse Anti-Nairobi : trajectoire émergent → ascendant ; texte « Bloc de résistance institutionnelle agissant comme force… »
- Gouvernements Régionaux Résiduels Reterritorialisants : trajectoire émergent → résiduel ; texte « Dans le chaos du breakdown, ces entités constituent les… »
- Guilde des Techniciens Nomades : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, ils assurent la survie… »
- Hanse Baltique Recomposée : trajectoire émergent → ascendant
- Hyphan Raghavan — Les Mains des Nœuds Oubliés : trajectoire ascendant → dominant ; texte « Ancien technicien nomade formé dans les ruines des… »
- Ilse Varga-Holm — Les Mains des Nœuds Oubliés : trajectoire ascendant → dominant
- Ligue Eurasiatique–Coalition Pacifique : trajectoire émergent → ascendant
- Milices Contractuelles des Anciens États-Membres : trajectoire émergent → ascendant
- Milices Privées Documentées Terrain : trajectoire émergent → ascendant ; texte « elles remplissent les fonctions régaliennes minimales [...]… »
- Milices Séparatistes du Conseil des Pêcheries d'Islande : trajectoire émergent → ascendant
- Les Racines-Mères : trajectoire transformé → ascendant ; texte « Certaines branches ont embrassé une écologie du soin et de… »
- Nadia Ferreira-Sato — Les Nœuds de la Ceinture Verte : trajectoire ascendant → dominant
- Nairobi CRRC — Les Cellules du Dernier Maillage : trajectoire ascendant → dominant
- Fragments BioSyn : trajectoire transformé → ascendant ; texte « Certains segments ont été absorbés par des seigneurs… »
- Nœud Mnemos Pannonie — Les Gardiens du Danube : trajectoire ascendant → dominant
- Nœud Nordark Tromsø — Le Carrefour du Froid : trajectoire ascendant → dominant
- Les Racines-Mères — Confédération Occitane des Semences et des Mémoires : trajectoire ascendant → dominant
- Réseau de Récupération Industrielle Illicite : trajectoire émergent → ascendant
- Réseau des Anciens Financeurs Devenus Censeurs : trajectoire émergent → ascendant
- Les Veilleurs des Brumes — Réseau des Cartographes des Zones Grises : trajectoire ascendant → dominant
- Réseaux de renseignement informels issus de l'ancienne structure militaire eurasienne : trajectoire émergent → ascendant
- Saboteurs des Corridors de Transit : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, ils fragilisent les corridors… »
- Seigneuries Foncières Opportunistes : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, les seigneuries foncières… »
- Seigneurs de Guerre Agro-Territoriaux : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, ils incarnent la fragmentation… »
- Seoul Collectif Nexcore — Les Grilles de l'Entre-Deux : trajectoire ascendant → dominant ; texte « Gère des réseaux d'échange et de sécurité locale dans les… »
- Terrafond Vallée — Le Pacte des Terres Vives : trajectoire ascendant → dominant ; texte « Dans un contexte de fragmentation institutionnelle totale,… »
- Cargo Mombasa CRRC — Les Dhows de la Dernière Chance : alliance nouvelle avec Réseaux Noirs Pharmaceutiques
- Victoire Fantôme du Parti Commun : texte « Le Parti Commun remporte 41% des votes dans les territoires… »
- Les Éclats Kontinuum : texte « La Directive Kontinuum, conçue pour gouverner par… »
- Conglométrat sino-sibérien Bohai Transit : texte « Dans le scénario breakdown, Bohai Transit représente l'un… »
- Archives Neutres de Genève : texte « Elles fonctionnent moins comme une institution que comme un… »
- Fantôme de Nairobi : texte « Surnommé 'le Fantôme de Nairobi' par les correspondants de… »
- Fragments CABS — Les Semeurs de Ruines : texte « Dépourvues de leur siège central détruit lors des conflits… »
- Pacte des Gardiens de l'Amazone — Ce qui reste : texte « Héritier fracturé du Consortium Amazônia Viva, le Pacte des… »
- Confédération des Bassins Vivants : texte « Chaque bassin de vie a développé ses propres protocoles de… »
- Ligue Hanséatique Baltique — Le Sceau du Gotland : texte « La Ligue Hanséatique Baltique est une confédération de… »
- Les Vestiges des Citadelles : texte « Holdfasts mythifiés, ces enclaves fortifiées des années… »
- Lagos Intérieur Mnemos — Les Cryptes Lagunaires : texte « Dans le chaos du territoire lagunaire post-effondrement,… »
- Le Signal : texte « Seule voix qui tente encore de donner du sens au chaos… »
- Les Sentinelles des Veines Bleues : texte « Elles agissent comme un réseau de surveillance citoyenne,… »
- Ligue Méditerranéenne des Villes-États Portuaires : texte « Elle assure la continuité des échanges régionaux via ses… »
- Les Cicatrices Vertes — Massif Central Fragmenté : texte « Des communautés autonomes s'y sont établies, vivant en… »
- Kharg-9 Data Haven : texte « Infrastructure offshore ancrée dans les eaux contestées du… »
- Les Cicatrices Vertes : texte « Ces tronçons de corridors biologiques, stations… »
- Vasil Orentchev : texte « Seigneur de guerre logistique opérant dans les corridors… »
- L'Exode des Grands Brûlés — La Déroute du Bureau des Résidus : texte « Les Grands Lacs deviennent une zone de friction explosive :… »
- La Fracture de Belém — Quand le Bassin Amazonien a cessé d'être un territoire : texte « Les milices contractuelles liées aux factions énergétiques… »
- Coalition Pacifique Nord : trajectoire émergent → ascendant
- Les Veines du Nord — Consortium des Pêcheries Autonomes du Grand Nord : trajectoire ascendant → dominant
- Consortiums Énergétiques Samoïèdes du Yamal : trajectoire émergent → ascendant
- Les Éclats d'Agadez — Ce qui reste du Forum : texte « Agadez, novembre 2061. Dans la grande salle du Palais des… »
- La Révolte des Zones Mortes — Effondrement de la RPDA : texte « L'été 2073, São Paulo brûle sous un autre soleil : celui… »
- L'Éventrement de Genève : texte « Le dépôt énergétique souterrain, conçu pour alimenter les… »
- Naufrage des Mémoires du Compact : texte « Milwaukee-Basse, été 2098. Sous une chaleur étouffante, les… »
- Les Voix du Seuil — Fragments de l'Oracle : texte « Ses fragments tournent sur des serveurs hétéroclites —… »
- Lagos Est Nexcore — Les Nœuds Lagunaires : trajectoire ascendant → déclinant ; texte « Elle gère les flux d'énergie et de données entre les… »
- Les Éclats du Sahel — Fragments de la Ligue : trajectoire transformé → marginal ; texte « Certains fragments maintiennent des protocoles ouverts… »
- Ligue des Cités Littorales en Sursis : trajectoire émergent → déclinant ; texte « Elles incarnent les entités territoriales au stade terminal… »
- Administration Fédérale Résiduelle du Midwest — Les Coursiers du Protocole : texte « Sans véritable autorité centralisée, elle fonctionne comme… »

_Réponses rejetées car mal formées (36) : trajectoire : agence_stabilisation_climatique_breakdown déjà disparu (aucun changement) ; trajectoire : agence_de_regulation_des_detroits_strategiques_ards_breakdown déjà résiduel (aucun changement) ; trajectoire : archives_neutres_de_geneve_breakdown déjà résiduel (aucun changement) ; trajectoire : armada_logistique_nordique_breakdown déjà dominant (aucun changement) ; trajectoire : assemblee_territoires_breakdown déjà résiduel (aucun changement) ; trajectoire : bureau_des_territoires_residuels_breakdown déjà résiduel (aucun changement) ; trajectoire : cargo_mombasa_crrc_breakdown déjà dominant (aucun changement) ; relation agence_de_regulation_des_detroits_strategiques_ards_breakdown / brigades_medicales_itinerantes_breakdown : alliance déjà présente …_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Statuts de zone**
- [ ] 1. `afrique_de_louest_lagos_sahel` (Afrique de l'Ouest – Nœuds Lagos et Sahel) : fragmenté → en_declin
  - à la main : geographie/breakdown.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario breakdown --execute)
  - _La pandémie décime les populations urbaines de Lagos et du Sahel, affaiblissant durablement les structures politiques et économiques de la région._
- [ ] 2. `espace_nord_americain_fragmente` (Espace Nord-Américain Fragmenté) : fragmenté → en_declin
  - à la main : geographie/breakdown.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario breakdown --execute)
  - _Les États-Unis et le Canada subissent un effondrement démographique et institutionnel, accélérant la fragmentation territoriale._
- [ ] 3. `zone_golfe_levant` (Zone Golfe Persique–Levant) : fragmenté → en_declin
  - à la main : geographie/breakdown.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario breakdown --execute)
  - _La pandémie aggrave les tensions géopolitiques et économiques dans une région déjà instable, réduisant son influence résiduelle._

**Élément**
- [ ] 4. Injecter l'événement `peste_pulmonaire_2043` en mode rupture (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios ; mode_impose: rupture écrit `mode: rupture` dans chaque fiche_
- [ ] 5. ⚠ Vérifier que la fiche porte `mode: rupture` et les forces simulées (demographie_mobilite_humaine +25, sante_biotechnologies +25, systemes_productifs_travail +18, systeme_economique_redistribution +15, frontieres_du_systeme +15, gouvernance_institutions +12, organisation_territoires +10, climat_environnement_global −5)
  - event_instances/peste_pulmonaire_2043_breakdown.md ; python3 generator/trace_injection.py --slug peste_pulmonaire_2043 --type evenement --scenario breakdown
  - _le Tracer doit finir chaque ligne « Déclaré » par « rupture » et retrouver l'effet simulé ; références déplacées par le moteur (rien à faire) : sante_biotechnologies 85,0 → 99,0 ; frontieres_du_systeme 85,0 → 96,4 ; gouvernance_institutions 80,0 → 90,7 ; demographie_mobilite_humaine 90,0 → 99,9 ; climat_environnement_global 95,0 → 90,0 ; organisation_territoires 90,0 → 97,6 ; systeme_economique_redistribution 95,0 → 100,0 ; systemes_productifs_travail 95,0 → 100,0 ; au plafond, plus aucune marge pour une autre crise : demographie_mobilite_humaine, systeme_economique_redistribution, systemes_productifs_travail_
- [ ] 6. Nouvelle référence : vérifier la lisibilité du moteur
  - `python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05`
  - _S19_

**Nouvelles entités**
- [ ] 7. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie proposée, à relire
  - étape ⑤ du panneau (« Ajouter à la file »), puis python3 generator/create_entities_and_instances.py --mode custom
  - _scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 8. Ligue Méditerranéenne des Villes-États Portuaires (`ligue_mediterraneenne_des_villes_etats_portuaires_breakdown`) : émergent → ascendant
  - à la main : instances/ligue_mediterraneenne_des_villes_etats_portuaires_breakdown.md, champ `trajectoire`
  - _Les villes-portuaires méditerranéennes deviennent des hubs de survie et de recomposition politique, capitalisant sur leur capacité à contrôler les flux maritimes et à imposer des quarantaines._
- [ ] 9. Bloc de Johannesburg (`bloc_de_johannesburg_breakdown`) : émergent → ascendant
  - à la main : instances/bloc_de_johannesburg_breakdown.md, champ `trajectoire`
  - _Johannesburg émerge comme un pôle de stabilité relative en Afrique australe, attirant les flux de réfugiés et les investissements résiduels._
- [ ] 10. ⚠ Conglométrat sino-sibérien Bohai Transit (`conglometrat_sino_siberien_bohai_transit_breakdown`) : émergent → mature
  - à la main : instances/conglometrat_sino_siberien_bohai_transit_breakdown.md, champ `trajectoire`
  - _saut d'un cran (sans passer par ascendant) : garder, ou ramener à ascendant ; Le corridor sino-sibérien se renforce en devenant un axe vital pour les échanges intra-asiatiques, moins dépendant des flux globaux._
- [ ] 11. Ligue Hanséatique Baltique — Le Sceau du Gotland (`hanse_baltique_breakdown`) : ascendant → dominant
  - à la main : instances/hanse_baltique_breakdown.md, champ `trajectoire`
  - _La Ligue Hanséatique Baltique consolide son contrôle sur les ports de la mer Baltique, devenant un acteur clé de la logistique nord-européenne post-pandémie._
- [ ] 12. Milices Extractivistes du Bassin du Congo (`milices_extractivistes_du_bassin_du_congo_breakdown`) : émergent → déclinant
  - à la main : instances/milices_extractivistes_du_bassin_du_congo_breakdown.md, champ `trajectoire`
  - _L'effondrement démographique et les quarantaines réduisent leur capacité à exploiter les ressources du Kivu, les rendant moins centrales._

**Relations**
- [ ] 13. opposition nouvelle : Ligue Méditerranéenne des Villes-États Portuaires ↔ Carthage Nord Nexcore — Le Joug du Détroit
  - à la main : ajouter `carthage_nord_nexcore_breakdown` dans `oppositions` de instances/ligue_mediterraneenne_des_villes_etats_portuaires_breakdown.md
  - _La Ligue conteste l'hégémonie de Carthage Nord sur les flux méditerranéens, notamment les contrôles sanitaires et les taxes imposées aux navires._
- [ ] 14. opposition nouvelle : Compact des Grands Lacs — Le Mur d'Eau ↔ États Fragmentés Nationalisant les Stocks
  - à la main : ajouter `etats_fragmentes_nationalisant_les_stocks_breakdown` dans `oppositions` de instances/grandes_lacs_compact_eau_breakdown.md
  - _Le Compact des Grands Lacs entre en conflit avec les États voisins qui tentent de saisir ses stocks d'eau et de médicaments._
- [ ] 15. alliance nouvelle : Kalaallit Nunaat Sovereign Fund — Fonds des Glaces Libérées ↔ Factions Militaires Résiduelles de l'Ex-OTAN Nordique
  - à la main : ajouter `factions_militaires_residuelles_de_l_ex_otan_nordique_breakdown` dans `alliances` de instances/kalaallit_nunaat_sovereign_fund_breakdown.md
  - _Le Fonds des Glaces Libérées s'allie avec les factions militaires nordiques pour sécuriser les corridors arctiques et les bases logistiques._
- [ ] 16. opposition nouvelle : Bloc de Johannesburg ↔ Milices Extractivistes du Bassin du Congo
  - à la main : ajouter `milices_extractivistes_du_bassin_du_congo_breakdown` dans `oppositions` de instances/bloc_de_johannesburg_breakdown.md
  - _Johannesburg tente de limiter l'influence des milices du Kivu sur les routes commerciales vers l'Afrique australe._
- [ ] 17. alliance nouvelle : Conglométrat sino-sibérien Bohai Transit ↔ Seigneuries Logistiques Armées
  - à la main : ajouter `seigneuries_logistiques_armees_breakdown` dans `alliances` de instances/conglometrat_sino_siberien_bohai_transit_breakdown.md
  - _Bohai Transit s'appuie sur les seigneuries logistiques pour sécuriser ses convois en échange de ressources et de protection._
- [ ] 18. alliance nouvelle : Front Humanitaire d'Urgence Non Affilié ↔ Communautés Religieuses des Relais Physiques
  - à la main : ajouter `communautes_religieuses_des_relais_physiques_breakdown` dans `alliances` de instances/front_humanitaire_d_urgence_non_affilie_breakdown.md
  - _Les deux entités collaborent pour acheminer des secours et des informations dans les zones sinistrées, malgré leurs différences idéologiques._
- [ ] 19. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario breakdown --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 20. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section breakdown
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 21. Corriger une phrase de `nexcore_breakdown` [passe exhaustive]
  - à la main : instances/nexcore_breakdown.md
  - _« NexCore s'est fragmenté en 2051 lors du collapse des infrastructures numériques mondiales » — contredit par : La pandémie de 2043-2046 a provoqué un effondrement des infrastructures bien avant 2051._
- [ ] 22. Corriger une phrase de `rede_paulista_de_distribuicao_algoritmica_breakdown` [passe exhaustive]
  - à la main : instances/rede_paulista_de_distribuicao_algoritmica_breakdown.md
  - _« sans mise à jour des données démographiques depuis 2091 » — contredit par : La pandémie de 2043-2046 a tué 25 % de la population mondiale, rendant les données démographiques obsolètes bien avant 2091._
- [ ] 23. Corriger une phrase de `exode_midwest_grands_lacs_breakdown` [passe exhaustive]
  - à la main : event_instances/exode_midwest_grands_lacs_breakdown.md
  - _« L'été 2044 marque la fin du Midwest habitable » — contredit par : La pandémie de peste pulmonaire (2043-2046) rend impossible la survie dans le Midwest dès 2043, et non 2044._
- [ ] 24. Instances et événements relus par la passe exhaustive (obligatoires ci-dessus et dans les autres sections) ; aucune zone ni ligne du registre ne cite l'hypothèse

**Possibles (facultatif)**
- [ ] 25. Brigades Médicales Itinérantes (`brigades_medicales_itinerantes_breakdown`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Effondrement des systèmes de santé formels, nécessité critique des brigades médicales itinérantes_
- [ ] 26. Collectifs de Santé Communautaire Autogérée (`collectifs_de_sante_communautaire_autogeree_breakdown`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Remplacement des systèmes de santé publics effondrés par des collectifs autogérés_
- [ ] 27. Réseaux Noirs Pharmaceutiques (`reseaux_noirs_pharmaceutiques_breakdown`) : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, comblent le vide laissé par… » [passe exhaustive]
  - _Vide pharmaceutique comblé par les réseaux noirs, variable sante_biotechnologies +10.7_
- [ ] 28. Pirates Biologiques Open-Source (`pirates_biologiques_open_source_breakdown`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Contournement des infrastructures sanitaires défaillantes, réponse open-source à la crise_
- [ ] 29. Réseaux de Soigneurs Traditionnels (`reseaux_de_soigneurs_traditionnels_breakdown`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Devenus principale source de soins dans les zones rurales, mobilité humaine réduite_
- [ ] 30. Les Bouches de Sfax — Relais de la Faim Juste (`sfax_relais_bouches_breakdown`) : trajectoire ascendant → dominant ; texte « Réseau informel de distribution alimentaire et logistique… » [passe exhaustive]
  - _Réseau logistique alimentaire dominant, rupture des chaînes d'approvisionnement_
- [ ] 31. Réseau Logistique Criminel Concurrent (`reseau_logistique_criminel_concurrent_breakdown`) : trajectoire émergent → dominant [passe exhaustive]
  - _Chaos logistique accru, quasi-État dans les marges post-effondrement_
- [ ] 32. Cartels Logistiques Régionaux (`cartels_logistiques_regionaux_breakdown`) : trajectoire émergent → ascendant ; texte « Dans un scénario de breakdown, elles comblent le vide… » [passe exhaustive]
  - _Fragmentation des chaînes d'approvisionnement, acteurs logistiques régionaux indispensables_
- [ ] 33. Consortiums Logistiques Agro-Corporatifs (`consortiums_logistiques_agro_corporatifs_breakdown`) : trajectoire émergent → ascendant ; texte « Dans le chaos du breakdown, les Consortiums Logistiques… » [passe exhaustive]
  - _Rupture des chaînes logistiques agro-corporatives, prédateurs de l'effondrement_
- [ ] 34. Blocs de Contrôle des Couloirs d'Approvisionnement Stratégiques (`blocs_de_controle_des_couloirs_d_approvisionnement_strategiques_breakdown`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Contrôle des couloirs d'approvisionnement stratégiques, fragmentation logistique accélérée_
- [ ] 35. Flux Migratoires Non Intégrables (`flux_migratoires_non_integrables_breakdown`) : trajectoire émergent → dominant ; texte « les flux migratoires non intégrables saturent… » [passe exhaustive]
  - _Crise démographique et logistique sans précédent, saturation des flux migratoires_
- [ ] 36. ONG de Gestion Migratoire Survivantes (`ong_de_gestion_migratoire_survivantes_breakdown`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Gestion migratoire centrale, effondrement des institutions étatiques_
- [ ] 37. Communautés Paysannes Réfugiées (`communautes_paysannes_refugiees_breakdown`) : trajectoire émergent → ascendant ; texte « Dans le scénario breakdown, incarnent la fragmentation des… » [passe exhaustive]
  - _Flux migratoires accrus, pression sur les territoires d'accueil_
- [ ] 38. Milices Agro-Défensives Locales (`milices_agro_defensives_locales_breakdown`) : trajectoire émergent → ascendant ; texte « Ils assurent une forme de sécurité territoriale de… » [passe exhaustive]
  - _Sécurité territoriale locale, affaiblissement des institutions étatiques_
- [ ] 39. Milices d'Accaparement Hydrique (`milices_d_accaparement_hydrique_breakdown`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Contrôle hydrique critique, effondrement des régulations publiques_
- [ ] 40. Factions Para-Étatiques Hydriques (`factions_para_etatiques_hydriques_breakdown`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Fragmentation du pouvoir autour des ressources hydriques, mobilité réduite_
- [ ] 41. Les Confédérations du Seuil Dernier (`collectifs_du_seuil_breakdown`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Doctrine apocalyptique validée, attractivité renforcée dans un monde en crise_
- [ ] 42. Communes Libres du Rust Belt — Les Forges du Commun (`mouvement_des_communes_du_rust_belt_breakdown`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Effondrement des grands employeurs, légitimité accrue des communes autogérées_
- [ ] 43. Communes Libres du Rust Belt — Les Forges du Commun (`communes_rust_belt_breakdown`) : trajectoire ascendant → dominant ; texte « Après l'effondrement des structures étatiques fédérales,… » [passe exhaustive]
  - _Effondrement des structures étatiques fédérales, nœuds de résistance locale_
- [ ] 44. Ligue du Sahel Numérique — Les Nœuds d'Agadez (`agadez_ligue_sahel_numerique_breakdown`) : trajectoire ascendant → dominant ; alliance nouvelle avec Réseaux de Soigneurs Traditionnels [passe exhaustive]
  - _Repli régional renforcé, décentralisation des réseaux de soins traditionnels_
- [ ] 45. … et 118 autre(s) fiche(s) avec des changements possibles
  - _détail dans la section « Passe exhaustive » de ce scénario_

**Articles et site**
- [ ] 46. 7 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« LYNTH, LIEU ENCOMMANDE »; « LA DETTE AVANCE EN CRÉDITS-CHUTEURS »; « Les Bouches de l’Abîme parlent : le Sahel numérique saigne en silence »; « CONVOIS FANTÔMES : LES COURTIERS DE L'OMBRE DES VENELLES »; « CONVOIS NOCTURNES : GUIDES ET ESCORTES POUR LES VENELLES EURASIENNES »; « « Kharg-9 : Le Dernier Souffle des Archives Mondiales avant l’Abîme » »; « Les Bouches de l’Abîme étouffées : le silence forcé des gardiens du dernier maillage »_
- [ ] 47. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario breakdown`
  - _payant, un appel_
- [ ] 48. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 49. Base
  - `python3 generator/validate.py`
- [ ] 50. Lore
  - `python3 generator/audit_lore.py --scenario breakdown`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Quarantaines Permanentes du Détroit de Gibraltar
  category: territoire
  role: Zone de contrôle sanitaire militarisée entre l'Europe et l'Afrique, verrouillant les flux migratoires
    et commerciaux.
  etat: émergent
  scenario_ref: breakdown
  scenario_hint:
  - breakdown
  zone_hint: arc_sahelo_mediterraneen
  source: et_si_peste_pulmonaire_2043
- nom: Réseau des Villes-Sanctuaires Méditerranéennes
  category: réseau
  role: Alliance informelle de villes portuaires (Marseille, Barcelone, Tunis) offrant des havres sanitaires
    et logistiques aux populations déplacées.
  etat: émergent
  scenario_ref: breakdown
  scenario_hint:
  - breakdown
  zone_hint: arc_sahelo_mediterraneen
  source: et_si_peste_pulmonaire_2043
- nom: Corporation des Bio-Surveillants du Sahel
  category: entreprise
  role: Entité privée contrôlant les tests, les quarantaines et les passeports sanitaires dans les corridors
    ouest-africains.
  etat: émergent
  scenario_ref: breakdown
  scenario_hint:
  - breakdown
  zone_hint: afrique_de_louest_lagos_sahel
  source: et_si_peste_pulmonaire_2043
```

## Liste d'application — injection commune

⚠ Simulation limitée à breakdown : l'entrée couvre aussi fortress_world, new_sustainability, eco_communalism, policy_reform, reference, non simulé(s) dans ce rapport ; les simuler avant d'injecter, ou les retirer de `scenarios` et de `impacts_imposes`.

Mode rupture : `mode_impose: rupture` fait écrire `mode: rupture` dans chaque fiche ; le moteur déplace alors durablement la référence du scénario au lieu d'amortir un choc.

Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). Forces, polarités, durées, date et propagation de cette simulation sont imposées (`impacts_imposes`, `date_imposee`, `via_matrice_impose`) : l'IA de l'injection ne les recalcule pas, elle rédige seulement le récit.

`acteurs_hint` : entités les plus touchées de chaque scénario (lecture IA, passe exhaustive), 4 au plus par scénario ; chaque slug ne vaut que pour son scénario.

`faits_imposes` : contraintes de l'hypothèse et sort des acteurs du récit (disparaît, change, reste) ; l'injection les donne à l'IA comme faits non négociables.

```yaml
- id: peste_pulmonaire_2043
  description: En 2043, une souche de peste pulmonaire résistante aux antibiotiques se diffuse sur tous
    les continents et tue un quart de la population mondiale en trois ans. Villes désertées, chaînes de
    production rompues, frontières fermées, effondrement des systèmes de santé, puis lente recomposition.
  portee: globale
  date_approximative: 2043
  intensite: <à choisir>
  persistance: permanente
  scenarios:
  - breakdown
  - fortress_world
  - new_sustainability
  - eco_communalism
  - policy_reform
  - reference
  variables_hint:
  - demographie_mobilite_humaine
  - sante_biotechnologies
  - systemes_productifs_travail
  - systeme_economique_redistribution
  - frontieres_du_systeme
  - gouvernance_institutions
  - organisation_territoires
  - climat_environnement_global
  variables_hint_count: 8
  source: et_si_peste_pulmonaire_2043
  acteurs_hint:
  - ligue_mediterraneenne_des_villes_etats_portuaires_breakdown
  - bloc_de_johannesburg_breakdown
  - conglometrat_sino_siberien_bohai_transit_breakdown
  - hanse_baltique_breakdown
  acteurs_hint_count: 4
  faits_imposes:
    breakdown:
    - fait: La pandémie tue environ 25 % de la population mondiale entre 2043 et 2046, sur tous les continents,
        plus fortement dans les villes denses.
      sort: contrainte
    - fait: Aucun traitement efficace avant le début des années 2050 ; la maladie devient ensuite endémique
        et contrôlée.
      sort: contrainte
    - fait: La population mondiale ne retrouve pas son niveau de 2042 avant la fin du siècle.
      sort: contrainte
    - fait: 'Ligue Méditerranéenne des Villes-États Portuaires (ligue_mediterraneenne_des_villes_etats_portuaires_breakdown)
        passe de « émergent » à « ascendant » après 2043 : elle existe toujours (elle peut perdre des
        lieux, des biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: ligue_mediterraneenne_des_villes_etats_portuaires_breakdown
      sort: change
    - fait: 'Bloc de Johannesburg (bloc_de_johannesburg_breakdown) passe de « émergent » à « ascendant
        » après 2043 : elle existe toujours (elle peut perdre des lieux, des biens ou du pouvoir), ne
        la décris pas comme disparue.'
      slug: bloc_de_johannesburg_breakdown
      sort: change
    - fait: 'Conglométrat sino-sibérien Bohai Transit (conglometrat_sino_siberien_bohai_transit_breakdown)
        passe de « émergent » à « mature » après 2043 : elle existe toujours (elle peut perdre des lieux,
        des biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: conglometrat_sino_siberien_bohai_transit_breakdown
      sort: change
    - fait: 'Ligue Hanséatique Baltique — Le Sceau du Gotland (hanse_baltique_breakdown) passe de « ascendant
        » à « dominant » après 2043 : elle existe toujours (elle peut perdre des lieux, des biens ou du
        pouvoir), ne la décris pas comme disparue.'
      slug: hanse_baltique_breakdown
      sort: change
    - fait: 'La zone Afrique de l''Ouest – Nœuds Lagos et Sahel (afrique_de_louest_lagos_sahel) passe
        de « fragmenté » à « en_declin » : le lieu subsiste.'
      slug: afrique_de_louest_lagos_sahel
      sort: zone
    - fait: 'La zone Espace Nord-Américain Fragmenté (espace_nord_americain_fragmente) passe de « fragmenté
        » à « en_declin » : le lieu subsiste.'
      slug: espace_nord_americain_fragmente
      sort: zone
    - fait: 'La zone Zone Golfe Persique–Levant (zone_golfe_levant) passe de « fragmenté » à « en_declin
        » : le lieu subsiste.'
      slug: zone_golfe_levant
      sort: zone
    fortress_world:
    - fait: La pandémie tue environ 25 % de la population mondiale entre 2043 et 2046, sur tous les continents,
        plus fortement dans les villes denses.
      sort: contrainte
    - fait: Aucun traitement efficace avant le début des années 2050 ; la maladie devient ensuite endémique
        et contrôlée.
      sort: contrainte
    - fait: La population mondiale ne retrouve pas son niveau de 2042 avant la fin du siècle.
      sort: contrainte
    new_sustainability:
    - fait: La pandémie tue environ 25 % de la population mondiale entre 2043 et 2046, sur tous les continents,
        plus fortement dans les villes denses.
      sort: contrainte
    - fait: Aucun traitement efficace avant le début des années 2050 ; la maladie devient ensuite endémique
        et contrôlée.
      sort: contrainte
    - fait: La population mondiale ne retrouve pas son niveau de 2042 avant la fin du siècle.
      sort: contrainte
    eco_communalism:
    - fait: La pandémie tue environ 25 % de la population mondiale entre 2043 et 2046, sur tous les continents,
        plus fortement dans les villes denses.
      sort: contrainte
    - fait: Aucun traitement efficace avant le début des années 2050 ; la maladie devient ensuite endémique
        et contrôlée.
      sort: contrainte
    - fait: La population mondiale ne retrouve pas son niveau de 2042 avant la fin du siècle.
      sort: contrainte
    policy_reform:
    - fait: La pandémie tue environ 25 % de la population mondiale entre 2043 et 2046, sur tous les continents,
        plus fortement dans les villes denses.
      sort: contrainte
    - fait: Aucun traitement efficace avant le début des années 2050 ; la maladie devient ensuite endémique
        et contrôlée.
      sort: contrainte
    - fait: La population mondiale ne retrouve pas son niveau de 2042 avant la fin du siècle.
      sort: contrainte
    reference:
    - fait: La pandémie tue environ 25 % de la population mondiale entre 2043 et 2046, sur tous les continents,
        plus fortement dans les villes denses.
      sort: contrainte
    - fait: Aucun traitement efficace avant le début des années 2050 ; la maladie devient ensuite endémique
        et contrôlée.
      sort: contrainte
    - fait: La population mondiale ne retrouve pas son niveau de 2042 avant la fin du siècle.
      sort: contrainte
  date_imposee: 2043
  mode_impose: rupture
  impacts_imposes:
    breakdown:
    - variable: demographie_mobilite_humaine
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: sante_biotechnologies
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: systemes_productifs_travail
      delta_level: 18
      duree: 4
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 15
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 15
      duree: 3
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: organisation_territoires
      delta_level: 10
      duree: 6
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 5
      duree: 10
      polarite: -1
    fortress_world:
    - variable: demographie_mobilite_humaine
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: sante_biotechnologies
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: systemes_productifs_travail
      delta_level: 18
      duree: 4
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 15
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 15
      duree: 3
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: organisation_territoires
      delta_level: 10
      duree: 6
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 5
      duree: 10
      polarite: -1
    new_sustainability:
    - variable: demographie_mobilite_humaine
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: sante_biotechnologies
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: systemes_productifs_travail
      delta_level: 18
      duree: 4
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 15
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 15
      duree: 3
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: organisation_territoires
      delta_level: 10
      duree: 6
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 5
      duree: 10
      polarite: -1
    eco_communalism:
    - variable: demographie_mobilite_humaine
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: sante_biotechnologies
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: systemes_productifs_travail
      delta_level: 18
      duree: 4
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 15
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 15
      duree: 3
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: organisation_territoires
      delta_level: 10
      duree: 6
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 5
      duree: 10
      polarite: -1
    policy_reform:
    - variable: demographie_mobilite_humaine
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: sante_biotechnologies
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: systemes_productifs_travail
      delta_level: 18
      duree: 4
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 15
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 15
      duree: 3
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: organisation_territoires
      delta_level: 10
      duree: 6
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 5
      duree: 10
      polarite: -1
    reference:
    - variable: demographie_mobilite_humaine
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: sante_biotechnologies
      delta_level: 25
      duree: 3
      polarite: 1
    - variable: systemes_productifs_travail
      delta_level: 18
      duree: 4
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 15
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 15
      duree: 3
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: organisation_territoires
      delta_level: 10
      duree: 6
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 5
      duree: 10
      polarite: -1
  via_matrice_impose: true
```

