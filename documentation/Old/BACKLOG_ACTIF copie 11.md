# Backlog actif — Ourrassol 2098
*Dernière consolidation majeure le 23 août 2026 (reconsolidé le 23
septembre 2026 : #2, #2bis, #4 et S11 clos et archivés), mis à jour en continu
à chaque clôture de session. Chantiers clos et leur historique complet
dans `BACKLOG_ARCHIVE.md` (fichier séparé, à uploader seulement en cas
de besoin de vérifier si un point a déjà été traité). Chaque chantier
a un nom stable — à réutiliser tel quel dans les prochaines sessions
pour éviter toute nouvelle divergence de nommage.*

---

# PARTIE 1 — CHANTIERS OUVERTS (à traiter)

---

## 🟢 1. Scénario 1 — Hyphan : worldbuilding géographique + zones fortress_world
**Ouvert le 8 septembre.** David a fourni le premier jet narratif du
scénario Hyphan (apartheid corporate/militaro-industriel, Ergo-Wian,
migrations forcées) plus les cartes annexes du docx. Scénario porteur
tranché : **fortress_world** (breakdown écarté, lore incompatible déjà
établi sur les mêmes territoires — Occitanie/Cellules Racines-Mères).

**Fait le 8 septembre** : liste complète des personnages/entités/
événements/zones candidats à l'injection extraite du texte (pas encore
transformée en fiches réelles). Zones créées dans le vault réel : **Al-Hima**
(Espagne/Portugal/Maroc/Algérie, via split de Bloc Atlantique), **Zone
Interdite de Heysham** (Angleterre/France, via split de Bloc Atlantique,
remplace le nom provisoire "Zone de Hartlepool"). **Nuuk-Forteresse**
reparentée sous **Espace Nordique et Arctique** (niveau 1 → niveau 2).

**Fait le 9-10 septembre** : Interzone renommée **Zone Euro Sud** (via le
bouton ✏️ Renommer du GUI — fonction dédiée découverte en cours de
session, existe depuis le 13 juillet). Bug Royaume-Uni/Zone Interdite de
Heysham (désaffectation qui ne tenait pas) diagnostiqué et corrigé —
cause : entrée "Royaume-Uni" orpheline dans l'`origine_reelle` de Heysham,
retrouvée à chaque resynchronisation. Nouvelle zone **Interzone Corridor**
trouvée dans le vault (créée par David hors session Claude) — couleur
personnalisée enregistrée mais **tracé overlay jamais créé côté serveur**,
à redessiner. Voir `HANDOFF_10_SEPTEMBRE.md` pour le détail complet.

