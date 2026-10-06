# HANDOFF — 4 octobre 2026

Suite de `HANDOFF_3_OCTOBRE.md`. Sessions du 3 (après-midi) et du 4 octobre,
consacrées à **S23 — génération d'articles** : signatures, lieu ≠ zone,
journaux manquants, rezonage des articles hérités, erreurs temporelles.
Le site est republié : **219 articles publiables sur 219, tous signés par
une personne de la rédaction**.

## Fait
- **Signatures inventées — diagnostic** (`audit_signatures.py`) : 83
  articles mal signés, tous antérieurs aux correctifs du 23-25 août
  (remontée N1, `metadata["journaliste"]`). Pas de bug actif, sauf un
  article sans zone qui sautait le chemin 1 **sans WARN** → WARN ajouté dans
  `get_journal_profile()`.
- **Coquille de clé** : origine trouvée, renommage du 26 sept
  (`_reconstructee` → `_reconstruite`) non reporté dans `journaux.yaml`.
  `europe_occidentale_reconstituee` (eco_communalism) n'est PAS une coquille :
  zone distincte, cohérente partout.
- **Lieu ≠ zone (bug actif)** : avec une zone fixée dans `generate.py`, les
  entités étaient tirées par thématique dans le monde entier (cas réel :
  journal Maghreb, article sur Kharg). Corrigé : jusqu'à
  `ZONE_PLACES_RESERVEES` = 3 places réservées aux instances de la zone du
  journal (N1 + sous-zones, `loader.zones_du_journal()`), au plus
  `MAX_ETRANGERES_ZONE` = 2 instances d'autres zones N1, transnationales
  libres. `build_snapshot(..., zone_article=None)`. Sans zone : inchangé.
  Séries et manuel non concernés (aucune zone fixée, zone = zone dominante
  des instances). Testé en réel : article eco_communalism Maghreb du
  5 août 2098 ancré à Oujda/Tlemcen, Kharg relégué en contexte.
- **9 zones N1 sans rédaction** (créées en septembre) : Zone Euro Sud,
  Al-Hima, Heysham, Anatolie, Madagascar (fortress_world), Écosse
  (breakdown), Nouveau Califat Barcelone, Péninsule Ibérique Coopérative,
  Ibérie Atlantique Fragmentée → **18 rédactions créées**
  (`generate_journaux.py --update`).
- **Rédaction de sous-zone prioritaire** : `get_journal_profile()` remonte
  depuis la zone exacte de l'article (`_resoudre_zone_redaction()`). Nuuk
  signe dans *Nuna Vey*, le reste de l'Espace Nordique dans *NAT
  Kontrollposten*. `export_revues.py` le faisait déjà.
- **`validate.py` : 12ᵉ section `[JOURNAUX]`** : clé orpheline (erreur),
  rédaction factice « Édition … » ou sans personne (erreur), zone N1 sans
  rédaction (avertissement). Base : 0 erreur.
- **Géographie breakdown** : `hanse_baltique` rattachée à
  `arc_eurasien_central` (était sous Genève-Bunker, contradiction avec les
  pays). Texte « ## Zones » régénéré (`validate.py --fix`).
- **Rezonage des articles hérités** (`rezoner_articles.py`) : la
  `zone_principale` d'avant le 21 août avait été reconstituée après coup
  (`enrich_articles_pre_p20.py`). Le LLM lit chaque article et choisit la
  zone N1 (pays + sous-zones fournis). **68 articles rezonés**, dont 6
  corrections manuelles (Bruxelles et Tbilissi → Zone Euro Sud, Kharg →
  Proche-Orient). 8 articles sans le champ : ligne insérée.
- **Réattribution des signatures** (`reattribuer_signatures.py`) : **94
  articles** signés par un·e journaliste curaté·e du bon journal ; nom
  conservé quand il était déjà dans la rédaction ; signature sous le titre
  pour l'ancien format de juin-juillet.
- **`export_revues.py`** : signatures cherchées aussi parmi les orateurs
  (articles oraux), et sous les deux formes de slug (ø, æ…).
- **8 articles sans `ligne_editoriale`** → `pro_pouvoir`, déduit des
  journaux cités dans leur signature (tous pro-pouvoir dans
  `journaux.yaml`).
