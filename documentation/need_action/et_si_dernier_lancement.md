# Et si ? — Effondrement de la circulation méridienne atlantique

*Simulation du 2026-10-17 10:46 — lecture seule, rien n'a été injecté (simulateur v8.20).*

En 2067, la grande circulation océanique de l'Atlantique (dont le Gulf Stream) s'effondre de façon irréversible. L'Europe du Nord-Ouest se refroidit de plusieurs degrés en une décennie, les moussons africaines et sud-américaines se déplacent, le niveau de la mer monte brusquement sur la côte est américaine. Le monde ne revient pas à l'état d'avant.

**Faits imposés à la lecture IA** :
- La circulation atlantique ne redémarre pas avant 2098 : le changement est permanent.
- Le refroidissement touche surtout l'Europe du Nord-Ouest ; le réchauffement global continue ailleurs.

- **Apparition** : 2067 · **Persistance** : — (mode **rupture** : l'équilibre du scénario est déplacé pour de bon) · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098
- **Carte** : élément déclaré sans effet territorial (`carte: non`), aucune proposition de carte retenue
- Déclaré : **climat_environnement_global** — force 6, aggrave ↑, montée sur 10 ans
- Déclaré : **systemes_productifs_travail** — force 4, aggrave ↑, montée sur 8 ans
- Déclaré : **energie_ressources_critiques** — force 3, aggrave ↑, montée sur 5 ans
- Déclaré : **demographie_mobilite_humaine** — force 4, aggrave ↑, montée sur 15 ans

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## reference

Apparu en 2067 dans le scénario reference, Effondrement de la circulation méridienne atlantique agit d'abord sur climat environnement global, systèmes productifs travail, démographie mobilité humaine et énergie ressources critiques. Son effet le plus fort aggrave climat environnement global, avec un écart maximal de +6,0 points vers 2098. Par propagation, organisation territoires réagit à son tour environ 16 ans après l'apparition (+0,4 points au plus fort). En 2098, il en subsiste +6,0 points sur climat environnement global.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| climat_environnement_global | 65,0 → 70,9 | 68,4 | 74,4 | **+6,0** | direct |
| systemes_productifs_travail | 70,0 → 74,0 | 75,2 | 79,8 | **+4,6** | direct |
| demographie_mobilite_humaine | 55,0 → 59,0 | 64,6 | 68,9 | **+4,3** | direct |
| energie_ressources_critiques | 72,0 → 75,0 | 79,7 | 82,9 | **+3,2** | direct |
| frontieres_du_systeme | 55,0 | 62,3 | 62,8 | **+0,5** | propagé |
| organisation_territoires | 65,0 | 74,9 | 75,3 | **+0,4** | propagé |
| sante_biotechnologies | 55,0 | 50,7 | 51,0 | **+0,3** | propagé |
| technologie_information | 80,0 | 92,8 | 93,1 | **+0,3** | propagé |
| systeme_economique_redistribution | 70,0 | 82,8 | 83,0 | **+0,2** | propagé |
| valeurs_culture_tempo_sociale | 60,0 | 69,1 | 69,3 | **+0,2** | propagé |
| gouvernance_institutions | 40,0 | 53,8 | 53,9 | **+0,1** | propagé |
| geopolitique_conflits | 75,0 | 88,6 | 88,7 | **+0,1** | propagé |

**Repères** :
- climat_environnement_global (direct) : pic +6,0 vers 2098
- systemes_productifs_travail (direct) : pic +4,6 vers 2098
- demographie_mobilite_humaine (direct) : pic +4,3 vers 2098
- energie_ressources_critiques (direct) : pic +3,2 vers 2098

**Tensions** : 42 sans l'hypothèse → 42 avec.
- ⬆ devient une cascade critique : demographie_mobilite_humaine → geopolitique_conflits
_Une tension se déclenche quand un niveau franchit un seuil (60, ou 70 pour une cascade, abaissés selon le risque de bascule de la variable) : un écart de quelques dixièmes peut suffire si le niveau était déjà au bord._

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

L'effondrement irréversible de la circulation méridienne atlantique en 2067 reconfigure durablement les équilibres géopolitiques et économiques du scénario *reference*, sans pour autant provoquer un basculement systémique. L'Europe du Nord-Ouest, frappée par un refroidissement brutal, voit ses systèmes productifs et ses flux migratoires bouleversés, tandis que les Amériques et l'Afrique subissent des perturbations hydrologiques et agricoles majeures. Les acteurs dominants (Corridor Arctique Nordique, Consortium Helios) renforcent leur emprise sur les ressources et les infrastructures critiques, mais les marges (Zones Grises, Sahel) deviennent des zones de friction accrues. Le monde absorbe le choc sans s'effondrer, mais l'équilibre fragile du scénario est durablement déplacé vers une logique de fragmentation et de résilience territoriale. _(ampleur : forte)_

**Trajectoires d'entités**
- Delta du Gange — Zone de Crise Permanente (`delta_du_gange_reference`) : déclinant → **résiduel** — Les déplacements des moussons et la montée des eaux submergent définitivement les infrastructures du delta, rendant la zone ingouvernable et accélérant son abandon.
- Consortiums d'Agriculture Verticale Algorithmique (`consortiums_d_agriculture_verticale_algorithmique_reference`) : émergent → **ascendant** — La perturbation des écosystèmes agricoles traditionnels en Europe et en Afrique accélère l'adoption des fermes verticales comme solution de souveraineté alimentaire.
- Autorités Régionales de Régulation Hydrologique (`autorites_regionales_de_regulation_hydrologique_reference`) : émergent → **dominant** — Les crises hydrologiques en cascade (Afrique, Amérique du Sud) imposent une gouvernance décentralisée de l'eau comme condition de survie, renforçant leur légitimité.
- Fonds Souverain Arctique Scandinave (`fonds_souverain_arctique_scandinave_reference`) : ascendant → **dominant** — Les revenus tirés de l'exploitation des terres rares et des nouvelles routes arctiques font du FSAS un acteur financier majeur, capable de peser sur les équilibres énergétiques.

**Relations**
- alliance nouvelle : Consortium Helios ↔ Fonds Souverain Arctique Scandinave — Helios et le FSAS s'allient pour sécuriser les infrastructures énergétiques orbitales et les corridors arctiques, combinant expertise technologique et contrôle des ressources.
- opposition nouvelle : Armada Logistique Nordique ↔ OptiFlow Global Logistics Network (OGLN) — L'ALN conteste le monopole d'OptiFlow sur les flux logistiques mondiaux, cherchant à imposer ses propres standards pour les routes arctiques.
- opposition nouvelle : Consortium Indo-Pacifique de l'Hydrogène ↔ Bloc Ressources Eurasiatique (BRE) — Le Consortium Indo-Pacifique et le BRE s'affrontent pour le contrôle des gisements d'hydrogène et des infrastructures de liquéfaction, dans un contexte de pénurie énergétique aggravée.
- opposition nouvelle : Gouvernements du Bloc Sahélien Autonome ↔ Union Africaine Résilience (UAR) — Le Bloc Sahélien, confronté à des déplacements de moussons et à des sécheresses prolongées, accuse l'UA de ne pas redistribuer équitablement les ressources hydriques et alimentaires.
- alliance nouvelle : Ergo-Wian Sovereign Holdings ↔ Consortiums Énergétiques Opaques — EWSH et les Consortiums Opaques s'associent pour exploiter les opportunités spéculatives liées aux pénuries énergétiques en Europe, en contournant les régulations publiques.

**Statut des zones**
- Europe Occidentale Reconstruite (`europe_occidentale_reconstruite`) : stable → **fragmenté** — Le refroidissement climatique et les crises agricoles fragmentent les solidarités territoriales, avec des régions comme le Massif Central ou l'Ibérie Atlantique devenant des zones de repli ou de conflit.
- Union Africaine de Résilience Territoriale (`union_africaine_resilience`) : emergent → **fragmenté** — Les déplacements des moussons et les crises hydriques exacerbent les tensions internes, affaiblissant la cohésion de l'UA face aux pressions migratoires et aux milices.

**Nouvelles entités plausibles**
- Alliance des Territoires Froids Européens (europe_occidentale_reconstruite) : Bloc de coopération pour la gestion des crises climatiques et énergétiques en Europe du Nord-Ouest, regroupant des régions sinistrées et des villes en repli. — Les régions touchées par le refroidissement (Massif Central, Pays de Galles) s'organisent pour mutualiser leurs ressources et négocier avec les acteurs dominants (Helios, Corridor Arctique).
- Consortium des Deltas de Crise (zones_grises_globales) : Structure de coordination entre les zones submergées (Gange, Mékong) pour gérer les migrations climatiques et les conflits fonciers, en partenariat avec les Consortiums d'Agriculture Verticale. — Les deltas deviennent des zones de non-droit où émergent des acteurs hybrides (milices, ONG, entreprises) pour organiser la survie des populations déplacées.
- Fonds d'Urgence Climatique Atlantique (europe_occidentale_reconstruite) : Fonds spéculatif créé par Ergo-Wian et des Consortiums Opaques pour investir dans les infrastructures de relocalisation et les technologies de survie en Europe du Nord-Ouest. — Les acteurs financiers exploitent la crise pour capter les dernières ressources publiques et privées des territoires en déclin.

_Corrections automatiques (1) : relation consortium_indo_pacifique_de_l_hydrogene_reference / bloc_ressources_eurasiatique_bre_reference : action absente -> nouvelle_

_Propositions écartées au contrôle (7) : trajectoire : corridor_arctique_nordique_reference déjà dominant (aucun changement) ; trajectoire : armada_logistique_nordique_reference déjà dominant (aucun changement) ; trajectoire : murmansk_transit_arctique_reference déjà disparu (aucun changement) ; trajectoire : entité inconnue 'ecosse_nordique_independante' ; relation milices_concurrentes_des_droits_de_passage_reference / agence_de_regulation_des_detroits_strategiques_ards_reference : opposition déjà présente ; statut de zone : corridor_arctique_nordique déjà dominant ; statut de zone : ameriques_multipolaires déjà fragmenté_

### Passe exhaustive (IA, toutes les fiches — rien n'est écrit)

194 fiche(s) relue(s) en 13 lot(s).
Verdicts : **1 fiche(s) à corriger**, 160 avec des changements possibles seulement, 33 inchangée(s).

_Contre-lecture des obligatoires : 7 vérifié(s), 1 confirmé(s), 6 rétrogradé(s) en possible._

#### Obligatoire — la fiche devient fausse sans ce changement

**Relations**
- opposition nouvelle : Bloc Eurasien Central (BEC) ↔ Bloc Ressources Eurasiatique (BRE) — Le BRE, en tant que régulateur autoritaire, ne peut plus maintenir d'alliance avec un BEC devenu résiduel et incapable de garantir des compromis stables. [lien relation : Le BRE devient un régulateur autoritaire des ressources critiques eurasiatiques, capable d'influer sur les prix mondiaux.] — contredit : Le BEC et le BRE sont alliés dans le scénario de référence.

