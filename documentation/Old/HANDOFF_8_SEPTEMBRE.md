# HANDOFF — 8 septembre 2026

## Fait

### Chantier "Scénario 1 — Hyphan" — worldbuilding géographique (en cours)
David a fourni le premier jet narratif du scénario Hyphan (fichier .docx),
avec cartes annexes (vue monde + vue Europe collées, capture d'itinéraire
Toulouse→Barcelone). Extraction complète des candidats à l'injection
(personnages, entités génériques/instances, événements, zones) depuis le
texte — liste donnée à David, **pas encore transformée en fiches réelles
dans le vault**.

Scénario porteur tranché : **fortress_world** (breakdown envisagé puis
écarté — déjà un lore incompatible établi sur les mêmes territoires,
Occitanie/Cellules Racines-Mères notamment, qui aurait entré en collision
directe avec Interzone/sud de la France).

Zones nommées et actées au fil de la session :
- **Al-Hima** — créée via GUI (`✂️ Scinder` Bloc Atlantique → Espagne,
  Portugal, Maroc, Algérie), description rédigée (confédération
  collectiviste des deux rives, climat désertique à oasis, principe
  pré-islamique du hima). `union_regionale`, `emergent`.
- **Zone Interdite de Heysham** — créée par David via Scinder (Angleterre +
  France extraites de Bloc Atlantique). Remplace le nom "Zone de
  Hartlepool" discuté plus tôt en session (accident nucléaire ~2044,
  centrale de Heysham 2 plutôt que Hartlepool). `zone_sinistree`,
  `en_declin`.
- **Nuuk-Forteresse** — reparentée sous **Espace Nordique et Arctique**
  (niveau 1 → niveau 2), à la demande de David : cohérence thématique,
  Espace Nordique et Arctique est déjà modélisée comme contrôlée par un
  opérateur privé armé (Nordisk Arktisk Transitkontroll), même principe
  qu'Ergo-Wian.
- **Nordgard** — tranchée **niveau 1** (pas sous Bloc Atlantique ni sous
  Espace Nordique et Arctique comme envisagé un temps), Pays-Bas comme
  point de départ. Étapes de création données à David, **pas confirmée
  créée dans le vault réel**.
- **Corridor d'Amsterdam**, **Interzone**, **Zone de Koursk** — discutées,
  nommées, description rédigée pour Corridor d'Amsterdam (couloir tampon
  entre Nordgard et une zone irradiée) ; **pas confirmées créées** dans le
  vault réel au moment du handoff.
- **Allemagne** — décision actée : partagée entre Espace Nordique et
  Arctique et Corridor d'Amsterdam via le mécanisme d'overlay dessiné (pas
  de pseudo-pays façon Royaume-Uni/Angleterre). Mise en œuvre commencée,
  **une erreur de pays à corriger** (voir Bugs trouvés).

### Chantier "Overlays GeoJSON + améliorations Carte" — gros chantier multi-bugs
Parti d'une question de David (zones qui coupent un pays en deux) — a mené
à un audit complet du système de coloriage de carte (`world.geo.json`,
granularité pays-entier confirmée par lecture de `app.py`/`app.js`/
`USER_MANUAL_COMPLET.md`) puis à la construction d'un système de polygones
custom dessinés à la main, et à la correction de plusieurs trous/bugs
trouvés en cours de route dans l'onglet Carte existant (pas seulement le
nouveau chantier).

**Backend (`app.py`)** :
- `GET /api/carte/overlays` (lecture), `POST /api/carte/overlays/creer`,
  `POST /api/carte/overlays/supprimer`
- `GET /api/carte/zones_toutes` — liste plate tous niveaux, pour peupler
  des listes déroulantes GUI plutôt qu'une saisie de slug à la main
- `_scan_zones_carte()` — nouvelle fonction, distincte de
  `_scan_n1_zones_with_desc` (conservée telle quelle pour
  `/api/carte/propose`, qui ne doit jamais suggérer une sous-zone comme
  cible pour un pays entier) — couleur unifiée niveau 1 + zones overlayées
  sur une seule roue de teintes, zéro collision
