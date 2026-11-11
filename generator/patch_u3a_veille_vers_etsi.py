#!/usr/bin/env python3
"""patch_u3a — veille 🔭 : « ✨ Envoyer vers « et si ? » » remplace « Préparer l'entrée de queue ».
Le candidat devient une HYPOTHÈSE (hypotheses.yaml) ; nouveau statut « en hypothèse ».
Dry-run par défaut ; --apply écrit (sauvegardes .bak_u3a). Depuis la racine du vault :
    python3 generator/patch_u3a_veille_vers_etsi.py [--apply]"""
import sys, shutil, subprocess, py_compile
from pathlib import Path
APPLY = "--apply" in sys.argv
ROOT = Path(sys.argv[sys.argv.index("--root")+1]) if "--root" in sys.argv else Path(".")
JS = ROOT / "gui" / "static" / "app.js"
PY = ROOT / "gui" / "routes_veille_signaux.py"

NOUVELLE_FONCTION = r'''async function _veilleVersEtSi(c) {
  // U3a : le candidat devient une hypothèse « et si ? » (même chemin que ✨ Nouvelle hypothèse).
  const btn = document.getElementById('veille-btn-preparer');
  const etat = document.getElementById('veille-action-etat');
  const type = document.getElementById('veille-type').value;
  const zone = document.getElementById('veille-proposition');
  if (btn.disabled) return;
  const appeler = async (action, texte) => {
    try {
      const res = await fetch(`/api/et_si/${action}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texte, type: action === 'proposer' ? type : '' }),
      });
      return await res.json();
    } catch (e) {
      return { error: `Erreur réseau : ${e.message}` };
    }
  };
  const afficher = (el, data, titreOk) => {
    const lignes = [];
    if (data.error) lignes.push(`✗ ${data.error}`);
    (data.erreurs || []).forEach(e => lignes.push(`✗ ${e}`));
    (data.avertissements || []).forEach(a => lignes.push(`⚠ ${a}`));
    if (data.justification) lignes.push(`💬 ${data.justification}`);
    if (!data.error && !(data.erreurs || []).length && titreOk) lignes.unshift(titreOk);
    el.textContent = lignes.join('\n');
    el.style.color = (data.error || (data.erreurs || []).length) ? '#b03a2e' : '';
  };
  btn.disabled = true;
  etat.textContent = 'Appel IA en cours (hypothese_depuis_texte.py)…';
  const data = await appeler('proposer', _veilleTexteProposition(c));
  btn.disabled = false;
  if (data.error || !data.bloc) {
    etat.textContent = `Erreur : ${data.error || 'aucun bloc proposé'}`;
    return;
  }
  etat.textContent = 'Relis le bloc, « Vérifier », puis « Ajouter à hypotheses.yaml ». Rien n\'est écrit avant.';

  zone.innerHTML = '';
  const retour = document.createElement('div');
  retour.className = 'option-desc';
  retour.style.whiteSpace = 'pre-wrap';
  afficher(retour, data, '✓ Proposition prête.');
  const bloc = document.createElement('textarea');
  bloc.className = 'yaml-edit';
  bloc.rows = 18;
  bloc.spellcheck = false;
  bloc.style.cssText = 'display:block;width:100%;font-family:monospace;margin:6px 0';
  bloc.value = data.bloc;
  const ligne = document.createElement('div');
  const btnVerifier = document.createElement('button');
  btnVerifier.type = 'button'; btnVerifier.className = 'yaml-btn'; btnVerifier.textContent = 'Vérifier';
  const btnAjouter = document.createElement('button');
  btnAjouter.type = 'button'; btnAjouter.className = 'yaml-btn yaml-btn-save';
  btnAjouter.style.marginLeft = '8px'; btnAjouter.textContent = 'Ajouter à hypotheses.yaml';
  ligne.appendChild(btnVerifier); ligne.appendChild(btnAjouter);
  const statut = document.createElement('div');
  statut.className = 'option-desc';
  statut.style.cssText = 'white-space:pre-wrap;margin-top:6px';
  [retour, bloc, ligne, statut].forEach(e => zone.appendChild(e));

  const occupe = (oui) => { btnVerifier.disabled = oui; btnAjouter.disabled = oui; };
  btnVerifier.addEventListener('click', async () => {
    occupe(true);
    const d = await appeler('verifier', bloc.value);
    occupe(false);
    afficher(statut, d, `✓ ${d.id || 'Hypothèse'} : bloc valide.`);
  });
  btnAjouter.addEventListener('click', async () => {
    occupe(true);
    const d = await appeler('ajouter', bloc.value);
    afficher(statut, d, d.message ? `✓ ${d.message}` : '');
    if (d.ok) {
      // Le candidat passe « en hypothèse » ; la suite se fait dans l'onglet Et si ? (mode Simuler).
      await _veilleChangerStatut(c, 'en_hypothese', { hypothese_id: d.id, hypothese_type: type });
    } else {
      occupe(false);
    }
  });
}

'''

