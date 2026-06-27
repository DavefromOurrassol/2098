
# RÉSUMÉ DU PROJET — OURRASSOL 2098

## Concept général

Simulateur de presse fictive générant des articles de journaux cohérents situés en 2098, basé sur **6 scénarios** × **12 variables systémiques** × **20 thématiques**. Architecture : **Obsidian** (stockage des données) → **Python** (orchestration/logique) → **API Claude** (rédaction des articles).

---

## Nomenclature canonique (à respecter strictement)

**12 variables systémiques** : `systeme_economique_redistribution`, `gouvernance_institutions`, `geopolitique_conflits`, `valeurs_culture_tempo_sociale`, `organisation_territoires`, `sante_biotechnologies`, `frontieres_du_systeme`, `technologie_information`, `climat_environnement_global`, `energie_ressources_critiques`, `demographie_mobilite_humaine`, `systemes_productifs_travail`

**6 scénarios** : `fortress_world`, `new_sustainability`, `breakdown`, `eco_communalism`, `policy_reform`, `reference`

**20 thématiques** (rubriques journalistiques) : `actualites_a_la_une`, `politique`, `economie_finance`, `environnement_climat`, `sciences_technologies`, `societe`, `culture`, `international`, `musique`, `sports`, `faits_divers`, `opinions_editoriaux`, `lifestyle_art_de_vivre`, `sante`, `education`, `histoire_patrimoine`, `medias_communication`, `religion_spiritualite`, `petites_annonces_services`, `meteo`

---

## Architecture du vault Obsidian (chemin local)

```
/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/
├── scenarios/          ✓ 6 fiches .md complètes
├── variables/          ✓ 12 fiches v3 (avec signal_to_state, 6 états/scénario chacune)
├── thematiques/        ✓ 20 fiches .md
├── influence_matrix.md ✓ 132 edges (12×11)
├── entites/            ✓ 5 entités archétypes
├── instances/          ✓ 20 instances (entité × scénario)
├── evenements/         ✓ 3 archétypes d'événements
├── event_instances/    ✓ 18 instances d'événements (3 archétypes × 6 scénarios)
└── articles/           (généré automatiquement par les scripts)
```

---

## Architecture des données — logique archétype/instance

**Principe central** : une entité (ou un événement) est un **archétype abstrait**. Chaque scénario possède sa propre **instance** de cet archétype — avec un nom potentiellement différent, un état temporel différent, un impact différent. La même entité peut être un personnage puissant dans un monde, mort/mythifié dans un autre, clandestin dans un troisième.

### Entités/Instances

- `entites/{slug}.md` — archétype : nom, catégorie, description, tension_fondamentale, variables_potentielles, scenarios_instances
- `instances/{slug}_{scenario}.md` — instance complète avec 8 blocs : identité, nature contextuelle, impact systémique (impact_local/impact_systemique_global 0-5), variables_influencees, zones (géographique/systémique), relations (alliances/oppositions), temps (annee_debut/fin, etat_temporel, age_historique, generation), narratif (description_journalistique, signes_distinctifs, tensions_narratives), + bloc `injection` (type: canonique|custom, annee_injection, impact_sur_variables, propagation.via_matrice)

**5 entités créées** (avec instances dans plusieurs scénarios) :

1. `conseil_regulation_algorithmique` (5 scénarios)
2. `nexcore` (3 scénarios)
3. `le_temoin` (6 scénarios — personnage journaliste : Vera Solano/Kofi Asante-Mensah/Le Signal/Mele Tupou/Ingrid Larsson/Raj Mehta selon le scénario)
4. `coalition_vivant` (3 scénarios)
5. `assemblee_territoires` (3 scénarios)

### Événements/Event_instances (même logique archétype/instance)

