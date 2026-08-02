# HANDOFF — session du 31 juillet 2026 (à uploader dans le nouveau chat)

*Session consacrée à une revue systématique, script par script, du panneau
GUI (`scripts_config.json`) — objectif : passer chaque entrée en
`gui_verified: true` après test réel ou lecture de code. Partie de la
matinée sur un point isolé (route Carte legacy), le reste sur la revue
proprement dite, qui a dévié plusieurs fois vers de vrais chantiers de
correction (bugs trouvés en creusant, pas juste de la relecture passive).*

---

## 1. Bilan du panneau — 16 sur 18 validés

| Script | Statut fin de session |
|---|---|
| `generate` | ✅ validé (déjà avant cette session) |
| `generate_series` | ✅ validé (déjà avant) |
| `generate_journaux` | ✅ validé (déjà avant) |
| `create_entities` | ✅ validé (déjà avant) |
| `inject_events` | ✅ validé (déjà avant) |
| `inject_signals` | ✅ validé (déjà avant) |
| `requeue_needs_review` | ✅ validé aujourd'hui (test réel avec entrée fabriquée) |
| `undo_custom` | ✅ validé (déjà avant) |
| `extract_phantom_slugs` | ✅ validé aujourd'hui (bugs corrigés, confirmé par David) |
| `enrich_geographie` | ✅ validé aujourd'hui (bug critique trouvé + corrigé, voir §2) |
| `scan_geographie_complet` | ✅ validé (déjà avant) |
| `generer_zones_topdown` | ✅ validé (déjà avant) |
| `zoning_topdown_test` | ✅ validé (déjà avant) |
| `reparenter_sous_zones_orphelines` | ✅ validé aujourd'hui (bug backend + nouvelle fonctionnalité, voir §3) |
| `extract_localisation` | ✅ validé aujourd'hui (testé en réel, 146 fiches, 0 doublon confirmé) |
| `review_localisation` | ✅ validé aujourd'hui (bug critique trouvé + corrigé, voir §4) |
| `enrich_minimal` | ❌ **non testé** — mis de côté volontairement (P8, gros chantier, coût réel) |
| `validate` | ❌ **non testé** — dernière entrée du panneau, jamais abordée cette session |

**`generate_manual` a été retiré du panneau** (19 → 18 entrées) — son seul
usage encore utile (aperçu de prompt copiable dans un LLM externe) est
maintenant couvert par la case `--dry-run` de `generate.py`, dont la
description a été clarifiée en ce sens.

---

## 2. Bug trouvé et corrigé : `lieux_emblematiques` mal formé

**Contexte** : `enrich_geographie_recursive.py` plantait en fin de run réel
sur `breakdown` (`AttributeError: 'str' object has no attribute 'get'`),
après tout le travail utile déjà fait (53 zones proposées, 51 retenues).

**Cause réelle, découverte en creusant** : pas un cas isolé — **195
entrées** `lieux_emblematiques` sur les 6 fichiers `geographie/*.md` sont
de simples chaînes ("Delhi (Citadelle Autonome)") au lieu du dict structuré
`{"nom": ..., "type": ..., "notes": ...}` attendu partout ailleurs dans le
pipeline. Cause probable : ces zones N1 datent d'une version antérieure de
`build_geographie_monde.py`, jamais retouchées depuis (traitées comme
"contexte fixe").

**Correctifs appliqués** :
- `enrich_geographie_recursive.py` : normalisation centrale à la lecture
  (`_normalize_lieux_emblematiques()`, dans `load_existing_geographie()`)
  + tolérance de format en défense dans `dedupe_promoted_lieux()` et
  `build_geographie_md()` (pour les `new_zones` proposées par le LLM, qui
  ne passent pas par la lecture normalisée) + fix cosmétique (parenthèses
  vides quand `type` est absent).
- `fix_lieux_residuels.py` : même tolérance de format (risque réel
  identifié à l'audit : chargeur de fichier indépendant, même pattern
  fragile).
- `build_geographie_monde.py` : même fix cosmétique par cohérence (risque
  écarté à l'audit — ne lit jamais de contenu existant — mais gardé pour
  que le rendu soit identique partout).
- **Nouveau script one-shot** : `fix_lieux_emblematiques_format.py` —
  normalise les fichiers sources eux-mêmes (aucun appel LLM, correction
  mécanique pure, `.bak` automatique). Testé en conditions réelles sur les
  6 fichiers : 195 entrées détectées en `--dry-run`, écriture réelle
  testée et vérifiée (intégrité confirmée champ par champ).

