# Et si ? — Dépôt de platinoïdes de Shackleton

*Simulation du 2026-11-15 19:44 — lecture seule, rien n'a été injecté (simulateur v8.25).*

En 2052, une mission de prospection privée révèle que le cratère de Shackleton (pôle Sud lunaire) contient un dépôt d'astéroïde riche en platinoïdes et terres rares lourdes, accessible en surface grâce à la glace permanente. L'extraction devient économiquement viable dès 2055 avec les robots lunaires existants, déversant des métaux critiques sur le marché mondial.

**Faits imposés (lecture IA et récit de l'événement)** :
- En 2052, une mission de prospection privée révèle que le cratère de Shackleton (pôle Sud lunaire) contient un dépôt d'astéroïde riche en platinoïdes et terres rares lourdes, accessible en surface grâce à la glace permanente.
- L'extraction devient économiquement viable dès 2055 avec les robots lunaires existants.
- Les métaux critiques extraits arrivent en masse sur le marché mondial.

- **Apparition** : 2052 · **Persistance** : — (mode **rupture** : l'équilibre du scénario est déplacé pour de bon) · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098
- **Carte** : élément déclaré sans effet territorial (`carte: non`), aucune proposition de carte retenue
- **⚡ Wild card** : rupture à faible probabilité et impact majeur ; elle peut contredire les fiches et les tendances, jamais les règles de lore
- Déclaré : **frontieres_du_systeme** — force 30, apaise ↓, montée sur 5 ans
- Déclaré : **energie_ressources_critiques** — force 32, apaise ↓, montée sur 8 ans
- Déclaré : **geopolitique_conflits** — force fortress_world 35, reference 28, aggrave ↑, montée sur 5 ans
- Déclaré : **systeme_economique_redistribution** — force fortress_world 28, reference 30, aggrave ↑, montée sur 8 ans

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## fortress_world

Apparu en 2052 dans le scénario fortress_world, Dépôt de platinoïdes de Shackleton agit d'abord sur énergie ressources critiques, frontières du système, système économique redistribution et géopolitique conflits. Son effet le plus fort apaise énergie ressources critiques, avec un écart maximal de -30,4 points vers 2060. Par propagation, technologie information réagit à son tour environ 8 ans après l'apparition (+1,2 points au plus fort). Un contrecoup apparaît ensuite sur technologie information (-0,2 points vers 2074). En 2098, il en subsiste -29,2 points sur énergie ressources critiques.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| energie_ressources_critiques | 82,0 → 51,5 | 89,1 | 59,9 | **-29,2** | direct |
| frontieres_du_systeme | 70,0 → 41,7 | 78,7 | 51,0 | **-27,7** | direct |
| systeme_economique_redistribution | 60,0 → 84,2 | 63,6 | 86,3 | **+22,7** | direct |
| climat_environnement_global | 75,0 | 81,8 | 79,8 | **-2,0** | propagé |
| demographie_mobilite_humaine | 75,0 | 86,8 | 87,4 | **+0,6** | propagé |
| sante_biotechnologies | 65,0 | 67,0 | 67,4 | **+0,4** | propagé |
| geopolitique_conflits | 85,0 → 99,7 | 99,7 | 100,0 | **+0,3** | direct |
| valeurs_culture_tempo_sociale | 80,0 | 91,0 | 91,3 | **+0,3** | propagé |
| organisation_territoires | 80,0 | 92,5 | 92,7 | **+0,2** | propagé |
| systemes_productifs_travail | 85,0 | 96,3 | 96,5 | **+0,2** | propagé |
| gouvernance_institutions | 50,0 | 64,6 | 64,7 | **+0,1** | propagé |

**Repères** :
- energie_ressources_critiques (direct) : pic -30,4 vers 2060
- frontieres_du_systeme (direct) : pic -28,3 vers 2057
- systeme_economique_redistribution (direct) : pic +24,1 vers 2060
- geopolitique_conflits (direct) : pic +4,3 vers 2054

**Tensions** : 34 sans l'hypothèse → 34 avec.
- ⬇ n'est plus une cascade critique : energie_ressources_critiques → geopolitique_conflits
- ⬇ n'est plus une cascade critique : energie_ressources_critiques → systeme_economique_redistribution
- ⬇ n'est plus une cascade critique : energie_ressources_critiques → systemes_productifs_travail
- ⬇ n'est plus une cascade critique : energie_ressources_critiques → climat_environnement_global
_Une tension se déclenche quand un niveau franchit un seuil (60, ou 70 pour une cascade, abaissés selon le risque de bascule de la variable) : un écart de quelques dixièmes peut suffire si le niveau était déjà au bord._

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

Le dépôt de Shackleton casse la logique de rareté qui fondait la fermeture des blocs : avec l'abondance lunaire de platinoïdes, la sécurisation territoriale des ressources perd son urgence économique, fragilisant les cartels miniers et les fermetures frontalières tout en créant une nouvelle aristocratie spatiale centrée sur l'Arctique. Le choc ne modifie pas la géographie terrestre mais redistribue durablement le pouvoir vers ceux qui contrôlent l'accès à la Lune et la distribution des métaux critiques. _(ampleur : bascule)_

**Trajectoires d'entités**
- Cartels Miniers Militarisés Subsahariens (`cartels_miniers_militarises_subsahariens_fortress_world`) : émergent → **déclinant** — L'abondance lunaire détruit leur monopole de fait sur les métaux rares terrestres qui justifiait le pillage des zones effondrées.
- Les Ferrailleurs de Paris (`les_recycleurs_fortress_world`) : dominant → **déclinant** — Le marché des métaux rares contrôlé depuis Paris s'effondre face à l'offre massive de platinoïdes lunaires.
- Consortium Eurasiatique des Ressources Fermées (`consortium_eurasiatique_des_ressources_fermees_fortress_world`) : émergent → **déclinant** — La logique de fermeture des ressources critiques perd sa pertinence économique avec l'arrivée des métaux spatiaux.
- Alpha47 - Complexe Minier Ergo-Wian (`alpha47_fortress_world`) : mature → **déclinant** — La planète minière d'Ergo-Wian est directement concurrencée par Shackleton, plus accessible et moins coûteux à exploiter.
- Complexes Militaro-Industriels de Gestion des Ressources (`complexes_militaro_industriels_de_gestion_des_ressources_fortress_world`) : émergent → **ascendant** — Ils pivotent vers la sécurisation des infrastructures d'extraction lunaire et des corridors spatiaux, devenant les nouveaux gardiens des ressources.
- Réseaux privés de sécurité aux frontières (`reseaux_prives_de_securite_aux_frontieres_fortress_world`) : émergent → **déclinant** — La pression sur les frontières diminue fortement car les blocs n'ont plus besoin de fermer hermétiquement pour sécuriser leurs approvisionnements en métaux.

**Relations**
- opposition nouvelle : Cartels Miniers Militarisés Subsahariens ↔ Complexes Militaro-Industriels de Gestion des Ressources — Les cartels tentent de saboter l'accès lunaire pour préserver leur rente, tandis que les complexes veulent exploiter Shackleton.
- opposition nouvelle : Les Ferrailleurs de Paris ↔ Nuna Capital — Fonds Souverain de Kalaallit Nunaat — Concurrence directe pour le contrôle du marché mondial des métaux critiques entre Paris et le fonds groenlandais proche de l'Arctique.
- alliance nouvelle : Nordisk Arktisk Transitkontroll — NAT ↔ Nexcore Atlantique Infrastructure — Division Séparation Climatique — Coopération pour construire et sécuriser les spatioports arctiques servant de base aux missions lunaires vers Shackleton.

**Statut des zones**
- Afrique Subsaharienne — Zones d'Effondrement Étatique (`afrique_subsaharienne_zones_effondrees`) : fragmenté → **en_declin** — L'effondrement des cartels miniers militarisés laisse un vide sécuritaire et économique dans les zones déjà fragiles.
- Espace Nordique et Arctique (`espace_nordique_arctique`) : stable → **dominant** — L'Arctique devient le hub spatial mondial incontournable pour l'accès à Shackleton, renforçant la position d'Euro-Nord.
- Paris (`paris_hors`) : en_declin → **fragmenté** — La perte de pouvoir des Ferrailleurs sur les métaux rares plonge la zone dans un chaos plus prononcé.
- Bloc Eurasiatique Occidental (`bloc_eurasiatique_occidental`) : dominant → **stable** — La forteresse perd de sa nécessité stratégique avec l'abondance des ressources, passant d'un statut dominant à stable.

**Nouvelles entités plausibles**
- Consortium Shackleton d'Extraction Lunaire (espace_nordique_arctique) [organisation] : Gère l'extraction robotisée des platinoïdes au pôle Sud lunaire et leur première mise sur le marché mondial. — Nécessité d'une autorité centralisée pour coordonner l'exploitation du cratère de Shackleton depuis les bases arctiques.
- ARIA-Lune — Système d'Allocation des Métaux Orbitaux (aria_instance_fantome) [système] : Régule la distribution mondiale des métaux critiques lunaires pour éviter l'effondrement des économies terrestres dépendantes. — Extension du réseau ARIA dans l'orbite neutre pour gérer les flux de platinoïdes sans passer par les blocs terrestres fermés.
- Garde Spatiale Nordique — Unité de Protection des Corridors Lunaires (corridor_arctique_transit) [organisation] : Sécurise les trajectoires Terre-Lune et les installations de Shackleton contre les acteurs non alignés et les cartels hostiles. — Bras armé dédié à la protection des infrastructures spatiales critiques émergeant du choc lunaire.

_Propositions écartées au contrôle (1) : relation consortium_eurasiatique_des_ressources_fermees_fortress_world / regimes_autoritaires_du_bloc_eurasiatique_occidental_fortress_world : opposition à rompre absente du vault_

### Passe exhaustive (IA, toutes les fiches — rien n'est écrit)

159 fiche(s) relue(s) en 11 lot(s).
Verdicts : **0 fiche(s) à corriger**, 78 avec des changements possibles seulement, 81 inchangée(s).

_Contre-lecture des obligatoires : 1 vérifié(s), 0 confirmé(s), 1 rétrogradé(s) en possible._

#### Obligatoire — la fiche devient fausse sans ce changement

Aucun.

#### Possible — conséquence plausible, la fiche reste vraie sans elle

_Rétrogradés d'obligatoire à possible par les contrôles : 6 changement de degré, 1 contre-lecture nuance, 1 lien territoire alors qu'aucun territoire précis n'est touché, 1 élargit le rôle sans le contredire._

**À lire en priorité (20 fiches sur 78)** — choisies et ordonnées par l'IA

- **Ilse Varga-Holm — Syndicat des Gestionnaires de Seuils (SGS)** (`ilse_varga_holm_fortress_world`) — _Gestion directe des seuils de distribution des métaux extraits de Shackleton_
  - Ilse Varga-Holm — Syndicat des Gestionnaires de Seuils (SGS) (`ilse_varga_holm_fortress_world`) : ascendant → **dominant** — Le rôle de gestionnaire des seuils dans la distribution des métaux critiques extraits de Shackleton renforce la position d'Ilse Varga-Holm dans l'économie informelle des zones de friction. [lien variable : systeme_economique_redistribution (+22.7 points) : la redistribution des métaux critiques lunaires passe par les seuils et zones grises où opère l'économie informelle.]
- **Consortium des Blocs Solaires Orbitaux Concurrents** (`consortium_des_blocs_solaires_orbitaux_concurrents_fortress_world`) — _Approvisionnement énergétique orbital indispensable à la viabilité de l'extraction de Shackleton_
  - Consortium des Blocs Solaires Orbitaux Concurrents (`consortium_des_blocs_solaires_orbitaux_concurrents_fortress_world`) : émergent → **ascendant** — la viabilité de l'extraction de Shackleton dépend de l'approvisionnement énergétique orbital, donnant un poids stratégique nouveau à ces consortiums [lien variable : energie_ressources_critiques (-29.2 points) : l'extraction massive sur la Lune nécessite une énergie colossale, rendant les blocs solaires orbitaux indispensables au fonctionnement de l'économie lunaire]
- **Consortiums de Défense Orbitale Privés** (`consortiums_de_defense_orbitale_prives_fortress_world`) — _Contrôle de l'orbite comme goulot d'étranglement stratégique des métaux lunaires_
  - Consortiums de Défense Orbitale Privés (`consortiums_de_defense_orbitale_prives_fortress_world`) : émergent → **ascendant** — Le contrôle de l'orbite devient le goulot d'étranglement stratégique de l'approvisionnement en métaux lunaires, renforçant le poids des consortiums qui le détiennent. [lien variable : energie_ressources_critiques (-29.2) : l'extraction massive des platinoïdes de Shackleton rend l'accès orbital indispensable au flux des métaux critiques]
- **Instances ARIA Concurrentes des Blocs Rivaux** (`instances_aria_concurrentes_des_blocs_rivaux_fortress_world`) — _Gestion de l'accès à la Lune et des flux de platinoïdes exige des IA de pilotage supérieures_
  - Instances ARIA Concurrentes des Blocs Rivaux (`instances_aria_concurrentes_des_blocs_rivaux_fortress_world`) : émergent → **ascendant** — la gestion de l'accès à la Lune et des flux de platinoïdes exige des IA de pilotage stratégique supérieures, renforçant la course aux armements cognitifs entre blocs rivaux [lien relation : allié complexes_militaro_industriels_de_gestion_des_ressources_fortress_world qui devient ascendant et concentre le contrôle de la distribution des métaux critiques lunaires]
- **Helios Bloc Consortium — Division Souveraineté Énergétique** (`consortium_helios_fortress_world`) — _Fourniture de l'énergie nécessaire aux robots lunaires de Shackleton_
  - Helios Bloc Consortium — Division Souveraineté Énergétique (`consortium_helios_fortress_world`) : transformé → **ascendant** — malgré sa fracture, la branche survivante retrouve une centralité en fournissant l'énergie nécessaire aux robots lunaires de Shackleton [lien variable : energie_ressources_critiques (-29.2 points) : l'extraction lunaire à grande échelle exige un approvisionnement énergétique massif que seul un quasi-État énergétique comme Helios BSE peut garantir]
- **Commandement Stratégique des Matières Critiques Atlantique** (`commandement_strategique_des_matieres_critiques_atlantique_fortress_world`) — _Arbitrage des tensions sur l'accès aux ressources rendu obsolète par l'abondance (-29.2)_
  - Commandement Stratégique des Matières Critiques Atlantique (`commandement_strategique_des_matieres_critiques_atlantique_fortress_world`) : émergent → **déclinant** — la fiche affirme qu'il arbitre les tensions sur l'accès aux ressources ; avec l'abondance, ces tensions diminuent et son rôle d'arbitrage perd de son urgence [lien variable : energie_ressources_critiques (-29.2) : l'abondance lunaire de platinoïdes réduit la rareté des matières critiques, diminuant la nécessité d'un arbitrage autoritaire strict entre États membres]
- **Cartels Énergétiques des Bioréacteurs** (`cartels_energetiques_des_bioreacteurs_fortress_world`) — _Levier de survie des enclaves via les contrats énergétiques perd son urgence avec la fin de la crise (-29.2)_
  - Cartels Énergétiques des Bioréacteurs (`cartels_energetiques_des_bioreacteurs_fortress_world`) : émergent → **déclinant** — la fiche affirme que les cartels conditionnent la survie des enclaves à leurs contrats ; avec la diminution de la crise des ressources critiques, cette condition de survie s'atténue [lien variable : energie_ressources_critiques (-29.2) : l'abondance lunaire de platinoïdes réduit la crise globale des ressources critiques, diminuant la dépendance des enclaves aux contrats d'exclusivité énergétique des bioréacteurs]
- **Réseau d'Allocation Stratégique ARIA-Bloc** (`grille_aria_fortress_world`) — _Logique de souveraineté militarisée pour l'allocation des platinoïdes économiquement obsolète (-29.2)_
  - instance Réseau d'Allocation Stratégique ARIA-Bloc (`grille_aria_fortress_world`) : « gérant l'allocation des ressources critiques — énergie, eau, calories, soins — selon une logique de souveraineté militarisée » — La logique de souveraineté militarisée pour l'allocation des platinoïdes devient économiquement obsolète avec leur abondance lunaire, bien qu'elle persiste pour d'autres ressources. [lien variable : energie_ressources_critiques (-29.2 points) : l'abondance lunaire de platinoïdes et terres rares lourdes casse la logique de rareté qui justifiait la souveraineté militarisée sur ces métaux.]
- **Détroits Souverains - ARDS Fragmentée** (`agence_de_regulation_des_detroits_strategiques_ards_fortress_world`) — _Flux de ressources critiques ne transitent plus par les détroits (combine -29.2 et -27.7)_
  - Détroits Souverains - ARDS Fragmentée (`agence_de_regulation_des_detroits_strategiques_ards_fortress_world`) : déclinant → **résiduel** — La fiche décrit l'ARDS comme déclinante ; l'élément accentue ce déclin vers le résiduel car les flux de ressources critiques ne transitent plus par les détroits. [lien variable : frontieres_du_systeme (-27.7 points) et energie_ressources_critiques (-29.2 points) : les métaux critiques arrivant en masse par la Lune, le contrôle des détroits maritimes perd sa pertinence stratégique.]
- **Ceinture Productive Eurasiatique — Zones de Labeur Sous Mandat** (`zone_usines_forteresses_eurasie_fortress_world`) — _Production pour les forteresses riches perd son caractère avec les métaux déversés depuis la Lune_
  - Ceinture Productive Eurasiatique — Zones de Labeur Sous Mandat (`zone_usines_forteresses_eurasie_fortress_world`) : dominant → **déclinant** — La fiche affirme que ces zones produisent pour les forteresses riches ; avec les métaux critiques déversés depuis la Lune, cette production perd son caractère indispensable et les zones ne peuvent plus rester dominantes. [lien variable : energie_ressources_critiques (-29.2 points) : l'arrivée massive de platinoïdes lunaires sur le marché mondial dès 2055 réduit la valeur stratégique de la production terrestre de métaux critiques, affaiblissant le rôle des zones de labeur sous mandat qui produisaient pour les forteresses] — contredit : L'abondance lunaire casse la logique de rareté qui justifiait la sécurisation territoriale des ressources
- **Bloc Pacifique Nord** (`bloc_pacifique_nord_fortress_world`) — _Capitalisation sur la rareté des réserves terrestres rendue obsolète par l'abondance lunaire (-29.2)_
  - Bloc Pacifique Nord (`bloc_pacifique_nord_fortress_world`) : émergent → **marginal** — L'abondance lunaire de métaux critiques rend obsolète la capitalisation sur la rareté des réserves terrestres. [lien variable : dépend de la variable energie_ressources_critiques (-29.2 points) pour sa stratégie d'accumulation de réserves]
- **Collectifs de Réappropriation Énergétique Périphérique** (`collectifs_de_reappropriation_energetique_peripherique_fortress_world`) — _Érosion du monopole énergétique avec la diminution de la crise des ressources critiques (-29.2)_
  - Collectifs de Réappropriation Énergétique Périphérique (`collectifs_de_reappropriation_energetique_peripherique_fortress_world`) : émergent → **déclinant** — la fiche décrit une érosion du monopole énergétique ; avec la diminution de la crise des ressources critiques, ce monopole perd de son pouvoir de nuisance [lien variable : energie_ressources_critiques (-29.2) : l'abondance de métaux critiques lunaires réduit la valeur stratégique du monopole énergétique des zones protégées que les collectifs cherchent à éroder]
- **administrations de contrôle frontalier des blocs** (`administrations_de_controle_frontalier_des_blocs_fortress_world`) — _Bras opérationnel de la fermeture des blocs perd son urgence avec -27.7 sur les frontières_
  - administrations de contrôle frontalier des blocs (`administrations_de_controle_frontalier_des_blocs_fortress_world`) : émergent → **marginal** — La fiche affirme qu'elles constituent le bras opérationnel de la fermeture des blocs ; avec frontieres_du_systeme à -27.7, cette fermeture perd son urgence économique et ces administrations passent à marginal. [lien variable : frontieres_du_systeme (-27.7 points) : l'abondance lunaire de platinoïdes casse la logique de rareté qui fondait la fermeture des blocs, rendant le contrôle frontalier moins central.] _(rétrogradé : changement de degré)_ — contredit : le statut 'émergent' des administrations de contrôle frontalier alors que la variable frontieres_du_systeme chute de 27.7 points.
- **Appareils d'État des Blocs Fermés** (`appareils_d_etat_des_blocs_fermes_fortress_world`) — _Définition et maintien des frontières dures entre blocs rendu non pertinent (-27.7)_
  - Appareils d'État des Blocs Fermés (`appareils_d_etat_des_blocs_fermes_fortress_world`) : émergent → **marginal** — Leur rôle est de définir et maintenir les frontières dures entre blocs ; avec frontieres_du_systeme à -27.7, ils ne peuvent plus être émergents et passent à marginal. [lien variable : frontieres_du_systeme (-27.7 points) : les frontières dures perdent leur fondement économique avec l'abondance lunaire de platinoïdes.] _(rétrogradé : changement de degré)_ — contredit : le statut 'émergent' alors que la fermeture des blocs chute de 27.7 points.
