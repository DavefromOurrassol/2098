"""
patch_carte_etape2.py — Corrige 3 points remontés par David après le premier
test des villes principales + le fix overlay :

  1. Villes principales : plus de distinction visuelle capitale/autre ville,
     un seul style de marqueur.
  2. Les villes disparaissaient sous les calques pays/overlays après un
     clic sur une zone (renderCarteLayer() les redessinait par-dessus,
     dans l'ordre d'empilement Leaflet) -- renderCarteLayer() rappelle
     désormais systématiquement renderVillesLayer() à la fin, pour que les
     villes restent toujours au-dessus.
  3. Le contour orange de sélection dessinait un trait autour de CHAQUE pays
     de la zone séparément (frontières internes visibles) au lieu du
     contour extérieur unique de la zone entière. Nouvelle fonction
     renderSurlignageZone() : fusionne (turf.union) tous les pays/portions
     overlay appartenant à la zone sélectionnée en une seule géométrie, et
     ne dessine QUE son contour extérieur, sans remplissage. Les calques de
     base et overlay n'appliquent plus eux-mêmes de style "surligné".

Nécessite Turf.js (ajouté via CDN dans index.html par ce script -- calcul de
l'union géométrique, fait uniquement côté client, pas de nouvelle route).

Usage, depuis gui/ :
    python3 patch_carte_etape2.py --dry-run
    python3 patch_carte_etape2.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

INDEX_HTML = Path("templates/index.html")
if not INDEX_HTML.exists():
    INDEX_HTML = Path("index.html")

# ── app.js : renderCarteLayer() + toggleVillesPrincipales() + renderVillesLayer() ──
OLD_BLOCK = """function renderCarteLayer() {
  if (!CarteState.rawGeojson) return;
  if (CarteState.geojsonLayer) CarteState.map.removeLayer(CarteState.geojsonLayer);
  if (CarteState.overlaysLayer) CarteState.map.removeLayer(CarteState.overlaysLayer);

  const enToFr = _buildEnToFrIndex();
  const defs = _ensureSvgDefs();
  const zoneFillMap = {};
  CarteState.zonesN1.forEach(z => { zoneFillMap[z.slug] = _zoneFill(defs, z); });

  CarteState.geojsonLayer = L.geoJSON(CarteState.rawGeojson, {
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

      const zone = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
      const fill = zoneFillMap[zone] || '#3b6fd4';
      const estSurlignee = CarteState.zoneSurlignee && zone === CarteState.zoneSurlignee;
      return {
        fillColor: fill,
        weight: estSurlignee ? 4 : 1,
        color: estSurlignee ? '#ff5500' : '#666',
        fillOpacity: estSurlignee ? 1 : 0.85,
      };
    },
    onEachFeature: (feature, layer) => {
      const name = feature.properties?.name || feature.properties?.ADMIN || '';
      const frList = enToFr[_normEn(name)];
      if (!frList) return;
      // En mode dessin, on laisse le clic filer vers Leaflet.Draw (qui pose
      // un sommet du polygone) au lieu de sélectionner le pays -- sinon les
      // deux se déclenchaient en même temps (bug remonté par David, 8 sept).
      layer.on('click', () => { if (!CarteState.modeDessin && !CarteState.modeDessinZoneComplete) onCartePaysClick(frList, name); });
      layer.on('mouseover', () => layer.setStyle({ weight: 2, color: '#222' }));
      layer.on('mouseout', () => layer.setStyle({ weight: 1, color: '#666' }));
      layer.bindTooltip(frList.join(' / '), { sticky: true });
    },
  }).addTo(CarteState.map);

  // Overlays custom : zones qui coupent un pays en deux ou plus. Ajoutée
  // APRÈS la couche pays -- Leaflet empile dans l'ordre d'ajout des couches,
  // donc ces polygones s'affichent bien par-dessus.
  //
  // Refonte (12 sept 2026, point 1) : fillOpacity TOUJOURS à 1 (opaque),
  // même non sélectionné -- avant, 0.85 laissait transparaître le motif
  // hachuré du pays sous-jacent (et, par ricochet, la surbrillance d'une
  // AUTRE zone niveau 1 pouvait rester visible sous un overlay, bug trouvé
  // par David sur bloc_eurasiatique_occidental/Russie-Biélorussie). Couleur
  // et motif viennent de couleur_effective/motif_effectif, déjà résolus par
  // héritage N1 côté serveur (couverture_carte()) -- fonctionne même si
  // zone_slug référence une sous-zone (avant : retombait silencieusement
  // sur un bleu générique dans ce cas).
  if (CarteState.overlays?.features?.length) {
    CarteState.overlaysLayer = L.geoJSON(CarteState.overlays, {
      style: (feature) => {
        const slug = feature.properties?.zone_slug;
        const couleur = feature.properties?.couleur_effective;
        const motif = feature.properties?.motif_effectif;
        const fill = _zoneFill(defs, { slug, color: couleur || '#3b6fd4', motif });
        const estSurlignee = CarteState.zoneSurlignee && slug === CarteState.zoneSurlignee;
        return {
          fillColor: fill,
          weight: estSurlignee ? 4 : 1.5,
          color: estSurlignee ? '#ff5500' : '#333',
          fillOpacity: 1,
          dashArray: '4 3',  // pointillé : signale visuellement "frontière fictive dessinée à la main"
        };
      },
      onEachFeature: (feature, layer) => {
        const slug = feature.properties?.zone_slug;
        const zone = CarteState.zonesN1.find(z => z.slug === slug);
        const label = zone ? `${zone.nom} (${feature.properties?.pays || '?'})` : (slug || '?');
        layer.on('click', () => onCarteZoneOverlayClick(feature.properties || {}));
        layer.on('mouseover', () => layer.setStyle({ weight: 3, color: '#111' }));
        layer.on('mouseout', () => layer.setStyle({ weight: 1.5, color: '#333' }));
        layer.bindTooltip(label, { sticky: true });
      },
    }).addTo(CarteState.map);
  }

  // Diagnostic : pays FR sans correspondance trouvée sur le fond de carte
  const matchedFr = new Set(Object.values(enToFr).flat());
  const allFr = Object.keys(CarteState.faToEn || {}).filter(fr => CarteState.faToEn[fr]);
  const missing = allFr.filter(fr => !matchedFr.has(fr));
  const diagEl = document.getElementById('carte-diagnostic');
  if (missing.length) {
    diagEl.style.display = 'block';
    diagEl.innerHTML = `⚠ ${missing.length} pays non localisés sur le fond de carte (noms à corriger dans gui/static/pays_mapping.json) : ${missing.join(', ')}`;
  } else {
    diagEl.style.display = 'none';
  }
}

