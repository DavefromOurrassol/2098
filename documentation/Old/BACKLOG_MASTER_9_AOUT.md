# Backlog maître — Ourrassol 2098
*Consolidé le 9 août 2026, à partir de l'ensemble des handoffs/backlogs du
1er août au 9 août 2026. Remplace tous les documents précédents comme
référence unique. Chaque chantier a un nom stable — à réutiliser tel quel
dans les prochaines sessions pour éviter toute nouvelle divergence de
nommage.*

---

# PARTIE 1 — CHANTIERS OUVERTS (à traiter)

## 🔴 1. Dérive du LLM sur la longueur réelle des articles
**Nouveau, découvert le 9 août** en creusant le point clos "`metadata["longueur"]`
réutilisé en aval ?" (voir Partie 4). Sur les 31 articles du vault,
`audit_longueur_articles.py` isole désormais le vrai signal (hors bug
d'accent corrigé le jour même, voir Partie 4) : **70,4% des articles
(19/27 analysables) ont une longueur réelle hors de la plage demandée**
à la génération — parfois largement au-dessus (jusqu'à 1257 mots pour
une plage 600-900), parfois largement en dessous (322 mots pour une
plage 700-1000). Aucun biais directionnel net.

**Ce n'est plus un problème de métadonnées** (celui-là reste clos, sans
correction rétroactive, cosmétique) — c'est un vrai sujet de qualité de
génération : le LLM ne respecte pas la consigne de longueur donnée dans
`build_journalistic_brief()` de façon fiable. À investiguer : la
consigne est-elle assez explicite/insistante dans le prompt ? Le modèle
utilisé (Mistral, tier "strict") a-t-il une tendance connue à dériver
sur ce genre de contrainte ? Faut-il une validation post-génération avec
retry si la longueur réelle est hors plage (comme il en existe déjà pour
d'autres champs) ?

**Outil de diagnostic prêt** : `audit_longueur_articles.py` (lecture
seule, section GUI Validation) — distingue le vrai signal (Cas A, format
et longueur d'accord) d'une éventuelle divergence override (Cas B).

---

## 🟡 2. Test navigateur des entrées GUI modifiées
**Ouvert en continu depuis fin juillet**, périmètre qui s'est élargi à
chaque session sans jamais être clos par un vrai clic dans un navigateur.
Toute la logique a été confirmée par lecture de code à chaque fois
(confiance haute), mais `gui_verified: false` reste sur toutes ces
entrées :
- `fix_alliances_oppositions`, `enrich_minimal` (7 août)
- Les 2 entrées de veille — `export_prompt_veille`, `import_veille_
  etat_monde` (8 août)
- `generate_instances`, `fix_annee_debut_placeholder` (8 août)
- Les 3 audits — `audit_dates_instances`, `audit_type_relation_
  dominante`, `audit_etat_temporel_fin` (8-9 août)
- Options `--ancrage-temporel` sur `create_entities`/`generate_instances`
  (8 août)
- **Nouveau (9 août)** : menu `État`/`Clandestin` refondu dans
  `create_entities` (mode custom, chantier `trajectoire`)
- **Nouveau (9 août)** : `audit_longueur_articles` (section Validation)

**Suggestion** : plutôt qu'un test exhaustif de chaque entrée
séparément, une seule session dédiée "clic à travers tout le GUI"
pourrait clore ce point une fois pour toutes.

---

## 🟡 3. Même diagnostic `annee_debut`/`ancrage_reel` sur les événements ?
**Question posée le 8 août, jamais explorée.** Le chantier `annee_debut`
a porté exclusivement sur les instances. Les événements
(`inject_custom_events.py`, `registre_evenements.md`) ont-ils le même
problème structurel ? Diagnostic à faire en premier, avant de décider si
la même approche (bande de traçabilité graduée, `ancrage_reel`) s'y
applique.

---

## 🟡 4. Dimension temporelle pour la génération automatique
Deux idées liées, esquissées le 8 août, non codées — à traiter ensemble
plutôt que séparément (la seconde est explicitement une extension de la
première) :
- **Auto-suggest** (`analyze_entity_coverage()`) mesure déjà 3
  dimensions (géographie, zones absentes, catégories) — ajouter la
  distribution d'`annee_debut` par bande temporelle, pour que
  l'auto-suggest propose activement des créations dans les bandes
  sous-représentées.
- **Répartition homogène + ancrage sur les crises réelles** pour la
  génération automatique en général — éviter qu'une bande d'années ne
  se retrouve sur-représentée (rappel : 2041 concentre 22 % du vault),
  et ancrer sur les crises du registre du scénario plutôt qu'une
  répartition arithmétique/aléatoire.

---

## 🟢 5. Documentation à corriger (chantier `trajectoire`, 9 août)
`USER_MANUAL_COMPLET.md` doit être mis à jour sur un point tranché
aujourd'hui : `generate_instances.py` est confirmé **actif** (usage
distinct et complémentaire de `create_entities_and_instances.py` —
backfill d'instances pour des entités déjà créées), pas legacy comme le
manuel le décrit actuellement. Ce backlog maître documente déjà la
correction ; reste à la répercuter dans le manuel lui-même.

---

## 🟢 6. Doublon potentiel d'entité — `arctic_passage_authority` / `autorite_passage_arctique`
Trouvé le 9 août en marge du chantier `annee_fin`, sur le scénario
`breakdown`. Deux fiches entités distinctes (`entites/arctic_passage_
authority.md` et `entites/autorite_passage_arctique.md`) semblent décrire
la même entité — une version anglaise, une version française — d'après
la quasi-identité de leur rôle narratif observée dans les justifications
`annee_fin` générées pour leurs instances respectives (même jalon de
registre utilisé, même trajectoire de fragmentation en factions
rivales).

**À diagnostiquer** : vraie duplication (même archétype créé deux fois)
ou deux entités légitimement distinctes malgré la ressemblance ? Contenu
des deux fiches pas encore comparé en détail. Si duplication confirmée,
vérifier l'ampleur — cas isolé, ou symptôme plus large à chercher sur le
reste du vault (rappelle le pattern des 284 fiches sans `statut` trouvées
le 5 août, une strate plus ancienne du projet). Si confirmé comme
doublon, prévoir la fusion/suppression d'une des deux fiches et la
migration de ses références (instances, alliances/oppositions d'autres
fiches) vers celle conservée.

Aucun risque à laisser les deux fiches coexister en attendant ce
diagnostic — pas bloquant pour le chantier `annee_fin` en cours.

---

## 🟢 7. Nettoyage `test_durcissement_policy_reform`
**Résidu mineur du 8 août**, identifié le 9 août. 7 fiches instances de
`policy_reform` référencent encore `[[test_durcissement_policy_reform]]`
en alliance/opposition alors que cette fiche n'existe plus (ni dans
`entites/`, ni dans `instances/`) — wikilinks cassés, sans impact
fonctionnel, à nettoyer manuellement ou via un script `sed` ciblé.

---

## 🟢 8. Quatre reliquats jamais repris depuis la consolidation du 7 août
Identifiés en tout début de session le 8 août, promis pour la fin de
séance, reportés à chaque fois faute de temps :
- **Redéploiement des correctifs du 2 août jamais confirmé** —
  `routes_dashboard.py`, le fix du panneau Revue (`app.py`/`enrich_
  minimal.py`), `geographie/policy_reform.md` (Groenland) : livrés en
  session mais jamais confirmés déployés par un handoff ultérieur.
- **`instance_template.md`** — recommandation de le déplacer hors de
  `instances/` jamais suivie, impact potentiel sur d'autres scripts
  (`extract_phantom_slugs.py` etc.) jamais audité.
- **Limite du panneau Revue** — `entites_custom`/`signaux_custom`
  affichés avec un slug générique au lieu du vrai nom, jamais reprise
  dans un backlog depuis sa découverte initiale.
- **Discipline de rédaction du backlog** — exemple identifié où un
  backlog ne listait pas dans sa propre section "reste à faire" des
  points pourtant documentés ailleurs. Pas un chantier en soi, plutôt un
  rappel de méthode pour la tenue de ce document lui-même.

---

## 🟢 9. Renommage des YAML génériques par dossier
**En pause depuis fin juillet, jamais réévalué.** `queue.yaml`/
`processed.yaml`/`needs_review.yaml` répétés à l'identique dans
`entites_custom/`, `evenements_custom/`, `signaux_custom/` — décision de
renommage reportée (clarté vs coût de migration). Aucune urgence
identifiée à ce jour.

---

## ⚪ 10. Chantiers de fond, scopés mais non codés (pause longue durée)
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

- `acteurs_hint_count` (P15) non plafonné en filtre dur dans `inject_
  custom_events.py` — jamais observé comme un vrai problème.
- `--force` du panneau `--scan-pending` (`extract_localisation.py`) ne
  rafraîchit pas dynamiquement le menu — contournable via `--scenario`.
- `coverage_proposals_reference.yaml` sans `.applied` — anomalie
  repérée, famille legacy, sans impact opérationnel.
- `/api/carte/appliquer_zone_topdown_suspecte` — route dormante, seul
  point d'entrée UI retiré (absorbé par l'onglet Chantiers).