#### Possible — conséquence plausible, la fiche reste vraie sans elle

_Rétrogradés d'obligatoire à possible par les contrôles : 27 changement de degré, 19 lien territoire alors qu'aucun territoire précis n'est touché, 4 élargit le rôle sans le contredire, 3 contre-lecture aggravation, 3 atténue le rôle sans le contredire, 3 au conditionnel, 2 contre-lecture nuance, 1 contre-lecture invention, 1 extrait introuvable dans la fiche._

**À lire en priorité (20 fiches sur 161)** — choisies et ordonnées par l'IA

- **Agence Mondiale pour la Stabilisation Climatique** (`agence_stabilisation_climatique_reference`) — _Centralisation géo-ingénierie post-effondrement_
  - Agence Mondiale pour la Stabilisation Climatique (`agence_stabilisation_climatique_reference`) : mature → **dominant** — L'ampleur de la crise climatique post-2067 impose une centralisation accrue des interventions géo-ingénieristes, rendant l'AMSC incontournable. [lien variable : climat_environnement_global (+6.0)] _(rétrogradé : changement de degré)_ — contredit : L'AMSC ne peut rester en trajectoire 'mature' alors que l'effondrement de la circulation méridienne atlantique en fait l'acteur central de la gestion des crises climatiques irréversibles.
  - instance Agence Mondiale pour la Stabilisation Climatique (`agence_stabilisation_climatique_reference`) : « L'AMSC opère comme une instance de coordination technocratique internationale dont l'autorité est reconnue mais constamment négociée » — contredit par : L'autorité de l'AMSC n'est plus 'constamment négociée' mais devient un impératif de survie face à la crise climatique irréversible. — La phrase doit être révisée pour refléter l'urgence et la centralisation du rôle de l'AMSC. [lien variable : climat_environnement_global (+6.0)] _(rétrogradé : contre-lecture nuance)_ — La phrase de la fiche reste vraie : l'autorité de l'AMSC peut être 'reconnue mais constamment négociée' même si elle devient un impératif de survie. L'élément perturbateur n'impose pas que cette négociation cesse, seulement qu'elle soit plus urgente.
- **AgriSynth** (`agrisynth_reference`) — _Refonte agricole Europe du Nord-Ouest_
  - AgriSynth (`agrisynth_reference`) : émergent → **ascendant** — Le refroidissement de l'Europe du Nord-Ouest impose une refonte des systèmes agricoles, rendant AgriSynth un acteur clé de cette transition. [lien territoire : europe_occidentale_reconstruite (refroidissement brutal)] _(rétrogradé : changement de degré)_ — contredit : AgriSynth ne peut rester 'émergent' alors que l'Europe du Nord-Ouest, son territoire d'action, subit un refroidissement brutal nécessitant une adaptation agricole massive.
- **Consortium Amazônia Viva** (`consortium_amazonia_viva_reference`) — _Gestion hydrique Amazonie critique_
  - Consortium Amazônia Viva (`consortium_amazonia_viva_reference`) : ascendant → **dominant** — Les perturbations des moussons sud-américaines et les tensions sur les ressources hydriques renforcent le rôle du Consortium comme acteur central de la gouvernance écologique du bassin amazonien. [lien variable : climat_environnement_global (+6.0) et systemes_productifs_travail (+4.6)]
