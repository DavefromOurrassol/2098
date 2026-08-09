# HANDOFF — session du 8 août 2026 (à uploader dans le nouveau chat)

*Session très dense, entièrement construite autour du point de reprise
laissé ouvert le 7 août soir : le chantier `annee_debut`/`etat_du_monde_
reel.md` (voir `HANDOFF_7_AOUT_SUITE.md` §13, protocole en 5 étapes).
Contrairement au plan initial, cette session n'a pas suivi ce protocole
tel quel — elle est partie sur l'enrichissement du fichier de référence,
a construit un outil de veille pour le maintenir à jour, puis a découvert
en testant en conditions réelles que le fichier n'avait quasiment aucun
effet sur les corrections de dates — ce qui a ouvert un chantier de
robustesse imprévu, mené à bien avec plusieurs allers-retours de tests
réels par David. Session encore en cours au moment de la rédaction : David
vient de lancer `fix_annee_debut_placeholder.py --all` sur le vault réel.*

---

## 1. Enrichissement d'`etat_du_monde_reel.md` (début de session)

Le fichier du 7 août (8/12 sections remplies, simple photo du 7 août) a
été enrichi en trois passes successives, sur demande de David :

1. **Perspective historique ~10-15 ans** ajoutée aux 8 sections déjà
   remplies + les 4 sections vides complétées (`valeurs_culture_tempo_
   sociale` — vague Gen Z 2025-2026 — `organisation_territoires`,
   `sante_biotechnologies`, `frontieres_du_systeme`). Chaque section
   distingue désormais **trajectoire longue** (10-15 ans) et **situation
   actuelle et mouvements en cours**.
