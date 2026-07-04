# Guide utilisateur — Carte & Couverture géographique
*Ourrassol 2098 — 4 juillet 2026*

Ce guide couvre deux outils complémentaires : l'onglet **🗺️ Carte** du GUI (bascules pays↔zone au cas par cas, avec rapport d'impact) et le script **`complete_geographie_coverage.py`** (traitement en masse des pays sans zone). Un troisième outil, **`check_zones_coherence.py`**, sert à vérifier que tout est cohérent après coup.

---

## 1. L'onglet Carte

### À quoi ça sert
Affecter un pays à une zone N1 d'un scénario, en visualisant l'impact narratif avant de confirmer.

### Workflow
1. Ouvrir le GUI (`http://localhost:5000`), onglet **🗺️ Carte**
2. Choisir le scénario en haut
3. Cliquer sur un pays sur la carte (gris = non affecté, coloré = déjà affecté)
4. Dans le panneau latéral, deux options :
   - **Sélection manuelle** d'une zone N1 existante dans la légende
   - **"Demander une proposition (LLM)"** — le modèle configuré (voir §4) propose une zone avec justification
5. **"🔍 Évaluer l'impact"** — obligatoire, le bouton de confirmation n'apparaît qu'après. Génère un rapport en lecture seule (sous-zones orphelines, instances/événements liés, mentions textuelles), sauvegardé dans `documentation/need_action/impact_bascule_{pays}_{scenario}.md`
6. Confirmer la bascule

### Cas particulier : Royaume-Uni
`Royaume-Uni` / `Angleterre` / `Écosse` / `Pays de Galles` correspondent à 4 entrées `pays_liste` pour un seul polygone GBR sur le fond de carte. Un sélecteur intermédiaire apparaît au clic.

### Bouton "🚫 Ignorer"
Marque un pays comme "blanc intentionnel" — il reste dans `zones_manquantes.yaml` avec un statut dédié, mais disparaît de la vue "zones manquantes" du dashboard. Utile pour les pays qu'on ne veut délibérément pas traiter.

---

## 2. complete_geographie_coverage.py

### À quoi ça sert
Traiter en masse les pays qui n'ont **aucune** zone dans un scénario (contrairement à la carte, pensée pour un pays à la fois).

### Pré-requis : clé API chargée
```bash
source ~/.zshrc
echo "MISTRAL_API_KEY=${MISTRAL_API_KEY:0:8}..."
```
Si la clé n'apparaît pas, le script échouera avec `Illegal header value b'Bearer '`. À vérifier à chaque nouveau terminal.

### Workflow obligatoire en deux temps

**Étape 1 — Review** (ne modifie jamais le vault) :
```bash
python3 complete_geographie_coverage.py --scenario reference --review
```
Génère `coverage_proposals_reference.yaml` avec une proposition par pays manquant.

**Étape 2 — Validation manuelle** :
```bash
code coverage_proposals_reference.yaml
```
Parcourir les paires `pays` / `zone_slug` / `justification`. Mettre `valide: false` sur toute proposition géographiquement incohérente (ex. un pays d'Amérique du Sud envoyé vers une zone africaine).

Repérer aussi les rejets automatiques du script (déjà marqués `valide: false` avec un `avertissement`) :
```bash
python3 -c "
import yaml
data = yaml.safe_load(open('coverage_proposals_reference.yaml', encoding='utf-8'))
for a in data.get('affectations', []):
    if a.get('valide') is False:
        print(a.get('pays'), '→', a.get('avertissement') or a.get('justification', '')[:100])
"
```
Ces rejets automatiques signalent en général un vrai rate limit API (`Status 429`) — dans ce cas, il suffit de relancer `--review` sur ce scénario, ça retente tout depuis zéro.

**Étape 3 — Apply** :
```bash
python3 complete_geographie_coverage.py --scenario reference --apply
```
N'applique que les entrées restées `valide: true`.

### Traiter plusieurs scénarios

Le `--review` peut être lancé en boucle sans risque (il n'écrit rien) :
```bash
for s in breakdown fortress_world new_sustainability eco_communalism policy_reform reference; do
  echo "=== $s ==="
  python3 complete_geographie_coverage.py --scenario "$s" --review
done
```
En revanche, valider **chaque** fichier de propositions avant l'`--apply` correspondant — ne jamais enchaîner `--apply` sur plusieurs scénarios sans relecture intermédiaire.

### Rate limiting
Le script attend 8 secondes entre chaque appel API (batch de 12 pays). Si l'erreur `429 Rate limit exceeded` apparaît quand même, c'est que le palier de ton compte API est plus restrictif — relancer le `--review` du scénario concerné suffit, rien n'a été écrit entre-temps.

---

## 3. check_zones_coherence.py

### À quoi ça sert
Diagnostic pur (aucune écriture), à lancer après toute session touchant à la géographie :
- Le fichier `geographie/{scenario}.md` parse-t-il correctement en YAML ?
- Reste-t-il des pays réels rattachés uniquement à une sous-zone, sans zone N1 ?

```bash
python3 check_zones_coherence.py --scenario reference
python3 check_zones_coherence.py --all
```

**Réflexe recommandé** : lancer `--all` en fin de session, après tout `--apply` ou toute série de bascules sur la carte.

---

## 4. Choix du modèle LLM

Deux réglages possibles pour la carte (`carte_propose`) et pour `complete_geographie_coverage.py` : `config.json` (`llm.provider`, `llm.model_mistral`) ou le sélecteur du GUI.

**`mistral-small`** (par défaut actuellement) peut produire des raisonnements géographiques faux avec une grande confiance (ex. affirmer qu'un pays d'Amérique du Sud est proche de l'Afrique). Pour ce type de tâche, préférer :
- `claude-sonnet-4-6` — le plus fiable
- `mistral-large` — compromis coût/fiabilité correct

---

## 5. Résumé des commandes courantes

```bash
# Lancer le GUI
lsof -ti:5000 | xargs kill -9
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py

# Charger la clé API si besoin
source ~/.zshrc

# Traiter un scénario avec complete_geographie_coverage.py
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/generator"
python3 complete_geographie_coverage.py --scenario NOM --review
code coverage_proposals_NOM.yaml
python3 complete_geographie_coverage.py --scenario NOM --apply

# Vérifier la cohérence
python3 check_zones_coherence.py --all
```
