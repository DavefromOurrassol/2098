# HANDOFF — 13 et 15 octobre 2026

Suite de `HANDOFF_12_OCTOBRE.md`. Session consacrée au **simulateur « et si ? »
(S27)** : application réelle de Genève (point 1 du 12 oct), qui a montré que la
liste d'application n'était pas exhaustive, puis construction de la **phase 4**
(application automatique) : v8.18, v8.19 et `appliquer_et_si.py`.

## Fait
- **Genève appliquée de bout en bout, à la main** (13 oct) :
  - adoptée (19:01) ; description de l'entrée retouchée dans `queue.yaml` (le
    complexe enterré de Genève-Bunker résiste ; `.bak_bunker`) ; injectée
    (`event_instances/destruction_geneve_2076_breakdown.md`) ; statut « injecté » ;
  - `trace_injection.py` : gouvernance +6 sur 2 ans, effet net en 2098 +0,3
    (identique à la simulation) ;
  - zone `geneve_bunker_institutions` : fragmenté → en_declin, corps de
    `geographie/breakdown.md` régénéré ;
  - trajectoires : Archives Neutres émergent → résiduel ; Tour BCUC, Résidu AMSC
    et Palais des Fantômes transformé → disparu, `annee_fin` 2057 / 2061 → 2076 ;
  - les 3 entités disparues retirées des relations de **30 fiches** (la passe
    n'en avait relevé que 5) ; `validate.py` : 0 erreur, 0 avertissement.
- **S24 — doublon des Archives Neutres de Genève fusionné** :
  `archives_neutres_geneve_breakdown` → `archives_neutres_de_geneve_breakdown`
  (17 fichiers redirigés) ; fiche et archétype `archives_neutres_geneve` dans
  `_a_supprimer/fusion_archives_neutres_geneve_breakdown_20261013_1921/` ;
  Factions Propagandistes opposées aux Archives des deux côtés ; réciprocité
  (+4 alliances, +4 oppositions) ; base valide.
- **v8.18** (simulateur + injection) : l'entrée commune porte `faits_imposes`
  (contraintes de l'hypothèse, sort de chaque acteur : disparaît / change /
  reste, zones changées) ; l'injection les donne à l'IA comme non négociables ;
  le mot « matrice » n'est plus donné à l'IA ; ⚠ (sans rejet) si le récit
  détruit une entité censée rester ou emploie « matrice ».
- **v8.19** (simulateur) : chaque simulation écrit ses opérations structurées
  dans `generator/state/et_si_application/<id>.json` ; vérifié sans IA sur
  `fusion_commerciale_2038`.
- **`appliquer_et_si.py`** (phase 4) : livré, testé sur un faux vault, **pas
  encore en conditions réelles**.

## Bugs trouvés
- **Liste d'application non exhaustive** : elle ne contient que ce que l'IA a
  remarqué (5 relations contre 30 fiches) → résolu par `appliquer_et_si.py`
  (calcul depuis le vault).
- **L'injection réinventait le sort des entités** à chaque tirage (Bunker
  détruit puis sauvé) : la simulation ne lui transmettait rien → v8.18.
- **« la matrice » dans les récits** : venait de notre propre prompt
  (« Propagation via la matrice ») → v8.18.
- `annee_fin` antérieures à l'événement sur des entités « transformé » qui
  passent à « disparu » → règle ci-dessous, appliquée par `appliquer_et_si.py`.
- `trace_injection.py` : le récit IA de la traçabilité a échoué deux fois (repli
  sur le modèle) — non corrigé, sans conséquence.
