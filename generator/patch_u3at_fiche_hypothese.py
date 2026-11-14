#!/usr/bin/env python3
"""
patch_u3at_fiche_hypothese.py — Ourrassol 2098 (14 novembre 2026)

Dans le mode « Simuler », la liste des hypothèses n'affiche que le nom. Le panneau
Parcours montre désormais, sous le statut, un encadré « 📄 Description de
l'hypothèse » (repliable) : nom, type, date, catégorie, scénarios, rôle, état et
description complète de l'hypothèse choisie. Lecture seule, aucun appel IA.

  generator/et_si_statut.py : le statut renvoie aussi la fiche de l'hypothèse ;
  gui/static/app.js        : encadré dans le panneau Parcours.

Après application : Cmd+Maj+R (pas de redémarrage de Flask : et_si_statut.py est relancé à chaque appel).

    python3 generator/patch_u3at_fiche_hypothese.py            # aperçu
    python3 generator/patch_u3at_fiche_hypothese.py --apply
Sauvegardes .bak_u3at ; refuse un second passage ; contrôles de syntaxe avec restauration.
"""
import argparse
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3at"
STATUT = Path("generator/et_si_statut.py")
APP_JS = Path("gui/static/app.js")

PY_REMPL = [
    (
        "fiche dans le statut",
        '        "id": hid, "type": typ, "statut": st, "etape": etape, "alertes": alertes,\n',
        '        "id": hid, "type": typ, "statut": st, "etape": etape, "alertes": alertes,\n'
        '        "hypothese": _fiche_u3at(hid),\n',
    ),
    (
        "fonction _fiche_u3at",
        "def etat(hid):\n",
        """def _fiche_u3at(hid):   # U3at : fiche lisible de l'hypothèse pour le GUI
    brut = ed.hypothese_brute(hid)
    if not isinstance(brut, dict):
        return None
    fiche = {}
    for k in ("nom", "type", "date", "mode", "categorie", "scenario_ref", "scenarios",
              "role", "etat", "description"):
        v = brut.get(k)
        if v in (None, "", []):
            continue
        fiche[k] = [str(x) for x in v] if isinstance(v, list) else (v if isinstance(v, (int, float)) else str(v))
    return fiche


def etat(hid):
""",
    ),
]

JS_REMPL = [
    (
        "encadré",
        "  corps.appendChild(ligneStatut);\n",
        r"""  corps.appendChild(ligneStatut);
  // U3at : fiche de l'hypothèse choisie (nom, description…), repliable
  const ficheEl = document.createElement('details');
  ficheEl.open = true;
  ficheEl.style.cssText = 'display:none;border:1px solid #d5dbe1;border-radius:6px;padding:6px 8px;margin:6px 0;';
  const ficheTitre = document.createElement('summary');
  ficheTitre.textContent = '📄 Description de l\'hypothèse';
  ficheTitre.style.cursor = 'pointer';
  const ficheMeta = mk('div', 'option-desc');
  ficheMeta.style.fontWeight = '600';
  const ficheCorps = mk('div', 'option-desc');
  ficheCorps.style.whiteSpace = 'pre-wrap';
  ficheEl.appendChild(ficheTitre);
  ficheEl.appendChild(ficheMeta);
  ficheEl.appendChild(ficheCorps);
  corps.appendChild(ficheEl);
""",
    ),
    (
        "masquer sans hypothèse",
        "      statutTxt.textContent = 'Choisis une hypothèse dans la liste ci-dessus.';\n      alertesEl.textContent = '';\n",
        "      statutTxt.textContent = 'Choisis une hypothèse dans la liste ci-dessus.';\n      alertesEl.textContent = '';\n"
        "      ficheEl.style.display = 'none';   // U3at\n",
    ),
    (
        "remplir la fiche",
        "    statutTxt.textContent = `Statut : ${e.statut}  `;\n",
        r"""    statutTxt.textContent = `Statut : ${e.statut}  `;
    const fi = e.hypothese;   // U3at
    if (fi) {
      const entete = [fi.nom, fi.type === 'entite' ? 'entité' : (fi.type || 'événement'),
                      fi.date != null ? `date ${fi.date}` : '', fi.mode ? `mode ${fi.mode}` : '',
                      fi.categorie ? `catégorie ${fi.categorie}` : '',
                      fi.scenario_ref ? `réf. ${fi.scenario_ref}` : '',
                      (fi.scenarios && fi.scenarios.length) ? `scénarios : ${[].concat(fi.scenarios).join(', ')}` : '']
        .filter(Boolean).join(' · ');
      ficheMeta.textContent = entete;
      ficheCorps.textContent = [fi.description, fi.role ? `Rôle : ${fi.role}` : '', fi.etat ? `État : ${fi.etat}` : '']
        .filter(Boolean).join('\n\n') || '(pas de description)';
      ficheEl.style.display = '';
    } else {
      ficheEl.style.display = 'none';
    }
""",
    ),
]


