"""
patch_carte_etape7.py — Le fix précédent (zoneSurlignee mis à jour au clic
sur un pays) ne couvrait que le cas à une seule entrée (openCartePanel).
Le Royaume-Uni/Angleterre/Écosse/Pays de Galles partagent un seul polygone
sur le fond de carte mais correspondent à PLUSIEURS entrées côté vault --
cliquer dessus ouvre un petit sélecteur ("plusieurs entrées") sans jamais
passer par openCartePanel avant qu'un choix soit fait, donc la surbrillance
ne bougeait pas. Ce patch met aussi à jour la surbrillance dès l'ouverture
de ce sélecteur (sur la zone résolue de la première entrée affectée, même
logique que le calque de base).

Usage, depuis gui/ :
    python3 patch_carte_etape7.py --dry-run
    python3 patch_carte_etape7.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_BLOCK = """function onCartePaysClick(frList, displayName) {
  if (frList.length === 1) {
    openCartePanel(frList[0]);
    return;
  }
  const panel = document.getElementById('carte-panel');
  panel.innerHTML = `
    <div class="carte-panel-title">${displayName} — plusieurs entrées</div>
"""

NEW_BLOCK = """function onCartePaysClick(frList, displayName) {
  if (frList.length === 1) {
    openCartePanel(frList[0]);
    return;
  }

  // Fix (12 sept 2026) : cas à entrées multiples (ex. Royaume-Uni/Angleterre/
  // Écosse/Pays de Galles, un seul polygone sur le fond de carte pour
  // plusieurs entrées côté vault) -- le fix précédent ne couvrait que
  // openCartePanel (une seule entrée), donc cliquer ici ne mettait jamais à
  // jour la surbrillance avant qu'un choix soit fait dans le sélecteur.
  const zoneResolue = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
  CarteState.zoneSurlignee = zoneResolue || null;
  renderCarteLayer();

  const panel = document.getElementById('carte-panel');
  panel.innerHTML = `
    <div class="carte-panel-title">${displayName} — plusieurs entrées</div>
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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak10")
    bak.write_text(text, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
