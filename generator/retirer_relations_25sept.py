#!/usr/bin/env python3
"""
Script ponctuel (25 sept 2026, suite de l'audit du lore fortress_world) —
retire 6 relations précises, décidées par David :

  - 5 relations inter-scénarios (erreurs de génération : une fiche
    fortress_world opposée à une fiche d'un autre scénario). Les 2 alliés
    `_reference` de la NAT sont conservés (décision David).
  - Vikram ne s'oppose pas à sa nièce Hyphan.

Passe par fix_alliances_oppositions.write_alliances_patch() (frontmatter
alliances/oppositions + section « ## Relations » du corps), .bak par fiche.

Usage (depuis la racine du vault) :
  python3 generator/retirer_relations_25sept.py            # aperçu
  python3 generator/retirer_relations_25sept.py --execute  # écriture
"""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_alliances_oppositions import INSTANCES_DIR, parse_md, write_alliances_patch  # noqa: E402

# (fiche, champ, relation à retirer)
A_RETIRER = [
    ("bureau_gouvernance_algorithmique_fortress_world", "oppositions",
     "collectifs_de_desobeissance_algorithmique_new_sustainability"),
    ("conseil_regulation_algorithmique_fortress_world", "oppositions",
     "conseil_regulation_algorithmique_new_sustainability"),
    ("grille_aria_fortress_world", "oppositions",
     "collectifs_de_desobeissance_algorithmique_new_sustainability"),
    ("nexcore_fortress_world", "oppositions", "nexcore_new_sustainability"),
    ("voix_du_dehors_fortress_world", "oppositions",
     "services_de_contre_information_des_blocs_geopolitiques_concurrents_reference"),
    ("vikram_raghavan_fortress_world", "oppositions", "hyphan_raghavan_fortress_world"),
]


def main():
    execute = "--execute" in sys.argv
    print(f"Mode : {'ÉCRITURE' if execute else 'APERÇU (rien écrit)'}\n")
    par_fiche, erreurs = {}, 0
    for slug, champ, ref in A_RETIRER:
        par_fiche.setdefault(slug, []).append((champ, ref))

    plan = {}
    for slug, retraits in par_fiche.items():
        path = INSTANCES_DIR / f"{slug}.md"
        if not path.exists():
            print(f"  ✗ {slug} : fiche introuvable")
            erreurs += 1
            continue
        fm, _ = parse_md(path)
        al = list(fm.get("alliances") or [])
        op = list(fm.get("oppositions") or [])
        for champ, ref in retraits:
            liste = al if champ == "alliances" else op
            if ref in liste:
                liste.remove(ref)
                print(f"  ✓ {slug} : retrait de {ref} ({champ})")
            else:
                print(f"  · {slug} : {ref} absent de {champ} (déjà retiré ?)")
        if al != list(fm.get("alliances") or []) or op != list(fm.get("oppositions") or []):
            plan[path] = (al, op)

    if erreurs:
        print(f"\n{erreurs} anomalie(s) — rien écrit. Envoie cette sortie à Claude.")
        sys.exit(1)
    if not plan:
        print("\nRien à faire.")
        return
    if not execute:
        print(f"\n{len(plan)} fiche(s) à modifier. Relance avec --execute pour écrire.")
        return
    for path, (al, op) in plan.items():
        shutil.copy2(path, path.with_suffix(".md.bak"))
        write_alliances_patch(path, al, op)
        if not al and not op:
            # write_alliances_patch() ne touche pas au corps quand les deux
            # listes sont vides : l'ancienne section « ## Relations » (avec le
            # lien retiré) resterait. On la retire ici.
            raw = path.read_text(encoding="utf-8")
            m = re.match(r"^(---\s*\n.*?\n---\s*\n)(.*)", raw, re.DOTALL)
            corps = re.sub(r"\n## Relations\n(?:.*?\n)*?(?=\n## |\Z)", "\n", m.group(2))
            path.write_text(m.group(1) + corps, encoding="utf-8")
        fm, _ = parse_md(path)
        ok = (fm.get("alliances") or []) == al and (fm.get("oppositions") or []) == op
        print(f"  écrit : {path.name} (+ .bak){'' if ok else '  ✗ relecture non conforme'}")


if __name__ == "__main__":
    main()
