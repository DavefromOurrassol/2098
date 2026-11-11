# HANDOFF — 11 novembre 2026

Fin de séance (pause du 7 au 11 nov). Chantier **unification** : « et si ? » devient la
porte unique de tous les éléments (événements, signaux, entités). Le chemin **signal**
est éprouvé en réel de bout en bout depuis la veille 🔭 ; le chemin **Articles** est
livré mais testé seulement jusqu'au bloc proposé/vérifié. Base valide
(`validate.py` : 0 erreur, 0 avertissement). Décision de méthode inchangée : l'outil
d'abord, l'enrichissement ensuite.

## Fait
- **B3.1** : ligne « liens marquants » (couplages) dans le prompt des articles. **B4** :
  brouillon de règle de lore à termes multiples (nom complet, court, sigle, slug).
- **U2a-U2g** : type d'hypothèse `signal` dans « et si ? » (règles : force ≤ 10, 6
  scénarios, polarité ±1 par scénario, durée entière ≥ 1, date entre l'année en cours et
  2097, pas de rupture / carte / portée).
- **U2h** : `lieu` (→ `zone_hint`) et `contraintes` (transmises à l'IA du signal).
- **U3a** : veille 🔭 → « et si ? » (bouton « ✨ Envoyer vers « et si ? » », statut
  `en_hypothese`).
- **U3b** : Articles → « et si ? ». **U3c** : date, scénario(s), mode imposés depuis
  l'article. **U3d** : case « effet établi en 2098 » (durée = max(1, 2098 − date)).
- **Test réel signal** : `ia_autorite_spirituelle_2026` (veille) → adopté → injecté comme
  `chatbots_guides_spirituels_2026` ; `validate.py` 0/0.

## Bugs / erreurs rencontrés
- Patch lancé depuis la racine sans `generator/` : toujours `python3 generator/patch_….py`.
- U3c relancé deux fois : « 0 occurrence(s) » = déjà appliqué (normal) ; U3d exige U3c.
- L'IA a paraphrasé les chiffres Pew des contraintes (« 10-20 % de la population ») :
  corrigé à la main dans `signaux_custom/chatbots_guides_spirituels_2026.md` et
  `variables/gouvernance_institutions.md` (`.bak_chiffres`).
- Premier test Articles (avant U3c) : `scenarios: tous`, `rupture`, date 2097, durées
  longues → résolu par U3c/U3d (valeurs imposées).
- Message « contrôle node non concluant » : normal (node ancien, `||=` à `app.js:6790`).

## Décisions
- Fermer les accès directs (ancien Promouvoir, écran Édition « Injecter un événement
  depuis un article », anciens menus) **seulement à l'étape 5**.
- Ordre : éprouver → **entités** dans « et si ? » → **modes auto + wild cards** →
  étape 5. But : aucune manipulation manuelle à chaque promotion d'article.
- Flux de maintenance des entités (`enrich_minimal.py`, `extract_phantom_slugs.py`,
  `requeue_needs_review.py`, `create_entity.py`) hors du dispositif.
- Plage de dates d'hypothèse : 2026-2097 (limite d'injection) ; article de 2098 → 2097
  avec avertissement.

## Reste à faire
Voir `BACKLOG_ACTIF.md` B9 : (1) éprouver Articles → adoption → injection ;
(2) entités dans « et si ? » ; (3) modes auto + wild cards ; (4) étape 5 : fermer les
accès directs et supprimer le code mort (`renderArticlesPromouvoirForm`,
`submitArticlesPromouvoirInjection`, `_veillePreparer`, `_veilleAfficherPropositions`) ;
(5) réorganiser le panneau « Et si ? » (étapes, options payantes grisées pour un signal,
titre « Faits imposés à la lecture IA » trompeur) ; (6) consigne IA « reprendre tels
quels les chiffres des contraintes » ; (7) plage d'injection jusqu'à 2098 ;
(8) veille : date d'observation imposée. Aussi : C1 plancher 15 vs 20 non tranché ;
branches `test-s30` / `test-s30b` à supprimer quand inutiles ; S21 « sans suite » et
`delta_level` par scénario.
- **Git** : deux commits en attente. Placer les 4 documents dans `documentation/`.
  `methane_arctique_nordark_2097` est peut-être déjà dans `hypotheses.yaml`.

## Fichiers livrés
Patchs : `patch_b31_liens_marquants.py`, `patch_b4_termes_regle.py`,
`patch_b4_termes_regle2.py`, `patch_u2a` … `patch_u2g`, `patch_u2h_lieu_contraintes.py`,
`patch_u3a_veille_vers_etsi.py`, `patch_u3b_articles_vers_etsi.py`,
`patch_u3c_valeurs_imposees.py`, `patch_u3d_effet_plein.py`.
Sauvegardes : `.bak_u2a`…`.bak_u2f`, `.bak_u2h`, `.bak_u3a`…`.bak_u3d`, `.bak_b31liens`,
`.bak_b4termes`, `.bak_b4termes2`, `.bak_chiffres`.
Fichiers touchés : `inject_custom_signals.py`, `simuler_et_si.py`,
`hypothese_depuis_texte.py`, `gui/app.py`, `gui/static/app.js`,
`gui/routes_veille_signaux.py`.

## Rappels
- Relancer Flask entièrement après modif de `app.py` / `app.js`.
- Patchs : dry-run par défaut, `--apply`, `py_compile`, depuis la racine du vault.
- Une commande à la fois ; sorties dans `~/Documents/Ourrassol_sorties/<nom>.txt 2>&1`.
- git 2.17 : `git checkout -b`, pas `git switch`.
