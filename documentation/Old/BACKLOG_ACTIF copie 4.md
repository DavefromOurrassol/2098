# Backlog actif — Ourrassol 2098
*Dernière consolidation majeure le 23 août 2026, mis à jour en continu
à chaque clôture de session. Chantiers clos et leur historique complet
dans `BACKLOG_ARCHIVE.md` (fichier séparé, à uploader seulement en cas
de besoin de vérifier si un point a déjà été traité). Chaque chantier
a un nom stable — à réutiliser tel quel dans les prochaines sessions
pour éviter toute nouvelle divergence de nommage.*

---

# PARTIE 1 — CHANTIERS OUVERTS (à traiter)

---

## 🟢 1. P20 — Enrichissement frontmatter pour publication web (Phases A+B+C codées, service image à brancher)
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

---

## 🟢 2. Suite narrative des événements + détection de basculements — CLOS le 6 septembre
*Ouvert le 5 septembre (points A/B clos ce jour-là), points C/D et
l'extension "détection de basculements" clos le 6 septembre après
tests réels complets. Détail complet (logs, exemples, textes de
consigne) dans HANDOFF_6_SEPTEMBRE.md — à copier dans
BACKLOG_ARCHIVE.md. Résumé ci-dessous pour ne pas reperdre le fil.*

