# Backlog — GUI Ourrassol 2098
*Mis à jour le 1er juillet 2026*

---

## À vérifier en tout premier (avant toute nouvelle feature) 🔴
**Durée estimée : 15-20min**

- [ ] `pip3 install certifi`, relancer Flask, retester le bouton "Demander une proposition (LLM)" dans l'onglet Carte
- [ ] Ouvrir l'onglet Carte, vérifier le bandeau diagnostic orange (pays non matchés sur le fond de carte) — corriger `gui/static/pays_mapping.json` si besoin
- [ ] Vérifier visuellement les couleurs/motifs de zone sur un scénario à beaucoup de zones N1 (`breakdown` probablement)
- [ ] Tester le rapport d'impact sur un vrai cas (ex. bouger un pays du scénario `breakdown` qui a des sous-zones connues, comme la Russie → `arc_eurasien_central` a `district_mourmansk_residuel` en dessous)

---

## P1bis — Documenter l'onglet Carte + rapport d'impact 🟡
**Durée estimée : 30min**

Ajouter au `user_manual_updated.md` :
- Workflow carte (clic → évaluer impact → confirmer)
- Les 5 routes `/api/carte/*`
- Le cas Royaume-Uni (4 entrées pour 1 polygone)
- `merge_pays_monde.py` et son usage

---

## P2 — complete_geographie_coverage — 5 scénarios restants 🟡
**Durée estimée : 30min**

```bash
python3 complete_geographie_coverage.py --scenario fortress_world --review
# → valider coverage_proposals_fortress_world.yaml
python3 complete_geographie_coverage.py --scenario fortress_world --apply
# répéter pour new_sustainability, eco_communalism, policy_reform, reference
```
⚠️ Toujours `--review` avant `--apply`

---

## P3 — Tests end-to-end formulaires guidés 🟡
**Durée estimée : 1h**

- Generate : scénario → zones rafraîchissent → sauvegarder → lancer → vérifier article
- Generate series : chips thématiques → sauvegarder → lancer
- Create entities (custom) : formulaire → Ajouter à queue → vérifier entites_custom/queue.yaml → Lancer
- Inject events (custom) : zone_hint pays 2026 → lookup → vérifier injection

---

## P4 — Test streaming SSE 🟢
**Durée estimée : 30min**

- `validate.py --dry-run` depuis le GUI → log SSE visible
- `enrich_minimal.py --limit 2 --dry-run` → slug_select + streaming

---

## P5 — Fix pérenne décorateur dashboard 🟢
**Durée estimée : 15min**

Le `@app.route("/api/dashboard")` est régulièrement mangé par les patches.
Solution : séparer les routes dans `routes_dashboard.py` importé par `app.py`.

---

## P6 — scripts_config.json vérification complète 🟢
**Durée estimée : 1h**

Croiser les options de chaque script avec le code source Python.
Priorité : `generate_manual.py`, `undo_custom.py`, `extract_phantom_slugs.py`.

---

## P7 — Restructure zones (pipeline) ⚪
**Durée estimée : 2-3h**

Outil split/merge/reparent/rename de zones avec propagation complète dans le vault.
*Note (1er juillet) : la carte gère déjà les bascules pays → zone N1 individuelles avec rapport d'impact. Ce chantier reste nécessaire pour les opérations sur les zones elles-mêmes (fusionner deux zones N1, renommer un slug partout, etc.) — pas couvert par l'onglet Carte.*

---

## P8 — Enrich 426 fichiers officialise_minimal ⚪
**Script existant (`enrich_minimal.py`)**

Lancer après validation du pipeline. Coût API estimé ~$37.

---

## P9 — Nettoyage dossier orphelin evenements_custom ⚪
**Durée estimée : 10min**

Un `evenements_custom/queue.yaml` existe à la racine du vault, en plus de celui dans `generator/` (le seul lu par le code). Vérifier s'il contient des idées non migrées, les copier dans `generator/evenements_custom/queue.yaml` si oui, puis supprimer le dossier orphelin.

---

## P10 — Rapport d'impact : étendre aux entités ⚪
**Durée estimée : 1h (si besoin avéré)**

Le rapport d'impact (`/api/carte/impact`) couvre actuellement `instances/` et `event_instances/` mais pas `entites/` (archétypes, généralement peu liés à un pays précis). À évaluer après usage réel — probablement pas nécessaire si les entités restent génériques.

---

## Notes importantes

**complete_geographie_coverage.py** — workflow obligatoire :
1. `--review` → génère `coverage_proposals_{scenario}.yaml`
2. Valider dans VS Code (mettre `valide: false` sur les mauvaises propositions)
3. `--apply` → écrit dans la fiche + zones_pays.json

**Bascule de zone via la carte** — workflow désormais obligatoire :
1. Clic sur le pays (gris ou déjà coloré)
2. Choisir une zone (manuel ou proposition LLM)
3. **"🔍 Évaluer l'impact" obligatoire** — rapport en lecture seule, sauvegardé dans `documentation/need_action/impact_bascule_{pays}_{scenario}.md`
4. Le bouton de confirmation n'apparaît qu'après le rapport

**Zones null restantes** — la carte (P1) remplace l'approche par lot de `complete_geographie_coverage.py` pour le traitement manuel au cas par cas. Les ~112 nouveaux pays ajoutés cette session apparaîtront tous gris jusqu'à traitement individuel ou nouveau passage `complete_geographie_coverage.py`.
