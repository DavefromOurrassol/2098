#!/usr/bin/env python3
"""
patch_s27_indications.py -- indications « terminal » traduites dans le panneau (18 octobre 2026)
===============================================================================================
Les scripts appelés par le panneau « Parcours » écrivent des indications pour le
terminal (« Relancer avec --apply… », « --inclure 8 », « Injection à lancer à part :
python3 … »). Dans le GUI, elles sont remplacées par le bouton ou le champ à utiliser.
Les scripts ne changent pas (le terminal garde ses indications) : seule la sortie
affichée dans le panneau est adaptée.

  gui/static/app.js : fonction adapterSortie(), appliquée au résultat de chaque bouton.

Tout ou rien, sauvegarde .bak_indications, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_indications.py            (aperçu)
    python3 generator/patch_s27_indications.py --apply
Puis recharger la page du GUI.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_INDICATIONS"
APP_JS = Path.cwd() / "gui" / "static" / "app.js"

ANCRE_FONCTION = r"""  const tri = () => ({ sauter: sauter.value, inclure: inclure.value });
"""
FONCTION = r"""  // PATCH_S27_INDICATIONS : indications écrites pour le terminal → bouton ou champ du panneau.
  function adapterSortie(base, action, texte) {
    const bouton = { 'appliquer': '« Appliquer »', 'main/entites': '« Ajouter à la file »',
                     'main/regle': '« Ajouter la règle »' }[base] || 'le bouton d\'écriture';
    return String(texte)
      .replace(/Relancer avec --apply pour écrire \(sauvegarde \.bak_appliquer\), --sauter \/ --inclure pour trier ;\n?/g,
               'Pour écrire : bouton « Appliquer » (sauvegarde .bak_appliquer) ; champs « Sauter » / « Inclure » pour trier ;\n')
      .replace(/--reste-a-faire pour écrire seulement la check-list des tâches à la main\./g,
               'bouton « Générer la check-list » (étape ⑤) pour la check-list seule.')
      .replace(/sautée \(--inclure (\d+) pour l'appliquer\)/g, 'sautée (mettre $1 dans « Inclure » pour l\'appliquer)')
      .replace(/Relancer avec --apply\./g, `Pour écrire : bouton ${bouton}.`)
      .replace(/Relancer sans --apercu pour l'écrire dans evenements_custom\/queue\.yaml\./g,
               'Pour l\'écrire dans la file d\'injection : bouton « Adopter ».')
      .replace(/Injection à lancer à part : python3 generator\/inject_custom_events\.py --mode custom/g,
               'Injection : étape ③ « Injecter » de ce panneau (après ↻ Actualiser si besoin).');
  }
"""
REMPLACEMENTS = [
    (ANCRE_FONCTION, FONCTION + ANCRE_FONCTION),
    (
        r"""    sortie.textContent = data.error ? `✗ ${data.error}` : (data.sortie || '(aucune sortie)');""",
        r"""    sortie.textContent = data.error ? `✗ ${data.error}`
      : adapterSortie(base, action, data.sortie || '(aucune sortie)');   // PATCH_S27_INDICATIONS""",
    ),
]
DEBUT_PANNEAU = "// PATCH_S27_GUI_PARCOURS — PANNEAU"
FIN_PANNEAU = "// PATCH_GUI_OBSIDIAN_PANNEAUX"


def main():
    apply = "--apply" in sys.argv
    if not APP_JS.exists():
        sys.exit("✗ gui/static/app.js introuvable (lancer depuis la racine du coffre). Rien fait.")
    js = APP_JS.read_text(encoding="utf-8")
    if MARQUEUR in js:
        sys.exit("✗ patch déjà appliqué : rien fait.")
    for n, (ancien, neuf) in enumerate(REMPLACEMENTS, 1):
        if js.count(ancien) != 1:
            sys.exit(f"✗ repère n°{n} trouvé {js.count(ancien)} fois (attendu 1) : rien fait.")
        js = js.replace(ancien, neuf)
    i = js.find(DEBUT_PANNEAU)
    j = js.find(FIN_PANNEAU, i)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js[i:j])
    try:
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            sys.exit("✗ JavaScript invalide après patch, rien écrit :\n" + r.stderr)
    except FileNotFoundError:
        print("  (node absent : contrôle JS sauté)")
    finally:
        Path(f.name).unlink()
    print("  ✓ gui/static/app.js : indications adaptées au panneau prêtes")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(APP_JS, APP_JS.with_name("app.js.bak_indications"))
    APP_JS.write_text(js, encoding="utf-8")
    print("\n✓ Fait (sauvegarde app.js.bak_indications). Recharger la page du GUI.")


if __name__ == "__main__":
    main()
