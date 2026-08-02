# Ourrassol 2098 — Résumé de handoff (pour nouvelle conversation)

Document préparé le 2026-06-20 pour permettre la reprise du projet dans
une nouvelle conversation sans avoir à relire tout l'historique.

## CONTEXTE GÉNÉRAL DU PROJET

Simulateur de presse fictive située en 2098, basé sur un vault
Obsidian + pipeline Python + API Claude. Architecture :

- **12 variables systémiques** (`variables/*.md`) — ex: geopolitique_conflits,
  energie_ressources_critiques, gouvernance_institutions...
- **6 scénarios** (`scenarios/*.md`) — breakdown, fortress_world,
  new_sustainability, eco_communalism, policy_reform, reference
- **20 thématiques** (`thematiques/*.md`) — sports, economie, sante...
- **Entités** (`entites/*.md`) — archétypes intemporels (organisations,
  personnages, IA...) — actuellement 26+
- **Instances** (`instances/*.md`) — incarnation d'une entité dans UN
  scénario donné — actuellement 94+
- **Événements custom** (`evenements/*.md` + `event_instances/*.md`)
  — faits datés ponctuels avec impact sur les variables
- **Matrice d'influence** (`influence_matrix.md`) — 132 edges entre
  variables (weight, polarity, feedback_role, lag)
- **Registre** (`generator/registre_evenements.md`) — anti-collision
  partagée entre signaux ET événements custom (format 6 colonnes :
  type | date | source | variable(s) | pilote | evenement_cle)

Pipeline de génération d'articles : `loader.py` → `snapshot.py` →
`prompt_builder.py` → `api.py` (modèle claude-opus-4-6, MAX_TOKENS=2000
— **bug connu, articles tronqués, jamais corrigé, voir TODO**).

## SCRIPTS LIVRÉS ET TESTÉS (tous dans /mnt/user-data/outputs/generator/)

Tous testés sur les vraies données du vault (pas seulement mockés),
sauf mention contraire. Tous suivent le même pattern : `queue.yaml`
rempli par l'utilisateur → script Python avec appel Claude → validation
mécanique avec retry (max 2) → injection → `processed.yaml`/
`needs_review.yaml`. Tous ont un mode `--dry-run`.

