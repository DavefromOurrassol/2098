# HANDOFF — 14 septembre 2026

Suite directe de `HANDOFF_13_SEPTEMBRE.md`. Deux volets : (1) finir le
scan des doublons "pays entier" sur les deux scénarios restés non
touchés la veille (`policy_reform`, `reference`), corriger un bug
structurel trouvé au passage ; (2) construire et tester en conditions
réelles l'intégration GUI de l'outil de diagnostic, demandée
explicitement par David en fin de session du 13.

## Fait

### Scan `policy_reform` — bug #6 trouvé et corrigé
Le rapport texte de `diagnostiquer_doublons_pays_entier.py --scenario
policy_reform` (lecture seule) ne listait que 2 racines en conflit
pour la Corée du Sud (`espace_eurasiatique` conservée,
`zone_pacifique_industrielle` résidu probable). Lancer le nettoyage
ciblé en dry-run révélait une **troisième** racine jamais mentionnée
dans le rapport : `inde_corree_noeud_pacte` — sous-zone niveau 2 de
`espace_eurasiatique` elle-même, donc pas un vrai conflit. Vérification
dans `geographie/policy_reform.md` : rattachement narratif volontaire
et documenté ("Inde-Corée du Sud (nœud eurasiatique du Pacte)"),
texte substantiel sur le rôle des deux pays comme frange coopérative
de l'espace eurasiatique.

**Cause** : `retirer_doublons_pays_entier()` (`zone_repository.py`)
bouclait sur toutes les zones et n'excluait que le slug exact
`slug_a_conserver` — aucune vérification de lignée N1. Même classe de
bug que le v1 de `diagnostiquer_doublons_pays_entier.py` (13 sept),
jamais porté dans la méthode d'écriture, alors que l'utilitaire
nécessaire (`_zone_niveau1_ancestor()`) existait déjà dans le fichier.

**Corrigé** : filtre ajouté — toute zone dont la racine N1 est la
même que celle de `slug_a_conserver` est désormais exclue du
nettoyage. Vérifié en dry-run après patch : seule
`zone_pacifique_industrielle` apparaît, `inde_corree_noeud_pacte`
n'est plus listée. Nettoyage exécuté avec succès sur Corée du Sud +
Pays-Bas (`hub_europeen_regulation`, cas simple non affecté par ce
bug). `policy_reform` confirmé propre au rescan.

