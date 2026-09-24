# HANDOFF — 23 septembre 2026

Suite de `HANDOFF_14_SEPTEMBRE.md` (aucune session mémorisée entre le 14
et le 23). Session consacrée à fermer les chantiers #2, #2bis et #4 du
backlog. **Chantier #1 (Hyphan) mis en pause** sur décision de David en
début de session. #3 (P20, service d'image) non abordé.

Un incident git en cours de session (voir section dédiée) a été
entièrement réparé — **à lire avant toute nouvelle manipulation git**.

## Fait

### Revue des chantiers géographie (#4)
État de `chantiers_geographie.yaml` en début de session : 19 chantiers,
14 `a_traiter`, tous `zone_suspecte`. Tri proposé (à appliquer / à
ignorer / à lire), **non appliqué** — David a préféré traiter d'abord
#2/#2bis/#3/#4. Tri détaillé reporté dans `BACKLOG_ACTIF.md`, nouveau
chantier #4.

### Bug #5 — branche "aucun match" validée (#4)
Doublon artificiel `Balkans occidentaux` (`type_entite: autre`) placé dans
`afrique_centrale_australe` et `arc_sahelo_mediterraneen` (`breakdown`),
nettoyé via `diagnostiquer_doublons_pays_entier.py --nettoyer --pays
"Balkans occidentaux" --garder afrique_centrale_australe --execute`.
Résultat : entrée retirée d'`arc_sahelo_mediterraneen`, conservée sur
`afrique_centrale_australe`, **aucune clé dans `zones_pays.json`**. Bug #5
clos sur ses deux branches.

### Application en lot d'un chantier `doublon_pays_entier` validée (#4)
Doublon artificiel France (`afrique_centrale_australe` +
`arc_sahelo_mediterraneen`, `breakdown`) → `--write-chantiers` (id
`breakdown__france`, proposition correcte) → approbation → bouton global
"Appliquer les propositions approuvées" filtré sur `breakdown`. Entrée
retirée, `zones_pays.json["breakdown"]["France"] = arc_sahelo_
mediterraneen`, rescan : aucun doublon. Aucune erreur, chantier disparu de
la vue "À traiter". **Réserve** : le statut `traite` n'a pas été relu dans
le YAML avant la remise en état — à confirmer au prochain vrai chantier
de ce type.

### `app.js` — code mort, échappement HTML, "Zones à enrichir" (#2bis, #2)
Trois livraisons successives, toutes validées en navigateur par David :
1. Code mort retiré après analyse du graphe d'appels (acorn, y compris
   chaînes `onclick` et `index.html`) : `_ouvrirPersoPanel`,
   `_ouvrirSplitPanel`, `_carteImpactSplit`, `_carteSplitZone`.
   Échappement HTML (`_redactionEsc()`, déjà présente) de `cible`,
   `probleme` et de la proposition dans `renderChantierRow()` — couvre
   les trois types de chantier, pas seulement `contexte_narratif`.
2. `openOverlaysListePanel` (panneau "Gérer les overlays") supprimé sur
   décision de David (option B) : plus aucun bouton ne l'ouvrait depuis
   la refonte du 12 sept. Message d'erreur qui y renvoyait corrigé.
3. Panneau "🧬 Zones à enrichir" : la proposition LLM est désormais
   **éditable** avant application (3 champs, vide = `null`).

État final : 9 167 lignes + champs éditables (contre 9 478 au départ).

### `check_overlay_portion_coherence.py` — débogué et intégré (#2)
Premier passage en conditions réelles : annonçait "Aucun overlay" sur
`fortress_world` alors que le fichier existe. Trois bugs corrigés :
1. Chemin des overlays calculé relativement au dossier du script — le
   script vivait dans `generator/`, cherchait donc
   `generator/static/geo_overlays/`. Ancré désormais sur la racine du
   vault ; **script déplacé dans `gui/`** par David.
2. Sortie prématurée quand aucun overlay n'est trouvé → ne vérifiait
   jamais les textes `portion` (0 problème annoncé précisément quand tous
   les tracés auraient disparu).
3. Un pays listé deux fois dans une même zone écrasait la première entrée
   (dict) → nouveau signal **DOUBLON INTERNE**, compté à part, code
   retour 1.

Intégré à `scan_geographie_complet.py` comme étape optionnelle
**`--check-overlays`** (lecture seule, sans LLM, compatible `--run-*`,
reconnaissance de la ligne "Résumé :" dans le résumé consolidé) + case
"Tracés dessinés (overlays)" dans `scripts_config.json` (cochée par le
préréglage Maxi). **Testé depuis le GUI** sur `fortress_world`.

Overlays réels de `fortress_world` : 2, tous deux cohérents
(Heysham/France littoral ; Espace Nordique/Russie-Kaliningrad).
`gui/static/geo_overlays/` **est bien versionné** (`git ls-files`).

