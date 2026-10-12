# HANDOFF — 11 octobre 2026

Suite de `HANDOFF_10_OCTOBRE.md`. Session entièrement consacrée au **simulateur
« et si ? » (S27)**, sous un angle nouveau : faire de la simulation la première
étape d'un **pipeline d'injection unifié** — « 1. je teste l'injection d'un
événement, 2. je décide si j'injecte ». Trois livrables : l'injection reprend
ce qui a été simulé (impositions), une **passe exhaustive** relit toutes les
fiches d'un scénario face à l'hypothèse, et un **banc de rejeu** évalue la passe
sans appel IA contre une liste de référence validée par David.

## Fait
- **Cadrage du pipeline** : deux options exposées, (a) injecter l'événement
  fidèle à la simulation, (b) appliquer aussi les conséquences cochées.
  Choix : **(a) d'abord, comme étape vers (b)**.
- **Impositions à l'injection** (`patch_s27_injection_imposee.py`,
  `inject_custom_events.py`, `.bak_imposee`, 1880 → 2046 lignes) : champs
  `impacts_imposes` ({scénario: [{variable, delta_level, duree, polarite}]}),
  `date_imposee`, `via_matrice_impose` dans une entrée de
  `evenements_custom/queue.yaml`. Contrôle avant tout appel IA (delta 1-25,
  polarité ±1, durée > 0, mêmes variables dans chaque scénario, date
  2025-2098 ; entrée invalide → `needs_review`, rien de corrigé en silence).
  Bloc « VALEURS IMPOSÉES » dans le prompt de l'étape 2 ; valeurs réappliquées
  après l'IA ; `edition_active` ignoré si la date est imposée ; `QUEUE_TEMPLATE`
  documenté. Vérifié par un `--dry-run` réel (invasion du Brésil).
