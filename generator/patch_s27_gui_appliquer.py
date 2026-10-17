#!/usr/bin/env python3
"""
patch_s27_gui_appliquer.py — Ourrassol 2098 (S27, point 6, 17 octobre 2026)
==========================================================================

Branche la phase 4 (appliquer_et_si.py) dans le panneau « ⚖️ Décider » du
simulateur « et si ? » :
  - gui/app.py : route POST /api/et_si/appliquer/<apercu|appliquer|reste>
    (appliquer_et_si.py --id X [--sauter …] [--inclure …] [--apply | --reste-a-faire]) ;
  - gui/static/app.js : section « Appliquer au vault (phase 4) » sous les
    boutons existants — champs « Sauter » / « Inclure (⚠) », boutons Aperçu,
    Appliquer (confirmation), Check-list, et lien Obsidian vers la check-list.

Aucun appel IA. Tout ou rien : si une ancre manque dans un des deux fichiers,
rien n'est écrit. Sauvegardes .bak_gui_appliquer. Refuse un second passage.
Prérequis : patch_s27_reste_a_faire.py appliqué (option --reste-a-faire).

USAGE (depuis la racine du vault, puis redémarrer Flask)
    python3 generator/patch_s27_gui_appliquer.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
APP_PY = VAULT / "gui" / "app.py"
APP_JS = VAULT / "gui" / "static" / "app.js"
APPLIQUER = VAULT / "generator" / "appliquer_et_si.py"
MARQUEUR = "PATCH_S27_GUI_APPLIQUER"

PY = [
    (
        "TIMEOUT_IDEES_TEXTE_LIBRE = 180  # secondes -- un seul appel LLM\n",
        r'''# ---------------------------------------------------------------------------
# PATCH_S27_GUI_APPLIQUER (17 octobre 2026) -- phase 4 dans le panneau
# « Décider » : appliquer_et_si.py (aperçu, --apply, --reste-a-faire).
# Aucun appel IA ; « appliquer » écrit dans le vault (.bak_appliquer).
# ---------------------------------------------------------------------------

ACTIONS_APPLIQUER = {"apercu": [], "appliquer": ["--apply"], "reste": ["--reste-a-faire"]}
TIMEOUT_APPLIQUER = 300  # secondes -- --apply enchaîne réciprocité et validate.py


@app.route("/api/et_si/appliquer/<action>", methods=["POST"])
def et_si_appliquer(action):
    if action not in ACTIONS_APPLIQUER:
        return jsonify({"error": f"action inconnue : {action}"}), 404
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}
    hid = str(data.get("id") or "").strip()
    if not hid:
        return jsonify({"error": "choisis d'abord une hypothèse dans la liste"}), 400
    cmd = [sys.executable, "appliquer_et_si.py", "--id", hid]
    for cle in ("sauter", "inclure"):
        valeur = re.sub(r"[^0-9,]", "", str(data.get(cle) or ""))
        if valeur.strip(","):
            cmd += [f"--{cle}", valeur.strip(",")]
    cmd += ACTIONS_APPLIQUER[action]
    try:
        resultat = subprocess.run(cmd, cwd=pipeline_dir, capture_output=True, text=True,
                                  timeout=TIMEOUT_APPLIQUER, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Délai dépassé ({TIMEOUT_APPLIQUER} s)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"appliquer_et_si.py introuvable dans {pipeline_dir}"}), 500
    sortie = "\n".join(s for s in (resultat.stdout.strip(), resultat.stderr.strip()) if s)
    m = re.search(r"check-list : (\S+\.md)", sortie)
    return jsonify({"ok": resultat.returncode == 0, "sortie": sortie,
                    "checklist": m.group(1) if m else None})


TIMEOUT_IDEES_TEXTE_LIBRE = 180  # secondes -- un seul appel LLM
''',
    ),
]

JS = [
    (
        "  corps.appendChild(ligneAutres);\n",
        r"""  corps.appendChild(ligneAutres);

  // PATCH_S27_GUI_APPLIQUER (17 octobre 2026) : phase 4, appliquer_et_si.py.
  const titreAppliquer = mk('div', 'option-label', 'Appliquer au vault (phase 4)');
  titreAppliquer.style.marginTop = '12px';
  corps.appendChild(titreAppliquer);
  corps.appendChild(mk('div', 'option-desc',
    'Pour une hypothèse adoptée ET injectée : applique ses conséquences (statuts de zone, trajectoires, ' +
    'retrait des relations d\'une entité disparue, relations nouvelles ou rompues), puis réciprocité et ' +
    'validate.py. Toujours faire l\'aperçu d\'abord : les opérations ⚠ sont sautées sauf si leur numéro ' +
    'est dans « Inclure ». La check-list liste ce qui reste à faire à la main (phrases, entités, lore, ' +
    'articles) sans rien modifier. Aucun appel IA.'));
  const ligneTri = mk('div');
  ligneTri.style.margin = '6px 0';
  const champNumeros = (placeholder) => {
    const c = mk('input');
    c.type = 'text';
    c.placeholder = placeholder;
    c.autocomplete = 'off';
    c.style.width = '22%';
    c.style.marginRight = '12px';
    return c;
  };
  ligneTri.appendChild(mk('span', 'option-label', 'Sauter '));
  const sauter = champNumeros('ex : 3,7');
  ligneTri.appendChild(sauter);
  ligneTri.appendChild(mk('span', 'option-label', 'Inclure (⚠) '));
  const inclure = champNumeros('ex : 6');
  ligneTri.appendChild(inclure);
  corps.appendChild(ligneTri);
  const ligneAppliquer = mk('div');
  const btnAppApercu = bouton('Aperçu de l\'application');
  const btnAppliquer = bouton('Appliquer (écrit dans le vault)', 'yaml-btn yaml-btn-save');
  const btnReste = bouton('Check-list « reste à faire »');
  const btnChecklist = bouton('Ouvrir la check-list ↗');
  btnChecklist.style.display = 'none';
  [btnAppApercu, btnAppliquer, btnReste, btnChecklist].forEach(b => ligneAppliquer.appendChild(b));
  corps.appendChild(ligneAppliquer);
