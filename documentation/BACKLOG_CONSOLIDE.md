# Backlog consolidé — Ourrassol 2098
*Mis à jour le 13 juillet 2026 — fusionne le backlog historique et les items des sessions du 11, 12 et 13 juillet*

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

## P11 ⚪ — Intégrer `check_zones_coherence.py` au GUI
**Durée : 15–20 min**

Script actuellement CLI pure, lecture seule. Ajouter une entrée dans `scripts_config.json` pour l'avoir en un clic depuis le sidebar, comme les autres scripts. Pas urgent — usage CLI actuel suffisant.

**Sous-tâche identifiée le 4 juillet** : `gui/check_session.sh` fait actuellement trois choses de nature différente dans un seul script shell :
1. Cohérence de données géo (JSON valide `pays_mapping.json`/`zones_pays.json`, pays de `zones_pays.json` absents du mapping FR→EN)
2. Vérification d'environnement/process (`certifi` installé, port 5000, ping `GET /api/carte/affectations`)
3. Checklist manuelle non automatisable (bouton LLM carte, bandeau diagnostic, hachures, rapport d'impact)

La partie 1 devrait migrer dans `check_zones_coherence.py --all` (même famille de vérification que ce qu'il fait déjà — cohérence de la couche géographique) plutôt que de vivre en double dans un script shell séparé. Les parties 2 et 3 restent dans `check_session.sh`, qui n'a pas vocation à devenir une vérification de données (pas d'accès disque au vault dans son rôle actuel, dépend de Flask up). Ne pas mettre ça dans `validate.py` : `validate.py` lit le vault sur disque sans dépendance à Flask ni au réseau, et doit le rester.

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

## P17 🟡 — Nouveau (11 juillet) — Retester la fiabilité `mistral-small` sur choix contraint, pipeline corrigé
**Durée : 30 min**

Le bug #26 (handoff) a montré que la contamination culturelle observée les 6 et 11 juillet (bugs #18/#20 historiques) était en réalité causée par un bug de résolution de zone, reproduit à l'identique sur `mistral-small` **et** `mistral-large` — pas une limite de fiabilité modèle comme diagnostiqué initialement. Reste à vérifier si un vrai problème de fiabilité subsiste sur `mistral-small` une fois cette cause de code éliminée : relancer une génération d'article sur `mistral-small` (via override manuel `LLM_PROVIDER=mistral LLM_MODEL=mistral-small-latest`) sur la configuration désormais corrigée (Bassin du Congo/`sante`) et comparer au résultat obtenu sur `mistral-large`.

---

## P18 ✅ — Vérifier `routes_dashboard.py` après le renommage "Modèle si forcé" — CLOS le 13 juillet

Cohérence confirmée sur le point d'origine (`data.llm` reflète `gui/config.json`, cohérent avec le commentaire déjà présent dans `app.js`). **Bug bonus trouvé** (#35) : `import json` manquant dans `routes_dashboard.py`, provoquant un `NameError` sur chaque appel à `/api/dashboard` dès que `_entities_list.json` existe (toujours le cas — 571 entrées) — cassait tout l'endpoint, pas juste la carte Entités. Fix appliqué et confirmé par David sur son GUI réel.

---

## P19 ⚪ — Nouveau (11 juillet) — Bug #27 (mineur, en observation)
**Pas de durée estimée — dépend de la fréquence d'occurrence**

Incohérence de plausibilité logistique détectée sur un article test : un personnage d'une zone alliée lointaine (Pacte Amazônia Viva, Amazonie) décrit comme arrivant par un moyen de transport purement local (pirogue depuis Kisangani, Congo), sans mention de la traversée intercontinentale attendue. Décision prise le 11 juillet : observer si ça se reproduit avant de renforcer `build_system_prompt()` (`prompt_builder.py`) avec une consigne dédiée à la plausibilité des trajets inter-zones. Voir `HANDOFF_CONSOLIDE.md` §3bis, point 3, pour le détail complet.

---

## P20 ⚪ — Nouveau (12 juillet) — Enrichissement frontmatter pour publication web future
**Scoping fait, pas encore codé**

**Contexte** : anticiper la publication en ligne des articles générés en enrichissant le YAML frontmatter dès la génération, plutôt que de retraiter des centaines de fichiers a posteriori.

**Champs à ajouter au frontmatter des articles** :

| Champ | Description |
|---|---|
| `slug` | Identifiant URL-friendly (évite de le dériver du titre à chaque fois, risques de collision/accents) |
| `chapo` / `excerpt` | Résumé court (2-3 lignes) pour pages de liste et meta description SEO |
| `image_prompt` | Prompt de génération d'image, produit par le LLM en même temps que l'article |
| `a_une_photo` | Booléen, **basculé manuellement** — choix éditorial, pas systématique |
| `image_principale` | Chemin vers l'image générée (rempli en post-traitement) |
| `image_alt` | Texte alternatif (accessibilité + SEO) |
| `image_credit` | Traçabilité de la source/du prompt si génération IA |
| `tags` | Mots-clés distincts de `thematique` (orientés découverte/recherche lecteur) |
| `journaliste_slug` | Lien vers la fiche auteur (déjà présent dans `journaux.yaml`) |
| `date_publication` vs `date_evenement` | À distinguer si publication différée / calendrier éditorial |
| `articles_lies` | Liens vers 2-3 articles connexes — possiblement déductible automatiquement des entités partagées plutôt que généré par le LLM |
| `zone_principale` | Déjà présent via `localisation`, mais un champ dédié simplifie le filtrage géographique côté front |

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

## P22 ⚪ — Nouveau (13 juillet) — Garde-fou de cohérence géographique via `origine_reelle`
**Scopé, pas construit**

`enrich_geographie_recursive.py::resolve_parents_and_levels()` valide déjà l'existence du `parent`, détecte les cycles, dédoublonne les slugs — mais ne compare jamais `origine_reelle` de l'enfant contre celui du parent. Le champ `origine_reelle` (déjà obligatoire, structurellement validé par `validate_zone()`) est un bien meilleur signal que des mots-clés sur le nom : une entrée `type_entite: "ville"`/`"region_administrative"` de l'enfant qui n'a aucune trace dans les entrées `pays` de la chaîne de parenté est un signal fort d'incohérence — exactement le motif des 4 anomalies trouvées le 13 juillet (P7).

**Ce qui manque pour construire** : une ville/subdivision comme "Barcelone" ou "Cracovie" ne porte pas de pointeur explicite vers son pays dans les données actuelles. Deux options à trancher :
1. Petite table statique ville→pays (rapide, gratuit, couverture limitée aux villes courantes)
2. Passe de vérification LLM dédiée en lot (couverture complète, coût API, plus lent)

Non-bloquant, à intégrer en avertissement (comme le rapport d'impact actuel) plutôt qu'en blocage dur — le taux de faux positifs d'une première heuristique mots-clés (5 sur 9 lors du test du 13 juillet) montre qu'un blocage automatique serait risqué sans un signal plus fiable que le nom/la description.

---

## P23 ⚪ — Nouveau (13 juillet) — Corriger les 3 dernières incohérences géographiques trouvées dans le vault
**Durée : ~5 min avec l'outil P7 (reparent)**

Trouvées en testant P7, restent à corriger (Cracovie déjà faite en direct pendant les tests) :
- `barcelone_hub` (Barcelone-Hub — Bureau ibérique de la CMTCA), scénario `new_sustainability`, actuellement sous `ameriques_reconfigurees` — aucune zone Europe/Ibérie n'existe encore dans ce scénario, nécessite l'option "créer une nouvelle zone niveau 1" de l'étape 2 de P7 (déjà utilisée en test avec `peninsule_iberique_autonome`, zone de test à nettoyer ou réutiliser)
- `corridor_iberique_energetique`, scénario `new_sustainability`, même parent incohérent, même zone cible probable
- `noeud_mnemos_pannonie` (Nœud Mnemos du Bassin Pannonien), scénario `breakdown`, actuellement sous `arc_eurasien_central` — pas de zone Europe centrale identifiée non plus, à trancher (nouvelle zone, ou rattachement à `geneve_bunker_institutions` comme Cracovie ?)

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

**Restructuration de zones (P7, depuis le 13 juillet)** — dans l'onglet Carte :
- **Renommer** (slug + nom) : bouton ✏️ sur chaque zone niveau 1 de la légende
- **Voir l'arbre des sous-zones** (niveau 2/3, pas de représentation carte pour elles) : clic sur le nom/pastille d'une zone niveau 1 dans la légende
- **Déplacer une sous-zone** (reparent, avec son sous-arbre) : bouton "↗️ déplacer" sur chaque nœud non-racine de l'arbre — permet aussi de promouvoir en zone niveau 1 autonome ou de créer une nouvelle zone niveau 1 à la volée si aucun parent existant ne convient

**Clé API** — `Illegal header value b'Bearer '` → `source ~/.zshrc` avant de relancer un script en terminal (le GUI charge `.env` lui-même).

**Modèle LLM** — depuis le 11 juillet, régi par le routing par tier (`llm_client.py::TASK_TIER_DEFAULTS`) plutôt que par un seul réglage global. Pour forcer un modèle précis ponctuellement : toggle "Forcer ce modèle" dans le GUI (sticky, bandeau d'alerte visible tant qu'actif) ou `LLM_PROVIDER`/`LLM_MODEL` en variable d'environnement pour un usage CLI direct — jamais en export permanent dans `.zshrc`.

**Création d'entités/événements custom en mode multi-modes (`create_entities`, `inject_events`)** — depuis le 11 juillet, le formulaire GUI n'affiche que les champs pertinents à l'onglet Mode actif (`custom`/`auto`/`auto-suggest`), avec une note contextuelle rappelant si le mode injecte directement dans le vault ou ne fait qu'ajouter des idées à `queue.yaml` (à valider ensuite en mode `custom`).
