# Et si ? — Arrestation du Dispensaire des Grottes

*Simulation du 2026-11-11 18:29 — lecture seule, rien n'a été injecté (simulateur v8.25).*

Trois membres du Dispensaire des Grottes sont arrêtés en janvier 2098 pour « détournement de ressources médicales » après avoir permis des greffes et thérapies non autorisées. L'article du 24 mars 2098 rapporte cet événement dans le cadre du scénario new_sustainability.

**Faits imposés à la lecture IA** :
- Trois de ses membres ont été arrêtés en janvier dernier pour « détournement de ressources médicales
- Trois membres du Dispensaire des Grottes arrêtés pour « détournement de ressources médicales ».
- Événement rapporté dans le scénario new_sustainability.
- Date de l'événement : janvier 2098.

- **Apparition** : 2098.01 · **Persistance** : normale · **Propagation par la matrice** : oui
- **Effet mesuré en** : 2098.12
- **Carte** : élément déclaré sans effet territorial (`carte: non`), aucune proposition de carte retenue
- Déclaré : **sante_biotechnologies** — force 15, apaise ↓, montée sur 2 ans
- Déclaré : **gouvernance_institutions** — force 12, aggrave ↑, montée sur 3 ans
- Déclaré : **valeurs_culture_tempo_sociale** — force 10, apaise ↓, montée sur 4 ans
- Déclaré : **geopolitique_conflits** — force 8, apaise ↓, montée sur 3 ans

Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, toutes les injections existantes restant en place.

## new_sustainability

Dans le scénario new_sustainability, Arrestation du Dispensaire des Grottes n'a pas d'effet mesurable sur les variables du monde (choc absorbé ou variables déjà à leur plafond).

_(récit construit par le script)_

Effet en fin de période : négligeable (< 0,1 point, choc absorbé ou variables à leur plafond).

**Tensions** : 0 sans l'hypothèse → 0 avec.

### Liste d'application (à valider à la main — rien n'est écrit)

**Élément**
- [ ] 1. Injecter l'événement `arrets_dispensaire_grottes_2098` (entrée commune en fin de rapport)
  - `python3 generator/inject_custom_events.py --mode custom`
  - _une seule injection pour tous les scénarios de l'hypothèse_
- [ ] 2. Vérifier que la fiche porte les forces simulées (sante_biotechnologies −15, gouvernance_institutions +12, valeurs_culture_tempo_sociale −10, geopolitique_conflits −8)
  - event_instances/arrets_dispensaire_grottes_2098_new_sustainability.md, bloc impact_sur_variables ; python3 generator/trace_injection.py --slug arrets_dispensaire_grottes_2098 --type evenement --scenario new_sustainability
  - _imposées par l'entrée commune (impacts_imposes, date_imposee) : l'effet doit correspondre à cette simulation_
- [ ] 3. Gros choc : vérifier la lisibilité du moteur
  - `python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05`
  - _S19_

**Lore**
- [ ] 4. Règles à ajouter pour que l'audit du lore surveille : faits imposés de l'hypothèse
  - à la main : documentation/lore_regles.yaml, section new_sustainability
  - _comme les zones abandonnées de fortress_world (Nordgard, Koursk)_

**Fiches à relire**
- [ ] 5. Termes cherchés : Dispensaire, Grottes
  - _mot entier, sans casse ni accents ; le registre seulement après 2098.01 (chronologie)_
- [ ] 6. Événement `ouverture_dispensaire_regeneratif_geneve_2042_new_sustainability` cite « Dispensaire »
  - _Inauguration du Dispensaire Régénératif des Grottes…_

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
- id: arrets_dispensaire_grottes_2098
  description: Trois membres du Dispensaire des Grottes sont arrêtés en janvier 2098 pour « détournement
    de ressources médicales » après avoir permis des greffes et thérapies non autorisées. L'article du
    24 mars 2098 rapporte cet événement dans le cadre du scénario new_sustainability.
  portee: globale
  date_approximative: 2098
  intensite: <à choisir>
  persistance: normale
  scenarios:
  - new_sustainability
  variables_hint:
  - sante_biotechnologies
  - gouvernance_institutions
  - valeurs_culture_tempo_sociale
  - geopolitique_conflits
  variables_hint_count: 4
  source: et_si_arrets_dispensaire_grottes_2098
  faits_imposes:
    new_sustainability:
    - fait: Trois de ses membres ont été arrêtés en janvier dernier pour « détournement de ressources
        médicales
      sort: contrainte
    - fait: Trois membres du Dispensaire des Grottes arrêtés pour « détournement de ressources médicales
        ».
      sort: contrainte
    - fait: Événement rapporté dans le scénario new_sustainability.
      sort: contrainte
    - fait: 'Date de l''événement : janvier 2098.'
      sort: contrainte
  date_imposee: 2098.01
  impacts_imposes:
    new_sustainability:
    - variable: sante_biotechnologies
      delta_level: 15
      duree: 2
      polarite: -1
    - variable: gouvernance_institutions
      delta_level: 12
      duree: 3
      polarite: 1
    - variable: valeurs_culture_tempo_sociale
      delta_level: 10
      duree: 4
      polarite: -1
    - variable: geopolitique_conflits
      delta_level: 8
      duree: 3
      polarite: -1
  via_matrice_impose: true
```

