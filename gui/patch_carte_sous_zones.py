"""
patch_carte_sous_zones.py — Point 3 de la demande initiale de David :
"je voudrais pouvoir localiser des sous zones". Jusqu'ici, sélectionner une
sous-zone (niveau 2/3) via la recherche ne faisait que la surligner dans le
TEXTE de l'arbre -- rien ne s'affichait sur la carte (cohérent avec le fait
qu'une sous-zone n'a pas de couleur propre depuis la refonte, mais elle doit
quand même pouvoir être localisée).

Approche : une sous-zone n'a pas de tracé propre en général, donc on
reconstruit son emprise à partir de ses PROPRES entrées origine_reelle,
filtrées parmi les pays déjà affectés (en base) à sa racine niveau 1 --
plus ses éventuels overlays directs, le cas échéant. Même mécanisme de
contour (turf.union + turf.difference) que pour une zone N1, réutilisé tel
quel.

Usage, depuis gui/ :
    python3 patch_carte_sous_zones.py --dry-run
    python3 patch_carte_sous_zones.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

# ── 1) état : racineParSlug ──────────────────────────────────────────────
OLD_STATE_TAIL = """  origineReelleParSlug: {},  // slug -> origine_reelle, reconstruit à chaque ouverture d'arbre (split)"""

NEW_STATE_TAIL = """  origineReelleParSlug: {},  // slug -> origine_reelle, reconstruit à chaque ouverture d'arbre (split)
  racineParSlug: {},  // slug -> slug de la racine niveau 1, reconstruit à chaque ouverture d'arbre (localiser une sous-zone)"""

# ── 2) indexeur de l'arbre : trace aussi la racine N1 de chaque nœud ───────
OLD_INDEXER = """    CarteState.origineReelleParSlug = {};
    (function indexer(node) {
      CarteState.origineReelleParSlug[node.slug] = node.origine_reelle || [];
      (node.enfants || []).forEach(indexer);
    })(data.arbre);"""

NEW_INDEXER = """    CarteState.origineReelleParSlug = {};
    CarteState.racineParSlug = {};
    (function indexer(node) {
      CarteState.origineReelleParSlug[node.slug] = node.origine_reelle || [];
      CarteState.racineParSlug[node.slug] = data.arbre.slug;  // racine N1 de tout l'arbre affiché
      (node.enfants || []).forEach(indexer);
    })(data.arbre);"""

# ── 3) sélection d'un résultat de recherche : surligne aussi sur la carte ──
OLD_SELECTION = """async function _carteSelectionnerResultatRecherche(resultat) {
  document.getElementById('carte-search-results').style.display = 'none';
  document.getElementById('carte-search-input').value = resultat.nom;

  const racineSlug = (resultat.chemin && resultat.chemin[0] && resultat.chemin[0].slug) || resultat.slug;
  await openArbreZonePanel(racineSlug);

  const noeud = document.querySelector(`#arbre-zone-tree [data-slug="${CSS.escape(resultat.slug)}"]`);
  if (noeud) {
    noeud.scrollIntoView({ behavior: 'smooth', block: 'center' });
    noeud.classList.add('surlignee-recherche');
    setTimeout(() => noeud.classList.remove('surlignee-recherche'), 2500);
  }
}"""

NEW_SELECTION = """async function _carteSelectionnerResultatRecherche(resultat) {
  document.getElementById('carte-search-results').style.display = 'none';
  document.getElementById('carte-search-input').value = resultat.nom;

  const racineSlug = (resultat.chemin && resultat.chemin[0] && resultat.chemin[0].slug) || resultat.slug;
  await openArbreZonePanel(racineSlug);

  const noeud = document.querySelector(`#arbre-zone-tree [data-slug="${CSS.escape(resultat.slug)}"]`);
  if (noeud) {
    noeud.scrollIntoView({ behavior: 'smooth', block: 'center' });
    noeud.classList.add('surlignee-recherche');
    setTimeout(() => noeud.classList.remove('surlignee-recherche'), 2500);
  }

  // Localiser sur la carte (12 sept 2026) : avant, seule la surbrillance
  // texte dans l'arbre existait -- une sous-zone n'apparaissait nulle part
  // sur la carte elle-même. openArbreZonePanel vient de peupler
  // racineParSlug/origineReelleParSlug pour tout l'arbre affiché, donc
  // renderSurlignageZone (appelé via renderCarteLayer) sait maintenant
  // reconstruire l'emprise de n'importe quel nœud, N1 ou sous-zone.
  CarteState.zoneSurlignee = resultat.slug;
  renderCarteLayer();
}"""

# ── 4) renderSurlignageZone : gère aussi les sous-zones ────────────────────
OLD_RENDER = """function renderSurlignageZone() {
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
  });"""

NEW_RENDER = """function renderSurlignageZone() {
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
  });"""


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
        (OLD_STATE_TAIL, NEW_STATE_TAIL),
        (OLD_INDEXER, NEW_INDEXER),
        (OLD_SELECTION, NEW_SELECTION),
        (OLD_RENDER, NEW_RENDER),
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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak16")
    bak.write_text(original, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
