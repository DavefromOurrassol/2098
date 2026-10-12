#!/usr/bin/env python3
"""
patch_s27_v8161.py — Ourrassol 2098 (S27, 12 octobre 2026)
==========================================================

simuler_et_si.py v8.16 -> v8.16.1 : quand la passe exhaustive a tourné, la
recherche par mots des « Fiches à relire » ne liste plus les instances ni les
événements (la passe les a tous relus et dit lesquels deviennent faux). Restent
les zones et les lignes du registre, que la passe ne lit pas. L'étape
« Relecture IA ciblée d'une instance » disparaît dans ce cas.
Sans passe : comportement inchangé.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v8161.py --dry-run && python3 generator/patch_s27_v8161.py
Sauvegarde .bak_v8161 ; refuse un second passage.
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "simuler_et_si.py"

REMPLACEMENTS = [
    ('VERSION = "v8.16"', 'VERSION = "v8.16.1"'),

    ('    # 9 bis. Fiches à relire (V8.3) ------------------------------------------------\n'
     '    if cites:\n'
     '        _etape(E, "Fiches à relire", "Termes cherchés : " + ", ".join(sorted(termes)[:20])\n'
     '               + (f" … (+{len(termes) - 20})" if len(termes) > 20 else ""),\n'
     '               motif="mot entier, sans casse ni accents ; le registre seulement après "\n'
     '               f"{hyp[\'date\']:g} (chronologie)")\n'
     '        for type_, items in cites.items():\n',
     '    # 9 bis. Fiches à relire (V8.3) ------------------------------------------------\n'
     '    # V8.16.1 : avec la passe exhaustive, instances et événements sont déjà relus ;\n'
     '    # la recherche par mots ne garde que les zones et le registre.\n'
     '    cites_lus = {k: v for k, v in cites.items()\n'
     '                 if not passe or k not in ("Instances", "Événements")}\n'
     '    if cites_lus:\n'
     '        _etape(E, "Fiches à relire", "Termes cherchés : " + ", ".join(sorted(termes)[:20])\n'
     '               + (f" … (+{len(termes) - 20})" if len(termes) > 20 else ""),\n'
     '               motif="mot entier, sans casse ni accents ; le registre seulement après "\n'
     '               f"{hyp[\'date\']:g} (chronologie)"\n'
     '               + (" ; instances et événements relus par la passe exhaustive : seuls les zones "\n'
     '                  "et le registre sont listés" if passe else ""))\n'
     '        for type_, items in cites_lus.items():\n'),

    ('        if cites.get("Instances"):\n'
     '            _etape(E, "Fiches à relire", "Relecture IA ciblée d\'une instance (contradictions avec l\'hypothèse)",\n',
     '        if cites_lus.get("Instances"):\n'
     '            _etape(E, "Fiches à relire", "Relecture IA ciblée d\'une instance (contradictions avec l\'hypothèse)",\n'),

    ('    elif passe:\n'
     '        _etape(E, "Fiches à relire", "Aucun pays ni nom propre à chercher : la passe exhaustive a relu "\n'
     '               "toutes les fiches du scénario (obligatoires ci-dessus et dans les autres sections)")\n',
     '    elif passe:\n'
     '        _etape(E, "Fiches à relire", "Instances et événements relus par la passe exhaustive "\n'
     '               "(obligatoires ci-dessus et dans les autres sections) ; aucune zone ni ligne du registre "\n'
     '               "ne cite l\'hypothèse")\n'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cible", default=str(CIBLE))
    args = ap.parse_args()
    cible = Path(args.cible)
    texte = cible.read_text(encoding="utf-8")
    if 'VERSION = "v8.16.1"' in texte or "V8.16.1 :" in texte:
        sys.exit("✗ Patch déjà appliqué (v8.16.1) : rien à faire.")
    if 'VERSION = "v8.16"' not in texte:
        sys.exit("✗ simuler_et_si.py n'est pas en v8.16 : appliquer d'abord patch_s27_v816.py.")
    for n, (avant, apres) in enumerate(REMPLACEMENTS, 1):
        compte = texte.count(avant)
        if compte != 1:
            sys.exit(f"✗ Ancre n°{n} trouvée {compte} fois (1 attendue) : rien écrit.\n"
                     f"  Début de l'ancre : {avant[:80]!r}")
        texte = texte.replace(avant, apres)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(texte)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas, rien écrit : {e}")
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass
    if args.dry_run:
        print(f"✓ {len(REMPLACEMENTS)} remplacements possibles, compilation OK (dry-run, rien écrit).")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_v8161"))
    cible.write_text(texte, encoding="utf-8")
    print(f"✓ simuler_et_si.py passé en v8.16.1 ({len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_v8161.")


if __name__ == "__main__":
    main()
