# Backlog consolidé — Ourrassol 2098
*Mis à jour le 11 juillet 2026 — fusionne le backlog historique (P1–P13) et les items de la session du 11 juillet*

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

## P4 🟢 — Test streaming SSE

- `validate.py --dry-run` depuis le GUI → log SSE visible
- `enrich_minimal.py --limit 2 --dry-run` → slug_select + streaming

---

## P6 ✅ — `scripts_config.json` : vérification complète — CLOS le 11 juillet

Croisement systématique des `flag` déclarés côté GUI avec l'`argparse` réel de chaque script, sur les 19 entrées de `scripts_config.json`. Résultats : 2 flags fantômes trouvés et supprimés (`--scenario` sur `create_entities` et `inject_events`), `zone_hint` confirmé fonctionnel malgré son absence de la doc `QUEUE_TEMPLATE` (voir P16), tous les `config_fields` (formulaires `queue.yaml`) vérifiés lus correctement, `restructure_zones.py` confirmé absent du disque (attendu, P7). Détail complet : `HANDOFF_CONSOLIDE.md` §3bis, point 6.

---

## P7 ⚪ — Restructure zones (pipeline)
**Durée : 2–3h — pas encore codé**

Outil split/merge/reparent/rename de zones N1 avec propagation complète dans le vault (`instance.localisation.zone`, `event_instance.localisation.zone`, `zones_proposees.yaml`, `parent` dans `geographie/{scenario}.md`, wikilinks éventuels, `registre_evenements.md`).
*Note : l'onglet Carte gère déjà les bascules pays → zone N1 individuelles avec rapport d'impact ; ce chantier reste nécessaire pour les opérations sur les zones elles-mêmes (fusionner deux zones N1, renommer un slug partout, etc.) — pas couvert par la Carte.*
Une entrée `restructure_zones` existe déjà dans `scripts_config.json` (sidebar GUI, section maintenance) mais échouera tant que le script n'est pas écrit.
Questions ouvertes avant de coder : y a-t-il des wikilinks vers des slugs de zones dans le vault ? `registre_evenements.md` référence-t-il des zones ?

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

## P10 ⚪ — Rapport d'impact : étendre aux entités
**Durée : 1h, si besoin avéré**

`/api/carte/impact` couvre actuellement `instances/` et `event_instances/` mais pas `entites/` (archétypes, généralement peu liés à un pays précis). À évaluer après usage réel — probablement pas nécessaire si les entités restent génériques.

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

## P16 🟢 — Nouveau (11 juillet) — Documenter `zone_hint` dans `QUEUE_TEMPLATE`
**Durée : 10 min**

`zone_hint` (`entites_custom/queue.yaml` et `evenements_custom/queue.yaml`) est confirmé fonctionnel (ancrage géographique explicite injecté dans le prompt de génération) mais absent du commentaire `QUEUE_TEMPLATE` en tête des deux fichiers — repéré pendant la vérification P6.

---

## P17 🟡 — Nouveau (11 juillet) — Retester la fiabilité `mistral-small` sur choix contraint, pipeline corrigé
**Durée : 30 min**

Le bug #26 (handoff) a montré que la contamination culturelle observée les 6 et 11 juillet (bugs #18/#20 historiques) était en réalité causée par un bug de résolution de zone, reproduit à l'identique sur `mistral-small` **et** `mistral-large` — pas une limite de fiabilité modèle comme diagnostiqué initialement. Reste à vérifier si un vrai problème de fiabilité subsiste sur `mistral-small` une fois cette cause de code éliminée : relancer une génération d'article sur `mistral-small` (via override manuel `LLM_PROVIDER=mistral LLM_MODEL=mistral-small-latest`) sur la configuration désormais corrigée (Bassin du Congo/`sante`) et comparer au résultat obtenu sur `mistral-large`.

---

## P18 🟢 — Nouveau (11 juillet) — Vérifier `routes_dashboard.py` après le renommage "Modèle si forcé"
**Durée : 10 min**

La carte dashboard "LLM actif" a été renommée "Modèle si forcé" côté `app.js` (bug #28 du handoff, cohérence avec le nouveau routing par tier). `routes_dashboard.py` n'a pas été fourni pendant la session du 11 juillet — à vérifier que le champ `data.llm` qu'il expose reste cohérent avec ce nouveau libellé (il devrait, puisqu'il reflète toujours `gui/config.json`, mais non vérifié).

---

## P19 ⚪ — Nouveau (11 juillet) — Bug #27 (mineur, en observation)
**Pas de durée estimée — dépend de la fréquence d'occurrence**

Incohérence de plausibilité logistique détectée sur un article test : un personnage d'une zone alliée lointaine (Pacte Amazônia Viva, Amazonie) décrit comme arrivant par un moyen de transport purement local (pirogue depuis Kisangani, Congo), sans mention de la traversée intercontinentale attendue. Décision prise le 11 juillet : observer si ça se reproduit avant de renforcer `build_system_prompt()` (`prompt_builder.py`) avec une consigne dédiée à la plausibilité des trajets inter-zones. Voir `HANDOFF_CONSOLIDE.md` §3bis, point 3, pour le détail complet.

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

**Clé API** — `Illegal header value b'Bearer '` → `source ~/.zshrc` avant de relancer un script en terminal (le GUI charge `.env` lui-même).

**Modèle LLM** — depuis le 11 juillet, régi par le routing par tier (`llm_client.py::TASK_TIER_DEFAULTS`) plutôt que par un seul réglage global. Pour forcer un modèle précis ponctuellement : toggle "Forcer ce modèle" dans le GUI (sticky, bandeau d'alerte visible tant qu'actif) ou `LLM_PROVIDER`/`LLM_MODEL` en variable d'environnement pour un usage CLI direct — jamais en export permanent dans `.zshrc`.

**Création d'entités/événements custom en mode multi-modes (`create_entities`, `inject_events`)** — depuis le 11 juillet, le formulaire GUI n'affiche que les champs pertinents à l'onglet Mode actif (`custom`/`auto`/`auto-suggest`), avec une note contextuelle rappelant si le mode injecte directement dans le vault ou ne fait qu'ajouter des idées à `queue.yaml` (à valider ensuite en mode `custom`).
