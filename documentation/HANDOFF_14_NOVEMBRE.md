# HANDOFF — 14 novembre 2026 (fin de séance)

Chantier **unification** : « et si ? » est maintenant la **porte unique** de tous les
éléments qui s'ajoutent au monde — événements, signaux **et entités**. Les quatre entrées
(« Nouvelle hypothèse », veille 🔭, onglet Articles, « Lecture IA » de l'étape ⑤) créent
une hypothèse dans `et_si/hypotheses.yaml` ; les accès directs sont fermés et le code mort
est retiré. Séance de la journée entière : patchs **U3aa → U3bf**. Dépôt : tout est commité
(dernier commit `3ae0304`, U3aq → U3bf) ; **rien n'est poussé** (décision de David). Il reste à
**commiter les 4 documents** (ce handoff, `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`,
`USER_MANUAL_COMPLET.md`). Décision de méthode inchangée : l'outil d'abord, l'enrichissement
ensuite.

## Fait

**Événement tiré d'un article : la fiche n'invente plus** (B9 « source mince »)
- **U3aa** : pour un événement d'article, `realisation` et `description_complete` = la
  description de l'hypothèse (tirée de l'article) ; l'IA n'écrit plus ces champs ;
  `consequences` = formule fixe ; `note_coherence` = renvoi à l'article + citation ;
  `date_label` = l'année seule sauf mois/saison présents dans l'article. Contrôle ⚠ (sans
  IA) des noms propres et sigles absents de l'article et des noms du vault. **U3ab** :
  `nom` et `evenement_cle` qui s'écartent de la description sont reformulés (jamais
  bloquant au dernier essai). **U3ac** : le fait `[ARTICLE]` n'est plus contrôlé (il l'était
  sur un récit remplacé : réécritures inutiles).
- **U3ad** : dates 2098.xx dans la Passe exhaustive et la Lecture IA (date de mesure ramenée
  à 2098.12 en ligne de commande, événement « 2098 » relu, dates écrites « mars 2098 »).

**Panneau « Et si ? »**
- **U3ae** titres/messages (« Faits imposés au récit du signal », étape ④ sans opération :
  quoi faire) ; **U3af** pour un signal : options payantes grisées, étapes ④ et ⑤ masquées
  (parcours en 3 étapes) ; **U3ag** l'étape ⑤ n'avait pas disparu : elle apparaît après
  « Appliquer » (dit dans le panneau) ; l'alerte « sans passe exhaustive » devient une
  information.
- **U3at → U3av** : sous la liste « Hypothèse » du mode Simuler, un encadré « 📄 Description
  de l'hypothèse » (nom, type, date, catégorie, scénarios, rôle, état, description). Route
  `/api/et_si/fiche` (lecture directe, instantanée). Le volet flottant de U3au est remplacé.
- **U3ap** : menu regroupé — ① Ajouter au monde (« Simulateur « et si ? » » + « Outils
  directs (ancien, avancé) » replié), ② Sources (Veille 🔭 + 6 outils monde réel), …,
  ④ Entretien (replié). Aucun script ne disparaît.

**Entités dans « et si ? »** (option A : pas de simulation chiffrée)
- **U3ah** `create_entities_and_instances.py` : slug déjà pris → refus mécanique avant tout
  appel IA ; « doublon détecté » non corrigeable ; mode `--idea '<json>'` (une idée, sans
  `queue.yaml`). **U3aj** type `entite` (bloc : id, nom, description, categorie,
  scenario_ref, role, etat, annee_debut, scenarios) ; **U3ak** contrôle des doublons à
  l'étape ① (erreur : slug existant ou même nom à l'article près ; ⚠ : entités proches) ;
  **U3al** parcours vérifié → adopter → injecter (aucune file) ; **U3am** correctif ancien :
  une idée sans `etat` ne produit plus `etat_ref: None` (la contrainte dure du scénario de
  référence faisait échouer l'instance) ; **U3an** panneau GUI (frise à 3 étapes) ;
  **U3ao** liste « … (entité) ».
- **U3aw** `annee_debut` (optionnel, 2026-2098) : l'entité garde sa date de naissance ;
  contrainte dure dans le scénario de référence, consigne de cohérence dans les autres ;
  la fiche mémorise `annee_ref`. Vérifié en réel (2068-2070).
- **U3ax** `et_si_supprimer.py` : supprime des hypothèses d'entité non injectées (11
  supprimées pour être régénérées avec la date). **U3ba** : après l'injection d'une entité,
  l'extraction de localisation est relancée une fois si elle a échoué, sinon ⚠ explicite.
- **U3bb** « 📦 Traiter plusieurs entités d'un coup » (adopter + injecter la sélection,
  une par une, ≈ 6-8 min chacune) ; **U3bc** n'affiche plus les ⚠ sans gravité. Utilisé en
  réel : 2 entités injectées d'un coup.
