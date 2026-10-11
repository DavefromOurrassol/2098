# Et si ? — Invasion du Brésil par les États-Unis

*Simulation du 2026-10-11 08:32 — lecture seule, rien n'a été injecté (simulateur v8.15).*

En 2029, les États-Unis envahissent le Brésil (portée continentale, intensité majeure). Conflit durable, déplacements de population, pression sur l'Amazonie, rupture des échanges régionaux.

- **Apparition** : 2029 · **Persistance** : durable · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098
- Déclaré : **geopolitique_conflits** — force 20, aggrave ↑, montée sur 5 ans
- Déclaré : **frontieres_du_systeme** — force 12, aggrave ↑, montée sur 5 ans
- Déclaré : **demographie_mobilite_humaine** — force 10, aggrave ↑, montée sur 8 ans
- Déclaré : **gouvernance_institutions** — force 10, aggrave ↑, montée sur 8 ans
- Déclaré : **climat_environnement_global** — force 8, aggrave ↑, montée sur 10 ans
- Déclaré : **systeme_economique_redistribution** — force 8, aggrave ↑, montée sur 8 ans

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## fortress_world

Apparu en 2029 dans le scénario fortress_world, Invasion du Brésil par les États-Unis agit d'abord sur géopolitique conflits, frontières du système, système économique redistribution, gouvernance institutions, démographie mobilité humaine et 1 autre. Son effet le plus fort aggrave géopolitique conflits, avec un écart maximal de +4,6 points vers 2044. Par propagation, technologie information réagit à son tour environ 14 ans après l'apparition (+0,7 points au plus fort). En 2098, il en subsiste +0,1 points sur géopolitique conflits.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| systeme_economique_redistribution | 60,0 | 62,8 | 64,0 | **+1,2** | direct |
| frontieres_du_systeme | 70,0 | 79,0 | 80,0 | **+1,0** | direct |
| climat_environnement_global | 75,0 | 83,3 | 84,1 | **+0,8** | direct |
| demographie_mobilite_humaine | 75,0 | 86,9 | 87,4 | **+0,5** | direct |
| sante_biotechnologies | 65,0 | 68,2 | 68,6 | **+0,4** | propagé |
| energie_ressources_critiques | 82,0 | 91,2 | 91,6 | **+0,4** | propagé |
| systemes_productifs_travail | 85,0 | 96,1 | 96,4 | **+0,3** | propagé |
| valeurs_culture_tempo_sociale | 80,0 | 90,5 | 90,7 | **+0,2** | propagé |
| technologie_information | 85,0 | 97,4 | 97,6 | **+0,2** | propagé |
| gouvernance_institutions | 50,0 | 64,6 | 64,7 | **+0,1** | direct |
| geopolitique_conflits | 85,0 | 99,7 | 99,8 | **+0,1** | direct |
| organisation_territoires | 80,0 | 92,8 | 92,9 | **+0,1** | propagé |

**Repères** :
- geopolitique_conflits (direct) : pic +4,6 vers 2044
- frontieres_du_systeme (direct) : pic +3,5 vers 2051
- systeme_economique_redistribution (direct) : pic +2,2 vers 2049
- gouvernance_institutions (direct) : pic +2,1 vers 2044

**Tensions** : 42 sans l'hypothèse → 42 avec.

### Liste d'application (à valider à la main — rien n'est écrit)

**Élément**
- [ ] 1. Injecter l'événement `invasion_bresil_2029` (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios de l'hypothèse_
- [ ] 2. Vérifier que la fiche porte les forces simulées (geopolitique_conflits +20, frontieres_du_systeme +12, demographie_mobilite_humaine +10, gouvernance_institutions +10, climat_environnement_global +8, systeme_economique_redistribution +8)
  - event_instances/invasion_bresil_2029_fortress_world.md, bloc impact_sur_variables ; python3 generator/trace_injection.py --slug invasion_bresil_2029 --type evenement --scenario fortress_world
  - _imposées par l'entrée commune (impacts_imposes, date_imposee) : l'effet doit correspondre à cette simulation_
- [ ] 3. Gros choc : vérifier la lisibilité du moteur
  - `python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05`
  - _S19_

**Fiches à relire**
- [ ] 4. Termes cherchés : Amazonie, Brésil, États-Unis
  - _mot entier, sans casse ni accents ; le registre seulement après 2029 (chronologie)_
- [ ] 5. Instance `amazonie_pacte_vert_fortress_world` cite « Amazonie »
  - _Manaus-Forteresse, Amazonie…_
- [ ] 6. Instance `consortium_amazonia_viva_fortress_world` cite « Amazonie »
  - _Amazonie — Territoire du Pacte Vert…_
