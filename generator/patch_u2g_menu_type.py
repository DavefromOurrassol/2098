#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U2g — « Nouvelle hypothèse » : le menu « Type » passe sur la ligne du bouton « ✨ Proposer »,
largeur automatique (il s'étirait sur tout le panneau et sa flèche était coupée).
Appliquer après patch_u2f_finitions.py. Redémarrer Flask.

    python3 generator/patch_u2g_menu_type.py            # dry-run
    python3 generator/patch_u2g_menu_type.py --apply    # applique (.bak_u2g)
"""
import shutil
import subprocess
import sys
from pathlib import Path

F = Path("gui/static/app.js")
EDITS = [
    ("  corps.appendChild(btnProposer);\n  // U2f : type imposé",
     "  const ligneProposer = document.createElement('div');   // U2g\n"
     "  ligneProposer.style.cssText = 'display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:6px 0 10px;';\n"
     "  btnProposer.style.margin = '0';\n"
     "  ligneProposer.appendChild(btnProposer);\n"
     "  // U2f : type imposé"),
    ("  selType.style.marginLeft = '8px';\n",
     "  selType.style.setProperty('width', 'auto', 'important');\n"
     "  selType.style.maxWidth = '70%';\n"),
    ("  corps.appendChild(selType);\n",
     "  ligneProposer.appendChild(selType);\n  corps.appendChild(ligneProposer);\n"),
]


def main():
    if not F.is_file():
        print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(F))
        return 1
    src = F.read_text(encoding="utf-8")
    if "U2g" in src:
        print("Déjà appliqué : rien à faire.")
        return 0
    if "U2f : type imposé" not in src:
        print("ERREUR : appliquer d'abord patch_u2f_finitions.py.")
        return 1
    for i, (ancre, _) in enumerate(EDITS, 1):
        n = src.count(ancre)
        if n != 1:
            print("ERREUR : ancre n°{} trouvée {} fois (attendu : 1). Rien modifié.".format(i, n))
            return 1
    print("{} modifications prévues dans {}.".format(len(EDITS), F))
    if "--apply" not in sys.argv:
        print("Dry-run : rien écrit. Relancer avec --apply pour appliquer.")
        return 0
    new = src
    for ancre, rempl in EDITS:
        new = new.replace(ancre, rempl)
    shutil.copy2(F, str(F) + ".bak_u2g")
    F.write_text(new, encoding="utf-8")
    def node_ok(p):
        return subprocess.run(["node", "--check", str(p)], capture_output=True, text=True, timeout=60).returncode == 0
    try:
        if not node_ok(F) and node_ok(str(F) + ".bak_u2g"):
            shutil.copy2(str(F) + ".bak_u2g", F)
            print("ERREUR de syntaxe JavaScript, fichier restauré.")
            return 1
    except (OSError, subprocess.TimeoutExpired):
        pass
    print("Appliqué (sauvegarde .bak_u2g). Redémarrer Flask.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
