# Backlog consolidé Ourrassol 2098 — état au 4 août 2026

*Reconstitué à partir de `BACKLOG_CONSOLIDE_3_AOUT.md` et de
`HANDOFF_4_AOUT.md`. Objectif inchangé : ne garder que ce qui est
réellement encore ouvert.*

---

## 0. Nouveautés du 4 août 2026 — résumé actionnable

Le point de reprise n°1 laissé ouvert le 3 août est **clos** :

1. ✅ **Test de charge Semi-guidé à 6 entités** (§6.1 du 3 août) — testé
   en conditions réelles sur `policy_reform`. Les 4 ajouts de l'audit du
   3 août tous confirmés présents et corrects sur les 6 entités
   simultanées. Taille du prompt mesurée : 58 948 caractères (~14 700
   tokens), au-dessus de la fourchette précédente mais structurellement
   bornée (plafond de 6 entités = coût fixe, ne grossira pas avec le
   vault).

Ce test a débouché sur un **chantier majeur non planifié, mené à terme
dans la même session** : diagnostic puis correction complète du champ
`alliances`/`oppositions`, vide sur 356/426 fiches instances (83,6 % du
vault) au départ. Détail complet en `HANDOFF_4_AOUT.md` §2-8.

2. ✅ **Chantier alliances/oppositions — clos, vérifié sur le vault
   entier** : `fix_alliances_oppositions.py` livré, testé, corrigé deux
   fois en cours de route (troncature JSON par `max_tokens` trop bas ;
   crash du run `--all` sur une panne 503 transitoire de l'API Mistral,
   corrigé par un mécanisme de retry/backoff sur les pannes réseau,
   distinct des retries de contenu déjà existants). Déployé sur les 6
   scénarios. **Vérification finale sur les 426 fiches du vault : 0
   fiche encore vide (contre 356 au départ).** 563 relations complétées
   au total par la passe de réciprocité, **146 conflits d'asymétrie
   détectés et volontairement laissés en l'état** (décision de David :
   asymétrie de perception acceptée comme texture narrative, pas une
   anomalie à corriger) — voir point 1.1 ci-dessous pour la question
   encore ouverte sur ces conflits.

**Fichiers livrés** : `fix_alliances_oppositions.py` (nouveau, version
finale avec les 2 correctifs). Aucun script de production existant
modifié cette session.

---

## 1. Ce qui reste réellement à faire

### 1.1 — Que faire des 146 conflits de réciprocité, à terme ?
Décision du 4 août : laissés tels quels pour l'instant, pas de correction
automatique. Mais la question de fond reste ouverte — "on verra comment
on règle ça pour la suite" (David, 4 août). Pistes possibles à
explorer/trancher lors d'une prochaine session, sans urgence :
- Laisser définitivement (asymétrie assumée comme feature narrative) ;
- Résolution manuelle cas par cas via le rapport
  `documentation/need_action/fix_alliances_conflits_reciprocite.md` ;
- Règle automatique à définir (ex. l'opposition l'emporte toujours sur
  l'alliance, ou l'inverse) — nécessiterait une nouvelle passe de code
  si cette voie est choisie.
Aucune action requise tant que David n'a pas tranché.

### 1.2 — Cas d'échec LLM ponctuel : confusion zone/instance
Sur `policy_reform`, une fiche (`front_de_souverainete_biologique_
eurasiatique_policy_reform`) avait persisté sur 3 tentatives à proposer
un slug de **zone géographique** (`hub_europeen_de_regulation_policy_
reform`) comme si c'était une instance, avant d'être retraitée avec
succès dans le run `--all` final (le vault est à 0 fiche vide, donc ce
cas a fini par passer). Pas d'action requise puisque résolu, mais motif
à garder en tête si le même symptôme réapparaît sur un futur
enrichissement — pourrait indiquer que le prompt gagnerait à lister
explicitement les slugs de zones à ne PAS utiliser, en plus des slugs
d'instances valides.