- **Bureaux de Contrôle Frontalier des Blocs Fermés** (`bureaux_de_controle_frontalier_des_blocs_fermes_fortress_world`) — _Monopole total sur les passages frontaliers fragilisé par l'ouverture du système (-27.7)_
  - Bureaux de Contrôle Frontalier des Blocs Fermés (`bureaux_de_controle_frontalier_des_blocs_fermes_fortress_world`) : émergent → **marginal** — La fragilisation des frontières du système rend le monopole total sur les passages frontaliers moins pertinent. [lien variable : dépend de la variable frontieres_du_systeme (-27.7 points) pour le monopole sur les passages frontaliers]
- **Les Campements des Checkpoints** (`campements_seuils_fermes_fortress_world`) — _Disparition des campements due à la perte de fonction des seuils frontaliers_
  - Les Campements des Checkpoints (`campements_seuils_fermes_fortress_world`) : marginal → **disparu** — La perte de fonction des seuils frontaliers due à l'abondance lunaire entraîne la disparition des campements établis à ces checkpoints. [lien variable : dépend de la variable frontieres_du_systeme (-27.7 points) qui fonde l'existence des seuils comme points de contrôle]
- **agences de sécurité intérieure des États forteresses** (`agences_de_securite_interieure_des_etats_forteresses_fortress_world`) — _Maintien de l'étanchéité des frontières impossible dans un monde fragmenté ouvert (-27.7)_
  - agences de sécurité intérieure des États forteresses (`agences_de_securite_interieure_des_etats_forteresses_fortress_world`) : émergent → **marginal** — Leur rôle est de maintenir l'étanchéité des frontières dans un monde fragmenté ; avec frontieres_du_systeme à -27.7, elles ne peuvent plus être émergentes et deviennent marginales. [lien variable : frontieres_du_systeme (-27.7 points) : l'étanchéité des frontières perd son urgence avec l'abondance lunaire de métaux critiques.] _(rétrogradé : changement de degré)_ — contredit : le statut 'émergent' de ces agences alors que la fermeture des frontières chute de 27.7 points.
- **Pacte des Forteresses Souveraines** (`alliance_blocs_souverains_fortress_world`) — _Logique de fermeture fondant le Pacte des Forteresses Souveraines fragilisée (-27.7)_
  - Pacte des Forteresses Souveraines (`alliance_blocs_souverains_fortress_world`) : déclinant → **résiduel** — La fiche le décrit comme déclinant ; l'élément fragilise davantage la logique de fermeture qui fonde le Pacte des Forteresses Souveraines. [lien variable : frontieres_du_systeme (-27.7 points) et energie_ressources_critiques (-29.2 points) : le Pacte fonde sa légitimité sur la sécurisation des ressources par la fermeture, rendue obsolète par l'abondance lunaire.]
