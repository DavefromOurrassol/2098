# HANDOFF — fin de session du 25 juillet 2026 (à uploader dans le nouveau chat)

*Suite directe de `HANDOFF_CHANTIERS_GEOGRAPHIE.md` (matin du 25 juillet).
Les points 4.1 à 4.4 de ce handoff sont **terminés et testés en conditions
réelles**. Reste 4.5, plus deux extensions décidées en cours de route
(sélection d'étapes + audit sidebar). Détail complet dans
`USER_MANUAL_COMPLET.md` mis à jour (§4, §4bis, §7) — ce document-ci est
un résumé de navigation, pas une redite.*

---

## 1. Ce qui a été fait aujourd'hui, dans l'ordre

### 4.1 à 4.4 du handoff du matin (fusion chantiers_geographie.yaml)
- **`chantiers.py`** : bug trouvé et corrigé AVANT tout test réel — `charger_chantiers()` avalait silencieusement une corruption YAML (`except yaml.YAMLError: return []`), risquant un écrasement silencieux du fichier au prochain ajout. Lève maintenant `ChantiersCorrompuError`.
- **Les 3 scripts déjà migrés** (`check_zones_coherence.py`, `check_origine_reelle_coherence.py`, `check_patron_spatial_coherence.py`) : testés à blanc puis en conditions réelles sur les 6 scénarios. 15 chantiers `zone_suspecte` créés, 0 chantier `pays_sans_zone` (rien à signaler).
- **`generer_zones_topdown.py`** réécrit pour lire/écrire via `chantiers.py` (plus de fichier `zones_proposees_topdown_{scenario}.yaml` séparé). Ajout d'un flag `--force` (protège une proposition non approuvée d'être régénérée par erreur). Testé en conditions réelles : review + approbation + apply sur `reference/europe_occidentale_reconstructee` — diff chirurgical confirmé (seule la description a changé, aucune fuite des champs non révisables).
- **`migrer_vers_chantiers.py`** créé et exécuté : 12 propositions LLM déjà existantes récupérées gratuitement (`fortress_world`, `new_sustainability`, `eco_communalism`, `policy_reform`), 2 chantiers `traite` créés depuis l'historique `corrige_via_c2`. 0 écrasement, 0 orpheline.
- **`scan_geographie_complet.py`** harmonisé : un seul flag `--write-chantiers` (remplace `--write-suspectes`/`--write-zones-manquantes`, qui ne correspondaient plus à rien depuis la migration). Bug corrigé au passage : l'étape 1 ne propageait jamais aucune écriture avant.
- **`scripts_config.json`** : libellés/descriptions simplifiés (langage utilisateur, plus de jargon `--flag`) pour les 7 options de `scan_geographie_complet`.

### Extensions décidées en cours de route (au-delà du handoff du matin)
- **Préréglages Léger / À la carte / Maxi** sur `scan_geographie_complet` (`app.js` : `renderPresets()`/`applyPreset()`, nouveau type `script.presets`). Deux bugs trouvés et corrigés en testant :
  - Collision de classe CSS `mode-tab` → injectait `--mode None` et plantait le script (corrigé : classe dédiée `preset-tab`).
  - `<select>` "Scénario" restait grisé pour toujours après avoir coché "Tous les scénarios" une fois, et gardait une valeur périmée qui partait quand même dans les arguments (corrigé dans les deux sens : réactivation + purge de la valeur).
- **Sélection d'étapes** (`--run-zones`/`--run-type-entite`/`--run-origine-reelle`/`--run-conventions`/`--run-patron-spatial`) ajoutée à `scan_geographie_complet.py` — permet de lancer une seule étape (ou plusieurs) au lieu des 5 systématiquement. Numérotation dynamique (`Étape 1/2`), notes de fin conditionnées à l'étape réellement lancée.
- **`--marquer-resolus`** ajouté à l'orchestrateur (propagé à l'étape 1) pour boucler la parité complète de flags avec l'entrée individuelle `check_zones_coherence`.
- **`--write-chantiers` passé à `default: true`** sur les 4 entrées GUI concernées (`scan_geographie_complet`, `check_zones_coherence`, `check_origine_reelle_coherence`, `check_patron_spatial_coherence`) — à la demande de David pour simplifier l'usage courant. `Léger` continue de tout décocher explicitement (reste 100% lecture seule).

