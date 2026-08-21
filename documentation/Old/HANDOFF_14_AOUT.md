# HANDOFF — session du 14 août 2026 (à uploader dans le nouveau chat)

*Session en continuité directe de `HANDOFF_13_AOUT.md`. Structure
inhabituelle : la session a démarré par une recherche exhaustive dans
l'archive complète des anciens backlogs/handoffs (juin-août) pour
retrouver des points tombés du radar, puis a enchaîné sur le
traitement systématique de tout ce qui a été retrouvé, complété par
plusieurs chantiers de la Partie 1/Partie 2 du backlog du 9 août.
Session très dense : 9 chantiers clos, 12 fichiers livrés, 2 nouveaux
scripts d'audit/migration réutilisables, 1 nouveau chantier substantiel
identifié pour la suite.*

---

## 0. Méthode de la session — recherche exhaustive dans l'archive

À la demande de David, recherche systématique dans une archive de ~40
fichiers (12 backlogs consolidés + handoffs du 20 juin au 12 août) pour
identifier tout sujet mentionné une fois puis disparu sans clôture
formelle. Quatre trouvailles confirmées :

- **P16** — documenter `zone_hint` dans `QUEUE_TEMPLATE` (décidé le 11
  juillet, jamais fait) → **clos cette session**, voir §2.
- **P17** — retester la fiabilité `mistral-small` sur choix contraint
  (11 juillet) → toujours ouvert, remis en tête de backlog, David a
  choisi de le garder pour plus tard sans le traiter aujourd'hui.
- **Bug #27** — incohérence de plausibilité logistique inter-zones (un
  personnage du Pacte Amazônia Viva arrivant par pirogue depuis
  Kisangani sans mention de traversée intercontinentale, 11 juillet) →
  toujours ouvert. David veut faire une **analyse d'articles** plus
  tard pour vérifier si le symptôme s'est reproduit, plutôt que de
  coder un correctif préventif sans données.
- **Nettoyage des fichiers de rotation** (`state/instance_usage.json`,
  `trajectory_usage.json`, `event_relevance_usage.json`, noté le 8
  août) → **requalifié**, pas fermé ni traité : ce n'est pas un
  nettoyage de routine mais un outil de **reset volontaire de la
  mémoire de rotation**, à activer seulement le jour où David veut
  repartir sur une mémoire vierge (nouveau cycle éditorial, etc.).
  Commande prête si besoin un jour :
  ```bash
  rm state/instance_usage.json state/trajectory_usage.json state/event_relevance_usage.json
  ```
  (régénérés automatiquement au run suivant).

**Point de méthode confirmé plusieurs fois cette session** : la doc
(backlog et/ou manuel) est en retard sur le code réel à plusieurs
reprises — voir §3 (point 2 du backlog déjà appliqué), §5.2
(`instance_template.md` déjà déplacé), §5.3 (limite panneau Revue déjà
corrigée le 12 août). Aucun de ces trois n'a nécessité de nouveau
code — juste une vérification contre le code/l'état réel avant de
lancer un chantier qui n'en était plus un.

---

## 1. Point de reprise du 13 août — tranché

Le point 2 du backlog du 13 août (« Documentation à corriger — chantier
`trajectoire` ») a été vérifié : déjà appliqué dans
`USER_MANUAL_COMPLET.md` (§1 et §6, tous deux datés "corrigé le 9 août
2026"). **Fermé sans travail supplémentaire.**

---

## 2. P16 — `zone_hint` documenté dans `QUEUE_TEMPLATE` — clos

Diagnostic : `create_entities_and_instances.py` documentait déjà
`zone_hint` correctement (lignes 607-611 de son `QUEUE_TEMPLATE`) —
seul `inject_custom_events.py` avait l'oubli. `inject_custom_signals.py`
confirmé hors scope (pas de champ `zone_hint` dans son pipeline).

**Corrigé** : ajout de l'entrée `zone_hint` dans le bloc CHAMPS du
`QUEUE_TEMPLATE` d'`inject_custom_events.py` (après
`acteurs_hint_count`, avant `source`), plus mise à jour de l'exemple
JSON — même formulation que la version déjà présente côté
`create_entities_and_instances.py`.