- **Points C/D codés et testés.** Nouveau champ `developpements`
  (liste cumulative sur la fiche instance d'un événement —
  `date_label`/`article_slug`/`resume`, `resume` = chapo déjà généré,
  aucun appel LLM supplémentaire), alimenté par `api.py::save_article()`
  après chaque forçage `sujet_central` réussi ; réécriture ciblée du
  fichier par substitution de texte (jamais de round-trip YAML complet,
  sauvegarde automatique dans `_backups/`). `forced_angle_directive`
  (`snapshot.py`) injecte l'historique au LLM lors d'un nouveau forçage
  sur le même événement ("Développements déjà racontés... poursuis
  l'histoire"). Testé en conditions réelles sur 2 forçages successifs
  du même événement (cas Sahel, `revolution_travail_sahel_numerique_
  policy_reform`) : accumulation confirmée (2 entrées, fichier intact
  par ailleurs), 2e article véritablement une suite (offensive
  institutionnelle, classement Kontinuum) plutôt qu'une redite.
- `evenements_cites`/`developpements` resserrés sur `mode ==
  "sujet_central"` — sans effet observable aujourd'hui : `generate.py`
  force TOUJOURS ce mode depuis une décision du 2 août (docstring du
  module) ; le mode "ingredient" est du code mort dans l'architecture
  actuelle du forçage, jamais atteignable en pratique. Resserrement
  gardé par cohérence/anticipation, pas correctif d'un bug actif.
- **Trou de plomberie résolu.** Action "Promouvoir en événement"
  intégrée dans le panneau de détail de l'onglet Articles plutôt que
  dans l'ancien écran (limité au mois de parution actif) — celui-ci a
  été entièrement retiré du GUI (nav, tab HTML, CSS dédiée), la route
  backend `/api/edition/injecter_evenement` réutilisée telle quelle
  (déjà neutre sur tous les champs). Date approximative (année)
  éditable, pré-remplie avec la vraie date de l'article ;
  `edition_active` décoché par défaut (inverse de l'ancien écran).
  Filtre "Mois en cours seulement" ajouté à l'onglet Articles pour
  garder l'usage rapide (case grisée si aucune édition n'a jamais été
  enregistrée).
- **Incohérence de dates corrigée (cas contemporain).** Nouveau champ
  `date_precise` (date complète de l'article source) envoyé en plus de
  `date_approximative` (année seule) — consigne LLM distinguant
  explicitement un article contemporain de l'événement qu'il décrit
  (ancrage sur la MÊME SAISON, sans exception de dérive) d'un article
  rétrospectif (anniversaire/référence historique — ignorer la date de
  l'article, suivre la période suggérée par le récit). 1er essai réel
  a échoué (formulation avec clause d'échappement ±10 ans trop large,
  appliquée aux deux cas) — resserré (drift réservé au seul cas
  rétrospectif) puis validé en conditions réelles sur le cas contemporain
  (Milwaukee-Basse, ancrage correct après correctif). Cas rétrospectif
  ambigu (anniversaire interprété comme l'événement de la célébration
  plutôt que l'origine commémorée, cas Sahel) — limite acceptée avec
  David, pas de correctif supplémentaire.
- **`detect_basculements_narratifs.py` vérifié et intégré au GUI.**
  Vérification manuelle contre le texte intégral sur 3 candidats du
  scénario `reference` (séquence cohérente 27 mai → 4 juin → 19 juin) :
  sélection fiable 3/3, mais catégorisation (`type_bascule`) fausse sur
  1/3 (19 juin classé "déblocage" sur la foi du chapo seul, en réalité
  une poursuite de l'aggravation une fois le texte intégral lu — rejet
  institutionnel de la charte de Väinälä, nouvelle censure) : le champ
  est une indication à vérifier, pas une classification fiable telle
  quelle — décision actée, pas de correctif (limite du chapo seul,
  cohérente avec le scope tranché le 5 septembre). Testé aussi sur
  `reference` en plus de `new_sustainability` (5 septembre) : le
  scénario `reference` produit bien un `deblocage`, ce qui penche pour
  un biais du scénario `new_sustainability` plutôt qu'un biais
  systématique du LLM sur cette catégorie — pas définitivement tranché
  sur un seul scénario supplémentaire.
  Intégration GUI (onglet Articles) : cache persistant
  (`state/basculements_narratifs.json`, fusion par scénario — un scan
  partiel ne fait jamais disparaître les résultats des autres),
  nouvelles routes `GET /api/articles/basculements` (lecture seule) et
  `POST /api/articles/lancer_basculements` (relance à la demande,
  scénario optionnel, timeout 600s), case "Basculement narratif
  détecté" (grisée sans cache), bouton de relance, encart dans le
  panneau de détail (type + justification + rappel "catégorie
  indicative, vérifie contre le texte intégral"). Bug de chemin trouvé
  et corrigé en cours de route : le cache s'écrivait sous le vault
  Obsidian (`VAULT_ROOT/state/`) au lieu du dossier des scripts
  (`pipeline_dir/state/`, même convention que `state/editions.json`) —
  le GUI ne le trouvait donc jamais.
- **Nouveau, hors scope initial, PAS comblé.** Catalogue d'entités pour
  l'audit par sujet (onglet "Audit par sujet") : le type "Entité" n'a
  aucun catalogue contrairement aux événements — juste un champ texte
  libre demandant de connaître le slug exact, peu exploitable pour un
  usage exploratoire. Limite identifiée en testant l'audit par sujet,
  David a choisi de ne pas la traiter cette session.
- **Deux ajustements UX supplémentaires sur l'onglet Articles**,
  demandés en cours de session : la fiche de détail se ferme
  désormais au changement de filtre ou au clic en dehors du
  tableau/panneau (bug de fermeture immédiate trouvé et corrigé —
  `e.target.closest()` cassé par le re-rendu du tableau au clic sur une
  ligne, remplacé par `e.composedPath()`, insensible à l'ordre de
  rendu) ; nouveau bouton "Ouvrir dans Obsidian" (schéma d'URI natif
  `obsidian://open?vault=...&file=...`, aucune route backend
  nécessaire — réutilise `vault_root` déjà chargé dans `/api/config`).
- **Bug de fond trouvé en fin de session, corrigé** : `validate.py`
  interdisait aux événements custom d'être datés 2098 (borne
  `[2025-2097]` en dur, reliquat d'avant le chantier "Mois de
  parution") — 3 fausses erreurs sur des événements légitimement créés
  aujourd'hui. Diagnostiqué en 2 itérations : une borne dynamique liée
  à l'édition active a été implémentée puis **abandonnée** (les
  articles peuvent être préparés à l'avance et datés au-delà de
  l'édition active, plusieurs éditions couvrant différents mois de la
  même année 2098) ; borne fixe **[2025, 2098]** retenue à la place
  (2098 = année finale de la fiction), appliquée dans `validate.py`
  (règle événements + `annee_injection`) et `inject_custom_events.py`
  (`clamp_date_dans_plage()`, consigne LLM simplifiée). Recherche
  confirmée sur tout `generator/` : aucune autre occurrence de "2097" à
  corriger. Détail complet dans HANDOFF_6_SEPTEMBRE.md.

---

---

**Nettoyé le 19 août** — retrait des points reconfirmés à plusieurs
reprises sans jamais avoir mené à une action (aucune condition de
réouverture identifiée) : anomalie `coverage_proposals_reference.yaml`
sans `.applied`, route dormante `/api/carte/appliquer_zone_topdown_suspecte`,
champ `type` des zones géographiques jamais utilisé dans le prompt.
`constrained_variables` retiré de cette liste pour la raison inverse —
traité et résolu, voir BACKLOG_ARCHIVE.md. Bloc `simulation` retiré également,
pour la même raison inverse — P22 a confirmé et résolu son statut le
20 août (câblé dans `snapshot.py`, opérationnel), voir BACKLOG_ARCHIVE.md.

- `--min-shingle` de `detect_registre_leakage()` (fonction désormais
  partagée, voir BACKLOG_ARCHIVE.md) fixé en dur à 6 mots — pourrait devenir un
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
  que sur le dernier batch seul). Sans incidence sur les nouveaux
  outils d'audit/inventaire (5 septembre) : tous scannent le dossier
  directement et excluent explicitement les fichiers `_index.md`.

---

*Chantier "Mois de parution (éditions datées)" + son extension
"Promouvoir un événement" — clos le 3 septembre, testés en conditions
réelles par David (génération réelle, écran "Mois de parution du
journal", écran "Promouvoir un événement", bandeau série). Archivés
dans `BACKLOG_ARCHIVE.md`. Documentation complète : §2quinquies de
`USER_MANUAL_COMPLET.md`. Point restant, pas une tâche : observer le
risque de formulation temporelle relative incohérente sur plus de
volume avant d'envisager un correctif (cohérent avec P17/Bug#27). Voir
aussi le chantier 2 ci-dessus (5 septembre) : l'écran "Promouvoir un
événement" issu de ce chantier montre une limite (mois de parution
actif uniquement) qui n'était pas apparue lors de sa clôture.*

---

## Secondaire — différé, pas d'action tant que rien ne remonte
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

# PARTIE 3 — RISQUE STRUCTUREL IDENTIFIÉ (pas un bug actif)

**Aucun point actif.** Le seul risque identifié ici (instances custom
potentiellement non sélectionnées dans `filtered_instances`, depuis le
3 août) a été corrigé le 21 août — voir BACKLOG_ARCHIVE.md, chantier "Garantie
d'inclusion des instances custom (`loader.py`)".

---
