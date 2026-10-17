# Reste à faire à la main — effondrement_circulation_atlantique_2067

*Généré le 2026-10-17 12:03 par appliquer_et_si.py, à partir de la simulation du 2026-10-17T10:46 (v8.20). Les opérations mécaniques (zones, trajectoires, relations) sont déjà appliquées : ne figure ici que ce qui reste à la main.*

## reference

### Décisions laissées de côté (⚠)

- [ ] 1. opposition nouvelle : Armada Logistique Nordique ↔ OptiFlow Global Logistics Network (OGLN) [lecture] — ⚠ contredit une alliance existante. Garder tel quel, ou `python3 generator/appliquer_et_si.py --id effondrement_circulation_atlantique_2067 --inclure 8 --apply`.
- [ ] 2. opposition nouvelle : Gouvernements du Bloc Sahélien Autonome ↔ Union Africaine Résilience (UAR) [lecture] — ⚠ contredit une alliance existante. Garder tel quel, ou `python3 generator/appliquer_et_si.py --id effondrement_circulation_atlantique_2067 --inclure 10 --apply`.
- [ ] 3. opposition nouvelle : Bloc Eurasien Central (BEC) ↔ Bloc Ressources Eurasiatique (BRE) [passe] — ⚠ contredit une alliance existante. Garder tel quel, ou `python3 generator/appliquer_et_si.py --id effondrement_circulation_atlantique_2067 --inclure 12 --apply`.

### Nouvelles entités proposées (facultatif)

- [ ] 4. 3 entité(s) : choisir `category`, garder ou retirer chaque entrée, coller dans `entites_custom/queue.yaml`, puis `python3 generator/create_entities_and_instances.py --mode custom`.

```yaml
- nom: Alliance des Territoires Froids Européens
  category: <à choisir>
  role: Bloc de coopération pour la gestion des crises climatiques et énergétiques en Europe du Nord-Ouest, regroupant des régions sinistrées et des villes en repli.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: europe_occidentale_reconstruite
  source: et_si_effondrement_circulation_atlantique_2067
- nom: Consortium des Deltas de Crise
  category: <à choisir>
  role: Structure de coordination entre les zones submergées (Gange, Mékong) pour gérer les migrations climatiques et les conflits fonciers, en partenariat avec les Consortiums d'Agriculture Verticale.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: zones_grises_globales
  source: et_si_effondrement_circulation_atlantique_2067
- nom: Fonds d'Urgence Climatique Atlantique
  category: <à choisir>
  role: Fonds spéculatif créé par Ergo-Wian et des Consortiums Opaques pour investir dans les infrastructures de relocalisation et les technologies de survie en Europe du Nord-Ouest.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: europe_occidentale_reconstruite
  source: et_si_effondrement_circulation_atlantique_2067
```

### Règle de lore (brouillon)

- [ ] 5. Relire puis ajouter à `documentation/lore_regles.yaml`, section `reference` (vérifier le format sur une règle existante, par exemple `bruxelles_pas_un_centre`).

```yaml
# section reference > regles
# contrainte à transformer si besoin : La circulation atlantique ne redémarre pas avant 2098 : le changement est permanent.
# contrainte à transformer si besoin : Le refroidissement touche surtout l'Europe du Nord-Ouest ; le réchauffement global continue ailleurs.
```

### Articles à relire

- [ ] 6. `articles/reference/20260820_194020_reference_culture_article_3janvier2098.md` — *« Mémoire en fragments : quand l’art défie la muraille de verre »*, 3 janvier 2098 (cite `delta_du_gange_reference`, zone `europe_occidentale_reconstruite`)
- [ ] 7. `articles/reference/20260820_194438_reference_histoire_patrimoine_article_5avril2098.md` — *Les mémoires oubliées de Tbilissi : quand l’Histoire résiste aux algorithmes*, 5 avril 2098 (cite `delta_du_gange_reference`)

### Pour finir

- [ ] 8. Relecture du lore : `python3 generator/audit_lore.py --scenario reference` (puis étapes 2 et 3 de Relations & lore si besoin)
- [ ] 9. Résumé du scénario (payant, un appel) : `python3 generator/generate_resume_scenarios.py --scenario reference`

## Site

- [ ] 10. Si des articles ont été corrigés : `python3 generator/chapos_revues.py`, puis `bash generator/publier_site.sh`

## Non repris ici

Les « possibles » de la passe exhaustive, la carte et les fiches trouvées par mots-clés restent dans le rapport du simulateur : `documentation/need_action/et_si_effondrement_circulation_atlantique_2067.md`.
