"""
patch_carte_unification.py — Unifie les deux façons de modifier une zone
(légende vs boutons de l'arbre) en un seul point d'entrée, sur demande de
David (12 sept 2026) :

  1. Les sous-zones (niveau 2/3) n'ont plus AUCUN bouton d'édition sauf
     "déplacer" (reparent) -- scinder/réviser/personnaliser retirés.
  2. Les zones niveau 1 n'ont plus qu'UN bouton "éditer" dans l'arbre (en
     plus de "déplacer" et "réviser", conservés tels quels) -- scinder et
     personnaliser (couleur/motif/hachures) disparaissent de l'arbre,
     fusionnés dans le même panneau que la légende.
  3. Le panneau (openRenommerZonePanel, désormais commun légende+arbre)
     remplace la section "Overlays de cette zone" par "Pays & portions de
     cette zone" : une ligne par entrée origine_reelle, avec "déplacer"
     (= scinder CETTE entrée précise vers une autre zone, sans repasser par
     un formulaire multi-sélection séparé) et "dessiner"/"retirer le tracé"
     selon qu'un overlay existe déjà pour elle. Un bouton "+ Ajouter un
     nouveau pays" reste disponible pour un pays pas encore dans
     origine_reelle.

Nécessite patch_carte_panneau_unique.py déjà appliqué (ce patch construit
dessus).

Usage, depuis gui/ :
    python3 patch_carte_unification.py --dry-run
    python3 patch_carte_unification.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

# ── 1) état : dessinPaysPreselectionne ──────────────────────────────────────
OLD_STATE_TAIL = """  dessinZonePreselectionnee: null,  // slug pré-choisi pour le prochain overlay dessiné (panneau unique)
};"""

NEW_STATE_TAIL = """  dessinZonePreselectionnee: null,  // slug pré-choisi pour le prochain overlay dessiné (panneau unique)
  dessinPaysPreselectionne: null,   // pays pré-choisi (dessin depuis une ligne "Pays & portions")
};"""

# ── 2) onCarteOverlayDrawCreated : saute _promptPays si pays pré-choisi ────
OLD_DRAW_PAYS = """  const choixPays = await _promptPays(scenario, zoneSlug);
  if (!choixPays) {
    CarteState.drawnItemsLayer.clearLayers();
    _relancerSiModeActif();
    return;
  }
  const { pays, estNouveau } = choixPays;"""

NEW_DRAW_PAYS = """  const paysPreselectionne = CarteState.dessinPaysPreselectionne;
  CarteState.dessinPaysPreselectionne = null;
  const choixPays = paysPreselectionne
    ? { pays: paysPreselectionne, estNouveau: false }
    : await _promptPays(scenario, zoneSlug);
  if (!choixPays) {
    CarteState.drawnItemsLayer.clearLayers();
    _relancerSiModeActif();
    return;
  }
  const { pays, estNouveau } = choixPays;"""

# ── 3) arbre : wiring + _renderArbreNode -- un seul bouton éditer pour N1,
#    plus rien que déplacer pour les sous-zones ─────────────────────────────
OLD_ARBRE = """    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-move-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirReparentPanel(btn.dataset.slug, btn.dataset.nom));
    });

    CarteState.origineReelleParSlug = {};
    (function indexer(node) {
      CarteState.origineReelleParSlug[node.slug] = node.origine_reelle || [];
      (node.enfants || []).forEach(indexer);
    })(data.arbre);

    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-split-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirSplitPanel(btn.dataset.slug, btn.dataset.nom));
    });

    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-topdown-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirTopdownRevisionPanel(btn.dataset.slug, btn.dataset.nom));
    });

    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-perso-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirPersoPanel(btn.dataset.slug, btn.dataset.couleur, btn.dataset.motif, btn.dataset.hachures === '1'));
    });
  } catch (e) {
    panel.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

function _renderArbreNode(node, estRacine) {
  const typeLabel = node.type ? `<span class="arbre-zone-type">${node.type}</span>` : '';
  const statutLabel = node.statut ? `<span class="arbre-zone-statut">${node.statut}</span>` : '';

  let html = `<div class="arbre-zone-branch">`;
  html += `<div class="arbre-zone-node-row arbre-niveau-${node.niveau}" data-slug="${node.slug}">`;
  html += `<span class="arbre-zone-nom">${node.nom}</span>`;
  html += `<span class="arbre-zone-slug">${node.slug}</span>`;
  html += `${typeLabel}${statutLabel}`;
  if (!estRacine) {
    html += `<button class="arbre-zone-move-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Déplacer vers un autre parent">↗️ déplacer</button>`;
  } else if (node.niveau === 1) {
    // Corrige un trou trouvé le 8 sept 2026 : la racine de l'arbre affiché
    // n'avait jamais ce bouton (masqué par le `!estRacine` ci-dessus), donc
    // une zone niveau 1 ouverte depuis la légende (toujours racine dans ce
    // contexte) ne pouvait JAMAIS être rétrogradée en sous-zone d'une autre
    // zone niveau 1 -- alors que /api/carte/reparent_zone le gère très bien
    // dans les deux sens. Condition sur niveau===1 : une racine de niveau
    // 2/3 affichée ailleurs (ex. panneau dédié) passe déjà par le cas
    // !estRacine normalement, ce cas-ci vise spécifiquement le trou niveau 1.
    html += `<button class="arbre-zone-move-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Déplacer vers un autre parent (rétrograder cette zone niveau 1 en sous-zone)">↗️ déplacer</button>`;
  }
  if ((node.origine_reelle || []).length > 1) {
    html += `<button class="arbre-zone-split-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Sortir un ou plusieurs pays de cette zone vers une autre">✂️ scinder</button>`;
  }
  if (node.niveau === 1) {
    html += `<button class="arbre-zone-topdown-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="P24 étape C — réviser cette zone contre le patron spatial narratif du scénario (ex. suite à un signalement check_patron_spatial_coherence.py)">🧭 réviser (patron spatial)</button>`;
  }
  html += `<button class="arbre-zone-perso-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" data-couleur="${node.couleur || ''}" data-motif="${node.motif || ''}" data-hachures="${node.hachures ? '1' : ''}" title="Choisir une couleur et/ou un motif pour cette zone">🎨 personnaliser</button>`;
  html += `</div>`;
  html += `<div id="reparent-panel-${node.slug}"></div>`;
  html += `<div id="split-panel-${node.slug}"></div>`;
  html += `<div id="topdown-panel-${node.slug}"></div>`;
  html += `<div id="perso-panel-${node.slug}"></div>`;

  if (node.enfants && node.enfants.length) {
    html += `<div class="arbre-zone-children">`;
    html += node.enfants.map(c => _renderArbreNode(c, false)).join('');
    html += `</div>`;
  }
  html += `</div>`;
  return html;
}"""

NEW_ARBRE = """    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-move-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirReparentPanel(btn.dataset.slug, btn.dataset.nom));
    });

    CarteState.origineReelleParSlug = {};
    (function indexer(node) {
      CarteState.origineReelleParSlug[node.slug] = node.origine_reelle || [];
      (node.enfants || []).forEach(indexer);
    })(data.arbre);

    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-topdown-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirTopdownRevisionPanel(btn.dataset.slug, btn.dataset.nom));
    });

    // Point d'entrée unique (12 sept 2026) : scinder et personnaliser
    // (couleur/motif/hachures) ont été retirés de l'arbre, fusionnés dans
    // openRenommerZonePanel (même panneau que la légende) -- voir sa
    // section "Pays & portions de cette zone".
    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-editer-btn').forEach(btn => {
      btn.addEventListener('click', () => openRenommerZonePanel(btn.dataset.slug));
    });
  } catch (e) {
    panel.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

function _renderArbreNode(node, estRacine) {
  const typeLabel = node.type ? `<span class="arbre-zone-type">${node.type}</span>` : '';
  const statutLabel = node.statut ? `<span class="arbre-zone-statut">${node.statut}</span>` : '';

  let html = `<div class="arbre-zone-branch">`;
  html += `<div class="arbre-zone-node-row arbre-niveau-${node.niveau}" data-slug="${node.slug}">`;
  html += `<span class="arbre-zone-nom">${node.nom}</span>`;
  html += `<span class="arbre-zone-slug">${node.slug}</span>`;
  html += `${typeLabel}${statutLabel}`;
  if (!estRacine) {
    html += `<button class="arbre-zone-move-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Déplacer vers un autre parent">↗️ déplacer</button>`;
  } else if (node.niveau === 1) {
    // Corrige un trou trouvé le 8 sept 2026 : la racine de l'arbre affiché
    // n'avait jamais ce bouton (masqué par le `!estRacine` ci-dessus), donc
    // une zone niveau 1 ouverte depuis la légende (toujours racine dans ce
    // contexte) ne pouvait JAMAIS être rétrogradée en sous-zone d'une autre
    // zone niveau 1 -- alors que /api/carte/reparent_zone le gère très bien
    // dans les deux sens. Condition sur niveau===1 : une racine de niveau
    // 2/3 affichée ailleurs (ex. panneau dédié) passe déjà par le cas
    // !estRacine normalement, ce cas-ci vise spécifiquement le trou niveau 1.
    html += `<button class="arbre-zone-move-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Déplacer vers un autre parent (rétrograder cette zone niveau 1 en sous-zone)">↗️ déplacer</button>`;
  }
  if (node.niveau === 1) {
    html += `<button class="arbre-zone-topdown-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="P24 étape C — réviser cette zone contre le patron spatial narratif du scénario (ex. suite à un signalement check_patron_spatial_coherence.py)">🧭 réviser (patron spatial)</button>`;
    html += `<button class="arbre-zone-editer-btn" data-slug="${node.slug}" title="Éditer cette zone : renommer, couleur/motif/hachures, pays et overlays">✏️ éditer</button>`;
  }
  html += `</div>`;
  html += `<div id="reparent-panel-${node.slug}"></div>`;
  html += `<div id="topdown-panel-${node.slug}"></div>`;

  if (node.enfants && node.enfants.length) {
    html += `<div class="arbre-zone-children">`;
    html += node.enfants.map(c => _renderArbreNode(c, false)).join('');
    html += `</div>`;
  }
  html += `</div>`;
  return html;
}"""

# ── 4) fetch arbre_zone : capture aussi origine_reelle (même appel réseau) ─
OLD_FETCH_ARBRE = """  let couleurActuelle = null, motifActuel = null, hachuresActuel = false;
  try {
    const res = await fetch(`/api/carte/arbre_zone?scenario=${encodeURIComponent(CarteState.scenario)}&slug=${encodeURIComponent(ancienSlug)}`);
    const data = await res.json();
    if (data.arbre) {
      couleurActuelle = data.arbre.couleur || null;
      motifActuel = data.arbre.motif || null;
      hachuresActuel = !!data.arbre.hachures;
    }
  } catch (e) {
    // Non bloquant : le panneau s'ouvre quand même, juste sans préremplissage.
  }"""

NEW_FETCH_ARBRE = """  let couleurActuelle = null, motifActuel = null, hachuresActuel = false, origineReelleZone = [];
  try {
    const res = await fetch(`/api/carte/arbre_zone?scenario=${encodeURIComponent(CarteState.scenario)}&slug=${encodeURIComponent(ancienSlug)}`);
    const data = await res.json();
    if (data.arbre) {
      couleurActuelle = data.arbre.couleur || null;
      motifActuel = data.arbre.motif || null;
      hachuresActuel = !!data.arbre.hachures;
      origineReelleZone = data.arbre.origine_reelle || [];
    }
  } catch (e) {
    // Non bloquant : le panneau s'ouvre quand même, juste sans préremplissage.
  }"""

# ── 5) openRenommerZonePanel : fusion overlays -> "Pays & portions" ────────
OLD_PANEL_BLOCK = """  const overlaysDeCetteZone = (CarteState.overlays?.features || [])
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
  `;

  document.getElementById('renommer-impact-btn').addEventListener('click', () => {
    const nouveauSlug = document.getElementById('renommer-nouveau-slug').value.trim();
    const nouveauNom = document.getElementById('renommer-nouveau-nom').value.trim();
    if (!nouveauSlug) { alert('Le nouveau slug est requis'); return; }
    if (!/^[a-z0-9_]+$/.test(nouveauSlug)) {
      alert('Le slug ne doit contenir que des minuscules, chiffres et underscores');
      return;
    }
    _carteImpactRenommage(ancienSlug, nouveauSlug, nouveauNom,
      document.getElementById('renommer-impact-report'));
  });

  const couleurInput = document.getElementById('perso-legende-couleur');
  const autoCheckbox = document.getElementById('perso-legende-auto');
  autoCheckbox.addEventListener('change', () => { couleurInput.disabled = autoCheckbox.checked; });
  couleurInput.disabled = autoCheckbox.checked;

  document.getElementById('perso-legende-appliquer').addEventListener('click', async () => {
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

NEW_PANEL_BLOCK = """  const overlaysParPays = {};
  (CarteState.overlays?.features || []).forEach(f => {
    if (f.properties?.zone_slug === ancienSlug && f.properties?.pays) {
      overlaysParPays[f.properties.pays] = f.properties.id;
    }
  });

  const paysRowsHtml = origineReelleZone.length
    ? origineReelleZone.map((o, i) => {
        const overlayId = overlaysParPays[o.entite];
        const entiteAttr = (o.entite || '').replace(/"/g, '&quot;');
        return `
        <div class="pp-row" style="border:1px solid #eee;border-radius:4px;padding:6px;margin-bottom:4px;font-size:11px;">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
            <div>
              <strong>${o.entite}</strong>${overlayId ? ' <span style="color:#2a7d2a;">📍 tracé</span>' : ''}
              ${o.portion ? `<div style="color:#888;">${o.portion}</div>` : ''}
            </div>
            <div style="display:flex;gap:4px;">
              <button class="pp-deplacer-btn" data-i="${i}" data-entite="${entiteAttr}">↗️ déplacer</button>
              ${overlayId
                ? `<button class="pp-retirer-tracer-btn" data-id="${overlayId}">🗑️ tracé</button>`
                : `<button class="pp-dessiner-btn" data-entite="${entiteAttr}">✏️ dessiner</button>`}
            </div>
          </div>
          <div id="pp-deplacer-form-${i}"></div>
        </div>`;
      }).join('')
    : '<div style="font-size:11px;color:#888;">Aucune entrée.</div>';

  panel.innerHTML = `
    <div class="carte-panel-title">Éditer : ${z ? z.nom : ancienSlug}</div>
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
      <label>Pays &amp; portions de cette zone (${origineReelleZone.length})</label>
      <div id="renommer-pays-liste" style="margin-top:4px;">${paysRowsHtml}</div>
      <button id="renommer-dessiner-overlay-btn" class="yaml-btn" style="margin-top:6px;">✏️ Ajouter un nouveau pays (dessiner un tracé)</button>
    </div>

    <div id="carte-panel-msg"></div>
  `;

  document.getElementById('renommer-impact-btn').addEventListener('click', () => {
    const nouveauSlug = document.getElementById('renommer-nouveau-slug').value.trim();
    const nouveauNom = document.getElementById('renommer-nouveau-nom').value.trim();
    if (!nouveauSlug) { alert('Le nouveau slug est requis'); return; }
    if (!/^[a-z0-9_]+$/.test(nouveauSlug)) {
      alert('Le slug ne doit contenir que des minuscules, chiffres et underscores');
      return;
    }
    _carteImpactRenommage(ancienSlug, nouveauSlug, nouveauNom,
      document.getElementById('renommer-impact-report'));
  });

  const couleurInput = document.getElementById('perso-legende-couleur');
  const autoCheckbox = document.getElementById('perso-legende-auto');
  autoCheckbox.addEventListener('change', () => { couleurInput.disabled = autoCheckbox.checked; });
  couleurInput.disabled = autoCheckbox.checked;

  document.getElementById('perso-legende-appliquer').addEventListener('click', async () => {
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

  panel.querySelectorAll('.pp-deplacer-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      _ouvrirDeplacerPaysInline(ancienSlug, btn.dataset.entite, btn.dataset.i);
    });
  });

  panel.querySelectorAll('.pp-dessiner-btn').forEach(btn => {
    btn.addEventListener('click', () => demarrerDessinPourPays(ancienSlug, btn.dataset.entite));
  });

  panel.querySelectorAll('.pp-retirer-tracer-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!window.confirm('Retirer ce tracé ? (origine_reelle reste inchangé)')) return;
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
}

// Variante : le pays est AUSSI déjà connu (ligne "Pays & portions"), saute
// _promptZoneSlug ET _promptPays -- juste le tracé à poser.
function demarrerDessinPourPays(zoneSlug, pays) {
  CarteState.dessinZonePreselectionnee = zoneSlug;
  CarteState.dessinPaysPreselectionne = pays;
  if (!CarteState.modeDessin) toggleModeDessin();
  document.getElementById('carte-status').textContent =
    `Mode dessin actif pour "${pays}" (${zoneSlug}) — clique sur la carte pour poser chaque sommet du polygone, double-clic pour le fermer.`;
}

// ── Fusion scinder/overlay (12 sept 2026) : déplace UNE entrée précise
// d'origine_reelle vers une autre zone, formulaire replié sous sa ligne
// dans "Pays & portions" -- même logique que l'ancien _ouvrirSplitPanel
// (désormais retiré de l'arbre), mais ciblée sur un seul pays au lieu d'une
// sélection multiple, et affichée en ligne plutôt que dans un panneau à part.
function _ouvrirDeplacerPaysInline(zoneSlug, entite, i) {
  const container = document.getElementById(`pp-deplacer-form-${i}`);
  if (!container) return;
  if (container.dataset.open === '1') { container.innerHTML = ''; container.dataset.open = '0'; return; }
  container.dataset.open = '1';

  // Même règle que l'ancien split : le premier token suffit, le backend
  // retrouve les autres formulations du même pays (voir _entite_references_pays).
  const premierToken = entite.split(/[(,]/)[0].trim().toLowerCase();

  container.innerHTML = `
    <div class="carte-panel-proposal-box" style="margin:6px 0 4px 0">
      <label style="font-size:10px;color:#666">Destination pour "${entite}"</label>
      <select id="pp-cible-select-${i}" style="width:100%;font-size:11px;padding:4px;margin:4px 0">
        <option value="__creer__">+ Créer une nouvelle zone niveau 1…</option>
        <option value="__existante__">→ Ajouter à une zone niveau 1 existante…</option>
      </select>
      <div id="pp-cible-form-${i}"></div>
      <button id="pp-impact-btn-${i}" class="yaml-btn" style="margin-top:4px">🔍 Évaluer l'impact</button>
      <div id="pp-impact-report-${i}"></div>
    </div>
  `;

  const cibleSelect = document.getElementById(`pp-cible-select-${i}`);
  const majFormCible = async () => {
    const formEl = document.getElementById(`pp-cible-form-${i}`);
    if (cibleSelect.value === '__existante__') {
      formEl.innerHTML = `<div class="carte-status">Chargement des zones…</div>`;
      try {
        const res = await fetch(`/api/carte/zones_toutes?scenario=${encodeURIComponent(CarteState.scenario)}`);
        const data = await res.json();
        const options = (data.zones || [])
          .filter(z => z.niveau === 1 && z.slug !== zoneSlug)
          .map(z => `<option value="${z.slug}">${z.nom} (${z.slug})</option>`)
          .join('');
        formEl.innerHTML = `
          <select id="pp-existant-slug-${i}" style="width:100%;padding:3px;font-family:'JetBrains Mono',monospace;margin-top:4px">
            <option value="">— choisir —</option>
            ${options}
          </select>`;
      } catch (e) {
        formEl.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
      }
    } else {
      formEl.innerHTML = `
        <input type="text" id="pp-nouveau-slug-${i}" placeholder="slug_nouvelle_zone (minuscules_underscores)"
               style="width:100%;padding:3px;margin:4px 0;font-family:'JetBrains Mono',monospace">
        <input type="text" id="pp-nouveau-nom-${i}" placeholder="Nom affiché"
               style="width:100%;padding:3px;margin-bottom:4px">
        <select id="pp-nouveau-type-${i}" style="width:100%;padding:3px;margin-bottom:4px">
          ${['bloc_continental','union_regionale','territoire_autonome','territoire_herite','region','ville','infrastructure','site_strategique','zone_sinistree','autre']
            .map(t => `<option value="${t}">${t}</option>`).join('')}
        </select>
        <select id="pp-nouveau-statut-${i}" style="width:100%;padding:3px;margin-bottom:4px">
          ${['dominant','stable','fragmenté','en_declin','disparu','emergent']
            .map(t => `<option value="${t}">${t}</option>`).join('')}
        </select>
        <textarea id="pp-nouveau-desc-${i}" placeholder="Description courte (optionnel)"
                  style="width:100%;padding:3px;font-size:10px" rows="2"></textarea>`;
    }
  };
  cibleSelect.addEventListener('change', majFormCible);
  majFormCible();

  document.getElementById(`pp-impact-btn-${i}`).addEventListener('click', () => {
    let cible;
    if (cibleSelect.value === '__existante__') {
      const slugExistant = document.getElementById(`pp-existant-slug-${i}`).value.trim();
      if (!slugExistant) { alert('Choisis une zone existante.'); return; }
      cible = { mode: 'zone_existante', slug_existant: slugExistant };
    } else {
      const cibleSlug = document.getElementById(`pp-nouveau-slug-${i}`).value.trim();
      const cibleNom = document.getElementById(`pp-nouveau-nom-${i}`).value.trim();
      const cibleType = document.getElementById(`pp-nouveau-type-${i}`).value;
      const cibleStatut = document.getElementById(`pp-nouveau-statut-${i}`).value;
      const cibleDesc = document.getElementById(`pp-nouveau-desc-${i}`).value.trim();
      if (!cibleSlug || !cibleNom) { alert('Slug et nom de la nouvelle zone requis.'); return; }
      cible = { mode: 'nouvelle_zone_n1', slug: cibleSlug, nom: cibleNom, type: cibleType, statut: cibleStatut, description: cibleDesc };
    }
    _ppImpactDeplacer(zoneSlug, premierToken, cible, i);
  });
}

async function _ppImpactDeplacer(zoneSlug, premierToken, cible, i) {
  const container = document.getElementById(`pp-impact-report-${i}`);
  container.innerHTML = '<div class="carte-status">Analyse en cours…</div>';
  try {
    const res = await fetch('/api/carte/impact_split_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug_source: zoneSlug, pays_a_extraire: [premierToken], cible }),
    });
    const r = await res.json();
    if (r.error) { container.innerHTML = `<div class="carte-panel-error">Erreur : ${r.error}</div>`; return; }

    let html = `<div style="margin-top:6px">`;
    html += `<div>Entité(s) extraite(s) : ${r.entites_extraites.map(e => e.entite).join(', ')}</div>`;
    html += `<div style="margin-top:4px">Destination : ${r.cible.nom} ` +
      `(${r.cible.mode === 'nouvelle_zone_n1' ? 'nouvelle zone' : 'zone existante'})</div>`;
    if (r.enfants_qui_suivront.length) {
      html += `<div style="margin-top:6px"><strong>${r.enfants_qui_suivront.length} sous-zone(s) suivent automatiquement</strong> ` +
        `(leur propre origine_reelle référence aussi ce pays) :</div>`;
      html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
        r.enfants_qui_suivront.map(e => `<li>${e.nom}</li>`).join('') + '</ul>';
    }
    html += `<button id="pp-confirm-btn-${i}" class="yaml-btn" style="margin-top:8px;font-weight:700">✓ Confirmer</button>`;
    html += `</div>`;
    container.innerHTML = html;

    document.getElementById(`pp-confirm-btn-${i}`).addEventListener('click', () => {
      _ppConfirmerDeplacer(zoneSlug, premierToken, cible, i);
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function _ppConfirmerDeplacer(zoneSlug, premierToken, cible, i) {
  const container = document.getElementById(`pp-impact-report-${i}`);
  container.innerHTML = '<div class="carte-status">Déplacement en cours…</div>';
  try {
    const res = await fetch('/api/carte/split_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug_source: zoneSlug, pays_a_extraire: [premierToken], cible }),
    });
    const data = await res.json();
    if (data.ok) {
      await refreshCarte();
      openRenommerZonePanel(zoneSlug);  // réaffiche le panneau à jour
    } else {
      container.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
    }
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}"""


def _patch(text, replacements, label):
    for old, new in replacements:
        n = text.count(old)
        print(f"[{label}] bloc attendu : {n} occurrence(s)")
        if n != 1:
            print(f"  -> ERREUR : attendu exactement 1 occurrence. RIEN N'EST ÉCRIT.")
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
        (OLD_STATE_TAIL, NEW_STATE_TAIL),
        (OLD_DRAW_PAYS, NEW_DRAW_PAYS),
        (OLD_ARBRE, NEW_ARBRE),
        (OLD_FETCH_ARBRE, NEW_FETCH_ARBRE),
        (OLD_PANEL_BLOCK, NEW_PANEL_BLOCK),
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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak12")
    bak.write_text(original, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
