# Handoff — GUI Ourrassol 2098
*Session du 30 juin 2026 — état final*

---

## Lancement

```bash
lsof -ti:5000 | xargs kill -9
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py
# → http://localhost:5000 dans Chrome
# Après remplacement de fichiers JS/CSS sans relancer Flask : Cmd+Shift+R
```

---

## Fichiers modifiés cette session

### `gui/`
```bash
cp app.py            "…/gui/app.py"
cp app.js            "…/gui/static/app.js"
cp style.css         "…/gui/static/style.css"
cp scripts_config.json "…/gui/scripts_config.json"
cp zones_pays.json   "…/gui/zones_pays.json"
```

### `generator/`
```bash
cp complete_geographie_coverage.py "…/generator/"
```

### `documentation/need_action/`
```bash
cp zones_manquantes.yaml "…/documentation/need_action/"
```

---

## État zones_pays.json — breakdown

- **71 pays affectés** avec slugs valides dans breakdown.md
- **23 pays null** dont 8 remis manuellement (affectations incorrectes du run tronqué) :
  - Remis à null : Allemagne, Belgique, Pays-Bas, Hongrie, Serbie, Roumanie, Venezuela, Grèce
  - Null d'origine : Angleterre, Australie, Autriche, Bangladesh, Chili, Inde, Mexique, Nouvelle-Zélande, Pakistan, Pays de Galles, Philippines, Pologne, Polynésie française, Royaume-Uni, Écosse
- Les 5 autres scénarios n'ont pas encore été traités par `complete_geographie_coverage.py`

---

## Ce qui fonctionne en fin de session

| Feature | Notes |
|---|---|
| Formulaires guidés — 5 scripts | generate, generate_series, create_entities, inject_events, inject_signals |
| Double select Zone 2098 / Pays 2026 | create_entities + inject_events uniquement |
| Lookup pays → zone en temps réel | Relit origine_reelle à jour, puis fallback table statique |
| Dashboard — section Zones manquantes | Par scénario, boutons Revérifier + Enrichir + Intentionnel |
| Route /api/zones/recheck | Relit la fiche géo à jour, retire les entrées résolues |
| complete_geographie_coverage.py | Modes --review, --apply, batches de 12, descriptions dans prompt |
| 🧭 Couverture géo complète | Dans sidebar section Maintenance |

---

## Pourquoi complete_geographie_coverage a échoué sur breakdown

- Run lancé sans `--review` → écriture directe
- JSON tronqué (Mistral small, 46 pays en un seul appel)
- Affectations incorrectes (Allemagne → arc_sahelo_mediterraneen, etc.) faute de contexte narratif
- **Fix appliqué** : batches de 12, descriptions des zones dans le prompt, mode --review
- **Prochaine fois** : toujours lancer `--review` d'abord pour valider avant `--apply`

---

## Workflow correct pour complete_geographie_coverage

```bash
# 1. Générer les propositions (sans écrire)
python3 complete_geographie_coverage.py --scenario breakdown --review
# → crée generator/coverage_proposals_breakdown.yaml

# 2. Vérifier dans VS Code
# mettre valide: false sur les propositions incorrectes
# modifier zone_slug si besoin

# 3. Appliquer
python3 complete_geographie_coverage.py --scenario breakdown --apply
# → écrit dans breakdown.md + zones_pays.json
# → archive coverage_proposals_breakdown.applied.yaml
```

---

## Architecture routes Flask complètes

| Route | Méthode | Description |
|---|---|---|
| `/api/config` | GET/POST | Config |
| `/api/scripts` | GET | Liste des scripts |
| `/api/script/<id>` | GET | Config d'un script |
| `/api/yaml` | GET/POST | Lecture/écriture YAML brut |
| `/api/yaml/form` | POST | Sauvegarde champs individuels YAML |
| `/api/yaml/append` | POST | Appende entrée dans queue YAML |
| `/api/slugs` | GET | Slugs dynamiques |
| `/api/zones/lookup` | GET | Lookup pays 2026 → zone 2098 (relit fiche à jour) |
| `/api/zones/pays-liste` | GET | Liste 86 pays |
| `/api/zones/manquantes` | GET/POST | Zones manquantes (lecture + mise à jour statut) |
| `/api/zones/recheck` | POST | Revérifie les nulls après enrichissement |
| `/api/dashboard` | GET | Stats vault |
| `/api/review` | GET | Items en revue |
| `/api/run` | POST | Lance un script |
| `/api/stream/<run_id>` | GET | SSE streaming |
| `/api/stop/<run_id>` | POST | Stop subprocess |
| `/api/status` | GET | État run actif |

---

## Bugs récurrents

| Bug | Fix |
|---|---|
| `@app.route dashboard` mangé par patch | `python3 -c "f=open('app.py');c=f.read();f.close();c=c.replace('\ndef get_dashboard():','\n@app.route(\"/api/dashboard\",methods=[\"GET\"])\ndef get_dashboard():');open('app.py','w').write(c)"` |
| Port 5000 occupé | `lsof -ti:5000 \| xargs kill -9` |
| zones vides (type zones/zones_all) | Vérifier que `_scan_zone_slugs` reçoit `vault_root` pas `pipeline_dir` |

---

## Prochaine session — P1 : Tableau de bord géographie avec carte

### Vision
Nouvel onglet "Carte" dans le GUI :
- Select scénario en haut
- Carte mondiale interactive (Leaflet.js)
- Pays colorés par zone N1 (palette auto, une couleur par zone)
- Pays null = gris
- Légende zones N1 à droite
- Clic sur pays null → panneau latéral :
  - Meilleure zone existante proposée (via `/api/zones/lookup`)
  - Proposition de nouvelle zone N1
  - Boutons : **Absorber** | **Créer la zone** | **Ignorer**

### Fichiers nécessaires
- `gui/static/countries.geojson` — frontières pays du monde (données libres ~500kb)
- Leaflet.js via CDN
- Nouvelle route Flask `/api/carte/affectations?scenario=breakdown`
  → retourne { pays: zone_slug | null } pour tous les pays de la liste

### Dépendances à coder
1. Route `/api/carte/affectations` — lecture zones_pays.json filtré par scénario
2. Route `/api/carte/propose` — appel LLM pour proposition d'affectation d'un pays
3. Onglet Carte dans index.html + JS + CSS
4. Intégration Leaflet avec colorisation par zone

### Durée estimée : 2-3h

---

## Backlog complet (ordre de priorité)

| ID | Feature | Durée | Notes |
|---|---|---|---|
| P1 | Tableau de bord géographie + carte interactive | 2-3h | Voir ci-dessus |
| P2 | complete_geographie_coverage — 5 scénarios restants | 30min | Lancer --review puis --apply pour fortress_world, new_sustainability, eco_communalism, policy_reform, reference |
| P3 | Tests end-to-end formulaires guidés | 1h | generate, generate_series, create_entities, inject_events |
| P4 | Test streaming SSE | 30min | validate --dry-run, enrich_minimal --limit 2 --dry-run |
| P5 | Fix pérenne décorateur dashboard | 15min | Séparer routes dans modules |
| P6 | scripts_config.json vérification complète | 1h | Croiser avec code source |

