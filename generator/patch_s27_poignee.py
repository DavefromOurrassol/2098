#!/usr/bin/env python3
"""
patch_s27_poignee.py -- poignée de largeur du panneau « Parcours » (18 octobre 2026)
====================================================================================
  gui/static/app.js : une poignée sur le bord droit du panneau (le bord se colore au
  survol) : glisser pour élargir ou rétrécir ; largeur mémorisée dans le navigateur ;
  double-clic : largeur normale. Le bouton « ⛶ Agrandir » reste disponible (la poignée
  est masquée pendant l'agrandissement, la largeur choisie revient ensuite).

Prérequis : patch_s27_largeur.py appliqué. Tout ou rien, sauvegarde .bak_poignee,
refuse un second passage. Usage, depuis la racine du coffre :
    python3 generator/patch_s27_poignee.py            (aperçu)
    python3 generator/patch_s27_poignee.py --apply
Puis recharger la page du GUI.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_POIGNEE"
APP_JS = Path.cwd() / "gui" / "static" / "app.js"

REMPLACEMENTS = [
    (
        r"""      Object.assign(s, { position: 'fixed',""",
        r"""      // PATCH_S27_POIGNEE : la largeur choisie à la poignée est mise de côté pendant l'agrandissement.
      wrapper.dataset.largeur = s.width;
      s.width = '';
      s.maxWidth = '';
      poignee.style.display = 'none';
      Object.assign(s, { position: 'fixed',""",
    ),
    (
        r"""      ['position', 'top', 'left', 'right', 'bottom', 'overflow', 'zIndex', 'background', 'padding',
       'boxShadow', 'borderRadius'].forEach(p => { s[p] = ''; });""",
        r"""      ['top', 'left', 'right', 'bottom', 'overflow', 'zIndex', 'background', 'padding',
       'boxShadow', 'borderRadius'].forEach(p => { s[p] = ''; });
      s.position = 'relative';
      if (wrapper.dataset.largeur) { s.width = wrapper.dataset.largeur; s.maxWidth = 'none'; }
      poignee.style.display = '';""",
    ),
    (
        r"""  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && agrandi && wrapper.isConnected) basculerLargeur(false);
  });
""",
        r"""  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && agrandi && wrapper.isConnected) basculerLargeur(false);
  });
  // PATCH_S27_POIGNEE : poignée de largeur sur le bord droit (mémorisée dans ce navigateur).
  const CLE_LARGEUR = 'ourrassol_parcours_largeur';
  const LARGEUR_MIN = 400;
  wrapper.style.position = 'relative';
  const poignee = mk('div');
  poignee.title = 'Glisser pour changer la largeur du panneau (double-clic : largeur normale)';
  Object.assign(poignee.style, { position: 'absolute', top: '0', right: '-5px', width: '10px', height: '100%',
                                 cursor: 'col-resize', zIndex: '5' });
  poignee.addEventListener('mouseenter', () => { poignee.style.background = 'rgba(46,134,193,0.3)'; });
  poignee.addEventListener('mouseleave', () => { if (!tire) poignee.style.background = ''; });
  wrapper.appendChild(poignee);
  const poserLargeur = (px) => {
    wrapper.style.width = px ? `${px}px` : '';
    wrapper.style.maxWidth = px ? 'none' : '';
  };
  try {
    const memorisee = parseInt(localStorage.getItem(CLE_LARGEUR), 10);
    if (memorisee >= LARGEUR_MIN) poserLargeur(memorisee);
  } catch (e) { /* stockage indisponible : largeur normale */ }
  let tire = false;
  poignee.addEventListener('mousedown', (ev) => {
    if (agrandi) return;
    tire = true;
    document.body.style.userSelect = 'none';
    ev.preventDefault();
  });
  document.addEventListener('mousemove', (ev) => {
    if (!tire) return;
    const gauche = wrapper.getBoundingClientRect().left;
    const px = Math.max(LARGEUR_MIN, Math.min(window.innerWidth - gauche - 12, ev.clientX - gauche));
    poserLargeur(Math.round(px));
  });
  document.addEventListener('mouseup', () => {
    if (!tire) return;
    tire = false;
    document.body.style.userSelect = '';
    poignee.style.background = '';
    try { localStorage.setItem(CLE_LARGEUR, String(parseInt(wrapper.style.width, 10))); } catch (e) { /* rien */ }
  });
  poignee.addEventListener('dblclick', () => {
    poserLargeur(0);
    try { localStorage.removeItem(CLE_LARGEUR); } catch (e) { /* rien */ }
  });
""",
    ),
]
DEBUT_PANNEAU = "// PATCH_S27_GUI_PARCOURS — PANNEAU"
FIN_PANNEAU = "// PATCH_GUI_OBSIDIAN_PANNEAUX"


def main():
    apply = "--apply" in sys.argv
    if not APP_JS.exists():
        sys.exit("✗ gui/static/app.js introuvable (lancer depuis la racine du coffre). Rien fait.")
    js = APP_JS.read_text(encoding="utf-8")
    if MARQUEUR in js:
        sys.exit("✗ patch déjà appliqué : rien fait.")
    if "PATCH_S27_LARGEUR" not in js:
        sys.exit("✗ appliquer d'abord patch_s27_largeur.py : rien fait.")
    for n, (ancien, neuf) in enumerate(REMPLACEMENTS, 1):
        if js.count(ancien) != 1:
            sys.exit(f"✗ repère n°{n} trouvé {js.count(ancien)} fois (attendu 1) : rien fait.")
        js = js.replace(ancien, neuf)
    i = js.find(DEBUT_PANNEAU)
    j = js.find(FIN_PANNEAU, i)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js[i:j])
    try:
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            sys.exit("✗ JavaScript invalide après patch, rien écrit :\n" + r.stderr)
    except FileNotFoundError:
        print("  (node absent : contrôle JS sauté)")
    finally:
        Path(f.name).unlink()
    print("  ✓ gui/static/app.js : poignée de largeur prête")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(APP_JS, APP_JS.with_name("app.js.bak_poignee"))
    APP_JS.write_text(js, encoding="utf-8")
    print("\n✓ Fait (sauvegarde app.js.bak_poignee). Recharger la page du GUI.")


if __name__ == "__main__":
    main()
