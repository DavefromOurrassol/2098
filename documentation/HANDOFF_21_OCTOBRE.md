# HANDOFF — 16 au 21 octobre 2026

Suite de `HANDOFF_15_OCTOBRE.md`. Session consacrée au **simulateur « et si ? »
(S27)** et à **S19** : premier test réel de la phase 4, mode rupture dans le vrai
moteur, panneau GUI « 🧭 Parcours de l'hypothèse » (étapes ① à ⑤), outillage de
l'étape ⑤ « À la main », intégration de la **carte** dans l'application.
Simulateur v8.19 → **v8.25**.

## Fait
- **Phase 4 testée en réel** (17 oct) : `explosion_brise_glace_murmansk_2081`
  (reference, choc) simulée, adoptée, injectée, appliquée ; check-list
  `et_si_explosion_brise_glace_murmansk_2081_reste_a_faire.md`. Articles relus à
  l'étape ⑤ : aucune vraie contradiction.
- **Panneau GUI « 🧭 Parcours de l'hypothèse »** (17-18 oct) : remplace « ⚖️ Décider »
  (statut, étapes ① Tester ② Décider ③ Injecter ④ Appliquer ⑤ À la main, frise de
  pastilles, cartes colorées, « ⛶ Agrandir », poignée violette entre formulaire et
  sortie pour tous les scripts) ; `et_si_statut.py`, `et_si_injecter.py` (injecte
  UNE hypothèse, sans le reste de la queue) ; phase 4 branchée (Aperçu, Sauter /
  Inclure, Appliquer, Check-list) ; indications « terminal » traduites en boutons.
- **S19, option B — rupture dans le vrai moteur** (17 oct) : une fiche
  `event_instances` avec `mode: rupture` déplace la référence du scénario
  (`loader`, `dynamique`, `snapshot`, `trace_injection`, `banc_calibration`,
  simulateur) ; non-régression stricte (0/72 niveaux changés sans fiche
  rupture). Chaîne branchée (v8.20) : l'entrée de queue impose les forces et
  `mode_impose: rupture`, l'injection écrit `mode: rupture`, la phase 4 l'accepte.
  **Test réel** : `effondrement_circulation_atlantique_2067` (reference,
  `carte: non`) appliquée de bout en bout.
- **Amplitude des chocs** (`banc_amplitude.py`, 17 oct) : **décision A — rien ne
  change** (`GAIN_CHOCS` 0,25). Règle : **choc = s'estompe, rupture = change le
  monde** ; un gros événement passe par le mode rupture.
