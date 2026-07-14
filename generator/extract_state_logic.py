"""
extract_state_logic.py

Extrait states.{scenario}.state_logic depuis n'importe quelle fiche
variables/{variable}.md du vault (frontmatter YAML délimité par '---').

Pourquoi un parseur dédié plutôt qu'un yaml.safe_load direct :
le frontmatter utilise la syntaxe wikilink Obsidian comme clé YAML dans les
blocs coupling_intensity, ex. :
    coupling_intensity:
      [[geopolitique_conflits]]: 95
`[[xxx]]` est interprété par YAML comme une liste imbriquée, donc une clé de
mapping non hashable -> yaml.safe_load lève 'found unhashable key'. On
sanitize ces clés (-> chaîne "xxx") avant parsing plutôt que de modifier le
vault ou de maintenir un parseur YAML custom.

Usage CLI :
    python3 extract_state_logic.py variables/organisation_territoires.md
    python3 extract_state_logic.py variables/organisation_territoires.md --scenario breakdown
    python3 extract_state_logic.py variables/geopolitique_conflits.md variables/frontieres_du_systeme.md --json

Usage programmatique (P24 étape C — générateur top-down, et P22 — garde-fou) :
    from extract_state_logic import extract_state_logic
    logics = extract_state_logic("variables/geopolitique_conflits.md")
    # {"reference": "...", "breakdown": "...", ...}
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

# Sanitize les clés wikilink Obsidian [[xxx]] -> "xxx" avant parsing YAML.
# Ne touche que ce motif précis ; le reste du frontmatter est du YAML standard.
_WIKILINK_KEY = re.compile(r"\[\[([^\]]+)\]\]")


def _read_frontmatter(path: Path) -> dict:
    """Extrait et parse le bloc YAML frontmatter (entre les deux premiers '---')."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path} : pas de frontmatter YAML (le fichier doit commencer par '---').")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} : frontmatter YAML mal formé (délimiteurs '---' manquants).")

    frontmatter_raw = _WIKILINK_KEY.sub(r'"\1"', parts[1])

    try:
        data = yaml.safe_load(frontmatter_raw)
    except yaml.YAMLError as e:
        raise ValueError(f"{path} : erreur de parsing YAML dans le frontmatter : {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"{path} : frontmatter YAML vide ou invalide.")
    return data


def extract_state_logic(path) -> dict:
    """
    Retourne {scenario: state_logic} pour une fiche variables/{var}.md donnée.
    Lève ValueError si le fichier n'a pas de bloc 'states', ou si un scénario
    listé n'a pas de 'state_logic'.
    """
    path = Path(path)
    data = _read_frontmatter(path)

    states = data.get("states")
    if not states:
        raise ValueError(f"{path} : aucun bloc 'states' trouvé dans le frontmatter.")

    result = {}
    for scenario, bloc in states.items():
        if not isinstance(bloc, dict) or "state_logic" not in bloc or bloc["state_logic"] is None:
            raise ValueError(f"{path} : scénario '{scenario}' sans 'state_logic'.")
        # YAML '>' (folded scalar) : un \n final subsiste presque toujours -> strip.
        result[scenario] = str(bloc["state_logic"]).strip()
    return result


def extract_many(paths) -> dict:
    """
    {nom_variable: {scenario: state_logic}} pour plusieurs fiches à la fois.
    nom_variable dérivé du nom de fichier (sans extension), ex. 'organisation_territoires'.
    """
    out = {}
    for p in paths:
        p = Path(p)
        out[p.stem] = extract_state_logic(p)
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Extrait states.{scenario}.state_logic depuis une ou plusieurs "
                     "fiches variables/{variable}.md du vault."
    )
    parser.add_argument("files", nargs="+", help="Chemin(s) vers variables/{variable}.md")
    parser.add_argument("--scenario", help="Limiter la sortie à un seul scénario")
    parser.add_argument("--json", action="store_true", help="Sortie JSON plutôt que texte lisible")
    args = parser.parse_args()

    try:
        results = extract_many(args.files)
    except (ValueError, OSError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    if args.scenario:
        filtered = {}
        for var, logics in results.items():
            if args.scenario in logics:
                filtered[var] = {args.scenario: logics[args.scenario]}
            else:
                print(f"Avertissement : scénario '{args.scenario}' absent de {var}.md", file=sys.stderr)
        results = filtered

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for var, logics in results.items():
            print(f"# {var}")
            for scenario, logic in logics.items():
                print(f"  [{scenario}]")
                print(f"    {logic}")
            print()


if __name__ == "__main__":
    main()
