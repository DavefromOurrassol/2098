# Et si ? — Réintégration de l'Écosse au Royaume-Uni

*Simulation du 2026-10-19 18:54 — lecture seule, rien n'a été injecté (simulateur v8.22).*

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
- [ ] 8. Termes cherchés : Birmingham, Europe, Glasgow, Leeds, Liverpool, London, Londres, Manchester, Newcastle, Royaume-Uni, Sheffield, Écosse
  - _mot entier, sans casse ni accents ; le registre seulement après 2070 (chronologie)_
- [ ] 9. Instance `armada_logistique_nordique_reference` cite « Europe »
  - _…s chroniques. Elle administre les routes de transit entre l'Europe, l'Asie et l'Amérique du Nord avec une autorité quasi-souveraine, négociant ses…_
- [ ] 10. Instance `bloc_ressources_eurasiatique_bre_reference` cite « Europe »
  - _…ité à maintenir — ou rompre — les flux de ressources vers l'Europe occidentale, l'Indo-Pacifique et les Amériques en fait un acteur incontournable…_
- [ ] 11. Instance `cartel_des_terres_rares_d_asie_centrale_reference` cite « Europe »
  - _…t entre le Bloc Eurasien Central, l'Arc Indo-Pacifique et l'Europe Occidentale Reconstruite, capables de faire monter ou baisser la tension géopol…_
- [ ] 12. Instance `collectifs_de_journalistes_independants_regionaux_reference` cite « Europe »
  - _…illés en plusieurs centaines de nœuds autonomes à travers l'Europe Reconstruite, le Sahel et les Amériques fragmentées, les Collectifs de Journali…_
- [ ] 13. Instance `conseil_des_etats_nordiques_integres_reference` cite « Europe »
  - _…e Helsinki et Nuuk symbolise l'équilibre revendiqué entre l'Europe reconstruite et l'Arctique émergent.…_
- [ ] 14. Instance `consortium_des_grandes_plateformes_ia_integrees_reference` cite « Europe »
  - _…le Bloc Eurasien Central, transparence algorithmique pour l'Europe Occidentale Reconstruite, accès libre pour les Zones Grises. Sa tension fondame…_
- [ ] 15. Instance `consortium_energetique_des_mers_du_nord_reference` cite « Europe »
  - _…neté. Il pèse directement sur les rapports de force entre l'Europe occidentale reconstruite, le Corridor Arctique Nordique et le Bloc Eurasien Cen…_
- [ ] 16. Instance `consortiums_d_extraction_miniere_du_bassin_congolais_reference` cite « Europe »
  - _…ustriels consommateurs, notamment l'Arc Indo-Pacifique et l'Europe Occidentale Reconstruite.…_
- [ ] 17. Instance `consortiums_prives_d_extraction_de_ressources_critiques_reference` cite « Europe »
  - _…cité à opérer simultanément dans des zones de droit dense — Europe reconstruite, Arc Indo-Pacifique — et dans des territoires de non-droit — Sahel…_
