---
type: documentation
titre: Ourrassol 2098 — Manuel d'utilisation
date_maj: 2026-06-25
---

# Ourrassol 2098 — Manuel d'utilisation

Ce guide explique comment utiliser le système au quotidien : générer des articles, enrichir la géographie, gérer les localisations, injecter tes propres idées (entités, événements, signaux), retirer des éléments du lore, et résoudre les problèmes courants. Pour le détail technique du code, voir `recap_pipeline.md`.

Toutes les commandes se lancent depuis le dossier `generator/` :
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

- `scenario` : un des 6 mondes — `breakdown`, `fortress_world`, `new_sustainability`, `eco_communalism`, `policy_reform`, `reference`
- `thematique` : la rubrique de l'article (`politique`, `sports`, `culture`, `sante`...)
- `longueur` : `auto` (recommandé) ou une longueur forcée

**2. Toujours vérifier d'abord, sans payer d'appel API**

```bash
python3 generate.py --dry-run
```

Affiche le prompt complet — relis surtout la section "Ancrage de cet article" dans la géographie et la "CONSIGNE DE RÉDACTION" à la fin.

**3. Générer pour de vrai**

```bash
python3 generate.py
```

L'article est sauvegardé dans `articles/{scenario}/`.

---

## Générer une série d'articles

```yaml
scenario: reference
thematiques:
  - politique
  - sciences_technologies
  - sports
articles_par_thematique: 1
```

```bash
python3 generate_series.py --dry-run
python3 generate_series.py
python3 generate_series.py --scenario breakdown
```

---

## Évaluer un article sans payer d'appel API (workflow manuel)

```bash
python3 generate_manual.py prompt    # affiche le prompt à copier dans un chat Claude
python3 generate_manual.py status    # avancement X/N dans la série
python3 generate_manual.py save /tmp/article.txt   # sauvegarde avant le prochain prompt
```

---

## Enrichir la géographie d'un scénario

**Vérifier l'état actuel** :
```bash
python3 -c "
import re, yaml; from pathlib import Path
for sc in ['reference','eco_communalism','breakdown','fortress_world','new_sustainability','policy_reform']:
    p = Path(f'../geographie/{sc}.md')
    if not p.exists(): print(f'{sc}: ABSENT'); continue
    m = re.match(r'^---\n(.*?)\n---', p.read_text(), re.DOTALL)
    zones = yaml.safe_load(m.group(1)).get('zones',[])
    niv = {}
    for z in zones: n=z.get('niveau',1); niv[n]=niv.get(n,0)+1
    print(f'{sc}: {len(zones)} zones {dict(sorted(niv.items()))}')
"
```

**Étape 1 — créer le squelette (une seule fois par scénario)**

```bash
python3 build_geographie_monde.py --scenario fortress_world --dry-run
python3 build_geographie_monde.py --scenario fortress_world
```

**Étape 2 — ajouter les sous-zones (relançable à volonté)**

```bash
python3 enrich_geographie_recursive.py --scenario fortress_world --dry-run
python3 enrich_geographie_recursive.py --scenario fortress_world
python3 enrich_geographie_recursive.py --all
```

Additif, jamais destructeur — les zones existantes ne sont jamais réécrites.

**Après chaque enrichissement** :
```bash
python3 extract_localisation.py
python3 review_localisation.py --auto-resolve
```

---

## Gérer les localisations (`localisation`)

**Extraire les localisations sur les nouvelles fiches**

```bash
python3 extract_localisation.py              # traite les fiches sans localisation
python3 extract_localisation.py --dry-run    # simulation
python3 extract_localisation.py --scenario reference
python3 extract_localisation.py --force      # retraite les fiches déjà traitées
python3 extract_localisation.py --report-only  # génère le rapport sans extraire
```

**Consulter les ambigus en attente**

Le rapport `documentation/need_action/localisation_review.md` liste toutes les fiches avec `statut: review_manuelle`.

