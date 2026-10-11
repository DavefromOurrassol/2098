# Backlog actif — Ourrassol 2098
*Dernière consolidation majeure le 23 août 2026 (reconsolidé le 23
septembre 2026 : #2, #2bis, #4 et S11 clos et archivés ; le 24 septembre :
#1 Hyphan clos et archivé, S15/S16 ajoutés ; le 25 septembre : #4, S13 et
S15.1 clos et archivés, S17 « audit du lore » ajouté ; le 26 septembre :
S12, S16 et S17 clos et archivés, S15 réduit, S18 ajouté ; le 27 septembre :
chantier « Injection et propagation » ouvert et clos dans la session,
archivé, S19 ajouté ; le 27 septembre après-midi : chantier « Signaux
faibles — polarité, persistance, idées en texte libre » ouvert et clos,
archivé, S19 mis à jour, S20 ajouté ; le 28 septembre : chantier « Veille
signaux faibles » ouvert et clos, archivé, S21 ajouté ; le 29 septembre :
S21 options 1 et 2 closes — flux RSS en service, recherche web par API non
retenue —, archivées ; le 1er octobre : S22 ajouté, S20 et S21 mis à jour ;
le 3 octobre : chantier 5 « Site des revues » ouvert, S23 ajouté, #3 mis à
jour ; le 4 octobre : S23 clos pour l'essentiel et archivé (signatures,
lieu ≠ zone, journaux manquants, rezonage, temporel), S23 réduit à ses
restes, S24 ajouté ; le 5 octobre : S22 signal orphelin corrigé et `+1`
retiré, chantier 5 avancé — titres, recherche, continents forcés —, Hyphan
exclue hors reference, S25 « Kharg-9 surreprésenté » et S26 « journal
couvrant un fait d'une autre zone » ajoutés ; le 6 octobre : S25 traité
côté code (cooldown durci, Kharg-9 exclu en eco_communalism, doublon retiré)
et mis en surveillance, S26 clos et archivé, `nouveau_califat_barcelone`
supprimée, « Rédaction à » sur le site, S3/S6/S7/S10 et `_extract_byline()`
clos par décision, Hacker News retiré des flux RSS, S28 « outils
externes » ajouté ; le 9 octobre : S22 clos et archivé (reprise réussie,
fence réparée, patch des événements frères), Mistral Large 4 évalué et non
retenu par défaut (S29 ajouté), S27 avancé — simulateur « et si ? » v6 en
service —, anomalies de données notées dans S24, notes de calibrage dans
S19),
mis à jour en continu
à chaque clôture de session. Chantiers clos et leur historique complet
dans `BACKLOG_ARCHIVE.md` (fichier séparé, à uploader seulement en cas
de besoin de vérifier si un point a déjà été traité). Chaque chantier
a un nom stable — à réutiliser tel quel dans les prochaines sessions
pour éviter toute nouvelle divergence de nommage.*

---

# PARTIE 1 — CHANTIERS OUVERTS (à traiter)

---

## ✅ 1. Scénario 1 — Hyphan (fortress_world) — CLOS le 24 septembre
Géographie tranchée le matin (revue point par point), personnages/entités/
événements injectés l'après-midi depuis le docx `Ourrassol_Scénario1.docx`
(16 entités, guerre indo-arabe 2038, sous-zones Paris/Évry/Tolosa), Hyphan
elle-même en instance fortress_world exclue des articles. Détail :
`BACKLOG_ARCHIVE.md` et `HANDOFF_24_SEPTEMBRE.md`. Suites optionnelles
déplacées en secondaire (S15).

---

## ✅ 2 / 2bis. Overlays + améliorations Carte / Refonte architecture Carte — CLOS le 23 septembre
Reliquats traités le 23 sept (code mort `app.js`, `check_overlay_portion_
coherence.py` débogué + intégré au scan, premier test réel "Zones à
enrichir", portions orphelines rescannées). Détail : `BACKLOG_ARCHIVE.md`
et `HANDOFF_23_SEPTEMBRE.md`. Points résiduels mineurs déplacés en
secondaire (S12, S13, S14).

---

## 🟢 3. P20 — Enrichissement frontmatter pour publication web (Phases A+B+C codées, service image à brancher)
**Relancé le 21 août** (scoping d'origine du 12 juillet, resté en pause
jusqu'ici — voir BACKLOG_ARCHIVE.md pour l'historique complet). Le chantier a été
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
prépare le rapprochement `articles_lies` — calculé depuis.

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
P25 (secondaire, S1) pour le détail des anomalies de signature
observées sur ce dernier batch, qui restent le seul point non résolu
de ce chantier.

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

**Hébergement des journaux — tranché et en ligne le 3 oct** : voir chantier
5 « Site des revues ». Le site affiche aujourd'hui un emplacement vide pour
les articles `a_une_photo: true` ; brancher les vraies images (fichier +
`image_alt`) dans `export_revues.py` au moment du choix du service.

**À faire au branchement (26 sept)** : régénérer l'image de l'article
fortress_world du 23 août (`20260823_080632_…_18octobre2098.md`) — son
`image_prompt` a été corrigé (Halifax-Haute au lieu de Bruxelles-Forteresse),
mais une image déjà produite montrerait encore Bruxelles.


---

## ✅ 4. Revue des 14 chantiers `zone_suspecte` — CLOS le 25 septembre
11 ignorés, `ameriques_multipolaires` marqué traité (déjà appliqué),
`bloc_persique_autonome` appliqué (`stable`), Portugal rattaché à
`peninsule_iberique_cooperative` (policy_reform). Aucun chantier
`a_traiter` restant. Détail : `BACKLOG_ARCHIVE.md` et
`HANDOFF_25_SEPTEMBRE.md`.

---

## 🟢 5. Site des revues — publication web (ouvert le 2-3 octobre)
**En ligne : https://ourrassol.pages.dev** (kiosque + 12 revues, 145 chapôs de
rédaction). Fonctionnement, commandes et décisions : manuel §2octies ;
déroulé : `HANDOFF_3_OCTOBRE.md`. Publier = `python3 generator/chapos_revues.py`
(si nouveaux articles) puis `bash generator/publier_site.sh`.

