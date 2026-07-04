# Backlog — GUI Ourrassol 2098
*Mis à jour le 29 juin 2026*

---

## Légende
- 🔴 Bloquant / bug
- 🟡 Priorité haute
- 🟢 Priorité normale
- ⚪ Backlog long terme

---

## P1 — Section "Zones manquantes" dans le Dashboard 🟡
**Durée estimée : 30-45 min**

Afficher les nulls de `zones_manquantes.yaml` dans le Dashboard :
- Groupés par scénario
- Bouton "Enrichir" → lance `enrich_geographie_recursive --scenario x` via `/api/run`
- Bouton "Marquer intentionnel" → met à jour le statut dans le yaml
- Badge compteur dans la sidebar si nulls présents

**Fichiers concernés :** `app.py` (route `/api/zones/manquantes`), `app.js` (carte Dashboard), `style.css`

---

## P2 — Test end-to-end formulaires guidés 🟡
**Durée estimée : 1h (tests + corrections)**

Tester chaque formulaire guidé avec de vraies données :
- **Generate** : scénario → zones rafraîchissent → sauvegarder → lancer → article généré
- **Generate series** : chips thématiques → sauvegarder → lancer → série générée
- **Create entities (custom)** : formulaire → Ajouter à la queue → vérifier `entites_custom/queue.yaml` → Lancer
- **Inject events (custom)** : idem → vérifier `evenements_custom/queue.yaml`
- **zone_hint Pays 2026** : sélectionner pays → lookup → injection → vérifier que zone apparaît dans l'instance

---

## P3 — Test streaming end-to-end 🟡
**Durée estimée : 30 min**

- `validate.py --dry-run` depuis le GUI → vérifier SSE log
- `enrich_minimal.py --limit 2 --dry-run` → vérifier slug_select + streaming
- Vérifier que l'onglet Revue se peuple après un vrai run

---

## P4 — Corriger le décorateur dashboard de manière pérenne 🟡
**Durée estimée : 15 min**

Le `@app.route("/api/dashboard")` est régulièrement mangé lors des patches Python.
Solutions :
- Option A : ajouter un test automatique au démarrage Flask qui vérifie les routes enregistrées
- Option B : séparer `app.py` en modules (`routes_dashboard.py`, `routes_yaml.py`, etc.) pour éviter les collisions de patch

---

## P5 — Enrichissement zones_pays.json via lookup à la volée 🟢
**Durée estimée : 45 min**

Remplacer le fichier statique `zones_pays.json` par un lookup dynamique dans `/api/zones/lookup` :
- Lire directement `geographie/{scenario}.md` à chaque appel
- Parser `origine_reelle` en temps réel
- Appliquer la table de fallback statique pour les cas non couverts
- Avantage : toujours à jour après `enrich_geographie_recursive`, pas de régénération nécessaire

---

## P6 — scripts_config.json vérification complète 🟢
**Durée estimée : 1h**

Croiser les options de chaque script dans `scripts_config.json` avec le code source Python.
Scripts à vérifier en priorité :
- `generate_manual.py` (modes prompt/status/save non encore câblés dans le formulaire)
- `undo_custom.py` (logique --execute vs dry-run à vérifier)
- `extract_phantom_slugs.py`, `fix_alliance_suffixes.py`

---

## P7 — Restructure zones (chantier pipeline) ⚪
**Durée estimée : 2-3h**

Outil préventif pour split/merge/reparent/rename de zones géographiques avec propagation complète.
Scope à finaliser :
- `instance.localisation.zone`
- `event_instance.localisation.zone`
- `zones_proposees.yaml`
- `parent` field dans `geographie/{scenario}.md`
- Wikilinks éventuels
- `registre_evenements.md`

---

## P8 — Enrich 426 fichiers officialise_minimal ⚪
**Durée estimée : script existant (`enrich_minimal.py`), coût API estimé ~$37 pour tout**

Lancer `enrich_minimal.py --all` après validation du pipeline.
Prérequis : vault validé (0 erreurs), journaux locaux générés.

---

## P9 — Phase 7 Config — validation chemins 🟢
**Durée estimée : 30 min**

Améliorer l'onglet Config :
- Validation des chemins `vault_root` et `pipeline_dir` côté serveur
- Route `/api/test-paths` qui vérifie que les dossiers existent
- Feedback visuel immédiat (vert/rouge)

---

## P10 — Onglet Dashboard — stats ligne éditoriale ⚪
**Durée estimée : 30 min**

Ajouter dans le Dashboard la répartition des articles par ligne éditoriale (`pro_pouvoir` / `opposition`) — lit le frontmatter des articles.

---

## Bugs connus

| Bug | Impact | Fix rapide |
|---|---|---|
| `@app.route dashboard` mangé par patches | Dashboard 404 | `python3 -c "..."` voir HANDOFF |
| `_scan_zone_slugs` utilise pipeline_dir au lieu de vault_root | zones/zones_all vides | Changer une ligne dans app.py |
| AppleScript relance sans tuer le process existant | Port 5000 occupé | `lsof -ti:5000 \| xargs kill -9` |

