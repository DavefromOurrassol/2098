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

## 🟡 2. Suite narrative des événements + détection de basculements (5 septembre — EN COURS, non clos)
**Ouvert le 5 septembre.** Objectif : permettre aux articles de
construire une vraie continuité narrative sur les événements custom
plutôt que de repartir d'une fiche statique à chaque génération.
Découpé en 4 points par David : A (champ de lien article→événement),
B (outil d'audit par sujet, événements ET entités, toutes dates), C
("Promouvoir un sujet en événement" — champ `developpements` cumulatif
sur l'instance, rapatrié via B), D (génération Forcer enrichie +
option d'évolution de l'événement/entité). Étendu en cours de session
vers un chantier annexe : détection de basculements narratifs dans les
articles déjà publiés.

**Point A — codé et testé, CLOS.** Nouveau champ `evenements_cites`
(+ `evenements_cites_source`) dans le frontmatter — écrit dans
`api.py::build_article_md()` uniquement quand `forcer_resolu["type"]
== "evenement"` (déterministe, aucun appel LLM, garanti par
`forced_angle_directive` de `snapshot.py`). Testé en conditions
réelles (article forcé sur `accord_carbone_amazonie_blocs_new_
sustainability`).

**Rattrapage rétroactif — tenté puis ABANDONNÉ.** Nouveau script
`detect_evenements_cites_retroactif.py` (reste disponible si un vrai
cas se présente un jour, mais pas utilisé activement). Trois
itérations de critère de détection avant abandon : vocabulaire seul
(65/74 faux positifs sur new_sustainability — vocabulaire trop
générique à cet univers), acteur OU année (69/74 — les acteurs sont un
pool d'institutions récurrent partagé par presque tous les articles),
acteur ET année en intersection (16/74 candidats raisonnables → 7/16
confirmés par LLM avec la consigne initiale, mais vérification
manuelle a trouvé un faux positif — citation en exemple, jamais
développée → consigne resserrée à "SUJET CENTRAL" → 0/16 confirmés,
et 0/7 sur eco_communalism). **Conclusion testée sur 2 scénarios (95
articles) : aucun article ancien ne développe un événement comme sujet
central**, seulement en toile de fond/précédent/exemple. Décision de
David : ne pas tester les 4 scénarios restants, pattern jugé net. Les
206 articles déjà publiés ne nourriront donc jamais `developpements`
rétroactivement — seuls les forçages futurs le pourront. Outil de
debug annexe `debug_test_evenement_central.py` (verdict + justification
par candidat, pour calibrer une consigne sur des cas choisis à la
main) — a aussi révélé que le LLM peut halluciner des slugs
d'événements plausibles à partir du texte au lieu de juger les
candidats fournis, quand la liste n'est pas pré-filtrée (corrigé par
validation stricte des slugs retournés).

**Point B — construit et testé, CLOS.** `audit_sujets.py` (lecture
seule) : `--list-evenements` (catalogue par scénario, trié
chronologiquement sur le champ `date` numérique — pas sur `date_label`,
texte libre à granularité variable) et audit d'un sujet (événement ou
entité) sur toutes les dates, avec signal `POSTÉRIEUR AU MOIS DE
PARUTION ACTIF`. `editer_sujets.py` (destructif, garde-fous) :
suppression d'article → déplacement vers `_corbeille/{scenario}/`
horodatée (jamais de suppression définitive), modification de
`date_evenement` → sauvegarde préalable dans `_backups/` + renommage
de fichier cohérent (fragment de date sans accent) + synchronisation
conditionnelle de `date_publication`. Tout derrière `--apply`/
`--dry-run`, journal append-only `_corbeille/journal_actions.jsonl`.

Intégration GUI : onglet "Audit par sujet" (section entités-création)
+ nouvel onglet top-level **"Articles"** (demandé explicitement par
David — même gabarit que "Rédaction" : table triable/filtrable/
paginée sur tout l'inventaire, filtrage 100% côté client, panneau de
détail réutilisant les mêmes actions Supprimer/Modifier-date via des
fonctions JS généralisées). 6 nouvelles routes Flask (`/api/sujets/
evenements`, `/api/sujets/audit`, `/api/sujets/supprimer_article`,
`/api/sujets/modifier_date`, `/api/sujets/inventaire`, `/api/articles/
liste`). Testé en conditions réelles par David de bout en bout : audit,
suppression réelle, modification de date réelle avec renommage,
onglet Articles (filtres, tri, panneau, actions).