### 1. `loader.py` + `prompt_builder.py` (versions enrichies)
Ajout de l'extraction et l'affichage dans le prompt de génération
d'articles : `sub_variables` (name+trend, sans `links`) et
`indicateurs` (primary uniquement) par variable ; `boucles`
(stabilisation/déstabilisation) et `signaux_faibles_scenario` par
scénario. Testé en conditions réelles via `generate.py --dry-run` puis
un vrai run : prompt +10.5% de taille, qualité des articles jugée
meilleure (angles plus riches, personnages mieux différenciés).
**`prompt_builder.py` recharge ces données directement via
`load_all_variables()`/`load_scenario()` plutôt que de passer par
`snapshot.py`** (je n'ai jamais vu le code de `snapshot.py`).

### 2. `migrate_registre.py`
Script one-shot, migre `registre_evenements.md` de l'ancien format
(5 colonnes, signaux uniquement) vers le nouveau format hybride
(6 colonnes, signaux + événements). Déjà exécuté avec succès sur le
vault réel. **Ne pas relancer** si déjà fait (le script détecte le
nouveau format et ne fait rien si déjà migré).

### 3. `inject_custom_signals.py` (mis à jour)
Pipeline batch pour les signaux faibles → écrit dans
`variables/{var}.md` (section 12, signal_to_state) + section 7
(annotation) + registre. Queue : `signaux_custom/queue.yaml`.
Nouveauté ajoutée cette session : **mécanisme `sibling_events`** — pour
un signal touchant plusieurs variables dans le même run, chaque
variable voit les `evenement_cle` déjà utilisés par les variables
précédentes du même run, pour éviter les doublons de formulation
(bug initial trouvé et corrigé avec succès, testé en réel sur
`trump_putsch_ice_2028`/`trump_putsch_recomposition_blocs_2028` — puis
**nettoyé/supprimé du vault** par l'utilisateur car jugé être un
événement plutôt qu'un signal, voir plus bas).

### 4. `inject_custom_events.py`
Pipeline batch pour les événements custom → écrit `evenements/{slug}.md`
(archétype) + `event_instances/{slug}_{scenario}.md` (par scénario) +
registre. Queue : `evenements_custom/queue.yaml` (champs : description,
portee, date_approximative, intensite, scenarios, variables_hint,
variables_hint_count, acteurs_hint, acteurs_hint_count, source). Charge
les instances d'entités déjà existantes par scénario
(`load_available_actors()`) pour proposer des acteurs cohérents avec
le lore plutôt qu'inventés. Validation mécanique : delta_level dans
±25, variables valides, mot-count + année sur evenement_cle,
anti-collision registre, acteurs vérifiés (avertissement, pas bloquant,
si l'acteur ressemble à un slug snake_case mais ne correspond à aucune
instance réelle).
**Testé en réel avec succès** : `conflit_israel_iran_2026` injecté sur
les 6 scénarios, evenement_cle tous différenciés (le mécanisme
anti-collision via registre RÉELLEMENT mis à jour entre scénarios
fonctionne — contrairement au dry-run où rien n'est comparé puisque
rien n'est écrit).
**Correction apportée cette session** : suppression de
`write_custom_fiche()` (créait `evenements_custom/{slug}.md`,
entièrement redondant avec l'archétype `evenements/{slug}.md` —
contrairement aux signaux où la fiche custom est la SEULE trace de
l'idée source, ici elle dupliquait pour rien).

### 5. `create_entity.py` (nouvelle version, remplace l'ancien)
Crée des fiches ENTITÉ uniquement (pas les instances — voir
`generate_instances.py`). Deux modes, demandés interactivement au
lancement (`custom` ou `auto`) :
- **custom** : lit `entites_custom/queue.yaml` (champs : nom, category,
  role, etat, scenario_ref, scenario_hint, source). Claude DÉDUIT
  l'archétype (description, tension_fondamentale, variables_potentielles)
  à partir d'UNE instance de référence que l'utilisateur fixe
  précisément (role/etat dans scenario_ref = CONTRAINTES DURES, stockées
  ensuite dans le frontmatter de la fiche entité : `scenario_ref`,
  `role_ref`, `etat_ref` — c'est CE mécanisme que
  `generate_instances.py` utilise pour savoir où appliquer les
  contraintes dures).
- **auto** : demande un nombre N (+ catégorie optionnelle), Claude
  invente N entités libres.
- **Anti-doublon dans LES DEUX modes** : `entites/_entities_list.json`
  (à l'origine un simple cache de session dans l'ancien
  `generate_entities.py`, transformé en registre PERMANENT anti-doublon,
  mis à jour à chaque création). Claude doit déclarer explicitement
  `doublon_detecte`/`doublon_slug` s'il juge une entité trop proche
  d'une existante ; validation mécanique rejette si déclaré.
**Testé en réel avec succès** dans les deux modes : "Le Cartographe
Silencieux" (custom, scenario_ref=breakdown) et "Institut des Seuils
Démographiques"/"Oracle Démographique SYBIL" (auto).
**Validation des alliances/oppositions explicitement REPORTÉE** (voir
TODO).

### 6. `generate_instances.py` (renommage + réécriture de
   `generate_entities.py`)
Génère les instances par scénario pour des entités DÉJÀ créées (par
`create_entity.py`, custom ou auto, ou anciennes). Logique clé : lit
le frontmatter de chaque `entites/{slug}.md` ; si `scenario_ref` y est
présent, applique `role_ref`/`etat_ref` comme CONTRAINTE DURE
uniquement pour ce scénario précis (Claude ne reformule pas le rôle,
l'`etat_temporel` généré est vérifié mécaniquement contre la valeur
imposée) ; tous les autres scénarios de la même entité restent
entièrement libres, sans contrainte de cohérence biographique (un
même personnage peut être banquier ici, rebelle là — c'est voulu).
Options : `--entity slug` (une seule), `--scenario X` (un seul),
`--force` (régénère même si l'instance existe), `--dry-run` (affiche
le JSON complet de chaque instance générée, ajouté cette session sur
demande de l'utilisateur).
**Testé en réel avec succès**, dry-run confirmé fonctionnel sur les
deux cas (contrainte dure ET libre) — `[CONTRAINTE DURE]` s'affiche
correctement uniquement pour le bon scénario dans les logs.
**N'écrit jamais alliances/oppositions comme des slugs vérifiés
actuellement** — reprend la même logique texte-libre que l'ancien
`generate_entities.py` (voir TODO, sujet de la toute dernière
discussion de la session précédente).

## DÉCISIONS ARCHITECTURALES IMPORTANTES

- **Fusion future prévue** : `create_entity.py` + `generate_instances.py`
  seront un jour fusionnés en `create_entities_and_instances.py` (même
  logique que prévue à terme pour signaux/événements), mais
  intentionnellement développés séparément pour itérer plus vite. Les
  fonctions sont déjà conçues comme des briques réutilisables.
- **Coût/modèle** : tous les scripts d'injection (signaux, événements,
  entités, instances) utilisent `claude-sonnet-4-6`. SEUL `generate.py`
  (génération d'articles) utilise `claude-opus-4-6` — plus cher (~$0.086
  par article mesuré en réel, donc ~$26-35 pour 300 articles, à
  recalculer si MAX_TOKENS est augmenté).
- **`--dry-run` n'écrit JAMAIS rien sur disque, y compris le registre**
  — donc l'anti-collision inter-scénarios ne peut PAS être validée en
  dry-run (déjà causé une fausse alerte de doublon sur
  `conflit_israel_iran_2026` qui ne s'est PAS reproduite en run réel).
- **Nettoyage manuel après tests** : pas encore de script `undo_custom.py`
  générique (évoqué mais jamais codé) — le nettoyage de tests
  (`guerre_israelo_iranienne`, `trump_putsch_*`) a été fait fichier par
  fichier, manuellement, avec mon aide pour identifier précisément quoi
  supprimer.

## TODO / CHANTIERS OUVERTS, NON RÉSOLUS

1. **`MAX_TOKENS = 2000` dans `api.py`** — articles tronqués
   systématiquement (confirmé sur 2 générations réelles), jamais corrigé.
   Recommandation : passer à 3000-4000.

2. **Validation alliances/oppositions** (entités/instances) — chantier
   discuté en détail en toute fin de session précédente, PAS commencé.
   Contexte : sur 94 fiches instances existantes, analyse réelle donne
   27 mentions slug valides, 2 slug cassés, **488 mentions en texte
   libre (485 uniques)**. Débat non tranché : faut-il "officialiser"
   rétroactivement ces 485 mentions en vraies entités (chantier
   potentiellement aussi gros que la création initiale des entités), ou
   laisser tel quel puisque `prompt_builder.py` n'exploite actuellement
   JAMAIS ces champs (confirmé par lecture de code) donc aucun impact
   réel sur les articles générés à ce jour ? Dernière position de
   l'utilisateur : réfléchit encore, pas de décision prise.

3. **1068 avertissements `validate.py` historiques** (avant cette
   session) — entités sur-générées par l'ancien `generate_entities.py`
   (valeurs hors [0-5], alliances/oppositions texte libre déjà identifié
   comme cause probable, 2 `categorie: média` invalides sur
   `prisme_global`/`voix_du_dehors`). Recoupe le point 2. Jamais traité.

4. **`undo_custom.py`** — script générique de nettoyage
   (`--type signal/evenement/entite --slug X`) évoqué mais jamais écrit.
   Utile vu la fréquence des tests à nettoyer manuellement.

5. **Cohérence des noms de fiches custom signaux/événements/entités**
   — pour les signaux multi-variables, un même thème peut donner
   plusieurs `signal_slug` différents (ex: trump_putsch_ice_2028 ET
   trump_putsch_recomposition_blocs_2028 pour la même idée) — pas un
   bug, mais source de confusion si non documenté.

## FICHIERS DE RÉFÉRENCE DISPONIBLES

Si besoin de les revoir, je dois redemander à l'utilisateur d'uploader
(pas stockés au-delà de cette session) :
- `entity_template.md`, `instance_template.md` (gabarits officiels)
- Fiches réelles vues en détail : `consortium_helios.md`,
  `vasil_orentchev_breakdown.md`, `agence_stabilisation_climatique_*.md`
- `_entities_list.json` (avant transformation en registre permanent)
- Code source complet déjà lu en entier : `loader.py`,
  `prompt_builder.py` (anciennes versions), `create_event.py`,
  `create_entity.py` (ancien), `generate_entities.py` (ancien),
  `inject_custom_signals.py` (avant sibling_events)

## COMMENT REPRENDRE EFFICACEMENT

1. Uploader ce document en début de nouvelle conversation
2. Uploader le vault complet en zip SI une tâche nécessite d'y accéder
   (pas la peine sinon — je peux travailler sur la base de ce résumé
   pour des décisions de conception)
3. Préciser sur quel chantier reprendre en priorité (suggestion :
   MAX_TOKENS d'abord, rapide ; alliances/oppositions ensuite, plus
   gros morceau à trancher d'abord sur le fond avant de coder)
