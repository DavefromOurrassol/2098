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

**Reste à faire** :
- **Recréer Interzone Corridor proprement** (supprimée le 12 sept pour
  repartir de zéro) et dessiner ses tracés pays par pays via le nouveau
  panneau unique (bouton "✏️ dessiner" par ligne de pays).
- Créer Nordgard (niveau 1, Pays-Bas comme point de départ), Corridor
  d'Amsterdam, Zone de Koursk — discutées/nommées, **pas confirmées
  créées dans le vault réel**, à vérifier en début de session plutôt que
  supposer.
- Corriger un overlay mal renseigné sur l'Allemagne (enregistré comme
  couvrant la Norvège par erreur de sélection dans la liste déroulante —
  voir chantier #2 ci-dessous, "Overlay créé sur le mauvais pays") —
  statut non revérifié depuis le 8 septembre.
- Injecter dans le vault les personnages/entités/événements extraits du
  texte Hyphan (liste déjà faite, jamais transformée en fiches).
- Écrire les textes `portion` du partage France (Zone Euro Sud / Zone
  Interdite de Heysham) — **partiellement traité le 12 sept** : les
  textes `portion` obsolètes/orphelins (masque supprimé sans que le texte
  suive, avant le fix du 12 sept) ont été nettoyés sur les entrées
  identifiées (Allemagne/Russie/Biélorussie/Slovaquie/République
  tchèque/Belgique sur `espace_nordique_arctique`, France/Pays-Bas/
  Allemagne sur `zone_euro_sud`) — écrire un texte `portion` **correct et
  à jour** pour le partage France reste à faire ; `tensions_internes`/
  `periode_transition` toujours vides sur Zone Interdite de Heysham.

Voir `HANDOFF_8_SEPTEMBRE.md`, `HANDOFF_10_SEPTEMBRE.md` et
`HANDOFF_12_SEPTEMBRE.md` pour le détail complet des zones et décisions
actées.

---

## 🟢 2. Overlays GeoJSON + améliorations Carte (zones qui coupent un pays)
**Ouvert le 8 septembre**, parti d'une question de David sur le scénario
Hyphan (zones qui coupent un pays en deux) — a mené à la construction d'un
système complet de polygones custom dessinés à la main sur la carte
Leaflet, puis (12 septembre) à une **refonte complète de l'architecture**
suite à l'accumulation de bugs de synchronisation. Voir le sous-chantier
"Refonte architecture Carte" plus bas pour le détail de cette deuxième
phase, nettement plus large que le scope initial.

**Codé et livré le 8 septembre** : routes overlays (créer/lire/supprimer,
écriture directe de `origine_reelle` manquante à la création), interface
de dessin (Leaflet.Draw), panneau "Zones à enrichir" (comble
`tensions_internes`/`periode_transition` vides sur une zone issue d'un
split — aucun script existant ne le faisait), panneau "Gérer les
overlays", bouton "Désaffecter" un pays, liste déroulante de zones dans
`✂️ Scinder` (remplace la saisie de slug à la main), fix du bouton
"déplacer" manquant sur les zones niveau 1, fix de la synchronisation
`zones_pays.json` après un reparent (zone rétrogradée niveau 1→2+),
`enrich_zone_manquante.py` (nouveau script `generator/`).

**Non testé en conditions réelles avant livraison** (pas d'accès à
`llm_client.py` ni à une vraie clé API côté Claude) : la génération LLM
du panneau "Zones à enrichir" — premier vrai test à faire par David.

**Fait le 9-10 septembre** : option "+ Créer une nouvelle zone niveau 1…"
ajoutée au flux de dessin d'overlay (réutilise `/api/carte/creer_zone_vide`,
déjà existante pour S11). Fix géométrie invalide sur
`zone_dessin_complet.py` (S11) — `TopologyException` GEOS sur un tracé
à main levée auto-intersectant, corrigé via `.buffer(0)`. Personnalisation
visuelle de zone (couleur/motif, construite le 8 septembre sur une branche
divergente) rapatriée dans la branche principale — bouton 🎨 dans l'arbre
**et** dans le menu ✏️ de la légende, motif explicite "sans hachure"
ajouté.

