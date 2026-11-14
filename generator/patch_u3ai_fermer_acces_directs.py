#!/usr/bin/env python3
"""
patch_u3ai_fermer_acces_directs.py — Ourrassol 2098 (14 novembre 2026)

Étape 1 du plan « ajouter au monde » : fermer les accès directs d'injection
d'événement, sans changer ce que l'utilisateur voit (ces accès n'étaient plus
appelés depuis l'interface : le bouton Articles ouvre « et si ? », le bouton
de la veille aussi).

  gui/static/app.js  — supprime le code mort :
      renderArticlesPromouvoirForm, submitArticlesPromouvoirInjection,
      _articlesPromSuggestId, INJEV_VALID_VARS,
      _veillePreparer, _veilleAfficherPropositions et leurs constantes
      VEILLE_*, plus la ligne qui n'était jamais vraie
      (VeilleState.propositions[c.id] n'est plus rempli nulle part).
  gui/app.py — la route /api/edition/injecter_evenement répond 410 (fermée)
      au lieu d'injecter. Le code reste dessous, inactif : retour arrière en
      supprimant les 4 lignes marquées U3ai.

NE TOUCHE PAS : /api/yaml/append (formulaires « Ajouter à la queue » des
outils d'injection, encore utilisés), /api/idees/proposer (bouton
« Compléter les autres champs »), les outils d'injection du menu.

Usage (racine du vault) :
    python3 generator/patch_u3ai_fermer_acces_directs.py            # aperçu
    python3 generator/patch_u3ai_fermer_acces_directs.py --apply    # écrit

Sauvegardes .bak_u3ai ; refuse un second passage ; tout ou rien (si un
contrôle échoue, aucun fichier n'est écrit).
Après --apply : redémarrer Flask (app.py modifié), puis Cmd+Maj+R dans le
navigateur (app.js modifié).
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3ai"
JS = Path("gui/static/app.js")
PY = Path("gui/app.py")

# Identifiants qui ne doivent plus apparaître dans app.js après suppression.
DISPARUS_JS = [
    "renderArticlesPromouvoirForm", "submitArticlesPromouvoirInjection",
    "_articlesPromSuggestId", "INJEV_VALID_VARS", "_veillePreparer",
    "_veilleAfficherPropositions", "VEILLE_VARIABLES", "VEILLE_PERSISTANCES",
    "VEILLE_PORTEES", "VEILLE_INTENSITES", "VEILLE_MAX_VARS",
]


def couper(texte, debut, fin, nom, inclure_fin=False):
    """Supprime de `debut` (inclus) jusqu'à `fin` (exclu, ou inclus)."""
    if texte.count(debut) != 1:
        raise ValueError(f"{nom} : ancre de début présente {texte.count(debut)} fois")
    i = texte.index(debut)
    j = texte.find(fin, i + len(debut))
    if j < 0:
        raise ValueError(f"{nom} : ancre de fin introuvable")
    if inclure_fin:
        j += len(fin)
    print(f"  ✓ {nom} : {texte[i:j].count(chr(10))} lignes retirées")
    return texte[:i] + texte[j:]


def retirer_exact(texte, bloc, nom):
    if texte.count(bloc) != 1:
        raise ValueError(f"{nom} : bloc présent {texte.count(bloc)} fois")
    print(f"  ✓ {nom}")
    return texte.replace(bloc, "", 1)


def transformer_js(t):
    t = couper(
        t,
        "// Même liste que VALID_VARS dans inject_custom_events.py -- dupliquée ici\n",
        "];\n\n", "INJEV_VALID_VARS", inclure_fin=True)
    t = couper(
        t, "function _articlesPromSuggestId(article) {",
        "}\n\n", "_articlesPromSuggestId", inclure_fin=True)
    t = couper(
        t, "function renderArticlesPromouvoirForm(article, container) {",
        "// Génère le rapport Markdown complet (documentation/inventaire_articles.md,",
        "ancien formulaire Promouvoir + submit")
    t = retirer_exact(
        t, "\n  if (VeilleState.propositions[c.id]) _veilleAfficherPropositions(c);\n",
        "ligne morte (veille)")
    t = couper(
        t, "async function _veillePreparer(c) {",
        "initPanelResizer('#tab-veille_signaux", "ancien flux veille → queue")
    restes = [n for n in DISPARUS_JS if n in t]
    if restes:
        raise ValueError(f"identifiants encore référencés dans app.js : {restes}")
    return t


ANCRE_PY = (
    "    /api/edition/articles et lance l'injection en un clic, sans passer par\n"
    "    queue.yaml.\n"
    '    """\n'
)
BLOC_PY = (
    "    # U3ai (14 nov 2026) : accès direct fermé -- passer par « Et si ? ».\n"
    '    return jsonify({"ok": False, "error": "Accès fermé : utiliser '
    '« Et si ? » (onglet Articles → Envoyer vers « et si ? »)."}), 410\n'
)


def transformer_py(t):
    if t.count(ANCRE_PY) != 1:
        raise ValueError(f"app.py : ancre de la route présente {t.count(ANCRE_PY)} fois")
    print("  ✓ app.py : route /api/edition/injecter_evenement → 410")
    return t.replace(ANCRE_PY, ANCRE_PY + BLOC_PY, 1)


def syntaxe_js_ok(texte):
    """True si node accepte le texte ; None si node ne peut pas juger."""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(texte)
        chemin = f.name
    try:
        r = subprocess.run(["node", "--check", chemin], capture_output=True, text=True)
    except FileNotFoundError:
        return None
    finally:
        Path(chemin).unlink(missing_ok=True)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    for p in (JS, PY):
        if not p.exists():
            print(f"✗ Introuvable : {p} (lancer depuis la racine du vault)")
            return 2
    js0 = JS.read_text(encoding="utf-8")
    py0 = PY.read_text(encoding="utf-8")
    if MARQUEUR in py0 or "_veillePreparer" not in js0 and "renderArticlesPromouvoirForm" not in js0:
        print(f"✗ {MARQUEUR} semble déjà appliqué — refus d'un second passage.")
        return 1

    try:
        print("app.js :")
        js1 = transformer_js(js0)
        print("app.py :")
        py1 = transformer_py(py0)
    except ValueError as e:
        print(f"✗ {e} — rien écrit.")
        return 1

    avant = syntaxe_js_ok(js0)
    apres = syntaxe_js_ok(js1)
    if apres is False and avant is not False:
        print("✗ app.js n'est plus valide pour node après suppression — rien écrit.")
        return 1
    if avant is False:
        print("  (node refuse déjà l'original, p. ex. '||=' sur un node ancien : "
              "contrôle de syntaxe ignoré)")
    elif apres is None:
        print("  (node introuvable : contrôle de syntaxe ignoré)")
    else:
        print("  ✓ syntaxe app.js valide")

    try:
        import ast
        ast.parse(py1)
        print("  ✓ syntaxe app.py valide")
    except SyntaxError as e:
        print(f"✗ app.py invalide : {e} — rien écrit.")
        return 1

    if not args.apply:
        print(f"\nAperçu seulement : app.js {len(js0.splitlines())} → "
              f"{len(js1.splitlines())} lignes. Relancer avec --apply pour écrire.")
        return 0

    for p in (JS, PY):
        shutil.copy2(p, p.with_name(p.name + ".bak_u3ai"))
    JS.write_text(js1, encoding="utf-8")
    PY.write_text(py1, encoding="utf-8")
    print("\n✓ Écrit : gui/static/app.js et gui/app.py (sauvegardes .bak_u3ai).")
    print("→ Redémarrer Flask, puis Cmd+Maj+R dans le navigateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