- `evenements/{slug}.md` — archétype : name, type_evenement, portee, date_approximative, intensite, description, variables_hint, scenarios_instances
- `event_instances/{slug}_{scenario}.md` — instance : nom, date, date_label, realisation (comment l'événement se produit ou non dans ce monde), description_complete, consequences, impact_sur_variables (delta_level, duree, polarite), acteurs_impliques, propagation.via_matrice, note_coherence, champ `impossible` (bool)

**3 événements créés** (× 6 scénarios = 18 instances) :

1. `election_parti_commun_americain` — 2055 (répression 2052/victoire intégrée/victoire fantôme/dissolution locale/réforme progressive/élection contestée)
2. `effondrement_reseau_mondial_communication` — 2040 (prétexte nationalisation/catalyseur communs numériques/début agonie/accélérateur localisation/déclencheur régulation/crise partiellement absorbée)
3. `arrestation_chris_van_derburgh` — 2078 (archives non certifiées/procès patrimoine acquitté/milice Detroit/procès communautaire/jurisprudence/technologies non déclarées)

---

## Pipeline Python — dossier `generator/`

Tous les scripts dans : `/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/generator/`

| Script                 | Fonction                                                                                                                                      | Statut                 |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| `loader.py`            | Lit tous les fichiers Obsidian → dicts Python (scénarios, variables, thématiques, matrice, entités, instances, event_instances)               | ✓ opérationnel         |
| `snapshot.py`          | Construit le monde 2098 cohérent (états variables, tensions, trajectoire, instances filtrées, injections custom, événements custom appliqués) | ✓ opérationnel         |
| `prompt_builder.py`    | Assemble le prompt pour Claude (6 sections : monde, variables, tensions, trajectoire+événements custom, entités canoniques, consigne)         | ✓ opérationnel         |
| `api.py`               | Appelle l'API Claude et sauvegarde l'article                                                                                                  | ⏳ attend clé API       |
| `generate.py`          | Génère 1 article — lit `config.yaml`, mode `--dry-run` disponible                                                                             | ✓ opérationnel (testé) |
| `generate_series.py`   | Génère une série d'articles — lit `config_series.yaml`, génère un index, mode `--dry-run`                                                     | ✓ opérationnel (testé) |
| `generate_entities.py` | Génère les 20 entités canoniques + leurs instances via API                                                                                    | ⏳ attend API           |
| `create_entity.py`     | Crée une entité custom interactivement (avec injection temporelle optionnelle) + génère ses instances                                         | ⏳ attend API           |
| `create_event.py`      | Crée un événement archétype interactivement + génère ses 6 instances par scénario via API                                                     | ⏳ attend API           |
| `validate.py`          | Valide la cohérence complète de la base — **7 passes**                                                                                        | ✓ opérationnel (testé) |

### Fichiers de configuration

- `config.yaml` — génération d'1 article (scenario, thematique, article.longueur="auto"|breve|analyse|etc, injections[], output)
- `config_series.yaml` — génération en série (scenario, thematiques[], articles_par_thematique, longueur, angle_specifique, injections[])

---

## validate.py — 7 passes de validation

1. **Nomenclature** — slugs dans listes canoniques, 6 scénarios + 12 variables présents
2. **Cohérence systémique** — levels/state_logic présents dans tous les states
3. **Entités/instances** — champs obligatoires, catégories valides (incl. "mouvement"), cohérence etat_temporel ↔ state_of_system du scénario, injections custom valides (annee_injection 2025-2097, delta cohérent)
4. **Thématiques** — formats valides (gère accents : "brève"/"breve", "éditorial"/"editorial"), variables référencées existent
5. **Références croisées** — wikilinks non cassés
6. **Matrice** — 132 edges, pas de doublons, weight∈[0,1], polarity∈{1,-1}
7. **Événements** — slug cohérent avec scénario, archétype référencé existe, variables/dates valides, delta vs level cohérent, acteurs_impliques existent, wikilinks

**Résultat actuel** : `✓ BASE VALIDE — 0 erreurs | 4 avertissements` Les 4 avertissements concernent 2 références à des instances non encore créées (`assemblee_territoires_policy_reform`, `nexcore_reference`) — normal, disparaîtront quand toutes les instances seront générées via l'API.

---

## Logique signal_to_state (trajectoire historique)

Chaque fiche variable contient une **section 12 "Trajectoire des signaux 2025→2098"** : pour 2 signaux faibles par variable, on définit comment ce signal évolue dans chacun des 6 scénarios, avec :

- `evolution` (description du changement)
- `date_bascule` (fenêtre temporelle, ex "2041-2058")
- `evenement_cle` (nom d'un événement historique daté concret, ex "guerre des minerais d'Afrique centrale 2051")

`snapshot.py` agrège ces événements via `build_signal_trajectory()`, les classe en majeur/structurant/local selon le nombre de variables touchées et si une variable pilote est impliquée. Ces événements datés apparaissent dans le prompt section TRAJECTOIRE pour donner à Claude des faits concrets et nommés à mentionner.

---

## Système d'injection custom (entités et événements)

**Entités custom** : bloc `injection` dans une instance avec `type: custom`, `annee_injection`, `impact_sur_variables` (delta_level, duree, polarite), `propagation.via_matrice`. `snapshot.py::apply_custom_injections()` calcule le delta pondéré par la durée d'effet réelle et l'applique au level de la variable, avec propagation optionnelle via les edges forts (≥0.75) de la matrice.

**Événements custom** : même logique via `apply_custom_events()`. Les événements apparaissent dans le prompt avec badge `[CUSTOM]` dans la section TRAJECTOIRE, et les perturbations de variables sont listées dans la section MONDE 2098.

**config.yaml / config_series.yaml** ont un champ `injections: []` pour activer des instances custom.

---

## Tests effectués (sans API — copier/coller manuel)

Plusieurs articles ont été générés en simulant l'appel API (system prompt + user prompt collés dans la conversation, réponse rédigée manuellement par Claude) :

- `breakdown × actualites_a_la_une` — "L'Effondrement du Réseau NexCore"
- `eco_communalism × religion_spiritualite` — "Le Retour des Dieux Locaux"
- `fortress_world × musique` — "AtlasFest 2098" (utilise entités canoniques : Vera Solano, NexCore Bloc Atlantique, ANBA, Chambre de Sécurité Territoriale)
- `eco_communalism × economie_finance` — "Les Monnaies Territoriales à l'Épreuve de la Coordination" (utilise : Réseau des Assemblées Bioterritoriales, Les Gardiens du Territoire, Mele Tupou)

Tous les articles respectent : pas de métalangage (scénario/variable/simulation), noms propres crédibles 2098, entités canoniques utilisées avec noms exacts, événements datés mentionnés naturellement, cohérence avec l'état systémique du monde.

`generate_series.py --dry-run` testé avec succès sur 6 thématiques pour `breakdown` (6 prompts assemblés correctement, ~9000-9300 caractères chacun).

---

## PROCHAINES ÉTAPES (dans l'ordre)

1. **Obtenir une clé API Anthropic** (`export ANTHROPIC_API_KEY="sk-ant-..."`)
2. `python3 generate_entities.py --entities-only` puis sans flag → génère les 20 entités canoniques + ~120 instances manquantes
3. `python3 create_entity.py` → pour créer des entités custom additionnelles si besoin
4. `python3 create_event.py` → pour créer d'autres événements custom si besoin
5. `python3 validate.py -v` → vérifier la base enrichie (devrait passer à 0 avertissements une fois toutes les instances générées)
6. `python3 generate_series.py` → générer la première vraie série d'articles avec l'API
7. Plus tard : `generate_all.py` (tous scénarios × toutes thématiques, automatique)

---

## Fichiers livrés disponibles (zips précédents)

- `variables_v3_fixed.zip`, `scenarios_v2.zip`, `thematiques_obsidian.zip`, `influence_matrix.md`
- `entites_instances.zip` (5 entités + 20 instances)
- `evenements_event_instances.zip` (3 archétypes + 18 instances)
- `templates/` (entity_template.md, instance_template.md)
- `generator/` — tous les scripts Python listés ci-dessus

**Tout est déjà copié dans le vault Obsidian de l'utilisateur** — ce résumé sert de référence pour la suite, pas pour re-livrer les fichiers.
