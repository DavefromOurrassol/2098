# Backlog consolidé — Ourrassol 2098
*Mis à jour le 15 juillet 2026 — fusionne le backlog historique et les items des sessions du 11, 12, 13, 14 et 15 juillet*

Légende priorité : 🔴 bloquant/urgent · 🟡 important · 🟢 confort · ⚪ improvisation libre / pas pressé

---

## ✅ Checklist manuelle (`check_session.sh`) — testée et close le 4 juillet

*Les 4 items reportés depuis `check_session.sh` ont été vérifiés :*

- [x] **Bouton LLM carte** (`/api/carte/propose`) — testé en vrai depuis le navigateur, OK.
- [x] **Bandeau diagnostic orange de l'onglet Carte** — non affiché, et c'est normal : ce bandeau (`#carte-diagnostic` dans `app.js`) est **conditionnel**, il ne s'affiche que s'il existe des pays FR sans correspondance trouvée sur le fond de carte Leaflet (noms mal mappés dans `gui/static/pays_mapping.json`). Absence de bandeau = aucun pays mal mappé actuellement, cohérent avec le check `pays_mapping.json` déjà vert dans `check_session.sh`. Rien à corriger ; à re-tester seulement après un futur ajout de pays au mapping.
- [x] **Hachures de zone** — vérifiées visuellement sur un scénario >8 zones N1, OK.
- [x] **Rapport d'impact** — testé sur un vrai cas (pays avec sous-zones connues), OK.

---

## ✅ Vérification 10 min — faite et propre le 4 juillet

- [x] `generator/complete_geographie_coverage.py` contient bien le fix #9 (`grep -c "nouvelles_zones_ce_batch"` ≥ 2, confirmé).
- [x] `python3 check_zones_coherence.py --all` propre sur les 6 scénarios.

---

## P2quinquies ✅ — ID de modèle `mistral-small` corrigé + bug de sauvegarde config résolu
**Appliqué et confirmé le 4 juillet.**

Deux correctifs liés :
1. `mistral-small` (sans suffixe, invalide) → `mistral-small-latest` dans `gui/config.json` (`llm.model_mistral`) **et** dans `generator/llm_client.py` (`_DEFAULT_MODELS["mistral"]`). ✅ Les deux fichiers corrigés et remplacés.
2. Bug #14 du handoff : `/api/config` (POST) effaçait les `available_models_mistral`/`available_models_claude` à chaque sauvegarde depuis le GUI (ordre d'écrasement dans `update_config()`). Patché dans `app.py`, confirmé fonctionnel.

État final `gui/config.json.llm` :
```json
{
  "provider": "mistral",
  "model_mistral": "mistral-small-latest",
  "model_claude": "claude-sonnet-4-6",
  "available_providers": ["mistral", "claude"],
  "available_models_mistral": ["mistral-small-latest", "mistral-large-latest"],
  "available_models_claude": ["claude-sonnet-4-6", "claude-sonnet-5", "claude-opus-4-8", "claude-haiku-4-5-20251001"]
}
```

---

