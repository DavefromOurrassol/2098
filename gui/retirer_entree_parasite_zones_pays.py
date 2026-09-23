#!/usr/bin/env python3
"""Retire une entrée non-pays ajoutée par erreur (via un nettoyage
générique) dans zones_pays.json[scenario] -- ex. "Balkans occidentaux"
après --nettoyer sur une entité non reconnue comme pays souverain (13 sept
2026). Sûr : n'écrit que si la clé est bien ABSENTE de pays_liste (donc
jamais un vrai pays), et passe par _save_zones_pays() pour le .bak
automatique."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from zone_repository import ZoneRepository, ZoneRepositoryError


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--entite", required=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    from app import load_config
    cfg = load_config()
    repo = ZoneRepository(Path(cfg.get("vault_root", "")), Path(__file__).parent)

    zp = repo._load_zones_pays()
    pays_liste = zp.get("pays_liste", [])
    if args.entite in pays_liste:
        print(f"Erreur : '{args.entite}' est un vrai pays (dans pays_liste) -- refus de la retirer.",
              file=sys.stderr)
        return 1

    sc = zp.get(args.scenario, {})
    if args.entite not in sc:
        print(f"'{args.entite}' n'est pas dans zones_pays.json['{args.scenario}'] -- rien à faire.")
        return 0

    slug = sc[args.entite]
    if not args.execute:
        print(f"[DRY-RUN] Retirerait '{args.entite}' -> '{slug}' de zones_pays.json['{args.scenario}']")
        return 0

    del sc[args.entite]
    zp[args.scenario] = sc
    repo._save_zones_pays(zp)
    print(f"Retiré : '{args.entite}' (-> '{slug}') de zones_pays.json['{args.scenario}']")
    return 0


if __name__ == "__main__":
    sys.exit(main())
