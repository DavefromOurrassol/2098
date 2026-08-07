# HANDOFF — session du 2 août 2026 (à uploader dans le nouveau chat)

*Session très dense, deux grands chantiers : (1) audit + nettoyage complet
du backlog historique, avec correction de plusieurs bugs réels trouvés en
creusant le code (dashboard, panneau Revue, cohérence entités) ; (2)
conception et construction d'un outil de traçabilité (`trace_injection.py`)
puis d'une refonte majeure de `generate.py` — un mode "Forcer un élément"
qui garantit la présence d'une instance/un événement/un signal précis dans
un ou plusieurs articles générés. Le mode Forcer a nécessité une dizaine
d'allers-retours de debug en conditions réelles (David a testé en direct),
chaque bug corrigé étant vérifié soit par du code, soit par un test
fonctionnel avec des données synthétiques.*

---

## 1. Backlog historique — audit et nettoyage (première moitié de session)

Tous les points ouverts identifiés en début de session ont été traités :

- **P8** (426 fiches `officialise_minimal`) — **clos**, preuve trouvée
  directement dans les fiches (marqueur `## Notes` daté du 27 juin 2026,
  426 occurrences exactes). Le backlog le donnait comme "jamais lancé",
  c'était faux — traité en une fois, la trace ne s'était juste jamais
  propagée aux handoffs suivants.
- **`validate`** (dernière entrée du panneau GUI jamais testée) — testé
  par David, RAS. Les 18 entrées du panneau sont maintenant validées.
- **Entrée Groenland sans `type_entite`** (`policy_reform`) — corrigée
  (`check_type_entite_coherence.py --apply`), fichier livré.
- **`--cible` sur plusieurs chantiers** — vérifié fonctionnel avec des
  données de test (n'affecte que le chantier ciblé).
- **Entrée fantôme `restructure_zones`** dans `scripts_config.json` —
  déjà absente, vérifié.
- **`queue_sahel_v2.yaml`** — supprimé par David.
- **Bug dashboard** (entrée fantôme `: 1` dans la carte INSTANCES) —
  cause réelle : `instance_template.md` compté comme une 711e instance
  par `_stats_instances()`/`_stats_enrichissement()` (pas de filtre sur
  le gabarit). Corrigé dans `routes_dashboard.py`.
- **Panneau Revue vide** — deux causes cumulées : `enrich_minimal.py`
  était le seul `yaml.dump()` du pipeline sans `sort_keys=False`
  (cassait le parseur de `app.py`) ; et `entites_custom`/`signaux_custom`
  n'étaient jamais lus comme sources par `/api/review`. Les deux
  corrigées.

**Fichiers livrés dans cette partie** (déjà transmis en cours de
session) : `routes_dashboard.py`, `enrich_minimal.py`, `app.py` (version
initiale), `policy_reform.md`, `scripts_config.json` (version initiale).

---

## 2. `trace_injection.py` — nouvel outil de traçabilité

Script diagnostic pur (lecture seule, aucun appel LLM) qui reconstitue,
pour un slug donné (instance/événement/signal), son origine, sa
propagation dans l'espace (scénarios/zones) et le temps, son réseau
causal (variables influencées) et relationnel (alliances/oppositions ou
acteurs impliqués), et son usage aval dans les articles publiés.

- Auto-détection du type, ou forcé via `--type`.
- Sortie markdown (lisible) ou `--json` (structuré), `--report` écrit les
  deux dans `documentation/need_action/`.
- `--list` pour lister les slugs disponibles par type en CLI.
- Résolution tolérante : accepte qu'on lui passe un slug d'instance/
  event_instance à la place du slug d'entité/archétype attendu (dérive
  automatiquement via le champ `entite:`/`archetype:`).
- Résolution des zones (`geographie/{scenario}.md`) et des variables
  (`variables/{slug}.md`) en noms lisibles plutôt que des slugs bruts.
- Déduplication automatique entre "Description d'origine" (§1) et
  "Descriptif" (§2) si les deux textes se recoupent.
- Listes de slugs (acteurs, alliances) tronquées proprement (5-8 max +
  compteur) plutôt qu'alignées sur une seule ligne illisible.

**Intégration GUI** : nouvelle entrée `trace_injection` dans
`scripts_config.json` (section "entités — nettoyage"), menu Type →
Élément en cascade (même mécanisme que `undo_custom`), nouvelle route
`/api/trace/<slug>` dans `app.py`. Nouveau type `evenements` ajouté à
`/api/slugs` (manquait, seuls `entities`/`signals` existaient).

**Testé en conditions réelles par David** sur plusieurs slugs
(`insurrection_rust_belt`, `crise_gouvernance_amazonie`,
`courants_post_technocratiques_de_reconquete_democratique`) — fonctionne.

---

## 3. Mode "Forcer un élément" — refonte majeure de `generate.py`

Fonctionnalité demandée : forcer la génération d'un ou plusieurs articles
autour d'une instance/un événement/un signal précis, avec un article par
scénario retenu.

