# Handoff — 29 août 2026

Suite de la session P21 (voir `HANDOFF_25_AOUT.md` et `HANDOFF_26_AOUT.md`
pour le contexte complet du chantier). Fusion des deux parties de la
journée (matin : clôture point 10 + `ton_personnel` ; après-midi :
outillage orateurs P21 + rationalisation des documents de référence).

## Fait

- **Point 10 du backlog clos** — 53 doublons de nom complet entre
  journalistes `pro_pouvoir`/`opposition` corrigés via nouvel outil
  `fix_doublons_journalistes.py` (renommage semi-automatisé LLM,
  toujours côté opposition, validation anti-collision, sauvegarde
  horodatée). 2 bugs trouvés/corrigés en marge (retry ne couvrait pas
  les échecs de parsing JSON ; guillemets ASCII cassant le JSON
  strict). 53/53 réussis en 2 passes.
- **Nouveau chantier `ton_personnel`** — nuance de style personnelle
  par journaliste/orateur, en complément (jamais en remplacement) du
  ton de zone. Champ unifié. Nouvel outil `set_ton_personnel.py`.
  3 allers-retours de test réel, chacun ayant révélé un vrai problème
  (citations verbatim + stéréotypes culturels, garde-fou anti-guillemets
  incomplet, longueur non maîtrisée par la seule consigne) — tous
  corrigés, confirmé sur les 3 points simultanément.
- **Piste métaphores vs. descripteurs directs — mise de côté par
  David.** Protocole de test empirique conçu mais jamais exécuté ;
  `set_ton_personnel.py` jugé suffisant tel quel pour le moment.
- **Nouvel outil `inject_orateur_custom.py`** — contrepartie de
  `inject_journaliste_custom.py` : mode manuel, mode auto (effectif
  minimum 2 par zone déjà oral/mixte, `--scenario` toujours requis,
  jamais de `--all` multi-scénarios), et **mode `convertir`** (bascule
  `type_diffusion` + crée les orateur·rices manquant·es sur une liste
  explicite de zones — jamais un balayage automatique). GUI complet :
  entrée "Ajouter des orateurs", mode convertir avec multi-select
  dynamique (`zones_candidates_oral`/`dynamic_multi_select`, aucune
  modification `app.js` nécessaire). **Testé et validé en conditions
  réelles.**
- **`--avec-ton-personnel`** ajouté aux deux outils de création
  (journaliste et orateur), strictement mode manuel — enchaîne
  `set_ton_personnel.py` juste après la création.
- **P21 — mode `mixte` testé en conditions réelles** (6 articles,
  tirage confirmé non figé, plafond `MOTS_MAX_ORAL` respecté,
  `STYLE_ORAL` très bien suivi — call-and-response réussi, clôture en
  question ouverte). **Considéré validé.**
- **Backlog restructuré** : `BACKLOG_MASTER_9_AOUT.md` remplacé par
  `BACKLOG_ACTIF.md` (Parties 1+3, à uploader chaque session) +
  `BACKLOG_ARCHIVE.md` (Partie 4 + historique, au besoin seulement).
- **Manuel utilisateur restructuré et mis à jour** : même principe —
  `USER_MANUAL_COMPLET.md` allégé à la référence pure (§0-§7, ~2100
  lignes contre ~3960), les ~2000 lignes d'addenda chronologiques
  déplacées vers `USER_MANUAL_HISTORIQUE.md` (au besoin seulement).
  Nouvelle section **§2quater — Pipeline rédaction** consolidant en
  entrées de référence structurées ce qui était jusqu'ici éparpillé en
  addenda : `audit_couverture_journalistes.py`,
  `propose_couverture_journalistes.py`, `inject_journaliste_custom.py`,
  `inject_orateur_custom.py`, `set_ton_personnel.py`,
  `fix_doublons_journalistes.py`, mécanisme `type_diffusion`/`STYLE_ORAL`.
  Intégrité vérifiée (diff programmatique : aucun contenu perdu dans
  le découpage).
- **`TEMPLATE_HANDOFF.md` créé** — ce document utilise ce format.

## Bugs trouvés/corrigés

- `fix_doublons_journalistes.py` : retry ne couvrait que les
  collisions de nom, jamais les échecs de parsing JSON ; guillemets
  ASCII internes cassant le JSON strict.
- `set_ton_personnel.py` : garde-fou anti-guillemets ne détectait pas
  les guillemets simples ASCII (confondus avec apostrophes normales du
  français) — corrigé avec un motif de paire stricte.
- `inject_journaliste_custom.py` (bug latent du 23 août, jamais
  rencontré avant) : le LLM peut inventer des libellés de thématiques
  hors de `THEMATIQUES_CONNUES`, vidant silencieusement la liste et
  faisant échouer l'outil sans retry. Corrigé par double verrou
  (consigne renforcée + retry technique).