**Risque d'écrasement identifié et confirmé avant de coder** :
`save_queue_with_template()` réécrit tout `queue.yaml` depuis la
constante Python `QUEUE_TEMPLATE` à chaque vidage — éditer le YAML
directement aurait été écrasé au prochain run. D'où l'édition du `.py`,
pas du `.yaml`.

---

## 3. Backlog #3 — doublon d'entité `arctic_passage_authority` /
`autorite_passage_arctique` — clos

**Diagnostic** : vrai doublon confirmé, généré automatiquement par
`extract_phantom_slugs.py` — `entites_custom/processed.yaml` contient 3
entrées avec des champs `_slug_fantome_original`/`_slug_corrige`
pointant vers `autorite_passage_arctique`, confirmant qu'un slug
fantôme (probablement une référence de zone, `geographie/breakdown.md`
ligne 2278) a été détecté sans entité correspondante et a généré une
entité fantôme indépendante, sans savoir qu'`arctic_passage_authority`
existait déjà pour la même institution (le récit des deux instances
`breakdown` partage le même jalon de registre et la même trajectoire de
fragmentation en factions, déjà noté le 9 août).

**Point hors scope identifié et volontairement non touché** : les
champs `zone: autorite_passage_arctique` (dans les deux instances
`breakdown` et dans `event_instances/incident_passage_arctique_
breakdown.md`) et l'entrée `geographie/breakdown.md:2278` sont des
références à une **zone géographique**, pas à l'entité — chantier
séparé, sans lien avec le doublon.

**Migration exécutée** (script `fix_arctic_passage_duplicate.py`,
livré cette session, réutilisable) :
- Dry-run puis exécution réelle : **17 fiches migrées, 34 références**
  (liste YAML + wikilink alliance/opposition) réécrites de
  `autorite_passage_arctique_breakdown` vers
  `arctic_passage_authority_breakdown`.
- Puis `undo_custom.py --slug autorite_passage_arctique --type entite
  --generalisation yes --execute` : archétype fantôme + son instance
  `breakdown` supprimés, `_entities_list.json` nettoyé,
  `last_validated.json` réinitialisé.
- **`validate.py --verbose` final : 0 erreur, 0 wikilink cassé.**

---

## 4. Backlog #4 — wikilinks cassés `test_durcissement_policy_reform`
— clos

7 fiches `instances/*.md` de `policy_reform` référençaient encore
`[[test_durcissement_policy_reform]]` (une fiche supprimée, résidu du 8
août) — une seule ligne bullet par fiche (`- [[test_durcissement_
policy_reform]]`), format identique partout, section `## Relations`.

**Corrigé** (script `fix_test_durcissement_wikilinks.py`, livré cette
session, réutilisable pour tout futur cas de wikilink mort similaire) :
7 lignes retirées sur 7 fiches, dry-run puis exécution confirmés.
**`validate.py --verbose` final après ce chantier : 0 erreur, 0
avertissement** (y compris les 3 avertissements narratifs vus
précédemment — non reproduits car le scan narratif a été sauté, rien
n'ayant changé côté `event_instances/` entre les deux runs).

---

## 5. Backlog #5 — quatre reliquats du 7 août — clos dans son ensemble

### 5.1 — Redéploiement des correctifs du 2 août — confirmé de facto

`routes_dashboard.py`, le fix du panneau Revue (`app.py`/`enrich_
minimal.py`) et `geographie/policy_reform.md` (Groenland) n'avaient
jamais de confirmation formelle de déploiement post-livraison. Vérifié
via le manuel : Groenland confirmé corrigé et rescanné le jour même (2
août) ; le panneau Revue a été utilisé en conditions réelles avec un
second bug trouvé et corrigé le 12 août (« signalé par David ») — preuve
d'usage réel post-livraison. **Fermé sans action, confirmation
rétroactive suffisante.**

### 5.2 — `instance_template.md` — clos, confirmé déplacé

David confirme : déjà déplacé vers un dossier `/templates`, hors de
`instances/`. Vérifié qu'aucun autre script du pipeline n'a de
dépendance documentée sur le fait que ce fichier vive dans `instances/`
— les filtres explicites déjà en place (`officialize_alliances.py`,
`_stats_instances()`, `_stats_enrichissement()`) deviennent simplement
inertes, pas cassés. Les scripts jamais audités individuellement
(`create_entities_and_instances.py`, `enrich_minimal.py`,
`extract_phantom_slugs.py`, `fix_impact_scale.py`) n'ont plus besoin
d'audit : l'angle mort qu'ils pouvaient avoir n'existe plus
structurellement. **Rien à corriger côté code.**

### 5.3 — Limite panneau Revue (slug générique entités/signaux) — clos,
déjà résolu le 12 août

Le manuel décrivait encore le bug du 2 août (« limite connue : slug
générique `(entité)`/`(signal)` »). Vérifié dans le code réel
d'`app.py` (`_read_needs_review_yaml()`) : un correctif du **12 août**
(non documenté dans le manuel) ajoute trois branches reconnaissant les
clés `nom:`, `scenario_ref:`, `reason:` imbriquées sous `idea:` — le
parseur ignorant de toute façon l'indentation, ces clés sont lues au
même niveau que les autres sans problème structurel. **Test tracé à la
main sur un vrai extrait de `needs_review.yaml`** (« Les Veilleurs des
Nappes Phréatiques ») : le nom réel, le scénario et la raison de rejet
sont tous correctement extraits, plus de placeholder générique. Manuel
à corriger sur ce point (fait, voir §8 ci-dessous).

### 5.4 — Discipline de rédaction du backlog — non-actionnable, vigilance
continue

Pas un chantier de code — juste le rappel méthodologique déjà noté par
le passé. Ironie relevée : c'est exactement ce pattern (points
documentés ailleurs mais absents de la section « reste à faire ») qui a
causé la perte de P16/P17/Bug#27/nettoyage rotation, retrouvés en début
de session (voir §0). Aucune action corrective codable — juste
continuer à vérifier soigneusement à chaque mise à jour de backlog.

