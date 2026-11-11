# Et si ? — Piratage des écrans du Centre Régénératif du Léman

*Simulation du 2026-11-11 10:44 — lecture seule, rien n'a été injecté (simulateur v8.25).*

Le 8 mars 2098, le collectif Santé pour Tous pirate les écrans du Centre Régénératif du Léman pour y afficher les noms des 1 247 personnes en attente d’une greffe hépatique dans le canton.

**Faits imposés à la lecture IA** :
- 1 247 personnes en attente de greffes hépatiques sont mentionnées.
- Date précise : 8 mars 2098.

- **Apparition** : 2098.03 · **Persistance** : normale · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098.12
- **Carte** : élément déclaré sans effet territorial (`carte: non`), aucune proposition de carte retenue
- Déclaré : **sante_biotechnologies** — force 15, aggrave ↑, montée sur 2 ans
- Déclaré : **gouvernance_institutions** — force 10, aggrave ↑, montée sur 3 ans
- Déclaré : **technologie_information** — force 12, aggrave ↑, montée sur 1 ans
- Déclaré : **valeurs_culture_tempo_sociale** — force 8, apaise ↓, montée sur 4 ans

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## new_sustainability

Dans le scénario new_sustainability, Piratage des écrans du Centre Régénératif du Léman n'a pas d'effet mesurable sur les variables du monde (choc absorbé ou variables déjà à leur plafond).

_(récit construit par le script)_

Effet en fin de période : négligeable (< 0,1 point, choc absorbé ou variables à leur plafond).

**Tensions** : 0 sans l'hypothèse → 0 avec.

### Liste d'application (à valider à la main — rien n'est écrit)

**Élément**
- [ ] 1. Injecter l'événement `piratage_ecrans_greffes_hepatiques_2098` (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios de l'hypothèse_
- [ ] 2. Vérifier que la fiche porte les forces simulées (sante_biotechnologies +15, gouvernance_institutions +10, technologie_information +12, valeurs_culture_tempo_sociale −8)
  - event_instances/piratage_ecrans_greffes_hepatiques_2098_new_sustainability.md, bloc impact_sur_variables ; python3 generator/trace_injection.py --slug piratage_ecrans_greffes_hepatiques_2098 --type evenement --scenario new_sustainability
  - _imposées par l'entrée commune (impacts_imposes, date_imposee) : l'effet doit correspondre à cette simulation_
- [ ] 3. Gros choc : vérifier la lisibilité du moteur
  - `python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05`
  - _S19_

**Lore**
- [ ] 4. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section new_sustainability
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 5. Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche
  - _une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, après l'ajout des faits imposés dans lore_regles.yaml (section Lore)_
- [ ] 6. Estimer la relecture IA des fiches de plus fort impact
  - `python3 generator/audit_lore.py --scenario new_sustainability --llm --estimer --limit 10`
  - _aucun appel_
- [ ] 7. Relecture IA des 10 fiches de plus fort impact (contradictions avec l'hypothèse)
  - `python3 generator/audit_lore.py --scenario new_sustainability --llm --limit 10`
  - _payant (≈ 0,5 centime la fiche) ; après application de l'événement_

**Articles et site**
- [ ] 8. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario new_sustainability`
  - _payant, un appel_
- [ ] 9. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 10. Base
  - `python3 generator/validate.py`
- [ ] 11. Lore
  - `python3 generator/audit_lore.py --scenario new_sustainability`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

## Liste d'application — injection commune

Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). Forces, polarités, durées, date et propagation de cette simulation sont imposées (`impacts_imposes`, `date_imposee`, `via_matrice_impose`) : l'IA de l'injection ne les recalcule pas, elle rédige seulement le récit.

`faits_imposes` : contraintes de l'hypothèse et sort des acteurs du récit (disparaît, change, reste) ; l'injection les donne à l'IA comme faits non négociables.

```yaml
- id: piratage_ecrans_greffes_hepatiques_2098
  description: Le 8 mars 2098, le collectif Santé pour Tous pirate les écrans du Centre Régénératif du
    Léman pour y afficher les noms des 1 247 personnes en attente d’une greffe hépatique dans le canton.
  portee: globale
  date_approximative: 2098
  intensite: <à choisir>
  persistance: normale
  scenarios:
  - new_sustainability
  variables_hint:
  - sante_biotechnologies
  - gouvernance_institutions
  - technologie_information
  - valeurs_culture_tempo_sociale
  variables_hint_count: 4
  source: et_si_piratage_ecrans_greffes_hepatiques_2098
  faits_imposes:
    new_sustainability:
    - fait: 1 247 personnes en attente de greffes hépatiques sont mentionnées.
      sort: contrainte
    - fait: 'Date précise : 8 mars 2098.'
      sort: contrainte
  date_imposee: 2098.03
  impacts_imposes:
    new_sustainability:
    - variable: sante_biotechnologies
      delta_level: 15
      duree: 2
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 10
      duree: 3
      polarite: 1
    - variable: technologie_information
      delta_level: 12
      duree: 1
      polarite: 1
    - variable: valeurs_culture_tempo_sociale
      delta_level: 8
      duree: 4
      polarite: -1
  via_matrice_impose: true
```

