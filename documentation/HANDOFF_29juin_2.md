# Handoff — GUI Ourrassol 2098
*Session du 29 juin 2026 — partie 2*

---

## Lancement

```bash
lsof -ti:5000 | xargs kill -9
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py
# → http://localhost:5000 dans Chrome
# Après remplacement de fichiers : Cmd+Shift+R pour vider le cache
```

---

## Fichiers modifiés cette session

### À copier dans `gui/`
```bash
cp app.py    "…/gui/app.py"
cp app.js    "…/gui/static/app.js"
cp style.css "…/gui/static/style.css"
cp scripts_config.json "…/gui/scripts_config.json"
cp zones_pays.json "…/gui/zones_pays.json"
```

### À copier dans `generator/`
```bash
cp create_entities_and_instances.py "…/generator/"
cp inject_custom_events.py          "…/generator/"
```

### À copier dans `documentation/need_action/`
```bash
cp zones_manquantes.yaml "…/documentation/need_action/"
```

---

## État des fichiers GUI

```
gui/
  app.py                  ← modifié (routes zones/lookup, zones/pays-liste, yaml/form, yaml/append)
  config.json             ← inchangé
  scripts_config.json     ← modifié (config_fields complets pour 5 scripts)
  zones_pays.json         ← NOUVEAU (table correspondance 86 pays × 6 scénarios)
  templates/index.html    ← inchangé
  static/style.css        ← modifié (yaml form panel, double select zones)
  static/app.js           ← modifié (formulaires guidés, double select zones)
  .env                    ← inchangé
```

---

## Phases livrées cette session

| Feature | Statut | Notes |
|---|---|---|
| Formulaires guidés YAML — generate | ✅ | 7 champs, select zones hiérarchique simple |
| Formulaires guidés YAML — generate_series | ✅ | chips thématiques, doublon --scenario supprimé |
| Formulaires guidés queue — create_entities | ✅ | 8 champs dont zone_hint double select |
| Formulaires guidés queue — inject_events | ✅ | 9 champs dont zone_hint double select |
| Formulaires guidés queue — inject_signals | ✅ | 5 champs |
| Select zones hiérarchique N1/N2/N3 | ✅ | Optgroups par N1 |
| Double select Zone 2098 / Pays 2026 | ✅ | Uniquement zone_hint (create_entities, inject_events) |
| Route /api/zones/lookup | ✅ | Lookup pays→zone via zones_pays.json |
| Route /api/zones/pays-liste | ✅ | Liste 86 pays depuis zones_pays.json |
| zones_pays.json | ✅ | 86 pays × 6 scénarios, construit depuis origine_reelle + fallback |
| zones_manquantes.yaml | ✅ | 276 entrées statut: blanc_a_evaluer |
| zone_hint dans create_entities | ✅ | Injecté dans build_instance_prompt |
| zone_hint dans inject_events | ✅ | Injecté dans step2_develop_instance |
| route /api/yaml/form | ✅ | Sauvegarde champs individuels YAML |
| route /api/yaml/append | ✅ | Appende entrée dans queue YAML |

---

## Bugs récurrents à surveiller

| Bug | Symptôme | Fix |
|---|---|---|
| Décorateur `@app.route` dashboard mangé par patch | 404 /api/dashboard | `python3 -c "content=open('app.py').read(); open('app.py','w').write(content.replace('\ndef get_dashboard():', '\n@app.route(\"/api/dashboard\", methods=[\"GET\"])\ndef get_dashboard():'))"` |
| Port 5000 occupé | "Address already in use" | `lsof -ti:5000 \| xargs kill -9` |
| zones_hier retourne [] | Select zones vide | Vérifier que `_scan_zone_slugs_hier` reçoit `vault_root` pas `pipeline_dir` |

---

## Architecture — routes Flask complètes