JS_EDITS = [
 ("const VEILLE_STATUTS_LABEL = { a_trier: 'à trier', ecarte: 'écarté', en_queue: 'en queue' };",
  "const VEILLE_STATUTS_LABEL = { a_trier: 'à trier', ecarte: 'écarté', en_queue: 'en queue', en_hypothese: 'en hypothèse' };"),
 ("remplir('veille-statut', ['a_trier', 'en_queue', 'ecarte'], 'Tous', v => VEILLE_STATUTS_LABEL[v]);",
  "remplir('veille-statut', ['a_trier', 'en_hypothese', 'en_queue', 'ecarte'], 'Tous', v => VEILLE_STATUTS_LABEL[v]);"),
 ("  if (c.statut === 'en_queue') {\n    const queue = VEILLE_QUEUES[c.queue_type] || 'la queue';",
  "  if (c.statut === 'en_hypothese') {   // U3a\n"
  "    actions.innerHTML = `<label>Action</label>✓ Envoyé vers « et si ? » (${_veilleEsc(c.hypothese_type || '')} : ${_veilleEsc(c.hypothese_id)}).\n"
  "      <div class=\"option-desc\">Suite : onglet « Et si ? », mode Simuler → Décider → Injecter.</div>\n"
  "      <button id=\"veille-btn-retrier\" class=\"yaml-btn\" style=\"margin-top:6px\">↶ Remettre à trier</button>\n"
  "      <div class=\"option-desc\" id=\"veille-action-etat\"></div>`;\n"
  "    document.getElementById('veille-btn-retrier').addEventListener('click', async () => {\n"
  "      const ok = confirm(`Remettre « ${c.titre} » à trier ?\\n\\nL'hypothèse « ${c.hypothese_id} » n'est PAS retirée de hypotheses.yaml : "
  "supprime-la dans l'onglet « Et si ? » si tu n'en veux plus.`);\n"
  "      if (ok) await _veilleChangerStatut(c, 'a_trier');\n"
  "    });\n"
  "    return;\n"
  "  }\n"
  "  if (c.statut === 'en_queue') {\n    const queue = VEILLE_QUEUES[c.queue_type] || 'la queue';"),
 ('title="Un appel IA réel (idees_vers_queue.py)">✨ Préparer l\'entrée de queue</button>',
  'title="Un appel IA réel (hypothese_depuis_texte.py) : le candidat devient une hypothèse « et si ? »">✨ Envoyer vers « et si ? »</button>'),
 ("document.getElementById('veille-btn-preparer').addEventListener('click', () => _veillePreparer(c));",
  "document.getElementById('veille-btn-preparer').addEventListener('click', () => _veilleVersEtSi(c));"),
 ("async function _veillePreparer(c) {", NOUVELLE_FONCTION + "async function _veillePreparer(c) {"),
]

PY_EDITS = [
 ('STATUTS = ("a_trier", "ecarte", "en_queue")', 'STATUTS = ("a_trier", "ecarte", "en_queue", "en_hypothese")'),
 ('        if statut == "en_queue":\n            cible["queue_id"] = body.get("queue_id")\n            cible["queue_type"] = body.get("queue_type")\n        else:\n            cible.pop("queue_id", None)\n            cible.pop("queue_type", None)\n',
  '        if statut == "en_queue":\n            cible["queue_id"] = body.get("queue_id")\n            cible["queue_type"] = body.get("queue_type")\n        else:\n            cible.pop("queue_id", None)\n            cible.pop("queue_type", None)\n'
  '        if statut == "en_hypothese":   # U3a : hypothèse « et si ? » créée depuis ce candidat\n'
  '            cible["hypothese_id"] = body.get("hypothese_id")\n            cible["hypothese_type"] = body.get("hypothese_type")\n'
  '        else:\n            cible.pop("hypothese_id", None)\n            cible.pop("hypothese_type", None)\n'),
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

def node_ok(chemin):
    try:
        return subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True).returncode == 0
    except FileNotFoundError:
        return None

js_txt, ok1 = appliquer(JS.read_text(encoding="utf-8"), JS_EDITS, "app.js")
py_txt, ok2 = appliquer(PY.read_text(encoding="utf-8"), PY_EDITS, "routes_veille_signaux.py")
if not (ok1 and ok2):
    print("✗ rien écrit"); sys.exit(1)
if not APPLY:
    print("✓ dry-run : 6 modifications dans app.js, 2 dans routes_veille_signaux.py"); sys.exit(0)

shutil.copy2(JS, JS.with_name(JS.name + ".bak_u3a")); shutil.copy2(PY, PY.with_name(PY.name + ".bak_u3a"))
JS.write_text(js_txt, encoding="utf-8"); PY.write_text(py_txt, encoding="utf-8")
py_compile.compile(str(PY), doraise=True)
avant = node_ok(JS.with_name(JS.name + ".bak_u3a")); apres = node_ok(JS)
if avant is True and apres is False:
    shutil.copy2(JS.with_name(JS.name + ".bak_u3a"), JS); shutil.copy2(PY.with_name(PY.name + ".bak_u3a"), PY)
    print("✗ erreur de syntaxe JavaScript introduite : fichiers restaurés"); sys.exit(1)
print("✓ appliqué" + ("" if apres else " (contrôle node non concluant : node absent ou déjà en erreur avant le patch)"))
