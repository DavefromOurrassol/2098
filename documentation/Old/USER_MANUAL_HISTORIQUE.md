# Manuel utilisateur — Historique des sessions et chantiers
*Contrepartie de `USER_MANUAL_COMPLET.md`, qui référence ce fichier
pour le détail narratif complet. Contient tous les addenda
chronologiques par session (bugs trouvés, itérations de test réel,
diagnostics, décisions) depuis la consolidation du 15 juillet 2026.
Consulter uniquement pour retrouver le détail d'un chantier passé ou
comprendre le raisonnement d'une décision — pas besoin de le recharger
à chaque session.*

*Consolidé le 15 juillet 2026, mis à jour le 3 août 2026, 9 août 2026,
10 août 2026, 11 août 2026 (deux fois : clarté des descriptifs le
matin, bugs réels + clôture du test navigateur GUI le soir), 12 août
2026, et 13 août 2026 (chantier dimension temporelle codé, chantier
cohérence événements custom confirmé en injection réelle, bug
`evenement_cle` corrigé). Scindé de `USER_MANUAL_COMPLET.md` le 29
août 2026 pour alléger le fichier rechargé à chaque session — voir ce
dernier pour la référence à jour de chaque script (notamment §2quater,
pipeline rédaction, qui consolide plusieurs addenda ci-dessous en
entrées de référence structurées).*

---

### Addendum — chantier `trajectoire` et audit longueur articles (9 août 2026)

Trois changements à `scripts_config.json` cette session, tous non
testés en navigateur (`gui_verified: false`) :

- **Entrée `create_entities`, champ `etat`** (mode custom) — renommé
  label "Trajectoire (contrainte dure)", 11 choix (au lieu des 6
  anciennes valeurs `etat_temporel`). Nouveau champ `est_clandestin`
  inséré juste après (select tri-état `oui`/`non`/vide) — voir §3bis
  pour le détail complet du câblage Python.
- **Entrée `audit_etat_temporel_fin`** — label et description corrigés
  (mentionnaient encore `etat_temporel`, disaient le chantier
  `annee_fin` "pas encore construit" alors qu'il est clos depuis cette
  même session — voir §5).
- **Nouvelle entrée `audit_longueur_articles`** — section `validation`,
  même famille que les 3 audits existants (`--dossier` optionnel comme
  seule option). Voir §5 pour le détail du diagnostic.

Vérification structurelle faite après ces trois changements : diff
programmatique confirmant qu'aucune des 26 autres entrées du fichier
n'a été altérée (comparaison champ par champ contre la version
d'avant-session).

### Addendum — clarté des descriptifs et validation navigateur (11 août 2026)

David a commencé à valider le GUI dans un vrai navigateur (backlog
Partie 1, point désormais renommé "Test navigateur des entrées GUI
modifiées") et a signalé, au fil du test, plusieurs descriptifs trop
techniques pour quelqu'un qui ne lit pas le code — trois entrées de
`scripts_config.json` reformulées en conséquence :

- **`fix_annee_debut_placeholder`** — descriptif ramené à l'essentiel,
  jargon interne retiré (`officialise_enrichi`, `ancrage_reel`,
  `annee_debut_verifiee` ne sont plus mentionnés dans le texte affiché).
- **`trace_injection`** — même traitement, plus un correctif de code sur
  la sortie elle-même (le texte produit par le script, pas seulement le
  descriptif du bouton) — voir §2, entrée `trace_injection.py`, pour le
  détail complet.
- **`fix_alliances_oppositions`** — la plus dense des trois : descriptif
  principal + 7 options + 2 libellés de rapports reformulés. Le
  vocabulaire du projet (alliances, oppositions, scénario, fiche) est
  conservé partout — c'est le jargon d'implémentation ("passe LLM",
  chemins de fichiers bruts affichés tels quels comme libellés) qui a
  été retiré ou reformulé.

**Principe appliqué aux trois** : garder le vocabulaire propre au monde
fictif et au projet (variables, scénarios, entités, alliances...), que
David maîtrise déjà et qui structure tout le vault — mais retirer le
vocabulaire d'implémentation interne (noms de fichiers YAML/JSON,
mécanique de pipeline, termes comme "injection"/"aval"/"rétroactif" sans
explication) qui n'apporte rien à quelqu'un qui clique sur un bouton
sans avoir lu le code.

**10 entrées passées à `gui_verified: true`** après clic réel dans le
navigateur par David : les 4 audits (`audit_dates_instances`,
`audit_etat_temporel_fin`, `audit_longueur_articles`,
`audit_type_relation_dominante`), les 2 entrées de veille
(`export_prompt_veille`, `import_veille_etat_monde`), `trace_injection`,
`fix_annee_debut_placeholder`, `fix_alliances_oppositions`, `generate`.
Vérification structurelle faite après coup (diff programmatique) :
exactement ces 10 entrées modifiées, aucune autre altérée. Restent à
`gui_verified: false` (non concernées par cette passe) : `create_entities`,
`enrich_minimal`, `generate_instances` — voir `BACKLOG_MASTER_9_AOUT.md`
Partie 1 pour le suivi.

### Addendum — session du 11 août 2026 (soir) : clôture du test navigateur GUI

Suite directe de l'addendum ci-dessus, même jour, deuxième session
(voir §2 pour `create_entities_and_instances.py` et §7 pour les bugs
`app.js`/`app.py` — détail complet dans les deux sections concernées,
pas répété ici). Résumé de ce qui change côté `scripts_config.json` :
les 3 dernières entrées (`create_entities`, `enrich_minimal`,
`generate_instances`) passent à leur tour à `gui_verified: true` — **les
28 entrées du panneau sidebar le sont désormais toutes**, chantier
"Test navigateur GUI" (ouvert en continu depuis fin juillet) clos pour
de bon. 17 clarifications de descriptifs supplémentaires (8
descriptifs principaux + 9 options), et `--zone-slug` de `generate.py`
basculé sur le nouveau type `zones_hier_journal`. 4 fichiers livrés :
`create_entities_and_instances.py`, `app.js`, `app.py`,
`scripts_config.json`.

### Addendum — session du 12 août 2026 : cohérence événements custom + validation signature

**1. Validation réelle du correctif signature itération 2** (ouvert
depuis le 10 août, voir §2ter point 4) — un run `generate.py` en
Semi-guidé avec une zone valide (`geneve_bunker_institutions`, passant
le filtre `zones_hier_journal` livré le 11 août soir) a confirmé la
signature apparaissant une seule fois, immédiatement sous la date.
Chantier clos.

**2. Diagnostic `annee_debut`/`ancrage_reel` sur les événements**
(question ouverte depuis le 8 août, voir §2ter et backlog) — mené sur
`inject_custom_events.py`, `fix_annee_debut_placeholder.py`,
`loader.py`, et un dépouillement réel de `registre_evenements.md` (53
événements custom). Conclusions : les événements ont une structure de
date différente des instances (champ `date` unique, pas de bande
`annee_debut`/`annee_fin`) ; aucune dérive de concentration observée
(pic max 11% sur une année, contre 22% pour les instances avant
correctif) ; mais **aucun mécanisme d'ancrage réel n'existait avant
cette session**, ni en mode auto ni en mode custom, et
`analyze_vault_coverage()` (couverture auto des événements) n'a — comme
`analyze_entity_coverage()` pour les entités — aucune dimension
temporelle. Décision prise : pas de mécanisme lourd type `ancrage_reel`
des instances (bande graduée + anti-recyclage), un enrichissement de
contexte suffit — voir point 3.

