# P24 étape C — Scoping du générateur top-down
*Rédigé le 25 juillet 2026 — suite directe d'`APPROCHE_ZONING_GEOGRAPHIE_SCENARIOS.md` (13 juillet), §5-6. Décisions actées avant tout code, à intégrer au prochain `HANDOFF_CONSOLIDE.md`/`BACKLOG_CONSOLIDE.md`.*

---

## 1. Rappel de l'objectif (P24)

La 3ème passe géographique du pipeline (`complete_geographie_coverage.py`) est **top-down mais naïve** : elle juge un rattachement de pays à une zone sur la seule ressemblance textuelle, sans jamais revalider contre la logique systémique du scénario. C'est la cause des 4 anomalies trouvées le 13 juillet (Barcelone-Hub et Corridor ibérique énergétique dans `ameriques_reconfigurees`, Cracovie et Bassin Pannonien dans `arc_eurasien_central`).

- **Étape A** (livrée 14 juillet) : `patrons_spatiaux.py` + `extract_state_logic.py` — formalise le patron spatial des 6 scénarios depuis le vault.
- **Étape B** (livrée 15 juillet) : garde-fou d'avertissement intégré à `complete_geographie_coverage.py` — compare une proposition de rattachement au patron avant confirmation.
- **Étape C** (ce document, pas commencée) : le générateur top-down proprement dit — générer directement des zones qui incarnent le patron spatial du scénario pour une région mal couverte, plutôt que de forcer un rattachement à l'existant.

B empêche les mauvais rattachements *vers l'existant* ; C doit permettre de créer *la bonne zone dès le départ* quand rien d'existant ne convient.

---

## 2. Décisions d'architecture actées (25 juillet)

| Question | Décision |
|---|---|
| Où vit le générateur ? | **Hybride** — fonction cœur partagée, appelée en CLI batch et depuis le GUI |
| Périmètre de déclenchement | **Les deux dès le départ** — pays sans zone ET zones existantes suspectes |
| Mode d'écriture | **Les deux** — review YAML pour le CLI, pré-remplissage formulaire pour le GUI |
| Appel GUI → fonction cœur | **Subprocess + JSON** — cohérent avec le pattern existant (le GUI appelle déjà tous les scripts `generator/` en sous-processus), pas d'import direct entre les deux codebases |

---

## 3. Scope détaillé

### C.1 — `check_patron_spatial_coherence.py` (diagnostic, indépendant)
Nouveau script de diagnostic, 5ᵉ script de `scan_geographie_complet.py`. Pour chaque zone N1 du scénario, compare sa `description`/son `type` au `state_logic` d'`organisation_territoires` pour ce scénario, via LLM. Avertissement uniquement, jamais bloquant — même philosophie que le garde-fou §4 de la synthèse du 13 juillet (le taux de faux positifs d'une première heuristique mots-clés était de 5/9, un signal qualitatif comme celui-ci ne doit jamais bloquer automatiquement).

**Dépendance** : étape A uniquement. Peut être livré et donner de la valeur seul, sans attendre C.2/C.3/C.4.

### C.2 — `generator/zoning_topdown.py` (fonction cœur)
Nouveau module dédié plutôt qu'une extension de plus sur `complete_geographie_coverage.py` (qui a déjà 3 responsabilités). Fonction principale :

```
generer_zone_topdown(scenario, region_cible, raison) -> proposition JSON
```

