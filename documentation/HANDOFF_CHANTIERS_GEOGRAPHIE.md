# HANDOFF — Fusion chantiers_geographie.yaml (à poursuivre dans un nouveau chat)

*Rédigé le 25 juillet 2026, en milieu de chantier. À uploader dans le nouveau chat
avec les 4 fichiers déjà produits (voir §3).*

---

## 1. Contexte — pourquoi ce chantier

Après avoir construit P24 étape C (C.1 à C.4, plus tôt le 25 juillet — diagnostic
patron spatial, générateur top-down, intégration GUI), un problème d'usage est
remonté : trop de fichiers YAML séparés à gérer à la main (`patron_spatial_
suspectes.yaml`, `zones_proposees_topdown_{scenario}.yaml` x6, `zones_manquantes.
yaml`, plus `coverage_proposals_{scenario}.yaml` x6 d'un script plus ancien).

**Décision actée** : tout fusionner dans **un seul fichier**,
`documentation/need_action/chantiers_geographie.yaml`, avec un vocabulaire de
statuts simplifié à 3 valeurs (`a_traiter` / `ignore` / `traite`), et à terme un
onglet GUI "Chantiers" pour remplacer l'édition manuelle de YAML.

**Décision additionnelle** : `complete_geographie_coverage.py` (script plus ancien,
gère aussi les pays sans zone mais sans conscience du patron spatial) est **retiré
de l'usage actif** — son rôle est maintenant entièrement couvert par C.3/C.4, en
mieux. Pas supprimé, juste sorti de la sidebar GUI (pas encore fait, voir §5).

---

## 2. Schéma retenu (`chantiers.py`, déjà construit)

```yaml
chantiers:
- id: <scenario>__<cible>              # identifiant stable (slugifié)
  scenario: breakdown
  type: zone_suspecte | pays_sans_zone
  cible: geneve_bunker_institutions    # slug de zone OU nom de pays
  probleme: "texte du diagnostic"
  source_diagnostic: patron_spatial | origine_reelle | zones_coherence
  date_detection: "2026-07-25"
  statut: a_traiter | ignore | traite
  proposition: null | {...zone complète, schéma validate_zone()...}
  proposition_approuvee: false         # true = relu et approuvé, prêt pour --apply-topdown
  date_proposition: null | "2026-07-25"
  date_traitement: null | "2026-07-25"
```

**Statuts** :
- `a_traiter` (défaut) — pas encore examiné.
- `ignore` — examiné, choix narratif légitime, la zone ne change pas, plus jamais réaffiché.
- `traite` — la zone A ÉTÉ MODIFIÉE (proposition appliquée ou édition manuelle), problème réglé.

**`proposition_approuvee`** — ajouté pour garder un geste de validation explicite
malgré la fusion en un seul fichier : une proposition générée reste `false` tant
qu'elle n'a pas été relue et approuvée (à la main dans le YAML, ou via le futur
bouton GUI). `--apply-topdown` (et le futur bouton "Appliquer") ne consomment que
`chantiers_prets_a_appliquer()` (statut `a_traiter` + `proposition` non nulle +
`proposition_approuvee: true`).

---

## 3. Fichiers déjà construits et cohérents (à uploader dans le nouveau chat)

1. **`chantiers.py`** (nouveau module partagé) — schéma, `ajouter_chantier()`,
   `get_chantier()`, `mettre_a_jour_chantier()`, `chantiers_eligibles()`,
   `chantiers_prets_a_appliquer()`. Syntaxe vérifiée.
2. **`check_patron_spatial_coherence.py`** — migré vers `chantiers.py`
   (`--write-chantiers` remplace `--write-suspectes`). Syntaxe vérifiée.
3. **`check_origine_reelle_coherence.py`** — migré vers `chantiers.py`
   (`--write-chantiers` remplace `--write-zones-manquantes`). Syntaxe vérifiée.
4. **`check_zones_coherence.py`** — migré : lit les chantiers `pays_sans_zone`
   pour l'obsolescence (`--marquer-resolus`, nouveau, marque `traite`
   automatiquement quand le pays a déjà une zone N1 — seul cas sans jugement
   narratif nécessaire), et écrit maintenant lui-même des chantiers pour les
   pays totalement absents (`--write-chantiers`). Syntaxe vérifiée.

**Aucun de ces 4 fichiers n'a encore été testé sur le vault réel** — contrairement
à tout le reste de la session (C.1-C.4), cette partie est seulement vérifiée
syntaxiquement (`ast.parse`), jamais exécutée en vrai. À tester en priorité avant
de continuer à construire dessus.

---

## 4. Ce qui reste à faire, dans l'ordre

### 4.1 — `generer_zones_topdown.py` (C.3) — pas commencé
Doit être réécrit pour :
- Remplacer `_zones_suspectes_eligibles()` et `_pays_sans_zone()` (détection en
  dur) par `chantiers.chantiers_eligibles(scenario, type_=...)`.