Reste à faire, dans l'ordre envisagé :
- **12 identités visuelles** : un bloc `style` par revue dans `revues.yaml`
  (polices, couleurs, variantes de mise en page) lu par `export_revues.py`,
  une maquette par revue à valider comme celle du *Courrier des Continents*.
  Champs `style_visuel` déjà posés (ex. `samizdat`, `transcription_radio`).
- ~~**Guillemet orphelin dans des titres**~~ — **fait le 5 oct** (24 titres,
  `retirer_guillemets_englobants()`). Même jour : **titres en capitales**
  remis en casse française à l'export (14 articles, `normaliser_capitales()`)
  et consigne ajoutée au prompt ; **recherche** par revue et sur le kiosque
  (texte complet) ; **continents forcés** pour 5 zones transcontinentales
  (manuel §2octies) ; entrée GUI « 📰 Audit des revues ».
- ~~**Continent deviné** `nouveau_califat_barcelone`~~ — **zone supprimée le
  6 oct** (coquille vide : ni pays ni description ; 2 rédactions retirées de
  `journaux.yaml`).
- ~~**Siège de la revue**~~ — **fait le 6 oct** : « Rédaction à Séoul » en pied
  de page, bandeau de la Une et kiosque (`patch_redaction_siege.py`).
- **Photos** : brancher les images de `generate_images.py` (lié à #3 P20).
- **Audio** (*Radio Frontières*, journaux oraux `type_diffusion: oral`) :
  fichiers lourds → stockage Cloudflare R2 envisagé ; origine des extraits
  (synthèse vocale ou enregistrements) à décider.
- **Version multilingue** : isoler les libellés fixes par langue, pages sous
  `site/<langue>/`. Attention au plafond Cloudflare Pages (20 000 fichiers).
- Optionnel : titre réécrit par la revue et encadré « Contexte » (même appel
  que le chapô) ; protection d'accès Cloudflare pendant les tests ; bouton
  « Publier » dans le GUI ; références entre articles (David, à part).
- **167 articles en ligne** au 6 oct (le doublon Kharg-9 *Le Nexus qui défie
  Genève* retiré).
- **219 articles publiables sur 219, tous signés** (4 oct) : les 17 non
  publiables du 3 oct sont réglés (zones rattrapées par le rezonage,
  `ligne_editoriale` déduite des journaux cités). Publication :
  `bash generator/publier_site.sh` (le script lance lui-même
  `export_revues.py --build` ; exécutable depuis le 6 oct :
  `generator/publier_site.sh`).
- **18 nouveaux journaux** (4 oct) : fiches publiques présentes, chapôs
  régénérés et site republié.

---

# PARTIE 2 — SECONDAIRE — différé, pas d'action tant que rien ne remonte
*Priorité basse confirmée le 30 août — regroupés ici pour ne pas encombrer la lecture des chantiers actifs. À retraiter dès qu'un signal réel remonte (récurrence, besoin concret), pas de calendrier fixé.*

---

## ⚪ S1. P17 — retester la fiabilité `mistral-small` sur choix contraint
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

Note P25 (signature journaliste, ~25-33% d'échec, symptôme signature
après séparateur `---` observé sur le batch policy_reform du 21 août) :
même logique d'observation avant correctif, rattaché ici sous le même
principe plutôt qu'en entrée séparée.

---

## ⚪ S2. Bug #27 — plausibilité logistique inter-zones
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

## ✅ S3. Renommage des YAML génériques par dossier — CLOS (non retenu) le 6 octobre
Aucune gêne réelle en trois mois ; décision David : laissé tel quel.

---

## ⚪ S4. Troncatures JSON occasionnelles lors de la génération d'instances
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

**Mise à jour du 24 septembre** : un 3e cas (régénération Hyphan,
1 208 jetons de sortie) n'était **pas** une troncature — le JSON était
très probablement complet, suivi d'un commentaire après le bloc ```json,
et le filet de secours regex ne lisait que 2 niveaux d'imbrication. Les
cas du 11 août étaient peut-être de la même nature. Corrigé :
`extraire_json()` (`instance_generation_common.py`) tolère texte
avant/après, imbrication profonde et virgules finales ; en cas d'échec,
la réponse brute est sauvée dans `gui/logs/llm_json_echec_*.txt`.
**Au prochain échec, lire ce fichier** avant de conclure à une
troncature.

---

## ⚪ S5. Intégration GUI de `promote_ville.py`
**Nouveau, 19 août.** Script `promote_ville.py` livré et validé (voir BACKLOG_ARCHIVE.md
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

## ✅ S6. P14 — tier LLM `strict` vers `claude-sonnet-5` — CLOS (non retenu) le 6 octobre
Différé sine die depuis le 1er août ; retiré du backlog. À rouvrir seulement
si David le redemande.

---

## ✅ S7. Métaphores vs. descripteurs directs (`ton_personnel`) — CLOS (non retenu) le 6 octobre
Protocole de test jamais exécuté ; `set_ton_personnel.py` jugé suffisant.

---

## ⚪ S8. `--min-shingle` en dur dans `detect_registre_leakage()`
**Repéré le 19 août**, en marge d'un nettoyage de points reconfirmés
sans action. Le paramètre est fixé en dur à 6 mots (fonction partagée,
voir BACKLOG_ARCHIVE.md) — pourrait devenir un paramètre CLI si un
faux positif/négatif apparaît en usage réel. Aucun cas observé à ce
jour, pas de correctif tant que rien ne remonte.

---

## ⚪ S9. Confusion slug zone/instance — cas isolé
**Observé une fois le 4 août.** Échec LLM ponctuel : confusion entre
un slug de zone géographique et un slug d'instance sur une fiche —
résolu par retry, gardé en tête comme motif à surveiller si le même
symptôme réapparaît (pourrait indiquer que le prompt gagnerait à
lister explicitement les slugs de zones à ne PAS utiliser). Un seul
cas à ce jour, pas de correctif préventif.

---

## ✅ S10. `_index.md` réécrit en mode écrasement — CLOS (accepté) le 6 octobre
Jamais gênant ; tous les outils d'audit l'ignorent. Laissé tel quel.

---

## ✅ S12. Dérive `zones_pays.json` — CLOS le 26 septembre
Mesure avec la même règle que la Carte (`_entite_references_pays`) : 0 écart
sur les 6 scénarios après réaffectation de l'Italie (reference) et retrait
de 2 entrées parasites. Détail : `BACKLOG_ARCHIVE.md`.

---

## ✅ S13. Affectation depuis la Carte : entrée `origine_reelle` incomplète — CLOS le 25 septembre
Corrigé dans `zone_repository.py` (entrée complète, entrées overlay
préservées, zone créée au schéma complet). Détail : `BACKLOG_ARCHIVE.md`.

---

## ⚪ S14. Piège "couleur fantôme" Royaume-Uni/Angleterre/Écosse/Galles
**Surveillance seulement** (identifié le 8 sept, reporté de #2). Le
mécanisme multi-noms partageant un polygone peut laisser une couleur
fantôme si un seul des 4 noms est réaffecté. Au 23 sept, les 4 noms +
Irlande sont dans Zone Interdite de Heysham (`fortress_world`),
`check_conventions_territoires` cohérent. À revérifier si l'un d'eux
change de zone. Mineur connexe : `sao_paulo_megapole` (`fortress_world`)
n'a aucun pays dans son `origine_reelle` (2 alertes du garde-fou pour ses
sous-zones).

---

## ⚪ S15. Suites optionnelles du scénario Hyphan (fortress_world)
**Nouveau, 24 sept ; réduit le 26 sept** (Ergo-Wian/NAT faits le 25, texte
des géographies le 26 — voir `BACKLOG_ARCHIVE.md`). Reste, en attente d'un
besoin :
- **Milan** (QG du Mouvement de Reconquête européenne) et **Lyon** (son
  antenne) ne sont que des `lieu` en texte libre dans `zone_euro_sud`. En
  faire de vraies sous-zones si d'autres entités doivent y être placées —
  désormais en deux clics (Carte → ➕ sous-zone, S16).
- Personnages en réserve (exclus des articles) : Malo, Anton Vasko,
  Raimon, et Hyphan elle-même — à ré-autoriser via 🎯 quand le récit
  les fera apparaître.

---

## ✅ S16. Création directe de sous-zone dans le GUI — CLOS le 26 septembre
Carte → arbre d'une zone → « ➕ sous-zone » (aperçu puis création,
`ZoneRepository.creer_sous_zone`). Détail : `BACKLOG_ARCHIVE.md`.

---

## ✅ S17. Audit du lore — suites — CLOS le 26 septembre
Section sidebar « Relations & lore — étapes 1 → 5 » testée de bout en bout,
premier passage `--llm` réel, consignes IA durcies, règles `reference`,
correctif `write_alliances_patch()`, exceptions NAT supprimées. Détail :
`BACKLOG_ARCHIVE.md` et `HANDOFF_26_SEPTEMBRE.md`.

---

## ⚪ S18. Audit du lore — usage courant
**Nouveau, 26 sept.** Rien de bloquant :
- **Règles de lore des 4 autres scénarios** (breakdown, new_sustainability,
  eco_communalism, policy_reform) — seuls fortress_world et reference en
  ont. Faits établis à fournir par David quand le besoin se présente.
- **Relectures IA ciblées** au fil de l'eau (étape 4, `--limit 10` par
  scénario ≈ 5 centimes). Une passe complète (826 fiches) coûterait
  ~4-6 $ et produirait des milliers de propositions à trier.
