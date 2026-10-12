# HANDOFF — 12 octobre 2026

Suite de `HANDOFF_11_OCTOBRE.md`. Session consacrée au **simulateur « et si ? »
(S27)** : les points 1 à 3 proposés la veille, dans l'ordre, puis deux
améliorations du GUI demandées en fin de session. Le pipeline « tester →
décider » est complet ; « injecter » reste la commande existante.

## Fait
- **Point 1 — passe exhaustive branchée dans le simulateur** (v8.16 → v8.16.2) :
  - `--passe-exhaustive` : obligatoires dans la liste d'application
    (« [passe exhaustive] »), 20 possibles prioritaires dans une section
    « Possibles (facultatif) », relations rompues d'une entité disparue
    regroupées par entité ; Genève : 75 → 59 étapes ;
  - v8.16.1 : la recherche par mots ne double plus la passe (instances et
    événements déjà relus) ;
  - v8.16.2 : ⚠ sur une relation rompue « parce que l'entité a disparu » alors
    qu'elle n'est déclarée disparue nulle part ; `acteurs_hint` de l'entrée
    commune = entités les plus touchées, 4 au plus par scénario.
- **Point 2 — `inject_custom_events.py`** : plus de troncature ni de faux ⚠
  « N variables reçues au lieu de 4 max » quand les impacts sont imposés ; un
  `acteurs_hint` suffixé d'un autre scénario n'est pas imposé.
- **Case GUI « Passe exhaustive »** (option A), vérifiée dans le GUI.
- **Point 3 — étape « décider »** (v8.17 → v8.17.1, `et_si_dossiers.py`) :
  - dossier de chaque hypothèse dans `generator/state/et_si_dossiers.json`,
    réécrit à chaque simulation ;
  - `--dossiers`, `--adopter <id> --portee … --intensite … [--apercu]`,
    `--rejeter <id> --motif …`, `--annuler-decision <id>` ; statut dans
    `--lister` et dans la liste du GUI ;
  - panneau GUI **⚖️ Décider** (route `/api/et_si/decider/<action>`) ;
  - « Annuler la décision » retire de la queue l'entrée adoptée pas encore
    injectée.
- **Panneaux de fichiers du GUI** : titre d'un `.md` cliquable vers Obsidian
  (tous les panneaux) ; option `lien_seul` (nom du fichier seul ; `.yaml` →
  Visual Studio Code), activée pour les deux panneaux du simulateur.

## Résultats et constats
- **La passe dépend de la lecture IA**, qui lui sert de contexte : lancée
  depuis le simulateur avec une lecture neuve, elle a tout relu (≈ 0,10 $) et
  rendu 14 obligatoires au lieu de 24 sur Genève. **Banc de rejeu : toujours
  26/27** — la référence tient. La contradiction lecture / passe (Archives
  Neutres « résiduel » contre alliances rompues « parce que disparues ») est
  signalée par le ⚠ de la v8.16.2, sans règle IA.
- **Décider, validé sur Genève** en ligne de commande puis dans le GUI :
  simulé → aperçu → adopté, en attente d'injection → décision annulée. État
  actuel : **Genève « simulé »** (simulation complète du 12 oct, 20:51, avec
  passe), **queue vide**, rien injecté (choix de David).
- Le node de l'iMac est trop ancien pour vérifier `app.js` entier (`||=`) :
  les patchs GUI ne vérifient alors que le code ajouté.

## Décisions actées
- Statuts des hypothèses dans un **fichier à part**
  (`generator/state/et_si_dossiers.json`).
- **« Adopter » écrit l'entrée dans `queue.yaml`**, sans injecter ;
  `portee` et `intensite` choisies à ce moment-là ; l'injection reste une
  action séparée.
- On n'adopte que **la dernière simulation complète** (sans `--scenario`) d'une
  hypothèse **inchangée** depuis.
- Le statut « injecté » est **calculé à la lecture** (vault, queue,
  `needs_review.yaml`), jamais stocké.