- `--review-topdown` : génère la proposition (inchangé, via `zoning_topdown.
  generer_zone_topdown()`), puis l'attache à l'entrée existante via
  `chantiers.mettre_a_jour_chantier(scenario, cible, proposition=..., 
  date_proposition=...)` — **plus de fichier `zones_proposees_topdown_
  {scenario}.yaml` séparé**.
- `--apply-topdown` : consomme `chantiers.chantiers_prets_a_appliquer()`
  au lieu de lire un fichier de review. Après application réussie :
  `chantiers.mettre_a_jour_chantier(scenario, cible, statut="traite",
  date_traitement=...)`.
- La logique d'écriture elle-même (`_appliquer_pays_sans_zone`,
  `_appliquer_zone_suspecte`, l'appel à `reparenter_sous_zones_orphelines.py`)
  reste inchangée — seule la source de lecture/écriture des chantiers change.

### 4.2 — Script de migration (une fois, pas commencé)
Importer l'existant dans `chantiers_geographie.yaml` sans rien perdre :
- `patron_spatial_suspectes.yaml` → chantiers `type: zone_suspecte`
  (mapping statuts : `a_traiter`→`a_traiter`, `accepte_tel_quel`→`ignore`,
  `corrige_manuellement`/`corrige_via_c2`→`traite`, `en_attente_c2`→`a_traiter`).
- `zones_manquantes.yaml` → chantiers `type: pays_sans_zone`
  (`statut: blanc_intentionnel`→`ignore`, sinon `a_traiter`).
- `zones_proposees_topdown_{scenario}.yaml` (x6, si encore présents) → attacher
  leur `proposition` aux chantiers correspondants déjà migrés, avec
  `proposition_approuvee` = valeur de leur `valide: true/false`.

### 4.3 — `scan_geographie_complet.py` — pas commencé
Harmoniser les noms de flags (`--write-suspectes`/`--write-zones-manquantes`
→ `--write-chantiers` uniformément), mettre à jour la 6e étape optionnelle pour
qu'elle propage toujours `--write-chantiers` plutôt que les anciens noms.

### 4.4 — `scripts_config.json` — pas commencé
- Retirer/désactiver l'entrée `complete_geographie_coverage` de la sidebar
  (ou la relabelliser "déprécié — voir Générer zones top-down").
- Mettre à jour les entrées déjà ajoutées aujourd'hui (`check_patron_spatial_
  coherence`, `generer_zones_topdown`) pour refléter `--write-chantiers`.

### 4.5 — Onglet GUI "Chantiers" — pas commencé, le morceau le plus visible
Nouvel onglet listant `chantiers.chantiers_eligibles()` (statut `a_traiter`),
avec pour chaque entrée :
- Le problème en clair.
- Si `proposition` existe : aperçu + bouton "✓ Approuver" (passe
  `proposition_approuvee` à `true`) puis "Appliquer" (ou un seul bouton qui fait
  les deux) ; sinon bouton "🧭 Générer une proposition" (appelle
  `/api/carte/generer_zone_topdown`, déjà existante, réutilisable telle quelle).
- Bouton "🗂️ Laisser tel quel" → `chantiers.mettre_a_jour_chantier(..., 
  statut="ignore")`.
Nécessite : nouvelles routes Flask (lister les chantiers, approuver, ignorer,
appliquer) + nouvel onglet dans `index.html`/`app.js`.

---

## 5. Points de vigilance à ne pas perdre

- **`chantiers.py` et les 3 scripts migrés n'ont jamais été testés en vrai** —
  premier geste à faire dans la nouvelle session, avant de construire la suite.
- **`coverage_proposals_{scenario}.yaml`** (complete_geographie_coverage.py)
  reste hors scope de la fusion (décision actée) — mais le script doit quand
  même être retiré de la sidebar pour éviter la confusion avec C.3/C.4 sur le
  même cas d'usage (pays sans zone).
- **Ne jamais faire écrire chantiers.py automatiquement un changement de statut
  `a_traiter`→autre chose sans un geste explicite** (bouton GUI ou édition
  manuelle) — seule exception délibérée : `--marquer-resolus` dans
  `check_zones_coherence.py`, qui ne fait que marquer `traite` un cas où le
  problème n'existe plus objectivement (le pays a une zone), pas un jugement
  narratif.
- **Fichiers legacy à ne PAS supprimer tout de suite** une fois la migration
  faite (`patron_spatial_suspectes.yaml`, `zones_manquantes.yaml`,
  `zones_proposees_topdown_*.yaml`) — les garder comme filet de sécurité jusqu'à
  ce que `chantiers_geographie.yaml` ait fait ses preuves sur quelques sessions.
