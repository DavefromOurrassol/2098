# FAQ — Ourrassol 2098

*Document vivant, distinct du backlog et du manuel : il rassemble les
questions de compréhension ("comment ça marche", "pourquoi c'est fait
comme ça") posées au fil des sessions — pas des bugs, pas des tâches,
juste des réponses à retrouver facilement plus tard sans re-fouiller le
code à chaque fois. Alimenté au fur et à mesure.*

---

## Pipeline de génération

### L'injection d'événements ou d'entités se fait-elle sur des zones déjà définies ?

**Non — c'est délibérément découplé en deux temps.**

**Au moment de l'injection** (`inject_custom_events.py`,
`create_entity.py`/`create_entities_and_instances.py`), le seul lien avec
la géographie est `zone_hint` — un **texte libre optionnel** (ex. "Sahel",
"côte atlantique marocaine"), simple indication narrative donnée au LLM
pour orienter l'ancrage géographique de ce qu'il génère. Ce n'est **ni une
contrainte, ni une référence à un slug de zone existant** — si `zone_hint`
est `null`, le LLM choisit librement.

**L'ancrage réel dans une zone du vault se fait après coup**, par un
passage dédié :
```
extract_localisation.py → review_localisation.py --auto-resolve → validate.py
```
`extract_localisation.py` relit les fiches déjà écrites (événements/
entités riches, hors `officialise_minimal`), déduit un lieu précis, et
**valide mécaniquement le slug de zone contre `geographie/{scenario}.md`**
— trois issues possibles : lieu trouvé → `localisation.zone` rempli ;
entité transnationale sans ancrage local → laissé vide, assumé ; ambigu →
`statut: review_manuelle`, jamais deviné au hasard.

Ce cycle post-injection s'enchaîne **automatiquement** en fin de run
d'`inject_custom_events.py` dès qu'au moins une entité/instance a été
créée.

**Conséquence pratique** : la génération de contenu n'est jamais bloquée
par l'état de la carte géographique — elle peut créer du contenu
narrativement situé n'importe où, y compris dans une région pas encore
cartographiée. C'est la passe de localisation, séparée et postérieure,
qui rattache ce contenu à une zone existante (ou laisse volontairement en
attente si ambigu).

*(2 août 2026)*

---

## GUI & Dashboard

### Quand un bug d'affichage du dashboard est corrigé, est-ce que ça répare aussi la donnée source ?

**Non, ce sont deux choses différentes — un correctif de code ne répare
pas les fiches du vault.**

Exemple concret : le bug de l'entrée fantôme `: 1` dans la carte
INSTANCES. Le correctif (exclure `instance_template.md` du comptage)
change uniquement la façon dont le dashboard **affiche** les données —
il empêche le gabarit d'être compté comme une vraie instance. Mais si le
problème avait été une vraie fiche avec un champ mal rempli (hypothèse
initiale, avant qu'on trouve la vraie cause), corriger le code du
dashboard n'aurait pas rempli ce champ dans la fiche elle-même : la
donnée serait restée incomplète, simplement mieux affichée (regroupée
sous "inconnu" plutôt qu'affichée comme une ligne vide).

**Distinction à garder en tête** : un bug d'affichage/agrégation se
corrige dans le code (`routes_dashboard.py`, `app.py`...) ; un problème de
donnée se corrige dans le vault lui-même (fiche `.md`, souvent via un
script dédié comme `check_type_entite_coherence.py --apply`). Les deux
peuvent coexister sur un même symptôme, et corriger l'un ne dispense pas
de vérifier l'autre.

*(2 août 2026)*

---

## Traçabilité & vérification

### Comment vérifier qu'une fiche a bien été traitée par `enrich_minimal.py` ?

**`enrich_minimal.py` laisse une trace permanente et datée dans le corps
de chaque fiche qu'il enrichit** — pas seulement dans le rapport
(`enrich_minimal_report.md`, qui n'est pas cumulatif d'une session à
l'autre).

Concrètement, `write_enriched_fiche()` ajoute une section `## Notes` en
fin de fiche avec la ligne :
```
Fiche enrichie depuis officialise_minimal le {date}.
```

C'est la preuve la plus fiable qu'une fiche est passée par ce script,
plus fiable que de se fier au champ `statut: officialise_enrichi` seul
(qui indique *que* c'est enrichi, pas *quand* ni *par quel run*). Utile
pour reconstituer un historique quand un handoff ne l'a pas noté : une
recherche
```bash
grep -rh "Fiche enrichie depuis officialise_minimal" instances/*.md | sort | uniq -c
```
donne à la fois le total de fiches traitées et la ou les dates exactes
des runs — c'est exactement comme ça qu'on a confirmé que les 426 fiches
`officialise_minimal` avaient déjà été traitées en un coup le 27 juin
2026, information qu'aucun backlog n'avait conservée.

*(2 août 2026)*

---
