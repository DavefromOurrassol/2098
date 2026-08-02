# Approche consolidée — Zoning et géographie cohérente avec les scénarios
*Rédigé le 13 juillet 2026 — synthèse de session (vault Ourrassol + 7 sources externes). Point de départ pour construire P24 (générateur top-down) et affiner P22 (garde-fou).*

---

## 1. Le problème, précisément posé

Le pipeline géographique actuel (`generator/`) fonctionne en **trois passes indépendantes**, chacune avec sa propre logique :

| Passe | Script | Logique | D'où vient l'info |
|---|---|---|---|
| 1 | `build_geographie_monde.py` | **Bottom-up** — repère les zones mentionnées dans le narratif déjà écrit (instances, événements), fusionne les variantes | Corpus narratif du scénario |
| 2 | `enrich_geographie_recursive.py` | **Bottom-up, additif** — ajoute des sous-zones (niveau 2/3) à partir du même corpus, sans jamais toucher aux zones existantes | Même corpus narratif |
| 3 | `complete_geographie_coverage.py` | **Top-down, mais naïf** — pour chaque pays réel sans zone, demande au LLM "cette zone existante convient-elle ?" en ne montrant que les zones N1 + leur `origine_reelle` | Liste des ~200 pays réels, **sans revalidation contre le narratif ou la logique du scénario** |

