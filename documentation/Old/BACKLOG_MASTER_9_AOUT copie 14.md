# Backlog maître — Ourrassol 2098
*Consolidé le 9 août 2026, à partir de l'ensemble des handoffs/backlogs du
1er août au 9 août 2026. Mis à jour en place le 10 août 2026 (chantier
longueur/qualité des articles générés), le 11 août 2026 en deux temps :
clarté des descriptifs GUI + validation navigateur (session du matin — voir
`HANDOFF_11_AOUT.md`), puis correctifs de bugs réels trouvés en testant les
3 dernières entrées GUI + clôture définitive du chantier de validation
navigateur (session du soir — voir `HANDOFF_11_AOUT_SOIR.md`), et le
12 août 2026 (validation réelle du correctif signature, diagnostic
`annee_debut`/`ancrage_reel` sur les événements + nouveau chantier de
cohérence événements custom — voir `HANDOFF_12_AOUT.md`), et le
13 août 2026 (chantier "dimension temporelle pour la génération
automatique" codé et validé en dry-run réel, confirmation en injection
réelle du chantier de cohérence événements custom du 12 août, bug
`evenement_cle` trouvé et corrigé — voir `HANDOFF_13_AOUT.md`), et le
14 août 2026 (session dense : recherche exhaustive dans l'archive complète
ayant retrouvé 4 chantiers tombés du radar sans clôture formelle, fusion du
doublon d'entité Arctic, nettoyage des wikilinks `test_durcissement`,
clôture des 4 reliquats du 7 août, correctif de la cause racine de
l'encodage portugais cassé dans les slugs (+ migration de 2 cas réels sur
le vault), filtre dur `acteurs_hint_count` enfin appliqué, déduplication de
`detect_registre_leakage()`, correctif du refresh GUI `--force` sur le
panneau localisation (3 causes, 3 fichiers), et identification d'un
chantier substantiel non résolu (`forces_attractives`/`forces_repulsives`,
contenu réel du vault jamais exploité par le pipeline) — voir
`HANDOFF_14_AOUT.md`), et le 15 août 2026 (chantier `forces_attractives`/
`forces_repulsives` mené à son terme : décision de source de vérité,
câblage `loader.py`/`prompt_builder.py`, et trois correctifs découverts et
validés en cours de route — consigne d'équilibre attractif/répulsif,
correction de la rotation d'instances (récurrence anormale de l'entité
`terminal_kharg_data_haven`), consigne de couverture des variables
pilotes ; correctif du nom réel du gabarit entité (`entity_template.md`,
pas `entite_template.md`) et déplacement vers `/templates` ; décision et
création de l'entité "Les Veilleurs des Nappes Phréatiques", avec audit et
correction de 4 autres fiches déjà touchées par la même catégorie
invalide — voir `HANDOFF_15_AOUT.md`), et le 16 août 2026 (chantier
"injection matricielle" mené sur les trois types d'injection custom :
câblage de l'impact chiffré sur variables pour les instances custom
(`impact_sur_variables`/`propagation_via_matrice`, plafond dérivé de
`impact_systemique_global`), extension du même mécanisme aux signaux
faibles (plafond fixe `MAX_DELTA_SIGNAL=10`, `annee_injection`/`duree`
dérivés de `date_bascule`), et nouveau contrôle de cohérence section 7 ↔
section 12 intégré à `validate.py` — voir `HANDOFF_16_AOUT.md`), et le
17 août 2026 (chantier "instances manquantes — audit et comblement" :
nouveau script `audit_instances_manquantes.py` créé, corrigé à deux
reprises après de vrais faux positifs trouvés en conditions réelles sur
le vault, puis intégré au GUI ; 19 trous de couverture initiaux
ramenés à 1 seul restant après diagnostic complet — dont la suppression
propre de l'entité de test résiduelle "Le Cartographe Silencieux" (19
juin 2026, jamais générée, dupliquée dans `entites_custom/
processed.yaml`) — et 13 instances effectivement régénérées ; nouveau
point mineur ouvert au passage, erreur de localisation sur
`gelecek_meclisi_policy_reform` — voir `HANDOFF_17_AOUT.md`), et le
18-19 août 2026 (diagnostic complet du slug de zone `istanbul` inconnu
sur `gelecek_meclisi_policy_reform`, nouveau script `promote_ville.py`
conçu et livré, chantier clos avec `validate.py` à 0 erreur/0
avertissement — première fois depuis le début de l'investigation ;
activation de `constrained_variables` dans le prompt (Option A) ;
découverte du bloc `simulation` jamais consommé en aval, documentée
comme nouveau chantier P22 nécessitant une session de conception dédiée
— voir `HANDOFF_19_AOUT.md`), une session du 20 août 2026 sans handoff
rédigé (P22 câblé dans `snapshot.py` : `volatility`/`tipping_point_risk`/
`systemic_criticality` rendus opérationnels avec logique de non-
régression, décision confirmée a posteriori le 21 août — trou de
traçabilité comblé rétroactivement dans `HANDOFF_21_AOUT.md`), et le
21 août 2026 (clôture du chantier retry longueur sur 25 articles post-
mécanisme réels, 100% de succès ; correctif du risque structurel
Partie 3 — garantie d'inclusion des instances custom dans
`filtered_instances`, `loader.py` ; ménage complet du vault en 5
catégories ; P20 Phase A codée et validée en conditions réelles sur 2
batches — voir `HANDOFF_21_AOUT.md`), et le 21 août 2026 (soir,
poursuite de séance : P20 Phases B et C codées et livrées
`generate_images.py`, `image_credit`, placeholders, garde-fou de
troncature `image_alt`, consigne `image_prompt` sujet nommé ; champs
GUI `a_une_photo`/`image_credit`/`photo_policy` sur `generate.py`/
`generate_series.py` ; débogage réel en conditions live avec David
révélant le piège de redémarrage Flask sur `photo_policy`, un nouveau
symptôme P25 (signature en pied d'article après un `---`), et la
décision du vocabulaire de tags accumulé/réutilisé — deux nouveaux
chantiers ouverts, tags et rétro-application sur les articles déjà
existants, aucun des deux codé, séance interrompue en plein débogage
— voir `HANDOFF_21_AOUT.md`, section "soir"). Remplace
tous les documents
précédents comme référence unique. Chaque chantier a un nom stable — à
réutiliser tel quel dans les prochaines sessions pour éviter toute
nouvelle divergence de nommage.*

---

# PARTIE 1 — CHANTIERS OUVERTS (à traiter)

---

## ⚪ 3. P17 — retester la fiabilité `mistral-small` sur choix contraint
**Retrouvé le 14 août** via recherche exhaustive dans l'archive (décidé
le 11 juillet, jamais fait, disparu du backlog sans clôture formelle
après la consolidation du 2 août). Le bug #26 avait montré que la
contamination culturelle observée les 6 et 11 juillet était en réalité
causée par un bug de résolution de zone, reproduit à l'identique sur
`mistral-small` **et** `mistral-large` — pas une limite de fiabilité
modèle comme diagnostiqué initialement. Reste à vérifier si un vrai
problème de fiabilité subsiste sur `mistral-small` une fois cette cause
de code éliminée : relancer une génération d'article sur `mistral-small`
(override manuel `LLM_PROVIDER=mistral LLM_MODEL=mistral-small-latest`)
et comparer au résultat obtenu sur `mistral-large`. **David a choisi de
le garder pour plus tard, non traité le 14 août.**

---

## ⚪ 4. Bug #27 — plausibilité logistique inter-zones
**Retrouvé le 14 août** via recherche exhaustive dans l'archive (noté le
11 juillet, jamais repris). Incohérence détectée sur un article test : un
personnage du Pacte Amazônia Viva (Amazonie) décrit comme arrivant par
un moyen de transport purement local (pirogue depuis Kisangani, Congo),
sans mention de la traversée intercontinentale attendue. Décision du 11
juillet : observer si ça se reproduit avant de renforcer
`build_system_prompt()` (`prompt_builder.py`) avec une consigne dédiée à
la plausibilité des trajets inter-zones — observation qui n'a en réalité
jamais eu lieu, personne n'ayant recherché activement le symptôme depuis.
**David veut faire une analyse d'articles pour vérifier la récurrence
avant de décider d'un correctif** — pas de correctif préventif sans
données. Non traité le 14 août, gardé pour plus tard.

---

## ⚪ 5. Renommage des YAML génériques par dossier
**Décision reportée une nouvelle fois le 14 août** (en pause depuis fin
juillet). `queue.yaml`/`processed.yaml`/`needs_review.yaml` répétés à
l'identique dans `entites_custom/`, `evenements_custom/`,
`signaux_custom/` — pas de collision technique (dossiers distincts),
juste une ambiguïté visuelle. Coût de migration identifié si un jour
tranché en faveur du renommage : constantes `QUEUE_PATH` dans 3 scripts,
entrées `scripts_config.json`, documentation (dont les `QUEUE_TEMPLATE`
eux-mêmes). Aucune urgence identifiée à ce jour.

---

## ⚪ 6. Troncatures JSON occasionnelles lors de la génération d'instances
(Mistral)
**Toujours en observation, gardé pour plus tard le 14 août.** Deux échecs
`"Aucun JSON exploitable trouvé dans la réponse"` observés le 11 août
lors de tests réels (`generate_instances`/`create_entities`) — le modèle
Mistral s'arrête en plein milieu du JSON. Diagnostic déjà fait : pas un
problème de plafond de tokens (`INSTANCE_MAX_TOKENS = 4000`, sorties bien
en dessous), aléa côté API, même famille que le timeout 503 vu le même
jour sur `extract_localisation.py`. Décision : point de vigilance, pas de
correctif codé tant que le taux reste faible (2/~35 générations observées)
— le mécanisme de résilience existant gère déjà correctement ce cas. À
surveiller : si le symptôme devient fréquent sur un futur batch de
volume, envisager un retry automatique dédié (distinct de celui déjà en
place sur la longueur des articles).

---

## ⚪ 8. Intégration GUI de `promote_ville.py`
**Nouveau, 19 août.** Script `promote_ville.py` livré et validé (voir Partie 4
pour le détail du chantier Istanbul qui l'a motivé) — injection ciblée d'une
ville en zone géographique, sur un ou plusieurs scénarios, avec détection
multi-forme (slug/nom/lieu_emblematique/mention narrative) et rattachement au
parent le plus précis. Fonctionne en CLI, jamais intégré au GUI Flask.
**Scopage non fait** : le script utilise `input()` pour les confirmations
interactives (cas ambigus de détection, choix du pays) — incompatible tel
quel avec une interface web, demanderait soit un redécoupage en étapes
(proposer → attendre le clic → continuer), soit un mode `--auto-promote`
sans confirmation. Deux pistes possibles, à trancher un jour : intégration
complète (redécoupage interactif façon SSE streaming, cohérent avec les
autres écrans à appels LLM) ou intégration légère (bouton déclenchant le
script en arrière-plan avec paramètres fixes, perd la finesse de contrôle
construite le 18-19 août). Reste utilisable en CLI dans l'intervalle — pas
bloquant.

---

## 🟢 9. P20 — Enrichissement frontmatter pour publication web (Phases A+B+C codées, service image à brancher)
**Relancé le 21 août** (scoping d'origine du 12 juillet, resté en pause
jusqu'ici — voir Partie 4 pour l'historique complet). Le chantier a été
redécoupé en 3 phases lors de la reprise, pour distinguer ce qui était
codable sans nouvelle décision de ce qui restait bloqué. **Les trois
phases sont maintenant codées** — seul le choix d'un service externe de
génération d'image reste en suspens (point technique isolé, pas un
blocage de conception).

**Phase A — codée et validée en conditions réelles (21 août)** : 7
champs (`slug`, `chapo`, `image_prompt`, `tags`, `a_une_photo`,
`journaliste_slug`, `date_evenement`) dans `api.py`/`prompt_builder.py`.
Bloc `===METADONNEES_PUBLICATION===` demandé au LLM dans le même appel
que l'article (Option 1 actée le 12 juillet), extrait et retiré du
texte avant tout comptage de mots pour ne pas fausser le retry longueur
du 10 août.

**Phase B — codée (21 août)**, trois décisions tranchées rapidement
grâce à du code déjà existant : `zone_principale` réutilise
`snapshot["zone_slug"]` (déjà calculé par `_dominant_zone()`, déjà
utilisé pour choisir le journal de zone — même valeur, pas un second
mécanisme) ; `date_publication` = `date_evenement` pour l'instant
(aucun délai éditorial simulé, champs gardés séparés pour ne pas fermer
la porte à un vrai décalage plus tard) ; `entites_citees` (liste des
slugs de `filtered_instances`) ajouté comme sous-produit gratuit,
prépare le rapprochement `articles_lies` — **calculé depuis, voir point
9bis ci-dessous**.

**Phase C — codée (21 août)**, `generate_images.py` (nouveau script) :
scanne les articles `a_une_photo: true`, traite selon `image_credit`
(`IA_generated` / `personnel` / `autre` / vide) — génère via API
(actuellement un stub, voir ci-dessous), ou pose un placeholder neutre
(2 SVG créés, `images/_placeholder_en_attente_manuel.svg` et
`..._generation.svg`) en attendant respectivement un upload manuel ou
le branchement d'un vrai service. Un placeholder "IA non branchée" est
automatiquement retraité au prochain run, sans `--force`. `image_alt`
dérivé d'`image_prompt` (pas de second appel LLM), avec garde-fou de
troncature à la phrase (`_truncate_alt()`, 180 caractères, jamais coupé
en plein mot) — testé sur cas réels de dépassement (LLM produisant 2-3
phrases au lieu d'une). Consigne d'`image_prompt` renforcée en cours de
route : si l'article porte sur une personne/entité nommée précise,
l'image doit la représenter explicitement, pas rester une scène neutre
anonyme — non testé en conditions réelles à ce stade (nécessite un
batch avec un sujet clairement individualisé).

**Service de génération d'image : décision explicite de report (21
août)** — Claude/Anthropic n'a pas d'API image native, un service tiers
est nécessaire (OpenAI/Stability/Google Imagen/autre, non choisi).
`_generate_image_via_api()` est un point d'intégration générique déjà
prêt (signature stable), à brancher le jour où le choix est fait.