- [ ] 7. Instance `terrashield_geoengineering_fortress_world` cite « Amazonie »
  - _…es des blocs souverains. On les accuse d’avoir transformé l’Amazonie en laboratoire à ciel ouvert, où des forêts entières sont gérées comme des acti…_
- [ ] 8. Événement `crise_gouvernance_amazonie_fortress_world` cite « Amazonie »
  - _Belém : l'Amazonie bascule, les milices prennent le bassin…_
- [ ] 9. Zone `amazonie_pacte_vert` cite « Amazonie »
  - _Amazonie — Territoire du Pacte Vert…_
- [ ] 10. Zone `bloc_atlantique` cite « États-Unis »
  - _États-Unis ; Canada ; Mexique ; Monaco ; Saint-Marin ; Vatican ; Malte ; Cuba ; République…_
- [ ] 11. Zone `sao_paulo_megapole` cite « Brésil »
  - _São Paulo ; Brésil…_
- [ ] 12. Registre (après la date) `evenement | 2047 | crise_gouvernance_amazonie` cite « Amazonie »
  - _| evenement | 2047 | crise_gouvernance_amazonie | climat_environnement_global, geopolitique_conflits, gouvernance_institutions,…_
- [ ] 13. Relecture IA ciblée d'une instance (contradictions avec l'hypothèse)
  - `python3 generator/audit_lore.py --scenario fortress_world --llm --slug <slug>`
  - _payant (≈ 0,5 centime la fiche) ; après application de la carte et de l'événement_

**Articles et site**
- [ ] 14. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario fortress_world`
  - _payant, un appel_
- [ ] 15. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 16. Base
  - `python3 generator/validate.py`
- [ ] 17. Lore
  - `python3 generator/audit_lore.py --scenario fortress_world`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

## Liste d'application — injection commune

⚠ Simulation limitée à fortress_world : l'entrée couvre aussi breakdown, new_sustainability, eco_communalism, policy_reform, reference, non simulé(s) dans ce rapport ; les simuler avant d'injecter, ou les retirer de `scenarios` et de `impacts_imposes`.

Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). Forces, polarités, durées, date et propagation de cette simulation sont imposées (`impacts_imposes`, `date_imposee`, `via_matrice_impose`) : l'IA de l'injection ne les recalcule pas, elle rédige seulement le récit.

```yaml
- id: invasion_bresil_2029
  description: En 2029, les États-Unis envahissent le Brésil (portée continentale, intensité majeure).
    Conflit durable, déplacements de population, pression sur l'Amazonie, rupture des échanges régionaux.
  portee: globale
  date_approximative: 2029
  intensite: <à choisir>
  persistance: durable
  scenarios:
  - breakdown
  - fortress_world
  - new_sustainability
  - eco_communalism
  - policy_reform
  - reference
  variables_hint:
  - geopolitique_conflits
  - frontieres_du_systeme
  - demographie_mobilite_humaine
  - gouvernance_institutions
  - climat_environnement_global
  - systeme_economique_redistribution
  variables_hint_count: 6
  source: et_si_invasion_bresil_2029
  date_imposee: 2029
  impacts_imposes:
    breakdown:
    - variable: geopolitique_conflits
      delta_level: 20
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: demographie_mobilite_humaine
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 8
      duree: 10
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 8
      duree: 8
      polarite: 1
    fortress_world:
    - variable: geopolitique_conflits
      delta_level: 20
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: demographie_mobilite_humaine
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 8
      duree: 10
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 8
      duree: 8
      polarite: 1
    new_sustainability:
    - variable: geopolitique_conflits
      delta_level: 20
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: demographie_mobilite_humaine
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 8
      duree: 10
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 8
      duree: 8
      polarite: 1
    eco_communalism:
    - variable: geopolitique_conflits
      delta_level: 20
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: demographie_mobilite_humaine
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 8
      duree: 10
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 8
      duree: 8
      polarite: 1
    policy_reform:
    - variable: geopolitique_conflits
      delta_level: 20
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: demographie_mobilite_humaine
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 8
      duree: 10
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 8
      duree: 8
      polarite: 1
    reference:
    - variable: geopolitique_conflits
      delta_level: 20
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 12
      duree: 5
      polarite: 1
    - variable: demographie_mobilite_humaine
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: gouvernance_institutions
      delta_level: 10
      duree: 8
      polarite: 1
    - variable: climat_environnement_global
      delta_level: 8
      duree: 10
      polarite: 1
    - variable: systeme_economique_redistribution
      delta_level: 8
      duree: 8
      polarite: 1
  via_matrice_impose: true
```