- **Frente Sertão Livre** (`frente_sertao_livre_reference`) — _Conflit hydrique Amérique du Sud dominant_
  - Frente Sertão Livre (`frente_sertao_livre_reference`) : ascendant → **dominant** — Les perturbations hydrologiques et agricoles en Amérique du Sud, exacerbées par le déplacement des moussons, renforcent la dépendance aux modèles agroécologiques résilients portés par la Frente Sertão Livre, ce qui pourrait accélérer son ascension. [lien variable : systemes_productifs_travail (+4.6) et demographie_mobilite_humaine (+4.3), touchés par l'élément perturbateur]
  - opposition nouvelle : Frente Sertão Livre ↔ Consortium Amazônia Viva — Les perturbations hydrologiques en Amazonie pourraient intensifier les conflits entre la Frente Sertão Livre et le Consortium Amazônia Viva pour le contrôle des terres et des ressources en eau. [lien relation : consortium_amazonia_viva_reference est un rival historique, mais les perturbations climatiques pourraient exacerber les tensions pour le contrôle des ressources en Amazonie]
- **Compact des Grands Lacs** (`great_lakes_autonomous_compact_reference`) — _Stratégie Grands Lacs post-montée des eaux_
  - Compact des Grands Lacs (`great_lakes_autonomous_compact_reference`) : mature → **dominant** — La montée du niveau de la mer sur la côte est américaine et les perturbations climatiques pourraient renforcer l'importance stratégique du Compact des Grands Lacs comme réservoir d'eau douce et zone de stabilité. [lien variable : demographie_mobilite_humaine (+4.3) et systemes_productifs_travail (+4.6), touchés par l'élément perturbateur]
- **Valparaíso FCT — Facilitation & Compensation Transfrontalière** (`valparaiso_fct_reference`) — _Hub logistique Valparaíso incontournable_
  - Valparaíso FCT — Facilitation & Compensation Transfrontalière (`valparaiso_fct_reference`) : mature → **dominant** — La reconfiguration des flux économiques et logistiques post-effondrement renforce le rôle de Valparaíso FCT comme hub de compensation interbloc. [lien variable : systemes_productifs_travail (+4.6) et energie_ressources_critiques (+3.2)]
- **Assemblée des Territoires Fédérés (ATF)** (`assemblee_territoires_reference`) — _Coordination décentralisée post-fragmentation_
  - Assemblée des Territoires Fédérés (ATF) (`assemblee_territoires_reference`) : ascendant → **dominant** — La fragmentation territoriale post-2067 renforce la nécessité d'une coordination décentralisée, augmentant l'importance de l'ATF. [lien variable : organisation_territoires (+0.4)] _(douteux : lien variable sous 2 points)_
- **Gouvernements du Bloc Sahélien Autonome** (`gouvernements_du_bloc_sahelien_autonome_reference`) — _Bloc Sahélien face aux moussons déplacées_
  - Gouvernements du Bloc Sahélien Autonome (`gouvernements_du_bloc_sahelien_autonome_reference`) : émergent → **ascendant** — Les perturbations des moussons africaines et les flux migratoires accrus renforcent le rôle du Bloc Sahélien Autonome comme acteur incontournable de la résilience territoriale en Afrique subsaharienne. [lien variable : demographie_mobilite_humaine (+4.3) et systemes_productifs_travail (+4.6), touchés par l'élément perturbateur] _(rétrogradé : changement de degré)_ — contredit : Le rôle du Bloc Sahélien Autonome reste émergent, alors que les perturbations des moussons africaines et les flux migratoires accrus en font un acteur clé pour la stabilité régionale.
- **Commission Hydrique de l'Union Africaine** (`commission_hydrique_de_l_union_africaine_reference`) — _Régulation hydrique Union Africaine critique_
  - Commission Hydrique de l'Union Africaine (`commission_hydrique_de_l_union_africaine_reference`) : émergent → **ascendant** — Les perturbations des moussons africaines et les tensions hydriques accrues rendent son rôle de régulation et de médiation indispensable, renforçant sa trajectoire. [lien variable : systemes_productifs_travail (+4.6) et demographie_mobilite_humaine (+4.3)] _(rétrogradé : changement de degré)_ — contredit : Acteur institutionnel de référence sur les questions d'accès à l'eau en Afrique, elle intervient comme autorité de régulation et de médiation entre États membres confrontés à des tensions hydriques croissantes.
- **Union Africaine de Résilience Territoriale** (`union_africaine_de_resilience_territoriale_reference`) — _Résilience territoriale africaine renforcée_
  - Union Africaine de Résilience Territoriale (`union_africaine_de_resilience_territoriale_reference`) : émergent → **ascendant** — Les perturbations hydrologiques et agricoles en Afrique (déplacement des moussons) renforcent le besoin d'une gouvernance régionale autonome, accélérant la trajectoire de l'UART. [lien variable : demographie_mobilite_humaine (+4.3) et systemes_productifs_travail (+4.6)]
  - alliance nouvelle : Union Africaine de Résilience Territoriale ↔ Autorités Régionales de Régulation Hydrologique — La gestion des ressources hydriques devient critique pour l'Afrique post-effondrement, rendant une alliance avec les autorités hydrologiques émergentes plausible. [lien variable : organisation_territoires (+0.4) et systemes_productifs_travail (+4.6)]
- **Consortium Africain de Biotechnologies Sociales (CABS)** (`consortium_africain_de_biotechnologies_sociales_reference`) — _Biorevenu africain face aux crises agricoles_
  - Consortium Africain de Biotechnologies Sociales (CABS) (`consortium_africain_de_biotechnologies_sociales_reference`) : ascendant → **dominant** — Les perturbations hydrologiques et agricoles en Afrique augmentent la dépendance des populations aux programmes de biorevenu et aux solutions biotechnologiques, renforçant le rôle du CABS comme acteur dominant. [lien variable : systemes_productifs_travail (+4.6) et demographie_mobilite_humaine (+4.3)] _(rétrogradé : changement de degré)_ — contredit : Le CABS opère comme un intermédiaire stratégique entre les grandes institutions financières et régulatrices mondiales et les populations africaines à faibles revenus.
- **Kalaallit Nunaat Sovereign Fund** (`kalaallit_nunaat_sovereign_fund_reference`) — _Fonds souverain arctique dominant post-refroidissement_
  - Kalaallit Nunaat Sovereign Fund (`kalaallit_nunaat_sovereign_fund_reference`) : ascendant → **dominant** — Le refroidissement de l'Europe du Nord-Ouest et la reconfiguration des routes logistiques arctiques renforcent la position géopolitique du KNSF comme acteur clé des ressources critiques et des négociations arctiques. [lien variable : energie_ressources_critiques (+3.2)]
  - opposition nouvelle : Kalaallit Nunaat Sovereign Fund ↔ Fonds Souverain Arctique Scandinave — La compétition pour le contrôle des ressources arctiques et des nouvelles routes logistiques pourrait opposer le KNSF au Fonds Souverain Arctique Scandinave, déjà allié à un acteur dominant. [lien relation : alliance déjà retenue entre Consortium Helios et Fonds Souverain Arctique Scandinave]
- **Bloc Ressources Eurasiatique (BRE)** (`bloc_ressources_eurasiatique_bre_reference`) — _Ressources eurasiatiques critiques post-effondrement_
  - Bloc Ressources Eurasiatique (BRE) (`bloc_ressources_eurasiatique_bre_reference`) : émergent → **dominant** — L'effondrement de la circulation atlantique renforce la dépendance aux ressources critiques eurasiatiques, augmentant l'influence du BRE sans rendre sa trajectoire actuelle fausse. [lien variable : energie_ressources_critiques (+3.2) est directement touché.]
- **Pacte des Souverains** (`alliance_blocs_souverains_reference`) — _Pacte des Souverains renforcé par fragmentation_
  - Pacte des Souverains (`alliance_blocs_souverains_reference`) : ascendant → **dominant** — La fragmentation territoriale et la résilience accrue des blocs souverains post-2067 renforcent leur poids géopolitique. [lien variable : frontieres_du_systeme (+0.5) et organisation_territoires (+0.4)] _(douteux : lien variable sous 2 points)_
  - alliance nouvelle : Pacte des Souverains ↔ Fonds Souverain Arctique Scandinave — La collaboration avec les acteurs arctiques devient stratégique pour sécuriser les ressources et les routes logistiques. [lien relation : Alliée au Fonds Souverain Arctique Scandinave, déjà retenu comme dominant.]
- **The Tidewater Canon** (`the_tidewater_canon_reference`) — _Doctrine Tidewater Canon dominante post-crise_
  - The Tidewater Canon (`the_tidewater_canon_reference`) : mature → **dominant** — La reconfiguration des systèmes productifs et des chaînes logistiques post-effondrement renforce la pertinence de la doctrine souverainiste du Tidewater Canon, déjà en phase ascendante. [lien variable : systemes_productifs_travail (+4.6)]
  - alliance nouvelle : The Tidewater Canon ↔ Fonds Souverain Arctique Scandinave — Le Tidewater Canon, philosophie des blocs souverains, pourrait s'aligner plus étroitement avec les acteurs dominants post-effondrement comme le Fonds Souverain Arctique Scandinave. [lien relation : Alliance déjà retenue entre Consortium Helios et Fonds Souverain Arctique Scandinave]
- **The Lattice of Chartered Cities** (`the_lattice_reference`) — _Villes-refuge pour migrations climatiques massives_
  - The Lattice of Chartered Cities (`the_lattice_reference`) : mature → **ascendant** — L'effondrement de la circulation méridienne atlantique provoque des migrations climatiques massives depuis l'Europe du Nord-Ouest et les zones agricoles perturbées, renforçant le rôle des juridictions autonomes comme The Lattice pour absorber ces flux. [lien variable : demographie_mobilite_humaine (+4.3)]
  - alliance nouvelle : The Lattice of Chartered Cities ↔ Réseau des Villes-Refuge pour Travailleurs Désaugmentés — La crise migratoire post-2067 rend probable une coopération accrue avec les réseaux de villes-refuge pour gérer les travailleurs déplacés. [lien variable : demographie_mobilite_humaine (+4.3)]
- **Réseau des Métropoles Côtières Adaptées** (`reseau_des_metropoles_cotieres_adaptees_reference`) — _Gouvernance métropoles côtières post-montée des eaux_
  - Réseau des Métropoles Côtières Adaptées (`reseau_des_metropoles_cotieres_adaptees_reference`) : émergent → **ascendant** — La montée brutale du niveau de la mer et les déplacements de populations côtières rendent indispensable une gouvernance renforcée des métropoles côtières. Un statut émergent devient faux. [lien variable : demographie_mobilite_humaine (+4.3), organisation_territoires (+0.4)] _(rétrogradé : changement de degré)_ — contredit : Le réseau reste émergent malgré la montée des eaux sur la côte est américaine et les perturbations côtières.
  - instance Réseau des Métropoles Côtières Adaptées (`reseau_des_metropoles_cotieres_adaptees_reference`) : « Acteur collectif structurant la gouvernance territoriale des zones côtières en 2098, pesant sur les arbitrages entre adaptation, relocalisation et maintien des populations littorales » — contredit par : Le rôle reste inchangé malgré la montée des eaux et les perturbations côtières. — La crise côtière rend le réseau central, pas seulement influent. La phrase doit refléter une nécessité accrue de coordination. [lien variable : demographie_mobilite_humaine (+4.3)] _(rétrogradé : élargit le rôle sans le contredire)_
- **Fédération des Communs Territoriaux** (`federation_communs_territoriaux_reference`) — _Fédération des Communs Territoriaux dominante_
  - Fédération des Communs Territoriaux (`federation_communs_territoriaux_reference`) : ascendant → **dominant** — La fragmentation territoriale et la crise climatique renforcent la pertinence des modèles décentralisés comme la FCT. [lien variable : climat_environnement_global (+6.0), systemes_productifs_travail (+4.6)]
- **Internationale des Travailleurs Augmentés** (`internationale_travailleurs_augmentes_reference`) — _Travailleurs augmentés précarisés post-bouleversements_
  - Internationale des Travailleurs Augmentés (`internationale_travailleurs_augmentes_reference`) : ascendant → **dominant** — Les bouleversements des systèmes productifs en Europe du Nord-Ouest et ailleurs pourraient augmenter la précarité des travailleurs augmentés, renforçant le rôle de l'ITA comme syndicat transnational de défense. [lien variable : systemes_productifs_travail (+4.6)]
- **Coopératives Agro-Écologiques de Reconstruction Territoriale** (`cooperatives_agro_ecologiques_de_reconstruction_territoriale_reference`) — _Coopératives agro-écologiques sahéliennes critiques_
  - Coopératives Agro-Écologiques de Reconstruction Territoriale (`cooperatives_agro_ecologiques_de_reconstruction_territoriale_reference`) : émergent → **ascendant** — La perturbation des systèmes productifs et des flux migratoires renforce le rôle des coopératives comme acteurs de résilience locale, surtout dans les zones touchées par les déplacements de populations. [lien variable : demographie_mobilite_humaine (+4.3) et systemes_productifs_travail (+4.6)]
  - alliance nouvelle : Coopératives Agro-Écologiques de Reconstruction Territoriale ↔ Gouvernements du Bloc Sahélien Autonome — Les coopératives pourraient s'allier aux gouvernements sahéliens pour répondre aux perturbations hydrologiques en Afrique. [lien relation : gouvernements_du_bloc_sahelien_autonome_reference (opposé à l'Union Africaine Résilience)]

**Autres fiches avec des changements possibles (141)**
- Réseau Terrafond : trajectoire mature → déclinant ; texte « Le Réseau Terrafond constitue l'une des architectures… »
- Union Occidentale de Coordination (UOC) : trajectoire déclinant → résiduel ; opposition nouvelle avec Fonds Souverain Arctique Scandinave ; texte « Elle ne prétend plus à l'intégration politique profonde de… »
- Syndicats de travail rural hybride : trajectoire émergent → déclinant
- Banque des Communs : trajectoire émergent → ascendant ; alliance nouvelle avec Consortiums d'Agriculture Verticale Algorithmique
- Bloc Eurasien Central (BEC) : trajectoire déclinant → résiduel
- Bureau des Zones Non Prioritaires (BZNP) : trajectoire déclinant → résiduel
- Collectifs de Journalisme Embarqué : trajectoire émergent → ascendant ; texte « Ancrés dans des zones à fort enjeu territorial — deltas… »
- Conseil de Régulation des Ressources Critiques : trajectoire déclinant → résiduel
- Alliance des Glaces Libres (AGL) : trajectoire ascendant → dominant
- Front Souverainiste des Ressources d'Amérique du Sud : trajectoire émergent → ascendant
- Accords Hydriques de Kinshasa : trajectoire mature → déclinant ; opposition nouvelle avec Autorités Régionales de Régulation Hydrologique
- Les Gardiens des Rives : trajectoire ascendant → dominant
- Mouvement des Racines Vivantes : trajectoire ascendant → dominant ; alliance nouvelle avec Coopératives Agro-Écologiques du Bassin Méditerranéen
- Programme ONU-Eau 2080 : trajectoire émergent → ascendant ; texte « Sert de référentiel normatif et d'instance de coordination… »
- Régulateurs de l'Union Continentale Africaine : trajectoire émergent → ascendant ; alliance nouvelle avec Gouvernements du Bloc Sahélien Autonome
- Réseau des Coopératives Agro-Sahéliennes : trajectoire émergent → ascendant
- Union Africaine Résilience (UAR) : trajectoire déclinant → résiduel
- Autorités Régionales de Régulation Hydrologique : alliance nouvelle avec Fonds Souverain Arctique Scandinave
- Consortium des Grandes Plateformes Logistiques Globales : opposition nouvelle avec Armada Logistique Nordique ; texte « il est l'épine dorsale matérielle sans laquelle l'équilibre… »
- Ergo-Wian Sovereign Holdings : alliance nouvelle avec Fonds Souverain Arctique Scandinave
- Alliance des Blocs Souverains (ABS) : opposition nouvelle avec Fonds Souverain Arctique Scandinave
- Detroit Compact Grands Lacs : texte « le Compact coordonne la gestion des ressources hydriques et… »
- Administrations Hybrides des Cités-Relais Périphériques : trajectoire émergent → ascendant
- Agence Internationale des Énergies Renouvelables (IRENA-2) : trajectoire émergent → ascendant
- Agences de Sécurité Régionales de Normalisation des Zones Grises : trajectoire émergent → ascendant
- Algorithmic Labor Exchange : trajectoire émergent → ascendant
- Amara Diallo-Nkosi : trajectoire mature → dominant
- Banque Mondiale des Transitions Climatiques : trajectoire émergent → ascendant ; alliance nouvelle avec Autorités Régionales de Régulation Hydrologique
- Bloc des Souverainistes Climatiques : trajectoire émergent → ascendant ; opposition nouvelle avec Fonds Souverain Arctique Scandinave
- Direction des Zones Non Prioritaires (DZNP) : trajectoire mature → ascendant
- Cartel des Terres Rares d'Asie Centrale : trajectoire émergent → ascendant
- Collectif Nuit Jaune : trajectoire émergent → ascendant ; opposition nouvelle avec Autorités Régionales de Régulation Hydrologique
- Collectifs Académiques Indépendants : trajectoire émergent → ascendant
- Collectifs de Biopiraterie Inversée : trajectoire émergent → ascendant
- Collectifs de Journalistes Indépendants Régionaux : trajectoire émergent → ascendant
- Communs Numériques Agroécologiques : trajectoire émergent → ascendant
- Conseil de Genève pour les Droits Biosociaux : trajectoire émergent → ascendant
- Conseil des États Nordiques Intégrés : trajectoire ascendant → dominant ; alliance nouvelle avec Consortium Helios
- Consortium des Fournisseurs d'Énergie Renouvelable Distribuée : trajectoire émergent → ascendant
- Consortium Énergétique Baltique : trajectoire émergent → déclinant ; alliance nouvelle avec Consortium Helios
- Consortium Énergétique des Mers du Nord : trajectoire émergent → déclinant ; alliance nouvelle avec Consortium Helios
- Consortium Indo-Pacifique de l'Hydrogène : trajectoire émergent → ascendant
- Consortium Logistique Asiatique de Contournement ALN : trajectoire émergent → ascendant
- Consortiums Énergétiques Opaques : trajectoire émergent → ascendant ; alliance nouvelle avec Fonds Souverain Arctique Scandinave
- Consortiums Privés d'Extraction de Ressources Critiques : trajectoire émergent → ascendant ; alliance nouvelle avec Fonds Souverain Arctique Scandinave
- Consortiums Privés de Gestion des Données Critiques : trajectoire émergent → ascendant
- Coopératives Agro-Écologiques du Bassin Méditerranéen : trajectoire émergent → ascendant
- Coopératives Énergétiques Décentralisées : trajectoire émergent → ascendant ; opposition nouvelle avec Armada Logistique Nordique
- Corporations d'Extraction Énergétique Non Signataires : trajectoire émergent → ascendant
- Courant Nationaliste Instrumentalisateur du Discours des Racines : trajectoire émergent → ascendant
- Delta du Mékong — Zone de Friction Nourricière : trajectoire déclinant → résiduel
- Factions d'Extraction Minière Indépendantes : trajectoire émergent → ascendant
- Factions Eurasiatiques contre la Tarification Hydrique : trajectoire émergent → ascendant
- Fonds d'Investissement Foncier Climatique : trajectoire émergent → ascendant
- Fonds Monétaire Climatique (FMC) : trajectoire émergent → ascendant
- Fonds Souverains de la Ceinture Financière Pacifique : trajectoire émergent → ascendant
- Forum Léman — Coordination pour le Recul des Eaux : trajectoire mature → déclinant ; texte « Organisation de gestion environnementale et patrimoniale… »
- Helsinki Communs Numériques : trajectoire mature → déclinant
- Institut Polytechnique de Ouagadougou : trajectoire émergent → ascendant
- Kaspar Lind : trajectoire marginal → ascendant
- Réseau Étincelle : trajectoire marginal → ascendant
- Lamplight Collective : trajectoire ascendant → dominant
- Leena Väinälä : trajectoire ascendant → dominant
- Réseau des Sentinelles des Eaux Profondes : trajectoire ascendant → dominant
- Ligue des Métropoles du Sud pour les Infrastructures Libres : trajectoire émergent → ascendant
- Ligue des Municipalités Périphériques Sous-Connectées : trajectoire émergent → ascendant
- Lobbies Agro-Industriels à Haute Consommation d'Eau : trajectoire émergent → ascendant
- Lobbies Industriels des États Non-Signataires : trajectoire émergent → ascendant
- Milices Concurrentes des Droits de Passage : trajectoire émergent → ascendant
- Mouvement pour la Libre Circulation des Personnes et des Données : trajectoire émergent → ascendant
- Nairobi CRRC — Centre Régional de Résilience et de Coordination : trajectoire mature → ascendant
- NeuroHarmonics Global Augmentation Network (NH-GAN) : trajectoire dominant → mature
- Observatoire Climatique des Territoires (OCT) : trajectoire émergent → ascendant
- ONG de Traçabilité des Ressources Critiques : trajectoire émergent → ascendant
- ONG Environnementales de Terrain : trajectoire émergent → ascendant ; texte « Dans le scénario de référence, elles constituent un… »
- Opérateurs de Zones Économiques Spéciales Périurbaines : trajectoire émergent → ascendant
- Opérateurs Logistiques Privés des Zones Grises Eurasiennes : trajectoire émergent → ascendant
- Opérateurs Privés d'Énergie Distribuée Hors-FCT : trajectoire émergent → ascendant ; texte « Leur expansion — notamment depuis la généralisation du… »
- OptiFlow Global Logistics Network (OGLN) : trajectoire dominant → mature
- Ouagadougou Polytechnique : trajectoire ascendant → dominant
- Plateformes d'Optimisation Territoriale par IA : trajectoire émergent → ascendant
- Prisme Global : trajectoire ascendant → dominant
- Réseaux de Capteurs Citoyens : trajectoire émergent → ascendant
- Sibérie Fédérale : trajectoire marginal → ascendant ; opposition nouvelle avec Fonds Souverain Arctique Scandinave
- Syndicats de travailleurs de la transition énergétique : trajectoire émergent → ascendant
- Universités et Think Tanks en Zones de Liberté Académique : trajectoire émergent → ascendant ; texte « elles produisent des contre-expertises sur les gouvernances… »
- Consortiums Médiatiques Corporatifs : alliance nouvelle avec Consortium Helios ; texte « ils minimisent les signaux de rupture, valorisent les… »
- gelecek_meclisi_reference : alliance nouvelle avec Autorités Régionales de Régulation Hydrologique
- Hyphan Raghavan de Ergo-Wian Sovereign Holdings : alliance nouvelle avec Fonds Souverain Arctique Scandinave
- Ilse Varga-Holm de Ergo-Wian Sovereign Holdings : alliance nouvelle avec Fonds Souverain Arctique Scandinave
- Meridian Assembly : alliance nouvelle avec Confédération des Archipels Flottants du Pacifique Sud (CAFPS)
- Nexus BioSyn : alliance nouvelle avec Consortiums d'Agriculture Verticale Algorithmique
- Consortiums Énergétiques des Mégapoles : texte « ils exercent une pression pour absorber les corridors… »
- Autorité de Régulation des Passages Stratégiques (ARPS) : texte « Elle incarne une gouvernance hybride, mêlant souveraineté… »
- Consortium de Maintenance Orbitale SEOM-7 : texte « Il est l'opérateur technique de dernier recours sur lequel… »
- Consortiums Bancaires Financiarisés : texte « ils incarnent une dépendance structurelle aux… »
- Consortiums d'Extraction Minière du Bassin Congolais : texte « les ressources critiques nécessaires à la décarbonation… »
- Maëlys Okonkwo : texte « Son travail se concentre sur l'exposition des liens entre… »
- Nadia Ferreira-Sato de Raised Hands : texte « elle crée des structures alternatives de survie et de… »
- NexCore Global Infrastructure Group : texte « elle opère les réseaux de communication intercontinentaux,… »
- Confédération des Archipels Flottants du Pacifique Sud (CAFPS) : texte « Confédération de communautés installées sur des archipels… »
- Alliance pour la Souveraineté Maritime des Peuples Insulaires (ASMPI) : texte « L'ASMPI fédère les États-archipels et communautés… »
- Plateformes Centralisées de Narration Officielle : texte « Elles constituent le cadre dominant contre lequel s'inscrit… »
- Plateformes Informationnelles Dominantes et leurs IA de Modération : texte « Dans le scénario reference, elles forment le substrat… »
- Voix du Dehors : texte « Dans un monde où l'infrastructure numérique est hautement… »
- Programme Pilote de Bio-Revenu Universel de Nairobi : texte « Le programme, s'il survit à ses contestations juridiques,… »
- Amazonie Consortium Viva : trajectoire dominant → mature
- Bloc des États du Sud Global contre la Cession de Données : trajectoire émergent → ascendant
- Bureaux de Régulation Informationnelle : trajectoire émergent → ascendant
- Coalition des Gouvernements Contre les Chartes de Déstabilisation : trajectoire émergent → ascendant
- Coalition pour la Souveraineté Numérique Nationale : trajectoire émergent → ascendant
- États à Tendance Centraliste Numérique : trajectoire émergent → ascendant
- Fédération des Cliniques Autonomes : trajectoire émergent → ascendant
- Gouvernements à Régime de Productivité Mandatée : trajectoire émergent → ascendant
- Guadalajara Nexus : trajectoire ascendant → dominant
- Atlas des Marges : trajectoire ascendant → dominant
- Réseau des Villes-Refuge pour Travailleurs Désaugmentés : trajectoire émergent → ascendant
- Réseaux de gouvernance multilatérale survivants : trajectoire émergent → déclinant
- Réseaux de lanceurs d'alerte institutionnels dissidents : trajectoire émergent → ascendant
- Prefeitura Metropolitana de São Paulo — Administração de Continuidade (PMSP-AC) : trajectoire déclinant → résiduel ; texte « La PMSP-AC continue d'administrer une agglomération de 32… »
- Services de contre-information des blocs géopolitiques concurrents : trajectoire émergent → ascendant
- Kharg Data Nexus : trajectoire mature → dominant
- Aurelio Stahl : texte « En tant que conférencier et essayiste itinérant entre les… »
- Confédération des Mégapoles Autonomes : texte « Incarne la fragmentation géopolitique en blocs… »
- Système Kontinuum : texte « Le Système Kontinuum est une infrastructure algorithmique… »
- Raj Mehta : texte « Couvre les tensions géopolitiques et économiques dans un… »
- Sistema Paulista de Alocação Algorítmica de Recursos (SPAAR) : texte « orchestre en temps réel l'allocation de l'eau, de… »
- Gouvernements Fédéraux Résiduels Souverainistes : trajectoire émergent → déclinant
- Réseau des Administrations Locales Rurales Participatives : trajectoire émergent → ascendant
- Réseaux de financement gris issus d'anciens blocs militaires : trajectoire émergent → ascendant
- Réseaux de médecine traditionnelle augmentée : trajectoire émergent → ascendant
- Oracle des Seuils : texte « l'Oracle des Seuils est devenu l'instrument de référence… »
- Autorité de Passage Arctique : trajectoire mature → dominant
- Bruxelles Nouveau : trajectoire déclinant → résiduel ; opposition nouvelle avec Fonds Souverain Arctique Scandinave
- Collectifs de Pêche Inuit et Sami : trajectoire ascendant → dominant
- Passage Arctique du Nord — Zone de Transit Disputée : trajectoire dominant → mature ; texte « une voie maritime dégagée par la fonte quasi-totale de la… »
- Murmansk Transit Arctique : trajectoire disparu → historique
- Tribunal Algorithmique de Bruxelles : trajectoire ascendant → déclinant ; texte « Le Tribunal Algorithmique de Bruxelles est la juridiction… »
- Delta du Gange — Zone de Crise Permanente : texte « Territoire en crise permanente, submergé par la montée des… »
- Lyon Métropole — Autorité de Coordination Territoriale : texte « Lyon Métropole est une organisation administrative… »
- L'Écho Glacé de Murmansk : texte « Le *Polaris-7*, fleuron de la flotte de Murmansk Transit… »

_Réponses rejetées car mal formées (47) : trajectoire : armada_logistique_nordique_reference déjà dominant (aucun changement) ; relation administrations_hybrides_des_cites_relais_peripheriques_reference / autorites_regionales_de_regulation_hydrologique_reference : alliance déjà présente ; relation agence_de_regulation_des_detroits_strategiques_ards_reference / arctic_passage_authority_reference : alliance déjà présente ; relation agrisynth_reference / consortiums_d_agriculture_verticale_algorithmique_reference : alliance déjà présente ; relation arctic_passage_authority_reference / fonds_souverain_arctique_scandinave_reference : alliance déjà présente ; trajectoire : blocs_signataires_du_pacte_energetique_multilateral_reference émergent → mature présenté comme un renforcement (contresens sur l'axe) ; relation conseil_des_etats_nordiques_integres_reference / fonds_souverain_arctique_scandinave_reference : alliance déjà présente ; relation collectifs_academiques_independants_reference / autorites_regionales_de_regulation_hydrologique_reference : alliance déjà présente …_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Statuts de zone**
- [ ] 1. `europe_occidentale_reconstruite` (Europe Occidentale Reconstruite) : stable → fragmenté
  - à la main : geographie/reference.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario reference --execute)
  - _Le refroidissement climatique et les crises agricoles fragmentent les solidarités territoriales, avec des régions comme le Massif Central ou l'Ibérie Atlantique devenant des zones de repli ou de conflit._
- [ ] 2. `union_africaine_resilience` (Union Africaine de Résilience Territoriale) : emergent → fragmenté
  - à la main : geographie/reference.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario reference --execute)
  - _Les déplacements des moussons et les crises hydriques exacerbent les tensions internes, affaiblissant la cohésion de l'UA face aux pressions migratoires et aux milices._