**Résoudre les ambigus**

```bash
python3 review_localisation.py                          # interactif fiche par fiche
python3 review_localisation.py --auto-resolve           # Claude tranche seul
python3 review_localisation.py --auto-resolve --dry-run # simulation d'abord
python3 review_localisation.py --scenario reference
```

Décisions interactives : `[V]` valider · `[C]` choisir autre zone · `[0]` vide assumé · `[S]` skip · `[Q]` quitter

---

## Injecter tes propres idées dans le monde

### Entités custom (personnages, organisations, institutions...)

**1. Décrire dans `entites_custom/queue.yaml`**

```yaml
queue:
  - nom: Le Cartographe Silencieux
    category: humain
    role: >
      Ancien officier de renseignement devenu cartographe clandestin
      des zones de non-droit, vendant ses relevés aux plus offrants.
      Basé à Tbilissi, opère dans les corridors eurasiens.
    etat: clandestin
    scenario_ref: breakdown
    scenario_hint: null
    source: idee_2026-06
```

**2. Lancer**

```bash
python3 create_entities_and_instances.py --dry-run
python3 create_entities_and_instances.py
```

Deux modes au lancement : **`custom`** (traite la queue, contrôle total) ou **`auto`** (Claude invente librement, N entités, pas de contrôle géographique).

**3. Propager dans le lore**

```bash
python3 extract_localisation.py
python3 review_localisation.py --auto-resolve
python3 validate.py
```

### Événements custom (faits datés, ruptures, crises...)

**1. Décrire dans `evenements_custom/queue.yaml`**

```yaml
queue:
  - id: mon_evenement
    description: >
      Description détaillée de l'événement, avec lieu et acteurs.
    portee: globale
    date_approximative: "2047"
    intensite: majeure
    scenarios: null
    variables_hint: [geopolitique_conflits, energie_ressources_critiques]
    variables_hint_count: 3
    acteurs_hint: null
    acteurs_hint_count: 2
    source: idee_2026-06
```

**⚠️ Important** : si la description contient ":", l'entourer de guillemets dans le YAML.

**2. Lancer**

```bash
python3 inject_custom_events.py --dry-run
python3 inject_custom_events.py
```

**3. Propager dans le lore**

```bash
python3 extract_localisation.py
python3 review_localisation.py --auto-resolve
python3 validate.py
```

**Ordre recommandé** : créer les entités d'abord, puis les événements.

### Signaux faibles custom

```yaml
queue:
  - id: mon_signal
    description: >
      Observation ou tendance émergente.
    source: actualite_2026-06
    variable_hint: sante_biotechnologies
```

```bash
python3 inject_custom_signals.py --dry-run
python3 inject_custom_signals.py
```

---

## Retirer des éléments du lore (`undo_custom.py`)

Pour annuler une injection ou nettoyer le lore.

**Via queue** — `evenements_custom/undo_queue.yaml` :

```yaml
undo:
  - type: event_instance
    slug: mon_evenement_breakdown
    generalisation: no
  - type: instance
    slug: mon_entite_reference
    generalisation: yes
```

**Via argument direct** :

```bash
python3 undo_custom.py --slug mon_evenement_breakdown --type event_instance --generalisation no
python3 undo_custom.py --slug mon_entite --type entite --generalisation yes --execute
```

**`generalisation: no`** — retire uniquement le fichier ciblé + ses dépendances directes (ligne registre, références alliances/oppositions).

**`generalisation: yes`** — remonte à l'archétype et supprime tout : archétype + toutes instances/event_instances sur tous les scénarios + toutes leurs dépendances.

**Types disponibles** : `event_instance`, `instance`, `event` (= event_instance + generalisation:yes), `entite` (= instance + generalisation:yes).

**Sécurité** :
- Dry-run par défaut — `--execute` pour écrire réellement
- Backup `.bak` automatique avant toute suppression
- `last_validated.json` resetté, queue vidée après `--execute`