**3. Nouveau chantier — cohérence événements custom / vault, registre,
géographie, état du monde** (`inject_custom_events.py`) — détail complet
en §2, section `inject_custom_events.py`. Résumé : import des fonctions
`load_etat_monde_reel()`/`load_scenario_timeline_summary()` depuis
`instance_generation_common.py` (réutilisation, pas de duplication),
deux nouveaux blocs de contexte dans le prompt de développement
d'événement, validation mécanique de `zone_hint` contre les zones
réelles du scénario (refaite à chaque itération de la boucle scénarios,
initiale et retry). Couvre les deux modes (auto n'écrit que dans
`queue.yaml`, l'injection réelle passe toujours par le mode custom).
Testé en conditions réelles (dry-run, qui appelle le LLM pour de vrai —
voir piège transversal §0) sur 5 cas ciblés, tous concluants, dont un
test croisé (même `zone_hint` sur deux scénarios) prouvant que la
revalidation se refait bien par scénario. **Non testé en injection
réelle (non dry-run)** — chemin d'écriture non modifié par ce
correctif, risque jugé faible.

**Fichier livré** : `inject_custom_events.py`.

**4. Panneau Revue — slug/scénario/détail vides sur entités et signaux**
(`app.py`, fonction `_read_needs_review_yaml()`) — signalé par David sur
une entrée réelle ("Les Veilleurs des Nappes Phréatiques" affichée comme
`(entité)` / `—` / `—`). Voir §7, sous-section dédiée ci-dessous pour le
détail complet (diagnostic, les deux correctifs, tests).

---

### Addendum — session du 14 août 2026 : recherche exhaustive dans
l'archive, fusion de doublon, encodage cassé, filtre acteurs, bug GUI
`--force`

Session dense partie d'une recherche exhaustive dans l'archive complète
des anciens backlogs/handoffs (méthode et trouvailles détaillées dans
`HANDOFF_14_AOUT.md` §0), enchaînée sur le traitement systématique de
tout ce qui a été retrouvé, puis une revue complète de la Partie 2 du
backlog (points mineurs) avec le code source complet disponible pour la
première fois. Résumé des chantiers les plus substantiels ; le détail
complet de chacun (diagnostic pas à pas, tests, fichiers livrés) est
dans `HANDOFF_14_AOUT.md`.

**1. Encodage portugais cassé dans les slugs — cause racine et
migration.** `slugify()` utilisait une table de remplacement d'accents
**français uniquement** au lieu d'une normalisation Unicode générique —
tout caractère accentué non-français (portugais, espagnol...) tombait
dans le `re.sub` générique suivant et devenait `_` au lieu d'être
translittéré. Trois fichiers concernés, tous corrigés :
`create_entities_and_instances.py`, `create_entity.py` (legacy),
`officialize_alliances.py`. Correctif : normalisation Unicode NFD (même
principe que `_fold()`, déjà utilisée dans `gui/app.py`). Nouveau script
`audit_broken_slugs.py` (lecture seule, réutilisable) pour comparer le
slug enregistré de chaque entité au slug que produirait la fonction
corrigée — sur 590 entités auditées, 18 candidats, seulement 2 vrais
cas confirmés (`rede_paulista_de_distribuic_o_algor_tmica`,
`frente_sert_o_livre`), le reste étant des raccourcissements
volontaires de slug (faux positifs) ou un artefact du script lui-même
sur `entity_template.md` (nom réel du gabarit, en anglais — la première
version de cette note disait à tort "entite_template.md" en français ;
point clos le 15 août, voir addendum plus bas). Nouveau script `rename_broken_
slugs.py` (réutilisable) pour la migration proprement dite : renommage
de fichier (archétype + toutes ses instances par scénario) et
réécriture de toutes les références externes — contrairement à une
fusion de doublon (voir point 2 ci-dessous), c'est un vrai renommage
d'une même entité. Exécuté sur les 2 cas confirmés : 11 fichiers
renommés, 322 références réécrites dans 141 fiches, `documentation/`
explicitement exclu de la migration (historique, jamais réécrit —
même principe que pour `entites_custom/processed.yaml` au point 2).
`entites/_entities_list.json` mis à jour par remplacement de texte
ciblé, pas de parse/dump JSON complet, pour préserver le formatage
d'origine. `validate.py --verbose` final : 0 erreur.

**2. Doublon d'entité `arctic_passage_authority` /
`autorite_passage_arctique` — fusionné.** Diagnostic confirmé : vrai
doublon généré automatiquement par `extract_phantom_slugs.py` —
`entites_custom/processed.yaml` contient 3 entrées avec des champs
`_slug_fantome_original`/`_slug_corrige` le prouvant. Un slug fantôme
(probablement une référence de zone géographique, `geographie/
breakdown.md` ligne 2278) a été détecté sans entité correspondante et a
généré une entité indépendante, sans savoir qu'`arctic_passage_
authority` existait déjà pour la même institution — les deux instances
`breakdown` partageaient déjà le même jalon de registre et la même
trajectoire de fragmentation en factions (noté le 9 août). Point hors
scope identifié et volontairement non touché : les champs `zone:
autorite_passage_arctique` (dans les deux instances `breakdown` et dans
`event_instances/incident_passage_arctique_breakdown.md`) et l'entrée
`geographie/breakdown.md:2278` sont des références à une **zone
géographique**, pas à l'entité. Nouveau script `fix_arctic_passage_
duplicate.py` (réutilisable) : 17 fiches migrées, 34 références
alliance/opposition réécrites, puis `undo_custom.py --slug
autorite_passage_arctique --type entite --generalisation yes --execute`
(archétype fantôme + instance supprimés, `_entities_list.json`
nettoyé, `last_validated.json` réinitialisé). `validate.py --verbose`
final : 0 erreur.

**3. Wikilinks cassés `test_durcissement_policy_reform` — nettoyés.** 7
fiches `instances/*.md` de `policy_reform` référençaient encore une
fiche supprimée (résidu du 8 août), une ligne bullet identique
(`- [[test_durcissement_policy_reform]]`) dans la section
`## Relations` de chacune — contrairement au doublon Arctic, pas un
renommage mais une suppression pure de référence morte. Nouveau script
`fix_test_durcissement_wikilinks.py` (réutilisable pour tout futur cas
de wikilink mort similaire) : 7 lignes retirées sur 7 fiches.
`validate.py --verbose` final : 0 erreur, 0 avertissement.

**4. `acteurs_hint_count` (P15) — filtre dur enfin appliqué.**
Diagnostic précis dans `inject_custom_events.py` : la valeur était bien
calculée et bornée (`max(1, min(4, ...))`) mais **jamais transmise** à
`step2_develop_instance()` ni utilisée par `validate_instance()` —
calculée puis jetée sans effet, contrairement à `variables_hint_count`
qui a une vraie troncature dure après coup. Nouvelle fonction
`truncate_actors(instance_data, actors_hint, actors_hint_count,
available_actors)`, appliquée à chaque production d'acteurs par le LLM
(essai initial **et** chaque retry) — même schéma exact que la
troncature `variables` déjà en place : les hints imposés par
l'utilisateur sont toujours préservés en premier (via `dict.fromkeys`
pour dédupliquer sans perdre l'ordre), le reste est coupé au plafond.
Testé unitairement (troncature simple, préservation du hint imposé même
hors tête de liste, non-modification si déjà sous le plafond) — les 3
cas passent. **Pas encore confirmé en conditions réelles** — laissé en
validation au fil de l'eau plutôt que de provoquer un test dédié, même
logique que le chantier "retry longueur des articles" du 10 août.

**5. Duplication `detect_registre_leakage()` — consolidée.** La
fonction (documentée en détail au point 12 ci-dessus, chantier
"Diagnostic `annee_debut`/`ancrage_reel`... corrigé le 8 août") existait
en réalité en **double**, avec deux fonctions dépendantes
(`_read_registre_text()`, `_normalize_for_matching()`) elles aussi
dupliquées, entre `instance_generation_common.py` (module partagé) et
`fix_annee_debut_placeholder.py` (copie indépendante, jamais
factorisée). Vérifié avant de corriger : divergence purement cosmétique
entre les deux copies (docstrings différents, un style de code
différent pour `_read_registre_text()` mais fonctionnellement
équivalent, un `flags=re.UNICODE` explicite mais redondant côté
`fix_annee_debut_placeholder.py` puisque Python 3 traite déjà `\w` en
Unicode par défaut) — aucune divergence fonctionnelle actuelle.
`fix_annee_debut_placeholder.py` importe désormais les trois fonctions
depuis `instance_generation_common.py` au lieu de garder ses propres
copies ; variable de cache locale `_registre_cache` devenue inutile,
retirée. Même pattern de duplication qui avait causé de vraies
divergences fonctionnelles avant la factorisation de juillet/août
(~20 fonctions dupliquées à l'époque, plusieurs avaient déjà divergé
silencieusement) — corrigé avant que ça ne se reproduise ici.

**6. GUI — `--force` du panneau localisation ne rafraîchissait pas le
menu — corrigé (trois causes, trois fichiers).** Chantier retrouvé en
Partie 2 du backlog (« contournable via `--scenario` »), diagnostic bien
plus profond que prévu :

- **Cause 1 (`scripts_config.json`)** — le champ `--slug` (type
  `slug_select`, `slug_type: "fiches_a_localiser"`) de l'entrée
  `extract_localisation` n'avait **aucune déclaration
  `slug_extra_params`** reliant son contenu à `--force`. Seul
  `--scenario` déclenchait un rafraîchissement, via le mécanisme
  générique `data-needs-scenario` (tous les `slug_select` y sont
  abonnés par défaut) — `slug_extra_params` (ajouté le 2 août, voir
  §2ter ou section GUI correspondante) est un mécanisme opt-in, jamais
  branché sur ce champ précis. La description du champ documentait
  elle-même le contournement, preuve que le bug était connu et
  contourné depuis un moment. **Corrigé** : ajout de
  `"slug_extra_params": {"force": "--force"}`, description mise à jour
  (contournement retiré du texte, devenu inutile). Vérifié par diff
  programmatique qu'une seule entrée du fichier a été modifiée.
- **Cause 2 (`app.js`, `lireValeurChamp()`)** — même une fois le
  mécanisme câblé, la fonction utilisée pour lire la valeur du champ
  source lisait `el.value` inconditionnellement. Pour une checkbox HTML
  **sans attribut `value` explicite** (le cas ici, vérifié dans le code
  de rendu du champ `--force`), `.value` renvoie toujours la chaîne
  statique `"on"`, quel que soit l'état coché ou non — deux autres
  fonctions du même fichier (`collectArgs()`, `isFlagActive()`)
  géraient déjà ce cas correctement via `.checked`, `lireValeurChamp()`
  était la seule exception. **Corrigé** : test `el.type === 'checkbox'`
  ajouté, renvoie `'true'`/`'false'` selon `el.checked` dans ce cas.
- **Cause 3 (`app.py`, route `/api/slugs`)** — même avec les deux
  points précédents corrigés, `get_slugs()` et
  `_scan_localisation_candidats()` ne lisaient ni ne transmettaient
  **jamais** le paramètre `force` au sous-processus
  `extract_localisation.py --scan-pending` — silencieusement ignoré
  côté serveur même parfaitement envoyé par le frontend. **Corrigé** :
  lecture de `request.args.get("force", "").lower() == "true"`,
  transmis à `_scan_localisation_candidats(..., force=force)`, qui
  ajoute `--force` à la commande du sous-processus si actif. Vérifié
  séparément que `extract_localisation.py --scan-pending` respectait
  déjà correctement `--force` en interne (`collect_fiches(force=args.
  force)`) — aucun correctif nécessaire côté script lui-même.

**Testé et confirmé en conditions réelles par David dans le navigateur**
— panneau "Repérer la localisation des fiches", case "Retraiter même si
déjà fait" cochée, le menu "Une seule fiche" affiche désormais toutes
les fiches (déjà traitées incluses) sans avoir besoin de toucher
`--scenario`.

**7. `forces_attractives`/`forces_repulsives` — escaladé en chantier
substantiel, non résolu.** Voir §3 (audit de complétude snapshot/
variables) pour la mise à jour du constat initial, et
`BACKLOG_MASTER_9_AOUT.md` Partie 1 point 2 pour la portée complète du
chantier restant à faire — décision de conception à prendre par David
(quelle section du corps Markdown des fiches variables fait foi) avant
tout nouveau code dans `loader.py`/`prompt_builder.py`.

**Fichiers livrés cette session** : `inject_custom_events.py` (deux
correctifs cumulés : documentation `zone_hint` + filtre `acteurs_hint_
count`), `create_entities_and_instances.py`, `create_entity.py`,
`officialize_alliances.py`, `fix_annee_debut_placeholder.py`, `app.js`,
`app.py`, `scripts_config.json`, plus 4 nouveaux scripts d'audit/
migration réutilisables : `fix_arctic_passage_duplicate.py`,
`fix_test_durcissement_wikilinks.py`, `audit_broken_slugs.py`,
`rename_broken_slugs.py`. Détail complet, y compris les chantiers
retrouvés via l'archive et non traités (P17, Bug #27, nettoyage des
fichiers de rotation, décision sur "Les Veilleurs des Nappes
Phréatiques") : `HANDOFF_14_AOUT.md`.

### Addendum — session du 15 août 2026 : `forces_attractives`/
`forces_repulsives` mené à terme, gabarit entité renommé, "Les Veilleurs
des Nappes Phréatiques" créée

**7bis. `forces_attractives`/`forces_repulsives` — chantier complet, en
trois temps.**

*Décision de conception.* Analyse comparative programmatique des 12
fiches `variables/*.md` : section `## 3. Dynamique interne` (snake_case)
systématiquement plus riche (4 à 8 items par liste) que section
`## 4. Structure causale` (1 à 5 items), cette dernière étant quasi
toujours une paraphrase compressée de la première, avec un artefact de
formatage (`snake_case` cassé) observé sur 2 fiches sur 12
(`systemes_productifs_travail`, `technologie_information`) —
caractéristique d'un contenu dérivé plutôt qu'indépendant. **Décision :
section 3 comme source de vérité unique**, section 4 ignorée.

*Développement.* Nouvelle fonction `_extract_forces_from_body()` dans
`loader.py` (même convention que `_extract_indicateurs_from_body()`
préexistante — regex sur le bloc `## 3. Dynamique interne`, extraction
des sous-listes `**forces_attractives**`/`**forces_repulsives**`).
Câblée dans `load_variable()` : deux nouvelles clés `forces_attractives`
et `forces_repulsives` au même niveau que `indicateurs`, `sub_variables`.
Côté `prompt_builder.py`, `build_variables_context()` affiche désormais
les 4 premiers items de chaque liste, par variable détaillée (même
plafond que `indicateurs[:4]` déjà en place). Testé unitairement contre
les 12 fiches réelles (comptages exacts confirmés, cohérents avec
l'analyse comparative de la décision) puis en génération réelle via
Flask (prompt inspecté directement, forces bien présentes et limitées à
4 items).

*Trois problèmes découverts et corrigés en cours de validation réelle
— chacun re-testé sur au moins une génération après correctif :*

- **(a) Déséquilibre systématique répulsif/attractif.** Sur les 3
  premiers articles tests, 0 trace de force attractive malgré leur
  présence dans le prompt — le LLM ne mobilisait que le répulsif,
  cohérent avec un ton de rédaction tendu mais laissant la moitié du
  contenu nouvellement câblé inexploité. Consigne de pilotage ajoutée
  dans `build_variables_context()`, d'abord descriptive ("à parts
  égales" — insuffisante), puis reformulée en contrainte concrète et
  actionnable ("au moins un fait/acteur/citation illustrant une force
  attractive sur l'ensemble de l'article"). Portée clarifiée une
  deuxième fois après question de David : la contrainte porte sur
  l'article dans son ensemble, pas sur chaque variable individuellement
  (risque de bourrage artificiel sinon). Confirmée fonctionnelle sur
  test réel (article `breakdown`, "Opération Baraka" — résilience/
  reconstruction citée explicitement à côté du récit de tension
  dominant).

- **(b) Récurrence anormale de l'entité `terminal_kharg_data_haven`**
  comme sujet principal de l'article sur 4/4 générations consécutives,
  deux scénarios différents (`policy_reform`, `new_sustainability`),
  thématique `actualites_a_la_une` à chaque fois. Diagnostic exact :
  `filter_instances_for_thematique()` (`loader.py`) score chaque
  instance par recoupement de variables + zones systémiques +
  `impact_systemique_global`. Cette entité, avec un impact élevé et un
  recoupement constant avec les zones de cette thématique précise,
  obtient un score structurellement avantageux sur chaque scénario où
  elle existe — et la rotation à mémoire (`_select_least_used_
  instances()`, ajoutée le 2 août) ne départage que les ex-aequo de
  score **strict**, jamais atteint ici puisque son avantage est réel
  mais léger. **Corrigé** : nouvelle fonction `_score_bucket()`,
  regroupement des scores par tranche de tolérance
  (`INSTANCE_SCORE_TOLERANCE = 2.0`, calculée relativement au score
  maximum du lot de candidats pour éviter un effet de bord d'arrondi
  identifié en testant une première version par arrondi absolu) plutôt
  que par égalité stricte — la rotation s'applique désormais aux scores
  proches, pas seulement identiques. Testé sur cas synthétiques
  reproduisant le problème (recul de 15/15 à 4/15 sur un écart réaliste
  d'environ 1 point) tout en vérifiant qu'un écart réellement dominant
  (15 points) reste à 15/15 — le principe de fond du mécanisme
  (pertinence prioritaire sur rotation forcée) n'est pas cassé. Confirmé
  en conditions réelles sur `eco_communalism` (compteur d'usage déjà à 2
  pour cette entité sur ce scénario) : Kharg-9 relégué à une mention
  secondaire, plus sujet principal.

- **(c) `climat_environnement_global` totalement absente du texte sur
  5/5 générations**, alors qu'elle est variable pilote sur 4 des 5
  scénarios testés. Vérification précise (reconstruction manuelle de
  `priority[:MAX_VARIABLES_DETAIL]` avec les vraies données de la fiche
  `thematiques/actualites_a_la_une.md`) : elle était bien systématiquement
  dans le top 6 détaillé à chaque run (position 5 ou 6 sur 6) — donc pas
  un problème de troncature côté code, contrairement à l'hypothèse
  initiale. Le LLM recevait la donnée en détail (y compris ses forces)
  mais ne la mobilisait jamais, probablement un effet de position dans
  un prompt de 56-62k caractères combiné à l'orientation narrative de la
  thématique (`variables_visibles` de `actualites_a_la_une` ne contient
  aucune variable climatique, `dependances_fortes` pointant vers
  géopolitique/technologie). Nouvelle consigne de couverture minimale
  des variables pilotes (tag `[VARIABLE PILOTE]`, une résonance —
  fait, chiffre, acteur — exigée par variable pilote, portée clarifiée
  pour ne pas exiger la reprise exhaustive des forces précises). Premier
  test après ce correctif positif (article `breakdown`, première
  résonance climatique obtenue en 6 articles, via le thème de
  désertification) — un seul échantillon, à confirmer sur plusieurs
  générations futures.

**Considéré terminé par David en fin de session**, avec la réserve que
le 3e correctif (couverture des pilotes) n'a qu'un seul test positif à
ce stade. Détail complet : `HANDOFF_15_AOUT.md`.

**8. Gabarit entité — nom réel corrigé, déplacé vers `/templates`.**
Le point Partie 2 du 14 août ("`audit_broken_slugs.py` ne filtre pas le
gabarit") avait été noté avec le mauvais nom (`entite_template.md`,
français) — jamais présent sur le vault. Nom réel confirmé par
recherche directe : `entity_template.md` (anglais). Filtre corrigé dans
`audit_broken_slugs.py`. Déplacement décidé et exécuté par David vers
`/templates` (cohérent avec `instance_template.md`, déjà présent à cet
emplacement depuis le 14 août) : `entites/entity_template.md` →
`templates/entity_template.md`. Vérification en amont avant déplacement :
aucune référence codée en dur au fichier par son nom ailleurs dans le
projet, mais deux endroits listaient `entites/*.md` sans filtrer le
gabarit (`gui/routes_dashboard.py`, total du dashboard ;
`generator/generate_instances.py`, chargement de toutes les fiches) —
corrigés de facto par le déplacement, sans toucher leur code. Confirmé
indirectement par le compteur global de `validate.py` (590 → 589
entités après déplacement), pas vérifié fichier par fichier.

**9. "Les Veilleurs des Nappes Phréatiques" — décision tranchée,
entité créée, dette historique découverte au passage.** Décision en
tout début de session (point laissé ouvert le 14 août) : corriger et
créer, pas d'abandon — contenu jugé solide (ancrage géographique réel,
cohérence forte avec `eco_communalism`, rôle différencié). `category:
mouvement` absente de `VALID_CATEGORIES` — `organisation` retenue comme
catégorie de repli la plus proche, après vérification que `category`
n'est utilisée nulle part dans `prompt_builder.py` (aucune influence sur
le contenu narratif généré, uniquement une étiquette de classification
interne, vérifiée par `grep` sur tout `prompt_builder.py`, zéro
résultat).

Avant correction, audit élargi (`grep -h "^category:" entites/*.md |
sort | uniq -c`) : 4 autres fiches déjà présentes dans le vault avec la
même catégorie invalide (`coalition_vivant`, `collectifs_du_seuil`,
`internationale_travailleurs_augmentes`, `mouvement_racines_vivantes`).
Ces 4 fiches n'ont aucun champ `date_generation` (contrairement aux
entités passées par le pipeline custom récent), suggérant une origine
du socle initial de juin 2026, antérieure à l'existence du garde-fou
`VALID_CATEGORIES` — pas une faille de couverture active du pipeline
actuel (confirmé par un deuxième audit sur `entites_custom/queue.yaml`/
`processed.yaml`/`needs_review.yaml` : une seule occurrence de
`mouvement`, celle déjà identifiée et traitée). Le champ `category` est
vérifié par `validate.py` (avertissement, pas erreur bloquante) — ces 4
fiches généraient donc déjà 4 avertissements silencieux à chaque
validation. Corrigées en lot (`sed -i ''`), confirmé par `validate.py` :
0 erreur, 0 avertissement, disparition des 4 lignes "catégorie
invalide".

Idée elle-même : `entites_custom/needs_review.yaml` corrigé
(`category: mouvement` → `organisation`), remise en file via
`requeue_needs_review.py`, entité créée via
`create_entities_and_instances.py --mode custom`. Cycle post-injection
complet enchaîné automatiquement (`extract_localisation.py` →
`review_localisation.py --auto-resolve` → `validate.py`, comme toujours
dès qu'au moins une entité/instance est créée) : 5 instances créées sur
6 scénarios (`breakdown`, `fortress_world`, `new_sustainability`,
`policy_reform`, `reference`), localisations résolues (3 extraites
directement, 2 ambiguës auto-résolues sans review manuelle restante).
**1 échec** sur `eco_communalism` (le `scenario_ref` d'origine de
l'idée) : le garde-fou `ancrage_reel` a correctement bloqué une
hallucination du LLM (citation d'un événement fictif du registre du
scénario — "mouvement mondial de souveraineté hydrique locale" — comme
s'il s'agissait d'un fait réel et vérifiable de 2026). **1 avertissement
mineur** sur l'instance `reference` : une alliance filtrée car pointant
vers un slug invalide (`reseau_des_capteurs_citoyens_reference`),
probablement une entité inventée par le LLM sans existence réelle dans
le vault — filtrage correct du garde-fou, rien à corriger. `validate.py`
final : 0 erreur, 0 avertissement (590 entités, 737 instances). **Reste
en attente pour une prochaine session** : retenter la génération de
l'instance `eco_communalism`.

**Fichiers livrés cette session** : `loader.py` (fonction
`_extract_forces_from_body()`, câblage dans `load_variable()`, nouvelle
fonction `_score_bucket()` et refonte de `_select_least_used_instances()`
pour la tolérance de rotation), `prompt_builder.py` (câblage des forces
dans `build_variables_context()`, consigne d'équilibre attractif/
répulsif, consigne de couverture des variables pilotes),
`audit_broken_slugs.py` (nom du gabarit corrigé), `needs_review.yaml`
(catégorie corrigée pour "Les Veilleurs des Nappes Phréatiques").
**Redémarrage Flask requis** après changement de `loader.py` — piège
rencontré en cours de session (un premier test de génération a tourné
sur l'ancienne version du fichier, sans effet du correctif, avant
redémarrage). Détail complet, y compris les échanges de diagnostic et
les tests intermédiaires : `HANDOFF_15_AOUT.md`.

### `constrained_variables` — activation dans le prompt, Option A (19 août 2026)

Champ frontmatter présent sur les 6 fiches `scenarios/{scenario}.md`
(3 variables distinctes par scénario) depuis les fondations du projet,
chargé par `loader.py` et propagé jusqu'au snapshot (`snapshot.py`),
mais **jamais consommé par `prompt_builder.py`** — listé en Partie 2 du
backlog comme point mineur depuis le 14 août ("calculé, jamais affiché
dans le prompt"). Retrouvé en nettoyant cette section le 19 août.

**Intention d'origine, clarifiée par David** : une variable "contrainte"
n'est PAS une valeur figée ni un simple état défavorable — c'est une
**limite structurelle sur l'espace des trajectoires accessibles** dans le
scénario. Distinction à trois rôles : *moteur* (la variable pousse
activement le scénario dans une direction — `dominant_variables`/
`reinforced_variables`, déjà câblées en `pilot_variables`), *contrainte*
(la variable limite les trajectoires accessibles, sans nécessairement les
piloter), *conséquence* (la variable résulte des autres dynamiques). Une
variable contrainte peut évoluer, mais ne peut pas basculer vers son
extrême opposé sans qu'une rupture structurelle majeure du scénario le
justifie explicitement — exemple donné : dans un monde de repli
territorial (`fortress_world`), la mobilité humaine ne peut pas être
dépeinte en ouverture soudaine, même si elle peut légèrement fluctuer.

**Deux options de mise en œuvre envisagées** : Option A (direction de la
borne déduite par le LLM depuis le contexte narratif du scénario déjà
transmis dans le prompt) vs Option B (encodage explicite de la direction
dans le frontmatter, `{variable, direction_interdite}` par entrée —
demande une migration de schéma + rédaction manuelle sur les 18 entrées).
**Option A retenue** — plus simple, le contexte narratif déjà fourni
(`system_logic`/`interpretation` du scénario) est jugé suffisamment
explicite pour que le LLM déduise correctement le sens de chaque borne.

**Câblage réalisé, `build_variables_context()` (`prompt_builder.py`)** :
- `constrained_variables` du snapshot ajouté à l'ordre de priorité des
  variables affichées, aux côtés de `pilot_variables`.
- Nouveau tag `[VARIABLE CONTRAINTE]`, priorité d'affichage `PRINCIPALE >
  PILOTE > CONTRAINTE` — une variable ne montre qu'un seul tag même si
  elle pourrait cumuler pilote+contrainte narrativement, pour rester
  lisible dans le prompt.
- Nouvelle consigne dédiée, juste après celle sur la couverture des
  variables pilotes, reprenant fidèlement la distinction ci-dessus avec
  l'exemple de la mobilité humaine en monde fortifié — insiste
  explicitement sur le fait que ce n'est pas une valeur imposée mais une
  borne directionnelle à déduire du contexte déjà fourni.

**Testé unitairement** (données simulées, tag et consigne confirmés
présents dans la sortie) puis **en conditions réelles sur 2 générations
complètes** (`fortress_world`, variable contrainte
`demographie_mobilite_humaine`) : tag et consigne bien injectés dans le
vrai prompt (confirmé sur prompt brut, premier essai `dry-run`) ; deux
articles générés (thématiques `religion_spiritualite` puis
`actualites_a_la_une`) sans aucune contradiction de la borne. **Réserve
notée explicitement** : les deux thématiques testées n'obligeaient pas
le LLM à se prononcer activement sur la mobilité humaine — validation
positive mais faible, pas un test réellement discriminant. Aucune
régression observée sur la couverture des variables pilotes ni la
qualité narrative des deux articles (longueurs cohérentes avec le format
demandé, légers dépassements sous le seuil de retry).

**Considéré suffisant par David, clos pour la prod.** Un test plus
exigeant (thématique société/démographie/migrations, si elle existe dans
`thematiques/`) resterait à faire pour une confirmation plus solide, à
envisager seulement si un doute apparaît sur un futur batch réel — pas
bloquant dans l'intervalle.

**Fichier livré** : `prompt_builder.py` (3 modifications localisées dans
`build_variables_context()`, aucun autre fichier touché).



Ajoutée à `scripts_config.json`, section `validation`, sur le même
patron que les audits déjà en place (`audit_dates_instances`,
`audit_type_relation_dominante`, etc. — voir §5 pour le détail complet
du script). Quatre options exposées : `--vault-root` (texte, optionnel,
vide = racine du vault courant), `--report` (checkbox, cochée par
défaut, écrit le rapport dans `documentation/need_action/
instances_manquantes.md`), `--seuil-absolu` et `--seuil-suspect`
(nombres, valeurs par défaut 3 et 0.5, exposés pour ajuster la
sensibilité de classification sans toucher au code). Champ `yaml_files`
renseigné (même mécanisme que `fix_alliances_oppositions`, voir plus
haut) pour afficher le rapport `.md` directement dans le panneau de
review après un lancement avec `--report`. **Confirmé fonctionnel dès
le premier lancement réel depuis le navigateur par David** — rapport
bien écrit sur disque, résultat cohérent avec les runs CLI précédents
de la même session. `gui_verified: true`. Redémarrage Flask requis
(changement dans `scripts_config.json`).

### Validation à grande échelle du retry longueur + `audit_longueur_articles.py` v4 (21 août 2026)

Chantier backlog Partie 1 point 1 (voir §2ter pour le mécanisme de
retry lui-même, ajouté le 10 août). L'échantillon initial (12 articles,
3 retries) était jugé trop petit pour mesurer fiablement le taux de
réussite réel du mécanisme, sur une génération qui tourne à
température 1.0 (forte variance).

**`audit_longueur_articles.py` étendu en v4** : les versions précédentes
mesuraient seulement "dans la plage ou non" — pas la bonne question
pour ce chantier, puisque le retry ne se déclenche que si l'écart
dépasse `RETRY_DEVIATION_THRESHOLD = 0.40` (40%, `api.py`). Nouvelle
fonction `deviation_ratio()`, copie exacte de `_deviation_ratio()` côté
`api.py`, pour reproduire fidèlement la condition de déclenchement.
Nouvelle section de rapport qui :
- exclut proprement les articles générés avant le 10 août (pas de champ
  `retry_longueur`/`mots_reels` dans leur frontmatter, mécanisme
  inexistant à l'époque) plutôt que de les compter à tort contre le
  mécanisme ;
- pour les articles post-mécanisme, croise la déviation recalculée avec
  `retry_longueur` déclaré dans le frontmatter, détecte deux anomalies
  possibles : déviation > 40% mais retry non déclenché (signal de bug),
  et retry déclenché mais résultat final encore hors plage à plus de
  40% (comportement normal et documenté — un seul retry, résultat
  accepté quoi qu'il arrive — mais désormais quantifié) ;
- calcule un taux de succès du retry (résultat ramené sous 40% d'écart).

**Résultat sur le vault réel (56 articles scannés, 25 post-mécanisme)** :
4 retries déclenchés, 0 anomalie détectée, **taux de succès du retry :
100% (4/4)**. Sur les 29 articles "hors plage" au sens strict (tous
formats confondus), seuls 3 dépassaient 40% d'écart — et les 3 dataient
de fin juin/début juillet, donc antérieurs au mécanisme, pas des échecs
de celui-ci. **Chantier considéré clos** — voir `BACKLOG_MASTER_9_AOUT.md`
Partie 4 pour le résumé de clôture.

**Fichier livré** : `audit_longueur_articles.py` (v4 — nouvelle
constante `RETRY_DEVIATION_THRESHOLD`, fonction `deviation_ratio()`,
nouvelle section de rapport, aucune modification des sections Cas A/B
préexistantes).

### P22 — Bloc `simulation` rendu opérationnel dans `snapshot.py` (20 août 2026, documenté le 21 août)

**Trou de traçabilité comblé rétroactivement** : cette session (20 août)
n'a pas eu de handoff rédigé sur le moment. Contenu et statut
(validé/fonctionnel) confirmés a posteriori par David le 21 août.

Chantier ouvert le 19 août (voir addendum précédent pour le contexte
complet et le nœud de décision) : le bloc `simulation` des fiches
`variables/*.md` (`volatility`/`predictability`/`uncertainty_level`/
`tipping_point_risk`/`systemic_criticality`) était chargé par
`loader.py` mais jamais relu en aval. Question posée par David avant
tout code : métadonnée purement descriptive, ou opérationnelle (le
moteur calcule réellement avec ces valeurs) ? **Décision : opérationnel.**

**Trois champs câblés**, mapping qualitatif → numérique avec valeur par
défaut garantissant la non-régression totale (toute variable sans bloc
`simulation` renseigné, ou avec une valeur de champ absente/non
reconnue, se comporte exactement comme avant ce chantier) :

- **`volatility`** → `VOLATILITY_DAMPING` (`low`:0.3, `medium`:0.5,
  `high`:0.8, `very_high`:1.0, défaut 0.5 = comportement fixe d'avant).
  Module le facteur d'amortissement de la propagation matricielle côté
  variable **cible** (remplace le `× 0.5` fixe partout où il apparaissait
  — instances/événements/signaux custom) : une cible volatile réagit
  plus fort à une poussée reçue.
- **`tipping_point_risk`** → `TIPPING_THRESHOLD_ADJUST` (`low`:0,
  `medium`:5, `high`:10, `very_high`:15, défaut 0). Abaisse les seuils
  de détection de tension dans `check_coherence()` (60 pour la tension
  négative, 70 pour la cascade critique) côté variable qui **porte** le
  risque — source ou cible selon le test, jamais les deux à la fois.
- **`systemic_criticality`** → `CRITICALITY_MULTIPLIER` (échelle réelle
  entière 1-5, vérifiée sur les 12 fiches variables, pas une chaîne
  qualitative comme les deux champs ci-dessus : {1:0.7, 2:0.85, 3:1.0,
  4:1.3, 5:1.6}, défaut 1.0). Multiplicateur additionnel sur le delta
  propagé côté variable **source** : une variable critique qui bouge
  pèse plus lourd sur ce qu'elle influence.

`predictability`/`uncertainty_level` restés **hors scope** —
introduiraient de l'aléa dans un pipeline aujourd'hui déterministe.

**Implémentation** : nouvelle fonction `_get_simulation_param(all_variables,
var_slug, field, mapping, default_value)` centralise la lecture du champ
qualitatif + la conversion + le repli sur défaut. Câblée dans
`check_coherence()` (nouveau paramètre `all_variables`),
`apply_custom_injections()`, `apply_custom_events()`,
`apply_custom_signals()` (les trois avec le même nouveau paramètre) —
les quatre fonctions qui appliquaient jusqu'ici un facteur fixe (`0.5`
d'amortissement, seuils `60`/`70` non ajustés) l'appliquent désormais
via ce mapping.

**Fichier livré** : `snapshot.py` (bloc de constantes P22 + fonction
`_get_simulation_param()` + signature élargie des 4 fonctions listées
ci-dessus).

### Garantie d'inclusion des instances custom dans `filtered_instances` (`loader.py`, 21 août 2026)

Résolution du risque structurel identifié le 3 août
(`BACKLOG_MASTER_9_AOUT.md`, ex-Partie 3) : `snapshot.py` applique
**toujours** les deltas d'une instance custom (`apply_custom_injections()`,
appelée sur `custom_instances` — liste non filtrée, tous les
`injection.type == "custom"` du scénario), mais sa description
narrative ne parvenait au LLM que si elle survivait au même filtrage
par pertinence thématique qu'une instance du socle
(`filter_instances_for_thematique()`/`select_instances_by_impact()`,
plafond `MAX_INSTANCES = 6`) — confirmé par lecture de code, pas
seulement théorique : décalage réel entre "ce qui bouge les chiffres du
monde" et "ce que le LLM voit et peut nommer".

**Nouvelle fonction partagée `_select_with_custom_guarantee(scored,
scenario_slug, dry_run, max_n)`**, utilisée par les deux points de
sélection : toute instance avec `injection.type == "custom"` obtient
une place garantie dans `filtered_instances`, même à score de
pertinence nul pour la thématique en cours. Si plus de `max_n`
instances custom sont en lice qu'il n'y a d'emplacements disponibles
(édge case non rencontré à ce jour, vault à zéro instance custom),
priorité entre elles par score décroissant, avec avertissement `[WARN]`
explicite. Les emplacements restants vont aux instances non-custom, via
**exactement** la même rotation à mémoire qu'avant ce correctif
(`_select_least_used_instances()`) si `scenario_slug` est fourni, sinon
un tri déterministe simple (repli legacy, inchangé).

**Non-régression garantie par construction** : sans instance custom
parmi les candidates (cas de tout le vault à ce jour), le comportement
est strictement identique à avant — testé et confirmé sur 6 cas
synthétiques (non-régression sans custom, custom à score nul garanti,
édge case 8 instances custom pour 6 emplacements, rotation avec
`scenario_slug`, plus les 2 mêmes cas côté `select_instances_by_impact()`).

**Non testé en conditions réelles** — le vault ne contient à ce jour
aucune instance custom (seulement des événements custom). À confirmer à
la prochaine injection réelle d'une instance custom, via les logs
`[loader] Instance(s) custom garantie(s) dans filtered_instances : ...`.

**Fichier livré** : `loader.py` (nouvelle fonction
`_select_with_custom_guarantee()`, `filter_instances_for_thematique()`
et `select_instances_by_impact()` toutes deux réécrites pour l'utiliser
— aucun autre fichier touché, `snapshot.py`/`prompt_builder.py` appellent
ces deux fonctions sans changement de signature).

### Cooldown d'usage + exemption de dominance écrasante (`loader.py`, 22 août 2026)

Remplace une première tentative (pénalité de score, jamais déployée —
voir historique dans le code et `BACKLOG_MASTER_9_AOUT.md` point 9bis)
invalidée par test synthétique avant tout usage réel : une pénalité
proportionnelle au nombre d'usages cumulés échoue mathématiquement dès
que plusieurs instances sont sélectionnées à la même fréquence (cas
réel diagnostiqué le 22 août : cluster de 5-6 institutions
structurellement favorisées ensemble dans `policy_reform`, pas une
seule dominante isolée) — deux instances à égalité de fréquence
accumulent la même pénalité, l'écart entre elles ne bouge jamais, quel
que soit le plafond choisi.

**Mécanisme retenu — cooldown dur, indépendant du score.** Dans
`_select_least_used_instances()` : après `COOLDOWN_STREAK = 3`
sélections **consécutives** pour un scénario donné, une instance
devient inéligible pendant `COOLDOWN_DURATION = 2` apparitions
suivantes où elle aurait autrement été candidate — quel que soit son
score. N'étant pas comparatif (ne compare jamais deux instances entre
elles), ce mécanisme n'a pas le défaut mathématique de la première
tentative.

**Exemption de dominance écrasante** (`DOMINANCE_EXEMPTION_GAP = 10.0`) :
une instance dont le score dépasse la 2e meilleure candidate du lot
d'au moins ce seuil échappe entièrement au cooldown ce round-ci (ni
cooldown possible, ni accumulation de streak). Calibré empiriquement
entre l'écart réel diagnostiqué (`directive_kontinuum_policy_reform`,
~5.5 points — doit rester soumis au cooldown) et un écart réellement
extrême (testé synthétiquement à 16 points — doit en être exempté).
Valeur ouverte à recalibrage si les scores réels du vault s'écartent
significativement de ces deux repères.

**Structure de `state/instance_usage.json`** étendue par scénario :
`instances` (compteur cumulé, inchangé depuis le 2 août), plus deux
nouvelles clés `streaks` (sélections consécutives en cours) et
`cooldowns` (apparitions restantes avant réintégration) — additif,
aucun risque de casse sur l'existant.

**Testé sur cas synthétiques** (cluster réel : 12/20 au lieu de 20/20
sans le mécanisme ; dominance écrasante : 20/20 conservé ; cas limite
juste sous le seuil d'exemption : 12/20, comme le cluster ; premier run
sans historique : identique au comportement du 15 août). **Confirmé en
conditions réelles** (2 batches sur `policy_reform`, thématique
`actualites_a_la_une`) : deux déclenchements réels observés
(`consortium_helios_policy_reform`, `terminal_kharg_data_haven_policy_reform`),
cycle complet déclenchement → cooldown actif → expiration →
réintégration confirmé sur `consortium_helios`.

### Mécanisme `priorite_forcee` — présence garantie durable d'une entité (22 août 2026)

Permet de forcer délibérément la présence d'une entité (institution/
personne) dans les articles générés, sur un scénario donné — cas
d'usage : un événement narratif majeur rendant une entité un acteur
permanent qu'on veut voir cité partout. Garantit la **présence/citation**
(comme la garantie custom du 21 août), pas le statut de sujet
principal. Portée **par instance** (une entité peut être forcée sur un
scénario mais pas un autre).

**Champ de frontmatter** sur une instance : `priorite_forcee: true`
(absent/`false` par défaut). Deux points de câblage dans `loader.py` :
- `_select_with_custom_guarantee()` : pool garanti élargi de
  `injection.type == "custom"` à `injection.type == "custom" or
  priorite_forcee == True`.
- `filter_instances_for_thematique()` : même élargissement sur la
  condition qui empêche un score nul d'être écarté avant la garantie.

Une instance `priorite_forcee` échappe automatiquement au cooldown
d'usage ci-dessus (elle ne passe jamais par le circuit de rotation) —
aucun conflit entre les deux mécanismes.

**`set_priorite_forcee.py` (nouveau script)** : patch chirurgical du
frontmatter d'une instance existante — isole le bloc frontmatter par
regex, insère/remplace/retire la ligne `priorite_forcee:` selon le cas,
sans toucher au reste du fichier, sans appel LLM. Fonction
`set_priorite_forcee(slug, value, instances_dir=None)` réutilisable en
CLI (`--slug`, `--scenario` [accepté mais non utilisé, le scénario est
déjà encodé dans le slug d'instance], `--value {true,false}`) et
importable depuis `create_entities_and_instances.py`.

**Deux points d'activation, tous deux testés en conditions réelles** :
1. **Création** (`create_entities_and_instances.py`) : checkbox
   `priorite_forcee` dans le formulaire custom du GUI
   (`config_fields` de `create_entities`), propagée via
   `process_custom_idea()` → `generate_instances_for_entity()` (nouveau
   paramètre `priorite_forcee=False`) → appel à `set_priorite_forcee()`
   après chaque instance créée avec succès (`status == "created"`
   uniquement — jamais tenté sur un échec, aucun risque de crash sur
   ce cas). Documenté dans `QUEUE_TEMPLATE`.
2. **Édition d'une instance existante** : nouvel outil GUI dédié
   (section `entites_nettoyage` de `scripts_config.json`, id
   `set_priorite_forcee`) — aucun panneau d'édition d'instance
   n'existait avant ce chantier (seulement de la création). Champs :
   `--scenario` (filtre la liste), `--slug` (`slug_select`,
   `slug_type: "instances"`), `--value` (Forcer/Retirer).

**4 bugs GUI trouvés et corrigés en testant, tous introduits par les
nouvelles entrées de ce chantier** (aucun n'affectait le GUI avant
aujourd'hui) :
- `priorite_forcee` de `create_entities` sans `"default"` explicite →
  premier choix de la liste (`true`) pré-sélectionné par défaut.
  Corrigé (`"default": "false"`).
- Entrée `set_priorite_forcee` : `"optional": false` au lieu de
  `"required": true` (la clé réellement lue par la validation
  pré-lancement dans `app.js`) — le GUI laissait lancer sans `--slug`.
  Corrigé sur les 3 champs.
- `set_priorite_forcee.py` n'acceptait pas `--scenario` (envoyé par le
  GUI, jamais déclaré côté `argparse`) → `unrecognized arguments`.
  Corrigé (accepté, non utilisé fonctionnellement).
- **Piège latent plus large, `app.js`** : `loadSlugsForSelect()`
  (contrairement à `loadSlugsForChips()`, qui préserve les sélections
  actives au rechargement depuis le 2 août) ne préservait jamais la
  sélection d'un `<select>` simple lors d'un rechargement déclenché par
  le changement d'un autre champ — un `slug_select` dépendant du
  scénario perdait silencieusement sa valeur si l'utilisateur
  choisissait l'instance avant le scénario. Nouveau mécanisme opt-in
  `requires_scenario_selected` (sur l'option, propagé en
  `dataset.requiresScenarioSelected`) : le champ reste désactivé avec
  un placeholder explicite ("Choisis d'abord un scénario") tant
  qu'aucun scénario n'est choisi, empêchant la séquence problématique à
  la source plutôt que d'en réparer les effets. N'affecte aucun champ
  existant qui ne déclare pas ce flag.

**Testé de bout en bout en conditions réelles** : entité de test créée
sur 6 scénarios (4 succès avec `priorite_forcee: true` confirmé par
grep direct sur le vault, 2 échecs dus à des garde-fous préexistants
sans lien avec ce chantier — JSON malformé LLM, `ancrage_reel`) ;
outil d'édition testé dans les deux sens (retrait puis réactivation) ;
`validate.py` final 0 erreur/0 avertissement sur 762 instances.
Nettoyage de fin de session : entité de test supprimée via
`undo_custom.py --generalisation yes --execute`.

### Uniformisation du dossier de sortie `generate.py` (22 août 2026)

Un article généré en mode unitaire (`generate.py`, hors série)
atterrissait toujours à la racine `articles/`, contrairement aux
séries (`articles/{scenario}/`, corrigé le 10 août) — comportement
conçu ainsi le 10 août (le correctif ne visait que les séries) mais
jamais explicité comme un choix conscient. Uniformisé sur demande de
David : `_generate_one()` (`generate.py`, fonction déjà factorisée
pour les modes simple ET "forcer" — un seul point de code couvre les
deux) fixe désormais `article_config["output"]["dossier"] =
"articles/{scenario_slug}"` avant l'appel à `build_prompt()`/
`generate_article()`. Pas de sous-dossier séparé ni d'`_index.md` créé
(ça reste spécifique aux séries).

Non-régression vérifiée sur `trace_injection.py` et
`audit_longueur_articles.py` (les deux scans d'`articles/`) : déjà
rendus récursifs le 10 août pour ce cas exact, extraient le scénario
depuis le frontmatter plutôt que le chemin — aucune modification
nécessaire.

### Rotation pondérée des journalistes par séniorité (`prompt_builder.py`, 22 août 2026)

Remplace l'ancienne sélection déterministe dans `get_journal_profile()`
("premier·ère journaliste de la zone dont `thematiques` correspond à
l'article") — figeait pour toujours le·la même journaliste sur une
thématique donnée d'une zone donnée, sans aucune variété.

**Nouvelle fonction `_select_journaliste_pondere(candidats, usage_state,
scenario_slug, namespace)`** :
- Tirage aléatoire pondéré par le champ `seniorite` de chaque
  journaliste (`journaux.yaml`) — probabilité de retour plus haute
  pour une séniorité plus élevée. Absente ou non numérique, repli sur
  `JOURNALISTE_SENIORITE_DEFAUT = 1`.
- **Garde-fou anti-oubli**, non comparatif entre journalistes
  (contrairement à la pénalité de score des instances, invalidée le
  même jour pour cette raison) : au-delà de
  `JOURNALISTE_MAX_ABSENCE_STREAK = 5` apparitions consécutives sans
  être choisi·e parmi ses occasions réelles d'éligibilité, un·e
  journaliste est sélectionné·e d'office, indépendamment de sa
  séniorité.

**État persistant** : réutilise `TRAJECTORY_STATE_FILE` (le même
fichier que la rotation des jalons), nouveau namespace
`"journalistes::{ligne}::{zone_slug}"` sous `usage_state[scenario_slug]`
— même convention de clé (`namespace` en string) que
`_select_least_used()`. Chargé/sauvegardé de façon autonome dans
`get_journal_profile()`, sans dépendre de l'état chargé par
`build_trajectory_context()` — vérifié que `build_system_prompt()` est
appelé avant `build_trajectory_context()` dans `build_prompt()`, donc
les deux sauvegardes séquentielles sur le même fichier ne s'écrasent
jamais l'une l'autre.

`dry_run` propagé (nouveau paramètre sur `get_journal_profile()` et
`build_system_prompt()`, threadé depuis `build_prompt(dry_run)`) : un
aperçu de prompt met à jour l'état en mémoire mais ne le persiste pas
sur disque — même convention que la rotation des jalons.

**Testé sur cas synthétiques** (candidat unique, aucune séniorité
définie nulle part, rotation pondérée réelle sur 200 tirages) avant
tout déploiement — non testé en conditions réelles à ce jour.

**`journaux.yaml`** : chaque entrée de la liste `journalistes` d'une
zone accepte désormais un champ optionnel `seniorite` (entier, aucune
échelle imposée — 1-5 ou 1-10 fonctionnent aussi bien). Enrichi le 22
août avec `seniorite: 1` par défaut sur les 1740 journalistes
existants (non-régression : comportement de rotation équilibrée tant
qu'aucune valeur n'est ajustée manuellement). Vérifié sans risque avec
les 3 autres scripts qui consomment ce fichier
(`check_journaux_coherence.py`, `clean_fallback_journaux.py`,
`generate_journaux.py` en mode `--update`/`--fill-journalistes`) — seul
un lancement explicite de `generate_journaux.py` sans `--update`
écraserait le champ.

### Remontée de zone niveau 1 pour la résolution du journal local (`prompt_builder.py`, 23 août 2026)

Corrige la cause racine de P25 (fiabilité de la signature journaliste,
voir `BACKLOG_MASTER_9_AOUT.md` point 10). `journaux.yaml` n'a jamais
qu'une entrée par zone **niveau 1** — déjà connu depuis le 12 août
(correctif appliqué à l'époque uniquement à la sélection manuelle
`--zone-slug` du GUI), mais jamais appliqué à la résolution automatique
de zone (`_dominant_zone()`, `snapshot.py`), qui peut retourner le
slug d'une sous-zone niveau 2/3 selon la localisation des instances
filtrées.

**Nouvelle fonction `_resoudre_zone_n1(zone_slug, scenario_slug)`** :
remonte la hiérarchie de zones (`geographie/{scenario}.md`, champ
`parent`) jusqu'à la zone niveau 1 la plus proche — même principe que
le breadcrumb `chemin` de la Carte (`app.py`,
`/api/carte/rechercher_zone`), garde-fou anti-cycle inclus. Appelée en
tout début de `get_journal_profile()`, avant toute recherche dans
`journaux.yaml` : `zone_slug` (potentiellement N2/N3) devient
`zone_slug_n1`, utilisé pour la recherche d'édition locale ET pour le
namespace de rotation des journalistes
(`_select_journaliste_pondere()`, chantier du 22 août) — une sous-zone
et sa zone N1 partagent la même rédaction, les compter séparément
aurait fragmenté le garde-fou anti-oubli.

Retourne `zone_slug` **inchangé** si déjà niveau 1, si la zone est
introuvable dans la géographie, si un cycle est détecté, ou si la
géographie du scénario n'est pas encore disponible — jamais un
comportement pire qu'avant ce correctif.

**Testé sur 6 cas synthétiques** (déjà N1, N2→N1 un saut, N3→N1 deux
sauts — reproduisant le cas réel exact documenté le 12 août
`archives_neutres_geneve`, zone inconnue, cycle, géographie absente).
**Confirmé en conditions réelles** sur 2 scénarios indépendants
(`new_sustainability`, `fortress_world`) : 100% de fiabilité de
signature sur les deux, contre ~25-33% avant ce correctif.

### Dashboard GUI récursif sur `articles/` (`routes_dashboard.py`, 23 août 2026)

`_stats_articles()` et `_stats_thematiques()` utilisaient
`articles_dir.glob("*.md")`, non récursif — cassé silencieusement par
l'uniformisation du 22 août (`generate.py` range désormais dans
`articles/{scenario}/` même en génération unitaire). Même classe de
bug déjà corrigée le 10 août pour `trace_injection.py`/
`audit_longueur_articles.py`, jamais répercutée ici : ce fichier vit
délibérément hors du flux de patches habituel sur `app.py` (extrait le
4 juillet pour cette raison précise), ce qui l'a fait passer sous le
radar. Corrigé : `glob("**/*.md")` + exclusion des `_index.md` (même
filtre qu'`audit_longueur_articles.py`).

### Variété de palette/éclairage + réutilisation des signes distinctifs dans `image_prompt` (`prompt_builder.py`, 23 août 2026)

Deux ajustements de la consigne `IMAGE_PROMPT` (bloc
`===METADONNEES_PUBLICATION===`) :
1. **Variété de palette** : ~23% des `image_prompt` déjà générés
   (30/129 mesurés) contenaient du vocabulaire bleu ("lueur bleue",
   "teintes azur"), sans qu'aucune consigne ne pousse dans cette
   direction — tic stylistique du LLM sur les scènes tech/futuristes
   de cet univers. Ligne ajoutée demandant de varier l'éclairage/la
   palette selon le contexte réel de la scène.
2. **Réutilisation des signes distinctifs** : le champ
   `signes_distinctifs` (présent sur 758/758 instances du vault) est
   déjà transmis au LLM pour chaque entité citée depuis le 3 août
   (`build_entities_context()`), mais la consigne `IMAGE_PROMPT` ne
   faisait jamais explicitement le lien vers cette section pourtant
   déjà présente dans le même prompt — probable facteur supplémentaire
   du réflexe de palette générique. Consigne réécrite pour demander
   explicitement la réutilisation des signes distinctifs déjà établis
   quand l'article porte sur une entité qui en a.

Aucun test synthétique possible (consigne de prompt, comportement
stochastique du LLM) — à vérifier sur un futur batch normal.

### Garde-fou retry pour `signes_distinctifs` manquant (`instance_generation_common.py`, 23 août 2026)

`signes_distinctifs` n'est pas un champ structurellement garanti :
suggéré dans le schéma JSON envoyé au LLM sans être marqué requis,
repli silencieux sur `""` dans `write_instance_file()` si absent,
aucune vérification dans `validate.py`. Le 758/758 actuel (100% de
couverture) est un hasard statistique favorable, pas une garantie.

**Nouvelle fonction `_retry_with_signes_distinctifs_feedback()`**,
même principe que `_retry_with_length_feedback()` (articles, 10 août) :
un seul nouvel appel LLM avec rappel explicite si le champ est vide
après le premier essai, résultat accepté quoi qu'il arrive (pas de
boucle si le 2e essai échoue aussi). Nouveau champ frontmatter
`retry_signes_distinctifs: oui/non` (même convention que
`retry_longueur` côté articles).

