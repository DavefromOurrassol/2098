# Backlog consolidé Ourrassol 2098 — état au soir du 7 août 2026

*Complète BACKLOG_CONSOLIDE_7_AOUT.md (chantier réciprocité alliances/
oppositions, clos). Reconstitué à partir de ce même fichier + du chantier
point 1.2 traité en profondeur dans la suite de la même journée. Voir
HANDOFF_7_AOUT_SUITE.md pour le détail narratif complet.*

---

## 0. Nouveautés de la suite du 7 août 2026 — résumé actionnable

Point 1.2 ("décider du sort de type_relation_dominante/annee_debut/
annee_fin") : **transformé en chantier complet**, largement avancé mais
**pas encore testé en conditions réelles** (reporté au 8 août).

1. ✅ **Diagnostic complet** — 3 causes distinctes du blocage de 67 % des
   fiches (477/710) à `annee_debut: 2026` : placeholder codé en dur
   (`officialize_alliances.py`), champ jamais redemandé par l'enrichissement
   (`enrich_minimal.py`), biais d'ancrage sur un exemple JSON littéral
   (`generate_instances.py`/`create_entities_and_instances.py`).
2. ✅ **`prompt_builder.py` corrigé** — `type_relation_dominante`/dates
   maintenant affichées dans le prompt de génération d'articles (avec
   garde-fou anti-fabrication).
3. ✅ **3 scripts de création/enrichissement corrigés à la source** —
   ancrage sur la chronologie fictionnelle réelle du scénario
   (`registre_evenements.md`) ET sur un nouvel état du monde réel
   (`etat_du_monde_reel.md`), avec règle d'usage conditionnel selon la
   date choisie.
4. ✅ **Bug réel découvert et corrigé** — `parse_registre_table()` dans
   `inject_custom_events.py` aveugle sur toute la section `breakdown` du
   registre (0 ligne parsée au lieu de ~84) depuis un reformatage manuel
   de la ligne séparatrice. Correctif porté depuis un fix identique déjà
   fait le 26 juillet dans `inject_custom_signals.py`, jamais répercuté.
5. ✅ **`fix_annee_debut_placeholder.py`** — nouveau script de rattrapage
   pour les 477 fiches existantes, testé une première fois (3 fiches,
   résultat cohérent : 1 correction 2026→2038 sur jalon réel, 2
   confirmations justifiées).
6. ✅ **`etat_du_monde_reel.md`** — nouveau fichier de référence factuelle,
   rempli à 8/12 sections via recherches web du 7 août 2026 (guerre
   Ukraine, conflit Moyen-Orient depuis février 2026, tension réelle sur
   l'AIE, AI Act européen, COP30, choc pétrolier 2026...).
7. ⏳ **Non testé** : le dry-run du point 5 a été fait AVANT le câblage de
   l'état du monde réel (point 6). Cas notable à revérifier : l'entité
   "AIER" (réforme fictionnelle de l'AIE) confirmée à 2026 sans
   vérification de plausibilité réelle — à retester maintenant que la
   tension réelle sur l'AIE (menace de retrait américain, février 2026)
   est disponible dans le prompt.

**Fichiers livrés cette session (suite)** : `prompt_builder.py`,
`generate_instances.py`, `create_entities_and_instances.py`,
`enrich_minimal.py`, `inject_custom_events.py`,
`fix_annee_debut_placeholder.py`, `etat_du_monde_reel.md`,
`audit_type_relation_dominante.py`, `audit_dates_instances.py`.

---

## 1. Ce qui reste réellement à faire

### 1.1 — Déployer et tester le chantier point 1.2 (priorité du 8 août)
Voir HANDOFF_7_AOUT_SUITE.md §10 pour le protocole détaillé en 5 étapes :
placer les fichiers, dry-run ciblé (revérifier le cas AIER), élargir le
dry-run par scénario, lancer pour de vrai scénario par scénario, réaudit
final avec `audit_dates_instances.py`.

### 1.2 — Tester les deux entrées GUI dans un vrai navigateur
Inchangé depuis le 7 août matin — voir BACKLOG_CONSOLIDE_7_AOUT.md §1.1.
Protocole partiellement suivi (points 2 et 6 vérifiés en direct par
David), reste à finaliser. `gui_verified: false` toujours sur les deux
entrées.

### 1.3 — Corriger la documentation sur le mécanisme `depends_on`
`HANDOFF_7_AOUT.md` §9 et `USER_MANUAL_COMPLET.md` décrivent à tort
`depends_on` comme un masquage conditionnel. Le mécanisme réel (confirmé
par lecture de `app.js` en session) : l'option enfant est TOUJOURS
visible, cocher l'enfant force le parent à se cocher, décocher le parent
décoche l'enfant. Correction textuelle à faire dans les deux documents —
non faite en session faute d'accès au contenu complet de
`USER_MANUAL_COMPLET.md`.

### 1.4 — Compléter `etat_du_monde_reel.md`
4 sections laissées vides faute de résultats de recherche suffisamment
spécifiques en une session : `valeurs_culture_tempo_sociale`,
`organisation_territoires`, `sante_biotechnologies`, `frontieres_du_
systeme`. À enrichir manuellement ou lors d'une future session si des
entités proches de 2026 touchent particulièrement ces thèmes. Prévoir
aussi une révision périodique (tous les 3-6 mois recommandé).

### 1.5 — Vérifier si `metadata["longueur"]` (bug corrigé le 3 août) est réutilisé en aval
Inchangé depuis le 3 août.

---

## 2. Gros chantiers volontairement en pause

Inchangé depuis BACKLOG_CONSOLIDE_7_AOUT.md §2 — renommage YAML génériques
(2.1), P14 tier LLM strict→claude-sonnet-5 (2.2, différé sine die), P20
enrichissement frontmatter web (2.3), P21 journaux oraux (2.4).

---

## 3. Points mineurs, non bloquants

Inchangé depuis BACKLOG_CONSOLIDE_7_AOUT.md §3, avec un ajout :

- **Traçabilité des runs `fix_annee_debut_placeholder.py`** — même choix
  assumé que pour la réciprocité : rapport externe
  (`documentation/need_action/fix_annee_debut_placeholder.md`), tronqué en
  tête de run réel, jamais en dry-run.

---

## 4. Risque structurel identifié (pas un bug actif)

Inchangé depuis BACKLOG_CONSOLIDE_7_AOUT.md §4 — instances
`injection.type == "custom"` potentiellement non sélectionnées parmi les
`filtered_instances`.

---

## 5. Clarifications historiques (rappel, complété le 7 août soir)

Reprend BACKLOG_CONSOLIDE_7_AOUT.md §5, avec un ajout :

- **Point 1.2 backlog (dates annee_debut)** — diagnostic complet et
  correctifs livrés le 7 août soir, mais **PAS encore clos** : tests réels
  reportés au 8 août (voir §1.1 ci-dessus). Ne pas marquer comme clos tant
  que le déploiement + réaudit du HANDOFF_7_AOUT_SUITE.md §10 n'est pas
  fait.