// ── Villes principales (12 sept 2026) ───────────────────────────────────

function toggleVillesPrincipales() {
  CarteState.villesVisibles = !CarteState.villesVisibles;
  const btn = document.getElementById('carte-toggle-villes');
  if (btn) btn.classList.toggle('active', CarteState.villesVisibles);
  renderVillesLayer();
}

function renderVillesLayer() {
  if (CarteState.villesLayer) {
    CarteState.map.removeLayer(CarteState.villesLayer);
    CarteState.villesLayer = null;
  }
  if (!CarteState.villesVisibles || !CarteState.villes?.length) return;

  const markers = CarteState.villes.map(v => {
    const rayon = v.capitale ? 5 : 3;
    const marker = L.circleMarker([v.lat, v.lon], {
      radius: rayon,
      weight: 1,
      color: '#fff',
      fillColor: v.capitale ? '#d4342c' : '#333',
      fillOpacity: 0.9,
    });
    const pop = v.population ? `${v.population.toLocaleString('fr-FR')} hab.` : '';
    marker.bindTooltip(`${v.nom}${v.capitale ? ' ★' : ''}${pop ? ' — ' + pop : ''}`, { sticky: true });
    return marker;
  });

  CarteState.villesLayer = L.layerGroup(markers).addTo(CarteState.map);
}
"""

NEW_BLOCK = """function renderCarteLayer() {
  if (!CarteState.rawGeojson) return;
  if (CarteState.geojsonLayer) CarteState.map.removeLayer(CarteState.geojsonLayer);
  if (CarteState.overlaysLayer) CarteState.map.removeLayer(CarteState.overlaysLayer);

  const enToFr = _buildEnToFrIndex();
  const defs = _ensureSvgDefs();
  const zoneFillMap = {};
  CarteState.zonesN1.forEach(z => { zoneFillMap[z.slug] = _zoneFill(defs, z); });

  CarteState.geojsonLayer = L.geoJSON(CarteState.rawGeojson, {
    style: (feature) => {
      const name = feature.properties?.name || feature.properties?.ADMIN || '';
      const frList = enToFr[_normEn(name)];
      if (!frList) return { fillColor: 'transparent', weight: 0.5, color: '#ccc', fillOpacity: 0 };

      // Le calque de base affiche TOUJOURS la couleur de la zone de base du
      // pays, même s'il a par ailleurs un ou plusieurs overlays -- un pays
      // peut être partagé (ex. France : zone_interdite_heysham en base +
      // portion overlay zone_euro_sud). L'overlay, en opacité pleine plus
      // bas, recouvre correctement sa propre portion.
      //
      // La surbrillance ne se fait plus ici (12 sept 2026, étape 2) : un
      // trait orange par pays laissait les frontières internes de la zone
      // visibles. Un contour unique dessiné par renderSurlignageZone(), à la
      // fin de cette fonction, s'en charge désormais -- ce calque garde
      // toujours son style normal, surligné ou non.
      const allNull = frList.every(fr => !CarteState.affectations[fr]);
      if (allNull) return { fillColor: '#999', weight: 1, color: '#666', fillOpacity: 0.5 };

      const zone = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
      const fill = zoneFillMap[zone] || '#3b6fd4';
      return { fillColor: fill, weight: 1, color: '#666', fillOpacity: 0.85 };
    },
    onEachFeature: (feature, layer) => {
      const name = feature.properties?.name || feature.properties?.ADMIN || '';
      const frList = enToFr[_normEn(name)];
      if (!frList) return;
      // En mode dessin, on laisse le clic filer vers Leaflet.Draw (qui pose
      // un sommet du polygone) au lieu de sélectionner le pays -- sinon les
      // deux se déclenchaient en même temps (bug remonté par David, 8 sept).
      layer.on('click', () => { if (!CarteState.modeDessin && !CarteState.modeDessinZoneComplete) onCartePaysClick(frList, name); });
      layer.on('mouseover', () => layer.setStyle({ weight: 2, color: '#222' }));
      layer.on('mouseout', () => layer.setStyle({ weight: 1, color: '#666' }));
      layer.bindTooltip(frList.join(' / '), { sticky: true });
    },
  }).addTo(CarteState.map);

  // Overlays custom : zones qui coupent un pays en deux ou plus. Ajoutée
  // APRÈS la couche pays -- Leaflet empile dans l'ordre d'ajout des couches,
  // donc ces polygones s'affichent bien par-dessus. fillOpacity TOUJOURS à
  // 1 (opaque) -- 0.85 laissait transparaître le motif hachuré du pays
  // sous-jacent. Couleur et motif viennent de couleur_effective/
  // motif_effectif, déjà résolus par héritage N1 côté serveur.
  if (CarteState.overlays?.features?.length) {
    CarteState.overlaysLayer = L.geoJSON(CarteState.overlays, {
      style: (feature) => {
        const slug = feature.properties?.zone_slug;
        const couleur = feature.properties?.couleur_effective;
        const motif = feature.properties?.motif_effectif;
        const fill = _zoneFill(defs, { slug, color: couleur || '#3b6fd4', motif });
        return { fillColor: fill, weight: 1.5, color: '#333', fillOpacity: 1, dashArray: '4 3' };
      },
      onEachFeature: (feature, layer) => {
        const slug = feature.properties?.zone_slug;
        const zone = CarteState.zonesN1.find(z => z.slug === slug);
        const label = zone ? `${zone.nom} (${feature.properties?.pays || '?'})` : (slug || '?');
        layer.on('click', () => onCarteZoneOverlayClick(feature.properties || {}));
        layer.on('mouseover', () => layer.setStyle({ weight: 3, color: '#111' }));
        layer.on('mouseout', () => layer.setStyle({ weight: 1.5, color: '#333' }));
        layer.bindTooltip(label, { sticky: true });
      },
    }).addTo(CarteState.map);
  }

  // Diagnostic : pays FR sans correspondance trouvée sur le fond de carte
  const matchedFr = new Set(Object.values(enToFr).flat());
  const allFr = Object.keys(CarteState.faToEn || {}).filter(fr => CarteState.faToEn[fr]);
  const missing = allFr.filter(fr => !matchedFr.has(fr));
  const diagEl = document.getElementById('carte-diagnostic');
  if (missing.length) {
    diagEl.style.display = 'block';
    diagEl.innerHTML = `⚠ ${missing.length} pays non localisés sur le fond de carte (noms à corriger dans gui/static/pays_mapping.json) : ${missing.join(', ')}`;
  } else {
    diagEl.style.display = 'none';
  }

  // Étape 2 (12 sept 2026) : contour unique de la zone sélectionnée, et
  // villes toujours redessinées en dernier (donc toujours au-dessus) --
  // les deux dépendent de ce que renderCarteLayer() vient de (re)dessiner.
  renderSurlignageZone();
  renderVillesLayer();
}

