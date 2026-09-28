# HANDOFF — 28 septembre 2026

Suite de `HANDOFF_27_SEPTEMBRE.md`. Session consacrée à la veille « signaux
faibles » (concept d'Igor Ansoff) : chaîne web à coller dans les IA de
chat, lecture des livres par API, onglet de tri. En cours de route, deux
correctifs et un rangement de la veille « état du monde ». Chantier ouvert
et clos dans la session ; détail et justifications dans
`BACKLOG_ARCHIVE.md`, mode d'emploi dans `USER_MANUAL_COMPLET.md` §3quater.

## Fait
- **Veille signaux faibles, chaîne web** : `sources_signaux_faibles.yaml`
  (31 sources) → « 🔭 1. Préparer le prompt » (`export_prompt_signaux.py`,
  prompt collable, 📋/⬇) → une ou plusieurs IA → « 📥 2. Importer les
  réponses » (`import_signaux_faibles.py` : fusion entre IA, vérification
  des URL, écart automatique, rapprochement avec les veilles précédentes)
  → onglet « 🔭 Veille signaux faibles » (tri, mise en queue) → injection
  habituelle.
- **Définition stricte** dans les prompts (David) : observable, marginal ou
  incertain, transformateur par évolution ou combinaison ; 3 tests (+ un
  4e pour les livres) ; statistiques et classements exclus.
- **Livres par API** (`veille_livres_api.py` + `livres_veille.py`, bouton
  « 📚 Lire les livres (API) ») : « dépose et oublie » dans
  `documentation/livres/`, repérage des pages par le LLM (une fois par
  livre), lecture par rotation, citation exacte vérifiée, réponse
  `veille_signaux_reponse_livres.md` importée avec les autres. 7 documents
  lus chez David.
- **Veille état du monde** : correctif du « déjà connu » tronqué
  (`fin_situation`), import qui remplace toute la partie Situation,
  prompt collable (`copyable`), rangement dans
  `need_action/veille_etat_monde_reponses/` (réponse
  `veille_etat_monde_reponse.md`, `archive/`), migration automatique
  testée chez David. Veille réelle importée (12 sections), diff relu.
- **Sources** : lecture de Thorleuchter & Van den Poel 2015 et Jabbour et
  al. 2026 ; 9 bases de signaux ajoutées au YAML après la réflexion de
  David avec ChatGPT (URL vérifiées).
- `gui_verified: true` sur les trois entrées signaux faibles.

## Bugs trouvés
- Sous-variables prises pour des variables (DeepSeek, Mistral).
- Gemini : champs inventés, un `### FIN` par signal, 9 URL sur 10 en 404 ;
  Mistral : sources omises.
- Fichiers de réponse autrement nommés invisibles dans le GUI.
- Deux imports dans la même minute = même lot.
- « Déjà connu » tronqué à la fin (mouvements de fond perdus), dans les
  deux veilles.
- Livres : bibliographies puis tableaux en tête de la note ; statistiques
  prises pour des signaux ; 8 signaux sur 16 recopiés du « déjà connu »
  avec de fausses pages ; filtre `--livre` sans décodage de `%20`.
- Pas un bug : aperçu coché = fichier prompt non réécrit (Copier donnait
  l'ancien prompt).

## Décisions actées
- Mode par défaut = prompt collé dans l'IA de chat ; livres par API.
- Plusieurs IA fusionnées, doublons validés au tri (choix « a »).
- Candidats sans source valable : écartés à l'import, récupérables.
- Livres : pas d'entrée YAML (exceptions seulement), repérage LLM puis
  rotation ; « déjà connu » absent du prompt des livres.
- État du monde : même rangement que les signaux ; fusion multi-IA laissée
  de côté.
- Injection des signaux (6 scénarios obligatoires, intensité unique,
  jamais d'effet nul) : évolutions notées pour plus tard (S21).

## Reste à faire
- **S21** (nouveau) : voir le backlog — « sans suite » et intensité par
  scénario pour les signaux ; 32 pages JRC restantes ; PDF à déposer ;
  durcissement du prompt des livres ; options API web / RSS ; OCR ; fusion
  multi-IA de l'état du monde.
- **PDF repérés à déposer dans `documentation/livres/`** :
  - https://espas.eu/files/horizon/HorizonScanning_ESPAS_10.pdf (et
    numéros précédents, même modèle d'adresse)
  - https://publications.jrc.ec.europa.eu/repository/bitstream/JRC141934/JRC141934_01.pdf (Healing the Future)
  - https://publications.jrc.ec.europa.eu/repository/bitstream/JRC143535/JRC143535_01.pdf (Embodying the Future)
  - https://publications.jrc.ec.europa.eu/repository/handle/JRC139022 ((Dis)Entangling the Future)
  - https://publications.jrc.ec.europa.eu/repository/handle/JRC144401 (Observing the Future)
  - https://www.unep.org/resources/global-foresight-report (Navigating New Horizons)
  - https://reports.weforum.org/docs/WEF_Top_10_Emerging_Technologies_of_2025.pdf
  - https://www.un.org/scientific-advisory-board/sites/default/files/2026-03/260115_Executive%20Report%20-%20Horizon%20Scanning%202026.pdf
- Retirer du dossier des livres l'erratum `s11625-026-01828-6.pdf` si ce
  n'est pas déjà fait.
- Hérité : #3 P20 (service d'image), S18, S19, S20, S15.

## Fichiers livrés
- **Nouveaux** (`generator/`) : `export_prompt_signaux.py`,
  `import_signaux_faibles.py`, `veille_livres_api.py`, `livres_veille.py`,
  `sources_signaux_faibles.yaml` ; (`gui/`) `routes_veille_signaux.py`.
- **Modifiés** : `export_prompt_veille.py`, `import_veille_etat_monde.py`,
  `gui/app.py` (2 lignes : blueprint), `gui/static/app.js` (onglet 🔭,
  `copyable`), `gui/templates/index.html`, `gui/scripts_config.json`.
- **État** : `state/veille_signaux.json`, `state/livres_veille.json`.
- `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`, `USER_MANUAL_COMPLET.md`
  (§3quater, routes, `copyable`), `USER_MANUAL_HISTORIQUE.md`, ce handoff.

## Non traité hérité
S1-S10, S14 inchangés (voir backlog).
