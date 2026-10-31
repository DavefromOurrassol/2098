# HANDOFF — 30 octobre 2026

Suite de `HANDOFF_25_OCTOBRE.md`. Le « reste à faire » du 25 était déjà fait
(commit `b94e897`). Séance courte : S19 (propagation des signaux faibles), puis
une série de petits chantiers. Base valide (0 erreur, 0 avertissement) ; deux
commits (`778af2c` S19, horodatages de `validate.py` compris ; `2148340`
petits chantiers).

## Fait
- **S19 — signaux faibles propagés par la matrice** :
  - Constat : 10 signaux, 22 entrées (une par variable visée), toutes à
    `propagation_via_matrice: false` ; aucune injection depuis le 25 oct, donc
    pas de recalage de `K_COUPLAGE`.
  - Lecture de `dynamique.py` : le drapeau est lu par entrée ; `true` = pleine
    force dans le couplage ; pas de propagation partielle (l'option « 30 % »
    demanderait du code) ; double comptage négligeable (≈ K × poids × criticité
    ≈ 5 % de l'écart voisin, avec retard).
  - Appliqué : les 22 entrées à `true` (`sed`, copie dans
    `/tmp/signaux_custom_avant_s19`) ; `patch_s19_signaux_propagation.py` passe
    la consigne d'`inject_custom_signals.py` à « toujours true » et ses deux
    défauts du code à `True`.
  - Mesure (`mesure_niveaux.py`, référence
    `documentation/niveaux_avant_s19_signaux.json`) : 62 niveaux sur 72 bougent,
    1,1 point au plus, dans le sens de chaque scénario (vers la crise en
    fortress_world / breakdown / reference, vers l'apaisement ailleurs).
  - Commentaire de `K_COUPLAGE` mis à jour (ρ ≈ 0,34 depuis le 25 oct).
- **S28.1 — `coupling_intensity` examiné** : lu par aucun calcul ni prompt
  (`loader.py` le charge, `snapshot.py` le transmet ; trois scripts ne font que
  contourner ses clés en wikilink) ; confirmé par les deux manuels. Donnée
  pourtant utile : liens marquants propres à chaque scénario, que la matrice
  commune n'a pas. Usages notés au backlog, rien de codé.
- **S21** : `patch_s21_prompt_livres.py` durcit le prompt d'extraction de
  `veille_livres_api.py` (recommandation de l'auteur ≠ observation ; grand
  programme d'État ≠ marginal). `verifier_flux_rss.py --apply` : 16 flux sur
  31 sources (1 nouveau écrit, `.bak` créé).
- **S20** : `patch_s20_yaml_append_entete.py` — `/api/yaml/append` garde
  l'en-tête de commentaires de `queue.yaml` (testé sur copie, pas encore en
  réel).
- **S24** : `reparer_bloc_metadonnees.py` → 0 article. Scan de géographie
  (`--all`) : 3 incohérences `origine_reelle` / parenté (voir Reste à faire).
- **S14** : les 2 alertes `sao_paulo_megapole` ont disparu.
- **S23** : audit des revues (216 articles) ; plancher 15 = 38 articles, 20 =
  75 ; chantier mis de côté, plancher non choisi.
- `.obsidian/graph.json` sorti du suivi git (`.gitignore` + `git rm --cached`).

## Bugs trouvés
- Aucun bug de code. `/api/yaml/append` effaçait l'en-tête parce que
  `yaml.safe_load` + `yaml.dump` perdent les commentaires (corrigé).
- `mesure_niveaux.py --sauver` exige un nom de fichier.
- `scan_geographie_complet.py` exige `--scenario` ou `--all`.
- `git add` d'un chemin ignoré fait échouer toute la commande : ne pas remettre
  un fichier déjà retiré par `git rm --cached`.

## Décisions
- **Les signaux faibles se propagent par la matrice**, toujours (option a) : un
  signal faible transforme par combinaison ; l'effet reste petit.
- Pas de recalage de `K_COUPLAGE` sans nouveau lot d'injections.
- `coupling_intensity` : gardé ; usage conseillé dans le prompt des articles ;
  usage dans le moteur rattaché à S28.2 (CIB).
- Les 3 incohérences de géographie relèvent du lore : notées en S24, pas
  traitées.
- S23 avant S28.2 (CIB demande une session dédiée).

## Reste à faire
- Placer `BACKLOG_ACTIF.md` et `HANDOFF_30_OCTOBRE.md` dans `documentation/` ;
  **ajouter** (sans réécrire) `ADDENDUM_BACKLOG_ARCHIVE_30OCT.md` à la fin de
  `BACKLOG_ARCHIVE.md` ; lancer `patch_docs_manuel_30oct.py --apply` sur
  `USER_MANUAL_COMPLET.md` ; commiter.
- S21 : trier les 10 candidats RSS dans l'onglet 🔭 (Wegovy, BCE faibles).
- S20 : vérifier l'en-tête de `queue.yaml` au prochain ajout depuis le GUI.
- S24 : trancher `hanse_baltique`, `la_haye_cour_internationale`,
  `almaty_zone_friction`.
- S23 : choisir le plancher (15 conseillé), vérifier les trois sources de noms
  de réseaux, lancer les séries ciblées.
- Chantiers suivants conseillés : S23, #5.1 (identités visuelles), S28.2 (CIB).

## Fichiers livrés (30 oct)
- Code : `patch_s19_signaux_propagation.py`, `patch_s21_prompt_livres.py`,
  `patch_s20_yaml_append_entete.py` (dans `generator/`, appliqués et commités) ;
  `patch_docs_manuel_30oct.py`.
- Données : `documentation/niveaux_avant_s19_signaux.json`.
- Documentation : `BACKLOG_ACTIF.md`, `HANDOFF_30_OCTOBRE.md`,
  `ADDENDUM_BACKLOG_ARCHIVE_30OCT.md`.

## Rappels
- Après tout changement de propagation ou de réglage du moteur :
  `mesure_niveaux.py --sauver <fichier>` puis `--comparer <fichier>`.
- Après un changement de `gui/app.py` : redémarrer Flask entièrement.
- `validate.py` : `> /tmp/validate.txt 2>&1; tail -3`.
