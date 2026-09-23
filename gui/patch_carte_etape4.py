"""
patch_carte_etape4.py — Le calque "pays entier" était en fillOpacity 0.85
(légèrement transparent), pendant que les overlays sont en fillOpacity 1
(fix précédent). Même couleur exacte, mais deux opacités différentes ->
deux nuances visibles pour une même zone selon qu'un pays est représenté
par le calque de base ou par un overlay (remonté par David sur Zone Euro
Sud). Passe le calque de base en fillOpacity 1 également, pour une
cohérence totale.

Usage, depuis gui/ :
    python3 patch_carte_etape4.py --dry-run
    python3 patch_carte_etape4.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_LINE = "      return { fillColor: fill, weight: 1, color: '#666', fillOpacity: 0.85 };"
NEW_LINE = "      return { fillColor: fill, weight: 1, color: '#666', fillOpacity: 1 };"


def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not APP_JS.exists():
        print("ERREUR : app.js introuvable.")
        return

    text = APP_JS.read_text(encoding="utf-8")
    n = text.count(OLD_LINE)
    print(f"Ligne à corriger : {n} occurrence(s) exacte(s) trouvée(s)")
    if n != 1:
        print("\nERREUR : attendu exactement 1 occurrence -- RIEN N'EST ÉCRIT. "
              "Colle-moi ce message, je regénère le patch plutôt que deviner.")
        return

    new_text = text.replace(OLD_LINE, NEW_LINE, 1)

    if args.dry_run:
        print("\n[dry-run] Rien n'a été modifié. Relance avec --apply pour corriger réellement.")
        return

    node = shutil.which("node")
    if node:
        def _check(content, label):
            tmp = APP_JS.with_name(f"app_tmp_check_{label}.js")
            tmp.write_text(content, encoding="utf-8")
            result = subprocess.run([node, "--check", str(tmp)], capture_output=True, text=True)
            tmp.unlink()
            return result

        r_avant, r_apres = _check(text, "avant"), _check(new_text, "apres")
        if r_avant.returncode != 0 and r_apres.returncode != 0:
            print("(node --check échoue déjà sur l'original -- non bloquant, comme précédemment.)")
        elif r_avant.returncode == 0 and r_apres.returncode != 0:
            print(f"\nERREUR CRITIQUE : {r_apres.stderr}\nRIEN N'EST ÉCRIT.")
            return
        else:
            print("Validation `node --check` : OK")

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak6")
    bak.write_text(text, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