Testé sur 3 cas synthétiques (présent du premier coup, absent puis
récupéré, absent aux deux essais) et en conditions réelles
(non-régression du cas normal confirmée — le déclenchement effectif du
retry n'a pas pu être observé en conditions réelles, taux d'échec
naturel trop faible).

### Outillage de couverture des journalistes (23 août 2026, après-midi)

Suite du diagnostic `bassin_du_congo`/`petites_annonces_services` :
`Samira Benyahia` était la seule journaliste de sa zone à couvrir cette
thématique sur 6 — pas un bug de rotation (mécanisme du 22 août), un
trou de couverture dans les données. `audit_couverture_journalistes.py`
(nouveau) a confirmé que c'est structurel sur tout le vault : 96-98% des
combinaisons zone×thématique n'ont qu'un seul journaliste éligible sur
la plupart des scénarios — hérité de la conception d'origine de
`generate_journaux.py` ("chaque thématique couverte par au moins un·e",
jamais pensé pour permettre une rotation).

**`audit_couverture_journalistes.py`** (lecture seule) : balaie
`journaux.yaml`, signale les combinaisons à 0 (repli sur toute la liste,
rotation sans lien thématique) et à 1 (toujours le même nom) éligible.
`--report`/`-r` (même pattern que `validate.py`) écrit le détail dans un
fichier, ne laisse que le résumé en console. Chaque pourcentage est
accompagné d'une traduction qualitative en 5 paliers (de "rotation
possible partout" à "quasiment aucune rotation possible").

