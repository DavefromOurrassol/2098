# RÉSUMÉ DU PROJET — OURRASSOL 2098 (mise à jour)

## Concept général

Simulateur de presse fictive générant des articles de journaux cohérents
situés en 2098, basé sur **6 scénarios** × **12 variables systémiques** ×
**20 thématiques**. Architecture : **Obsidian** (stockage des données) →
**Python** (orchestration/logique) → **API Claude** (rédaction des
articles), avec un **mode "sans API"** permettant de rédiger les articles
manuellement dans le chat.

---

## Nomenclature canonique (à respecter strictement)

**12 variables systémiques** : `systeme_economique_redistribution`,
`gouvernance_institutions`, `geopolitique_conflits`,
`valeurs_culture_tempo_sociale`, `organisation_territoires`,
`sante_biotechnologies`, `frontieres_du_systeme`, `technologie_information`,
`climat_environnement_global`, `energie_ressources_critiques`,
`demographie_mobilite_humaine`, `systemes_productifs_travail`

**5 variables pilotes** (parmi les 12, par scénario — déterminent le pool
"majeurs" de la trajectoire) — pour `breakdown` :
`geopolitique_conflits`, `energie_ressources_critiques`,
`organisation_territoires`, `climat_environnement_global`,
`systemes_productifs_travail`

**6 scénarios** : `fortress_world`, `new_sustainability`, `breakdown`,
`eco_communalism`, `policy_reform`, `reference`

**20 thématiques** (rubriques journalistiques) : `actualites_a_la_une`,
`politique`, `economie_finance`, `environnement_climat`,
`sciences_technologies`, `societe`, `culture`, `international`, `musique`,
`sports`, `faits_divers`, `opinions_editoriaux`, `lifestyle_art_de_vivre`,
`sante`, `education`, `histoire_patrimoine`, `medias_communication`,
`religion_spiritualite`, `petites_annonces_services`, `meteo`

---

## Architecture du vault Obsidian

```
Ourrassol2098/
├── scenarios/              ✓ 6 fiches .md (9 sections numérotées chacune)
├── variables/              ✓ 12 fiches .md (12 sections numérotées chacune,
│                              dont section 7 "Signaux faibles" et section 12
│                              "Trajectoire signal_to_state" — voir plus bas)
├── thematiques/            ✓ 20 fiches .md
├── influence_matrix.md     ✓ 132 edges (12×11), source des "tensions"
├── entites/                ✓ 5 entités archétypes
├── instances/              ✓ 20 instances (entité × scénario)
├── evenements/             ✓ 3 archétypes d'événements custom
├── event_instances/        ✓ 18 instances d'événements (3 × 6 scénarios)
├── articles/                  généré (par scripts ou manuellement)
├── registre_evenements.md  ✓ NOUVEAU — registre de tous les evenement_cle
│                              (signal_to_state), par scénario, pour éviter
│                              les collisions lors de l'enrichissement
├── brief_section7_vers_12.md ✓ NOUVEAU — brief pour le chantier d'enrichissement
│                              des variables (voir section dédiée plus bas)
└── generator/
    ├── loader.py            ✓ lit tous les fichiers Obsidian → dicts Python
    ├── snapshot.py           ✓ construit le monde 2098 cohérent (états,
    │                            tensions, trajectoire, signal_to_state,
    │                            injections custom)
    ├── prompt_builder.py     ✓ assemble le prompt (6 sections + rotation
    │                            à mémoire — voir plus bas)
    ├── api.py                ✓ appelle l'API Claude et sauvegarde l'article
    ├── generate.py           ✓ génère 1 article (config.yaml), --dry-run dispo
    ├── generate_series.py    ✓ génère une série (config_series.yaml),
    │                            --dry-run dispo
    ├── generate_manual.py    ✓ NOUVEAU — pipeline SANS API (voir plus bas)
    ├── generate_entities.py  ⏳ attend API
    ├── create_entity.py      ⏳ attend API
    ├── create_event.py       ⏳ attend API
    ├── validate.py           ✓ 7 passes de validation — 0 erreur, 4 avertissements
    ├── config.yaml
    ├── config_series.yaml
    └── state/                 généré automatiquement
        ├── trajectory_usage.json   ✓ mémoire de rotation des jalons (par scénario)
        └── manual_progress.json    ✓ avancement de la série en mode manuel
```

