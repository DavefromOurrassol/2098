# Backlog consolidé Ourrassol 2098 — état au 2 août 2026

*Reconstitué en croisant : tous les BACKLOG_*/HANDOFF_* du 20 juin au 1er août
(archive), `USER_MANUAL_COMPLET.md` (version courante, post-1er-août),
`HANDOFF_1_AOUT.md`, et `backlog_publication_web_journaux_oraux.md`
(document de scoping du 12 juillet, retrouvé et intégré le 2 août — détail
complet des sections 2.4 et 2.5). Objectif : ne garder que ce qui est
réellement encore ouvert, en écartant les doublons et les items déjà clos
ailleurs.*

---

## 1. Ce qui reste réellement à faire

### 1.1 — Entrée `validate` du panneau GUI ✅ **testée, tout est OK (confirmé le 2 août)**
Le point de reprise du 31 juillet listait explicitement en priorité n°1 :
*« Tester `validate` (jamais abordé) — dernière entrée du panneau »*. La
session du 1er août ne l'avait pas traité, mais David confirme l'avoir
testée depuis — RAS. C'était la dernière des 18 entrées du panneau
sidebar encore non validée en conditions réelles : **les 18 sont
maintenant toutes validées.** L'audit de clôture global évoqué au point
n°4 du 31 juillet (« une fois validate et P8 traités ») est donc
désormais atteignable, si David souhaite le faire.

### 1.2 — Donnée corrigée : entrée sans `type_entite` (Groenland) ✅ **corrigé le 2 août 2026**
`policy_reform` / `ameriques_reformees` : l'entrée `origine_reelle`
Groenland sans `type_entite`, détectée par David le 25 juillet, jamais
corrigée depuis. Corrigée en direct à partir de `geographie/policy_reform.md`
et `gui/zones_pays.json` fournis par David :
```bash
python3 check_type_entite_coherence.py --scenario policy_reform --apply
```
**Diff vérifié chirurgical** — exactement 2 lignes ajoutées
(`type_entite: pays` + `portion: null`) sous `- entite: Groenland`, rien
d'autre touché sur les 3396 lignes du fichier. Backup `.bak` automatique
généré. **Scan complet des 6 scénarios confirmé après coup** :
`check_type_entite_coherence.py --all` → zéro entrée sans `type_entite`
restante nulle part dans le vault.

### 1.3 — Fichier de debug à supprimer par David ✅ **fait, confirmé le 2 août**
`signaux_custom/queue_sahel_v2.yaml` — identifié comme fichier de debug le
31 juillet. Supprimé par David.

### 1.4 — Vérification faite : `--cible` n'affecte que le chantier ciblé ✅ **confirmé le 2 août 2026**
Testé en réel le 1er août par David, mais seulement avec un seul chantier
approuvé au moment du test — restait à confirmer le cas à plusieurs
chantiers approuvés simultanément sur le même scénario.

**Test réalisé** (données synthétiques, sandbox isolée — aucun impact sur
le vault réel de David) : 2 chantiers `pays_sans_zone` fictifs sur
`policy_reform`, tous deux approuvés (Alpha ciblé, Beta témoin), puis :
```bash
python3 generer_zones_topdown.py --apply-topdown --scenario policy_reform --cible "Pays Test Alpha"
```
**Résultat vérifié à deux niveaux** :
- `chantiers_geographie.yaml` : Alpha → `statut: traite` +
  `date_traitement` rempli. Beta **strictement intact** — toujours
  `a_traiter`, `date_traitement: null`.
- `geographie/policy_reform.md` : diff complet avant/après → seule la
  zone Alpha ajoutée, aucune trace de Beta.

**Explication du comportement, au niveau du code** (`chantiers.py`) :
`chantiers_prets_a_appliquer(scenario, cible=cible)` filtre la liste
*avant* la boucle d'application dans `appliquer_scenario()` — avec
`--cible`, un seul élément entre dans la boucle, donc un seul appel
d'écriture, et `mettre_a_jour_chantier()` ne modifie que l'entrée dont
l'`id` correspond exactement. Comportement confirmé sûr, aucun correctif
nécessaire.

