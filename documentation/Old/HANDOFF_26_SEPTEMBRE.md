# HANDOFF — 26 septembre 2026

Suite de `HANDOFF_25_SEPTEMBRE.md`. Session consacrée à S17 (tests GUI,
premier vrai passage `--llm`, refonte de la section « Relations & lore »,
écran de validation), à des corrections de lore fortress_world/reference
trouvées par l'audit, puis à S15 (texte des géographies), S16 (sous-zone
depuis la Carte) et S12 (`zones_pays.json`). Toutes les modifications
faites sur le vault réel par David (aperçu, `.bak`, commit à chaque
étape). En fin de session : `validate.py` 0 erreur / 0 avertissement,
audit du lore 0 erreur, 0 relation à corriger, 0 inter-scénario.
Derniers commits : `5ced879` (S17), `4adef67` (S15), `2ffe703` (S16),
`9dcb9fb` (S12), `4696924` (renommage « reconstruite »).

## Fait

### S17 — Audit du lore — CLOS
- **Tests GUI** : les 5 étapes testées en conditions réelles, toutes
  `gui_verified: true` (étape 5 = onglet, sans drapeau).
- **Section sidebar « Relations & lore — étapes 1 → 5 »** (remplace les
  3 entrées du 25 sept, jugées confuses) : 1 🔍 Vérifier le lore (gratuit,
  « À faire ensuite » en fin de sortie), 2 🤝 Rendre les relations
  réciproques (Simulation + personnages en réserve cochés par défaut),
  3 🔀 Retirer les relations vers un autre scénario, 4 🤖 Relecture IA
  (« Estimer seulement » coché par défaut), 5 ✅ Valider les propositions
  de l'IA (nouvel onglet). L'ancien 🤝 devient « Compléter les relations
  avec l'IA » (section création). Nouveau mécanisme `fixed_args` dans
  `scripts_config.json` (arguments fixes ajoutés côté serveur).
- **Étape 5** : relations proposées (nom lisible de la cible, qui elle est,
  raison, extrait cité) → Garder / À trier / Rejeter ; contradictions
  (indice « extrait présent »), bouton « Marquer comme traitée », et
  **correction depuis le GUI** (texte modifiable, aperçu, `.bak_correction`,
  apostrophes YAML gérées) ; « Simuler l'écriture » obligatoire avant
  « Écrire dans les fiches », réciprocité enchaînée. Rejet = supprimé du
  fichier + inscrit dans `state/audit_lore_rejets.json` (jamais reproposé).
- **Premier passage `--llm` réel** (Mistral large) : Ergo-Wian puis Bloc
  Atlantique. ~8-10k jetons/fiche en entrée (~0,5 centime). Consignes
  durcies (v2) : relations certaines seulement, extrait cité obligatoire,
  filtre de sécurité sur le conditionnel/« ou » (écartées ⊘ dans le
  rapport), contradictions limitées aux faits incompatibles ; version des
  consignes dans l'empreinte du cache. Coût estimé d'une passe complète
  (826 fiches) : 4-6 $.
- **Règles de lore** : `reference` (Ergo-Wian non démocratique,
  succession d'Ergo-Wian = Hyphan, la démocratie n'est plus la norme) ;
  fortress_world + `bruxelles_pas_un_centre`. Messages de TOUTES les
  règles transmis à l'IA (plus seulement les « erreur »).
- **Personnages en réserve** comptés à part (« + 24 volontaires ») ;
  inter-scénarios = erreurs, **exceptions NAT supprimées** (et `--garder`).
- **`write_alliances_patch()` corrigé** : section « ## Relations »
  remplacée à sa place, retirée quand les deux listes sont vides.

### Lore corrigé (fortress_world, reference)
- **Halifax-Haute seul centre du Bloc Atlantique** ; **Bruxelles-Forteresse
  = vestiges de l'ancien gouvernement européen**, ville du Hors gouvernée
  par Ergo-Wian. Corrigés : géographie (zone Bloc Atlantique, 6 « ni
  Bruxelles ni Moscou » → Halifax), Orentchev, Autorité Numérique
  (`conseil_regulation_algorithmique`, siège Halifax), Bloc Eurasiatique
  Occidental, Bloc Atlantique et ANBA (Chambre de Recours sans pouvoir),
  article du 23 août (dépêche HALIFAX-HAUTE).
- **NexCore Atlantique** déplacé sous le Bloc Atlantique (niveau 2,
  origine Nouvelle-Écosse), fiche instance siège Halifax-Haute.
