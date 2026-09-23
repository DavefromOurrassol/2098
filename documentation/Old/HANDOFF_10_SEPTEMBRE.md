# HANDOFF — 9-10 septembre 2026

## Fait

### Renommage Interzone → Zone Euro Sud
Discussion de nommage (anglais, latin, réminiscence Union européenne),
nom retenu : **Zone Euro Sud** (slug `zone_euro_sud`). Appliqué via le
bouton ✏️ **Renommer** du GUI (rapport d'impact affiché avant confirmation :
2 sous-zones enfants — Plaine de Pannonie, Zone Tampon Balkano-Caucasienne
— + pays dans `zones_pays.json`). **Point non vérifié** : le rapport
d'impact affichait 22 pays alors qu'un chiffre de 23 avait été noté en
mémoire lors de la création de la zone le 8 septembre — écart jamais
tranché (voir Reste à faire).

**Découverte en cours de route** : le GUI a une fonction ✏️ **Renommer**
dédiée pour les zones N1 depuis le 13 juillet (chantier P7), que Claude ne
connaissait pas — a d'abord proposé un script de renommage ad hoc
(`rename_zone_interzone.py`) avant de la découvrir en lisant
`USER_MANUAL_COMPLET.md`. **Ce script est à ignorer**, obsolète dès sa
création — le bouton du GUI fait tout ce qu'il faut (slug/nom, enfants,
wikilinks, `relations.allies/rivaux`, `instances/*.md`, `zones_pays.json`).

### Bug Royaume-Uni — désaffectation qui ne tenait pas
David a tenté de désaffecter "Royaume-Uni" de Zone Interdite de Heysham
via le bouton ↩️ Désaffecter du GUI — l'entrée réapparaissait affectée à
chaque rechargement malgré une écriture confirmée correcte dans
`zones_pays.json` (`"Royaume-Uni": null` bien présent côté `fortress_world`).

