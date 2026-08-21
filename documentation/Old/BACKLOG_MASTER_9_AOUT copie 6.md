# Backlog maître — Ourrassol 2098
*Consolidé le 9 août 2026, à partir de l'ensemble des handoffs/backlogs du
1er août au 9 août 2026. Mis à jour en place le 10 août 2026 (chantier
longueur/qualité des articles générés), le 11 août 2026 en deux temps :
clarté des descriptifs GUI + validation navigateur (session du matin — voir
`HANDOFF_11_AOUT.md`), puis correctifs de bugs réels trouvés en testant les
3 dernières entrées GUI + clôture définitive du chantier de validation
navigateur (session du soir — voir `HANDOFF_11_AOUT_SOIR.md`), et le
12 août 2026 (validation réelle du correctif signature, diagnostic
`annee_debut`/`ancrage_reel` sur les événements + nouveau chantier de
cohérence événements custom — voir `HANDOFF_12_AOUT.md`), et le
13 août 2026 (chantier "dimension temporelle pour la génération
automatique" codé et validé en dry-run réel, confirmation en injection
réelle du chantier de cohérence événements custom du 12 août, bug
`evenement_cle` trouvé et corrigé — voir `HANDOFF_13_AOUT.md`), et le
14 août 2026 (session dense : recherche exhaustive dans l'archive complète
ayant retrouvé 4 chantiers tombés du radar sans clôture formelle, fusion du
doublon d'entité Arctic, nettoyage des wikilinks `test_durcissement`,
clôture des 4 reliquats du 7 août, correctif de la cause racine de
l'encodage portugais cassé dans les slugs (+ migration de 2 cas réels sur
le vault), filtre dur `acteurs_hint_count` enfin appliqué, déduplication de
`detect_registre_leakage()`, correctif du refresh GUI `--force` sur le
panneau localisation (3 causes, 3 fichiers), et identification d'un
chantier substantiel non résolu (`forces_attractives`/`forces_repulsives`,
contenu réel du vault jamais exploité par le pipeline) — voir
`HANDOFF_14_AOUT.md`). Remplace tous les documents précédents comme
référence unique. Chaque chantier a un nom stable — à réutiliser tel quel
dans les prochaines sessions pour éviter toute nouvelle divergence de
nommage.*

---

# PARTIE 1 — CHANTIERS OUVERTS (à traiter)

## 🟡 1. Validation à plus grande échelle du retry sur la longueur des articles
**Nouveau, 10 août.** Le mécanisme de retry automatique (voir Partie 4,
chantier "Dérive du LLM sur la longueur réelle des articles" pour le
détail complet, et `USER_MANUAL_COMPLET.md` §2ter) a été testé sur un
seul batch réel de 12 articles : 3 retries déclenchés, tous améliorés
(2 ramenés dans la plage ou très proches, 1 significativement rapproché).
Aucun faux négatif observé (aucun des 9 articles non retentés ne
dépassait le seuil de 40%). **Mais l'échantillon reste petit**, et la
génération tourne à température 1.0 (forte variance) — un batch plus
large (30-50 articles, plusieurs scénarios) donnerait une mesure
statistiquement plus fiable du taux de réussite réel du mécanisme.
Pas urgent (le mécanisme fonctionne, aucun signe d'échec) — à faire
quand un prochain batch de volume sera de toute façon généré pour
d'autres raisons, plutôt que de provoquer un test dédié.

---

## 🟢 2. `forces_attractives`/`forces_repulsives` — décision de conception à
prendre avant tout code
**Nouveau, 14 août — chantier prioritaire pour la prochaine session,
explicitement demandé par David.** Trouvé en Partie 2, escaladé après
vérification du vault réel. Le docstring de `build_variables_context()`
(`prompt_builder.py`) promet ces champs "si disponibles", et le code ne
les lit nulle part — mais contrairement à l'hypothèse initiale ("juste
une promesse jamais tenue"), le contenu **existe réellement** sur les
**12 fiches variables**, sans exception (confirmé par `grep -rl
"forces_attractives\|forces_repulsives" variables/`).

**Complication** : ce ne sont pas des clés YAML de frontmatter (contrairement
à `simulation`, `constrained_variables`, déjà vérifiés) — c'est du texte
en prose Markdown dans le **corps** de chaque fiche, sous deux titres
`##` différents avec un contenu qui se recoupe partiellement sans être
identique :
- `## 3. Dynamique interne` → `**forces_attractives**` / `**forces_
  repulsives**` (snake_case)
- `## 4. Structure causale` → `**Forces attractives**` / `**Forces
  répulsives**` (majuscules, accentué)

Confirmé par grep qu'aucune des deux sections n'est parsée nulle part
dans le pipeline.

**Portée du chantier** :
1. **David doit d'abord relire les 12 fiches** et trancher quelle
   section (3, 4, ou fusion des deux) sert de source de vérité — décision
   de contenu, pas de code.
2. Nouveau parseur de corps Markdown dans `loader.py` (différent des
   champs frontmatter déjà câblés — nécessite un scan par regex des
   sections `##`, pas un simple `fm.get(...)`).
3. Câblage dans `build_variables_context()` (`prompt_builder.py`) pour
   que le résultat atteigne enfin le prompt envoyé au LLM.

Détail complet du diagnostic : `HANDOFF_14_AOUT.md` §10.

---

## ⚪ 3. P17 — retester la fiabilité `mistral-small` sur choix contraint
**Retrouvé le 14 août** via recherche exhaustive dans l'archive (décidé
le 11 juillet, jamais fait, disparu du backlog sans clôture formelle
après la consolidation du 2 août). Le bug #26 avait montré que la
contamination culturelle observée les 6 et 11 juillet était en réalité
causée par un bug de résolution de zone, reproduit à l'identique sur
`mistral-small` **et** `mistral-large` — pas une limite de fiabilité
modèle comme diagnostiqué initialement. Reste à vérifier si un vrai
problème de fiabilité subsiste sur `mistral-small` une fois cette cause
de code éliminée : relancer une génération d'article sur `mistral-small`
(override manuel `LLM_PROVIDER=mistral LLM_MODEL=mistral-small-latest`)
et comparer au résultat obtenu sur `mistral-large`. **David a choisi de
le garder pour plus tard, non traité le 14 août.**

---

## ⚪ 4. Bug #27 — plausibilité logistique inter-zones
**Retrouvé le 14 août** via recherche exhaustive dans l'archive (noté le
11 juillet, jamais repris). Incohérence détectée sur un article test : un
personnage du Pacte Amazônia Viva (Amazonie) décrit comme arrivant par
un moyen de transport purement local (pirogue depuis Kisangani, Congo),
sans mention de la traversée intercontinentale attendue. Décision du 11
juillet : observer si ça se reproduit avant de renforcer
`build_system_prompt()` (`prompt_builder.py`) avec une consigne dédiée à
la plausibilité des trajets inter-zones — observation qui n'a en réalité
jamais eu lieu, personne n'ayant recherché activement le symptôme depuis.
**David veut faire une analyse d'articles pour vérifier la récurrence
avant de décider d'un correctif** — pas de correctif préventif sans
données. Non traité le 14 août, gardé pour plus tard.

