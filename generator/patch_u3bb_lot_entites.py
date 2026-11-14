#!/usr/bin/env python3
"""
patch_u3bb_lot_entites.py — Ourrassol 2098 (14 novembre 2026)

Niveau 2 : adopter puis injecter PLUSIEURS entités d'un coup. Dans le panneau Parcours
(mode « Simuler »), un bloc repliable « 📦 Traiter plusieurs entités d'un coup » :
liste des hypothèses d'entité à traiter (statut « vérifié » ou « adopté, en attente
d'injection »), cases à cocher, bouton « Adopter et injecter la sélection ».
Les entités passent l'une après l'autre : adoption, puis injection RÉELLE (mêmes
routes et mêmes contrôles que les boutons du Parcours : doublons, année d'origine,
relance de la localisation si U3ba est appliqué). Une entité qui échoue est signalée
avec son motif ; les suivantes continuent. « Arrêter après l'entité en cours » est
disponible. Compter environ 6 à 8 minutes par entité ; garder l'onglet ouvert.
Événements et signaux : non concernés (ils exigent une simulation avant l'adoption).

  generator/et_si_lot.py (NOUVEAU) : liste les entités et leur statut (lecture seule) ;
  gui/app.py : route POST /api/et_si/lot/lister ;
  gui/static/app.js : bloc dans le panneau Parcours.

Prérequis : U3al. Après application : redémarrer Flask ; Cmd+Maj+R.

    python3 generator/patch_u3bb_lot_entites.py            # aperçu
    python3 generator/patch_u3bb_lot_entites.py --apply
Sauvegardes .bak_u3bb ; refuse un second passage ; contrôles de syntaxe avec restauration.
"""
import argparse
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3bb"
SCRIPT = Path("generator/et_si_lot.py")
APP_PY = Path("gui/app.py")
APP_JS = Path("gui/static/app.js")
DOSSIERS = Path("generator/et_si_dossiers.py")

SCRIPT_CONTENU = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\net_si_lot.py (U3bb) — liste, pour le GUI, les hypothèses d\'ENTITÉ avec leur statut,\nafin de les adopter puis de les injecter en lot. Lecture seule : n\'écrit rien.\n\n  python3 generator/et_si_lot.py --lister --json\nSortie : {"ok": true, "entites": [{"id","nom","categorie","scenario_ref","annee_debut","statut"}]}\n(statut : vérifié · rejeté · adopté, en attente d\'injection · injecté)\n"""\nimport argparse\nimport json\nimport sys\nfrom pathlib import Path\n\nimport yaml\n\nGEN = Path(__file__).resolve().parent\nsys.path.insert(0, str(GEN))\nimport et_si_dossiers as ed  # noqa: E402\n\n\ndef lister():\n    try:\n        data = yaml.safe_load(ed.HYPOTHESES_PATH.read_text(encoding="utf-8")) or {}\n    except (OSError, yaml.YAMLError) as e:\n        return {"ok": False, "error": f"hypotheses.yaml illisible : {e}"}\n    dossiers = ed.charger()\n    sortie = []\n    for h in data.get("hypotheses") or []:\n        if not isinstance(h, dict) or str(h.get("type") or "").strip().lower() != "entite":\n            continue\n        hid = str(h.get("id"))\n        sortie.append({"id": hid, "nom": " ".join(str(h.get("nom") or hid).split()),\n                       "categorie": h.get("categorie"), "scenario_ref": h.get("scenario_ref"),\n                       "annee_debut": h.get("annee_debut"),\n                       "statut": ed.statut(hid, dossiers.get(hid) or {})})\n    return {"ok": True, "entites": sortie}\n\n\ndef main():\n    ap = argparse.ArgumentParser(description=__doc__.split("\\n")[1])\n    ap.add_argument("--lister", action="store_true")\n    ap.add_argument("--json", action="store_true")\n    a = ap.parse_args()\n    res = lister() if a.lister else {"ok": False, "error": "action attendue : --lister"}\n    if a.json:\n        print(json.dumps(res, ensure_ascii=False, default=str))\n    elif res.get("ok"):\n        for e in res["entites"]:\n            print(f"{e[\'id\']:45s} {e[\'statut\']:34s} {e.get(\'annee_debut\') or \'-\'}  {e[\'nom\']}")\n    else:\n        print("✗", res.get("error"))\n    return 0 if res.get("ok") else 1\n\n\nif __name__ == "__main__":\n    sys.exit(main())\n'

