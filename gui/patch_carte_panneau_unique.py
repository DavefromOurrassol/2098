"""
patch_carte_panneau_unique.py — Point 4 de la demande initiale de David :
"pas besoin de plusieurs menus overlay, dessin, un seul menu où je trouve
des options". Regroupe dans le panneau ✏️ (renommer + couleur/motif/
hachures, déjà existant) : la liste des overlays de CETTE zone (avec
suppression) et un bouton pour dessiner un nouvel overlay DIRECTEMENT pour
cette zone (sans repasser par le sélecteur générique de zone). Retire les
boutons globaux "✏️ Dessiner un overlay" et "🗑️ Gérer les overlays" de la
barre d'outils, désormais redondants.

Note : "🗺️ Dessiner une zone complète" (S11, mécanisme différent -- dessiner
le contour d'une NOUVELLE zone plutôt qu'un overlay pour une zone
existante) n'est pas concerné, reste dans la barre d'outils.

Usage, depuis gui/ :
    python3 patch_carte_panneau_unique.py --dry-run
    python3 patch_carte_panneau_unique.py --apply
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

# ── index.html : retire les 2 boutons devenus redondants ────────────────────
OLD_TOOLBAR = """        <button id="carte-toggle-dessin" class="btn-secondary" style="margin-left:12px" onclick="toggleModeDessin()">✏️ Dessiner un overlay</button>
        <button id="carte-toggle-dessin-zone-complete" class="btn-secondary" style="margin-left:12px" onclick="toggleModeDessinZoneComplete()">🗺️ Dessiner une zone complète</button>
        <button id="carte-toggle-enrichissement" class="btn-secondary" style="margin-left:6px" onclick="openEnrichissementPanel()">🧬 Zones à enrichir</button>
        <button id="carte-toggle-overlays-liste" class="btn-secondary" style="margin-left:6px" onclick="openOverlaysListePanel()">🗑️ Gérer les overlays</button>
        <button id="carte-toggle-villes" class="btn-secondary" style="margin-left:6px" onclick="toggleVillesPrincipales()">🏙️ Villes principales</button>"""

NEW_TOOLBAR = """        <button id="carte-toggle-dessin-zone-complete" class="btn-secondary" style="margin-left:12px" onclick="toggleModeDessinZoneComplete()">🗺️ Dessiner une zone complète</button>
        <button id="carte-toggle-enrichissement" class="btn-secondary" style="margin-left:6px" onclick="openEnrichissementPanel()">🧬 Zones à enrichir</button>
        <button id="carte-toggle-villes" class="btn-secondary" style="margin-left:6px" onclick="toggleVillesPrincipales()">🏙️ Villes principales</button>"""

# ── app.js : dessin pré-sélectionné pour une zone donnée ────────────────────
OLD_DRAW_CREATED_HEAD = """  const scenario = CarteState.scenario;
  const zoneSlug = await _promptZoneSlug(scenario);
  if (!zoneSlug) {
    CarteState.drawnItemsLayer.clearLayers();
    _relancerSiModeActif();
    return;
  }"""

NEW_DRAW_CREATED_HEAD = """  const scenario = CarteState.scenario;
  // Panneau unique (12 sept 2026) : si un dessin a été lancé depuis le
  // panneau d'une zone précise, on saute le sélecteur générique -- usage
  // unique, retombe ensuite sur le sélecteur classique pour le prochain
  // polygone si le mode dessin reste actif.
  const zonePreselectionnee = CarteState.dessinZonePreselectionnee;
  CarteState.dessinZonePreselectionnee = null;
  const zoneSlug = zonePreselectionnee || await _promptZoneSlug(scenario);
  if (!zoneSlug) {
    CarteState.drawnItemsLayer.clearLayers();
    _relancerSiModeActif();
    return;
  }"""

OLD_DRAW_CREATED_TAIL = """    statusEl.textContent = data.origine_reelle_creee
      ? `Overlay créé, origine_reelle ajoutée à '${zoneSlug}' (${data.total_features} overlay(s) au total).`
      : `Overlay créé (${data.total_features} au total pour ce scénario).`;
    CarteState.drawnItemsLayer.clearLayers();
    await refreshCarte();  // recharge overlays + réaffiche
    _relancerSiModeActif();"""

NEW_DRAW_CREATED_TAIL = """    statusEl.textContent = data.origine_reelle_creee
      ? `Overlay créé, origine_reelle ajoutée à '${zoneSlug}' (${data.total_features} overlay(s) au total).`
      : `Overlay créé (${data.total_features} au total pour ce scénario).`;
    CarteState.drawnItemsLayer.clearLayers();
    await refreshCarte();  // recharge overlays + réaffiche
    if (zonePreselectionnee) openRenommerZonePanel(zonePreselectionnee);  // réaffiche le panneau à jour
    _relancerSiModeActif();"""

# ── app.js : ajout de l'état + la fonction de démarrage ciblé ───────────────
OLD_STATE_TAIL = """  surligneLayer: null,     // contour unique de la zone sélectionnée (turf.union)
};"""

NEW_STATE_TAIL = """  surligneLayer: null,     // contour unique de la zone sélectionnée (turf.union)
  dessinZonePreselectionnee: null,  // slug pré-choisi pour le prochain overlay dessiné (panneau unique)
};"""

# ── app.js : openRenommerZonePanel -- ajout de la section overlays ──────────
OLD_PANEL = """  panel.innerHTML = `
    <div class="carte-panel-title">Renommer : ${z ? z.nom : ancienSlug}</div>
    <div class="carte-panel-sub">Slug actuel : ${ancienSlug}</div>

    <div class="carte-panel-section">
      <label>Nouveau slug</label>
      <input type="text" id="renommer-nouveau-slug" value="${ancienSlug}"
             style="width:100%;font-family:'JetBrains Mono',monospace;font-size:11px;padding:4px;margin-bottom:6px">
      <label>Nouveau nom affiché</label>
      <input type="text" id="renommer-nouveau-nom" value="${z ? z.nom : ''}"
             style="width:100%;font-size:11px;padding:4px;margin-bottom:6px">
      <button id="renommer-impact-btn" class="yaml-btn">🔍 Évaluer l'impact</button>
      <div id="renommer-impact-report"></div>
    </div>

    <div class="carte-panel-section">
      <label>Couleur / motif</label>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:4px;">
        <label>Couleur :
          <input type="color" id="perso-legende-couleur" value="${couleurActuelle || (z ? z.color : '#3b6fd4')}">
        </label>
        <label>
          <input type="checkbox" id="perso-legende-auto" ${couleurActuelle ? '' : 'checked'}> auto
        </label>
        <label>Motif :
          <select id="perso-legende-motif">${motifOptions}</select>
        </label>
        <label title="Hachures génériques en plus de la couleur -- désactivées par défaut">
          <input type="checkbox" id="perso-legende-hachures" ${hachuresActuel ? 'checked' : ''}> hachures
        </label>
        <button class="yaml-btn" id="perso-legende-appliquer">✓ Appliquer</button>
        <span id="perso-legende-msg" style="font-size:10px;"></span>
      </div>
    </div>

    <div id="carte-panel-msg"></div>
  `;"""

NEW_PANEL = """  const overlaysDeCetteZone = (CarteState.overlays?.features || [])
    .filter(f => f.properties?.zone_slug === ancienSlug);

  const overlaysHtml = overlaysDeCetteZone.length
    ? overlaysDeCetteZone.map(f => `
        <div style="border:1px solid #eee;border-radius:4px;padding:6px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;font-size:11px;">
          <div>
            <strong>${f.properties.pays || '?'}</strong>
            ${f.properties.portion_source ? `<div style="color:#888;">${f.properties.portion_source}</div>` : ''}
          </div>
          <button class="btn-secondary renommer-overlay-supprimer-btn" data-id="${f.properties.id}">🗑️</button>
        </div>
      `).join('')
    : '<div style="font-size:11px;color:#888;">Aucun overlay pour cette zone.</div>';

  panel.innerHTML = `
    <div class="carte-panel-title">Renommer : ${z ? z.nom : ancienSlug}</div>
    <div class="carte-panel-sub">Slug actuel : ${ancienSlug}</div>

    <div class="carte-panel-section">
      <label>Nouveau slug</label>
      <input type="text" id="renommer-nouveau-slug" value="${ancienSlug}"
             style="width:100%;font-family:'JetBrains Mono',monospace;font-size:11px;padding:4px;margin-bottom:6px">
      <label>Nouveau nom affiché</label>
      <input type="text" id="renommer-nouveau-nom" value="${z ? z.nom : ''}"
             style="width:100%;font-size:11px;padding:4px;margin-bottom:6px">
      <button id="renommer-impact-btn" class="yaml-btn">🔍 Évaluer l'impact</button>
      <div id="renommer-impact-report"></div>
    </div>

    <div class="carte-panel-section">
      <label>Couleur / motif</label>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:4px;">
        <label>Couleur :
          <input type="color" id="perso-legende-couleur" value="${couleurActuelle || (z ? z.color : '#3b6fd4')}">
        </label>
        <label>
          <input type="checkbox" id="perso-legende-auto" ${couleurActuelle ? '' : 'checked'}> auto
        </label>
        <label>Motif :
          <select id="perso-legende-motif">${motifOptions}</select>
        </label>
        <label title="Hachures génériques en plus de la couleur -- désactivées par défaut">
          <input type="checkbox" id="perso-legende-hachures" ${hachuresActuel ? 'checked' : ''}> hachures
        </label>
        <button class="yaml-btn" id="perso-legende-appliquer">✓ Appliquer</button>
        <span id="perso-legende-msg" style="font-size:10px;"></span>
      </div>
    </div>

    <div class="carte-panel-section">
      <label>Overlays de cette zone (${overlaysDeCetteZone.length})</label>
      <div id="renommer-overlays-liste" style="margin-top:4px;">${overlaysHtml}</div>
      <button id="renommer-dessiner-overlay-btn" class="yaml-btn" style="margin-top:6px;">✏️ Dessiner un nouvel overlay pour cette zone</button>
    </div>

    <div id="carte-panel-msg"></div>
  `;"""

# ── app.js : câblage des nouveaux boutons, juste avant la fin de la fonction ─
OLD_WIRING_TAIL = """  document.getElementById('perso-legende-appliquer').addEventListener('click', async () => {
    const msgEl = document.getElementById('perso-legende-msg');
    msgEl.textContent = 'Enregistrement…';
    const motifChoisi = document.getElementById('perso-legende-motif').value;
    const body = {
      scenario: CarteState.scenario,
      slug: ancienSlug,
      couleur: autoCheckbox.checked ? null : couleurInput.value,
      motif: motifChoisi || null,
      hachures: document.getElementById('perso-legende-hachures').checked,
    };
    try {
      const res = await fetch('/api/carte/personnaliser_zone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (data.error) { msgEl.textContent = `Erreur : ${data.error}`; return; }
      msgEl.textContent = '✓ Appliqué.';
      await refreshCarte();
    } catch (e) {
      msgEl.textContent = `Erreur réseau : ${e.message}`;
    }
  });
}"""

NEW_WIRING_TAIL = """  document.getElementById('perso-legende-appliquer').addEventListener('click', async () => {
    const msgEl = document.getElementById('perso-legende-msg');
    msgEl.textContent = 'Enregistrement…';
    const motifChoisi = document.getElementById('perso-legende-motif').value;
    const body = {
      scenario: CarteState.scenario,
      slug: ancienSlug,
      couleur: autoCheckbox.checked ? null : couleurInput.value,
      motif: motifChoisi || null,
      hachures: document.getElementById('perso-legende-hachures').checked,
    };
    try {
      const res = await fetch('/api/carte/personnaliser_zone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (data.error) { msgEl.textContent = `Erreur : ${data.error}`; return; }
      msgEl.textContent = '✓ Appliqué.';
      await refreshCarte();
    } catch (e) {
      msgEl.textContent = `Erreur réseau : ${e.message}`;
    }
  });

  panel.querySelectorAll('.renommer-overlay-supprimer-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!window.confirm('Supprimer cet overlay ? (le texte origine_reelle associé, lui, reste inchangé)')) return;
      btn.disabled = true;
      btn.textContent = '…';
      await _supprimerOverlay(btn.dataset.id);
      openRenommerZonePanel(ancienSlug);  // réaffiche le panneau à jour
    });
  });

  document.getElementById('renommer-dessiner-overlay-btn').addEventListener('click', () => {
    demarrerDessinPourZone(ancienSlug);
  });
}

