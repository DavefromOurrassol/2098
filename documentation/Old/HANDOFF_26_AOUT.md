# Handoff — 26 août 2026

Suite directe de la session du 25 août sur **P21 (journaux oraux)** —
toujours un **chantier en cours**, pas clos. Détail complet dans
`BACKLOG_MASTER_9_AOUT.md` (point 9, suite du 26 août + nouveau point
10) et `USER_MANUAL_COMPLET.md`.

## ⚠️ Chantier en cours — P21, toujours pas terminé

Voir `HANDOFF_25_AOUT.md` pour le contexte complet du chantier. Ce
fichier ne couvre que la suite du 26 août.

## Ce qui a été fait aujourd'hui

1. **Zsófia Nagy confirmée en conditions réelles** — l'orateure ajoutée
   hier sur `fortress_world`/`opposition`/`bloc_eurasiatique_occidental`
   a généré un article oral réussi (structure fidèle, tous les champs
   frontmatter remplis correctement).

2. **`duree_estimee` jugée trop longue (8 min) → plafond `MOTS_MAX_ORAL
   = 700`** (5 min × 140 mots/minute) dans `_resoudre_longueur()`,
   appliqué après toute la logique existante, quelle que soit la
   thématique. Testé en synthétique, **pas encore confirmé sur une
   vraie génération**.

3. **Crash critique trouvé et corrigé** : `NameError: name 'config' is
   not defined` dans `build_article_md()` — conséquence directe d'un
   correctif d'hier (`zone_principale`) qui tentait de lire `config`
   dans une fonction qui ne le reçoit jamais. **Touchait toute
   génération d'article**, pas seulement l'oral. Corrigé (calcul
   déplacé dans `save_article()`, transmis via `metadata`). **Confirmé
   résolu sur 2 générations réelles après correctif.**

4. **Nouveau champ GUI "Forcer un intervenant précis"** — liste
   déroulante dépendante de scénario/ligne/zone/mode, journalistes et
   orateurs mélangés en mode auto/mixte (décision de David). Aucune
   modification `app.js` nécessaire (mécanisme déjà générique depuis
   le 2 août). Un bug trouvé et corrigé en marge (`mode_only` manquant
   — le champ apparaissait à tort en mode "Forcer").

5. **Découverte en marge, non liée à P21** : 53 doublons de nom complet
   entre journalistes `pro_pouvoir`/`opposition` d'une même zone (28%
   des zones concernées) — problème hérité de la génération d'origine
   de `journaux.yaml`. **Nouveau point 10 du backlog, traitement
   reporté par David à une prochaine session.**

4. **3 retours de David sur "Forcer un intervenant précis", tous
   traités et confirmés fonctionnels en conditions réelles** :
   distinction journaliste/orateur dans la liste (labels), filtrage par
   thématique (même logique que `get_journal_profile()`), et un simple
   oubli de sélection de ligne éditoriale (pas un bug). Un doublon
   accidentel de fonction trouvé et nettoyé en marge.

## Fichiers livrés aujourd'hui

- `prompt_builder.py` (cumule tout : plafond oral + intervenant_override)
- `api.py` (correctif du crash `zone_principale`)
- `app.py` (nouvelle branche `intervenants_eligibles`, labels
  journaliste/orateur, filtrage par thématique — cumulé)
- `generate.py` (nouveau `--intervenant`)
- `scripts_config.json` (nouveau champ GUI + `mode_only` corrigé +
  `thematique` ajouté à `slug_extra_params`)

**Redémarrage GUI Flask nécessaire** pour `app.py` et
`scripts_config.json`. Pas nécessaire pour `prompt_builder.py`/
`generate.py`/`api.py`.

**Rappel important sur les dossiers** : `app.py` vit dans `gui/`, pas
`generator/` — même piège que `routes_dashboard.py`/`app.js` les jours
précédents.

## Point de reprise exact pour la prochaine session

1. **Traiter le point 10 du backlog** (doublons de noms pro_pouvoir/
   opposition) — David a explicitement dit "demain". Trois options déjà
   esquissées dans le backlog, aucune tranchée.
2. **Confirmer `MOTS_MAX_ORAL` sur une vraie génération** — jamais
   testé en conditions réelles, seulement synthétique.
3. **Tester le nouveau champ "Forcer un intervenant précis"** de bout
   en bout sur une vraie génération (le bug `mode_only` a été corrigé,
   mais le champ n'a jamais été testé une fois ce correctif appliqué).
4. Reste de P21 : nouveau type d'entité `orateur` (liste `journaux.yaml`
   vs vraie fiche `entites/`), outil de création par LLM, test du mode
   `mixte` en conditions réelles, signature résiduelle en fin d'article
   oral (mineur).

## Reste en attente, non traité (hérité des jours précédents)

- `chapo`/`tags`/`image_prompt` vides (~7% des cas, backlog point 7).
- Choix du service externe de génération d'image (P20, backlog point 6).
- P17 — retester `mistral-small` sur choix contraint.
- Bug #27 — plausibilité logistique inter-zones.
- Renommage des YAML génériques par dossier.
- Troncatures JSON occasionnelles.
- GUI `promote_ville.py`.
- P14 — tier LLM `strict` vers `claude-sonnet-5` (en pause volontaire).

## Fichiers à ré-uploader en début de prochaine session

- `BACKLOG_MASTER_9_AOUT.md` (mis à jour) — remplace la version du
  Project.
- `USER_MANUAL_COMPLET.md` (mis à jour) — remplace la version du
  Project.
- `HANDOFF_26_AOUT.md` (ce fichier) — nouveau, à ajouter au Project,
  en complément de `HANDOFF_25_AOUT.md` (toujours pertinent pour le
  contexte complet de P21).
