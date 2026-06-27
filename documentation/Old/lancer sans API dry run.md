
Voici le workflow exact qu'on a utilisé — à expliquer/coller dans le nouveau chat :

---

## Workflow de test SANS API (génération d'articles)

**1. Lancer le dry-run en local**

```bash
python3 generate.py --dry-run
```

(ou `generate_series.py --dry-run` pour plusieurs articles)

Ce mode fait tourner tout le pipeline Python (loader → snapshot → prompt_builder) mais **n'appelle pas l'API**. Il affiche dans le terminal :

```
--- SYSTEM PROMPT ---
[texte du system prompt]

--- USER PROMPT (complet) ---
[texte complet du user prompt — contexte monde, variables, tensions, trajectoire, entités, consigne]
```

**2. Copier les deux blocs dans le chat**

L'utilisateur colle le contenu de `--- SYSTEM PROMPT ---` et `--- USER PROMPT (complet) ---` dans le chat, en deux messages ou un seul, en précisant clairement que c'est le system prompt et le user prompt.

**3. Claude joue le rôle de l'API**

Claude lit le system prompt comme ses instructions de rôle (journaliste de 2098), et le user prompt comme la requête (contexte du monde + consigne de rédaction), puis **écrit directement l'article** — comme le ferait l'appel API réel.

**4. Validation**

Claude vérifie que l'article respecte les contraintes : entités canoniques utilisées avec noms exacts, pas de métalangage (scénario/variable/simulation), événements datés mentionnés naturellement, cohérence avec l'état systémique du monde.

---

## Point important pour le nouveau chat

Le nouveau chat **n'a pas accès au système de fichiers** (`/Users/davidlopez2005/...`) ni au vault Obsidian — il ne peut PAS lancer `python3 generate.py` lui-même. C'est **vous** qui lancez la commande dans votre Terminal local, et qui collez le résultat (system prompt + user prompt) dans le chat. Claude ne fait que la dernière étape : écrire l'article à partir de ce texte.

---

## Pour create_event.py sans API

Même logique mais inversée — au lieu de lancer un script, vous donnez directement à Claude dans le chat les informations qu'aurait demandées `create_event.py` (nom, date, description, scénarios), et Claude génère lui-même les fichiers `.md` (archétype + instances) avec la commande `create_file`, comme il l'a fait pour les 3 événements déjà créés.