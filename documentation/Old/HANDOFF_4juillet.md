# Handoff — GUI Ourrassol 2098
*Session du 4 juillet 2026 — état final*

---

## Résumé de la session

Session de débogage intensive sur l'onglet Carte et le script `complete_geographie_coverage.py`, déclenchée par un problème de légende incohérente sur le scénario `reference`. **9 bugs distincts identifiés et corrigés**, dont un problème de corruption YAML qui affectait potentiellement les 6 scénarios.

---

## Bugs corrigés (confirmé)

### 1. Corruption YAML dans les fiches geographie/{scenario}.md
**Symptôme** : carte entièrement bleue, légende vide, `zones_n1: []` dans l'API.
**Cause** : `save_geo_file()` dans `complete_geographie_coverage.py` faisait deux `yaml.dump()` séparés (`indent=4` sur les zones) puis recollait le tout avec une réindentation manuelle ligne par ligne, cassant l'alignement entre le tiret de liste et ses clés sœurs (`-   slug:` vs `    nom:`).
**Fix** : un seul `yaml.dump()` sur le frontmatter complet, `indent=2`. PyYAML gère l'alignement lui-même.
**Réparation manuelle effectuée** : `geographie/reference.md` corrigé via `sed` en urgence avant le fix du script (60 zones concernées).