### 1.5 — Entrée fantôme `restructure_zones` dans `scripts_config.json` ✅ **déjà absente, vérifié le 2 août 2026**
Le manuel documentait depuis le 13 juillet que P7 (restructuration de
zones) a été construit directement dans l'onglet Carte du GUI, pas comme
script séparé, et que l'entrée fantôme correspondante « peut être
retirée ». **Vérifié sur `scripts_config.json` fourni par David : elle
n'existe déjà plus.** Les 18 entrées du panneau (recherche `"restructure"`
: zéro occurrence) correspondent exactement à ce que documente le manuel
courant. Suppression déjà faite à un moment non tracé dans les handoffs —
même cas de figure que P8 (§4) : l'action a eu lieu, seule la trace
écrite manquait.

### 1.6 — Bug confirmé et corrigé : entrée fantôme dans la carte INSTANCES du dashboard ✅ **corrigé le 2 août 2026**
Carte concernée : **INSTANCES** (711 au total, 6 scénarios connus =
710 + 1 fantôme).

**Diagnostic initial (2 août, matin) erroné** : soupçon d'un problème de
regex/backtracking sur un champ `scenario:` vide dans une vraie fiche.
**Diagnostic confirmé après inspection réelle du dossier `instances/`
fourni par David** : la cause est ailleurs, plus simple.

**Cause réelle** : `instances/instance_template.md` — le fichier gabarit
du projet (placeholders type `<nom_instance>`, `scenario:
<slug_scenario>`, jamais remplis, c'est normal) — **vit directement dans
`instances/`**, au milieu des 710 vraies fiches. `_stats_instances()`
fait `instances_dir.glob("*.md")` sans l'exclure : il compte donc le
gabarit comme une 711e instance, avec pour valeur de scénario le texte
littéral `<slug_scenario>`. Ce texte part tel quel dans le JSON du
dashboard ; affiché sans échappement HTML côté frontend, le navigateur
interprète `<slug_scenario>` comme une balise inconnue et l'avale —
il ne reste visuellement que le texte qui suit, d'où `: 1`.

**Preuve que c'est un angle mort connu du projet, pas un cas isolé** :
`generator/officialize_alliances.py` (ligne 223) filtre déjà
explicitement ce fichier :
```python
f for f in INSTANCES_DIR.glob("*.md") if f.name != "instance_template.md"
```
Mais ce filtre n'existe que dans ce script. Vérifié dans tout
`generator/` : **absent** de `create_entities_and_instances.py`,
`enrich_minimal.py` (2 occurrences), `extract_phantom_slugs.py`,
`fix_impact_scale.py`, et bien sûr `routes_dashboard.py`. Le même trou
peut donc fausser d'autres traitements (ex. `extract_phantom_slugs.py`
pourrait traiter `<slug_entite>_<slug_scenario>` comme un slug réel) —
non vérifié en détail, mais à garder en tête si un comportement bizarre
apparaît ailleurs sur ces scripts.

**Correctif appliqué** dans `routes_dashboard.py` (fichier corrigé livré) :
1. `_stats_instances()` — exclusion explicite de `instance_template.md`
   (même filtre que `officialize_alliances.py`), + garde-fou défensif
   supplémentaire pour un futur cas de `scenario:` réellement vide sur
   une vraie fiche.
2. `_stats_enrichissement()` — même pollution trouvée et corrigée : le
   gabarit n'a pas de champ `statut:`, il tombait donc silencieusement
   dans le seau `"autre"`, faussant aussi cette carte.

