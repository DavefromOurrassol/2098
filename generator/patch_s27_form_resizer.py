#!/usr/bin/env python3
"""
patch_s27_form_resizer.py -- poignée violette entre le formulaire et la sortie (18 octobre 2026)
==============================================================================================
Le panneau « Parcours » vit dans la colonne du formulaire d'un script (#form-panel,
340 px fixes), à gauche de la colonne « Sortie » (#log-panel). La poignée posée sur le
panneau lui-même (patch_s27_poignee.py) ne pouvait pas élargir cette colonne.

  gui/templates/index.html : poignée `.panel-resizer` (la même que celles des onglets
      Articles, Instances, Carte…) entre #form-panel et #log-panel.
  gui/static/app.js :
      - glisser la poignée élargit ou rétrécit la colonne du formulaire, pour TOUS les
        scripts (la sortie garde au moins 260 px) ; largeur mémorisée ; double-clic :
        largeur par défaut (340 px) ;
      - la poignée propre au panneau « Parcours » est retirée, et sa largeur mémorisée
        oubliée (le bouton « ⛶ Agrandir » reste) ;
      - titres des étapes et des parties de l'étape ⑤ : écriture normale (le style
        « étiquette » du GUI les mettait en petites majuscules grises).

Prérequis : patch_s27_poignee.py et patch_s27_visuel.py appliqués.

Tout ou rien, sauvegardes .bak_form_resizer, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_form_resizer.py            (aperçu)
    python3 generator/patch_s27_form_resizer.py --apply
Puis recharger la page du GUI (Flask relit index.html à chaque requête en mode debug ;
sinon redémarrer le GUI).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_FORM_RESIZER"
VAULT = Path.cwd()
INDEX = VAULT / "gui" / "templates" / "index.html"
APP_JS = VAULT / "gui" / "static" / "app.js"

R_INDEX = [(
    '''        <div id="log-panel">''',
    '''        <!-- PATCH_S27_FORM_RESIZER : poignée formulaire / sortie -->
        <div class="panel-resizer" id="form-resizer" title="Glisser pour élargir/réduire le formulaire (double-clic : largeur par défaut)"></div>

        <div id="log-panel">''',
)]

R_JS = [
    (
        r"""initPanelResizer('#tab-articles .articles-sidebar', 'articles-resizer', 'ourrassol_articles_panel_width');""",
        r"""// PATCH_S27_FORM_RESIZER (18 octobre 2026) : poignée entre la colonne du formulaire d'un
// script (#form-panel, 340 px par défaut) et la sortie (#log-panel). Le panneau est à GAUCHE
// de sa poignée (comme #sidebar) : largeur = position de la souris − bord gauche.
(function initFormResizer() {
  const panel = document.getElementById('form-panel');
  const resizer = document.getElementById('form-resizer');
  if (!panel || !resizer) return;
  const CLE = 'ourrassol_form_panel_width';
  const MIN = 280;
  const maxi = () => Math.max(MIN, window.innerWidth - panel.getBoundingClientRect().left - 260);
  const poser = (px) => {
    panel.style.width = px ? `${px}px` : '';
    panel.style.minWidth = px ? `${px}px` : '';
  };
  try {
    const memo = parseInt(localStorage.getItem(CLE), 10);
    if (memo >= MIN) poser(Math.min(memo, Math.max(MIN, window.innerWidth - 500)));
  } catch (e) { /* stockage indisponible : largeur par défaut */ }
  let tire = false;
  resizer.addEventListener('mousedown', (e) => {
    tire = true;
    resizer.classList.add('dragging');
    document.body.classList.add('panel-resizing');
    e.preventDefault();
  });
  document.addEventListener('mousemove', (e) => {
    if (!tire) return;
    const largeur = e.clientX - panel.getBoundingClientRect().left;
    poser(Math.round(Math.max(MIN, Math.min(maxi(), largeur))));
  });
  document.addEventListener('mouseup', () => {
    if (!tire) return;
    tire = false;
    resizer.classList.remove('dragging');
    document.body.classList.remove('panel-resizing');
    try { localStorage.setItem(CLE, String(parseInt(panel.style.width, 10))); } catch (e) { /* rien */ }
  });
  resizer.addEventListener('dblclick', () => {
    poser(0);
    try { localStorage.removeItem(CLE); } catch (e) { /* rien */ }
  });
})();

initPanelResizer('#tab-articles .articles-sidebar', 'articles-resizer', 'ourrassol_articles_panel_width');""",
    ),
    (
        r"""  wrapper.appendChild(poignee);
