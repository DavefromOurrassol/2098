#!/usr/bin/env python3
"""
patch_s27_phrases.py -- étape ⑤ : phrases à corriger (18 octobre 2026)
=======================================================================
  gui/app.py         routes /api/et_si/main/phrases/proposer (IA) et
                     /api/et_si/main/phrase/<apercu|remplacer|ignorer>.
  gui/static/app.js  étape ⑤, section « Phrases à corriger » : bouton de relecture
                     de la fiche d'événement + propositions (IA), puis pour chaque
                     phrase : réécriture modifiable, Aperçu / Remplacer / Ignorer.

À placer avec la nouvelle version de generator/et_si_main.py (--phrases-proposer, --phrase).
Tout ou rien, sauvegardes .bak_phrases, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_phrases.py            (aperçu)
    python3 generator/patch_s27_phrases.py --apply
Puis redémarrer le GUI.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_PHRASES"
VAULT = Path.cwd()
R = {}

R["gui/app.py"] = [
    (
        '''TIMEOUTS_MAIN = {"etat": 120, "entites": 120, "regle": 60, "lancer": 900}''',
        '''TIMEOUTS_MAIN = {"etat": 120, "entites": 120, "regle": 60, "lancer": 900,
                 "phrases": 900, "phrase": 60}   # PATCH_S27_PHRASES''',
    ),
    (
        '''    elif quoi == "lancer" and action in ("audit", "resume") and re.match(r"^[a-z_]+$", sc):
        cmd += ["--lancer", action, "--scenario", sc]''',
        '''    elif quoi == "lancer" and action in ("audit", "resume") and re.match(r"^[a-z_]+$", sc):
        cmd += ["--lancer", action, "--scenario", sc]
    elif quoi == "phrases" and action == "proposer":   # PATCH_S27_PHRASES (appels IA)
        cmd.append("--phrases-proposer")
    elif (quoi == "phrase" and action in ("apercu", "remplacer", "ignorer")
          and re.match(r"^[a-z_]+:[A-Za-z0-9_]+:[0-9a-f]{8}$", str(data.get("cle") or ""))):
        cmd += ["--phrase", str(data["cle"])]
        cmd += ["--ignorer"] if action == "ignorer" else (["--apply"] if action == "remplacer" else [])
        entree = str(data.get("texte") or "")''',
    ),
]

JS_SECTION = r'''    // PATCH_S27_PHRASES : phrases à corriger (passe exhaustive + fiche d'événement relue par l'IA).
    zoneMain.appendChild(sousTitre('Phrases à corriger'));
    const phr = etat.phrases || [];
    const relue = (etat.evenement_verifie || []).length > 0;
    const bProp = bouton(relue ? 'Relire et proposer à nouveau (IA)'
                                : 'Vérifier la fiche d\'événement et proposer les réécritures (IA)');
    bProp.addEventListener('click', () => {
      if (!confirm('Appels IA (quelques centimes) : relecture de la fiche d\'événement, puis une proposition '
                   + 'par phrase sans proposition. Continuer ?')) return;
      appeler('main/phrases', 'proposer', {});
    });
    zoneMain.appendChild(bProp);
    tous.push(bProp);
    if (!phr.length) {
      zoneMain.appendChild(mk('div', 'option-desc', relue ? 'Aucune phrase à corriger.'
        : 'Aucune phrase relevée par la passe exhaustive ; la fiche d\'événement n\'a pas encore été relue.'));
    }
    phr.forEach(x => {
      const k = `${id}|${x.cle}`;
      const bloc = mk('div');
      bloc.style.margin = '6px 0';
      bloc.style.paddingLeft = '8px';
      bloc.style.borderLeft = '2px solid #ddd';
      const close = x.statut === 'corrigée' || x.statut === 'ignorée';
      const titre = mk('div', 'option-label', `${x.nom} — ${x.fichier}` + (x.statut ? `  [${x.statut}]` : ''));
      if (close) titre.style.color = '#1e8449';
      bloc.appendChild(titre);
      const av = mk('div', 'option-desc', `Phrase : « ${x.extrait} »\nContredit : ${x.contredit}`
        + (x.source === 'evenement' ? '\n(relevée par la relecture IA de la fiche d\'événement)' : ''));
      av.style.whiteSpace = 'pre-wrap';
      bloc.appendChild(av);
      if (x.statut === 'introuvable') {
        bloc.appendChild(mk('div', 'option-desc',
          'Phrase introuvable mot pour mot dans la fiche : à corriger à la main.'));
      } else if (!close) {
        const ta = mk('textarea');
        ta.rows = 3;
        ta.style.width = '100%';
        ta.placeholder = 'Réécriture : clique sur le bouton IA ci-dessus, ou écris la phrase toi-même';
        ta.value = (k in memo.texte) ? memo.texte[k] : (x.proposition || '');
        ta.addEventListener('input', () => { memo.texte[k] = ta.value; });
        bloc.appendChild(ta);
        const l = mk('div');
        const bA = bouton('Aperçu');
        const bR = bouton('Remplacer', 'yaml-btn yaml-btn-save');
        const bI = bouton('Ignorer');
        bA.addEventListener('click', () => appeler('main/phrase', 'apercu', { cle: x.cle, texte: ta.value }));
        bR.addEventListener('click', () => {
          if (!confirm(`Remplacer la phrase dans ${x.fichier} ? (sauvegarde .bak_et_si_main)`)) return;
          appeler('main/phrase', 'remplacer', { cle: x.cle, texte: ta.value });
        });
        bI.addEventListener('click', () => appeler('main/phrase', 'ignorer', { cle: x.cle }));
        [bA, bR, bI].forEach(b => { l.appendChild(b); tous.push(b); });
        bloc.appendChild(l);
      }
      zoneMain.appendChild(bloc);
    });

'''

R["gui/static/app.js"] = [
    ('''    // 2. Règle de lore
''', JS_SECTION + '''    // 2. Règle de lore
'''),
    (
        '''      'Phrases, articles et décisions ⚠ restent à faire avec la check-list.'));''',
        r'''      'Phrases : la relecture IA ajoute les phrases de la fiche d\'événement qui contredisent les faits ; ' +
      'chaque réécriture est modifiable, « Remplacer » l\'écrit dans la fiche (toutes ses occurrences, ' +
      'frontmatter et corps ; sauvegarde .bak_et_si_main). Seule la phrase change : relis la fiche si le ' +
      'reste du texte en dépend.\n' +
      'Articles et décisions ⚠ restent à faire avec la check-list.'));''',
    ),
]
PREREQUIS = {"gui/app.py": ["PATCH_S27_GUI_MAIN"], "gui/static/app.js": ["PATCH_S27_CATEGORIES"]}
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
    if not main_py.exists() or "def remplacer_phrase" not in main_py.read_text(encoding="utf-8"):
        sys.exit("✗ placer d'abord la nouvelle version de generator/et_si_main.py (phrases). Rien fait.")
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
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_phrases"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Phrases à corriger en place (sauvegardes .bak_phrases). Redémarrer le GUI.")


if __name__ == "__main__":
    main()
