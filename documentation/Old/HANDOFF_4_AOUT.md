# HANDOFF — session du 4 août 2026 (à uploader dans le nouveau chat)

*Session en deux temps : (1) test de charge du point de reprise laissé
ouvert le 3 août — impact taille du prompt en mode Semi-guidé à 6
entités, avec les 4 ajouts de l'audit de complétude — qui a débouché sur
un diagnostic imprévu (`alliances`/`oppositions` vides sur la quasi-
totalité du vault) ; (2) conception, développement et déploiement partiel
d'un script de correction ciblée, `fix_alliances_oppositions.py`, testé
en conditions réelles sur `policy_reform` (77 fiches) avant lancement
`--all` sur les 5 scénarios restants en fin de session.*

---

## 1. Point de reprise — test de charge Semi-guidé à 6 entités

**Testé en conditions réelles** (`generate.py --dry-run --scenario
policy_reform --thematique sciences_technologies --ligne-editoriale
opposition`, le scénario le plus chargé).

**Résultat : 6/6 entités filtrées, 4/4 ajouts de l'audit du 3 août tous
présents et corrects** — `Responsabilités`/`Signes distinctifs` affichés
en entier sur les 6 entités (aucune troncature), `→ Déroulement`
(realisation) présent sur les 8 événements custom en détail, Ruptures
majeures (3, plafond respecté) affichées avant Ruptures structurantes (4,
plafond respecté).

**Taille du prompt mesurée : 58 948 caractères** (2 742 système + 56 206
user), soit ~14 700 tokens estimés — au-dessus de la fourchette
40k-52k caractères observée le 3 août sur d'autres scénarios (+13% par
rapport au max précédent), mais **structurellement bornée** : la
croissance vient uniquement de la section entités, plafonnée à 6, donc
ce coût est désormais fixe et ne grossira pas avec le vault. Pas
d'alarme, juste confirmation empirique attendue par la décision du 3
août (§3 du backlog) de ne pas ajuster les plafonds avant d'avoir des
chiffres réels — ce test fournit ce chiffre.

**Point mineur relevé en passant, non un bug** : sur les 6 entités
affichées, une seule (Consortium Nexus-Calcul) n'avait ni `Alliés` ni
`Opposants` dans le prompt généré. Vérification faite sur la fiche
source : `alliances: []` et `oppositions: []` dans le frontmatter
lui-même — le prompt reflétait fidèlement une donnée vide, pas un bug
d'affichage. Mais la fiche décrit pourtant des rivaux clairs en texte
libre dans `tensions_narratives` ("blocs souverainistes non-signataires",
"régulateurs européens"), ce qui a motivé une investigation plus large.

---

## 2. Diagnostic — pourquoi `alliances`/`oppositions` est vide sur la quasi-totalité du vault

**Root cause identifiée dans `enrich_minimal.py`** : le prompt
d'enrichissement construit une section "GÉOGRAPHIE DU SCÉNARIO (slugs
valides)" (`build_geographie_summary()`) pour que le LLM choisisse
`localisation.zone` correctement — mais **aucune section équivalente
n'existe pour les instances/entités**. L'instruction dit "uniquement des
slugs d'instances réelles de ce scénario, ou tableau vide `[]`", sans
jamais fournir au LLM la liste sur laquelle piocher. Résultat : le LLM,
prudent, renvoie `[]` chaque fois que son texte source (`entite_body`,
`role_dans_scenario`) ne mentionne pas déjà, par coïncidence de
rédaction, un nom d'entité assez précis pour être transformé en slug
plausible.

