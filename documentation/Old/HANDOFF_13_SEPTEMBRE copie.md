# HANDOFF — 13 septembre 2026

Session déclenchée par un bug remonté par David sur l'outil "dessiner une
zone complète" (S11) : un tracé partiel sur la France colorait le pays
entier. A mené à la découverte d'une classe de bug plus large (doublons
"pays entier" dans `origine_reelle`), à un nouvel outil de diagnostic/
nettoyage, et à deux corrections structurelles dans `zone_repository.py`.

## Fait

### Bug initial — France/Zone Interdite de Heysham (couleur de base)
Diagnostic : `overlay_creer()` (quand le pays n'est pas encore dans
`origine_reelle` de la zone cible) ajoute une entrée structurellement
identique à un vrai rattachement "pays entier" (aucun marqueur
"overlay-only"). `origine_reelle_index()`/`affectations()` ne
distinguaient pas cette entrée d'un vrai split, donc la France entière se
retrouvait coloriée pour Zone Interdite de Heysham alors que seule une
portion avait été dessinée.

**Corrigé** dans `zone_repository.py` :
- Nouvelle méthode `_paires_overlay(scenario)` — ensemble des couples
  (zone_slug, pays_normalise) réellement backés par un tracé dans
  `geo_overlays/{scenario}.geojson`.
- `origine_reelle_index()` exclut désormais ces couples du calcul de la
  couleur "pays entier" de base.
- `zones_portant_un_pays()` enrichie : renvoie `type`
  (`pays_entier`/`overlay`) et `portion` par zone (au lieu de la seule
  liste de slugs).

### Nouvelle fonctionnalité GUI — panneau multi-zones
Demande de David : quand on clique un pays réparti sur plusieurs zones, le
panneau doit lister toutes ses zones d'appartenance (pas juste la
principale).

- Nouvelle route `GET /api/carte/zones_par_pays?scenario=&pays=`
  (`routes_carte.py`), appelle `zones_portant_un_pays()`.
- `app.js::openCartePanel()` passée en `async`, interroge cette route et
  affiche une section "Ce pays est réparti sur N zones" (badge pays
  entier/overlay + texte portion) quand `N > 1`. Aucun changement visuel
  pour un pays affecté à une seule zone.

### Bug structurel #2 — overlay_supprimer() recréait le même bug
Découvert sur Pays-Bas/Zone Interdite de Heysham : cliquer "🗑️ supprimer
le masque" ne faisait, depuis le fix du 12 sept, que vider le texte
`portion` — l'entrée `origine_reelle` restait, avec `portion: null`,
strictement indiscernable d'un vrai pays-entier. Chaque suppression de
masque recréait donc un nouveau doublon.

**Corrigé** : `overlay_supprimer()` retire maintenant l'entrée
`origine_reelle` ELLE-MÊME quand plus aucun autre masque ne couvre le même
couple (zone, pays) après suppression. Garde-fou testé : si un pays a
plusieurs polygones distincts dans la même zone, l'entrée n'est retirée
qu'après suppression du dernier.

### Bug structurel #3 — supprimer_zone_n1() bloquait les sous-zones
`supprimer_zone_n1()` refusait toute zone de niveau != 1, alors que rien
dans sa logique (enfants bloquants, relations, `zones_pays.json`,
overlays) n'est spécifique à une racine. Restriction retirée — la méthode
(et la route existante `/api/carte/supprimer_zone`) fonctionne maintenant
sur n'importe quel niveau. Nécessaire pour supprimer
`Casablanca-Périphérie` (niveau 2).

### Nouvel outil — diagnostiquer_doublons_pays_entier.py
Diagnostic + nettoyage de tout pays/entité ayant "pays entier" en double
entre deux racines N1 distinctes (hérite normalement la logique
`_paires_overlay`/niveau-N1 ci-dessus). Trois passes d'itération avant
d'être fiable :

1. **v1** : comparait chaque pays contre chaque zone (tous niveaux) sans
   distinguer parent/enfant → quasi tout le vault remontait en faux
   positif (sous-zones héritant normalement de leur racine N1). Lent en
   plus (relecture complète du vault par pays).
2. **v2** : réécrite en une seule lecture par fichier + comparaison
   uniquement entre racines N1 non apparentées. Beaucoup plus propre, mais
   toute entité absente de `zones_pays.json` (villes, régions fictives,
   entités composées type "Danemark / Groenland") ressortait signalée
   comme "résidu" à tort.
