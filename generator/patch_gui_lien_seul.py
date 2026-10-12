#!/usr/bin/env python3
"""
patch_gui_lien_seul.py — Ourrassol 2098 (12 octobre 2026)
=========================================================

Nouvelle option des panneaux de fichiers (yaml_files de scripts_config.json) :
"lien_seul": true. Le panneau ne montre plus que le nom du fichier, cliquable :
  - .md   -> Obsidian (lien posé par patch_gui_obsidian_panneaux.py, requis) ;
  - autre -> Visual Studio Code (route POST /api/ouvrir_vscode : `open -a
             "Visual Studio Code" <fichier>`, fichier du vault seulement).
Contenu et boutons Éditer/Sauvegarder masqués (toujours chargés en coulisse :
le reste du GUI qui recharge ces panneaux continue de fonctionner).

Activée ici pour les deux panneaux du simulateur « et si ? » :
et_si/hypotheses.yaml et le rapport du dernier lancement.

Fichiers (tout ou rien) : gui/static/app.js, gui/app.py, gui/scripts_config.json.

Usage (depuis la racine du vault) :
    python3 generator/patch_gui_lien_seul.py --dry-run && python3 generator/patch_gui_lien_seul.py
Sauvegardes .bak_lien_seul ; refuse un second passage. Redémarrer Flask, puis
recharger la page sans cache (Cmd+Maj+R).
"""

import argparse
import json
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
MARQUE = "PATCH_GUI_LIEN_SEUL"

JS_AVANT = ("  // Charger le contenu\n"
            "  await loadYamlContent(wrapper, yf.path);\n"
            "\n"
            "  return wrapper;\n"
            "}\n")
JS_APRES = ("  // Charger le contenu\n"
            "  await loadYamlContent(wrapper, yf.path);\n"
            "\n"
            "  // PATCH_GUI_LIEN_SEUL (12 octobre 2026) : option lien_seul -> le panneau\n"
            "  // ne montre que le nom du fichier ; .md -> Obsidian (lien déjà posé sur le\n"
            "  // titre), autre -> Visual Studio Code. Contenu chargé mais masqué.\n"
            "  if (yf.lien_seul) {\n"
            "    viewEl.style.display = 'none';\n"
            "    editEl.style.display = 'none';\n"
            "    actions.style.display = 'none';\n"
            "    if (!/\\.md$/i.test(yf.path)) {\n"
            "      titleEl.textContent = `${yf.label} ↗`;\n"
            "      titleEl.title = 'Ouvrir dans Visual Studio Code';\n"
            "      titleEl.style.cursor = 'pointer';\n"
            "      titleEl.addEventListener('mouseenter', () => { titleEl.style.textDecoration = 'underline'; });\n"
            "      titleEl.addEventListener('mouseleave', () => { titleEl.style.textDecoration = ''; });\n"
            "      titleEl.addEventListener('click', () => _panneauOuvrirDansVSCode(yf.path, statusMsg));\n"
            "    }\n"
            "  }\n"
            "\n"
            "  return wrapper;\n"
            "}\n")

JS_FONCTION = r'''

// PATCH_GUI_LIEN_SEUL (12 octobre 2026) : ouvre un fichier du vault dans
// Visual Studio Code (route /api/ouvrir_vscode, `open -a` côté Mac).
async function _panneauOuvrirDansVSCode(chemin, statusEl) {
  try {
    const res = await fetch('/api/ouvrir_vscode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: chemin }),
    });
    const data = await res.json();
    if (data.error) showYamlStatus(statusEl, 'error', `Erreur : ${data.error}`);
  } catch (e) {
    showYamlStatus(statusEl, 'error', `Erreur réseau : ${e.message}`);
  }
}
'''

PY_AVANT = '@app.route("/api/yaml", methods=["GET"])\n'
PY_APRES = '''# PATCH_GUI_LIEN_SEUL (12 octobre 2026) : panneaux « lien_seul » -- ouvre un
# fichier du vault (jamais en dehors) dans Visual Studio Code, sur le Mac où
# tourne le GUI. N'écrit rien.
@app.route("/api/ouvrir_vscode", methods=["POST"])
def ouvrir_vscode():
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    rel_path = str((request.get_json() or {}).get("path") or "")
    if not rel_path:
        return jsonify({"error": "Paramètre path manquant"}), 400
    target = (vault_root / rel_path).resolve()
    try:
        target.relative_to(vault_root.resolve())
    except ValueError:
        return jsonify({"error": "Chemin non autorisé"}), 403
    if not target.exists():
        return jsonify({"error": f"fichier absent : {rel_path}"}), 404
    if sys.platform != "darwin":
        return jsonify({"error": "ouverture dans Visual Studio Code prévue pour macOS seulement"}), 501
    try:
        r = subprocess.run(["open", "-a", "Visual Studio Code", str(target)],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as e:
        return jsonify({"error": f"ouverture impossible : {e}"}), 500
    if r.returncode != 0:
        return jsonify({"error": f"Visual Studio Code introuvable ? {r.stderr.strip()[-300:]}"}), 500
    return jsonify({"ok": True})


@app.route("/api/yaml", methods=["GET"])
'''

