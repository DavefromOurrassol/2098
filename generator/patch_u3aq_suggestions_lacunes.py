#!/usr/bin/env python3
"""
patch_u3aq_suggestions_lacunes.py — Ourrassol 2098 (14 novembre 2026)

Modes Auto -> suggestions d'hypothèses. Dans « ✨ Nouvelle hypothèse », un bloc
« 💡 Suggestions à partir des lacunes du vault » : choisir Événements ou
Entités, « Chercher » (UN appel IA), puis « Utiliser cette idée » copie le texte
dans la zone d'idée (type déjà choisi) ; le circuit habituel continue :
✨ Proposer -> Vérifier -> Ajouter. RIEN n'est écrit par la recherche : ni file
d'attente, ni vault, ni hypotheses.yaml. Les anciens modes Auto restent dans
« Outils directs (ancien, avancé) », inchangés.

  generator/suggerer_lacunes.py (NOUVEAU) : réutilise l'analyse de couverture et
      les consignes des modes Auto (zones vides, variables rares, bandes
      proche/moyen/lointain, concentration par année) ; écarte les entités déjà
      existantes (contrôle de doublons U3ak) ;
  gui/app.py : route POST /api/et_si/suggerer ;
  gui/static/app.js : bloc de suggestions dans le panneau.

Après application : redémarrer Flask ; Cmd+Maj+R dans le navigateur.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3aq_suggestions_lacunes.py            # aperçu
    python3 generator/patch_u3aq_suggestions_lacunes.py --apply    # écrit
Sauvegardes .bak_u3aq ; refuse un second passage ; contrôles de syntaxe avec restauration.
"""
import argparse
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3aq"
SCRIPT = Path("generator/suggerer_lacunes.py")
APP_PY = Path("gui/app.py")
APP_JS = Path("gui/static/app.js")

SCRIPT_CONTENU = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\nsuggerer_lacunes.py (U3aq) — propose des IDÉES d\'événements ou d\'entités à\npartir des lacunes du vault. N\'ÉCRIT RIEN : ni file d\'attente, ni vault, ni\nhypotheses.yaml. Chaque idée est un texte libre à coller dans « Nouvelle\nhypothèse » (qui fait ensuite ✨ Proposer → Vérifier → Ajouter).\n\n  python3 suggerer_lacunes.py --type evenement|entite [--n 5] [--scenario S] --json\n\nSortie (--json) : dernière ligne = {"ok": true, "type": ..., "suggestions":\n[{"titre","texte","raison","avertissements"}]} ou {"ok": false, "error": ...}.\nUn seul appel IA. Réutilise l\'analyse de couverture et les consignes des\nanciens modes Auto (bandes proche/moyen/lointain, concentration par année).\n"""\nimport argparse\nimport contextlib\nimport io\nimport json\nimport sys\n\n\ndef _evenements(n, scenario):\n    import inject_custom_events as ie\n    cov = ie.analyze_vault_coverage()\n    if scenario and scenario not in ie.SCENARIOS:\n        raise ValueError(f"scénario inconnu : {scenario!r}")\n    idees = ie.step_auto_generate_ideas(None, n, cov, scenario or None, None)\n    sortie = []\n    for i in (idees or [])[:n]:\n        if not isinstance(i, dict) or not str(i.get("description") or "").strip():\n            continue\n        morceaux = [str(i["description"]).strip()]\n        precis = []\n        if i.get("date_approximative"):\n            precis.append(f"vers {i[\'date_approximative\']}")\n        if i.get("portee"):\n            precis.append(f"portée {i[\'portee\']}")\n        if i.get("intensite"):\n            precis.append(f"intensité {i[\'intensite\']}")\n        if precis:\n            morceaux.append(" ; ".join(precis).capitalize() + ".")\n        if isinstance(i.get("scenarios"), list) and i["scenarios"]:\n            morceaux.append("Scénarios : " + ", ".join(map(str, i["scenarios"])) + ".")\n        sortie.append({"titre": str(i.get("id") or "événement"),\n                       "texte": " ".join(morceaux),\n                       "raison": str(i.get("rationale") or "").strip(),\n                       "avertissements": []})\n    return sortie\n\n\ndef _entites(n, scenario):\n    import create_entities_and_instances as ce\n    if scenario and scenario not in ce.SCENARIOS:\n        raise ValueError(f"scénario inconnu : {scenario!r}")\n    cov = ce.analyze_entity_coverage()\n    idees = ce.step_auto_suggest_entities(None, n, cov, [scenario] if scenario else None)\n    try:\n        import hypothese_depuis_texte as hdt\n        existantes = hdt.entites_existantes()\n    except Exception:\n        hdt, existantes = None, None\n    sortie = []\n    for i in (idees or [])[:n]:\n        nom = str((i or {}).get("nom") or "").strip()\n        if not nom:\n            continue\n        avert = []\n        if hdt is not None:\n            err, av = hdt.controle_doublon_entite(nom, existantes)\n            avert = [f"doublon probable : {e}" for e in err] + list(av)\n            if err:      # une entité qui existe déjà n\'est pas une lacune\n                continue\n        texte = f"Entité « {nom} » ({i.get(\'category\') or \'autre\'}). {str(i.get(\'role\') or \'\').strip()}"\n        if i.get("scenario_ref"):\n            texte += f" Scénario de référence : {i[\'scenario_ref\']}."\n        if i.get("etat"):\n            texte += f" État : {i[\'etat\']}."\n        sortie.append({"titre": nom, "texte": texte.strip(),\n                       "raison": str(i.get("rationale") or "").strip(),\n                       "avertissements": avert})\n    return sortie\n\n\ndef main():\n    ap = argparse.ArgumentParser(description=__doc__.split("\\n\\n")[0])\n    ap.add_argument("--type", required=True, choices=["evenement", "entite"])\n    ap.add_argument("--n", type=int, default=5)\n    ap.add_argument("--scenario", default="")\n    ap.add_argument("--json", action="store_true")\n    a = ap.parse_args()\n    n = max(1, min(a.n, 8))\n    tampon = io.StringIO()\n    try:\n        # les modules historiques impriment des messages de progression :\n        # on les détourne pour que la dernière ligne de stdout reste le JSON\n        with contextlib.redirect_stdout(tampon):\n            sugg = (_evenements if a.type == "evenement" else _entites)(n, a.scenario.strip())\n        res = {"ok": True, "type": a.type, "suggestions": sugg}\n        if not sugg:\n            res = {"ok": False, "error": "aucune suggestion exploitable (réponse IA vide)"}\n    except Exception as e:      # noqa: BLE001\n        res = {"ok": False, "error": f"{type(e).__name__} : {e}"}\n    if a.json:\n        print(json.dumps(res, ensure_ascii=False))\n    elif res["ok"]:\n        for s in res["suggestions"]:\n            print(f"- {s[\'titre\']}\\n  {s[\'texte\']}\\n  → {s[\'raison\']}")\n    else:\n        print("✗", res["error"])\n    return 0 if res["ok"] else 1\n\n\nif __name__ == "__main__":\n    sys.exit(main())\n'