""",
        r"""  // PATCH_S27_FORM_RESIZER : poignée du panneau remplacée par celle de la colonne (index.html).
  try { localStorage.removeItem(CLE_LARGEUR); } catch (e) { /* rien */ }
""",
    ),
    (
        r"""    if (memorisee >= LARGEUR_MIN) poserLargeur(memorisee);
""",
        r"""    void memorisee;   // PATCH_S27_FORM_RESIZER : plus de largeur propre au panneau
""",
    ),
    (
        r"""    Object.assign(titre.style, { display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.05em',
                                 fontWeight: '600', marginBottom: '6px' });""",
        r"""    Object.assign(titre.style, { display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.05em',
                                 fontWeight: '600', marginBottom: '6px',
                                 // PATCH_S27_FORM_RESIZER : pas le style « étiquette » (majuscules grises) du GUI
                                 textTransform: 'none', letterSpacing: 'normal', color: 'var(--text)' });""",
    ),
    (
        r"""    Object.assign(t.style, { marginTop: '18px', marginBottom: '8px', padding: '6px 10px', borderRadius: '6px',
                             background: 'rgba(128,128,128,0.14)', fontWeight: '600' });""",
        r"""    Object.assign(t.style, { marginTop: '18px', marginBottom: '8px', padding: '6px 10px', borderRadius: '6px',
                             background: 'rgba(128,128,128,0.14)', fontWeight: '600', fontSize: '12px',
                             textTransform: 'none', letterSpacing: 'normal', color: 'var(--text)' });""",
    ),
    (
        r"""  Object.assign(titreSortie.style, { marginTop: '16px', fontWeight: '600' });""",
        r"""  Object.assign(titreSortie.style, { marginTop: '16px', fontWeight: '600', fontSize: '12px',
                                     textTransform: 'none', letterSpacing: 'normal', color: 'var(--text)' });""",
    ),
]
DEBUT_PANNEAU = "// PATCH_S27_GUI_PARCOURS — PANNEAU"
FIN_PANNEAU = "// PATCH_GUI_OBSIDIAN_PANNEAUX"


def appliquer(texte, reps, nom, erreurs):
    for n, (ancien, neuf) in enumerate(reps, 1):
        if texte.count(ancien) != 1:
            erreurs.append(f"{nom} : repère n°{n} trouvé {texte.count(ancien)} fois (attendu 1)")
            continue
        texte = texte.replace(ancien, neuf)
    return texte


def node_check(code):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(code)
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
    for p in (INDEX, APP_JS):
        if not p.exists():
            sys.exit(f"✗ {p.relative_to(VAULT)} introuvable (lancer depuis la racine du coffre). Rien fait.")
    html = INDEX.read_text(encoding="utf-8")
    js = APP_JS.read_text(encoding="utf-8")
    if MARQUEUR in html or MARQUEUR in js:
        sys.exit("✗ patch déjà appliqué : rien fait.")
    erreurs = []
    for prealable, fichier in (("PATCH_S27_POIGNEE", "patch_s27_poignee.py"), ("PATCH_S27_VISUEL", "patch_s27_visuel.py")):
        if prealable not in js:
            erreurs.append(f"app.js : {fichier} absent (à appliquer d'abord)")
    html = appliquer(html, R_INDEX, "index.html", erreurs)
    js = appliquer(js, R_JS, "app.js", erreurs)
    if not erreurs:
        i = js.find("// PATCH_S27_FORM_RESIZER (18 octobre 2026)")
        j = js.find("initPanelResizer('#tab-articles", i)
        for morceau in (js[i:j], js[js.find(DEBUT_PANNEAU):js.find(FIN_PANNEAU, js.find(DEBUT_PANNEAU))]):
            err = node_check(morceau)
            if err:
                erreurs.append(f"app.js : JavaScript invalide après patch : {err}")
    if erreurs:
        print("✗ Rien n'a été écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
        sys.exit(1)
    print("  ✓ gui/templates/index.html : poignée formulaire / sortie prête")
    print("  ✓ gui/static/app.js : glissement de la colonne prêt, poignée du panneau retirée")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    for p, t in ((INDEX, html), (APP_JS, js)):
        shutil.copy2(p, p.with_name(p.name + ".bak_form_resizer"))
        p.write_text(t, encoding="utf-8")
    print("\n✓ Fait (sauvegardes .bak_form_resizer). Recharger la page du GUI (redémarrer si rien ne change).")


if __name__ == "__main__":
    main()
