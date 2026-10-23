# Reste à faire à la main — pacte_tabriz_2058

*Généré le 2026-10-23 19:42 par appliquer_et_si.py, à partir de la simulation du 2026-10-23T19:11 (v8.25). Les opérations mécaniques (zones, trajectoires, relations) sont déjà appliquées : ne figure ici que ce qui reste à la main.*

## breakdown

### Décisions laissées de côté (⚠)

- [ ] 1. Factions Énergétiques Héritières des Pactes ABS (`factions_energetiques_heritieres_des_pactes_abs_breakdown`) : émergent → dominant [lecture] — ⚠ saut d'un cran (sans passer par ascendant). Garder tel quel, ou `python3 generator/appliquer_et_si.py --id pacte_tabriz_2058 --inclure 7 --apply`.
- [ ] 2. opposition nouvelle : Konsortiet Nordark — Axes du Grand Nord ↔ Ligue Hanséatique Baltique — Le Sceau du Gotland [lecture] — ⚠ contredit une alliance existante. Garder tel quel, ou `python3 generator/appliquer_et_si.py --id pacte_tabriz_2058 --inclure 10 --apply`.

### Carte

- [ ] 3. Sous-zone `detroit_ormuz` (Détroit d'Ormuz) : elle porte aussi Oman et a perdu Iran. Au choix : la laisser ainsi ; la déplacer entière sous `arc_eurasien_central` (Carte → arbre → ↗️ déplacer) ; ou lui rendre une portion de Iran par un tracé (Carte → ✏️ éditer → ✏️ dessiner).
- [ ] 4. Contrôle de la géographie : `python3 generator/scan_geographie_complet.py --scenario breakdown`

### Nouvelles entités proposées (facultatif)

- [ ] 5. 3 entité(s) : choisir `category`, garder ou retirer chaque entrée, coller dans `entites_custom/queue.yaml`, puis `python3 generator/create_entities_and_instances.py --mode custom`.

```yaml
- nom: Veilleurs d'Ormuz
  category: <à choisir>
  role: Contrôle des flux maritimes dans le détroit d'Ormuz pour le compte de l'Arc Eurasien Central.
  etat: émergent
  scenario_ref: breakdown
  scenario_hint:
  - breakdown
  zone_hint: arc_eurasien_central
  source: et_si_pacte_tabriz_2058
- nom: Alliance des Ports Caspiennes
  category: organisation
  role: Coordination des échanges entre les ports de la Caspienne sous influence eurasienne.
  etat: émergent
  scenario_ref: breakdown
  scenario_hint:
  - breakdown
  zone_hint: bassin_caspien_zone_conflit
  source: et_si_pacte_tabriz_2058
- nom: Front de Libération du Golfe
  category: réseau
  role: Résistance armée aux bases eurasiennes dans le sud de l'Iran et à Oman.
  etat: émergent
  scenario_ref: breakdown
  scenario_hint:
  - breakdown
  zone_hint: iran_levant_residuel
  source: et_si_pacte_tabriz_2058
```

### Règle de lore (brouillon)

- [ ] 6. Relire puis ajouter à `documentation/lore_regles.yaml`, section `breakdown` (vérifier le format sur une règle existante, par exemple `bruxelles_pas_un_centre`).

```yaml
# section breakdown > regles
# contrainte à transformer si besoin : À partir de 2058, l'Iran fait partie de l'Arc Eurasien Central ; il n'appartient plus à la Zone Golfe Persique–Levant.
# contrainte à transformer si besoin : L'Arc Eurasien Central dispose de bases sur la côte iranienne du détroit d'Ormuz.
```

### Articles à relire

- [ ] 7. `articles/breakdown/20260706_183156_breakdown_medias_communication_article_24mars2098.md` — *« Mnemos nous ment ? L’Ordre Zonal face à l’effondrement des récits partagés »*, 12 novembre 2098 (zone `arc_eurasien_central`)
- [ ] 8. `articles/breakdown/20260821_194029_breakdown_opinions_editoriaux_article_17janvier2098.md` — *Les archives ne mentent plus, elles trahissent*, 17 janvier 2098 (zone `arc_eurasien_central`)
- [ ] 9. `articles/breakdown/20260823_175311_breakdown_petites_annonces_services_article_22aout2098.md` — *CONVOIS FANTÔMES : LES COURTIERS DE L'OMBRE DES VENELLES*, 22 août 2098 (cite `corridors_eurasiens_convoyage_breakdown`)
- [ ] 10. `articles/breakdown/20260823_181126_breakdown_petites_annonces_services_article_20septembre2098.md` — *CONVOIS NOCTURNES : GUIDES ET ESCORTES POUR LES VENELLES EURASIENNES*, 20 septembre 2098 (cite `corridors_eurasiens_convoyage_breakdown`)
- [ ] 11. `articles/breakdown/20260823_181920_breakdown_petites_annonces_services_article_17janvier2098.md` — *CONVOYEURS RECHERCHENT GUIDES LOCAUX POUR CORRIDOR OURAL-PANNONIE — PASSAGE GARANTI CONTRE SIGNAL*, 17 janvier 2098 (cite `corridors_eurasiens_convoyage_breakdown`)

### Pour finir

- [ ] 12. Relecture du lore : `python3 generator/audit_lore.py --scenario breakdown` (puis étapes 2 et 3 de Relations & lore si besoin)
- [ ] 13. Résumé du scénario (payant, un appel) : `python3 generator/generate_resume_scenarios.py --scenario breakdown`

## Site

- [ ] 14. Si des articles ont été corrigés : `python3 generator/chapos_revues.py`, puis `bash generator/publier_site.sh`

## Non repris ici

Les « possibles » de la passe exhaustive, les tracés de carte et les fiches trouvées par mots-clés restent dans le rapport du simulateur : `documentation/need_action/et_si_pacte_tabriz_2058.md`.