---

## 6. Backlog #6 — renommage YAML génériques par dossier — toujours
reporté

Discussion tenue : coût de migration (constantes `QUEUE_PATH` dans 3
scripts, entrées `scripts_config.json`, doc) vs bénéfice de clarté
(aucune collision technique, juste une ambiguïté visuelle). **David a
choisi de reporter encore une fois, sans trancher.** Noté explicitement
cette fois plutôt que de disparaître silencieusement.

---

## 7. Backlog #7 — fichiers parasites `generator/` (incident du 5 août)
— clos, confirmé propre

David a relancé la commande de vérification (`find . -maxdepth 1 -type
f -empty ! -name "*.*" -print`) : **aucun fichier trouvé**. Déjà
nettoyé entre-temps, ou jamais aussi problématique que redouté.
**Fermé, rien à faire.**

---

## 8. Chantier "encodage portugais cassé dans certains slugs" — clos

**Retrouvé lors de la recherche exhaustive du §0** (backlog Partie 2,
noté le 8 août, jamais traité).

### Diagnostic — cause racine identifiée avec précision

`slugify()` utilisait une table de remplacement d'accents **français
uniquement** (`é/è/ê/ë/à/â/ä/ù/û/ü/î/ï/ô/ö/ç`) au lieu d'une
normalisation Unicode générique. Tout caractère accentué absent de
cette table (portugais `ã/õ/á/í/ó/ú`, espagnol `ñ`, etc.) tombait dans
le `re.sub` générique suivant, qui le remplaçait par `_` au lieu de le
translittérer. Vérifié précisément sur le cas connu : « Rede Paulista
de Distribuição Algorítmica » → `ã` et `í` absents de la table →
`rede_paulista_de_distribuic_o_algor_tmica` (slug cassé observé le 8
août).

**Trois fichiers touchés, identiques mot pour mot, tous corrigés** :
- `create_entities_and_instances.py` (actif)
- `create_entity.py` (legacy/archivé, mais corrigé par cohérence si
  jamais relancé en CLI)
- `officialize_alliances.py` (actif)

**Correctif** : remplacement de la table d'accents par une
normalisation Unicode générique (NFD + suppression des marques
diacritiques), même principe que la fonction `_fold()` déjà existante
dans `gui/app.py`. Testé sur portugais, français (non-régression),
espagnol, allemand — tous corrects.

**Aucune autre copie du bug trouvée** ailleurs dans les 63 scripts du
dossier `generator/` (recherche du pattern exact `for fr, en in [`).

### Audit du vault — 2 cas confirmés sur 18 candidats

