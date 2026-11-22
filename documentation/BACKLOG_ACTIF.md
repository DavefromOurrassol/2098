# Backlog actif — Ourrassol 2098

*Ce qui reste ouvert, et seulement cela. Mis à jour le 21 novembre 2026 au soir (wild cards :
restes U4d5, U4d6, U4e faits, Shackleton supprimée (U4g) ; **Passe lente résolue** : l'alias
`mistral-large-latest` était passé à Large 4, Large 3 fixé ; **modifier une hypothèse**, U4h,
U4h2). Réorganisé le 31 octobre 2026 en trois
parties : **A. Bugs et vérifications**, **B. Développement (nouvelles
fonctionnalités)**, **C. Enrichissement de la base**. Règle actée le 31 oct :
l'outil doit avoir toutes ses fonctionnalités et aucun bug connu (partie A vide)
avant d'enrichir la base en volume (partie C).*

*Les chantiers gardent leur numéro (S20, S24, #5…) : un même chantier peut avoir
des points dans plusieurs parties, chacun est marqué de son numéro. Les points
clos sont dans `BACKLOG_ARCHIVE.md` (à uploader seulement pour vérifier si un
point a déjà été traité). Mode d'emploi : `USER_MANUAL_COMPLET.md` ; dernier état
de session : `HANDOFF_21_NOVEMBRE.md`.*

Légende : 🔴 à faire · 🟡 en cours · 👁 en surveillance (pas de correctif
préventif, agir si le cas revient) · ⚪ idée sans calendrier.

---

# PARTIE A — BUGS ET VÉRIFICATIONS

*Tous les bugs de code connus sont corrigés (31 oct et 1er nov : voir les
handoffs). Reste à éprouver en réel ce qui n'a tourné que sur copie ou avec une IA
simulée, et à surveiller des défauts qui dépendent de l'IA.*

## 🟡 A1. Fonctions à éprouver en réel (S30, S20)

**Tests réels de S30** (détail dans `BACKLOG_ARCHIVE.md`) : le 31 oct sur
`test-s30` (`reunification_ecosse_2070`, `occupation_bresil_2029` : étapes ① à ⑤,
Sauter / Inclure, Carte, Remplacer / Ignorer) ; le 1er nov sur `test-s30b`
(`chute_holdfast_2072` : **fiches des entités disparues** de bout en bout, contrôle
des faits imposés vu en réel, « 6 contrôlé(s), 0 non respecté(s) »). Dix défauts
trouvés et corrigés le jour même.

Reste à voir en réel :
- **S30 — relocalisation de l'événement** (31 oct, testée sur vault factice) : au
  premier cas réel avec `nouvelle_zone` ou zone vidée, vérifier la ligne « →
  événement … relocalisé » de l'aperçu ④, puis `localisation.zone` de la fiche.
- **S30 — citations de la passe** (31 oct) : à la prochaine simulation avec des
  obligatoires, les textes « citation inexacte, remplacée par la phrase de la fiche »
  doivent passer à l'étape ⑤ sans « introuvable mot pour mot ». (Holdfast : aucune
  phrase à corriger, rien à vérifier ; le remplacement a bien eu lieu à ①.)
- **S30 — correctifs du 1er nov testés en CLI ou sur copie** : au prochain parcours
  réel,
  - ③ bouton « Liste de l'étape ④ » avec les champs remplis : ✓ / –, « numéro(s)
    absent(s) », « Retiré de l'entrée à l'injection » (CLI vérifiée sur
    `pacte_tabriz_2058` ; GUI non vu, l'étape ③ n'étant ouverte qu'après adoption) ;
  - rapport ① : ligne « Propositions sans objet, écartées » distincte de « mal
    formées » ; « Fiches à relire » sans mots génériques (« Réseau »…) ;
  - aperçu ④ : bloc « Réciprocité » trié par relation (une relation ancienne d'une
    fiche touchée en « HORS hypothèse ») ;
  - aperçu « au passé » : ligne « [contexte] hypothèse `<id>` : description et N
    fait(s) imposé(s) transmis » (vérifiée sur Holdfast en CLI, pas encore lancée par
    l'étape ④ elle-même).
- **B9 — Articles → « et si ? »** (éprouvé le 11 nov sur cinq événements d'un même article :
  un « propre », un « propre » à date déduite, trois passés — 2039, 2042, 2044). Vus en
  réel : citation imposée propre et respectée, badges « déjà connu », filtre U3p / U3r /
  U3x, passage de l'article transmis (U3s), contrôle des citations sans faux positif.
  Reste à voir : a) le chemin **signal** depuis un article (non rejoué) ; b) une
  **réécriture** déclenchée par un fait `[ARTICLE]` omis (U3w : aucune omission depuis le
  patch) ; c) les alertes U3w (nom du scénario) et U3y (anachronisme) en réel (jamais
  déclenchées depuis les patchs) ; d) un article d'un **autre** scénario que
  new_sustainability, et un article dont l'en-tête a une clé `titre` ; e) **entité** :
  « comme entité » (Articles) puis ajout, adoption, injection ; entité de la Lecture IA
  jusqu'à l'injection ; f) les boutons de l'étape ⑤ et « Appliquer » en double-clic.
- **B9 — Wild cards** (U4a → U4h, 15 et 21 nov) : vus en réel le bouton ⚡ (3 idées, pas de
  lot), la case ⚡ de ✨ Proposer, la reprise des scénarios de l'idée (U4d5, Zéro-R), les
  contrôles (quota, fenêtre, forces), le contrôle des règles de lore (0 contredite), la Passe
  exhaustive forcée et les forces par scénario dans le rapport (Shackleton). Reste à voir :
  a) **adoption puis injection** d'une wild card (forces 25-35 acceptées par
  `inject_custom_events.py`, `wild_card: true` dans la fiche), puis `validate.py` (aucun plafond
  à 25 trouvé par recherche, à confirmer) ; b) une règle de lore **déclarée contredite**
  (blocage) ; c) le refus d'adoption sans Passe exhaustive ; d) **U4e** : la règle « fait
  établi » à l'étape ⑤ et le badge ⚡ (testés sur copie seulement) ; e) U4d6 (contrainte « En
  2058. » retirée) au prochain tirage qui la produit. **Décision du 21 nov** : injecter une wild
  card change le lore pour de bon ; a) à d) se testent donc sur une **branche jetable**
  (`git checkout -b test-u4`, parcours complet avec le Zéro-R, puis `git checkout main` et
  `git branch -D test-u4`), comme `test-s30` / `test-s30b`.
