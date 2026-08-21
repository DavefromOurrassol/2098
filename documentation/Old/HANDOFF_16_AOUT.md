# Handoff — session du 16 août 2026

*Session menée via chat avec Claude (aucun accès direct GUI/terminal côté
Claude), David exécutant les commandes/scripts sur son vault et
rapportant les résultats, plus des tests réels via le GUI (mode Forcer)
pour les deux premiers chantiers. Objectif de départ, formulé
explicitement par David : que les trois types d'injection custom
(entités/instances par scénario, événements, signaux faibles) puissent
réellement faire évoluer le monde de 2098, avec des articles qui
reflètent ces injections. Trois chantiers traités dans l'ordre :
instances custom, signaux faibles custom, cohérence section 7 ↔ section
12 des signaux (ce dernier motivé par une question de David en cours de
route, pas prévu au départ).*

---

## 0. Contexte préalable — exploration de la matrice d'influence

Avant les trois chantiers, une session d'exploration du mécanisme de
propagation de `influence_matrix.md` a permis de confirmer précisément
son fonctionnement dans `snapshot.py` : deux usages distincts (diagnostic
narratif via `check_coherence()`/`get_thematic_tensions()`, propagation
numérique via `apply_custom_injections()`/`apply_custom_events()`), à un
seul saut, amorti ×0.5, seuil `weight ≥ 0.75`. Confirmation que seuls les
événements custom propageaient réellement à cette date — les instances
custom n'avaient aucun script qui alimentait `injection.type: custom`
malgré le mécanisme de consommation déjà présent, et les signaux
n'avaient aucun mécanisme de delta chiffré du tout. C'est ce diagnostic
qui a directement motivé les deux premiers chantiers ci-dessous.

---

## 1. Instances custom — injection matricielle (`impact_sur_variables`)

### Décision de conception

Plafond du delta discuté avec David avant tout code : pas une constante
fixe comme les événements (`MAX_DELTA_LEVEL = 25`), mais dérivée de
`impact_systemique_global × 5` (0-25) — champ déjà renseigné sur chaque
instance, réutilisé plutôt que d'introduire un second jugement de
magnitude potentiellement incohérent. Borne aussi l'empilement
multi-variables (une instance touche souvent 3-5 variables). **Validé
par David.**

### Développement

Nouveau paramètre `injection_custom` (défaut `False`) propagé à travers
toute la chaîne `instance_generation_common.py` (`build_instance_prompt`,
`validate_instance`, `write_instance_file`, `process_entity_scenario`) et
`create_entities_and_instances.py` (`generate_instances_for_entity`),
activé **uniquement** depuis `process_custom_idea()` (mode `custom`) —
aucun changement de comportement pour `auto`/`auto-suggest` ni pour
`generate_instances.py`. Quand actif, prompt LLM enrichi avec la consigne
de plafond + schéma JSON pour `impact_sur_variables`/
`propagation_via_matrice`/`contexte_injection` ; `validate_instance()`
vérifie mécaniquement le plafond ; `write_instance_file()` écrit le bloc
`injection:` (jusque-là toujours vide en pratique).

### Deux bugs trouvés en testant en conditions réelles

**(a) Format non respecté par Mistral** — sur les 6 scénarios générés
pour l'entité test ("Gelecek Meclisi"), `propagation_via_matrice`/
`contexte_injection` étaient tantôt dupliqués à l'intérieur de chaque
élément de `impact_sur_variables`, tantôt absents du niveau racine (2
scénarios sur 6 sans aucun champ racine). Corrigé par un filet de
sécurité dans `write_instance_file()` (dérivation depuis les valeurs par
entrée si le champ racine est `None`) en plus d'un resserrement du
prompt ("ATTENTION FORMAT"). Reconfirmé propre sur un second test dry-run
complet.

**(b) Bug YAML cassant toute la fiche** — `contexte_injection` était
écrit en scalaire brut sur une seule ligne plutôt qu'en bloc replié `>`
comme tous les autres champs texte de la fiche. Découvert via un test
GUI réel (mode Forcer, scénario `eco_communalism`) : "Perturbations
custom actives" ne montrait aucune ligne pour l'instance testée, et les
logs affichaient `Avertissement YAML ... mapping values are not allowed
here`, pointant vers un `" : "` dans le texte de `contexte_injection`
(quasi systématique en français journalistique). Conséquence : la fiche
entière tombait en repli sur des valeurs par défaut (`trajectoire:
mature`, `impact:0/5`, `annee_debut` implicite 2026), et `injection.type`
ne valait plus jamais `custom` — le mécanisme entier était silencieusement
neutralisé. Corrigé (`contexte_injection: >`), testé unitairement avec le
texte exact qui avait cassé.