**Mesure exacte sur le vault réel** (script Python one-shot, parsing
identique à `parse_md()` d'`enrich_minimal.py`) :
- **356 / 426 fiches `officialise_enrichi` (83,6 %)** ont `alliances` ET
  `oppositions` vides.
- Distribution par type : pas de biais marqué vers les entités abstraites
  (institutions/infrastructures) comme l'hypothèse initiale le
  supposait — `organisation` (126) et `réseau` (90) sont majoritaires
  parmi les 356, exactement les types qui *devraient* avoir des rivaux
  nommés. L'hypothèse "texte source trop abstrait" a été explicitement
  invalidée par cette mesure.
- **`type_relation_dominante`, `annee_debut`, `annee_fin` sont remplis à
  100 % sur les 426 fiches**, y compris sur les 356 concernées — logique,
  puisque ces champs ne dépendent pas d'un slug validable contre une
  liste que le LLM n'a jamais reçue.

**Conclusion actionnable** : `alliances`/`oppositions`, tel que conçu, est
structurellement quasi inutilisable (vide dans 5 cas sur 6), pas un
problème de richesse de rédaction des fiches archétypes.

---

## 3. Décisions prises avec David avant développement

1. **Correction ciblée**, pas réenrichissement complet des 356 fiches —
   ne redemander au LLM QUE `alliances`/`oppositions`, laisser tous les
   autres champs déjà écrits (`responsabilites`, `description_
   journalistique`, `signes_distinctifs`, `tensions_narratives`, etc.)
   strictement intacts.
2. **Passe de réciprocité à prévoir** : si A cite B en alliance/
   opposition, B doit citer A en retour.
3. **Conflits de réciprocité (relation contradictoire des deux côtés) :
   laissés tels quels**, jamais résolus automatiquement — asymétrie de
   perception acceptée comme texture narrative plausible plutôt que
   comme anomalie à corriger.
4. **Vérifier le budget avant un run complet** — via `--limit` sur un
   petit échantillon avant de lancer à grande échelle.

---

## 4. `fix_alliances_oppositions.py` — nouveau script livré

**Conception** : ne touche jamais `enrich_minimal.py` en production
(nouveau script séparé, mêmes conventions `VAULT_ROOT`/`parse_md`/
`llm_client.py`). Deux passes :

1. **Passe LLM ciblée** — prompt minimal : contenu déjà enrichi de la
   fiche (rôle, responsabilités, tensions) + liste réelle des autres
   instances du scénario (l'ingrédient manquant, construite via
   `build_scenario_instances_index()`/`build_instances_summary()`,
   nouvel équivalent de `build_geographie_summary()` mais pour les
   instances). Validation stricte (slug hors liste = erreur bloquante,
   pas juste un warning comme dans `enrich_minimal.py`, puisque le LLM
   n'a plus d'excuse pour halluciner). Patch chirurgical du frontmatter
   (regex ciblée sur `alliances:`/`oppositions:`, aucune réécriture
   complète du YAML — tous les autres champs, y compris ceux à
   formatage multi-lignes, restent identiques au caractère près) + ajout/
   mise à jour de la section `## Relations` dans le corps Markdown
   (wikilinks, même style que `write_enriched_fiche()` de `enrich_
   minimal.py`).
2. **Passe de réciprocité** (locale, aucun appel LLM) — scanne toutes les
   instances du scénario après la passe 1, complète les relations
   manquantes côté cible, détecte et consigne les conflits dans
   `documentation/need_action/fix_alliances_conflits_reciprocite.md`
   sans jamais les corriger automatiquement.

**Tests avant déploiement** : patch chirurgical vérifié sur la vraie
fiche `consortium_nexus_calcul_policy_reform.md` (diff : uniquement les 2
clés + section Relations ajoutée, YAML re-parsable, 28 clés frontmatter
préservées) ; passe de réciprocité testée sur un cas synthétique à 3
entités avec un conflit délibéré (conflit bien détecté des deux côtés,
aucune fiche en conflit modifiée, la 3e fiche complétée correctement).

---

## 5. Déploiement réel — `policy_reform`

**Test à 5 fiches en `--dry-run --limit 5`** : 5/5 réussies (2 avec
1 retry), 0 échec. Coût mesuré : ~6 680 tokens/fiche en moyenne (retries
inclus) via Mistral (`mistral-large-latest`, tier "strict" actuel).
Extrapolation aux 356 fiches du vault entier : ~2,38M tokens.

**Run réel complet sur `policy_reform`** (77 fiches concernées) :
- **Passe LLM : 75/77 réussies, 2 échecs.**
  - `front_de_souverainete_biologique_eurasiatique_policy_reform` :
    persistait à proposer `hub_europeen_de_regulation_policy_reform` en
    opposition — confusion apparente entre un slug de **zone
    géographique** ("Hub Européen de Régulation") et un slug
    d'**instance**. La validation a eu raison de rejeter (le slug
    n'existe pas dans la liste d'instances fournie), mais 3 tentatives
    n'ont pas suffi à corriger le LLM.
  - `institut_de_modelisation_hydrologique_de_kinshasa_policy_reform` :
    **bug du script**, pas du LLM — `max_tokens=600` trop bas pour cette
    fiche, dont la réponse (probablement 8-10+ relations, comme observé
    sur d'autres fiches du même run) a été tronquée en plein milieu d'un
    slug, cassant le parsing JSON. **Corrigé en cours de session** :
    `max_tokens` porté de 600 à 1500 dans `call_llm_json()`.
- **Passe de réciprocité : 91 fiches complétées, 26 conflits détectés**,
  tous consignés dans le rapport, aucun résolu automatiquement (conforme
  à la décision §3.3).
- **Retraitement des 2 échecs** (`--slug` ciblé, script corrigé) :
  Kinshasa a été retraité avec succès (bug de troncature résolu par le
  fix `max_tokens`). Confirmé par un relancement de `--scenario
  policy_reform` : **0 fiche restante concernée** — les 77/77 sont
  traitées.
- **Décision finale sur les 26 conflits** : confirmée par David —
  **laissés tels quels**, asymétrie assumée. Pas de correction
  automatique codée.

---

## 6. Premier run `--all` — crash sur panne API transitoire, corrigé

David a lancé `python3 fix_alliances_oppositions.py --all` pour traiter
les 5 scénarios restants (`breakdown`, `fortress_world`,
`new_sustainability`, `eco_communalism`, `reference`, ~279 fiches
estimées). **Le run a crashé** avec une exception non gérée : erreur 503
transitoire de l'API Mistral (`upstream connect error... Connection
refused`) remontée sans filet jusqu'à faire planter tout le script.

**Rassurant** : aucune perte de données — le script écrit fiche par
fiche au fil de l'eau, donc tout ce qui avait été traité avant le crash
était déjà persisté sur disque, et le script est naturellement
"resumable" (`find_target_fiches()` ne renvoie que les fiches encore
vides).

**Bug corrigé avant relance** : `process_fiche()` n'attrapait que
`ValueError` (erreurs de contenu), pas les exceptions transitoires
(`RuntimeError` levée par `llm_client.py` sur panne API). Correctifs
apportés :
- Nouveau `call_llm_json_resilient()` — retry avec backoff progressif
  (5s, 10s) sur les pannes transitoires (jusqu'à 3 tentatives), distinct
  du mécanisme de correction de contenu déjà existant (`MAX_FIX_
  ATTEMPTS`, qui reste inchangé pour les erreurs de validation).
- Élargissement des `except` de `ValueError` à `Exception` dans
  `process_fiche()`, pour qu'une panne persistante marque seulement la
  fiche en cours comme échec au lieu de remonter et tuer le script.
- Filet de sécurité supplémentaire dans `run_scenario()` : même une
  erreur totalement imprévue sur une fiche (I/O, etc.) ne peut plus
  interrompre le traitement des suivantes.

Comportement vérifié par test synthétique (panne simulée qui se résout
après 2 tentatives → succès sans crash ; panne persistante au-delà des 3
tentatives → exception propre, attrapable, fiche marquée en échec sans
tuer le run).

---

## 7. Relance `--all` — succès, chantier clos

David a relancé `python3 fix_alliances_oppositions.py --all` avec le
script corrigé. **Run allé au bout sans nouveau crash.**

**Vérification finale sur le vault entier** (426 fiches
`officialise_enrichi`, même méthode de mesure que le diagnostic
initial) :

```
Total fiches officialise_enrichi : 426
Encore vides : 0 (0.0%)
```

**356 → 0 fiche vide.** Les cas d'échec initiaux de `policy_reform`
(Kinshasa, l'entité eurasiatique confondant zone et instance) ont
été retraités avec succès dans ce run final — le vault entier est à 0
fiche vide, sans exception résiduelle documentée.

**Réciprocité, chiffres finaux tous scénarios confondus** : **563
fiches complétées, 146 conflits détectés** — proportionnellement dans la
même fourchette que sur `policy_reform` seul (~26 % de conflits par
rapport aux complétions, contre ~29 % sur `policy_reform` isolément),
donc pas un signal d'anomalie propre aux 5 nouveaux scénarios.

**Décision de David sur les 146 conflits** : laissés tels quels pour
l'instant, comme sur `policy_reform`. Contrairement au 26 conflits de
`policy_reform` (tranchés définitivement comme "asymétrie assumée"),
David a explicitement laissé la question ouverte pour ce chiffre plus
large — *"on verra comment on règle ça pour la suite"*. Pas une
clôture définitive de la question, juste un statu quo assumé pour
l'instant. Voir §8.

---

## 8. Fichiers livrés cette session

`fix_alliances_oppositions.py` — script complet, deux rounds de
correction en cours de route :
1. `max_tokens` porté de 600 à 1500 (troncature JSON sur les fiches à
   beaucoup de relations) ;
2. Résilience aux pannes API transitoires (retry/backoff sur erreurs
   réseau, filet de sécurité au niveau de la boucle scénario).

Aucune modification faite aux scripts de production existants
(`enrich_minimal.py`, `prompt_builder.py`, `loader.py`, `snapshot.py`
n'ont pas été touchés cette session).

---

## 9. Point de reprise suggéré pour la prochaine session

1. **Décider du traitement à long terme des 146 conflits de
   réciprocité** — question explicitement laissée ouverte par David
   (§7). Trois pistes esquissées dans `BACKLOG_CONSOLIDE_4_AOUT.md`
   §1.1 : laisser définitivement, résoudre manuellement au cas par cas,
   ou coder une règle de priorité automatique (alliance vs opposition).
   Aucune action requise tant que la décision n'est pas prise.
2. Reste du backlog historique inchangé — voir
   `BACKLOG_CONSOLIDE_4_AOUT.md`.
