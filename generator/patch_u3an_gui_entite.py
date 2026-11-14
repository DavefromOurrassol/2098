#!/usr/bin/env python3
"""
patch_u3an_gui_entite.py — Ourrassol 2098 (14 novembre 2026)

Patch 4/4 du type « entité » dans « Et si ? » : le panneau du GUI.
Prérequis : U3aj à U3al (scripts). Deux fichiers :

  gui/app.py
    1. /api/et_si/proposer accepte le type « entite » (transmis à
       hypothese_depuis_texte.py --type entite).
  gui/static/app.js
    2. « Nouvelle hypothèse » : le sélecteur de type propose « Entité ».
    3. « Parcours de l'hypothèse » pour une entité : frise en 3 étapes
       (Vérifier · Décider · Injecter) ; l'étape ① Tester, ④ et ⑤ sont masquées ;
       portée/intensité et options payantes de simulation grisées ; la ligne
       « Sauter / Inclure / Liste de l'étape ④ » est masquée ; textes adaptés
       (« Simuler l'injection » = vrais appels IA sans rien écrire) ; l'étape ⑤
       (et_si_main.py) n'est pas chargée.

Après application : redémarrer Flask (app.py) puis Cmd+Maj+R (app.js).
Hors périmètre : le rattachement des entités proposées par la « Lecture IA »
(étape ⑤ des événements) reste inchangé.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3an_gui_entite.py            # aperçu
    python3 generator/patch_u3an_gui_entite.py --apply    # écrit

Sauvegarde .bak_u3an ; refuse un second passage ; contrôle de syntaxe de
app.py (py_compile) et de app.js (node --check ; une erreur déjà présente dans
l'original, ex. « ||= » avec un node ancien, ne bloque pas ; sans node : équilibre des accolades) ; restauration en cas d'échec.
"""
import argparse
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

MARQUEUR = "U3an"
APP_PY = Path("gui/app.py")
APP_JS = Path("gui/static/app.js")

PY_REMPL = [(
    "type entite accepté par /api/et_si/proposer",
    '    if action == "proposer" and data.get("type") in ("evenement", "signal"):   # U2f\n',
    '    if action == "proposer" and data.get("type") in ("evenement", "signal", "entite"):   # U2f / U3an\n',
)]

JS_REMPL = [
    ("sélecteur de type",
     "[['', 'Type : l\\'IA décide'], ['evenement', 'Événement'], ['signal', 'Signal']]",
     "[['', 'Type : l\\'IA décide'], ['evenement', 'Événement'], ['signal', 'Signal'], ['entite', 'Entité']]"),

    ("frise : 3 étapes nommées pour une entité",
     "    const nbEtapes = typeCourant === 'signal' ? 3 : ETAPES_COURTES.length;   // U3af : un signal s'arrête à ③\n"
     "    ETAPES_COURTES.slice(0, nbEtapes).forEach((nom, i) => {\n",
     "    const nbEtapes = (typeCourant === 'signal' || typeCourant === 'entite') ? 3 : ETAPES_COURTES.length;   // U3af : un signal s'arrête à ③ ; U3an : une entité aussi\n"
     "    const nomsFrise = typeCourant === 'entite' ? ['Vérifier', 'Décider', 'Injecter'] : ETAPES_COURTES;   // U3an\n"
     "    nomsFrise.slice(0, nbEtapes).forEach((nom, i) => {\n"),

    ("blocs d'étapes masqués",
     "      const sansObjet = typeCourant === 'signal' && b.n > 3;   // U3af : un signal s'arrête à ③\n",
     "      const sansObjet = (typeCourant === 'signal' && b.n > 3)   // U3af : un signal s'arrête à ③\n"
     "        || (typeCourant === 'entite' && (b.n > 3 || b.n === 1));   // U3an : une entité n'a ni ① Tester, ni ④, ni ⑤\n"),

    ("options de simulation grisées",
     "    griserSignal(typeCourant === 'signal');   // U3af\n    dessinerFrise(e.etape);\n",
     "    griserSignal(typeCourant === 'signal' || typeCourant === 'entite');   // U3af / U3an\n    dessinerFrise(e.etape);\n"),

    ("portée / intensité sans objet",
     "    [portee, intensite].forEach(x => {\n"
     "      x.disabled = typeCourant === 'signal';\n"
     "      x.title = typeCourant === 'signal' ? 'Sans objet pour un signal' : '';\n"
     "      x.style.opacity = typeCourant === 'signal' ? '0.45' : '';\n"
     "    });\n",
     "    const sansPI = typeCourant === 'signal' || typeCourant === 'entite';   // U3an\n"
     "    [portee, intensite].forEach(x => {\n"
     "      x.disabled = sansPI;\n"
     "      x.title = sansPI ? 'Sans objet pour ' + (typeCourant === 'entite' ? 'une entité' : 'un signal') : '';\n"
     "      x.style.opacity = sansPI ? '0.45' : '';\n"
     "    });\n"
     "    montrer(ligneTri3, typeCourant !== 'entite');   // U3an : pas de liste ④ pour une entité\n"),

    ("textes de l'étape ③",
     "    resumeInj.textContent = e.etape > 3 ? (typeCourant === 'signal' ? 'Signal injecté dans le vault. Rien à appliquer : parcours terminé.' : 'Événement injecté dans le vault.') :\n"
     "      (e.statut === 'adopté, en attente d\\'injection' ? 'En attente dans la file d\\'injection.' : '');\n",
     "    resumeInj.textContent = e.etape > 3 ? (typeCourant === 'signal' ? 'Signal injecté dans le vault. Rien à appliquer : parcours terminé.'\n"
     "        : (typeCourant === 'entite' ? 'Entité injectée dans le vault (fiche et instances). Rien à appliquer : parcours terminé.' : 'Événement injecté dans le vault.')) :\n"
     "      (e.statut === 'adopté, en attente d\\'injection'\n"
     "        ? (typeCourant === 'entite'\n"
     "          ? 'Entité adoptée, prête à injecter (aucune file). « Simuler l\\'injection » fait de vrais appels IA (un par scénario, plusieurs minutes) sans rien écrire ; « Injecter » crée la fiche et les instances : l\\'annulation n\\'est pas automatique.'\n"
     "          : 'En attente dans la file d\\'injection.') : '');   // U3an\n"),

    ("étape ⑤ non chargée pour une entité",
     "      if (data.etape >= 5 && data.type !== 'signal') chargerMain(); else viderMain();",
     "      if (data.etape >= 5 && data.type !== 'signal' && data.type !== 'entite') chargerMain(); else viderMain();"),
]


