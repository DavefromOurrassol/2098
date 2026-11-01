# HANDOFF — 31 octobre 2026 (journée complète)

Remplace la version du matin. Séance de nuit / matin : bugs de code (S24, S20,
S23), backlog réorganisé en A / B / C. Après-midi : tests réels de S30 (partie
A1) sur branche jetable, cinq défauts trouvés et corrigés. Décision de méthode
inchangée : **l'outil d'abord** (partie A vide), l'enrichissement ensuite. Base
valide sur `main`, dépôt propre.

## Fait — nuit et matin
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

## Fait — après-midi
- **Rangement** : documentation du matin déjà en place et commitée (`129bedd`) ;
  `state/chapos_revues.json` (cache après migration des slugs) commité (`911f8ef`).
- **A1 — tests réels de S30** sur `test-s30` (créée par `git checkout -b` : git 2.17
  n'a pas `git switch`) :
  - `reunification_ecosse_2070` : ① sans IA, puis lecture IA + passe exhaustive
    (193 fiches, 0 obligatoire), ② aperçu puis Adopter (portée régionale, intensité
    modérée), ③ Liste de l'étape ④, Sauter 9,12, simulation d'injection puis
    injection (validate 0/0), ④ aperçu puis Appliquer, Carte : zone vidée gardée,
    *The Northern Caledonian* gardé en exil, *Fo Thuinn Alba* retiré ; ⑤ Remplacer /
    Ignorer. État figé par un commit jetable (`1bcedbd`).
  - `occupation_bresil_2029` : ① lecture + passe (205 fiches, 5 à corriger), ②
    (continentale, majeure), ③ Sauter 7 (fait et acteur retirés de l'entrée),
    injection, ④ (nouvelle zone `bresil_occupe`, 2 sous-zones rattachées,
    `sao_paulo_spaar` suit son parent), ⑤ « déplacer entière » le Bassin Amazonien.
  - Retour sur `main` : rien ne reste. Non couvert : fiches des entités disparues.
- **Cinq défauts corrigés** (patchs dans `generator/`, appliqués et commités) :
  1. événement resté dans la zone quittée → relocalisé après la carte
     (`patch_s30_relocaliser_evenement.py`, `3ff62d7`) ;
  2. faits imposés ignorés sans alerte (Écosse → UOC au lieu du Royaume-Uni) →
     vérifiés par l'IA à l'injection, une réécriture puis ⚠
     (`patch_s30_faits_contraintes.py`, `7ef4462`) ;
  3. citations réécrites par la passe (3 phrases « introuvables » à ⑤ ; contrôle
     sur 120 caractères) → extrait entier, sinon vraie phrase et possible
     (`patch_s30_extrait_exact.py`, `3e01837`) ;
  4. réciprocité non annoncée (fiche hors hypothèse modifiée) → bloc
     « Réciprocité » dans l'aperçu ④ (`patch_s30_apercu_reciprocite.py`,
     `e773378`), aligné sur `--ignorer-exclus` (`patch_s30_reciprocite_exclus.py`,
     `c1db74b`) ; validé sur le vrai vault ;
  5. affichage : titres en double « « », libellé « passe exhaustive », sous-zones
     rattachées (`patch_s30_affichage.py`, `64b4027`).
- **Documentation** : backlog (A1 réécrit, A2 et A3 complétés, C4 relations à sens
  unique, routines), archive (section « Clos le 31 octobre 2026 » complétée),
  manuel (§0 conventions, §3 faits imposés, §3quinquies passe, ③, ④, essai sans
  garder) — versions complètes, remplacent les anciennes.

## Bugs trouvés
- Nuit et matin : les cinq bugs de code ci-dessus (bloc métadonnées, fallback factice qui écrase, doublon de
  signal après interruption, slugs sur 10 copies, posture de bloc).
- Procédure : `mv … && migration --apply …; validate` — le `mv` a échoué (fichier
  déjà déplacé à la main), la chaîne s'est arrêtée, `validate.py` a tourné sur la
  base non migrée et le premier commit ne contenait que le code. Leçon : lire la
  sortie de chaque étape (ici « Aperçu seulement ») avant de commiter.
- `audit_slugs_s24.py` : faux positif `tromsoe_aln` (correct).
- Après-midi : les cinq défauts S30 ci-dessus. Tests sur vault factice (1),
  IA simulée (2), phrases réelles (3), vrai vault (4).
- `git switch` et `git branch --show-current` absents (git 2.17) : première
  tentative de branche sans effet, vérifiée avant de continuer.

## Décisions
- **Outil d'abord** : partie A du backlog vide avant l'enrichissement en volume.
- **Slug unique** : tout calcul de slug passe par `generator/slugs.py` ;
  `export_revues.slugify()` (URL du site) reste à part.
- Les migrations n'écrivent pas dans `documentation/Old/` (archives historiques).
- Tests réels de S30 : branche jetable `test-s30` avec les deux exemples à ne
  jamais adopter — faits l'après-midi.
- « émergent → déclinant » reste non signalé à l'étape ④ (échec précoce plausible).
- Contrôle des faits imposés par appel IA (≈ 1 centime par scénario), pas par
  mots-clés (un sens d'évolution inversé n'est pas un mot absent).
- Commandes sans `cd` (lancées depuis la racine du vault) ; sorties dans
  `~/Documents/Ourrassol_sorties/`.
- Documents de fin de séance livrés complets (pas d'addendum).

## Reste à faire
- Remplacer dans `documentation/` : `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`,
  `USER_MANUAL_COMPLET.md`, `HANDOFF_31_OCTOBRE.md` ; commiter ; `git push origin main`
  (14 commits locaux avant les documents).
- A1 : test réel des fiches d'entités disparues (hypothèse où une entité meurt) ;
  observer en réel la relocalisation et le contrôle des faits imposés.
- Supprimer `test-s30` quand plus utile (`git branch -D test-s30`).
- Puis partie B (développement) selon priorité de David, ou C1 (volume par revue,
  plancher 15 conseillé).

## Fichiers livrés (31 oct)
- Code (dans `generator/`, appliqués et commités) : `patch_s24_bloc_metadonnees.py`,
  `patch_s24b_bloc_tronque.py`, `patch_s24_journaux_fallback.py`,
  `patch_s20_interruption_signaux.py`, `slugs.py`, `patch_s24_slugs_unifies.py`,
  `audit_slugs_s24.py`, `migrer_slugs_s24.py`, `patch_s23_profils_reseaux.py`.
- Documentation du matin (remplacée par les versions complètes du soir) :
  `ADDENDUM_BACKLOG_ARCHIVE_31OCT.md`, `patch_docs_manuel_31oct.py`.
- Sauvegardes : `_backups/migration_slugs_s24_<date>/`, `*.bak_s24slug`,
  `api.py.bak_*`, `generate_journaux.py.bak_*`, `inject_custom_signals.py.bak_*`,
  `prompt_builder.py.bak_*`.
- Après-midi (dans `generator/`, appliqués et commités) :
  `patch_s30_relocaliser_evenement.py`, `patch_s30_extrait_exact.py`,
  `patch_s30_apercu_reciprocite.py`, `patch_s30_reciprocite_exclus.py`,
  `patch_s30_faits_contraintes.py`, `patch_s30_affichage.py`.
- Sauvegardes : `appliquer_et_si.py.bak_s30reloc` / `.bak_s30recip` /
  `.bak_s30exclus` / `.bak_s30affichage`, `et_si_exhaustif.py.bak_s30extrait`,
  `inject_custom_events.py.bak_s30faits`, `simuler_et_si.py.bak_s30affichage`.
- Documentation (complète) : `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`,
  `USER_MANUAL_COMPLET.md`, `HANDOFF_31_OCTOBRE.md`.

## Rappels
- Après tout changement de propagation ou de réglage du moteur :
  `mesure_niveaux.py --sauver <fichier>` puis `--comparer <fichier>`.
- Après un changement de `gui/app.py` : redémarrer Flask entièrement.
- `validate.py` : `python3 generator/validate.py > ~/Documents/Ourrassol_sorties/validate.txt 2>&1; tail -3 ~/Documents/Ourrassol_sorties/validate.txt`.
- Commandes depuis la racine du vault, sans `cd` ; git 2.17 : `git checkout`, pas `git switch`.
