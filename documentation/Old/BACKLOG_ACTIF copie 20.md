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
jour),
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
- **Guillemet orphelin dans des titres** (« Qui contrôle le récit… isruter ») :
  `nettoyer_corps()` retire le « de tête même quand il n'encadre pas tout le
  titre. Ne retirer les guillemets que s'ils encadrent le titre entier.
- **Photos** : brancher les images de `generate_images.py` (lié à #3 P20).
- **Audio** (*Radio Frontières*, journaux oraux `type_diffusion: oral`) :
  fichiers lourds → stockage Cloudflare R2 envisagé ; origine des extraits
  (synthèse vocale ou enregistrements) à décider.
- **Version multilingue** : isoler les libellés fixes par langue, pages sous
  `site/<langue>/`. Attention au plafond Cloudflare Pages (20 000 fichiers).
- Optionnel : titre réécrit par la revue et encadré « Contexte » (même appel
  que le chapô) ; protection d'accès Cloudflare pendant les tests ; bouton
  « Publier » dans le GUI ; références entre articles (David, à part).
- 17 articles non publiables, laissés tels quels : 8 sans `ligne_editoriale`
  (juin, décision du 7 sept), 9 sans `zone_principale` (8 fortress_world du
  21 août, antérieurs à la phase B de P20, et l'article Amazônia Viva).

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

## ⚪ S3. Renommage des YAML génériques par dossier
**Décision reportée une nouvelle fois le 14 août** (en pause depuis fin
juillet). `queue.yaml`/`processed.yaml`/`needs_review.yaml` répétés à
l'identique dans `entites_custom/`, `evenements_custom/`,
`signaux_custom/` — pas de collision technique (dossiers distincts),
juste une ambiguïté visuelle. Coût de migration identifié si un jour
tranché en faveur du renommage : constantes `QUEUE_PATH` dans 3 scripts,
entrées `scripts_config.json`, documentation (dont les `QUEUE_TEMPLATE`
eux-mêmes). Aucune urgence identifiée à ce jour.

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

## ⚪ S6. P14 — tier LLM `strict` vers `claude-sonnet-5` en prod
**Différé sine die** sur demande explicite de David (1er août). Pas un
oubli, une décision — à reconsidérer seulement si David le redemande.

---

## ⚪ S7. Métaphores vs. descripteurs directs (`ton_personnel`)
**Repéré le 29 août**, en marge du chantier `ton_personnel`. Question
non tranchée : privilégier des métaphores plutôt que des descripteurs
directs pour certains profils de ton personnel. Un protocole de test
empirique a été conçu mais jamais exécuté — **David a choisi de mettre
la piste de côté**, `set_ton_personnel.py` jugé suffisant tel quel pour
le moment. Aucune décision de fond prise ; à reprendre seulement si un
besoin réel se manifeste en usage.

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

## ⚪ S10. `_index.md` réécrit en mode écrasement, pas cumulatif
**Repéré le 15 août.** `articles/{scenario}/_index.md`, généré par
`generate_series.py` (`build_index()`), ne liste que les articles du
dernier batch à chaque run sur un même scénario — pas un cumul
historique de tous les articles jamais générés. Pas vérifié comme
gênant en pratique. À réévaluer si un historique cumulatif devient
utile (ex. navigation Obsidian sur l'ensemble d'un scénario plutôt que
sur le dernier batch seul). Sans incidence sur les outils d'audit/
inventaire (depuis le 5 septembre) : tous scannent le dossier
directement et excluent explicitement les fichiers `_index.md`.

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
- `_a_supprimer/` : article du 24 sept (Hyphan en Asie centrale) à
  supprimer définitivement quand David le décide.

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
  service (`veille_rss_api.py`, 16 flux) ; recherche web par API essayée
  sur Mistral et non retenue. Suites possibles, sans urgence :
  - **Recherche en deux temps** (un appel court par variable, puis mise en
    forme limitée aux URL trouvées), si l'automatisation de la partie web
    devient utile : ~12 fois plus chère en recherches.
  - **Hacker News** : flux sans texte (titres seuls), ignoré à chaque
    passe ; retirer son champ `rss` ou lire les pages liées.
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

## ⚪ S22. Injection des signaux — suites du 1er octobre
**Nouveau, 1er oct.** 5 signaux injectés après correctifs (`+1` toléré dans
le JSON, plancher de bascule ; voir manuel §3, `inject_custom_signals.py`).
Reste :
- **Exception en cours d'injection = signal orphelin** (bug réel, non
  corrigé, **à traiter en priorité**) : si une exception survient après
  l'écriture d'une première variable, `main()` envoie l'idée entière en
  `needs_review` (champ `error`), sans fiche d'audit ni
  `idee_a_remettre_en_queue`. Le signal reste dans la fiche variable et le
  registre, sans impact chiffré. Cas réel le 30 sept
  (`ia_agents_autonomes_evasion` dans `gouvernance_institutions`, nettoyé
  avec `undo_custom.py`). Piste : capturer les exceptions par variable dans
  `process_idea()`, pour que la fiche d'audit et la reprise s'appliquent
  comme pour un échec de validation.
- **Option** : remplacer `"<+1 ou -1>"` par `"<1 ou -1>"` dans l'exemple JSON
  de l'étape 2, pour supprimer le `+` à la source (le correctif du parsing
  reste en filet de sécurité). L'emplacement avait été choisi le 27 sept parce
  qu'un exemple chiffré était recopié tel quel : vérifier que ça ne revient
  pas.
