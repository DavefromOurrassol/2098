# Et si ? — Réintégration de l'Écosse au Royaume-Uni

*Simulation du 2026-10-19 19:27 — lecture seule, rien n'a été injecté (simulateur v8.23).*

En 2070, après l'échec du corridor nordique, l'Écosse renonce à son indépendance et réintègre le Royaume-Uni. Les institutions écossaises sont dissoutes ou absorbées par celles de l'Europe occidentale reconstruite.

**Faits imposés à la lecture IA** :
- À partir de 2070, l'Écosse fait de nouveau partie du Royaume-Uni ; elle n'a plus de gouvernement indépendant.

- **Apparition** : 2070 · **Persistance** : durable · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098
- Déclaré : **gouvernance_institutions** — force 6, aggrave ↑, montée sur 5 ans
- Déclaré : **frontieres_du_systeme** — force 5, apaise ↓, montée sur 5 ans

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## reference

Apparu en 2070 dans le scénario reference, Réintégration de l'Écosse au Royaume-Uni agit d'abord sur frontières du système et gouvernance institutions. Son effet le plus fort apaise frontières du système, avec un écart maximal de -1,1 points vers 2091. En 2098, il en subsiste -0,9 points sur frontières du système.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| frontieres_du_systeme | 55,0 | 62,8 | 61,8 | **-1,0** | direct |
| gouvernance_institutions | 40,0 | 53,9 | 54,0 | **+0,1** | direct |
| valeurs_culture_tempo_sociale | 60,0 | 69,3 | 69,4 | **+0,1** | propagé |
| sante_biotechnologies | 55,0 | 51,0 | 51,1 | **+0,1** | propagé |

**Repères** :
- frontieres_du_systeme (direct) : pic -1,1 vers 2091

**Tensions** : 42 sans l'hypothèse → 42 avec.

### Carte (aperçu, rien n'est modifié)

**Écosse** rattaché à `europe_occidentale_reconstruite`
- Aujourd'hui : `ecosse_nordique_independante`
- Zone quittée `ecosse_nordique_independante` : n'aurait **plus aucun territoire** ; ses journaux (journaux.yaml) resteraient sans territoire
- Aucune fiche, sous-zone ou ligne du registre touchée.
- Autres instances des zones concernées, sans lien avec Écosse : 21 (non listées)

### Liste d'application (à valider à la main — rien n'est écrit)

**Carte**
- [ ] 1. Rattacher Écosse à `europe_occidentale_reconstruite`
  - ④ « Appliquer » le fait
  - _le pays change de mains_
- [ ] 2. `ecosse_nordique_independante` n'a plus aucun territoire : la garder (vestige, exil) ou la supprimer
  - Carte → ✏️ éditer → Zone dangereuse (refusé tant qu'elle a des sous-zones)
  - _zone quittée par Écosse_

**Journaux**
- [ ] 3. *The Northern Caledonian* (pro_pouvoir, `ecosse_nordique_independante`) n'a plus de territoire (vidée par la carte)
  - à la main : le garder (journal en exil) ou le retirer de journaux.yaml (load_journaux / save_journaux, comme le 6 oct)
  - _aucun outil de migration des journaux_
- [ ] 4. *Fo Thuinn Alba* (opposition, `ecosse_nordique_independante`) n'a plus de territoire (vidée par la carte)
  - à la main : le garder (journal en exil) ou le retirer de journaux.yaml (load_journaux / save_journaux, comme le 6 oct)
  - _aucun outil de migration des journaux_

**Élément**
- [ ] 5. Injecter l'événement `reunification_ecosse_2070` (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios de l'hypothèse_
- [ ] 6. Vérifier que la fiche porte les forces simulées (gouvernance_institutions +6, frontieres_du_systeme −5)
  - event_instances/reunification_ecosse_2070_reference.md, bloc impact_sur_variables ; python3 generator/trace_injection.py --slug reunification_ecosse_2070 --type evenement --scenario reference
  - _imposées par l'entrée commune (impacts_imposes, date_imposee) : l'effet doit correspondre à cette simulation_

**Lore**
- [ ] 7. Règles à ajouter pour que l'audit du lore surveille : zone `ecosse_nordique_independante`, faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section reference
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 8. Termes cherchés : Aberdeen, Dundee, Edinburgh, Glasgow, Inverness, Écosse, Édimbourg
  - _mot entier, sans casse ni accents ; le registre seulement après 2070 (chronologie)_
- [ ] 9. Zone `ecosse_nordique_independante` cite « Écosse »
  - _Écosse Nordique Indépendante…_

**Articles et site**
- [ ] 10. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario reference`
  - _payant, un appel_
- [ ] 11. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 12. Base
  - `python3 generator/validate.py`
- [ ] 13. Géographie
  - `python3 generator/scan_geographie_complet.py --scenario reference`
- [ ] 14. Lore
  - `python3 generator/audit_lore.py --scenario reference`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

## Liste d'application — injection commune

Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). Forces, polarités, durées, date et propagation de cette simulation sont imposées (`impacts_imposes`, `date_imposee`, `via_matrice_impose`) : l'IA de l'injection ne les recalcule pas, elle rédige seulement le récit.

`faits_imposes` : contraintes de l'hypothèse et sort des acteurs du récit (disparaît, change, reste) ; l'injection les donne à l'IA comme faits non négociables.

```yaml
- id: reunification_ecosse_2070
  description: En 2070, après l'échec du corridor nordique, l'Écosse renonce à son indépendance et réintègre
    le Royaume-Uni. Les institutions écossaises sont dissoutes ou absorbées par celles de l'Europe occidentale
    reconstruite.
  portee: <locale | regionale | continentale | globale>
  date_approximative: 2070
  intensite: <à choisir>
  persistance: durable
  scenarios:
  - reference
  variables_hint:
  - gouvernance_institutions
  - frontieres_du_systeme
  variables_hint_count: 2
  source: et_si_reunification_ecosse_2070
  faits_imposes:
    reference:
    - fait: À partir de 2070, l'Écosse fait de nouveau partie du Royaume-Uni ; elle n'a plus de gouvernement
        indépendant.
      sort: contrainte
  date_imposee: 2070
  impacts_imposes:
    reference:
    - variable: gouvernance_institutions
      delta_level: 6
      duree: 5
      polarite: 1
    - variable: frontieres_du_systeme
      delta_level: 5
      duree: 5
      polarite: -1
  via_matrice_impose: true
```

