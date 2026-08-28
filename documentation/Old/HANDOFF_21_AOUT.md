# Handoff — session du 21 août 2026

*Session menée via chat avec Claude (aucun accès direct GUI/terminal côté
Claude), David exécutant les commandes/scripts sur son vault et
rapportant les résultats, plus deux uploads du vault complet (zip) et
d'un batch d'articles test (zip) permettant une exploration directe du
code et du contenu réel côté Claude au fil de la session.*

## 0. Point de départ — reprise du backlog du 19 août

Backlog Partie 1 : point 1 (validation retry longueur, 🟡), points 3 à 9
en attente, dont le point 9 nouvellement ouvert le 19 août (P22, bloc
`simulation`, décision d'architecture non tranchée).

## 1. Chantier retry longueur — clos, `audit_longueur_articles.py` v4

Le point 1 du backlog demandait un échantillon plus large que les 12
articles testés le 10 août pour mesurer fiablement le taux de réussite
du mécanisme de retry. Script étendu en v4 : nouvelle section qui
recalcule la déviation exacte (`deviation_ratio()`, copie de
`_deviation_ratio()` côté `api.py`) plutôt que de se contenter d'un
"dans la plage ou non", exclut proprement les articles antérieurs au
10 août (pas de champ `retry_longueur` dans leur frontmatter — hors
périmètre du mécanisme), et croise déviation recalculée avec
`retry_longueur` déclaré pour détecter deux anomalies possibles (retry
manquant, retry insuffisant).

**Résultat sur le vault réel** : 56 articles scannés, 25 post-mécanisme,
4 retries déclenchés, **0 anomalie, taux de succès 100% (4/4)**. Les 3
seuls articles dépassant réellement 40% d'écart dataient tous de fin
juin/début juillet — antérieurs au mécanisme, pas des échecs de
celui-ci. Chantier clos.

## 2. Ménage du vault — 5 catégories traitées

David a fourni le zip complet du vault (72 Mo décompressés) pour
exploration directe. Audit catégorie par catégorie, validation de
David avant chaque action :

- **Fixtures de test confirmées** : 5 événements de test
  (`zone_valide_test`, `zone_invalide_test`, `multi_scenario_zone_test`,
  `escalade_sahel_2028_test`, `controle_date_lointaine_test`) retirés
  via `undo_custom.py --type event --generalisation yes` (outil déjà
  existant, dry-run puis exécution réelle), `validate.py` confirmé à
  0 erreur/0 avertissement après coup. 3 `.bak` orphelins de
  `test_undo_event` (événement déjà supprimé avant cette session) et
  `entites_custom/queue_a_regarder.yaml` ("Test Requeue Debug", non
  référencé par aucun script) supprimés à la main par David.
- **Fichiers isolés à la racine** : `diag_slug.py` (debug ad hoc du 17
  août, obsolète depuis `audit_instances_manquantes.py`),
  `europe_occidentale_reconstituee.md` (0 octet, orphelin, coïncidence
  de nom avec une vraie zone géographique sans rapport),
  `generator.zip` (copie redondante du dossier `generator/` déjà en
  clair) — supprimés à la main.
- **Fichiers système/IDE** : 18 `.DS_Store`, 2 `__pycache__`, 2
  `.code-workspace` mal placés (`gui/`, `evenements_custom/`) supprimés ;
  `.gitignore` enrichi (`.DS_Store`, `__pycache__/`, `*.pyc`).
- **Purge `.bak` de plus de 30 jours** : 367 fichiers (4,6 Mo)
  supprimés après confirmation que David commite régulièrement sur Git
  (historique déjà capturé séparément par les commits).
- **Archives zip redondantes** : `variables/Archive.zip`,
  `documentation/Old/Archive.zip`, `documentation/Old/Archive 2.zip` —
  vérifiées fichier par fichier (100% de recoupement avec le contenu
  déjà présent en clair) puis supprimées.

**Laissé de côté volontairement** : les 34 doublons `*copie*` de
`documentation/Old/` — archive historique intentionnelle, utile aux
recherches `grep` passées (ex. retrouver "Le Cartographe Silencieux"
le 17 août) — pas touché sans décision explicite future.

## 3. Découverte — P22 déjà codé le 20 août, session sans handoff

En explorant `documentation/need_action/` (répertoire de sortie des
scripts de diagnostic), un fichier détonnait du reste :
`snapshot_ORIGINAL_avant_P22.py`, daté du 20 août 16h53 — une
sauvegarde manuelle prise juste avant une modification réelle de
`snapshot.py`. Diff avec le `snapshot.py` actuel : 199 lignes,
implémentation complète et aboutie du chantier P22 (voir backlog du 19
août, point 9) — alors que ce point était encore listé comme "rien
codé" dans le backlog de référence de cette session.

**David confirme** : une session a bien eu lieu le 20 août, sans
handoff rédigé sur le moment. Contenu et statut (validé/fonctionnel)
confirmés a posteriori. P22 est donc en réalité **clos depuis le 20
août** — trou de traçabilité comblé rétroactivement ici. Voir
`USER_MANUAL_COMPLET.md` (nouvelle section dédiée) pour le détail
complet du mécanisme (`volatility`/`tipping_point_risk`/
`systemic_criticality` rendus opérationnels dans `snapshot.py`, avec
logique de non-régression).

## 4. Résolution du risque structurel Partie 3 — `loader.py`

Risque identifié le 3 août, jamais rencontré en pratique jusqu'ici :
une instance custom voit toujours ses deltas de variables appliqués
(`apply_custom_injections()` dans `snapshot.py`, liste non filtrée),
mais sa description ne parvient au LLM que si elle survit au même
filtrage par pertinence thématique qu'une instance du socle
(`filter_instances_for_thematique()`, plafond `MAX_INSTANCES=6`).
David comptant injecter une instance custom prochainement, décision de
corriger préventivement plutôt que d'attendre de l'observer en réel.

**Nouvelle fonction partagée `_select_with_custom_guarantee()`** :
garantit une place à toute instance custom dans `filtered_instances`,
même à score nul ; emplacements restants disputés par les non-custom
via la rotation à mémoire existante, inchangée. Non-régression garantie
par construction (sans instance custom, comportement strictement
identique à avant) — testée sur 6 cas synthétiques, tous passent.
**Non testé en conditions réelles** (vault toujours à zéro instance
custom) — à confirmer à la prochaine injection réelle, via les logs
`[loader] Instance(s) custom garantie(s)...`.

## 5. Relance de P20 (frontmatter publication web) — Phase A codée et testée

Chantier scopé le 12 juillet, en pause depuis, relancé à la demande de
David. Redécoupé en 3 phases pour distinguer le codable sans nouvelle
décision (A) du bloqué sur décision (B) et du hors scope explicite (C,
images — dépend d'un futur `generate_images.py` non conçu).

**Phase A livrée** : 7 champs (`slug`, `chapo`, `image_prompt`, `tags`,
`a_une_photo`, `journaliste_slug`, `date_evenement`). Bloc
`===METADONNEES_PUBLICATION===` demandé au LLM dans le même appel que
l'article (Option 1 actée le 12 juillet), extrait et retiré du texte
AVANT tout comptage de mots pour ne pas fausser le retry longueur du 10
août. `journaliste_slug` extrait de la signature réelle du corps de
l'article plutôt que du profil pré-calculé (peut être vide si le LLM
invente son propre nom).

**Testé sur 2 batches réels de 8 articles (`fortress_world`, fournis par
David via upload zip)** :
- Batch 1 : bloc métadonnées 6/8, `journaliste_slug` 4/8. Diagnostic
  détaillé de chaque trou : signature en gras non reconnue par le regex
  (bug réel, corrigé), bloc métadonnées omis par le LLM sur 2
  générations, signature totalement absente du texte sur 2 générations.
- Correctifs appliqués entre les deux batches : regex signature tolère
  désormais un habillage gras optionnel ; consigne du bloc métadonnées
  et de la signature remontées dans les "Contraintes impératives" du
  prompt (même traitement que la longueur le 10 août).
- Batch 2 : bloc métadonnées **8/8** (problème résolu), `journaliste_slug`
  5/8 — taux de signature manquante inchangé (~25%), plus un nouveau
  symptôme (signature présente mais mal positionnée en fin d'article,
  format à 3 parties inattendu).

**Phase A considérée close.** Phase B (`zone_principale`,
`date_publication`, `articles_lies`) reste ouverte — voir backlog
Partie 1 point 9.

## 6. Nouveau chantier ouvert — P25, fiabilité de la signature journaliste

Découvert en marge de P20 : la consigne de signature du 10 août
("apparaît TOUJOURS") n'est pas fiable à ~75% sur les deux batches
testés, taux inchangé malgré son renforcement en contrainte impérative.
Décision, comme P17/Bug#27 : observer sur un futur batch de volume
avant de sur-corriger sur un échantillon de seulement 16 articles.
`_extract_byline()` reste volontairement limité aux 8 premières lignes
de l'article — pas élargi pour chasser le cas "signature en fin
d'article", qui relève d'abord d'un problème de consigne LLM, pas
d'extraction.

## 7. Fichiers livrés cette session

- `audit_longueur_articles.py` (v4 — section retry, `deviation_ratio()`,
  `RETRY_DEVIATION_THRESHOLD`).
- `loader.py` (nouvelle fonction `_select_with_custom_guarantee()`,
  `filter_instances_for_thematique()` et `select_instances_by_impact()`
  réécrites pour l'utiliser).
- `api.py` (P20 Phase A — `_slugify()`, `_yaml_escape()`,
  `_extract_publication_metadata()`, `_extract_byline()`,
  `_extract_title()`, `build_article_md()`/`save_article()`/
  `generate_article()`/`_retry_with_length_feedback()` modifiées).
- `prompt_builder.py` (consigne du bloc métadonnées + renforcement de
  la consigne signature dans `build_journalistic_brief()`).
- `BACKLOG_MASTER_9_AOUT.md` (mis à jour en place — voir ci-dessous).
- `USER_MANUAL_COMPLET.md` (5 nouvelles sections en fin de fichier).
- Suppressions manuelles côté vault (voir §2) — aucun fichier de contenu
  livré, uniquement des suppressions.

**Redémarrage Flask requis** (changements dans `loader.py`/`api.py`/
`prompt_builder.py` — piège déjà rencontré par le passé, cf. session du
15 août).

## 8. Mise à jour du backlog

`BACKLOG_MASTER_9_AOUT.md` mis à jour en place (convention du projet,
jamais recréé sous un nouveau nom) :
- **Point 1** (retry longueur) : clos, basculé en Partie 4.
- **Point 9** (P22) : clos, basculé en Partie 4. Partie 2 nettoyée en
  conséquence (bloc `simulation` n'est plus "jamais utilisé").
- **Partie 3** (risque instances custom) : résolu, basculé en Partie 4,
  section vidée.
- **Nouveau point 9** (remplace l'ancien, numérotation réutilisée) :
  P20, 🟡, Phase A close/Phases B-C ouvertes — sorti du groupement
  "pause longue durée" du point 7 puisqu'activement travaillé.
- **Nouveau point 10** : P25 (fiabilité signature), ⚪, observation en
  cours.
- Point 7 (chantiers de fond) : ne contient plus que P21/P14 — P20 en
  est sorti.
- Ancien bloc de récapitulatif de fin de fichier (obsolète, dupliquait
  du contenu déjà capturé dans le tableau Partie 4) retiré, remplacé
  par une note de reprise courte et à jour.

## 9. Point de reprise suggéré pour la prochaine session

Rien d'urgent laissé en suspens de façon bloquante. Priorités
suggérées, sans ordre imposé :
- **P25** (fiabilité signature) : observer sur le prochain batch de
  volume généré pour d'autres raisons, pas de test dédié à provoquer.
- **P20 Phase B** : trancher `zone_principale` (dérivation depuis
  `filtered_instances`/`zone_systemique` ou nouveau champ LLM ?),
  `date_publication` (sens exact face à `date_evenement`), `articles_lies`
  (mécanique de rapprochement par entités partagées) avant tout code.
- **Garantie instances custom** (`loader.py`) : confirmer en conditions
  réelles à la prochaine injection d'une instance custom.
- Reste inchangé en Partie 1 : points 3 (P17), 4 (Bug #27), 5
  (renommage YAML), 6 (troncatures JSON), 8 (intégration GUI
  `promote_ville.py`), 7 (P21/P14, pause longue durée) — tous en
  attente sur décision explicite de David.
