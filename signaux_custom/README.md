# Injecteur de signaux faibles custom — Ourrassol 2098

## Installation

```bash
pip install anthropic pyyaml --break-system-packages
export ANTHROPIC_API_KEY=sk-ant-...
```

## Emplacement des fichiers

Placer `inject_custom_signals.py` dans `Ourrassol2098/generator/`
(le script se base sur cet emplacement pour retrouver `variables/` et
`registre_evenements.md` à la racine du vault, via
`Path(__file__).resolve().parent.parent`).

Placer `queue.yaml` dans `Ourrassol2098/signaux_custom/` (le dossier est
créé automatiquement si besoin).

```
Ourrassol2098/
├── variables/...
├── registre_evenements.md
├── signaux_custom/
│   ├── queue.yaml          ← tu remplis ça
│   ├── processed.yaml       ← généré (historique des succès)
│   ├── needs_review.yaml    ← généré (échecs à reprendre en chat)
│   └── {signal_slug}.md      ← généré (1 fiche d'audit par signal injecté)
└── generator/
    └── inject_custom_signals.py
```

## Utilisation

1. Remplir `signaux_custom/queue.yaml` (voir le fichier d'exemple fourni
   — une liste d'idées en langage naturel, avec source et variable
   suggérée optionnelle).

2. Test à blanc (appelle Claude, valide, affiche le résultat, **n'écrit
   rien sur disque**) :
   ```bash
   python3 generator/inject_custom_signals.py --dry-run
   ```

3. Exécution réelle (injecte dans `variables/{slug}.md`, régénère
   `registre_evenements.md`, écrit les fiches d'audit, met à jour la
   queue) :
   ```bash
   python3 generator/inject_custom_signals.py
   ```

4. Vérifier le résultat :
   ```bash
   python3 generator/validate.py
   ```

## Ce que fait le script pour chaque idée

1. **Sélection** (appel Claude #1) : choisit 1-2 variables cibles, une
   catégorie (technological/geopolitical/social/environmental/
   cognitive_cultural), et un `signal_slug` snake_case.
2. **Développement** (appel Claude #2, par variable cible) : rédige le
   bloc YAML `signal_to_state` (6 scénarios) au format calibré, en
   s'appuyant sur le `state_logic` de la section 8 et le registre des
   événements pour éviter les collisions.
3. **Validation mécanique** (Python pur, sans API) :
   - comptage de mots `evolution`/`evenement_cle` (4-11)
   - année de `evenement_cle` ∈ `date_bascule`
   - pas de fenêtre `date_bascule` dupliquée pour cette variable/scénario
   - pas de collision exacte avec un `evenement_cle` du registre
4. **Correction** (appel Claude #3, jusqu'à 2 fois) si la validation
   échoue, avec la liste précise des problèmes à corriger.
5. **Injection** :
   - ajoute l'entrée dans la section 12 de `variables/{cible}.md`
   - ajoute une ligne dans une sous-section "**custom (signaux
     d'actualité)**" de la section 7
   - régénère `registre_evenements.md` (tri par date, mise à jour du
     total)
   - écrit `signaux_custom/{signal_slug}.md` (fiche d'audit : idée
     source, date, variable(s), trajectoire injectée)

## Si une idée échoue (`needs_review.yaml`)

Le script tente 2 corrections automatiques. Si ça échoue encore (cas
rares — idée trop ambiguë, conflit de fond avec le lore...), l'idée est
loggée avec les derniers problèmes détectés. Le plus simple est alors de
reprendre cette idée **dans un chat avec Claude** (comme pour les 12
variables du chantier initial) : donne le brief + le registre +
`needs_review.yaml` + la fiche variable concernée.

## Limites connues / pistes d'amélioration

- Le script envoie le **registre complet** à Claude pour l'anti-collision
  (~430 lignes, ~9-10k tokens) — fonctionne bien jusqu'à plusieurs
  centaines d'entrées, mais pourrait être filtré par variable si le
  registre grossit beaucoup.
- L'annotation section 7 est ajoutée dans une sous-section dédiée
  "**custom (signaux d'actualité)**", plutôt que mêlée aux catégories
  technological/geopolitical/etc. — choix volontaire pour distinguer
  visuellement la provenance, modifiable si tu préfères l'inverse.
- Pas de recherche web intégrée (le script suppose que `description`
  dans `queue.yaml` contient déjà l'info pertinente). Une étape
  `discover_signals.py` avec l'outil `web_search` de l'API pourrait
  pré-remplir la queue automatiquement — chantier séparé si tu veux
  l'ajouter plus tard.