PY_REMPL = [(
    "route /api/et_si/lot/lister",
    '@app.route("/api/et_si/statut", methods=["POST"])\n',
    r"""@app.route("/api/et_si/lot/lister", methods=["POST"])
def et_si_lot_lister():   # U3bb : entités et statuts pour le traitement en lot (lecture seule)
    pipeline_dir = Path(load_config().get("pipeline_dir", ""))
    try:
        r = subprocess.run([sys.executable, "et_si_lot.py", "--lister", "--json"], cwd=pipeline_dir,
                           capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Délai dépassé (60 s)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"et_si_lot.py introuvable dans {pipeline_dir}"}), 500
    try:
        payload = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return jsonify({"error": (r.stderr or r.stdout or "réponse illisible").strip()[-500:]}), 500
    if not payload.get("ok"):
        return jsonify({"error": payload.get("error", "erreur inconnue")}), 500
    return jsonify(payload)


@app.route("/api/et_si/statut", methods=["POST"])
""",
)]

JS_REMPL = [(
    "bloc de traitement en lot",
    "  const ligneStatut = mk('div');\n",
    r"""  // U3bb : traiter plusieurs entités d'un coup (adopter puis injecter, l'une après l'autre)
  const lotEl = document.createElement('details');
  lotEl.style.cssText = 'border:1px solid #9aa5b1;border-radius:6px;padding:6px 8px;margin:0 0 10px;';
  const lotTitre = document.createElement('summary');
  lotTitre.textContent = '📦 Traiter plusieurs entités d\'un coup (adopter + injecter)';
  lotTitre.style.cursor = 'pointer';
  lotEl.appendChild(lotTitre);
  lotEl.appendChild(mk('div', 'option-desc',
    'Coche les entités à traiter. Pour chacune : adoption, puis injection RÉELLE dans le vault (appels IA, ' +
    'environ 6 à 8 minutes par entité). Elles passent l\'une après l\'autre ; garde cet onglet ouvert. ' +
    'Une entité qui échoue est signalée et les suivantes continuent.'));
  const lotListe = mk('div');
  lotListe.style.margin = '6px 0';
  lotEl.appendChild(lotListe);
  const lotBtns = mk('div');
  const btnLotMaj = bouton('↻ Actualiser la liste');
  const btnLotTout = bouton('Tout cocher');
  const btnLotGo = bouton('Adopter et injecter la sélection', 'yaml-btn yaml-btn-save');
  const btnLotStop = bouton('Arrêter après l\'entité en cours');
  btnLotStop.disabled = true;
  [btnLotMaj, btnLotTout, btnLotGo, btnLotStop].forEach(b => lotBtns.appendChild(b));
  lotEl.appendChild(lotBtns);
  const lotEtat = mk('div', 'option-desc');
  lotEtat.style.whiteSpace = 'pre-wrap';
  lotEl.appendChild(lotEtat);
  corps.appendChild(lotEl);

  let lotLignes = [];
  let lotArret = false;
  let lotEnCours = false;
  const lotPost = async (url, body) => {
    try {
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                     body: JSON.stringify(body) });
      return await res.json();
    } catch (e) {
      return { ok: false, error: `Erreur réseau : ${e.message}` };
    }
  };
  const lotCharger = async () => {
    lotEtat.style.color = '';
    const data = await lotPost('/api/et_si/lot/lister', {});
    lotListe.textContent = '';
    lotLignes = [];
    if (data.error) { lotEtat.style.color = '#b03a2e'; lotEtat.textContent = `✗ ${data.error}`; return; }
    const aTraiter = (data.entites || []).filter(e => e.statut === 'vérifié' || e.statut === 'adopté, en attente d\'injection');
    const autres = (data.entites || []).length - aTraiter.length;
    aTraiter.forEach(e => {
      const ligne = mk('div');
      ligne.style.margin = '3px 0';
      const c = document.createElement('input');
      c.type = 'checkbox';
      c.style.marginRight = '6px';
      const lib = mk('span', null, `${e.nom} — ${e.categorie || '?'}` +
        (e.annee_debut ? ` — née en ${e.annee_debut}` : ' — sans année') + ` (${e.statut})`);
      const etat = mk('div', 'option-desc');
      etat.style.whiteSpace = 'pre-wrap';
      etat.style.marginLeft = '24px';
      ligne.appendChild(c);
      ligne.appendChild(lib);
      ligne.appendChild(etat);
      lotListe.appendChild(ligne);
      lotLignes.push({ e, case: c, etat, fait: false });
    });
    lotEtat.textContent = aTraiter.length
      ? `${aTraiter.length} entité(s) à traiter` + (autres ? ` (${autres} autre(s) déjà injectée(s) ou rejetée(s), non listée(s))` : '') + '.'
      : 'Aucune entité à traiter (ajoute-en avec « Nouvelle hypothèse »).';
  };
  lotEl.addEventListener('toggle', () => { if (lotEl.open && !lotLignes.length && !lotEnCours) lotCharger(); });
  btnLotMaj.addEventListener('click', () => { if (!lotEnCours) lotCharger(); });
  btnLotTout.addEventListener('click', () => { lotLignes.forEach(l => { if (!l.fait) l.case.checked = true; }); });
  btnLotStop.addEventListener('click', () => {
    lotArret = true;
    lotEtat.textContent = 'Arrêt demandé : l\'entité en cours se termine, les suivantes ne sont pas traitées.';
  });
  btnLotGo.addEventListener('click', async () => {
    if (lotEnCours) return;
    const choix = lotLignes.filter(l => l.case.checked && !l.fait);
    if (!choix.length) { lotEtat.style.color = '#b03a2e'; lotEtat.textContent = '✗ Coche d\'abord au moins une entité.'; return; }
    lotEnCours = true;
    lotArret = false;
    [btnLotMaj, btnLotTout, btnLotGo].forEach(b => { b.disabled = true; });
    btnLotStop.disabled = false;
    lotEtat.style.color = '';
    let ok = 0, aVoir = 0, traitees = 0;
    for (const l of choix) {
      if (lotArret) break;
      traitees++;
      l.etat.style.color = '';
      lotEtat.textContent = `⏳ Entité ${traitees} sur ${choix.length} : ${l.e.nom}`;
      if (l.e.statut === 'vérifié') {
        l.etat.textContent = '⏳ adoption…';
        const a = await lotPost('/api/et_si/decider/adopter', { id: l.e.id });
        if (!a.ok) {
          aVoir++;
          l.etat.style.color = '#b9770e';
          l.etat.textContent = `✗ adoption refusée : ${(a.sortie || a.error || '').split('\n').filter(x => x.trim()).slice(-3).join('\n')}`;
          continue;
        }
        l.e.statut = 'adopté, en attente d\'injection';
      }
      const t0 = Date.now();
      const minuteur = setInterval(() => {
        l.etat.textContent = `⏳ injection en cours, ${Math.round((Date.now() - t0) / 1000)} s (plusieurs minutes)`;
      }, 5000);
      l.etat.textContent = '⏳ injection en cours…';
      const r = await lotPost('/api/et_si/injecter/injecter', { id: l.e.id });
      clearInterval(minuteur);
      const sortie = r.sortie || r.error || '';
      const lignes = sortie.split('\n').filter(x => x.trim());
      const avert = lignes.filter(x => x.trim().startsWith('⚠'));
      if (r.ok && /statut : injecté/.test(sortie)) {
        l.fait = true;
        l.case.checked = false;
        l.case.disabled = true;
        ok++;
        if (avert.length) {
          aVoir++;
          l.etat.style.color = '#b9770e';
          l.etat.textContent = `✓ injectée, mais à voir :\n${avert.join('\n')}`;
        } else {
          l.etat.style.color = '#1e8449';
          l.etat.textContent = '✓ injectée';
        }
      } else {
        aVoir++;
        l.etat.style.color = '#b9770e';
        l.etat.textContent = `✗ non injectée (la décision reste « adopté ») :\n${lignes.slice(-4).join('\n')}`;
      }
    }
    lotEnCours = false;
    [btnLotMaj, btnLotTout, btnLotGo].forEach(b => { b.disabled = false; });
    btnLotStop.disabled = true;
    lotEtat.style.color = aVoir ? '#b9770e' : '#1e8449';
    lotEtat.textContent = `Terminé : ${ok} entité(s) injectée(s), ${aVoir} à voir avec toi` +
      (lotArret ? ' (arrêt demandé : les entités restantes n\'ont pas été traitées)' : '') + '.';
    const selH = listeHyp();
    if (selH) await rafraichirChampDynamique(selH);
  });

  const ligneStatut = mk('div');
""",
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
    ap.add_argument("--dossiers", default=str(DOSSIERS))
    a = ap.parse_args()
    cible = Path(a.script)
    if cible.exists():
        print(f"✗ {cible} existe déjà — refus d'un second passage.")
        return 1
    for p in (Path(a.py), Path(a.js), Path(a.dossiers), cible.parent):
        if not p.exists():
            print(f"✗ Introuvable : {p} (lancer depuis la racine du vault)")
            return 2
    if "U3al" not in Path(a.dossiers).read_text(encoding="utf-8"):
        print("✗ Prérequis U3al absent de et_si_dossiers.py.")
        return 1
    py, js = Path(a.py), Path(a.js)
    prepares = []
    for chemin, remp in ((py, PY_REMPL), (js, JS_REMPL)):
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
        prepares.append((chemin, texte, nouveau))
    print(f"  ✓ {cible.name} : nouveau script ({len(SCRIPT_CONTENU.splitlines())} lignes)")
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, _, apres in prepares:
        bak = chemin.with_name(chemin.name + ".bak_u3bb")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(apres, encoding="utf-8")
    cible.write_text(SCRIPT_CONTENU, encoding="utf-8")

    def restaurer():
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)
        if cible.exists():
            cible.unlink()

    try:
        for chemin in (baks[0][0], cible):
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
    print(f"✓ Créé : {cible}\n\nÀ faire : redémarrer Flask ; Cmd+Maj+R dans le navigateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
