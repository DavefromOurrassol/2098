#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unification « et si ? » — finitions des signaux (U2f).

  - inject_custom_signals.py : « selection » liste les variables réellement injectées ;
    l'IA ne cite plus de chiffre de force dans `contexte_injection`.
  - simuler_et_si.py : la « Liste d'application » d'un signal ne propose plus d'étapes
    d'événement (injection du signal + validate).
  - hypothese_depuis_texte.py + gui/app.py + gui/static/app.js : choix « Type : l'IA décide /
    Événement / Signal » dans « Nouvelle hypothèse » ; panneau Parcours : portée et intensité
    grisées pour un signal, libellés adaptés, pas d'étape ⑤ pour un signal.
Rien ne change pour un événement. Redémarrer Flask après application.

    python3 generator/patch_u2f_finitions.py            # dry-run
    python3 generator/patch_u2f_finitions.py --apply    # applique (.bak_u2f)
"""
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

G = Path("generator")
GUI = Path("gui")

LISTE_SIGNAL = '''    if hyp.get("type") == "signal":   # U2f : un signal n'a ni carte, ni zones, ni trajectoires
        E = []
        _etape(E, "Élément", f"Injecter le signal `{hyp['id']}` (entrée en fin de rapport)",
               "étape ③ « Injecter » du panneau (ou python3 generator/et_si_injecter.py --id " + hyp["id"] + ")",
               "un seul appel pour les 6 scénarios ; forces, sens et date de cette simulation sont imposés")
        _etape(E, "Contrôles", "Base", "python3 generator/validate.py")
        return {"etapes": E, "avert": [], "sources_ia": False, "fiches_citant": {},
                "nouvelles_entites": [], "acteurs": [], "faits": []}
    E = []
    cons = cons if cons and not cons.get("erreur") else {}
'''

# (fichier, ancre, remplacement)
EDITS = [
    # ---- simuler_et_si.py
    (G / "simuler_et_si.py",
     '    E = []\n    cons = cons if cons and not cons.get("erreur") else {}\n', LISTE_SIGNAL),
    # ---- inject_custom_signals.py
    (G / "inject_custom_signals.py",
     '            variables = list(imp["par_var"])\n',
     '            variables = list(imp["par_var"])\n'
     '            selection["variables"] = list(variables)\n'),
    (G / "inject_custom_signals.py",
     '    return "\\n".join(lignes) + "\\n"\n',
     '    lignes.append("Dans `contexte_injection`, n\'écris AUCUN chiffre de force ni de polarité "\n'
     '                  "(+5, -1, niveau…) : ils sont fixés ailleurs ; décris seulement le mécanisme.")\n'
     '    return "\\n".join(lignes) + "\\n"\n'),
    # ---- hypothese_depuis_texte.py
    (G / "hypothese_depuis_texte.py",
     'def construire_prompt(texte, variables):\n',
     'def construire_prompt(texte, variables, type_force=None):\n'),
    (G / "hypothese_depuis_texte.py",
     '    return f"""Tu aides l\'auteur du monde fictif',
     '    ligne_type = (f"TYPE IMPOSÉ PAR L\'AUTEUR : {type_force} (ne le change pas).\\n\\n"\n'
     '                  if type_force else "")\n'
     '    return f"""{ligne_type}Tu aides l\'auteur du monde fictif'),
    (G / "hypothese_depuis_texte.py",
     'def proposer(texte, _llm=appeler_llm):\n',
     'def proposer(texte, _llm=appeler_llm, type_force=None):\n'),
    (G / "hypothese_depuis_texte.py",
     '    brut = _llm(construire_prompt(texte, variables))\n',
     '    brut = _llm(construire_prompt(texte, variables, type_force))\n'),
    (G / "hypothese_depuis_texte.py",
     '        raise ValueError("réponse de l\'IA inexploitable")\n',
     '        raise ValueError("réponse de l\'IA inexploitable")\n'
     '    if type_force in ("evenement", "signal"):\n'
     '        brut["type"] = type_force   # le choix de l\'auteur l\'emporte sur celui de l\'IA\n'),
    (G / "hypothese_depuis_texte.py",
     '    ap.add_argument("--json", action="store_true", help="sortie JSON sur une ligne (GUI)")\n',
     '    ap.add_argument("--json", action="store_true", help="sortie JSON sur une ligne (GUI)")\n'
     '    ap.add_argument("--type", choices=("evenement", "signal"), default=None,\n'
     '                    help="avec --proposer : impose le type (sinon l\'IA décide)")\n'),
    (G / "hypothese_depuis_texte.py",
     '            res = proposer(texte)\n',
     '            res = proposer(texte, type_force=args.type)\n'),
    # ---- gui/app.py
    (GUI / "app.py",
     '    cmd = [sys.executable, "hypothese_depuis_texte.py", f"--{action}", "--json"]\n',
     '    cmd = [sys.executable, "hypothese_depuis_texte.py", f"--{action}", "--json"]\n'
     '    if action == "proposer" and data.get("type") in ("evenement", "signal"):   # U2f\n'
     '        cmd += ["--type", data["type"]]\n'),
    # ---- gui/static/app.js
    (GUI / "static" / "app.js",
     "  corps.appendChild(btnProposer);\n\n  const retour = mk('div', 'option-desc');\n",
     "  corps.appendChild(btnProposer);\n"
     "  // U2f : type imposé (l'IA décide si vide)\n"
     "  const selType = document.createElement('select');\n"
     "  selType.style.marginLeft = '8px';\n"
     "  [['', 'Type : l\\'IA décide'], ['evenement', 'Événement'], ['signal', 'Signal']].forEach(([v, t]) => {\n"
     "    const o = document.createElement('option'); o.value = v; o.textContent = t; selType.appendChild(o);\n"
     "  });\n"
     "  corps.appendChild(selType);\n\n  const retour = mk('div', 'option-desc');\n"),
    (GUI / "static" / "app.js",
     "        body: JSON.stringify({ texte }),\n",
     "        body: JSON.stringify({ texte, type: action === 'proposer' ? selType.value : '' }),\n"),
    (GUI / "static" / "app.js",
     "  // Affichage selon l'état\n  const afficher = (e) => {\n",
     "  let typeCourant = 'evenement';   // U2f\n  // Affichage selon l'état\n  const afficher = (e) => {\n"),
    (GUI / "static" / "app.js",
     "    statutTxt.textContent = `Statut : ${e.statut}  `;\n",
     "    typeCourant = e.type || 'evenement';   // U2f\n    statutTxt.textContent = `Statut : ${e.statut}  `;\n"),
    (GUI / "static" / "app.js",
     "    montrer(zoneAdopter, e.etape === 2);\n",
     "    montrer(zoneAdopter, e.etape === 2);\n"
     "    // U2f : portée et intensité sont sans objet pour un signal\n"
     "    [portee, intensite].forEach(x => {\n"
     "      x.disabled = typeCourant === 'signal';\n"
     "      x.title = typeCourant === 'signal' ? 'Sans objet pour un signal' : '';\n"
     "      x.style.opacity = typeCourant === 'signal' ? '0.45' : '';\n"
     "    });\n"),
    (GUI / "static" / "app.js",
     "    resumeInj.textContent = e.etape > 3 ? 'Événement injecté dans le vault.' :\n",
     "    resumeInj.textContent = e.etape > 3 ? (typeCourant === 'signal' ? 'Signal injecté dans le vault. Rien à appliquer : parcours terminé.' : 'Événement injecté dans le vault.') :\n"),
    (GUI / "static" / "app.js",
     "      if (data.etape >= 5) chargerMain(); else viderMain();   // PATCH_S27_GUI_MAIN\n",
     "      if (data.etape >= 5 && data.type !== 'signal') chargerMain(); else viderMain();   // PATCH_S27_GUI_MAIN (U2f : pas d'étape ⑤ pour un signal)\n"),
    (GUI / "static" / "app.js",
     "    if (!confirm('Adopter : placer l\\'événement simulé dans la file d\\'injection ?')) return;\n",
     "    if (!confirm(typeCourant === 'signal' ? 'Adopter : placer le signal simulé dans la file d\\'injection des signaux ?' : 'Adopter : placer l\\'événement simulé dans la file d\\'injection ?')) return;\n"),
    (GUI / "static" / "app.js",
     "    if (!confirm('Injecter cet événement dans le vault ? (appels IA ; plusieurs minutes)')) return;\n",
     "    if (!confirm((typeCourant === 'signal' ? 'Injecter ce signal' : 'Injecter cet événement') + ' dans le vault ? (appels IA ; plusieurs minutes)')) return;\n"),
]


