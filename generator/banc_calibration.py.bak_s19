#!/usr/bin/env python3
"""
banc_calibration.py — Ourrassol 2098
-------------------------------------
Banc de calibration du moteur dynamique (dynamique.py). LECTURE SEULE :
ne modifie aucune fiche, ne touche pas au pipeline, n'appelle aucun LLM.

Pour chaque scénario demandé :
  - charge variables, matrice et injections custom via loader.py ;
  - simule de 2025 à la date de fin (2098 par défaut) ;
  - écrit documentation/need_action/calibration/<scenario>.png
    (12 trajectoires, référence en pointillés) si matplotlib est
    disponible, sinon un CSV ;
  - affiche un tableau : référence, niveau final, écart, écart max et
    son année, plus le rayon spectral (stabilité des boucles).

Paramètres surchargeables en ligne de commande pour tester sans
modifier dynamique.py.

Usage (depuis generator/) :
  python3 banc_calibration.py                          # breakdown + new_sustainability
  python3 banc_calibration.py --scenarios all
  python3 banc_calibration.py --k 0.15 --demi-vie 15 --plafond 20
"""

import argparse
import csv
import sys
from pathlib import Path

import dynamique as dyn
from loader import (load_all_variables, load_influence_matrix, load_events_for_scenario,
                    load_instances_for_scenario, load_custom_signals, VALID_VARS, VALID_SCENARIOS)

SORTIE = Path(__file__).resolve().parent.parent / "documentation" / "need_action" / "calibration"
COURT = {
    "systeme_economique_redistribution": "économie", "gouvernance_institutions": "gouvernance",
    "geopolitique_conflits": "géopolitique", "valeurs_culture_tempo_sociale": "valeurs",
    "organisation_territoires": "territoires", "sante_biotechnologies": "santé",
    "frontieres_du_systeme": "espace", "technologie_information": "technologie",
    "climat_environnement_global": "climat", "energie_ressources_critiques": "énergie",
    "demographie_mobilite_humaine": "démographie", "systemes_productifs_travail": "production",
}


def lancer(scenario, all_vars, matrix, date_fin, signals):
    niveaux_ref, params = {}, {}
    for v in VALID_VARS:
        st = (all_vars[v].get("states") or {}).get(scenario) or {}
        try:
            niveaux_ref[v] = float(st.get("level"))
        except (TypeError, ValueError):
            niveaux_ref[v] = 50.0
        params[v] = dyn.parametres_variable(all_vars[v].get("simulation"))
    liens = dyn.couplages(VALID_VARS, matrix["edges"], params)
    chocs = dyn.chocs_depuis_donnees(scenario, load_instances_for_scenario(scenario),
                                     load_events_for_scenario(scenario), signals)
    res = dyn.simuler(VALID_VARS, niveaux_ref, params, liens, chocs, date_fin, echantillonner=0.5)
    return niveaux_ref, liens, chocs, res