- **B9 — Modifier une hypothèse** (U4h, 21 nov) : vu en réel (refus d'une hypothèse adoptée,
  remplacement puis retour). Reste à voir : le refus d'une hypothèse **injectée**, et une
  modification suivie d'une resimulation et d'une adoption (l'adoption doit refuser tant que
  la simulation est périmée).
- **S20** : `/api/yaml/append` garde l'en-tête de `queue.yaml` (correctif du 30 oct,
  testé sur copie) → vérifier au prochain ajout depuis le GUI (ex. entrée préparée
  dans 🔭), puis retirer ce point. (« Adopter » du simulateur garde bien l'en-tête :
  constaté le 31 oct, `queue.yaml` revenu identique après adoption puis injection.)
- **S20** : reprise d'injection partielle (`idee_a_remettre_en_queue`) et arrêt
  propre sur interruption (31 oct) — testés avec une IA simulée seulement ; à
  observer au premier cas réel.
- **#3 P20** : consigne « une personne ou entité nommée doit être représentée » de
  l'`image_prompt`, à juger quand le service d'images sera branché (B2).

## 👁 A2. Défauts dépendant de l'IA — en surveillance

- **S25 Kharg-9 surreprésenté** : cooldown durci le 6 oct (`loader.py`,
  `COOLDOWN_STREAK` 2, `COOLDOWN_DURATION` 3), exclu en eco_communalism. Mesurer
  l'effet sur les articles postérieurs au 6 oct ; si les titres se répètent
  (« casino des données », « défie Genève-Nexus »), retoucher la
  `description_journalistique` de l'instance.
- **S1 / P25** : fiabilité de `mistral-small` sur choix contraint (relancer un
  article avec `LLM_PROVIDER=mistral LLM_MODEL=mistral-small-latest`, comparer à
  `mistral-large`) ; signature journaliste ~25-33 % d'échec en août. Observer avant
  de corriger.
- **S2 (bug #27)** : plausibilité logistique inter-zones (pirogue Amazonie ← Congo,
  juillet). Mesurer la récurrence sur des articles avant tout correctif.
- **S4** : JSON d'instances illisible (Mistral). `extraire_json()` est tolérant ; au
  prochain échec, lire `gui/logs/llm_json_echec_*.txt` avant de conclure à une
  troncature ; retry dédié seulement si fréquent.
- **S9** : confusion slug de zone / slug d'instance (un cas le 4 août). Si cela
  revient : lister dans le prompt les slugs de zones à ne pas utiliser.
- **S8** : `--min-shingle` fixé à 6 mots dans `detect_registre_leakage()` ; en
  faire une option seulement si un faux positif ou négatif apparaît.
- **S24 trajectoires « émergent » par défaut** : la lecture IA propose souvent
  « émergent → dominant » d'un coup (signalé ⚠ à l'étape ④). « émergent →
  déclinant » (échec précoce) reste non signalé, décision du 31 oct.
- **S30 rédaction des hypothèses** : un fait imposé doit rester vrai dans le lore du
  scénario. « réintègre le Royaume-Uni » était ambigu en reference (le Royaume-Uni
  n'y est plus un acteur, l'UOC couvre la zone) : l'IA a écrit l'UOC deux fois. Si
  le contrôle des faits (A1) alerte souvent, revoir d'abord la rédaction du fait.
- **S30 forces et saturation** : force 20 sur `geopolitique_conflits`
  (`occupation_bresil_2029`) → +0,3 en 2098 (pic +3,9 en 2043), variable déjà à 88,7
  sans l'hypothèse ; voir B7 « Saturation près des bornes ».
- **S24 bloc `===METADONNEES_PUBLICATION===`** : correctif préventif du 31 oct
  (bloc sans fin, en double ou tronqué). Si un bloc réapparaît dans un article,
  lire la sortie console de la génération (avertissements `[api] [WARN]`).
- **S14 couleur fantôme** Royaume-Uni / Angleterre / Écosse / Galles (un polygone
  pour quatre noms) : revérifier si l'un d'eux change de zone.
- **S30 contrôle des faits imposés** (vu en réel le 1er nov, 6 faits, 0 alerte) :
  surveiller les faux positifs (fait non mentionné jugé « remplacé »).
- **S30 `fiche_au_passe.py`** : la consigne « une phrase au plus par texte » pour la
  fin n'est pas toujours tenue (Holdfast : `tensions_narratives` 721 → 938 car., une
  phrase ajoutée à trois points sur quatre, sans fait inventé). Relire l'aperçu ;
  durcir la consigne si cela revient.
- **B9 injection d'un événement tiré d'un article** : depuis U3aa → U3ac (14 nov), la
  fiche **reprend la description de l'hypothèse** (tirée de l'article) au lieu d'être
  inventée par l'IA ; `consequences` et `note_coherence` sont fixes, un contrôle ⚠ signale
  les noms propres et sigles absents de l'article. David **ne relit pas** chaque fiche : à
  confirmer en réel sur un prochain événement d'article ; restent les points de B9 (« source
  mince, suite »).
- **B9 localisation des fiches injectées** : `extract_localisation.py` (mistral-small) a
  placé les arrestations des Grottes (Genève) en `afrique_continentale` / « quartier de
  la Jonction » à cause de « communautés sahéliennes » dans la description (corrigé U3u).
  Les trois autres fiches du 11 nov étaient bien placées. Si cela revient : passer le
  `lieu` / la zone de l'article à l'extraction, ou contrôler la zone contre celle de
  l'article.
