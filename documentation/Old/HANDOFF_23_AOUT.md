# Handoff — 23 août 2026

Session consacrée principalement à la clôture de P25 (reprise du 22
août), avec plusieurs découvertes et correctifs en cours de route.
Détail complet dans `BACKLOG_MASTER_9_AOUT.md` (points 10, 16, 17, 18)
et `USER_MANUAL_COMPLET.md` (nouvelles sections juste avant "P20 —
Phase A").

## Ce qui a été fait et clos aujourd'hui

1. **P25 clos définitivement.** Cause racine trouvée sur point soulevé
   par David (hiérarchie de zones niveau 1/2/3, jamais prise en compte
   avant) : `journaux.yaml` n'a qu'une entrée par zone N1,
   `_dominant_zone()` peut retourner une sous-zone N2/N3, la recherche
   échouait silencieusement et tombait sur le chemin "LLM invente un
   nom". Nouvelle fonction `_resoudre_zone_n1()` (remontée par
   `parent`, garde-fou anti-cycle). Testé sur 6 cas synthétiques dont
   le cas réel exact du 12 août, **confirmé à 100% de fiabilité sur 2
   scénarios indépendants en conditions réelles**
   (`new_sustainability`, `fortress_world`), contre ~25-33% avant.

2. **Bug dashboard "0 articles"** trouvé et corrigé — `routes_dashboard.py`
   avait le même défaut de scan non récursif déjà corrigé le 10 août
   ailleurs, mais jamais répercuté ici (fichier extrait du flux de
   patches habituel sur `app.py` depuis le 4 juillet, ce qui l'a fait
   passer sous le radar). Testé sur structure synthétique, pas encore
   re-testé sur le vrai dashboard de David.

3. **Consigne `image_prompt` corrigée en deux temps** : variété de
   palette (23% des articles avaient du vocabulaire "bleu", aucune
   consigne ne poussait dans cette direction) puis réutilisation des
   signes distinctifs déjà établis (`signes_distinctifs`, présent sur
   758/758 instances, déjà transmis au LLM depuis le 3 août mais jamais
   explicitement lié à la consigne image). Aucun test synthétique
   possible — à vérifier sur un futur batch normal.

4. **Idée de "base d'infrastructures" explorée puis résolue sans
   nouveau code** : le pipeline entités/instances existant couvre déjà
   ce besoin (`VALID_CATEGORIES` inclut `infrastructure`), et
   `signes_distinctifs` répond déjà à l'objectif réel de David
   (inspiration visuelle cohérente pour les futurs articles). Pas de
   nouveau système à construire.

5. **Garde-fou retry pour `signes_distinctifs`** : le champ n'était pas
   structurellement garanti (suggéré, pas requis, aucune validation).
   Même principe que le retry de longueur des articles (10 août).
   Testé en synthétique (3 cas) et en conditions réelles
   (non-régression confirmée, déclenchement réel non observé — taux
   d'échec naturel trop faible pour tomber dessus par hasard).

## Fichiers livrés aujourd'hui (à remettre en place dans le vault)

- `prompt_builder.py` (3 correctifs cumulés : remontée zone N1 pour
  P25, variété de palette, réutilisation signes distinctifs — un seul
  remplacement suffit)
- `routes_dashboard.py` (scan récursif)
- `instance_generation_common.py` (garde-fou retry signes_distinctifs)

**Redémarrage GUI Flask nécessaire** pour `routes_dashboard.py`. Pas
nécessaire pour `prompt_builder.py`/`instance_generation_common.py`
(scripts backend).

## Point de reprise pour la prochaine session

**Rien d'urgent en cours.** Deux vérifications à faire "en passant" au
prochain usage normal, pas de test dédié requis :
1. Confirmer que le dashboard affiche à nouveau les bons chiffres après
   redémarrage GUI.
2. Observer si le taux de vocabulaire "bleu" dans `image_prompt` baisse
   sur un futur batch (pas de comparaison avant/après rigoureuse
   possible, le batch `fortress_world` d'aujourd'hui a été généré
   avant ce correctif).

Sujet explicitement mis en pause, à reprendre si David le souhaite :
aucun (résolu dans la discussion elle-même — pas de vraie "pause"
restante, l'idée de base de données a été remplacée par la
constatation que `signes_distinctifs` couvre déjà le besoin).

## Reste en attente, non traité aujourd'hui

- Diagnostic des personnes récurrentes (`leena_vainala`,
  `amara_diallo_nkosi`) — toujours jamais commencé.
- `chapo`/`tags`/`image_prompt` vides (~7% des cas, point 14 du
  backlog) — pas retouché aujourd'hui.
- Choix du service externe de génération d'image (P20) — toujours non
  tranché.
- Bug mineur `--stats` de `rapprocher_articles.py` (seuil minimum
  d'articles) — toujours pas corrigé, mineur.

## Fichiers à ré-uploader en début de prochaine session

- `BACKLOG_MASTER_9_AOUT.md` (mis à jour) — remplace la version du
  Project.
- `USER_MANUAL_COMPLET.md` (mis à jour) — remplace la version du
  Project.
- `HANDOFF_23_AOUT.md` (ce fichier) — nouveau, à ajouter au Project.
