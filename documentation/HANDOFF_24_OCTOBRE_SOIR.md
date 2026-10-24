# HANDOFF — 24 octobre 2026 (soir)

Suite de `HANDOFF_24_OCTOBRE.md`. Session consacrée à **S24** : doublons
d'entités et anomalies de géographie, puis hygiène du dépôt et durcissement de
l'outil de fusion. Base valide à chaque étape (0 erreur, 0 avertissement à la
fin) ; un commit par cas.

## Fait
- **Doublons — 12 cas fusionnés (13 fusions)**, en gardant de préférence
  l'archétype partagé entre scénarios, sinon le sens qui réécrit le moins de
  fichiers :
  - eco_communalism : Amazônia Viva (`consortium_amazonia_viva` gardé), Arc
    Septentrional, Bassins Vivants (`confederation_bassins_vivants` gardé),
    Terrafond (`reseau_terrafond_bassins` gardé), Trame Mnemos
    (`reseau_mnemos` gardé), Réseau Fennoscandien ;
  - breakdown : triplon Rust Belt (`mouvement_des_communes_du_rust_belt`
    gardé), Hanse Baltique (`hanse_baltique_breakdown` gardé) ;
  - fortress_world : Rust Belt, Pacte des Forteresses Souveraines
    (`alliance_blocs_souverains` gardé) ;
  - new_sustainability : Tribunal Algorithmique de Bruxelles ;
  - reference : RGMS (`institutions_multilaterales_survivantes` gardé).
  Après chaque fusion : réciprocité (`--reciprocite-seule --ignorer-exclus
  --resoudre-conflits`), auto-références et conflits internes retirés à la main.
- **Faux doublons (acteurs distincts au nom proche) — 6 renommages**, slugs
  inchangés : BioPatente Amazonas (reference), Label des Sanctuaires Souverains,
  Les Campements des Checkpoints (fortress_world), Observatoire Mondial des
  Dynamiques Démographiques (new_sustainability), Trame Bioclimatique — les Arcs
  Orphelins, Les Racines Vivantes (breakdown ; nébuleuse distincte des
  Racines-Mères occitanes, décision de David).
- **Géographie** :
  - breakdown : `hanse_baltique` complétée (Estonie, Lettonie, Lituanie,
    Allemagne ; parent `arc_eurasien_central` confirmé juste) ; Uruguay →
    `argentine_pampas_autonome` ; Grand São Paulo passé N1 (zone sinistrée) avec
    ses rédactions *O Alerta Paulista* / *O Alerta dos Bairros* ; portion du
    Brésil dans `amazon_pacte_gardiens` ;
  - new_sustainability : Brésil partagé avec portions, Manaus et Belém passées
    sous `reseau_vivant_continental` ;
  - reference : « Asie Centrale (…) » scindée en trois pays, Paraguay (Chaco)
    retiré du Sertão ;
  - fortress_world : zone `bureau_territoires_residuels` renommée
    `bureau_territoires_residuels_washington` (collision avec l'archétype du
    Bureau genevois).
- `geographie/breakdown_avant_test.md` (copie du premier commit) rangé dans
  `_a_supprimer/geographie_obsolete/`.
- **Dépôt** : règle `*.bak*` dans `.gitignore`, sauvegardes retirées du suivi
  puis supprimées du disque (1 358 fichiers ; environ 800 n'étaient pas suivis).
- **`fusionner_doublon_instance.py` v2** (testée sur mini-vault) : événement
  portant le même slug protégé, auto-références et conflits internes traités.

## Bugs trouvés
- Outil de fusion v1 : réécrivait l'event_instance et l'archétype d'un
  événement portant le même slug (Rust Belt breakdown, restauré depuis
  `.bak_fusion`) ; laissait auto-références et conflits internes → v2.
- `fix_alliances_oppositions.py` sans `--reciprocite-seule` relance une passe IA
  sur des fiches sans rapport : toujours le passer après une fusion.
- `fix_alliances_oppositions.py` n'a pas d'`--apply` : sans `--dry-run`, il écrit.

## Décisions
- Fusion : garder l'archétype partagé, sinon le sens qui touche le moins de
  fichiers ; en cas de conflit, opposition prioritaire.
- Deux acteurs opposés au nom proche ne se fusionnent pas : on renomme l'un.
- Racines-Mères (breakdown) : deux niveaux, nébuleuse et branche occitane.
- Sauvegardes : plus jamais suivies par git.

## Reste à faire
- Placer les documents (`documentation/`) et commiter.
- **Ajouter** (sans réécrire) `ADDENDUM_BACKLOG_ARCHIVE_S24.md` à la fin de
  `BACKLOG_ARCHIVE.md` et `ADDENDUM_MANUEL_S24.md` à `USER_MANUAL_COMPLET.md`
  (section des outils de données).
- Chantiers suivants conseillés : #5 (identités visuelles des revues), S23
  (séries ciblées), #3 (images) ; S30 et S25 à l'usage.

## Fichiers livrés (24 oct, soir)
- Code : `scan_doublons_lore.py`, `renommer_faux_doublons.py`,
  `zones_par_pays.py`, `patch_s24_geo_reference.py`,
  `fusionner_doublon_instance.py` (v2).
- Documentation : `BACKLOG_ACTIF.md`, `HANDOFF_24_OCTOBRE_SOIR.md`,
  `ADDENDUM_BACKLOG_ARCHIVE_S24.md`, `ADDENDUM_MANUEL_S24.md`.

## Rappels
- `validate.py` met une à deux minutes : passer par un fichier
  (`> /tmp/validate.txt; tail -3`) plutôt qu'un tube.
- Après toute modification d'une zone : `validate.py --fix` resynchronise le
  texte « ## Zones » ; une nouvelle zone N1 demande
  `generate_journaux.py --scenario X --update`.
- Jamais `git checkout -- FICHIER` sans `git status` / `git diff` ; commiter avant
  tout test.
