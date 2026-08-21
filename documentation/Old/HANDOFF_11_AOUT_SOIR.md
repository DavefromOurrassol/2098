# HANDOFF — session du 11 août 2026, soir (à uploader dans le nouveau chat)

*Deuxième session du 11 août, en continuité directe de `HANDOFF_11_AOUT.md`
(session du matin, clarté des descriptifs GUI + début de validation
navigateur). Session dense, entièrement pilotée par des tests réels de
David plutôt que par une checklist prévue à l'avance : 17 clarifications
supplémentaires de descriptifs, puis **6 bugs réels trouvés et corrigés**
en testant `create_entities`, `enrich_minimal` et un run `generate.py`
classique — le chantier "Test navigateur des entrées GUI modifiées",
ouvert en continu depuis fin juillet, est désormais **définitivement
clos**. 5 fichiers livrés au total.*

---

## 1. Suite de la clarté des descriptifs GUI (17 changements)

Revue systématique des 28 entrées de `scripts_config.json`, au-delà des
3 déjà traitées le matin. Deux passes :

**8 descriptifs principaux** — `enrich_minimal`, `zoning_topdown_test`,
`reparenter_sous_zones_orphelines`, `scan_geographie_complet`,
`audit_dates_instances`, `audit_etat_temporel_fin`,
`audit_longueur_articles`, `audit_type_relation_dominante`. Même
principe que le matin : retrait des notes de développeur datées
("8 août 2026 : ... confirmé par test réel"), des noms de fichiers
internes (`frontmatter`, `loader.py`), de l'historique de bugs
(diagnostics/itérations v1/v2/v3) qui n'apporte rien à l'utilisateur
final.