**Recommandation structurelle, au-delà du patch** : déplacer
`instance_template.md` hors de `instances/` (ex. dans un dossier
`templates/` à la racine du vault) réglerait le problème à la racine pour
*tous* les scripts d'un coup, plutôt que de devoir ajouter le filtre
`if f.name != "instance_template.md"` dans chaque script qui itère sur
`instances/*.md`. Décision et action laissées à David (déplacement de
fichier dans le vault, hors périmètre de ce qui a été patché ici).

### 1.7 — Bug confirmé et corrigé : panneau « Revue » vide malgré des fiches en échec ✅ **corrigé le 2 août 2026**
**Cause confirmée : incohérence `sort_keys` entre l'écriture et la
lecture de `needs_review_enrich.yaml`** (diagnostic initial validé, pas de
correction cette fois — contrairement au §1.6).

- Écriture, `generator/enrich_minimal.py`, `write_needs_review()` : seul
  appel `yaml.dump()` du pipeline sans `sort_keys=False` → PyYAML triait
  les clés alphabétiquement (`date` avant `slug`) → le parseur maison de
  `app.py` (qui ne reconnaît une nouvelle entrée que via `"- slug:"` en
  tête de ligne pour cette source) ne matchait plus jamais rien.
- **Correctif appliqué** : `sort_keys=False` ajouté à l'appel `yaml.dump()`
  (fichier `enrich_minimal.py` corrigé livré). Suffisant pour toutes les
  futures écritures ; un fichier déjà existant chez David avec des
  entrées mal ordonnées se corrigera de lui-même au prochain
  `enrich_minimal.py` (ré-écrit intégralement à chaque `write_needs_review`).

**Deuxième gap trouvé en creusant, plus large que prévu, corrigé aussi** :
le panneau `/api/review` de `app.py` ne couvrait que 2 des 4 sources
possibles de fiches en échec (`needs_review_enrich.yaml` et
`evenements_custom/needs_review.yaml`). **`entites_custom/needs_review.yaml`
et `signaux_custom/needs_review.yaml` (créées par `create_entity.py`/
`create_entities_and_instances.py` et `inject_custom_signals.py`)
n'étaient tout simplement jamais lues** — ni le chemin de fichier, ni le
format de leurs entrées (première clé `status:`, différente de `slug:`/
`idea:`) n'étaient couverts par le parseur.

**Correctif appliqué dans `app.py`** :
- Deux nouvelles fonctions `_parse_needs_review_entites()` et
  `_parse_needs_review_signaux()`, appelées dans `get_review()`.
- `_read_needs_review_yaml()` généralisée avec un paramètre `start_marker`
  optionnel (`"- status:"` pour ces deux sources), sans toucher au
  comportement existant sur `enrich`/`events`.

**Correctif appliqué dans `routes_dashboard.py`** (le badge de comptage,
distinct du contenu du panneau) : `_count_review_items()` complétée avec
les deux mêmes fichiers manquants.

**Limite connue du correctif entités/signaux** : le parseur reste naïf —
les entrées s'affichent avec un slug générique `(entité)`/`(signal)`
plutôt que le vrai nom, faute de descendre dans le sous-bloc `idea:`
imbriqué. Suffisant pour rendre les fiches visibles et comptées ; un
affichage plus détaillé resterait à faire si besoin.

**Vérifié par David le 2 août** : `instances_custom/needs_review_enrich.yaml`
n'existe pas actuellement sur le vault — le panneau vide est donc **normal
en l'état**. Explication trouvée après coup (voir §4) : P8 a en fait déjà
été traité intégralement le 27 juin 2026 (426/426 fiches, aucun échec
résiduel), donc ce fichier de review n'a jamais eu de raison d'exister —
pas un signe que le correctif n'a pas fonctionné. Le vrai test du fix se
fera au prochain run d'`enrich_minimal.py` qui produit un échec (sur de
nouvelles fiches, puisque le stock du 27 juin est épuisé) — ou sur une
des 3 autres sources (`entites_custom`/`evenements_custom`/`signaux_custom`)
si l'une d'elles a déjà des entrées en attente.

---