**Fait le 12 septembre** (voir `HANDOFF_12_SEPTEMBRE.md` pour le détail
complet — chantier surtout consacré à la refonte Carte, chantier #2) :
- **Zone Euro Sud, nombre de pays tranché** : 26 pays via `zones_pays.json`
  (assignation pays-entier), 28 entrées dans `origine_reelle` — l'écart
  n'était pas une erreur, ce sont Allemagne et Pays-Bas, présents
  uniquement via overlay (portion partielle), donc absents à raison de
  l'index pays-entier. Rien à corriger.
- **Doublon Turquie trouvé et corrigé** (présente dans `origine_reelle` de
  `zone_euro_sud` ET d'une nouvelle zone top-down `anatolie_forteresse_
  eurasiatique` créée en session — la création top-down ne retirait pas
  l'ancienne affectation). Fix structurel apporté à `creer_zone_n1()` :
  toute création retire désormais automatiquement le pays des autres
  zones qui le référençaient.
- **Interzone Corridor** : renommée "Interzone Corridor Test" en cours de
  session (test du bouton Renommer), restée invisible sur la carte (son
  tracé n'a toujours jamais été dessiné — confirmé via un nouveau
  diagnostic, `diagnostiquer_zones_invisibles.py`). **David a choisi de
  la supprimer entièrement** (nouvelle capacité `supprimer_zone_n1`,
  construite cette session) pour repartir de zéro plutôt que de continuer
  à réparer l'existant — **à recréer proprement**, voir Reste à faire.

**Statut au 23 septembre : EN PAUSE sur décision de David.** Seuls deux
points ont avancé en marge d'autres chantiers : `tensions_internes`/
`periode_transition`/`evenement_transition` de Zone Interdite de Heysham
renseignés (premier test réel du panneau "Zones à enrichir"), et
Royaume-Uni affecté à Heysham par David (entrée `origine_reelle` au format
minimal, voir S13).

**Reste à faire** :
- **Recréer Interzone Corridor proprement** (supprimée le 12 sept pour
  repartir de zéro) et dessiner ses tracés pays par pays via le panneau
  unique (bouton "✏️ dessiner" par ligne de pays). **Clarifier au passage
  le sens de "Interzone"** : la description de Heysham parle des
  "pillards de l'Interzone" — ancien nom de Zone Euro Sud, ou futur
  Interzone Corridor ? Corriger la description si c'est un reste.
- Créer Nordgard (niveau 1, Pays-Bas comme point de départ), Corridor
  d'Amsterdam, Zone de Koursk — discutées/nommées, **pas confirmées
  créées dans le vault réel**, à vérifier en début de session plutôt que
  supposer.
- Injecter dans le vault les personnages/entités/événements extraits du
  texte Hyphan (liste déjà faite, jamais transformée en fiches).
- **Partage France / Allemagne à trancher (constats du 23 sept,
  `check_overlay_portion_coherence.py` + `diagnostiquer_portions_
  orphelines.py`)** — aucune correction faite, car chacune revient à
  décider qui possède quelle partie du territoire :
  - Heysham a un overlay France (littoral Manche-Atlantique, Calais →
    Lorient) cohérent avec son texte `portion`.
  - Zone Euro Sud liste **France deux fois** (DOUBLON INTERNE), sans
    aucun overlay : "France - Interzone" (placeholder, ancien nom) et un
    texte qui décrit **Heysham** sur le Bassin parisien/Loire/Nord —
    incompatible avec le texte littoral de Heysham. Retirer les textes
    sans décider ferait de ces entrées des revendications "France
    entière".
  - Espace Nordique et Arctique porte une entrée Allemagne avec un
    placeholder "Allemagne - Espace Nordique et Artique", sans overlay.
    L'Allemagne n'est plus du tout dans Zone Euro Sud. L'ancien point
    "overlay Allemagne enregistré sur la Norvège" est **périmé** : aucun
    overlay Allemagne ni Norvège n'existe plus (seuls overlays de
    `fortress_world` : Heysham/France et Espace Nordique/Russie-
    Kaliningrad).
- **Finlande et Lituanie** dans aucune zone de `fortress_world` (fichiers
  `impact_bascule_*` présents : probablement désaffectées depuis la Carte
  sans réaffectation). 2 chantiers `pays_sans_zone` écrits le 23 sept.
- **12 sous-zones restées sous leur ancien parent** après les découpages
  Hyphan (`check_origine_reelle_coherence`, 23 sept) : Bratislava-Secteur
  Alpha et Genève-Bunker (+ leurs enfants) sous `bloc_eurasiatique_
  occidental` alors que Slovaquie/Suisse sont dans Zone Euro Sud ;
  Tbilissi-Nord (+ enfant) sous `zones_grises_tampons` alors que la
  Géorgie est dans Zone Euro Sud ; Almaty (+ enfant) sous `zones_grises_
  tampons` alors que le Kazakhstan est dans le Bloc Eurasiatique.
  `reparenter_sous_zones_orphelines.py` ou "↗️ déplacer" dans l'arbre.

Voir `HANDOFF_8_SEPTEMBRE.md`, `HANDOFF_10_SEPTEMBRE.md` et
`HANDOFF_12_SEPTEMBRE.md` pour le détail complet des zones et décisions
actées.

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


---

## 🟢 4. Revue des 14 chantiers `zone_suspecte` en attente
**Ouvert le 23 septembre** (reliquat du système du 25 juillet ; le
chantier "Doublons pays-entier" qui le portait est clos et archivé). État
au 23 sept : 19 chantiers au total, 14 `a_traiter`, **tous
`zone_suspecte`** (plus aucun `pays_sans_zone` avant le scan du 23 qui en a
ajouté 2 pour Finlande/Lituanie, voir #1). Tri proposé en session, **non
appliqué — David a choisi de traiter d'abord #2/#2bis/#3/#4** :
- **À appliquer** : `ameriques_multipolaires`/reference — proposition
  déjà approuvée, relire puis "✓ Appliquer ce chantier".
- **Probablement à ignorer** (faux positif ou choix narratif) :
  `moyen_orient_golfe`/new_sustainability (conflit Israël-Iran de 2026 =
  histoire réelle de départ) ; `al_hima`, `espace_nordique_arctique`
  (zones Hyphan, choix de David) ; `tuvalu_refugies_climatiques`,
  `singapour_megapole`, `amazonie_pacte_vert` (enclaves neutres
  plausibles en fortress_world) ; `japon_archipel_resilient`,
  `inde_bassins_sacres` (eco_communalism, nuance plus qu'incohérence).
- **À lire vraiment** : `peninsule_iberique_cooperative`/policy_reform
  (seul signal structurel : "union régionale" avec Espagne seule dans
  `origine_reelle`) ; `bloc_eurasiatique_souverainiste`/
  new_sustainability ; `espace_eurasiatique`/policy_reform ;
  `bloc_persique_autonome` et `pacte_des_souverains`/reference.

⚠ Ne pas utiliser le bouton global "Appliquer" avec le filtre "Tous" tant
que `ameriques_multipolaires` n'a pas été relu : il serait appliqué au
passage.

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

## ⚪ S12. Dérive ancienne `zones_pays.json` (hors fortress_world)
**Connue depuis le 8 sept, remesurée le 23 sept** après restauration de
`zones_pays.json` (voir handoff) : `breakdown` (Arctique, Groenland),
`new_sustainability` (Norvège), `reference` (Afghanistan, Italie, Kenya,
Kirghizistan, Tadjikistan — Kenya est un rattachement volontaire).
`fortress_world`, `eco_communalism`, `policy_reform` : 0. La carte ne lit
pas ce fichier pour ses couleurs (elle lit les fiches `.md`), la dérive
est donc invisible visuellement — mais le fichier sert à d'autres outils.
Commande de mesure dans `HANDOFF_23_SEPTEMBRE.md`. Pas d'urgence.

---

## ⚪ S13. Affectation depuis la Carte : entrée `origine_reelle` incomplète
**Repéré le 23 sept.** `assign_pays` (`zone_repository.py`) écrit
`- entite: X` seul, sans `type_entite` ni `portion`, alors que les autres
chemins d'écriture produisent l'entrée complète (13 cas sur
`fortress_world`). Rattrapable à tout moment par `scan_geographie_complet
--run-type-entite --apply-type-entite` ; corriger la cause dans
`zone_repository.py` à la prochaine passe sur ce fichier (à fournir).

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

# PARTIE 3 — RISQUE STRUCTUREL IDENTIFIÉ (pas un bug actif)

**Aucun point actif.** Le seul risque identifié ici (instances custom
potentiellement non sélectionnées dans `filtered_instances`, depuis le
3 août) a été corrigé le 21 août — voir BACKLOG_ARCHIVE.md, chantier "Garantie
d'inclusion des instances custom (`loader.py`)".

---