Nouvel outil annexe `audit_inventaire_articles.py` : inventaire complet
lecture seule (tous scénarios), résumé + détail, export `--md` (natif
vault, `documentation/inventaire_articles.md`, recommandé) et `--csv`
(secondaire, tableur externe) — confirmé cohérent avec les stats du
dashboard existant (211 articles, mêmes répartitions).

**Points C et D — PAS CODÉS.** Le risque de redite qui a motivé ce
chantier au départ n'est donc **toujours pas résolu** : forcer deux
fois le même événement aujourd'hui repart chaque fois de la même fiche
statique (`description`/`consequences`/`realisation`), sans aucune
connaissance de ce qu'un article précédent a raconté. Seule la
détection après coup (`evenements_cites`) existe.

**Détection de basculements narratifs (extension, en cours).**
Vérifié avant de construire : `tension_level`/`scenario_state` sont
CONFIRMÉS STATIQUES par scénario (lus une fois depuis `scenarios/
{slug}.md` via `loader.py::load_scenario()`, jamais recalculés par
article) ; `variables_pilotes` ne liste que des noms de variables,
jamais de niveau numérique — aucune donnée structurée gratuite
n'existe pour détecter un basculement dans le temps, seule la lecture
du texte le peut. Scope tranché avec David : tout le corpus (200+
articles), granularité CHAPO SEUL (pas le corps complet), sortie en
rapport simple à parcourir à la main (pas de création automatique
d'événement). Nouvel outil `detect_basculements_narratifs.py` : un
seul appel LLM PAR SCÉNARIO (tous les chapos triés chronologiquement
dans un même prompt, pas un appel par article — 6 appels au lieu de
200+), catégories aggravation/amelioration/deblocage/blocage/
emergence_crise/autre, même garde-fou anti-hallucination de fichier
que le script de rattrapage.

Testé sur `new_sustainability` (73 articles, 1 seul appel LLM, 10576
tokens entrée / 1530 sortie) : 10 candidats/73 (~14%), justifications
cohérentes avec le lore réel du scénario (Kharg-9, CGAI, IA Seuil,
APRC), types variés mais **aucun `amelioration`/`blocage` détecté** —
biais réel du scénario (qui semble structurellement orienté vers la
dégradation) ou biais du LLM, pas encore tranché. Plusieurs candidats
partagent la même date fictive (dates réutilisées entre batches de
génération, phénomène déjà connu du pipeline). **Pas encore vérifié
manuellement contre le texte intégral** (seulement le chapo a été lu
par le LLM), **pas encore testé sur un 2e scénario**.

**Trou de plomberie découvert, PAS RÉSOLU** : l'écran GUI "Promouvoir
un événement" (chantier "Mois de parution", archivé) ne liste que les
articles du MOIS DE PARUTION ACTIF (appelle `audit_sujets_edition.py`
sans année/mois précis) — or les candidats de basculement viennent de
dates éparpillées dans toute la chronologie, la plupart hors du mois
actif, donc non sélectionnables tels quels dans cet écran. Incertitude
non vérifiée à trancher avant de coder quoi que ce soit : est-ce que
la date de l'événement créé se cale automatiquement sur le mois de
parution actif plutôt que sur la date réelle de l'article source
(`inject_custom_events.py::process_idea()`, champ `edition_active` —
fichier pas revu sous cet angle cette session) ? Piste proposée mais
pas actée : ajouter l'action "Promouvoir en événement" directement
dans le panneau de détail du nouvel onglet Articles (qui n'a pas cette
limite de mois), à côté de Supprimer/Modifier-date.

**Reste à faire, dans l'ordre logique** :
1. Vérifier `inject_custom_events.py::process_idea()` sur la gestion
   de la date avant de toucher au process de promotion.
2. Décider et coder l'action "Promouvoir en événement" dans l'onglet
   Articles (ou une autre solution à la limite de mois).
3. Vérifier manuellement 1-2 candidats de basculement contre le texte
   intégral ; tester sur un 2e scénario.
4. Lancer `detect_basculements_narratifs.py` sur tout le corpus une
   fois le process aval réglé.
5. Coder le point C (`developpements` cumulatif) et le point D
   (option d'évolution en mode Forcer) — condition pour que le risque
   de redite initial soit vraiment résolu.

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
