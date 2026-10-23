#!/usr/bin/env python3
"""
test_patch_carte_type_entite.py — 23 octobre 2026.

Vérifie PATCH_CARTE_TYPE_ENTITE sur une COPIE temporaire (rien n'est écrit dans
le vrai vault) : l'Écosse (scénario reference) est réaffectée par le bouton de
la Carte, en « absorber » vers une autre zone N1 puis en « créer », et le
type_entite écrit doit rester celui d'origine.

Usage (depuis la racine du vault) :
    python3 generator/test_patch_carte_type_entite.py [--scenario reference] [--pays Écosse]
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
GUI = VAULT / "gui"
sys.path.insert(0, str(GUI))
from zone_repository import ZoneRepository  # noqa: E402


def copie_temporaire(scenario: str) -> tuple:
    tmp = Path(tempfile.mkdtemp(prefix="test_type_entite_"))
    vault_tmp, gui_tmp = tmp / "vault", tmp / "gui"
    (vault_tmp / "geographie").mkdir(parents=True)
    (gui_tmp / "static" / "geo_overlays").mkdir(parents=True)
    shutil.copy2(VAULT / "geographie" / f"{scenario}.md", vault_tmp / "geographie")
    shutil.copy2(GUI / "zones_pays.json", gui_tmp)
    overlay = GUI / "static" / "geo_overlays" / f"{scenario}.geojson"
    if overlay.exists():
        shutil.copy2(overlay, gui_tmp / "static" / "geo_overlays")
    return tmp, ZoneRepository(vault_tmp, gui_tmp)


def entrees(repo, scenario, pays):
    return [(z["slug"], z.get("niveau"), o.get("type_entite"))
            for z in repo.load_all_zones(scenario)
            for o in (z.get("origine_reelle") or [])
            if isinstance(o, dict) and o.get("entite") == pays]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="reference")
    ap.add_argument("--pays", default="Écosse")
    a = ap.parse_args()

    tmp, repo = copie_temporaire(a.scenario)
    try:
        avant = entrees(repo, a.scenario, a.pays)
        if not avant:
            print(f"✗ « {a.pays} » absent de geographie/{a.scenario}.md — choisir un autre --pays.")
            return 1
        attendu = repo._type_entite_origine(repo.load_all_zones(a.scenario), a.pays)
        print(f"Avant : {avant}")
        print(f"Type attendu après réaffectation : {attendu}")

        zones_n1 = [z["slug"] for z in repo.load_all_zones(a.scenario) if int(z.get("niveau") or 1) == 1]
        source = {s for s, _, _ in avant}
        cible = next((s for s in zones_n1 if s not in source), None)
        if not cible:
            print("✗ Aucune autre zone N1 pour tester « absorber ».")
            return 1

        ok = True
        repo.assign_pays(a.scenario, a.pays, "absorber", zone_slug=cible)
        apres = [e for e in entrees(repo, a.scenario, a.pays) if e[0] == cible]
        bon = bool(apres) and apres[0][2] == attendu
        ok &= bon
        print(f"{'✓' if bon else '✗'} absorber → {cible} : {apres}")

        repo.assign_pays(a.scenario, a.pays, "creer",
                         nouvelle_zone={"slug": "zone_test_type_entite", "nom": "Zone test"})
        apres = [e for e in entrees(repo, a.scenario, a.pays) if e[0] == "zone_test_type_entite"]
        bon = bool(apres) and apres[0][2] == attendu
        ok &= bon
        print(f"{'✓' if bon else '✗'} créer → zone_test_type_entite : {apres}")

        print("\n" + ("✓ Correctif vérifié." if ok else "✗ Échec — ne pas redémarrer Flask avant de regarder."))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