**Cycle post-undo** :
```bash
python3 undo_custom.py --execute
python3 validate.py
```

---

## Valider le vault

```bash
python3 validate.py                  # validation complète (9 sections)
python3 validate.py -v               # détail de tous les avertissements dans le terminal
python3 validate.py --report         # génère validation_report.md dans le vault (Obsidian)
python3 validate.py --localisation   # scan localisation uniquement
python3 validate.py --narrative      # force le scan cohérence narrative (sinon conditionnel)
```

**Voir le détail des avertissements** :
```bash
python3 validate.py --verbose 2>&1 | grep "narrative"   # warnings narratifs uniquement
```

**9 sections de validation** :
1. Nomenclature — slugs, fichiers
2. Cohérence systémique — levels, états, trajectoires
3. Entités/instances — relations, injections
4. Thématiques — formats, variables, `echelle`
5. Localisation — champ localisation, slug zone, review_manuelle
6. Références croisées — wikilinks cassés
7. Matrice d'influence — edges, valeurs
8. Événements — archétypes, instances, cohérence temporelle, YAML cassé
9. **Cohérence narrative** — acteurs inactifs dans événements, overflow delta, cohérence dates instances

---

## Rééquilibrer la géographie du vault

1. Créer des entités ancrées (mode `custom`, lieu précis dans `role`)
2. Injecter des événements liés
3. Relancer l'enrichissement géo : `enrich_geographie_recursive.py --all`
4. Extraire les localisations : `extract_localisation.py`
5. Résoudre les ambigus : `review_localisation.py --auto-resolve`

---

## Problèmes courants

**"Une idée custom a atterri dans `needs_review.yaml`"**
→ Relire la raison du rejet, corriger l'idée, la remettre dans `queue.yaml`.

**"Une fiche event_instance a un YAML cassé (':')"**
→ Ouvrir dans Obsidian, entourer la valeur problématique de guillemets :
```yaml
name: "La Saisie du Passage : NAT contre APA"
```

**"Je veux vérifier que rien n'est cassé dans le vault"**
```bash
python3 validate.py -v
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
```

**"Un lieu apparaît deux fois dans `geographie/{scenario}.md`"**
```bash
python3 fix_lieux_residuels.py --scenario {nom} --dry-run
python3 fix_lieux_residuels.py --scenario {nom}
```

---

## Scripts ponctuels déjà exécutés (ne pas relancer)

- **`migrate_registre.py`** — migration `registre_evenements.md` vers le format hybride actuel
- **`officialize_alliances.py`** — conversion alliances/oppositions texte libre → slugs réels
- **`fix_impact_scale.py`** — correction des échelles d'impact hors plage [0-5]

---

## Récapitulatif des commandes

```bash
# Article unique
python3 generate.py --dry-run
python3 generate.py

# Série
python3 generate_series.py --dry-run
python3 generate_series.py [--scenario NOM]

# Workflow manuel
python3 generate_manual.py prompt
python3 generate_manual.py status
python3 generate_manual.py save /tmp/article.txt

# Géographie
python3 build_geographie_monde.py --scenario NOM [--dry-run] | --all
python3 enrich_geographie_recursive.py --scenario NOM [--dry-run] | --all
python3 fix_lieux_residuels.py --scenario NOM [--dry-run]

# Localisation
python3 extract_localisation.py [--dry-run] [--scenario NOM] [--slug SLUG] [--force] [--report-only]
python3 review_localisation.py [--auto-resolve] [--dry-run] [--scenario NOM]

# Injections custom (remplir le queue.yaml correspondant avant)
python3 create_entities_and_instances.py [--dry-run]
python3 inject_custom_events.py [--dry-run]
python3 inject_custom_signals.py [--dry-run]

# Retrait du lore
python3 undo_custom.py [--slug SLUG --type TYPE --generalisation yes|no] [--execute]

# Validation
python3 validate.py [-v] [--report] [--localisation] [--narrative]
```