**Élément**
- [ ] 3. Injecter l'événement `effondrement_circulation_atlantique_2067` en mode rupture (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios ; mode_impose: rupture écrit `mode: rupture` dans chaque fiche_
- [ ] 4. climat_environnement_global : référence 65,0 → 70,9
  - aucune action : déplacée par le moteur dès l'injection
- [ ] 5. systemes_productifs_travail : référence 70,0 → 74,0
  - aucune action : déplacée par le moteur dès l'injection
- [ ] 6. demographie_mobilite_humaine : référence 55,0 → 59,0
  - aucune action : déplacée par le moteur dès l'injection
- [ ] 7. energie_ressources_critiques : référence 72,0 → 75,0
  - aucune action : déplacée par le moteur dès l'injection
- [ ] 8. Vérifier que la fiche porte `mode: rupture` et les forces simulées (climat_environnement_global +6, systemes_productifs_travail +4, energie_ressources_critiques +3, demographie_mobilite_humaine +4)
  - event_instances/effondrement_circulation_atlantique_2067_reference.md ; python3 generator/trace_injection.py --slug effondrement_circulation_atlantique_2067 --type evenement --scenario reference
  - _le Tracer doit finir chaque ligne « Déclaré » par « rupture »_
- [ ] 9. Nouvelle référence : vérifier la lisibilité du moteur
  - `python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05`
  - _S19_