**9 changements au niveau des options** — dev-log daté retiré
(`--forcer-scenarios`, `--ancrage-temporel` sur `create_entities` ET
`generate_instances`), nom de fichier brut retiré (`--update` de
`generate_journaux`, `--slug` d'`undo_custom`), jargon isolé clarifié
("N1" → "premier niveau", "cache" → "résultat déjà calculé", "additif"
→ reformulé), et les 5 libellés de choix techniques bruts d'`undo_custom
--type` (`instance`, `event_instance`, `entite`, `event`, `signal`)
rendus lisibles.

**Vérifié par diff programmatique à chaque étape** : 14 entrées
touchées au total sur cette passe, aucune autre altérée.

---

## 2. Chantier "Test navigateur GUI" — clos

Les 3 dernières entrées non testées (`create_entities`, `enrich_minimal`,
`generate_instances`) ont toutes été couvertes :

- **`create_entities`** — cycle complet testé en conditions réelles :
  mode auto-suggest (génère des idées dans `queue.yaml`) → mode custom
  (injecte réellement dans le vault) → cycle post-injection automatique
  (`extract_localisation` → `review_localisation --auto-resolve` →
  `validate`). 2 bugs de code réels trouvés et corrigés en cours de
  route (détail §3 et §4).
- **`enrich_minimal`** — testé, résultat vide (0 fiche
  `officialise_minimal` restante dans le vault) — cohérent avec le
  chantier P8 clos depuis le 27 juin, comportement attendu plutôt qu'un
  échec.
- **`generate_instances`** — exercé comme dépendance directe du cycle
  post-injection du test `create_entities` (21 instances générées avec
  succès sur cette session), pas cliqué séparément via son propre bouton
  GUI, mais comportement confirmé fonctionnel en conditions réelles.

**Les 28 entrées du panneau sidebar sont désormais toutes
`gui_verified: true`.**

---

## 3. Bug — crash EOFError en création d'entités (mode auto-suggest/auto)

**Symptôme** : `EOFError: EOF when reading a line` en lançant
`create_entities` (mode auto-suggest) depuis le GUI, immédiatement après
l'affichage du mode — le script attendait une réponse clavier sur un
`input()` alors qu'aucun terminal interactif n'est connecté au
sous-processus Flask.

**Cause** : `run_auto_suggest_mode()` (`create_entities_and_instances.py`)
a deux `input()` non protégés (nombre d'idées, scénario ciblé) —
`run_auto_mode()` a le même défaut sur ses deux propres sous-questions
(nombre d'entités, catégorie imposée). Seul le choix de `--mode`
lui-même avait été protégé, le 11 juillet, pour ce même symptôme ;
jamais étendu à ces sous-questions.

**Correctif** : les 4 `input()` protégés par `sys.stdin.isatty()` — hors
terminal interactif (GUI/cron), retombe directement sur la valeur par
défaut déjà prévue dans le code (n=3, scénario=libre choix du LLM,
catégorie=libre) plutôt que de planter. Pour `n` dans `run_auto_mode()`,
pas de défaut sensé possible : arrêt propre avec message clair au lieu
d'un crash.

**Bug de type corrigé au passage** : le repli interactif de
`scenario_filter` produisait une chaîne simple, alors que tout le reste
du script (`step_auto_suggest_entities`, `args.scenario` en
`nargs="+"`) le traite comme une **liste** — un scénario tapé en CLI
pur aurait été itéré caractère par caractère (`"breakdown"` → `b`, `r`,
`e`...). Corrigé (`scenario_filter = [scenario_raw]`).

**Testé en conditions réelles** : mode auto-suggest relancé après
correctif, plus de crash, 5 idées générées avec succès et écrites dans
`queue.yaml`.

---

## 4. Bug — silence sur rejet `category`/`scenario_ref` invalide

**Symptôme** : en traitant la queue générée au §3, une entité ("Les
Veilleurs des Nappes Phréatiques") disparaissait du log sans aucun
message après son en-tête `=== Nom ===` — ni succès, ni erreur visible.

**Cause** : `process_custom_idea()` retournait directement sur un rejet
`category`/`scenario_ref` invalide, sans jamais imprimer — contrairement
à tous les autres cas d'échec de la fonction (archétype, instance) qui
affichent toujours leur motif. `needs_review.yaml` contenait bien la
raison (`category invalide : 'mouvement'` — le LLM auto-suggest a
halluciné une catégorie hors liste malgré la contrainte explicite du
prompt JSON), simplement jamais montrée à l'écran.

**Correctif** : `print(f"  ✗ Rejetée : {reason}")` ajouté sur les deux
cas de rejet précoce (`category`, `scenario_ref`).

**Pas un bug de garde-fou** : la validation elle-même a fonctionné
correctement (rien de mal formé n'a atteint le vault) ; seul
l'affichage console manquait.

---

## 5. Bug GUI — `queue.yaml` écrasé par un panneau caché

**Symptôme** : le run auto-suggest du §3 avait bien écrit 5 idées dans
`entites_custom/queue.yaml` (confirmé par le log de fin de run), mais le
fichier était retrouvé vide juste après.

**Cause** : `saveOpenConfigForms()` (`app.js`, ajoutée le 31 juillet pour
un autre bug — sauvegarder automatiquement un panneau YAML resté ouvert
avant de lancer un script) sauvegarde tout panneau `.yaml-form-panel`
présent dans `#form-body`, sans vérifier s'il est pertinent pour le mode
actuellement actif. Un panneau `config_fields_mode` (le formulaire du
mode Custom de `create_entities`, réservé à ce mode) reste dans le DOM
même quand un autre mode est actif — `updateModeOnlyVisibility()` ne
fait que le cacher (`display:none`), jamais un retrait du DOM. Ce
panneau, resté ouvert/vu plus tôt dans la session sans jamais avoir été
rempli, a donc été sauvegardé **vide** par-dessus le fichier qu'auto-
suggest venait d'écrire, au moment du clic Lancer suivant.

**Correctif** : `saveOpenConfigForms()` ignore désormais tout panneau
dont le mode déclaré (`dataset.modeOnly`) ne correspond pas à l'onglet
Mode actif au moment du clic — même logique que
`updateModeOnlyVisibility()`.

**Portée potentielle non vérifiée** : `inject_events` et
`inject_signals` ont le même mécanisme `config_fields_mode` — même
angle mort probable, jamais testé spécifiquement.

**Testé en conditions réelles** : queue.yaml retrouve bien son contenu
après le correctif ; le cycle complet auto-suggest → custom du §2 a pu
aller jusqu'au bout dessus.

---

## 6. Bug — placeholder cassé + réapparition d'une saisie ancienne (champ Angle)

**Symptôme signalé par David** : le champ "Angle spécifique" de
`generate.py` affichait "romuva la nouvelle religion en europe" dans le
récapitulatif d'un run, alors qu'il se souvenait avoir tapé ça il y a
plusieurs semaines et que le champ apparaissait vide à l'écran.

**Deux causes distinctes derrière le même symptôme**, découvertes en
deux temps :

**(1) Bug JS réel, mais pas la cause de la persistance** :
`renderOption()` fixait `inp.placeholder = opt.label` (le libellé du
champ, déjà affiché juste au-dessus) au lieu de `opt.placeholder` (le
texte d'exemple prévu, "ex : focus sur les réfugiés climatiques") — ce
dernier n'était donc jamais visible. Corrigé
(`inp.placeholder = opt.placeholder || opt.label`).
`autocomplete="off"` ajouté en prévention sur tous les champs texte
générés dynamiquement, bien qu'il se soit avéré que ce n'était pas la
cause du symptôme initial.

**(2) La vraie cause — reliquat `config.yaml`** : un champ texte vide
dans le formulaire GUI n'envoie tout simplement pas le flag CLI
correspondant (`collectArgs()`, comportement voulu : `if (val !== '')`).
Le mode Semi-guidé retombe alors sur `config.yaml` comme base — qui
gardait `angle_specifique: romuva la nouvelle religion en europe` depuis
un test d'il y a plusieurs semaines, jamais nettoyé depuis (rien ne
l'écrase tant que le champ GUI reste vide). Pas un bug de code, un
piège d'UX : un champ optionnel laissé vide ne veut pas dire "aucun
angle", ça veut dire "ne touche pas à ce qui est déjà dans
`config.yaml`".

**Nettoyage** : `config.yaml` ligne 44 vidée manuellement par David
(`sed -i '.bak' '44s/.*/  angle_specifique: /' config.yaml`, backup
automatique créé). Confirmé résolu par David au run suivant.

---

## 7. Bug — `--zone-slug` proposait des sous-zones sans journal

**Symptôme** : un run `generate.py` (Semi-guidé, zone choisie au hasard
dans le menu) a échoué avant génération : `zone_slug invalide :
'archives_neutres_geneve' n'existe pas dans journaux.yaml pour
breakdown/pro_pouvoir`.

**Diagnostic** : `archives_neutres_geneve` existe bien dans
`geographie/breakdown.md`, mais en tant que **sous-zone niveau 2**
(`parent: geneve_bunker_institutions`). `journaux.yaml` n'a jamais
qu'une entrée par zone **niveau 1** (structure confirmée :
`data[scenario][ligne]['zones']`, dict indexé par slug, 36 entrées pour
`breakdown/pro_pouvoir`, toutes niveau 1). Le menu `--zone-slug` (type
`zones_hier`, fonction `_scan_zone_slugs_hier()`) liste toutes les zones
tous niveaux confondus, sans jamais filtrer sur la présence réelle d'un
journal — le garde-fou `validate_config_semi_guide()` (11 juillet) ne se
déclenche qu'*après* la sélection, au lancement, plutôt que d'empêcher
le choix en amont.

**Contrainte du correctif** : le type `zones_hier` est **partagé** avec
`zone_hint` (`create_entities`/`inject_events`), qui a légitimement
besoin de la hiérarchie complète pour ancrer une entité sur une
sous-zone précise — impossible de simplement restreindre la source
partagée aux zones niveau 1 sans casser ces usages.

**Correctif** : nouveau type `zones_hier_journal`, spécifique à
`--zone-slug` de `generate.py` :
- Nouvelle fonction `_zones_avec_journal(pipeline_dir, scenario)`
  (`app.py`) — lit `journaux.yaml`, retourne l'ensemble des slugs
  présents dans `zones` pour au moins une des deux lignes éditoriales
  (union `pro_pouvoir`/`opposition`). Filtre sur le **contenu réel** de
  `journaux.yaml` plutôt que sur `niveau == 1`, pour rester correct même
  si la convention de niveaux changeait un jour.
- Nouvelle branche dans `/api/slugs` (`zones_hier_journal`) : réutilise
  `_scan_zone_slugs_hier()` pour la hiérarchie complète, puis filtre via
  `_zones_avec_journal()`.
- `scripts_config.json` : `--zone-slug` de `generate.py` bascule sur ce
  nouveau type, description mise à jour ("Ne liste que les zones ayant
  un journal — les sous-zones plus fines ne sont pas sélectionnables
  ici.").
- **`zones_hier` (l'ancien type) reste totalement inchangé**, toujours
  utilisé tel quel par `zone_hint`.

**Vérifié avant livraison** (test unitaire local, hors Flask) :
`geneve_bunker_institutions` passe le filtre, `archives_neutres_geneve`
non — comportement exact attendu.

**Non re-testé en conditions réelles après correctif** — David a
confirmé "ça marche" après application, mais aucun nouveau run
`generate.py` avec sélection de zone n'a été rejoué dans cette session
pour vérifier de bout en bout (le point Partie 1 #2 du backlog, retry
signature, reste donc non tranché — voir ce fichier).

---

## 8. Points de vigilance notés, pas corrigés

**Fichiers parasites dans `generator/` (incident du 5 août)** — ~80
fichiers vides, sans extension, à la racine de `generator/`, tous
horodatés à la même minute (5 août 19:09), certains avec des fragments
de noms cassés et `[dry-run]` incrusté dedans. Diagnostic : aucune
fonction du pipeline n'écrit dans `generator/` ni ne produit ce genre de
nom — hypothèse retenue, un copier-coller de sortie console `--dry-run`
collé par erreur après une commande `touch` dans le terminal, un jour
donné. Incident isolé (rien après le 5 août). Commande de nettoyage
fournie à David, **pas confirmée exécutée** — à vérifier à la prochaine
session.

**Troncatures JSON occasionnelles côté Mistral (génération d'instances)**
— 2 occurrences dans la session (`reseau_..._fortress_world`,
`institut_des_seuils_demographiques_breakdown`), le modèle s'arrête en
plein milieu du JSON. Vérifié : **pas** un problème de plafond de tokens
(`INSTANCE_MAX_TOKENS = 4000`, sorties observées à ~1200-1300 tokens
seulement — le détecteur de troncature déjà présent dans
`call_claude_json()` a d'ailleurs correctement écarté cette hypothèse).
Aléa API, même famille que le timeout 503 vu le même jour sur
`extract_localisation.py`. Le mécanisme de résilience existant (le
script continue avec l'élément suivant) gère déjà correctement ce cas —
pas de correctif codé, juste un point à surveiller si la fréquence
augmente sur un futur batch de volume.

**`needs_review.yaml` — une idée en attente** — "Les Veilleurs des
Nappes Phréatiques" (`category: mouvement`, invalide) reste dans
`needs_review.yaml` suite au §4. Le garde-fou a fonctionné comme prévu ;
à corriger manuellement (changer `category` pour une valeur valide) si
David souhaite un jour créer cette entité.

---

## 9. Fichiers livrés cette session

- **`create_entities_and_instances.py`** — 2 correctifs cumulés (§3, §4).
- **`app.js`** — 2 correctifs cumulés (§5, §6.1).
- **`app.py`** — 1 correctif (§7 : `_zones_avec_journal()` +
  branche `zones_hier_journal`).
- **`scripts_config.json`** — cumule : 17 clarifications de descriptifs
  (§1), `create_entities`/`enrich_minimal` passées à `gui_verified: true`
  (§2), `--zone-slug` basculé sur `zones_hier_journal` (§7). Toutes les
  modifications vérifiées par diff programmatique à chaque étape,
  systématiquement.

**Chez David, à faire au prochain lancement** :
1. Remplacer les 4 fichiers dans `generator/`/`gui/`.
2. **Redémarrer Flask** (obligatoire — `app.py` et `scripts_config.json`
   ont changé ; `app.js` seul n'aurait nécessité qu'un rechargement page).
3. Nettoyer les fichiers parasites de `generator/` (§8, commande fournie,
   pas encore confirmée exécutée).

---

## 10. Point de reprise suggéré pour la prochaine session

Backlog Partie 1, dans l'ordre — voir `BACKLOG_MASTER_9_AOUT.md`,
entièrement à jour :

1. Validation à plus grande échelle du retry sur la longueur (10 août) —
   pas urgent.
2. Validation réelle du fix signature itération 2 (10 août) — **toujours
   non tranché**, le test de génération d'article de cette session a
   échoué avant génération (zone invalide, §7) sans avoir permis de
   statuer.
3. Diagnostic `annee_debut`/`ancrage_reel` sur les événements (8 août) —
   jamais exploré.
4. Dimension temporelle pour la génération automatique (8 août) — non
   codée.
5-11. Points 🟢/⚪ mineurs, dont les 2 nouveaux de cette session (fichiers
   parasites `generator/`, troncatures JSON Mistral).

**Chantier "Test navigateur GUI" retiré de la Partie 1** — définitivement
clos, déplacé en Partie 4 (référence historique).

**Rappel de méthode, toujours valable** : à chaque modification de
`scripts_config.json`, vérifier par diff programmatique (pas juste
visuel) qu'aucune entrée en dehors de celle(s) visée(s) n'a été altérée.
Fait systématiquement cette session, sur les 4 modifications successives
du fichier — aucune régression détectée.
