# Handoff — GUI Ourrassol 2098
*Session du 29 juin 2026 — état final*

---

## Lancement

```bash
lsof -ti:5000 | xargs kill -9
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py
# → http://localhost:5000 dans Chrome
# Après remplacement de fichiers sans relancer Flask : Cmd+Shift+R
```

---

## Fichiers à jour sur disque (session du jour)

### `gui/`
| Fichier | État |
|---|---|
| `app.py` | Modifié — nouvelles routes yaml/form, yaml/append, zones/lookup, zones/pays-liste |
| `scripts_config.json` | Modifié — config_fields complets pour 5 scripts |
| `zones_pays.json` | **Nouveau** — table 86 pays × 6 scénarios |
| `static/app.js` | Modifié — formulaires guidés, double select zones |
| `static/style.css` | Modifié — yaml form panel, double select zones |

### `generator/`
| Fichier | État |
|---|---|
| `create_entities_and_instances.py` | Modifié — zone_hint dans build_instance_prompt |
| `inject_custom_events.py` | Modifié — zone_hint dans step2_develop_instance |

### `documentation/need_action/`
| Fichier | État |
|---|---|
| `zones_manquantes.yaml` | **Nouveau** — 276 entrées statut: blanc_a_evaluer |

---

## Ce qui fonctionne en fin de session

| Feature | Notes |
|---|---|
| Formulaires guidés — generate | Select zones N1/N2/N3, thématiques, longueurs officielles |
| Formulaires guidés — generate_series | Chips thématiques, doublon --scenario supprimé |
| Formulaires guidés — create_entities | 8 champs dont zone_hint double select |
| Formulaires guidés — inject_events | 9 champs dont zone_hint double select |
| Formulaires guidés — inject_signals | 5 champs |
| Double select Zone 2098 / Pays 2026 | Uniquement zone_hint (create_entities, inject_events) |
| Lookup pays 2026 → zone 2098 | Résultat vert/orange, log auto dans zones_manquantes.yaml |
| zones_pays.json | 86 pays × 6 scénarios depuis origine_reelle + fallback |
| Route /api/yaml/form | Sauvegarde champs individuels, préserve commentaires |
| Route /api/yaml/append | Appende entrée dans queue YAML, reset formulaire après succès |
| Dashboard | Fonctionnel (décorateur restauré manuellement en cours de session) |

---

## Bugs connus non résolus

| Bug | Symptôme | Fix |
|---|---|---|
| `_scan_zone_slugs` (type zones/zones_all) utilise `pipeline_dir` | Select zones vide sur les anciens types | `sed -i '' 's/slugs = _scan_zone_slugs(pipeline_dir/slugs = _scan_zone_slugs(vault_root/' app.py` |
| `@app.route dashboard` mangé par patches | 404 /api/dashboard au prochain patch app.py | `python3 -c "f=open('app.py');c=f.read();f.close();c=c.replace('\ndef get_dashboard():','\n@app.route(\"/api/dashboard\",methods=[\"GET\"])\ndef get_dashboard():');open('app.py','w').write(c)"` |
| AppleScript ne tue pas le process existant | "Address already in use" | `lsof -ti:5000 \| xargs kill -9` avant relance |

---

## Architecture routes Flask complètes

| Route | Méthode | Description |
|---|---|---|
| `/api/config` | GET/POST | Config (POST préserve available_*) |
| `/api/scripts` | GET | Liste des scripts |
| `/api/script/<id>` | GET | Config d'un script |
| `/api/yaml` | GET/POST | Lecture/écriture YAML brut |
| `/api/yaml/form` | POST | Sauvegarde champs individuels YAML (préserve commentaires) |
| `/api/yaml/append` | POST | Appende entrée dans queue YAML |
| `/api/slugs` | GET | Slugs dynamiques (instances/entities/zones/zones_hier) |
| `/api/zones/lookup` | GET | Lookup pays 2026 → zone 2098 via zones_pays.json |
| `/api/zones/pays-liste` | GET | Liste 86 pays depuis zones_pays.json |
| `/api/dashboard` | GET | Stats complètes vault |
| `/api/review` | GET | Items en attente de revue |
| `/api/run` | POST | Lance un script |
| `/api/stream/<run_id>` | GET | SSE streaming stdout |
| `/api/stop/<run_id>` | POST | Stop subprocess |
| `/api/status` | GET | État run actif |

---

## zones_pays.json — structure et couverture

```json
{
  "pays_liste": ["France", "Allemagne", ...],
  "breakdown":         { "France": "arc_sahelo_mediterraneen", "Allemagne": null, ... },
  "fortress_world":    { "France": "bloc_atlantique", ... },
  "new_sustainability": { ... },
  "eco_communalism":   { ... },
  "policy_reform":     { ... },
  "reference":         { ... }
}
```

Couverture : 35–50 pays couverts / 86 par scénario.
`null` = blanc géographique → loggé dans `zones_manquantes.yaml` à chaque lookup infructueux.

**Mise à jour** : après `enrich_geographie_recursive`, la route `/api/zones/lookup` relit les fiches en temps réel — pas besoin de régénérer `zones_pays.json` pour les nouveaux `origine_reelle`.

---

## zones_manquantes.yaml — workflow

Chaque entrée a un champ `statut` :
- `blanc_a_evaluer` → valeur par défaut
- `blanc_intentionnel` → territoire effondré, mer, espace disputé — laisser null
- `a_enrichir` → lancer `enrich_geographie_recursive.py --scenario x`

Nouvelles entrées ajoutées automatiquement lors des lookups sans résultat.

---

## Logique double select zones

- Activé uniquement si `field.key === 'zone_hint'` ET `field.slug_type === 'zones_hier'`
- `generate` → `zone_slug` → simple select hiérarchique (pas de double select)
- `create_entities` / `inject_events` → `zone_hint` → double select
- Onglet "Zone 2098" : select hiérarchique N1/N2/N3 avec optgroups
- Onglet "Pays 2026" : liste 86 pays → lookup → vert (trouvé) / orange (null)
- Valeur finale = toujours un slug zone 2098 (ou vide si null)

---

## Prochaine session — priorités

### P1 — Section "Zones manquantes" dans le Dashboard (30-45 min)
Afficher les nulls de `zones_manquantes.yaml` groupés par scénario :
- Bouton "Enrichir" → lance `enrich_geographie_recursive --scenario x`
- Bouton "Marquer intentionnel" → met à jour le statut
- Après enrichissement → `zones_pays.json` mis à jour automatiquement

### P2 — Tests end-to-end formulaires guidés (1h)
- Generate → sauvegarder config.yaml → lancer → vérifier article généré
- Generate series → chips → sauvegarder → lancer
- Create entities (custom) → "Ajouter à la queue" → vérifier queue.yaml → Lancer
- Inject events (custom) → zone_hint pays 2026 → lookup → injection → vérifier localisation

### P3 — Test streaming SSE (30 min)
- `validate.py --dry-run` depuis le GUI
- `enrich_minimal.py --limit 2 --dry-run`

### P4 — Fix pérenne décorateur dashboard (15 min)
Séparer les routes dashboard dans un module séparé pour éviter les collisions de patch.

