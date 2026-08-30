# Handoff — 23 août 2026

Session très dense, sur toute la journée. Détail complet dans
`BACKLOG_MASTER_9_AOUT.md` (points 10, 16, 17, 18, 19, 20) et
`USER_MANUAL_COMPLET.md` (sections juste avant "P20 — Phase A").

## Ce qui a été fait et clos aujourd'hui

1. **P25 clos définitivement.** Cause racine trouvée sur point soulevé
   par David (hiérarchie de zones niveau 1/2/3, jamais prise en compte
   avant) : `journaux.yaml` n'a qu'une entrée par zone N1,
   `_dominant_zone()` peut retourner une sous-zone N2/N3, la recherche
   échouait silencieusement. Nouvelle fonction `_resoudre_zone_n1()`.
   Testé sur 6 cas synthétiques, **confirmé à 100% de fiabilité sur 2
   scénarios indépendants en conditions réelles** (`new_sustainability`,
   `fortress_world`), contre ~25-33% avant.

2. **Bug dashboard "0 articles"** trouvé et corrigé —
   `routes_dashboard.py` avait le même défaut de scan non récursif déjà
   corrigé le 10 août ailleurs, jamais répercuté ici. **Vit dans `gui/`,
   pas `generator/`** (point de confusion en cours de session — noté
   pour éviter de refaire l'erreur).

3. **Consigne `image_prompt` corrigée en trois temps** : variété de
   palette (23% des articles avaient du vocabulaire "bleu"), réutilisation
   des signes distinctifs déjà établis (758/758 instances, déjà transmis
   au LLM mais jamais explicitement lié à la consigne image), puis
   variété de composition (52% des articles avaient le mot "écran" —
   motif dominant "salle de contrôle/hologrammes"). Aucun test réel
   possible — à vérifier sur un futur batch normal.

4. **Idée de "base d'infrastructures" explorée puis résolue sans
   nouveau code** : le pipeline entités/instances existant + le champ
   `signes_distinctifs` couvrent déjà le besoin réel de David.

5. **Garde-fou retry pour `signes_distinctifs`** : le champ n'était pas
   structurellement garanti. Testé en synthétique et en conditions
   réelles (non-régression confirmée, déclenchement réel non observé —
   taux d'échec naturel trop faible).

6. **Cooldown `gelecek_meclisi` (chantier de la veille) confirmé
   fonctionnel après un vrai détour de débogage** : deux bugs distincts
   trouvés en marge — un décalage de 5h entre les fichiers livrés et
   ceux réellement en place (fichiers restés dans `~/Downloads` sans
   être recopiés dans `generator/`), puis un vrai bug de code
   (`load_instance()` reconstruit le dict d'une instance avec une liste
   blanche de champs connus — `garantie_selection` ET `priorite_forcee`
   du 22 août y étaient tous deux absents, silencieusement perdus à
   chaque chargement malgré une écriture correcte sur disque). **Les
   deux corrigés.** Confirmé en conditions réelles sur 2 scénarios :
   `fortress_world` 0/8 nouveaux articles avec `gelecek_meclisi`
   (contre 49% affiché avant), `new_sustainability` 7/17 ≈ 41% (contre
   quasi 100% avant).
   **Important** : ça veut dire que `priorite_forcee` (chantier du 22
   août) n'avait probablement jamais fonctionné en pratique jusqu'à ce
   correctif — seule son écriture avait été testée hier, jamais sa
   prise en compte réelle par une génération. À re-tester si besoin.

7. **Diagnostic des personnes récurrentes clos** — `leena_vainala`
   (42%→30%) et `amara_diallo_nkosi` (42%→22%) ont baissé grâce au
   mécanisme du 22 août seul, sans nouveau code nécessaire.

8. **Découverte majeure en cours de route** : `gelecek_meclisi`,
   entité injectée en custom par David il y a longtemps, était
   quasi-omniprésente sur 4 scénarios (jusqu'à 98% sur
   `new_sustainability`) à cause de la garantie d'inclusion
   inconditionnelle du 21 août, jamais limitée par le cooldown (les
   instances custom y échappent par conception). Nouveau flag
   `injection.garantie_selection` (défaut `true`, non-régression totale)
   pour découpler la garantie de présence de la propagation d'impact sur
   les variables (celle-ci reste active, seule la garantie de présence
   est retirée). Nouvel outil `set_garantie_selection.py`. Appliqué sur
   les 4 fiches `gelecek_meclisi`.

9. **Outillage complet de couverture des journalistes construit**
   (`audit_couverture_journalistes.py`, `propose_couverture_journalistes.py`,
   `inject_journaliste_custom.py` mode manuel+auto) — voir backlog
   point 19 pour le détail complet. Mode auto testé une fois sur
   `fortress_world` (396 redistributions + 21 créations, fragilité
   96-98%→49%). **3 bugs GUI trouvés et corrigés en marge**
   (`mode_only` jamais respecté par `validateRequiredFields()` ni
   `collectArgs()` dans `app.js`, mauvaise convention `--thematiques`).

10. **Format `petites_annonces_services` ET `meteo` corrigés**, deux
    mécanismes distincts, tous deux testés en conditions réelles.
    `STYLE_DESCRIPTIONS` (le style, rapproché par David de P21) +
    `format_fige` (la longueur, **indépendant** de P21 — David a
    explicitement clarifié qu'il ne faut pas les confondre). **3e
    occurrence du même piège "load_X() perd les nouveaux champs" en
    une journée** : `load_thematique()` avait le même défaut de liste
    blanche que `load_instance()` — corrigé. `petites_annonces_services`
    confirmé (`mots_reels: 221`, format transformé en vraie structure
    d'annonce). `meteo` traité en toute fin de session : `format_fige`
    déjà présent (ajouté par David), nouvelle entrée `informatif`
    ajoutée à `STYLE_DESCRIPTIONS` (bulletin factuel plutôt que récit)
    — **"testé et validé"** par David.

## Fichiers livrés aujourd'hui (à remettre en place — attention aux dossiers)

**Dans `generator/`** :
- `prompt_builder.py` (6 correctifs cumulés : zone N1, palette,
  signes distinctifs, composition, `STYLE_DESCRIPTIONS`, rotation
  journalistes de la veille)
- `loader.py` (garantie_selection + priorite_forcee dans la liste
  blanche de `load_instance()`)
- `instance_generation_common.py` (retry signes_distinctifs)
- `set_garantie_selection.py` (nouveau)
- `audit_couverture_journalistes.py` (nouveau)
- `propose_couverture_journalistes.py` (nouveau)
- `inject_journaliste_custom.py` (nouveau)
- `journaux.yaml` (enrichi `seniorite`, puis modifié par le mode auto
  sur `fortress_world` — 396 redistributions + 21 créations)

**Dans `thematiques/`** (édition manuelle, pas de code) :
- `petites_annonces_services.md` — `format_fige: true` ajouté et testé
- `meteo.md` — `format_fige: true` déjà présent (fait par David),
  fonctionnel une fois `loader.py` en place

**Dans `gui/`** (attention, PAS `generator/` — confusion faite en
session) :
- `routes_dashboard.py`
- `app.js`
- `scripts_config.json`

**Redémarrage GUI Flask nécessaire** pour les 3 fichiers `gui/`. Pas
nécessaire pour les fichiers `generator/` (scripts backend).

## Point de reprise exact pour la prochaine session

**Rien de cassé, tout est dans un état stable.** Plusieurs pistes
possibles, aucune urgente :

1. **Terminer le mode auto de couverture des journalistes** sur les 5
   scénarios restants (`breakdown`, `eco_communalism`,
   `new_sustainability`, `policy_reform`, `reference`), tester `--all`,
   éventuellement une 2e passe sur `fortress_world` (49%, encore loin
   de 0%).
2. **Re-tester `priorite_forcee`** en conditions réelles maintenant que
   le bug `load_instance()` est corrigé — jamais confirmé fonctionner
   pour de vrai jusqu'à aujourd'hui.
3. **Vérifier les 3 correctifs `image_prompt`** (palette, signes
   distinctifs, composition) et le correctif `STYLE_DESCRIPTIONS` sur
   un futur batch normal.
4. **Ajuster les valeurs de `seniorite`** au-delà du défaut uniforme
   (chantier du 22 août, jamais fait).

## Reste en attente, non traité aujourd'hui

- `chapo`/`tags`/`image_prompt` vides (~7% des cas, point 14 du
  backlog).
- Choix du service externe de génération d'image (P20).
- Bug mineur `--stats` de `rapprocher_articles.py` (seuil minimum
  d'articles).
- P21 (journaux oraux) — seul le socle `STYLE_DESCRIPTIONS` est prêt,
  le chantier complet (entité `orateur`, champs frontmatter,
  `type_diffusion`) reste à faire en entier.
- Site web public (hébergement, nom de domaine) — mis en pause,
  DS112J jugé insuffisant pour de l'hébergement public.
- Âge/succession générationnelle des journalistes — mis en pause.
- Dette technique : triple implémentation du calcul de couverture
  zone×thématique (audit/propose/mode_auto) — jamais factorisée.

## Fichiers à ré-uploader en début de prochaine session

- `BACKLOG_MASTER_9_AOUT.md` (mis à jour) — remplace la version du
  Project.
- `USER_MANUAL_COMPLET.md` (mis à jour) — remplace la version du
  Project.
- `HANDOFF_23_AOUT.md` (ce fichier) — remplace toute version
  précédente du même jour déjà ajoutée au Project.
