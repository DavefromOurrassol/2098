# BRIEF — Enrichissement section 7 → section 12 (signaux faibles)
## Projet Ourrassol 2098

---

## Contexte

Ourrassol 2098 est un simulateur de presse fictive générant des articles
de journaux situés en 2098, basé sur 6 scénarios systémiques × 12 variables
× 20 thématiques (architecture Obsidian + Python + API Claude).

Chaque fiche variable (`variables/{slug}.md`) contient 12 sections. Deux
nous intéressent ici :

- **Section 7 "Signaux faibles"** : liste de 10-20 signaux faibles par
  variable, répartis en 5 catégories (`technological`, `geopolitical`,
  `social`, `environmental`, `cognitive_cultural`). Ce sont des noms de
  signaux, sans développement.
- **Section 12 "Trajectoire des signaux 2025 → 2098"** : bloc YAML
  `signal_to_state` où certains signaux (actuellement 2/variable) sont
  "développés" avec, pour chacun des 6 scénarios, une `evolution`, une
  `date_bascule` et un `evenement_cle` (événement daté et nommé).

Le pipeline (`loader.py` → `snapshot.py` → `prompt_builder.py`) lit
**uniquement** la section 12. Ces événements datés/nommés alimentent la
section "TRAJECTOIRE 2025 → 2098" du prompt envoyé à Claude pour rédiger
chaque article — ils donnent des faits concrets à mentionner naturellement.

Le pipeline est **déjà générique** : il gère n'importe quel nombre de
signaux par variable, classe automatiquement chaque `evenement_cle` en
"majeur" (variable pilote), "structurant" (partagé entre variables) ou
"local" (variable non-pilote), et applique une **rotation à mémoire**
(fichier `state/trajectory_usage.json`) pour éviter les répétitions sur
un grand corpus d'articles.

**➜ Conclusion : ce chantier est purement un travail de CONTENU (rédaction
de YAML dans les fiches `.md`), AUCUNE modification de code n'est nécessaire.**

---

## Objectif

Pour chaque variable, **promouvoir 3-4 signaux supplémentaires** de la
section 7 vers la section 12 (en plus des 2 déjà existants), en écrivant
pour chacun une trajectoire complète sur les 6 scénarios
(`breakdown`, `fortress_world`, `new_sustainability`, `eco_communalism`,
`policy_reform`, `reference`).

**Variables pilotes** (impact sur le pool "majeurs" — plus visibles) :
`geopolitique_conflits`, `energie_ressources_critiques`,
`organisation_territoires`, `climat_environnement_global`,
`systemes_productifs_travail`

**Variables non-pilotes** (impact sur le pool "locaux") :
`systeme_economique_redistribution`, `gouvernance_institutions`,
`valeurs_culture_tempo_sociale`, `sante_biotechnologies` ✅ **fait**,
`frontieres_du_systeme`, `technologie_information`,
`demographie_mobilite_humaine`

⚠️ **Cas particulier** : `systeme_economique_redistribution` a sa
**section 7 entièrement vide**. Il faudra reconstruire une liste de
signaux candidats à partir de zéro (en s'inspirant du `domain`, des
`sub_variables`, et du `state_logic` par scénario de cette variable),
avant de pouvoir en développer 3-4 en section 12.

---

## Format calibré (validé sur sante_biotechnologies)

- `evolution` et `evenement_cle` : **~7 mots en moyenne** (min 4, max 11),
  même registre que les 144 entrées existantes — phrases courtes et
  percutantes, pas de longues descriptions.
- `evenement_cle` : inclut généralement une **année précise** à la fin
  (ex: "... 2051"), sauf quelques exceptions sans année dans les entrées
  existantes (rester cohérent avec le style déjà présent pour CETTE variable).
- `date_bascule` : fenêtre temporelle `AAAA-AAAA`, cohérente avec la
  narration du scénario (un événement de `breakdown` qui détruit un
  système peut avoir une fenêtre 2040-2065 ; un événement de
  `new_sustainability` qui construit quelque chose, plutôt 2030-2050).

---

## Processus, étape par étape

1. **Choisir 3-4 signaux** parmi ceux de la section 7 **non encore
   développés** en section 12 — viser la diversité entre les 5 catégories
   (technological/geopolitical/social/environmental/cognitive_cultural)
   plutôt que de piocher tous dans la même.

2. **Lire la section 8** ("États par scénario") de la fiche — chaque
   scénario y a un `state_logic` narratif. Les nouvelles `evolution`
   doivent être cohérentes avec ce narratif (ex: si `breakdown` dit
   "effondrement des systèmes de santé", l'évolution d'un nouveau signal
   santé doit aller dans ce sens, pas le contraire).

3. **Vérifier les anti-collisions** via `registre_evenements.md` :
   - Pas de nom d'`evenement_cle` identique ou quasi-identique à un
     existant
   - Pas de date qui contredit un événement déjà établi pour ce scénario
   - **Réutiliser intelligemment** la géographie/factions déjà établies
     quand pertinent (cf. lore ci-dessous) plutôt que d'en inventer
     systématiquement de nouvelles — ça renforce la cohérence du monde