PY_REMPL = [(
    "route /api/et_si/suggerer",
    'TIMEOUT_ET_SI = {"proposer": 180, "verifier": 60, "ajouter": 60}\n',
    '''TIMEOUT_ET_SI = {"proposer": 180, "verifier": 60, "ajouter": 60}


@app.route("/api/et_si/suggerer", methods=["POST"])
def et_si_suggerer():   # U3aq : idées à partir des lacunes du vault (un appel IA, n'écrit rien)
    data = request.get_json() or {}
    type_ = data.get("type")
    if type_ not in ("evenement", "entite"):
        return jsonify({"error": "type attendu : evenement ou entite"}), 400
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    cmd = [sys.executable, "suggerer_lacunes.py", "--type", type_, "--n", "5", "--json"]
    try:
        resultat = subprocess.run(cmd, cwd=pipeline_dir, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Délai dépassé (240 s)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"suggerer_lacunes.py introuvable dans {pipeline_dir}"}), 500
    sortie = resultat.stdout.strip()
    try:
        payload = json.loads(sortie.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return jsonify({"error": f"Sortie inattendue (code {resultat.returncode}) : "
                                  f"{(resultat.stderr or sortie)[-500:]}"}), 500
    if not payload.get("ok"):
        return jsonify({"error": payload.get("error", "erreur inconnue")}), 500
    return jsonify(payload)
''',
)]

