# Backlog actif — Ourrassol 2098

*Ce qui reste ouvert, et seulement cela. Mis au propre le 24 octobre 2026 : les
chantiers clos ont été retirés (leur détail est dans `BACKLOG_ARCHIVE.md`, à
uploader seulement pour vérifier si un point a déjà été traité). Chaque chantier
garde son nom et son numéro : les réutiliser tels quels. Mode d'emploi des outils :
`USER_MANUAL_COMPLET.md` ; dernier état de session : `HANDOFF_24_OCTOBRE.md`.*

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

- **Volume très inégal entre revues** (« 📰 Audit des revues », 5 oct) :
  Crieur des Marges 5, Courrier des Continents 6, Chronique 8, Miroir 8,
  Moniteur 11, Peuple Souverain 13, Journal des Normes 17, Lecteur des Communs
  18, Radio Frontières 24, Contre-Courant 30, Limes 35, Revue de la Transition
  44. Remonter toutes les revues à 15 = 39 articles ; à 20 = 74. Moyen : séries
  ciblées (scénario + ligne éditoriale dans `config_series.yaml`). Pas encore
  lancé.
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
- Cosmétique : `et_si_injecter.py --plan` affiche « ⚠ déjà appliqué » au lieu
  de « · déjà appliqué ».
- Optionnel (ex-S27.5) : homonymes (Santa Cruz, Sucre, Perth, Medina) ;
  synthèse haut niveau des hypothèses ; récit IA de `trace_injection.py` (repli
  sur le modèle) ; idées « wild cards » et « passe équipe rouge » (Red Team
  Défense, voir S28).

## ⚪ S24. Anomalies de données et suites techniques

À vérifier à la main ; rien n'a été modifié.

- **Géographie** :
  - breakdown : **Uruguay** rattaché à `espace_nord_americain_fragmente` ;
    **`hanse_baltique`** (Pologne, côte baltique) rangée sous
    `arc_eurasien_central`, dont la Pologne ne fait pas partie (contrôle de
    géographie du 24 oct) ; `asie_pacifique_sud_est` jugée trop centralisée pour
    le patron spatial.
  - new_sustainability : le **Brésil** est porté par deux zones N1
    (`ameriques_reconfigurees`, `reseau_vivant_continental`).
  - reference : la sous-zone `sertao_nordeste_bresilien` déclare le **Paraguay
    (Chaco)** ; **Afghanistan, Kirghizistan, Tadjikistan** sans zone N1 ;
    3 zones jugées trop innovantes par le contrôle de géographie.
