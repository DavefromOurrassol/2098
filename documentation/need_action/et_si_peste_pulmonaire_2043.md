# Et si ? — Pandémie de peste pulmonaire

*Simulation du 2026-10-10 20:30 — lecture seule, rien n'a été injecté (simulateur v8.12).*

En 2043, une souche de peste pulmonaire résistante aux antibiotiques se diffuse sur tous les continents et tue un quart de la population mondiale en trois ans. Villes désertées, chaînes de production rompues, frontières fermées, effondrement des systèmes de santé, puis lente recomposition.

**Faits imposés à la lecture IA** :
- La pandémie tue environ 25 % de la population mondiale entre 2043 et 2046, sur tous les continents, plus fortement dans les villes denses.
- Aucun traitement efficace avant le début des années 2050 ; la maladie devient ensuite endémique et contrôlée.
- La population mondiale ne retrouve pas son niveau de 2042 avant la fin du siècle.

- **Apparition** : 2043 · **Persistance** : — (mode **rupture** : l'équilibre du scénario est déplacé pour de bon) · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098
- **Carte** : élément déclaré sans effet territorial (`carte: non`), aucune proposition de carte retenue
- Déclaré : **demographie_mobilite_humaine** — force 25, aggrave ↑, montée sur 3 ans
- Déclaré : **sante_biotechnologies** — force 25, aggrave ↑, montée sur 3 ans
- Déclaré : **systemes_productifs_travail** — force 18, aggrave ↑, montée sur 4 ans
- Déclaré : **systeme_economique_redistribution** — force 15, aggrave ↑, montée sur 5 ans
- Déclaré : **frontieres_du_systeme** — force 15, aggrave ↑, montée sur 3 ans
- Déclaré : **gouvernance_institutions** — force 12, aggrave ↑, montée sur 5 ans
- Déclaré : **organisation_territoires** — force 10, aggrave ↑, montée sur 6 ans
- Déclaré : **climat_environnement_global** — force 5, apaise ↓, montée sur 10 ans
- ⚠ `persistance` sans objet en mode rupture (le déplacement est permanent) : ignorée

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## breakdown

Apparu en 2043 dans le scénario breakdown, Pandémie de peste pulmonaire agit d'abord sur santé biotechnologies, frontières du système, gouvernance institutions, démographie mobilité humaine, organisation territoires et 3 autres. Son effet le plus fort aggrave santé biotechnologies, avec un écart maximal de +13,5 points vers 2046. Par propagation, technologie information réagit à son tour environ 8 ans après l'apparition (+0,6 points au plus fort). En 2098, il en subsiste +10,7 points sur santé biotechnologies.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| sante_biotechnologies | 85,0 → 99,0 | 89,3 | 100,0 | **+10,7** | direct |
| frontieres_du_systeme | 85,0 → 96,4 | 91,4 | 100,0 | **+8,6** | direct |
| gouvernance_institutions | 80,0 → 90,7 | 93,2 | 99,9 | **+6,7** | direct |
| demographie_mobilite_humaine | 90,0 → 99,9 | 96,6 | 100,0 | **+3,4** | direct |
| valeurs_culture_tempo_sociale | 90,0 | 95,4 | 97,5 | **+2,1** | propagé |
| climat_environnement_global | 95,0 → 90,0 | 99,6 | 98,0 | **-1,6** | direct |
| organisation_territoires | 90,0 → 97,6 | 98,6 | 100,0 | **+1,4** | direct |
| systeme_economique_redistribution | 95,0 → 100,0 | 99,3 | 100,0 | **+0,7** | direct |
| energie_ressources_critiques | 96,0 | 99,3 | 99,9 | **+0,6** | propagé |
| systemes_productifs_travail | 95,0 → 100,0 | 99,4 | 100,0 | **+0,6** | direct |

**Repères** :
- sante_biotechnologies (direct) : pic +13,5 vers 2046
- frontieres_du_systeme (direct) : pic +12,3 vers 2066
- gouvernance_institutions (direct) : pic +10,5 vers 2048
- demographie_mobilite_humaine (direct) : pic +8,5 vers 2045

**Tensions** : 42 sans l'hypothèse → 42 avec.

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

_(résultat repris du cache : même hypothèse, mêmes effets — `--refaire` pour relancer)_

La pandémie de peste pulmonaire résistante (2043-2046) accélère brutalement la fragmentation du monde Ourrassol en ciblant les nœuds urbains denses et les infrastructures logistiques déjà fragilisées. Elle ne crée pas de nouveaux territoires inhabitables, mais elle renforce les dynamiques de repli régional, de privatisation des services et de contestation des autorités centrales. Les zones les plus résilientes (Arctique Nordark, Asie-Pacifique) limitent les dégâts grâce à leur faible densité, tandis que les régions fragmentées (Afrique de l'Ouest, Méditerranée) basculent dans des logiques de survie locale. Le choc sanitaire ne modifie pas la géographie politique, mais il cristallise des rapports de force préexistants. _(ampleur : forte)_

**Trajectoires d'entités**
- Ligue Méditerranéenne des Villes-États Portuaires (`ligue_mediterraneenne_des_villes_etats_portuaires_breakdown`) : émergent → **ascendant** — Les villes portuaires méditerranéennes deviennent des refuges logistiques et sanitaires, capitalisant sur leur capacité à contrôler les flux malgré l'effondrement des États centraux.
- Bloc de Johannesburg (`bloc_de_johannesburg_breakdown`) : émergent → **ascendant** — L'Afrique australe, moins touchée par la pandémie grâce à sa démographie dispersée, voit Johannesburg émerger comme un pôle de stabilité relative, attirant des flux de réfugiés et de capitaux.
- Conglométrat sino-sibérien Bohai Transit (`conglometrat_sino_siberien_bohai_transit_breakdown`) : émergent → **dominant** — Les corridors sino-sibériens deviennent incontournables pour les échanges eurasiatiques, la Chine et la Russie profitant du vide logistique pour imposer leur contrôle.
- Ligue Hanséatique Baltique — Le Sceau du Gotland (`hanse_baltique_breakdown`) : ascendant → **mature** — La Ligue Hanséatique Baltique consolide son rôle de médiateur commercial en Europe du Nord, où la pandémie a affaibli les États sans remettre en cause ses réseaux.
- Administration Résiduelle de Mourmansk — Le Bastion du Détroit Gelé (`district_mourmansk_residuel_breakdown`) : résiduel → **disparu** — L'effondrement démographique et logistique de Mourmansk rend toute administration résiduelle obsolète, le territoire étant absorbé par les factions arctiques.

**Relations**
- opposition nouvelle : Ligue Méditerranéenne des Villes-États Portuaires ↔ Carthage Nord Nexcore — Le Joug du Détroit — La Ligue conteste le contrôle milicien de Carthage-Nord sur les flux méditerranéens, exacerbé par la pandémie qui a polarisé les accès aux ressources.
- opposition nouvelle : Compact des Grands Lacs — Le Mur d'Eau ↔ États-Fragments en Guerre pour les Stations Atmosphériques — Le Compact des Grands Lacs entre en conflit avec les États-Fragments pour le contrôle des stations de filtration d'air, devenues vitales après la pandémie.
- alliance nouvelle : Kalaallit Nunaat Sovereign Fund — Fonds des Glaces Libérées ↔ Factions Militaires Résiduelles de l'Ex-OTAN Nordique — Le Fonds des Glaces Libérées s'allie aux factions OTAN résiduelles pour sécuriser les corridors arctiques contre les milices locales, dans un contexte de pénurie post-pandémique.
- opposition nouvelle : Bloc de Johannesburg ↔ Milices Extractivistes du Bassin du Congo — Johannesburg tente de reprendre le contrôle des ressources du Kivu, accaparées par les milices après l'effondrement des États centraux africains.
- alliance rompue : Conglométrat sino-sibérien Bohai Transit ↔ Les Venelles — Corridors Eurasiens Convoyage — La Chine et la Russie imposent un monopole sur les corridors eurasiatiques, marginalisant les convoyeurs indépendants après la pandémie.
- opposition nouvelle : Enclaves Corporatives Fortifiées ↔ Flux Migratoires Non Intégrables — Les enclaves corporatives africaines renforcent leurs barrières contre les flux migratoires, devenus ingérables après la pandémie.

**Statut des zones**
- Afrique de l'Ouest – Nœuds Lagos et Sahel (`afrique_de_louest_lagos_sahel`) : fragmenté → **en_declin** — La pandémie décime les populations urbaines (Lagos, Sahel) et accélère l'effondrement des structures étatiques, déjà fragilisées.
- Espace Nord-Américain Fragmenté (`espace_nord_americain_fragmente`) : fragmenté → **en_declin** — Les États-Unis et le Canada subissent un effondrement démographique et institutionnel, les zones côtières résiduelles ne suffisant pas à maintenir une cohérence territoriale.

**Nouvelles entités plausibles**
- Culte des Souffles Purs (arc_sahelo_mediterraneen) : Communauté religieuse sanitaire — Né dans les ruines des villes méditerranéennes, ce culte prône la purification par l'isolement et contrôle des relais de soins post-pandémiques.
- Guilde des Convoyeurs Sanitaires (corridors_eurasiens_convoyage) : Milice logistique spécialisée — Les derniers convoyeurs eurasiatiques se structurent en guilde armée pour protéger les flux de médicaments et de nourriture contre les pillards.
- Bloc des Survivants des Grands Lacs (grandes_lacs_compact_eau) : Alliance de communautés riveraines — Les communautés des Grands Lacs s'unissent pour gérer les ressources hydriques et sanitaires, marginalisant les anciennes institutions.

_Propositions écartées au contrôle (5) : trajectoire : grandes_lacs_compact_eau_breakdown déjà dominant (aucun changement) ; trajectoire : kalaallit_nunaat_sovereign_fund_breakdown déjà dominant (aucun changement) ; trajectoire : entité inconnue 'nairobi_crrc' ; statut de zone : arc_sahelo_mediterraneen déjà fragmenté ; statut de zone : geneve_bunker_institutions → disparu écarté, hypothèse sans effet territorial (`carte: non`)_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Statuts de zone**
- [ ] 1. `afrique_de_louest_lagos_sahel` (Afrique de l'Ouest – Nœuds Lagos et Sahel) : fragmenté → en_declin
  - à la main : geographie/breakdown.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario breakdown --execute)
  - _La pandémie décime les populations urbaines (Lagos, Sahel) et accélère l'effondrement des structures étatiques, déjà fragilisées._
- [ ] 2. `espace_nord_americain_fragmente` (Espace Nord-Américain Fragmenté) : fragmenté → en_declin
  - à la main : geographie/breakdown.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario breakdown --execute)
  - _Les États-Unis et le Canada subissent un effondrement démographique et institutionnel, les zones côtières résiduelles ne suffisant pas à maintenir une cohérence territoriale._

**Élément**
- [ ] 3. Mode rupture : décision S19 à prendre avant toute écriture
  - _l'injection réelle ne connaît que le mode choc ; appliquer la rupture = changer la référence_
- [ ] 4. sante_biotechnologies : référence 85,0 → 99,0
  - à la main : variables/sante_biotechnologies.md, states.breakdown.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 5. frontieres_du_systeme : référence 85,0 → 96,4
  - à la main : variables/frontieres_du_systeme.md, states.breakdown.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 6. gouvernance_institutions : référence 80,0 → 90,7
  - à la main : variables/gouvernance_institutions.md, states.breakdown.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 7. demographie_mobilite_humaine : référence 90,0 → 99,9
  - à la main : variables/demographie_mobilite_humaine.md, states.breakdown.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 8. climat_environnement_global : référence 95,0 → 90,0
  - à la main : variables/climat_environnement_global.md, states.breakdown.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 9. organisation_territoires : référence 90,0 → 97,6
  - à la main : variables/organisation_territoires.md, states.breakdown.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 10. systeme_economique_redistribution : référence 95,0 → 100,0
  - à la main : variables/systeme_economique_redistribution.md, states.breakdown.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 11. systemes_productifs_travail : référence 95,0 → 100,0
  - à la main : variables/systemes_productifs_travail.md, states.breakdown.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_

**Nouvelles entités**
- [ ] 12. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie à choisir
  - `python3 generator/create_entities_and_instances.py --mode custom`
  - _la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 13. Ligue Méditerranéenne des Villes-États Portuaires (`ligue_mediterraneenne_des_villes_etats_portuaires_breakdown`) : émergent → ascendant
  - à la main : instances/ligue_mediterraneenne_des_villes_etats_portuaires_breakdown.md, champ `trajectoire`
  - _Les villes portuaires méditerranéennes deviennent des refuges logistiques et sanitaires, capitalisant sur leur capacité à contrôler les flux malgré l'effondrement des États centraux._
- [ ] 14. Bloc de Johannesburg (`bloc_de_johannesburg_breakdown`) : émergent → ascendant
  - à la main : instances/bloc_de_johannesburg_breakdown.md, champ `trajectoire`
  - _L'Afrique australe, moins touchée par la pandémie grâce à sa démographie dispersée, voit Johannesburg émerger comme un pôle de stabilité relative, attirant des flux de réfugiés et de capitaux._
- [ ] 15. ⚠ Conglométrat sino-sibérien Bohai Transit (`conglometrat_sino_siberien_bohai_transit_breakdown`) : émergent → dominant
  - à la main : instances/conglometrat_sino_siberien_bohai_transit_breakdown.md, champ `trajectoire`
  - _saut d'un cran (sans passer par ascendant) : garder, ou ramener à ascendant ; Les corridors sino-sibériens deviennent incontournables pour les échanges eurasiatiques, la Chine et la Russie profitant du vide logistique pour imposer leur contrôle._
- [ ] 16. Ligue Hanséatique Baltique — Le Sceau du Gotland (`hanse_baltique_breakdown`) : ascendant → mature
  - à la main : instances/hanse_baltique_breakdown.md, champ `trajectoire`
  - _La Ligue Hanséatique Baltique consolide son rôle de médiateur commercial en Europe du Nord, où la pandémie a affaibli les États sans remettre en cause ses réseaux._
- [ ] 17. Administration Résiduelle de Mourmansk — Le Bastion du Détroit Gelé (`district_mourmansk_residuel_breakdown`) : résiduel → disparu
  - à la main : instances/district_mourmansk_residuel_breakdown.md, champ `trajectoire` ; puis `annee_fin` (fix_annee_fin_manquant.py)
  - _L'effondrement démographique et logistique de Mourmansk rend toute administration résiduelle obsolète, le territoire étant absorbé par les factions arctiques._

**Relations**
- [ ] 18. opposition nouvelle : Ligue Méditerranéenne des Villes-États Portuaires ↔ Carthage Nord Nexcore — Le Joug du Détroit
  - à la main : ajouter `carthage_nord_nexcore_breakdown` dans `oppositions` de instances/ligue_mediterraneenne_des_villes_etats_portuaires_breakdown.md
  - _La Ligue conteste le contrôle milicien de Carthage-Nord sur les flux méditerranéens, exacerbé par la pandémie qui a polarisé les accès aux ressources._
- [ ] 19. opposition nouvelle : Compact des Grands Lacs — Le Mur d'Eau ↔ États-Fragments en Guerre pour les Stations Atmosphériques
  - à la main : ajouter `etats_fragments_en_guerre_pour_les_stations_atmospheriques_breakdown` dans `oppositions` de instances/grandes_lacs_compact_eau_breakdown.md
  - _Le Compact des Grands Lacs entre en conflit avec les États-Fragments pour le contrôle des stations de filtration d'air, devenues vitales après la pandémie._
- [ ] 20. alliance nouvelle : Kalaallit Nunaat Sovereign Fund — Fonds des Glaces Libérées ↔ Factions Militaires Résiduelles de l'Ex-OTAN Nordique
  - à la main : ajouter `factions_militaires_residuelles_de_l_ex_otan_nordique_breakdown` dans `alliances` de instances/kalaallit_nunaat_sovereign_fund_breakdown.md
  - _Le Fonds des Glaces Libérées s'allie aux factions OTAN résiduelles pour sécuriser les corridors arctiques contre les milices locales, dans un contexte de pénurie post-pandémique._
- [ ] 21. opposition nouvelle : Bloc de Johannesburg ↔ Milices Extractivistes du Bassin du Congo
  - à la main : ajouter `milices_extractivistes_du_bassin_du_congo_breakdown` dans `oppositions` de instances/bloc_de_johannesburg_breakdown.md
  - _Johannesburg tente de reprendre le contrôle des ressources du Kivu, accaparées par les milices après l'effondrement des États centraux africains._
- [ ] 22. alliance rompue : Conglométrat sino-sibérien Bohai Transit ↔ Les Venelles — Corridors Eurasiens Convoyage
  - à la main : retirer de `alliances` dans les DEUX fiches (conglometrat_sino_siberien_bohai_transit_breakdown, corridors_eurasiens_convoyage_breakdown)
  - _la réciprocité n'enlève rien_
- [ ] 23. opposition nouvelle : Enclaves Corporatives Fortifiées ↔ Flux Migratoires Non Intégrables
  - à la main : ajouter `flux_migratoires_non_integrables_breakdown` dans `oppositions` de instances/enclaves_corporatives_fortifiees_breakdown.md
  - _Les enclaves corporatives africaines renforcent leurs barrières contre les flux migratoires, devenus ingérables après la pandémie._
- [ ] 24. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario breakdown --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 25. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section breakdown
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 26. Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche
  - _une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, après l'ajout des faits imposés dans lore_regles.yaml (section Lore)_
- [ ] 27. Estimer la relecture IA des fiches de plus fort impact
  - `python3 generator/audit_lore.py --scenario breakdown --llm --estimer --limit 10`
  - _aucun appel_
- [ ] 28. Relecture IA des 10 fiches de plus fort impact (contradictions avec l'hypothèse)
  - `python3 generator/audit_lore.py --scenario breakdown --llm --limit 10`
  - _payant (≈ 0,5 centime la fiche) ; après application de l'événement_
- [ ] 29. Relecture IA des fiches de la zone `afrique_de_louest_lagos_sahel` (statut changé)
  - `python3 generator/audit_lore.py --scenario breakdown --llm --zone afrique_de_louest_lagos_sahel`
  - _estimer d'abord avec --estimer ; payant_
- [ ] 30. Relecture IA des fiches de la zone `espace_nord_americain_fragmente` (statut changé)
  - `python3 generator/audit_lore.py --scenario breakdown --llm --zone espace_nord_americain_fragmente`
  - _estimer d'abord avec --estimer ; payant_

**Articles et site**
- [ ] 31. 7 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« LYNTH, LIEU ENCOMMANDE »; « LA DETTE AVANCE EN CRÉDITS-CHUTEURS »; « Les Bouches de l’Abîme parlent : le Sahel numérique saigne en silence »; « CONVOIS FANTÔMES : LES COURTIERS DE L'OMBRE DES VENELLES »; « CONVOIS NOCTURNES : GUIDES ET ESCORTES POUR LES VENELLES EURASIENNES »; « « Kharg-9 : Le Dernier Souffle des Archives Mondiales avant l’Abîme » »; « Les Bouches de l’Abîme étouffées : le silence forcé des gardiens du dernier maillage »_
- [ ] 32. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario breakdown`
  - _payant, un appel_
- [ ] 33. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 34. Base
  - `python3 generator/validate.py`
- [ ] 35. Lore
  - `python3 generator/audit_lore.py --scenario breakdown`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Culte des Souffles Purs
  category: <à choisir>
  role: Communauté religieuse sanitaire
  etat: émergent
  scenario_ref: breakdown
  scenario_hint:
  - breakdown
  zone_hint: arc_sahelo_mediterraneen
  source: et_si_peste_pulmonaire_2043
- nom: Guilde des Convoyeurs Sanitaires
  category: <à choisir>
  role: Milice logistique spécialisée
  etat: émergent
  scenario_ref: breakdown
  scenario_hint:
  - breakdown
  zone_hint: corridors_eurasiens_convoyage
  source: et_si_peste_pulmonaire_2043
- nom: Bloc des Survivants des Grands Lacs
  category: <à choisir>
  role: Alliance de communautés riveraines
  etat: émergent
  scenario_ref: breakdown
  scenario_hint:
  - breakdown
  zone_hint: grandes_lacs_compact_eau
  source: et_si_peste_pulmonaire_2043
```

## fortress_world

Apparu en 2043 dans le scénario fortress_world, Pandémie de peste pulmonaire agit d'abord sur santé biotechnologies, démographie mobilité humaine, système économique redistribution, frontières du système, systèmes productifs travail et 3 autres. Son effet le plus fort aggrave santé biotechnologies, avec un écart maximal de +24,3 points vers 2098. Par propagation, technologie information réagit à son tour environ 8 ans après l'apparition (+3,4 points au plus fort). En 2098, il en subsiste +24,3 points sur santé biotechnologies.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| sante_biotechnologies | 65,0 → 86,5 | 68,2 | 92,5 | **+24,3** | direct |
| systeme_economique_redistribution | 60,0 → 74,3 | 62,8 | 81,5 | **+18,7** | direct |
| frontieres_du_systeme | 70,0 → 83,9 | 79,0 | 95,0 | **+16,0** | direct |
| demographie_mobilite_humaine | 75,0 → 94,0 | 86,9 | 100,0 | **+13,1** | direct |
| gouvernance_institutions | 50,0 → 61,8 | 64,6 | 76,6 | **+12,0** | direct |
| organisation_territoires | 80,0 → 89,2 | 92,8 | 99,8 | **+7,0** | direct |
| systemes_productifs_travail | 85,0 → 97,5 | 96,1 | 100,0 | **+3,9** | direct |
| climat_environnement_global | 75,0 → 70,0 | 83,3 | 80,1 | **-3,2** | direct |
| energie_ressources_critiques | 82,0 | 91,2 | 93,4 | **+2,2** | propagé |
| valeurs_culture_tempo_sociale | 80,0 | 90,5 | 92,1 | **+1,6** | propagé |
| technologie_information | 85,0 | 97,4 | 99,0 | **+1,6** | propagé |
| geopolitique_conflits | 85,0 | 99,7 | 99,9 | **+0,2** | propagé |

**Repères** :
- sante_biotechnologies (direct) : pic +24,3 vers 2098
- demographie_mobilite_humaine (direct) : pic +18,9 vers 2046
- systeme_economique_redistribution (direct) : pic +18,8 vers 2076
- frontieres_du_systeme (direct) : pic +17,0 vers 2077

**Tensions** : 42 sans l'hypothèse → 42 avec.

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

_(résultat repris du cache : même hypothèse, mêmes effets — `--refaire` pour relancer)_

La pandémie de peste pulmonaire résistante (2043-2046) accélère brutalement la logique de fragmentation et de fermeture du scénario fortress_world. Elle valide a posteriori les choix d'autonomie stratégique et de contrôle des populations, tout en exacerbant les inégalités entre zones protégées et territoires exposés. Les blocs dominants (bloc_atlantique, bloc_eurasiatique_occidental) renforcent leur emprise, tandis que les zones fragmentées (afrique_subsaharienne_zones_effondrees, golfe_moyen_orient_zone_disputee) sombrent dans un chaos durable. Le choc ne remet pas en cause la trajectoire générale du scénario, mais en radicalise les mécanismes : la santé devient un enjeu de souveraineté absolue, et la mobilité humaine est quasi éradiquée. _(ampleur : bascule)_

**Trajectoires d'entités**
- Cartels Miniers Militarisés Subsahariens (`cartels_miniers_militarises_subsahariens_fortress_world`) : émergent → **résiduel** — L'effondrement démographique et logistique en Afrique subsaharienne réduit leur capacité à négocier avec les forteresses du Nord, les rendant dépendants de l'aide humanitaire conditionnelle.
- Populations des Zones Déficitaires d'Optimisation (`populations_des_zones_deficitaires_d_optimisation_fortress_world`) : émergent → **marginal** — Les populations des zones non protégées sont massivement décimées ou déplacées, réduites à des effectifs résiduels sans capacité de résistance.
- Pacte des Forteresses Souveraines — Charte de Sécurité Intégrale (`pacte_forteresses_souveraines_fortress_world`) : dominant → **disparu** — L'ONU et l'OTAN, héritiers du Pacte, sont discrédités par leur incapacité à coordonner une réponse globale, laissant place à des alliances bilatérales entre forteresses.

**Relations**
- opposition nouvelle : Pacte Atlantique de Préservation Civilisationnelle — PAPC ↔ Forteresse Eurasiatique Occidentale — Pacte de Stabilité Intérieure — La compétition pour les rares stocks de vaccins et de traitements post-2050 exacerbe les tensions, chacun accusant l'autre de manipulation génétique du pathogène.
- alliance nouvelle : Genève Bunker — Forteresse Souveraine Climatique ↔ Bureau des Territoires Résiduels — Division Continentale — Genève-Bunker externalise la gestion des zones contaminées au Bureau des Territoires Résiduels, créant un partenariat public-privé de quarantaine.
- alliance nouvelle : NeuroSentry Sovereign Cognitive Division (NSCD) ↔ Directive Kontinuum — Module Minsk — Les deux entités fusionnent leurs algorithmes de surveillance pour traquer les porteurs asymptomatiques et modéliser les risques de résurgence.

**Nouvelles entités plausibles**
- Brigades Sanitaires de l'Arc Arctique (espace_nordique_arctique) : Unité militaire spécialisée dans la décontamination et la sécurisation des corridors logistiques polaires — La NAT et Ergo-Wian créent une force dédiée pour empêcher toute intrusion de porteurs de pathogènes dans les zones protégées via les routes arctiques.
- Consortium des Forteresses Vitales (geneve_bunker) : Alliance des enclaves biotech pour le partage sécurisé des données épidémiologiques et des traitements — Genève-Bunker fédère les acteurs dominants de la santé (Nexus BioSyn, NeuroSentry) pour éviter une guerre des brevets post-pandémie.
- Réseau des Cimetières Climatiques (zones_grises_tampons) : Infrastructure de crémation et de stockage des déchets biologiques sous contrôle militaire — Les zones tampons deviennent des sites de traitement des cadavres et des déchets médicaux, gérés par des sous-traitants privés sous supervision des blocs.

_Propositions écartées au contrôle (12) : trajectoire : geneve_bunker_fortress_world déjà dominant (aucun changement) ; trajectoire : nexus_biosyn_division_eurasienne_fortress_world déjà dominant (aucun changement) ; trajectoire : nexus_biosyn_division_pacifique_fortress_world déjà dominant (aucun changement) ; trajectoire : bureau_territoires_residuels_fortress_world déjà dominant (aucun changement) ; trajectoire : les_recycleurs_fortress_world dominant → ascendant (recul sur la phase de montée, incohérent) ; relation nexus_biosyn_division_eurasienne_fortress_world / nexus_biosyn_division_pacifique_fortress_world : opposition déjà présente ; relation : entités 'armada_logistique_nordique_fortress_world' / 'corridor_arctique_transit_fortress_world' inconnues ou identiques ; relation : entités 'les_recycleurs_fortress_world' / 'zone_euro_sud_fortress_world' inconnues ou identiques …_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Élément**
- [ ] 1. Mode rupture : décision S19 à prendre avant toute écriture
  - _l'injection réelle ne connaît que le mode choc ; appliquer la rupture = changer la référence_
- [ ] 2. sante_biotechnologies : référence 65,0 → 86,5
  - à la main : variables/sante_biotechnologies.md, states.fortress_world.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 3. systeme_economique_redistribution : référence 60,0 → 74,3
  - à la main : variables/systeme_economique_redistribution.md, states.fortress_world.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 4. frontieres_du_systeme : référence 70,0 → 83,9
  - à la main : variables/frontieres_du_systeme.md, states.fortress_world.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 5. demographie_mobilite_humaine : référence 75,0 → 94,0
  - à la main : variables/demographie_mobilite_humaine.md, states.fortress_world.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 6. gouvernance_institutions : référence 50,0 → 61,8
  - à la main : variables/gouvernance_institutions.md, states.fortress_world.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 7. organisation_territoires : référence 80,0 → 89,2
  - à la main : variables/organisation_territoires.md, states.fortress_world.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 8. systemes_productifs_travail : référence 85,0 → 97,5
  - à la main : variables/systemes_productifs_travail.md, states.fortress_world.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 9. climat_environnement_global : référence 75,0 → 70,0
  - à la main : variables/climat_environnement_global.md, states.fortress_world.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_

**Nouvelles entités**
- [ ] 10. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie à choisir
  - `python3 generator/create_entities_and_instances.py --mode custom`
  - _la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 11. Cartels Miniers Militarisés Subsahariens (`cartels_miniers_militarises_subsahariens_fortress_world`) : émergent → résiduel
  - à la main : instances/cartels_miniers_militarises_subsahariens_fortress_world.md, champ `trajectoire`
  - _L'effondrement démographique et logistique en Afrique subsaharienne réduit leur capacité à négocier avec les forteresses du Nord, les rendant dépendants de l'aide humanitaire conditionnelle._
- [ ] 12. Populations des Zones Déficitaires d'Optimisation (`populations_des_zones_deficitaires_d_optimisation_fortress_world`) : émergent → marginal
  - à la main : instances/populations_des_zones_deficitaires_d_optimisation_fortress_world.md, champ `trajectoire`
  - _Les populations des zones non protégées sont massivement décimées ou déplacées, réduites à des effectifs résiduels sans capacité de résistance._
- [ ] 13. Pacte des Forteresses Souveraines — Charte de Sécurité Intégrale (`pacte_forteresses_souveraines_fortress_world`) : dominant → disparu
  - à la main : instances/pacte_forteresses_souveraines_fortress_world.md, champ `trajectoire` ; puis `annee_fin` (fix_annee_fin_manquant.py)
  - _L'ONU et l'OTAN, héritiers du Pacte, sont discrédités par leur incapacité à coordonner une réponse globale, laissant place à des alliances bilatérales entre forteresses._

**Relations**
- [ ] 14. opposition nouvelle : Pacte Atlantique de Préservation Civilisationnelle — PAPC ↔ Forteresse Eurasiatique Occidentale — Pacte de Stabilité Intérieure
  - à la main : ajouter `bloc_eurasiatique_occidental_fortress_world` dans `oppositions` de instances/bloc_atlantique_fortress_world.md
  - _La compétition pour les rares stocks de vaccins et de traitements post-2050 exacerbe les tensions, chacun accusant l'autre de manipulation génétique du pathogène._
- [ ] 15. alliance nouvelle : Genève Bunker — Forteresse Souveraine Climatique ↔ Bureau des Territoires Résiduels — Division Continentale
  - à la main : ajouter `bureau_territoires_residuels_fortress_world` dans `alliances` de instances/geneve_bunker_fortress_world.md
  - _Genève-Bunker externalise la gestion des zones contaminées au Bureau des Territoires Résiduels, créant un partenariat public-privé de quarantaine._
- [ ] 16. alliance nouvelle : NeuroSentry Sovereign Cognitive Division (NSCD) ↔ Directive Kontinuum — Module Minsk
  - à la main : ajouter `directive_kontinuum_fortress_world` dans `alliances` de instances/neurosentry_fortress_world.md
  - _Les deux entités fusionnent leurs algorithmes de surveillance pour traquer les porteurs asymptomatiques et modéliser les risques de résurgence._
- [ ] 17. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario fortress_world --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 18. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section fortress_world
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 19. Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche
  - _une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, après l'ajout des faits imposés dans lore_regles.yaml (section Lore)_
- [ ] 20. Estimer la relecture IA des fiches de plus fort impact
  - `python3 generator/audit_lore.py --scenario fortress_world --llm --estimer --limit 10`
  - _aucun appel_
- [ ] 21. Relecture IA des 10 fiches de plus fort impact (contradictions avec l'hypothèse)
  - `python3 generator/audit_lore.py --scenario fortress_world --llm --limit 10`
  - _payant (≈ 0,5 centime la fiche) ; après application de l'événement_

**Articles et site**
- [ ] 22. 12 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« Les musées du Mur : quand l’Histoire devient un crime de conformité »; « Le Nœud Mémoriel Eurasiatique "perd" 12 millions de profils : sabotage ou panne systémique ? »; « Les Nœuds Mémoriels craquent sous le poids des archives fantômes »; « NexCore et l’ANBA lancent un protocole de "séparation proactive" des données inter-blocs »; « Kharg-9 : Le Data Haven du Golfe Persique dans le collimateur du Bloc Atlantique »; « NexCore Atlantique : la faille dans le bouclier numérique »; « L’ANBA durcit ses protocoles : les "zones grises" numériques dans le collimateur »; « NexCore et VaultCorp scellent l’alliance des murs numériques »; « Les Archives du Dehors : quand la mémoire devient un acte de résistance »; « LES ARCHIVES INTERDITES : QUAND LE PACTE EFFACE SA PROPRE HISTOIRE » …_
- [ ] 23. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario fortress_world`
  - _payant, un appel_
- [ ] 24. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 25. Base
  - `python3 generator/validate.py`
- [ ] 26. Lore
  - `python3 generator/audit_lore.py --scenario fortress_world`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Brigades Sanitaires de l'Arc Arctique
  category: <à choisir>
  role: Unité militaire spécialisée dans la décontamination et la sécurisation des corridors logistiques
    polaires
  etat: émergent
  scenario_ref: fortress_world
  scenario_hint:
  - fortress_world
  zone_hint: espace_nordique_arctique
  source: et_si_peste_pulmonaire_2043
- nom: Consortium des Forteresses Vitales
  category: <à choisir>
  role: Alliance des enclaves biotech pour le partage sécurisé des données épidémiologiques et des traitements
  etat: émergent
  scenario_ref: fortress_world
  scenario_hint:
  - fortress_world
  zone_hint: geneve_bunker
  source: et_si_peste_pulmonaire_2043
- nom: Réseau des Cimetières Climatiques
  category: <à choisir>
  role: Infrastructure de crémation et de stockage des déchets biologiques sous contrôle militaire
  etat: émergent
  scenario_ref: fortress_world
  scenario_hint:
  - fortress_world
  zone_hint: zones_grises_tampons
  source: et_si_peste_pulmonaire_2043
```

## new_sustainability

Apparu en 2043 dans le scénario new_sustainability, Pandémie de peste pulmonaire agit d'abord sur démographie mobilité humaine, santé biotechnologies, systèmes productifs travail, frontières du système, système économique redistribution et 3 autres. Son effet le plus fort aggrave démographie mobilité humaine, avec un écart maximal de +27,7 points vers 2098. Par propagation, technologie information réagit à son tour environ 9 ans après l'apparition (+6,0 points au plus fort). En 2098, il en subsiste +27,7 points sur démographie mobilité humaine.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| demographie_mobilite_humaine | 45,0 → 68,4 | 42,9 | 70,6 | **+27,7** | direct |
| sante_biotechnologies | 30,0 → 54,0 | 27,8 | 55,0 | **+27,2** | direct |
| systemes_productifs_travail | 50,0 → 67,3 | 45,0 | 67,8 | **+22,8** | direct |
| frontieres_du_systeme | 20,0 → 34,8 | 14,8 | 33,3 | **+18,5** | direct |
| systeme_economique_redistribution | 65,0 → 79,1 | 55,2 | 72,8 | **+17,6** | direct |
| organisation_territoires | 35,0 → 44,9 | 23,5 | 36,1 | **+12,6** | direct |
| gouvernance_institutions | 10,0 → 21,9 | 0,3 | 9,8 | **+9,5** | direct |
| geopolitique_conflits | 30,0 | 26,7 | 33,7 | **+7,0** | propagé |
| technologie_information | 70,0 | 60,0 | 66,0 | **+6,0** | propagé |
| energie_ressources_critiques | 38,0 | 35,1 | 39,4 | **+4,3** | propagé |
| valeurs_culture_tempo_sociale | 55,0 | 51,6 | 55,2 | **+3,6** | propagé |
| climat_environnement_global | 35,0 → 30,0 | 30,4 | 28,1 | **-2,3** | direct |

**Repères** :
- demographie_mobilite_humaine (direct) : pic +27,7 vers 2098
- sante_biotechnologies (direct) : pic +27,2 vers 2098
- systemes_productifs_travail (direct) : pic +22,8 vers 2098
- frontieres_du_systeme (direct) : pic +19,0 vers 2082

**Tensions** : 2 sans l'hypothèse → 13 avec.
- ➕ apparaît : systeme_economique_redistribution (level 72) aggrave une crise déjà forte de systemes_productifs_travail (level 67)
- ➕ apparaît : technologie_information (level 66) aggrave une crise déjà forte de systemes_productifs_travail (level 67)
- ➕ apparaît : systemes_productifs_travail (level 67) aggrave une crise déjà forte de systeme_economique_redistribution (level 72)
- ➕ apparaît : systemes_productifs_travail (level 67) aggrave une crise déjà forte de technologie_information (level 66)
- ➕ apparaît : CASCADE CRITIQUE : systeme_economique_redistribution déclenche une cascade rapide sur energie_ressources_critiques
- ➕ apparaît : systemes_productifs_travail (level 67) en crise atténue la pression sur energie_ressources_critiques (level 39)
- ➕ apparaît : demographie_mobilite_humaine (level 70) aggrave une crise déjà forte de systemes_productifs_travail (level 67)
- ➕ apparaît : systemes_productifs_travail (level 67) aggrave une crise déjà forte de demographie_mobilite_humaine (level 70)
- ➕ apparaît : CASCADE CRITIQUE : systeme_economique_redistribution déclenche une cascade rapide sur geopolitique_conflits
- ➕ apparaît : CASCADE CRITIQUE : demographie_mobilite_humaine déclenche une cascade rapide sur geopolitique_conflits
- ➕ apparaît : systemes_productifs_travail (level 67) en crise atténue la pression sur climat_environnement_global (level 28)
_Une tension se déclenche quand un niveau franchit un seuil (60, ou 70 pour une cascade, abaissés selon le risque de bascule de la variable) : un écart de quelques dixièmes peut suffire si le niveau était déjà au bord._

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

_(résultat repris du cache : même hypothèse, mêmes effets — `--refaire` pour relancer)_

La pandémie de peste pulmonaire résistante (2043-2046) fracture brutalement l'équilibre hybride du scénario *new_sustainability* en désorganisant les systèmes productifs, sanitaires et démographiques. Les capacités de coordination technocratique et algorithmique (ARIA, CGAI) sont mises à l'épreuve, mais résistent en se recentrant sur la gestion de crise, tandis que les réseaux territoriaux (RVC, CTSA) deviennent des refuges de résilience. La gouvernance mondiale se polarise entre urgence sanitaire et régénération écologique, sans remettre en cause les institutions dominantes (CMRE, APRC), mais en accélérant leur transformation. Les zones urbaines denses et les corridors logistiques sont les plus touchés, tandis que les territoires autonomes ou ruraux (Sahel, Amazonie, Arctique) limitent les dégâts. _(ampleur : forte)_

**Trajectoires d'entités**
- Réseau des Villes Régénératives (`reseau_des_villes_regeneratives_new_sustainability`) : émergent → **marginal** — Effondrement des villes denses et désaffection des modèles urbains centralisés, malgré leur rôle initial dans la transition écologique.
- Agence Globale de Régénération des Bassins Versants (AGRB-ONU) (`agence_globale_de_regeneration_des_bassins_versants_agrb_onu_new_sustainability`) : émergent → **ascendant** — La crise sanitaire révèle l'importance critique de l'eau et des bassins versants, renforçant son mandat et ses ressources.
- Nexus BioSyn Consortium for Life Sciences (`nexus_biosyn_new_sustainability`) : transformé → **dominant** — Urgence biotechnologique accélère la recherche sur les pathogènes, consolidant son rôle dans la gouvernance sanitaire mondiale.
- Confédération des Territoires Sahéliens Autonomes — CTSA (`ligue_des_cites_du_sahel_numerique_new_sustainability`) : mature → **dominant** — Les corridors verts du Sahel deviennent des zones de repli et de régénération, attirant populations et investissements.
- Consortium Amazônia Viva (`consortium_amazonia_viva_new_sustainability`) : dominant → **mature** — L'Amazonie, moins touchée par la pandémie, renforce son autonomie face aux pressions extérieures et devient un modèle de gouvernance post-urbaine.
- Réseau ARIA — Architecture Régionale d'Intelligence Allocative (`grille_aria_new_sustainability`) : dominant → **transformé** — L'infrastructure IA-native est réorientée vers la gestion des crises sanitaires et logistiques, perdant une partie de sa neutralité initiale.
- Mnemos — Réseau de Mémoire Distribuée (`reseau_mnemos_new_sustainability`) : dominant → **mature** — La mémoire distribuée devient un outil clé pour préserver les savoirs critiques dans un monde fragmenté, mais son accès est restreint par les urgences.

**Relations**
- alliance nouvelle : Conseil Mondial de la Régénération Écosystémique (CMRE) ↔ Autorité Planétaire pour la Régénération Climatique — Les deux institutions fusionnent temporairement leurs priorités pour intégrer la résilience sanitaire dans les plans de régénération écologique.
- opposition nouvelle : Nexus BioSyn Consortium for Life Sciences ↔ Collectifs Riverains du Bassin du Congo — Les collectifs locaux s'opposent aux essais cliniques accélérés de Nexus BioSyn dans le bassin du Congo, craignant une exploitation sanitaire.

**Statut des zones**
- Amériques reconfigurées (`ameriques_reconfigurees`) : emergent → **fragmenté** — Effondrement des chaînes logistiques et tensions entre zones urbaines sinistrées (Chicago) et territoires autonomes (Amazonie, Grands Lacs).
- Sahel — Corridors verts du RVC (`sahel_corridors_verts_rvc`) : emergent → **stable** — Les corridors verts du Sahel, moins touchés par la pandémie, deviennent des zones de stabilité et de régénération prioritaires.
- Barcelone-Hub — Bureau ibérique de la CMTCA (`barcelone_hub`) : stable → **en_declin** — Barcelone, hub urbain dense, subit un exode massif et une perte d'influence au profit de territoires moins exposés.

**Nouvelles entités plausibles**
- Alliance des Territoires Sanitaires Autonomes (ATSA) (afrique_continentale) : Réseau de gouvernance locale pour la gestion des crises sanitaires et la résilience territoriale, contestant les modèles centralisés. — Émergence de zones autonomes (Sahel, bassin du Congo) refusant les protocoles sanitaires imposés par les institutions globales.
- Fonds d'Urgence pour la Régénération Humaine (FURH) (hub_nairobi_kigali) : Mécanisme financier dédié à la reconstruction démographique et sanitaire, piloté par le Hub Nairobi-Kigali. — Nécessité de financer des programmes de repeuplement et de soins dans les zones les plus touchées.
- Observatoire des Pathogènes Résistants (OPR) (centre_institutionnel_geneve) : Agence de surveillance et de modélisation des menaces sanitaires, intégrée au CGAI. — La pandémie révèle l'absence de coordination globale sur les pathogènes résistants, justifiant une nouvelle institution.

_Propositions écartées au contrôle (6) : trajectoire : institut_des_seuils_demographiques_new_sustainability déjà dominant (aucun changement) ; relation bloc_eurasien_souverainiste_new_sustainability / centre_institutionnel_geneve_new_sustainability : opposition déjà présente ; relation : entités 'reseau_des_villes_regeneratives_new_sustainability' / 'reseau_vivant_continental_new_sustainability' inconnues ou identiques ; relation hub_nairobi_kigali_new_sustainability / parlement_territoires_nairobi_new_sustainability : alliance déjà présente (proposée comme renforcée, rien à changer) ; relation pacifique_sud_resilience_network_new_sustainability / te_moana_nui_plateforme : 'te_moana_nui_plateforme' est une zone (une relation relie deux entités) ; statut de zone : moyen_orient_golfe → disparu écarté, hypothèse sans effet territorial (`carte: non`)_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Statuts de zone**
- [ ] 1. `ameriques_reconfigurees` (Amériques reconfigurées) : emergent → fragmenté
  - à la main : geographie/new_sustainability.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario new_sustainability --execute)
  - _Effondrement des chaînes logistiques et tensions entre zones urbaines sinistrées (Chicago) et territoires autonomes (Amazonie, Grands Lacs)._
- [ ] 2. `sahel_corridors_verts_rvc` (Sahel — Corridors verts du RVC) : emergent → stable
  - à la main : geographie/new_sustainability.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario new_sustainability --execute)
  - _Les corridors verts du Sahel, moins touchés par la pandémie, deviennent des zones de stabilité et de régénération prioritaires._
- [ ] 3. `barcelone_hub` (Barcelone-Hub — Bureau ibérique de la CMTCA) : stable → en_declin
  - à la main : geographie/new_sustainability.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario new_sustainability --execute)
  - _Barcelone, hub urbain dense, subit un exode massif et une perte d'influence au profit de territoires moins exposés._

