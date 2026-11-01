# HANDOFF — 31 octobre 2026

Suite de `HANDOFF_30_OCTOBRE.md` (dont le « reste à faire » documentaire a été
fait en début de séance). Décision de méthode : **l'outil d'abord** (toutes les
fonctionnalités, aucun bug connu), l'enrichissement de la base ensuite. Séance
consacrée aux bugs de code : tous les bugs connus sont corrigés et commités ; le
backlog est réorganisé en trois parties (bugs / développement / enrichissement).
Base valide (0 erreur, 0 avertissement), site republié.

## Fait
- **S24 — bloc `===METADONNEES_PUBLICATION===` resté dans un article** (`8aeb5af`).
  Cause probable : la regex d'`api.py` exigeait le marqueur de fin ; une réponse
  tronquée (`MAX_TOKENS`) ou un bloc non fermé — risque accru au retry de longueur,
  qui réécrit tout l'article — restait entier dans le texte, et le retry des
  métadonnées travaillait ensuite sur ce texte. Aucune trace de l'article réparé
  (pas de `.bak_meta`) : correctif préventif.
  - `patch_s24_bloc_metadonnees.py` : fin facultative (bloc pris jusqu'à la fin du
    texte), toutes les occurrences retirées, avertissements console.
  - `patch_s24b_bloc_tronque.py` : bloc sans fin ET incomplet → champs partiels
    jetés, le retry ciblé redemande le bloc (sinon chapô coupé publié).