## P2quater ✅ — Modèle LLM par défaut pour Carte / Coverage — tranché le 4 juillet
**Décision : reste `mistral` / `mistral-small` par défaut.** `claude-sonnet-4-6` disponible en sélection ponctuelle dans le GUI pour la carte/coverage si besoin de fiabilité géographique accrue (cf. bug #3 du handoff), mais pas le défaut global.

**Bug corrigé au passage (#12 du handoff)** : le sélecteur de modèle du GUI était vide (case présente, aucune option) faute des clés `available_providers`/`available_models_mistral`/`available_models_claude` dans `gui/config.json`. Fix appliqué — voir handoff pour la commande exacte.

*(11 juillet : ce sélecteur a été réarchitecturé en toggle "Forcer ce modèle" + routing par tier — voir P14 ci-dessous. Le défaut effectif dépend maintenant du tier de la tâche, pas d'un seul réglage global.)*

---

## P1bis ✅ — Documenter l'onglet Carte + rapport d'impact dans le manuel principal
**Fait le 4 juillet.**

`USER_MANUAL_carte_et_couverture_4juillet.md` fusionné dans `USER_MANUAL_COMPLET.md` (section "Onglet Carte — workflow détaillé", §7) : workflow pas à pas, cas Royaume-Uni, bouton "Ignorer", bandeau diagnostic, choix du modèle LLM (mis à jour avec le sélecteur GUI fonctionnel depuis les bugs #12/#14), résumé des commandes courantes. `USER_MANUAL_carte_et_couverture_4juillet.md` peut désormais être archivé — le contenu à jour vit dans `USER_MANUAL_COMPLET.md`.

---

## P2ter ✅ — 32 pays "sous-zone sans N1" — déjà résolu, liste obsolète
**Confirmé clos le 4 juillet, après vérification.**

La liste de 32 pays ci-dessous provenait de `BACKLOG_4juillet.md`, écrit **avant** la fin de la session du jour. Le passage complet de P2bis (review/apply sur les 6 scénarios) et le fix du bug #10 (`regenerate_zones_pays.py` + `add_pays_to_zone.py` pour les 2 derniers cas résiduels Arctique/Groenland) ont traité cette catégorie en même temps que les pays totalement absents. Confirmé par `check_zones_coherence.py --all` : "✓ Tous les pays présents ont une zone N1" sur les 6 scénarios, sans aucun avertissement `⚠`. Rien à faire.

<details>
<summary>Liste originale (obsolète, conservée pour référence)</summary>

| Scénario | Pays concernés |
|---|---|
| fortress_world | — (aucun) |
| new_sustainability | Espagne, Belgique, Portugal, Vietnam, Cambodge, Nigeria, Burkina Faso, Corée du Sud, France |
| eco_communalism | Groenland, Pologne, République tchèque, Chine |
| policy_reform | Sénégal, Singapour, Groenland |
| reference | Mali, Niger, Tchad, Kirghizistan, Tadjikistan, Afghanistan, Soudan, Cambodge, Tuvalu, Kiribati, Îles Marshall, Italie, République du Congo |
| breakdown | Estonie, Lettonie, Lituanie |

</details>

---

## P3 ✅ — Tests end-to-end formulaires guidés — CLOS le 11 juillet

- [x] **Generate** : sélecteur de zone testé — cassé puis corrigé en cours de route (bug #21 du handoff : `config_file` désynchronisé de `yaml_files.path` après le fix bug #16, pour `generate` et `generate_series`). Article généré avec succès.
- [x] **Couverture `journaux.yaml`** : trou massif découvert (160 zones N1 sans journal sur 160, 0 orphelin) via `check_journaux_coherence.py`. Comblé intégralement via `generate_journaux.py --all --update`. Confirmé : 0 manquant, 0 orphelin sur les 6 scénarios.
- [x] **Generate series** : chips thématiques testées, sauvegarde d'abord "muette" (bug #23 du handoff — Flask pas redémarré, pas un bug de code), résolu après redémarrage. Série de 2 articles générée avec succès.
- [x] **Rédaction de 6 journalistes par journal**, par thématique — générée pour les 290 journaux existants. **Vérification finale faite le 11 juillet** : a révélé le bug #26 (handoff) — cause racine du problème journal/journaliste incohérent, sans lien avec la fiabilité des modèles. Corrigé (`config.yaml`, `prompt_builder.py`, `generate.py::validate_config()`), confirmé par régénération d'article réussie.
- [x] **Create entities (custom)** — testé bout-en-bout avec succès le 11 juillet, après correction de plusieurs bugs bloquants découverts en cours de route : blocage `input()` en lancement GUI (bug #30 handoff), flag fantôme `--scenario` (bug #31), reliquat `resp` non défini (bug #32), double-clic sur "Ajouter à la queue" (bug #33), `--n`/variables non plafonnés en mode auto (bug #34).
- [x] **Inject events (custom)** — testé bout-en-bout avec succès le 11 juillet, `zone_hint` + `acteurs_hint` confirmés fonctionnels (référence croisée vers une vraie instance créée dans la même session). Bug trouvé et corrigé : `variables_hint_count` non appliqué en filtre dur (bug #34 handoff, occurrence 2). Mode auto également bloqué sur `input()` non couverts, même famille de fix que Create entities (bug #30 bis).

**P3 est intégralement clos.** Voir `HANDOFF_CONSOLIDE.md` §3bis pour le détail complet des bugs trouvés pendant ces deux derniers tests.

---

## P4 ✅ — Test streaming SSE — CLOS le 13 juillet

Testé par David depuis le GUI : `validate.py` (sans flags — n'a jamais eu de `--dry-run`, correction de l'item de backlog lui-même, script lecture seule par nature) et `enrich_minimal.py --limit 2 --dry-run` (formulaire `slug_select` + streaming). Les deux fonctionnent, logs en direct confirmés dans les deux cas.

---

## P6 ✅ — `scripts_config.json` : vérification complète — CLOS le 11 juillet

Croisement systématique des `flag` déclarés côté GUI avec l'`argparse` réel de chaque script, sur les 19 entrées de `scripts_config.json`. Résultats : 2 flags fantômes trouvés et supprimés (`--scenario` sur `create_entities` et `inject_events`), `zone_hint` confirmé fonctionnel malgré son absence de la doc `QUEUE_TEMPLATE` (voir P16), tous les `config_fields` (formulaires `queue.yaml`) vérifiés lus correctement, `restructure_zones.py` confirmé absent du disque (attendu, P7). Détail complet : `HANDOFF_CONSOLIDE.md` §3bis, point 6.

---

## P7 ✅ — Restructure zones (pipeline) — CLOS le 13 juillet

Outil de restructuration de zones construit en 3 étapes, intégré directement dans l'onglet Carte (pas de script CLI séparé — décision prise en cours de scoping, split/merge collant déjà au modèle carte existant, rename/reparent nécessitant une UI dédiée à l'arbre plutôt qu'à la géographie).

**Étape 1 (rename)** : `/api/carte/renommer_zone` + `/api/carte/impact_renommage_zone`. Propage vers `zones[].slug`/`nom`, `zones[].parent` des enfants directs, wikilinks `sous [[...]]`, **`relations.allies`/`rivaux` de n'importe quelle zone du scénario** (pas seulement les enfants — découvert en testant), lignes `**Rivaux**`/`**Alliés**` en texte brut du corps markdown, `instances/*.md`+`event_instances/*.md` (`localisation.zone`), `zones_pays.json`. UI : bouton ✏️ sur chaque zone niveau 1 de la légende carte.

**Étape 2 (reparent)** : `/api/carte/reparent_zone` + `/api/carte/impact_reparent_zone`. Déplace une zone (et tout son sous-arbre) vers un nouveau parent à n'importe quelle profondeur, avec recalcul en cascade du `niveau` (YAML + niveau de titre markdown) sur toute la branche. Anti-cycle intégré. Deux extensions : promotion en zone niveau 1 autonome (`nouveau_parent_slug` vide → `parent: null`) et création d'une nouvelle zone niveau 1 à la volée (`/api/carte/creer_zone_niveau1`, schéma conforme à `enrich_geographie_recursive.py`). UI : arbre hiérarchique en lecture seule (clic sur une zone de la légende → `/api/carte/arbre_zone`) avec bouton "↗️ déplacer" par nœud non-racine.

**Étape 3 (bascules pays)** : la détection (`sous_zones_orphelines` dans `carte_impact()`) existait déjà — seul un bouton d'action manquait. `app.js` uniquement : bouton "↗️ rattacher à {nouvelle_zone}" par sous-zone orpheline détectée dans le rapport d'impact de bascule, appelant directement l'endpoint reparent de l'étape 2.

**Scope initial du backlog en partie obsolète** : `registre_evenements.md` et `zones_proposees.yaml` n'existent pas (retirés du scope). `instance.localisation.zone`/`event_instance.localisation.zone` couverts par l'étape 1. Pas de script `restructure_zones.py` séparé — l'entrée fantôme dans `scripts_config.json` (section maintenance) peut être retirée.

**4 vraies incohérences géographiques trouvées dans le vault en testant** (voir `HANDOFF_CONSOLIDE.md` §3ter pour le détail) : Barcelone-Hub + Corridor ibérique énergétique (`new_sustainability`, sous `ameriques_reconfigurees`) et Nœud Mnemos du Bassin Pannonien (`breakdown`, sous `arc_eurasien_central`) restent à corriger — Cracovie déjà corrigée en direct pendant les tests.

---

## P8 ⚪ — Enrich 426 fichiers `officialise_minimal`
**Script existant : `enrich_minimal.py` — en cours, gros chantier**

Coût API estimé ~$37 pour la totalité. Lancer après validation complète du pipeline géographique (fait) — pas de dépendance bloquante restante. Depuis le 11 juillet, tourne sur le tier `creative_souple` (`mistral-large-latest` par défaut) via `llm_client.py` — le coût réel pourrait différer légèrement de l'estimation initiale (faite sur Claude), à recalculer si besoin avant de lancer en masse.

---

## P9 ✅ — Nettoyage dossier orphelin `evenements_custom`
**Fait et confirmé le 4 juillet.**

Vérification approfondie (tailles de fichiers + grep sur les 36 scripts, cf. handoff) : le sens était inversé par rapport au texte original du backlog. Le dossier actif et lu par le code est `evenements_custom/` **à la racine du vault** (`queue.yaml` 3429 octets, `processed.yaml` 246 946 octets, `needs_review.yaml` 14 octets). L'orphelin est `generator/evenements_custom/` (`queue.yaml` et `queue.yaml.bak`, tous deux 0 octet) — supprimé (`rm -rf generator/evenements_custom`).

**Origine probable de l'orphelin, découverte en creusant (bug #16 du handoff)** : l'entrée `inject_events` de `scripts_config.json` déclarait `evenements_custom/queue.yaml`, résolu par le GUI relativement à `pipeline_dir` (= `generator/`) au lieu de `vault_root` — donc toute tentative d'ajout via le formulaire GUI "Ajouter à queue" aurait écrit dans le mauvais fichier (vide, jamais lu par `inject_custom_events.py`). Corrigé avec le reste du bug #16.

## P12 ✅ — Retraitement des entités custom en échec — clos
**Découvert et traité intégralement le 4 juillet.**

Parcours complet : 25 idées initiales (dont "Almaty Zone Friction" retirée — doublon conceptuel avec "Zones Grises Tampons") → plusieurs vagues de retraitement ayant révélé et corrigé au passage :
- bug #17 (rate limiting Mistral, fix centralisé dans `llm_client.py`)
- bug #18 (fiabilité `mistral-small` sur les `variables_potentielles` — choix contraint mal respecté ; contourné en basculant sur `claude-sonnet-4-6` pour le dernier lot ; **à requalifier depuis le 11 juillet, voir P17**)
- 9 vrais doublons identifiés et abandonnés en cours de route (Corridors Eurasiens Convoyage, Tresse Verte Corridor, Arctique Nordark, Communes Rust Belt, Communes Rust Belt Zones Libres, Corridor Arctique Nordique, Rust Belt Communes Libres, Zone Usines Forteresses Eurasie, Zones Grises Globales)
- **✅ Toutes les idées restantes créées avec succès** (`needs_review.yaml` confirmé vide en fin de session)

**`communes_rust_belt`** : finalement déjà correct dans sa fiche `.md` (description/tension/variables déjà remplies depuis le 27 juin) — `needs_review.yaml` était simplement périmé, aucune action nécessaire sur ce point précis.

**Découverte en creusant ce point** : bug #19 (handoff) — `_entities_list.json` accumulait des doublons (645 entrées / 571 slugs uniques) faute de dédoublonnage à l'ajout. Fix appliqué + fichier nettoyé fourni (`_entities_list_clean.json`) + `create_entities_and_instances.py` mis à jour.

**P12 est entièrement clos, confirmé** par `check_zones_coherence.py --all` : 6 scénarios propres (breakdown 89/36 N1, fortress_world 71/21, new_sustainability 60/15, eco_communalism 87/42, policy_reform 61/15, reference 61/16), `zones_manquantes.yaml` vide. Registre `_entities_list.json` nettoyé et remplacé, script `create_entities_and_instances.py` à jour avec le fix #19.

---

## P13 ✅ — Migrer `complete_geographie_coverage.py` vers le retry centralisé de `llm_client.py` — CLOS le 11 juillet

Le délai fixe de 8s entre batches (fix du bug #8, avant l'existence du retry centralisé du bug #17) a été retiré des deux boucles concernées (`process_scenario`, `process_scenario_review`), ainsi que l'import `time` devenu mort. Le rate limiting est désormais purement réactif via `llm_client.py`, comme pour tous les autres scripts du pipeline. Un compte au palier large (ex. Scale) n'est plus ralenti artificiellement sur ce script.

**Bonus fait dans la foulée (11 juillet)** : l'anomalie architecturale distincte de `complete_geographie_coverage.py` (fonction `call_llm()` locale bypassant totalement `llm_client.py`, appel direct aux SDK) a aussi été corrigée à cette occasion — migré vers l'abstraction commune, tier `structured_strict`.

---

## P10 ✅ — Rapport d'impact : étendre aux entités — pas nécessaire, confirmé le 13 juillet

Question tranchée pendant le scoping de P7 : grep exhaustif du vault entier pour des wikilinks vers des slugs de zone en dehors de `geographie/{scenario}.md` — zéro résultat légitime (22 faux positifs initiaux, tous des collisions de nommage avec des entités homonymes, confirmées via `entites/{slug}.md`). `entites/` n'a besoin d'aucune propagation liée aux zones. Pas d'action nécessaire.

---

## P11 ✅ — CLOS le 14 juillet — Intégrer les scripts de diagnostic géographie au GUI

**Périmètre élargi en cours de route** : à l'origine juste `check_zones_coherence.py`, étendu aux 4 autres scripts de diagnostic géographie livrés le 14 juillet (David : "à terme ces outils de maintenance devront être intégrés dans le GUI"). 5 entrées ajoutées à `scripts_config.json` (section `maintenance`, après `complete_geographie_coverage`) :
- `check_zones_coherence` — `--scenario`/`--all`
- `check_type_entite_coherence` — `--scenario`/`--all`, `--apply` (badge P26)
- `check_origine_reelle_coherence` — `--scenario`/`--all`, `--resolve-llm`, `--write-zones-manquantes` (badge P22), `requires: ["check_type_entite_coherence"]` (avertissement non bloquant — les `type_entite` manquants faussent ce diagnostic, vécu en le construisant)
- `check_conventions_territoires` — `--scenario`/`--all` (badge P27)
- `scan_geographie_complet` — `--scenario`/`--all`, `--apply-type-entite`, `--resolve-llm`, `--write-zones-manquantes` (orchestrateur des 4 précédents)

**Non fait, à ne pas oublier** : le retrait de l'entrée fantôme `restructure_zones.py` (jamais existé comme script CLI, P7 vit dans l'onglet Carte) a été fait au passage, dans le même fichier. **Nécessite un redémarrage de Flask** pour apparaître dans la sidebar (remplacer le fichier sur disque ne suffit pas).

**Sous-tâche du 4 juillet toujours ouverte, distincte** : migrer la partie 1 de `gui/check_session.sh` (cohérence JSON `pays_mapping.json`/`zones_pays.json`) dans `check_zones_coherence.py --all`, pour ne plus avoir cette vérification en double dans un script shell séparé. Les parties 2 (environnement/process) et 3 (checklist manuelle) de `check_session.sh` restent hors scope de ce script.

---

## P14 🟢 — Nouveau (11 juillet) — Repasser le tier `strict` sur Claude au passage en production
**Durée : 1 min — une ligne à changer**

`llm_client.py::TASK_TIER_DEFAULTS["strict"]` est actuellement sur `mistral-large-latest` (phase de test délibérée). Repasser sur `claude-sonnet-5` (ou le modèle jugé approprié à ce moment-là) quand le pipeline d'articles passe en production. Concerne `api.py` (rédaction d'articles) et `generate_journaux.py` (génération des journalistes).

---

## P15 ⚪ — Nouveau (11 juillet) — Plafonner `acteurs_hint_count` en filtre dur
**Durée : 15 min, mineur**

`inject_custom_events.py` calcule `actors_hint_count` mais ne l'applique jamais en filtre dur sur le nombre d'acteurs réellement retenus dans l'instance générée (contrairement à `variables_hint_count`, corrigé le 11 juillet — voir bug #34 du handoff). Risque jugé moindre qu'un dépassement sur les variables, car un acteur en texte libre est explicitement toléré par le schéma. Pas le symptôme observé pendant les tests du 11 juillet — à corriger seulement si ça pose problème en usage réel.

---

## P16 ✅ — Documenter `zone_hint` dans `QUEUE_TEMPLATE` — CLOS le 13 juillet

Ajouté au bloc `CHAMPS :` + exemple, sur les deux fichiers concernés : `evenements_custom/queue.yaml` (`inject_custom_events.py`) et `entites_custom/queue.yaml` (`create_entities_and_instances.py`).

---

## P17 ✅ — CLOS le 16 juillet — Fiabilité `mistral-small` sur choix contraint, pipeline corrigé

Le bug #26 (handoff) a montré que la contamination culturelle observée les 6 et 11 juillet (bugs #18/#20 historiques) était en réalité causée par un bug de résolution de zone, reproduit à l'identique sur `mistral-small` **et** `mistral-large` — pas une limite de fiabilité modèle comme diagnostiqué initialement.

**Test fait le 16 juillet** : article régénéré sur `mistral-small-latest` (override manuel), même configuration que le test de référence du bug #26 (Bassin du Congo/`sante`, `eco_communalism`). Résultat propre sur tout ce qui était directement testable : langue 100% française, `zone_slug` correct (aucune fuite du bug #26), aucune incohérence numérique flagrante. Bon signal de fiabilité générale sur `mistral-small` une fois la cause de code éliminée.

**Limite du test, à noter honnêtement** : la règle 2 (non-transposition culturelle d'un allié, bug #20) n'a pas pu être mise à l'épreuve — l'article généré n'a invoqué aucune zone alliée externe, donc le modèle n'a pas eu l'occasion de bien ou mal l'appliquer sur ce run précis. David a choisi de considérer le test suffisant plutôt que de forcer artificiellement une interaction inter-zones (ce qui aurait faussé le test — le modèle doit décider lui-même d'en évoquer une). Si un doute resurgit spécifiquement sur la règle 2 avec `mistral-small`, ce n'est pas à 100% écarté par ce test.

---

## P18 ✅ — Vérifier `routes_dashboard.py` après le renommage "Modèle si forcé" — CLOS le 13 juillet

Cohérence confirmée sur le point d'origine (`data.llm` reflète `gui/config.json`, cohérent avec le commentaire déjà présent dans `app.js`). **Bug bonus trouvé** (#35) : `import json` manquant dans `routes_dashboard.py`, provoquant un `NameError` sur chaque appel à `/api/dashboard` dès que `_entities_list.json` existe (toujours le cas — 571 entrées) — cassait tout l'endpoint, pas juste la carte Entités. Fix appliqué et confirmé par David sur son GUI réel.

---

## P19 ✅ — CLOS le 15 juillet — Bug #27 (plausibilité logistique, cas isolé)

Incohérence de plausibilité logistique détectée sur un article test le 11 juillet : un personnage d'une zone alliée lointaine (Pacte Amazônia Viva, Amazonie) décrit comme arrivant par un moyen de transport purement local (pirogue depuis Kisangani, Congo), sans mention de la traversée intercontinentale attendue. Décision prise le 11 juillet : observer si ça se reproduit avant de renforcer `build_system_prompt()` (`prompt_builder.py`).

**Vérification faite le 15 juillet** : recherche (`grep`) sur tous les articles du vault pour des formulations de transport local associées à "depuis" — un seul autre résultat trouvé (`eco_communalism`/`sante`, 5 juillet), qui s'est révélé être un faux positif (emploi métaphorique de "pirogue", sans rapport avec un trajet ou un personnage distant). Aucune récidive réelle du pattern.

**Décision de David : fermer sans ajouter de consigne** — un seul cas réel sur plusieurs semaines de génération ne justifie pas d'alourdir `build_system_prompt()` (coût en tokens + risque de contradiction avec une autre règle existante). Une réouverture serait légitime si un nouveau cas apparaît, mais ce n'est plus un point de suivi actif.

---

## P20 ⚪ — Nouveau (12 juillet) — Enrichissement frontmatter pour publication web future
**Scoping fait, pas encore codé**

**Contexte** : anticiper la publication en ligne des articles générés en enrichissant le YAML frontmatter dès la génération, plutôt que de retraiter des centaines de fichiers a posteriori.

**Champs à ajouter au frontmatter des articles** :

| Champ                                  | Description                                                                                                                   |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `slug`                                 | Identifiant URL-friendly (évite de le dériver du titre à chaque fois, risques de collision/accents)                           |
| `chapo` / `excerpt`                    | Résumé court (2-3 lignes) pour pages de liste et meta description SEO                                                         |
| `image_prompt`                         | Prompt de génération d'image, produit par le LLM en même temps que l'article                                                  |
| `a_une_photo`                          | Booléen, **basculé manuellement** — choix éditorial, pas systématique                                                         |
| `image_principale`                     | Chemin vers l'image générée (rempli en post-traitement)                                                                       |
| `image_alt`                            | Texte alternatif (accessibilité + SEO)                                                                                        |
| `image_credit`                         | Traçabilité de la source/du prompt si génération IA                                                                           |
| `tags`                                 | Mots-clés distincts de `thematique` (orientés découverte/recherche lecteur)                                                   |
| `journaliste_slug`                     | Lien vers la fiche auteur (déjà présent dans `journaux.yaml`)                                                                 |
| `date_publication` vs `date_evenement` | À distinguer si publication différée / calendrier éditorial                                                                   |
| `articles_lies`                        | Liens vers 2-3 articles connexes — possiblement déductible automatiquement des entités partagées plutôt que généré par le LLM |
| `zone_principale`                      | Déjà présent via `localisation`, mais un champ dédié simplifie le filtrage géographique côté front                            |

**Génération d'images — option retenue (Option 1)** : le LLM génère un `image_prompt` descriptif **au moment de la génération de l'article** (même appel API, cohérence garantie avec le contenu). La décision d'illustrer (`a_une_photo`) reste manuelle et découplée de la génération technique — le prompt est stocké dès la création, réutilisable des semaines plus tard sans repasser par le LLM.

**Implémentation envisagée** :
1. Instruction dans `prompt_builder.py` pour que le LLM produise systématiquement `image_prompt` (description visuelle neutre : lieu, ambiance, éléments clés), même si non utilisé immédiatement.
2. `a_une_photo: false` par défaut, basculé à `true` manuellement (ou via script de sélection) par David.
3. Script séparé `generate_images.py` : scanne les articles `a_une_photo: true` sans `image_principale` renseignée, appelle l'API image, remplit `image_principale` + `image_alt`.

**Question ouverte** : rendu HTML — site statique généré (Hugo/Eleventy-like) à partir des YAML/Markdown, ou moteur de rendu intégré au pipeline Flask existant. Non bloquant pour enrichir le frontmatter dès maintenant.

---

## P21 ⚪ — Nouveau (12 juillet) — Journaux oraux, orateurs itinérants
**Scoping décidé, pas encore codé**

**Contexte** : pour certains scénarios, des orateurs itinérants informent les communautés en sessions orales plutôt que par écrit — pertinent notamment pour `eco_communalism` et/ou `breakdown`, scénarios où l'infrastructure de diffusion écrite/numérique est dégradée ou volontairement rejetée au profit du lien communautaire direct.

**Scoping décidé** : variante coexistant avec l'écrit au sein d'un même scénario — pas un scénario entier qui bascule en mode oral. Certains journaux d'un scénario donné seront oraux, d'autres resteront écrits.

**Structure technique** :
- **Journal** : champ `type_diffusion` (`ecrit` / `oral` / `mixte`) sur l'entité journal dans `journaux.yaml`, pour router `prompt_builder.py` vers le bon registre via la logique existante de résolution de profil (`get_journal_profile()` adaptée).
- **Orateur — entité séparée (Option B décidée, Option A "réutiliser journaliste_slug avec métier élargi" écartée)** : nouveau type d'entité `orateur`, distinct de `journaliste`, avec ses propres attributs — itinérance entre communautés, communautés desservies, réputation orale, possible style rhétorique propre. Implique un nouveau lien dans `journaux.yaml` et une logique de résolution de profil adaptée (variante de `get_journal_profile()`).

**Registre oral dans `prompt_builder.py`** (différences vs écrit) : adresse directe à l'auditoire, formules d'ouverture/clôture ritualisées, répétitions rhétoriques, pas de mise en page journalistique (pas de chapô, pas de sous-titres), structure accroche → développement → appel à l'action ou question ouverte finale, possibilité de call-and-response.

**Champs frontmatter spécifiques aux articles oraux** :

| Champ | Description |
|---|---|
| `duree_estimee` | Calibrer la longueur du texte à un temps de parole réaliste |
| `lieu_diffusion` | Place publique, marché, assemblée... — granularité plus fine que `localisation` |
| `mode_reception` | Assemblée silencieuse, discussion ouverte, etc. — capture l'ambiance sociale |

---

## P22 — Garde-fou de cohérence géographique via `origine_reelle`

### Signal 1 (origine_reelle vs chaîne de parenté) — ✅ CONSTRUIT ET CLOS le 14 juillet

**Script livré : `check_origine_reelle_coherence.py`** (`generator/`). Compare le pays d'une zone `ville`/`region_administrative` à l'union des pays de toute sa lignée d'ancêtres — avertissement seul, jamais de blocage (confirmé : le taux de faux positifs d'une première heuristique mots-clés était de 5/9 le 13 juillet).

**Résolution en cascade** : extraction directe (pays déjà écrit dans le champ) → alias adjectival (`"américain"` → États-Unis) → table statique `VILLE_PAYS` (à enrichir manuellement au fil de l'eau) → `--resolve-llm` (batch, tier `structured_strict`, résultat mis en cache dans `cache_ville_pays_llm.json`, jamais repayé).

**Extension "candidats"** : pour chaque incohérence, cherche automatiquement une zone N1 du même scénario qui revendique déjà le pays en question, et si trouvée, la propose comme cible de reparent — plus besoin de chercher soi-même. Si aucun candidat, propose l'écriture dans `zones_manquantes.yaml` (`--write-zones-manquantes`, opt-in, même schéma que `complete_geographie_coverage.py` + 2 champs de traçabilité `origine`/`zone_incoherente_a_reparenter`).

**Extension "racine N1"** : chaque incohérence liste aussi la racine N1 à ouvrir dans la Carte (peut différer du parent immédiat si celui-ci est lui-même une sous-zone — cas réel : `delta_rhone_fermes_verticales` sous `corridor_iberique_energetique`, lui-même sous `nouveau_califat_barcelone`, la vraie racine à chercher).

**Tableau récapitulatif markdown** : généré automatiquement en fin de run, prêt à copier tel quel (scénario / cas problématique / zone de départ / racine N1 / candidat).

**Trois bugs de données découverts et corrigés dans la logique de résolution en testant sur le vrai vault** (invisibles sur un cas isolé) :
1. `type_entite` totalement absent sur certaines entrées `origine_reelle` (27+ cas trouvés) — voir nouvel item de backlog dédié à la réparation.
2. `type_entite: region_administrative` ou `autre` sur des territoires qui sont pourtant des entrées de premier rang dans `zones_pays.json` (Polynésie française, Groenland) — `_compte_comme_pays()` généralisée : seul `type_entite: ville` reste exclu, tout le reste se fie à une correspondance exacte avec la liste de référence.
3. Convention de nommage du Groenland incohérente entre scénarios (`"Groenland"` autonome dans certains, implicitement fondu dans `"Danemark"` dans d'autres) — `VILLE_PAYS["nuuk"]` résout maintenant vers les deux (`["groenland", "danemark"]`), laisse remonter tous les candidats plausibles plutôt que d'en imposer un.

**Résultat final, 6 scénarios, confirmé par David le 14 juillet : 0 incohérence.**

### Signal 2 (cohérence de patron spatial) — ⚪ toujours scopé, pas construit

Comparer la description/le type d'une zone au `state_logic` du scénario (voir P24 étape A, déjà livré). Dépend de `patrons_spatiaux.py`, livré mais pas encore consommé par aucun script du pipeline.

---

## P23 ✅ — CLOS le 14 juillet — Corriger les 3 dernières incohérences géographiques trouvées dans le vault (13 juillet)

Les 3 cas listés le 13 juillet sont soit déjà corrigés, soit n'étaient jamais de vraies anomalies :
- `barcelone_hub`, `corridor_iberique_energetique` → corrigés (sous `nouveau_califat_barcelone`, nouvelle zone N1 Ibérie)
- `noeud_mnemos_pannonie` → **n'était jamais une vraie anomalie** : `arc_eurasien_central` liste bien la Hongrie dans son `origine_reelle` complet (~25 pays, pas les 5 identifiés en lecture rapide initiale). Erreur d'appréciation, pas un bug du vault.

---

## P24 — Générateur top-down de zones cohérent avec la logique des scénarios
**Scoping approfondi fait — voir `APPROCHE_ZONING_GEOGRAPHIE_SCENARIOS.md` pour le détail complet**

**Constat de départ** : le pipeline géographique a 2 passes bottom-up (`build_geographie_monde.py`, `enrich_geographie_recursive.py` — les zones émergent du narratif déjà écrit) et 1 passe top-down mais naïve (`complete_geographie_coverage.py` — juge un rattachement pays→zone sur la seule ressemblance textuelle avec `origine_reelle`, sans jamais revalider contre la logique systémique du scénario). C'est la cause racine des anomalies trouvées et corrigées cette semaine (P23, P25).

**Découverte clé** : le vault contient déjà, dans `variables/{variable}.md → states.{scenario}.state_logic`, le patron de structuration spatiale exact de chaque scénario (`organisation_territoires` en premier lieu, aussi `geopolitique_conflits`, `frontieres_du_systeme`) — jamais exploité pour la génération de zones.

**Recherche documentaire menée** (7 sources externes lues et croisées avec le vault — détail et bibliographie complète dans le document dédié) : le Global Scenario Group original (Raskin et al., 2002), *Global Trends 2040* du NIC/CIA (2021), *The Limits to Growth* (Meadows/Club de Rome, 1972), un rapport SmartCSOs, un compte-rendu Futuribles sur la réinterprétation locale des institutions "universelles", la méthode d'analyse morphologique de Michel Godet, la thèse de Thierry Gaudin.

### Étape A — ✅ CONSTRUITE ET TESTÉE le 14 juillet

**Fichiers livrés** :
- **`extract_state_logic.py`** (`generator/`) — parseur générique de n'importe quelle fiche `variables/{variable}.md → states.{scenario}.state_logic`. Gère la sanitisation des clés wikilink Obsidian (`[[xxx]]`) dans les blocs `coupling_intensity`, qui cassent un `yaml.safe_load` brut.
- **`patrons_spatiaux.py`** (`generator/`) — formalise le patron spatial des 6 scénarios. Les citations (`state_logic`, `state_logic_complementaire` sur `organisation_territoires`/`geopolitique_conflits`/`frontieres_du_systeme`) sont **chargées dynamiquement depuis le vault** à chaque import, jamais figées en dur — si le texte du vault change, le module suit automatiquement. L'analyse (`patron_a_respecter`/`a_eviter`/`sources_vault`) reste écrite à la main dans `_ANALYSE`, à revalider manuellement si un scénario change en profondeur. Garde-fou : lève une erreur explicite si un scénario de `_ANALYSE` disparaît du vault.
- Config : variable d'environnement `OURRASSOL_VAULT_ROOT`, sinon déduite automatiquement (confirmé fonctionnel avec `generator/`+`variables/` au même niveau, config par défaut chez David).

**Rien dans le pipeline actuel n'importe encore `patrons_spatiaux.py`** — prêt, en attente d'être consommé par l'étape B ou C.

### Étape B (garde-fou étendu, fusion avec P22 signal 2) — ✅ CONSTRUITE le 15 juillet

**Intégrée directement dans `complete_geographie_coverage.py`** (choix de David, plutôt qu'un script diagnostic autonome séparé) : `build_user_prompt()` injecte désormais `patron_spatial_prompt_block(scenario)` dans le prompt de proposition d'affectation pays→zone, et `SYSTEM_PROMPT` demande au LLM de juger chaque affectation contre ce patron. Conformément au docstring de `patrons_spatiaux.py` ("en avertissement uniquement, jamais en blocage dur") : le LLM ne rejette jamais une affectation pour ce motif, il ajoute un champ optionnel `avertissement_patron_spatial` **seulement en cas de doute réel**, laissé à la validation manuelle de David dans `coverage_proposals_{scenario}.yaml` — même mécanisme que le champ `avertissement` déjà existant pour les slugs inconnus. Zéro coût LLM supplémentaire (même appel qui décidait déjà de l'affectation).

Testé en conditions réelles le 15 juillet (Guatemala, scénario `reference`, temporairement retiré de `zones_pays.json` puis restauré) : le prompt enrichi est bien pris en compte (2490 → 2935 tokens d'entrée), et le champ d'avertissement n'apparaît pas quand aucun anti-pattern n'est contredit — confirmé être le comportement attendu (silence quand tout va bien), pas un signe que le garde-fou ne fonctionne pas. Cas positif (avertissement réellement déclenché) non testé — jugé non bloquant, le test de silence + l'augmentation de tokens suffisent à valider l'intégration technique.

**Bonus trouvé en creusant le même fichier (15 juillet)** : `zones_pays.json` n'était écrit sur disque qu'une seule fois, à la toute fin de `main()`, après la boucle sur tous les scénarios (`--all`). Si le script plantait en cours de route, les fiches `geographie/*.md` des scénarios déjà traités restaient à jour sur disque mais `zones_pays.json` ne l'était jamais pour aucun scénario — même famille de risque que le bug split_zone ci-dessus, causée ici par un ordre d'écriture différé plutôt qu'un oubli. Corrigé : nouvelle fonction `_write_zones_pays()`, appelée immédiatement après chaque scénario traité (`process_scenario()` et `apply_proposals()`), plus une fois en fin de `main()` par sécurité (désormais redondante mais inoffensive).

### Étape C (le générateur top-down proprement dit) — ⚪ pas construite, le plus gros chantier
Nouveau script ou extension de `complete_geographie_coverage.py`, branché sur le formulaire "créer une nouvelle zone niveau 1" de P7 étape 2.

---

## P25 ✅ — CLOS le 14 juillet — Traiter les incohérences détectées par `check_origine_reelle_coherence.py`

13 incohérences trouvées au premier run complet (6 scénarios), réduites à 0 au fil de plusieurs cycles diagnostic → correction :
- Reparents via l'onglet Carte (Genève, Bruxelles, Hanse Baltique, Camargue, Nuuk×2, Mourmansk) au fur et à mesure des candidats proposés par le script
- `ouagadougou_nouvelle_ctsa` → révélé être un cas de `type_entite` manquant (voir P26), pas un mauvais rattachement
- `nuna_capital_siege` → révélé être un faux positif (Groenland typé `autre` dans `nuuk_forteresse`, généralisation de `_compte_comme_pays()`)
- `seoul_accords` → révélé être un faux positif (Corée du Sud présente mais `type_entite` manquant dans `bloc_eurasien_souverainiste`)

**Confirmé par David le 14 juillet : `check_origine_reelle_coherence.py --all` → 0 incohérence sur les 6 scénarios.**

---

## P26 ✅ — CONSTRUIT le 14 juillet — Réparer les entrées `origine_reelle` sans `type_entite`

**Découverte** : 27+ entrées `origine_reelle` sur les 6 scénarios ont un `entite` de pays réel mais aucun `type_entite` (ex. "Burkina Faso" listé nu, sans `type_entite: pays`) — probable oubli de champ à l'écriture. Masquait plusieurs cas dans P25 (faux positifs ET candidats invisibles).

**Script livré : `check_type_entite_coherence.py`** (`generator/`). Diagnostic seul par défaut, `--apply` corrige (`type_entite: pays` + `portion: null`), backup `.bak` automatique. Édition ligne-à-ligne (pas de re-dump YAML complet) pour ne toucher que les lignes concernées sur des fichiers de 3000+ lignes — testé : diff chirurgical de 8 lignes sur `breakdown.md`, rien d'autre bougé.

Bug corrigé en testant sur le vrai vault : une valeur `entite` repliée sur deux lignes (YAML standard, ex. `pacte_des_souverains`) était prise à tort pour une entrée incomplète par le premier scan — corrigé avant tout `--apply` réel.

**Confirmé par David le 14 juillet : plus aucune entrée sans `type_entite` sur les 6 scénarios.**

---

## P27 ✅ — CLOS le 15 juillet — Territoires ambigus : convention décidée, traitement final

**Script livré : `check_conventions_territoires.py`** (`generator/`). Diagnostic distinct de `check_origine_reelle_coherence.py` : au lieu de comparer une zone à sa chaîne de parenté, compare un même territoire ambigu (dépendance/collectivité) **entre les 6 scénarios**. A révélé qu'un rattachement peut être syntaxiquement valide (la zone qui le revendique existe bien dans `zones_pays.json`) tout en étant incohérent narrativement — cas trouvé : le Groenland revendiqué par `espace_eurasiatique` (bloc russo-chinois technocratique, aucune mention d'Arctique) dans `policy_reform`, alors que `europe_nord_ouest` (Danemark, Norvège, Suède...) est un bien meilleur candidat et le revendique déjà.

**Table `TERRITOIRES_AMBIGUS`** (à enrichir manuellement) : Groenland, Polynésie française, Nouvelle-Calédonie, Guyane française, Écosse, Pays de Galles.

**Convention décidée par David le 14 juillet : les territoires dépendants/autonomes suivis sont toujours traités comme des entités distinctes de leur pays souverain réel**, quand ils apparaissent dans un scénario (extension du pattern déjà observé sur la Polynésie française, distincte de la France dans les 6/6 scénarios où elle apparaît). Le script vérifie la conformité à cette règle plutôt que juste la variance.

**Bug trouvé et corrigé le 15 juillet en traitant le premier cas réel** (Écosse/`breakdown`, voir P7 étape 4 ci-dessous) : `_apply_split_zone()` (`gui/app.py`) écrivait bien dans `geographie/{scenario}.md` mais jamais dans `zones_pays.json` — même angle mort que celui déjà corrigé pour le renommage (`_rename_zone_in_zones_pays`), jamais répliqué pour le split. Corrigé avec une nouvelle fonction `_split_zone_in_zones_pays()`, appelée en dry-run (rapport d'impact) et en apply réel.

**Limite découverte au passage, pas un bug** : la carte Leaflet (`gui/static/app.js`, fond de carte `johan/world.geo.json`) ne peut pas afficher séparément un territoire infra-national de son pays souverain — un seul polygone par pays reconnu par l'ONU, aucune subdivision Écosse/Pays de Galles/Angleterre/Irlande du Nord. Les données du vault sont correctes après un split ; seul le rendu visuel de la carte ne peut pas le représenter. Option pour plus tard, pas urgente : fond de carte avec subdivisions infranationales (Natural Earth admin-1, ou GeoJSON UK dédié superposé).

**Traitement final des 11 cas identifiés le 14 juillet, décidé le 15 juillet :**
| Territoire | Scénario | Décision |
|---|---|---|
| Écosse | `breakdown` | Split fait → nouvelle zone `ecosse` |
| Écosse | `fortress_world` | **Accepté tel quel** — le Royaume-Uni entier reste politiquement uni dans ce scénario (logique de repli sur les frontières existantes) |
| Écosse | `policy_reform` | Accepté tel quel |
| Pays de Galles | `breakdown` | **Accepté tel quel** — l'Angleterre et le Pays de Galles restent unis dans `archipel_anglo_celtique` pendant que l'Écosse se détache (exception narrative propre à ce scénario) |
| Pays de Galles | `fortress_world` | Accepté tel quel (même raison que Écosse/`fortress_world`) |
| Pays de Galles | `new_sustainability` | Accepté tel quel |
| Pays de Galles | `eco_communalism` | Accepté tel quel |
| Pays de Galles | `policy_reform` | Accepté tel quel |
| Groenland | `breakdown` | Réaffecté directement vers `amérique réformée` (sans split — n'était pas mélangé avec le Danemark, juste mal placé dans `espace_eurasiatique`) |
| Groenland | `eco_communalism` | Déjà correct (`arc_septentrional`, pas mélangé) — aucune action |
| Groenland | `reference` | Accepté tel quel |

Décision de David : clore P27 avec ces 8 cas acceptés tels quels plutôt que de les séparer systématiquement — une réouverture de ce sujet serait un choix volontaire, pas un oubli.

---

## Notes de workflow à ne pas oublier

**`complete_geographie_coverage.py`** — workflow obligatoire :
1. `--review` → génère `coverage_proposals_{scenario}.yaml`
2. Valider dans VS Code (`valide: false` sur les mauvaises propositions)
3. `--apply` → écrit dans la fiche + `zones_pays.json`
4. `check_zones_coherence.py --scenario X` → confirmer la cohérence

*(Depuis le 11 juillet, plus de délai fixe entre batches — voir P13. Le rate limiting reste géré, mais de façon réactive plutôt que préventive.)*

**Bascule de zone via la carte** — workflow obligatoire :
1. Clic sur le pays (gris ou déjà coloré)
2. Choisir une zone (manuel ou proposition LLM)
3. **"🔍 Évaluer l'impact" obligatoire** — rapport sauvegardé dans `documentation/need_action/impact_bascule_{pays}_{scenario}.md`
4. Le bouton de confirmation n'apparaît qu'après le rapport
5. **Depuis le 13 juillet (P7 étape 3)** : si le rapport détecte des sous-zones potentiellement orphelines, un bouton "↗️ rattacher à {nouvelle_zone}" par sous-zone permet de les recorriger en un clic, indépendamment de la confirmation de la bascule elle-même

**Restructuration de zones (P7)** — dans l'onglet Carte :
- **Renommer** (slug + nom, depuis le 13 juillet) : bouton ✏️ sur chaque zone niveau 1 de la légende
- **Voir l'arbre des sous-zones** (niveau 2/3, pas de représentation carte pour elles) : clic sur le nom/pastille d'une zone niveau 1 dans la légende
- **Déplacer une sous-zone** (reparent, avec son sous-arbre, depuis le 13 juillet) : bouton "↗️ déplacer" sur chaque nœud non-racine de l'arbre — permet aussi de promouvoir en zone niveau 1 autonome ou de créer une nouvelle zone niveau 1 à la volée si aucun parent existant ne convient
- **Scinder une zone** (split, depuis le 14 juillet ; correctif zones_pays.json le 15 juillet) : bouton "✂️ scinder" sur tout nœud de l'arbre (racine incluse) ayant plus d'un pays dans son `origine_reelle` — extrait un ou plusieurs pays vers une nouvelle zone niveau 1 ou une zone niveau 1 existante. Les sous-zones dont la PROPRE `origine_reelle` référence aussi le(s) pays extrait(s) suivent automatiquement (détecté, pas décidé manuellement) ; les autres restent en place. Différent de déplacer : déplacer bouge une zone entière telle quelle, scinder la coupe en deux et n'en bouge qu'un morceau. Différent de "créer une nouvelle zone" via le clic carte : celui-ci ne gère qu'un seul pays à la fois, en correspondance de chaîne exacte, et ne fait jamais suivre les sous-zones — le split gère plusieurs formulations du même pays (tokenisation, comme `check_origine_reelle_coherence.py`) et le suivi automatique des sous-zones concernées. **Bug corrigé le 15 juillet** : `_apply_split_zone()` n'écrivait jamais dans `zones_pays.json` (seulement dans la fiche géographie) — la carte affichait alors l'ancienne couleur malgré un split réussi côté données. Voir P27 pour le détail.

**Rechercher une zone tous niveaux (depuis le 14 juillet)** — champ de recherche en haut de la sidebar de l'onglet Carte. La légende/liste principale n'affiche que les zones niveau 1 ; ce champ cherche aussi les niveaux 2/3 par nom ou slug (insensible aux accents/casse) et affiche le chemin complet racine→zone trouvée. Au clic sur un résultat, ouvre directement le bon arbre et centre/surligne la zone — évite de deviner/remonter la chaîne à la main quand le parent immédiat d'une zone n'est pas sa racine N1 (cas réel : `delta_rhone_fermes_verticales`, niveau 3, sous `corridor_iberique_energetique`, lui-même sous `nouveau_califat_barcelone`).

**Scan géographie complet (`scan_geographie_complet.py`, depuis le 14 juillet)** — orchestrateur en `generator/`, appelle en séquence `check_zones_coherence.py` → `check_type_entite_coherence.py` → `check_origine_reelle_coherence.py` → `check_conventions_territoires.py`, résumé consolidé à la fin. Chaque script reste utilisable seul (entrée sidebar GUI intacte) ; aucune écriture par défaut, `--apply-type-entite`/`--resolve-llm`/`--write-zones-manquantes` propagent les flags correspondants.
```bash
python3 scan_geographie_complet.py --all
```

**Clé API** — `Illegal header value b'Bearer '` → `source ~/.zshrc` avant de relancer un script en terminal (le GUI charge `.env` lui-même).

**Modèle LLM** — depuis le 11 juillet, régi par le routing par tier (`llm_client.py::TASK_TIER_DEFAULTS`) plutôt que par un seul réglage global. Pour forcer un modèle précis ponctuellement : toggle "Forcer ce modèle" dans le GUI (sticky, bandeau d'alerte visible tant qu'actif) ou `LLM_PROVIDER`/`LLM_MODEL` en variable d'environnement pour un usage CLI direct — jamais en export permanent dans `.zshrc`.

**Création d'entités/événements custom en mode multi-modes (`create_entities`, `inject_events`)** — depuis le 11 juillet, le formulaire GUI n'affiche que les champs pertinents à l'onglet Mode actif (`custom`/`auto`/`auto-suggest`), avec une note contextuelle rappelant si le mode injecte directement dans le vault ou ne fait qu'ajouter des idées à `queue.yaml` (à valider ensuite en mode `custom`).