// ── Panneau unique (12 sept 2026) : lance le dessin d'overlay directement
// pour la zone dont le panneau est ouvert, sans repasser par le sélecteur
// générique de zone (_promptZoneSlug).
function demarrerDessinPourZone(slug) {
  CarteState.dessinZonePreselectionnee = slug;
  if (!CarteState.modeDessin) toggleModeDessin();
  document.getElementById('carte-status').textContent =
    `Mode dessin actif pour "${slug}" — clique sur la carte pour poser chaque sommet du polygone, double-clic pour le fermer.`;
}"""


def _patch(text, replacements, label):
    for old, new in replacements:
        n = text.count(old)
        print(f"[{label}] bloc attendu : {n} occurrence(s)")
        if n != 1:
            print(f"  -> ERREUR : attendu exactement 1 occurrence. RIEN N'EST ÉCRIT pour ce fichier.")
            return None
        text = text.replace(old, new, 1)
    return text


def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    original_js = APP_JS.read_text(encoding="utf-8") if APP_JS.exists() else None
    original_html = INDEX_HTML.read_text(encoding="utf-8") if INDEX_HTML.exists() else None
    if original_js is None or original_html is None:
        print("ERREUR : app.js ou index.html introuvable.")
        return

    new_js = _patch(original_js, [
        (OLD_DRAW_CREATED_HEAD, NEW_DRAW_CREATED_HEAD),
        (OLD_DRAW_CREATED_TAIL, NEW_DRAW_CREATED_TAIL),
        (OLD_STATE_TAIL, NEW_STATE_TAIL),
        (OLD_PANEL, NEW_PANEL),
        (OLD_WIRING_TAIL, NEW_WIRING_TAIL),
    ], "app.js")
    new_html = _patch(original_html, [
        (OLD_TOOLBAR, NEW_TOOLBAR),
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

        r_avant, r_apres = _check(original_js, "avant"), _check(new_js, "apres")
        if r_avant.returncode != 0 and r_apres.returncode != 0:
            print("(node --check échoue déjà sur l'original -- non bloquant, comme précédemment.)")
        elif r_avant.returncode == 0 and r_apres.returncode != 0:
            print(f"\nERREUR CRITIQUE (app.js) : {r_apres.stderr}\nRIEN N'EST ÉCRIT.")
            return
        else:
            print("Validation `node --check` (app.js) : OK")

    bak_js = APP_JS.with_suffix(APP_JS.suffix + ".bak11")
    bak_js.write_text(original_js, encoding="utf-8")
    APP_JS.write_text(new_js, encoding="utf-8")

    bak_html = INDEX_HTML.with_suffix(INDEX_HTML.suffix + ".bak3")
    bak_html.write_text(original_html, encoding="utf-8")
    INDEX_HTML.write_text(new_html, encoding="utf-8")

    print(f"\n{APP_JS} et {INDEX_HTML} mis à jour. Sauvegardes : {bak_js}, {bak_html}")


if __name__ == "__main__":
    main()