**Élément**
- [ ] 4. Mode rupture : décision S19 à prendre avant toute écriture
  - _l'injection réelle ne connaît que le mode choc ; appliquer la rupture = changer la référence_
- [ ] 5. demographie_mobilite_humaine : référence 45,0 → 68,4
  - à la main : variables/demographie_mobilite_humaine.md, states.new_sustainability.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 6. sante_biotechnologies : référence 30,0 → 54,0
  - à la main : variables/sante_biotechnologies.md, states.new_sustainability.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 7. systemes_productifs_travail : référence 50,0 → 67,3
  - à la main : variables/systemes_productifs_travail.md, states.new_sustainability.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 8. frontieres_du_systeme : référence 20,0 → 34,8
  - à la main : variables/frontieres_du_systeme.md, states.new_sustainability.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 9. systeme_economique_redistribution : référence 65,0 → 79,1
  - à la main : variables/systeme_economique_redistribution.md, states.new_sustainability.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 10. organisation_territoires : référence 35,0 → 44,9
  - à la main : variables/organisation_territoires.md, states.new_sustainability.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 11. gouvernance_institutions : référence 10,0 → 21,9
  - à la main : variables/gouvernance_institutions.md, states.new_sustainability.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 12. climat_environnement_global : référence 35,0 → 30,0
  - à la main : variables/climat_environnement_global.md, states.new_sustainability.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_

