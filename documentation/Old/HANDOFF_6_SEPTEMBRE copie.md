# Handoff — 6 septembre 2026

Session consacrée à finir le chantier "Suite narrative des événements +
détection de basculements" (ouvert le 5 septembre, points A/B clos ce
jour-là). **Chantier entièrement CLOS aujourd'hui** — points C/D codés
et testés, plomberie de promotion résolue, incohérence de dates
corrigée, `detect_basculements_narratifs.py` vérifié et intégré au GUI.
Plus deux ajustements UX demandés en cours de route sur l'onglet
Articles.

## Fait

**Points C et D — champ `developpements` cumulatif + prise en compte
dans le forçage**
- `loader.py::load_event_instances_for_scenario()` : nouveau champ
  `developpements` exposé sur l'objet événement chargé (générique,
  `yaml.safe_load` s'en charge).
- `snapshot.py` : `forced_angle_directive`, en mode `sujet_central` sur
  un événement, ajoute désormais l'historique des développements
  précédents à la consigne LLM ("Développements déjà racontés sur cet
  événement — ne les répète pas, poursuis l'histoire à partir de là").
- `api.py` : nouvelles fonctions `_format_developpements_block()` et
  `append_developpement_evenement()` — après l'écriture réussie d'un
  article forcé en `sujet_central`, ajoute une entrée (`date_label`,
  `article_slug`, `resume` = le chapo déjà généré, aucun appel LLM
  supplémentaire) à la fiche instance de l'événement. Réécriture
  ciblée par substitution de texte (jamais de round-trip YAML complet,
  pour ne jamais perturber le formatage/wikilinks du reste de la
  fiche) ; sauvegarde automatique dans `vault/_backups/` avant chaque
  modification (même convention qu'`editer_sujets.py`).
- `evenements_cites` (déjà existant) et `developpements` (nouveau)
  resserrés tous les deux sur `forcer_resolu.get("mode") ==
  "sujet_central"` — avant, `evenements_cites` se déclenchait aussi en
  mode `ingredient` (garantie de présence dans le prompt, sans garantie
  de développement réel), même piège que celui isolé par le rattrapage
  rétroactif abandonné le 5 septembre ("citation en exemple, pas
  développée"). **Découverte en cours de test** : ce resserrement n'a
  aucun effet observable dans l'état actuel du pipeline —
  `generate.py` force TOUJOURS le mode `sujet_central` depuis une
  décision architecturale du 2 août (voir docstring du module : "pas de
  variante ingrédient en mode forcer, la distinction n'a plus lieu
  d'être dans cette architecture"). Le mode `ingredient` reste dans le
  code de `loader.py`/`snapshot.py` mais est inatteignable en pratique.
  Le resserrement reste donc une clarification défensive/anticipatrice,
  pas la correction d'un bug actif.
- `inject_custom_events.py::write_instance_file()` : les nouvelles
  fiches instance portent désormais `developpements: []` dès leur
  création.
- **Testé en conditions réelles** sur l'événement
  `revolution_travail_sahel_numerique_policy_reform` (scénario
  `policy_reform`) : 2 forçages `sujet_central` successifs (2 août puis
  9 août 2098). Résultat confirmé sur le fichier instance final :
  2 entrées `developpements` accumulées, la première intacte, aucune
  perturbation du reste de la fiche. Le 2e article généré est une
  vraie suite narrative (offensive du CTNI, classement Kontinuum en
  "zone à potentiel disruptif modéré", menaces de coupures ciblées) —
  pas une redite du lancement de 2047 déjà raconté dans le 1er article.

**Nettoyage GUI — écran "Promouvoir un événement" retiré, action
intégrée dans l'onglet Articles**
- Diagnostic du trou de plomberie hérité du 5 septembre : l'ancien
  écran (section "Entités & événements — création") ne listait que les
  articles du mois de parution actif (`GET /api/edition/articles`, lui-
  même limité par `audit_sujets_edition.py`), et verrouillait
  `date_approximative` sur ce même mois (champ désactivé côté
  formulaire, `edition_active` coché par défaut) — aucun moyen d'y
  passer la vraie date d'un article plus ancien.
- Nouvelle action "Promouvoir en événement" dans le panneau de détail
  de l'onglet Articles (`ArticlesState`, déjà construit le 5
  septembre) : `date_approximative` (année) éditable, pré-remplie avec
  l'année réelle de l'article (pas le mois actif) ; `edition_active`
  décoché par défaut (inverse de l'ancien écran — ici on veut
  généralement garder la vraie date). Même route backend
  `/api/edition/injecter_evenement`, déjà neutre sur ces champs,
  aucune modification nécessaire côté `app.py`/`inject_custom_events.py`
  pour ce point précis.
- Ancien écran entièrement retiré : nav (`injection_evenement`),
  `<div id="tab-injection_evenement">`, CSS dédiée (toolbar/layout/
  article-card/sidebar). Classes CSS réutilisées par le nouveau
  formulaire (`.injev-panel*`, `.injev-chip*`, `.injev-checkbox-row`,
  `.injev-result-box`) et `.injev-banner` (aussi utilisée par
  `#sujets-banner`) conservées.
- Filtre "Mois en cours seulement" ajouté à l'onglet Articles (case à
  cocher, grisée si aucune édition n'a jamais été enregistrée dans
  `state/editions.json`) — garde l'usage rapide de l'ancien écran sans
  sa limite.
- **Testé en conditions réelles** : dry-run puis écriture réelle sur un
  article du 3 janvier 2098 (`ils_ont_noye_les_archives_a_milwaukee_
  basse_le_reg`, scénario `breakdown`) — fiche archétype et fiche
  instance correctement créées, `date_approximative` = année réelle de
  l'article, pas le mois de parution actif.

**Incohérence de dates (cas contemporain) — corrigée**
- Problème observé lors du 1er test réel de la nouvelle action : le
  LLM choisissait une date_label ("été 2098") très éloignée de la date
  réelle de l'article source (3 janvier 2098), faute de consigne
  distinguant les deux dates.
- Nouveau champ `date_precise` (date complète de l'article, ex. "3
  janvier 2098") envoyé par le formulaire de l'onglet Articles en plus
  de `date_approximative` (année seule, inchangée pour compatibilité).
- `inject_custom_events.py::step2_develop_instance()` : quand
  `date_precise` est fourni, la règle générale "la date peut varier de
  +/- 10 ans" est remplacée par une consigne distinguant deux cas : (1)
  article CONTEMPORAIN de l'événement qu'il décrit → ancrage sur la
  MÊME SAISON, sans exception ; (2) article RÉTROSPECTIF (anniversaire,
  référence historique) → ignorer la date de l'article, suivre la
  période suggérée par le récit (dérive +/- 10 ans autorisée
  uniquement dans ce cas).
- **1er essai de formulation insuffisant** : la clause de dérive +/- 10
  ans s'appliquait aux DEUX cas, donnant au LLM une échappatoire facile
  pour ignorer l'ancrage serré voulu pour le cas 1 — observé en
  conditions réelles (article du 3 janvier, LLM parti sur le 12
  juillet malgré la consigne). Reformulé en retirant la dérive du cas
  1 (formulation en "DOIT... aucune exception"), la dérive +/- 10 ans
  réservée au seul cas 2.
- **Testé et validé** sur le cas contemporain après correctif (même
  article Milwaukee-Basse, date_label obtenue proche de janvier/hiver
  2098).
- **Cas rétrospectif testé, ambigu** : repris l'article Sahel du 2 août
  ("fête ses 50 ans de résistance") via la nouvelle action de l'onglet
  Articles — le LLM a bien détecté le caractère rétrospectif (nom
  généré : "Cinquantième anniversaire de la résistance sahelienne...")
  mais a créé un événement à propos de LA CÉLÉBRATION (datée 2098) au
  lieu de l'événement d'ORIGINE commémoré (2047, qui existe déjà comme
  fiche custom séparée — doublon potentiel). **Décision actée avec
  David : accepter cette ambiguïté comme limite connue**, pas de
  correctif supplémentaire — compter sur une vérification manuelle
  après coup plutôt qu'une garantie automatique sur les cas nuancés.

**`detect_basculements_narratifs.py` — vérifié et intégré au GUI**
- Testé sur un 2e scénario (`reference`, 13 articles) en plus de
  `new_sustainability` (5 septembre, 73 articles) : 3 candidats formant
  une séquence narrative cohérente (27 mai : émergence de crise → 4
  juin : aggravation → 19 juin : déblocage). `reference` produit bien
  un `deblocage`, absent sur `new_sustainability` — penche pour un
  biais du scénario `new_sustainability` plutôt qu'un biais
  systématique du LLM sur cette catégorie, mais pas définitivement
  tranché sur un seul scénario supplémentaire.
- **Vérification manuelle contre le texte intégral** des 3 candidats
  `reference` : sélection fiable 3/3 (les 3 articles marquent
  effectivement un vrai basculement). Catégorisation fausse sur 1/3
  (19 juin classé `deblocage` sur la foi du chapo seul — en réalité une
  poursuite de l'aggravation : nouvelle notification de censure contre
  la journaliste elle-même, rejet institutionnel de la charte de
  Väinälä par le Gelecek Meclisi — le chapo, plus positif dans le ton,
  avait fait passer un rejet pour un progrès). **Conclusion actée** :
  le champ `type_bascule` est une indication à vérifier, pas une
  classification fiable telle quelle — limite du chapo seul, cohérente
  avec le scope tranché le 5 septembre, pas de correctif.
- **Intégration GUI** (onglet Articles) :
  - Script : nouveau cache persistant `state/basculements_narratifs.json`
    (fonctions `lire_cache()`/`ecrire_cache()`), écrit à CHAQUE
    exécution indépendamment de `--md`/`--json`. Fusion par scénario —
    un scan limité à `--scenario X` ne fait jamais disparaître les
    résultats déjà en cache pour les autres scénarios ; chaque
    scénario porte son propre horodatage.
  - `app.py` : deux nouvelles routes — `GET /api/articles/basculements`
    (lecture seule du cache, rapide, aucun appel LLM) et `POST
    /api/articles/lancer_basculements` (relance le script en sous-
    processus, `scenario` optionnel dans le body pour limiter le scan,
    timeout 600s).
  - `app.js`/`index.html` : case "Basculement narratif détecté" dans
    les filtres (grisée sans cache), bouton "Détecter les basculements
    narratifs" (limité au scénario filtré ou tout le corpus), ligne de
    statut (nombre de candidats en cache + dernière génération), encart
    d'alerte dans le panneau de détail (type + justification + rappel
    "catégorie indicative, vérifie contre le texte intégral").
  - **Bug trouvé et corrigé en conditions réelles** : le 1er essai a
    donné "Détection jamais lancée" côté GUI malgré un script qui
    tournait sans erreur — cause : le cache s'écrivait sous
    `VAULT_ROOT/state/` (le vault Obsidian) alors que la route Flask le
    cherchait sous `pipeline_dir/state/` (le dossier des scripts, même
    convention que `state/editions.json`) — deux dossiers différents
    dans ce projet. Corrigé en rendant le chemin du cache relatif au
    dossier d'exécution du script (`state/basculements_narratifs.json`,
    résolu via le `cwd` du sous-processus), plus de dépendance à
    `VAULT_ROOT` pour ce fichier. **Re-testé et validé** après
    correctif.

**Onglet Articles — deux ajustements UX demandés en cours de session**
- Fermeture automatique de la fiche de détail : au changement de
  n'importe quel filtre (scénario/thématique/ligne/recherche/cases à
  cocher), et au clic en dehors du tableau ET du panneau (nouvel
  écouteur `click` sur `document`).