- **S24 — `generate_journaux.py`** (`patch_s24_journaux_fallback.py`, commité).
  Bug plus grave que noté : un lot au JSON cassé écrivait « Édition <zone> » vide ;
  en `--update` la zone passait pour présente (jamais régénérée), et **en mode
  complet elle écrasait un bon journal**. Désormais : aucune entrée factice (zone
  ratée absente, listée, reprise par `--update`) ; parse JSON tolérant (texte
  autour, virgules finales, entrées complètes d'une réponse tronquée) ; zones
  manquantes retentées une fois seules ; réponse illisible dans
  `gui/logs/llm_json_echec_journaux_*.txt` ; `journaux.yaml.bak` avant écriture ;
  compte réel en `--fill-journalistes`. Refus du nom factice limité au motif exact
  « Édition <nom de la zone> » (un vrai journal peut s'appeler « Édition Andine »).
- **S20 — reprise d'injection et exception** : le point du backlog était caduc,
  `patch_s22_exception_signal.py` (5 oct) le couvre déjà. Trou voisin trouvé et
  corrigé (`19e7e53`, `patch_s20_interruption_signaux.py`) : `queue.yaml` n'était
  réécrite qu'en fin de run → après une interruption, idées déjà traitées
  retraitées, slug suffixé `_2`, **signal injecté en double** ; et Ctrl-C (pas une
  `Exception`) contournait la restauration S22. Désormais : file réécrite après
  chaque idée ; interruption pendant une variable → écriture annulée, variables
  restantes « interrompu », fiche d'audit et `idee_a_remettre_en_queue` produites,
  arrêt code 130 ; SIGTERM (Stop du GUI) = Ctrl-C.
- **S24 — slugs (ø, æ, œ, ß, ł, đ, ı → `_`)**. Constat : 10 copies de la fonction
  (pas seulement `api.py`), toutes fautives sauf `export_revues.slugify()` ; å était
  déjà bien traité. `export_revues.slug_pipeline()` et `reattribuer_signatures.py`
  recopient exprès `api._slugify` : corriger `api.py` seul aurait cassé le
  rattachement des journalistes sur le site.
  - Étape 1 (`68d3d23`) : module commun **`generator/slugs.py`** ; les 9 copies y
    délèguent (`patch_s24_slugs_unifies.py`, par AST, signature gardée).
  - Audit (`audit_slugs_s24.py`, lecture seule) : 44 noms concernés dans le lore,
    7 slugs réellement abîmés (4 entités, 3 instances), 36 slugs choisis autrement.
  - Étape 2 (`migrer_slugs_s24.py`, commité) : 4 entités et leurs 4 instances
    renommées, 9 slugs d'articles, 18 journalistes ; 472 remplacements dans
    144 fichiers (wikilinks, `entites_citees`, `developpements`, inventaires,
    caches `generator/state/` et `rejeu/`) ; `documentation/Old/` exclu
    (archives). `validate.py` : 0 erreur. Site republié.
- **S23 — trois sources des noms de réseaux** : `journaux.yaml` et
  `generate_journaux.RESEAUX` identiques par construction (`_reseau` réécrit à
  chaque run) ; `JOURNAL_PROFILES` ne donne son nom qu'au chemin 3 (yaml absent).
  Seule divergence : « L'Ordre du Territoire » → « L'Ordre Zonal ». Défaut réel :
  posture fortress_world pro-pouvoir « organe officiel du Bloc
  Atlantique-Méditerranéen » appliquée à toutes les zones au chemin 2 → « organe
  officiel du bloc dont relève la zone » (`patch_s23_profils_reseaux.py`, commité).
- **Documentation** : backlog réorganisé en A (bugs et vérifications), B
  (développement), C (enrichissement), numéros de chantier conservés.

## Bugs trouvés
- Les cinq ci-dessus (bloc métadonnées, fallback factice qui écrase, doublon de
  signal après interruption, slugs sur 10 copies, posture de bloc).
- Procédure : `mv … && migration --apply …; validate` — le `mv` a échoué (fichier
  déjà déplacé à la main), la chaîne s'est arrêtée, `validate.py` a tourné sur la
  base non migrée et le premier commit ne contenait que le code. Leçon : lire la
  sortie de chaque étape (ici « Aperçu seulement ») avant de commiter.
- `audit_slugs_s24.py` : faux positif `tromsoe_aln` (correct).

## Décisions
- **Outil d'abord** : partie A du backlog vide avant l'enrichissement en volume.
- **Slug unique** : tout calcul de slug passe par `generator/slugs.py` ;
  `export_revues.slugify()` (URL du site) reste à part.
- Les migrations n'écrivent pas dans `documentation/Old/` (archives historiques).
- Sorties à transmettre : sur le Bureau (`> ~/Desktop/<nom>.txt 2>&1`), pas `/tmp`.
- Tests réels de S30 : branche jetable `test-s30` avec les deux exemples à ne
  jamais adopter — **reporté** à une prochaine séance.

## Reste à faire
- Placer `BACKLOG_ACTIF.md` et `HANDOFF_31_OCTOBRE.md` dans `documentation/` ;
  **ajouter** (sans réécrire) `ADDENDUM_BACKLOG_ARCHIVE_31OCT.md` à la fin de
  `BACKLOG_ARCHIVE.md` ; lancer `patch_docs_manuel_31oct.py --apply` ; commiter.
- Partie A1 du backlog : tests réels S30 sur branche `test-s30`.
- Puis partie B (développement) selon priorité de David, ou C1 (volume par revue,
  plancher 15 conseillé).

## Fichiers livrés (31 oct)
- Code (dans `generator/`, appliqués et commités) : `patch_s24_bloc_metadonnees.py`,
  `patch_s24b_bloc_tronque.py`, `patch_s24_journaux_fallback.py`,
  `patch_s20_interruption_signaux.py`, `slugs.py`, `patch_s24_slugs_unifies.py`,
  `audit_slugs_s24.py`, `migrer_slugs_s24.py`, `patch_s23_profils_reseaux.py`.
- Documentation : `BACKLOG_ACTIF.md`, `HANDOFF_31_OCTOBRE.md`,
  `ADDENDUM_BACKLOG_ARCHIVE_31OCT.md`, `patch_docs_manuel_31oct.py`.
- Sauvegardes : `_backups/migration_slugs_s24_<date>/`, `*.bak_s24slug`,
  `api.py.bak_*`, `generate_journaux.py.bak_*`, `inject_custom_signals.py.bak_*`,
  `prompt_builder.py.bak_*`.

## Rappels
- Après tout changement de propagation ou de réglage du moteur :
  `mesure_niveaux.py --sauver <fichier>` puis `--comparer <fichier>`.
- Après un changement de `gui/app.py` : redémarrer Flask entièrement.
- `validate.py` : `> ~/Desktop/validate.txt 2>&1; tail -3 ~/Desktop/validate.txt`.