- **B9 extracteur, variabilité** : d'une détection à l'autre, l'IA tronque parfois une
  citation (« [...] ») ou change un mot (« le quai » pour « au quai ») : l'événement est
  alors écarté ou marqué « citation introuvable ». Relancer la détection suffit en
  général.
- **B9 wild cards proposées par ⚡** (15 nov) : premier tirage physiquement impossible (corrigé
  U4d2), puis catastrophes régionales (VEI 6 : écarté, U4d3), puis toutes en « tous » (U4d4).
  Le 4ᵉ tirage était bon (Shackleton, supraconducteur, stérilité). Surveiller : mécanismes
  « quasi impossibles » admis par l'IA elle-même, acteurs propres à un scénario nommés dans
  une idée valable pour plusieurs mondes.
- **S30 contre-lecture de la Passe trop indulgente** (21 nov, mesure Large 3 sur
  `fusion_commerciale_2038`, reference) : 2 obligatoires confirmés sur 18, tous deux discutables —
  la Crise des Détroits Indo-Arabes (juin 2038) jugée caduque alors que la fusion met 15 ans à se
  diffuser (piège « chronologie »), la Gouvernance-IA de l'Archipel Pétrolier contredite par un
  fait inventé (« pénuries résolues dès 2050 », piège « invention »). Les possibles sont
  nombreux (176 fiches). Observer à la prochaine Passe réelle (Large 3) avant de durcir
  `CONSIGNE_CONTRE`.
- **B8 / modèles : alias qui changent seuls** (21 nov) : `mistral-large-latest` est passé à Large
  4 sans décision (vers le 14 nov, date du correctif « réflexion » de `llm_client.py`). Les trois
  tiers « large » sont fixés sur `mistral-large-2512`. `mistral-small-latest` (tier `volume`)
  reste un alias : vérifier de temps en temps vers quoi il pointe (`c.models.list()`, gratuit).
  Les articles générés entre le 14 et le 21 nov ont pu sortir de Large 4 (à relire seulement si
  l'un d'eux détonne).
- **Signal `remboursement_chatbots_therapeutes_2040`** : statut « adopté, absent de la queue »
  (adopté, jamais injecté, entrée absente de `signaux_custom/queue.yaml`). À trancher :
  l'injecter (« Annuler la décision », re-adopter, ③) ou le rejeter.
- **B9 wild card et saturation** : `geopolitique_conflits` en fortress_world est déjà à 99,7
  sans l'hypothèse ; une force 35 n'y ajoute que +0,3 (Shackleton). Limite des bornes, pas un
  bug (U4b abandonné : une rupture n'est pas freinée par le plafond de 15 points).
- **B9 `frontieres_du_systeme`** : la lecture IA et la Passe la lisent comme la fermeture des
  frontières entre blocs ; une polarité -1 « ouvre » fortress_world (toutes les administrations
  frontalières en déclin, Shackleton). Vérifier le sens de cette variable avant de l'utiliser
  dans une wild card.
- **S30 lecture IA, propositions lointaines** : sur Holdfast, trajectoire du fonds
  groenlandais et opposition Atlas des Marges ↔ ARPS sans lien avec l'hypothèse
  (sautées à la main). Sauter suffit ; à surveiller si cela devient fréquent.

## ⚪ A3. Écarts connus, laissés en l'état (décision du 31 oct)

- **S24 slugs** : `export_revues.slugify()` (URL du site) supprime ø au lieu de le
  translittérer ; sans conséquence (le site se reconstruit), gardé.
- **S24 slugs** : un journaliste dont le nom a été inventé par l'IA (signature hors
  `journaux.yaml`) garde l'ancien `journaliste_slug` (ø → `_`) dans ses articles
  antérieurs au 31 oct.
- **S24** : `audit_slugs_s24.py` signale `tromsoe_aln` (geographie/reference) : faux
  positif, ce slug est correct.
- **S30** : `test-s30` (branche locale, deux commits jetables) et `test-s30b`
  (commit jetable `3a79654` : `chute_holdfast_2072`, Holdfast disparu, au passé)
  gardées pour consultation ; les supprimer quand plus utiles :
  `git branch -D test-s30 test-s30b`. L'hypothèse `chute_holdfast_2072` n'existe
  que sur `test-s30b`.
- **S30** : le slug `amazonie_consortium_viva_reference` porte le nom « BioPatente
  Amazonas », distinct de `consortium_amazonia_viva_reference` (Consortium Amazônia
  Viva) : piège slug ≠ nom (voir C4), pas un doublon.

---

# PARTIE B — DÉVELOPPEMENT : NOUVELLES FONCTIONNALITÉS

## 🔴 B1. Site des revues — suites (#5)

En ligne : https://ourrassol.pages.dev (kiosque + 12 revues). Publier :
`python3 generator/chapos_revues.py` (si nouveaux articles) puis
`bash generator/publier_site.sh`. Mode d'emploi : manuel §2octies.

Dans l'ordre envisagé :
1. **12 identités visuelles** : un bloc `style` par revue dans `revues.yaml`
   (polices, couleurs, variantes de mise en page) lu par `export_revues.py` ; une
   maquette par revue à valider, comme celle du *Courrier des Continents*. Les
   champs `style_visuel` sont déjà posés (ex. `samizdat`, `transcription_radio`).
2. **Photos** : voir B2.
3. **Audio** (*Radio Frontières*, journaux oraux `type_diffusion: oral`) : stockage
   Cloudflare R2 envisagé ; origine des extraits (synthèse vocale ou
   enregistrements) à décider.
4. **Version multilingue** : libellés fixes par langue, pages sous
   `site/<langue>/` ; attention au plafond Cloudflare Pages (20 000 fichiers).