JS_REMPL = [(
    "bloc de suggestions",
    "  corps.appendChild(ligneProposer);\n",
    r'''  corps.appendChild(ligneProposer);

  // U3aq : suggestions à partir des lacunes du vault (un appel IA, n'écrit rien)
  const blocSugg = mk('div');
  blocSugg.style.cssText = 'border:1px dashed #9aa5b1;border-radius:6px;padding:8px;margin:0 0 10px;';
  blocSugg.appendChild(mk('div', 'option-label', '💡 Pas d\'idée ? Suggestions à partir des lacunes du vault'));
  const ligneSugg = document.createElement('div');
  ligneSugg.style.cssText = 'display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:6px 0;';
  const selSugg = document.createElement('select');
  selSugg.style.setProperty('width', 'auto', 'important');
  [['evenement', 'Événements'], ['entite', 'Entités']].forEach(([v, t]) => {
    const o = document.createElement('option'); o.value = v; o.textContent = t; selSugg.appendChild(o);
  });
  const btnSugg = mk('button', 'yaml-btn', 'Chercher des lacunes');
  btnSugg.type = 'button';
  ligneSugg.appendChild(selSugg);
  ligneSugg.appendChild(btnSugg);
  blocSugg.appendChild(ligneSugg);
  const etatSugg = mk('div', 'option-desc');
  etatSugg.style.whiteSpace = 'pre-wrap';
  etatSugg.textContent = 'Analyse le vault (zones vides, variables rares, dates sur-représentées) et propose 5 idées. ' +
    'Un appel IA ; rien n\'est écrit.';
  blocSugg.appendChild(etatSugg);
  const listeSugg = mk('div');
  blocSugg.appendChild(listeSugg);
  corps.appendChild(blocSugg);

  btnSugg.addEventListener('click', async () => {
    const type = selSugg.value;
    btnSugg.disabled = true;
    listeSugg.textContent = '';
    etatSugg.style.color = '';
    etatSugg.textContent = '💡 Analyse en cours… (un appel IA, jusqu\'à une minute)';
    let data;
    try {
      const res = await fetch('/api/et_si/suggerer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type }),
      });
      data = await res.json();
    } catch (e) {
      data = { error: `Erreur réseau : ${e.message}` };
    }
    btnSugg.disabled = false;
    if (data.error) { etatSugg.style.color = '#b03a2e'; etatSugg.textContent = `✗ ${data.error}`; return; }
    etatSugg.textContent = `${(data.suggestions || []).length} idée(s). « Utiliser cette idée » la copie dans la zone d'idée ci-dessous ; rien n'est ajouté tant que tu n'as pas fait Proposer, Vérifier puis Ajouter.`;
    (data.suggestions || []).forEach(s => {
      const carte = mk('div');
      carte.style.cssText = 'border:1px solid #d5dbe1;border-radius:6px;padding:6px 8px;margin:6px 0;';
      const t = mk('div', 'option-label', s.titre);
      const d = mk('div', 'option-desc', s.texte);
      carte.appendChild(t);
      carte.appendChild(d);
      if (s.raison) { const r = mk('div', 'option-desc', `→ ${s.raison}`); r.style.fontStyle = 'italic'; carte.appendChild(r); }
      (s.avertissements || []).forEach(a => { const w = mk('div', 'option-desc', `⚠ ${a}`); w.style.color = '#b9770e'; carte.appendChild(w); });
      const b = mk('button', 'yaml-btn', 'Utiliser cette idée');
      b.type = 'button';
      b.addEventListener('click', () => {
        if (idee.value.trim() && idee.value.trim() !== s.texte && !confirm('Remplacer l\'idée actuelle ?')) return;
        idee.value = s.texte;
        selType.value = (data.type === 'entite') ? 'entite' : '';
        idee.scrollIntoView({ behavior: 'smooth', block: 'center' });
        idee.focus();
      });
      carte.appendChild(b);
      listeSugg.appendChild(carte);
    });
  });
''',
)]


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
    ap.add_argument("--script", default=str(SCRIPT))
    ap.add_argument("--py", default=str(APP_PY))
    ap.add_argument("--js", default=str(APP_JS))
    a = ap.parse_args()
    cible_script = Path(a.script)
    if cible_script.exists():
        print(f"✗ {cible_script} existe déjà — refus d'un second passage.")
        return 1
    if not cible_script.parent.exists():
        print(f"✗ Dossier introuvable : {cible_script.parent} (lancer depuis la racine du vault)")
        return 2
    prepares = []
    for chemin, remp in ((Path(a.py), PY_REMPL), (Path(a.js), JS_REMPL)):
        if not chemin.exists():
            print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
            return 2
        texte = chemin.read_text(encoding="utf-8")
        if MARQUEUR in texte:
            print(f"✗ {MARQUEUR} déjà appliqué dans {chemin.name} — refus d'un second passage.")
            return 1
        nouveau = texte
        for libelle, ancre, rempl in remp:
            n = nouveau.count(ancre)
            if n != 1:
                print(f"✗ {chemin.name} : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
                return 1
            nouveau = nouveau.replace(ancre, rempl, 1)
            print(f"  ✓ {chemin.name} : {libelle}")
        if MARQUEUR not in nouveau:
            nouveau = nouveau.replace(remp[0][2], remp[0][2], 1)
        prepares.append((chemin, texte, nouveau))
    print(f"  ✓ {cible_script.name} : nouveau script ({len(SCRIPT_CONTENU.splitlines())} lignes)")
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, _, apres in prepares:
        bak = chemin.with_name(chemin.name + ".bak_u3aq")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(apres, encoding="utf-8")
    cible_script.write_text(SCRIPT_CONTENU, encoding="utf-8")

    def restaurer():
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)
        cible_script.unlink(missing_ok=True) if sys.version_info >= (3, 8) else None

    try:
        for chemin in (baks[0][0], cible_script):
            py_compile.compile(str(chemin), doraise=True)
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
    print(f"✓ Créé : {cible_script}")
    print("\nÀ faire : redémarrer Flask ; Cmd+Maj+R dans le navigateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
