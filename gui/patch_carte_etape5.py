"""
patch_carte_etape5.py — Corrige le libellé "— aucun (hachures automatiques) —"
dans les menus déroulants de motif (panneaux perso + renommer), resté
obsolète depuis que les hachures ne sont plus automatiques (12 sept 2026) --
elles sont désormais désactivées par défaut, activables uniquement via un
contrôle dédié pas encore présent dans l'UI (prévu dans le futur panneau
unique). Le libellé ne doit plus laisser croire à un comportement encore
actif.

Usage, depuis gui/ :
    python3 patch_carte_etape5.py --dry-run
    python3 patch_carte_etape5.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_TEXT = "'— aucun (hachures automatiques) —'"
NEW_TEXT = "'— aucun —'"


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
    print(f"Occurrences trouvées : {n} (2 attendues -- panneau perso + panneau renommer)")
    if n != 2:
        print("\nERREUR : attendu exactement 2 occurrences -- RIEN N'EST ÉCRIT. "
              "Colle-moi ce message, je regénère le patch plutôt que deviner.")
        return

    new_text = text.replace(OLD_TEXT, NEW_TEXT)  # les 2 occurrences, pas de limite ici

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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak7")
    bak.write_text(text, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
