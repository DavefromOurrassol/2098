#!/usr/bin/env python3
"""
patch_u4f_force_par_scenario.py — Ourrassol 2098 (U4f, 15 novembre 2026)
========================================================================

Décision de David (15 nov, option b) : une hypothèse peut frapper un scénario plus
qu'un autre. `delta_level` d'un impact peut être un dictionnaire par scénario,
comme `polarite` :

    - variable: sante_biotechnologies
      delta_level: {breakdown: 35, fortress_world: 30, reference: 15, ...}
      polarite: -1

  - Tous les scénarios couverts doivent avoir une valeur (sinon erreur).
  - Événement ordinaire : chaque valeur de 1 à 25 (au-delà, avertissement, comme avant).
  - WILD CARD : 25 à 35 dans au moins un scénario, 10 au moins partout
    (WILD_CARD_FORCE_MIN_SC). Toujours 3 à 6 impacts.
  - Un nombre seul garde son sens : la même force partout.

Câblé dans la vérification, la simulation (chocs, ruptures), le rapport, la liste
d'application, l'entrée d'injection (impacts_imposes par scénario, déjà lu ainsi par
inject_custom_events.py) et ✨ Proposer (normalisation ; avec la case ⚡, l'IA peut
proposer des forces par scénario).

Fichiers : generator/simuler_et_si.py, generator/hypothese_depuis_texte.py.
USAGE (depuis la racine du vault)
    python3 generator/patch_u4f_force_par_scenario.py            # dry-run
    python3 generator/patch_u4f_force_par_scenario.py --apply
Sauvegardes .bak_u4f. Pas de relance de Flask (sous-processus). Exige U4a, U4c, U4d3.
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

GEN = Path.cwd() / "generator"
TAG = "U4f"

SE = [
    ("constante",
     '''WILD_CARD_FORCE = (25, 35)
''',
     '''WILD_CARD_FORCE = (25, 35)
WILD_CARD_FORCE_MIN_SC = 10    # U4f : force minimale d'une wild card dans un scénario moins touché


def force_sc(imp, sc):
    """U4f : force d'un impact normalisé dans le scénario `sc` (forces par scénario, sinon la force unique)."""
    return (imp.get("forces") or {}).get(sc, imp["force"])
'''),
    ("vérification : forces par scénario",
     '''        try:
            force = abs(float(imp.get("delta_level")))
        except (TypeError, ValueError):
            erreurs.append(f"impact {var} : delta_level absent ou non numérique")
            continue
        if force < 1:
            erreurs.append(f"impact {var} : delta_level doit valoir au moins 1")
        if wild and not est_signal:   # U4a
            if not WILD_CARD_FORCE[0] <= force <= WILD_CARD_FORCE[1]:
                erreurs.append(f"impact {var} : delta_level {force:g} hors de la plage d'une wild card "
                               f"({WILD_CARD_FORCE[0]} à {WILD_CARD_FORCE[1]})")
''',
     '''        brut_f = imp.get("delta_level")   # U4f : un nombre, ou un dictionnaire par scénario
        try:
            if isinstance(brut_f, dict):
                manquants = [s for s in scen if s not in brut_f]
                if manquants:
                    erreurs.append(f"impact {var} : delta_level absent pour {manquants}")
                    continue
                forces = {s: abs(float(brut_f[s])) for s in scen}
            else:
                forces = {s: abs(float(brut_f)) for s in scen}
        except (TypeError, ValueError):
            erreurs.append(f"impact {var} : delta_level absent ou non numérique")
            continue
        if not forces:
            continue
        force, force_min = max(forces.values()), min(forces.values())
        if force_min < 1:
            erreurs.append(f"impact {var} : delta_level doit valoir au moins 1")
        if wild and not est_signal:   # U4a / U4f
            if not WILD_CARD_FORCE[0] <= force <= WILD_CARD_FORCE[1] or force_min < WILD_CARD_FORCE_MIN_SC:
                erreurs.append(f"impact {var} : delta_level hors des règles d'une wild card ({WILD_CARD_FORCE[0]} à "
                               f"{WILD_CARD_FORCE[1]} dans au moins un scénario, {WILD_CARD_FORCE_MIN_SC} au moins "
                               f"partout ; reçu {force_min:g} à {force:g})")
'''),
    ("vérification : impact normalisé",
     '''        impacts.append({"variable": var, "force": force, "polarites": pols, "duree": duree})