- [ ] 18. Instance `cooperative_terrafond_reference` cite « Europe »
  - _Europe Occidentale (47 bassins, des plaines ibériques au Massif Central en passant par…_
- [ ] 19. Instance `cooperatives_agro_ecologiques_de_reconstruction_territoriale_reference` cite « Europe »
  - _…les institutions de gouvernance territoriale — notamment en Europe occidentale reconstruite et en Afrique sahélienne — et confrontation avec les p…_
- [ ] 20. Instance `cooperatives_energetiques_decentralisees_reference` cite « Europe »
  - _…nt aujourd'hui plusieurs centaines de structures actives en Europe occidentale reconstruite, dans les Amériques multipolaires et dans l'arc africa…_
- [ ] 21. Instance `cooperatives_ia_open_source_reference` cite « Europe »
  - _…s, équipent aujourd'hui plusieurs gouvernements régionaux d'Europe du Nord et d'Afrique subsaharienne qui ont renoncé à négocier des licences avec…_
- [ ] 22. Instance `corridor_arctique_nordique_reference` cite « Europe »
  - _…es, de ressources critiques et de données physiques entre l'Europe nordique et les territoires sibériens en cours d'exploitation. Gérer les droits…_
- [ ] 23. Instance `europe_occidentale_reconstruite_reference` cite « Europe »
  - _…Européenne, l'UOC fédère de manière lâche plusieurs États d'Europe de l'Ouest autour de normes commerciales et sécuritaires minimales. Elle ne pré…_
- [ ] 24. Instance `fonds_monetaire_climatique_fmc_reference` cite « Europe »
  - _…bailleurs dominants, les blocs du Corridor Arctique et de l'Europe Occidentale, qui orientent les allocations selon leurs intérêts géopolitiques e…_
- [ ] 25. Instance `gelecek_meclisi_reference` cite « Europe »
  - _…ur' en turc, langue choisie pour son statut de pont entre l'Europe et l'Asie) est devenu en 2098 l'un des rares espaces où mégapoles autonomes, Ét…_
- [ ] 26. Instance `kaspar_lind_reference` cite « Europe »
  - _Recruteur clandestin pour le réseau Kindling en Europe Occidentale Reconstruite, Kaspar Lind opère dans l'ombre des administrations hy…_
- [ ] 27. Instance `kindling_reference` cite « Europe »
  - _Cellules accélérationnistes clandestines opérant en Europe Occidentale Reconstruite (UOC), où les institutions démocratiques résistent enc…_
- [ ] 28. Instance `lobbies_agro_industriels_a_haute_consommation_d_eau_reference` cite « Europe »
  - _…s façades de prospérité alimentaire des plaines irriguées d'Europe du Sud et des Amériques, les lobbies agro-industriels hydrovores tirent les fic…_
- [ ] 29. Instance `maelys_okonkwo_reference` cite « Europe »
  - _…nkwo, figure emblématique du journalisme d'investigation en Europe Occidentale Reconstruite, est devenue une voix incontournable dans l'exposition…_
- [ ] 30. Instance `plateformes_informationnelles_dominantes_et_leurs_ia_de_moderation_reference` cite « Europe »
  - _…le Pacte des Souverains exigeant des versions localisées, l'Europe Occidentale Reconstruite imposant des audits partiels —, elles naviguent entre…_
- [ ] 31. Instance `reseau_des_administrations_locales_rurales_participatives_reference` cite « Europe »
  - _…patives s'est imposé comme la voix des marges oubliées de l'Europe Occidentale Reconstruite — ces communes où l'État n'arrive plus qu'en signal nu…_
- [ ] 32. Instance `syndicats_de_travail_rural_hybride_reference` cite « Europe »
  - _…l, est lu par plus de 40 millions de travailleurs ruraux en Europe occidentale reconstruite.…_
- [ ] 33. Événement `effondrement_circulation_atlantique_2067_reference` cite « Londres »
  - _…les températures chutent en Europe du Nord-Ouest, plongeant Londres, Amsterdam et Copenhague dans un hiver permanent. Les ports de la côte est amér…_
- [ ] 34. Zone `ecosse_nordique_independante` cite « Écosse »
  - _Écosse Nordique Indépendante…_
- [ ] 35. Zone `europe_occidentale_reconstruite` cite « Europe »
  - _Europe Occidentale Reconstruite…_
- [ ] 36. Zone `iberie_atlantique_fragmentee` cite « Europe »
  - _…és lisboètes, favorables à une intégration renforcée avec l'Europe Occidentale Reconstruée, et les régions intérieures, où des mouvements autonomi…_
- [ ] 37. Zone `turquie_eurasie_moyen_orient` cite « Europe »
  - _…détroits stratégiques et les corridors énergétiques entre l'Europe et l'Asie. Centre de transit pour les flux de données et d'énergie.…_
- [ ] 38. Zone `istanbul` cite « Europe »
  - _…ux et territoires autonomes. Son statut de ville-pont entre Europe et Asie en fait un symbole de la fragmentation géopolitique, mais aussi un hub…_
- [ ] 39. Zone `lyon_metropole` cite « Europe »
  - _Ville française ordinaire de l'Europe Occidentale Reconstruite, lieu de l'arrestation de Chris van Derburgh en juin 2…_
- [ ] 40. Zone `zones_tampons_climatiques_europeennes` cite « Europe »
  - _Espaces de transition écologique aux marges de l'Europe Occidentale Reconstruite, gérés partiellement par le Réseau Terrafond et invest…_
- [ ] 41. Relecture IA ciblée d'une instance (contradictions avec l'hypothèse)
  - `python3 generator/audit_lore.py --scenario reference --llm --slug <slug>`
  - _payant (≈ 0,5 centime la fiche) ; après application de la carte et de l'événement_

**Articles et site**
- [ ] 42. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario reference`
  - _payant, un appel_
- [ ] 43. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 44. Base
  - `python3 generator/validate.py`
- [ ] 45. Géographie
  - `python3 generator/scan_geographie_complet.py --scenario reference`
- [ ] 46. Lore
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