4. **Rédiger le bloc YAML** (6 scénarios × signal), au format calibré.

5. **Insérer** dans la fiche `.md`, section 12, à l'intérieur du bloc
   ```yaml / signal_to_state existant (ajouter de nouvelles entrées
   `- signal: ...` après les existantes, avant le ``` final).

6. **Renommer si besoin** : si le nom du signal en section 7 contient des
   accents/caractères spéciaux, utiliser une version sans accent comme
   identifiant `signal:` en section 12 (cohérence avec les identifiants
   existants type `emergence_pathogenes_nouveaux`).

7. **Régénérer `registre_evenements.md`** (script ci-dessous) pour
   inclure les nouvelles entrées — à donner au chat suivant.

8. **Optionnel** : si l'environnement le permet, lancer `validate.py`
   pour confirmer 0 erreur (le YAML doit rester syntaxiquement valide).

---

## Script de régénération du registre

```python
from loader import load_all_variables, VALID_VARS

all_vars = load_all_variables()
pilots = ['geopolitique_conflits', 'energie_ressources_critiques',
          'organisation_territoires', 'climat_environnement_global',
          'systemes_productifs_travail']
SCENARIOS = ['breakdown', 'fortress_world', 'new_sustainability',
             'eco_communalism', 'policy_reform', 'reference']

rows_by_scenario = {s: [] for s in SCENARIOS}
for var_slug in VALID_VARS:
    var = all_vars[var_slug]
    for signal_name, scenarios in var.get('signal_to_state', {}).items():
        for scen, data in scenarios.items():
            date_bascule = data.get('date_bascule', '')
            try:
                date_debut = int(date_bascule.split('-')[0])
            except Exception:
                date_debut = 9999
            rows_by_scenario[scen].append({
                'variable': var_slug,
                'pilote': var_slug in pilots,
                'signal': signal_name,
                'date_bascule': date_bascule,
                'date_debut': date_debut,
                'evenement_cle': data.get('evenement_cle', ''),
            })

# ... puis génération markdown triée par date_debut, par scénario
# (voir registre_evenements.md pour le format exact attendu)
```

---

## Lore établi à réutiliser (cohérence inter-variables)

**Événements custom canoniques** (existent indépendamment de
`signal_to_state`, font partie du monde `breakdown`) :
- L'Attentat des Neuf Nœuds — Le Jour Sans Signal (2040)
- Victoire Fantôme du Parti Commun (2055)
- L'Arrestation de Van Derburgh par la Milice de Detroit-Sud (2078)

**Lieux/géographie récurrents** :
- Detroit-Sud (territoire fragmenté, milice locale — `breakdown`)
- Lagos-Est, Lagos-Mumbai-Jakarta (mégapoles sous tension — `breakdown`)
- Carthage-Nord (utilisé dans un article test — `breakdown`)

**Organisations/factions par scénario** (à réutiliser si pertinent) :
- `breakdown` : Alliance Pacifique, milices locales (Detroit-Sud)
- `fortress_world` : Bloc Atlantique, Bloc Sibérien, ANBA, Chambre de
  Sécurité Territoriale
- `new_sustainability` : Réseau Mondial de Biosurveillance (2038),
  Réseau Mondial de Médecine Prédictive (2044)
- `eco_communalism` : maisons de santé communautaires, Réseau des
  Assemblées Bioterritoriales, Les Gardiens du Territoire

**Entités canoniques** (archétype/instance, utilisées dans les articles) :
`conseil_regulation_algorithmique`, `nexcore` (Les Fragments NexCore),
`le_temoin` (Le Signal / Vera Solano / Kofi Asante-Mensah / etc. selon
scénario), `coalition_vivant`, `assemblee_territoires`. Évoquées dans
les `evenement_cle` uniquement si ça a du sens — ne pas forcer.

---

## Fichiers à fournir au nouveau chat

1. Ce brief
2. `registre_evenements.md` à jour
3. La (les) fiche(s) variable(s) `.md` à traiter (1-3 par chat)

---

## État d'avancement

| Variable | Pilote | Statut |
|---|---|---|
| sante_biotechnologies | non | ✅ fait (6 signaux : 2 existants + 4 nouveaux) |
| systeme_economique_redistribution | non | ⏳ à faire (section 7 vide — reconstruire) |
| gouvernance_institutions | non | ⏳ à faire |
| valeurs_culture_tempo_sociale | non | ⏳ à faire |
| frontieres_du_systeme | non | ⏳ à faire |
| technologie_information | non | ⏳ à faire |
| demographie_mobilite_humaine | non | ⏳ à faire |
| geopolitique_conflits | oui | ⏳ à faire |
| energie_ressources_critiques | oui | ⏳ à faire |
| organisation_territoires | oui | ⏳ à faire |
| climat_environnement_global | oui | ⏳ à faire |
| systemes_productifs_travail | oui | ⏳ à faire |