**Le trou identifié cette session** : la passe 3 ne revalide jamais sa décision contre ce que les passes 1 et 2 savaient déjà (la description narrative précise d'une zone, sa logique systémique). Elle juge "ce pays ressemble-t-il assez à cette zone" sur un critère faible — d'où les 4 anomalies trouvées en testant P7 : Barcelone-Hub et Corridor ibérique énergétique absorbés dans `ameriques_reconfigurees` (aucun rapport géographique), Cracovie et le Bassin Pannonien absorbés dans `arc_eurasien_central` (axe Géorgie-Kazakhstan-Caspienne, sans lien avec l'Europe centrale).

**Le principe correcteur** : un rattachement ou une création de zone ne devrait jamais être jugé sur la seule ressemblance textuelle — il doit être validé contre **la logique spatiale propre au scénario**, qui existe déjà dans le vault mais n'est actuellement exploitée par aucune des 3 passes.

---

## 2. Ce que le vault sait déjà — et n'exploite pas encore

Chaque scénario a une fiche `scenarios/{scenario}.md` **structurée et quantifiée** (pas seulement narrative) : `dominant_variables`, `variable_states` (niveau/tendance des 12 variables), boucles de stabilisation/déstabilisation, `forces_dominantes`, section "Synthèse systémique" (résumé, logique système, interprétation, implications).

Chaque variable a une fiche `variables/{variable}.md` avec un bloc `states.{scenario}` par scénario — `state_logic`, `dominant_dynamics`, `coupling_intensity` avec les autres variables. **`organisation_territoires` est directement le patron de structuration spatiale attendu**, littéralement écrit, pour chacun des 6 scénarios :

| Scénario | `organisation_territoires.states.{scenario}.state_logic` |
|---|---|
| `reference` | *"Monde dominé par des mégapoles globales structurantes, avec une hiérarchie territoriale stable mais sous tension croissante entre concentration urbaine et périphéries en déclin."* |
| `policy_reform` | *"Rééquilibrage territorial progressif via politiques publiques, infrastructures distribuées et planification coordonnée des flux humains, énergétiques et économiques."* |
| `breakdown` | *"Désorganisation territoriale majeure avec effondrement de mégapoles, rupture des chaînes logistiques et fragmentation des espaces humains sous contrainte climatique, énergétique et géopolitique."* |
| `fortress_world` | *"Archipel territorial fragmenté en zones sécurisées fortement contrôlées, avec fort contraste entre espaces protégés et zones abandonnées ou instables."* |
| `eco_communalism` | *"Relocalisation territoriale forte avec densité modérée, circuits courts et réorganisation écologique des espaces humains."* |
| `new_sustainability` | *"Système territorial distribué optimisé par IA, combinant hubs urbains, réseaux intelligents et résilience locale avancée."* |

Deux autres variables très pertinentes pour le zoning, avec le même niveau de détail déjà écrit dans le vault : `geopolitique_conflits` (structure des blocs/tensions — directement liée à `relations.allies`/`relations.rivaux` des zones) et `frontieres_du_systeme` (pour les zones orbitales/spatiales, `zone_geographique: orbital`).

**Conclusion pratique** : construire un garde-fou ou un générateur qui ignore ces fiches reconstruirait à la main ce qui existe déjà. Elles doivent être la source de vérité citée dans tout prompt de génération ou de vérification de zone.

---

## 3. Grille de lecture par scénario — patron spatial + ancrage externe

Pour chaque scénario, le patron issu du vault est maintenant croisé avec les cadres externes lus cette session — deux ancrages indépendants qui se recoupent, ce qui renforce la fiabilité du patron plutôt que de le remettre en cause.

### `breakdown`
- **Vault** : effondrement des mégapoles, rupture logistique, fragmentation sous contrainte climatique/énergétique/géopolitique.
- **Global Scenario Group (1990s)** : archétype "Breakdown" — conflits et crises en spirale, institutions qui s'effondrent, absence de réponse coordonnée.
- **Global Trends 2040 (CIA/NIC, 2021)** : proche de "Separate Silos" en version dégradée — blocs auto-suffisants centrés sur les grandes puissances, chaînes logistiques réorientées, pays vulnérables pris entre deux feux.
- **Patron à respecter pour toute nouvelle zone** : fragmentation en blocs rivaux (`Bloc IV`/`Bloc IX` déjà dans le vault), zones no-go entre blocs, aucune institution supranationale stable. Une zone `breakdown` ne devrait jamais porter une logique de gouvernance centralisée forte.

### `fortress_world`
- **Vault** : archipel de zones sécurisées, contraste fort entre espaces protégés et abandonnés ; blocs fermés militarisés.
- **Global Scenario Group** : archétype "Fortress World" — une "Alliance for Global Salvation" (coalition militaro-institutionnelle) impose l'ordre, enclaves protégées **dans les pays riches ET les pays pauvres** ("bubbles of privilege amidst oceans of misery"), pas un simple clivage Nord/Sud.
- **Global Trends 2040** : "Separate Silos" — blocs centrés sur quelques puissances, contrôle strict des flux d'information et de ressources.
- **Patron à respecter** : une nouvelle zone `fortress_world` doit être soit une enclave protégée (n'importe où dans le monde, y compris en zone historiquement pauvre — cf. Bloc Johannesburg déjà dans le vault), soit un "hors-forteresse" explicitement dégradé. Éviter de générer des zones "neutres"/intermédiaires qui n'incarnent ni l'un ni l'autre.

### `reference`
- **Vault** : mégapoles globales dominantes, hiérarchie territoriale stable mais tendue, polarisation centre/périphérie.
- **Global Scenario Group** : proche de "Market Forces" — logique de marché auto-régulatrice, pas de rupture de paradigme.
- **Global Trends 2040** : proche de "A World Adrift" — système sans direction claire, pas de recomposition cohérente, problèmes non traités mais pas d'effondrement non plus.
- **Patron à respecter** : zones organisées autour de hubs urbains dominants avec périphéries en déclin, pas de rupture radicale — c'est le scénario le plus "conservateur" des 6, une nouvelle zone ne devrait pas y introduire une innovation institutionnelle ou sociale trop marquée (ça appartiendrait plutôt à `policy_reform` ou `new_sustainability`).

### `policy_reform`
- **Vault** : rééquilibrage territorial progressif par les politiques publiques, infrastructures distribuées, planification coordonnée.
- **Global Scenario Group** : archétype "Policy Reform" — action gouvernementale coordonnée et globale pour la réduction de la pauvreté et la soutenabilité (filiation Keynes/Brundtland).
- **Global Trends 2040** : proche de "Competitive Coexistence" — rivalité gérée (ex. USA-Chine), coopération technique qui rend les problèmes globaux "gérables" à moyen terme.
- **Patron à respecter** : institutions de régulation régionales/internationales actives mais pas hégémoniques, montée de villes secondaires plutôt que mégapoles uniques, coopération réelle mais non totale entre blocs rivaux.

### `eco_communalism`
- **Vault** : relocalisation forte, densité modérée, circuits courts, réorganisation écologique.
- **Global Scenario Group** : archétype "Eco-communalism" — bio-régionalisme, démocratie directe, autarcie économique (filiation Morris/Gandhi/Schumacher, "small is beautiful").
- **Patron à respecter** : petites communautés autonomes, désurbanisation volontaire, pas de grande institution centralisée. C'est le scénario le plus éloigné d'une logique de "mégazone" — une nouvelle zone `eco_communalism` de grande taille et centralisée serait probablement incohérente avec le patron.

### `new_sustainability`
- **Vault** : système territorial distribué optimisé par IA, hubs urbains + réseaux intelligents + résilience locale.
- **Global Scenario Group** : archétype "New Sustainability Paradigm" (filiation Mill) — pas un repli localiste comme l'eco-communalisme, mais une transformation de civilisation globale qui reste connectée, solidaire, hybridée.
- **Global Trends 2040** : proche de "Tragedy and Mobilization" — coalition UE+Chine, ONG et institutions multilatérales revitalisées, transition bas-carbone après une catastrophe climatique/alimentaire, transferts d'aide des pays riches vers les pays pauvres.
- **Patron à respecter** : institutions supranationales actives (déjà incarnées par l'AGRB-ONU, l'AIER dans le vault) + réseau distribué de hubs plutôt qu'un centre unique. **Point de vigilance narratif** (tiré de l'article Futuribles sur les entreprises "qui réussissent") : une institution supranationale ne s'implante jamais identiquement partout — elle se fait réinterpréter localement. Une nouvelle zone `new_sustainability` ne devrait donc pas être une simple copie de l'institution mère, mais montrer une friction ou une adaptation locale spécifique.

---

## 4. Le garde-fou de cohérence (P22) — mécanique concrète proposée

**Signal principal : `origine_reelle`**, déjà obligatoire et validé structurellement par `validate_zone()` dans `enrich_geographie_recursive.py`. Une entrée `type_entite: "ville"/"region_administrative"` de l'enfant sans aucune correspondance dans les entrées `pays` de la chaîne de parenté est un signal fort — c'était le cas des 4 anomalies trouvées.

**Ce qui manque pour rendre ce signal actionnable automatiquement** : une ville/subdivision ne porte pas de pointeur explicite vers son pays. Deux options, non tranchées :
1. Petite table statique ville→pays (rapide, gratuit, couverture limitée)
2. Passe de vérification LLM dédiée en lot (couverture complète, coût API)

**Second signal, nouveau, issu de cette synthèse** : cohérence de *patron spatial*, pas seulement géographique. Une zone peut être dans la bonne région réelle mais incohérente avec la logique du scénario (ex. une "mégapole dominante centralisée" dans `eco_communalism`, ou une institution supranationale douce dans `breakdown`). Ce contrôle nécessite de comparer la `description`/`type` de la zone au `state_logic` d'`organisation_territoires` pour ce scénario — plus qualitatif que le premier signal, donc à garder en avertissement, jamais en blocage automatique.

**Non-négociable, confirmé par le test du 13 juillet** : rester un **avertissement actionnable** (comme le bouton "↗️ rattacher" de l'étape 3 de P7), jamais un blocage dur — le taux de faux positifs d'une première heuristique mots-clés (5 sur 9 lors du test) montre qu'un contrôle automatique strict serait risqué sans un signal aussi fiable qu'`origine_reelle`.

---

## 5. Le générateur top-down (nouveau chantier, pas encore scopé en détail)

**Principe** : pour une macro-région réelle mal couverte dans un scénario donné, générer un jeu de zones qui **incarne le patron spatial du scénario pour cette région précise**, plutôt que "des zones plausibles en général".

**Sources du prompt, toutes déjà écrites dans le vault** :
1. `scenarios/{scenario}.md` — synthèse systémique globale
2. `variables/organisation_territoires.md → states.{scenario}` — le patron spatial directement applicable
3. `variables/geopolitique_conflits.md → states.{scenario}` — structure des blocs/tensions, pour peupler `relations.allies`/`relations.rivaux` de façon cohérente dès la création
4. Éventuellement d'autres variables selon le contexte régional (`energie_ressources_critiques` pour une région riche en ressources, `frontieres_du_systeme` si zone orbitale)

**Consigne centrale du prompt** : ne pas générer une zone plausible dans l'absolu, mais une zone qui répond explicitement à "comment le patron spatial de ce scénario s'est-il concrétisé dans *cette* région réelle, avec quelle friction ou réinterprétation locale par rapport à la logique globale du scénario" (leçon de l'article Futuribles/d'Iribarne — l'universel ne s'implante jamais identiquement).

**Sortie** : passe par le garde-fou (§4) avant écriture, exactement comme une création manuelle via l'option "créer une nouvelle zone niveau 1" de P7 étape 2 (déjà construite) — le générateur top-down pourrait d'ailleurs **pré-remplir ce même formulaire** plutôt que d'être un chemin d'écriture séparé.

---

## 6. Séquencement recommandé pour la construction

| Étape | Contenu | Ampleur | Dépendances |
|---|---|---|---|
| **A** | Documenter le patron spatial des 6 scénarios (tableau §3) dans un format exploitable par le code — probablement une constante Python dans `prompt_builder.py` ou un fichier de référence dédié | Petite — le contenu existe déjà, juste à formaliser | Aucune |
| **B** | Garde-fou `origine_reelle` (P22) — trancher table statique vs passe LLM, intégrer à `resolve_parents_and_levels()` | Moyenne | Étape A utile mais pas bloquante |
| **C** | Générateur top-down proprement dit — nouveau script ou extension de `complete_geographie_coverage.py`, branché sur le formulaire "créer une nouvelle zone" de P7 | Grosse — le vrai chantier | Étapes A et B |

Étape B est la plus urgente (empêche activement de nouvelles erreurs comme les 4 trouvées). Étape C est la plus structurante mais peut attendre.

---

## 7. Sources externes consultées cette session (pour référence future)

| Source | Nature | Apport principal |
|---|---|---|
| Raskin et al., *Great Transition* (Global Scenario Group, 2002) | Rapport de prospective, texte intégral | Origine du cadre à 6 familles de scénarios ; archétypes philosophiques (Table 2) ; récit détaillé Fortress World/Policy Reform |
| National Intelligence Council, *Global Trends 2040* (2021) | Rapport gouvernemental US, domaine public | 5 scénarios 2040 recoupant les 6 d'Ourrassol ; 4 forces structurelles proches des 12 variables systémiques |
| Meadows et al., *The Limits to Growth* (Club de Rome, 1972) | Rapport scientifique, accès libre (Dartmouth) | Boucles de rétroaction population/capital/pollution/ressources — grounding quantitatif pour `energie_ressources_critiques`, `climat_environnement_global` |
| Narberhaus et al., *Réussir la grande transition* (SmartCSOs, 2011) | Rapport d'ONG | Cadre macro/méso/micro (paysage/régimes/niches) — transposable à la tension régime dominant/niches dissidentes d'une zone |
| d'Iribarne, *Le tiers-monde qui réussit* (Futuribles, 2004) | Compte-rendu de table ronde | Une institution "universelle" se réinterprète toujours localement — friction à intégrer dans le prompt du générateur top-down |
| Godet, *Creating Futures* (2006) | Manuel de méthode | Analyse morphologique (MICMAC/MACTOR) — logique de combinaisons cohérentes de variables, applicable au garde-fou |
| Gaudin, thèse de doctorat (2008) + *2100, récit du prochain siècle* (extraits cités) | Thèse + récit narratif unique (pas de scénarios branchants) | Texture atmosphérique ponctuelle, moins directement actionnable — cadre des "quatre pôles" (matière/énergie/temps/vivant) en réserve |

---

*Fin du document — prêt à servir de base à la prochaine session pour scoper P24 en détail ou commencer la construction de l'étape A.*