**Nouvelles entités**
- [ ] 13. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie à choisir
  - `python3 generator/create_entities_and_instances.py --mode custom`
  - _la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 14. Réseau des Villes Régénératives (`reseau_des_villes_regeneratives_new_sustainability`) : émergent → marginal
  - à la main : instances/reseau_des_villes_regeneratives_new_sustainability.md, champ `trajectoire`
  - _Effondrement des villes denses et désaffection des modèles urbains centralisés, malgré leur rôle initial dans la transition écologique._
- [ ] 15. Agence Globale de Régénération des Bassins Versants (AGRB-ONU) (`agence_globale_de_regeneration_des_bassins_versants_agrb_onu_new_sustainability`) : émergent → ascendant
  - à la main : instances/agence_globale_de_regeneration_des_bassins_versants_agrb_onu_new_sustainability.md, champ `trajectoire`
  - _La crise sanitaire révèle l'importance critique de l'eau et des bassins versants, renforçant son mandat et ses ressources._
- [ ] 16. Nexus BioSyn Consortium for Life Sciences (`nexus_biosyn_new_sustainability`) : transformé → dominant
  - à la main : instances/nexus_biosyn_new_sustainability.md, champ `trajectoire`
  - _Urgence biotechnologique accélère la recherche sur les pathogènes, consolidant son rôle dans la gouvernance sanitaire mondiale._