- **Événements recopiés entre variables d'un même signal** : malgré
  `sibling_events`, Mistral reprend parfois les `evenement_cle` qu'il vient
  d'écrire pour la variable précédente (Mumbai, Tuvalu le 1er oct). Rattrapé
  par la validation et une relance ; à surveiller, ça coûte un appel.
- **Avertissements « fenêtre déjà utilisée »** très fréquents (quasi
  systématiques sur les 12 variables) : non bloquants par décision du 26
  juillet ; les fenêtres convergent vers les mêmes plages. Constat, pas de
  décision.
- **Origine de la fence manquante** dans `organisation_territoires.md`
  inconnue (`undo_custom.py` avalait la fence autrefois, corrigé depuis).
  Si ça se reproduit, chercher quel outil a écrit le fichier en dernier.

---

## 🟡 S23. Génération d'articles — anomalies révélées par le site (3 oct)
**Nouveau, 3 oct. Sujet de la prochaine session.** Le site rend visibles des
défauts des articles générés :
- **Lieu de l'article ≠ zone de son journal** : trois journaux de zones
  différentes (*The Indo-Pacific Herald*, *El Otro Lado de la Frontera*, *Le
  Glacier Bleu*) traitent du même Nœud Mnemos de Tbilissi ; *The Broken Ledger*
  (Amérique du Nord, breakdown) écrit sur Lyon et Sfax ; *Isbjørnens Vrede*
  (Nordark) « depuis Lagos-Est ». À comprendre : comment `zone_principale`
  (`_dominant_zone()`) et le journal sont choisis par rapport au sujet.
- **Signatures** : 73 / 218 articles avec `journaliste_slug` vide (31) ou
  inconnu de `journaux.yaml` (42). Lien avec P25 (S1). Vérifier dans
  `prompt_builder.py` si la coquille `europe_occidentale_reconstructee`
  (corrigée le 3 oct) faisait signer au nom du réseau.
- **`prompt_builder.py` (l. 748-876)** garde sa propre copie des noms de
  réseaux, en plus de `journaux.yaml` et `generate_journaux.py` : trois
  sources pour la même donnée.
- **Erreur temporelle** : un article de 2098 prévoit un effondrement « d'ici
  2070 » (`20260924_101034_reference_environnement_climat_article_10aout2098.md`).
- **Slug fabriqué depuis une ligne de date** :
  `23_novembre_2098_troms_n_ud_nordark` (breakdown).
- **Lore reference à vérifier** : le même article fait de Hyphan Raghavan la
  dirigeante d'Ergo-Wian Sovereign Holdings « depuis 2091 », alors que la règle
  du 26 sept la dit successeuse désignée.
- Volume très inégal entre revues (de 4 à 44 articles publiés) : à rééquilibrer
  par la génération, toutes zones et thématiques devant être couvertes à terme.

---

# PARTIE 3 — RISQUE STRUCTUREL IDENTIFIÉ (pas un bug actif)

**Aucun point actif.** Le seul risque identifié ici (instances custom
potentiellement non sélectionnées dans `filtered_instances`, depuis le
3 août) a été corrigé le 21 août — voir BACKLOG_ARCHIVE.md, chantier "Garantie
d'inclusion des instances custom (`loader.py`)".

---
