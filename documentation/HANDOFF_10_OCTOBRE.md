# HANDOFF — 10 octobre 2026

Suite de `HANDOFF_9_OCTOBRE.md`. Session entièrement consacrée au
**simulateur « et si ? » (S27)**, passé de la v6 à la **v8.14** : partition,
région, mode rupture, entrée GUI en deux onglets, assistant d'écriture
d'hypothèses, puis (après-midi et soir) **liste d'application** (phase 3),
éprouvée sur quatre hypothèses. Tout est testé en réel chez David.
**Statut de la phase 3 : en service, pas encore validée** — la validation
attend une première application réelle d'une liste (voir « Reste à faire »).

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
- **Après-midi — phase 3, liste d'application (v8, v8.1, v8.2)** : en fin de
  chaque scénario du rapport, étapes à cocher dans l'ordre avec la commande ou
  « à la main » ; entrée d'injection commune en fin de rapport. Testé sur
  `invasion_bresil_2029` / fortress_world (cache, 30 étapes). `test_region_nordeste`
  : déjà retirée.
- **Soir — liste d'application v8.3 → v8.14**, rapport réel par rapport réel
  (les 6 scénarios à chaque fois) :
  - v8.3 : section **« Fiches à relire »** — instances, événements, zones et
    lignes du registre (après la date) qui citent le pays, ses grandes villes
    ou les noms propres de l'hypothèse (mot entier, sans casse ni accents) ;
  - v8.4 → v8.7 : carte — sous-zones liées au pays par une ville (à déplacer ?),
    zone de niveau 1 au nom d'une ville du pays (reste à part ou rejoint ?),
    sous-zone à plusieurs pays non rattachée en bloc, jamais vers elle-même ;
    villes non comptées comme autres pays ; « États-Unis » = « États-Unis
    d'Amérique » ; ville homonyme d'un pays (Salvador) ignorée dans les
    territoires ;
  - v8.8 : « États » (de « pétro-États ») n'est plus un nom propre ; doublons de
    termes fusionnés ; sous-zone dont les territoires désignent un autre pays
    (Haïfa) non proposée ;
  - v8.9 : hypothèse sans pays ni nom propre → relecture IA proposée
    (`audit_lore.py --llm --estimer`, `--limit 10`, `--zone` des zones au
    statut changé) ;
  - v8.10 : nouvelle entité placée dans une zone créée par la même lecture :
    zone gardée (contrôle de la lecture IA) ; partition : retirer le pays d'une
    zone quittée qui le porte entier ; sous-zone cible d'une partie non
    « à répartir » ;
  - v8.11 : une région ne déclenche plus de déplacement de sous-zones ;
    « Golfe », « Détroit »… cherchés avec le mot qui suit (« Golfe persique ») ;
  - v8.12 : saut de trajectoire (émergent/marginal → dominant/mature) gardé et
    signalé « ⚠ » (choix de David : signaler, pas corriger) ;
  - v8.13 : mode rupture — l'événement est aussi créé pour le récit (entrée
    commune, puis `impact_sur_variables` à vider), référence au plafond
    signalée, banc de calibration ;
  - v8.14 : nom français des villes (≈ 110, Moscou, Pékin…) et nom court des
    sous-zones du pays cherchés dans les fiches à relire.
- **`--refaire`** de `invasion_bresil_2029`, `fusion_commerciale_2038` et
  `extreme_droite_2034` (18 appels) : lectures conformes aux consignes v7.3 à
  v7.9 (partitions et régions en nombre). `peste_pulmonaire_2043` testée en
  mode rupture (cache).
- **Récit construit par le script** (`trace_injection.py`) : plus de troncature
  (« … et 2 autres »), accents rétablis sur les noms de variables
  (`patch_s27_recit.py`, `patch_s27_recit2.py`) — les fiches `variables/`
  n'ont pas de nom lisible (`name` = slug).
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
- Phase 3 **non validée** tant qu'aucune liste n'a été appliquée pour de vrai.
- Sauts de trajectoire : signalés dans la liste, jamais corrigés d'office.
- Mode rupture appliqué : la référence change (décision S19) et l'événement
  existe aussi pour le récit, sans impact chiffré.

## Reste à faire
- **S27** (dans l'ordre proposé) :
  1. **Appliquer une liste pour de vrai**, au moins une fois (hypothèse à
     adopter, ou copie du vault) : seule validation possible de la phase 3,
     préalable à la phase 4. Une partie des étapes est payante.
  2. **Décision S19 — mode rupture dans le vrai moteur** : changer la
     référence à la main (ce que propose la liste) ou faire évoluer
     `snapshot` / Tracer.
  3. **Amplitude des chocs** (`GAIN_CHOCS`) à juger (constat du 9 oct).
  4. **Anomalies de données** relevées par le simulateur (S24) : Uruguay dans
     `espace_nord_americain_fragmente`, Brésil porté par deux N1 en
     new_sustainability, Paraguay dans `sertao_nordeste_bresilien`, doublons
     « Pacte / Consortium Amazônia Viva », trajectoires « émergent » par
     défaut.
  5. Optionnel : homonymes (Santa Cruz, Medina…), test de
     `ia_majorite_travail_2040`, synthèse haut niveau, phase 4.
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
  `patch_s27_v791.py`, `patch_s27_v8.py`, `patch_s27_v81.py`,
  `patch_s27_v82.py`, `patch_s27_v83.py` … `patch_s27_v89.py`,
  `patch_s27_v810.py` … `patch_s27_v814.py`, `patch_s27_recit.py`,
  `patch_s27_recit2.py`.
- **Modifiés** (sauvegardes entre parenthèses) :
  - `generator/simuler_et_si.py` (`.bak_partition`, `.bak_v71`, `.bak_v72`,
    `.bak_v73` … `.bak_v791`, `.bak_v8` … `.bak_v89`, `.bak_v810` …
    `.bak_v814`) ;
  - `generator/trace_injection.py` (`.bak_recit`, `.bak_recit2`) ;
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
- `USER_MANUAL_COMPLET.md` : en-tête, §3quinquies réécrit (dont « Liste
  d'application »), note sur les ruptures dans le moteur dynamique ;
- `USER_MANUAL_HISTORIQUE.md` : addenda du 10 oct (matin et après-midi) ;
- `BACKLOG_ACTIF.md` / `BACKLOG_ARCHIVE.md` : S27 phase 3.
- Soir : les cinq documents mis à jour pour v8.3 → v8.14, le récit, le statut
  (phase 3 en service, non validée) et le reste à faire.