**GUI — champs de décision manuelle, câblés au moment de l'écriture de
l'article plutôt qu'après coup uniquement (21 août)** : sur l'écran
"Générer un article" (semi-guidé ET forcer, aucune restriction de
mode), deux nouveaux champs — "Aura une image" (case à cocher,
décochée par défaut) et "Crédit image" (menu déroulant, vide par
défaut, ignoré si la case n'est pas cochée). Sur l'écran série, un
champ "Illustration des articles" — Aucune / Toutes / Aléatoire (25%,
probabilité actée avec David). En mode série, `image_credit` reste
toujours vide même quand `a_une_photo` devient `true` via la
politique — décision explicite, la source se choisit par article, plus
tard, avant de lancer `generate_images.py`.

**Testé en conditions réelles à trois reprises le 21 août** (2 batches
de 8 articles `fortress_world` avant la Phase B/C, puis un batch de 3
articles `policy_reform` généré depuis le GUI après Phase B/C) — voir
P25 ci-dessous pour le détail des anomalies de signature observées sur
ce dernier batch, qui restent le seul point non résolu de ce chantier.

**Piège rencontré et confirmé le 21 août (soir)** : un nouveau champ
`config_fields` ajouté à `scripts_config.json` n'apparaît dans le
formulaire GUI qu'après redémarrage de Flask — `photo_policy` absent de
`config_series.yaml` après un premier lancement en série malgré la
sélection "Toutes" à l'écran, parce que Flask n'avait pas encore été
redémarré au moment du lancement. Pas un bug de code (vérifié : `app.js`
construit le formulaire de façon générique depuis `config_fields`,
aucune whitelist figée à mettre à jour) — juste le piège de redémarrage
déjà documenté plusieurs fois par le passé (15 août notamment),
reconfirmé ici sur un nouveau cas concret. Résolu après redémarrage,
confirmé par David.

---

## ✅ 9bis. `articles_lies` + tags + institutions à spectre large (`priorite_forcee`, cooldown) — clos et testé en conditions réelles (22 août)
**Conçus ensemble le 21 août (soir)**, à la demande de David : `articles_lies`
(resté en jachère depuis la Phase B de P20) et le vocabulaire de tags
(point 11 initial) reposent sur le même mécanisme de fond — un
rapprochement entre articles par recoupement (entités partagées ET/OU
tags partagés). Un seul script plutôt que deux.

**`rapprocher_articles.py` (nouveau)** :
- Construit/rafraîchit `generator/tags_reference.yaml` (fréquence
  d'usage de chaque tag déjà vu dans `articles/*.md`).
- Calcule `articles_lies` par score pondéré (`3 × entités partagées + 1
  × tags partagés`, ratio acté avec David), restreint **strictement au
  même scénario** (les 6 scénarios sont des futurs alternatifs
  séparés — jamais de rapprochement cross-scénario). Top 3 retenus.
- Met à jour une ligne `**Voir aussi**` en wikilinks Obsidian
  (`[[slug]]`) en fin de corps de chaque article traité, combinant
  `entites_citees` + `articles_lies` — **découverte utile en cours de
  route** : la vue graphique native d'Obsidian suit les wikilinks du
  corps (jamais les listes de frontmatter, confirmé sur les fiches
  `entites/*.md` existantes), donc cette ligne suffit à rendre le
  corpus explorable visuellement dans Obsidian sans outil
  supplémentaire à construire.
- Mode `--stats` (diagnostic pur, aucune écriture) : fréquence des
  entités par scénario (pas en absolu — évite de fausser la
  comparaison entre scénarios de tailles différentes), alerte
  `QUASI-OMNIPRÉSENTE` au-delà de 40% des articles d'un scénario.

**`prompt_builder.py`** : la consigne `TAGS` charge et injecte les tags
déjà connus (`_load_tags_suggeres()`, plafonné à 50, triés par
fréquence), demande une réutilisation prioritaire — sans obligation,
le LLM reste libre d'inventer un tag pertinent absent de la liste.

**Testé intégralement sur corpus synthétique** avant tout usage réel
(rapprochement trouvé/absent, séparation stricte par scénario
confirmée, ligne "Voir aussi" combinée et idempotente sur relance,
`--stats` avec entité artificiellement omniprésente détectée à 100%).

**Lancé en dry-run sur le corpus complet (71 articles, tous scénarios,
après clôture du point 12)** : 262 tags distincts pour 357 usages
cumulés (réutilisation encore faible — attendu, tous ces tags ont été
écrits avant que la consigne de réutilisation existe, l'effet ne se
verra que sur les prochaines générations) ; 70/71 articles avec au
moins un lien trouvé, regroupements cohérents à l'examen (clusters
Genève-Nexus/gouvernance algorithmique, Amazonie/santé/longévité,
doublons quasi-identiques "Bruxelles-Forteresse" liés entre eux).
**Exécution réelle confirmée le 22 août.** `tags_reference.yaml`
présent sur disque (22 août, 10:47), et `articles_lies` vérifié rempli
avec des listes de slugs cohérentes sur plusieurs fiches `breakdown`
de dates différentes (`grep` direct sur le vault). Point définitivement
clos — aucune relance nécessaire.

**`gelecek_meclisi` : hypothèse d'hier soir INVALIDÉE par le vrai
volume.** Sur 71 articles, `breakdown` 30% et `policy_reform` 33% —
sous le seuil de 40% dans les deux cas. L'omniprésence à 100% observée
la veille sur 7 articles seulement était un artefact d'échantillon trop
petit, pas un signal réel. Validation nette de la décision de David
d'observer avant de corriger.

**Mais un nouveau constat de fond émerge du vrai volume — plus large
que ce qui était soupçonné.** Le même mécanisme structurel (spectre de
`variables_influencees`/`zone_systemique` large favorisant certaines
instances dans `filter_instances_for_thematique()`) touche
**plusieurs entités différentes, sur 5 des 6 scénarios** (seul
`new_sustainability` non concerné, mais lui-même faussé par un
échantillon d'1 seul article — voir bug ci-dessous) :
- `eco_communalism` : `consortium_africain_de_biotechnologies_sociales`
  (57%), `reseau_mnemos` (50%), `trame_mnemos_noeud_reseau` (50%)
- `fortress_world` : `bureau_gouvernance_algorithmique` (48%)
- `policy_reform` : `directive_kontinuum` (58%),
  `consortium_africain_de_biotechnologies_sociales` (50%),
  `leena_vainala` (42%), `reseau_des_auditeurs_algorithmiques_
  independants` (42%), `amara_diallo_nkosi` (42%), `prisme_global`
  (42%)
- `reference` : `reseau_mnemos` (62%), `directive_kontinuum` (46%)

**Point notable non exploré plus avant** : `leena_vainala` et
`amara_diallo_nkosi` sont des **personnes**, pas des institutions —
un type de récurrence différent (source/commentatrice citée souvent
dans les articles) de celui des institutions à spectre large. Chacune
n'est omniprésente que sur un seul scénario (`policy_reform`),
contrairement aux institutions ci-dessous qui le sont souvent sur
plusieurs scénarios à la fois — signal d'une cause racine distincte
(pool de personnages nommés trop restreint sur ce scénario ?
non vérifié). **Diagnostic non commencé, reste à faire.**

**Bug identifié dans `--stats`, non corrigé** : aucun seuil minimum
d'articles avant d'afficher l'alerte `QUASI-OMNIPRÉSENTE` — sur
`new_sustainability` (1 seul article exploitable), **toutes** ses
entités s'affichent mécaniquement à "100%", un artefact du calcul sur
un échantillon d'1, pas un vrai signal. À corriger (ex. ignorer les
scénarios avec moins de N articles) avant de tirer des conclusions sur
ce scénario précis.

### Diagnostic institutions à spectre large — chantier complet, clos le 22 août

**Diagnostic (matin)** mené sur les 3 institutions les plus
représentatives (`consortium_africain_de_biotechnologies_sociales`,
`reseau_mnemos`, `directive_kontinuum`) + `bureau_gouvernance_algorithmique`.

**Piste `zone_geographique`/`zone_systemique` vide — écartée.** Les 7
fiches instance inspectées ont ce champ vide à 100%, sans exception.
Vérifié dans le code (`loader.py`) : un ensemble vide donne une
intersection vide avec les zones de la thématique, donc contribution
nulle au score — **pas un bug, pas un avantage artificiel**.

**Cause confirmée : recoupement structurel sur des `variables_influencees`
génériques.** Les 4 institutions partagent presque toutes
`gouvernance_institutions`/`technologie_information`/
`organisation_territoires` — des variables pilotes sur la majorité des
thématiques du vault. Formule de score (`filter_instances_for_thematique()`) :
`(∩ variables_visibles) × 3 + (∩ variables_secondaires) × 1 +
(∩ zones) × 1 + impact_systemique_global × 0.5`. Ces institutions
décrochent un score élevé à quasiment chaque thématique, indépendamment
du scénario — `directive_kontinuum` cumule en plus
`impact_systemique_global: 5` (le max). La rotation à mémoire
(`_score_bucket`, tolérance 2.0) ne départage que des scores **proches** ;
une institution structurellement dominante n'est jamais concurrencée,
même mécanisme que `terminal_kharg_data_haven`/`gelecek_meclisi`
(15 août) mais confirmé ici sur un pattern plus large (4 institutions,
plusieurs scénarios simultanément pour certaines).

**Décision de David : le mécanisme de sélection doit atténuer la
domination répétée, y compris hors ex-aequo strict.**

**Première tentative — pénalité de score, CONÇUE PUIS INVALIDÉE PAR TEST
SYNTHÉTIQUE avant tout déploiement réel.** Principe initial : score
effectif décroissant avec le nombre d'usages cumulés, plafonné
(`USAGE_PENALTY_CAP`). Test synthétique reproduisant fidèlement le cas
réel (cluster de 5-6 institutions structurellement favorisées
*ensemble*, comme observé dans `policy_reform` — pas une seule
dominante isolée) : **échec total**, 20/20 sélections inchangées quel
que soit le plafond testé (jusqu'à 15, largement au-dessus de l'écart
réel de 5.5 points). **Cause identifiée** : deux instances sélectionnées
à la même fréquence accumulent la même pénalité — l'écart entre elles
ne bouge jamais, quelle que soit la fonction de pénalité choisie
(défaut mathématique du principe, pas un problème de calibration).
Piste abandonnée avant tout code livré au vault.

**Mécanisme retenu à la place — cooldown dur avec exemption de
dominance écrasante, CODÉ ET TESTÉ (synthétique + conditions réelles).**
Après `COOLDOWN_STREAK = 3` sélections consécutives pour un scénario
donné, une instance devient inéligible pendant `COOLDOWN_DURATION = 2`
apparitions suivantes — exclusion déterministe, indépendante du score
(donc insensible au défaut mathématique ci-dessus, puisqu'il ne compare
jamais les instances entre elles). **Exemption** (ajoutée après retour
de David sur le premier test) : une instance dont le score dépasse la
2e meilleure candidate du lot d'au moins `DOMINANCE_EXEMPTION_GAP = 10.0`
échappe entièrement au cooldown ce round-ci — calibré pour que l'écart
réel diagnostiqué (`directive_kontinuum`, ~5.5 points) **reste** soumis
au cooldown, tandis qu'une dominance vraiment écrasante (testé à 16
points d'écart) en soit exemptée. Cas limite testé à 9.9 points (juste
sous le seuil) : reste soumis, confirmant que la bascule se produit
précisément où attendu.

**Tests synthétiques (4 cas)** : cluster réel (`directive_kontinuum`
12/20 au lieu de 20/20 sans le mécanisme) ; dominance écrasante exemptée
(20/20 conservé) ; cas limite sous le seuil (12/20, comme le cluster) ;
non-régression sur un premier run sans historique (sélection identique
au comportement du 15 août).

**Testé en conditions réelles** (2 batches réels sur `policy_reform`,
thématique `actualites_a_la_une`, via GUI) : deux déclenchements réels
observés (`consortium_helios_policy_reform`, puis
`terminal_kharg_data_haven_policy_reform`), cycle complet confirmé
(déclenchement → cooldown actif → expiration → réintégration en
streak). `directive_kontinuum` nettement ralenti par rapport au
premier batch (+1 usage sur le 2e batch contre +3 sur le 1er).
`instance_usage.json` gagne deux nouvelles clés par scénario
(`streaks`, `cooldowns`) en plus de `instances` — structure additive,
aucun risque de casse.

**Fichier livré** : `loader.py` (`_select_least_used_instances()`
entièrement réécrite — pénalité de score retirée avant tout déploiement,
remplacée par le cooldown ; `_select_with_custom_guarantee()` élargie
pour la garantie `priorite_forcee`, voir ci-dessous).

**`instance_usage.json` de test restauré** à l'état pré-test pour
`policy_reform` en fin de session (28 instances, compteurs simples,
sans `streaks`/`cooldowns`) — les 5 autres scénarios n'ont jamais été
touchés par ce test.

### Nouveau mécanisme `priorite_forcee` — conçu, codé et testé de bout en bout le 22 août

