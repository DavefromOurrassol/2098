#!/usr/bin/env python3
"""
patch_s30_apercu_reciprocite.py — Ourrassol 2098 (S30, 31 octobre 2026)
=======================================================================

Défaut trouvé au test réel de S30 (exemple reunification_ecosse_2070) : l'étape ④
annonçait « Fichiers modifiés : 7 », mais la remise en réciprocité lancée après
l'écriture (fix_alliances_oppositions.py --reciprocite-seule, sur TOUT le
scénario) a aussi modifié une fiche sans lien avec l'hypothèse
(institutions_multilaterales_survivantes_reference : ancienne relation à sens unique).

Correctif dans appliquer_et_si.py : quand des relations ou disparitions sont
retenues, l'aperçu (et l'écriture) affichent, avant d'écrire, une estimation
calculée sur les fiches du scénario telles qu'elles seront après les opérations :
  · fiches complétées par réciprocité des opérations de l'hypothèse ;
  · relations à sens unique déjà présentes dans le vault, hors hypothèse ;
  · conflits alliance / opposition (le script les tranche en opposition).
Rien ne change dans l'écriture elle-même : fix_alliances_oppositions.py la fait.

USAGE (depuis la racine du vault)
    python3 generator/patch_s30_apercu_reciprocite.py            # aperçu
    python3 generator/patch_s30_apercu_reciprocite.py --apply    # écrit (sauvegarde .bak_s30recip)
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S30_RECIPROCITE"
PREREQUIS = "PATCH_S30_RELOCALISER"   # même fichier, patch précédent (ancres voisines)

ANCRE_FONCTION = "def lancer(cmd):\n"
FONCTION = '''def reciprocite_prevue(sc, W):
    """PATCH_S30_RECIPROCITE : ce que la remise en réciprocité (fix_alliances_oppositions.py,
    tout le scénario) changera, calculé sur les fiches telles qu'elles seront après les
    opérations (textes en mémoire de W). Estimation : le script fait foi.
    Retourne ({fiche: [ajouts]}, [(a, b) en conflit alliance/opposition])."""
    fms = {}
    for p in sorted(INSTANCES.glob(f"*_{sc}.md")):
        try:
            texte = W.textes.get(p) or p.read_text(encoding="utf-8")
        except OSError:
            continue
        d = decoupe(texte)
        fms[p.stem] = (lire_fm(d[1]) if d else None) or {}

    def liste(fm, champ):
        v = fm.get(champ)
        return [str(x).strip() for x in v if x] if isinstance(v, list) else []

    ajouts = {}
    for a, fm in fms.items():
        for champ in ("alliances", "oppositions"):
            for b in liste(fm, champ):
                if b in fms and b != a and a not in liste(fms[b], champ):
                    ajouts.setdefault(b, []).append(f"+ {champ[:-1]} `{a}`")
    conflits = sorted({tuple(sorted((a, b))) for a, fm in fms.items()
                       for b in set(liste(fm, "alliances")) & set(liste(fm, "oppositions"))})
    return ajouts, conflits


def afficher_reciprocite(ops, W):
    """PATCH_S30_RECIPROCITE : bloc « Réciprocité » de l'aperçu, par scénario touché."""
    touches = {p.stem for p in W.changes()}
    for sc in dict.fromkeys(o["sc"] for o in ops if o["retenue"] and o["genre"] in ("relation", "disparition")):
        ajouts, conflits = reciprocite_prevue(sc, W)
        par_op = {f: v for f, v in ajouts.items()
                  if any(x.split("`")[1] in touches for x in v)}
        anciennes = {f: v for f, v in ajouts.items() if f not in par_op}
        if not (ajouts or conflits):
            continue
        print(f"\\nRéciprocité ({sc}, après l'écriture, tout le scénario) — estimation :")
        for titre, bloc in (("complétées par réciprocité des opérations", par_op),
                            ("HORS hypothèse, relations à sens unique déjà dans le vault", anciennes)):
            if bloc:
                print(f"  · {titre} : {len(bloc)} fiche(s)")
                for f, v in sorted(bloc.items()):
                    print(f"      {f} ({'; '.join(v)})")
        if conflits:
            print(f"  · conflits alliance / opposition, tranchés en opposition : {len(conflits)}")
            for a, b in conflits:
                print(f"      {a} ↔ {b}")


'''

ANCRE_APPEL = '''    if erreurs:
        print("\\n✗ Refusé :\\n"'''
APPEL = '''    afficher_reciprocite(ops, W)   # PATCH_S30_RECIPROCITE
    if erreurs:
        print("\\n✗ Refusé :\\n"'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fichier", default=str(Path(__file__).resolve().parent / "appliquer_et_si.py"))
    a = ap.parse_args()

    cible = Path(a.fichier)
    if not cible.exists():
        sys.exit(f"✗ {cible} introuvable")
    texte = cible.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        print(f"· déjà appliqué ({MARQUEUR} présent) : rien à faire.")
        return
    if PREREQUIS not in texte:
        sys.exit(f"✗ {PREREQUIS} absent : appliquer d'abord patch_s30_relocaliser_evenement.py.")
    for nom, ancre in (("fonction", ANCRE_FONCTION), ("appel", ANCRE_APPEL)):
        n = texte.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (1 attendue) : fichier différent de celui analysé, rien écrit.")

    nouveau = texte.replace(ANCRE_FONCTION, FONCTION + ANCRE_FONCTION).replace(ANCRE_APPEL, APPEL)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(nouveau)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ le fichier patché ne compile pas, rien écrit :\n{e}")
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    print(f"{'ÉCRITURE' if a.apply else 'APERÇU (rien écrit)'} — {cible.name}")
    print("  + fonctions reciprocite_prevue, afficher_reciprocite")
    print("  + étape ④ : bloc « Réciprocité » (fiches hors hypothèse, conflits) avant toute écriture")
    print(f"  compilation : OK ({len(texte.splitlines())} → {len(nouveau.splitlines())} lignes)")
    if not a.apply:
        print("\nRelancer avec --apply pour écrire (sauvegarde .bak_s30recip).")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_s30recip"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"\n✓ {cible.name} patché (sauvegarde {cible.name}.bak_s30recip)")


if __name__ == "__main__":
    main()
