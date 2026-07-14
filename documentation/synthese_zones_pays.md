# Synthèse — Zones et pays (Ourrassol 2098)
*Rédigée le 14 juillet 2026, à partir de HANDOFF_CONSOLIDE.md, BACKLOG_CONSOLIDE.md, USER_MANUAL_COMPLET.md, APPROCHE_ZONING_GEOGRAPHIE_SCENARIOS.md (tous datés du 13 juillet) + travaux de la session du 14 juillet. Les docs sources n'ont pas encore été mis à jour avec les développements du 14 — cette synthèse comble l'écart.*

---

## 1. Le pipeline géographique — vue d'ensemble

Trois passes indépendantes construisent la géographie de chaque scénario :

| Passe | Script | Logique | Statut |
|---|---|---|---|
| 1 | `build_geographie_monde.py` | Bottom-up — zones N1 depuis le corpus narratif déjà écrit | Stable |
| 2 | `enrich_geographie_recursive.py` | Bottom-up additif — sous-zones N2/N3, ne touche jamais aux zones existantes | Stable |
| 3 | `complete_geographie_coverage.py` | Top-down naïf — pour chaque pays sans zone, LLM juge sur ressemblance textuelle avec `origine_reelle` uniquement, **sans revalider contre la logique du scénario** | Stable mais identifié comme cause racine des incohérences (§3) |

**Structure d'une zone** (`geographie/{scenario}.md`, YAML) : `slug`, `nom`, `niveau` (1/2/3), `parent`, `type`, `origine_reelle` (liste de `{entite, type_entite: pays|region_administrative|ville, portion}`), `description`, `relations.allies/rivaux`.

**Découverte clé (13-14 juillet)** : le vault contient déjà, dans `variables/{variable}.md → states.{scenario}.state_logic`, le patron de structuration spatiale exact de chaque scénario (`organisation_territoires` en premier lieu, aussi `geopolitique_conflits`, `frontieres_du_systeme`) — **jamais exploité par aucune des 3 passes**. C'est le trou que P24 (§6) vise à combler.

---

## 2. Outils existants (scripts + GUI)

| Outil | Rôle | Modifie le vault ? |
|---|---|---|
| `build_geographie_monde.py` | Étape 1 (voir §1) | Oui |
| `enrich_geographie_recursive.py` | Étape 2 (voir §1) | Oui |
| `complete_geographie_coverage.py` | Étape 3, workflow `--review` → `--apply` obligatoire | Oui |
| `check_zones_coherence.py` | Diagnostic : YAML valide, pays absents de toute zone, pays sans N1, entrées obsolètes de `zones_manquantes.yaml` | **Non — lecture seule** |
| `regenerate_zones_pays.py` | Reconstruit `gui/zones_pays.json` depuis les fiches (source de vérité) | Oui (avec `.bak`) |
| `add_pays_to_zone.py` | Ajoute un pays à l'`origine_reelle` d'une zone existante | Oui (avec `.bak`) |
| `merge_pays_monde.py` | One-shot déjà exécuté — a étendu `zones_pays.json` à ~198 pays | Déjà fait |
| **Onglet Carte** (GUI) | Bascule pays→zone unitaire (proposition LLM ou manuelle), + **restructuration de zones** (rename/reparent/bascule, voir §4) | Oui |
| `check_origine_reelle_coherence.py` | **Nouveau, 14 juillet** — garde-fou signal 1 de P22 (voir §5) | **Non — lecture seule** |

⚠️ **Point de documentation obsolète repéré dans `USER_MANUAL_COMPLET.md`** (§ligne 288) : le manuel décrit encore `restructure_zones.py` comme "planifié, pas encore codé (P7)", un script séparé distinct de l'onglet Carte. C'est **faux depuis le 13 juillet** — P7 a été livré directement dans l'onglet Carte (pas de script séparé, décision prise en cours de scoping). L'entrée fantôme dans `scripts_config.json` (section maintenance) doit être retirée, et cette section du manuel réécrite. Signalé aussi dans `BACKLOG_CONSOLIDE.md` (P7, note de scope) mais pas encore répercuté dans le manuel.

---

## 3. P7 — Restructure zones — ✅ CLOS le 13 juillet

Construit directement dans l'onglet Carte, en 3 étapes :

1. **Rename** — propage `slug`/`nom`, `parent` des enfants, wikilinks `sous [[...]]`, `relations.allies/rivaux` de **n'importe quelle** zone du scénario, `instances/*.md` + `event_instances/*.md`, `zones_pays.json`.
2. **Reparent** — déplace une zone (+ sous-arbre) vers un nouveau parent, recalcul en cascade du `niveau`. Extensions : promotion en zone N1 autonome, création d'une nouvelle zone N1 à la volée.
3. **Bascule pays** — bouton "↗️ rattacher" sur les sous-zones orphelines détectées lors d'un changement de zone d'un pays.