- [ ] 17. Confédération des Territoires Sahéliens Autonomes — CTSA (`ligue_des_cites_du_sahel_numerique_new_sustainability`) : mature → dominant
  - à la main : instances/ligue_des_cites_du_sahel_numerique_new_sustainability.md, champ `trajectoire`
  - _Les corridors verts du Sahel deviennent des zones de repli et de régénération, attirant populations et investissements._
- [ ] 18. Consortium Amazônia Viva (`consortium_amazonia_viva_new_sustainability`) : dominant → mature
  - à la main : instances/consortium_amazonia_viva_new_sustainability.md, champ `trajectoire`
  - _L'Amazonie, moins touchée par la pandémie, renforce son autonomie face aux pressions extérieures et devient un modèle de gouvernance post-urbaine._
- [ ] 19. Réseau ARIA — Architecture Régionale d'Intelligence Allocative (`grille_aria_new_sustainability`) : dominant → transformé
  - à la main : instances/grille_aria_new_sustainability.md, champ `trajectoire` ; puis `annee_fin` (fix_annee_fin_manquant.py)
  - _L'infrastructure IA-native est réorientée vers la gestion des crises sanitaires et logistiques, perdant une partie de sa neutralité initiale._
- [ ] 20. Mnemos — Réseau de Mémoire Distribuée (`reseau_mnemos_new_sustainability`) : dominant → mature
  - à la main : instances/reseau_mnemos_new_sustainability.md, champ `trajectoire`
  - _La mémoire distribuée devient un outil clé pour préserver les savoirs critiques dans un monde fragmenté, mais son accès est restreint par les urgences._

**Relations**
- [ ] 21. alliance nouvelle : Conseil Mondial de la Régénération Écosystémique (CMRE) ↔ Autorité Planétaire pour la Régénération Climatique
  - à la main : ajouter `agence_stabilisation_climatique_new_sustainability` dans `alliances` de instances/conseil_mondial_de_la_regeneration_ecosystemique_cmre_new_sustainability.md
  - _Les deux institutions fusionnent temporairement leurs priorités pour intégrer la résilience sanitaire dans les plans de régénération écologique._
- [ ] 22. opposition nouvelle : Nexus BioSyn Consortium for Life Sciences ↔ Collectifs Riverains du Bassin du Congo
  - à la main : ajouter `collectifs_riverains_du_bassin_du_congo_new_sustainability` dans `oppositions` de instances/nexus_biosyn_new_sustainability.md
  - _Les collectifs locaux s'opposent aux essais cliniques accélérés de Nexus BioSyn dans le bassin du Congo, craignant une exploitation sanitaire._
- [ ] 23. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario new_sustainability --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 24. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section new_sustainability
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 25. Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche
  - _une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, après l'ajout des faits imposés dans lore_regles.yaml (section Lore)_
- [ ] 26. Estimer la relecture IA des fiches de plus fort impact
  - `python3 generator/audit_lore.py --scenario new_sustainability --llm --estimer --limit 10`
  - _aucun appel_
