# Backlog actif — Ourrassol 2098

*Ce qui reste ouvert, et seulement cela. Mis au propre le 24 octobre 2026, mis à
jour le 30 octobre : les chantiers clos ont été retirés (leur détail est dans
`BACKLOG_ARCHIVE.md`, à uploader seulement pour vérifier si un point a déjà été
traité). Chaque chantier garde son nom et son numéro : les réutiliser tels quels.
Mode d'emploi des outils : `USER_MANUAL_COMPLET.md` ; dernier état de session :
`HANDOFF_30_OCTOBRE.md` (signaux faibles propagés par la matrice, petits
chantiers S20 / S21 / S24 / S28.1).*

Légende : 🟢 chantier actif · 🟡 en cours, partiellement traité · ⚪ en attente
d'un signal ou d'un besoin (pas de calendrier).

---

# PARTIE 1 — CHANTIERS ACTIFS

## 🟢 3. P20 — Images des articles (service à brancher)

Tout est codé (21 août) sauf le service externe de génération d'image :
Anthropic n'a pas d'API image, un service tiers est à choisir (OpenAI,
Stability, Google Imagen…). Point d'intégration prêt :
`_generate_image_via_api()` dans `generate_images.py` (signature stable).

- Les champs de publication (`chapo`, `image_prompt`, `tags`, `a_une_photo`,
  `image_credit`, `journaliste_slug`, `date_evenement`, `zone_principale`,
  `entites_citees`…) sont écrits à la génération ; voir manuel §2.
- En attendant, `generate_images.py` pose un placeholder neutre ; un placeholder
  « IA non branchée » est retraité automatiquement au run suivant.
- Le site affiche un emplacement vide pour les articles `a_une_photo: true` :
  au branchement, passer le fichier et `image_alt` dans `export_revues.py`.
- À faire au branchement : régénérer l'image de l'article fortress_world du
  23 août (`20260823_080632_…_18octobre2098.md`), dont l'`image_prompt` a été
  corrigé (Halifax-Haute au lieu de Bruxelles-Forteresse).
- Non testé en réel : la consigne « une personne ou entité nommée doit être
  représentée » de l'`image_prompt` (demande un lot au sujet individualisé).

## 🟢 5. Site des revues — suites

En ligne : https://ourrassol.pages.dev (kiosque + 12 revues). Publier :
`python3 generator/chapos_revues.py` (si nouveaux articles) puis
`bash generator/publier_site.sh`. Mode d'emploi : manuel §2octies.

Reste, dans l'ordre envisagé :
1. **12 identités visuelles** : un bloc `style` par revue dans `revues.yaml`
   (polices, couleurs, variantes de mise en page) lu par `export_revues.py` ;
   une maquette par revue à valider, comme celle du *Courrier des Continents*.
   Les champs `style_visuel` sont déjà posés (ex. `samizdat`,
   `transcription_radio`).
2. **Photos** : voir #3.
3. **Audio** (*Radio Frontières*, journaux oraux `type_diffusion: oral`) :
   stockage Cloudflare R2 envisagé ; origine des extraits (synthèse vocale ou
   enregistrements) à décider.
4. **Version multilingue** : libellés fixes par langue, pages sous
   `site/<langue>/` ; attention au plafond Cloudflare Pages (20 000 fichiers).
5. Optionnel : titre réécrit par la revue et encadré « Contexte » (même appel
   que le chapô) ; protection d'accès Cloudflare pendant les tests ; bouton
   « Publier » dans le GUI ; références entre articles.

Volume par revue : voir S23.

---

# PARTIE 2 — SECONDAIRE

*Pas d'action tant que rien ne remonte (récurrence, besoin concret).*

## 🟡 S23. Génération d'articles — restes

