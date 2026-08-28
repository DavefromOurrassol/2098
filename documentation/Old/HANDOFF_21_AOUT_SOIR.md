# Handoff — session du 21 août 2026 (soir)

*Suite de la session du 21 août — voir `HANDOFF_21_AOUT.md` pour la
première partie (retry longueur, découverte P22, ménage du vault,
risque instances custom, P20 Phase A). Menée via chat avec Claude
(aucun accès direct GUI/terminal côté Claude), David exécutant les
commandes et rapportant les résultats, avec plusieurs uploads
d'articles réels générés en direct pour valider le code au fil de la
séance. Séance interrompue en plein débogage, reprise prévue le
lendemain.*

## 0. Point de départ

P20 restait sur "Phase A close, Phases B/C ouvertes" à la fin du
handoff du matin. David souhaitait détailler et coder la Phase B avant
de continuer.

## 1. P20 Phase B — codée

Trois champs, trois décisions tranchées rapidement en réutilisant du
code déjà existant plutôt qu'en inventant un nouveau mécanisme :
- `zone_principale` ← `snapshot["zone_slug"]` (déjà calculé par
  `_dominant_zone()`, déjà utilisé pour choisir le journal de zone).
- `date_publication` = `date_evenement` pour l'instant (aucun délai
  éditorial simulé), champs gardés séparés pour l'avenir.
- `entites_citees` ← slugs de `filtered_instances`, sous-produit
  gratuit préparant le futur `articles_lies`.

Testé (cas normal, `zone_slug` absent, clé manquante du snapshot) — 3
cas, tous passent.

## 2. P20 Phase C — codée, `generate_images.py`

David a fourni le plan d'implémentation d'origine (12 juillet) :
`image_prompt` + `a_une_photo` déjà faits en Phase A, restait le
script `generate_images.py`. Vérifié par recherche web avant de coder :
**Claude/Anthropic n'a pas d'API de génération d'image native** — un
service tiers sera nécessaire. David a choisi de reporter ce choix
("point d'intégration générique à brancher plus tard").

Discussion approfondie sur la gestion des crédits, David a proposé un
principe plus riche que prévu : `image_credit` devient un champ à
valeurs contrôlées (`IA_generated`/`personnel`/`autre`/vide) qui pilote
le comportement du script — génération automatique si IA, placeholder
neutre en attente d'upload sinon. David a validé la création d'un
placeholder neutre par mes soins (2 SVG, distincts selon le cas).

**Script livré et testé sur 5 cas synthétiques** : IA_generated (stub
→ placeholder), personnel (placeholder manuel), credit vide (ignoré),
`a_une_photo: false` (jamais listé), image déjà réelle (skip sans
`--force`). Vérifié aussi le re-run automatique du placeholder IA (pas
besoin de `--force` pour le retraiter une fois le service branché).

## 3. `image_alt` — clarification et garde-fou

Repositionnement nécessaire : `image_alt` doit être un texte
descriptif de l'**image**, pas un résumé de l'article ni un endroit
pour le crédit — confirmé par comparaison avec la pratique des
journaux en ligne réels (alt = description visuelle, crédit = légende
séparée, jamais fusionnés). Décision : `image_alt` = copie
d'`image_prompt`, sans appel LLM supplémentaire.

