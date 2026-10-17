#!/usr/bin/env python3
"""
patch_s27_gui_parcours.py — Ourrassol 2098 (S27, refonte du panneau, 17 octobre 2026)
====================================================================================

Remplace le panneau « ⚖️ Décider » du simulateur « et si ? » par le panneau
« 🧭 Parcours de l'hypothèse » : statut de l'hypothèse choisie, puis les étapes
① Tester ② Décider ③ Injecter ④ Appliquer ⑤ À la main ; étapes à venir masquées,
aide « ⓘ » à chaque étape (dont le mode d'emploi de Sauter / Inclure).
  - gui/static/app.js : fonction buildDecisionHypothese() remplacée (même clé
    assistant_decision dans scripts_config.json) ;
  - gui/app.py : routes POST /api/et_si/statut (et_si_statut.py --json) et
    /api/et_si/injecter/<apercu|injecter> (et_si_injecter.py).
Prérequis : patch_s27_gui_appliquer.py appliqué ; generator/et_si_statut.py et
generator/et_si_injecter.py en place. Tout ou rien, sauvegardes .bak_gui_parcours,
refuse un second passage.

USAGE (depuis la racine du vault, puis redémarrer Flask)
    python3 generator/patch_s27_gui_parcours.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GEN = Path(__file__).resolve().parent
VAULT = GEN.parent
APP_PY = VAULT / "gui" / "app.py"
APP_JS = VAULT / "gui" / "static" / "app.js"
NOUVEAU_JS = r'''// ══════════════════════════════════════════════════
// PATCH_S27_GUI_PARCOURS — PANNEAU « PARCOURS DE L'HYPOTHÈSE » (PATCH_S27_GUI_PARCOURS, 17 octobre 2026)
// ══════════════════════════════════════════════════
// Remplace le panneau « Décider » du 12 octobre (même clé assistant_decision dans
// scripts_config.json, visible en mode « Simuler »). Pour l'hypothèse choisie dans la
// liste --id : statut, puis les étapes ① Tester ② Décider ③ Injecter ④ Appliquer
// ⑤ À la main. Les étapes à venir sont masquées ; l'étape en cours est ouverte.
// Routes : /api/et_si/statut, /api/et_si/decider/<action>, /api/et_si/injecter/<action>,
// /api/et_si/appliquer/<action>. Aucun appel IA, sauf ③ (injection).
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
  const champ = (placeholder, largeur) => {
    const c = mk('input');
    c.type = 'text';
    c.placeholder = placeholder;
    c.autocomplete = 'off';
    c.style.width = largeur || '22%';
    c.style.marginRight = '12px';
    return c;
  };
  const aide = (texte) => {
    const d = mk('details');
    d.style.margin = '4px 0 6px 0';
    const s = mk('summary', 'option-desc', 'ⓘ comment faire');
    s.style.cursor = 'pointer';
    d.appendChild(s);
    const p = mk('div', 'option-desc');
    p.style.whiteSpace = 'pre-wrap';
    p.style.marginTop = '4px';
    p.textContent = texte;
    d.appendChild(p);
    return d;
  };
  const lienObsidian = (texte) => {
    const b = bouton(texte);
    b.style.display = 'none';
    b.addEventListener('click', () => { if (b.dataset.chemin) _panneauOuvrirDansObsidian(b.dataset.chemin); });
    return b;
  };

  // En-tête : statut de l'hypothèse choisie
  const header = mk('div', 'yaml-panel-header');
  const titleRow = mk('div', 'yaml-panel-title-row');
  titleRow.appendChild(mk('span', 'yaml-panel-title', '🧭 Parcours de l\'hypothèse choisie dans la liste'));
  header.appendChild(titleRow);
  wrapper.appendChild(header);

  const corps = mk('div', 'yaml-form-zone');
  corps.style.padding = '8px 0';
  wrapper.appendChild(corps);

  const ligneStatut = mk('div');
  const statutTxt = mk('span', 'option-label', 'Choisis une hypothèse dans la liste ci-dessus.');
  const btnActualiser = bouton('↻ Actualiser');
  ligneStatut.appendChild(statutTxt);
  ligneStatut.appendChild(btnActualiser);
  corps.appendChild(ligneStatut);
  const alertesEl = mk('div', 'option-desc');
  alertesEl.style.color = '#b03a2e';
  alertesEl.style.whiteSpace = 'pre-wrap';
  corps.appendChild(alertesEl);

  // Une étape = un bloc avec titre (pastille d'état) et contenu
  const ETAPES = ['Tester', 'Décider', 'Injecter', 'Appliquer au vault', 'À faire à la main'];
  const blocs = ETAPES.map((nom, i) => {
    const bloc = mk('div');
    bloc.style.borderLeft = '3px solid #ccc';
    bloc.style.padding = '4px 0 4px 10px';
    bloc.style.margin = '10px 0';
    const titre = mk('div', 'option-label');
    const contenu = mk('div');
    bloc.appendChild(titre);
    bloc.appendChild(contenu);
    corps.appendChild(bloc);
    return { bloc, titre, contenu, nom, n: i + 1 };
  });

  // ① Tester
  const b1 = blocs[0].contenu;
  const resumeSim = mk('div', 'option-desc');
  b1.appendChild(resumeSim);
  b1.appendChild(aide(
    'Règle les options ci-dessus (laisse « Scénario » vide, coche « Lecture IA » et « Passe exhaustive »), ' +
    'puis clique sur Lancer. La simulation ne modifie jamais le vault. Lis ensuite le rapport : effets ' +
    'chiffrés, lecture IA, passe exhaustive, liste d\'application. Clique sur ↻ Actualiser quand elle est finie.'));
  const lienRapport = lienObsidian('Ouvrir le rapport ↗');
  b1.appendChild(lienRapport);

  // ② Décider
  const b2 = blocs[1].contenu;
  const resumeDec = mk('div', 'option-desc');
  b2.appendChild(resumeDec);
  const zoneAdopter = mk('div');
  zoneAdopter.appendChild(mk('span', 'option-label', 'Portée '));
  const portee = choix([['', '— celle de la simulation —'], ['locale', 'locale'], ['regionale', 'régionale'],
                        ['continentale', 'continentale'], ['globale', 'globale']]);
  zoneAdopter.appendChild(portee);
  zoneAdopter.appendChild(mk('span', 'option-label', 'Intensité '));
  const intensite = choix([['', '— à choisir —'], ['faible', 'faible'], ['modérée', 'modérée'],
                           ['forte', 'forte'], ['majeure', 'majeure']]);
  zoneAdopter.appendChild(intensite);
  const ligneAdopter = mk('div');
  const btnApercu = bouton('Aperçu de l\'adoption');
  const btnAdopter = bouton('Adopter', 'yaml-btn yaml-btn-save');
  ligneAdopter.appendChild(btnApercu);
  ligneAdopter.appendChild(btnAdopter);
  zoneAdopter.appendChild(ligneAdopter);
  const ligneRejeter = mk('div');
  const motif = champ('motif du rejet (facultatif)', '50%');
  const btnRejeter = bouton('Rejeter');
  ligneRejeter.appendChild(motif);
  ligneRejeter.appendChild(btnRejeter);
  zoneAdopter.appendChild(ligneRejeter);
  b2.appendChild(zoneAdopter);
  const btnAnnuler = bouton('Annuler la décision');
  b2.appendChild(btnAnnuler);
  b2.appendChild(aide(
    'Adopter : l\'événement, tel qu\'il a été simulé, est placé dans la file d\'injection. Choisis la portée ' +
    'si celle de la simulation ne convient pas (un accident local n\'est pas « globale »), et toujours ' +
    'l\'intensité. Fais l\'aperçu d\'abord.\nRejeter : garde la trace et le motif.\nAnnuler la décision : ' +
    'l\'hypothèse redevient « simulé » ; son entrée quitte la file si elle n\'a pas encore été injectée.'));

  // ③ Injecter
  const b3 = blocs[2].contenu;
  const resumeInj = mk('div', 'option-desc');
  b3.appendChild(resumeInj);
  const ligneInjecter = mk('div');
  const btnInjApercu = bouton('Simuler l\'injection');
  const btnInjecter = bouton('Injecter', 'yaml-btn yaml-btn-save');
  ligneInjecter.appendChild(btnInjApercu);
  ligneInjecter.appendChild(btnInjecter);
  b3.appendChild(ligneInjecter);
  b3.appendChild(aide(
    'Injecte cette hypothèse seule : sa fiche d\'événement est rédigée par l\'IA avec les valeurs et les ' +
    'faits imposés par la simulation, puis le cycle de localisation et validate.py s\'enchaînent. Son entrée ' +
    'quitte ensuite la file : « Injecter des événements » ne la reprendra pas.\nSimuler l\'injection fait les ' +
    'mêmes appels IA (quelques centimes) sans rien écrire : vérifie qu\'aucune ligne ⚠ n\'apparaît ' +
    '(entité censée survivre décrite comme détruite, mot « matrice »). Le texte final peut différer de la ' +
    'simulation (nouveau tirage). Compte une à deux minutes.'));

  // ④ Appliquer
  const b4 = blocs[3].contenu;
  const resumeApp = mk('div', 'option-desc');
  b4.appendChild(resumeApp);
  const ligneTri = mk('div');
  ligneTri.appendChild(mk('span', 'option-label', 'Sauter '));
  const sauter = champ('ex : 3,7');
  ligneTri.appendChild(sauter);
  ligneTri.appendChild(mk('span', 'option-label', 'Inclure (⚠) '));
  const inclure = champ('ex : 6');
  ligneTri.appendChild(inclure);
  b4.appendChild(ligneTri);
  const ligneAppliquer = mk('div');
  const btnAppApercu = bouton('Aperçu de l\'application');
  const btnAppliquer = bouton('Appliquer', 'yaml-btn yaml-btn-save');
  ligneAppliquer.appendChild(btnAppApercu);
  ligneAppliquer.appendChild(btnAppliquer);
  b4.appendChild(ligneAppliquer);
  b4.appendChild(aide(
    'Reporte les conséquences sur les fiches : statuts de zone, trajectoires, retrait de TOUTES les ' +
    'relations d\'une entité qui disparaît, relations nouvelles ou rompues ; puis réciprocité (l\'opposition ' +
    'l\'emporte) et validate.py. Fais toujours l\'aperçu d\'abord, et un commit git avant d\'appliquer.\n\n' +
    'Par défaut : les opérations ✓ sont appliquées, les ⚠ sont mises de côté.\n' +
    '• Sauter (numéros d\'opérations ✓) : à décider AVANT d\'appliquer, l\'outil ne sait pas défaire. ' +
    'Saute si le lien avec l\'événement est trop lointain, si l\'opération contredit ton lore, ou si une ' +
    'relation est seulement « opportune ».\n' +
    '• Inclure (numéros d\'opérations ⚠) : peut attendre, une relance n\'applique que ce qui manque.\n' +
    '  – saut d\'un cran (émergent → dominant) : inclure si l\'entité absorbe directement ce qui ' +
    'disparaît (souvent une fiche restée « émergent » par défaut) ; sinon passer l\'entité à « ascendant » ' +
    'avec changer_trajectoire.py.\n' +
    '  – contredit une alliance (ou opposition) existante : inclure seulement si l\'événement retourne la ' +
    'relation (l\'ancienne sera retirée).\n' +
    '  – lecture et passe divergent : lire les deux raisons dans le rapport ; inclure applique la version ' +
    'de la passe.\n' +
    '  – trajectoire actuelle ≠ « avant » : la fiche a changé depuis la simulation ; la relire, presque ' +
    'jamais inclure.\n' +
    '  – homonyme dans le scénario : ne pas inclure ; fusionner le doublon (fusionner_doublon_instance.py) ' +
    'puis resimuler.\n' +
    '  – rupture « justifiée par une disparition que rien ne déclare » : deux tirages de l\'IA se ' +
    'contredisent ; laisser de côté.\n' +
    'Plusieurs numéros : séparés par des virgules (3,7).'));

  // ⑤ À la main
  const b5 = blocs[4].contenu;
  const resumeMain = mk('div', 'option-desc');
  b5.appendChild(resumeMain);
  const ligneMain = mk('div');
  const btnReste = bouton('Générer la check-list');
  const lienChecklist = lienObsidian('Ouvrir la check-list ↗');
  ligneMain.appendChild(btnReste);
  ligneMain.appendChild(lienChecklist);
  b5.appendChild(ligneMain);
  b5.appendChild(aide(
    'La check-list liste ce que l\'outil ne fait pas : phrases à réécrire (en entier, avec le fait qui les ' +
    'contredit), nouvelles entités proposées (bloc YAML), brouillon de règle de lore, articles à relire, ' +
    'opérations ⚠ laissées de côté, puis audit du lore, résumé du scénario et site. C\'est du travail ' +
    'd\'écriture, à faire à ton rythme ; régénère-la si tu inclus une opération plus tard.'));

  // Pied : dossiers et sortie
  const pied = mk('div');
  pied.style.marginTop = '8px';
  const btnDossiers = bouton('Voir tous les dossiers');
  pied.appendChild(btnDossiers);
  corps.appendChild(pied);
  const sortie = mk('pre');
  sortie.style.whiteSpace = 'pre-wrap';
  sortie.style.fontSize = '0.85em';
  sortie.style.marginTop = '6px';
  corps.appendChild(sortie);

  const tous = [btnActualiser, btnApercu, btnAdopter, btnRejeter, btnAnnuler, btnInjApercu, btnInjecter,
                btnAppApercu, btnAppliquer, btnReste, btnDossiers];
  const listeHyp = () => document.querySelector('#form-body [data-slug-type="hypotheses_et_si"]');
  const montrer = (el, oui) => { el.style.display = oui ? '' : 'none'; };
  const date = (d) => {
    const m = String(d || '').match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}:\d{2}))?/);
    return m ? `${m[3]}/${m[2]}/${m[1]}` + (m[4] ? ` à ${m[4]}` : '') : (d || '?');
  };

  // Affichage selon l'état
  const afficher = (e) => {
    if (!e) {
      statutTxt.textContent = 'Choisis une hypothèse dans la liste ci-dessus.';
      alertesEl.textContent = '';
      blocs.forEach(b => montrer(b.bloc, false));
      return;
    }
    statutTxt.textContent = `Statut : ${e.statut}  `;
    alertesEl.textContent = (e.alertes || []).map(a => `⚠ ${a}`).join('\n');
    blocs.forEach(b => {
      const etat = b.n < e.etape ? 'fait' : (b.n === e.etape ? 'en cours' : 'à venir');
      montrer(b.bloc, etat !== 'à venir');
      b.titre.textContent = `${'①②③④⑤'[b.n - 1]} ${b.nom} — ${etat === 'fait' ? '✓ fait' : '▶ en cours'}`;
      b.bloc.style.borderLeftColor = etat === 'en cours' ? '#2e86c1' : '#7dcea0';
    });
    const sim = e.simulation, dec = e.decision;
    resumeSim.textContent = sim
      ? `Simulée le ${date(sim.date)} (${sim.version}) — ${sim.complet ? 'tous les scénarios' : 'simulation partielle'}` +
        `${sim.passe ? ', passe exhaustive' : ''}.`
      : 'Pas encore simulée.';
    if (sim && sim.rapport) { lienRapport.dataset.chemin = sim.rapport; montrer(lienRapport, true); }
    else montrer(lienRapport, false);
    resumeDec.textContent = dec
      ? `${dec.statut === 'rejeté' ? 'Rejetée' : 'Adoptée'} le ${date(dec.date)}` +
        (dec.portee ? ` — portée ${dec.portee}, intensité ${dec.intensite}` : '') +
        (dec.motif ? ` — ${dec.motif}` : '') + '.'
      : '';
    montrer(zoneAdopter, e.etape === 2);
    montrer(btnAnnuler, !!dec);
    montrer(ligneInjecter, e.etape === 3 && e.statut === 'adopté, en attente d\'injection');
    resumeInj.textContent = e.etape > 3 ? 'Événement injecté dans le vault.' :
      (e.statut === 'adopté, en attente d\'injection' ? 'En attente dans la file d\'injection.' : '');
    resumeApp.textContent = e.applique ? `Appliquée le ${date(e.applique)} (relancer n'applique que ce qui manque).`
      : (e.operations ? '' : 'Fichier des opérations absent : resimuler avant d\'appliquer.');
    resumeMain.textContent = e.checklist ? 'Check-list générée.' : '';
    if (e.checklist) { lienChecklist.dataset.chemin = e.checklist; montrer(lienChecklist, true); }
    else montrer(lienChecklist, false);
  };

  const actualiser = async () => {
    const sel = listeHyp();
    const id = sel ? sel.value : '';
    if (!id) { afficher(null); return; }
    try {
      const res = await fetch('/api/et_si/statut', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }),
      });
      const data = await res.json();
      if (data.error) { statutTxt.textContent = `✗ ${data.error}`; return; }
      afficher(data);
    } catch (err) {
      statutTxt.textContent = `✗ Erreur réseau : ${err.message}`;
    }
  };

  const appeler = async (base, action, extra) => {
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
      const res = await fetch(`/api/et_si/${base}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.assign({ id }, extra || {})),
      });
      data = await res.json();
    } catch (err) {
      data = { error: `Erreur réseau : ${err.message}` };
    }
    tous.forEach(b => { b.disabled = false; });
    sortie.textContent = data.error ? `✗ ${data.error}` : (data.sortie || '(aucune sortie)');
    sortie.style.color = (data.error || !data.ok) ? '#b03a2e' : '';
    if (sel && id && action !== 'dossiers') {
      await rafraichirChampDynamique(sel);   // statut dans la liste
      sel.value = id;
      await actualiser();
    }
  };

  const tri = () => ({ sauter: sauter.value, inclure: inclure.value });
  btnActualiser.addEventListener('click', actualiser);
  btnApercu.addEventListener('click', () =>
    appeler('decider', 'adopter', { portee: portee.value, intensite: intensite.value, apercu: true }));
  btnAdopter.addEventListener('click', () => {
    if (!confirm('Adopter : placer l\'événement simulé dans la file d\'injection ?')) return;
    appeler('decider', 'adopter', { portee: portee.value, intensite: intensite.value });
  });
  btnRejeter.addEventListener('click', () => appeler('decider', 'rejeter', { motif: motif.value }));
  btnAnnuler.addEventListener('click', () => {
    if (!confirm('Annuler la décision prise sur cette hypothèse ?')) return;
    appeler('decider', 'annuler', {});
  });
  btnInjApercu.addEventListener('click', () => appeler('injecter', 'apercu', {}));
  btnInjecter.addEventListener('click', () => {
    if (!confirm('Injecter cet événement dans le vault ? (appels IA ; une à deux minutes)')) return;
    appeler('injecter', 'injecter', {});
  });
  btnAppApercu.addEventListener('click', () => appeler('appliquer', 'apercu', tri()));
  btnAppliquer.addEventListener('click', () => {
    if (!confirm('Appliquer au vault les opérations retenues par l\'aperçu ?\n' +
                 '(Sauvegarde .bak_appliquer ; commit git conseillé avant.)')) return;
    appeler('appliquer', 'appliquer', tri());
  });
  btnReste.addEventListener('click', () => appeler('appliquer', 'reste', tri()));
  btnDossiers.addEventListener('click', () => appeler('decider', 'dossiers', {}));

  // Changement d'hypothèse dans la liste : un seul écouteur global pour tout le GUI,
  // qui rappelle le panneau actuellement affiché.
  window._parcoursActualiser = () => { if (wrapper.isConnected) actualiser(); };
  if (!window._parcoursEcoute) {
    window._parcoursEcoute = true;
    document.addEventListener('change', (ev) => {
      const t = ev.target;
      if (t && t.matches && t.matches('[data-slug-type="hypotheses_et_si"]') && window._parcoursActualiser) {
        window._parcoursActualiser();
      }
    });
  }
  afficher(null);
  setTimeout(actualiser, 400);   // la liste des hypothèses se charge après le panneau
  return wrapper;
}


'''
MARQUEUR = "PATCH_S27_GUI_PARCOURS"
DEBUT_JS = "// ══════════════════════════════════════════════════\n// PANNEAU « DÉCIDER »"
FIN_JS = "// PATCH_GUI_OBSIDIAN_PANNEAUX"
ANCRE_PY = "TIMEOUT_IDEES_TEXTE_LIBRE = 180  # secondes -- un seul appel LLM\n"
ROUTES_PY = r'''# ---------------------------------------------------------------------------
# PATCH_S27_GUI_PARCOURS (17 octobre 2026) -- panneau « Parcours de l'hypothèse » :
# état de l'hypothèse (et_si_statut.py, lecture seule) et injection d'une seule
# hypothèse adoptée (et_si_injecter.py : inject_custom_events.py --idea, puis
# retrait de son entrée de la queue).
# ---------------------------------------------------------------------------

TIMEOUT_INJECTER_ET_SI = 960  # secondes -- appels IA par scénario + cycle post-injection


@app.route("/api/et_si/statut", methods=["POST"])
def et_si_statut():
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    hid = str((request.get_json() or {}).get("id") or "").strip()
    if not hid:
        return jsonify({"error": "choisis d'abord une hypothèse dans la liste"}), 400
    try:
        r = subprocess.run([sys.executable, "et_si_statut.py", "--id", hid, "--json"], cwd=pipeline_dir,
                           capture_output=True, text=True, timeout=90, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Délai dépassé (90 s)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"et_si_statut.py introuvable dans {pipeline_dir}"}), 500
    try:
        return jsonify(json.loads(r.stdout.strip().splitlines()[-1]))
    except (ValueError, IndexError):
        return jsonify({"error": (r.stderr or r.stdout or "réponse illisible").strip()[-500:]}), 500


@app.route("/api/et_si/injecter/<action>", methods=["POST"])
def et_si_injecter(action):
    if action not in ("apercu", "injecter"):
        return jsonify({"error": f"action inconnue : {action}"}), 404
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    hid = str((request.get_json() or {}).get("id") or "").strip()
    if not hid:
        return jsonify({"error": "choisis d'abord une hypothèse dans la liste"}), 400
    cmd = [sys.executable, "et_si_injecter.py", "--id", hid] + (["--dry-run"] if action == "apercu" else [])
    try:
        r = subprocess.run(cmd, cwd=pipeline_dir, capture_output=True, text=True,
                           timeout=TIMEOUT_INJECTER_ET_SI, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Délai dépassé ({TIMEOUT_INJECTER_ET_SI} s) : vérifier "
                                 "evenements_custom/processed.yaml et needs_review.yaml"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"et_si_injecter.py introuvable dans {pipeline_dir}"}), 500
    sortie = "\n".join(s for s in (r.stdout.strip(), r.stderr.strip()) if s)
    return jsonify({"ok": r.returncode == 0, "sortie": sortie})


'''


def main():
    for p in (APP_PY, APP_JS, GEN / "et_si_statut.py", GEN / "et_si_injecter.py"):
        if not p.exists():
            sys.exit(f"✗ {p} introuvable : rien fait.")
    js, py = APP_JS.read_text(encoding="utf-8"), APP_PY.read_text(encoding="utf-8")
    if MARQUEUR in js or MARQUEUR in py:
        sys.exit("✗ patch déjà appliqué : rien fait.")
    if "PATCH_S27_GUI_APPLIQUER" not in py:
        sys.exit("✗ appliquer d'abord patch_s27_gui_appliquer.py : rien fait.")
    if js.count(DEBUT_JS) != 1 or py.count(ANCRE_PY) != 1:
        sys.exit("✗ début du panneau Décider ou ancre d'app.py introuvable (ou en double) : rien fait.")
    i = js.index(DEBUT_JS)
    j = js.find(FIN_JS, i)
    if j < 0 or "function buildDecisionHypothese()" not in js[i:j]:
        sys.exit("✗ fin du panneau Décider introuvable : rien fait.")
    js = js[:i] + NOUVEAU_JS + js[j:]
    if js.count("function buildDecisionHypothese()") != 1:
        sys.exit("✗ buildDecisionHypothese présente plusieurs fois après remplacement : rien fait.")
    py = py.replace(ANCRE_PY, ROUTES_PY + ANCRE_PY)
    compile(py, str(APP_PY), "exec")
    if "\nimport json" not in py and "import json," not in py:
        sys.exit("✗ app.py n'importe pas json : rien fait.")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(NOUVEAU_JS)
    try:
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            sys.exit("✗ nouveau panneau JS invalide, rien fait :\n" + r.stderr)
    except FileNotFoundError:
        print("  (node absent : contrôle JS sauté)")
    finally:
        Path(f.name).unlink(missing_ok=True)
    for p, t in ((APP_PY, py), (APP_JS, js)):
        shutil.copy2(p, p.with_name(p.name + ".bak_gui_parcours"))
        p.write_text(t, encoding="utf-8")
    print("✓ gui/app.py et gui/static/app.js modifiés, sauvegardes .bak_gui_parcours")
    print("  Redémarrer Flask : le panneau « 🧭 Parcours de l'hypothèse » remplace « ⚖️ Décider ».")


if __name__ == "__main__":
    main()