- **U3be** les entités proposées par la **Lecture IA** (étape ⑤) deviennent des
  **hypothèses d'entité** (sans appel IA : rôle et raison repris tels quels), au lieu
  d'être écrites dans `entites_custom/queue.yaml` ; l'onglet **Articles** a un 3e choix
  « comme entité » (on écrit le nom et ce que l'article en dit). Essayé en réel.

**Suggestions à partir des lacunes** (remplacent les modes Auto, gardés dans « Outils
directs »)
- **U3aq** bloc « 💡 Suggestions à partir des lacunes » dans « Nouvelle hypothèse »
  (événements ou entités, un appel IA, n'écrit rien) ; **U3ar/U3as** « Traiter les N en
  lot » : Proposer puis Ajouter si le bloc n'a ni erreur ni avertissement ; les idées à
  problème restent avec leur motif (« Ouvrir pour corriger ») ; **U3ay** les suggestions
  portent une année (événements) / `annee_debut` (entités). Essayé en réel : 5 entités
  ajoutées d'un coup sans problème.
- **U3bd** (suggestions de **signaux**) : écrit et testé sur copie, **jamais appliqué** :
  la veille 🔭 couvre déjà ce besoin (règles de couverture, « déjà connu », sources réelles).

**Fermeture et nettoyage (étape 5)**
- **U3ai** : accès directs fermés (code mort Articles/veille supprimé, route d'injection
  directe en 410). **U3bf** : les deux routes `/api/edition/articles` et
  `/api/edition/injecter_evenement` sont retirées ; commentaire périmé remplacé.
- **Double-clic à la place de `confirm()`** (bloqué dans le navigateur de David : le clic ne
  faisait rien) : **U3az** (Injecter, Annuler la décision) puis **U3bf** (Adopter, Appliquer,
  9 actions de l'étape ⑤, « Remettre à trier » de la veille, « Utiliser cette idée »,
  « Proposer » quand un texte est déjà saisi). Vu en réel : « Adopter » (une hypothèse
  adoptée puis annulée).

**Tests réels de la journée** : 3 entités injectées de bout en bout (Dr Ananya Rao,
Gouvernance IA de l'Archipel pétrolier, Territoire autonome de Karachi-BioSyn : 6 instances
chacune) ; localisation complétée (`extract_localisation.py --scan-pending` vide) ;
Lecture IA → hypothèse d'entité (`alliance_des_territoires_froids_europeens`, ajoutée, **non
adoptée**) ; Articles → entité : proposition valide et vérifiée (non ajoutée).

## Bugs / constats de la séance
- **`confirm()` bloqué** : le lot (U3ar) et « Injecter » ne faisaient rien, sans message.
  Corrigé par le double-clic (U3as, U3az, U3bf). Les `confirm()` restants (onglets Carte,
  Lore, Chantiers…) sont inchangés : un bouton muet = probablement un `confirm()`.
- Entité « créée en 2082 » datée 2026-2028 : la date n'était transmise à aucune étape (U3aw).
- Extraction de localisation en échec sur une instance sans message (U3ba).
- Lot : lignes ⚠ sans gravité affichées comme « à voir » (U3bc).
- Bug **latent** (non corrigé) : `hypothese_depuis_texte.normaliser_entite`, branche
  `except ValueError` de `annee_debut` : l'instruction `h[cle] = v` y réutilise les variables
  de la boucle précédente (pose `etat` à la dernière valeur lue). Sans effet tant que
  `annee_debut` est un entier ; à retirer au prochain passage.
- L'annulation d'une entité **déjà injectée** ne l'enlève pas du vault (message ⚠) :
  `undo_custom.py` pour l'enlever ; `et_si_supprimer.py` refuse une entité injectée.
- Outils appelés en sous-processus : pas de relance de Flask (sauf `app.py` modifié).

## Décisions
- **Quatre sources, une seule porte** : « Nouvelle hypothèse » (avec suggestions), veille 🔭,
  Articles (événement, signal, entité), Lecture IA (entités). Plus d'écriture directe dans les
  files par l'interface ; les flux de maintenance (`enrich_minimal.py`, …) restent hors
  dispositif. Les « Outils directs » restent repliés (sort à décider).
- Entités : option A, pas de simulation chiffrée ; test d'effet par « Simuler l'injection »
  puis « Tracer ». Une entité garde la date voulue par l'auteur (`annee_debut`).
- Modes Auto remplacés par des **suggestions** (idées d'abord, puis Proposer / Vérifier /
  Ajouter), traitées **en lot** quand elles sont propres ; adoption/injection en bloc
  seulement pour les **entités** (un événement ou un signal exige une simulation avant
  l'adoption).
- **Pas de suggestions de signaux** : la veille 🔭 est la source des signaux (U3bd non appliqué).
- David **ne relit pas** chaque fiche injectée depuis un article : l'invention est évitée par
  construction (U3aa : la fiche reprend la description de l'hypothèse).
- Lecture IA : ses entités passent par « et si ? » (plus de file) ; Articles : l'entité est
  nommée par l'utilisateur, pas détectée automatiquement.

## Reste à faire
Voir `BACKLOG_ACTIF.md` B9 et A1. Dans l'ordre conseillé :
1. **Modes automatiques + wild cards** (étape 3 de l'ordre) : les suggestions en sont la
   première moitié ; cadrer avec David la « wild card » (rupture à faible probabilité,
   impact majeur, injectée même si elle bouscule le lore).
2. **Éprouver en réel** : entité Articles → ajout → adoption → injection ; entité de la
   Lecture IA jusqu'à l'injection ; « Appliquer » et les boutons de l'étape ⑤ en double-clic ;
   un événement tiré d'un article avec la fiche U3aa (fidèle sans relecture ?) ; le chemin
   signal depuis un article.
3. **Source mince, suite** : anachronisme sans année (question dans `verifier_contraintes`),
   consigne « reprendre tels quels les chiffres des contraintes », refus des simples mentions
   à l'extraction, impacts jugés trop forts pour des faits locaux.
4. Décider du sort des **Outils directs** repliés ; bouton **« Modifier »** pour une hypothèse
   existante ; retirer le bug latent d'`annee_debut`.
5. **Pousser** (`git push origin main`) quand David le décide ; supprimer l'hypothèse d'essai
   `alliance_des_territoires_froids_europeens` si elle n'est pas voulue
   (`python3 generator/et_si_supprimer.py --id alliance_des_territoires_froids_europeens`).
Aussi : C1 plancher 15 vs 20 ; branches `test-s30` / `test-s30b` ; S21 « sans suite » et
`delta_level` par scénario.

## Fichiers livrés (dans `generator/`)
`patch_u3aa_fiche_depuis_article.py`, `patch_u3ab_titres_article.py`,
`patch_u3ac_pas_de_controle_article.py`, `patch_u3ad_dates_2098.py`,
`patch_u3ae_panneau_textes.py`, `patch_u3af_panneau_signal.py`, `patch_u3ag_etape5.py`,
`patch_u3ah_entites_doublons_idea.py`, `patch_u3ai_fermer_acces_directs.py`,
`patch_u3aj_type_entite.py`, `patch_u3ak_entite_doublons_etape1.py`,
`patch_u3al_entite_decider_injecter.py`, `patch_u3am_contrainte_dure_vide.py`,
`patch_u3an_gui_entite.py`, `patch_u3ao_liste_entite.py`, `patch_u3ap_menu_groupes.py`,
`patch_u3aq_suggestions_lacunes.py`, `patch_u3ar_lot_suggestions.py`,
`patch_u3as_lot_sans_confirm.py`, `patch_u3at_fiche_hypothese.py`,
`patch_u3au_fiche_volet_droit.py` (remplacé par U3av), `patch_u3av_fiche_pres_liste.py`,
`patch_u3aw_annee_entite.py`, `patch_u3az_confirmations_parcours.py`,
`patch_u3ba_localisation_apres_injection.py`, `patch_u3bb_lot_entites.py`,
`patch_u3bc_alertes_lot.py`, `patch_u3be_entites_vers_et_si.py`,
`patch_u3bf_nettoyage_et_confirmations.py`. Nouveaux scripts : `suggerer_lacunes.py` (remplacé
par la version U3ay), `et_si_lot.py`, `et_si_supprimer.py`. **Jamais appliqué** :
`patch_u3bd_suggestions_signaux.py` (livré, absent du dépôt ; à jeter ou garder). Sauvegardes
`.bak_<tag>` à côté de chaque fichier patché. Dernier commit : `3ae0304` (U3aq → U3bf).

## Rappels
- Relancer Flask entièrement après modif de `app.py` ; `app.js` seul : Cmd-Maj-R. Les
  scripts appelés en sous-processus (`et_si_*.py`, `suggerer_lacunes.py`, …) ne demandent
  pas de relance.
- Patchs : recevoir le `.py` prêt à placer dans `generator/`, dry-run par défaut, `--apply`,
  contrôles de syntaxe avec restauration, depuis la racine du vault. `node --check` échoue
  sur `||=` (Node ancien) : sans conséquence, le patch compare avec l'original.
- Une commande à la fois ; sorties dans `~/Documents/Ourrassol_sorties/<nom>.txt 2>&1`.
- Avant un commit : `python3 generator/validate.py` ; `git status` et `git add` nommément
  (jamais `git add -A`). Laissés volontairement hors commit : `documentation/need_action/
  localisation_review.md`, `generator/last_validated.json`, `documentation/Old/*`. git 2.17 :
  `git checkout -b`, pas `git switch`.
- Un bouton qui ne répond pas, sans message : soupçonner un `confirm()` bloqué
  (cf. `armer2()` dans `app.js`).