- **Volume très inégal entre revues** (audit du 30 oct, 216 articles, tous
  publiables) : Courrier des Continents 6, Crieur des Marges 7, Chronique 8,
  Miroir 8, Moniteur 10, Peuple Souverain 13, Journal des Normes 16, Lecteur des
  Communs 17, Radio Frontières 24, Contre-Courant 30, Limes 35, Revue de la
  Transition 42. Plancher à 15 = 38 articles (Courrier 9, Crieur 8, Chronique 7,
  Miroir 7, Moniteur 5, Peuple 2) ; à 20 = 75. Conseil : 15 d'abord. Plancher
  pas encore choisi, chantier mis de côté le 30 oct. Moyen : séries ciblées
  (scénario + ligne éditoriale dans `config_series.yaml`). **Avant de générer en
  volume**, vérifier que les trois sources de noms de réseaux (ci-dessous)
  concordent.
- **Trois sources pour les noms de réseaux** : `JOURNAL_PROFILES`
  (`prompt_builder.py`), `journaux.yaml` et `generate_journaux.py`. Non traité.
- **Hyphan** : exclue des articles hors `reference` ; la ré-exclure après toute
  régénération de sa fiche.
- Laissé tel quel (décision du 5 oct) : l'article Amazônia Viva
  (`20260924_101034_…`) fait de Hyphan la dirigeante d'Ergo-Wian « depuis 2091 ».

## 🟡 S25. Kharg-9 surreprésenté — en surveillance

Traité le 6 oct : cooldown durci pour toutes les instances (`loader.py`,
`COOLDOWN_STREAK` 2, `COOLDOWN_DURATION` 3), Kharg-9 exclu en eco_communalism,
doublon retiré du site. Reste : **mesurer l'effet** après les prochaines séries
(articles postérieurs au 6 oct) ; si les titres se répètent encore (« casino des
données », « défie Genève-Nexus »), retoucher la `description_journalistique`
de l'instance.

## ⚪ S30. Simulateur « et si ? » — à valider à l'usage

Le simulateur et son parcours sont terminés (S27, clos le 24 oct ; manuel
§3quinquies). À cocher au fil des prochaines hypothèses, sans session dédiée :

- **Livré le 24 oct, testé sur copie ou avec une IA simulée seulement** :
  - tri à l'étape ③ (« Liste de l'étape ④ », Sauter / Inclure avant
    l'injection, repris à l'étape ④) — seul `--plan` a tourné en réel ;
  - aperçu « au passé » lancé automatiquement à l'étape ④, puis rubrique
    « ⏳ Fiches des entités disparues » de l'étape ⑤ ;
  - plafond d'impact ramené (entités custom, `instance_generation_common.py`).
- **Carte, jamais vue sur le vrai vault** : zone vidée de tout territoire et ses
  journaux (garder en exil / retirer) ; création d'une nouvelle zone
  (`nouvelle_zone`) ; « déplacer entière » une sous-zone à plusieurs pays.
- **Exemples à ne jamais adopter** : `occupation_bresil_2029` et
  `reunification_ecosse_2070` (`et_si/hypotheses.yaml`) ; `invasion_bresil_2029`
  reste au banc de rejeu.
- **Second cas test proposé : « La ruée vers l'espace »** (scénario de la
  saison 3 de la Red Team Défense : tensions sur l'exploitation des ressources
  spatiales, acteurs privés et étatiques). L'espace a sa variable :
  `frontieres_du_systeme` (orbite, exploration, industrie spatiale,
  colonisation, ressources spatiales ; établi le 25 oct).
- Optionnel (ex-S27.5) : homonymes (Santa Cruz, Sucre, Perth, Medina) ;
  synthèse haut niveau des hypothèses ; récit IA de `trace_injection.py` (repli
  sur le modèle) ; idées issues de la Red Team Défense : **wild cards** (type
  d'événement « rupture » assumé, faible probabilité et impact majeur, injecté
  même s'il bouscule le lore ; les signaux faibles ne conviennent pas, ils sont
  déjà observables) et **passe « équipe rouge »** (faire attaquer les
  hypothèses d'un scénario plutôt qu'en vérifier la cohérence, ex. « qu'est-ce
  qui ferait tomber Ergo-Wian en dix ans ? » ; à confier à l'IA ou à des
  lecteurs aux profils variés, pour compenser le fait que David imagine seul).
  Source d'inspiration : la série *Ces guerres qui nous attendent*, qui
  restitue une partie des travaux de la Red Team Défense.