- **Bug trouvé et corrigé** : le clic sur une ligne du tableau ne
  faisait plus rien après ce changement — cause : `selectArticleRow()`
  redessine le `<tbody>` (donc détruit la ligne cliquée) avant que
  l'écouteur de clic externe ne s'exécute ; `e.target.closest(...)`
  échouait alors car l'élément cliqué n'avait plus de parent. Corrigé
  en utilisant `e.composedPath()` (chemin des ancêtres capturé au
  moment du clic, avant toute modification du DOM) à la place de
  `.closest()`.
- Nouveau bouton "Ouvrir dans Obsidian" dans le panneau de détail —
  construit un lien `obsidian://open?vault=...&file=...` côté client,
  à partir de `vault_root` déjà présent dans `/api/config` (aucune
  nouvelle route backend nécessaire). Vérifié cohérent avec un chemin
  réel observé dans les logs de génération de la session.

**Erreurs `validate.py` sur la date des événements — diagnostiquées et
corrigées (aller-retour en 2 itérations)**
- David lance `validate.py` en fin de session : 3 erreurs réelles,
  toutes `date {2098} hors plage [2025-2097]` — sur des événements créés
  aujourd'hui via l'action "Promouvoir en événement" (dont
  Milwaukee-Basse, le cas testé en direct). Cause directe : la consigne
  `date_precise` (cas 1, contemporain) ancre légitimement l'événement
  sur l'année de l'article source, qui est souvent 2098 — mais
  `validate.py` interdisait cette année pour un événement.