3. **v3** : ajout de `_resoudre_entite()`, réutilise `_tokens_entite()`
   (déjà dans `zone_repository.py` depuis le 14 juillet pour ce cas)
   pour reconnaître les entités composées et les comparer pays par pays
   contre `zones_pays.json`.

Fonctionnalités finales :
- `--scenario X` : rapport texte (ou `--json`), deux sections — "PAYS
  RÉELS" (prioritaire, affecte la carte) et "entités non reconnues"
  (villes/régions, à trancher narrativement).
- `--nettoyer --pays X --garder SLUG [--execute]` : nettoyage ciblé,
  dry-run par défaut.
- `--nettoyer-auto [--execute] [--rapport-portions FICHIER.md]` : nettoie
  en lot tous les cas non ambigus (un seul match `zones_pays.json`),
  laisse le reste de côté, sauvegarde les textes `portion` retirés avant
  suppression.
- Nouvelle méthode dédiée dans `zone_repository.py` :
  `retirer_doublons_pays_entier()` — **volontairement distincte** de
  `retirer_pays_des_autres_zones()` (existante) : cette dernière retire le
  pays de TOUTES les autres zones, y compris les overlays légitimes
  (testé, a cassé un cas réel en supprimant une portion valide et en
  laissant un masque orphelin) — la nouvelle ne touche jamais les entrées
  `overlay`.

