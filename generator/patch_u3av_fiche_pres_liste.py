#!/usr/bin/env python3
"""
patch_u3av_fiche_pres_liste.py — Ourrassol 2098 (14 novembre 2026)

Suite de U3at/U3au. Deux défauts vus à l'usage :
  - la description attendait la réponse (lente) du statut avant de s'afficher ;
  - le volet flottant était loin de la liste, texte pâle et difficile à lire.
Correctifs :
  gui/app.py : nouvelle route POST /api/et_si/fiche, lecture directe de
               hypotheses.yaml dans Flask (instantanée, sans lancer de script) ;
  gui/static/app.js : la fiche est demandée dès le choix dans la liste et
               s'affiche JUSTE SOUS la liste « Hypothèse » (dans le flux, plus de
               volet flottant), texte à contraste normal, fond bleuté.
Prérequis : U3at. Après application : redémarrer Flask ; Cmd+Maj+R.

    python3 generator/patch_u3av_fiche_pres_liste.py            # aperçu
    python3 generator/patch_u3av_fiche_pres_liste.py --apply
Sauvegardes .bak_u3av ; refuse un second passage ; contrôles de syntaxe avec restauration.
"""
import argparse
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3av"
APP_PY = Path("gui/app.py")
APP_JS = Path("gui/static/app.js")

PY_REMPL = [(
    "route /api/et_si/fiche",
    '@app.route("/api/et_si/statut", methods=["POST"])\n',
    r"""@app.route("/api/et_si/fiche", methods=["POST"])
def et_si_fiche():   # U3av : fiche d'une hypothèse, lecture directe (rapide)
    import yaml as _yaml
    hid = str((request.get_json() or {}).get("id") or "").strip()
    if not hid:
        return jsonify({"hypothese": None})
    chemin = Path(load_config().get("pipeline_dir", "")).parent / "et_si" / "hypotheses.yaml"
    try:
        data = _yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    except (OSError, _yaml.YAMLError) as e:
        return jsonify({"error": f"hypotheses.yaml illisible : {e}"}), 500
    for h in data.get("hypotheses") or []:
        if isinstance(h, dict) and str(h.get("id")) == hid:
            fiche = {}
            for k in ("nom", "type", "date", "mode", "categorie", "scenario_ref", "scenarios",
                      "role", "etat", "description"):
                v = h.get(k)
                if v in (None, "", []):
                    continue
                fiche[k] = [str(x) for x in v] if isinstance(v, list) else (v if isinstance(v, (int, float)) else str(v))
            return jsonify({"hypothese": fiche})
    return jsonify({"hypothese": None})


@app.route("/api/et_si/statut", methods=["POST"])
""",
)]

STYLE_U3AT = "  ficheEl.style.cssText = 'display:none;border:1px solid #d5dbe1;border-radius:6px;padding:6px 8px;margin:6px 0;';\n"
STYLE_U3AU = ("  ficheEl.style.cssText = 'display:none;position:fixed;top:90px;right:16px;width:340px;max-height:65vh;"
              "overflow:auto;z-index:900;background:Canvas;color:CanvasText;border:1px solid #9aa5b1;"
              "border-radius:8px;padding:8px 10px;box-shadow:0 4px 16px rgba(0,0,0,.25);';\n")
STYLE_NEW = ("  // U3av : dans le flux, sous la liste des hypothèses\n"
             "  ficheEl.style.cssText = 'display:none;border:1px solid #9aa5b1;border-left:4px solid #2e86c1;"
             "border-radius:6px;padding:8px 10px;margin:8px 0 12px;background:rgba(46,134,193,.08);color:CanvasText;';\n")