**Nouvelles entités**
- [ ] 10. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie à choisir
  - `python3 generator/create_entities_and_instances.py --mode custom`
  - _la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 11. Delta du Gange — Zone de Crise Permanente (`delta_du_gange_reference`) : déclinant → résiduel
  - à la main : instances/delta_du_gange_reference.md, champ `trajectoire`
  - _Les déplacements des moussons et la montée des eaux submergent définitivement les infrastructures du delta, rendant la zone ingouvernable et accélérant son abandon._
- [ ] 12. Consortiums d'Agriculture Verticale Algorithmique (`consortiums_d_agriculture_verticale_algorithmique_reference`) : émergent → ascendant
  - à la main : instances/consortiums_d_agriculture_verticale_algorithmique_reference.md, champ `trajectoire`
  - _La perturbation des écosystèmes agricoles traditionnels en Europe et en Afrique accélère l'adoption des fermes verticales comme solution de souveraineté alimentaire._
- [ ] 13. ⚠ Autorités Régionales de Régulation Hydrologique (`autorites_regionales_de_regulation_hydrologique_reference`) : émergent → dominant
  - à la main : instances/autorites_regionales_de_regulation_hydrologique_reference.md, champ `trajectoire`
  - _saut d'un cran (sans passer par ascendant) : garder, ou ramener à ascendant ; Les crises hydrologiques en cascade (Afrique, Amérique du Sud) imposent une gouvernance décentralisée de l'eau comme condition de survie, renforçant leur légitimité._