David a ensuite noté que le texte pourrait dépasser "quelques mots".
Discussion sur la vraie source du risque (pas la longueur en soi, mais
la fiabilité imparfaite du LLM sur la consigne "en une phrase" — déjà
vu ailleurs aujourd'hui). Garde-fou `_truncate_alt()` codé : garde la
première phrase complète si plusieurs sont produites, repli sur
troncature au mot (jamais en plein mot) seulement si cette phrase
unique dépasse 180 caractères. Testé sur 5 cas, tous passent, y
compris les deux qui comptent (multi-phrases, phrase unique trop
longue).

## 4. Consigne `image_prompt` — sujet nommé

David a remarqué que l'`image_prompt` devrait représenter le vrai sujet
de l'article (ex. une personne nommée) plutôt que rester une scène
neutre. Consigne renforcée dans `build_journalistic_brief()` :
représenter explicitement (nom/rôle) un sujet nommé précis s'il existe,
sinon rester neutre. Non testable sans appel LLM réel au moment du
correctif.

## 5. GUI — champs de décision manuelle

David a demandé à décider `a_une_photo`/`image_credit` **dès
l'écriture de l'article**, pas seulement après coup. Deux champs
ajoutés sur l'écran "Générer un article" (semi-guidé ET forcer, sans
restriction) : case "Aura une image" + menu "Crédit image". Pour la
série, politique "Illustration des articles" (Aucune/Toutes/Aléatoire) —
probabilité de 25% actée avec David pour "Aléatoire". Décision : en
série, `image_credit` reste toujours vide même si `a_une_photo` devient
`true` via la politique — la source se choisit par article, plus tard.

Câblage : `generate.py` (2 nouveaux flags CLI), `generate_series.py`
(nouveau champ `photo_policy`), `api.py` (`build_article_md()`/
`save_article()` acceptent ces valeurs au lieu de les figer en dur),
`scripts_config.json` (formulaire GUI). Testé : logique de probabilité
(26,5% mesuré sur 5000 tirages), non-régression confirmée.

## 6. Débogage en conditions réelles

David a uploadé 3 batches d'articles réels au fil de la séance pour
valider le code en conditions live.

**Premier batch (3 articles `breakdown`, avant Phase B/C)** : validation
complète — YAML valide, tous les champs présents, bloc métadonnées bien
retiré, signature cohérente sur 3/3. Meilleur résultat de la journée à
ce stade. Un point d'observation noté (pas un bug) : sur un article, un
personnage récurrent bien représenté visuellement dans `image_prompt`
mais sans que son nom y soit écrit — a motivé le renforcement de la
consigne du point 4 ci-dessus.

**Question sur `a_une_photo` toujours à `false`** : David se demandait
si l'absence d'image sur ces 3 articles s'expliquait par la politique
"Aléatoire" (25%). Clarifié : ces articles avaient probablement été
générés en mode individuel (case non cochée), pas en série — et même
en série, obtenir 0/3 avec 25% de chances n'a rien d'anormal
statistiquement (≈42% de probabilité d'avoir exactement 0 succès sur un
tirage de 3). David a choisi de forcer `a_une_photo: true` à la main
pour tester la suite du pipeline.

**Deuxième round — `image_alt`/`image_principale` absents.** David a
remarqué que ces deux champs n'apparaissaient pas dans le frontmatter.
Clarifié : comportement voulu — ces deux champs ne sont écrits que par
`generate_images.py`, jamais à la génération de l'article, et
seulement pour les articles `a_une_photo: true` (aucun des 3 testés ne
l'était). Proposé de changer ce comportement (champs vides dès la
génération) — question restée en suspens, David a préféré avancer sur
le test du pipeline complet plutôt que trancher ce point de cohérence
immédiatement.

**Test avec politique série "Toutes" — bug apparent.** David a relancé
une série de 3 articles (`policy_reform`) avec la politique
"Illustration des articles" sur "Toutes", en ayant préalablement
redémarré Flask (relance demandée par David lui-même après le premier
essai raté). Résultat : `a_une_photo: false` sur les 3 articles malgré
tout. **Diagnostic mené avec David** : demande de vérifier
`config_series.yaml` directement — confirmé, la clé `photo_policy`
était totalement absente du fichier. Cause identifiée par lecture de
code (`app.js::buildYamlFormPanel()` générique, `generate_series.py`
correct) : le premier lancement de la série avait eu lieu **avant**
que David redémarre Flask, donc le formulaire du navigateur ne
connaissait pas encore le nouveau champ au moment de cette génération
précise. Pas un bug de code — piège de redémarrage déjà documenté
plusieurs fois (15 août notamment), reconfirmé sur un nouveau fichier.
David a ensuite relancé après redémarrage effectif — voir plus bas pour
le résultat.

