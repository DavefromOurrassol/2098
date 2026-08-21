# Handoff — session du 15 août 2026

*Session menée principalement via chat avec Claude (hors GUI/terminal
direct sur la majorité des étapes), David exécutant les commandes et
scripts sur son vault et rapportant les résultats. Trois chantiers
traités : Partie 1 point 2 du backlog (`forces_attractives`/
`forces_repulsives`, mené à terme), un point mineur découvert en cours
de route (nom du gabarit entité), et le point 7 laissé ouvert le 14 août
("Les Veilleurs des Nappes Phréatiques", tranché et exécuté).*

---

## 1. `forces_attractives`/`forces_repulsives` — chantier complet

### Décision de conception

Analyse comparative programmatique des 12 fiches `variables/*.md`
(archive uploadée par David) : section `## 3. Dynamique interne`
systématiquement plus riche (4-8 items) que section
`## 4. Structure causale` (1-5 items, quasi toujours une paraphrase
compressée de la section 3, avec un artefact de formatage `snake_case`
cassé sur 2 fiches). **Décision de David : section 3 comme source de
vérité unique.**

### Développement

- `loader.py` : nouvelle fonction `_extract_forces_from_body()`
  (même convention regex que `_extract_indicateurs_from_body()`),
  câblée dans `load_variable()` — deux nouvelles clés
  `forces_attractives`/`forces_repulsives`.
- `prompt_builder.py` : `build_variables_context()` affiche les 4
  premiers items de chaque liste, par variable détaillée.
- Testé unitairement contre les 12 fiches réelles, puis en génération
  réelle via Flask (premier prompt complet inspecté directement).

### Trois problèmes découverts et corrigés en cours de validation réelle

**(a) Déséquilibre répulsif/attractif** — 0 force attractive sur les 3
premiers articles tests. Consigne de pilotage ajoutée dans
`build_variables_context()`, reformulée deux fois : d'abord descriptive
("à parts égales", insuffisante), puis contrainte concrète ("au moins
un fait/acteur/citation illustrant une force attractive sur l'ensemble
de l'article" — portée clarifiée à la demande de David pour éviter une
lecture "une par variable" trop lourde). Confirmée fonctionnelle sur le
dernier test (article `breakdown`, "Opération Baraka").

**(b) Récurrence anormale de l'entité `terminal_kharg_data_haven`**
comme sujet principal sur 4/4 générations, deux scénarios différents,
thématique `actualites_a_la_une` à chaque fois. Cause exacte :
`filter_instances_for_thematique()` (`loader.py`) — score
structurellement avantageux (impact systémique élevé + recoupement
constant avec les zones de cette thématique), jamais départagé par la
rotation à mémoire existante (`_select_least_used_instances()`), qui ne
joue que sur l'égalité de score **stricte**. Corrigé par
`_score_bucket()` : tolérance de tranche (`INSTANCE_SCORE_TOLERANCE =
2.0`), calculée relativement au score maximum du lot pour éviter un
effet de bord d'arrondi identifié en testant une première version.
Validé sur cas synthétiques (recul 15/15 → 4/15 sur écart réaliste,
15/15 préservé sur écart réellement dominant) puis en conditions
réelles sur `eco_communalism` (Kharg-9 relégué à une mention
secondaire).