## ⚪ S24. Anomalies de données et suites techniques

Doublons d'entités et anomalies de géographie **traités le 24 oct au soir**
(12 doublons, soit 13 fusions ; 6 renommages ; 7 corrections de géographie ; détail dans
`BACKLOG_ARCHIVE.md`). Reste :

- **Géographie — appréciations, sans erreur** : `asie_pacifique_sud_est`
  (breakdown) jugée trop centralisée pour le patron spatial ; 3 zones de
  reference jugées trop innovantes ; **Paraguay** rangé sous
  `amazon_pacte_gardiens` (breakdown), approximatif mais non signalé.
- **Doublons** : relancer `scan_doublons_lore.py` après chaque gros lot
  d'entités. Il ne voit que les noms proches (`hanse_baltique` lui avait
  échappé). Les 9 paires qu'il signale encore sont des acteurs distincts, déjà
  examinés.
- **Incohérences `origine_reelle` / chaîne de parenté** (scan du 30 oct,
  `scan_geographie_complet.py --all`, étape 3) : choix de lore pour chacune —
  déplacer la zone sous la candidate, réaffecter le pays dans la Carte, ou
  laisser :
  - breakdown, `hanse_baltique` (Pologne) sous `arc_eurasien_central`, qui n'a
    pas la Pologne → candidate `geneve_bunker_institutions` (l'alerte du 24 oct
    n'a donc pas disparu) ;
  - breakdown, `la_haye_cour_internationale` (Pays-Bas) sous `la_haye_tribunal`
    → candidate `europe_nord_ouest` ;
  - fortress_world, `almaty_zone_friction` (Kazakhstan) sous
    `zones_grises_tampons` → candidate `bloc_eurasiatique_occidental`.
  Le même scan signale 6 zones suspectes de patron spatial (résultats en cache,
  aucune modification).
- **Trajectoires « émergent » par défaut** sur beaucoup de fiches (la lecture IA
  propose souvent « émergent → dominant » d'un coup ; signalé ⚠ à l'étape ④).
- **Ancrage local** : une zone sans instance localisée reste dominée par des
  entités d'ailleurs (Maghreb ; Sri Lanka : 0 instance locale). Créer des
  instances localisées si le besoin se confirme.
- **`_slugify()` (`api.py`)** : ø, æ, å, ß, ł deviennent `_`. Corriger changerait
  les slugs existants ; sans effet visible sur le site (`export_revues.py` lit les
  deux formes).
- **`generate_journaux.py --update`** : un lot au JSON cassé laisse des
  rédactions factices (`validate.py` les signale ; nettoyage
  `clean_fallback_journaux.py`). Piste : parse JSON tolérant.
- **Audits S23** (`audit_signatures.py`, `audit_lieu_zone.py`,
  `audit_temporel.py`) : CLI seulement.
- **Bloc `===METADONNEES_PUBLICATION===`** resté une fois dans un article après
  un retry de longueur : relancer de temps en temps `reparer_bloc_metadonnees.py`
  (aperçu gratuit ; 0 article le 30 oct) ; cause non vérifiée dans `api.py`.

## ⚪ S19. Propagation dynamique — surveillance et réglages

Moteur `dynamique.py` (manuel §3ter). Règle actée : **choc = s'estompe, rupture
= change le monde** ; `GAIN_CHOCS` 0,25 inchangé (17 oct).

- **Matrice révisée le 25 oct (S28.1)** : gain des boucles ρ(|K·C|) passé de
  0,42 à 0,34 avec `K_COUPLAGE` inchangé (0,05) ; niveaux 2098 déplacés d'au
  plus 1,2 point (référence : `documentation/niveaux_avant_s28.json`). Décision :
  ne pas recaler K pour l'instant. **Au prochain gros lot d'injections**, lancer
  le banc et décider s'il faut passer K à ≈ 0,063 (même ρ qu'au 27 sept).
  Vérifié le 30 oct : aucune injection depuis le 25 (0 fiche modifiée dans
  `instances/`, `event_instances/`, `signaux_custom/`). Commentaire de
  `K_COUPLAGE` mis à jour (ρ ≈ 0,34).
