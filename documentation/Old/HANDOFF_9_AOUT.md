# HANDOFF — session du 9 août 2026 (à uploader dans le nouveau chat)

*Session très dense, quatre grands chantiers enchaînés : (1) factorisation
du code dupliqué entre `generate_instances.py` et
`create_entities_and_instances.py` ; (2) fusion complète `etat_temporel`+
`age_historique` → `trajectoire`+`est_clandestin` (chantier découlant
d'une incohérence trouvée le 8 août) ; (3) consolidation de tout
l'historique du backlog (1er→9 août) en un document maître unique,
dédupliqué ; (4) chantier `annee_fin`, puis un détour productif sur
`metadata["longueur"]` qui a débouché sur un vrai bug de production
trouvé et corrigé. Session directement enchaînée sur `HANDOFF_8_AOUT.md`.*

---

## 1. Factorisation — `instance_generation_common.py`

**Point de départ** : avant de coder le chantier `trajectoire` (prévisible
comme premier chantier de la journée), constat que `generate_instances.py`
et `create_entities_and_instances.py` contiennent ~20 fonctions dupliquées
pour la génération d'une instance (prompt, appel LLM, validation, écriture
fichier) — toute modification du schéma devrait être répercutée
manuellement dans les deux fichiers, avec risque de divergence.

**Détour important sur le statut de `generate_instances.py`** : en cours
de factorisation, hypothèse initiale que le script était "legacy"
(alignée sur le manuel existant) — une modification du 8 août
(`--ancrage-temporel`) a été jugée à tort comme une erreur à ne pas
reproduire. **Corrigé après vérification du GUI** : David a signalé voir
une entrée "Générer les instances manquantes" dans le sidebar —
vérification dans `scripts_config.json` (fourni en session) confirme une
entrée dédiée, décrite explicitement comme distincte de
`create_entities_and_instances.py` ("ne crée AUCUNE nouvelle entité, ne
fait que peupler les scénarios manquants pour des entités existantes").
**`generate_instances.py` est donc actif, pas legacy** — la modification
du 8 août était légitime. Le manuel (`USER_MANUAL_COMPLET.md` §6, entrée
`generate_instances.py`) contenait cette affirmation erronée depuis une
session antérieure — corrigée cette session (voir §9 ci-dessous).

**Module créé** : `instance_generation_common.py`. Fonctions factorisées :
`parse_md`, `_read_registre_text`, `_est_ligne_separateur`,
`_parse_registre_table`, `load_etat_monde_reel`,
`load_scenario_timeline_summary`, `load_scenario_context`,
`load_variables_states`, `instance_exists`, `load_instances_in_scenario`,
`get_client`, `call_claude_json`, `build_instance_prompt`,
`_normalize_for_matching`, `detect_registre_leakage`, `validate_instance`,
`clean_relations`, `write_instance_file`, `process_entity_scenario`.

**Trois bugs de divergence réels trouvés et corrigés au passage** (les
deux fichiers avaient dérivé l'un de l'autre sans que personne ne s'en
aperçoive) :
1. `call_claude_json()` — le correctif du 11 juillet (extraction JSON de
   secours, détection de troncature, fix du NameError `resp`) n'existait
   que côté `create_entities_and_instances.py`, jamais porté vers
   `generate_instances.py`.
2. `validate_instance()` — le contrôle de plage [0-5] sur
   `impact_local`/`impact_systemique_global` manquait côté
   `generate_instances.py`.
3. `MAX_TOKENS` — `generate_instances.py` resté à 2000 (jugé insuffisant
   par un commentaire historique dans l'autre fichier), déjà relevé à
   4000 côté `create_entities_and_instances.py`. Unifié à 4000
   (`INSTANCE_MAX_TOKENS`).

**Résultat** : `generate_instances.py` 1012→178 lignes,
`create_entities_and_instances.py` 2032→1252 lignes.

**Décision explicite avec David** : factoriser AVANT de coder
`trajectoire`, plutôt que modifier les deux fichiers séparément puis
factoriser après — pour ne pas écrire deux fois la même logique modifiée.

### Quatre erreurs de transcription trouvées et corrigées avant livraison

En construisant le module, plusieurs fonctions ont été **réécrites de
mémoire au lieu d'être recopiées depuis le code source réel** — repasse
systématique (diff automatisé de chaque fonction du module contre le
fichier source d'origine) a détecté :
1. `parse_md()` — version fabriquée sans l'étape de dépouillement des
   wikilinks `[[...]]` avant parsing YAML (aurait cassé le parsing de
   tout champ contenant des wikilinks, ex. `alliances`/`oppositions`).
2. `_est_ligne_separateur()` — algorithme complètement différent de
   l'original (regex par cellule au lieu du test `all(c in "-: \t" for
   c in interieur)`).
3. `_parse_registre_table()` — logique de détection de table
   entièrement différente (filtrage par première colonne au lieu du
   flag `table_started` déclenché par la ligne séparatrice).
4. `load_variables_states()` — retournait le champ `level` (numérique)
   au lieu de `state_logic` (texte), le champ réellement attendu par le
   reste du pipeline.

Toutes corrigées avec le corps exact du code source original avant
livraison — aucune n'a atteint le vault.

### Une régression fonctionnelle trouvée et corrigée après un signalement de David

`zone_hint` transformé en paramètre explicite de `process_entity_
scenario()`, jamais alimenté par les appelants — dans le code original,
il était lu en interne via `entity_fm.get("zone_hint")`. Aurait cassé
silencieusement la prise en compte du `zone_hint` en mode custom.
Corrigé : paramètre retiré, lecture interne restaurée. Vérifié par test
réel en mode custom (`create_entities_and_instances.py`, idée avec
`zone_hint: "Amazonie"`) — confirmé propagé correctement dans les 6
instances générées (noms, localisations, alliances tous ancrés en
Amazonie).

**Testé** : dry-run CLI (backfill via `generate_instances.py` sur
`assemblee_territoires`, création custom avec `zone_hint` via
`create_entities_and_instances.py`), run réel via GUI (0 erreur
`validate.py`), nettoyage de l'entité de test via `undo_custom.py`.

**Correctif cosmétique additionnel** : format d'indentation des logs
console (`log_prefix`) réaligné pour matcher exactement le comportement
d'origine de chaque script (`generate_instances.py` : `"  → {slug} ×
{scenario}"` ; `create_entities_and_instances.py` : `"    → {scenario}"`,
4 espaces).

---

## 2. Chantier `trajectoire` — fusion etat_temporel + age_historique

**Point de départ** : incohérence trouvée sur `zones_extractivistes_
corridors_eco_communalism` (`age_historique: ascendant` +
`etat_temporel: transformé`) lors d'une session antérieure — les deux
champs se chevauchent conceptuellement sans garantie mécanique de
cohérence mutuelle.

**Décision (Option B)** : fusion en un seul axe narratif continu de 11
valeurs : `émergent → marginal → ascendant → dominant → mature →
déclinant → résiduel → transformé → disparu → historique → mythifié`.
`clandestin` sort de l'axe, devient `est_clandestin` (booléen
indépendant) — permet désormais des combinaisons impossibles avant
(ex. `[DOMINANT] [CLANDESTIN]`).

