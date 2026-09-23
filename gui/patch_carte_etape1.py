"""
patch_carte_etape1.py — Étape 1 de la réécriture frontend (rendu de base +
point 1 : le motif du pays ne doit plus transparaître sous un overlay).

Remplace, dans gui/static/app.js (ou app.js à la racine de gui/, ajuste
APP_JS si besoin), deux fonctions EXACTEMENT comme elles existent
aujourd'hui :
  - refreshCarte()     : stocke désormais CarteState.couverture (pays
                         masqués + overlays déjà résolus par héritage N1,
                         venant de la nouvelle réponse /api/carte/affectations)
  - renderCarteLayer() : (a) un pays masqué par un overlay n'affiche plus
                         AUCUN remplissage "pays entier" -- l'overlay est la
                         seule source visuelle à cet endroit ; (b) les
                         overlays passent en fillOpacity 1 (opaque) au lieu
                         de 0.85 -- c'était la fuite visuelle du motif
                         sous-jacent ; (c) la couleur/motif d'un overlay
                         viennent de couleur_effective/motif_effectif déjà
                         résolus côté serveur (fonctionne même si zone_slug
                         référence une sous-zone, contrairement à avant qui
                         retombait sur un bleu générique dans ce cas).

Usage, depuis gui/ :
    python3 patch_carte_etape1.py --dry-run
    python3 patch_carte_etape1.py --apply

Sécurité : .bak avant écriture, validation `node --check` du fichier
résultant avant d'écrire quoi que ce soit (si node est installé -- sinon
avertissement, mais pas de blocage).
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_REFRESH_CARTE = """async function refreshCarte() {
  const scenario = document.getElementById('carte-scenario').value;
  if (!scenario) return;
  CarteState.scenario = scenario;

  const statusEl = document.getElementById('carte-status');
  statusEl.textContent = 'Chargement des affectations…';

  try {
    const [resAff, resOv] = await Promise.all([
      fetch(`/api/carte/affectations?scenario=${encodeURIComponent(scenario)}`),
      fetch(`/api/carte/overlays?scenario=${encodeURIComponent(scenario)}`),
    ]);
    const data = await resAff.json();
    if (data.error) {
      statusEl.textContent = `Erreur : ${data.error}`;
      return;
    }
    CarteState.affectations = data.affectations || {};
    CarteState.zonesN1 = data.zones_n1 || [];

    const ovData = await resOv.json();
    CarteState.overlays = ovData.error ? { type: 'FeatureCollection', features: [] } : ovData;
    if (ovData.error) console.error('Erreur chargement overlays', ovData.error);

    statusEl.textContent = '';
    renderCarteLayer();
    renderCarteLegend();
  } catch (e) {
    statusEl.textContent = `Erreur réseau : ${e.message}`;
  }
}
"""

NEW_REFRESH_CARTE = """async function refreshCarte() {
  const scenario = document.getElementById('carte-scenario').value;
  if (!scenario) return;
  CarteState.scenario = scenario;

  const statusEl = document.getElementById('carte-status');
  statusEl.textContent = 'Chargement des affectations…';

  try {
    // Refonte Carte (12 sept 2026, étape 1) : un seul appel désormais --
    // /api/carte/affectations renvoie déjà couverture.overlays (les mêmes
    // features qu'avant via /api/carte/overlays, mais avec couleur_effective/
    // motif_effectif déjà résolus par héritage N1 côté serveur). Plus besoin
    // du fetch séparé ni de deviner la couleur d'un overlay côté client.
    const res = await fetch(`/api/carte/affectations?scenario=${encodeURIComponent(scenario)}`);
    const data = await res.json();
    if (data.error) {
      statusEl.textContent = `Erreur : ${data.error}`;
      return;
    }
    CarteState.affectations = data.affectations || {};
    CarteState.zonesN1 = data.zones_n1 || [];
    const couverture = data.couverture || { pays_masques: {}, overlays: [] };
    CarteState.couverture = couverture;
    CarteState.overlays = { type: 'FeatureCollection', features: couverture.overlays || [] };

    statusEl.textContent = '';
    renderCarteLayer();
    renderCarteLegend();
  } catch (e) {
    statusEl.textContent = `Erreur réseau : ${e.message}`;
  }
}
"""

OLD_RENDER_CARTE_LAYER = """function renderCarteLayer() {
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
  if (CarteState.overlays?.features?.length) {
    CarteState.overlaysLayer = L.geoJSON(CarteState.overlays, {
      style: (feature) => {
        const slug = feature.properties?.zone_slug;
        const zone = CarteState.zonesN1.find(z => z.slug === slug);
        const fill = zone ? _zoneFill(defs, zone) : '#3b6fd4';
        const estSurlignee = CarteState.zoneSurlignee && slug === CarteState.zoneSurlignee;
        return {
          fillColor: fill,
          weight: estSurlignee ? 4 : 1.5,
          color: estSurlignee ? '#ff5500' : '#333',
          fillOpacity: estSurlignee ? 1 : 0.85,
          dashArray: '4 3',  // pointillé : signale visuellement "frontière fictive dessinée à la main"
        };
      },
      onEachFeature: (feature, layer) => {
        const slug = feature.properties?.zone_slug;
        const zone = CarteState.zonesN1.find(z => z.slug === slug);
        const label = zone ? `${zone.nom} (${feature.properties?.pays || '?'})` : slug;
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
"""

NEW_RENDER_CARTE_LAYER = """function renderCarteLayer() {
  if (!CarteState.rawGeojson) return;
  if (CarteState.geojsonLayer) CarteState.map.removeLayer(CarteState.geojsonLayer);
  if (CarteState.overlaysLayer) CarteState.map.removeLayer(CarteState.overlaysLayer);

  const enToFr = _buildEnToFrIndex();
  const defs = _ensureSvgDefs();
  const zoneFillMap = {};
  CarteState.zonesN1.forEach(z => { zoneFillMap[z.slug] = _zoneFill(defs, z); });

  // Refonte Carte (12 sept 2026, point 1) : un pays couvert par au moins un
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
"""


def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not APP_JS.exists():
        print("ERREUR : app.js introuvable (cherché dans static/app.js et ./app.js) -- "
              "lance ce script depuis gui/, ou ajuste APP_JS dans le script.")
        return

    text = APP_JS.read_text(encoding="utf-8")

    n_refresh = text.count(OLD_REFRESH_CARTE)
    n_render = text.count(OLD_RENDER_CARTE_LAYER)

    print(f"refreshCarte()     : {n_refresh} occurrence(s) exacte(s) trouvée(s)")
    print(f"renderCarteLayer() : {n_render} occurrence(s) exacte(s) trouvée(s)")

    if n_refresh != 1 or n_render != 1:
        print("\nERREUR : chaque fonction doit apparaître EXACTEMENT une fois pour un "
              "remplacement sûr. Le fichier a probablement divergé de la version sur "
              "laquelle ce patch a été préparé (espaces, commentaires, ou modifs "
              "entre-temps) -- RIEN N'EST ÉCRIT. Dis-moi ce que montre ce diagnostic, "
              "je regénère le patch en conséquence plutôt que de deviner.")
        return

    new_text = text.replace(OLD_REFRESH_CARTE, NEW_REFRESH_CARTE, 1)
    new_text = new_text.replace(OLD_RENDER_CARTE_LAYER, NEW_RENDER_CARTE_LAYER, 1)

    print(f"\nTaille avant : {len(text)} caractères -- après : {len(new_text)} caractères")

    if args.dry_run:
        print("\n[dry-run] Aucun fichier modifié. Relance avec --apply pour écrire réellement.")
        return

    node = shutil.which("node")
    if node:
        # Validation syntaxique : on compare l'AVANT et l'APRÈS avec la même
        # commande. Si l'ORIGINAL échoue déjà (ex. Node trop ancien pour une
        # syntaxe déjà présente ailleurs dans le fichier, sans rapport avec ce
        # patch), on ne bloque pas dessus -- seule une régression réelle
        # (l'original passe, le résultat casse) est traitée comme une erreur.
        def _check(content, label):
            tmp = APP_JS.with_name(f"app_tmp_check_{label}.js")
            tmp.write_text(content, encoding="utf-8")
            result = subprocess.run([node, "--check", str(tmp)], capture_output=True, text=True)
            tmp.unlink()
            return result

        result_avant = _check(text, "avant")
        result_apres = _check(new_text, "apres")

        if result_avant.returncode != 0 and result_apres.returncode != 0:
            print("\n(node --check échoue déjà sur l'ORIGINAL -- probablement une syntaxe "
                  "moderne que ta version de Node ne supporte pas, sans rapport avec ce "
                  "patch. Validation non bloquante dans ce cas précis.)")
        elif result_avant.returncode == 0 and result_apres.returncode != 0:
            print(f"\nERREUR CRITIQUE : le résultat ne serait plus un JavaScript valide "
                  f"alors que l'original l'était :\n{result_apres.stderr}\n"
                  "RIEN N'EST ÉCRIT, app.js inchangé.")
            return
        else:
            print("\nValidation `node --check` : OK")
    else:
        print("\n(node introuvable -- validation syntaxique sautée, pas bloquant)")

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak")
    bak.write_text(text, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde de l'ancienne version : {bak}")


if __name__ == "__main__":
    main()
