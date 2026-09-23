"""
patch_carte_sous_zone_repli.py — Certaines sous-zones référencent des
régions/lieux dans leur origine_reelle (ex. "Balkans occidentaux") plutôt
que des noms de pays exacts présents sur le fond de carte -- aucune
géométrie n'est alors trouvable, et sans tracé (overlay) dédié la sous-zone
reste invisible malgré le fix précédent. Plutôt que de ne rien afficher
silencieusement, on retombe sur la zone parente (racine N1) avec un message
explicite dans la barre de statut, pour que ce ne soit jamais un silence
qui ressemble à un bug.

Usage, depuis gui/ :
    python3 patch_carte_sous_zone_repli.py --dry-run
    python3 patch_carte_sous_zone_repli.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_BLOCK = """function renderSurlignageZone() {
  if (CarteState.surligneLayer) {
    CarteState.map.removeLayer(CarteState.surligneLayer);
    CarteState.surligneLayer = null;
  }
  const slug = CarteState.zoneSurlignee;
  if (!slug || !CarteState.rawGeojson) return;
  if (typeof turf === 'undefined') {
    console.warn('Turf.js non chargé -- contour de zone non affiché.');
    return;
  }

  // Sous-zone (niveau 2/3) : pas de couleur propre (héritage N1), mais peut
  // quand même être localisée -- on ne garde que SES propres pays (son
  // origine_reelle à elle), parmi ceux affectés en base à sa racine N1.
  // racineParSlug/origineReelleParSlug sont peuplés à l'ouverture de
  // l'arbre (openArbreZonePanel) -- absents tant qu'aucun arbre n'a encore
  // été ouvert pour cette branche, auquel cas la sous-zone reste non
  // localisable pour l'instant (pas d'erreur, juste rien à afficher).
  const estN1 = CarteState.zonesN1.some(z => z.slug === slug);
  const racineSlug = estN1 ? slug : (CarteState.racineParSlug?.[slug] || null);
  const paysSousZone = estN1 ? null : new Set(
    (CarteState.origineReelleParSlug?.[slug] || [])
      .map(o => o && o.entite)
      .filter(Boolean)
  );
  if (!racineSlug) return;

  const enToFr = _buildEnToFrIndex();
  const geometries = [];

  CarteState.rawGeojson.features.forEach(feature => {
    const name = feature.properties?.name || feature.properties?.ADMIN || '';
    const frList = enToFr[_normEn(name)];
    if (!frList) return;
    const zone = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
    if (zone !== racineSlug) return;
    if (paysSousZone && !frList.some(fr => paysSousZone.has(fr))) return;

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
  });

  if (!geometries.length) return;"""

NEW_BLOCK = """// Rassemble les géométries "pays entier + overlays" appartenant à
// `cibleSlugOverlay`, parmi les pays affectés en base à `racineSlug`, filtré
// le cas échéant par `paysFiltre` (Set de noms FR, ou null = pas de filtre).
// Factorisé (12 sept 2026) pour permettre le repli zone parente ci-dessous
// sans dupliquer la boucle turf.difference.
function _gatherZoneGeometries(racineSlug, cibleSlugOverlay, paysFiltre) {
  const enToFr = _buildEnToFrIndex();
  const geometries = [];

  CarteState.rawGeojson.features.forEach(feature => {
    const name = feature.properties?.name || feature.properties?.ADMIN || '';
    const frList = enToFr[_normEn(name)];
    if (!frList) return;
    const zone = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
    if (zone !== racineSlug) return;
    if (paysFiltre && !frList.some(fr => paysFiltre.has(fr))) return;

    // Ce pays est affecté (en base) à la zone surlignée -- mais si une
    // portion de son territoire est découpée par un overlay appartenant à
    // une AUTRE zone (ex. France : base Zone Interdite de Heysham, portion
    // Zone Euro Sud en overlay), il faut l'exclure du contour. Découpe
    // géométrique réelle (turf.difference), pas une approximation.
    let geom = feature;
    const overlaysAutreZone = (CarteState.overlays?.features || []).filter(f =>
      f.properties?.pays && frList.includes(f.properties.pays) && f.properties.zone_slug !== cibleSlugOverlay
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
    if (feature.properties?.zone_slug === cibleSlugOverlay) geometries.push(feature);
  });

  return geometries;
}

const _MSG_REPLI_SOUS_ZONE = "Cette sous-zone n'a pas de tracé propre localisable -- zone parente affichée à la place.";

function renderSurlignageZone() {
  if (CarteState.surligneLayer) {
    CarteState.map.removeLayer(CarteState.surligneLayer);
    CarteState.surligneLayer = null;
  }
  const slug = CarteState.zoneSurlignee;
  if (!slug || !CarteState.rawGeojson) return;
  if (typeof turf === 'undefined') {
    console.warn('Turf.js non chargé -- contour de zone non affiché.');
    return;
  }

  // Sous-zone (niveau 2/3) : pas de couleur propre (héritage N1), mais peut
  // quand même être localisée -- on ne garde que SES propres pays (son
  // origine_reelle à elle), parmi ceux affectés en base à sa racine N1.
  // racineParSlug/origineReelleParSlug sont peuplés à l'ouverture de
  // l'arbre (openArbreZonePanel) -- absents tant qu'aucun arbre n'a encore
  // été ouvert pour cette branche, auquel cas la sous-zone reste non
  // localisable pour l'instant (pas d'erreur, juste rien à afficher).
  const estN1 = CarteState.zonesN1.some(z => z.slug === slug);
  const racineSlug = estN1 ? slug : (CarteState.racineParSlug?.[slug] || null);
  if (!racineSlug) return;

  const statusEl = document.getElementById('carte-status');
  let geometries;

  if (estN1) {
    geometries = _gatherZoneGeometries(racineSlug, slug, null);
  } else {
    const paysSousZone = new Set(
      (CarteState.origineReelleParSlug?.[slug] || [])
        .map(o => o && o.entite)
        .filter(Boolean)
    );
    geometries = _gatherZoneGeometries(racineSlug, slug, paysSousZone);

    if (!geometries.length) {
      // Repli (12 sept 2026) : cette sous-zone référence des lieux/régions
      // plutôt que des noms de pays exacts (ex. "Balkans occidentaux"),
      // sans overlay dédié -- rien à dessiner pour elle spécifiquement.
      // Montrer sa zone parente plutôt que rien du tout, avec un message
      // explicite pour que ça ne ressemble jamais à un bug silencieux.
      geometries = _gatherZoneGeometries(racineSlug, racineSlug, null);
      if (statusEl) statusEl.textContent = _MSG_REPLI_SOUS_ZONE;
    } else if (statusEl && statusEl.textContent === _MSG_REPLI_SOUS_ZONE) {
      statusEl.textContent = '';
    }
  }

  if (!geometries.length) return;"""


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
    new_text = _patch(original, [(OLD_BLOCK, NEW_BLOCK)], "app.js")

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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak19")
    bak.write_text(original, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