JS_FIXES = [
    (
        "texte lisible",
        "  const ficheCorps = mk('div', 'option-desc');\n  ficheCorps.style.whiteSpace = 'pre-wrap';\n",
        "  const ficheCorps = mk('div', 'option-desc');\n  ficheCorps.style.whiteSpace = 'pre-wrap';\n"
        "  ficheMeta.style.color = 'CanvasText';   // U3av\n"
        "  ficheCorps.style.color = 'CanvasText';\n  ficheCorps.style.fontSize = '13px';\n",
    ),
    (
        "placement sous la liste",
        "      ficheEl.style.display = '';\n",
        "      placerFiche();   // U3av\n      ficheEl.style.display = '';\n",
    ),
    (
        "chargement rapide",
        "    if (!id) { afficher(null); return; }\n    try {\n      const res = await fetch('/api/et_si/statut', {\n",
        "    if (!id) { afficher(null); return; }\n    chargerFiche(id);   // U3av : description immédiate, sans attendre le statut\n"
        "    try {\n      const res = await fetch('/api/et_si/statut', {\n",
    ),
    (
        "fonctions chargerFiche / placerFiche",
        "  const actualiser = async () => {\n",
        r"""  // U3av : la fiche s'affiche juste sous la liste « Hypothèse »
  const placerFiche = () => {
    const sel = listeHyp();
    if (!sel || !sel.parentElement) return false;
    if (ficheEl.previousElementSibling !== sel.parentElement) sel.parentElement.insertAdjacentElement('afterend', ficheEl);
    return true;
  };
  const remplirFiche = (fi) => {
    if (!fi || !placerFiche()) { ficheEl.style.display = 'none'; return; }
    ficheMeta.textContent = [fi.nom, fi.type === 'entite' ? 'entité' : (fi.type || 'événement'),
                    fi.date != null ? `date ${fi.date}` : '', fi.mode ? `mode ${fi.mode}` : '',
                    fi.categorie ? `catégorie ${fi.categorie}` : '',
                    fi.scenario_ref ? `réf. ${fi.scenario_ref}` : '',
                    (fi.scenarios && fi.scenarios.length) ? `scénarios : ${[].concat(fi.scenarios).join(', ')}` : '']
      .filter(Boolean).join(' · ');
    ficheCorps.textContent = [fi.description, fi.role ? `Rôle : ${fi.role}` : '', fi.etat ? `État : ${fi.etat}` : '']
      .filter(Boolean).join('\n\n') || '(pas de description)';
    ficheEl.style.display = '';
  };
  const chargerFiche = async (id) => {
    try {
      const res = await fetch('/api/et_si/fiche', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }),
      });
      const data = await res.json();
      remplirFiche(data.hypothese);
    } catch (err) {
      ficheEl.style.display = 'none';
    }
  };

  const actualiser = async () => {
""",
    ),
]


def _node_check(chemin):
    try:
        r = subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None, "node absent"
    return r.returncode == 0, r.stderr.strip()


def _premiere_erreur(msg):
    lignes = [l for l in msg.splitlines() if l.strip()]
    return " | ".join(l.strip() for l in lignes[:4] if "SyntaxError" in l or l.strip().startswith("("))[:300]


def verifier_js(chemin, original):
    """Ne bloque que sur une erreur NOUVELLE (un vieux node refuse déjà « ||= » dans l'original)."""
    ok, msg = _node_check(chemin)
    if ok:
        return True, "node --check OK"
    if ok is False:
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "original.js"
            copie.write_text(Path(original).read_text(encoding="utf-8"), encoding="utf-8")
            ok0, msg0 = _node_check(copie)
        if ok0 is False and _premiere_erreur(msg) == _premiere_erreur(msg0):
            return True, "node --check refuse une syntaxe déjà présente dans l'original : aucune erreur nouvelle"
        return False, msg[:400]
    t = chemin.read_text(encoding="utf-8")
    ok2 = t.count("{") == t.count("}") and t.count("(") == t.count(")")
    return ok2, "accolades/parenthèses équilibrées (node absent)" if ok2 else "accolades/parenthèses déséquilibrées"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--py", default=str(APP_PY))
    ap.add_argument("--js", default=str(APP_JS))
    a = ap.parse_args()
    prepares = []
    for chemin in (Path(a.py), Path(a.js)):
        if not chemin.exists():
            print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
            return 2
    py, js = Path(a.py), Path(a.js)
    tpy, tjs = py.read_text(encoding="utf-8"), js.read_text(encoding="utf-8")
    if "U3at" not in tjs:
        print("✗ Prérequis U3at absent de app.js.")
        return 1
    if MARQUEUR in tpy or MARQUEUR in tjs:
        print(f"✗ {MARQUEUR} déjà appliqué — refus d'un second passage.")
        return 1
    remp_js = [("style de l'encadré", STYLE_U3AU if STYLE_U3AU in tjs else STYLE_U3AT, STYLE_NEW)] + JS_FIXES
    for chemin, texte, remp in ((py, tpy, PY_REMPL), (js, tjs, remp_js)):
        nouveau = texte
        for libelle, ancre, rempl in remp:
            n = nouveau.count(ancre)
            if n != 1:
                print(f"✗ {chemin.name} : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
                return 1
            nouveau = nouveau.replace(ancre, rempl, 1)
            print(f"  ✓ {chemin.name} : {libelle}")
        prepares.append((chemin, texte, nouveau))
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, _, apres in prepares:
        bak = chemin.with_name(chemin.name + ".bak_u3av")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(apres, encoding="utf-8")

    def restaurer():
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)

    try:
        py_compile.compile(str(baks[0][0]), doraise=True)
    except py_compile.PyCompileError as e:
        restaurer()
        print(f"✗ py_compile a échoué, fichiers restaurés : {e}")
        return 1
    ok, msg = verifier_js(baks[1][0], baks[1][1])
    if not ok:
        restaurer()
        print(f"✗ Contrôle de syntaxe app.js échoué, fichiers restaurés : {msg}")
        return 1
    print(f"  (app.js : {msg})")
    for chemin, bak in baks:
        print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})")
    print("\nÀ faire : redémarrer Flask ; Cmd+Maj+R dans le navigateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