- **Diagnostic de la borne elle-même**, avant tout correctif :
  recherche dans `snapshot.py` (`date_reference`, remplace le "2098" en
  dur depuis le chantier "Mois de parution" du 2-3 septembre) et
  `edition_utils.py` (aucune borne d'année codée en dur) — établit que
  2098 est traité ailleurs dans le pipeline comme le présent narratif
  mobile de l'univers, pas une frontière figée.
- **1ère itération, implémentée puis ABANDONNÉE** : borne dynamique
  liée à l'année de l'édition active (`validate.py` + `inject_custom_
  events.py::clamp_date_dans_plage()`, tous deux lisant `edition_utils.
  lire_edition_active()`) — un événement devait rester antérieur à
  l'ANNÉE de l'édition active. Abandonnée après clarification de David :
  les articles peuvent être préparés à l'avance et datés au-delà de
  l'édition actuellement active ; plusieurs éditions successives
  couvriront différents mois de la MÊME année 2098 ; la vraie borne est
  fixe (fin d'année 2098, l'année finale de la fiction dans son
  ensemble), pas liée à l'édition en cours.
- **2e itération, retenue** : borne fixe `[2025, 2098]` inclusive, sans
  dépendance à `edition_active`, dans les trois endroits concernés :
  - `validate.py::validate_events()` — règle "4. Date dans la plage
    valide" (`ANNEE_MAX_EVENEMENT = 2098`, import `edition_utils`
    retiré, devenu inutile).
  - `inject_custom_events.py::clamp_date_dans_plage()` — même borne
    fixe, garde-fou de génération inchangé dans son principe (dernier
    filet après le LLM), juste la valeur corrigée.
  - Consigne LLM (`step2_develop_instance()`, cas `date_precise`) —
    **simplifiée** : le contournement "ancre sur 2097 si l'article
    dépasse" n'a plus de raison d'être puisque 2098 est désormais une
    année valide pour un événement ; la règle "même saison que
    l'article" pour le cas contemporain s'applique maintenant sans
    exception à gérer.
