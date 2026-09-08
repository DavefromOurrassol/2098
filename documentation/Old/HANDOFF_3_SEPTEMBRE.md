# Handoff — 3 septembre 2026

Session de tests en conditions réelles du chantier "Mois de parution
(éditions datées)" scopé/codé le 2 septembre (voir `BACKLOG_ACTIF.md`
et `HANDOFF_2_SEPTEMBRE.md` avant cette session pour le contexte), puis
extension du chantier avec un nouvel écran "Promouvoir un événement".
Chantier entier clos en fin de session.

## Fait

- **Test 1 (vraie génération, non dry-run)** — premier lancement de
  `generate_series.py` a échoué proprement (`state/editions.json`
  n'existait pas encore, aucun mois de parution actif, comportement
  attendu). Résolu en configurant un mois de parution (2098/08) via
  l'écran GUI dédié "Mois de parution du journal", testé pour la
  première fois en conditions réelles. Génération relancée avec succès
  via le GUI ("Générer une série d'articles") : 3 articles
  `fortress_world` (culture/histoire_patrimoine/religion_spiritualite)
  avec dates de rédaction distinctes et bornées au mois (19/13/23 août
  2098) — confirme le tirage dynamique par article. Aucune
  incohérence de formulation temporelle relative observée sur ce
  batch (à confirmer sur plus de volume).
- **`state/editions.json` confirmé correct** après ce run réel :
  `edition_active`/`editions_connues`/`historique` tous cohérents
  (numéro 1, 2098/08, `fortress_world`, `nb_articles: 3`).
- **Bandeau "Mois de parution" étendu à `generate_series.py`**
  (`app.js`) — absent du scope initial du 2 septembre (l'écran série
  n'avait jamais eu ce bandeau), ajouté à la demande de David après le
  test 1. Texte spécifique à ce cas (mentionne le repli sur
  `config_series.yaml` et le risque d'échec si aucun mois n'est actif).
- **`audit_sujets_edition.py` intégré au GUI** — `--json` ajouté (même
  convention que `extract_localisation.py --json`), `entites_citees`
  ajouté à la sortie. Nouvelle entrée `scripts_config.json` (section
  "Validation"). Testé et validé par David.
- **Nouveau chantier "Promouvoir un événement depuis un article"** —
  David voulait remplacer la saisie manuelle de `queue.yaml` par un
  flux liste d'articles → sélection → formulaire pré-rempli →
  injection directe. Conception tranchée via question explicite :
  injection directe pour l'idée choisie (comme `--mode custom` mais
  pour une seule idée), liste limitée à un scénario à la fois.
  - `inject_custom_events.py` : nouveau mode `--idea '<json>' --json` —
    injecte une idée unique sans jamais passer par `queue.yaml`,
    réutilise `process_idea()` tel quel + nouvelle fonction partagée
    `_enregistrer_resultat_idea()` (factorisée depuis `run_custom_mode`).
  - `app.py` : deux nouvelles routes — `GET /api/edition/articles`
    (liste les articles du mois pour un scénario) et
    `POST /api/edition/injecter_evenement` (lance l'injection, timeout
    240s).
  - GUI : nouvel onglet custom "Promouvoir un événement", placé dans
    la section sidebar "Entités & événements — création" (décision
    explicite de David, pas un onglet top-level séparé). Gabarit
    visuel dupliqué depuis l'onglet Rédaction (liste cliquable +
    panneau de détail).
  - Testé en conditions réelles par David : chaîne `/api/edition/articles`
    validée (5 articles remontés sur `fortress_world`), écran testé,
    injection validée.
- **Question de David sur la reprise d'un événement promu dans les
  mois suivants** — mécanisme `select_relevant_events` (`loader.py`)
  analysé en détail : score = 3×(recoupement variables_visibles de la
  thématique) + 1×(variables_secondaires) + 1,5×rang de portée +
  0,1×min(amplitude, 40), trié décroissant ; la rotation à mémoire ne
  départage que les ex-æquo de score. Le mode "Forcer" existant
  (`generate.py`) garantit une inclusion mais article par article, pas
  un réglage mensuel. **Décision actée** : pour garantir qu'un article
  traite d'un sujet donné, générer cet article via le mode Forcer
  plutôt que chercher un mécanisme d'épinglage mensuel (qui n'existe
  pas).

