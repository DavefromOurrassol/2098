# Backlog maître — Ourrassol 2098
*Consolidé le 9 août 2026, à partir de l'ensemble des handoffs/backlogs du
1er août au 9 août 2026. Remplace tous les documents précédents comme
référence unique. Chaque chantier a un nom stable — à réutiliser tel quel
dans les prochaines sessions pour éviter toute nouvelle divergence de
nommage.*

---

# PARTIE 1 — CHANTIERS OUVERTS (à traiter)

## 🔴 1. Chantier `annee_fin`
**28 fiches instances sans date de fin renseignée**, alors que leur
`trajectoire` l'implique normalement (`transformé`/`disparu`). Identifié
le 8 août comme le même trou de conception qu'avait `annee_debut` avant
correction — jamais construit.

Sous-points déjà identifiés à l'ouverture de ce chantier (notes d'une
session antérieure à consolider ici) :
- **Concentration sur l'année 2041** — 36 % des 28 fiches, à mettre en
  regard de la concentration déjà connue sur l'ensemble du vault (2041 =
  157/710 fiches, 22 %). Cause à diagnostiquer avant de corriger.
- **Encodage portugais cassé dans certains slugs** — mineur, jamais
  traité, à corriger dans la foulée si le chantier `annee_fin` touche
  aux mêmes fiches.
- **Répartition inégale par scénario** (19/28 sur `breakdown`) — jugée
  probablement normale (`breakdown` = scénario le plus mature/actif),
  pas creusée davantage, pas bloquante.

