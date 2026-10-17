#!/usr/bin/env python3
"""
retirer_relations.py — Ourrassol 2098 (S27, 13 octobre 2026)
============================================================

Retire des entités (instances disparues) des listes `alliances` et
`oppositions` de toutes les instances d'un scénario : frontmatter, et liste
à puces de la section « ## Relations » du corps. Avec --vider-propres, vide
aussi les relations des entités elles-mêmes.

Rien d'autre n'est touché : acteurs d'événements, articles, textes libres
gardent leurs mentions (l'histoire de l'entité reste).

Ne modifie que des lignes de liste (pas de réécriture YAML) ; une liste
vidée devient `alliances: []`. Le frontmatter est relu après modification.

USAGE
    python3 generator/retirer_relations.py --scenario breakdown --entites a_breakdown,b_breakdown [--vider-propres]          # aperçu
    python3 generator/retirer_relations.py --scenario breakdown --entites a_breakdown,b_breakdown [--vider-propres] --apply  # écrit (.bak_rel)
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent
CHAMPS = ("alliances", "oppositions")


def nettoie(item):
    """'- [[x|alias]]' / "- 'x'" / '- x' -> 'x'."""
    v = re.sub(r"^\s*-\s*", "", item).strip().strip("'\"")
    m = re.match(r"^\[\[([^\]|]+)(\|[^\]]*)?\]\]$", v)
    return (m.group(1) if m else v).strip()


def traiter_frontmatter(lignes, cibles, tout):
    """Retire les cibles (ou tout) des listes alliances/oppositions. Retourne (lignes, retraits)."""
    out, retraits, i = [], [], 0
    while i < len(lignes):
        l = lignes[i]
        m = re.match(r"^(alliances|oppositions):\s*(.*)$", l)
        if not m:
            out.append(l)
            i += 1
            continue
        champ, reste = m.group(1), m.group(2).strip()
        if reste.startswith("["):   # liste en ligne
            try:
                items = yaml.safe_load(reste) or []
            except yaml.YAMLError:
                out.append(l)
                i += 1
                continue
            garde = [x for x in items if not (tout or str(x) in cibles)]
            retraits += [f"{champ} : {x}" for x in items if x not in garde]
            out.append(f"{champ}: [{', '.join(str(x) for x in garde)}]" if garde else f"{champ}: []")
            i += 1
            continue
        if reste:            # valeur scalaire inattendue : on ne touche pas
            out.append(l)
            i += 1
            continue
        j, items = i + 1, []
        while j < len(lignes) and re.match(r"^\s*-\s+", lignes[j]):
            items.append(lignes[j])
            j += 1
        garde = [x for x in items if not (tout or nettoie(x) in cibles)]
        retraits += [f"{champ} : {nettoie(x)}" for x in items if x not in garde]
        out.append(f"{champ}:" if garde else f"{champ}: []")
        out += garde
        i = j
    return out, retraits


def traiter_corps(corps, cibles, tout):
    """Retire les puces de la section « ## Relations ». Retourne (corps, retraits)."""
    lignes, out, dans, retraits = corps.split("\n"), [], False, []
    for l in lignes:
        if re.match(r"^##\s", l):
            dans = bool(re.match(r"^##\s+Relations\b", l))
        if dans and re.match(r"^\s*-\s+", l) and (tout or nettoie(l) in cibles):
            retraits.append(f"corps : {nettoie(l)}")
            continue
        out.append(l)
    return "\n".join(out), retraits


def main():
    ap = argparse.ArgumentParser(description="Retire des entités des relations d'un scénario (aperçu par défaut).")
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--entites", required=True, help="slugs séparés par des virgules")
    ap.add_argument("--vider-propres", action="store_true", help="vide aussi les relations de ces entités")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    cibles = {s.strip() for s in a.entites.split(",") if s.strip()}
    manquants = [s for s in cibles if not (VAULT / "instances" / f"{s}.md").exists()]
    if manquants:
        sys.exit(f"✗ Fiche(s) introuvable(s) : {', '.join(sorted(manquants))}")

    a_ecrire, rapport, erreurs = [], [], []
    for p in sorted((VAULT / "instances").glob(f"*_{a.scenario}.md")):
        texte = p.read_text(encoding="utf-8")
        m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", texte, re.S)
        if not m:
            continue
        propre = p.stem in cibles
        tout = propre and a.vider_propres
        fm_l, r1 = traiter_frontmatter(m.group(2).split("\n"), cibles, tout)
        corps, r2 = traiter_corps(texte[m.end():], cibles, tout)
        if not (r1 or r2):
            continue
        fm_txt = "\n".join(fm_l)
        try:
            fm = yaml.safe_load(re.sub(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]", r"\1", fm_txt)) or {}
            reste = [x for c in CHAMPS for x in (fm.get(c) or []) if (tout or str(x) in cibles)]
            if reste:
                raise ValueError(f"encore présent(s) après retrait : {reste}")
        except (yaml.YAMLError, ValueError) as e:
            erreurs.append(f"{p.name} : {e}")
            continue
        a_ecrire.append((p, m.group(1) + fm_txt + m.group(3) + corps))
        rapport.append(f"  {p.stem}" + (" (relations propres vidées)" if tout else "")
                       + f" : {len(r1)} retrait(s) frontmatter, {len(r2)} dans le corps")

    print(("ÉCRITURE" if a.apply else "APERÇU (rien écrit)") + f" — {len(a_ecrire)} fiche(s), scénario {a.scenario}")
    print("\n".join(rapport) or "  (aucune)")
    if erreurs:
        print("\n✗ Refusé :")
        print("\n".join(f"  {e}" for e in erreurs))
        sys.exit("✗ Rien n'est écrit tant qu'une fiche est refusée.")
    if not a.apply:
        print("Relancer avec --apply pour écrire (sauvegarde .bak_rel).")
        return
    for p, nouveau in a_ecrire:
        bak = p.with_name(p.name + ".bak_rel")
        if not bak.exists():
            shutil.copy2(p, bak)
        p.write_text(nouveau, encoding="utf-8")
    print(f"✓ {len(a_ecrire)} fiche(s) écrite(s).")


if __name__ == "__main__":
    main()