**Bug trouvé le 10 septembre** : le bouton ✏️ Renommer ne propage pas vers
les tracés d'overlay dessinés — **corrigé le 12 septembre** dans le cadre
de la refonte architecture (voir sous-chantier ci-dessous, `rename()` migre
désormais aussi les overlays).

**Reste à faire (hors refonte, toujours valable)** :
- `check_overlay_portion_coherence.py` (script de diagnostic, livré mais
  **volontairement pas intégré au GUI**) — David veut le déboguer en
  conditions réelles avant de l'ajouter comme étape optionnelle de
  `scan_geographie_complet.py`.
- Piège identifié, pas corrigé : le mécanisme multi-noms partageant un
  polygone (Royaume-Uni/Angleterre/Écosse/Pays de Galles) peut laisser une
  couleur "fantôme" si un seul des 4 noms est réaffecté — à surveiller si
  ça touche Écosse/Pays de Galles à l'avenir.
- Overlay Allemagne créé sur le mauvais pays (Norvège au lieu d'Allemagne,
  erreur de sélection dans la liste déroulante) — à supprimer et refaire,
  statut non revérifié depuis le 8 septembre.
- Drift `zones_pays.json` repéré en marge sur `breakdown` (Groenland,
  Arctique) et `reference` (Italie, Kirghizistan, Tadjikistan,
  Afghanistan) — sans incidence sur `fortress_world`, pas traité, aucune
  urgence identifiée.

Voir `HANDOFF_8_SEPTEMBRE.md` et `HANDOFF_10_SEPTEMBRE.md` pour le détail
complet (fichiers livrés, tous les bugs trouvés/corrigés).

---

## 🟢 2bis. Refonte architecture Carte (`zone_repository.py` + `routes_carte.py`)
**Ouvert et quasi entièrement bouclé le 12 septembre.** Motivé par
l'accumulation de bugs de synchronisation entre les trois sources de
vérité d'une zone (`geographie/{scenario}.md`, `zones_pays.json`,
`geo_overlays/{scenario}.geojson`) — split/reparent/rename avaient chacun
leur propre trou trouvé et corrigé séparément (15 juillet, 8 sept, 10
sept). David a demandé une refonte plutôt que d'attendre le prochain trou.