5. Optionnel : titre réécrit par la revue et encadré « Contexte » (même appel que
   le chapô) ; protection d'accès Cloudflare pendant les tests ; bouton « Publier »
   dans le GUI ; références entre articles.

## 🔴 B2. Images des articles — service à brancher (#3 P20)

Tout est codé (21 août) sauf le service externe : Anthropic n'a pas d'API image,
un service tiers est à choisir (OpenAI, Stability, Google Imagen…). Point
d'intégration prêt : `_generate_image_via_api()` dans `generate_images.py`
(signature stable).
- Champs de publication (`chapo`, `image_prompt`, `tags`, `a_une_photo`,
  `image_credit`, `journaliste_slug`, `date_evenement`, `zone_principale`,
  `entites_citees`…) écrits à la génération ; voir manuel §2.
- En attendant, placeholder neutre ; un placeholder « IA non branchée » est retraité
  automatiquement au run suivant. Le site affiche un emplacement vide pour les
  articles `a_une_photo: true` : au branchement, passer le fichier et `image_alt`
  dans `export_revues.py`.
- Au branchement : régénérer l'image de l'article fortress_world du 23 août
  (`20260823_080632_…_18octobre2098.md`), `image_prompt` corrigé (Halifax-Haute au
  lieu de Bruxelles-Forteresse) ; tester la consigne de personne nommée (A1).

## ⚪ B3. Outils externes à greffer (S28)

*Origine : comparaison d'Ourrassol avec la Red Team Défense (ministère des
Armées, lancée en 2019-2020 ; arrêtée en 2023 après trois saisons, à vérifier
avant de s'y référer). Même matière (ruptures technologiques, géopolitiques,
sociales), intention différente : la Red Team provoque des décideurs avec des
scénarios ponctuels 2030-2060 imaginés par des auteurs de SF, BD et scénaristes,
critiqués par des militaires et des scientifiques ; Ourrassol construit six mondes
parallèles cohérents sur 2025-2098 et les fait vivre par une presse fictive, avec
une veille outillée et des contrôles de cohérence.*

*Ce qu'Ourrassol fait mieux : la **propagation** (`trace_injection.py`), la
**pluralité des regards** (pouvoir et opposition, S26), la **traçabilité**. Son
point faible : la **surprise** (le moteur ramène vers la référence et sature près
des bornes, l'audit corrige ce qui détonne, l'IA recycle ce qu'elle a lu, David
imagine seul). D'où les pistes ci-dessous, et les wild cards et la passe « équipe
rouge » de B4.*

**S28.1 MICMAC : clos le 25 oct.** Suites de développement :
- **`coupling_intensity`** : usage « prompt des articles » **clos** (B3.1, voir archive). Reste l'usage « moteur » : moduler la matrice par scénario → avec S28.2.
- La criticité (`systemic_criticality`) pèse lourd dans le classement (×0,7 à ×1,6
  sur tous les liens sortants) : à rediscuter si un classement surprend.
- `variable_type` des fiches (moteur / relais / réactive) gardé comme intention de
  conception, distinct du classement MICMAC (diverge sur 7 variables) ; lu par
  `generate_entities.py`.
- Atelier de la matrice (page privée) :
  https://claude.ai/artifact/WgAxTF4arr9aRB5w7F9vxf — réutilisable.

Ordre conseillé : 2, puis 3.
2. **CIB (Cross-Impact Balance)**, ScenarioWizard (CIB-Lab de Stuttgart, version
   récente sur Zenodo ; licence et formats à vérifier). On note comment l'état de
   chaque variable favorise ou freine l'état des autres ; le logiciel liste les
   combinaisons cohérentes. Apport : vérifier que les 6 scénarios sont stables et
   faire apparaître des configurations non imaginées (réponse au manque de
   surprise). Coût : ≈ 1 200 jugements (3 états par variable). Point de départ :
   `coupling_intensity`. Session dédiée.
3. **Base SSP de l'IIASA** : population, PIB, urbanisation, énergie, émissions par
   grande région jusqu'en 2100. Correspondances : fortress_world ≈ SSP3,
   new_sustainability ≈ SSP1, policy_reform ≈ SSP2 (les autres à établir). Le plus
   utile pour la crédibilité des articles.
4. **API Metaculus** (2026-2035 ; accès à vérifier) : nourrir
   `etat_du_monde_reel.md` avec ce que les prévisionnistes jugent probable.
5. **GDELT** (événements de presse, tendances par pays / thème) et **OpenAlex**
   (publications scientifiques ; un sujet qui décolle = signal faible
   technologique) en complément du RSS.
En marge : *Global Trends 2040* comme grille de comparaison.

## ⚪ B4. Simulateur « et si ? » — options (S30, ex-S27.5)

Le simulateur est terminé (manuel §3quinquies) ; ses tests réels sont en A1.
- Homonymes (Santa Cruz, Sucre, Perth, Medina) ; synthèse haut niveau des
  hypothèses ; récit IA de `trace_injection.py` (repli sur le modèle).
- **Wild cards** : cadrées et codées le 15 nov, restes faits le 21 nov (→ B9, U4a → U4h) ; derniers points en B9.
- **Brouillon de règle de lore (étape ⑤)** : termes multiples **faits** (B4, 2-7 nov) ; à observer à la première hypothèse réelle qui fait disparaître une entité.
- **Passe « équipe rouge »** : faire attaquer les hypothèses d'un scénario plutôt
  qu'en vérifier la cohérence (ex. « qu'est-ce qui ferait tomber Ergo-Wian en dix
  ans ? »), par l'IA ou des lecteurs aux profils variés. Inspiration : la série
  *Ces guerres qui nous attendent* (travaux de la Red Team Défense).

## 🟡 B9. Unification — « et si ? » porte unique (U2-U4, 2-21 nov)