### 1.3 — Décider du sort de `type_relation_dominante`/`annee_debut`/`annee_fin`
Inchangé depuis le 3 août — trouvé lors de l'audit de complétude comme
non redondant avec le contenu déjà affiché dans le prompt de génération
d'articles. Renforcé par le diagnostic du 4 août : `type_relation_
dominante` est rempli à 100 % sur les 426 fiches (contre 16,4 % pour
`alliances`/`oppositions` avant correction), ce qui en fait un candidat
plus solide qu'estimé le 3 août. Décision toujours à prendre avec David.

### 1.4 — Vérifier si `metadata["longueur"]` (bug corrigé le 3 août) est réutilisé en aval
Inchangé depuis le 3 août. David doit vérifier `api.py` pour trancher si
un script de correction rétroactive est nécessaire sur les fiches déjà
publiées avant le correctif.

---

## 2. Gros chantiers volontairement en pause (pas oubliés, juste différés)

### 2.1 — Renommage des YAML génériques par dossier
Inchangé depuis le 3 août. Aucune urgence identifiée.

### 2.2 — P14 : passer le tier LLM `strict` vers `claude-sonnet-5` en prod
Différé sine die sur demande explicite de David (1er août). Note de
contexte du 4 août : `fix_alliances_oppositions.py` tourne actuellement
sur Mistral (`mistral-large-latest`, tier "strict" actuel) — les
observations de coût/qualité de ce chantier (retries, troncatures) sont
donc spécifiques à Mistral, à garder en tête si P14 est reconsidéré plus
tard.

### 2.3 — P20 : enrichissement frontmatter pour publication web future
Inchangé depuis le 3 août — scoping complet fait, rien codé.

### 2.4 — P21 : journaux oraux, orateurs itinérants
Inchangé depuis le 3 août — scoping complet fait, rien codé.

---

## 3. Points mineurs, non bloquants, sans action requise

- **P15** — `acteurs_hint_count` non plafonné en filtre dur. Inchangé
  depuis le 3 août.
- **`--force` du panneau `--scan-pending`** — inchangé.
- **`coverage_proposals_reference.yaml`** sans `.applied` — inchangé.
- **`/api/carte/appliquer_zone_topdown_suspecte`** — inchangé.
- **Champ `type` des zones géographiques** — inchangé.
- **Bloc `simulation`** sur les fiches variables — inchangé.
- **`constrained_variables`** — inchangé.
- **Incohérence documentation/code `forces_attractives`/`forces_
  repulsives`** — inchangé.
- **146 conflits de réciprocité alliances/oppositions, tous scénarios**
  (4 août, chiffre final après `--all`) — consignés dans
  `documentation/need_action/fix_alliances_conflits_reciprocite.md`,
  volontairement laissés en l'état pour l'instant. Décision de fond
  encore ouverte sur le traitement à long terme — voir §1.1.

---

## 4. Risque structurel identifié (pas un bug actif — rien à corriger tant qu'il ne se manifeste pas)

**Instances avec `injection.type == "custom"` non sélectionnées parmi
les `filtered_instances`** — inchangé depuis le 3 août. Aucun exemple
réel rencontré à ce jour.

---

## 5. Clarifications historiques (rappel, inchangé depuis le 3 août)

- **P8** (426 fiches `officialise_minimal`) — clos, traité intégralement
  le 27 juin 2026.
- **`noeud_mnemos_pannonie`** — clos depuis le 14 juillet (P23).
- **P18** (cohérence `routes_dashboard.py`) — clos le 13 juillet.
- **P22 signal 2** — fusionné et livré via P24 étape B.
- **P24 étape C** — absorbé par le système `chantiers_geographie.yaml`.
- **Point 4.5 (onglet GUI "Chantiers")** — livré et testé en conditions
  réelles le 26 juillet 2026, granularité "appliquer un seul chantier"
  ajoutée le 1er août 2026 (voir `recent_updates`, hors périmètre de ce
  backlog qui se concentre sur les points encore ouverts).
