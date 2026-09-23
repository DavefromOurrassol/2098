"""
patch_carte_hachures_ui.py — Ajoute une case à cocher "hachures" dans les
2 panneaux qui permettent déjà de personnaliser couleur/motif d'une zone :
  1. "🎨 personnaliser" (dans l'arbre de zones, _ouvrirPersoPanel)
  2. "✏️ renommer" (bouton crayon de la légende, openRenommerZonePanel)

Nécessite zone_repository.py à jour (build_zone_tree() expose déjà
`hachures`, personnaliser() accepte déjà ce paramètre -- livrés séparément).

Usage, depuis gui/ :
    python3 patch_carte_hachures_ui.py --dry-run
    python3 patch_carte_hachures_ui.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

# ── 1) bouton dans l'arbre : ajoute data-hachures ───────────────────────────
OLD_BTN = """  html += `<button class="arbre-zone-perso-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" data-couleur="${node.couleur || ''}" data-motif="${node.motif || ''}" title="Choisir une couleur et/ou un motif pour cette zone">🎨 personnaliser</button>`;"""

NEW_BTN = """  html += `<button class="arbre-zone-perso-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" data-couleur="${node.couleur || ''}" data-motif="${node.motif || ''}" data-hachures="${node.hachures ? '1' : ''}" title="Choisir une couleur et/ou un motif pour cette zone">🎨 personnaliser</button>`;"""

# ── 2) appel à _ouvrirPersoPanel : passe le 4e argument ─────────────────────
OLD_CALL = """      btn.addEventListener('click', () => _ouvrirPersoPanel(btn.dataset.slug, btn.dataset.couleur, btn.dataset.motif));"""

NEW_CALL = """      btn.addEventListener('click', () => _ouvrirPersoPanel(btn.dataset.slug, btn.dataset.couleur, btn.dataset.motif, btn.dataset.hachures === '1'));"""

# ── 3) _ouvrirPersoPanel : signature + case à cocher + envoi ────────────────
OLD_PERSO_PANEL = """function _ouvrirPersoPanel(slug, couleurActuelle, motifActuel) {
  const panel = document.getElementById(`perso-panel-${slug}`);
  if (panel.innerHTML) { panel.innerHTML = ''; return; } // toggle fermeture

  const motifOptions = ['', ...Object.keys(MOTIFS_LABELS)].map(m =>
    `<option value="${m}" ${m === motifActuel ? 'selected' : ''}>${m ? MOTIFS_LABELS[m] : '— aucun —'}</option>`
  ).join('');

  panel.innerHTML = `
    <div style="border:1px solid #dde3ee;border-radius:4px;padding:8px;margin-top:4px;font-size:11px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
      <label>Couleur :
        <input type="color" id="perso-couleur-${slug}" value="${couleurActuelle || '#3b6fd4'}">
      </label>
      <label>
        <input type="checkbox" id="perso-couleur-auto-${slug}" ${couleurActuelle ? '' : 'checked'}> auto
      </label>
      <label>Motif :
        <select id="perso-motif-${slug}">${motifOptions}</select>
      </label>
      <button class="btn-primary perso-appliquer-btn" data-slug="${slug}">✓ Appliquer</button>
      <span class="perso-msg" style="font-size:10px;"></span>
    </div>
  `;

  const couleurInput = document.getElementById(`perso-couleur-${slug}`);
  const autoCheckbox = document.getElementById(`perso-couleur-auto-${slug}`);
  autoCheckbox.addEventListener('change', () => { couleurInput.disabled = autoCheckbox.checked; });
  couleurInput.disabled = autoCheckbox.checked;

  panel.querySelector('.perso-appliquer-btn').addEventListener('click', async () => {
    const msgEl = panel.querySelector('.perso-msg');
    msgEl.textContent = 'Enregistrement…';
    const motifChoisi = document.getElementById(`perso-motif-${slug}`).value;
    const body = {
      scenario: CarteState.scenario,
      slug,
      couleur: autoCheckbox.checked ? null : couleurInput.value,
      motif: motifChoisi || null,
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

NEW_PERSO_PANEL = """function _ouvrirPersoPanel(slug, couleurActuelle, motifActuel, hachuresActuel) {
  const panel = document.getElementById(`perso-panel-${slug}`);
  if (panel.innerHTML) { panel.innerHTML = ''; return; } // toggle fermeture

  const motifOptions = ['', ...Object.keys(MOTIFS_LABELS)].map(m =>
    `<option value="${m}" ${m === motifActuel ? 'selected' : ''}>${m ? MOTIFS_LABELS[m] : '— aucun —'}</option>`
  ).join('');

  panel.innerHTML = `
    <div style="border:1px solid #dde3ee;border-radius:4px;padding:8px;margin-top:4px;font-size:11px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
      <label>Couleur :
        <input type="color" id="perso-couleur-${slug}" value="${couleurActuelle || '#3b6fd4'}">
      </label>
      <label>
        <input type="checkbox" id="perso-couleur-auto-${slug}" ${couleurActuelle ? '' : 'checked'}> auto
      </label>
      <label>Motif :
        <select id="perso-motif-${slug}">${motifOptions}</select>
      </label>
      <label title="Hachures génériques en plus de la couleur -- désactivées par défaut">
        <input type="checkbox" id="perso-hachures-${slug}" ${hachuresActuel ? 'checked' : ''}> hachures
      </label>
      <button class="btn-primary perso-appliquer-btn" data-slug="${slug}">✓ Appliquer</button>
      <span class="perso-msg" style="font-size:10px;"></span>
    </div>
  `;

  const couleurInput = document.getElementById(`perso-couleur-${slug}`);
  const autoCheckbox = document.getElementById(`perso-couleur-auto-${slug}`);
  autoCheckbox.addEventListener('change', () => { couleurInput.disabled = autoCheckbox.checked; });
  couleurInput.disabled = autoCheckbox.checked;

  panel.querySelector('.perso-appliquer-btn').addEventListener('click', async () => {
    const msgEl = panel.querySelector('.perso-msg');
    msgEl.textContent = 'Enregistrement…';
    const motifChoisi = document.getElementById(`perso-motif-${slug}`).value;
    const hachuresChoisi = document.getElementById(`perso-hachures-${slug}`).checked;
    const body = {
      scenario: CarteState.scenario,
      slug,
      couleur: autoCheckbox.checked ? null : couleurInput.value,
      motif: motifChoisi || null,
      hachures: hachuresChoisi,
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

# ── 4) openRenommerZonePanel : lecture hachures + case à cocher + envoi ─────
OLD_RENOMMER = """  let couleurActuelle = null, motifActuel = null;
  try {
    const res = await fetch(`/api/carte/arbre_zone?scenario=${encodeURIComponent(CarteState.scenario)}&slug=${encodeURIComponent(ancienSlug)}`);
    const data = await res.json();
    if (data.arbre) {
      couleurActuelle = data.arbre.couleur || null;
      motifActuel = data.arbre.motif || null;
    }
  } catch (e) {
    // Non bloquant : le panneau s'ouvre quand même, juste sans préremplissage.
  }

  const motifOptions = ['', ...Object.keys(MOTIFS_LABELS)].map(m =>
    `<option value="${m}" ${m === motifActuel ? 'selected' : ''}>${m ? MOTIFS_LABELS[m] : '— aucun —'}</option>`
  ).join('');

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
        <button class="yaml-btn" id="perso-legende-appliquer">✓ Appliquer</button>
        <span id="perso-legende-msg" style="font-size:10px;"></span>
      </div>
    </div>

    <div id="carte-panel-msg"></div>
  `;"""

NEW_RENOMMER = """  let couleurActuelle = null, motifActuel = null, hachuresActuel = false;
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
  }

  const motifOptions = ['', ...Object.keys(MOTIFS_LABELS)].map(m =>
    `<option value="${m}" ${m === motifActuel ? 'selected' : ''}>${m ? MOTIFS_LABELS[m] : '— aucun —'}</option>`
  ).join('');

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

    <div id="carte-panel-msg"></div>
  `;"""

OLD_RENOMMER_BODY = """    const body = {
      scenario: CarteState.scenario,
      slug: ancienSlug,
      couleur: autoCheckbox.checked ? null : couleurInput.value,
      motif: motifChoisi || null,
    };"""

NEW_RENOMMER_BODY = """    const body = {
      scenario: CarteState.scenario,
      slug: ancienSlug,
      couleur: autoCheckbox.checked ? null : couleurInput.value,
      motif: motifChoisi || null,
      hachures: document.getElementById('perso-legende-hachures').checked,
    };"""


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
        (OLD_BTN, NEW_BTN),
        (OLD_CALL, NEW_CALL),
        (OLD_PERSO_PANEL, NEW_PERSO_PANEL),
        (OLD_RENOMMER, NEW_RENOMMER),
        (OLD_RENOMMER_BODY, NEW_RENOMMER_BODY),
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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak8")
    bak.write_text(original, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