def appliquer():
    fichiers = {}
    for f, _, _ in EDITS:
        fichiers.setdefault(f, None)
    for f in fichiers:
        if not f.is_file():
            print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(f))
            return None
        fichiers[f] = f.read_text(encoding="utf-8")
    if "U2f" in fichiers[G / "simuler_et_si.py"] or "type_force" in fichiers[G / "hypothese_depuis_texte.py"]:
        print("Déjà appliqué : rien à faire.")
        return {}
    for fonction, requis in ((G / "inject_custom_signals.py", "lire_impositions_signal"),
                             (G / "simuler_et_si.py", "DELTA_MAX_SIGNAL"),
                             (G / "hypothese_depuis_texte.py", "SIGNAL_FORCE_MAX"),
                             (G / "et_si_statut.py", "type_dossier")):
        if requis not in fonction.read_text(encoding="utf-8"):
            print("ERREUR : {} ne contient pas {} : appliquer d'abord les patchs précédents.".format(fonction, requis))
            return None
    for i, (f, ancre, _) in enumerate(EDITS, 1):
        n = fichiers[f].count(ancre)
        if n != 1:
            print("ERREUR : ancre n°{} ({}) trouvée {} fois (attendu : 1). Rien modifié.".format(i, f.name, n))
            return None
    for f, ancre, rempl in EDITS:
        fichiers[f] = fichiers[f].replace(ancre, rempl)
    return fichiers


