# Handoff — 5 septembre 2026

Session consacrée au chantier "Suite narrative des événements" (les
articles ne construisent aucune continuité narrative sur les
événements custom, ils repartent d'une fiche statique à chaque
génération), scopé par David en 4 points (A/B/C/D), puis extension
vers un nouveau chantier "détection de basculements narratifs".
Chantier NON clos — points C/D restent à faire, le process de suite
("Promouvoir un événement" pour un candidat de basculement) a une
limite non résolue.

## Fait

**Point A — champ `evenements_cites`, prospectif**
- `api.py::build_article_md()` : écrit `evenements_cites` +
  `evenements_cites_source: generation` quand `forcer_resolu["type"]
  == "evenement"` — déterministe, aucun appel LLM, garanti par
  `forced_angle_directive` (snapshot.py).
- Testé en conditions réelles : article forcé sur
  `accord_carbone_amazonie_blocs_new_sustainability`, champ bien
  rempli.

**Rattrapage rétroactif — tenté puis ABANDONNÉ**
- Nouveau script `detect_evenements_cites_retroactif.py`, 3
  itérations de critère avant abandon :
  - v1 (vocabulaire seul du slug) : 65/74 faux positifs
    (new_sustainability) — vocabulaire trop générique à cet univers.
  - v2 (acteur OU année) : 69/74 — les acteurs sont un pool
    d'institutions récurrent, partagé par presque tous les articles.
  - v3 (acteur ET année, intersection) : 16/74 candidats raisonnables
    → passage LLM ("sujet ou fait significatif") : 7/16 confirmés,
    mais vérification manuelle a trouvé un faux positif (citation en
    exemple, pas développée) → consigne resserrée à "SUJET CENTRAL" →
    0/16 (new_sustainability), 0/7 (eco_communalism, où le match
    "certain" nom-exact avait aussi une faille — corrigé pour passer
    aussi par la vérification LLM).
- Conclusion testée sur 2 scénarios (95 articles au total) : **aucun
  article ancien** ne développe un événement comme sujet central,
  seulement en toile de fond/précédent/exemple. Décision de David :
  ne pas tester les 4 scénarios restants, pattern jugé net.
  Conséquence : les 206 articles déjà publiés ne nourriront jamais
  `developpements`, seuls les forçages futurs le pourront.
- Outil de debug annexe : `debug_test_evenement_central.py` (verdict +
  justification par candidat) — a aussi révélé que le LLM peut
  halluciner des slugs d'événements plausibles à partir du texte au
  lieu de juger les candidats fournis, quand la liste n'est pas
  pré-filtrée. Corrigé par validation stricte des slugs retournés.

**Point B — outil d'audit par sujet, construit et testé**
- `audit_sujets.py` (lecture seule) : `--list-evenements` (catalogue
  par scénario, trié chronologiquement sur le champ `date` numérique)
  et audit d'un sujet (événement ou entité) toutes dates confondues,
  avec signal `POSTÉRIEUR AU MOIS DE PARUTION ACTIF`.
- `editer_sujets.py` (destructif, gardé-fous) : suppression d'article
  → déplacement vers `_corbeille/{scenario}/` horodatée (jamais de
  rm), modification de `date_evenement` → sauvegarde préalable dans
  `_backups/` + renommage du fichier cohérent (fragment de date sans
  accent) + synchronisation conditionnelle de `date_publication`.
  Tout derrière `--apply`/`--dry-run`, journal append-only
  `_corbeille/journal_actions.jsonl`.
- Intégration GUI : onglet "Audit par sujet" (section entités-
  création) + nouvel onglet top-level **"Articles"** (demandé par
  David, même gabarit que "Rédaction" : table triable/filtrable/
  paginée sur tout l'inventaire, filtrage 100% client, panneau de
  détail avec les mêmes actions Supprimer/Modifier-date). 6 nouvelles
  routes Flask (`/api/sujets/evenements`, `/api/sujets/audit`,
  `/api/sujets/supprimer_article`, `/api/sujets/modifier_date`,
  `/api/sujets/inventaire`, `/api/articles/liste`).