### Validation finale

Les 6 fiches régénérées après les deux correctifs : YAML propre sur les
6 (confirmé par reparsing), plafond respecté sur les 18 impacts (aucun
dépassement, y compris un cas exactement à la borne), `annee_injection`
cohérent avec `annee_debut`. **Confirmation ultime en conditions
réelles** : génération d'article réelle (mode Forcer, `eco_communalism`,
non prévue comme définitive — un vrai appel API a eu lieu et un article a
été sauvegardé) montrant dans les logs `snapshot.py` :
```
[snapshot] Injection custom 'Meclis des Futurs Fragmentés' (an 2047, 51 ans d'effet)
  → gouvernance_institutions : 75 → 87.0 (delta:+12.0)
  → organisation_territoires : 40 → 48.0 (delta:+8.0)
  → technologie_information : 53.4 → 58.4 (delta:+5.0)
```
Chantier considéré clos.

---

## 2. Signaux faibles custom — injection matricielle (`impact_sur_variables`)

### Différences structurelles avec les instances

Un signal cible **une seule** variable par appel LLM (pas de liste), et
chaque scénario porte déjà sa propre fenêtre temporelle (`date_bascule`,
déjà écrite pour le bloc narratif `signal_to_state`) — `annee_injection`/
`duree` en sont donc dérivés automatiquement plutôt que redemandés au
LLM. Plafond fixe et bas, `MAX_DELTA_SIGNAL = 10` (pas de champ
`impact_*` équivalent aux instances pour le dériver), cohérent avec la
sémantique "signal faible". `propagation_via_matrice` recommandé à
`false` par défaut dans le prompt (décision prise avec David en amont du
codage).

### Développement

`inject_custom_signals.py` : prompt de `step2_develop()` enrichi des
mêmes champs, `validate_signal_block()` étendue pour vérifier le plafond.
Stockage dans un **nouveau bloc séparé** de la fiche d'audit
`signaux_custom/{slug}.md` (section "## Impact chiffré", distincte du
bloc `signal_to_state` narratif) — `contexte_injection` écrit d'emblée en
bloc replié `>`, leçon du bug (b) ci-dessus appliquée dès la conception,
jamais reproduite. Côté chargement : `loader.load_custom_signals()`
(nouveau, lit le bloc dans le corps markdown) et
`snapshot.apply_custom_signals()` (nouveau, même mécanique que les deux
fonctions sœurs, avec le scénario comme paramètre supplémentaire —
testé explicitement qu'un signal sans fenêtre pour un scénario donné n'a
aucun effet sur celui-ci).

Un bug trouvé et corrigé **avant** tout test réel, en relisant le
câblage : `event_modifications` aurait été compté deux fois dans le
prompt final (`modifications` incluait déjà les événements avant la
fusion). Corrigé.

### Validation en conditions réelles

**Aucun bug supplémentaire trouvé** — contrairement aux instances, où
Mistral avait mal placé les champs et où un bug YAML dormait. Signal réel
injecté par David (`decodage_langage_animaux_ia`, variable
`valeurs_culture_tempo_sociale`) : YAML parse propre y compris avec un
`" : "` et un `%` dans `contexte_injection`, `propagation_via_matrice`
bien un booléen au bon niveau, plafond respecté sur les 6 scénarios
(`delta_level: 5` uniforme), `annee_injection`/`duree` cohérents avec
`date_bascule` de chaque scénario. Chaîne `loader.load_custom_signals()`
→ `snapshot.apply_custom_signals()` testée directement contre ce vrai
fichier : delta appliqué correctement (`40 → 45.0` sur test synthétique
de niveau initial).

**Angle mort assumé** : ce premier signal réel avait
`propagation_via_matrice: false` — la propagation via matrice sur un
signal (`via_matrice: true`) n'a été vérifiée qu'en synthétique, jamais
sur un cas réel. Non bloquant, à garder en tête pour un futur signal.

---

## 3. Cohérence section 7 ↔ section 12 des signaux (`validate.py`)

### Origine du chantier

