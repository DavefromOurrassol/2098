---
type: documentation
titre: Conception — Point 9 (localisation) et filtrage géographique du prompt
date_creation: 2026-06-21
statut: conception validée, RIEN codé
---

# Point 9 — Champ `localisation` + filtrage géographique du prompt

Conception complète, issue du handoff du 20 juin (schéma de base) et approfondie en session du 21 juin (déclencheurs, conflits, filtrage par échelle). Rien n'est codé à ce stade — ce document sert de référence pour ne pas reperdre cette conception comme cela a failli arriver avec le handoff du 20 juin.

---

## 1. Schéma du champ `localisation`

À ajouter sur les instances et event_instances :

```yaml
localisation:
  zone: slug_zone_existante     # DOIT référencer un slug réel de geographie/{scenario}.md
                                  # — validé mécaniquement, jamais inventé
  lieu: texte_libre              # ex: "São Paulo" — reste du texte libre assumé
                                  # (un lieu réel peut survivre même si le pays qui
                                  # le gouvernait a disparu dans ce scénario)
  type_lieu: ville | region | infrastructure | site_strategique
```

## 2. Périmètre d'extraction initial

- **119 fiches riches seulement** : 95 instances avec contenu narratif réel + 24 event_instances (toutes riches, 0 placeholder).
- **PAS les 426 fiches `officialise_minimal`** (placeholders "à développer en phase 2") — celles-ci recevront `localisation` plus tard, directement au moment de leur enrichissement narratif phase 2 (point 12), pas via un script séparé après coup.

## 3. Trois issues possibles par fiche, aucune forcée

1. Lieu précis trouvé dans le texte → extrait.
2. Pas de lieu pertinent et c'est normal (entité transnationale "sans ancrage local fort", ex. l'ITA) → champ laissé vide, assumé.
3. Ambigu → signalé pour review manuelle, **jamais deviné silencieusement**.

## 4. Déclencheurs de l'enrichissement organique (zones manquantes)

Trois scripts produisent du texte narratif neuf susceptible de citer un lieu inédit, absent de `geographie/{scenario}.md` :

1. **`create_entities_and_instances.py`** (mode `custom` ET `auto`) — chaque nouvelle instance créée.
2. **`inject_custom_events.py`** — chaque nouvelle instance d'événement créée.
3. **`inject_custom_signals.py`** — chaque nouvel `evenement_cle` ajouté dans la section 12 (`Trajectoire des signaux 2025 → 2098`) d'une fiche `variables/{slug}.md`. Confirmé sur le vault réel : ces `evenement_cle` citent déjà des lieux précis (ex. *"guerre des minerais d'Afrique centrale 2051"*, *"Traité de Nairobi sur les minerais stratégiques 2042"*).

`inject_custom_signals.py` avait été initialement écarté à tort en cours de session — son rôle de déclencheur a été identifié et confirmé après vérification directe du vault.

## 5. Enrichissement organique — mécanisme acté

**Principes déjà actés (handoff du 20 juin)** :
- (a) jamais d'ajout automatique à la bible géographique.
- (b) l'instance reste bloquée (rien créé) tant que la nouvelle zone proposée n'a pas été validée manuellement.

**Mécanisme concret, acté en session du 21 juin** :

1. **File d'attente persistante** : `geographie_custom/zones_proposees.yaml` (même pattern que `entites_custom/queue.yaml`). Une entrée par proposition : `{slug_propose, nom, scenario, lieu_source, instance_source, justification, statut}`.

2. **Comportement batch** : un blocage sur une entité **ne stoppe pas tout le batch** — résilience cohérente avec `create_entities_and_instances.py` (continue avec les entités/scénarios suivants). L'entité bloquante est signalée en fin de run, pas un arrêt complet.

3. **Détection de conflit AVANT mise en file** (ajout du 21 juin, le handoff ne le couvrait pas) : avant d'ajouter une proposition à la queue, comparaison mécanique contre (a) toutes les zones déjà existantes du même scénario et (b) les autres propositions déjà en attente. En cas de risque de recoupement (doublon conceptuel, chevauchement géographique, contradiction de statut), la proposition est marquée `statut: conflit_potentiel` avec la zone suspectée affichée en regard — pas un simple rejet silencieux.