### 2. Prompt LLM incomplet pour les propositions de zone (carte)
**Symptôme** : proposition LLM absurde (Équateur → Union Africaine de Résilience).
**Cause** : `carte_propose()` dans `app.py` ne montrait au LLM que la description narrative de chaque zone, jamais la liste des pays déjà affectés — le LLM n'avait aucun signal géographique fiable pour certaines zones (ex. description de "Amériques Multipolaires" centrée sur la crise US, sans lister les pays membres).
**Fix** : ajout de la liste des pays déjà affectés (jusqu'à 10) entre crochets pour chaque zone dans le prompt, + instruction renforcée pour prioriser ce signal.

### 3. Modèle LLM sous-dimensionné pour ce type de raisonnement
**Constat** : `mistral-small` (modèle par défaut dans `config.json`) confabule des erreurs géographiques grossières et confiantes ("l'Équateur est géographiquement proche de l'Afrique du Sud").
**Recommandation** : basculer sur `claude-sonnet-4-6` ou a minima `mistral-large` pour les tâches de la carte et de `complete_geographie_coverage.py`. Non corrigé dans le code — c'est un réglage (`config.json` ou sélecteur GUI), à décider par David.

### 4. `_build_origine_reelle_index()` fragile (ordre du fichier)
**Cause** : l'index pays→zone (utilisé par la carte) prenait le premier slug rencontré dans l'ordre d'écriture du YAML, sans distinguer zone N1 et sous-zone. Un pays listé dans une sous-zone narrative (ex. une ville) AVANT sa zone N1 dans le fichier aurait été mal résolu.
**Fix** : l'index priorise désormais explicitement les zones N1, quel que soit l'ordre d'écriture du fichier.

### 5. Validation "absorber" trop permissive (toutes zones, tous niveaux)
**Cause** : `apply_affectations()` et `process_scenario_review()` validaient un `zone_slug` proposé par le LLM contre **toutes** les zones (N1 + sous-zones), alors que le LLM ne voit que les zones N1 dans son prompt. Un slug halluciné coïncidant par hasard avec une sous-zone existante était accepté à tort → pays absorbé dans une zone invisible sur la carte.
**Fix** : validation restreinte aux slugs de zones N1 uniquement, dans les deux fonctions.

### 6. `get_missing_pays()` ne détectait pas tous les pays sans zone
**Cause** : la fonction itérait sur les clés déjà présentes dans `zones_pays.json[scenario]`. Les ~112-114 pays ajoutés par `merge_pays_monde.py` à `pays_liste` n'avaient jamais reçu d'entrée `null` correspondante dans chaque dict de scénario — ils étaient donc invisibles pour le script, jamais soumis au LLM.
**Fix** : la fonction se base désormais sur `pays_liste` complet. Conséquence directe : le nombre de pays détectés comme "manquants" est passé de 36 à 109 pour `fortress_world`/`reference`.

### 7. Clé API vide (`Illegal header value b'Bearer '`)
**Cause** : variable d'environnement (`MISTRAL_API_KEY`) non chargée dans le terminal (`.zshrc` pas resourcé). Pas un bug de code.
**Fix côté utilisateur** : `source ~/.zshrc` avant de lancer le script. Revenu deux fois dans la session — David à surveiller à chaque nouveau terminal.

### 8. Rate limiting (429) en cours de `--review`
**Symptôme** : `Status 429 Rate limit exceeded` sur plusieurs batches consécutifs (`eco_communalism`, `new_sustainability`, `policy_reform`), entraînant des pays marqués `a_revoir`/`valide: false`.
**Fix** : ajout d'un délai de 8 secondes (`DELAY_ENTRE_BATCHS`) entre chaque appel LLM, dans les deux boucles de traitement par batch (mode direct et mode `--review`).

### 9. Faux rejets sur les groupements de nouvelles zones
**Symptôme** : de nombreux pays rejetés (`avertissement: Slug inconnu ou hors-N1`) alors que le LLM proposait un comportement cohérent — grouper plusieurs pays sous une même nouvelle zone logique (ex. Angleterre en `nouvelle_zone: archipel_britannique_insulaire`, puis Écosse et Pays de Galles en `absorber` vers ce même slug, dans le même batch).
**Cause** : la validation ne connaissait que les zones existant **avant** l'appel LLM — pas les nouvelles zones proposées plus tôt dans la même réponse.
**Fix** : suivi des slugs de nouvelles zones proposées au fil du batch, dans `process_scenario_review()` ET `apply_affectations()` (le même bug existait dans les deux).

---

## Fichiers modifiés et déployés cette session

| Fichier | Emplacement déployé | Statut |
|---|---|---|
| `app.py` | `gui/app.py` | ✅ Déployé, confirmé identique par re-upload |
| `complete_geographie_coverage.py` | `generator/complete_geographie_coverage.py` | ✅ Déployé (plusieurs itérations — vérifier que la dernière version avec le fix #9 est bien en place) |
| `check_zones_coherence.py` | `generator/check_zones_coherence.py` (nouveau) | ✅ Créé, à copier si pas déjà fait |

**⚠️ Point de vigilance** : `complete_geographie_coverage.py` a été patché plusieurs fois dans la session (fixes #1, #5, #6, #8, #9 tous dans ce fichier). Vérifier que la version actuellement dans `generator/` contient bien le fix #9 (le plus récent) avant de relancer quoi que ce soit — sinon les faux rejets sur les nouvelles zones groupées reviendront.

---

## Nouveau script : check_zones_coherence.py

Diagnostic en lecture seule (ne modifie jamais rien) :
- Vérifie que chaque `geographie/{scenario}.md` parse correctement en YAML
- Détecte les vrais pays (`pays_liste`) rattachés uniquement à une sous-zone, sans zone N1

```bash
python3 check_zones_coherence.py --scenario reference
python3 check_zones_coherence.py --all
```

Actuellement CLI uniquement, pas intégré au GUI (voir backlog P11).

---

### 10. Désynchronisation zones_pays.json / fiches réelles
**Symptôme** : après un `check_zones_coherence.py --all` tout vert, un pays (Arctique) manquant dans le dashboard s'est révélé introuvable dans la fiche — révélant que le check lui-même avait un angle mort (ne détectait que les pays présents ailleurs mal classés, pas les pays totalement absents).
**Cause plus profonde, découverte en creusant** : `zones_pays.json` contenait des valeurs non-null **obsolètes** pour ~55 pays à travers les 6 scénarios (héritées d'une génération antérieure, jamais resynchronisées avec les fiches `geographie/*.md` réelles). `get_missing_pays()` faisant confiance à ce fichier, ces pays n'ont **jamais** été soumis au LLM par `complete_geographie_coverage.py`, malgré le fix #6 — ils étaient invisibles à un niveau encore plus en amont.
**Fix en deux parties** :
- `check_zones_coherence.py` amélioré : détecte maintenant aussi les pays totalement absents de toute zone (pas seulement les mal classés), avec une correspondance tolérante aux variantes narratives (`ALIASES` — ex. "États-Unis d'Amérique" = "États-Unis") sans risquer de confondre des pays réellement distincts (Guinée ≠ Guinée équatoriale, Congo ≠ RDC, Soudan ≠ Soudan du Sud).
- Nouveau script `regenerate_zones_pays.py` : reconstruit `zones_pays.json` intégralement depuis les fiches (source de vérité), avec backup automatique. Lancé une fois, a corrigé 55 désynchronisations d'un coup.

**Après ce fix, un nouveau passage complet de P2 (review + apply sur les 6 scénarios) a permis de traiter les vrais trous révélés.** Les 2 derniers cas résiduels (Arctique, Groenland sur `breakdown`) ont été corrigés manuellement via `add_pays_to_zone.py`.

---

## État final de la couverture géographique (P2) — confirmé propre

**✅ TERMINÉ, confirmé par `check_zones_coherence.py --all` (version finale, 4 vérifications) :**

```
=== breakdown ===            ✓ 89 zones (36 N1)  — cohérent
=== fortress_world ===       ✓ 71 zones (21 N1)  — cohérent
=== new_sustainability ===   ✓ 60 zones (15 N1)  — cohérent
=== eco_communalism ===      ✓ 87 zones (42 N1)  — cohérent
=== policy_reform ===        ✓ 61 zones (15 N1)  — cohérent
=== reference ===            ✓ 61 zones (16 N1)  — cohérent
=== zones_manquantes.yaml ===✓ vide
```

Tous les pays de `pays_liste` ont désormais une vraie zone N1 dans chacun des 6 scénarios, et `zones_pays.json` est resynchronisé avec les fiches. Rien à reporter sur ce sujet à la prochaine session.

---

## Nouveau script : add_pays_to_zone.py

Utilitaire créé en fin de session pour rattacher rapidement un pays à sa vraie zone N1 parente, quand il n'était présent que dans une sous-zone (cas typique détecté par `check_zones_coherence.py`). Vérifie le niveau de la zone cible, évite les doublons, backup `.bak` avant écriture.

```bash
python3 add_pays_to_zone.py --scenario reference --zone union_africaine_resilience --pays Mali Niger Tchad
```

## Nouveau script : regenerate_zones_pays.py

Reconstruit intégralement `gui/zones_pays.json` depuis les fiches `geographie/*.md` (source de vérité), au lieu de faire confiance à l'état existant du fichier. À relancer si `check_zones_coherence.py` détecte encore des pays "totalement absents" après un `--apply` qui semblait avoir tout couvert — signe que `zones_pays.json` s'est désynchronisé.

```bash
python3 regenerate_zones_pays.py --dry-run   # aperçu
python3 regenerate_zones_pays.py              # écrit, backup .json.bak automatique
```

---

## Prochaine session — ordre recommandé

1. Décider du modèle LLM par défaut pour la carte/coverage (bug #3 — `mistral-small` déconseillé)
2. P1bis — documenter l'onglet Carte + workflow coverage dans `user_manual_updated.md` (base déjà fournie : `USER_MANUAL_carte_et_couverture_4juillet.md`)
3. P11 (optionnel) — intégrer `check_zones_coherence.py` au GUI
4. Reprendre P3 (tests end-to-end formulaires guidés) ou toute autre priorité du backlog — P2 n'est plus un point de blocage, et cette fois c'est vraiment vérifié en profondeur (pas seulement en surface)