- [ ] 14. Fonds Souverain Arctique Scandinave (`fonds_souverain_arctique_scandinave_reference`) : ascendant → dominant
  - à la main : instances/fonds_souverain_arctique_scandinave_reference.md, champ `trajectoire`
  - _Les revenus tirés de l'exploitation des terres rares et des nouvelles routes arctiques font du FSAS un acteur financier majeur, capable de peser sur les équilibres énergétiques._

**Relations**
- [ ] 15. alliance nouvelle : Consortium Helios ↔ Fonds Souverain Arctique Scandinave
  - à la main : ajouter `fonds_souverain_arctique_scandinave_reference` dans `alliances` de instances/consortium_helios_reference.md
  - _Helios et le FSAS s'allient pour sécuriser les infrastructures énergétiques orbitales et les corridors arctiques, combinant expertise technologique et contrôle des ressources._
- [ ] 16. opposition nouvelle : Armada Logistique Nordique ↔ OptiFlow Global Logistics Network (OGLN)
  - à la main : ajouter `optiflow_logistics_reference` dans `oppositions` de instances/armada_logistique_nordique_reference.md
  - _L'ALN conteste le monopole d'OptiFlow sur les flux logistiques mondiaux, cherchant à imposer ses propres standards pour les routes arctiques._
- [ ] 17. opposition nouvelle : Consortium Indo-Pacifique de l'Hydrogène ↔ Bloc Ressources Eurasiatique (BRE)
  - à la main : ajouter `bloc_ressources_eurasiatique_bre_reference` dans `oppositions` de instances/consortium_indo_pacifique_de_l_hydrogene_reference.md
  - _Le Consortium Indo-Pacifique et le BRE s'affrontent pour le contrôle des gisements d'hydrogène et des infrastructures de liquéfaction, dans un contexte de pénurie énergétique aggravée._
