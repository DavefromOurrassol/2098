# HANDOFF — 25 septembre 2026

Suite de `HANDOFF_24_SEPTEMBRE.md`. Session consacrée à #4 (zones
suspectes), S13 (`assign_pays`), S15.1 (Ergo-Wian/NAT), puis à un nouvel
outil d'audit du lore appliqué aux 6 scénarios et intégré au GUI. Toutes
les modifications faites sur le vault réel par David (scripts avec aperçu,
`.bak`, relecture YAML ; commit à chaque étape). `validate.py` : 0 erreur,
0 avertissement en fin de session.

## Fait

### #4 — Revue des 14 chantiers `zone_suspecte` — CLOS
- **11 ignorés** (choix narratifs ou faux positifs) : amazonie_pacte_vert,
  espace_nordique_arctique, singapour_megapole, tuvalu_refugies_climatiques,
  al_hima (fortress_world) ; bloc_eurasien_souverainiste, moyen_orient_golfe
  (new_sustainability) ; inde_bassins_sacres, japon_archipel_resilient
  (eco_communalism) ; espace_eurasiatique (policy_reform) ;
  pacte_des_souverains (reference).
- **ameriques_multipolaires** (reference) : proposition déjà appliquée
  (5 champs identiques à la fiche), seul le statut manquait → `traite`.
- **bloc_persique_autonome** (reference) : proposition appliquée via le GUI,
  statut `stable` ; répare des relations cassées (auto-alliance, noms en
  clair au lieu de slugs).
- **peninsule_iberique_cooperative** (policy_reform) : Portugal retiré de
  `hub_europeen_regulation` et rattaché à la péninsule depuis la Carte
  (+ `--apply-type-entite`), chantier marqué `traite`.
- Constat documenté (manuel §4bis) : une proposition `zone_suspecte` est un
  instantané de la zone ENTIÈRE au moment du scan. « Appliquer » n'écrit que
  5 champs (description, type, statut, tensions_internes, relations), jamais
  `origine_reelle` — mais écrase ces 5 champs avec leur version d'alors.
  Proposition « Espace Nordique » périmée : ajoutait Cap-Vert (origine
  probable du « Cap-Vert fantôme » du 8 sept) et retirait 9 pays.

### S13 — `assign_pays` (`gui/zone_repository.py`) — CLOS
Patch v2 appliqué et testé (6/6 sur copie de `fortress_world`) :
1. entrée `origine_reelle` complète (`type_entite: pays`, `portion: null`),
   à l'affectation comme à la création ;
2. **le ménage « retirer le pays des autres zones » épargne désormais les
   entrées adossées à un tracé overlay** (même filtre que
   `retirer_doublons_pays_entier`) — avant, affecter la France à une zone
   effaçait l'entrée littorale de Heysham et laissait son tracé orphelin ;
3. zone créée depuis un clic au schéma complet (type `autre`, statut
   `emergent`, relations…, titre dans le corps), comme `creer_zone_n1`.

### S15.1 — Ergo-Wian / NAT alignés sur Euro-Nord — CLOS
Retouche ciblée (pas de régénération) de 2 instances fortress_world :
- **Ergo-Wian Sovereign Dominion** : localisation `espace_nordique_arctique`
  (était transnationale), rôle = gouvernement-entreprise d'Euro-Nord, NAT
  filiale armée, main-d'œuvre importée du Hors ; « ancien cadre de
  BlackRock » → « ancien gérant de fonds du XXIe siècle » (et PDG →
  souverain-gérant) ; NAT + Contrats de service en alliés.
- **NAT** : filiale armée d'Ergo-Wian, **fait connu de tous** (plus de
  « neutralité affichée ») ; tensions réécrites ; Ergo-Wian + Contrats en
  alliés. Ses 2 alliés `_reference` conservés (décision David).
- Contrats de service d'Ergo-Wian : déjà cohérents, inchangés.

### Nouvel outil — audit du lore (S17)
- **`generator/audit_lore.py`** : sans LLM par défaut (règles de lore,
  quarantaine, transnationales localisées dans le texte, réciprocité,
  inter-scénarios) ; `--llm` (contradictions + relations proposées parmi
  les instances existantes, cache, garde-fou 15 appels, `--estimer`) ;
  `--appliquer` (relations `valide: true` seulement). Détail : manuel §3,
  « Audit du lore ».
- **`documentation/lore_regles.yaml`** : règles fortress_world (Interzone,
  zones abandonnées, quarantaine Heysham en deux niveaux, NAT non neutre
  avec négations ignorées, exception Brest-Litovsk).
- **`fix_alliances_oppositions.py`** : `calculer_reciprocite()` extrait
  (fonction pure, sortie identique avant/après vérifiée sur 4 modes) +
  option **`--ignorer-exclus`** (les personnages en réserve ne sont pas
  propagés chez les autres fiches).