''',
     '''        impacts.append({"variable": var, "force": force, "polarites": pols, "duree": duree,
                        "forces": forces})   # U4f : force par scénario (force = la plus forte)
'''),
    ("chocs",
     '''        "persistance": hyp["persistance"], "fin": None,
        "amplitude": imp["force"] * imp["polarites"][sc],
''',
     '''        "persistance": hyp["persistance"], "fin": None,
        "amplitude": force_sc(imp, sc) * imp["polarites"][sc],   # U4f
'''),
    ("ruptures",
     '''        "variable": imp["variable"], "t0": hyp["date"], "duree": imp["duree"],
        "amplitude": imp["force"] * imp["polarites"][sc],
''',
     '''        "variable": imp["variable"], "t0": hyp["date"], "duree": imp["duree"],
        "amplitude": force_sc(imp, sc) * imp["polarites"][sc],   # U4f
'''),
    ("lecture IA : forces du scénario",
     '''    impacts_txt = ", ".join(f"{i['variable']} (force {i['force']:g})" for i in hyp["impacts"]) or "aucun"
''',
     '''    impacts_txt = ", ".join(f"{i['variable']} (force {force_sc(i, sc):g})" for i in hyp["impacts"]
                            if sc in i["polarites"]) or "aucun"   # U4f
'''),
    ("rapport",
     '''        L.append(f"- Déclaré : **{imp['variable']}** — force {imp['force']:g}, {sens_txt}, montée sur {imp['duree']:g} ans")
''',
     '''        fs = sorted(set((imp.get("forces") or {}).values()) or {imp["force"]})   # U4f
        force_txt = (f"force {fs[0]:g}" if len(fs) == 1 else
                     "force " + ", ".join(f"{s} {f:g}" for s, f in imp["forces"].items()))
        L.append(f"- Déclaré : **{imp['variable']}** — {force_txt}, {sens_txt}, montée sur {imp['duree']:g} ans")
'''),
    ("liste d'application (rupture)",
     '''        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{i['force']:g}"
                           for i in hyp["impacts"] if sc in i["polarites"])
        _etape(E, "Élément", ("⚠ " if plafonnees else "")''',
     '''        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{force_sc(i, sc):g}"
                           for i in hyp["impacts"] if sc in i["polarites"])   # U4f
        _etape(E, "Élément", ("⚠ " if plafonnees else "")'''),
    ("liste d'application (choc)",
     '''        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{i['force']:g}"
                           for i in hyp["impacts"] if sc in i["polarites"])
        # V8.15''',
     '''        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{force_sc(i, sc):g}"
                           for i in hyp["impacts"] if sc in i["polarites"])   # U4f
        # V8.15'''),
    ("entrée d'injection d'un signal",
     '''              "impacts_imposes": {
                  sc: [{"variable": i["variable"], "delta_level": _nombre(i["force"]),''',
     '''              "impacts_imposes": {
                  sc: [{"variable": i["variable"], "delta_level": _nombre(force_sc(i, sc)),   # U4f'''),
    ("entrée d'injection commune",
     '''        entree["impacts_imposes"] = {
            sc: [{"variable": i["variable"], "delta_level": _nombre(i["force"]),''',
     '''        entree["impacts_imposes"] = {
            sc: [{"variable": i["variable"], "delta_level": _nombre(force_sc(i, sc)),   # U4f'''),
]

