# HANDOFF — 29 septembre 2026

Suite de `HANDOFF_28_SEPTEMBRE.md`. Session consacrée aux deux modes
automatiques de la veille « signaux faibles » laissés en S21 : recherche
web par API (option 1) et lecture des flux RSS des sources (option 2).
Détail et justifications dans `BACKLOG_ARCHIVE.md`, mode d'emploi dans
`USER_MANUAL_COMPLET.md` §3quater.

## Fait
- **Option 1, recherche web par API** : 3 tests réels sur Mistral (API
  Conversations + `web_search`). Non retenue (voir Décisions). Scripts de
  test supprimés.
- **Option 2, flux RSS** :
  - `verifier_flux_rss.py` : 16 flux trouvés sur 31 sources, écrits dans
    le YAML (`--apply`, .bak) ; flux périmés de l'ONU et du PNUE écartés.
  - `veille_rss_api.py` : collecte 30 jours, résumés des flux, lots de 40,
    citation exacte vérifiée, mémoire `state/rss_veille.json`, réponse
    `veille_signaux_reponse_rss.md` (`ia: rss`).
  - Premier passage réel : 211 articles → 6 lots → 12 signaux → import :
    12 URL sur 12 OK, 2 fusionnés dans des candidats du 28 sept, **10
    nouveaux candidats** dans l'onglet 🔭. Deuxième passage : 0 article.
- **Prompt collé recentré** : les 16 sources à flux y sont signalées comme
  déjà lues ; l'IA se concentre sur les 15 autres et sur l'élargissement.
- **GUI** : bouton « 📰 Signaux faibles — Lire les flux RSS (API) »
  (`gui_verified: true`), emplacement « Réponse des flux RSS » dans
  l'import.

## Bugs trouvés
- Mistral sans consigne : aucune recherche, 10 signaux de mémoire, URL
  inventées (404).
- `tool_choice` : `any` refusé ; `required` refusé avec un outil intégré.
- Mistral avec consigne : 2 signaux sur 10 déformés, bloc « SOURCES
  CONSULTÉES » faux, aucun `tool_reference` dans ce format.
- Prompt de test pas à jour (fichier du 28 sept sans définition stricte ni
  bloc SOURCES CONSULTÉES) : régénéré.
- Import : avertissement « SOURCES CONSULTÉES absent » pour `rss` →
  dispensé comme `livres`.
- Miens, corrigés avant usage : barre oblique dans une f-string (Python
  3.9 chez David), script lancé depuis la racine du vault.

## Décisions actées
- Recherche web par API **non codée** : pas plus efficace que le prompt
  collé, payante à chaque lancement ; recherche en deux temps gardée en
  réserve.
- RSS : fenêtre de 30 jours, résumés des flux (pas les pages complètes),
  prompt collé recentré.
- Flux périmé (> 180 jours) = pas de flux.

## Reste à faire
- **S21** (mis à jour) : « sans suite » et intensité par scénario pour les
  signaux ; livres (32 pages JRC, PDF à déposer, durcissement du prompt) ;
  OCR ; fusion multi-IA de l'état du monde ; suites RSS (Hacker News sans
  texte, Crisis Group non daté, pages complètes, relance périodique de
  `verifier_flux_rss.py`).
- Trier les 10 nouveaux candidats RSS dans 🔭 (dont 2 plus faibles :
  Wegovy, BCE).
- Hérité : #3 P20 (service d'image), S15, S18, S19, S20.

## Fichiers livrés
- **Nouveaux** (`generator/`) : `verifier_flux_rss.py`, `veille_rss_api.py`.
- **Modifiés** : `export_prompt_signaux.py` (prompt recentré),
  `import_signaux_faibles.py` (une ligne), `sources_signaux_faibles.yaml`
  (16 flux, .bak), `gui/scripts_config.json` (entrée RSS, emplacement
  d'import, description du prompt).
- **État** : `state/rss_veille.json`, `state/veille_signaux.json` (lot
  `20260929_185743`).
- `BACKLOG_ACTIF.md`, `BACKLOG_ARCHIVE.md`, `USER_MANUAL_COMPLET.md`
  (§3quater), `USER_MANUAL_HISTORIQUE.md` (addendum du 29 sept), ce
  handoff.
- Prérequis ajouté : `pip3 install feedparser`.

## Non traité hérité
S1-S10, S14 inchangés (voir backlog).