- **Signaux faibles propagés depuis le 30 oct** (clos, détail dans l'archive) :
  les 22 entrées des 10 signaux à `true`, défaut `true` dans
  `inject_custom_signals.py`. À garder en tête au prochain banc : les signaux
  comptent désormais dans le couplage (écart 1,1 point au plus le 30 oct,
  référence `documentation/niveaux_avant_s19_signaux.json`).
- **Saturation près des bornes** : en breakdown, 8 variables finissent entre 99
  et 100 ; en new_sustainability, `gouvernance_institutions` descend à 0,3. Un
  choc y est presque sans effet chiffré (Pacte de Tabriz, 24 oct : +0,3 au plus).
  À revoir seulement si des articles en pâtissent.
- **Dérive de `reference` vers fortress_world** (géopolitique 75 → 86 en 2098) :
  peut-être voulue par le lore.
- **Après un gros lot d'injections** : `python3 generator/banc_calibration.py
  --scenarios all --balayage-k 0.05`, et `mesure_niveaux.py` avant / après tout
  réglage de `GAIN_CHOCS`, `DEMI_VIE`, `DEMI_VIE_PAR_TYPE` ou `PERSISTANCE`.
- Mineurs : `matplotlib` absent (le banc écrit des CSV) ; les tendances
  (`trend`) des fiches scénario ne sont lues par aucun calcul.

## ⚪ S18. Audit du lore — usage courant

- **Règles de lore manquantes** pour new_sustainability, eco_communalism et
  policy_reform (faits à fournir par David quand le besoin se présente).
  breakdown a ses premières règles depuis le 23-24 oct (Genève, Iran), reference
  en a de plus (Mourmansk, Atlantique).
- **Routine après chaque lot d'entités** : étapes 1 → 2 → 3 de « Relations &
  lore », puis `validate.py`.
- **Relectures IA ciblées** au fil de l'eau (étape 4, `--limit 10` par scénario,
  ≈ 5 centimes) ; une passe complète (≈ 830 fiches) coûterait 4 à 6 $.
- Pièges de slugs ≠ noms : `les_veilleurs_des_nappes_phreatiques` = Sentinelles
  des Aquifères Oubliés ; `conseil_regulation_algorithmique` = Autorité
  Numérique du Bloc Atlantique (≠ `anba_siege_atlantique`, entreprise maritime).
- `_a_supprimer/` contient la fiche et l'archétype fusionnés des Archives
  Neutres (`fusion_archives_neutres_geneve_breakdown_20261013_1921/`), les
  13 dossiers `fusion_*_20261024_*` du 24 oct et
  `geographie_obsolete/breakdown_avant_test.md` : à vider quand les fusions sont
  confirmées à l'usage (articles générés sans anomalie).

## ⚪ S14. Couleur fantôme Royaume-Uni / Angleterre / Écosse / Galles

Surveillance : quatre noms partagent un polygone ; réaffecter un seul nom peut
laisser une couleur fantôme. À revérifier si l'un d'eux change de zone. Le bouton
de la Carte garde désormais le `type_entite` d'origine (corrigé le 23 oct). Les
2 alertes du garde-fou sur les sous-zones de `sao_paulo_megapole`
(fortress_world) ont disparu au scan du 30 oct.

## ⚪ S20. Signaux faibles et idées en texte libre — pistes

Mises de côté par David, à rouvrir à l'usage :
- bouton « Proposer en événement » quand l'assistant ✨ signale « ressemble
  plutôt à un événement » ;
- doublons d'idées sous un autre nom (`idees_vers_queue.py` ne compare que l'`id`) ;
- reprise d'injection partielle (`idee_a_remettre_en_queue`) testée en
  synthétique seulement ; elle ne couvre pas un échec par exception ;
- un signal custom n'est jamais « structurant » dans
  `build_signal_trajectory()` (constat) ;
- `/api/yaml/append` garde désormais l'en-tête modèle de `queue.yaml`
  (correctif du 30 oct, testé sur copie) : **à vérifier au prochain ajout depuis
  le GUI** (ex. entrée de queue préparée dans 🔭), puis retirer ce point ;
- pas de champ `persistance` dans la file des entités (à ajouter si besoin).

## ⚪ S21. Veille monde réel et signaux faibles — suites

Chaîne en production (manuel §3quater). Pistes :
- **Injection des signaux** : les 6 scénarios sont obligatoires, `polarite` ±1
  et un seul `delta_level`. Noté pour plus tard : a) « sans suite » par
  scénario ; b) `delta_level` par scénario.
- **10 candidats RSS à trier** dans l'onglet 🔭 (dont 2 faibles : Wegovy, BCE).
- **Livres** : 32 pages repérées restent dans le rapport JRC (≈ 4 passes).
  Prompt d'extraction durci le 30 oct (recommandation de l'auteur ≠
  observation ; grand programme d'État ≠ marginal) : juger l'effet aux
  prochaines passes.
  Documents à déposer : ESPAS Horizon Scanning n° 10, JRC FUTURINNOV, PNUE
  Navigating New Horizons, WEF Top 10 Emerging Technologies 2025, ONU Horizon
  Scanning 2026.
- **Flux RSS** : 16 flux sur 31 sources depuis le 30 oct (1 trouvé et écrit par
  `verifier_flux_rss.py --apply`) ; le relancer de temps en temps ; ajouter des
  sources de façon ciblée (flux actif, résumé exploitable, angle absent des
  16 flux) ; les 15 sources sans flux sont institutionnelles (OCDE, PNUD, JRC,
  ESPAS…), exploitées par les livres ou le prompt collé ; Crisis Group n'a pas de flux CrisisWatch ; certains flux ne donnent
  qu'un résumé (STAT+, Rest of World, GEAB).
- Non faits : OCR des PDF scannés ; fusion multi-IA pour l'état du monde ;
  défaire une fusion dans 🔭 ; recherche web en deux temps (≈ 12 fois plus chère).
- Idée : repérer les signaux qui relient plusieurs variables (analyse en réseau
  sur la matrice 12×12 ; `micmac_matrice.py` en donne la base).

## ⚪ S28. Outils externes à greffer (pistes du 6 oct)

*Origine : comparaison d'Ourrassol avec la Red Team Défense (ministère des
Armées, lancée en 2019-2020 ; arrêtée en 2023 après trois saisons, à vérifier
avant de s'y référer). Même matière (ruptures technologiques, géopolitiques,
sociales), intention différente : la Red Team provoque des décideurs avec des
scénarios ponctuels 2030-2060 imaginés par des auteurs de SF, BD et scénaristes,
critiqués par des militaires et des scientifiques ; Ourrassol construit six
mondes parallèles cohérents sur 2025-2098 et les fait vivre par une presse
fictive, avec une veille outillée et des contrôles de cohérence.*

*Ce qu'Ourrassol fait mieux : la **propagation** (un événement injecté se
diffuse et se mesure dans le temps, `trace_injection.py`) ; la **pluralité des
regards** (pouvoir et opposition, depuis sa zone ou une autre, S26) ; la
**traçabilité** (chaque idée a une origine, une date, et on sait où elle a
pesé). Son point faible : la **surprise**. Le moteur ramène les variables vers
leur référence et sature près des bornes (S19) ; l'audit du lore corrige ce qui
détonne (S18) ; l'IA recycle ce qu'elle a lu (Kharg-9, S25) ; et David imagine
seul, là où la Red Team croisait des sensibilités très différentes. Le système
approfondit bien une rupture qu'on lui donne, beaucoup moins il n'en invente
une vraiment dérangeante. D'où les pistes ci-dessous, et les wild cards et la
passe « équipe rouge » de S30.*

**1. MICMAC : clos le 25 oct** (`micmac_matrice.py`, matrice d'influence révisée
dans l'Atelier, détail dans `BACKLOG_ARCHIVE.md`). Suites, sans calendrier :
- **Relancer `micmac_matrice.py`** après toute retouche de `influence_matrix.md`
  ou d'une `systemic_criticality`, puis `regenerer_position_fiches.py --apply`.
  Référence du 25 oct : motrices climat et technologie, dépendante territoires.
- **`variable_type` des fiches** (moteur / relais / réactive) : gardé comme
  **intention de conception**, distinct du classement MICMAC (décision du
  25 oct) ; il diverge sur 7 variables (géopolitique, énergie, productifs,
  démographie, gouvernance, territoires, valeurs). Lu par `generate_entities.py`.
- **`coupling_intensity`** (dans `states` de chaque fiche, par scénario) :
  **examiné le 30 oct.** Aujourd'hui lu par aucun calcul ni aucun prompt :
  `loader.py` le charge, `snapshot.py` le transmet, personne ne s'en sert
  (`export_prompt_veille.py`, `extract_state_logic.py` et
  `inject_custom_signals.py` ne font que contourner ses clés en wikilink). Aucun
  risque de contradiction avec la matrice. Mais la donnée a de la valeur : 2 à 4
  partenaires par scénario, différents d'un monde à l'autre et cohérents avec la
  `state_logic` (ex. énergie : géopolitique en fortress_world / breakdown,
  technologie et gouvernance en new_sustainability / policy_reform, territoires
  en eco_communalism) — l'information « par scénario » que la matrice, commune
  aux 6, n'a pas. Limites : palmarès, pas matrice complète ; sens du lien non
  précisé. Deux usages notés, rien de codé :
  - **prompt des articles** (le plus simple, conseillé) : une ligne « liens
    marquants dans ce scénario » à côté de `state_logic` / `dominant_dynamics`
    dans `prompt_builder.py` (l. 1356-1420) ; aucun chiffre ne bouge ;
  - **moteur** : moduler la matrice par scénario (liens listés renforcés) ;
    demande une règle pour les liens absents et un recalage au banc → à traiter
    avec S28.2 (CIB), même logique de liens dépendant de l'état du monde.
- **Texte rédigé des fiches** (sections 3 à 10) : peut encore évoquer des liens
  modifiés ; à relire au fil de l'eau.
- La criticité (`systemic_criticality`) pèse lourd dans le classement (×0,7 à
  ×1,6 sur tous les liens sortants) : à rediscuter si un classement surprend.
- Atelier de la matrice (page privée) : https://claude.ai/artifact/WgAxTF4arr9aRB5w7F9vxf
  — réutilisable pour une prochaine révision des poids.

Reste, rien de décidé ni de codé ; ordre conseillé : 2 (plus pertinent depuis que
la matrice est asymétrique), puis 3.
2. **CIB (Cross-Impact Balance)**, logiciel ScenarioWizard, maintenu par le
   CIB-Lab de Stuttgart (version récente sur Zenodo ; licence et formats à
   vérifier). On note comment l'**état** de chaque variable favorise ou freine
   l'état des autres, et le logiciel liste toutes les combinaisons cohérentes.
   Apport : vérifier que les 6 scénarios sont des configurations stables, et
   surtout faire apparaître des configurations cohérentes non imaginées : la
   réponse méthodique au manque de surprise. Coût : noter la matrice autrement,
   par états de variables et non par poids (≈ 1 200 jugements avec 3 états par
   variable). Point de départ possible : `coupling_intensity` (voir S28.1), qui
   donne déjà les liens marquants de chaque scénario.
3. **Base SSP de l'IIASA** (Shared Socioeconomic Pathways) : population, PIB,
   urbanisation, énergie et émissions par grande région jusqu'en 2100, pour cinq
   futurs. Correspondances : fortress_world ≈ SSP3, new_sustainability ≈ SSP1,
   policy_reform ≈ SSP2 (les autres à établir). Apport : ordres de grandeur
   crédibles pour les articles (population d'une zone en 2098, mix
   énergétique) et repère pour les niveaux des variables. Le plus utile pour la
   crédibilité des articles.
4. **API Metaculus** (2026-2035 ; conditions d'accès à vérifier) : nourrir
   `etat_du_monde_reel.md` avec ce que les prévisionnistes jugent probable, pas
   seulement ce qui s'est passé.
5. **Détection de signaux en complément du RSS** : **GDELT** (base mondiale
   d'événements tirés de la presse, accès libre ; tendances par pays ou par
   thème pour repérer une montée encore marginale) et **OpenAlex** (API
   gratuite sur la publication scientifique ; un sujet dont le nombre
   d'articles décolle est un bon signal faible technologique, dans l'esprit des
   catalogues du JRC).
En marge : *Global Trends 2040* comme grille de comparaison.

## ⚪ S1. Fiabilité de `mistral-small` sur choix contraint (P17)

Relancer une génération d'article avec `LLM_PROVIDER=mistral
LLM_MODEL=mistral-small-latest` et comparer à `mistral-large` (la contamination
de juillet venait d'un bug de zone, pas du modèle). Gardé pour plus tard. Même
principe pour P25 (signature journaliste, ~25-33 % d'échec en août) : observer
avant de corriger.

## ⚪ S2. Plausibilité logistique inter-zones (bug #27)

Un cas en juillet (personnage d'Amazonie arrivant en pirogue depuis le Congo).
David veut d'abord analyser des articles pour mesurer la récurrence ; pas de
correctif préventif.

## ⚪ S4. JSON d'instances illisible (Mistral)

`extraire_json()` tolère désormais texte autour, imbrication profonde et
virgules finales. **Au prochain échec, lire `gui/logs/llm_json_echec_*.txt`**
avant de conclure à une troncature ; retry dédié seulement si le cas devient
fréquent.

## ⚪ S5. `promote_ville.py` dans le GUI

Le script marche en CLI mais demande des confirmations (`input()`). À trancher
un jour : redécoupage interactif (comme les écrans SSE) ou bouton à paramètres
fixes.

## ⚪ S8. `--min-shingle` en dur dans `detect_registre_leakage()`

Fixé à 6 mots ; en faire une option seulement si un faux positif ou négatif
apparaît.

## ⚪ S9. Confusion slug de zone / slug d'instance

Un cas le 4 août, résolu par retry. Si cela se reproduit : lister dans le prompt
les slugs de zones à ne pas utiliser.

## ⚪ S15. Suites optionnelles du scénario Hyphan (fortress_world)

- Milan (QG du Mouvement de Reconquête européenne) et Lyon (son antenne) ne sont
  que des `lieu` dans `zone_euro_sud` : en faire des sous-zones si d'autres
  entités doivent y être placées (Carte → ➕ sous-zone).
- Personnages en réserve, exclus des articles : Malo, Anton Vasko, Raimon et
  Hyphan ; à ré-autoriser (🎯) quand le récit les fera apparaître.

## ⚪ S29. Mistral Large 4 — à rejuger

Branché (`mistral-large-4` dans le sélecteur), non retenu par défaut. À rejuger
s'il sort de l'aperçu, si la réflexion peut être coupée ou si le tarif baisse.
Avant tout usage hors article : relever `max_tokens` (la réflexion peut tout
consommer).