- Ligne de commande d'abord, GUI ensuite (fait dans la session).
- Incohérence entre deux tirages IA : **signaler**, pas de règle IA.

## Reste à faire
- **S27** (dans l'ordre proposé) :
  1. **Appliquer une liste pour de vrai** — candidat : Genève (adopter,
     `inject_custom_events.py --mode custom`, vérifier le statut « injecté »,
     puis dérouler la liste d'application). Validation de la phase 3 et
     préalable à la phase 4 (option b) ; une partie des étapes est payante.
  2. **Décision S19** (mode rupture dans le vrai moteur).
  3. **Amplitude des chocs** (`GAIN_CHOCS`).
  4. Anomalies de données (S24), homonymes, synthèse : optionnels.
- **S24** : doublons probables notés le 11 oct (Archives Neutres de Genève,
  Communes du Rust Belt, Bureau des territoires résiduels), toujours à
  vérifier à la main.
- Hérité : S23 séries ciblées, S25 mesure du cooldown Kharg-9, chantier 5, S28,
  S29.
- Non confirmé : `gui_verified: true` sur l'entrée `simuler_et_si` de
  `scripts_config.json` (one-liner donné, résultat non rapporté).

## Fichiers livrés
- **Nouveau (`generator/`)** : `et_si_dossiers.py`.
- **Patchs (`generator/`, appliqués, refusent un second passage)** :
  `patch_s27_v816.py`, `patch_s27_v8161.py`, `patch_s27_v8162.py` (simulateur +
  injection), `patch_s27_gui_passe.py`, `patch_s27_v817.py`,
  `patch_s27_gui_decider.py` (simulateur, `app.py`, `app.js`,
  `scripts_config.json`), `patch_gui_obsidian_panneaux.py`,
  `patch_gui_lien_seul.py` (`app.py`, `app.js`, `scripts_config.json`).
- **Modifiés** : `generator/simuler_et_si.py` (v8.17.1),
  `generator/inject_custom_events.py`, `gui/app.py`, `gui/static/app.js`,
  `gui/scripts_config.json` — sauvegardes `.bak_v816`, `.bak_v8161`,
  `.bak_v8162`, `.bak_v817`, `.bak_gui_passe`, `.bak_gui_decider`,
  `.bak_obsidian`, `.bak_lien_seul`.
- **Créés à l'usage** : `generator/state/et_si_dossiers.json`,
  `evenements_custom/queue.yaml.bak_et_si`.

## Rappels pratiques
- Terminal bash : `source ~/.zshrc;` en tête de commande pour charger
  `MISTRAL_API_KEY` (sinon la lecture IA échoue).
- Commandes en **une seule ligne**, enchaînées par `;` ou `&&`.
- Après un patch de `app.py` ou `scripts_config.json` : redémarrer Flask ;
  après `app.js` : recharger la page sans cache (Cmd+Maj+R).
- Adopter Genève quand ce sera le moment :
  `python3 generator/simuler_et_si.py --adopter destruction_geneve_2076 --portee regionale --intensite majeure --apercu`
  puis sans `--apercu` (ou panneau ⚖️ Décider) ; la simulation enregistrée
  reste valable tant que l'hypothèse n'est pas modifiée.
- Banc de rejeu (gratuit) :
  `python3 generator/export_et_si.py && python3 generator/rejeu/rejouer.py && python3 generator/rejeu/evaluer.py`
  — viser « VERDICTS : 26/27 ».

## À reporter dans les documents vivants
Fait dans cette session : `BACKLOG_ACTIF.md` (en-tête, S27),
`BACKLOG_ARCHIVE.md` (S27 du 12 oct), `USER_MANUAL_COMPLET.md` (en-tête, §3
`inject_custom_events.py`, §3quinquies : GUI, commandes, injection commune,
passe dans le simulateur, étape « décider », fichiers ; GUI : titres `.md` et
`lien_seul`), `USER_MANUAL_HISTORIQUE.md` (addendum du 12 oct).