**Demande de David** : pouvoir forcer délibérément la présence durable
d'une entité (institution/personne) dans les articles — cas d'usage
donné : un événement narratif majeur (ex. arrivée d'extraterrestres)
qui ferait d'une entité un acteur permanent qu'on veut voir cité
partout. **Scope confirmé avec David** : entité de type récurrent (pas
un événement ponctuel type `inject_custom_events.py`), portée **par
instance**, niveau de contrôle = garantie de **présence/citation**
(comme la garantie custom du 21 août), pas garantie de statut de sujet
principal.

**Conception retenue** — un seul mécanisme centralisé pour les deux
usages (édition d'entité existante + création) :
- Nouveau champ optionnel de frontmatter sur une instance :
  `priorite_forcee: true` (absent/`false` par défaut).
- `_select_with_custom_guarantee()` : condition du pool garanti élargie
  de `injection.type == "custom"` à
  `injection.type == "custom" or priorite_forcee == True`.
- `filter_instances_for_thematique()` : même élargissement sur la
  ligne qui empêche un score nul d'être écarté.
- Une instance `priorite_forcee` échappe automatiquement au cooldown
  d'usage (ne passe jamais par le circuit de rotation) — aucun conflit
  entre les deux mécanismes, aucun cas particulier codé pour ça.

**Nouveau script `set_priorite_forcee.py`** : patch chirurgical du
frontmatter (regex sur une seule clé, pas de réécriture complète,
aucun appel LLM), fonction `set_priorite_forcee(slug, value,
instances_dir=None)` réutilisable en CLI et importable. **Testé
unitairement sur la vraie fiche `directive_kontinuum_policy_reform`**
avant tout déploiement (5 cas : activation sur champ absent,
ré-activation idempotente sans doublon, désactivation propre, no-op sur
désactivation déjà à l'état par défaut, gestion d'erreur slug
inexistant) — intégrité du reste du frontmatter et du corps vérifiée
bit-à-bit à chaque cas.

**GUI — deux volets, tous deux testés en conditions réelles** :
1. **Création** (`create_entities_and_instances.py`) : nouveau champ
   `priorite_forcee` (checkbox) dans `config_fields` de `create_entities`,
   propagé via `process_custom_idea()` → `generate_instances_for_entity()`
   → appel à `set_priorite_forcee()` après chaque instance créée avec
   succès. **Testé en conditions réelles** : entité de test créée sur 6
   scénarios, 4 succès + 2 échecs (JSON malformé LLM, garde-fou
   `ancrage_reel` — deux mécanismes préexistants sans lien avec ce
   chantier, mon code ne s'est déclenché QUE sur les 4 succès, comme
   prévu). `validate.py` final : 0 erreur/0 avertissement sur 762
   instances.
2. **Édition d'instance existante** (nouvel outil GUI, aucun panneau
   équivalent trouvé dans `scripts_config.json` avant ce chantier —
   seulement de la création) : section `entites_nettoyage`, même
   famille qu'`undo_custom`/`fix_annee_debut_placeholder`. **Testé en
   conditions réelles dans les deux sens** (retrait puis réactivation
   sur la même instance) — confirmé par lecture directe du frontmatter
   après chaque opération.

**4 bugs GUI réels trouvés et corrigés en testant** (aucun n'existait
avant ce chantier, tous introduits par les nouvelles entrées ajoutées
aujourd'hui, tous corrigés le jour même) :
- Champ `priorite_forcee` de `create_entities` sans `"default"` explicite
  → premier choix de la liste (`true`) pré-sélectionné par défaut dans
  le GUI, risque de forcer involontairement toute nouvelle entité.
  Corrigé (`"default": "false"` ajouté).
- Entrée `set_priorite_forcee` : `"optional": false` utilisé au lieu de
  `"required": true` (la clé réellement lue par la validation
  pré-lancement dans `app.js`, `isFlagActive(opt.flag)`) — le GUI
  laissait lancer sans `--slug`, échec côté `argparse`. Corrigé sur les
  3 champs de l'entrée.
- `set_priorite_forcee.py` n'acceptait pas `--scenario` en argument
  (envoyé par le GUI pour filtrer la liste d'instances, mais jamais
  déclaré côté `argparse`) → `unrecognized arguments`. Corrigé
  (accepté, non utilisé fonctionnellement, le scénario est déjà encodé
  dans le slug d'instance).
- **Piège latent plus large trouvé en marge** (`app.js`,
  `loadSlugsForSelect()`) : contrairement à la version "chips"
  (`loadSlugsForChips()`, qui préserve les sélections actives au
  rechargement depuis le 2 août), la version `<select>` simple n'a
  jamais eu cet équivalent — un `slug_select` dépendant d'un scénario
  perdait silencieusement la sélection si l'utilisateur choisissait
  l'instance avant le scénario. Nouveau mécanisme opt-in
  `requires_scenario_selected` (dataset attribute) : désactive et
  affiche un placeholder explicite ("Choisis d'abord un scénario")
  tant qu'aucun scénario n'est choisi, empêchant la séquence
  problématique à la source. N'affecte aucun champ existant qui ne
  déclare pas ce flag (`undo_custom`, `fix_annee_debut_placeholder`,
  `zone_hint`) — comportement strictement inchangé pour eux, non
  retesté spécifiquement mais diff confiné et non-régression par
  construction (flag absent = ancien comportement).

**Fichiers livrés** : `set_priorite_forcee.py` (nouveau), `loader.py`,
`create_entities_and_instances.py`, `scripts_config.json`, `app.js`.

**Nettoyage de fin de session** : entité de test et ses instances
supprimées via `undo_custom.py --generalisation yes --execute` (par
David) ; articles de test supprimés (par David).

---

## ⚪ 10. P25 — Fiabilité de la signature journaliste dans le corps de l'article
**Nouveau, 21 août.** Découvert en marge du chantier P20 (Phase A) : le
nouveau champ `journaliste_slug` dépend de l'extraction de la signature
("Prénom Nom — Journal") depuis le corps de l'article généré — ce qui a
rendu visible pour la première fois un problème de fond préexistant
sur la consigne de signature du 10 août 2026 ("apparaît TOUJOURS"),
jusqu'ici jamais mesuré faute d'un mécanisme qui en dépendait.

**Mesuré sur 2 batches réels de 8 articles (`fortress_world`), avant et
après renforcement de la consigne** ("TOUJOURS, SANS EXCEPTION..." ajoutée
aux contraintes impératives, même traitement que la longueur le 10 août) :
taux de signature manquante inchangé, environ 25% (2/8 puis 2/8) — le
renforcement n'a pas suffi. Un troisième symptôme apparu au 2e batch,
absent du premier : signature présente mais mal positionnée (fin
d'article plutôt qu'immédiatement sous la date), avec un format à 3
parties inattendu ("Nom — Organisation — Journal") au lieu du format à
2 parties attendu.

**Réévalué le 21 août (soir)** sur un nouveau batch réel généré depuis
le GUI (3 articles, `policy_reform`, série) : 1/3 signature correcte,
1/3 signature repoussée en fin d'article **précédée d'un séparateur
`---`** (nouveau détail — pas juste "en fin d'article" comme observé
plus tôt, mais littéralement présentée comme une note de bas de page
après une ligne horizontale, positionnée après l'article complet), 1/3
sans aucune signature du tout. Cohérent avec le taux déjà mesuré
(~25-33% d'échec), le pattern `---` avant signature est une piste
concrète utile pour un futur diagnostic — pourrait indiquer que le LLM
traite parfois la consigne de signature comme une note de fin plutôt
qu'un en-tête, malgré la position imposée par la consigne.

**Décision inchangée (comme P17/Bug#27)** : observer sur un futur batch
de volume avant de sur-corriger — l'échantillon cumulé reste petit
(16 puis 19 articles), et température 1.0 (forte variance) rend un
seul renforcement de consigne peu concluant sur si peu de données.
`_extract_byline()` (`api.py`) reste volontairement limité aux 8
premières lignes de l'article (évite les faux positifs sur un tiret
cadratin en dialogue/citation) — pas élargi pour chasser le cas
"signature en fin d'article", qui relève d'abord d'un problème de
consigne, pas d'extraction. Nouvelle piste pour la prochaine session,
si le taux se confirme : détecter spécifiquement le pattern `---` en
fin de texte et y chercher la signature en repli, sans élargir la
recherche à tout le corps (garderait le risque de faux positif sous
contrôle).

### Batch de volume réalisé le 22 août — résultat net, hypothèse de couverture réfutée, piste architecturale identifiée

**2 batches indépendants sur `new_sustainability`** (série, GUI),
21 puis 20 articles : **41/41 avec `journaliste_slug` rempli — 0%
d'échec**, contre ~25-33% mesuré sur `fortress_world`/`policy_reform`
le 21 août. Écart statistiquement significatif (probabilité d'obtenir
0/21 par hasard si le taux réel était toujours ~25% : environ 0,2%).
**Format vérifié manuellement sur 4 articles** (frontmatter + corps) :
conformité totale, 2 parties "Nom — Journal", position correcte sous
la date, aucune trace du pattern `---`/fin d'article observé le 21
août.

**Hypothèse testée : écart dû à la couverture de `journaux.yaml`
(certaines zones sans liste de journalistes curatée, forçant le LLM à
en inventer un) — RÉFUTÉE.** Vérification directe de `journaux.yaml` :
couverture à **100%**, chaque zone de chaque scénario (`new_sustainability`,
`fortress_world`, `policy_reform`) a exactement 6 journalistes
configurés. Le chemin 1 (`get_journal_profile()`, nom curaté, LLM
instruit avec un nom exact) s'applique donc partout, sans exception —
**la cause de l'écart scénario-dépendant reste non expliquée**, piste
la plus probable actuellement : simple variance d'échantillon (batches
du 21 août à 8 et 3 articles seulement, contre 41 aujourd'hui).

**Découverte architecturale indépendante, plus importante que l'écart
lui-même** (retour de David : "l'auteur et la date peuvent-ils être
gérés à l'édition plutôt qu'à la génération ?") : `journaliste_slug`
est aujourd'hui **entièrement dérivé par extraction** du texte généré
(`_extract_byline()`, `api.py`, ligne ~577) — alors que dans 100% des
cas mesurés, le nom du journaliste est **déjà connu par le code avant
l'appel au LLM** (`profile["journaliste"]`, `get_journal_profile()`,
`prompt_builder.py`). Le code redemande donc systématiquement une
information qu'il connaît déjà, en la faisant dépendre inutilement de
la fiabilité du LLM à la retranscrire correctement dans le texte — la
vraie racine de la fragilité de P25, indépendante du taux d'échec
scénario-dépendant. `date_publication` n'a pas ce problème : déjà
100% déterministe depuis le 21 août (P20 Phase B).

**Proposition non codée, à traiter en session dédiée** : assigner
`journaliste_slug` directement depuis `profile["journaliste"]` au
moment de la construction du prompt (avant génération), au lieu de
l'extraction post-génération. Rendrait le frontmatter fiable à 100% —
indépendamment de ce que le LLM écrit réellement dans le corps — et
permettrait au site web d'afficher auteur + date depuis les champs
structurés seuls, sans dépendre de la signature textuelle. La
signature *dans le texte* pourrait continuer d'exister (lisibilité
Obsidian) mais deviendrait cosmétique plutôt que fonctionnelle si elle
est parfois absente/mal placée. Nécessite de vérifier si un chemin
2/3 (LLM invente un nom) peut réellement se produire ailleurs dans le
vault avant de supprimer l'extraction en repli.

---

## ✅ 13. Uniformisation du dossier de sortie `generate.py` — clos (22 août)
**Signalé par David** : les articles générés en mode unitaire
(`generate.py`, pas en série) atterrissaient toujours à la racine
`articles/`, contrairement aux séries (`articles/{scenario}/`, corrigé
le 10 août). **Diagnostic** : confirmé dans le code, pas un bug — un
run `generate.py` seul ne définissait jamais
`config["output"]["dossier"]`, contrairement à `generate_series.py`/
`generate_manual.py`. Comportement tel que conçu le 10 août (le
correctif ne visait que les séries), jamais explicité comme un choix
conscient. **Décision de David : uniformiser** — `generate.py` doit
aussi ranger dans `articles/{scenario}`, même pour un article isolé.

**Corrigé** dans `_generate_one()` (`generate.py`), fonction déjà
factorisée pour les deux modes (simple ET "forcer") — un seul point de
code couvre les deux. `article_config["output"]["dossier"]` fixé à
`"articles/{scenario_slug}"` avant l'appel à `build_prompt()`/
`generate_article()`. Pas de sous-dossier séparé ni d'`_index.md` créé
(ça reste spécifique aux séries) — juste le rangement.

**Non-régression vérifiée sur les deux outils qui scannent `articles/`**
(`trace_injection.py`, `audit_longueur_articles.py`) : les deux étaient
déjà rendus récursifs le 10 août pour ce cas exact, et extraient le
scénario depuis le frontmatter (pas depuis le chemin) — aucune
modification nécessaire, confirmé par lecture directe des deux
fichiers. Diff confiné à une seule zone dans `generate.py`, syntaxe
vérifiée.

**Fichier livré** : `generate.py`.

---

## ⚪ 14. `chapo`/`tags`/`image_prompt` vides — bloc `===METADONNEES_PUBLICATION===` absent de la réponse LLM (~7% des cas)
**Découvert en marge du batch de volume P25** (22 août, via un warning
console : `[api] [WARN] Bloc ===METADONNEES_PUBLICATION=== absent de
la réponse du LLM`). **Mesuré** : 3 articles sur 41 (~7%), dont 2 sur
la même thématique (`religion_spiritualite`) — possible coïncidence
sur un petit échantillon, possible signal (thématique générant des
réponses plus longues/complexes ?), pas assez de données pour trancher.

Le garde-fou de P20 Phase A fonctionne comme prévu (pas de plantage,
champs laissés vides) — mais **aucun mécanisme de retry n'existe pour
ce cas**, contrairement à la longueur (retry automatique depuis le 10
août). Diagnostic et éventuelle correction (retry ciblé sur ce bloc
précis ?) laissés pour une prochaine session.

---

---

## ✅ 12. Rétro-application sur les articles déjà existants — clos
**Ouvert le 21 août (soir), clos le 21 août (soir également)** — chantier
mené intégralement dans la foulée de son ouverture, sans report au
lendemain contrairement à ce qui était anticipé.

**`enrich_articles_pre_p20.py` (nouveau script)**, trois niveaux de
récupération sur les articles sans `slug` (marqueur "pré-P20") :
1. **Mécanique** (sans LLM) : `slug`/`journaliste_slug`/`date_evenement`
   /`date_publication`, réutilisant les fonctions déjà testées d'`api.py`.
2. **Approximation** (sans LLM, décision explicite de David plutôt que
   laisser vide) : `entites_citees`/`zone_principale` par recoupement du
   texte contre le nom des entités connues du scénario (vote majoritaire
   sur leur zone) — limite assumée et testée (une entité citée pour dire
   qu'elle n'est *pas* concernée est quand même détectée, la
   correspondance texte ne comprend pas la négation).
3. **LLM** (un seul appel par article, réutilise le format
   `===METADONNEES_PUBLICATION===` et `_extract_publication_metadata()`
   d'`api.py` sans dupliquer le parsing) : `chapo`/`tags`/`image_prompt`,
   plus un **4ᵉ champ ajouté en cours de route**, `JOURNALISTE` — le LLM
   lit l'article complet et tranche lui-même si la signature captée est
   une vraie personne ou un nom d'institution/lieu (ex. réel rencontré :
   "Bratislava Secteur Alpha" confondu avec un nom de journaliste par le
   regex mécanique) — problème de sens, pas de motif, donc résolu par le
   bon outil plutôt que par une nouvelle heuristique. Coût marginal nul,
   l'appel est de toute façon déjà fait pour les 3 autres champs.

**Bugs réels trouvés et corrigés en route** (tous testés avant
d'affecter le run réel) :
- Slugs dupliqués (`_extract_title()` retombe parfois sur une ligne de
  repli non unique) → désambiguïsation par suffixe numérique, unicité
  garantie y compris contre les articles déjà P20.
- Préfixe "Par"/"By" capturé avec le nom de journaliste → retiré avant
  slugification.
- Regex interne de `_extract_publication_metadata()` sensible à la
  casse (`CHAPO:` strict) → passé en `re.IGNORECASE`, **correctif
  partagé avec la génération live** (pas seulement ce script).
- Piège identifié avant qu'il ne se produise : lancer `--skip-llm` pour
  de vrai (sans `--dry-run`) aurait posé un `slug` sur chaque article
  traité, les excluant ensuite définitivement d'un futur passage
  complet avant que `chapo`/`tags`/`image_prompt` soient jamais
  remplis → combinaison refusée activement par le script (erreur
  explicite), pas juste déconseillée en commentaire.
- Regex de date trop stricte (exigeait que la ligne entière soit *juste*
  la date) → élargi en deux temps : tolérance gras/italique autour,
  puis recherche du motif *dans* la ligne plutôt que sur la ligne
  entière (découvert sur le tout premier format du projet, juin 2026 :
  date combinée au lieu sur une même ligne, "Bratislava-Secteur Alpha —
  9 novembre 2098").

**Exécution réelle complète** : 56/56 articles pré-P20 traités
(3 avertissements initiaux — bloc métadonnées vide, retentés avec
succès ensuite). Mode `--audit` ajouté après coup (diagnostic pur :
rangement racine/sous-dossier, dates vides, chapo vides), qui a révélé
un problème hors scope initial mais découvert dans la foulée :

**Découverte annexe — rangement incohérent du corpus historique.** 44
des 56 articles étaient posés directement à la racine de `articles/`
plutôt que dans leur sous-dossier par scénario (convention différente
avant un certain point — `config["output"]["dossier"]` ne pointait pas
toujours vers un sous-dossier). `rapprocher_articles.py` ET
`enrich_articles_pre_p20.py` ne balayaient jusque-là que les
sous-dossiers, ratant silencieusement ces 44 fichiers — corrigé dans
les deux scripts (balaient désormais racine + sous-dossiers, scénario
lu depuis le frontmatter plutôt que déduit de l'emplacement du
fichier). Nouveau mode `--reorganize` ajouté à `enrich_articles_pre_p20.py`
pour déplacer les fichiers mal rangés — lancé en réel, 44/44 déplacés
sans collision.

**Deux nouveaux modes de rattrapage ciblé ajoutés** après l'audit, pour
ne retraiter que ce qui manquait sans retoucher les champs déjà bons :
`--retry-empty-date` (mécanique, gratuit — 26/29 dates récupérées après
l'élargissement du regex) et `--retry-empty-chapo` (LLM, 3/3 récupérés
après le correctif de casse).

**3 dates résiduelles irrécupérables mécaniquement**, diagnostiquées
une par une :
- Année tronquée à 3 chiffres dans le texte lui-même ("298" au lieu de
  "2098", coquille de génération de juillet) — David corrige à la main
  plutôt que deviner automatiquement.
- Date en portugais ("12 de novembro de 2098") — format supplémentaire
  non couvert, un seul article concerné, pas codé (rapport coût/
  bénéfice jugé trop faible pour un seul cas).
- Calendrier fictif propre à la narration d'un article ("Le 14 de
  l'Eau Profonde, 2098") — pas une vraie date, aucun regex ne peut la
  interpréter. 2 des 3 cas corrigés à la main par David en cours de
  route, 1 laissé vide (calendrier fictif, pas de correspondance
  réelle possible).

**Découverte annexe supplémentaire, sans lien avec ce chantier** : sur
au moins un article (`lynth_lieu_encommande`), la date écrite dans le
corps par le LLM (14 novembre 2098) ne correspond pas à la date
demandée à la génération, visible dans le nom de fichier (3 janvier
2098) — écart préexistant de juillet, invisible jusqu'ici faute d'un
champ qui en dépendait. Décision : la date extraite du texte fait foi
pour `date_evenement` (c'est ce que le lecteur voit réellement), pas
celle du nom de fichier (simple horodatage technique de génération).

**Audit final** : 0 fichier à la racine, 1 date vide (le cas calendrier
fictif, accepté), 0 chapo vide. Chantier considéré clos.

**Décision de fond actée en cours de route** : face à la question "ne
vaudrait-il pas mieux supprimer et régénérer tout le corpus pré-P20
plutôt que le rattraper", David a choisi de conserver le rattrapage —
la régénération remplacerait les récits déjà écrits par des articles
différents (coût de régénération bien supérieur, et aucune garantie de
"rattraper" au sens propre), alors que le rattrapage préserve le
contenu existant en ne touchant qu'aux métadonnées.

---

## ⚪ 7. Chantiers de fond, scopés mais non codés (pause longue durée)
- **P21 — journaux oraux, orateurs itinérants** : scoping complet fait
  (12 juillet), rien codé. Nouveau type d'entité `orateur` (Option B
  décidée), champ `type_diffusion`, registre oral distinct dans
  `prompt_builder.py`.
- **P14 — tier LLM `strict` vers `claude-sonnet-5` en prod** : différé
  sine die sur demande explicite de David (1er août). Pas un oubli, une
  décision — à reconsidérer seulement si David le redemande.

---

# PARTIE 2 — POINTS MINEURS, NON BLOQUANTS (sans action requise)

**Nettoyé le 19 août** — retrait des points reconfirmés à plusieurs
reprises sans jamais avoir mené à une action (aucune condition de
réouverture identifiée) : anomalie `coverage_proposals_reference.yaml`
sans `.applied`, route dormante `/api/carte/appliquer_zone_topdown_suspecte`,
champ `type` des zones géographiques jamais utilisé dans le prompt.
`constrained_variables` retiré de cette liste pour la raison inverse —
traité et résolu, voir Partie 4. Bloc `simulation` retiré également,
pour la même raison inverse — P22 a confirmé et résolu son statut le
20 août (câblé dans `snapshot.py`, opérationnel), voir Partie 4.

- `--min-shingle` de `detect_registre_leakage()` (fonction désormais
  partagée, voir Partie 4) fixé en dur à 6 mots — pourrait devenir un
  paramètre CLI si un faux positif/négatif apparaît en usage réel.
- Cas d'échec LLM ponctuel observé une fois (4 août) : confusion entre
  un slug de zone géographique et un slug d'instance sur une fiche —
  résolu par retry, gardé en tête comme motif à surveiller si le même
  symptôme réapparaît (pourrait indiquer que le prompt gagnerait à
  lister explicitement les slugs de zones à ne PAS utiliser).
- **Nouveau, 15 août** : `articles/{scenario}/_index.md`, généré par
  `generate_series.py` (`build_index()`), est réécrit en mode écrasement
  à chaque run sur un même scénario — ne liste que les articles du
  dernier batch, pas un cumul historique de tous les articles jamais
  générés pour ce scénario. Repéré en discussion, pas vérifié comme
  gênant en pratique. À réévaluer si un historique cumulatif devient
  utile (ex. navigation Obsidian sur l'ensemble d'un scénario plutôt
  que sur le dernier batch seul).

---

# PARTIE 3 — RISQUE STRUCTUREL IDENTIFIÉ (pas un bug actif)

**Aucun point actif.** Le seul risque identifié ici (instances custom
potentiellement non sélectionnées dans `filtered_instances`, depuis le
3 août) a été corrigé le 21 août — voir Partie 4, chantier "Garantie
d'inclusion des instances custom (`loader.py`)".

---

# PARTIE 4 — CHANTIERS CLOS (référence historique — ne pas rouvrir sans raison)

Regroupés par nom de chantier stable, avec date de clôture, pour éviter
qu'une future session ne les rouvre par erreur faute de contexte.

| Chantier | Clos le | Résumé |
|---|---|---|
| **P8 — 426 fiches `officialise_minimal`** | 27 juin | Traité intégralement, preuve dans les fiches elles-mêmes. |
| **`noeud_mnemos_pannonie`** | 14 juillet | P23, absorbé par `check_origine_reelle_coherence.py`. |
| **P18 — cohérence `routes_dashboard.py`** | 13 juillet | — |
| **P24 étape C** | 1er août | Absorbé par `chantiers_geographie.yaml`. |
| **Onglet GUI "Chantiers"** | 26 juillet → 1er août | Livré et testé en réel ; granularité "appliquer un seul chantier" ajoutée le 1er août. |
| **Bug dashboard (entrée fantôme instances)** | 2 août | `instance_template.md` compté à tort comme 711e instance — corrigé. |
| **Panneau Revue vide** | 2 août | Deux causes cumulées corrigées (`sort_keys=False`, sources `entites_custom`/`signaux_custom` jamais lues). |
| **`trace_injection.py`** | 2 août | Nouvel outil de traçabilité, livré et testé en réel. |
| **Mode "Forcer un élément"** | 2 août | Refonte majeure de `generate.py`, 7 bugs trouvés et corrigés en conditions réelles. |
| **Plafonnement événements/géographie** | 3 août | Testé en conditions réelles, 2 bugs annexes corrigés (badge `[FORCÉ]`, zone manquante). |
| **Revalidation mode Semi-guidé** | 3 août | Les 7 champs du bug §3.7 confirmés appliqués ; bug annexe `metadata["longueur"]` trouvé (→ a mené au chantier "Dérive du LLM sur la longueur réelle des articles" ci-dessous, clos le 10 août). |
| **Audit de complétude snapshot/variables** | 3 août | 4 pertes de contenu narratif trouvées et corrigées. |
| **Test de charge Semi-guidé à 6 entités** | 4 août | 58 948 caractères mesurés, structurellement borné. A débouché sur le chantier alliances/oppositions ci-dessous. |
| **Chantier alliances/oppositions** | 4-5 août | 356→0 fiche vide sur 426, réciprocité automatisée, root cause corrigée à la source (`enrich_minimal.py`), validation durcie partiellement, découverte et correction annexe de 284 fiches sans `statut` (vault à 710/710 cohérent). |
| **146 conflits de réciprocité alliances/oppositions** | 7 août | Règle "opposition prioritaire" implémentée et appliquée, 2 bugs découverts et corrigés (écrasement multi-conflits, rapports jamais réinitialisés), intégrée en continu à `enrich_minimal.py`, GUI mis à jour. |
| **`fix_alliances_oppositions.py` absent du GUI** | 7 août | Résolu par l'intégration GUI du chantier ci-dessus. |
| **Documentation `depends_on`** | 8 août | Fausse alerte — vérifié en détail, le mécanisme était déjà correctement décrit. Rien à corriger. |
| **Chantier `annee_debut`** | 8 août | 477 fiches bloquées à 2026 corrigées, outil de veille construit (`etat_du_monde_reel.md` + export/import), chantier de robustesse `ancrage_reel` mené en parallèle (bande graduée 10 ans), run `--all` confirmé par un passage à vide. |
| **`ancrage_reel` / traçabilité graduée** | 8 août | Ouvert et refermé dans la même session, 5 itérations de test réel. |
| **Statut de `generate_instances.py`** | 9 août | Confirmé **actif**, usage distinct de `create_entities_and_instances.py` (backfill vs création). Voir Partie 1 point 3 (documentation à corriger dans le manuel) pour le suivi resté ouvert. |
| **Factorisation `instance_generation_common.py`** | 9 août | ~20 fonctions dupliquées entre `generate_instances.py` et `create_entities_and_instances.py` unifiées en un seul module. 3 bugs de divergence réels corrigés au passage (`call_claude_json`, `validate_instance`, `MAX_TOKENS`). Détail complet : `USER_MANUAL_COMPLET.md` §1. |
| **Chantier `trajectoire`** | 9 août | Fusion `etat_temporel`+`age_historique` en un axe unique + `est_clandestin` séparé. 710 fiches migrées via `migrate_trajectoire.py` (nouveau script, mécanique, aucun appel LLM), `validate.py` recalibré (bug C4 corrigé au passage), GUI mis à jour (menu `État`/`Clandestin` dans `create_entities`), `audit_etat_temporel_fin.py` adapté. Détail complet : `USER_MANUAL_COMPLET.md` §3bis. |
| **Chantier `annee_fin`** | 9 août | 28 fiches à trajectoire terminale sans date de fin corrigées (`fix_annee_fin_manquant.py`, nouveau script, ancré sur le registre du scénario). 27/28 directement, 1 cas résistant résolu par renforcement du prompt + filet de sécurité de plafonnement automatique ajouté au script. Concentration sur 2041/2061/2057 vérifiée légitime (jalons de rupture réels du registre, pas une convergence artificielle). Vérifié par `audit_etat_temporel_fin.py` (0% d'incohérence) et `validate.py` (0 erreur). |
| **Décision `type_relation_dominante`** | 9 août | Fausse alerte — en réalité déjà décidé et implémenté le 7 août (`prompt_builder.py`, `build_entities_context()`), jamais retiré du backlog dans les sessions suivantes. Affiché en ligne dédiée par entité avec période (`annee_debut`–`annee_fin`) ; garde-fou anti-fabrication confirmé suffisant (consigne générale "ne les contredis pas" du bloc entités, pas de mécanisme dédié nécessaire). |
| **`metadata["longueur"]` réutilisé en aval ?** | 9 août | Vérifié : oui, écrit de façon permanente dans le frontmatter par `api.py` ET `generate_manual.py` (traçabilité), mais jamais relu par aucun script (`trace_injection.py` lit `scenario`/`date_publication`/`titre`, jamais `longueur`) — impact purement cosmétique. **Correction rétroactive abandonnée** : la reconstruction resterait ambiguë (catégories `FORMAT_LONGUEUR` qui se chevauchent) et rien en aval n'en dépend fonctionnellement. Nouvel outil créé pour mesurer sans corriger : `audit_longueur_articles.py` (lecture seule, section GUI Validation) — 3 itérations en session pour arriver à un diagnostic fiable (v1 : bug de correspondance catégorie/plage, 100% faux positifs ; v2 : parsing direct de la plage textuelle, 64,5% mais mélangeait deux causes différentes ; v3 : distingue Cas A [vrai signal] de Cas B [divergence format/longueur]) — chiffre final fiable : **70,4% (19/27 analysables)**, a mené au chantier "Dérive du LLM sur la longueur réelle des articles" ci-dessous. |
| **Bug d'accent `FORMAT_LONGUEUR` (`brève`/`éditorial`/`réflexif`)** | 9 août | Trouvé en creusant le point ci-dessus (les 4 articles `format: brève` retombaient tous sur le filet de secours générique "300 à 500 mots" au lieu de leur vraie plage "200 à 400 mots"). Cause : `FORMAT_LONGUEUR` (`prompt_builder.py`) ne couvrait que les orthographes sans accent, alors que `VALID_FORMATS` (`validate.py`) accepte explicitement les deux orthographes pour `breve`/`brève`, `editorial`/`éditorial`, `reflexif`/`réflexif`. Corrigé : les 3 variantes accentuées ajoutées à `FORMAT_LONGUEUR`, un seul dict module-level donc correctif appliqué aux deux points d'usage (`build_journalistic_brief()`, `build_prompt()`) automatiquement. Vérifié fonctionnellement (les 3 nouvelles clés mappent bien vers la même plage que leur équivalent sans accent). Aucune correction rétroactive des articles déjà publiés avec ce défaut (même décision que le point ci-dessus — cosmétique, non consommé en aval). |
| **Dérive du LLM sur la longueur réelle des articles** | 10 août | Diagnostic complet : consigne de longueur isolée dans le prompt, jamais reprise dans le bloc final avant génération, aucune validation post-génération. Renforcement du prompt seul testé **insuffisant** (94,4% d'incohérence sur un batch isolé, pire que la référence du 9 août, biais net vers le dépassement) — mécanisme de retry automatique ajouté à la place : écart > 40% de la borne dépassée → un seul essai supplémentaire, avec rappel chiffré de l'écart mesuré (pas de boucle, résultat du 2e essai accepté quoi qu'il arrive). Nouveaux champs frontmatter `mots_reels`/`retry_longueur` pour la traçabilité. **Testé en conditions réelles sur 12 articles** : 3 retries déclenchés, tous améliorés ; aucun faux négatif sur les 9 non retentés. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. Validation à plus grande échelle en suivi : Partie 1 point 1. |
| **Date fictive jamais transmise au LLM** | 10 août | La date calculée par `generate.py`/`generate_series.py` pour espacer une série ne servait qu'au nom de fichier, jamais envoyée au LLM (consigne "une date crédible en 2098", totalement libre) — d'où la convergence observée vers une date quasi unique sur plusieurs articles, et l'incohérence systématique entre date du nom de fichier et date affichée dans l'article. Corrigé dans `prompt_builder.py` (`build_journalistic_brief()`) : la date est transmise explicitement, avec instruction de la reprendre telle quelle. Testé en conditions réelles : 12/12 articles cohérents. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Signature absente ou incohérente (2 itérations)** | 10 août, itération 2 validée le 12 août | Root cause : `get_journal_profile()` ne peuple le nom de journaliste curaté que sur 1 des 3 chemins de résolution du profil éditorial — sur les 2 autres, l'instruction de signature était purement absente du prompt, laissant le LLM libre de signer ou non. Itération 1 : signature toujours instruite, format unifié "Nom — Journal". Testé en conditions réelles : 12/12 articles signés (contre présence aléatoire avant), mais position incohérente (haut/bas) et 1 doublon trouvés. Itération 2 (même jour, après clarification des usages réels de la presse en ligne) : position fixée en haut sous la date, "une seule fois" renforcé en interdiction stricte de répétition. **Validée en conditions réelles le 12 août** : un run `generate.py` avec une zone valide (`geneve_bunker_institutions`, débloqué par le correctif `zones_hier_journal` du 11 août soir) a confirmé une signature unique, toujours immédiatement sous la date. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Accent supprimé dans le nom de fichier (`fvrier` au lieu de `février`)** | 10 août | `build_article_filename()` (`api.py`) : la regex de nettoyage du slug de date ne reconnaissait que les lettres non accentuées, supprimant silencieusement tout accent au lieu de le translittérer. Corrigé via `unicodedata.normalize()` avant filtrage. Testé en conditions réelles sur 12 articles : confirmé corrigé. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Dossier de sortie des articles de série ignoré** | 10 août | `save_article()` (`api.py`) écrivait toujours à la racine de `articles/`, sans jamais lire `config["output"]["dossier"]` — `generate_series.py`/`generate_manual.py` construisaient pourtant ce chemin et y écrivaient leur `_index.md`, orphelin des articles qu'il indexe. Corrigé : `save_article()` lit désormais ce champ. Vérifié sur les 3 cas de figure (série, unité, config sans bloc `output`). Testé en conditions réelles : les 12 articles du batch de test se sont bien retrouvés dans `articles/policy_reform/`. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Scan non récursif de `trace_injection.py`/`audit_longueur_articles.py`** | 10 août | Effet de bord du correctif précédent : ces deux outils scannaient `articles/` à plat (`os.listdir`/`glob` non récursif) — sans correction, ils seraient devenus aveugles à tout article généré en série/manuel une fois rangé en sous-dossier. Corrigés en scan récursif (`os.walk` / `glob("**/*.md")`), `_index.md` explicitement ignoré par l'audit. `audit_longueur_articles.py` testé en conditions réelles (43 fichiers retrouvés, racine + sous-dossier). `trace_injection.py` testé en isolation seulement, pas en conditions réelles. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Gap de documentation — `state/event_relevance_usage.json` absent de l'inventaire** | 10 août | Pas un bug : mécanisme de rotation à mémoire des événements custom existant depuis le 2 août (`loader.py`, `select_relevant_events()`), simplement jamais documenté dans `USER_MANUAL_COMPLET.md` ni intégré au protocole de nettoyage post-test. Découvert en nettoyant un test de génération réelle (fichier non suivi par Git, donc non restauré par `git checkout`). Manuel et protocole de test corrigés en conséquence (§0, §2, §2ter). |
| **Clarté des descriptifs GUI + sortie `trace_injection.py`** | 11 août (matin) | David a commencé la validation navigateur du GUI, signalant au fil du test 3 descriptifs jugés trop techniques : `fix_annee_debut_placeholder` (descriptif principal), `trace_injection` (descriptif principal), `fix_alliances_oppositions` (descriptif principal + 7 options + 2 libellés de rapports) — tous reformulés en retirant le jargon d'implémentation (chemins de fichiers bruts, "passe LLM", "rétroactif" sans explication) tout en conservant le vocabulaire propre au projet (variables, scénarios, entités, alliances). Correctif de lisibilité appliqué en plus directement à la sortie de `trace_injection.py` (`_rendre_markdown()`) suite à un exemple réel fourni par David : type technique brut remplacé par un libellé lisible, statut d'origine reformulé, échelle d'impact explicite, listes d'alliances/oppositions enfin lisibles (suffixe de scénario retiré quand non ambigu, snake_case converti en texte normal). **10 entrées validées en conditions réelles et marquées `gui_verified: true`** : les 4 audits, les 2 entrées de veille, `trace_injection`, `fix_annee_debut_placeholder`, `fix_alliances_oppositions`, `generate`. Détail complet : `USER_MANUAL_COMPLET.md` §7 (addendum du 11 août) et §2. |
| **Clarté suite des descriptifs GUI (11 août, session soir)** | 11 août (soir) | Revue systématique des 28 entrées de `scripts_config.json` pour repérer le jargon d'implémentation restant, au-delà des 3 déjà traitées le matin. **17 changements appliqués** : 8 descriptifs principaux (`enrich_minimal`, `zoning_topdown_test`, `reparenter_sous_zones_orphelines`, `scan_geographie_complet`, `audit_dates_instances`, `audit_etat_temporel_fin`, `audit_longueur_articles`, `audit_type_relation_dominante` — retrait de notes de développeur datées, de noms de fichiers internes type `frontmatter`/`loader.py`, d'historique de bugs non pertinent pour l'utilisateur) + 9 changements au niveau des options (dev-log daté retiré sur `--forcer-scenarios`/`--ancrage-temporel` ×2, nom de fichier brut retiré sur `--update`/`--slug` (undo_custom), jargon "N1"/"cache"/"additif" clarifié, libellés de choix techniques bruts d'`undo_custom --type` rendus lisibles). Vérifié par diff programmatique à chaque étape : 14 entrées touchées au total, aucune autre altérée. |
| **Test navigateur des entrées GUI modifiées** | 11 août (soir) | **Chantier définitivement clos.** Les 3 dernières entrées (`create_entities`, `enrich_minimal`, `generate_instances`) testées en conditions réelles. `create_entities` : cycle complet testé (auto-suggest → custom → cycle post-injection), 2 bugs de code réels trouvés et corrigés en cours de route (voir lignes dédiées ci-dessous). `enrich_minimal` : testé, résultat vide (0 fiche `officialise_minimal` restante) — cohérent avec le chantier P8 clos depuis le 27 juin, comportement attendu. `generate_instances` : exercé comme dépendance du cycle post-injection du test `create_entities` (pas cliqué directement via son propre bouton GUI, mais comportement du script confirmé fonctionnel en conditions réelles). Les 28 entrées du panneau GUI sont désormais **toutes** `gui_verified: true`. Détail des bugs trouvés en testant : voir les 5 lignes suivantes de ce tableau. |
| **Crash EOFError en création d'entités (mode auto-suggest/auto, GUI)** | 11 août (soir) | En testant `create_entities` (mode auto-suggest) depuis le GUI : `EOFError: EOF when reading a line` sur un `input()` non protégé dans `run_auto_suggest_mode()` (`create_entities_and_instances.py`) — même bug que celui corrigé le 11 juillet sur `--mode`, jamais étendu aux deux sous-questions de ce mode (nombre d'idées, scénario ciblé) ni à celles du mode `auto` (nombre d'entités, catégorie imposée). **4 `input()` protégés** par `sys.stdin.isatty()` : hors terminal interactif (GUI/cron), retombe directement sur la valeur par défaut déjà prévue dans le code plutôt que de planter. **Bug de type corrigé au passage** : `scenario_filter` était traité comme une chaîne simple dans le repli interactif, alors que tout le reste du script (`step_auto_suggest_entities`, `args.scenario` en `nargs="+"`) le traite comme une liste — un scénario tapé en CLI pur aurait été itéré caractère par caractère. Corrigé (`scenario_filter = [scenario_raw]`). Testé en conditions réelles : mode auto-suggest relancé après correctif, plus de crash, 5 idées générées avec succès. |
| **Silence sur rejet `category`/`scenario_ref` invalide (mode custom)** | 11 août (soir) | Trouvé en traitant la queue générée par le test ci-dessus : une entité ("Les Veilleurs des Nappes Phréatiques") disparaissait du log sans aucun message après son en-tête `=== Nom ===`, alors que `needs_review.yaml` contenait bien la raison (`category invalide : 'mouvement'`, hallucination du LLM auto-suggest malgré la contrainte de prompt). Cause : `process_custom_idea()` retournait directement sur ces deux rejets précoces sans jamais imprimer, contrairement à tous les autres cas d'échec de la fonction (archétype, instance) qui affichent toujours leur motif. Corrigé : `print(f"  ✗ Rejetée : {reason}")` ajouté sur les deux cas (`category`, `scenario_ref`). |
| **`queue.yaml` écrasé par un panneau caché (`saveOpenConfigForms`, GUI)** | 11 août (soir) | Un run `create_entities` en mode auto-suggest avait bien écrit 5 idées dans `entites_custom/queue.yaml` (confirmé par le log), mais le fichier était retrouvé vide juste après. Cause : `saveOpenConfigForms()` (`app.js`, ajoutée le 31 juillet pour un autre bug) sauvegarde tout panneau `.yaml-form-panel` présent dans `#form-body` avant de lancer un script — mais un panneau `config_fields_mode` (ex. le formulaire Custom de `create_entities`, réservé à ce mode) reste dans le DOM même caché par un autre mode actif (`updateModeOnlyVisibility()` ne fait que du `display:none`, jamais un retrait du DOM). Le panneau Custom, resté ouvert/vu plus tôt dans la session et jamais rempli, a donc été sauvegardé vide par-dessus le fichier qu'auto-suggest venait d'écrire. Corrigé : `saveOpenConfigForms()` ignore désormais tout panneau dont le mode déclaré ne correspond pas à l'onglet actif au moment du clic Lancer — même logique que `updateModeOnlyVisibility()`. Affecte potentiellement aussi `inject_events`/`inject_signals` (même mécanisme `config_fields_mode`), non vérifié spécifiquement. |
| **Placeholder cassé + réapparition d'une saisie ancienne (champ Angle, `generate.py`)** | 11 août (soir) | Deux causes distinctes derrière le même symptôme ("Angle : romuva la nouvelle religion en europe" réapparaissant dans le récapitulatif malgré un champ vide à l'écran). **(1) Bug JS réel** : `renderOption()` fixait `inp.placeholder = opt.label` au lieu de `opt.placeholder` — le texte d'exemple ("ex : focus sur les réfugiés climatiques") ne s'affichait jamais, remplacé par le libellé du champ. Corrigé, `autocomplete="off"` ajouté en prévention sur tous les champs texte générés (empêche une resucée future du navigateur, bien que ce n'était pas la cause ici). **(2) Reliquat `config.yaml`** : un champ vide dans le formulaire GUI n'envoie tout simplement pas le flag CLI correspondant (`collectArgs()`, comportement voulu) — le mode Semi-guidé retombe alors sur `config.yaml` comme base, qui gardait `angle_specifique: romuva la nouvelle religion en europe` depuis un test d'il y a plusieurs semaines, jamais nettoyé depuis. Pas un bug de code : `config.yaml` ligne 44 vidée manuellement par David (`sed -i '.bak' '44s/.*/  angle_specifique: /' config.yaml`), confirmé résolu. |
| **`--zone-slug` proposait des sous-zones sans journal (`generate.py`, Semi-guidé)** | 11 août (soir) | Repéré en testant la génération d'article : `zone_slug invalide : 'archives_neutres_geneve' n'existe pas dans journaux.yaml pour breakdown/pro_pouvoir`, alors que cette zone existe bien dans `geographie/breakdown.md` — mais en tant que sous-zone niveau 2 (`parent: geneve_bunker_institutions`). `journaux.yaml` n'a jamais qu'une entrée par zone niveau 1 ; le menu `--zone-slug` (type `zones_hier`) listait toutes les zones tous niveaux confondus sans filtrer sur la présence réelle d'un journal, laissant l'échec se produire seulement au lancement (`validate_config_semi_guide()`) plutôt que d'empêcher la sélection en amont. **Corrigé sans casser les usages légitimes de la hiérarchie complète** (`zone_hint` sur `create_entities`/`inject_events`, qui veut délibérément pouvoir cibler une sous-zone précise) : nouveau type `zones_hier_journal` (`app.py`, fonction `_zones_avec_journal()`) qui filtre sur le contenu réel de `journaux.yaml` (`data[scenario][ligne]['zones']`, union des deux lignes éditoriales) plutôt que de supposer "niveau 1 = a un journal". `--zone-slug` de `generate.py` bascule sur ce nouveau type dans `scripts_config.json`, description mise à jour en conséquence. `zones_hier` (l'ancien type) reste inchangé et utilisé tel quel par `zone_hint`. Vérifié par test unitaire local avant livraison : `geneve_bunker_institutions` passe le filtre, `archives_neutres_geneve` non. **Confirmé en conditions réelles le 12 août** — a servi de base au test de validation de la signature (voir ligne dédiée ci-dessus). |
| **Diagnostic `annee_debut`/`ancrage_reel` sur les événements** | 12 août | Question ouverte depuis le 8 août. Mené sur `inject_custom_events.py`, `fix_annee_debut_placeholder.py`, `loader.py`, et un dépouillement réel de `registre_evenements.md` (53 événements custom, tous scénarios). Conclusions : structure de date différente des instances (champ `date` unique, pas de bande `annee_debut`/`annee_fin`) ; aucune dérive de concentration observée (pic max 11% sur une seule année — 2041/2044/2047 à 6/53 chacun — contre 22% pour les instances avant correctif ; seulement 2/53 événements en 2026, pas de blocage comparable au bug des 477 fiches d'instances) ; **mais aucun mécanisme d'ancrage réel n'existait avant cette session**, ni en mode auto ni en mode custom (`inject_custom_events.py` ne chargeait jamais `etat_du_monde_reel.md`, contrairement à la génération d'instances), et `analyze_vault_coverage()` (couverture auto des événements) n'a — comme `analyze_entity_coverage()` côté entités — aucune dimension temporelle (a élargi la portée du point Partie 1 #2 aux événements, pas seulement aux entités). **Décision prise** : pas de mécanisme lourd type `ancrage_reel` des instances (bande graduée + anti-recyclage par shingle-matching) pour les événements — un enrichissement de contexte suffit, voir ligne "Cohérence événements custom" ci-dessous. |
| **Cohérence événements custom / vault, registre, géographie, état du monde** | 12 août | Nouveau chantier, demandé par David suite au diagnostic ci-dessus, sur `inject_custom_events.py` — couvre les deux modes (auto n'écrit que dans `queue.yaml`, l'injection réelle passe toujours par le mode custom via `process_idea()`, donc un seul point de code modifié couvre les deux). Trois changements : (1) import de `load_etat_monde_reel()`/`load_scenario_timeline_summary()` depuis `instance_generation_common.py` — réutilisation, aucune duplication ; (2) deux nouveaux blocs de contexte dans le prompt de développement d'événement (`## CHRONOLOGIE RÉELLE DU SCÉNARIO`, `## ÉTAT DU MONDE RÉEL`) plus une règle explicite de cohérence, en particulier pour une date proche dans le temps ; (3) validation mécanique de `zone_hint` contre `load_all_zones_event(scenario)`, refaite à **chaque itération** de la boucle scénarios (initiale et retry) — zone invalide pour ce scénario → avertissement + repli sur "libre". Décision délibérée de ne PAS ajouter de garde-fou mécanique bloquant sur le chevauchement thématique du registre (enrichissement de contexte seulement) — cohérent avec la pratique du projet de ne pas construire de mécanique de calibration pour un problème non observé (53 événements seulement, risque de mauvaise calibration comme vécu sur le chantier longueur du 10 août). **Testé en conditions réelles (dry-run, qui appelle le LLM pour de vrai — voir piège transversal du 31 juillet)** sur une queue de 5 idées ciblées : date proche 2028 (ancrage réel confirmé dans `note_coherence`), zone invalide (warning déclenché), zone valide (silence, zone utilisée), contrôle date lointaine (non-régression), et surtout **le même `zone_hint` sur deux scénarios différents** — validé silencieusement sur `eco_communalism`, warning déclenché sur `breakdown` où la zone n'existe pas, preuve que la revalidation se refait bien à chaque itération de la boucle plutôt qu'une seule fois en amont ; ce dernier cas a aussi déclenché un vrai retry de validation, confirmant que le zone_hint validé (pas la version brute) est bien réutilisé sur le retry. **Non testé en injection réelle (non dry-run)** — chemin d'écriture non modifié par ce correctif, risque jugé faible. Détail complet : `USER_MANUAL_COMPLET.md` §2, section `inject_custom_events.py`. |
| **Panneau Revue — slug/scénario/détail vides sur entités et signaux** | 12 août | Signalé par David sur une entrée réelle (`Les Veilleurs des Nappes Phréatiques` affichée `(entité)` / `—` / `—`). Cause : `_read_needs_review_yaml()` (`app.py`), parseur YAML maison ligne par ligne construit pour le format événements/enrichissement — le correctif du 2 août avait fait apparaître les sources `entites_custom`/`signaux_custom` dans le panneau sans jamais leur apprendre à lire leurs propres champs (`idea.nom`, `idea.scenario_ref`, `reason:` à plat, structure différente du format d'origine). **Deux correctifs** : (1) reconnaissance de `nom:`/`scenario_ref:`/`reason:`, avec déséchappement naïf des quotes doublées YAML — testé directement contre le vrai fichier de David ; (2) suite à sa question sur la couverture des 3 pipelines, trouvaille d'un second trou touchant entités/événements/signaux identiquement : le repli générique sur exception imprévue des 3 scripts d'injection écrit une clé `error:` **scalaire singulière**, jamais reconnue (seule la forme plurielle `errors:`/liste l'était) — corrigé de la même façon, testé avec un cas simulé. **Confirmé en conditions réelles dans le navigateur** sur l'entrée de David — les 3 colonnes s'affichent désormais correctement. Détail complet : `USER_MANUAL_COMPLET.md` §7. |
| **Cohérence événements custom — confirmation en injection réelle (non dry-run)** | 13 août | Suivi léger laissé ouvert le 12 août (chantier lui-même déjà clos ce jour-là — voir ligne ci-dessus dans le tableau du 12 août). Queue de 5 cas rejouée en conditions réelles (pas dry-run) : `zone_invalide_test` et `multi_scenario_zone_test`/`breakdown` ont déclenché le warning `zone_hint` attendu (revalidation par scénario confirmée en réel, pas seulement en dry-run) ; `escalade_sahel_2028_test` et `zone_valide_test` injectés au premier essai ; `controle_date_lointaine_test` a échoué 3/3 (root cause distincte, voir ligne dédiée ci-dessous). Deux événements réels hors queue de test (`revolution_travail_sahel_numerique`, `greve_generale_corridors_eurasiens`) injectés avec succès sur tous leurs scénarios cibles, retries sur acteurs fonctionnant comme prévu. `validate.py` : 0 erreur, 10 avertissements, base valide. Écriture disque du chantier du 12 août définitivement confirmée fonctionnelle. |
| **Dimension temporelle pour la génération automatique** | 13 août | Chantier backlog Partie 1 (ex-point 2), esquissé le 8 août, portée élargie aux événements le 12 août, codé le 13 août. Choix de granularité tranché avec David : **bandes larges** (proche 2026-2035 / moyen 2036-2060 / lointain 2061-2098) pour le signal envoyé au LLM à l'étape auto-suggest/auto — actionnable, peu de bruit sur un vault encore modeste — et **année exacte** conservée en interne pour la détection de concentration (même granularité que celle qui avait révélé 22% sur 2041 côté instances avant le correctif `annee_fin`). Nouvelles fonctions partagées dans `instance_generation_common.py` : `TEMPORAL_BANDS`, `compute_temporal_distribution()`, `format_temporal_summary()`, `format_concentration_warnings()` (seuil de concentration : 12% du total, seulement si l'échantillon atteint 15 — sous ce seuil jugé trop bruité pour être actionnable). Appliqué symétriquement dans `analyze_entity_coverage()` (`annee_debut`) et `analyze_vault_coverage()` (`date`), résumés de prompt enrichis d'une section "Distribution temporelle actuelle" + avertissement de concentration vault-entier, consignes des deux prompts auto-suggest mises à jour (compenser les bandes sous-représentées, éviter les années sur-concentrées, et pour toute proposition proche de 2026-2035 privilégier une idée rattachable à une dynamique réelle documentée plutôt qu'une date arbitraire — l'ancrage précis restant fait à l'étape de développement, déjà en place). Testé : fonctions helper validées unitairement (bandes correctement regroupées, seuil de bruit respecté, concentration détectée à 44%/20%/16% sur un cas simulé) ; **validé par David en dry-run réel** sur le vault. Injection réelle non spécifiquement retestée pour ce chantier (le mécanisme ne touche que la sélection/le prompt, pas le chemin d'écriture). `inject_custom_signals.py` vérifié sans dimension temporelle (aucun champ `annee_debut`/`date`) — non concerné, cohérent avec l'architecture du vault. |
| **Bug `evenement_cle` — année exigée en fin de phrase (jamais respecté par le LLM)** | 13 août | Trouvé en rejouant la queue de test en conditions réelles (voir ligne ci-dessus) : `controle_date_lointaine_test` a épuisé ses 3 essais de retry sans jamais être injecté, la validation rejetant systématiquement `evenement_cle` malgré une année bien présente — le LLM produit invariablement le format `"2091 : L'Europe unifie l'horloge..."` (année en tête), alors que `validate_instance()` n'acceptait qu'une année en toute fin de chaîne (`re.search(r"(\d{4})\s*$", ...)`). Le message de retry ne précisait pas *où* replacer l'année, d'où 3 échecs identiques sans convergence. Vérifié que la position de l'année dans `evenement_cle` n'a aucune fonction technique en aval (`date` est stockée séparément dans sa propre colonne du registre par `regenerate_registre_with_event()`, et `load_scenario_timeline_summary()` préfixe de toute façon sa propre date à l'affichage) — la contrainte de position était une pure convention sans nécessité. **Corrigé** : regex assouplie (`re.search(r"\b(\d{4})\b", ...)`, année acceptée n'importe où), prompt et exemple JSON mis à jour en cohérence (ne plus demander une "année finale" que la validation n'exige plus), message d'erreur reformulé. **Confirmé en conditions réelles** : `controle_date_lointaine_test` relancé avec la même idée d'origine (retrouvée dans `needs_review.yaml`, où le champ `idea` complet était bien préservé malgré la disparition de `queue.yaml`, vidée par design à chaque run) — injecté au premier essai, `validate.py` toujours propre (0 erreur, 10 avertissements inchangés). |
| **Documentation à corriger (chantier `trajectoire`)** | 14 août | Point 2 du backlog du 13 août — vérifié déjà appliqué dans `USER_MANUAL_COMPLET.md` (§1 et §6, tous deux datés "corrigé le 9 août 2026"). Fermé sans travail supplémentaire, juste une vérification avant de lancer un chantier qui n'en était plus un. |
| **P16 — `zone_hint` documenté dans `QUEUE_TEMPLATE`** | 14 août | Retrouvé via recherche exhaustive dans l'archive (décidé le 11 juillet, jamais fait, disparu du backlog sans clôture après le 2 août). `create_entities_and_instances.py` le documentait déjà — seul `inject_custom_events.py` avait l'oubli, corrigé (ajout de l'entrée dans le bloc CHAMPS du `QUEUE_TEMPLATE` + exemple JSON). `inject_custom_signals.py` confirmé hors scope. Risque d'écrasement identifié avant de coder : `save_queue_with_template()` réécrit tout `queue.yaml` depuis la constante Python à chaque vidage — d'où l'édition du `.py`, jamais du `.yaml` directement. |
| **Doublon d'entité `arctic_passage_authority` / `autorite_passage_arctique`** | 14 août | Diagnostic confirmé : vrai doublon généré automatiquement par `extract_phantom_slugs.py` (`entites_custom/processed.yaml` contient 3 entrées `_slug_fantome_original`/`_slug_corrige` le prouvant) — un slug fantôme détecté sans entité correspondante (probablement une référence de zone géographique) a généré une entité indépendante, sans savoir qu'`arctic_passage_authority` existait déjà pour la même institution. Champs `zone:` et l'entrée `geographie/breakdown.md:2278` identifiés comme un chantier séparé (référence géographique, pas d'entité) et volontairement non touchés. **Script `fix_arctic_passage_duplicate.py` livré** (réutilisable) : 17 fiches migrées, 34 références alliance/opposition réécrites, puis `undo_custom.py --generalisation yes --execute` (archétype fantôme + instance supprimés, `_entities_list.json` nettoyé). `validate.py` final : 0 erreur. |
| **Wikilinks cassés `test_durcissement_policy_reform`** | 14 août | 7 fiches `policy_reform` référençaient encore une fiche supprimée (résidu du 8 août), une ligne bullet identique par fiche. **Script `fix_test_durcissement_wikilinks.py` livré** (réutilisable pour tout futur cas similaire) : 7 lignes retirées sur 7 fiches. `validate.py` final : 0 erreur, 0 avertissement. |
| **Quatre reliquats de la consolidation du 7 août** | 14 août | Les 4 sous-points traités d'un coup. (1) Redéploiement des correctifs du 2 août (`routes_dashboard.py`, panneau Revue, Groenland) : confirmé de facto via usage réel documenté (bug trouvé le 12 août sur le panneau Revue, preuve d'utilisation post-livraison) — fermé sans action. (2) `instance_template.md` : confirmé par David déjà déplacé vers `/templates` ; vérifié qu'aucun autre script n'a de dépendance sur son emplacement dans `instances/` — les filtres existants deviennent inertes, pas cassés. (3) Limite panneau Revue (slug générique) : vérifié dans le code réel d'`app.py` que c'était déjà corrigé le 12 août (branches `nom:`/`scenario_ref:`/`reason:` ajoutées à `_read_needs_review_yaml()`, non documenté dans le manuel jusqu'ici) — tracé à la main sur un vrai extrait `needs_review.yaml`, confirmé fonctionnel. (4) Discipline de rédaction du backlog : non-actionnable, vigilance continue notée. |
| **Fichiers parasites `generator/` (incident du 5 août)** | 14 août | David a relancé la commande de vérification fournie le 11 août : aucun fichier trouvé, déjà propre. Fermé, rien à faire. |
| **Encodage portugais cassé dans certains slugs** | 14 août | Retrouvé via recherche exhaustive dans l'archive (noté le 8 août, jamais traité). Cause racine identifiée avec précision : `slugify()` utilisait une table d'accents français en dur au lieu d'une normalisation Unicode générique — tout accent non-français (portugais, espagnol...) tombait dans le `re.sub` générique et devenait `_`. Trois fichiers touchés et corrigés, identiques mot pour mot : `create_entities_and_instances.py`, `create_entity.py` (legacy), `officialize_alliances.py` (actif). Correctif : normalisation Unicode NFD (même principe que `_fold()` déjà existant dans `gui/app.py`), testé sur portugais/français/espagnol/allemand. **Audit du vault** (`audit_broken_slugs.py` livré, réutilisable, lecture seule) : 590 entités auditées, 18 candidats, 2 vrais cas confirmés (`rede_paulista_de_distribuic_o_algor_tmica`, `frente_sert_o_livre`), 15 faux positifs (raccourcissements volontaires de slug), 1 artefact du script (`entity_template.md`, voir Partie 2 — nom réel corrigé le 15 août, la doc disait à tort "entite_template.md" en français ; erreur reproduite dans une première version du filtre, corrigée aussi le 15 août). **Migration des 2 cas exécutée** (`rename_broken_slugs.py` livré, réutilisable) : 11 fichiers renommés, 322 références réécrites dans 141 fiches, `documentation/` explicitement exclu (historique, jamais réécrit). `validate.py` final : 0 erreur. |
| **`acteurs_hint_count` (P15) non plafonné en filtre dur** | 14 août | Diagnostic précis : la valeur était calculée et bornée (1-4) mais jamais transmise à `step2_develop_instance()` ni utilisée par `validate_instance()` — calculée puis jetée sans effet, contrairement à `variables_hint_count` qui a une vraie troncature. **Corrigé** : nouvelle fonction `truncate_actors()` dans `inject_custom_events.py`, appliquée à l'essai initial et à chaque retry, même schéma que la troncature `variables` (hints préservés en priorité). Testé unitairement (3 cas). Pas encore confirmé en conditions réelles — laissé en validation au fil de l'eau, comme le point #1 du backlog. |
| **Duplication `detect_registre_leakage()`** | 14 août | La fonction et deux fonctions dépendantes (`_read_registre_text()`, `_normalize_for_matching()`) existaient en double entre `instance_generation_common.py` (module partagé) et `fix_annee_debut_placeholder.py` (copie indépendante) — divergence purement cosmétique constatée (docstrings, style), aucune divergence fonctionnelle. **Corrigé** : `fix_annee_debut_placeholder.py` importe désormais les trois fonctions depuis le module partagé, variable de cache locale devenue inutile retirée. Prévient une future divergence silencieuse, même pattern que celui ayant causé de vraies erreurs avant la factorisation de juillet/août. |
| **GUI — `--force` du panneau localisation ne rafraîchissait pas le menu** | 14 août | Diagnostic en trois causes distinctes, sur trois fichiers. (1) `scripts_config.json` : le champ `--slug` d'`extract_localisation` n'avait aucune déclaration `slug_extra_params` reliant son contenu à `--force` — corrigé, ajout de `{"force": "--force"}`, vérifié par diff programmatique qu'aucune autre entrée n'a été touchée. (2) `app.js` : `lireValeurChamp()` lisait `.value` au lieu de `.checked` sur les checkboxes — une checkbox sans attribut `value` explicite renvoie toujours `"on"` quel que soit son état. Corrigé. (3) `app.py` : la route `/api/slugs` ne lisait ni ne transmettait jamais le paramètre `force` au sous-processus `extract_localisation.py --scan-pending`, même une fois envoyé par le frontend. Corrigé. Vérifié séparément que `extract_localisation.py` respectait déjà correctement `--force` en interne (`collect_fiches()`) — aucun correctif nécessaire côté script. **Testé et confirmé en navigateur réel par David.** |
| **Artefact `audit_broken_slugs.py` — gabarit non filtré du rapport** | 15 août | Fix initial appliqué avec le mauvais nom (`entite_template.md`, français, jamais présent sur disque) — corrigé après vérification directe du vault (`find . -iname "*entite*template*"` infructueux, `find . -iname "*template*"` révélant le vrai nom `entity_template.md`, en anglais). Filtre corrigé dans `audit_broken_slugs.py`. **Déplacement du gabarit** décidé dans la foulée (cohérent avec `instance_template.md` déjà présent dans `/templates`) : `entites/entity_template.md` → `templates/entity_template.md`, exécuté par David (`git mv`). Vérification en amont avant déplacement : grep exhaustif du projet ne trouvant aucune référence codée en dur au fichier par nom, mais révélant que `gui/routes_dashboard.py` (`len(list(entites_dir.glob("*.md")))`, total du dashboard) et `generator/generate_instances.py` (chargement de "toutes les fiches entites/\*.md") listaient `entites/` sans filtrer le gabarit — donc potentiellement affectés silencieusement avant le déplacement, corrigés de facto par celui-ci sans toucher à leur code. **Confirmé après déplacement** : `validate.py` post-déplacement montre 589 entités chargées (vs 590 avant), cohérent avec la sortie du gabarit du dossier compté. Le filtre resté dans `audit_broken_slugs.py` est désormais un no-op inoffensif (le fichier n'étant plus dans `entites/`, plus jamais scanné) — pas retiré, sans urgence. |
| **`forces_attractives`/`forces_repulsives` — décision de conception + câblage** | 15 août | Chantier prioritaire de la session, en trois temps. **(1) Décision de contenu** : analyse comparative des 12 fiches `variables/*.md` (script Python, comptage + recoupement des deux sections candidates) — section 3 (`Dynamique interne`, snake_case) systématiquement plus riche (4-8 items) que section 4 (`Structure causale`, 1-5 items, parfois en `snake_case` cassé sur 2 fiches) et quasi-toujours un sous-ensemble reformulé de celle-ci. **Décision de David : section 3 comme source de vérité unique**, section 4 ignorée. **(2) Développement** : nouveau parseur `_extract_forces_from_body()` dans `loader.py` (même convention que `_extract_indicateurs_from_body()`), câblé dans `load_variable()` ; `build_variables_context()` (`prompt_builder.py`) affiche désormais les 4 premiers items de chaque liste par variable détaillée. Testé unitairement contre les 12 fiches réelles (comptages exacts confirmés) puis en génération réelle (prompt Flask inspecté, forces bien présentes et correctement limitées à 4 items). **(3) Trois problèmes découverts et corrigés en cours de validation réelle**, chacun re-testé sur au moins une génération après correctif : *(a)* déséquilibre systématique répulsif/attractif (3/3 premiers tests : 0 trace de forces attractives, malgré une consigne de pilotage v1 descriptive) — consigne resserrée en contrainte concrète et actionnable ("au moins un fait/acteur/citation illustrant une force attractive sur l'ensemble de l'article", portée clarifiée après question de David pour éviter une lecture "une par variable" trop lourde) ; confirmée fonctionnelle sur test réel (Opération Baraka, article `breakdown`). *(b)* Récurrence anormale de l'entité `terminal_kharg_data_haven` comme sujet principal sur 4/4 générations consécutives, deux scénarios différents — diagnostic exact du mécanisme (`filter_instances_for_thematique()` dans `loader.py` : score structurellement avantageux via `impact_systemique_global` élevé + recoupement constant avec les zones de la thématique `actualites_a_la_une`, jamais départagé par la rotation à mémoire qui ne joue que sur l'égalité de score stricte). Corrigé par élargissement de la notion d'ex-aequo (`_score_bucket()`, tolérance relative au score max du lot plutôt qu'égalité absolue, évite un effet de bord d'arrondi identifié en testant) — testé sur cas synthétiques (recul de 15/15 à 4/15 sur un écart réaliste, tout en préservant 15/15 sur un écart réellement dominant) puis confirmé en conditions réelles sur `eco_communalism` (2 usages déjà enregistrés). *(c)* `climat_environnement_global` totalement absente du texte sur 5/5 générations malgré vérification qu'elle était bien dans le top `MAX_VARIABLES_DETAIL` (6) à chaque fois — donc pas un problème de troncature côté code, le LLM reçoit la donnée en détail mais ne la mobilise pas (probablement un effet de position/priorité narrative de la thématique, `climat_environnement_global` toujours en position 5-6 sur 6). Nouvelle consigne de couverture minimale des variables pilotes (tag `[VARIABLE PILOTE]`, une résonance minimale exigée par variable, portée clarifiée pour ne pas exiger une couverture exhaustive des forces précises). Premier test après ce 3e correctif positif (article `breakdown`, résonance climatique obtenue pour la première fois en 6 articles) — un seul échantillon, à confirmer sur plusieurs générations futures. **Considéré terminé par David** en fin de session, avec cette réserve de confirmation dans la durée. |
| **"Les Veilleurs des Nappes Phréatiques" — décision tranchée et entité créée** | 15 août | Décision en tout début de session : corriger et créer (pas d'abandon). Diagnostic préalable avant correction : `category: mouvement` absent de `VALID_CATEGORIES` (`create_entities_and_instances.py`) — `organisation` retenue comme catégorie de repli la plus proche, après vérification que le champ `category` n'est utilisé nulle part dans `prompt_builder.py` (aucune influence sur le contenu narratif généré, seulement une étiquette de classification interne). **Audit élargi avant correction** : 4 autres fiches déjà présentes dans `entites/*.md` avec la même catégorie invalide (`coalition_vivant`, `collectifs_du_seuil`, `internationale_travailleurs_augmentes`, `mouvement_racines_vivantes`) — dette historique antérieure au garde-fou actuel (aucun champ `date_generation`, suggérant une origine du socle initial de juin 2026), sans lien avec une faille de couverture active du pipeline. Corrigées en lot (`sed`), confirmé par `validate.py` (0 erreur, 0 avertissement, disparition des 4 warnings "catégorie invalide"). **Idée elle-même** : `needs_review.yaml` corrigé (`category: mouvement` → `organisation`), remis en file via `requeue_needs_review.py`, entité créée via `create_entities_and_instances.py --mode custom`. Cycle post-injection complet exécuté automatiquement (`extract_localisation` → `review_localisation --auto-resolve` → `validate.py`) : 5/6 instances créées avec succès (breakdown, fortress_world, new_sustainability, policy_reform, reference), localisations résolues (3 directes, 2 ambiguës auto-résolues, 0 review manuelle restante). **1 instance en échec** : `eco_communalism` (le `scenario_ref` d'origine de l'idée) — garde-fou `ancrage_reel` a correctement bloqué une hallucination du LLM (citation d'un événement fictif du registre du scénario comme fait réel de 2026). **1 avertissement mineur** sur l'instance `reference` : alliance filtrée pointant vers un slug invalide (`reseau_des_capteurs_citoyens_reference`, probablement une entité inventée par le LLM sans existence réelle dans le vault). `validate.py` final : 0 erreur, 0 avertissement (590 entités, 737 instances). **Reste en attente pour une prochaine session** : retenter la génération de l'instance `eco_communalism`. |
| **Injection matricielle — instances/entités custom (`impact_sur_variables`)** | 16 août | Objectif de David : que les trois types d'injection custom (entités/instances, événements — déjà opérationnel —, signaux faibles) puissent réellement faire évoluer le `level` des variables, pas seulement les influencer narrativement. Côté instances : `injection.type` restait toujours `canonique` avec bloc `impact_sur_variables` vide dans les trois scripts qui écrivent des fiches instance (`instance_generation_common.py`, `generate_entities.py`, `officialize_alliances.py`) — `apply_custom_injections()` (`snapshot.py`) existait déjà côté consommation mais n'était jamais alimenté. **Plafond du delta** : dérivé de `impact_systemique_global × 5` (0-25) plutôt qu'une constante fixe comme les événements (25) — réutilise un jugement de magnitude déjà écrit sur la fiche plutôt que d'en introduire un second potentiellement incohérent, et borne l'empilement multi-variables (une instance influence souvent 3-5 variables). Câblage limité au mode `custom` de `create_entities_and_instances.py` (idée utilisateur explicite) — modes `auto`/`auto-suggest` et `generate_instances.py` non touchés, comportement canonique inchangé. **Deux bugs trouvés et corrigés en testant en conditions réelles (test réel complet, 6 scénarios, "Gelecek Meclisi")** : (1) Mistral ne respecte pas toujours la position racine demandée pour `propagation_via_matrice`/`contexte_injection` dans le JSON — les duplique par variable dans `impact_sur_variables`, parfois sans jamais les mettre au niveau racine du tout (2 scénarios sur 6 sans champ racine) — corrigé par un filet de sécurité dans `write_instance_file()` (dérivation depuis les valeurs par entrée si le champ racine est absent) en plus d'un resserrement du prompt ; (2) `contexte_injection` écrit en scalaire YAML brut sur une ligne au lieu d'un bloc replié `>` comme les autres champs texte — un simple `" : "` dans le texte (quasi systématique en français) cassait le parsing YAML de **toute la fiche**, avec repli silencieux sur des valeurs par défaut pour `trajectoire`/`annee_debut`/`impact_local`/etc., et `injection.type` ne valant plus jamais `custom` (donc aucune propagation, silencieusement). Trouvé via un test GUI réel (mode Forcer) où "Perturbations custom actives" ne montrait aucune ligne pour l'instance testée. **Validé de bout en bout après correctifs** : 6 fiches régénérées, YAML parse propre sur les 6, plafond respecté (aucun dépassement sur 18 impacts), et confirmation finale par les logs `snapshot.py` en conditions réelles (`[snapshot] Injection custom 'Meclis des Futurs Fragmentés' (an 2047, 51 ans d'effet)`, 3 deltas appliqués conformes à la fiche). Un article réel a été généré et sauvegardé pendant ce test (non prévu comme définitif, coût API réel engagé). |
| **Injection matricielle — signaux faibles (`impact_sur_variables`)** | 16 août | Extension du même mécanisme aux signaux faibles, avec une architecture différente des instances : un signal cible une seule variable par appel LLM (contrairement aux instances qui balaient plusieurs `variables_influencees`), et chaque scénario a déjà sa propre fenêtre temporelle (`date_bascule`) — `annee_injection`/`duree` sont donc dérivés automatiquement de cette fenêtre plutôt que redemandés au LLM. **Plafond fixe `MAX_DELTA_SIGNAL = 10`** (pas dérivé d'un score comme les instances, les signaux n'ont pas de champ `impact_*` équivalent) — délibérément bas, cohérent avec la sémantique "signal faible". `propagation_via_matrice` recommandé à `false` par défaut dans le prompt. **Stockage** : nouveau bloc `impact_sur_variables` dans la fiche d'audit `signaux_custom/{slug}.md` (corps markdown, section dédiée), séparé du bloc `signal_to_state` narratif existant — aucune modification du mécanisme d'écriture déjà testé (registre, anti-collision, section 12). Bloc écrit d'emblée avec `contexte_injection: >` (bloc replié), leçon tirée directement du bug YAML des instances plus haut, jamais reproduit ici. **Nouveau côté chargement** : `loader.load_custom_signals()` (lit le bloc dans le corps markdown, pas le frontmatter) et `snapshot.apply_custom_signals()` (même mécanique que les deux fonctions sœurs, avec une différence structurelle clé : le scénario compte, un signal peut ne couvrir que certains scénarios — testé explicitement qu'aucune modification n'a lieu sur un scénario non couvert). Un bug de fusion trouvé et corrigé avant tout test réel : `event_modifications` aurait été compté deux fois dans le prompt final. **Validé en conditions réelles sans aucun bug supplémentaire trouvé** (contrairement aux instances) : un vrai signal injecté (`decodage_langage_animaux_ia`), YAML parse propre, plafond respecté sur les 6 scénarios (`delta_level: 5` partout), `annee_injection`/`duree` cohérents avec `date_bascule`, chargement et application confirmés par un test direct de la chaîne `loader`→`snapshot`. **Angle mort mineur restant** : ce premier signal réel avait `propagation_via_matrice: false` — la propagation matricielle sur un signal n'a été testée qu'en synthétique, jamais sur un vrai cas avec `via_matrice: true`. |
| **Cohérence section 7 ↔ section 12 des signaux (`validate.py`, 10e section)** | 16 août | Nouveau chantier demandé par David suite à une question sur la fiabilité de la synchronisation section 7 (annotations courtes) / section 12 (bloc `signal_to_state`) des fiches variables — motivée par un incident réel documenté le 26 juillet (signal dupliqué dans `variables/geopolitique_conflits.md` après un crash entre l'écriture de la fiche variable et celle du registre) et des bugs similaires le 27 juillet (annotation sans préfixe, bloc section 12 cassé par `undo_custom.py`). **Approche** : croiser 3 sources indépendantes (section 7, section 12, `variables_cibles` des fiches d'audit `signaux_custom/*.md`, plus le registre en complément) plutôt que faire confiance à une seule — même principe que le fix appliqué à `resolve_signal_variables()` le 26 juillet. Diagnostic uniquement, aucune correction automatique. Intégré comme 10e section de `validate.py` (`validate_signals()`), à la demande explicite de David plutôt qu'un script autonome. **Faux positif massif trouvé et corrigé au premier test réel** : 60 avertissements sur le premier run contre le vrai vault, tous des faux positifs — les signaux du socle initial (juin 2026, antérieurs à l'existence même d'`inject_custom_signals.py`) utilisent un format différent en section 7 (marqueurs de catégorie type `**technological**`/`**social**`, référence `(→ slug)` sans le préfixe `signal_custom:`), que le contrôle traitait à tort comme des signaux custom mal annotés. Corrigé : le croisement 7↔12 ne s'applique désormais qu'aux signaux **prouvés custom** (une fiche d'audit correspondante existe dans `signaux_custom/`) — un signal du socle sans fiche d'audit est ignoré, à raison. **Confirmé sur le vault réel après correctif** : 0 avertissement `[SIGNALS]` sur 10 variables et tous les signaux custom existants (26/27 juillet + ceux du jour) — aucune vraie anomalie de cohérence détectée à ce jour. **Non couvert par ce contrôle** : le nouveau bloc `impact_sur_variables` (delta chiffré, chantier ci-dessus) — vit dans un bloc YAML séparé du `signal_to_state`, pas encore intégré à cette vérification. |
| **Instances manquantes — audit et comblement (`audit_instances_manquantes.py`)** | 17 août | Point de départ : aucun mécanisme persistant pour repérer un échec de génération d'instance sur un scénario isolé (le chemin de code `generate_instances_for_entity()`/`process_entity_scenario()` dans `create_entities_and_instances.py` retourne bien un statut `needs_review` par scénario en cas d'échec, mais l'appelant ne fait qu'incrémenter un compteur `stats["errors"]` sans jamais écrire nulle part QUEL scénario a échoué ni POURQUOI — seul un `print()` console au moment du run le montrait, capturé si le run passait par le GUI dans un fichier plat sous `gui/logs/`, jamais relu ni centralisé). **Nouveau script `audit_instances_manquantes.py`** (lecture seule, aucun appel LLM, même esprit que `trace_injection.py`/`audit_broken_slugs.py`) : compare pour chaque entité `scenarios_instances` (fiche entité) aux fichiers réels d'`instances/`, classe chaque trou en 3 catégories — désaccord de slug probable / entité entière suspecte / échec ponctuel probable — avec recherche best-effort du motif dans `gui/logs/*.log` (parsing du bloc `=== {nom} ===` puis de la ligne `{scenario}... ✗` et des lignes de raison `     - ...` qui suivent). **Deux itérations de correction après de vrais faux positifs trouvés en conditions réelles sur le vault** : (1) la passe de détection floue (difflib) sur les noms de fichiers comparait le suffixe `_scenario.md` inclus, gonflant artificiellement la similarité entre deux entités totalement sans rapport partageant juste ce suffixe (cas réel : `nexcore` vs `nexus_biosyn`, 0.42 de similarité réelle sur le nom mais 0.79 avec le suffixe partagé — 3 des 4 "faux positifs de slug" du premier run réel étaient en fait des faux positifs de CE mécanisme) — retirée du chemin de reclassification automatique, conservée uniquement comme indice faible non déterministe annoté en note (`piste_nommage_incertaine`), jamais utilisée pour déplacer un trou d'une catégorie à l'autre ; (2) le seuil de classification "entité suspecte" basé sur une proportion cassait sur les entités à peu de scénarios prévus (`Les Gardiens des Nœuds Hybrides`, 1 seul scénario prévu, son unique instance manquante = 100% à tort classée "majorité manquante") — corrigé par un seuil absolu (`--seuil-absolu`, défaut 3 scénarios manquants) combiné à la proportion (`--seuil-suspect`, défaut 0.5, ignoré si le total prévu est trop petit). **19 trous initiaux sur le premier run réel**, investigués un par un via `grep` dans `documentation/Old/`, `entites_custom/processed.yaml` et `entites_custom/queue.yaml` : 2 faux positifs de détection retirés par les correctifs ci-dessus, 2 entités classées "suspectes" toutes deux datées du 19 juin 2026 (avant même l'existence du garde-fou `ancrage_reel`, donc sans rapport avec lui) — l'une (`institut_des_seuils_demographiques`) confirmée comme un vrai trou de couverture legacy (aucune trace `custom_source`, probablement mode `auto`), l'autre (`le_cartographe_silencieux`) identifiée comme une entité de test résiduelle (voir chantier séparé ci-dessous). **13 instances confirmées relançables régénérées** avec succès (`generate_instances.py --entity ... --scenario ...`) : Réseau des Cartographes des Zones Grises, Assemblée des Territoires ×2, Coalition du Vivant, Consortium des Pêcheries Autonomes du Grand Nord, NexCore, Les Gardiens des Nœuds Hybrides, Institut des Seuils Démographiques ×6. Un cas isolé (`institut_des_seuils_demographiques`/`new_sustainability`) manqué dans le premier lot de commandes fournies (oubli, pas un échec), rattrapé et confirmé au second passage de l'audit depuis le GUI. **Intégré au GUI** (section `validation`, `scripts_config.json`), rapport affiché dans le panneau de review (`documentation/need_action/instances_manquantes.md`), confirmé fonctionnel en conditions réelles par David — `gui_verified: true`. `validate.py` final : 0 erreur, 1 avertissement (inchangé — `gelecek_meclisi_policy_reform`, voir Partie 1 point 8, découvert en marge de ce chantier). Point de reprise du 16 août (`eco_communalism`/"Les Veilleurs des Nappes Phréatiques") : n'apparaît plus dans l'audit exhaustif du 17 août — couverture complète confirmée pour cette entité, sans qu'on ait pu déterminer si elle a été générée entre les deux sessions ou si le constat initial du 16 août portait sur un état déjà résolu depuis. |
| **"Le Cartographe Silencieux" — suppression d'une entité de test résiduelle** | 17 août | Trouvé en investiguant le chantier ci-dessus (0/6 scénarios présents, classée "entité entière suspecte" par l'audit). Recherche dans `documentation/Old/` (handoffs et manuels archivés) et dans les fichiers custom réels : aucune mention en dehors d'un commentaire `# EXEMPLE :` dans l'en-tête de documentation d'`entites_custom/queue.yaml`, illustrant le format attendu d'une idée à écrire à la main — **exactement le nom, le rôle et l'`etat` de l'exemple copié mot pour mot**, avec `source: idee_2026-06`, cohérent avec l'origine du projet début juin 2026. `entites_custom/processed.yaml` contenait deux blocs `status: injected` complets et distincts pour cette même idée (deux appels LLM réels, deux `description_complete`/`tension_fondamentale` différentes) — signe d'une relance manuelle après un premier échec silencieux, elle-même restée sans effet. **Décision de David : supprimer** (pas de conservation). Vérifié au préalable qu'aucune autre fiche du vault (`entites/`, `instances/`, `evenements/`) ne référençait ce slug — suppression sans risque de casser une référence croisée. **Étapes réalisées** : sauvegarde (`documentation/need_action/backup_suppression_cartographe_silencieux/`), suppression de la fiche `entites/le_cartographe_silencieux.md`, retrait de l'entrée `_entities_list.json` (592→591), retrait des 2 blocs dupliqués de `processed.yaml`. **Un correctif supplémentaire trouvé en vérifiant le résultat** : une édition manuelle intermédiaire de `processed.yaml` avait laissé une ligne orpheline (`- status: injected` sans aucun champ `idea`/`slug` en dessous, entrée YAML incomplète mais syntaxiquement valide — risque de `KeyError` pour tout script supposant `idea`/`slug` toujours présents) — détectée par un script de vérification dédié (un seul orphelin trouvé sur 201 entrées scannées), retirée. `validate.py` confirmé stable après coup (0 erreur, 1 avertissement — inchangé). |
| **Localisation — slug de zone `istanbul` inconnu (`gelecek_meclisi_policy_reform`) + nouvel outil `promote_ville.py`** | 18-19 août | Point de départ (17 août) : `[VALIDATION ÉCHOUÉE] slug zone inconnu : 'istanbul'` sur `gelecek_meclisi_policy_reform` (`policy_reform`). **Diagnostic en plusieurs temps** : (1) aucun slug `istanbul` dans `geographie/policy_reform.md`, ni candidat par nom (espace_eurasiatique, union_technocratique_eurasiatique_territoire — cette dernière exclue, `origine_reelle` = Russie/Chine/Kazakhstan, sans rapport) ; (2) `zones_pays.json` confirme qu'aucune zone `istanbul` n'existe nulle part, même en `reference` (Turquie → `zone_moyen_orient_golfe` en `policy_reform`, `turquie_eurasie_moyen_orient` en `reference`) ; (3) trouvé dans `geographie/reference.md` comme simple `lieu_emblematique` de `turquie_eurasie_moyen_orient` ("Istanbul (siège de la Ligue des Détroits)"), jamais une zone à part entière — le LLM avait halluciné un slug de zone depuis un nom de ville cité dans le texte narratif de l'instance (siège du Gelecek Meclisi), sans passer par la résolution réelle pays/ville → zone. **`enrich_geographie_recursive.py --scenario reference --dry-run` testé mais insuffisant** : premier essai en échec (503 Mistral, aléa infrastructure, résolu par simple relance), second essai réussi mais Istanbul non retenue parmi les promotions malgré sa présence en `lieu_emblematique` (arbitrage LLM non déterministe sur un corpus de 62 zones/174 instances/370k caractères) — écrit quand même (les autres sous-zones proposées restent utiles). **Nouveau script `promote_ville.py` conçu et livré** : injection ciblée d'une ville sur un ou plusieurs scénarios (`--all` par défaut), détection en 3 cas avant toute création (zone déjà exploitable / `lieu_emblematique` non exploitable nécessitant promotion forcée / mention narrative seule ou rien), résolution pays réel via LLM avec confirmation, résolution du parent le plus précis toujours tentée (`zones_pays.json` puis arbitrage LLM entre zone-pays niveau 1 et sous-zones existantes), réutilisation intégrale des fonctions de validation d'`enrich_geographie_recursive.py` (`validate_zone`, `resolve_parents_and_levels`, `clean_sources`, `clean_zone_relations`, `dedupe_promoted_lieux`), slug toujours imposé (jamais laissé au LLM). **Deux bugs trouvés et corrigés en dry-run réel** : `type_entite: 'ville'` proposé par le LLM alors que `TYPE_ENTITE_REELLE` n'accepte que `pays/etat_federe/province/region_administrative/autre` (corrigé par prompt + filet de sécurité mécanique, normalisation automatique vers `autre`) ; log excessivement verbeux (`write_geographie_file` imprime tout le fichier reconstruit en dry-run, hérité d'`enrich_geographie_recursive.py` où c'est adapté mais pas ici — contourné côté `promote_ville.py`, plus un flag `--quiet` masquant les lignes `[llm]` de `llm_client.py` sans le modifier). **Exécuté en réel sur `policy_reform` + `reference`** : zone `istanbul` créée sur les deux scénarios, dédoublonnage réussi sur `reference` (`lieu_emblematique` retiré de `turquie_eurasie_moyen_orient` au moment de la promotion). **Clôture complète** : `extract_localisation.py --scenario policy_reform --slug gelecek_meclisi_policy_reform` a résolu correctement `zone: istanbul` (la fiche n'avait en réalité jamais eu de bloc `localisation` du tout — l'erreur d'origine provenait de l'étape d'extraction, jamais persistée). `validate.py` final : **0 erreur, 0 avertissement** — première fois depuis le début de cette investigation. |
| **`constrained_variables` — activation dans le prompt (Option A)** | 19 août | Trouvé en nettoyant la Partie 2 (listé comme point mineur "calculé, jamais affiché dans le prompt" depuis le 14 août) — David a précisé l'intention d'origine : une variable contrainte n'est pas une valeur figée ni un état défavorable, mais une **limite structurelle sur l'espace des trajectoires accessibles** dans le scénario (distinction moteur/contrainte/conséquence). Vérifié sur le vault réel : rempli sur les 6 scénarios, 3 variables distinctes par scénario, jamais un vestige de schéma — vrai trou fonctionnel, pas un point mineur. **Option A retenue** (direction de la borne déduite du contexte narratif déjà transmis, pas encodée explicitement dans le frontmatter — plus simple que l'Option B, encodage explicite `{variable, direction_interdite}`, mise de côté). **Câblage dans `build_variables_context()` (`prompt_builder.py`)** : `constrained_variables` du snapshot ajouté à l'ordre de priorité, nouveau tag `[VARIABLE CONTRAINTE]` (priorité d'affichage PRINCIPALE > PILOTE > CONTRAINTE), nouvelle consigne dédiée reprenant fidèlement la distinction de David avec exemple concret. Testé unitairement avec données simulées (tag et consigne confirmés présents). **Validé en conditions réelles sur 2 générations complètes** (`fortress_world`, variable contrainte `demographie_mobilite_humaine`) : tag et consigne bien injectés dans le vrai prompt (confirmé sur le prompt brut du premier essai) ; deux articles générés (`religion_spiritualite` puis `actualites_a_la_une`) sans aucune contradiction de la borne, mais aussi sans mise en tension réelle (la thématique n'obligeait pas le LLM à se prononcer sur la mobilité humaine — validation positive mais faible, notée explicitement). **Aucune régression observée** sur la couverture des variables pilotes ni la qualité narrative des deux articles. **Considéré suffisant par David**, clos pour la prod — test plus discriminant (thématique société/démographie) resté non fait, à envisager si un doute apparaît sur un futur batch réel. |
| **P22 — Bloc `simulation` rendu opérationnel dans `snapshot.py`** | 20 août | Session sans handoff rédigé — trou de traçabilité comblé rétroactivement le 21 août après que David a confirmé le contenu et le statut validé/fonctionnel. Décision tranchée : `simulation` devient **opérationnel** (pas seulement descriptif). Trois champs câblés avec mapping qualitatif → numérique et valeurs par défaut garantissant la non-régression (toute variable sans bloc `simulation` renseigné se comporte exactement comme avant ce chantier) : `volatility` → `VOLATILITY_DAMPING` module l'amortissement de la propagation matricielle côté variable CIBLE (remplace le facteur fixe 0.5) ; `tipping_point_risk` → `TIPPING_THRESHOLD_ADJUST` abaisse les seuils de détection de tension dans `check_coherence()` (60/70) côté variable qui PORTE le risque ; `systemic_criticality` → `CRITICALITY_MULTIPLIER` (échelle réelle 1-5 vérifiée sur les 12 fiches) multiplie le delta propagé côté variable SOURCE. Nouvelle fonction `_get_simulation_param()` centralise la lecture + repli sur défaut. Câblé dans `check_coherence()`, `apply_custom_injections()`, `apply_custom_events()`, `apply_custom_signals()` (nouveau paramètre `all_variables` sur les quatre). `predictability`/`uncertainty_level` restés hors scope (introduiraient de l'aléa dans un pipeline aujourd'hui déterministe). |
| **Garantie d'inclusion des instances custom dans `filtered_instances` (`loader.py`)** | 21 août | Résolution du risque structurel Partie 3 (identifié le 3 août, jamais rencontré en pratique jusqu'ici). Confirmé par lecture de code que `snapshot.py` applique TOUJOURS les deltas d'une instance custom (`apply_custom_injections()`, liste non filtrée), alors que sa description ne parvient au LLM que si elle survit au même filtrage par pertinence thématique qu'une instance du socle (`filter_instances_for_thematique()`/`select_instances_by_impact()`, plafond `MAX_INSTANCES=6`) — décalage confirmé, pas théorique. **Nouvelle fonction partagée `_select_with_custom_guarantee()`** : toute instance `injection.type == "custom"` obtient une place garantie, même à score de pertinence nul pour la thématique en cours ; si plus de 6 instances custom sont en lice qu'il n'y a d'emplacements, priorité entre elles par score décroissant (édge case non rencontré, vault à zéro instance custom à ce jour) ; emplacements restants disputés par les non-custom via la rotation à mémoire existante, inchangée. **Non-régression garantie et testée** : sans instance custom, comportement strictement identique à avant. Testé sur 6 cas synthétiques (non-régression, score nul garanti, édge case 8 customs pour 6 places, rotation avec `scenario_slug`, mêmes cas sur `select_instances_by_impact()`) — tous passent. **Non testé en conditions réelles** (vault toujours à zéro instance custom à ce jour) — à confirmer à la prochaine injection réelle d'une instance custom, via les logs `[loader] Instance(s) custom garantie(s)...`. |
| **P20 Phase A — enrichissement frontmatter publication web (7 champs)** | 21 août | Relance du chantier P20 (scoping du 12 juillet, en pause depuis). Redécoupé en 3 phases pour distinguer le codable sans nouvelle décision (A) du bloqué sur décision (B, reste ouvert — voir Partie 1 point 9) et du hors scope explicite (C, images). **Phase A livrée** : `slug`/`chapo`/`image_prompt`/`tags` via un bloc `===METADONNEES_PUBLICATION===` demandé au LLM dans le même appel que l'article (Option 1 actée le 12 juillet), extrait et retiré du texte AVANT tout comptage de mots (`_extract_publication_metadata()`, `api.py`) pour ne pas fausser le retry longueur du 10 août — extraction appliquée aussi bien au premier essai qu'au retry. `journaliste_slug` extrait de la signature réelle du corps de l'article (`_extract_byline()`, plus fiable que le profil édition locale pré-calculé, qui peut être vide si le LLM invente son propre nom) — tolère un habillage gras optionnel. `date_evenement` : la date fictive était déjà calculée à chaque génération mais seulement utilisée pour le nom de fichier, jamais persistée — simple ajout. `a_une_photo: false` par défaut (bascule manuelle plus tard, décision du 12 juillet). `_yaml_escape()` ajoutée pour sécuriser l'insertion de texte libre (chapo/image_prompt) dans le frontmatter construit à la main. **Testé sur 2 batches réels de 8 articles (`fortress_world`)** : bloc métadonnées 6/8 puis 8/8 après renforcement de la consigne en contrainte impérative (même traitement que la longueur le 10 août) — considéré clos. `journaliste_slug` 4/8 puis 5/8 — un bug réel corrigé en cours de route (signature en gras non reconnue par le regex initial), le reste relève d'un problème de fond distinct du LLM (signature omise ou mal positionnée), documenté séparément — voir P25, Partie 1 point 10. |
| **Ménage du vault — 5 catégories** | 21 août | Audit complet du vault (72 Mo décompressés) demandé par David, traité catégorie par catégorie avec validation avant chaque action. **(1) Fixtures de test confirmées** : 5 événements de test (`zone_valide_test`, `zone_invalide_test`, `multi_scenario_zone_test`, `escalade_sahel_2028_test`, `controle_date_lointaine_test`) retirés proprement via `undo_custom.py --type event --generalisation yes` (outil déjà existant, pas de nouveau script) — dry-run puis exécution réelle, `validate.py` confirmé à 0 erreur/0 avertissement après coup ; 3 `.bak` orphelins de `test_undo_event` (événement déjà supprimé avant cette session) et `entites_custom/queue_a_regarder.yaml` ("Test Requeue Debug", non référencé par aucun script) supprimés à la main. **(2) Fichiers isolés à la racine** : `diag_slug.py` (script de debug ad hoc du 17 août, remplacé depuis par `audit_instances_manquantes.py`), `europe_occidentale_reconstituee.md` (0 octet, orphelin — coïncidence de nom avec une vraie zone géographique très utilisée ailleurs, sans rapport), `generator.zip` (copie redondante du dossier `generator/` déjà présent en clair) — supprimés. **(3) Fichiers système/IDE** : 18 `.DS_Store`, 2 `__pycache__`, 2 `.code-workspace` mal placés (`gui/`, `evenements_custom/`) supprimés ; `.gitignore` enrichi (`.DS_Store`, `__pycache__/`, `*.pyc` — ne contenait que `.env` auparavant). **(4) Purge `.bak` de plus de 30 jours** : 367 fichiers (4,6 Mo) supprimés après confirmation que David commite régulièrement sur Git (historique déjà capturé séparément) — dry-run par `find -mtime +30` puis suppression réelle. **(5) Archives zip redondantes** : `variables/Archive.zip`, `documentation/Old/Archive.zip`, `documentation/Old/Archive 2.zip` — vérifiées fichier par fichier (100% de recoupement avec le contenu déjà présent en clair) puis supprimées. **Laissé de côté volontairement** : les 34 doublons `*copie*` de `documentation/Old/` (archive historique intentionnelle, utile aux recherches `grep` passées — pas touché sans décision explicite future). |


---

*Fin du backlog maître. Séance du 21 août prolongée en soirée bien
au-delà de ce qui était anticipé — le point 12, censé être "à scoper
demain", a finalement été entièrement scopé, codé, testé ET exécuté en
réel le soir même, suivi du lancement de `rapprocher_articles.py` sur
le corpus complet. Pour la prochaine session, dans l'ordre suggéré :*
- **Confirmer l'exécution réelle de `rapprocher_articles.py`** (point
  9bis) — vérifier que `tags_reference.yaml` existe bien et que
  `articles_lies` est bien écrit dans le frontmatter (le dry-run a été
  vérifié, mais l'exécution réelle n'a pas explicitement été confirmée
  en fin de séance).
- **Nouveau constat de fond à qualifier** (point 9bis) — le mécanisme
  structurel repéré sur `gelecek_meclisi` (7 articles, invalidé par la
  suite) touche en réalité plusieurs entités sur 5 des 6 scénarios,
  confirmé sur le corpus complet (71 articles). Mérite une vraie
  session de discussion : défaut à corriger, caractéristique voulue de
  certaines entités, ou distinction à faire entre institutions
  (spectre large) et personnes récurrentes (`leena_vainala`,
  `amara_diallo_nkosi` — cause probablement différente).
- **Bug `--stats` à corriger** (point 9bis) — aucun seuil minimum
  d'articles avant l'alerte `QUASI-OMNIPRÉSENTE`, fausse `new_
  sustainability` (1 seul article, 100% mécanique sur tout).
- **P25 (signature journaliste)** — nouveau symptôme observé la veille
  (pattern `---` avant signature en pied d'article) ; toujours en
  observation, pas de correctif isolé avant un batch plus large (voir
  Partie 1, point 10).
- **Point 8** (intégration GUI de `promote_ville.py`) — scopage
  toujours non fait, pas bloquant.
- Reste en Partie 1 sans changement : points 3 (P17), 4 (Bug #27), 5
  (renommage YAML), 6 (troncatures JSON), 7 (P21/P14, pause longue
  durée) — tous en attente sur décision explicite de David.