- [ ] 27. Relecture IA des 10 fiches de plus fort impact (contradictions avec l'hypothèse)
  - `python3 generator/audit_lore.py --scenario new_sustainability --llm --limit 10`
  - _payant (≈ 0,5 centime la fiche) ; après application de l'événement_
- [ ] 28. Relecture IA des fiches de la zone `ameriques_reconfigurees` (statut changé)
  - `python3 generator/audit_lore.py --scenario new_sustainability --llm --zone ameriques_reconfigurees`
  - _estimer d'abord avec --estimer ; payant_
- [ ] 29. Relecture IA des fiches de la zone `barcelone_hub` (statut changé)
  - `python3 generator/audit_lore.py --scenario new_sustainability --llm --zone barcelone_hub`
  - _estimer d'abord avec --estimer ; payant_
- [ ] 30. Relecture IA des fiches de la zone `sahel_corridors_verts_rvc` (statut changé)
  - `python3 generator/audit_lore.py --scenario new_sustainability --llm --zone sahel_corridors_verts_rvc`
  - _estimer d'abord avec --estimer ; payant_

**Articles et site**
- [ ] 31. 29 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« « Slow Regeneration » : quand les familles kényanes réinventent le luxe dans l’ère post-croissance »; « « Slow Data » : quand la mémoire numérique devient un art de vivre »; « « Longévité fluide » : quand la médecine régénérative réinvente les rites familiaux »; « « Besoin d’un audit algorithmique citoyen ? Le Collectif Dados Abertos Já lance son service d’été à Heliópolis » »; « « Offre d’emploi : Médiateur cognitif pour hubs urbains régénératifs » »; « Te Moana Nui sous alerte orange : les courants du Pacifique Sud défient les modèles »; « « Seuil » franchit la ligne rouge : quand l’alerte climatique devient une arme politique »; « L’IA décisionnelle à l’épreuve de la mémoire : quand les algorithmes oublient les crises »; « « ARIA-2.0 : Quand l’optimisation algorithmique devient un acte politique » »; « « Mnemos sous pression : quand les archives numériques deviennent un champ de bataille géopolitique » » …_
- [ ] 32. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario new_sustainability`
  - _payant, un appel_
- [ ] 33. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 34. Base
  - `python3 generator/validate.py`
- [ ] 35. Lore
  - `python3 generator/audit_lore.py --scenario new_sustainability`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Alliance des Territoires Sanitaires Autonomes (ATSA)
  category: <à choisir>
  role: Réseau de gouvernance locale pour la gestion des crises sanitaires et la résilience territoriale,
    contestant les modèles centralisés.
  etat: émergent
  scenario_ref: new_sustainability
  scenario_hint:
  - new_sustainability
  zone_hint: afrique_continentale
  source: et_si_peste_pulmonaire_2043
- nom: Fonds d'Urgence pour la Régénération Humaine (FURH)
  category: <à choisir>
  role: Mécanisme financier dédié à la reconstruction démographique et sanitaire, piloté par le Hub Nairobi-Kigali.
  etat: émergent
  scenario_ref: new_sustainability
  scenario_hint:
  - new_sustainability
  zone_hint: hub_nairobi_kigali
  source: et_si_peste_pulmonaire_2043
- nom: Observatoire des Pathogènes Résistants (OPR)
  category: <à choisir>
  role: Agence de surveillance et de modélisation des menaces sanitaires, intégrée au CGAI.
  etat: émergent
  scenario_ref: new_sustainability
  scenario_hint:
  - new_sustainability
  zone_hint: centre_institutionnel_geneve
  source: et_si_peste_pulmonaire_2043
```

## eco_communalism

Apparu en 2043 dans le scénario eco_communalism, Pandémie de peste pulmonaire agit d'abord sur démographie mobilité humaine, santé biotechnologies, systèmes productifs travail, système économique redistribution, frontières du système et 3 autres. Son effet le plus fort aggrave démographie mobilité humaine, avec un écart maximal de +27,7 points vers 2098. Par propagation, technologie information réagit à son tour environ 9 ans après l'apparition (+7,8 points au plus fort). En 2098, il en subsiste +27,7 points sur démographie mobilité humaine.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| demographie_mobilite_humaine | 40,0 → 63,6 | 41,1 | 68,8 | **+27,7** | direct |
| sante_biotechnologies | 40,0 → 63,6 | 39,2 | 66,1 | **+26,9** | direct |
| systemes_productifs_travail | 45,0 → 62,4 | 42,7 | 65,7 | **+23,0** | direct |
| systeme_economique_redistribution | 35,0 → 49,7 | 37,1 | 56,3 | **+19,2** | direct |
| frontieres_du_systeme | 50,0 → 64,6 | 48,9 | 67,4 | **+18,5** | direct |
| gouvernance_institutions | 25,0 → 36,9 | 28,2 | 44,2 | **+16,0** | direct |
| organisation_territoires | 40,0 → 49,9 | 30,9 | 44,7 | **+13,8** | direct |
| technologie_information | 45,0 | 40,3 | 48,1 | **+7,8** | propagé |
| geopolitique_conflits | 35,0 | 36,7 | 43,0 | **+6,3** | propagé |
| energie_ressources_critiques | 50,0 | 50,2 | 54,4 | **+4,2** | propagé |
| valeurs_culture_tempo_sociale | 40,0 | 33,1 | 36,4 | **+3,3** | propagé |
| climat_environnement_global | 55,0 → 50,0 | 56,2 | 53,9 | **-2,3** | direct |

**Repères** :
- demographie_mobilite_humaine (direct) : pic +27,7 vers 2098
- sante_biotechnologies (direct) : pic +26,9 vers 2098
- systemes_productifs_travail (direct) : pic +23,1 vers 2098
- systeme_economique_redistribution (direct) : pic +19,2 vers 2098

**Tensions** : 2 sans l'hypothèse → 16 avec.
- ➕ apparaît : systeme_economique_redistribution (level 56) aggrave une crise déjà forte de systemes_productifs_travail (level 65)
- ➕ apparaît : systemes_productifs_travail (level 65) aggrave une crise déjà forte de systeme_economique_redistribution (level 56)
- ➕ apparaît : systeme_economique_redistribution (level 56) aggrave une crise déjà forte de energie_ressources_critiques (level 54)
- ➕ apparaît : energie_ressources_critiques (level 54) aggrave une crise déjà forte de systeme_economique_redistribution (level 56)
- ➕ apparaît : energie_ressources_critiques (level 54) aggrave une crise déjà forte de systemes_productifs_travail (level 65)
- ➕ apparaît : systemes_productifs_travail (level 65) en crise atténue la pression sur energie_ressources_critiques (level 54)
- ➕ apparaît : CASCADE CRITIQUE : frontieres_du_systeme déclenche une cascade rapide sur geopolitique_conflits
- ➕ apparaît : climat_environnement_global (level 53) aggrave une crise déjà forte de demographie_mobilite_humaine (level 68)
- ➕ apparaît : demographie_mobilite_humaine (level 68) aggrave une crise déjà forte de climat_environnement_global (level 53)
- ➕ apparaît : demographie_mobilite_humaine (level 68) aggrave une crise déjà forte de systemes_productifs_travail (level 65)
- ➕ apparaît : systemes_productifs_travail (level 65) aggrave une crise déjà forte de demographie_mobilite_humaine (level 68)
- ➕ apparaît : climat_environnement_global (level 53) aggrave une crise déjà forte de systemes_productifs_travail (level 65)
- ➕ apparaît : CASCADE CRITIQUE : demographie_mobilite_humaine déclenche une cascade rapide sur geopolitique_conflits
- ➕ apparaît : systemes_productifs_travail (level 65) en crise atténue la pression sur climat_environnement_global (level 53)
_Une tension se déclenche quand un niveau franchit un seuil (60, ou 70 pour une cascade, abaissés selon le risque de bascule de la variable) : un écart de quelques dixièmes peut suffire si le niveau était déjà au bord._

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

_(résultat repris du cache : même hypothèse, mêmes effets — `--refaire` pour relancer)_

La pandémie de peste pulmonaire de 2043-2046 accélère brutalement la fragmentation du monde éco-communaliste en renforçant l'autonomie locale, mais elle ne remet pas en cause sa logique fondamentale : la résilience territoriale et la gouvernance par les communs. Les zones urbaines denses et les réseaux logistiques globaux, déjà fragilisés, s'effondrent, tandis que les bioterritoires ruraux et les assemblées de bassin versant résistent mieux, devenant des refuges. La mortalité massive et la peur des contagions durcissent les frontières entre communautés, mais aussi entre factions technophiles et communalistes, creusant des lignes de fracture déjà présentes. Le scénario n'est pas bouleversé dans son essence, mais il est durablement marqué par une méfiance accrue envers les flux humains et une recentralisation forcée des ressources critiques. _(ampleur : forte)_

**Trajectoires d'entités**
- Consórcio Paulistano de Gestão Algorítmica (CPGA) (`sao_paulo_algorithmique_eco_communalism`) : dominant → **déclinant** — São Paulo, mégapole dense et dépendante des flux logistiques, subit une hémorragie démographique et une désorganisation de ses algorithmes de gestion, incapables de s'adapter à l'effondrement des chaînes d'approvisionnement.
- Factions Technophiles de la Géo-Ingénierie Centralisée (`factions_technophiles_de_la_geo_ingenierie_centralisee_eco_communalism`) : émergent → **ascendant** — Les factions technophiles profitent du chaos pour promouvoir des solutions centralisées de géo-ingénierie sanitaire, attirant les communautés désespérées par l'effondrement des systèmes locaux.
- Consortiums Industriels de l'Eau (`consortiums_industriels_de_l_eau_eco_communalism`) : émergent → **ascendant** — Les consortiums industriels de l'eau exploitent la crise pour reprendre le contrôle des nappes phréatiques et des infrastructures hydrauliques, contestant la gouvernance communautaire.

**Relations**
- opposition nouvelle : Communautés Isolationnistes Refusant la Continuité Écologique ↔ Assemblées Bioterritoriales Régionales — Les communautés isolationnistes radicalisent leur refus de coopération régionale, exacerbé par la peur des contagions et la méfiance envers les assemblées bioterritoriales.

**Statut des zones**
- São Paulo — Fragments Algorithmiques (`sao_paulo_algorithmique`) : fragmenté → **en_declin** — La mégapole de São Paulo, frappée par la pandémie et l'effondrement des flux logistiques, voit sa population et son influence décliner rapidement.
- Bioterritoires d'Amérique du Nord (`bioterritoires_amerique_du_nord`) : fragmenté → **stable** — Les Bioterritoires d'Amérique du Nord résistent mieux que les zones urbaines, mais leur statut reste précaire en raison des tensions internes et des pressions des factions technophiles.

**Nouvelles entités plausibles**
- Réseau des Sanctuaires Sanitaires Communautaires : Infrastructure de santé autonome et décentralisée, gérant les stocks de médicaments, les protocoles de quarantaine et les échanges de savoirs médicaux entre communautés. — La pandémie pousse les communautés amazoniennes à structurer leurs pratiques sanitaires traditionnelles en un réseau formel pour résister aux futures crises.
- Guilde des Passeurs de Frontières (sahel_numerique_ligue) : Réseau clandestin de facilitateurs assurant la circulation des personnes et des biens entre zones fermées, en échange de ressources ou de savoir-faire. — La fermeture des frontières et la méfiance envers les flux humains créent un marché noir des déplacements, contrôlé par des acteurs informels.
- Alliance des Bassins Résilients (confederation_bassins_vivants) : Coalition de bassins versants européens et méditerranéens partageant des protocoles sanitaires et des stocks de semences pour sécuriser leur autonomie alimentaire. — La crise sanitaire pousse les assemblées de bassin versant à mutualiser leurs ressources pour éviter les pénuries et les dépendances extérieures.

_Corrections automatiques (1) : relation communautes_isolationnistes_refusant_la_continuite_ecologique_eco_communalism / assemblees_bioterritoriales_regionales_eco_communalism : renforcée -> nouvelle (absente du vault)_

_Propositions écartées au contrôle (13) : trajectoire : ligue_des_cites_du_sahel_numerique_eco_communalism déjà dominant (aucun changement) ; trajectoire : entité inconnue 'amazon_pacte_viva_eco_communalism' ; trajectoire : confederation_bassins_vivants_eco_communalism déjà dominant (aucun changement) ; trajectoire : mouvement_des_communes_du_rust_belt_eco_communalism déjà mature (aucun changement) ; trajectoire : reseau_terrafond_bassins_eco_communalism déjà mature (aucun changement) ; relation ligue_des_cites_du_sahel_numerique_eco_communalism / sahel_numerique_ligue : 'sahel_numerique_ligue' est une zone (une relation relie deux entités) ; relation : entités 'amazon_pacte_viva_eco_communalism' / 'enclaves_extractivistes_et_etats_residuels_eco_communalism' inconnues ou identiques ; relation confederation_bassins_vivants_eco_communalism / factions_technophiles_de_la_geo_ingenierie_centralisee_eco_communalism : opposition déjà présente …_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Statuts de zone**
- [ ] 1. `sao_paulo_algorithmique` (São Paulo — Fragments Algorithmiques) : fragmenté → en_declin
  - à la main : geographie/eco_communalism.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario eco_communalism --execute)
  - _La mégapole de São Paulo, frappée par la pandémie et l'effondrement des flux logistiques, voit sa population et son influence décliner rapidement._
- [ ] 2. `bioterritoires_amerique_du_nord` (Bioterritoires d'Amérique du Nord) : fragmenté → stable
  - à la main : geographie/eco_communalism.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario eco_communalism --execute)
  - _Les Bioterritoires d'Amérique du Nord résistent mieux que les zones urbaines, mais leur statut reste précaire en raison des tensions internes et des pressions des factions technophiles._

**Élément**
- [ ] 3. Mode rupture : décision S19 à prendre avant toute écriture
  - _l'injection réelle ne connaît que le mode choc ; appliquer la rupture = changer la référence_
- [ ] 4. demographie_mobilite_humaine : référence 40,0 → 63,6
  - à la main : variables/demographie_mobilite_humaine.md, states.eco_communalism.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 5. sante_biotechnologies : référence 40,0 → 63,6
  - à la main : variables/sante_biotechnologies.md, states.eco_communalism.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 6. systemes_productifs_travail : référence 45,0 → 62,4
  - à la main : variables/systemes_productifs_travail.md, states.eco_communalism.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 7. systeme_economique_redistribution : référence 35,0 → 49,7
  - à la main : variables/systeme_economique_redistribution.md, states.eco_communalism.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 8. frontieres_du_systeme : référence 50,0 → 64,6
  - à la main : variables/frontieres_du_systeme.md, states.eco_communalism.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 9. gouvernance_institutions : référence 25,0 → 36,9
  - à la main : variables/gouvernance_institutions.md, states.eco_communalism.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 10. organisation_territoires : référence 40,0 → 49,9
  - à la main : variables/organisation_territoires.md, states.eco_communalism.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 11. climat_environnement_global : référence 55,0 → 50,0
  - à la main : variables/climat_environnement_global.md, states.eco_communalism.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_

**Nouvelles entités**
- [ ] 12. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie à choisir
  - `python3 generator/create_entities_and_instances.py --mode custom`
  - _la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 13. Consórcio Paulistano de Gestão Algorítmica (CPGA) (`sao_paulo_algorithmique_eco_communalism`) : dominant → déclinant
  - à la main : instances/sao_paulo_algorithmique_eco_communalism.md, champ `trajectoire`
  - _São Paulo, mégapole dense et dépendante des flux logistiques, subit une hémorragie démographique et une désorganisation de ses algorithmes de gestion, incapables de s'adapter à l'effondrement des chaînes d'approvisionnement._
- [ ] 14. Factions Technophiles de la Géo-Ingénierie Centralisée (`factions_technophiles_de_la_geo_ingenierie_centralisee_eco_communalism`) : émergent → ascendant
  - à la main : instances/factions_technophiles_de_la_geo_ingenierie_centralisee_eco_communalism.md, champ `trajectoire`
  - _Les factions technophiles profitent du chaos pour promouvoir des solutions centralisées de géo-ingénierie sanitaire, attirant les communautés désespérées par l'effondrement des systèmes locaux._
- [ ] 15. Consortiums Industriels de l'Eau (`consortiums_industriels_de_l_eau_eco_communalism`) : émergent → ascendant
  - à la main : instances/consortiums_industriels_de_l_eau_eco_communalism.md, champ `trajectoire`
  - _Les consortiums industriels de l'eau exploitent la crise pour reprendre le contrôle des nappes phréatiques et des infrastructures hydrauliques, contestant la gouvernance communautaire._

**Relations**
- [ ] 16. opposition nouvelle : Communautés Isolationnistes Refusant la Continuité Écologique ↔ Assemblées Bioterritoriales Régionales
  - à la main : ajouter `assemblees_bioterritoriales_regionales_eco_communalism` dans `oppositions` de instances/communautes_isolationnistes_refusant_la_continuite_ecologique_eco_communalism.md
  - _Les communautés isolationnistes radicalisent leur refus de coopération régionale, exacerbé par la peur des contagions et la méfiance envers les assemblées bioterritoriales._
- [ ] 17. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario eco_communalism --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 18. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section eco_communalism
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 19. Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche
  - _une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, après l'ajout des faits imposés dans lore_regles.yaml (section Lore)_
- [ ] 20. Estimer la relecture IA des fiches de plus fort impact
  - `python3 generator/audit_lore.py --scenario eco_communalism --llm --estimer --limit 10`
  - _aucun appel_