**(c) `climat_environnement_global` totalement absente du texte sur
5/5 générations**, malgré vérification manuelle qu'elle était
systématiquement dans le top 6 détaillé (`priority[:MAX_VARIABLES_
DETAIL]`, reconstruit à la main avec les vraies données de
`thematiques/actualites_a_la_une.md`) — donc pas un problème de
troncature côté code. Le LLM recevait la donnée en détail mais ne la
mobilisait jamais (probablement un effet de position dans un prompt de
56-62k caractères, combiné à l'orientation narrative de la thématique).
Nouvelle consigne de couverture minimale des variables pilotes (tag
`[VARIABLE PILOTE]`, une résonance exigée par variable). Premier test
positif (article `breakdown`, première résonance climatique en 6
articles) — **un seul échantillon, à confirmer sur plusieurs
générations futures**.

### Statut

**Considéré terminé par David.** Réserve explicite : le correctif (c)
n'a qu'un test positif, pas encore consolidé dans la durée.

---

## 2. Gabarit entité — nom corrigé, déplacé vers `/templates`

Le point Partie 2 du 14 août ("`audit_broken_slugs.py` ne filtre pas le
gabarit") avait été noté avec le mauvais nom (`entite_template.md`,
français — jamais présent sur le vault). Recherche directe
(`find . -iname "*template*"`) a révélé le vrai nom : `entity_
template.md` (anglais). Filtre corrigé dans `audit_broken_slugs.py`.

David a ensuite déplacé le fichier vers `/templates` (cohérent avec
`instance_template.md`, déjà présent à cet emplacement depuis le
14 août) : `entites/entity_template.md` → `templates/entity_template.md`
(`git mv`).

**Vérification en amont avant déplacement** : grep exhaustif du projet
ne trouvant aucune référence codée en dur au fichier par son nom
littéral, mais révélant que deux scripts listaient `entites/*.md` sans
filtrer le gabarit : `gui/routes_dashboard.py` (total du dashboard) et
`generator/generate_instances.py` (chargement de toutes les fiches).
Ces deux points sont corrigés de facto par le déplacement, sans
modification de leur code. Confirmé indirectement par le compteur
global de `validate.py` (590 → 589 entités après déplacement) — **pas
vérifié fichier par fichier**, à garder en tête si un doute apparaît
plus tard sur le dashboard ou `generate_instances.py`.

Le filtre resté dans `audit_broken_slugs.py` est désormais un no-op
inoffensif (plus jamais de fichier à ce nom dans `entites/`) — pas
retiré, sans urgence.

**Documentation corrigée aux 4 endroits qui répétaient l'erreur** :
`BACKLOG_MASTER_9_AOUT.md` (×2), `HANDOFF_14_AOUT.md` (×3, non modifié
— document de session historique, erreur laissée en l'état comme
trace), `USER_MANUAL_COMPLET.md` (×1, corrigé).

---

## 3. "Les Veilleurs des Nappes Phréatiques" — décision tranchée, entité créée

### Décision

En tout début de session : **corriger et créer**, pas d'abandon.
Contenu jugé solide par Claude (ancrage géographique réel — nappes
phréatiques contaminées du Midwest, bassin du Congo —, cohérence forte
avec `eco_communalism`, rôle différencié, pas un doublon). David a
validé cette recommandation.

### Diagnostic avant correction

`category: mouvement` absente de `VALID_CATEGORIES`
(`create_entities_and_instances.py` : `IA, organisation, entreprise,
institution, infrastructure, réseau, humain, système, hybride, autre,
média, territoire`). `organisation` retenue comme catégorie de repli la
plus proche. Vérifié que `category` n'est utilisée nulle part dans
`prompt_builder.py` (`grep` sans résultat) — aucune influence sur le
contenu narratif généré par le LLM, uniquement une étiquette de
classification interne (stats de couverture, validation).

### Dette historique découverte au passage

Avant de corriger, audit élargi
(`grep -h "^category:" entites/*.md | sort | uniq -c`) : **4 autres
fiches déjà présentes dans le vault avec `category: mouvement`** —
`coalition_vivant`, `collectifs_du_seuil`,
`internationale_travailleurs_augmentes`, `mouvement_racines_vivantes`.
Aucune n'a de champ `date_generation` (contrairement aux entités
récentes du pipeline custom), suggérant une origine du socle initial de
juin 2026, antérieure à l'existence du garde-fou `VALID_CATEGORIES` —
pas une faille de couverture active du pipeline actuel. Confirmé par un
deuxième audit sur les files d'attente (`entites_custom/queue.yaml`/
`processed.yaml`/`needs_review.yaml`) : une seule occurrence de
`mouvement` au total, celle déjà en cours de traitement.

Ces 4 fiches généraient déjà 4 avertissements silencieux à chaque
`validate.py` (`category` vérifiée en warning, pas en erreur
bloquante). **Corrigées en lot** :
```bash
sed -i '' 's/^category: mouvement$/category: organisation/' entites/coalition_vivant.md entites/collectifs_du_seuil.md entites/internationale_travailleurs_augmentes.md entites/mouvement_racines_vivantes.md
```
Confirmé par `grep -l` (vide) et `validate.py` (0 erreur, 0
avertissement, avant même la création de la nouvelle entité).