- `raison` : `"pays_sans_zone"` ou `"zone_suspecte"` (sortie de C.1)
- Sources du prompt (déjà écrites dans le vault, cf. §5 d'`APPROCHE_ZONING_GEOGRAPHIE_SCENARIOS.md`) :
  1. `scenarios/{scenario}.md` — synthèse systémique globale
  2. `variables/organisation_territoires.md → states.{scenario}` — patron spatial
  3. `variables/geopolitique_conflits.md → states.{scenario}` — structure des blocs/tensions, pour peupler `relations.allies`/`relations.rivaux` dès la création
  4. Éventuellement d'autres variables selon le contexte (`energie_ressources_critiques`, `frontieres_du_systeme` si zone orbitale)
- Consigne centrale du prompt : ne pas générer une zone plausible dans l'absolu, mais répondre à "comment le patron spatial de ce scénario s'est-il concrétisé dans *cette* région, avec quelle friction/réinterprétation locale" (leçon Futuribles/d'Iribarne — l'universel ne s'implante jamais identiquement).
- Sortie : proposition de zone complète (nom, slug, description, type, `origine_reelle`, `relations.allies/rivaux`), conforme au schéma déjà utilisé par la création manuelle de zone niveau 1 (P7 étape 2 : `ZONE_TYPES`/`ZONE_STATUTS`/`TYPE_ENTITE_REELLE`).
- Passe par le garde-fou (étape B) avant toute écriture, exactement comme une création manuelle.

**Dépendance** : étapes A + B. Bloque C.3 et C.4.

### C.3 — Mode CLI (batch)
`--review-topdown` / `--apply-topdown` sur `complete_geographie_coverage.py` (ou script séparé si l'ampleur le justifie une fois en cours de construction — à trancher en codant, pas maintenant).

- Source des cas : `get_missing_pays()` existant (pays sans zone) + sorties de C.1 (zones suspectes)
- Workflow identique au reste du pipeline : YAML de propositions (`valide: false` par défaut) → validation manuelle dans VS Code → `--apply-topdown`
- Réutilise `_write_zones_pays()` pour la double écriture `geographie/{scenario}.md` + `zones_pays.json` — **point de vigilance direct**, voir §4 du handoff du 15 juillet sur ce sujet précis

**Dépendance** : C.2.

### C.4 — Mode GUI (geste ponctuel)
Deux points d'entrée dans l'onglet Carte :
- Clic sur un pays gris → bouton "🧭 Générer proposition top-down" (en plus du rattachement à l'existant déjà proposé)
- Zone N1 flaguée suspecte par C.1, visible dans l'arbre → même bouton

Appelle C.2 via subprocess + échange JSON (décision §2), pré-remplit le formulaire de création de zone niveau 1 déjà construit (P7 étape 2) plutôt que d'écrire directement — validation humaine bouton par bouton avant écriture réelle.

**Dépendance** : C.2. Peut être construit en parallèle de C.3 une fois C.2 stable, puisque les deux consomment la même sortie JSON.

---

## 4. Ordre de construction recommandé

1. **C.1** — indépendant, le plus petit, donne de la valeur immédiatement (visibilité sur les zones suspectes sans attendre le reste)
2. **C.2** — le vrai cœur technique, bloque C.3 et C.4
3. **C.3 et C.4** — en parallèle une fois C.2 stable

---

## 5. Points de vigilance à ne pas oublier en construisant

- **Double écriture `zones_pays.json`/`geographie/{scenario}.md`** — toute nouvelle fonction d'écriture (C.3 comme C.4) doit suivre le réflexe déjà établi pour rename/split (`_rename_zone_in_zones_pays`, `_split_zone_in_zones_pays`) : chercher l'équivalent existant avant d'écrire une nouvelle logique, écrire immédiatement plutôt qu'en différé.
- **Collision slug zone/entité** (ex. `nairobi_crrc`) — toute génération de nouveau slug de zone doit vérifier `entites/{slug}.md` avant de considérer le slug comme libre.
- **`gui/app.py` et `generator/` sont deux codebases séparées** — confirmé pour C.4 : l'appel se fait en subprocess + JSON, pas en import direct. Toute logique de tokenisation/normalisation utile aux deux doit être dupliquée consciemment si besoin, pas supposée partagée.
- **Consignes de prompt jamais auto-appliquées** — le filtre "conforme au schéma P7 étape 2" doit être vérifié en sortie du LLM (C.2), pas seulement demandé dans le prompt (leçon des bugs #18/#34).
- **`patron_spatial_suspectes.yaml` (C.1, livré le 25 juillet) ne progresse jamais tout seul** — le script n'écrit `a_traiter` qu'une fois, à la création de l'entrée ; il ne modifie jamais un statut existant (`accepte_tel_quel`/`corrige_manuellement`/`en_attente_c2`), et ne le propose jamais à la place de David. Sans revue manuelle périodique du fichier, les entrées s'accumulent en `a_traiter` et sont réaffichées en avertissement actif à chaque `--all`, indéfiniment. Le fichier a besoin d'un geste de revue régulier, comme `zones_manquantes.yaml` — mais rien dans le pipeline ne le rappelle automatiquement pour l'instant.

---

*Prêt à démarrer la construction de C.1 à la prochaine session.*
