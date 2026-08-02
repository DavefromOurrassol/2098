# HANDOFF — session du 26 juillet 2026 (à uploader dans le nouveau chat)

*Suite directe de `HANDOFF_25_JUILLET_SOIR.md`. Les 3 points laissés en
suspens ce soir-là (décision sur les 5 diagnostics, "niveau 2", point 4.5)
sont **tous clos** aujourd'hui. Session très longue, dans l'ordre : audit
complet du panneau GUI, onglet Chantiers (4.5), puis un chantier non prévu
au départ — validation approfondie d'`inject_signals`, qui a fini par
occuper la majorité de la session et a débouché sur plusieurs vrais bugs
corrigés + un type `signal` ajouté à `undo_custom.py`.*

---

## 1. Ce qui a été fait aujourd'hui, dans l'ordre

### 1.1 — Clôture des 3 points en attente du 25 juillet soir

**"Niveau 2" (pairing diagnostic/correction sur `scan_geographie_complet`)**
— la conception du 25 juillet (griser la correction tant que l'étape
parente n'est pas cochée) s'est révélée **inversée** dès le premier essai
réel : vérifié dans les scripts Python que le diagnostic est toujours
obligatoire et tourne dans le même appel que sa correction — donc
c'est l'inverse qui est vrai. Refait sur ce principe : cocher la
correction force le diagnostic parent coché, décocher le diagnostic
décoche sa correction. Effet de bord découvert en le construisant : le
préréglage Maxi devait aussi cocher explicitement les 5 `--run-*`, sans
quoi forcer 3 parents sur 5 déclenchait une "sélection partielle"
excluant Zones/Conventions du run. `--write-chantiers` exclu de ce
mécanisme (nature différente — passif, partagé entre 3 diagnostics, pas
une vraie paire diagnostic/correction).

**Décision sur les 5 diagnostics individuels** — David a testé les 4 cas
restants avec succès. **Retirés du panneau** (`check_zones_coherence`,
`check_type_entite_coherence`, `check_origine_reelle_coherence`,
`check_conventions_territoires`, `check_patron_spatial_coherence`),
traçabilité ajoutée au manuel (§4 + tableau §6), toujours utilisables en
CLI directe.

**Point 4.5 (onglet GUI "Chantiers")** — livré en entier, voir §1.3.

### 1.2 — Audit complet du panneau (au-delà des 5 diagnostics)

- **Aucun nouveau doublon trouvé** parmi les 21 entrées restantes
  (vérifié en lisant les docstrings, pas juste les noms).
- **Nouvelle règle actée** : un script one-shot n'a plus sa place dans le
  panneau, même pour un usage résiduel ponctuel (`--force`...) — 🪦 et 🧩
  sont désormais mutuellement exclusifs dans la légende du manuel.
  Appliquée à `build_geographie_monde.py` (les 6 scénarios sont
  définitifs, confirmé par David) et `fix_alliance_suffixes.py` (bug de
  suffixe confirmé résolu partout via `--dry-run --verbose`, 0
  correction). **21 → 19 entrées.**
- **Bug généralisé trouvé et corrigé** : `scan_geographie_complet` plantait
  ("one of the arguments --scenario --all is required") faute de
  validation GUI. Généralisé à 9 autres scripts partageant le même défaut
  (`required_one_of` + `validateRequiredGroups()`, appelée au clic
  Lancer). En creusant plus loin : 2 formes supplémentaires du même bug
  trouvées sur `zoning_topdown_test` et `reparenter_sous_zones_orphelines`
  (invisibles au premier grep, pas de `mutually_exclusive_with`) — un
  champ `required: true` déjà présent dans le schéma s'est révélé
  **purement cosmétique** (jamais vérifié avant le clic Lancer). Corrigé :
  `validateRequiredFields()` + nouveau champ `required_if` pour les cas
  conditionnels (`--raison-suspicion` requis avec `--zone-suspecte`,
  `--type` requis avec `--slug`).
- **Passage de clarté complet sur les 19 scripts restants** : titres et
  descriptions réécrits en langage utilisateur, "Dry run" harmonisé en
  "Simulation (aucune écriture)" partout (11 occurrences), jargon
  technique reformulé sans perdre la précision (ex. "slug" → "identifié
  par son nom de fichier technique").
- **`gui_verified` mis à jour** pour 3 scripts réellement exercés via le
  GUI cette session (`scan_geographie_complet`, `generer_zones_topdown`,
  `zoning_topdown_test` — ces deux derniers via l'onglet Chantiers, pas
  leur propre formulaire).

### 1.3 — Point 4.5 : onglet GUI "Chantiers"

Cycle complet (lister → générer proposition IA → approuver/rejeter →
appliquer → ignorer/marquer traité), décidé avec David au démarrage.

- **5 nouvelles routes Flask** (`app.py`) : `GET /api/chantiers` (liste
  filtrable), `POST /api/chantiers/generer` (proposition IA pour un seul
  chantier, granularité que `generer_zones_topdown.py --review-topdown`
  n'offre pas), `POST /api/chantiers/approuver`, `POST
  /api/chantiers/statut`, `POST /api/chantiers/appliquer` (délègue à
  `generer_zones_topdown.py --apply-topdown` en sous-processus, scope
  scénario ou tous). Toutes lisent/écrivent `chantiers_geographie.yaml`
  directement (pas d'import de `generator/chantiers.py` — même
  convention de séparation de codebase que le reste du fichier).
- **Frontend** (`index.html` + `app.js`) : nouvel onglet nav, liste
  groupée par scénario, badges type/statut/approbation, aperçu de
  proposition, actions contextuelles par ligne.
- **Testé en conditions réelles par David** : cas complet sur
  `policy_reform/bloc_souverainiste_non_signataire` — généré, approuvé,
  appliqué avec succès.
- **Limite connue, non traitée** : pas de granularité "appliquer un seul
  chantier" — comme `--apply-topdown` lui-même, `/api/chantiers/appliquer`
  applique tout un scénario (ou tous) d'un coup. Nécessiterait un filtre
  `--id` côté `generator/generer_zones_topdown.py`, pas fait.
- **Trouvaille en cours de route, pas corrigée** : la route Carte
  existante `/api/carte/appliquer_zone_topdown_suspecte` écrit encore
  dans l'ancien `patron_spatial_suspectes.yaml` — jamais migrée vers
  `chantiers.py` le 25 juillet. Signalé à David, laissé tel quel (hors
  scope de la session).

### 1.4 — Chantier non prévu : validation approfondie d'`inject_signals`

Parti d'une simple demande de clarté GUI, a fini par occuper le plus gros
de la session suite à des tests réels en conditions réelles par David.

**Bugs GUI trouvés et corrigés (`app.js`)** :
- `_appendYamlQueue()` (bouton "Ajouter à la queue") calculait une
  validation de champs requis mais ne la vérifiait jamais — et le
  sélecteur qu'elle utilisait ne pouvait de toute façon rien filtrer
  (`data-optional` jamais posé nulle part). Cas réel : une entrée avec la
  description vide est passée sans encombre, aurait fait planter
  `inject_custom_signals.py` sur `idea["description"]`. Corrigé
  (`_markOptional()` + validation réellement bloquante), et généralisé
  aux 3 scripts à file d'attente — en re-vérifiant dans le code de
  chacun quels champs sont réellement optionnels (`inject_signals`:
  `id` ; `inject_events`: `id`, `scenarios` ; `create_entities`:
  `scenario_hint`, `role`, `etat` — tous marqués à tort comme requis
  jusqu'ici).
- Mode "Édition brute" affichait un **instantané périmé** du fichier
  (capturé une seule fois à l'ouverture du script) — sauvegarder depuis
  ce mode pouvait écraser un ajout fait entre-temps via le formulaire
  guidé. Cas réel vécu : une entrée bien ajoutée s'est fait écraser par
  ce mécanisme. Corrigé : rechargement depuis le disque à chaque bascule
  vers ce mode.

**Bug de fond trouvé et corrigé (`inject_custom_signals.py`)** :
- `regenerate_registre()`/`parse_registre_table()` ne reconnaissaient que
  le format de séparateur de tableau compact (`|---|`) — une section du
  registre (`## breakdown`) avait été reformatée avec des espaces
  d'alignement (probablement par un éditeur Markdown), invisible au
  format attendu. Conséquence : plantage (`TypeError: unsupported
  operand type(s) for +: 'NoneType' and 'int'`) dès l'écriture réelle (le
  dry-run ne passe jamais par cette fonction, d'où le bug resté invisible
  jusqu'à un vrai run). Corrigé avec `_est_ligne_separateur()`, robuste
  aux deux formats — testé contre le vrai fichier de David, les 6
  sections se parsent maintenant correctement. Au passage : ajout d'un
  `.bak` manquant avant l'écriture du registre (seul point d'écriture du
  pipeline géographie qui n'en avait pas).

**Incident de données traité manuellement** : le signal
`norvege_terres_rares_levier_geopolitique` (produit par le run qui a
plantouillé pendant la découverte du bug ci-dessus) s'est retrouvé
**dupliqué** dans `variables/geopolitique_conflits.md` (le crash
survenait après l'écriture de la fiche variable mais avant celle du
registre — un re-run ultérieur a réinjecté par-dessus sans le savoir).
Nettoyé entièrement à la main (les deux occurrences + les 6 lignes du
registre), pendant qu'un 3e essai (`norvege_terres_rares_geopolitique`,
réussi sur les 2 variables cette fois) a été vérifié propre et conservé.

**Améliorations de fond décidées avec David** :
- **Collision de fenêtre entre signaux différents** rétrogradée de
  blocage à avertissement — le registre existe pour éviter les doublons
  *accidentels*, pas pour interdire à deux signaux réellement
  indépendants de coexister sur la même période. Le cas de collision
  interne (même nouveau signal, deux scénarios, même fenêtre) reste
  bloquant — lui, c'est un vrai signe de bug de génération.
- **Prompt de correction enrichi** : consignes explicites désormais pour
  le dépassement de mots (reformuler autour du fait central plutôt que
  couper un mot) et pour la collision de fenêtre (décaler la fenêtre,
  pas le contenu narratif) — avant, silencieux/implicite, ce qui
  expliquait en partie pourquoi `energie_ressources_critiques` avait
  échoué après ses 2 essais sur le cas réel testé.
- **Cohérence thématique avec les signaux existants** — jusqu'ici la
  section 12 était montrée au LLM "pour le style" uniquement, sans
  consigne de cohérence. Ajouté : repérage lexical par mots-clés partagés
  (`_signaux_thematiquement_proches()`, pas de la vraie sémantique — pas
  d'infra d'embeddings ici) + champ obligatoire dans la réponse JSON du
  LLM (`signaux_existants_consideres`), qui doit expliciter comment il
  s'est positionné (ou dire explicitement qu'il n'a rien trouvé) — rendu
  vérifiable dans la fiche d'audit plutôt que silencieux.
- **`zone_hint`** ajouté à `inject_custom_signals.py` (n'existait pas du
  tout, contrairement à `inject_custom_events.py`) — même mécanisme,
  glissé dans le prompt. Renforcé ensuite avec deux consignes explicites
  suite à des questions de David : privilégier le lieu mentionné dans
  l'idée source en cas de conflit avec le hint, et ne pas forcer une zone
  incohérente scénario par scénario (la zone vient d'un seul scénario,
  rien ne garantit qu'elle existe dans les 5 autres — limite connue,
  acceptée telle quelle, pas de vérification mécanique).
- **"Intensité" pour les signaux** — pas ajouté, décision explicite : pas
  d'équivalent structurel (contrairement aux événements, un signal décrit
  une évolution par scénario, pas un niveau global unique).

**Compréhension confirmée du parcours complet d'un signal** (utile pour
la suite) : queue → sélection de variable(s) → rédaction par variable (6
scénarios) → validation mécanique → écriture (fiche variable + registre +
fiche d'audit) → consommé plus tard par `prompt_builder.py` au moment de
générer un article, filtré par `scope` (majeur/structurant/local, calculé
dans `snapshot.py` selon le nombre de variables partageant le même
`evenement_cle` et si une variable pilote est impliquée) et par une
rotation à mémoire anti-répétition. **Conclusion actionnable pour
David** : les événements custom (Priorité 0, inconditionnels) sont plus
fiables pour influencer le monde de façon garantie ; les signaux restent
une texture de fond, jamais garantie d'apparaître dans un article donné.

### 1.5 — `undo_custom.py` : nouveau type `signal`

Demandé par David en voyant qu'aucun outil n'existait pour annuler un
signal (`undo_custom.py` ne connaissait que `instance`/`event_instance`/
`entite`/`event`).

- **`resolve_signal_variables()`** : retrouve les fiches variables
  concernées via `variables_cibles` de la fiche d'audit, avec repli sur
  un scan complet si la fiche est absente.
- **`remove_signal_from_variable()`** : retire annotation section 7 +
  bloc(s) section 12 (gère le cas dupliqué, comme celui nettoyé à la main
  au §1.4).
- **`remove_signal_from_registre()`** : retrait par correspondance exacte
  de colonne (pas de sous-chaîne) + **recalcul du total** — piège identifié
  en le faisant à la main plus tôt dans la session.
- **`remove_signal_fiche_and_logs()`** : supprime la fiche d'audit +
  nettoie `processed.yaml`/`needs_review.yaml` du dossier `signaux_custom/`.
- **Testé en conditions réelles** contre les vrais fichiers manipulés ce
  soir (dry-run puis exécution réelle) — résultat identique au nettoyage
  manuel fait plus tôt (485 entrées, 72 signaux uniques).

**Câblage GUI associé** :
- Nouvelle route `/api/slugs?type=signals` + `_scan_signal_slugs()`
  (`app.py`) — le sélecteur "Fiche cible" n'avait aucune source pour
  lister des signaux.
- Nouveau mécanisme générique `slug_type_field`/`slug_type_map`
  (`scripts_config.json` + `app.js`) : la source de `--slug` change
  dynamiquement selon la valeur de `--type` — réutilisable pour un futur
  script avec le même besoin.
- Nouveau mécanisme générique `hide_when` (`scripts_config.json` +
  `app.js`) : masque un champ entier selon la valeur d'un autre (utilisé
  pour masquer "Étendue de l'annulation", qui n'a pas de sens pour un
  signal).
