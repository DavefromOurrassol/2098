"""
integrate_routes_carte.py — Intègre le Blueprint routes_carte.py dans
gui/app.py :
  1) ajoute `from routes_carte import carte_bp` + `app.register_blueprint(carte_bp)`
     juste après l'enregistrement existant de dashboard_bp (même patron déjà
     en place dans le fichier)
  2) retire les anciennes définitions des routes que routes_carte.py remplace

Usage, depuis gui/ :
    python3 integrate_routes_carte.py --dry-run     # aperçu, n'écrit rien
    python3 integrate_routes_carte.py --apply       # applique réellement (.bak avant)

Sécurité :
- .bak automatique (app.py.bak) avant toute écriture réelle
- chaque route à retirer est localisée par son chemin EXACT (pas de préfixe
  flou) -- si une route attendue est introuvable (le fichier a divergé de la
  version fournie fin de session précédente), le script le signale et NE
  RETIRE RIEN pour cette route plutôt que de deviner
- vérifie que le fichier résultant est un Python syntaxiquement valide avant
  d'écrire quoi que ce soit -- si ce n'est pas le cas, rien n'est écrit
"""

import argparse
import ast
import re
import sys
from pathlib import Path

APP_PY = Path("app.py")

# Chemins EXACTS des routes à retirer de app.py (remplacées par routes_carte.py).
# L'ordre n'a pas d'importance.
ROUTES_A_RETIRER = [
    "/api/carte/affectations",
    "/api/carte/zones_toutes",
    "/api/carte/overlays",
    "/api/carte/overlays/creer",
    "/api/carte/overlays/supprimer",
    "/api/carte/rechercher_zone",
    "/api/carte/arbre_zone",
    "/api/carte/impact_renommage_zone",
    "/api/carte/renommer_zone",
    "/api/carte/impact_reparent_zone",
    "/api/carte/reparent_zone",
    "/api/carte/impact_split_zone",
    "/api/carte/split_zone",
    "/api/carte/personnaliser_zone",
    "/api/carte/assign",
    "/api/carte/desaffecter",
    "/api/carte/creer_zone_niveau1",
    "/api/carte/propose",
    "/api/carte/ignorer",
    "/api/carte/impact",
]


def _find_route_block(text: str, path: str):
    """
    Localise le bloc @app.route("<path>", ...) / def ...(): / corps, via
    l'AST Python (et non une heuristique de texte) -- une fonction dont le
    corps contient une chaîne multi-lignes non indentée (ex. un prompt LLM
    écrit en f-string triple-guillemets) a des lignes qui démarrent en
    colonne 0 SANS être une nouvelle instruction top-level ; une détection
    par texte s'y trompe et tronque la fonction en plein milieu d'une
    chaîne, laissant un fichier syntaxiquement cassé. L'AST connaît les
    vraies frontières de chaque fonction, quel que soit son contenu.

    Retourne (start, end, nom_fonction) en offsets caractères dans `text`,
    ou None si la route n'existe pas (ou si `text` ne parse pas -- dans ce
    cas le caller le découvrira de toute façon à la validation finale).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None

    lines = text.splitlines(keepends=True)
    line_starts = [0]
    for line in lines:
        line_starts.append(line_starts[-1] + len(line))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                    and dec.func.attr == "route" and dec.args):
                continue
            arg0 = dec.args[0]
            arg_value = getattr(arg0, "value", None)  # ast.Constant (Python 3.8+)
            if arg_value != path:
                continue
            start_line = min(d.lineno for d in node.decorator_list)  # 1-indexé
            end_line = node.end_lineno  # 1-indexé, dernière ligne du corps
            start = line_starts[start_line - 1]
            end = line_starts[end_line]
            return start, end, node.name
    return None


def build_new_content(text: str):
    """Retourne (nouveau_texte, rapport) sans jamais lever -- rapport liste
    ce qui a été retiré et ce qui n'a pas été trouvé."""
    rapport = {"retirees": [], "introuvables": []}

    # Les offsets bougent à chaque suppression -- on retraite le texte
    # séquentiellement plutôt que de calculer tous les offsets sur le texte
    # d'origine.
    for path in ROUTES_A_RETIRER:
        bloc = _find_route_block(text, path)
        if bloc is None:
            rapport["introuvables"].append(path)
            continue
        start, end, func_name = bloc
        text = text[:start] + text[end:]
        rapport["retirees"].append((path, func_name))

    # Insertion de l'enregistrement du Blueprint, juste après celui de
    # dashboard_bp (même patron déjà en place). Idempotent : si déjà fait
    # lors d'un run précédent (re-lancer ce script après avoir ajouté une
    # route à ROUTES_A_RETIRER), ne duplique rien.
    if "from routes_carte import carte_bp" in text:
        rapport["blueprint_deja_present"] = True
    else:
        anchor = "app.register_blueprint(dashboard_bp)\n"
        if anchor not in text:
            rapport["erreur_ancrage"] = (
                "Ligne 'app.register_blueprint(dashboard_bp)' introuvable -- "
                "insertion du Blueprint carte_bp NON FAITE, à ajouter à la main."
            )
        else:
            insertion = (
                "\n# Refonte Carte (10 sept 2026) : routes /api/carte/* déplacées "
                "dans routes_carte.py,\n# même patron que dashboard_bp ci-dessus.\n"
                "from routes_carte import carte_bp\n"
                "app.register_blueprint(carte_bp)\n"
            )
            text = text.replace(anchor, anchor + insertion, 1)
            rapport["blueprint_insere"] = True

    return text, rapport