def ecrire_sortie(scenario, niveaux_ref, res):
    SORTIE.mkdir(parents=True, exist_ok=True)
    traj = res["trajectoire"]
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        path = SORTIE / f"{scenario}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["annee"] + VALID_VARS)
            for t, niv in traj:
                w.writerow([t] + [round(niv[v], 2) for v in VALID_VARS])
        return path
    fig, axes = plt.subplots(3, 4, figsize=(16, 10), sharex=True)
    for ax, v in zip(axes.flat, VALID_VARS):
        ax.plot([t for t, _ in traj], [niv[v] for _, niv in traj], lw=1.8)
        ax.axhline(niveaux_ref[v], ls="--", lw=1, color="grey")
        ax.set_title(f"{COURT[v]} (réf. {niveaux_ref[v]:g})", fontsize=10)
        ax.set_ylim(0, 100)
        ax.grid(alpha=0.3)
    fig.suptitle(f"{scenario} — K={dyn.K_COUPLAGE}, gain={dyn.GAIN_CHOCS}, demi-vie={dyn.DEMI_VIE} ans, plafond=±{dyn.PLAFOND}")
    fig.tight_layout()
    path = SORTIE / f"{scenario}.png"
    fig.savefig(path, dpi=90)
    plt.close(fig)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarios", default="breakdown,new_sustainability",
                    help="liste séparée par des virgules, ou 'all'")
    ap.add_argument("--fin", type=float, default=2098.0)
    ap.add_argument("--k", type=float, help="K_COUPLAGE")
    ap.add_argument("--demi-vie", type=float, help="DEMI_VIE (années)")
    ap.add_argument("--plafond", type=float, help="PLAFOND (points)")
    ap.add_argument("--cycle", type=float, help="ANNEES_PAR_CYCLE")
    ap.add_argument("--gain", type=float, help="GAIN_CHOCS")
    ap.add_argument("--balayage-k", help="ex. 0.1,0.05,0.02 : tableau compact des écarts BRUTS "
                    "(avant plafond) pour plusieurs K, sans écrire de fichier")
    args = ap.parse_args()
    if args.k is not None: dyn.K_COUPLAGE = args.k
    if args.demi_vie is not None: dyn.DEMI_VIE = args.demi_vie
    if args.plafond is not None: dyn.PLAFOND = args.plafond
    if args.cycle is not None: dyn.ANNEES_PAR_CYCLE = args.cycle
    if args.gain is not None: dyn.GAIN_CHOCS = args.gain

    scenarios = VALID_SCENARIOS if args.scenarios == "all" else args.scenarios.split(",")
    all_vars = load_all_variables()
    matrix = load_influence_matrix()
    signals = load_custom_signals()

    if args.balayage_k:
        ks = [float(k) for k in args.balayage_k.split(",")]
        print(f"Balayage K (écarts BRUTS en 2098 avant plafond, et |max| sur 2025-2098) — "
              f"demi-vie={dyn.DEMI_VIE} ans, cycle={dyn.ANNEES_PAR_CYCLE} ans")
        for sc in scenarios:
            lignes = {v: [] for v in VALID_VARS}
            entete = []
            for k in ks:
                dyn.K_COUPLAGE = k
                niveaux_ref, liens, chocs, res = lancer(sc, all_vars, matrix, args.fin, signals)
                rho = dyn.rayon_spectral(VALID_VARS, liens)
                ampli = 1 / (1 - rho) if rho < 1 else float("inf")
                entete.append(f"K={k} (ρ={rho:.2f}, ×{ampli:.1f})")
                for v in VALID_VARS:
                    xs = [x for _, x in res["ecarts_traj"]]
                    xmax = max((abs(e[v]) for e in xs), default=0)
                    lignes[v].append(f"{res['ecarts'][v]:+7.1f} |{xmax:5.1f}|")
            print(f"\n=== {sc} — {len(chocs)} chocs")
            print(f"  {'variable':<13} " + "   ".join(f"{h:>22}" for h in entete))
            for v in VALID_VARS:
                print(f"  {COURT[v]:<13} " + "   ".join(f"{c:>22}" for c in lignes[v]))
        return 0

    print(f"Paramètres : K={dyn.K_COUPLAGE}  gain chocs={dyn.GAIN_CHOCS}  demi-vie={dyn.DEMI_VIE} ans  plafond=±{dyn.PLAFOND}  "
          f"cycle={dyn.ANNEES_PAR_CYCLE} ans")
    for sc in scenarios:
        niveaux_ref, liens, chocs, res = lancer(sc, all_vars, matrix, args.fin, signals)
        rho = dyn.rayon_spectral(VALID_VARS, liens)
        n_via = sum(1 for c in chocs if c["via_matrice"])
        print(f"\n=== {sc} — {len(chocs)} chocs ({n_via} propagés), rayon spectral K·C = {rho:.2f} "
              f"({'stable' if rho < 1 else 'INSTABLE'})")
        print(f"  {'variable':<13} {'réf':>5} {'final':>6} {'écart':>6}   {'écart max':>9} (année)")
        for v in VALID_VARS:
            devs = [(niv[v] - niveaux_ref[v], t) for t, niv in res["trajectoire"]]
            dmax, tmax = max(devs, key=lambda d: abs(d[0]))
            print(f"  {COURT[v]:<13} {niveaux_ref[v]:>5.0f} {res['niveaux'][v]:>6.1f} "
                  f"{res['niveaux'][v] - niveaux_ref[v]:>+6.1f}   {dmax:>+9.1f} ({tmax:.0f})")
        print(f"  → {ecrire_sortie(sc, niveaux_ref, res)}")


if __name__ == "__main__":
    sys.exit(main())