- `GET /api/carte/zones_manquantes_enrichissement`,
  `POST /api/carte/generer_enrichissement_zone`,
  `POST /api/carte/appliquer_enrichissement_zone` — comble
  `tensions_internes`/`periode_transition` vides sur une zone créée par
  split (jamais rempli par aucun script existant, confirmé par lecture de
  `build_geographie_monde.py`/`enrich_geographie_recursive.py` : les deux
  ne créent que des zones neuves, aucun des deux ne complète une zone
  déjà existante)
- `POST /api/carte/desaffecter` — bouton manquant trouvé en cours de
  session, aucun moyen de repasser un pays à "Non affecté" une fois
  assigné (le bouton "Ignorer" existant sert à tout autre chose : marquer
  un pays *non encore affecté* comme blanc intentionnel)
- Fix `_apply_reparent_zone` : ne synchronisait jamais `zones_pays.json`
  (bug trouvé sur Nuuk-Forteresse → le Groenland restait bleu générique
  après le reparentage niveau 1 → niveau 2). Nouvelles fonctions
  `_sync_zones_pays_after_reparent()`, `_zone_niveau1_ancestor()`.
- `/api/carte/overlays/creer` écrit maintenant directement l'entrée
  `origine_reelle` manquante dans la zone cible (portion demandée à
  l'utilisateur au moment du dessin), au lieu de se contenter d'avertir
  que l'entrée manque

**Frontend (`app.js`/`index.html`)** :
- Interface de dessin (Leaflet.Draw, dépendance externe ajoutée en CDN
  dans `index.html`) : bouton "✏️ Dessiner un overlay", outil polygone
  démarré automatiquement à l'activation (évite un clic superflu sur
  l'icône du contrôle Leaflet.Draw)
- Panneau "🧬 Zones à enrichir" (génération LLM + application séparées en
  deux appels, review humaine avant écriture — même doctrine que le
  top-down existant)
- Panneau "🗑️ Gérer les overlays" (liste + suppression par bouton,
  volontairement indépendant du mode dessin)
- Bouton "↩️ Désaffecter" dans le panneau pays (visible seulement si le
  pays est déjà affecté à une zone)
- Liste déroulante de vraies zones (remplace un champ de saisie libre du
  slug) dans `✂️ Scinder`, mode "zone existante"
- Bouton "↗️ déplacer" désormais visible aussi sur la racine de l'arbre
  affiché — trou trouvé : une zone niveau 1 ouverte depuis la légende
  (toujours racine dans ce contexte) ne pouvait jamais être reparentée, le
  bouton était masqué par design uniquement sur les nœuds racine
- Le remplissage "pays entier" ne se désactive plus quand un overlay
  existe pour ce pays — corrigé pour permettre le vrai cas d'usage
  demandé par David (portion dessinée visible en plus de la couleur
  d'origine du reste du pays, pas un remplacement du pays entier)

**Nouveau script** : `enrich_zone_manquante.py` (`generator/`), mode
`--json` pour appel GUI en sous-processus (même doctrine que
`zoning_topdown.py` : génération et application séparées).

## Bugs trouvés

- **`_apply_reparent_zone` ne synchronisait pas `zones_pays.json`** — une
  zone niveau 1 rétrogradée en sous-zone laissait `zones_pays.json`
  pointer vers un slug qui n'est plus niveau 1 ; `_scan_zones_carte()` ne
  lui trouve alors plus de couleur (retombe sur le bleu générique).
  **Corrigé.**
- **`_promptPays` (app.js) lisait `data.origine_reelle` au lieu de
  `data.arbre.origine_reelle`** — `/api/carte/arbre_zone` renvoie sa
  réponse imbriquée sous la clé `arbre`, jamais à plat. Résultat : liste
  de pays toujours vide au moment de dessiner un overlay, malgré une
  `origine_reelle` bien remplie côté serveur. **Corrigé.**
- **Conflit de clic entre le mode dessin et la suppression d'overlay** —
  depuis que l'outil polygone démarre automatiquement en mode dessin,
  chaque clic pose un sommet au lieu d'atteindre le gestionnaire de clic
  de la couche overlay en dessous. La suppression "au clic sur la carte"
  prévue initialement ne fonctionne plus. **Corrigé** en remplaçant par un
  panneau liste dédié, indépendant du mode dessin.
- **Royaume-Uni/Angleterre/Écosse/Pays de Galles partagent un seul
  polygone GeoJSON** (mécanisme préexistant, pas nouveau) — piège
  rencontré en pratique : extraire "Angleterre" seule d'une zone via
  Scinder ne suffit pas à changer la couleur affichée si "Royaume-Uni"
  (entrée séparée, même polygone) reste affecté à l'ancienne zone — le
  code de rendu prend la première affectation non nulle trouvée parmi les
  4 noms partageant le polygone. **Pas corrigé dans le code** (c'est le
  comportement du mécanisme multi-noms lui-même, pas un bug isolé) — juste
  identifié et contourné manuellement par David (réaffectation explicite
  de "Royaume-Uni" en plus d'"Angleterre"). À garder en tête si le même
  piège touche Écosse/Pays de Galles plus tard.
- **Overlay créé sur le mauvais pays** (David, fin de session) — en
  choisissant un pays dans la liste déroulante des pays déjà connus de la
  zone plutôt que "✏️ Autre pays (saisie libre)", un dessin destiné à
  l'Allemagne a été enregistré comme couvrant la Norvège. Pas un bug de
  code, un piège d'interface (l'option "Autre pays" est en dernière
  position de la liste, pas mise en évidence). **Pas corrigé** — à
  reprendre si ça se reproduit (ex. mettre "Autre pays" en tête de liste).

## Décisions actées

- `check_overlay_portion_coherence.py` (script de diagnostic, cohérence
  entre le texte narratif `portion` et le dessin de l'overlay) :
  **volontairement pas encore intégré au GUI** — David veut le déboguer
  d'abord en conditions réelles avant de l'ajouter comme étape optionnelle
  de `scan_geographie_complet.py`.
- Espagne/Maroc (chevauchement Al-Hima / Bloc Atlantique / Zones Grises et
  Tampons) : tranché en faveur d'un split propre via `✂️ Scinder` (pas de
  coexistence narrative façon Interzone/France) — fait.
- Allemagne : partagée entre Espace Nordique et Arctique et Corridor
  d'Amsterdam via le mécanisme d'overlay dessiné plutôt que des pseudo-pays
  (Allemagne-Nord/Allemagne-Sud envisagés puis écartés, l'overlay faisant
  tout ce qu'il faut plus simplement).
- Nordgard : confirmée zone **niveau 1** — Pays-Bas comme point de départ
  pour le split.
- Zone Interdite de Heysham remplace "Zone de Hartlepool" (nom provisoire
  utilisé en tout début de discussion sur les zones irradiées) — accident
  nucléaire recentré sur Heysham 2 plutôt que Hartlepool.
- **France partagée entre Interzone et Zone Interdite de Heysham** :
  confirmé volontaire par David (pas une erreur à corriger) — reste à
  écrire un texte `portion` clair des deux côtés (voir Reste à faire),
  actuellement vide côté Heysham et juste répétitif côté Interzone
  ("France - Interzone", ne décrit rien de géographique).
- Outil de dessin de zone complète avec détection automatique multi-pays
  (calcul d'intersection géométrique, split auto sur pays entièrement
  couverts, overlay sur pays partiellement couverts, description
  enrichie via Natural Earth + LLM) : **conception documentée, pas
  commencée** — consignée en détail dans `BACKLOG_ACTIF.md` (S11) plutôt
  qu'attaquée cette session, chantier de fond distinct de ce qui a été
  codé aujourd'hui.

## État réel vérifié en fin de session (croisement `zones_pays.json` +
`fortress_world.md` envoyés par David)

- **Al-Hima** — cohérente des deux côtés (4 pays), rien à signaler.
- **Zone Interdite de Heysham** — cohérente (8 pays des deux côtés,
  Royaume-Uni/Pays de Galles bien inclus suite au piège du polygone
  partagé). `tensions_internes`/`periode_transition` **toujours vides**.
- **Interzone** — existe bel et bien (23 pays), **et a été enrichie entre
  deux uploads de David** (`tensions_internes`/`periode_transition`
  remplis) — première confirmation en conditions réelles que le panneau
  "🧬 Zones à enrichir" fonctionne de bout en bout (génération LLM +
  écriture), jusque-là non testé de mon côté faute d'accès à une vraie
  clé API.
- **Espace Nordique et Arctique** — l'entrée "Allemagne" est bien
  présente dans `origine_reelle` **sans** apparaître dans
  `zones_pays.json` pour cette zone : confirme que le mécanisme d'overlay
  fonctionne exactement comme conçu (portion ajoutée au texte sans
  déplacer le pays entier sur la carte). "Cap-Vert", présent avant la
  session, a disparu de `origine_reelle` — **origine inconnue, pas
  d'action de ma part qui l'explique**, à clarifier avec David si besoin.
- **Corridor d'Amsterdam** — existe comme zone (description/type/statut
  remplis) mais **aucun pays** ni dans `origine_reelle` ni dans
  `zones_pays.json` — coquille vide.
- **Nordgard** et **Zone de Koursk** — confirmées **absentes** des deux
  fichiers, jamais créées malgré la discussion.

## Reste à faire

- Écrire les textes `portion` du partage France (Interzone / Zone
  Interdite de Heysham) — propositions faites à David en fin de session,
  pas confirmées appliquées.
- Peupler Corridor d'Amsterdam (coquille vide, aucun pays).
- Créer Nordgard et Zone de Koursk dans le vault réel — toujours
  absentes, confirmé par croisement des fichiers en fin de session.
- Corriger l'overlay Allemagne/Norvège si pas déjà fait (supprimer via
  "🗑️ Gérer les overlays", refaire avec la nouvelle liste déroulante
  unifiée).