Parti d'une question de David sur un détail observé ("pourquoi certains
signaux en section 7 ont `(→ section 12)` et pas d'autres ?"), débouchant
sur une question plus large ("qu'est-ce qui assure que la section 12 se
nourrit de tous les éléments de la section 7 ?"). Recherche dans
`HANDOFF_26_JUILLET.md` confirmant que cette désynchronisation s'est déjà
produite réellement (signal `norvege_terres_rares_levier_geopolitique`
dupliqué le 26 juillet suite à un crash entre écriture de la fiche
variable et écriture du registre) et que deux bugs similaires ont été
trouvés le 27 juillet (annotation sans préfixe, bloc section 12 cassé par
`undo_custom.py`).

### Approche

Croiser 3 sources indépendantes (section 7, section 12, `variables_cibles`
des fiches d'audit) plutôt que de faire confiance à une seule — même
principe que le fix appliqué à `resolve_signal_variables()` le 26
juillet. Diagnostic uniquement, aucune correction automatique. **Intégré
à `validate.py` comme 9e section (sur 10 désormais)**, à la demande
explicite de David plutôt qu'un script autonome initialement envisagé.

### Faux positif massif trouvé et corrigé au premier test réel

60 avertissements sur le premier run contre le vrai vault — tous des
faux positifs. Cause : les signaux du socle initial (juin 2026,
antérieurs à l'existence même d'`inject_custom_signals.py`) utilisent un
format de section 7 complètement différent — marqueurs de catégorie
(`**technological**`, `**social**`, etc.) et simple `(→ slug)` sans le
préfixe `signal_custom:` introduit le 26 juillet. Le contrôle les
traitait à tort comme des signaux custom mal annotés. Corrigé : le
croisement 7↔12 ne s'applique désormais qu'aux signaux **prouvés
custom** (présence d'une fiche d'audit correspondante dans
`signaux_custom/`) — un signal du socle sans fiche d'audit est ignoré.

### Validation finale

Testé sur cas synthétiques reproduisant les 4 anomalies documentées
(doublon en section 12, orphelin 7→12, orphelin 12→7, `variables_cibles`
incomplet) — toutes détectées. Testé sur un cas sain synthétique — zéro
faux positif. **Confirmé sur le vault réel après correctif** :
`0 erreurs | 1 avertissement` (le seul restant, `[LOCALISATION]` sur
`gelecek_meclisi_policy_reform.md`, indépendant de ce chantier) — 0
avertissement `[SIGNALS]`, aucune vraie anomalie détectée sur l'ensemble
des signaux custom existants (26/27 juillet + celui du jour).

**Non couvert par ce contrôle** : le nouveau bloc `impact_sur_variables`
(chantier 2 ci-dessus) — vit dans un bloc YAML séparé, pas encore intégré
à cette vérification de cohérence.

---

## 4. Fichiers livrés cette session

- `instance_generation_common.py` — paramètre `injection_custom`,
  prompt/validation/écriture du bloc `impact_sur_variables`, filet de
  sécurité et correctif YAML `contexte_injection: >`.
- `create_entities_and_instances.py` — activation du paramètre en mode
  `custom`, plus deux bugs préexistants trouvés en testant :
  `idea.get('role')`/`idea.get('etat')` au lieu d'accès direct
  (`KeyError` sur champs optionnels non renseignés), exception
  silencieuse dans `run_custom_mode()` rendue visible à l'écran.
- `inject_custom_signals.py` — mêmes champs d'impact chiffré côté
  signaux, plafond `MAX_DELTA_SIGNAL`, dérivation depuis `date_bascule`.
- `loader.py` — nouvelle fonction `load_custom_signals()`.
- `snapshot.py` — nouvelle fonction `apply_custom_signals()`, correctif
  du double-comptage de `event_modifications`.
- `validate.py` — nouvelle section 9/10 `validate_signals()`, correctif
  du faux positif sur les signaux du socle.

**Redémarrage Flask requis** après changement dans `loader.py`/
`snapshot.py`/`instance_generation_common.py` (piège déjà rencontré les
sessions précédentes — à vérifier systématiquement).

---

## 5. Point de reprise suggéré pour la prochaine session

1. **Priorité toujours en attente depuis le 15 août, non traitée
   aujourd'hui** : retenter l'instance `eco_communalism` manquante pour
   "Les Veilleurs des Nappes Phréatiques" (bloquée par le garde-fou
   `ancrage_reel`, qui a correctement empêché une hallucination).
2. Confirmer sur un cas réel la propagation via matrice d'un signal
   faible (`via_matrice: true`) — testée en synthétique seulement à ce
   stade.
3. Envisager d'étendre `validate_signals()` pour couvrir aussi le bloc
   `impact_sur_variables` (cohérence du delta chiffré, pas seulement du
   narratif) — pas fait aujourd'hui, mentionné comme suite possible.
4. Chantiers Partie 1 du backlog toujours ouverts, sans changement de
   statut cette session : point #1 (validation retry longueur, 🟡, sans
   urgence), P17, Bug #27, renommage YAML génériques, troncatures JSON —
   tous gardés pour plus tard sur décision explicite de David, non
   rouverts cette session.
