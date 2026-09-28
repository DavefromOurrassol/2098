# HANDOFF — 27 septembre 2026

Suite de `HANDOFF_26_SEPTEMBRE.md`. Session consacrée à la chaîne
d'injection des événements, instances et signaux faibles, et à la
propagation de leur influence jusqu'en 2098. Elle a commencé par une
question de compréhension de David et s'est terminée par une refonte en
8 étapes, un moteur de propagation dynamique et un outil « Tracer »
enrichi (récit IA + graphique). Toutes les modifications ont été faites
sur le vault réel par David, étape par étape (simulation, `.bak`, puis
écriture). En fin de session : `validate.py` 0 erreur, 0 avertissement,
0 correction.

## Fait

### Convention unique d'intensité (étapes 1 à 8)
- **Diagnostic** : l'effet d'un impact était `delta_level × facteur ×
  polarite`, avec des deltas négatifs et des polarités −1 (141 doubles
  négations, `audit_polarite.py`). Les échelles mélangeaient « capacité »
  et « intensité » selon la variable, la matrice contenait des liens de
  sens incohérent, et les tensions étaient calculées avant les
  injections.
- **Convention actée** : pour les 12 variables, 0 = calme et 100 = crise
  maximale. `delta_level` = force (toujours ≥ 0), `polarite` = sens (+1
  aggrave, −1 apaise). Effet = `abs(delta) × facteur × polarite`.
- **Étapes 1+2** (`migrer_echelles.py`) : un bloc `echelle:` (`type:
  intensite`, `zero`, `cent`) dans chaque fiche variable.
  `gouvernance_institutions` et `frontieres_du_systeme` sont inversées
  (sens fragilité/désordre), et la santé est recalée. Le texte de la
  section 8 est mis à jour et 40 liens de matrice sont inversés.
- **Étape 3** : `echelles.py` (nouveau module) injecte l'échelle et la
  convention dans les prompts d'injection (événements, signaux,
  instances, `enrich_minimal`). `verifier_impact()` contrôle chaque
  impact produit.
- **Étape 4** : `abs(delta)` dans `snapshot.py` (anciennes fonctions
  gardées) et dans `validate.py`.
- **Étape 5** (`polarites_matrice.py`) : matrice en +1 partout, sauf 3
  amortisseurs à −1 (économie→climat, production→climat,
  production→énergie).
- **Étape 6** (`reevaluer_polarites.py`) : l'IA a réévalué le sens de
  chaque impact stocké (153 fiches écrites, sens demandé par scénario
  pour les signaux).
- **Étape 7** : `check_coherence` réécrit avec 3 types de tension
  (`crise_mutuelle`, `amortissement`, `cascade_critique`). Les tensions
  et les tensions thématiques passent **après** les injections.
- **Étape 8** (`synchroniser_scenarios.py`) : `variable_states` et le
  tableau 4A des fiches scénario sont alignés sur les fiches variables.
  Les tendances sont inversées pour 9 variables.

### Moteur de propagation dynamique (`dynamique.py`)
- Chaque variable est un système du second ordre amorti. Son
  amortissement vient de la volatilité et sa période de la résilience.
  Les couplages suivent la matrice (poids × polarité × poids temporel ×
  criticité de la source), avec un retard = lag × 5 ans. Chocs : rampe
  sur `duree`, puis décroissance (demi-vie de 20 ans). Pas mensuel depuis
  2025.
- **Stabilité garantie** : garde « petit gain » (`k_effectif`), qui
  réduit K automatiquement si la résonance × ρ(|K·C|) dépasse 0,9.
  Mesuré : 0,74 ; ρ = 0,42. Réponse à David : ajouter des événements ne
  peut pas rendre le système instable, cela ne fait que déplacer les
  niveaux, qui restent bornés.
- Sortie saturée : `ref + marge·tanh(x/marge)`, avec une marge de 15
  points au plus, bornée par la distance à 0/100.
- Branché dans `snapshot.py` (`MOTEUR_DYNAMIQUE = True`,
  `appliquer_dynamique`) : une modification par variable si |écart| ≥
  0,5, avec 3 contributeurs au plus. Le prompt affiche « ref → nouveau
  (±x) — surtout : … ».
- `banc_calibration.py` : banc de réglage en lecture seule (CSV,
  `--balayage-k`).

### Doublon Rust Belt
`insurrection_rust_belt` (événement) supprimé via `undo_custom.py` ;
`communes_rust_belt_zones_libres` gardé (cité dans un article, a une
entité).