- **Routine après chaque lot d'entités** : étapes 1 → 2 → 3 → `validate.py`.
- Pièges connus de slugs ≠ noms (l'IA s'y trompe) :
  `les_veilleurs_des_nappes_phreatiques` = Sentinelles des Aquifères
  Oubliés ; `conseil_regulation_algorithmique` = Autorité Numérique du Bloc
  Atlantique (à ne pas confondre avec `anba_siege_atlantique`, entreprise
  maritime). Renommage possible un jour, pas urgent.
- ~~`_a_supprimer/`~~ — **vidé et supprimé le 6 oct** (articles Hyphan,
  doublon Kharg-9, article test S26). Le dossier peut resservir pour retirer
  un article du site (il est hors `articles/`).

---

## ⚪ S19. Propagation dynamique — surveillance et réglages
**Nouveau, 27 sept.** Moteur `dynamique.py` en service (voir manuel §3ter).
Rien de bloquant :
- ~~`gui_verified: true` à remettre sur `trace_injection`~~ — fait (vérifié
  dans `scripts_config.json` le 27 sept après-midi).
- **Signaux faibles non propagés** : un signal avec `propagation_via_matrice:
  false` (le cas par défaut) agit sur sa variable cible, dans le calcul et
  donc dans les articles, mais ne se propage pas aux autres variables.
  Options non tranchées : **a)** passer certains signaux à `true` à la
  main ; **b)** changer la consigne du prompt `inject_custom_signals.py` ;
  **c)** propager tous les signaux à ~30 % de leur force. *Depuis le 27
  sept après-midi*, un signal `durable`/`permanente` pèse enfin en 2098
  sur sa variable (avant : ≈ 0,4 point résiduel, sous le seuil
  d'affichage) — la question de sa propagation aux autres variables reste
  entière.
- **Après un gros lot d'injections** : relancer `python3
  banc_calibration.py --scenarios all --balayage-k 0.05` et vérifier que
  les écarts restent lisibles. La stabilité est garantie par la garde
  `k_effectif`, pas la lisibilité.
- **Dérive de `reference` vers fortress_world** (géopolitique 75 → 86 en
  2098) : à surveiller, c'est peut-être voulu par le lore.
- **GAIN_CHOCS (0,25) et DEMI_VIE (20 ans)** relèvent du goût narratif :
  ils règlent la force des événements et la durée de leur trace, et
  peuvent être ajustés au banc sans toucher au reste. Depuis le 27 sept
  après-midi, la durée se règle aussi **par type** (`DEMI_VIE_PAR_TYPE`) et
  **par choc** (`persistance` : table `PERSISTANCE`) ; les instances
  actives sont `permanente` (`PERSISTANCE_INSTANCE_ACTIVE`, repli
  `durable` si l'effet paraît trop fort) — mesurer avec
  `mesure_niveaux.py` avant/après tout réglage.
- **Saturation près des bornes** : dans breakdown, 8 variables finissent
  entre 99 et 100 (référence déjà à 90-96) ; en new_sustainability,
  `gouvernance_institutions` descend à 0,3 (référence 10). Tout nouveau choc
  y est presque sans effet chiffré. Voulu par le plafond doux ; à revoir
  seulement si des articles en pâtissent (piste : référence moins
  extrême, ou marge du plafond).
- **Constats du simulateur « et si ? » (9 oct, S27)** : un choc déclaré
  « majeur » (invasion du Brésil, forces 8 à 20 sur 6 variables) ne
  déplace les niveaux que de **3 à 5 points au pic**, atteint en **15 à 20
  ans**, et il en reste 0,1 à 2,3 points en 2098. En breakdown et
  fortress_world, `geopolitique_conflits` saturée (≈ 99,7) n'enregistre
  presque rien. Un choc apaisant (fusion, forces 10 à 20) donne −3,5 à −5,4
  sur l'énergie, et c'est le premier test où les **tensions** changent
  vraiment (policy_reform 11 → 5). L'amplitude et la lenteur sont à juger
  avant tout réglage de `GAIN_CHOCS` ; aucun mode « rupture » n'existe (voir
  S27).
- `undo_custom.py` ne recalcule pas la ligne « Total » du registre des
  événements (mineur, cosmétique).
- `matplotlib` absent : le banc écrit des CSV au lieu de graphiques
  (`pip3 install matplotlib` si besoin).
- Tendances (`trend`) des fiches scénario : affichage seulement, aucun
  calcul ne les lit.

---

## ⚪ S20. Signaux faibles et idées en texte libre — suites possibles
**Nouveau, 27 sept (après-midi).** Rien de bloquant, pistes écartées ou
reportées explicitement :
- **Bouton « Proposer en événement »** dans la carte de l'assistant ✨
  quand le ⚠ « ressemble plutôt à un événement » apparaît — mis de côté
  par David (« voir à l'usage »).
- **Doublons d'idées** : le contrôle d'`id` de `idees_vers_queue.py` ne
  voit pas une idée déjà injectée sous un autre nom (cas réel : les
  prompteurs, déjà `clerge_prompteurs_ia`). Piste : comparer aux slugs de
  `signaux_custom/` (ne détecterait que des noms proches). Mis de côté.
- **Descriptions étoffées sur texte très court** (« chine 2049 champion
  économique » → 5 phrases et 4 variables) : David a choisi de ne pas
  ajouter de règle de longueur ; relire, ou « ↶ Rétablir mon texte ».
- **Reprise d'injection partielle** (`idee_a_remettre_en_queue`) : testée en
  synthétique seulement — à observer au premier cas réel. *1er oct* : le
  premier cas réel d'injection partielle venait d'une **exception**, que la
  reprise ne couvre pas (voir S22).
- **Portée narrative d'un signal** : un jalon de signal custom n'est
  jamais « structurant » dans `build_signal_trajectory()` (un
  `evenement_cle` par variable, jamais partagé) — « majeur » si sa
  variable est pilote du scénario, sinon « local » et rarement cité. Le
  multi-variables n'augmente pas son poids narratif. Constat, pas de
  décision.
- `/api/yaml/append` réécrit `queue.yaml` avec `yaml.dump` : l'en-tête
  modèle (`QUEUE_TEMPLATE`) disparaît jusqu'au prochain run du script
  d'injection, qui le remet. Cosmétique, préexistant.
- Entités : pas de champ `persistance` dans la queue de
  `create_entities_and_instances.py` (la persistance d'une instance se
  déduit de sa trajectoire ; forçage possible à la main dans le bloc
  `injection`). À ajouter seulement si le besoin se présente.

---

## ⚪ S21. Veille monde réel et signaux faibles — suites
**Nouveau, 28 sept.** Chaîne en production (manuel §3quater). Rien de
bloquant :
- **Injection des signaux** (lecture de `inject_custom_signals.py`) : les 6
  scénarios sont obligatoires, `polarite` ±1 (jamais 0) et un seul
  `delta_level` pour les 6. Chez Ansoff, beaucoup de signaux ne donnent
  rien dans certains futurs. Pistes, **notées pour plus tard par David** :
  **a)** « sans suite » autorisé par scénario (évolution narrative, sans
  effet chiffré) ; **b)** `delta_level` par scénario.
- **Livres** : 32 pages repérées restent dans le rapport JRC (≈ 4 passes).
  Documents à déposer repérés le 28 sept (liens dans le handoff) : ESPAS
  Horizon Scanning n° 10 (et précédents), JRC FUTURINNOV (Healing,
  Embodying, (Dis)Entangling, Observing…), PNUE Navigating New Horizons,
  WEF Top 10 Emerging Technologies 2025, ONU Horizon Scanning 2026.
- **Prompt des livres** : Mistral remplit le quota (3/3). Durcissement
  possible : une recommandation de l'auteur (« should », « would be »)
  n'est pas une observation ; un grand programme d'État n'est pas marginal.
- ~~**Option 1** (recherche web par API) et **option 2** (collecte locale
  RSS)~~ — **closes le 29 sept** (voir `BACKLOG_ARCHIVE.md`) : RSS en
  service (`veille_rss_api.py`, 16 flux, 15 depuis le 6 oct) ; recherche web par API essayée
  sur Mistral et non retenue. Suites possibles, sans urgence :
  - **Recherche en deux temps** (un appel court par variable, puis mise en
    forme limitée aux URL trouvées), si l'automatisation de la partie web
    devient utile : ~12 fois plus chère en recherches.
  - ~~**Hacker News**~~ — **retiré des flux le 6 oct** (`rss: null`,
    `.bak_hn`) ; reste proposé à l'IA de chat dans le prompt à coller.
  - **Crisis Group** : flux général du site (pas CrisisWatch), articles non
    datés.
  - **Pages complètes** au lieu des résumés des flux (articles réservés
    aux abonnés réduits à une ou deux phrases : STAT+, Rest of World, GEAB).
  - Relancer `verifier_flux_rss.py` de temps en temps (un flux peut
    changer ou mourir) ; une nouvelle source avec flux est lue
    automatiquement une fois son champ `rss` rempli.
  - Mistral reprend parfois des titres de « déjà repérés » malgré la
    consigne (rattrapé par l'import).
- **OCR** des PDF scannés : non fait (détectés et signalés).
- **Fusion multi-IA pour l'état du monde** : proposée (prompt de fusion
  collable, faits cités par ≥ 2 IA), laissée de côté par David.
- Onglet 🔭 : pas de bouton pour défaire une fusion ; si l'IA découpe un
  candidat en plusieurs idées, seule la première ajoutée compte.
- Idée à garder (Jabbour, ChatGPT) : repérer les signaux qui **relient**
  plusieurs variables (analyse en réseau via la matrice 12×12).
- `gui_verified` passé à `true` le 28 sept sur les trois entrées signaux
  faibles (testées chez David).
- **Ajout de sources RSS (30 sept)** : de façon ciblée, pas en masse. Critères
  : flux actif (article de moins de 30 jours), résumé exploitable, tendances
  plutôt qu'actualité chaude, angle absent des 16 flux actuels. Circuit :
  entrée ajoutée à la main dans `sources_signaux_faibles.yaml` (même format
  que les autres, `rss: null`, valeurs de `famille`/`variables` déjà
  présentes dans le fichier), puis `verifier_flux_rss.py --apply`. Idée non
  codée : un outil qui crée les entrées depuis une simple liste (nom + URL).
- **10 candidats RSS à trier** dans 🔭 (dont 2 plus faibles : Wegovy, BCE).

---

## ✅ S22. Injection des signaux — suites du 1er octobre — CLOS le 9 octobre
Confirmé en conditions réelles (signal `reseau_mobile_decentralise_urgence`,
idée « radio maillée chiffrée », 3 variables) : exception capturée et écriture
restaurée sans orphelin ; `"<1 ou -1>"` non recopié ; fence de
`geopolitique_conflits.md` réparée (séquelle de l'ancien bug d'`undo_custom.py`,
`.bak_fence`) ; recopie des événements frères corrigée
(`patch_s22_evenements_freres.py`), reprise passée du premier coup ; 18 lignes
au registre, validate 0/0/0. Détail : `BACKLOG_ARCHIVE.md`, manuel §3.
Restent en simple constat : avertissements « fenêtre déjà utilisée ».

---

## 🟡 S23. Génération d'articles — restes (3-4 oct)
**Clos pour l'essentiel le 4 oct** (signatures, lieu ≠ zone, 9 zones sans
journal, rezonage de 68 articles, réattribution de 94 signatures, erreurs
temporelles) — voir `BACKLOG_ARCHIVE.md` et `HANDOFF_4_OCTOBRE.md`. Reste :
- **`prompt_builder.py` (profils `JOURNAL_PROFILES`)** garde sa propre copie
  des noms de réseaux, en plus de `journaux.yaml` et `generate_journaux.py` :
  trois sources pour la même donnée. Non traité.
- **Lore reference à vérifier** : l'article Amazônia Viva
  (`20260924_101034_…`) fait de Hyphan Raghavan la dirigeante d'Ergo-Wian
  « depuis 2091 », alors que la règle du 26 sept la dit successeuse
  désignée. **Laissé tel quel le 5 oct** (décision David).
- **Hyphan** (5 oct) : exclue des articles dans les 5 scénarios hors
  `reference` ; les articles du lot forcé du 24 sept supprimés (6 oct).
  Ré-exclure après toute régénération.
- **Volume très inégal entre revues** — diagnostic du 5 oct (219 articles,
  « 📰 Audit des revues ») : Crieur des Marges 5, Courrier des Continents 6,
  Chronique 8, Miroir 8, Moniteur 11, Peuple Souverain 13, Journal des
  Normes 17, Lecteur des Communs 18 ; Radio Frontières 24, Contre-Courant 30,
  Limes 35, Revue de la Transition 44. Remonter toutes les revues à 15 :
  39 articles ; à 20 : 74. Génération reportée par David (séries ciblées :
  scénario + ligne éditoriale dans `config_series.yaml`). *6 oct* : en ligne
  (mois d'août), le Crieur des Marges n'a qu'**un** article. *9 oct* : +2
  articles (eco_communalism, opposition, société, Sri Lanka), produits par le
  test Large 3 / Large 4 (S29) ; pas encore de série ciblée.

---

## ⚪ S24. Suites techniques de S23 (4 oct)
Rien de bloquant :
- **`_slugify()` (`api.py`)** : ø, æ, å, ß, ł deviennent `_`
  (`eirik_b_rresen`), même famille que le bug portugais du 14 août.
  Corriger change les slugs existants ; `export_revues.py` lit
  maintenant les deux formes, donc plus d'effet visible sur le site.
- ~~**`_extract_byline()`**~~ — **clos (accepté) le 6 oct** : ne sert plus
  qu'en repli depuis le 25 août.
- **`generate_journaux.py --update`** : un lot au JSON cassé laisse des
  rédactions factices (7 cas le 3 oct). Nettoyage : `clean_fallback_journaux.py`
  (existant) ; `validate.py` les signale désormais. Piste : parse JSON
  tolérant, comme `fix_doublons_journalistes.py`.
- ~~**`nettoyer_placeholders_journaux.py`**~~ — **supprimé le 6 oct**
  (aucun appel ailleurs).
- **Outils d'audit S23** (`audit_signatures.py`, `audit_lieu_zone.py`,
  `audit_temporel.py`) : CLI seulement. `audit_signatures.py` n'exclut pas
  `_index.md` et n'emploie pas le slug du pipeline (6 faux positifs).
- **Ancrage local** : une zone qui n'a qu'une instance localisée reste
  dominée par des entités d'ailleurs (cas Maghreb). Créer des instances
  localisées dans les zones pauvres, si le besoin se confirme. *9 oct* :
  **Sri Lanka** n'a aucune instance localisée (« 0 locale(s) ») ; l'article
  tombe sur le Meclis, instance custom garantie d'eco_communalism.
- **Anomalies de données repérées par le simulateur S27 (9 oct)**, à vérifier
  à la main, rien n'a été modifié :
  - breakdown : **Uruguay** rattaché à `espace_nord_americain_fragmente`
    (l'IA y a placé une « alliance des cités portuaires sud-américaines »).
  - new_sustainability : le **Brésil** est porté par deux zones N1
    (`ameriques_reconfigurees` et `reseau_vivant_continental`).
  - reference : la sous-zone `sertao_nordeste_bresilien` déclare le
    **Paraguay (Chaco)** parmi ses territoires.
  - Doublons d'entités : eco_communalism, deux fiches « Pacte Amazônia Viva »
    (`amazonie_pacte_viva_eco_communalism`,
    `consortium_amazonia_viva_eco_communalism`) ; reference,
    `amazonie_consortium_viva_reference` et
    `consortium_amazonia_viva_reference`.
  - Beaucoup de fiches gardent la trajectoire **« émergent »** par défaut
    (18 propositions de la lecture IA partaient de là, souvent vers
    « dominant » ou « résiduel » d'un coup).
- **Bloc `===METADONNEES_PUBLICATION===` resté dans le texte** (5 oct) : 1
  article (education, policy_reform, 23 août, avec retry de longueur) ;
  réparé par `reparer_bloc_metadonnees.py`. Cause non vérifiée : relire
  l'extraction après retry dans `api.py`. Relancer le script de temps en
  temps (aperçu gratuit) — relancé le 6 oct : 0 article.
- **Doublon de génération Kharg-9** : voir S25.

---

## 🟡 S25. Kharg-9 surreprésenté sur le site — traité côté code le 6 oct, en surveillance
**Mesure du 6 oct** (articles du vault citant Kharg-9) : eco_communalism 13/22
(7 où il est le sujet), policy_reform 11/29, fortress_world 11/59, breakdown
3/18, new_sustainability 5/73, reference 0/14. Depuis le 22 août encore :
eco 5/8, policy 5/17, fortress 11/38. Dans 24 cas sur 27, il entre par la
**sélection d'instances** (`entites_citees`), pas par la géographie ni les
événements. Instance identique dans les 6 scénarios (impact 4/3, dominant).
Fait :
- **A — cooldown durci** pour toutes les instances (`loader.py`,
  `COOLDOWN_STREAK` 3 → 2, `COOLDOWN_DURATION` 2 → 3, `.bak_s25`) : ≈ 40 %
  de présence au plus (avant ≈ 60 %). Exemption de dominance inchangée.
- **C — exclusion** en eco_communalism (`set_selection_instance.py`).
- **D — doublon retiré du site** : *Le Nexus qui défie Genève* (Revue de la
  Transition, 10 mai). La paire « Dernier Souffle » (Limes / Moniteur)
  vérifiée : sujets différents, gardée.
- Piste **b** (baisser l'impact) écartée : 4/3 n'est pas extrême et changerait
  l'état du monde.
Reste : **mesurer l'effet de A** après les prochaines séries (même script de
comptage, articles postérieurs au 6 oct) ; l'IA recycle la description de
l'instance (« casino des données », « défie Genève-Nexus ») — si les titres
se répètent encore, retoucher `description_journalistique` de l'instance.

---

## ✅ S26. Journal couvrant un fait d'une autre zone — CLOS le 6 octobre
Mode Forcer, champ « Journal d'une autre zone » (liste déroulante,
`--forcer-zone-journal`) ; consigne « couverture d'un fait étranger » ;
`zone_principale` = zone du journal. Testé en réel. Détail : manuel §2 et
`BACKLOG_ARCHIVE.md`.

---

## 🟡 S27. Simulateur « et si ? » avant injection — v6 en service le 9 oct
**Fait le 9 oct** (voir manuel §3quinquies et `HANDOFF_9_OCTOBRE.md`) :
`generator/simuler_et_si.py` + `et_si/hypotheses.yaml` (à la racine du vault,
éditable). Lecture seule, rien n'est écrit dans le vault (seulement le rapport
`documentation/need_action/et_si_<id>.md`, le cache IA et l'état).
- **Étage A — niveaux** : `dynamique.simuler()` avec / sans l'hypothèse,
  écart en 2098, pics, tensions apparues / disparues / aggravées.
- **Étage B — lecture IA** (`--consequences-ia`, 1 appel
  `structured_strict` par scénario, ≈ 1-2 centimes) : lecture, ampleur,
  trajectoires, relations, statuts de zone, carte, nouvelles entités ;
  contrôle mécanique de chaque proposition, cache revérifié à chaque lecture.
- **Étage C — carte en aperçu** : `ZoneRepository.impact_bascule_pays`
  (rien n'est modifié), bloc `geographie:` manuel ou propositions de l'IA.
- **Faits imposés** (`contraintes:`, v6) : corrigent les idées reçues de l'IA
  sur un sujet technique (cas du tritium).
- Testé sur deux chocs : `invasion_bresil_2029` (agression locale) et
  `fusion_commerciale_2038` (technologie mondiale, polarité variable).
Reste, dans l'ordre proposé :
1. **Action « partition »** : couper un pays en morceaux nommés (zones
   occupées / résistantes), chacun rattaché à une zone existante ou nouvelle.
   Les six mondes la réclament pour le Brésil. Vérifier d'abord que la Carte
   gère un même pays dans plusieurs zones (`origine_reelle` + `portion`) :
   `grep -rn "portion" geographie/*.md | head -20`.
2. **Entrée GUI** (lancement, lecture du rapport, édition du fichier
   d'hypothèses ; graphique Chart.js comme le Tracer).
3. **Mode « rupture »** de l'étage A : le moteur amortit tout choc et ramène
   vers l'équilibre du scénario ; aucune bifurcation possible (lié à S19).
4. **Phase 3 — liste d'application** : tout ce que l'hypothèse impose de
   changer, dans l'ordre, avec l'outil à lancer, **à valider à la main** (l'IA
   propose encore des rattachements absurdes : Qatar dans le Pacifique,
   Australie dans l'espace eurasiatique). Trous identifiés : aucun outil pour
   migrer les journaux d'une zone qui disparaît ; instances et articles
   corrigés fiche par fiche seulement.
5. Phase 4 (optionnelle) : mode application.
Limites connues : la lecture IA varie d'un tirage à l'autre (le cache fige
le dernier ; `--refaire` en produit un autre) ; l'ampleur annoncée par l'IA
(« forte ») ne suit pas les écarts chiffrés, faibles (S19).

---

## ⚪ S28. Outils externes à greffer sur Ourrassol (pistes du 6 oct)
**Nouveau, 6 oct (recherche à la demande de David, après la comparaison avec
la Red Team Défense).** Cinq outils, chacun branché sur une brique existante.
Rien de décidé ni de codé ; ordre conseillé : 1, puis 3 ou 2.
1. **Analyse structurelle type MICMAC** sur `influence_matrix.md` (12×12) :
   influence et dépendance directes **et indirectes** de chaque variable →
   motrices / relais / dépendantes / autonomes. Vérifier que les variables
   pilotes sont bien motrices, repérer des leviers cachés. Gratuit, sans IA,
   quelques lignes de Python (ou paquet R `ISMtools`). Le plus simple.
2. **Analyse CIB (Cross-Impact Balance)**, logiciel ScenarioWizard (CIB-Lab,
   université de Stuttgart, version récente sur Zenodo ; licence et formats à
   vérifier) : liste toutes les configurations cohérentes d'un jeu de
   variables à états. Contrôler que les 6 scénarios sont stables et faire
   apparaître des configurations cohérentes non envisagées (réponse
   méthodique au manque de surprise). Demande de noter la matrice par états
   de variables, pas par niveaux.
3. **Base SSP de l'IIASA** (Shared Socioeconomic Pathways) : trajectoires
   chiffrées par région jusqu'en 2100 (population, PIB, urbanisation, énergie,
   émissions) pour 5 futurs, même famille que les 6 scénarios (fortress world
   ≈ SSP3, new sustainability ≈ SSP1, policy reform ≈ SSP2…). Ordres de
   grandeur pour les articles et repère pour les niveaux de variables.
4. **Prévisions collectives (API Metaculus)** pour le proche horizon
   2026-2035 : probabilités agrégées sur des milliers de questions, pour
   nourrir `etat_du_monde_reel.md` (« ce qui est jugé probable », pas
   seulement « ce qui s'est passé »). Conditions d'accès à vérifier.
5. **Détection de signaux en complément du RSS** : **GDELT** (base mondiale
   d'événements tirés de la presse, accès libre — montées encore marginales
   par pays/thème) et **OpenAlex** (API gratuite sur la publication
   scientifique — sujets dont le nombre d'articles décolle, dans l'esprit des
   catalogues JRC).
En marge : *Global Trends 2040* (National Intelligence Council, 2021 ; édition
2025 annulée en sept. 2025) comme grille de comparaison des scénarios et source
pour la veille état du monde ; idées « wild cards » et « passe équipe rouge »
tirées de la Red Team Défense (à rattacher à S27).

---

## ⚪ S29. Mistral Large 4 — rejuger à la sortie de l'aperçu
**Nouveau, 9 oct.** Évalué le 9 oct (voir `BACKLOG_ARCHIVE.md`) : branché
(`mistral-large-4` dans le sélecteur, `patch_llm_large4.py`), **non retenu par
défaut** — aucun tier changé. À rejuger si : il sort de l'aperçu, Mistral
permet de couper la réflexion, ou le tarif baisse. Avant tout usage hors
article : relever les `max_tokens`, la réflexion peut consommer tout le
plafond (réponse vide, cas réel au premier appel).

---

# PARTIE 3 — RISQUE STRUCTUREL IDENTIFIÉ (pas un bug actif)

**Aucun point actif.** Le seul risque identifié ici (instances custom
potentiellement non sélectionnées dans `filtered_instances`, depuis le
3 août) a été corrigé le 21 août — voir BACKLOG_ARCHIVE.md, chantier "Garantie
d'inclusion des instances custom (`loader.py`)".

---
