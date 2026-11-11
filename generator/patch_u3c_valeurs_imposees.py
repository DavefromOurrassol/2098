#!/usr/bin/env python3
"""patch_u3c — « Envoyer vers et si ? » depuis un article : date, scénarios et mode IMPOSÉS
mécaniquement (l'IA ne les devine plus). Par défaut : date = année de l'article, scénarios =
celui de l'article, mode = choc. Cases pour élargir à tous les scénarios ou passer en rupture.
Fichiers : generator/hypothese_depuis_texte.py, gui/app.py, gui/static/app.js.
Dry-run par défaut ; --apply écrit (sauvegardes .bak_u3c). Depuis la racine du vault :
    python3 generator/patch_u3c_valeurs_imposees.py [--apply]"""
import sys, shutil, subprocess, py_compile
from pathlib import Path
APPLY = "--apply" in sys.argv
ROOT = Path(sys.argv[sys.argv.index("--root")+1]) if "--root" in sys.argv else Path(".")
HT = ROOT / "generator" / "hypothese_depuis_texte.py"
APP = ROOT / "gui" / "app.py"
JS = ROOT / "gui" / "static" / "app.js"

HT_EDITS = [
 (r'''def construire_prompt(texte, variables, type_force=None):
    ligne_type = (f"TYPE IMPOSÉ PAR L'AUTEUR : {type_force} (ne le change pas).\n\n"
                  if type_force else "")
''',
  r'''def construire_prompt(texte, variables, type_force=None, imposes=None):
    ligne_type = (f"TYPE IMPOSÉ PAR L'AUTEUR : {type_force} (ne le change pas).\n\n"
                  if type_force else "")
    if imposes:   # U3c : valeurs tirées de la source (article), imposées ensuite mécaniquement
        morceaux = []
        if imposes.get("date"):
            morceaux.append(f"date {imposes['date']}")
        if imposes.get("scenarios") is not None:
            morceaux.append("scénarios : " + (", ".join(imposes["scenarios"]) if imposes["scenarios"] else "tous"))
        if imposes.get("mode"):
            morceaux.append(f"mode {imposes['mode']}")
        if morceaux:
            ligne_type += "VALEURS IMPOSÉES PAR L'AUTEUR (ne les change pas) : " + " ; ".join(morceaux) + ".\n\n"
'''),
 (r'''def proposer(texte, _llm=appeler_llm, type_force=None):
''',
  r'''def appliquer_imposes(h, imposes, est_signal):
    """U3c : date, scénarios et mode venant de la source (article), imposés APRÈS la réponse de
    l'IA. Chaque écart avec sa proposition est signalé. Retourne la liste d'avertissements."""
    av = []
    if not imposes:
        return av
    d = imposes.get("date")
    if d is not None:
        plancher = max(2026, datetime.now().year) if est_signal else 2026
        d2 = min(2097, max(plancher, int(d)))
        if d2 != int(d):
            av.append(f"date imposée {d} hors de {plancher}-2097 -> {d2}")
        if h.get("date") != d2:
            av.append(f"date imposée : {d2} (l'IA proposait {h.get('date')})")
        h["date"] = d2
    if est_signal:
        return av   # un signal couvre toujours les 6 scénarios, sans mode rupture
    sc = imposes.get("scenarios")
    if sc is not None:
        valides = [s for s in sc if s in se.SCENARIOS]
        if sc and not valides:
            av.append(f"scénario(s) imposé(s) inconnu(s), ignoré(s) : {sc}")
        else:
            if len(valides) != len(sc):
                av.append(f"scénario(s) imposé(s) inconnu(s) retiré(s) : {[s for s in sc if s not in se.SCENARIOS]}")
            cible = valides if 0 < len(valides) < len(se.SCENARIOS) else "tous"
            if h.get("scenarios") != cible:
                av.append(f"scénarios imposés : {cible} (l'IA proposait {h.get('scenarios')})")
            h["scenarios"] = cible
    mode = imposes.get("mode")
    if mode in ("choc", "rupture"):
        if h.get("mode") != mode:
            av.append(f"mode imposé : {mode} (l'IA proposait {h.get('mode')})")
        h["mode"] = mode
        if mode == "rupture":
            h.pop("persistance", None)
        else:
            h.setdefault("persistance", dyn.PERSISTANCE_DEFAUT)
    return av


def proposer(texte, _llm=appeler_llm, type_force=None, imposes=None):
'''),
 (r'''    brut = _llm(construire_prompt(texte, variables, type_force))
''',
  r'''    brut = _llm(construire_prompt(texte, variables, type_force, imposes))
'''),
 (r'''    h, av = normaliser_proposition(brut, variables, ids_existants())
''',
  r'''    h, av = normaliser_proposition(brut, variables, ids_existants())
    av += appliquer_imposes(h, imposes, h.get("type") == "signal")   # U3c
'''),
 (r'''                    help="avec --proposer : impose le type (sinon l'IA décide)")
''',
  r'''                    help="avec --proposer : impose le type (sinon l'IA décide)")
    ap.add_argument("--date", type=int, default=None, help="avec --proposer : année imposée")
    ap.add_argument("--scenarios", default=None,
                    help="avec --proposer : scénarios imposés (a,b,c) ou « tous »")
    ap.add_argument("--mode", choices=("choc", "rupture"), default=None,
                    help="avec --proposer : mode imposé (événement seulement)")
'''),
 (r'''            res = proposer(texte, type_force=args.type)
''',
  r'''            imposes = {}
            if args.date is not None:
                imposes["date"] = args.date
            if args.scenarios is not None:
                imposes["scenarios"] = ([] if args.scenarios.strip() in ("", "tous")
                                        else [s.strip() for s in args.scenarios.split(",") if s.strip()])
            if args.mode:
                imposes["mode"] = args.mode
            res = proposer(texte, type_force=args.type, imposes=imposes or None)
'''),
]

