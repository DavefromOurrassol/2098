# HANDOFF — 9 octobre 2026

Suite de `HANDOFF_6_OCTOBRE.md`. Session consacrée à **S22** (clos), à
l'évaluation de **Mistral Large 4** (non retenu par défaut) et au
**simulateur « et si ? » (S27)**, livré en v6 et testé sur deux hypothèses.

## Fait
- **S22 clos** : vraie injection (signal `reseau_mobile_decentralise_urgence`,
  3 variables). Exception capturée et écriture restaurée ; fence de
  `geopolitique_conflits.md` réparée (séquelle de l'ancien bug
  d'`undo_custom.py`) ; recopie des événements frères corrigée
  (`patch_s22_evenements_freres.py`) ; reprise réussie ; validate 0/0/0.
- **Mistral Large 4** branché (`patch_llm_large4.py`, sélecteur du GUI),
  testé sur un article : écriture plus propre, moins de vault, réflexion qui
  peut épuiser `max_tokens`, coût ×4 à ×7. Large 3 reste par défaut.
- **Crieur des Marges** : +2 articles (Sri Lanka, eco_communalism, test
  Large 3 / Large 4).
- **S27 — simulateur « et si ? »** : `generator/simuler_et_si.py` (v6) et
  `et_si/hypotheses.yaml`. Niveaux avec / sans, lecture IA contrôlée, aperçu
  de carte, faits imposés. Testé sur `invasion_bresil_2029` et
  `fusion_commerciale_2038`, 6 scénarios chacun.

## Décisions actées
- Large 3 reste le modèle de tous les tiers ; Large 4 pour essais seulement.
- Hypothèses du simulateur dans un fichier YAML éditable (`et_si/`, racine
  du vault) ; GUI plus tard.
- Le simulateur n'écrit jamais dans le vault ; l'application future passera
  par une liste de changements **validée à la main** (l'IA propose encore des
  rattachements géographiquement absurdes).
- Les propositions de carte de l'IA ne s'appliquent qu'aux scénarios sans
  bloc `geographie:` manuel.
- Partition des pays : prochaine session.

## Reste à faire
- **S27, suite** : 1) action « partition » (commencer par
  `grep -rn "portion" geographie/*.md | head -20`) ; 2) entrée GUI ; 3) mode
  « rupture » ; 4) liste d'application (phase 3).
- **Anomalies de données** à vérifier (S24) : Uruguay dans
  `espace_nord_americain_fragmente` (breakdown) ; Brésil dans deux zones N1
  (new_sustainability) ; Paraguay dans `sertao_nordeste_bresilien`
  (reference) ; doublons « Pacte / Consortium Amazônia Viva » (eco_communalism,
  reference) ; trajectoires « émergent » par défaut ; Sri Lanka sans instance
  localisée.
- **S19** : amplitude faible et pics lents relevés par le simulateur (voir
  backlog).
- Hérité : S23 séries ciblées (volume des revues), S25 mesure du cooldown
  Kharg-9, chantier 5, S28, S29 (Large 4 à rejuger).

## Fichiers livrés
- **Nouveaux (`generator/`)** : `simuler_et_si.py` (v6) ;
  `patch_s22_evenements_freres.py` et `patch_llm_large4.py` (déjà appliqués,
  refusent un second passage).
- **Nouveau (racine du vault)** : `et_si/hypotheses.yaml` (`.bak_fusion`,
  `.bak_tritium`, `.bak_v6`).
- **Modifiés** : `generator/inject_custom_signals.py` (`.bak_s22_freres`),
  `generator/llm_client.py` (`.bak_large4`), `gui/config.json`
  (`.bak_large4`), `variables/geopolitique_conflits.md` (`.bak_fence`),
  `signaux_custom/queue.yaml` (`.bak_reprise`, `.bak_reprise2`).
- **Créés à l'usage** : `generator/state/et_si_consequences.json` (cache),
  `generator/state/dernier_et_si.json`, rapports
  `documentation/need_action/et_si_*.md` et `impact_bascule_*.md`.

## Scripts ad hoc utiles (non livrés en fichier)
- Origine d'une fence manquante : pour chaque commit du fichier, compter les
  lignes `` ``` `` (`git show <c>:<fichier> | grep -c '^```'`) et repérer le
  passage d'un nombre pair à impair.
- Remettre une reprise de `needs_review.yaml` en queue : script Python qui
  prend la dernière entrée `idee_a_remettre_en_queue` de l'`id` voulu et
  réécrit `signaux_custom/queue.yaml` (avec `.bak`).
- Sur le Mac de David, `sed -i` sans suffixe échoue (sed BSD) : passer par un
  petit script Python.

## À reporter dans les documents vivants
Fait dans cette session : `BACKLOG_ACTIF.md` (S22 clos, S19, S23, S24, S27
réécrit, S29 ajouté), `BACKLOG_ARCHIVE.md` (S22, Large 4, S27 v1-v6),
`USER_MANUAL_COMPLET.md` (§0 et §7 Large 4, §1 `llm_client.py`, §3 S22 et
fences, §3quinquies simulateur), `USER_MANUAL_HISTORIQUE.md` (addendum du
9 oct).
