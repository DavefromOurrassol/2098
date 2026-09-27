#!/usr/bin/env python3
"""
synchroniser_scenarios.py — Ourrassol 2098
-------------------------------------------
Étape 8 du chantier "convention unique d'intensité" (27 septembre 2026).

Les fiches scenarios/*.md contiennent une copie des niveaux de variables
(bloc `variable_states` du frontmatter + tableau "## 4A. États des
variables" du corps) qui n'est lue par AUCUN calcul (snapshot.py lit les
fiches variables) mais qui était déjà désynchronisée AVANT la migration
(ex. new_sustainability : technologie 95 ici contre 70 dans la fiche
variable) et l'est encore plus depuis (gouvernance/frontières inversées,
santé recalée).

Ce script aligne cette copie sur la source de vérité :
  - level  <- variables/{var}.md -> states.{scenario}.level
  - trend  : inversé (up <-> down) pour les 9 variables dont ce bloc
             suivait la logique "niveau favorable" (voir INVERSEES) ;
             inchangé pour géopolitique, territoires et frontières.
Le bloc est conservé (validate.py vérifie sa présence).

Par défaut : SIMULATION (affiche les changements, n'écrit rien).
--appliquer : sauvegarde unique .bak_etape8 (jamais écrasée), écriture,
relecture et vérification. Idempotent : les tendances ne sont inversées
qu'une fois (marqueur `convention_echelle` ajouté au frontmatter).

Usage (depuis la racine du vault) :
  python3 generator/synchroniser_scenarios.py
  python3 generator/synchroniser_scenarios.py --appliquer
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = VAULT_ROOT / "scenarios"
VARIABLES_DIR = VAULT_ROOT / "variables"
SCENARIOS = ["breakdown", "fortress_world", "new_sustainability",
             "eco_communalism", "policy_reform", "reference"]
# Variables dont le bloc variable_states des fiches scénario suivait la
# logique "niveau favorable" (niveau haut = bonne situation) : corrélation
# NÉGATIVE entre anciens niveaux du bloc et niveaux d'intensité des fiches
# variables sur les 6 scénarios (mesurée le 27 septembre 2026 : économie
# -0,61, gouvernance -0,66, valeurs -0,89, santé -0,86, technologie -0,33,
# climat -0,95, énergie -0,69, démographie -0,66, production -0,44).
# Leur tendance est inversée (up <-> down) pour passer en logique
# d'intensité. Non inversées (déjà en logique d'intensité ou ambiguës) :
# géopolitique (+0,95), territoires (+0,17), frontières (+0,49).
INVERSEES = {
    "systeme_economique_redistribution", "gouvernance_institutions",
    "valeurs_culture_tempo_sociale", "sante_biotechnologies",
    "technologie_information", "climat_environnement_global",
    "energie_ressources_critiques", "demographie_mobilite_humaine",
    "systemes_productifs_travail",
}
INVERSION_TREND = {"up": "down", "down": "up"}
MARQUEUR = "convention_echelle: intensite_2026-09-27"


def decouper(raw):
    return re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*\n", raw, re.DOTALL)


def yaml_propre(txt):
    return yaml.safe_load(re.sub(r"\[\[([^\]]+)\]\]", r"\1", txt)) or {}


def niveaux_reference():
    """{scenario: {variable: level}} lu dans variables/*.md"""
    out = {s: {} for s in SCENARIOS}
    for path in sorted(VARIABLES_DIR.glob("*.md")):
        m = decouper(path.read_text(encoding="utf-8"))
        if not m:
            continue
        fm = yaml_propre(m.group(1))
        if fm.get("type") != "systemic_variable":
            continue
        for sc, st in (fm.get("states") or {}).items():
            if sc in out and isinstance(st, dict) and st.get("level") not in (None, ""):
                out[sc][path.stem] = st["level"]
    return out


def traiter(path, niveaux, appliquer):
    raw = path.read_text(encoding="utf-8")
    m = decouper(raw)
    if not m:
        return [f"  ✗ {path.name} : frontmatter introuvable"], False
    fm_str, corps = m.group(1), raw[m.end():]
    scen = path.stem
    deja = MARQUEUR.split(":")[0] + ":" in fm_str
    cibles = niveaux.get(scen, {})
    fm_avant = yaml_propre(fm_str)
    vs_avant = fm_avant.get("variable_states") or {}

    # Valeurs attendues
    attendu = {}
    for var, d in vs_avant.items():
        d = d or {}
        trend = d.get("trend", "")
        if var in INVERSEES and not deja:
            trend = INVERSION_TREND.get(trend, trend)
        attendu[var] = {"level": cibles.get(var, d.get("level")), "trend": trend}

    # Frontmatter, ligne par ligne dans le bloc variable_states
    lignes = fm_str.split("\n")
    dans_bloc, var = False, None
    for i, l in enumerate(lignes):
        if re.match(r"^variable_states:\s*$", l):
            dans_bloc = True
            continue
        if dans_bloc and re.match(r"^\S", l):
            dans_bloc = False
        if not dans_bloc:
            continue
        mv = re.match(r"^\s{2}\[*([a-z_]+)\]*:\s*$", l)
        if mv:
            var = mv.group(1)
            continue
        if var in attendu:
            ml = re.match(r"^(\s+level:\s*)\S+\s*$", l)
            if ml:
                lignes[i] = f"{ml.group(1)}{attendu[var]['level']}"
            mt = re.match(r"^(\s+trend:\s*)\S*\s*$", l)
            if mt:
                lignes[i] = f"{mt.group(1)}{attendu[var]['trend']}"
    fm_neuf = "\n".join(lignes)
    if not deja:
        fm_neuf = fm_neuf.rstrip("\n") + "\n" + MARQUEUR

    # Corps : tableau 4A "| [[var]] | level | trend |"
    def repl(mm):
        v = mm.group(1)
        if v not in attendu:
            return mm.group(0)
        return f"| [[{v}]] | {attendu[v]['level']} | {attendu[v]['trend']} |"
    corps_neuf = re.sub(r"^\|[ \t]*\[\[([a-z_]+)\]\][ \t]*\|[^|\n]*\|[^|\n]*\|[ \t]*$", repl, corps, flags=re.M)

    nouveau = f"---\n{fm_neuf}\n---\n{corps_neuf}"
    rapport = []
    for v, d in vs_avant.items():
        d = d or {}
        a = attendu[v]
        if str(d.get("level")) != str(a["level"]) or d.get("trend", "") != a["trend"]:
            rapport.append(f"    {v:<36} level {d.get('level')!s:>3} → {a['level']!s:<3}  "
                           f"trend {d.get('trend', '')} → {a['trend']}")

    # Vérification
    vs_apres = yaml_propre(decouper(nouveau).group(1)).get("variable_states") or {}
    for v, a in attendu.items():
        d = vs_apres.get(v) or {}
        if str(d.get("level")) != str(a["level"]) or d.get("trend", "") != a["trend"]:
            return [f"  ✗ {path.name} : vérification échouée sur {v}, rien écrit"], False

    if appliquer and nouveau != raw:
        bak = path.with_suffix(path.suffix + ".bak_etape8")
        if not bak.exists():
            bak.write_text(raw, encoding="utf-8")
        path.write_text(nouveau, encoding="utf-8")
    entete = f"  ✓ {path.name} : {len(rapport)} variable(s) modifiée(s)" + (" (déjà synchronisé une fois)" if deja else "")
    return [entete] + rapport, True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--appliquer", action="store_true")
    args = ap.parse_args()
    print("=== SYNCHRO SCÉNARIOS — {} ===".format("ÉCRITURE RÉELLE" if args.appliquer else "SIMULATION (rien n'est écrit)"))
    niveaux = niveaux_reference()
    ok = True
    for sc in SCENARIOS:
        path = SCENARIOS_DIR / f"{sc}.md"
        if not path.exists():
            print(f"  ✗ {path.name} introuvable")
            ok = False
            continue
        lignes, res = traiter(path, niveaux, args.appliquer)
        ok = ok and res
        print("\n".join(lignes))
    if ok and not args.appliquer:
        print("\nRelance avec --appliquer pour écrire (sauvegardes .bak_etape8).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