- **Étape ⑤ outillée** (`et_si_main.py`, 17-18 oct) : nouvelles entités vers la
  file (catégorie proposée par l'IA depuis la v8.21, ou devinée d'après le nom),
  règle de lore (insertion qui garde les commentaires de `lore_regles.yaml`),
  phrases à corriger (passe + relecture IA de la fiche d'événement, réécriture,
  Remplacer / Ignorer), articles à relire (repérage IA, jamais d'écriture),
  commandes de fin. Atlantique : une vraie correction (Autorités « jusque-là
  émergentes »), le reste ignoré.
- **Menu** : « Simulateur « et si ? » » rangé dans « Entités & événements —
  Création », avant « Injecter des événements » (18 oct).
- **Carte dans l'application** (18-21 oct) :
  - v8.22 : la simulation enregistre la carte ; quand l'hypothèse fixe la carte
    d'un scénario, les propositions de carte de l'IA sont écartées ;
  - phase 4 : `absorber` / `nouvelle_zone` appliqués par la Carte
    (`ZoneRepository`), après les autres écritures ; les sous-zones qui ne portent
    que ce pays le gardent et suivent ; échec ⇒ géographie et `zones_pays.json`
    remis en l'état ;
  - étape ⑤ « 🗺️ Carte » : sous-zones à plusieurs pays (laisser, déplacer entière,
    tracer une portion), zones vidées (garder, supprimer), leurs journaux (garder
    en exil, retirer de `journaux.yaml`), nouvelle zone (description, relations) ;
  - essais : `occupation_bresil_2029` (simulation seule) et
    `reunification_ecosse_2070` (écrite sur une branche git jetable, puis défaite).
- **Corrections tirées des essais** (19-21 oct) : sauvegarde `.bak_appliquer`
  refaite à chaque écriture ; type d'origine gardé (`region_administrative`) ;
  aperçu qui annonce les fichiers de la carte ; « Fiches à relire » limitée au
  territoire qui change de mains (v8.23 : 40 → 2 lignes pour l'Écosse) ; nouvelle
  entité qui nomme le pays rattachée à la zone d'arrivée (v8.24) ; trois libellés
  justes (v8.25 : catégorie, carte écartée en premier, « hors carte »).

## Bugs trouvés
- Le bouton « créer une zone » de la Carte retire le pays de **toutes** ses
  zones, sous-zones comprises : São Paulo ITA et SPAAR se retrouvaient sans
  territoire, et `reparenter_sous_zones_orphelines.py` ne les trouvait plus →
  la phase 4 rend le pays aux sous-zones d'un seul pays avant de les rattacher.
- **Sauvegardes `.bak_appliquer` périmées** : seule la première était gardée ;
  le 19 oct, celle de la géographie datait du 26 sept → refaite à chaque écriture.
- La Carte écrit `type_entite: pays` par défaut (Écosse : `region_administrative`)
  → corrigé dans la phase 4 ; **le bouton de l'onglet Carte garde le défaut**.
- Faux positifs de l'IA (relecture des phrases et des articles) : « déjà
  dominante », « renforce », « omission » → consignes durcies et filtre
  `vraie_contradiction` (`VERSION_RELECTURE = v3-etats-cites`).
- Une phrase citée à tort dans le rapport venait d'une fiche du faux coffre de
  test, pas du vrai vault (corrigé en séance).
- Le contrôle de géographie n'est pas gratuit (étape 5 : un appel Mistral) :
  libellé corrigé.
- Après l'essai Écosse, l'hypothèse a été **adoptée et injectée par erreur sur
  `main`** (rien d'appliqué) ; défait à la main (`git checkout`, 2 fichiers).

## Décisions actées
- Amplitude : `GAIN_CHOCS` inchangé ; **choc = s'estompe, rupture = change le monde**.
- Phase 4, carte : automatique pour `absorber` / `nouvelle_zone` et les sous-zones
  d'un seul pays ; **guidé à l'étape ⑤** pour les sous-zones à plusieurs pays
  (trois choix), les zones vidées et leurs journaux ; partition et région restent
  à la main (tracés).
- Journaux d'une zone vidée : **A (garder en exil) ou B (retirer)** dans le GUI ;
  rattacher à la zone d'arrivée se fait à la main.
- Une proposition de carte de l'IA, quand l'hypothèse fixe déjà la carte du
  scénario, est écartée ; une proposition IA seule est ⚠ (`--inclure`).
- Hypothèses de test `occupation_bresil_2029` et `reunification_ecosse_2070`
  **gardées comme exemples**, à ne jamais adopter.
- Essai d'écriture sur le vrai vault : **branche git jetable** après un commit
  propre, puis retour en arrière (méthode du 19 oct).

## Reste à faire
- **S27** :
  1. Voir pour de vrai (première hypothèse qui change la carte) : déplacement
     d'une sous-zone à plusieurs pays, rattachement des sous-zones d'un pays,
     partie Carte de l'étape ⑤ et ses journaux (testés sur faux vault seulement).
  2. Genève, hors application (voir S27 du backlog, point 2).
  3. Banc de rejeu : rebâtir les couples breakdown.
- **Hors S27** : bouton Carte (`assign_pays`) qui écrit `pays` comme type ;
  anomalies du contrôle de géographie de `reference` (Afghanistan, Kirghizistan,
  Tadjikistan sans zone N1 ; 3 zones jugées trop innovantes).

## Fichiers livrés
- **Nouveaux (`generator/`)** : `et_si_statut.py`, `et_si_injecter.py`,
  `et_si_main.py`, `banc_amplitude.py`.
- **Patchs (`generator/`, appliqués, refusent un second passage)** :
  `patch_s27_reste_a_faire.py`, `patch_s27_reste_titre.py`,
  `patch_s27_gui_appliquer.py`, `patch_s27_gui_parcours.py`,
  `patch_s19_moteur_rupture.py`, `patch_s19_chaine_rupture.py`,
  `patch_s19_retouches.py`, `patch_s27_gui_main.py`, `patch_s27_categories.py`,
  `patch_s27_phrases.py`, `patch_s27_largeur.py`, `patch_s27_poignee.py`,
  `patch_s27_visuel.py`, `patch_s27_form_resizer.py`, `patch_s27_indications.py`,
  `patch_s27_articles.py`, `patch_s27_menu_et_si.py`, `patch_s27_carte.py`,
  `patch_s27_carte_main.py`, `patch_s27_carte_retouches.py`,
  `patch_s27_termes.py`, `patch_s27_journaux.py`, `patch_s27_zone_entite.py`,
  `patch_s27_libelles.py`.
- **Modifiés** : `generator/simuler_et_si.py` (**v8.25**),
  `generator/appliquer_et_si.py`, `generator/inject_custom_events.py`,
  `generator/loader.py`, `generator/dynamique.py`, `generator/snapshot.py`,
  `generator/trace_injection.py`, `generator/banc_calibration.py`, `gui/app.py`,
  `gui/static/app.js`, `gui/templates/index.html`, `gui/scripts_config.json`
  — une sauvegarde `.bak_<patch>` par patch.
- **Créés à l'usage** : `generator/state/et_si_application/<id>.main.json`
  (suivi de l'étape ⑤), `documentation/need_action/et_si_<id>_reste_a_faire.md`,
  `documentation/need_action/banc_amplitude.md`.
- **Dossiers d'hypothèses** : Mourmansk et Atlantique « injecté », appliquées ;
  Brésil (occupation) et Écosse « simulé » (exemples).
- Derniers commits : `6a24002`, `b294a4a`, `fc6d1dd`, v8.24, puis libellés et documentation.

## Rappels pratiques
- Tout le parcours se fait dans le GUI : Entités & événements — Création →
  « Simulateur « et si ? » » → panneau 🧭.
- Pour **voir** un rapport de carte, simuler **sans IA** (gratuit) et ne pas
  adopter. Une lecture IA nouvelle relance la passe exhaustive (payante).
- `et_si_main.py` : suivi dans `generator/state/et_si_application/<id>.main.json`.

## À reporter dans les documents vivants
- Fait dans cette session : `BACKLOG_ACTIF.md` (en-tête, S19, S27, S14),
  `BACKLOG_ARCHIVE.md` (16-21 oct), `USER_MANUAL_COMPLET.md` (§3quinquies).