// ── Surbrillance : contour extérieur unique de la zone sélectionnée ─────
//
// Avant (12 sept 2026) : chaque pays de la zone recevait individuellement
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

  const enToFr = _buildEnToFrIndex();
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
  });

  if (!geometries.length) return;

  let union = geometries[0];
  for (let i = 1; i < geometries.length; i++) {
    try {
      union = turf.union(union, geometries[i]);
    } catch (e) {
      console.warn('turf.union a échoué sur une géométrie (ignorée pour le contour)', e);
    }
  }
  if (!union) return;

  CarteState.surligneLayer = L.geoJSON(union, {
    style: { fill: false, weight: 4, color: '#ff5500' },
    interactive: false,
  }).addTo(CarteState.map);
}

// ── Villes principales (12 sept 2026) ───────────────────────────────────

function toggleVillesPrincipales() {
  CarteState.villesVisibles = !CarteState.villesVisibles;
  const btn = document.getElementById('carte-toggle-villes');
  if (btn) btn.classList.toggle('active', CarteState.villesVisibles);
  renderVillesLayer();
}

function renderVillesLayer() {
  if (CarteState.villesLayer) {
    CarteState.map.removeLayer(CarteState.villesLayer);
    CarteState.villesLayer = null;
  }
  if (!CarteState.villesVisibles || !CarteState.villes?.length) return;

  // Un seul style de marqueur pour toutes les villes (12 sept 2026, sur
  // demande de David -- avant, distinction capitale/autre ville).
  const markers = CarteState.villes.map(v => {
    const marker = L.circleMarker([v.lat, v.lon], {
      radius: 3.5,
      weight: 1,
      color: '#fff',
      fillColor: '#333',
      fillOpacity: 0.9,
    });
    const pop = v.population ? `${v.population.toLocaleString('fr-FR')} hab.` : '';
    marker.bindTooltip(`${v.nom}${pop ? ' — ' + pop : ''}`, { sticky: true });
    return marker;
  });

  CarteState.villesLayer = L.layerGroup(markers).addTo(CarteState.map);
}
"""

# ── app.js : ajout du champ d'état surligneLayer ────────────────────────────
OLD_STATE_TAIL = """  villes: null,          // [{nom,pays,lat,lon,population,capitale}], chargé une seule fois
  villesLayer: null,
  villesVisibles: false,  // off par défaut
};"""

NEW_STATE_TAIL = """  villes: null,          // [{nom,pays,lat,lon,population,capitale}], chargé une seule fois
  villesLayer: null,
  villesVisibles: false,  // off par défaut
  surligneLayer: null,     // contour unique de la zone sélectionnée (turf.union)
};"""

# ── index.html : ajout de Turf.js via CDN, juste après Leaflet Draw ─────────
OLD_SCRIPTS = """<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>"""

NEW_SCRIPTS = """<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
<script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>"""


def _patch_one(path, replacements, label):
    if not path.exists():
        print(f"ERREUR : {path} introuvable.")
        return None
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        n = text.count(old)
        print(f"[{label}] bloc attendu : {n} occurrence(s)")
        if n != 1:
            print(f"  -> ERREUR : attendu exactement 1 occurrence pour ce bloc dans {path}. "
                  "RIEN N'EST ÉCRIT pour ce fichier.")
            return None
        text = text.replace(old, new, 1)
    return text


def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    new_js = _patch_one(APP_JS, [
        (OLD_BLOCK, NEW_BLOCK),
        (OLD_STATE_TAIL, NEW_STATE_TAIL),
    ], "app.js")
    new_html = _patch_one(INDEX_HTML, [
        (OLD_SCRIPTS, NEW_SCRIPTS),
    ], "index.html")

    if new_js is None or new_html is None:
        print("\nAu moins un fichier n'a pas pu être patché -- rien n'a été écrit nulle part.")
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

        r_avant = _check(APP_JS.read_text(encoding="utf-8"), "avant")
        r_apres = _check(new_js, "apres")
        if r_avant.returncode != 0 and r_apres.returncode != 0:
            print("(node --check échoue déjà sur l'original -- non bloquant, comme précédemment.)")
        elif r_avant.returncode == 0 and r_apres.returncode != 0:
            print(f"\nERREUR CRITIQUE (app.js) : {r_apres.stderr}\nRIEN N'EST ÉCRIT.")
            return
        else:
            print("Validation `node --check` (app.js) : OK")

    bak_js = APP_JS.with_suffix(APP_JS.suffix + ".bak4")
    bak_js.write_text(APP_JS.read_text(encoding="utf-8"), encoding="utf-8")
    APP_JS.write_text(new_js, encoding="utf-8")

    bak_html = INDEX_HTML.with_suffix(INDEX_HTML.suffix + ".bak2")
    bak_html.write_text(INDEX_HTML.read_text(encoding="utf-8"), encoding="utf-8")
    INDEX_HTML.write_text(new_html, encoding="utf-8")

    print(f"\n{APP_JS} et {INDEX_HTML} mis à jour. Sauvegardes : {bak_js}, {bak_html}")


if __name__ == "__main__":
    main()
