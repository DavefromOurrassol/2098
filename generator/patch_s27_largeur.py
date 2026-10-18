#!/usr/bin/env python3
"""
patch_s27_largeur.py -- panneau « Parcours de l'hypothèse » agrandissable (18 octobre 2026)
==========================================================================================
  gui/static/app.js : bouton « ⛶ Agrandir » dans l'en-tête du panneau. Le panneau
  passe en grand, par-dessus la page (presque toute la fenêtre, défilement propre) ;
  « ⤡ Réduire » ou la touche Échap le remet en place. Indépendant de la mise en page
  du GUI (largeur du formulaire, sidebar).

Tout ou rien, sauvegarde .bak_largeur, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_largeur.py            (aperçu)
    python3 generator/patch_s27_largeur.py --apply
Puis recharger la page du GUI (pas besoin de redémarrer Flask : seul app.js change).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_LARGEUR"
APP_JS = Path.cwd() / "gui" / "static" / "app.js"
ANCRE = r"""  titleRow.appendChild(mk('span', 'yaml-panel-title', '🧭 Parcours de l\'hypothèse choisie dans la liste'));
"""
AJOUT = r"""  // PATCH_S27_LARGEUR : panneau agrandi par-dessus la page (Échap ou « Réduire » pour revenir).
  const btnLarge = mk('button', 'yaml-btn', '⛶ Agrandir');
  btnLarge.type = 'button';
  btnLarge.style.marginLeft = '12px';
  titleRow.appendChild(btnLarge);
  let agrandi = false;
  const fondPage = () => {
    const c = getComputedStyle(document.body).backgroundColor;
    return (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') ? c : '#ffffff';
  };
  const basculerLargeur = (oui) => {
    agrandi = oui;
    const s = wrapper.style;
    if (oui) {
      Object.assign(s, { position: 'fixed', top: '2vh', left: '2vw', right: '2vw', bottom: '2vh',
                         overflow: 'auto', zIndex: '1000', background: fondPage(), padding: '12px 18px',
                         boxShadow: '0 4px 30px rgba(0,0,0,0.35)', borderRadius: '6px' });
    } else {
      ['position', 'top', 'left', 'right', 'bottom', 'overflow', 'zIndex', 'background', 'padding',
       'boxShadow', 'borderRadius'].forEach(p => { s[p] = ''; });
    }
    btnLarge.textContent = oui ? '⤡ Réduire' : '⛶ Agrandir';
  };
  btnLarge.addEventListener('click', () => basculerLargeur(!agrandi));
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && agrandi && wrapper.isConnected) basculerLargeur(false);
  });
"""
DEBUT_PANNEAU = "// PATCH_S27_GUI_PARCOURS — PANNEAU"
FIN_PANNEAU = "// PATCH_GUI_OBSIDIAN_PANNEAUX"


def main():
    apply = "--apply" in sys.argv
    if not APP_JS.exists():
        sys.exit("✗ gui/static/app.js introuvable (lancer depuis la racine du coffre). Rien fait.")
    js = APP_JS.read_text(encoding="utf-8")
    if MARQUEUR in js:
        sys.exit("✗ patch déjà appliqué : rien fait.")
    if js.count(ANCRE) != 1:
        sys.exit(f"✗ en-tête du panneau trouvé {js.count(ANCRE)} fois (attendu 1) : rien fait.")
    js = js.replace(ANCRE, ANCRE + AJOUT)
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
    print("  ✓ gui/static/app.js : bouton « ⛶ Agrandir » prêt")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(APP_JS, APP_JS.with_name("app.js.bak_largeur"))
    APP_JS.write_text(js, encoding="utf-8")
    print("\n✓ Fait (sauvegarde app.js.bak_largeur). Recharger la page du GUI.")


if __name__ == "__main__":
    main()
