# Handoff — session du 17 août 2026

*Session menée via chat avec Claude (aucun accès direct GUI/terminal côté
Claude), David exécutant les commandes/scripts sur son vault et
rapportant les résultats, plus un lancement réel depuis le GUI en fin de
session pour valider l'intégration. Point de départ : une question de
David en fin de session précédente ("comment je sais qu'il y a un
problème si je regarde le Flask ?"), suite à la découverte que le
panneau Revue du GUI était vide malgré un échec de génération connu
(`eco_communalism`, "Les Veilleurs des Nappes Phréatiques", 15 août).
Un seul chantier traité, mais en plusieurs temps forts : diagnostic de
l'angle mort, création et correction d'un script d'audit, investigation
approfondie sur le vault réel, décision et exécution d'une suppression
d'entité, comblement des instances manquantes, intégration GUI.*

---

## 0. Point de départ — pourquoi le panneau Revue était vide

Diagnostic fait avant tout code, en lisant le comportement réel plutôt
qu'en supposant : le rejet d'une idée entière (`category`/`scenario_ref`
invalide) écrit bien dans `entites_custom/needs_review.yaml`, lu par le
panneau Revue. Mais un échec *après* la création réussie de l'entité,
sur un seul scénario de sa boucle d'instances (le cas exact
d'`eco_communalism`, bloqué par le garde-fou `ancrage_reel` le 15 août
alors que l'entité et 5/6 instances avaient déjà réussi), ne passe pas
par ce chemin — l'idée d'origine avait déjà été retirée de la file
avant même que la boucle sur les 6 scénarios ne démarre. Ce type
d'échec n'existe qu'en sortie console au moment du run, jamais relu
ensuite. Conclusion actée avec David : ce n'est pas un signe que le
problème avait disparu, juste l'état normal d'un mécanisme qui n'a
jamais eu de sortie persistante pour ce cas précis.

David a alors demandé s'il existait un moyen de centraliser la liste
des éléments à corriger sans avoir à relancer des scripts pour le
découvrir — c'est ce qui a motivé tout le reste de la session.

---

## 1. Diagnostic du mécanisme réel (lecture de code, pas de suppositions)

Avant d'écrire quoi que ce soit, lecture directe du code fourni par
David (`create_entities_and_instances.py`, `instance_generation_common.py`,
`app.py`, `scripts_config.json`) plutôt que de deviner :

- `process_entity_scenario()` retourne bien un statut structuré par
  scénario en cas d'échec (`{"status": "needs_review", "issues": [...]}`)
  — l'information existe au moment de l'échec.
- Son appelant, `generate_instances_for_entity()`, ne fait
  qu'incrémenter `stats["errors"] += 1` sans jamais propager ni
  persister le détail. L'information est donc calculée puis jetée.
- `app.py` (`_execute_script()`) capture pourtant déjà l'intégralité du
  stdout de chaque run lancé depuis le GUI dans un fichier persistant
  (`gui/logs/{script_id}_{timestamp}.log`, jamais purgé) — mais ce
  fichier n'est relu par aucun mécanisme existant.
- `write_entity_file()` enregistre dans le frontmatter de chaque
  entité un champ `scenarios_instances` (liste des scénarios prévus à
  la création) — comparable directement aux fichiers réellement
  présents dans `instances/`, indépendamment des logs.

Deux briques exploitables identifiées sans avoir besoin d'en construire
de nouvelles : le diff filesystem (fiable, toujours disponible) et les
logs GUI existants (best-effort, seulement si le run est passé par le
GUI et que le fichier n'a pas été supprimé).

---

## 2. `audit_instances_manquantes.py` — v1

Script de lecture seule, aucune écriture, aucun appel LLM, même
convention que `trace_injection.py`/`audit_broken_slugs.py`. Compare
`scenarios_instances` (fiche entité) aux fichiers `instances/
{slug}_{scenario}.md` réels ; pour chaque trou, cherche best-effort le
motif dans `gui/logs/*.log` (parsing du bloc `=== {nom} ===`, puis de
la ligne `{scenario}... ✗` et des lignes de raison `     - ...` qui
suivent — format exact de sortie de `process_entity_scenario()`/
`process_custom_idea()`).

Testé sur un mini-vault synthétique reproduisant fidèlement le cas réel
(`eco_communalism`) avant tout lancement contre le vrai vault : trou
détecté, raison exacte extraite du log simulé, zéro faux positif sur un
cas sain, sortie `--json` valide.

---

## 3. Premier run réel — 19 trous, pas 1

Lancé contre le vrai vault : **19 instances manquantes**, bien au-delà
du seul cas connu. Décision de ne pas traiter ça comme "19 échecs à
corriger" sans d'abord comprendre la répartition — deux profils très
différents sautaient aux yeux dans la sortie brute (une entité à 6/6
scénarios manquants d'un coup n'a rien à voir avec un échec ponctuel de
garde-fou qui ne bloque normalement qu'un seul scénario) plus un slug
visiblement cassé (`les_gardiens_des_n_uds_hybrides`, encodage
d'accents non-français).

---

## 4. `audit_instances_manquantes.py` — v2 : classification en 3 catégories

Ajout d'une classification pour éviter de traiter des signaux
hétérogènes de façon uniforme :
- **Faux positif probable (désaccord de slug)** : un fichier existe
  déjà sous un slug proche, détecté par recalcul déterministe
  (`slugify_fixed()`, fonction corrigée du 14 août) + une passe floue
  (`difflib`) sur les noms de fichiers.
- **Entité entière suspecte** : proportion de scénarios manquants ≥
  seuil (`--seuil-suspect`, défaut 0.5).
- **Échec ponctuel probable** : le reste, profil `eco_communalism`.

Relancé contre le vrai vault : **4 "faux positifs de slug" remontés**
(`Coalition du Vivant`↔`consortium_amazonia_viva`, `Les Gardiens...`↔
`...corridors_hybrides`, `NexCore`↔`nexus_biosyn`, `Réseau des
Cartographes...`↔`contrebandiers_energetiques...`).

**Vérification manuelle immédiate de ces 4 matches, avant d'agir** :
calcul direct des ratios `difflib` avec et sans le suffixe `_scenario.md`
partagé. Résultat sans appel : le suffixe partagé gonflait
artificiellement la similarité sur des entités **sans aucun rapport**
(`nexcore` vs `nexus_biosyn` : 0.42 de similarité réelle sur le nom
seul, 0.79 avec le suffixe — au-dessus du seuil 0.75 utilisé, donc un
faux match automatique du script lui-même). 3 des 4 étaient des
artefacts de détection, pas de vrais désaccords de nommage. Seul le 4e
cas (`Les Gardiens...`) restait plausible mais non confirmé (pattern de
nommage partagé entre deux entités probablement distinctes, "Les
Gardiens des X Hybrides").

---

## 5. `audit_instances_manquantes.py` — v3 : retrait de la passe floue automatique

Correctif : la reclassification automatique en "faux positif" ne
repose plus que sur la passe déterministe. La passe floue est
conservée uniquement comme indice faible non déterministe (seuil
relevé à 0.90, comparaison SANS le suffixe scénario cette fois),
annoté en note dans la catégorie d'origine du trou, jamais utilisé pour
le déplacer. Testé sur 3 vaults synthétiques (deux entités sans rapport
partageant un scénario, cas limite à 0.85 de similarité réelle) —
confirmé : plus aucune reclassification à tort, l'indice apparaît en
note sans déplacer le trou.

Relancé contre le vrai vault : **0 faux positif de slug** cette fois —
les 4 précédents rejoignent la liste des échecs ponctuels probables.

---

## 6. Seuil de classification "entité suspecte" — bug trouvé sur un 2e run réel

Un nouveau run réel a révélé un cas limite : `Les Gardiens des Nœuds
Hybrides` classée "entité entière suspecte" avec `manquants (1/1)` —
un seul scénario prévu au total, et c'est celui-là qui manquait,
proportion 100% à tort interprétée comme "majorité manquante" alors que
le profil est identique à un simple échec isolé. **Corrigé** par un
seuil absolu (`--seuil-absolu`, défaut 3 scénarios manquants en valeur
absolue) combiné à la proportion — celle-ci n'entre en jeu que si le
total prévu est lui-même assez grand. Testé sur 4 profils synthétiques
(1/1, 2/6, 3/6, 6/6) : classification correcte sur les 4 après
correctif.

---

## 7. Investigation des 2 dernières "entités suspectes" — recherche dans l'archive

Après ces deux correctifs, le run réel se stabilise à **2 entités
suspectes** (`institut_des_seuils_demographiques` 6/6,
`le_cartographe_silencieux` 6/6) et **6 échecs ponctuels**. Les deux
suspectes partagent la même `date_creation: 2026-06-19` — indice
qu'une recherche dans l'archive du vault pouvait éclaircir plutôt que
de relancer en masse à l'aveugle.

Commande fournie à David :
```bash
grep -rniE "19 juin|19_juin|2026-06-19|institut_des_seuils|seuils démographiques|cartographe_silencieux|cartographe silencieux" \
  --include="*.md" --include="*.txt" --include="*.yaml" . \
  | grep -v "^\./instances/\|^\./entites/"
```

**Résultats croisés** :
- `institut_des_seuils_demographiques_breakdown` mentionné dans
  `documentation/Old/HANDOFF_11_AOUT_SOIR.md` §8 — troncature JSON
  transitoire côté Mistral, aléa API documenté et déjà classé comme
  "pas de correctif nécessaire, résilience existante suffisante".
  N'explique qu'1 des 6 scénarios manquants ; les 5 autres restent sans
  trace documentée. Entité sans `custom_source` — probablement issue du
  mode `auto`.
- `Le Cartographe Silencieux` : deux entrées complètes et distinctes
  dans `entites_custom/processed.yaml` (deux vrais appels LLM, deux
  `description_complete` différentes — pas un artefact de copier-coller),
  et une seule mention ailleurs dans tout le vault : le commentaire
  `# EXEMPLE :` de l'en-tête de documentation d'`entites_custom/
  queue.yaml`, avec le nom, le rôle et l'`etat` copiés mot pour mot,
  `source: idee_2026-06`.

**Conclusion** : `Le Cartographe Silencieux` est très probablement une
donnée de test résiduelle du tout début du projet (l'exemple de doc
copié-collé littéralement, deux fois), pas une vraie intention de
peupler le vault — cohérent avec 0/6 instances sur le disque dans les
deux tentatives. `Institut des Seuils Démographiques` reste un vrai
trou de couverture ancien, sans lien avec le garde-fou `ancrage_reel`
(inexistant en juin, créé le 8 août) malgré la coïncidence de date de
création qui aurait pu le suggérer à tort.

---

## 8. Décision et suppression du Cartographe Silencieux

David tranche : supprimer, pas conserver.

**Vérification préalable** : `grep -rn` sur `entites/`, `instances/`,
`evenements/` pour confirmer qu'aucune autre fiche du vault ne
référence ce slug avant suppression — résultat propre, seule la fiche
elle-même s'auto-référence (son propre tableau interne de scénarios,
jamais alimenté par une vraie instance). Suppression sans risque de
casser une référence croisée.

**Étapes réalisées** :
1. Sauvegarde (`documentation/need_action/backup_suppression_cartographe_silencieux/`).
2. Suppression de `entites/le_cartographe_silencieux.md`.
3. Retrait de l'entrée `_entities_list.json` (script Python fourni,
   confirmé 1 entrée retirée sur 592 → 591).
4. Retrait des 2 blocs dupliqués de `entites_custom/processed.yaml`.

**Correctif supplémentaire trouvé en vérifiant le fichier après l'étape
4** — David avait fourni le fichier `processed.yaml` déjà édité
manuellement : les deux blocs avaient bien disparu, mais une ligne
orpheline restait (`- status: injected` sans aucun champ `idea:`/
`slug:` en dessous — entrée YAML incomplète mais syntaxiquement valide,
donc invisible à un simple `grep "Cartographe"`, mais un risque réel de
`KeyError` pour tout script supposant `idea`/`slug` toujours présents).
Détectée par un script de vérification dédié (comparant chaque entrée
`- status: injected` à la présence d'un champ indenté sur la ligne
suivante) : un seul orphelin trouvé sur 201 entrées scannées. Fichier
corrigé et retourné à David (10284 lignes, 200 entrées, toutes
complètes, `yaml.safe_load()` confirmé propre).

**Validation finale** : `validate.py` → 0 erreur, 1 avertissement
(inchangé, `[LOCALISATION]` sur `gelecek_meclisi_policy_reform`, déjà
connu depuis le 16 août, sans rapport).

---

## 9. Comblement des 13 instances manquantes confirmées

Commandes `generate_instances.py --entity ... --scenario ...` fournies
par lot. **Incident méthodologique en cours de route** : après
confirmation par David d'avoir lancé une seule commande de vérification
(`--dry-run` sur `reseau_des_cartographes_des_zones_grises`/
`fortress_world`), le script a répondu "déjà existant" — alors que
cette instance apparaissait comme manquante dans le diagnostic
précédent. Avant de continuer à l'aveugle sur les 12 autres, diagnostic
immédiat demandé : script `diag_slug.py` fourni pour comparer, avec
`repr()`, le slug/scénarios lus par l'audit contre les fichiers réels.
Résultat : **les 6 fichiers existaient bel et bien**, avec leurs `.bak`
associés — confirmant que le bloc de 12 commandes avait en réalité déjà
été exécuté dans son intégralité au moment du copier-coller précédent
(pas un bug du script d'audit). Un nouveau run de l'audit a confirmé
que seuls 3 trous restaient réellement, dont un jamais inclus dans les
listes de commandes fournies (`les_gardiens_des_n_uds_hybrides`/
`fortress_world`, oubli de ma part en préparant les commandes) — les 3
lancés, confirmés.

**Dernier trou restant** (`institut_des_seuils_demographiques`/
`new_sustainability`, manqué dans le tout premier lot) : lancé
séparément après un run de l'audit **depuis le GUI**, confirmant au
passage l'intégration (voir §10). Cycle post-injection automatique
enchaîné (`extract_localisation.py` → `review_localisation.py
--auto-resolve` → `validate.py`), qui a retraité au passage les 2
fiches en attente de localisation (pas seulement la nouvelle) — voir
point mineur §11.

**Validation finale** : `validate.py` → 0 erreur, 1 avertissement
(inchangé). 758 instances chargées (755 + 3 générées ce jour), 591
entités (592 − 1, Cartographe Silencieux). Confirmé stable par un
dernier passage de l'audit (0/0/0 sur les 3 catégories, hors le trou
`new_sustainability` comblé dans la foulée).

---

## 10. Intégration GUI

Nouvelle entrée `audit_instances_manquantes` ajoutée à
`scripts_config.json`, section `validation`, sur le patron des audits
déjà en place (`audit_dates_instances` et consorts) — quatre options
exposées (`--vault-root`, `--report` coché par défaut, `--seuil-absolu`,
`--seuil-suspect`), champ `yaml_files` renseigné pour afficher le
rapport dans le panneau de review (même mécanisme que
`fix_alliances_oppositions`). **Lancé et confirmé fonctionnel par
David dès le premier essai réel dans le navigateur** — rapport bien
écrit sur disque (`documentation/need_action/instances_manquantes.md`),
résultat cohérent avec les runs CLI précédents de la session.
`gui_verified: true`.

---

## 11. Point mineur non traité — laissé ouvert

`[VALIDATION ÉCHOUÉE] slug zone inconnu : 'istanbul' (non trouvé dans
geographie/policy_reform.md)` sur `gelecek_meclisi_policy_reform`,
révélé par le cycle post-injection du §9 (`extract_localisation.py`
retraite systématiquement toutes les fiches en attente, pas seulement
la dernière créée). Pas d'investigation approfondie faite le 17 août —
repéré en marge d'un autre chantier. `validate.py` reste à 1
avertissement `[LOCALISATION]`, statut inchangé, pas bloquant. Ajouté
au backlog (Partie 1, point 8) pour une prochaine session.

---

## 12. Fichiers livrés cette session

- `audit_instances_manquantes.py` *(nouveau)* — 3 versions itérées en
  session, voir §2/§4/§5/§6 pour le détail de chaque correctif.
- `scripts_config.json` — nouvelle entrée GUI `audit_instances_manquantes`.
- `entites/_entities_list.json` — 592 → 591 entités (retrait Cartographe
  Silencieux).
- `entites_custom/processed.yaml` — 2 blocs dupliqués + 1 ligne
  orpheline retirés (202 → 200 entrées).
- 13 nouvelles fiches instance (voir `BACKLOG_MASTER_9_AOUT.md` Partie 4
  pour la liste complète par entité/scénario).
- `entites/le_cartographe_silencieux.md` — supprimée (sauvegarde dans
  `documentation/need_action/backup_suppression_cartographe_silencieux/`).

**Redémarrage Flask requis** après changement dans `scripts_config.json`
— déjà fait par David avant le test GUI du §10, confirmé sans piège
cette fois.

---

## 13. Point de reprise suggéré pour la prochaine session

1. **Nouveau, non traité** : investiguer l'erreur de localisation
   `istanbul` sur `gelecek_meclisi_policy_reform` (§11) — vérifier si
   une zone équivalente existe dans `geographie/policy_reform.md` sous
   un nom différent, ou si c'est un vrai trou de couverture géographique.
2. Point de reprise du 16 août (`eco_communalism`/"Les Veilleurs des
   Nappes Phréatiques") : **levé** — n'apparaît plus dans l'audit
   exhaustif du 17 août, couverture confirmée complète pour cette
   entité (origine exacte du comblement non déterminée, voir §9).
3. Toujours en attente depuis le 16 août : confirmer la propagation
   matricielle (`via_matrice: true`) sur un signal faible en conditions
   réelles — testée en synthétique seulement à ce stade.
4. Confirmer sur plusieurs générations futures que le 3e correctif du
   chantier `forces_attractives`/`forces_repulsives` (couverture des
   variables pilotes) tient dans la durée — un seul test positif à ce
   stade, du 15 août.
5. Chantiers Partie 1 du backlog toujours ouverts, sans changement de
   statut cette session : point #1 (validation retry longueur, 🟡, sans
   urgence), P17, Bug #27, renommage YAML génériques, troncatures JSON
   — tous gardés pour plus tard sur décision explicite de David, non
   rouverts cette session.
