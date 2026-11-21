# HANDOFF — 15 novembre 2026 (fin de séance)

Chantier **unification**, étape 3 de l'ordre décidé le 7 nov : **wild cards**. Cadrage avec
David, puis patchs **U4a, U4c, U4d, U4d2, U4d3, U4d4, U4f** (U4b abandonné). Premier essai réel :
`shackleton_platinoides_2052`, ajoutée et **simulée** (rapport complet), **non adoptée**.
Dépôt : en début de séance, la suppression de `HANDOFF_11_NOVEMBRE.md` a été commitée
(`a6d486a`) et **tout a été poussé** (`main` = `origin/main`). **Rien de la séance n'est commité** :
patchs, fichiers modifiés et ces 4 documents sont à commiter (voir « Reste à faire » ①).

## Décisions (cadrage du 15 nov)
- **Nature** : une wild card est un **événement** marqué `wild_card: true` (pas un 4ᵉ type),
  mode **rupture** obligatoire. Option **B** (après l'essai du volcan) : elle change le monde
  **entier** pour de bon, sur plusieurs domaines à la fois. C'est souvent une découverte ou une
  percée (exemples de David : gisement sur une autre planète, signe de vie extraterrestre, molécule
  qui allonge la vie de 30 ans), pas une catastrophe régionale dont l'effet s'estompe.
- **Lore** : elle peut contredire les fiches et les tendances (conséquences à appliquer), **jamais
  les règles de lore** (`lore_regles.yaml` : erreur bloquante).
- **Portée** : un ou plusieurs scénarios ; chaque monde l'absorbe à sa façon. Option **b** :
  la force peut varier par scénario.
- **Plafonds** : 3 au plus par scénario, 10 ans d'écart dans un même scénario, entre 2030 et
  2090, 3 à 6 impacts ; force 25-35 dans au moins un scénario, 10 au moins partout.
- **Suggestions** : bouton ⚡ à part des lacunes (3 idées) ; case ⚡ pour ses propres idées ;
  **jamais en lot**.
- **Simulation** : Passe exhaustive obligatoire ; (A) « échapper au frein près des bornes »
  choisi puis **abandonné** (U4b) : une rupture n'a déjà ni `GAIN_CHOCS` ni plafond de 15 points ;
  le gain aurait été de quelques points. Près de 100, rien ne peut monter plus haut.
- **Étape ⑤** : brouillon de règle de lore proposé d'office ; badge ⚡ (**U4e, pas encore fait**).

## Fait (patchs livrés, tous appliqués)
- **U4a** `patch_u4a_wild_card_controles.py` (`simuler_et_si.py`, `hypothese_depuis_texte.py`) :
  champ `wild_card`, constantes `WILD_CARD_*`, `est_wild_card()`, `controle_wild_cards()` (quota,
  écart ; rejetées exclues), contrôles dans `verifier_hypothese()` (signal interdit, rupture,
  fenêtre, forces, nombre d'impacts), refus de simuler, champ `wild_card` dans la liste du GUI,
  ligne ⚡ du rapport ; ✨ Proposer `--wild-card` (normalisation : rupture, fenêtre, forces,
  6 impacts au plus) ; **bug latent d'`annee_debut` retiré**.
- **U4c** `patch_u4c_wild_card_simulation_injection.py` (`simuler_et_si.py`, `et_si_exhaustif.py`,
  `et_si_dossiers.py`, `inject_custom_events.py`) : lecture IA et Passe **forcées** ;
  `regles_lore_scenario()` + `controle_regles_lore()` (un appel IA par scénario, cache
  `generator/state/et_si_regles_lore.json`, échec = blocage) ; consignes « wild card » dans la
  lecture et la Passe ; adoption refusée sans Passe ; injection : `wild_card_impose`,
  `WILD_CARD_FORCE_MAX = 35`, `validate_instance(max_delta=…)`, `wild_card: true` dans la fiche,
  récit prévenu que l'événement se produit.
- **U4d** `patch_u4d_wild_card_gui.py` (`suggerer_lacunes.py`, `gui/app.py`, `gui/static/app.js`) :
  `suggerer_lacunes.py --type wildcard` (3 idées ; scénarios, signaux, règles de lore, wild cards
  existantes ; contrôles en ⚠) ; bouton « ⚡ Proposer des wild cards » ; case « ⚡ wild card » ;
  pas de lot pour les wild cards. `et_si_lot.py` inchangé (entités seulement).
- **U4d2** idées « improbables, pas impossibles » (1er tirage : constante alpha, inversion
  chirale…) ; année non répétée dans le texte.
- **U4d3** option B : critère « monde entier, pour de bon », exemples de David ; ✨ Proposer
  rappelle que chaque impact est permanent et qu'un domaine apaisé prend la polarité -1.
- **U4d4** les idées ⚡ choisissent leurs scénarios (liste, « tous » au plus une fois sur trois,
  ligne « Scénarios : pourquoi »).
- **U4f** `patch_u4f_force_par_scenario.py` (`simuler_et_si.py`, `hypothese_depuis_texte.py`) :
  `delta_level` nombre ou **dictionnaire par scénario** (comme `polarite`) ; `force_sc()` ;
  vérification, chocs, ruptures, lecture IA, rapport, liste d'application, entrées d'injection
  (événement et signal) ; ✨ Proposer normalise les dictionnaires.

## Essais réels de la séance
- Bouton ⚡, quatre tirages : 1) impossible (corrigé U4d2) ; 2) Champs Phlégréens VEI 6, Antarctique,
  cyclone Lagos (catastrophes régionales ou limites : U4d3) ; 3) archées des Mariannes, Conscience du
  Grid, Voile de fer (bon registre, tout en « tous » : U4d4) ; 4) stérilité HERV-W, **Shackleton**,
  supraconducteur Zéro-R (scénarios variés et justifiés).
