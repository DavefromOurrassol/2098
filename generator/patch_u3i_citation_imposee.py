#!/usr/bin/env python3
"""
patch_u3i_citation_imposee.py — Ourrassol 2098 (U3i, 11 novembre 2026)

La citation EXACTE de l'article (vérifiée mot pour mot par l'extracteur) devient
automatiquement un FAIT IMPOSÉ de l'hypothèse (premier de ses `contraintes`), donc
transmis à l'IA d'injection et contrôlé sur le récit. Fini la correction à la main
du texte de la fiche pour les faits que l'article dit déjà.

  hypothese_depuis_texte.py : option --citation, ajoutée aux contraintes après la
                              réponse de l'IA (4 au maximum, la citation en tête)
  gui/app.py                : transmet data["citation"] à --citation
  gui/.../app.js            : envoie la citation de l'événement choisi, seulement
                              si elle a été retrouvée mot pour mot (citation_ok)

Dry-run par défaut ; --apply pour écrire (sauvegardes .bak_u3i). Idempotent.
À lancer depuis la racine du vault.
"""
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

APPLY = "--apply" in sys.argv

# ---- hypothese_depuis_texte.py ------------------------------------------------
HYP_1_ANCIEN = """    if est_signal:
        return av   # un signal couvre toujours les 6 scénarios, sans mode rupture
"""
HYP_1_NEUF = """    cit = " ".join(str(imposes.get("citation") or "").split())
    if cit and not est_signal:   # U3i : la citation exacte de l'article devient un fait imposé
        contraintes = [" ".join(str(c).split()) for c in (h.get("contraintes") or [])]
        if cit not in contraintes:
            contraintes = [cit] + contraintes
            if len(contraintes) > 4:
                av.append("une contrainte proposée par l'IA retirée (4 au maximum)")
            h["contraintes"] = contraintes[:4]
            av.append("citation de l'article ajoutée aux faits imposés")
    if est_signal:
        return av   # un signal couvre toujours les 6 scénarios, sans mode rupture
"""
HYP_2_ANCIEN = """                    help="avec --proposer : durées de montée calculées (2098 - date) pour un effet plein en 2098")
"""
HYP_2_NEUF = HYP_2_ANCIEN + """    ap.add_argument("--citation", default=None,
                    help="avec --proposer : citation exacte de l'article, ajoutée aux faits imposés (U3i)")
"""
HYP_3_ANCIEN = """            if args.effet_plein:
                imposes["effet_plein"] = True
"""
HYP_3_NEUF = HYP_3_ANCIEN + """            if args.citation:   # U3i
                imposes["citation"] = args.citation
"""

# ---- gui/app.py ---------------------------------------------------------------
APP_ANCIEN = """        if data.get("effet_plein") is True:   # U3d
            cmd.append("--effet-plein")
"""
APP_NEUF = APP_ANCIEN + """        cit_ = " ".join(str(data.get("citation") or "").split())[:600]   # U3i
        if cit_:
            cmd.append("--citation=" + cit_)
"""

# ---- app.js -------------------------------------------------------------------
JS_ANCIEN = """    extra.effet_plein = cbPlein.checked;   // U3d
"""
JS_NEUF = JS_ANCIEN + """    if (selType.value !== 'signal' && evChoisi && evChoisi.citation && evChoisi.citation_ok) extra.citation = evChoisi.citation;   // U3i
"""


def trouver_js():
    for p in sorted(Path("gui").rglob("app.js")):
        if "U3d" in p.read_text(encoding="utf-8", errors="replace"):
            return p
    return None


def editer(chemin, remplacements):
    texte = chemin.read_text(encoding="utf-8")
    nouveau = texte
    for ancien, neuf in remplacements:
        if neuf in nouveau:
            print(f"  = {chemin} : déjà appliqué ({neuf.splitlines()[-1].strip()[:50]}…)")
            continue
        if nouveau.count(ancien) != 1:
            print(f"  ✗ {chemin} : ancre introuvable ou multiple ({nouveau.count(ancien)}) :\n{ancien}")
            return False
        nouveau = nouveau.replace(ancien, neuf)
        print(f"  + {chemin} : modification prévue")
    if nouveau == texte:
        return True
    if APPLY:
        shutil.copy2(chemin, str(chemin) + ".bak_u3i")
        chemin.write_text(nouveau, encoding="utf-8")
        if chemin.suffix == ".py":
            py_compile.compile(str(chemin), doraise=True)
        elif subprocess.run(["which", "node"], capture_output=True).returncode == 0:
            r = subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True)
            if r.returncode != 0:
                print(f"  ✗ node --check a échoué :\n{r.stderr}\n  -> restaurer : cp {chemin}.bak_u3i {chemin}")
                return False
        print(f"  ✓ {chemin} écrit (sauvegarde .bak_u3i)")
    return True


def main():
    hyp = Path("generator/hypothese_depuis_texte.py")
    app = Path("gui/app.py")
    js = trouver_js()
    for p in (hyp, app):
        if not p.exists():
            sys.exit(f"✗ {p} introuvable (lancer depuis la racine du vault)")
    if js is None:
        sys.exit("✗ app.js de la GUI introuvable sous gui/")
    ok = (editer(hyp, [(HYP_1_ANCIEN, HYP_1_NEUF), (HYP_2_ANCIEN, HYP_2_NEUF), (HYP_3_ANCIEN, HYP_3_NEUF)])
          and editer(app, [(APP_ANCIEN, APP_NEUF)])
          and editer(js, [(JS_ANCIEN, JS_NEUF)]))
    print("\n" + ("✓ terminé" if ok else "✗ arrêt : rien de plus n'a été modifié après l'erreur"))
    if not APPLY:
        print("(dry-run : rien écrit ; relancer avec --apply)")
    print("Penser à redémarrer Flask et à recharger la page (Ctrl-Maj-R).")


main()
