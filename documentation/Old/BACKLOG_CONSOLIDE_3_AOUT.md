# Backlog consolidé Ourrassol 2098 — état au 3 août 2026

*Reconstitué à partir de `BACKLOG_CONSOLIDE_2_AOUT.md` et de
`HANDOFF_3_AOUT.md`. Objectif inchangé : ne garder que ce qui est
réellement encore ouvert.*

---

## 0. Nouveautés du 3 août 2026 — tout traité, résumé actionnable

Les 3 points de reprise laissés ouverts le 2 août sont **clos** :

1. ✅ **Plafonnement événements/géographie** (§6.4 du 2 août) — testé en
   conditions réelles. Plafonds eux-mêmes corrects du premier coup (8
   événements détail / 25 résumé / 20 zones résumé, tous vérifiés par
   comptage exact). 2 bugs annexes trouvés et corrigés : badge `[FORCÉ]`
   jamais affiché sur l'événement forcé (`loader.py`), zone de l'élément
   forcé absente de la section géographie détaillée pour un
   événement/signal forcé (`prompt_builder.py`, `build_geographie_
   context()` ne recevait pas `config`).
2. ✅ **Revalidation mode Semi-guidé** (§6.3 du 2 août) — testé en
   conditions réelles, les 7 champs du bug §3.7 (thématique, ligne
   éditoriale, longueur, angle, scénario, zone, titre suggéré) tous
   confirmés appliqués, y compris `zone_slug` (test dédié avec une zone
   réelle de `journaux.yaml`). 1 bug annexe trouvé et corrigé :
   `metadata["longueur"]` retourné par `build_prompt()` ignorait
   l'override de config, recalculé indépendamment depuis le
   `format_dominant` de la thématique — le prompt réel envoyé au LLM
   était toujours correct, seul le champ de métadonnées affiché en fin
   de `--dry-run` (et potentiellement réutilisé en aval) était faux.
3. ✅ **Ajustement des plafonds par défaut** (§7.3 du 2 août) — décision
   documentée de ne pas toucher aux plafonds maintenant : vault encore
   trop jeune pour des chiffres fiables, budget API de David pas encore
   vérifié précisément. À revisiter plus tard avec des données réelles.

**Nouveau chantier initié par David** : audit de complétude
snapshot/variables → 4 pertes de contenu narratif trouvées et corrigées
(`responsabilites`, `signes_distinctifs` sur les instances,
`realisation` sur les événements custom, jalons génériques de portée
"majeur" jamais affichés). Détail complet en §4 de `HANDOFF_3_AOUT.md`.

**Fichiers livrés** : `loader.py`, `prompt_builder.py` (versions finales
cumulant tous les correctifs de la session).

---

## 1. Ce qui reste réellement à faire

### 1.1 — Tester l'impact taille du prompt en mode Semi-guidé à 6 entités
Les 4 ajouts de l'audit de complétude (§0 ci-dessus, détail en
`HANDOFF_3_AOUT.md` §4) n'ont été testés qu'en mode Forcer-instance
(une seule entité détaillée). Le cas de charge réel — jusqu'à 6×
`responsabilites` + 6× `signes_distinctifs` simultanément en mode
Semi-guidé — n'a jamais été mesuré. **Priorité n°1 de la prochaine
session.**

### 1.2 — Décider du sort de `type_relation_dominante`/`annee_debut`/`annee_fin`
Trouvés lors de l'audit de complétude comme non redondants avec le
contenu déjà affiché (`type_relation_dominante` en particulier :
compense les listes `alliances`/`oppositions` souvent vides sur le
vault actuel). Pas encore ajoutés au prompt — décision à prendre avec
David lors d'une prochaine session, probablement après avoir mesuré
l'impact du point 1.1 ci-dessus.

### 1.3 — Vérifier si `metadata["longueur"]` (bug corrigé le 3 août) est réutilisé en aval
Si ce champ sert à autre chose que l'affichage `--dry-run` (frontmatter
d'articles sauvegardés par `api.py`, stats, filtrage), des fiches déjà
publiées avant le correctif du 3 août pourraient porter une longueur
affichée incohérente avec leur contenu réel — pas un problème de
qualité du texte généré, juste une étiquette potentiellement fausse.
David doit vérifier `api.py` pour trancher si un script de correction
rétroactive est nécessaire.

---

## 2. Gros chantiers volontairement en pause (pas oubliés, juste différés)

### 2.1 — Renommage des YAML génériques par dossier
`queue.yaml`/`processed.yaml`/`needs_review.yaml` répétés à l'identique
dans `entites_custom/`, `evenements_custom/`, `signaux_custom/` —
décision de renommage reportée (clarté vs coût). Aucune urgence
identifiée.

