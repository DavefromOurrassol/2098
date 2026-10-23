#!/usr/bin/env python3
"""
patch_s27_articles.py -- étape ⑤ : articles à relire (18 octobre 2026)
=======================================================================
  gui/app.py         routes /api/et_si/main/articles/verifier (IA, lecture seule) et
                     /api/et_si/main/article/relu.
  gui/static/app.js  étape ⑤, partie « 📰 Articles à relire » : articles qui citent une
                     entité touchée (ou dont la zone a changé), passages relevés par l'IA
                     (phrase, fait contredit, suggestion), « Ouvrir dans Obsidian ↗ »,
                     « Marquer comme relu ». Aucun article n'est jamais modifié par l'outil.
                     Titres des phrases et des articles en écriture normale.

À placer avec la nouvelle version de generator/et_si_main.py (--articles-verifier).
Tout ou rien, sauvegardes .bak_articles, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_articles.py            (aperçu)
    python3 generator/patch_s27_articles.py --apply
Puis redémarrer le GUI.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_ARTICLES"
VAULT = Path.cwd()
R = {}

R["gui/app.py"] = [
    (
        '''                 "phrases": 900, "phrase": 60}   # PATCH_S27_PHRASES''',
        '''                 "phrases": 900, "phrase": 60,   # PATCH_S27_PHRASES
                 "articles": 1500, "article": 60}   # PATCH_S27_ARTICLES''',
    ),
    (
        '''    else:
        return jsonify({"error": f"demande inconnue : {quoi}/{action}"}), 404''',
        '''    elif quoi == "articles" and action == "verifier":   # PATCH_S27_ARTICLES (appels IA, lecture seule)
        cmd.append("--articles-verifier")
    elif (quoi == "article" and action == "relu" and ".." not in str(data.get("chemin") or "")
          and re.match(r"^articles/\\S+\\.md$", str(data.get("chemin") or ""))):
        cmd += ["--article-relu", str(data["chemin"])]
    else:
        return jsonify({"error": f"demande inconnue : {quoi}/{action}"}), 404''',
    ),
]

JS_SECTION = r'''    // PATCH_S27_ARTICLES : articles à relire -- repérage par l'IA, jamais d'écriture dans un article.
    zoneMain.appendChild(sousTitre('Articles à relire'));
    const arts = etat.articles || [];
    const titreNormal = (el) => Object.assign(el.style, { textTransform: 'none', letterSpacing: 'normal',
                                                          fontSize: '12px', color: 'var(--text)' });
    if (!arts.length) {
      zoneMain.appendChild(mk('div', 'option-desc',
        'Aucun article ne cite une entité touchée ni n\'a pour zone une zone changée.'));
    } else {
      const neufs = arts.filter(a => !a.verifie).length;
      const bV = bouton(neufs ? `Relire ${neufs} article(s) avec l'IA` : 'Relire à nouveau avec l\'IA');
      bV.addEventListener('click', () => {
        if (!confirm('Appels IA (quelques centimes par article) : repérage seulement, aucun article n\'est '
                     + 'modifié. Continuer ?')) return;
        appeler('main/articles', 'verifier', {});
      });
      zoneMain.appendChild(bV);
      tous.push(bV);
    }
    arts.forEach(a => {
      const bloc = mk('div');
      Object.assign(bloc.style, { margin: '6px 0', paddingLeft: '8px', borderLeft: '2px solid #ddd' });
      const titre = mk('div', 'option-label', `${a.titre}${a.date ? ' — ' + a.date : ''}` + (a.relu ? '  [relu]' : ''));
      titreNormal(titre);
      if (a.relu) titre.style.color = '#1e8449';
      bloc.appendChild(titre);
      const n = (a.passages || []).length;
      const info = mk('div', 'option-desc', `${a.chemin} (${(a.motifs || []).join(', ')})\n`
        + (!a.verifie ? 'Pas encore relu par l\'IA.'
           : (n ? `${n} passage(s) à revoir :` : 'Aucun passage contradictoire relevé par l\'IA.')));
      info.style.whiteSpace = 'pre-wrap';
      bloc.appendChild(info);
      (a.passages || []).forEach(p => {
        const d = mk('div', 'option-desc', `« ${p.extrait} »\nContredit : ${p.fait}`
          + (p.suggestion ? `\nSuggestion : ${p.suggestion}` : ''));
        Object.assign(d.style, { whiteSpace: 'pre-wrap', margin: '4px 0 4px 12px', paddingLeft: '8px',
                                 borderLeft: '2px solid #e0a040' });
        bloc.appendChild(d);
      });
      const l = mk('div');
      const bO = bouton('Ouvrir dans Obsidian ↗');
      bO.addEventListener('click', () => _panneauOuvrirDansObsidian(a.chemin));
      l.appendChild(bO);
      if (!a.relu) {
        const bR = bouton('Marquer comme relu');
        bR.addEventListener('click', () => appeler('main/article', 'relu', { chemin: a.chemin }));
        l.appendChild(bR);
        tous.push(bR);
      }
      bloc.appendChild(l);
      zoneMain.appendChild(bloc);
    });

'''

R["gui/static/app.js"] = [
    ('''    // 2. Règle de lore
''', JS_SECTION + '''    // 2. Règle de lore
'''),
    (
        '''    const ICONES = [['Nouvelles', '🧩'], ['Phrases', '✏️'], ['Règle', '📜'], ['Pour finir', '🏁']];''',
        '''    const ICONES = [['Nouvelles', '🧩'], ['Phrases', '✏️'], ['Articles', '📰'], ['Règle', '📜'],
                    ['Pour finir', '🏁']];''',
    ),
    (
        '''      const titre = mk('div', 'option-label', `${x.nom} — ${x.fichier}` + (x.statut ? `  [${x.statut}]` : ''));''',
        '''      const titre = mk('div', 'option-label', `${x.nom} — ${x.fichier}` + (x.statut ? `  [${x.statut}]` : ''));
      Object.assign(titre.style, { textTransform: 'none', letterSpacing: 'normal', fontSize: '12px',
                                   color: 'var(--text)' });   // PATCH_S27_ARTICLES''',
    ),
]
PREREQUIS = {"gui/app.py": ["PATCH_S27_PHRASES"], "gui/static/app.js": ["PATCH_S27_PHRASES", "PATCH_S27_VISUEL"]}
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
    if not main_py.exists() or "def verifier_articles" not in main_py.read_text(encoding="utf-8"):
        sys.exit("✗ placer d'abord la nouvelle version de generator/et_si_main.py (articles). Rien fait.")
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
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_articles"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Articles à relire en place (sauvegardes .bak_articles). Redémarrer le GUI.")


if __name__ == "__main__":
    main()