**Ce qui manque encore** (jamais scopé en détail, périmètre "carte" à l'origine) : **split / merge de zones**. C'est le chaînon manquant identifié en session (§7) — nécessaire si P24 génère une nouvelle zone cohérente sur un territoire déjà englouti dans le `origine_reelle` d'une zone fourre-tout voisine (cas réel trouvé : `arc_eurasien_central` liste à la fois Russie/Kazakhstan/Géorgie **et** Hongrie/Autriche/Allemagne/Belgique dans `breakdown`).

---

## 4. P22 — Garde-fou de cohérence géographique

### Signal 1 — `origine_reelle` vs chaîne de parenté — ✅ CONSTRUIT ET TESTÉ le 14 juillet

**Script livré** : `check_origine_reelle_coherence.py`. Compare le pays d'une zone `ville`/`region_administrative` à l'union des pays de toute sa lignée d'ancêtres. **Avertissement seul, jamais de blocage** (décision du 13 juillet, confirmée par un taux de faux positifs de 5/9 sur une première heuristique mots-clés).

Résolution en cascade : extraction directe (pays déjà écrit dans le champ) → alias adjectival (`"américain"` → États-Unis) → table statique `VILLE_PAYS` → `--resolve-llm` (batch, tier `structured_strict`, résultat mis en cache dans `cache_ville_pays_llm.json`, jamais repayé).

**Résultat du run réel (14 juillet, 6 scénarios, après `--resolve-llm`) : 13 incohérences confirmées**, triées en 3 familles — détail complet en §8 (P25).

Bugs corrigés en cours de construction (invisibles sur un cas isolé, trouvés en testant sur le vrai vault) :
- Qualificatifs entre parenthèses côté ancêtre (`"Russie (Sibérie orientale)"`) non réduits à leur pays de base
- Zones racine (N1, `parent: null`) vérifiées à tort — pas de chaîne de parenté à valider pour la racine
- Variantes de nommage (`"États-Unis"` / `"États-Unis d'Amérique"`) — résolu en import direct de `ALIASES` depuis `check_zones_coherence.py`, source unique plutôt que table dupliquée

**Limite connue et assumée** : quand le parent N1 est lui-même typé `region_administrative` (pas `pays`) dans son `origine_reelle`, la chaîne ne trouve "aucun" pays même si le rattachement est légitime (2 cas sur les 13 : `nuna_capital_siege`, `archives_communautaires_polynesie`). Amélioration future du script, pas un bug du vault.

### Signal 2 — Cohérence de patron spatial — ⚪ scopé, pas construit

Comparer la description/le type d'une zone au `state_logic` de `organisation_territoires.states.{scenario}` (voir P24 §6). Plus qualitatif que le signal 1, donc avertissement uniquement. Dépend de `patrons_spatiaux.py` (déjà livré, §6).

### Extension "candidats" — en discussion, pas construite

Pour chaque incohérence du signal 1, scanner les autres zones N1 du même scénario et proposer celles dont `origine_reelle` contient déjà le pays résolu — sur le modèle de ce que fait P7 manuellement aujourd'hui, mais suggéré automatiquement. Si aucun candidat trouvé → signal d'entrée naturel pour déclencher P24 étape C (le territoire n'a pas de zone cohérente dans ce scénario, il faut en générer une).

---

## 5. P23 — Corriger les 3 anomalies historiques (13 juillet) — état réel : **peut être clos**

Les 3 cas listés dans `BACKLOG_CONSOLIDE.md` sont obsolètes ou déjà traités :
- `barcelone_hub` → ✅ corrigé (sous `nouveau_califat_barcelone`, nouvelle zone N1 Ibérie)
- `corridor_iberique_energetique` → ✅ corrigé (même parent)
- `noeud_mnemos_pannonie` → **n'était jamais une vraie anomalie** : `arc_eurasien_central` liste bien la Hongrie dans son `origine_reelle` complet (~25 pays, pas les 5 initialement identifiés en lecture rapide en session). Erreur d'appréciation initiale, pas un bug du vault.

Reste dans `BACKLOG_CONSOLIDE.md` à retirer/clore formellement.

---

## 6. P24 — Générateur top-down de zones cohérentes avec le scénario

**Scoping complet fait** (`APPROCHE_ZONING_GEOGRAPHIE_SCENARIOS.md`), séquencement A → B → C :

- **Étape A — ✅ CONSTRUITE le 14 juillet** : `patrons_spatiaux.py` + `extract_state_logic.py`. Formalise le patron spatial des 6 scénarios (`organisation_territoires`, `geopolitique_conflits`, `frontieres_du_systeme`). Les citations (`state_logic`) sont **chargées dynamiquement depuis le vault** à chaque import — jamais figées en dur. L'analyse (`patron_a_respecter`/`a_eviter`) reste écrite à la main, à revalider manuellement si un scénario change en profondeur.
- **Étape B** — fusion avec le signal 2 de P22 (§4) — ⚪ pas construite
- **Étape C** — le générateur proprement dit, branché sur le formulaire "créer une nouvelle zone N1" de P7 étape 2 — ⚪ pas construite, le plus gros chantier

**Rien dans le pipeline actuel n'importe encore `patrons_spatiaux.py`** — il est prêt, en attente d'être consommé par B ou C.

---

## 7. Le chaînon manquant identifié en session — split de zones

Question posée en session : une fois P24 capable de générer une nouvelle zone cohérente pour une région, comment éviter qu'un même pays reste revendiqué à la fois par la nouvelle zone et par une zone fourre-tout existante qui le listait déjà ?

**Réponse** : rien dans le pipeline actuel ne fait ça. C'est un split de zone (retirer un sous-ensemble de pays de l'`origine_reelle` d'une zone existante pour les céder à une nouvelle) — jamais scopé en détail dans P7 (qui a livré rename/reparent/bascule, mais split/merge sont restés "dans le workflow carte" sans être codés). Cas réel qui illustre le besoin : `arc_eurasien_central` (`breakdown`) mélange un bloc Asie centrale/Caucase et un bloc Europe centrale dans le même `origine_reelle`.

**Enchaînement complet une fois tout construit** : extension "candidats" (§4) repère un rattachement incohérent → si aucun candidat N1 existant, P24 génère une zone neuve → si cette zone neuve chevauche l'`origine_reelle` d'une zone plus large existante, un split est nécessaire pour le résoudre proprement. Pas encore scopé comme item de backlog à part entière.

---

## 8. P25 — Nouveau (14 juillet) — Traiter les 13 incohérences détectées

**Famille 1 — Reparent probable, via outil P7 étape 2** (8 cas) : `hanse_baltique` (Pologne sous bloc nordique, `breakdown`), `geneve_bunker` + 2 enfants (Genève sous "zones grises tampons", `fortress_world`), `bruxelles_tribunal_algo` + 1 enfant (Bruxelles sous bloc alpin, `new_sustainability`), `seoul_accords` (Séoul sous bloc eurasien post-soviétique, `new_sustainability`), `delta_rhone_fermes_verticales` (Camargue/France sous corridor ibérique/Espagne, `new_sustainability`), `nuuk_knsf` (Nuuk/Danemark sous bloc américain, `policy_reform`), `murmansk_transit_arctique` (Mourmansk/Russie sous corridor nordique, `reference`).

**Famille 2 — Gap de données côté parent** (1 cas) : `ouagadougou_nouvelle_ctsa` — `afrique_continentale` liste presque toute l'Afrique mais pas le Burkina Faso. Correction par ajout (`add_pays_to_zone.py`), pas par reparent.

**Famille 3 — Limite structurelle du script, pas un vrai signal** (2 cas) : `nuna_capital_siege`, `archives_communautaires_polynesie` — parent N1 typé `region_administrative` au lieu de `pays`.

---

## 9. Fichiers livrés cette session (14 juillet)

| Fichier | Rôle | Statut |
|---|---|---|
| `extract_state_logic.py` | Parseur générique `variables/*.md → state_logic` | ✅ testé |
| `patrons_spatiaux.py` | Source de vérité patron spatial × scénario, chargement dynamique | ✅ testé, pas encore consommé en aval |
| `check_origine_reelle_coherence.py` | Garde-fou P22 signal 1 | ✅ testé sur les 6 scénarios réels, `--resolve-llm` validé |

## 10. Ce qui reste ouvert, par ordre de dépendance

1. Clore formellement P23 dans le backlog
2. Corriger les documents obsolètes du 13 juillet une fois validé (déjà exécuté à ce stade normalement) : rename `corridor_arctique_nordique_testmodif`, mise à jour `USER_MANUAL_COMPLET.md` sur `restructure_zones.py`
3. Trier les 13 cas de P25 (décision manuelle zone par zone, famille 1 surtout)
4. Construire l'extension "candidats" de `check_origine_reelle_coherence.py`
5. P22 signal 2 (patron spatial)
6. P24 étapes B et C
7. Scoper et construire le split de zones (§7) — pas encore un item de backlog formel