---

## ⚪ 5. Renommage des YAML génériques par dossier
**Décision reportée une nouvelle fois le 14 août** (en pause depuis fin
juillet). `queue.yaml`/`processed.yaml`/`needs_review.yaml` répétés à
l'identique dans `entites_custom/`, `evenements_custom/`,
`signaux_custom/` — pas de collision technique (dossiers distincts),
juste une ambiguïté visuelle. Coût de migration identifié si un jour
tranché en faveur du renommage : constantes `QUEUE_PATH` dans 3 scripts,
entrées `scripts_config.json`, documentation (dont les `QUEUE_TEMPLATE`
eux-mêmes). Aucune urgence identifiée à ce jour.

---

## ⚪ 6. Troncatures JSON occasionnelles lors de la génération d'instances
(Mistral)
**Toujours en observation, gardé pour plus tard le 14 août.** Deux échecs
`"Aucun JSON exploitable trouvé dans la réponse"` observés le 11 août
lors de tests réels (`generate_instances`/`create_entities`) — le modèle
Mistral s'arrête en plein milieu du JSON. Diagnostic déjà fait : pas un
problème de plafond de tokens (`INSTANCE_MAX_TOKENS = 4000`, sorties bien
en dessous), aléa côté API, même famille que le timeout 503 vu le même
jour sur `extract_localisation.py`. Décision : point de vigilance, pas de
correctif codé tant que le taux reste faible (2/~35 générations observées)
— le mécanisme de résilience existant gère déjà correctement ce cas. À
surveiller : si le symptôme devient fréquent sur un futur batch de
volume, envisager un retry automatique dédié (distinct de celui déjà en
place sur la longueur des articles).

---

## ⚪ 7. "Les Veilleurs des Nappes Phréatiques" — idée rejetée en attente
de décision
**Décision non tranchée en fin de session le 14 août**, remonté depuis
la Partie 2 (ce n'est plus un simple point mineur "sans action requise"
— une vraie décision reste à prendre). `entites_custom/needs_review.yaml`
contient une idée rejetée le 11 août (`category: mouvement` — valeur
hors liste, hallucinée par le LLM auto-suggest malgré la contrainte
explicite du prompt). Le garde-fou de validation a fonctionné comme
prévu, rien à corriger côté code. **Question à trancher en tout début de
prochaine session** : corriger manuellement le champ `category` vers une
valeur valide et créer l'entité, ou laisser tomber définitivement cette
idée ?

---

## ⚪ 8. Chantiers de fond, scopés mais non codés (pause longue durée)
- **P20 — enrichissement frontmatter pour publication web future** :
  scoping complet fait (12 juillet), rien codé. Champs prévus : `slug`,
  `chapo`/`excerpt`, `image_prompt`, `a_une_photo`, `image_principale`,
  `image_alt`, `image_credit`, `tags`, `journaliste_slug`, `date_
  publication`, `articles_lies`, `zone_principale`.
- **P21 — journaux oraux, orateurs itinérants** : scoping complet fait
  (12 juillet), rien codé. Nouveau type d'entité `orateur` (Option B
  décidée), champ `type_diffusion`, registre oral distinct dans
  `prompt_builder.py`.
- **P14 — tier LLM `strict` vers `claude-sonnet-5` en prod** : différé
  sine die sur demande explicite de David (1er août). Pas un oubli, une
  décision — à reconsidérer seulement si David le redemande.

---

# PARTIE 2 — POINTS MINEURS, NON BLOQUANTS (sans action requise)

- `coverage_proposals_reference.yaml` sans `.applied` — anomalie
  repérée, famille legacy, sans impact opérationnel.
- `/api/carte/appliquer_zone_topdown_suspecte` — route dormante, seul
  point d'entrée UI retiré (absorbé par l'onglet Chantiers). Reconfirmé
  le 14 août.
- Champ `type` des zones géographiques (`zone_sinistree` etc.) — jamais
  utilisé dans le prompt, distinct de `statut` qui l'est. Reconfirmé le
  14 août.
- Bloc `simulation` sur les fiches variables — chargé par `loader.py`,
  jamais utilisé par `prompt_builder.py`. Probablement du monitoring
  interne, pas de la narration. Reconfirmé le 14 août.
- `constrained_variables` (snapshot) — calculé, jamais affiché dans le
  prompt. Reconfirmé le 14 août.
- `--min-shingle` de `detect_registre_leakage()` (fonction désormais
  partagée, voir Partie 4) fixé en dur à 6 mots — pourrait devenir un
  paramètre CLI si un faux positif/négatif apparaît en usage réel.
- Cas d'échec LLM ponctuel observé une fois (4 août) : confusion entre
  un slug de zone géographique et un slug d'instance sur une fiche —
  résolu par retry, gardé en tête comme motif à surveiller si le même
  symptôme réapparaît (pourrait indiquer que le prompt gagnerait à
  lister explicitement les slugs de zones à ne PAS utiliser).
- **Nouveau, 14 août** : `audit_broken_slugs.py` (voir Partie 4, chantier
  encodage portugais) ne filtre pas `entite_template.md` (le fichier
  gabarit) de son rapport — faux positif mineur et inoffensif si le
  script est réutilisé plus tard, le rapport l'explique déjà clairement
  comme "à vérifier manuellement". À corriger si le script devient
  d'usage fréquent.

---

# PARTIE 3 — RISQUE STRUCTUREL IDENTIFIÉ (pas un bug actif)