---

## Architecture des données — logique archétype/instance (inchangé)

Une entité (ou un événement) est un **archétype abstrait**. Chaque scénario
possède sa propre **instance** de cet archétype — nom, état temporel,
impact potentiellement différents.

- `entites/{slug}.md` + `instances/{slug}_{scenario}.md` (8 blocs + bloc
  `injection` canonique|custom)
- `evenements/{slug}.md` + `event_instances/{slug}_{scenario}.md`

**5 entités** : `conseil_regulation_algorithmique`, `nexcore` (Les
Fragments NexCore), `le_temoin` (Le Signal / Vera Solano / etc.),
`coalition_vivant`, `assemblee_territoires`

**3 événements custom canoniques** (monde `breakdown`) :
1. L'Attentat des Neuf Nœuds — Le Jour Sans Signal (2040)
2. Victoire Fantôme du Parti Commun (2055)
3. L'Arrestation de Van Derburgh par la Milice de Detroit-Sud (2078)

---

## Structure d'une fiche VARIABLE (12 sections) — ce qui est utilisé

| Section | Contenu | Utilisé dans le prompt ? |
|---|---|---|
| 1. Identité systémique | Description, rôle | non (redondant avec state_logic) |
| 2. Position dans le système | influences/influenced_by | non (redondant avec matrice) |
| 3. Dynamique interne | tendances, forces | non (redondant) |
| 4. Structure causale | forces/tensions conceptuelles | non (candidat futur) |
| 5. Ruptures | jalons génériques | ✓ "Ruptures structurantes" |
| 6. Indicateurs | noms abstraits | non |
| **7. Signaux faibles** | **10-20 signaux/variable, 5 catégories** | **non directement — réservoir pour section 12** |
| 8. États par scénario | level/volatility/state_logic ×6 | ✓ cœur de "ÉTAT DES VARIABLES" |
| 9. Scénarios liés | dominant/constrained_scenarios | non |
| 10. Narratif systémique | résumé variable | non |
| 11. Métadonnées de simulation | criticité/tipping_point/résilience | non (candidat futur "profil systémique") |
| **12. Trajectoire signaux 2025→2098** | **bloc YAML `signal_to_state`** | **✓ section TRAJECTOIRE du prompt** |

---

## Structure d'une fiche SCÉNARIO (9 sections) — ce qui est utilisé

