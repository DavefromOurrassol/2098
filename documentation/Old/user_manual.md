---
type: documentation
titre: Manuel Utilisateur — Ourrassol 2098
date_maj: 2026-06-28
---

# Manuel Utilisateur — Ourrassol 2098

Guide pratique pour utiliser le pipeline de génération d'articles fictifs en 2098.

---

## Prérequis

### Installation (une fois)

```bash
python3 -m pip install anthropic
python3 -m pip install mistralai
```

### Clés API (dans `~/.zshrc`)

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
export MISTRAL_API_KEY='...'
```

Après modification du `.zshrc` :
```bash
source ~/.zshrc
```

---

## Choisir son fournisseur LLM

Par défaut, tous les scripts utilisent **Mistral**. Pour utiliser Claude :

```bash
LLM_PROVIDER=claude python3 generate_series.py
```

Pour changer le modèle Mistral :
```bash
LLM_MODEL=mistral-large-latest python3 generate_series.py
```

---

## Générer un article unique

### 1. Configurer `config.yaml`

```yaml
scenario: breakdown              # le monde dans lequel se passe l'article
ligne_editoriale: opposition     # pro_pouvoir | opposition
zone_slug: ""                    # laisser vide = zone automatique
thematique: actualites_a_la_une  # rubrique de l'article
article:
  longueur: analyse              # breve | analyse | reportage | chronique | editorial | auto
  angle_specifique: ""           # optionnel : "focus sur les réfugiés"
  titre_suggere: ""              # optionnel
output:
  nom_fichier: auto              # auto = horodatage + date fictive
```

### 2. Lancer la génération

```bash
cd generator/
python3 generate.py
```

L'article est sauvegardé dans `articles/{scenario}/`.

### 3. Tester sans générer

```bash
python3 generate.py --dry-run
```

Affiche le system prompt et le user prompt sans appeler l'API.

---

## Générer une série d'articles

### 1. Configurer `config_series.yaml`

```yaml
scenario: eco_communalism
ligne_editoriale:                # laisser vide = pro_pouvoir/opposition aléatoire à chaque article
thematiques:
  - actualites_a_la_une
  - politique
  - economie_finance
  - societe
articles_par_thematique: 1
longueur: auto
angle_specifique: ""
injections: []
```

### 2. Lancer la série

```bash
python3 generate_series.py
```

### 3. Options utiles

```bash
python3 generate_series.py --dry-run          # tester sans appeler l'API
python3 generate_series.py --scenario breakdown  # forcer un scénario
python3 generate_series.py --validate-first   # valider le vault avant de générer
```

---

## Générer un article manuellement (sans API)

Utile pour évaluer le prompt avant de dépenser des tokens.

```bash
# Affiche le prompt à copier dans le chat Claude
python3 generate_manual.py prompt

# Voir l'avancement de la série
python3 generate_manual.py status

# Sauvegarder l'article généré dans le vault
python3 generate_manual.py save /tmp/mon_article.txt
```

---

## Les journaux locaux

Chaque article est rédigé depuis la perspective d'un journal ancré dans une zone géographique.

### Structure éditoriale

Deux lignes par scénario :

| Ligne | Description |
|---|---|
| `pro_pouvoir` | Journal aligné avec le pouvoir dominant du scénario |
| `opposition` | Journal critique, clandestin ou marginal |

### Générer les journaux locaux

**À faire une fois par scénario**, après que la bible géographique existe :

```bash
python3 generate_journaux.py --scenario breakdown
python3 generate_journaux.py --all               # tous les scénarios
```

Si de nouvelles zones sont ajoutées au vault plus tard :
```bash
python3 generate_journaux.py --all --update      # ajoute seulement les zones manquantes
```

### Comment le journal est choisi à la génération

Le pipeline choisit automatiquement l'édition locale correspondant à la zone de l'article.
Si aucune édition locale n'existe pour cette zone, il remonte vers le réseau global, puis
vers le profil hardcodé. Un warning s'affiche dans ce cas :

```
[WARN][journal] Pas d'édition locale pour zone 'X' / breakdown / opposition → fallback réseau global
```

---

## Les scénarios disponibles

| Slug | Description | Tension |
|---|---|---|
| `breakdown` | Effondrement partiel, fragmentation des États | 5/5 |
| `fortress_world` | Blocs géopolitiques fermés, contrôle des ressources | 5/5 |
| `policy_reform` | Technocratie mondiale, régulation globale | 4/5 |
| `reference` | Équilibre fragile, crises récurrentes | 3/5 |
| `eco_communalism` | Territoires autonomes, sobriété énergétique | 3/5 |
| `new_sustainability` | Transition écologique réussie, gouvernance IA | 2/5 |

---

## Les thématiques disponibles

```
actualites_a_la_une  politique            economie_finance
environnement_climat sciences_technologies societe
culture              international        musique
sports               faits_divers         opinions_editoriaux
lifestyle_art_de_vivre sante             education
histoire_patrimoine  medias_communication religion_spiritualite
petites_annonces_services meteo
```

---

## Les longueurs d'articles

| Valeur | Longueur cible |
|---|---|
| `breve` | 200 à 400 mots |
| `analyse` | 600 à 900 mots |
| `reportage` | 700 à 1000 mots |
| `chronique` | 400 à 700 mots |
| `editorial` | 500 à 800 mots |
| `auto` | format naturel de la thématique |

---

## Ajouter des entités au vault

```bash
python3 create_entities_and_instances.py
```

Au lancement, choisir le mode :
- `custom` — traite `entites_custom/queue.yaml` (tu as défini les entités à l'avance)
- `auto` — Claude invente N entités selon le scénario
- `auto-suggest` — Claude propose des idées dans `queue.yaml` sans injecter

Après injection, le cycle de validation se lance automatiquement.

---

## Ajouter des événements au vault

```bash
python3 inject_custom_events.py
```

Modes : `custom` | `auto`

---

## Valider le vault

```bash
python3 validate.py                    # validation silencieuse
python3 validate.py -v                 # verbose — détail de chaque section
python3 validate.py --report           # génère validation_report.md
python3 validate.py --narrative        # force la vérification narrative
```

À lancer après chaque injection ou modification du vault.

---

## Retirer une entité ou un événement

```bash
# Mode interactif (lit undo_queue.yaml)
python3 undo_custom.py --execute

# Mode direct
python3 undo_custom.py --slug mon_entite_breakdown --type instance --generalisation no --execute
```

Toujours tester en dry-run d'abord (comportement par défaut sans `--execute`).

---

## Où trouvent les articles générés ?

```
vault/
  articles/
    breakdown/
      20260628_143022_breakdown_actualites_a_la_une_article_3janvier2098.md
      20260628_143045_breakdown_politique_article_17janvier2098.md
      _index.md
    eco_communalism/
      ...
```

---

## Commandes du quotidien

```bash
# Générer une série complète
python3 generate_series.py

# Avec Claude
LLM_PROVIDER=claude python3 generate_series.py

# Tester le pipeline sans dépenser de tokens
python3 generate_series.py --dry-run

# Valider le vault
python3 validate.py

# Mettre à jour les journaux locaux si nouvelles zones
python3 generate_journaux.py --all --update
```

---

## En cas de problème

**Clé API non définie :**
```bash
source ~/.zshrc
```

**Module manquant :**
```bash
python3 -m pip install mistralai
python3 -m pip install anthropic
```

**Vault invalide avant génération :**
```bash
python3 validate.py -v    # identifier les erreurs
```

**Warning journal zone manquante :**
```bash
python3 generate_journaux.py --all --update
```