## 2. Gros chantiers volontairement en pause (pas oubliés, juste différés)

### 2.2 — Renommage des YAML génériques par dossier
`queue.yaml`/`processed.yaml`/`needs_review.yaml` répétés à l'identique
dans `entites_custom/`, `evenements_custom/`, `signaux_custom/` — décision
de renommage reportée (clarté vs coût : toucherait plusieurs scripts +
`scripts_config.json`). Aucune urgence identifiée.

### 2.3 — P14 : passer le tier LLM `strict` vers `claude-sonnet-5` en prod
Différé sine die sur demande explicite de David (1er août). Décision, pas
un oubli — à reconsidérer plus tard si David le demande.

### 2.4 — P20 : enrichissement frontmatter pour publication web future
Scoping complet retrouvé (`backlog_publication_web_journaux_oraux.md`,
12 juillet) — **rien codé**.

**Champs à ajouter au frontmatter des articles** : `slug` (identifiant
URL-friendly), `chapo`/`excerpt` (résumé 2-3 lignes, pages de liste + meta
SEO), `image_prompt` (généré par le LLM en même temps que l'article),
`a_une_photo` (booléen, **basculé manuellement** — choix éditorial, pas
systématique), `image_principale` (rempli en post-traitement),
`image_alt`, `image_credit` (traçabilité), `tags` (distinct de
`thematique`, orienté découverte lecteur), `journaliste_slug` (déjà
présent dans `journaux.yaml`), `date_publication` vs `date_evenement`
(à distinguer si calendrier éditorial différé), `articles_lies` (2-3
articles connexes, possiblement déductible des entités partagées plutôt
que généré), `zone_principale` (dédié, simplifie le filtrage géo côté
front par rapport à `localisation`).

**Génération d'images — Option 1 retenue** : le LLM produit un
`image_prompt` descriptif (lieu, ambiance, éléments clés) au moment même
de la génération de l'article (même appel API, cohérence garantie). La
décision d'illustrer (`a_une_photo`) reste manuelle et découplée de la
génération technique — le prompt est stocké dès la création, réutilisable
des semaines plus tard sans repasser par le LLM.

**Implémentation envisagée** :
1. Instruction dans `prompt_builder.py` pour que le LLM produise
   systématiquement `image_prompt`, même si non utilisé immédiatement.
2. `a_une_photo: false` par défaut, basculé à `true` manuellement (ou via
   script de sélection) par David.
3. Script séparé `generate_images.py` : scanne les articles
   `a_une_photo: true` sans `image_principale` renseignée, appelle l'API
   image, remplit `image_principale` + `image_alt`.

**Question ouverte, non bloquante** : rendu HTML — site statique généré
(type Hugo/Eleventy) à partir des YAML/Markdown, ou moteur de rendu
intégré au pipeline Flask existant. Pas tranché, n'empêche pas d'enrichir
le frontmatter dès maintenant.

### 2.5 — P21 : journaux oraux, orateurs itinérants
Scoping complet retrouvé (même document, 12 juillet) — **rien codé**.

**Contexte** : pour certains scénarios, des orateurs itinérants informent
les communautés lors de sessions orales plutôt que par écrit — pertinent
notamment pour `eco_communalism` et/ou `breakdown`, où l'infrastructure de
diffusion écrite/numérique est dégradée ou volontairement rejetée au
profit du lien communautaire direct. **Coexiste avec l'écrit au sein d'un
même scénario** — pas un scénario entier qui bascule en mode oral :
certains journaux d'un scénario donné seront oraux, d'autres resteront
écrits.

**Structure technique** :
- **Journal** : nouveau champ `type_diffusion` (`ecrit`/`oral`/`mixte`)
  sur l'entité journal dans `journaux.yaml`, pour router
  `prompt_builder.py` vers le bon registre via `get_journal_profile()`
  adapté.
- **Orateur — entité séparée (Option B décidée)** : au lieu de réutiliser
  `journaliste_slug` avec un métier élargi (Option A, écartée — risque de
  forcer des spécificités narratives d'itinérance/réputation orale dans un
  modèle pensé pour un rôle différent), créer un nouveau type d'entité
  `orateur` avec ses propres attributs : itinérance entre communautés,
  communautés desservies, réputation orale, style rhétorique propre.
  Implique un nouveau lien dans `journaux.yaml` (en complément ou
  substitution de `journaliste_slug` selon `type_diffusion`) et une
  variante de `get_journal_profile()`.

**Registre oral dans `prompt_builder.py`** (différences vs écrit) :
adresse directe à l'auditoire, formules d'ouverture/clôture ritualisées,
répétitions rhétoriques, pas de chapô ni de sous-titres, structure
accroche → développement → appel à l'action/question ouverte finale,
possibilité de call-and-response pour le côté performatif.

**Champs frontmatter spécifiques aux articles oraux** : `duree_estimee`
(calibrer la longueur à un temps de parole réaliste), `lieu_diffusion`
(place publique, marché, assemblée — plus fin que `localisation`),
`mode_reception` (assemblée silencieuse, discussion ouverte — ambiance
sociale).

---

## 3. Points mineurs, non bloquants, sans action requise

- **P15** — `acteurs_hint_count` non plafonné en filtre dur dans
  `inject_custom_events.py` (contrairement à `variables_hint_count`, corrigé
  le 11 juillet). Jamais observé comme un vrai problème en usage réel :
  gardé en information de fond, pas au backlog actif.
- **`--force` du panneau `--scan-pending`** (extract_localisation) ne
  rafraîchit pas dynamiquement le menu de fiches — limite connue documentée
  le 31 juillet, contournable via `--scenario`.
- **`coverage_proposals_reference.yaml`** sans `.applied` (contrairement
  aux 5 autres scénarios) — anomalie repérée, jamais creusée, famille
  legacy (`complete_geographie_coverage.py` retiré du pipeline). Sans
  impact opérationnel, laissé tel quel par décision documentée.
- **`/api/carte/appliquer_zone_topdown_suspecte`** — route dormante jamais
  migrée vers `chantiers.py`, mais son seul point d'entrée UI a été retiré
  le 31 juillet. Aucune action requise (route conservée par précaution).

---

## 4. Clarifications utiles trouvées en croisant les documents

- **P8 (enrichir les 426 fiches `officialise_minimal`) — ✅ CLOS,
  découvert le 2 août en croisant les fiches réelles.** Le backlog le
  listait depuis fin juin comme *« en attente, jamais lancé en masse »*.
  En réalité **déjà traité intégralement le 27 juin 2026**, en une seule
  fois, en dehors de toute session documentée dans les handoffs suivants
  — la trace ne s'est jamais propagée aux BACKLOG_CONSOLIDE ultérieurs.
  **Preuve directe dans les fiches** : `enrich_minimal.py` inscrit une
  ligne de traçabilité permanente (section `## Notes` du corps de chaque
  fiche) — *« Fiche enrichie depuis officialise_minimal le
  {date}. »*. Recherche sur les 710 fiches d'`instances/` : **426
  occurrences, toutes datées du 27 juin 2026** — correspond exactement
  au total de fiches `statut: officialise_enrichi` sur les 6 scénarios
  (74+60+67+46+77+102), et **zéro fiche `statut: officialise_minimal`
  restante** sur l'ensemble du vault. Confirmé par David : pas de
  souvenir d'un run manuel CLI, mais l'hypothèse la plus probable reste
  un lancement hors GUI (`enrich_minimal.py --all`) ce jour-là.
- **`noeud_mnemos_pannonie`** — le handoff du 1er août le rouvrait comme
  *« statut toujours incertain »*. En réalité **déjà tranché le 14 juillet**
  (P23, `BACKLOG_CONSOLIDE copie 2.md`) : ce n'était jamais une vraie
  anomalie — `arc_eurasien_central` liste bien la Hongrie dans son
  `origine_reelle` complet (~25 pays), erreur d'appréciation en lecture
  rapide initiale. **Ce point peut être définitivement clos.**
- **P18** (cohérence `routes_dashboard.py` après renommage « Modèle si
  forcé ») — le manuel courant affiche encore la mention *« ⚠️ Non vérifié
  au 11 juillet »*, mais P18 a en fait été **clos le 13 juillet** (bug
  bonus #35 trouvé et corrigé : `import json` manquant cassait
  `/api/dashboard`). Résidu de rédaction à nettoyer dans le manuel, pas un
  vrai point ouvert.
- **P22 signal 2** (cohérence de patron spatial) — listé isolément comme
  *« toujours scopé, pas construit »* dans le backlog du 16 juillet, mais
  en réalité fusionné et livré via P24 étape B (garde-fou intégré à
  `complete_geographie_coverage.py`, construit le 15 juillet). Pas un
  doublon à rouvrir.
- **P24 étape C** (générateur top-down proprement dit, scopé le 25 juillet
  dans `P24_ETAPE_C_SCOPING.md`, C.1 à C.4) — entièrement absorbé et livré
  par la suite des sessions (25 juillet → 1er août) sous la forme du
  système `chantiers_geographie.yaml` + `generer_zones_topdown.py` +
  onglet Chantiers du GUI. Le point de vigilance noté dans le scoping
  (« `patron_spatial_suspectes.yaml` ne progresse jamais tout seul, sans
  revue manuelle ») est résolu par la fusion du 25 juillet en un fichier
  unique à 3 statuts (`a_traiter`/`ignore`/`traite`).

---

## 5. Résumé actionnable pour la prochaine session

1. ✅ Fait — `validate` testé, RAS. Les 18 entrées du panneau sidebar sont
   maintenant toutes validées.
2. ✅ Fait — `check_type_entite_coherence.py --scenario policy_reform
   --apply` lancé, correctif chirurgical vérifié (2 lignes), scan complet
   des 6 scénarios confirme zéro entrée restante. `geographie/policy_reform.md`
   corrigé livré — reste à David de le remettre en place dans le vault.
3. ✅ Fait — vérifié avec des données de test à 2 chantiers approuvés :
   `--cible` n'affecte que le chantier ciblé, l'autre reste intact
   (§1.4).
4. ✅ Fait — vérifié sur `scripts_config.json` : l'entrée fantôme
   `restructure_zones` n'existe déjà plus, rien à faire.
5. ✅ Fait — `signaux_custom/queue_sahel_v2.yaml` supprimé.
6. ✅ Clos le 2 août — P8 (`enrich_minimal`) : déjà traité intégralement
   le 27 juin 2026, preuve trouvée dans les fiches elles-mêmes. Plus
   rien à décider ni relancer.
7. `noeud_mnemos_pannonie` : ne plus le lister comme incertain — déjà clos
   le 14 juillet.
8. ✅ Fait — `routes_dashboard.py` corrigé et livré : exclusion
   d'`instance_template.md` dans `_stats_instances()` et
   `_stats_enrichissement()` (vraie cause de l'entrée fantôme ` : 1`,
   §1.6). Reste à David : remplacer le fichier côté GUI, redémarrer
   Flask, et envisager de déplacer `instance_template.md` hors de
   `instances/` pour régler le problème à la racine dans tous les
   scripts concernés.
9. ✅ Fait — panneau Revue corrigé et livré : `sort_keys=False` dans
   `enrich_minimal.py`, + `entites_custom`/`signaux_custom` ajoutées comme
   sources dans `app.py` (`get_review()`) et dans le badge
   `_count_review_items()` de `routes_dashboard.py` (§1.7). Reste à David :
   remplacer les 3 fichiers, redémarrer Flask, vérifier en conditions
   réelles que le panneau affiche maintenant des entrées.