- Fiche `agence_stabilisation_climatique_breakdown` : 0 retrait dans le corps
  (pas de section « ## Relations » à puces ?) — à vérifier d'un coup d'œil.
- **Banc de rejeu : 21/27**, non lié à v8.18 : les caches breakdown (lecture et
  passe) sont indexés sur un vault qui a changé. Passe de la peste rafraîchie
  (≈ 0,10 $) mais sans lecture IA : non comparable à la référence.
- Terminal bloqué par une commande `python3 -c` très longue (Ctrl+C sans effet,
  fenêtre fermée).

## Décisions actées
- Genève-Bunker : **le lieu survit** (zone en_declin), **l'institution
  disparaît** (Palais des Fantômes) ; le *Moniteur de l'Ordre* peut y siéger.
- Entité qui disparaît : `annee_fin` = année de l'élément, même si elle était
  remplie ; autre fin (transformé…) : remplie seulement si vide.
- Entité qui disparaît : retirée de **toutes** les relations du scénario, ses
  propres relations vidées ; acteurs d'événements, articles et textes gardent
  leurs mentions.
- Conflit alliance / opposition : **opposition prioritaire**.
- Faits de la simulation **imposés** à l'injection ; contradiction signalée ⚠,
  pas de rejet (même règle que le 12 oct).
- Phase 4 : n'appliquer qu'une hypothèse **adoptée et injectée** ; opérations
  ⚠ sautées par défaut (`--inclure N`), `--sauter N` pour refuser ; les
  possibles ne sont jamais appliqués ; phrases, lore, carte, articles et site
  restent listés à la main.
- Banc de rejeu : Genève retirée (déjà appliquée) ; seuil provisoire =
  **4 couples hors breakdown conformes**.
- Commandes : plus de `mv` (David place les fichiers) ; pas de `python3 -c`
  long, un petit script à la place.

## Reste à faire
- **S27** :
  1. **Test réel de la phase 4** : simuler une nouvelle hypothèse avec lecture
     IA et passe exhaustive (≈ 0,15 $), adopter, injecter (vérifier les ⚠ de
     v8.18), puis `appliquer_et_si.py --id <id>` (aperçu, tri, `--apply`).
  2. Genève, hors application : règle de lore (étape 26), phrase de l'AMSC
     (27), zones et articles à relire (28-33, 55), résumé du scénario et site
     (56-57), `audit_lore.py --scenario breakdown` (59).
  3. Décision S19 ; amplitude des chocs (`GAIN_CHOCS`).
  4. Banc : rebâtir les couples breakdown sur le vault actuel (lecture neuve,
     nouveau tri manuel).
  5. Brancher `appliquer_et_si.py` dans le GUI (panneau ⚖️ Décider).
- **S24** : doublon probable **Hanse Baltique** (`hanse_baltique_breakdown` /
  `hanse_baltique_recomposee_breakdown`) ; Communes du Rust Belt ; Bureau des
  territoires résiduels — `fusionner_doublon_instance.py` est prêt.
- Vider `_a_supprimer/` quand la fusion des Archives est confirmée.

## Fichiers livrés
- **Nouveaux (`generator/`)** : `fusionner_doublon_instance.py`,
  `changer_statut_zone.py`, `changer_trajectoire.py` (`--ecraser-annee-fin`),
  `retirer_relations.py`, `appliquer_et_si.py`.
- **Patchs (`generator/`, appliqués, refusent un second passage)** :
  `patch_s27_v818.py` (simulateur + injection), `patch_s27_v819.py`
  (simulateur).
- **Modifiés** : `generator/simuler_et_si.py` (**v8.19**),
  `generator/inject_custom_events.py` — sauvegardes `.bak_v818`, `.bak_v819`.
- **Vault (breakdown)** : `.bak_fusion`, `.bak_conflit`, `.bak_statut`,
  `.bak_corps`, `.bak_traj`, `.bak_rel` ; `evenements_custom/queue.yaml.bak_bunker`.
- **Créés à l'usage** : `generator/state/et_si_application/` (v8.19),
  `documentation/need_action/fix_alliances_conflits_reciprocite*.md`.
- **Dossiers d'hypothèses** : Genève « injecté » ; peste « simulé »
  (breakdown seul, sans lecture) ; fusion commerciale « simulé » (sans IA).

## Non traité hérité
- S23 séries ciblées, S25 cooldown Kharg-9, chantier 5, S28, S29.
- Non confirmé : `gui_verified: true` sur l'entrée `simuler_et_si` de
  `scripts_config.json`.

## Rappels pratiques
- `source ~/.zshrc;` en tête de commande pour les appels IA.
- Phase 4 : `python3 generator/appliquer_et_si.py --id <id>` (aperçu), puis
  `--sauter …` / `--inclure …` / `--apply` ; journal
  `generator/state/et_si_application/<id>.applique.json`.
- Une hypothèse simulée avant v8.19 doit être resimulée pour être appliquée.

## À reporter dans les documents vivants
- `BACKLOG_ACTIF.md` : en-tête ; S27 (v8.18, v8.19, phase 4 livrée, test réel
  à faire, banc breakdown à rebâtir) ; S24 (Archives fusionnées, Hanse
  Baltique ajoutée).
- `BACKLOG_ARCHIVE.md` : Genève appliquée (13 oct), fusion des Archives.
- `USER_MANUAL_COMPLET.md` : §3quinquies (`faits_imposes`, fichier des
  opérations v8.19, `appliquer_et_si.py`, règles d'application) ; les 4
  scripts unitaires (fusion, statut de zone, trajectoire, retrait de relations).
