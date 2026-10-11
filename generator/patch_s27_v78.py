#!/usr/bin/env python3
"""
patch_s27_v78.py — Ourrassol 2098 (S27, 10 octobre 2026)
=========================================================

Simulateur « et si ? » v7.7 -> v7.8 : GUI en deux modes.

  Mode « Simuler »          : l'hypothèse se choisit dans une LISTE DÉROULANTE
                              (nom, date, ⚠ si invalide), plus besoin de lister.
  Mode « Nouvelle hypothèse »: panneau ✨ : idée en texte libre -> Proposer (IA)
                              -> bloc YAML modifiable -> Vérifier -> Ajouter à
                              et_si/hypotheses.yaml (seul chemin d'écriture).

Fichiers modifiés (sauvegardes .bak_v78) :
  generator/simuler_et_si.py   --lister --json, --mode simuler|nouvelle
  gui/app.py                   /api/slugs?type=hypotheses_et_si,
                               /api/et_si/proposer|verifier|ajouter
  gui/static/app.js            panneau « Nouvelle hypothèse »
  gui/scripts_config.json      entrée simuler_et_si en deux modes
Fichier nouveau (à placer dans generator/ AVANT de lancer ce patch) :
  generator/hypothese_depuis_texte.py

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v78.py            # aperçu
    python3 generator/patch_s27_v78.py --apply    # écrit
Puis redémarrer Flask et recharger la page (Cmd-Maj-R : app.js a changé).
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"
ASSIST = VAULT_ROOT / "generator" / "hypothese_depuis_texte.py"
APP = VAULT_ROOT / "gui" / "app.py"
CONF = VAULT_ROOT / "gui" / "scripts_config.json"
JS_CANDIDATS = [VAULT_ROOT / "gui" / "static" / "app.js", VAULT_ROOT / "gui" / "static" / "js" / "app.js"]

# ------------------------------------------------------------ simuler_et_si.py
REMPLACEMENTS_SIMU = [
    ("version", 'VERSION = "v7.7"', 'VERSION = "v7.8"'),
    ("option --mode (onglets du GUI)",
     '''    ap.add_argument("--json", action="store_true", help="sortie JSON seule")
    args = ap.parse_args()
''',
     '''    ap.add_argument("--json", action="store_true", help="sortie JSON seule")
    ap.add_argument("--mode", choices=["simuler", "nouvelle"], default="simuler",
                    help="onglet du GUI (nouvelle = panneau d'écriture, rien à lancer)")
    args = ap.parse_args()
    if args.mode == "nouvelle":
        print("Mode « Nouvelle hypothèse » : écris l'idée dans le panneau ✨ ci-dessous, puis "
              "Proposer, Vérifier, Ajouter. Le bouton Lancer ne sert qu'en mode « Simuler ».")
        return
'''),
    ("--lister --json (liste déroulante du GUI)",
     '''    hyps = charger_hypotheses()
    if args.lister or not args.id:''',
     '''    hyps = charger_hypotheses()
    if (args.lister or not args.id) and args.json:
        # V7.8 : liste déroulante du GUI (/api/slugs?type=hypotheses_et_si).
        import dynamique as dyn
        from loader import VALID_VARS
        liste = []
        for h in hyps:
            _, err, _ = verifier_hypothese(dict(h), VALID_VARS, dyn)
            liste.append({"id": h.get("id"), "nom": h.get("nom") or h.get("id"),
                          "date": h.get("date"), "erreurs": err})
        print(json.dumps(liste, ensure_ascii=False, default=str))
        return
    if args.lister or not args.id:'''),
]

# --------------------------------------------------------------------- app.py
APP_SLUGS = '''        elif slug_type == "hypotheses_et_si":
            # Simulateur « et si ? » v7.8 (10 octobre 2026) : liste déroulante
            # des hypothèses de et_si/hypotheses.yaml (nom, date, ⚠ invalide),
            # via simuler_et_si.py --lister --json (aucun appel IA).
            resultat = subprocess.run(
                [sys.executable, "simuler_et_si.py", "--lister", "--json"], cwd=pipeline_dir,
                capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
            )
            try:
                hyps = json.loads(resultat.stdout.strip().splitlines()[-1])
            except (json.JSONDecodeError, IndexError):
                return jsonify({"slugs": [], "error": (resultat.stderr or resultat.stdout)[-500:]})
            for h in hyps:
                if not h.get("id"):
                    continue
                slugs.append(h["id"])
                labels[h["id"]] = (f"{h.get('nom')} ({h.get('date')})"
                                   + (" ⚠ invalide" if h.get("erreurs") else ""))
'''

APP_ROUTES = '''# ---------------------------------------------------------------------------
# Simulateur « et si ? » v7.8 (10 octobre 2026) -- assistant « Nouvelle
# hypothèse ». Trois actions de hypothese_depuis_texte.py, le texte (idée ou
# bloc YAML) passé sur l'entrée standard : proposer (UN appel IA, n'écrit
# rien), verifier (sans IA, n'écrit rien), ajouter (contrôle refait, seul
# chemin d'écriture vers et_si/hypotheses.yaml, sauvegarde .bak_ajout).
# ---------------------------------------------------------------------------

TIMEOUT_ET_SI = {"proposer": 180, "verifier": 60, "ajouter": 60}


@app.route("/api/et_si/<action>", methods=["POST"])
def et_si_assistant(action):
    if action not in TIMEOUT_ET_SI:
        return jsonify({"error": f"action inconnue : {action}"}), 404
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}
    texte = data.get("texte") or ""   # pas de strip() : l'indentation du bloc YAML compte
    if not texte.strip():
        return jsonify({"error": "texte vide"}), 400
    cmd = [sys.executable, "hypothese_depuis_texte.py", f"--{action}", "--json"]
    try:
        resultat = subprocess.run(cmd, cwd=pipeline_dir, capture_output=True, text=True,
                                  input=texte, timeout=TIMEOUT_ET_SI[action])
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Délai dépassé ({TIMEOUT_ET_SI[action]} s)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"hypothese_depuis_texte.py introuvable dans {pipeline_dir}"}), 500
    sortie = resultat.stdout.strip()
    try:
        payload = json.loads(sortie.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return jsonify({"error": f"Sortie inattendue (code {resultat.returncode}) : "
                                  f"{(resultat.stderr or sortie)[-500:]}"}), 500
    if payload.get("error"):
        return jsonify({"error": payload["error"]}), 500
    return jsonify(payload)


'''

REMPLACEMENTS_APP = [
    ("/api/slugs : type hypotheses_et_si",
     '''        elif slug_type == "signals":
            slugs = _scan_signal_slugs(vault_root)''',
     APP_SLUGS + '''        elif slug_type == "signals":
            slugs = _scan_signal_slugs(vault_root)'''),
    ("routes /api/et_si/proposer|verifier|ajouter",
     "TIMEOUT_IDEES_TEXTE_LIBRE = 180  # secondes -- un seul appel LLM",
     APP_ROUTES + "TIMEOUT_IDEES_TEXTE_LIBRE = 180  # secondes -- un seul appel LLM"),
]

# ---------------------------------------------------------------------- app.js
JS_APPEL = '''  // YAML panels
  await renderYamlPanels(script);

  // Assistant « Nouvelle hypothèse » (simulateur « et si ? » v7.8, 10 octobre
  // 2026) -- avant updateModeOnlyVisibility() ci-dessous, qui le masque en
  // mode « Simuler » (data-mode-only="nouvelle").
  if (script.assistant_hypothese) body.appendChild(buildAssistantHypothese());
'''

JS_FONCTIONS = r'''

// ══════════════════════════════════════════════════
// ASSISTANT « NOUVELLE HYPOTHÈSE » (simulateur « et si ? » v7.8, 10 octobre 2026)
// ══════════════════════════════════════════════════
// Panneau de l'entrée simuler_et_si (clé assistant_hypothese dans
// scripts_config.json), visible en mode « Nouvelle hypothèse ». Trois
// routes (app.py -> hypothese_depuis_texte.py) :
//   ✨ Proposer  /api/et_si/proposer  UN appel IA, bloc YAML modifiable ;
//   Vérifier     /api/et_si/verifier  sans IA, n'écrit rien ;
//   Ajouter      /api/et_si/ajouter   contrôle refait côté serveur, seul
//                                     chemin d'écriture (sauvegarde .bak_ajout).
function buildAssistantHypothese() {
  const wrapper = document.createElement('div');
  wrapper.className = 'yaml-panel';
  wrapper.dataset.modeOnly = 'nouvelle';

  const mk = (tag, cls, txt) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt) e.textContent = txt;
    return e;
  };

  const header = mk('div', 'yaml-panel-header');
  const titleRow = mk('div', 'yaml-panel-title-row');
  titleRow.appendChild(mk('span', 'yaml-panel-title', '✨ Nouvelle hypothèse'));
  header.appendChild(titleRow);
  wrapper.appendChild(header);

  const corps = mk('div', 'yaml-form-zone');
  corps.style.padding = '8px 0';
  corps.appendChild(mk('div', 'option-desc',
    'Écris l\'idée librement (date, chiffres, point d\'arrivée…), puis « ✨ Proposer » : l\'IA remplit ' +
    'l\'hypothèse complète (un appel IA). Corrige le bloc si besoin, « Vérifier », puis « Ajouter ». ' +
    'Rien n\'est écrit avant « Ajouter ». La nouvelle hypothèse apparaît ensuite dans la liste du mode « Simuler ».'));

  const idee = mk('textarea', 'yaml-form-textarea');
  idee.rows = 4;
  idee.placeholder = 'ex : à partir de 2040, des IA font le travail de 60 % des emplois salariés…';
  idee.autocomplete = 'off';
  idee.style.width = '100%';
  corps.appendChild(idee);

  const btnProposer = mk('button', 'yaml-btn yaml-btn-save', '✨ Proposer');
  btnProposer.type = 'button';
  btnProposer.style.margin = '6px 0 10px';
  corps.appendChild(btnProposer);

  const retour = mk('div', 'option-desc');
  retour.style.whiteSpace = 'pre-wrap';
  corps.appendChild(retour);

  corps.appendChild(mk('div', 'option-label', 'Bloc de l\'hypothèse (modifiable)'));
  const bloc = mk('textarea', 'yaml-edit');
  bloc.rows = 20;
  bloc.spellcheck = false;
  bloc.style.display = 'block';
  bloc.style.width = '100%';
  bloc.style.fontFamily = 'monospace';
  bloc.placeholder = '  - id: …\n    nom: …';
  corps.appendChild(bloc);

  const ligneBoutons = mk('div');
  ligneBoutons.style.marginTop = '8px';
  const btnVerifier = mk('button', 'yaml-btn', 'Vérifier');
  btnVerifier.type = 'button';
  const btnAjouter = mk('button', 'yaml-btn yaml-btn-save', 'Ajouter à hypotheses.yaml');
  btnAjouter.type = 'button';
  btnAjouter.style.marginLeft = '8px';
  ligneBoutons.appendChild(btnVerifier);
  ligneBoutons.appendChild(btnAjouter);
  corps.appendChild(ligneBoutons);

  const statut = mk('div', 'option-desc');
  statut.style.whiteSpace = 'pre-wrap';
  statut.style.marginTop = '6px';
  corps.appendChild(statut);
  wrapper.appendChild(corps);

  const afficher = (zone, data, titreOk) => {
    const lignes = [];
    if (data.error) lignes.push(`✗ ${data.error}`);
    (data.erreurs || []).forEach(e => lignes.push(`✗ ${e}`));
    (data.avertissements || []).forEach(a => lignes.push(`⚠ ${a}`));
    if (data.justification) lignes.push(`💬 ${data.justification}`);
    if (!data.error && !(data.erreurs || []).length && titreOk) lignes.unshift(titreOk);
    zone.textContent = lignes.join('\n');
    zone.style.color = (data.error || (data.erreurs || []).length) ? '#b03a2e' : '';
  };

  const appeler = async (action, texte) => {
    try {
      const res = await fetch(`/api/et_si/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texte }),
      });
      return await res.json();
    } catch (e) {
      return { error: `Erreur réseau : ${e.message}` };
    }
  };

  const occupe = (oui) => {
    [btnProposer, btnVerifier, btnAjouter].forEach(b => { b.disabled = oui; });
  };

  btnProposer.addEventListener('click', async () => {
    if (!idee.value.trim()) { retour.textContent = '✗ Écris d\'abord l\'idée.'; return; }
    if (bloc.value.trim() && !confirm('Remplacer le bloc actuel par une nouvelle proposition ?')) return;
    occupe(true);
    btnProposer.textContent = '✨ Proposition en cours… (un appel IA)';
    const data = await appeler('proposer', idee.value);
    btnProposer.textContent = '✨ Proposer';
    occupe(false);
    if (data.bloc) bloc.value = data.bloc;
    statut.textContent = '';
    afficher(retour, data, data.bloc ? '✓ Proposition prête : relis le bloc, puis Vérifier.' : '');
  });

  btnVerifier.addEventListener('click', async () => {
    if (!bloc.value.trim()) { statut.textContent = '✗ Bloc vide.'; return; }
    occupe(true);
    const data = await appeler('verifier', bloc.value);
    occupe(false);
    afficher(statut, data, `✓ ${data.id || 'Hypothèse'} : bloc valide.`);
  });

  btnAjouter.addEventListener('click', async () => {
    if (!bloc.value.trim()) { statut.textContent = '✗ Bloc vide.'; return; }
    occupe(true);
    const data = await appeler('ajouter', bloc.value);
    occupe(false);
    afficher(statut, data, data.message ? `✓ ${data.message}` : '');
    if (data.ok) {
      const sel = document.querySelector('#form-body [data-slug-type="hypotheses_et_si"]');
      if (sel) await rafraichirChampDynamique(sel);
      const panneau = document.querySelector('#form-body .yaml-panel[data-yaml-path="et_si/hypotheses.yaml"]');
      if (panneau) await loadYamlContent(panneau, 'et_si/hypotheses.yaml');
    }
  });

  return wrapper;
}
'''

# ------------------------------------------------------- scripts_config.json
MODE_SELECT = {
    "label": "Mode",
    "choices": [
        {"value": "simuler", "label": "Simuler une hypothèse",
         "note": "Choisis une hypothèse dans la liste, puis Lancer. Rien n'est jamais écrit dans le vault."},
        {"value": "nouvelle", "label": "Nouvelle hypothèse",
         "note": "Écris une idée dans le panneau ✨ ci-dessous : l'IA propose l'hypothèse, tu la corriges, "
                 "puis tu l'ajoutes à et_si/hypotheses.yaml. Le bouton Lancer ne sert pas dans ce mode."},
    ],
}

OPTION_ID = {
    "flag": "--id",
    "type": "slug_select",
    "label": "Hypothèse",
    "slug_type": "hypotheses_et_si",
    "mode_only": "simuler",
    "description": "Hypothèses de et_si/hypotheses.yaml (⚠ = mal remplie : le lancement listera ses erreurs). "
                   "« Aucun » = liste des hypothèses, sans rien simuler."
}


def maj_conf(conf):
    """Entrée simuler_et_si en deux modes. Retourne (conf, erreurs)."""
    e = next((x for x in conf if x.get("id") == "simuler_et_si"), None)
    if e is None:
        return conf, ["entrée `simuler_et_si` absente (patch v7.7 non appliqué ?)"]
    if e.get("assistant_hypothese"):
        return conf, ["entrée `simuler_et_si` déjà en deux modes"]
    opts = [o for o in e.get("options", []) if o.get("flag") != "--id"]
    # Scénario AVANT l'hypothèse : changer de scénario recharge les listes
    # déroulantes (et viderait une hypothèse déjà choisie).
    scen = [o for o in opts if o.get("flag") == "--scenario"]
    autres = [o for o in opts if o.get("flag") != "--scenario"]
    opts = scen + [OPTION_ID] + autres
    for o in opts:
        o["mode_only"] = "simuler"
    e["options"] = opts
    e["mode_select"] = MODE_SELECT
    e["assistant_hypothese"] = True
    e["description"] = ("Teste une hypothèse « et si ? » AVANT toute injection : effet chiffré sur les 12 "
                        "variables (avec et sans), tensions, aperçu de la carte et, en option, lecture des "
                        "conséquences par l'IA. Ne modifie jamais le vault. Onglet « Nouvelle hypothèse » : "
                        "écrire une hypothèse à partir d'une idée. Rapport : "
                        "documentation/need_action/et_si_<id>.md (et ci-dessous).")
    return conf, []


def appliquer(nom, texte, remplacements, erreurs):
    print(f"{nom} :")
    for libelle, ancien, nouveau in remplacements:
        n = texte.count(ancien)
        if n != 1:
            erreurs.append(f"{nom} — {libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        texte = texte.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    return texte


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7.7 -> v7.8 (GUI en deux modes).")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon : aperçu)")
    args = ap.parse_args()
    js_path = next((p for p in JS_CANDIDATS if p.exists()), None)
    for f in (SIMU, APP, CONF):
        if not f.exists():
            sys.exit(f"✗ Fichier introuvable : {f}")
    if js_path is None:
        sys.exit("✗ app.js introuvable (gui/static/app.js)")
    if not ASSIST.exists():
        sys.exit(f"✗ {ASSIST.relative_to(VAULT_ROOT)} absent : le placer dans generator/ d'abord")
    simu = SIMU.read_text(encoding="utf-8")
    if 'VERSION = "v7.8"' in simu:
        sys.exit("✗ Patch déjà appliqué (v7.8). Rien à faire.")
    if 'VERSION = "v7.7"' not in simu:
        sys.exit("✗ La v7.7 n'est pas installée : appliquer d'abord patch_s27_v77.py.")
    app_txt, js_txt, conf_txt = (APP.read_text(encoding="utf-8"), js_path.read_text(encoding="utf-8"),
                                 CONF.read_text(encoding="utf-8"))
    erreurs = []
    simu = appliquer("simuler_et_si.py", simu, REMPLACEMENTS_SIMU, erreurs)
    app_txt = appliquer("app.py", app_txt, REMPLACEMENTS_APP, erreurs)
    print("app.js :")
    if "function buildAssistantHypothese" in js_txt:
        erreurs.append("app.js : buildAssistantHypothese existe déjà")
    elif js_txt.count("  // YAML panels\n  await renderYamlPanels(script);\n") != 1:
        erreurs.append("app.js — appel du panneau : point d'insertion introuvable")
    else:
        js_txt = js_txt.replace("  // YAML panels\n  await renderYamlPanels(script);\n", JS_APPEL)
        js_txt = js_txt.rstrip("\n") + "\n" + JS_FONCTIONS
        print("  ✓ appel du panneau dans renderFormBody")
        print("  ✓ fonction buildAssistantHypothese (fin du fichier)")
    print("scripts_config.json :")
    try:
        conf = json.loads(conf_txt)
    except json.JSONDecodeError as e:
        sys.exit(f"✗ scripts_config.json illisible : {e}")
    conf, err_conf = maj_conf(conf)
    erreurs += [f"scripts_config.json : {e}" for e in err_conf]
    if not err_conf:
        print("  ✓ entrée simuler_et_si : modes Simuler / Nouvelle hypothèse, liste déroulante")
    nouveau_conf = json.dumps(conf, ensure_ascii=False, indent=2) + ("\n" if conf_txt.endswith("\n") else "")

    for f, src in ((SIMU, simu), (APP, app_txt), (ASSIST, ASSIST.read_text(encoding="utf-8"))):
        try:
            compile(src, str(f), "exec")
        except SyntaxError as e:
            erreurs.append(f"{f.name} ne compilerait pas : {e}")
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    for f, contenu in ((SIMU, simu), (APP, app_txt), (js_path, js_txt), (CONF, nouveau_conf)):
        shutil.copy(f, f.with_name(f.name + ".bak_v78"))
        f.write_text(contenu, encoding="utf-8")
        print(f"→ écrit : {f.relative_to(VAULT_ROOT)} (sauvegarde {f.name}.bak_v78)")
    print("\nSimulateur passé en v7.8. Redémarrer Flask, puis recharger la page (Cmd-Maj-R).")


if __name__ == "__main__":
    main()