**`propose_couverture_journalistes.py`** (lecture seule) : pour chaque
trou, propose d'ajouter la thématique à 1-2 journalistes déjà existants
de la même zone (priorité aux moins chargés). Ne modifie jamais
`journaux.yaml` — proposition à valider manuellement, CLI uniquement.

**`inject_journaliste_custom.py`** (deux modes) :
- **Manuel** : ajoute un journaliste précis, généré par LLM cohérent
  avec le ton déjà établi de l'édition. `--nom`+`--thematiques` fournis
  ensemble = patch direct sans appel LLM ; `--nom` seul = LLM ne génère
  que les thématiques ; rien fourni = comportement d'origine. `--genre`
  oriente le LLM si le nom doit être inventé. `--seniorite` (défaut 1,
  même convention que les 1740 journalistes du 22 août).
- **Auto** : scanne un scénario (`--scenario` ou `--all` pour les 6
  d'affilée) et choisit entre redistribuer (journaliste existant sous
  `MAX_THEMATIQUES_PAR_JOURNALISTE = 6`) ou créer un nouveau profil par
  LLM si tous les existants sont au plafond.

**Testé en conditions réelles** : mode manuel confirmé de bout en bout.
Mode auto lancé une fois sur `fortress_world` : 396 redistributions +
21 créations, fragilité du scénario passée à 49% après ce seul passage
(une seule passe ne suffit pas à tout combler, la capacité de
redistribution est plafonnée). `--all` jamais testé.

