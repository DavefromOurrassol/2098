"""
patch_carte_sous_zones_fix.py — openArbreZonePanel() surlignait
immédiatement sa RACINE (zone N1) le temps de charger l'arbre, avant que
_carteSelectionnerResultatRecherche() bascule vers la sous-zone visée.
Pour une sous-zone sans géométrie propre localisable (ses entrées
origine_reelle ne correspondent à aucun nom de pays exact -- une région,
par exemple), la bascule finale ne trouvait rien à dessiner : l'utilisateur
voyait la racine surlignée brièvement puis plus rien, un "flash" trompeur.

Ajoute un paramètre optionnel skipHighlight à openArbreZonePanel(), utilisé
uniquement par la sélection d'un résultat de recherche -- un seul rendu a
lieu désormais, directement sur la cible finale (sous-zone ou N1), jamais
de surbrillance intermédiaire sur la racine.

Usage, depuis gui/ :
    python3 patch_carte_sous_zones_fix.py --dry-run
    python3 patch_carte_sous_zones_fix.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_OPEN_ARBRE_HEAD = """async function openArbreZonePanel(slug) {
  const panel = document.getElementById('carte-panel');
  panel.innerHTML = `<div class="carte-panel-title">Arborescence</div><div class="carte-status">Chargement…</div>`;

  CarteState.zoneSurlignee = slug;
  renderCarteLayer();"""

NEW_OPEN_ARBRE_HEAD = """async function openArbreZonePanel(slug, options = {}) {
  const panel = document.getElementById('carte-panel');
  panel.innerHTML = `<div class="carte-panel-title">Arborescence</div><div class="carte-status">Chargement…</div>`;

  // skipHighlight (12 sept 2026) : la sélection d'un résultat de recherche
  // vise en réalité une SOUS-ZONE, pas cette racine -- surligner la racine
  // ici puis basculer juste après créait un flash trompeur (racine visible
  // une seconde, puis rien si la sous-zone n'a pas de géométrie propre).
  if (!options.skipHighlight) {
    CarteState.zoneSurlignee = slug;
    renderCarteLayer();
  }"""

OLD_SELECTION = """  const racineSlug = (resultat.chemin && resultat.chemin[0] && resultat.chemin[0].slug) || resultat.slug;
  await openArbreZonePanel(racineSlug);"""

NEW_SELECTION = """  const racineSlug = (resultat.chemin && resultat.chemin[0] && resultat.chemin[0].slug) || resultat.slug;
  await openArbreZonePanel(racineSlug, { skipHighlight: true });"""


def _patch(text, replacements, label):
    for old, new in replacements:
        n = text.count(old)
        print(f"[{label}] bloc attendu : {n} occurrence(s)")
        if n != 1:
            print("  -> ERREUR : attendu exactement 1 occurrence. RIEN N'EST ÉCRIT.")
            return None
        text = text.replace(old, new, 1)
    return text


def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not APP_JS.exists():
        print("ERREUR : app.js introuvable.")
        return

    original = APP_JS.read_text(encoding="utf-8")
    new_text = _patch(original, [
        (OLD_OPEN_ARBRE_HEAD, NEW_OPEN_ARBRE_HEAD),
        (OLD_SELECTION, NEW_SELECTION),
    ], "app.js")

    if new_text is None:
        print("\nRien n'a été écrit.")
        return

    if args.dry_run:
        print("\n[dry-run] Rien n'a été modifié. Relance avec --apply pour écrire réellement.")
        return

    node = shutil.which("node")
    if node:
        def _check(content, label):
            tmp = APP_JS.with_name(f"app_tmp_check_{label}.js")
            tmp.write_text(content, encoding="utf-8")
            result = subprocess.run([node, "--check", str(tmp)], capture_output=True, text=True)
            tmp.unlink()
            return result

        r_avant, r_apres = _check(original, "avant"), _check(new_text, "apres")
        if r_avant.returncode != 0 and r_apres.returncode != 0:
            print("(node --check échoue déjà sur l'original -- non bloquant, comme précédemment.)")
        elif r_avant.returncode == 0 and r_apres.returncode != 0:
            print(f"\nERREUR CRITIQUE : {r_apres.stderr}\nRIEN N'EST ÉCRIT.")
            return
        else:
            print("Validation `node --check` : OK")

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak17")
    bak.write_text(original, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
