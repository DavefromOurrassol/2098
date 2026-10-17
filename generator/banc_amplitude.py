#!/usr/bin/env python3
"""
banc_amplitude.py -- Ourrassol 2098 (S19, 17 octobre 2026)
==========================================================
Diagnostic EN LECTURE SEULE pour juger GAIN_CHOCS avant tout réglage.
Aucun appel IA, aucune écriture dans le vault.

Partie 1 -- « Un choc type » : pour chaque variable et chaque scénario, on ajoute
au monde actuel un choc de force 10, monté en 3 ans à partir de 2060,
persistance normale, propagé. On mesure l'écart (avec − sans) : pic, année du
pic et reste en 2098. On compare plusieurs valeurs de GAIN_CHOCS.

Partie 2 -- « Le monde actuel » : les injections DÉJÀ présentes (entités,
événements, signaux, ruptures) sont recalculées avec chaque GAIN_CHOCS. On
mesure de combien les 72 niveaux de 2098 bougeraient si l'on changeait le gain
(c'est le prix d'un réglage : tout le monde existant se déplace).

Usage, depuis la racine du coffre :
    python3 generator/banc_amplitude.py                    # gains 0,25 / 0,4 / 0,6
    python3 generator/banc_amplitude.py --gains 0.25,0.5
Écrit aussi documentation/need_action/banc_amplitude.md (rapport, rien d'autre).
"""
import argparse
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))

import dynamique as dyn            # noqa: E402
import trace_injection as ti       # noqa: E402
from loader import load_custom_signals, VALID_SCENARIOS  # noqa: E402

FORCE, DUREE, T0, FIN = 10.0, 3.0, 2060.0, 2098.0


def v(x, d=1):
    return f"{x:+.{d}f}".replace(".", ",")