- [ ] 18. opposition nouvelle : Gouvernements du Bloc Sahélien Autonome ↔ Union Africaine Résilience (UAR)
  - à la main : ajouter `union_africaine_resilience_reference` dans `oppositions` de instances/gouvernements_du_bloc_sahelien_autonome_reference.md
  - _Le Bloc Sahélien, confronté à des déplacements de moussons et à des sécheresses prolongées, accuse l'UA de ne pas redistribuer équitablement les ressources hydriques et alimentaires._
- [ ] 19. alliance nouvelle : Ergo-Wian Sovereign Holdings ↔ Consortiums Énergétiques Opaques
  - à la main : ajouter `consortiums_energetiques_opaques_reference` dans `alliances` de instances/ergo_wian_sovereign_holdings_reference.md
  - _EWSH et les Consortiums Opaques s'associent pour exploiter les opportunités spéculatives liées aux pénuries énergétiques en Europe, en contournant les régulations publiques._
- [ ] 20. opposition nouvelle : Bloc Eurasien Central (BEC) ↔ Bloc Ressources Eurasiatique (BRE) [passe exhaustive]
  - à la main : ajouter `bloc_ressources_eurasiatique_bre_reference` dans `oppositions` de instances/bloc_eurasien_central_reference.md
  - _Le BRE, en tant que régulateur autoritaire, ne peut plus maintenir d'alliance avec un BEC devenu résiduel et incapable de garantir des compromis stables. [lien relation : Le BRE devient un régulateur autoritaire des ressources critiques eurasiatiques, capable d'influer sur les prix mondiaux.] — contredit : Le BEC et le BRE sont alliés dans le scénario de référence._
- [ ] 21. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario reference --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 22. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section reference
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 23. Termes cherchés : Atlantique, Gulf, Nord-Ouest, Stream
  - _mot entier, sans casse ni accents ; le registre seulement après 2067 (chronologie) ; instances et événements relus par la passe exhaustive : seuls les zones et le registre sont listés_
- [ ] 24. Zone `iberie_atlantique_fragmentee` cite « Atlantique »
  - _Ibérie Atlantique Fragmentée…_
- [ ] 25. Zone `pays_de_galles_atlantique` cite « Atlantique »
  - _Pays de Galles Atlantique…_

**Possibles (facultatif)**
- [ ] 26. Agence Mondiale pour la Stabilisation Climatique (`agence_stabilisation_climatique_reference`) : trajectoire mature → dominant ; texte « L'AMSC opère comme une instance de coordination… » [passe exhaustive]
  - _Centralisation géo-ingénierie post-effondrement_
