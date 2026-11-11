# HANDOFF — 11 novembre 2026 (fin de séance, soir)

Chantier **unification** : « et si ? » devient la porte unique de tous les éléments
(événements, signaux, entités). Le chemin **Articles → « et si ? »** est éprouvé en réel
sur **cinq événements** d'un même article (new_sustainability, « Genève,
ville-laboratoire… », 24 mars 2098) ; le chemin **signal** l'avait été le 7 nov depuis la
veille 🔭. Le soir : extracteur filtré mécaniquement, et **passage de l'article transmis à
l'IA d'injection** avec consignes de fidélité et contrôles. Base valide (`validate.py` :
0 erreur, 0 avertissement, 90 instances d'événements). Dépôt : tout le code et les données
sont commités (dernier commit `bfc8276`) ; **pousser** si ce n'est pas fait, puis commiter
les 4 documents. Décision de méthode inchangée : l'outil d'abord, l'enrichissement ensuite.

## Fait (11 nov, matin)
- **Test réel Articles → « et si ? »** : `piratage_ecrans_greffes_hepatiques_2098`
  (8 mars 2098) détecté, proposé, vérifié, ajouté, simulé, adopté, injecté ; fiche corrigée
  à la main (U3h).
- **U3e** date d'événement en année + mois (≤ 2098.12, jamais après l'article ; signaux
  entiers ≤ 2097). **U3f** bouton « 🔎 Détecter les événements de l'article ». **U3g**
  simulateur (mots génériques, date de mesure). **U3i + U3k** citation exacte = premier fait
  imposé. **U3j** sélection de texte dans le panneau. **U3l + U3m** note de cohérence en
  texte brut. **U3n** message « Fiches à relire ». **U3o** blocage des doublons.

## Fait (11 nov, soir)
- **Extracteur** (`extraire_evenements_article.py`) : **U3p** filtre mécanique (année
  postérieure à l'article, marqueurs de projet, plan / programme / débat sans fait
  accompli) ; **U3q** citations sans guillemets doublés ni astérisques ; **U3r** citations
  tronquées (« [...] ») et statistiques de tendance écartées ; **U3x** la règle plan /
  programme ne vaut que si la description commence par ce nom (« Lancement du programme
  Écoles Résilientes » n'est plus écarté), « réduction », « hausse »… ajoutés aux tendances.
- **Injection** (`inject_custom_events.py`) : **U3s** le passage de l'article (paragraphe de
  la citation + voisins, ≤ 2 800 car.) est retrouvé dans `articles/<scénario>/` et transmis
  au prompt (ligne `[contexte article]` dans le terminal de Flask) ; **U3t** description
  sobre, pas de paroles ni de citation ajoutées, ⚠ « citation absente de l'article » ;
  **U3w** fait de l'article marqué `[ARTICLE]` dans le contrôle des faits (omission = non
  respecté ⇒ réécriture), jamais le nom d'un scénario dans le texte, conséquences sans
  débat ni réaction inventés ; **U3y** l'événement raconté à sa date (pas de recopie du
  passage, ni fait postérieur, ni « aujourd'hui »), ⚠ anachronisme.
