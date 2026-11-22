# HANDOFF — 21 novembre 2026 (fin de séance)

Chantier **unification**, suite de l'étape 3 (wild cards) : restes faits, Passe lente résolue,
bouton « Modifier ». Patchs **U4d5, U4d6, U4g, U4e, LARGE3, U4h, U4h2**, tous appliqués.
Dépôt : le travail du 15 nov a été commité le matin (`b065fa1`) ; **cinq commits** dans la
journée, **tous poussés** (`main` = `origin/main`) : `8ef9ee0` (U4d5, U4d6, U4g), `9537bb6` (U4e),
`7327d2f` (Large 3), `dc33456` (U4h, U4h2, cache de la Passe). **Restent à commiter : ces 4
documents** (voir « Reste à faire » ①).

## Fait
- **U4d5** `patch_u4d5_scenarios_depuis_idee.py` (`hypothese_depuis_texte.py`) : la ligne
  « Scénarios : a, b. » d'une idée (⚡ ou 💡) est imposée à ✨ Proposer (⚠ « scénarios repris de
  l'idée ») ; forces par scénario limitées aux scénarios couverts. Vu en réel (Zéro-R).
- **U4d6** `patch_u4d6_contraintes_vides.py` (`hypothese_depuis_texte.py`) : contraintes réduites à
  une date (« En 2058. ») ou à « Scénarios : … » retirées, avec ⚠.
- **U4g** `patch_u4g_retirer_shackleton.py` : `shackleton_platinoides_2052` retirée de
  `hypotheses.yaml` (décision de David) ; 24 hypothèses ; rapport et caches gardés.
- **U4e** `patch_u4e_wild_card_etape5_badge.py` (`et_si_main.py`, `gui/app.py`, `gui/static/app.js`) :
  règle de lore « fait établi » proposée d'office à l'étape ⑤ pour une wild card ; badge ⚡ (liste
  et fiche). Testé sur copie ; GUI sans régression ; non vu en réel (plus de wild card).
- **Passe lente** : chiffrée depuis le cache (Shackleton ≈ 4 min par lot). Cause :
  **`mistral-large-latest` = Mistral Large 4** (modèle à réflexion), sans décision.
  **`patch_llm_large3.py`** (`llm_client.py`) : `strict`, `structured_strict`, `creative_souple` →
  `mistral-large-2512` (Large 3). Mesure (Passe `fusion_commerciale_2038`, reference, `--refaire`) :
  14 lots en **7 min 35 s** (≈ 28 s par appel). Parallélisme écarté.
- **U4h** `patch_u4h_modifier_hypothese.py` (`hypothese_depuis_texte.py` `--extraire` / `--remplacer`,
  `gui/app.py`, `gui/static/app.js`) : « ✏️ Modifier une hypothèse existante » (Charger, Vérifier,
  Remplacer à sa place, `.bak_remplacer`). Refus : id changé, hypothèse adoptée ou injectée.
  **U4h2** : bouton « Remplacer » grisé quand désactivé. Vus en réel.

## Constats
- **Alias de modèle** : un `-latest` peut changer de modèle seul. Les tiers « large » sont fixés ;
  `mistral-small-latest` (tier `volume`) reste un alias. Les articles du 14 au 21 nov ont pu
  sortir de Large 4.
- **Contre-lecture de la Passe** (fusion, Large 3) : 2 obligatoires confirmés, discutables
  (« chronologie » : Crise des Détroits de juin 2038 ; « invention » : « pénuries résolues dès
  2050 ») ; 176 fiches en possible. En surveillance (A2).
- Le Zéro-R proposé par ✨ Proposer garde la **même force** dans ses deux scénarios (B9 a).
- Signal `remboursement_chatbots_therapeutes_2040` : « adopté, absent de la queue » (A2).
- Le cache `generator/state/et_si_exhaustif.json` de fusion a été refait (commité dans `dc33456`).

## Reste à faire (ordre conseillé)
1. **Commiter les 4 documents** (après `python3 generator/validate.py` et `git status`, fichiers
   nommés) : `documentation/BACKLOG_ACTIF.md`, `documentation/BACKLOG_ARCHIVE.md`,
   `documentation/USER_MANUAL_COMPLET.md`, `documentation/HANDOFF_21_NOVEMBRE.md`, et la
   suppression de `documentation/HANDOFF_15_NOVEMBRE.md` (rangé dans `documentation/Old/`).
2. **Wild card de bout en bout sur une branche jetable** (A1, décision du 21 nov : injecter une
   wild card change le lore) : `git checkout -b test-u4`, Zéro-R (⚡ coché), simuler (≈ 15 min),
   adopter, injecter, ④, ⑤ (règle « fait établi », badge ⚡), `validate.py` ; puis
   `git checkout main` et `git branch -D test-u4` (vérifier que `main` est propre avant).
3. **B9, suite** : forces par scénario dans ✨ Proposer ; « Outils directs » (garder ou retirer) ;
   consigne « chiffres des contraintes tels quels » ; « source mince, suite ».
4. Trancher le signal `remboursement_chatbots_therapeutes_2040` (injecter ou rejeter).

## Rappels
- Relancer Flask entièrement après modif de `app.py` ; `app.js` seul : Cmd-Maj-R. Les scripts en
  sous-processus ne demandent pas de relance.
- Patchs : `.py` prêt dans `generator/` (vérifier le nom : pas de « (1) »), dry-run par défaut,
  `--apply`, sauvegardes `.bak_<tag>`, depuis la racine du vault.
- Une commande à la fois ; sorties dans `~/Documents/Ourrassol_sorties/<nom>.txt 2>&1`.
- Avant un commit : `validate.py`, `git status`, `git add` nommément (jamais `-A`). Hors commit :
  `documentation/need_action/localisation_review.md`, `generator/last_validated.json`,
  `documentation/Old/*`. git 2.17 : `git checkout -b`.
- Modèles : version explicite dans `TASK_TIER_DEFAULTS` ; vérifier les alias avec
  `python3 -c "import os; from mistralai import Mistral; c = Mistral(api_key=os.environ['MISTRAL_API_KEY']); [print(m.id, m.aliases) for m in c.models.list().data if 'large' in m.id or 'small' in m.id]"`.
- Modifier une hypothèse déjà simulée : la **resimuler** avant d'adopter (l'adoption refuse sinon).