**3 bugs GUI trouvés en construisant cette entrée, tous corrigés** :
- `validateRequiredFields()` (`app.js`) ne tenait jamais compte de
  `mode_only` — un champ masqué par le mode actif restait `required`,
  bloquant le lancement sur un champ invisible. Jamais rencontré avant
  (aucune entrée existante ne combinait `mode_select` et un `required`
  restreint par `mode_only`).
- Même trou dans `collectArgs()` — un champ masqué pouvait quand même
  voir sa valeur envoyée dans la commande. Corrigé par la même occasion.
- `--thematiques` : le GUI envoie les valeurs `multi_select` comme
  arguments séparés par des espaces (`nargs="+"`, convention déjà
  établie dans `inject_custom_events.py`), pas une chaîne séparée par
  virgules — corrigé après un premier échec réel.

**Dette technique notée, non traitée** : trois implémentations
indépendantes du même calcul de couverture (audit, propose, mode_auto)
— fonctionne, mais risque de maintenance si la logique change un jour.

### `STYLE_DESCRIPTIONS` + `format_fige` — deux mécanismes distincts pour `petites_annonces_services` (`prompt_builder.py`/`loader.py`, 23 août 2026)

**Important : deux correctifs indépendants**, David a explicitement
clarifié que le second n'a aucun rapport avec P21/l'oralité, malgré la
même thématique déclenchante.

