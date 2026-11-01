#!/usr/bin/env python3
"""patch_s30_sans_objet.py — Ourrassol 2098, 1er novembre 2026

Défaut relevé au test réel de S30 (chute_holdfast_2072) : la passe exhaustive
affichait « Réponses rejetées car mal formées (22) », alors que ces réponses
étaient bien formées mais SANS OBJET : relation déjà présente, relation à
rompre absente du vault, trajectoire déjà à la valeur proposée (« aucun
changement ») — les mêmes motifs que les « écartées au contrôle » de la
lecture IA. Le libellé laissait croire à un défaut de l'IA ou du parseur.

Correctif (et_si_exhaustif.py, rendu du rapport) : deux lignes distinctes,
« Propositions sans objet, écartées » et « Réponses rejetées car mal
formées » (entité inconnue, valeur invalide, contresens). Le contenu de
res["rejetees"] ne change pas : seul l'affichage est séparé.

Usage (depuis la racine du vault) :
    python3 generator/patch_s30_sans_objet.py
Idempotent (marqueur PATCH_S30_SANS_OBJET) ; sauvegarde
et_si_exhaustif.py.bak_s30sansobjet ; contrôle de compilation, restauration si échec.
"""
import py_compile
import shutil
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
CIBLE = GEN / "et_si_exhaustif.py"
MARQUEUR = "PATCH_S30_SANS_OBJET"

AVANT = '''    if res["rejetees"]:
        L += [f"_Réponses rejetées car mal formées ({len(res['rejetees'])}) : " + " ; ".join(res["rejetees"][:8])
              + (" …" if len(res["rejetees"]) > 8 else "") + "_", ""]
'''

APRES = '''    if res["rejetees"]:   # PATCH_S30_SANS_OBJET : « sans objet » séparé de « mal formé »
        sans_objet = [r for r in res["rejetees"]
                      if _re.search(r"déjà |absente? du vault|aucun changement", str(r))]
        mal = [r for r in res["rejetees"] if r not in sans_objet]
        for titre, liste in (("Propositions sans objet, écartées (déjà en place, ou relation à rompre "
                              "absente du vault)", sans_objet),
                             ("Réponses rejetées car mal formées", mal)):
            if liste:
                L += [f"_{titre} ({len(liste)}) : " + " ; ".join(liste[:8])
                      + (" …" if len(liste) > 8 else "") + "_", ""]
'''


def main():
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable — lancer depuis la racine du vault. Rien fait.")
    src = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in src:
        print("· déjà appliqué — rien fait.")
        return
    n = src.count(AVANT)
    if n != 1:
        sys.exit(f"✗ bloc « mal formées » trouvé {n} fois (attendu 1) — rien fait.")
    if "import re as _re" not in src and "_re = " not in src:
        sys.exit("✗ alias _re introuvable dans et_si_exhaustif.py — rien fait.")
    bak = CIBLE.with_name(CIBLE.name + ".bak_s30sansobjet")
    shutil.copy2(CIBLE, bak)
    CIBLE.write_text(src.replace(AVANT, APRES, 1), encoding="utf-8")
    try:
        py_compile.compile(str(CIBLE), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, CIBLE)
        sys.exit(f"✗ compilation échouée, fichier restauré : {e}")
    print(f"✓ {CIBLE.name} patché (sauvegarde {bak.name})")


if __name__ == "__main__":
    main()
