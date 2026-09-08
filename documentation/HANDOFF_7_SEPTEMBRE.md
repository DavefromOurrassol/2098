# HANDOFF — 7 septembre 2026

## Fait

### Chantier "GUI Entités/Instances/Événements/Signaux" — CLOS
Demande de David : nouvelles sections GUI sur le gabarit Rédaction/Articles (table filtrable/triable/paginée + panneau détail au clic) pour Entités, Instances, Événements, Signaux faibles. Scope tranché avec David : traiter d'abord Instances, Event_instances, Signaux faibles (pas Entités/Événements archétypes séparément pour l'instant). Un type à la fois, de bout en bout, validé en conditions réelles avant d'enchaîner.

**Instances** : `audit_inventaire_instances.py` (nouveau — dossier plat `instances/`, résolution `entite`→`entite_name` via `entites/{slug}.md` avec cache mémoire, champ dérivé `transnationale` depuis `localisation.zone` vide/null). Routes `GET /api/instances/liste` + `POST /api/instances/inventaire`. Onglet GUI "Instances" (table + panneau, entité archétype parente affichée avec ⚠ si introuvable, bouton Obsidian). Testé sur tout le vault réel : 758 instances, 0 illisibles, 0 entité introuvable, 275 transnationales, 42 clandestines.

**Event_instances** : `audit_inventaire_event_instances.py` (résolution `archetype`→`archetype_name` via `evenements/{slug}.md`). Routes `GET /api/event_instances/liste` + `POST /api/event_instances/inventaire`. Onglet GUI "⚡ Événements". Testé : 80 event_instances, 0 illisibles. Champ `description` ajouté après coup (script + panneau) sur demande de David.

**Signaux faibles** : `audit_inventaire_signaux.py` — structure la plus différente des deux précédents : pas de champ `scenario` en frontmatter, rattachement scénarios extrait d'un bloc YAML imbriqué dans le corps Markdown (`## Trajectoire injectée`, PAS `## Impact chiffré` comme d'abord supposé — corrigé après lecture de 2 exemples réels). Routes `GET /api/signaux/liste` + `POST /api/signaux/inventaire`. Onglet GUI "📡 Signaux faibles". Testé : 3 signaux (dossier peu peuplé), 0 illisibles, README.md correctement exclu. Extension post-clôture (demande de David) : panneau enrichi avec `description` (section "Idée source") et `trajectoire` (détail complet évolution/date_bascule/evenement_cle par scénario, groupé par entrée si plusieurs variables cibles).

**Transverse** : panneaux Articles/Instances/Événements/Signaux rendus redimensionnables (glisser-déposer, classe CSS générique `.panel-resizer`, fonction JS générique `initPanelResizer()`, une clé localStorage par onglet, bornes 280-900px).

### Chantier "Résumé par scénario" — CLOS
Demande de David : résumé de chaque scénario avec les principaux événements/acteurs. Scope tranché via choix rapides : prose générée par IA (1 appel LLM/scénario), sélection par score d'impact (`impact_local`+`impact_systemique_global` pour les instances, `portee` pour les event_instances), intégré au GUI.

`generate_resume_scenarios.py` (nouveau) : réutilise `scanner_tout()` de `audit_inventaire_instances.py`/`audit_inventaire_event_instances.py` (pas de reparsing) — top 15 instances par score d'impact, top 10 event_instances par portée, prompt construit depuis ces listes curatées. `call_llm(task_tier="creative_souple")` (pas `call_claude_json`, qui est spécifique JSON structuré — vérifié dans `llm_client.py`). Cache `state/resume_scenarios.json`, même mécanique que `detect_basculements_narratifs.py`. Routes `GET /api/scenarios/resume` + `POST /api/scenarios/generer_resume` (timeout 600s). Onglet GUI "📝 Résumés par scénario" — gabarit différent (grille de cartes, pas table+panneau). Testé en conditions réelles sur eco_communalism : résumé jugé très solide par David.

## Bugs trouvés

