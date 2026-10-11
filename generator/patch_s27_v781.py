#!/usr/bin/env python3
"""
patch_s27_v781.py — Ourrassol 2098 (S27, 10 octobre 2026)
==========================================================

Simulateur « et si ? » v7.8 -> v7.8.1 : garde-fou contre le double ajout.
Constat de David : après « Ajouter à hypotheses.yaml », l'idée et le bloc
restent dans le panneau ; on peut ajouter deux fois la même hypothèse.

1. gui/static/app.js : après un ajout réussi, l'idée et le bloc sont vidés,
   et « Ajouter » reste désactivé jusqu'à la prochaine modification du bloc
   ou la prochaine proposition.
2. (côté serveur, fichier livré à part) hypothese_depuis_texte.py refuse un
   bloc dont le nom ou la description existe déjà sous un autre id.

Fichier : gui/static/app.js (.bak_v781). Ensuite : recharger la page (Cmd-Maj-R).

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v781.py            # aperçu
    python3 generator/patch_s27_v781.py --apply    # écrit
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
JS_CANDIDATS = [VAULT_ROOT / "gui" / "static" / "app.js", VAULT_ROOT / "gui" / "static" / "js" / "app.js"]

REMPLACEMENTS = [
    ("après ajout : panneau vidé, Ajouter verrouillé",
     '''    afficher(statut, data, data.message ? `✓ ${data.message}` : '');
    if (data.ok) {''',
     '''    afficher(statut, data, data.message ? `✓ ${data.message}` : '');
    if (data.ok) {
      // v7.8.1 : garde-fou contre le double ajout -- l'idée et le bloc sont
      // vidés, « Ajouter » reste verrouillé jusqu'à un nouveau bloc.
      idee.value = '';
      bloc.value = '';
      btnAjouter.disabled = true;
      btnAjouter.dataset.verrou = '1';'''),
    ("verrou levé à la modification du bloc",
     '''  btnVerifier.addEventListener('click', async () => {''',
     '''  bloc.addEventListener('input', () => {
    if (btnAjouter.dataset.verrou) { delete btnAjouter.dataset.verrou; btnAjouter.disabled = false; }
  });

  btnVerifier.addEventListener('click', async () => {'''),
    ("verrou levé à une nouvelle proposition",
     '''    if (data.bloc) bloc.value = data.bloc;''',
     '''    if (data.bloc) { bloc.value = data.bloc; delete btnAjouter.dataset.verrou; }'''),
    ("occupé() respecte le verrou",
     '''    [btnProposer, btnVerifier, btnAjouter].forEach(b => { b.disabled = oui; });''',
     '''    [btnProposer, btnVerifier].forEach(b => { b.disabled = oui; });
    btnAjouter.disabled = oui || !!btnAjouter.dataset.verrou;'''),
]


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7.8 -> v7.8.1.")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    js = next((p for p in JS_CANDIDATS if p.exists()), None)
    if js is None:
        sys.exit("✗ app.js introuvable")
    txt = js.read_text(encoding="utf-8")
    if "function buildAssistantHypothese" not in txt:
        sys.exit("✗ La v7.8 n'est pas installée (panneau Nouvelle hypothèse absent).")
    if "btnAjouter.dataset.verrou" in txt:
        sys.exit("✗ Patch déjà appliqué (v7.8.1). Rien à faire.")
    erreurs = []
    print("app.js :")
    for libelle, ancien, nouveau in REMPLACEMENTS:
        n = txt.count(ancien)
        if n != 1:
            erreurs.append(f"{libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        txt = txt.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    shutil.copy(js, js.with_name(js.name + ".bak_v781"))
    js.write_text(txt, encoding="utf-8")
    print(f"→ écrit : {js.relative_to(VAULT_ROOT)} (sauvegarde {js.name}.bak_v781)")
    print("\nPassé en v7.8.1. Recharger la page (Cmd-Maj-R).")


if __name__ == "__main__":
    main()