- [ ] 21. Relecture IA des 10 fiches de plus fort impact (contradictions avec l'hypothèse)
  - `python3 generator/audit_lore.py --scenario eco_communalism --llm --limit 10`
  - _payant (≈ 0,5 centime la fiche) ; après application de l'événement_
- [ ] 22. Relecture IA des fiches de la zone `bioterritoires_amerique_du_nord` (statut changé)
  - `python3 generator/audit_lore.py --scenario eco_communalism --llm --zone bioterritoires_amerique_du_nord`
  - _estimer d'abord avec --estimer ; payant_
- [ ] 23. Relecture IA des fiches de la zone `sao_paulo_algorithmique` (statut changé)
  - `python3 generator/audit_lore.py --scenario eco_communalism --llm --zone sao_paulo_algorithmique`
  - _estimer d'abord avec --estimer ; payant_

**Articles et site**
- [ ] 24. 7 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« À 126 ans, Maman Élikya oblige la santé des communs à regarder ses fractures »; « Kharg-9 : Le Data Haven des communs au bord de la rupture ? »; « Kharg-9 : Le coffre-fort des communs devient un supermarché des données »; « Les algorithmes de la soif : quand les bassins méditerranéens négocient leur eau en secret »; « « Kharg-9 sous pression : quand le sanctuaire des données devient l’enjeu d’une guerre des seuils » »; « « SahelOS sous pression : quand la souveraineté numérique devient une monnaie d’échange » »; « « Les données ne coulent plus : le Maghreb en tension sur les seuils numériques » »_
- [ ] 25. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario eco_communalism`
  - _payant, un appel_
- [ ] 26. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 27. Base
  - `python3 generator/validate.py`
- [ ] 28. Lore
  - `python3 generator/audit_lore.py --scenario eco_communalism`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Réseau des Sanctuaires Sanitaires Communautaires
  category: <à choisir>
  role: Infrastructure de santé autonome et décentralisée, gérant les stocks de médicaments, les protocoles
    de quarantaine et les échanges de savoirs médicaux entre communautés.
  etat: émergent
  scenario_ref: eco_communalism
  scenario_hint:
  - eco_communalism
  source: et_si_peste_pulmonaire_2043
- nom: Guilde des Passeurs de Frontières
  category: <à choisir>
  role: Réseau clandestin de facilitateurs assurant la circulation des personnes et des biens entre zones
    fermées, en échange de ressources ou de savoir-faire.
  etat: émergent
  scenario_ref: eco_communalism
  scenario_hint:
  - eco_communalism
  zone_hint: sahel_numerique_ligue
  source: et_si_peste_pulmonaire_2043
- nom: Alliance des Bassins Résilients
  category: <à choisir>
  role: Coalition de bassins versants européens et méditerranéens partageant des protocoles sanitaires
    et des stocks de semences pour sécuriser leur autonomie alimentaire.
  etat: émergent
  scenario_ref: eco_communalism
  scenario_hint:
  - eco_communalism
  zone_hint: confederation_bassins_vivants
  source: et_si_peste_pulmonaire_2043
```

## policy_reform

Apparu en 2043 dans le scénario policy_reform, Pandémie de peste pulmonaire agit d'abord sur démographie mobilité humaine, santé biotechnologies, systèmes productifs travail, système économique redistribution, frontières du système et 3 autres. Son effet le plus fort aggrave démographie mobilité humaine, avec un écart maximal de +27,2 points vers 2098. Par propagation, technologie information réagit à son tour environ 10 ans après l'apparition (+7,6 points au plus fort). En 2098, il en subsiste +27,2 points sur démographie mobilité humaine.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| demographie_mobilite_humaine | 50,0 → 73,1 | 50,7 | 77,9 | **+27,2** | direct |
| sante_biotechnologies | 45,0 → 68,4 | 43,7 | 70,4 | **+26,7** | direct |
| systemes_productifs_travail | 60,0 → 76,9 | 59,1 | 81,5 | **+22,4** | direct |
| systeme_economique_redistribution | 55,0 → 69,5 | 52,5 | 71,8 | **+19,3** | direct |
| frontieres_du_systeme | 55,0 → 69,5 | 53,7 | 72,1 | **+18,4** | direct |
| gouvernance_institutions | 20,0 → 31,9 | 10,7 | 26,0 | **+15,3** | direct |
| organisation_territoires | 50,0 → 59,9 | 46,4 | 61,3 | **+14,9** | direct |
| technologie_information | 65,0 | 59,1 | 66,8 | **+7,7** | propagé |
| geopolitique_conflits | 45,0 | 47,3 | 53,4 | **+6,1** | propagé |
| energie_ressources_critiques | 58,0 | 56,6 | 60,9 | **+4,3** | propagé |
| valeurs_culture_tempo_sociale | 50,0 | 46,8 | 50,4 | **+3,6** | propagé |
| climat_environnement_global | 45,0 → 40,0 | 43,9 | 41,7 | **-2,2** | direct |

**Repères** :
- demographie_mobilite_humaine (direct) : pic +27,2 vers 2098
- sante_biotechnologies (direct) : pic +26,7 vers 2098
- systemes_productifs_travail (direct) : pic +22,5 vers 2098
- systeme_economique_redistribution (direct) : pic +19,4 vers 2098

**Tensions** : 11 sans l'hypothèse → 31 avec.
- ➕ apparaît : geopolitique_conflits (level 53) aggrave une crise déjà forte de energie_ressources_critiques (level 60)
- ➕ apparaît : CASCADE CRITIQUE : energie_ressources_critiques déclenche une cascade rapide sur geopolitique_conflits
- ➕ apparaît : geopolitique_conflits (level 53) aggrave une crise déjà forte de organisation_territoires (level 61)
- ➕ apparaît : geopolitique_conflits (level 53) aggrave une crise déjà forte de technologie_information (level 66)
- ➕ apparaît : organisation_territoires (level 61) aggrave une crise déjà forte de geopolitique_conflits (level 53)
- ➕ apparaît : technologie_information (level 66) aggrave une crise déjà forte de geopolitique_conflits (level 53)
- ➕ apparaît : geopolitique_conflits (level 53) aggrave une crise déjà forte de frontieres_du_systeme (level 72)
- ➕ apparaît : organisation_territoires (level 61) aggrave une crise déjà forte de systemes_productifs_travail (level 81)
- ➕ apparaît : CASCADE CRITIQUE : frontieres_du_systeme déclenche une cascade rapide sur geopolitique_conflits
- ➕ apparaît : demographie_mobilite_humaine (level 77) aggrave une crise déjà forte de systemes_productifs_travail (level 81)
- ➕ apparaît : systemes_productifs_travail (level 81) aggrave une crise déjà forte de organisation_territoires (level 61)
- ➕ apparaît : systemes_productifs_travail (level 81) aggrave une crise déjà forte de demographie_mobilite_humaine (level 77)
- ➕ apparaît : CASCADE CRITIQUE : systeme_economique_redistribution déclenche une cascade rapide sur geopolitique_conflits
- ➕ apparaît : geopolitique_conflits (level 53) aggrave une crise déjà forte de systeme_economique_redistribution (level 71)
- ➕ apparaît : geopolitique_conflits (level 53) aggrave une crise déjà forte de demographie_mobilite_humaine (level 77)
- ➕ apparaît : organisation_territoires (level 61) aggrave une crise déjà forte de technologie_information (level 66)
- ➕ apparaît : organisation_territoires (level 61) aggrave une crise déjà forte de demographie_mobilite_humaine (level 77)
- ➕ apparaît : technologie_information (level 66) aggrave une crise déjà forte de organisation_territoires (level 61)
- ➕ apparaît : CASCADE CRITIQUE : demographie_mobilite_humaine déclenche une cascade rapide sur geopolitique_conflits
- ➕ apparaît : demographie_mobilite_humaine (level 77) aggrave une crise déjà forte de organisation_territoires (level 61)
- ⬆ devient une cascade critique : systeme_economique_redistribution → energie_ressources_critiques
- ⬆ devient une cascade critique : energie_ressources_critiques → systeme_economique_redistribution
- ⬆ devient une cascade critique : energie_ressources_critiques → systemes_productifs_travail
_Une tension se déclenche quand un niveau franchit un seuil (60, ou 70 pour une cascade, abaissés selon le risque de bascule de la variable) : un écart de quelques dixièmes peut suffire si le niveau était déjà au bord._

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

_(résultat repris du cache : même hypothèse, mêmes effets — `--refaire` pour relancer)_

La pandémie de peste pulmonaire de 2043-2046 constitue un choc démographique et systémique majeur qui accélère la centralisation technocratique et la gouvernance algorithmique, tout en creusant les fractures entre zones stables et territoires en déclin. Les institutions globales (hub_europeen_regulation, espace_eurasiatique) renforcent leur légitimité en tant que garantes de la résilience sanitaire et économique, tandis que les zones déjà fragiles (bloc_souverainiste_non_signataire, zone_moyen_orient_golfe) sombrent dans des crises de gouvernance. La reconstruction post-pandémie consolide les modèles de régulation préexistants (ARIA-Nexus, RIREC) plutôt qu’elle ne les remet en cause, mais elle révèle aussi l’incapacité des États à gérer seuls les crises transnationales, renforçant le rôle des entités supranationales. Les territoires urbains denses, vidés par la mortalité, deviennent des laboratoires de réorganisation spatiale et sociale, tandis que les zones rurales ou autonomes (Archipel des Comores, Madagascar) résistent mieux mais peinent à s’intégrer aux réseaux globaux. _(ampleur : bascule)_

**Trajectoires d'entités**
- Coalition des Villes de Reconversion (`coalition_des_villes_de_reconversion_policy_reform`) : émergent → **dominant** — La désertification des villes denses impose une refonte radicale des politiques urbaines, donnant à la coalition un rôle central dans la reconstruction et la régulation des flux humains.
- Consortium des Villes-États Durables (`consortium_des_villes_etats_durables_policy_reform`) : émergent → **dominant** — Les villes-États deviennent les unités de gouvernance les plus résilientes, leur modèle de durabilité étant validé par la crise sanitaire et économique.
- Autorité Mondiale du Vivant (AMV) (`autorite_mondiale_du_vivant_amv_policy_reform`) : émergent → **dominant** — La gestion des pathogènes et des biotechnologies médicales passe sous contrôle supranational, renforçant l’AMV.
- Front des Autonomies Territoriales Radicales (`front_des_autonomies_territoriales_radicales_policy_reform`) : émergent → **marginal** — Les territoires dissidents, incapables de gérer seuls la crise sanitaire, perdent en influence face aux institutions globales.
- Syndicats d'Extraction Privée Non Régulés (`syndicats_d_extraction_privee_non_regules_policy_reform`) : émergent → **résiduel** — L’effondrement des chaînes d’approvisionnement et la priorité donnée aux ressources stratégiques marginalisent les acteurs non régulés.

**Relations**
- alliance nouvelle : Coalition des Villes de Reconversion ↔ Consortium des Villes-États Durables — Les deux entités unissent leurs efforts pour standardiser les politiques de reconstruction urbaine et sanitaire.
- alliance nouvelle : NexCore Global Infrastructure Alliance (NGIA) ↔ Autorité Centrale de Régulation Algorithmique (ACRA) — La dépendance aux infrastructures numériques critiques (santé, logistique) consolide leur collaboration pour une régulation centralisée.
- opposition nouvelle : Collectifs de Gouvernance Communautaire Décentralisée ↔ Institut des Seuils Démographiques - Autorité de Régulation des Flux Humains (ISD-ARFH) — Les collectifs locaux contestent les politiques de relocalisation forcée imposées par l’ISD-ARFH, jugées autoritaires.
- alliance nouvelle : Consortium Helios ↔ Agence Mondiale pour la Stabilisation Climatique — La crise sanitaire accélère les projets de géo-ingénierie climatique, perçus comme un rempart contre les futures pandémies liées aux dérèglements écologiques.

**Statut des zones**
- Bloc Souverainiste Non-Signataire (Sud Global dissident) (`bloc_souverainiste_non_signataire`) : stable → **fragmenté** — La pandémie aggrave les divisions internes, certains territoires (Niger, Mali) sombrant dans l’instabilité tandis que d’autres (Brésil, Argentine) se rapprochent des institutions globales.
- Hub Africain de Gouvernance (Nairobi-Kigali-Brazzaville) (`hub_africain_gouvernance`) : emergent → **dominant** — Sa gestion efficace de la crise sanitaire et hydrique en fait un modèle de gouvernance régionale, attirant des territoires voisins en déclin.

**Nouvelles entités plausibles**
- Autorité Sanitaire Mondiale (ASM) (geneve_lacustre) : Institution supranationale chargée de la prévention et de la gestion des pandémies, intégrant les protocoles de l’AMV et de l’ATRB. — La crise révèle l’absence d’une autorité sanitaire globale, justifiant la création d’une entité dédiée.
- Collectifs de Résilience Urbaine Post-Peste (CRUPP) (amsterdam_region) : Réseaux locaux de reconstruction et de gestion des ressources dans les villes désertées, en opposition aux politiques centralisées. — Les habitants des villes sinistrées s’organisent en marge des institutions pour survivre et reconstruire.
- Fonds de Reconstruction Démographique (FRD) (geneve_nexus) : Mécanisme financier global pour relancer la natalité et les migrations contrôlées, piloté par l’ISD-ARFH et l’ACRA. — La chute démographique impose des politiques de repeuplement ciblées, nécessitant un outil financier dédié.

_Corrections automatiques (2) : relation nexcore_policy_reform / bureau_gouvernance_algorithmique_policy_reform : renforcée -> nouvelle (absente du vault) ; relation consortium_helios_policy_reform / agence_stabilisation_climatique_policy_reform : renforcée -> nouvelle (absente du vault)_

_Propositions écartées au contrôle (7) : trajectoire : institut_des_seuils_demographiques_policy_reform déjà dominant (aucun changement) ; trajectoire : grille_aria_policy_reform déjà dominant (aucun changement) ; trajectoire : trame_bioclimatique_policy_reform déjà dominant (aucun changement) ; relation agence_de_regulation_des_detroits_strategiques_ards_policy_reform / arctic_passage_authority_policy_reform : alliance déjà présente ; relation hub_africain_gouvernance / bloc_souverainiste_non_signataire : 'hub_africain_gouvernance' et 'bloc_souverainiste_non_signataire' sont des zones (une relation relie deux entités) ; statut de zone : zone_moyen_orient_golfe → disparu écarté, hypothèse sans effet territorial (`carte: non`) ; statut de zone : sahel_occidental_dissident → disparu écarté, hypothèse sans effet territorial (`carte: non`)_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Statuts de zone**
- [ ] 1. `bloc_souverainiste_non_signataire` (Bloc Souverainiste Non-Signataire (Sud Global dissident)) : stable → fragmenté
  - à la main : geographie/policy_reform.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario policy_reform --execute)
  - _La pandémie aggrave les divisions internes, certains territoires (Niger, Mali) sombrant dans l’instabilité tandis que d’autres (Brésil, Argentine) se rapprochent des institutions globales._
- [ ] 2. `hub_africain_gouvernance` (Hub Africain de Gouvernance (Nairobi-Kigali-Brazzaville)) : emergent → dominant
  - à la main : geographie/policy_reform.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario policy_reform --execute)
  - _Sa gestion efficace de la crise sanitaire et hydrique en fait un modèle de gouvernance régionale, attirant des territoires voisins en déclin._