### Nouvel outil — retirer_entree_parasite_zones_pays.py
Effet de bord découvert en nettoyant des entités non-pays (Balkans
occidentaux, Danemark / Groenland en tant que clé composée) :
`retirer_doublons_pays_entier()` met toujours à jour `zones_pays.json`,
et ajoute donc une clé parasite pour une entité qui n'est pas dans
`pays_liste`. Script dédié pour la retirer proprement (refuse d'agir si
l'entité est un vrai pays, `.bak` automatique via `_save_zones_pays()`).

### Nettoyage réel effectué
- **fortress_world** : 12 pays réels (Allemagne, Belgique, Biélorussie,
  Brésil, Irak, Kirghizistan, Ouzbékistan, Pays-Bas ×2 passes — voir bug
  #2 —, Russie, République tchèque, Slovaquie, Ukraine) + Bruxelles
  (voir décision ci-dessous) + Balkans occidentaux + Casablanca-Périphérie
  (supprimée). Scan final : 0 doublon.
- **breakdown** : Sénégal (1 cas).
- **eco_communalism** : Algérie, Brésil, Kazakhstan, Maroc (4 cas,
  `--nettoyer-auto`).
- **new_sustainability** : Internet mondial/GAFAM (héritage), Danemark /
  Groenland (après le fix v3). Entrée parasite `zones_pays.json` identifiée,
  **pas confirmée nettoyée** (voir Reste à faire).
- **policy_reform, reference** : **jamais scannés** cette session.

### Bruxelles/ANBA → renommage + déplacement
Décisions de David : `Bruxelles-Forteresse` et l'ex-`Siège de l'ANBA —
Autorité Numérique du Bloc Atlantique` rattachées toutes les deux à
`Zone Euro Sud` (niveau 2). L'ANBA renommée **ANZES** — "Siège de l'ANZES
— Autorité Numérique de la Zone Euro Sud" (slug
`anzes_siege_zone_euro_sud`), via `renommer_zone`/`reparent_zone`
existants (aucun nouvel outil nécessaire). Vérifié : pas de tracé overlay
sous l'ancien slug, rien à migrer de ce côté.

## Bugs trouvés
1. `overlay_creer()` : entrée `origine_reelle` overlay-only indiscernable
   d'un pays-entier — **corrigé** (`_paires_overlay`/`origine_reelle_index`).
2. `overlay_supprimer()` : suppression de masque recréait le même bug
   (ne vidait que le texte `portion`) — **corrigé**.
3. `supprimer_zone_n1()` : bloquait toute zone niveau != 1 sans raison
   dans sa logique — **corrigé** (renommage de méthode gardé pour ne pas
   casser le contrat des routes existantes).
4. `retirer_pays_des_autres_zones()` (existante, pas modifiée) : trop
   large pour le nettoyage de doublons pays-entier — supprime aussi les
   overlays légitimes du pays dans d'autres zones. **Ne pas l'utiliser**
   pour ce cas, `retirer_doublons_pays_entier()` est le bon outil.
5. `retirer_doublons_pays_entier()` (nouvelle) : mode à surveiller — met
   toujours à jour `zones_pays.json`, ce qui pollue le fichier d'une clé
   parasite pour toute entité qui n'est pas un vrai pays (villes, régions,
   entités composées). Contournement en place
   (`retirer_entree_parasite_zones_pays.py`), **pas corrigé à la racine**
   — piste pour la prochaine session : ne mettre à jour `zones_pays.json`
   que si l'entité est dans `pays_liste`.

## Décisions actées
- `Bruxelles-Forteresse` + `ANZES` (ex-ANBA) → niveau 2 sous `Zone Euro Sud`.
- `Balkans occidentaux` → gardé sous `Zone Euro Sud` (via
  `Zone Tampon Balkano-Caucasienne`), résidu `Zones Grises et Tampons`
  nettoyé.
- `Casablanca-Périphérie` (sous `Zones Grises et Tampons`) → **supprimée
  entièrement**, gardé `Marchés Gris de Casablanca-Périphérie` (sous
  `Al-Hima`).
- `Internet mondial / GAFAM (héritage)` (new_sustainability) → gardé sur
  `Tours de contrôle orbital Helios`.
- **Prochaine session, demande explicite de David** : intégrer l'outil de
  diagnostic+nettoyage dans le GUI, sous forme d'une **liste de
  propositions déjà calculées** (comme le panneau "Zones à enrichir" ou
  le panneau de review S11) — l'utilisateur choisit/coche/applique, il ne
  doit **jamais avoir à taper un slug ou un nom à la main**. Pas encore
  scopé (onglet dédié vs section du panneau Carte, review pays par pays
  vs bouton "tout nettoyer") — à trancher en début de prochaine session.

## Reste à faire
- **Scanner `policy_reform` et `reference`** (jamais touchés cette
  session) avec `diagnostiquer_doublons_pays_entier.py`.
- **Reconfirmer `new_sustainability` propre** après nettoyage Danemark/
  Groenland (dernier scan non relancé après ce nettoyage).
- **Nettoyer l'entrée parasite `"Danemark / Groenland"`** dans
  `zones_pays.json["new_sustainability"]` — script prêt
  (`retirer_entree_parasite_zones_pays.py`), **commande donnée mais
  exécution non confirmée**.
- **Relire `rapport_portions_eco_communalism_13sept.md`** (et l'équivalent
  fortress_world, `rapport_portions_retirees_13sept.md`) — textes
  narratifs retirés lors des nettoyages en lot, à éventuellement
  redessiner en overlay proprement plutôt que perdre le contenu.
- **Intégration GUI de l'outil de diagnostic** (voir Décisions actées
  ci-dessus) — chantier à scoper et construire.
- **Fix racine du bug #5** (`retirer_doublons_pays_entier` ne devrait pas
  toucher `zones_pays.json` pour une entité hors `pays_liste`) — pas fait,
  contournement suffisant pour l'instant.

## Fichiers livrés

**Modifiés (à remplacer dans `gui/`)** :
- `zone_repository.py` — `_paires_overlay()` (nouveau), `origine_reelle_index()`
  (fix), `zones_portant_un_pays()` (enrichi), `retirer_doublons_pays_entier()`
  (nouveau), `overlay_supprimer()` (fix), `supprimer_zone_n1()` (niveau
  générique).
- `routes_carte.py` — route `GET /api/carte/zones_par_pays`.
- `app.js` — `openCartePanel()` async + section multi-zones.

**Nouveaux scripts (à placer dans `gui/`, à côté de `zone_repository.py`/`app.py`)** :
- `diagnostiquer_doublons_pays_entier.py` — voir usage détaillé ci-dessus.
- `retirer_entree_parasite_zones_pays.py` — `--scenario X --entite "Y" [--execute]`.

**Rapports générés (à conserver, contenu narratif)** :
- `rapport_portions_retirees_13sept.md` (fortress_world)
- `rapport_portions_eco_communalism_13sept.md`

## Non traité hérité
- P20 (service de génération d'images externe) — toujours en attente.
- Trou connu du 10 sept (renommage de zone ne migre pas les overlays
  dessinés) — non recroisé cette session, sauf vérification ponctuelle
  ANZES (rien à migrer dans ce cas précis).
- Points géographiques hérités du 12 sept (Nordgard/Corridor d'Amsterdam/
  Zone de Koursk à confirmer créées, overlay Allemagne mal renseigné,
  injection personnages Hyphan, `tensions_internes`/`periode_transition`
  vides sur Zone Interdite de Heysham) — non touchés cette session.
