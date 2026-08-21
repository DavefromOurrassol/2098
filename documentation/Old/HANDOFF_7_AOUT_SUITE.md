# HANDOFF — suite de session du 7 août 2026 (à uploader dans le nouveau chat)

*Complète HANDOFF_7_AOUT.md (chantier réciprocité alliances/oppositions,
clos). Cette suite couvre le chantier point 1.2 du backlog, ouvert et
creusé en profondeur dans la même journée, avec un niveau de détail
volontairement dense — beaucoup de sous-étapes, de chiffres exacts et de
fichiers touchés en une seule session. Tests réels reportés au lendemain
(8 août). À uploader avec HANDOFF_7_AOUT.md +
BACKLOG_CONSOLIDE_7_AOUT_SUITE.md dans le nouveau chat, ainsi que tous les
fichiers listés en §12.*

---

## 1. Point de départ

Reprise du point 1.2 du backlog ("décider du sort de
type_relation_dominante/annee_debut/annee_fin — 100 % remplis sur les 426
fiches d'origine, candidat solide pour le prompt de génération
d'articles"). David a demandé de creuser en détail plutôt que de trancher
rapidement, avec un objectif explicite : *"je veux m'assurer que le
snapshot et la rédaction n'oublient pas de paramètres des fiches"*.

## 2. Étape 1 — Traçage snapshot/prompt_builder (fichiers demandés : snapshot.py, prompt_builder.py, loader.py + 4 fiches réelles)

Lecture ligne par ligne des trois fichiers du pipeline pour tracer le sort
exact des trois champs entre le frontmatter et le prompt final envoyé au
LLM de génération d'articles.

- **`loader.py` (lignes 717-719)** : lit correctement les trois champs
  avec fallback — `type_relation_dominante` → `"neutralité"` si absent,
  `annee_debut` → `2026` si absent, `annee_fin` → `None` si absent.
- **`snapshot.py`** : aucun filtrage. `filtered_instances`/`all_instances`
  transportent les dicts complets produits par `loader.py`, intacts. Les
  trois champs survivent donc jusqu'au snapshot.
- **`prompt_builder.py::build_entities_context()` (lignes 1399-1543)** :
  **c'est ici que ça cassait.** La fonction lit explicitement
  `etat_temporel`, `impact_systemique_global`, `description_
  journalistique`, `responsabilites`, `signes_distinctifs`,
  `tensions_narratives`, `alliances`, `oppositions` — mais jamais
  `type_relation_dominante`, `annee_debut`, ni `annee_fin`. Un commentaire
  à la ligne 1505 montre qu'un audit de complétude similaire avait déjà eu
  lieu le 3 août (corrigeant la même perte pour `responsabilites`/
  `signes_distinctifs`), sans détecter que ces trois champs avaient le
  même problème — angle mort resté 4 jours.

**Point structurel noté** : `type_relation_dominante` est UNE valeur par
fiche (tonalité dominante des relations en général), pas un tag par
allié/opposant précis.

## 3. Étape 2 — Premier patch de `prompt_builder.py`

Ajout d'une ligne `*Relation dominante* : <valeur> (depuis <annee_debut>)`
ou `(<annee_debut>–<annee_fin>)` si terminée, juste après les blocs
Alliés/Opposants dans `build_entities_context()`. Testé par exécution
isolée de la fonction sur les 2 vraies fiches fournies par David (BCUC —
`agence_stabilisation_climatique_breakdown`, et Mouvement Souveraineté —
`mouvement_pour_la_souverainete_territoriale_absolue_policy_reform`) :
rendu correct, `annee_fin` vide gérée sans plage vide affichée.

**Garde-fou ajouté ensuite** : `loader.py` peut retourner `"neutralité"`
(fallback si champ absent) qui est une chaîne non vide donc *truthy* —
risque d'afficher une donnée fabriquée comme si elle venait de la fiche.
Correctif : n'afficher la ligne que si `alliances` OU `oppositions` est
non vide (une tonalité relationnelle n'a de sens que s'il y a un réseau à
qualifier). Testé sur 3 cas synthétiques (aucune relation / relations
réelles / cas résiduel ambigu).

## 4. Étape 3 — Vérification empirique du risque de fallback sur le vault réel

Doute soulevé : le garde-fou couvre-t-il un vrai risque, ou une pure
hypothèse théorique ? Deux scripts d'audit créés et **exécutés par David
sur le vault réel** (710 fiches) :

**`audit_type_relation_dominante.py`** — résultat exact obtenu :
```
Fiches avec au moins 1 alliance/opposition réelle : 710
  - type_relation_dominante ABSENT du frontmatter  : 0
  - présent, valeur = 'neutralité' (choix réel)    : 17
  - présent, autre valeur (rivalité/conflit/...)   : 693
```

**`audit_dates_instances.py`** — résultat exact obtenu :
```
Fiches avec au moins 1 alliance/opposition réelle : 710
-- annee_debut --
  ABSENT du frontmatter : 0
  Présent, valeur = 2026 : 477
  Présent, autre année : 233
  Distribution : 2026:477, 2041:94, 2031:76, 2061:27, 2038:6, 2071:4,
                 2081:4, 2051:2, 2052:1, 2050:1
-- annee_fin --
  ABSENT : 0
  Présent, null/vide (en cours) : 708
  Présent, valeur renseignée (terminée) : 2
```

**Conclusion à ce stade** : 0 cas résiduel sur les deux audits — le
garde-fou ne se déclenche jamais sur les données actuelles, mais reste une
protection utile pour l'avenir. Point 1.2 semblait clos ici. **David a
alors posé la question qui a rouvert tout le chantier** : pourquoi 477
fiches sur 710 (67 %) ont-elles exactement `annee_debut: 2026`, alors que
la plupart des entités ne devraient pas encore exister aujourd'hui ?

## 5. Étape 4 — Diagnostic de la cause racine (fichiers demandés : generator.zip complet)

David a uploadé l'intégralité du dossier `generator/` en zip. Recherche de
toutes les occurrences d'`annee_debut` dans le code :
```
generate_instances.py:305 (schéma JSON exemple), :432, :495 (écriture)
officialize_alliances.py:565 (frontmatter en dur)
enrich_minimal.py:367 (lecture seule, PAS de réécriture)
create_entities_and_instances.py:780, :896, :959 (même pattern que generate_instances.py)
```

**Trois causes distinctes confirmées par lecture directe du code** :

1. **`officialize_alliances.py` (ligne 565)** — crée les fiches
   `officialise_minimal` (étape "squelette"). **Aucun appel LLM à ce
   stade** : `annee_debut: 2026` est **codé en dur** dans le template de
   frontmatter, avec `type_relation_dominante: neutralité`,
   `etat_temporel: actif`, `age_historique: émergent`,
   `generation: transition` — tous marqués "à développer en phase 2".

2. **`enrich_minimal.py`** (la "phase 2" censée corriger ça) — vérifié en
   détail : son schéma de sortie JSON ne contenait **pas**
   `annee_debut`/`annee_fin`. La fonction lit bien
   `annee_debut = fm.get("annee_debut", 2026)` (ligne 367) pour
   l'AFFICHER en contexte au LLM, mais ne le lui redemande jamais en
   sortie, et `write_enriched_fiche()` n'avait aucun bloc pour l'écrire.
   Une fiche créée par le chemin 1 restait donc bloquée à 2026 **même
   après enrichissement complet**.

3. **`generate_instances.py`/`create_entities_and_instances.py`** —
   schéma JSON montrant littéralement `"annee_debut": 2026,` comme valeur
   D'EXEMPLE, sans aucune instruction reliant ce champ à
   `age_historique`/`generation`. Biais d'ancrage classique : le LLM tend
   à recopier une valeur numérique concrète montrée en exemple plutôt que
   de raisonner dessus.

## 6. Étape 5 — Correctifs à la source (3 fichiers patchés)

**`generate_instances.py`** et **`create_entities_and_instances.py`**
(patch identique en miroir sur les deux) :
- Retrait de `"annee_debut": 2026,` du schéma JSON, remplacé par
  `"annee_debut": "<année entre 2026 et 2098, cohérente avec age_
  historique/generation choisis ci-dessous — voir CONSIGNE CHRONOLOGIE>"`.
- Ajout d'un bloc `CONSIGNE CHRONOLOGIE` explicite : "émergent"/
  "transition" → proche de 2026 ; "résiduel"/"post-effondrement"/
  "mythifié"/"déclinant" → nettement antérieur à 2098 ; "ascendant"/
  "dominant" → valeur intermédiaire.
- Validation défensive ajoutée à l'écriture (`write_instance_file()`) :
  cast en `int`, vérification de plage `2026 <= v <= 2098`, fallback à
  2026 si la réponse LLM n'est pas exploitable malgré la consigne.

**`enrich_minimal.py`** :
- Ajout de `"annee_debut"` et `"annee_fin"` au schéma JSON de sortie.
- Ajout d'une `RÈGLE CHRONOLOGIE` dans le prompt, réutilisant le contexte
  déjà connu (`age_historique={age_historique}`,
  `generation={generation}`) pour demander au LLM de CONFIRMER ou
  RÉEXAMINER `annee_debut`, pas de le randomiser.
- **Écriture réelle ajoutée dans `write_enriched_fiche()`** — c'était le
  maillon manquant : sans ce bloc, le LLM aurait pu répondre correctement
  sans que rien ne s'écrive dans la fiche. Même garde-fou de plage
  (2026-2098) qu'à l'écriture des deux autres scripts.

Syntaxe vérifiée (`ast.parse`) sur les trois fichiers après chaque
modification.

## 7. Étape 6 — David pose la question de fond : cohérence avec le monde réel

Question exacte de David : *"le problème c'est que 2026 est aujourd'hui et
que le vault n'est pas cohérent avec la réalité. si les dates sont proches
d'aujourd'hui il faut que les entités soient dans le prolongement de ce
qui existe aujourd'hui dans le vrai monde."*

Recherche dans le code de tout mécanisme d'ancrage réel existant :
```
grep -rln "monde réel|actualité|aujourd'hui|situation actuelle|contexte réel|2025" *.py
→ inject_custom_events.py, inject_custom_signals.py (et quelques autres non pertinents)
```

**Mécanisme trouvé mais insuffisant** : `inject_custom_events.py`/
`inject_custom_signals.py` permettent déjà un ancrage réel — David fournit
une idée d'actualité comme inspiration, le LLM en extrapole une
conséquence fictionnelle datée. C'est ce qui explique l'événement déjà
présent dans le registre : `conflit_israel_iran_2026` (daté 2027 dans la
fiction). **Mais ce mécanisme est entièrement manuel/opt-in**, et ne
couvre PAS la création d'entités par défaut — confirmé par relecture du
contexte `sc_ctx` envoyé au LLM dans les 3 scripts de création
(`state_of_system`, `trajectory`, `political_regime`,
`dominant_variables` — entièrement abstrait, aucune référence au monde
réel actuel).

## 8. Étape 7 — Ancrage sur la chronologie FICTIONNELLE du scénario (chantier A, avant même la question du monde réel)

Avant même la question du monde réel, un premier problème avait été
identifié : le raisonnement qualitatif seul (age_historique/generation →
année) n'a **aucune plage numérique précise** — deux fiches "résiduel"
pourraient recevoir des années arbitrairement différentes sans
incohérence détectable. Le scénario a pourtant une vraie trajectoire
datée : la fiche BCUC elle-même mentionne *"cessé de financer... dès
2071"* dans son propre texte.

**Source retenue** : `registre_evenements.md`, généré/tenu à jour par
`inject_custom_events.py`/`inject_custom_signals.py` (maintenu à jour
automatiquement à chaque injection). D'abord envisagé via
`snapshot.py::build_signal_trajectory` (calcul dynamique), puis **remplacé
par une lecture directe du registre** — plus riche (inclut les événements
custom en plus des signaux), moins coûteux (pas de recalcul), déjà
maintenu par le pipeline. Décision prise après que David a signalé
l'existence de ce fichier ("je ne sais pas qui le remplit mais il semble
que les informations contenues sont très utiles").

**Fonctions ajoutées** dans les 3 scripts (`generate_instances.py`,
`create_entities_and_instances.py`, plus consommation du `registre_
excerpt` déjà existant dans `enrich_minimal.py`) :
- `_read_registre_text()` — lecture avec cache module-level.
- `_est_ligne_separateur()` — détection robuste (voir bug §9).
- `_parse_registre_table()` — parsing par section de scénario.
- `load_scenario_timeline_summary(scenario_slug)` — filtre sur
  `type == "evenement"` OU `pilote == "oui"`, plafonné à 40 lignes,
  **mis en cache par scénario** pour ne calculer qu'une fois par run
  (vérifié par test : 2 lookups même scénario → 1 seul appel réel,
  3ᵉ lookup scénario différent → 2ᵉ appel).

**Injection dans le prompt** : nouvelle section
`## CHRONOLOGIE RÉELLE DU SCÉNARIO {scenario}`, avec consigne "PRIORITÉ
ABSOLUE" — si un jalon correspond clairement à l'origine de l'instance,
utiliser cette année plutôt qu'une estimation qualitative libre.

## 9. Bug découvert en testant le chantier A — `parse_registre_table()` aveugle sur `breakdown`

En testant le parsing sur le VRAI `registre_evenements.md` (fourni par
David dans le zip), résultat initial anormal :
```
breakdown: (aucun jalon trouvé) — 0 lignes
fortress_world, new_sustainability, eco_communalism, policy_reform, reference: OK
```

**Cause identifiée par inspection ligne à ligne** : la section
`## breakdown` (lignes 15-18 du fichier) a une ligne séparatrice de
tableau différente des 5 autres sections :
```
breakdown  : | --------- | --------- | ----------------------------------------- | ...
autres     : |---|---|---|---|---|---|
```
Probablement une réédition manuelle via un éditeur de tableau Markdown
(Obsidian réaligne automatiquement ce genre de tableau). La première
détection testée (`line.startswith("|---")`) ne matchait que le format
compact.

**Vérification que ce n'était pas propre au script en cours d'écriture** :
test de la fonction ORIGINALE `parse_registre_table()`
d'`inject_custom_events.py` (copiée telle quelle, sans modification)
contre le vrai fichier :
```
breakdown: 0 lignes parsées avec la fonction ORIGINALE
fortress_world: 83, new_sustainability: 82, eco_communalism: 82,
policy_reform: 82, reference: 84
```
**Confirmé : bug réel préexistant en production**, pas un artefact du
nouveau script. Impact réel : `get_registre_excerpt_for_variables()`/
`get_all_evenements()` (anti-collision d'événements/signaux) étaient
aveugles sur tout le scénario `breakdown` depuis que cette section a été
reformatée.

**Découverte supplémentaire** : `inject_custom_signals.py` avait
**déjà été corrigé pour exactement ce bug le 26 juillet 2026** —
fonction `_est_ligne_separateur()`, dont le docstring cite explicitement
`## breakdown` comme cas de figure cassé. Ce correctif n'avait simplement
jamais été porté vers `inject_custom_events.py`, qui gardait l'ancienne
détection.

**Correctif appliqué** : portage à l'identique de `_est_ligne_
separateur()` dans `inject_custom_events.py::parse_registre_table()`
(pas de nouvelle logique inventée — réutilisation du correctif déjà
existant et éprouvé). Vérifié après coup :
```
breakdown: 84 lignes parsées (corrigé) — cohérent avec les 82-84 des autres
```
`regenerate_registre_with_event()` (fonction d'ÉCRITURE) vérifiée
séparément — elle avait déjà sa propre détection robuste, pas concernée
par ce bug.

**Fichier livré** : `inject_custom_events.py`.
**`inject_custom_signals.py` n'a PAS été modifié** (déjà correct depuis le
26 juillet) — ne pas le confondre avec un fichier à déployer.

## 10. Chantier B — Ancrage sur le monde RÉEL

Distinct du chantier A (chronologie fictionnelle interne). David a validé
l'option "ajouter un vrai contexte état-du-monde-2026 (rédigé une fois par
David) injecté dans les prompts de création" parmi 3 options proposées.

**Fichier créé** : `etat_du_monde_reel.md`, structuré sur les 12 variables
déjà utilisées partout dans le projet (`VALID_VARS` de `loader.py` :
`systeme_economique_redistribution`, `gouvernance_institutions`,
`geopolitique_conflits`, `valeurs_culture_tempo_sociale`,
`organisation_territoires`, `sante_biotechnologies`,
`frontieres_du_systeme`, `technologie_information`,
`climat_environnement_global`, `energie_ressources_critiques`,
`demographie_mobilite_humaine`, `systemes_productifs_travail`).

**Câblage réalisé dans LES 4 SCRIPTS** (les 3 précédents + le script de
rattrapage §11, David ayant explicitement demandé la cohérence vault
entier) :
- Constante `ETAT_MONDE_PATH = GENERATOR_DIR / "etat_du_monde_reel.md"`.
- Fonction `load_etat_monde_reel()` — lecture simple avec cache
  module-level, **tolère l'absence ou le vide du fichier sans planter**
  (retombe sur un message explicite "aucun ancrage réel disponible") —
  testé explicitement pour ce cas.
- Injection dans le prompt sous `## ÉTAT DU MONDE RÉEL (référence
  factuelle, PAS de la fiction)`.
- Consigne d'usage **conditionnel selon la date choisie** : proche
  d'aujourd'hui (3-5 ans) → prolongement plausible obligatoire ; plus
  lointain → simple toile de fond historique, la fiction spéculative
  reprend le dessus.
- Pour `fix_annee_debut_placeholder.py` spécifiquement (voir §11) :
  consigne renforcée — si le contenu déjà écrit d'une fiche contredit
  l'état réel, NE PAS confirmer 2026, proposer une année plus lointaine où
  la divergence devient plausible comme évolution future.

**Remplissage du fichier — recherches web effectuées en session (7 août
2026)**, requêtes exactes lancées :
1. "actualité géopolitique majeure août 2026"
2. "guerre Ukraine Russie situation août 2026"
3. "régulation intelligence artificielle 2026 IA générale"
4. "accord climat COP 2026 objectifs émissions"
5. "COP30 Belém résultats 2025 objectifs 2026"
6. "Agence internationale de l'énergie AIE 2026"
7. "crise migratoire mondiale 2026 flux déplacements"
8. "économie mondiale 2026 croissance dette inflation"

**8 sections remplies avec sources factuelles** :
- `systeme_economique_redistribution` — croissance mondiale 2,5-3,3 %
  selon institutions (FMI/Banque mondiale/ONU), toutes révisées à la
  baisse à cause du conflit Moyen-Orient ; dette publique mondiale
  qualifiée d'"insoutenable" pour plusieurs économies développées dont la
  France.
- `gouvernance_institutions` — **tension réelle documentée sur l'AIE** :
  le secrétaire américain à l'Énergie (Chris Wright) a publiquement
  critiqué le scénario "net zéro" de l'AIE en février 2026 ("des rêves
  d'hommes politiques... inhumain, immoral, totalement irréaliste"),
  menace de retrait américain (14 % du financement de l'agence). COP30
  (Belém, nov. 2025) : bilan "mitigé", accord sur le triplement du
  financement d'adaptation d'ici 2035, mais échec sur l'élimination des
  fossiles.
- `geopolitique_conflits` — guerre Russie-Ukraine toujours active (gains
  territoriaux russes nets en juillet 2026 selon DeepState, trêve
  ponctuelle de 32h à Pâques orthodoxe le 11 avril 2026 sans suite) ;
  **conflit Moyen-Orient débuté février 2026** (dynamique Israël-Iran),
  escalade documentée début août 2026 (frappes IRGC directes sur
  pétroliers sous escorte navale US dans le détroit d'Ormuz).
- `technologie_information` — AI Act européen : entrée en application de
  la majorité des dispositions le **2 août 2026** (5 jours avant la
  session), obligation de signaler tout usage de chatbot, marquage des
  contenus IA-générés. "Digital Omnibus on AI" (accord du 7 mai 2026) a
  assoupli le calendrier initial.
- `climat_environnement_global` — détail COP30/COP31 (Antalya, Turquie,
  9-20 nov. 2026), plans climatiques nationaux actuels ne permettant que
  ~10 % de baisse d'émissions d'ici 2035 contre 60 % jugés nécessaires par
  le GIEC.
- `energie_ressources_critiques` — **choc pétrolier qualifié par l'AIE de
  "plus grave choc d'offre pétrolière de l'histoire"**, lié au détroit
  d'Ormuz, perte de production ~10 millions de barils/jour en mars 2026,
  libération coordonnée sans précédent des réserves stratégiques (32 pays
  membres AIE, 426 millions de barils, plus d'un tiers des stocks).
- `demographie_mobilite_humaine` — déplacements liés au conflit
  Moyen-Orient (~1M déplacés internes Liban mi-mai 2026, 3,2M déplacés
  temporaires en Iran fin mars 2026), Soudan toujours plus grande crise
  mondiale (9,1M déplacés internes).
- `systemes_productifs_travail` — adoption large de l'IA générative/
  agentique comme facteur de productivité, fragmentation géopolitique
  (tensions US/Chine) comme frein structurel.

**4 sections laissées vides** (marquées explicitement comme telles dans le
fichier, pas de résultats de recherche assez spécifiques en une session) :
`valeurs_culture_tempo_sociale`, `organisation_territoires`,
`sante_biotechnologies`, `frontieres_du_systeme`.

**Implication directe pour le cas AIER** (voir §11) : la tension réelle
trouvée sur l'AIE rend une réforme institutionnelle fictionnelle proche de
2026 **plausible** plutôt qu'inventée dans le vide — nuance importante
pour réinterpréter le test du §11, fait AVANT que ce fichier existe.

## 11. Script de rattrapage — `fix_annee_debut_placeholder.py` (nouveau, testé)

Créé sur le modèle chirurgical de `fix_alliances_oppositions.py` (même
conventions : `SCENARIOS`, `MAX_FIX_ATTEMPTS`, `TRANSIENT_RETRIES`,
patch frontmatter par regex ciblée sur une seule clé, rapport tronqué en
tête de run réel jamais en dry-run).

**Fonctions clés** :
- `find_target_fiches(scenario, slug_filter)` — fiches `officialise_
  enrichi` avec `annee_debut == 2026` uniquement.
- `build_targeted_prompt(fiche, scenario, timeline_summary)` — envoie au
  LLM le profil narratif déjà écrit + la chronologie réelle du scénario
  (chantier A) + l'état du monde réel (chantier B, ajouté après coup).
- `patch_annee_debut_frontmatter()` / `write_annee_debut_patch()` — patch
  chirurgical, ne touche QUE la clé `annee_debut`, laisse tout le reste
  intact (vérifié par test unitaire sur un frontmatter factice).
- `call_llm_json_resilient()` — absorbe les pannes transitoires API avec
  backoff (même mécanisme que `fix_alliances_oppositions.py`).

**Testé par David en dry-run réel** (AVANT le câblage du chantier B) :
```
python3 fix_annee_debut_placeholder.py --scenario policy_reform --dry-run --limit 3
```
Résultat exact obtenu (81 fiches concernées au total sur policy_reform,
traitement limité à 3) :

1. **AIER** (`agence_internationale_de_l_energie_reformatee_aier_
   policy_reform`) — confirmé à 2026. Justification LLM : *"L'année 2026
   est confirmée car elle correspond explicitement à la refondation de
   l'AIE en AIER, mentionnée dans la description journalistique comme
   'née des cendres de l'ancienne AIE en 2026', et s'aligne avec le
   profil émergent/transition."* — **confirmé SANS vérification de
   plausibilité réelle** (chantier B pas encore câblé à ce moment du
   test).
2. **ATRB** (`agence_technocratique_pour_la_resilience_biospherique_atrb_
   policy_reform`) — confirmé à 2026 par déduction qualitative pure,
   aucun jalon précis trouvé.
3. **ACRA** (`autorite_continentale_des_ressources_aquatiques_acra_
   policy_reform`) — **corrigé 2026 → 2038**. Justification LLM : *"La
   description mentionne explicitement que l'ACRA a été fondée 'dans le
   sillage des grandes sécheresses continentales des années 2030', et le
   jalon 'traité de Niamey sur le partage des nappes phréatiques 2038'
   (chronologie réelle) correspond à une réponse institutionnelle
   structurante."*

Coût mesuré (fournisseur Mistral, modèle `mistral-large-latest`) : ~3000
tokens entrée / 86-112 tokens sortie par appel. Résumé : 3 traitées, 1
corrigée, 2 confirmées, 0 échec.

**Ce test doit être REFAIT** une fois `etat_du_monde_reel.md` en place —
le cas AIER en particulier, pour voir si la justification cite maintenant
la tension réelle AIE (février 2026, menace de retrait américain) plutôt
que de confirmer 2026 sur la seule base du texte narratif de la fiche.

## 12. Fichiers livrés cette session (chantier point 1.2, liste exhaustive)

| Fichier | Nature | Action à faire |
|---|---|---|
| `prompt_builder.py` | Patché | Remplacer dans `generator/` |
| `generate_instances.py` | Patché | Remplacer dans `generator/` |
| `create_entities_and_instances.py` | Patché | Remplacer dans `generator/` |
| `enrich_minimal.py` | Patché | Remplacer dans `generator/` |
| `inject_custom_events.py` | Patché (bug breakdown) | Remplacer dans `generator/` |
| `fix_annee_debut_placeholder.py` | Nouveau | Copier dans `generator/` |
| `etat_du_monde_reel.md` | Nouveau, rempli 8/12 | Copier dans `generator/` |
| `audit_type_relation_dominante.py` | Nouveau, déjà exécuté | Garder pour réaudit futur |
| `audit_dates_instances.py` | Nouveau, déjà exécuté | Garder pour réaudit futur |

**`inject_custom_signals.py` n'a PAS été livré/modifié** — déjà correct
depuis le 26 juillet, mentionné uniquement comme source du correctif porté
vers `inject_custom_events.py`.

## 13. Point de reprise pour la prochaine session (8 août) — protocole en 5 étapes

1. **Déployer** les 5 fichiers patchés + 2 nouveaux fichiers (tableau §12)
   dans `generator/`.
2. **Dry-run ciblé prioritaire** — revérifier spécifiquement le cas AIER
   maintenant que l'état du monde réel est câblé :
   ```
   python3 fix_annee_debut_placeholder.py --scenario policy_reform --dry-run --limit 5
   ```
   Comparer la nouvelle justification LLM à celle du §11 point 1.
3. **Élargir le dry-run** scénario par scénario (retirer `--limit`) pour
   estimer le volume réel de corrections avant tout run réel — 477 fiches
   réparties inégalement sur 6 scénarios (81 rien que sur policy_reform).
4. **Lancer pour de vrai**, scénario par scénario (pas `--all` d'entrée).
5. **Réaudit** : relancer `audit_dates_instances.py` après coup, comparer
   au chiffre initial (477/710 à 2026) pour mesurer l'impact réel.

## 14. Rappel — reliquat non traité de HANDOFF_7_AOUT.md (indépendant du chantier point 1.2)

- `gui_verified: true` sur les deux entrées `fix_alliances_oppositions` et
  `enrich_minimal` — protocole de test navigateur en 7 points partiellement
  suivi (points 2 et 6 vérifiés en direct par David avec une clarification
  importante sur `depends_on`, voir point suivant), reste à finaliser.
- **Erreur de documentation confirmée mais non corrigée** dans
  `HANDOFF_7_AOUT.md` §9 et `USER_MANUAL_COMPLET.md` : décrivent à tort
  `depends_on` comme un masquage conditionnel. Mécanisme réel (confirmé
  par lecture directe d'`app.js` en session — fonction
  `syncDependsOnParents()` + listeners dans `renderOption()`, établi le
  26 juillet après un retour explicite de David) : l'option enfant (ex.
  `--bascule-en-opposition`) est TOUJOURS visible (juste indentée
  visuellement) ; cocher l'enfant force le parent à se cocher
  automatiquement ; décocher le parent décoche l'enfant. Observé
  concrètement par David sur `fix_alliances_oppositions` : le champ
  `--bascule-en-opposition` apparaît qu'on coche `--resoudre-conflits` ou
  non — comportement attendu, pas un bug. **Non corrigé dans les fichiers
  eux-mêmes** faute d'accès au contenu complet de `USER_MANUAL_COMPLET.md`
  en session (seuls `HANDOFF_7_AOUT.md` et `BACKLOG_CONSOLIDE_7_AOUT.md`
  étaient fournis en texte intégral — `USER_MANUAL_COMPLET.md` uploadé en
  fichier mais jamais son contenu chargé en contexte).