HT = [
    ("proposer : consigne forces par scénario",
     '''                       "qu'il apaise prend la polarité -1.\\n\\n")   # U4d3
''',
     '''                       "qu'il apaise prend la polarité -1. Si l'élément frappe certains scénarios plus que "
                       "d'autres, \\"delta_level\\" peut être un dictionnaire par scénario (comme polarite, les 6 "
                       f"scénarios) : {se.WILD_CARD_FORCE[0]} à {se.WILD_CARD_FORCE[1]} dans au moins un scénario, "
                       f"{se.WILD_CARD_FORCE_MIN_SC} au moins dans les autres.\\n\\n")   # U4d3 / U4f
'''),
    ("normalisation : forces par scénario",
     '''        try:
            force = int(round(abs(float(imp.get("delta_level")))))
        except (TypeError, ValueError):
            av.append(f"{var} : force illisible -> 10")
            force = 10
        fmax = SIGNAL_FORCE_MAX if est_signal else FORCE_MAX
        fmin = 1
        if wild:   # U4a
            fmin, fmax = se.WILD_CARD_FORCE
        if not fmin <= force <= fmax:
            av.append(f"{var} : force {force} ramenée entre {fmin} et {fmax}")
            force = min(fmax, max(fmin, force))
''',
     '''        fmax = SIGNAL_FORCE_MAX if est_signal else FORCE_MAX
        fmin = 1
        if wild:   # U4a
            fmin, fmax = se.WILD_CARD_FORCE
        dl = imp.get("delta_level")
        if isinstance(dl, dict):   # U4f : force par scénario
            couverts = se.SCENARIOS if scen == "tous" else list(scen)
            vals = {}
            for s_, v_ in dl.items():
                try:
                    if s_ in couverts:
                        vals[s_] = int(round(abs(float(v_))))
                except (TypeError, ValueError):
                    pass
            if not vals:
                av.append(f"{var} : forces par scénario illisibles -> 10")
                force = 10
            else:
                plancher = se.WILD_CARD_FORCE_MIN_SC if wild else 1
                for s_ in couverts:
                    if s_ not in vals:
                        vals[s_] = max(vals.values())
                        av.append(f"{var} : force absente pour {s_} -> {vals[s_]}")
                for s_, v_ in list(vals.items()):
                    if not plancher <= v_ <= fmax:
                        vals[s_] = min(fmax, max(plancher, v_))
                        av.append(f"{var} : force {v_} ({s_}) ramenée entre {plancher} et {fmax}")
                if max(vals.values()) < fmin:
                    s_max = max(vals, key=vals.get)
                    av.append(f"{var} : aucune force à {fmin} au moins -> {s_max} porté à {fmin}")
                    vals[s_max] = fmin
                force = vals if len(set(vals.values())) > 1 else next(iter(vals.values()))
        else:
            try:
                force = int(round(abs(float(dl))))
            except (TypeError, ValueError):
                av.append(f"{var} : force illisible -> 10")
                force = 10
            if not fmin <= force <= fmax:
                av.append(f"{var} : force {force} ramenée entre {fmin} et {fmax}")
                force = min(fmax, max(fmin, force))
'''),
]

FICHIERS = [(GEN / "simuler_et_si.py", SE), (GEN / "hypothese_depuis_texte.py", HT)]


def main():
    a = argparse.ArgumentParser(description="U4f : force par scénario.")
    a.add_argument("--apply", action="store_true")
    x = a.parse_args()
    if not GEN.is_dir():
        sys.exit("✗ lancer depuis la racine du vault (dossier generator/ introuvable)")
    nouveaux, erreurs = {}, []
    for chemin, remp in FICHIERS:
        if not chemin.exists():
            erreurs.append(f"{chemin.name} introuvable")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if f"# {TAG}" in texte:
            erreurs.append(f"{chemin.name} : {TAG} déjà appliqué")
            continue
        for libelle, avant, apres in remp:
            n = texte.count(avant)
            if n != 1:
                erreurs.append(f"{chemin.name} [{libelle}] : passage trouvé {n} fois (attendu 1) — U4a/U4c/U4d3 appliqués ?")
                continue
            texte = texte.replace(avant, apres)
        nouveaux[chemin] = texte
    if erreurs:
        sys.exit("✗ Rien n'est écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
    for chemin, neuf in nouveaux.items():
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(neuf)
        try:
            py_compile.compile(f.name, doraise=True)
        except py_compile.PyCompileError as e:
            sys.exit(f"✗ {chemin.name} : syntaxe invalide après patch, rien n'est écrit\n{e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    for chemin, remp in FICHIERS:
        print(f"generator/{chemin.name} : {len(remp)} modification(s)")
        for libelle, _, _ in remp:
            print(f"  · {libelle}")
    if not x.apply:
        print("\nDRY-RUN : syntaxe vérifiée sur copie, rien n'est écrit. Relancer avec --apply.")
        return
    faits = []
    try:
        for chemin, neuf in nouveaux.items():
            shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_u4f"))
            chemin.write_text(neuf, encoding="utf-8")
            faits.append(chemin)
            py_compile.compile(str(chemin), doraise=True)
    except Exception as e:  # noqa: BLE001
        for chemin in faits:
            shutil.copy2(chemin.with_name(chemin.name + ".bak_u4f"), chemin)
        sys.exit(f"✗ échec ({type(e).__name__}: {e}) : fichiers restaurés depuis .bak_u4f")
    print("\n✓ U4f appliqué (sauvegardes .bak_u4f). Pas de relance de Flask.")


if __name__ == "__main__":
    main()