- Blocs : volcan VEI 6 (non ajouté : permanent et exagéré) ; archées (non ajoutée) ;
  **Shackleton** : ✨ Proposer a ignoré les scénarios de l'idée (bloc corrigé à la main :
  `[fortress_world, reference]`, durées 5-8 ans, forces par scénario), Vérifier ✓, **ajoutée**.
- **Simulation Shackleton** (17:37 → 19:44, **2 h**) : règles de lore 0 contredite ; lecture IA ;
  Passe 159 + 200 fiches en 25 lots ; 1 obligatoire (reference), ~75 possibles par scénario ;
  ressources critiques -29 (les deux), économie +23 / +17, géopolitique +0,3 en fortress_world
  (déjà 99,7 : saturation) et +11 en reference ; `frontieres_du_systeme` -28 lue comme
  l'**ouverture** des blocs (administrations frontalières en déclin en fortress_world) ; l'Arctique
  désigné comme base des missions lunaires (peu réaliste). **Arrêt décidé par David** : pas
  d'adoption.

## Bugs / constats
- ✨ Proposer ignore « Scénarios : … » d'une idée ⚡ (→ U4d5).
- ✨ Proposer donne la même force partout (archées) : corrigé à la main.
- Passe exhaustive très lente (2 h pour 2 scénarios) et forcée pour chaque wild card.
- `frontieres_du_systeme` : sens à préciser avant de l'utiliser dans une wild card.
- `node --check` échoue toujours sur l'original d'`app.js` (`||=`, Node ancien) : sans conséquence.

## Reste à faire (ordre conseillé)
1. **Commiter** (après `python3 generator/validate.py` et `git status`, fichiers nommés) :
   `generator/simuler_et_si.py`, `generator/hypothese_depuis_texte.py`, `generator/et_si_exhaustif.py`,
   `generator/et_si_dossiers.py`, `generator/inject_custom_events.py`, `generator/suggerer_lacunes.py`,
   `gui/app.py`, `gui/static/app.js`, `et_si/hypotheses.yaml` (Shackleton ajoutée), les 7 patchs
   `generator/patch_u4*.py`, et les 4 documents. Vérifier dans `git status` si des fichiers de
   `generator/state/` apparaissent avant de les ajouter.
2. **Wild cards, restes** (B9) : U4d5 (scénarios imposés depuis l'idée ⚡) ; U4e (règle de lore
   d'office à l'étape ⑤, badge ⚡) ; Passe lente ; décider du sort de Shackleton (corriger : retirer
   `frontieres_du_systeme`, contrainte « lancements depuis l'équateur » ; ou supprimer à la main).
3. **Éprouver une wild card jusqu'à l'injection**, puis `validate.py` (A1).
4. Suite du handoff du 14 nov : éprouver en réel (entités Articles et Lecture IA jusqu'à
   l'injection, double-clic de l'étape ⑤, fiche U3aa, signal depuis un article) ; « source mince,
   suite » ; « Outils directs » ; bouton « Modifier » (regretté aujourd'hui pour Shackleton).

## Rappels
- Relancer Flask entièrement après modif de `app.py` ; `app.js` seul : Cmd-Maj-R. Les scripts en
  sous-processus (`simuler_et_si.py`, `hypothese_depuis_texte.py`, `suggerer_lacunes.py`…) ne
  demandent pas de relance.
- Patchs : `.py` prêt dans `generator/`, dry-run par défaut, `--apply`, sauvegardes `.bak_<tag>`,
  contrôles de syntaxe avec retour arrière, depuis la racine du vault.
- Une commande à la fois ; sorties dans `~/Documents/Ourrassol_sorties/<nom>.txt 2>&1`.
- Avant un commit : `validate.py`, `git status`, `git add` nommément (jamais `-A`). Hors commit :
  `documentation/need_action/localisation_review.md`, `generator/last_validated.json`,
  `documentation/Old/*`. git 2.17 : `git checkout -b`.
- Une simulation de wild card est **longue** (Passe forcée) : suivre l'avancement avec l'heure de
  `generator/state/et_si_exhaustif.json` (réécrit après chaque lot).