✅ **Un sous-point de ce diagnostic initial est résolu** : l'incohérence
`ascendant`+`transformé` sur `zones_extractivistes_corridors_eco_
communalism` (qui avait initialement motivé l'ouverture de ce chantier)
est réglée par le chantier `trajectoire` (voir Partie 2, clos le 9 août)
— un seul champ ne peut plus porter cette contradiction.

**État au 9 août (en cours)** : `fix_annee_fin_manquant.py` construit et
testé (modèle repris de `fix_annee_debut_placeholder.py`, sans ancrage
sur l'état du monde réel — non pertinent pour une date de fin fictive,
seulement le registre du scénario). Dry-run sur `breakdown` (19 fiches)
concluant — concentration de justifications sur quelques jalons du
registre (2061, 2057, 2053) vérifiée légitime, raisonnement distinct par
fiche à chaque fois, pas de convergence artificielle. Run réel sur
`breakdown` puis les 5 autres scénarios restant à faire.

**Trouvaille en marge, ajoutée en point 8 ci-dessous** : doublon
potentiel d'entité repéré sur `breakdown` en cours de traitement.

**Outil de diagnostic** : `audit_etat_temporel_fin.py`, corrigé le
9 août pour lire `trajectoire` (au lieu de l'ancien `etat_temporel`),
testé et fonctionnel — sert à mesurer l'avancement de ce chantier.

---

## 🔴 2. Décision `type_relation_dominante`
**Ouvert depuis le 3 août, jamais tranché malgré 6 sessions successives
qui l'ont reporté.** Candidat solide pour être ajouté au prompt de
génération d'articles — rempli à 100 % sur les fiches d'origine
(contrairement à `alliances`/`oppositions`, souvent vides avant leur
propre chantier de correction). Décision à prendre avec David : l'ajouter
au prompt ou non, et si oui, comment.

**C'est l'item du backlog le plus ancien encore ouvert** — à traiter en
priorité pour ne pas le reporter une septième fois.

---

## 🟡 3. Vérifier `metadata["longueur"]` réutilisé en aval ?
**Ouvert depuis le 3 août**, jamais vérifié. Bug corrigé le 3 août sur le
calcul de `metadata["longueur"]` (n'appliquait pas l'override de config).
Reste à vérifier si ce champ sert à autre chose que l'affichage
`--dry-run` (frontmatter d'articles déjà publiés, stats, filtrage côté
`api.py`) — si oui, les fiches publiées avant le correctif pourraient
porter une étiquette de longueur incohérente avec leur contenu réel (pas
un problème de qualité du texte, juste une métadonnée potentiellement
fausse). Nécessite que David vérifie `api.py` pour trancher si un script
de correction rétroactive est utile.

---

## 🟡 4. Test navigateur des entrées GUI modifiées
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

**Suggestion** : plutôt qu'un test exhaustif de chaque entrée
séparément, une seule session dédiée "clic à travers tout le GUI"
pourrait clore ce point une fois pour toutes.

---

## 🟡 5. Même diagnostic `annee_debut`/`ancrage_reel` sur les événements ?
**Question posée le 8 août, jamais explorée.** Le chantier `annee_debut`
a porté exclusivement sur les instances. Les événements
(`inject_custom_events.py`, `registre_evenements.md`) ont-ils le même
problème structurel ? Diagnostic à faire en premier, avant de décider si
la même approche (bande de traçabilité graduée, `ancrage_reel`) s'y
applique.

---

## 🟡 6. Dimension temporelle pour la génération automatique
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

## 🟢 7. Documentation à corriger (chantier `trajectoire`, 9 août)
`USER_MANUAL_COMPLET.md` doit être mis à jour sur un point tranché
aujourd'hui : `generate_instances.py` est confirmé **actif** (usage
distinct et complémentaire de `create_entities_and_instances.py` —
backfill d'instances pour des entités déjà créées), pas legacy comme le
manuel le décrit actuellement. Ce backlog maître documente déjà la
correction ; reste à la répercuter dans le manuel lui-même.

---

## 🟢 8. Doublon potentiel d'entité — `arctic_passage_authority` / `autorite_passage_arctique`
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

## 🟢 9. Nettoyage `test_durcissement_policy_reform`
**Résidu mineur du 8 août**, identifié le 9 août. 7 fiches instances de
`policy_reform` référencent encore `[[test_durcissement_policy_reform]]`
en alliance/opposition alors que cette fiche n'existe plus (ni dans
`entites/`, ni dans `instances/`) — wikilinks cassés, sans impact
fonctionnel, à nettoyer manuellement ou via un script `sed` ciblé.

---

## 🟢 10. Quatre reliquats jamais repris depuis la consolidation du 7 août
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

## 🟢 11. Renommage des YAML génériques par dossier
**En pause depuis fin juillet, jamais réévalué.** `queue.yaml`/
`processed.yaml`/`needs_review.yaml` répétés à l'identique dans
`entites_custom/`, `evenements_custom/`, `signaux_custom/` — décision de
renommage reportée (clarté vs coût de migration). Aucune urgence
identifiée à ce jour.

---

## ⚪ 12. Chantiers de fond, scopés mais non codés (pause longue durée)
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
| **Revalidation mode Semi-guidé** | 3 août | Les 7 champs du bug §3.7 confirmés appliqués ; bug annexe `metadata["longueur"]` trouvé (→ voir Partie 1 point 3 pour le suivi resté ouvert). |
| **Audit de complétude snapshot/variables** | 3 août | 4 pertes de contenu narratif trouvées et corrigées. |
| **Test de charge Semi-guidé à 6 entités** | 4 août | 58 948 caractères mesurés, structurellement borné. A débouché sur le chantier alliances/oppositions ci-dessous. |
| **Chantier alliances/oppositions** | 4-5 août | 356→0 fiche vide sur 426, réciprocité automatisée, root cause corrigée à la source (`enrich_minimal.py`), validation durcie partiellement, découverte et correction annexe de 284 fiches sans `statut` (vault à 710/710 cohérent). |
| **146 conflits de réciprocité alliances/oppositions** | 7 août | Règle "opposition prioritaire" implémentée et appliquée, 2 bugs découverts et corrigés (écrasement multi-conflits, rapports jamais réinitialisés), intégrée en continu à `enrich_minimal.py`, GUI mis à jour. |
| **`fix_alliances_oppositions.py` absent du GUI** | 7 août | Résolu par l'intégration GUI du chantier ci-dessus. |
| **Documentation `depends_on`** | 8 août | Fausse alerte — vérifié en détail, le mécanisme était déjà correctement décrit. Rien à corriger. |
| **Chantier `annee_debut`** | 8 août | 477 fiches bloquées à 2026 corrigées, outil de veille construit (`etat_du_monde_reel.md` + export/import), chantier de robustesse `ancrage_reel` mené en parallèle (bande graduée 10 ans), run `--all` confirmé par un passage à vide. |
| **`ancrage_reel` / traçabilité graduée** | 8 août | Ouvert et refermé dans la même session, 5 itérations de test réel. |
| **Statut de `generate_instances.py`** | 9 août | Confirmé **actif**, usage distinct de `create_entities_and_instances.py` (backfill vs création). Voir Partie 1 point 7 pour la mise à jour du manuel encore à faire. |
| **Factorisation `instance_generation_common.py`** | 9 août | ~20 fonctions dupliquées entre `generate_instances.py` et `create_entities_and_instances.py` unifiées en un seul module. 3 bugs de divergence réels corrigés au passage (`call_claude_json`, `validate_instance`, `MAX_TOKENS`). |
| **Chantier `trajectoire`** | 9 août | Fusion `etat_temporel`+`age_historique` en un axe unique + `est_clandestin` séparé. 710 fiches migrées, `validate.py` recalibré (bug C4 corrigé au passage), GUI mis à jour (menu `État`/`Clandestin` dans `create_entities`), `audit_etat_temporel_fin.py` adapté. |

---

*Fin du backlog maître. Pour la prochaine session : reprendre directement
depuis la Partie 1, dans l'ordre proposé (🔴 en premier).*
