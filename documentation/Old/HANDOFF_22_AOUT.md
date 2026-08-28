# Handoff — 22 août 2026

Session longue, en plusieurs reprises dans la journée (démarrée courte
par contrainte de crédits, largement poursuivie ensuite). Détail
complet des décisions dans `BACKLOG_MASTER_9_AOUT.md` (points 9bis,
13, 14) et `USER_MANUAL_COMPLET.md` (nouvelles sections juste avant
"P20 — Phase A").

## Ce qui a été fait et clos aujourd'hui

1. **Confirmation de l'exécution réelle de `rapprocher_articles.py`**
   (point resté en suspens depuis le 21 août soir) — clos.

2. **Diagnostic complet du pattern "institutions à spectre large"** —
   cause confirmée (variables génériques + impact élevé, piste zone
   vide écartée). Deux mécanismes conçus, codés et testés en
   conditions réelles :
   - **Pénalité de score** : conçue, puis **invalidée par test
     synthétique avant tout déploiement** — défaut mathématique
     (n'agit pas sur un cluster de plusieurs instances à égalité de
     fréquence). Abandonnée avant tout code livré au vault.
   - **Cooldown dur + exemption de dominance écrasante** : conçu à la
     place, codé, testé synthétiquement (4 cas) puis **confirmé en
     conditions réelles** (2 déclenchements observés en production sur
     `policy_reform`, cycle complet trigger → cooldown → expiration →
     réintégration confirmé).

3. **Mécanisme `priorite_forcee`** (présence garantie durable d'une
   entité, demande de David) — conçu, codé, **testé de bout en bout en
   conditions réelles** sur les 3 volets (création custom, édition GUI
   dans les deux sens, sélection). **4 bugs GUI trouvés et corrigés en
   testant** (tous introduits par ce chantier, tous corrigés le jour
   même) : `default` manquant sur un champ select, `optional` au lieu
   de `required` (clé jamais lue par la validation), `--scenario` non
   accepté par `argparse`, et un piège plus large dans `app.js`
   (`loadSlugsForSelect()` ne préserve jamais une sélection au
   rechargement, contrairement à la version chips) — corrigé par un
   nouveau mécanisme opt-in (`requires_scenario_selected`).

4. **Uniformisation du dossier de sortie `generate.py`** (signalé par
   David) : les articles unitaires atterrissaient à la racine
   `articles/`, contrairement aux séries. Diagnostiqué (comportement
   conçu ainsi le 10 août, jamais explicité), corrigé sur demande de
   David — `generate.py` range désormais dans `articles/{scenario}`
   comme les séries. Non-régression vérifiée sur les deux scripts qui
   scannent `articles/` (déjà récursifs, déjà basés sur le frontmatter).

5. **Batch de volume P25** (41 articles `new_sustainability`, 2
   batches indépendants) : **0% d'échec de signature**, contre ~25-33%
   mesuré le 21 août sur `fortress_world`/`policy_reform`. Hypothèse
   "couverture `journaux.yaml` incomplète" testée et **réfutée**
   (couverture à 100% partout, aucune zone sans journaliste curaté) —
   cause de l'écart scénario-dépendant **toujours non expliquée**.

6. **Découverte architecturale indépendante** (retour de David :
   "auteur/date gérés à l'édition plutôt qu'à la génération ?") :
   `journaliste_slug` est aujourd'hui extrait du texte généré alors que
   le nom est **déjà connu par le code avant l'appel LLM** dans 100%
   des cas mesurés (`profile["journaliste"]`,
   `get_journal_profile()`). Proposition claire pour régler P25 à la
   racine — **documentée, pas codée**, remise à une session dédiée.

7. **Nouveau point découvert en marge** : `chapo`/`tags`/`image_prompt`
   vides sur ~7% des articles (3/41) — bloc
   `===METADONNEES_PUBLICATION===` absent de la réponse LLM sur ces
   cas. Garde-fou existant fonctionne (pas de plantage), mais aucun
   retry n'existe pour ce cas (contrairement à la longueur). Pas
   diagnostiqué plus avant.

## Fichiers livrés aujourd'hui (à remettre en place dans le vault)

- `set_priorite_forcee.py` (nouveau)
- `loader.py` (cooldown + `priorite_forcee`)
- `create_entities_and_instances.py` (checkbox `priorite_forcee` +
  propagation)
- `scripts_config.json` (nouvelle entrée GUI `set_priorite_forcee` +
  champ `priorite_forcee` sur `create_entities`)
- `app.js` (mécanisme `requires_scenario_selected`)
- `generate.py` (dossier de sortie uniformisé)

**Redémarrage GUI Flask nécessaire** (fichiers `app.js`/
`scripts_config.json` modifiés). Pas nécessaire pour les scripts
backend seuls (`loader.py`, `set_priorite_forcee.py`,
`create_entities_and_instances.py`, `generate.py`).

## Point de reprise exact pour la prochaine session

**Rien d'urgent en cours** — tous les chantiers ouverts aujourd'hui
sont soit clos, soit documentés proprement comme piste pour plus tard.
Trois directions possibles pour la prochaine session, aucune ordonnée
par priorité absolue :

1. **P25 — implémenter la proposition architecturale** : basculer
   `journaliste_slug` d'extraction post-génération à assignation
   directe depuis `profile["journaliste"]` avant génération. Vérifier
   d'abord si un chemin 2/3 (LLM invente un nom) peut réellement se
   produire ailleurs dans le vault avant de supprimer l'extraction en
   repli.
2. **Diagnostic des personnes récurrentes** (`leena_vainala`,
   `amara_diallo_nkosi`) — jamais commencé, distinct du diagnostic
   institutions (cause probablement différente : pool de personnages
   nommés trop restreint sur `policy_reform` ?).
3. **`chapo`/`tags`/`image_prompt` vides (~7%)** — diagnostiquer la
   cause, envisager un retry ciblé comme celui de la longueur.

## Reste en attente, non traité aujourd'hui

- Bug mineur `--stats` de `rapprocher_articles.py` : pas de seuil
  minimum d'articles avant l'alerte `QUASI-OMNIPRÉSENTE` (faussait
  `new_sustainability` à 1 article, avant que le vrai volume ne soit
  disponible). Mineur, non bloquant.
- Choix du service externe de génération d'image (P20) — décision de
  report du 21 août, toujours non tranchée.

## Fichiers à ré-uploader en début de prochaine session

- `BACKLOG_MASTER_9_AOUT.md` (mis à jour) — remplace la version du
  Project.
- `USER_MANUAL_COMPLET.md` (mis à jour) — remplace la version du
  Project.
- `HANDOFF_22_AOUT.md` (ce fichier) — remplace la version précédente
  du même jour si déjà ajoutée au Project.