### Architecture finale (après plusieurs itérations avec David)

- **`mode_select`** en haut du panneau : **Semi-guidé** (comportement
  historique, inchangé) vs **Forcer** (nouveau).
- **Mode Forcer** :
  - Type d'élément (instance/événement/signal) → liste filtrée en
    cascade.
  - Scénarios : "tous" (= tous les scénarios où l'élément existe
    *réellement*, pas les 6 sans distinction) ou sélection multiple
    précise, restreinte dynamiquement à ce qui est disponible.
  - Zone(s) : dépend uniquement de l'élément choisi (pas des scénarios
    cochés) — "tous" par défaut, ou zones réellement associées à
    l'élément. **Une zone cochée remplace le choix de scénarios** (une
    zone appartient à un seul scénario, donc plus précise) plutôt que de
    le filtrer en "ET" — ancien comportement produisait des combinaisons
    impossibles.
  - Titre suggéré : jamais éditable dans ce mode, toujours généré par
    l'IA (angle spécifique aussi écrasé automatiquement — directive
    générée à partir de la description de l'élément forcé).
  - **Un article généré et sauvegardé par scénario retenu** (boucle dans
    `generate.py`, résumé du lot affiché en fin de run).
- **Mode Semi-guidé** : strictement inchangé (scénario unique, sélection
  automatique, zone/titre/angle éditables).
- **Champs indépendants du mode** : Thématique, Ligne éditoriale, Angle
  spécifique (Angle masqué en mode Forcer, sans effet dans ce mode).
- Les 4 champs partagés (Thématique/Ligne éditoriale/Longueur/Angle) se
  réinitialisent à leur valeur par défaut après chaque lancement, pour
  éviter qu'une valeur oubliée d'un essai précédent ne se glisse
  silencieusement dans le suivant.

### Bugs trouvés et corrigés en conditions réelles (chronologie)

1. **Libellés "(optionnel)" doublés** — bug préexistant sur 9 champs du
   fichier (pas propre à cette session), le GUI ajoute déjà la mention
   automatiquement. Nettoyé partout.
2. **Menu Type vide** — `choices` en liste de chaînes au lieu du format
   `{value, label}` attendu partout ailleurs dans le fichier.
3. **Entités affichées comme des instances** — `_scan_entity_slugs()`
   (dans `app.py`) retombait sur les slugs d'*instances* quand
   `_entities_list.json` était absent/périmé. Corrigé à la source :
   dérive maintenant les vrais slugs d'entités depuis le champ `entite:`
   de chaque fiche instance.
4. **Menu Zone toujours vide** — deux causes : (a) mauvais nom de
   paramètre transmis par le GUI (`element_type` envoyé, `forcer_type`
   lu côté serveur) ; (b) le calcul des zones dépendait des scénarios
   déjà cochés, qui n'étaient jamais pré-sélectionnés par défaut.
   Redesigné : la zone ne dépend plus que de l'élément choisi.
5. **"tous" + un scénario précis cochables en même temps** — chips
   rendues mutuellement exclusives dans `app.js`.
6. **Bouton "Sauvegarder" disparu** — `yaml_files` laissé par erreur
   dans la config après le passage de `config_fields` vers `options` ;
   pointait vers un panneau YAML brut obsolète. Retiré ; le bouton
   d'action est désormais "Lancer" (mécanisme CLI), pas "Sauvegarder"
   (mécanisme YAML) — changement de nom inévitable, pas un bug résiduel.
7. **Thématique/Angle utilisant une valeur d'un essai précédent, malgré
   un menu affichant la bonne valeur à l'écran** — bug le plus sérieux
   de la session : lors du passage de `config_fields` vers `options`,
   seuls les flags `--forcer-*` avaient été ajoutés au parsing CLI de
   `generate.py`. Les 7 champs préexistants (`--thematique`,
   `--ligne-editoriale`, `--article-longueur`, `--article-angle-specifique`,
   `--scenario`, `--zone-slug`, `--article-titre-suggere`) étaient
   envoyés correctement par le navigateur mais **jamais lus côté
   serveur** — `generate.py` retombait sur les valeurs figées de
   `config.yaml`. **Corrigé : tous les champs sont maintenant lus et
   appliqués en override.** Ce bug touchait potentiellement aussi le
   mode Semi-guidé (le scénario du menu n'était peut-être jamais
   réellement pris en compte).
8. **Zone d'ancrage géographique incohérente** (article sur un événement
   au Moyen-Orient, mais "ancré" à Genève) — la directive venait de
   `_dominant_zone(filtered_instances)`, calculée sur les 6 instances
   auto-sélectionnées génériques, jamais sur l'élément forcé. Fonctionnait
   par coïncidence pour une instance forcée (elle devient la seule
   `filtered_instance`), jamais pour un événement forcé. Corrigé en
   propageant explicitement la vraie zone de l'élément forcé (par
   scénario) dans `config["zone_slug"]`.

### Fichiers livrés (versions finales de fin de session)

