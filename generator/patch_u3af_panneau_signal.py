#!/usr/bin/env python3
"""
patch_u3af_panneau_signal.py — Ourrassol 2098 (14 novembre 2026)
Panneau « Parcours de l'hypothèse » (gui/static/app.js, buildDecisionHypothese), cas d'un signal :
  1. les options payantes sans objet de l'étape ① (--consequences-ia = Lecture IA,
     --passe-exhaustive, --refaire = nouveau tirage) sont décochées et grisées quand l'hypothèse
     choisie est un signal (ni carte, ni zones, ni trajectoires), et rétablies sinon ;
  2. les étapes ④ et ⑤ ne sont plus affichées pour un signal (le parcours s'arrête à ③ : la
     frise passe à 3 étapes) ;
  3. l'aide de l'étape ① le dit.
Un événement ne change pas. Contrôle de syntaxe avec node si disponible.

Usage (racine du vault) :
    python3 generator/patch_u3af_panneau_signal.py            # dry-run
    python3 generator/patch_u3af_panneau_signal.py --apply    # écrit (app.js.bak_u3af)
Recharger la page du GUI après --apply (Flask n'a pas besoin d'être relancé).
"""
import argparse, shutil, subprocess, sys, tempfile
from pathlib import Path

CIBLE = Path("gui/static/app.js")

def une_fois(texte, ancre, nouveau):
    n = texte.count(ancre)
    if n != 1:
        raise ValueError(f"ancre trouvée {n} fois (attendu 1) : {ancre[:70]!r}")
    return texte.replace(ancre, nouveau)

def appliquer(src):
    m = []
    # 1. frise : 3 étapes pour un signal
    src = une_fois(src,
        "    ETAPES_COURTES.forEach((nom, i) => {\n      const n = i + 1;\n",
        "    const nbEtapes = typeCourant === 'signal' ? 3 : ETAPES_COURTES.length;   // U3af : un signal s'arrête à ③\n"
        "    ETAPES_COURTES.slice(0, nbEtapes).forEach((nom, i) => {\n      const n = i + 1;\n")
    src = une_fois(src, "      if (n < 5) {\n", "      if (n < nbEtapes) {\n")
    m.append("frise à 3 étapes pour un signal")
    # 2. fonction de grisage, avant typeCourant
    src = une_fois(src, "  let typeCourant = 'evenement';   // U2f\n",
"""  // U3af : options payantes sans objet pour un signal (ni carte, ni zones, ni trajectoires)
  const OPTIONS_SANS_OBJET_SIGNAL = ['--consequences-ia', '--passe-exhaustive', '--refaire'];
  const griserSignal = (oui) => {
    OPTIONS_SANS_OBJET_SIGNAL.forEach(flag => {
      const el = document.querySelector(`#form-body [data-flag="${flag}"]`);
      if (!el) return;
      if (oui && el.checked) {
        el.checked = false;
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
      el.disabled = oui;
      const ligne = el.closest('.checkbox-row') || el.parentElement;
      if (ligne) {
        ligne.title = oui ? 'Sans objet pour un signal (ni carte, ni zones, ni trajectoires)' : '';
        ligne.style.opacity = oui ? '0.45' : '';
      }
    });
  };
  let typeCourant = 'evenement';   // U2f
""")
    m.append("fonction griserSignal")
    # 3. afficher : aucune hypothèse -> options rétablies
    src = une_fois(src,
        "      blocs.forEach(b => montrer(b.bloc, false));\n      dessinerFrise(0);\n      return;\n",
        "      blocs.forEach(b => montrer(b.bloc, false));\n      dessinerFrise(0);\n      griserSignal(false);   // U3af\n      return;\n")
    # 4. afficher : étapes ④ et ⑤ masquées pour un signal, options grisées
    src = une_fois(src,
        "      montrer(b.bloc, etat !== 'à venir');\n      if (etat !== 'à venir') styliserEtape(b, etat);\n    });\n    dessinerFrise(e.etape);\n",
        "      const sansObjet = typeCourant === 'signal' && b.n > 3;   // U3af : un signal s'arrête à ③\n"
        "      montrer(b.bloc, etat !== 'à venir' && !sansObjet);\n      if (etat !== 'à venir') styliserEtape(b, etat);\n    });\n"
        "    griserSignal(typeCourant === 'signal');   // U3af\n    dessinerFrise(e.etape);\n")
    m.append("étapes ④ et ⑤ masquées et options grisées pour un signal")
    # 5. aide de l'étape ①
    src = une_fois(src,
        "'Règle les options ci-dessus (laisse « Scénario » vide, coche « Lecture IA » et « Passe exhaustive »), ' +",
        "'Règle les options ci-dessus (laisse « Scénario » vide, coche « Lecture IA » et « Passe exhaustive » ; " 
        "pour un signal, ces options payantes sont sans objet et grisées), ' +")
    m.append("aide de l'étape ①")
    return src, m

def syntaxe_ok(texte):
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "app.js"; t.write_text(texte, encoding="utf-8")
        try:
            r = subprocess.run(["node", "--check", str(t)], capture_output=True, text=True)
        except FileNotFoundError:
            print(" · node absent : syntaxe non vérifiée"); return True
        if r.returncode:
            return False
        return True

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not CIBLE.exists():
        sys.exit(f"{CIBLE} introuvable : lancer depuis la racine du vault.")
    src = CIBLE.read_text(encoding="utf-8")
    if "U3af" in src:
        sys.exit("U3af déjà appliqué : rien à faire.")
    try:
        neuf, msgs = appliquer(src)
    except ValueError as e:
        sys.exit(f"Abandon, rien écrit : {e}")
    if not syntaxe_ok(src):   # le fichier d'origine échoue déjà (node trop ancien, ex. opérateur ||=)
        print(" · node ne valide pas le fichier d'origine (version trop ancienne) : syntaxe non vérifiée")
    elif not syntaxe_ok(neuf):
        sys.exit("Abandon : erreur de syntaxe JavaScript dans le résultat, rien n'est écrit.")
    for x in msgs: print(" ·", x)
    if not a.apply:
        print("\nDry-run : le résultat est valide, rien n'est écrit. Relancer avec --apply."); return
    sauv = CIBLE.with_name(CIBLE.name + ".bak_u3af")
    shutil.copy2(CIBLE, sauv); CIBLE.write_text(neuf, encoding="utf-8")
    print(f"\nÉcrit : {CIBLE} (sauvegarde : {sauv.name}). Recharger la page du GUI.")

if __name__ == "__main__":
    main()
