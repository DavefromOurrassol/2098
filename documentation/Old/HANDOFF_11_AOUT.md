# HANDOFF — session du 11 août 2026 (à uploader dans le nouveau chat)

*Session courte et ciblée, en continuité directe de `HANDOFF_10_AOUT.md` :
David a commencé à valider le GUI dans un vrai navigateur (backlog Partie
1, point "Test navigateur des entrées GUI modifiées", ouvert depuis fin
juillet). Trois descriptifs jugés trop techniques ont été reformulés au
fil du test, un correctif de lisibilité appliqué à la sortie de
`trace_injection.py` suite à un exemple réel fourni par David, et 10
entrées `scripts_config.json` marquées `gui_verified: true` après clic
réel. Aucun nouveau bug de fond — uniquement de la clarté d'interface et
un test de bout en bout du GUI.*

---

## 1. Contexte — validation navigateur en cours

David valide les entrées du GUI une par une, dans l'ordre où il tombe
dessus (pas de plan préétabli). Trois entrées ont donné lieu à une
reformulation de leur descriptif, jugé trop chargé en jargon interne
pour quelqu'un qui ne lit pas le code (fichier fourni en session :
`scripts_config.json`, 28 entrées).

**Principe appliqué aux trois reformulations** : garder le vocabulaire
propre au projet (variables, scénarios, entités, alliances, fiches —
que David maîtrise et qui structure tout le vault) ; retirer le
vocabulaire d'implémentation interne (noms de fichiers YAML/JSON bruts,
mécanique de pipeline, termes comme "injection"/"aval"/"rétroactif" non
expliqués).

---

## 2. Descriptif clarifié — `fix_annee_debut_placeholder`

**Avant** : *"Corrige rétroactivement les fiches officialise_enrichi
restées au placeholder annee_debut=2026 : confirme ou corrige selon le
profil narratif, priorité aux jalons du scénario, avec une exigence de
traçabilité réelle (champ ancrage_reel) obligatoire pour toute date dans
les 10 prochaines années (2026-2036), validée mécaniquement contre le
recyclage de jalons fictifs. Idempotent : une fiche confirmée ou
corrigée est marquée annee_debut_verifiee et n'est plus jamais
retraitée aux runs suivants, quel que soit le nombre de relances."*

**Après** : *"Corrige les fiches d'entités dont l'année de
naissance/création était restée bloquée à une valeur par défaut (2026),
en la remplaçant par une date cohérente avec l'histoire du scénario.
Sans risque à relancer : une fiche déjà corrigée n'est jamais retraitée,
quel que soit le nombre de fois où tu lances ce script."*

Marquée `gui_verified: true` après validation.

---

## 3. Descriptif clarifié + sortie corrigée — `trace_injection`

