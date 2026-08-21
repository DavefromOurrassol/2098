# HANDOFF — session du 12 août 2026 (à uploader dans le nouveau chat)

*Session en continuité directe de `HANDOFF_11_AOUT_SOIR.md` (clôture du
chantier "Test navigateur GUI", 6 bugs corrigés). Quatre volets : (1)
validation réelle du correctif signature itération 2, resté en suspens
depuis le 10 août ; (2) diagnostic demandé de longue date sur
`annee_debut`/`ancrage_reel` côté événements custom ; (3) nouveau
chantier construit et testé le jour même à partir de ce diagnostic —
ancrage des événements custom sur l'état du monde réel + validation
géographique ; (4) bug GUI trouvé par David sur le panneau Revue
(entrées entités/signaux affichées vides), deux correctifs successifs.
2 fichiers livrés, tous deux testés (dry-run pour l'un, conditions
réelles navigateur pour l'autre).*

---

## 1. Validation réelle du correctif signature (itération 2) — clos

Point ouvert depuis le 10 août, resté non tranché après un premier essai
raté le 11 août soir (échec avant génération sur une zone invalide).

Avec le correctif `zones_hier_journal` livré le 11 août soir, un run
`generate.py` en Semi-guidé avec une zone valide
(`geneve_bunker_institutions`) a pu aller jusqu'au bout. Résultat
confirmé : la signature apparaît **une seule fois**, toujours
**immédiatement sous la date**. Chantier clos — voir
`BACKLOG_MASTER_9_AOUT.md` Partie 4.

---

## 2. Diagnostic `annee_debut`/`ancrage_reel` sur les événements — clos

Question ouverte depuis le 8 août, jamais explorée : le chantier
`annee_debut` (8 août) avait porté exclusivement sur les instances. Les
événements custom ont-ils le même problème structurel ?

**Méthode** : lecture de `inject_custom_events.py`,
`fix_annee_debut_placeholder.py`, `loader.py`, et dépouillement réel de
`registre_evenements.md` (53 événements custom, tous scénarios).

**Constats** :
- **Structure de date différente** — un événement custom n'a qu'un
  champ `date` (année unique) et un `date_label` texte libre, pas de
  bande `annee_debut`/`annee_fin` comme les instances.
- **Aucune dérive de concentration observée** — pic max 11% sur une
  seule année (2041/2044/2047, 6/53 chacun), à comparer aux 22% sur
  2041 pour les instances avant correctif. Seulement 2/53 événements en
  2026 — rien de comparable au bug des 477 fiches d'instances bloquées
  au placeholder.
- **Mais aucun ancrage réel n'existait, dans aucun des deux modes** —
  `inject_custom_events.py` ne chargeait jamais `etat_du_monde_reel.md`,
  contrairement à la génération d'instances (`create_entities_and_
  instances.py`/`generate_instances.py`, qui ont `--ancrage-temporel`
  depuis le 8 août). Vérifié que custom et auto convergent vers le même
  prompt (`step2_develop_instance`) — un seul point de code à corriger
  couvre donc les deux modes.
- **`analyze_vault_coverage()` (couverture auto des événements) n'a pas
  de dimension temporelle** — même gap que `analyze_entity_coverage()`
  côté entités (backlog Partie 1 point 2, déjà connu) : ce diagnostic a
  confirmé que le gap touche identiquement les deux pipelines, pas
  seulement les entités comme supposé au 8 août. Portée du point 2
  élargie en conséquence dans le backlog.

**Décision prise** (échange avec David sur l'approche à privilégier) :
**pas** de reconstruction du mécanisme lourd des instances (bande
graduée `ancrage_reel` + anti-recyclage par shingle-matching) pour les
événements — jugé disproportionné vu le faible volume (53 événements)
et la nature différente du risque (proximité thématique diffuse entre
deux éléments fictifs, pas recyclage accidentel d'un jalon fictif dans
un champ censé être factuel). Un enrichissement de contexte au moment
de la génération suffit — voir point 3.

---

## 3. Nouveau chantier — cohérence événements custom / vault, registre, géographie, état du monde

Demandé par David suite au diagnostic ci-dessus, avec un cas concret en
tête : *peut-on injecter un événement proche dans le temps (ex. une
guerre mondiale en 2028) sans que le LLM improvise hors-sol ?*

### Implémentation — `inject_custom_events.py`, trois changements

1. **Import de `load_etat_monde_reel()` et
   `load_scenario_timeline_summary()`** depuis
   `instance_generation_common.py` — réutilisation pure, aucune
   duplication (mêmes chemins `REGISTRE_PATH`/`ETAT_MONDE_PATH`, même
   liste `SCENARIOS` déjà partagés par le module).
2. **Deux nouveaux blocs de contexte** injectés dans le prompt
   `step2_develop_instance` : `## CHRONOLOGIE RÉELLE DU SCÉNARIO` et
   `## ÉTAT DU MONDE RÉEL`, plus une règle explicite demandant au LLM de
   rester cohérent avec les deux — en particulier pour une date proche,
   où une escalade doit s'ancrer sur une tension réellement documentée
   plutôt que d'être inventée hors-sol. Le garde-fou existant
   `impossible_dans_scenario` reste la soupape si l'événement ne colle
   vraiment pas au scénario demandé.
3. **Validation mécanique de `zone_hint`** contre
   `load_all_zones_event(scenario)` (fonction déjà existante, jusque-là
   utilisée seulement côté mode auto) — refaite à **chaque itération**
   de la boucle scénarios, appel initial et retry inclus. Zone invalide
   pour ce scénario → avertissement console, repli sur "libre" plutôt
   que transmission telle quelle au LLM.

**Décision délibérée de ne pas ajouter davantage** : pas de garde-fou
mécanique bloquant sur le chevauchement thématique avec le registre
(type shingle-matching) — enrichissement de contexte seulement, cohérent
avec la pratique du projet de ne pas construire de mécanique de
calibration pour un problème non observé (risque de mauvaise
calibration déjà vécu sur le chantier longueur du 10 août : le
renforcement de prompt seul avait donné un résultat pire que la
référence).

**Couvre les deux modes** sans duplication de code : le mode auto
n'écrit que dans `queue.yaml`, l'injection réelle (donc l'appel à
`step2_develop_instance`) passe toujours par le mode custom via
`process_idea()`.

### Test — queue de 5 cas construite pour l'occasion

Une queue de test (`queue_test_robustesse.yaml`, artefact de test, pas
un livrable permanent) a été générée avec 5 idées, chacune ciblant un
mécanisme précis :

| Idée | Teste | Résultat |
|---|---|---|
| `escalade_sahel_2028_test` | Ancrage réel sur date proche (2028) | ✅ `note_coherence` cite explicitement les tensions hydriques/infrastructures documentées |
| `zone_invalide_test` | Garde-fou négatif (zone inventée) | ✅ Warning déclenché, repli sur "libre" |
| `zone_valide_test` | Garde-fou positif (`sahel_numerique_ligue`, réel) | ✅ Silence, zone utilisée comme ancrage |
| `controle_date_lointaine_test` | Non-régression (date lointaine, 2091) | ✅ Génération normale |
| `multi_scenario_zone_test` | Revalidation **par scénario** (même zone_hint sur `eco_communalism` + `breakdown`) | ✅ **Test le plus probant** — silence sur `eco_communalism` (zone valide), warning sur `breakdown` (zone absente) ; a aussi déclenché un vrai retry de validation, confirmant que le zone_hint validé (pas la version brute) est bien réutilisé |

**Note de méthode** : `--dry-run` sur ce script appelle réellement le
LLM (voir `USER_MANUAL_COMPLET.md` §0, piège transversal du 31 juillet —
seule l'écriture disque est sautée). Le test porte donc sur du contenu
réellement généré, pas simulé.

**Deux observations, pas des bugs** :
- La citation "tensions réelles documentées" (cas 1) reste à vérifier
  qualitativement — le mécanisme grounde bien mécaniquement (le bloc de
  contexte est transmis), mais un coup d'œil rapide à
  `etat_du_monde_reel.md` confirmerait que le texte produit s'appuie
  vraiment dessus plutôt que de juste sembler plausible.
- Sur les cas 2 et 5, le LLM a repris le texte de test dans le contenu
  narratif généré (ex. *"Test Fantôme des Zones Invalides"*) — normal
  puisque le champ `description` de ces idées de test parlait
  explicitement de la mécanique testée. Pour une vraie idée en
  production, éviter de mentionner la mécanique de test dans
  `description`.

**Non testé** : injection réelle (non dry-run) — le chemin d'écriture
disque n'a pas été touché par ce correctif, risque jugé faible, mais
reste à confirmer au premier usage réel.

---

## 4. Bug GUI — panneau Revue, slug/scénario/détail vides sur entités et signaux

**Symptôme signalé par David** : dashboard affiche 1 item en revue,
notification "1" sur l'onglet Revue confirmée, mais la ligne `ENTITES`
affiche `(entité)` / `—` / `—` sur les 3 colonnes au lieu du vrai
contenu.

**Cause** : `_read_needs_review_yaml()` (`app.py`) est un parseur YAML
maison ligne par ligne (sans PyYAML), construit à l'origine pour le
format événements/enrichissement (`- slug:`/`- idea:`, champs
`scenario:`, `date:`, `failed_scenarios:`, `errors:` en liste). Le
correctif du 2 août avait bien fait apparaître les sources
`entites_custom`/`signaux_custom` dans le panneau (jusque-là totalement
invisibles) — mais sans jamais leur apprendre à lire leurs propres
champs. Leur structure réelle (`idea.nom`, `idea.scenario_ref`,
`reason:` à plat) diffère du format d'origine et n'était reconnue par
aucune branche existante.

**Premier correctif** : reconnaissance de `nom:` (remplace le
placeholder de slug, seulement s'il en est encore un), `scenario_ref:`
et `reason:` (avec déséchappement naïf des quotes doublées YAML,
`''mouvement''` → `'mouvement'`). Testé directement contre le vrai
`needs_review.yaml` fourni par David : les 3 champs sortent corrects.

**Deuxième correctif, trouvé en répondant à une question de David sur
la couverture des 3 pipelines** (entités/événements/signaux) : les 3
scripts d'injection (`create_entities_and_instances.py`,
`inject_custom_events.py`, `inject_custom_signals.py`) ont chacun un
repli générique identique sur exception imprévue —
`{"error": str(e)}`, une clé **scalaire singulière**, jamais reconnue
par le parseur (seule la forme plurielle `errors:`/liste l'était).
Une entrée née de ce chemin, sur n'importe lequel des 3 pipelines,
aurait toujours affiché DÉTAIL vide même après le premier correctif.
Corrigé de la même façon, testé avec un cas simulé.

**Confirmé en conditions réelles dans le navigateur** par David, sur
l'entrée réelle ("Les Veilleurs des Nappes Phréatiques",
`category invalide : 'mouvement'`) — les 3 colonnes s'affichent
désormais correctement.

**Pas un bug résiduel** : `(entité)`/`(signal)` reste affiché quand un
rejet survient trop tôt pour que le LLM ait déjà produit un nom
(différence structurelle avec les entrées "post-génération") — comportement
attendu, pas un manque du parseur.

---

## 5. Fichiers livrés cette session

- **`inject_custom_events.py`** — les 3 changements du point 3
  (import, deux blocs de contexte, validation `zone_hint` par scénario
  sur l'appel initial et le retry).
- **`app.py`** — les 2 correctifs du point 4 (`nom:`/`scenario_ref:`/
  `reason:`, puis `error:` scalaire générique) dans
  `_read_needs_review_yaml()`.

**Chez David, à faire au prochain lancement** :
1. Remplacer `inject_custom_events.py` dans `generator/` et `app.py`
   dans `gui/`.
2. **Redémarrer Flask** (`app.py` modifié — contrairement à
   `inject_custom_events.py` seul, qui n'aurait rien nécessité de plus).
3. Vérifier que `etat_du_monde_reel.md` est à jour avant tout test
   portant sur une date proche, sans quoi le LLM retombera sur "aucun
   ancrage réel disponible".

---

## 6. Point de reprise suggéré pour la prochaine session

Backlog Partie 1, entièrement à jour dans `BACKLOG_MASTER_9_AOUT.md` —
**2 points 🟡 seulement**, aucun 🔴 :

1. Validation à plus grande échelle du retry sur la longueur des
   articles (10 août) — pas urgent.
2. Dimension temporelle pour la génération automatique (8 août,
   portée élargie le 12 août aux événements en plus des entités) — non
   codée.

Le reste (🟢/⚪) est mineur ou en pause longue durée — voir Partie 1
points 3 à 10 du backlog pour le détail.

**Suivi léger recommandé, pas urgent** : confirmer en conditions réelles
(non dry-run) que le correctif de cohérence événements custom du point 3
écrit correctement sur disque — la queue de test est prête si besoin
(`queue_test_robustesse.yaml`, déjà remplie avec des slugs de zone
réels).

**Rappel de méthode, toujours valable** : à chaque modification de
`scripts_config.json`, vérifier par diff programmatique qu'aucune entrée
en dehors de celle(s) visée(s) n'a été altérée. Sans objet cette
session (aucune modification de ce fichier), mais à reprendre dès la
prochaine session qui y touche.
