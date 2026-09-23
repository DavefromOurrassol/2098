# HANDOFF — 12 septembre 2026

Session consacrée presque entièrement à la **refonte de l'architecture
Carte** (chantier #2bis du backlog), déclenchée par l'accumulation de
bugs de synchronisation trouvés sur P7/overlays lors des sessions
précédentes.

## Fait

### Refonte backend — `zone_repository.py` + `routes_carte.py`
Diagnostic de départ : presque tous les bugs Carte récents (split/reparent/
rename, chacun corrigé séparément le 15 juillet, 8 et 10 septembre)
partageaient la même cause — trois sources de vérité pour une même zone
(`geographie/{scenario}.md`, `zones_pays.json`,
`geo_overlays/{scenario}.geojson`), chaque opération réimplémentant sa
propre logique de propagation entre elles.

**Construit** : `gui/zone_repository.py` (module Python pur, zéro
dépendance Flask, classe `ZoneRepository`) devient le seul point
d'écriture sur une zone. `gui/routes_carte.py` (Blueprint Flask) en est la
couche HTTP fine. Remplace ~20 routes historiques d'`app.py`.

**Méthodes portées, toutes testées en conditions réelles sur le vault de
David** (`fortress_world`) : `rename`, `reparent`, `split`, `personnaliser`
(couleur/motif/**hachures**, nouveau champ), `assign_pays`/`desaffecter`,
`overlay_creer`/`overlay_supprimer`, `creer_zone_n1`, **`supprimer_zone_n1`
(entièrement nouveau — n'existait pas avant cette session)**,
`impact_bascule_pays`, `marquer_pays_ignore`, plus les méthodes de lecture
(`affectations`, `zones_n1_colorees`, `couverture_carte`, `arbre_zone`,
`rechercher_zone`, `zones_toutes`, `origine_reelle_index`) et de
diagnostic (`zones_portant_un_pays`, `retirer_pays_des_autres_zones`).

**Script d'intégration** `integrate_routes_carte.py` : retire les
anciennes routes d'`app.py`, insère l'enregistrement du Blueprint (même
patron que `routes_dashboard.py`), valide le résultat avant d'écrire quoi
que ce soit. **Bug trouvé et corrigé en cours de route** : la première
version localisait la fin d'une fonction par heuristique de texte (première
ligne suivante en colonne 0) — cassait sur `/api/carte/propose`, dont le
prompt LLM est un f-string multi-lignes **non indenté** (donc avec des
lignes en colonne 0 qui ne sont PAS du code top-level). Réécrit pour
utiliser l'AST Python (`ast.parse` + `end_lineno`), qui connaît les vraies
frontières d'une fonction quel que soit son contenu.

### Refonte frontend
- **Masquage overlay (point 1 du départ)** : le calque "pays entier"
  garde toujours sa couleur de base (jamais supprimé) ; les overlays
  passent en opacité pleine (1, au lieu de 0.85) pour ne plus laisser
  transparaître le motif du dessous. Couleur overlay résolue par héritage
  N1 côté serveur — garantit une couleur identique entre le territoire
  "pays entier" d'une zone et ses portions en overlay.
- **Villes principales** : nouvelle couche (bouton toggle), capitales +
  mégapoles + >1M habitants par défaut, extraites de Natural Earth
  `populated_places` via `extraire_villes_principales.py` (précalcul,
  19 Mo → quelques centaines de Ko), servie par `GET /api/carte/villes`.
- **Contour de sélection unifié** : `turf.union` de tous les pays/overlays
  d'une zone (Turf.js ajouté via CDN), au lieu d'un trait par pays qui
  laissait les frontières internes visibles. `turf.difference` retire la
  portion d'un pays partagé qui appartient à une AUTRE zone.
- **Sous-zones localisables** (jamais construit avant) : cliquer le nom
  d'une sous-zone (arbre ou recherche) affiche son contour, reconstruit
  depuis ses propres entrées `origine_reelle` parmi les pays affectés à sa
  racine N1, plus ses overlays directs. Repli sur la zone parente + message
  explicite si la sous-zone n'a pas de géométrie propre (lieux/régions
  plutôt que noms de pays exacts, ex. "Balkans occidentaux").
- **Panneau unique par zone** : un seul bouton "✏️ éditer" (légende ET
  arbre) regroupe renommer, couleur/motif/hachures, "Pays & portions de
  cette zone" (fusion scinder + overlays), et la suppression de zone.
- **Hachures génériques** : désactivées par défaut (avant : automatiques
  au-delà de 8 zones N1), activables individuellement par zone.
- **Sous-zones (niveau 2/3)** : plus aucun bouton d'édition sauf
  "↗️ déplacer" — plus de couleur/motif propres (héritage N1 strict).

## Bugs trouvés (en testant chaque étape en conditions réelles)

1. **Doublon Turquie** : la création top-down d'`anatolie_forteresse_
   eurasiatique` (test réel) ajoutait la Turquie sans la retirer de
   `zone_euro_sud`, où elle était déjà. Fixé structurellement dans
   `creer_zone_n1()`.
2. **Couleur incohérente base/overlay** : la couleur d'un overlay ne
   passait pas par le même calcul (roue de teintes automatique) que le
   calque "pays entier". Fixé en faisant résoudre les deux par la même
   fonction `zones_n1_colorees()`.
3. **France "sans couleur" après le premier fix du masquage** : la
   première version supprimait tout le calque de base dès qu'un pays avait
   un overlay — perdait la couleur de la portion NON couverte pour un pays
   partagé. Corrigé en ne touchant plus au calque de base du tout.
4. **Surbrillance bloquée sur la zone précédente** : cliquer un pays ne
   mettait jamais à jour `zoneSurlignee` — corrigé dans `openCartePanel`,
   puis étendu au cas multi-entrées (Royaume-Uni/Angleterre/Écosse/
   Galles).
5. **Contour orange incluant tout un pays partagé** : sélectionner Zone
   Interdite de Heysham montrait tout le contour de la France, y compris
   la portion Zone Euro Sud. Corrigé avec `turf.difference`.
6. **Désaffecter ne fonctionnait pas réellement** : ne remettait à zéro
   que `zones_pays.json`, jamais `origine_reelle` — l'affichage carte
   priorisant `origine_reelle`, le pays réapparaissait affecté. Corrigé :
   désaffecter retire maintenant le pays de partout.
7. **Masques fantômes persistants après clic "supprimer"** : au moins un
   cas confirmé (France/zone_euro_sud) où le masque n'a pas été retiré par
   le bouton — cause exacte non identifiée avec certitude, débloqué par
   script direct. Point de vigilance si ça se reproduit.
8. **Portions orphelines** : supprimer un masque ne retirait pas le texte
   `portion` associé. Corrigé (`overlay_supprimer` efface maintenant aussi
   la portion) + nettoyage ponctuel des orphelins déjà existants (14
   entrées identifiées et nettoyées, hors `interzone_corridor_test` qui
   n'a jamais eu de masque du tout — pas orphelin).
9. **Flash de sous-zone à la sélection** : `openArbreZonePanel` surlignait
   d'abord la racine N1 le temps de charger l'arbre, avant de basculer
   vers la sous-zone visée. Corrigé (`skipHighlight`, un seul rendu direct
   sur la cible finale).
10. **Sélection impossible depuis l'arbre** : cliquer un nom de zone dans
    l'arbre (hors recherche) ne faisait rien — ajouté un clic sur le nom,
    tous niveaux.
11. **Script d'intégration cassé par un prompt LLM multi-lignes** — voir
    section backend ci-dessus (fix AST).

## Décisions actées

- Hachures génériques : désactivées par défaut, activables par zone —
  plus jamais automatiques selon un seuil de compte de zones.
- Sous-zones : plus d'édition couleur/motif/scinder/réviser, seul
  "déplacer" (reparent) conservé.
- Un seul point d'entrée d'édition ("✏️ éditer") pour toute zone N1,
  légende et arbre confondus.
- Scinder et suppression-de-masque restent deux opérations distinctes sur
  le plan des données mais regroupées dans la même section du panneau
  unique.
- Supprimer un masque efface aussi son texte `portion` associé.
- **Interzone Corridor** (renommée "Interzone Corridor Test" en cours de
  session, test du bouton Renommer) : jamais eu de tracé dessiné, restée
  invisible malgré toutes les corrections apportées cette session — David
  a choisi de la **supprimer entièrement** (nouvelle capacité) plutôt que
  de continuer à réparer, pour repartir sur des bases propres.
- Libellé "🗑️ tracé" renommé en "🗑️ supprimer le masque" (plus explicite,
  demande de David).

## Reste à faire

- **Recréer Interzone Corridor** proprement, dessiner ses tracés pays par
  pays via le panneau unique.
- **Enrichissement LLM des zones manquantes** — routes non portées,
  restent dans l'ancien `app.py`, fonctionnelles telles quelles.
  (**Correction du 12 sept, soir** : cette section listait aussi S11 comme
  "à construire" — faux, vérifié sur le code réel le soir même : S11 est
  complet et fonctionnel depuis avant cette session, information
  provenant d'une mémoire de session périmée. Seule la migration de sa
  route vers `routes_carte.py` reste, elle, non faite.)
- **Nettoyage de code mort** : `_ouvrirSplitPanel`, `_ouvrirPersoPanel`
  (`app.js`) et fonctions associées, plus jamais appelées.
- Vérifier si d'autres textes `portion` orphelins existent au-delà de
  ceux déjà nettoyés (`diagnostiquer_portions_orphelines.py` disponible).
- Écrire un texte `portion` à jour pour le partage France (l'ancien a été
  effacé comme orphelin/obsolète, pas remplacé).
- Points hérités du 10 septembre toujours ouverts : Nordgard/Corridor
  d'Amsterdam/Zone de Koursk à confirmer créées dans le vault réel,
  overlay Allemagne mal renseigné (couvre la Norvège), injection des
  personnages/entités Hyphan, `tensions_internes`/`periode_transition`
  vides sur Zone Interdite de Heysham.

## Fichiers livrés

**Durables** (à garder dans `gui/`) :
- `zone_repository.py` — repository complet (voir Fait, ci-dessus)
- `routes_carte.py` — Blueprint Flask
- `integrate_routes_carte.py` — réutilisable si de nouvelles routes
  doivent être migrées d'`app.py` un jour

**Scripts ponctuels/diagnostics, utiles à garder** :
- `extraire_villes_principales.py` — à relancer si le seuil de population
  doit changer
- `lister_overlays.py`, `diagnostiquer_zones_invisibles.py`,
  `diagnostiquer_portions_orphelines.py` — diagnostics réutilisables
- `nettoyer_portions_orphelines.py` — nettoyage ciblé (liste explicite en
  dur, à adapter si relancé)

**Scripts de patch JS/HTML incrémentaux** (déjà appliqués, plus besoin de
les relancer — une quinzaine de fichiers `patch_carte_*.py`, tous
appliqués cumulativement sur `app.js`/`index.html` en cours de session) :
non listés individuellement ici, leur effet cumulé est déjà dans les
fichiers du GUI.

**Scripts de test** (réutilisables pour valider un futur changement) :
`test_zone_repository_dryrun.py`, `test_routes_carte.py`,
`test_propose.py`.

**Documentation mise à jour** : `USER_MANUAL_COMPLET.md` (section
"Refonte Carte (12 septembre 2026)" ajoutée, tableau des routes API
actualisé), `BACKLOG_ACTIF.md` (chantier #1 mis à jour, nouveau chantier
#2bis).

## Non traité hérité

- P20 (service de génération d'images externe) — toujours en attente de
  choix, pas touché cette session.
- Secondaire S1-S11 (voir `BACKLOG_ACTIF.md`) — pas touché cette session.