- `inject_orateur_custom.py` : `communautes_desservies` générées en
  phrases narratives de 16+ mots au lieu de locutions courtes du vault.
  Corrigé par double verrou (consigne ancrée sur exemples réels + retry
  si un item dépasse 9 mots).
- `inject_orateur_custom.py` mode auto : message de résumé ambigu sur
  "0 création" — corrigé, les deux causes possibles distinguées
  explicitement.

## Décisions actées

- `ton_personnel` jamais couplé automatiquement à la création en mode
  auto (risque de dérive en volume sans relecture individuelle) —
  disponible uniquement en mode manuel, sur les deux outils.
- Mode auto orateurs : `--scenario` toujours requis, jamais de `--all`
  multi-scénarios — les orateurs restent opt-in par zone.
- Conversion de zones en oral/mixte jamais automatisée en aveugle —
  toujours une liste explicite choisie par David (mode `convertir` +
  GUI multi-select dynamique).
- Signature formatée résiduelle en tête/fin d'article oral (malgré la
  consigne `STYLE_ORAL`) : **acceptable, pas de correctif prévu.**
- Documentation : narratif détaillé désormais réservé aux fichiers
  `_HISTORIQUE`/`_ARCHIVE`, les fichiers actifs restent des références
  concises rechargées chaque session.

## Reste à faire (point de reprise)

- **P21 potentiellement clôturable** : les 4 points restants du
  backlog (entité orateur, outil de création LLM, test mode mixte
  réel, signature résiduelle) sont tous traités ou actés comme
  acceptables aujourd'hui. À confirmer et déplacer en archive à la
  prochaine session si rien d'autre ne remonte.
- `ton_personnel` (hors création) : `--all-manquants` jamais lancé sur
  une zone entière ; intégration GUI de `set_ton_personnel.py`
  lui-même (l'outil autonome, pas le flag `--avec-ton-personnel`) pas
  commencée.
- **Correction de contenu backlog toujours en suspens** (identifiée en
  tout début de session, jamais appliquée aux fichiers) : l'entrée
  `ton_personnel` en Partie 4/archive devrait être scindée — le
  mécanisme cœur est clos, mais le reliquat ci-dessus doit apparaître
  en Partie 1/actif. Nouveau point ⚪ "métaphores vs. descripteurs
  directs" à ajouter au passage (texte déjà rédigé, jamais collé dans
  les fichiers).

## Fichiers livrés/modifiés

- `fix_doublons_journalistes.py` (nouveau)
- `set_ton_personnel.py` (nouveau)
- `inject_orateur_custom.py` (nouveau — 3 modes : manuel/auto/convertir)
- `inject_journaliste_custom.py` (modifié — `--avec-ton-personnel`, bug
  thématiques corrigé)
- `prompt_builder.py` (modifié — mécanisme `ton_personnel`)
- `app.py` (modifié — `_zones_candidates_oral()`, branchement
  `get_slugs()`)
- `scripts_config.json` (modifié — entrée orateurs, mode convertir,
  `--avec-ton-personnel` sur les deux outils de création)
- `BACKLOG_ACTIF.md` / `BACKLOG_ARCHIVE.md` (nouveaux, remplacent
  `BACKLOG_MASTER_9_AOUT.md`)
- `USER_MANUAL_COMPLET.md` / `USER_MANUAL_HISTORIQUE.md` (restructurés,
  remplacent l'ancien `USER_MANUAL_COMPLET.md` monolithique)
- `TEMPLATE_HANDOFF.md` (nouveau)

## Non traité aujourd'hui (hérité)

- Point ⚪ métaphores vs. descripteurs directs (`ton_personnel`) — voir
  Reste à faire ci-dessus pour le texte à ajouter au backlog.
- `chapo`/`tags`/`image_prompt` vides (~7% des cas).
- Choix du service externe de génération d'image (P20).
- P17, Bug #27, renommage YAML génériques, troncatures JSON, GUI
  `promote_ville.py`, P14 — tous en observation, aucun changement.

## Fichiers à ré-uploader en début de prochaine session

- `BACKLOG_ACTIF.md` — remplace `BACKLOG_MASTER_9_AOUT.md` dans le
  Project.
- `USER_MANUAL_COMPLET.md` — remplace l'ancienne version dans le
  Project.
- `HANDOFF_29_AOUT.md` (ce fichier, fusionné) — remplace les deux
  parties précédentes.
- `BACKLOG_ARCHIVE.md`/`USER_MANUAL_HISTORIQUE.md` : seulement si
  besoin de vérifier un chantier clos ou un détail narratif passé.
