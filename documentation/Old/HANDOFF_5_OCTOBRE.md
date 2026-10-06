# HANDOFF — 5 octobre 2026

Suite de `HANDOFF_4_OCTOBRE.md`. Session consacrée à **S22** (injection des
signaux) et au **site des revues** (chantier 5) : titres, recherche,
continents, plus le retrait de Hyphan hors `reference`. Site republié :
**168 articles en ligne**.

## Fait
- **Vérifications du handoff du 4** : chapôs à jour (0 à refaire), site déjà
  à jour. Les 18 nouveaux journaux avaient leurs fiches.
- **S22 — signal orphelin** (`patch_s22_exception_signal.py`, appliqué) :
  `process_idea()` capture les exceptions variable par variable ; instantané
  fiche variable + registre restauré si l'écriture est interrompue ; échec de
  fiche d'audit signalé. Testé sur faux vault (3 cas), **pas encore en
  conditions réelles**.
- **S22 — `+1`** : exemple JSON `"<1 ou -1>"` (sed, `.bak_plus1`).
- **Audit des revues dans le GUI** : entrée « 📰 Audit des revues (site) »
  (Validation, `--detail`, `--continents`), `gui_verified: true`.
- **Volume des revues — diagnostic** : de 5 (Crieur des Marges) à 44 (Revue de
  la Transition) sur 219 articles ; 39 articles pour tout porter à 15, 74 pour
  20. **Génération reportée.**
- **Titres du site** : guillemets orphelins (24 titres,
  `patch_guillemets_titres.py`) ; titres en capitales remis en casse française
  à l'export (14 articles, `patch_titres_capitales.py` + `_v2.py` + appel
  élargi au chapô / `image_prompt` par sed) ; consigne « titre à la
  française, jamais tout en capitales » ajoutée au prompt (`prompt_builder.py`,
  `.bak_titre_capitales`).
- **Recherche** (`patch_recherche_revues.py`) : loupe par revue + recherche
  globale sur le kiosque, texte complet, sans serveur. Publiée.
- **Continents forcés** (`continents_zones.yaml`) : Bloc Souverainiste
  Non-Signataire, zones grises tampons, institutions multilatérales → Monde ;
  al_hima → Europe ; arc_sahelo_mediterraneen → Afrique.
- **Bloc de métadonnées dans le texte** : 1 article (education, policy_reform,
  23 août) réparé par `reparer_bloc_metadonnees.py`, chapô de revue refait.
- **Hyphan** : `exclure_articles: true` sur les 5 instances hors `reference` ;
  4 articles du lot forcé du 24 sept déplacés dans `_a_supprimer/` (racine du
  vault, avec celui de fortress_world).

## Bugs trouvés, non corrigés
- **Extraction du bloc de métadonnées après retry** (`api.py`, août) :
  cause probable du cas réparé, non relue. Un seul cas sur 219.
- **Kharg-9 surreprésenté** : 18 articles sur 168, doublons quasi identiques
  entre scénarios → **S25**.

## Décisions actées
- Hyphan citable seulement en `reference` ; fortress_world reste « en
  réserve » (instance conservée, exclue).
- L'article Amazônia Viva (Hyphan « dirigeante » d'Ergo-Wian) est laissé tel
  quel.
- Titres : correction à l'export, articles du vault non modifiés.
- Recherche : par revue + globale, texte complet, index maison (pas de
  Pagefind).
- Siège de revue affiché sur toutes ses pages, même pour un article d'ailleurs
  (modèle *Courrier International*).

## Reste à faire
- **Confirmer S22** à la prochaine vraie injection de signal (chemin normal +
  absence de `<1 ou -1>` recopié), puis archiver.
- **Tester la recherche en ligne** (kiosque « sahel » ; une revue ; « geneve »).
- **S25** Kharg-9 : choisir une piste (plafond, impact, exclusion, retrait de
  doublons).
- **S26** journal couvrant un fait d'une autre zone : option du mode Forcer +
  consigne de prompt.
- **S27** simulateur « et si ? » avant injection (évaluer un événement ou un
  signal sans rien écrire) ; cas test : invasion du Brésil par les États-Unis
  en 2029.
- **Volume des revues** : séries ciblées (Crieur, Courrier, Chronique, Miroir
  en priorité).
- `nouveau_califat_barcelone` : confirmer Europe dans `continents_zones.yaml`.
- Optionnel : « Rédaction à Séoul » dans le pied de page ; `rm -r _a_supprimer`.
- Chantier 5 : identités visuelles, photos, audio, multilingue.
- Hérité : S24 (`_slugify()`, `_extract_byline()`, `generate_journaux.py
  --update`, doublon `nettoyer_placeholders_journaux.py`, `chmod +x
  publier_site.sh`), S21, S20, S19, #3 P20.

## Fichiers livrés (`generator/`)
- **Nouveaux** : `patch_s22_exception_signal.py`, `patch_guillemets_titres.py`,
  `patch_titres_capitales.py`, `patch_titres_capitales_v2.py`,
  `patch_recherche_revues.py`, `reparer_bloc_metadonnees.py` (tous déjà
  appliqués ; les patchs refusent un second passage).
- **Modifiés** : `inject_custom_signals.py` (`.bak_s22`, `.bak_plus1`),
  `export_revues.py` (`.bak_guillemets`, `.bak_capitales`, `.bak_capitales2`,
  `.bak_capitales3`, `.bak_recherche`), `prompt_builder.py`
  (`.bak_titre_capitales`), `continents_zones.yaml` (`.bak`),
  `gui/scripts_config.json` (entrée `audit_revues`).
- **Données** : 5 instances `hyphan_raghavan_*` (exclusion) ; 1 article
  policy_reform (`.bak_meta`) ; `state/chapos_revues.json` ; `_a_supprimer/`.

## Scripts ad hoc utiles (non livrés en fichier)
- Blocs transcontinentaux : depuis `generator/`, `import export_revues as x`,
  puis pour chaque zone à journal comparer `x.continent_pays()` de ses pays à
  `x.continent_zone()` (seuil 15 %).
- Doublons de sujet : lire `site/recherche.json` et filtrer titres + chapôs
  sur un mot (« kharg »).

## À reporter dans les documents vivants
Fait dans cette session : `BACKLOG_ACTIF.md` (S22, chantier 5, S23, S24, S25,
S26, S27), `BACKLOG_ARCHIVE.md`, `USER_MANUAL_COMPLET.md` (§2octies recherche /
titres / continents / audit / réparation / siège ; §2nonies consigne de
titre ; §3 S22 et Hyphan), `USER_MANUAL_HISTORIQUE.md` (addendum du 5 oct).