### « Tracer une instance / un événement / un signal »
- Nouvelle section 4 « Effet sur le monde (moteur dynamique) » : effet
  net attribuable, calculé en contrefactuel (monde avec / sans
  l'élément), avec la propagation, par scénario. Les articles passent en
  section 5.
- **Récit pour l'utilisateur** (IA, tier `creative_souple`), vérifié :
  chiffres et années conformes aux jalons calculés, au moins une
  ampleur citée. Sinon, repli sur un récit modèle sans IA.
- **Graphique GUI** (Chart.js) sous le journal : vue « effet » et vue
  « niveaux avec/sans » (pointillés), avec un marqueur d'apparition.
  Route `GET /api/trace/derniere`. Testé par David (capture OK).
- Options : `--scenario`, `--date` (2098 par défaut), `--sans-recit`,
  `--skip-effet`.

## Bugs trouvés
- f-string avec antislash (Python < 3.12) dans `recit_llm` — corrigé.
- Variable `k` qui masquait l'indice de boucle dans `simuler` (tout
  saturait à ±15) — renommée `k_coup`.
- Regex qui avalaient des lignes vides (`migrer_echelles`,
  `synchroniser_scenarios`) — corrigées.
- Un second `--appliquer` écrasait les `.bak` — sauvegardes désormais
  écrites une seule fois, avec des marqueurs d'idempotence.
- Cache des échelles indexé par slug du frontmatter — désormais par nom
  de fichier.
- Couplage trop fort au premier réglage (K = 0,1, amplification ×6,5) —
  recalibré.
- Premier récit IA : il exagérait des effets minimes sans citer
  d'ampleur — consignes et contrôle durcis.

## Décisions actées
- Convention d'intensité (0 = calme, 100 = crise) pour les 12
  variables ; `delta_level` ≥ 0, sens porté par `polarite`.
- Matrice : option b (+1 partout, 3 amortisseurs à −1).
- Réglages du moteur : K = 0,05 ; GAIN_CHOCS = 0,25 ; demi-vie de 20
  ans ; plafond de 15 points ; 5 ans par cycle de lag.
- Les tendances des fiches scénario ne servent qu'à l'affichage (aucun
  calcul ne les lit).
- Tracer : récit IA (option b) + graphique Chart.js (option B).

## Reste à faire
- **Remettre `gui_verified: true`** sur `trace_injection` dans
  `scripts_config.json` (testé et validé par David, drapeau oublié).
- **S19** (nouveau) — surveillance du moteur dynamique ; voir le backlog.
  Il inclut la question ouverte de David : un signal avec
  `propagation_via_matrice: false` agit sur sa variable, mais ne se
  propage pas aux autres. Options non tranchées : a) passer certains
  signaux à `true` à la main ; b) changer la consigne du prompt ; c) tous
  les signaux propagés à ~30 %.
- Hérité : #3 P20 (service d'image), S18, S15.

## Fichiers livrés
- **Nouveaux** (`generator/`) : `echelles.py`, `dynamique.py`,
  `banc_calibration.py`. Outils ponctuels déjà appliqués :
  `migrer_echelles.py`, `polarites_matrice.py`, `reevaluer_polarites.py`,
  `synchroniser_scenarios.py`. Diagnostics en lecture seule :
  `audit_polarite.py`, `extraire_echelles.py`.
- **Modifiés** : `snapshot.py`, `prompt_builder.py`, `loader.py`,
  `validate.py`, `inject_custom_events.py`, `inject_custom_signals.py`,
  `enrich_minimal.py`, `instance_generation_common.py`,
  `trace_injection.py`, `gui/app.py`, `gui/templates/index.html`,
  `gui/static/app.js`, `gui/scripts_config.json`.
- **Vault** : 12 fiches `variables/`, `influence_matrix.md`, 6 fiches
  `scenarios/`, 153 fiches d'impact (instances, event_instances,
  signaux_custom).
- `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`, `USER_MANUAL_COMPLET.md`,
  `USER_MANUAL_HISTORIQUE.md`, ce handoff.

## Non traité hérité
S1-S10, S14 inchangés (voir backlog).

---

# Seconde partie (après-midi) — Signaux faibles, persistance, idées en texte libre

Partie de la question « synthèse du mécanisme d'injection des signaux
faibles ». Chantier ouvert et clos dans l'après-midi ; détail et
justifications dans `BACKLOG_ARCHIVE.md`.

## Fait
- **Double gain corrigé** dans les contributeurs affichés
  (`snapshot.appliquer_dynamique`) — niveaux inchangés, liste « surtout : »
  enfin remplie.
- **Signaux** (`inject_custom_signals.py`) : polarité par scénario
  (dictionnaire), `delta_level` ≥ 1, champ `persistance`, champ
  `annee_apparition` (contrainte + validation), année de `evenement_cle`
  n'importe où, reprise d'injection partielle (`idee_a_remettre_en_queue`,
  bloc `reprise`, garde-fou anti-doublon), slug déjà pris → `_2`,
  `variables_cibles` = variables réellement injectées.
