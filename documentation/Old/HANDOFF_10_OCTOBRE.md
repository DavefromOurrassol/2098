# HANDOFF — 10 octobre 2026

Suite de `HANDOFF_9_OCTOBRE.md`. Session entièrement consacrée au
**simulateur « et si ? » (S27)**, passé de la v6 à la **v7.9.1** : partition,
région, mode rupture, entrée GUI en deux onglets et assistant d'écriture
d'hypothèses. Tout est testé en réel chez David.

## Fait
- **Partition (v7, v7.1)** : un pays coupé en parties, chacune dans une zone
  existante ou nouvelle, avec sa portion. Modèle France par défaut, modèle
  Allemagne avec `partie_principale`. Deux parties sous une même zone N1
  refusées. Testé : Brésil en 3 parties.
- **São Paulo** (`fortress_world`, S14) rattaché au Brésil par David depuis
  la Carte (portion + tracé).
- **v7.2** : mentions de pays en mot entier (`zone_repository.py`) ; modèle
  JSON des parties clarifié.
- **v7.3** : la carte ne change que si un territoire change de mains ; champ
  `carte: non` (filtre mécanique) ; exemple de consigne neutre.
- **Mode rupture (v7.4)** : la référence elle-même se déplace
  (`dynamique.simuler(ruptures=…)`, non-régression vérifiée). Peste :
  démographie +27 au lieu de +1, tensions 2 → 13-16 dans les mondes qui
  allaient bien.
- **v7.5** : avec `carte: non`, statut de zone `disparu` écarté.
- **Région (v7.6)** : sous-zone sans changement de mains. Testé sur le
  Nordeste.
- **GUI (v7.7, v7.8, v7.8.1)** : entrée « 🔮 Simulateur « et si ? » ».
  Onglet Simuler (liste déroulante des hypothèses), onglet Nouvelle
  hypothèse (✨ Proposer / Vérifier / Ajouter, `hypothese_depuis_texte.py`),
  garde-fous contre le double ajout.
- **v7.9, v7.9.1** : bruit des relations réduit (action « renforcée »,
  action absente, suffixe oublié, zones prises pour des entités ; entités
  « transnationales » acceptées), corrections listées dans le rapport.
- **Hypothèses ajoutées** : `peste_pulmonaire_2043` (rupture, `carte: non`),
  `extreme_droite_2034` (`carte: non`), `ia_majorite_travail_2040` (écrite par
  l'assistant, rupture).
- **Hors S27** : entrée résiduelle de `signaux_custom/needs_review.yaml`
  vidée (`.bak_residu`) ; le signal S22 était bien injecté dans les 3 variables.

## Décisions actées
- Partition : imposée dans le YAML (prioritaire) ou proposée par l'IA,
  toujours contrôlée, jamais écrite.
- Mode rupture réglé **par hypothèse** (pas par impact).
- `carte: non` : ni carte, ni région, ni zone `disparu`.
- Assistant : **voie B**, un bloc YAML proposé, modifiable et vérifié, plutôt
  qu'un formulaire champ par champ. Jamais de géographie proposée par
  l'assistant.
- Liste déroulante : on affiche le nom lisible, c'est l'id qui est envoyé.
- Nom du rapport : `et_si_<id>.md` (id stable), plus une copie
  `et_si_dernier_lancement.md` pour le panneau.
- Option « Récit IA » gardée telle quelle ; idée de synthèse haut niveau
  notée pour plus tard.

## Reste à faire
- **S27** :
  1. Phase 3, liste d'application.
  2. Relancer avec `--refaire` l'invasion, la fusion et l'extrême droite
     (consignes v7.3 à v7.9).
  3. Récit tronqué (`recit_modele()`, `trace_injection.py`).
  4. Grands sauts de trajectoire.
  5. Synthèse haut niveau, un jour.
- **Hypothèse de test** `test_region_nordeste` : à retirer de
  `hypotheses.yaml` si elle y est encore (sauvegarde `.bak_test_region`).
- **S14** : reconfirmer les alertes des sous-zones de São Paulo au prochain
  scan géographie.
- **S19** : le mode rupture n'existe que dans le simulateur ; l'étendre aux
  injections réelles serait une décision séparée.
- Hérité : S23 séries ciblées, S24 anomalies de données, S25 mesure du
  cooldown Kharg-9, chantier 5, S28, S29.

## Fichiers livrés
- **Nouveau (`generator/`)** : `hypothese_depuis_texte.py`.
- **Patchs (`generator/`, déjà appliqués, refusent un second passage)** :
  `patch_s27_partition.py` (v7), `patch_s27_partition_v71.py`,
  `patch_s27_v72.py`, `patch_s27_v73.py`, `patch_s27_v74.py`,
  `patch_s27_v75.py`, `patch_s27_v76.py`, `patch_s27_v77.py`,
  `patch_s27_v78.py`, `patch_s27_v781.py`, `patch_s27_v79.py`,
  `patch_s27_v791.py`.
- **Modifiés** (sauvegardes entre parenthèses) :
  - `generator/simuler_et_si.py` (`.bak_partition`, `.bak_v71`, `.bak_v72`,
    `.bak_v73` … `.bak_v791`) ;
  - `generator/dynamique.py` (`.bak_v74`) ;
  - `gui/zone_repository.py` (`.bak_mots`) ;
  - `gui/app.py` (`.bak_v78`) ;
  - `gui/static/app.js` (`.bak_v78`, `.bak_v781`) ;
  - `gui/scripts_config.json` (`.bak_v77`, `.bak_v78`) ;
  - `et_si/hypotheses.yaml` (`.bak_partition`, `.bak_v73`, `.bak_v74`,
    `.bak_v76`, `.bak_test_region`, `.bak_ajout`, `.bak_retrait`) ;
  - `geographie/fortress_world.md` et `gui/static/geo_overlays/fortress_world.geojson`
    (São Paulo, via la Carte) ;
  - `signaux_custom/needs_review.yaml` (`.bak_residu`).
- **Créés à l'usage** : `documentation/need_action/et_si_dernier_lancement.md`,
  rapports `et_si_*.md`, cache `generator/state/et_si_consequences.json`.

## Rappels pratiques
- Après une modification de `gui/` : redémarrer Flask ; après `app.js` :
  recharger la page avec Cmd-Maj-R.
- Une règle de contrôle nouvelle s'applique au cache sans appel payant ;
  une **consigne** IA nouvelle demande `--refaire` (ou « Nouveau tirage »).
- Sur le Mac de David, `sed -i` sans suffixe échoue : passer par un petit
  script Python.

## À reporter dans les documents vivants
Fait dans cette session :
- `BACKLOG_ACTIF.md` : en-tête, S14, S19, S22, S27 réécrit ;
- `BACKLOG_ARCHIVE.md` : S27 v7 → v7.9.1 ;
- `USER_MANUAL_COMPLET.md` : en-tête, §3quinquies réécrit, note sur les
  ruptures dans le moteur dynamique ;
- `USER_MANUAL_HISTORIQUE.md` : addendum du 10 oct.
