# Backlog consolidé Ourrassol 2098 — état au 5 août 2026

*Reconstitué à partir de `BACKLOG_CONSOLIDE_4_AOUT.md` et de
`HANDOFF_5_AOUT.md`. Objectif inchangé : ne garder que ce qui est
réellement encore ouvert.*

---

## 0. Nouveautés du 5 août 2026 — résumé actionnable

Session directement enchaînée sur le chantier alliances/oppositions du 4
août. Deux points étaient explicitement laissés ouverts : (1) corriger
la source pour que les futures instances ne retombent pas dans le même
piège, (2) automatiser la réciprocité. **Les deux sont clos.**

1. ✅ **Root cause corrigée dans `enrich_minimal.py`** — nouvelle section
   de prompt listant les instances réelles du scénario (`build_
   instances_summary()`, équivalent de `build_geographie_summary()`
   pour la géographie). Testé en conditions réelles : 8/8 slugs générés
   confirmés réels dans le vault.
2. ✅ **Réciprocité automatisée** — `enrich_minimal.py` appelle
   désormais `reciprocity_pass()` (de `fix_alliances_oppositions.py`,
   devenu une dépendance de production) en fin de run, sauf `--dry-run`
   ou `--skip-reciprocite`. Testé : 3 cas unitaires + 1 test réel (7
   fiches du vault complétées automatiquement après enrichissement
   d'une fiche de test).
3. ✅ **Validation `alliances`/`oppositions` durcie partiellement** —
   auto-référence et chevauchement alliances/oppositions bloquants
   (déclenchent le retry existant), warning sur slug inconnu laissé
   inchangé pour préserver le pipeline de slugs fantômes
   (`extract_and_queue_phantoms()`). Décision de David après
   présentation de 3 options.

**Découverte annexe, indépendante mais traitée dans la foulée** :

4. ✅ **284 fiches instances (40% du vault) sans champ `statut` du
   tout** — invisibles à tous les scripts filtrant sur `statut`,
   inconnues du diagnostic du 4 août (qui ne portait donc que sur 426
   des 710 fiches réelles). 283/284 avaient un contenu enrichi complet
   (juste jamais étiquetées) ; régularisées en `officialise_enrichi`
   après vérification. **Vault désormais à 710/710 fiches cohérentes.**
   Détail complet en `HANDOFF_5_AOUT.md` §3.

**Fichiers livrés** : `enrich_minimal.py` (version finale cumulant les 3
correctifs). Aucune modification à `fix_alliances_oppositions.py`
lui-même (réutilisé tel quel comme dépendance).

---

## 1. Ce qui reste réellement à faire

### 1.1 — Que faire des 146 conflits de réciprocité, à terme ?
**Inchangé depuis le 4 août** — toujours en statu quo assumé, décision
de fond encore ouverte. Trois pistes déjà esquissées (laisser
définitivement / résolution manuelle cas par cas / règle automatique de
priorité) — voir `BACKLOG_CONSOLIDE_4_AOUT.md` §1.1 pour le détail.
Aucune action requise tant que David n'a pas tranché. Ce chiffre ne
devrait plus augmenter de façon significative via `fix_alliances_
oppositions.py` (chantier de migration clos), mais peut légèrement
grossir via la réciprocité désormais automatique dans `enrich_
minimal.py` à chaque nouvelle création d'instance — normal, pas un
signal d'alerte.

### 1.2 — `fix_alliances_oppositions.py` absent du GUI
Le script tourne uniquement en CLI aujourd'hui — jamais enregistré dans
`scripts_config.json`. Pas bloquant (la ligne de commande reste
pleinement fonctionnelle), mais à reconsidérer maintenant qu'il est
devenu une **dépendance de production** d'`enrich_minimal.py` (import
direct de `reciprocity_pass()`) plutôt qu'un simple outil de migration
ponctuel. Décision à prendre avec David — pas de calendrier imposé.

### 1.3 — Décider du sort de `type_relation_dominante`/`annee_debut`/`annee_fin`
Inchangé depuis le 3-4 août — `type_relation_dominante` rempli à 100 %
sur les 426 fiches d'origine (candidat solide pour le prompt de
génération d'articles). Décision toujours à prendre avec David.

### 1.4 — Vérifier si `metadata["longueur"]` (bug corrigé le 3 août) est réutilisé en aval
Inchangé depuis le 3 août. David doit vérifier `api.py` pour trancher si
un script de correction rétroactive est nécessaire sur les fiches déjà
publiées avant le correctif.

---

## 2. Gros chantiers volontairement en pause (pas oubliés, juste différés)

### 2.1 — Renommage des YAML génériques par dossier
Inchangé depuis le 3 août. Aucune urgence identifiée.

### 2.2 — P14 : passer le tier LLM `strict` vers `claude-sonnet-5` en prod
Différé sine die sur demande explicite de David (1er août). Inchangé
depuis le 4 août.

### 2.3 — P20 : enrichissement frontmatter pour publication web future
Inchangé depuis le 3 août — scoping complet fait, rien codé.

### 2.4 — P21 : journaux oraux, orateurs itinérants
Inchangé depuis le 3 août — scoping complet fait, rien codé.

---

## 3. Points mineurs, non bloquants, sans action requise

- **P15** — `acteurs_hint_count` non plafonné en filtre dur. Inchangé.
- **`--force` du panneau `--scan-pending`** — inchangé.
- **`coverage_proposals_reference.yaml`** sans `.applied` — inchangé.
- **`/api/carte/appliquer_zone_topdown_suspecte`** — inchangé.
- **Champ `type` des zones géographiques** — inchangé.
- **Bloc `simulation`** sur les fiches variables — inchangé.
- **`constrained_variables`** — inchangé.
- **Incohérence documentation/code `forces_attractives`/`forces_
  repulsives`** — inchangé.
- **146 conflits de réciprocité alliances/oppositions** — voir §1.1
  ci-dessus (déplacé de "points mineurs" à "ce qui reste à faire" le 5
  août, puisque David a explicitement laissé la question ouverte plutôt
  que de la classer comme définitivement close).

---

## 4. Risque structurel identifié (pas un bug actif — rien à corriger tant qu'il ne se manifeste pas)

**Instances avec `injection.type == "custom"` non sélectionnées parmi
les `filtered_instances`** — inchangé depuis le 3 août. Aucun exemple
réel rencontré à ce jour.

---

## 5. Clarifications historiques (rappel, inchangé depuis le 3-4 août)

- **P8** (426 fiches `officialise_minimal`) — clos, traité intégralement
  le 27 juin 2026.
- **`noeud_mnemos_pannonie`** — clos depuis le 14 juillet (P23).
- **P18** (cohérence `routes_dashboard.py`) — clos le 13 juillet.
- **P22 signal 2** — fusionné et livré via P24 étape B.
- **P24 étape C** — absorbé par le système `chantiers_geographie.yaml`.
- **Chantier alliances/oppositions (4-5 août)** — clos à tous les
  niveaux : migration du passé (356→0 fiche vide), découverte et
  correction d'une anomalie indépendante (284 fiches sans `statut`,
  vault à 710/710 cohérent), correction de la source dans `enrich_
  minimal.py`, réciprocité automatisée, validation durcie. Seul reliquat
  ouvert : le traitement à long terme des 146 conflits (§1.1).
