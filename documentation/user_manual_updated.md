---
type: documentation
titre: Manuel Utilisateur — Ourrassol 2098
date_maj: 2026-06-29
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

## Lancer le GUI

```bash
# Tuer un éventuel process existant
lsof -ti:5000 | xargs kill -9

cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py
# → ouvrir http://localhost:5000 dans Chrome
```

Le GUI permet de lancer tous les scripts du pipeline avec des formulaires guidés, sans passer par le terminal.

---

## Choisir son fournisseur LLM

Dans la **barre latérale du GUI** : sélecteur LLM toujours visible en haut.
- Provider : Mistral (défaut) ou Claude
- Modèle : liste filtrée selon le provider
- Badge coût : 🟢 économique / 🟡 standard / 🔴 coûteux

En ligne de commande :
```bash
LLM_PROVIDER=claude python3 generate_series.py
LLM_MODEL=mistral-large-latest python3 generate_series.py
```

---

## Générer un article unique

### Via le GUI
1. Cliquer sur **Generate** dans la sidebar
2. Remplir le formulaire guidé `config.yaml` :
   - Scénario, ligne éditoriale, zone géographique (select hiérarchique N1/N2/N3)
   - Thématique (select 20 valeurs), longueur, angle spécifique
3. Cliquer **Sauvegarder** puis **Lancer**

### Via le terminal
```bash
cd generator/
python3 generate.py
python3 generate.py --dry-run   # tester sans appeler l'API
```

### config.yaml — valeurs autorisées

**scenario** : `breakdown | fortress_world | new_sustainability | eco_communalism | policy_reform | reference`

**ligne_editoriale** : `pro_pouvoir | opposition`

**thematique** : `actualites_a_la_une | politique | economie_finance | environnement_climat | sciences_technologies | societe | culture | international | musique | sports | faits_divers | opinions_editoriaux | lifestyle_art_de_vivre | sante | education | histoire_patrimoine | medias_communication | religion_spiritualite | petites_annonces_services | meteo`

**longueur** : `breve (200-400) | analyse (600-900) | reportage (700-1000) | chronique (400-700) | editorial (500-800) | auto`

---

## Générer une série d'articles

### Via le GUI
1. Cliquer sur **Generate series**
2. Remplir le formulaire guidé `config_series.yaml` :
   - Scénario, ligne éditoriale (ou vide = aléatoire)
   - Thématiques : chips cliquables (sélection multiple)
   - Articles par thématique, longueur, angle
3. Sauvegarder puis Lancer

### Via le terminal
```bash
python3 generate_series.py
python3 generate_series.py --dry-run
python3 generate_series.py --validate-first
```

---

## Générer un article manuellement (sans API)

```bash
python3 generate_manual.py prompt   # affiche le prompt
python3 generate_manual.py status   # avancement de la série
python3 generate_manual.py save /tmp/mon_article.txt
```

---

## Les journaux locaux

```bash
python3 generate_journaux.py --scenario breakdown
python3 generate_journaux.py --all
python3 generate_journaux.py --all --update   # zones manquantes seulement
```

---

## Ajouter des entités au vault

### Via le GUI
1. Cliquer sur **Create entities**
2. Choisir le mode dans les options CLI : `custom | auto | auto-suggest`
3. En mode **custom** : remplir le formulaire guidé (queue) :
   - **Nom** : texte libre
   - **Catégorie** : `IA | organisation | entreprise | institution | infrastructure | réseau | humain | système | hybride | autre | média | territoire`
   - **Rôle** : textarea — contrainte dure, reprise telle quelle
   - **État** : `actif | disparu | transformé | clandestin | historique | mythifié`
   - **Scénario de référence** : select 6 scénarios
   - **Scénarios à couvrir** : chips multi-select
   - **Zone géographique (hint)** : double select —
     - Onglet "Zone 2098" : select hiérarchique N1/N2/N3
     - Onglet "Pays 2026" : liste 86 pays → zone 2098 déduite automatiquement
   - **Source** : texte libre (optionnel)
4. Cliquer **Ajouter à la queue** — le formulaire se réinitialise
5. Répéter pour chaque entité
6. Cliquer **Lancer** pour traiter la queue

### Via le terminal
```bash
python3 create_entities_and_instances.py
# → choisir le mode : custom | auto | auto-suggest
```

---

## Ajouter des événements au vault

