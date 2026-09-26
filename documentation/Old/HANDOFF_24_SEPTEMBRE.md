# HANDOFF — 24 septembre 2026 (matin + après-midi)

Suite de `HANDOFF_23_SEPTEMBRE.md`. Session courte consacrée à la revue
point par point du "Reste à faire" du chantier #1 (Hyphan,
`fortress_world`), à la demande de David. Toutes les modifications ont
été faites sur le vault réel par David (scripts fournis, chacun vérifiant
le YAML avant écriture, ou GUI), avec `git status` propre et commit à
chaque étape.

## Fait — décisions de David et exécution

1. **Interzone = ancien nom de Zone Euro Sud** (lecture A). Interzone
   Corridor abandonné et retiré du backlog. Correction de 3 occurrences :
   "pillards de l'Interzone" → "pillards de la Zone Euro Sud" dans la
   description de Heysham (frontmatter + corps markdown), entrée
   `France / portion: France - Interzone` retirée de Zone Euro Sud
   (doublon interne).
2. **Nordgard, Corridor d'Amsterdam, Zone de Koursk abandonnés.** Corridor
   d'Amsterdam (N1 sans aucun pays) supprimé par David. Pays-Bas restent
   dans l'Espace Nordique. `fortress_world` : 75 zones, 25 N1.
4. **France (F1b)** : Zone Euro Sud porte la base du pays, texte `portion`
   réécrit ("Toute la France hors littoral Manche-Atlantique (Zone
   Interdite de Heysham) : Bassin parisien, Centre, Est, vallée du Rhône
   et façade méditerranéenne."), Heysham garde son overlay littoral.
   **Allemagne (A1)** : entière dans l'Espace Nordique, texte provisoire
   remplacé par `null`. `check_overlay_portion_coherence` : 0 dérive,
   0 orphelin, 0 doublon interne, 1 INFO voulue (texte France de ZES).
5. **Finlande et Lituanie** ajoutées à l'Espace Nordique dans la fiche
   (format complet), 2 chantiers `pays_sans_zone` marqués traités via
   `--all --run-zones --marquer-resolus`, entrée générique "pays baltes"
   retirée du Bloc Eurasiatique. `check_zones_coherence --all` : tous les
   pays des 6 scénarios ont une zone.
6. **Sous-zones** : Bratislava, Genève, Tbilissi (+ lieux rattachés)
   déplacées sous Zone Euro Sud depuis l'arbre de la Carte. Premier
   passage : Marchés Gris de Tbilissi déplacé à la place de Tbilissi-Nord,
   corrigé. **Almaty + Complexe d'Orentchev gardés volontairement sous les
   Zones Grises.** Garde-fou attendu à 4 incohérences (Almaty ×2 voulues,
   São Paulo ×2 hors Hyphan).

## Constat corrigé dans la documentation
La carte **se replie sur `zones_pays.json`** pour un pays absent de toute
fiche (Finlande/Lituanie s'affichaient en Espace Nordique sans être dans
`fortress_world.md`). L'affirmation du 23 sept "la carte ne lit pas
`zones_pays.json`" était trop forte — manuel et backlog (S12) corrigés.

---

# APRÈS-MIDI — injection Hyphan, lot Apocalypse Nerds, nouveaux outils

Le chantier #1 (Hyphan) est **clos**. Base validée en fin de session :
**0 erreur, 0 avertissement** (`validate.py`). `git status` propre,
`.gitignore` en place.