**Cause trouvée** : l'`origine_reelle` de Zone Interdite de Heysham
contenait toujours une entrée `- entite: Royaume-Uni` (en plus
d'Angleterre/Pays de Galles) — `regenerate_zones_pays.py`, lancé même
indirectement, retrouve cette entrée et réaffecte le pays, écrasant
silencieusement toute désaffectation manuelle. Anomalie structurelle
trouvée au passage sur cette même zone : 5 des 7 entrées `origine_reelle`
(Pays de Galles, Royaume-Uni, Irlande, Belgique, Luxembourg) n'avaient
que le champ `entite`, sans `type_entite`/`portion` (contrairement à
France/Angleterre) — même famille de malformation que celle corrigée le
31 juillet sur `lieux_emblematiques`.

**Corrigé** : entrée "Royaume-Uni" retirée de l'`origine_reelle` de Zone
Interdite de Heysham (`fix_remove_uk_heysham.py`, `.bak` + dry-run,
appliqué par David). Vérifié avec
`generator/regenerate_zones_pays.py --dry-run` : `fortress_world (0
changement(s))` après le fix — confirmé stable.

**Drift préexistant repéré au passage, sans rapport avec ce bug** : le
même `--dry-run` a signalé 6 changements sur `breakdown` (Groenland,
Arctique) et `reference` (Italie, Kirghizistan, Tadjikistan,
Afghanistan) — `zones_pays.json` désynchronisé de leurs fiches
géographie respectives sur ces scénarios. **Pas touché**, hors sujet du
jour — à traiter si besoin un jour (voir Reste à faire).

### Overlays GeoJSON — suite du chantier du 8 septembre
- **Créer une nouvelle zone directement en dessinant un overlay** :
  jusqu'ici `_promptZoneSlug()` (app.js) n'offrait que les zones
  existantes. Ajout d'une option "+ Créer une nouvelle zone niveau 1…"
  en tête de liste, qui appelle la route `/api/carte/creer_zone_vide`
  (existante, déjà testée pour S11, jamais branchée à ce flux). Aucun
  changement backend nécessaire.
- **`TopologyException: side location conflict` (GEOS)** sur
  `zone_dessin_complet.py` (S11) — un tracé à main levée englobant à la
  fois terres et océans s'auto-intersectait, geometrie invalide refusée
  par GEOS à l'intersection. **Corrigé** : nouvelle fonction
  `reparer_geometrie()` (idiome Shapely `.buffer(0)`), appliquée au
  polygone dessiné et défensivement à chaque géométrie pays dans
  `couverture_pct()`.

### Personnalisation visuelle de zone (couleur/motif) — rapatriement de branche
David a fourni une ancienne paire `app.py`/`app.js` ("obsolète") qui
portait une fonctionnalité construite le 8 septembre sur une branche
ayant divergé de la branche principale avant l'arrivée de S11
(`creer_zone_vide`, dessin de zone complète, etc.) — la branche
principale n'avait donc jamais reçu la personnalisation, et la branche
personnalisation n'avait jamais reçu S11.

**Rapatrié par Claude** (diff ciblé bloc par bloc, `.bak`, testé en
dry-run contre les vrais fichiers avant application, vérifié par diff
exact + compilation/syntaxe) :
- `app.js` : bibliothèque `MOTIFS_ICONES`/`MOTIFS_LABELS` (radiation,
  flamme, vague, crâne), `_zoneFill()` avec priorité au motif
  personnalisé, bouton "🎨 personnaliser" + panneau dans l'arbre de
  sous-zones, badge motif dans la légende.
- `app.py` : `_scan_zones_carte()` avec couleur/motif custom
  (`_couleur_custom`/`_motif_custom`, prennent le pas sur le calcul
  automatique), nouvelle route `/api/carte/personnaliser_zone`,
  `_build_zone_tree()` expose `couleur`/`motif` bruts.

**Étendu ensuite (demande de David)** :
- Couleur/motif éditables aussi via le menu ✏️ à droite de la légende
  (pas seulement dans l'arbre) — `openRenommerZonePanel()` étendue
  (devenue asynchrone, va chercher la valeur réelle
  couleur/motif — pas la couleur calculée — via `/api/carte/arbre_zone`
  avant affichage, pour que la case "auto" reflète le vrai état).
- Motif explicite "sans hachure" (`aucun`), distinct de l'option vide
  qui signifiait "automatique" — ambiguïté remontée par David en test
  réel. Ajouté à `MOTIFS_VALIDES` (app.py) et `MOTIFS_LABELS` (app.js,
  "⬜ Uni (sans hachure)"), libellé de l'option vide clarifié
  ("— automatique (hachures si nécessaire) —").

## Bugs trouvés

- **✏️ Renommer ne propage pas vers les tracés d'overlay dessinés**
  (`gui/static/geo_overlays/{scenario}.geojson`) — sur le renommage
  Interzone → Zone Euro Sud, 7 des 8 features overlay taguées
  `zone_slug: interzone` ont été migrées vers `zone_euro_sud`, **1 est
  restée orpheline** avec l'ancien slug. Découvert en diffant le fichier
  actuel contre son `.bak` (12 vs 13 features) après que David a
  supprimé cette entrée orpheline en pensant qu'elle appartenait à
  Interzone Corridor (voir ci-dessous) — suppression sans conséquence
  réelle (fragment déjà couvert par les 7 autres correctement migrées).
  **Pas corrigé dans le code**, juste identifié — à garder en tête pour
  tout futur renommage de zone ayant des overlays dessinés.
- **Personnalisation "Appliqué" mais rien ne change visuellement sur la
  carte** — en réalité deux zones différentes en jeu, confusion de David
  entre elles (voir Décisions actées / Interzone Corridor). La route
  d'écriture fonctionne (couleur bien enregistrée dans `fortress_world.md`
  dans les deux cas observés) — le vrai problème identifié est ailleurs
  (tracé jamais enregistré, voir ci-dessous).

## Décisions actées

- **Interzone Corridor** (`interzone_corridor`) : zone découverte le 10
  septembre dans `fortress_world.md`, créée par David entre deux
  sessions sans que Claude en ait connaissance — corridor tampon Espace
  Nordique et Arctique / Zone Interdite de Heysham (République tchèque,
  Slovaquie, Biélorussie, Pays-Bas, Allemagne, Hongrie, Ukraine, Russie
  dans `origine_reelle`). Sa couleur personnalisée (`#ababab`) est bien
  écrite dans `fortress_world.md`, **mais son tracé (overlay) n'a jamais
  été enregistré côté serveur** — absent à la fois du fichier overlay
  actuel et de son `.bak`. À redessiner en sélectionnant bien "Interzone
  Corridor" dans le picker de zone (pas l'entrée orpheline "Interzone" —
  voir bug ci-dessus, source de la confusion initiale de David).
  **Non résolu à la fin de cette session.**