- Testé en conditions réelles par David : audit (occurrence unique
  retrouvée après un forçage), suppression réelle, modification de
  date réelle avec renommage, onglet Articles de bout en bout
  (filtres, tri, panneau, actions).

**Nouvel outil `audit_inventaire_articles.py`**
- Inventaire complet lecture seule (tous scénarios) : résumé
  (total/par scénario/par ligne/par thématique/avec événement forcé/
  dates non reconnues) + détail. Export `--md` (natif vault,
  `documentation/inventaire_articles.md`, recommandé) et `--csv`
  (secondaire). Confirmé cohérent avec le dashboard existant (211
  articles, mêmes répartitions).

**Nouveau chantier "détection de basculements narratifs"**
- Motivé par : aucune donnée structurée gratuite n'existe pour
  détecter un basculement (`tension_level`/`scenario_state` confirmés
  STATIQUES par scénario dans `loader.py::load_scenario()`, jamais
  recalculés par article ; `variables_pilotes` ne liste que des noms,
  jamais de niveau).
- Scope tranché avec David : tout le corpus (200+ articles), chapo
  seul (pas le corps complet), rapport simple à parcourir à la main
  (pas de création automatique d'événement).
- Nouvel outil `detect_basculements_narratifs.py` : **un seul appel
  LLM par scénario** (tous les chapos triés chronologiquement dans un
  même prompt), catégories aggravation/amelioration/deblocage/
  blocage/emergence_crise/autre, même garde-fou anti-hallucination de
  fichier que le script de rattrapage.
- Testé sur new_sustainability (73 articles, 1 appel LLM) : 10
  candidats/73, justifications cohérentes avec le lore réel, mais
  aucun amelioration/blocage détecté — biais du scénario ou du LLM,
  pas encore tranché. Pas encore vérifié manuellement contre le texte
  intégral, pas encore testé sur un 2e scénario.

## Bugs trouvés/corrigés

- `_llm_confirm_events()` (rattrapage) : le LLM peut inventer des
  slugs d'événements hors de la liste de candidats fournie — corrigé
  par validation stricte des slugs retournés (déjà présente dans le
  script principal, ajoutée aussi à l'outil de debug annexe).
- Deux fois pendant l'intégration GUI, un edit sur `app.py` a
  accidentellement supprimé le décorateur `@app.route(...)` de
  `/api/redaction/personnes` (fonction toujours définie mais plus
  exposée comme route) — repéré les deux fois en comparant le nombre
  de routes/fonctions avant/après chaque lot de modifications,
  corrigé immédiatement.
- `audit_sujets.py` : le catalogue d'événements (`--list-evenements`)
  était trié alphabétiquement par nom de fichier au lieu de
  chronologiquement — corrigé en triant sur le champ `date` numérique
  de chaque fiche événement (`date_label`, texte libre à granularité
  variable — saison/mois/année — reste intact, seul l'ORDRE
  d'affichage était en cause).
- `audit_inventaire_articles.py --json` : les champs jour/mois/année
  parsés étaient retirés de la sortie JSON avant que l'export CSV/MD
  n'existe — corrigé pour les garder (renommés sans underscore),
  nécessaires à l'affichage/tri de l'onglet GUI Articles.

## Décisions actées

- Pas de rattrapage rétroactif sur `evenements_cites` — l'utilisateur
  choisit lui-même quels événements "favoriser" en les forçant
  activement ; chaque forçage devient le point de départ du
  développement de cet événement, pas une suite à un historique
  préexistant qui n'existe pas.
- CSV abandonné comme format principal d'export au profit de
  Markdown (natif au vault Obsidian, consultable directement) — CSV
  reste disponible en option secondaire.
- Nouvel onglet GUI top-level "Articles" plutôt qu'un bouton dans
  "Audit par sujet" — demande explicite de David, même gabarit que
  "Rédaction".
- Détection de basculements : tout le corpus, chapo seul, rapport à
  la main (pas de lien pré-rempli vers "Promouvoir un événement" pour
  l'instant).

## Reste à faire (point de reprise)

- **Point C** (`developpements` cumulatif sur l'instance événement) et
  **point D** (option d'évolution en mode Forcer) — **pas codés**. Le
  risque de redite initial (forcer deux fois le même événement repart
  de la même fiche statique) n'est donc **toujours pas résolu**.
- **Trou de plomberie non résolu** : l'écran "Promouvoir un
  événement" ne liste que les articles du mois de parution ACTIF —
  les candidats de basculement viennent de dates éparpillées dans
  toute la chronologie, la plupart hors du mois actif, donc non
  sélectionnables tels quels. Incertitude à vérifier avant de coder
  quoi que ce soit : est-ce que la date de l'événement créé se cale
  automatiquement sur le mois actif plutôt que sur la date réelle de
  l'article source (`inject_custom_events.py::process_idea()`, champ
  `edition_active` — fichier pas revu sous cet angle cette session) ?
  Piste proposée, pas actée : ajouter l'action "Promouvoir en
  événement" dans le panneau de l'onglet Articles (pas de limite de
  mois là-bas).
- `detect_basculements_narratifs.py` : vérifier manuellement 1-2
  candidats contre le texte intégral (pas juste le chapo), tester sur
  un 2e scénario pour voir si l'absence d'amelioration/blocage est un
  vrai biais du scénario ou du LLM, avant de lancer sur tout le
  corpus.
- Aucune entrée `scripts_config.json` pour les nouveaux scripts
  destinés au GUI — cohérent avec le précédent `inject_custom_events.py`
  (mode `--idea`), tous ces écrans sont des onglets custom avec leurs
  propres routes.

## Fichiers livrés/modifiés

- `api.py` (modifié — `evenements_cites`/`evenements_cites_source`
  dans `build_article_md()`)
- `detect_evenements_cites_retroactif.py` (nouveau — rattrapage,
  finalement abandonné mais le script reste disponible/réutilisable
  si un vrai cas se présente un jour)
- `debug_test_evenement_central.py` (nouveau — outil de calibrage
  ponctuel, verdict + justification)
- `audit_sujets.py` (nouveau — audit lecture seule par sujet)
- `editer_sujets.py` (nouveau — suppression/modification de date,
  destructif avec garde-fous)
- `audit_inventaire_articles.py` (nouveau — inventaire complet,
  export `--md`/`--csv`/`--json`)
- `detect_basculements_narratifs.py` (nouveau — détection de
  basculements, un appel LLM par scénario)
- `app.py` (modifié — 6 nouvelles routes `/api/sujets/*` et
  `/api/articles/liste`)
- `app.js` (modifié — nouvel onglet "Articles" complet, wiring de
  "Audit par sujet", fonctions généralisées
  `apercuSupprimerArticle`/`apercuModifierDateArticle`)
- `index.html` (modifié — CSS + structure HTML des deux onglets)
- `HANDOFF_5_SEPTEMBRE.md` (ce fichier — remplace
  `HANDOFF_3_SEPTEMBRE.md`)

## Non traité aujourd'hui (hérité)

- P20 : choix du service externe de génération d'image — toujours en
  suspens.
- Secondaire S1-S7 (P17, Bug #27, renommage YAML génériques,
  troncatures JSON Mistral, GUI `promote_ville.py`, métaphores vs.
  descripteurs directs) — tous en observation, aucun changement.

## Fichiers à ré-uploader en début de prochaine session

- `BACKLOG_ACTIF.md` — version mise à jour ci-jointe, remplace la
  précédente dans le Project.
- `HANDOFF_5_SEPTEMBRE.md` (ce fichier) — remplace
  `HANDOFF_3_SEPTEMBRE.md`.
- `USER_MANUAL_COMPLET.md` — PAS mis à jour cette session (chantier
  non clos, rien à documenter côté utilisateur final pour l'instant).