**Instances avec `injection.type == "custom"` potentiellement non
sélectionnées parmi les `filtered_instances`** — leurs deltas de
variables sont visibles, mais pas leur description complète. Identifié
le 3 août, jamais rencontré en pratique (le vault semble ne contenir que
des événements custom, pas d'instances custom). Rien à corriger tant que
ça ne se manifeste pas.

---

# PARTIE 4 — CHANTIERS CLOS (référence historique — ne pas rouvrir sans raison)

Regroupés par nom de chantier stable, avec date de clôture, pour éviter
qu'une future session ne les rouvre par erreur faute de contexte.

| Chantier | Clos le | Résumé |
|---|---|---|
| **P8 — 426 fiches `officialise_minimal`** | 27 juin | Traité intégralement, preuve dans les fiches elles-mêmes. |
| **`noeud_mnemos_pannonie`** | 14 juillet | P23, absorbé par `check_origine_reelle_coherence.py`. |
| **P18 — cohérence `routes_dashboard.py`** | 13 juillet | — |
| **P24 étape C** | 1er août | Absorbé par `chantiers_geographie.yaml`. |
| **Onglet GUI "Chantiers"** | 26 juillet → 1er août | Livré et testé en réel ; granularité "appliquer un seul chantier" ajoutée le 1er août. |
| **Bug dashboard (entrée fantôme instances)** | 2 août | `instance_template.md` compté à tort comme 711e instance — corrigé. |
| **Panneau Revue vide** | 2 août | Deux causes cumulées corrigées (`sort_keys=False`, sources `entites_custom`/`signaux_custom` jamais lues). |
| **`trace_injection.py`** | 2 août | Nouvel outil de traçabilité, livré et testé en réel. |
| **Mode "Forcer un élément"** | 2 août | Refonte majeure de `generate.py`, 7 bugs trouvés et corrigés en conditions réelles. |
| **Plafonnement événements/géographie** | 3 août | Testé en conditions réelles, 2 bugs annexes corrigés (badge `[FORCÉ]`, zone manquante). |
| **Revalidation mode Semi-guidé** | 3 août | Les 7 champs du bug §3.7 confirmés appliqués ; bug annexe `metadata["longueur"]` trouvé (→ a mené au chantier "Dérive du LLM sur la longueur réelle des articles" ci-dessous, clos le 10 août). |
| **Audit de complétude snapshot/variables** | 3 août | 4 pertes de contenu narratif trouvées et corrigées. |
| **Test de charge Semi-guidé à 6 entités** | 4 août | 58 948 caractères mesurés, structurellement borné. A débouché sur le chantier alliances/oppositions ci-dessous. |
| **Chantier alliances/oppositions** | 4-5 août | 356→0 fiche vide sur 426, réciprocité automatisée, root cause corrigée à la source (`enrich_minimal.py`), validation durcie partiellement, découverte et correction annexe de 284 fiches sans `statut` (vault à 710/710 cohérent). |
| **146 conflits de réciprocité alliances/oppositions** | 7 août | Règle "opposition prioritaire" implémentée et appliquée, 2 bugs découverts et corrigés (écrasement multi-conflits, rapports jamais réinitialisés), intégrée en continu à `enrich_minimal.py`, GUI mis à jour. |
| **`fix_alliances_oppositions.py` absent du GUI** | 7 août | Résolu par l'intégration GUI du chantier ci-dessus. |
| **Documentation `depends_on`** | 8 août | Fausse alerte — vérifié en détail, le mécanisme était déjà correctement décrit. Rien à corriger. |
| **Chantier `annee_debut`** | 8 août | 477 fiches bloquées à 2026 corrigées, outil de veille construit (`etat_du_monde_reel.md` + export/import), chantier de robustesse `ancrage_reel` mené en parallèle (bande graduée 10 ans), run `--all` confirmé par un passage à vide. |
| **`ancrage_reel` / traçabilité graduée** | 8 août | Ouvert et refermé dans la même session, 5 itérations de test réel. |
| **Statut de `generate_instances.py`** | 9 août | Confirmé **actif**, usage distinct de `create_entities_and_instances.py` (backfill vs création). Voir Partie 1 point 3 (documentation à corriger dans le manuel) pour le suivi resté ouvert. |
| **Factorisation `instance_generation_common.py`** | 9 août | ~20 fonctions dupliquées entre `generate_instances.py` et `create_entities_and_instances.py` unifiées en un seul module. 3 bugs de divergence réels corrigés au passage (`call_claude_json`, `validate_instance`, `MAX_TOKENS`). Détail complet : `USER_MANUAL_COMPLET.md` §1. |
| **Chantier `trajectoire`** | 9 août | Fusion `etat_temporel`+`age_historique` en un axe unique + `est_clandestin` séparé. 710 fiches migrées via `migrate_trajectoire.py` (nouveau script, mécanique, aucun appel LLM), `validate.py` recalibré (bug C4 corrigé au passage), GUI mis à jour (menu `État`/`Clandestin` dans `create_entities`), `audit_etat_temporel_fin.py` adapté. Détail complet : `USER_MANUAL_COMPLET.md` §3bis. |
| **Chantier `annee_fin`** | 9 août | 28 fiches à trajectoire terminale sans date de fin corrigées (`fix_annee_fin_manquant.py`, nouveau script, ancré sur le registre du scénario). 27/28 directement, 1 cas résistant résolu par renforcement du prompt + filet de sécurité de plafonnement automatique ajouté au script. Concentration sur 2041/2061/2057 vérifiée légitime (jalons de rupture réels du registre, pas une convergence artificielle). Vérifié par `audit_etat_temporel_fin.py` (0% d'incohérence) et `validate.py` (0 erreur). |
| **Décision `type_relation_dominante`** | 9 août | Fausse alerte — en réalité déjà décidé et implémenté le 7 août (`prompt_builder.py`, `build_entities_context()`), jamais retiré du backlog dans les sessions suivantes. Affiché en ligne dédiée par entité avec période (`annee_debut`–`annee_fin`) ; garde-fou anti-fabrication confirmé suffisant (consigne générale "ne les contredis pas" du bloc entités, pas de mécanisme dédié nécessaire). |
| **`metadata["longueur"]` réutilisé en aval ?** | 9 août | Vérifié : oui, écrit de façon permanente dans le frontmatter par `api.py` ET `generate_manual.py` (traçabilité), mais jamais relu par aucun script (`trace_injection.py` lit `scenario`/`date_publication`/`titre`, jamais `longueur`) — impact purement cosmétique. **Correction rétroactive abandonnée** : la reconstruction resterait ambiguë (catégories `FORMAT_LONGUEUR` qui se chevauchent) et rien en aval n'en dépend fonctionnellement. Nouvel outil créé pour mesurer sans corriger : `audit_longueur_articles.py` (lecture seule, section GUI Validation) — 3 itérations en session pour arriver à un diagnostic fiable (v1 : bug de correspondance catégorie/plage, 100% faux positifs ; v2 : parsing direct de la plage textuelle, 64,5% mais mélangeait deux causes différentes ; v3 : distingue Cas A [vrai signal] de Cas B [divergence format/longueur]) — chiffre final fiable : **70,4% (19/27 analysables)**, a mené au chantier "Dérive du LLM sur la longueur réelle des articles" ci-dessous. |
| **Bug d'accent `FORMAT_LONGUEUR` (`brève`/`éditorial`/`réflexif`)** | 9 août | Trouvé en creusant le point ci-dessus (les 4 articles `format: brève` retombaient tous sur le filet de secours générique "300 à 500 mots" au lieu de leur vraie plage "200 à 400 mots"). Cause : `FORMAT_LONGUEUR` (`prompt_builder.py`) ne couvrait que les orthographes sans accent, alors que `VALID_FORMATS` (`validate.py`) accepte explicitement les deux orthographes pour `breve`/`brève`, `editorial`/`éditorial`, `reflexif`/`réflexif`. Corrigé : les 3 variantes accentuées ajoutées à `FORMAT_LONGUEUR`, un seul dict module-level donc correctif appliqué aux deux points d'usage (`build_journalistic_brief()`, `build_prompt()`) automatiquement. Vérifié fonctionnellement (les 3 nouvelles clés mappent bien vers la même plage que leur équivalent sans accent). Aucune correction rétroactive des articles déjà publiés avec ce défaut (même décision que le point ci-dessus — cosmétique, non consommé en aval). |
| **Dérive du LLM sur la longueur réelle des articles** | 10 août | Diagnostic complet : consigne de longueur isolée dans le prompt, jamais reprise dans le bloc final avant génération, aucune validation post-génération. Renforcement du prompt seul testé **insuffisant** (94,4% d'incohérence sur un batch isolé, pire que la référence du 9 août, biais net vers le dépassement) — mécanisme de retry automatique ajouté à la place : écart > 40% de la borne dépassée → un seul essai supplémentaire, avec rappel chiffré de l'écart mesuré (pas de boucle, résultat du 2e essai accepté quoi qu'il arrive). Nouveaux champs frontmatter `mots_reels`/`retry_longueur` pour la traçabilité. **Testé en conditions réelles sur 12 articles** : 3 retries déclenchés, tous améliorés ; aucun faux négatif sur les 9 non retentés. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. Validation à plus grande échelle en suivi : Partie 1 point 1. |
| **Date fictive jamais transmise au LLM** | 10 août | La date calculée par `generate.py`/`generate_series.py` pour espacer une série ne servait qu'au nom de fichier, jamais envoyée au LLM (consigne "une date crédible en 2098", totalement libre) — d'où la convergence observée vers une date quasi unique sur plusieurs articles, et l'incohérence systématique entre date du nom de fichier et date affichée dans l'article. Corrigé dans `prompt_builder.py` (`build_journalistic_brief()`) : la date est transmise explicitement, avec instruction de la reprendre telle quelle. Testé en conditions réelles : 12/12 articles cohérents. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Signature absente ou incohérente (2 itérations)** | 10 août, itération 2 validée le 12 août | Root cause : `get_journal_profile()` ne peuple le nom de journaliste curaté que sur 1 des 3 chemins de résolution du profil éditorial — sur les 2 autres, l'instruction de signature était purement absente du prompt, laissant le LLM libre de signer ou non. Itération 1 : signature toujours instruite, format unifié "Nom — Journal". Testé en conditions réelles : 12/12 articles signés (contre présence aléatoire avant), mais position incohérente (haut/bas) et 1 doublon trouvés. Itération 2 (même jour, après clarification des usages réels de la presse en ligne) : position fixée en haut sous la date, "une seule fois" renforcé en interdiction stricte de répétition. **Validée en conditions réelles le 12 août** : un run `generate.py` avec une zone valide (`geneve_bunker_institutions`, débloqué par le correctif `zones_hier_journal` du 11 août soir) a confirmé une signature unique, toujours immédiatement sous la date. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Accent supprimé dans le nom de fichier (`fvrier` au lieu de `février`)** | 10 août | `build_article_filename()` (`api.py`) : la regex de nettoyage du slug de date ne reconnaissait que les lettres non accentuées, supprimant silencieusement tout accent au lieu de le translittérer. Corrigé via `unicodedata.normalize()` avant filtrage. Testé en conditions réelles sur 12 articles : confirmé corrigé. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Dossier de sortie des articles de série ignoré** | 10 août | `save_article()` (`api.py`) écrivait toujours à la racine de `articles/`, sans jamais lire `config["output"]["dossier"]` — `generate_series.py`/`generate_manual.py` construisaient pourtant ce chemin et y écrivaient leur `_index.md`, orphelin des articles qu'il indexe. Corrigé : `save_article()` lit désormais ce champ. Vérifié sur les 3 cas de figure (série, unité, config sans bloc `output`). Testé en conditions réelles : les 12 articles du batch de test se sont bien retrouvés dans `articles/policy_reform/`. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Scan non récursif de `trace_injection.py`/`audit_longueur_articles.py`** | 10 août | Effet de bord du correctif précédent : ces deux outils scannaient `articles/` à plat (`os.listdir`/`glob` non récursif) — sans correction, ils seraient devenus aveugles à tout article généré en série/manuel une fois rangé en sous-dossier. Corrigés en scan récursif (`os.walk` / `glob("**/*.md")`), `_index.md` explicitement ignoré par l'audit. `audit_longueur_articles.py` testé en conditions réelles (43 fichiers retrouvés, racine + sous-dossier). `trace_injection.py` testé en isolation seulement, pas en conditions réelles. Détail complet : `USER_MANUAL_COMPLET.md` §2ter. |
| **Gap de documentation — `state/event_relevance_usage.json` absent de l'inventaire** | 10 août | Pas un bug : mécanisme de rotation à mémoire des événements custom existant depuis le 2 août (`loader.py`, `select_relevant_events()`), simplement jamais documenté dans `USER_MANUAL_COMPLET.md` ni intégré au protocole de nettoyage post-test. Découvert en nettoyant un test de génération réelle (fichier non suivi par Git, donc non restauré par `git checkout`). Manuel et protocole de test corrigés en conséquence (§0, §2, §2ter). |
| **Clarté des descriptifs GUI + sortie `trace_injection.py`** | 11 août (matin) | David a commencé la validation navigateur du GUI, signalant au fil du test 3 descriptifs jugés trop techniques : `fix_annee_debut_placeholder` (descriptif principal), `trace_injection` (descriptif principal), `fix_alliances_oppositions` (descriptif principal + 7 options + 2 libellés de rapports) — tous reformulés en retirant le jargon d'implémentation (chemins de fichiers bruts, "passe LLM", "rétroactif" sans explication) tout en conservant le vocabulaire propre au projet (variables, scénarios, entités, alliances). Correctif de lisibilité appliqué en plus directement à la sortie de `trace_injection.py` (`_rendre_markdown()`) suite à un exemple réel fourni par David : type technique brut remplacé par un libellé lisible, statut d'origine reformulé, échelle d'impact explicite, listes d'alliances/oppositions enfin lisibles (suffixe de scénario retiré quand non ambigu, snake_case converti en texte normal). **10 entrées validées en conditions réelles et marquées `gui_verified: true`** : les 4 audits, les 2 entrées de veille, `trace_injection`, `fix_annee_debut_placeholder`, `fix_alliances_oppositions`, `generate`. Détail complet : `USER_MANUAL_COMPLET.md` §7 (addendum du 11 août) et §2. |
| **Clarté suite des descriptifs GUI (11 août, session soir)** | 11 août (soir) | Revue systématique des 28 entrées de `scripts_config.json` pour repérer le jargon d'implémentation restant, au-delà des 3 déjà traitées le matin. **17 changements appliqués** : 8 descriptifs principaux (`enrich_minimal`, `zoning_topdown_test`, `reparenter_sous_zones_orphelines`, `scan_geographie_complet`, `audit_dates_instances`, `audit_etat_temporel_fin`, `audit_longueur_articles`, `audit_type_relation_dominante` — retrait de notes de développeur datées, de noms de fichiers internes type `frontmatter`/`loader.py`, d'historique de bugs non pertinent pour l'utilisateur) + 9 changements au niveau des options (dev-log daté retiré sur `--forcer-scenarios`/`--ancrage-temporel` ×2, nom de fichier brut retiré sur `--update`/`--slug` (undo_custom), jargon "N1"/"cache"/"additif" clarifié, libellés de choix techniques bruts d'`undo_custom --type` rendus lisibles). Vérifié par diff programmatique à chaque étape : 14 entrées touchées au total, aucune autre altérée. |
| **Test navigateur des entrées GUI modifiées** | 11 août (soir) | **Chantier définitivement clos.** Les 3 dernières entrées (`create_entities`, `enrich_minimal`, `generate_instances`) testées en conditions réelles. `create_entities` : cycle complet testé (auto-suggest → custom → cycle post-injection), 2 bugs de code réels trouvés et corrigés en cours de route (voir lignes dédiées ci-dessous). `enrich_minimal` : testé, résultat vide (0 fiche `officialise_minimal` restante) — cohérent avec le chantier P8 clos depuis le 27 juin, comportement attendu. `generate_instances` : exercé comme dépendance du cycle post-injection du test `create_entities` (pas cliqué directement via son propre bouton GUI, mais comportement du script confirmé fonctionnel en conditions réelles). Les 28 entrées du panneau GUI sont désormais **toutes** `gui_verified: true`. Détail des bugs trouvés en testant : voir les 5 lignes suivantes de ce tableau. |
| **Crash EOFError en création d'entités (mode auto-suggest/auto, GUI)** | 11 août (soir) | En testant `create_entities` (mode auto-suggest) depuis le GUI : `EOFError: EOF when reading a line` sur un `input()` non protégé dans `run_auto_suggest_mode()` (`create_entities_and_instances.py`) — même bug que celui corrigé le 11 juillet sur `--mode`, jamais étendu aux deux sous-questions de ce mode (nombre d'idées, scénario ciblé) ni à celles du mode `auto` (nombre d'entités, catégorie imposée). **4 `input()` protégés** par `sys.stdin.isatty()` : hors terminal interactif (GUI/cron), retombe directement sur la valeur par défaut déjà prévue dans le code plutôt que de planter. **Bug de type corrigé au passage** : `scenario_filter` était traité comme une chaîne simple dans le repli interactif, alors que tout le reste du script (`step_auto_suggest_entities`, `args.scenario` en `nargs="+"`) le traite comme une liste — un scénario tapé en CLI pur aurait été itéré caractère par caractère. Corrigé (`scenario_filter = [scenario_raw]`). Testé en conditions réelles : mode auto-suggest relancé après correctif, plus de crash, 5 idées générées avec succès. |
| **Silence sur rejet `category`/`scenario_ref` invalide (mode custom)** | 11 août (soir) | Trouvé en traitant la queue générée par le test ci-dessus : une entité ("Les Veilleurs des Nappes Phréatiques") disparaissait du log sans aucun message après son en-tête `=== Nom ===`, alors que `needs_review.yaml` contenait bien la raison (`category invalide : 'mouvement'`, hallucination du LLM auto-suggest malgré la contrainte de prompt). Cause : `process_custom_idea()` retournait directement sur ces deux rejets précoces sans jamais imprimer, contrairement à tous les autres cas d'échec de la fonction (archétype, instance) qui affichent toujours leur motif. Corrigé : `print(f"  ✗ Rejetée : {reason}")` ajouté sur les deux cas (`category`, `scenario_ref`). |
| **`queue.yaml` écrasé par un panneau caché (`saveOpenConfigForms`, GUI)** | 11 août (soir) | Un run `create_entities` en mode auto-suggest avait bien écrit 5 idées dans `entites_custom/queue.yaml` (confirmé par le log), mais le fichier était retrouvé vide juste après. Cause : `saveOpenConfigForms()` (`app.js`, ajoutée le 31 juillet pour un autre bug) sauvegarde tout panneau `.yaml-form-panel` présent dans `#form-body` avant de lancer un script — mais un panneau `config_fields_mode` (ex. le formulaire Custom de `create_entities`, réservé à ce mode) reste dans le DOM même caché par un autre mode actif (`updateModeOnlyVisibility()` ne fait que du `display:none`, jamais un retrait du DOM). Le panneau Custom, resté ouvert/vu plus tôt dans la session et jamais rempli, a donc été sauvegardé vide par-dessus le fichier qu'auto-suggest venait d'écrire. Corrigé : `saveOpenConfigForms()` ignore désormais tout panneau dont le mode déclaré ne correspond pas à l'onglet actif au moment du clic Lancer — même logique que `updateModeOnlyVisibility()`. Affecte potentiellement aussi `inject_events`/`inject_signals` (même mécanisme `config_fields_mode`), non vérifié spécifiquement. |
| **Placeholder cassé + réapparition d'une saisie ancienne (champ Angle, `generate.py`)** | 11 août (soir) | Deux causes distinctes derrière le même symptôme ("Angle : romuva la nouvelle religion en europe" réapparaissant dans le récapitulatif malgré un champ vide à l'écran). **(1) Bug JS réel** : `renderOption()` fixait `inp.placeholder = opt.label` au lieu de `opt.placeholder` — le texte d'exemple ("ex : focus sur les réfugiés climatiques") ne s'affichait jamais, remplacé par le libellé du champ. Corrigé, `autocomplete="off"` ajouté en prévention sur tous les champs texte générés (empêche une resucée future du navigateur, bien que ce n'était pas la cause ici). **(2) Reliquat `config.yaml`** : un champ vide dans le formulaire GUI n'envoie tout simplement pas le flag CLI correspondant (`collectArgs()`, comportement voulu) — le mode Semi-guidé retombe alors sur `config.yaml` comme base, qui gardait `angle_specifique: romuva la nouvelle religion en europe` depuis un test d'il y a plusieurs semaines, jamais nettoyé depuis. Pas un bug de code : `config.yaml` ligne 44 vidée manuellement par David (`sed -i '.bak' '44s/.*/  angle_specifique: /' config.yaml`), confirmé résolu. |
| **`--zone-slug` proposait des sous-zones sans journal (`generate.py`, Semi-guidé)** | 11 août (soir) | Repéré en testant la génération d'article : `zone_slug invalide : 'archives_neutres_geneve' n'existe pas dans journaux.yaml pour breakdown/pro_pouvoir`, alors que cette zone existe bien dans `geographie/breakdown.md` — mais en tant que sous-zone niveau 2 (`parent: geneve_bunker_institutions`). `journaux.yaml` n'a jamais qu'une entrée par zone niveau 1 ; le menu `--zone-slug` (type `zones_hier`) listait toutes les zones tous niveaux confondus sans filtrer sur la présence réelle d'un journal, laissant l'échec se produire seulement au lancement (`validate_config_semi_guide()`) plutôt que d'empêcher la sélection en amont. **Corrigé sans casser les usages légitimes de la hiérarchie complète** (`zone_hint` sur `create_entities`/`inject_events`, qui veut délibérément pouvoir cibler une sous-zone précise) : nouveau type `zones_hier_journal` (`app.py`, fonction `_zones_avec_journal()`) qui filtre sur le contenu réel de `journaux.yaml` (`data[scenario][ligne]['zones']`, union des deux lignes éditoriales) plutôt que de supposer "niveau 1 = a un journal". `--zone-slug` de `generate.py` bascule sur ce nouveau type dans `scripts_config.json`, description mise à jour en conséquence. `zones_hier` (l'ancien type) reste inchangé et utilisé tel quel par `zone_hint`. Vérifié par test unitaire local avant livraison : `geneve_bunker_institutions` passe le filtre, `archives_neutres_geneve` non. **Confirmé en conditions réelles le 12 août** — a servi de base au test de validation de la signature (voir ligne dédiée ci-dessus). |
| **Diagnostic `annee_debut`/`ancrage_reel` sur les événements** | 12 août | Question ouverte depuis le 8 août. Mené sur `inject_custom_events.py`, `fix_annee_debut_placeholder.py`, `loader.py`, et un dépouillement réel de `registre_evenements.md` (53 événements custom, tous scénarios). Conclusions : structure de date différente des instances (champ `date` unique, pas de bande `annee_debut`/`annee_fin`) ; aucune dérive de concentration observée (pic max 11% sur une seule année — 2041/2044/2047 à 6/53 chacun — contre 22% pour les instances avant correctif ; seulement 2/53 événements en 2026, pas de blocage comparable au bug des 477 fiches d'instances) ; **mais aucun mécanisme d'ancrage réel n'existait avant cette session**, ni en mode auto ni en mode custom (`inject_custom_events.py` ne chargeait jamais `etat_du_monde_reel.md`, contrairement à la génération d'instances), et `analyze_vault_coverage()` (couverture auto des événements) n'a — comme `analyze_entity_coverage()` côté entités — aucune dimension temporelle (a élargi la portée du point Partie 1 #2 aux événements, pas seulement aux entités). **Décision prise** : pas de mécanisme lourd type `ancrage_reel` des instances (bande graduée + anti-recyclage par shingle-matching) pour les événements — un enrichissement de contexte suffit, voir ligne "Cohérence événements custom" ci-dessous. |
| **Cohérence événements custom / vault, registre, géographie, état du monde** | 12 août | Nouveau chantier, demandé par David suite au diagnostic ci-dessus, sur `inject_custom_events.py` — couvre les deux modes (auto n'écrit que dans `queue.yaml`, l'injection réelle passe toujours par le mode custom via `process_idea()`, donc un seul point de code modifié couvre les deux). Trois changements : (1) import de `load_etat_monde_reel()`/`load_scenario_timeline_summary()` depuis `instance_generation_common.py` — réutilisation, aucune duplication ; (2) deux nouveaux blocs de contexte dans le prompt de développement d'événement (`## CHRONOLOGIE RÉELLE DU SCÉNARIO`, `## ÉTAT DU MONDE RÉEL`) plus une règle explicite de cohérence, en particulier pour une date proche dans le temps ; (3) validation mécanique de `zone_hint` contre `load_all_zones_event(scenario)`, refaite à **chaque itération** de la boucle scénarios (initiale et retry) — zone invalide pour ce scénario → avertissement + repli sur "libre". Décision délibérée de ne PAS ajouter de garde-fou mécanique bloquant sur le chevauchement thématique du registre (enrichissement de contexte seulement) — cohérent avec la pratique du projet de ne pas construire de mécanique de calibration pour un problème non observé (53 événements seulement, risque de mauvaise calibration comme vécu sur le chantier longueur du 10 août). **Testé en conditions réelles (dry-run, qui appelle le LLM pour de vrai — voir piège transversal du 31 juillet)** sur une queue de 5 idées ciblées : date proche 2028 (ancrage réel confirmé dans `note_coherence`), zone invalide (warning déclenché), zone valide (silence, zone utilisée), contrôle date lointaine (non-régression), et surtout **le même `zone_hint` sur deux scénarios différents** — validé silencieusement sur `eco_communalism`, warning déclenché sur `breakdown` où la zone n'existe pas, preuve que la revalidation se refait bien à chaque itération de la boucle plutôt qu'une seule fois en amont ; ce dernier cas a aussi déclenché un vrai retry de validation, confirmant que le zone_hint validé (pas la version brute) est bien réutilisé sur le retry. **Non testé en injection réelle (non dry-run)** — chemin d'écriture non modifié par ce correctif, risque jugé faible. Détail complet : `USER_MANUAL_COMPLET.md` §2, section `inject_custom_events.py`. |
| **Panneau Revue — slug/scénario/détail vides sur entités et signaux** | 12 août | Signalé par David sur une entrée réelle (`Les Veilleurs des Nappes Phréatiques` affichée `(entité)` / `—` / `—`). Cause : `_read_needs_review_yaml()` (`app.py`), parseur YAML maison ligne par ligne construit pour le format événements/enrichissement — le correctif du 2 août avait fait apparaître les sources `entites_custom`/`signaux_custom` dans le panneau sans jamais leur apprendre à lire leurs propres champs (`idea.nom`, `idea.scenario_ref`, `reason:` à plat, structure différente du format d'origine). **Deux correctifs** : (1) reconnaissance de `nom:`/`scenario_ref:`/`reason:`, avec déséchappement naïf des quotes doublées YAML — testé directement contre le vrai fichier de David ; (2) suite à sa question sur la couverture des 3 pipelines, trouvaille d'un second trou touchant entités/événements/signaux identiquement : le repli générique sur exception imprévue des 3 scripts d'injection écrit une clé `error:` **scalaire singulière**, jamais reconnue (seule la forme plurielle `errors:`/liste l'était) — corrigé de la même façon, testé avec un cas simulé. **Confirmé en conditions réelles dans le navigateur** sur l'entrée de David — les 3 colonnes s'affichent désormais correctement. Détail complet : `USER_MANUAL_COMPLET.md` §7. |
| **Cohérence événements custom — confirmation en injection réelle (non dry-run)** | 13 août | Suivi léger laissé ouvert le 12 août (chantier lui-même déjà clos ce jour-là — voir ligne ci-dessus dans le tableau du 12 août). Queue de 5 cas rejouée en conditions réelles (pas dry-run) : `zone_invalide_test` et `multi_scenario_zone_test`/`breakdown` ont déclenché le warning `zone_hint` attendu (revalidation par scénario confirmée en réel, pas seulement en dry-run) ; `escalade_sahel_2028_test` et `zone_valide_test` injectés au premier essai ; `controle_date_lointaine_test` a échoué 3/3 (root cause distincte, voir ligne dédiée ci-dessous). Deux événements réels hors queue de test (`revolution_travail_sahel_numerique`, `greve_generale_corridors_eurasiens`) injectés avec succès sur tous leurs scénarios cibles, retries sur acteurs fonctionnant comme prévu. `validate.py` : 0 erreur, 10 avertissements, base valide. Écriture disque du chantier du 12 août définitivement confirmée fonctionnelle. |
| **Dimension temporelle pour la génération automatique** | 13 août | Chantier backlog Partie 1 (ex-point 2), esquissé le 8 août, portée élargie aux événements le 12 août, codé le 13 août. Choix de granularité tranché avec David : **bandes larges** (proche 2026-2035 / moyen 2036-2060 / lointain 2061-2098) pour le signal envoyé au LLM à l'étape auto-suggest/auto — actionnable, peu de bruit sur un vault encore modeste — et **année exacte** conservée en interne pour la détection de concentration (même granularité que celle qui avait révélé 22% sur 2041 côté instances avant le correctif `annee_fin`). Nouvelles fonctions partagées dans `instance_generation_common.py` : `TEMPORAL_BANDS`, `compute_temporal_distribution()`, `format_temporal_summary()`, `format_concentration_warnings()` (seuil de concentration : 12% du total, seulement si l'échantillon atteint 15 — sous ce seuil jugé trop bruité pour être actionnable). Appliqué symétriquement dans `analyze_entity_coverage()` (`annee_debut`) et `analyze_vault_coverage()` (`date`), résumés de prompt enrichis d'une section "Distribution temporelle actuelle" + avertissement de concentration vault-entier, consignes des deux prompts auto-suggest mises à jour (compenser les bandes sous-représentées, éviter les années sur-concentrées, et pour toute proposition proche de 2026-2035 privilégier une idée rattachable à une dynamique réelle documentée plutôt qu'une date arbitraire — l'ancrage précis restant fait à l'étape de développement, déjà en place). Testé : fonctions helper validées unitairement (bandes correctement regroupées, seuil de bruit respecté, concentration détectée à 44%/20%/16% sur un cas simulé) ; **validé par David en dry-run réel** sur le vault. Injection réelle non spécifiquement retestée pour ce chantier (le mécanisme ne touche que la sélection/le prompt, pas le chemin d'écriture). `inject_custom_signals.py` vérifié sans dimension temporelle (aucun champ `annee_debut`/`date`) — non concerné, cohérent avec l'architecture du vault. |
| **Bug `evenement_cle` — année exigée en fin de phrase (jamais respecté par le LLM)** | 13 août | Trouvé en rejouant la queue de test en conditions réelles (voir ligne ci-dessus) : `controle_date_lointaine_test` a épuisé ses 3 essais de retry sans jamais être injecté, la validation rejetant systématiquement `evenement_cle` malgré une année bien présente — le LLM produit invariablement le format `"2091 : L'Europe unifie l'horloge..."` (année en tête), alors que `validate_instance()` n'acceptait qu'une année en toute fin de chaîne (`re.search(r"(\d{4})\s*$", ...)`). Le message de retry ne précisait pas *où* replacer l'année, d'où 3 échecs identiques sans convergence. Vérifié que la position de l'année dans `evenement_cle` n'a aucune fonction technique en aval (`date` est stockée séparément dans sa propre colonne du registre par `regenerate_registre_with_event()`, et `load_scenario_timeline_summary()` préfixe de toute façon sa propre date à l'affichage) — la contrainte de position était une pure convention sans nécessité. **Corrigé** : regex assouplie (`re.search(r"\b(\d{4})\b", ...)`, année acceptée n'importe où), prompt et exemple JSON mis à jour en cohérence (ne plus demander une "année finale" que la validation n'exige plus), message d'erreur reformulé. **Confirmé en conditions réelles** : `controle_date_lointaine_test` relancé avec la même idée d'origine (retrouvée dans `needs_review.yaml`, où le champ `idea` complet était bien préservé malgré la disparition de `queue.yaml`, vidée par design à chaque run) — injecté au premier essai, `validate.py` toujours propre (0 erreur, 10 avertissements inchangés). |
| **Documentation à corriger (chantier `trajectoire`)** | 14 août | Point 2 du backlog du 13 août — vérifié déjà appliqué dans `USER_MANUAL_COMPLET.md` (§1 et §6, tous deux datés "corrigé le 9 août 2026"). Fermé sans travail supplémentaire, juste une vérification avant de lancer un chantier qui n'en était plus un. |
| **P16 — `zone_hint` documenté dans `QUEUE_TEMPLATE`** | 14 août | Retrouvé via recherche exhaustive dans l'archive (décidé le 11 juillet, jamais fait, disparu du backlog sans clôture après le 2 août). `create_entities_and_instances.py` le documentait déjà — seul `inject_custom_events.py` avait l'oubli, corrigé (ajout de l'entrée dans le bloc CHAMPS du `QUEUE_TEMPLATE` + exemple JSON). `inject_custom_signals.py` confirmé hors scope. Risque d'écrasement identifié avant de coder : `save_queue_with_template()` réécrit tout `queue.yaml` depuis la constante Python à chaque vidage — d'où l'édition du `.py`, jamais du `.yaml` directement. |
| **Doublon d'entité `arctic_passage_authority` / `autorite_passage_arctique`** | 14 août | Diagnostic confirmé : vrai doublon généré automatiquement par `extract_phantom_slugs.py` (`entites_custom/processed.yaml` contient 3 entrées `_slug_fantome_original`/`_slug_corrige` le prouvant) — un slug fantôme détecté sans entité correspondante (probablement une référence de zone géographique) a généré une entité indépendante, sans savoir qu'`arctic_passage_authority` existait déjà pour la même institution. Champs `zone:` et l'entrée `geographie/breakdown.md:2278` identifiés comme un chantier séparé (référence géographique, pas d'entité) et volontairement non touchés. **Script `fix_arctic_passage_duplicate.py` livré** (réutilisable) : 17 fiches migrées, 34 références alliance/opposition réécrites, puis `undo_custom.py --generalisation yes --execute` (archétype fantôme + instance supprimés, `_entities_list.json` nettoyé). `validate.py` final : 0 erreur. |
| **Wikilinks cassés `test_durcissement_policy_reform`** | 14 août | 7 fiches `policy_reform` référençaient encore une fiche supprimée (résidu du 8 août), une ligne bullet identique par fiche. **Script `fix_test_durcissement_wikilinks.py` livré** (réutilisable pour tout futur cas similaire) : 7 lignes retirées sur 7 fiches. `validate.py` final : 0 erreur, 0 avertissement. |
| **Quatre reliquats de la consolidation du 7 août** | 14 août | Les 4 sous-points traités d'un coup. (1) Redéploiement des correctifs du 2 août (`routes_dashboard.py`, panneau Revue, Groenland) : confirmé de facto via usage réel documenté (bug trouvé le 12 août sur le panneau Revue, preuve d'utilisation post-livraison) — fermé sans action. (2) `instance_template.md` : confirmé par David déjà déplacé vers `/templates` ; vérifié qu'aucun autre script n'a de dépendance sur son emplacement dans `instances/` — les filtres existants deviennent inertes, pas cassés. (3) Limite panneau Revue (slug générique) : vérifié dans le code réel d'`app.py` que c'était déjà corrigé le 12 août (branches `nom:`/`scenario_ref:`/`reason:` ajoutées à `_read_needs_review_yaml()`, non documenté dans le manuel jusqu'ici) — tracé à la main sur un vrai extrait `needs_review.yaml`, confirmé fonctionnel. (4) Discipline de rédaction du backlog : non-actionnable, vigilance continue notée. |
| **Fichiers parasites `generator/` (incident du 5 août)** | 14 août | David a relancé la commande de vérification fournie le 11 août : aucun fichier trouvé, déjà propre. Fermé, rien à faire. |
| **Encodage portugais cassé dans certains slugs** | 14 août | Retrouvé via recherche exhaustive dans l'archive (noté le 8 août, jamais traité). Cause racine identifiée avec précision : `slugify()` utilisait une table d'accents français en dur au lieu d'une normalisation Unicode générique — tout accent non-français (portugais, espagnol...) tombait dans le `re.sub` générique et devenait `_`. Trois fichiers touchés et corrigés, identiques mot pour mot : `create_entities_and_instances.py`, `create_entity.py` (legacy), `officialize_alliances.py` (actif). Correctif : normalisation Unicode NFD (même principe que `_fold()` déjà existant dans `gui/app.py`), testé sur portugais/français/espagnol/allemand. **Audit du vault** (`audit_broken_slugs.py` livré, réutilisable, lecture seule) : 590 entités auditées, 18 candidats, 2 vrais cas confirmés (`rede_paulista_de_distribuic_o_algor_tmica`, `frente_sert_o_livre`), 15 faux positifs (raccourcissements volontaires de slug), 1 artefact du script (`entite_template.md`, voir Partie 2). **Migration des 2 cas exécutée** (`rename_broken_slugs.py` livré, réutilisable) : 11 fichiers renommés, 322 références réécrites dans 141 fiches, `documentation/` explicitement exclu (historique, jamais réécrit). `validate.py` final : 0 erreur. |
| **`acteurs_hint_count` (P15) non plafonné en filtre dur** | 14 août | Diagnostic précis : la valeur était calculée et bornée (1-4) mais jamais transmise à `step2_develop_instance()` ni utilisée par `validate_instance()` — calculée puis jetée sans effet, contrairement à `variables_hint_count` qui a une vraie troncature. **Corrigé** : nouvelle fonction `truncate_actors()` dans `inject_custom_events.py`, appliquée à l'essai initial et à chaque retry, même schéma que la troncature `variables` (hints préservés en priorité). Testé unitairement (3 cas). Pas encore confirmé en conditions réelles — laissé en validation au fil de l'eau, comme le point #1 du backlog. |
| **Duplication `detect_registre_leakage()`** | 14 août | La fonction et deux fonctions dépendantes (`_read_registre_text()`, `_normalize_for_matching()`) existaient en double entre `instance_generation_common.py` (module partagé) et `fix_annee_debut_placeholder.py` (copie indépendante) — divergence purement cosmétique constatée (docstrings, style), aucune divergence fonctionnelle. **Corrigé** : `fix_annee_debut_placeholder.py` importe désormais les trois fonctions depuis le module partagé, variable de cache locale devenue inutile retirée. Prévient une future divergence silencieuse, même pattern que celui ayant causé de vraies erreurs avant la factorisation de juillet/août. |
| **GUI — `--force` du panneau localisation ne rafraîchissait pas le menu** | 14 août | Diagnostic en trois causes distinctes, sur trois fichiers. (1) `scripts_config.json` : le champ `--slug` d'`extract_localisation` n'avait aucune déclaration `slug_extra_params` reliant son contenu à `--force` — corrigé, ajout de `{"force": "--force"}`, vérifié par diff programmatique qu'aucune autre entrée n'a été touchée. (2) `app.js` : `lireValeurChamp()` lisait `.value` au lieu de `.checked` sur les checkboxes — une checkbox sans attribut `value` explicite renvoie toujours `"on"` quel que soit son état. Corrigé. (3) `app.py` : la route `/api/slugs` ne lisait ni ne transmettait jamais le paramètre `force` au sous-processus `extract_localisation.py --scan-pending`, même une fois envoyé par le frontend. Corrigé. Vérifié séparément que `extract_localisation.py` respectait déjà correctement `--force` en interne (`collect_fiches()`) — aucun correctif nécessaire côté script. **Testé et confirmé en navigateur réel par David.** |

---

*Fin du backlog maître. Pour la prochaine session : reprendre en priorité
le chantier `forces_attractives`/`forces_repulsives` (Partie 1, point 2)
— David doit d'abord relire les 12 fiches `variables/*.md` et trancher
quelle section sert de source de vérité avant tout code. Reste sinon en
Partie 1 : le point #1 (validation retry longueur, toujours 🟡, sans
urgence), P17/Bug#27/renommage YAML/troncatures JSON (tous rouverts ou
gardés pour plus tard sur décision explicite de David), et la question
non tranchée sur "Les Veilleurs des Nappes Phréatiques" — **à trancher
en tout début de session**.

Session du 14 août particulièrement dense : recherche exhaustive dans
l'archive complète des 40 anciens backlogs/handoffs ayant retrouvé 4
chantiers tombés du radar (P16 clos, P17/Bug#27/nettoyage rotation
rouverts) ; 5 chantiers de la Partie 1 du 13 août entièrement clos
(doublon Arctic, wikilinks `test_durcissement`, quatre reliquats du 7
août, fichiers parasites `generator/`, doc `trajectoire`) ; 3 points de
la Partie 2 résolus en profondeur (encodage portugais avec audit +
migration réelle sur le vault, `acteurs_hint_count`, duplication
`detect_registre_leakage()`) ; 1 bug GUI diagnostiqué et corrigé sur 3
fichiers distincts (`--force` panneau localisation) ; 1 nouveau chantier
substantiel identifié (`forces_attractives`/`forces_repulsives`, contenu
réel du vault jamais exploité par le pipeline).

**12 fichiers livrés** (voir `HANDOFF_14_AOUT.md` §13 pour le détail
complet) : `inject_custom_events.py` (deux correctifs cumulés),
`create_entities_and_instances.py`, `create_entity.py`,
`officialize_alliances.py`, `fix_annee_debut_placeholder.py`, `app.js`,
`app.py`, `scripts_config.json`, plus 4 nouveaux scripts d'audit/
migration réutilisables : `fix_arctic_passage_duplicate.py`,
`fix_test_durcissement_wikilinks.py`, `audit_broken_slugs.py`,
`rename_broken_slugs.py`. Redémarrage Flask requis (changements dans
`app.py`/`scripts_config.json`).*