### Scan `reference` — 6 cas, tous des rattachements narratifs volontaires
6 cas PAYS RÉELS + 1 entité non reconnue détectés. **Aucun nettoyage
effectué** après vérification manuelle de `geographie/reference.md` :
tous les cas suivent le même schéma qu'`inde_corree_noeud_pacte` —
un pays a un rattachement territorial "de base" et appartient en plus
à une zone thématique transversale qui le traverse narrativement
(zones grises sahéliennes pour Burkina Faso/Niger/Soudan/Tchad,
réseau d'institutions multilatérales pour Kenya/Suisse via des
entités composées "Nairobi, Kenya"/"Genève, Suisse" correctement
résolues par `_resoudre_entite()`). L'entité non reconnue, `Arctique
russe (Mourmansk)`, s'est avérée le cas le plus explicite des 7
rencontrés cette session : la fiche de la sous-zone `Mourmansk`
décrit littéralement la ville comme "zone de contact" disputée entre
deux blocs — le sujet narratif central de la zone, pas un résidu.
`reference` confirmé propre (aucune action nécessaire).

`new_sustainability` rescanné en confirmation (nettoyage Danemark/
Groenland de la veille) : propre. **Les 6 scénarios sont désormais
tous scannés.**

### Bug #5 — garde-fou `zones_pays.json` corrigé
`retirer_doublons_pays_entier()` écrivait `zones_pays.json`
inconditionnellement (`sc[pays] = slug_a_conserver`), créant une clé
parasite pour toute entité hors `pays_liste` (villes, régions
fictives, entités composées type "Danemark / Groenland", "Balkans
occidentaux") — bug connu depuis le 13 sept, contourné mais pas
corrigé à la racine. **Corrigé** sur le même principe que
`creer_zone_n1()` : résolution de `pays` contre
`zones_pays.json["pays_liste"]` (normalisation `_normalise_pays`),
synchronisation `zones_pays.json` seulement sur match exact.

### Relecture des rapports de portions retirées (13 sept)
`rapport_portions_eco_communalism_13sept.md` : vide, rien perdu.
`rapport_portions_retirees_13sept.md` (fortress_world) : 7 textes
relus, 6 substantiels (Allemagne, Belgique, Biélorussie, Pays-Bas,
République tchèque, Slovaquie) identifiés comme candidats à un
redessin en overlay si pertinent un jour, 1 quasi vide (Russie,
placeholder générique, rien à préserver). **Décision de David : sujet
fermé, aucun redessin engagé pour l'instant.**

### Intégration GUI de l'outil de diagnostic — construite et testée
Demande explicite de David (13 sept) : liste de propositions
cochables/approuvables, jamais de slug/nom à taper à la main. Choix
d'architecture : réutilisation du système existant
`chantiers_geographie.yaml`/onglet Chantiers (construit le 25-26
juillet pour `pays_sans_zone`/`zone_suspecte`) plutôt qu'un nouvel
écran — nouveau type `doublon_pays_entier` ajouté au même système.
Répond aux deux décisions non tranchées du 13 sept (pas de nouvel
onglet, les deux granularités de review existent déjà).

Différence clé avec les deux types existants : la proposition n'est
jamais générée par un LLM à la demande — calculée de façon
déterministe et attachée dès l'écriture du chantier
(`diagnostiquer_doublons_pays_entier.py --write-chantiers`, via
`zones_portant_un_pays()`). Champ d'application volontairement
restreint aux cas non ambigus (une seule correspondance
`zones_pays.json`, même critère que `--nettoyer-auto`) — les entités
non reconnues et les cas ambigus ne génèrent jamais de chantier
automatique. Chaque proposition inclut un `contexte_narratif`
(premiers ~220 caractères de la description de la zone retirée),
affiché directement dans la ligne du chantier — pensé pour éviter de
reproduire en un clic un cas comme `inde_corree_noeud_pacte`.

**Testé en conditions réelles, cycle complet** (doublon artificiel
France sur `afrique_centrale_australe`/`breakdown`, en plus de
`arc_sahelo_mediterraneen` déjà légitime, créé et retiré au cours du
test) :
1. `--write-chantiers` détecte et écrit le chantier avec proposition
   correcte.
2. Ligne visible dans l'onglet Chantiers, badge "Doublon pays-entier",
   proposition affichée avec `contexte_narratif` lisible.
3. Filtre Type : option manquante trouvée et corrigée en session
   (`index.html`).
4. Approbation : bouton "✓ Appliquer ce chantier" apparaît seulement
   après, comme attendu.
5. Application : entrée `origine_reelle` en trop retirée de
   `afrique_centrale_australe`, `arc_sahelo_mediterraneen` intact,
   `zones_pays.json["breakdown"]["France"]` correctement synchronisé
   (valide le bug #5 sur le cas "match trouvé").
6. Rescan : "Aucun doublon... détecté" — confirmé.

Doublon de test retiré de `chantiers_geographie.yaml` et vault restauré
à un état légitime après le test (voir Reste à faire pour ce qui n'a
pas pu être re-testé).

## Bugs trouvés
6. `retirer_doublons_pays_entier()` : filtre de lignée N1 absent —
   une sous-zone légitime de la même racine N1 que `slug_a_conserver`
   était traitée comme une racine concurrente non apparentée —
   **corrigé** (`_zone_niveau1_ancestor()`, déjà présent dans le
   fichier, jamais branché sur cette méthode). Testé en dry-run réel
   (Corée du Sud/policy_reform) et en application réelle (test France/
   breakdown).
7. `retirer_doublons_pays_entier()` : écrivait `zones_pays.json`
   inconditionnellement pour toute entité, y compris hors
   `pays_liste` — **corrigé** (résolution contre `pays_liste` avant
   toute synchronisation, même principe que `creer_zone_n1()`). Testé
   sur le cas "match trouvé" (France, vrai pays) ; **cas "aucun
   match" non re-testé** (voir Reste à faire) — c'est pourtant la
   branche qui corrige effectivement le bug d'origine.
8. `index.html` : filtre Type de l'onglet Chantiers sans option pour
   le nouveau type `doublon_pays_entier` (oubli de la première passe
   d'intégration GUI, trouvé en testant le filtre en navigateur) —
   **corrigé**.

## Décisions actées
- Sujet "rapports de portions retirées" fermé sans redessin (voir
  ci-dessus).
- Intégration GUI : réutilisation du système `chantiers_geographie.
  yaml`/onglet Chantiers plutôt qu'un nouvel écran, nouveau type
  `doublon_pays_entier`. Champ d'application volontairement restreint
  aux cas non ambigus — jamais de chantier automatique pour une
  entité non reconnue ou un cas ambigu.

## Reste à faire
- **Bug #5, branche "aucun match" non re-testée** — rejouer sur un
  cas réel hors `pays_liste` (ex. Balkans occidentaux, Danemark /
  Groenland) pour confirmer qu'aucune clé parasite n'est créée.
  `retirer_entree_parasite_zones_pays.py` reste utile pour nettoyer
  les clés parasites déjà présentes dans le vault (créées avant ce
  fix), mais ne devrait plus en générer de nouvelles.
- **Application en LOT non testée en navigateur** (bouton "Appliquer"
  global scenario/all, notamment mélangée avec des chantiers
  `pays_sans_zone`/`zone_suspecte` du même scénario) — seul le chemin
  "chantier isolé" (id) a été validé en conditions réelles.
- **`contexte_narratif` non échappé en HTML** dans `app.js` —
  cohérent avec le comportement préexistant des deux autres types
  (pas une régression), mais un texte narratif contenant `<` ou `&`
  casserait l'affichage. Jamais rencontré sur le vault réel à ce
  jour.
- **Backlog `pays_sans_zone`/`zone_suspecte` préexistant** (système
  du 25 juillet, indépendant de ce chantier) — état actuel non vérifié
  cette session, David a signalé qu'il restait des chantiers de ce
  type visibles dans l'onglet. À consulter en début de prochaine
  session :
  ```
  python3 -c "
  import yaml
  data = yaml.safe_load(open('documentation/need_action/chantiers_geographie.yaml').read())
  for c in data['chantiers']:
      if c.get('statut') == 'a_traiter':
          print(c['type'], '-', c['scenario'], '-', c['cible'])
  "
  ```
- **`diagnostiquer_doublons_pays_entier.py --write-chantiers` jamais
  lancé sur un vrai scénario** — seul le cas de test artificiel
  (France/breakdown) l'a exercé. Les 6 scénarios réels ont été
  nettoyés en CLI direct (`--nettoyer`/`--nettoyer-auto`) avant que
  le mode `--write-chantiers` n'existe, donc aucun chantier réel
  `doublon_pays_entier` n'est actuellement dans le vault — normal,
  pas une anomalie.

## Fichiers livrés
**Modifiés** :
- `zone_repository.py` — `retirer_doublons_pays_entier()` : filtre de
  lignée N1 (bug #6) + garde-fou `zones_pays.json` limité à
  `pays_liste` (bug #5). Reste du fichier inchangé par rapport à la
  version du 13 sept.
- `chantiers.py` (generator/) — type `doublon_pays_entier` ajouté à
  `TYPES_VALIDES`, schéma documenté dans le docstring du module.
- `app.py` (gui/) — import direct de `ZoneRepository`.
  `/api/chantiers/generer` rejette proprement `doublon_pays_entier`
  (pas de génération IA). `/api/chantiers/appliquer` applique
  directement via `retirer_doublons_pays_entier()` pour ce type
  (chantier isolé et en lot), au lieu du sous-processus
  `generer_zones_topdown.py --apply-topdown` qui l'ignore.
- `app.js` (gui/) — badge de type "Doublon pays-entier",
  `_chantiersFormatProposition()` enrichie pour afficher
  `slug_a_conserver`/`zones_a_retirer` + `contexte_narratif`.
- `index.html` (gui/) — option de filtre Type ajoutée.

**Nouveau** :
- `diagnostiquer_doublons_pays_entier.py` (gui/) — flag
  `--write-chantiers` : écrit un chantier par cas non ambigu, avec
  proposition pré-calculée et `contexte_narratif` par zone à retirer.
  Réimplémentation locale de l'écriture YAML (pas d'import de
  `generator/chantiers.py`, séparation de codebase gui/generator/
  déjà en vigueur ailleurs dans le projet).

## Non traité hérité
- P20 (service de génération d'images externe) — toujours en attente.
- Trou du 10 sept (renommage de zone ne migre pas les overlays
  dessinés) — non recroisé cette session.
- Points géographiques hérités du 12 sept (Nordgard/Corridor
  d'Amsterdam/Zone de Koursk à confirmer créées, overlay Allemagne mal
  renseigné, injection personnages Hyphan, `tensions_internes`/
  `periode_transition` vides sur Zone Interdite de Heysham) — non
  touchés cette session.
