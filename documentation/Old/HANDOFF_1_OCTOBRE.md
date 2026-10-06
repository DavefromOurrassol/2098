# HANDOFF — 1er octobre 2026

Suite de `HANDOFF_29_SEPTEMBRE.md`. Sessions du 30 septembre (courte, fin de
quota) et du 1er octobre, consacrées à l'injection des 5 signaux faibles issus
de la veille, qui étaient tous partis en `needs_review`.

## Fait
- **Injection des 5 signaux réussie** (12 variables, 0 en `needs_review`) :
  `radicalisation_anti_ia_violence`, `data_centers_water_wars_megapoles`,
  `ia_phages_antibioresistance_biosurete`, `climate_migration_sovereignty_treaty`,
  `ia_agents_autonomes_evasion`. Log complet : `injection_01oct.log`.
- **Signal orphelin nettoyé** : `ia_agents_autonomes_evasion` avait été écrit
  dans `gouvernance_institutions` (sections 7 et 12 + 6 lignes du registre) le
  30 sept, sans fiche d'audit, donc sans impact chiffré. Retiré avec
  `undo_custom.py --execute` (dry-run vérifié avant), puis réinjecté proprement.
- **Contrôle de toutes les fiches variables** : seule `organisation_territoires`
  avait un bloc YAML non refermé ; les 11 autres sont saines.
- **Recensement des fenêtres antérieures à 2026** : 44 `date_bascule` qui
  commencent entre 2022 et 2025, dans 11 fiches sur 12 (toutes sauf santé).
- **Discussions sans code** : ajout de sources RSS (méthode de choix, format
  d'une entrée du YAML) ; hébergement des journaux (voir Reste à faire).

## Bugs trouvés
- **`Expecting value … column 18`** (4 signaux sur 5) : l'exemple JSON du prompt
  de l'étape 2 montre `"<+1 ou -1>"`, et Mistral répond `"breakdown": +1`, ce qui
  n'est pas du JSON valide. Corrigé dans `call_claude_json` (voir Fichiers).
- **`Aucun bloc yaml trouvé dans organisation_territoires.md`** : la fermeture
  ```` ``` ```` de la section 12 manquait (origine inconnue). Ajoutée à la main,
  `.bak` fait.
- **Exception en cours d'injection = signal orphelin** : quand une exception
  survient après l'injection d'une première variable, l'idée part entière en
  `needs_review` sans fiche d'audit ni `idee_a_remettre_en_queue`. Le
  mécanisme de reprise ne s'applique qu'aux échecs de validation, pas aux
  exceptions. **Non corrigé.**
- **`MISTRAL_API_KEY non définie`** : le terminal de David tourne sous bash,
  alors que les clés sont dans `~/.zshrc`. Faire `source ~/.zshrc` dans chaque
  nouveau terminal.
- Mistral réutilise parfois les `evenement_cle` qu'il vient d'écrire pour une
  autre variable du même signal, malgré la consigne. Rattrapé par la
  validation et une relance (Mumbai, Tuvalu), non bloquant.

## Décisions actées
- **Plancher de bascule** : une fenêtre `date_bascule` ne peut plus commencer
  avant la plus tardive de deux dates, l'année d'apparition du signal (si
  renseignée) ou l'année en cours (lue sur l'horloge). Un signal faible n'a
  pas encore basculé dans la réalité.
- **Le projet commence en 2026.** `annee_apparition` peut valoir 2025, au sens
  de l'année où le phénomène a été observé dans la réalité, mais aucune
  nouvelle bascule ne peut commencer avant 2026.
- **Les 44 fenêtres existantes antérieures à 2026 sont laissées telles
  quelles** : elles décrivent des tendances déjà en cours, ce qui est cohérent.
  Contrôle des `evenement_cle` datés d'avant 2026 lancé ; aucun résultat
  signalé.
- **Ajout de sources RSS** : de façon ciblée, selon 4 critères (flux actif à
  moins de 30 jours, résumé exploitable, tendances plutôt qu'actualité chaude,
  angle absent des 16 flux actuels).

## Reste à faire
- Corriger le bug « exception = signal orphelin » dans `process_idea()`.
- Option : remplacer `"<+1 ou -1>"` par `"<1 ou -1>"` dans l'exemple JSON du
  prompt de l'étape 2, pour supprimer le `+` à la source (le correctif du
  parsing reste utile en filet de sécurité).
- Outil pour ajouter des sources au YAML à partir d'une simple liste (nom + URL),
  puis lancer `verifier_flux_rss.py --apply` : idée seulement, non codé.
- Hébergement des journaux Ourrassol : piste d'un site statique généré depuis
  le vault (Quartz, ou Hugo/Astro), hébergé sur GitHub Pages, Cloudflare Pages
  ou Netlify ; le GUI Flask reste en local. **À trancher :** un seul site avec
  une rubrique par journal, ou un site par journal ?
- Trier les 10 candidats RSS dans 🔭 (hérité du 29 sept).
- Hérité : S21 (sans suite et intensité par scénario, livres, OCR, fusion
  multi-IA de l'état du monde, suites RSS), #3 P20 (service d'image), S15,
  S18, S19, S20.

## Fichiers livrés
- **Modifié** : `generator/inject_custom_signals.py` (`.bak` à faire avant
  remplacement)
  - `call_claude_json` : en cas d'échec du parsing JSON, retire le `+` devant
    un nombre et réessaie ; un `+20 %` dans un texte valide n'est pas touché ;
  - nouvelle fonction `annee_plancher_bascule()` (la plus tardive entre
    l'apparition et l'année en cours), utilisée dans la consigne de l'étape 2
    et dans `validate_signal_block()` ;
  - consigne de correction et aide en tête de `queue.yaml` mises à jour.
- **Réparé** : `variables/organisation_territoires.md` (fermeture du bloc
  YAML, `.bak`).
- **Données** : 5 fiches dans `signaux_custom/`, fiches variables et
  `registre_evenements.md` mis à jour par l'injection ; `.bak` de
  `queue.yaml` et `needs_review.yaml`.

## À reporter dans les documents vivants
- **USER_MANUAL_COMPLET.md**, injection des signaux custom :
  - le plancher de bascule et le sens de `annee_apparition` (année
    d'observation réelle, 2025 permise) ;
  - le rappel `source ~/.zshrc` sous bash.
- **BACKLOG_ACTIF.md** : les 3 premiers points de « Reste à faire » ;
  l'hébergement des journaux en idée de fonctionnalité.

## Non traité hérité
S1-S10, S14 inchangés (voir backlog).