| Section | Utilisé ? |
|---|---|
| 1. Description | non |
| 2. Déclencheurs | ✓ `triggers` |
| 3. Effets systémiques | ✓ `system_effects` |
| 4. Variables structurantes | ✓ pilotes/renforcées/contraintes |
| 4A. États des variables | non (redondant, fiches variables prioritaires) |
| 5-8 | non |
| **9. Synthèse systémique** (Résumé/Logique système/Interprétation/Implications) | **✓ FIXÉ récemment** (bug d'extraction corrigé dans `loader.py`) — apparaît maintenant dans "Résumé du monde", "Logique systémique", "Implications globales" |

---

## Mécanisme `signal_to_state` (section 12) — cœur de la trajectoire

Chaque variable a un bloc YAML `signal_to_state` listant des **signaux**,
chacun avec, **pour chacun des 6 scénarios** : `evolution` (~7 mots),
`date_bascule` (fenêtre AAAA-AAAA), `evenement_cle` (~7 mots, événement
daté nommé).

`snapshot.py::build_signal_trajectory()` agrège, pour le scénario actif,
tous les `evenement_cle` et les classe :
- **"majeur"** : implique une variable pilote
- **"structurant"** : `evenement_cle` partagé entre ≥2 variables
- **"local"** : variable non-pilote, non partagée

`prompt_builder.py` sélectionne :
- **6 "majeurs/structurants"** → section "Événements historiques clés"
- **2 "locaux"** (filtrés par pertinence avec les `variables_visibles`/
  `variables_secondaires` de la thématique) → section "Signaux complémentaires"

### Rotation à mémoire (NOUVEAU)

Fichier `generator/state/trajectory_usage.json` : compte, par scénario et
par `evenement_cle`, combien de fois il a déjà été sélectionné. À chaque
génération (hors `--dry-run`), les événements les moins utilisés sont
privilégiés → couverture homogène sur un grand corpus d'articles, sans
répétition systématique.

**État actuel (breakdown)** : 28 signaux uniques (24 historiques + 4
ajoutés sur `sante_biotechnologies`) → 10 "majeurs", 18 "locaux".

---

## Pipeline Python — 3 modes de génération

### Mode API (`generate.py` / `generate_series.py`, sans `--dry-run`)
loader → snapshot → prompt_builder (`dry_run=False`, met à jour la mémoire
de rotation) → `api.py` (appel Claude) → sauvegarde `.md` (frontmatter +
article) dans `articles/{scenario}/` → `_index.md`

### Mode dry-run (`--dry-run`)
Identique mais sans appel API, sans mise à jour de la mémoire de rotation
(juste un aperçu).

### Mode manuel SANS API (`generate_manual.py` — NOUVEAU)
```
python3 generate_manual.py prompt   # affiche SYSTEM+USER PROMPT du prochain
                                     # article de la série, met à jour la
                                     # mémoire de rotation, avance la séquence
python3 generate_manual.py status   # avancement (X/N, prévisualisé/sauvegardé)
python3 generate_manual.py save <fichier_article.txt>  # (optionnel) sauvegarde
                                     # au format .md dans articles/{scenario}/
```
L'article est rédigé par Claude **dans le chat**, à partir du prompt
copié-collé. `manual_progress.json` suit l'avancement.

---

## validate.py — 7 passes (inchangé)

Résultat actuel : **0 erreurs | 4 avertissements** (2 références à des
instances non encore créées — normal, en attente de l'API).

---

## CHANTIER EN COURS — Enrichissement section 7 → section 12

**Objectif** : pour chaque variable, promouvoir 3-4 signaux de la section
7 ("Signaux faibles", 10-20 par variable, jamais utilisés actuellement)
vers la section 12 (`signal_to_state`, développé sur les 6 scénarios),
pour enrichir le pool de jalons disponibles pour la rotation à mémoire
(corpus cible : 5-10 articles/thématique × 20 thématiques par scénario).

**Aucune modification de code requise** — le pipeline est déjà générique.

**Format calibré** : ~7 mots/champ (`evolution`, `evenement_cle`), validé
sur `sante_biotechnologies`.

**Process** : 1 chat par variable (ou 2-3 regroupées), en fournissant à
chaque fois `brief_section7_vers_12.md` + `registre_evenements.md` à jour
+ la/les fiche(s) variable(s) concernée(s). Le registre est régénéré après
chaque variable traitée pour éviter les collisions de noms/dates/lieux
entre chats séparés.

**Avancement** : 1/12 fait (`sante_biotechnologies` : 2 signaux existants
+ 4 nouveaux = 6 signaux développés). Cas particulier à traiter :
`systeme_economique_redistribution` a sa section 7 **vide** (à reconstruire).

---

## Fichiers modifiés/créés durant cette session (à jour sur la machine)

- `generator/loader.py` — fix extraction section 9 scénarios (Résumé/
  Logique système/Implications)
- `generator/prompt_builder.py` — rotation des jalons majeurs + signaux
  complémentaires locaux + rotation à mémoire
- `generator/generate.py` — fix import `anthropic` en dry-run
- `generator/generate_series.py` — idem + VAULT_PATH
- `generator/generate_manual.py` — nouveau, pipeline sans API
- `variables/sante_biotechnologies.md` — +4 signaux en section 12
- `registre_evenements.md` — nouveau
- `brief_section7_vers_12.md` — nouveau

---

## PROCHAINES ÉTAPES

1. Continuer le chantier section 7→12 (11 variables restantes, nouveaux chats)
2. Une fois une clé API obtenue : `generate_entities.py`, `create_entity.py`,
   `create_event.py` pour compléter les instances manquantes (2 avertissements
   actuels de `validate.py`)
3. Génération de la première vraie série avec l'API (ou en mode manuel)
4. Plus tard : signaux faibles **custom** liés à l'actualité (architecture
   similaire aux événements custom — chantier séparé, après stabilisation
   du format section 7→12)
