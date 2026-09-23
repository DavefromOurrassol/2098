"""
Test en lecture seule de zone_repository.py contre les vraies données du
vault. N'écrit RIEN (dry_run=True partout, aucun appel à personnaliser()
qui lui écrit directement) -- safe à lancer sur le vault réel.

Usage : à lancer depuis gui/ (là où vit app.py et config.json) :
    python3 test_zone_repository_dryrun.py [scenario] [slug_zone]

Sans argument, utilise fortress_world / zone_euro_sud par défaut.
"""

import json
import sys
from pathlib import Path

from zone_repository import ZoneRepository, ZoneRepositoryError

GUI_DIR = Path(__file__).parent
config = json.loads((GUI_DIR / "config.json").read_text(encoding="utf-8"))
vault_root = Path(config["vault_root"])

scenario = sys.argv[1] if len(sys.argv) > 1 else "fortress_world"
slug = sys.argv[2] if len(sys.argv) > 2 else "zone_euro_sud"

repo = ZoneRepository(vault_root, GUI_DIR)

print(f"── vault_root : {vault_root}")
print(f"── gui_dir    : {GUI_DIR}")
print(f"── scénario   : {scenario}")
print(f"── zone       : {slug}\n")

print("=== 1) Rapport d'impact d'un renommage (dry-run, n'écrit rien) ===")
try:
    rapport = repo.rename(scenario, slug, slug + "_test_dryrun", dry_run=True)
    print(json.dumps(rapport, indent=2, ensure_ascii=False))
except ZoneRepositoryError as e:
    print(f"Erreur métier (normal si le slug/scénario n'existe pas) : {e}")

print("\n=== 2) Couverture carte (pays masqués par overlay + couleur/motif hérités) ===")
try:
    couv = repo.couverture_carte(scenario)
    print(f"{len(couv['pays_masques'])} pays masqués par au moins un overlay :")
    for pays, slugs in couv["pays_masques"].items():
        print(f"  - {pays} -> {slugs}")
    print(f"\n{len(couv['overlays'])} overlays au total, couleur/motif résolus par héritage N1 :")
    for f in couv["overlays"][:5]:
        p = f["properties"]
        print(f"  - {p.get('zone_slug')} / {p.get('pays')} -> "
              f"couleur={p.get('couleur_effective')} motif={p.get('motif_effectif')}")
except ZoneRepositoryError as e:
    print(f"Erreur métier : {e}")

print("\n=== 3) Résolution couleur/motif hérités sur une sous-zone ===")
gf = repo._load_geo(scenario)
sous_zones = [z for z in gf.zones if int(z.get("niveau", 1)) != 1]
if sous_zones:
    test_slug = sous_zones[0]["slug"]
    couleur, motif = repo.couleur_motif_effectifs(gf.zones, test_slug)
    print(f"Sous-zone '{test_slug}' -> hérite couleur={couleur} motif={motif} de sa racine N1")
else:
    print("Aucune sous-zone trouvée dans ce scénario pour tester l'héritage.")

print("\n=== 4) Rapport d'impact d'un split (dry-run, extrait le 1er pays trouvé) ===")
try:
    zone_courante = repo._find(gf.zones, slug)
    origine = (zone_courante or {}).get("origine_reelle") or []
    premier_pays = next((o.get("entite") for o in origine if isinstance(o, dict) and o.get("entite")), None)
    if premier_pays:
        cible = {"mode": "nouvelle_zone_n1", "slug": "zone_test_split_dryrun",
                 "nom": "Zone Test Split", "type": "region", "statut": "stable",
                 "description": "Zone de test (dry-run, jamais créée)."}
        rapport_split = repo.split(scenario, slug, [premier_pays], cible, dry_run=True)
        print(f"Extraction de '{premier_pays}' hors de '{slug}' (simulation) :")
        print(json.dumps({k: v for k, v in rapport_split.items() if k != "source"},
                          indent=2, ensure_ascii=False))
    else:
        print("Zone sans origine_reelle exploitable, test split sauté.")
except ZoneRepositoryError as e:
    print(f"Erreur métier : {e}")

print("\n=== 5) Rapport d'impact d'un reparent (dry-run, promotion en N1 si sous-zone, sinon sauté) ===")
try:
    zone_courante = repo._find(gf.zones, slug)
    if zone_courante and int(zone_courante.get("niveau", 1)) != 1:
        rapport_reparent = repo.reparent(scenario, slug, None, dry_run=True)
        print(json.dumps(rapport_reparent, indent=2, ensure_ascii=False))
    else:
        print(f"'{slug}' est déjà niveau 1 (ou introuvable) -- passe un slug de sous-zone en "
              f"argument pour tester ce cas (ex: {sys.argv[0]} {scenario} {test_slug if sous_zones else '<slug_n2>'})")
except ZoneRepositoryError as e:
    print(f"Erreur métier : {e}")

print("\nTerminé -- aucun fichier n'a été modifié.")