- Injecter dans le vault les personnages/entités/événements extraits du
  texte Hyphan en tout début de session (liste donnée, jamais transformée
  en fiches réelles).
- `check_overlay_portion_coherence.py` à déboguer en conditions réelles
  avant intégration GUI (voir Décisions actées).
- Outil de dessin de zone complète (détection auto multi-pays, Natural
  Earth) — voir `BACKLOG_ACTIF.md` S11, conception seulement.
- P20 (service de génération d'images externe) — toujours en attente de
  choix, hérité, pas touché cette session.
- Secondaire S1-S10 (voir BACKLOG_ACTIF.md) — pas touché cette session.

## Fichiers livrés

- `app.py` (routes overlays lecture/écriture/suppression, zones_toutes,
  enrichissement de zone, désaffecter, fix reparent → zones_pays.json)
- `app.js` (interface de dessin Leaflet.Draw, panneaux enrichissement et
  gestion des overlays, liste déroulante unifiée pour le choix du pays
  lors du dessin d'un overlay — remplace l'ancienne liste "pays connus +
  Autre en dernier" source d'erreur de sélection, fixes divers listés
  ci-dessus)
- `index.html` (librairie Leaflet.Draw en CDN, boutons "Dessiner un
  overlay" / "Zones à enrichir" / "Gérer les overlays")
- `enrich_zone_manquante.py` (nouveau, `generator/`) — **confirmé
  fonctionnel en conditions réelles** (voir État réel vérifié ci-dessus)
- `check_overlay_portion_coherence.py` (nouveau, `generator/`, **pas
  encore intégré au GUI** — voir Décisions actées)
- `BACKLOG_ACTIF.md` (mis à jour — 2 nouveaux chantiers actifs en tête,
  nouvelle entrée S11)

## Non traité hérité

- P20, S1-S10 (voir BACKLOG_ACTIF.md) — inchangé cette session.