- Champ `type` des zones géographiques (`zone_sinistree` etc.) — jamais
  utilisé dans le prompt, distinct de `statut` qui l'est.
- Bloc `simulation` sur les fiches variables — chargé par `loader.py`,
  jamais utilisé par `prompt_builder.py`. Probablement du monitoring
  interne, pas de la narration.
- `constrained_variables` (snapshot) — calculé, jamais affiché dans le
  prompt.
- Incohérence documentation/code sur `forces_attractives`/`forces_
  repulsives` — la docstring de `build_variables_context()` promet ces
  champs "si disponibles", jamais implémentés côté `loader.py` non plus.
- `--min-shingle` de `detect_registre_leakage()` (3 scripts touchés par
  `ancrage_reel`) fixé en dur à 6 mots — pourrait devenir un paramètre
  CLI si un faux positif/négatif apparaît en usage réel.
- Cas d'échec LLM ponctuel observé une fois (4 août) : confusion entre
  un slug de zone géographique et un slug d'instance sur une fiche —
  résolu par retry, gardé en tête comme motif à surveiller si le même
  symptôme réapparaît (pourrait indiquer que le prompt gagnerait à
  lister explicitement les slugs de zones à ne PAS utiliser).
- Encodage portugais cassé dans certains slugs (repéré à l'ouverture du
  chantier `annee_fin`, 8 août) — jamais traité, mineur.

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
| **Revalidation mode Semi-guidé** | 3 août | Les 7 champs du bug §3.7 confirmés appliqués ; bug annexe `metadata["longueur"]` trouvé (→ voir Partie 1 point 2 pour le suivi resté ouvert). |
| **Audit de complétude snapshot/variables** | 3 août | 4 pertes de contenu narratif trouvées et corrigées. |
| **Test de charge Semi-guidé à 6 entités** | 4 août | 58 948 caractères mesurés, structurellement borné. A débouché sur le chantier alliances/oppositions ci-dessous. |
| **Chantier alliances/oppositions** | 4-5 août | 356→0 fiche vide sur 426, réciprocité automatisée, root cause corrigée à la source (`enrich_minimal.py`), validation durcie partiellement, découverte et correction annexe de 284 fiches sans `statut` (vault à 710/710 cohérent). |
| **146 conflits de réciprocité alliances/oppositions** | 7 août | Règle "opposition prioritaire" implémentée et appliquée, 2 bugs découverts et corrigés (écrasement multi-conflits, rapports jamais réinitialisés), intégrée en continu à `enrich_minimal.py`, GUI mis à jour. |
| **`fix_alliances_oppositions.py` absent du GUI** | 7 août | Résolu par l'intégration GUI du chantier ci-dessus. |
| **Documentation `depends_on`** | 8 août | Fausse alerte — vérifié en détail, le mécanisme était déjà correctement décrit. Rien à corriger. |
| **Chantier `annee_debut`** | 8 août | 477 fiches bloquées à 2026 corrigées, outil de veille construit (`etat_du_monde_reel.md` + export/import), chantier de robustesse `ancrage_reel` mené en parallèle (bande graduée 10 ans), run `--all` confirmé par un passage à vide. |
| **`ancrage_reel` / traçabilité graduée** | 8 août | Ouvert et refermé dans la même session, 5 itérations de test réel. |
| **Statut de `generate_instances.py`** | 9 août | Confirmé **actif**, usage distinct de `create_entities_and_instances.py` (backfill vs création). Voir Partie 1 point 6 pour la mise à jour du manuel encore à faire. |
| **Factorisation `instance_generation_common.py`** | 9 août | ~20 fonctions dupliquées entre `generate_instances.py` et `create_entities_and_instances.py` unifiées en un seul module. 3 bugs de divergence réels corrigés au passage (`call_claude_json`, `validate_instance`, `MAX_TOKENS`). Détail complet : `USER_MANUAL_COMPLET.md` §1. |
| **Chantier `trajectoire`** | 9 août | Fusion `etat_temporel`+`age_historique` en un axe unique + `est_clandestin` séparé. 710 fiches migrées via `migrate_trajectoire.py` (nouveau script, mécanique, aucun appel LLM), `validate.py` recalibré (bug C4 corrigé au passage), GUI mis à jour (menu `État`/`Clandestin` dans `create_entities`), `audit_etat_temporel_fin.py` adapté. Détail complet : `USER_MANUAL_COMPLET.md` §3bis. |
| **Chantier `annee_fin`** | 9 août | 28 fiches à trajectoire terminale sans date de fin corrigées (`fix_annee_fin_manquant.py`, nouveau script, ancré sur le registre du scénario). 27/28 directement, 1 cas résistant résolu par renforcement du prompt + filet de sécurité de plafonnement automatique ajouté au script. Concentration sur 2041/2061/2057 vérifiée légitime (jalons de rupture réels du registre, pas une convergence artificielle). Vérifié par `audit_etat_temporel_fin.py` (0% d'incohérence) et `validate.py` (0 erreur). |
| **Décision `type_relation_dominante`** | 9 août | Fausse alerte — en réalité déjà décidé et implémenté le 7 août (`prompt_builder.py`, `build_entities_context()`), jamais retiré du backlog dans les sessions suivantes. Affiché en ligne dédiée par entité avec période (`annee_debut`–`annee_fin`) ; garde-fou anti-fabrication confirmé suffisant (consigne générale "ne les contredis pas" du bloc entités, pas de mécanisme dédié nécessaire). |
| **`metadata["longueur"]` réutilisé en aval ?** | 9 août | Vérifié : oui, écrit de façon permanente dans le frontmatter par `api.py` ET `generate_manual.py` (traçabilité), mais jamais relu par aucun script (`trace_injection.py` lit `scenario`/`date_publication`/`titre`, jamais `longueur`) — impact purement cosmétique. **Correction rétroactive abandonnée** : la reconstruction resterait ambiguë (catégories `FORMAT_LONGUEUR` qui se chevauchent) et rien en aval n'en dépend fonctionnellement. Nouvel outil créé pour mesurer sans corriger : `audit_longueur_articles.py` (lecture seule, section GUI Validation) — 3 itérations en session pour arriver à un diagnostic fiable (v1 : bug de correspondance catégorie/plage, 100% faux positifs ; v2 : parsing direct de la plage textuelle, 64,5% mais mélangeait deux causes différentes ; v3 : distingue Cas A [vrai signal] de Cas B [divergence format/longueur]) — chiffre final fiable : **70,4% (19/27 analysables)**, voir Partie 1 point 1 pour le vrai sujet que ça a révélé. |
| **Bug d'accent `FORMAT_LONGUEUR` (`brève`/`éditorial`/`réflexif`)** | 9 août | Trouvé en creusant le point ci-dessus (les 4 articles `format: brève` retombaient tous sur le filet de secours générique "300 à 500 mots" au lieu de leur vraie plage "200 à 400 mots"). Cause : `FORMAT_LONGUEUR` (`prompt_builder.py`) ne couvrait que les orthographes sans accent, alors que `VALID_FORMATS` (`validate.py`) accepte explicitement les deux orthographes pour `breve`/`brève`, `editorial`/`éditorial`, `reflexif`/`réflexif`. Corrigé : les 3 variantes accentuées ajoutées à `FORMAT_LONGUEUR`, un seul dict module-level donc correctif appliqué aux deux points d'usage (`build_journalistic_brief()`, `build_prompt()`) automatiquement. Vérifié fonctionnellement (les 3 nouvelles clés mappent bien vers la même plage que leur équivalent sans accent). Aucune correction rétroactive des articles déjà publiés avec ce défaut (même décision que le point ci-dessus — cosmétique, non consommé en aval). |

---

*Fin du backlog maître. Pour la prochaine session : reprendre directement
depuis la Partie 1, dans l'ordre proposé (🔴 en premier).*