APP_EDITS = [
 (r'''        cmd += ["--type", data["type"]]
''',
  r'''        cmd += ["--type", data["type"]]
    if action == "proposer":   # U3c : date, scénarios et mode imposés par la source (article)
        try:
            if data.get("date") not in (None, ""):
                cmd += ["--date", str(int(data["date"]))]
        except (TypeError, ValueError):
            pass
        if isinstance(data.get("scenarios"), list):
            sc_ = [s for s in data["scenarios"] if isinstance(s, str) and re.fullmatch(r"[a-z_]+", s)]
            cmd += ["--scenarios", ",".join(sc_) if sc_ else "tous"]
        if data.get("mode") in ("choc", "rupture"):
            cmd += ["--mode", data["mode"]]
'''),
]

JS_EDITS = [
 (r'''  const appeler = async (action, corps, type) => {
    try {
      const res = await fetch(`/api/et_si/${action}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texte: corps, type: action === 'proposer' ? type : '' }),''',
  r'''  const appeler = async (action, corps, type, extra) => {
    try {
      const res = await fetch(`/api/et_si/${action}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texte: corps, type: action === 'proposer' ? type : '',
                               ...(action === 'proposer' ? (extra || {}) : {}) }),'''),
 (r'''  ligne.appendChild(selType); ligne.appendChild(btn);
  boite.appendChild(ligne);
''',
  r'''  ligne.appendChild(selType); ligne.appendChild(btn);
  boite.appendChild(ligne);
  // U3c : valeurs tirées de l'article, imposées à l'IA (elle ne les devine plus)
  const reglages = mk('div', '', 'display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:8px;font-size:11px');
  const champDate = document.createElement('input');
  champDate.type = 'number'; champDate.min = '2026'; champDate.max = '2097'; champDate.style.width = '80px';
  champDate.value = article.annee != null ? Math.min(2097, Math.max(2026, article.annee)) : '';
  const lblDate = mk('label', 'Date de l\'événement :', 'margin:0');
  lblDate.appendChild(champDate);
  const caseOui = (texteCase) => {
    const l = mk('label', '', 'margin:0;display:flex;align-items:center;gap:4px');
    const c = document.createElement('input'); c.type = 'checkbox';
    l.appendChild(c); l.appendChild(document.createTextNode(texteCase));
    return [l, c];
  };
  const [lblTous, cbTous] = caseOui(`valable pour les 6 scénarios (sinon : « ${article.scenario} » seulement)`);
  const [lblRupt, cbRupt] = caseOui('mode rupture (déplace durablement le monde)');
  [lblDate, lblTous, lblRupt].forEach(e => reglages.appendChild(e));
  boite.appendChild(reglages);
  const majReglages = () => {   // un signal couvre toujours les 6 scénarios, sans mode rupture
    const sig = selType.value === 'signal';
    [cbTous, cbRupt].forEach(c => { c.disabled = sig; });
    [lblTous, lblRupt].forEach(l => { l.style.opacity = sig ? '0.4' : ''; });
  };
  selType.addEventListener('change', majReglages);
  majReglages();
'''),
 (r'''    const data = await appeler('proposer', texte, selType.value);
    btn.disabled = false;
    if (data.error || !data.bloc) {
      etat.style.color = '#b03a2e';''',
  r'''    const extra = { date: champDate.value ? parseInt(champDate.value, 10) : null };
    if (selType.value !== 'signal') {
      extra.scenarios = cbTous.checked ? [] : [article.scenario];
      extra.mode = cbRupt.checked ? 'rupture' : 'choc';
    }
    const data = await appeler('proposer', texte, selType.value, extra);
    btn.disabled = false;
    if (data.error || !data.bloc) {
      etat.style.color = '#b03a2e';'''),
]

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
    shutil.copy2(p, p.with_name(p.name + ".bak_u3c"))
HT.write_text(ht, encoding="utf-8"); APP.write_text(ap_, encoding="utf-8"); JS.write_text(js, encoding="utf-8")
try:
    py_compile.compile(str(HT), doraise=True); py_compile.compile(str(APP), doraise=True)
except py_compile.PyCompileError as e:
    for p in (HT, APP, JS):
        shutil.copy2(p.with_name(p.name + ".bak_u3c"), p)
    print(f"✗ erreur de syntaxe Python, fichiers restaurés : {e}"); sys.exit(1)
avant, apres = node_ok(JS.with_name(JS.name + ".bak_u3c")), node_ok(JS)
if avant is True and apres is False:
    for p in (HT, APP, JS):
        shutil.copy2(p.with_name(p.name + ".bak_u3c"), p)
    print("✗ erreur de syntaxe JavaScript introduite : fichiers restaurés"); sys.exit(1)
print("✓ appliqué" + ("" if apres else " (contrôle node non concluant : node absent ou déjà en erreur avant le patch)"))
