# HANDOFF — 22 juin 2026
## Session du 21 juin — État exact au moment de l'arrêt

---

## Ce qui a été fait aujourd'hui

### Chantier 8 — Bible géographique récursive (CLOS)
- `enrich_geographie_recursive.py` : écrit, débogué (troncature silencieuse à 12000 tokens → porté à 24000, streaming SDK requis), testé en réel sur `reference` (36 zones) et `eco_communalism` (19 zones).
- `fix_lieux_residuels.py` : script ponctuel de nettoyage des doublons résiduels (lieux promus en zone mais encore listés sur plusieurs zones parentes). Régénère YAML + markdown pour rester cohérent.
- `dedupe_promoted_lieux` dans `enrich_geographie_recursive.py` corrigée pour chercher les résidus sur TOUTES les zones existantes, pas seulement le parent désigné par Claude.
- Validé sur `reference.md` et `eco_communalism.md` réels uploadés.

### Chantier 11 — Connexion géographie → prompt_builder.py (CLOS)
- `build_geographie_context(snapshot)` ajoutée dans `prompt_builder.py` : charge `geographie/{scenario}.md` directement depuis le disque, injecte toutes les zones (tous niveaux) en détail riche.
- Correction pré-existante : `build_entities_context` — résolution cross-scénario des alliances/oppositions (49 cas sur 530, 9,2% du vault, slug brut → nom propre via chargement paresseux par scénario).
- Validé de bout en bout : dry-run × 3 + article réel généré (`fortress_world` / `sciences_technologies`).

### Documentation (CLOS)
- `recap_pipeline.md` : référence technique complète, 9 sections.
- `manuel_utilisateur.md` : guide orienté tâches.
- `conception_localisation_filtrage_geo.md` : conception complète des chantiers 9 + filtrage géo.

---

## Ce qu'on fait demain (priorités 1 et 2 uniquement)

### Priorité 1 — Extraction `localisation` sur les 119 fiches riches

**Schéma acté** :
```yaml
localisation:
  zone: slug_zone_existante     # slug réel de geographie/{scenario}.md — validé mécaniquement
  lieu: texte_libre              # ex: "São Paulo"
  type_lieu: ville | region | infrastructure | site_strategique
```

**Périmètre** : 119 fiches riches (95 instances + 24 event_instances). PAS les 426 `officialise_minimal`.

**À vérifier en début de session** : le champ exact qui distingue les fiches riches des `officialise_minimal` dans le frontmatter — pas confirmé aujourd'hui.

**Trois issues par fiche** :
1. Lieu précis trouvé → extrait
2. Pas de lieu pertinent (entité transnationale) → champ vide, assumé
3. Ambigu → signalé pour review manuelle, jamais deviné

### Priorité 2 — Filtrage géographique dans `prompt_builder.py`

**Mécanisme** :
1. Pour chaque instance sélectionnée (`filtered_instances`), lire `localisation.zone`
2. Inclure cette zone systématiquement
3. Remonter la chaîne de `parent` pour ajouter le contexte
4. `thematique.echelle` renseigné → plafond sur la remontée
5. `thematique.echelle` null → remontée complète

**Cas limite tranché** : plafond ne tronque jamais l'instance vedette elle-même.

**Vocabulaire `échelle` à harmoniser sur les fiches thématiques** (pas encore fait) :
```
locale | urbaine | nationale | régionale | continentale | globale
```

---

## Chantiers suivants (pas demain)

- Enrichissement organique (zones manquantes, file d'attente, review) — conçu, pas codé
- `restructure` — dépend de `localisation`
- Point 13 (`undo_custom.py`) — isolé, sans dépendance
- Point 12 (enrichissement 426 fiches `officialise_minimal`) — gros chantier de fond

---

## Fichiers livrés aujourd'hui (à déposer dans le vault)

`generator/` :
- `enrich_geographie_recursive.py`
- `fix_lieux_residuels.py`
- `prompt_builder.py`

Racine vault :
- `recap_pipeline.md`
- `manuel_utilisateur.md`
- `conception_localisation_filtrage_geo.md`
