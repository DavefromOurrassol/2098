#!/usr/bin/env python3
"""
patch_s27_gui_decider.py — Ourrassol 2098 (S27, point 3 « décider » dans le GUI, 12 octobre 2026)
================================================================================================

Panneau « ⚖️ Décider » sous le formulaire du simulateur « et si ? » (mode
« Simuler »), sur l'hypothèse choisie dans la liste : Aperçu, Adopter, Rejeter
(motif), Annuler la décision, Voir les dossiers. Chaque bouton appelle
simuler_et_si.py (--adopter, --rejeter, --annuler-decision, --dossiers) ;
aucune logique dupliquée dans le GUI.

Fichiers (tout ou rien) :
  generator/simuler_et_si.py  v8.17 -> v8.17.1 (messages d'annulation déjà
                              préfixés ✓ / ⚠ par et_si_dossiers.py) ;
  gui/app.py                  route POST /api/et_si/decider/<action> ;
  gui/static/app.js           buildDecisionHypothese() + appel ;
  gui/scripts_config.json     clé assistant_decision sur simuler_et_si.

et_si_dossiers.py (nouvelle version, à copier AVANT) : « Annuler la décision »
retire de la queue l'entrée adoptée pas encore injectée.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_gui_decider.py --dry-run && python3 generator/patch_s27_gui_decider.py
Sauvegardes .bak_gui_decider ; refuse un second passage. Redémarrer Flask, puis
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

GENERATOR = Path(__file__).resolve().parent
VAULT = GENERATOR.parent
MARQUE = "PATCH_S27_GUI_DECIDER"

SIMULATEUR = [
    ('VERSION = "v8.17"', 'VERSION = "v8.17.1"', 1),
    ('            ancien, avert = ed.annuler_decision(hid)\n'
     '            print(f"✓ Décision retirée ({ancien}) : {hid} revient à « {ed.statut(hid)} ».")\n'
     '            for a in avert:\n'
     '                print(f"  ⚠ {a}")\n',
     '            # V8.17.1 (PATCH_S27_GUI_DECIDER) : messages déjà préfixés ✓ / ⚠.\n'
     '            ancien, messages = ed.annuler_decision(hid)\n'
     '            print(f"✓ Décision retirée ({ancien}) : {hid} revient à « {ed.statut(hid)} ».")\n'
     '            for m in messages:\n'
     '                print(f"  {m}")\n', 1),
]

ROUTE = '''# ---------------------------------------------------------------------------
# Simulateur « et si ? » v8.17.1 (12 octobre 2026, PATCH_S27_GUI_DECIDER) --
# panneau « Décider » : appelle simuler_et_si.py --dossiers / --adopter /
# --rejeter / --annuler-decision (et_si_dossiers.py). Aucun appel IA ; seul
# « adopter » (sans apercu) écrit, dans evenements_custom/queue.yaml
# (sauvegarde .bak_et_si) ; « annuler » peut en retirer l'entrée adoptée.
# ---------------------------------------------------------------------------

ACTIONS_DECIDER = {"dossiers": "--dossiers", "adopter": "--adopter",
                   "rejeter": "--rejeter", "annuler": "--annuler-decision"}


@app.route("/api/et_si/decider/<action>", methods=["POST"])
def et_si_decider(action):
    if action not in ACTIONS_DECIDER:
        return jsonify({"error": f"action inconnue : {action}"}), 404
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}
    hid = str(data.get("id") or "").strip()
    cmd = [sys.executable, "simuler_et_si.py", ACTIONS_DECIDER[action]]
    if action != "dossiers":
        if not hid:
            return jsonify({"error": "choisis d'abord une hypothèse dans la liste"}), 400
        cmd.append(hid)
    if action == "adopter":
        for cle in ("portee", "intensite"):
            if data.get(cle):
                cmd += [f"--{cle}", str(data[cle])]
        if data.get("apercu"):
            cmd.append("--apercu")
    if action == "rejeter" and str(data.get("motif") or "").strip():
        cmd += ["--motif", str(data["motif"]).strip()]
    try:
        resultat = subprocess.run(cmd, cwd=pipeline_dir, capture_output=True, text=True,
                                  timeout=120, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Délai dépassé (120 s)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"simuler_et_si.py introuvable dans {pipeline_dir}"}), 500
    sortie = "\\n".join(s for s in (resultat.stdout.strip(), resultat.stderr.strip()) if s)
    return jsonify({"ok": resultat.returncode == 0, "sortie": sortie})


'''

APP_PY = [
    ('TIMEOUT_IDEES_TEXTE_LIBRE = 180  # secondes -- un seul appel LLM\n',
     ROUTE + 'TIMEOUT_IDEES_TEXTE_LIBRE = 180  # secondes -- un seul appel LLM\n', 1),
]

FONCTION_JS = r'''

// ══════════════════════════════════════════════════
// PANNEAU « DÉCIDER » (simulateur « et si ? » v8.17.1, 12 octobre 2026, PATCH_S27_GUI_DECIDER)
// ══════════════════════════════════════════════════
// Clé assistant_decision dans scripts_config.json, visible en mode « Simuler ».
// Agit sur l'hypothèse choisie dans la liste --id, via /api/et_si/decider/<action>
// (app.py -> simuler_et_si.py -> et_si_dossiers.py). Seul « Adopter » écrit
// (evenements_custom/queue.yaml) ; l'injection reste à lancer à part.
function buildDecisionHypothese() {
  const wrapper = document.createElement('div');
  wrapper.className = 'yaml-panel';
  wrapper.dataset.modeOnly = 'simuler';

  const mk = (tag, cls, txt) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt) e.textContent = txt;
    return e;
  };
  const bouton = (txt, cls) => {
    const b = mk('button', cls || 'yaml-btn', txt);
    b.type = 'button';
    b.style.margin = '4px 8px 4px 0';
    return b;
  };
  const choix = (options) => {
    const s = mk('select');
    options.forEach(([v, l]) => { const o = mk('option', null, l); o.value = v; s.appendChild(o); });
    s.style.marginRight = '12px';
    return s;
  };

  const header = mk('div', 'yaml-panel-header');
  const titleRow = mk('div', 'yaml-panel-title-row');
  titleRow.appendChild(mk('span', 'yaml-panel-title', '⚖️ Décider (hypothèse choisie dans la liste)'));
  header.appendChild(titleRow);
  wrapper.appendChild(header);

  const corps = mk('div', 'yaml-form-zone');
  corps.style.padding = '8px 0';
  corps.appendChild(mk('div', 'option-desc',
    'Après une simulation de TOUS les scénarios (sans « Scénario » limité). « Adopter » écrit l\'entrée ' +
    'd\'injection de cette dernière simulation dans evenements_custom/queue.yaml ; l\'injection reste à ' +
    'lancer à part. « Rejeter » garde la trace et le motif. « Annuler la décision » remet l\'hypothèse à ' +
    '« simulé » et retire de la queue l\'entrée adoptée si elle n\'est pas encore injectée. ' +
    'Le statut s\'affiche dans la liste des hypothèses. Aucun appel IA.'));

  const ligneChoix = mk('div');
  ligneChoix.style.margin = '6px 0';
  ligneChoix.appendChild(mk('span', 'option-label', 'Portée '));
  const portee = choix([['', '— celle de la simulation —'], ['locale', 'locale'], ['regionale', 'régionale'],
                        ['continentale', 'continentale'], ['globale', 'globale']]);
  ligneChoix.appendChild(portee);
  ligneChoix.appendChild(mk('span', 'option-label', 'Intensité '));
  const intensite = choix([['', '— à choisir —'], ['faible', 'faible'], ['modérée', 'modérée'],
                           ['forte', 'forte'], ['majeure', 'majeure']]);
  ligneChoix.appendChild(intensite);
  corps.appendChild(ligneChoix);

  const ligneAdopter = mk('div');
  const btnApercu = bouton('Aperçu de l\'adoption');
  const btnAdopter = bouton('Adopter (écrit dans la queue)', 'yaml-btn yaml-btn-save');
  ligneAdopter.appendChild(btnApercu);
  ligneAdopter.appendChild(btnAdopter);
  corps.appendChild(ligneAdopter);

  const ligneRejeter = mk('div');
  const motif = mk('input');
  motif.type = 'text';
  motif.placeholder = 'motif du rejet (facultatif)';
  motif.autocomplete = 'off';
  motif.style.width = '50%';
  motif.style.marginRight = '8px';
  const btnRejeter = bouton('Rejeter');
  ligneRejeter.appendChild(motif);
  ligneRejeter.appendChild(btnRejeter);
  corps.appendChild(ligneRejeter);

  const ligneAutres = mk('div');
  const btnAnnuler = bouton('Annuler la décision');
  const btnDossiers = bouton('Voir les dossiers');
  ligneAutres.appendChild(btnAnnuler);
  ligneAutres.appendChild(btnDossiers);
  corps.appendChild(ligneAutres);

  const sortie = mk('pre');
  sortie.style.whiteSpace = 'pre-wrap';
  sortie.style.fontSize = '0.85em';
  sortie.style.marginTop = '6px';
  corps.appendChild(sortie);
  wrapper.appendChild(corps);

  const tous = [btnApercu, btnAdopter, btnRejeter, btnAnnuler, btnDossiers];
  const listeHyp = () => document.querySelector('#form-body [data-slug-type="hypotheses_et_si"]');

  const appeler = async (action, extra, rafraichir) => {
    const sel = listeHyp();
    const id = sel ? sel.value : '';
    if (action !== 'dossiers' && !id) {
      sortie.textContent = '✗ Choisis d\'abord une hypothèse dans la liste.';
      sortie.style.color = '#b03a2e';
      return;
    }
    tous.forEach(b => { b.disabled = true; });
    sortie.style.color = '';
    sortie.textContent = '…';
    let data;
    try {
      const res = await fetch(`/api/et_si/decider/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.assign({ id }, extra || {})),
      });
      data = await res.json();
    } catch (e) {
      data = { error: `Erreur réseau : ${e.message}` };
    }
    tous.forEach(b => { b.disabled = false; });
    sortie.textContent = data.error ? `✗ ${data.error}` : (data.sortie || '(aucune sortie)');
    sortie.style.color = (data.error || !data.ok) ? '#b03a2e' : '';
    if (data.ok && rafraichir && sel) {
      // La liste est reconstruite (statut à jour) : on remet l'hypothèse choisie.
      await rafraichirChampDynamique(sel);
      sel.value = id;
    }
  };

  const adoption = () => ({ portee: portee.value, intensite: intensite.value });

  btnApercu.addEventListener('click', () => appeler('adopter', Object.assign(adoption(), { apercu: true }), false));
  btnAdopter.addEventListener('click', () => {
    if (!confirm('Écrire l\'entrée de la dernière simulation dans evenements_custom/queue.yaml ?\n' +
                 '(Elle sera injectée au prochain inject_custom_events.py --mode custom.)')) return;
    appeler('adopter', adoption(), true);
  });
  btnRejeter.addEventListener('click', () => appeler('rejeter', { motif: motif.value }, true));
  btnAnnuler.addEventListener('click', () => {
    if (!confirm('Annuler la décision prise sur cette hypothèse ?')) return;
    appeler('annuler', {}, true);
  });
  btnDossiers.addEventListener('click', () => appeler('dossiers', {}, false));

  return wrapper;
}
'''

APP_JS = [
    ('  if (script.assistant_hypothese) body.appendChild(buildAssistantHypothese());\n',
     '  if (script.assistant_hypothese) body.appendChild(buildAssistantHypothese());\n'
     '  // Panneau « Décider » (PATCH_S27_GUI_DECIDER, 12 octobre 2026), mode « Simuler ».\n'
     '  if (script.assistant_decision) body.appendChild(buildDecisionHypothese());\n', 1),
]


def appliquer(chemin, remplacements, attendu):
    texte = chemin.read_text(encoding="utf-8")
    if MARQUE in texte:
        sys.exit(f"✗ {chemin.name} : patch déjà appliqué : rien à faire.")
    if attendu and attendu not in texte:
        sys.exit(f"✗ {chemin.name} : version attendue absente ({attendu!r}) : rien écrit.")
    for n, (avant, apres, compte_attendu) in enumerate(remplacements, 1):
        compte = texte.count(avant)
        if compte != compte_attendu:
            sys.exit(f"✗ {chemin.name}, ancre n°{n} trouvée {compte} fois ({compte_attendu} attendue) : "
                     f"rien écrit.\n  Début de l'ancre : {avant[:80]!r}")
        texte = texte.replace(avant, apres)
    return texte


def compile_py(nom, texte):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(texte)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ {nom} patché ne compile pas, rien écrit : {e}")
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass


def _node_check(texte):
    """None si node absent, sinon (ok, stderr)."""
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


def verifier_js(original, texte):
    """Contrôle de syntaxe avec node, seulement si node accepte déjà l'app.js
    d'origine (un node trop ancien refuse la syntaxe récente qu'il contient)."""
    if _node_check(original) in (None,) or not _node_check(original)[0]:
        # node absent ou trop ancien : on vérifie au moins la fonction ajoutée seule.
        seul = _node_check(FONCTION_JS)
        if seul is None:
            return "node absent : syntaxe JS non vérifiée"
        if not seul[0]:
            sys.exit(f"✗ fonction JS ajoutée : erreur de syntaxe, rien écrit :\n{seul[1][-800:]}")
        return "syntaxe de la fonction ajoutée vérifiée (node trop ancien pour app.js entier)"
    ok, err = _node_check(texte)
    if not ok:
        sys.exit(f"✗ app.js patché : erreur de syntaxe, rien écrit :\n{err[-800:]}")
    return "syntaxe JS vérifiée (node)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--vault", default=str(VAULT))
    args = ap.parse_args()
    v = Path(args.vault)
    sim, app_py = v / "generator" / "simuler_et_si.py", v / "gui" / "app.py"
    app_js, conf = v / "gui" / "static" / "app.js", v / "gui" / "scripts_config.json"
    for f in (sim, app_py, app_js, conf, v / "generator" / "et_si_dossiers.py"):
        if not f.exists():
            sys.exit(f"✗ {f} introuvable : rien écrit.")
    if "def _retirer_de_queue" not in (v / "generator" / "et_si_dossiers.py").read_text(encoding="utf-8"):
        sys.exit("✗ generator/et_si_dossiers.py n'est pas la nouvelle version : la copier d'abord. Rien écrit.")

    t_sim = appliquer(sim, SIMULATEUR, 'VERSION = "v8.17"')
    compile_py(sim.name, t_sim)
    t_py = appliquer(app_py, APP_PY, None)
    compile_py(app_py.name, t_py)
    t_js = appliquer(app_js, APP_JS, "function buildAssistantHypothese()")
    t_js = t_js.rstrip("\n") + "\n" + FONCTION_JS
    note_js = verifier_js(app_js.read_text(encoding="utf-8"), t_js)

    t_conf = conf.read_text(encoding="utf-8")
    data = json.loads(t_conf)
    if json.dumps(data, ensure_ascii=False, indent=2) != t_conf:
        sys.exit("✗ Mise en forme de scripts_config.json inattendue : rien écrit.")
    entrees = [e for e in data if e.get("id") == "simuler_et_si"]
    if len(entrees) != 1:
        sys.exit(f"✗ Entrée simuler_et_si trouvée {len(entrees)} fois : rien écrit.")
    if entrees[0].get("assistant_decision"):
        sys.exit("✗ scripts_config.json : patch déjà appliqué : rien à faire.")
    entrees[0]["assistant_decision"] = True
    t_conf2 = json.dumps(data, ensure_ascii=False, indent=2)

    if args.dry_run:
        print(f"✓ 4 fichiers patchables, compilation OK, {note_js} (dry-run, rien écrit).")
        return
    for chemin, texte in ((sim, t_sim), (app_py, t_py), (app_js, t_js), (conf, t_conf2)):
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_gui_decider"))
        chemin.write_text(texte, encoding="utf-8")
    print("✓ Panneau « Décider » ajouté (simuler_et_si.py v8.17.1, app.py, app.js, scripts_config.json) ; "
          "sauvegardes .bak_gui_decider. Redémarrer Flask, puis recharger la page sans cache (Cmd+Maj+R).")


if __name__ == "__main__":
    main()