## Bugs trouvés/corrigés

Aucun nouveau bug trouvé aujourd'hui — les deux bugs de la session
précédente (arrondi flottant `snapshot.py`, réattribution de numéro
d'édition `definir_edition_active()`) sont restés stables sous test
réel, rien de nouveau observé.

## Décisions actées

- **Placement et titre de l'écran** : "Promouvoir un événement" (pas
  "Injecter un événement"), rangé dans "Entités & événements —
  création" plutôt qu'en onglet top-level séparé — décision explicite
  de David après avoir vu la première version.
- **Injection directe, pas de passage par `queue.yaml`** pour ce
  nouvel écran — tranché via question explicite à David.
- **Périmètre de la liste d'articles : un scénario à la fois** (comme
  `audit_sujets_edition.py`), pas tous les scénarios mélangés —
  tranché via la même question.
- **Reprise d'un événement dans le mois suivant : mode Forcer,
  article par article** — pas de nouveau mécanisme d'épinglage mensuel
  à construire, le levier existant (variables_hint + Forcer) suffit.

## Reste à faire (point de reprise)

- **Observer le risque de formulation temporelle relative** sur un
  volume plus important d'articles générés (rien observé sur le petit
  batch de ce jour, mais l'échantillon reste faible) — pas de
  correctif préventif tant que rien ne remonte, cohérent avec
  P17/Bug#27.
- Chantier "Mois de parution" + "Promouvoir un événement" considérés
  **clos** par David — rien d'autre identifié à ce stade.

## Fichiers livrés/modifiés

- `audit_sujets_edition.py` (modifié — `--json`, `entites_citees`)
- `inject_custom_events.py` (modifié — mode `--idea`/`--json`,
  `_enregistrer_resultat_idea()`)
- `app.py` (modifié — routes `/api/edition/articles` et
  `/api/edition/injecter_evenement`)
- `app.js` (modifié — bandeau étendu à `generate_series`, nouvel écran
  "Promouvoir un événement")
- `index.html` (modifié — CSS et structure HTML du nouvel écran)
- `scripts_config.json` (modifié — `audit_sujets_edition` ajouté,
  `gui_verified: true` sur `definir_edition` et `audit_sujets_edition`)
- `USER_MANUAL_COMPLET.md` (mis à jour — §2quinquies étendu : mécanisme
  de reprise détaillé, section "Promouvoir un événement", tableau des
  routes GUI en §7, en-tête actualisé)
- `BACKLOG_ACTIF.md` (chantier 2 clos et retiré, renvoi vers
  `BACKLOG_ARCHIVE.md`)
- `HANDOFF_3_SEPTEMBRE.md` (ce fichier — remplace
  `HANDOFF_2_SEPTEMBRE.md`)

## Non traité aujourd'hui (hérité)

- Point ⚪ métaphores vs. descripteurs directs (`ton_personnel`) —
  toujours en suspens.
- Choix du service externe de génération d'image (P20).
- P17, Bug #27, renommage YAML génériques, troncatures JSON, GUI
  `promote_ville.py`, P14 — tous en observation, aucun changement.

## Fichiers à ré-uploader en début de prochaine session

- `BACKLOG_ACTIF.md` — remplace la version précédente dans le Project.
- `USER_MANUAL_COMPLET.md` — remplace l'ancienne version dans le
  Project.
- `HANDOFF_3_SEPTEMBRE.md` (ce fichier) — remplace `HANDOFF_2_SEPTEMBRE.md`.

## À faire par David avant la prochaine session

