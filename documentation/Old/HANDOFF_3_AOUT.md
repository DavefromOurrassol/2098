# HANDOFF — session du 3 août 2026 (à uploader dans le nouveau chat)

*Session en deux temps : (1) validation en conditions réelles des 3 points
de reprise laissés ouverts par le handoff du 2 août — plafonnement
événements/géographie, revalidation du mode Semi-guidé, ajustement des
plafonds par défaut ; (2) audit de complétude demandé par David
("est-ce que toutes les données intéressantes du snapshot/des variables
sont bien utilisées pour la génération ?"), qui a débouché sur 4 ajouts
de contenu au prompt. Méthode systématique tout du long : chaque
correctif a été vérifié par un vrai `--dry-run` avec sortie collée dans
le chat, pas seulement par lecture de code.*

---

## 1. Point de reprise §6.4 du 2 août — plafonnement événements/géographie

**Testé en conditions réelles** (`generate.py --dry-run --mode forcer
--forcer-type evenement --forcer-slug encheres_terres_rares_groenland
--forcer-scenarios policy_reform`) sur le scénario le plus chargé
(`policy_reform`, 11 événements custom, 62 zones).

**Plafonds eux-mêmes : corrects du premier coup.**
- Événements en détail complet : exactement 8 sur 11 (`— 8 sur 11 au
  total, les plus pertinents pour cet article`)
- Zones en résumé : exactement 20 lignes, puis `(+ 39 autres zones...)`
- Total zones cohérent : 3 détail + 20 résumé + 39 compact = 62 ✓

**Mais le test a débusqué deux résidus du bug §3.8 du 2 août** (la
correction de zone d'ancrage n'avait touché que la consigne textuelle
finale, pas deux autres endroits du prompt) :

### Bug A — badge `[FORCÉ]` jamais affiché sur l'événement forcé
**Cause** (`loader.py`, `select_relevant_events()`) : l'événement forcé
était bien placé en tête de la liste retournée
(`([forced] if forced else []) + selected`), mais la clé `"forced":
True` n'était jamais posée sur son dict — `prompt_builder.py` lit
`ev.get("forced")` pour afficher le badge, qui restait donc toujours
faux.
**Correctif** : `forced = dict(forced); forced["forced"] = True` avant
réinsertion, avec correction du filtre d'exclusion de `reste` (passage
de `is not forced` par identité, cassé par la copie, à une comparaison
par `slug`/`archetype`).
**Vérifié** : `[automne 2041] [FORCÉ] Enchères Circumpolaires du
Kalaallit — Protocole de Nairobi` apparaît bien dans le retest.