**Élément**
- [ ] 3. Mode rupture : décision S19 à prendre avant toute écriture
  - _l'injection réelle ne connaît que le mode choc ; appliquer la rupture = changer la référence_
- [ ] 4. demographie_mobilite_humaine : référence 50,0 → 73,1
  - à la main : variables/demographie_mobilite_humaine.md, states.policy_reform.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 5. sante_biotechnologies : référence 45,0 → 68,4
  - à la main : variables/sante_biotechnologies.md, states.policy_reform.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 6. systemes_productifs_travail : référence 60,0 → 76,9
  - à la main : variables/systemes_productifs_travail.md, states.policy_reform.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 7. systeme_economique_redistribution : référence 55,0 → 69,5
  - à la main : variables/systeme_economique_redistribution.md, states.policy_reform.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 8. frontieres_du_systeme : référence 55,0 → 69,5
  - à la main : variables/frontieres_du_systeme.md, states.policy_reform.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 9. gouvernance_institutions : référence 20,0 → 31,9
  - à la main : variables/gouvernance_institutions.md, states.policy_reform.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 10. organisation_territoires : référence 50,0 → 59,9
  - à la main : variables/organisation_territoires.md, states.policy_reform.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 11. climat_environnement_global : référence 45,0 → 40,0
  - à la main : variables/climat_environnement_global.md, states.policy_reform.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_

**Nouvelles entités**
- [ ] 12. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie à choisir
  - `python3 generator/create_entities_and_instances.py --mode custom`
  - _la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 13. ⚠ Coalition des Villes de Reconversion (`coalition_des_villes_de_reconversion_policy_reform`) : émergent → dominant
  - à la main : instances/coalition_des_villes_de_reconversion_policy_reform.md, champ `trajectoire`
  - _saut d'un cran (sans passer par ascendant) : garder, ou ramener à ascendant ; La désertification des villes denses impose une refonte radicale des politiques urbaines, donnant à la coalition un rôle central dans la reconstruction et la régulation des flux humains._
- [ ] 14. ⚠ Consortium des Villes-États Durables (`consortium_des_villes_etats_durables_policy_reform`) : émergent → dominant
  - à la main : instances/consortium_des_villes_etats_durables_policy_reform.md, champ `trajectoire`
  - _saut d'un cran (sans passer par ascendant) : garder, ou ramener à ascendant ; Les villes-États deviennent les unités de gouvernance les plus résilientes, leur modèle de durabilité étant validé par la crise sanitaire et économique._
- [ ] 15. ⚠ Autorité Mondiale du Vivant (AMV) (`autorite_mondiale_du_vivant_amv_policy_reform`) : émergent → dominant
  - à la main : instances/autorite_mondiale_du_vivant_amv_policy_reform.md, champ `trajectoire`
  - _saut d'un cran (sans passer par ascendant) : garder, ou ramener à ascendant ; La gestion des pathogènes et des biotechnologies médicales passe sous contrôle supranational, renforçant l’AMV._
- [ ] 16. Front des Autonomies Territoriales Radicales (`front_des_autonomies_territoriales_radicales_policy_reform`) : émergent → marginal
  - à la main : instances/front_des_autonomies_territoriales_radicales_policy_reform.md, champ `trajectoire`
  - _Les territoires dissidents, incapables de gérer seuls la crise sanitaire, perdent en influence face aux institutions globales._
- [ ] 17. Syndicats d'Extraction Privée Non Régulés (`syndicats_d_extraction_privee_non_regules_policy_reform`) : émergent → résiduel
  - à la main : instances/syndicats_d_extraction_privee_non_regules_policy_reform.md, champ `trajectoire`
  - _L’effondrement des chaînes d’approvisionnement et la priorité donnée aux ressources stratégiques marginalisent les acteurs non régulés._

**Relations**
- [ ] 18. alliance nouvelle : Coalition des Villes de Reconversion ↔ Consortium des Villes-États Durables
  - à la main : ajouter `consortium_des_villes_etats_durables_policy_reform` dans `alliances` de instances/coalition_des_villes_de_reconversion_policy_reform.md
  - _Les deux entités unissent leurs efforts pour standardiser les politiques de reconstruction urbaine et sanitaire._
- [ ] 19. alliance nouvelle : NexCore Global Infrastructure Alliance (NGIA) ↔ Autorité Centrale de Régulation Algorithmique (ACRA)
  - à la main : ajouter `bureau_gouvernance_algorithmique_policy_reform` dans `alliances` de instances/nexcore_policy_reform.md
  - _La dépendance aux infrastructures numériques critiques (santé, logistique) consolide leur collaboration pour une régulation centralisée._
- [ ] 20. opposition nouvelle : Collectifs de Gouvernance Communautaire Décentralisée ↔ Institut des Seuils Démographiques - Autorité de Régulation des Flux Humains (ISD-ARFH)
  - à la main : ajouter `institut_des_seuils_demographiques_policy_reform` dans `oppositions` de instances/collectifs_de_gouvernance_communautaire_decentralisee_policy_reform.md
  - _Les collectifs locaux contestent les politiques de relocalisation forcée imposées par l’ISD-ARFH, jugées autoritaires._
- [ ] 21. alliance nouvelle : Consortium Helios ↔ Agence Mondiale pour la Stabilisation Climatique
  - à la main : ajouter `agence_stabilisation_climatique_policy_reform` dans `alliances` de instances/consortium_helios_policy_reform.md
  - _La crise sanitaire accélère les projets de géo-ingénierie climatique, perçus comme un rempart contre les futures pandémies liées aux dérèglements écologiques._
- [ ] 22. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario policy_reform --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 23. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section policy_reform
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 24. Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche
  - _une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, après l'ajout des faits imposés dans lore_regles.yaml (section Lore)_
- [ ] 25. Estimer la relecture IA des fiches de plus fort impact
  - `python3 generator/audit_lore.py --scenario policy_reform --llm --estimer --limit 10`
  - _aucun appel_
- [ ] 26. Relecture IA des 10 fiches de plus fort impact (contradictions avec l'hypothèse)
  - `python3 generator/audit_lore.py --scenario policy_reform --llm --limit 10`
  - _payant (≈ 0,5 centime la fiche) ; après application de l'événement_
- [ ] 27. Relecture IA des fiches de la zone `bloc_souverainiste_non_signataire` (statut changé)
  - `python3 generator/audit_lore.py --scenario policy_reform --llm --zone bloc_souverainiste_non_signataire`
  - _estimer d'abord avec --estimer ; payant_
- [ ] 28. Relecture IA des fiches de la zone `hub_africain_gouvernance` (statut changé)
  - `python3 generator/audit_lore.py --scenario policy_reform --llm --zone hub_africain_gouvernance`
  - _estimer d'abord avec --estimer ; payant_

**Articles et site**
- [ ] 29. 6 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« « ARIA-Nexus en alerte rouge : la régulation mondiale des ressources à l’épreuve des fuites de Kharg-9 » »; « Kharg-9 : Le Data Nexus qui défie Genève-Nexus »; « L’IA médicale en crise de légitimité : quand les algorithmes de Genève soignent sans consentement »; « L’AMV face au scandale des « vies sous licence » : quand la santé devient un privilège algorithmique »; « Les mémoires effacées de Tillabéri : quand l’Atlas Fantôme défie les archives de Genève »; « « Votre quota ARIA-Nexus expire demain — solutions locales avant gel des flux » »_
- [ ] 30. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario policy_reform`
  - _payant, un appel_
- [ ] 31. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 32. Base
  - `python3 generator/validate.py`
- [ ] 33. Lore
  - `python3 generator/audit_lore.py --scenario policy_reform`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Autorité Sanitaire Mondiale (ASM)
  category: <à choisir>
  role: Institution supranationale chargée de la prévention et de la gestion des pandémies, intégrant
    les protocoles de l’AMV et de l’ATRB.
  etat: émergent
  scenario_ref: policy_reform
  scenario_hint:
  - policy_reform
  zone_hint: geneve_lacustre
  source: et_si_peste_pulmonaire_2043
- nom: Collectifs de Résilience Urbaine Post-Peste (CRUPP)
  category: <à choisir>
  role: Réseaux locaux de reconstruction et de gestion des ressources dans les villes désertées, en opposition
    aux politiques centralisées.
  etat: émergent
  scenario_ref: policy_reform
  scenario_hint:
  - policy_reform
  zone_hint: amsterdam_region
  source: et_si_peste_pulmonaire_2043
- nom: Fonds de Reconstruction Démographique (FRD)
  category: <à choisir>
  role: Mécanisme financier global pour relancer la natalité et les migrations contrôlées, piloté par
    l’ISD-ARFH et l’ACRA.
  etat: émergent
  scenario_ref: policy_reform
  scenario_hint:
  - policy_reform
  zone_hint: geneve_nexus
  source: et_si_peste_pulmonaire_2043
```

## reference

Apparu en 2043 dans le scénario reference, Pandémie de peste pulmonaire agit d'abord sur santé biotechnologies, démographie mobilité humaine, systèmes productifs travail, frontières du système, système économique redistribution et 3 autres. Son effet le plus fort aggrave santé biotechnologies, avec un écart maximal de +25,9 points vers 2098. Par propagation, technologie information réagit à son tour environ 8 ans après l'apparition (+2,0 points au plus fort). En 2098, il en subsiste +25,9 points sur santé biotechnologies.

_(récit construit par le script)_

| Variable | Référence | Sans | Avec | Écart | |
|---|---|---|---|---|---|
| sante_biotechnologies | 55,0 → 77,7 | 50,7 | 76,5 | **+25,8** | direct |
| demographie_mobilite_humaine | 55,0 → 77,7 | 64,2 | 89,2 | **+25,0** | direct |
| systemes_productifs_travail | 70,0 → 86,1 | 75,1 | 95,3 | **+20,2** | direct |
| frontieres_du_systeme | 55,0 → 69,5 | 62,3 | 79,4 | **+17,1** | direct |
| systeme_economique_redistribution | 70,0 → 83,9 | 82,4 | 97,5 | **+15,1** | direct |
| gouvernance_institutions | 40,0 → 51,8 | 53,8 | 66,2 | **+12,4** | direct |
| organisation_territoires | 65,0 → 74,7 | 74,2 | 86,5 | **+12,3** | direct |
| energie_ressources_critiques | 72,0 | 78,9 | 81,9 | **+3,0** | propagé |
| climat_environnement_global | 65,0 → 60,0 | 68,4 | 65,9 | **-2,5** | direct |
| valeurs_culture_tempo_sociale | 60,0 | 69,1 | 71,1 | **+2,0** | propagé |
| technologie_information | 80,0 | 92,8 | 94,2 | **+1,4** | propagé |
| geopolitique_conflits | 75,0 | 88,3 | 89,3 | **+1,0** | propagé |

**Repères** :
- sante_biotechnologies (direct) : pic +25,9 vers 2098
- demographie_mobilite_humaine (direct) : pic +24,9 vers 2098
- systemes_productifs_travail (direct) : pic +20,2 vers 2097
- frontieres_du_systeme (direct) : pic +17,5 vers 2078

**Tensions** : 42 sans l'hypothèse → 42 avec.
- ⬆ devient une cascade critique : gouvernance_institutions → geopolitique_conflits
- ⬆ devient une cascade critique : demographie_mobilite_humaine → geopolitique_conflits
_Une tension se déclenche quand un niveau franchit un seuil (60, ou 70 pour une cascade, abaissés selon le risque de bascule de la variable) : un écart de quelques dixièmes peut suffire si le niveau était déjà au bord._

### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)

_(résultat repris du cache : même hypothèse, mêmes effets — `--refaire` pour relancer)_

La pandémie de peste pulmonaire résistante (2043-2046) agit comme un accélérateur brutal des déséquilibres structurels du scénario *reference*, sans en modifier la logique profonde. Elle exacerbe les tensions préexistantes (démographie, santé, gouvernance) et force une reconfiguration des acteurs dominants, mais ne remet pas en cause l'équilibre systémique fondé sur l'innovation technologique et la régulation partielle. Les zones urbaines denses et les corridors logistiques, déjà fragilisés, deviennent des épicentres de crise, tandis que les marges et les territoires autonomes résistent mieux. Le monde de 2098 reste un système en équilibre fragile, mais recentré sur de nouvelles priorités : résilience territoriale, souveraineté sanitaire et contrôle des flux humains. _(ampleur : forte)_

**Trajectoires d'entités**
- Réseau des Villes-États Pilotes en Gouvernance Participative (`reseau_des_villes_etats_pilotes_en_gouvernance_participative_reference`) : émergent → **ascendant** — Les villes-refuge et les modèles de gouvernance locale deviennent des laboratoires de reconstruction post-pandémie, attirant des populations désillusionnées par les États centraux.
- Réseau des Villes-Refuge pour Travailleurs Désaugmentés (`reseau_des_villes_refuge_pour_travailleurs_desaugmentes_reference`) : émergent → **dominant** — La désindustrialisation accélérée et l'effondrement des chaînes de valeur globales créent une demande massive pour des espaces de reconversion, faisant de ce réseau un acteur systémique.
- Consortium Helios (`consortium_helios_reference`) : dominant → **mature** — La crise sanitaire révèle la dépendance aux infrastructures énergétiques critiques, renforçant son rôle de régulateur *de facto* mais limitant son expansion face aux risques systémiques.
- OptiFlow Global Logistics Network (OGLN) (`optiflow_logistics_reference`) : dominant → **déclinant** — La fragmentation des flux logistiques et la priorité donnée aux circuits courts réduisent son emprise sur les échanges mondiaux, malgré son rôle initial dans la gestion de crise.
- NexCore Global Infrastructure Group (`nexcore_reference`) : dominant → **déclinant** — L'effondrement des budgets publics et la méfiance envers les infrastructures centralisées affaiblissent sa position, malgré son rôle dans la reconstruction numérique.
- Algorithmic Labor Exchange (`algorithmic_labor_exchange_reference`) : émergent → **déclinant** — La précarisation massive du travail et la défiance envers les plateformes algorithmiques réduisent son influence, au profit de modèles plus locaux ou coopératifs.
- Consortiums d'Extraction Minière du Bassin Congolais (`consortiums_d_extraction_miniere_du_bassin_congolais_reference`) : émergent → **dominant** — La course aux ressources critiques pour les biotechnologies et les infrastructures post-pandémie renforce leur pouvoir, malgré les tensions sociales et environnementales.

**Relations**
- opposition nouvelle : Réseau des Villes-Refuge pour Travailleurs Désaugmentés ↔ Consortiums Énergétiques des Mégapoles — Les villes-refuge contestent l'emprise des consortiums énergétiques sur les territoires, promouvant des modèles décentralisés et autonomes.
- alliance nouvelle : Consortium Helios ↔ Fonds Souverain Arctique Scandinave — Helios et le fonds scandinave coordonnent leurs investissements dans les infrastructures énergétiques arctiques, mutualisant risques et ressources.
- opposition nouvelle : Gouvernements du Bloc Sahélien Autonome ↔ Union Africaine Résilience (UAR) — Le Bloc Sahélien, renforcé par sa gestion autonome de la crise, conteste l'autorité de l'Union Africaine, jugée trop dépendante des institutions multilatérales.

**Statut des zones**
- Europe Occidentale Reconstruite (`europe_occidentale_reconstruite`) : stable → **fragmenté** — Les tensions entre métropoles reconstruites et territoires ruraux abandonnés s'aggravent, avec des mouvements sécessionnistes ou autonomistes (ex. Massif Central, Ibérie Atlantique).
- Zones Grises Globales (`zones_grises_globales`) : fragmenté → **dominant** — L'effondrement des États centraux et la prolifération des milices et des trafics font des zones grises les nouveaux espaces de pouvoir informel.

**Nouvelles entités plausibles**
- Alliance des Villes Sanitaires Autonomes : Réseau de villes ayant mis en place des protocoles sanitaires stricts et des infrastructures médicales décentralisées, devenant des pôles d'attraction pour les populations et les investissements. — La pandémie révèle l'importance des capacités sanitaires locales, poussant les villes à mutualiser leurs ressources et à s'affranchir des États centraux.
- Consortium des Biotechnologies Post-Pandémiques (bruxelles_nouveau) : Alliance de laboratoires publics et privés ayant développé des traitements contre la peste pulmonaire, contrôlant désormais l'accès aux technologies médicales critiques. — La course aux traitements et aux vaccins crée un oligopole biotechnologique, capable de dicter ses conditions aux États et aux institutions multilatérales.
- Front des Territoires Non Connectés (zones_grises_globales) : Mouvement politique et social regroupant les régions exclues des réseaux logistiques et énergétiques globaux, promouvant des modèles de résilience locale et de décroissance. — La pandémie accélère la marginalisation des territoires périphériques, poussant à l'émergence d'une contre-culture systémique.

_Propositions écartées au contrôle (7) : trajectoire : armada_logistique_nordique_reference déjà dominant (aucun changement) ; relation armada_logistique_nordique_reference / corridor_arctique_nordique_reference : alliance déjà présente ; relation milices_concurrentes_des_droits_de_passage_reference / agence_de_regulation_des_detroits_strategiques_ards_reference : opposition déjà présente ; relation cooperatives_agro_ecologiques_de_reconstruction_territoriale_reference / consortiums_d_agriculture_verticale_algorithmique_reference : opposition déjà présente ; statut de zone : ameriques_multipolaires déjà fragmenté ; statut de zone : corridor_arctique_nordique déjà dominant ; nouvelle entité Alliance des Villes Sanitaires Autonomes : zone 'reseau_des_villes_etats_pilotes_en_gouvernance_participative_reference' inconnue (gardée sans zone)_

### Liste d'application (à valider à la main — rien n'est écrit)

_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de l'appliquer ; écarter une proposition suffit à sauter ses étapes._

**Statuts de zone**
- [ ] 1. `europe_occidentale_reconstruite` (Europe Occidentale Reconstruite) : stable → fragmenté
  - à la main : geographie/reference.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario reference --execute)
  - _Les tensions entre métropoles reconstruites et territoires ruraux abandonnés s'aggravent, avec des mouvements sécessionnistes ou autonomistes (ex. Massif Central, Ibérie Atlantique)._
