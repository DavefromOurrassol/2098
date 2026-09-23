"""
patch_carte_villes.py — Ajoute l'affichage des villes principales sur la
carte (capitales, mégapoles, villes > seuil de population) : un bouton
toggle dans la barre d'outils, une couche Leaflet de marqueurs, chargée une
seule fois depuis /api/carte/villes (géographie réelle, indépendante du
scénario -- pas rechargée à chaque changement de scénario).

Patche deux fichiers :
  - gui/static/app.js    (ou gui/app.js) : état + chargement + rendu
  - gui/templates/index.html (ou gui/index.html) : bouton toggle

Usage, depuis gui/ :
    python3 patch_carte_villes.py --dry-run
    python3 patch_carte_villes.py --apply
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

# ── app.js : ajout de 2 champs d'état (insertion ciblée, pas de remplacement
#    du bloc entier -- moins fragile si le bloc a bougé ailleurs) ───────────
OLD_STATE_TAIL = """  searchDebounceTimer: null,
  origineReelleParSlug: {},  // slug -> origine_reelle, reconstruit à chaque ouverture d'arbre (split)
};"""

NEW_STATE_TAIL = """  searchDebounceTimer: null,
  origineReelleParSlug: {},  // slug -> origine_reelle, reconstruit à chaque ouverture d'arbre (split)
  villes: null,          // [{nom,pays,lat,lon,population,capitale}], chargé une seule fois
  villesLayer: null,
  villesVisibles: false,  // off par défaut
};"""

# ── app.js : chargement une seule fois dans loadCarte() ─────────────────────
OLD_LOADCARTE_FATOEN = """  if (!CarteState.faToEn) {
    try {
      const res = await fetch('/static/pays_mapping.json');
      CarteState.faToEn = await res.json();
    } catch (e) {
      console.error('Erreur chargement pays_mapping.json', e);
      CarteState.faToEn = {};
    }
  }
"""

NEW_LOADCARTE_FATOEN = """  if (!CarteState.faToEn) {
    try {
      const res = await fetch('/static/pays_mapping.json');
      CarteState.faToEn = await res.json();
    } catch (e) {
      console.error('Erreur chargement pays_mapping.json', e);
      CarteState.faToEn = {};
    }
  }

  if (!CarteState.villes) {
    try {
      const res = await fetch('/api/carte/villes');
      const data = await res.json();
      CarteState.villes = Array.isArray(data) ? data : [];
    } catch (e) {
      console.error('Erreur chargement villes_principales.json', e);
      CarteState.villes = [];
    }
  }
"""

# ── app.js : nouvelles fonctions, insérées juste après renderCarteLayer() ──
ANCHOR_APRES_RENDER_CARTE_LAYER = "\n// ── Overlays custom : dessin, création, suppression (26 août 2026) ─────────\n"

NEW_FUNCTIONS = """
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

""" + ANCHOR_APRES_RENDER_CARTE_LAYER

# ── index.html : bouton toggle dans la barre d'outils ───────────────────────
OLD_TOOLBAR_TAIL = """        <button id="carte-toggle-overlays-liste" class="btn-secondary" style="margin-left:6px" onclick="openOverlaysListePanel()">🗑️ Gérer les overlays</button>
        <span id="carte-status" class="carte-status"></span>"""

NEW_TOOLBAR_TAIL = """        <button id="carte-toggle-overlays-liste" class="btn-secondary" style="margin-left:6px" onclick="openOverlaysListePanel()">🗑️ Gérer les overlays</button>
        <button id="carte-toggle-villes" class="btn-secondary" style="margin-left:6px" onclick="toggleVillesPrincipales()">🏙️ Villes principales</button>
        <span id="carte-status" class="carte-status"></span>"""

# ── index.html : style visuel de l'état actif du bouton ─────────────────────
OLD_CSS_TAIL = """    .carte-toolbar select { font-family: 'JetBrains Mono', monospace; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; background: #fff; }"""

NEW_CSS_TAIL = """    .carte-toolbar select { font-family: 'JetBrains Mono', monospace; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; background: #fff; }
    #carte-toggle-villes.active { border-color: #3b6fd4; background: #eef4fa; color: #2a52a8; font-weight: 600; }"""


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
        (OLD_STATE_TAIL, NEW_STATE_TAIL),
        (OLD_LOADCARTE_FATOEN, NEW_LOADCARTE_FATOEN),
        (ANCHOR_APRES_RENDER_CARTE_LAYER, NEW_FUNCTIONS),
    ], "app.js")
    new_html = _patch_one(INDEX_HTML, [
        (OLD_TOOLBAR_TAIL, NEW_TOOLBAR_TAIL),
        (OLD_CSS_TAIL, NEW_CSS_TAIL),
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

    bak_js = APP_JS.with_suffix(APP_JS.suffix + ".bak3")
    bak_js.write_text(APP_JS.read_text(encoding="utf-8"), encoding="utf-8")
    APP_JS.write_text(new_js, encoding="utf-8")

    bak_html = INDEX_HTML.with_suffix(INDEX_HTML.suffix + ".bak")
    bak_html.write_text(INDEX_HTML.read_text(encoding="utf-8"), encoding="utf-8")
    INDEX_HTML.write_text(new_html, encoding="utf-8")

    print(f"\n{APP_JS} et {INDEX_HTML} mis à jour. Sauvegardes : {bak_js}, {bak_html}")


if __name__ == "__main__":
    main()
