# Manuel utilisateur — Pipeline Ourrassol 2098

*Mode d'emploi de l'état actuel : ce que fait chaque outil, quand l'utiliser,
comment le lancer (GUI ou terminal), ses pièges. Mis au propre le 24 octobre 2026,
mis à jour le 11 novembre 2026 au soir (unification « et si ? » ; Articles → « et si ? » éprouvé ;
extracteur filtré, passage de l'article transmis à l'injection, U3p → U3y).
Le récit des sessions (bugs trouvés, itérations, tests, versions successives) est
dans `USER_MANUAL_HISTORIQUE.md` ; les chantiers ouverts dans `BACKLOG_ACTIF.md`.
Les numéros de section (§2octies, §3quinquies…) sont stables : backlog et
handoffs y renvoient.*

**Sommaire**
- §0 Architecture, LLM, conventions · §1 Modules internes · §1bis Utilitaires géographie
- §2 Génération d'articles · §2bis Contenu du prompt · §2ter Longueur, date, signature ·
  §2quater Rédactions (journalistes, orateurs) · §2quinquies Mois de parution ·
  §2sexies Suite narrative et basculements · §2septies Onglets d'inventaire et résumés ·
  §2octies Site des revues · §2nonies Journaux, zones et audits d'articles
- §3 Entités, événements, signaux custom · §3bis Trajectoire · §3ter Injection et
  propagation dynamique · §3quater Veille (état du monde, signaux faibles) ·
  §3quinquies Simulateur « et si ? »
- §4 Géographie · §4bis Chantiers géographie · §5 Validation · §6 Scripts one-shot et
  legacy · §7 GUI Flask

---

## 0. Architecture, LLM, conventions

```
Ourrassol2098/                          ← racine du vault Obsidian (dépôt git)
├── generator/                          ← pipeline Python
│   ├── config.yaml, config_series.yaml, journaux.yaml, revues.yaml
│   ├── state/                          ← états persistants (usage des instances,
│   │                                     rezonage, et_si_application/, export_et_si.json…)
│   ├── entites_custom/  (queue.yaml, processed.yaml, needs_review.yaml)
│   ├── evenements_custom/ (queue.yaml, processed.yaml, needs_review.yaml, undo_queue.yaml)
│   ├── signaux_custom/  (queue.yaml, processed.yaml, needs_review.yaml)
│   └── rejeu/                          ← banc de rejeu de la passe exhaustive (§3quinquies)
├── gui/                                ← GUI Flask (app.py, scripts_config.json,
│   │                                     zones_pays.json, static/app.js, templates/, logs/)
├── state/                              ← états à la racine (editions.json, chapos_revues.json,
│                                         resume_scenarios.json, veille…)
├── geographie/{scenario}.md            ← 6 bibles géopolitiques (frontmatter zones + corps)
├── entites/, instances/                ← archétypes / instances d'entités
├── evenements/, event_instances/       ← archétypes / instances d'événements
├── variables/, scenarios/, thematiques/
├── et_si/hypotheses.yaml               ← hypothèses du simulateur
├── articles/{scenario}/                ← articles générés
└── documentation/                      ← backlog, manuel, handoffs, lore_regles.yaml,
    └── need_action/                      rapports à traiter
```

**Cycle des trois files custom** (`entites_custom/`, `evenements_custom/`,
`signaux_custom/`) : `queue.yaml` (à traiter) → `processed.yaml` (succès, parfois
`partial`) ou `needs_review.yaml` (échec ou cas à trancher ; pour les entités,
`requeue_needs_review.py` les remet en file). `evenements_custom/` a en plus
`undo_queue.yaml` (`undo_custom.py`).

**LLM** : tout passe par `llm_client.py` (Mistral par défaut, Claude, OpenAI).
- **Routage par tier** (`task_tier` passé à `call_llm()`, table `TASK_TIER_DEFAULTS`) :

  | Tier | Modèle | Usage |
  |---|---|---|
  | `strict` | `mistral-large-latest` | Sortie longue à identité imposée (articles, journalistes) |
  | `structured_strict` | `mistral-large-latest` | JSON canonique référencé ailleurs (entités, instances, géographie, relectures) |
  | `creative_souple` | `mistral-large-latest` | Rédaction libre (résumés, chapôs, réécritures) |
  | `volume` | `mistral-small-latest` | Extraction, classification courte (localisation…) |

- **Forçage ponctuel** : `LLM_PROVIDER` / `LLM_MODEL` (variables d'environnement) ou
  bascule GUI « Forcer ce modèle » (bandeau orange). Jamais en `export` permanent.
- **Mistral Large 4** (`mistral-large-4`) : dans le sélecteur, utilisé par aucun tier
  (raisonne avant d'écrire ; la réflexion compte dans `max_tokens` et peut tout
  consommer ; 4 à 7 fois plus cher par article). Voir backlog S29.
- Retry automatique sur 429, sans pause préventive, pour les trois fournisseurs.
- Clé API : `~/.zshrc`. Le Terminal du Mac s'ouvre sous bash, qui ne lit pas
  `~/.zshrc` : recharger la clé dans chaque nouveau terminal (sinon « MISTRAL_API_KEY
  non définie » et toute une file part en `needs_review`). Vérifier sans l'afficher :
  `python3 -c "import os; print('OK' if os.environ.get('MISTRAL_API_KEY') else 'ABSENTE')"`.
  Le GUI la lit depuis l'environnement de lancement.

**Conventions de statut** utilisées dans ce manuel :
🔁 répétable · 🧩 lançable depuis le GUI · 🗄️ terminal seulement · 🪦 one-shot ou
migration (jamais dans le GUI) · 📦 legacy, remplacé.

**Règles de travail** :
- Aperçu ou `--dry-run` d'abord ; écriture avec `--apply` ou bouton dédié ; une
  sauvegarde `.bak_<outil>` est faite avant toute écriture.
- ⚠ **`--dry-run` n'évite pas toujours l'IA.** Vrai dry-run (aucun appel) :
  `generate.py`, `generate_series.py`, `generate_journaux.py`,
  `extract_phantom_slugs.py`. Simulation partielle (appels IA réels, seule l'écriture
  est sautée) : `create_entities_and_instances.py`, `inject_custom_events.py`,
  `inject_custom_signals.py`, `enrich_geographie_recursive.py`, `enrich_minimal.py`,
  `extract_localisation.py`, `review_localisation.py --auto-resolve`,
  `et_si_injecter.py --dry-run`. `extract_localisation.py --report-only` et
  `--scan-pending` sont gratuits.
- Commit git propre avant toute écriture importante ; pour un essai d'écriture
  jetable sur le vrai vault : branche git dédiée, puis retour en arrière.
- Après une modification de `app.py`, `scripts_config.json` ou `app.js` :
  **redémarrer Flask entièrement** puis recharger la page (remplacer le fichier ne
  suffit pas ; un nouveau champ de formulaire n'apparaît qu'après redémarrage).
- Les patchs (`generator/patch_*.py`) refusent un second passage et gardent une
  sauvegarde ; une fois appliqués, ils ne se relancent pas.
- **Slugs** : un seul calcul, `generator/slugs.py` (31 oct 2026) — `slugify()`
  translittère ø, æ, œ, ß, ł, đ, ı… puis retire les accents. Tout script l'importe
  (`from slugs import slugify`) au lieu de recopier la fonction. Seule exception :
  `export_revues.slugify()` (URL du site).
- Commandes lancées depuis la racine du vault (pas de `cd`). Sortie à transmettre
  à Claude : `> ~/Documents/Ourrassol_sorties/<nom>.txt 2>&1`, puis glisser le
  fichier (répertoire dédié hors du vault, depuis le 31 oct 2026 ; pas le Bureau,
  pas `/tmp`, invisible dans le Finder).
- **git 2.17 (Apple)** : pas de `git switch` ni de `git branch --show-current` ;
  utiliser `git checkout -b <branche>`, `git checkout main`,
  `git rev-parse --abbrev-ref HEAD`.

---

## 1. Modules internes (jamais lancés directement)

| Module | Rôle |
|---|---|
| `loader.py` | Lecture du vault (frontmatter + corps), `VAULT_PATH`, `VALID_VARS`, `VALID_SCENARIOS`. Sélection des instances (`filter_instances_for_thematique()`, rotation à mémoire, cooldown, ancrage local), des événements (`select_relevant_events()`), extraction des forces attractives / répulsives des variables. |
| `snapshot.py` | Snapshot cohérent du monde pour un scénario et une date : niveaux des variables (moteur dynamique, §3ter), jalons, `zone_slug` par défaut (`_dominant_zone`, seulement en repli : une zone explicite prime). `build_snapshot(date_edition=…, zone_article=…)`. |
| `prompt_builder.py` | Assemble le prompt d'article (système + utilisateur) depuis le snapshot, la thématique et `config.yaml` ; profils de journaux (`JOURNAL_PROFILES`), résolution du journal (§2nonies), `STYLE_ORAL` (§2quater). |
| `api.py` | Appel LLM de l'article (tier `strict`), retry de longueur (§2ter), extraction du bloc `===METADONNEES_PUBLICATION===` (tolérante depuis le 31 oct : marqueur de fin facultatif, bloc en double retiré, bloc tronqué → retry ciblé des métadonnées), sauvegarde dans `articles/{scenario}/` (champ `config["output"]["dossier"]`), nom de fichier translittéré. |
| `slugs.py` | `slugify()` commun à tout le pipeline (31 oct 2026) : translittération (ø → o, æ → ae, œ → oe, ß → ss, ł → l…), NFD sans diacritiques, `_` comme séparateur. `api._slugify`, `export_revues.slug_pipeline`, `create_entities_and_instances.slugify` et les autres copies y délèguent. |
| `llm_client.py` | Abstraction Mistral / Claude / OpenAI, `call_llm(..., task_tier=...)`, `resolve_for_tier()`, réponse Mistral « en morceaux » réduite au texte (`_texte_reponse()`). |
| `instance_generation_common.py` | Génération d'UNE instance, partagée par `generate_instances.py` et `create_entities_and_instances.py` : prompt, appel, `validate_instance()`, `ramener_au_plafond()` (§3), écriture ; trajectoires (`VALID_TRAJECTOIRE`), `extraire_json()` tolérant (échec → `gui/logs/llm_json_echec_*.txt`), bandes temporelles (`compute_temporal_distribution()`). |
| `edition_utils.py` | Mois de parution : conversions année/mois ↔ date fractionnaire (`2098.08`), tirage d'un jour, registre `state/editions.json` (§2quinquies). |
| `echelles.py` | Échelle de chaque variable et convention d'intensité (`CONVENTION_NIVEAUX`, `CONSIGNE_IMPACT`, `verifier_impact()`), §3ter. |
| `dynamique.py` | Moteur de propagation, pur calcul : `simuler()`, couplages, `k_effectif()`, saturation, persistance des chocs, ruptures (§3ter). |
| `extract_state_logic.py` | Lit `variables/*.md → states.{scenario}.state_logic` (nettoie les clés wikilink) ; aussi en CLI (`--json`, `--scenario`). |
| `patrons_spatiaux.py` | Patron spatial de chaque scénario (`patron_a_respecter` / `a_eviter` écrits à la main dans `_ANALYSE`, `state_logic` relu du vault) ; utilisé par la génération de zones et le garde-fou spatial (§4). |
| `chantiers.py` | Lecture / écriture de `chantiers_geographie.yaml` (§4bis). |

## 1bis. Utilitaires partagés des diagnostics de géographie

| Fonction | Fichier | Rôle |
|---|---|---|
| `_tokens()` | `check_origine_reelle_coherence.py` | Découpe une entrée `entite` en noms comparables (parenthèses, virgules, barres) ; réutilisée par `check_conventions_territoires.py` et `check_type_entite_coherence.py`. |
| `_normaliser()` | id. | Forme canonique d'un nom de pays (`ALIASES` de `check_zones_coherence.py`). |
| `_compte_comme_pays()` | id. | `type_entite: pays` → toujours ; `ville` → jamais ; sinon si le nom est dans `zones_pays.json`. |

⚠ `gui/app.py` et `gui/zone_repository.py` ont leurs propres copies
(`_tokens_entite()`, `_normalise_pays()`) : si la découpe évolue d'un côté, vérifier
l'autre. Même lecture « par mots » dans `appliquer_et_si.py` (`porte_pays_cite()`) et
`extract_localisation.py` (`zone_porte_pays()`).

---

## 2. Génération d'articles

### `generate.py` 🔁 🧩 — un article (ou un par scénario en mode Forcer)
- **Semi-guidé** (défaut) : un scénario (`config.yaml` ou `--scenario`), instances
  choisies par pertinence thématique ; zone, titre, angle éditables.
- **Forcer** : garantit un élément précis (instance, événement ou signal) comme sujet
  central ; angle généré, titre toujours laissé à l'IA. Un article par scénario
  retenu, résumé du lot en fin de run ; toute résolution impossible arrête le run.
```bash
python3 generator/generate.py                       # semi-guidé, config.yaml
python3 generator/generate.py --dry-run              # prompt affiché, aucun appel
python3 generator/generate.py --mode forcer --forcer-type instance \
    --forcer-slug oracle_des_seuils --forcer-scenarios tous
python3 generator/generate.py --mode forcer --forcer-type evenement \
    --forcer-slug conflit_israel_iran_2026 --forcer-scenarios breakdown policy_reform \
    --forcer-zone moyen_orient_golfe
python3 generator/generate.py --mode forcer --forcer-type instance \
    --forcer-slug terminal_kharg_data_haven --forcer-scenarios policy_reform \
    --forcer-zone-journal maghreb_atlantique --ligne-editoriale pro_pouvoir \
    --thematique international
```
- `--forcer-scenarios` : `tous` (scénarios où l'élément existe réellement) ou liste
  séparée par des espaces. `--forcer-zone` remplace le choix des scénarios (une zone
  n'appartient qu'à un scénario).
- **Journal d'une autre zone** (`--forcer-zone-journal`, champ GUI « Journal d'une
  autre zone ») : le journal de cette zone couvre l'élément comme un **fait étranger**
  (date et lieu de publication = la rédaction ; sources à distance ; conséquences
  vues depuis la zone du journal). Seuls les scénarios où la zone a une rédaction
  sont traités ; `zone_principale` = zone du journal. Liste GUI :
  `/api/slugs?type=zones_journal_forcer`.
- Le mois de parution actif fixe la date (§2quinquies) ; un article isolé ne le fait
  jamais avancer. Bandeau GUI « mois utilisé » (`GET /api/edition/active`).
- Override ponctuel du mode oral : `--type-diffusion`, `--intervenant` (§2quater).
- `validate_config_semi_guide()` refuse un `zone_slug` absent de `journaux.yaml`.

**Sélection des instances** (`loader.py`) :
- 6 entités au plus ; au-delà de 6 candidates, les ex-aequo sont départagés par
  l'usage passé (`state/instance_usage.json`) ; même rotation pour les jalons
  (`trajectory_usage.json`) et les événements custom (`event_relevance_usage.json`).
- **Cooldown** : après `COOLDOWN_STREAK` (2) sélections consécutives, une instance est
  écartée pendant `COOLDOWN_DURATION` (3) occasions (≈ 40 % de présence au plus).
  Exemption de dominance écrasante (`DOMINANCE_EXEMPTION_GAP = 10`) ; les instances
  custom et `priorite_forcee` n'y passent pas.
- **Ancrage local** : quand une zone est fixée, jusqu'à 3 des 6 entités sont des
  instances localisées dans la zone du journal (N1 et sous-zones), au plus 2 d'autres
  N1, transnationales libres ; places non remplies laissées vides
  (`[loader] Zone du journal : N locale(s)…`).
- ⚠ Une génération réelle **modifie toujours** les trois fichiers d'usage. Après un
  test qui ne doit pas laisser de trace : `git checkout -- state/instance_usage.json
  state/trajectory_usage.json state/event_relevance_usage.json`, et vérifier
  `git status state/` (fichiers non suivis compris).

### `generate_series.py` 🔁 🧩 — série d'articles
Plusieurs thématiques avec cohérence temporelle, pilotée par `config_series.yaml`
(`annee_edition` / `mois_edition` facultatifs : mois actif par défaut). Sortie dans
`articles/{scenario}/` avec `_index.md` (réécrit à chaque série). Champ « Illustration
des articles » : Aucune / Toutes / Aléatoire 25 % (`photo_policy`).
```bash
python3 generator/generate_series.py [--dry-run] [--scenario breakdown] [--validate-first]
```
Pour remonter le volume d'une revue : série ciblée (scénario + ligne éditoriale), voir
backlog S23.

### `generate_journaux.py` 🔁 🧩 — rédactions par zone (`journaux.yaml`)
Une entrée par zone N1 × ligne éditoriale : `nom`, `ton`, `langue_style`,
`type_diffusion`, 6 `journalistes` couvrant les 20 thématiques (+ `orateurs` si
oral), fiche publique. Tier `strict`.
```bash
python3 generator/generate_journaux.py --scenario NOM | --all [--ligne pro_pouvoir|opposition|all]
python3 generator/generate_journaux.py --update               # zones manquantes seulement
python3 generator/generate_journaux.py --fill-journalistes    # complète le champ journalistes
python3 generator/generate_journaux.py --all --fill-presentation [--force]   # fiche publique
python3 generator/generate_journaux.py --dry-run
```
- **Fiche publique** (`--fill-presentation`) : `presentation`, `ville` (« itinérant »
  si clandestin), `periodicite` (liste fermée), `fondation` ; lots de 5,
  `creative_souple`, `.bak_presentation` ; rien d'autre n'est touché.
- ⚠ Le mode complet (sans `--update`) **remplace** chaque entrée (efface fiches,
  `seniorite`, `ton_personnel`…). `_reseau` est réécrit à chaque lancement.
- Lots de 3 zones. Depuis le 31 oct 2026, **aucune rédaction factice** : réponse
  lue avec tolérance (texte autour, virgules finales ; d'une réponse tronquée, les
  journaux complets sont gardés) ; zones manquantes d'un lot retentées une fois
  seules ; une zone encore ratée n'est pas écrite et est listée en fin
  (« relancer avec --update »). Réponse illisible gardée dans
  `gui/logs/llm_json_echec_journaux_*.txt` ; `journaux.yaml.bak` avant chaque
  écriture.

### `check_journaux_coherence.py` 🔁 🗄️ — zones N1 ↔ `journaux.yaml`
Manquantes et orphelines dans les deux sens, 6 scénarios × 2 lignes. Lecture seule.

### `clean_fallback_journaux.py` 🔁 🗄️
Retire les rédactions factices du fallback de `--update` (nom « Édition … », `ton` et
`langue_style` vides). Faire une copie de `journaux.yaml` avant. Ne sert plus
qu'aux restes antérieurs au 31 oct 2026 (le fallback factice n'existe plus).

### `trace_injection.py` 🔁 🧩 — parcours d'un élément
Origine, scénarios et zones, variables influencées, relations, usage dans les
articles (scan récursif), et **effet sur le monde** (moteur dynamique, récit, graphique
GUI : §3ter).
```bash
python3 generator/trace_injection.py --slug oracle_des_seuils --type instance [--json|--report]
python3 generator/trace_injection.py --slug pacte_tabriz_2058 --type evenement --scenario breakdown
python3 generator/trace_injection.py --list --type instance
```
Accepte un slug d'instance à la place du slug d'entité. GUI : menu Type puis Élément
(liste en cascade), route `/api/trace/<slug>`.

### `generate_manual.py` 🪦 (hors GUI)
Construit le prompt du prochain article d'une série pour le coller dans un chat
(`prompt`, `status`, `save fichier.txt`), état dans `state/manual_progress.json`.
Remplacé dans l'usage courant par `generate.py --dry-run`.