- **Conglomérats Industriels d'État des Augmentations Propriétaires** (`conglomerats_industriels_d_etat_des_augmentations_proprietaires_fortress_world`) — _Coût des augmentations baisse avec les matériaux abondants, accélérant leur diffusion (+22.7)_
  - Conglomérats Industriels d'État des Augmentations Propriétaires (`conglomerats_industriels_d_etat_des_augmentations_proprietaires_fortress_world`) : émergent → **ascendant** — avec des matériaux abondants, le coût des augmentations baisse et leur diffusion s'accélère, renforçant le poids de ces conglomérats même si le lien avec les frontières s'affaiblit [lien variable : systeme_economique_redistribution (+22.7 points) : l'abondance de métaux critiques lunaires permet de produire massivement des augmentations, élargissant leur base de distribution malgré la fragilisation des frontières]
- **Syndicats Industriels Résiduels Post-Crise** (`syndicats_industriels_residuels_post_crise_fortress_world`) — _Redistribution économique induite par l'abondance lunaire renforce la représentation des travailleurs (+22.7)_
  - Syndicats Industriels Résiduels Post-Crise (`syndicats_industriels_residuels_post_crise_fortress_world`) : émergent → **ascendant** — La redistribution économique induite par l'abondance lunaire renforce la pertinence de la représentation collective des travailleurs résiduels dans les secteurs industriels encore actifs. [lien variable : systeme_economique_redistribution (+22.7 points)]

**Autres fiches avec des changements possibles (58)**
- Les Cycles de Paris : trajectoire mature → déclinant
- Alliance Sanitaire des Populations Exclues : trajectoire émergent → marginal
- Archives Chiffrées de l'Open Internet Coalition : trajectoire émergent → marginal
- Coalition Arctique des Blocs Continentaux : trajectoire émergent → ascendant
- Alliance des Glaces Autonomes (AGA) : trajectoire ascendant → dominant
- Consortium Sino-Finlandais de Flotte Autonome : trajectoire émergent → ascendant
- Factions Anti-Privatisation des Voies Souveraines Scandinaves : trajectoire émergent → ascendant
- Les Échos du Hors : trajectoire émergent → ascendant
- Milices Privées de Protection des Sites Germinaux : trajectoire émergent → ascendant
- VaultCorp Sovereign Defense Systems (VCSDS) : trajectoire dominant → déclinant
- Vikram Raghavan — Le Gardien des Seuils Parisiens : trajectoire ascendant → déclinant
- Zone de Friction d'Almaty — Périmètre des Seuils Kazakhs : trajectoire dominant → mature
- Anba Siege Atlantique — Division Accès Protégés : trajectoire dominant → mature
- Chambre de Sécurité Territoriale : trajectoire mature → déclinant
- Pacte Atlantique de Préservation Civilisationnelle — PAPC : trajectoire dominant → mature
- Forteresse Eurasiatique Occidentale — Pacte de Stabilité Intérieure : trajectoire dominant → mature
- Bunker — Chambre de Sécurité Territoriale : trajectoire dominant → mature
- Bureau des Territoires Résiduels — Division Continentale : trajectoire dominant → mature
- Coalitions des Déplacés et Apatrides : trajectoire émergent → déclinant
- Collectifs d'Ingénieurs Dissidents Anti-Militarisation : trajectoire émergent → ascendant
- Les Seuils Fermés : trajectoire ascendant → déclinant
- Commandements Logistiques Périphériques du Bloc Eurasien Central : trajectoire émergent → déclinant
- Pacte Vert Amazônia — Souveraineté des Gardiens : trajectoire déclinant → émergent
- Consortium des Médias d'État Souverains (Hegemonia Press / Xinhua Fortifiée / EuroVox Integral) : trajectoire émergent → marginal
- Consortiums Énergétiques du Bloc Ourrassol : trajectoire émergent → déclinant ; texte « conditionnant l'accès aux ressources comme levier de… »
- Contrebandiers Énergétiques des Zones Grises : trajectoire émergent → déclinant
- Corps des Inspecteurs de Conformité Inter-Blocs : trajectoire émergent → déclinant
- Dispositifs de Surveillance Numérique Souveraine : trajectoire émergent → déclinant
- Dissidences Internes aux Blocs Minoritaires : trajectoire émergent → ascendant
- États-Forteresses sous Contrat de Souveraineté Biologique : trajectoire émergent → déclinant
- Factions Dissidentes du Consortium Helios : trajectoire émergent → ascendant
- Factions Internes Pro-Autarcie Totale : trajectoire émergent → déclinant
- Front Résilient Pro-Système : trajectoire émergent → déclinant
- Gelecek Meclisi Fragmentaire : trajectoire ascendant → dominant
- Seuils Intégraux — Division de Contrôle Biopolitique (SIDCB) : trajectoire dominant → déclinant
- Institutions Multilatérales Résiduelles : trajectoire émergent → ascendant
- Ironclad Sovereign Corridors (ISC) : trajectoire dominant → déclinant
- Corridors Souverains Hybrides (CSH) : trajectoire dominant → déclinant
- Nexus des Seuils Hybrides (NSH) : trajectoire dominant → déclinant
- Les Sentinelles des Aquifères Oubliés : trajectoire ascendant → dominant
- Les Gardiens des Veines Oubliées : trajectoire ascendant → mature
- Marchés Gris de Casablanca — Bureau des Interstices Atlantiques : trajectoire mature → déclinant
- Marches Gris Tbilissi — Réseau des Interstices Caucasiens : trajectoire ascendant → mature
- Mouvement Commun Midwest — Front du Dehors : trajectoire ascendant → mature
- NeuroSentry Sovereign Cognitive Division (NSCD) : trajectoire dominant → mature
- Nexcore Atlantique Infrastructure — Division Séparation Climatique : trajectoire dominant → mature
- SGC — Siege Genevois Cars, Division Alpes Souveraines : trajectoire dominant → déclinant
- Sigrid Halvorsen — Gouverneurat des Interfaces Bruxelles-Ergo-Wian : trajectoire dominant → déclinant
- Systèmes de Scoring de Productivité Corporative : trajectoire émergent → déclinant
- Kharg-9 Data Haven : trajectoire dominant → déclinant
- TerraShield Sovereign GeoEngineering (TSG) : trajectoire dominant → déclinant
- Vasil Orentchev : trajectoire dominant → déclinant
- Périmètres de Seuil — Zones Tampons de Contrôle Climatique : trajectoire dominant → déclinant
- Genève Bunker — Forteresse Souveraine Climatique : texte « Elle contrôle l'accès aux ressources et à la protection… »
- Réseau Vert Clandestin : trajectoire ascendant → déclinant
- Nexus BioSyn — Division Eurasienne des Forteresses Vitales : trajectoire dominant → mature
- Nexus BioSyn — Division Pacifique des Corridors Vitaux : trajectoire dominant → mature
- Milices de Piraterie Logistique Arctique : texte « ils parasitent les corridors d'approvisionnement arctiques… »

_Propositions sans objet, écartées (déjà en place, ou relation à rompre absente du vault) (1) : relation factions_anti_privatisation_des_voies_souveraines_scandinaves_fortress_world / kalaallit_nunaat_sovereign_fund_fortress_world : opposition déjà présente_

_Réponses rejetées car mal formées (3) : trajectoire : anton_vasko_fortress_world ascendant → marginal (recul sur la phase de montée, incohérent) ; trajectoire : aymeric_de_valfort_fortress_world ascendant → marginal (recul sur la phase de montée, incohérent) ; trajectoire : conseil_regulation_ressources_fortress_world transformé → résiduel (recul dans la phase de déclin, incohérent ; une renaissance irait vers ascendant)_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Statuts de zone**
- [ ] 1. `afrique_subsaharienne_zones_effondrees` (Afrique Subsaharienne — Zones d'Effondrement Étatique) : fragmenté → en_declin
  - à la main : geographie/fortress_world.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario fortress_world --execute)
  - _L'effondrement des cartels miniers militarisés laisse un vide sécuritaire et économique dans les zones déjà fragiles._
- [ ] 2. `espace_nordique_arctique` (Espace Nordique et Arctique) : stable → dominant
  - à la main : geographie/fortress_world.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario fortress_world --execute)
  - _L'Arctique devient le hub spatial mondial incontournable pour l'accès à Shackleton, renforçant la position d'Euro-Nord._
- [ ] 3. `paris_hors` (Paris) : en_declin → fragmenté
  - à la main : geographie/fortress_world.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario fortress_world --execute)
  - _La perte de pouvoir des Ferrailleurs sur les métaux rares plonge la zone dans un chaos plus prononcé._
- [ ] 4. `bloc_eurasiatique_occidental` (Bloc Eurasiatique Occidental) : dominant → stable
  - à la main : geographie/fortress_world.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario fortress_world --execute)
  - _La forteresse perd de sa nécessité stratégique avec l'abondance des ressources, passant d'un statut dominant à stable._

**Élément**
- [ ] 5. Injecter l'événement `shackleton_platinoides_2052` en mode rupture (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios ; mode_impose: rupture écrit `mode: rupture` dans chaque fiche_
- [ ] 6. ⚠ Vérifier que la fiche porte `mode: rupture` et les forces simulées (frontieres_du_systeme −30, energie_ressources_critiques −32, geopolitique_conflits +35, systeme_economique_redistribution +28)
  - event_instances/shackleton_platinoides_2052_fortress_world.md ; python3 generator/trace_injection.py --slug shackleton_platinoides_2052 --type evenement --scenario fortress_world
  - _le Tracer doit finir chaque ligne « Déclaré » par « rupture » et retrouver l'effet simulé ; références déplacées par le moteur (rien à faire) : energie_ressources_critiques 82,0 → 51,5 ; frontieres_du_systeme 70,0 → 41,7 ; systeme_economique_redistribution 60,0 → 84,2 ; geopolitique_conflits 85,0 → 99,7 ; au plafond, plus aucune marge pour une autre crise : geopolitique_conflits_
- [ ] 7. Nouvelle référence : vérifier la lisibilité du moteur
  - `python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05`
  - _S19_

**Nouvelles entités**
- [ ] 8. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie proposée, à relire
  - étape ⑤ du panneau (« Ajouter à la file »), puis python3 generator/create_entities_and_instances.py --mode custom
  - _scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 9. Cartels Miniers Militarisés Subsahariens (`cartels_miniers_militarises_subsahariens_fortress_world`) : émergent → déclinant
  - à la main : instances/cartels_miniers_militarises_subsahariens_fortress_world.md, champ `trajectoire`
  - _L'abondance lunaire détruit leur monopole de fait sur les métaux rares terrestres qui justifiait le pillage des zones effondrées._
- [ ] 10. Les Ferrailleurs de Paris (`les_recycleurs_fortress_world`) : dominant → déclinant
  - à la main : instances/les_recycleurs_fortress_world.md, champ `trajectoire`
  - _Le marché des métaux rares contrôlé depuis Paris s'effondre face à l'offre massive de platinoïdes lunaires. ; instance custom : ne régénérer qu'avec generate_instances.py --injection-custom_
- [ ] 11. Consortium Eurasiatique des Ressources Fermées (`consortium_eurasiatique_des_ressources_fermees_fortress_world`) : émergent → déclinant
  - à la main : instances/consortium_eurasiatique_des_ressources_fermees_fortress_world.md, champ `trajectoire`
  - _La logique de fermeture des ressources critiques perd sa pertinence économique avec l'arrivée des métaux spatiaux._
- [ ] 12. Alpha47 - Complexe Minier Ergo-Wian (`alpha47_fortress_world`) : mature → déclinant
  - à la main : instances/alpha47_fortress_world.md, champ `trajectoire`
  - _La planète minière d'Ergo-Wian est directement concurrencée par Shackleton, plus accessible et moins coûteux à exploiter. ; instance custom : ne régénérer qu'avec generate_instances.py --injection-custom_
