# Et si ? — Accords de 2039 : OMS régulation mondiale

*Simulation du 2026-11-11 19:03 — lecture seule, rien n'a été injecté (simulateur v8.25).*

Transformation de l’OMS en une institution dotée de pouvoirs de régulation mondiale via les accords de 2039, posant les bases de la régénération médicale planétaire. Genève devient le cœur d’une révolution médicale sans précédent.

**Faits imposés à la lecture IA** :
- Depuis les accords de 2039, qui ont transformé l’OMS en une institution dotée de pouvoirs de régulation mondiale, Genève est le cœur battant d’une révolution médicale sans précédent.
- Transformation de l’OMS en institution dotée de pouvoirs de régulation mondiale via les accords de 2039
- Genève est le cœur battant d’une révolution médicale sans précédent
- Date de l'événement : 2039

- **Apparition** : 2039.01 · **Persistance** : durable · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098
- **Carte** : élément déclaré sans effet territorial (`carte: non`), aucune proposition de carte retenue
- Déclaré : **gouvernance_institutions** — force 20, apaise ↓, montée sur 3 ans
- Déclaré : **geopolitique_conflits** — force 15, apaise ↓, montée sur 5 ans
- Déclaré : **sante_biotechnologies** — force 22, apaise ↓, montée sur 4 ans
- Déclaré : **technologie_information** — force 10, apaise ↓, montée sur 5 ans
- Déclaré : **valeurs_culture_tempo_sociale** — force 12, apaise ↓, montée sur 5 ans

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## new_sustainability

Apparu en 2039 dans le scénario new_sustainability, Accords de 2039 : OMS régulation mondiale agit d'abord sur géopolitique conflits, santé biotechnologies, technologie information, gouvernance institutions et valeurs culture tempo sociale. Son effet le plus fort apaise géopolitique conflits, avec un écart maximal de -4,3 points vers 2058. Par propagation, systèmes productifs travail réagit à son tour environ 16 ans après l'apparition (-0,5 points au plus fort). En 2098, il en subsiste -1,9 points sur géopolitique conflits.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| sante_biotechnologies | 30,0 | 25,5 | 23,3 | **-2,2** | direct |
| geopolitique_conflits | 30,0 | 26,2 | 24,3 | **-1,9** | direct |
| valeurs_culture_tempo_sociale | 55,0 | 49,6 | 48,2 | **-1,4** | direct |
| technologie_information | 70,0 | 60,6 | 59,8 | **-0,8** | direct |
| energie_ressources_critiques | 38,0 | 35,1 | 34,7 | **-0,4** | propagé |
| demographie_mobilite_humaine | 45,0 | 42,6 | 42,2 | **-0,4** | propagé |
| systemes_productifs_travail | 50,0 | 44,3 | 43,9 | **-0,4** | propagé |
| frontieres_du_systeme | 20,0 | 14,6 | 14,3 | **-0,3** | propagé |
| systeme_economique_redistribution | 65,0 | 53,9 | 53,7 | **-0,2** | propagé |
| gouvernance_institutions | 10,0 | 0,2 | 0,1 | **-0,1** | direct |
| organisation_territoires | 35,0 | 22,9 | 22,8 | **-0,1** | propagé |

**Repères** :
- geopolitique_conflits (direct) : pic -4,3 vers 2058
- sante_biotechnologies (direct) : pic -3,9 vers 2050
- technologie_information (direct) : pic -2,2 vers 2050
- gouvernance_institutions (direct) : pic -2,1 vers 2047

**Tensions** : 0 sans l'hypothèse → 0 avec.

### Liste d'application (à valider à la main — rien n'est écrit)

**Élément**
- [ ] 1. Injecter l'événement `accords_oms_regulation_mondiale_2039` (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios de l'hypothèse_
- [ ] 2. Vérifier que la fiche porte les forces simulées (gouvernance_institutions −20, geopolitique_conflits −15, sante_biotechnologies −22, technologie_information −10, valeurs_culture_tempo_sociale −12)
  - event_instances/accords_oms_regulation_mondiale_2039_new_sustainability.md, bloc impact_sur_variables ; python3 generator/trace_injection.py --slug accords_oms_regulation_mondiale_2039 --type evenement --scenario new_sustainability
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
  - _une hypothèse peut contredire des fiches sans les nommer : relecture IA ci-dessous, après l'ajout des faits imposés dans lore_regles.yaml (section Lore)_
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
- id: accords_oms_regulation_mondiale_2039
  description: Transformation de l’OMS en une institution dotée de pouvoirs de régulation mondiale via
    les accords de 2039, posant les bases de la régénération médicale planétaire. Genève devient le cœur
    d’une révolution médicale sans précédent.
  portee: globale
  date_approximative: 2039
  intensite: <à choisir>
  persistance: durable
  scenarios:
  - new_sustainability
  variables_hint:
  - gouvernance_institutions
  - geopolitique_conflits
  - sante_biotechnologies
  - technologie_information
  - valeurs_culture_tempo_sociale
  variables_hint_count: 5
  source: et_si_accords_oms_regulation_mondiale_2039
  faits_imposes:
    new_sustainability:
    - fait: Depuis les accords de 2039, qui ont transformé l’OMS en une institution dotée de pouvoirs
        de régulation mondiale, Genève est le cœur battant d’une révolution médicale sans précédent.
      sort: contrainte
    - fait: Transformation de l’OMS en institution dotée de pouvoirs de régulation mondiale via les accords
        de 2039
      sort: contrainte
    - fait: Genève est le cœur battant d’une révolution médicale sans précédent
      sort: contrainte
    - fait: 'Date de l''événement : 2039'
      sort: contrainte
  date_imposee: 2039.01
  impacts_imposes:
    new_sustainability:
    - variable: gouvernance_institutions
      delta_level: 20
      duree: 3
      polarite: -1
    - variable: geopolitique_conflits
      delta_level: 15
      duree: 5
      polarite: -1
    - variable: sante_biotechnologies
      delta_level: 22
      duree: 4
      polarite: -1
    - variable: technologie_information
      delta_level: 10
      duree: 5
      polarite: -1
    - variable: valeurs_culture_tempo_sociale
      delta_level: 12
      duree: 5
      polarite: -1
  via_matrice_impose: true
```

