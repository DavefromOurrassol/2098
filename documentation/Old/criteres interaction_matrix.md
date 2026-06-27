# 🔷 1. weight (poids d’influence)

## Définition

Mesure la **force de l’influence causale directe** d’une variable A sur une variable B.

## Sens

- Intensité de l’impact
- Amplitude de propagation dans le système

## Type

- réel normalisé (souvent 0 → 1 ou 0 → 10)

## Interprétation

- 0.0 = aucune influence
- 0.3 = influence faible
- 0.6 = influence significative
- 1.0 = influence structurelle majeure

## Exemple

```
energie → geopolitique = 0.9
```

👉 L’énergie structure fortement la géopolitique.

---

# 🔷 2. polarity (polarité)

## Définition

Indique si l’influence est :

- **positive (+)** : renforce / augmente
- **negative (-)** : inhibe / réduit

## Sens systémique

Détermine la dynamique des boucles.

## Valeurs

```
+  : effet amplificateur-  : effet inhibiteur
```

## Exemples

- économie ↑ → énergie ↑ → (+)
- climat dégradé → agriculture ↓ → (+ ou - selon structure)

---

# 🔷 3. lag (délai temporel)

## Définition

Temps nécessaire pour que l’effet de A sur B soit observable.

## Unité

- abstraite (1–10) ou réelle (mois / années)

## Interprétation

- 0–1 : immédiat (marchés, infos)
- 2–4 : court terme (économie, politique)
- 5–7 : moyen terme (démographie, infrastructures)
- 8–10 : long terme (climat, biogéophysique)

## Exemple

```
climat → economie = lag 8
```

👉 impact lent mais structurel.

---

# 🔷 4. nonlinearity (non-linéarité)

## Définition

Mesure si la relation A → B est :

- proportionnelle (linéaire)
- ou avec seuils / ruptures / accélérations

## Valeurs possibles

```
low        = relation stable et proportionnellemedium     = effets avec saturationhigh       = effets de seuil / basculevery_high  = comportement chaotique ou exponentiel
```

## Exemples

- énergie → croissance : medium
- climat → migration : high
- conflits → géopolitique : very_high

---

# 🔷 5. temporal_weight (poids temporel)

## Définition

Mesure **l’importance d’une relation dans le temps long du système**.

👉 Différent de weight :

- weight = intensité instantanée
- temporal_weight = importance sur horizon long

## Sens

Permet de distinguer :

- influences rapides mais superficielles
- influences lentes mais structurelles

## Valeurs

```
0.0 → court terme uniquement0.5 → mix court / long terme1.0 → structurant long terme
```

## Exemple

```
climat → energie :weight = 0.7temporal_weight = 1.0
```

👉 impact très fort dans le long terme.

---

# 🔷 6. feedback_role (rôle dans boucle)

## Définition

Indique comment une interaction participe aux boucles de rétroaction.

## Valeurs principales

### 🔁 reinforcing (R)

Amplifie le système

```
A → B → A = croissance ou effondrement
```

---

### ⚖️ balancing (B)

Stabilise le système

```
A ↑ → B ↓ → A ↓
```

---

### ⊘ neutral

Pas significatif dans une boucle

---

### ❓ conditional

Dépend du contexte (seuils, régime)

---

## Exemple

```
geopolitique → energie:  feedback_role: reinforcing
```

👉 conflits renforcent la pression énergétique → conflits augmentent.

---

# 🔷 SYNTHÈSE ULTRA-COMPACTE

```
weight           = force de l’effetpolarity         = direction (+ / -)lag              = délai temporelnonlinearity     = stabilité vs rupturetemporal_weight  = importance long termefeedback_role    = rôle dans les boucles
```

# 🔷 IMPORTANT (pour ton système)

Ces 6 paramètres permettent :

### 1. dynamique locale

→ weight + polarity + lag

### 2. comportement global

→ nonlinearity + feedback_role

### 3. stabilité du système dans le temps

→ temporal_weight