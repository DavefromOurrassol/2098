# Backlog consolidé — Ourrassol 2098
*Mis à jour le 4 juillet 2026 — fusionne le backlog historique (P1–P11) et les items de la session du 4 juillet*

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

## P3 🟡 — Tests end-to-end formulaires guidés — en cours
**Durée : 1h — démarré le 5 juillet, tests 1 et 2/4 faits (6 juillet)**

- [x] **Generate** : sélecteur de zone testé — cassé puis corrigé en cours de route (bug #21 du handoff : `config_file` désynchronisé de `yaml_files.path` après le fix bug #16, pour `generate` et `generate_series`). Article généré avec succès, mais a révélé le bug #20 (contamination langue/culture entre zones alliées) — deux fix de prompt appliqués (`prompt_builder.py`, `generate_journaux.py`), le second pas totalement suffisant avec `mistral-small`. **Décision provisoire** : `mistral` reste le défaut confirmé pour la prod. OpenAI/Claude servent d'environnement de test/debug pendant le développement. Le choix définitif du LLM pour la génération d'articles en masse reste ouvert — à trancher plus tard avec plus de recul.
- [x] **Couverture `journaux.yaml`** : trou massif découvert (160 zones N1 sans journal sur 160, 0 orphelin) via le script `check_journaux_coherence.py` (livré le 5 juillet). Comblé intégralement via `generate_journaux.py --all --update` sous OpenAI/GPT-5.5, après avoir levé 2 bugs de compatibilité (bug #22 du handoff : `max_tokens`→`max_completion_tokens`, `temperature` non personnalisable sur GPT-5.x) et nettoyé 2 fois des placeholders de fallback (`clean_fallback_journaux.py`). Confirmé : 0 manquant, 0 orphelin sur les 6 scénarios. Coût réel : ~58k tokens, ≈$0,92.
- [x] **Generate series** : chips thématiques testées, sauvegarde d'abord "muette" (bug #23 du handoff — Flask pas redémarré après le dernier `app.py`, pas un bug de code), résolu après redémarrage. Série de 2 articles générée avec succès (`policy_reform` / `politique`+`societe` / `breve`).
- [x] **Nouvelle fonctionnalité (hors périmètre initial de P3, ajoutée le 6 juillet à la demande de David)** : rédaction de 6 journalistes par journal, répartis par thématique (les 20 thématiques du projet, plusieurs pouvant partager un même journaliste). Généré pour les 290 journaux existants via `generate_journaux.py --all --fill-journalistes` (bug #24 du handoff : troncature JSON avec lots de 5 → corrigé avec lots de 3 + `max_tokens` 8000). Coût réel : ~292k tokens, ≈$6. **Reste à vérifier (prochaine session)** : `--dry-run` confirme bien 0 restant, qualité d'une rédaction, et test d'un article régénéré (Bassin du Congo/`sante`) pour confirmer signature + bonne correspondance thématique.
- [ ] Create entities (custom) : formulaire → Ajouter à queue → vérifier `entites_custom/queue.yaml` → Lancer
- [ ] Inject events (custom) : `zone_hint` pays 2026 → lookup → vérifier injection

---

## P4 🟢 — Test streaming SSE

- `validate.py --dry-run` depuis le GUI → log SSE visible
- `enrich_minimal.py --limit 2 --dry-run` → slug_select + streaming

---

## P5 ✅ — Fix pérenne décorateur dashboard
**Fait et confirmé le 4 juillet.**

`/api/dashboard` et ses 8 fonctions `_stats_*`/`_count_review_items` extraites de `app.py` vers `routes_dashboard.py` (nouveau fichier, Blueprint Flask), importé et enregistré via `app.register_blueprint(dashboard_bp)` juste après la création de `app`. Import de `load_config` fait en différé (dans la fonction) pour éviter l'import circulaire, sans créer de module supplémentaire. Testé en réel (boot Flask + appel `/api/dashboard` → `200`) avant livraison. Aucun changement visible côté GUI — même données, même affichage ; seul le code serveur est réorganisé pour ne plus être exposé aux patches sur le reste de `app.py`.

---

## P6 🟢 — `scripts_config.json` : vérification complète
**Durée : 1h**

Croiser les options de chaque script avec le code source Python. Priorité : `generate_manual.py`, `undo_custom.py`, `extract_phantom_slugs.py`. Peut être fusionné avec P11.

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

Coût API estimé ~$37 pour la totalité. Lancer après validation complète du pipeline géographique (fait) — pas de dépendance bloquante restante.

---

## P9 ✅ — Nettoyage dossier orphelin `evenements_custom`
**Fait et confirmé le 4 juillet.**

Vérification approfondie (tailles de fichiers + grep sur les 36 scripts, cf. handoff) : le sens était inversé par rapport au texte original du backlog. Le dossier actif et lu par le code est `evenements_custom/` **à la racine du vault** (`queue.yaml` 3429 octets, `processed.yaml` 246 946 octets, `needs_review.yaml` 14 octets). L'orphelin est `generator/evenements_custom/` (`queue.yaml` et `queue.yaml.bak`, tous deux 0 octet) — supprimé (`rm -rf generator/evenements_custom`).

**Origine probable de l'orphelin, découverte en creusant (bug #16 du handoff)** : l'entrée `inject_events` de `scripts_config.json` déclarait `evenements_custom/queue.yaml`, résolu par le GUI relativement à `pipeline_dir` (= `generator/`) au lieu de `vault_root` — donc toute tentative d'ajout via le formulaire GUI "Ajouter à queue" aurait écrit dans le mauvais fichier (vide, jamais lu par `inject_custom_events.py`). Corrigé avec le reste du bug #16.

## P12 ✅ — Retraitement des entités custom en échec — clos
**Découvert et traité intégralement le 4 juillet.**

Parcours complet : 25 idées initiales (dont "Almaty Zone Friction" retirée — doublon conceptuel avec "Zones Grises Tampons") → plusieurs vagues de retraitement ayant révélé et corrigé au passage :
- bug #17 (rate limiting Mistral, fix centralisé dans `llm_client.py`)
- bug #18 (fiabilité `mistral-small` sur les `variables_potentielles` — choix contraint mal respecté ; contourné en basculant sur `claude-sonnet-4-6` pour le dernier lot)
- 9 vrais doublons identifiés et abandonnés en cours de route (Corridors Eurasiens Convoyage, Tresse Verte Corridor, Arctique Nordark, Communes Rust Belt, Communes Rust Belt Zones Libres, Corridor Arctique Nordique, Rust Belt Communes Libres, Zone Usines Forteresses Eurasie, Zones Grises Globales)
- **✅ Toutes les idées restantes créées avec succès** (`needs_review.yaml` confirmé vide en fin de session)

**`communes_rust_belt`** : finalement déjà correct dans sa fiche `.md` (description/tension/variables déjà remplies depuis le 27 juin) — `needs_review.yaml` était simplement périmé, aucune action nécessaire sur ce point précis.

**Découverte en creusant ce point** : bug #19 (handoff) — `_entities_list.json` accumulait des doublons (645 entrées / 571 slugs uniques) faute de dédoublonnage à l'ajout. Fix appliqué + fichier nettoyé fourni (`_entities_list_clean.json`) + `create_entities_and_instances.py` mis à jour.

**P12 est entièrement clos, confirmé** par `check_zones_coherence.py --all` : 6 scénarios propres (breakdown 89/36 N1, fortress_world 71/21, new_sustainability 60/15, eco_communalism 87/42, policy_reform 61/15, reference 61/16), `zones_manquantes.yaml` vide. Registre `_entities_list.json` nettoyé et remplacé, script `create_entities_and_instances.py` à jour avec le fix #19.

---

## P13 🟢 — Migrer `complete_geographie_coverage.py` vers le retry centralisé de `llm_client.py`
**Durée : 10-15 min**

Ce script utilise encore son propre délai fixe de 8s entre batches (fix du bug #8, avant l'existence du retry centralisé du bug #17). Fonctionnel mais redondant : le retirer et laisser `llm_client.py` gérer le rate limiting de façon réactive, comme pour `create_entities_and_instances.py`, permettrait de profiter automatiquement d'un futur passage en plan Scale sans y retoucher.

---

## P10 ⚪ — Rapport d'impact : étendre aux entités
**Durée : 1h, si besoin avéré**

`/api/carte/impact` couvre actuellement `instances/` et `event_instances/` mais pas `entites/` (archétypes, généralement peu liés à un pays précis). À évaluer après usage réel — probablement pas nécessaire si les entités restent génériques.

---

## P11 ⚪ — Intégrer `check_zones_coherence.py` au GUI
**Durée : 15–20 min**

Script actuellement CLI pure, lecture seule. Ajouter une entrée dans `scripts_config.json` pour l'avoir en un clic depuis le sidebar, comme les autres scripts. Pas urgent — usage CLI actuel suffisant. Peut être fusionné avec P6.

**Sous-tâche identifiée le 4 juillet** : `gui/check_session.sh` fait actuellement trois choses de nature différente dans un seul script shell :
1. Cohérence de données géo (JSON valide `pays_mapping.json`/`zones_pays.json`, pays de `zones_pays.json` absents du mapping FR→EN)
2. Vérification d'environnement/process (`certifi` installé, port 5000, ping `GET /api/carte/affectations`)
3. Checklist manuelle non automatisable (bouton LLM carte, bandeau diagnostic, hachures, rapport d'impact)

La partie 1 devrait migrer dans `check_zones_coherence.py --all` (même famille de vérification que ce qu'il fait déjà — cohérence de la couche géographique) plutôt que de vivre en double dans un script shell séparé. Les parties 2 et 3 restent dans `check_session.sh`, qui n'a pas vocation à devenir une vérification de données (pas d'accès disque au vault dans son rôle actuel, dépend de Flask up). Ne pas mettre ça dans `validate.py` : `validate.py` lit le vault sur disque sans dépendance à Flask ni au réseau, et doit le rester.

---

## Notes de workflow à ne pas oublier

**`complete_geographie_coverage.py`** — workflow obligatoire :
1. `--review` → génère `coverage_proposals_{scenario}.yaml`
2. Valider dans VS Code (`valide: false` sur les mauvaises propositions)
3. `--apply` → écrit dans la fiche + `zones_pays.json`
4. `check_zones_coherence.py --scenario X` → confirmer la cohérence

⚠️ Délai de 8s entre batches (rate limiting) depuis le 4 juillet — runs plus longs mais plus fiables, ne pas interrompre.

**Bascule de zone via la carte** — workflow obligatoire :
1. Clic sur le pays (gris ou déjà coloré)
2. Choisir une zone (manuel ou proposition LLM)
3. **"🔍 Évaluer l'impact" obligatoire** — rapport sauvegardé dans `documentation/need_action/impact_bascule_{pays}_{scenario}.md`
4. Le bouton de confirmation n'apparaît qu'après le rapport

**Clé API** — `Illegal header value b'Bearer '` → `source ~/.zshrc` avant de relancer un script en terminal (le GUI charge `.env` lui-même).

**Modèle LLM** — défaut confirmé `mistral` / `mistral-small` (P2quater). Reste moins fiable en raisonnement géographique (bug #3) : basculer ponctuellement sur `claude-sonnet-4-6` depuis le sélecteur GUI pour une session carte/coverage si des erreurs grossières réapparaissent.