### Décisions actées une par une avec David (avant codage)

1. **`marginal`** entre `émergent` et `ascendant` (pas une branche
   parallèle — un seul axe, `marginal` comme position de repos possible,
   pas une étape obligatoire).
2. **`actif`** — supprimé pour toute nouvelle création, conservé
   uniquement comme mapping migratoire (→ `mature` + marqueur). Cas
   `clandestin` traité pareil (`mature` + marqueur + `est_clandestin:
   true`), plutôt que demander à David de positionner les 23 fiches une
   par une.
3. **`historique`/`mythifié`** — gardés distincts (0 fiche concernée,
   aucun coût de migration à garder l'option ouverte).
4. **`generation`** — schéma inchangé, non concerné par la fusion.
5. **Hard constraint (`Option 1`)** — `est_clandestin` ajouté comme champ
   optionnel (`None`/`True`/`False`) au mécanisme `hard_constraint`,
   même si jamais exercé en pratique (0 fiche avec `scenario_ref`/
   `etat_ref` renseigné sur le vault au moment de la décision).
6. **`COHERENCE_MAP`** — renommée `TRAJECTOIRE_COHERENCE_MAP`, version
   resserrée décidée (pas de joker large en remplacement de l'ancien
   `actif`).
7. **Rollback** — suppression immédiate d'`etat_temporel`/`age_
   historique` du frontmatter après migration (vault versionné Git, pas
   besoin de cohabitation temporaire).

### Fichiers modifiés

`validate.py` (`VALID_TRAJECTOIRE`, `TRAJECTOIRE_INACTIVES` — unifie
`INACTIVE_ETATS`/`ETAT_INACTIFS`/le hardcode `"disparu"` du check C4 en
une seule constante, **corrige au passage un bug réel** : C4 ne
détectait avant que les fiches `disparu` sans `annee_fin`, pas
`transformé`/`historique`/`mythifié` comme C3 le fait déjà) ;
`loader.py` (schéma) ; `prompt_builder.py` (badge `[TRAJECTOIRE]
[CLANDESTIN]` combinable) ; `officialize_alliances.py` (template) ;
`enrich_minimal.py` (lecture contextuelle, 2 constantes mortes
retirées) ; `instance_generation_common.py` (cœur — `build_instance_
prompt`, `validate_instance`, `write_instance_file`, `hard_constraint`).

### `TRAJECTOIRE_COHERENCE_MAP` — deux erreurs de calibrage corrigées en session

1. **Première version** : joker `actif` retiré sans compensation → 102
   avertissements sur `breakdown` seul, tous des faux positifs
   (`émergent`/`ascendant`/`dominant` signalés incohérents avec
   `chaotique`, alors qu'un monde chaotique génère justement des
   entités émergentes/montantes).
2. **Deuxième version**, calibrée sur les données réelles du vault
   entier (710 fiches migrées) : 528 avertissements — cause trouvée,
   `émergent` absent de TOUTES les lignes de la map (oubli, pas un
   calibrage fin à refaire).
3. **Décision finale avec David** : plutôt que de continuer à ajuster à
   la marge, **simplifié** — ne garde le check que sur `resilient`/
   `collapsing` (les deux seuls `state_of_system` où il discrimine
   vraiment, 0 avertissement observé avec les valeurs déjà en place) ;
   `chaotique`/`fragile`/`instable`/`stable` retirés de la map (absence
   de clé → set vide → check silencieux, comportement voulu).

### `migrate_trajectoire.py` (nouveau script)

Mécanique, **aucun appel LLM** (contrairement au script modèle `fix_
annee_debut_placeholder.py`) — règles de migration entièrement
déterministes. Testé sur 5 cas synthétiques couvrant toute la table de
décision, idempotence confirmée (`0 fiche restante` au second passage),
YAML re-parsable vérifié après patch. **Exécuté sur le vault réel : 710
fiches migrées, 0 erreur `validate.py`.**

### GUI — menu `État`/`Clandestin` refondu

`scripts_config.json`, entrée `create_entities` (mode custom) : champ
`etat` passé de 6 valeurs (`etat_temporel`) à 11 (`trajectoire`),
renommé "Trajectoire (contrainte dure)". Nouveau champ `est_clandestin`
inséré juste après (select tri-état `oui`/`non`/vide — un checkbox
classique ne peut pas exprimer "indifférent"). Câblage Python complet :
`_parse_optional_bool()` (nouveau helper), `write_entity_file()`
(nouveau paramètre `est_clandestin_ref`, écrit uniquement si une
contrainte a été explicitement posée), `process_custom_idea()` (lit,
propage, retourne). Testé fonctionnellement (5 cas), diff structurel
confirmant qu'aucune des 26 autres entrées du fichier n'a été altérée.

### `audit_etat_temporel_fin.py` — adapté

Lisait `etat_temporel`/`age_historique`, corrigé pour lire `trajectoire`
+ `est_clandestin`, réutilise `TRAJECTOIRE_INACTIVES` importée de
`validate.py` (une seule source de vérité — pas une troisième liste
dupliquée comme celle qui existait avant la fusion). Label/description
GUI corrigés au passage (mentionnaient encore l'ancien schéma, disaient
le chantier `annee_fin` "pas encore construit" — les deux corrigés,
`annee_fin` étant clos dans la même session, voir §4).

**Vérification finale** : `audit_etat_temporel_fin.py` → 30/30 fiches
cohérentes (0% d'incohérence). `validate.py --report` → 0 erreur, 7
avertissements (résidu `test_durcissement_policy_reform`, sans rapport
— voir §5).

---

## 3. Consolidation du backlog — `BACKLOG_MASTER_9_AOUT.md`

David a signalé que le backlog fragmenté (un fichier par jour depuis le
1er août, beaucoup de doublons, des points ouverts depuis 6+ sessions
sans jamais être tranchés) n'était plus exploitable. Demande explicite :
liste claire, chantiers nommés, dédupliquée, propre pour la suite.

**Construit** : `BACKLOG_MASTER_9_AOUT.md`, 4 parties (chantiers ouverts
priorisés 🔴🟡🟢⚪, points mineurs non bloquants, risque structurel,
chantiers clos — référence historique). **Établi comme référence
officielle unique** — remplace tous les `BACKLOG_CONSOLIDE_*`/`HANDOFF_*`
précédents comme source de vérité, à mettre à jour en place (pas
recréer) à chaque session future.

**Deux résolutions croisées trouvées en consolidant** :
- Le sous-point "`zones_extractivistes_...`" qui avait ouvert le
  chantier `annee_fin` est en fait déjà réglé par le chantier
  `trajectoire` du jour même.
- "`fix_alliances_oppositions.py` absent du GUI" (ouvert le 5 août) a
  été silencieusement résolu le 7 août (intégration GUI), jamais
  formellement refermé dans aucun backlog avant celui-ci.

**Deux fausses alertes trouvées en attaquant les points un par un** :
- **`type_relation_dominante`** — listé "décision à prendre avec David"
  depuis le 3 août, 6+ sessions. En réalité déjà décidé et **implémenté
  le 7 août** (`prompt_builder.py`, `build_entities_context()`, ligne
  dédiée `*Relation dominante* : X (période)`), jamais retiré du
  backlog dans les sessions suivantes — pur problème de suivi
  documentaire, pas un oubli de conception. Garde-fou anti-fabrication
  confirmé suffisant (consigne générale "ne les contredis pas" du bloc
  entités, pas de mécanisme dédié nécessaire — décision de David).
- **`metadata["longueur"]` réutilisé en aval ?** — voir §5, résolu par
  investigation directe du code plutôt que deviné.

---

## 4. Chantier `annee_fin`

**28 fiches** à `trajectoire` terminale (`transformé`/`disparu`) sans
`annee_fin`, taux d'incohérence 93,3% confirmé par `audit_etat_
temporel_fin.py` (post-migration `trajectoire` — le chiffre historique
de 28 tient toujours à l'identique).

**`fix_annee_fin_manquant.py`** (nouveau script, modèle repris de `fix_
annee_debut_placeholder.py`) — différence structurelle : **pas
d'ancrage sur `etat_du_monde_reel.md`**, une date de fin fictive n'a pas
besoin de continuité avec le monde réel d'aujourd'hui, seulement avec
`registre_evenements.md`. Règle de priorité actée avec David : jalon du
registre en premier si identifiable, sinon estimation depuis le
contexte narratif déjà écrit.

**Déploiement** : 27/28 corrigées directement sur les 6 scénarios. 1 cas
résistant (`consortium_helios_new_sustainability`, LLM proposant
systématiquement `2101` au-delà de l'horizon 2098, sur deux tentatives
puis un run entier après renforcement du prompt) — résolu en deux
temps : (1) consigne de plafonnement explicite ajoutée au prompt
("choisis 2098 lui-même plutôt que de dépasser"), qui a fini par
suffire au run suivant ; (2) un **filet de sécurité automatique** ajouté
au script en parallèle (plafonnement à 2098 si dépassement persistant
après épuisement des tentatives — jamais déclenché au final sur ce cas,
mais disponible pour un futur cas similaire). Le filet ne s'applique
jamais si le problème est `annee_fin ≤ annee_debut` ou une valeur non
numérique (restent de vrais échecs à examiner).

**Concentration sur quelques années vérifiée légitime** (2061, 2057,
2053 sur `breakdown`, coïncidant avec la concentration déjà connue sur
2041 pour `annee_debut`) — examen du détail des justifications LLM
confirme un raisonnement narratif distinct et contextualisé à chaque
fiche, pas une convergence artificielle vers une réponse par défaut.

**Vérification finale** : `audit_etat_temporel_fin.py` → 30/30
cohérentes (0%). `validate.py` → 0 erreur.

**Trouvaille en marge, non résolue** : doublon potentiel d'entité
repéré sur `breakdown` — `arctic_passage_authority` (anglais) et
`autorite_passage_arctique` (français), deux fiches distinctes dans
`entites/` dont le raisonnement narratif (justifications `annee_fin`)
semble quasi identique. Ajouté au backlog maître comme chantier à part,
non traité cette session (contenu des deux fiches jamais comparé en
détail).

---

## 5. Détour `metadata["longueur"]` — de la métadonnée cosmétique au vrai bug

**Point de départ** : question backlog ouverte depuis le 3 août — le
champ `metadata["longueur"]` (bug corrigé le 3 août, override de config
parfois ignoré) est-il réutilisé en aval, au-delà de l'affichage
`--dry-run` ?

**Investigation directe du code** (`api.py`) : confirmé — écrit de façon
permanente dans le frontmatter de chaque article (`api.py` ET `generate_
manual.py`, à des fins de traçabilité), mais **jamais relu par aucun
script** (`trace_injection.py`, seul autre lecteur du frontmatter
d'articles, extrait `scenario`/`date_publication`/`titre`, jamais
`longueur`). Impact confirmé purement cosmétique.

**Décision : pas de correction rétroactive.** Même en sachant que le
champ stocke une plage textuelle déjà résolue (pas un nom de catégorie),
une reconstruction depuis le seul comptage de mots resterait ambiguë
(plusieurs catégories `FORMAT_LONGUEUR` partagent la même plage — ex.
`chronique`/`narratif` toutes deux "400-700 mots"). Rapport
effort/bénéfice jugé mauvais face à un impact nul en aval.

### `audit_longueur_articles.py` — nouvel outil, 3 itérations en session

Demande de David : pouvoir au moins **mesurer** sans corriger.

- **v1** : cherchait `longueur` comme un nom de catégorie — faux,
  c'est une plage textuelle déjà résolue (`metadata["longueur"]` =
  `FORMAT_LONGUEUR[config_lon]`, la chaîne elle-même, pas la clé).
  Résultat : 100% "étiquette inconnue", pas une vraie incohérence.
- **v2** : corrigé pour parser la plage textuelle directement (regex).
  Fonctionnel — 64,5% d'incohérence — mais mélangeait deux causes
  différentes en un seul chiffre.
- **v3** (suite à une remarque de David : *"je pensais que la catégorie
  de l'article était intégrée et qu'il fallait juste récupérer ce
  label"*) — exploite le champ `format` du frontmatter, qui **est**
  déjà le nom de catégorie (`meta["format"] = thematique.get("format_
  dominant")`), toujours dérivé de la thématique, jamais de l'override.
  Distingue **Cas A** (`format` et `longueur` pointent vers la même
  plage — pas d'override, le vrai signal) de **Cas B** (divergence —
  override probable, informatif seulement).

**Résultat final, fiable** : Cas A = **70,4% d'incohérence (19/27
analysables)**, sans biais directionnel (certains articles dépassent
largement la plage demandée, d'autres sont largement en dessous).

### Bug de production trouvé et corrigé en marge de cet audit

Cas B a d'abord affiché 0, puis (après correction d'un bug d'accent
dans le script d'audit lui-même — `FORMAT_LONGUEUR_BORNES` local ne
couvrait pas `"brève"` accentué) est remonté à **4 articles**, tous
`format: brève`. En creusant : **`FORMAT_LONGUEUR` dans `prompt_
builder.py` (le vrai fichier de production, pas juste mon script
d'audit) ne couvrait que les orthographes sans accent**
(`breve`/`editorial`/`reflexif`), alors que `VALID_FORMATS`
(`validate.py`) accepte explicitement les deux orthographes pour
chacune. Toute thématique avec `format_dominant: brève` (accentué,
probablement la plus utilisée) retombait silencieusement sur le filet
de secours générique `"300 à 500 mots"` au lieu de sa vraie plage
`"200 à 400 mots"`.

**Corrigé** : les 3 variantes accentuées (`brève`, `éditorial`,
`réflexif`) ajoutées à `FORMAT_LONGUEUR`. Un seul dict module-level,
donc correctif appliqué automatiquement aux deux points d'usage
(`build_journalistic_brief()`, `build_prompt()`). Vérifié
fonctionnellement (les 3 nouvelles clés mappent bien vers la même plage
que leur équivalent sans accent). Pas de correction rétroactive des
articles déjà publiés avec ce défaut (même raisonnement que le point
principal — cosmétique, non consommé en aval).

**Nouveau chantier ouvert au backlog** (🔴, priorité) : le 70,4%
restant n'est PAS expliqué par ce bug — c'est un vrai sujet de qualité
de génération (le LLM ne respecte pas fiablement la consigne de
longueur), distinct et non encore investigué.

---

## 6. GUI — `audit_longueur_articles` ajouté

Sur suggestion de David. `scripts_config.json`, section `validation`,
même famille que les 3 audits existants (`--dossier` optionnel comme
seule option). Description périmée d'`audit_etat_temporel_fin` corrigée
au passage (voir §2). Diff structurel confirmant qu'aucune autre entrée
n'a été altérée (27→28 entrées, exactement +1).

---

## 7. Fichiers livrés cette session

**Nouveaux scripts** : `instance_generation_common.py`, `migrate_
trajectoire.py`, `fix_annee_fin_manquant.py`, `audit_longueur_
articles.py`.

**Scripts modifiés** : `generate_instances.py`, `create_entities_and_
instances.py`, `validate.py`, `loader.py`, `prompt_builder.py`,
`officialize_alliances.py`, `enrich_minimal.py`, `audit_etat_temporel_
fin.py`, `scripts_config.json`.

**Documentation** : `BACKLOG_MASTER_9_AOUT.md` (nouveau, référence
officielle), `USER_MANUAL_COMPLET.md` (édité — voir §9), ce handoff.

Tous les scripts modifiés/créés testés (syntaxe `ast.parse`, tests
fonctionnels sur données synthétiques, et pour la plupart en conditions
réelles sur le vault via David).

---

## 8. Bilan des vérifications finales

| Vérification | Résultat |
|---|---|
| `validate.py --report` (post-migration `trajectoire`) | 0 erreur, 7 avertissements (résidu `test_durcissement_policy_reform`) |
| `audit_etat_temporel_fin.py` (post-`annee_fin`) | 30/30 fiches cohérentes, 0% |
| Diff structurel `scripts_config.json` (×2 sessions de modif) | Aucune entrée hors périmètre altérée |
| `FORMAT_LONGUEUR` accents | 3 variantes testées, mappent correctement |

---

## 9. Documentation mise à jour cette session

- **`BACKLOG_MASTER_9_AOUT.md`** — établi comme référence officielle,
  mis à jour en continu tout au long de la session (chantiers fermés
  déplacés en Partie 4 au fil de l'eau, nouveaux chantiers ajoutés en
  Partie 1 à mesure des découvertes).
- **`USER_MANUAL_COMPLET.md`** — édité (pas réécrit) :
  - Entrée `generate_instances.py` (§6) corrigée : actif, pas legacy.
  - Description de `create_entities_and_instances.py` (§3) corrigée —
    contenait la même affirmation erronée sur `generate_instances.py`.
  - Champs du mode custom (§3) mis à jour : `etat` → 11 valeurs
    `trajectoire`, nouveau `est_clandestin`.
  - **Nouvelle section §3bis** — chantier `trajectoire` complet.
  - **Nouvelle entrée §1** — `instance_generation_common.py`.
  - **Nouvelles entrées §6** — `fix_annee_debut_placeholder.py`
    (gap comblé — existait déjà en usage réel, jamais documenté),
    `migrate_trajectoire.py`, `fix_annee_fin_manquant.py`.
  - **Nouvelle sous-section §5** — chantier `annee_fin` +
    `audit_longueur_articles.py` + bug d'accent `FORMAT_LONGUEUR`.
  - **Addendum §7** — 3 changements `scripts_config.json` de la
    session (menu `create_entities`, `audit_etat_temporel_fin`
    corrigé, `audit_longueur_articles` ajouté).

---

## 10. Point de reprise suggéré pour la prochaine session

Le backlog maître (`BACKLOG_MASTER_9_AOUT.md`, Partie 1) est la
référence — dans l'ordre de priorité actuel :

1. **🔴 Dérive du LLM sur la longueur réelle des articles** (nouveau,
   70,4% d'incohérence Cas A) — sujet de qualité de génération à
   investiguer, distinct du bug d'accent déjà corrigé.
2. **🟡 Test navigateur des entrées GUI modifiées** — périmètre large,
   jamais fait, suggestion d'une session dédiée "clic à travers tout le
   GUI" plutôt que du cas par cas.
3. **🟡 Même diagnostic `annee_debut`/`ancrage_reel` sur les
   événements** — jamais exploré, le chantier `annee_debut` n'a porté
   que sur les instances.
4. Reste du backlog : voir `BACKLOG_MASTER_9_AOUT.md` Partie 1, points
   4 à 10 — doublon d'entité `arctic_passage_authority`/`autorite_
   passage_arctique` (§4 ci-dessus) à diagnostiquer, nettoyage `test_
   durcissement_policy_reform`, 4 reliquats du 7 août, renommage YAML
   génériques.

**Discipline à maintenir** : `BACKLOG_MASTER_9_AOUT.md` doit être **mis
à jour en place**, jamais recréé sous un nouveau nom daté — c'est
précisément le problème de fragmentation que cette session a corrigé.
