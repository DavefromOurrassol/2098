
---

## ✅ Signaux faibles — polarité, persistance, idées en texte libre — CLOS le 27 septembre 2026 (après-midi)

**Origine** : question de David (« fais la synthèse du mécanisme d'injection
des signaux faibles »). La lecture du code (`inject_custom_signals.py`,
`dynamique.py`, `loader.py`, `snapshot.py`, une fiche réelle) a fait
apparaître cinq défauts, puis deux demandes (persistance configurable,
outil « idées → queue »).

**Défauts trouvés et corrigés** :
1. **Double gain dans les contributeurs** (`snapshot.appliquer_dynamique`) :
   `forcage()` applique déjà `GAIN_CHOCS`, la liste « surtout : … » le
   réappliquait (force ÷4, seuil 0,2 point jamais atteint, « —
   propagation » affiché à tort). Niveaux calculés non touchés. Vérifié :
   aucun autre script ne le fait (`grep GAIN_CHOCS`). Après correctif, les
   12 variables de breakdown affichent leurs contributeurs.
2. **Une seule polarité recopiée dans les 6 scénarios** alors que la
   trajectoire narrative diverge (la fiche `decodage_langage_animaux_ia`
   n'avait des polarités différenciées que grâce à `reevaluer_polarites.py`,
   passé après coup). Corrigé : `polarite` = dictionnaire des 6 scénarios,
   `normaliser_polarites()`. Premier test réel : les 3 variables avaient
   exactement le motif de l'exemple JSON du prompt → Mistral recopiait.
   Exemple remplacé par des emplacements (`"<+1 ou -1>"`) ; second test :
   polarités différenciées d'une variable à l'autre.
3. **`delta_level: 0` dans l'exemple JSON** : un 0 recopié passait la
   validation puis était écarté en silence par le moteur. `delta_level` ≥ 1
   exigé ; plus de repli `polarite or 1`.
4. **Injection partielle remise en queue = doublons** : bloc `reprise` +
   `idee_a_remettre_en_queue` dans `needs_review.yaml`, fiche d'audit
   complétée, garde-fou section 12, `variables_cibles` = variables
   réellement injectées. Au passage : un slug déjà pris écrasait la fiche
   d'audit d'un autre signal → suffixe `_2`.
5. **Année exigée en fin de `evenement_cle`** (correctif du 13 août non
   reporté depuis les événements) : acceptée n'importe où, la dernière fait
   foi.

**Effet chiffré quasi nul en 2098** (calcul manuel : ≈ 0,2-0,4 point
résiduel pour un signal de delta 5 dont la bascule finit vers 2050-2060,
sous le seuil d'affichage de 0,5) → demande de David : rendre la durée
configurable. **Persistance** (`ephemere`/`normale`/`durable`/`permanente`)
dans `dynamique.py`, câblée pour les signaux et les événements (queue →
fiche → loader → moteur). Vérifié au préalable qu'aucun mécanisme
équivalent n'existait (seule `DEMI_VIE` globale ; `intensite` des
événements = force, pas durée ; `priorite_forcee` = présence narrative).
Pour les **instances** : persistance déduite de `trajectoire`/`annee_fin`
(« l'effet dure tant que l'entité existe »), mesurée avant/après avec le
nouvel outil `mesure_niveaux.py` : écarts ≤ 4,3 points, dans le sens de
chaque scénario ; `permanente` gardée pour les instances actives. Signal
`clerge_prompteurs_ia` passé à la main en `permanente` : il apparaît
désormais parmi les contributeurs de ses 3 variables en
new_sustainability.

**`annee_apparition`** (signaux, demande de David) : distinction apparition
(même date partout) / bascule (par scénario) ; contrainte dans le prompt +
validation. Le choc chiffré démarre toujours au début de la bascule
(option « montée dès l'apparition » proposée, non retenue).

**Idées en texte libre** : `idees_vers_queue.py` (propose, n'écrit jamais)
+ bouton GUI. Vérifié au préalable : rien d'équivalent (formulaire manuel,
modes `auto`/`auto-suggest` qui partent des manques du vault, « Promouvoir
en événement » sans LLM). Première version GUI avec une zone de texte
séparée → jugée en doublon avec Description par David → refaite : bouton
« ✨ Compléter les autres champs » sous Description. Règle d'extraction de
l'année d'apparition assouplie après le test « chine 2049 champion
économique » (champ resté vide) + rattrapage mécanique. Au passage, le
formulaire signaux ne permettait d'imposer qu'UNE variable (`select`) →
`multi_select` avec libellés.

**Tests réels** : injection `pretres_de_l_ia_2027` (3 variables, 1er essai
chacune), snapshots breakdown/new_sustainability, comparaison
`mesure_niveaux.py`, `idees_vers_queue.py` en CLI et depuis le GUI.
Testé en synthétique seulement : reprise d'injection partielle.

**Piège rappelé** : deux fois un ancien fichier resté en place
(`gui/static/app.js` non remplacé ; vérifier par `grep` d'une chaîne
propre à la nouvelle version avant de conclure à un bug).