- [ ] 2. `zones_grises_globales` (Zones Grises Globales) : fragmenté → dominant
  - à la main : geographie/reference.md, champ `statut` (texte mis à jour par regenerer_corps_geographie.py --scenario reference --execute)
  - _L'effondrement des États centraux et la prolifération des milices et des trafics font des zones grises les nouveaux espaces de pouvoir informel._

**Élément**
- [ ] 3. Mode rupture : décision S19 à prendre avant toute écriture
  - _l'injection réelle ne connaît que le mode choc ; appliquer la rupture = changer la référence_
- [ ] 4. sante_biotechnologies : référence 55,0 → 77,7
  - à la main : variables/sante_biotechnologies.md, states.reference.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 5. demographie_mobilite_humaine : référence 55,0 → 77,7
  - à la main : variables/demographie_mobilite_humaine.md, states.reference.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 6. systemes_productifs_travail : référence 70,0 → 86,1
  - à la main : variables/systemes_productifs_travail.md, states.reference.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 7. frontieres_du_systeme : référence 55,0 → 69,5
  - à la main : variables/frontieres_du_systeme.md, states.reference.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 8. systeme_economique_redistribution : référence 70,0 → 83,9
  - à la main : variables/systeme_economique_redistribution.md, states.reference.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 9. gouvernance_institutions : référence 40,0 → 51,8
  - à la main : variables/gouvernance_institutions.md, states.reference.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 10. organisation_territoires : référence 65,0 → 74,7
  - à la main : variables/organisation_territoires.md, states.reference.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_
- [ ] 11. climat_environnement_global : référence 65,0 → 60,0
  - à la main : variables/climat_environnement_global.md, states.reference.level, puis python3 generator/synchroniser_scenarios.py
  - _seulement si la décision S19 est oui_

**Nouvelles entités**
- [ ] 12. 3 entrée(s) prête(s) (bloc YAML ci-dessous) pour entites_custom/queue.yaml — catégorie à choisir
  - `python3 generator/create_entities_and_instances.py --mode custom`
  - _la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario_

**Trajectoires**
- [ ] 13. Réseau des Villes-États Pilotes en Gouvernance Participative (`reseau_des_villes_etats_pilotes_en_gouvernance_participative_reference`) : émergent → ascendant
  - à la main : instances/reseau_des_villes_etats_pilotes_en_gouvernance_participative_reference.md, champ `trajectoire`
  - _Les villes-refuge et les modèles de gouvernance locale deviennent des laboratoires de reconstruction post-pandémie, attirant des populations désillusionnées par les États centraux._
- [ ] 14. ⚠ Réseau des Villes-Refuge pour Travailleurs Désaugmentés (`reseau_des_villes_refuge_pour_travailleurs_desaugmentes_reference`) : émergent → dominant
  - à la main : instances/reseau_des_villes_refuge_pour_travailleurs_desaugmentes_reference.md, champ `trajectoire`
  - _saut d'un cran (sans passer par ascendant) : garder, ou ramener à ascendant ; La désindustrialisation accélérée et l'effondrement des chaînes de valeur globales créent une demande massive pour des espaces de reconversion, faisant de ce réseau un acteur systémique._
- [ ] 15. Consortium Helios (`consortium_helios_reference`) : dominant → mature
  - à la main : instances/consortium_helios_reference.md, champ `trajectoire`
  - _La crise sanitaire révèle la dépendance aux infrastructures énergétiques critiques, renforçant son rôle de régulateur *de facto* mais limitant son expansion face aux risques systémiques._
- [ ] 16. OptiFlow Global Logistics Network (OGLN) (`optiflow_logistics_reference`) : dominant → déclinant
  - à la main : instances/optiflow_logistics_reference.md, champ `trajectoire`
  - _La fragmentation des flux logistiques et la priorité donnée aux circuits courts réduisent son emprise sur les échanges mondiaux, malgré son rôle initial dans la gestion de crise._
- [ ] 17. NexCore Global Infrastructure Group (`nexcore_reference`) : dominant → déclinant
  - à la main : instances/nexcore_reference.md, champ `trajectoire`
  - _L'effondrement des budgets publics et la méfiance envers les infrastructures centralisées affaiblissent sa position, malgré son rôle dans la reconstruction numérique._
- [ ] 18. Algorithmic Labor Exchange (`algorithmic_labor_exchange_reference`) : émergent → déclinant
  - à la main : instances/algorithmic_labor_exchange_reference.md, champ `trajectoire`
  - _La précarisation massive du travail et la défiance envers les plateformes algorithmiques réduisent son influence, au profit de modèles plus locaux ou coopératifs._
- [ ] 19. ⚠ Consortiums d'Extraction Minière du Bassin Congolais (`consortiums_d_extraction_miniere_du_bassin_congolais_reference`) : émergent → dominant
  - à la main : instances/consortiums_d_extraction_miniere_du_bassin_congolais_reference.md, champ `trajectoire`
  - _saut d'un cran (sans passer par ascendant) : garder, ou ramener à ascendant ; La course aux ressources critiques pour les biotechnologies et les infrastructures post-pandémie renforce leur pouvoir, malgré les tensions sociales et environnementales._

**Relations**
- [ ] 20. opposition nouvelle : Réseau des Villes-Refuge pour Travailleurs Désaugmentés ↔ Consortiums Énergétiques des Mégapoles
  - à la main : ajouter `consortiums_energetiques_des_megapoles_reference` dans `oppositions` de instances/reseau_des_villes_refuge_pour_travailleurs_desaugmentes_reference.md
  - _Les villes-refuge contestent l'emprise des consortiums énergétiques sur les territoires, promouvant des modèles décentralisés et autonomes._
- [ ] 21. alliance nouvelle : Consortium Helios ↔ Fonds Souverain Arctique Scandinave
  - à la main : ajouter `fonds_souverain_arctique_scandinave_reference` dans `alliances` de instances/consortium_helios_reference.md
  - _Helios et le fonds scandinave coordonnent leurs investissements dans les infrastructures énergétiques arctiques, mutualisant risques et ressources._
- [ ] 22. opposition nouvelle : Gouvernements du Bloc Sahélien Autonome ↔ Union Africaine Résilience (UAR)
  - à la main : ajouter `union_africaine_resilience_reference` dans `oppositions` de instances/gouvernements_du_bloc_sahelien_autonome_reference.md
  - _Le Bloc Sahélien, renforcé par sa gestion autonome de la crise, conteste l'autorité de l'Union Africaine, jugée trop dépendante des institutions multilatérales._
- [ ] 23. Rendre les relations réciproques
  - `python3 generator/fix_alliances_oppositions.py --scenario reference --reciprocite-seule --ignorer-exclus`
  - _étape 2 de Relations & lore (simulation d'abord)_

**Lore**
- [ ] 24. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section reference
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 25. Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche
  - _une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, après l'ajout des faits imposés dans lore_regles.yaml (section Lore)_
- [ ] 26. Estimer la relecture IA des fiches de plus fort impact
  - `python3 generator/audit_lore.py --scenario reference --llm --estimer --limit 10`
  - _aucun appel_
- [ ] 27. Relecture IA des 10 fiches de plus fort impact (contradictions avec l'hypothèse)
  - `python3 generator/audit_lore.py --scenario reference --llm --limit 10`
  - _payant (≈ 0,5 centime la fiche) ; après application de l'événement_
- [ ] 28. Relecture IA des fiches de la zone `europe_occidentale_reconstruite` (statut changé)
  - `python3 generator/audit_lore.py --scenario reference --llm --zone europe_occidentale_reconstruite`
  - _estimer d'abord avec --estimer ; payant_
- [ ] 29. Relecture IA des fiches de la zone `zones_grises_globales` (statut changé)
  - `python3 generator/audit_lore.py --scenario reference --llm --zone zones_grises_globales`
  - _estimer d'abord avec --estimer ; payant_

**Articles et site**
- [ ] 30. 2 article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)
  - _« « Mémoire en fragments : quand l’art défie la muraille de verre » »; « Les mémoires oubliées de Tbilissi : quand l’Histoire résiste aux algorithmes »_
- [ ] 31. Résumé du scénario
  - `python3 generator/generate_resume_scenarios.py --scenario reference`
  - _payant, un appel_
- [ ] 32. Site des revues
  - `python3 generator/chapos_revues.py`
  - _puis bash generator/publier_site.sh_

**Contrôles**
- [ ] 33. Base
  - `python3 generator/validate.py`
- [ ] 34. Lore
  - `python3 generator/audit_lore.py --scenario reference`
  - _puis étapes 2 et 3 de Relations & lore si besoin_

Entrées pour `entites_custom/queue.yaml` :

```yaml
- nom: Alliance des Villes Sanitaires Autonomes
  category: <à choisir>
  role: Réseau de villes ayant mis en place des protocoles sanitaires stricts et des infrastructures médicales
    décentralisées, devenant des pôles d'attraction pour les populations et les investissements.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  source: et_si_peste_pulmonaire_2043
- nom: Consortium des Biotechnologies Post-Pandémiques
  category: <à choisir>
  role: Alliance de laboratoires publics et privés ayant développé des traitements contre la peste pulmonaire,
    contrôlant désormais l'accès aux technologies médicales critiques.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: bruxelles_nouveau
  source: et_si_peste_pulmonaire_2043
- nom: Front des Territoires Non Connectés
  category: <à choisir>
  role: Mouvement politique et social regroupant les régions exclues des réseaux logistiques et énergétiques
    globaux, promouvant des modèles de résilience locale et de décroissance.
  etat: émergent
  scenario_ref: reference
  scenario_hint:
  - reference
  zone_hint: zones_grises_globales
  source: et_si_peste_pulmonaire_2043
```