**Backend construit et testé en conditions réelles** : `gui/
zone_repository.py` (nouveau module, point d'écriture unique) +
`gui/routes_carte.py` (Blueprint Flask, couche HTTP fine) remplacent ~20
routes historiques d'`app.py`. Toutes les opérations portées : rename,
reparent, split, personnaliser (+ hachures), assign/desaffecter, overlays
créer/supprimer, creer_zone_n1, **supprimer_zone_n1 (nouveau, n'existait
pas avant)**, propose (LLM), impact, ignorer. Script d'intégration
réutilisable (`integrate_routes_carte.py`, retire les anciennes routes
d'`app.py`, insère le Blueprint, valide via AST Python + `node --check`
avant d'écrire quoi que ce soit).

**Frontend reconstruit** : masquage overlay correct (opacité pleine,
uniforme base/overlay), couleur identique entre calque de base et overlay
d'une même zone, villes principales (nouvelle couche + toggle), contour de
sélection unique et géométriquement précis (`turf.union`/`turf.difference`
plutôt qu'un trait par pays), sous-zones enfin localisables (avec repli
sur la zone parente si pas de géométrie propre), panneau unique par zone
(fusion scinder + overlays + personnalisation + suppression, un seul point
d'entrée "✏️ éditer" légende+arbre), hachures génériques désormais
désactivées par défaut et pilotables par zone (au lieu d'automatiques
au-delà de 8 zones).

**~15 bugs trouvés et corrigés en testant en conditions réelles** pendant
la refonte elle-même — liste complète dans `HANDOFF_12_SEPTEMBRE.md`
(doublon Turquie, incohérence couleur base/overlay, surbrillance qui ne
suivait pas le clic, opacité incohérente, désaffecter qui ne fonctionnait
pas réellement, portions orphelines après suppression de masque, flash de
sous-zone au chargement, bug du script d'intégration sur un prompt LLM
multi-lignes non indenté confondu avec du code par une heuristique texte
— corrigé en repassant par l'AST Python).

**Reste à faire** :
- **Correction du 12 septembre (soir)** : ce chantier listait à tort S11
  comme "panneau GUI encore à construire" — vérification faite sur le code
  réel, **S11 est en fait complet et fonctionnel** (route `/api/carte/
  dessiner_zone_complete/proposer` + cycle `app.js` entier : dessin,
  proposition, panneau de review éditable, application). Seul vrai reste
  à faire : **enrichissement LLM des zones manquantes** — routes non
  portées, reste dans l'ancien `app.py`, fonctionnel tel quel ; et migrer
  `dessiner_zone_complete/proposer` vers `routes_carte.py` si l'unification
  complète est souhaitée un jour (pas fait le 12 sept, hors scope de cette
  refonte-ci).
- **Nettoyage de code mort** : `_ouvrirSplitPanel`, `_ouvrirPersoPanel`
  (`app.js`) et leurs fonctions associées ne sont plus jamais appelées
  depuis la fusion dans le panneau unique — laissées en place par
  précaution, à retirer dans une prochaine passe.
- Diagnostiquer si d'autres pays/zones ont des textes `portion` orphelins
  au-delà de ceux déjà nettoyés le 12 sept (`diagnostiquer_portions_
  orphelines.py` disponible pour relancer le scan).
- Voir chantier #1 pour la suite d'Interzone Corridor (supprimée, à
  recréer).

Voir `HANDOFF_12_SEPTEMBRE.md` pour le détail complet (tous les fichiers
livrés — une trentaine de scripts de patch/diagnostic incrémentaux,
`zone_repository.py`/`routes_carte.py`/`integrate_routes_carte.py` comme
livrables durables).

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

## 🟢 4. Doublons "pays entier" (`origine_reelle`) + intégration GUI
**Ouvert le 13 septembre, clos le 14.** Bug structurel `origine_reelle`
diagnostiqué et corrigé sur les 6 scénarios, intégration GUI demandée par
David construite et testée en conditions réelles de bout en bout (cycle
complet : diagnostic → chantier → approbation → application). Détail
complet : voir `BACKLOG_ARCHIVE.md` (table des chantiers clos) et
`HANDOFF_13_SEPTEMBRE.md`/`HANDOFF_14_SEPTEMBRE.md`.

**Reste ouvert** (mineur, ne bloque rien) :
- Bug #5 (garde-fou `zones_pays.json` limité à `pays_liste`) : seul le cas
  "match trouvé" a été testé en conditions réelles. La branche "aucun
  match" -- celle qui corrige effectivement le bug d'origine -- reste à
  rejouer sur un cas réel (ex. Balkans occidentaux, Danemark / Groenland).
- Application en LOT du chantier `doublon_pays_entier` (bouton "Appliquer"
  global scenario/all) jamais testée en navigateur -- seul le chemin
  "chantier isolé" (id) a été validé.
- Backlog `pays_sans_zone`/`zone_suspecte` préexistant (système du 25
  juillet, indépendant de ce chantier) : David a signalé qu'il restait des
  chantiers de ce type visibles dans l'onglet -- état actuel non vérifié
  cette session, à consulter en début de prochaine session.

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

## ⚪ S11. Outil de dessin de zone complète — CLOS, information périmée retirée le 12 septembre
**Repéré le 8 septembre**, conçu et codé progressivement (9-12 septembre).
Cette entrée décrivait le stade "discussion de conception seulement" —
**périmé** : le chantier est en réalité complet et fonctionnel (dessin
d'un contour complet, classification automatique split/overlay/ignoré par
intersection géométrique Shapely, enrichissement Natural Earth + LLM pour
les textes de portion, panneau GUI de review avant application). Voir
chantier #2bis (Refonte architecture Carte) pour le détail à jour — cette
entrée reste ici seulement le temps du prochain passage en archive.

---

# PARTIE 3 — RISQUE STRUCTUREL IDENTIFIÉ (pas un bug actif)

**Aucun point actif.** Le seul risque identifié ici (instances custom
potentiellement non sélectionnées dans `filtered_instances`, depuis le
3 août) a été corrigé le 21 août — voir BACKLOG_ARCHIVE.md, chantier "Garantie
d'inclusion des instances custom (`loader.py`)".

---
