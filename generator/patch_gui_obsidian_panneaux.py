#!/usr/bin/env python3
"""
patch_gui_obsidian_panneaux.py — Ourrassol 2098 (12 octobre 2026)
=================================================================

Dans tous les panneaux de fichiers du GUI (yaml_files de scripts_config.json),
le titre d'un fichier .md devient cliquable (« … ↗ ») et ouvre le fichier dans
Obsidian, avec le même lien obsidian://open que les boutons « Ouvrir dans
Obsidian » existants (nom du vault = dernier segment de vault_root).
Les .yaml ne sont pas concernés (Obsidian ne les affiche pas sans plugin).

Un seul fichier : gui/static/app.js. Aucune route serveur.

Usage (depuis la racine du vault) :
    python3 generator/patch_gui_obsidian_panneaux.py --dry-run && python3 generator/patch_gui_obsidian_panneaux.py
Sauvegarde .bak_obsidian ; refuse un second passage. Recharger la page sans
cache (Cmd+Maj+R) ; pas besoin de redémarrer Flask.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CIBLE = Path(__file__).resolve().parent.parent / "gui" / "static" / "app.js"
MARQUE = "PATCH_GUI_OBSIDIAN_PANNEAUX"

AVANT = ("  titleEl.textContent = yf.label;\n"
         "\n"
         "  const actions = document.createElement('div');\n"
         "  actions.className = 'yaml-panel-actions';\n"
         "\n"
         "  if (!yf.readonly) {\n"
         "    const btnEdit = document.createElement('button');\n")

APRES = ("  titleEl.textContent = yf.label;\n"
         "  // PATCH_GUI_OBSIDIAN_PANNEAUX (12 octobre 2026) : titre d'un .md cliquable,\n"
         "  // ouvre le fichier dans Obsidian (même lien que les boutons existants).\n"
         "  if (/\\.md$/i.test(yf.path)) {\n"
         "    titleEl.textContent = `${yf.label} ↗`;\n"
         "    titleEl.title = 'Ouvrir dans Obsidian';\n"
         "    titleEl.style.cursor = 'pointer';\n"
         "    titleEl.addEventListener('mouseenter', () => { titleEl.style.textDecoration = 'underline'; });\n"
         "    titleEl.addEventListener('mouseleave', () => { titleEl.style.textDecoration = ''; });\n"
         "    titleEl.addEventListener('click', () => _panneauOuvrirDansObsidian(yf.path));\n"
         "  }\n"
         "\n"
         "  const actions = document.createElement('div');\n"
         "  actions.className = 'yaml-panel-actions';\n"
         "\n"
         "  if (!yf.readonly) {\n"
         "    const btnEdit = document.createElement('button');\n")

FONCTION = r'''

// PATCH_GUI_OBSIDIAN_PANNEAUX (12 octobre 2026, demande de David) : ouvre dans
// Obsidian le fichier .md d'un panneau (chemin relatif au vault, sans .md).
function _panneauOuvrirDansObsidian(chemin) {
  const vaultRoot = (State.config?.vault_root || '').replace(/[/\\]+$/, '');
  if (!vaultRoot) {
    alert('vault_root introuvable dans la configuration -- impossible de construire le lien Obsidian.');
    return;
  }
  const vaultName = vaultRoot.split(/[/\\]/).pop();
  const fichier = chemin.replace(/^[/\\]+/, '').replace(/\.md$/i, '');
  window.open(`obsidian://open?vault=${encodeURIComponent(vaultName)}&file=${encodeURIComponent(fichier)}`, '_blank');
}
'''


def _node_check(texte):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
        tmp.write(texte)
    try:
        r = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass
    return r.returncode == 0, r.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cible", default=str(CIBLE))
    args = ap.parse_args()
    cible = Path(args.cible)
    if not cible.exists():
        sys.exit(f"✗ {cible} introuvable : rien écrit.")
    texte = cible.read_text(encoding="utf-8")
    if MARQUE in texte:
        sys.exit("✗ Patch déjà appliqué : rien à faire.")
    if "function _panneauOuvrirDansObsidian" in texte:
        sys.exit("✗ Fonction _panneauOuvrirDansObsidian déjà présente : rien écrit.")
    compte = texte.count(AVANT)
    if compte != 1:
        sys.exit(f"✗ Ancre trouvée {compte} fois (1 attendue) : rien écrit.")
    nouveau = texte.replace(AVANT, APRES).rstrip("\n") + "\n" + FONCTION
    # Syntaxe : app.js entier si node l'accepte déjà, sinon les ajouts seuls.
    origine = _node_check(texte)
    if origine is None:
        note = "node absent : syntaxe JS non vérifiée"
    elif origine[0]:
        ok, err = _node_check(nouveau)
        if not ok:
            sys.exit(f"✗ app.js patché : erreur de syntaxe, rien écrit :\n{err[-800:]}")
        note = "syntaxe JS vérifiée (node)"
    else:
        ok, err = _node_check("const State = {}, yf = {}, titleEl = {};\n" + FONCTION)
        if not ok:
            sys.exit(f"✗ fonction ajoutée : erreur de syntaxe, rien écrit :\n{err[-800:]}")
        note = "syntaxe de la fonction ajoutée vérifiée (node trop ancien pour app.js entier)"
    if args.dry_run:
        print(f"✓ Patch applicable, {note} (dry-run, rien écrit).")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_obsidian"))
    cible.write_text(nouveau, encoding="utf-8")
    print("✓ Titres des panneaux .md cliquables (↗ Obsidian) ; sauvegarde app.js.bak_obsidian. "
          "Recharger la page sans cache (Cmd+Maj+R).")


if __name__ == "__main__":
    main()
