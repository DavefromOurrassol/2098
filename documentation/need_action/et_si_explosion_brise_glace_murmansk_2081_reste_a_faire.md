# Reste à faire à la main — explosion_brise_glace_murmansk_2081

*Généré le 2026-10-17 08:31 par appliquer_et_si.py, à partir de la simulation du 2026-10-17T07:49 (v8.19). Les opérations mécaniques (zones, trajectoires, relations) sont déjà appliquées : ne figure ici que ce qui reste à la main.*

## reference

### Décisions laissées de côté (⚠)

- [ ] 1. Consortium Énergétique des Mers du Nord (`consortium_energetique_des_mers_du_nord_reference`) : émergent → dominant [lecture] — ⚠ saut d'un cran (sans passer par ascendant). Garder tel quel, ou `python3 generator/appliquer_et_si.py --id explosion_brise_glace_murmansk_2081 --inclure 6 --apply`.
- [ ] 2. opposition nouvelle : Sibérie Fédérale ↔ Bloc Eurasien Central (BEC) [lecture] — ⚠ contredit une alliance existante. Garder tel quel, ou `python3 generator/appliquer_et_si.py --id explosion_brise_glace_murmansk_2081 --inclure 12 --apply`.

### Phrases à corriger

- [ ] 3. `instances/murmansk_transit_arctique_reference.md` (Murmansk Transit Arctique)
  - Phrase : « Plaque tournante stratégique du trafic maritime et énergétique arctique, Murmansk Transit Arctique s'est imposée comme nœud incontournable des nouvelles routes commerciales ouvertes par la fonte accélérée des glaces polaires depuis les années 2040 »
  - Contredite par : L'infrastructure Murmansk Transit Arctique n'existe plus en 2098.

### Nouvelles entités proposées (facultatif)

- [ ] 4. 3 entité(s) : choisir `category`, garder ou retirer chaque entrée, coller dans `entites_custom/queue.yaml`, puis `python3 generator/create_entities_and_instances.py --mode custom`.

```yaml
- nom: Commission de Réhabilitation de Mourmansk
  category: <à choisir>
  role: Organisme de gestion post-catastrophe chargé de la décontamination et de la reconstruction partielle de Mourmansk.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: murmansk_transit_arctique
  source: et_si_explosion_brise_glace_murmansk_2081
- nom: Alliance des Ports Arctiques Secondaires
  category: <à choisir>
  role: Réseau de ports arctiques mineurs cherchant à capter une partie des flux logistiques redirigés depuis Mourmansk.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: corridor_arctique_nordique
  source: et_si_explosion_brise_glace_murmansk_2081
- nom: Fonds de Compensation Arctique
  category: <à choisir>
  role: Mécanisme financier pour indemniser les acteurs économiques affectés par la disparition de Mourmansk Transit Arctique.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: tromsoe_aln
  source: et_si_explosion_brise_glace_murmansk_2081
```

### Règle de lore (brouillon)

- [ ] 5. Relire puis ajouter à `documentation/lore_regles.yaml`, section `reference` (vérifier le format sur une règle existante, par exemple `bruxelles_pas_un_centre`).

```yaml
# section reference > regles
- id: murmansk_transit_arctique_disparu_2081
  termes: ["Murmansk Transit Arctique"]
  gravite: a_relire
  message: "Murmansk Transit Arctique disparaît en 2081 (explosion_brise_glace_murmansk_2081) : toute mention au présent après 2081 est fausse."
# contrainte à transformer si besoin : L'infrastructure Murmansk Transit Arctique disparaît définitivement.
# contrainte à transformer si besoin : La ville de Mourmansk survit, mais déclinante et en partie évacuée.
# contrainte à transformer si besoin : Le Passage Arctique du Nord reste ouvert.
# contrainte à transformer si besoin : L'Armada Logistique Nordique, basée à Tromsø, récupère l'essentiel du trafic arctique et se renforce, sans changer de nature.
```

### Articles à relire

- [ ] 6. `articles/reference/20260820_194817_reference_medias_communication_article_27mai2098.md` — *« Le Silence des Algorithmes : Quand les Plateformes Éteignent les Voix du Nord »*, 27 mai 2098 (cite `conseil_des_etats_nordiques_integres_reference`)
- [ ] 7. `articles/reference/20260820_194923_reference_medias_communication_article_4juin2098.md` — *« Qui contrôle le récit contrôle les isruter » : la guerre des flux dans l’Arctique déglacé*, 4 juin 2098 (cite `conseil_des_etats_nordiques_integres_reference`)

### Pour finir

- [ ] 8. Relecture du lore : `python3 generator/audit_lore.py --scenario reference` (puis étapes 2 et 3 de Relations & lore si besoin)
- [ ] 9. Résumé du scénario (payant, un appel) : `python3 generator/generate_resume_scenarios.py --scenario reference`

## Site

- [ ] 10. Si des articles ont été corrigés : `python3 generator/chapos_revues.py`, puis `bash generator/publier_site.sh`

## Non repris ici

Les « possibles » de la passe exhaustive, la carte et les fiches trouvées par mots-clés restent dans le rapport du simulateur : `documentation/need_action/et_si_explosion_brise_glace_murmansk_2081.md`.
