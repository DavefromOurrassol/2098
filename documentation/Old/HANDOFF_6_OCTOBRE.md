# HANDOFF — 6 octobre 2026

Suite de `HANDOFF_5_OCTOBRE.md`. Session consacrée à **S25** (Kharg-9),
**S26** (journal d'une autre zone, clos) et à une série de petits chantiers.
Site republié : **167 articles en ligne**.

## Fait
- **Recherche du site** testée en ligne par David : fonctionnelle.
- **`nouveau_califat_barcelone`** (new_sustainability) : zone N1 vide (ni pays
  ni description), supprimée depuis la Carte ; ses 2 rédactions retirées de
  `journaux.yaml` (`.bak_califat`). validate 0/0/0.
- **S25 — Kharg-9** : mesuré (eco 13/22, policy 11/29, fortress 11/59 ; encore
  fort après le 22 août ; 24/27 via la sélection d'instances).
  - Cooldown durci pour toutes les instances : `COOLDOWN_STREAK` 3 → 2,
    `COOLDOWN_DURATION` 2 → 3 (`loader.py`, `.bak_s25`), ≈ 40 % de présence au
    plus.
  - Kharg-9 exclu des articles en eco_communalism (`set_selection_instance.py`).
  - Doublon *Le Nexus qui défie Genève* (Revue de la Transition) retiré du site.
    Paire « Dernier Souffle » (Limes / Moniteur) : sujets différents, gardée.
- **S26 — clos** : mode Forcer, champ « Journal d'une autre zone » (liste
  déroulante) = `generate.py --forcer-zone-journal`. Le journal choisi couvre
  l'élément comme un fait étranger ; `zone_principale` = zone du journal.
  Testé en réel (Kharg-9 vu du Maghreb Atlantique), article test retiré.
- **« Rédaction à <ville> »** sur le site (pied, bandeau de la Une, kiosque).
- **Nettoyage** : `publier_site.sh` exécutable ; `nettoyer_placeholders_
  journaux.py` supprimé ; `_a_supprimer/` supprimé ; aperçu
  `reparer_bloc_metadonnees.py` : 0 article ; Hacker News retiré des flux RSS.
- **Clos par décision** : S3, S6, S7, S10, `_extract_byline()`.

## Décisions actées
- Cooldown 2/3 pour **toutes** les instances (pas un plafond propre à Kharg-9).
- Baisser l'impact de Kharg-9 : écarté (4/3 n'est pas extrême).
- S26 : `zone_principale` = zone du journal ; l'élément reste le sujet forcé
  (`developpements` alimenté comme d'habitude pour un événement).
- Champ S26 en liste déroulante (zones à rédaction pour la ligne, dans les
  scénarios où l'élément existe).
- Hacker News : `rss: null`, reste proposé à l'IA de chat ; ne pas accepter
  son flux si `verifier_flux_rss.py --apply` le retrouve.

## Reste à faire
- **Mesurer l'effet du cooldown** sur les prochaines séries (même comptage
  « kharg », articles postérieurs au 6 oct). Si les titres « casino des
  données / défie Genève-Nexus » reviennent, retoucher la
  `description_journalistique` de `terminal_kharg_data_haven_*`.
- **Confirmer S22** à la prochaine vraie injection de signal.
- **Volume des revues** : séries ciblées (en ligne, le Crieur des Marges n'a
  qu'un article ; Courrier, Chronique, Miroir peu).
- **S27** simulateur « et si ? » (cas test : invasion du Brésil, 2029).
- Chantier 5 : identités visuelles, photos, audio, multilingue.
- Hérité : S23 (profils de journaux en triple), S24 (`_slugify()`,
  `generate_journaux.py --update`, outils d'audit CLI), S18 à S21, #3 P20.

## Fichiers livrés
- **Nouveaux (`generator/`, déjà appliqués, refusent un second passage)** :
  `patch_s26_journal_etranger.py`, `patch_s26_liste_zones_journal.py`,
  `patch_redaction_siege.py`.
- **Modifiés** : `generator/loader.py` (`.bak_s25`), `generator/generate.py` et
  `generator/prompt_builder.py` (`.bak_s26`), `gui/app.py`
  (`.bak_s26_liste`), `gui/scripts_config.json` (`.bak_s26`,
  `.bak_s26_liste`), `generator/export_revues.py` (`.bak_redaction`),
  `generator/journaux.yaml` (`.bak_califat`),
  `generator/sources_signaux_faibles.yaml` (`.bak_hn`).
- **Données** : `geographie/new_sustainability.md` (zone supprimée, `.bak` de
  la Carte) ; `instances/terminal_kharg_data_haven_eco_communalism.md`
  (`exclure_articles: true`) ; 1 article new_sustainability supprimé.
- **Supprimés** : `generator/nettoyer_placeholders_journaux.py`,
  `_a_supprimer/`.

## Scripts ad hoc utiles (non livrés en fichier)
- Présence de Kharg-9 par scénario et avant/après une date : parcourir
  `articles/**/*.md`, compter « kharg » dans le titre/chapô/début (sujet) ou
  le corps (cité), date = préfixe `AAAAMMJJ_` du nom de fichier.
- Index du site `site/recherche.json` : clés abrégées `t` titre, `c` chapô,
  `r` revue, `d` date, `u` chemin, `x` texte.

## À reporter dans les documents vivants
Fait dans cette session : `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`,
`USER_MANUAL_COMPLET.md` (§2 cooldown et S26 ; §2octies continents et
« Rédaction à » ; §3 exclusions ; §3quater Hacker News ; §7 route
`zones_journal_forcer`), `USER_MANUAL_HISTORIQUE.md` (addendum du 6 oct).