| Route | Méthode | Description |
|---|---|---|
| `/api/config` | GET/POST | Config (POST préserve available_*) |
| `/api/scripts` | GET | Liste des scripts |
| `/api/script/<id>` | GET | Config d'un script |
| `/api/yaml` | GET/POST | Lecture/écriture YAML brut |
| `/api/yaml/form` | POST | Sauvegarde champs individuels YAML |
| `/api/yaml/append` | POST | Appende entrée dans queue YAML |
| `/api/slugs` | GET | Slugs dynamiques (instances/entities/zones/zones_hier) |
| `/api/zones/lookup` | GET | Lookup pays 2026 → zone 2098 |
| `/api/zones/pays-liste` | GET | Liste 86 pays depuis zones_pays.json |
| `/api/dashboard` | GET | Stats complètes vault |
| `/api/review` | GET | Items en attente de revue |
| `/api/run` | POST | Lance un script |
| `/api/stream/<run_id>` | GET | SSE streaming stdout |
| `/api/stop/<run_id>` | POST | Stop subprocess |
| `/api/status` | GET | État run actif |

---

## Logique double select zones (app.js)

- Activé uniquement si `field.key === 'zone_hint'` ET `field.slug_type === 'zones_hier'`
- `generate` → `zone_slug` → simple select hiérarchique (pas de double select)
- `create_entities` / `inject_events` → `zone_hint` → double select
- Onglet "Zone 2098" : select hiérarchique N1/N2/N3
- Onglet "Pays 2026" : liste 86 pays → lookup → résultat vert (trouvé) / orange (null)
- Valeur finale transmise = toujours un slug zone 2098 (ou vide si null)
- Null loggé automatiquement dans `documentation/need_action/zones_manquantes.yaml`

---

## zones_pays.json — structure

```json
{
  "pays_liste": ["France", "Allemagne", ...],
  "breakdown":        { "France": "arc_sahelo_mediterraneen", "Allemagne": null, ... },
  "fortress_world":   { "France": "bloc_atlantique", ... },
  "new_sustainability": { ... },
  "eco_communalism":  { ... },
  "policy_reform":    { ... },
  "reference":        { ... }
}
```

Couverture actuelle : 35-50 pays couverts / 86 par scénario.
Null = blanc géographique → à évaluer dans `zones_manquantes.yaml`.

---

## zones_manquantes.yaml — workflow

Chaque entrée a un champ `statut` à affecter manuellement :
- `blanc_a_evaluer` → valeur par défaut
- `blanc_intentionnel` → territoire effondré, mer, espace disputé — laisser null
- `a_enrichir` → lancer `enrich_geographie_recursive.py --scenario x`

Nouvelles entrées ajoutées automatiquement lors des lookups sans résultat.

---

## Prochaine session — backlog priorisé

### P1 — Section "Zones manquantes" dans le Dashboard (30-45 min)
Afficher les nulls de `zones_manquantes.yaml` groupés par scénario avec :
- Bouton "Enrichir" → lance `enrich_geographie_recursive --scenario x`
- Bouton "Marquer intentionnel" → met à jour le statut dans le yaml
- Après enrichissement : relancer `generate_zones_pays.py` pour mettre à jour `zones_pays.json`

### P2 — Régénération zones_pays.json après enrichissement géographie
Script ou bouton GUI qui relit les fiches géographie mises à jour et régénère `zones_pays.json`.
Option B (recommandée) : lookup à la volée dans `/api/zones/lookup` — lit directement les fiches, pas besoin de régénérer.

### P3 — Test end-to-end formulaires guidés
- Generate : sélectionner scénario → zones se rafraîchissent → sauvegarder → lancer
- Generate series : chips thématiques → sauvegarder → lancer
- Create entities (mode custom) : remplir → "Ajouter à la queue" → vérifier `entites_custom/queue.yaml`
- Inject events (mode custom) : idem → vérifier `evenements_custom/queue.yaml`
- Tester zone_hint Pays 2026 → lookup → injection

### P4 — Test streaming end-to-end
`validate.py --dry-run` et `enrich_minimal.py --limit 2 --dry-run` depuis le GUI.

### P5 — Corriger décorateur dashboard de manière pérenne
Le décorateur `@app.route("/api/dashboard")` est régulièrement mangé par les patches.
Solution : intégrer une vérification automatique dans le script de patch.

### P6 — scripts_config.json vérification complète
Croiser toutes les options de chaque script avec le code source pour détecter les divergences.

---

## Note architecture importante

`create_entities`, `inject_events`, `inject_signals` lancent automatiquement après injection :
1. `extract_localisation.py`
2. `review_localisation.py --auto-resolve`
3. `validate.py`

Le `zone_hint` est une contrainte souple pour Claude — `extract_localisation` extrait ensuite la zone réelle du contenu généré.