- **2 fichiers `evenements/*.md` cassés** (`incident_passage_arctique.md`, `helios_bse_active_le_protocole_ombre_les_coupures_.md`) : `name:` contenait un `:` non échappé, cassant tout le parsing YAML du frontmatter (`mapping values are not allowed here`). Diagnostiqué via `⚠ Archétype événementiel parent introuvable` (5, dont 4 venant du même seul fichier cassé, réutilisé par 4 scénarios). Scan élargi (`scan_frontmatter_casse.py`, outil ponctuel, 1455 fichiers scannés dans entites/instances/evenements/event_instances/signaux_custom) a confirmé que ces 2 fichiers étaient les SEULS cassés sur tout le vault. Corrigés par David via `fix_name_non_quote.py` (outil ponctuel, `.bak` + guillemets autour de la valeur `name:` uniquement).
- **Faux signal découvert dans mon propre script** : `audit_inventaire_signaux.py` levait à tort `⚠ Entrée signal_to_state dupliquée` quand un signal avait plusieurs entrées `signal_to_state`. Investigation (lecture de `inject_custom_signals.py` fourni par David) a confirmé que ce n'est PAS un bug : une entrée par variable cible du signal est le comportement normal du pipeline d'injection. Corrigé pour vérifier une vraie incohérence à la place (`entrees_trajectoire` ≠ nombre de `variables_cibles`, signe d'injection partielle).
- Deux bugs mineurs dans mes propres livraisons, trouvés et corrigés AVANT livraison (jamais atteint David) : un edit avait supprimé l'en-tête d'un commentaire de bloc dans `app.js` (2 fois, même type d'erreur que le bug du 7 sept sur Rédaction) — repérés par `node --check` systématique avant chaque livraison de fichier `.js`.
- **`signaux_custom/README.md`** remonte comme "cassé" dans `scan_frontmatter_casse.py` — faux positif confirmé (pas un fichier de données, pas de frontmatter attendu), déjà exclu explicitement de `audit_inventaire_signaux.py`.

## Décisions actées

- Entités/Événements (archétypes) comme sections GUI séparées : **hors scope**, pas demandées pour l'instant (seulement Instances/Event_instances/Signaux, qui référencent leur archétype parent dans leur panneau).
- Anomalie `type_dans_scenario: infrastructure|hybride` (1 fichier instances/, valeur combinée avec pipe) : notée, **pas corrigée**, pas demandée par David.
- `Custom: 80 | Canoniques: 0` sur les event_instances : question posée à David sur si c'est attendu, **jamais répondue** — pas bloquant, mais point ouvert si quelqu'un s'interroge dessus plus tard.
- `description_journalistique` (instances) : **volontairement non ajouté** au panneau Instances (David a validé "Instances ok" sans demander cet ajout, contrairement à Event_instances où `description` a été explicitement demandé).

## Reste à faire

- Rien d'ouvert sur les 2 chantiers de cette session — tous deux clos et testés en conditions réelles.
- Actif hérité : P20 (choix du service de génération d'images externe, seul point restant) + secondaire S1-S7 (voir BACKLOG_ACTIF.md).

## Fichiers livrés

- `audit_inventaire_instances.py` (nouveau)
- `audit_inventaire_event_instances.py` (nouveau)
- `audit_inventaire_signaux.py` (nouveau)
- `generate_resume_scenarios.py` (nouveau)
- `scan_frontmatter_casse.py` (outil ponctuel, diagnostic, pas un script du pipeline)
- `fix_name_non_quote.py` (outil ponctuel, correction, pas un script du pipeline)
- `app.py` (routes ajoutées : `/api/instances/*`, `/api/event_instances/*`, `/api/signaux/*`, `/api/scenarios/*`)
- `index.html` (4 nouveaux onglets : Instances, Événements, Signaux faibles, Résumés par scénario)
- `app.js` (logique des 4 nouveaux onglets + mécanisme de redimensionnement générique des panneaux)

## Non traité hérité

- P20 (service de génération d'images externe) — toujours en attente de choix (OpenAI/Stability/Google Imagen/autre), intégration `_generate_image_via_api()` prête et en attente.
- Secondaire S1-S7 — voir BACKLOG_ACTIF.md pour le détail, non touché cette session.