- `rename_zone_interzone.py` (script ad hoc écrit avant la découverte du
  bouton ✏️ Renommer) : **abandonné**, jamais utilisé, à ignorer si
  retrouvé dans le dossier `generator/`.

## Reste à faire

- **Redessiner le tracé d'Interzone Corridor** (voir ci-dessus) — priorité
  immédiate, zone actuellement invisible sur la carte malgré des données
  correctement enregistrées.
- **Vérifier le nombre de pays de Zone Euro Sud** (22 vus dans le
  rapport d'impact du renommage vs 23 attendus d'après la mémoire du 8
  septembre) — jamais tranché, la conversation est partie sur autre
  chose avant vérification.
- Écrire les textes `portion` du partage France (Zone Euro Sud / Zone
  Interdite de Heysham) — toujours en attente depuis le 8 septembre.
- Peupler Corridor d'Amsterdam (coquille vide, aucun pays) — toujours
  en attente depuis le 8 septembre.
- Créer Nordgard et Zone de Koursk dans le vault réel — toujours
  absentes (à reconfirmer en début de session plutôt que supposer, vu la
  découverte d'Interzone Corridor créée sans trace côté Claude).
- Injecter dans le vault les personnages/entités/événements extraits du
  texte Hyphan (liste déjà faite le 8 septembre, jamais transformée en
  fiches réelles).
- `tensions_internes`/`periode_transition` toujours vides sur Zone
  Interdite de Heysham.
- `check_overlay_portion_coherence.py` toujours pas intégré au GUI
  (David veut le déboguer en conditions réelles d'abord).
- **S11 — panneau GUI de dessin de zone complète** : le calcul
  (`zone_dessin_complet.py`, corrigé le 9 septembre pour les géométries
  invalides) fonctionne en conditions réelles, mais le panneau GUI
  dessin+review+application (route
  `/api/carte/dessiner_zone_complete/proposer`) reste à construire.
- Overlay Allemagne créé sur le mauvais pays (Norvège au lieu
  d'Allemagne, hérité du 8 septembre) — statut non revérifié cette
  session.
- **Drift `zones_pays.json` sur `breakdown` (Groenland, Arctique) et
  `reference` (Italie, Kirghizistan, Tadjikistan, Afghanistan)** —
  repéré en marge du fix Royaume-Uni via
  `regenerate_zones_pays.py --dry-run`, pas d'incidence sur
  `fortress_world`, pas traité (hors sujet du jour, aucune urgence
  identifiée).
- Piège Royaume-Uni/Angleterre/Écosse/Pays de Galles (polygone partagé)
  — toujours pas corrigé dans le code, hérité du 8 septembre.

## Fichiers livrés

- `app.py` — route `/api/carte/creer_zone_vide` branchée au flux overlay
  (aucun changement backend nécessaire pour ce point précis),
  personnalisation couleur/motif rapatriée (`_scan_zones_carte`, route
  `/api/carte/personnaliser_zone`, `_build_zone_tree`), motif `aucun`
  ajouté à `MOTIFS_VALIDES`.
- `app.js` — option "+ Créer une nouvelle zone niveau 1…" dans le flux de
  dessin d'overlay, personnalisation couleur/motif rapatriée (bouton
  arbre + panneau), couleur/motif éditables depuis le menu ✏️ de la
  légende, motif "⬜ Uni (sans hachure)" ajouté.
- `generator/zone_dessin_complet.py` — fix géométrie invalide
  (`reparer_geometrie()`, idiome `.buffer(0)`).
- `fix_remove_uk_heysham.py` (ponctuel, `generator/` ou racine — au choix
  de David) — retire l'entrée Royaume-Uni de l'`origine_reelle` de Zone
  Interdite de Heysham. **Appliqué**, à ne pas relancer.
- `rename_zone_interzone.py` — livré puis rendu obsolète en cours de
  session (voir Décisions actées), jamais appliqué.
- `BACKLOG_ACTIF.md` (mis à jour — chantiers #1 et #2 actualisés).

## Non traité hérité

- P20 (service de génération d'images externe) — toujours en attente de
  choix, pas touché cette session.
- Secondaire S1-S10 (voir `BACKLOG_ACTIF.md`) — pas touché cette session.
