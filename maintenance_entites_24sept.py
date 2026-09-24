#!/usr/bin/env python3
"""
maintenance_entites_24sept.py — Ourrassol 2098 (one-shot, 24 septembre 2026)

Suite de la création des 16 entités "Apocalypse Nerds". Trois opérations,
SIMULATION PAR DÉFAUT (rien n'est écrit sans --execute) :

  1. Renommage du slug `elias_m_rk` → `elias_mork` (bug de slugify sur "ø",
     corrigé le même jour dans create_entities_and_instances.py) :
     renomme les fichiers entites/ et instances/, puis remplace le slug
     partout dans les fichiers texte du vault (.md/.json/.yaml/.yml),
     hors .git et hors *.bak.
  2. Report des `consignes_scenarios` dans le frontmatter des fiches
     entités créées le 24 sept (lues dans entites_custom/processed.yaml),
     pour qu'une régénération par generate_instances.py les retrouve.
  3. Correction de localisation de deux instances `reference` :
       holdfast_reference                    → indo_pacifique_emergent
       ergo_wian_sovereign_holdings_reference → pacte_des_souverains

Chaque fichier modifié est relu (frontmatter YAML) avant écriture ; un
échec de relecture annule l'écriture de ce fichier.

USAGE (depuis la racine du vault)
    python3 maintenance_entites_24sept.py             # simulation
    python3 maintenance_entites_24sept.py --execute   # écrit
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent
ENTITES = VAULT / "entites"
INSTANCES = VAULT / "instances"
PROCESSED = VAULT / "entites_custom" / "processed.yaml"

ANCIEN, NOUVEAU = "elias_m_rk", "elias_mork"
SOURCE_LOT = "apocalypse_nerds_2026-09"
LOCALISATIONS = {
    "holdfast_reference": ("indo_pacifique_emergent", "Nouvelle-Zélande (Arc Indo-Pacifique)"),
    "ergo_wian_sovereign_holdings_reference": ("pacte_des_souverains",
                                               "Territoire associé du Pacte des Souverains"),
}
EXTS = {".md", ".json", ".yaml", ".yml"}


def frontmatter_ok(texte):
    m = re.match(r"^---\n(.*?)\n---", texte, re.S)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None


def ecrire(path, texte, execute, verifier_fm=True):
    if verifier_fm and path.suffix == ".md" and texte.startswith("---") and frontmatter_ok(texte) is None:
        print(f"    ✗ {path.relative_to(VAULT)} : frontmatter invalide après modification — NON écrit")
        return False
    if execute:
        path.write_text(texte, encoding="utf-8")
    return True


# ---------------------------------------------------------------- 1. slug
def renommer_slug(execute):
    print(f"\n[1] Renommage du slug {ANCIEN} → {NOUVEAU}")
    fichiers = [p for p in [ENTITES / f"{ANCIEN}.md"] + sorted(INSTANCES.glob(f"{ANCIEN}_*.md"))
                if p.exists()]
    if not fichiers and not any(True for _ in ENTITES.glob(f"{NOUVEAU}.md")):
        print("    ✗ Aucune fiche elias_m_rk trouvée — rien à faire.")
        return
    # Pas de \b : "_" compte comme caractère de mot, "elias_m_rk_reference"
    # ne serait pas trouvé. On exige seulement l'absence de lettre/chiffre autour.
    motif = re.compile(rf"(?<![A-Za-z0-9]){ANCIEN}(?![A-Za-z0-9])")
    n_fichiers = n_occ = 0
    for p in VAULT.rglob("*"):
        if (not p.is_file() or p.suffix not in EXTS or ".git" in p.parts
                or p.name.endswith(".bak")):
            continue
        try:
            t = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        k = len(motif.findall(t))
        if k:
            n_fichiers += 1
            n_occ += k
            print(f"    · {p.relative_to(VAULT)} : {k} occurrence(s)")
            ecrire(p, motif.sub(NOUVEAU, t), execute)
    for p in fichiers:
        cible = p.with_name(p.name.replace(ANCIEN, NOUVEAU, 1))
        if cible.exists():
            print(f"    ✗ {cible.relative_to(VAULT)} existe déjà — {p.name} non renommé")
            continue
        print(f"    · renommage {p.relative_to(VAULT)} → {cible.name}")
        if execute:
            p.rename(cible)
    print(f"    {n_occ} occurrence(s) dans {n_fichiers} fichier(s), {len(fichiers)} fichier(s) à renommer")


# ---------------------------------------------------- 2. consignes_scenarios
def reporter_consignes(execute):
    print("\n[2] Report des consignes_scenarios dans les fiches entités")
    if not PROCESSED.exists():
        print("    ✗ processed.yaml introuvable")
        return
    items = (yaml.safe_load(PROCESSED.read_text(encoding="utf-8")) or {}).get("processed") or []
    for it in items:
        idea = it.get("idea") or {}
        if SOURCE_LOT not in str(idea.get("source", "")):
            continue
        cons = {sc: " ".join(str(t).split()) for sc, t in (idea.get("consignes_scenarios") or {}).items()
                if sc in (it.get("scenarios") or []) and str(t).strip()}
        slug = str(it.get("slug", "")).replace(ANCIEN, NOUVEAU)
        path = ENTITES / f"{slug}.md"
        if not path.exists() and slug == NOUVEAU:
            path = ENTITES / f"{ANCIEN}.md"  # simulation : pas encore renommé
        if not cons:
            continue
        if not path.exists():
            print(f"    ✗ {slug} : fiche introuvable")
            continue
        t = path.read_text(encoding="utf-8")
        fm = frontmatter_ok(t)
        if fm is None:
            print(f"    ✗ {slug} : frontmatter illisible — ignoré")
            continue
        if fm.get("consignes_scenarios"):
            print(f"    = {slug} : déjà présent")
            continue
        bloc = yaml.dump({"consignes_scenarios": cons}, allow_unicode=True, sort_keys=False, width=1000)
        i = t.index("\n---", 3)
        nouveau = t[:i + 1] + bloc.rstrip("\n") + t[i:]
        if ecrire(path, nouveau, execute):
            print(f"    ✓ {slug} : {', '.join(cons)}")


# ---------------------------------------------------------- 3. localisation
def corriger_localisations(execute):
    print("\n[3] Localisations")
    for slug, (zone, lieu) in LOCALISATIONS.items():
        path = INSTANCES / f"{slug}.md"
        if not path.exists():
            print(f"    ✗ {slug} : fiche introuvable")
            continue
        t = path.read_text(encoding="utf-8")
        m = re.search(r"^localisation:\n((?:[ \t]+.*\n)+)", t, re.M)
        if not m:
            print(f"    ✗ {slug} : bloc 'localisation:' introuvable — à corriger à la main")
            continue
        bloc = m.group(1)
        avant = frontmatter_ok(t).get("localisation")
        nb = re.subn(r"^(\s+zone:).*$", rf"\g<1> {zone}", bloc, count=1, flags=re.M)
        if nb[1] != 1:
            print(f"    ✗ {slug} : ligne 'zone:' introuvable — à corriger à la main")
            continue
        bloc2 = re.sub(r"^(\s+lieu\w*:).*$", lambda mm: f"{mm.group(1)} '{lieu}'", nb[0], count=1, flags=re.M)
        nouveau = t[:m.start(1)] + bloc2 + t[m.end(1):]
        apres = (frontmatter_ok(nouveau) or {}).get("localisation")
        print(f"    · {slug}\n        avant : {avant}\n        après : {apres}")
        ecrire(path, nouveau, execute)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="écrit réellement (sinon simulation)")
    args = ap.parse_args()
    if not ENTITES.is_dir() or not INSTANCES.is_dir():
        sys.exit("À lancer depuis la racine du vault (dossiers entites/ et instances/ introuvables).")
    print("=" * 60)
    print("MAINTENANCE ENTITÉS 24 SEPT —", "EXÉCUTION" if args.execute else "SIMULATION (rien n'est écrit)")
    print("=" * 60)
    renommer_slug(args.execute)
    reporter_consignes(args.execute)
    corriger_localisations(args.execute)
    print("\nTerminé." + ("" if args.execute else " Relancer avec --execute pour appliquer."))


if __name__ == "__main__":
    main()
