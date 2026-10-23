#!/usr/bin/env python3
"""
patch_s27_menu_et_si.py -- « Simulateur « et si ? » » rangé dans « Entités & événements —
Création » (18 octobre 2026)
=========================================================================================
  gui/scripts_config.json : l'entrée `simuler_et_si` passe de la section
  `entites_nettoyage` à `entites_creation`, placée juste avant « Injecter des
  événements » (on teste une hypothèse avant de l'injecter). Rien d'autre ne change :
  le fichier est relu et réécrit au même format (indentation 2), et le patch vérifie
  que toutes les autres entrées sont identiques.

Sauvegarde .bak_menu. Usage, depuis la racine du coffre :
    python3 generator/patch_s27_menu_et_si.py            (aperçu)
    python3 generator/patch_s27_menu_et_si.py --apply
Puis redémarrer le GUI.
"""
import json
import shutil
import sys
from pathlib import Path

CHEMIN = Path.cwd() / "gui" / "scripts_config.json"


def main():
    apply = "--apply" in sys.argv
    if not CHEMIN.exists():
        sys.exit("✗ gui/scripts_config.json introuvable (lancer depuis la racine du coffre). Rien fait.")
    texte = CHEMIN.read_text(encoding="utf-8")
    liste = json.loads(texte)
    ids = [e.get("id") for e in liste]
    if "simuler_et_si" not in ids:
        sys.exit("✗ entrée simuler_et_si absente. Rien fait.")
    entree = liste[ids.index("simuler_et_si")]
    if entree.get("section") == "entites_creation":
        sys.exit("· déjà dans « Entités & événements — Création » : rien à faire.")
    avant = entree.get("section")
    autres = [e for e in liste if e.get("id") != "simuler_et_si"]
    entree = dict(entree, section="entites_creation")
    ids_autres = [e.get("id") for e in autres]
    pos = ids_autres.index("inject_events") if "inject_events" in ids_autres else next(
        (i for i, e in enumerate(autres) if e.get("section") == "entites_creation"), len(autres))
    nouvelle = autres[:pos] + [entree] + autres[pos:]
    # Contrôles : mêmes entrées, seule la section de simuler_et_si a changé.
    assert len(nouvelle) == len(liste)
    for e in liste:
        n = next(x for x in nouvelle if x.get("id") == e.get("id"))
        attendu = dict(e, section="entites_creation") if e.get("id") == "simuler_et_si" else e
        assert n == attendu, e.get("id")
    sortie = json.dumps(nouvelle, ensure_ascii=False, indent=2) + ("\n" if texte.endswith("\n") else "")
    print(f"  ✓ simuler_et_si : section {avant} → entites_creation, juste avant « Injecter des événements »")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CHEMIN, CHEMIN.with_name("scripts_config.json.bak_menu"))
    CHEMIN.write_text(sortie, encoding="utf-8")
    print("\n✓ Fait (sauvegarde scripts_config.json.bak_menu). Redémarrer le GUI.")


if __name__ == "__main__":
    main()