""",
    ),
    (
        "const tous = [btnApercu, btnAdopter, btnRejeter, btnAnnuler, btnDossiers];",
        "const tous = [btnApercu, btnAdopter, btnRejeter, btnAnnuler, btnDossiers, btnAppApercu, btnAppliquer, btnReste];",
    ),
    (
        "const appeler = async (action, extra, rafraichir) => {",
        "const appeler = async (action, extra, rafraichir, base = 'decider') => {",
    ),
    (
        "fetch(`/api/et_si/decider/${action}`",
        "fetch(`/api/et_si/${base}/${action}`",
    ),
    (
        "btnDossiers.addEventListener('click', () => appeler('dossiers', {}, false));\n",
        r"""btnDossiers.addEventListener('click', () => appeler('dossiers', {}, false));

  // PATCH_S27_GUI_APPLIQUER
  let cheminChecklist = null;
  const appliquer = async (action) => {
    btnChecklist.style.display = 'none';
    await appeler(action, { sauter: sauter.value, inclure: inclure.value }, false, 'appliquer');
    const m = (sortie.textContent || '').match(/check-list : (\S+\.md)/);
    if (m) {
      cheminChecklist = m[1];
      btnChecklist.style.display = '';
    }
  };
  btnAppApercu.addEventListener('click', () => appliquer('apercu'));
  btnAppliquer.addEventListener('click', () => {
    if (!confirm('Appliquer au vault les opérations retenues par l\'aperçu ?\n' +
                 '(Sauvegarde .bak_appliquer ; réciprocité et validate.py ensuite. Commit git conseillé avant.)')) return;
    appliquer('appliquer');
  });
  btnReste.addEventListener('click', () => appliquer('reste'));
  btnChecklist.addEventListener('click', () => { if (cheminChecklist) _panneauOuvrirDansObsidian(cheminChecklist); });
""",
    ),
]


def preparer(chemin, remplacements):
    texte = chemin.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit(f"✗ {chemin.name} : patch déjà appliqué, rien fait.")
    for ancre, _ in remplacements:
        if texte.count(ancre) != 1:
            sys.exit(f"✗ {chemin.name} : ancre trouvée {texte.count(ancre)} fois au lieu d'une, rien fait.\n{ancre[:120]}")
    for ancre, nouveau in remplacements:
        texte = texte.replace(ancre, nouveau)
    return texte


def main():
    for p in (APP_PY, APP_JS, APPLIQUER):
        if not p.exists():
            sys.exit(f"✗ {p} introuvable")
    if "--reste-a-faire" not in APPLIQUER.read_text(encoding="utf-8"):
        sys.exit("✗ appliquer d'abord generator/patch_s27_reste_a_faire.py, rien fait.")
    py, js = preparer(APP_PY, PY), preparer(APP_JS, JS)
    compile(py, str(APP_PY), "exec")
    if "\nimport re" not in py and "\nimport re," not in py:
        sys.exit("✗ app.py n'importe pas re : rien fait.")
    # Contrôle JS : node de l'iMac trop ancien pour app.js entier (||=) -> code ajouté seul,
    # dans une fonction (contrôle de syntaxe uniquement).
    import tempfile
    ajout = JS[0][1].replace("  corps.appendChild(ligneAutres);\n", "", 1) + \
        JS[4][1].replace("btnDossiers.addEventListener('click', () => appeler('dossiers', {}, false));\n", "", 1)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write("async function essai() {\n" + ajout + "\n}\n")
    try:
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            sys.exit("✗ code JS ajouté invalide, rien fait :\n" + r.stderr)
    except FileNotFoundError:
        print("  (node absent : contrôle JS sauté)")
    finally:
        Path(f.name).unlink(missing_ok=True)
    for p, t in ((APP_PY, py), (APP_JS, js)):
        shutil.copy2(p, p.with_name(p.name + ".bak_gui_appliquer"))
        p.write_text(t, encoding="utf-8")
    print("✓ gui/app.py et gui/static/app.js modifiés, sauvegardes .bak_gui_appliquer")
    print("  Redémarrer Flask pour voir la section « Appliquer au vault (phase 4) » du panneau ⚖️ Décider.")


if __name__ == "__main__":
    main()
