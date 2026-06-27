---
type: documentation
titre: Ourrassol 2098 — Manuel d'utilisation
date_maj: 2026-06-25
---

# Ourrassol 2098 — Manuel d'utilisation

Ce guide explique comment utiliser le système au quotidien : générer des articles, enrichir la géographie, gérer les localisations, injecter tes propres idées (entités, événements, signaux), retirer des éléments du lore, et résoudre les problèmes courants.

Toutes les commandes se lancent depuis `generator/` :
```bash
cd generator
```

---

## Générer un seul article

**1. Configurer `config.yaml`**
```yaml
scenario: reference
thematique: sciences_technologies
article:
  longueur: auto
```

**2. Vérifier sans appel API**
```bash
python3 generate.py --dry-run
```

**3. Générer**
```bash
python3 generate.py
```

---

## Générer une série d'articles

```bash
python3 generate_series.py --dry-run
python3 generate_series.py
python3 generate_series.py --scenario breakdown
```

---

## Workflow manuel (sans appel API)

```bash
python3 generate_manual.py prompt       # affiche le prompt à copier dans un chat Claude
python3 generate_manual.py status       # avancement X/N
python3 generate_manual.py save /tmp/article.txt
```

---

## Enrichir la géographie d'un scénario

```bash
# Étape 1 — squelette niveau 1 (une seule fois par scénario)
python3 build_geographie_monde.py --scenario fortress_world --dry-run
python3 build_geographie_monde.py --scenario fortress_world

# Étape 2 — sous-zones (additif, relançable à volonté)
python3 enrich_geographie_recursive.py --scenario fortress_world --dry-run
python3 enrich_geographie_recursive.py --scenario fortress_world
python3 enrich_geographie_recursive.py --all
```

---

## Gérer les localisations

```bash
python3 extract_localisation.py              # fiches sans localisation
python3 extract_localisation.py --dry-run
python3 extract_localisation.py --scenario reference
python3 extract_localisation.py --slug nexcore_reference
python3 extract_localisation.py --force      # retraite les déjà faites
python3 extract_localisation.py --report-only

python3 review_localisation.py               # interactif fiche par fiche
python3 review_localisation.py --auto-resolve
python3 review_localisation.py --auto-resolve --dry-run
python3 review_localisation.py --scenario reference
```

Décisions interactives : `[V]` valider · `[C]` choisir autre zone · `[0]` vide assumé · `[S]` skip · `[Q]` quitter

---

## Injecter des entités dans le lore

```bash
python3 create_entities_and_instances.py --dry-run
python3 create_entities_and_instances.py
```

**Trois modes au lancement :**

### Mode `custom` — contrôle total
Remplis `entites_custom/queue.yaml` :
```yaml
queue:
  - nom: Le Cartographe Silencieux
    category: humain
    role: >
      Ancien officier de renseignement devenu cartographe clandestin
      des zones de non-droit. Basé à Tbilissi, opère dans les corridors eurasiens.
    etat: clandestin
    scenario_ref: breakdown
    scenario_hint: null     # null = les 6 scénarios
    source: idee_2026-06
```
Puis lance le script → mode `custom`.

### Mode `auto` — génération libre
Donne un nombre N + catégorie optionnelle. Claude invente les entités et les injecte directement. Pas de contrôle géographique.

### Mode `auto-suggest` — suggestions géo-équilibrées *(recommandé)*
Analyse la couverture géographique actuelle du vault et les zones sans instance, génère N idées ciblées → écrit dans `entites_custom/queue.yaml` sans injecter.

```
Nombre d'idées à générer ? [défaut: 3]
Scénario de référence ciblé ? (Entrée pour laisser Claude choisir)
```

Après inspection de `queue.yaml`, relancer en mode `custom` pour injecter.

**Cycle post-injection automatique** : après une injection réussie en mode `custom` ou `auto`, le script enchaîne automatiquement :
```
extract_localisation.py → review_localisation.py --auto-resolve → validate.py
```

---

## Injecter des événements dans le lore

```bash
python3 inject_custom_events.py --dry-run
python3 inject_custom_events.py
```

**Deux modes au lancement :**

### Mode `custom` — contrôle total
Remplis `evenements_custom/queue.yaml` :
```yaml
queue:
  - id: mon_evenement
    description: >
      Description détaillée, avec lieu et acteurs potentiels.
    portee: globale
    date_approximative: "2047"
    intensite: majeure
    scenarios: null              # null = les 6 scénarios
    variables_hint: [gouvernance_institutions, geopolitique_conflits]
    variables_hint_count: 3
    acteurs_hint: null
    acteurs_hint_count: 2
    source: idee_2026-06
```
⚠️ Si la description contient ":", entourer de guillemets.