Script `audit_broken_slugs.py` livré (réutilisable, lecture seule) :
compare le slug enregistré de chaque entité au slug que produirait la
fonction corrigée à partir du `name`/`nom`.

**Résultat** : 590 entités auditées, 18 candidats bruts.
- **2 vrais cas** (signature caractéristique : une lettre isolée
  manquante en plein mot) : `rede_paulista_de_distribuic_o_algor_tmica`
  et `frente_sert_o_livre` (« Frente **Sertão** Livre », le `ã` perdu).
- **15 faux positifs** : raccourcissement volontaire de slug (mots de
  liaison omis : "de", "des", "du", "pour la", élisions "d'Israël" →
  "israel") — pas le bug, choix éditorial légitime au moment de la
  création.
- **1 artefact du script** : `entite_template.md` (le gabarit
  lui-même, `nom: <nom_entite>` littéral) — l'audit devrait l'exclure,
  point à corriger si le script est relancé plus tard (non corrigé
  cette session, noté pour info).

### Migration des 2 cas confirmés — exécutée

Script `rename_broken_slugs.py` livré (réutilisable pour tout futur cas
similaire) — contrairement à la fusion Arctic (§3), c'est un vrai
**renommage** (même entité, slug corrigé), pas une fusion :

- **11 fichiers renommés** : 2 archétypes + 6 instances
  (`rede_paulista...`, tous scénarios sauf eco_communalism absent) + 3
  instances (`frente_sertao_livre`, breakdown/eco_communalism/
  reference).
- **Ampleur des références externes plus grande que prévu** : 322
  références réécrites dans 141 fiches (`instances/`, `event_
  instances/`, `geographie/*.md`) — l'entité `rede_paulista` s'est
  révélée être un acteur narratif central très connecté (lié aux
  événements `emeutes_algorithme_sao_paulo_*`).
