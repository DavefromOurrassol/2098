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
  que sur le dernier batch seul).

---

## ⚪ 2. Éditions datées (mensuel) — progression réelle du monde dans l'année
**Scopé le 30 août**, suite à une réflexion de David sur la parution à
dates régulières (ex. mensuel) avec cohérence temporelle des sujets
traités et continuité narrative entre éditions. **Diagnostic complet
fait, rien codé.**

**Constat de départ (lecture de `generate.py`/`snapshot.py`/
`generate_series.py`/`generate_manual.py`)** : `date_fictive` ne touche
**jamais** le contenu généré. `build_snapshot(scenario_slug,
thematique=None, dry_run=True, forcer_config=None)` n'a même pas de
paramètre de date. Confirmé par grep sur les 3 fichiers : `date_fictive`
ne sert qu'à `prompt_builder.py` pour la ligne "date de publication"
sous le titre — jamais transmise à `variable_states`/aux instances
sélectionnées. Deux articles datés "3 janvier 2098" et "22 décembre
2098" reçoivent un `variable_states` strictement identique. Les dates
elles-mêmes ne progressent pas : `generate.py` tire au hasard dans
`DATES_2098` (`random.choice`), `generate_series.py`/`generate_manual.py`
bouclent dessus (`% len(DATES_2098)`) — une liste fixe de ~20-24 dates,
toutes dans la seule année 2098, aucune notion d'édition ni de fenêtre.

**Un mécanisme existant s'en approche, mais n'est pas conçu pour ça** :
`apply_custom_events()`/`apply_custom_injections()`/`apply_custom_signals()`
(3 formules identiques, dupliquées) calculent `duree_effet = 2098 -
int(annee)` — **2098 en dur comme "présent" absolu du système**, plus
`snapshot["scenario"]["year"] = 2098` en dur également. Ce mécanisme
répond à "comment un événement du passé (2050, 2070...) irrigue encore
l'état du monde en 2098", pas à "que s'est-il passé le mois dernier
dans la même année" — un événement daté "2098" donne `duree_effet = 0`,
donc un effet quasi nul, l'inverse de ce qu'il faudrait pour une
progression mensuelle.

**Décision actée avec David (30 août)** : le monde doit **vraiment**
progresser dans l'année (pas seulement la sélection des sujets sur un
état par ailleurs figé) — option la plus ambitieuse des deux
envisagées.

**Piste retenue, à valider avant de coder** : généraliser les 3
formules dupliquées vers une vraie "date de référence de l'édition"
(fractionnaire, ex. `2098.08` pour août) plutôt que `2098` en dur. Les
`custom_events` **persistent déjà dans le vault** et se réappliquent à
chaque nouvelle génération — une fois ce calcul généralisé, chaque
édition mensuelle pourrait injecter ses propres `custom_events` (les
sujets réellement traités ce mois-là), qui irrigueraient automatiquement
toutes les éditions suivantes. **Ça répondrait aux deux besoins de
David avec un seul mécanisme** (progression du monde ET continuité
narrative entre éditions), plutôt que deux chantiers séparés.

**Reste à trancher avant de coder** :
- Généraliser les 3 formules dupliquées (`apply_custom_injections`/
  `apply_custom_events`/`apply_custom_signals`) + le `year: 2098` en
  dur du snapshot — vérifier aussi l'impact ailleurs dans le pipeline
  (`generate.py`, `prompt_builder.py`) où "on est en 2098" pourrait
  être supposé implicitement, pas vérifié à ce stade.
- Faire remonter la date de référence de l'édition jusqu'à
  `build_snapshot()` (paramètre absent aujourd'hui) depuis
  `generate_series.py`/`config_series.yaml`.
- Construire la notion d'édition elle-même (numéro, date de parution,
  fenêtre par rapport à la précédente) — n'existe nulle part
  aujourd'hui.
- **Comment les `custom_events` de chaque édition sont produits** :
  curation manuelle (comme aujourd'hui, `inject_custom_events.py`), ou
  extraction automatique depuis les articles réellement générés ce
  mois-là (séduisant mais nouveau mécanisme à concevoir : quels
  articles méritent de devenir des `custom_events` influençant la
  suite, avec quels deltas).

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
