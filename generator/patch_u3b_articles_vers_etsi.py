#!/usr/bin/env python3
"""patch_u3b — onglet Articles : « Promouvoir en événement » devient « ✨ Envoyer vers « et si ? » ».
L'article devient une HYPOTHÈSE (hypotheses.yaml) au lieu d'une injection directe.
L'ancien formulaire (et la route /api/edition/injecter_evenement, aussi utilisée par l'écran Édition)
restent en place, sans être appelés depuis Articles. Dry-run par défaut ; --apply écrit (.bak_u3b).
Depuis la racine du vault :  python3 generator/patch_u3b_articles_vers_etsi.py [--apply]"""
import sys, shutil, subprocess
from pathlib import Path
APPLY = "--apply" in sys.argv
ROOT = Path(sys.argv[sys.argv.index("--root")+1]) if "--root" in sys.argv else Path(".")
JS = ROOT / "gui" / "static" / "app.js"

FONCTION = r'''function renderArticlesVersEtSi(article, container) {
  // U3b : l'article devient une hypothèse « et si ? » (même chemin que ✨ Nouvelle hypothèse).
  const dateReelle = article.annee != null
    ? `${article.jour} ${MOIS_FR_JS[article.mois]} ${article.annee}` : null;
  const texte = [
    article.chapo || article.slug || '',
    dateReelle ? `Article du ${dateReelle} (scénario ${article.scenario}).`
               : `Article du scénario ${article.scenario}.`,
    article.zone_principale ? `Lieu : ${article.zone_principale}.` : '',
    (article.entites_citees || []).length ? `Entités citées : ${article.entites_citees.join(', ')}.` : '',
    `Source : article ${article.fichier}.`,
  ].filter(Boolean).join(' ');

  const mk = (tag, txt, css) => {
    const e = document.createElement(tag);
    if (txt) e.textContent = txt;
    if (css) e.style.cssText = css;
    return e;
  };
  const appeler = async (action, corps, type) => {
    try {
      const res = await fetch(`/api/et_si/${action}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texte: corps, type: action === 'proposer' ? type : '' }),
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

  container.innerHTML = '';
  const boite = mk('div', '', 'margin-top:4px;border-top:1px solid #444;padding-top:12px');
  boite.appendChild(mk('div', `Envoyer « ${article.slug} » vers « et si ? »`, 'font-size:13px;font-weight:600'));
  boite.appendChild(mk('div',
    'L\'IA transforme l\'article en hypothèse (un appel IA). Tu relis le bloc, « Vérifier », puis ' +
    '« Ajouter ». Rien n\'est écrit avant « Ajouter » ; la suite se fait dans l\'onglet « Et si ? » ' +
    '(Simuler → Décider → Injecter).', 'font-size:11px;color:#888;margin:4px 0 8px'));
  const ligne = mk('div', '', 'display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px');
  const selType = mk('select', '', 'width:auto;max-width:60%');
  [['evenement', 'comme événement'], ['signal', 'comme signal faible']].forEach(([v, l]) => {
    const o = document.createElement('option'); o.value = v; o.textContent = l; selType.appendChild(o);
  });
  const btn = mk('button', '✨ Proposer');
  btn.type = 'button'; btn.className = 'yaml-btn yaml-btn-save';
  ligne.appendChild(selType); ligne.appendChild(btn);
  boite.appendChild(ligne);
  const etat = mk('div', '', 'font-size:11px;white-space:pre-wrap');
  const zone = mk('div');
  boite.appendChild(etat); boite.appendChild(zone);
  container.appendChild(boite);

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    etat.style.color = '';
    etat.textContent = 'Appel IA en cours (hypothese_depuis_texte.py)…';
    const data = await appeler('proposer', texte, selType.value);
    btn.disabled = false;
    if (data.error || !data.bloc) {
      etat.style.color = '#b03a2e';
      etat.textContent = `✗ ${data.error || 'aucun bloc proposé'}`;
      return;
    }
    etat.textContent = '';
    zone.innerHTML = '';
    const retour = mk('div', '', 'font-size:11px;white-space:pre-wrap');
    afficher(retour, data, '✓ Proposition prête : relis le bloc, puis Vérifier.');
    const bloc = mk('textarea', '', 'display:block;width:100%;font-family:monospace;margin:6px 0');
    bloc.className = 'yaml-edit'; bloc.rows = 18; bloc.spellcheck = false; bloc.value = data.bloc;
    const lb = mk('div');
    const bV = mk('button', 'Vérifier'); bV.type = 'button'; bV.className = 'yaml-btn';
    const bA = mk('button', 'Ajouter à hypotheses.yaml', 'margin-left:8px');
    bA.type = 'button'; bA.className = 'yaml-btn yaml-btn-save';
    lb.appendChild(bV); lb.appendChild(bA);
    const st = mk('div', '', 'font-size:11px;white-space:pre-wrap;margin-top:6px');
    [retour, bloc, lb, st].forEach(e => zone.appendChild(e));
    const occupe = (oui) => { bV.disabled = oui; bA.disabled = oui; };
    bV.addEventListener('click', async () => {
      occupe(true);
      const d = await appeler('verifier', bloc.value);
      occupe(false);
      afficher(st, d, `✓ ${d.id || 'Hypothèse'} : bloc valide.`);
    });
    bA.addEventListener('click', async () => {
      occupe(true);
      const d = await appeler('ajouter', bloc.value);
      afficher(st, d, d.message ? `✓ ${d.message}` : '');
      if (!d.ok) occupe(false);   // ajout réussi : « Ajouter » reste verrouillé (pas de double ajout)
    });
  });
}

'''

EDITS = [
 ('style="background:#2c8a4b">Promouvoir en événement</button>',
  'style="background:#2c8a4b" title="Un appel IA : l\'article devient une hypothèse « et si ? »">✨ Envoyer vers « et si ? »</button>'),
 ("      renderArticlesPromouvoirForm(a, zone);",
  "      renderArticlesVersEtSi(a, zone);   // U3b"),
 ("function renderArticlesPromouvoirForm(article, container) {",
  FONCTION + "function renderArticlesPromouvoirForm(article, container) {"),
]
txt = JS.read_text(encoding="utf-8")
ok = True
for k, (old, new) in enumerate(EDITS, 1):
    n = txt.count(old)
    if n != 1:
        print(f"✗ modif {k} : {n} occurrence(s) (1 attendue)"); ok = False
    else:
        txt = txt.replace(old, new)
if not ok:
    print("✗ rien écrit"); sys.exit(1)
if not APPLY:
    print("✓ dry-run : 3 modifications dans app.js"); sys.exit(0)

def node_ok(p):
    try:
        return subprocess.run(["node", "--check", str(p)], capture_output=True, text=True).returncode == 0
    except FileNotFoundError:
        return None
bak = JS.with_name(JS.name + ".bak_u3b")
shutil.copy2(JS, bak)
JS.write_text(txt, encoding="utf-8")
avant, apres = node_ok(bak), node_ok(JS)
if avant is True and apres is False:
    shutil.copy2(bak, JS)
    print("✗ erreur de syntaxe JavaScript introduite : fichier restauré"); sys.exit(1)
print("✓ appliqué" + ("" if apres else " (contrôle node non concluant : node absent ou déjà en erreur avant le patch)"))