| Fichier | Statut |
|---|---|
| `generator/loader.py` | Rotation à mémoire des instances (§4), résolution du forçage, scoring/plafond des événements (§5) |
| `generator/snapshot.py` | `forcer_config`/`dry_run` threadés, rotation instances |
| `generator/prompt_builder.py` | Signal forcé prioritaire, angle forcé, plafond événements/zones (§5) |
| `generator/generate.py` | Réécriture quasi complète — deux modes, parsing CLI complet, boucle multi-scénarios, zone-remplace-scénario |
| `generator/config.yaml` | Bloc `forcer:` documenté |
| `gui/app.py` | Routes `/api/trace/*`, `/api/forcer/*`, cases `forcer_scenarios`/`forcer_zones` dans `/api/slugs`, fix `_scan_entity_slugs` |
| `gui/app.js` | `slug_extra_params`, type `dynamic_multi_select`, exclusivité "tous", réinitialisation post-run |
| `gui/scripts_config.json` | Entrée `trace_injection`, refonte complète de l'entrée `generate` |

**Tous testés soit par du code (syntaxe + tests fonctionnels avec
données synthétiques), soit en conditions réelles par David — la
dernière itération (log du conflit Israël-Iran, zone Moyen-Orient/Golfe)
a confirmé thématique correcte, scénario correct, zone correcte.**

---

## 4. Passage à l'échelle — événements et géographie (fin de session)

Constat de David : le vault va grossir, il faut sélectionner les
éléments les plus pertinents pour l'écriture sans perdre la vision
globale du monde. Audit fait section par section du prompt :

- **Déjà protégés** (rotation à mémoire ou plafond existant) :
  instances, jalons historiques (signaux), tensions systémiques,
  variables d'état.
- **Non protégés, trouvés en vérifiant** : événements custom (aucun
  plafond, tous inclus systématiquement) et géographie (liste "Autres
  zones" parcourue en entier, déjà ~60 zones sur un scénario mature).

**Principe retenu, appliqué aux deux** : une couche large et peu coûteuse
qui préserve la vision globale (résumé une ligne, plafonné plus haut,
noms seuls au-delà), et une couche détaillée filtrée par pertinence +
rotation à mémoire (plafonnée plus bas). L'élément forcé (mode Forcer)
est toujours garanti présent dans la couche détaillée, jamais soumis au
tri.

**Réutilise le matériau déjà standardisé sur les fiches** plutôt qu'une
nouvelle heuristique : `portee` (locale→globale, `VALID_PORTEES` dans
`inject_custom_events.py`) + amplitude réelle des `impact_sur_variables`
+ recoupement avec les variables de la thématique — même principe que le
score déjà utilisé pour les instances.

- Événements : 8 max en détail complet (§ Trajectoire), 25 max en
  résumé (§ Perturbations), noms+dates seuls au-delà.
- Géographie : zones pertinentes (ancrage) toujours en détail complet
  sans plafond, 20 max en résumé, noms seuls au-delà.

**Testé fonctionnellement** (données synthétiques) : plafonds respectés,
élément forcé toujours inclus. **Pas encore testé en conditions réelles
par David** — à faire en priorité à la prochaine session.

---

## 5. Fichiers livrés cette session (récapitulatif complet)

`routes_dashboard.py`, `enrich_minimal.py`, `policy_reform.md`,
`trace_injection.py`, `loader.py`, `snapshot.py`, `prompt_builder.py`,
`generate.py`, `config.yaml`, `app.py`, `app.js`, `scripts_config.json`.

Tous validés syntaxiquement (`ast.parse`/`node --check`). La plupart
testés fonctionnellement avec des données synthétiques en sandbox ; les
mécanismes GUI les plus critiques (mode Forcer de bout en bout) testés
en conditions réelles par David, avec correction itérative jusqu'à
validation.

---

## 6. Point de reprise suggéré pour la prochaine session

1. **Tester en conditions réelles le plafonnement événements/géographie**
   (§4 ci-dessus, jamais vérifié hors sandbox) — vérifier que le prompt
   reste cohérent et que l'élément forcé apparaît toujours bien en
   détail complet.
2. **Vérifier que le mode Semi-guidé fonctionne aussi correctement**
   après le fix du bug §3.7 — pas explicitement retesté en conditions
   réelles depuis le correctif (seul le mode Forcer a été revalidé).
3. Envisager, si le volume d'événements/zones continue de grossir,
   d'ajuster les plafonds actuels (8 événements détaillés / 25 en
   résumé ; 20 zones en résumé) — chiffres choisis par défaut, jamais
   discutés avec David dans le détail.
4. Nettoyer les fichiers d'état de rotation si besoin de repartir sur
   une mémoire vierge : `generator/state/instance_usage.json`,
   `generator/state/trajectory_usage.json`,
   `generator/state/event_relevance_usage.json` (nouveau) — aucun risque
   à les supprimer, ils se régénèrent seuls.
5. Reste du backlog historique : rien d'identifié comme encore ouvert à
   ce stade — l'audit du §1 a épuisé tout ce qui restait.