### Via le GUI
1. Cliquer sur **Inject events**
2. En mode **custom** : remplir le formulaire guidé (queue) :
   - **ID** : identifiant court (lettres, chiffres, underscores)
   - **Description** : textarea langage naturel
   - **Portée** : `locale | regionale | continentale | globale`
   - **Date approximative** : 2025–2097
   - **Intensité** : `faible | modérée | forte | majeure`
   - **Scénarios** : chips multi-select (vide = les 6)
   - **Variables impactées (hint)** : chips multi-select sur les 12 variables
   - **Nb variables max** : 1–4
   - **Zone géographique (hint)** : double select Zone 2098 / Pays 2026
   - **Source** : texte libre (optionnel)
3. Cliquer **Ajouter à la queue** puis **Lancer**

### Via le terminal
```bash
python3 inject_custom_events.py
```

---

## Zone géographique — double select (hint)

Pour `create_entities` et `inject_events`, le champ **Zone géographique (hint)** propose deux modes :

**Onglet "Zone 2098"** : select hiérarchique des zones fictives du scénario actif
- N1 : grandes zones continentales
- N2 : sous-zones régionales (indentées)
- N3 : zones locales (indentées ×2)

**Onglet "Pays 2026"** : liste de ~86 pays/régions du monde réel
- Sélectionner un pays → le système cherche la zone 2098 correspondante
- Résultat vert : zone trouvée → pré-remplit le select 2098
- Résultat orange : aucune zone 2098 ne couvre ce pays dans ce scénario → zone_hint vide, Claude gère narrativement

**Comportement si null** :
- L'entité/événement est créé normalement
- Le cas est loggé dans `documentation/need_action/zones_manquantes.yaml`
- À traiter via `enrich_geographie_recursive.py` pour combler le blanc

---

## Injecter des signaux faibles

### Via le GUI
1. Cliquer sur **Inject signals**
2. Remplir le formulaire guidé :
   - ID, description (textarea), variable hint (optionnel), nb variables max, source
3. Lancer

### Via le terminal
```bash
python3 inject_custom_signals.py
```

---

## Valider le vault

```bash
python3 validate.py                  # validation silencieuse
python3 validate.py -v               # verbose
python3 validate.py --report         # génère validation_report.md
python3 validate.py --narrative      # force vérification narrative
```

---

## Enrichir les instances minimales

```bash
python3 enrich_minimal.py --all --dry-run
python3 enrich_minimal.py --scenario breakdown --limit 10
python3 enrich_minimal.py --slug mon_entite_breakdown
python3 enrich_minimal.py --all --auto-cycle
```

---

## Géographie — construire et enrichir

```bash
# Construire une fiche géographie depuis zéro
python3 build_geographie_monde.py --scenario breakdown

# Enrichir les sous-zones récursivement
python3 enrich_geographie_recursive.py --scenario breakdown
python3 enrich_geographie_recursive.py --all
```

**Après enrichissement** : les zones `origine_reelle` sont mises à jour.
La route `/api/zones/lookup` relit les fiches en temps réel — pas besoin de régénérer `zones_pays.json`.

---

## Retirer une entité ou un événement

```bash
python3 undo_custom.py --execute                          # mode interactif
python3 undo_custom.py --slug mon_entite_breakdown --type instance --generalisation no --execute
```

Toujours tester en dry-run d'abord (comportement par défaut sans `--execute`).

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

## Les 12 variables du système

```
systeme_economique_redistribution    gouvernance_institutions
geopolitique_conflits                valeurs_culture_tempo_sociale
organisation_territoires             sante_biotechnologies
frontieres_du_systeme                technologie_information
climat_environnement_global          energie_ressources_critiques
demographie_mobilite_humaine         systemes_productifs_travail
```

---

## Commandes du quotidien

```bash
# Générer une série complète
python3 generate_series.py

# Avec Claude
LLM_PROVIDER=claude python3 generate_series.py

# Tester sans tokens
python3 generate_series.py --dry-run

# Valider le vault
python3 validate.py

# Mettre à jour les journaux locaux si nouvelles zones
python3 generate_journaux.py --all --update
```

---

## En cas de problème

**Port 5000 occupé :**
```bash
lsof -ti:5000 | xargs kill -9
```

**Dashboard erreur 404 :**
Relancer Flask après avoir vérifié que `app.py` contient bien `@app.route("/api/dashboard"...)`.

**Zones 2098 vides dans le formulaire :**
Vérifier que `vault_root` dans `config.json` pointe sur la racine du vault (là où se trouve `geographie/`).

**Zone null pour un pays 2026 :**
Le cas est loggé dans `documentation/need_action/zones_manquantes.yaml`.
Lancer `enrich_geographie_recursive.py --scenario x` pour enrichir la fiche.

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
python3 validate.py -v
```
