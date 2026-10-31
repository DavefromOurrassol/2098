#!/usr/bin/env python3
"""
patch_s30_reciprocite_exclus.py — Ourrassol 2098 (S30, 31 octobre 2026)
=======================================================================

Suite de patch_s30_apercu_reciprocite.py. Test sur le vrai vault : 15 fiches
« à sens unique » annoncées en fortress_world, toutes dues aux personnages en
réserve (Anton Vasko, Malo, Raimon). Or l'étape ④ lance la réciprocité avec
--ignorer-exclus : une fiche `exclure_articles: true` ne propage pas ses
relations (calculer_reciprocite, fix_alliances_oppositions.py). L'estimation
appliquait une règle différente.

Correctif : reciprocite_prevue() reprend exactement la règle de
calculer_reciprocite(ignorer_exclues=True) — exclus sautés comme source, slug
lu dans le frontmatter, conflit = A cite B dans un champ et B cite A dans l'autre
(ces paires ne sont pas comptées comme ajouts).

USAGE (depuis la racine du vault)
    python3 generator/patch_s30_reciprocite_exclus.py            # aperçu
    python3 generator/patch_s30_reciprocite_exclus.py --apply    # écrit (sauvegarde .bak_s30exclus)
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S30_RECIP_EXCLUS"
ANCIEN = '''def reciprocite_prevue(sc, W):
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


'''
NOUVEAU = '''def reciprocite_prevue(sc, W):
    """PATCH_S30_RECIPROCITE : ce que la remise en réciprocité (fix_alliances_oppositions.py,
    tout le scénario) changera, calculé sur les fiches telles qu'elles seront après les
    opérations (textes en mémoire de W). Estimation : le script fait foi.
    PATCH_S30_RECIP_EXCLUS : même règle que calculer_reciprocite(ignorer_exclues=True), l'option
    --ignorer-exclus de l'étape ④ : une fiche `exclure_articles: true` ne propage pas ses
    relations ; conflit = A cite B dans un champ, B cite A dans l'autre.
    Retourne ({fiche: [ajouts]}, [(a, b) en conflit alliance/opposition])."""
    fms = {}
    for p in sorted(INSTANCES.glob(f"*_{sc}.md")):
        try:
            texte = W.textes.get(p) or p.read_text(encoding="utf-8")
        except OSError:
            continue
        d = decoupe(texte)
        fm = (lire_fm(d[1]) if d else None) or {}
        fms[str(fm.get("slug") or p.stem)] = fm

    def liste(fm, champ):
        v = fm.get(champ)
        return [str(x).strip() for x in v if x] if isinstance(v, list) else []

    ajouts, conflits = {}, set()
    for a, fm in fms.items():
        if fm.get("exclure_articles") is True:
            continue   # personnage en réserve : ses relations ne sont pas propagées
        for champ, inverse in (("alliances", "oppositions"), ("oppositions", "alliances")):
            for b in liste(fm, champ):
                if b not in fms or b == a or a in liste(fms[b], champ):
                    continue
                if a in liste(fms[b], inverse):
                    conflits.add(tuple(sorted((a, b))))
                    continue
                ajouts.setdefault(b, []).append(f"+ {champ[:-1]} `{a}`")
    return ajouts, sorted(conflits)


'''


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
    n = texte.count(ANCIEN)
    if n != 1:
        sys.exit(f"✗ fonction reciprocite_prevue trouvée {n} fois telle que livrée (1 attendue) : "
                 "patch_s30_apercu_reciprocite.py appliqué ? rien écrit.")
    nouveau = texte.replace(ANCIEN, NOUVEAU)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(nouveau)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ le fichier patché ne compile pas, rien écrit :\n{e}")
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    print(f"{'ÉCRITURE' if a.apply else 'APERÇU (rien écrit)'} — {cible.name}")
    print("  ~ reciprocite_prevue : règle de calculer_reciprocite(ignorer_exclues=True)")
    print(f"  compilation : OK ({len(texte.splitlines())} → {len(nouveau.splitlines())} lignes)")
    if not a.apply:
        print("\nRelancer avec --apply pour écrire (sauvegarde .bak_s30exclus).")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_s30exclus"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"\n✓ {cible.name} patché (sauvegarde {cible.name}.bak_s30exclus)")


if __name__ == "__main__":
    main()
