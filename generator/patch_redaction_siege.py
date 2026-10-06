"""
patch_redaction_siege.py — 6 octobre 2026
-----------------------------------------
Site des revues : la ville siège de la revue est affichée « Rédaction à
<ville> » (pied de page, bandeau de la Une, kiosque), pour lever l'ambiguïté
quand un article d'ailleurs est repris par une revue basée à Séoul, etc.

Usage (depuis la racine du vault) :
    python3 generator/patch_redaction_siege.py          # aperçu
    python3 generator/patch_redaction_siege.py --apply  # écrit (.bak_redaction)
Refuse un second passage.
"""

import os
import shutil
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
CHEMIN = os.path.join(ICI, "export_revues.py")
MARQUEUR = "def redaction_siege("

REMPLACEMENTS = [
    (
        "pied de page",
        'def pied(rv):\n'
        '    return (f\'<footer><div class="wrap"><span>{e(rv["nom"])} · {e(str(rv.get("ville_siege", "")))}\'\n',
        'def redaction_siege(rv, majuscule=True):\n'
        '    """« Rédaction à <ville> » (6 octobre 2026) ; vide si la revue n\'a pas de siège."""\n'
        '    ville = str(rv.get("ville_siege", "") or "").strip()\n'
        '    if not ville:\n'
        '        return ""\n'
        '    return ("Rédaction à " if majuscule else "rédaction à ") + ville\n'
        '\n'
        '\n'
        'def pied(rv):\n'
        '    return (f\'<footer><div class="wrap"><span>{e(rv["nom"])} · {e(redaction_siege(rv))}\'\n',
    ),
    (
        "bandeau de la Une",
        '<span>Mensuel fondé en {e(str(rv.get("fondation", "")))} · {e(str(rv.get("ville_siege", "")))}</span>',
        '<span>Mensuel fondé en {e(str(rv.get("fondation", "")))} · {e(redaction_siege(rv, False))}</span>',
    ),
    (
        "kiosque",
        'fondée en {e(str(rv.get("fondation", "")))} · {e(str(rv.get("ville_siege", "")))}</div></div>',
        'fondée en {e(str(rv.get("fondation", "")))} · {e(redaction_siege(rv, False))}</div></div>',
    ),
]


def main():
    texte = open(CHEMIN, encoding="utf-8").read()
    if MARQUEUR in texte:
        print("✗ export_revues.py : déjà patché.")
        sys.exit(1)
    for libelle, ancre, nouveau in REMPLACEMENTS:
        n = texte.count(ancre)
        if n != 1:
            print("✗ {} : ancre trouvée {} fois (attendu 1). Rien écrit.".format(libelle, n))
            sys.exit(1)
        texte = texte.replace(ancre, nouveau)
        print("✓ {}".format(libelle))
    compile(texte, "export_revues.py", "exec")
    if "--apply" not in sys.argv:
        print("\nAperçu seulement — relancer avec --apply pour écrire.")
        return
    shutil.copy2(CHEMIN, CHEMIN + ".bak_redaction")
    open(CHEMIN, "w", encoding="utf-8").write(texte)
    print("✓ export_revues.py écrit (sauvegarde .bak_redaction)")


if __name__ == "__main__":
    main()