### 2.2 — P14 : passer le tier LLM `strict` vers `claude-sonnet-5` en prod
Différé sine die sur demande explicite de David (1er août). Décision,
pas un oubli — à reconsidérer plus tard si David le demande.

### 2.3 — P20 : enrichissement frontmatter pour publication web future
Scoping complet fait (`backlog_publication_web_journaux_oraux.md`, 12
juillet) — rien codé. Champs à ajouter : `slug`, `chapo`/`excerpt`,
`image_prompt`, `a_une_photo` (bool manuel), `image_principale`,
`image_alt`, `image_credit`, `tags`, `journaliste_slug`,
`date_publication` vs `date_evenement`, `articles_lies`,
`zone_principale`. Génération d'images : option 1 retenue (LLM produit
`image_prompt` au moment de la génération de l'article, décision
d'illustrer découplée et manuelle).

### 2.4 — P21 : journaux oraux, orateurs itinérants
Scoping complet fait (même document, 12 juillet) — rien codé.
Coexiste avec l'écrit au sein d'un même scénario (pas un scénario
entier qui bascule). Nouveau type d'entité `orateur` (Option B décidée),
nouveau champ `type_diffusion` sur les journaux, registre oral distinct
dans `prompt_builder.py`, champs frontmatter spécifiques
(`duree_estimee`, `lieu_diffusion`, `mode_reception`).

---

## 3. Points mineurs, non bloquants, sans action requise

- **P15** — `acteurs_hint_count` non plafonné en filtre dur dans
  `inject_custom_events.py`. Jamais observé comme un vrai problème.
- **`--force` du panneau `--scan-pending`** (`extract_localisation.py`)
  ne rafraîchit pas dynamiquement le menu — contournable via
  `--scenario`.
- **`coverage_proposals_reference.yaml`** sans `.applied` — anomalie
  repérée, famille legacy, sans impact opérationnel.
- **`/api/carte/appliquer_zone_topdown_suspecte`** — route dormante,
  seul point d'entrée UI retiré. Aucune action requise.
- **Champ `type` des zones géographiques** (`zone_sinistree` etc.,
  trouvé lors de l'audit de complétude du 3 août) — jamais utilisé dans
  le prompt, distinct de `statut` qui lui l'est. Jugé mineur, non
  traité.
- **Bloc `simulation`** sur les fiches variables (volatility/
  predictability/uncertainty_level/tipping_point_risk/
  systemic_criticality/resilience/adaptability, trouvé le 3 août) —
  chargé par `loader.py`, jamais utilisé par `prompt_builder.py`.
  Probablement pensé pour du monitoring interne, pas la narration.
- **`constrained_variables`** (snapshot, trouvé le 3 août) — calculé,
  jamais affiché dans le prompt.
- **Incohérence documentation/code** — la docstring de
  `build_variables_context()` (`prompt_builder.py`) promet
  `forces_attractives`/`forces_repulsives` "si disponibles", jamais
  implémenté, champs jamais extraits par `loader.py` non plus. Reliquat
  ou fonctionnalité inachevée, non tranché.

---

## 4. Risque structurel identifié (pas un bug actif — rien à corriger tant qu'il ne se manifeste pas)

**Instances avec `injection.type == "custom"` non sélectionnées parmi
les `filtered_instances`** : leurs deltas de variables sont bien
visibles ("Perturbations custom actives"), mais leur description
complète (responsabilités, tensions, etc.) ne l'est pas — seul un nom
tronqué apparaît dans la ligne de delta. Aucun exemple réel rencontré à
ce jour (le vault ne semble contenir que des événements custom, pas
d'instances custom) — trou de code identifié le 3 août, à garder en
tête si une instance custom est injectée un jour et qu'un comportement
bizarre apparaît.

---

## 5. Clarifications historiques (rappel, inchangé depuis le 2 août)

- **P8** (426 fiches `officialise_minimal`) — clos, traité intégralement
  le 27 juin 2026, preuve trouvée dans les fiches elles-mêmes.
- **`noeud_mnemos_pannonie`** — jamais une vraie anomalie, clos depuis
  le 14 juillet (P23).
- **P18** (cohérence `routes_dashboard.py`) — clos le 13 juillet, résidu
  de rédaction nettoyé dans le manuel.
- **P22 signal 2** — fusionné et livré via P24 étape B, pas un doublon.
- **P24 étape C** — entièrement absorbé par le système `chantiers_
  geographie.yaml` du 25 juillet → 1er août.
