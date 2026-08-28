# Instructions personnalisées — Project Ourrassol 2098

## Contexte du projet
Ourrassol 2098 est un vault de presse simulée fictive (worldbuilding / prospective) construit en Python + Obsidian.
- Vault Obsidian : `/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/`
- Repo Git : `DavefromOurrassol/2098`
- Scripts exécutés depuis le sous-dossier `generator/`
- LLM par défaut : Mistral. Le workflow `generate_manual.py` ("sans API") utilise Claude.ai directement — c'est intentionnel, pas une relique.
- Clés API dans `~/.zshrc` (MISTRAL_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY) ; `.env` chargé au démarrage de la GUI Flask.
- Architecture : 6 scénarios × 12 variables × 20 thématiques, pattern archétype/instance pour entités et événements.

## Conventions de documentation
- `BACKLOG_MASTER_[DATE].md` : source unique de vérité, **mise à jour en place, jamais recréée**. Structure : Partie 1 (ouvert, priorisé 🔴🟡🟢⚪), Partie 2 (mineur non-bloquant), Partie 3 (risque structurel), Partie 4 (clos, historique).
- `HANDOFF_[DATE].md` par session : uploadé en début de session suivante.
- `USER_MANUAL_COMPLET.md` : référence vivante.
- Les mises à jour de documentation sont groupées **en fin de session, sur demande explicite uniquement** — ne pas les faire spontanément en cours de session.

## Règles techniques à retenir
- La GUI Flask doit être **entièrement redémarrée** après toute modification de `app.py` ou `scripts_config.json`.
- `validate.py` : état cible = 0 erreur / 0 warning. `-v/--verbose` pour le détail terminal, `--report/-r` pour générer `validation_report.md`.
- `--dry-run` sur les scripts d'injection **appelle réellement le LLM** — seule l'écriture disque est court-circuitée. Ne pas présenter `--dry-run` comme "sans coût/sans appel".
- `depends_on` dans `scripts_config.json` : l'enfant est toujours visible/indenté ; cocher l'enfant force le parent ; décocher le parent force l'enfant. Ce n'est **pas** de l'affichage conditionnel.

## Méthode de travail attendue
- Dry-run avant exécution réelle.
- Diagnostic avant codage — comprendre la cause racine avant de patcher.
- Lire les fichiers sources réels uploadés plutôt que supposer leur comportement.
- Valider en conditions réelles avant de marquer un chantier comme clos.
- Documenter les décisions avec leur justification, pas seulement le résultat.
- Préférer les corrections centralisées aux patchs par script (éviter la prolifération de scripts quand une solution générale existe).

## Ce que je n'ai PAS besoin qu'on me réexplique à chaque session
- L'architecture générale du vault (scénarios/variables/thématiques)
- Les conventions de documentation ci-dessus
- Mon niveau technique (ingénieur RF/payload, à l'aise en Python et MATLAB)