---

## 2bis. Contenu du prompt d'article et plafonds

- Le prompt reprend pour chaque instance `responsabilites` et `signes_distinctifs`
  (en entier), pour les événements custom `realisation` et `consequences` (tronqués),
  les jalons « majeurs » (3 au plus, `MAX_JALONS_RUPTURES_MAJEURES`) avant les
  « structurants », et les forces attractives / répulsives des variables (section
  « 3. Dynamique interne » des fiches `variables/`).
- **Plafonds** : événements custom — 8 en détail (pertinence + rotation), 25 au plus
  en liste compacte ; zones — pertinentes en détail, 20 au plus en liste compacte.
  L'élément forcé est toujours en détail, badge `[FORCÉ]`, et sa zone toujours dans
  la géographie détaillée.
- **Pertinence d'un événement custom** (`_score_evenement_pertinence`) : 3 × variables
  communes avec les variables visibles de la thématique + 1 × variables secondaires
  + 1,5 × rang de portée + 0,1 × amplitude (plafonnée à 40). La rotation ne départage
  que les ex-aequo. Conséquence : bien choisir `variables_hint` à l'injection compte
  plus que la portée ; pour garantir qu'un article traite un événement, utiliser le
  mode Forcer.
- Non utilisés dans le prompt (choix assumé) : `impact_local`, `zone_geographique`,
  `type_relation_dominante`, `annee_debut` / `annee_fin`, `generation`,
  `constrained_variables`, le `type` des zones, le bloc `simulation` des variables.

**Liens marquants (B3.1, nov. 2026).** Le prompt de l'article contient aussi une ligne « liens
marquants dans ce scénario », tirée de `coupling_intensity` (2 à 4 liens par scénario),
à côté de `state_logic` et `dominant_dynamics`. Aucun calcul du moteur n'en dépend.

## 2ter. Longueur, date, signature — règles en place et protocole de test

- **Longueur** : consigne répétée dans les « Contraintes impératives ». Si l'écart
  dépasse **40 %** de la borne dépassée, l'article est **régénéré une fois** en entier
  avec l'écart chiffré (jamais de boucle). Frontmatter : `mots_reels`,
  `retry_longueur: oui|non`.
- **Date** : la date fictive calculée est transmise à l'IA, qui doit la reprendre
  telle quelle ; nom de fichier translittéré (`19fevrier2098`).
- **Signature** : toujours demandée, format « Nom — Journal », **en haut sous la
  date, une seule fois** (nom curaté si la rédaction en a un). `journaliste_slug` est
  fixé depuis le profil, jamais lu dans le texte.
- **Titre** : à la française, jamais tout en capitales (§2nonies) ; règle temporelle :
  une année antérieure à 2098 est du passé.
- **Protocole de test** d'un changement de `prompt_builder.py`, `api.py`,
  `generate.py`, `generate_series.py` :
  1. `git status state/` propre avant de commencer ;
  2. `generate.py --dry-run` sur 1-2 thématiques ;
  3. lot réel via `generate_series.py` (`longueur: auto`, 2-3 articles par thématique,
     la génération étant à température 1,0) ;
  4. nettoyage : supprimer les articles de test, `git checkout --` des trois fichiers
     d'usage, vérifier les fichiers non suivis de `state/`.
- `audit_longueur_articles.py` (§5) mesure l'écart sur tout le corpus.

## 2quater. Rédactions — journalistes, orateurs, `ton_personnel`

`journaux.yaml` (par zone N1 × ligne) : `nom`, `ton`, `langue_style`,
`type_diffusion` (`ecrit` par défaut, `oral`, `mixte` = tirage 50/50 par article),
`journalistes`, et `orateurs` si oral ou mixte (`nom`, `seniorite`,
`communautes_desservies`, `reputation_orale`) ; `ton_personnel` facultatif par
personne. Onglet GUI **Rédaction** : liste par zone, clic sur une personne → nombre
d'articles, liste, lien Obsidian.

| Outil | Rôle | Commande type |
|---|---|---|
| `audit_couverture_journalistes.py` 🔁 🧩 | Combinaisons zone × thématique à 0 ou 1 journaliste éligible (lecture seule) | `--seuil 1`, `--report` |
| `propose_couverture_journalistes.py` 🔁 🧩 | Propose d'ajouter des thématiques aux journalistes les moins chargés (n'écrit jamais) | — |
| `inject_journaliste_custom.py` 🔁 🧩 | Comble les trous. `--mode manuel` (`--nom` + `--thematiques` = sans IA ; `--genre`, `--seniorite`, `--avec-ton-personnel`) ; `--mode auto` (`--scenario` ou `--all`, `--cible`) : redistribue sous `MAX_THEMATIQUES_PAR_JOURNALISTE = 6` ou crée un profil | `--mode manuel --scenario NOM --ligne pro_pouvoir --zone-slug SLUG --thematiques meteo,sante` |
| `inject_orateur_custom.py` 🔁 🧩 | Orateur·rices. `--mode manuel` ; `--mode auto` (`--scenario` obligatoire, jamais `--all`, zones déjà orales) ; `--mode convertir` (bascule `type_diffusion` et crée les orateurs, liste explicite `--zones ligne::zone_slug`, `--type-diffusion-cible oral|mixte`) | `--mode convertir --scenario breakdown --zones pro_pouvoir::maghreb_mediterraneen` |
| `set_ton_personnel.py` 🔁 🧩 | Nuance de style personnelle, en complément du `ton` de la zone. `--nom` (IA), `--ton-personnel "…"` (direct), `--all-manquants`, `--overwrite` pour remplacer | `--scenario NOM --ligne pro_pouvoir --zone-slug SLUG --nom "Nom exact"` |

- `--avec-ton-personnel` : **mode manuel seulement** (la relecture individuelle est le
  point de contrôle). Garde-fous de `ton_personnel` : pas de citation, pas de
  stéréotype culturel de 2026, 35 mots au plus.
- Garde-fous : thématiques hors `THEMATIQUES_CONNUES` filtrées (retry si la liste se
  vide) ; `communautes_desservies` en locutions courtes (retry au-delà de 9 mots).
- **`STYLE_ORAL`** (`prompt_builder.py`) : adresse directe, formules ritualisées,
  répétitions, pas de chapô ni d'intertitres, accroche → développement → appel ou
  question, call-and-response ; ton hérité de la zone ; `MOTS_MAX_ORAL = 700`.
  Accepté : l'IA ajoute parfois une signature en mode oral (sans effet sur
  `journaliste_slug`).
- GUI du mode convertir : `--zones` en puces cochables
  (`/api/slugs?type=zones_candidates_oral&scenario=X`).

## 2quinquies. Mois de parution

Le monde avance mois par mois : la date d'édition entre dans le calcul du snapshot.
**Un mois de parution global** pour les 6 scénarios.

- **Registre** `state/editions.json` : `edition_active` (`numero`, `annee`, `mois`),
  `editions_connues` (toute édition déclarée), `historique` (articles réellement
  produits, par scénario).
- **`definir_edition.py`** 🔁 🧩 (section « Mois de parution du journal ») : fixe ou
  avance le mois sans générer d'article.
  ```bash
  python3 generator/definir_edition.py --annee 2098 --mois 9
  python3 generator/definir_edition.py --statut
  ```
- `generate_series.py` : mois actif par défaut, surchargeable dans
  `config_series.yaml` ; incrémente l'historique à la fin d'un lot réel.
  `generate.py` lit le mois actif sans jamais l'avancer ; sans registre, repli sur
  l'année 2098 entière. Bandeau GUI « Mois de parution » sur tous les écrans.
- **`audit_sujets_edition.py`** 🔁 🧩 (Validation) : articles d'un mois et événements
  custom déjà injectés pour ce mois (`--scenario`, `--annee` + `--mois`, `--json`).
- **Événement daté du mois** : `edition_active: true` sur une idée de
  `evenements_custom/queue.yaml` remplace la date proposée par l'IA par le mois actif.
