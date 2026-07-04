# Handoff — GUI Ourrassol 2098
*Session du 1er juillet 2026 — état final*

---

## Lancement

```bash
lsof -ti:5000 | xargs kill -9
pip3 install certifi   # si pas déjà fait — nécessaire pour le bouton LLM de la carte
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py
# → http://localhost:5000 dans Chrome, Cmd+Shift+R après tout remplacement de fichier
```

---

## Fichiers modifiés cette session

### `gui/`
```bash
cp app.py               "…/gui/app.py"
cp app.js               "…/gui/static/app.js"
cp index.html            "…/gui/templates/index.html"
cp pays_mapping.json    "…/gui/static/pays_mapping.json"
cp merge_pays_monde.py  "…/gui/"
```

`merge_pays_monde.py` doit être **exécuté une fois** depuis `gui/` (`python3 merge_pays_monde.py`) pour étendre `zones_pays.json` — backup automatique en `.bak`, aucune affectation existante touchée.

---

## Ce qui a été construit — P1 : onglet Carte (Leaflet)

Nouvel onglet **🗺️ Carte** dans le GUI, entièrement fonctionnel :

| Route Flask | Rôle |
|---|---|
| `GET /api/carte/affectations?scenario=x` | Zones N1 (couleur+motif) + affectation de chaque pays (fiche à jour > `zones_pays.json` > null) |
| `POST /api/carte/propose` | Appel LLM (Mistral/Claude selon le sélecteur GUI) — propose zone existante ou nouvelle, avec justification |
| `POST /api/carte/impact` | **Lecture seule.** Rapport d'impact narratif avant bascule — sous-zones orphelines, instances/événements liés, mentions textuelles, lignes du registre. Sauvegardé dans `documentation/need_action/impact_bascule_{pays}_{scenario}.md` |
| `POST /api/carte/assign` | Écrit la bascule (absorber zone existante ou créer une nouvelle) — backup `.bak`, retire proprement l'ancienne affectation, met à jour `zones_pays.json`, nettoie `zones_manquantes.yaml` |
| `POST /api/carte/ignorer` | Marque un pays "blanc intentionnel" (crée l'entrée si absente) |

**Workflow carte** : clic sur pays gris → panneau latéral → soit sélection manuelle d'une zone existante, soit "Demander une proposition (LLM)" → dans les deux cas, **"🔍 Évaluer l'impact" est obligatoire avant de pouvoir confirmer** (le bouton de bascule n'apparaît qu'après le rapport).

**Cas Royaume-Uni** : `Royaume-Uni`/`Angleterre`/`Écosse`/`Pays de Galles` = 4 entrées `pays_liste` pour un seul polygone GBR sur la carte → sélecteur intermédiaire au clic.

**Fond de carte** : chargé depuis un CDN (`world.geo.json` via jsDelivr), pas de fichier local à gérer. Matching pays FR → EN via `gui/static/pays_mapping.json` (200 entrées). Bandeau diagnostic orange si des pays ne matchent pas — à corriger dans ce fichier si besoin, aucun code à toucher.

**Couleurs de zone** : recalculées cette session — répartition uniforme sur la roue de teintes (fini le hash qui pouvait faire collision) + **motifs hachurés automatiques** dès qu'un scénario dépasse 8 zones N1, pour garantir la distinction visuelle même avec des teintes proches. Motif = couleur de zone + hachures plus sombres, angle variable selon l'index.

---

## Bugs corrigés cette session

| Bug | Fix |
|---|---|
| Dropdown "choisir une zone" vide dans le panneau carte | `_scan_n1_zones_with_desc` recevait `pipeline_dir` au lieu de `vault_root` (même bug que celui déjà documenté pour `_scan_zone_slugs`) — corrigé dans `affectations`, `propose`, `assign` |
| Bascule de zone dupliquait le pays dans l'ancienne ET la nouvelle zone | `carte_assign` retire maintenant le pays de toutes les autres zones avant de l'ajouter à la cible (actions `absorber` et `creer`) |
| Bouton LLM carte → `SSL: CERTIFICATE_VERIFY_FAILED` | Classique macOS avec Python python.org. Fix code : utilise `certifi.where()` pour le contexte SSL si le paquet est installé. **Nécessite `pip3 install certifi`** |
| Zones de couleur identique sur la carte | Couleurs hash-based → répartition uniforme de teintes + motifs (voir ci-dessus) |

---

## Pays couverts

- `pays_liste` étendu de 88 → ~200 pays (quasi-couverture mondiale) via `merge_pays_monde.py`, à exécuter une fois
- Nouveaux pays apparaissent gris (non affectés) tant qu'ils n'ont pas été traités — normal, aucune régression sur les affectations existantes

---

## Points non testés / à vérifier en premier demain

1. **Bouton LLM (`/api/carte/propose`)** — corrigé pour le SSL mais pas revérifié après `pip3 install certifi`. À retester en premier.
2. **Bandeau diagnostic pays** — avec les ~112 nouveaux pays ajoutés, il est probable que plusieurs noms anglais dans `pays_mapping.json` ne matchent pas exactement le fond de carte CDN (ex. "Macédoine du Nord" → "Macedonia" est une estimation). Ouvrir l'onglet Carte et regarder le bandeau orange en premier.
3. **Motifs de zone** — pas testés en conditions réelles (besoin d'un scénario avec >8 zones N1 pour voir les hachures apparaître). À vérifier visuellement.
4. **Rapport d'impact** — testé uniquement sur la structure de code, pas sur un vrai scénario avec de vraies sous-zones orphelines. Bon candidat pour un premier essai réel demain (ex. bouger "Russie" dans `breakdown` et lire le rapport généré).

---

## Dossier orphelin repéré

`evenements_custom/queue.yaml` existe à **deux endroits** : le bon (`generator/evenements_custom/queue.yaml`, confirmé par le code de `app.py`) et un autre à la racine du vault, non référencé par aucun script. Vérifier s'il contient des idées non migrées avant de le supprimer.

---

## Architecture routes Flask — ajouts de cette session

| Route | Méthode | Description |
|---|---|---|
| `/api/carte/affectations` | GET | Zones N1 + affectations pays pour un scénario |
| `/api/carte/propose` | POST | Proposition LLM pour un pays non affecté |
| `/api/carte/impact` | POST | Rapport d'impact narratif (lecture seule) |
| `/api/carte/assign` | POST | Écrit une bascule de zone |
| `/api/carte/ignorer` | POST | Marque blanc intentionnel |

(Liste complète des routes précédentes toujours valide — voir `HANDOFF_30juin.md`.)

---

## Prochaine session — pistes

- Reprendre le fil P7 (chantier restructure zones) — la carte gère déjà les bascules pays→zone N1, mais pas le split/merge/reparent de zones elles-mêmes
- Étendre le rapport d'impact pour couvrir aussi les **entités** (actuellement seulement instances/événements) si l'usage réel s'avère nécessaire
- Documenter l'onglet Carte + le rapport d'impact dans `user_manual_updated.md`
- P2 toujours en attente : lancer `complete_geographie_coverage.py --review` puis `--apply` sur les 5 scénarios restants (`fortress_world`, `new_sustainability`, `eco_communalism`, `policy_reform`, `reference`)
