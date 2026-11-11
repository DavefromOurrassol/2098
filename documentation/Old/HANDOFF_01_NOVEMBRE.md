# HANDOFF — 1er novembre 2026

Fin de séance. Partie A1 : le dernier test qui n'avait jamais tourné en réel, celui des
**fiches d'entités disparues**, est fait sur la branche jetable `test-s30b`. Le test a
trouvé un vrai défaut, puis quatre défauts mineurs relevés pendant le parcours ont été
corrigés. Décision de méthode inchangée : **l'outil d'abord** (partie A vide),
l'enrichissement ensuite. Base valide sur `main`, tout est poussé, le dépôt est propre.

## Fait
- **Clôture du 31 oct vérifiée** : les 4 documents du soir sont commités (`75212a0`) et
  poussés.
- **A1, test réel des fiches d'entités disparues** (`test-s30b`, commit jetable
  `3a79654`). Hypothèse jetable `chute_holdfast_2072` (reference, 2072, `carte: non`) :
  les Citadelles du Sud-Pacifique sont évacuées et saisies. Trois contraintes : Holdfast
  disparaît ; Ergo-Wian et les consortiums de données survivent ; aucune frontière ne
  change.
  - Choix de l'entité : le RGMS a été écarté (78 fichiers le citent) au profit de
    `holdfast_reference` (19 occurrences, 6 relations, trajectoire « résiduel »).
  - ① lecture IA et passe exhaustive : 193 fiches, 0 obligatoire. ② Adopter, portée
    régionale, intensité faible. ③ injection : « [faits imposés] 6 contrôlé(s), 0 non
    respecté(s) », premier contrôle vu en réel.
  - ④ Appliquer : Holdfast passe à « disparu », `annee_fin` vaut 2072, 12 retraits de
    relations dans 7 fiches, réciprocité sans conflit, `validate` à 0 erreur. L'aperçu
    « au passé » se lance tout seul.
  - ⑤ rubrique « ⏳ » puis « Écrire dans la fiche » : la fiche est au passé, sans reste
    au présent ; `validate` à 0 erreur.
- **Cinq correctifs** (dans `generator/`, appliqués et commités sur `main`, poussés) :
  1. `fiche_au_passe.py` reçoit la description et les faits imposés de l'hypothèse. Avant,
     il recevait seulement « chute_holdfast_2072 (2072.0) », et l'IA inventait « chute »
     et « ruines » au lieu de « saisie » et « sites publics »
     (`patch_s30_contexte_au_passe.py`, `c5c093d`) ;
  2. étape ③ : « Liste de l'étape ④ » tient compte de Sauter et Inclure (✓ / –, numéros
     absents, retraits de l'entrée, sans IA) (`patch_s30_liste_sauts.py`,
     `patch_s30_liste_sauts_js.py`, `2af6ba1`) ;
  3. « Fiches à relire » : les mots génériques (« Réseau », « Conseil », « Pacte »,
     « Arc »…) ne sont plus cherchés (`patch_s30_mots_generiques.py`, `53d4b18`) ;
  4. passe exhaustive : les réponses « sans objet » sont séparées des réponses « mal
     formées » (`patch_s30_sans_objet.py`, `e3eca50`) ;
  5. bloc « Réciprocité » trié par relation, et non plus par fiche
     (`patch_s30_recip_par_relation.py`, `98dc31b`).
