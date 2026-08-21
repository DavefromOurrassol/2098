# Backlog consolidé Ourrassol 2098 — état au 8 août 2026

*Reconstitué à partir de `BACKLOG_CONSOLIDE_7_AOUT_SUITE.md` et de
`HANDOFF_8_AOUT.md`. Objectif inchangé : ne garder que ce qui est
réellement encore ouvert.*

---

## 0. Nouveautés du 8 août 2026 — résumé actionnable

Le chantier `annee_debut` (point 1.2 du backlog, ouvert depuis le 3 août)
a occupé toute la session. Contrairement au protocole en 5 étapes prévu la
veille, la session est partie sur l'enrichissement d'`etat_du_monde_reel.
md` et la construction d'un outil de veille associé, avant de découvrir
que le fichier n'avait quasiment aucun effet réel sur les corrections de
dates — ce qui a ouvert un chantier de robustesse non planifié.

1. ✅ **`etat_du_monde_reel.md` enrichi** — perspective ~10-15 ans sur les
   12 sections (4 sections vides du 7 août complétées) + perspective
   longue durée ~200 ans sur les 12. Testé par relecture, pas par appel
   LLM (contenu factuel rédigé directement).
2. ✅ **Outil de veille construit et livré** —
   `export_prompt_veille.py`/`import_veille_etat_monde.py`, sans
   dépendance API (David copie-colle dans l'IA de son choix). Sous-
   variables des fiches injectées dans le prompt, seuil de matérialité
   explicite, 13e question "hors catégories", garde-fou de fraîcheur.
   Intégré au GUI (2 entrées, nouvelle section "Référence — monde réel").
   **`gui_verified: false`** — jamais testé en navigateur.
3. ⚠️ **Découverte majeure, non anticipée** : `etat_du_monde_reel.md`
   n'avait aucun effet mesurable sur `fix_annee_debut_placeholder.py` —
   confirmé par 3 tests réels avec fait-test tracé. Cause : une règle
   "PRIORITÉ ABSOLUE" aux jalons du registre fictif du scénario
   l'emporte presque toujours, le fichier ne servant qu'à justifier
   qu'une date est "trop tôt", jamais à choisir la vraie date.
4. ✅ **Chantier `--ancrage-temporel {libre,recent}`** — ajouté à
   `generate_instances.py`/`create_entities_and_instances.py`, pour
   créer des entités délibérément ancrées dans le présent quand
   souhaité. Testé en conditions réelles, 2 bugs trouvés et corrigés en
   cours de route (contrainte de maturité insuffisante ; retry d'entité
   rejetée qui ne changeait jamais le nom malgré une collision de slug).
5. ✅ **Chantier `ancrage_reel` (traçabilité graduée)** — nouveau champ
   obligatoire sous condition de distance temporelle, validé
   mécaniquement. 5 rounds de tests réels et correctifs (recyclage du
   jalon fictif déguisé, faux positif sur la vraie AIE, bug de recherche
   par sous-chaîne de caractères). **Resserré en fin de session** : bande
   obligatoire réduite de 50 à 10 ans, après que David a remis en
   question la nécessité du garde-fou sur des dates déjà bien justifiées
   par un jalon de scénario.
6. ✅ **Run `--all` mené à terme, avec 3 bugs supplémentaires trouvés et
   corrigés en cours de route** : rapport ne traçant jamais les échecs
   (corrigé), confusion date réelle/date fictive sur `annee_debut`
   (corrigé dans les 3 scripts, + découverte annexe qu'aucune validation
   de plage n'existait dans les 2 scripts de création), bug
   d'idempotence faisant retraiter indéfiniment les fiches déjà
   confirmées (corrigé par un marqueur `annee_debut_verifiee`). **Chantier
   `annee_debut` officiellement clos, confirmé par un run à vide à 0
   fiche traitée.**
7. ✅ **`fix_annee_debut_placeholder.py` intégré au GUI** — section
   `entites_nettoyage`, même famille que `fix_alliances_oppositions`.
8. ⚠️ **Nouveau chantier identifié, différé** : `annee_fin` a le même
   trou de conception qu'`annee_debut` avait — 28/30 fiches concernées
   sans date de fin, sur un total bien plus restreint (voir §1.1bis).
9. ✅ **3 scripts d'audit convertis et ajoutés au GUI** — `audit_dates_
   instances.py`, `audit_type_relation_dominante.py`, `audit_etat_
   temporel_fin.py` (nouveau) — argument positionnel remplacé par
   `--dossier` (argparse), section `validation` du menu.
10. 🎯 **Chantier de conception majeur identifié en fin de session, PAS
    codé — priorité de la prochaine session** : investigation complète
    de `etat_temporel`/`age_historique`/`generation`, partie d'une
    incohérence trouvée sur une fiche (§1.1ter). Révèle un bug de
    cohérence interne dans `validate.py` (3 définitions différentes du
    même concept) et l'absence totale de validation d'`age_historique`.
    **Décision : fusionner `etat_temporel`+`age_historique` en un seul
    axe narratif continu** (Option B), `clandestin` devient un booléen
    indépendant. Voir `HANDOFF_8_AOUT.md` §12bis pour le détail intégral.

**Fichiers livrés** : `etat_du_monde_reel.md`, `export_prompt_veille.py`,
`import_veille_etat_monde.py`, `generate_instances.py`,
`create_entities_and_instances.py`, `fix_annee_debut_placeholder.py`,
`audit_dates_instances.py`, `audit_type_relation_dominante.py`,
`audit_etat_temporel_fin.py` (nouveau), `scripts_config.json`, `app.js`.

---

## 1. Ce qui reste réellement à faire

### 1.1 — Chantier `annee_debut` : CLOS, confirmé
Vault entier traité par David, 0 échec persistant, script rendu
réellement idempotent (bug de retraitement infini corrigé — voir
`HANDOFF_8_AOUT.md` §9.3). Confirmé par un run à vide produisant
`Traitées: 0` sur toute la ligne. **Ce point peut être définitivement
retiré du backlog.**

### 1.1ter — PRIORITÉ DE REPRISE : fusion `etat_temporel`/`age_historique` (Option B retenue)
Chantier de conception né en creusant l'incohérence de la fiche
`zones_extractivistes_corridors_eco_communalism` (`age_historique:
ascendant` + `etat_temporel: transformé`). Investigation complète faite,
**rien codé** — voir `HANDOFF_8_AOUT.md` §12bis pour le détail intégral
(définitions inférées, cartographie des usages, bug trouvé dans
`validate.py`, matrice de compatibilité, les deux options présentées).

**Décision de David : Option B retenue** — fusionner `etat_temporel` +
`age_historique` en un seul axe narratif continu (`émergent → ascendant
→ dominant → mature → déclinant → résiduel → transformé → disparu →
mythifié/historique`), `clandestin` devient un champ booléen indépendant
(`est_clandestin`) plutôt qu'un état parmi d'autres. `generation` reste
inchangé (orthogonal, pas de recouvrement identifié).

**Découverte importante en cours de route** : `validate.py` a déjà des
checks sur ces champs (A2, C1-C4) mais avec un bug de cohérence interne
(3 définitions différentes du même concept — `INACTIVE_ETATS` ≠
`ETAT_INACTIFS` ≠ le hardcodage de `C4`) qui rend les 28 fiches
invisibles à l'outil existant. **Correctif isolé possible sans attendre
la fusion complète** si un résultat rapide est voulu : aligner `C4` sur
`ETAT_INACTIFS` (une ligne).

**À faire en premier à la prochaine session** :
1. Valider les définitions inférées par Claude (jamais confirmées
   formellement par David).
2. Affiner l'ordre exact du nouvel axe et les règles de migration des
   710 fiches existantes.
3. Construire la migration (`loader.py`, 5 scripts de création/
   correction, `prompt_builder.py`, `validate.py`, script de migration
   rétroactive).

**Priorité recommandée sur `annee_fin` (1.1bis ci-dessous)** — plus
simple à construire une fois qu'il n'y aura plus qu'un seul champ de
statut à croiser avec `annee_fin`, plutôt que deux.

### 1.1bis — Chantier `annee_fin` — 28 fiches, à construire APRÈS 1.1ter
Même trou de conception que `annee_debut` avant ce soir, mais à bien
plus petite échelle. Diagnostic fait (`audit_etat_temporel_fin.py`,
nouveau, ajouté au GUI) :
- 30 fiches ont un `etat_temporel` impliquant normalement une fin
  (`transformé` 28, `disparu` 2).
- **28/30 (93,3 %) sans `annee_fin` renseignée.**
- `historique`/`mythifié` : 0 occurrence dans tout le vault — pas un
  chantier, juste une observation à garder en tête.
- `clandestin` (23 fiches) : deviendra un booléen indépendant via 1.1ter
  — plus besoin de trancher son cas séparément une fois la fusion faite.

**Décision de David** : différé à une prochaine session, à construire
après le chantier de fusion (1.1ter). Voir `HANDOFF_8_AOUT.md` §10 et
§12bis pour le détail complet.

**Points annexes observés sur ces 28 fiches, notés sans action requise** :
- Concentration sur 2041 (36 % des 28) — écho du constat global (157/710
  sur tout le vault, voir §8 de la session), lié au futur chantier de
  répartition homogène (1.8 ci-dessous).
- Encodage portugais cassé sur certains slugs (`rede_paulista_de_
  distribuic_o_algor_tmica` — accents perdus à la slugification) — mineur,
  pas de chantier dédié prévu.
- Répartition très inégale par scénario (19/28 sur `breakdown`) — jugé
  probablement normal vu la nature du scénario, jamais creusé davantage.

### 1.2 — Tester les nouvelles entrées GUI dans un vrai navigateur
Concerne, au total cette session : les 2 entrées de veille (`export_
prompt_veille`, `import_veille_etat_monde`), `generate_instances`, `fix_
annee_debut_placeholder` (nouveau, intégré en fin de session), les 3
audits (`audit_dates_instances`, `audit_type_relation_dominante`, `audit_
etat_temporel_fin` — nouveaux, section `validation`), et les options
ajoutées à `create_entities` (`--ancrage-temporel`). Protocole détaillé
esquissé en session du 8 août (checklist dates, garde-fou de fraîcheur,
sections indépendantes) — voir transcript si besoin de le retrouver.
`gui_verified: false` sur toutes ces entrées.

### 1.3 — Trancher le statut de `generate_instances.py`
Le manuel (avant mise à jour du 8 août) le classait "Legacy — fusionné
dans `create_entities_and_instances.py`". La session du 8 août l'a
pourtant mis à jour et ajouté au GUI comme outil actif. À clarifier avec
David : la fusion documentée était-elle réellement complète, ou ce
script garde-t-il un usage résiduel légitime (backfill d'instances pour
des entités déjà créées, sans repasser par la création d'entité) ?

### 1.4 — Dimension temporelle pour l'auto-suggest (idée du 8 août, non codée)
`analyze_entity_coverage()` (dans `create_entities_and_instances.py`,
mode "Auto-suggest — suggestions depuis gaps") mesure déjà 3 dimensions
(géographie, zones absentes, catégories) — aucune dimension temporelle.
Proposition esquissée en session : ajouter la distribution de `annee_
debut` par bande (par scénario) à cette analyse, pour que l'auto-suggest
propose activement des créations dans les bandes sous-représentées,
plutôt que de compter sur le hasard ou sur des blocages a posteriori.
Décision de David : traiter ça à une prochaine session plutôt que ce
soir.

### 1.5 — Décider du sort de `type_relation_dominante`
Inchangé depuis le 3-4 août — `type_relation_dominante` rempli à 100 %
sur les fiches d'origine. Décision toujours à prendre avec David.
`annee_fin` n'est plus dans ce point — voir §1.1bis, ce n'est plus "voulu
par défaut, jamais challengé" mais un vrai chantier identifié (28
fiches), le libellé précédent était périmé.

### 1.6 — Vérifier si `metadata["longueur"]` (bug corrigé le 3 août) est réutilisé en aval
Inchangé depuis le 3 août.

### 1.7 — Même diagnostic sur les événements que sur les instances ?
Question de David, non explorée cette session (8 août) : tout le
chantier `annee_debut`/`ancrage_reel` a porté exclusivement sur les
instances. Les événements (`inject_custom_events.py`, `registre_
evenements.md`) ont-ils un problème analogue ? Diagnostic à faire en
premier, avant de décider si la même approche s'applique.

### 1.8 — Répartition homogène des dates + ancrage sur les crises, pour la génération automatique
Idée précisée par David en fin de session du 8 août, extension de l'idée
notée le 8 août matin (dimension temporelle pour l'auto-suggest — voir
`HANDOFF_8_AOUT.md` §12.2 pour le détail complet). Deux volets à
concevoir ensemble, sur le modèle de ce qui existe déjà pour la
géographie dans `analyze_entity_coverage()` :
1. Contrainte de répartition homogène pour éviter qu'une génération
   automatique ne fasse converger massivement les nouvelles entités vers
   une poignée d'années sur-représentées (rappel : 2041 concentre à lui
   seul 22 % du vault, 157/710 fiches).
2. Ancrage sur les crises réelles du registre du scénario plutôt qu'une
   répartition purement arithmétique/aléatoire.
Non conçu, non codé cette session.

---

## 2. Reliquats de la consolidation du 7 août soir — jamais traités

Ces quatre points avaient été identifiés en tout début de la session du 8
août (avant que le chantier `annee_debut` ne prenne toute la place), avec
la promesse de les traiter en fin de séance. Reportés une nouvelle fois,
faute de temps.

### 2.1 — Fausse alerte `depends_on` — close, aucune action requise
Vérifié en détail le 8 août matin : ni `HANDOFF_7_AOUT.md` §9 ni
`USER_MANUAL_COMPLET.md` ne décrivaient à tort un masquage conditionnel.
Rien à corriger. **Ce point peut être définitivement retiré du backlog.**

### 2.2 — Trois items du 2 août jamais confirmés déployés
- Redéploiement effectif des correctifs du 2 août (`routes_dashboard.py`,
  `app.py`/`enrich_minimal.py` pour le panneau Revue, `geographie/
  policy_reform.md` pour Groenland) — jamais confirmé par un handoff
  ultérieur.
- Recommandation de déplacer `instance_template.md` hors de `instances/`
  + audit non fait de son impact potentiel sur d'autres scripts
  (`extract_phantom_slugs.py` etc.) — jamais repris.
- Limite connue du panneau Revue (`entites_custom`/`signaux_custom`
  affichés avec un slug générique au lieu du vrai nom) — jamais reprise
  dans un backlog ultérieur.

### 2.3 — Gap de process sur le backlog du 2 août
`BACKLOG_CONSOLIDE_2_AOUT.md` ne listait pas, dans sa propre section
"reste à faire", les 3 points de reprise du mode Forcer/plafonnement
pourtant documentés dans `HANDOFF_2_AOUT.md` §6 — ils n'apparaissent que
rétroactivement dans le backlog du 3 août. Pas de conséquence pratique
(tout a été traité), mais reste un exemple à garder en tête pour la
discipline "le backlog doit être auto-suffisant".

### 2.4 — Nettoyage optionnel des fichiers de rotation
`generator/state/instance_usage.json`, `trajectory_usage.json`, `event_
relevance_usage.json` — nettoyage conditionnel ("si besoin de repartir
sur une mémoire vierge"), jamais nécessaire à ce jour, aucun risque à les
supprimer s'il le faut un jour.

---

## 3. Gros chantiers volontairement en pause

Inchangé depuis le 7 août — renommage YAML génériques (3.1), P14 tier LLM
strict→claude-sonnet-5 (3.2, différé sine die), P20 enrichissement
frontmatter web (3.3), P21 journaux oraux (3.4).

---

## 4. Points mineurs, non bloquants

Inchangé depuis le 7 août (P15, `--force` du panneau `--scan-pending`,
`coverage_proposals_reference.yaml` sans `.applied`, etc.) — voir
`BACKLOG_CONSOLIDE_7_AOUT.md` §3 pour le détail complet, aucun changement
cette session.

**Ajout du 8 août** : `--min-shingle` de `detect_registre_leakage()`
(dans les 3 scripts touchés par le chantier `ancrage_reel`) est fixé en
dur à 6 mots dans le code — pourrait devenir un paramètre CLI si jamais
un nouveau faux positif/négatif apparaît en usage réel, mais pas
nécessaire tant que ça ne se manifeste pas.

---

## 5. Risque structurel identifié (pas un bug actif)

Inchangé depuis le 3 août — instances `injection.type == "custom"`
potentiellement non sélectionnées parmi les `filtered_instances`.

---

## 6. Clarifications historiques (rappel, complété le 8 août)

Reprend `BACKLOG_CONSOLIDE_7_AOUT_SUITE.md` §5, avec deux ajouts :

- **Point 1.2 backlog (dates `annee_debut`)** — chantier mené à bien le 8
  août avec un détour important (outil de veille, découverte de
  l'inefficacité du fichier, chantier de robustesse `ancrage_reel`).
  **Toujours pas formellement clos** : le run `--all` réel vient d'être
  lancé, résultat à vérifier avant de considérer ce point comme terminé.
- **`ancrage_reel` / traçabilité graduée** — chantier ouvert et refermé
  dans la même session (8 août), en 5 itérations de test réel. Décision
  finale : bande obligatoire resserrée à 10 ans (2026-2036), au-delà
  optionnel avec contrôle anti-recyclage du registre si rempli.