- **`BACKLOG_ARCHIVE.md`** : le chantier "Mois de parution (éditions
  datées)" + "Promouvoir un événement" doit y être archivé (texte
  complet ci-dessous, prêt à coller) — je n'ai pas ce fichier cette
  session pour l'éditer directement.

<details>
<summary>Texte à archiver dans BACKLOG_ARCHIVE.md</summary>

```markdown
## Mois de parution (éditions datées) + Promouvoir un événement — clos le 3 septembre 2026
Scopé le 30 août, conçu et codé le 2 septembre, testé et étendu le 3
septembre. Objectif double : progression réelle du monde dans l'année
(pas juste une sélection de sujets sur un état figé) + continuité
narrative entre éditions successives. Terminologie "mois de parution"
retenue (préférée à "édition", jugée ambiguë).

Mécanisme central : edition_utils.py (conversion année+mois ↔ date
fractionnaire 2098.08, tirage du jour de rédaction, registre
state/editions.json GLOBAL partagé par les 6 scénarios).
build_snapshot() gagne date_edition (rétrocompatible) ; les 3 formules
duree_effet remplacent 2098 en dur.

Nouveaux outils : definir_edition.py (fixe/avance le mois de parution
indépendamment de tout lancement de série, écran GUI dédié,
gui_verified: true) ; audit_sujets_edition.py (liste les articles du
mois + custom_events déjà injectés, intégré au GUI le 3 septembre) ;
puis extension "Promouvoir un événement" (3 septembre) : nouveau mode
inject_custom_events.py --idea (injection directe d'une idée unique,
sans queue.yaml), routes /api/edition/articles et
/api/edition/injecter_evenement, écran GUI dédié rangé dans "Entités &
événements — création".

generate_series.py/generate_manual.py : annee_edition/mois_edition
optionnels dans config_series.yaml, repli sur le mois de parution
actif. generate.py : lit en lecture seule, ne crée/avance jamais.
Bandeau GUI "Mois de parution" sur les trois écrans de génération
(generate, generate_series, definir_edition).

Production des custom_events : option manuelle retenue
(inject_custom_events.py, champ edition_active: true) plutôt
qu'extraction automatique LLM — jugée trop risquée sans protocole de
validation.

Bugs trouvés et corrigés en testant : artefact d'imprécision flottante
à l'affichage (snapshot.py, round(duree_effet, 2)) ; réattribution du
même numéro d'édition en avançant plusieurs fois sans générer
(definir_edition_active(), corrigé avec le registre editions_connues
séparé de historique).

Mécanisme de reprise d'un custom_event dans les articles futurs
(analysé en détail le 3 septembre, loader.py::select_relevant_events) :
score = 3×(recoupement variables_visibles thématique) +
1×(variables_secondaires) + 1,5×rang_portee + 0,1×min(amplitude,40),
trié décroissant ; rotation à mémoire ne départage que les ex-æquo de
score, ne fait jamais remonter un événement faible. Mode Forcer
(forced_event_slug, existant sur generate.py) garantit une inclusion
mais article par article, pas de réglage mensuel équivalent. Décision :
pour garantir qu'un article traite d'un sujet, utiliser le mode Forcer
plutôt qu'un mécanisme d'épinglage qui n'existe pas.

Testé en conditions réelles le 3 septembre par David : génération
réelle (3 articles fortress_world, dates distinctes bornées au mois,
state/editions.json cohérent), écran "Mois de parution du journal",
bandeau sur "Générer une série d'articles", écran "Promouvoir un
événement" de bout en bout. Aucune incohérence de formulation
temporelle observée sur ce petit volume — à continuer d'observer, pas
de correctif préventif (cohérent avec P17/Bug#27).

Documentation complète : §2quinquies de USER_MANUAL_COMPLET.md.

Fichiers touchés : edition_utils.py, definir_edition.py,
audit_sujets_edition.py (nouveaux) ; snapshot.py, generate_series.py,
generate_manual.py, generate.py, inject_custom_events.py,
config_series.yaml, scripts_config.json, app.py, app.js, index.html
(modifiés).
```

</details>