```bash
python3 fix_lieux_emblematiques_format.py --all --dry-run   # vérifier (195 attendues)
python3 fix_lieux_emblematiques_format.py --all              # écrire, .bak automatique
```

**Statut : appliqué**, les 6 fichiers `geographie/*.md` livrés dans cette
session contiennent déjà cette normalisation (voir §5 pour le détail
complet des fichiers livrés).

---

## 3. `reparenter_sous_zones_orphelines` — bug backend + nouveau mode scan

**Bug trouvé** (`gui/app.py`, `_scan_zone_slugs`) : le menu déroulant
`--zone-cible` ne remontait qu'**une seule zone N1** par scénario, peu
importe leur nombre réel (37, 42, 21, 16, 16, 17 selon le scénario).
Cause : découpage par regex (`re.split` sur `---`) suivi de `.search()`
(première occurrence seulement), alors que les fichiers n'ont que 2
délimiteurs `---` au total (un seul bloc YAML englobant toutes les zones).
**Corrigé** : remplacé par un vrai parsing YAML, testé sur les 6 vrais
fichiers (compte de zones N1 confirmé).

**Nouvelle fonctionnalité, à la demande de David** : proposer les 16 à 42
zones N1 d'un scénario dans `--zone-cible` était peu exploitable (l'écrasante
majorité n'a jamais de sous-zone orpheline). Ajout d'un mode
`--scan-candidates` (lecture seule, aucun appel LLM) à
`reparenter_sous_zones_orphelines.py`, qui ne liste que les zones ayant
*réellement* des sous-zones orphelines en attente. Branché côté GUI via une
nouvelle route `/api/slugs?type=zones_a_reparenter`, sur le même principe
que l'appel automatique post-reparent déjà existant (sous-processus + JSON,
tolérant aux échecs).

