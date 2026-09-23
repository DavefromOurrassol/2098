"""
patch_carte_supprimer_zone.py — Ajoute un bouton "🗑️ Supprimer cette zone"
dans le panneau unifié (openRenommerZonePanel), avec aperçu d'impact avant
confirmation (même patron que "Évaluer l'impact" pour le renommage).
Bloqué si la zone a encore des sous-zones rattachées (le backend refuse déjà
cette suppression -- ce patch se contente d'afficher clairement pourquoi
plutôt que de laisser l'utilisateur cliquer confirmer pour rien).

Usage, depuis gui/ :
    python3 patch_carte_supprimer_zone.py --dry-run
    python3 patch_carte_supprimer_zone.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_BLOCK = """    <div class="carte-panel-section">
      <label>Pays &amp; portions de cette zone (${origineReelleZone.length})</label>
      <div id="renommer-pays-liste" style="margin-top:4px;">${paysRowsHtml}</div>
      <button id="renommer-dessiner-overlay-btn" class="yaml-btn" style="margin-top:6px;">✏️ Ajouter un nouveau pays (dessiner un tracé)</button>
    </div>

    <div id="carte-panel-msg"></div>
  `;"""

NEW_BLOCK = """    <div class="carte-panel-section">
      <label>Pays &amp; portions de cette zone (${origineReelleZone.length})</label>
      <div id="renommer-pays-liste" style="margin-top:4px;">${paysRowsHtml}</div>
      <button id="renommer-dessiner-overlay-btn" class="yaml-btn" style="margin-top:6px;">✏️ Ajouter un nouveau pays (dessiner un tracé)</button>
    </div>

    <div class="carte-panel-section" style="border-top:1px solid #f0c0c0;padding-top:8px;">
      <label style="color:#a33;">Zone dangereuse</label>
      <button id="renommer-supprimer-btn" class="btn-secondary" style="margin-top:4px;color:#a33;border-color:#e0a0a0;">🗑️ Supprimer cette zone</button>
      <div id="renommer-supprimer-report" style="margin-top:6px;"></div>
    </div>

    <div id="carte-panel-msg"></div>
  `;"""

# ── câblage : juste avant le wiring de renommer-dessiner-overlay-btn ───────
OLD_WIRING = """  document.getElementById('renommer-dessiner-overlay-btn').addEventListener('click', () => {
    demarrerDessinPourZone(ancienSlug);
  });
}"""

NEW_WIRING = """  document.getElementById('renommer-dessiner-overlay-btn').addEventListener('click', () => {
    demarrerDessinPourZone(ancienSlug);
  });

  document.getElementById('renommer-supprimer-btn').addEventListener('click', () => {
    _afficherImpactSuppression(ancienSlug);
  });
}

// ── Suppression de zone (12 sept 2026) : aperçu d'impact avant confirmation,
// même doctrine que rename/reparent/split -- jamais de suppression directe
// sans montrer d'abord ce qui va être touché (pays désaffectés, overlays
// retirés, sous-zones bloquantes le cas échéant).
async function _afficherImpactSuppression(slug) {
  const container = document.getElementById('renommer-supprimer-report');
  container.innerHTML = '<div class="carte-status">Analyse en cours…</div>';
  try {
    const res = await fetch('/api/carte/impact_supprimer_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug }),
    });
    const r = await res.json();
    if (r.error) { container.innerHTML = `<div class="carte-panel-error">Erreur : ${r.error}</div>`; return; }

    if (!r.peut_supprimer) {
      container.innerHTML = `
        <div class="carte-panel-error">
          Impossible : ${r.enfants_bloquants.length} sous-zone(s) encore rattachée(s) --
          déplace-les ou supprime-les d'abord :
          <ul style="margin:4px 0;padding-left:16px;font-size:10px">
            ${r.enfants_bloquants.map(e => `<li>${e.nom}</li>`).join('')}
          </ul>
        </div>`;
      return;
    }

    let html = '<div style="font-size:11px;">';
    if (r.pays_a_desaffecter.length) {
      html += `<div>${r.pays_a_desaffecter.length} pays seront désaffectés : ${r.pays_a_desaffecter.join(', ')}</div>`;
    }
    if (r.overlays_a_supprimer) {
      html += `<div style="margin-top:4px;">${r.overlays_a_supprimer} overlay(s) seront retirés.</div>`;
    }
    if (r.zones_relations_liees.length) {
      html += `<div style="margin-top:4px;">Référencée en allié/rival par : ${r.zones_relations_liees.join(', ')} (nettoyé automatiquement).</div>`;
    }
    html += `<button id="renommer-supprimer-confirm-btn" class="yaml-btn" style="margin-top:8px;color:#a33;font-weight:700;">✓ Confirmer la suppression</button>`;
    html += '</div>';
    container.innerHTML = html;

    document.getElementById('renommer-supprimer-confirm-btn').addEventListener('click', () => {
      _confirmerSuppressionZone(slug);
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function _confirmerSuppressionZone(slug) {
  const container = document.getElementById('renommer-supprimer-report');
  container.innerHTML = '<div class="carte-status">Suppression en cours…</div>';
  try {
    const res = await fetch('/api/carte/supprimer_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug }),
    });
    const data = await res.json();
    if (!data.ok) {
      container.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
      return;
    }
    // La zone n'existe plus -- ferme le panneau plutôt que de le réafficher.
    document.getElementById('carte-panel').innerHTML =
      `<div class="carte-panel-empty">Zone "${slug}" supprimée.</div>`;
    CarteState.zoneSurlignee = null;
    await refreshCarte();
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}"""


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
        (OLD_BLOCK, NEW_BLOCK),
        (OLD_WIRING, NEW_WIRING),
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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak15")
    bak.write_text(original, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