def main():
    nouveaux = appliquer()
    if nouveaux is None:
        return 1
    if nouveaux == {}:
        return 0
    print("{} modifications prévues dans {} fichiers.".format(len(EDITS), len(nouveaux)))
    if "--apply" not in sys.argv:
        print("Dry-run : rien écrit. Relancer avec --apply pour appliquer.")
        return 0
    for f, txt in nouveaux.items():
        shutil.copy2(f, str(f) + ".bak_u2f")
        f.write_text(txt, encoding="utf-8")
    try:
        for f in nouveaux:
            if f.suffix == ".py":
                py_compile.compile(str(f), doraise=True)
    except py_compile.PyCompileError as e:
        for f in nouveaux:
            shutil.copy2(str(f) + ".bak_u2f", f)
        print("ERREUR de syntaxe, fichiers restaurés :\n{}".format(e))
        return 1
    js = GUI / "static" / "app.js"

    def node_ok(chemin):
        r = subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True, timeout=60)
        return r.returncode == 0, r.stderr[-800:]

    try:
        ok_apres, err = node_ok(js)
        if not ok_apres:
            ok_avant, _ = node_ok(Path(str(js) + ".bak_u2f"))
            if ok_avant:   # mon patch casse le JavaScript : retour arrière
                for f in nouveaux:
                    shutil.copy2(str(f) + ".bak_u2f", f)
                print("ERREUR de syntaxe JavaScript, fichiers restaurés :\n{}".format(err))
                return 1
            print("· node (ancienne version) ne comprend pas une syntaxe déjà présente dans app.js "
                  "avant ce patch : contrôle JavaScript non concluant, relire l'interface après redémarrage.")
        else:
            print("Syntaxe JavaScript vérifiée (node).")
    except (OSError, subprocess.TimeoutExpired):
        print("· node absent : syntaxe JavaScript non vérifiée (relire l'interface après redémarrage).")
    print("Appliqué (sauvegardes .bak_u2f). Syntaxe Python vérifiée. Redémarrer Flask.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