- **Doublons d'entités probables** (outil : `fusionner_doublon_instance.py
  --garder A --retirer B`, aperçu puis `--apply`) :
  - eco_communalism : `amazonie_pacte_viva_eco_communalism` /
    `consortium_amazonia_viva_eco_communalism` ;
  - reference : `amazonie_consortium_viva_reference` /
    `consortium_amazonia_viva_reference` ;
  - fortress_world : `bureau_des_territoires_residuels_fortress_world` /
    `bureau_territoires_residuels_fortress_world` ;
  - breakdown : trois « Communes Libres du Rust Belt »
    (`communes_rust_belt_breakdown`, `communes_rust_belt_zones_libres_breakdown`,
    `mouvement_des_communes_du_rust_belt_breakdown`) ; `hanse_baltique_breakdown`
    / `hanse_baltique_recomposee_breakdown`.
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
  `audit_temporel.py`) : CLI seulement ; `audit_signatures.py` n'exclut pas
  `_index.md` (6 faux positifs).
- **Bloc `===METADONNEES_PUBLICATION===`** resté une fois dans un article après
  un retry de longueur : relancer de temps en temps `reparer_bloc_metadonnees.py`
  (aperçu gratuit) ; cause non vérifiée dans `api.py`.

## ⚪ S19. Propagation dynamique — surveillance et réglages

Moteur `dynamique.py` (manuel §3ter). Règle actée : **choc = s'estompe, rupture
= change le monde** ; `GAIN_CHOCS` 0,25 inchangé (17 oct).

- **Signaux faibles non propagés** : un signal `propagation_via_matrice: false`
  (le défaut) agit sur sa variable mais pas sur les autres. Options non
  tranchées : a) passer certains signaux à `true` à la main ; b) changer la
  consigne de `inject_custom_signals.py` ; c) propager tous les signaux à ~30 %.
- **Saturation près des bornes** : en breakdown, 8 variables finissent entre 99
  et 100 ; en new_sustainability, `gouvernance_institutions` descend à 0,3. Un
  choc y est presque sans effet chiffré (Pacte de Tabriz, 24 oct : +0,3 au plus).
  À revoir seulement si des articles en pâtissent.
- **Dérive de `reference` vers fortress_world** (géopolitique 75 → 86 en 2098) :
  peut-être voulue par le lore.
- **Après un gros lot d'injections** : `python3 generator/banc_calibration.py
  --scenarios all --balayage-k 0.05`, et `mesure_niveaux.py` avant / après tout
  réglage de `GAIN_CHOCS`, `DEMI_VIE`, `DEMI_VIE_PAR_TYPE` ou `PERSISTANCE`.
- Mineurs : `undo_custom.py` ne recalcule pas la ligne « Total » du registre ;
  `matplotlib` absent (le banc écrit des CSV) ; les tendances (`trend`) des
  fiches scénario ne sont lues par aucun calcul.

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
  Neutres (`fusion_archives_neutres_geneve_breakdown_20261013_1921/`) : à vider
  quand la fusion est confirmée.

## ⚪ S14. Couleur fantôme Royaume-Uni / Angleterre / Écosse / Galles

Surveillance : quatre noms partagent un polygone ; réaffecter un seul nom peut
laisser une couleur fantôme. À revérifier si l'un d'eux change de zone. Le bouton
de la Carte garde désormais le `type_entite` d'origine (corrigé le 23 oct). Les
2 alertes du garde-fou sur les sous-zones de `sao_paulo_megapole`
(fortress_world) sont à reconfirmer au prochain scan de géographie.

## ⚪ S20. Signaux faibles et idées en texte libre — pistes

Mises de côté par David, à rouvrir à l'usage :
- bouton « Proposer en événement » quand l'assistant ✨ signale « ressemble
  plutôt à un événement » ;
- doublons d'idées sous un autre nom (`idees_vers_queue.py` ne compare que l'`id`) ;
- reprise d'injection partielle (`idee_a_remettre_en_queue`) testée en
  synthétique seulement ; elle ne couvre pas un échec par exception ;
- un signal custom n'est jamais « structurant » dans
  `build_signal_trajectory()` (constat) ;
- `/api/yaml/append` fait disparaître l'en-tête modèle de `queue.yaml` jusqu'au
  prochain run (cosmétique) ;
- pas de champ `persistance` dans la file des entités (à ajouter si besoin).

## ⚪ S21. Veille monde réel et signaux faibles — suites

Chaîne en production (manuel §3quater). Pistes :
- **Injection des signaux** : les 6 scénarios sont obligatoires, `polarite` ±1
  et un seul `delta_level`. Noté pour plus tard : a) « sans suite » par
  scénario ; b) `delta_level` par scénario.
- **10 candidats RSS à trier** dans l'onglet 🔭 (dont 2 faibles : Wegovy, BCE).
- **Livres** : 32 pages repérées restent dans le rapport JRC (≈ 4 passes).
  Documents à déposer : ESPAS Horizon Scanning n° 10, JRC FUTURINNOV, PNUE
  Navigating New Horizons, WEF Top 10 Emerging Technologies 2025, ONU Horizon
  Scanning 2026.
- **Prompt des livres** à durcir : une recommandation de l'auteur n'est pas une
  observation ; un grand programme d'État n'est pas marginal.
- **Flux RSS** : relancer `verifier_flux_rss.py` de temps en temps ; ajouter des
  sources de façon ciblée (flux actif, résumé exploitable, angle absent des
  15 flux) ; Crisis Group n'a pas de flux CrisisWatch ; certains flux ne donnent
  qu'un résumé (STAT+, Rest of World, GEAB).
- Non faits : OCR des PDF scannés ; fusion multi-IA pour l'état du monde ;
  défaire une fusion dans 🔭 ; recherche web en deux temps (≈ 12 fois plus chère).
- Idée : repérer les signaux qui relient plusieurs variables (analyse en réseau
  sur la matrice 12×12).

## ⚪ S28. Outils externes à greffer (pistes du 6 oct)

Rien de décidé ni de codé ; ordre conseillé : 1, puis 3 ou 2.
1. **MICMAC** sur `influence_matrix.md` : influence et dépendance directes et
   indirectes → variables motrices / relais / dépendantes / autonomes. Gratuit,
   sans IA, quelques lignes de Python.
2. **CIB (Cross-Impact Balance)**, logiciel ScenarioWizard : configurations
   cohérentes d'un jeu de variables à états ; contrôle de stabilité des 6
   scénarios. Licence et formats à vérifier.
3. **Base SSP de l'IIASA** : trajectoires chiffrées par région jusqu'en 2100,
   repère pour les ordres de grandeur.
4. **API Metaculus** (2026-2035) pour `etat_du_monde_reel.md`.
5. **GDELT** et **OpenAlex** en complément du RSS.
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
