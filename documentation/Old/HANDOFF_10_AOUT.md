# HANDOFF — session du 10 août 2026 (à uploader dans le nouveau chat)

*Session entièrement consacrée au chantier ouvert le 9 août ("Dérive du
LLM sur la longueur réelle des articles", 70,4% d'incohérence mesurée).
Un seul fil conducteur, mais qui s'est ramifié en 9 correctifs distincts
au fil des tests réels et des remarques de David sur les articles
produits : renforcement du prompt (insuffisant seul), transmission de la
date fictive au LLM, signature toujours instruite (2 itérations), fix
d'accent dans les noms de fichiers, retry automatique borné, et deux
bugs annexes découverts en creusant (dossier de sortie ignoré, deux
outils de lecture rendus aveugles par ce dernier correctif). Session
directement enchaînée sur `HANDOFF_9_AOUT.md`.*

---

## 1. Diagnostic initial

Lecture du code réel (`prompt_builder.py`, `api.py`, `llm_client.py`) —
pas de nouvelle donnée vault, tout le diagnostic vient de la lecture de
`generator/` fourni en session (archive `generator.zip`). Deux causes
structurelles trouvées :

1. La consigne de longueur n'apparaissait qu'une seule fois dans
   `build_journalistic_brief()`, tôt dans le prompt, noyée parmi une
   dizaine d'autres lignes de métadonnées. Le bloc "Contraintes
   impératives" — la seule liste de règles explicitement qualifiées de
   strictes, juste avant que le LLM écrive — ne la reprenait jamais.
2. `generate_article()` (`api.py`) sauvegardait l'article du LLM tel
   quel, sans aucune vérification de longueur ni mécanisme de retry —
   contrairement à ce que supposait le point ouvert le 9 août ("comme il
   en existe déjà pour d'autres champs" — vrai pour les champs
   structurés JSON des entités/instances, faux pour les articles en
   texte libre).

---

## 2. Correctif 1 — renforcement du prompt (testé insuffisant seul)

**Fichier : `prompt_builder.py`, `build_journalistic_brief()`.** La
consigne de longueur est répétée dans le bloc "Contraintes impératives",
reformulée en contrainte dure ("ne t'arrête pas avant la borne basse, ne
dépasse pas la borne haute — contrainte dure, pas une indication
approximative").

**Test réel (David, batch de 18 articles via `generate_series.py`,
scénario `policy_reform`)** : taux d'incohérence Cas A isolé sur ce
batch = **94,4%**, pire que la référence du 9 août (70,4%), avec un
biais net vers le dépassement (17/17 articles incohérents étaient trop
longs, aucun trop court — certains dépassements de 60%+ au-dessus de la
borne haute). Conclusion actée avec David : le renforcement seul ne
suffit pas, le LLM ne semble pas "oublier" la consigne mais la traite
comme secondaire. Le correctif reste en place (inoffensif), mais le vrai
levier est le retry (§6).

---

## 3. Trois remarques de David sur le batch de test — trois bugs distincts

En observant le batch de 18 articles, David a signalé trois problèmes
indépendants du sujet longueur :

1. La date dans le nom de fichier ne correspondait jamais à la date
   réellement écrite dans l'article — et presque tous les articles
   convergeaient vers la même date ("12 octobre 2098").
2. Certains articles n'avaient aucune signature en bas, d'autres avaient
   une signature avec le nom du journal, d'autres sans — incohérent.
3. Faute d'orthographe systématique dans les noms de fichiers, ex.
   `fvrier` au lieu de `février`.

Diagnostic de chacun ci-dessous (§4, §5, §7).

---

## 4. Correctif 2 — date fictive jamais transmise au LLM

**Root cause** : `generate.py`/`generate_series.py` calculent bien une
date différente par article (liste `DATES_2098`, pour espacer une série
dans le temps), mais cette date ne servait **qu'au nom de fichier**
(`build_article_filename()`) — jamais lue dans
`build_journalistic_brief()`, qui donnait seulement au LLM l'instruction
*"une date crédible en 2098"*, totalement libre. La convergence
observée vers une date quasi unique est cohérente avec ce type de
consigne trop ouverte.

**Fichier : `prompt_builder.py`, `build_journalistic_brief()`.** La date
est transmise explicitement quand elle est fournie, avec instruction de
la reprendre telle quelle — reprise à la fois dans la consigne
principale et dans le bloc "Contraintes impératives" (même schéma de
renforcement que la longueur, §2).

**Testé en conditions réelles sur le 2e batch (12 articles, voir §9) :
12/12 corrects.**

---

## 5. Correctif 3 — signature (2 itérations)

**Root cause** : `get_journal_profile()` a 3 chemins de résolution du
profil éditorial (édition locale zone > réseau global > profil
hardcodé). Seul le premier peuple la clé `journaliste`. Dans
`build_system_prompt()`, si cette clé est vide, l'instruction de
signature est **entièrement absente du prompt** — pas juste vide, elle
n'existe pas — laissant le LLM libre de signer ou non. D'où les
articles sans signature. Pour ceux qui avaient une instruction (chemin
1), elle ne précisait que le nom, jamais si le nom du journal devait
suivre — d'où l'incohérence de format.

**Itération 1** : une instruction de signature est désormais toujours
donnée (`build_system_prompt()`), au format unifié `"Nom — Journal"` —
nom curaté si disponible, sinon inventé par le LLM au même format.

**Test réel sur le 2e batch (12 articles)** : 12/12 signés (contre
présence aléatoire avant). Mais lecture détaillée des 12 fichiers a
révélé deux problèmes résiduels : position incohérente (parfois sous la
date en haut, parfois en fin d'article), et un doublon (article du 5
avril — signature répétée aux deux endroits, malgré l'instruction "une
seule fois").

**Itération 2** (même jour, après clarification avec David des usages
réels de la presse en ligne — la signature/byline se met en haut, sous
le titre et la date ; la position "en bas" est plutôt réservée aux
tribunes/éditoriaux) : position fixée explicitement en haut, "une seule
fois" reformulé en majuscules avec interdiction stricte de répétition,
repris à la fois dans `build_system_prompt()` et dans le bloc
"Contraintes impératives" de `build_journalistic_brief()`.

**Itération 2 non testée en conditions réelles** — codée en toute fin de
session, aucun batch généré depuis. Point de suivi ouvert (backlog
Partie 1 point 2).

---

## 6. Correctif 4 — retry automatique borné (le vrai levier sur la longueur)

**Décision actée avec David**, en réponse directe à l'échec du
renforcement seul (§2) : puisque répéter la consigne ne suffit pas, un
mécanisme de re-génération automatique complète le dispositif — mais
strictement borné, pour ne pas doubler indéfiniment le temps/coût de
génération (question explicite de David sur ce point avant validation de
l'approche).

**Règle retenue** (seuil unique, pas de palier intermédiaire malgré la
formulation initiale "±20%/±40%" de David — clarifié en session) : écart
> 40% par rapport à la borne dépassée (haute ou basse) → **un seul
retry**, jamais de boucle. En dessous, l'article est accepté tel quel.

**Mécanique du retry** : pas un découpage mécanique du texte — le
premier essai est jeté, le LLM réécrit l'article en entier depuis le
titre, avec un message supplémentaire indiquant l'écart mesuré au
premier essai en chiffres exacts (ex. *"Ta précédente tentative faisait
1300 mots, soit 44% de trop par rapport à la borne haute (900 mots).
Coupe le texte pour rester entre 600 et 900 mots cette fois."*).

**Fichier : `api.py`.** Nouvelles fonctions : `_parse_longueur_bornes()`,
`_count_words()`, `_deviation_ratio()`, `_retry_with_length_feedback()`.
`generate_article()` orchestre validation + retry conditionnel.
Nouveaux champs frontmatter `mots_reels` (comptage final) et
`retry_longueur` (oui/non) pour la traçabilité, sans dépendre de l'audit
externe pour vérifier après coup.

**Testé en conditions réelles sur le 2e batch (12 articles)** : retry
déclenché 3 fois (3 janvier, 2 février, 10 mai) — les 3 résultats
finaux dans la plage ou nettement rapprochés. Sur les 9 articles non
retentés, écart recalculé manuellement pour chacun : aucun ne dépassait
40% (le plus proche à 36,9%) — pas de faux négatif observé. Échantillon
encore petit (12 articles, 3 retries) — validation à plus grande échelle
en suivi (backlog Partie 1 point 1).

---

## 7. Correctif 5 — accent supprimé dans le slug de date du nom de fichier

**Root cause (`api.py`, `build_article_filename()`)** : la regex de
nettoyage (`re.sub(r"[^a-z0-9]", "", date_slug)`) ne matche que les
lettres non accentuées — tout caractère accentué (`é`, `û`...) est
silencieusement supprimé, pas translittéré. `"février"` → `"fvrier"`.

**Correctif** : passage par `unicodedata.normalize("NFKD", ...)` puis
encodage ascii avant le filtrage — sépare la lettre de sa marque
d'accent, ne supprime que celle-ci. `"février"` → `"fevrier"`.

**Testé en conditions réelles sur le 2e batch : confirmé** (`2fevrier2098`,
`19fevrier2098`, `5avril2098`...).

---

## 8. Deux bugs annexes trouvés en marge — dossier de sortie et scan non récursif

**Découverte de David** entre les deux batchs de test : les articles de
la série (`generate_series.py`) atterrissaient tous à la racine de
`articles/`, alors que le script construit un chemin `articles/
{scenario}/` et y écrit son `_index.md`.

**Root cause (`api.py`, `save_article()`)** : le dossier de sortie était
figé en dur sur `ARTICLES_DIR` (la racine), sans jamais lire
`config["output"]["dossier"]` — que `generate_series.py` et
`generate_manual.py` construisaient pourtant correctement.

**Correctif** : `save_article()` lit désormais ce champ de config.
Vérifié sur les 3 cas de figure possibles (série → sous-dossier ; unité
→ racine, comportement historique inchangé ; config sans bloc `output` →
repli propre sur la racine).

**Effet de bord anticipé avant qu'il ne cause un problème en aval** :
`trace_injection.py` et `audit_longueur_articles.py` scannent `articles/`
à plat (`os.listdir`/`glob` non récursif). Sans correction simultanée,
ils seraient devenus aveugles à tout article de série/manuel une fois
réellement rangé en sous-dossier — un nouveau bug de traçabilité pire
que l'original. Corrigés en même temps : `trace_injection.py`
(`glob("**/*.md")`), `audit_longueur_articles.py` (`os.walk`, affichage
par chemin relatif, `_index.md` explicitement ignoré).

**Testé** : `save_article()` et `audit_longueur_articles.py` en
conditions réelles (2e batch, 43 fichiers retrouvés par l'audit, racine
+ sous-dossier `policy_reform/`). `trace_injection.py` testé en
isolation seulement (logique du scan vérifiée), pas en conditions
réelles faute d'entités disponibles pour un test complet en session.

---

## 9. Deux batchs de test réels

**Batch 1** (18 articles, `generate_series.py`, `policy_reform`,
avant les correctifs date/signature/accent/dossier) — a servi à évaluer
le renforcement du prompt seul (§2, résultat négatif) et a déclenché la
découverte du bug de dossier de sortie (§8) quand David a signalé que
les articles étaient à la racine plutôt qu'en sous-dossier.

**Batch 2** (12 articles, même scénario, après tous les correctifs sauf
la 2e itération signature) — analysé fichier par fichier par Claude
(upload `policy_reform.zip`) : date 12/12 correcte (§4), signature
présente 12/12 mais position/duplication à corriger (§5, a mené à
l'itération 2), retry déclenché 3/12 fois avec succès (§6), accent
confirmé corrigé (§7), dossier de sortie confirmé correct (§8).

**Nettoyage post-test** : découverte en fin de session d'un **3e fichier
d'état non anticipé**, `state/event_relevance_usage.json` (rotation à
mémoire des événements custom, mécanisme du 2 août 2026 — simplement
absent de l'inventaire initial donné par Claude en session). N'étant pas
suivi par Git au moment du test, `git checkout` ne l'a pas restauré — a
dû être supprimé à la main. Gap de documentation corrigé dans
`USER_MANUAL_COMPLET.md` (§0, §2) et dans le protocole de test qui y est
documenté (§2ter).

---

## 10. Fichiers livrés cette session

**Scripts modifiés** : `prompt_builder.py` (renforcement longueur, date
fictive, signature ×2 itérations), `api.py` (accent, retry automatique,
dossier de sortie), `trace_injection.py` (scan récursif),
`audit_longueur_articles.py` (scan récursif, `_index.md` ignoré).

**Documentation** : `USER_MANUAL_COMPLET.md` (nouvelle section §2ter
complète — voir §11 ci-dessous), `BACKLOG_MASTER_9_AOUT.md` (mis à jour
en place : ancien point 1 de la Partie 1 déplacé en Partie 4 comme clos,
7 nouvelles lignes ajoutées à la table des chantiers clos, 2 nouveaux
points de suivi ouverts en Partie 1, renumérotation complète de la
Partie 1), ce handoff.

Tous les scripts modifiés testés (syntaxe `ast.parse`, tests unitaires
isolés par mocks pour la logique du retry et le fix de dossier), et pour
la plupart en conditions réelles sur deux batchs de test via David — sauf
la 2e itération du fix signature et `trace_injection.py`, encore en
attente d'un test réel (voir backlog Partie 1 points 1 et 2).

---

## 11. Documentation mise à jour cette session

- **`USER_MANUAL_COMPLET.md`** — nouvelle section **§2ter** complète
  ("Chantier longueur/qualité des articles générés"), volontairement
  détaillée et sans jargon pour rester compréhensible hors contexte de
  la session. Couvre les 9 points du diagnostic aux correctifs, plus un
  protocole de test réutilisable pour tout futur changement touchant la
  génération d'articles. Entrées `prompt_builder.py`/`api.py` (§1),
  `generate_series.py`, `trace_injection.py`, `audit_longueur_
  articles.py` (§2, §5) mises à jour pour pointer vers §2ter. Inventaire
  des fichiers `state/` corrigé (§0, §2) — `instance_usage.json` et
  `event_relevance_usage.json` manquaient.
- **`BACKLOG_MASTER_9_AOUT.md`** — mis à jour en place (pas recréé).
  Chantier "Dérive du LLM sur la longueur réelle des articles" déplacé
  en Partie 4 (clos), avec renvoi vers les 2 points de suivi restés
  ouverts. 7 nouvelles lignes dans la table des chantiers clos (longueur,
  date, signature, accent, dossier de sortie, scan récursif, gap
  `event_relevance_usage.json`). Partie 1 renumérotée (1→11), 2 nouveaux
  points de suivi en tête de liste (🟡 validation retry à plus grande
  échelle, 🟡 validation réelle du fix signature itération 2). Note
  finale mise à jour : plus aucun 🔴 en attente.

---

## 12. Point de reprise suggéré pour la prochaine session

Le backlog maître (`BACKLOG_MASTER_9_AOUT.md`, Partie 1) est la
référence — dans l'ordre de priorité actuel, tout en 🟡 (plus aucun 🔴) :

1. **Validation à plus grande échelle du retry sur la longueur** — pas
   urgent (aucun signe d'échec), à faire au prochain batch de volume
   généré de toute façon.
2. **Validation réelle du fix signature itération 2** — position en
   haut, une seule occurrence. Aucun batch généré depuis ce correctif,
   à vérifier au prochain test.
3. **Test navigateur des entrées GUI modifiées** — scope large, jamais
   fait, suggestion d'une session dédiée "clic à travers tout le GUI".
4. **Même diagnostic `annee_debut`/`ancrage_reel` sur les événements** —
   jamais exploré.
5. Reste du backlog : voir `BACKLOG_MASTER_9_AOUT.md` Partie 1, points 5
   à 11 — dimension temporelle génération auto, documentation
   `generate_instances.py` à corriger dans le manuel, doublon d'entité
   `arctic_passage_authority`/`autorite_passage_arctique`, nettoyage
   `test_durcissement_policy_reform`, 4 reliquats du 7 août, renommage
   YAML génériques.

**Discipline à maintenir** : `BACKLOG_MASTER_9_AOUT.md` doit continuer
d'être **mis à jour en place**, jamais recréé sous un nouveau nom daté —
cette session l'a fait correctement malgré le volume important de
changements (9 correctifs, 2 batchs de test).

**Rappel pratique pour tout futur test de génération réelle** : vérifier
`git status state/` avant ET après (pas seulement les 2 fichiers connus
`instance_usage.json`/`trajectory_usage.json` — un 3e, `event_relevance_
usage.json`, existait déjà sans être documenté ; un futur mécanisme de
rotation pourrait en ajouter un 4e sans prévenir). Protocole complet
documenté dans `USER_MANUAL_COMPLET.md` §2ter.
