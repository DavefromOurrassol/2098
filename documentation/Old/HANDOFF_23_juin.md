# HANDOFF — 23 juin 2026
## Session du 23 juin — État exact au moment de l'arrêt

---

## Ce qui a été fait aujourd'hui

### Chantier 9 — Extraction `localisation` sur les fiches riches (CLOS)
- `extract_localisation.py` : écrit, testé, lancé en réel sur 119 fiches (95 instances riches + 24 event_instances).
- Schéma acté : `zone` (slug validé mécaniquement), `lieu` (texte libre), `type_lieu` (ville|region|infrastructure|site_strategique).
- Trois issues : `extrait` / `vide` (transnationale assumée) / `ambigu` (statut: review_manuelle, jamais deviné).
- Options : `--dry-run`, `--scenario`, `--slug`, `--force`, `--report-only`.
- Génère automatiquement `documentation/need_action/localisation_review.md` à chaque run (scan vault réel, pas seulement le run courant).
- Résultats : 89 extraits, 30 vides assumés, 30 ambigus (review_manuelle).

### Chantier 9b — Review des localisations ambiguës (CLOS)
- `review_localisation.py` : review interactive fiche par fiche (V/C/0/S/Q) + mode `--auto-resolve` (Claude tranche seul).
- Validation mécanique : slug zone vérifié contre geographie/{scenario}.md, jamais de slug fantôme écrit.
- Régénère `localisation_review.md` à la fin de chaque session.
- `--auto-resolve --dry-run` testé et validé sur les 3 ambigus restants après les injections.

### Filtrage géographique dans prompt_builder.py (CLOS)
- `build_geographie_context(snapshot, thematique=None)` — signature étendue, rétrocompatible.
- Section "Ancrage de cet article" en tête : liste les zones des instances vedettes avec lieu et type_lieu.
- Zones pertinentes en détail complet, les autres en résumé une ligne.
- Plafond `echelle` : remontée de la chaîne de parents limitée selon thematique.echelle. Cas limite : zone de l'instance toujours incluse même si hors plafond.
- `loader.py` : champ `localisation` ajouté dans le dict retourné par `load_instance`, testé end-to-end.
- Validé en dry-run sur fortress_world / sciences_technologies.

### Harmonisation `echelle` sur les 20 fiches thématiques (CLOS)
- Vocabulaire passé de 3 valeurs (`global/national/local`) à 6 (`globale/nationale/locale/continentale/régionale/urbaine`).
- Suffixe `e` ajouté partout (requis pour matcher ECHELLE_NIVEAU_MAX dans prompt_builder.py).
- Valeurs affinées : `sports` → `continentale`, `musique` → `continentale`, `opinions_editoriaux` → `nationale`, `lifestyle_art_de_vivre` → `nationale`.

### Rééquilibrage géographique — entités (CLOS)
- Analyse de l'empreinte géographique par scénario : Océanie absente partout, Amérique du Nord (8 mentions), Moyen-Orient faible.
- 10 entités créées via `create_entities_and_instances.py --custom` :
  - Brésil : Consortium Amazônia Viva, Rede Paulista de Distribuição Algorítmica, Frente Sertão Livre
  - USA : Bureau des Territoires Résiduels, Great Lakes Autonomous Compact, Mouvement des Communes du Rust Belt
  - Groenland : Kalaallit Nunaat Sovereign Fund, Arctic Passage Authority
  - Sahel : Ligue des Cités du Sahel Numérique
  - Océanie : Pacifique Sud Resilience Network
- 40 instances générées, 0 erreur.

### Rééquilibrage géographique — événements (CLOS)
- 9/10 événements injectés via `inject_custom_events.py` :
  - Brésil : urgence_ecologique_amazonie_2047, traite_souverainete_carbone_amazonie
  - USA : secession_grands_lacs_eau_douce, exode_midwest_desertification_2044, communes_rust_belt_zones_libres
  - Groenland : groenland_encheres_terres_rares, saisie_convoi_passage_nordouest
  - Océanie : tuvalu_submersion_souverainete_flottante
  - Sahel : forum_agadez_souverainete_numerique
- `emeutes_algorithme_sao_paulo` : sauté silencieusement (ni processed ni needs_review) — à réinjecter.

### Bug détecté : `inject_custom_events.py` — valeurs YAML avec ":"
- 3 fiches event_instances avec YAML cassé : `communes_rust_belt_zones_libres_breakdown.md`, `saisie_convoi_passage_nordouest_fortress_world.md`, `urgence_ecologique_amazonie_2047_breakdown.md`.
- Cause : champ `name` ou `description` contenant ":" sans guillemets.
- À corriger manuellement dans Obsidian (entourer la valeur de guillemets).
- À corriger dans le script pour les prochaines injections.

