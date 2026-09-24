# HANDOFF — 24 septembre 2026 (matin)

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

## Reste à faire
- **Hyphan, point 3** (seul restant) : injecter les personnages/entités/
  événements. Fournir `HANDOFF_8_SEPTEMBRE.md` ou le texte Hyphan.
- Vérifier que le dernier scan `--run-origine-reelle` donne bien 4
  incohérences (réponse "ok" de David, sortie non recollée).
- Suite inchangée du handoff du 23 : `--apply-type-entite` sur
  `fortress_world` si pas fait, #3 P20 (service d'image), #4 revue des
  `zone_suspecte`, `.gitignore`, S13.
- Optionnel : `git config --global user.name/user.email` (avertissement
  git à chaque commit, sans conséquence).

## Fichiers livrés
- `BACKLOG_ACTIF.md` — chantier #1 réécrit (revue du 24), S12 précisé.
- `USER_MANUAL_COMPLET.md` — repli de la carte sur `zones_pays.json`.
- Vault (modifié par David) : `geographie/fortress_world.md`,
  `documentation/need_action/chantiers_geographie.yaml`, `gui/zones_pays.json`
  (suppression Corridor d'Amsterdam).