*Principe : tout élément (événement, signal, entité) naît comme **hypothèse** dans
`et_si/hypotheses.yaml`, puis ①simuler → ②décider → ③injecter → ④appliquer →
⑤à la main (un **signal** s'arrête à ③ ; une **entité** : ① vérifier → ② décider →
③ injecter, sans simulation chiffrée). Les flux de maintenance qui écrivent la file des
entités (`enrich_minimal.py`, `extract_phantom_slugs.py`, `requeue_needs_review.py`,
`create_entity.py`) restent hors du dispositif.*

**Les quatre entrées, toutes par « et si ? »** (état du 14 nov) :

| Entrée | Types | Remarque |
|---|---|---|
| ✨ Nouvelle hypothèse (idée libre, 💡 suggestions, lot, ⚡ wild cards) | événement (dont wild card), signal, entité | suggestions : événements et entités ; ⚡ : 3 wild cards, jamais en lot |
| 🔭 Veille signaux faibles | signal, événement | source des signaux (pas de suggestions de signaux) |
| Onglet Articles | événement (détecté dans l'article), signal, entité (nom saisi) | date verrouillée, citation imposée |
| Étape ⑤ « Lecture IA » : nouvelles entités | entité | plus de file `entites_custom/queue.yaml` |

**Fait** (détails dans l'archive et les handoffs). Jusqu'au 11 nov : type `signal`
(U2a-U2g), lieu + contraintes (U2h), veille → « et si ? » (U3a), Articles → « et si ? »
(U3b-U3d), dates en année + mois jusqu'à 2098.12 (U3e), détection des événements du texte
complet (U3f), citation exacte imposée (U3i, U3k), doublons bloqués (U3o), filtre mécanique
de l'extracteur (U3p, U3r, U3x), passage de l'article transmis à l'injection (U3s, U3t, U3w,
U3y). **14 nov** (U3aa → U3bf) :
- **source mince → invention** : la fiche d'un événement d'article reprend la description
  de l'hypothèse au lieu d'être inventée (U3aa), titres recadrés (U3ab), contrôle du fait
  `[ARTICLE]` retiré (U3ac) ; dates 2098.xx dans la Passe exhaustive et la Lecture IA (U3ad) ;
- **panneau** : titres et messages (U3ae), signal en 3 étapes avec options payantes grisées
  (U3af), étape ⑤ expliquée (U3ag), description de l'hypothèse sous la liste (U3at-U3av) ;
- **entités** : type `entite` en 4 patchs + doublons + `--idea` (U3ah-U3ao), date de
  naissance respectée (`annee_debut`, U3aw), suppression des hypothèses d'entité non injectées
  (U3ax), localisation relancée après l'injection (U3ba), 📦 adopter + injecter plusieurs
  entités (U3bb, U3bc), Lecture IA et Articles vers les hypothèses (U3be) ;
- **suggestions** à partir des lacunes (événements, entités) avec année, traitées en lot
  (U3aq, U3ar, U3as, U3ay) ;
- **étape 5** : accès directs fermés (U3ai), menu regroupé (U3ap), routes mortes et
  commentaire périmé retirés (U3bf) ; **confirmations en double-clic** (U3as, U3az, U3bf).
Chemin signal éprouvé en réel (veille, 7 nov) ; chemin Articles → événement éprouvé le 11 nov ;
entités éprouvées le 14 nov (3 entités injectées, 2 par le lot).

**15 nov — wild cards (étape 3)**, cadrage avec David puis U4a → U4f :
- **Définition** : un **événement** marqué `wild_card: true` (pas un 4ᵉ type), mode **rupture**
  obligatoire, qui change le monde ENTIER pour de bon sur plusieurs domaines (souvent une
  découverte ou une percée ; pas une catastrophe régionale qui s'estompe). Il peut contredire les
  fiches et les tendances (corrections à appliquer), **jamais les règles de lore** (erreur
  bloquante). Un ou plusieurs scénarios.
- **Plafonds** : 3 au plus par scénario, 10 ans d'écart dans un même scénario (rejetées
  exclues), date 2030-2090, 3 à 6 impacts ; force 25-35 dans au moins un scénario, 10 au moins
  partout (U4f : `delta_level` peut être un dictionnaire par scénario, pour tout événement).
- **Suggestions** : bouton « ⚡ Proposer des wild cards » à part des lacunes (3 idées, un appel
  IA, rien n'écrit, contrôles en ⚠) ; case « ⚡ wild card » à côté de ✨ Proposer
  (`--wild-card`) ; **jamais en lot**.
- **Simulation** : lecture IA et Passe exhaustive **forcées** ; contrôle IA des règles de lore
  avant tout calcul (cache `state/et_si_regles_lore.json`) ; adoption refusée sans Passe.
- **Injection** : `wild_card_impose: true`, forces jusqu'à 35, `wild_card: true` dans la fiche,
  récit prévenu que l'événement se produit.
- **U4b abandonné** : le frein près des bornes ne s'applique presque pas à une rupture (pas de
  `GAIN_CHOCS` ni de plafond de 15) ; le gain aurait été de quelques points au milieu de l'échelle.

**21 nov — restes des wild cards, Passe, modifier** (détail dans l'archive) :
- **U4d5** : la ligne « Scénarios : … » d'une idée est imposée à ✨ Proposer ; **U4d6** :
  contraintes réduites à une date retirées ; **U4g** : Shackleton supprimée ; **U4e** : règle
  « fait établi » proposée d'office à l'étape ⑤, badge ⚡.
- **Passe lente** : cause trouvée (Large 4 derrière `mistral-large-latest`), Large 3 fixé
  (`patch_llm_large3.py`) : ≈ 30 s par lot au lieu de ≈ 4 min ; parallélisme écarté.
- **U4h / U4h2** : « ✏️ Modifier une hypothèse existante » (Charger, Remplacer à sa place).

**Ordre décidé (David, 7 nov)** : 1. éprouver les chemins ; 2. **entités** dans « et si ? »
(**fait**) ; 3. **modes automatiques + wild cards** (**fait** le 15 nov, restes ci-dessous) ;
4. **étape 5 : fermer** les accès directs (**fait**, sauf le sort des « Outils directs »).

À faire :
- 🔴 **Wild cards, restes** :
  a) ✨ Proposer ne fait pas jouer les écarts entre scénarios (archées, Zéro-R : même force
  partout) : forces par scénario corrigées à la main ;
  b) idée : interdire de nommer un acteur propre à un monde dans une idée valable pour plusieurs ;
  c) éprouver le parcours complet sur une branche jetable (voir A1).
