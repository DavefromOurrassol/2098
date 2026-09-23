"""
patch_carte_selection_arbre.py — Cliquer sur une zone directement dans
l'arbre (sans passer par la recherche) ne faisait rien -- seule la
recherche déclenchait la localisation sur la carte. Ajoute un clic sur le
NOM de la zone (n'importe quel niveau) dans l'arbre pour la localiser
aussi, en réutilisant le même mécanisme (CarteState.zoneSurlignee +
renderCarteLayer()) déjà mis en place pour la recherche.

Usage, depuis gui/ :
    python3 patch_carte_selection_arbre.py --dry-run
    python3 patch_carte_selection_arbre.py --apply
"""

import argparse
import shutil
import subprocess
from pathlib import Path

APP_JS = Path("static/app.js")
if not APP_JS.exists():
    APP_JS = Path("app.js")

OLD_NOM = """  html += `<span class="arbre-zone-nom">${node.nom}</span>`;"""

NEW_NOM = """  html += `<span class="arbre-zone-nom" style="cursor:pointer;text-decoration:underline dotted;" title="Localiser sur la carte">${node.nom}</span>`;"""

OLD_WIRING = """    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-move-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirReparentPanel(btn.dataset.slug, btn.dataset.nom));
    });

    CarteState.origineReelleParSlug = {};
    CarteState.racineParSlug = {};
    (function indexer(node) {
      CarteState.origineReelleParSlug[node.slug] = node.origine_reelle || [];
      CarteState.racineParSlug[node.slug] = data.arbre.slug;  // racine N1 de tout l'arbre affiché
      (node.enfants || []).forEach(indexer);
    })(data.arbre);"""

NEW_WIRING = """    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-move-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirReparentPanel(btn.dataset.slug, btn.dataset.nom));
    });

    CarteState.origineReelleParSlug = {};
    CarteState.racineParSlug = {};
    (function indexer(node) {
      CarteState.origineReelleParSlug[node.slug] = node.origine_reelle || [];
      CarteState.racineParSlug[node.slug] = data.arbre.slug;  // racine N1 de tout l'arbre affiché
      (node.enfants || []).forEach(indexer);
    })(data.arbre);

    // Localiser une zone (N1 ou sous-zone) sur la carte en cliquant
    // directement son nom dans l'arbre (12 sept 2026) -- avant, seule la
    // recherche déclenchait le surlignage carte, parcourir l'arbre à la
    // main ne faisait rien.
    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-nom').forEach(el => {
      el.addEventListener('click', () => {
        const ligne = el.closest('.arbre-zone-node-row');
        if (!ligne) return;
        CarteState.zoneSurlignee = ligne.dataset.slug;
        renderCarteLayer();
      });
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
        (OLD_NOM, NEW_NOM),
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

    bak = APP_JS.with_suffix(APP_JS.suffix + ".bak18")
    bak.write_text(original, encoding="utf-8")
    APP_JS.write_text(new_text, encoding="utf-8")
    print(f"\n{APP_JS} mis à jour. Sauvegarde : {bak}")


if __name__ == "__main__":
    main()