### Création de l'entité

`entites_custom/needs_review.yaml` corrigé (`category: mouvement` →
`organisation`), remis en file via `requeue_needs_review.py`, entité
créée via `create_entities_and_instances.py --mode custom`.

Cycle post-injection complet enchaîné automatiquement
(`extract_localisation.py` → `review_localisation.py --auto-resolve` →
`validate.py`) :

- **5 instances créées sur 6** : `breakdown`, `fortress_world`,
  `new_sustainability`, `policy_reform`, `reference`.
- **Localisations résolues** : 3 extraites directement (Sahel via 2
  instances, bassin du Congo), 2 ambiguës auto-résolues (Massif Central
  pour l'extension européenne, bassin du Congo confirmé pour
  `new_sustainability`) — 0 review manuelle restante.
- **1 échec** : `eco_communalism` (le `scenario_ref` d'origine de
  l'idée). Le garde-fou `ancrage_reel` a **correctement bloqué une
  hallucination** — le LLM citait un événement fictif du registre du
  scénario ("mouvement mondial de souveraineté hydrique locale") comme
  s'il s'agissait d'un fait réel et vérifiable de 2026.
- **1 avertissement mineur** sur l'instance `reference` : alliance
  filtrée pointant vers un slug invalide
  (`reseau_des_capteurs_citoyens_reference`), probablement une entité
  inventée par le LLM sans existence réelle dans le vault — filtrage
  correct du garde-fou, rien à corriger.

`validate.py` final : **0 erreur, 0 avertissement** (590 entités, 737
instances).

### Reste en attente

**Retenter la génération de l'instance `eco_communalism`** pour "Les
Veilleurs des Nappes Phréatiques" — priorité pour le tout début de la
prochaine session.

---

## 4. Point mineur repéré, non traité — pour référence future

`articles/{scenario}/_index.md` (généré par `generate_series.py`,
fonction `build_index()`) est réécrit en mode écrasement à chaque run
sur un même scénario — liste seulement les articles du dernier batch,
pas un cumul historique. Repéré en discussion, pas vérifié comme
gênant en pratique à ce jour. Ajouté en Partie 2 du backlog (points
mineurs, sans action requise pour l'instant).

---

## 5. Fichiers livrés cette session

- `loader.py` — `_extract_forces_from_body()`, câblage dans
  `load_variable()`, `_score_bucket()` + refonte de
  `_select_least_used_instances()` (tolérance de rotation).
- `prompt_builder.py` — câblage des forces dans
  `build_variables_context()`, consigne d'équilibre attractif/répulsif,
  consigne de couverture des variables pilotes.
- `audit_broken_slugs.py` — nom du gabarit corrigé
  (`entity_template.md`).
- `needs_review.yaml` — catégorie corrigée pour "Les Veilleurs des
  Nappes Phréatiques".

**Redémarrage Flask requis** après changement de `loader.py` — piège
rencontré en session : un premier test de génération a tourné sur
l'ancienne version du fichier (Flask non redémarré), donnant un faux
négatif sur l'efficacité du fix Kharg-9. À rappeler systématiquement
pour tout changement dans `loader.py`, pas seulement `app.py`/
`scripts_config.json`.

---

## 6. Point de reprise suggéré pour la prochaine session

1. **Priorité immédiate** : retenter l'instance `eco_communalism`
   manquante pour "Les Veilleurs des Nappes Phréatiques".
2. **Confirmer dans la durée** le correctif (c) du chantier forces
   (couverture des variables pilotes) — un seul test positif à ce
   stade, idéalement sur plusieurs générations et plusieurs thématiques
   différentes de `actualites_a_la_une`.
3. Chantiers Partie 1 du backlog toujours ouverts, sans changement de
   statut cette session : point #1 (validation retry longueur, 🟡, sans
   urgence), P17 (fiabilité `mistral-small`), Bug #27 (plausibilité
   logistique inter-zones), renommage YAML génériques, troncatures JSON
   génération instances — tous gardés pour plus tard sur décision
   explicite de David lors des sessions précédentes, non rouverts cette
   session.