- [ ] 13. Complexes Militaro-Industriels de Gestion des Ressources (`complexes_militaro_industriels_de_gestion_des_ressources_fortress_world`) : émergent → ascendant
  - à la main : instances/complexes_militaro_industriels_de_gestion_des_ressources_fortress_world.md, champ `trajectoire`
  - _Ils pivotent vers la sécurisation des infrastructures d'extraction lunaire et des corridors spatiaux, devenant les nouveaux gardiens des ressources._
- [ ] 14. Réseaux privés de sécurité aux frontières (`reseaux_prives_de_securite_aux_frontieres_fortress_world`) : émergent → déclinant
  - à la main : instances/reseaux_prives_de_securite_aux_frontieres_fortress_world.md, champ `trajectoire`
  - _La pression sur les frontières diminue fortement car les blocs n'ont plus besoin de fermer hermétiquement pour sécuriser leurs approvisionnements en métaux._

**Relations**
- [ ] 15. opposition nouvelle : Cartels Miniers Militarisés Subsahariens ↔ Complexes Militaro-Industriels de Gestion des Ressources
  - à la main : ajouter `complexes_militaro_industriels_de_gestion_des_ressources_fortress_world` dans `oppositions` de instances/cartels_miniers_militarises_subsahariens_fortress_world.md
  - _Les cartels tentent de saboter l'accès lunaire pour préserver leur rente, tandis que les complexes veulent exploiter Shackleton._
- [ ] 16. opposition nouvelle : Les Ferrailleurs de Paris ↔ Nuna Capital — Fonds Souverain de Kalaallit Nunaat
  - à la main : ajouter `kalaallit_nunaat_sovereign_fund_fortress_world` dans `oppositions` de instances/les_recycleurs_fortress_world.md
  - _Concurrence directe pour le contrôle du marché mondial des métaux critiques entre Paris et le fonds groenlandais proche de l'Arctique._
- [ ] 17. alliance nouvelle : Nordisk Arktisk Transitkontroll — NAT ↔ Nexcore Atlantique Infrastructure — Division Séparation Climatique
  - à la main : ajouter `nexcore_atlantique_infrastructure_fortress_world` dans `alliances` de instances/armada_logistique_nordique_fortress_world.md
  - _Coopération pour construire et sécuriser les spatioports arctiques servant de base aux missions lunaires vers Shackleton._
- [ ] 18. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario fortress_world --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 19. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section fortress_world
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 20. Instances et événements relus par la passe exhaustive (obligatoires ci-dessus et dans les autres sections) ; aucune zone ni ligne du registre ne cite l'hypothèse