- ⚪ **Passe exhaustive en parallèle** (plusieurs lots à la fois) : écarté le 21 nov (≈ 15 min
  par wild card en Large 3) ; à rouvrir seulement si la durée gêne à l'usage.
- 🔴 **Source mince → invention, suite** : a) **anachronisme sans année** : U3y ne détecte que
  des années ou « aujourd'hui » ; une scène de 2098 transposée passe (piste : question
  ajoutée à l'appel `verifier_contraintes`) ; b) refuser à l'extraction les événements à
  peine mentionnés (une incise) ; c) **impacts** des événements d'article : 6 variables et
  forces 15 à 22 pour des faits locaux (la portée `locale` n'abaisse pas les forces) à juger
  avant d'injecter en volume ; d) vérifier en réel que la fiche U3aa est fidèle **sans
  relecture** (David ne relit pas chaque fiche).
- 🔴 **Consigne IA** : « reprendre tels quels les chiffres des contraintes » (l'IA a
  paraphrasé Pew « 1 sur 10 / 1 sur 5 chez les moins de 30 ans » en « 10-20 % de la
  population » ; corrigé à la main le 7 nov, `.bak_chiffres`).
- ⚪ **« Outils directs (ancien, avancé) »** (menu, replié) : Créer des entités, Injecter des
  événements, Injecter des signaux faibles, avec leurs files à remplir à la main
  (`/api/yaml/append`, `/api/idees/proposer`) : les garder, ou les retirer à leur tour.
- ⚪ **Adopter + injecter en bloc pour événements et signaux** : exige une simulation avant
  l'adoption, donc hors du lot d'entités (décision du 14 nov).
- ⚪ **Entité depuis un article** : l'utilisateur écrit le nom et ce que l'article en dit ;
  pas de détection automatique des entités citées ni de rapprochement avec les entités
  de l'article.
- ⚪ **Annulation d'une entité injectée** : ne l'enlève pas du vault (`undo_custom.py`).
- ⚪ **`confirm()` restants** (Carte, Lore, Chantiers, quelques boutons) : à passer en
  double-clic (`armer2()`) si l'un d'eux reste muet.
- ⚪ **U3bd** (suggestions de signaux) : écrit, testé sur copie, **non appliqué** (la veille
  suffit) ; garder ou jeter le fichier.
- ⚪ **Hypothèse d'essai** `alliance_des_territoires_froids_europeens` (entité, non adoptée) :
  `python3 generator/et_si_supprimer.py --id … --apply` si elle n'est pas voulue.
- ⚪ **Idées de wild cards en réserve** (non ajoutées) : supraconducteur Zéro-R
  (new_sustainability, policy_reform ; bloc proposé le 21 nov, forces 25-35, identiques dans les
  deux scénarios), thérapie des archées des Mariannes (new_sustainability, eco_communalism,
  policy_reform). Shackleton supprimée le 21 nov (U4g) ; son rapport reste dans
  `documentation/need_action/et_si_shackleton_platinoides_2052.md`.
- ⚪ **« Fiches à relire »** : la recherche ne cible que des mots isolés ; une recherche de
  noms propres à plusieurs mots la rendrait plus utile.
- ⚪ **Détection des doublons d'événements** : elle repose sur l'IA (slug « déjà connu ») ; une
  reformulation très différente d'un événement déjà injecté peut passer. Piste : comparaison
  mécanique (lieu + date + entités).
- ⚪ **Archétype injecté** (`evenements/<id>.md`) : colonnes « Réalisation » et « Impact » du
  tableau des instances vides pour l'instance injectée ; à comparer avec un archétype plus
  ancien avant de décider si c'est normal.
- ⚪ **Veille** : passer la date d'observation comme date imposée. Signaux toujours ≤ 2097
  (décision conservée).
- ⚪ Perte connue : l'IA ne peut plus ajouter de variables en plus (signaux).
- ⚪ Cosmétique : suffixe d'id `_2098` pour une date 2097 (`methane_arctique_nordark_2097`).
- ⚪ Cosmétique (11 nov) : a) libellé « écarté (plan / projet / débat) » aussi pour une
  statistique ou une citation tronquée → « écarté (pas un événement) » ; b) citation dont le
  guillemet ouvrant n'est pas fermé dans la phrase de l'article affichée « « « … » » ; c)
  contexte U3s : titre = nom de fichier et ligne `---` dans le passage ; d) l'archétype
  `evenements/accords_oms_regulation_mondiale_2039.md` garde l'ancien nom d'affichage.

## ⚪ B5. Chaîne idées → signaux et veille (S20, S21)

- **S20** : bouton « Proposer en événement » quand l'assistant ✨ signale
  « ressemble plutôt à un événement » ; doublons d'idées sous un autre nom
  (`idees_vers_queue.py` ne compare que l'`id`) ; champ `persistance` dans la file
  des entités (si besoin).
- **S20 (constat)** : un signal custom n'est jamais « structurant » dans
  `build_signal_trajectory()`.
- **S21 injection des signaux** : polarité ±1 par scénario **faite** via « et si ? »
  (7 nov). Reste : a) « sans suite » par scénario ; b) `delta_level` par scénario.
- **S21 veille** : OCR des PDF scannés ; fusion multi-IA pour l'état du monde ;
  défaire une fusion dans 🔭 ; recherche web en deux temps (≈ 12 fois plus chère) ;
  repérer les signaux qui relient plusieurs variables (analyse en réseau sur la
  matrice 12×12, base : `micmac_matrice.py`).