### Bug B — zone de l'élément forcé absente de la section géographie détaillée
Le plus significatif des deux. La consigne finale du prompt disait bien
*"ancré dans la zone Nuuk Knsf"*, mais la section `## GÉOGRAPHIE DE CE
MONDE` juste au-dessus affichait en détail complet des zones sans
rapport (Genève), reléguant Nuuk dans la liste compacte des 39 zones non
détaillées — signal contradictoire pour le LLM (aucune description/
tensions/alliés fournis pour sa vraie zone d'ancrage).
**Cause** (`prompt_builder.py`, `build_geographie_context()`) :
`zones_pertinentes` était calculé uniquement depuis
`snapshot["filtered_instances"]` (les 6 instances génériques
auto-sélectionnées, indépendantes de l'élément forcé pour un
événement/signal — contrairement à une instance forcée, qui devient
elle-même l'unique `filtered_instance`).
**Correctif** : `build_geographie_context()` reçoit maintenant `config`
en paramètre (comme `build_system_prompt()` le fait déjà pour la même
raison), lit `config.get("zone_slug")` (la vraie zone forcée, injectée
par `generate.py`) et l'ajoute explicitement à `zones_pertinentes` via
`collect_zone_chain()`.
**Vérifié** : `Nuuk (siège du KNSF-AGRC)` apparaît en détail complet
avec description/tensions/alliés dans le retest ; comptes zones
toujours cohérents (5 détail + 20 résumé + 37 compact = 62, les 2 zones
en plus étant celles qui sont passées de "compact" à "détail").

---

## 2. Point de reprise §6.3 — revalidation du mode Semi-guidé

**Testé en conditions réelles**, deux commandes distinctes :
```bash
python3 generate.py --dry-run --scenario breakdown \
  --thematique sciences_technologies --ligne-editoriale opposition \
  --article-longueur breve \
  --article-angle-specifique "MARQUEUR_ANGLE_TEST_CLI_12345" \
  --article-titre-suggere "MARQUEUR_TITRE_TEST_CLI_67890"

python3 generate.py --dry-run --scenario breakdown \
  --thematique sciences_technologies --ligne-editoriale opposition \
  --zone-slug afrique_de_louest_lagos_sahel
```

**Les 7 champs du bug §3.7 (2 août) sont tous confirmés appliqués
correctement**, vérifiés à la fois dans l'en-tête `print_header()` ET
dans le contenu réel du prompt (pas seulement l'affichage) :
- `--article-angle-specifique`/`--article-titre-suggere` : recopiés
  tels quels dans la consigne de rédaction
- `--article-longueur breve` : change réellement `**Longueur**` dans la
  consigne (`200 à 400 mots`) même quand la thématique testée a un
  format par défaut différent (`analyse` → 600-900 mots) — preuve que ce
  n'est pas juste cosmétique
- `--zone-slug afrique_de_louest_lagos_sahel` : édition locale
  correctement trouvée (plus de `[WARN] Pas d'édition locale...`),
  identité éditoriale et registre linguistique cohérents avec la zone,
  consigne finale correctement ancrée dessus

### Bug C — trouvé au passage : `longueur` des MÉTADONNÉES ignore l'override
Dans `prompt_builder.py`, `build_prompt()` recalculait `longueur` pour
le dict `metadata` retourné en fin de fonction **sans jamais regarder
`config`** :
```python
format_dom = thematique.get("format_dominant", "breve")
longueur   = FORMAT_LONGUEUR.get(format_dom, "300 à 500 mots")
```
alors que `build_journalistic_brief()` (qui construit la vraie consigne
lue par le LLM) fait bien les choses en priorisant l'override de
`config["article"]["longueur"]` s'il est présent. Résultat : dans le
`--dry-run`, la section MÉTADONNÉES affichait une longueur différente
de celle réellement envoyée au LLM.
**Portée réelle** : le prompt envoyé au LLM était toujours correct — ce
bug touchait uniquement le champ `metadata["longueur"]` retourné par
`build_prompt()`. Comme la longueur par défaut du GUI est `breve`
(configurable à chaque lancement, pas figée), ce décalage apparaît dès
que la thématique traitée a un `format_dominant` différent de `breve`
— fréquent, mais pas systématique. **Point à vérifier par David** : si
ce champ `metadata["longueur"]` est réutilisé en aval (frontmatter
d'article sauvegardé, stats, filtrage), des fiches déjà publiées
pourraient porter une longueur affichée incohérente avec leur contenu
réel — pas un problème de qualité du texte, juste une étiquette
potentiellement fausse.
**Correctif** : même logique de priorité que `build_journalistic_brief()`
dupliquée dans `build_prompt()`.
**Vérifié** : les deux sections (consigne + métadonnées) affichent
maintenant la même longueur dans le retest.

---

## 3. Point de reprise §7.3 — ajustement des plafonds par défaut

**Pas d'action prise, décision documentée plutôt qu'un oubli.**
Discussion avec David : le vault va grossir significativement (x2 à x5
selon lui), mais son budget/coût API n'est pas encore vérifié
précisément. Données objectives rassemblées cette session (tailles de
prompt sur 3 scénarios testés, 40k-52k caractères / ~10-13k tokens) —
insuffisantes pour ajuster des plafonds sans arbitraire, d'autant que le
design en 3 couches (détail plafonné / résumé plafonné / liste compacte
non plafonnée) absorbe déjà bien la croissance : seule la liste compacte
continue de grossir avec le vault, à coût quasi nul (noms seuls).
**Recommandation à David** : vérifier son usage/coût réel sur la
console Anthropic, revisiter ce point plus tard avec des chiffres
empiriques une fois le vault effectivement plus gros — pas de plafond
changé pour l'instant.

---

## 4. Audit de complétude snapshot/variables (nouveau chantier, initié par David)

Demande initiale de David : s'assurer que toutes les données
intéressantes calculées par `snapshot.py`/`loader.py` sont bien
utilisées par `prompt_builder.py`, et qu'on ne perd pas de contenu
narratif intéressant en route.

**Méthode** : comparaison champ par champ entre ce que chaque fonction
de `loader.py` extrait des fiches, ce que `snapshot.py` assemble dans le
dict final, et ce que `prompt_builder.py` lit réellement (grep
systématique de tous les accès `snapshot.get(...)`, `inst.get(...)`,
`ev.get(...)`, `zone.get(...)` dans le fichier). Fichiers de référence
utilisés : `snapshot.py`, une fiche variable (`climat_environnement_
global.md`), une fiche scénario (`fortress_world.md`), une fiche
géographie (`breakdown.md` = `geographie/breakdown.md`), et 6 fiches
instances de test (`coalition_des_souverainistes_numeriques_
policy_reform.md`, `coalition_arctique_des_blocs_continentaux_
fortress_world.md`, `coalition_des_villes_de_reconversion_
policy_reform.md`, `coalitions_des_deplaces_et_apatrides_
fortress_world.md`, `collectifs_academiques_independants_reference.md`,
`collectifs_de_biohackers_agro_communautaires_policy_reform.md`).

### 4 pertes significatives trouvées et corrigées

1. **`responsabilites` (instances)** — paragraphe distinct de
   `description_journalistique` (récit d'origine/statut, écrit "de
   l'extérieur") et `tensions_narratives` : décrit ce que l'entité FAIT
   concrètement (actions, leviers, méthodes, souvent avec des noms
   propres et détails opérationnels absents ailleurs). Jamais affiché.
2. **`signes_distinctifs` (instances)** — détails concrets/visuels/
   symboliques (slogans, symboles, pratiques caractéristiques) qui
   rendent l'entité reconnaissable et citable. Jamais affiché.
3. **`realisation` (événements custom)** — décrit comment l'événement
   s'est concrètement déroulé, distinct de `description` (mise en
   scène) et `consequences` (effets en aval, déjà affiché). Jamais
   affiché.
4. **Jalons génériques de portée "majeur"** — le système des `ruptures`
   (fiches variables, section "5. Ruptures") produit des jalons classés
   `majeur`/`structurant`/`local`. Seuls les `structurant` étaient
   affichés (`**Ruptures structurantes**`, 4 max) ; les `majeur`
   (pourtant la portée la plus significative du classement — 3+
   variables touchées, ou variable pilote + rupture "core") n'étaient
   **jamais montrés**. `snapshot["trajectory_majors"]`, calculé exprès
   pour ça, n'était lu nulle part dans `prompt_builder.py`.

**Correctifs appliqués** (`prompt_builder.py`) :
- `build_entities_context()` : ajout de `*Responsabilités*` et `*Signes
  distinctifs*`, affichés en entier (comme `description_journalistique`,
  pas tronqués), entre la description et les tensions narratives.
- `build_trajectory_context()`, section "Événements injectés" : ajout de
  `→ Déroulement : {realisation}` (tronqué à 80 caractères, même limite
  que `consequences`), entre la description et les conséquences.
- `build_trajectory_context()`, section trajectoire : nouvelle
  sous-section `**Ruptures majeures** (contexte de fond, portée large)`,
  affichée AVANT `**Ruptures structurantes**`, plafonnée à 3
  (`MAX_JALONS_RUPTURES_MAJEURES`), réutilise
  `snapshot["trajectory_majors"]` déjà calculé.

**Vérifié en conditions réelles** (`generate.py --dry-run --mode forcer
--forcer-type instance --forcer-slug
coalition_arctique_des_blocs_continentaux --forcer-scenarios
fortress_world`) : les 4 ajouts apparaissent tous correctement dans le
prompt généré. Taille du prompt sur ce test : 41 361 caractères — pas
d'explosion notable par rapport aux tests précédents (une seule entité
détaillée dans ce cas précis, mode Forcer-instance).

**⚠️ Non testé : impact taille en mode Semi-guidé à 6 entités
simultanées** (jusqu'à 6× `responsabilites` + 6× `signes_distinctifs`
en même temps) — c'est le vrai cas de charge maximale pour ces deux
ajouts, jamais mesuré. À faire en priorité à la prochaine session.

### Trouvailles additionnelles de l'audit, volontairement non traitées cette session

- **Champs mineurs jamais utilisés, sur demande explicite de David** :
  `impact_local`, `zone_geographique` (tags d'échelle locale/régionale/
  continentale/globale — distinct de `localisation.zone`),
  `type_relation_dominante`, `annee_debut`/`annee_fin`,
  `age_historique`, `generation`. Analyse de redondance faite : aucun
  n'est vraiment doublé par ce qui est déjà affiché, sauf `annee_debut`
  qui a un équivalent approximatif (littéraire, pas structuré) dans
  `description_journalistique`. **`type_relation_dominante` identifié
  comme le plus intéressant du lot** — sur les 6 fiches de test,
  `alliances`/`oppositions` sont systématiquement vides (`[]`) alors
  que `type_relation_dominante` vaut "conflit" ou "compétition" : la
  posture générale de l'entité est actuellement invisible dès que les
  listes de relations sont vides. Candidat pour une prochaine passe,
  avec `annee_debut`/`annee_fin`.
- **Incohérence documentation/code** : la docstring de
  `build_variables_context()` promet `forces_attractives`/
  `forces_repulsives` ("si disponibles") — jamais implémenté dans le
  code, et `loader.py` n'extrait même pas ces champs des fiches
  variables (section "4. Structure causale" du markdown, jamais
  parsée). Reliquat d'une version antérieure ou fonctionnalité jamais
  terminée — non tranché, non traité.
- **`constrained_variables`** (calculé au niveau snapshot depuis la
  fiche scénario) — jamais affiché dans le prompt. Non traité.
- **`coherence_ok`** et **`year`** — jugés normaux à rester non
  affichés (flag de QA interne pour les logs, valeur constante 2098
  déjà hardcodée dans les en-têtes). Pas des pertes réelles.
- **Risque structurel identifié, pas encore observé dans le vault** :
  une instance avec `injection.type == "custom"` (entité ajoutée
  spécifiquement, distincte d'un événement custom) affecte bien les
  variables (visible comme delta dans "Perturbations custom actives"),
  mais si elle n'est pas aussi sélectionnée parmi les 6
  `filtered_instances`, son nom n'apparaît que tronqué dans une ligne de
  delta — jamais décrite. Aucun exemple réel rencontré cette session
  (le vault semble n'avoir que des événements custom, pas d'instances
  custom pour l'instant) mais le trou existe déjà dans le code pour le
  jour où ça arrive.
- **Champ `type` des zones géographiques** (ex. `zone_sinistree`,
  distinct de `statut` qui lui est affiché) — jamais utilisé. Non
  traité, jugé mineur.
- **Bloc `simulation`** sur les fiches variables (volatility/
  predictability/uncertainty_level/tipping_point_risk/
  systemic_criticality/resilience/adaptability) — chargé par
  `loader.py` mais jamais lu par `prompt_builder.py`. Probablement pensé
  pour du monitoring interne plutôt que la narration ; non traité.

---

## 5. Fichiers livrés cette session

`loader.py` (bug A), `prompt_builder.py` (bugs B et C + les 4 ajouts de
l'audit — toutes les corrections cumulées dans une seule version finale).

Tous validés syntaxiquement (`ast.parse`). Testés en conditions réelles
via `--dry-run` collé dans le chat pour chaque correctif, avec
vérification explicite des comptages/contenus avant de considérer
chaque point comme clos.

---

## 6. Point de reprise suggéré pour la prochaine session

1. **Tester l'impact taille du prompt en mode Semi-guidé à 6 entités**
   avec les 4 ajouts de l'audit (§4) — jamais mesuré, c'est le cas de
   charge le plus élevé pour `responsabilites`/`signes_distinctifs`.
2. **Décider si `type_relation_dominante`/`annee_debut`/`annee_fin`
   valent le coup d'être ajoutés** (§4, trouvailles non traitées) —
   discussion à avoir avec David, pas encore tranché.
3. **Vérifier si `metadata["longueur"]` (bug C) est réutilisé en aval**
   (frontmatter d'articles sauvegardés, stats) — si oui, envisager un
   script de correction rétroactive des fiches déjà publiées avec une
   longueur affichée incohérente.
4. Ajustement des plafonds par défaut (§3) : revisiter avec des
   chiffres réels une fois le vault plus gros et le budget API vérifié
   par David — pas de plafond à changer avant ça.
5. Reste du backlog historique : rien d'identifié comme encore ouvert
   au-delà des chantiers volontairement différés (P14, P20, P21,
   renommage YAML §2.2) — voir `BACKLOG_CONSOLIDE_3_AOUT.md`.