4. **Script de review séparé**, déclenché à la demande (`review_zones_proposees.py`, pas encore nommé/codé) : affiche chaque proposition une par une avec son contexte narratif ; pour les cas `conflit_potentiel`, affiche la comparaison côte à côte (zone existante vs proposition) ; décision interactive au clavier (accepter / rejeter / fusionner avec l'existante / modifier le nom). **Jamais automatique.**

5. **Interface envisagée pour le cas normal (pas de conflit)**, en mode custom CLI : afficher les zones/lieux déjà disponibles de la bible du scénario concerné et proposer un choix interactif au clavier plutôt que de laisser retaper un slug de mémoire.

**Reste à trancher** (pas urgent, pas bloquant pour démarrer l'extraction des 119 fiches) : format exact détaillé de la file d'attente, processus concret pas-à-pas de la review.

---

## 6. Filtrage géographique du prompt — conception du 21 juin

### Le problème de départ

`build_geographie_context` (codée le 21 juin, point 11) injecte aujourd'hui **toutes** les zones du scénario, tous niveaux confondus, sans filtrage — choix assumé à l'époque pour observer l'effet sur de vrais articles avant d'optimiser. Question posée : le champ `échelle` des fiches thématiques (`global`/`national`/`local`) pourrait-il piloter un filtrage par niveau de zone ?

### Pourquoi un mapping echelle→niveau simple a été rejeté

Démontré par des contre-exemples concrets, vérifiés sur le vault réel :
- **`meteo` (`echelle: local`)** : un mapping "local → tous niveaux" ajoute du bruit inutile (zones niveau 1 = blocs continentaux, sans usage pour un bulletin météo).
- **`sports` (`echelle: global`)** : un mapping "global → niveau 1 seulement" exclurait à tort une ville hôte précise (niveau 2), pourtant l'info la plus utile pour un article sportif.
- **`politique` (`echelle: national`)** : une seule thématique couvre aussi bien une élection municipale (besoin de niveau 2-3) qu'une élection de l'Union européenne (besoin de niveau 1) — l'échelle figée par thématique ne peut PAS distinguer ces deux cas, puisqu'elle est définie une fois pour toute la rubrique, pas par article.
- **Entité supranationale avec impact local** (ex. ARIA-Bloc causant un fait divers dans une ville précise) : l'article a besoin des DEUX niveaux simultanément, montrant qu'un filtrage par niveau unique est structurellement insuffisant.

**Conclusion** : l'échelle de la thématique est un mauvais signal pour piloter QUELLES zones injecter — elle décrit une tendance générale de la rubrique, pas le contenu réel de l'article en cours de génération.

### Le vrai signal : la chaîne de parenté des zones réellement liées à l'article

Mécanisme retenu, qui réutilise la hiérarchie `parent` déjà construite par `enrich_geographie_recursive.py` (et déjà exploitée par `compute_level` pour calculer les niveaux) :

1. Pour chaque instance/événement sélectionné dans l'article (`snapshot["filtered_instances"]`), lire `localisation.zone`.
2. Inclure cette zone **telle quelle dans le prompt, systématiquement**, quel que soit son niveau.
3. Remonter sa chaîne de `parent` pour ajouter le contexte géographique plus large autour d'elle.

### Rôle réinventé du champ `échelle` : un plafond optionnel sur la remontée, pas une instruction textuelle isolée

- **`echelle: null`** sur la fiche thématique → remontée complète jusqu'au sommet de la hiérarchie (niveau 1). Le système déduit naturellement le bon niveau de contexte à partir du contenu réel de l'article.
- **`echelle: valeur_fixe`** (ex. `nationale`) → la remontée de la chaîne de `parent` **s'arrête** au niveau correspondant à cette valeur. On n'ajoute pas de contexte plus large que ce plafond.
- **Cas limite tranché** : le plafond ne s'applique JAMAIS pour exclure ou tronquer l'instance vedette elle-même — uniquement pour limiter l'ajout de contexte parent autour d'elle. Une institution de niveau 1 mentionnée dans un article à plafond "national" reste incluse telle quelle ; simplement, on ne va pas chercher encore plus large qu'elle (ce qui n'existerait probablement pas de toute façon, niveau 1 étant le sommet).

### Vocabulaire à harmoniser

Le champ `échelle` des fiches thématiques (`global`/`national`/`local`, 3 valeurs) doit être élargi pour correspondre au vocabulaire déjà utilisé et déjà éprouvé sur 500+ fiches instances via le champ `zone_geographique` :

```
locale | urbaine | nationale | régionale | continentale | globale
```

(`orbital` a aussi été observé sur au moins une fiche — cas exotique à examiner séparément, pas forcément à intégrer dans le vocabulaire standard.)

**Ce changement n'a pas encore été appliqué aux fiches thématiques — à faire au moment de coder le filtrage, pas avant** (pas d'intérêt à le faire avant que le mécanisme qui le consomme existe).

### Ce qui ne change pas

L'usage actuel d'`échelle` dans `build_journalistic_brief` (ligne `**Échelle** : {} | **Temporalité** : {}` du prompt, cadrage stylistique pour Claude) reste inchangé et continue en parallèle — le nouveau rôle de plafond géographique s'ajoute, ne remplace pas l'usage existant.

---

## 7. Dépendances et ordre

- **`localisation` doit être codé avant le filtrage géographique** décrit en section 6 — sans le champ, il n'y a rien à utiliser pour remonter une chaîne de parenté.
- **`localisation` doit aussi être codé avant le chantier `restructure`** (scinder/fusionner/reparenter/renommer des zones) — c'est lui qui crée la vraie dépendance externe (`instance.localisation.zone → geographie.slug`) qu'un `--restructure` fiable doit scanner avant d'agir.
- Le filtrage géographique (section 6) et `restructure` peuvent ensuite être menés en parallèle ou dans l'ordre qui convient, les deux ne dépendant que de `localisation`, pas l'un de l'autre.