- **`annee_injection` corrigé au passage** : même bug, même borne
  `[2025-2097]` en dur, sur un champ différent (`validate.py::validate_
  instances()`, injections custom sur des entités plutôt que des
  événements) — repéré en cherchant "2097" sur tout `generator/` à la
  demande de David. Corrigé sur la même borne `[2025-2098]`. Recherche
  confirmée : aucun autre script du pipeline ne référence "2097" —
  contrairement aux événements, aucun mécanisme de génération parallèle
  (type `clamp_date_dans_plage()`) n'existe pour ce champ, donc rien
  d'autre à corriger pour l'instant.
- Testé : syntaxe des 2 fichiers validée (`py_compile`), logique de
  borne dynamique testée en isolation avant d'être abandonnée (donnait
  bien 2097 aujourd'hui, aurait suivi une édition active future) — pas
  encore re-testé en conditions réelles après le retour à la borne
  fixe 2098 (David doit relancer `validate.py` pour confirmer que les 3
  erreurs ont disparu).

## Bugs trouvés/corrigés

- `evenements_cites`/`developpements` : mode `ingredient` déclenchait
  à tort ces mécanismes (avant resserrement sur `sujet_central`) — sans
  impact réel actuellement (voir plus haut, mode inatteignable).
- Consigne de datation (1er essai) : clause de dérive +/- 10 ans trop
  permissive, appliquée aux deux cas au lieu du seul cas rétrospectif —
  corrigée après échec observé en conditions réelles.
- Cache `detect_basculements_narratifs.py` : mauvais dossier
  d'écriture (`VAULT_ROOT` au lieu de `pipeline_dir`) — corrigé.
- Onglet Articles : clic sur une ligne cassé par le nouveau mécanisme
  de fermeture automatique (`closest()` invalidé par le re-rendu du
  tableau) — corrigé avec `composedPath()`.
- Bug réel de fond découvert en fin de session : `validate.py`
  interdisait aux événements d'être datés 2098 (borne `[2025-2097]` en
  dur, reliquat d'avant le chantier "Mois de parution") — 3 fausses
  erreurs sur des événements légitimement créés aujourd'hui. Corrigé en
  2 itérations (voir "Fait" ci-dessus pour le détail complet) : borne
  dynamique tentée puis abandonnée, borne fixe `[2025, 2098]` retenue
  dans `validate.py` ET `inject_custom_events.py`. Même bug trouvé et
  corrigé sur `annee_injection` (instances, pas événements).

## Décisions actées

