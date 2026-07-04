# Backlog — GUI Ourrassol 2098
*Mis à jour le 4 juillet 2026*

---

## À vérifier en tout premier (avant toute nouvelle feature) 🔴
**Durée estimée : 10min**

- [ ] Vérifier que `generator/complete_geographie_coverage.py` contient bien le dernier fix (groupement de nouvelles zones dans un même batch — cf. HANDOFF_4juillet.md, bug #9). Commande de vérification :
  ```bash
  grep -c "nouvelles_zones_ce_batch" complete_geographie_coverage.py
  ```
  Doit renvoyer `2` ou plus. Si `0`, redéployer la dernière version.
- [ ] `python3 check_zones_coherence.py --all` — état des lieux avant de continuer

---

## P2bis — Finaliser la couverture géographique (suite session 4 juillet) 🔴
**Durée estimée : 1h-1h30 (selon rate limiting)**

Le fix de `get_missing_pays()` a révélé beaucoup plus de pays sans zone que ce qui avait été traité initialement (109 au lieu de 36 pour certains scénarios). À relancer proprement sur 5 scénarios (`reference` est déjà bon) :

```bash
for s in breakdown eco_communalism fortress_world policy_reform new_sustainability; do
  echo "=== $s ==="
  python3 complete_geographie_coverage.py --scenario "$s" --review
done
```

Puis, pour chaque fichier `coverage_proposals_*.yaml` généré :
1. Ouvrir dans VS Code, survol rapide (chercher les incohérences géographiques flagrantes type "Équateur → Afrique")
2. Vérifier les rejets automatiques (`valide: false`) avec la commande d'extraction ci-dessous — s'assurer qu'il ne reste que de vrais problèmes (rate limit résiduel, incohérence réelle), pas des faux positifs du bug #9
3. `--apply` une fois validé

```bash
python3 -c "
import yaml, glob
for f in sorted(glob.glob('coverage_proposals_*.yaml')):
    data = yaml.safe_load(open(f, encoding='utf-8'))
    rejets = [a for a in data.get('affectations', []) if a.get('valide') is False]
    if rejets:
        print(f'=== {f} ({len(rejets)} rejeté(s)) ===')
        for a in rejets:
            print(f\"  - {a.get('pays')} : {a.get('avertissement') or a.get('justification', '')[:100]}\")
"
```

Terminer par :
```bash
python3 check_zones_coherence.py --all
```
Doit être propre (0 pays réel sans zone N1, parsing OK) sur les 6 scénarios.

---

## P2ter — Corriger les 32 pays "sous-zone sans N1" 🟡
**Durée estimée : 20-30min**

Pays déjà présents dans le vault via une sous-zone narrative, mais sans affectation N1 — distinct de P2bis (ceux-ci ont déjà *une* zone, juste pas la bonne granularité). Via l'onglet Carte, bouton "🚫 Ignorer" (rapide) ou réaffectation manuelle :

| Scénario | Pays concernés |
|---|---|
| fortress_world | — (aucun) |
| new_sustainability | Espagne, Belgique, Portugal, Vietnam, Cambodge, Nigeria, Burkina Faso, Corée du Sud, France |
| eco_communalism | Groenland, Pologne, République tchèque, Chine |
| policy_reform | Sénégal, Singapour, Groenland |
| reference | Mali, Niger, Tchad, Kirghizistan, Tadjikistan, Afghanistan, Soudan, Cambodge, Tuvalu, Kiribati, Îles Marshall, Italie, République du Congo |
| breakdown | Estonie, Lettonie, Lituanie |

---

## P2quater — Décider du modèle LLM par défaut pour Carte / Coverage 🟡
**Durée estimée : 5min de réflexion + réglage config.json**

`mistral-small` (modèle par défaut actuel) confabule des erreurs géographiques grossières et confiantes. Options :
- `claude-sonnet-4-6` (fiable, plus cher)
- `mistral-large` (compromis)

À trancher puis mettre à jour `config.json` (`llm.provider` / `llm.model_mistral`).

---

## P1bis — Documenter l'onglet Carte + rapport d'impact 🟡
**Durée estimée : 30min**

Ajouter au `user_manual_updated.md` (voir aussi `USER_MANUAL_carte_et_couverture_4juillet.md` livré cette session, à fusionner) :
- Workflow carte (clic → évaluer impact → confirmer)
- Les 5 routes `/api/carte/*`
- Le cas Royaume-Uni (4 entrées pour 1 polygone)
- `merge_pays_monde.py` et son usage
- Workflow `complete_geographie_coverage.py` (review/apply)
- `check_zones_coherence.py`

---

## P3 — Tests end-to-end formulaires guidés 🟡
**Durée estimée : 1h**

- Generate : scénario → zones rafraîchissent → sauvegarder → lancer → vérifier article
- Generate series : chips thématiques → sauvegarder → lancer
- Create entities (custom) : formulaire → Ajouter à queue → vérifier entites_custom/queue.yaml → Lancer
- Inject events (custom) : zone_hint pays 2026 → lookup → vérifier injection

---

## P4 — Test streaming SSE 🟢
**Durée estimée : 30min**

- `validate.py --dry-run` depuis le GUI → log SSE visible
- `enrich_minimal.py --limit 2 --dry-run` → slug_select + streaming

---

## P5 — Fix pérenne décorateur dashboard 🟢
**Durée estimée : 15min**

Le `@app.route("/api/dashboard")` est régulièrement mangé par les patches.
Solution : séparer les routes dans `routes_dashboard.py` importé par `app.py`.

---

## P6 — scripts_config.json vérification complète 🟢
**Durée estimée : 1h**

Croiser les options de chaque script avec le code source Python.
Priorité : `generate_manual.py`, `undo_custom.py`, `extract_phantom_slugs.py`.

---

## P7 — Restructure zones (pipeline) ⚪
**Durée estimée : 2-3h**

Outil split/merge/reparent/rename de zones avec propagation complète dans le vault.
*Note (1er juillet) : la carte gère déjà les bascules pays → zone N1 individuelles avec rapport d'impact. Ce chantier reste nécessaire pour les opérations sur les zones elles-mêmes (fusionner deux zones N1, renommer un slug partout, etc.) — pas couvert par l'onglet Carte.*

---

## P8 — Enrich 426 fichiers officialise_minimal ⚪
**Script existant (`enrich_minimal.py`)**

Lancer après validation du pipeline. Coût API estimé ~$37.

---

## P9 — Nettoyage dossier orphelin evenements_custom ⚪
**Durée estimée : 10min**

Un `evenements_custom/queue.yaml` existe à la racine du vault, en plus de celui dans `generator/` (le seul lu par le code). Vérifier s'il contient des idées non migrées, les copier dans `generator/evenements_custom/queue.yaml` si oui, puis supprimer le dossier orphelin.

---

## P10 — Rapport d'impact : étendre aux entités ⚪
**Durée estimée : 1h (si besoin avéré)**

Le rapport d'impact (`/api/carte/impact`) couvre actuellement `instances/` et `event_instances/` mais pas `entites/` (archétypes, généralement peu liés à un pays précis). À évaluer après usage réel — probablement pas nécessaire si les entités restent génériques.

---

## P11 — Intégrer check_zones_coherence.py au GUI ⚪
**Durée estimée : 15-20min**

Script actuellement en CLI pure (`generator/check_zones_coherence.py`, lecture seule).
Diagnostique : parsing YAML des fiches geographie/{scenario}.md + pays réels sans
zone N1 (attachés uniquement à une sous-zone). À lancer après chaque `--apply` de
`complete_geographie_coverage.py` ou session de travail sur la carte.

Ajouter une entrée dans `scripts_config.json` pour l'avoir en un clic depuis le
sidebar GUI, comme les autres scripts. Pas urgent — usage CLI actuel suffisant.
Peut être fusionné avec P6.

---

## Notes importantes

**complete_geographie_coverage.py** — workflow obligatoire :
1. `--review` → génère `coverage_proposals_{scenario}.yaml`
2. Valider dans VS Code (mettre `valide: false` sur les mauvaises propositions)
3. `--apply` → écrit dans la fiche + zones_pays.json
4. `check_zones_coherence.py --scenario X` → confirmer la cohérence

⚠️ Depuis le 4 juillet : le script inclut un délai de 8s entre batches (rate limiting) — les runs sont plus longs mais plus fiables. Ne pas interrompre en cours de route.

**Bascule de zone via la carte** — workflow désormais obligatoire :
1. Clic sur le pays (gris ou déjà coloré)
2. Choisir une zone (manuel ou proposition LLM)
3. **"🔍 Évaluer l'impact" obligatoire** — rapport en lecture seule, sauvegardé dans `documentation/need_action/impact_bascule_{pays}_{scenario}.md`
4. Le bouton de confirmation n'apparaît qu'après le rapport

**Clé API** — si erreur `Illegal header value b'Bearer '` : la variable d'environnement n'est pas chargée dans le terminal courant. `source ~/.zshrc` avant de relancer.

**Modèle LLM** — `mistral-small` déconseillé pour la carte/coverage (raisonnement géographique peu fiable). Préférer `claude-sonnet-4-6` ou `mistral-large`.