def _node_check(chemin):
    """(ok, message) de node --check ; (None, ...) si node est absent."""
    try:
        r = subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None, "node absent"
    return r.returncode == 0, r.stderr.strip()


def _premiere_erreur(msg):
    """Ligne « fichier:ligne » + texte de l'erreur, sans le chemin (comparable entre deux fichiers)."""
    lignes = [l for l in msg.splitlines() if l.strip()]
    return " | ".join(l.strip() for l in lignes[:4] if "SyntaxError" in l or l.strip().startswith("("))[:300]


def verifier_js(chemin, original):
    """Contrôle de app.js. Un node ancien peut refuser une syntaxe DÉJÀ présente dans
    l'original (ex. « ||= ») : on ne bloque que si l'erreur est NOUVELLE.
    Repli sans node : équilibre des accolades et parenthèses."""
    ok, msg = _node_check(chemin)
    if ok:
        return True, "node --check OK"
    if ok is False:
        import tempfile   # node refuse une extension autre que .js (ex. app.js.bak_u3an)
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "original.js"
            copie.write_text(Path(original).read_text(encoding="utf-8"), encoding="utf-8")
            ok0, msg0 = _node_check(copie)
        if ok0 is False and _premiere_erreur(msg) == _premiere_erreur(msg0):
            return True, ("node --check refuse une syntaxe déjà présente dans l'original "
                          f"({_premiere_erreur(msg0)[:90]}) : aucune erreur nouvelle")
        return False, msg[:400]
    t = chemin.read_text(encoding="utf-8")
    ok2 = t.count("{") == t.count("}") and t.count("(") == t.count(")")
    return ok2, ("accolades/parenthèses équilibrées (node absent)" if ok2
                 else "accolades/parenthèses déséquilibrées")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="écrit (sinon aperçu)")
    ap.add_argument("--py", default=str(APP_PY))
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
        for chemin, avant, apres in prepares:
            print(f"  {chemin.name} : {len(avant.splitlines())} -> {len(apres.splitlines())} lignes")
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, _, apres in prepares:
        bak = chemin.with_name(chemin.name + ".bak_u3an")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(apres, encoding="utf-8")
    echec = None
    try:
        py_compile.compile(str(prepares[0][0]), doraise=True)
    except py_compile.PyCompileError as e:
        echec = f"app.py : {e}"
    if not echec:
        ok, msg = verifier_js(prepares[1][0], baks[1][1])
        if not ok:
            echec = f"app.js : {msg}"
        else:
            print(f"  app.js : {msg}")
    if echec:
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)
        print(f"✗ Contrôle de syntaxe échoué, fichiers restaurés : {echec}")
        return 1
    for chemin, bak in baks:
        print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})")
    print("\nÀ faire : redémarrer Flask (app.py), puis Cmd+Maj+R dans le navigateur (app.js).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