- **Erreurs temporelles** (`audit_temporel.py`) : 12 passages relevés,
  3 vraies erreurs corrigées (« d'ici 2050/2070 » → 2115/2120) ; règle
  ajoutée aux règles absolues du prompt système (année < 2098 = passé).

## Bugs trouvés, non corrigés
- **`generate_journaux.py --update`** : un lot échoué (JSON cassé par des
  guillemets, même cause que le 29 août) écrit des rédactions factices
  « Édition <zone> » sans journaliste — comportement **déjà documenté**
  (manuel §2), avec son outil de nettoyage **`clean_fallback_journaux.py`**,
  oublié en séance : `nettoyer_placeholders_journaux.py` en est un doublon,
  à supprimer. 7 cas le 3 oct, nettoyés puis régénérés. Désormais signalé
  par `validate.py` (section 12). Amélioration possible : parse JSON
  tolérant (comme `fix_doublons_journalistes.py`) pour moins d'échecs.
- **`_slugify()` (`api.py`)** : ø, æ, å, ß, ł deviennent `_`
  (`eirik_b_rresen`). Même famille que le bug portugais du 14 août.
  Corriger change les slugs existants ; l'export lit les deux formes.
- **`_extract_byline()`** : prenait une ligne d'annonce ou de date pour une
  signature (`convoyeurs_recherchent…`, `23_novembre_2098_…`). Ne sert plus
  qu'en repli depuis le 25 août.
- `audit_signatures.py` n'exclut pas `_index.md` et n'emploie pas le slug du
  pipeline (6 faux positifs résiduels).
- `publier_site.sh` sans droit d'exécution (`chmod +x`, ou `bash …`).
- Deux dossiers `state/` (racine du vault : chapôs, éditions ;
  `generator/state/` : rotations, rezonage) — voulu, à documenter.

## Décisions actées
- Hanse Baltique sous l'Arc eurasien central (breakdown).
- Une sous-zone dotée d'une rédaction signe ses articles ; les journaux de
  Nuuk sont gardés.
- Ancrage local : 3 places réservées, 2 instances étrangères au plus.
- Articles hérités : le **texte** fait foi, pas la `zone_principale`
  reconstituée → rezonage puis réattribution.
- Bruxelles-Forteresse, Genève-Bunker, Bratislava, Tbilissi : Zone Euro Sud
  (fortress_world), conformément au lore de septembre.

## Reste à faire
- **`chapos_revues.py`** : chapôs de revue invalidés pour les 3 articles
  corrigés (empreinte du texte changée), puis republier.
- Vérifier que les 18 nouveaux journaux ont leur fiche publique
  (`generate_journaux.py --all --fill-presentation`).
- Corriger `generate_journaux.py --update` (voir bugs).
- Slugs : `_slugify()`, `_extract_byline()` (backlog).
- Site (chantier 5) : identités visuelles, guillemet orphelin des titres,
  photos, audio, multilingue.
- Hérité : vault `2098` public sur GitHub ; S22, S21, S20, S19, #3 P20.

## Fichiers livrés (`generator/`)
- **Nouveaux** : `audit_signatures.py`, `audit_lieu_zone.py`,
  `reattribuer_signatures.py`, `rezoner_articles.py`, `audit_temporel.py`,
  `nettoyer_placeholders_journaux.py` (doublon de
  `clean_fallback_journaux.py`, à supprimer), patchs `patch_zone_instances.py`,
  `patch_zone_etrangeres.py`, `patch_validate_journaux.py`,
  `patch_redaction_sous_zone.py`, `patch_export_signatures.py`.
- **Modifiés** : `loader.py`, `snapshot.py`, `generate.py`,
  `prompt_builder.py` (WARN zone vide, sous-zone prioritaire, règle
  temporelle), `validate.py`, `export_revues.py` — sauvegardes `.bak_*`.
- **Données** : `journaux.yaml` (18 rédactions ; `.bak_s23_update`,
  `.bak_placeholders`) ; `geographie/breakdown.md` (`.bak_hanse`) ;
  ~170 articles (`.bak_rezonage`, `.bak_signature`, `.bak_ligne`,
  `.bak_temporel`) ; `generator/state/rezonage_articles.json`,
  `rezonage_rapport.md`, `audit_temporel.md`.

## À reporter dans les documents vivants
- `BACKLOG_ACTIF.md` : S23 clos pour signatures, lieu ≠ zone, journaux
  manquants, rezonage, temporel ; ouvrir les points « Bugs trouvés ».
- `USER_MANUAL_COMPLET.md` : zone de `generate.py` et ancrage local ;
  résolution du journal (sous-zone prioritaire) ; `validate.py` section 12 ;
  nouveaux scripts (rezonage, réattribution, audits).
- `USER_MANUAL_HISTORIQUE.md` : addendum du 3-4 octobre.