**Effet de bord découvert en marge (P24 étape C, gui/app.py)** : ce script
est déjà appelé automatiquement dans ses deux vrais contextes d'usage
(reparent manuel dans l'onglet Carte, et `generer_zones_topdown
--apply-topdown`) — l'entrée manuelle du panneau ne sert donc que de filet
de secours (l'appel automatique avale silencieusement ses erreurs). Pas
encore documenté explicitement dans le panneau (`description` du script) —
**reste à faire**, voir §6.

**Cascade d'orphelins diagnostiquée et traitée sur les 6 scénarios** (avec
le vrai `zones_pays.json`, fourni par David en cours de session — voir
§6, point de vigilance) :

| Cas | Type | Décision |
|---|---|---|
| Medellín (breakdown) | désalignement simple | ✅ reparenté |
| Karachi (breakdown) | désalignement simple | ✅ reparenté |
| Bassin Caspien (breakdown) | **transnational** (Iran / Kazakhstan-Azerbaïdjan-Turkménistan) | ✅ tranché : gardé sous Arc Eurasien Central, Iran retiré de son `origine_reelle` |
| Nuuk (eco_communalism) | désalignement simple | ✅ reparenté |
| Réseau Terrafond des Bassins (eco_communalism) | **transnational voulu** (les 2 zones se décrivent explicitement comme liées) | **laissé tel quel**, réapparaîtra dans le scan en continu, assumé |
| Corridors Migratoires Anatoliens (eco_communalism) | **transnational** (Syrie = origine migratoire, pas territoire du corridor) | ✅ tranché : gardé sous Bioterritoires Anatoliens, Syrie retirée |
| Sahel — Corridors verts RVC (new_sustainability) | désalignement simple | ✅ reparenté |
| Nœuds d'irrigation sahéliens (policy_reform) | désalignement simple | ✅ reparenté |
| Zones Tampons Climatiques Européennes (reference) | désalignement simple (conséquence directe du nettoyage Italie, §2bis) | ✅ reparenté |

**État final du scan** : `fortress_world`, `new_sustainability`,
`policy_reform`, `reference`, `breakdown` → 0 candidat. `eco_communalism` →
1 candidat restant (Réseau Terrafond), volontaire.

### 2bis. Nettoyage manuel `zones_grises_globales` (reference.md)

Repéré en creusant le cas Zones Tampons : cette zone (`type:
zone_sinistree`, archétype narratif volontairement dispersé — "espaces
hors-cadre institutionnel") avait "Italie" dans son `origine_reelle`, un
pays qui détonnait par rapport au reste de la liste (États fragiles/
périphériques). Confirmé comme erreur probable par David. Retiré, ainsi que
3 doublons individuels (Kirghizistan/Tadjikistan/Afghanistan, déjà présents
via l'entrée groupée "Asie Centrale (...)").

---

## 4. `review_localisation` — bug critique trouvé avant qu'il ne morde

Le mode par défaut (case "Auto-résoudre" décochée) est **interactif**
(`input()`, choix `[V]/[C]/[0]/[S]/[Q]` au clavier). Or **tous** les
scripts lancés depuis le GUI utilisent `stdin=subprocess.DEVNULL`
(confirmé dans `gui/app.py`, décision documentée du 12 juillet suite à un
bug similaire sur `inject_custom_events.py`). Un `input()` sur stdin
DEVNULL lève une `EOFError` non gérée dans `run_review()` — le script
aurait planté dès la première fiche si lancé sans cocher la case.

**Corrigé** : `--auto-resolve` passé de "décochée par défaut, optionnelle"
à **"cochée par défaut, obligatoire"** côté panneau (`scripts_config.json`
uniquement — le script Python lui-même n'a pas été touché, le mode
interactif reste entièrement fonctionnel en CLI directe). Testé en réel
après correctif : fonctionne parfaitement (1 fiche résolue, motif
cohérent, écriture réussie).

---

## 5. Autres changements notables du panneau

- **Mécanisme `hide_when`** appliqué à `extract_phantom_slugs` (`--report`
  n'a d'effet que si la source inclut le rapport d'enrichissement).
- **Nouveau 7e mécanisme conditionnel** : `"advanced": true` sur une
  option → regroupée sous un bloc repliable "Options avancées" en bas du
  formulaire (`app.js` + CSS minimal dans `index.html`). Utilisé pour
  `--report` sur `extract_phantom_slugs`.
- **`yaml_files` erroné corrigé** sur `extract_phantom_slugs` (pointait
  vers `instances_custom/needs_review_enrich.yaml`, copié par erreur
  depuis `enrich_minimal` — corrigé vers `entites_custom/queue.yaml`, le
  vrai fichier écrit par ce script, rendu modifiable).
- **Sauvegarde automatique avant "Lancer"** (`app.js`,
  `saveOpenConfigForms()`) — corrige un cas réel vécu par David : un
  formulaire `config_fields` rempli puis lancé sans passer par
  "Sauvegarder" utilisait l'ancienne config sur disque.
- **7 scripts** avaient une case `--dry-run` trompeuse ("simulation, aucune
  écriture" alors qu'un appel LLM réel a quand même lieu) : `create_entities`,
  `inject_events`, `inject_signals`, `enrich_geographie`, `enrich_minimal`,
  `extract_localisation`, `review_localisation`. Toutes corrigées avec un
  avertissement explicite. `generate`/`generate_series`/`generate_journaux`/
  `extract_phantom_slugs` vérifiés comme de VRAIS dry-run, non touchés.
- **Nouveau mode `--scan-pending`** sur `extract_localisation.py` (même
  principe que `--scan-candidates` sur `reparenter` — lecture seule,
  purement mécanique) : le champ `--slug` ne liste plus que les fiches
  réellement en attente de localisation, au lieu de toutes les instances.
  Testé en réel (146 fiches détectées avec `--force`, 0 sans).
- **Sections fusionnées** : la section "Localisation" (2 entrées) a été
  supprimée, `extract_localisation`/`review_localisation` déplacées dans
  "Géographie — diagnostic" (`app.js`, tableau `SECTIONS` + `scripts_config.json`).
  Décision de David après discussion (les deux options se défendaient :
  fichiers différents touchés vs flux d'usage souvent enchaîné).

---

## 6. Points de vigilance / backlog pour la suite

- **`enrich_minimal` (P8)** — jamais testé côté GUI. 426 fiches restantes,
  ~37$ estimé (à recalculer, tarif Mistral). Dépendance identifiée avec
  `enrich_geographie` : les champs que P8 remplit
  (`description_journalistique`, `tensions_narratives`, `role_dans_scenario`)
  sont exactement ceux que lit `enrich_geographie_recursive.py` pour son
  corpus — **lancer P8 avant un futur `enrich_geographie --all`** donnerait
  un corpus plus riche. Recommandation : tester avec `--limit` 2-3 avant
  `--all`.
- **`validate`** — dernière entrée du panneau, jamais abordée cette
  session. À faire en premier à la prochaine reprise.
- **`zones_pays.json`** — nécessaire pour tout test futur de
  `reparenter_sous_zones_orphelines --scan-candidates` (ou tout ce qui
  passe par `resoudre_pays()`) : sans lui, la résolution pays échoue
  silencieusement sur les entités composées ("Mer Caspienne (zone
  frontalière Russie/Kazakhstan/...)") et fausse les résultats. **David
  devra le refournir à chaque nouvelle session** tant qu'il n'est pas
  inclus par défaut dans les uploads.
- **Description du panneau `reparenter_sous_zones_orphelines`** — devrait
  mentionner explicitement qu'il est déjà appelé automatiquement dans ses
  2 vrais contextes d'usage (Carte, top-down), et que l'entrée manuelle
  n'est qu'un filet de secours. Discuté, pas encore fait.
- **`queue_sahel_v2.yaml`** — fichier de debug identifié dans
  `signaux_custom/`, à supprimer par David (pas fait par Claude, pas
  d'accès direct au vault).
- **Symétrie non documentée** — `entites_custom/processed.yaml`,
  `evenements_custom/needs_review.yaml`, `evenements_custom/processed.yaml`,
  `signaux_custom/needs_review.yaml` existent (pattern symétrique aux 3
  pipelines) mais ne sont mentionnés nulle part dans
  `USER_MANUAL_COMPLET.md`.
- **`generator/journaux.yaml`** — chemin exact à corriger dans le manuel
  (cité sans préfixe `generator/` à un endroit).
- **`generator/coverage_proposals_reference.yaml`** (sans `.applied`,
  contrairement aux 5 autres scénarios qui n'ont que la version
  `.applied.yaml`) — anomalie repérée, jamais creusée (famille legacy de
  toute façon, `complete_geographie_coverage.py` retiré).
- **Renommage des YAML génériques par dossier** (`queue.yaml`,
  `processed.yaml`, `needs_review.yaml` répétés dans 3 dossiers différents)
  — décision reportée : clarté vs coût de renommage (toucherait plusieurs
  scripts + `scripts_config.json`).

---

## 7. Fichiers livrés cette session (tous testés, sauf mention contraire)

**GUI**
- `gui/app.js` — nombreux changements cumulés (voir §5), + fix `SECTIONS`
- `gui/index.html` — CSS "Options avancées", CSS bouton legacy retiré
- `gui/app.py` — fix `_scan_zone_slugs`, 2 nouvelles routes (`zones_a_reparenter`,
  `fiches_a_localiser`)
- `gui/scripts_config.json` — voir §1/§5 pour le détail exhaustif

**Pipeline géographie**
- `generator/enrich_geographie_recursive.py` — fix `lieux_emblematiques` (§2)
- `generator/fix_lieux_residuels.py` — même fix défensif
- `generator/build_geographie_monde.py` — fix cosmétique par cohérence
- `generator/fix_lieux_emblematiques_format.py` — **nouveau**, one-shot testé
- `generator/reparenter_sous_zones_orphelines.py` — nouveau mode `--scan-candidates`
- `generator/extract_localisation.py` — nouveau mode `--scan-pending`

**Fiches géographie (contenu, pas structure)**
- `geographie/breakdown.md`, `eco_communalism.md`, `new_sustainability.md`,
  `policy_reform.md`, `reference.md` — voir §2/§3 pour le détail par fichier.
  `fortress_world.md` non modifié (fourni pour le set complet uniquement).

**Documentation**
- `USER_MANUAL_COMPLET.md` — mis à jour (voir document séparé, changements
  détaillés par section)

---

## 8. Point de reprise suggéré pour la prochaine session

1. Tester `validate` (jamais abordé) — dernière entrée du panneau.
2. Décider du sort de `enrich_minimal`/P8 : lancer un premier test
   `--limit` 2-3, ou continuer à le reporter.
3. Nettoyer les points de vigilance mineurs du §6 (`queue_sahel_v2.yaml`,
   symétrie processed/needs_review, chemin `journaux.yaml`) si le temps le
   permet — aucun n'est bloquant.
4. Une fois `validate` et `enrich_minimal` traités, **les 18 entrées du
   panneau seront toutes validées** — bon moment pour un audit de clôture
   global (relire `USER_MANUAL_COMPLET.md` en entier, comme fait après les
   précédentes vagues de revue).