CHEMINS_LIEN_SEUL = {"et_si/hypotheses.yaml", "documentation/need_action/et_si_dernier_lancement.md"}


def _node_check(texte):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
        tmp.write(texte)
    try:
        r = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass
    return r.returncode == 0, r.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--vault", default=str(VAULT))
    args = ap.parse_args()
    v = Path(args.vault)
    app_js, app_py, conf = v / "gui" / "static" / "app.js", v / "gui" / "app.py", v / "gui" / "scripts_config.json"
    for f in (app_js, app_py, conf):
        if not f.exists():
            sys.exit(f"✗ {f} introuvable : rien écrit.")

    t_js = app_js.read_text(encoding="utf-8")
    if MARQUE in t_js:
        sys.exit("✗ Patch déjà appliqué : rien à faire.")
    if "PATCH_GUI_OBSIDIAN_PANNEAUX" not in t_js:
        sys.exit("✗ Appliquer d'abord patch_gui_obsidian_panneaux.py : rien écrit.")
    if t_js.count(JS_AVANT) != 1:
        sys.exit(f"✗ app.js : ancre trouvée {t_js.count(JS_AVANT)} fois (1 attendue) : rien écrit.")
    n_js = t_js.replace(JS_AVANT, JS_APRES).rstrip("\n") + "\n" + JS_FONCTION
    origine = _node_check(t_js)
    if origine is None:
        note = "node absent : syntaxe JS non vérifiée"
    elif origine[0]:
        ok, err = _node_check(n_js)
        if not ok:
            sys.exit(f"✗ app.js patché : erreur de syntaxe, rien écrit :\n{err[-800:]}")
        note = "syntaxe JS vérifiée (node)"
    else:
        ok, err = _node_check(JS_FONCTION)
        if not ok:
            sys.exit(f"✗ fonction ajoutée : erreur de syntaxe, rien écrit :\n{err[-800:]}")
        note = "syntaxe de la fonction ajoutée vérifiée (node trop ancien pour app.js entier)"

    t_py = app_py.read_text(encoding="utf-8")
    if MARQUE in t_py:
        sys.exit("✗ app.py : patch déjà appliqué : rien écrit.")
    if t_py.count(PY_AVANT) != 1:
        sys.exit(f"✗ app.py : ancre trouvée {t_py.count(PY_AVANT)} fois (1 attendue) : rien écrit.")
    n_py = t_py.replace(PY_AVANT, PY_APRES)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(n_py)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ app.py patché ne compile pas, rien écrit : {e}")
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass

    t_conf = conf.read_text(encoding="utf-8")
    data = json.loads(t_conf)
    if json.dumps(data, ensure_ascii=False, indent=2) != t_conf:
        sys.exit("✗ Mise en forme de scripts_config.json inattendue : rien écrit.")
    entrees = [e for e in data if e.get("id") == "simuler_et_si"]
    if len(entrees) != 1:
        sys.exit(f"✗ Entrée simuler_et_si trouvée {len(entrees)} fois : rien écrit.")
    vus = set()
    for yf in entrees[0].get("yaml_files") or []:
        if yf.get("path") in CHEMINS_LIEN_SEUL:
            yf["lien_seul"] = True
            vus.add(yf["path"])
    if vus != CHEMINS_LIEN_SEUL:
        sys.exit(f"✗ scripts_config.json : panneau(x) absent(s) : {', '.join(CHEMINS_LIEN_SEUL - vus)}. Rien écrit.")
    n_conf = json.dumps(data, ensure_ascii=False, indent=2)

    if args.dry_run:
        print(f"✓ 3 fichiers patchables, compilation OK, {note} (dry-run, rien écrit).")
        return
    for chemin, texte in ((app_js, n_js), (app_py, n_py), (conf, n_conf)):
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_lien_seul"))
        chemin.write_text(texte, encoding="utf-8")
    print("✓ Panneaux du simulateur réduits à leur nom (.md -> Obsidian, .yaml -> Visual Studio Code) ; "
          "sauvegardes .bak_lien_seul. Redémarrer Flask, puis recharger la page sans cache (Cmd+Maj+R).")


if __name__ == "__main__":
    main()
