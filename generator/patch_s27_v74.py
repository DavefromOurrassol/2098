#!/usr/bin/env python3
"""
patch_s27_v74.py — Ourrassol 2098 (S27, 10 octobre 2026)
=========================================================

Simulateur « et si ? » v7.3 -> v7.4 : mode « rupture ».
Constat des tests peste / extrême droite : le moteur traite tout élément comme
une perturbation passagère (GAIN_CHOCS 0,25, demi-vie, plafond ±15 autour de
la référence) ; une peste à 25 % de mortalité ne pèse que ~+3 points.

`mode: rupture` (au niveau de l'hypothèse) : l'élément déplace l'ÉQUILIBRE du
scénario. Pour chaque variable touchée, la référence glisse de force × polarité
sur `duree`, puis y reste (pas de GAIN_CHOCS, pas de demi-vie). Le glissement
est saturé en douceur vers la borne 0 / 100 (jamais au-delà). Le ressort ramène
vers la nouvelle référence, le plafond ±15 des autres chocs s'applique autour
d'elle, et les voisines suivent par la matrice (elles voient le déplacement
total de la variable source).

1. dynamique.py : fonctions `rampe_rupture` et `reference_deplacee`, paramètre
   optionnel `ruptures=None` de simuler(). Sans ce paramètre : calcul identique
   (snapshot.py, trace_injection.py inchangés).
2. simuler_et_si.py : champ `mode` (choc | rupture, défaut choc), simulation,
   rapport (référence avant -> après), consigne IA adaptée, cache distinct.
3. hypotheses.yaml : champ documenté ; `mode: rupture` ajouté à
   peste_pulmonaire_2043 (si présente) pour le test.

Fichiers : generator/dynamique.py, generator/simuler_et_si.py,
           et_si/hypotheses.yaml (sauvegardes .bak_v74)

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v74.py            # aperçu (+ contrôle de non-régression)
    python3 generator/patch_s27_v74.py --apply    # écrit
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
DYN = VAULT_ROOT / "generator" / "dynamique.py"
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"
HYPS = VAULT_ROOT / "et_si" / "hypotheses.yaml"

# ---------------------------------------------------------------- dynamique.py
REMPLACEMENTS_DYN = [
    ("fonctions de rupture",
     '''# ─────────────────────────────────────────
# Intégration
# ─────────────────────────────────────────
''',
     '''def rampe_rupture(rupture, t):
    """V7.4 (simulateur « et si ? », mode rupture) : déplacement de la
    référence (points de level) à la date t. Rampe linéaire sur `duree`,
    puis pleine valeur pour toujours. Ni GAIN_CHOCS, ni demi-vie."""
    t0, duree = rupture["t0"], max(float(rupture["duree"]), PAS)
    if t < t0:
        return 0.0
    return rupture["amplitude"] * min(1.0, (t - t0) / duree)


def reference_deplacee(ref, d):
    """Référence + déplacement d, saturé en douceur vers la borne 0 ou 100
    (même forme que niveau_sature, sans le plafond de 15 points)."""
    if d == 0:
        return ref
    marge = (100.0 - ref) if d > 0 else ref
    if marge <= 1e-6:
        return ref
    return ref + marge * math.tanh(d / marge)


# ─────────────────────────────────────────
# Intégration
# ─────────────────────────────────────────
'''),

    ("signature de simuler",
     "def simuler(variables, niveaux_ref, params, liens, chocs, date_fin, echantillonner=None, k=None):",
     "def simuler(variables, niveaux_ref, params, liens, chocs, date_fin, echantillonner=None, k=None,\n"
     "            ruptures=None):"),

    ("docstring : ruptures",
     '''    echantillonner : None, ou pas (années) pour renvoyer une trajectoire
''',
     '''    echantillonner : None, ou pas (années) pour renvoyer une trajectoire
    ruptures     : None, ou [{"variable", "t0", "duree", "amplitude"}] (V7.4,
                   simulateur « et si ? ») : déplacement permanent de la
                   référence. Avec ruptures, le résultat contient aussi
                   "references" {slug: référence déplacée en fin de période}.
'''),

    ("état des ruptures",
     '''    chocs_loc = [c for c in chocs if not c.get("via_matrice") and c["variable"] in x_net]

    def niveau(v):
        return niveau_sature(niveaux_ref[v], x_net[v] + x_loc[v])
''',
     '''    chocs_loc = [c for c in chocs if not c.get("via_matrice") and c["variable"] in x_net]
    ruptures = [r for r in (ruptures or []) if r["variable"] in x_net]
    dep = {v: 0.0 for v in variables}           # déplacement de la référence (ruptures)
    hist_dep = {v: [] for v in variables}

    def maj_dep(t):
        for v in variables:
            dep[v] = 0.0
        for r in ruptures:
            dep[r["variable"]] += rampe_rupture(r, t)

    def niveau(v):
        if ruptures:
            return niveau_sature(reference_deplacee(niveaux_ref[v], dep[v]), x_net[v] + x_loc[v])
        return niveau_sature(niveaux_ref[v], x_net[v] + x_loc[v])
'''),

    ("mise à jour à chaque pas",
     '''        t = ANNEE_DEPART + k * PAS
        if echantillonner and t >= prochain_echantillon - 1e-9:''',
     '''        t = ANNEE_DEPART + k * PAS
        if ruptures:
            maj_dep(t)
        if echantillonner and t >= prochain_echantillon - 1e-9:'''),

    ("historique des déplacements",
     '''        for v in variables:
            hist[v].append(x_net[v])
''',
     '''        for v in variables:
            hist[v].append(x_net[v])
            if ruptures:
                hist_dep[v].append(dep[v])
'''),

    ("couplage : déplacement total de la source",
     '''                if i >= 0:
                    coup += cf * hist[s][i]''',
     '''                if i >= 0:
                    coup += cf * (hist[s][i] + hist_dep[s][i]) if ruptures else cf * hist[s][i]'''),

    ("fin de période",
     '''    t_fin = ANNEE_DEPART + n_pas * PAS
    if echantillonner:
        trajectoire.append((round(t_fin, 3), {v: niveau(v) for v in variables}))
    return {
        "niveaux": {v: round(niveau(v), 1) for v in variables},
        "ecarts": {v: round(x_net[v] + x_loc[v], 2) for v in variables},
        "trajectoire": trajectoire,
        "ecarts_traj": ecarts_traj,
    }''',
     '''    t_fin = ANNEE_DEPART + n_pas * PAS
    if ruptures:
        maj_dep(t_fin)
    if echantillonner:
        trajectoire.append((round(t_fin, 3), {v: niveau(v) for v in variables}))
    res = {
        "niveaux": {v: round(niveau(v), 1) for v in variables},
        "ecarts": {v: round(x_net[v] + x_loc[v], 2) for v in variables},
        "trajectoire": trajectoire,
        "ecarts_traj": ecarts_traj,
    }
    if ruptures:
        res["references"] = {v: round(reference_deplacee(niveaux_ref[v], dep[v]), 1) for v in variables}
    return res'''),
]

# ----------------------------------------------------------- simuler_et_si.py
REMPLACEMENTS_SIMU = [
    ("version", 'VERSION = "v7.3"', 'VERSION = "v7.4"'),

    ("lecture du champ mode",
     '''    norm = {
        "contraintes": contraintes, "carte": carte,''',
     '''    # V7.4 : `mode: rupture` = l'élément déplace durablement l'équilibre du scénario.
    mode = str(h.get("mode") or "choc").strip().lower()
    if mode not in ("choc", "rupture"):
        erreurs.append(f"mode {h.get('mode')!r} inconnu (choc | rupture)")
        mode = "choc"
    if mode == "rupture" and h.get("persistance") is not None:
        avert.append("`persistance` sans objet en mode rupture (le déplacement est permanent) : ignorée")
    norm = {
        "contraintes": contraintes, "carte": carte, "mode": mode,'''),

    ("ruptures de l'hypothèse",
     '''# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
''',
     '''def ruptures_hypothese(hyp, sc):
    """V7.4 : déplacements de référence au format de dynamique.simuler(ruptures=...)."""
    return [{
        "variable": imp["variable"], "t0": hyp["date"], "duree": imp["duree"],
        "amplitude": imp["force"] * imp["polarites"][sc],
    } for imp in hyp["impacts"] if sc in imp["polarites"]]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
'''),

    ("simulation avec ruptures",
     '''        propres = chocs_hypothese(hyp, sc)
        if not propres:
            continue
        sans = dyn.simuler(variables, ref, params, liens, chocs_sans, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k)
        avec = dyn.simuler(variables, ref, params, liens, chocs_sans + propres, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k)
        directes = {c["variable"] for c in propres}
''',
     '''        rupture = hyp.get("mode") == "rupture"
        propres = [] if rupture else chocs_hypothese(hyp, sc)
        rupts = ruptures_hypothese(hyp, sc) if rupture else []
        if not propres and not rupts:
            continue
        sans = dyn.simuler(variables, ref, params, liens, chocs_sans, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k)
        avec = dyn.simuler(variables, ref, params, liens, chocs_sans + propres, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k, ruptures=rupts or None)
        directes = {c["variable"] for c in propres + rupts}
        ref_apres = avec.get("references") or ref
'''),

    ("effets : référence après",
     '''                effets.append({"variable": v, "reference": ref[v], "sans": sans["niveaux"][v],''',
     '''                effets.append({"variable": v, "reference": ref[v], "reference_apres": ref_apres[v],
                               "sans": sans["niveaux"][v],'''),

    ("cache distinct en mode rupture",
     '''    brut = json.dumps({"h": {k: hyp.get(k) for k in ("nom", "description", "date", "impacts", "persistance", "contraintes")
                             if k != "contraintes" or hyp.get(k)},''',
     '''    brut = json.dumps({"h": {k: hyp.get(k) for k in ("nom", "description", "date", "impacts", "persistance",
                                                       "contraintes", "mode")
                             if k not in ("contraintes", "mode") or (hyp.get(k) and hyp.get(k) != "choc")},'''),

    ("consigne IA : avertissement selon le mode",
     '''    bloc_carte = ""
    if not hyp.get("carte", True):''',
     '''    if hyp.get("mode") == "rupture":
        nature = "MODE RUPTURE (déplacement permanent de l'équilibre du scénario)"
        avert_moteur = ("Effet chiffré simulé en fin de période (niveau 100 = crise) — MODE RUPTURE : l'élément\\n"
                        "déplace durablement l'équilibre du scénario, ces chiffres en tiennent compte ; une variable\\n"
                        "déjà proche de 100 ne peut plus monter beaucoup, juge aussi d'après la nature de l'élément :")
    else:
        nature = f"persistance {hyp['persistance']}"
        avert_moteur = ("Effet chiffré simulé en fin de période (niveau 100 = crise) — ATTENTION : le moteur\\n"
                        "amortit fortement les chocs (il les fait revenir vers l'équilibre du scénario) ;\\n"
                        "juge l'ampleur de la reconfiguration d'après la nature de l'élément, pas d'après ces seuls chiffres :")
    bloc_carte = ""
    if not hyp.get("carte", True):'''),

    ("consigne IA : nature de l'élément",
     "{hyp['nom']} — apparition en {hyp['date']:g}, persistance {hyp['persistance']}.",
     "{hyp['nom']} — apparition en {hyp['date']:g}, {nature}."),

    ("consigne IA : texte de l'avertissement",
     '''Effet chiffré simulé en fin de période (niveau 100 = crise) — ATTENTION : le moteur
amortit fortement les chocs (il les fait revenir vers l'équilibre du scénario) ;
juge l'ampleur de la reconfiguration d'après la nature de l'élément, pas d'après ces seuls chiffres :
''',
     '''{avert_moteur}
'''),

    ("rapport : en-tête selon le mode",
     '''    L += [f"- **Apparition** : {hyp['date']:g} · **Persistance** : {hyp['persistance']} · "''',
     '''    pers_txt = ("— (mode **rupture** : l'équilibre du scénario est déplacé pour de bon)"
                if hyp.get("mode") == "rupture" else hyp["persistance"])
    L += [f"- **Apparition** : {hyp['date']:g} · **Persistance** : {pers_txt} · "'''),

    ("rapport : référence avant -> après",
     '''                L.append(f"| {e['variable']} | {_virgule(e['reference'], False)} | {_virgule(e['sans'], False)} | "''',
     '''                ref_txt = _virgule(e['reference'], False)
                if abs(e.get("reference_apres", e["reference"]) - e["reference"]) >= 0.1:
                    ref_txt += f" → {_virgule(e['reference_apres'], False)}"
                L.append(f"| {e['variable']} | {ref_txt} | {_virgule(e['sans'], False)} | "'''),
]

DOC_MODE = '''#   mode         : optionnel, choc | rupture (défaut choc, simulateur v7.4).
#                  choc    = perturbation amortie qui s'efface (persistance), le monde
#                            revient vers l'équilibre du scénario.
#                  rupture = l'élément change le monde pour de bon : la référence de
#                            chaque variable touchée glisse de delta_level × polarite
#                            sur `duree`, puis y reste (persistance sans objet).
#                            Pour une pandémie massive, une IA qui remplace le travail...
'''

REMPLACEMENTS_HYPS = [
    ("en-tête : champ mode (obligatoire)",
     "#   carte        : optionnel, défaut oui.",
     DOC_MODE + "#   carte        : optionnel, défaut oui.", True),
    ("peste_pulmonaire_2043 : mode: rupture",
     "  - id: peste_pulmonaire_2043\n", "  - id: peste_pulmonaire_2043\n    mode: rupture\n", False),
]


def appliquer(nom, texte, remplacements, erreurs):
    print(f"{nom} :")
    for libelle, ancien, nouveau in remplacements:
        n = texte.count(ancien)
        if n != 1:
            erreurs.append(f"{nom} — {libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        texte = texte.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    return texte


def controle_non_regression(ancien_src, nouveau_src, erreurs):
    """Même calcul sans ruptures, au chiffre près, sur un petit système couplé."""
    import types
    mods = []
    for src in (ancien_src, nouveau_src):
        m = types.ModuleType("dyn_test")
        exec(compile(src, "dynamique.py", "exec"), m.__dict__)
        mods.append(m)
    variables = ["a", "b", "c"]
    ref = {"a": 60.0, "b": 92.0, "c": 30.0}
    params = {v: {"omega": 0.4, "zeta": 0.7} for v in variables}
    liens = [("a", "b", 0.8, 1), ("b", "c", -0.5, 0), ("c", "a", 0.6, 2)]
    chocs = [{"nom": "x", "variable": "a", "t0": 2030, "duree": 5, "amplitude": 20, "via_matrice": True},
             {"nom": "y", "variable": "c", "t0": 2050, "duree": 3, "amplitude": -15, "via_matrice": False,
              "persistance": "durable"}]
    r_old = mods[0].simuler(variables, ref, params, liens, chocs, 2098.5, echantillonner=0.5, k=0.05)
    r_new = mods[1].simuler(variables, ref, params, liens, chocs, 2098.5, echantillonner=0.5, k=0.05)
    if r_old != r_new:
        erreurs.append("dynamique.py : le calcul SANS rupture a changé (non-régression en échec)")
    else:
        print("  ✓ non-régression : calcul sans rupture identique au chiffre près")
    r_rup = mods[1].simuler(variables, ref, params, liens, chocs, 2098.5, k=0.05,
                            ruptures=[{"variable": "a", "t0": 2043, "duree": 3, "amplitude": 25}])
    print(f"  ✓ essai rupture : a {r_new['niveaux']['a']} -> {r_rup['niveaux']['a']} "
          f"(référence 60 -> {r_rup['references']['a']}), voisine b {r_new['niveaux']['b']} -> {r_rup['niveaux']['b']}")


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7.3 -> v7.4 (mode rupture).")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon : aperçu)")
    args = ap.parse_args()
    for f in (DYN, SIMU, HYPS):
        if not f.exists():
            sys.exit(f"✗ Fichier introuvable : {f}")
    dyn0 = DYN.read_text(encoding="utf-8")
    simu, hyps = SIMU.read_text(encoding="utf-8"), HYPS.read_text(encoding="utf-8")
    if 'VERSION = "v7.4"' in simu or "def reference_deplacee" in dyn0:
        sys.exit("✗ Patch déjà appliqué (v7.4). Rien à faire.")
    if 'VERSION = "v7.3"' not in simu:
        sys.exit("✗ La v7.3 n'est pas installée : appliquer d'abord patch_s27_v73.py.")
    erreurs = []
    dyn = appliquer("dynamique.py", dyn0, REMPLACEMENTS_DYN, erreurs)
    simu = appliquer("simuler_et_si.py", simu, REMPLACEMENTS_SIMU, erreurs)
    print("hypotheses.yaml :")
    for libelle, ancien, nouveau, obligatoire in REMPLACEMENTS_HYPS:
        n = hyps.count(ancien)
        if n == 1:
            hyps = hyps.replace(ancien, nouveau)
            print(f"  ✓ {libelle}")
        elif obligatoire:
            erreurs.append(f"hypotheses.yaml — {libelle} : texte attendu trouvé {n} fois (1 attendu)")
        else:
            print(f"  – {libelle} : hypothèse introuvable, ignoré (ajouter `mode: rupture` à la main)")
    for f, src in ((DYN, dyn), (SIMU, simu)):
        try:
            compile(src, str(f), "exec")
        except SyntaxError as e:
            erreurs.append(f"{f.name} ne compilerait pas : {e}")
    try:
        import yaml
        yaml.safe_load(hyps)
    except Exception as e:  # noqa: BLE001
        erreurs.append(f"hypotheses.yaml modifié illisible : {e}")
    if not erreurs:
        print("contrôle du moteur :")
        try:
            controle_non_regression(dyn0, dyn, erreurs)
        except Exception as e:  # noqa: BLE001
            erreurs.append(f"contrôle du moteur impossible : {e!r}")
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    for f, contenu in ((DYN, dyn), (SIMU, simu), (HYPS, hyps)):
        shutil.copy(f, f.with_name(f.name + ".bak_v74"))
        f.write_text(contenu, encoding="utf-8")
        print(f"→ écrit : {f.relative_to(VAULT_ROOT)} (sauvegarde {f.name}.bak_v74)")
    print("\nSimulateur passé en v7.4.")


if __name__ == "__main__":
    main()