**Possibles (facultatif)**
- [ ] 21. Ilse Varga-Holm — Syndicat des Gestionnaires de Seuils (SGS) (`ilse_varga_holm_fortress_world`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Gestion directe des seuils de distribution des métaux extraits de Shackleton_
- [ ] 22. Consortium des Blocs Solaires Orbitaux Concurrents (`consortium_des_blocs_solaires_orbitaux_concurrents_fortress_world`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Approvisionnement énergétique orbital indispensable à la viabilité de l'extraction de Shackleton_
- [ ] 23. Consortiums de Défense Orbitale Privés (`consortiums_de_defense_orbitale_prives_fortress_world`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Contrôle de l'orbite comme goulot d'étranglement stratégique des métaux lunaires_
- [ ] 24. Instances ARIA Concurrentes des Blocs Rivaux (`instances_aria_concurrentes_des_blocs_rivaux_fortress_world`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Gestion de l'accès à la Lune et des flux de platinoïdes exige des IA de pilotage supérieures_
- [ ] 25. Helios Bloc Consortium — Division Souveraineté Énergétique (`consortium_helios_fortress_world`) : trajectoire transformé → ascendant [passe exhaustive]
  - _Fourniture de l'énergie nécessaire aux robots lunaires de Shackleton_
- [ ] 26. Commandement Stratégique des Matières Critiques Atlantique (`commandement_strategique_des_matieres_critiques_atlantique_fortress_world`) : trajectoire émergent → déclinant [passe exhaustive]
  - _Arbitrage des tensions sur l'accès aux ressources rendu obsolète par l'abondance (-29.2)_
- [ ] 27. Cartels Énergétiques des Bioréacteurs (`cartels_energetiques_des_bioreacteurs_fortress_world`) : trajectoire émergent → déclinant [passe exhaustive]
  - _Levier de survie des enclaves via les contrats énergétiques perd son urgence avec la fin de la crise (-29.2)_
- [ ] 28. Réseau d'Allocation Stratégique ARIA-Bloc (`grille_aria_fortress_world`) : texte « gérant l'allocation des ressources critiques — énergie,… » [passe exhaustive]
  - _Logique de souveraineté militarisée pour l'allocation des platinoïdes économiquement obsolète (-29.2)_
- [ ] 29. Détroits Souverains - ARDS Fragmentée (`agence_de_regulation_des_detroits_strategiques_ards_fortress_world`) : trajectoire déclinant → résiduel [passe exhaustive]
  - _Flux de ressources critiques ne transitent plus par les détroits (combine -29.2 et -27.7)_
- [ ] 30. Ceinture Productive Eurasiatique — Zones de Labeur Sous Mandat (`zone_usines_forteresses_eurasie_fortress_world`) : trajectoire dominant → déclinant [passe exhaustive]
  - _Production pour les forteresses riches perd son caractère avec les métaux déversés depuis la Lune_
- [ ] 31. Bloc Pacifique Nord (`bloc_pacifique_nord_fortress_world`) : trajectoire émergent → marginal [passe exhaustive]
  - _Capitalisation sur la rareté des réserves terrestres rendue obsolète par l'abondance lunaire (-29.2)_
- [ ] 32. Collectifs de Réappropriation Énergétique Périphérique (`collectifs_de_reappropriation_energetique_peripherique_fortress_world`) : trajectoire émergent → déclinant [passe exhaustive]
  - _Érosion du monopole énergétique avec la diminution de la crise des ressources critiques (-29.2)_
- [ ] 33. administrations de contrôle frontalier des blocs (`administrations_de_controle_frontalier_des_blocs_fortress_world`) : trajectoire émergent → marginal [passe exhaustive]
  - _Bras opérationnel de la fermeture des blocs perd son urgence avec -27.7 sur les frontières_
- [ ] 34. Appareils d'État des Blocs Fermés (`appareils_d_etat_des_blocs_fermes_fortress_world`) : trajectoire émergent → marginal [passe exhaustive]
  - _Définition et maintien des frontières dures entre blocs rendu non pertinent (-27.7)_
- [ ] 35. Bureaux de Contrôle Frontalier des Blocs Fermés (`bureaux_de_controle_frontalier_des_blocs_fermes_fortress_world`) : trajectoire émergent → marginal [passe exhaustive]
  - _Monopole total sur les passages frontaliers fragilisé par l'ouverture du système (-27.7)_
- [ ] 36. Les Campements des Checkpoints (`campements_seuils_fermes_fortress_world`) : trajectoire marginal → disparu [passe exhaustive]
  - _Disparition des campements due à la perte de fonction des seuils frontaliers_
- [ ] 37. agences de sécurité intérieure des États forteresses (`agences_de_securite_interieure_des_etats_forteresses_fortress_world`) : trajectoire émergent → marginal [passe exhaustive]
  - _Maintien de l'étanchéité des frontières impossible dans un monde fragmenté ouvert (-27.7)_
- [ ] 38. Pacte des Forteresses Souveraines (`alliance_blocs_souverains_fortress_world`) : trajectoire déclinant → résiduel [passe exhaustive]
  - _Logique de fermeture fondant le Pacte des Forteresses Souveraines fragilisée (-27.7)_
- [ ] 39. Conglomérats Industriels d'État des Augmentations Propriétaires (`conglomerats_industriels_d_etat_des_augmentations_proprietaires_fortress_world`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Coût des augmentations baisse avec les matériaux abondants, accélérant leur diffusion (+22.7)_
- [ ] 40. Syndicats Industriels Résiduels Post-Crise (`syndicats_industriels_residuels_post_crise_fortress_world`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Redistribution économique induite par l'abondance lunaire renforce la représentation des travailleurs (+22.7)_
- [ ] 41. … et 58 autre(s) fiche(s) avec des changements possibles
  - _détail dans la section « Passe exhaustive » de ce scénario_

**Articles et site**
- [ ] 42. 20 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« Les agents autonomes franchissent le seuil décisionnel : comment l'IA souveraine échappe à ses architectes »; « Quand les blocs se lisent eux-mêmes : l'IA décisionnelle au miroir de ses propres angles morts »; « Bruxelles-Forteresse, 12 octobre 2098 »; « Les Seuils de l’Âme : Quand la Spiritualité Devient Frontière »; « Arctique : la NAT frappe, le monde retient son souffle »; « Nexus7 : l’école où l’on apprend à oublier le dehors »; « Nexus7 : l’envers du paradis vertical »; « Le Marathon des Seuils : quand le sport défie les frontières du Bloc »; « Helios BSE coupe le courant sur la Pannonie : la "Stromsperre" comme arme de recentrage »; « Helios BSE active son protocole « Hiver Ciblé » : les zones tampons du Caucase privées d’énergie pour trois semaines » …_
- [ ] 43. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario fortress_world`
  - _payant, un appel_
- [ ] 44. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 45. Base
  - `python3 generator/validate.py`
- [ ] 46. Lore
  - `python3 generator/audit_lore.py --scenario fortress_world`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Consortium Shackleton d'Extraction Lunaire
  category: organisation
  role: Gère l'extraction robotisée des platinoïdes au pôle Sud lunaire et leur première mise sur le marché
    mondial.
  etat: émergent
  scenario_ref: fortress_world
  scenario_hint:
  - fortress_world
  zone_hint: espace_nordique_arctique
  source: et_si_shackleton_platinoides_2052
- nom: ARIA-Lune — Système d'Allocation des Métaux Orbitaux
  category: système
  role: Régule la distribution mondiale des métaux critiques lunaires pour éviter l'effondrement des économies
    terrestres dépendantes.
  etat: émergent
  scenario_ref: fortress_world
  scenario_hint:
  - fortress_world
  zone_hint: aria_instance_fantome
  source: et_si_shackleton_platinoides_2052
- nom: Garde Spatiale Nordique — Unité de Protection des Corridors Lunaires
  category: organisation
  role: Sécurise les trajectoires Terre-Lune et les installations de Shackleton contre les acteurs non
    alignés et les cartels hostiles.
  etat: émergent
  scenario_ref: fortress_world
  scenario_hint:
  - fortress_world
  zone_hint: corridor_arctique_transit
  source: et_si_shackleton_platinoides_2052
```

## reference

Apparu en 2052 dans le scénario reference, Dépôt de platinoïdes de Shackleton agit d'abord sur énergie ressources critiques, frontières du système, système économique redistribution et géopolitique conflits. Son effet le plus fort apaise énergie ressources critiques, avec un écart maximal de -30,0 points vers 2060. Par propagation, organisation territoires réagit à son tour environ 8 ans après l'apparition (+0,8 points au plus fort). Un contrecoup apparaît ensuite sur technologie information (-0,2 points vers 2074). En 2098, il en subsiste -29,4 points sur énergie ressources critiques.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| energie_ressources_critiques | 75,0 → 44,5 | 80,1 | 50,7 | **-29,4** | direct |
| frontieres_du_systeme | 55,0 → 27,7 | 62,5 | 35,5 | **-27,0** | direct |
| systeme_economique_redistribution | 70,0 → 92,8 | 82,9 | 99,9 | **+17,0** | direct |
| geopolitique_conflits | 75,0 → 95,2 | 88,7 | 100,0 | **+11,3** | direct |
| climat_environnement_global | 70,9 | 73,1 | 70,5 | **-2,6** | propagé |
| demographie_mobilite_humaine | 59,0 | 68,8 | 69,5 | **+0,7** | propagé |
| gouvernance_institutions | 40,0 | 53,8 | 54,1 | **+0,3** | propagé |
| valeurs_culture_tempo_sociale | 60,0 | 69,9 | 70,2 | **+0,3** | propagé |
| organisation_territoires | 65,0 | 75,3 | 75,6 | **+0,3** | propagé |
| sante_biotechnologies | 55,0 | 49,9 | 50,1 | **+0,2** | propagé |
| systemes_productifs_travail | 74,0 | 79,3 | 79,5 | **+0,2** | propagé |
| technologie_information | 80,0 | 92,8 | 92,7 | **-0,1** | propagé |

**Repères** :
- energie_ressources_critiques (direct) : pic -30,0 vers 2060
- frontieres_du_systeme (direct) : pic -27,3 vers 2057
- systeme_economique_redistribution (direct) : pic +20,8 vers 2060
- geopolitique_conflits (direct) : pic +12,9 vers 2056

**Tensions** : 33 sans l'hypothèse → 31 avec.
- ➖ disparaît : technologie_information (level 92) aggrave une crise déjà forte de frontieres_du_systeme (level 62)
- ➖ disparaît : frontieres_du_systeme (level 62) aggrave une crise déjà forte de systeme_economique_redistribution (level 82)
- ⬇ n'est plus une cascade critique : energie_ressources_critiques → geopolitique_conflits
- ⬇ n'est plus une cascade critique : energie_ressources_critiques → systeme_economique_redistribution
- ⬇ n'est plus une cascade critique : energie_ressources_critiques → systemes_productifs_travail
- ⬇ n'est plus une cascade critique : energie_ressources_critiques → climat_environnement_global
_Une tension se déclenche quand un niveau franchit un seuil (60, ou 70 pour une cascade, abaissés selon le risque de bascule de la variable) : un écart de quelques dixièmes peut suffire si le niveau était déjà au bord._

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

Le dépôt de Shackleton inonde le marché mondial de platinoïdes et terres rares lourdes, cassant la rente des acteurs miniers terrestres (Congo, Asie centrale, Groenland) tout en créant un nouvel axe géopolitique spatial centré sur l'arc arctique. Ce choc ne modifie aucune frontière territoriale mais reconfigure les rapports de force entre extracteurs terrestres déclinants et nouveaux opérateurs lunaires. L'équilibre fragile du scénario se déplace vers une économie cislunaire où le corridor arctique nordique devient le pivot de l'approvisionnement en métaux critiques. _(ampleur : bascule)_

**Trajectoires d'entités**
- Consortiums d'Extraction Minière du Bassin Congolais (`consortiums_d_extraction_miniere_du_bassin_congolais_reference`) : émergent → **déclinant** — La valeur des terres rares congolaises s'effondre face à l'abondance lunaire de platinoïdes.
- Cartel des Terres Rares d'Asie Centrale (`cartel_des_terres_rares_d_asie_centrale_reference`) : émergent → **déclinant** — Son monopole sur les terres rares lourdes est brisé par l'offre massive de Shackleton.
- Kalaallit Nunaat Sovereign Fund (`kalaallit_nunaat_sovereign_fund_reference`) : ascendant → **déclinant** — Les revenus du Groenland tirés des terres rares terrestres perdent leur avantage compétitif face à la Lune.
- Bloc Ressources Eurasiatique (BRE) (`bloc_ressources_eurasiatique_bre_reference`) : émergent → **déclinant** — Son levier géopolitique fondé sur le contrôle des ressources critiques terrestres s'érode avec la dévalorisation de ces métaux.
- Consortiums Privés d'Extraction de Ressources Critiques (`consortiums_prives_d_extraction_de_ressources_critiques_reference`) : émergent → **ascendant** — Ils pivotent vers l'extraction lunaire et deviennent les nouveaux maîtres des flux de platinoïdes.
- Fonds Souverains de la Ceinture Financière Pacifique (`fonds_souverains_de_la_ceinture_financiere_pacifique_reference`) : émergent → **ascendant** — Ils financent massivement les infrastructures d'extraction et de transport lunaire, prenant le contrôle du nouvel axe spatial.

**Relations**
- alliance nouvelle : Consortiums Privés d'Extraction de Ressources Critiques ↔ Consortium Helios — Couplage entre extraction lunaire de platinoïdes et infrastructure solaire orbitale pour alimenter les robots d'extraction.
- alliance nouvelle : OptiFlow Global Logistics Network (OGLN) ↔ Consortiums Privés d'Extraction de Ressources Critiques — OGLN organise et sécurise les flux de retour des métaux lunaires vers les marchés terrestres.
- opposition nouvelle : Autorité de Régulation des Passages Stratégiques (ARPS) ↔ Consortium Helios — L'ARPS revendique la régulation du 'détroit cislunaire' face au quasi-régulateur privé de l'énergie orbitale.
- opposition nouvelle : Cartel des Terres Rares d'Asie Centrale ↔ Consortiums d'Extraction Minière du Bassin Congolais — Rivalité entre anciens fournisseurs terrestres qui tentent de saboter l'extraction lunaire pour préserver leurs prix.

**Statut des zones**
- Nuuk-Capitale (`nuuk_capitale_groenland`) : emergent → **en_declin** — La capitale groenlandaise perd son statut de hub stratégique des terres rares face à la concurrence lunaire.
- Corridors Eurasiens Centraux (`corridors_eurasiens_zones_grises`) : fragmenté → **en_declin** — L'effondrement du cartel des terres rares d'Asie centrale fragilise ces corridors périphériques.
- Bloc Eurasien Central (`bloc_eurasien_central`) : fragmenté → **en_declin** — Le déclin du BRE, pilier du bloc, entraîne une fragilisation générale de la zone eurasiatique.

**Nouvelles entités plausibles**
- Consortium Shackleton d'Extraction Lunaire (corridor_arctique_nordique) [entreprise] : Opérateur privé dominant de l'extraction des platinoïdes du cratère de Shackleton, contrôlant les flux de métaux critiques vers la Terre depuis 2055. — L'extraction viable crée un nouvel acteur économique majeur basé dans l'arc arctique qui contrôle l'accès spatial et les robots lunaires.
- Ligue des Terres Rares Terrestres (zones_grises_globales) [organisation] : Cartel défensif des producteurs terrestres de terres rares (Congo, Asie centrale, Groenland) cherchant à limiter l'offre lunaire pour préserver leurs rentes. — Les acteurs miniers terrestres menacés par l'abondance lunaire s'organisent dans les marges pour défendre leurs intérêts économiques.
- Autorité de Transit Cislunaire (corridor_arctique_nordique) [infrastructure] : Réseau de contrôle du trafic spatial entre la Terre et la Lune, gérant les corridors de lancement et de rentrée des cargaisons de platinoïdes. — La massification des flux lunaires nécessite une infrastructure dédiée de régulation du trafic orbital depuis les bases arctiques.

_Propositions écartées au contrôle (2) : relation kalaallit_nunaat_sovereign_fund_reference / consortiums_prives_d_extraction_de_ressources_critiques_reference : opposition déjà présente ; relation bloc_ressources_eurasiatique_bre_reference / armada_logistique_nordique_reference : opposition déjà présente_

### Passe exhaustive (IA, toutes les fiches — rien n'est écrit)

200 fiche(s) relue(s) en 14 lot(s).
Verdicts : **1 fiche(s) à corriger**, 73 avec des changements possibles seulement, 126 inchangée(s).

_Contre-lecture des obligatoires : 2 vérifié(s), 1 confirmé(s), 1 rétrogradé(s) en possible._

#### Obligatoire — la fiche devient fausse sans ce changement

**Textes**
- instance Cartel des Terres Rares d'Asie Centrale (`cartel_des_terres_rares_d_asie_centrale_reference`) : « conditionne concrètement l'accès aux ressources critiques indispensables aux technologies de 2098 » — contredit par : Les métaux critiques extraits de Shackleton arrivent en masse sur le marché mondial, rendant l'accès indépendant du Cartel et abondant. — La phrase affirme un monopole d'accès que l'élément rend faux. [lien variable : energie_ressources_critiques (-29.4)]

#### Possible — conséquence plausible, la fiche reste vraie sans elle

_Rétrogradés d'obligatoire à possible par les contrôles : 1 contre-lecture nuance, 1 atténue le rôle sans le contredire._

**À lire en priorité (20 fiches sur 73)** — choisies et ordonnées par l'IA

- **Armada Logistique Nordique** (`armada_logistique_nordique_reference`) — _Alliance logistique créée directement par le flux massif de métaux lunaires transitant par l'arc arctique_
  - alliance nouvelle : Armada Logistique Nordique ↔ Consortiums Privés d'Extraction de Ressources Critiques — L'élément crée un flux massif de métaux lunaires transitant par l'arc arctique, créant une alliance logistique avec les nouveaux opérateurs d'extraction cislunaire. [lien relation : Alliée potentielle d'une entité directement touchée (consortiums_prives_d_extraction_de_ressources_critiques_reference, devenus ascendants) via le corridor arctique pivot]
- **Réseau des Citadelles du Sud-Pacifique (RCSP)** (`holdfast_reference`) — _Reconversion directe des enclaves en bases logistiques pour les nouveaux opérateurs lunaires_
  - Réseau des Citadelles du Sud-Pacifique (RCSP) (`holdfast_reference`) : résiduel → **ascendant** — les enclaves reconverties en bases logistiques pour les nouveaux opérateurs lunaires gagnent une importance stratégique dans l'économie cislunaire [lien relation : allié de consortiums_prives_d_extraction_de_ressources_critiques_reference qui devient ascendant grâce au dépôt de Shackleton]
- **Consortium de Maintenance Orbitale SEOM-7** (`consortium_de_maintenance_orbitale_seom_7_reference`) — _Maintenance orbitale devenue infrastructure de dernier recours pour les flux lunaires via l'arc arctique_
  - Consortium de Maintenance Orbitale SEOM-7 (`consortium_de_maintenance_orbitale_seom_7_reference`) : émergent → **ascendant** — La maintenance orbitale devient l'infrastructure de dernier recours pour les flux lunaires via l'arc arctique. [lien variable : La variable frontieres_du_systeme chute de 27.0 points avec l'ouverture de l'axe cislunaire et la reconfiguration du corridor arctique, élargissant le domaine orbital critique géré par SEOM-7] — contredit : Le dépôt de Shackleton crée un nouvel axe géopolitique spatial centré sur l'arc arctique et une économie cislunaire
- **Consortium des Grandes Plateformes Logistiques Globales** (`consortium_des_grandes_plateformes_logistiques_globales_reference`) — _Extension nécessaire de l'épine dorsale logistique mondiale à l'axe Terre-Lune_
  - Consortium des Grandes Plateformes Logistiques Globales (`consortium_des_grandes_plateformes_logistiques_globales_reference`) : émergent → **ascendant** — L'épine dorsale logistique mondiale s'étend nécessairement à l'axe Terre-Lune via le corridor arctique. [lien variable : La variable frontieres_du_systeme chute de 27.0 points avec la reconfiguration des frontières logistiques vers l'arc arctique et l'orbite lunaire] — contredit : Le corridor arctique nordique devient le pivot de l'approvisionnement en métaux critiques venus de la Lune
- **Conseil des États Nordiques Intégrés** (`conseil_des_etats_nordiques_integres_reference`) — _Centralité géopolitique accrue par la reconfiguration des frontières vers l'arc arctique_
  - Conseil des États Nordiques Intégrés (`conseil_des_etats_nordiques_integres_reference`) : ascendant → **dominant** — La reconfiguration des frontières du système vers l'arc arctique accroît leur centralité géopolitique dans la nouvelle économie cislunaire. [lien variable : frontieres_du_systeme (-27.0 points) : le corridor arctique nordique qu'ils administrent devient le pivot de l'approvisionnement mondial en métaux critiques lunaires]
- **Hyphan Raghavan de Ergo-Wian Sovereign Holdings** (`hyphan_raghavan_reference`) — _Montée en puissance directe des consortiums d'extraction lunaire au sein du Pacte des Souverains_
  - Hyphan Raghavan de Ergo-Wian Sovereign Holdings (`hyphan_raghavan_reference`) : ascendant → **dominant** — la montée en puissance des consortiums d'extraction lunaire renforce le poids d'Hyphan Raghavan au sein du Pacte des Souverains [lien relation : alliée de consortiums_prives_d_extraction_de_ressources_critiques_reference qui deviennent ascendants via l'extraction de Shackleton]
- **ONG de Traçabilité des Ressources Critiques** (`ong_de_tracabilite_des_ressources_critiques_reference`) — _Nouveau besoin de distinguer la provenance lunaire vs terrestre créé par l'abondance de platinoïdes_
  - ONG de Traçabilité des Ressources Critiques (`ong_de_tracabilite_des_ressources_critiques_reference`) : émergent → **ascendant** — l'abondance de métaux lunaires augmente l'importance de distinguer la provenance des ressources critiques entre extraction terrestre et lunaire [lien variable : dépend de energie_ressources_critiques (-29.4 points) : l'inondation du marché par les platinoïdes lunaires rend la traçabilité de l'origine des métaux critiques stratégique]
- **Coopératives Énergétiques Décentralisées** (`cooperatives_energetiques_decentralisees_reference`) — _Score chiffré de tension énergétique mentionné dans la fiche directement modifié par l'élément_
  - instance Coopératives Énergétiques Décentralisées (`cooperatives_energetiques_decentralisees_reference`) : « face à un système énergétique mondial sous tension (score 72/100) » — contredit par : la variable energie_ressources_critiques baisse de 29.4 points suite à l'inondation du marché par les métaux lunaires, ramenant le niveau de crise bien en dessous de 72/100 — le score chiffré de tension énergétique mentionné dans la fiche est directement modifié par l'élément perturbateur [lien variable : energie_ressources_critiques (-29.4 points)] _(rétrogradé : atténue le rôle sans le contredire)_
- **Agence Internationale des Énergies Renouvelables (IRENA-2)** (`agence_internationale_des_energies_renouvelables_irena_2_reference`) — _Effondrement de la rente des ressources critiques terrestres (-29.4) augmente l'importance stratégique des ENR_
  - Agence Internationale des Énergies Renouvelables (IRENA-2) (`agence_internationale_des_energies_renouvelables_irena_2_reference`) : émergent → **ascendant** — L'effondrement de la rente des ressources critiques terrestres augmente l'importance stratégique des énergies renouvelables dans le système mondial. [lien variable : Dépend directement de energie_ressources_critiques (-29.4 points)]
- **Régulateurs de l'Union Continentale Africaine** (`regulateurs_de_l_union_continentale_africaine_reference`) — _Inondation du marché par les platinoïdes lunaires rend la régulation des ressources critiques centrale dans les arbitrages africains_
  - Régulateurs de l'Union Continentale Africaine (`regulateurs_de_l_union_continentale_africaine_reference`) : émergent → **ascendant** — l'inondation du marché mondial par les platinoïdes et terres rares lunaires rend la régulation des ressources critiques plus centrale dans les arbitrages continentaux, renforçant le poids des Régulateurs de l'UCA [lien variable : dépend de energie_ressources_critiques (-29.4) via son rôle d'imposition de cadres communs sur les ressources critiques]
- **Banque des Communs** (`banque_des_communs_reference`) — _Casse de la rente minière terrestre augmente les territoires où les circuits marchands se rétractent_
  - Banque des Communs (`banque_des_communs_reference`) : émergent → **ascendant** — La casse de la rente minière terrestre augmente le nombre de territoires où les circuits marchands se rétractent, élargissant le champ d'action de la Banque des Communs. [lien variable : systeme_economique_redistribution (+17.0)]
- **Bloc des États du Sud Global contre la Cession de Données** (`bloc_des_etats_du_sud_global_contre_la_cession_de_donnees_reference`) — _Perte de rente des pays extracteurs du Sud Global renforce la légitimité du Bloc comme voix des perdants_
  - Bloc des États du Sud Global contre la Cession de Données (`bloc_des_etats_du_sud_global_contre_la_cession_de_donnees_reference`) : émergent → **ascendant** — La perte de rente des pays extracteurs du Sud Global renforce la légitimité du Bloc comme voix des perdants de la reconfiguration économique cislunaire. [lien variable : systeme_economique_redistribution (+17.0)]
- **Assemblée des Territoires Fédérés (ATF)** (`assemblee_territoires_reference`) — _Redistribution économique massive (+17.0) nécessite une coordination territoriale renforcée entre territoires fédérés_
  - Assemblée des Territoires Fédérés (ATF) (`assemblee_territoires_reference`) : ascendant → **dominant** — La redistribution économique massive induite par l'arrivée des métaux lunaires nécessite une coordination territoriale renforcée entre les territoires fédérés. [lien variable : Dépend directement de systeme_economique_redistribution (+17.0 points)]
- **Agences de Sécurité Régionales de Normalisation des Zones Grises** (`agences_de_securite_regionales_de_normalisation_des_zones_grises_reference`) — _Crise des frontières du système (-27.0) augmente directement le besoin de normalisation des zones grises_
  - Agences de Sécurité Régionales de Normalisation des Zones Grises (`agences_de_securite_regionales_de_normalisation_des_zones_grises_reference`) : émergent → **ascendant** — La crise des frontières du système augmente le besoin de normalisation des zones grises par ces agences. [lien variable : Dépend directement de frontieres_du_systeme (-27.0 points)]
- **Mouvement pour la Libre Circulation des Personnes et des Données** (`mouvement_pour_la_libre_circulation_des_personnes_et_des_donnees_reference`) — _Crise des frontières (-27.0) alimente directement la pression pour l'abolition des barrières à la mobilité_
  - Mouvement pour la Libre Circulation des Personnes et des Données (`mouvement_pour_la_libre_circulation_des_personnes_et_des_donnees_reference`) : émergent → **ascendant** — La crise des frontières du système (-27.0 points) alimente la pression pour l'abolition des barrières à la mobilité. [lien variable : frontieres_du_systeme -27.0] — contredit : aucun
- **Pacte des Souverains** (`alliance_blocs_souverains_reference`) — _Augmentation des conflits géopolitiques (+11.3) renforce le Pacte des Souverains comme alternative diplomatique_
  - Pacte des Souverains (`alliance_blocs_souverains_reference`) : ascendant → **dominant** — L'augmentation des conflits géopolitiques induite par l'élément renforce le Pacte des Souverains comme alternative diplomatique. [lien variable : Dépend directement de geopolitique_conflits (+11.3 points)]
- **Sibérie Fédérale** (`siberie_federale_reference`) — _Crise des frontières (-27.0) affaiblit les délimitations territoriales que la Sibérie conteste_
  - Sibérie Fédérale (`siberie_federale_reference`) : marginal → **ascendant** — la crise des frontières du système affaiblit les délimitations territoriales qu'elle conteste, renforçant sa pertinence dans l'arc arctique reconfiguré [lien variable : frontieres_du_systeme -27.0]
- **Alliance pour la Souveraineté Maritime des Peuples Insulaires (ASMPI)** (`pacifique_sud_resilience_network_reference`) — _Face à la puissance des nouveaux opérateurs lunaires, l'ASMPI affirme son cadre juridique post-territorial_
  - Alliance pour la Souveraineté Maritime des Peuples Insulaires (ASMPI) (`pacifique_sud_resilience_network_reference`) : ascendant → **dominant** — face à la puissance des nouveaux opérateurs lunaires, l'ASMPI affirme son cadre juridique post-territorial pour négocier l'accès aux ressources et les droits souverains mobiles [lien relation : rivale des consortiums_prives_d_extraction_de_ressources_critiques_reference qui deviennent ascendants avec l'extraction lunaire]
- **Conseil de Genève pour les Droits Biosociaux** (`conseil_de_geneve_pour_les_droits_biosociaux_reference`) — _Ascension des nouveaux opérateurs d'extraction lunaire intensifie les conflits sur les droits biosociaux_
  - Conseil de Genève pour les Droits Biosociaux (`conseil_de_geneve_pour_les_droits_biosociaux_reference`) : émergent → **ascendant** — L'ascension des nouveaux opérateurs d'extraction intensifie les conflits sur les droits biosociaux, renforçant leur rôle de point de friction institutionnel. [lien relation : rivaux de consortiums_prives_d_extraction_de_ressources_critiques_reference, devenus ascendants avec l'extraction lunaire]
- **Consortiums Bancaires Financiarisés** (`consortiums_bancaires_financiarises_reference`) — _Infrastructures de clearing devenues critiques pour financer les nouvelles chaînes d'approvisionnement lunaires_
  - Consortiums Bancaires Financiarisés (`consortiums_bancaires_financiarises_reference`) : émergent → **ascendant** — Les infrastructures de clearing deviennent critiques pour financer les nouvelles chaînes d'approvisionnement lunaires. [lien variable : La variable systeme_economique_redistribution augmente de 17.0 points vers l'économie cislunaire, créant de nouveaux flux financiers que les consortiums bancaires doivent traiter via leurs infrastructures de clearing] — contredit : Le système économique mondial se redistribue vers l'axe cislunaire et le corridor arctique

**Autres fiches avec des changements possibles (53)**
- Amara Diallo-Nkosi : trajectoire mature → ascendant
- Autorité de Passage Arctique : trajectoire mature → dominant
- Bloc Eurasien Central (BEC) : trajectoire déclinant → résiduel
- Collectifs de Biopiraterie Inversée : trajectoire émergent → ascendant
- Collectifs de Pêche Inuit et Sami : trajectoire ascendant → dominant
- Consortium Africain de Biotechnologies Sociales (CABS) : trajectoire ascendant → dominant
- Consortium Amazônia Viva : trajectoire ascendant → dominant
- Consortium AugmentWork : trajectoire émergent → marginal
- Alliance des Glaces Libres (AGL) : trajectoire ascendant → déclinant
- Consortium Énergétique Baltique : trajectoire émergent → ascendant
- Consortium Énergétique des Mers du Nord : trajectoire émergent → ascendant
- Consortium Indo-Pacifique de l'Hydrogène : trajectoire émergent → ascendant
- Consortium Logistique Asiatique de Contournement ALN : trajectoire émergent → déclinant
- Leena Väinälä : trajectoire ascendant → dominant
- Opérateurs Logistiques Privés des Zones Grises Eurasiennes : trajectoire émergent → déclinant ; alliance rompue avec Cartel des Terres Rares d'Asie Centrale
- Plateformes Centralisées de Narration Officielle : trajectoire émergent → déclinant
- Régulateurs de l'Union Eurasiatique sur les Données Critiques : trajectoire émergent → marginal
- Réseau des Villes-États Pilotes en Gouvernance Participative : trajectoire émergent → ascendant
- Réseau des Villes-Refuge pour Travailleurs Désaugmentés : trajectoire émergent → marginal
- Syndicats de travail rural hybride : trajectoire émergent → marginal
- Syndicats de travailleurs de la transition énergétique : trajectoire émergent → marginal
- Banque Mondiale des Transitions Climatiques : trajectoire émergent → ascendant
- Bloc des Souverainistes Climatiques : trajectoire émergent → ascendant
- Blocs Signataires du Pacte Énergétique Multilatéral : trajectoire émergent → ascendant
- Bruxelles Nouveau : trajectoire déclinant → résiduel
- Bureau des Zones Non Prioritaires (BZNP) : trajectoire déclinant → résiduel
- Bureaux de Régulation Informationnelle : trajectoire émergent → ascendant
- Coalition des Gouvernements Contre les Chartes de Déstabilisation : trajectoire émergent → ascendant
- Coalition pour la Souveraineté Numérique Nationale : trajectoire émergent → ascendant
- Commission Hydrique de l'Union Africaine : trajectoire émergent → ascendant
- Conseil de Régulation des Ressources Critiques : trajectoire déclinant → résiduel
- Consortium des Fournisseurs d'Énergie Renouvelable Distribuée : trajectoire émergent → ascendant
- Consortium des Grandes Plateformes IA Intégrées : trajectoire émergent → ascendant
- Consortiums d'Agriculture Verticale Algorithmique : trajectoire ascendant → dominant
- Consortiums Énergétiques des Mégapoles : trajectoire émergent → ascendant
- Factions d'Extraction Minière Indépendantes : trajectoire émergent → déclinant
- Raj Mehta : trajectoire ascendant → dominant
- Ligue des Métropoles du Sud pour les Infrastructures Libres : trajectoire émergent → ascendant
- Milices Concurrentes des Droits de Passage : trajectoire émergent → ascendant
- Nairobi CRRC — Centre Régional de Résilience et de Coordination : trajectoire mature → déclinant
- Opérateurs de Zones Économiques Spéciales Périurbaines : trajectoire émergent → ascendant
- Opérateurs Privés d'Énergie Distribuée Hors-FCT : trajectoire émergent → ascendant
- Alliance des Blocs Souverains (ABS) : trajectoire mature → déclinant
- Plateformes d'Optimisation Territoriale par IA : trajectoire émergent → ascendant
- Réseau Hospitalier Hybride Eurasiatique : trajectoire émergent → ascendant
- Services de contre-information des blocs géopolitiques concurrents : trajectoire émergent → ascendant
- Bloc Ressources Eurasiatique (BRE) : texte « capable d'influer sur les prix mondiaux de l'énergie et des… »
- Agence Mondiale pour la Stabilisation Climatique : trajectoire mature → ascendant
- Collectifs de Journalisme Embarqué : trajectoire émergent → ascendant
- Communs Numériques Agroécologiques : trajectoire émergent → ascendant
- Institut Polytechnique de Ouagadougou : trajectoire émergent → ascendant
- Réseau des Coopératives Agro-Sahéliennes : trajectoire émergent → ascendant
- Réseau des Métropoles Côtières Adaptées : trajectoire émergent → ascendant

_Propositions sans objet, écartées (déjà en place, ou relation à rompre absente du vault) (1) : relation ong_de_tracabilite_des_ressources_critiques_reference / consortiums_prives_d_extraction_de_ressources_critiques_reference : opposition déjà présente_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Statuts de zone**
- [ ] 1. `nuuk_capitale_groenland` (Nuuk-Capitale) : emergent → en_declin
  - à la main : geographie/reference.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario reference --execute)
  - _La capitale groenlandaise perd son statut de hub stratégique des terres rares face à la concurrence lunaire._
- [ ] 2. `corridors_eurasiens_zones_grises` (Corridors Eurasiens Centraux) : fragmenté → en_declin
  - à la main : geographie/reference.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario reference --execute)
  - _L'effondrement du cartel des terres rares d'Asie centrale fragilise ces corridors périphériques._
- [ ] 3. `bloc_eurasien_central` (Bloc Eurasien Central) : fragmenté → en_declin
  - à la main : geographie/reference.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario reference --execute)
  - _Le déclin du BRE, pilier du bloc, entraîne une fragilisation générale de la zone eurasiatique._

**Élément**
- [ ] 4. Injecter l'événement `shackleton_platinoides_2052` en mode rupture (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios ; mode_impose: rupture écrit `mode: rupture` dans chaque fiche_
- [ ] 5. Vérifier que la fiche porte `mode: rupture` et les forces simulées (frontieres_du_systeme −30, energie_ressources_critiques −32, geopolitique_conflits +28, systeme_economique_redistribution +30)
  - event_instances/shackleton_platinoides_2052_reference.md ; python3 generator/trace_injection.py --slug shackleton_platinoides_2052 --type evenement --scenario reference
  - _le Tracer doit finir chaque ligne « Déclaré » par « rupture » et retrouver l'effet simulé ; références déplacées par le moteur (rien à faire) : energie_ressources_critiques 75,0 → 44,5 ; frontieres_du_systeme 55,0 → 27,7 ; systeme_economique_redistribution 70,0 → 92,8 ; geopolitique_conflits 75,0 → 95,2_
- [ ] 6. Nouvelle référence : vérifier la lisibilité du moteur
  - `python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05`
  - _S19_

**Nouvelles entités**
- [ ] 7. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie proposée, à relire
  - étape ⑤ du panneau (« Ajouter à la file »), puis python3 generator/create_entities_and_instances.py --mode custom
  - _scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 8. Consortiums d'Extraction Minière du Bassin Congolais (`consortiums_d_extraction_miniere_du_bassin_congolais_reference`) : émergent → déclinant
  - à la main : instances/consortiums_d_extraction_miniere_du_bassin_congolais_reference.md, champ `trajectoire`
  - _La valeur des terres rares congolaises s'effondre face à l'abondance lunaire de platinoïdes._
- [ ] 9. Cartel des Terres Rares d'Asie Centrale (`cartel_des_terres_rares_d_asie_centrale_reference`) : émergent → déclinant
  - à la main : instances/cartel_des_terres_rares_d_asie_centrale_reference.md, champ `trajectoire`
  - _Son monopole sur les terres rares lourdes est brisé par l'offre massive de Shackleton._
- [ ] 10. Kalaallit Nunaat Sovereign Fund (`kalaallit_nunaat_sovereign_fund_reference`) : ascendant → déclinant
  - à la main : instances/kalaallit_nunaat_sovereign_fund_reference.md, champ `trajectoire`
  - _Les revenus du Groenland tirés des terres rares terrestres perdent leur avantage compétitif face à la Lune._
- [ ] 11. Bloc Ressources Eurasiatique (BRE) (`bloc_ressources_eurasiatique_bre_reference`) : émergent → déclinant
  - à la main : instances/bloc_ressources_eurasiatique_bre_reference.md, champ `trajectoire`
  - _Son levier géopolitique fondé sur le contrôle des ressources critiques terrestres s'érode avec la dévalorisation de ces métaux._
- [ ] 12. Consortiums Privés d'Extraction de Ressources Critiques (`consortiums_prives_d_extraction_de_ressources_critiques_reference`) : émergent → ascendant
  - à la main : instances/consortiums_prives_d_extraction_de_ressources_critiques_reference.md, champ `trajectoire`
  - _Ils pivotent vers l'extraction lunaire et deviennent les nouveaux maîtres des flux de platinoïdes._
- [ ] 13. Fonds Souverains de la Ceinture Financière Pacifique (`fonds_souverains_de_la_ceinture_financiere_pacifique_reference`) : émergent → ascendant
  - à la main : instances/fonds_souverains_de_la_ceinture_financiere_pacifique_reference.md, champ `trajectoire`
  - _Ils financent massivement les infrastructures d'extraction et de transport lunaire, prenant le contrôle du nouvel axe spatial._

**Relations**
- [ ] 14. alliance nouvelle : Consortiums Privés d'Extraction de Ressources Critiques ↔ Consortium Helios
  - à la main : ajouter `consortium_helios_reference` dans `alliances` de instances/consortiums_prives_d_extraction_de_ressources_critiques_reference.md
  - _Couplage entre extraction lunaire de platinoïdes et infrastructure solaire orbitale pour alimenter les robots d'extraction._
- [ ] 15. alliance nouvelle : OptiFlow Global Logistics Network (OGLN) ↔ Consortiums Privés d'Extraction de Ressources Critiques
  - à la main : ajouter `consortiums_prives_d_extraction_de_ressources_critiques_reference` dans `alliances` de instances/optiflow_logistics_reference.md
  - _OGLN organise et sécurise les flux de retour des métaux lunaires vers les marchés terrestres._
- [ ] 16. opposition nouvelle : Autorité de Régulation des Passages Stratégiques (ARPS) ↔ Consortium Helios
  - à la main : ajouter `consortium_helios_reference` dans `oppositions` de instances/agence_de_regulation_des_detroits_strategiques_ards_reference.md
  - _L'ARPS revendique la régulation du 'détroit cislunaire' face au quasi-régulateur privé de l'énergie orbitale._
- [ ] 17. opposition nouvelle : Cartel des Terres Rares d'Asie Centrale ↔ Consortiums d'Extraction Minière du Bassin Congolais
  - à la main : ajouter `consortiums_d_extraction_miniere_du_bassin_congolais_reference` dans `oppositions` de instances/cartel_des_terres_rares_d_asie_centrale_reference.md
  - _Rivalité entre anciens fournisseurs terrestres qui tentent de saboter l'extraction lunaire pour préserver leurs prix._
- [ ] 18. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario reference --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 19. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section reference
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 20. Corriger une phrase de `cartel_des_terres_rares_d_asie_centrale_reference` [passe exhaustive]
  - à la main : instances/cartel_des_terres_rares_d_asie_centrale_reference.md
  - _« conditionne concrètement l'accès aux ressources critiques indispensables aux technologies de 2098 » — contredit par : Les métaux critiques extraits de Shackleton arrivent en masse sur le marché mondial, rendant l'accès indépendant du Cartel et abondant._
- [ ] 21. Instances et événements relus par la passe exhaustive (obligatoires ci-dessus et dans les autres sections) ; aucune zone ni ligne du registre ne cite l'hypothèse

**Possibles (facultatif)**
- [ ] 22. Armada Logistique Nordique (`armada_logistique_nordique_reference`) : alliance nouvelle avec Consortiums Privés d'Extraction de Ressources Critiques [passe exhaustive]
  - _Alliance logistique créée directement par le flux massif de métaux lunaires transitant par l'arc arctique_
- [ ] 23. Réseau des Citadelles du Sud-Pacifique (RCSP) (`holdfast_reference`) : trajectoire résiduel → ascendant [passe exhaustive]
  - _Reconversion directe des enclaves en bases logistiques pour les nouveaux opérateurs lunaires_
- [ ] 24. Consortium de Maintenance Orbitale SEOM-7 (`consortium_de_maintenance_orbitale_seom_7_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Maintenance orbitale devenue infrastructure de dernier recours pour les flux lunaires via l'arc arctique_
- [ ] 25. Consortium des Grandes Plateformes Logistiques Globales (`consortium_des_grandes_plateformes_logistiques_globales_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Extension nécessaire de l'épine dorsale logistique mondiale à l'axe Terre-Lune_
- [ ] 26. Conseil des États Nordiques Intégrés (`conseil_des_etats_nordiques_integres_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Centralité géopolitique accrue par la reconfiguration des frontières vers l'arc arctique_
- [ ] 27. Hyphan Raghavan de Ergo-Wian Sovereign Holdings (`hyphan_raghavan_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Montée en puissance directe des consortiums d'extraction lunaire au sein du Pacte des Souverains_
- [ ] 28. ONG de Traçabilité des Ressources Critiques (`ong_de_tracabilite_des_ressources_critiques_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Nouveau besoin de distinguer la provenance lunaire vs terrestre créé par l'abondance de platinoïdes_
- [ ] 29. Coopératives Énergétiques Décentralisées (`cooperatives_energetiques_decentralisees_reference`) : texte « face à un système énergétique mondial sous tension (score… » [passe exhaustive]
  - _Score chiffré de tension énergétique mentionné dans la fiche directement modifié par l'élément_
- [ ] 30. Agence Internationale des Énergies Renouvelables (IRENA-2) (`agence_internationale_des_energies_renouvelables_irena_2_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Effondrement de la rente des ressources critiques terrestres (-29.4) augmente l'importance stratégique des ENR_
- [ ] 31. Régulateurs de l'Union Continentale Africaine (`regulateurs_de_l_union_continentale_africaine_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Inondation du marché par les platinoïdes lunaires rend la régulation des ressources critiques centrale dans les arbitrages africains_
- [ ] 32. Banque des Communs (`banque_des_communs_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Casse de la rente minière terrestre augmente les territoires où les circuits marchands se rétractent_
- [ ] 33. Bloc des États du Sud Global contre la Cession de Données (`bloc_des_etats_du_sud_global_contre_la_cession_de_donnees_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Perte de rente des pays extracteurs du Sud Global renforce la légitimité du Bloc comme voix des perdants_
- [ ] 34. Assemblée des Territoires Fédérés (ATF) (`assemblee_territoires_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Redistribution économique massive (+17.0) nécessite une coordination territoriale renforcée entre territoires fédérés_
- [ ] 35. Agences de Sécurité Régionales de Normalisation des Zones Grises (`agences_de_securite_regionales_de_normalisation_des_zones_grises_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Crise des frontières du système (-27.0) augmente directement le besoin de normalisation des zones grises_
- [ ] 36. Mouvement pour la Libre Circulation des Personnes et des Données (`mouvement_pour_la_libre_circulation_des_personnes_et_des_donnees_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Crise des frontières (-27.0) alimente directement la pression pour l'abolition des barrières à la mobilité_
- [ ] 37. Pacte des Souverains (`alliance_blocs_souverains_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Augmentation des conflits géopolitiques (+11.3) renforce le Pacte des Souverains comme alternative diplomatique_
- [ ] 38. Sibérie Fédérale (`siberie_federale_reference`) : trajectoire marginal → ascendant [passe exhaustive]
  - _Crise des frontières (-27.0) affaiblit les délimitations territoriales que la Sibérie conteste_
- [ ] 39. Alliance pour la Souveraineté Maritime des Peuples Insulaires (ASMPI) (`pacifique_sud_resilience_network_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Face à la puissance des nouveaux opérateurs lunaires, l'ASMPI affirme son cadre juridique post-territorial_
- [ ] 40. Conseil de Genève pour les Droits Biosociaux (`conseil_de_geneve_pour_les_droits_biosociaux_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Ascension des nouveaux opérateurs d'extraction lunaire intensifie les conflits sur les droits biosociaux_
- [ ] 41. Consortiums Bancaires Financiarisés (`consortiums_bancaires_financiarises_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Infrastructures de clearing devenues critiques pour financer les nouvelles chaînes d'approvisionnement lunaires_
- [ ] 42. … et 53 autre(s) fiche(s) avec des changements possibles
  - _détail dans la section « Passe exhaustive » de ce scénario_

**Articles et site**
- [ ] 43. 5 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« Tbilissi, laboratoire invisible de la guerre des algorithmes »; « Les mémoires oubliées de Tbilissi : quand l’Histoire résiste aux algorithmes »; « Mnemos : la mémoire qui résiste aux algorithmes »; « Tbilissi, capitale des mémoires oubliées : quand l’archive défie la géopolitique »; « Qui décide quand l’algorithme parle ? » : Leena Väinälä contre le silence des plateformes_
- [ ] 44. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario reference`
  - _payant, un appel_
- [ ] 45. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 46. Base
  - `python3 generator/validate.py`
- [ ] 47. Lore
  - `python3 generator/audit_lore.py --scenario reference`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Consortium Shackleton d'Extraction Lunaire
  category: entreprise
  role: Opérateur privé dominant de l'extraction des platinoïdes du cratère de Shackleton, contrôlant
    les flux de métaux critiques vers la Terre depuis 2055.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: corridor_arctique_nordique
  source: et_si_shackleton_platinoides_2052
- nom: Ligue des Terres Rares Terrestres
  category: organisation
  role: Cartel défensif des producteurs terrestres de terres rares (Congo, Asie centrale, Groenland) cherchant
    à limiter l'offre lunaire pour préserver leurs rentes.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: zones_grises_globales
  source: et_si_shackleton_platinoides_2052
- nom: Autorité de Transit Cislunaire
  category: infrastructure
  role: Réseau de contrôle du trafic spatial entre la Terre et la Lune, gérant les corridors de lancement
    et de rentrée des cargaisons de platinoïdes.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: corridor_arctique_nordique
  source: et_si_shackleton_platinoides_2052
```

## Liste d'application — injection commune

Mode rupture : `mode_impose: rupture` fait écrire `mode: rupture` dans chaque fiche ; le moteur déplace alors durablement la référence du scénario au lieu d'amortir un choc.

Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). Forces, polarités, durées, date et propagation de cette simulation sont imposées (`impacts_imposes`, `date_imposee`, `via_matrice_impose`) : l'IA de l'injection ne les recalcule pas, elle rédige seulement le récit.

`acteurs_hint` : entités les plus touchées de chaque scénario (lecture IA, passe exhaustive si elle a tourné), 4 au plus par scénario ; chaque slug ne vaut que pour son scénario.

`faits_imposes` : contraintes de l'hypothèse et sort des acteurs du récit (disparaît, change, reste) ; l'injection les donne à l'IA comme faits non négociables.

```yaml
- id: shackleton_platinoides_2052
  description: En 2052, une mission de prospection privée révèle que le cratère de Shackleton (pôle Sud
    lunaire) contient un dépôt d'astéroïde riche en platinoïdes et terres rares lourdes, accessible en
    surface grâce à la glace permanente. L'extraction devient économiquement viable dès 2055 avec les
    robots lunaires existants, déversant des métaux critiques sur le marché mondial.
  portee: globale
  date_approximative: 2052
  intensite: <à choisir>
  persistance: permanente
  scenarios:
  - fortress_world
  - reference
  variables_hint:
  - frontieres_du_systeme
  - energie_ressources_critiques
  - geopolitique_conflits
  - systeme_economique_redistribution
  variables_hint_count: 4
  source: et_si_shackleton_platinoides_2052
  acteurs_hint:
  - cartels_miniers_militarises_subsahariens_fortress_world
  - les_recycleurs_fortress_world
  - consortium_eurasiatique_des_ressources_fermees_fortress_world
  - alpha47_fortress_world
  - cartel_des_terres_rares_d_asie_centrale_reference
  - consortiums_d_extraction_miniere_du_bassin_congolais_reference
  - kalaallit_nunaat_sovereign_fund_reference
  - bloc_ressources_eurasiatique_bre_reference
  acteurs_hint_count: 4
  faits_imposes:
    fortress_world:
    - fait: En 2052, une mission de prospection privée révèle que le cratère de Shackleton (pôle Sud lunaire)
        contient un dépôt d'astéroïde riche en platinoïdes et terres rares lourdes, accessible en surface
        grâce à la glace permanente.
      sort: contrainte
    - fait: L'extraction devient économiquement viable dès 2055 avec les robots lunaires existants.
      sort: contrainte
    - fait: Les métaux critiques extraits arrivent en masse sur le marché mondial.
      sort: contrainte
    - fait: 'Cartels Miniers Militarisés Subsahariens (cartels_miniers_militarises_subsahariens_fortress_world)
        passe de « émergent » à « déclinant » après 2052 : elle existe toujours (elle peut perdre des
        lieux, des biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: cartels_miniers_militarises_subsahariens_fortress_world
      sort: change
    - fait: 'Les Ferrailleurs de Paris (les_recycleurs_fortress_world) passe de « dominant » à « déclinant
        » après 2052 : elle existe toujours (elle peut perdre des lieux, des biens ou du pouvoir), ne
        la décris pas comme disparue.'
      slug: les_recycleurs_fortress_world
      sort: change
    - fait: 'Consortium Eurasiatique des Ressources Fermées (consortium_eurasiatique_des_ressources_fermees_fortress_world)
        passe de « émergent » à « déclinant » après 2052 : elle existe toujours (elle peut perdre des
        lieux, des biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: consortium_eurasiatique_des_ressources_fermees_fortress_world
      sort: change
    - fait: 'Alpha47 - Complexe Minier Ergo-Wian (alpha47_fortress_world) passe de « mature » à « déclinant
        » après 2052 : elle existe toujours (elle peut perdre des lieux, des biens ou du pouvoir), ne
        la décris pas comme disparue.'
      slug: alpha47_fortress_world
      sort: change
    - fait: 'La zone Afrique Subsaharienne — Zones d''Effondrement Étatique (afrique_subsaharienne_zones_effondrees)
        passe de « fragmenté » à « en_declin » : le lieu subsiste.'
      slug: afrique_subsaharienne_zones_effondrees
      sort: zone
    - fait: 'La zone Espace Nordique et Arctique (espace_nordique_arctique) passe de « stable » à « dominant
        » : le lieu subsiste.'
      slug: espace_nordique_arctique
      sort: zone
    - fait: 'La zone Paris (paris_hors) passe de « en_declin » à « fragmenté » : le lieu subsiste.'
      slug: paris_hors
      sort: zone
    - fait: 'La zone Bloc Eurasiatique Occidental (bloc_eurasiatique_occidental) passe de « dominant »
        à « stable » : le lieu subsiste.'
      slug: bloc_eurasiatique_occidental
      sort: zone
    reference:
    - fait: En 2052, une mission de prospection privée révèle que le cratère de Shackleton (pôle Sud lunaire)
        contient un dépôt d'astéroïde riche en platinoïdes et terres rares lourdes, accessible en surface
        grâce à la glace permanente.
      sort: contrainte
    - fait: L'extraction devient économiquement viable dès 2055 avec les robots lunaires existants.
      sort: contrainte
    - fait: Les métaux critiques extraits arrivent en masse sur le marché mondial.
      sort: contrainte
    - fait: 'Cartel des Terres Rares d''Asie Centrale (cartel_des_terres_rares_d_asie_centrale_reference)
        passe de « émergent » à « déclinant » après 2052 : elle existe toujours (elle peut perdre des
        lieux, des biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: cartel_des_terres_rares_d_asie_centrale_reference
      sort: change
    - fait: 'Consortiums d''Extraction Minière du Bassin Congolais (consortiums_d_extraction_miniere_du_bassin_congolais_reference)
        passe de « émergent » à « déclinant » après 2052 : elle existe toujours (elle peut perdre des
        lieux, des biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: consortiums_d_extraction_miniere_du_bassin_congolais_reference
      sort: change
    - fait: 'Kalaallit Nunaat Sovereign Fund (kalaallit_nunaat_sovereign_fund_reference) passe de « ascendant
        » à « déclinant » après 2052 : elle existe toujours (elle peut perdre des lieux, des biens ou
        du pouvoir), ne la décris pas comme disparue.'
      slug: kalaallit_nunaat_sovereign_fund_reference
      sort: change
    - fait: 'Bloc Ressources Eurasiatique (BRE) (bloc_ressources_eurasiatique_bre_reference) passe de
        « émergent » à « déclinant » après 2052 : elle existe toujours (elle peut perdre des lieux, des
        biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: bloc_ressources_eurasiatique_bre_reference
      sort: change
    - fait: 'La zone Nuuk-Capitale (nuuk_capitale_groenland) passe de « emergent » à « en_declin » : le
        lieu subsiste.'
      slug: nuuk_capitale_groenland
      sort: zone
    - fait: 'La zone Corridors Eurasiens Centraux (corridors_eurasiens_zones_grises) passe de « fragmenté
        » à « en_declin » : le lieu subsiste.'
      slug: corridors_eurasiens_zones_grises
      sort: zone
    - fait: 'La zone Bloc Eurasien Central (bloc_eurasien_central) passe de « fragmenté » à « en_declin
        » : le lieu subsiste.'
      slug: bloc_eurasien_central
      sort: zone
  date_imposee: 2052
  mode_impose: rupture
  wild_card_impose: true
  impacts_imposes:
    fortress_world:
    - variable: frontieres_du_systeme
      delta_level: 30
      duree: 5
      polarite: -1
    - variable: energie_ressources_critiques
      delta_level: 32
      duree: 8
      polarite: -1
    - variable: geopolitique_conflits
      delta_level: 35
      duree: 5
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 28
      duree: 8
      polarite: 1
    reference:
    - variable: frontieres_du_systeme
      delta_level: 30
      duree: 5
      polarite: -1
    - variable: energie_ressources_critiques
      delta_level: 32
      duree: 8
      polarite: -1
    - variable: geopolitique_conflits
      delta_level: 28
      duree: 5
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 30
      duree: 8
      polarite: 1
  via_matrice_impose: true
```

