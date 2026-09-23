"""
patch_carte_etape6.py — Le contour orange d'une zone incluait tout le
territoire d'un pays partagé (ex. France pour Zone Interdite de Heysham),
même la portion qui appartient en réalité à une AUTRE zone via un overlay
(ex. Zone Euro Sud). Utilise turf.difference() pour retirer précisément ces
portions avant de calculer le contour -- plus une approximation, une vraie
découpe géométrique.

Usage, depuis gui/ :
    python3 patch_carte_etape6.py --dry-run
    python3 patch_carte_etape6.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_BLOCK = """  const enToFr = _buildEnToFrIndex();
  const geometries = [];

  CarteState.rawGeojson.features.forEach(feature => {
    const name = feature.properties?.name || feature.properties?.ADMIN || '';
    const frList = enToFr[_normEn(name)];
    if (!frList) return;
    const zone = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
    if (zone === slug) geometries.push(feature);
  });

  (CarteState.overlays?.features || []).forEach(feature => {
    if (feature.properties?.zone_slug === slug) geometries.push(feature);
  });"""

NEW_BLOCK = """  const enToFr = _buildEnToFrIndex();
  const geometries = [];

  CarteState.rawGeojson.features.forEach(feature => {
    const name = feature.properties?.name || feature.properties?.ADMIN || '';
    const frList = enToFr[_normEn(name)];
    if (!frList) return;
    const zone = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
    if (zone !== slug) return;

    // Ce pays est affecté (en base) à la zone surlignée -- mais si une
    // portion de son territoire est découpée par un overlay appartenant à
    // une AUTRE zone (ex. France : base Zone Interdite de Heysham, portion
    // Zone Euro Sud en overlay), il faut l'exclure du contour. Découpe
    // géométrique réelle (turf.difference), pas une approximation.
    let geom = feature;
    const overlaysAutreZone = (CarteState.overlays?.features || []).filter(f =>
      f.properties?.pays && frList.includes(f.properties.pays) && f.properties.zone_slug !== slug
    );
    overlaysAutreZone.forEach(ov => {
      try {
        const diff = turf.difference(geom, ov);
        if (diff) geom = diff;
      } catch (e) {
        console.warn('turf.difference a échoué (géométrie non modifiée)', e);
      }
    });
    geometries.push(geom);
  });

  (CarteState.overlays?.features || []).forEach(feature => {
    if (feature.properties?.zone_slug === slug) geometries.push(feature);
  });"""


OLD_COMMENT = """// Avant (12 sept 2026) : chaque pays de la zone recevait individuellement
// un trait orange, laissant les frontières internes de la zone visibles --
// pas ce que David voulait (juste le contour extérieur de la zone entière).
// Fusionne (turf.union) tous les pays "pays entier" + portions overlay
// appartenant à la zone sélectionnée en une seule géométrie, et affiche
// uniquement son contour, sans remplissage, par-dessus tout le reste.
//
// Approximation assumée : pour un pays partagé (ex. France, base=Heysham +
// overlay=Zone Euro Sud), surligner Heysham inclut tout le contour de la
// France (pas seulement la portion hors-overlay) -- une vraie découpe
// (turf.difference) serait plus précise mais nettement plus coûteuse pour
// un gain surtout invisible sur le contour EXTÉRIEUR de la zone.
function renderSurlignageZone() {"""

NEW_COMMENT = """// Avant (12 sept 2026) : chaque pays de la zone recevait individuellement
// un trait orange, laissant les frontières internes de la zone visibles --
// pas ce que David voulait (juste le contour extérieur de la zone entière).
// Fusionne (turf.union) tous les pays "pays entier" + portions overlay
// appartenant à la zone sélectionnée en une seule géométrie, et affiche
// uniquement son contour, sans remplissage, par-dessus tout le reste.
//
// Pour un pays partagé (ex. France, base=Heysham + overlay=Zone Euro Sud),
// la portion overlay d'une AUTRE zone est retirée par turf.difference avant
// le calcul du contour -- surligner Heysham ne montre plus tout le contour
// de la France, seulement sa portion réelle (fix du 12 sept 2026).
function renderSurlignageZone() {"""


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

    n2 = new_text.count(OLD_COMMENT)
    if n2 == 1:
        new_text = new_text.replace(OLD_COMMENT, NEW_COMMENT, 1)
        print("Commentaire obsolète (approximation) également mis à jour.")
    else:
        print("(commentaire d'en-tête non trouvé tel quel -- pas bloquant, juste pas nettoyé)")

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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak9")
    bak.write_text(text, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
