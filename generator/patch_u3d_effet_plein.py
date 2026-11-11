#!/usr/bin/env python3
"""patch_u3d — case « effet établi en 2098 » : les durées de montée des impacts sont CALCULÉES
(2098 − date, au moins 1 an) pour que l'effet soit à pleine force en 2098. Suite de U3c.
Dry-run par défaut ; --apply écrit (sauvegardes .bak_u3d). Depuis la racine du vault :
    python3 generator/patch_u3d_effet_plein.py [--apply]"""
import sys, shutil, subprocess, py_compile
from pathlib import Path
APPLY = "--apply" in sys.argv
ROOT = Path(sys.argv[sys.argv.index("--root")+1]) if "--root" in sys.argv else Path(".")
HT = ROOT / "generator" / "hypothese_depuis_texte.py"
APP = ROOT / "gui" / "app.py"
JS = ROOT / "gui" / "static" / "app.js"

HT_EDITS = [
 (r'''        if imposes.get("mode"):
            morceaux.append(f"mode {imposes['mode']}")
''',
  r'''        if imposes.get("mode"):
            morceaux.append(f"mode {imposes['mode']}")
        if imposes.get("effet_plein"):
            morceaux.append("durées de montée calculées pour que l'effet soit à pleine force en 2098")
'''),
 (r'''    if est_signal:
        return av   # un signal couvre toujours les 6 scénarios, sans mode rupture
''',
  r'''    if imposes.get("effet_plein"):   # U3d : durée de montée = 2098 - date (au moins 1 an)
        n = max(1, 2098 - int(h.get("date") or 2098))
        change = False
        for imp in h.get("impacts") or []:
            if imp.get("duree") != n:
                imp["duree"] = n
                change = True
        if change:
            av.append(f"effet plein en 2098 : durée de montée portée à {n} an(s) sur tous les impacts")
    if est_signal:
        return av   # un signal couvre toujours les 6 scénarios, sans mode rupture
'''),
 (r'''    ap.add_argument("--mode", choices=("choc", "rupture"), default=None,
                    help="avec --proposer : mode imposé (événement seulement)")
''',
  r'''    ap.add_argument("--mode", choices=("choc", "rupture"), default=None,
                    help="avec --proposer : mode imposé (événement seulement)")
    ap.add_argument("--effet-plein", action="store_true",
                    help="avec --proposer : durées de montée calculées (2098 - date) pour un effet plein en 2098")
'''),
 (r'''            if args.mode:
                imposes["mode"] = args.mode
''',
  r'''            if args.mode:
                imposes["mode"] = args.mode
            if args.effet_plein:
                imposes["effet_plein"] = True
'''),
]
APP_EDITS = [
 (r'''            cmd += ["--mode", data["mode"]]
''',
  r'''            cmd += ["--mode", data["mode"]]
        if data.get("effet_plein") is True:   # U3d
            cmd.append("--effet-plein")
'''),
]
JS_EDITS = [
 (r'''  const [lblRupt, cbRupt] = caseOui('mode rupture (déplace durablement le monde)');
  [lblDate, lblTous, lblRupt].forEach(e => reglages.appendChild(e));
''',
  r'''  const [lblRupt, cbRupt] = caseOui('mode rupture (déplace durablement le monde)');
  const [lblPlein, cbPlein] = caseOui('effet établi en 2098 (durées de montée calculées)');
  [lblDate, lblTous, lblRupt, lblPlein].forEach(e => reglages.appendChild(e));
'''),
 (r'''    const data = await appeler('proposer', texte, selType.value, extra);
''',
  r'''    extra.effet_plein = cbPlein.checked;   // U3d
    const data = await appeler('proposer', texte, selType.value, extra);
'''),
]

if "appliquer_imposes" not in HT.read_text(encoding="utf-8"):
    sys.exit("✗ U3c n'est pas appliqué (appliquer_imposes absent) : appliquer d'abord patch_u3c_valeurs_imposees.py")

def appliquer(txt, edits, nom):
    ok = True
    for k, (old, new) in enumerate(edits, 1):
        n = txt.count(old)
        if n != 1:
            print(f"✗ {nom} modif {k} : {n} occurrence(s) (1 attendue)"); ok = False
        else:
            txt = txt.replace(old, new)
    return txt, ok

ht, a = appliquer(HT.read_text(encoding="utf-8"), HT_EDITS, "hypothese_depuis_texte.py")
ap_, b = appliquer(APP.read_text(encoding="utf-8"), APP_EDITS, "app.py")
js, c = appliquer(JS.read_text(encoding="utf-8"), JS_EDITS, "app.js")
if not (a and b and c):
    print("✗ rien écrit"); sys.exit(1)
if not APPLY:
    print(f"✓ dry-run : {len(HT_EDITS)} modifs hypothese_depuis_texte.py, {len(APP_EDITS)} app.py, {len(JS_EDITS)} app.js")
    sys.exit(0)

def node_ok(p):
    try:
        return subprocess.run(["node", "--check", str(p)], capture_output=True, text=True).returncode == 0
    except FileNotFoundError:
        return None
for p in (HT, APP, JS):
    shutil.copy2(p, p.with_name(p.name + ".bak_u3d"))
HT.write_text(ht, encoding="utf-8"); APP.write_text(ap_, encoding="utf-8"); JS.write_text(js, encoding="utf-8")
try:
    py_compile.compile(str(HT), doraise=True); py_compile.compile(str(APP), doraise=True)
except py_compile.PyCompileError as e:
    for p in (HT, APP, JS):
        shutil.copy2(p.with_name(p.name + ".bak_u3d"), p)
    print(f"✗ erreur de syntaxe Python, fichiers restaurés : {e}"); sys.exit(1)
avant, apres = node_ok(JS.with_name(JS.name + ".bak_u3d")), node_ok(JS)
if avant is True and apres is False:
    for p in (HT, APP, JS):
        shutil.copy2(p.with_name(p.name + ".bak_u3d"), p)
    print("✗ erreur de syntaxe JavaScript introduite : fichiers restaurés"); sys.exit(1)
print("✓ appliqué" + ("" if apres else " (contrôle node non concluant : node absent ou déjà en erreur avant le patch)"))
