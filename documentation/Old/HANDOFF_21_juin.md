# Ourrassol 2098 — Résumé de handoff (pour nouvelle conversation)

Document préparé le 2026-06-21 pour permettre la reprise du projet dans
une nouvelle conversation sans avoir à relire tout l'historique. Fait
suite au HANDOFF du 20 juin (chantiers de cette session précédente
tous clos sauf mention contraire ci-dessous).

## CONTEXTE GÉNÉRAL DU PROJET

Simulateur de presse fictive située en 2098, basé sur un vault
Obsidian + pipeline Python + API Claude. Architecture inchangée par
rapport au handoff précédent (12 variables, 6 scénarios, 20
thématiques, entités/instances, événements custom, registre
d'anti-collision). Nouveauté de cette session : un système de
géographie/géopolitique par scénario (`geographie/`), encore en
construction.

**Important sur le mode de travail** : Claude (l'assistant) n'a jamais
accès à la clé API Anthropic ni à internet dans son environnement de
travail. Tous les scripts impliquant un vrai appel à l'API Claude sont
écrits et testés mécaniquement (syntaxe, logique pure, données réelles
du vault chargées en lecture) par l'assistant, mais **toujours lancés
par l'utilisateur lui-même chez lui**, avec sa propre clé API. Le
cycle de travail type : assistant écrit/corrige le script → utilisateur
lance en `--dry-run` → utilisateur colle le résultat → assistant
diagnostique d'éventuels bugs (souvent révélés uniquement par un vrai
appel API, jamais visibles en test mécanique) → corrige → relance.
Plusieurs bugs réels de cette nature ont été trouvés et corrigés cette
session (voir plus bas) : toujours commencer par `--dry-run`, jamais
lancer un nouveau script directement en écriture réelle.

## CHANTIERS CLOS CETTE SESSION (21 juin)

### 1. Phase 1 — Officialisation alliances/oppositions (suite et fin)
Chantier hérité du 20 juin, terminé ce jour-là mais avec un bug
découvert et corrigé le 21 :
- **Bug trouvé** : `officialize_alliances.py` réécrivait le frontmatter
  YAML (`alliances:`/`oppositions:`) mais oubliait la section
  `## Relations` du corps markdown, qui dupliquait les mêmes
  informations en wikilinks texte libre. Corrigé rétroactivement sur
  les 75 fichiers concernés (reconstruction position-par-position,
  fiable à 100%, sauvegarde créée avant).
- Résultat : avertissements `validate.py` passés de 732 à 0 (voir
  point 3 ci-dessous pour le détail complet de cette réduction).

### 2. Avertissements `validate.py` — 1068 (handoff initial) → 732 → 0
Travail mené en plusieurs passes :
- **`VALID_CATEGORIES`** de `validate.py` était obsolète/incomplète
  (manquait `entreprise`, `IA`, `média` — catégories légitimes et déjà
  utilisées dans le vault). Corrigé.
- **`COHERENCE_MAP`** (cohérence `etat_temporel` ↔ `state_of_system`
  du scénario) trop restrictive : `actif` ajouté comme accepté pour
  `chaotique`, `transformé` ajouté comme accepté pour `instable` —
  décisions prises au cas par cas après lecture des fiches concernées
  (jugées narrativement cohérentes, pas des erreurs).
- **`impact_local`/`impact_systemique_global` hors plage [0-5]** : 72
  fiches anciennes (résidu de l'ancien `generate_entities.py`, jamais
  contraint sur l'échelle) recalibrées via un nouveau script dédié
  `fix_impact_scale.py` (voir section scripts). Coût réel ~$0,30-0,40.
- **2 fiches manquantes** (`Gouvernement d'Israël`, `République
  Islamique d'Iran`) créées manuellement pour combler une référence
  d'acteurs géopolitiques réels dans `event_instances/
  conflit_israel_iran_2026_policy_reform.md` (texte libre → slugs).
- **Résultat final vérifié** : `python3 validate.py` → **0 erreurs,
  0 avertissements**, confirmé sur le vault complet.

### 3. Règle technique anti-texte-libre pour alliances/oppositions
Décidée le 20 juin comme principe déclaratif, **implémentée
techniquement** le 21 :
- `generate_instances.py` (et son successeur `create_entities_and_
  instances.py`) : le prompt liste désormais les instances réellement
  disponibles dans le même scénario (slug + nom), avec consigne
  stricte de ne référencer QUE ces slugs. Nouvelle fonction
  `clean_relations()` : filtre mécaniquement toute entrée non
  conforme avant écriture (nettoyage silencieux, pas de retry — décision
  explicite de l'utilisateur).
- `validate.py` : distingue désormais clairement "texte libre" (avec
  message explicite renvoyant vers la règle) vs "slug cassé/instance
  manquante" dans ses avertissements.

### 4. Fusion `create_entity.py` + `generate_instances.py`
Prévue depuis le handoff initial ("développés séparément pour itérer
plus vite, fusion prévue à terme"). Faite cette session :
nouveau script **`create_entities_and_instances.py`**, qui remplace
les deux anciens (toujours présents dans `generator/` à titre
d'archive, plus le flux recommandé). Comportement validé avec
l'utilisateur avant codage : un seul run, entité → instances enchaînées
automatiquement (plus besoin de relancer un second script) :
- **Mode custom** : décrit une instance de référence dans
  `entites_custom/queue.yaml`, Claude déduit l'archétype, crée
  l'entité PUIS enchaîne automatiquement la génération de toutes ses
  instances (scenario_hint, ou les 6 scénarios par défaut).
- **Mode auto** : demande un nombre N, Claude invente N entités, CHACUNE
  enchaîne automatiquement sur SES `scenarios_instances` proposés
  (pas systématiquement les 6).
- Résilience : un échec d'instance n'interrompt pas les
  scénarios/entités suivants (même logique que l'ancien
  `generate_instances.py`).
- **Testé en conditions réelles avec succès** : mode auto, 1 entité
  ("L'Arbitre des Derniers Recours"), 4 instances enchaînées
  automatiquement, contenu narrativement riche et cohérent, 0
  hallucination de slug dans alliances/oppositions.

### 5. Résolution des slugs en noms dans les articles générés
Découverte en cours de session : contrairement à ce qu'affirmait le
handoff du 20 juin ("`prompt_builder.py` n'exploite actuellement
JAMAIS ces champs"), **`alliances`/`oppositions` étaient en réalité
déjà exploités** dans le pipeline de génération d'articles
(`loader.py` → `snapshot.py` → `prompt_builder.py::
build_entities_context()`) — mais affichés en **slugs bruts**
(`nexcore_breakdown`) plutôt qu'en noms lisibles. Corrigé : nouvelle
table de résolution slug→nom construite à partir de
`snapshot["all_instances"]` (toutes les instances du scénario, pas
seulement celles sélectionnées pour l'article en cours), avec
fallback sûr si un slug n'est pas trouvé. Vérifié sur données réelles
du vault.

### 6. `zone_geographique` — ajout de la valeur "orbital" + validation stricte
- Découvert que "orbital" était déjà utilisé spontanément par Claude
  (3x, sur Consortium Helios, infrastructures orbitales) sans être
  dans la liste suggérée par les prompts. Ajouté officiellement comme
  7e valeur (`locale|urbaine|nationale|régionale|continentale|globale|orbital`)
  dans `generate_instances.py` et `create_entities_and_instances.py`.
- **Nouvelle validation stricte ajoutée dans `validate.py`**
  (`VALID_ZONES_GEOGRAPHIQUES`) — ce champ n'était jusqu'ici PAS
  contrôlé mécaniquement (contrairement à `category`/`etat_temporel`).
  Décision explicite de l'utilisateur de le rendre strict. Coût de
  cette validation supplémentaire mesuré comme négligeable
  (~0,0001 ms pour tout le vault).

### 7. Bible géographique par scénario — étape 1 (schéma plat)
Nouveau chantier majeur de cette session, né d'une question de
l'utilisateur sur où la géographie réelle (pays/continents) était
gérée dans le vault. Réponse : nulle part de façon structurée — un
scan a montré 33 variantes informelles de blocs géopolitiques
("Bloc Eurasien", "Bloc Eurasien Central", "Union Eurasiatique"...)
nées sans coordination au fil des générations.

**Décision de conception (validée avec l'utilisateur)** : créer une
"bible monde" par scénario (6 fichiers `geographie/{scenario}.md`),
rétro-construite à partir du corpus narratif existant (instances +
event_instances), mais éditable manuellement à tout moment (garde-fou
anti-écrasement intégré).

**Script livré : `build_geographie_monde.py`**
- Lit le texte narratif (`description_journalistique`,
  `role_dans_scenario`, `tensions_narratives` des instances ;
  `description`/`consequences`/`realisation` des event_instances) de
  tout un scénario, l'envoie à Claude pour synthèse.
- Schéma de "zone" (nœud géographique) actuel — voir plus bas pour
  le détail complet ; champs clés : `slug`, `nom`, `niveau` (toujours
  1 pour l'instant), `type`, `parent` (toujours null pour l'instant),
  `origine_reelle` (filiation vers pays/subdivisions réelles 2026 —
  TOUJOURS renseignée, même approximative), `statut`,
  `periode_transition`, `evenement_transition` (slug d'event_instance
  si applicable), `lieux_emblematiques`, `relations` (allies/rivaux —
  DOIVENT être des slugs d'autres zones du même scénario, jamais un
  slug d'instance ni un concept inventé), `sources_attestees`.
- Garde-fous mécaniques : validation stricte de chaque zone
  (`validate_zone`), filtrage anti-hallucination des
  `sources_attestees` et `evenement_transition` contre le vrai corpus,
  filtrage des `relations` (`clean_zone_relations`) contre les vraies
  zones du batch.
- `--dry-run` fait un VRAI appel API (bug initial corrigé — la
  première version retournait `{"zones": []}` codé en dur sans
  appeler l'API, donnant un faux "0 zone identifiée" trompeur).
- `--force` régénère en écrasant, avec sauvegarde `.md.bak`
  automatique. Sans `--force`, refuse d'écraser un fichier existant
  (protection des éditions manuelles).

**Bug trouvé et corrigé en cours de route** : `relations`
(allies/rivaux) référençait parfois des slugs d'instances ou des
concepts inventés plutôt que de vraies zones du même scénario (7 cas
sur 104 références, sur le premier jeu de 6 bibles). Corrigé via
consigne prompt renforcée + nouveau filtre mécanique
`clean_zone_relations()`.

**État final vérifié** : les 6 bibles ont été régénérées avec le
schéma complet (`origine_reelle`, `periode_transition`,
`evenement_transition` inclus) et **intégralement vérifiées** : YAML
valide ×6, 0 doublon de slug sur 51 zones, 0 référence cassée sur 73
relations, 0 hallucination sur 254 sources_attestees et 23
evenement_transition. `eco_communalism` (scénario redouté pauvre en
géopolitique) a produit une bible riche et cohérente avec son esprit
(unions régionales et territoires autonomes plutôt que blocs
continentaux — ex: "Bioterritoires d'Amérique du Nord", référence au
Chiapas zapatiste).

## CHANTIERS OUVERTS / EN PAUSE, NON RÉSOLUS

### 8. Bible géographique — étape 2 : maillage hiérarchique récursif
**Décision de conception actée mais PAS codée.** Discussion approfondie
avec l'utilisateur :
- Le schéma de "nœud" doit être **récursif à profondeur libre** —
  pas de niveaux fixes (Bloc/Pays/Région/Ville) imposés à tous les
  scénarios, car certains scénarios (ex: eco_communalism) ont une
  géographie naturellement différente (entités régionales plutôt que
  blocs). C'est le `type` du nœud qui varie librement selon ce qui a
  du sens, pas une position fixe dans une hiérarchie à N étages.
- Relation nœud fictif ↔ pays réel : **many-to-many confirmée** — un
  nœud peut fusionner plusieurs pays réels (ex: Bloc Atlantique =
  USA+Canada+UK), ET un même pays réel peut être scindé entre
  plusieurs nœuds du même scénario (ex: France coupée entre deux
  blocs rivaux). D'où le schéma `origine_reelle` actuel
  `[{entite, type_entite, portion}]` plutôt qu'une simple liste de
  noms.
- **Séquencement validé** : étape 1 (schéma plat, faite) puis étape 2
  (sous-arbre récursif, séparée) — pas tout en une fois, pour limiter
  le risque de qualité inégale entre scénarios sur un chantier aussi
  ambitieux. Raison : enrichir récursivement demande à Claude
  d'INVENTER de la matière nouvelle cohérente sur 6 mondes à la fois
  (contrairement à l'étape 1 qui extrayait/synthétisait du contenu
  déjà existant) — risque de dérive de qualité reconnu explicitement,
  pas encore mitigé par une vraie conception de script.
- Piste de mitigation évoquée mais pas tranchée : découper le travail
  zone par zone plutôt qu'un mega-prompt par scénario, donner un
  gabarit indicatif commun (ex: "2-4 sous-zones par zone existante").

### 9. Champ `localisation` sur instances/événements
**Conception largement avancée, RIEN codé.**
- Schéma validé : `localisation: {zone: slug_zone_existante,
  lieu: texte_libre, type_lieu: ville|region|infrastructure|
  site_strategique}`. `zone` doit référencer un slug réellement
  présent dans `geographie/{scenario}.md` (validé mécaniquement) ;
  `lieu` reste du texte libre assumé (cas discuté : une ville réelle
  peut survivre même si le pays qui la gouvernait a disparu —
  ex. São Paulo dans un monde où le Brésil n'existe plus en tant que
  tel).
- **Diagnostic chiffré sur l'ampleur réelle** (vérifié sur le vault
  21 juin) : sur 521 instances, seules **95 ont un contenu narratif
  réel** exploitable pour extraire une localisation — les 426
  restantes sont `statut: officialise_minimal` (placeholders
  `(à développer en phase 2)`, 100% vides de contenu narratif
  exploitable). Les **24 event_instances**, en revanche, sont TOUTES
  riches en contenu (0 placeholder).
- **Conclusion actée avec l'utilisateur** : un script d'extraction
  ciblé sur les 95+24 = **119 fiches riches**, PAS sur les 426
  fiches minimales (qui seront traitées plus tard, au moment de leur
  enrichissement en phase 2 — le champ localisation s'intégrera
  alors directement dans CE geste d'enrichissement, pas via un script
  séparé après coup).
- **Trois issues possibles par fiche**, actées avec l'utilisateur,
  aucune ne doit être forcée :
  1. Lieu précis trouvé dans le texte → extrait
  2. Pas de lieu pertinent et c'est normal (ex: une organisation
     transnationale "sans ancrage local fort" — l'ITA vue en exemple
     réel dans le vault) → champ laissé vide, assumé
  3. Ambigu → signalé pour review manuelle, jamais deviné
    silencieusement
- **PAS ENCORE TRANCHÉ** : le mécanisme d'enrichissement ORGANIQUE de
  la bible géographique (quand une NOUVELLE instance est créée et
  qu'aucune zone existante ne convient). Deux décisions actées :
  (a) **jamais d'ajout automatique** à la bible, (b) **l'instance
  reste bloquée** (rien créé) tant que la nouvelle zone proposée n'a
  pas été validée manuellement par l'utilisateur — pas de création
  avec "localisation en attente". Reste à trancher : comportement du
  mode batch/auto face à un blocage (continuer les autres entités du
  batch, ou tout arrêter ?), format exact de la file d'attente de
  zones proposées, processus concret de review. Discussion explicitement
  mise en pause par l'utilisateur ("je ne suis pas prêt à prendre des
  décisions sur l'enrichissement mécanique").
- **Interface envisagée** (pas codée) : en mode custom CLI, afficher
  les zones/lieux déjà disponibles de la bible du scénario concerné et
  demander un choix interactif au clavier, plutôt que de laisser
  retaper un slug de mémoire.

### 10. Historique multi-étapes des transitions géographiques
**Juste évoqué, pas conçu en détail.** Pour l'instant, l'étape 1 ne
capture qu'UNE période de transition par zone
(`periode_transition: "2031-2045"`). L'utilisateur voudrait à terme
plusieurs étapes possibles (ex: 2031 premier pacte, 2045 fusion
complète, 2067 réorganisation interne). Jugé nettement plus complexe
que le reste (risque de dupliquer ce que le registre d'événements
fait déjà). **Principe acté** : relation bidirectionnelle avec le
registre d'événements — (a) la construction de l'historique doit
D'ABORD chercher les événements déjà existants pertinents pour chaque
transition plutôt que d'en réinventer, (b) toute transition
significative sans événement existant devrait pouvoir DÉCLENCHER la
création d'une vraie fiche événement dédiée, avec références croisées
dans les deux sens plutôt que duplication de contenu. Dépend de la
stabilisation du point 8 (maillage récursif) avant d'être attaqué.

Discussion connexe non résolue : possibilité de voir le contenu d'une
bible comme des "instances" d'un "scénario" au sens où le système le
fait déjà pour les entités — exploré en profondeur avec l'utilisateur,
conclusion nuancée : peu utile pour AMÉLIORER LA GÉNÉRATION D'ARTICLES
en tant que telle (le pipeline est cloisonné par scénario, jamais de
lecture croisée entre scénarios au moment de générer un article), mais
potentiellement utile pour des requêtes ANALYTIQUES transversales
("tracer l'impact d'un même événement à travers les 6 mondes" —
inter-scénario) ou, suite à clarification de l'utilisateur, pour des
requêtes **intra-scénario** ("quelles zones d'UN scénario ont été
impactées par tel événement") — cette dernière étant en fait déjà
quasi-possible avec le schéma actuel (`evenement_transition` sur
chaque zone), juste pas encore interrogeable facilement dans ce sens.
Piste simple évoquée et non tranchée : un petit script de requête
plutôt qu'un changement de schéma.

### 11. Connecter `geographie/{scenario}.md` à `prompt_builder.py`
**Identifié comme le levier le plus direct pour la crédibilité des
articles, PAS codé.** Constat explicite en fin de session : la bible
géographique, aussi riche soit-elle, n'a aujourd'hui AUCUN effet sur
les articles générés tant qu'elle n'est pas lue par
`prompt_builder.py` au moment de la génération (sur le modèle de ce
qui a été fait au point 5 pour les entités). C'est distinct du champ
`localisation` (point 9) — il s'agirait ici d'injecter le contexte
des zones du scénario (noms, statuts, tensions) dans le prompt
général de l'article, pour que les lieux mentionnés restent cohérents
avec la bible plutôt que d'être réinventés à la volée par Claude à
chaque génération d'article.

### 12. Phase 2 — enrichissement narratif des 426 fiches `officialise_minimal`
Chantier de fond identifié depuis le 20 juin, toujours pas commencé.
424 entités + 424 instances (chiffre devenu 426 après les 2 ajouts
Israël/Iran de cette session) créées par la phase 1 d'officialisation,
avec description minimale et placeholders `(à développer en phase 2)`.
À traiter par lots, au rythme de l'utilisateur, via
`create_entities_and_instances.py` repris sur la base du flag
`officialise_minimal`. Pas de script dédié écrit pour cette reprise
spécifique (le mode "force" de `generate_instances.py`/nouveau script
pourrait s'en charger mais pas testé dans ce sens précis).

### 13. `undo_custom.py`
Toujours pas écrit. Script de nettoyage générique
(`--type signal/evenement/entite --slug X`) pour annuler proprement un
test, évoqué depuis le 20 juin, jamais codé. Utile vu la fréquence
des tests/itérations dans ce projet.

## SCRIPTS LIVRÉS CETTE SESSION (tous dans /mnt/user-data/outputs/generator/
puis à copier dans generator/ par l'utilisateur)

1. **`officialize_alliances.py`** — déjà connu du 20 juin, corrections
   mineures de robustesse (max_tokens, checkpoint/resume) apportées
   le 21 suite à un crash réel en production (lot de 150 mentions →
   JSON tronqué). `CLUSTER_BATCH_SIZE` réduit à 80, `max_tokens` monté
   à 16000, mécanisme de checkpoint (`officialize_checkpoint.json`)
   + option `--resume` ajoutés. Plus un outil "one-shot" actif
   aujourd'hui (la phase 1 est terminée) mais réutilisable si un
   nouveau cas de texte libre massif apparaissait.

2. **`fix_impact_scale.py`** — nouveau, one-shot, recalibre
   rétroactivement `impact_local`/`impact_systemique_global` sur les
   fiches historiques hors plage [0-5]. Deux bugs réels trouvés et
   corrigés en cours de route (dry-run factice sans appel API ;
   réponses Claude avec raisonnement visible non géré, troncature à
   max_tokens=500 → monté à 1024 + extraction du dernier bloc JSON
   trouvé dans le texte plutôt qu'exiger une réponse 100% JSON pure).
   **A été lancé avec succès** sur les 72 fiches concernées
   (72/72 réussi). Probablement plus nécessaire (le stock historique
   est traité), gardé en archive.

3. **`generate_instances.py`** — mis à jour plusieurs fois cette
   session (consigne alliances + `clean_relations`, échelle impact
   0-5, ajout "orbital"). Toujours fonctionnel mais **plus le flux
   recommandé** — remplacé par `create_entities_and_instances.py`
   pour les nouvelles créations. Gardé en archive/référence.

4. **`create_entities_and_instances.py`** — nouveau, fusion de
   `create_entity.py` + `generate_instances.py`. **Le flux recommandé
   désormais** pour toute nouvelle création d'entité/instance. Testé
   en conditions réelles avec succès (voir point 4 ci-dessus).

5. **`validate.py`** — mis à jour plusieurs fois (catégories,
   cohérence état/scénario, validation stricte zone_geographique).
   Note technique connue : contient un chemin absolu codé en dur
   (`VAULT_PATH = "/Users/davidlopez2005/..."`) qui fonctionne très
   bien chez l'utilisateur mais empêche Claude (l'assistant) de le
   lancer directement dans son propre environnement de travail sans
   bidouiller ce chemin à chaque fois (même limitation que
   `loader.py`, `snapshot.py`).

6. **`prompt_builder.py`** — mis à jour (résolution slugs→noms,
   point 5 ci-dessus). Seule fonction modifiée : `build_entities_
   context()`.

7. **`build_geographie_monde.py`** — nouveau, voir point 7 ci-dessus
   pour le détail complet. Script central du nouveau chantier
   géographie.

## FICHIERS DE RÉFÉRENCE DISPONIBLES

Comme précédemment, je (l'assistant) dois redemander à l'utilisateur
d'uploader si besoin de les revoir (pas stockés au-delà de la
session) :
- Le vault complet en zip (le mode de travail standard de ce projet)
- `HANDOFF_20 juin.md` (handoff de la session précédente, antérieur à
  celui-ci)
- Tout fichier précis mentionné ci-dessus si un examen détaillé est
  nécessaire

## COMMENT REPRENDRE EFFICACEMENT

1. Uploader ce document en début de nouvelle conversation
2. Uploader le vault complet en zip — quasiment toujours nécessaire
   pour ce projet vu sa nature (beaucoup de vérifications de
   cohérence sur données réelles)
3. Préciser sur quel chantier reprendre en priorité. Suggestions par
   ordre de "rapidité/impact" :
   - **Point 11** (connecter la bible au prompt_builder) : rapide,
     impact direct et immédiat sur la qualité des articles, ne dépend
     d'aucune décision en attente
   - **Point 13** (`undo_custom.py`) : isolé, utile, pas de
     dépendance
   - **Point 9** (champ localisation, sur les 119 fiches riches
     seulement) : conception quasi complète, codable rapidement, MAIS
     le sous-chantier "enrichissement organique" reste en pause
     (décision utilisateur)
   - **Point 8** (maillage récursif) : gros chantier, nécessite de
     bien re-cadrer l'ambition avec l'utilisateur avant de coder
   - **Point 12** (phase 2 narrative) : gros chantier de fond,
     au rythme de l'utilisateur, pas de blocage technique
4. Rappeler que tout script touchant l'API doit être testé d'abord en
   `--dry-run` par l'utilisateur avant tout lancement réel — plusieurs
   bugs n'apparaissent qu'au moment d'un vrai appel API (raisonnement
   visible du modèle, troncature, format JSON inattendu).