def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not APP_PY.exists():
        print(f"ERREUR : {APP_PY} introuvable -- lance ce script depuis gui/")
        sys.exit(1)

    original = APP_PY.read_text(encoding="utf-8")
    new_text, rapport = build_new_content(original)

    print(f"Routes retirées avec succès ({len(rapport['retirees'])}/{len(ROUTES_A_RETIRER)}) :")
    for path, func_name in rapport["retirees"]:
        print(f"  - {path}  (fonction {func_name})")

    if rapport["introuvables"]:
        print(f"\nRoutes INTROUVABLES, laissées telles quelles dans app.py ({len(rapport['introuvables'])}) :")
        for path in rapport["introuvables"]:
            print(f"  - {path}")
        print("  -> le fichier a peut-être divergé depuis la version fournie -- "
              "vérifie ces routes à la main si besoin.")

    if "erreur_ancrage" in rapport:
        print(f"\nATTENTION : {rapport['erreur_ancrage']}")
    elif rapport.get("blueprint_insere"):
        print("\nEnregistrement du Blueprint carte_bp inséré après dashboard_bp.")
    elif rapport.get("blueprint_deja_present"):
        print("\nBlueprint carte_bp déjà enregistré (run précédent) -- rien à refaire ici.")

    # Validation syntaxique avant tout écriture -- ne jamais laisser un
    # app.py cassé, même en cas de bug dans ce script.
    try:
        ast.parse(new_text)
    except SyntaxError as e:
        print(f"\nERREUR CRITIQUE : le résultat ne serait plus un Python valide ({e}) "
              "-- RIEN N'EST ÉCRIT, app.py inchangé.")
        sys.exit(1)

    print(f"\nTaille avant : {len(original)} caractères -- après : {len(new_text)} caractères "
          f"({len(original) - len(new_text)} retirés)")

    if args.dry_run:
        print("\n[dry-run] Aucun fichier modifié. Relance avec --apply pour écrire réellement.")
        return

    bak = APP_PY.with_suffix(".py.bak")
    bak.write_text(original, encoding="utf-8")
    APP_PY.write_text(new_text, encoding="utf-8")
    print(f"\napp.py mis à jour. Sauvegarde de l'ancienne version : {bak}")


if __name__ == "__main__":
    main()
