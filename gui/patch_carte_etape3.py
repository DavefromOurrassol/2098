"""
patch_carte_etape3.py — Corrige le contour orange qui restait bloqué sur la
zone précédemment sélectionnée : cliquer sur un pays (openCartePanel) ne
mettait jamais à jour CarteState.zoneSurlignee -- seuls un clic sur un
overlay ou sur une ligne de légende le faisaient. Après ce patch, cliquer
sur n'importe quel pays met à jour la surbrillance sur SA zone (ou l'efface
si le pays n'est pas affecté).

Usage, depuis gui/ :
    python3 patch_carte_etape3.py --dry-run
    python3 patch_carte_etape3.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_BLOCK = """function openCartePanel(pays) {
  const zone = CarteState.affectations[pays];
  const panel = document.getElementById('carte-panel');
"""

NEW_BLOCK = """function openCartePanel(pays) {
  const zone = CarteState.affectations[pays];

  // Fix (12 sept 2026) : cliquer sur un pays ne mettait jamais à jour la
  // zone surlignée -- seuls un clic sur un overlay ou sur la légende le
  // faisaient. Résultat : le contour orange restait bloqué sur la
  // précédente sélection tant qu'on ne cliquait pas spécifiquement sur un
  // overlay de cette même zone. Maintenant : tout clic sur un pays met à
  // jour la surbrillance sur SA zone (ou l'efface si le pays n'est pas
  // affecté).
  CarteState.zoneSurlignee = zone || null;
  renderCarteLayer();

  const panel = document.getElementById('carte-panel');
"""


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
    n = text.count(OLD_BLOCK)
    print(f"Bloc à corriger : {n} occurrence(s) exacte(s) trouvée(s)")
    if n != 1:
        print("\nERREUR : attendu exactement 1 occurrence -- RIEN N'EST ÉCRIT. "
              "Colle-moi ce message, je regénère le patch plutôt que deviner.")
        return

    new_text = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
    print(f"Taille avant : {len(text)} -- après : {len(new_text)}")

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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak5")
    bak.write_text(text, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