**Troisième batch (3 articles `policy_reform`, après redémarrage
Flask)** : deux découvertes.

1. **P25, nouveau symptôme.** 1/3 signature correcte, 1/3 signature
   présente mais repoussée en fin d'article après un séparateur `---`
   (nouveau détail, jamais observé dans les batches précédents), 1/3
   sans aucune signature. Décision inchangée d'observer avant de
   corriger — nouvelle piste notée pour la prochaine session (détecter
   le pattern `---` en fin de texte).
2. **Tags non réutilisés entre articles.** David a repéré que chaque
   article invente ses propres tags. Discussion sur la pratique réelle
   des rédactions en ligne (ni libre indéfiniment, ni taxonomie fixée à
   l'avance — accumulation + réutilisation + nettoyage périodique).
   **Décision (Option C)** : vocabulaire qui s'auto-construit depuis le
   corpus existant, consigne de réutilisation prioritaire, possibilité
   de figer plus tard. Rien codé — nouveau chantier ouvert (backlog
   Partie 1, point 11).

## 7. Nouveau besoin — rétro-application sur les articles existants

David a demandé explicitement, avant la coupure de séance, d'ajouter la
possibilité d'agir rétroactivement sur les articles déjà générés — pas
seulement les futurs. Deux cas à couvrir : les articles antérieurs à
P20 (aucun nouveau champ), et les articles générés aujourd'hui même
avant certains correctifs de cours de route (consigne `image_prompt`,
futur vocabulaire de tags). Rien scopé en détail — nouveau chantier
ouvert (backlog Partie 1, point 12), portée et méthode à trancher à la
prochaine session.

## 8. Fichiers livrés cette session (soir)

- `api.py` (cumulatif — Phase B, Phase C, `image_credit`,
  `a_une_photo`/`image_credit` en paramètres de `build_article_md()`/
  `save_article()`).
- `generate_images.py` (nouveau, avec `_truncate_alt()`).
- `prompt_builder.py` (consigne `image_prompt` sujet nommé).
- `generate.py` (flags `--a-une-photo`/`--credit`).
- `generate_series.py` (champ `photo_policy`).
- `scripts_config.json` (formulaire GUI, 3 nouveaux champs au total).
- `images/_placeholder_en_attente_manuel.svg` et
  `_placeholder_en_attente_generation.svg` (nouveaux, dossier `images/`
  à créer manuellement à la racine du vault).

**Redémarrage Flask requis** après `scripts_config.json` — déjà vécu ce
soir comme piège concret, à ne pas oublier à la prochaine reprise si
d'autres champs GUI sont ajoutés.

## 9. Mise à jour de la documentation

`BACKLOG_MASTER_9_AOUT.md` mis à jour en place :
- **Point 9 (P20)** : statut passé à 🟢, Phases A+B+C toutes codées,
  service image restant à brancher (point technique isolé, pas un
  blocage de conception). GUI documenté dans ce même point.
- **Point 10 (P25)** : enrichi avec le nouveau symptôme du pattern
  `---`, décision d'observation inchangée.
- **Nouveau point 11** : vocabulaire des tags (Option C, rien codé).
- **Nouveau point 12** : rétro-application sur les articles existants
  (rien scopé, demandé explicitement par David).
- Note de fin de fichier réécrite pour refléter la coupure en plein
  débogage et l'ordre suggéré de reprise.

`USER_MANUAL_COMPLET.md` mis à jour en place — nouvelle section
"P20 — Phases B et C, GUI, et débogage réel" en fin de fichier,
couvrant tout le contenu ci-dessus en détail technique.

## 10. La séance a en fait continué — pas d'interruption réelle

Contrairement à ce qu'annonçait la section précédente, la séance ne
s'est pas arrêtée là : David a enchaîné directement sur les points 11
et 12 le soir même, jusqu'à leur clôture complète. Suite du récit
ci-dessous.

## 11. `rapprocher_articles.py` — articles_lies + tags conçus ensemble

David a demandé comment les tags sont gérés dans les vraies rédactions
en ligne avant de trancher. Discussion : accumulation progressive,
réutilisation suggérée, nettoyage périodique — ni liste figée à
l'avance, ni vocabulaire libre indéfiniment. Décision (Option C)
confirmée dans cette optique.

En concevant la solution, réalisé que `articles_lies` (resté en
jachère depuis la Phase B de P20) et le vocabulaire de tags reposent
sur le même mécanisme de fond — un seul script plutôt que deux :
`rapprocher_articles.py`, construit et testé (voir
`USER_MANUAL_COMPLET.md` pour le détail technique complet).

David a ensuite demandé s'il existait un outil d'analyse de contenu
plus complet, citant la vue graphique d'Obsidian. Vérifié sur les
fiches `entites/*.md` existantes : leurs wikilinks vivent dans le corps
(jamais le frontmatter) — confirmé que la vue graphique d'Obsidian ne
suit que ça. Ajout d'une ligne `**Voir aussi**` en wikilinks en fin de
corps de chaque article (génération native ET `rapprocher_articles.py`),
combinant `entites_citees` + `articles_lies` — branche le corpus sur
Obsidian sans outil supplémentaire à construire.

Mode `--stats` ajouté sur demande explicite de David ("le but est
aussi de détecter si ma génération d'articles a un biais non voulu").
Testé sur un tout petit échantillon réel (7 articles, 2 scénarios) :
`gelecek_meclisi` omniprésente à 100% sur les deux. Investigation
menée avant de conclure — confirmé structurel (variables/zones très
larges dans sa fiche instance, favorisée par la formule de score de
`filter_instances_for_thematique()`), pas un artefact aléatoire.
**David a choisi d'observer sur un corpus plus large avant de
trancher** plutôt que de corriger dans l'immédiat.

**`rapprocher_articles.py` codé et testé intégralement, jamais encore
lancé pour de vrai sur le corpus complet** — reporté après la clôture
du point 12 (voir ci-dessous), puisque le corpus éligible allait
changer radicalement une fois le rattrapage terminé.

## 12. `enrich_articles_pre_p20.py` — rétro-application, ouvert ET clos le soir même

David a demandé "je voudrais mettre au propre tous les articles avant
de continuer" — clarifié en 3 sous-demandes précises (dates manquantes,
rangement incohérent, chapo vides) avant d'agir.

**Conception et premiers tests** : script à 3 niveaux (mécanique,
approximation, LLM) construit et testé sur corpus synthétique avant
tout usage réel — voir `USER_MANUAL_COMPLET.md` pour le détail complet
des 3 niveaux et des bugs corrigés en route (slugs dupliqués, préfixe
"Par", regex de casse partagé avec la génération live, piège
`--skip-llm` bloqué activement, regex de date élargi en deux temps).

**Un point de fond discuté avant de foncer** : David a demandé s'il ne
valait pas mieux supprimer et régénérer tout le corpus pré-P20 plutôt
que le rattraper. Compromis présenté (coût, perte du contenu narratif
existant, absence de point d'arrêt naturel vu que le pipeline continue
d'évoluer) — David a choisi de conserver le rattrapage.

**Un vrai problème de fond découvert et résolu en cours de route** :
David a remarqué "certains articles n'ont pas de slug auteur, et je
vois des tags que je ne connais pas" à un autre moment de la séance —
distinct de ce chantier mais lié : ça a motivé la décision sur le
vocabulaire des tags (point 11 ci-dessus) et confirmé, via un exemple
concret ("Bratislava Secteur Alpha" pris pour un nom de journaliste),
que le regex mécanique de signature ne pouvait pas distinguer une
personne d'une institution — d'où l'ajout du champ `JOURNALISTE` à
l'appel LLM de ce script (le LLM tranche, pas une nouvelle heuristique
regex).

**Exécution réelle complète** : 56/56 articles traités, 3 avertissements
initiaux (résolus par le correctif de casse). David a ensuite demandé
un "mode audit" pour vérifier la propreté avant de considérer le
chantier terminé — révélant un problème totalement inattendu : **44
des 56 articles étaient posés à la racine de `articles/`** plutôt que
dans un sous-dossier par scénario (convention différente avant un
certain point du projet). Corrigé dans `rapprocher_articles.py` ET
`enrich_articles_pre_p20.py` (balaient désormais racine + sous-dossiers,
scénario lu depuis le frontmatter). Nouveau mode `--reorganize` créé et
lancé en réel : 44/44 déplacés sans collision.

Deux modes de rattrapage ciblé ajoutés ensuite pour finir le ménage
sans tout retraiter : `--retry-empty-date` (26/29 dates récupérées) et
`--retry-empty-chapo` (3/3 récupérés). 3 dates résiduelles diagnostiquées
une par une avec David (année tronquée à 3 chiffres, date en portugais,
calendrier fictif propre à un article) — 2 corrigées à la main par
David, 1 laissée vide (calendrier fictif, aucune correspondance réelle
possible).

**Découverte annexe, sans lien avec ce chantier** : sur un article
(`lynth_lieu_encommande`), la date écrite dans le texte par le LLM à la
génération ne correspond pas à celle demandée (visible dans le nom de
fichier) — écart préexistant de juillet, invisible jusqu'ici. Décision :
la date du texte publié fait foi, pas celle du nom de fichier.

**Audit final** : 0 fichier à la racine, 1 date vide (acceptée), 0
chapo vide. **Point 12 considéré clos.**

## 13. Fichiers livrés (au-delà de ceux déjà listés au point 8)

- `rapprocher_articles.py` (nouveau).
- `enrich_articles_pre_p20.py` (nouveau, 5 modes au total : défaut,
  `--audit`, `--reorganize`, `--retry-empty-date`, `--retry-empty-chapo`).
- `api.py` (section "Voir aussi" ajoutée à `build_article_md()` ;
  `_extract_publication_metadata()` corrigé en `re.IGNORECASE`, partagé
  avec la génération live).
- `prompt_builder.py` (`_load_tags_suggeres()` + consigne TAGS enrichie).
- `generator/tags_reference.yaml` — sera créé au premier lancement réel
  de `rapprocher_articles.py`, pas encore fait.

## 14. Mise à jour de la documentation (cette clôture)

`BACKLOG_MASTER_9_AOUT.md` mis à jour en place :
- **Point 9bis** (nouveau) : `articles_lies` + vocabulaire tags, statut
  🟢 codé/testé, pas encore lancé en réel sur le corpus complet.
  Observation `gelecek_meclisi` documentée dedans.
- **Point 12** : statut passé à ✅ clos, résumé complet de tout le
  chantier (bugs trouvés, découverte du rangement incohérent, 3 dates
  résiduelles, décision garder-vs-régénérer).
- Ancien point 11 (vocabulaire tags, "décidé non codé") retiré,
  absorbé dans le point 9bis puisque désormais codé.
- Note de fin de fichier réécrite pour refléter que le point 12 a été
  entièrement traité le soir même, pas reporté au lendemain comme
  anticipé.

`USER_MANUAL_COMPLET.md` mis à jour en place — deux nouvelles sections
détaillées en fin de fichier (`rapprocher_articles.py` et
`enrich_articles_pre_p20.py`), reprenant tout le raisonnement technique
et les découvertes de la soirée.

## 15. `rapprocher_articles.py` lancé sur le corpus complet — l'hypothèse `gelecek_meclisi` invalidée, constat plus large confirmé

Lancé en dry-run sur les 71 articles exploitables (tout le corpus, la
totalité étant désormais éligible depuis la clôture du point 12) :
262 tags distincts / 357 usages cumulés, 70/71 articles avec au moins
un lien trouvé, regroupements cohérents à l'examen. David a demandé
l'exécution réelle puis directement le mode `--stats`.

**Résultat majeur : l'hypothèse de la veille sur `gelecek_meclisi` est
invalidée.** Sur 71 articles (contre 7 hier soir), `breakdown` 30% et
`policy_reform` 33% — sous le seuil de 40%. L'omniprésence à 100%
observée hier était un artefact de petit échantillon, pas un signal
réel. Validation nette de la décision d'observer avant de corriger.

**Mais le mécanisme structurel soupçonné existe bel et bien — en plus
large que prévu.** `--stats` sur le corpus complet montre le même
mécanisme (spectre variables/zones large favorisant certaines instances
dans `filter_instances_for_thematique()`) sur **plusieurs entités
différentes, sur 5 des 6 scénarios** — pas un cas isolé de
`gelecek_meclisi`, un pattern de fond. Point notable relevé mais non
creusé : deux des entités récurrentes (`leena_vainala`, `amara_diallo_
nkosi`) sont des personnes, pas des institutions — cause potentiellement
différente, à diagnostiquer séparément.

**Bug repéré dans `--stats` en marge de l'analyse, non corrigé** :
aucun seuil minimum d'articles avant l'alerte — fausse `new_
sustainability` (1 seul article, "100%" mécanique sur toutes ses
entités).

David a demandé de tout documenter avant de passer à une autre session
plutôt que de qualifier/corriger ce nouveau constat dans l'immédiat —
voir `BACKLOG_MASTER_9_AOUT.md` Partie 1 point 9bis pour le détail
complet.

**Point resté ambigu à vérifier en ouverture de la prochaine session** :
l'exécution réelle (sans `--dry-run`) de `rapprocher_articles.py` a été
demandée mais n'apparaît pas explicitement confirmée dans l'historique
de conversation — `--stats` fonctionne indépendamment sur les
`entites_citees`/`tags` déjà en frontmatter (pas sur `articles_lies`
lui-même), donc son succès ne prouve pas que le run réel a eu lieu à
vérifier : `generator/tags_reference.yaml` existe-t-il sur le vault
réel, et le frontmatter contient-il bien `articles_lies` rempli ?

## 16. Point de reprise réel pour la prochaine session

1. **Confirmer l'exécution réelle de `rapprocher_articles.py`** (voir
   point 15 ci-dessus) — vérifier `tags_reference.yaml` et
   `articles_lies` en frontmatter avant toute autre action sur ce
   chantier.
2. **Qualifier le nouveau constat structurel** (point 9bis backlog) —
   plusieurs entités quasi-omniprésentes sur 5/6 scénarios, mérite une
   vraie session de discussion (défaut vs caractéristique voulue vs
   distinction institutions/personnes).
3. **Corriger le bug `--stats`** (seuil minimum d'articles avant
   l'alerte) si le point 2 est traité.
4. **P25** — continuer à observer, envisager la piste du pattern `---`
   en fin de texte si le taux se confirme sur un futur batch.
5. Reste inchangé : points 3 (P17), 4 (Bug #27), 5 (renommage YAML), 6
   (troncatures JSON), 7 (P21/P14), 8 (GUI `promote_ville.py`) — tous
   en attente sur décision explicite de David.

Rien en suspens de façon bloquante. Séance très longue mais tous les
chantiers ouverts ce soir ont été menés à leur terme, jusqu'à la
découverte d'un nouveau constat de fond documenté pour la prochaine
session plutôt que traité dans la précipitation.
