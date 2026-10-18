#!/usr/bin/env python3
"""
patch_s27_gui_main.py -- étape ⑤ « À la main » outillée dans le panneau
« Parcours de l'hypothèse » (17 octobre 2026)
=========================================================================
  gui/app.py        routes /api/et_si/main/etat, /entites/<apercu|ajouter>,
                    /regle/<apercu|ajouter>, /lancer/<audit|resume>
                    (appellent generator/et_si_main.py ; aucun appel IA, sauf « résumé »).
  gui/static/app.js étape ⑤ : nouvelles entités (case + catégorie → file),
                    règle de lore (brouillon modifiable → lore_regles.yaml),
                    boutons « Relecture du lore » et « Résumé du scénario ».

Prérequis : generator/et_si_main.py en place ; patchs PATCH_S27_GUI_PARCOURS et
PATCH_S19_RETOUCHES appliqués. Tout ou rien, sauvegardes .bak_gui_main, refuse un
second passage. Usage, depuis la racine du coffre :
    python3 generator/patch_s27_gui_main.py            (aperçu)
    python3 generator/patch_s27_gui_main.py --apply
Puis redémarrer le GUI et recharger la page.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_GUI_MAIN"
VAULT = Path.cwd()
APP_PY = VAULT / "gui" / "app.py"
APP_JS = VAULT / "gui" / "static" / "app.js"
DEBUT_PANNEAU = "// PATCH_S27_GUI_PARCOURS — PANNEAU"
FIN_PANNEAU = "// PATCH_GUI_OBSIDIAN_PANNEAUX"

ROUTES_PY = r'''# ---------------------------------------------------------------------------
# PATCH_S27_GUI_MAIN (17 octobre 2026) -- étape ⑤ « À la main » du panneau
# « Parcours » : generator/et_si_main.py (entités vers la file, règle de lore,
# relecture du lore, résumé du scénario). Aucun appel IA, sauf « résumé ».
# ---------------------------------------------------------------------------

TIMEOUTS_MAIN = {"etat": 120, "entites": 120, "regle": 60, "lancer": 900}


@app.route("/api/et_si/main/<quoi>", methods=["POST"])
@app.route("/api/et_si/main/<quoi>/<action>", methods=["POST"])
def et_si_main_route(quoi, action=None):
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}
    hid = str(data.get("id") or "").strip()
    if not hid:
        return jsonify({"error": "choisis d'abord une hypothèse dans la liste"}), 400
    cmd = [sys.executable, "et_si_main.py", "--id", hid]
    entree = None
    sc = str(data.get("scenario") or "").strip()
    if quoi == "etat" and action is None:
        cmd.append("--json")
    elif quoi == "entites" and action in ("apercu", "ajouter"):
        choix = data.get("choix") if isinstance(data.get("choix"), list) else []
        cmd += ["--entites", json.dumps(choix, ensure_ascii=False)] + (["--apply"] if action == "ajouter" else [])
    elif quoi == "regle" and action in ("apercu", "ajouter") and re.match(r"^[a-z_]+$", sc):
        cmd += ["--regle", sc] + (["--apply"] if action == "ajouter" else [])
        entree = str(data.get("texte") or "")
    elif quoi == "lancer" and action in ("audit", "resume") and re.match(r"^[a-z_]+$", sc):
        cmd += ["--lancer", action, "--scenario", sc]
    else:
        return jsonify({"error": f"demande inconnue : {quoi}/{action}"}), 404
    delai = TIMEOUTS_MAIN[quoi]
    try:
        r = subprocess.run(cmd, cwd=pipeline_dir, capture_output=True, text=True, timeout=delai,
                           input=entree if entree is not None else "")
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Délai dépassé ({delai} s)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"et_si_main.py introuvable dans {pipeline_dir}"}), 500
    if quoi == "etat":
        try:
            return jsonify(json.loads(r.stdout.strip().splitlines()[-1]))
        except (ValueError, IndexError):
            return jsonify({"error": (r.stderr or r.stdout or "réponse illisible").strip()[-500:]}), 500
    sortie = "\n".join(s for s in (r.stdout.strip(), r.stderr.strip()) if s)
    return jsonify({"ok": r.returncode == 0, "sortie": sortie})


'''
ANCRE_PY = "TIMEOUT_IDEES_TEXTE_LIBRE = 180"

JS_ZONE = ('''  b5.appendChild(ligneMain);
''', '''  b5.appendChild(ligneMain);
  const zoneMain = mk('div');   // PATCH_S27_GUI_MAIN, rempli par chargerMain()
  b5.appendChild(zoneMain);
''')
JS_ACTUALISER = ('''      afficher(data);
''', '''      afficher(data);
      if (data.etape >= 5) chargerMain(); else viderMain();   // PATCH_S27_GUI_MAIN
''')
JS_BLOC = r'''  // PATCH_S27_GUI_MAIN : étape ⑤, partie mécanique (et_si_main.py) -- nouvelles
  // entités vers la file, règle de lore vers lore_regles.yaml, commandes de fin.
  // Les saisies (cases, catégories, brouillons) survivent aux actualisations.
  const nBase = tous.length;
  const memo = { garde: {}, cat: {}, texte: {} };
  function viderMain() {
    zoneMain.textContent = '';
    tous.splice(nBase);
  }
  function sousTitre(txt) {
    const t = mk('div', 'option-label', txt);
    t.style.marginTop = '10px';
    return t;
  }
  function rendreMain(etat) {
    viderMain();
    const id = etat.id;
    if ((etat.erreurs || []).length) {
      const e = mk('div', 'option-desc', etat.erreurs.map(x => `⚠ ${x}`).join('\n'));
      e.style.color = '#b03a2e';
      e.style.whiteSpace = 'pre-wrap';
      zoneMain.appendChild(e);
    }

    // 1. Nouvelles entités
    zoneMain.appendChild(sousTitre('Nouvelles entités proposées par la lecture IA'));
    const ents = etat.entites || [];
    if (!ents.length) zoneMain.appendChild(mk('div', 'option-desc', 'Aucune.'));
    ents.forEach(e => {
      const k = `${id}|${e.cle}`;
      const ligne = mk('div');
      ligne.style.margin = '4px 0';
      const libre = e.statut === 'proposée';
      const garde = mk('input');
      garde.type = 'checkbox';
      garde.disabled = !libre;
      garde.checked = libre && !!memo.garde[k];
      garde.addEventListener('change', () => { memo.garde[k] = garde.checked; });
      const cat = choix([['', '— catégorie —']].concat((etat.categories || []).map(c => [c, c])));
      cat.disabled = !libre;
      cat.value = memo.cat[k] || '';
      cat.addEventListener('change', () => {
        memo.cat[k] = cat.value;
        if (cat.value && !garde.checked) { garde.checked = true; memo.garde[k] = true; }
      });
      const nom = mk('span', 'option-label', ` ${e.nom} `);
      ligne.appendChild(garde);
      ligne.appendChild(nom);
      ligne.appendChild(cat);
      const etatTxt = mk('span', 'option-desc', libre ? '' : `✓ ${e.statut}${e.detail ? ' — ' + e.detail : ''}`);
      etatTxt.style.color = libre ? '' : '#1e8449';
      ligne.appendChild(etatTxt);
      const desc = mk('div', 'option-desc',
        `${e.role}${e.zone_nom ? ' — ancrage : ' + e.zone_nom : ''} (${e.sc})` + (e.raison ? `\nPourquoi : ${e.raison}` : ''));
      desc.style.whiteSpace = 'pre-wrap';
      desc.style.marginLeft = '22px';
      ligne.appendChild(desc);
      ligne.dataset.cle = e.cle;
      ligne._garde = garde;
      ligne._cat = cat;
      zoneMain.appendChild(ligne);
    });
    if (ents.some(e => e.statut === 'proposée')) {
      const l = mk('div');
      const bA = bouton('Aperçu (entités cochées)');
      const bE = bouton('Ajouter à la file', 'yaml-btn yaml-btn-save');
      const lire = () => [...zoneMain.querySelectorAll('div[data-cle]')]
        .filter(d => d._garde.checked).map(d => ({ cle: d.dataset.cle, category: d._cat.value }));
      bA.addEventListener('click', () => appeler('main/entites', 'apercu', { choix: lire() }));
      bE.addEventListener('click', () => {
        const c = lire();
        if (!c.length) { sortie.textContent = '✗ Coche au moins une entité.'; sortie.style.color = '#b03a2e'; return; }
        if (!confirm(`Ajouter ${c.length} entité(s) à entites_custom/queue.yaml ?`)) return;
        appeler('main/entites', 'ajouter', { choix: c });
      });
      l.appendChild(bA);
      l.appendChild(bE);
      zoneMain.appendChild(l);
      tous.push(bA, bE);
    }

    // 2. Règle de lore
    zoneMain.appendChild(sousTitre('Règle de lore (documentation/lore_regles.yaml)'));
    (etat.regles || []).forEach(r => {
      const k = `${id}|${r.sc}`;
      const bloc = mk('div');
      bloc.style.margin = '4px 0';
      const info = mk('div', 'option-desc', `Section ${r.sc}`
        + ((r.ajoutees || []).length ? ` — ✓ déjà ajoutée(s) : ${r.ajoutees.join(', ')}` : '')
        + ((r.deja || []).length && !(r.ajoutees || []).length ? ` — déjà présente(s) : ${r.deja.join(', ')}` : ''));
      bloc.appendChild(info);
      const ta = mk('textarea');
      ta.rows = 8;
      ta.style.width = '100%';
      ta.style.fontFamily = 'monospace';
      ta.style.fontSize = '0.85em';
      ta.value = (k in memo.texte) ? memo.texte[k]
        : (r.brouillon || '# Aucune entité disparue : écrire une règle si une contrainte doit être surveillée.\n');
      ta.addEventListener('input', () => { memo.texte[k] = ta.value; });
      bloc.appendChild(ta);
      const l = mk('div');
      const bA = bouton('Aperçu de la règle');
      const bE = bouton('Ajouter la règle', 'yaml-btn yaml-btn-save');
      bA.addEventListener('click', () => appeler('main/regle', 'apercu', { scenario: r.sc, texte: ta.value }));
      bE.addEventListener('click', () => {
        if (!confirm(`Ajouter cette règle à lore_regles.yaml (section ${r.sc}) ?`)) return;
        appeler('main/regle', 'ajouter', { scenario: r.sc, texte: ta.value });
      });
      l.appendChild(bA);
      l.appendChild(bE);
      bloc.appendChild(l);
      zoneMain.appendChild(bloc);
      tous.push(bA, bE);
    });

    // 3. Pour finir
    zoneMain.appendChild(sousTitre('Pour finir'));
    (etat.scenarios || []).forEach(sc => {
      const l = mk('div');
      (etat.fin || []).forEach(f => {
        const b = bouton(`${f.libelle} — ${sc}`);
        b.addEventListener('click', () => {
          if (f.action === 'resume' && !confirm(`Régénérer le résumé du scénario ${sc} ? (un appel IA payant)`)) return;
          appeler('main/lancer', f.action, { scenario: sc });
        });
        l.appendChild(b);
        tous.push(b);
      });
      zoneMain.appendChild(l);
    });
    const site = mk('div', 'option-desc',
      'Site, si des articles ont été corrigés : dans le terminal, python3 generator/chapos_revues.py puis '
      + 'bash generator/publier_site.sh (publication : laissée hors du GUI).');
    site.style.marginTop = '4px';
    zoneMain.appendChild(site);
    zoneMain.appendChild(aide(
      'Entités : coche celles à garder et choisis leur catégorie ; l\'aperçu montre les entrées, « Ajouter » les ' +
      'écrit dans entites_custom/queue.yaml (sauvegarde .bak_et_si_main, refus si l\'entité existe déjà ou est ' +
      'déjà dans la file). La création reste « Créer des entités » (appels IA, traite toute la file).\n' +
      'Règle : relis et modifie le brouillon (les lignes # sont ignorées) ; « Ajouter » l\'écrit à la fin de la ' +
      'section du scénario (format et identifiant vérifiés, sauvegarde .bak_et_si). Lance ensuite la relecture ' +
      'du lore pour voir ce qu\'elle signale.\n' +
      'Phrases, articles et décisions ⚠ restent à faire avec la check-list.'));
  }
  async function chargerMain() {
    const sel = listeHyp();
    const id = sel ? sel.value : '';
    if (!id) { viderMain(); return; }
    try {
      const res = await fetch('/api/et_si/main/etat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }),
      });
      const data = await res.json();
      if (data.error) { viderMain(); zoneMain.appendChild(mk('div', 'option-desc', `✗ ${data.error}`)); return; }
      rendreMain(data);
    } catch (err) {
      viderMain();
      zoneMain.appendChild(mk('div', 'option-desc', `✗ Erreur réseau : ${err.message}`));
    }
  }

'''
ANCRE_JS = "  const tri = () => ({ sauter: sauter.value, inclure: inclure.value });"


def controle_js(js):
    i = js.find(DEBUT_PANNEAU)
    j = js.find(FIN_PANNEAU, i)
    if i < 0 or j < 0:
        return "bornes du panneau introuvables"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js[i:j])
    try:
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True, timeout=30)
        return None if r.returncode == 0 else r.stderr.strip()
    except FileNotFoundError:
        print("  (node absent : contrôle JS sauté)")
        return None
    finally:
        Path(f.name).unlink()


def main():
    apply = "--apply" in sys.argv
    gen_main = VAULT / "generator" / "et_si_main.py"
    if not gen_main.exists():
        sys.exit("✗ generator/et_si_main.py absent : le placer d'abord. Rien fait.")
    for p in (APP_PY, APP_JS):
        if not p.exists():
            sys.exit(f"✗ {p.relative_to(VAULT)} introuvable (lancer depuis la racine du coffre). Rien fait.")
    py = APP_PY.read_text(encoding="utf-8")
    js = APP_JS.read_text(encoding="utf-8")
    if MARQUEUR in py or MARQUEUR in js:
        sys.exit("✗ patch déjà appliqué : rien fait.")
    erreurs = []
    if "PATCH_S27_GUI_PARCOURS" not in py or "PATCH_S19_RETOUCHES" not in js:
        erreurs.append("patchs PATCH_S27_GUI_PARCOURS / PATCH_S19_RETOUCHES absents")
    if "\nimport re" not in py and "import re," not in py and ", re\n" not in py:
        erreurs.append("app.py n'importe pas re")
    for nom, texte, ancre in (("app.py", py, ANCRE_PY), ("app.js", js, JS_ZONE[0]),
                              ("app.js", js, JS_ACTUALISER[0]), ("app.js", js, ANCRE_JS)):
        if texte.count(ancre) != 1:
            erreurs.append(f"{nom} : repère « {ancre.strip()[:50]} » trouvé {texte.count(ancre)} fois (attendu 1)")
    if erreurs:
        print("✗ Rien n'a été écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
        sys.exit(1)
    py = py.replace(ANCRE_PY, ROUTES_PY + ANCRE_PY)
    js = js.replace(JS_ZONE[0], JS_ZONE[1]).replace(JS_ACTUALISER[0], JS_ACTUALISER[1])
    js = js.replace(ANCRE_JS, JS_BLOC + ANCRE_JS)
    try:
        compile(py, str(APP_PY), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ app.py invalide après patch ({e}) : rien écrit.")
    err = controle_js(js)
    if err:
        sys.exit(f"✗ app.js invalide après patch : rien écrit.\n{err}")
    print("  ✓ gui/app.py : routes /api/et_si/main/… prêtes")
    print("  ✓ gui/static/app.js : étape ⑤ outillée prête")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    for p, t in ((APP_PY, py), (APP_JS, js)):
        shutil.copy2(p, p.with_name(p.name + ".bak_gui_main"))
        p.write_text(t, encoding="utf-8")
    print("\n✓ gui/app.py et gui/static/app.js modifiés (sauvegardes .bak_gui_main). "
          "Redémarrer le GUI et recharger la page.")


if __name__ == "__main__":
    main()
