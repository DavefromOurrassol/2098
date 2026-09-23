"""
patch_carte_etape1_fix.py — Corrige un sur-effet de patch_carte_etape1.py :
le calque "pays entier" ne doit PAS être totalement supprimé dès qu'un pays a
un overlay (cas France : overlay zone_euro_sud sur une portion, mais
affectation de base zone_interdite_heysham pour le reste -- tout supprimer
faisait disparaître la couleur de la majorité du territoire).

La bonne règle (déjà suffisante) : le calque de base affiche TOUJOURS la
couleur de la zone de base du pays ; l'overlay, en opacité pleine (fix
précédent, conservé), le recouvre par-dessus SEULEMENT à l'endroit de son
propre tracé -- pas besoin de masquer quoi que ce soit en dessous.

Usage, depuis gui/ :
    python3 patch_carte_etape1_fix.py --dry-run
    python3 patch_carte_etape1_fix.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_BLOCK = """  // Refonte Carte (12 sept 2026, point 1) : un pays couvert par au moins un
  // overlay ne doit plus jamais afficher son remplissage "pays entier" en
  // dessous -- l'overlay devient la SEULE source visuelle à cet endroit.
  // pays_masques vient du serveur (couverture_carte), indexé par nom FR.
  const paysMasques = CarteState.couverture?.pays_masques || {};

  CarteState.geojsonLayer = L.geoJSON(CarteState.rawGeojson, {
    style: (feature) => {
      const name = feature.properties?.name || feature.properties?.ADMIN || '';
      const frList = enToFr[_normEn(name)];
      if (!frList) return { fillColor: 'transparent', weight: 0.5, color: '#ccc', fillOpacity: 0 };

      const estMasque = frList.some(fr => paysMasques[fr]);
      if (estMasque) {
        // Portion(s) déjà représentée(s) par un ou plusieurs overlays
        // dessinés par-dessus -- ne rien peindre ici évite toute
        // superposition de motif/couleur (le bug "motif visible en dessous").
        return { fillColor: 'transparent', weight: 1, color: '#666', fillOpacity: 0 };
      }

      const allNull = frList.every(fr => !CarteState.affectations[fr]);
      if (allNull) return { fillColor: '#999', weight: 1, color: '#666', fillOpacity: 0.5 };
"""

NEW_BLOCK = """  CarteState.geojsonLayer = L.geoJSON(CarteState.rawGeojson, {
    style: (feature) => {
      const name = feature.properties?.name || feature.properties?.ADMIN || '';
      const frList = enToFr[_normEn(name)];
      if (!frList) return { fillColor: 'transparent', weight: 0.5, color: '#ccc', fillOpacity: 0 };

      // Refonte Carte (12 sept 2026, point 1 -- corrigé) : le calque de base
      // affiche TOUJOURS la couleur de la zone de base du pays, même s'il a
      // par ailleurs un ou plusieurs overlays -- un pays peut être partagé
      // (ex. France : zone_interdite_heysham en base + portion overlay
      // zone_euro_sud), supprimer tout le calque de base faisait disparaître
      // la couleur de la portion NON couverte par un overlay. L'overlay,
      // rendu en opacité pleine plus bas, recouvre correctement sa propre
      // portion sans qu'il soit nécessaire de masquer quoi que ce soit ici.
      const allNull = frList.every(fr => !CarteState.affectations[fr]);
      if (allNull) return { fillColor: '#999', weight: 1, color: '#666', fillOpacity: 0.5 };
"""


def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not APP_JS.exists():
        print("ERREUR : app.js introuvable (cherché dans static/app.js et ./app.js).")
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
            print("(node --check échoue déjà sur l'original -- non bloquant, comme la dernière fois.)")
        elif r_avant.returncode == 0 and r_apres.returncode != 0:
            print(f"\nERREUR CRITIQUE : {r_apres.stderr}\nRIEN N'EST ÉCRIT.")
            return
        else:
            print("Validation `node --check` : OK")

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak2")
    bak.write_text(text, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
