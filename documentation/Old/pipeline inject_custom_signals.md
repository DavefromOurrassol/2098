
Voici le pipeline complet de `inject_custom_signals.py`, de A à Z :

## 0. Point de départ — toi

Tu remplis `signaux_custom/queue.yaml` avec des idées en langage naturel :

```yaml
queue:
  - id: mon_signal
    description: >
      Plusieurs pays testent des chatbots thérapeutes remboursés
      par la sécurité sociale.
    source: actualite_2026-06
    variable_hint: sante_biotechnologies  # optionnel
```
    variable_hint: null quand on ne sait pas
Tu lances :

```bash
python3 generator/inject_custom_signals.py
```

---

## 1. Sélection — Appel API #1

Le script envoie à Claude :

- ton idée (description)
- un résumé condensé des 12 variables (nom, domain, sub_variables, state_logic par scénario — ~5 200 tokens)

Claude répond en JSON :

```json
{"variables": ["sante_biotechnologies"], "categorie": "technological", "signal_slug": "chatbots_therapeutes_remboursement"}
```

---

## 2. Développement — Appel API #2 (par variable cible)

Le script envoie à Claude :

- ton idée + le signal_slug + la catégorie
- la section 7 de la fiche variable (signaux faibles existants)
- la section 8 (state_logic des 6 scénarios — pour la cohérence narrative)
- la section 12 (signaux déjà développés — pour le style et le format)
- le registre des événements filtré (anti-collision)
- les règles de format (`FORMAT_RULES` : 4-11 mots, fenêtres AAAA-AAAA, années dans les fenêtres...)

Claude répond en JSON avec :

```json
{
  "signal_to_state_yaml": "  - signal: chatbots_therapeutes_remboursement\n    scenarios:\n      breakdown:\n        evolution: ...\n        date_bascule: 2040-2058\n        evenement_cle: ... 2051\n      ...",
  "section7_annotation": "- chatbots thérapeutes remboursés (→ signal_custom: ...)"
}
```

---

## 3. Validation mécanique — Python pur, zéro API

Le script vérifie automatiquement :

- YAML syntaxiquement valide
- 6 scénarios présents
- `evolution` et `evenement_cle` : 4 à 11 mots
- année dans `evenement_cle` ∈ `date_bascule`
- pas de fenêtre `date_bascule` dupliquée pour cette variable/scénario
- pas de collision exacte avec un `evenement_cle` du registre

**Si ça échoue** → Appel API #3 (correction ciblée) avec la liste des problèmes, jusqu'à 2 tentatives. Si toujours en échec → `needs_review.yaml`.

---

## 4. Injection — Python pur, zéro API

Si la validation passe :

**a)** Ajoute le bloc YAML dans `variables/{slug}.md`, section 12 (avant le ``` final)

**b)** Ajoute une ligne dans la section 7 de la même fiche, sous `**custom (signaux d'actualité)**` :

```
- chatbots thérapeutes remboursés (→ signal_custom: chatbots_therapeutes_remboursement, source: actualite_2026-06)
```

**c)** Régénère `generator/registre_evenements.md` : insère les 6 nouvelles lignes (1 par scénario), triées chronologiquement, met à jour le compteur total

**d)** Écrit `signaux_custom/{signal_slug}.md` — fiche d'audit avec l'idée source, la date, la variable cible, et le YAML injecté

**e)** Déplace l'idée de `queue.yaml` vers `processed.yaml`

---

## 5. Résultat

- `variables/sante_biotechnologies.md` : 7 signaux au lieu de 6
- `generator/registre_evenements.md` : 444 entrées au lieu de 432
- `signaux_custom/chatbots_therapeutes_remboursement.md` : fiche d'audit
- `signaux_custom/processed.yaml` : historique des injections réussies
- `signaux_custom/queue.yaml` : vidé (les idées traitées en sont retirées)

---

## Ce que le pipeline ne fait PAS

- Il ne modifie pas `validate.py`, `loader.py`, `snapshot.py` ou `prompt_builder.py`
- Il ne crée pas d'entité ni d'instance
- Il ne génère pas d'article
- Il ne fait pas de recherche web — l'idée vient entièrement de toi dans `queue.yaml`