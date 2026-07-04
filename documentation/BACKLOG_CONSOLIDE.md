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

## 🔴 À vérifier en tout premier (10 min), avant toute nouvelle feature

- [ ] Confirmer que `generator/complete_geographie_coverage.py` contient bien le fix #9 (groupement de nouvelles zones dans un même batch) :
  ```bash
  grep -c "nouvelles_zones_ce_batch" complete_geographie_coverage.py
  ```
  Doit renvoyer `2` ou plus. Si `0`, redéployer la dernière version.
- [ ] `python3 check_zones_coherence.py --all` — doit rester propre (0 pays réel sans zone N1, parsing OK, `zones_manquantes.yaml` vide) sur les 6 scénarios.

---

## P2quinquies ✅ — ID de modèle `mistral-small` corrigé + bug de sauvegarde config résolu
**Appliqué et confirmé le 4 juillet.**

Deux correctifs liés :
1. `mistral-small` (sans suffixe, invalide) → `mistral-small-latest` dans `gui/config.json` (`llm.model_mistral`). Fix équivalent à appliquer dans `generator/llm_client.py` (`_DEFAULT_MODELS["mistral"]`) — **pas encore fait, à ne pas oublier**.
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

## P1bis 🟡 — Documenter l'onglet Carte + rapport d'impact dans le manuel principal
**Durée : 30 min**

`USER_MANUAL_carte_et_couverture_4juillet.md` (livré le 4 juillet) et `USER_MANUAL_COMPLET.md` (livré aujourd'hui, couvre tout le pipeline) sont à fusionner en une seule référence à jour : workflow carte (clic → évaluer impact → confirmer), les 5 routes `/api/carte/*`, le cas Royaume-Uni, `merge_pays_monde.py`, le workflow `complete_geographie_coverage.py`, `check_zones_coherence.py`.

---

## P2ter 🟡 — Corriger les 32 pays "sous-zone sans N1"
**Durée : 20–30 min**

Distinct des trous corrigés par le bug #10 (ceux-ci avaient déjà *une* zone, juste pas la bonne granularité). Via l'onglet Carte, bouton "🚫 Ignorer" (si volontaire) ou réaffectation manuelle vers la vraie zone N1 :

| Scénario | Pays concernés |
|---|---|
| fortress_world | — (aucun) |
| new_sustainability | Espagne, Belgique, Portugal, Vietnam, Cambodge, Nigeria, Burkina Faso, Corée du Sud, France |
| eco_communalism | Groenland, Pologne, République tchèque, Chine |
| policy_reform | Sénégal, Singapour, Groenland |
| reference | Mali, Niger, Tchad, Kirghizistan, Tadjikistan, Afghanistan, Soudan, Cambodge, Tuvalu, Kiribati, Îles Marshall, Italie, République du Congo |
| breakdown | Estonie, Lettonie, Lituanie |

*Note : le rapport d'impact `impact_bascule_belgique_new_sustainability.md` (déjà généré) montre l'exemple Belgique → `union_nordique_europe_nord` : 1 sous-zone orpheline potentielle (`tribunal_gouvernance_algorithmique_bruxelles`), 12 instances/événements liés à réexaminer après bascule.*

---

## P3 🟡 — Tests end-to-end formulaires guidés
**Durée : 1h — plus de blocage P2, à reprendre**

- Generate : scénario → zones rafraîchissent → sauvegarder → lancer → vérifier article
- Generate series : chips thématiques → sauvegarder → lancer
- Create entities (custom) : formulaire → Ajouter à queue → vérifier `entites_custom/queue.yaml` → Lancer
- Inject events (custom) : `zone_hint` pays 2026 → lookup → vérifier injection

---

## P4 🟢 — Test streaming SSE

- `validate.py --dry-run` depuis le GUI → log SSE visible
- `enrich_minimal.py --limit 2 --dry-run` → slug_select + streaming

---

## P5 🟢 — Fix pérenne décorateur dashboard
**Durée : 15 min**

`@app.route("/api/dashboard")` régulièrement mangé par les patches. Solution proposée : séparer les routes dans `routes_dashboard.py` importé par `app.py`.

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

## P9 ⚪ — Nettoyage dossier orphelin `evenements_custom`
**Durée : 10 min**

Un `evenements_custom/queue.yaml` existe à la racine du vault, en plus de celui dans `generator/` (le seul lu par le code). Vérifier s'il contient des idées non migrées, les copier dans `generator/evenements_custom/queue.yaml` si oui, puis supprimer le dossier orphelin.

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