### Mode `auto` — suggestions géo-équilibrées *(recommandé)*
Analyse la couverture du vault (zones absentes, types d'événements peu représentés, variables peu couvertes), génère N idées → ajout dans `evenements_custom/queue.yaml` sans injection.

```
Nombre d'idées à générer ? [défaut: 3]
Scénario ciblé ? (Entrée pour laisser Claude choisir)
```

Après inspection de `queue.yaml`, relancer en mode `custom` pour injecter.

**Cycle post-injection automatique** : idem entités — enchaîne automatiquement après injection réussie.

**Ordre recommandé** : créer les entités d'abord, puis les événements.

---

## Injecter des signaux faibles

```bash
python3 inject_custom_signals.py --dry-run
python3 inject_custom_signals.py
```

Queue : `signaux_custom/queue.yaml`.

---

## Retirer des éléments du lore (`undo_custom.py`)

```bash
python3 undo_custom.py                          # dry-run depuis undo_queue.yaml
python3 undo_custom.py --execute                # supprime réellement
python3 undo_custom.py --slug SLUG --type TYPE --generalisation yes|no [--execute]
```

**Queue** : `evenements_custom/undo_queue.yaml`
```yaml
undo:
  - type: event_instance   # | instance | event | entite
    slug: mon_slug
    generalisation: no     # | yes
```

**`generalisation: no`** — fichier ciblé + dépendances directes (registre, alliances/oppositions).

**`generalisation: yes`** — archétype + toutes instances/event_instances sur tous les scénarios + toutes dépendances.

**Types** : `event_instance`, `instance`, `event` (= event_instance + yes), `entite` (= instance + yes).

**Garanties** : dry-run par défaut, backup `.bak`, `last_validated.json` resetté, `_entities_list.json` nettoyé, queue vidée après `--execute`.

**Vérifier la suppression complète** :
```bash
grep -r "chaine_du_slug" ../instances/ ../entites/ ../event_instances/ ../evenements/
```

**Cycle post-undo** :
```bash
python3 undo_custom.py --execute
python3 validate.py
```

---

## Valider le vault

```bash
python3 validate.py                  # 9 sections
python3 validate.py -v               # détail avertissements terminal
python3 validate.py --report         # génère validation_report.md (Obsidian)
python3 validate.py --localisation   # scan localisation uniquement
python3 validate.py --narrative      # force scan cohérence narrative
python3 validate.py --verbose 2>&1 | grep "narrative"   # warnings narratifs uniquement
```

**9 sections :**
1. Nomenclature
2. Cohérence systémique
3. Entités/instances
4. Thématiques
5. Localisation → génère `localisation_review.md`
6. Références croisées
7. Matrice d'influence
8. Événements (archétypes, instances, YAML cassé)
9. Cohérence narrative (acteurs inactifs, overflow delta, cohérence dates)

---

## Rééquilibrer la géographie du vault

1. `create_entities_and_instances.py` mode `auto-suggest` — cibler les zones absentes
2. `inject_custom_events.py` mode `auto` — cibler les zones sans événements
3. Relancer l'enrichissement : `enrich_geographie_recursive.py --all`

---

## Problèmes courants

**"Une idée custom a atterri dans `needs_review.yaml`"**
→ Relire la raison du rejet, corriger l'idée, la remettre dans `queue.yaml`.

**"Une fiche event_instance a un YAML cassé (':')"**
→ Ouvrir dans Obsidian, entourer la valeur de guillemets :
```yaml
name: "La Saisie du Passage : NAT contre APA"
```

**"Je veux voir les problèmes de cohérence narrative"**
```bash
python3 validate.py --narrative -v
# ou consulter documentation/need_action/narrative_issues.yaml
```

**"Je veux annuler une injection récente"**
```bash
python3 undo_custom.py --slug mon_slug --type event_instance --generalisation no
# dry-run par défaut — ajouter --execute pour confirmer
python3 validate.py
```

**"Un lieu apparaît deux fois dans `geographie/{scenario}.md`"**
```bash
python3 fix_lieux_residuels.py --scenario {nom} --dry-run
python3 fix_lieux_residuels.py --scenario {nom}
```

---

## Scripts ponctuels déjà exécutés (ne pas relancer)

- **`migrate_registre.py`** — migration registre vers format hybride
- **`officialize_alliances.py`** — alliances/oppositions texte libre → slugs réels
- **`fix_impact_scale.py`** — correction échelles d'impact hors plage [0-5]

---

## Récapitulatif des commandes

```bash
# Article
python3 generate.py [--dry-run]
python3 generate_series.py [--dry-run] [--scenario NOM]
python3 generate_manual.py prompt|status|save

# Géographie
python3 build_geographie_monde.py --scenario NOM [--dry-run] | --all
python3 enrich_geographie_recursive.py --scenario NOM [--dry-run] | --all
python3 fix_lieux_residuels.py --scenario NOM [--dry-run]

# Localisation
python3 extract_localisation.py [--dry-run] [--scenario NOM] [--slug SLUG] [--force] [--report-only]
python3 review_localisation.py [--auto-resolve] [--dry-run] [--scenario NOM]

# Injections custom (cycle post-injection automatique inclus)
python3 create_entities_and_instances.py [--dry-run]   # custom | auto | auto-suggest
python3 inject_custom_events.py [--dry-run]            # custom | auto
python3 inject_custom_signals.py [--dry-run]

# Retrait du lore
python3 undo_custom.py [--slug SLUG --type TYPE --generalisation yes|no] [--execute]

# Validation
python3 validate.py [-v] [--report] [--localisation] [--narrative]
```