- **Tests réels** (une fiche par patch d'injection) : ouverture du dispensaire des Grottes
  (2042), arrestations au dispensaire (janvier 2098), accords OMS (2039), réaménagement du
  quai Wilson (2044). Chaque fiche corrigée à la main d'après l'article : **U3v**, **U3u**,
  **U3z**, **U3za** (ponctuels, à ne pas réutiliser).

## Bugs / constats de la séance
- **Source mince → invention** : quand l'article ne donne qu'une mention, l'IA remplit les
  3 à 5 lignes exigées par le schéma (quai Wilson : sigle APRC développé à tort en
  « Autorité Planétaire pour la Régénération Climatique », digues, port, migrations).
  Chaque consigne réduit le problème sans le supprimer. **Relire toute fiche injectée.**
- **Anachronisme sans année** non détecté (files d'attente de 2098 placées en 2044).
- **Omission** d'une issue (libération après pétition) non signalée avant U3w.
- **Localisation** : `extract_localisation.py` (mistral-small) a mis les Grottes (Genève)
  en `afrique_continentale` à cause de « communautés sahéliennes » (corrigé U3u).
- **Extracteur variable** : une détection sur deux tronque ou change un mot de la
  citation ; relancer suffit.
- **Rectificatif** : l'unité mobile, la fibrose pulmonaire, les greffes de peau et les UV
  résiduels sont bien dans l'article (grep initial au singulier) ; je les avais dits
  inventés pour la fiche de 2042. Leur retrait reste justifié (l'article les place en 2098).
- Cosmétiques laissés : libellé « écarté (plan / projet / débat) » pour une statistique ;
  « « « … » » quand le guillemet ouvrant n'est pas fermé dans la phrase ; titre = nom de
  fichier et ligne `---` dans le contexte U3s ; ancien nom d'affichage dans l'archétype
  des accords de 2039.
- Toujours vrai : étape ④ sans consigne quand Lecture IA / Passe exhaustive manquent ;
  **l'étape ⑤ n'apparaît plus dans l'interface** ; `node --check` échoue sur `app.js`
  (`||=`, Node ancien), sans conséquence.

## Décisions
- Règle d'Articles → « et si ? » : l'événement vient du **texte de l'article**, jamais libre ;
  daté au plus tard à la date de l'article ; date verrouillée sauf « forcer la date ».
- Doublons bloqués par défaut. Plage : événements ≤ 2098.12 ; signaux ≤ 2097.
- **Lecture IA inutile** pour un simple événement d'article (elle ne sert qu'à l'étape ④).
- Une fiche injectée depuis un article se **corrige à la main** d'après l'article (patch
  ponctuel) : ne garder que ce que l'article dit, à la date de l'événement.
- Arrêter d'empiler des consignes de prompt : la suite porte sur la cause (longueur exigée
  par le schéma) et sur des contrôles mécaniques.
- Fermer les accès directs **seulement à l'étape 5**. Ordre : entités dans « et si ? » →
  modes auto + wild cards → étape 5. Flux de maintenance des entités hors du dispositif.

## Reste à faire
Voir `BACKLOG_ACTIF.md` B9. Prochains points, dans l'ordre conseillé :
1. **Source mince** : longueur des textes proportionnelle au passage (vérifier d'abord ce
   qu'exige `validate_instance()`), contrôle mécanique des sigles et noms propres absents de
   l'article et des acteurs du vault ; éventuellement refuser les simples mentions.
2. Anachronisme sans année : question ajoutée à l'appel `verifier_contraintes` existant.
3. Vérifier Lecture IA et Passe exhaustive pour les dates 2098.xx (`et_si_exhaustif.py`).
4. Panneau « Et si ? » : étape ④ explicite, étape ⑤ à rétablir ou à retirer de la doc,
   options payantes grisées pour un signal, titre « Faits imposés à la lecture IA ».
5. Entités dans « et si ? », puis modes auto + wild cards, puis étape 5 (fermer les accès
   directs, supprimer le code mort).
6. Cosmétiques ci-dessus ; consigne « chiffres des contraintes tels quels » ; noms propres
   à plusieurs mots pour « Fiches à relire » ; veille : date d'observation imposée.
Aussi : impacts des événements tirés d'un article (6 variables, forces 15-22 pour des faits
locaux) à juger avant d'injecter en volume ; C1 plancher 15 vs 20 ; branches `test-s30` /
`test-s30b` ; S21 « sans suite » et `delta_level` par scénario.

## Fichiers livrés (séance du soir, dans `generator/`)
`patch_u3p_filtre_plans.py`, `patch_u3q_guillemets_citation.py`,
`patch_u3r_statistiques_citations_tronquees.py`, `patch_u3s_contexte_article_injection.py`,
`patch_u3t_sobriete_citations_article.py`, `patch_u3u_fiche_arrets_grottes.py` (ponctuel),
`patch_u3v_fiche_dispensaire_2042.py` (ponctuel), `patch_u3w_faits_article_sobriete.py`,
`patch_u3x_filtre_plans_precision.py`, `patch_u3y_evenement_a_sa_date.py`,
`patch_u3z_fiche_accords_2039.py` (ponctuel), `patch_u3za_fiche_quai_wilson_2044.py`
(ponctuel). Sauvegardes `.bak_<tag>` à côté de chaque fichier patché. Fichiers touchés :
`extraire_evenements_article.py`, `inject_custom_events.py`, 4 fiches `event_instances/`
(+ archétypes `evenements/`). Commits du soir : `4bed262`, `1a822ef`, `26e615f`,
`52000d5`, `bfc8276` (matin : `bdb35e1` … `022681b`).

## Rappels
- Relancer Flask entièrement après modif de `app.py` ; `app.js` seul : Ctrl-Maj-R. Les
  scripts appelés en sous-processus (`extraire_evenements_article.py`,
  `inject_custom_events.py`) ne demandent pas de relance.
- Patchs : recevoir le `.py` prêt à placer dans `generator/`, dry-run par défaut, `--apply`,
  `py_compile`, depuis la racine du vault (`python3 generator/patch_….py`).
- Une commande à la fois ; sorties dans `~/Documents/Ourrassol_sorties/<nom>.txt 2>&1`.
- Avant un commit : `python3 generator/validate.py` ; vérifier `git status` et ajouter les
  fichiers nommément (code, puis données) plutôt que `git add -A`. git 2.17 :
  `git checkout -b`, pas `git switch`.
- Vérifier qu'un détail d'une fiche vient de l'article : `grep -o -i -E "a|b"
  articles/<scénario>/<fichier>.md` (attention aux pluriels).