## ⚪ B6. GUI — outils encore en ligne de commande (S5, S24)

- **S5** `promote_ville.py` : demande des confirmations (`input()`) ; à trancher :
  redécoupage interactif (comme les écrans SSE) ou bouton à paramètres fixes.
- **S24** audits S23 (`audit_signatures.py`, `audit_lieu_zone.py`,
  `audit_temporel.py`) : CLI seulement.

## ⚪ B7. Moteur de propagation — réglages (S19)

Moteur `dynamique.py` (manuel §3ter). Règle : **choc = s'estompe, rupture = change
le monde** ; `GAIN_CHOCS` 0,25 (17 oct).
- **Recalage de `K_COUPLAGE`** : matrice révisée le 25 oct (ρ 0,42 → 0,34, K 0,05
  inchangé, niveaux 2098 déplacés d'au plus 1,2 point, référence
  `documentation/niveaux_avant_s28.json`). Au prochain gros lot d'injections :
  `banc_calibration.py --scenarios all --balayage-k 0.05`, et décider s'il faut
  passer K à ≈ 0,063. Depuis le 30 oct les signaux faibles comptent dans le
  couplage (écart ≤ 1,1 point, référence `documentation/niveaux_avant_s19_signaux.json`).
- **Saturation près des bornes** : en breakdown, 8 variables entre 99 et 100 ; en
  new_sustainability, `gouvernance_institutions` à 0,3 ; un choc y est presque sans
  effet chiffré (Pacte de Tabriz : +0,3 au plus). À revoir si des articles en
  pâtissent.
- **Dérive de `reference` vers fortress_world** (géopolitique 75 → 86 en 2098) :
  peut-être voulue par le lore.
- Mineurs : `matplotlib` absent (le banc écrit des CSV) ; les tendances (`trend`) des
  fiches scénario ne sont lues par aucun calcul.

## ⚪ B8. Mistral Large 4 — à rejuger (S29)

Branché (`mistral-large-4`), non retenu par défaut. **21 nov** : l'alias `mistral-large-latest`
pointait vers lui depuis une date inconnue (probablement le 14 nov) ; les trois tiers « large »
sont désormais fixés sur `mistral-large-2512` (Large 3). Mesure : Passe exhaustive ≈ 4 min par
lot en Large 4 contre ≈ 30 s en Large 3. À rejuger s'il sort de l'aperçu, si la réflexion peut
être coupée ou si le tarif baisse. Le correctif « THINKING » de `llm_client.py` (×4 sur
`max_tokens` pour tout modèle « large ») s'applique aussi à Large 3 : sans effet sur le coût
(seule la sortie réelle compte), à garder.

---

# PARTIE C — ENRICHISSEMENT DE LA BASE

*À lancer en volume une fois la partie A vide.*

## 🔴 C1. Volume d'articles par revue (S23)

- Audit du 30 oct (216 articles, tous publiables) : Courrier des Continents 6,
  Crieur des Marges 7, Chronique 8, Miroir 8, Moniteur 10, Peuple Souverain 13,
  Journal des Normes 16, Lecteur des Communs 17, Radio Frontières 24,
  Contre-Courant 30, Limes 35, Revue de la Transition 42.
- Plancher à 15 = 38 articles (Courrier 9, Crieur 8, Chronique 7, Miroir 7,
  Moniteur 5, Peuple 2) ; à 20 = 75. **Conseil : 15.** Plancher pas encore choisi.
- Moyen : séries ciblées (scénario + ligne éditoriale dans `config_series.yaml`).
- Prérequis levé le 31 oct : les trois sources de noms de réseaux concordent
  (`JOURNAL_PROFILES` aligné sur `journaux.yaml`).
- Après les séries : `chapos_revues.py` puis `publier_site.sh` ; mesurer S25 (A2).

## 🔴 C2. Veille monde réel (S21)

Chaîne en production (manuel §3quater).
- **10 candidats RSS à trier** dans l'onglet 🔭 (dont 2 faibles : Wegovy, BCE).
- **Livres** : 32 pages repérées restent dans le rapport JRC (≈ 4 passes) ; juger
  l'effet du prompt d'extraction durci le 30 oct (recommandation de l'auteur ≠
  observation ; grand programme d'État ≠ marginal). Documents à déposer : ESPAS
  Horizon Scanning n° 10, JRC FUTURINNOV, PNUE Navigating New Horizons, WEF Top 10
  Emerging Technologies 2025, ONU Horizon Scanning 2026.
- **Flux RSS** : 16 flux sur 31 sources ; relancer `verifier_flux_rss.py` de temps
  en temps ; ajouter des sources de façon ciblée (flux actif, résumé exploitable,
  angle absent des 16 flux). Les 15 sources sans flux sont institutionnelles (OCDE,
  PNUD, JRC, ESPAS…), exploitées par les livres ou le prompt collé ; Crisis Group
  n'a pas de flux CrisisWatch ; certains flux ne donnent qu'un résumé (STAT+, Rest
  of World, GEAB).

## 🔴 C3. Géographie — choix de lore (S24)

- **Incohérences `origine_reelle` / chaîne de parenté** (scan du 30 oct,
  `scan_geographie_complet.py --all`, étape 3) — pour chacune : déplacer la zone
  sous la candidate, réaffecter le pays dans la Carte, ou laisser :
  - breakdown, `hanse_baltique` (Pologne) sous `arc_eurasien_central`, qui n'a pas
    la Pologne → candidate `geneve_bunker_institutions` ;
  - breakdown, `la_haye_cour_internationale` (Pays-Bas) sous `la_haye_tribunal` →
    candidate `europe_nord_ouest` ;
  - fortress_world, `almaty_zone_friction` (Kazakhstan) sous
    `zones_grises_tampons` → candidate `bloc_eurasiatique_occidental`.
  Le même scan signale 6 zones suspectes de patron spatial (en cache).
- **Appréciations, sans erreur** : `asie_pacifique_sud_est` (breakdown) trop
  centralisée pour le patron spatial ; 3 zones de reference trop innovantes ;
  Paraguay rangé sous `amazon_pacte_gardiens` (breakdown).
- **Ancrage local** : une zone sans instance localisée reste dominée par des entités
  d'ailleurs (Maghreb ; Sri Lanka : 0 instance locale) ; créer des instances
  localisées si le besoin se confirme.

## ⚪ C4. Lore — règles, relectures, nettoyage (S18, S28.1)

- **Règles de lore manquantes** pour new_sustainability, eco_communalism et
  policy_reform (faits à fournir par David). breakdown a ses premières règles
  (Genève, Iran), reference en a de plus (Mourmansk, Atlantique).
- **Relectures IA ciblées** au fil de l'eau (étape 4, `--limit 10` par scénario,
  ≈ 5 centimes) ; une passe complète (≈ 830 fiches) coûterait 4 à 6 $.
