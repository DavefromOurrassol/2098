# Backlog — Publication web & journaux oraux

*Document de scoping issu de session de discussion, à intégrer dans BACKLOG_CONSOLIDE.md*

---

## 1. Enrichissement frontmatter pour publication web future

**Contexte** : anticiper la publication en ligne des articles générés en enrichissant le YAML frontmatter dès la génération, plutôt que de retraiter des centaines de fichiers a posteriori.

### Champs à ajouter au frontmatter des articles

| Champ | Description |
|---|---|
| `slug` | Identifiant URL-friendly (évite de le dériver du titre à chaque fois, risques de collision/accents) |
| `chapo` / `excerpt` | Résumé court (2-3 lignes) pour pages de liste et meta description SEO |
| `image_prompt` | Prompt de génération d'image, produit par le LLM en même temps que l'article |
| `a_une_photo` | Booléen, **basculé manuellement** — tous les articles n'auront pas de photo, c'est un choix éditorial |
| `image_principale` | Chemin vers l'image générée (rempli en post-traitement) |
| `image_alt` | Texte alternatif (accessibilité + SEO) |
| `image_credit` | Traçabilité de la source/du prompt si génération IA |
| `tags` | Mots-clés distincts de `thematique` (plus orientés découverte/recherche lecteur) |
| `journaliste_slug` | Lien vers la fiche auteur (déjà présent dans `journaux.yaml`) |
| `date_publication` vs `date_evenement` | À distinguer si publication différée / calendrier éditorial |
| `articles_lies` | Liens vers 2-3 articles connexes — possiblement déductible automatiquement des entités partagées plutôt que généré par le LLM |
| `zone_principale` | Déjà présent via `localisation`, mais un champ dédié simplifie le filtrage géographique côté front |

### Génération d'images — option retenue

**Option 1 retenue** : le LLM génère un `image_prompt` descriptif **au moment de la génération de l'article** (même appel API, cohérence garantie avec le contenu).

- La décision d'illustrer ou non un article (`a_une_photo`) reste **manuelle**, déclenchée par David — pas tous les articles ne méritent une image.
- Ça découple la décision éditoriale de la génération technique : le prompt est stocké dans le frontmatter dès la création, utilisable des semaines plus tard sans repasser par le LLM.

**Implémentation envisagée** :
1. Ajouter une instruction dans `prompt_builder.py` pour que le LLM produise systématiquement un champ `image_prompt` (description visuelle neutre : lieu, ambiance, éléments clés), même si non utilisé immédiatement.
2. `a_une_photo: false` par défaut dans le frontmatter, basculé à `true` manuellement (ou via script de sélection) par David.
3. Script séparé `generate_images.py` : scanne les articles `a_une_photo: true` sans `image_principale` encore renseignée, appelle l'API image, remplit `image_principale` + `image_alt`.

### Question ouverte
- **Rendu HTML** : approche pas encore décidée entre site statique généré (Hugo/Eleventy-like) à partir des YAML/Markdown, ou moteur de rendu intégré au pipeline Flask existant. Non bloquant pour enrichir le frontmatter dès maintenant.

---

## 2. Journaux oraux — orateurs itinérants

**Contexte** : pour certains scénarios, imaginer des orateurs itinérants qui informent les communautés lors de sessions orales plutôt que par écrit — pertinent notamment pour `eco_communalism` et/ou `breakdown`, scénarios où l'infrastructure de diffusion écrite/numérique est dégradée ou volontairement rejetée au profit du lien communautaire direct.

### Scoping décidé
- **Variante coexistant avec l'écrit au sein d'un même scénario** — pas un scénario entier qui bascule en mode oral. Certains journaux d'un scénario donné (ex. `eco_communalism`) seront oraux, d'autres resteront écrits.

### Structure technique

**Journal** : ajout d'un champ `type_diffusion` (`ecrit` / `oral` / `mixte`) sur l'entité journal dans `journaux.yaml`, pour router `prompt_builder.py` vers le bon registre via la logique existante de résolution de profil (`get_journal_profile()` adaptée).

**Orateur — entité séparée (Option B décidée)**

Deux options étaient envisagées :
- *Option A (écartée)* : réutiliser `journaliste_slug` avec un métier élargi ("orateur communautaire") — plus simple mais risque de forcer des spécificités narratives (itinérance, réputation orale) dans un modèle pensé pour un rôle différent.
- *Option B (retenue)* : créer une entité `orateur` distincte de `journaliste`, avec ses propres attributs :
  - itinérance entre communautés
  - communautés desservies
  - réputation orale
  - possible style rhétorique propre

**Implications d'implémentation** :
- Nouveau type d'entité `orateur`
- Nouveau lien dans `journaux.yaml` (en complément ou substitution de `journaliste_slug` selon `type_diffusion`)
- Logique de résolution de profil adaptée (variante de `get_journal_profile()` pour les journaux oraux)

### Registre oral dans `prompt_builder.py`

Différences de contenu par rapport au registre écrit :
- Adresse directe à l'auditoire ("vous avez sans doute remarqué que...")
- Formules d'ouverture/clôture ritualisées
- Répétitions rhétoriques
- Pas de mise en page journalistique : pas de chapô, pas de sous-titres
- Structure de discours : accroche → développement → appel à l'action ou question ouverte finale
- Possibilité d'éléments de call-and-response (question posée à l'auditoire), pour le côté performatif

### Champs frontmatter spécifiques aux articles oraux

| Champ | Description |
|---|---|
| `duree_estimee` | Calibrer la longueur du texte à un temps de parole réaliste |
| `lieu_diffusion` | Place publique, marché, assemblée... — granularité plus fine que `localisation` |
| `mode_reception` | Assemblée silencieuse, discussion ouverte, etc. — capture l'ambiance sociale |

---

*Fin du document — à copier dans BACKLOG_CONSOLIDE.md lors de la prochaine consolidation.*
