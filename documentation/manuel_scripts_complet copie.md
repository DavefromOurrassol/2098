---
type: documentation
titre: Manuel des scripts — Ourrassol 2098
date_maj: 2026-06-28
---

# Manuel des scripts — Ourrassol 2098

Mis à jour après la session du 28 juin 2026 (migration LLM Claude/Mistral, journaux locaux par zone, lignes éditoriales pro_pouvoir/opposition).

---

## Variables d'environnement globales

```bash
export LLM_PROVIDER=mistral        # mistral (défaut) | claude
export LLM_MODEL=mistral-large-latest  # override modèle (optionnel)
export ANTHROPIC_API_KEY='sk-ant-...'
export MISTRAL_API_KEY='...'
```

Tous ces exports sont à placer dans `~/.zshrc` pour persistance entre sessions.

---

## llm_client.py *(nouveau)*

Module central d'abstraction LLM. Importé par tous les scripts qui font appel à l'API.

```bash
python3 llm_client.py                          # test Mistral (défaut)
LLM_PROVIDER=claude python3 llm_client.py     # test Claude
```

**Aucun argument CLI.** Configuration via variables d'environnement uniquement.

---

## 1. Génération d'articles

### generate.py

```bash
python3 generate.py [--dry-run]
LLM_PROVIDER=claude python3 generate.py
```

Lit `config.yaml`. Tire une date fictive 2098 aléatoirement si absente.

**config.yaml :**
```yaml
scenario: breakdown
ligne_editoriale: pro_pouvoir   # pro_pouvoir | opposition | absent = pro_pouvoir
zone_slug: ""                   # optionnel — force une édition locale
thematique: actualites_a_la_une
article:
  titre_suggere: ""
  angle_specifique: ""
  longueur: auto                # breve | analyse | reportage | chronique | editorial | auto
output:
  nom_fichier: auto
```

**Nom de fichier généré :**
`YYYYMMDD_HHMMSS_{scenario}_{thematique}_article_{datefictive}.md`

---

### generate_series.py

```bash
python3 generate_series.py [--dry-run] [--validate-first] [--scenario NOM]
LLM_PROVIDER=mistral python3 generate_series.py
```

Lit `config_series.yaml`. Tire `ligne_editoriale` aléatoirement à chaque article si non défini.

**config_series.yaml :**
```yaml
scenario: breakdown
ligne_editoriale:               # vide/absent = aléatoire | pro_pouvoir | opposition
thematiques:
  - actualites_a_la_une
  - politique
articles_par_thematique: 1
longueur: auto
angle_specifique: ""
injections: []
```

---

### generate_manual.py

```bash
python3 generate_manual.py prompt    # affiche system+user prompt à copier dans le chat
python3 generate_manual.py status    # avancement de la série
python3 generate_manual.py save /tmp/article.txt  # sauvegarde dans le vault
```

Lit `config_series.yaml`. Gère `state/manual_progress.json`.
Tire `ligne_editoriale` aléatoirement si non défini dans config.

---

## 2. Journaux locaux *(nouveau)*

### generate_journaux.py

Génère `generator/journaux.yaml` — un journal local par zone N1 par scénario×ligne.

```bash
python3 generate_journaux.py --scenario NOM
python3 generate_journaux.py --all
python3 generate_journaux.py --all --update        # ajoute seulement les zones manquantes
python3 generate_journaux.py --scenario breakdown --ligne opposition
python3 generate_journaux.py --scenario breakdown --dry-run

LLM_PROVIDER=mistral python3 generate_journaux.py --all
```

**Options :**
- `--scenario NOM | --all` : scénario(s) à traiter (obligatoire)
- `--ligne pro_pouvoir|opposition|all` : filtre la ligne éditoriale (défaut: all)
- `--update` : n'ajoute que les zones absentes de journaux.yaml
- `--dry-run` : affiche sans écrire ni appeler l'API

**Structure `journaux.yaml` :**
```yaml
breakdown:
  opposition:
    _reseau:
      nom: "Réseau La Dépêche des Territoires"
      charte: "..."
    zones:
      afrique_centrale_australe:
        nom: "La Voix du Bassin"
        ton: "..."
        langue_style: "français, registre oral de terrain"
```

**Profils des 12 réseaux éditoriaux (hardcodés dans `prompt_builder.py`) :**