## Lot Apocalypse Nerds (16 entités, surtout `reference`)
Entités inspirées du livre *Apocalypse Nerds* (néo-réaction, démocratie
qui n'est plus la norme dans certaines zones). Scénario porteur
`reference` ; ailleurs, simples **souvenirs** en 2098, poids faible
(consigne par scénario). Institutions/idées : The Lattice, Ergo-Wian
Sovereign Holdings, Meridian Assembly, The Tidewater Canon, Deepfield
Institute, Holdfast, Kindling, Lamplight, Raised Hands. Personnes : Ilse
Varga-Holm, Hyphan Raghavan, Aurelio Stahl, Nadia Ferreira-Sato, Kaspar
Lind, Maëlys Okonkwo, Elias Mørk. **Ergo-Wian** durcie dans `reference`
(gouvernement-entreprise monopolistique, non démocratique ; rôle actif
avec des fonctions différentes dans les autres scénarios). Hyphan
Raghavan : successeuse désignée à la tête d'Ergo-Wian dans `reference`.

## Lot Hyphan (docx `Ourrassol_Scénario1.docx`, `fortress_world` seul)
- **Géographie** : Euro-Nord = Espace Nordique (gouverné par Ergo-Wian,
  NAT sa filiale armée) ; le « Hors » = Zone Euro Sud ; Califat de
  Barcelone = Al-Hima. Sous-zones créées : `paris_hors` (N2),
  `evry_hors` (N3, ex-Génopole, terrain neutre de négociation), `tolosa`
  (N2, « Saint-Sernin-du-Désert », cité refuge de la Tribu des Cinq
  Nations, alliée d'Al-Hima).
- **16 entités** : Recycleurs, Cycles (centres de collecte), Mouvement
  de Reconquête européenne (**QG Milan, antenne Lyon**), Alpha47, Contrats
  de service d'Ergo-Wian, Dédoublés (« Superposés » chez Ergo-Wian,
  « Porteurs de reflets » au Califat), Garde du Seuil (clandestine),
  Tribu des Cinq Nations ; Vikram et Anjali Raghavan, Malo, Anton Vasko,
  Ingrid Solberg, Aymeric de Valfort, Guilhelma (cheffe-chamane), Raimon.
  **En réserve** (exclus des articles) : Malo, Anton Vasko, Raimon.
- **Guerre indo-arabe 2038** : `guerre_indo_arabe_2038_fortress_world`
  (majeure) + `conflit_indo_arabe_2038` (breakdown, policy_reform,
  reference).
- **Hyphan Raghavan / fortress_world** : orpheline d'environ 15 ans à
  Paris-Hors, nièce de Vikram, glaneuse pour les Cycles avec Malo,
  Dédoublée qui s'ignore ; aucun lien avec la direction d'Ergo-Wian.
  Régénérée avec consigne enrichie puis **exclue des articles**.
- **Localisations corrigées** : Guilhelma → `tolosa` ; Ingrid Solberg et
  Aymeric de Valfort → `bruxelles_forteresse` (mention erronée du « Bloc
  Atlantique » retirée du rôle d'Aymeric) ; Reconquête → `zone_euro_sud`,
  lieu « Milan (QG) — antenne à Lyon ».
- **Validation** : Deepfield Institute (`new_sustainability`) dates
  2026-2053 (mythifié exigeait `annee_fin`) ; Alpha47
  `zone_geographique: planétaire` → `globale`.

## Nouveaux outils et correctifs (détail : manuel §3 et §7)
- **Consignes par scénario** (`consignes_scenarios`) à la création
  d'entités, enregistrées dans la fiche entité.
- **`generate_instances.py`** : `--role` (scénario de référence),
  `--consigne` (autres scénarios), `--injection-custom`.
- **🎯 `set_selection_instance.py`** : exclure/ré-autoriser une instance
  des articles (`exclure_articles`), retirer/rétablir la garantie des
  instances custom. ⚠ Une régénération fait perdre l'exclusion.
- **Carte** : bouton **✏️ renommer** sur les sous-zones niveau 2/3 de
  l'arbre (slug + nom, impact puis confirmation). Outil sidebar
  provisoire `renommer_slug_zone` retiré.
- **Lecture JSON LLM robuste** (`extraire_json()`) : l'échec « Aucun JSON
  exploitable » de la régénération Hyphan n'était pas une troncature.
  Réponse brute sauvée dans `gui/logs/llm_json_echec_*.txt` en cas
  d'échec.
- **`slugify`** : translittération ø/æ/ß/ł…
- **`.gitignore`** : `.DS_Store`, `workspace.json`, `*.bak`,
  `gui/logs/`, `__pycache__/`.
- Scripts ponctuels supprimés du vault (`hyphan_zones_section4.py`,
  `maintenance_entites_24sept.py`, `renommer_slug_sous_zone.py`,
  `localiser_bruxelles_milan.py`).

## Reste à faire (prochaine session)
- #3 P20 — brancher le service d'image.
- #4 — revue des 14 `zone_suspecte` (tri proposé le 23, non appliqué).
- S13 — `assign_pays` écrit des entrées `origine_reelle` minimales.
- S15 — suites optionnelles Hyphan (Ergo-Wian fortress_world aligné sur
  Euro-Nord ; Milan/Lyon en sous-zones si besoin ; corps markdown
  périmé ; personnages en réserve à ré-autoriser au fil du récit).
- S16 — création directe de sous-zone dans le GUI, si le besoin revient.
- Optionnel : `git push` (la branche a plus de 25 commits d'avance sur
  `origin/main`) ; `git config --global user.name/user.email`.

## Fichiers livrés (après-midi)
- `gui/static/app.js` — renommage des sous-zones dans l'arbre.
- `gui/scripts_config.json` — consignes par scénario, options
  `generate_instances`, entrée 🎯, sans `renommer_slug_zone`.
- `generator/instance_generation_common.py` — consigne par scénario,
  `extraire_json()`.
- `generator/generate_instances.py`, `generator/create_entities_and_instances.py`,
  `generator/loader.py`, `generator/set_selection_instance.py`.
- `BACKLOG_ACTIF.md` (#1 clos, S4 mis à jour, S15/S16),
  `BACKLOG_ARCHIVE.md` (#1 archivé), `USER_MANUAL_COMPLET.md`,
  ce handoff.