### Audit du panneau sidebar (27 → 26 entrées)
- **`complete_geographie_coverage` retiré** du panneau — confirmé obsolète après lecture complète du code (même fonction que `generer_zones_topdown.py`, pipeline déconnecté de `chantiers_geographie.yaml`). Traçabilité ajoutée au manuel (§4 + tableau §6).
- **`zoning_topdown_test` et `reparenter_sous_zones_orphelines` initialement soupçonnés de doublon, puis CONSERVÉS** après lecture du code réel : les deux fichiers ont un double usage légitime (CLI manuel + appel machine `--json` par le GUI). Descriptions clarifiées dans `scripts_config.json` pour éviter la même fausse alerte à l'avenir — **leçon à retenir : toujours vérifier le contenu réel d'un script avant de le retirer d'un panneau, jamais se fier au seul nom/description.**
- **Les 5 scripts `check_*` restent dans le panneau pour l'instant** — vérifiés flag par flag comme entièrement redondants avec `scan_geographie_complet` + sélection d'étapes (voir §2 ci-dessous, décision pas encore actée).

---

## 2. Décision en attente : retirer les 5 diagnostics individuels du panneau ?

Parité de flags confirmée entre chaque script individuel et
`scan_geographie_complet` + `--run-*` :

| Script individuel | Couvert à 100% par l'orchestrateur ? |
|---|---|
| `check_zones_coherence` | ✅ (après ajout de `--marquer-resolus` à l'orchestrateur) |
| `check_type_entite_coherence` | ✅ |
| `check_origine_reelle_coherence` | ✅ |
| `check_conventions_territoires` | ✅ |
| `check_patron_spatial_coherence` | ✅ |

David a testé au moins un cas réel (`--run-type-entite` seul, `--all`,
sans `--apply`) avec succès sur son vault — a détecté un vrai cas
(`policy_reform/ameriques_reformees`, Groenland sans `type_entite`, pas
encore corrigé). **Reste à tester les 4 autres cases avant de retirer les
5 entrées individuelles du panneau.** Si David confirme, même traitement
que `complete_geographie_coverage` : retrait de `scripts_config.json` +
ligne de traçabilité au tableau §6 du manuel.

---

## 3. Backlog noté en mémoire (pas dans ce document, déjà dans les mémoires Claude)

- **Point 4.5 du handoff du matin** (onglet GUI "Chantiers") : en pause,
  nécessite `gui/app.py` pour rester cohérent avec les routes Flask
  existantes (ex. `/api/carte/generer_zone_topdown`) avant de coder les
  nouvelles routes + l'onglet `index.html`/`app.js`.
- **"Niveau 2" scan_geographie_complet** : imbriquer visuellement chaque
  option corrective (`--apply-type-entite`, `--resolve-llm`...) sous sa
  case de sélection d'étape correspondante, avec grisé/affichage
  conditionnel tant que l'étape parente n'est pas cochée. Nouveau champ
  `depends_on` à inventer dans `scripts_config.json` + logique `app.js`
  dédiée (distincte de `mode_only`, qui gère onglet→bloc, pas
  checkbox→checkbox).

---

## 4. Fichiers livrés aujourd'hui (tous testés, sauf mention contraire)

| Fichier | Statut |
|---|---|
| `generator/chantiers.py` | Testé (12 tests unitaires + conditions réelles) |
| `generator/generer_zones_topdown.py` | Testé (fixtures + conditions réelles) |
| `generator/migrer_vers_chantiers.py` | Testé et **déjà exécuté** sur le vault réel |
| `generator/scan_geographie_complet.py` | Testé (fixtures + conditions réelles, 3 passes) |
| `gui/scripts_config.json` | Testé (rendu GUI confirmé par captures/retours de David) |
| `gui/app.js` | Testé (logique isolée + confirmé en conditions réelles par David) |
| `documentation/USER_MANUAL_COMPLET.md` | Mis à jour (§4, §4bis, §5→pas touché, §7) — pas encore relu par David |

**Fichiers NON modifiés aujourd'hui, à ne pas toucher par erreur en les
confondant avec une version antérieure** : tous les autres scripts de
`generator/` et `gui/` (notamment `gui/app.py`, jamais uploadé cette
session — nécessaire pour 4.5).

---

## 5. Point de reprise suggéré pour demain

1. David confirme le test des 4 dernières cases de sélection d'étape sur
   `scan_geographie_complet` (Zones / Cohérence pays-zone / Conventions /
   Patron spatial).
2. Décision : retirer ou non les 5 entrées individuelles du panneau
   (§2 ci-dessus).
3. David relit `USER_MANUAL_COMPLET.md` mis à jour, signale toute
   incohérence.
4. Enchaîner sur 4.5 (onglet GUI "Chantiers") — uploader `gui/app.py`
   pour démarrer.
