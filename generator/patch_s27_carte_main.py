#!/usr/bin/env python3
"""
patch_s27_carte_main.py -- étape ⑤ : partie « 🗺️ Carte » du panneau (18 octobre 2026)
=====================================================================================
  gui/app.py         routes /api/et_si/main/carte/{apercu,deplacer,laisser} ;
                     « Contrôle de la géographie » accepté dans « Pour finir ».
  gui/static/app.js  étape ⑤, partie « 🗺️ Carte » (en tête) : pour chaque changement de
                     carte appliqué, les sous-zones à plusieurs pays qui ont perdu le pays
                     (« La laisser ainsi », « Aperçu du déplacement », « La déplacer sous… »,
                     « Tracer une portion ↗ » = onglet Carte), les zones vidées, la nouvelle
                     zone (description et relations dans Obsidian, rédactions, continent).

À placer avec la nouvelle version de generator/et_si_main.py (--carte-deplacer) ; demande
patch_s27_carte.py déjà appliqué. Tout ou rien, sauvegardes .bak_carte_main, refuse un
second passage. Usage, depuis la racine du coffre :
    python3 generator/patch_s27_carte_main.py            (aperçu)
    python3 generator/patch_s27_carte_main.py --apply
Puis redémarrer le GUI.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_CARTE_MAIN"
VAULT = Path.cwd()
R = {}

R["gui/app.py"] = [
    (
        '''                 "articles": 1500, "article": 60}   # PATCH_S27_ARTICLES''',
        '''                 "articles": 1500, "article": 60,   # PATCH_S27_ARTICLES
                 "carte": 120}   # PATCH_S27_CARTE_MAIN''',
    ),
    (
        '''    elif quoi == "lancer" and action in ("audit", "resume") and re.match(r"^[a-z_]+$", sc):''',
        '''    elif quoi == "lancer" and action in ("audit", "resume", "geo") and re.match(r"^[a-z_]+$", sc):''',
    ),
    (
        '''    elif quoi == "articles" and action == "verifier":   # PATCH_S27_ARTICLES (appels IA, lecture seule)''',
        '''    elif (quoi == "carte" and action in ("apercu", "deplacer", "laisser")   # PATCH_S27_CARTE_MAIN
          and re.match(r"^[a-z_]+:[a-z0-9_]+$", str(data.get("cle") or ""))):
        cle = str(data["cle"])
        cmd += ["--carte-laisser", cle] if action == "laisser" else (
            ["--carte-deplacer", cle] + (["--apply"] if action == "deplacer" else []))
    elif quoi == "articles" and action == "verifier":   # PATCH_S27_ARTICLES (appels IA, lecture seule)''',
    ),
]

JS_SECTION = r'''    // PATCH_S27_CARTE_MAIN : suites de la carte appliquée (étape ④).
    const cartes = etat.carte || [];
    if (cartes.length) {
      zoneMain.appendChild(sousTitre('Carte'));
      const normal = (el) => Object.assign(el.style, { textTransform: 'none', letterSpacing: 'normal',
                                                       fontSize: '12px', color: 'var(--text)' });
      const ouvrirCarte = (sc) => {
        showTab('carte');
        const s = document.getElementById('carte-scenario');
        if (s && s.value !== sc && [...s.options].some(o => o.value === sc)) {
          s.value = sc;
          s.dispatchEvent(new Event('change'));
        }
      };
      const ETATS = {
        a_decider: ['⚠ à décider', '#b9770e'], laissee: ['✓ laissée ainsi', '#1e8449'],
        deplacee: ['✓ déplacée', '#1e8449'], portion: ['✓ garde une portion (tracé)', '#1e8449'],
        disparue: ['· n\'existe plus', '#888'], gardee: ['✓ gardée', '#1e8449'],
        territoire: ['✓ a de nouveau un territoire', '#1e8449'], supprimee: ['· supprimée', '#888'],
        en_attente: ['· carte pas encore appliquée', '#888'],
      };
      cartes.forEach(c => {
        const bloc = mk('div');
        Object.assign(bloc.style, { margin: '6px 0', paddingLeft: '8px', borderLeft: '2px solid #ddd' });
        const titre = mk('div', 'option-label', c.manuel
          ? `${c.pays} : ${c.action} (tracés) — ${c.sc}`
          : (c.nouvelle ? `Nouvelle zone ${c.nom_cible} (${c.cible}) avec ${c.pays}`
                        : `${c.pays} rattaché à ${c.nom_cible} (${c.cible})`) + ` — ${c.sc}`
            + (c.applique ? '  [appliqué]' : ''));
        normal(titre);
        if (c.applique) titre.style.color = '#1e8449';
        bloc.appendChild(titre);
        if (c.manuel || !c.applique) {
          bloc.appendChild(mk('div', 'option-desc', c.manuel
            ? 'À faire dans l\'onglet Carte, d\'après la liste d\'application du rapport.'
            : 'Pas encore appliqué : étape ④ « Appliquer ».'));
          if (c.manuel) {
            const bC = bouton('Ouvrir la Carte ↗');
            bC.addEventListener('click', () => ouvrirCarte(c.sc));
            bloc.appendChild(bC);
          }
          zoneMain.appendChild(bloc);
          return;
        }
        const ligneZone = (z, texte, actions) => {
          const d = mk('div');
          Object.assign(d.style, { margin: '6px 0 6px 8px' });
          const [lib, coul] = ETATS[z.etat] || [z.etat, '#888'];
          d.appendChild(mk('div', 'option-desc', texte));
          const e = mk('div', 'option-desc', lib);
          Object.assign(e.style, { color: coul, fontWeight: '600' });
          d.appendChild(e);
          if (z.etat === 'a_decider') {
            const l = mk('div');
            actions.forEach(([txt, fn, cls]) => {
              const b = bouton(txt, cls);
              b.addEventListener('click', fn);
              l.appendChild(b);
              tous.push(b);
            });
            d.appendChild(l);
          }
          return d;
        };
        (c.sous_zones || []).forEach(z => {
          bloc.appendChild(ligneZone(z,
            `Sous-zone ${z.nom} (${z.slug}) : porte aussi ${(z.autres || []).join(', ')}, a perdu ${c.pays}.`,
            [['La laisser ainsi', () => appeler('main/carte', 'laisser', { cle: z.cle })],
             [`Aperçu : la déplacer sous ${c.cible}`, () => appeler('main/carte', 'apercu', { cle: z.cle })],
             [`La déplacer sous ${c.cible}`, () => {
               if (!confirm(`Déplacer ${z.slug} (et ses ${(z.autres || []).join(', ')}) sous ${c.cible} ? `
                            + '(sauvegarde .bak_et_si_main)')) return;
               appeler('main/carte', 'deplacer', { cle: z.cle });
             }, 'yaml-btn yaml-btn-save'],
             ['Tracer une portion ↗', () => ouvrirCarte(c.sc)]]));
        });
        (c.videes || []).forEach(z => {
          bloc.appendChild(ligneZone(z, `Zone ${z.nom} (${z.slug}) : n'a plus aucun territoire.`,
            [['La garder (vestige, exil)', () => appeler('main/carte', 'laisser', { cle: z.cle })],
             ['La supprimer : onglet Carte ↗', () => ouvrirCarte(c.sc)]]));
        });
        if (c.nouvelle) {
          const n = mk('div', 'option-desc',
            `Nouvelle zone : description et relations (alliés / rivaux) à écrire dans geographie/${c.sc}.md.\n`
            + `Rédactions (payant) : python3 generator/generate_journaux.py --scenario ${c.sc} --update\n`
            + 'Continent sur le site : python3 generator/export_revues.py --continents');
          Object.assign(n.style, { whiteSpace: 'pre-wrap', margin: '6px 0 4px 8px' });
          bloc.appendChild(n);
          const l = mk('div');
          const bO = bouton(`Ouvrir geographie/${c.sc}.md dans Obsidian ↗`);
          bO.addEventListener('click', () => _panneauOuvrirDansObsidian(`geographie/${c.sc}.md`));
          const bC = bouton('Ouvrir la Carte ↗');
          bC.addEventListener('click', () => ouvrirCarte(c.sc));
          l.appendChild(bO);
          l.appendChild(bC);
          bloc.appendChild(l);
        }
        zoneMain.appendChild(bloc);
      });
    }

'''

R["gui/static/app.js"] = [
    ('''    // 1. Nouvelles entités
''', JS_SECTION + '''    // 1. Nouvelles entités
'''),
    (
        '''    const ICONES = [['Nouvelles', '🧩'], ['Phrases', '✏️'], ['Articles', '📰'], ['Règle', '📜'],
                    ['Pour finir', '🏁']];''',
        '''    const ICONES = [['Carte', '🗺️'], ['Nouvelles', '🧩'], ['Phrases', '✏️'], ['Articles', '📰'],
                    ['Règle', '📜'], ['Pour finir', '🏁']];   // PATCH_S27_CARTE_MAIN''',
    ),
    (
        '''      'Articles et décisions ⚠ restent à faire avec la check-list.'));''',
        r'''      'Carte : une sous-zone qui porte aussi d\'autres pays a perdu le pays ; la laisser ainsi, la ' +
      'déplacer entière sous la zone cible (ses autres pays la suivent ; aperçu d\'abord), ou lui rendre ' +
      'une portion par un tracé dans l\'onglet Carte (l\'état se met à jour à l\'actualisation).\n' +
      'Articles et décisions ⚠ restent à faire avec la check-list.'));''',
    ),
]
PREREQUIS = {"gui/app.py": ["PATCH_S27_ARTICLES"], "gui/static/app.js": ["PATCH_S27_ARTICLES", "PATCH_S27_VISUEL"]}
DEBUT_PANNEAU = "// PATCH_S27_GUI_PARCOURS — PANNEAU"
FIN_PANNEAU = "// PATCH_GUI_OBSIDIAN_PANNEAUX"


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
    main_py = VAULT / "generator" / "et_si_main.py"
    if not main_py.exists() or "def carte_deplacer" not in main_py.read_text(encoding="utf-8"):
        sys.exit("✗ placer d'abord la nouvelle version de generator/et_si_main.py (carte). Rien fait.")
    app_py = VAULT / "generator" / "appliquer_et_si.py"
    if not app_py.exists() or "PATCH_S27_CARTE" not in app_py.read_text(encoding="utf-8"):
        sys.exit("✗ appliquer d'abord patch_s27_carte.py. Rien fait.")
    nouveaux, erreurs = {}, []
    for nom, reps in R.items():
        chemin = VAULT / nom
        if not chemin.exists():
            erreurs.append(f"{nom} : introuvable (lancer depuis la racine du coffre)")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if MARQUEUR in texte:
            erreurs.append(f"{nom} : déjà patché ({MARQUEUR} présent)")
            continue
        for p in PREREQUIS.get(nom, []):
            if p not in texte:
                erreurs.append(f"{nom} : « {p} » absent (patch précédent non appliqué ?)")
        for n, (ancien, neuf) in enumerate(reps, 1):
            nb = texte.count(ancien)
            if nb != 1:
                erreurs.append(f"{nom} : repère n°{n} trouvé {nb} fois (attendu 1)")
                continue
            texte = texte.replace(ancien, neuf)
        if nom.endswith(".py"):
            try:
                compile(texte, str(chemin), "exec")
            except SyntaxError as e:
                erreurs.append(f"{nom} : erreur de syntaxe après patch ({e})")
        else:
            err = controle_js(texte)
            if err:
                erreurs.append(f"{nom} : JavaScript invalide après patch : {err}")
        nouveaux[nom] = texte
    if erreurs:
        print("✗ Rien n'a été écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
        sys.exit(1)
    for nom in R:
        print(f"  ✓ {nom} : {len(R[nom])} remplacement(s) prêt(s)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    for nom, texte in nouveaux.items():
        chemin = VAULT / nom
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_carte_main"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Partie « Carte » de l'étape ⑤ en place (sauvegardes .bak_carte_main). Redémarrer le GUI.")


if __name__ == "__main__":
    main()