### Enrichissement géographique récursif (PARTIEL)
- `enrich_geographie_recursive.py --all` lancé après toutes les injections.
- `breakdown` : 15 nouvelles zones (niveaux 2-3) ✓
- `fortress_world` : 20 nouvelles zones (niveaux 2-3) ✓
- `new_sustainability`, `eco_communalism`, `policy_reform` : crédit épuisé en cours de run — à relancer.
- `reference` : déjà enrichi (36 zones), le run a juste été tenté sans succès.

### `validate.py` — mise à jour (CLOS)
- Nouvelle section 4b `validate_localisation` :
  - Vérifie présence du champ `localisation` sur toutes les fiches riches
  - Valide le slug `zone` contre `geographie/{scenario}.md`
  - Valide `type_lieu` contre les 4 valeurs autorisées
  - Génère `documentation/need_action/localisation_review.md`
- Section 4 (thématiques) : vérification que `echelle` est dans les 6 valeurs valides
- Section 7 (événements) : détection YAML cassé (`:` non quotés) → erreur
- Nouveau flag `--localisation` : scan review_manuelle uniquement
- Pipeline passé de 7 à 8 étapes

---

## Ce qu'on fait à la prochaine session (priorités)

### Priorité 1 — Compléter l'enrichissement géographique
```bash
python3 enrich_geographie_recursive.py --scenario new_sustainability
python3 enrich_geographie_recursive.py --scenario eco_communalism
python3 enrich_geographie_recursive.py --scenario policy_reform
```

### Priorité 2 — Réinjecter l'événement manquant
Remettre `emeutes_algorithme_sao_paulo` dans `evenements_custom/queue.yaml` et relancer `inject_custom_events.py`.

### Priorité 3 — Corriger les 3 fiches YAML cassées
Dans Obsidian, entourer de guillemets les valeurs avec ":" dans :
- `event_instances/communes_rust_belt_zones_libres_breakdown.md` (ligne 45)
- `event_instances/saisie_convoi_passage_nordouest_fortress_world.md` (ligne 1, champ name)
- `event_instances/urgence_ecologique_amazonie_2047_breakdown.md` (ligne 46)

### Priorité 4 — extract_localisation + review sur les nouvelles fiches
```bash
python3 extract_localisation.py        # nouvelles instances + events
python3 review_localisation.py --auto-resolve
```

---

## Chantiers suivants (backlog)

| Chantier | Statut | Notes |
|---|---|---|
| Bug `inject_custom_events.py` — ":" non quotés | À corriger | Voir mémoire |
| `validate.py` — cohérence narrative post-injection | À coder | Appel API optionnel, détecte contradictions entre entités |
| `validate.py` — appel `review_localisation.py` | À coder | Voir mémoire |
| Mode `auto-balanced` `create_entities_and_instances.py` | À coder | Analyse déséquilibres géo + génération ciblée |
| Mode `auto-balanced` `inject_custom_events.py` | À coder | Même principe |
| `restructure` | Débloqué | Dépendait de `localisation` — maintenant disponible |
| Point 13 `undo_custom.py` | Isolé | Sans dépendance |
| Point 12 — enrichissement 426 fiches `officialise_minimal` | Gros chantier | Débloque niveaux 2-3 géo plus denses |
| Cycle continu géo | En place | Nouvelles entités → enrich_geo → extract_loc → review_loc |

---

## Fichiers livrés aujourd'hui (à déposer dans le vault)

`generator/` :
- `extract_localisation.py` *(nouveau)*
- `review_localisation.py` *(nouveau)*
- `prompt_builder.py` *(mis à jour — filtrage géo + ancrage)*
- `loader.py` *(mis à jour — champ localisation)*
- `validate.py` *(mis à jour — 8 sections, --localisation)*

`thematiques/` :
- Les 20 fiches thématiques *(echelle harmonisée)*

`documentation/need_action/` :
- `localisation_review.md` *(généré automatiquement)*

---

## Bugs connus en attente de correction

1. **`inject_custom_events.py`** — valeurs YAML avec ":" non quotées → casse le parser. Corriger avec `yaml.dump()` pour sérialiser les champs texte.
2. **3 fiches event_instances** — YAML cassé à corriger manuellement dans Obsidian (voir Priorité 3 ci-dessus).
