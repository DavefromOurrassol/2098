# Handoff — session du 18-19 août 2026

*Session menée via chat avec Claude (aucun accès direct GUI/terminal côté
Claude), David exécutant les commandes/scripts sur son vault et
rapportant les résultats, plus plusieurs lancements réels depuis le
terminal/GUI (dry-run puis écriture réelle) au fil de la session.*

## 0. Point de départ — reprise du point laissé ouvert le 17 août

Backlog Partie 1, point 8 : investiguer le slug de zone `istanbul`
inconnu sur `gelecek_meclisi_policy_reform` (`policy_reform`) —
`[VALIDATION ÉCHOUÉE] slug zone inconnu : 'istanbul'`.

## 1. Diagnostic Istanbul — trois fausses pistes avant la bonne

- **Piste 1** : chercher un slug `istanbul` existant sous un autre nom
  dans `geographie/policy_reform.md`. Négatif — aucune zone de ce nom,
  ni candidat plausible (`espace_eurasiatique`,
  `union_technocratique_eurasiatique_territoire` — cette dernière
  exclue, `origine_reelle` = Russie/Chine/Kazakhstan, sans rapport).
- **Piste 2** : `zones_pays.json` confirme qu'aucune zone `istanbul`
  n'existe nulle part, même en `reference` (Turquie → `zone_moyen_
  orient_golfe` en `policy_reform`, `turquie_eurasie_moyen_orient` en
  `reference`).
- **Piste 3, la bonne** : Istanbul existe comme simple
  `lieu_emblematique` de `turquie_eurasie_moyen_orient` dans
  `geographie/reference.md` ("Istanbul, siège de la Ligue des
  Détroits") — jamais une zone à part entière. Le LLM avait halluciné
  un slug de zone depuis ce nom de ville, cité dans le texte narratif
  de l'instance (siège du Gelecek Meclisi décrit "à Istanbul"), sans
  passer par une résolution réelle pays/ville → zone.

## 2. `enrich_geographie_recursive.py` testé, insuffisant

Outil existant le plus proche (scan complet du corpus par scénario,
mécanisme `promu_depuis` pour transformer un `lieu_emblematique` en
vraie sous-zone). Lancé en `--dry-run --scenario reference` :
- 1er essai : échec `503 unreachable_backend` côté Mistral (aléa
  infrastructure, pas lié au travail en cours) — résolu par simple
  relance.
- 2e essai : réussi, plusieurs sous-zones promues avec succès (Nairobi,
  Kinshasa, Tampere, Tbilissi, Mourmansk, Singapour-Est...), mais
  **Istanbul non retenue** malgré sa présence en `lieu_emblematique` —
  arbitrage LLM non déterministe sur un corpus de 62 zones/174
  instances/370k caractères, pas de garantie de sélection d'un lieu
  précis. Écrit quand même (les autres sous-zones proposées restent
  utiles indépendamment d'Istanbul).

Conclusion : besoin d'un outil ciblé, pas d'un scan global.

## 3. Conception et livraison de `promote_ville.py`

Nouveau script, conçu par itérations successives avec David sur les
points de design suivants, tous tranchés en session :
- Résolution pays réel : LLM automatique + confirmation avant écriture
  (pas de saisie manuelle obligatoire).
- Portée par défaut : `--all` (6 scénarios), restreignable via
  `--scenarios`.
- Détection en 3 cas avant toute création (voir doctrine détaillée dans
  `USER_MANUAL_COMPLET.md`) : zone déjà exploitable (rien à faire) /
  `lieu_emblematique` non exploitable (promotion forcée par défaut,
  point ajouté après une question de David sur l'angle mort d'une
  fausse confirmation "ça répond déjà au besoin") / mention narrative
  seule ou rien (création directe).
- Rattachement au parent le plus précis toujours tenté (zones_pays.json
  puis arbitrage LLM entre zone-pays niveau 1 et sous-zones existantes).
- Réutilisation intégrale des fonctions de validation d'`enrich_
  geographie_recursive.py`, zéro duplication de logique.

**Deux bugs trouvés et corrigés en dry-run réel** :
1. `type_entite: 'ville'` proposé par le LLM, invalide (`TYPE_ENTITE_
   REELLE` n'accepte pas cette valeur) — corrigé par prompt + filet de
   sécurité mécanique (normalisation automatique vers `"autre"`).
2. Log excessif en dry-run — `write_geographie_file()` réutilisée
   imprime tout le fichier reconstruit (63 zones affichées pour un seul
   ajout) — contourné côté `promote_ville.py` sans toucher à la
   fonction partagée, plus un flag `--quiet` masquant les lignes `[llm]`
   de `llm_client.py`.

## 4. Exécution réelle et clôture du chantier Istanbul

- `promote_ville.py --ville Istanbul --pays Turquie --slug istanbul
  --scenarios policy_reform,reference` lancé en réel (après dry-run
  validé) : zone créée sur les deux scénarios, dédoublonnage réussi sur
  `reference` (`lieu_emblematique` retiré de `turquie_eurasie_moyen_
  orient` au moment de la promotion).
- Investigation complémentaire : le champ `localisation` n'avait en
  réalité **jamais existé** sur `gelecek_meclisi_policy_reform.md` (pas
  un champ mal renseigné, un champ absent — l'erreur d'origine venait de
  l'étape d'extraction, jamais persistée dans la fiche).
- `extract_localisation.py --scenario policy_reform --slug gelecek_
  meclisi_policy_reform` relancé après création de la zone : extraction
  réussie, `zone: istanbul` correctement résolu.
- `validate.py` final : **0 erreur, 0 avertissement** — première fois
  depuis le début de cette investigation.

## 5. Question ouverte — intégration GUI de `promote_ville.py`

David a demandé si le script serait intégré au GUI. Diagnostic :
non-trivial contrairement à `audit_instances_manquantes.py` (17 août,
read-only) — `promote_ville.py` utilise `input()` pour les
confirmations interactives (incompatible tel quel avec une interface
web) et écrit réellement dans `geographie/{scenario}.md`. Trois options
esquissées (rester CLI / intégration complète redécoupée en étapes /
intégration légère avec `--auto-promote`) — **David a choisi de laisser
en chantier futur à scoper**, pas de décision définitive. Documenté en
Partie 1 du backlog.

## 6. Nettoyage de la Partie 2 du backlog (points mineurs)

David a demandé une revue point par point plutôt qu'une simple
condensation. Tri proposé et confirmé :
- **Supprimés** (reconfirmés plusieurs fois sans jamais mener à une
  action, aucune condition de réouverture identifiée) :
  `coverage_proposals_reference.yaml` sans `.applied`, route dormante
  `/api/carte/appliquer_zone_topdown_suspecte`, champ `type` des zones
  géographiques.
- **Conservés** (condition de déclenchement claire) : bloc `simulation`
  sur les fiches variables, `--min-shingle` fixé en dur, cas d'échec LLM
  confusion slug zone/instance, `_index.md` écrasé à chaque run.
- **Retiré pour raison inverse** (pas obsolète — traité) :
  `constrained_variables`, voir point suivant.

## 7. `constrained_variables` — activation dans le prompt (Option A)

Repéré en nettoyant la Partie 2 : champ rempli sur les 6 scénarios
depuis les fondations du projet (3 variables distinctes par scénario),
jamais consommé par `prompt_builder.py`. David a précisé l'intention
d'origine — une variable "contrainte" n'est pas une valeur figée, c'est
une limite structurelle sur l'espace des trajectoires accessibles du
scénario (distinction moteur/contrainte/conséquence).

Deux options envisagées, Option A retenue (direction de la borne
déduite du contexte narratif déjà transmis, plus simple que l'encodage
explicite de l'Option B). Câblage dans `build_variables_context()`
(`prompt_builder.py`) : `constrained_variables` ajouté à l'ordre de
priorité, nouveau tag `[VARIABLE CONTRAINTE]`, nouvelle consigne dédiée
reprenant fidèlement la distinction de David.

**Validé sur 2 générations réelles** (`fortress_world`, contrainte
`demographie_mobilite_humaine`, thématiques `religion_spiritualite` puis
`actualites_a_la_une`) : tag et consigne bien injectés, aucune
contradiction de la borne dans les deux articles, aucune régression sur
la couverture des variables pilotes. **Réserve explicite** : les deux
thématiques testées n'obligeaient pas le LLM à se prononcer activement
sur la mobilité humaine — validation positive mais peu discriminante.
David a jugé cela suffisant pour la prod (test plus exigeant resté non
fait, à envisager seulement si un doute apparaît sur un futur batch
réel).

## 8. Découverte tardive — bloc `simulation` des fiches variables (P22)

En revérifiant le point 4 du tri Partie 2 ("bloc `simulation`,
probablement du monitoring interne") avant de le laisser tel quel,
grep exhaustif (`["simulation"]`/`.get("simulation"`) confirmant qu'il
est bien chargé (`loader.py`) mais jamais relu nulle part en aval —
contrairement à `constrained_variables`, ce n'était donc PAS un trou
caché derrière un grep trop étroit, verdict inverse cette fois.

David a alors précisé l'intention d'origine, en deux temps : ce bloc
décrit des propriétés intrinsèques de la dynamique d'une variable
(volatilité, prévisibilité, incertitude, risque de bascule, criticité
systémique), indépendantes du scénario — pas un état comme
`variable_states`, mais un paramètre du moteur prospectif lui-même,
destiné à différencier comment deux variables réagissent différemment
à une même force d'influence dans la matrice. Question non tranchée
posée explicitement par David avant tout code : ces valeurs qualitatives
(`high`/`medium`/`low`) doivent-elles rester descriptives (aide à la
conception humaine) ou devenir opérationnelles (réellement utilisées par
`snapshot.py` pour moduler des calculs) ? Dans ce dernier cas, une vraie
spécification mathématique serait nécessaire avant tout câblage — plus
lourd que le simple ajout de consigne fait pour `constrained_variables`.

**Documenté comme nouveau chantier (P22, Partie 1, point 9)**, scopé
mais non codé — nécessite une session de conception dédiée. Aucun
fichier touché ce soir sur ce point, contrairement aux autres chantiers
de la session.

## 9. Fichiers livrés cette session

- `promote_ville.py` (nouveau, à placer dans `generator/`).
- `prompt_builder.py` (3 modifications localisées dans
  `build_variables_context()` — ajout `constrained_variables`,
  nouveau tag, nouvelle consigne).

## 10. Point de reprise suggéré pour la prochaine session

Rien d'urgent laissé en suspens par cette session. Chantiers Partie 1
inchangés (validation retry longueur, P17, Bug #27, renommage YAML
génériques, troncatures JSON) — tous en attente sur décision explicite
de David, comme au 17 août. Deux nouveaux points Partie 1 : scoper
l'intégration GUI de `promote_ville.py` si le besoin s'en fait sentir,
et surtout P22 (bloc `simulation`) qui mérite une vraie session de
conception dédiée — trancher métadonnée descriptive vs opérationnelle
avant toute tentative de câblage.