- **Aucun de ces 3 mécanismes GUI n'a été testé dans un vrai navigateur**
  — seule la logique Python (`undo_custom.py`) a été testée en conditions
  réelles. Voir §3.

### 1.6 — Addendum du 27 juillet : marathon de validation `inject_signals`

Ce qui devait être "un dernier test réel" avant clôture (§4 de la version
précédente de ce handoff, point 3) a duré ~1h et traversé 5 bugs
supplémentaires — un vrai test en usage prolongé, pas une vérification
isolée. **Résultat final : succès confirmé de bout en bout**, sur une
idée réelle (irrigation solaire + tensions hydriques, `zone_hint: Sahel`),
`status: injected` dans `processed.yaml`, et confirmation qualitative que
les 6 scénarios générés incarnent bien le Sahel différemment selon la
logique de chaque scénario plutôt que de répéter le même contexte.

**Les 5 bugs, dans l'ordre de découverte** :
1. Deuxième variable (`variables/energie_ressources_critiques.md`) avec le
   même symptôme "fence manquante" que le bug du registre du 26 (mais un
   fichier différent, cette fois sans lien avec le bug déjà corrigé —
   fichier réellement mal formé, cause inconnue).
2. Hallucination "Scénario inconnu" — le LLM a ajouté une 7e clé nommée
   comme la variable elle-même dans `scenarios`. Corrigé côté prompt
   (`FORMAT_RULES` + consigne de correction dédiée).