def simuler(donnees, chocs, ruptures, gain, ech=None):
    variables, ref, params, liens, k = donnees
    ancien = dyn.GAIN_CHOCS
    dyn.GAIN_CHOCS = gain
    try:
        return dyn.simuler(variables, ref, params, liens, chocs, FIN, echantillonner=ech, k=k,
                           ruptures=ruptures or None)
    finally:
        dyn.GAIN_CHOCS = ancien


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--gains", default="0.25,0.4,0.6")
    a = ap.parse_args()
    gains = [float(g) for g in a.gains.split(",")]
    signaux = load_custom_signals()
    scenarios = list(VALID_SCENARIOS)
    L = [f"# Banc d'amplitude des chocs (GAIN_CHOCS actuel : {dyn.GAIN_CHOCS:g})", "",
         f"Gains comparés : {', '.join(f'{g:g}' for g in gains)}. Lecture seule.", ""]

    # ── Partie 1 : choc type ─────────────────────────────────────────────
    # Le moteur est linéaire en x : l'écart du monde + choc = écart du monde + écart du
    # choc seul. On simule donc le monde UNE fois par gain, puis chaque choc seul (rapide) ;
    # seule la sortie (plafond doux, référence déplacée par les ruptures) est recomposée.
    res1 = {}   # (var, sc, gain) -> (pic, annee_pic, reste, niveau sans le choc)
    base, mondes = {}, {}
    for sc in scenarios:
        variables, ref, params, liens, k, inst, evs = ti._donnees_scenario(sc)
        donnees = (variables, ref, params, liens, k)
        chocs = dyn.chocs_depuis_donnees(sc, inst, evs, signaux)
        rupt = dyn.ruptures_depuis_donnees(evs) if hasattr(dyn, "ruptures_depuis_donnees") else []
        base[sc] = (donnees, chocs, rupt, ref)

        def niveau(var, t, x):
            d = sum(dyn.rampe_rupture(r, t) for r in rupt if r["variable"] == var)
            return dyn.niveau_sature(dyn.reference_deplacee(ref[var], d), x)

        for g in sorted(set(gains + [dyn.GAIN_CHOCS])):
            sans = simuler(donnees, chocs, rupt, g, ech=0.5)
            mondes[(sc, g)] = sans["niveaux"]
            if g not in gains:
                continue
            xs = sans["ecarts_traj"]
            for var in variables:
                choc = {"nom": "[banc]", "type": "evenement", "variable": var, "t0": T0, "duree": DUREE,
                        "via_matrice": True, "persistance": "normale", "fin": None, "amplitude": FORCE}
                seul = simuler(donnees, [choc], [], g, ech=0.5)
                serie = [(t, niveau(var, t, xa[var] + xc[var]) - niveau(var, t, xa[var]))
                         for (t, xa), (_, xc) in zip(xs, seul["ecarts_traj"]) if t >= T0]
                t_pic, pic = max(serie, key=lambda p: abs(p[1]))
                x_fin = sans["ecarts"][var]
                reste = niveau(var, FIN, x_fin + seul["ecarts"][var]) - niveau(var, FIN, x_fin)
                res1[(var, sc, g)] = (pic, t_pic, reste, sans["niveaux"][var])
        print(f"  {sc} fait", file=sys.stderr)

    variables = base[scenarios[0]][0][0]
    L += ["## 1. Un choc type (force 10, montée 3 ans, en 2060, persistance normale)", "",
          "Écart dû au choc sur SA variable : pic (année du pic) → reste en 2098. "
          "Médiane des scénarios où la variable n'est pas saturée (niveau sans le choc < 95) ; "
          "entre crochets, le nombre de scénarios saturés.", "",
          "| Variable | " + " | ".join(f"gain {g:g}" for g in gains) + " |",
          "|---|" + "---|" * len(gains)]
    for var in variables:
        cellules = []
        for g in gains:
            ok = [res1[(var, sc, g)] for sc in scenarios if res1[(var, sc, g)][3] < 95]
            sat = len(scenarios) - len(ok)
            if not ok:
                cellules.append(f"saturée [{sat}]")
                continue
            ok.sort(key=lambda r: abs(r[0]))
            pic, t_pic, reste, _ = ok[len(ok) // 2]
            cellules.append(f"{v(pic)} ({t_pic:.0f}) → {v(reste)}" + (f" [{sat}]" if sat else ""))
        L.append(f"| {var} | " + " | ".join(cellules) + " |")
    L.append("")

    # ── Partie 2 : le monde actuel ───────────────────────────────────────
    L += ["## 2. Le monde actuel recalculé avec chaque gain", "",
          f"Écart des niveaux de 2098 à ceux du gain actuel ({dyn.GAIN_CHOCS:g}) : "
          "moyenne des |écarts|, plus grand écart, nombre de niveaux qui bougent d'au moins 1 point, "
          "et nombre de variables ≥ 99 (saturées).", "",
          "| Scénario | " + " | ".join(f"gain {g:g}" for g in gains) + " |",
          "|---|" + "---|" * len(gains)]
    for sc in scenarios:
        actuel = mondes[(sc, dyn.GAIN_CHOCS)]
        cellules = []
        for g in gains:
            n = mondes[(sc, g)]
            ecarts = [n[x] - actuel[x] for x in n]
            plus = max(ecarts, key=abs)
            cellules.append(f"moy {sum(abs(e) for e in ecarts) / len(ecarts):.1f}".replace(".", ",")
                            + f", max {v(plus)}, ≥1 pt : {sum(1 for e in ecarts if abs(e) >= 1)}"
                            + f", ≥99 : {sum(1 for x in n.values() if x >= 99)}")
        L.append(f"| {sc} ({len(base[sc][1])} chocs) | " + " | ".join(cellules) + " |")
    L += ["", "_Rappel : le mode rupture n'est pas concerné par GAIN_CHOCS ; ce banc ne mesure que les chocs._"]

    sortie = GEN.parent / "documentation" / "need_action" / "banc_amplitude.md"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\n→ {sortie.relative_to(GEN.parent)}", file=sys.stderr)


if __name__ == "__main__":
    main()
