# Et si ? — Réaménagement du quai Wilson après les inondations de 2044

*Simulation du 2026-11-11 19:18 — lecture seule, rien n'a été injecté (simulateur v8.25).*

Ce matin, devant les portes vitrées du Centre Régénératif du Léman, une file d’attente silencieuse s’étire jusqu’au quai Wilson, réaménagé après la montée des eaux de 2044.

**Faits imposés à la lecture IA** :
- Ce matin, devant les portes vitrées du Centre Régénératif du Léman, une file d’attente silencieuse s’étire jusqu’au quai Wilson, réaménagé après la montée des eaux de 2044.
- Montée des eaux en 2044
- Réaménagement du quai Wilson après les inondations
- Lieu : centre_institutionnel_geneve

- **Apparition** : 2044.01 · **Persistance** : durable · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098
- **Carte** : élément déclaré sans effet territorial (`carte: non`), aucune proposition de carte retenue
- Déclaré : **climat_environnement_global** — force 20, aggrave ↑, montée sur 3 ans
- Déclaré : **organisation_territoires** — force 15, apaise ↓, montée sur 5 ans
- Déclaré : **gouvernance_institutions** — force 10, apaise ↓, montée sur 4 ans
- Déclaré : **geopolitique_conflits** — force 5, apaise ↓, montée sur 3 ans
- Déclaré : **sante_biotechnologies** — force 10, apaise ↓, montée sur 5 ans
- Déclaré : **demographie_mobilite_humaine** — force 12, aggrave ↑, montée sur 4 ans

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## new_sustainability

Apparu en 2044 dans le scénario new_sustainability, Réaménagement du quai Wilson après les inondations de 2044 agit d'abord sur climat environnement global, démographie mobilité humaine, organisation territoires, géopolitique conflits, santé biotechnologies et 1 autre. Son effet le plus fort aggrave climat environnement global, avec un écart maximal de +5,0 points vers 2064. Par propagation, technologie information réagit à son tour environ 18 ans après l'apparition (-0,1 points au plus fort). En 2098, il en subsiste +2,0 points sur climat environnement global.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| climat_environnement_global | 35,0 | 31,1 | 33,1 | **+2,0** | direct |
| demographie_mobilite_humaine | 45,0 | 42,2 | 43,6 | **+1,4** | direct |
| sante_biotechnologies | 30,0 | 23,3 | 22,5 | **-0,8** | direct |
| organisation_territoires | 35,0 | 22,8 | 22,3 | **-0,5** | direct |
| geopolitique_conflits | 30,0 | 24,3 | 23,9 | **-0,4** | direct |
| technologie_information | 70,0 | 59,8 | 59,7 | **-0,1** | propagé |
| energie_ressources_critiques | 38,0 | 34,7 | 34,8 | **+0,1** | propagé |
| systemes_productifs_travail | 50,0 | 43,9 | 44,0 | **+0,1** | propagé |

**Repères** :
- climat_environnement_global (direct) : pic +5,0 vers 2064
- demographie_mobilite_humaine (direct) : pic +2,6 vers 2062
- organisation_territoires (direct) : pic -2,5 vers 2056
- geopolitique_conflits (direct) : pic -1,4 vers 2062

**Tensions** : 0 sans l'hypothèse → 0 avec.

### Liste d'application (à valider à la main — rien n'est écrit)

**Élément**
- [ ] 1. Injecter l'événement `reamenagement_quai_wilson_2044` (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios de l'hypothèse_
- [ ] 2. Vérifier que la fiche porte les forces simulées (climat_environnement_global +20, organisation_territoires −15, gouvernance_institutions −10, geopolitique_conflits −5, sante_biotechnologies −10, demographie_mobilite_humaine +12)
  - event_instances/reamenagement_quai_wilson_2044_new_sustainability.md, bloc impact_sur_variables ; python3 generator/trace_injection.py --slug reamenagement_quai_wilson_2044 --type evenement --scenario new_sustainability
  - _imposées par l'entrée commune (impacts_imposes, date_imposee) : l'effet doit correspondre à cette simulation_
- [ ] 3. Gros choc : vérifier la lisibilité du moteur
  - `python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05`
  - _S19_

**Lore**
- [ ] 4. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section new_sustainability
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 5. Termes cherchés : Léman, Wilson
  - _mot entier, sans casse ni accents ; le registre seulement après 2044.01 (chronologie)_
- [ ] 6. Événement `piratage_ecrans_greffes_hepatiques_2098_new_sustainability` cite « Léman »
  - _Piratage des écrans du Centre Régénératif du Léman par Santé pour Tous…_

**Articles et site**
- [ ] 7. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario new_sustainability`
  - _payant, un appel_
- [ ] 8. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 9. Base
  - `python3 generator/validate.py`
- [ ] 10. Lore
  - `python3 generator/audit_lore.py --scenario new_sustainability`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

## Liste d'application — injection commune

Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). Forces, polarités, durées, date et propagation de cette simulation sont imposées (`impacts_imposes`, `date_imposee`, `via_matrice_impose`) : l'IA de l'injection ne les recalcule pas, elle rédige seulement le récit.

`faits_imposes` : contraintes de l'hypothèse et sort des acteurs du récit (disparaît, change, reste) ; l'injection les donne à l'IA comme faits non négociables.

```yaml
- id: reamenagement_quai_wilson_2044
  description: Ce matin, devant les portes vitrées du Centre Régénératif du Léman, une file d’attente
    silencieuse s’étire jusqu’au quai Wilson, réaménagé après la montée des eaux de 2044.
  portee: globale
  date_approximative: 2044
  intensite: <à choisir>
  persistance: durable
  scenarios:
  - new_sustainability
  variables_hint:
  - climat_environnement_global
  - organisation_territoires
  - gouvernance_institutions
  - geopolitique_conflits
  - sante_biotechnologies
  - demographie_mobilite_humaine
  variables_hint_count: 6
  source: et_si_reamenagement_quai_wilson_2044
  faits_imposes:
    new_sustainability:
    - fait: Ce matin, devant les portes vitrées du Centre Régénératif du Léman, une file d’attente silencieuse
        s’étire jusqu’au quai Wilson, réaménagé après la montée des eaux de 2044.
      sort: contrainte
    - fait: Montée des eaux en 2044
      sort: contrainte
    - fait: Réaménagement du quai Wilson après les inondations
      sort: contrainte
    - fait: 'Lieu : centre_institutionnel_geneve'
      sort: contrainte
  date_imposee: 2044.01
  impacts_imposes:
    new_sustainability:
    - variable: climat_environnement_global
      delta_level: 20
      duree: 3
      polarite: 1
    - variable: organisation_territoires
      delta_level: 15
      duree: 5
      polarite: -1
    - variable: gouvernance_institutions
      delta_level: 10
      duree: 4
      polarite: -1
    - variable: geopolitique_conflits
      delta_level: 5
      duree: 3
      polarite: -1
    - variable: sante_biotechnologies
      delta_level: 10
      duree: 5
      polarite: -1
    - variable: demographie_mobilite_humaine
      delta_level: 12
      duree: 4
      polarite: 1
  via_matrice_impose: true
```