### Premier test réel "Zones à enrichir" (#2)
Zone Interdite de Heysham (`fortress_world`, Mistral). Proposition
relue et retouchée par David ("pillards de l'Interzone" → "pillards venus
des marges de la zone", `evenement_transition` renseigné à la main :
"Fusion partielle du réacteur de Heysham 2 (2044)", période 2044-2050).
Diff limité aux trois clés de Heysham. Le terme "Interzone" venait de la
**description** de Heysham elle-même (question ouverte, chantier #1).

### Scan géographie complet de `fortress_world` (constats, rien corrigé)
- Finlande, Lituanie dans aucune zone (2 chantiers `pays_sans_zone`
  écrits — `--write-chantiers` coché par défaut dans le GUI).
- 13 entrées sans `type_entite` = format minimal écrit par l'affectation
  depuis la Carte (voir S13). **Correction proposée, non confirmée
  lancée** : `scan_geographie_complet.py --scenario fortress_world
  --run-type-entite --apply-type-entite`.
- 12 sous-zones restées sous leur ancien parent (Bratislava, Genève,
  Tbilissi, Almaty + enfants) — restes des découpages Hyphan.
- `sao_paulo_megapole` sans pays dans son `origine_reelle`.
- 4 zones suspectes déjà connues ; doublon interne France/Zone Euro Sud.

Tout ce qui relève de Hyphan est consigné dans le chantier #1.

## Incident git — `git checkout` sur des fichiers non committés

**Cause (erreur de Claude)** : pour remettre le vault en état après les
tests du bug #5, Claude a fait lancer `git checkout -- geographie/
breakdown.md gui/zones_pays.json …` sans avoir vérifié que ces fichiers
n'avaient pas de modifications non committées. Ils en avaient : le vault
n'avait pas été committé depuis longtemps (`zones_pays.json` : dernier
commit fin juillet, `b0a15b9`).

**Pertes constatées puis réparées** :
- `breakdown.md` : nettoyage Sénégal du 13 sept annulé (réapparu en
  double dans `arc_sahelo_mediterraneen`). Restauré depuis la copie du
  fichier envoyée par David juste avant le test.
- `zones_pays.json` : ~2 mois d'affectations perdues (42 pays de
  `fortress_world` revenus aux blocs de fin juillet). Invisible sur la
  carte (qui lit les fiches `.md`). Restauré depuis
  `git show 4aa4260:gui/zones_pays.json.bak` — le `.bak` écrit par le GUI
  juste avant l'application en lot, committé par hasard dans le premier
  commit de la session — puis Royaume-Uni → Heysham réappliqué. Contrôle
  final : dérive `fortress_world` = 0, autres scénarios identiques à
  avant.

Commande de contrôle de dérive `zones_pays.json` ↔ fiches (racine du
vault) :
```bash
python3 -c "
import json, re, yaml
cur = json.load(open('gui/zones_pays.json'))
for sc in ['breakdown','fortress_world','new_sustainability','eco_communalism','policy_reform','reference']:
    fm = yaml.safe_load(re.match(r'^---\n(.*?)\n---', open(f'geographie/{sc}.md').read(), re.S).group(1))
    md = {}
    for z in fm['zones']:
        for o in z.get('origine_reelle') or []:
            if isinstance(o, dict) and o.get('entite') and not o.get('portion'):
                md.setdefault(o['entite'], []).append(z['slug'])
    print(f'{sc:20}', sorted(p for p, s in cur.get(sc, {}).items() if p in md and s not in md[p]))
"
```
Valeurs attendues au 23 sept : `breakdown` [Arctique, Groenland],
`new_sustainability` [Norvège], `reference` [Afghanistan, Italie, Kenya,
Kirghizistan, Tadjikistan], les trois autres vides.

**Règle adoptée** : commiter avant tout test ; jamais de `git checkout`/
`git restore` sur un fichier du vault sans `git status`/`git diff`
préalable. Consignée dans le manuel (§7, "Précaution git").

## Décisions actées
- Chantier #1 (Hyphan) en pause ; les incohérences France/Allemagne de
  `fortress_world` ne sont **pas** corrigées mécaniquement (chacune revient
  à décider qui possède quelle partie du territoire).
- Panneau "Gérer les overlays" supprimé (pas rebranché).
- `check_overlay_portion_coherence.py` vit dans `gui/` ; étape optionnelle
  du scan, jamais par défaut.
- Royaume-Uni → Zone Interdite de Heysham (`fortress_world`) : voulu.
- #2 et #2bis clos ; résidus déplacés en secondaire (S12 dérive
  `zones_pays.json` ancienne, S13 format d'affectation, S14 couleur
  fantôme UK).

## Reste à faire
- **Commits à vérifier** : `app.js` (dernière version, champs éditables),
  `scan_geographie_complet.py` + `scripts_config.json`, Heysham enrichi.
  Faire un `git status` en début de prochaine session : doit être propre.
- **`--apply-type-entite` sur `fortress_world`** si pas encore lancé
  (13 entrées), puis commit.
- **#3 P20** : choisir le service de génération d'image (comparatif
  qualité/prix/API/restrictions sur personnages nommés proposé, pas
  commencé).
- **#4** : revue des 14 `zone_suspecte` (tri prêt dans le backlog).
- `.gitignore` : `.DS_Store`, `.obsidian/workspace.json`, `*.bak` —
  **attention** : les `.bak` versionnés ont servi de filet de sécurité
  aujourd'hui ; ne les exclure qu'une fois l'habitude de commiter
  régulièrement prise.
- S13 (cause dans `zone_repository.py`) à la prochaine passe sur ce
  fichier.

## Fichiers livrés
**Modifiés** :
- `gui/static/app.js` — code mort retiré (5 fonctions), échappement HTML
  onglet Chantiers, champs éditables "Zones à enrichir".
- `gui/check_overlay_portion_coherence.py` (déplacé de `generator/`) —
  3 bugs corrigés, signal DOUBLON INTERNE.
- `scan_geographie_complet.py` — étape optionnelle `--check-overlays`.
- `gui/scripts_config.json` — case "Tracés dessinés (overlays)" + Maxi.
- `geographie/breakdown.md` — restauré (état d'avant tests).
- `gui/zones_pays.json` — restauré depuis `4aa4260` + Royaume-Uni.
- `geographie/fortress_world.md` — Heysham enrichi (par le GUI).
- `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`, `USER_MANUAL_COMPLET.md`.
