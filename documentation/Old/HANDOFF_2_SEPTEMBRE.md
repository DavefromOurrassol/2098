# Handoff — 2 septembre 2026

Session complète sur le chantier "Mois de parution (éditions datées)",
scopé le 30 août (voir `BACKLOG_ACTIF.md` avant cette session pour le
diagnostic d'origine). Design tranché point par point avec David, puis
codé et testé le même jour.

## Fait

- **Point 1 (ampleur de la généralisation) confirmé et élargi** — grep
  exhaustif de `2098` dans `generator/` : 3× `duree_effet` en dur
  (`snapshot.py`), `year: 2098` en dur, **et découverte que `DATES_2098`
  est tripliquée** (copies indépendantes dans `generate.py`/
  `generate_series.py`/`generate_manual.py`), toutes fixées à l'année
  2098 sans notion de mois. Fallback texte de `prompt_builder.py`
  (ligne ~1782) confirmé mort en pratique (aucun chemin actuel ne le
  déclenche — vérifié via `scripts_config.json`, aucun flag
  `--date-fictive` exposé côté GUI).
- **Point 2 (format de la date de référence) tranché** — décimal
  fractionnaire (`2098.08`), via deux fonctions centralisées
  obligatoires (`edition_date_to_float`/`float_to_edition_date`) pour
  éviter tout bug de comparaison flottante par concaténation ad hoc.
  Jour de rédaction par article tranché séparément (mois de parution =
  un label unique par numéro, jour de rédaction = propre à chaque
  article, façon dateline journalistique — recherche web sur la presse
  mensuelle réelle) : tiré dynamiquement dans le mois, pas de fenêtre
  de bouclage débordant sur le mois précédent (jugé trop complexe pour
  le gain).
- **Point 3 (remontée jusqu'à `build_snapshot()` + notion d'édition)
  tranché** — paramètre optionnel `date_edition=None` (rétrocompatible).
  `generate_series.py` **et** `generate_manual.py` adoptent le mois de
  parution (même `config_series.yaml`, `generate_manual.py` suit
  structurellement la même série). `generate.py` (article isolé) **lit**
  le mois de parution actif, ne l'écrit jamais (décision de David).
- **Point 4 (production des `custom_events`) tranché** — Option
  manuelle retenue (curation via `inject_custom_events.py`, nouveau
  champ `edition_active: true`) plutôt qu'extraction automatique LLM
  (jugée trop risquée sans protocole de validation, même raisonnement
  que l'exclusion du mode auto sur `ton_personnel`). Nouvel outil
  `audit_sujets_edition.py` décidé et codé dans le même chantier.
- **Implémentation complète** : `edition_utils.py` (nouveau module
  central), `snapshot.py`, `generate_series.py`, `generate_manual.py`,
  `generate.py`, `inject_custom_events.py`, `config_series.yaml`
  modifiés. Testé en dry-run réel par David : 4/4 prompts assemblés
  sans erreur, dates correctement bornées au mois de l'édition, `year`
  et `duree_effet` cohérents.
- **Mois de parution configurable indépendamment** (demande de David
  après le premier lot codé) — nouvel outil `definir_edition.py` :
  fixe/avance le mois de parution actif sans générer aucun article.
  `generate_series.py`/`generate_manual.py` retombent dessus par défaut
  si `annee_edition`/`mois_edition` sont absents de
  `config_series.yaml` (toujours surchargeables ponctuellement).
- **Terminologie revue** ("édition" jugé ambigu par David — lu comme
  "modifier" plutôt que "numéro du journal") : "mois de parution" adopté
  partout où le texte est visible par David (CLI, GUI, description
  d'écran) — les noms de fichiers/fonctions internes
  (`state/editions.json`, `edition_utils.py`) restent inchangés, pur
  détail d'implémentation invisible.
- **GUI** : nouvel écran "Mois de parution du journal" (`scripts_config.
  json`, `gui_verified: false`), champs `annee_edition`/`mois_edition`
  retirés de l'écran "Générer une série d'articles" (redondants avec le
  nouvel écran). Bandeau informatif ajouté sur "Générer un article"
  (confirme le mois qui sera utilisé) et sur le nouvel écran (état
  avant modification) — nouvelle route `GET /api/edition/active`
  (`app.py`, lecture directe de `state/editions.json`, même pattern que
  `_lire_journaux()`).
- **`USER_MANUAL_COMPLET.md` mis à jour** — nouvelle section §2quinquies
  (mécanisme complet, décisions, limites connues), renvoi ajouté sur
  l'entrée `inject_custom_events.py` existante (§3), nouvelle route API
  ajoutée au tableau (§7), en-tête et compteur de scripts actualisés.

## Bugs trouvés/corrigés

- **`snapshot.py`** : artefact d'imprécision flottante à l'affichage
  (`51.05000000000018 ans d'effet` au lieu de `51.05`) — trouvé en
  lisant la sortie du dry-run de David. Corrigé par `round(duree_effet,
  2)` sur les 3 `print()` concernés ; le calcul en aval (`facteur`)
  utilise toujours la valeur exacte non arrondie, seul l'affichage
  change.
- **`edition_utils.py`** : `definir_edition_active()` réattribuait le
  même numéro d'édition en avançant plusieurs fois de suite sans jamais
  générer d'article réel (ex. avancer de juin → septembre → octobre
  sans rien générer redonnait le même numéro à septembre et octobre) —
  cause racine : le numéro n'était calculé que depuis `historique`
  (articles réellement produits), qui restait vide tant que rien
  n'était généré. Corrigé avec un registre séparé `editions_connues`
  (toute édition déclarée OU générée), indépendant de `historique`.
  Retesté : numéros stables et uniques même en avançant plusieurs fois
  sans génération.

## Décisions actées

- **Mois de parution GLOBAL** (David, en réponse à une question
  explicite) : un seul numéro partagé par les 6 scénarios, pas un
  numéro indépendant par scénario — les mondes fictifs avancent en
  parallèle, pas indépendamment.
- **`generate.py` suit le mois de parution actif sans jamais le créer**
  (option 2 tranchée par David face à deux options présentées) — un
  article isolé n'a pas vocation à déclencher un nouveau mois de
  parution, seuls les lancements de série le peuvent.
- **Production des `custom_events` : curation manuelle**, pas
  d'extraction automatique pour ce chantier — notée comme piste
  séparée possible si le besoin se confirme, pas immédiatement
  nécessaire.
- **Risque de formulation temporelle relative incohérente** (deux
  articles du même numéro à des jours différents) : pas de correctif
  préventif, à observer en conditions réelles d'abord — cohérent avec
  l'approche déjà suivie sur P17/Bug#27.
- **Fenêtre de bouclage** (jour de rédaction débordant sur la fin du
  mois précédent, comme en presse réelle) : écartée, jugée trop
  complexe pour un gain surtout esthétique.
- **Terminologie "mois de parution"** actée pour tout texte visible par
  David — noms de fichiers/fonctions internes non renommés (pur détail
  d'implémentation).

## Reste à faire (point de reprise)

- **Tester une vraie génération** (non dry-run) et confirmer que
  `state/editions.json` s'enregistre correctement en conditions
  réelles (au-delà du dry-run déjà validé).
- **Tester `inject_custom_events.py --edition-active`** en conditions
  réelles (nécessite un mois de parution déjà actif, donc après le
  point précédent ou via `definir_edition.py`).
- **Cliquer dans le navigateur réel** sur l'écran "Mois de parution du
  journal" et le bandeau de "Générer un article" — `gui_verified` à
  passer à `true` sur `definir_edition` une fois fait.
- **Observer si le risque de formulation temporelle** (identifié mais
  pas corrigé préventivement) se matérialise réellement sur des
  articles générés en conditions réelles.
- Piste "extraction automatique des `custom_events`" laissée de côté —
  à ne reprendre que si le besoin se confirme après usage réel de la
  curation manuelle.

## Fichiers livrés/modifiés

- `edition_utils.py` (nouveau)
- `definir_edition.py` (nouveau)
- `audit_sujets_edition.py` (nouveau)
- `snapshot.py` (modifié)
- `generate_series.py` (modifié)
- `generate_manual.py` (modifié)
- `generate.py` (modifié)
- `inject_custom_events.py` (modifié)
- `config_series.yaml` (modifié)
- `scripts_config.json` (modifié — nouvel écran, champs retirés de
  "Générer une série")
- `app.py` (modifié — route `GET /api/edition/active`)
- `app.js` (modifié — bandeau informatif sur deux écrans)
- `USER_MANUAL_COMPLET.md` (restructuré — nouvelle section §2quinquies
  + mises à jour ponctuelles §0/§3/§7)
- `BACKLOG_ACTIF.md` (chantier 2 mis à jour : ⚪ diagnostic → 🟢 codé,
  à tester)

## Non traité aujourd'hui (hérité)

- Point ⚪ métaphores vs. descripteurs directs (`ton_personnel`) —
  toujours en suspens, voir Partie 1/secondaire du backlog.
- `chapo`/`tags`/`image_prompt` vides (~7% des cas).
- Choix du service externe de génération d'image (P20).
- P17, Bug #27, renommage YAML génériques, troncatures JSON, GUI
  `promote_ville.py`, P14 — tous en observation, aucun changement.

## Fichiers à ré-uploader en début de prochaine session

- `BACKLOG_ACTIF.md` — remplace la version précédente dans le Project.
- `USER_MANUAL_COMPLET.md` — remplace l'ancienne version dans le
  Project.
- `HANDOFF_2_SEPTEMBRE.md` (ce fichier) — remplace `HANDOFF_29_AOUT.md`.