- **Documentation** : backlog (A1 réécrit, A2, A3, B4, routines), archive (section
  « Clos le 1er novembre 2026 »), manuel (§3quinquies : ③, `--plan`, Réciprocité,
  `fiche_au_passe.py`, lecture d'un rapport). Versions complètes, qui remplacent les
  anciennes.

## Bugs trouvés
- Le contexte de `fiche_au_passe.py` était vide de sens (correctif 1). La cause est chez
  les appelants (④ et ⑤), mais la correction est faite dans le script appelé, et les deux
  appelants en profitent.
- **Erreur de procédure, de Claude** : à l'étape ③, les numéros de Sauter ont été donnés
  d'après la liste du rapport ①, au lieu de celle de l'étape ④. Résultat : le fait
  « Holdfast disparaît » et Holdfast comme acteur ont été retirés de l'entrée, et le
  fonds groenlandais a été gardé. Sans conséquence : la contrainte principale est restée
  dans l'entrée, et les sauts ont été corrigés à ④. D'où le correctif 2 et une routine
  dans le backlog.
- Défauts mineurs : les correctifs 3, 4 et 5.
- Hors défaut :
  - « années disparues : 2098 » est attendu dans l'aperçu au passé ;
  - `signes_distinctifs` n'a qu'une copie dans la fiche, d'où 1 seul remplacement ;
  - l'étape ③ ne s'ouvre qu'après l'adoption, si bien que le bouton « Liste » n'a pas
    pu être vu dans le GUI.

## Décisions
- Les tests de disparition se font sur une entité petite et localisée. Les sauts de ③ se
  contrôlent avec « Liste de l'étape ④ », champs remplis, avant « Injecter ».
- Propositions lointaines de la lecture IA (fonds groenlandais, Atlas des Marges ↔ ARPS) :
  on les saute à la main, et on surveille leur fréquence (A2).
- La branche `test-s30b` est gardée pour consultation, comme `test-s30`.

## Reste à faire
- Remplacer dans `documentation/` : `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`,
  `USER_MANUAL_COMPLET.md` ; ajouter `HANDOFF_01_NOVEMBRE.md` ; commiter ;
  `git push origin main`.
- A1 : à vérifier au premier cas réel :
  - la relocalisation de l'événement ;
  - les citations de la passe ;
  - les correctifs 2 à 5 dans le GUI ou dans un vrai rapport ;
  - les deux points S20 ;
  - P20, qui attend B2.
  Ce ne sont plus que des observations : tous les bugs de code connus sont corrigés.
- Supprimer `test-s30` et `test-s30b` quand elles ne servent plus
  (`git branch -D test-s30 test-s30b`).
- Ensuite : partie B selon la priorité de David, ou C1 (volume par revue, plancher de 15
  conseillé). Une hypothèse réelle avec carte, à adopter pour de bon, permettrait de vider
  A1 en passant.

## Fichiers livrés (1er nov)
- Code (dans `generator/`, appliqués et commités) : `patch_s30_contexte_au_passe.py`,
  `patch_s30_liste_sauts.py`, `patch_s30_liste_sauts_js.py`,
  `patch_s30_mots_generiques.py`, `patch_s30_sans_objet.py`,
  `patch_s30_recip_par_relation.py`.
- Sauvegardes : `fiche_au_passe.py.bak_s30contexte`, `et_si_injecter.py.bak_s30liste`,
  `gui/app.py.bak_s30liste`, `gui/static/app.js.bak_s30listejs`,
  `simuler_et_si.py.bak_s30generiques`, `et_si_exhaustif.py.bak_s30sansobjet`,
  `appliquer_et_si.py.bak_s30recipRel`.
- Documentation (complète) : `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`,
  `USER_MANUAL_COMPLET.md`, `HANDOFF_01_NOVEMBRE.md`.

## Rappels
- Simulateur, étape ③ : les numéros sont ceux de l'étape ④, pas ceux du rapport ①.
- Après un changement de `gui/app.py` ou de `gui/static/app.js` : redémarrer Flask
  entièrement.
- Après tout changement de propagation ou de réglage du moteur :
  `mesure_niveaux.py --sauver <fichier>` puis `--comparer <fichier>`.
- `validate.py` : `python3 generator/validate.py > ~/Documents/Ourrassol_sorties/validate.txt 2>&1; tail -3 ~/Documents/Ourrassol_sorties/validate.txt`.
- Commandes depuis la racine du vault, sans `cd`. git 2.17 : `git checkout`, pas
  `git switch`.
