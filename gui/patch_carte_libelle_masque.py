"""
patch_carte_libelle_masque.py — Renomme le bouton "🗑️ tracé" en
"🗑️ supprimer le masque" dans la section "Pays & portions" (plus explicite,
sur demande de David : "tracé" seul ne disait pas assez clairement que
l'action retire le polygone dessiné).

Usage, depuis gui/ :
    python3 patch_carte_libelle_masque.py --dry-run
    python3 patch_carte_libelle_masque.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_TEXT = '<button class="pp-retirer-tracer-btn" data-id="${overlayId}">🗑️ tracé</button>'
NEW_TEXT = '<button class="pp-retirer-tracer-btn" data-id="${overlayId}" title="Retire le polygone dessiné pour ce pays -- origine_reelle reste inchangé">🗑️ supprimer le masque</button>'


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
    n = text.count(OLD_TEXT)
    print(f"Occurrences trouvées : {n} (1 attendue)")
    if n != 1:
        print("\nERREUR : attendu exactement 1 occurrence -- RIEN N'EST ÉCRIT. "
              "Colle-moi ce message, je regénère le patch plutôt que deviner.")
        return

    new_text = text.replace(OLD_TEXT, NEW_TEXT, 1)

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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak13")
    bak.write_text(text, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
