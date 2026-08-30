# Handoff — 29 août 2026

Suite de la session P21 (voir `HANDOFF_25_AOUT.md` et `HANDOFF_26_AOUT.md`
pour le contexte complet du chantier). Ce fichier couvre : la clôture
du point 10 du backlog (doublons de noms), et le nouveau chantier
`ton_personnel`.

## Ce qui a été fait aujourd'hui

1. **Point 10 du backlog clos** — les 53 doublons de nom complet entre
   journalistes `pro_pouvoir`/`opposition` sont tous corrigés.
   Nouvel outil `fix_doublons_journalistes.py` : renommage
   semi-automatisé par LLM (toujours côté opposition), validation
   anti-collision stricte, sauvegarde horodatée automatique avant
   écriture. **2 bugs trouvés et corrigés en marge** : le retry ne
   couvrait que les collisions de nom (jamais les échecs de parsing
   JSON, expliquant pourquoi relancer le script retombait sur le même
   échec), et la cause probable des échecs identifiée (guillemets
   ASCII internes pour un surnom cassant le JSON strict). 53/53
   réussis en 2 passes.

2. **Nouveau chantier `ton_personnel`** — nuance de style personnelle
   par journaliste/orateur, en complément (jamais en remplacement) du
   ton déjà établi de la zone. Champ unifié (David a préféré un seul
   nom plutôt que `ton_personnel`/`style_rhetorique` séparés). Nouvel
   outil `set_ton_personnel.py` (mode personne unique ou zone entière,
   valeur directe possible sans LLM).

3. **3 allers-retours de test réel sur `set_ton_personnel.py`, chacun
   ayant révélé un vrai problème** :
   - Citations verbatim + dérive vers des stéréotypes culturels
     contemporains (métaphore de machette/soldat) — consignes
     anti-répétition et anti-stéréotype ajoutées, avec un principe
     clair : 2098 a eu 70 ans pour évoluer différemment de 2026, ne
     jamais présumer qu'une origine culturelle implique un trait de
     caractère.
   - Bug réel trouvé dans le garde-fou anti-guillemets (ne détectait
     pas les guillemets simples ASCII, confondus avec les apostrophes
     normales du français) — corrigé avec un motif de paire stricte.
   - La consigne "25 mots max" en prose seule n'a pas suffi (~42 mots
     obtenus) — double verrou ajouté (`max_tokens` réduit + validation
     explicite avec retry).
   - **Confirmé sur les 3 points simultanément** après les correctifs
     cumulés.

4. **Piste de suivi notée, pas traitée** : David s'interroge sur la
   fiabilité des métaphores littéraires pour un LLM par rapport à des
   descripteurs directifs concrets (sarcastique, sec, confrontant...).
   Reporté à une prochaine session.

## Fichiers livrés aujourd'hui

- `fix_doublons_journalistes.py` (nouveau, avec les 2 correctifs de
  robustesse cumulés)
- `set_ton_personnel.py` (nouveau, avec les 4 correctifs de consigne
  cumulés : anti-répétition, anti-stéréotype, anti-violence, longueur)
- `prompt_builder.py` (mécanisme `ton_personnel` dans
  `get_journal_profile()`/`build_system_prompt()`, cumulé avec tout le
  reste de la session)

Aucun changement GUI aujourd'hui — les deux nouveaux outils sont
CLI uniquement pour l'instant, pas d'intégration `scripts_config.json`.

## Point de reprise exact pour la prochaine session

1. **Piste métaphores vs. descripteurs directs** (voir ci-dessus) — à
   tester empiriquement ou à retravailler la consigne de
   `set_ton_personnel.py`.
2. **`ton_personnel` jamais utilisé en pratique au-delà du test** —
   aucune autre personne du vault n'a ce champ rempli pour l'instant.
   `--all-manquants` jamais lancé sur une zone entière.
3. **Intégration GUI pour `set_ton_personnel.py`** — pas commencée,
   CLI uniquement pour l'instant.
4. Reste de P21 (hérité des jours précédents, toujours ouvert) :
   nouveau type d'entité `orateur` dans le pipeline principal, outil de
   création d'orateurs par LLM, test du mode `mixte` en conditions
   réelles, signature résiduelle en fin d'article oral.

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
- `HANDOFF_29_AOUT.md` (ce fichier) — nouveau, à ajouter au Project,
  en complément de `HANDOFF_25_AOUT.md`/`HANDOFF_26_AOUT.md` pour le
  contexte complet de P21.