def _node_check(chemin):
    try:
        r = subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None, "node absent"
    return r.returncode == 0, r.stderr.strip()


def _premiere_erreur(msg):
    lignes = [l for l in msg.splitlines() if l.strip()]
    return " | ".join(l.strip() for l in lignes[:4] if "SyntaxError" in l or l.strip().startswith("("))[:300]


def verifier_js(chemin, original):
    """Ne bloque que sur une erreur NOUVELLE (un vieux node refuse déjà « ||= » dans l'original)."""
    ok, msg = _node_check(chemin)
    if ok:
        return True, "node --check OK"
    if ok is False:
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "original.js"
            copie.write_text(Path(original).read_text(encoding="utf-8"), encoding="utf-8")
            ok0, msg0 = _node_check(copie)
        if ok0 is False and _premiere_erreur(msg) == _premiere_erreur(msg0):
            return True, "node --check refuse une syntaxe déjà présente dans l'original : aucune erreur nouvelle"
        return False, msg[:400]
    t = chemin.read_text(encoding="utf-8")
    ok2 = t.count("{") == t.count("}") and t.count("(") == t.count(")")
    return ok2, "accolades/parenthèses équilibrées (node absent)" if ok2 else "accolades/parenthèses déséquilibrées"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--py", default=str(STATUT))
    ap.add_argument("--js", default=str(APP_JS))
    a = ap.parse_args()
    prepares = []
    for chemin, remp in ((Path(a.py), PY_REMPL), (Path(a.js), JS_REMPL)):
        if not chemin.exists():
            print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
            return 2
        texte = chemin.read_text(encoding="utf-8")
        if MARQUEUR in texte:
            print(f"✗ {MARQUEUR} déjà appliqué dans {chemin.name} — refus d'un second passage.")
            return 1
        nouveau = texte
        for libelle, ancre, rempl in remp:
            n = nouveau.count(ancre)
            if n != 1:
                print(f"✗ {chemin.name} : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
                return 1
            nouveau = nouveau.replace(ancre, rempl, 1)
            print(f"  ✓ {chemin.name} : {libelle}")
        prepares.append((chemin, texte, nouveau))
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, _, apres in prepares:
        bak = chemin.with_name(chemin.name + ".bak_u3at")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(apres, encoding="utf-8")

    def restaurer():
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)

    try:
        py_compile.compile(str(baks[0][0]), doraise=True)
    except py_compile.PyCompileError as e:
        restaurer()
        print(f"✗ py_compile a échoué, fichiers restaurés : {e}")
        return 1
    ok, msg = verifier_js(baks[1][0], baks[1][1])
    if not ok:
        restaurer()
        print(f"✗ Contrôle de syntaxe app.js échoué, fichiers restaurés : {msg}")
        return 1
    print(f"  (app.js : {msg})")
    for chemin, bak in baks:
        print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})")
    print("\nÀ faire : Cmd+Maj+R dans le navigateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
