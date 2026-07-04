# Handoff — GUI Ourrassol 2098
*Session du 28 juin 2026*

---

## État du projet

Le GUI Flask est **fonctionnel et déployé** dans le vault.

```
/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui/
  app.py                  ← serveur Flask (backend complet)
  config.json             ← configuration vault + LLM
  scripts_config.json     ← définition des 18 scripts
  templates/index.html    ← layout HTML
  static/style.css        ← light theme
  static/app.js           ← logique frontend
  logs/                   ← logs des runs
```

**Lancement :**
```bash
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py
# → http://localhost:5000 dans Chrome
```

---

## Chemins configurés (config.json)

```json
{
  "vault_root":     "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098",
  "pipeline_dir":   "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/generator",
  "default_scenario": "reference"
}
```

---

## Phases livrées

| Phase | Statut | Contenu |
|---|---|---|
| 1 — Squelette Flask | ✅ | app.py, index.html, style.css, app.js |
| 2 — Sélecteur LLM | ✅ | Provider + modèle, badge coût, injection env subprocess |
| 3 — Formulaires dynamiques | ✅ | Tous types : checkbox, select, ligne_select, number, text, slug_select, mode_select |
| 4 — Exécution + streaming | ✅ | SSE stdout, bouton Stop, sauvegarde logs, coloration lignes |
| 5 — Dashboard stats réelles | ✅ | 8 cartes + tableau thématiques |
| 6 — Onglet Revue | ✅ | 3 sources parsées, groupées par type |
| YAML viewer/editor | ✅ | Lecture + édition inline avec backup .bak |
| slug_select | ✅ | Scan vault réel (instances, entités, zones) |

---

## Phases restantes

### Phase 7 — Onglet Config (améliorations)
- Actuellement : formulaire basique lecture/écriture config.json
- À améliorer : validation des chemins côté serveur (vérifier que vault_root et pipeline_dir existent réellement), feedback visuel immédiat, bouton "Tester" qui ping les dossiers via `/api/test-paths`

### Phase 8 — scripts_config.json complet
- 18 scripts intégrés avec toutes les options
- À faire : vérifier les options réelles de chaque script contre le code source
- Scripts à valider en priorité : `generate.py`, `generate_series.py`, `generate_manual.py` (config_file fields pas encore câblés dans le frontend)

### À tester en priorité
1. Lancer `validate.py --dry-run` depuis le GUI → vérifier le streaming log
2. Lancer `enrich_minimal.py --limit 2 --dry-run` → vérifier slug_select + streaming
3. Vérifier que l'onglet Revue se peuple après un vrai run

---

## Bugs connus / points d'attention

| Problème | Détail | Priorité |
|---|---|---|
| `generate.py` config_file | Le champ `config_fields` est dans scripts_config.json mais le rendu inline n'est pas encore implémenté dans app.js | Moyenne |
| Noms Mistral | Corrigés en `mistral-small/medium/large` (sans `-latest`) | ✅ Résolu |
| Dashboard erreur initiale | Était dû à `statCard` non définie — corrigé | ✅ Résolu |
| Zones géo = 0 | Parser corrigé pour le format liste YAML `- slug: / niveau: 1` | ✅ Résolu |
| Journaux locaux = 0 | Parser corrigé pour le format imbriqué `scenario > ligne > réseau` | ✅ Résolu |

---

## Architecture backend (app.py)

### Routes disponibles

| Route | Méthode | Description |
|---|---|---|
| `/` | GET | Interface principale |
| `/api/config` | GET/POST | Lecture/écriture config.json |
| `/api/scripts` | GET | Liste tous les scripts |
| `/api/script/<id>` | GET | Config d'un script |
| `/api/yaml` | GET | Lecture fichier YAML (relatif à pipeline_dir) |
| `/api/yaml` | POST | Sauvegarde YAML avec backup .bak |
| `/api/slugs` | GET | Slugs dynamiques (instances/entities/zones/zones_all) |
| `/api/dashboard` | GET | Stats complètes du vault |
| `/api/review` | GET | Items en attente de revue |
| `/api/run` | POST | Lance un script subprocess |
| `/api/stream/<run_id>` | GET | SSE streaming stdout |
| `/api/stop/<run_id>` | POST | Termine le subprocess |
| `/api/status` | GET | État du run actif |

### Variables LLM injectées dans tous les subprocesses
```python
env["LLM_PROVIDER"] = config["llm"]["provider"]
env["LLM_MODEL"]    = config["llm"]["model_mistral"]  # ou model_claude
```

---

## Fichiers parsés par la Revue

| Fichier | Chemin dans pipeline_dir | Parser |
|---|---|---|
| needs_review_enrich.yaml | `instances_custom/needs_review_enrich.yaml` | `_parse_needs_review_enrich()` |
| needs_review.yaml | `evenements_custom/needs_review.yaml` | `_parse_needs_review_events()` |
| localisation_review.md | `documentation/need_action/localisation_review.md` | `_parse_localisation_review()` |

---

## Design

- Light theme : fond `#eeecea`, accent bleu `#3b6fd4`, texte noir
- Police UI : system font (`-apple-system`) + `JetBrains Mono` pour le log et les slugs
- Item actif nav : fond bleu clair + bordure gauche bleue + icône carré rempli
- Log : coloration ok(vert) / warn(orange) / error(rouge) / llm(bleu) / done(bleu accent)

---

## Prochaine session — suggestions d'ordre

1. **Tester un vrai run** (validate --dry-run) pour valider le streaming end-to-end
2. **Phase 7** — validation chemins config + feedback
3. **Phase 8** — compléter scripts_config.json avec les vraies options vérifiées
4. **config_file fields** — câbler le rendu inline pour generate.py / generate_series.py