- **Texte rédigé des fiches variables** (sections 3 à 10) : peut encore évoquer des
  liens modifiés par la révision de la matrice ; à relire au fil de l'eau.
- Pièges de slugs ≠ noms : `les_veilleurs_des_nappes_phreatiques` = Sentinelles des
  Aquifères Oubliés ; `conseil_regulation_algorithmique` = Autorité Numérique du
  Bloc Atlantique (≠ `anba_siege_atlantique`, entreprise maritime).
- `_a_supprimer/` (fiche et archétype fusionnés des Archives Neutres, 13 dossiers
  `fusion_*_20261024_*`, `geographie_obsolete/breakdown_avant_test.md`) : à vider
  quand les fusions sont confirmées à l'usage.
- **Doublons** : les 9 paires que signale encore `scan_doublons_lore.py` sont des
  acteurs distincts, déjà examinés.
- **Relations à sens unique** (relevé du 31 oct, aperçu ④) : 3 anciennes, une par
  scénario — `institutions_multilaterales_survivantes_reference` (opposition
  `consortiums_prives_de_gestion_des_donnees_critiques_reference`),
  `hanse_baltique_breakdown` (`armada_logistique_nordique_breakdown`),
  `tribunal_algorithmique_de_bruxelles_new_sustainability`
  (`bloc_des_architectes_d_efficience_algorithmique_new_sustainability`). Corrigées
  par la routine « Relations & lore » étape 2 au prochain passage.

## ⚪ C5. Hypothèses et personnages (S30, S15, S23)

- **S30 second cas test : « La ruée vers l'espace »** (saison 3 de la Red Team
  Défense : ressources spatiales, acteurs privés et étatiques) ; variable
  `frontieres_du_systeme`. Pourrait servir au test restant de A1 si une entité y
  disparaît.
- **Exemples à ne jamais adopter** : `occupation_bresil_2029` et
  `reunification_ecosse_2070` (`et_si/hypotheses.yaml`) ; `invasion_bresil_2029`
  reste au banc de rejeu.
- **S15** : Milan (QG du Mouvement de Reconquête européenne) et Lyon (antenne) ne
  sont que des `lieu` dans `zone_euro_sud` : en faire des sous-zones si d'autres
  entités doivent y être placées. Personnages en réserve, exclus des articles :
  Malo, Anton Vasko, Raimon et Hyphan ; à ré-autoriser (🎯) quand le récit les fera
  apparaître.
- **S23 Hyphan** : exclue des articles hors `reference` ; la ré-exclure après toute
  régénération de sa fiche. Laissé tel quel (5 oct) : l'article Amazônia Viva
  (`20260924_101034_…`) fait de Hyphan la dirigeante d'Ergo-Wian « depuis 2091 ».

---

# ROUTINES (rappel)

- **Après chaque lot d'entités** : « Relations & lore » étapes 1 → 2 → 3, puis
  `validate.py` ; `scan_doublons_lore.py` (il ne voit que les noms proches).
- **Après un gros lot d'injections** : `banc_calibration.py --scenarios all
  --balayage-k 0.05` ; `mesure_niveaux.py --sauver <fichier>` avant et
  `--comparer <fichier>` après tout réglage du moteur.
- **Après une retouche de `influence_matrix.md` ou d'une `systemic_criticality`** :
  `micmac_matrice.py`, puis `regenerer_position_fiches.py --apply`.
- **Après de nouveaux articles** : `chapos_revues.py` puis `publier_site.sh`.
- **De temps en temps** : `verifier_flux_rss.py`.
- **Nouveau script** : calculer les slugs avec `from slugs import slugify`, jamais
  une copie locale de la fonction.
- **Sorties à transmettre à Claude** : `> ~/Documents/Ourrassol_sorties/<nom>.txt 2>&1`,
  puis glisser le fichier ; commandes lancées depuis la racine du vault (pas de `cd`).
- **git 2.17** : `git checkout -b` / `git checkout main` (pas `git switch`).
- **Simulateur, étape ③** : les numéros de Sauter / Inclure sont ceux de l'étape ④,
  PAS ceux de la liste d'application du rapport ① (numérotée autrement). Contrôler
  avec « Liste de l'étape ④ » (champs remplis, sans IA) avant « Injecter ».
- **Pousser** : `git push origin main` (les branches jetables restent locales).
- **Modèles** : toujours une version explicite dans `TASK_TIER_DEFAULTS` (jamais `-latest`) ;
  de temps en temps, lister les modèles du compte (`c.models.list()`, gratuit).
- **Patchs** : recevoir le `.py` prêt (à placer dans `generator/`), `python3 generator/patch_….py` en dry-run puis `--apply`, sortie vers `~/Documents/Ourrassol_sorties/`. Changement de `app.py` : relancer Flask entièrement ; `app.js` seul : Ctrl-Maj-R. `node --check` échoue sur `||=` (Node ancien) : sans conséquence.
