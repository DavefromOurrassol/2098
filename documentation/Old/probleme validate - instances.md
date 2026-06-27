## Résumé du problème — à transmettre au prochain chat

### Contexte

Projet Ourrassol 2098 — simulateur de presse fictive. Le vault Obsidian contient notamment un dossier `instances/` où chaque entité possède une fiche par scénario (`{slug}_{scenario}.md`). Ces fiches sont générées via `generator/generate_entities.py` qui appelle l'API Claude.

### Ce qui s'est passé

`generate_entities.py` a été lancé pour la première fois (l'API était maintenant disponible). Il a correctement créé les instances manquantes des 5 entités d'origine, et en a aussi généré de **nouvelles entités** (25 au total, 92 instances au total). La base reste valide (0 erreur), mais `validate.py` remonte **1068 avertissements** répartis en 4 types :

### Les 4 types d'avertissements

**Type 1 — Valeurs numériques hors plage** (~100 avertissements) Les champs `impact_local` et `impact_systemique_global` doivent être dans **[0-5]** selon `validate.py`, mais Claude a généré des valeurs comme 6, 7, 8, 9, 72, 85, 88, 91... Cause : le prompt dans `generate_entities.py` ne contraint pas explicitement la plage.

Correction : script Python qui parcourt tous les fichiers `instances/*.md`, lit le frontmatter YAML, et ramène toute valeur > 5 à 5 (ou la normalise sur [0-5]).

**Type 2 — Catégorie invalide** (2 avertissements) `prisme_global.md` et `voix_du_dehors.md` ont `categorie: média` qui n'est pas dans la liste des catégories valides du validateur.

Correction : remplacer `média` par `réseau` (ou autre catégorie valide) dans ces 2 fichiers.

**Type 3 — Références alliances/oppositions non trouvées** (~500 avertissements) Les champs `alliances` et `oppositions` des instances contiennent des descriptions textuelles libres (ex: "Réseaux de semenciers clandestins"), mais `validate.py` les interprète comme des slugs d'instances devant exister dans `instances/`. Cause : `generate_entities.py` génère du texte narratif libre, pas des slugs.

Correction à discuter : soit modifier le prompt pour forcer des slugs d'instances existantes, soit (plus simple) corriger `validate.py` pour qu'il ne valide ces champs que si la valeur ressemble à un slug (`snake_case` sans espaces).

**Type 4 — Wikilinks cassés** (~470 avertissements, miroir du type 3) Les descriptions libres dans `alliances`/`oppositions` sont entourées de `[[...]]` par Claude, que `validate.py` traite comme des wikilinks Obsidian vers des fichiers existants. Même cause et même correction que le type 3.

### Ce qui fonctionne déjà

- 0 erreur, base valide
- La génération d'articles n'est pas bloquée par ces avertissements
- `loader.py`, `snapshot.py`, `prompt_builder.py` n'utilisent pas les champs `alliances`/`oppositions` pour construire les prompts d'articles

### Priorité de correction

1. **Type 1** (valeurs hors plage) — script de normalisation, ~15 min
2. **Type 2** (catégorie invalide) — 2 lignes à modifier manuellement
3. **Types 3 & 4** (alliances/oppositions) — décision de conception à prendre : corriger `validate.py` ou corriger `generate_entities.py` (+ régénérer les instances concernées)

---

## Fichiers à fournir au nouveau chat

1. **`generator/validate.py`** — pour comprendre exactement ce qui est vérifié aux passes INSTANCES et CROSS_REFERENCES
2. **`generator/generate_entities.py`** — pour voir le prompt envoyé à Claude (et le corriger si on choisit cette voie)
3. **`validation_report.md`** — le rapport complet avec les 1068 avertissements (celui que tu viens de joindre)
4. **2-3 exemples de fiches `instances/`** qui posent problème, par exemple :
    - `instances/amara_diallo_nkosi_breakdown.md` (valeurs hors plage + alliances libres)
    - `instances/prisme_global_reference.md` (catégorie invalide + alliances libres)
    - `instances/conseil_regulation_algorithmique_policy_reform.md` (les 2 seuls avertissements "historiques" de l'ancienne version)
5. **`generator/loader.py`** (version corrigée avec le bon `VAULT_PATH`) — pour que le chat puisse tester sans casser le pipeline