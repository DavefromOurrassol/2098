# Backlog consolidé Ourrassol 2098 — état au 7 août 2026

*Remplace intégralement la première version de
`BACKLOG_CONSOLIDE_7_AOUT.md` livrée plus tôt dans cette même session.
Reconstitué à partir de `BACKLOG_CONSOLIDE_5_AOUT.md` et de
`HANDOFF_7_AOUT.md` (version finale).*

---

## 0. Nouveautés du 7 août 2026 — résumé actionnable

Seul point resté ouvert depuis le 5 août : le traitement à long terme
des 146 conflits de réciprocité. **Clos cette session**, avec deux bugs
réels découverts et corrigés en cours de route.

1. ✅ **Résolution automatique des conflits implémentée** — règle
   "opposition prioritaire" (`resolve_reciprocity_conflicts()`). Mode
   conservateur par défaut, mode fort optionnel (`--bascule-en-opposition`).
2. ✅ **Vault réel traité : 0 conflit restant**, confirmé.
3. ✅ **Bug #1 corrigé** — écrasement silencieux des résolutions quand
   une fiche était impliquée dans plusieurs conflits distincts du même
   scénario (frontmatter original jamais rafraîchi entre écritures).
   Découvert au premier `--apply` réel, corrigé (accumulation par fiche
   avant écriture), re-testé, second `--apply` confirmé 0 conflit.
4. ✅ **Bug #2 corrigé — rapports `.md` jamais réinitialisés.** David
   confus par `fix_alliances_conflits_reciprocite.md`, affiché tel quel
   par le GUI, accumulant sans jamais s'effacer l'historique de tous les
   runs depuis le 4 août — donnant l'impression fausse d'un vault plein
   de conflits alors qu'il était déjà propre. Cause : les deux fichiers
   de rapport ouverts en mode `"a"` (append), jamais tronqués. Corrigé
   avec `reset_conflict_reports()`, appelée une fois en tête de chaque
   run réel (jamais en dry-run), y compris le cas limite d'un run à 0
   conflit sur tous les scénarios (sans quoi le vieux fichier serait
   resté affiché indéfiniment).
5. ✅ **Renommage "Règle C" → "opposition prioritaire"** — dans le code
   et le manuel.
6. ✅ **Intégration continue dans `enrich_minimal.py`** — résolution des
   conflits ET reset des rapports, opt-in où pertinent, comportement par
   défaut inchangé sans les nouveaux flags. Testé (câblage complet).
7. ✅ **Intégration GUI réelle** — nouvelle entrée
   `fix_alliances_oppositions` + entrée `enrich_minimal` complétée dans
   `scripts_config.json`, descriptions mises à jour pour préciser l'état
   "dernier run uniquement" des rapports. Vérifié sans régression sur
   les 18/19 autres entrées.
8. ✅ **Mécanique GUI vérifiée par lecture directe du code réel**
   (`app.py`/`app.js`, uploadés en session) — les deux dernières
   incertitudes du manuel (rendu `depends_on`+`advanced` combinés,
   affichage `.md` dans le panneau de review) confirmées fonctionnelles
   sans avoir besoin d'un test navigateur. Commande de lancement du GUI
   confirmée : `python3 app.py`, `http://localhost:5000`.
9. ✅ **Documentation à jour** — `USER_MANUAL_COMPLET.md` §3/§6/§7
   réécrits pour refléter l'état réel de bout en bout.

**Fichiers livrés** : `fix_alliances_oppositions.py`, `enrich_minimal.py`,
`scripts_config.json`, `USER_MANUAL_COMPLET.md`.

---

## 1. Ce qui reste réellement à faire

### 1.1 — Tester les deux entrées GUI dans un vrai navigateur
Seul point encore purement ouvert. La logique (`depends_on`+`advanced`,
affichage `.md`, exclusions mutuelles, `required_one_of`) a été
confirmée par lecture directe du code source réel (`app.py`/`app.js`),
donc la confiance est haute — mais personne n'a encore cliqué dans un
vrai navigateur. `gui_verified: false` sur les deux entrées tant que ce
n'est pas fait.

### 1.2 — Décider du sort de `type_relation_dominante`/`annee_debut`/`annee_fin`
Inchangé depuis le 3-4 août — `type_relation_dominante` rempli à 100 %
sur les 426 fiches d'origine (candidat solide pour le prompt de
génération d'articles). Décision toujours à prendre avec David.

### 1.3 — Vérifier si `metadata["longueur"]` (bug corrigé le 3 août) est réutilisé en aval
Inchangé depuis le 3 août.

---

## 2. Gros chantiers volontairement en pause (pas oubliés, juste différés)

### 2.1 — Renommage des YAML génériques par dossier
Inchangé depuis le 3 août.

### 2.2 — P14 : passer le tier LLM `strict` vers `claude-sonnet-5` en prod
Différé sine die sur demande explicite de David (1er août).

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
- **Traçabilité des résolutions "opposition prioritaire"** — choix
  assumé de journaliser en fichier externe (désormais réinitialisé à
  chaque run, voir §0 point 4) plutôt que de marquer chaque fiche
  résolue dans son propre frontmatter. Cohérent avec l'esprit "patch
  chirurgical" du script.

---

## 4. Risque structurel identifié (pas un bug actif — rien à corriger tant qu'il ne se manifeste pas)

**Instances avec `injection.type == "custom"` non sélectionnées parmi
les `filtered_instances`** — inchangé depuis le 3 août. Aucun exemple
réel rencontré à ce jour.

---

## 5. Clarifications historiques (rappel, complété le 7 août)

- **P8** (426 fiches `officialise_minimal`) — clos, 27 juin 2026.
- **`noeud_mnemos_pannonie`** — clos depuis le 14 juillet (P23).
- **P18** (cohérence `routes_dashboard.py`) — clos le 13 juillet.
- **P22 signal 2** — fusionné et livré via P24 étape B.
- **P24 étape C** — absorbé par le système `chantiers_geographie.yaml`.
- **Chantier alliances/oppositions (4-5 août)** — clos à tous les
  niveaux.
- **Chantier résolution des conflits de réciprocité (7 août)** — clos à
  tous les niveaux, y compris les deux bugs découverts en conditions
  réelles (écrasement multi-conflits, rapports jamais réinitialisés) et
  la vérification GUI par lecture de code. Seul reliquat : test
  navigateur (§1.1 ci-dessus).
