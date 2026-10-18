#!/usr/bin/env python3
"""
patch_s27_visuel.py -- panneau « Parcours » plus lisible (18 octobre 2026)
=========================================================================
  gui/static/app.js :
  - frise des cinq étapes en haut (pastilles numérotées : vert = fait, bleu = en cours,
    gris = à venir) ;
  - chaque étape devient une carte : bordure gauche épaisse et fond teinté de la couleur
    de son état, pastille numérotée, étiquette « ✓ fait » / « ▶ en cours », ombre légère
    sur l'étape en cours ;
  - étape ⑤ : chaque partie (🧩 entités, ✏️ phrases, 📜 règle, 🏁 pour finir) a un
    bandeau de titre ;
  - le résultat du dernier bouton est encadré, sous un titre, avec défilement propre.
  Couleurs translucides : lisibles en thème clair comme sombre.

Tout ou rien, sauvegarde .bak_visuel, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_visuel.py            (aperçu)
    python3 generator/patch_s27_visuel.py --apply
Puis recharger la page du GUI.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_VISUEL"
APP_JS = Path.cwd() / "gui" / "static" / "app.js"

REMPLACEMENTS = [
    (r"""  corps.appendChild(alertesEl);
""", r"""  corps.appendChild(alertesEl);

  // PATCH_S27_VISUEL : frise des cinq étapes + cartes colorées selon l'état.
  const COULEURS = { 'fait': ['#27ae60', 'rgba(39,174,96,0.07)'],
                     'en cours': ['#2e86c1', 'rgba(46,134,193,0.10)'],
                     'à venir': ['#9aa5ad', 'transparent'] };
  const ETAPES_COURTES = ['Tester', 'Décider', 'Injecter', 'Appliquer', 'À la main'];
  const frise = mk('div');
  Object.assign(frise.style, { display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px',
                               margin: '12px 0 4px 0' });
  corps.appendChild(frise);
  function pastille(n, couleur, plein) {
    const p = mk('span', null, String(n));
    Object.assign(p.style, { display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      width: '26px', height: '26px', borderRadius: '50%', fontWeight: '700', fontSize: '0.95em',
      border: `2px solid ${couleur}`, background: plein ? couleur : 'transparent',
      color: plein ? '#fff' : couleur, flex: '0 0 auto', boxSizing: 'border-box' });
    return p;
  }
  function styliserEtape(b, etat) {
    const [c, fond] = COULEURS[etat];
    b.bloc.style.borderLeftColor = c;
    b.bloc.style.background = fond;
    b.bloc.style.boxShadow = etat === 'en cours' ? '0 2px 12px rgba(46,134,193,0.20)' : '';
    b.titre.textContent = '';
    b.titre.appendChild(pastille(b.n, c, etat !== 'à venir'));
    b.titre.appendChild(mk('span', null, b.nom));
    const etiq = mk('span', null, etat === 'fait' ? '✓ fait' : '▶ en cours');
    Object.assign(etiq.style, { marginLeft: 'auto', fontSize: '0.8em', fontWeight: '600', padding: '2px 10px',
                                borderRadius: '10px', color: '#fff', background: c });
    b.titre.appendChild(etiq);
  }
  function dessinerFrise(etape) {
    frise.textContent = '';
    if (!etape) return;
    ETAPES_COURTES.forEach((nom, i) => {
      const n = i + 1;
      const etat = n < etape ? 'fait' : (n === etape ? 'en cours' : 'à venir');
      const [c] = COULEURS[etat];
      const item = mk('span');
      Object.assign(item.style, { display: 'inline-flex', alignItems: 'center', gap: '5px',
                                  fontWeight: etat === 'en cours' ? '700' : '' });
      if (etat === 'à venir') item.style.color = c;
      item.appendChild(pastille(n, c, etat !== 'à venir'));
      item.appendChild(mk('span', null, nom));
      frise.appendChild(item);
      if (n < 5) {
        const trait = mk('span', null, '——');
        trait.style.color = n < etape ? COULEURS['fait'][0] : '#9aa5ad';
        frise.appendChild(trait);
      }
    });
  }
"""),
    (r"""    const bloc = mk('div');
    bloc.style.borderLeft = '3px solid #ccc';
    bloc.style.padding = '4px 0 4px 10px';
    bloc.style.margin = '10px 0';
    const titre = mk('div', 'option-label');
""", r"""    const bloc = mk('div');
    Object.assign(bloc.style, { border: '1px solid rgba(128,128,128,0.25)', borderLeft: '6px solid #ccc',
                                borderRadius: '8px', padding: '10px 14px', margin: '14px 0' });
    const titre = mk('div', 'option-label');
    Object.assign(titre.style, { display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.05em',
                                 fontWeight: '600', marginBottom: '6px' });
"""),
    (r"""      blocs.forEach(b => montrer(b.bloc, false));
      return;
""", r"""      blocs.forEach(b => montrer(b.bloc, false));
      dessinerFrise(0);
      return;
"""),
    (r"""      b.titre.textContent = `${'①②③④⑤'[b.n - 1]} ${b.nom} — ${etat === 'fait' ? '✓ fait' : '▶ en cours'}`;
      b.bloc.style.borderLeftColor = etat === 'en cours' ? '#2e86c1' : '#7dcea0';
    });
""", r"""      if (etat !== 'à venir') styliserEtape(b, etat);
    });
    dessinerFrise(e.etape);
"""),
    (r"""  function sousTitre(txt) {
    const t = mk('div', 'option-label', txt);
    t.style.marginTop = '10px';
    return t;
  }
""", r"""  function sousTitre(txt) {
    const ICONES = [['Nouvelles', '🧩'], ['Phrases', '✏️'], ['Règle', '📜'], ['Pour finir', '🏁']];
    const icone = (ICONES.find(([k]) => txt.startsWith(k)) || [null, ''])[1];
    const t = mk('div', 'option-label', (icone ? icone + '  ' : '') + txt);
    Object.assign(t.style, { marginTop: '18px', marginBottom: '8px', padding: '6px 10px', borderRadius: '6px',
                             background: 'rgba(128,128,128,0.14)', fontWeight: '600' });
    return t;
  }
"""),
    (r"""  const sortie = mk('pre');
  sortie.style.whiteSpace = 'pre-wrap';
  sortie.style.fontSize = '0.85em';
  sortie.style.marginTop = '6px';
  corps.appendChild(sortie);
""", r"""  const titreSortie = mk('div', 'option-label', '📋 Résultat du dernier bouton');
  Object.assign(titreSortie.style, { marginTop: '16px', fontWeight: '600' });
  corps.appendChild(titreSortie);
  const sortie = mk('pre');
  Object.assign(sortie.style, { whiteSpace: 'pre-wrap', fontSize: '0.85em', marginTop: '6px', padding: '10px 12px',
                                border: '1px solid rgba(128,128,128,0.3)', borderRadius: '6px', minHeight: '2em',
                                background: 'rgba(128,128,128,0.06)', maxHeight: '60vh', overflow: 'auto' });
  corps.appendChild(sortie);
"""),
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
    if "PATCH_S27_GUI_MAIN" not in js:
        sys.exit("✗ patch de l'étape ⑤ (PATCH_S27_GUI_MAIN) absent : rien fait.")
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
    print("  ✓ gui/static/app.js : présentation en cartes prête")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(APP_JS, APP_JS.with_name("app.js.bak_visuel"))
    APP_JS.write_text(js, encoding="utf-8")
    print("\n✓ Fait (sauvegarde app.js.bak_visuel). Recharger la page du GUI.")


if __name__ == "__main__":
    main()