2. **Perspective longue durée (~200 ans)** ajoutée à chacune des 12
   sections — grand arc depuis la révolution industrielle. Objectif :
   donner un repère civilisationnel pour juger la plausibilité des
   entités les plus lointaines dans le temps fictionnel (jusqu'à 2098),
   pas seulement celles proches d'aujourd'hui.
3. **`Variables_save.docx`** (document fourni par David) analysé : c'est
   le document de conception d'origine des 12 variables (fictionnel,
   antérieur à la formalisation actuelle des fiches `variables/*.md`) —
   **pas utile** pour `etat_du_monde_reel.md` (qui documente le monde
   réel, pas la fiction), mais utile comme référence de contrôle générale
   du projet (vérifié fidèle sur l'échantillon climat).

Chaque section a maintenant 3 niveaux : perspective ~200 ans → trajectoire
~10-15 ans → situation actuelle. Fichier livré : `etat_du_monde_reel.md`
(version enrichie, ~590 lignes).

---

## 2. Outil de veille — `export_prompt_veille.py` / `import_veille_etat_monde.py` (nouveau)

Constat de David : l'outil doit pouvoir être remis à jour régulièrement
sans dépendre d'un abonnement API particulier. Design retenu, en 100%
sans appel API — David copie un prompt généré dans l'IA de son choix
(Claude.ai, ChatGPT...), colle la réponse dans un fichier, un second
script l'importe.

### `export_prompt_veille.py`
- Extrait automatiquement le paragraphe "Situation actuelle" + sa date de
  chaque section, injecte tout dans un prompt prêt à copier.
- **Sous-variables des fiches réelles injectées** (ajout demandé par
  David après avoir remarqué que `valeurs_culture_tempo_sociale` ne
  couvrait que le mouvement Gen Z, sur 5 sous-dimensions officielles de
  la fiche — rien sur la montée du conservatisme, le masculinisme en
  ligne, etc.). Lit `variables/{slug}.md`, extrait `sub_variables` en
  isolant juste ce bloc du frontmatter (le frontmatter complet n'est pas
  du YAML standard — wikilinks Obsidian comme clés dans `coupling_
  intensity`, fait planter `yaml.safe_load()` sur le fichier entier).
- **Seuil de matérialité explicite** dans le prompt (demande de David) :
  le LLM ne doit marquer une section `[MODIFIÉ]` que si un changement est
  réellement significatif, jamais pour une reformulation ou un chiffre
  qui bouge de quelques points.
- **13e section `hors_categories`** : question ouverte, hors des 12
  variables, pour capter un événement de rupture totale qui ne collerait
  à aucune case prédéfinie (ex. testé avec un scénario "artefact
  extraterrestre découvert"). Jamais auto-intégrée dans le fichier — juste
  signalée bien visible (`!!!`) pour revue manuelle.
- **Consigne de livraison en fichier téléchargeable** (Canvas/artifact),
  ajoutée sur demande de David pour éviter le copier-coller manuel.

### `import_veille_etat_monde.py`
- Parse la réponse collée, patch chirurgical des seules sections
  `[MODIFIÉ]` (titre + paragraphe), laisse `[INCHANGÉ]` et les niveaux
  historiques strictement intacts.
- **Chaque section garde sa propre date de dernière mise à jour**
  (normalisation du titre `**Situation actuelle (mise à jour : DATE)**`,
  remplaçant l'ancien titre fixe "à l'été 2026") — permet de savoir en un
  coup d'œil quelles sections sont fraîches.
- **Garde-fou de fraîcheur** : compare la date de modification du fichier
  collé à aujourd'hui — bloque l'import sans `--force` si le fichier n'a
  pas été touché le jour même (probable réponse oubliée d'une veille
  précédente). Testé dans les deux sens (bloque sans `--force`, passe
  avec).
- Archive automatiquement la réponse brute après import réussi
  (horodatée), écrit un rapport diff.
- **Dates en français codées en dur** (table de correspondance des mois)
  plutôt que `strftime("%B")`, qui dépend d'une locale système absente du
  bac à sable de test — bug trouvé et corrigé avant livraison.

### Intégration GUI
- Deux nouvelles entrées dans `scripts_config.json`, nouvelle section de
  menu **"Référence — monde réel"** (une ligne ajoutée à `SECTIONS` dans
  `app.js` — seule modification nécessaire sur ce fichier).
- Panneau prompt rendu éditable (`readonly: false`) sur demande de David.
- **Aucune modification à `app.py`** — le mécanisme générique `/api/yaml`
  (déjà existant) suffit pour coller/éditer les deux fichiers d'échange.
- **`gui_verified: false`** sur les deux entrées — jamais testées dans un
  vrai navigateur cette session.

---

## 3. Découverte majeure : `etat_du_monde_reel.md` n'avait aucun effet mesurable

Avant de valider le GUI, David a voulu vérifier que les mises à jour du
fichier étaient vraiment prises en compte dans le choix des dates de
naissance des entités (`annee_debut`). **Trois tests réels, sur trois
fiches différentes, avec un "fait-test" traçable injecté dans le fichier
entre deux runs identiques** :

1. **AMMC** (`new_sustainability`, agence climatique) — 2026 → 2038 dans
   les deux runs, justification identique, fait-test jamais mentionné.
2. **Collectifs de Géo-Observateurs Citoyens** (`eco_communalism`) — 2026
   → 2036 dans les deux runs, même verdict.
3. **Commission Hydrique de l'Union Africaine** (`reference`) — 2026 →
   2031 puis 2036 (jalon différent), mais le fait-test réapparaît
   quasi mot pour mot dans la justification du second run — preuve que le
   fichier est bien lu, mais seulement comme argument d'appoint, jamais
   comme source de l'année elle-même.

**Cause identifiée dans le prompt** : une règle "PRIORITÉ ABSOLUE" donne
la main aux jalons de `registre_evenements.md` (chronologie interne du
scénario) dès qu'un jalon correspond au profil de la fiche — "plus fiable
que ton propre jugement qualitatif seul". Comme la quasi-totalité des
fiches du vault évoquent une origine de crise/rupture quelque part dans
leur texte (souvent `description_journalistique`, pas toujours `role_
dans_scenario`), cette règle se déclenche presque systématiquement.
`etat_du_monde_reel.md` ne sert alors qu'à justifier que 2026 est "trop
tôt", jamais à choisir la vraie date.

**Ce n'est pas un bug de câblage** (prouvé mécaniquement : le contenu du
fichier apparaît bien, verbatim, dans le prompt réellement construit —
testé directement sans appel LLM) — c'est un choix de conception implicite
qui neutralisait le fichier dans la pratique.

---

## 4. Chantier `--ancrage-temporel` — création d'entités "récentes" à la demande

Suite logique du constat du §3 : pour garantir que certaines *nouvelles*
entités restent bien ancrées dans le présent, un flag explicite plutôt
qu'un espoir statistique.

- **`generate_instances.py`** et **`create_entities_and_instances.py`** :
  nouveau flag CLI `--ancrage-temporel {libre,recent}` (défaut `libre`,
  comportement inchangé).
- **Mode `recent`** : force `annee_debut` entre 2026-2029, `age_
  historique="émergent"`, `generation="transition"`, ignore délibérément
  la chronologie du scénario, exige un ancrage direct dans `etat_du_monde_
  reel.md`.
- **Testé en conditions réelles par David** — résultat "Les Veilleurs des
  Interstices" (2027) : validé, wiring confirmé (tag `[ANCRAGE RÉCENT]`
  visible dans le log).

### Bug de maturité trouvé et corrigé
Premier test réel : l'entité générée en mode `recent` avait un profil
"émergent" en métadonnées mais un texte décrivant une institution déjà
pleinement consolidée (réseau de checkpoints intercontinentaux, badges
IA, emblème historique). **Consigne de maturité ajoutée** : le texte
narratif doit rester cohérent avec une origine récente et fragile, pas
seulement les champs de métadonnées. **Retesté avec succès** : deuxième
génération ("Les Veilleurs des Lisières Flottantes") nettement plus
modeste, low-tech, légitimité disputée — comparaison ligne à ligne
documentée dans la conversation.

### `generate_instances.py` ajouté au GUI
Nouvelle entrée `generate_instances` dans `scripts_config.json`
(`--entity` en dropdown dynamique via `slug_type: entities`, déjà
disponible côté `app.py`). **⚠️ Point de vigilance signalé au §9** :
`USER_MANUAL_COMPLET.md` classait ce script comme "Legacy — fusionné dans
`create_entities_and_instances.py`" — à trancher avec David si le script
doit redevenir un outil actif à part entière ou si cette réintégration au
GUI doit être reconsidérée.

### Bug de retry sur entités rejetées (mode auto)
Découvert en test réel : une entité rejetée pour une simple faute de
frappe LLM sur un slug de variable (`systeme_productifs_travail` au lieu
de `systemes_productifs_travail`) n'avait aucune seconde chance — perte
sèche du slot entier. **`step_auto_fix_entity()` ajoutée** : retry ciblé
avec feedback sur les erreurs précises, jusqu'à `MAX_FIX_ATTEMPTS` (2),
symétrique du mécanisme déjà existant en mode `custom`. **Deuxième bug
trouvé au premier vrai test** : le LLM gardait le même `nom` (donc le même
slug) à travers les deux tentatives de correction sur un problème de
collision de slug, la consigne "ne change rien sauf ce qui est concerné"
ne faisant pas le lien implicite slug↔nom. Clarification explicite
ajoutée, **confirmée résolue** au test suivant (nom distinct dès le
premier essai).

---

## 5. Chantier "traçabilité graduée" (`ancrage_reel`) — 5 rounds de tests réels

Demande de David : renforcer la cohérence avec `etat_du_monde_reel.md` de
façon progressive selon la distance temporelle, plutôt qu'un principe
vague. Nouveau champ `ancrage_reel` (obligatoire selon la distance),
**validé mécaniquement**, pas seulement suggéré en prose — ajouté aux 3
scripts (`generate_instances.py`, `create_entities_and_instances.py`,
`fix_annee_debut_placeholder.py`).

**Chronologie des tests réels sur la fiche AMMC (`--dry-run`), chacun
suivi d'un correctif avant le test suivant :**

1. **Bande graduée 0-50 ans, prose seule** → le LLM recopie le nom du
   jalon fictif (`Traité mondial sur l'eau, 2038`) dans `ancrage_reel`.
2. **Prose renforcée avec contre-exemple explicite** → contournée plus
   subtilement (même jalon, habillé d'une parenthèse pour paraître réel).
3. **Garde-fou mécanique ajouté** (détection de séquences de mots
   identiques entre `ancrage_reel` et le registre, seuil 4 mots) →
   **faux positif** : bloque une référence légitime à la vraie AIE
   (Agence Internationale de l'Énergie) à cause d'une collision fortuite
   avec un jalon fictif sans rapport ("Agence Internationale de la
   Fusion", 2045).
4. **Seuil relevé à 6 mots** → un nouveau test révèle un **bug de fond**,
   pas un problème de seuil : recherche par sous-chaîne de caractères au
   lieu de comparaison mot à mot ("de l'" matchait le début de "de la"
   par hasard de caractères). **Corrigé par comparaison de tuples de
   mots** (robuste, élimine structurellement ce type de faux positif).
5. **Test réussi** : la fiche passe, `ancrage_reel` cite un fait plausible
   de 2026 (tensions institutionnelles, AIE, ressources critiques).

### Recadrage important — resserrement de la bande à 10 ans
En examinant le résultat final (2038, sans lien direct nommé avec 2026),
**David a interrogé la nécessité même du garde-fou pour cette distance** :
un jalon de scénario déjà construit sérieusement (via `signal_to_state`,
lui-même issu à l'origine d'une projection de tendances réelles) justifie
déjà la date à 12 ans — exiger *en plus* un ancrage réel explicite est une
couche de rigueur coûteuse (5 tours de patch ce soir) sans gain clair de
qualité. **Décision : resserrement de la bande obligatoire de 50 ans à 10
ans** — `ancrage_reel` obligatoire seulement pour `annee_debut < 2036`,
optionnel au-delà (le contrôle anti-recyclage du registre continue de
s'appliquer si le champ est rempli, même optionnellement). Testé et
confirmé sur les 3 scripts : 2038 passe sans ancrage_reel, 2030 sans
ancrage_reel échoue toujours, 2030 avec ancrage_reel valide passe.

### Piste identifiée mais non codée — connexion au présent à l'échelle du vault
Question de David : comment s'assurer que le vault dans son ensemble
reste connecté au présent, si la contrainte par fiche est desserrée ?
Deux réponses données en session, la seconde restant à construire :
1. Le flag `--ancrage-temporel recent` couvre déjà le cas "je veux
   sciemment semer des entités récentes".
2. **Idée non codée** : le mode "Auto-suggest — suggestions depuis gaps"
   existant (`analyze_entity_coverage()` dans `create_entities_and_
   instances.py`) mesure déjà 3 dimensions de couverture du vault
   (géographie, zones absentes, catégories) — **mais aucune dimension
   temporelle**. Proposition : ajouter une 4e dimension (distribution de
   `annee_debut` par bande, par scénario) pour que l'auto-suggest
   détecte et comble activement un déséquilibre, plutôt que de bloquer
   des fiches individuelles a posteriori. **Non implémenté cette
   session** — voir backlog.

---

## 6. Fichiers livrés cette session (récapitulatif complet)

| Fichier | Statut |
|---|---|
| `etat_du_monde_reel.md` | Enrichi 2 fois (perspective ~10-15 ans + ~200 ans) |
| `export_prompt_veille.py` | Nouveau, plusieurs correctifs (dates FR, sous-variables, hors_categories) |
| `import_veille_etat_monde.py` | Nouveau, plusieurs correctifs (dates FR, garde-fou fraîcheur, hors_categories) |
| `generate_instances.py` | `--ancrage-temporel`, contrainte de maturité, `ancrage_reel` gradué puis resserré, entrée GUI ajoutée |
| `create_entities_and_instances.py` | Idem + `step_auto_fix_entity()` (retry entités rejetées) + fix slug↔nom |
| `fix_annee_debut_placeholder.py` | `ancrage_reel` gradué puis resserré à 10 ans, `detect_registre_leakage()` |
| `scripts_config.json` | 2 entrées veille + 1 entrée `generate_instances` + option `--ancrage-temporel`/`--force` sur `create_entities` |
| `app.js` | 1 ligne ajoutée (section menu "Référence — monde réel") |

Tous testés soit mécaniquement (construction de prompt sans appel LLM,
comme le fait-test tracé et la comparaison de tuples de mots), soit en
conditions réelles par David avec correction itérative jusqu'à
validation — aucun appel API n'a été fait côté Claude cette session (pas
de clé configurée dans le bac à sable), tous les tests réels ont été
faits par David dans son environnement.

---

## 7. Ce qui reste ouvert

### 7.1 — Run `--all` — résultat connu, voir §9 pour la suite complète
David a lancé `python3 fix_annee_debut_placeholder.py --all` en toute fin
de la première partie de session. **Résultat final, après plusieurs
itérations de correctifs documentées en §9** : vault entier traité, 0
échec persistant, script rendu réellement idempotent (confirmé par un
run à vide produisant `Traitées: 0` sur toute la ligne).

### 7.2 — Validation GUI, toujours en attente
Aucune des entrées touchées/créées cette session n'a été testée dans un
vrai navigateur : les 2 entrées veille, `generate_instances`, et les
options ajoutées à `create_entities`. `gui_verified: false` partout.
Protocole de test déjà esquissé en session (checklist dates, garde-fou de
fraîcheur, sections indépendantes) — voir conversation pour le détail.

### 7.3 — Discrépance à trancher : statut de `generate_instances.py`
Le manuel utilisateur (avant mise à jour) classait ce script comme
"Legacy — fusionné dans `create_entities_and_instances.py`". Cette
session l'a traité comme un outil actif (mis à jour avec `--ancrage-
temporel`, ajouté au GUI). À clarifier : la fusion documentée était-elle
complète en pratique, ou ce script a-t-il un vrai usage résiduel
(backfill d'instances pour entités déjà créées) qui justifie son
maintien actif ?

### 7.4 — Dimension temporelle pour l'auto-suggest (voir §5 fin)
Idée esquissée, non codée : ajouter la distribution de `annee_debut` par
bande à `analyze_entity_coverage()`, pour que le mode auto-suggest
propose activement des créations dans les bandes sous-représentées.

### 7.5 — Reliquats de la consolidation précédente (7 août soir), toujours en attente
Cinq points identifiés en tout début de cette session, jamais traités
faute de priorité (le chantier `annee_debut` a pris toute la session) :
1. Fausse alerte `depends_on` — confirmé non-problème, rien à corriger.
2. Trois items du 2 août jamais confirmés déployés (`instance_template.md`,
   limite du panneau Revue, confirmation redémarrage Flask).
3. Gap de process : le backlog du 2 août ne listait pas ses propres
   points de reprise (mode Forcer/plafonnement) dans sa section "reste à
   faire".
4. Nettoyage optionnel des fichiers de rotation — jamais repris, sans
   urgence.

---

## 9. Compléments de fin de session — après validation GUI du run principal

Suite directe des sections précédentes : plusieurs bugs supplémentaires
trouvés et corrigés en observant les runs réels de David sur le vault
complet, jusqu'à convergence totale.

### 9.1 — Bug de rapport : les échecs n'étaient jamais tracés
Le rapport `fix_annee_debut_placeholder.md` ne contenait que les succès
(`report_line = None` sur échec persistant) — David a dû recoller la
sortie console pour identifier ses 2 premiers échecs. **Corrigé** : les
échecs apparaissent désormais dans le rapport (`❌ ÉCHEC PERSISTANT —
<détail>`), au même titre que les succès.

### 9.2 — Nouveau bug : confusion entre date réelle et date fictive
Un échec réel a révélé un cas non anticipé : `union_africaine_
resilience_reference` proposée à `annee_debut=2002` — le LLM avait
confondu la date de fondation **réelle** de l'Union Africaine (2002) avec
l'origine de sa **version fictive** dans le scénario. **Deux correctifs,
dans les 3 scripts concernés** (`fix_annee_debut_placeholder.py`,
`generate_instances.py`, `create_entities_and_instances.py`) :
- Consigne explicite dans le prompt : ignorer toute date de fondation
  réelle d'une organisation existante, `annee_debut` décrit uniquement
  l'origine de la fiction.
- Message d'erreur de validation enrichi d'un indice ciblé quand la
  valeur est < 2026, pour aider le retry à se corriger plus vite.

**Découverte annexe importante en vérifiant ce point** : `generate_
instances.py` et `create_entities_and_instances.py` n'avaient **aucune**
validation de plage sur `annee_debut` — une valeur hors [2026-2098]
n'était jamais rejetée, juste ramenée **silencieusement** à 2026 au
moment d'écrire le fichier (`write_instance_file`), sans jamais remonter
en `needs_review`. Corrigé dans les deux scripts : même vérification de
plage + même indice de correction que `fix_annee_debut_placeholder.py`.

### 9.3 — Bug d'idempotence : le script retraitait indéfiniment les fiches déjà confirmées
David a remarqué qu'un run répétait presque exactement les mêmes fiches
d'un lancement à l'autre. Cause : une fiche "confirmée à 2026" (le LLM
juge que 2026 est correct) n'était **jamais écrite sur disque** — son
`annee_debut` restait littéralement 2026, indiscernable d'un placeholder
jamais traité. `find_target_fiches()` la retrouvait donc à chaque run,
pour rien (35/38 fiches d'un run typique). **Corrigé** : nouveau champ
`annee_debut_verifiee: true`, posé sur toute fiche traitée avec succès
(confirmée ou corrigée) ; `find_target_fiches()` ignore désormais les
fiches déjà marquées. **Confirmé résolu par David** : après un run de
rattrapage (pour marquer les fiches déjà traitées avant ce correctif),
un nouveau `--all` a produit `Traitées: 0` sur toute la ligne — le
script est maintenant réellement idempotent.

### 9.4 — Chantier `annee_debut` officiellement clos
État final vérifié par David : vault entier passé en revue, 0 échec
persistant, script idempotent (0 retraitement sur relance à vide).

### 9.5 — `fix_annee_debut_placeholder.py` intégré au GUI
Nouvelle entrée `fix_annee_debut_placeholder` dans `scripts_config.json`,
section `entites_nettoyage` (même famille que `fix_alliances_
oppositions`) : `--all`/`--scenario` en exclusion mutuelle + requis
ensemble, `--slug` en dropdown dynamique, `--limit`, `--dry-run` avec
avertissement sur le coût API réel malgré le mot "simulation". Vérifié
avant ajout : pas d'`input()` dans le script (pas de risque de blocage
GUI). Aucune modification à `app.py`/`app.js`. `gui_verified: false`.

---

## 10. État des lieux `annee_fin` — nouveau chantier identifié, PAS encore traité

Question de David en clôture du chantier `annee_debut` : le même trou
existe-t-il pour `annee_fin` ? Vérification faite, avec un nouveau script
d'audit (`audit_etat_temporel_fin.py`, nouveau, ajouté au GUI section
`validation` — voir §11).

### Diagnostic confirmé
Le schéma JSON envoyé au LLM à la création d'une instance montre
`"annee_fin": null` codé en dur comme exemple, sans lien structurel avec
`etat_temporel` (`actif|disparu|transformé|clandestin|historique|
mythifié`). Aucune validation ne vérifie leur cohérence. `fix_annee_
debut_placeholder.py` ne touche jamais `annee_fin` (hors de son scope).

### Chiffres réels (vault complet, 710 fiches)
- Distribution `etat_temporel` : `actif` 657, `transformé` 28,
  `clandestin` 23, `disparu` 2, **`historique` et `mythifié` : 0
  occurrence dans tout le vault** (valeurs du schéma jamais utilisées en
  pratique — à garder en tête, pas nécessairement un problème).
- **30 fiches** (`transformé` + `disparu`) ont un état impliquant
  normalement une fin narrative.
- **28/30 (93,3 %) n'ont aucune `annee_fin` renseignée.**
- `clandestin` (23 fiches) volontairement **exclu** de ce calcul —
  classé par convention comme "n'impliquant pas de fin" dans le script
  d'audit, mais David note que ce n'est pas forcément juste : une entité
  clandestine pourrait légitimement avoir une date de fin selon son
  contexte narratif précis — **du cas par cas plutôt qu'une règle
  automatique**, à trancher au moment de construire le chantier, pas
  aujourd'hui.

### Décision de David
**Chantier volontairement différé** — ampleur bien plus réduite que
`annee_debut` (28 fiches contre 477 au départ), mais pas traité cette
session faute de temps. Reste ouvert pour une prochaine session (voir
§13 point de reprise). Ne pas confondre avec `historique`/`mythifié`
(0 occurrence, pas un chantier de correction — juste une observation) ni
avec `clandestin` (23 fiches, cas par cas à définir, pas une règle
automatique évidente).

---

## 11. Scripts d'audit convertis et ajoutés au GUI

Question de David : les scripts de diagnostic (lecture seule, aucune
écriture) seraient-ils utiles dans le GUI pour la maintenance courante ?
Réponse : oui, faits et livrés cette session.

**Conversion technique préalable** (les 3 scripts existaient déjà en
CLI mais avec un argument positionnel `sys.argv[1]`, incompatible avec le
mécanisme d'options `--flag` du GUI) :
- `audit_dates_instances.py`
- `audit_type_relation_dominante.py`
- `audit_etat_temporel_fin.py` (nouveau cette session, voir §10)

Les 3 convertis vers `argparse` avec un flag `--dossier` optionnel,
défaut calculé automatiquement (`instances/` du vault courant, même
convention `VAULT_ROOT`/`GENERATOR_DIR` que le reste du pipeline) —
utilisables en un clic sans aucun paramètre requis. Testés : fonctionnent
avec et sans `--dossier` explicite.

**Ajoutés au GUI**, section `validation` (aux côtés de `validate.py`) —
3 nouvelles entrées, aucune modification `app.py`/`app.js` nécessaire
(mécanisme générique de lancement de script + `type: text` déjà
supporté). `gui_verified: false` sur les 3.

---

## 12. Pistes identifiées pour une prochaine session, non traitées

### 12.1 — Même approche pour les événements, pas seulement les instances ?
Question de David, non explorée cette session : tout le chantier
`annee_debut`/`ancrage_reel`/traçabilité graduée a porté exclusivement
sur les **instances**. Les **événements** (`inject_custom_events.py`,
`registre_evenements.md`) ont-ils un problème de nature similaire (dates
mal ancrées dans le réel, ou tout autre souci analogue) ? Diagnostic
jamais fait — à vérifier en premier lieu avant de décider si la même
approche doit s'y appliquer.

### 12.2 — Répartition homogène des dates + ancrage sur les crises du vault, pour la génération automatique
Extension de l'idée déjà notée au §12.4 de la version précédente de ce
handoff (dimension temporelle pour l'auto-suggest). David précise
l'intention : s'inspirer du mécanisme déjà existant pour la **géographie**
dans `analyze_entity_coverage()` (mode auto-suggest, détecte les zones
sans instance et les propose comme cibles) et construire l'équivalent
temporel — deux volets distincts à concevoir ensemble :
1. **Contrainte de répartition homogène** — éviter qu'une génération
   automatique (mode `auto`/`auto-suggest`) ne fasse encore converger
   massivement les nouvelles entités vers une poignée d'années
   sur-représentées (rappel du constat du §8 de la version précédente :
   **2041 concentre à lui seul 22 % du vault**, 157/710 fiches — very
   probablement parce qu'un jalon du registre à cette date correspond au
   profil d'un grand nombre d'entités différentes).
2. **Ancrage sur les crises réelles du vault** — pas une répartition
   purement arithmétique/aléatoire : les nouvelles dates générées
   devraient continuer à s'appuyer sur les jalons du registre du
   scénario (crises, ruptures) plutôt que d'ignorer la cohérence
   narrative au profit d'un simple équilibrage statistique.

**Non conçu, non codé cette session** — nécessiterait probablement une
nouvelle dimension dans `analyze_entity_coverage()` (distribution de
`annee_debut` par bande, par scénario) et une consigne de prompt adaptée
pour le mode auto-suggest, dans l'esprit de ce qui existe déjà pour la
géographie. À concevoir en détail lors d'une prochaine session.

---

## 12bis. Investigation `etat_temporel`/`age_historique`/`generation` — chantier de conception, PAS codé

Parti du point 2 des "5 sujets" identifiés par David en observant les 28
fiches `annee_fin` manquantes (§10) : la fiche `zones_extractivistes_
corridors_eco_communalism` combine `age_historique: ascendant` et
`etat_temporel: transformé` — une contradiction potentielle. L'investigation
qui a suivi a débordé largement le cas isolé et révélé plusieurs problèmes
de fond sur ces 3 champs, jamais traités jusqu'ici. **Rien n'a été codé
cette session** — uniquement de l'investigation et de la conception,
prêtes à être construites à la prochaine session.

### Étape 1 — Confirmation de l'incohérence sur la fiche
Lecture complète de `zones_extractivistes_corridors_eco_communalism.md` :
le texte (`role_dans_scenario`, `description_journalistique`, `tensions_
narratives`) décrit sans ambiguïté une transformation **en cours**, jamais
achevée (le mot "reste" employé 3 fois pour des tensions toujours vives).
Confirmé : vraie incohérence, pas une lecture ambiguë. Hypothèse de cause :
confusion entre "transformé" au sens littéral (le lieu physique a été
transformé) et "transformé" au sens de statut narratif attendu par le
schéma (l'entité a fini d'évoluer).

### Étape 2 — Aucune définition officielle n'existe
Recherche dans tout le code et le manuel : les valeurs de `etat_temporel`/
`age_historique`/`generation` sont de simples énumérations (liste
séparées par `|` dans le prompt), **sans aucun texte expliquant ce que
chaque valeur signifie**. Aucune définition à citer comme référence — tout
ce qui suit repose sur des définitions **inférées** par Claude à partir de
l'usage observé sur de nombreuses fiches cette session, **jamais validées
par David formellement** (point resté ouvert, voir §12bis point de reprise
ci-dessous).

**Découverte annexe** : `age_historique` n'a **aucune validation
mécanique** nulle part dans le pipeline (pas de `VALID_AGE_HISTORIQUE`,
contrairement à `VALID_ETATS` pour `etat_temporel`) — rien n'empêche le
LLM d'inventer une valeur hors de la liste suggérée en prose.

### Étape 3 — Cartographie complète des usages dans le pipeline
Recherche exhaustive (`grep -rl` sur les 3 champs, tous scripts) :

| Champ | Utilisé dans | Rôle |
|---|---|---|
| `etat_temporel` | `loader.py`, `validate.py`, `generate_instances.py`/`create_entities_and_instances.py` | Structurel + validé (avec bug, voir étape 4) |
| `etat_temporel` | **`prompt_builder.py` ligne 1478** | **Affiché comme badge dans le prompt final d'écriture d'article** (`[TRANSFORMÉ]` à côté du nom de l'entité) — seul des 3 champs à avoir un impact narratif direct sur l'article généré |
| `age_historique` | `loader.py`, scripts de création (signal d'entrée pour `annee_debut`) | Jamais affiché à l'article — outil de génération interne uniquement |
| `age_historique` | `validate.py`, check A2 uniquement | Validé seulement dans le contexte des acteurs cités dans un événement, jamais sur l'ensemble des 710 fiches |
| `generation` | `loader.py`, scripts de création | Même rôle que `age_historique` — jamais validé nulle part, jamais affiché à l'article |

**Confirmé** : les événements (`inject_custom_events.py`, `inject_custom_
signals.py`) n'ont **aucun** de ces 3 champs — système propre aux
instances uniquement.

### Étape 4 — `validate.py` a déjà un système de validation, mais buggé
Découverte majeure : `validate.py` contient déjà des checks sur ces champs
(A2, C1-C4) — **mais avec un bug de cohérence interne**, trois définitions
différentes du même concept dans le même fichier :
```
INACTIVE_ETATS = {"disparu", "historique"}                          (ligne 1187, check A2)
ETAT_INACTIFS  = {"disparu", "transformé", "historique", "mythifié"} (ligne 1266, check C3 — le bon ensemble)
C4 (ligne ~1319) : etat == "disparu"                                  (hardcodé, ni l'un ni l'autre)
```
`C4` (le check censé repérer "état inactif sans `annee_fin`") ne teste que
`disparu` littéralement, malgré le fait que `ETAT_INACTIFS` (complet et
correct) existe déjà 50 lignes plus haut dans le même fichier. C'est
précisément ce bug qui rend les 28 fiches invisibles à l'outil de
validation existant — **`validate.py` n'a pas besoin d'un nouveau
chantier, juste d'une correction d'une ligne pour révéler le vrai
périmètre du problème.**

### Étape 5 — Plan en 3 volets proposé (avant la décision de fusion, étape 7)
1. **Empêcher que ça grossisse** — ajouter `VALID_AGE_HISTORIQUE`/`VALID_
   GENERATION`, exiger `annee_fin` dès la création si `etat_temporel`
   l'implique (extension du système `ancrage_reel` du chantier `annee_
   debut`), ajouter une cohérence `etat_temporel`↔`age_historique` dans
   `validate_instance()`.
2. **Corriger `validate.py`** — aligner `C4` et `INACTIVE_ETATS` sur
   `ETAT_INACTIFS`, ajouter un check de cohérence général (pas limité au
   contexte événements).
3. **Corriger l'existant** — nouveau script `fix_annee_fin_placeholder.py`
   sur le modèle de `fix_annee_debut_placeholder.py`, une fois le vrai
   périmètre connu via `validate.py` corrigé.

### Étape 6 — Cartographie des combinaisons, avant de coder quoi que ce soit
David a posé la question clé avant de lancer le code : a-t-on besoin
d'une cartographie des combinaisons possibles pour éviter des règles de
validation mal calibrées ? Réponse : oui pour les définitions et les
paires incohérentes connues, mais pas une matrice complète des 336
combinaisons théoriques (6 `etat_temporel` × 8 `age_historique` × 7
`generation`) — disproportionné, `generation` étant largement orthogonal
aux deux autres.

**Tableau de définitions inférées produit** (à valider par David — voir
point de reprise) pour les 3 champs, plus une **matrice de compatibilité
`etat_temporel`↔`age_historique` par groupes** (pas cellule par cellule) :
- Groupe "vivant" (`émergent/marginal/ascendant/dominant/mature`) ↔
  cohérent avec `actif`/`clandestin` uniquement.
- Groupe "fin de vie" (`déclinant/résiduel`) ↔ zone grise assumée, cohérent
  avec `actif`, `transformé` ou `disparu`.
- `age_historique: mythifié` ↔ cohérent uniquement avec `etat_temporel`
  ∈ {mythifié, historique, disparu}.

Le cas `zones_extractivistes_corridors` (`ascendant`+`transformé`) tombe
dans la première règle — confirmé comme une vraie incohérence par cette
grille, pas une zone grise.

### Étape 7 — Décision : Option B retenue (fusion des champs)
Deux options présentées à David :
- **Option A** (rejetée) — correctif léger, garder les 3 champs séparés,
  juste coder la matrice de compatibilité comme règle de validation.
- **Option B** (**retenue**) — **fusionner `etat_temporel` + `age_
  historique` en un seul axe narratif continu**, motivé par le constat que
  les deux champs racontent la même histoire (le cycle de vie de
  l'entité) avec deux vocabulaires qui se chevauchent — signal fort :
  `mythifié` existe dans les DEUX listes actuellement.

**Nouvel axe unique proposé** (ordre à valider/affiner avec David) :
```
émergent → ascendant → dominant → mature → déclinant → résiduel → transformé → disparu → mythifié/historique
```

**`clandestin` sort du nouvel axe** pour devenir un champ booléen
indépendant (`est_clandestin: true/false`) — la visibilité (caché ou non)
est jugée orthogonale au cycle de vie : une entité peut être dominante-et-
clandestine ou émergente-et-clandestine, ce que l'ancien schéma ne pouvait
pas représenter (un seul état à la fois).

**`generation` reste largement inchangé** — jugé orthogonal (question de
contexte de naissance, pas de statut actuel), sans recouvrement à
corriger. Seule réserve notée : certaines valeurs (`forteresse`, `ère
cognitive`) semblent taillées pour un scénario précis plutôt qu'universelles
— à vérifier si elles sont vraiment utilisées à travers tous les
scénarios ou seulement certains (jamais vérifié cette session).

**Ampleur du chantier si Option B est construite** : touche `loader.py`,
les 5 scripts de création/correction (`generate_instances.py`, `create_
entities_and_instances.py`, `enrich_minimal.py`, `fix_annee_debut_
placeholder.py`, `officialize_alliances.py`), `prompt_builder.py`,
`validate.py`, plus un script de migration rétroactive des 710 fiches
existantes (mapper les anciennes paires `etat_temporel`+`age_historique`
vers le nouvel axe unique, et `etat_temporel: clandestin` vers `est_
clandestin: true`). **Rien de tout ça n'a été codé cette session** — c'est
un chantier de conception, prêt à être construit en détail.

---

## 13. Point de reprise mis à jour pour la prochaine session

**Priorité proposée : le chantier de fusion (§12bis) avant `annee_fin`
(§10)** — puisque `annee_fin` sera plus simple à construire une fois
qu'il n'y aura plus qu'un seul champ de statut à croiser avec lui, plutôt
que deux.

1. **Valider les définitions inférées** des 3 champs (§12bis étape 2 et
   6) — jamais confirmées formellement par David, tout le chantier de
   fusion en dépend.
2. **Concevoir le détail du nouvel axe unique** (§12bis étape 7) — ordre
   exact final, règles de migration précises pour les 710 fiches
   existantes, cas limites (ex. `age_historique: mythifié` actuel — vers
   quelle position exacte du nouvel axe ?).
3. **Construire la migration** — `loader.py`, les 5 scripts de création/
   correction, `prompt_builder.py`, `validate.py`, script de migration
   rétroactive des 710 fiches, `clandestin` → `est_clandestin`.
4. **Chantier `annee_fin`** (§10) — 28 fiches (nombre à revérifier une
   fois `validate.py` corrigé/le nouvel axe en place) à corriger
   rétroactivement, sur le modèle `annee_debut`. Le cas `clandestin`
   devient plus simple à trancher une fois converti en booléen
   indépendant (§12bis étape 7).
5. **Correctif isolé possible avant la fusion, si besoin d'un résultat
   rapide** : aligner `C4`/`INACTIVE_ETATS` sur `ETAT_INACTIFS` dans
   `validate.py` (§12bis étape 4) — une ligne, redonne une vision fiable
   via l'outil déjà existant, indépendamment du calendrier de la fusion.
6. **Points annexes des "5 sujets" du 8 août, toujours en note** :
   concentration sur 2041 (§8 de la session précédente, écho de 157/710
   sur tout le vault — lié au futur chantier de répartition homogène,
   §12.2) ; encodage portugais cassé dans certains slugs (mineur,
   `rede_paulista_de_distribuic_o_algor_tmica`) ; répartition très
   inégale par scénario sur les 28 fiches (19/28 sur `breakdown`, jugé
   probablement normal, jamais creusé davantage).
7. Test navigateur des entrées GUI (inchangé, voir version précédente de
   ce handoff §7.2/§1.2 du backlog).
8. **Diagnostic événements** (§12.1) — vérifier si le même problème que
   celui traité sur les instances existe côté `inject_custom_events.py`.
9. **Répartition homogène + ancrage crises** (§12.2) — extension
   temporelle d'`analyze_entity_coverage()` pour le mode auto-suggest.
10. Trancher le statut de `generate_instances.py` (§7.3, inchangé).
11. Reliquats du 7 août (§7.5, inchangés) — toujours en attente.