- **Persistance des chocs** (`dynamique.py`) : table `PERSISTANCE`
  (éphémère 10 ans / normale / durable 40 ans / permanente),
  `DEMI_VIE_PAR_TYPE`, palier jusqu'à `annee_fin`. Câblée pour signaux,
  événements (`inject_custom_events.py`, queue/archétype/instances/mode
  auto) et instances (déduite de la trajectoire, `PERSISTANCE_INSTANCE_
  ACTIVE = "permanente"`). `loader.py` transmet `persistance` (signaux,
  event_instances, bloc `injection` des instances).
- `clerge_prompteurs_ia` injecté (idée « prêtres de l'IA ») puis passé en
  `permanente` à la main : contributeur de ses 3 variables en
  new_sustainability.
- **`mesure_niveaux.py`** (nouveau) : photo avant/après des 72 niveaux.
  Persistance des instances mesurée : écarts ≤ 4,3 points, dans le sens de
  chaque scénario.
- **`idees_vers_queue.py`** (nouveau) + bouton GUI « ✨ Compléter les autres
  champs » sous Description (formulaires signaux et événements), route
  `POST /api/idees/proposer`. Formulaire signaux : thèmes en sélection
  multiple (libellés lisibles), champs Année d'apparition et Persistance ;
  formulaire événements : champ Persistance.

## Bugs trouvés
- Double `GAIN_CHOCS` dans `appliquer_dynamique` (corrigé).
- Exemple JSON du prompt recopié par Mistral (`delta_level: 0`, puis motif
  de polarités) — remplacé par des emplacements.
- `polarite or 1` transformait un 0 en +1 sans prévenir (supprimé).
- Injection partielle remise en queue → variables réinjectées en double
  (corrigé) ; slug déjà pris → fiche d'audit d'un autre signal écrasée
  (corrigé).
- Année exigée en fin de `evenement_cle` (corrigé, aligné sur les
  événements).
- Formulaire GUI signaux : une seule variable imposable (`select`) →
  `multi_select`.
- `annee_apparition` non extraite de « chine 2049 champion économique »
  (règle trop stricte) → règle assouplie + rattrapage mécanique.
- Pas un bug de code : ancien `gui/static/app.js` resté en place chez
  David (nouveau fichier enregistré ailleurs).

## Décisions actées
- Polarité par scénario pour les signaux ; `delta_level` unique (1-10).
- Persistance configurable (table dans `dynamique.py`), par choc et par
  type ; `intensite` (événements) = force, `persistance` = durée.
- Instances : « l'effet dure tant que l'entité existe » ; actives en
  `permanente` (repli `durable` possible).
- `annee_apparition` : contrainte sur les fenêtres ; le choc démarre au
  début de la bascule (pas dès l'apparition).
- Assistant texte libre : propose seulement, écriture par « Ajouter à la
  queue » (un seul chemin) ; une seule zone de saisie (Description).
- Pas de règle de longueur sur la description reformulée (David : « c'est
  ok »). Bouton « Proposer en événement » : non, à revoir à l'usage.

## Reste à faire
- S19 (mis à jour) : propagation des signaux via la matrice toujours non
  tranchée ; saturation près des bornes (breakdown ≈ 99, gouvernance
  new_sustainability 0,3) à surveiller.
- S20 (nouveau) : suites possibles de l'assistant et des signaux (voir
  backlog).
- Hérité : #3 P20 (service d'image), S18, S15.

## Fichiers livrés
- **Nouveaux** (`generator/`) : `idees_vers_queue.py`, `mesure_niveaux.py`.
- **Modifiés** : `snapshot.py`, `dynamique.py`, `loader.py`,
  `inject_custom_signals.py`, `inject_custom_events.py`, `gui/app.py`,
  `gui/static/app.js`, `gui/scripts_config.json`.
- **Vault** : `signaux_custom/clerge_prompteurs_ia.md` (nouveau, puis
  `persistance: permanente` ; `.bak` gardé), fiches variables
  `technologie_information`, `gouvernance_institutions`,
  `valeurs_culture_tempo_sociale` (sections 7 et 12),
  `registre_evenements.md`.
- `BACKLOG_ACTIF.md`, `USER_MANUAL_COMPLET.md`, ce handoff ; bloc à ajouter
  en fin de `BACKLOG_ARCHIVE.md` (`ajout_BACKLOG_ARCHIVE_27_septembre_apres_midi.md`).

## Non traité hérité
S1-S10, S14 inchangés (voir backlog).
