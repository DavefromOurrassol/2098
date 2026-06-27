
## 1. OBJECTIF GÉNÉRAL

Ourrassol est un système de modélisation et d’analyse de dynamiques systémiques.

Il vise à :

- représenter des variables structurées (concepts, forces, systèmes)
    
- modéliser les influences entre ces variables
    
- analyser les interactions et boucles de rétroaction
    
- générer des scénarios prospectifs
    
- exploiter GPT comme moteur d’interprétation et de synthèse
    

---

## 2. NATURE DU SYSTÈME

Le système est un **graphe de connaissances dynamique** composé de :

- Variables (nœuds)
    
- Relations d’influence (arêtes)
    
- Scénarios (combinaisons de variables)
    
- Tendances (évolutions temporelles)
    
- Acteurs / systèmes (contextes)
    

---

## 3. STRUCTURE DES VARIABLES

Chaque variable contient :

- Nom
    
- Type (ex : moteur, dépendant, stabilisateur)
    
- Intensité (faible / moyenne / forte)
    
- Vitesse (lente / moyenne / rapide)
    
- Inertie (faible / moyenne / forte)
    
- Direction (↑ ↓ →)
    
- Influence (liste de variables influencées)
    
- Influencée par (liste de variables sources)
    

---

## 4. REPRÉSENTATION DES RELATIONS

Deux formats possibles :

### A. Notion (structure base de données)

- relations via IDs
    
- multi-select pour simplification
    
- dépendance à API
    

### B. Obsidian (recommandé long terme)

- liens directs [[Variable]]
    
- graphe natif
    
- structure lisible et modifiable
    

---

## 5. PIPELINE DE DONNÉES

### Option 1 — Notion + Python + GPT

1. extraction des variables depuis Notion API
    
2. transformation en structure texte ou JSON
    
3. analyse par GPT
    
4. retour interprétation
    

### Option 2 — Obsidian + Python + GPT

1. lecture des fichiers Markdown
    
2. extraction des liens [[...]]
    
3. construction d’un graphe
    
4. analyse et simulation via GPT
    

---

## 6. RÔLE DE PYTHON

Python agit comme moteur intermédiaire :

- extraction des données
    
- nettoyage et transformation
    
- construction du graphe
    
- calcul des relations
    
- préparation des prompts GPT
    

---

## 7. RÔLE DE GPT

GPT est utilisé pour :

- analyser les structures systémiques
    
- identifier les variables critiques
    
- détecter les boucles d’influence
    
- générer des scénarios prospectifs
    
- proposer des interprétations globales
    

---

## 8. LIMITES ACTUELLES

### Notion

- relations complexes difficiles à manipuler
    
- IDs non lisibles
    
- API parfois restrictive
    

### Make

- faible flexibilité pour graphes complexes
    
- difficile à maintenir
    

### Mac 2011

- compatible pour prototype Python léger uniquement
    

---

## 9. DIRECTION RECOMMANDÉE

### Court terme

- Notion + Python + GPT (prototype fonctionnel)
    

### Moyen terme

- migration vers Obsidian pour structure graphe
    

### Long terme

- système hybride :  
    Obsidian (structure)
    
    - Python (moteur)
        
    - GPT (raisonnement)
        

---

## 10. VISION DU SYSTÈME

Ourrassol évolue vers un :

> moteur de simulation systémique basé sur des variables interconnectées permettant d’explorer des scénarios futurs à partir de dynamiques causales.