**Mécanisme 1 — `STYLE_DESCRIPTIONS` (le style)** : `style_journalistique`
était envoyé au LLM comme un mot brut (`**Style** : utilitaire`), sans
indication de ce que ça doit changer concrètement dans la forme —
diagnostiqué sur `petites_annonces_services` : le LLM produisait un
mini-article journalistique classique (accroche, citations, chute), pas
une annonce de service. Rapproché par David de P21 ("Journaux oraux,
orateurs itinérants", scopé le 12 juillet, jamais codé), qui prévoyait
déjà un "registre oral" avec ses propres règles structurelles — même
niveau de détail manquant ici. Nouveau dictionnaire extensible
`STYLE_DESCRIPTIONS` plutôt qu'un correctif isolé : `utilitaire`
développé ("va à l'essentiel, pas de citation de porte-parole
nécessaire, pas de chute, ton neutre comme une annonce de service
public"), prêt à accueillir une entrée `"oral"` le jour où P21 sera codé
(reste un chantier à part entière). Tout style absent garde le mot brut
d'origine — non-régression.

**Mécanisme 2 — `format_fige` (la longueur, indépendant du premier)** :
le choix manuel de longueur dans le GUI ("analyse", 600-900 mots)
écrasait systématiquement le format naturel court de la thématique —
contradiction insoluble pour le LLM. Portée tranchée en comparant à la
presse réelle : `meteo`/`petites_annonces_services` sont de vrais genres
à forme intrinsèquement courte ; `actualites_a_la_une` volontairement
laissée flexible ("à la une" est une priorité éditoriale, pas un genre).
Nouveau champ opt-in `format_fige: true` dans le frontmatter des
thématiques concernées (même logique déclarative que `format_dominant`),
plutôt qu'une liste codée en dur. **Refactoring fait au passage** : la
logique de priorité longueur était dupliquée entre
`build_journalistic_brief()` et `build_prompt()` — même classe de bug
que celui corrigé le 3 août (`metadata["longueur"]` incohérent).
Centralisée dans `_resoudre_longueur()`, appelée par les deux.

**Bug trouvé en testant en conditions réelles — 3e occurrence du même
piège en une journée** : `format_fige: true` bien écrit sur le fichier
`.md`, mais silencieusement perdu au chargement — `load_thematique()`
(`loader.py`) reconstruit le dict d'une thématique avec une liste
blanche de champs connus, exactement comme `load_instance()` pour
`garantie_selection`/`priorite_forcee` plus tôt dans la journée.
Corrigé (`format_fige` ajouté à la liste).

**Confirmé en conditions réelles après correctif** : `petites_annonces_services`,
longueur forcée manuellement sur "analyse" (piège volontairement
reproduit) → `mots_reels: 221` (plage 200-400 correcte), format
transformé en vraie structure d'annonce (titre-annonce, "Mission :",
"Rémunération :", coordonnées de contact — plus d'accroche narrative
ni de chute). Non-régression confirmée sur `actualites_a_la_une` (non
figée) dans l'intervalle.

**Reste à faire côté vault** : ~~`thematiques/meteo.md` n'a jamais reçu
`format_fige: true` en session~~ — en fait déjà présent (ajouté par
David de son côté), fonctionnel directement une fois `loader.py`
corrigé.

**`meteo` traité en fin de session** : `style_journalistique: informatif`
(différent d'`utilitaire`) ajouté à `STYLE_DESCRIPTIONS` ("registre
factuel et condensé, priorité aux données concrètes, pas de
développement narratif, citations courtes seulement si elles apportent
une donnée précise, structure info-clé→contexte bref→recommandation
pratique — proche d'un bulletin d'agence"). Testé en synthétique puis
en conditions réelles, **validé par David**.

### P21 — Journaux oraux, orateurs itinérants (25 août 2026)

Une zone de `journaux.yaml` peut désormais être `type_diffusion: ecrit`
(défaut, non-régression), `oral`, ou `mixte` (tirage 50/50 par
article). Conception issue d'une discussion de scoping affinée le 23
août (voir backlog point 9 pour l'historique complet) : la tonalité
orale n'est **jamais** gérée par un mécanisme séparé — elle est héritée
automatiquement du `ton`/`langue_style` déjà établi de la zone, exactement
comme pour un journal écrit. Seule la **structure** change.

**`STYLE_ORAL`** (`prompt_builder.py`) : bloc structurel, délibérément
séparé de `STYLE_DESCRIPTIONS` (axe orthogonal aux styles thématiques,
pas une variante de plus dans le même dictionnaire). Couvre : adresse
directe à l'auditoire, formules d'ouverture/clôture ritualisées,
répétitions rhétoriques, pas de chapô/sous-titres, structure
accroche→développement→appel à l'action/question ouverte,
call-and-response. Ajouté **en complément** du Format/Style habituel de
la thématique dans `build_journalistic_brief()` (nouveau paramètre
`type_diffusion`), jamais en remplacement — le sujet et la profondeur
restent définis par la thématique.

**Routage** (`get_journal_profile()`) : en oral, un·e orateur·rice est
choisi·e dans `zone_data["orateurs"]` (nouvelle liste parallèle à
`journalistes`, même format `{nom, seniorite, ...}`, plus
`communautes_desservies`/`reputation_orale` optionnels) via
`_select_journaliste_pondere()` réutilisée telle quelle (générique sur
nom/seniorite), namespace de rotation distinct
`orateurs::{ligne}::{zone}`. Repli automatique sur écrit si oral
demandé mais aucun orateur défini pour la zone — jamais un
comportement pire qu'avant ce chantier.

**`build_system_prompt()` retourne désormais `(texte, profil)`** au
lieu de texte seul — nécessaire pour transmettre `type_diffusion` à
`build_journalistic_brief()` sans rappeler `get_journal_profile()` une
2e fois (qui doublerait l'incrément de rotation pondérée pour le même
article). Un seul point d'appel réel dans `build_prompt()`. Persona
adaptée ("orateur·rice itinérant·e" au lieu de "journaliste senior"),
signature reformulée (identité intégrée naturellement au discours, pas
de byline "Nom — Journal" formatée — exclue par définition du registre
oral).

**Override `type_diffusion` pour un article isolé** (`generate.py`
uniquement, jamais `generate_series.py`) : nouveau
`--type-diffusion` (`auto`/`ecrit`/`oral`/`mixte`, défaut `auto`, même
convention que `--article-longueur`). Une valeur explicite force ce
mode pour cet article précis, sans jamais modifier `journaux.yaml`. Le
garde-fou "repli écrit si aucun orateur" reste actif même avec
l'override.

**Champs frontmatter** (uniquement présents/remplis si oral, sinon
vides) :
- `type_diffusion` — toujours écrit (même `"ecrit"` par défaut)
- `duree_estimee` — calculée après génération depuis `mots_reels`
  (~140 mots/minute), jamais demandée au LLM, plancher à 1 minute
- `lieu_diffusion`/`mode_reception` — demandées au LLM dans le bloc
  `===METADONNEES_PUBLICATION===`, extraites par
  `_extract_publication_metadata()` (nouveau paramètre `type_diffusion`,
  n'attend ces deux champs que si oral)

**`journaliste_slug` assigné directement depuis le profil** (correctif
plus large que P21, déclenché par lui) : `_extract_byline()` cherchait
un format "Nom — Journal" dans les 8 premières lignes du texte — un
article oral n'en a jamais (identité intégrée dans la prose). Corrigé
en implémentant enfin l'amélioration architecturale identifiée le 23
août sur P25 : `journaliste_slug` est désormais assigné directement
depuis `prompt_data["metadata"]["journaliste"]` (le nom déjà résolu de
façon déterministe par `get_journal_profile()`), l'extraction du texte
ne servant plus qu'en repli pour le cas rare où aucun nom curaté
n'existait. Améliore la fiabilité de l'écrit au passage, pas seulement
l'oral.

**`zone_principale` corrigé** : lisait uniquement
`snapshot["zone_slug"]` (zone auto-calculée), ignorant tout choix de
zone manuel — alors que `get_journal_profile()` priorise déjà le choix
manuel depuis le 11 juillet (bug #26). Bug du 21 août (P20 Phase B),
révélé par le premier test oral réel (contenu clairement africain,
`zone_principale` affichant une zone eurasienne). Même priorité que
`build_prompt()` désormais : `config.get("zone_slug") or
snapshot.get("zone_slug")`.

**Testé en conditions réelles** (25 août, `breakdown`/`pro_pouvoir`/
`afrique_centrale_australe`) : orateur correctement sélectionné,
adresse directe fidèle à la consigne, deux vrais call-and-response,
aucun chapô/sous-titre, structure respectée. Point non corrigé, mineur :
le LLM ajoute parfois quand même une signature formatée en toute fin de
texte malgré la consigne contraire (sans impact sur `journaliste_slug`
depuis le correctif ci-dessus).

### Suite du 26 août — plafond de longueur, champ "forcer un intervenant", crash critique corrigé

**`MOTS_MAX_ORAL = 700`** (5 min × 140 mots/minute, retour de David
après le premier test réel jugé trop long à 8 minutes) : nouveau
plafond dans `_resoudre_longueur()`, appliqué **après** toute la
logique existante (override manuel, `format_fige`) — un discours de
meeting a une contrainte physique de temps de parole qu'aucune
thématique/override écrit ne peut lever. Garde-fou sur le cas limite
où la borne basse dépasserait la borne haute après plafonnement.

**Crash critique trouvé et corrigé** : le correctif `zone_principale`
du 25 août tentait de lire `config.get("zone_slug")` directement dans
`build_article_md()`, qui **n'a jamais reçu `config` en paramètre**
(seul `save_article()`, son appelant, l'a) — `NameError` sur **toute**
génération d'article, écrit ou oral. Corrigé : `save_article()`
calcule la valeur et la dépose dans
`prompt_data["metadata"]["zone_principale_resolue"]` avant d'appeler
`build_article_md()`, qui la lit comme tout autre champ du bloc.

**Nouveau champ GUI "Forcer un intervenant précis"** : liste
déroulante des journalistes/orateurs éligibles pour la zone/ligne/mode
choisis (mélangés si mode mixte/auto). `app.py` : nouvelle branche
`intervenants_eligibles` dans `get_slugs()` +
`_scan_intervenants_eligibles()` (lecture directe de `journaux.yaml`,
même pattern que `_zones_avec_journal()`). **Aucune modification
`app.js` nécessaire** — le mécanisme `slug_extra_params` (rechargement
automatique dès qu'un champ surveillé change) était déjà générique.
`prompt_builder.py` : nouveau paramètre `intervenant_override` sur
`get_journal_profile()` — le nom choisi détermine le mode implicitement
(un choix d'orateur force l'oral même en mode "Auto"), réutilise
`_select_journaliste_pondere()` filtrée à cette seule personne pour
garder le comptage d'usage cohérent. `generate.py` : nouveau
`--intervenant`, jamais sur `generate_series.py`.

**Bug trouvé en marge** : le nouveau champ n'avait pas de `mode_only`
— apparaissait aussi en mode "Forcer" du GUI, où `--zone-slug` (son
champ dépendant) n'existe pas. Corrigé (`mode_only: "semi_guide"`).

**Suite du 26 août, après-midi** — 3 retours de David sur le champ
"Forcer un intervenant précis", tous confirmés fonctionnels en
conditions réelles :
1. Distinction visuelle journaliste/orateur dans la liste mélangée
   (mode auto/mixte) : `_scan_intervenants_eligibles()` retourne
   `(noms, labels)` — `labels` affiche `"Nom (journaliste)"`/`"Nom
   (orateur)"` dans le menu, mais la **valeur soumise reste le nom
   exact sans suffixe** (mécanisme `data.labels` déjà supporté par
   `app.js`, aucune modification JS nécessaire).
2. **Filtrage par thématique** : la liste ne filtrait pas les
   journalistes par thématique, contrairement à `get_journal_profile()`
   au moment réel de la génération — corrigé, même logique de filtrage
   + même repli sur la liste complète si aucun·e journaliste ne
   correspond. Les orateurs restent non filtrés (pas de notion de
   spécialité pour eux). Nouveau paramètre `thematique` dans
   `slug_extra_params` — le champ se recharge désormais sur 4 critères
   (ligne, zone, mode, thématique).
3. Bug trouvé en marge (doublon accidentel de fonction introduit par
   un correctif précédent dans la même session) — nettoyé.

**Constat en marge, non lié à P21** : 53 doublons de nom complet entre
journalistes `pro_pouvoir`/`opposition` d'une même zone, sur 145 zones
concernées (~28%) — problème hérité de la génération d'origine de
`journaux.yaml`. Corrigé le 29 août via `fix_doublons_journalistes.py`
(renommage semi-automatisé par LLM, toujours côté opposition, avec
validation anti-collision et sauvegarde horodatée automatique) — 53/53
réussis en 2 passes, 2 bugs trouvés et corrigés en cours de route (le
retry ne couvrait que les collisions de nom, jamais les échecs de
parsing JSON ; cause des échecs de parsing identifiée — guillemets
ASCII internes pour un surnom, cassant le JSON strict).

### `ton_personnel` — nuance personnelle par journaliste/orateur (29 août 2026)

Nouveau champ opt-in, unifié pour journalistes ET orateurs (pas de
distinction `ton_personnel`/`style_rhetorique` — David a préféré un
seul nom, ce dernier hérité du scoping P21 du 12 juillet mais jamais
branché avant aujourd'hui). Ajoute une nuance de style **personnelle**
à une personne précise, **en complément** du ton déjà établi de sa
zone/édition — jamais en remplacement. Absent par défaut sur toutes
les entrées existantes de `journaux.yaml` : aucune régression, le
paragraphe supplémentaire n'apparaît dans le prompt que si ce champ
est explicitement rempli pour la personne réellement sélectionnée.

**Mécanisme** (`prompt_builder.py`) : `get_journal_profile()` recherche
`ton_personnel` uniquement sur la personne sélectionnée par la
rotation (ou par `intervenant_override`), jamais sur tout le vivier de
la zone. `build_system_prompt()` ajoute un paragraphe conditionnel
après l'identité éditoriale, explicitement encadré : *"à exprimer EN
COHÉRENCE avec le ton éditorial ci-dessus, jamais en contradiction"*.

**Nouvel outil `set_ton_personnel.py`** (génère ou fixe directement la
valeur) :
- `--nom "Nom exact"` : une seule personne précise (journaliste ou
  orateur·rice, cherché dans les deux listes de la zone)
- `--all-manquants` : tout le monde dans une zone sans `ton_personnel`
  encore (journalistes + orateurs confondus)
- `--ton-personnel "..."` : valeur donnée directement, aucun appel LLM
- `--overwrite` : requis pour remplacer une valeur déjà écrite (sinon
  ignorée, jamais écrasée par erreur)
- Sauvegarde horodatée automatique avant toute écriture (même
  principe que `fix_doublons_journalistes.py`)

**Consigne LLM affinée sur 3 allers-retours de test réel, chacun ayant
révélé un problème concret** :
1. **Anti-répétition + anti-stéréotype** : le tout premier essai
   contenait des citations verbatim entre guillemets simples
   (`'lois divines'`) ET dérivait vers un stéréotype culturel
   contemporain (métaphore de machette/soldat sur une zone
   centrafricaine, alors que 2098 est un monde qui a eu 70 ans pour
   évoluer différemment du nôtre). Consignes ajoutées : jamais de
   citation verbatim, jamais de métaphore de violence/guerre, jamais
   d'ancrage dans des clichés culturels/ethniques/religieux
   contemporains — sauf si le `ton` déjà établi de la zone les
   intègre déjà explicitement (worldbuilding existant à suivre, pas à
   enrichir de soi-même).
2. **Bug de détection trouvé** : le garde-fou anti-guillemets ne
   vérifiait que `«»`/`"`, jamais les guillemets simples ASCII — qui
   servent aussi aux apostrophes normales du français (`l'urgence`,
   `j'ai`). Corrigé avec un motif exigeant une PAIRE de guillemets
   simples entourant 3 caractères ou plus (`'[\w\s]{3,40}'`), sans
   faux positif sur une contraction isolée.
3. **Longueur non maîtrisée par la seule consigne textuelle** : "25
   mots maximum" en prose n'a pas suffi (~42 mots obtenus dans les
   faits) — leçon générale : un LLM respecte peu fiablement une
   contrainte numérique donnée uniquement en instruction. Double
   verrou ajouté : `max_tokens` réduit de 200 à 90 (plafond technique,
   pas juste une consigne) + validation explicite du nombre de mots
   après coup avec un retry si plus de 35 (tolérance, pas de retry
   pour un dépassement mineur).

**Confirmé en conditions réelles, les 3 points simultanément** après
les 3 correctifs cumulés : aucune citation, métaphore neutre
(artisanat/forgeron, pas de violence), longueur maîtrisée (~27 mots).

**Piste de suivi non traitée** (retour de David) : les métaphores
littéraires ("cadence de forgeron") pourraient être moins fiables à
interpréter concrètement pour un LLM que des descripteurs directifs
(sarcastique, sec, hésitant, confrontant...) — l'image doit d'abord
être "traduite" en choix stylistiques par le LLM, contrairement à un
descripteur qui s'applique directement. À tester empiriquement ou à
retravailler la consigne pour privilégier le descriptif concret,
la métaphore restant un bonus optionnel plutôt que le cœur de la
réponse. Reporté, non traité le 29 août.

### P20 — Enrichissement frontmatter pour publication web, Phase A (21 août 2026)

Relance du chantier scopé le 12 juillet (voir `BACKLOG_CONSOLIDE.md`
dans `documentation/Old/` pour le scoping d'origine complet — 12 champs
répartis en 3 phases lors de la reprise : A codable sans nouvelle
décision, B bloquée sur décision, C explicitement hors scope tant que
`generate_images.py` n'existe pas).

**Phase A — 7 champs livrés** : `slug`, `chapo`, `image_prompt`, `tags`,
`a_une_photo`, `journaliste_slug`, `date_evenement`.

**Bloc `===METADONNEES_PUBLICATION===`** (`chapo`/`tags`/`image_prompt`) :
demandé au LLM dans le **même appel** que l'article (Option 1 actée le
12 juillet — cohérence garantie avec le contenu, pas de second appel).
Consigne ajoutée en fin de `build_journalistic_brief()`
(`prompt_builder.py`), remontée dans les "Contraintes impératives" après
un premier test (voir plus bas). Côté `api.py`, nouvelle fonction
`_extract_publication_metadata()` : extrait et **retire** le bloc du
texte **avant** tout comptage de mots (`_count_words()`) — sinon le
bloc aurait faussé la mesure de longueur et le déclenchement du retry
(chantier du 10 août). Extraction appliquée aussi bien au premier essai
qu'au retry (`_retry_with_length_feedback()` modifiée pour retourner le
triplet `(article, wc, meta)` au lieu de `(article, wc)`). Non
bloquant par construction : bloc absent ou champ manquant → warning
`[api] [WARN]`, champ(s) laissé(s) vide(s), jamais d'échec de
génération.

**`journaliste_slug`** : extrait de la signature réelle du corps de
l'article (`_extract_byline()`, regex sur les 8 premières lignes non
vides — position garantie sous la date depuis le correctif du 10 août)
plutôt que du profil édition locale pré-calculé (`get_journal_profile()`),
qui peut être vide si le LLM invente son propre nom (chemins 2/3,
réseau global/profils hardcodés). Tolère un habillage Markdown gras
optionnel autour de la ligne (`**Nom — Journal**`) — ajouté après un
test réel où ce format est apparu. Slug produit par `_slugify()`,
copie exacte de la fonction du même nom dans `create_entity.py` (NFD +
suppression des marques diacritiques, cf. correctif du 14 août sur les
slugs portugais cassés).

**`slug`** (de l'article) : dérivé du titre réel via `_extract_title()`
(première ligne en gras de l'article) + `_slugify()`, tronqué à 80
caractères.

**`date_evenement`** : la date fictive (`config["article"]["date_fictive"]`)
était déjà calculée à chaque génération mais seulement utilisée pour le
nom de fichier (`build_article_filename()`), jamais persistée dans le
frontmatter — `save_article()` modifiée pour la calculer une seule fois
et la transmettre aux deux (`build_article_filename()` ET
`build_article_md()`, nouveau paramètre `date_fictive`).

**`a_une_photo`** : `false` par défaut, bascule manuelle plus tard
(choix éditorial, pas systématique — décision du 12 juillet).

**`_yaml_escape()`** : nouvelle fonction, échappement minimal (guillemets,
deux-points, retours à la ligne) pour insérer du texte libre (`chapo`,
`image_prompt`) dans le frontmatter construit à la main par
`build_article_md()` (pas de dumper YAML) — les champs pré-existants
étaient tous des valeurs contrôlées (slugs, enums, nombres), ces deux
champs sont les premiers à contenir du texte libre.

**Testé sur 2 batches réels de 8 articles (`fortress_world`)** :

| Champ | Batch 1 | Batch 2 (après correctifs) |
|---|---|---|
| `slug`/`date_evenement`/`a_une_photo` | 8/8 | 8/8 |
| Bloc métadonnées (chapo/tags/image) | 6/8 | **8/8** |
| `journaliste_slug` | 4/8 | 5/8 |

Bloc métadonnées : passage de la consigne en contrainte impérative a
suffi (même traitement que la longueur le 10 août). `journaliste_slug` :
un bug réel corrigé entre les deux batches (regex ne gérait pas le
format gras — corrigé, testé sur le cas réel exact) ; le reste des cas
vides relève d'un problème de fond côté LLM (signature omise ou
mal positionnée), pas d'un bug d'extraction — voir P25 ci-dessous,
ouvert séparément plutôt que traité comme faisant partie de ce chantier.

**Phase A considérée close.** Phase B (`zone_principale`, `date_publication`,
`articles_lies`) reste ouverte, décisions à trancher avant tout code —
voir `BACKLOG_MASTER_9_AOUT.md` Partie 1 point 9.

**Fichiers livrés** : `api.py` (7 nouvelles fonctions :
`_slugify()`, `_yaml_escape()`, `_extract_publication_metadata()`,
`_extract_byline()`, `_extract_title()`, plus `build_article_md()`/
`save_article()`/`generate_article()`/`_retry_with_length_feedback()`
modifiées), `prompt_builder.py` (consigne du bloc métadonnées +
renforcement de la consigne signature dans `build_journalistic_brief()`).

### P25 — Fiabilité de la signature journaliste dans le corps de l'article (21 août 2026, nouveau chantier ouvert)

Découvert en marge de P20 Phase A : le nouveau champ `journaliste_slug`
dépend de l'extraction de la signature depuis le corps de l'article, ce
qui a rendu visible pour la première fois un problème de fond
préexistant sur la consigne de signature du 10 août 2026 ("apparaît
TOUJOURS, immédiatement sous la date"), jusqu'ici jamais mesuré faute
d'un mécanisme qui en dépendait réellement.

**Mesuré sur 2 batches réels de 8 articles, avant et après renforcement
de la consigne** (passage en contrainte impérative "TOUJOURS, SANS
EXCEPTION...") : taux de signature manquante inchangé, environ 25%
(2/8 puis 2/8) — le renforcement n'a pas suffi à lui seul. Un troisième
symptôme apparu seulement au 2e batch : signature présente mais
mal positionnée (fin d'article plutôt que sous la date), avec un format
à 3 parties inattendu ("Nom — Organisation — Journal") plutôt que le
format à 2 parties attendu.

**Décision, comme P17/Bug#27** : observer sur un futur batch de volume
plutôt que sur-corriger sur un échantillon de 16 articles au total
(temperature 1.0, forte variance, deux batches de 8 restent
statistiquement faibles). `_extract_byline()` reste volontairement
limité aux 8 premières lignes de l'article — élargir la recherche pour
chasser aussi le cas "signature en fin d'article" augmenterait le
risque de faux positifs sur un tiret cadratin en dialogue/citation,
pour un problème qui relève d'abord de la consigne, pas de
l'extraction.

**Non codé plus avant** — voir `BACKLOG_MASTER_9_AOUT.md` Partie 1
point 10 pour le suivi.

---

### P20 — Phases B et C, GUI, et débogage réel (21 août 2026, soir)

Poursuite de séance après la clôture initiale du 21 août — P20 était
resté sur "Phase A close, B/C ouvertes". Les deux phases restantes ont
été codées dans la foulée, avant un cycle de débogage en conditions
réelles avec David qui a révélé plusieurs points nouveaux (voir plus
bas).

**Phase B — codée.** Trois décisions tranchées rapidement en
s'appuyant sur du code déjà existant plutôt qu'en inventant un nouveau
mécanisme :
- `zone_principale` réutilise `snapshot["zone_slug"]`, déjà calculé par
  `_dominant_zone()` (`snapshot.py`, vote majoritaire sur
  `localisation.zone` des `filtered_instances`) et déjà utilisé pour
  choisir le journal/journaliste de zone (`prompt_builder.py`) — même
  valeur, pas de second mécanisme. Vide si `zone_slug` est `None`
  (aucune instance localisée dans `filtered_instances`).
- `date_publication` = `date_evenement` pour l'instant — aucun délai
  éditorial simulé (le pipeline ne modélise qu'une seule date). Champs
  gardés séparés dans le frontmatter (pas fusionnés) pour ne pas fermer
  la porte à un vrai décalage éditorial plus tard sans migration de
  schéma.
- `entites_citees` : liste des slugs de `filtered_instances`, sous-
  produit gratuit qui prépare le futur script de rapprochement
  `articles_lies` (non fait — le vrai calcul de similarité entre
  articles reste un chantier séparé, décidé mais pas scopé).

**Phase C — codée, `generate_images.py` (nouveau script).** Traite les
articles `a_une_photo: true` selon `image_credit` :
- `IA_generated` → appelle `_generate_image_via_api()` (voir plus bas —
  stub, aucun service branché) ;
- `personnel`/`autre` → pose un placeholder neutre
  (`images/_placeholder_en_attente_manuel.svg`), en attente d'upload
  manuel par David ;
- vide → ignoré, rien à faire tant que la décision n'est pas prise.

Convention de chemin actée : `images/{scenario}/{slug}.png` (le `slug`
déjà présent en frontmatter, pas re-dérivé). Patch ciblé du frontmatter
(même pattern que `fix_annee_debut_placeholder.py` — ne touche que
`image_principale`/`image_alt`, rien d'autre). Deux placeholders SVG
neutres créés, visuellement distincts (teintes différentes) : un pour
"attend un upload manuel" (`_placeholder_en_attente_manuel.svg`), un
pour "attend le branchement du service IA"
(`_placeholder_en_attente_generation.svg`) — ce dernier est
spécifiquement reconnu par le script comme "encore à faire" (pas
"déjà fait"), donc un nouveau run après branchement du vrai service
retraite automatiquement tous les articles concernés, sans `--force`.

**`_generate_image_via_api()` — décision explicite de David : reportée.**
Claude/Anthropic n'a pas d'API de génération d'image native (vérifié
par recherche web avant de coder) — un service tiers est nécessaire
(OpenAI/Stability/Google Imagen/autre, non choisi). Point d'intégration
générique déjà prêt (signature stable : prompt en entrée, chemin de
sortie, retourne True/False), à brancher le jour venu sans toucher au
reste du script.

**`image_alt` — dérivé d'`image_prompt`, pas de second appel LLM.**
Décision actée après discussion avec David sur la convention des
journaux en ligne réels : l'`alt` décrit l'image (pas l'article, déjà
le rôle de `chapo`), le crédit s'affiche séparément (légende, pas fusionné
dans l'`alt` — question de rendu HTML remise à plus tard). Garde-fou de
troncature ajouté après une remarque de David sur le risque de dépasser
"quelques mots" : `_truncate_alt()`, deux temps — (1) ne garde que la
PREMIÈRE phrase complète si le LLM en a produit plusieurs malgré la
consigne "en une phrase" (cible directement le vrai risque observé
ailleurs aujourd'hui : bloc métadonnées, signature, pas toujours
respectées à la lettre) ; (2) repli seulement si cette phrase unique
dépasse 180 caractères, troncature au dernier espace avec ellipse —
jamais en plein mot. Testé sur 5 cas dont les deux qui comptent : LLM
multi-phrases (garde la 1ère, propre) et phrase unique trop longue
(troncature au mot).

**Consigne `image_prompt` renforcée** après remarque de David :
l'image doit refléter le sujet réel de l'article, pas rester
systématiquement neutre — si l'article porte principalement sur une
personne/entité/lieu nommé précis, l'`image_prompt` doit la représenter
explicitement (nom/rôle mentionné), sinon rester une description de
scène neutre (lieu/ambiance/éléments clés). Non testé en conditions
réelles au moment du correctif — premier batch réel après ce changement
(voir plus bas) montre un comportement globalement correct sur des
articles centrés sur un lieu/système plutôt qu'une personne, avec un
cas limite noté (rôle mentionné, nom absent — voir plus bas).

**GUI — décision manuelle dès l'écriture de l'article, pas seulement
après coup.** Deux nouveaux champs sur l'écran "Générer un article"
(semi-guidé ET forcer, sans restriction de mode) : "Aura une image"
(case à cocher, décochée par défaut → `a_une_photo`) et "Crédit image"
(menu déroulant, vide par défaut → `image_credit`, ignoré si la case
n'est pas cochée). Câblés une seule fois dans `generate.py`
(`config["article"]` est partagé par les deux modes, donc un seul point
de câblage couvre les deux). Sur l'écran série
(`generate_series.py`/`config_series.yaml`), nouveau champ "Illustration
des articles" : Aucune / Toutes / Aléatoire (25%, probabilité actée
avec David) — décision par article, indépendante de `ligne_editoriale`
qui peut être fixe pour toute la série. `image_credit` reste toujours
vide en mode série même quand `a_une_photo` devient `true` via la
politique — décision explicite de David, la source se choisit par
article, plus tard, avant `generate_images.py`.

Côté `api.py` : `build_article_md()`/`save_article()` acceptent
désormais `a_une_photo`/`image_credit` en paramètres au lieu de les
figer en dur (`false`/`""`) — non-régression testée (config sans ces
clés → comportement identique à avant ce changement).

**Fichiers livrés (Phase B/C + GUI)** : `api.py`, `generate_images.py`
(nouveau), `generate.py`, `generate_series.py`, `prompt_builder.py`
(consigne `image_prompt`), `scripts_config.json` (2 champs
`generate.py`, 1 champ `generate_series.py`), 2 SVG placeholders dans
`images/` (nouveau dossier, à créer manuellement avec les 2 fichiers —
les sous-dossiers par scénario se créent automatiquement).

#### Débogage en conditions réelles (21 août, soir)

**Piège de redémarrage Flask, nouveau cas concret.** Après avoir généré
une série avec la politique "Toutes" sélectionnée à l'écran,
`a_une_photo: false` sur les 3 articles produits. Diagnostic :
`config_series.yaml` ne contenait pas la clé `photo_policy` du tout —
confirmé en inspectant le fichier directement. Cause : Flask n'avait
pas été redémarré après la livraison du nouveau `scripts_config.json`,
donc le formulaire du navigateur ne connaissait pas encore le champ
"Illustration des articles". Vérifié que ce n'est pas un bug de code :
`app.js::buildYamlFormPanel()` construit le formulaire de façon
générique depuis `config_fields` (aucune whitelist figée par champ à
mettre à jour), et `generate_series.py` lit correctement
`config.get("photo_policy", "aucune")` depuis tout `config_series.yaml`
chargé (`load_config()` fait un simple `yaml.safe_load()` sans
filtrage). Résolu après redémarrage de Flask, confirmé par David — même
piège que celui documenté le 15 août sur `loader.py`, reconfirmé ici
sur un nouveau fichier.

**P25, nouveau symptôme observé.** Sur le batch de 3 articles
`policy_reform` (généré après redémarrage Flask) : 1/3 signature
correcte et bien extraite, 1/3 signature présente mais repoussée en
toute fin d'article, précédée d'un séparateur `---` (comme si le LLM la
traitait comme une note de bas de page plutôt qu'un en-tête malgré la
consigne de position), 1/3 sans aucune signature. Voir
`BACKLOG_MASTER_9_AOUT.md` Partie 1 point 10 pour le suivi — décision
inchangée d'observer avant de corriger, avec une piste concrète notée
pour la prochaine session (détection du pattern `---` en fin de texte).

**Vocabulaire des tags — décision actée, rien codé.** David a repéré
que chaque article invente ses propres tags sans jamais réutiliser ceux
d'un article précédent — comportement de la consigne Phase A, jamais
explicitement discuté avec David (un choix d'implémentation, pas une
décision commune). Comparaison avec la pratique réelle des rédactions
en ligne : ni vocabulaire libre indéfiniment, ni taxonomie fermée
définie à l'avance — accumulation progressive, réutilisation
prioritaire suggérée au moment de la publication, nettoyage périodique
des quasi-doublons. **Décision (Option C, hybride)** : un vocabulaire
qui s'auto-construit depuis le corpus existant (script à écrire),
injecté dans la consigne du prompt pour encourager la réutilisation
plutôt que l'invention systématique — possibilité de figer en taxonomie
fermée plus tard si le vocabulaire semble stable. Rien codé — voir
`BACKLOG_MASTER_9_AOUT.md` Partie 1 point 11.

**Rétro-application sur les articles existants — nouveau besoin,
demandé explicitement par David en toute fin de séance.** Deux cas
distincts à couvrir avec un même chantier à scoper : les articles
antérieurs à P20 (aucun des nouveaux champs frontmatter n'existe), et
les articles générés le 21 août avant certains correctifs de cours de
route (consigne `image_prompt`, futur vocabulaire de tags). Rien scopé
en détail — probable script type `enrich_minimal.py` pour les champs
dépendant du contenu (`chapo`/`tags`/`image_prompt`, ré-appel LLM sans
retoucher le texte publié), traitement mécanique pour les champs
dérivables sans LLM (`slug`, `date_evenement`). Voir
`BACKLOG_MASTER_9_AOUT.md` Partie 1 point 12.

**Séance interrompue en plein débogage** — reprise prévue le lendemain,
voir `HANDOFF_21_AOUT.md` section "soir" pour le point de reprise
complet.

*(En pratique, la séance a repris dans la foulée le soir même — voir
sections suivantes.)*

---

### `rapprocher_articles.py` — articles_lies + vocabulaire des tags (21 août 2026, soir)

Backlog Partie 1 point 9bis. `articles_lies` (resté en jachère depuis
la Phase B de P20 -- seul champ jamais calculé de tout le chantier) et
le vocabulaire de tags (David : chaque article inventait ses propres
tags sans jamais réutiliser ceux d'un article précédent, comportement
de la consigne Phase A jamais explicitement décidé) reposent sur le
même mécanisme de fond -- un rapprochement entre articles par
recoupement. Conçus et codés ensemble.

**Comparaison avec la pratique réelle des rédactions en ligne**
(discutée avec David avant de coder) : les tags remplissent plusieurs
fonctions distinctes dans la presse en ligne -- navigation/découverte
pour le lecteur, pages thématiques qui agrègent automatiquement les
articles liés à un sujet filé dans le temps, base du "articles liés"/
recommandation (deux tags partagés entre deux articles = signal de
lien), SEO, et usage éditorial interne (retrouver ce qui a déjà été
écrit sur un sujet). Aucune rédaction ne fige une taxonomie à l'avance
ni ne laisse un vocabulaire totalement libre indéfiniment -- accumulation
progressive, réutilisation suggérée en priorité, nettoyage périodique
des quasi-doublons. Distinction claire entre *rubriques* (peu
nombreuses, contrôlées -- déjà `thematique`) et *tags* (nombreux,
souples mais pas anarchiques). **Décision (Option C, hybride)** : un
vocabulaire qui s'auto-construit depuis le corpus existant plutôt
qu'une taxonomie pré-écrite, avec possibilité de figer plus tard si le
vocabulaire semble stable.

**Ce que fait le script** :
1. Construit/rafraîchit `generator/tags_reference.yaml` (fréquence
   d'usage de chaque tag déjà vu dans `articles/*.md`, triés
   décroissant).
2. Calcule `articles_lies` par score pondéré : `3 × |entités
   partagées| + 1 × |tags partagées|` (ratio 3:1 acté avec David --
   une entité nommée partagée est un signal plus spécifique et plus
   fort qu'un tag générique partagé). **Restreint strictement au même
   scénario** -- les 6 scénarios sont des futurs alternatifs séparés,
   un rapprochement cross-scénario n'aurait aucun sens narratif. Top 3
   retenus par article.
3. Met à jour une ligne `**Voir aussi**` en wikilinks Obsidian
   (`[[slug]]`) en fin de corps de chaque article traité, combinant
   `entites_citees` (déjà présent depuis la génération, Phase B) +
   `articles_lies` (calculé ici), dédoublonné. Idempotent -- une ligne
   déjà présente est remplacée, jamais dupliquée sur une relance.

**Découverte utile en cours de route, sans lien direct avec le calcul
d'`articles_lies` lui-même** : David a demandé s'il existait un outil
d'analyse de contenu plus complet, citant la vue graphique d'Obsidian
en exemple. Vérification faite sur les fiches `entites/*.md`
existantes : leurs wikilinks vivent dans le **corps** du document
(un tableau en bas de fiche), jamais dans le frontmatter -- confirmé
que la vue graphique d'Obsidian ne suit que les liens du corps. Les
articles générés n'avaient jusqu'ici aucun wikilink nulle part
(`entites_citees` en frontmatter est du texte brut, invisible pour le
graphe). La ligne "Voir aussi" comble ce manque directement -- Obsidian
devient utilisable pour explorer visuellement le corpus sans outil
supplémentaire à construire. Ajouté aussi côté génération native
(`api.py::build_article_md()`, avec seulement `entites_citees` au
moment de la génération -- `articles_lies` n'existe pas encore à ce
stade, complété par ce script après coup).

**`prompt_builder.py`** : nouvelle fonction `_load_tags_suggeres()`,
charge `tags_reference.yaml` (absent avant le premier passage du
script -- retourne `[]` sans erreur), plafonné à 50 tags par fréquence
décroissante. La consigne `TAGS` du prompt les injecte et demande une
réutilisation prioritaire, sans obligation -- le LLM reste libre
d'inventer un tag pertinent absent de la liste.

**Mode `--stats`** (diagnostic pur, aucune écriture) : fréquence de
chaque entité **par scénario** (pas en absolu -- un scénario avec plus
d'articles fausserait sinon la comparaison), alerte
`QUASI-OMNIPRÉSENTE` au-delà de 40% des articles du scénario. Conçu
pour répondre à la demande de David de "détecter un biais non voulu de
génération", pas seulement pour diagnostiquer le calcul de liens.

**Découverte réelle avec `--stats`, sur un tout petit échantillon (7
articles seulement, 2 scénarios)** : `gelecek_meclisi_{scenario}`
présente à 100% sur `breakdown` (3/3) et `policy_reform` (4/4).
Investigation menée avant de conclure à un bug : lecture des fiches
instance de `gelecek_meclisi` sur les deux scénarios -- `variables_
influencees` délibérément large (gouvernance_institutions, valeurs_
culture_tempo_sociale, technologie_information, organisation_
territoires -- des variables très génériques qui recoupent quasiment
toute thématique), `zone_geographique: continentale/globale`. Pas un
artefact aléatoire : `filter_instances_for_thematique()` la favorise
structurellement par la formule de score elle-même, et la rotation à
mémoire (`_select_least_used_instances()`, ajoutée le 2 août
précisément pour éviter ce genre de skew) ne peut la départager que si
son score reste dans le même panier que d'autres candidates -- pas si
elle domine systématiquement. **Décision de David : observer sur un
corpus plus large avant de trancher** -- 7 articles est un échantillon
trop faible pour juger si c'est un vrai problème de diversité
narrative ou une caractéristique voulue (institution "tissu conjonctif"
du monde, cohérente avec son rôle narratif décrit dans sa fiche). Même
philosophie que P17/Bug#27/P25 : ne pas sur-corriger avant d'avoir de
vraies données.

**Testé intégralement sur corpus synthétique** avant tout usage réel :
rapprochement trouvé/absent selon recoupement, séparation stricte par
scénario confirmée (entités/tags identiques sur un autre scénario ne
créent jamais de lien), ligne "Voir aussi" combinée et idempotente sur
relance (pas de duplication), `--stats` avec une entité artificiellement
rendue omniprésente correctement détectée à 100%.

#### Lancé sur le corpus complet (71 articles) — l'hypothèse `gelecek_meclisi` invalidée, un constat plus large confirmé

**Dry-run sur les 71 articles exploitables** (tout le corpus, après
clôture du point 12) : 262 tags distincts pour 357 usages cumulés
(réutilisation encore faible -- attendu, ces tags datent tous d'avant
la consigne de réutilisation) ; 70/71 articles avec au moins un lien
trouvé, regroupements cohérents à l'examen (clusters Genève-Nexus/
gouvernance algorithmique, Amazonie/santé/longévité, les deux
doublons quasi-identiques "Bruxelles-Forteresse" bien liés entre eux).

**`gelecek_meclisi` : hypothèse de la veille invalidée par le vrai
volume.** Sur 71 articles, `breakdown` 30% et `policy_reform` 33% --
sous le seuil de 40% dans les deux cas. L'omniprésence à 100% observée
sur l'échantillon de 7 articles était bien un artefact de petit
échantillon, pas un signal réel -- validation nette de la décision
d'observer avant de corriger.

**Mais le mécanisme structurel soupçonné existe bien, en plus large que
prévu.** Sur `--stats` exécuté sur les 71 articles, le même mécanisme
(spectre `variables_influencees`/`zone_systemique` large favorisant
certaines instances dans `filter_instances_for_thematique()`) touche
**plusieurs entités différentes, sur 5 des 6 scénarios** :
`consortium_africain_de_biotechnologies_sociales` (jusqu'à 57%),
`reseau_mnemos` (jusqu'à 62%), `directive_kontinuum` (jusqu'à 58%),
`bureau_gouvernance_algorithmique` (48%), `trame_mnemos_noeud_reseau`
(50%), et d'autres. Un pattern de fond, pas un cas isolé.

**Point notable, non exploré plus avant** : deux des entités
récurrentes sont des **personnes** (`leena_vainala` jusqu'à 42%,
`amara_diallo_nkosi` 42%), pas des institutions à spectre large --
un mécanisme de récurrence potentiellement différent (source/
commentatrice citée souvent dans les articles plutôt qu'un score de
pertinence thématique structurellement élevé). Mériterait un
diagnostic séparé de celui des institutions.

**Bug repéré dans `--stats`, non corrigé** : aucun seuil minimum
d'articles avant l'affichage de l'alerte `QUASI-OMNIPRÉSENTE` -- sur
`new_sustainability` (1 seul article exploitable dans tout le
scénario), **toutes** ses entités s'affichent mécaniquement à "100%",
un artefact du calcul sur un échantillon d'1 article, pas un vrai
signal. Faussement alarmant si lu sans ce contexte.

**Décision de fin de séance** : le constat, passé du statut "point
d'observation isolé sur une seule entité" à "pattern structurel avéré
sur la majorité des scénarios", est documenté pour discussion à la
prochaine session plutôt que qualifié ou corrigé dans l'immédiat --
trancher entre défaut à corriger, caractéristique voulue de certaines
entités "tissu conjonctif" du monde, ou distinction institutions/
personnes mérite une vraie session dédiée, pas un correctif réflexe en
fin de journée. Voir `BACKLOG_MASTER_9_AOUT.md` Partie 1 point 9bis.

**Point en suspens à vérifier en ouverture de la prochaine session** :
l'exécution réelle (sans `--dry-run`) de `rapprocher_articles.py` a été
demandée à David mais n'apparaît pas explicitement confirmée dans
l'historique de la session -- `--stats` fonctionne indépendamment sur
les `entites_citees`/`tags` déjà présents en frontmatter (pas sur
`articles_lies` lui-même), donc son succès ne prouve pas que le run
réel a eu lieu. À confirmer : `generator/tags_reference.yaml`
existe-t-il sur le vault réel, et le frontmatter des articles
contient-il bien un `articles_lies` rempli ?

**Fichiers livrés** : `rapprocher_articles.py` (nouveau), `api.py`
(section "Voir aussi" ajoutée à `build_article_md()`), `prompt_builder.py`
(`_load_tags_suggeres()` + consigne TAGS enrichie).

---

### `enrich_articles_pre_p20.py` — rétro-application sur les articles existants (21 août 2026, soir)

Backlog Partie 1 point 12, **clos le soir même de son ouverture** --
contrairement à l'anticipation initiale ("à scoper demain"). David a
demandé la portée la plus large possible (tout le corpus pré-P20 d'un
coup) et une approximation plutôt qu'un abandon pour les deux champs
dépendant du snapshot au moment de la génération (`zone_principale`/
`entites_citees`, données qui n'existent plus après coup).

**Trois niveaux de récupération, traités différemment** :

1. **Mécanique** (sans LLM, réutilise les fonctions déjà testées
   d'`api.py` -- aucune duplication de logique) : `slug` (`_extract_
   title()` + `_slugify()`), `journaliste_slug` (`_extract_byline()`
   + `_slugify()`), `date_evenement`/`date_publication` (extraits du
   corps -- délibérément PAS reconstruits depuis le nom de fichier,
   dont le suffixe est translittéré sans accents et non fiable à
   re-décoder), `a_une_photo`/`image_credit` (défauts, décisions
   manuelles par nature, rien à récupérer).

2. **Approximation** (sans LLM, décision explicite de David) :
   `entites_citees` par recoupement du corps de l'article contre le
   nom de chaque entité connue du scénario (`instances/*_{scenario}.md`,
   champ `name`, correspondance insensible à la casse sur la partie
   avant un éventuel tiret cadratin de sous-titre) ; `zone_principale`
   par vote majoritaire sur `localisation.zone` des entités approximées
   (même principe que `_dominant_zone()` dans `snapshot.py`, appliqué
   après coup). **Limite assumée et testée** : une entité mentionnée
   pour dire qu'elle n'est *pas* concernée est quand même détectée --
   la correspondance texte ne comprend pas la négation, seulement la
   présence du nom.

3. **LLM** (un seul appel par article) : réutilise le même format de
   bloc que la génération normale (`===METADONNEES_PUBLICATION===`),
   parsé par `_extract_publication_metadata()` importée d'`api.py` sans
   dupliquer le parsing -- `chapo`/`tags`/`image_prompt`, plus un **4ᵉ
   champ ajouté en cours de route, `JOURNALISTE`**. Repéré par David :
   le regex mécanique confondait parfois un nom d'institution/lieu avec
   un nom de personne (ex. réel : "Bratislava Secteur Alpha" capté
   comme signature). Problème de sens, pas de motif -- aucune règle
   mécanique supplémentaire ne pouvait le résoudre de façon fiable.
   Solution : demander au LLM, qui lit déjà l'article complet pour les
   3 autres champs, de trancher lui-même si la signature est une vraie
   personne. Coût marginal nul (appel déjà fait). En mode `--skip-llm`
   (aperçu gratuit), repli sur l'extraction mécanique uniquement --
   les deux sources ne sont jamais mélangées pour un même champ.

**Bugs réels trouvés et corrigés au fil des tests, tous vérifiés avant
d'affecter le run réel sur 56 articles** :
- **Slugs dupliqués** : `_extract_title()` retombe sur la première
  ligne non vide quand aucune ligne en gras n'est trouvée (articles
  antérieurs à la convention "titre toujours en gras") -- ce repli est
  parfois une dateline plutôt qu'un vrai titre, produisant deux fois le
  même slug sur deux articles différents ("Bruxelles-Forteresse, 12
  octobre 2098" comme "titre" sur deux fichiers distincts). Corrigé par
  désambiguïsation mécanique (suffixe numérique incrémental sur
  collision), `used_slugs` amorcé avec les slugs déjà en usage sur tout
  le vault (pas seulement entre les articles du lot en cours) pour
  éviter une collision avec un article déjà P20 natif.
- **Préfixe "Par"/"By"** capturé avec le nom de journaliste par le
  regex de signature (ex. "Par Elias Mwangi — Journal") -- retiré avant
  slugification.
- **Regex interne de `_extract_publication_metadata()` sensible à la
  casse** (`CHAPO:` strict, pas `Chapo:`/`chapo:`) -- diagnostiqué sur
  un cas réel (bloc trouvé mais aucun des 3 champs internes reconnu),
  corrigé en `re.IGNORECASE`. **Correctif partagé avec la génération
  live**, pas seulement ce script, puisque `_extract_publication_
  metadata()` vit dans `api.py`.
- **Piège identifié et bloqué avant qu'il ne se produise** : lancer
  `--skip-llm` pour de vrai (sans `--dry-run`) aurait posé un `slug` sur
  chaque article traité -- le critère de détection du script ("pas de
  slug = à traiter") les aurait ensuite exclus définitivement d'un
  futur passage complet, laissant `chapo`/`tags`/`image_prompt` vides
  pour toujours sans aucun avertissement. Combinaison refusée
  activement par le script (message d'erreur explicite en plus de
  l'avertissement dans la docstring), pas seulement déconseillée en
  commentaire.
- **Regex de date, deux élargissements successifs** : (1) tolérance
  gras/italique autour de la ligne (`*17 janvier 2098*`) ; (2) recherche
  du motif *dans* la ligne plutôt que sur la ligne entière, découvert
  sur le tout premier format du projet (juin 2026) où la date est
  combinée au lieu sur une même ligne en gras ("**Bratislava-Secteur
  Alpha — 9 novembre 2098**") -- format bien antérieur à la convention
  stabilisée mi-août (titre en `#` plutôt que `**`, byline en "*Par X,
  descripteur*" sans tiret cadratin vers un journal).

**Exécution réelle complète** : 56/56 articles pré-P20 traités, 3
avertissements initiaux (bloc métadonnées vide -- corrigé par le
correctif de casse ci-dessus, confirmé sur un nouveau test avant la
vraie exécution).

**Mode `--audit` ajouté après coup** (diagnostic pur, aucune écriture),
demandé par David pour "mettre au propre" avant de considérer le
chantier terminé -- trois vérifications : rangement racine/sous-
dossier, `date_evenement` vide, `chapo` vide.

**Découverte annexe via l'audit -- rangement incohérent du corpus
historique.** 44 des 56 articles étaient posés directement à la racine
de `articles/` plutôt que dans un sous-dossier par scénario (convention
différente avant un certain point du projet -- `config["output"]
["dossier"]` ne pointait pas toujours vers un sous-dossier).
`rapprocher_articles.py` ET `enrich_articles_pre_p20.py` ne balayaient
jusque-là que les sous-dossiers (`articles/{scenario}/*.md`), ratant
silencieusement ces 44 fichiers. **Corrigé dans les deux scripts** :
`_iter_all_article_files()` balaie désormais racine ET sous-dossiers,
et le scénario est lu depuis le frontmatter (`fm.get("scenario")`,
toujours présent, ancien comme nouveau format) plutôt que déduit de
l'emplacement physique du fichier -- source de vérité unique et fiable.
Nouveau mode `--reorganize` : déplace les fichiers mal rangés vers leur
sous-dossier, gère les collisions (refuse d'écraser) et les scénarios
manquants (ignore proprement) sans planter. Lancé en réel : 44/44
déplacés sans collision.

**Deux modes de rattrapage ciblé ajoutés après l'audit**, pour ne
retraiter que ce qui manquait sans retoucher les champs déjà bons :
- `--retry-empty-date` (mécanique, gratuit -- relance uniquement
  `extract_date_from_body()` avec le regex élargi) : 26/29 dates
  récupérées.
- `--retry-empty-chapo` (LLM, ne retouche que chapo/tags/image_prompt/
  journaliste_slug) : 3/3 récupérés après le correctif de casse.

**3 dates résiduelles irrécupérables mécaniquement**, diagnostiquées
individuellement en lisant le corps réel de chaque article :
- Année tronquée à 3 chiffres dans le texte lui-même ("298" au lieu de
  "2098", coquille de génération de juillet, pas un bug de ce script)
  -- David corrige à la main plutôt que deviner automatiquement la
  valeur voulue.
- Date en portugais ("12 de novembro de 2098", cohérent avec un article
  au style volontairement lusophone) -- format supplémentaire non
  couvert, un seul article concerné, jugé pas assez rentable à coder
  pour un cas unique.
- Calendrier fictif propre à la narration d'un article ("Le 14 de
  l'Eau Profonde, 2098") -- pas une vraie date calendaire, aucun regex
  ne peut l'interpréter, nécessiterait une compréhension sémantique du
  texte. 2 des 3 cas corrigés à la main par David en cours de route, 1
  laissé vide (le calendrier fictif, sans correspondance réelle
  possible).

**Découverte annexe supplémentaire, sans lien avec ce chantier** : sur
`lynth_lieu_encommande.md` (`breakdown`), la date écrite dans le corps
par le LLM à la génération (14 novembre 2098) ne correspond pas à la
date demandée au moment de la génération, visible dans le nom de
fichier ("3janvier2098") -- écart préexistant de juillet 2026, invisible
jusqu'ici faute d'un champ qui en dépendait réellement. **Décision** :
la date extraite du texte publié fait foi pour `date_evenement` (c'est
ce que le lecteur voit réellement dans l'article), pas celle du nom de
fichier (simple horodatage technique de génération, jamais montré au
lecteur).

**Audit final, après toutes les étapes** : 0 fichier à la racine, 1
date vide (le cas calendrier fictif, accepté comme irrécupérable),
0 chapo vide.

**Décision de fond actée en cours de route** : face à la question de
David ("ne vaudrait-il pas mieux supprimer et régénérer tout le corpus
pré-P20 plutôt que le rattraper"), analyse du compromis présentée --
la régénération remplace les récits déjà écrits par des articles
différents sur les mêmes sujets (coût de régénération nettement
supérieur à un simple appel de rattrapage de métadonnées, et le
pipeline continuant d'évoluer, un corpus "regénéré aujourd'hui"
deviendrait lui-même daté à la prochaine évolution -- il n'existe pas
de point d'arrêt naturel où tout serait "à jour pour toujours"). David
a choisi de conserver le rattrapage, qui préserve le contenu narratif
existant en ne touchant qu'aux métadonnées.

**Fichiers livrés** : `enrich_articles_pre_p20.py` (nouveau, 4 modes :
défaut, `--audit`, `--reorganize`, `--retry-empty-date`,
`--retry-empty-chapo` -- 5 en comptant le défaut), `api.py` (regex
`_extract_publication_metadata()` corrigé en `re.IGNORECASE`, partagé
avec la génération live).

### P21 — Outillage de création des orateur·rices, mode `convertir`, `--avec-ton-personnel` (29 août 2026, suite)

Suite du chantier `ton_personnel` du 29 août (matin) — voir addendum
ci-dessus. L'après-midi a porté sur les points restants de P21 :
absence d'outil de création dédié aux orateur·rices, et test du mode
`mixte` en conditions réelles (jamais fait au-delà du synthétique).

**Nouvel outil `inject_orateur_custom.py`**, contrepartie de
`inject_journaliste_custom.py`. Conçu sur le même patron (import
`load_journaux()`/`save_journaux()`/`parse_geographie()`, sauvegarde
horodatée avant écriture — absente de `inject_journaliste_custom.py`
du 23 août, ajoutée ici pour rester cohérent avec la pratique la plus
récente). Deux différences structurelles assumées avec les
journalistes : pas de `thematiques` (jamais filtré par spécialité), et
le mode auto ne cible que les zones **déjà** oral/mixte (créer des
orateur·rices sur une zone écrite les laisserait inutilisé·es).

**Mode manuel** : premier test réel a révélé un bug de consigne —
`communautes_desservies` généré en phrases narratives de 16+ mots avec
proposition relative (*"Les jardins flottants de Nador, où les serres
hydroponiques s'accrochent aux épaves des pétroliers échoués"*) au
lieu des locutions courtes réelles du vault (*"villages du fleuve"*,
2-3 mots). Root cause : la consigne demandait *"1 à 3 groupes/lieux
concrets"* sans contrainte de longueur ni exemple de format — même
famille de dérive que les autres garde-fous du projet. Corrigé par
double verrou : consigne renforcée avec les vraies locutions du vault
comme ancrage de registre + limite explicite (5-6 mots visés) + retry
technique si un item dépasse 9 mots de tolérance. Confirmé corrigé sur
un second test réel (items descendus à 3-4 mots chacun).

**Mode auto** : `--scenario` toujours requis, **délibérément aucun**
`--all` multi-scénarios (contrairement aux journalistes) — décision de
David, les orateurs sont opt-in par zone via `type_diffusion`, un
balayage aveugle sur les 6 scénarios créerait des orateur·rices sur
des zones jamais pensées pour l'oral. Effectif cible par défaut : 2
(décision de David, "2 orateurs mini"). Premier test réel : message de
résumé "0 création" ambigu, ne distinguait pas "aucune zone oral/mixte
trouvée" de "toutes les zones oral/mixte sont déjà à l'effectif cible"
— corrigé en trackant les deux causes séparément (`zones_eligibles`
vs `zones_deja_cible`), résumé désormais précis et actionnable (liste
les zones oral/mixte trouvées nommément).

**Discussion de conception, mode auto vs conversion de zones** : David
a proposé que le mode auto bascule aussi `type_diffusion` sur des
zones encore en `ecrit`, en plus de créer des orateur·rices. Refusé
tel quel : sur ~90 zones × 2 lignes par scénario, une seule commande
aurait pu convertir des dizaines de zones d'un coup sans validation
individuelle — alors que `type_diffusion: oral` n'existe aujourd'hui
que sur 2 zones dans tout le vault, chacune choisie à la main avec une
intention narrative précise (ex. langue construite `kholus` sur
`afrique_centrale_australe`). Risque identifié : coût LLM non borné,
choix `oral` vs `mixte` arbitraire par zone, perte de la curation
éditoriale. **Solution retenue** : nouveau mode `--mode convertir`,
qui bascule `type_diffusion` ET crée les orateur·rices manquant·es,
mais **uniquement sur une liste explicite de zones** fournie par
l'utilisateur (`--zones ligne::zone_slug ...`) — jamais un balayage
automatique.

**Câblage GUI du mode convertir** : David a demandé un multi-select
dans le GUI, peuplé par les zones candidates (celles sans oral/mixte)
pour un scénario donné. Vérification préalable : aucun champ
`multi_select` existant dans `scripts_config.json` n'était alimenté
dynamiquement (tous en `choices` statiques) — mais `dynamic_multi_select`
existait déjà (ajouté le 2 août pour `--forcer-scenarios`) et couvrait
exactement le besoin (chips cochables, rechargement au changement de
scénario, collecte générique via `data-multi-flag` dans `collectArgs()`).
**Aucune modification `app.js` nécessaire.** Côté backend, nouvelle
fonction `_zones_candidates_oral()` (`app.py`), même pattern de
lecture directe de `journaux.yaml` que `_zones_avec_journal()`/
`_scan_intervenants_eligibles()` — retourne un `slug` composite
`"{ligne}::{zone_slug}"` (nécessaire car le même `zone_slug` peut
exister sous les deux lignes avec un statut `type_diffusion`
différent), plus des `labels` lisibles pour l'affichage des chips.
Branché sur `GET /api/slugs?type=zones_candidates_oral`. Testé en
conditions réelles (fonctionnel avec des données factices avant
livraison, puis confirmé par David en conditions réelles).

**Bug latent trouvé dans `inject_journaliste_custom.py`** (fichier du
23 août, jamais rencontré avant) : en testant la création manuelle
d'un journaliste, le LLM a retourné des thématiques hors de la liste
fermée `THEMATIQUES_CONNUES` (*"gestion des citernes d'eau potable"*,
*"épidémies insulaires"*, et une variante accentuée `"santé"` au lieu
du slug exact `"sante"`) — le filtre strict
(`t in THEMATIQUES_CONNUES`) a alors vidé silencieusement la liste, et
l'ancien code (un seul essai, aucun retry) échouait sec. Corrigé par
double verrou : consigne renforcée (interdiction explicite d'inventer,
rappel du format slug exact sans accent/majuscule) + retry technique
(2 tentatives) dans `_generer_journaliste()` — bénéficie
automatiquement aux modes manuel et auto (même fonction, deux points
d'appel).

**`--avec-ton-personnel`** ajouté aux deux outils de création
(journaliste et orateur), en réutilisant directement
`_generer_ton_personnel()`/`_contexte_specifique()` de
`set_ton_personnel.py` (import, pas de logique dupliquée). Question de
David : pourquoi pas systématique à chaque création ? Réponse : le
champ est délibérément rare/opt-in (jamais utilisé en masse même sur
les 1740+ journalistes existants), et packer deux consignes LLM dans
le même flux de création augmenterait le risque de dérive silencieuse
sans le filet de relecture individuelle. **Décision : disponible en
mode manuel uniquement, jamais en mode auto ou convertir** — la
relecture individuelle du mode manuel est précisément le point de
contrôle qui a permis de repérer les 3 dérives réelles de ce champ le
26-29 août (citations, stéréotypes, longueur).

**Test du mode `mixte` en conditions réelles** (6 articles générés sur
`eco_communalism`/`maghreb_mediterraneen`) : tirage confirmé non figé
(1 `oral` / 5 `ecrit`), plafond `MOTS_MAX_ORAL` respecté (658 mots),
`journaliste_slug` bien résolu (`lalla_nsara_tidewhisper`).
`STYLE_ORAL` très bien suivi sur le fond : adresse directe constante,
répétitions rhétoriques délibérées (*"Silence sur... Silence sur...
Silence, surtout, sur..."*), **call-and-response réussi et explicite**
(*"Répondez-moi : L'eau est à qui ? — À nous !"*), clôture en question
ouverte plutôt qu'une chute qui referme le sujet. **Un problème
confirmé, mais accepté** : signature formatée résiduelle (`Nom —
Journal`) malgré la consigne contraire — observée ici en tête de
texte (juste sous la date), alors que le point ouvert du backlog la
documentait seulement "en fin d'article". Root cause probable :
la consigne anti-signature (`build_system_prompt()`) est formulée
dans le contexte de l'ouverture (*"fais savoir qui tu es... dans les
premières phrases"*), le LLM peut la lire comme scopée au début plutôt
qu'au texte entier. **David a jugé le résultat acceptable pour les
articles oraux — pas de correctif prévu.**

**Fichiers livrés/modifiés** : `inject_orateur_custom.py` (nouveau, 3
modes), `inject_journaliste_custom.py` (`--avec-ton-personnel`, bug
thématiques corrigé), `app.py` (`_zones_candidates_oral()`, branchement
`get_slugs()`), `scripts_config.json` (entrée "Ajouter des orateurs",
mode convertir, `--avec-ton-personnel` sur les deux outils de
création).

**P21 potentiellement clôturable** : les 4 points restants du backlog
(entité orateur, outil de création LLM, test mode mixte réel,
signature résiduelle) sont tous traités ou actés comme acceptables au
29 août. À confirmer et déplacer vers l'archive du backlog à la
prochaine session.
