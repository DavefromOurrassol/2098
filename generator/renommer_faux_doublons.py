#!/usr/bin/env python3
"""S24 — renomme 5 fiches d'instance (faux doublons de nom). Slugs inchangés.

Usage (depuis la racine du vault) :
    python3 generator/renommer_faux_doublons.py           # aperçu, rien n'est écrit
    python3 generator/renommer_faux_doublons.py --apply   # écrit (.bak_nom par fichier)

Refuse un second passage sur une fiche déjà renommée.
"""
import shutil
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent

# (fichier, nouveau nom, fragment à ne plus trouver, remplacements du plus long au plus court)
RENOMMAGES = [
    ("instances/amazonie_consortium_viva_reference.md", "BioPatente Amazonas", "Consortium Viva", [
        ("Amazonie Consortium Viva", "BioPatente Amazonas"),
        ("le Consortium Viva", "BioPatente Amazonas"),
        ("Le Consortium Viva", "BioPatente Amazonas"),
        ("du Consortium Viva", "de BioPatente Amazonas"),
        ("au Consortium Viva", "à BioPatente Amazonas"),
        ("Consortium Viva", "BioPatente Amazonas"),
    ]),
    ("instances/amazonie_pacte_vert_fortress_world.md", "Label des Sanctuaires Souverains", "Pacte Vert", [
        ("Pacte Vert Amazônia — Division Sanctuaires Souverains", "Label des Sanctuaires Souverains"),
        ("Pacte Vert Amazônia", "Label des Sanctuaires Souverains"),
        ("Pacte Vert", "Label"),
    ]),
    ("instances/campements_seuils_fermes_fortress_world.md", "Les Campements des Checkpoints", "Seuils Fermés", [
        ("Les Seuils Fermés — Réseau des Campements Périphériques", "Les Campements des Checkpoints"),
        ("Campements des Seuils Fermés", "Campements des Checkpoints"),
    ]),
    ("instances/institut_des_seuils_demographiques_new_sustainability.md",
     "Observatoire Mondial des Dynamiques Démographiques (OMDD)", "Seuil —", [
        ("Seuil — Observatoire Mondial des Dynamiques Démographiques",
         "Observatoire Mondial des Dynamiques Démographiques"),
        ("S-OMDD", "OMDD"),
    ]),
    ("instances/trame_bioclimatique_breakdown.md", "Trame Bioclimatique — les Arcs Orphelins", "Cicatrices", [
        ("name: Les Cicatrices Vertes", "name: Trame Bioclimatique — les Arcs Orphelins"),
        ("# Les Cicatrices Vertes", "# Trame Bioclimatique — les Arcs Orphelins"),
        ("Cicatrices Vertes", "Arcs Orphelins"),
    ]),
]


def main():
    apply = "--apply" in sys.argv
    print("ÉCRITURE" if apply else "APERÇU (rien n'est écrit)")
    for rel, nouveau, fragment, regles in RENOMMAGES:
        p = VAULT / rel
        if not p.exists():
            print(f"✗ {rel} : introuvable")
            continue
        t = p.read_text(encoding="utf-8")
        name_ligne = next((l for l in t.splitlines() if l.startswith("name:")), "")
        if nouveau in name_ligne:
            print(f"· {rel} : déjà renommé — rien fait")
            continue
        total = 0
        for a, b in regles:
            total += t.count(a)
            t = t.replace(a, b)
        reste = t.count(fragment)
        print(f"{'✓' if apply else '→'} {rel} : {total} remplacement(s) ; "
              f"reste « {fragment} » : {reste}")
        if apply:
            shutil.copy(p, str(p) + ".bak_nom")
            p.write_text(t, encoding="utf-8")
    if not apply:
        print("\nRelancer avec --apply pour écrire.")


if __name__ == "__main__":
    main()
