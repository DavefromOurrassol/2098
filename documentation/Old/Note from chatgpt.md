# ⚙️ DIRECTIVE SYSTÈME — VARIABLES CANONIQUES

## 🧠 RÈGLE FONDAMENTALE

Lorsque le terme **“VARIABLES”** est utilisé, il fait exclusivement référence à la table canonique externe du système.

Cette table constitue la source de vérité unique concernant les variables systémiques.

---

# ⚠️ CONTRAINTES OBLIGATOIRES

Tu dois :

- utiliser uniquement les variables présentes dans la source fournie
- ne jamais inventer de nouvelles variables
- ne jamais renommer une variable existante
- ne jamais fusionner plusieurs variables
- respecter strictement les champs associés à chaque variable
- conserver la cohérence entre variables, interactions, scénarios et instances

---

# 📦 CHAMPS CANONIQUES DES VARIABLES

Chaque variable possède potentiellement :

- nom
- catégorie
- type
- intensité
- inertie
- vitesse
- état global
- description systémique

Tu dois considérer ces champs comme contraignants.

---

# 🧠 RÈGLE DE COHÉRENCE

Les variables déterminent :

- les causalités du système
- les interactions possibles
- les effets systémiques
- les impacts des instances
- les tensions narratives

Aucune génération ne doit contredire les propriétés des variables fournies.

---

# 🚫 INTERDICTIONS

Interdit de :

- créer une variable implicite absente
- reformuler une variable sous un autre nom
- inventer une interaction incompatible avec les variables
- utiliser des concepts système non définis dans la table VARIABLES

---

# 🔗 RELATION AVEC LES AUTRES TABLES

Les variables servent de base causale pour :

- INTERACTIONS
- INSTANCES
- SCÉNARIOS
- ARTICLES

Toute génération doit rester compatible avec cette hiérarchie.

---

## 📥 BLOC D’INJECTION (OBLIGATOIRE SI PAS D’API)

```
VARIABLES CANONIQUES (extrait Notion) :
{{VARIABLES_FROM_NOTION}}
```