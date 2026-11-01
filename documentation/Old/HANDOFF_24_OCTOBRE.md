# HANDOFF — 23 et 24 octobre 2026

Suite de `HANDOFF_21_OCTOBRE.md`. Session de **clôture de S27** (simulateur
« et si ? ») : bouton Carte, banc de rejeu rebâti, restes de Genève, première
hypothèse réelle qui change la carte (Pacte de Tabriz), finitions du parcours pour
automatiser au maximum ; puis **mise au propre de toute la documentation**.
Détail complet : `BACKLOG_ARCHIVE.md`, section « ✅ S27 (clôture) ».

## Fait
- **Bouton Carte** : `assign_pays` garde le `type_entite` déjà présent dans la fiche
  (Écosse reste `region_administrative`).
- **S27.3 — banc de rejeu** : peste breakdown relancée et réexportée, Genève
  retirée du banc ; passe **v9.6** (contrôle « date contestée ») après 3 faux
  positifs ; **banc 23/23, priorités 6/6** ; commit `eabab05`.
- **S27.2 — Genève** : fiches disparues au passé (AMSC/BCUC, Tour BCUC, Palais des
  Fantômes), trois premières règles de lore breakdown, résumé régénéré.
- **S27.1 — `pacte_tabriz_2058`** (breakdown) : Iran rattaché à
  `arc_eurasien_central` ; simulé, adopté, injecté, appliqué (carte comprise),
  étape ⑤ faite. Ormuz laissée sous le Golfe ; Alliance des Ports Caspiennes sans
  bloc d'impact (décision : laissée ainsi).
- **Finitions** : règles de lore Mourmansk et Atlantique, fiche Murmansk Transit
  Arctique au passé ; relecture IA des articles limitée aux faits appliqués
  (Tabriz 7 → 0 faux positif) ; plafond d'impact ramené au lieu d'échouer ;
  localisation contrôlée par le pays du lieu ; tri Sauter / Inclure dès l'étape ③
  (`<id>.sauter.json`) ; `fiche_au_passe.py` lancé à l'étape ④ et rubrique « ⏳ » à
  l'étape ⑤.
- **Documentation (24 oct)** :
  - `BACKLOG_ACTIF.md` réduit aux points ouverts ; S27 archivé ; **S30** « à
    valider à l'usage » créé ; anomalies vues pendant la session versées dans S24.
  - `USER_MANUAL_COMPLET.md` réécrit en **mode d'emploi de l'état actuel**
    (~1 800 lignes au lieu de ~4 900), numérotation des sections inchangée ; §3bis
    rétabli (il manquait au sommaire).
  - `USER_MANUAL_HISTORIQUE.md` : addenda conservés (Partie I) + **ancien manuel
    complet du 21 oct en annexe intégrale** (Partie II) — rien n'est perdu.

## Bugs trouvés
- Contrôle final de la carte (phase 4) : exigeait le nom du pays mot pour mot dans
  les sous-zones (« Île de Kharg, Iran ») et remettait toute la carte en l'état →
  lecture par mots (`patch_s27_carte_sous_zones.py`).
- Relecture des articles : conditionnel et faits non appliqués pris pour des
  contradictions → deux patchs (`VERSION_ARTICLES` v3-appliquee).
- Instance custom refusée pour une force au-dessus du plafond (deux échecs sur
  l'Alliance) → force ramenée au plafond.
- Mistral-small ignorait les territoires des zones pour la localisation (Veilleurs
  d'Ormuz au Golfe) → contrôle mécanique du pays.
- Passe exhaustive : « date trop tardive » sans fait matériel → v9.6.

## Décisions
- Point 6 (étape ⑤ pour une hypothèse appliquée à la main) clos sans code : Genève
  était le seul cas.
- S27.4 → S24 ; S27.5 (optionnel) → S30.
- Archives (`BACKLOG_ARCHIVE.md`, historique) : seulement complétées, jamais
  réécrites.
- Le récit (bugs, itérations, tests) va dans l'historique ; le manuel ne garde que
  le mode d'emploi.

## Reste à faire
- **S30** : valider à la prochaine hypothèse le tri de l'étape ③, l'aperçu « au
  passé » de l'étape ④ / rubrique ⏳ de l'étape ⑤, le plafond d'impact, et les
  branches de carte jamais vues en réel (zone vidée, `nouvelle_zone`, « déplacer
  entière »).
- **S24** : anomalies de géographie (Uruguay, `hanse_baltique`, Brésil double,
  Paraguay, Asie centrale sans zone) et doublons d'entités probables — à trancher
  à la main (`fusionner_doublon_instance.py`).
- Commiter la documentation et les patchs du 24 oct.
- Le reste : `BACKLOG_ACTIF.md` (#3 images, #5 site des revues, S23, S25…).

## Fichiers livrés (24 oct)
- Code : `patch_s27_carte_sous_zones.py`, `patch_s27_relecture_articles.py`,
  `patch_s27_relecture_appliquee.py`, `patch_s27_plafond_impact.py`,
  `patch_s27_localisation_territoires.py`, `patch_s27_localisation_pays.py`,
  `patch_s27_sauter_avant_injection.py`, `patch_s27_gui_sauter.py`,
  `fiche_au_passe.py`, `patch_s27_checklist_au_passe.py`,
  `patch_s27_gui_au_passe.py`, `patch_s27_murmansk_passe.py`,
  `et_si_retirer_faits.py`, `scan_candidats_carte.py` (+ ceux du 23 oct :
  `patch_carte_type_entite.py`, `patch_s27_dates_contestees.py`,
  `patch_s27_amsc_passe.py`, `patch_s27_geneve_passe.py`, `regles_lore_geneve.py`).
- Documentation : `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`,
  `USER_MANUAL_COMPLET.md`, `USER_MANUAL_HISTORIQUE.md`, `HANDOFF_24_OCTOBRE.md`
  (à placer dans `documentation/`, en remplaçant les anciennes versions).

## Rappels
- Hypothèses d'exemple à ne jamais adopter : `occupation_bresil_2029`,
  `reunification_ecosse_2070`.
- Choc = s'estompe ; rupture = change le monde.
- `source ~/.zshrc` dans chaque nouveau terminal avant un script IA.
- Jamais `git checkout -- FICHIER` sans `git status` / `git diff` ; commiter avant
  tout test.
- Patchs : marqueur, remplacement unique, contrôle de compilation, `.bak`, refus
  d'une deuxième passe ; tester sur copie avant livraison.