- Borne de date d'un événement custom : **fixe à [2025, 2098]**
  (2098 = année finale de la fiction dans son ensemble), PAS liée à
  l'édition active — un article peut être préparé à l'avance et daté
  au-delà du mois de parution actuellement actif, plusieurs éditions
  couvrant différents mois de la même année 2098. Décision de David,
  suite à une 1ère tentative de borne dynamique jugée incorrecte.

- Cas rétrospectif ambigu de la consigne `date_precise` : accepté comme
  limite connue, pas de correctif supplémentaire — vérification
  manuelle après coup plutôt que garantie automatique.
- `type_bascule` de `detect_basculements_narratifs.py` : indication à
  vérifier, pas une classification fiable — pas de correctif (chapo
  seul, limite déjà actée le 5 septembre).
- Catalogue d'entités pour l'audit par sujet (limite découverte en
  testant "Audit par sujet" → type Entité) : identifié, **pas comblé**
  cette session, laissé de côté.
- Ancien écran "Promouvoir un événement" (section Entités & événements
  — création) supprimé plutôt que fusionné avec l'onglet Articles —
  un seul point d'entrée désormais pour cette action.

## Reste à faire (point de reprise)

- **Relancer `validate.py`** pour confirmer que les 3 erreurs de date
  et la correction `annee_injection` sont bien résolues après
  redémarrage Flask — pas encore re-testé en conditions réelles après
  le retour à la borne fixe 2098 (voir "Fait" ci-dessus).
- Catalogue d'entités pour "Audit par sujet" (onglet Sujets, type
  Entité) : aujourd'hui un simple champ texte libre demandant de
  connaître le slug exact, aucun catalogue contrairement aux
  événements. Pas scopé, pas commencé.
- `detect_basculements_narratifs.py` : le biais scénario vs LLM sur
  l'absence d'`amelioration`/`blocage` n'est toujours pas
  définitivement tranché (2 scénarios testés sur 6) — à confirmer si
  besoin sur un 3e scénario un jour.
- Aucun point bloquant restant sur le chantier "Suite narrative des
  événements" lui-même — CLOS.

## Fichiers livrés/modifiés

- `loader.py` (modifié — champ `developpements` exposé)
- `snapshot.py` (modifié — `forced_angle_directive` enrichi de
  l'historique des développements)
- `api.py` (modifié — `evenements_cites` resserré,
  `append_developpement_evenement()`/`_format_developpements_block()`
  nouvelles, hook dans `save_article()`)
- `inject_custom_events.py` (modifié — `developpements: []` par
  défaut sur les nouvelles fiches, consigne `date_precise` conditionnelle
  dans `step2_develop_instance()`, `clamp_date_dans_plage()` nouvelle
  — borne fixe [2025, 2098] pour la date d'un événement)
- `validate.py` (modifié — borne de date des événements et
  `annee_injection` corrigées de [2025-2097] à [2025-2098])
- `detect_basculements_narratifs.py` (modifié — cache persistant
  `state/basculements_narratifs.json`, fusion par scénario)
- `app.py` (modifié — 2 nouvelles routes `/api/articles/basculements`
  et `/api/articles/lancer_basculements`)
- `app.js` (modifié — action "Promouvoir en événement" dans l'onglet
  Articles, ancien écran retiré, filtres "Mois en cours"/"Basculement
  narratif détecté", bouton de détection, fermeture auto de la fiche,
  bouton "Ouvrir dans Obsidian")
- `index.html` (modifié — CSS/HTML de l'ancien écran retirés, nouveaux
  éléments de la barre d'outils Articles)
- `BACKLOG_ACTIF.md` (modifié — chantier 2 clos et condensé)
- `HANDOFF_6_SEPTEMBRE.md` (ce fichier — remplace
  `HANDOFF_5_SEPTEMBRE.md`)

## Non traité aujourd'hui (hérité)

- P20 : choix du service externe de génération d'image — toujours en
  suspens.
- Secondaire S1-S7 (P17, Bug #27, renommage YAML génériques,
  troncatures JSON Mistral, GUI `promote_ville.py`, métaphores vs.
  descripteurs directs) — tous en observation, aucun changement.

## Fichiers à ré-uploader en début de prochaine session

- `BACKLOG_ACTIF.md` — version mise à jour ci-jointe, remplace la
  précédente dans le Project.
- `HANDOFF_6_SEPTEMBRE.md` (ce fichier) — remplace
  `HANDOFF_5_SEPTEMBRE.md`.
- `USER_MANUAL_COMPLET.md` — mis à jour cette session (nouvelle
  section documentant "Promouvoir en événement" dans l'onglet Articles
  et la détection de basculements narratifs).
