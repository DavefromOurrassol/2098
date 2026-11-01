# HANDOFF — 25 octobre 2026

Suite de `HANDOFF_24_OCTOBRE_SOIR.md`. Matinée : fin du « reste à faire » d'hier
et trois corrections rapides du backlog. Après-midi : **S28.1 MICMAC**, qui a
débouché sur une révision complète de la matrice d'influence. Base valide à la
fin (0 erreur, 0 avertissement) ; un commit par étape.

## Fait
- **Reste à faire du 24 au soir** : documents déjà en place, addenda S24 déjà
  intégrés à `BACKLOG_ARCHIVE.md` et `USER_MANUAL_COMPLET.md`. Rien à commiter.
- **S30** : `et_si_injecter.py --plan` affiche « · » pour les opérations déjà
  faites (« déjà appliqué / présente / absente »), « ⚠ » seulement pour les vraies
  alertes. Même règle que `_ecartees()` (alerte commençant par « déjà »).
- **S24** : `audit_signatures.py` exclut les fichiers `_*.md` (les 6 faux
  positifs de `_index.md` ont disparu).
- **S19** : `undo_custom.py` recalcule la ligne « Total » du registre au retrait
  d'un **événement** (c'était déjà le cas pour les signaux), avec sauvegarde, et
  compare le slug exactement (3ᵉ colonne) au lieu d'une sous-chaîne.
- **S28.1 MICMAC** :
  - `micmac_matrice.py` : influence et dépendance directes et indirectes, classes
    motrice / relais / dépendante / autonome, leviers cachés, diagnostic de la
    matrice (symétrie, amortisseurs, criticité). Lecture seule.
  - Constat : l'ancienne matrice était **symétrique** (65 paires sur 66) et
    **pleine** (132 liens) ; seules la criticité et les 3 amortisseurs créaient
    des leviers.
  - Trois sources confrontées : mes propositions sens par sens, la matrice
    Excel préliminaire (`analyse_structurelle_V1.xlsx`, 41 variables 0/1
    regroupées en 12) et les liens déclarés dans les fiches (69 sur 132).
  - **Atelier de la matrice** (page privée, curseurs + étoile + plan
    influence / dépendance en direct, repères « fiche » / « à examiner » et note
    Excel) : les 12 lots validés par David, 34 poids retouchés.
  - **Matrice validée appliquée** : 125 liens (7 coupés), 9 paires symétriques
    sur 66, polarités / lags / `temporal_weight` inchangés. Classement avec
    criticité : motrices technologie et climat ; relais géopolitique, énergie,
    productifs, économie ; dépendantes gouvernance et territoires.
  - Effet sur le moteur : ρ(|K·C|) 0,42 → 0,34 ; niveaux 2098 déplacés d'au
    plus 1,2 point (`mesure_niveaux.py --comparer`).
  - **Fiches variables** : listes `influences` / `influenced_by` /
    `bidirectional_links` retirées de l'en-tête ; section « 2. Position dans le
    système » générée depuis la matrice (liens ≥ 0,5).
  - `validate.py` accepte une matrice creuse (au plus 132 liens, aucune
    variable isolée).

## Bugs trouvés
- `undo_custom.py` : retrait d'un événement par sous-chaîne (`terres_rares`
  aurait effacé `terres_rares_norvege`) et total du registre non recalculé.
- MICMAC, premier calcul : liens additionnés avec leur signe, ce qui retranchait
  les amortisseurs de l'influence (systèmes productifs classés à tort
  « dépendante »). Corrigé : force du lien en valeur absolue, partout.
- `validate.py` exigeait exactement 132 liens (matrice pleine).
- Fiches gouvernance et territoires : listes de liens vides (leurs liens
  n'apparaissaient qu'à travers les autres fiches).
- Lecture erronée de `frontieres_du_systeme` (limites planétaires) : c'est
  **l'espace** (orbite, exploration, colonisation, ressources spatiales). Ses
  22 liens ont été refaits avant validation.
- macOS : `grep -m1` sur plusieurs fichiers s'arrête à la première
  correspondance globale ; passer par une boucle.

## Décisions
- **La matrice est la seule source des liens.** Les fiches n'en gardent qu'une
  vue générée (section 2) ; on ne l'édite pas à la main.
- Systèmes productifs : **relais fort** (exemple de David : capitalisme et
  communisme au XIXᵉ siècle, esclavage, prolétariat) ; cinq liens sortants
  relevés (valeurs, gouvernance, géopolitique, territoires, démographie).
- Un lien absent des fiches n'est pas supprimé d'office : examiné lien par lien.
- MICMAC compte la force des liens, pas leur sens (un amortisseur est une
  influence).
- `K_COUPLAGE` laissé à 0,05 : écart d'au plus un point, à revoir au banc après
  le prochain gros lot d'injections.
- `variable_type` des fiches gardé comme **intention de conception**, distinct du
  classement MICMAC (option b).

## Reste à faire
- Placer les documents (`documentation/`) et commiter.
- **Ajouter** (sans réécrire) `ADDENDUM_BACKLOG_ARCHIVE_S28.md` à la fin de
  `BACKLOG_ARCHIVE.md` et `ADDENDUM_MANUEL_S28.md` à `USER_MANUAL_COMPLET.md`.
- Suites S28 notées au backlog : `coupling_intensity` à examiner, texte rédigé
  des fiches, recalage de `K_COUPLAGE` au banc.
- Chantiers suivants conseillés : #5.1 (identités visuelles des revues), S23
  (séries ciblées), S28.2 (CIB).

## Fichiers livrés (25 oct)
- Code : `micmac_matrice.py`, `appliquer_matrice_validee.py`,
  `regenerer_position_fiches.py`, `patch_s28_validate.py`,
  `patch_s19_undo_total.py` ; correctifs en ligne de commande pour
  `et_si_injecter.py` et `audit_signatures.py`.
- Données : `documentation/matrice_validee.csv`,
  `documentation/niveaux_avant_s28.json`.
- Page : Atelier de la matrice, https://claude.ai/artifact/WgAxTF4arr9aRB5w7F9vxf
  (privée ; les poids validés y restent enregistrés).
- Documentation : `BACKLOG_ACTIF.md`, `HANDOFF_25_OCTOBRE.md`,
  `ADDENDUM_BACKLOG_ARCHIVE_S28.md`, `ADDENDUM_MANUEL_S28.md`.

## Rappels
- Après toute retouche de la matrice : `micmac_matrice.py`, puis
  `regenerer_position_fiches.py --apply`, puis `validate.py`.
- Avant / après un changement de la matrice ou des réglages du moteur :
  `mesure_niveaux.py --sauver` puis `--comparer`.
- `validate.py` met une à deux minutes : passer par un fichier
  (`> /tmp/validate.txt; tail -3`) ; le détail des avertissements est en `-v`.