- [ ] 27. AgriSynth (`agrisynth_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Refonte agricole Europe du Nord-Ouest_
- [ ] 28. Consortium Amazônia Viva (`consortium_amazonia_viva_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Gestion hydrique Amazonie critique_
- [ ] 29. Frente Sertão Livre (`frente_sertao_livre_reference`) : trajectoire ascendant → dominant ; opposition nouvelle avec Consortium Amazônia Viva [passe exhaustive]
  - _Conflit hydrique Amérique du Sud dominant_
- [ ] 30. Compact des Grands Lacs (`great_lakes_autonomous_compact_reference`) : trajectoire mature → dominant [passe exhaustive]
  - _Stratégie Grands Lacs post-montée des eaux_
- [ ] 31. Valparaíso FCT — Facilitation & Compensation Transfrontalière (`valparaiso_fct_reference`) : trajectoire mature → dominant [passe exhaustive]
  - _Hub logistique Valparaíso incontournable_
- [ ] 32. Assemblée des Territoires Fédérés (ATF) (`assemblee_territoires_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Coordination décentralisée post-fragmentation_
- [ ] 33. Gouvernements du Bloc Sahélien Autonome (`gouvernements_du_bloc_sahelien_autonome_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Bloc Sahélien face aux moussons déplacées_
- [ ] 34. Commission Hydrique de l'Union Africaine (`commission_hydrique_de_l_union_africaine_reference`) : trajectoire émergent → ascendant [passe exhaustive]
  - _Régulation hydrique Union Africaine critique_
- [ ] 35. Union Africaine de Résilience Territoriale (`union_africaine_de_resilience_territoriale_reference`) : trajectoire émergent → ascendant ; alliance nouvelle avec Autorités Régionales de Régulation Hydrologique [passe exhaustive]
  - _Résilience territoriale africaine renforcée_
- [ ] 36. Consortium Africain de Biotechnologies Sociales (CABS) (`consortium_africain_de_biotechnologies_sociales_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Biorevenu africain face aux crises agricoles_
- [ ] 37. Kalaallit Nunaat Sovereign Fund (`kalaallit_nunaat_sovereign_fund_reference`) : trajectoire ascendant → dominant ; opposition nouvelle avec Fonds Souverain Arctique Scandinave [passe exhaustive]
  - _Fonds souverain arctique dominant post-refroidissement_
- [ ] 38. Bloc Ressources Eurasiatique (BRE) (`bloc_ressources_eurasiatique_bre_reference`) : trajectoire émergent → dominant [passe exhaustive]
  - _Ressources eurasiatiques critiques post-effondrement_
- [ ] 39. Pacte des Souverains (`alliance_blocs_souverains_reference`) : trajectoire ascendant → dominant ; alliance nouvelle avec Fonds Souverain Arctique Scandinave [passe exhaustive]
  - _Pacte des Souverains renforcé par fragmentation_
- [ ] 40. The Tidewater Canon (`the_tidewater_canon_reference`) : trajectoire mature → dominant ; alliance nouvelle avec Fonds Souverain Arctique Scandinave [passe exhaustive]
  - _Doctrine Tidewater Canon dominante post-crise_
- [ ] 41. The Lattice of Chartered Cities (`the_lattice_reference`) : trajectoire mature → ascendant ; alliance nouvelle avec Réseau des Villes-Refuge pour Travailleurs Désaugmentés [passe exhaustive]
  - _Villes-refuge pour migrations climatiques massives_
- [ ] 42. Réseau des Métropoles Côtières Adaptées (`reseau_des_metropoles_cotieres_adaptees_reference`) : trajectoire émergent → ascendant ; texte « Acteur collectif structurant la gouvernance territoriale… » [passe exhaustive]
  - _Gouvernance métropoles côtières post-montée des eaux_
- [ ] 43. Fédération des Communs Territoriaux (`federation_communs_territoriaux_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Fédération des Communs Territoriaux dominante_
- [ ] 44. Internationale des Travailleurs Augmentés (`internationale_travailleurs_augmentes_reference`) : trajectoire ascendant → dominant [passe exhaustive]
  - _Travailleurs augmentés précarisés post-bouleversements_
- [ ] 45. Coopératives Agro-Écologiques de Reconstruction Territoriale (`cooperatives_agro_ecologiques_de_reconstruction_territoriale_reference`) : trajectoire émergent → ascendant ; alliance nouvelle avec Gouvernements du Bloc Sahélien Autonome [passe exhaustive]
  - _Coopératives agro-écologiques sahéliennes critiques_
- [ ] 46. … et 141 autre(s) fiche(s) avec des changements possibles
  - _détail dans la section « Passe exhaustive » de ce scénario_

**Articles et site**
- [ ] 47. 2 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« « Mémoire en fragments : quand l’art défie la muraille de verre » »; « Les mémoires oubliées de Tbilissi : quand l’Histoire résiste aux algorithmes »_
- [ ] 48. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario reference`
  - _payant, un appel_
- [ ] 49. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 50. Base
  - `python3 generator/validate.py`
- [ ] 51. Lore
  - `python3 generator/audit_lore.py --scenario reference`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Alliance des Territoires Froids Européens
  category: <à choisir>
  role: Bloc de coopération pour la gestion des crises climatiques et énergétiques en Europe du Nord-Ouest,
    regroupant des régions sinistrées et des villes en repli.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: europe_occidentale_reconstruite
  source: et_si_effondrement_circulation_atlantique_2067
- nom: Consortium des Deltas de Crise
  category: <à choisir>
  role: Structure de coordination entre les zones submergées (Gange, Mékong) pour gérer les migrations
    climatiques et les conflits fonciers, en partenariat avec les Consortiums d'Agriculture Verticale.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: zones_grises_globales
  source: et_si_effondrement_circulation_atlantique_2067
- nom: Fonds d'Urgence Climatique Atlantique
  category: <à choisir>
  role: Fonds spéculatif créé par Ergo-Wian et des Consortiums Opaques pour investir dans les infrastructures
    de relocalisation et les technologies de survie en Europe du Nord-Ouest.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: europe_occidentale_reconstruite
  source: et_si_effondrement_circulation_atlantique_2067
```

## Liste d'application — injection commune

Mode rupture : `mode_impose: rupture` fait écrire `mode: rupture` dans chaque fiche ; le moteur déplace alors durablement la référence du scénario au lieu d'amortir un choc.

Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). Forces, polarités, durées, date et propagation de cette simulation sont imposées (`impacts_imposes`, `date_imposee`, `via_matrice_impose`) : l'IA de l'injection ne les recalcule pas, elle rédige seulement le récit.

`acteurs_hint` : entités les plus touchées de chaque scénario (lecture IA, passe exhaustive), 4 au plus par scénario ; chaque slug ne vaut que pour son scénario.

`faits_imposes` : contraintes de l'hypothèse et sort des acteurs du récit (disparaît, change, reste) ; l'injection les donne à l'IA comme faits non négociables.

```yaml
- id: effondrement_circulation_atlantique_2067
  description: En 2067, la grande circulation océanique de l'Atlantique (dont le Gulf Stream) s'effondre
    de façon irréversible. L'Europe du Nord-Ouest se refroidit de plusieurs degrés en une décennie, les
    moussons africaines et sud-américaines se déplacent, le niveau de la mer monte brusquement sur la
    côte est américaine. Le monde ne revient pas à l'état d'avant.
  portee: globale
  date_approximative: 2067
  intensite: <à choisir>
  persistance: normale
  scenarios:
  - reference
  variables_hint:
  - climat_environnement_global
  - systemes_productifs_travail
  - energie_ressources_critiques
  - demographie_mobilite_humaine
  variables_hint_count: 4
  source: et_si_effondrement_circulation_atlantique_2067
  acteurs_hint:
  - delta_du_gange_reference
  - consortiums_d_agriculture_verticale_algorithmique_reference
  - autorites_regionales_de_regulation_hydrologique_reference
  - fonds_souverain_arctique_scandinave_reference
  acteurs_hint_count: 4
  faits_imposes:
    reference:
    - fait: 'La circulation atlantique ne redémarre pas avant 2098 : le changement est permanent.'
      sort: contrainte
    - fait: Le refroidissement touche surtout l'Europe du Nord-Ouest ; le réchauffement global continue
        ailleurs.
      sort: contrainte
    - fait: 'Delta du Gange — Zone de Crise Permanente (delta_du_gange_reference) passe de « déclinant
        » à « résiduel » après 2067 : elle existe toujours (elle peut perdre des lieux, des biens ou du
        pouvoir), ne la décris pas comme disparue.'
      slug: delta_du_gange_reference
      sort: change
    - fait: 'Consortiums d''Agriculture Verticale Algorithmique (consortiums_d_agriculture_verticale_algorithmique_reference)
        passe de « émergent » à « ascendant » après 2067 : elle existe toujours (elle peut perdre des
        lieux, des biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: consortiums_d_agriculture_verticale_algorithmique_reference
      sort: change
    - fait: 'Autorités Régionales de Régulation Hydrologique (autorites_regionales_de_regulation_hydrologique_reference)
        passe de « émergent » à « dominant » après 2067 : elle existe toujours (elle peut perdre des lieux,
        des biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: autorites_regionales_de_regulation_hydrologique_reference
      sort: change
    - fait: 'Fonds Souverain Arctique Scandinave (fonds_souverain_arctique_scandinave_reference) passe
        de « ascendant » à « dominant » après 2067 : elle existe toujours (elle peut perdre des lieux,
        des biens ou du pouvoir), ne la décris pas comme disparue.'
      slug: fonds_souverain_arctique_scandinave_reference
      sort: change
    - fait: 'La zone Europe Occidentale Reconstruite (europe_occidentale_reconstruite) passe de « stable
        » à « fragmenté » : le lieu subsiste.'
      slug: europe_occidentale_reconstruite
      sort: zone
    - fait: 'La zone Union Africaine de Résilience Territoriale (union_africaine_resilience) passe de
        « emergent » à « fragmenté » : le lieu subsiste.'
      slug: union_africaine_resilience
      sort: zone
  date_imposee: 2067
  mode_impose: rupture
  impacts_imposes:
    reference:
    - variable: climat_environnement_global
      delta_level: 6
      duree: 10
      polarite: 1
    - variable: systemes_productifs_travail
      delta_level: 4
      duree: 8
      polarite: 1
    - variable: energie_ressources_critiques
      delta_level: 3
      duree: 5
      polarite: 1
    - variable: demographie_mobilite_humaine
      delta_level: 4
      duree: 15
      polarite: 1
  via_matrice_impose: true
```

