#!/usr/bin/env python3
"""
check_type_entite_coherence.py — Ourrassol 2098

Détecte les entrées origine_reelle sans `type_entite` du tout (trouvé le 14
juillet en creusant les cas Ouagadougou et Genève-Bunker/Pologne — un oubli
de champ à l'écriture, pas une modélisation volontaire). Une comparaison
stricte `type_entite == "pays"` ailleurs dans le pipeline (notamment
check_origine_reelle_coherence.py) ignore silencieusement ces entrées,
produisant des faux positifs et masquant des candidats de reparent valides.

Approche texte, pas YAML, pour l'écriture : un re-dump YAML complet
(yaml.safe_dump) reformatterait tout le fichier (ordre des clés, quoting,
commentaires) sur 3000+ lignes -- bien trop invasif pour corriger 2 lignes
manquantes. Le script repère la ligne exacte `- entite: X` et insère
`type_entite:`/`portion:` juste après, sans toucher au reste du fichier.

USAGE
-----
    python3 check_type_entite_coherence.py --all                 # diagnostic, lecture seule
    python3 check_type_entite_coherence.py --scenario breakdown
    python3 check_type_entite_coherence.py --all --apply          # corrige, backup .bak automatique
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

from check_origine_reelle_coherence import _tokens, _normaliser  # source unique, réutilisée

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
GUI_DIR = VAULT_ROOT / "gui"
ZONES_PAYS = GUI_DIR / "zones_pays.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

ENTITE_RE = re.compile(r'^(\s*)- entite:\s*(.+?)\s*$')
TYPE_ENTITE_RE = re.compile(r'^\s*type_entite:')
SLUG_RE = re.compile(r'^- slug:\s*(.+?)\s*$')


def detecter_entrees_sans_type(texte: str, pays_liste_norm: set) -> list:
    """
    Scan ligne par ligne (pas de parsing YAML) : repère chaque `- entite: X`
    dont le type_entite est absent -- l'entrée est structurellement
    incomplète. Associe à chaque entrée la zone en cours (dernier
    `- slug:` vu) et une proposition de type ("pays" si le nom correspond
    exactement à la liste de référence, None sinon -- jamais deviné pour
    ville/region_administrative, trop risqué en auto).

    Gère les scalaires YAML repliés sur plusieurs lignes (ex. une valeur
    `entite` trop longue continuée sur la ligne suivante, plus indentée,
    avant le vrai `type_entite:`) -- sans ça, une valeur repliée peut être
    prise à tort pour une entrée incomplète, avec le risque qu'--apply
    insère les nouvelles lignes au mauvais endroit et corrompe le YAML.
    """
    lignes = texte.split("\n")
    resultats = []
    slug_courant = None

    for i, ligne in enumerate(lignes):
        m_slug = SLUG_RE.match(ligne)
        if m_slug:
            slug_courant = m_slug.group(1)
            continue

        m = ENTITE_RE.match(ligne)
        if not m:
            continue
        indent, entite_brut = m.group(1), m.group(2).strip("'\"")
        indent_len = len(indent)

        # Avancer au-delà des lignes de continuation d'un scalaire replié
        # (plus indentées que ne le serait une clé sœur type_entite/portion)
        j = i + 1
        while (
            j < len(lignes)
            and lignes[j].strip() != ""
            and (len(lignes[j]) - len(lignes[j].lstrip(" "))) > indent_len + 2
        ):
            entite_brut += " " + lignes[j].strip()
            j += 1
        derniere_ligne_entree = j - 1

        suivante = lignes[j] if j < len(lignes) else ""
        if TYPE_ENTITE_RE.match(suivante):
            continue  # déjà complet, rien à signaler

        entite_norm = entite_brut.lower().strip()
        propose = "pays" if entite_norm in pays_liste_norm else None

        resultats.append({
            "ligne_index": derniere_ligne_entree,
            "indent": indent,
            "entite": entite_brut,
            "zone_slug": slug_courant,
            "propose": propose,
        })
    return resultats


def reparer_fichier(path: Path, entrees: list) -> int:
    """
    Insère `type_entite: pays` + `portion: null` après chaque entrée
    confirmée (propose == "pays"), du bas vers le haut du fichier pour ne
    jamais décaler les indices déjà traités. Backup .bak avant écriture.
    Retourne le nombre d'entrées effectivement corrigées.
    """
    a_corriger = [e for e in entrees if e["propose"] == "pays"]
    if not a_corriger:
        return 0

    texte = path.read_text(encoding="utf-8")
    lignes = texte.split("\n")

    for e in sorted(a_corriger, key=lambda e: e["ligne_index"], reverse=True):
        indent_enfant = e["indent"] + "  "
        nouvelles_lignes = [
            f"{indent_enfant}type_entite: pays",
            f"{indent_enfant}portion: null",
        ]
        i = e["ligne_index"]
        lignes[i + 1:i + 1] = nouvelles_lignes

    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text(texte, encoding="utf-8")
    path.write_text("\n".join(lignes), encoding="utf-8")
    return len(a_corriger)


def check_scenario(scenario: str, pays_liste_norm: set, appliquer: bool) -> dict:
    print(f"\n=== {scenario} ===")
    geo_file = GEO_DIR / f"{scenario}.md"
    if not geo_file.exists():
        print(f"  ✗ Fiche introuvable : {geo_file}")
        return {"corrigees": 0, "indeterminees": []}

    texte = geo_file.read_text(encoding="utf-8")
    entrees = detecter_entrees_sans_type(texte, pays_liste_norm)

    if not entrees:
        print(f"  ✓ Aucune entrée sans type_entite")
        return {"corrigees": 0, "indeterminees": []}

    confirmees = [e for e in entrees if e["propose"] == "pays"]
    indeterminees = [e for e in entrees if e["propose"] is None]

    print(f"  ⚠ {len(entrees)} entrée(s) sans type_entite "
          f"({len(confirmees)} reconnue(s) comme pays, {len(indeterminees)} indéterminée(s))")

    for e in confirmees:
        marque = "→ corrigée" if appliquer else "→ serait corrigée (relancer avec --apply)"
        print(f"      - {e['zone_slug']!r} : {e['entite']!r} {marque}")
    for e in indeterminees:
        print(f"      - {e['zone_slug']!r} : {e['entite']!r} → type indéterminé, "
              f"probablement ville/region_administrative, à corriger manuellement")

    corrigees = 0
    if appliquer and confirmees:
        corrigees = reparer_fichier(geo_file, entrees)
        print(f"  ✓ {corrigees} entrée(s) corrigée(s), backup : {geo_file.with_suffix('.md.bak')}")

    return {"corrigees": corrigees, "indeterminees": indeterminees}


def main():
    parser = argparse.ArgumentParser(
        description="Détecte (et corrige avec --apply) les entrées origine_reelle "
                     "sans type_entite. Lecture seule par défaut."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", help="Scénario unique à vérifier")
    group.add_argument("--all", action="store_true", help="Vérifier les 6 scénarios")
    parser.add_argument(
        "--apply", action="store_true",
        help="Corrige les entrées reconnues comme pays (type_entite: pays + "
             "portion: null). Backup .bak automatique. Sans ce flag : aperçu seul."
    )
    args = parser.parse_args()

    if not ZONES_PAYS.exists():
        print(f"✗ {ZONES_PAYS} introuvable.")
        sys.exit(1)
    import json
    zones_pays = json.loads(ZONES_PAYS.read_text(encoding="utf-8"))
    pays_liste_norm = {p.lower().strip() for p in zones_pays.get("pays_liste", [])}

    scenarios = SCENARIOS if args.all else [args.scenario]
    if args.scenario and args.scenario not in SCENARIOS:
        print(f"✗ Scénario inconnu : {args.scenario}")
        print(f"  Scénarios valides : {', '.join(SCENARIOS)}")
        sys.exit(1)

    print("=" * 60)
    print("  Cohérence type_entite — geographie/{scenario}.md")
    print("=" * 60)

    total_corrigees = 0
    total_indeterminees = 0
    for s in scenarios:
        r = check_scenario(s, pays_liste_norm, args.apply)
        total_corrigees += r["corrigees"]
        total_indeterminees += len(r["indeterminees"])

    print("\n" + "=" * 60)
    if args.apply:
        print(f"  Terminé — {total_corrigees} entrée(s) corrigée(s), "
              f"{total_indeterminees} indéterminée(s) restante(s) (manuel).")
    else:
        print(f"  Terminé — aperçu affiché (relancer avec --apply pour corriger).")
    print("=" * 60)


if __name__ == "__main__":
    main()