- Sentinelles des Aquifères Oubliés (Ergo-Wian) ; 3 oppositions Ergo-Wian
  + Cellules du Midwest pour le Bloc Atlantique ; NAT sans allié `_reference`.
- **Ingrid Solberg → Sigrid Halvorsen** (slug inclus, 11 fiches liées) :
  évite la confusion avec Ingrid Solvay (PDG NexCore).
- **Vikram** : alliance avec Ergo-Wian retirée des relations (secrète,
  connue de très peu), texte « négocie en secret ». **Hyphan n'est pas une
  résistante** (Vikram, Malo corrigés) ; article du 24 sept (Hyphan en
  Asie centrale) déplacé dans `_a_supprimer/`.
- Gelecek : `name` corrigé. `reference` : `europe_occidentale_reconstructee`
  → `europe_occidentale_reconstruite` (zone via la Carte ; entité, instance
  et 22 relations via outil ponctuel).

### S15 — texte des géographies — CLOS (reste en attente de besoin)
`generator/regenerer_corps_geographie.py` (sans IA) reconstruit la section
« ## Zones » depuis le frontmatter (Vue d'ensemble / Notes intactes).
Appliqué aux 6 scénarios (il manquait jusqu'à 29 zones). Maintenu à jour
**automatiquement** par la Carte (`ZoneRepository._save_geo`), bouton GUI
« 📝 Mettre à jour le texte des géographies », contrôle `validate.py`
11/11 (avertissement ; `--fix` corrige).

### S16 — sous-zone depuis la Carte — CLOS
Bouton « ➕ sous-zone » sur chaque nœud de l'arbre (aperçu → créer),
`ZoneRepository.creer_sous_zone`, route `/api/carte/creer_sous_zone`.
Arbre : boutons unifiés, panneau latéral redimensionnable.
`creer_zone_n1` n'ajoute plus de titre après « ## Notes ».

### S12 — `zones_pays.json` — CLOS
Mesure avec la même règle que la Carte : 0 écart sur 6 scénarios après
Italie (reference) réaffectée et 2 entrées parasites retirées (« Arctique »
fortress_world, « Internet mondial / GAFAM » new_sustainability).

## Bugs trouvés
- `write_alliances_patch()` (section vide laissée, section déplacée) — corrigé.
- Sortie de l'étape 5 sur une seule ligne (règle `pre` de style.css) — corrigé.
- `creer_zone_n1` ajoutait le titre après « ## Notes » — corrigé.
- L'IA confond deux fiches au même sigle (ANBA : Autorité Numérique vs Anba
  Siege) — alliance erronée rejetée ; slug `conseil_regulation_algorithmique`
  ≠ nom, piège comme `les_veilleurs_des_nappes_phreatiques` (Sentinelles).
- Le renommage de zone de la Carte ne rafraîchit pas l'affichage (Cmd+Maj+R).

## Décisions actées
- Aucune relation inter-scénarios, sans exception (mondes parallèles).
- Une alliance secrète ne va pas dans les relations (lues par les articles).
- Halifax seul centre ; Bruxelles vestige gouverné par Ergo-Wian ; NexCore
  actif = Bloc Atlantique.
- Rejet d'une proposition IA = supprimée et mémorisée comme rejetée.

## Reste à faire
- **#3 P20** — choisir et brancher le service d'image ; régénérer alors
  l'image de l'article du 23 août (montre encore Bruxelles).
- **S18** (nouveau, attente) — règles de lore des 4 autres scénarios (faits
  à fournir par David), relectures IA ciblées au fil de l'eau.
- S15 — Milan/Lyon (faisables via ➕ sous-zone), personnages en réserve.
- Supprimer `_a_supprimer/` quand David le décide.

## Fichiers livrés
- `gui/app.py`, `gui/static/app.js`, `gui/templates/index.html`,
  `gui/scripts_config.json` (section Relations & lore, entrée 📝),
  `gui/zone_repository.py`, `gui/routes_carte.py`.
- `generator/audit_lore.py`, `generator/fix_alliances_oppositions.py`,
  `generator/corriger_relations_inter_scenarios.py`, `generator/validate.py`,
  `generator/regenerer_corps_geographie.py`, `documentation/lore_regles.yaml`.
- Outils ponctuels utilisés puis supprimés : `renommer_personnage_26sept.py`,
  `renommer_slug_26sept.py`, `ajouter_entree_corps_geo.py`.
- `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`, `USER_MANUAL_COMPLET.md`,
  `USER_MANUAL_HISTORIQUE.md`, ce handoff.

## Non traité hérité
S1-S10, S14 inchangés (voir backlog).