**Descriptif avant** : *"Reconstitue le parcours complet d'un slug
donné : origine (idée source, date d'injection), propagation dans
l'espace (scénarios, zones) et le temps (fictif et réel), variables
systémiques influencées, réseau relationnel (alliances/oppositions ou
acteurs impliqués), et usage aval dans les articles publiés. Diagnostic
pur, lecture seule, aucun appel LLM."*

**Descriptif après** : *"Retrace l'histoire complète d'un personnage,
événement ou signal : d'où il vient, dans quels scénarios et quelles
zones il apparaît, quel effet il a sur le monde, et dans quels articles
déjà publiés il a été utilisé. Ne modifie rien, gratuit (pas d'appel à
l'IA)."*

**Sortie du script elle-même corrigée** (David a fourni un exemple réel
complet en session — pas juste le bouton, le contenu produit) :

| Avant | Après |
|---|---|
| `(instance)` en titre | `(entité)` |
| `Statut d'injection : origine introuvable (idée non trouvée dans processed/needs_review.yaml)` | `Origine : non retrouvée — l'idée qui a mené à la création de cette fiche n'a pas pu être identifiée (probablement une fiche ancienne, créée avant la mise en place du suivi)` |
| `Impact local/global : 5/3` (échelle non précisée) | `Impact local : 5/5 · Impact global : 3/5` |
| `Enrichie le : 2026-06-27` | `Détails complétés par l'IA le : 2026-06-27` |
| `amazonie_pacte_viva_eco_communalism, archives_ouvertes_des_jurisprudences_communales_aojc_eco_communalism...` (slugs bruts, suffixe répété 20+ fois) | `Amazonie pacte viva, Archives ouvertes des jurisprudences communales aojc...` |
| `## 4. Aval — usage dans les articles publiés` | `## 4. Usage dans les articles déjà publiés` |

**Fichier modifié : `trace_injection.py`**, fonctions `_rendre_markdown()`
et `_formater_liste_slugs()`. Cette dernière détecte désormais un
suffixe de scénario partagé même sans le recevoir en paramètre explicite
(avant : seul le cas où `scenario=` était passé explicitement était
nettoyé) — mais seulement si **tous** les slugs de la liste partagent le
même suffixe, pour ne jamais créer d'ambiguïté sur une liste mélangeant
plusieurs scénarios.

**Testé** : reconstruction exacte de l'exemple réel fourni par David
(comparaison ligne à ligne, résultat conforme au tableau ci-dessus), plus
4 cas de non-régression sur `_formater_liste_slugs()` — dont le cas le
plus risqué (slugs de plusieurs scénarios mélangés), confirmé sans perte
d'information : le suffixe reste affiché quand le retirer créerait une
ambiguïté. **Pas de nouveau test en conditions réelles sur le vault** —
le test s'appuie sur l'exemple déjà fourni par David, fidèlement
reconstruit en mémoire, pas sur un nouveau run réel du script.

Marquée `gui_verified: true` après validation.

---

## 4. Descriptif clarifié (le plus dense) — `fix_alliances_oppositions`

La plus grosse des trois reformulations : descriptif principal + 7
options + 2 libellés de rapports.

**Descriptif principal avant** : *"Corrige les alliances/oppositions
vides sur les fiches déjà enrichies (prompt ciblé, liste réelle des
instances du scénario fournie au LLM). Complète aussi la réciprocité (si
A cite B en alliance/opposition, B doit citer A en retour) et peut
résoudre automatiquement les conflits de réciprocité détectés selon la
règle "opposition prioritaire" (une opposition déclarée l'emporte sur
une alliance déclarée en cas de contradiction) — rétroactif, modifie les
fiches en conflit sur disque. Les deux rapports ci-dessous (conflits
détectés / résolus) sont réinitialisés à chaque run réel (pas en
simulation) : ils ne reflètent que l'état du DERNIER run, plus aucun
historique cumulé."*

**Après** : *"Remplit les alliances et oppositions manquantes sur les
fiches déjà complétées, en s'assurant que chaque relation est bien
réciproque (si A dit qu'il est allié à B, B doit le dire aussi) — et
peut résoudre automatiquement les cas où deux fiches se contredisent
(l'une dit « allié », l'autre dit « opposé »). Les rapports ci-dessous ne
montrent que le dernier lancement, pas un historique cumulé."*

**Les 7 options** — même traitement systématique, "passe LLM" remplacé
par "remplissage par l'IA" partout, avertissements de dépendance entre
cases conservés (ex. `--dry-run` : le piège "l'IA est quand même
appelée, coût réel malgré simulation" reformulé directement dans le
label, pas seulement dans la description). **Les 2 libellés de rapports**
— remplacés (avant : chemin de fichier brut répété tel quel comme
libellé ; après : "Rapport des conflits détectés/résolus (dernier
lancement)").

Marquée `gui_verified: true` après validation.

---

## 5. Dix entrées marquées `gui_verified: true`

Après clic réel dans le navigateur par David, en une seule fois :
`audit_dates_instances`, `audit_etat_temporel_fin`,
`audit_longueur_articles`, `audit_type_relation_dominante`,
`export_prompt_veille`, `import_veille_etat_monde`, `trace_injection`,
`fix_annee_debut_placeholder`, `fix_alliances_oppositions`, `generate`.

Vérification structurelle faite après coup (diff programmatique
champ par champ) : exactement ces 10 entrées modifiées, aucune autre
altérée dans les 28 du fichier.

**Restent à `gui_verified: false`** (non concernées par cette passe,
David ne les a pas mentionnées) : `create_entities`, `enrich_minimal`,
`generate_instances` — voir backlog Partie 1 point 3 pour le détail de
ce qui reste à tester.

---

## 6. Fichiers livrés cette session

**Scripts modifiés** : `trace_injection.py` (lisibilité de la sortie —
voir §3).

**Configuration modifiée** : `scripts_config.json` (3 descriptifs
reformulés, 10 entrées passées à `gui_verified: true` — toutes les
modifications vérifiées isolées par diff programmatique après coup, à
chaque étape).

**Documentation** : `USER_MANUAL_COMPLET.md` (nouvel addendum §7 pour le
11 août ; entrées `trace_injection.py`, `fix_alliances_oppositions.py`,
`fix_annee_debut_placeholder.py`, `audit_longueur_articles.py` mises à
jour — dont une correction d'une affirmation devenue fausse sur
`fix_alliances_oppositions.py`, qui indiquait encore `gui_verified:
false`), `BACKLOG_MASTER_9_AOUT.md` (mis à jour en place : point 3 de la
Partie 1 réduit aux entrées réellement encore à tester, nouvelle ligne
dans la table des chantiers clos), ce handoff.

---

## 7. Point de reprise suggéré pour la prochaine session

Backlog Partie 1, toujours en tête (🟡 uniquement, aucun 🔴) :

1. Validation à plus grande échelle du retry sur la longueur (chantier
   du 10 août) — pas urgent.
2. Validation réelle du fix signature itération 2 (position + unicité,
   chantier du 10 août) — aucun batch généré depuis ce correctif.
3. **Suite du test navigateur GUI** — désormais concentré sur 3 entrées
   seulement : `create_entities`, `enrich_minimal`, `generate_instances`
   (plus les options `--ancrage-temporel` et le menu `État`/`Clandestin`
   qui vivent dans ces mêmes entrées). Une seule session ciblée sur ces
   3 pourrait clore ce point pour de bon.
4. Reste du backlog inchangé depuis le 10 août — voir
   `BACKLOG_MASTER_9_AOUT.md` Partie 1, points 4 à 11.

**Rappel de méthode qui continue de bien fonctionner** : à chaque
modification de `scripts_config.json`, vérifier par diff programmatique
(pas juste visuel) qu'aucune entrée en dehors de celle(s) visée(s) n'a
été altérée — fait systématiquement cette session, aucune régression
détectée sur les 28 entrées du fichier au fil des 4 modifications
successives.