- **Simulateur v8.15** (`patch_s27_v815.py`, `.bak_v815`) : l'entrée d'injection
  commune transmet forces, polarités, durées (`impacts_imposes`, tous les
  scénarios de l'hypothèse), date et propagation ; ⚠ si la simulation a été
  limitée par `--scenario` ou si une force dépasse le plafond (25) ; en mode
  rupture, seule la date est imposée ; l'étape « Élément » de la liste devient
  une vérification. Vérifié sur `et_si_invasion_bresil_2029.md`.
- **Passe exhaustive** — `generator/et_si_exhaustif.py` (nouveau, v1 → v9.5) :
  relit **toutes** les instances du scénario et les événements datés après
  l'hypothèse, par lots de 15, sans plafond de propositions, lecture seule
  (cache `generator/state/et_si_exhaustif.json`). Environ 0,05 à 0,11 $ par
  scénario ; contre-lecture et classement ≈ 1-2 centimes. Principales étapes :
  - v2-v5 : lien direct obligatoire (territoire, relation, variable ≥ 2 points),
    conditionnel écarté, extrait vérifié mot pour mot, lot coupé relancé en
    deux, fiches sans réponse redemandées, réponses hors du lot comptées à part ;
  - **v6** : **classer au lieu de filtrer** — chaque changement est
    « obligatoire » (la fiche devient fausse sans lui) ou « possible » (la fiche
    reste vraie) ; les contrôles mécaniques **rétrogradent**, ils ne suppriment
    plus ; verdict pour chaque fiche ;
  - **v7** : seule une **disparition** peut être une trajectoire obligatoire ;
    **contre-lecture** de chaque obligatoire par une question fermée
    (« incompatible ou non ? ») ; v7.1 : exemples neutres, argumentaire du
    proposant masqué ;
  - v8-v9.3 : possibles regroupés par fiche, **20 prioritaires choisis par
    l'IA** (un appel), les autres sur une ligne ; propositions bâties sur un
    fait inventé exclues de la priorité ; « douteux » sans le conditionnel ;
  - **v9.4** : lien territoire valable si la fiche est située dans un **lieu
    nommé par l'hypothèse** (cas Genève, hors carte) ; contre-lecture : **le
    passé ne change pas**, un **choc amorti** ne contredit pas un état tardif,
    ligne « effet résiduel » calculée ; verdicts en cache un par un ;
  - **v9.5** : la contre-lecture classe le fait invoqué **matériel / tendance**,
    le code rétrograde « choc amorti (< 25 % de la force initiale en fin de
    période) + tendance » ; elle voit le lieu (instance) ou la date (événement)
    de chaque fiche.
- **Export et banc de rejeu** : `generator/export_et_si.py` (nouveau) écrit
  `generator/state/export_et_si.json` (tous les couples hypothèse:scénario
  présents dans le cache, avec fiches, effets, lecture et cache) ;
  `generator/rejeu/` (nouveau : `rejouer.py`, `evaluer.py`, `reference.json`,
  `loader.py` et `llm_client.py` de rejeu, `LISEZMOI.md`) rejoue la passe sans
  IA et la note contre la référence.
- **Hypothèse ajoutée** : `destruction_geneve_2076` (breakdown, `carte: non`,
  deux contraintes, gouvernance +6) — cas à réponse connue d'avance.
- **Six cas passés** (v9.5) : invasion / fortress_world, fusion /
  policy_reform, peste / breakdown, extrême droite / new_sustainability,
  IA 60 % / eco_communalism, Genève / breakdown.

## Résultat (v9.5, banc de rejeu)
**Verdicts : 26/27 conformes**, priorités (indicatif) 4/6.

| Cas | Obligatoires | Lecture |
|---|---|---|
| Invasion du Brésil (2029) | 3 | ruptures avec le Pacte Vert (acte matériel) |
| Fusion commerciale (2038) | 3 | fiches qui supposent la rente des hydrocarbures |
| Peste (2043) | 1 | RPDA, faux positif toléré ; 140 possibles classés |
| Extrême droite (2034) | 0 | choc amorti, monde coopératif de 2098 intact |
| IA 60 % du travail (2040) | 1 | rupture durable : CRAD « algorithmes rares » |
| Destruction de Genève (2076) | 24 | 4 institutions genevoises et leurs alliances |

## Décisions actées
- Pipeline : **tester avant d'injecter** ; option (a) d'abord, puis (b).
- Ce qui a été simulé est **imposé** à l'injection ; l'IA d'injection ne rédige
  plus que le récit.
- La passe exhaustive fait partie de l'étape « tester », en option.
- **Critère unique** : « si on laisse la fiche telle quelle, un lecteur qui
  connaît l'élément y trouve-t-il une affirmation fausse ? » — oui :
  obligatoire ; non : possible. Rien n'est supprimé, tout est classé.
- Trajectoire obligatoire = disparition seulement ; un changement de degré est
  possible.
- Le passé ne change pas ; un choc amorti ne rend pas faux un état tardif, sauf
  fait matériel (destruction, morts, acte entre parties nommées, contraintes).
- Réponses de David servant de référence : extrême droite → institutions de 2098
  **compatibles** ; invasion → rupture Pacte Vert / Pacte des Forteresses
  **obligatoire** en 2098 ; RPDA → **pas obligatoire** ; Résidu de Genève →
  **obligatoire**.
- Classement des possibles : aide à la lecture, pas une décision ; on
  **arrête les réglages** (variable d'un passage à l'autre).
- Écart RPDA toléré (une proposition isolée ; une règle dédiée serait du
  sur-ajustement).
- Façon de travailler : **régler sur le banc de rejeu**, pas en relisant des
  rapports ; une consigne IA modifiée demande une relance réelle puis un export.

## Reste à faire
- **S27** (dans l'ordre proposé) :
  1. **Brancher la passe dans le simulateur** (`--passe-exhaustive`) :
     obligatoires dans la liste d'application, 20 possibles prioritaires en
     étapes facultatives, étapes marquées « passe exhaustive » ; entités les
     plus touchées en `acteurs_hint` (4 au plus) dans l'entrée d'injection.
     Les alliances rompues qui découlent d'une disparition (Genève : 24)
     gagneraient à être regroupées sous l'entité disparue.
  2. **Corriger le ⚠ « N variables reçues au lieu de 4 max »** d'
     `inject_custom_events.py` quand les impacts sont imposés (la troncature à 4
     passe avant la reprise des variables imposées ; message trompeur, trois
     lignes).
  3. **Étape « décider »** du pipeline : statuts du dossier simulé → adopté /
     rejeté → injecté.
  4. Hérité du 10 oct : **appliquer une liste pour de vrai** (validation de la
     phase 3), **décision S19** (mode rupture dans le vrai moteur), amplitude
     des chocs, phase 4 = option (b).
- **S24** (doublons probables vus par la passe, à vérifier à la main) :
  `bureau_des_territoires_residuels_fortress_world` /
  `bureau_territoires_residuels_fortress_world` ; en breakdown, deux « Archives
  Neutres de Genève » (`archives_neutres_de_geneve_breakdown`, émergent, et
  `archives_neutres_geneve_breakdown`, résiduel) et trois « Communes Libres du
  Rust Belt — Les Forges du Commun » (`communes_rust_belt_breakdown`,
  `communes_rust_belt_zones_libres_breakdown`,
  `mouvement_des_communes_du_rust_belt_breakdown`).
- Hérité : S23 séries ciblées, S25 mesure du cooldown Kharg-9, chantier 5, S28,
  S29.

## Fichiers livrés
- **Nouveaux (`generator/`)** : `et_si_exhaustif.py` (v9.5), `export_et_si.py`,
  `rejeu/` (`rejouer.py`, `evaluer.py`, `reference.json`, `loader.py`,
  `llm_client.py`, `LISEZMOI.md`).
- **Patchs (`generator/`, appliqués, refusent un second passage)** :
  `patch_s27_injection_imposee.py`, `patch_s27_v815.py`.
- **Modifiés** : `generator/inject_custom_events.py` (`.bak_imposee`),
  `generator/simuler_et_si.py` (`.bak_v815`), `et_si/hypotheses.yaml`
  (hypothèse Genève, ajoutée à la main).
- **Créés à l'usage** : `generator/state/et_si_exhaustif.json` (cache de la
  passe), `generator/state/export_et_si.json`, rapports
  `documentation/need_action/et_si_exhaustif_*.md` et `passe_*.md`,
  `generator/rejeu/sorties/` et `cache_rejeu.json` (jetables).

## Rappels pratiques
- **Commandes en une seule ligne** : un copier-coller de plusieurs lignes a
  collé `> /dev/null` à la commande suivante (« /dev/nullpython3: Operation
  not permitted »). Enchaîner avec `;` ou une boucle `for`.
- Relancer les six cas puis exporter :
  `for c in invasion_bresil_2029:fortress_world fusion_commerciale_2038:policy_reform peste_pulmonaire_2043:breakdown extreme_droite_2034:new_sustainability ia_majorite_travail_2040:eco_communalism destruction_geneve_2076:breakdown; do python3 generator/et_si_exhaustif.py --id ${c%%:*} --scenario ${c##*:} > documentation/need_action/passe_${c%%:*}.md; done; python3 generator/export_et_si.py`
- Rejouer et noter (gratuit) :
  `python3 generator/rejeu/rejouer.py && python3 generator/rejeu/evaluer.py`
  — viser « VERDICTS : 26/27 » ou mieux ; « appels manquants » > 0 = une
  consigne a changé, relancer les passes réelles d'abord.
- Une nouvelle session peut reprendre l'évaluation avec
  `generator/state/export_et_si.json` et le dossier `generator/rejeu/`.
- L'application Claude pour ordinateur ne tourne pas sur High Sierra : pas de
  session liée à l'iMac, d'où le banc de rejeu.

## À reporter dans les documents vivants
Fait dans cette session : `BACKLOG_ACTIF.md` (en-tête, S24, S27),
`BACKLOG_ARCHIVE.md` (S27 du 11 oct), `USER_MANUAL_COMPLET.md` (en-tête,
§3 `inject_custom_events.py` impositions, §3quinquies v8.15, passe exhaustive,
banc de rejeu, fichiers), `USER_MANUAL_HISTORIQUE.md` (addendum du 11 oct).
