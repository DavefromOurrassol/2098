"""
patch_export_signatures.py -- S23, 4 octobre 2026.

export_revues.py signait « La rédaction de <journal> » dans deux cas où
la personne existe pourtant bien dans la rédaction :
  1. articles ORAUX : la signature n'était cherchée que dans
     `journalistes`, jamais dans `orateurs` ;
  2. noms avec ø, æ, å, ß, ł… : slugify() d'export_revues (NFKD + ascii
     ignore) donne "brresen" là où api._slugify() (NFD sans marques,
     puis non-alphanumérique -> "_") a écrit "b_rresen" dans
     journaliste_slug.
Correctif : recherche dans journalistes + orateurs, sous les deux formes
de slug.

Usage (depuis generator/) :
  python3 patch_export_signatures.py           # aperçu
  python3 patch_export_signatures.py --apply   # .bak_signatures + compilation
"""
import argparse
import py_compile
import shutil
import sys

EDITS = [
    (
        '''def trouver(nom):''',
        '''def slug_pipeline(s):
    """Même slug que api._slugify() (celui écrit dans journaliste_slug) :
    NFD, marques diacritiques retirées, tout non-alphanumérique -> "_".
    Diffère de slugify() ci-dessus pour ø, æ, å, ß, ł… (S23, 4 octobre 2026)."""
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def trouver(nom):''',
    ),
    (
        '''                    noms = {slugify(p["nom"]): p["nom"] for p in j.get("journalistes", [])}''',
        '''                    # Journalistes ET orateurs (articles oraux), sous les deux
                    # formes de slug (S23, 4 octobre 2026).
                    noms = {}
                    for p in (j.get("journalistes") or []) + (j.get("orateurs") or []):
                        if p.get("nom"):
                            noms.setdefault(slugify(p["nom"]), p["nom"])
                            noms.setdefault(slug_pipeline(p["nom"]), p["nom"])''',
    ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    p = "export_revues.py"
    t = open(p, encoding="utf-8").read()
    if "def slug_pipeline" in t:
        print("✗ export_revues.py : déjà patché")
        sys.exit(1)
    for old, new in EDITS:
        n = t.count(old)
        if n != 1:
            print("✗ {} occurrence(s) pour « {} » : rien n'est écrit".format(n, old.strip()[:60]))
            sys.exit(1)
        t = t.replace(old, new)
        print("✓ « {} »".format(old.strip()[:60]))
    if not args.apply:
        print("\nAperçu OK, rien n'est écrit. Relance avec --apply.")
        return
    shutil.copy2(p, p + ".bak_signatures")
    open(p, "w", encoding="utf-8").write(t)
    try:
        py_compile.compile(p, doraise=True)
        print("écrit + compilé : export_revues.py")
    except py_compile.PyCompileError as e:
        shutil.copy2(p + ".bak_signatures", p)
        print("✗ compilation échouée, export_revues.py restauré : {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
