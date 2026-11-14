#!/usr/bin/env python3
"""
patch_u3ae_panneau_textes.py — Ourrassol 2098 (14 novembre 2026)
Panneau « Et si ? » : deux textes trompeurs, côté scripts (l'interface reste à traiter à part).

  1. simuler_et_si.py, rapport : le titre « Faits imposés à la lecture IA » devient
     « Faits imposés au récit du signal » pour un signal, et
     « Faits imposés (lecture IA et récit de l'événement) » pour un événement
     (ces faits sont aussi transmis à l'injection, pas seulement à la lecture IA).
  2. appliquer_et_si.py, étape ④ : « aucune opération enregistrée : lecture IA et passe exhaustive
     absentes ? » dit maintenant quoi faire (normal pour un signal ou un simple événement ;
     sinon relancer l'étape ① avec Lecture IA et Passe exhaustive).

Usage (racine du vault) :
    python3 generator/patch_u3ae_panneau_textes.py            # dry-run
    python3 generator/patch_u3ae_panneau_textes.py --apply    # écrit (.bak_u3ae)
"""
import argparse, py_compile, shutil, sys, tempfile
from pathlib import Path

SIM = Path("generator/simuler_et_si.py")
APP = Path("generator/appliquer_et_si.py")

A_SIM = '''        L += ["**Faits imposés à la lecture IA** :"] + [f"- {c}" for c in hyp["contraintes"]] + [""]
'''
N_SIM = '''        titre_faits = ("Faits imposés au récit du signal" if hyp.get("type") == "signal"   # U3ae
                       else "Faits imposés (lecture IA et récit de l'événement)")
        L += [f"**{titre_faits}** :"] + [f"- {c}" for c in hyp["contraintes"]] + [""]
'''
A_APP = '''        print("  (aucune opération enregistrée : lecture IA et passe exhaustive absentes ?)")
'''
N_APP = '''        # U3ae : dire quoi faire
        print("  Aucune opération à appliquer : la simulation n'a enregistré ni zone, ni trajectoire, "
              "ni relation.")
        print("  · Pour un signal ou un événement sans effet sur les fiches, c'est normal : "
              "rien à écrire ici, passer à la suite.")
        print("  · Sinon, relancer la simulation (étape ①) avec « Lecture IA » puis « Passe exhaustive » "
              "cochées, puis revenir à cette étape.")
'''

def editer(chemin, ancre, nouveau):
    if not chemin.exists():
        sys.exit(f"{chemin} introuvable : lancer depuis la racine du vault.")
    src = chemin.read_text(encoding="utf-8")
    if "U3ae" in src:
        sys.exit(f"U3ae déjà appliqué dans {chemin.name} : rien à faire.")
    if src.count(ancre) != 1:
        sys.exit(f"Abandon, rien écrit ({chemin.name}) : ancre trouvée {src.count(ancre)} fois (attendu 1).")
    neuf = src.replace(ancre, nouveau)
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / chemin.name; t.write_text(neuf, encoding="utf-8")
        try: py_compile.compile(str(t), doraise=True)
        except py_compile.PyCompileError as e: sys.exit(f"Abandon, {chemin.name} ne compile pas : {e}")
    return neuf

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    cibles = [(SIM, editer(SIM, A_SIM, N_SIM), "simuler_et_si : titre des faits imposés (signal / événement)"),
              (APP, editer(APP, A_APP, N_APP), "appliquer_et_si : message quand aucune opération")]
    for _, _, m in cibles: print(" ·", m)
    if not a.apply:
        print("\nDry-run : les deux fichiers compilent, rien n'est écrit. Relancer avec --apply."); return
    for chemin, neuf, _ in cibles:
        sauv = chemin.with_name(chemin.name + ".bak_u3ae")
        shutil.copy2(chemin, sauv); chemin.write_text(neuf, encoding="utf-8")
        py_compile.compile(str(chemin), doraise=True)
        print(f"Écrit : {chemin} (sauvegarde : {sauv.name}). py_compile OK.")

if __name__ == "__main__":
    main()