3. Plafond `variable_hint_count` jamais vérifié mécaniquement (3 variables
   retournées au lieu du plafond de 2). Corrigé : troncature mécanique
   après l'appel LLM.
4. Annotation section 7 écrite sans le préfixe `signal_custom:` attendu,
   rendant la ligne invisible au retrait par `undo_custom.py`. Corrigé des
   deux côtés (prompt + regex de retrait tolérant aux deux formats).
5. **Bug le plus sérieux, causé par `undo_custom.py` lui-même** : son
   regex de retrait du bloc section 12 avalait la fence de fermeture
   quand le signal retiré était le dernier du bloc — cassant le fichier
   une seconde fois après une première réparation. Trouvé seulement après
   plusieurs cycles complets (queue → échec → nettoyage → re-queue →
   nouvel échec ailleurs), jamais lors du test initial du 26 juillet.

**Leçon retenue, à garder pour toute future fonction de retrait de contenu
structuré** : un script "testé en conditions réelles" une fois ne veut
pas dire "à l'abri des cas limites" — les bords de fichier (première/
dernière entrée d'un bloc) méritent un test dédié, pas juste un test sur
le cas nominal.

**Fichiers finaux, tous re-livrés en fin de session pour éviter toute
confusion de version** : `inject_custom_signals.py`, `undo_custom.py`
(2 correctifs supplémentaires : croisement fiche/registre dans
`resolve_signal_variables()`, et le bug de fence ci-dessus), plus les 2
fiches variables réparées manuellement (`systemes_productifs_travail.md`,
`energie_ressources_critiques.md`).

---

## 2. Fichiers livrés aujourd'hui

| Fichier | Statut |
|---|---|
| `gui/scripts_config.json` | 19 entrées (21→19). Testé en usage réel pour la partie scan_geographie_complet/Chantiers ; **pas testé visuellement** pour les mécanismes `hide_when`/`slug_type_field` (undo_custom) |
| `gui/app.js` | Onglet Chantiers + tous les mécanismes génériques ci-dessus. Syntaxe validée, logique testée isolément, **rendu navigateur non confirmé** pour les ajouts de fin de session |
| `gui/app.py` | 5 routes Chantiers + route `/api/slugs?type=signals`. Syntaxe validée, **jamais exécuté dans un vrai Flask** cette session (pas d'environnement serveur ici) |
| `gui/templates/index.html` | Onglet Chantiers (markup + CSS inline) |
| `generator/inject_custom_signals.py` | Bug registre corrigé + testé contre le vrai fichier, améliorations de fond (fenêtre/cohérence/zone_hint) — **pas encore re-testé en conditions réelles après tous ces changements cumulés** |
| `generator/undo_custom.py` | Type `signal` complet, testé en conditions réelles (dry-run + exécution) |
| `documentation/USER_MANUAL_COMPLET.md` | Mis à jour pour §1.1/§1.2 (niveau 2, 5 diagnostics, audit sidebar) **uniquement** — **PAS mis à jour pour 4.5, inject_signals, ni le type `signal` d'undo_custom** (voir §4, point 1) |

**Fichiers de données corrigés à la main pendant la session** (déjà
intégrés par David, mentionnés ici pour mémoire) : `variables/
geopolitique_conflits.md`, `registre_evenements.md`, `signaux_custom/
needs_review.yaml`, `signaux_custom/queue.yaml`.

---

## 3. Points de vigilance nouveaux (en plus de ceux déjà dans `USER_MANUAL_COMPLET.md`)

- **Rien de ce qui touche à `app.py`/`app.js`/`index.html` cette session
  n'a été vu tourner dans un vrai navigateur** — je n'ai pas d'environnement
  pour ça ici. Priorité au prochain test réel : onglet Chantiers (déjà
  partiellement validé par David lui-même), puis spécifiquement le menu
  Type d'`undo_custom` (bascule "Fiche cible" entités↔signaux, masquage
  d'"Étendue de l'annulation").
- **Un script qui plante APRÈS avoir déjà écrit sur disque peut laisser
  une trace partielle invisible au prochain lancement** — le cas
  `norvege_terres_rares_levier_geopolitique` (fiche variable modifiée,
  registre pas encore écrit au moment du crash) en est un exemple concret
  cette session. Réflexe pour tout futur diagnostic de crash similaire :
  vérifier l'ordre réel des écritures dans la fonction, pas juste le
  message d'erreur.
- **`inject_custom_signals.py` a reçu beaucoup de changements cumulés ce
  soir** (bug registre, prompts de correction, cohérence thématique,
  zone_hint) **sans un nouveau test de bout en bout après le dernier
  changement** (zone_hint + consignes de cohérence renforcées). À faire
  avant de considérer le script stabilisé.
- **`scripts_config.json` : deux nouveaux mécanismes génériques**
  (`hide_when`, `slug_type_field`/`slug_type_map`) viennent s'ajouter à
  `depends_on`/`mode_only`/`required_one_of`/`required_if` — le fichier
  accumule maintenant 6 mécanismes de comportement conditionnel distincts.
  Pas un problème en soi, mais à garder en tête si un futur script a
  besoin d'un 7e cas de figure : vérifier d'abord qu'aucun des 6
  existants ne le couvre déjà avant d'en inventer un nouveau.

---

## 4. Backlog ouvert pour la prochaine session

1. **Mettre à jour `USER_MANUAL_COMPLET.md`** — ✅ **fait** (27 juillet,
   avant la fin de session) : Chantiers (4.5), session `inject_signals`
   complète (bug registre, zone_hint, cohérence thématique, les 5 bugs de
   l'addendum §1.6), type `signal` d'`undo_custom.py` avec ses 2 bugs
   supplémentaires, les mécanismes génériques GUI.
2. **Tester dans un vrai navigateur** tout ce qui a été construit côté
   GUI (Chantiers, menu Type d'`undo_custom`, `hide_when`,
   `slug_type_field`) — **toujours pas fait**, aucun environnement
   navigateur disponible côté Claude pour le confirmer soi-même.
3. ~~Re-tester `inject_custom_signals.py` de bout en bout~~ — ✅ **fait**,
   voir §1.6. Validé de bout en bout sur un cas réel.
4. **`/api/carte/appliquer_zone_topdown_suspecte` non migrée vers
   `chantiers.py`** (trouvaille du §1.3) — toujours pas tranché.
5. Reste du backlog antérieur non touché cette session (voir les handoffs
   précédents pour le détail) : P8 (enrichissement des 426 fiches
   `officialise_minimal`), P11/P20/P21 (scoping uniquement), passage du
   tier `strict` sur `claude-sonnet-5` en prod.

---

## 5. Point de reprise suggéré pour demain

1. David teste dans son navigateur les changements GUI (Chantiers déjà
   partiellement fait par l'usage réel ; menu Type d'`undo_custom`,
   `hide_when` et `slug_type_field` jamais vus tourner visuellement).
2. Décision sur `/api/carte/appliquer_zone_topdown_suspecte` (§4, point 4).
3. `inject_signals` et `undo_custom` (type `signal`) sont maintenant
   validés de bout en bout sur un cas réel — mais un seul cas. Un usage
   normal continu (pas un test dédié) reste la meilleure vérification
   dans la durée, comme pour tout le reste du panneau.
4. Reprendre le reste du backlog antérieur (§4, point 5) si rien d'urgent
   ne remonte.