- **Injection directe d'une idée** : `inject_custom_events.py --idea '<json>' --json`
  (ne lit ni n'écrit `queue.yaml`), utilisée par « Promouvoir en événement » (§2sexies)
  et par le simulateur (`et_si_injecter.py`, §3quinquies).
- Limites : un événement injecté n'apparaît que s'il est jugé pertinent (§2bis) ; la
  cohérence des formulations relatives (« il y a un mois ») dépend de l'IA (à observer).

## 2sexies. Suite narrative des événements et basculements

- **`developpements`** (fiches `event_instances/`) : à chaque article généré en mode
  Forcer sur un événement, une entrée (`date_label`, `article_slug`, `resume` = chapô)
  est ajoutée ; au forçage suivant, l'IA reçoit « déjà raconté, poursuis à partir de
  là ».
- **`evenements_cites`** (frontmatter d'article) : événements effectivement traités.
- **Onglet Articles** : tableau filtrable (scénario, thématique, ligne, zone, « Mois en
  cours seulement », « Basculement narratif détecté »), panneau de détail
  (redimensionnable, « Ouvrir dans Obsidian »). Action **« ✨ Envoyer vers « et si ? » »** (depuis le 7 nov 2026, remplace « Promouvoir en
  événement » ; l'ancien formulaire reste jusqu'à l'étape 5 de l'unification, voir §3quinquies) :
  texte pré-rempli (chapô, date, scénario, zone, entités citées, source) + réglages ; ancien
  formulaire, pour mémoire : formulaire pré-rempli (id, description depuis le chapô, zone, acteurs depuis
  `entites_citees`, scénarios, variables, date approximative = année de l'article,
  `date_precise` ; `edition_active` décoché par défaut ; dry-run possible). L'IA garde
  la saison d'un article contemporain et suit le récit d'un article rétrospectif (cas
  ambigus à vérifier à la main).
- **`detect_basculements_narratifs.py`** (lecture seule, un appel par scénario, sur les
  chapôs) : articles qui marquent une aggravation, amélioration, déblocage, blocage ou
  émergence de crise. Bouton « Détecter les basculements narratifs » de l'onglet
  Articles (scénario filtré ou tout le corpus), cache
  `state/basculements_narratifs.json` fusionné par scénario. La sélection est fiable,
  l'étiquette `type_bascule` moins : lire la justification.
- **Audit par sujet** (`audit_sujets.py`, `editer_sujets.py`, onglet « Audit par
  sujet ») : retrouver les occurrences d'un sujet, supprimer, corriger une date.
- `audit_inventaire_articles.py` (`--md`, `--csv`, `--json`) : inventaire lecture seule
  (alimente l'onglet Articles et Rédaction).

## 2septies. Onglets d'inventaire et résumés par scénario

Onglets **Instances**, **⚡ Événements** et **📡 Signaux faibles** : tableau filtrable,
trié, paginé + panneau de détail redimensionnable (280-900 px, double-clic = défaut,
largeur mémorisée par onglet). Lecture seule.

| Onglet | Script | Particularités |
|---|---|---|
| Instances | `audit_inventaire_instances.py` (`--scenario`, `--detail`, `--md`, `--csv`, `--json`) | Entité parente résolue (⚠ si introuvable), `transnationale` = zone vide ; filtres type, trajectoire, transnationales, clandestines. Rapport `documentation/inventaire_instances.md`. |
| Événements | `audit_inventaire_event_instances.py` | Archétype parent résolu ; filtres portée, type, « impossible » ; description en tête. |
| Signaux faibles | `audit_inventaire_signaux.py` | Pas de `scenario` en frontmatter : rattachement lu dans le bloc « Trajectoire injectée » (`signal_to_state[].scenarios`) ; une entrée par variable cible (normal) ; « Impact chiffré » facultatif ; `README.md` exclu. |

**📝 Résumés par scénario** (`generate_resume_scenarios.py`, `--scenario`, `--md`,
`--json`) : 2-3 paragraphes par scénario, un appel `creative_souple` ; éléments retenus
sans IA (15 instances au plus fort impact, 10 événements de plus grande portée). Une
carte par scénario avec « Générer / Régénérer », bouton global ; cache
`state/resume_scenarios.json`. Payant : jamais lancé tout seul. Un événement de portée
régionale peut ne pas y figurer.

Outils ponctuels liés : `scan_frontmatter_casse.py` (frontmatters illisibles du vault),
`fix_name_non_quote.py <fichier> --apply` (met entre guillemets un `name:` contenant
`:`).

## 2octies. Site des revues

Les articles sont publiés en **12 revues de presse** (modèle *Courrier
International*) : une pro-pouvoir et une d'opposition par scénario, chacune ne reprend
que les journaux de son camp. En ligne : **https://ourrassol.pages.dev** (pages
statiques ; le GUI reste local).

- **`generator/revues.yaml`** : `nom`, `reseau_source`, `sous_titre`, `fondation`,
  `ville_siege`, `periodicite`, `style_visuel`, `langue_publication`, et au besoin
  `statut: privee_toleree` (*Le Moniteur de l'Ordre*, *Limes*, siège Genève-Bunker) ou
  `diffusion: radio_transcriptions` (*Radio Frontières*).
- **Rattachement** : revue = `scenario` + `ligne_editoriale` ; journal = première zone
  à rédaction en remontant depuis `zone_principale` ; signature = la personne de
  `journaliste_slug` si elle appartient au journal (journalistes et orateurs), sinon
  « La rédaction de *journal* » ; « Traduit du … » = première langue de `langue_style`.
  Publiés : articles rattachés, datés jusqu'au mois de parution actif. Non publiables :
  sans ligne, sans zone, ou zone sans journal sur sa chaîne.
- **Organisation** : kiosque (hors fiction) → par revue : Une, 8 continents (zones),
  20 thématiques, pages zone, pages article (fil d'Ariane, chapô de revue, signature,
  « La source », mots-clés, « Lire aussi »), « Nos sources », recherche. Toutes les
  zones et thématiques apparaissent, même vides. Numéro = (année − fondation) × 12 +
  mois. Bandeau et pied : « Rédaction à <ville siège de la revue> ».
- **Continents** : majorité des pays de la zone ; « Monde » si aucun continent n'atteint
  40 % sur au moins 3 continents ; forçage dans `generator/continents_zones.yaml`
  (`{scenario: {zone: Continent}}` ; forçages actuels :
  `policy_reform/bloc_souverainiste_non_signataire`, `fortress_world/zones_grises_tampons`,
  `reference/institutions_multilaterales_survivantes` → Monde ;
  `fortress_world/al_hima` → Europe ; `breakdown/arc_sahelo_mediterraneen` → Afrique).
- **Titres** à l'export : guillemets retirés seulement s'ils encadrent tout le titre ;
  titre à plus de 80 % en capitales remis en casse française (`normaliser_capitales()`) ;
  les articles du vault ne sont pas modifiés.
- **Recherche** (loupe sur chaque revue et le kiosque) : index `recherche.json` par
  revue et global, texte complet, dans le navigateur ; ne marche que servi
  (`python3 -m http.server -d site`, ou en ligne).

```bash
python3 generator/export_revues.py                 # audit : publiables / signés / refusés
python3 generator/export_revues.py --detail | --csv audit.csv | --continents
python3 generator/export_revues.py --build [--mois 2098-09]   # génère site/ seulement
python3 generator/chapos_revues.py --dry-run | --limit 3 | (rien) | --refaire reference/<f>.md
bash generator/publier_site.sh --dry-run           # fichiers ajoutés / modifiés / supprimés
bash generator/publier_site.sh                     # build + copie + commit + push
```
- **`chapos_revues.py`** 🔁 🧩 : chapô propre à la revue (un appel par article,
  `creative_souple`), stocké dans `state/chapos_revues.json`, jamais dans les articles ;
  refait seulement si le texte de l'article change ; 60 mots au plus, commence par le
  fait, cite le journal une fois. Annonces et Météo n'en ont pas.
- **`publier_site.sh`** lance lui-même `--build`, copie `site/` dans le dépôt privé
  `DavefromOurrassol/ourrassol-site` (cloné à côté du vault ; `SITE_REPO=` pour un autre
  chemin), commit et push ; Cloudflare Pages (projet `ourrassol`, branche `main`, sans
  commande de build) republie en 1-2 minutes. `site/` est dans le `.gitignore`.
  Connexion GitHub : « Continue with Apple ».
- **Audit dans le GUI** : « 📰 Audit des revues (site) », section Validation
  (`--detail`, `--continents`).
- **`reparer_bloc_metadonnees.py`** (sans IA) : article contenant encore
  `===METADONNEES_PUBLICATION===` → reporte chapô, tags, `image_prompt` dans le
  frontmatter et retire le bloc (`.bak_meta`) ; aperçu, `--apply`. Puis
  `chapos_revues.py` et publication. Depuis le 31 oct 2026, `api.py` retire aussi
  un bloc non fermé ou en double à la génération : l'outil ne sert plus qu'à
  l'existant.
- Suites (identités visuelles, photos, audio, multilingue) : backlog chantier 5.

## 2nonies. Journaux, zones et audits d'articles

- **Résolution du journal** (`get_journal_profile()`) : remonte depuis la zone exacte
  de l'article (sous-zone, parents, N1) jusqu'à la première rédaction ; sans zone :
  réseau global et signature inventée (`[WARN][journal] Aucune zone fournie`).
  `export_revues.py` applique la même remontée.
- **`validate.py` section 12 `[JOURNAUX]`** : erreur si une clé de `journaux.yaml`
  n'existe pas dans la géographie ou si une rédaction est factice ; avertissement si
  une zone N1 n'a pas de rédaction.

| Outil (CLI) | Rôle | Écrit ? |
|---|---|---|
| `audit_signatures.py` | Signatures hors rédaction de leur zone, par cause et par mois (n'exclut pas `_index.md`) | non |
| `audit_lieu_zone.py` | Zone de chaque article récent + début du texte, à comparer à l'œil | non |
| `audit_temporel.py` | Années passées employées au futur ; rapport `generator/state/audit_temporel.md` | non |
| `rezoner_articles.py` | Corrige `zone_principale` d'articles anciens ou sans zone (IA parmi les zones à rédaction ; cache `state/rezonage_articles.json`, rapport `rezonage_rapport.md`) ; `--jusqu-au`, `--corriger DEBUT_FICHIER=ZONE`, `--apply` sans IA | `--apply` (`.bak_rezonage`) |
| `reattribuer_signatures.py` | Remplace une signature hors rédaction par une personne du bon journal ; à lancer après un rezonage | `--apply` (`.bak_signature`) |

---

## 3. Entités, événements et signaux custom

Trois files (§0) alimentent le vault : entités (+ instances), événements (+
event_instances), signaux faibles. Après une création réussie, le **cycle
post-injection** se lance tout seul : `extract_localisation.py` →
`review_localisation.py --auto-resolve` → `validate.py`.

**Dimension temporelle** (modes `auto` / `auto-suggest`) : la répartition des dates
du vault (bandes proche 2026-2035, moyen 2036-2060, lointain 2061-2098) et les
années trop concentrées (> 12 % d'un échantillon d'au moins 15) sont données à l'IA,
qui doit compenser ; une idée proche (avant 2036) doit s'ancrer sur une dynamique
réelle documentée.

### `create_entities_and_instances.py` 🔁 🧩 — créer une entité et ses instances
Crée l'entité **et** génère ses instances dans le même run (tier `structured_strict`).
Pour une entité **existante**, utiliser `generate_instances.py`.
- **custom** : idées de `entites_custom/queue.yaml` — `nom`, `category`, `role`,
  `etat` (une des 11 trajectoires, contrainte dure dans le scénario de référence),
  `est_clandestin` (facultatif), `scenario_ref`, `scenario_hint`, `zone_hint`,
  `consignes_scenarios` (`{scenario: texte}`, injectée seulement dans ce scénario et
  gardée dans la fiche entité), `priorite_forcee`, `source`. L'IA déduit
  l'archétype, crée l'entité, puis les instances.
- **auto** : crée et injecte directement N entités (`--n`, `--category`,
  `--scenario` = contrainte dure, plusieurs valeurs possibles).
- **auto-suggest** : propose N idées et les **ajoute seulement à la file**.
```bash
python3 generator/create_entities_and_instances.py --mode custom
python3 generator/create_entities_and_instances.py --mode auto --n 3 --category humain --scenario eco_communalism breakdown
python3 generator/create_entities_and_instances.py --mode auto-suggest --n 5 --scenario policy_reform
```
- Depuis le GUI, `--n` doit être rempli (pas de saisie au clavier possible).
- Catégories valides : IA, organisation, entreprise, institution, infrastructure,
  réseau, humain, système, hybride, autre, média, territoire (« milice » n'en fait pas
  partie). Une catégorie ou un `scenario_ref` invalide part en `needs_review` avec son
  motif affiché.
- **Bloc d'impact** (mode custom seulement) : l'instance porte `impact_sur_variables`
  (1-3 variables), `propagation_via_matrice`, `contexte_injection` dans son bloc
  `injection:` ; plafond = `impact_systemique_global × 5`. Une force au-dessus du
  plafond est **ramenée au plafond** (signe gardé, ⚠ à l'écran, trace
  `plafond_applique`) au lieu de faire échouer l'instance ; impact 0 → refus.
- Une idée rejetée va dans `needs_review.yaml` ; un échec **après** la création de
  l'entité, sur une seule instance, n'y va pas : le repérer avec
  `audit_instances_manquantes.py` et relancer `generate_instances.py`. Ne pas remettre
  l'idée en file (le contrôle anti-doublon refuserait l'entité existante).

### `generate_instances.py` 🔁 🧩 — instances d'une entité existante
Entrée GUI « Générer les instances manquantes ». Relit la fiche entité (rôle,
consignes) et génère les instances absentes.
```bash
python3 generator/generate_instances.py --entity SLUG --scenario breakdown
python3 generator/generate_instances.py --entity SLUG --scenario breakdown --injection-custom
python3 generator/generate_instances.py --entity SLUG --scenario reference --role "…" --force
python3 generator/generate_instances.py --entity SLUG --scenario fortress_world --consigne "…" --force
```
- `--force` régénère une instance existante (réécrit **toute** la fiche, retouches
  manuelles et `exclure_articles` compris). `--dry-run` appelle l'IA sans écrire.
- `--role` : nouveau rôle du **scénario de référence** ; `--consigne` : consigne d'un
  **autre** scénario (refusé sinon). Les deux exigent `--entity`, `--scenario`,
  `--force`.
- `--injection-custom` : garde (ou crée) le bloc d'impact d'une instance custom.
- `--ancrage-temporel recent` : nouvelles instances dans les 1-3 prochaines années,
  ancrées dans `etat_du_monde_reel.md`.

### `inject_custom_events.py` 🔁 🧩 — injecter des événements
Crée l'archétype (`evenements/{slug}.md`) et une instance par scénario
(`event_instances/{slug}_{scenario}.md`) ; tier `structured_strict`.
- **custom** : traite toute la file `evenements_custom/queue.yaml`. Champs : `id`,
  `description`, `portee`, `date_approximative`, `intensite`, `persistance`
  (`ephemere | normale | durable | permanente`, durée de l'effet ; ≠ `intensite`, qui
  oriente la force), `scenarios`, `variables_hint`, `variables_hint_count` (défaut 2,
  filtre dur), `acteurs_hint`, `acteurs_hint_count` (filtre dur), `zone_hint`
  (revalidé pour chaque scénario ; invalide → ⚠ et zone libre), `edition_active`,
  `source`.
- **auto** : propose N idées et les ajoute seulement à la file.
- **`--idea '<json>' [--json]`** : injecte UNE idée sans toucher la file (onglet
  Articles, simulateur).
```bash
python3 generator/inject_custom_events.py --mode custom
python3 generator/inject_custom_events.py --mode auto --n 3 --scenario breakdown
python3 generator/inject_custom_events.py --idea '{"id": "...", ...}' --json [--dry-run]
```
- L'étape de développement reçoit la chronologie réelle du scénario et
  `etat_du_monde_reel.md`, et doit rester cohérente avec eux ; garde-fou
  `impossible_dans_scenario`. `evenement_cle` doit contenir une année (n'importe où).
- **Champs imposés par le simulateur** (§3quinquies), contrôlés avant tout appel IA
  (entrée invalide → `needs_review`) :
  - `impacts_imposes` (`{scénario: [{variable, delta_level 1-25, duree, polarite ±1}]}`),
    `date_imposee` (2025-2098, ignore `edition_active`), `via_matrice_impose` ; l'IA
    écrit le récit, les chiffres sont remis après sa réponse ;
  - `faits_imposes` (`{scénario: [{fait, slug, sort}]}`, `sort` : `disparait`, `change`,
    `reste`, `zone`, `contrainte`) : le récit ne doit jamais les contredire ;
    ⚠ (sans rejet) si une entité « reste » est associée à une destruction, ou si le
    mot « matrice » apparaît. **Depuis le 31 oct 2026** (`verifier_contraintes`), les
    faits `contrainte`, `change` et `zone` sont vérifiés par un appel IA
    (`structured_strict`, ≈ 1 centime par scénario) une fois la validation passée :
    fait non respecté (contredit, remplacé par un autre rattachement, sens
    d'évolution inversé) ⇒ **une** réécriture par le mécanisme des problèmes de
    validation, puis ⚠ « fait imposé non respecté » s'il l'est toujours (non
    bloquant) ; appel en échec ⇒ ⚠ « relire le récit à la main ». Sans
    `faits_imposes`, aucun appel ;
  - `mode_impose` (`choc` | `rupture`) : chaque fiche écrite porte `mode: rupture`
    (lu par le moteur, §3ter).
  - `acteurs_hint` s'applique par scénario (un slug d'un autre scénario n'est pas
    imposé).
- **Passage de l'article d'origine** (U3s → U3y, 11 nov 2026) : si un fait imposé
  `contrainte` d'au moins 8 mots se retrouve dans **un seul** article de
  `articles/<scénario>/`, le prompt de développement reçoit son paragraphe et ses deux
  voisins (≤ 2 800 car.), avec des consignes de fidélité (description sobre, événement à
  sa date, pas de citation, chiffre, sigle ni nom de scénario ajoutés). Contrôles non
  bloquants en fin de scénario : citation « … » absente de l'article, nom de scénario
  dans la description ou les conséquences, année postérieure à l'événement ou
  « aujourd'hui ». Le fait tiré de l'article est marqué `[ARTICLE]` pour
  `verifier_contraintes` (omission = non respecté). Sans article retrouvé, rien ne change
  (prompt d'avant, description « vivante »). Détail : §3quinquies, « Articles → « et si ? » ».
- Résultats dans `processed.yaml` (`partial` si succès partiel) et `needs_review.yaml`
  (l'idée complète y reste, pour la relancer).

### `inject_custom_signals.py` 🔁 🧩 — injecter des signaux faibles

*Nov. 2026 : champs de file ajoutés par « et si ? » — `impacts_imposes`, `date_imposee`, `via_matrice_impose` (valeurs forcées), `contraintes` (faits transmis à l'IA : « FAITS À RESPECTER … ») et `zone_hint` (lieu). Options : `--dry-run`, `--idea <id>`, `--json`.*
Signaux de `signaux_custom/queue.yaml` → fiches variables (`signal_to_state` pour les
6 scénarios + annotation section 7), registre `registre_evenements.md`, fiche d'audit
`signaux_custom/{slug}.md` (sections « Idée source », « Trajectoire injectée »,
« Impact chiffré », « Cohérence avec les signaux existants »).
```bash
python3 generator/inject_custom_signals.py [--dry-run]
```
- Parcours : choix de la ou des variables par l'IA (`variable_hint`,
  `variable_hint_count` tronqué mécaniquement) → rédaction des 6 scénarios par
  variable → validation (mots, fenêtres de dates, collisions) avec 2 relances →
  écriture.
- **Impact chiffré** : une force `delta_level` (1-10, `MAX_DELTA_SIGNAL = 10`, jamais 0)
  et une `polarite` ±1 **par scénario** ; `propagation_via_matrice` toujours
  `true` depuis le 30 oct 2026 (consigne et défaut du code ; le signal se
  diffuse dans le réseau, voir §3ter). `persistance` et `annee_apparition` (année d'observation réelle,
  2025-2097) facultatifs.
- **Plancher de bascule** : aucune fenêtre `date_bascule` ni année d'`evenement_cle`
  avant max(`annee_apparition`, année en cours).
- `zone_hint` = lieu réel de 2026 en texte libre (« Norvège ») ; l'IA trouve la zone
  de chaque scénario. Cohérence avec les signaux proches : repérage lexical, champ
  `signaux_existants_consideres` obligatoire.
- Collision de fenêtre avec un autre signal : avertissement ; collision interne au
  même signal : bloquant.
- **Injection partielle** : les variables réussies sont gardées ; `needs_review.yaml`
  contient une entrée `idee_a_remettre_en_queue` (variables restantes + bloc
  `reprise`) qui, recopiée dans la file, complète le même signal. Une exception sur
  une variable annule son écriture (instantané restauré) sans toucher les autres.
- **Interruption** (Ctrl-C, ou Stop du GUI = SIGTERM ; 31 oct 2026) : `queue.yaml`
  est réécrite après **chaque** idée (seules les idées non traitées y restent, plus
  de doublon sous `_2` au run suivant). Pendant une variable : écriture annulée,
  variables restantes en échec « interrompu », fiche d'audit des variables faites
  et `idee_a_remettre_en_queue` produites, puis arrêt (code 130). Hors des
  variables (sélection, fiche) : l'idée reste en file.
- Slug déjà pris : suffixe `_2`. Les variables sœurs d'un même signal ne réutilisent
  pas le même `evenement_cle`.
- Un signal n'a **aucune garantie** d'apparaître dans un article (texture de fond) ;
  pour un fait sûr et visible, préférer un événement.
- Fiche variable cassée (« Aucun bloc ```yaml trouvé ») : repérer les fiches à nombre
  impair de fences —
  `for f in variables/*.md; do n=$(grep -c '^```' "$f"); [ $((n % 2)) -ne 0 ] && echo "$f : $n"; done`
  — puis `.bak` et ajouter la fence de fermeture en fin de fichier.

### `idees_vers_queue.py` 🔁 — texte libre → entrées de file
```bash
python3 generator/idees_vers_queue.py --type signal --texte "…"
python3 generator/idees_vers_queue.py --type evenement --fichier idees.txt
pbpaste | python3 generator/idees_vers_queue.py --type signal
```
Un appel IA : découpe en idées, description reformulée, `id`, variables (1-4),
persistance, et selon le type `zone_hint` / `annee_apparition` ou `portee`,
`date_approximative`, `intensite`, `scenarios`. Contrôles signalés par ⚠ (variables,
`id` unique, bornes ; ⚠ « ressemble plutôt à un événement »). **N'écrit jamais dans
la file.** Dans le GUI : bouton **« ✨ Compléter les autres champs »** sous la
Description des formulaires « Injecter des signaux faibles » et « Injecter des
événements » (`POST /api/idees/proposer`) ; plusieurs idées → une carte par idée ;
« ↶ Rétablir mon texte ». Sur un texte très court, la description peut s'étoffer :
relire.

### Autres outils de la chaîne entités

| Outil | Rôle | Commande |
|---|---|---|
| `enrich_minimal.py` 🔁 🧩 | Enrichit les fiches `statut: officialise_minimal` (responsabilités, description, tensions, localisation, impacts, relations), réciprocité en fin de run. Plus aucune fiche minimale au 2 août. | `--scenario NOM` \| `--all` \| `--slug SLUG`, `--limit N`, `--auto-cycle`, `--skip-reciprocite`, `--resoudre-conflits [--bascule-en-opposition]`, `--dry-run` |
| `extract_phantom_slugs.py` 🔁 🧩 | Slugs cités mais inexistants → rôles générés → `entites_custom/queue.yaml` | `--source all\|enrich\|validate`, `--report PATH`, `--dry-run` |
| `requeue_needs_review.py` 🔁 🧩 | Remet `entites_custom/needs_review.yaml` en file | `[--dry-run]` |
| `undo_custom.py` 🔁 🧩 | Retire entités, instances, événements, event_instances ou signaux avec leurs dépendances (`.bak`) ; simulation par défaut | `--slug SLUG --type TYPE --generalisation yes\|no [--execute]` ; `--type signal` ; sans argument : `evenements_custom/undo_queue.yaml` |
| `audit_instances_manquantes.py` 🔁 | Instances prévues (`scenarios_instances`) absentes du disque : désaccord de slug / entité entière suspecte (`--seuil-absolu 3`, `--seuil-suspect 0.5`) / échec ponctuel (motif cherché dans `gui/logs/`) | lecture seule |
| `set_selection_instance.py` 🔁 🧩 (🎯) | `exclure` / `autoriser` (`exclure_articles`, personnage en réserve, toujours utilisable en mode Forcer) ; `sans_garantie` / `garantie` (instances custom : place garantie dans les articles) | `--slug SLUG --action exclure` ; `--entite E --scenario S --action sans_garantie [--dry-run]` |
| `fix_alliances_oppositions.py` 🔁 🧩 | Réciprocité des relations (`--reciprocite-seule`), `--ignorer-exclus`, `--resoudre-conflits` (l'opposition l'emporte), `--bascule-en-opposition` ; section « ## Relations » réécrite à sa place | voir « Relations & lore » |
| « Compléter les relations avec l'IA » 🧩 | Remplit les alliances / oppositions vides, puis réciprocité (payant) | section Entités — création |

- `undo_custom.py --type signal` : retire annotation section 7, blocs section 12
  (sans avaler la fence), lignes du registre, fiche d'audit et entrées des fichiers
  `processed` / `needs_review` ; ne recalcule pas la ligne « Total » du registre des
  événements (cosmétique).
- ⚠ Toute régénération d'instance fait perdre `exclure_articles` : ré-exclure (cas
  Hyphan, exclue hors `reference` ; Kharg-9 exclu en eco_communalism).
- **Localisation sans sous-zone** : `zone` = zone existante, `lieu` = texte libre
  (`zone: zone_euro_sud`, `lieu: Milan (QG) — antenne à Lyon`) ; le générateur lit le
  rôle, pas `lieu` : citer aussi la ville dans `role_dans_scenario`.
- Une alliance **secrète** ne va pas dans `alliances` (lue par les articles) : l'écrire
  dans le texte de la fiche.

### Relations & lore — étapes 1 → 5

Une instance est écrite une fois et ne suit pas l'évolution du lore (zone renommée,
pays en quarantaine, entité disparue). Ces outils trouvent et corrigent ce qui a
dérivé. Section du sidebar **« Relations & lore — étapes 1 → 5 »**, dans l'ordre :

| Étape | Entrée | Script | Coût | Écrit ? |
|---|---|---|---|---|
| 1 | 🔍 Vérifier le lore | `audit_lore.py` | gratuit | rapports |
| 2 | 🤝 Rendre les relations réciproques | `fix_alliances_oppositions.py --reciprocite-seule` | gratuit | oui (Simulation cochée par défaut) |
| 3 | 🔀 Retirer les relations vers un autre scénario | `corriger_relations_inter_scenarios.py` | gratuit | `--execute` |
| 4 | 🤖 Relecture IA du lore | `audit_lore.py --llm` | ≈ 0,5 centime / fiche | propositions (Estimer coché par défaut) |
| 5 | ✅ Valider les propositions de l'IA | onglet (`/api/lore/*`) | gratuit | oui, après simulation |

**Routine après un lot d'entités** : 1 → 2 → 3 → `validate.py` (4 et 5 au besoin).

- **Étape 1 — `audit_lore.py`** (sans IA) : règles de `lore_regles.yaml` sur les textes
  des instances et `event_instances` (+ articles avec `--avec-articles`) ; quarantaine
  (instance dans une zone en quarantaine hors `trajectoires_tolerees`) ;
  transnationales localisées dans le texte (information) ; réciprocité et relations
  contradictoires (celles d'un personnage en réserve comptées à part) ; relations
  inter-scénarios (toujours des erreurs : les scénarios sont des mondes parallèles).
  « À faire ensuite » indique l'étape suivante. Sorties :
  `documentation/need_action/audit_lore_{scenario}.md` (section 5 : règles à relire),
  `audit_lore_dernier_lancement.md`, `--json`.
  ```bash
  python3 generator/audit_lore.py --scenario breakdown [--avec-articles]
  python3 generator/audit_lore.py --all
  ```
- **Étape 3** : une relation `X_autre` sur une fiche du scénario S devient `X_S` si
  elle existe, sinon est retirée ; aucune exception ; aperçu, `--execute` (`.bak`).
- **Étape 4 — `audit_lore.py --llm`** (`structured_strict`) : confronte rôle,
  responsabilités, description, tensions à la zone, aux relations et aux messages des
  règles ; renvoie des **contradictions** (extrait + correction) et des **relations**
  certaines et durables, chacune avec une `preuve` (sans preuve ou au conditionnel →
  écartée, « ⊘ »). Garde-fous : `--estimer`, `--slug`, `--zone`, `--limit N`, refus
  au-delà de 15 appels sans ciblage ni `--tout`, cache `state/audit_lore_cache.json`
  (`--no-cache`). Une passe complète (≈ 830 fiches) coûterait 4 à 6 $ : cibler.
  Propositions dans `documentation/need_action/audit_lore_propositions.yaml`.
  ```bash
  python3 generator/audit_lore.py --scenario fortress_world --llm --estimer --limit 10
  ```
- **Étape 5 — onglet ✅** : relations proposées → Garder / À trier / Rejeter (une
  relation rejetée n'est jamais reproposée, `state/audit_lore_rejets.json`) ; « 1.
  Simuler l'écriture » puis « 2. Écrire dans les fiches » (`--appliquer` + réciprocité).
  Contradictions : « Marquer comme traitée », ou correction depuis le GUI (Aperçu,
  Appliquer, `.bak_correction`).

**`documentation/lore_regles.yaml`** (éditable à la main, ou depuis l'étape ⑤ du
simulateur) : une section par scénario (+ `_tous`) avec `zones_quarantaine:
[{zone, trajectoires_tolerees, message}]` et `regles:`. Chaque règle : `id`,
`gravite` (`erreur` | `a_relire`), `termes` (mot entier ; casse et accents ignorés,
sauf termes EN MAJUSCULES avec `sensible_casse`) **ou** `meme_phrase: [[A…], [B…]]`
(un terme de A et un de B dans la même phrase), `message` ; options `sauf_zones`,
`exceptions`, `ignorer_negation`, `suggestion`.
- **fortress_world** : Interzone → Zone Euro Sud ; zones abandonnées (Nordgard,
  Corridor d'Amsterdam, Zone de Koursk) ; quarantaine Heysham ; NAT non neutre ;
  `bruxelles_pas_un_centre` (Halifax-Haute seul centre du Bloc Atlantique).
- **reference** : Ergo-Wian non démocratique ; succession d'Ergo-Wian = Hyphan ; la
  démocratie n'est plus la norme ; `murmansk_transit_arctique_disparu_2081` ;
  `circulation_atlantique_pas_de_redemarrage_2098`.
- **breakdown** : trois fiches disparues avec Genève en 2076
  (`agence_stabilisation_climatique_disparu_2076`,
  `geneve_bunker_institutions_disparu_2076`, `tour_bcuc_geneve_disparu_2076`) ;
  `iran_dans_arc_eurasien_2058`.
- new_sustainability, eco_communalism, policy_reform : aucune règle (backlog S18).
- Les fiches elles-mêmes et l'événement qui les fait disparaître sont toujours
  signalés (légitime) : relire d'un coup d'œil.

---

## 3bis. Trajectoire d'une entité

Une instance porte un seul axe narratif, `trajectoire` :

```
émergent → marginal → ascendant → dominant → mature → déclinant
  → résiduel → transformé → disparu → historique → mythifié
```

- **`est_clandestin`** (booléen) est indépendant de l'axe : une entité peut être
  `dominant` et clandestine.
- **Positions inactives** (`TRAJECTOIRE_INACTIVES`, `validate.py`, seule source de
  vérité) : `transformé`, `disparu`, `historique`, `mythifié`. Elles exigent
  `annee_fin` (contrôle de `validate.py`, avec `annee_debut < annee_fin ≤ 2098`).
  Une fiche passée à `disparu` par le simulateur se réécrit au passé avec
  `fiche_au_passe.py` (§3quinquies).
- **`TRAJECTOIRE_COHERENCE_MAP`** (`validate.py`) : avertissement doux entre la
  trajectoire d'une instance et le `state_of_system` du scénario. Ne couvre que
  `resilient` et `collapsing` ; ailleurs le contrôle est silencieux (voulu).
- `trajectoire_migree_par_defaut: true` marque les fiches passées à `mature` faute
  d'information lors de la migration d'août 2026 : candidates à un retravail ciblé.
- **GUI** : `create_entities` (mode custom) propose les 11 valeurs dans le champ
  `etat`, et `est_clandestin` en oui / non / indifférent.
- **Changer une trajectoire à la main** : `changer_trajectoire.py` (§3quinquies,
  outils unitaires).
- `audit_etat_temporel_fin.py` (section Validation) : fiches inactives sans
  `annee_fin` ; correction par `fix_annee_fin_manquant.py` (§6).

---

## 3ter. Injection et propagation dynamique

Comment un événement, une instance ou un signal injecté modifie le monde jusqu'en 2098.

### Convention d'intensité
- **12 variables, 0 = calme, 100 = crise maximale.** Chaque fiche `variables/*.md`
  porte un bloc `echelle:` (`type: intensite`, `zero:`, `cent:`).
  `gouvernance_institutions` et `frontieres_du_systeme` se lisent dans le sens
  fragilité / désordre.
- Un impact (`impact_sur_variables`) = `delta_level` (force, **toujours ≥ 0**) +
  `polarite` (**+1 aggrave, −1 apaise**) + `duree` + `annee_injection` +
  `propagation_via_matrice`. Effet = `abs(delta) × facteur × polarite`.
- Les prompts d'injection reçoivent l'échelle de chaque variable et la consigne
  (`echelles.py`) ; `verifier_impact()` signale un delta négatif ou une polarité
  invalide.
- Matrice (`influence_matrix.md`) : liens en +1 (« la crise de A aggrave B ») et
  3 amortisseurs en −1 (économie → climat, production → climat, production → énergie).

### Moteur (`dynamique.py`)
Chaque variable est un ressort amorti qui revient vers la référence de son scénario,
poussé par les chocs et par les autres variables via la matrice :
`x'' + 2ζω x' + ω² x = ω² [u + K Σ c·x_j(t − τ)]`, pas mensuel depuis 2025.

| Paramètre | Vient de | Valeurs |
|---|---|---|
| amortissement ζ | `simulation.volatility` | low 1,0 · medium 0,7 · high 0,45 · very_high 0,3 |
| période T | `simulation.resilience` | 1 → 40 ans … 5 → 10 ans |
| couplage c | matrice | poids × polarité × poids temporel × criticité de la source (0,7 → 1,6) |
| retard τ | `lag` de la matrice | lag × 5 ans (`ANNEES_PAR_CYCLE`) |
| choc u | impacts injectés | rampe sur `duree`, puis décroissance selon la persistance × `GAIN_CHOCS` = 0,25 |
| K | `K_COUPLAGE` | 0,05 (réduit par `k_effectif()` si la résonance dépasse 0,9 : le système ne diverge jamais) |

- Sortie bornée : `niveau = ref + marge·tanh(écart/marge)`, marge ≤ 15 points et ≤
  distance à 0 / 100. Près des bornes, un choc bouge peu (backlog S19).
- Un choc `propagation_via_matrice: false` n'agit que sur sa variable. Les
  signaux faibles sont tous à `true` depuis le 30 oct 2026 (effet mesuré :
  1,1 point au plus ; référence `documentation/niveaux_avant_s19_signaux.json`).
- **Choc ou rupture** — règle actée : **un choc s'estompe, une rupture change le
  monde.** Une fiche `event_instances` qui porte **`mode: rupture`** (sous
  `persistance:`) déplace la **référence** du scénario (`ruptures_depuis_donnees()`,
  `rampe_rupture()`, `reference_deplacee()`) au lieu d'agir comme un choc ; les
  voisines voient le déplacement. Lu par `snapshot.py`, `trace_injection.py`,
  `banc_calibration.py` et le simulateur. Sans fiche rupture, calcul identique.
- `snapshot.py` (`MOTEUR_DYNAMIQUE = True`) : une modification par variable dont
  l'écart ≥ 0,5, avec ses 3 principaux contributeurs (« ref → nouveau (±x) — surtout :
  … » dans le prompt) ; tensions calculées après. `False` revient aux anciennes
  fonctions additives.

### Persistance des chocs
| `persistance` | Demi-vie | Usage |
|---|---|---|
| `ephemere` | 10 ans | mode, buzz, crise vite oubliée |
| `normale` (défaut) | celle du type (`DEMI_VIE_PAR_TYPE`, sinon `DEMI_VIE` = 20 ans) | cas courant |
| `durable` | 40 ans | transformation sur plusieurs générations |
| `permanente` | aucune décroissance | institution ou structure encore là en 2098 |

- Table `PERSISTANCE` en tête de `dynamique.py`. Saisie tolérante ; valeur inconnue →
  avertissement, traitée comme `normale`.
- Signaux : champ de la file, recopié dans la fiche d'audit (modifiable à la main).
  Événements : champ de la file, écrit dans l'archétype et chaque `event_instances`.
- **Instances** : l'effet dure tant que l'entité existe — trajectoire active →
  `PERSISTANCE_INSTANCE_ACTIVE` (`permanente`) ; `disparu` / `historique` / `mythifié`
  avec `annee_fin` → pleine force jusqu'à `annee_fin`, puis décroissance ; sans
  `annee_fin` → normale. Un `persistance` explicite dans le bloc `injection` prime.
  `PERSISTANCE_INSTANCES_PAR_TRAJECTOIRE = False` revient au comportement d'avant.

### Outils de mesure (lecture seule, sans IA)
```bash
python3 generator/mesure_niveaux.py --sauver avant.json          # photo des 12 × 6 niveaux de 2098
python3 generator/mesure_niveaux.py --comparer avant.json [--seuil 0.5]
python3 generator/banc_calibration.py [--scenarios all]          # référence, final, écart max, rayon spectral
python3 generator/banc_calibration.py --gain 0.3 --demi-vie 15    # tester un réglage sans rien modifier
python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05   # contrôle après un gros lot
python3 generator/banc_amplitude.py                              # amplitude des chocs (rapport need_action/banc_amplitude.md)
```
Options du banc : `--k`, `--gain`, `--demi-vie`, `--plafond`, `--cycle`, `--fin` ;
sortie CSV (PNG si `matplotlib` est installé) dans
`documentation/need_action/calibration/`. Pour adopter un réglage : modifier la
constante en tête de `dynamique.py`, et mesurer avant / après.

### `trace_injection.py` — effet sur le monde
- Section « Effet sur le monde » : effet net **attribuable** (simulation avec
  l'élément moins sans, propagation comprise), jalons, variables les plus touchées.
- Récit IA (`creative_souple`, ≈ 1 appel par scénario), **vérifié** (chaque chiffre et
  année doit correspondre aux jalons) ; sinon récit modèle sans IA.
- Écrit `generator/state/derniere_trace.json` ; GUI : graphique Chart.js, vues
  « effet » et « niveaux avec / sans » (`GET /api/trace/derniere`).
```bash
python3 generator/trace_injection.py --slug <slug> --type evenement --scenario breakdown
python3 generator/trace_injection.py --slug <slug> --type signal --date 2070 --sans-recit   # gratuit
python3 generator/trace_injection.py --slug <slug> --type instance --skip-effet
```

---


### Matrice d'influence : analyser et réviser (S28.1, 25 octobre 2026)

**Principe.** `influence_matrix.md` est la **seule source** des liens entre les
12 variables : le moteur `dynamique.py` la lit (poids, polarité, retard,
`temporal_weight`). Les fiches de `variables/` n'en gardent qu'une vue générée,
la section « 2. Position dans le système », qu'on n'édite pas à la main. Depuis le
25 octobre, la matrice est asymétrique et creuse : 125 liens sur 132 possibles.

Le champ `variable_type` des fiches (moteur / relais / réactive) reste une
**intention de conception** : il n'est pas recalculé depuis la matrice et peut
différer du classement MICMAC.

**Analyser : `micmac_matrice.py`** (lecture seule, sans IA)

```bash
python3 generator/micmac_matrice.py                    # avec la criticité des variables
python3 generator/micmac_matrice.py --sans-criticite   # poids de la matrice seuls
python3 generator/micmac_matrice.py --puissance 8      # sauts pour l'indirect (défaut 6)
```

- Force d'un lien = |poids × polarité × `temporal_weight` × criticité de la
  source|, comme dans le moteur (table `CRITICITE` importée de `dynamique.py`).
  Un amortisseur (−1) compte comme une influence.
- Influence = somme des liens sortants ; dépendance = somme des entrants ;
  indirect = mêmes sommes sur la matrice élevée à la puissance N.
- Classes : **motrice** (influence ≥ moyenne, dépendance < moyenne), **relais**
  (les deux ≥ moyenne), **dépendante**, **autonome**. « ← levier caché » : la
  classe ou le rang change entre direct et indirect.
- En tête : diagnostic de la matrice (paires symétriques, amortisseurs,
  criticité manquante).
- Référence du 25 oct (indirect) : motrices climat et technologie, dépendante
  territoires.

Quand le lancer : après toute retouche de la matrice ou d'une
`systemic_criticality` ; avant une hypothèse « et si ? » ou une grosse
injection, pour savoir si la variable visée diffuse le choc (climat, technologie)
ou l'absorbe (territoires, valeurs).

**Réviser les poids**

1. **Atelier de la matrice** (page privée) :
   https://claude.ai/artifact/WgAxTF4arr9aRB5w7F9vxf — un lot de 11 liens par
   variable source, curseur de 0 à 1 par pas de 0,05, étoile de la variable
   (sortants, entrants ou les deux), plan influence / dépendance recalculé en
   direct. Repères par lien : « fiche » ou « à examiner », note de la matrice
   Excel préliminaire, poids actuel et poids du sens retour (« inverse »). Les
   poids sont enregistrés dans la page : Claude les relit directement. Le bouton
   CSV n'est qu'une copie de sécurité.
   Lecture des poids : 0 = pas d'effet direct ; 0,2–0,3 faible ; 0,4–0,6 réel
   mais partiel ; 0,7–0,8 fort et régulier ; 0,85–1 majeur, presque mécanique.
2. Référence des niveaux avant changement :
   `python3 generator/mesure_niveaux.py --sauver documentation/niveaux_avant_<x>.json`
3. Report dans la matrice (aperçu, puis écriture avec `.bak_s28`) :
   ```bash
   python3 generator/appliquer_matrice_validee.py documentation/matrice_validee.csv
   python3 generator/appliquer_matrice_validee.py documentation/matrice_validee.csv --apply
   ```
   Seul `weight` change ; un lien à 0 est retiré ; statistiques et tableaux du
   corps régénérés. Le CSV doit couvrir les 132 liens (colonnes `source`,
   `cible`, `poids_valide`), sinon rien n'est écrit.
4. Comparaison des niveaux :
   `python3 generator/mesure_niveaux.py --comparer documentation/niveaux_avant_<x>.json`
5. Fiches variables (aperçu, puis écriture) :
   ```bash
   python3 generator/regenerer_position_fiches.py            # --seuil 0.5 par défaut
   python3 generator/regenerer_position_fiches.py --apply
   ```
   Retire les listes `influences` / `influenced_by` / `bidirectional_links` de
   l'en-tête s'il en reste et régénère la section 2 (liens ≥ seuil, sortants et
   entrants, sens « aggrave » / « amortit », liens réciproques). Idempotent.
6. `python3 generator/validate.py > /tmp/validate.txt; tail -3 /tmp/validate.txt`
   — contrôle matrice : au plus 132 liens, aucune variable isolée.

Changer beaucoup de poids modifie le gain des boucles du moteur (25 oct :
ρ 0,42 → 0,34). Si les niveaux bougent nettement, recaler `K_COUPLAGE` au banc
(`banc_calibration.py`, voir §3ter).

#### Notes sur les outils de données (25 octobre 2026)

- **`undo_custom.py`** : le retrait d'un événement recalcule aussi la ligne
  « Total » du registre (comme pour un signal), avec sauvegarde, et ne retire que
  les lignes dont le slug est exactement celui visé.
- **`audit_signatures.py`** : ignore les fichiers dont le nom commence par `_`
  (dont `_index.md`).
- **`et_si_injecter.py --plan`** : « · » devant une opération déjà faite, « ⚠ »
  devant une vraie alerte.

## 3quater. Veille sur le monde réel

Deux veilles, section GUI **« Référence — monde réel »**. Principe : **pas de
recherche web par API** (essayée sur Mistral et non retenue : sources inventées ou
non lues). Le prompt généré se colle dans l'IA de chat de son choix, qui a le web ; sa
réponse revient dans un emplacement du GUI puis est importée. Seuls les **livres**
déposés et les **flux RSS** sont lus par API, chaque signal étant vérifié contre le
texte fourni.

| Veille | Met à jour | Boutons |
|---|---|---|
| État du monde | `generator/etat_du_monde_reel.md` (« Situation… » des 12 variables) | « Préparer le prompt de veille » → « Importer le résultat de la veille » |
| Signaux faibles | candidats à trier (onglet 🔭) → files signaux ou événements | « 🔭 1. Préparer le prompt », « 📚 Lire les livres (API) », « 📰 Lire les flux RSS (API) », « 📥 2. Importer les réponses » |

Panneaux de prompt : boutons **📋 Copier** et **⬇ Télécharger .md** (option
`"copyable": true` d'un `yaml_files`, fichier relu au clic). ⚠ Un lancement avec
**Aperçu** coché n'écrit pas le fichier : relancer Aperçu décoché avant de copier.

### A. État du monde
```bash
python3 generator/export_prompt_veille.py [--dry-run]        # need_action/veille_prompt_a_copier.md
python3 generator/import_veille_etat_monde.py --dry-run      # aperçu
python3 generator/import_veille_etat_monde.py [--force]      # écriture (--force : réponse d'un autre jour)
```
- Le prompt reprend pour chaque variable toute la partie « Situation… » et demande
  `[MODIFIÉ]` / `[INCHANGÉ]`, plus un bloc `## hors_categories`.
- Réponse à coller dans
  `documentation/need_action/veille_etat_monde_reponses/veille_etat_monde_reponse.md`
  (Éditer → coller → Sauvegarder). L'import remplace la Situation des sections
  `[MODIFIÉ]` (Trajectoire, Perspective, notes conservées), ajoute une révision,
  écrit `veille_etat_monde_diff.md` et archive la réponse. Refuse une réponse non
  modifiée aujourd'hui (sauf `--force`). `hors_categories` n'est jamais intégré
  (alerte, à traiter à la main).
- Après un import : relire le diff section par section (les faits ne sont pas
  vérifiés ; surveiller les formulations trop affirmatives).

### B. Signaux faibles
**Définition** (Ansoff, au sens strict) : phénomène **déjà observable**, encore
**marginal ou incertain**, qui pourrait produire une transformation importante, seul
ou en **combinaison**. Pas un signal : une tendance installée, un gros titre, une
statistique ou un classement, ce qui est déjà connu.

```
sources_signaux_faibles.yaml ─┐
état du monde, signaux_custom,├─► 1. export_prompt_signaux.py ─► prompt ─► IA de chat (1 ou plusieurs)
candidats déjà vus ───────────┘                                               │
documentation/livres/* ─► 📚 veille_livres_api.py ─► veille_signaux_reponses/*.md
flux RSS (champ rss)   ─► 📰 veille_rss_api.py    ─► (même dossier)         │
                              2. import_signaux_faibles.py ◄─────────────────┘
                                        ▼
               state/veille_signaux.json ─► onglet 🔭 (tri) ─► queue.yaml ─► injection
```

- **`generator/sources_signaux_faibles.yaml`** (éditable dans le GUI) : `sources:`
  (`nom`, `url`, `langue`, `famille`, `variables`, `acces`, `rss`, `verifie`, `actif`,
  `ajoute_par`) ; `dossier_livres:` (défaut `documentation/livres`) ; `livres:`
  (exceptions seulement). Une source avec `rss` est lue par le canal RSS et n'est plus
  proposée à l'IA de chat.
- **`export_prompt_signaux.py`** (`--nb 15`, `--depuis "juillet 2026"`, `--dry-run`) :
  écrit `documentation/need_action/veille_signaux_prompt_a_copier.md` — livraison
  (fichier `veille_signaux_reponse_<ia>.md`, ligne `ia: <nom>`, `### FIN`), définition,
  **règles de couverture** (pour 10 : au plus 2 par variable principale, au moins
  8 variables, au plus 3 dont le moteur est le numérique ; variable principale = domaine
  transformé), sources à élargir, 12 variables et sous-variables, « déjà connu » (état
  du monde, signaux injectés, 150 titres de candidats précédents), notes 1-5
  (pertinence, nouveauté, impact), bloc `### SOURCES CONSULTÉES`.
- **`veille_livres_api.py`** (+ `livres_veille.py`) : tout PDF (avec texte), EPUB,
  `.txt` ou `.md` déposé dans `documentation/livres/` est lu (« dépose et oublie » ;
  `pip3 install pypdf`). 1) repérage des pages utiles (un petit appel, mémorisé) ;
  2) lecture des pages non lues (30 000 caractères par livre, 0 à 3 signaux, source
  `livre: <titre>, p. N — « citation exacte »` ; consigne : une recommandation
  de l'auteur n'est pas une observation, un grand programme d'État n'est pas
  marginal) ; 3) signal rejeté si la page n'a pas
  été envoyée ou si la citation n'y est pas ; 4) écriture ajoutée dans
  `veille_signaux_reponse_livres.md` ; 5) mémoire `state/livres_veille.json`.
  Exceptions YAML : `actif: false`, `titre`/`auteur`/`annee`, `pages: "45-80"` ou
  `chapitres: "3-5"`, `max_caracteres`, `note`.
  ```bash
  python3 generator/veille_livres_api.py [--dry-run | --lister-livres | --livre "weak" | --relire-livres | --refaire-reperage]
  ```
  Bons résultats sur les catalogues de signaux (JRC) ; les synthèses de tendances
  donnent surtout du connu. PDF scanné : détecté, pas lu (pas d'OCR). Un signal tiré
  d'un livre reçoit « 📖 état actuel non vérifié ».
- **`verifier_flux_rss.py`** (sans IA, `pip3 install feedparser`) : trouve le flux de
  chaque source (champ `rss`, autodécouverte, adresses courantes) ; retenu seulement
  si son dernier article a moins de 180 jours (`--max-jours`). `--source X`,
  `--apply` (écrit seulement les `rss:` vides, `.bak`). À relancer de temps en temps.
  Hacker News a été retiré volontairement (`rss: null`) : ne pas accepter son flux.
- **`veille_rss_api.py`** : articles des 30 derniers jours (`--jours`) pas encore lus
  (résumé du flux, ~1 200 caractères), lots de 40 (`--taille-lot`), 0 à 3 signaux par
  lot ; chaque signal cite `[A12]` + une citation exacte, rejeté sinon ; écriture dans
  `veille_signaux_reponse_rss.md` ; mémoire `state/rss_veille.json` (120 jours).
  ```bash
  python3 generator/veille_rss_api.py [--lister | --dry-run | --source grist --jours 60 | --relire]
  ```
- **`import_signaux_faibles.py`** : lit tous les `.md` de
  `documentation/need_action/veille_signaux_reponses/`, fusionne, compare aux veilles
  précédentes, écrit un lot dans `state/veille_signaux.json` et le rapport
  `veille_signaux_fusion.md`, archive les réponses.
  ```bash
  python3 generator/import_signaux_faibles.py --dry-run --verifier-sources   # aperçu (défaut GUI)
  python3 generator/import_signaux_faibles.py --verifier-sources [--force] [--seuil-titre 0.6]
  ```
  Provenance par `ia:` (fichiers renommés `veille_signaux_reponse_<ia>.md`, `<ia>_2`
  pour une deuxième réponse) ; parsing tolérant ; fusion entre IA (URL significative
  commune ou titres proches, ⭐ « convergent ») ; `--verifier-sources` : ✅ / ❌ / ❔ ;
  candidat sans source valable → « écarté » (récupérable, réhabilité s'il revient
  sourcé) ; candidat déjà à trier → fusionné ; déjà écarté ou en file → ignoré ;
  🔁 s'il ressemble à un signal déjà injecté.
- **Onglet « 🔭 Veille signaux faibles »** (`gui/routes_veille_signaux.py`) : filtres
  lot, statut (`a_trier`, `ecarte`, `en_queue`, `en_hypothese`), variable, IA, recherche ; actions
  **Écarter**, **Remettre à trier** (depuis `en_queue` : retirer l'entrée de la file à
  la main), **✨ Envoyer vers « et si ? »** (depuis le 7 nov 2026) : crée une hypothèse (type signal
  ou événement) dans `et_si/hypotheses.yaml` ; le candidat passe au statut `en_hypothese`
  (« ✓ Envoyé vers « et si ? » … ») ; suite dans l'onglet « Et si ? » (simuler → décider →
  injecter). L'ancien bouton « Préparer l'entrée de queue » est remplacé (code conservé
  jusqu'à l'étape 5). Statuts : `a_trier`, `ecarte`, `en_queue`, `en_hypothese`.

**Routine** : 1. préparer le prompt (Aperçu décoché) → 📋 Copier → coller dans 2-3 IA
→ déposer chaque réponse ; 2. livres si nouveaux ; 3. flux RSS (Lister d'abord) ;
4. importer (aperçu puis réel) ; 5. trier dans 🔭, puis injecter. Les candidats non
triés s'additionnent d'une veille à l'autre, sans doublon. Constat : Claude livre des
signaux sourcés ; Mistral omet souvent les sources ; Gemini a inventé des URL.

**Limites** : pas de bouton pour défaire une fusion ; si l'IA découpe un candidat en
plusieurs idées à « Préparer l'entrée », seule la première ajoutée compte ; 15 sources
sur 31 ont un flux ; résumés RSS parfois très courts (articles réservés aux abonnés).

---

## 3quinquies. Simulateur « et si ? » et parcours d'une hypothèse

Tester l'effet d'un élément perturbateur (événement, bascule) sur le lore **avant**
de l'injecter, puis l'injecter et appliquer ses conséquences au vault. Tout se fait
dans le GUI : **Entités & événements — Création → « 🔮 Simulateur « et si ? » »**,
panneau **🧭 Parcours de l'hypothèse**.

**Les cinq étapes** : ① **Tester** (simulation, lecture IA, carte, passe exhaustive)
→ ② **Décider** (adopter ou rejeter) → ③ **Injecter** l'événement tel qu'il a été
simulé → ④ **Appliquer** les conséquences (zones, trajectoires, relations, carte) →
⑤ **À la main**, outillé (carte, fiches disparues, entités, phrases, articles, règle
de lore, contrôles de fin).

Hypothèses appliquées de bout en bout : `destruction_geneve_2076` (breakdown, à la
main), `explosion_brise_glace_murmansk_2081` (reference, choc),
`effondrement_circulation_atlantique_2067` (reference, rupture), `pacte_tabriz_2058`
(breakdown, carte : l'Iran passe à l'Arc Eurasien Central). **Exemples à ne jamais
adopter** : `occupation_bresil_2029` (nouvelle zone + sous-zones),
`reunification_ecosse_2070` (absorber + zone vidée).

### Marche à suivre
1. **Écrire l'hypothèse** (onglet « Nouvelle hypothèse », ou à la main dans
   `et_si/hypotheses.yaml`). Si un territoire **change de mains** (conquête,
   sécession, annexion), remplir le bloc `geographie:` ; sinon `carte: non`. Choisir
   **choc** (l'effet s'estompe) ou **rupture** (le monde change pour de bon).
   Limiter `scenarios` à ceux où l'hypothèse a un sens (zones propres à un scénario).
2. **① Simuler** d'abord sans IA (gratuit : niveaux, carte, liste d'application), puis
   avec « Lecture IA » et « Passe exhaustive » (≈ 0,10-0,15 $ par scénario). Lire le
   rapport (lien Obsidian), surtout la carte et les **obligatoires**.
3. **② Adopter** (portée, intensité ; Aperçu d'abord) ou Rejeter.
4. **③ Injecter** : « Liste de l'étape ④ » (sans IA) → mettre dans **Sauter** les
   propositions à écarter (et dans **Inclure** les ⚠ à garder) → **relancer « Liste »
   avec les champs remplis** pour contrôler (✓ / –, numéros absents, ce qui sera
   retiré de l'entrée) → « Simuler l'injection » si besoin → « Injecter ». Les
   numéros sont ceux de l'étape ④, **pas** ceux de la liste d'application du rapport
   ① (numérotée autrement). Les propositions écartées ne sont pas
   données comme faits à l'IA de l'injection.
5. **Commit git**, puis **④** Aperçu (le champ Sauter reprend les choix de l'étape
   ③) → Appliquer.
6. **⑤** : rubriques dans l'ordre ; commit à la fin.

### Panneau « 🧭 Parcours de l'hypothèse »
Agit sur l'hypothèse choisie dans la liste. Statut et frise des cinq étapes (vert =
fait, bleu = en cours, gris = à venir) ; une carte par étape avec son aide « ⓘ » ;
« ⛶ Agrandir » (Échap) ; poignée violette entre formulaire et sortie (largeur
mémorisée, double-clic : 340 px). Pendant un appel : « ⏳ … en cours, N s — ne pas
recliquer » ; résultat en bas du panneau, indications de terminal traduites en noms
de boutons. Routes `/api/et_si/statut`, `/decider/…`, `/injecter/…`, `/appliquer/…`,
`/main/…`. `et_si_statut.py --id <id> [--json]` donne l'étape en cours.

- **① Tester** — formulaire du simulateur (onglet **Simuler une hypothèse**) :
  Scénario (vide = tous ceux de l'hypothèse ; à choisir **avant** l'hypothèse),
  Hypothèse (« nom (date) · statut », « ⚠ invalide » si mal remplie), Effet mesuré en
  (2098), **Lecture IA** (≈ 1-2 centimes par scénario, cache), **Passe exhaustive**
  (≈ 0,05-0,11 $ par scénario, à cocher avec la lecture IA), **Nouveau tirage**
  (`--refaire`, relance aussi la passe), Récit IA (avancé). Fichiers :
  `et_si/hypotheses.yaml ↗` (VS Code), « Rapport du dernier lancement ↗ » (Obsidian).
- **② Décider** — Portée, Intensité, Aperçu de l'adoption, Adopter, Rejeter (motif),
  Annuler la décision, Voir les dossiers.
- **③ Injecter** — « Liste de l'étape ④ » (tient compte des champs, sans IA), champs
  **Sauter** / **Inclure (⚠)**,
  « Simuler l'injection » (appels IA réels, rien écrit), « Injecter » (une à
  plusieurs minutes ; cette hypothèse seulement, son entrée quitte ensuite la file).
- **④ Appliquer** — champs Sauter / Inclure, « Aperçu de l'application »,
  « Appliquer », « Générer la check-list », lien vers la check-list.
- **⑤ À la main** — rubriques ci-dessous.

### Types d'hypothèse, entrées et réglages (unification, nov. 2026)
« Et si ? » est la **porte unique** : veille 🔭, Articles et idées y arrivent comme
hypothèses (chantier en cours, voir le backlog B9).
- **Type** : `evenement` (défaut) ou `signal`. Signal : force ≤ 10, les 6 scénarios, une
  force par variable, polarité ±1 par scénario, durée entière ≥ 1, date entière entre
  l'année en cours et 2097 ; ni mode rupture, ni carte, ni portée / intensité. À
  l'étape ③ une hypothèse signal écrit une entrée dans `signaux_custom/queue.yaml`
  (champs `impacts_imposes`, `date_imposee`, `via_matrice_impose`, `contraintes`,
  `zone_hint`) au lieu de la file des événements.
- **Nouveaux champs** : `lieu` (signal seulement, devient `zone_hint` ; ignoré avec un
  avertissement pour un événement) et `contraintes` (maintenant transmises aussi à l'IA
  du signal). Anciens champs du formulaire signal : Thèmes à privilégier = variables des
  impacts ; Nombre de thèmes max = nombre d'impacts ; Persistance = `persistance:` ; Année
  d'apparition = `date:`. L'IA ne peut plus ajouter de variables en plus.
- **Plage de dates** : **événement** : année + mois (`2098.03`), de 2026 à **2098.12** ; la
  fiche garde `date_label` (« 8 mars 2098 »). **Signal** : année entière, de l'année en
  cours à 2097. `duree` = années de montée jusqu'à pleine force ; l'effet est mesuré en
  2098. Une date de mesure antérieure à l'apparition **dans la même année** est ramenée à
  année + 0,12 (message sur la sortie d'erreur).
- **Depuis la veille ou un article** : bouton « ✨ Envoyer vers « et si ? » ». Pour un
  **signal** venant d'un article, la ligne de réglages impose la date (entière, bornée
  2026-2097) ; pour un **événement**, voir « Articles → « et si ? » » ci-dessous. Les
  cases « valable pour les 6 scénarios » (sinon le scénario de l'article seul), « mode
  rupture » (sinon choc) et « effet établi en 2098 » (durées = max(1, 2098 − date)) sont
  **forcées après la réponse de l'IA** (avertissements affichés). CLI :
  `hypothese_depuis_texte.py --proposer --date 2098.03 --scenarios … --mode … --effet-plein
  --citation="…"` (l'idée est lue sur l'entrée standard).
- **Pour un signal** : les options payantes de l'étape ① (Lecture IA, Passe exhaustive,
  Nouveau tirage) sont inutiles ; le titre « Faits imposés à la lecture IA » du rapport est
  trompeur (à corriger).
- ⚠ L'IA peut paraphraser les chiffres des `contraintes` : relire le signal injecté.
- Accès directs encore ouverts jusqu'à l'étape 5 : ancien formulaire Promouvoir, écran
  Édition « Injecter un événement depuis un article », anciens menus d'injection.

### Articles → « et si ? » : un événement tiré de l'article (11 nov. 2026)
Règle : l'événement injecté doit être **dans le texte de l'article** et **ne peut pas être
postérieur à sa date** (sinon on place à volonté l'événement que raconte l'article).
1. Onglet Articles : choisir l'article, section « → Envoyer vers « et si ? » », type
   événement. Cliquer sur **« 🔎 Détecter les événements de l'article »** : un appel IA lit
   le texte complet (`extraire_evenements_article.py`, ≤ 8 événements). Chaque événement
   affiche sa date (« déduite » si l'article ne la donne pas ou la donne en relatif :
   « janvier dernier »), sa nature (« événement de l'article » ou « événement passé
   mentionné »), sa **citation exacte** (sans astérisques ni guillemets doublés, U3q) et
   des badges : « ⚠ déjà connu » (présent dans `event_instances`, `hypotheses.yaml` ou cité
   par l'article), « ⚠ citation introuvable » (le texte n'a pas été retrouvé mot pour mot :
   l'IA a souvent changé un mot, ne pas l'envoyer sans vérifier).
   **Filtre mécanique** (U3p, U3r, U3x) : sont écartés, avec un avertissement
   « écarté (…) : <motif> » en tête de liste, les candidats dont la description cite une
   année postérieure à l'article, contient un marqueur de projet (« en préparation »,
   « devrait », « envisage », « d'ici 20… », « à l'horizon », « sera lancé »…), **commence**
   par « Plan », « Programme », « Projet », « Stratégie », « Débat », « Réforme »… sans verbe
   d'accomplissement (adopté, lancé, voté, signé…), dont la citation est tronquée (« [...] »,
   « … ») ou qui sont une statistique de tendance (évolution chiffrée + durée : « a chuté de
   45 % en une décennie »). Le libellé dit toujours « plan / projet / débat », même pour
   une statistique ou une citation tronquée : seul le motif compte. Les réponses de l'IA
   varient : relancer la détection peut faire revenir un événement écarté (par exemple
   avec une citation entière cette fois).
2. Choisir l'événement (bouton radio). Année et mois se **verrouillent** sur lui ; case
   « forcer la date » pour les déverrouiller (la date reste bornée par l'article).
   Un événement « déjà connu » **bloque** « Proposer » tant que la case « créer quand même
   un doublon (effets cumulés) » n'est pas cochée.
3. **Proposer** (un appel IA, rien d'écrit) : le bloc YAML a la citation exacte de
   l'article en **première contrainte** (donc fait imposé : transmise à l'IA d'injection et
   contrôlée sur le récit), avertissement « citation de l'article ajoutée aux faits
   imposés ». 4 contraintes au maximum (celles de l'IA sont retirées au besoin).
4. **Vérifier**, **Ajouter à hypotheses.yaml**, puis le parcours ①→③ (simuler, décider,
   adopter, injecter). Le scénario est imposé par l'article. **Lecture IA inutile** pour
   un simple événement d'article : elle ne sert qu'à l'étape ④ (fiches d'entités touchées).
   Sélectionner du texte à la souris dans le panneau est sans danger depuis U3j.
5. **À l'injection (étape ③)**, `inject_custom_events.py` retrouve la citation (≥ 8 mots)
   dans `articles/<scénario>/*.md` (un seul article doit la contenir) et donne à l'IA le
   **passage de l'article** : paragraphe de la citation, précédent et suivant, 2 800
   caractères au plus (U3s ; terminal de Flask : ligne `[contexte article] <fichier>
   (paragraphe n/N)`). Consignes ajoutées quand ce passage est fourni : description
   sobre sur l'événement choisi seul, à sa date (U3t, U3y) ; ni scène, ni dialogue, ni
   paroles prêtées à un personnage hors passage, ni date plus précise, ni chiffre, lieu,
   acteur ou sigle absent du passage ; jamais le nom d'un scénario dans la description ou
   les conséquences ; conséquences limitées à des tensions ou tendances déductibles, sans
   débat ni réaction d'autorité (U3w) ; aucun fait postérieur à l'événement ni
   « aujourd'hui » (U3y). Contrôles :
   - **faits imposés** (appel IA déjà existant) : la citation de l'article est marquée
     `[ARTICLE]` ; son omission (qui, quoi, quand, issue) compte comme « non respecté » et
     déclenche une réécriture (U3w) ;
   - **mécaniques, sans IA, non bloquants** (lignes ⚠ de la sortie) : citation « … » de
     la fiche absente de l'article (U3t) ; nom de scénario dans la description ou les
     conséquences (U3w) ; année postérieure à l'événement ou « aujourd'hui » dans la
     réalisation ou la description (U3y).
6. **Relire la fiche injectée** (`event_instances/<id>_<scénario>.md`) et la comparer à
   l'article, **toujours**. Défauts vus le 11 nov malgré les contrôles : quand l'article ne
   donne qu'une mention, l'IA remplit les champs (3 à 5 lignes exigées) avec des détails
   inventés (sigle mal développé, travaux, migrations) ; une scène de 2098 transposée à la
   date de l'événement sans citer d'année (non détectée) ; omission d'une issue (libération
   après pétition). Vérifier aussi `localisation` : `extract_localisation.py`
   (mistral-small) a placé un quartier de Genève en `afrique_continentale` à cause de
   « communautés sahéliennes ». Corriger à la main (patch ponctuel ou éditeur), puis
   `validate.py`. Pour vérifier qu'un détail vient de l'article :
   `grep -o -i -E "terme1|terme2" articles/<scénario>/<fichier>.md` (attention aux pluriels).
Limites connues : un événement de mars 2098 pèse très peu sur les chiffres de 2098 (le
moteur travaille en années) ; l'étape ④ n'a rien à appliquer sans Lecture IA / Passe
exhaustive lancées à l'étape ① (« Appliquer » écrit alors 0 fichier) ; l'étape ⑤
n'apparaît plus dans l'interface. La note de cohérence d'une fiche injectée est écrite en
texte brut dans le corps depuis U3l (avant, version YAML avec guillemets).

### Onglet « Nouvelle hypothèse » — `hypothese_depuis_texte.py` 🔁 🧩
On écrit l'idée librement ; **✨ Proposer** (un appel IA) remplit un bloc YAML
complet (2 à 8 impacts, contraintes fidèles à l'idée, jamais de géographie) avec ⚠
et justification ; **Vérifier** (sans IA) ; **Ajouter à hypotheses.yaml** (seul
chemin d'écriture, `.bak_ajout`, commentaires conservés). Refus : id pris, même nom ou
même description qu'une hypothèse existante.
```bash
echo "idée…" | python3 generator/hypothese_depuis_texte.py --proposer     # n'écrit rien
python3 generator/hypothese_depuis_texte.py --verifier < bloc.yaml
python3 generator/hypothese_depuis_texte.py --ajouter --json < bloc.yaml
```
⚠ Relire le bloc proposé : l'IA met souvent `scenarios: tous`, applique le même
partage de polarités (3 mondes « durs » contre 3 « doux »), choisit `rupture` pour un
événement régional, et laisse le changement de carte dans la description au lieu du
bloc `geographie` (sans ce bloc, rien ne bouge sur la carte).

### `et_si/hypotheses.yaml`
Champs : `id`, `nom`, `description`, `date` (2025-2098), `mode` (`choc` |
`rupture`), `persistance` (mode choc), `via_matrice`, `scenarios` (liste ou `tous`),
`carte` (`non` = sans effet territorial), `impacts` (par variable : `delta_level` =
force, `polarite` 1 / −1 — nombre ou dictionnaire par scénario —, `duree` de
montée), `contraintes` (faits imposés à la lecture IA et à l'injection),
`geographie` (par scénario) :
```yaml
geographie:
  breakdown:
    - pays: Iran
      action: absorber            # absorber | nouvelle_zone | partition | region
      zone: arc_eurasien_central
```
- `absorber` : le pays rejoint une zone existante ; `nouvelle_zone` : zone N1 créée
  avec le pays ; `partition` : le pays coupé en parties (`parties`, chacune avec
  `portion` ; `partie_principale` = modèle Allemagne : cette partie garde le pays
  entier) ; `region` : une partie prend une existence propre **sans changer de
  mains** (sous-zone sous `parent`).
- Pour trouver un pays dont le changement exerce sous-zones et zone vidée :
  `python3 generator/scan_candidats_carte.py [--top 15]` (lecture seule ; drapeaux
  S = sous-zones d'un seul pays, M = sous-zone à plusieurs pays, V = zone vidée,
  J = zone à journaux).

### `simuler_et_si.py` 🔁 🧩
```bash
python3 generator/simuler_et_si.py --lister [--json]
python3 generator/simuler_et_si.py --id <id> --report                         # niveaux + carte
python3 generator/simuler_et_si.py --id <id> --consequences-ia --passe-exhaustive --report
# options : --scenario X | --date 2070 | --recit-ia | --json | --refaire
python3 generator/simuler_et_si.py --dossiers
python3 generator/simuler_et_si.py --adopter <id> --portee regionale --intensite forte [--apercu]
python3 generator/simuler_et_si.py --rejeter <id> --motif "…"
python3 generator/simuler_et_si.py --annuler-decision <id>
```
Lecture seule, sauf : rapport `documentation/need_action/et_si_<id>.md` (copie
`et_si_dernier_lancement.md`), états `generator/state/dernier_et_si.json`,
`et_si_consequences.json` (cache IA), `et_si_exhaustif.json` (cache de la passe),
`et_si_dossiers.json`, opérations `generator/state/et_si_application/<id>.json`, et
rapports d'impact de la Carte (`need_action/impact_bascule_*.md`).

**A — Niveaux** : `dynamique.simuler()` avec et sans l'hypothèse, toutes les
injections existantes en place (même contrefactuel que le Tracer) : écarts, pics,
variables entraînées par la matrice, tensions apparues / disparues.
- **Choc** : perturbation amortie, retour vers l'équilibre ; quelques points d'écart.
- **Rupture** : la **référence** des variables touchées glisse de force × polarité
  sur `duree` puis y reste (« référence 75,0 → 94,0 ») ; vaut pour toute l'hypothèse
  (un impact passager se règle par une force plus faible) ; `persistance` ignorée.
- Près des bornes (breakdown, fortress_world), même une rupture bouge peu.

**B — Lecture IA** (`--consequences-ia`, un appel `structured_strict` par scénario) :
lecture et ampleur, trajectoires (8 au plus), relations (6), statuts de zone (4),
carte (4), nouvelles entités (3, avec catégorie). **Contrôle mécanique**, chaque
proposition écartée étant listée : slug inconnu, valeur invalide, aucun changement,
recul de phase, relation déjà présente ou absente, carte d'un scénario déjà fixée par
l'hypothèse, partition sans changement de mains, `carte: non` (aucune carte ni zone
`disparu`). Corrections automatiques listées (action de relation, suffixe de slug,
entité qui nomme un pays rattachée à sa zone d'arrivée). Cache revérifié à chaque
lecture ; `--refaire` = nouveau tirage (la lecture varie d'un tirage à l'autre).

**C — Carte** (aperçu) : pour chaque changement, `ZoneRepository.impact_bascule_pays()`
— zone quittée (vidée ? journaux ?), sous-zones qui deviendraient orphelines,
instances du pays, fiches qui le citent ; partition (portions, tracés,
`zones_pays.json`) ; région (`creer_sous_zone(dry_run=True)`).

**Liste d'application** (fin de chaque scénario du rapport, à cocher) : carte,
localisation des fiches, journaux, statuts de zone, élément (vérifier que la fiche
porte les forces simulées), nouvelles entités (YAML), trajectoires, relations, lore,
**fiches à relire** (recherche par mots : pays, capitales et villes de plus d'un
million, sous-zones, noms propres de l'hypothèse ; avec la passe, seulement zones et
registre), possibles prioritaires, articles et site, contrôles. Puis **« injection
commune »** : l'entrée pour `evenements_custom/queue.yaml` avec `impacts_imposes`,
`date_imposee`, `via_matrice_impose`, `mode_impose`, `acteurs_hint` (4 au plus par
scénario) et `faits_imposes` (contraintes, sort des acteurs, statuts de zone).
⚠ Cette entrée est tirée de **toute** la lecture IA : écarter à l'étape ③ ce qu'on ne
veut pas.

### Passe exhaustive — `et_si_exhaustif.py` 🔁 (v9.6)
Relit **toutes** les instances du scénario et les événements datés après l'hypothèse,
par lots de 15 (`structured_strict`), avec la lecture IA comme contexte (une lecture
nouvelle relance toute la passe et peut changer le résultat).
```bash
python3 generator/et_si_exhaustif.py --id <id> --scenario <sc> --estimer     # coût, aucun appel
python3 generator/et_si_exhaustif.py --id <id> --scenario <sc> > documentation/need_action/passe_<id>.md
# options : --refaire | --taille-lot 15 | --sans-contre-lecture | --sans-classement | --json | --date 2098
```
- **Obligatoire** : la fiche devient **fausse** sans ce changement (trajectoire : seule
  une disparition ; relations ; textes avec extrait mot pour mot et fait contredit).
- **Possible** : conséquence plausible ; 20 prioritaires choisis par l'IA, puis les
  autres sur une ligne. Les possibles ne sont jamais appliqués.
- **Contrôles mécaniques** (rétrogradent d'obligatoire à possible, motif affiché) :
  sans lien direct, conditionnel, lien variable sous 2 points ou seulement propagé,
  lien territoire sans territoire touché (sauf lieu nommé), texte qui élargit ou
  atténue sans contredire, extrait introuvable, **citation inexacte** (31 oct 2026 :
  l'extrait doit se retrouver EN ENTIER dans la fiche — avant, ses 120 premiers
  caractères ; une citation réécrite par l'IA est remplacée par la vraie phrase de la
  fiche, gardée dans `extrait_ia`, et le changement passe en possible), changement
  de degré, et (v9.6)
  **date de la fiche contestée** — la justification ne conteste qu'une année de la
  fiche que l'hypothèse ne fixe pas (« trop tardive », « dès 2043, et non 2044 »),
  sauf fait matériel invoqué (destruction, « n'existe plus »).
- **Contre-lecture** des obligatoires (paquets de 25) : « incompatible ou non ? »,
  pièges nommés (omission, aggravation, nuance, chronologie, passé, amorti…), fait
  classé matériel ou tendance (un choc amorti + tendance est rétrogradé).

### Banc de rejeu (régler la passe sans IA)
- `python3 generator/export_et_si.py --couple id:scénario [...]` écrit
  `generator/state/export_et_si.json` (sans `--couple` : tous les couples du cache).
- `generator/rejeu/` : `rejouer.py` (tout appel IA refusé et compté en « appels
  manquants »), `evaluer.py` (score contre `reference.json`), `LISEZMOI.md`.
- **Cinq couples** : `invasion_bresil_2029:fortress_world`,
  `fusion_commerciale_2038:policy_reform`, `peste_pulmonaire_2043:breakdown`,
  `extreme_droite_2034:new_sustainability`, `ia_majorite_travail_2040:eco_communalism`
  (Genève retirée : hypothèse appliquée). Score attendu : **VERDICTS 23/23,
  priorités 6/6**.
```bash
python3 generator/export_et_si.py --couple invasion_bresil_2029:fortress_world --couple fusion_commerciale_2038:policy_reform --couple peste_pulmonaire_2043:breakdown --couple extreme_droite_2034:new_sustainability --couple ia_majorite_travail_2040:eco_communalism
python3 generator/rejeu/rejouer.py && python3 generator/rejeu/evaluer.py
```
- Après un changement de **code** de la passe : rejouer directement. Après un
  changement de **consigne** (`VERSION_PROMPT`, `VERSION_CONTRE`,
  `VERSION_CLASSEMENT`) : relancer les passes réelles des cinq couples, puis exporter
  et rejouer.
- **Après une modification d'un scénario** (fiche modifiée, événement injecté), ses
  couples sont périmés (« lots en cache 0/N », `RuntimeError`) : relancer sa passe
  réelle (simulateur, sans adopter) et réexporter. Une hypothèse déjà appliquée ne
  peut plus servir de référence.

### Étape ② — dossiers (`et_si_dossiers.py`)
Chaque simulation enregistre le dossier de l'hypothèse (`state/et_si_dossiers.json`).
**Statut** (calculé à chaque lecture) : non simulé · simulé · rejeté · adopté, en
attente d'injection · injecté · injecté partiellement · à revoir · adopté, absent de
la file.
- **Adopter** écrit dans `evenements_custom/queue.yaml` l'entrée de la **dernière
  simulation complète** (`portee` si laissée à choisir, `intensite` toujours ;
  `.bak_et_si`). Refus : jamais simulée, modifiée depuis, simulation partielle, sans
  entrée, déjà adoptée ou injectée.
- **Annuler la décision** : retour à « simulé », retire l'entrée pas encore injectée ;
  ne touche jamais au vault (pour un événement injecté : `undo_custom.py`).

### Étape ③ — `et_si_injecter.py` 🔁 🧩
```bash
python3 generator/et_si_injecter.py --id <id> --plan [--sauter 3,4,9] [--inclure 7]   # liste de l'étape ④, sans IA
python3 generator/et_si_injecter.py --id <id> --sauter 3,4,9 [--inclure 7] --dry-run
python3 generator/et_si_injecter.py --id <id> --sauter 3,4,9 [--inclure 7]
```
- Passe l'entrée de l'hypothèse à `inject_custom_events.py --idea`, puis la retire de
  la file ; refuse une hypothèse qui n'est pas « adopté, en attente d'injection ».
- **`--plan` avec Sauter / Inclure** (1er nov 2026) : chaque ligne marquée ✓ (appliquée)
  ou – (écartée, ⚠ écartés par défaut compris), « ⚠ numéro(s) absent(s) de cette
  liste », et « Retiré de l'entrée à l'injection » (faits imposés, acteurs) si
  l'entrée est dans la file. Le contrôle gratuit à faire avant « Injecter ».
- **Sauter / Inclure** : mêmes numéros qu'à l'étape ④. Les faits imposés et les
  acteurs des opérations écartées (trajectoires, disparitions, zones sautées, et les ⚠
  sauf `--inclure`) sont retirés de l'entrée passée à l'injection. À l'injection
  réelle, les choix sont gardés dans `generator/state/et_si_application/<id>.sauter.json`
  et repris par l'étape ④ quand son champ reste vide.
- Relire l'aperçu de l'injection : si l'IA invente un fait (une date, une
  destruction), l'ajouter comme contrainte à `faits_imposes` de l'entrée avant
  l'injection réelle (le nouveau tirage peut différer).
- Outil manuel équivalent pour une entrée déjà adoptée :
  `python3 generator/et_si_retirer_faits.py --id <id> --slugs a_sc,b_sc [--apply]`.
- L'injection vérifie les faits imposés `contrainte` / `change` / `zone` (une
  réécriture, puis ⚠ dans « Alertes de l'injection », §3).
- La localisation de l'événement est calculée à l'injection, AVANT la carte : une
  zone créée à l'étape ④ n'existe pas encore (l'étape ④ relocalise, voir ci-dessous).

### Étape ④ — `appliquer_et_si.py` 🔁 🧩
```bash
python3 generator/appliquer_et_si.py --id <id>                        # aperçu, rien écrit
python3 generator/appliquer_et_si.py --id <id> --sauter 3,7 --apply
python3 generator/appliquer_et_si.py --id <id> --reste-a-faire        # check-list seule
```
Refus : fichier d'opérations absent (simulation antérieure à v8.19), simulation
partielle, statut autre que « injecté », simulation changée depuis l'adoption ; en mode
rupture, une fiche injectée sans `mode: rupture`.

**Opérations numérotées** (✓ retenue, – sautée, · déjà appliqué) :
- **statut de zone** (contrôle du statut actuel) ;
- **trajectoire** (lecture et passe fusionnées) — ⚠ et sautée si la fiche a changé, si
  lecture et passe divergent, si le saut passe un cran (émergent → dominant), ou si un
  homonyme existe ; « disparu » ⇒ `annee_fin` = année de l'élément ;
- **disparition** — retire l'entité de toutes les relations du scénario et vide les
  siennes ;
- **relation** rompue ou nouvelle — ⚠ si elle contredit une relation inverse ;
- **carte** (`absorber`, `nouvelle_zone`), appliquée par la Carte **après** les autres
  écritures : le pays rejoint la zone et quitte les autres ; les **sous-zones qui ne
  portent que ce pays** le gardent et sont rattachées à la zone cible (leurs entrées
  sont lues par mots : « Île de Kharg, Iran » porte l'Iran) ; type d'origine du
  territoire gardé ; résultat relu, sinon géographie et `zones_pays.json` remis en
  l'état (le reste reste écrit). Partition et région restent à la main (tracés).
  L'aperçu ne liste que les sous-zones rattachées, « (avec leurs sous-zones : …) »
  pour celles qui suivent leur parent. **Relocalisation de l'événement** (31 oct
  2026) : si `localisation.zone` de `event_instances/<id>_<sc>.md` est une zone que
  le pays quitte (ni la cible, ni une sous-zone qui suit, ni une sous-zone à
  répartir), elle est remplacée par la cible après la carte réussie (ligne
  « → événement … relocalisé : A → B » dans l'aperçu ; `.bak_appliquer`). Carte en
  échec : rien n'est relocalisé.
- **Bloc « Réciprocité »** de l'aperçu (31 oct 2026), quand des relations ou
  disparitions sont retenues : estimation de ce que changera
  `fix_alliances_oppositions.py` sur TOUT le scénario (même règle que
  `calculer_reciprocite(ignorer_exclues=True)`) — fiches complétées par réciprocité
  des opérations ; fiches **hors hypothèse** à relation à sens unique déjà dans le
  vault (tri par relation depuis le 1er nov 2026 : une relation déjà présente dans une
  fiche touchée par une opération reste « hors hypothèse » ; une fiche peut figurer
  dans les deux rubriques) ; conflits alliance / opposition (tranchés en opposition). Le script fait foi.

Tri : tout est retenu sauf les ⚠ ; `--sauter` retire, `--inclure` reprend une ⚠ ;
« déjà appliqué » n'est jamais rejoué (relancer n'applique que ce qui manque).

**Avec `--apply`** : écriture de tous les fichiers, ou d'aucun si une opération
échoue (`.bak_appliquer` refaite à chaque écriture) ; puis la carte ; puis
`regenerer_corps_geographie.py --execute` si une zone a changé,
`fix_alliances_oppositions.py --reciprocite-seule --ignorer-exclus --resoudre-conflits
--bascule-en-opposition` si une relation a changé, `validate.py` ; puis, pour chaque
entité qui vient de disparaître, **l'aperçu « au passé » de sa fiche**
(`fiche_au_passe.py`, un appel IA chacune). Journal
`et_si_application/<id>.applique.json` ; check-list
`documentation/need_action/et_si_<id>_reste_a_faire.md`.

### Étape ⑤ — `et_si_main.py` 🔁 🧩
Suivi dans `generator/state/et_si_application/<id>.main.json`. Rien n'est écrit sans
le bouton d'écriture (ou `--apply`). Ne s'ouvre que pour une hypothèse passée par la
phase 4.
```bash
python3 generator/et_si_main.py --id X --json
python3 generator/et_si_main.py --id X --entites '[{"cle": "breakdown:1", "category": "organisation"}]' [--apply]
python3 generator/et_si_main.py --id X --regle breakdown [--apply] <<'EOF'
- id: …
EOF
python3 generator/et_si_main.py --id X --au-passe <slug> [--apply]
python3 generator/et_si_main.py --id X --phrases-proposer [--refaire]
python3 generator/et_si_main.py --id X --phrase CLE [--apply | --ignorer] < phrase.txt
python3 generator/et_si_main.py --id X --articles-verifier [--refaire]
python3 generator/et_si_main.py --id X --article-relu articles/<sc>/<f>.md
python3 generator/et_si_main.py --id X --carte-deplacer sc:<sous_zone> [--apply]
python3 generator/et_si_main.py --id X --carte-laisser sc:<zone>
python3 generator/et_si_main.py --id X --journal-garder sc:<zone>:<orientation>
python3 generator/et_si_main.py --id X --journal-retirer sc:<zone>:<orientation> [--apply]
python3 generator/et_si_main.py --id X --lancer audit|resume|geo --scenario sc
```
⚠ Dans le terminal, un bloc `<<'EOF' … EOF` se colle **en entier** ; s'il reste
ouvert, taper `EOF` seul sur une ligne puis Entrée (le script refuse un texte vide).

Rubriques du panneau, dans l'ordre :
- **🗺️ Carte** — sous-zone à plusieurs pays qui a perdu le pays : « La laisser ainsi »,
  « Aperçu : la déplacer sous <cible> » / « La déplacer » (ses autres pays la suivent),
  « Tracer une portion ↗ » ; zone vidée : « La garder (vestige, exil) » ou « La
  supprimer : onglet Carte ↗ », et ses journaux : « Le garder (en exil) » ou « Le
  retirer » (de `journaux.yaml`, aperçu d'abord) ; nouvelle zone : description et
  relations dans `geographie/<sc>.md`, rédactions (`generate_journaux.py --update`),
  continent (`export_revues.py --continents`).
- **⏳ Fiches des entités disparues (au passé)** — la phase 4 change la trajectoire,
  pas le texte. Pour chaque entité disparue : état (« aperçu pas encore fait »,
  « avant / après prêt », « écrite »), « Ouvrir l'avant / après ↗ » (retouchable dans
  Obsidian), « Écrire dans la fiche », « Mettre au passé / Refaire l'aperçu (IA) »,
  « Ouvrir la fiche ↗ » (voir `fiche_au_passe.py` ci-dessous).
- **🧩 Nouvelles entités** — case + catégorie → `entites_custom/queue.yaml` ; puis
  « Créer des entités » (traite toute la file : vérifier d'abord qu'elle ne contient
  que ces entrées) ; vérifier ensuite la localisation des nouvelles fiches.
- **✏️ Phrases à corriger** — de la passe et de la fiche d'événement (relecture IA en
  cache) ; réécriture modifiable ; Aperçu / Remplacer / Ignorer.
- **📰 Articles à relire** — articles qui citent une entité touchée ou dont la zone a
  changé ; « Relire avec l'IA » relève les passages contredits (aucun article n'est
  modifié). La relecture ne retient que ce qui a été **appliqué** (les propositions
  sautées ne comptent pas), donne les territoires des zones changées, et écarte les
  justifications au conditionnel ou par sous-entendu, celles qui ne parlent que
  d'entités inchangées, et, pour une entité dont le rang monte, un passage sans mot de
  déclin ou de disparition. « Ouvrir dans Obsidian ↗ », « Marquer comme relu ».
- **📜 Règle de lore** — brouillon (une règle par entité disparue ; contraintes en
  commentaires, à transformer au besoin) → aperçu → insertion dans
  `documentation/lore_regles.yaml` (`.bak_et_si`). Sans entité disparue, le brouillon
  ne contient que des commentaires : écrire la règle (ex. `meme_phrase` pour une
  contrainte), sinon l'outil refuse (« aucune règle »).
- **🏁 Pour finir** — Relecture du lore (gratuit), Contrôle de la géographie (un petit
  appel IA), Résumé du scénario (payant) ; site depuis le terminal.

### `fiche_au_passe.py` 🔁 — fiche d'une entité disparue mise au passé
Un appel IA met au passé `role_dans_scenario`, `responsabilites`,
`description_journalistique`, `signes_distinctifs`, `tensions_narratives` (ceux qui
sont remplis), sans fait nouveau sauf la fin elle-même.
```bash
python3 generator/fiche_au_passe.py --slug <slug> [--contexte "explosion du Polaris-7 (2081)"]   # aperçu
python3 generator/fiche_au_passe.py --slug <slug> --apply                                        # écrit
```
- `--contexte` : si le texte désigne une hypothèse de `et_si/hypotheses.yaml` (son id
  ou son nom, suffixe « (année) » ignoré), il est remplacé par nom, date, description
  et contraintes (ligne « [contexte] hypothèse `<id>` : description et N fait(s)
  imposé(s) transmis ») — c'est ce que passent les étapes ④ et ⑤ (1er nov 2026 ;
  avant, l'IA recevait le seul identifiant et inventait la fin). Un texte libre reste
  tel quel.
- « ⚠ années disparues : 2098 » est attendu quand la fiche décrivait 2098 au présent.
- L'aperçu écrit `documentation/need_action/fiche_au_passe_<slug>.md` (avant / après,
  avertissements : longueur, noms propres perdus, années postérieures à la fin) ; les
  textes « Après » se retouchent dans Obsidian.
- `--apply` écrit exactement ces textes (frontmatter et corps), sans nouvel appel ;
  refuse si la fiche a changé depuis l'aperçu ; `.bak_au_passe`.
- Lancé automatiquement par l'étape ④ ; rubrique « ⏳ » de l'étape ⑤ ; case dans la
  check-list.

### Lire un rapport
- La lecture IA est une lecture possible, pas une prévision ; comparer plusieurs
  tirages au besoin. Les propositions de carte de l'IA sont toujours à relire.
- Le récit en tête de scénario (« construit par le script ») ne décrit que la courbe
  chiffrée.
- Passe exhaustive : « Propositions sans objet, écartées » (relation déjà présente,
  relation à rompre absente du vault, trajectoire inchangée) n'est pas un défaut ;
  « Réponses rejetées car mal formées » (entité inconnue, valeur invalide, contresens)
  en est un (1er nov 2026).
- « Fiches à relire » : termes tirés des pays de la carte et des noms propres de
  l'hypothèse ; les mots génériques qui ouvrent les noms (`MOTS_GENERIQUES` de
  `simuler_et_si.py` : Réseau, Conseil, Pacte, Arc…) ne sont pas cherchés.
- Brouillon de règle de lore (⑤) : le brouillon propose le nom complet, le nom court, le sigle et
  le slug de l'entité (B4, nov. 2026) ; vérifier que les termes couvrent les formes employées
  par les articles (« Holdfast », « les Citadelles »), compléter `termes` à la main si besoin.
- **Limites connues** : la lecture varie d'un tirage à l'autre et la passe en dépend ;
  le classement des possibles varie ; le mode rupture vaut pour toute l'hypothèse ;
  près des bornes, même une rupture bouge peu ; un slug mal orthographié par l'IA reste
  écarté ; partition et région restent à la main (tracés) ; villes cherchées limitées
  aux capitales et aux villes de plus d'un million (plus une table pour Écosse, Pays de
  Galles, Irlande du Nord) ; homonymes possibles (Santa Cruz, Sucre, Perth, Medina).

### Essayer une écriture sans la garder
Commit propre, `git checkout -b essai`, ② ③ ④ dans le GUI, contrôles (`git diff`),
puis `git checkout -- .`, suppression des nouveaux fichiers (fiche d'événement,
check-list, journaux d'application : voir `git status`), `git checkout main`,
`git branch -D essai`. Variante employée le 31 oct 2026 (branche `test-s30`, deux
hypothèses à la suite) : `git add -A && git commit -m "… (jetable)"` sur la branche
après chaque hypothèse (diff lisible de la suivante), puis `git checkout main`
(dépôt propre, rien ne reste), `git branch -D essai` une fois les constats notés. Pour **voir** seulement un rapport : simuler sans IA et ne pas
adopter.

### Outils unitaires d'application
Aperçu par défaut, `--apply` pour écrire ; refus si l'état actuel n'est pas celui
annoncé.
- **`fusionner_doublon_instance.py --garder A --retirer B`** : redirige toutes les
  citations de B vers A (instances, événements, archétypes, articles, géographies),
  retire les doublons créés, met B et son archétype dans `_a_supprimer/fusion_<B>_<date>/`
  (`.bak_fusion`) ; ensuite réciprocité et `validate.py`.
- **`changer_statut_zone.py --scenario S --zone Z --avant X --apres Y`** (`.bak_statut`),
  puis `regenerer_corps_geographie.py --scenario S --execute`.
- **`changer_trajectoire.py --changer slug=avant:apres [...] [--annee-fin N]
  [--ecraser-annee-fin]`** (`.bak_traj`).
- **`retirer_relations.py --scenario S --entites a,b [--vider-propres]`** (`.bak_rel`).

---

## 4. Géographie

Chaque `geographie/{scenario}.md` a deux parties : le **frontmatter** (`zones:`),
seule référence lue par la Carte et les scripts, et le **corps** (« ## Vue
d'ensemble », « ## Zones », « ## Notes »), texte pour Obsidian. Index secondaire :
`gui/zones_pays.json` (pays → zone N1 par scénario, et `pays_liste` de référence,
~200 pays). Toute écriture de la Carte passe par `gui/zone_repository.py` (§7), qui
tient fiche, `zones_pays.json` et tracés (`gui/static/geo_overlays/{scenario}.geojson`)
ensemble et régénère le corps.

**Rappels de lecture**
- Une entrée `origine_reelle` = `{entite, type_entite, portion}`. `portion` vide =
  pays entier ; `portion` remplie + tracé dessiné = overlay.
- La carte colore d'abord depuis la fiche, puis se replie sur `zones_pays.json`
  pour un pays absent de toute fiche : une carte juste ne prouve pas qu'une fiche
  est complète (vérifier avec `scan_geographie_complet --run-zones`).
- Un territoire infra-national (Écosse, Galles…) ne peut avoir sa propre couleur que
  par un overlay dessiné : le fond de carte n'a qu'un polygone par pays.
- `type_entite` valides : `pays`, `etat_federe`, `province`, `region_administrative`,
  `autre` (une ville listée elle-même = `autre`).

### `enrich_geographie_recursive.py` 🔁 🧩 — sous-zones
Ajoute des sous-zones (profondeur libre) sous les zones N1, à partir du corpus.
Additif : ne modifie jamais une zone existante. Tier `structured_strict`. Ne garantit
pas de retenir un lieu précis : pour une ville voulue, `promote_ville.py`.
```bash
python3 enrich_geographie_recursive.py --scenario NOM   # ou --all
python3 enrich_geographie_recursive.py --dry-run
```

### `promote_ville.py` 🔁 🧩 — une ville en zone (CLI seulement)
Crée (ou promeut) une ville en zone sur un ou plusieurs scénarios. Confirmations au
clavier (`input()`), donc pas dans le GUI.
- Zone déjà existante → confirmation, rien créé.
- Ville présente seulement en `lieu_emblematique` → **promotion forcée** : un lieu
  emblématique n'est pas un slug valide pour `localisation.zone`.
- Sinon → création après confirmation.
- Parent : zone N1 du pays (`zones_pays.json`), puis arbitrage IA vers une sous-zone
  plus précise si elle existe. Slug toujours imposé, jamais laissé à l'IA.
```bash
python3 promote_ville.py --ville NOM --dry-run
python3 promote_ville.py --ville NOM --pays PAYS [--slug SLUG]
python3 promote_ville.py --ville NOM --pays PAYS --scenarios policy_reform,reference
python3 promote_ville.py --ville NOM --pays PAYS --all [--quiet]
```
Ensuite : `extract_localisation.py --slug` sur les fiches qui citent la ville.

### `extract_localisation.py` 🔁 🧩 — rattacher les fiches à une zone
Remplit `localisation` (zone / lieu / type_lieu) des instances riches et de toutes
les `event_instances`. Trois issues : lieu trouvé, transnational (vide assumé),
ambigu (`statut: review_manuelle`). Tier `volume`.
- Le prompt donne à l'IA les **territoires de chaque zone** ; l'IA renvoie aussi le
  **pays** du lieu, et `controler_pays()` le vérifie mécaniquement : si la zone
  choisie ne porte pas ce pays, la zone est corrigée vers l'unique zone N1 qui le
  porte, sinon la fiche passe en « ambigu » (octobre 2026).
- `--force` retraite les fiches déjà faites (le bloc existant est remplacé, jamais
  dupliqué).
- GUI : le menu `--slug` ne liste que les fiches en attente (`--scan-pending`) ; pour
  retraiter une fiche déjà faite, passer par `--scenario`.
```bash
python3 extract_localisation.py [--dry-run] [--scenario NOM | --slug SLUG] [--force]
python3 extract_localisation.py --report-only
python3 extract_localisation.py --scan-pending [--json]
```

### `review_localisation.py` 🔁 🧩 — fiches ambiguës
Traite les fiches `review_manuelle`. En terminal, mode interactif (`[V]` valider,
`[C]` autre zone, `[0]` vide assumé, `[S]` passer). Depuis le GUI, **`--auto-resolve`
est obligatoire** (coché, non décochable) : le GUI n'a pas de clavier (stdin fermé).
```bash
python3 review_localisation.py [--scenario NOM] [--dry-run]
python3 review_localisation.py --auto-resolve
```

### Outils de réparation ponctuelle 🔁 🗄️ (CLI)
| Script | Usage |
|---|---|
| `regenerate_zones_pays.py [--dry-run]` | Reconstruit `gui/zones_pays.json` depuis les fiches (`.json.bak`). Si des pays « totalement absents » apparaissent alors que les fiches les couvrent. |
| `add_pays_to_zone.py --scenario S --zone Z --pays A B [--dry-run]` | Ajoute des pays à une zone existante (ne crée jamais de zone). `.bak`. |
| `retirer_entree_parasite_zones_pays.py --scenario S --entite "Y" [--execute]` | Retire de `zones_pays.json` une clé qui n'est pas un pays (refuse un vrai pays). |
| `regenerer_corps_geographie.py --scenario S \| --all [--execute]` | Réécrit la section « ## Zones » du corps depuis le frontmatter, sans IA (`.bak_corps`). Automatique après toute écriture de la Carte ; GUI « 📝 Mettre à jour le texte des géographies » pour une modification faite par script ou à la main ; contrôlé par `validate.py` (étape 11, `--fix`). |

### Diagnostics — `scan_geographie_complet.py` 🔁 🗄️
Seul point d'entrée GUI des diagnostics géographie (« Scanner la géographie »,
préréglages Léger / À la carte / Maxi). Lance en sous-processus tout ou partie des
étapes ci-dessous, puis un résumé.

| Étape (`--run-…`) | Script sous-jacent (utilisable seul en CLI) | Contrôle |
|---|---|---|
| `--run-zones` | `check_zones_coherence.py` | YAML valide ; pays absents de toute zone ; pays rattachés seulement à une sous-zone ; chantiers `pays_sans_zone` devenus obsolètes (`--marquer-resolus`, avec `--all` seulement). |
| `--run-type-entite` | `check_type_entite_coherence.py` | Entrées `origine_reelle` sans `type_entite` ; `--apply-type-entite` corrige (`.bak`). |
| `--run-origine-reelle` | `check_origine_reelle_coherence.py` | Pays d'une zone ville/région vs pays de ses ancêtres ; `--resolve-llm` pour résoudre une ville inconnue (cache `cache_ville_pays_llm.json`). |
| `--run-conventions` | `check_conventions_territoires.py` | Un territoire dépendant (Groenland, Écosse, Pays de Galles…) traité de façon cohérente entre scénarios. 3 territoires restent signalés par choix narratif : attendu. |
| `--run-patron-spatial` | `check_patron_spatial_coherence.py` | Zone N1 vs patron spatial du scénario (IA, un appel par scénario, cache `patron_spatial_cache.json`, `--no-cache-patron-spatial`). Résultats un peu variables d'un appel à l'autre sur les cas limites. |
| `--check-overlays` (optionnel) | `gui/check_overlay_portion_coherence.py` | Tracés vs textes `portion` : DÉRIVE, ORPHELIN, DOUBLON INTERNE (pays listé deux fois dans une zone), portion sans overlay (info). |

Aucune étape passée = les 5 standard. `--write-chantiers` écrit les problèmes trouvés
(étapes zones, origine réelle, patron spatial) dans `chantiers_geographie.yaml`.
`--generer-propositions-topdown` enchaîne `generer_zones_topdown.py --review-topdown`
(appels IA, jamais par défaut, n'applique rien).
```bash
python3 scan_geographie_complet.py --all [--write-chantiers]
python3 scan_geographie_complet.py --scenario NOM --run-patron-spatial --no-cache-patron-spatial
python3 scan_geographie_complet.py --all --check-overlays
python3 scan_geographie_complet.py --all --apply-type-entite --resolve-llm --write-chantiers --generer-propositions-topdown
```
Réflexe : `--all --write-chantiers` en fin de session après des bascules sur la Carte.

### Doublons « pays entier » — `gui/diagnostiquer_doublons_pays_entier.py` 🔁 🗄️
Un pays est en doublon s'il est « pays entier » (sans tracé) dans **deux zones N1
distinctes** (une sous-zone qui hérite de sa racine n'est pas un doublon ; un pays
entier ici + overlay ailleurs non plus). Diagnostic seul par défaut.
```bash
python3 diagnostiquer_doublons_pays_entier.py --scenario X [--json]
python3 diagnostiquer_doublons_pays_entier.py --scenario X --nettoyer --pays P --garder SLUG [--execute]
python3 diagnostiquer_doublons_pays_entier.py --scenario X --nettoyer-auto [--execute] [--rapport-portions F.md]
python3 diagnostiquer_doublons_pays_entier.py --scenario X --write-chantiers
```
`--write-chantiers` crée des chantiers `doublon_pays_entier` avec la proposition déjà
calculée et un **`contexte_narratif`** (début de la description de la zone
concurrente) : la plupart des conflits sont des rattachements narratifs voulus
(zones thématiques transversales, Mourmansk « zone de contact »…). Un nom de zone ne
suffit jamais à juger ; les entités non reconnues comme pays et les cas ambigus ne
deviennent jamais des chantiers.

### Restructurer une zone
Pas de script : renommer, déplacer, scinder, créer, supprimer se font dans l'onglet
Carte (§7).

---

## 4bis. Chantiers géographie

Un seul fichier de suivi : `documentation/need_action/chantiers_geographie.yaml`,
lu et écrit par `chantiers.py` (generator) et par l'onglet Chantiers (§7).

- **Statuts** : `a_traiter` (défaut) / `ignore` (choix narratif, ne plus réafficher) /
  `traite`.
- **Types** : `pays_sans_zone`, `zone_suspecte`, `doublon_pays_entier`.
- **Entrée** : `id` (`scenario__cible`), `scenario`, `type`, `cible`, `probleme`,
  `source_diagnostic`, `date_detection`, `statut`, `proposition` (zone complète, ou
  `{slug_a_conserver, zones_a_retirer}` pour un doublon), `proposition_approuvee`,
  `date_proposition`, `date_traitement` (+ champs libres).
- **Fichier corrompu** : `charger_chantiers()` lève `ChantiersCorrompuError` plutôt
  que de repartir d'une liste vide ; réparer le YAML à la main avant toute écriture.

**Cycle** : diagnostic (`--write-chantiers`) → proposition IA → relecture →
approbation → application → `traite`.

### `zoning_topdown.py` 🔁 🧩 — génère une zone
`generer_zone_topdown()` : zone N1 complète (`pays_sans_zone`) ou révision de
`description`/`type`/`statut`/`tensions_internes`/`relations` (`zone_suspecte`) ;
slug et `origine_reelle` imposés, jamais laissés à l'IA. N'écrit rien. En CLI :
mode lisible (entrée GUI `zoning_topdown_test`) ou `--json` (appelé par la Carte et
l'onglet Chantiers).
```bash
python3 zoning_topdown.py --scenario NOM --pays Andorre [--json]
python3 zoning_topdown.py --scenario NOM --zone-suspecte SLUG --raison-suspicion "texte"
```

### `generer_zones_topdown.py` 🔁 🧩 — propositions et application en lot
- `--review-topdown` : une proposition par chantier `a_traiter` (`--source
  pays_sans_zone|zones_suspectes|both`) ; ne remplace pas une proposition non
  approuvée sans `--force`.
- `--apply-topdown` : applique les chantiers approuvés (`--cible` = un seul, avec
  `--scenario`). Pour `pays_sans_zone` : zone complète + `zones_pays.json` + sous-zones
  orphelines reparentées ; pour `zone_suspecte` : seulement les 5 champs révisables.
- ⚠ **Proposition ancienne** : elle écrase les 5 champs avec leur version de l'époque
  et peut citer des zones disparues. Toujours la comparer à la fiche actuelle avant
  d'approuver.
- `doublon_pays_entier` n'est pas traité ici (application directe par le GUI).
```bash
python3 generer_zones_topdown.py --review-topdown --scenario NOM [--source …] [--force]
python3 generer_zones_topdown.py --review-topdown --all
python3 generer_zones_topdown.py --apply-topdown --scenario NOM [--cible SLUG]
python3 generer_zones_topdown.py --apply-topdown --all
```
Approbation : bouton « Approuver » de l'onglet Chantiers (ou `proposition_approuvee:
true` à la main).

### `reparenter_sous_zones_orphelines.py` 🔁 🧩
Rattache à la bonne zone N1 les sous-zones dont le pays a changé de zone. Appelé
automatiquement par `--apply-topdown` et après un déplacement sur la Carte ;
utilisable seul. `--scan-candidates` (lecture seule, sans IA) liste les zones N1 qui
ont des orphelines (menu `--zone-cible` du GUI).
```bash
python3 reparenter_sous_zones_orphelines.py --scenario NOM --zone-cible SLUG [--json]
python3 reparenter_sous_zones_orphelines.py --scenario NOM --scan-candidates [--json]
```
Une sous-zone transnationale (pays de deux zones N1) reste « orpheline » d'un côté
quel que soit le choix : comparer ses pays à ceux de la cible et du parent ; si les
deux se recoupent, c'est structurel (cas laissé tel quel : Réseau Terrafond des
Bassins, eco_communalism). Dépend de `gui/zones_pays.json` pour résoudre les entités
composées.

---

## 5. Validation

### `validate.py` 🔁 🧩 — à lancer avant toute génération et après toute écriture
12 étapes : nomenclature ; cohérence systémique (niveaux, états, trajectoires) ;
entités / instances ; thématiques ; wikilinks cassés ; matrice d'influence ;
événements ; localisation ; **signaux faibles** (section 7 ↔ section 12 des fiches
variables et `variables_cibles` des signaux custom ; le socle de juin 2026 est
ignoré) ; **cohérence narrative** (acteurs actifs, delta dans [-20, 130], dates
d'instances) ; **texte des géographies** (11, corrigé par `--fix`) ; **journaux ↔
géographies** (12, §2nonies). Contrôles d'impact : `abs(delta_level) × polarite`
(§3ter).
```bash
python3 validate.py                  # complet
python3 validate.py -v               # détail (--verbose)
python3 validate.py -r               # écrit validation_report.md (--report)
python3 validate.py --localisation   # section localisation seule
python3 validate.py -n               # force le scan narratif (--narrative)
python3 validate.py --fix            # réécrit le texte des géographies en retard
```
Le scan narratif ne tourne que si `event_instances/` a changé depuis
`state/last_validated.json` (`-n` pour forcer) ; rapport :
`documentation/need_action/narrative_issues.yaml`.

### Audits (section GUI Validation, lecture seule, sans IA)
| Script | Ce qu'il mesure |
|---|---|
| `audit_longueur_articles.py` | Longueur réelle des articles vs leur `format`. Cas A (format et plage cohérents) = vrai signal qualité ; cas B = override probable. Scan récursif de `articles/`, ignore `_index.md`. |
| `audit_instances_manquantes.py` | `scenarios_instances` d'une entité vs fichiers `instances/{slug}_{scenario}.md` présents. Trois catégories (faux positif de slug / entité suspecte / échec ponctuel) avec la solution conseillée. `--report` écrit `need_action/instances_manquantes.md`, `--json`, `--seuil-absolu 3 --seuil-suspect 0.5`. |
| `audit_etat_temporel_fin.py` | Fiches à trajectoire inactive sans `annee_fin` (§3bis). |
| `audit_dates_instances.py`, `audit_type_relation_dominante.py` | Dates d'instances ; type de relation dominant. |

```bash
python3 audit_instances_manquantes.py --vault-root .. [--report | --json]
```

---

## 6. Scripts one-shot et legacy

Règle : un script 🪦 n'a pas d'entrée dans le panneau GUI ; il reste lançable en
terminal pour le cas précis indiqué.

**À relancer seulement si le symptôme réapparaît**
| Script | Quand |
|---|---|
| `fix_annee_debut_placeholder.py` | Fiches enrichies restées à `annee_debut: 2026` (ancrage registre + état du monde réel ; marqueur `annee_debut_verifiee`). |
| `fix_annee_fin_manquant.py` | Fiches à trajectoire inactive sans `annee_fin` (jalon du registre, sinon contexte ; plafonné à 2098). |
| `fix_lieux_residuels.py` | Un même lieu emblématique dupliqué sur plusieurs zones. |
| `fix_lieux_emblematiques_format.py` | Entrées `lieux_emblematiques` en simple chaîne au lieu de `{nom, type, notes}` (fait crasher l'enrichissement des sous-zones). |
| `fix_alliance_suffixes.py` | Suffixe `_{scenario}` manquant dans `alliances`/`oppositions` (sans IA). |
| `reevaluer_polarites.py [--appliquer]` | Anciennes fiches à impacts non réévalués (cache `state/reevaluation_polarites.json`). |
| `synchroniser_scenarios.py` | Resynchroniser `variable_states` et tableau 4A des fiches scénarios sur les fiches variables (sans risque). |
| `rebuild_processed.py` | Événements custom injectés à la main absents de `processed.yaml`. |
| `build_geographie_monde.py [--scenario \| --all] [--dry-run] [--force]` | Reconstruire la bible plate d'un scénario (`--force` écrase tout). |
| `merge_pays_monde.py` (gui/) | Ajouter des pays à `pays_liste` de `zones_pays.json`. |
| `generate_manual.py` | Prompt du prochain article d'une série à copier dans un chat externe (suivi `state/manual_progress.json`). Pour un simple aperçu : `generate.py --dry-run`. |
| `audit_slugs_s24.py` | Lecture seule : slugs abîmés par l'ancien slugify (ø, æ… → `_`) dans le lore et les zones. Depuis le 31 oct 2026, ne doit plus signaler de CASSÉ, hors `tromsoe_aln` (faux positif connu) ; les lignes « sans lien » sont normales. |

**Faits, ne plus relancer** : `migrate_registre.py`, `migrate_trajectoire.py`,
`migrer_vers_chantiers.py`, `officialize_alliances.py`, `fix_impact_scale.py`,
`migrer_echelles.py`, `polarites_matrice.py`, `audit_polarite.py`,
`extraire_echelles.py`, `fix_doublons_journalistes.py`, `audit_broken_slugs.py`
(slugs cassés, août 2026), `migrer_slugs_s24.py` et `patch_s24_slugs_unifies.py`
(slug commun, 31 oct 2026). Abandonné mais conservé : `detect_evenements_cites_retroactif.py`.

**Remplacés** : `complete_geographie_coverage.py` → `generer_zones_topdown.py` ;
`create_entity.py` et `generate_entities.py` → `create_entities_and_instances.py` ;
les 5 `check_*` géographie restent en CLI mais passent par `scan_geographie_complet`
dans le GUI. Snippets jetables : `check_arctique.py`, `remove_zone_manquante.py`.

**Toujours actifs malgré leur nom** : `generate_instances.py` (instances manquantes
d'entités existantes, distinct de `create_entities_and_instances.py`) ;
`fix_alliances_oppositions.py` (dépendance de production d'`enrich_minimal.py`, §3).

---

## 7. GUI Flask — `gui/app.py`

### Lancement
```bash
lsof -ti:5000 | xargs kill -9        # libérer le port si occupé
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py                        # ou ./start.sh / alias ourrassol / Ourrassol2098.app
```
Puis `http://localhost:5000`. Configuration : `gui/config.json` (`vault_root`,
`pipeline_dir`, `default_scenario`, `scenarios`, `llm.*`). Clés API : `gui/.env`
(chargé par `app.py`). En terminal (bash), refaire `source ~/.zshrc` dans **chaque**
nouveau terminal, sinon `MISTRAL_API_KEY non définie` et toute une file part en
`needs_review` ; vérifier :
`python3 -c "import os; print('OK' if os.environ.get('MISTRAL_API_KEY') else 'ABSENTE')"`.

**Fichiers** : `app.py` (routes générales), `routes_dashboard.py`, `routes_carte.py`
+ `zone_repository.py` (Carte), `routes_veille_signaux.py`, `scripts_config.json`
(panneau), `static/app.js`, `templates/index.html`.

### Choix du modèle
Chaque script choisit son modèle par tier (§0). Le sélecteur Fournisseur / Modèle
n'agit que si **« Forcer ce modèle pour le prochain lancement »** est coché : le
modèle est alors imposé à tous les lancements tant que la case reste cochée, avec un
bandeau orange permanent (bouton « Désactiver ») ; remis à zéro au rechargement. En
terminal : `LLM_PROVIDER=claude LLM_MODEL=… python3 script.py`.

### Panneau de scripts (`scripts_config.json`)
Le panneau gauche est organisé en sections (génération, entités — création /
nettoyage, Relations & lore, géographie — construction / diagnostic, validation,
simulateur…). Chaque entrée décrit ses options ; le formulaire se construit seul.

| Clé d'une entrée / option | Effet |
|---|---|
| `type` : checkbox, select, number, text, `slug_select`, `multi_select` | Type de champ. `slug_select` + `slug_type` charge une liste via `/api/slugs` (dont des listes filtrées : `zones_a_reparenter`, `fiches_a_localiser`, `zones_hier_journal`, `zones_journal_forcer`). |
| `mode_select`, `mode_only`, `config_fields_mode`, `choices[].note` | Onglets de mode ; champs visibles selon le mode ; note sous les onglets. |
| `required`, `required_one_of`, `required_if` | Vérifiés **avant** le lancement (message dans le log). |
| `mutually_exclusive_with` | Cocher « Tous les scénarios » vide et désactive « Scénario », et inversement. |
| `depends_on` | Cocher une correction coche son diagnostic parent ; décocher le parent décoche la correction. |
| `hide_when`, `slug_type_field`/`slug_type_map` | Masque une option ou change la liste de slugs selon un autre champ. |
| `advanced` | Option rangée sous « Options avancées » (repliées). |
| `presets` | Préréglages (ex. Léger / À la carte / Maxi) ; « À la carte » ne touche à rien, les autres posent un état complet. Classe CSS `preset-tab`, jamais `mode-tab`. |
| `fixed_args` | Arguments toujours ajoutés (plusieurs entrées pour un même script). |
| `yaml_files` (+ `copyable`, `lien_seul`) | Fichiers affichés / éditables sous le formulaire ; 📋 Copier, ⬇ Télécharger ; `lien_seul` = nom seul, `.md` ouvert dans Obsidian, autre extension dans VS Code. Le titre d'un `.md` ouvre toujours Obsidian. |

**Comportements à connaître**
- Avant « Lancer », les formulaires YAML ouverts du mode actif sont sauvegardés
  automatiquement (blocage si la sauvegarde échoue) ; ceux d'un autre mode sont
  ignorés.
- Un champ texte vide n'envoie pas son option : le script retombe sur sa config
  (ex. un vieil `angle_specifique` resté dans `config.yaml`).
- « Édition brute » recharge le fichier depuis le disque à chaque bascule.
- « Ajouter à la queue » refuse une entrée à champ requis vide et ne s'envoie qu'une
  fois.
- Les scripts tournent sans clavier (stdin fermé) : pas de mode interactif depuis
  le GUI.

### Onglets
- **Dashboard** : compteurs du vault (`/api/dashboard`), badge de revue.
- **Revue** : fiches en échec des quatre sources (`needs_review_enrich.yaml`,
  `entites_custom/`, `evenements_custom/`, `signaux_custom/` `needs_review.yaml`) avec
  slug, scénario, détail. Un rejet très précoce (avant que l'IA ait produit un nom)
  reste affiché `(entité)`/`(signal)`.
- **Inventaires, résumés, revues, veille, simulateur** : §2septies, §2octies,
  §3quater, §3quinquies.
- **Carte** et **Chantiers** : ci-dessous.

### Onglet Carte
Choisir le scénario ; cliquer un pays (gris = non affecté).
- **Affecter un pays** : zone choisie dans la légende ou « Demander une proposition
  (LLM) » → **🔍 Évaluer l'impact** (obligatoire ; rapport
  `need_action/impact_bascule_{pays}_{scenario}.md`) → confirmer. L'entrée écrite est
  complète (`type_entite: pays`, `portion: null`) ; les entrées adossées à un tracé
  dans d'autres zones sont préservées. Créer une zone depuis un clic donne une zone au
  schéma complet. Royaume-Uni : sélecteur Angleterre / Écosse / Galles.
- **🚫 Ignorer** : pays laissé blanc volontairement.
- **Recherche** (tous niveaux, sans accents) : ouvre l'arbre et entoure la zone en
  orange sur la carte. Une sous-zone sans pays exact ni tracé retombe sur le contour
  de son parent (message dans la barre de statut).
- **Zone N1 — « ✏️ éditer »** (panneau unique) : renommer (aperçu d'impact),
  couleur / motif / hachures (case par zone), « Pays & portions » (↗️ déplacer une
  entrée vers une autre zone = scinder ; ✏️ dessiner / 🗑️ supprimer le masque ;
  ajouter un pays), « Zone dangereuse » (supprimer : refusé s'il reste des
  sous-zones).
- **Sous-zones (arbre)** : ↗️ déplacer, ✏️ renommer (évaluer puis confirmer ; recharger
  la page si l'arbre ne se met pas à jour ; une entité qui porte le même mot dans son
  slug n'est pas renommée), ➕ sous-zone (aperçu, niveau = parent + 1). Elles héritent
  de la couleur de leur N1. Boutons regroupés à droite ; panneau latéral
  redimensionnable (double-clic = largeur par défaut).
- **Dessiner une zone complète** (S11, `gui/zone_dessin_complet.py`) : tracé → classification par pays (split,
  overlay, ignoré) → panneau éditable (cases, textes `portion`) → appliquer. Les
  portions sous le seuil de bruit (2 %) sont dans une section repliée, décochées par
  défaut, cochables.
- **🧬 Zones à enrichir** : proposition IA de `tensions_internes`,
  `periode_transition`, `evenement_transition`, **modifiables avant** « ✓ Appliquer »
  (compléter `evenement_transition` s'il revient vide).
- **🏙️ Villes principales** : capitales et villes > 1 M (seuil réglable,
  `gui/static/villes_principales.json`, précalculé par `extraire_villes_principales.py`
  depuis Natural Earth).
- Bandeau orange `#carte-diagnostic` : pays mal mappés dans
  `gui/static/pays_mapping.json` (absent = rien à corriger).
- Toutes les écritures passent par `ZoneRepository` (`.bak` de la géographie, corps
  régénéré, `zones_pays.json` et tracés synchronisés).

### Onglet Chantiers
Liste de `chantiers_geographie.yaml` groupée par scénario, filtres scénario / type /
statut. Par ligne : Générer / Régénérer (IA, sauf `doublon_pays_entier` déjà calculé),
aperçu de la proposition (avec `contexte_narratif` pour un doublon), Approuver /
Retirer, **✓ Appliquer ce chantier** (si approuvé), Ignorer, Marquer traité, Rouvrir.
Bouton global « Appliquer les propositions approuvées » selon le filtre scénario.
⚠ Avec le filtre sur « Tous », il applique aussi toutes les propositions approuvées
des autres scénarios. Un chantier traité disparaît de la vue « À traiter » (filtre
Statut « Traités » pour le retrouver).

### Routes API principales
| Route | Rôle |
|---|---|
| `/api/config` GET/POST | `config.json` (fusion des clés imbriquées). |
| `/api/scripts`, `/api/script/<id>` | Panneau de scripts. |
| `/api/run` POST, `/api/stream/<run_id>`, `/api/stop/<run_id>`, `/api/status` | Lancer (`{script_id, args, force_llm_override}`), suivre (SSE), arrêter. |
| `/api/yaml` GET/POST, `/api/yaml/form`, `/api/yaml/append` | Lire / écrire un fichier du vault (texte brut, `.bak`), formulaire, ajout à une file (l'en-tête de commentaires de la file est conservé). |
| `/api/slugs` | Listes pour `slug_select`. |
| `/api/review`, `/api/dashboard` | Revue, statistiques. |
| `/api/carte/*` | Carte (`routes_carte.py`) ; restent dans `app.py` : `generer_zone_topdown`, enrichissement des zones, `creer_zone_vide`, et la route dormante `appliquer_zone_topdown_suspecte` (aucun bouton). |
| `/api/zones/lookup`, `/api/zones/pays-liste` | Zone 2098 d'un pays ; liste des pays. |
| `/api/chantiers`, `/generer`, `/approuver`, `/statut`, `/appliquer` | Onglet Chantiers (`appliquer` : `{scenario}`, `{all}` ou `{id}`). |
| `/api/edition/active`, `/articles`, `/injecter_evenement` | Mois de parution (§2quinquies). |
| `/api/veille_signaux/liste`, `/statut` | Veille signaux faibles (§3quater). |
| `/api/ouvrir_vscode` POST | Ouvrir un fichier du vault dans VS Code (macOS). |

### Précautions
- **git** : ne jamais lancer `git checkout -- FICHIER` / `git restore` sans
  `git status` et `git diff FICHIER` : le vault garde souvent des semaines de travail
  non commité (incident du 23 septembre). Commiter avant tout test, restaurer depuis
  ce commit. Les `*.bak` ne sont plus versionnés (`.gitignore` : `.DS_Store`,
  `.obsidian/workspace.json`, `*.bak`, `gui/logs/`, `__pycache__/`, `.env`, `*.pyc`).
  Sur ce Mac, `git ls-files -ci` exige `--exclude-from=.gitignore`.
- **Chemins** : `pipeline_dir` (= `generator/`) ≠ `vault_root` (racine) ; `geographie/`
  est sous `vault_root`. Premier suspect en cas de bug de chemin.
- **Patchs JS** : le node de l'iMac est trop ancien pour vérifier `app.js` entier
  (`||=`) ; vérifier le code ajouté seul.

### Commandes courantes
```bash
# GUI
lsof -ti:5000 | xargs kill -9
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui" && python3 app.py

# Terminal : clé API dans chaque nouveau terminal
source ~/.zshrc

# Géographie
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/generator"
python3 scan_geographie_complet.py --all --write-chantiers
python3 generer_zones_topdown.py --review-topdown --scenario NOM
python3 generer_zones_topdown.py --apply-topdown --scenario NOM

# Contrôle
python3 validate.py
```


### Doublons d'entités et contrôles de géographie (outils du 24 octobre 2026)

*À ajouter à `USER_MANUAL_COMPLET.md`, dans la section des outils de données
(S24). Tous se lancent depuis la racine du vault ; aucun n'appelle l'IA.*

**Repérer les doublons — `scan_doublons_lore.py`** (lecture seule)

```bash
python3 generator/scan_doublons_lore.py [--scenario X] [--seuil 0.85] [--md FICHIER]
```

Trois sections : A, noms identiques ou proches dans un même scénario (nom de
base avant « — » ou « ( ») ; B, fiches alliées ou opposées à elles-mêmes ; C,
même cible à la fois en alliances et en oppositions. Le résumé est sur
l'avant-dernière ligne (`| tail -3`). Il ne compare que les noms : un doublon au
nom différent lui échappe. À relancer après chaque gros lot d'entités.

**Fusionner deux instances — `fusionner_doublon_instance.py`** (v2)

```bash
python3 generator/fusionner_doublon_instance.py --garder A --retirer B          # aperçu
python3 generator/fusionner_doublon_instance.py --garder A --retirer B --apply  # écrit (.bak_fusion)
```

1. Comparer d'abord les deux fiches (`type_dans_scenario`, `role_dans_scenario`,
   `localisation`) : deux acteurs opposés au nom proche ne se fusionnent pas.
2. Choisir la fiche gardée : l'archétype partagé avec d'autres scénarios ; sinon
   comparer les aperçus des deux sens et prendre celui qui réécrit le moins de
   fichiers.
3. Lire l'aperçu : citations dans `geographie/` (listes d'acteurs, « sources
   attestées » : normal), liens `[[archétype]]` laissés intacts (souvent une zone
   de même slug : normal).
4. L'outil protège un événement portant le même slug (event_instance, son
   archétype, champ `evenements_cites`) et l'annonce par ⚠ ; il retire les
   auto-références et résout les conflits internes (opposition gardée). Dans le
   texte libre des articles, un `[[slug]]` partagé reste redirigé.
5. Après `--apply` :
   ```bash
   python3 generator/fix_alliances_oppositions.py --scenario X --reciprocite-seule --ignorer-exclus --resoudre-conflits
   python3 generator/scan_doublons_lore.py --scenario X | sed -n '/^## B/,$p'
   ```
   (`fix_alliances_oppositions.py` écrit sans `--dry-run` ; sans
   `--reciprocite-seule`, il lance une passe IA.) Puis `validate.py` et commit.

La fiche retirée (et son archétype s'il ne sert plus) part dans
`_a_supprimer/fusion_<slug>_<date>/`.

**Zones d'un pays — `zones_par_pays.py`** (lecture seule)

```bash
python3 generator/zones_par_pays.py breakdown Uruguay Argentine Brésil
```

Liste les zones dont `origine_reelle` déclare ces pays (niveau, portion,
chaîne des parents) et leur rattachement dans `gui/zones_pays.json`. Utile avant
toute réaffectation dans la Carte.

**Après une correction de géographie**
- Réaffecter un pays : Carte → clic sur le pays → zone. Déplacer une zone (ou la
  passer N1) : ↗️ déplacer. Renommer une zone : ✏️ (lire le rapport d'impact
  avant de confirmer).
- `validate.py --fix` resynchronise le texte « ## Zones » sur le frontmatter.
- Une nouvelle zone N1 demande ses rédactions :
  `generate_journaux.py --scenario X --update`.
- Un pays partagé entre deux zones demande une `portion` des deux côtés.

**Sauvegardes.** Les fichiers `*.bak*` ne sont plus suivis par git
(`.gitignore`) ; ils restent utiles le temps d'une opération et peuvent être
supprimés ensuite : l'historique git garde l'état de chaque commit.