| Scénario | pro_pouvoir | opposition |
|---|---|---|
| breakdown | L'Ordre du Territoire | La Dépêche des Territoires |
| fortress_world | Le Bloc Informations | The Porous Border |
| new_sustainability | Nexus Global Review | Les Irréductibles |
| eco_communalism | La Gazette des Communs | Voix des Marges |
| policy_reform | Global Governance Report | La Souveraine |
| reference | Le Monde en Tension | Le Dessous des Cartes |

---

## 3. Géographie du monde

```bash
python3 build_geographie_monde.py --scenario NOM [--dry-run]
python3 enrich_geographie_recursive.py --scenario NOM | --all [--dry-run]
python3 fix_lieux_residuels.py --scenario NOM [--dry-run]
```

Tous les 6 scénarios enrichis N1+N2+N3 au 25 juin 2026.

---

## 4. Localisation des entités

```bash
python3 extract_localisation.py [--dry-run] [--scenario NOM] [--slug SLUG] [--force] [--report-only]
python3 review_localisation.py [--auto-resolve] [--dry-run] [--scenario NOM]
```

---

## 5. Injections custom — entités

```bash
python3 create_entities_and_instances.py [--dry-run]
```

Modes interactifs : `custom` | `auto` | `auto-suggest`

Cycle post-injection automatique (si ≥ 1 instance créée) :
```
extract_localisation.py → review_localisation.py --auto-resolve → validate.py
```

---

## 6. Injections custom — événements

```bash
python3 inject_custom_events.py [--dry-run]
```

Modes interactifs : `custom` | `auto`

---

## 7. Injections custom — signaux faibles

```bash
python3 inject_custom_signals.py [--dry-run]
```

---

## 8. Enrichissement fiches `officialise_minimal`

```bash
python3 enrich_minimal.py --scenario NOM [--dry-run] [--limit N] [--slug SLUG]
python3 enrich_minimal.py --all [--auto-cycle]
```

---

## 8b. Slugs fantômes

```bash
python3 extract_phantom_slugs.py [--source enrich|validate|all] [--report PATH] [--dry-run]
python3 fix_alliance_suffixes.py [--dry-run] [--verbose] [--scenario NOM]
python3 requeue_needs_review.py
```

---

## 9. Validation du vault

```bash
python3 validate.py [-v/--verbose] [--report/-r] [--localisation] [--narrative/-n]
python3 validate.py --verbose 2>&1 | grep "narrative"
```

---

## 10. Retrait du lore

```bash
python3 undo_custom.py [--execute]
python3 undo_custom.py --slug SLUG --type TYPE --generalisation yes|no [--execute]
```

---

## 11. Cycle continu complet

```bash
# Après injection d'entités ou événements :
create_entities_and_instances.py   (ou inject_custom_events.py)
→ extract_localisation.py
→ review_localisation.py --auto-resolve
→ validate.py
→ generate_journaux.py --all --update   # si nouvelles zones
→ generate_series.py

# Enrichissement fiches :
enrich_minimal.py --scenario X [--auto-cycle]
→ [inspecter enrich_minimal_report.md]
→ extract_phantom_slugs.py
→ create_entities_and_instances.py (custom)
→ generate_journaux.py --all --update
```

---

## 12. Scripts one-shot déjà exécutés (ne pas relancer)

`migrate_registre.py`, `officialize_alliances.py`, `fix_impact_scale.py`

---

## 13. Garanties de sécurité communes

- `--dry-run` : simule sans écrire (certains scripts appellent quand même l'API pour valider)
- Backup `.bak` automatique avant toute écriture
- Validation mécanique avant acceptation des données API
- Zones N1 jamais réécrites par `enrich_geographie_recursive.py`

---

## 14. Backlog (au 28 juin 2026)

| # | Chantier | Statut |
|---|---|---|
| P7 | Chantier `restructure` zones géo | 🟡 Périmètre à finaliser |
| — | `temperature` configurable dans config.yaml | 🟢 À faire |
| — | `translate_article.py` post-génération | 🟢 À faire (deuxième temps) |
| — | GUI Flask + Safari | 🟢 Spec existante (`ourrassol_gui_spec.json`) |
| — | Trigger auto `generate_journaux.py` post-injection | 🟢 À faire |
| — | Test qualité Mistral vs Claude sur `enrich_minimal` | 🔵 Optionnel |
| P4 | validate.py appel review_localisation auto | ❌ Won't do |