- **`documentation/` explicitement exclu** de la migration (6 fichiers,
  historique/handoffs mentionnant l'ancien slug comme preuve du bug
  découvert le 8 août — décision cohérente avec le traitement
  d'`entites_custom/processed.yaml` au §3 : jamais réécrire
  l'historique).
- `entites/_entities_list.json` mis à jour (2 entrées) par
  remplacement de texte ciblé, pas de parse/dump JSON complet, pour
  préserver le formatage.
- **`validate.py --verbose` final : 0 erreur.**

---

## 9. `acteurs_hint_count` (P15) — filtre dur enfin appliqué

**Retrouvé** lors de la revue systématique de la Partie 2 avec le code
complet disponible. Diagnostic précis : la valeur était bien calculée
et bornée (`max(1, min(4, ...))`, ligne 935-936 d'`inject_custom_
events.py`) mais **jamais transmise** à `step2_develop_instance()` ni
à `validate_instance()` — calculée puis jetée sans effet, contrairement
à `variables_hint_count` qui a une vraie troncature dure après coup.

**Corrigé** : nouvelle fonction `truncate_actors()` dans
`inject_custom_events.py`, appliquée à chaque production d'acteurs par
le LLM (essai initial **et** chaque retry) — même schéma exact que la
troncature `variables` déjà en place : les hints imposés par
l'utilisateur sont toujours préservés en premier, le reste est coupé au
plafond.

**Testé unitairement** (3 cas : troncature simple, préservation du hint
imposé même hors tête de liste, non-modification si déjà sous le
plafond) — tous corrects. **Pas encore confirmé en conditions réelles**
— David a choisi de laisser ça se valider au fil de l'eau plutôt que
de provoquer un test dédié, même logique que le point #1 du backlog
(validation retry longueur).

---

## 10. `forces_attractives`/`forces_repulsives` — escaladé en chantier
substantiel, non résolu, à reprendre en priorité

**Point de départ** : incohérence repérée en Partie 2 — le docstring de
`build_variables_context()` (`prompt_builder.py`) promet ces champs
« si disponibles », mais rien dans le code ne les lit nulle part.
Diagnostic initial (avant vérification du vault réel) : probablement
juste une promesse de docstring jamais tenue, correctif de commentaire
suffisant.

**Le vault réel a changé la donne.** David a confirmé, via un
`grep -rl "forces_attractives\|forces_repulsives" variables/`, que le
contenu existe bel et bien — **sur les 12 fiches variables, sans
exception**. Ce n'est donc pas une intention jamais concrétisée, c'est
du contenu rédigé et **silencieusement ignoré par le pipeline depuis le
début**.

**Complication trouvée en creusant le format réel** (fiche
`geopolitique_conflits.md` inspectée en détail) : ces champs ne sont
**pas** des clés YAML de frontmatter (contrairement à `simulation`,
`constrained_variables` déjà vérifiés) — ce sont des listes à puces en
prose Markdown dans le **corps** de la fiche, sous des titres `##`. Et
il y a un **doublon de contenu non résolu** :
- `## 3. Dynamique interne` → `**forces_attractives**` /
  `**forces_repulsives**` (snake_case, minuscules)
- `## 4. Structure causale` → `**Forces attractives**` / `**Forces
  répulsives**` (majuscules, accentué, orthographe différente)

Les deux listes se recoupent partiellement mais ne sont pas
identiques sur les 12 fiches (ex. section 3 de `geopolitique_conflits`
a "stabilité commerciale globale", section 4 ne l'a pas). **Confirmé
par grep : aucune des deux sections n'est parsée nulle part dans le
pipeline** (`grep -rn "Structure causale\|Dynamique interne" *.py` →
zéro résultat).

**Portée du chantier, telle qu'identifiée** :
1. **Décision de conception à prendre par David** — quelle section est
   la source de vérité (3, 4, ou fusion des deux) ? Pas une décision
   codable, nécessite de relire les 12 fiches.
2. **Nouveau parseur de corps Markdown** dans `loader.py` — différent
   des autres champs déjà câblés, qui sont de simples `fm.get(...)`
   sur le frontmatter YAML.
3. **Câblage dans `build_variables_context()`** (`prompt_builder.py`)
   pour que le résultat apparaisse enfin dans le prompt envoyé au LLM.

**David a explicitement demandé que ce soit traité comme un chantier
important pour la prochaine session, pas noyé dans les points
mineurs.** Rien codé cette session — prochaine étape : David relit les
12 fiches et tranche la question de la section source avant que du
code soit écrit.

---

## 11. Duplication `detect_registre_leakage()` — clos

**Retrouvé** en revue systématique de la Partie 2. La fonction
existait en double, avec deux fonctions dépendantes (`_read_registre_
text()`, `_normalize_for_matching()`) elles aussi dupliquées, entre
`instance_generation_common.py` (module partagé) et
`fix_annee_debut_placeholder.py` (copie indépendante).

**Vérifié avant de corriger** : les trois paires ne présentaient qu'une
divergence **cosmétique** (docstrings légèrement différents, un style
de code différent pour `_read_registre_text()` mais fonctionnellement
équivalent, un `flags=re.UNICODE` explicite mais redondant dans
`_normalize_for_matching()` côté `fix_annee_debut_placeholder.py`,
Python 3 traitant déjà `\w` en Unicode par défaut) — **aucune
divergence fonctionnelle actuelle**, donc refactorisation sans risque
de changement de comportement.

**Corrigé** : `fix_annee_debut_placeholder.py` importe désormais les
trois fonctions depuis `instance_generation_common.py` au lieu de
garder ses propres copies. Variable de cache locale `_registre_cache`
devenue inutile, retirée. Vérifié : plus aucune définition locale des
trois fonctions, les deux points d'appel existants (`_read_registre_
text()` ligne 203, `detect_registre_leakage()` ligne 563) fonctionnent
via l'import.

**Pourquoi c'était important de le traiter** : c'est exactement le
pattern de duplication qui avait causé de vraies divergences
fonctionnelles avant la factorisation de juillet/août dans
`instance_generation_common.py` (~20 fonctions dupliquées, plusieurs
avaient déjà divergé silencieusement à l'époque). Corrigé avant que ça
ne se reproduise ici.

---

## 12. GUI — `--force` du panneau localisation ne rafraîchissait pas le
menu — clos, testé en navigateur réel

**Retrouvé** en revue systématique de la Partie 2 (« `--force` du
panneau `--scan-pending` (`extract_localisation.py`) ne rafraîchit pas
dynamiquement le menu — contournable via `--scenario` »). Diagnostic
poussé bien plus loin que prévu — **trois causes distinctes, sur trois
fichiers**, chacune nécessaire mais pas suffisante seule.

### Cause 1 — `scripts_config.json`
Le champ `--slug` (type `slug_select`, `slug_type: "fiches_a_
localiser"`) de l'entrée `extract_localisation` n'avait **aucune
déclaration `slug_extra_params`** reliant son contenu à `--force`. Seul
`--scenario` déclenchait un rafraîchissement, via le mécanisme
générique `data-needs-scenario` (tous les `slug_select` y sont abonnés
par défaut) — `slug_extra_params` est un mécanisme opt-in (ajouté le 2
août), jamais branché sur ce champ précis. La description du champ
elle-même documentait le contournement (« laisser ce champ vide et
utiliser `--scenario` ») — preuve que le bug était connu et contourné
depuis un moment.

**Corrigé** : ajout de `"slug_extra_params": {"force": "--force"}` sur
le champ `--slug`. Description du champ mise à jour (contournement
`--scenario` devenu inutile, retiré du texte). **Vérifié par diff
programmatique** : une seule entrée modifiée dans tout le fichier
(`extract_localisation`), aucune autre touchée — pratique déjà établie
dans le projet à chaque modification de `scripts_config.json`.

### Cause 2 — `app.js`, `lireValeurChamp()`
Même une fois le mécanisme `slug_extra_params` câblé, la fonction
utilisée pour lire la valeur du champ source (`lireValeurChamp()`)
lisait `el.value` inconditionnellement — pour une checkbox HTML sans
attribut `value` explicite (le cas ici, vérifié dans le code de rendu),
`.value` renvoie toujours la chaîne statique `"on"`, **quel que soit
l'état coché ou non**. Deux autres fonctions du même fichier
(`collectArgs()`, `isFlagActive()`) géraient déjà correctement ce cas
via `.checked` — `lireValeurChamp()` était la seule exception.

**Corrigé** : `lireValeurChamp()` teste maintenant `el.type ===
'checkbox'` et renvoie `'true'`/`'false'` selon `el.checked` dans ce
cas, sinon `el.value` comme avant. Testé avec `node --check` (syntaxe
seulement, pas d'exécution navigateur possible depuis mon
environnement).

### Cause 3 — `app.py`, route `/api/slugs`
Même avec les deux points précédents corrigés, la route `get_slugs()`
et la fonction `_scan_localisation_candidats()` ne lisaient ni ne
transmettaient **jamais** le paramètre `force` au sous-processus
`extract_localisation.py --scan-pending` — le paramètre aurait été
silencieusement ignoré côté serveur même parfaitement envoyé par le
frontend.

**Corrigé** : `get_slugs()` lit désormais `request.args.get("force",
"").lower() == "true"` et le transmet à `_scan_localisation_
candidats(pipeline_dir, scenario, force=force)`, qui ajoute `--force` à
la commande du sous-processus si actif. **Vérifié séparément** que
`extract_localisation.py --scan-pending` respectait déjà correctement
`--force` au niveau du script lui-même (`collect_fiches(force=args.
force)`, déjà câblé) — aucun correctif nécessaire côté script.

### Test en conditions réelles — confirmé par David

Panneau « Repérer la localisation des fiches » ouvert dans le
navigateur, case « Retraiter même si déjà fait » cochée : le menu
« Une seule fiche » affiche maintenant toutes les fiches (déjà
traitées incluses), sans avoir besoin de toucher `--scenario`.
**Fonctionnel, confirmé en conditions réelles.**

---

## 13. Fichiers livrés cette session

**12 fichiers** au total, tous testés (syntaxe Python/JS validée
systématiquement, logique testée unitairement quand pertinent, `.bak`
créés automatiquement par les scripts de migration) :

**Correctifs sur scripts de production existants** :
- `inject_custom_events.py` — deux correctifs cumulés : documentation
  `zone_hint` dans `QUEUE_TEMPLATE` (§2) + filtre dur
  `acteurs_hint_count` via `truncate_actors()` (§9).
- `create_entities_and_instances.py` — correctif `slugify()` (§8).
- `create_entity.py` — correctif `slugify()` (§8, script legacy).
- `officialize_alliances.py` — correctif `slugify()` (§8).
- `fix_annee_debut_placeholder.py` — duplication `detect_registre_
  leakage()` retirée, import depuis `instance_generation_common.py`
  (§11).
- `app.js` — `lireValeurChamp()` corrigée pour les checkboxes (§12).
- `app.py` — route `/api/slugs` transmet désormais `force` au
  sous-processus (§12).
- `scripts_config.json` — `slug_extra_params` ajouté sur `--slug` de
  `extract_localisation` (§12).

**Nouveaux scripts d'audit/migration, réutilisables** :
- `fix_arctic_passage_duplicate.py` — migration de références
  alliance/opposition lors d'une fusion de doublon (§3). Déjà exécuté,
  mais réutilisable pour un futur cas similaire (patron générique :
  dry-run/`.bak`/exécution).
- `fix_test_durcissement_wikilinks.py` — nettoyage de wikilinks morts
  vers une fiche supprimée (§4). Réutilisable pour tout futur cas.
- `audit_broken_slugs.py` — audit en lecture seule des slugs
  potentiellement cassés par l'ancien bug d'accents (§8). Réutilisable
  périodiquement si besoin (avec la réserve du point d'amélioration
  noté : exclure `entite_template.md`).
- `rename_broken_slugs.py` — migration de renommage de slug (fichier +
  toutes ses références externes), distincte de la fusion (§8).
  Réutilisable pour tout futur cas de slug cassé détecté par le script
  d'audit ci-dessus.

**Chez David, à faire au prochain lancement** :
1. Remplacer les 8 fichiers de scripts de production dans leurs
   emplacements respectifs (`generator/` pour tous sauf `app.js`,
   `app.py`, `scripts_config.json` qui vont dans `gui/`).
2. **Redémarrage Flask requis** (changements dans `app.py` et
   `scripts_config.json`).
3. Les 4 scripts d'audit/migration sont déjà dans `generator/` (copiés
   en cours de session), rien à refaire — sauf si un futur cas
   similaire nécessite de les relancer.
4. Vérification GUI déjà faite par David en conditions réelles pour le
   fix `--force` (§12) — confirmé fonctionnel, rien à revérifier.

---

## 14. Point de reprise suggéré pour la prochaine session

**Chantier prioritaire, explicitement demandé par David** :

1. **`forces_attractives`/`forces_repulsives`** (§10) — David doit
   d'abord relire les 12 fiches `variables/*.md` et trancher quelle
   section (3, 4, ou fusion) sert de source de vérité, avant tout code.
   Une fois tranché : nouveau parseur de corps Markdown dans
   `loader.py` + câblage dans `build_variables_context()`
   (`prompt_builder.py`).

**Reste ouvert, sans urgence, à traiter au choix de David** :

2. Backlog #1 (validation retry longueur des articles) — toujours
   🟡, pas urgent, à valider au fil d'un futur batch de volume.
3. P17 (retest fiabilité `mistral-small`) — gardé pour plus tard.
4. Bug #27 (plausibilité logistique inter-zones) — **analyse d'articles
   à prévoir** pour vérifier si le symptôme s'est reproduit, avant de
   décider d'un correctif.
5. Backlog #6 (renommage YAML génériques) — décision toujours
   reportée.
6. Backlog #8 (troncatures JSON Mistral) — gardé pour plus tard.
7. `acteurs_hint_count` — correctif livré, à confirmer au fil de l'eau
   sur un futur run réel (pas de test dédié à provoquer).
8. **"Les Veilleurs des Nappes Phréatiques"** — idée rejetée dans
   `needs_review.yaml` (`category: mouvement` invalide, hallucinée par
   le LLM auto-suggest le 11 août). Décision jamais prise en fin de
   session (§0, question restée ouverte : corriger et créer l'entité,
   ou laisser tomber). **À trancher en tout début de prochaine
   session.**
9. Chantiers de fond en pause longue durée (P20 publication web, P21
   journaux oraux, P14 tier LLM strict) — inchangés, aucune urgence.

**Petit point d'amélioration noté, non traité** : `audit_broken_
slugs.py` (§8) ne filtre pas `entite_template.md` (le fichier gabarit)
de son rapport — faux positif mineur et inoffensif (le rapport
l'explique clairement comme "à vérifier manuellement"), mais à corriger
si le script est réutilisé souvent.

**Rappel de méthode, toujours valable** : à chaque modification de
`scripts_config.json`, vérifier par diff programmatique qu'aucune
entrée en dehors de celle(s) visée(s) n'a été altérée — fait
systématiquement cette session (§12).
