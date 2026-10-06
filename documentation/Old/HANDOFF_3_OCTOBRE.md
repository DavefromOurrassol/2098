# HANDOFF — 3 octobre 2026

Suite de `HANDOFF_1_OCTOBRE.md`. Sessions du 2 et du 3 octobre, consacrées à
la **mise en ligne des journaux** : conception des 12 revues de presse,
génération du site statique, hébergement, chapôs de rédaction et fiches des
journaux. Le site est en ligne : **https://ourrassol.pages.dev**. La
prochaine session revient sur la **génération d'articles** (voir S23).

## Fait
- **Concept arrêté** : un site de revues de presse sur le modèle de *Courrier
  International*. **12 revues**, une pro-pouvoir et une d'opposition par
  scénario, chacune ne reprenant que les journaux de son camp. Définies dans
  `generator/revues.yaml` (nom, sous-titre, fondation, siège, style, statut).
- **Cohérence des revues vérifiée** contre les 6 géographies et
  `registre_evenements.md` : aucune date de fondation ne contredit le
  registre ; sièges choisis dans les géographies.
- **Maquette** du *Courrier des Continents* (Une + page article) validée sur
  un canevas de design : c'est le gabarit du site.
- **`export_revues.py`** : audit de rattachement article → journal → revue,
  puis génération du site statique dans `site/` (kiosque, Une, rubriques par
  continent et par zone, thématiques, pages articles, « Nos sources »).
- **Hébergement** : dépôt GitHub privé `ourrassol-site` (à côté du vault),
  projet Cloudflare Pages `ourrassol`, publication par `publier_site.sh`.
- **Chapôs de rédaction** : 145 chapôs écrits par `chapos_revues.py` (voix de
  la revue, pas du journal), en cache dans `state/chapos_revues.json`.
- **Fiches des journaux** : nouveau mode `generate_journaux.py
  --fill-presentation` (présentation, ville, périodicité, fondation dans
  `journaux.yaml`). Essai sur reference/pro_pouvoir validé, puis passage
  complet lancé sur les 6 scénarios.
- **Continents** : les zones sont regroupées en 8 rubriques (Amériques,
  Europe, Afrique, Moyen-Orient, Asie, Océanie, Arctique, Monde) ; 12 zones
  fixées à la main dans `continents_zones.yaml` (Ourrassol en Europe).

## Bugs trouvés
- **Coquille de clé dans `journaux.yaml`** : `europe_occidentale_reconstructee`
  au lieu de `europe_occidentale_reconstruite` (reference, 2 camps). Seule clé
  orpheline des 6 scénarios. Corrigée par `sed` (`.bak_reconstructee`). Effet
  probable : les articles reference d'Europe occidentale ne trouvaient pas
  leur journal et signaient au nom du réseau (non vérifié dans
  `prompt_builder.py`).
- **Signatures inventées** : 73 articles sur 218 ont un `journaliste_slug` vide
  (31) ou absent de `journaux.yaml` (42), ex. « Léa Martines — Réseau Le Monde
  en Tension ». Le site signe alors « La rédaction de *journal* ».
- **Lieu de l'article ≠ zone de son journal** : trois journaux de zones
  différentes couvrent le même Nœud Mnemos de Tbilissi ; *The Broken Ledger*
  (Amérique du Nord) écrit sur Lyon et Sfax. Rendu visible par les chapôs.
- **Erreur temporelle** dans un article de 2098 : effondrement amazonien
  prévu « d'ici 2070 » (`20260924_101034_reference_environnement_climat_…`).
- **Slug fabriqué depuis une ligne de date** : `23_novembre_2098_troms_n_ud_nordark`.
- **Guillemet orphelin dans des titres du site** (« Qui contrôle le récit…
  isruter ») : vient du nettoyage du titre dans `export_revues.py`, qui retire
  le « de tête même quand il n'encadre pas tout le titre. **Non corrigé.**
- **Mois de parution non lu** au premier essai (`editions.json` cherché au
  mauvais endroit) : le site a montré quelques heures des articles datés après
  août. Corrigé (recherche dans `state/`, `generator/state/`, puis le vault).
- Le compte GitHub `DavefromOurrassol` a été créé avec « Se connecter avec
  Apple » (adresse masquée en relais) : se connecter par **Continue with
  Apple**, le mot de passe Gmail ne marche pas.