- **`generator/corriger_relations_inter_scenarios.py`** (générique, à
  garder) : relation vers un autre scénario → remplacée par l'équivalent du
  bon scénario s'il existe, sinon retirée ; exceptions NAT codées.
- **GUI** : 2 nouvelles entrées sidebar (« 🔍 Audit du lore »,
  « 🔀 Corriger les relations entre scénarios ») + case « Ne pas propager
  les personnages en réserve » sur 🤝. Aucun changement `app.py`/`app.js`.

### Corrections appliquées grâce à l'audit
- **fortress_world** : instance `bloc_atlantique` (Charte de Dublin →
  **Halifax**, siège Lisbonne-Haute → Halifax-Haute, « Irlande fortifiée /
  enclaves marocaines » → « Groenland fortifié / enclaves caribéennes ») ;
  article du 21 juin (corridor Reykjavik-Édimbourg / hub en Écosse-Nord →
  Halifax–Saint-Jean de Terre-Neuve / hub du Labrador) ; Vikram ne s'oppose
  plus à Hyphan.
- **6 scénarios** : 42+5 relations inter-scénarios retirées (aucun
  équivalent n'existait) ; réciprocité propagée (67 + 231 + ~50 fiches) ;
  2 conflits `breakdown` résolus (opposition prioritaire : Arctic Passage
  Authority retirée des alliés du Conglomérat sino-sibérien et de
  Mourmansk).
- **État final** (audit `--all`) : 0 erreur de lore, 0 contradiction,
  0 relation à sens unique hors les 24 volontaires (personnages en réserve
  fortress_world), 2 inter-scénarios (NAT, voulus).

## Bugs trouvés
- `assign_pays` effaçait les entrées overlay (corrigé, S13).
- Propositions `zone_suspecte` périmées dangereuses à appliquer sans relire
  (documenté, pas de code).
- `write_alliances_patch()` ne retire pas la section « ## Relations » quand
  les deux listes deviennent vides (le lien retiré restait dans le corps).
  Contourné dans les scripts du jour ; `fix_alliances_oppositions.py`
  inchangé sur ce point (voir S17).
- Faux positifs de la v1 de l'audit (négation « n'est pas neutre »,
  Brest-Litovsk) corrigés en v2.

## Décisions actées
- #4 : tri ci-dessus. Portugal dans la Péninsule Ibérique Coopérative
  (policy_reform). Bloc persique `stable`.
- Relations inter-scénarios = erreurs de génération, sauf les 2 alliés
  `_reference` de la NAT, conservés.
- Hyphan (fortress_world) s'oppose à Ergo-Wian mais n'est pas une rebelle
  active (fiche déjà conforme) ; Vikram ne s'oppose pas à elle.
- Charte de Halifax pour le PAPC ; articles archivés retouchés quand ils
  contredisent le lore (cas de l'article du 21 juin).
- Personnages en réserve : leurs relations ne sont pas propagées
  (`--ignorer-exclus`).
- Les instances ne suivent PAS l'évolution du lore : retouche ciblée ou
  régénération (qui écrase les retouches), à décider au cas par cas.

## Reste à faire
- **#3 P20** — brancher le service d'image.
- **S17** — audit du lore : tester les 2 entrées GUI (`gui_verified:
  false`), premier vrai passage `--llm` (jamais lancé en réel), règles pour
  les 5 autres scénarios (`reference` en premier : Ergo-Wian, Hyphan
  successeuse désignée…), relancer audit + réciprocité après chaque lot
  d'entités. Vikram allié d'Ergo-Wian (déclaré par le lot du 24 sept,
  propagé par réciprocité) : à revoir si ça gêne le récit.
- S15 (reste) : Milan/Lyon en sous-zones si besoin, corps markdown périmé
  de `fortress_world.md`, personnages en réserve à ré-autoriser.
- S16 — création directe de sous-zone dans le GUI, si le besoin revient.
- Scripts ponctuels à supprimer s'ils sont encore là :
  `aligner_ergo_wian_nat_25sept.py`, `retirer_relations_25sept.py`,
  `aligner_bloc_atlantique_25sept.py`, `marquer_zones_suspectes_25sept.py`,
  `patch_s13_assign_pays*.py`.

## Fichiers livrés
- `gui/zone_repository.py` (patch S13 v2), `gui/scripts_config.json`
  (2 entrées + 1 option).
- `generator/audit_lore.py` (v3), `generator/fix_alliances_oppositions.py`
  (v2), `generator/corriger_relations_inter_scenarios.py`,
  `documentation/lore_regles.yaml` (v2).
- Vault : `chantiers_geographie.yaml` (14 statuts), `geographie/
  policy_reform.md` + `reference.md`, `gui/zones_pays.json`, instances
  Ergo-Wian / NAT / Bloc Atlantique + ~400 fiches (relations), 1 article.
- `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`, `USER_MANUAL_COMPLET.md`, ce
  handoff.

## Non traité hérité
S1-S10, S12, S14 inchangés (voir backlog).
