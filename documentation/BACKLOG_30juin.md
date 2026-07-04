# Backlog — GUI Ourrassol 2098
*Mis à jour le 30 juin 2026*

---

## P1 — Tableau de bord géographie + carte interactive 🟡
**Durée estimée : 2-3h**

Nouvel onglet "Carte" dans le GUI :
- Select scénario en haut
- Carte mondiale Leaflet.js (`gui/static/countries.geojson`)
- Pays colorés par zone N1 (palette auto), pays null = gris
- Légende zones N1
- Clic sur pays null → panneau : proposition zone existante + proposition nouvelle zone + boutons Absorber / Créer / Ignorer
- Connexion directe à `complete_geographie_coverage.py` via `/api/run`

Routes Flask à ajouter :
- `/api/carte/affectations?scenario=x` — retourne {pays: zone|null} pour tous les pays
- `/api/carte/propose` — appel LLM pour proposition d'affectation d'un pays

---

## P2 — complete_geographie_coverage — 5 scénarios restants 🟡
**Durée estimée : 30min**

Lancer pour les 5 scénarios non traités :
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

---

## P8 — Enrich 426 fichiers officialise_minimal ⚪
**Script existant (`enrich_minimal.py`)**

Lancer après validation du pipeline. Coût API estimé ~$37.

---

## Notes importantes

**complete_geographie_coverage.py** — workflow obligatoire :
1. `--review` → génère `coverage_proposals_{scenario}.yaml`
2. Valider dans VS Code (mettre `valide: false` sur les mauvaises propositions)
3. `--apply` → écrit dans la fiche + zones_pays.json

**Zones null dans breakdown** (23 pays) à traiter via P1 (carte interactive) :
Allemagne, Belgique, Pays-Bas, Hongrie, Serbie, Roumanie, Venezuela, Grèce,
Angleterre, Australie, Autriche, Bangladesh, Chili, Inde, Mexique, Nouvelle-Zélande,
Pakistan, Pays de Galles, Philippines, Pologne, Polynésie française, Royaume-Uni, Écosse