## Décisions actées
- **12 revues** : breakdown *Le Moniteur de l'Ordre* / *Chronique des Jours
  Courants* ; fortress_world *Limes* / *Radio Frontières* ; new_sustainability
  *La Revue de la Transition* / *Contre-Courant* ; eco_communalism *Le Lecteur
  des Communs* / *Le Crieur des Marges* ; policy_reform *Le Journal des Normes*
  / *Le Peuple Souverain* ; reference *Le Courrier des Continents* / *Le Miroir*.
- **Réseaux `_reseau` gardés tels quels** : ils sont déjà dans le texte de 44
  articles (signatures, et l'« Ordre Zonal » est devenu un acteur du lore de
  breakdown). Les revues sont des publications distinctes qui reprennent leurs
  journaux.
- *Le Moniteur de l'Ordre* et *Limes* sont des **revues privées tolérées par
  tous les blocs** (siège Genève-Bunker), faute de pouvoir unique dans ces
  mondes. *Radio Frontières* est une **radio clandestine** dont la revue publie
  les transcriptions.
- Sièges : Ourrassol, Ceinture Boréale, Chiapas, La Haye, Agadez, Séoul,
  São Paulo (SPAAR), Genève-Bunker ×2 ; 3 revues clandestines sans siège.
- **Flux continu** par date (pas de numéros mensuels stricts) ; numéro du mois
  en en-tête ; seuls les articles datés jusqu'au **mois de parution** actif
  sont publiés.
- **Toutes les zones et toutes les thématiques** apparaissent, même vides ;
  Annonces et Météo publiées, sans chapô de rédaction.
- **Chapô de rédaction** : étape séparée (`chapos_revues.py`), jamais
  automatique, en cache hors des articles ; sur le site il **remplace** le
  chapô du journal (format *Courrier*).
- **Fiche des journaux** dans `journaux.yaml` (pas dans un cache).
- **Hébergement** : Cloudflare Pages (« legacy Pages », toujours pris en
  charge), dépôt privé séparé du vault ; `site/` exclu du git du vault. Le GUI
  Flask reste en local.
- À venir, non commencé : un style visuel par revue ; photos (service P20) ;
  extraits audio (stockage Cloudflare R2 envisagé) ; **version multilingue**.
- Les références entre articles seront travaillées à part (David).

## Reste à faire
- **Site des revues** (chantier 5 du backlog) : 12 identités visuelles,
  guillemet orphelin des titres, photos, audio, multilingue, protection
  d'accès éventuelle, bouton « Publier » dans le GUI.
- **Génération d'articles** (S23, prochaine session) : lieu ≠ zone du journal,
  signatures inventées, erreurs temporelles, slugs, vérifier l'effet de la
  coquille de clé dans `prompt_builder.py`.
- Vault `2098` **public** sur GitHub : à passer en privé si ce n'est pas voulu.
- Hérité : S22 (signal orphelin), S21, S20, S19, #3 P20 (service d'image).

## Fichiers livrés
- **Nouveaux** (`generator/`) : `revues.yaml`, `export_revues.py`,
  `chapos_revues.py`, `publier_site.sh`, `continents_zones.yaml`.
- **Modifié** : `generator/generate_journaux.py` (`--fill-presentation`,
  `--force`, tier `creative_souple` pour ce mode, `.bak_presentation`).
- **Données** : `generator/journaux.yaml` (clé corrigée, fiches ajoutées) ;
  `state/chapos_revues.json` ; `.gitignore` du vault (`site/`).
- **Hors vault** : dépôt `…/Obsidian Vault/ourrassol-site` ; projet
  Cloudflare Pages `ourrassol` (production `main`, pas de build, sortie `/`).

## À reporter dans les documents vivants
Fait dans cette session : `USER_MANUAL_COMPLET.md` (§2octies, entrée
`generate_journaux.py`), `BACKLOG_ACTIF.md` (chantier 5, S23, #3 mis à jour),
`USER_MANUAL_HISTORIQUE.md` (addendum du 2-3 octobre). `BACKLOG_ARCHIVE.md`
inchangé (aucun chantier clos).

## Non traité hérité
S1-S10, S14, S15, S18 inchangés (voir backlog).
