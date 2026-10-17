#!/usr/bin/env python3
"""
patch_s19_moteur_rupture.py -- S19, partie 1 (17 octobre 2026)
================================================================
Le moteur réel sait jouer une RUPTURE portée par une fiche d'événement :
une fiche event_instances avec `mode: rupture` déplace durablement la
référence du scénario (dynamique.simuler(ruptures=...)) au lieu d'agir
comme un choc amorti. Sans cette ligne dans aucune fiche, AUCUN niveau
ne change (non-régression stricte).

Fichiers modifiés (sauvegarde .bak_s19 de chacun) :
  generator/loader.py           lit `mode` sur chaque fiche d'événement
  generator/dynamique.py        chocs_depuis_donnees() ignore les ruptures ;
                                nouvelle ruptures_depuis_donnees()
  generator/snapshot.py         passe les ruptures au moteur
  generator/trace_injection.py  avec / sans tient compte des ruptures
  generator/simuler_et_si.py    la base « sans » inclut les ruptures déjà présentes
  generator/banc_calibration.py passe les ruptures au moteur

Tout ou rien : si un repère manque, rien n'est écrit. Refuse un second passage.
Usage, depuis la racine du coffre :
    python3 patch_s19_moteur_rupture.py            (aperçu, n'écrit rien)
    python3 patch_s19_moteur_rupture.py --apply
"""
import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_S19_RUPTURE"
RACINE = Path.cwd()
GEN = RACINE / "generator"

REMPLACEMENTS = {}

# ── loader.py ───────────────────────────────────────────────────────────
REMPLACEMENTS["loader.py"] = [(
    '''            "persistance":  _persistance_verifiee(fm.get("persistance"), fname),
            "custom":       True,''',
    '''            "persistance":  _persistance_verifiee(fm.get("persistance"), fname),
            # PATCH_S19_RUPTURE (17 octobre 2026) : `mode: rupture` = l'événement
            # déplace durablement la référence du scénario (dynamique.
            # ruptures_depuis_donnees) ; absent ou autre valeur = choc amorti.
            "mode":         "rupture" if str(fm.get("mode") or "").strip().lower() == "rupture" else "choc",
            "custom":       True,''',
)]

# ── dynamique.py ────────────────────────────────────────────────────────
REMPLACEMENTS["dynamique.py"] = [
    (
        '''    for ev in events or []:
        for imp in ev.get("impacts") or []:
            chocs.append({"nom": ev.get("name", "?"), "type": "evenement",''',
        '''    for ev in events or []:
        if est_rupture(ev):   # PATCH_S19_RUPTURE : jouée par ruptures_depuis_donnees()
            continue
        for imp in ev.get("impacts") or []:
            chocs.append({"nom": ev.get("name", "?"), "type": "evenement",''',
    ),
    (
        '''    return [c for c in chocs if c["amplitude"]]
''',
        '''    return [c for c in chocs if c["amplitude"]]


# PATCH_S19_RUPTURE (17 octobre 2026) -- événements en mode rupture
# (`mode: rupture` dans la fiche event_instances, lu par loader.py).

def est_rupture(ev):
    return str((ev or {}).get("mode") or "").strip().lower() == "rupture"


def ruptures_depuis_donnees(events):
    """Ruptures au format de simuler(ruptures=...) : une par impact d'un
    événement en mode rupture. Même convention que les chocs (force =
    |delta_level|, sens = polarite), mais ni GAIN_CHOCS ni demi-vie :
    la référence est déplacée pour de bon (voir rampe_rupture()).
    Liste vide si aucun événement n'est en rupture."""
    out = []
    for ev in events or []:
        if not est_rupture(ev):
            continue
        for imp in ev.get("impacts") or []:
            try:
                a = abs(float(imp.get("delta_level") or 0)) * (1 if int(imp.get("polarite") or 1) >= 0 else -1)
            except (TypeError, ValueError):
                a = 0.0
            if not a:
                continue
            out.append({"nom": ev.get("name", "?"), "variable": imp.get("variable", ""),
                        "t0": float(ev.get("date", 2050)), "duree": float(imp.get("duree") or 15),
                        "amplitude": a})
    return out
''',
    ),
]

# ── snapshot.py ─────────────────────────────────────────────────────────
REMPLACEMENTS["snapshot.py"] = [
    (
        '''    chocs = dyn.chocs_depuis_donnees(scenario_slug, instances, events, signals)
    res = dyn.simuler(variables, ref, params, liens, chocs, date_reference, k=k)''',
        '''    chocs = dyn.chocs_depuis_donnees(scenario_slug, instances, events, signals)
    # PATCH_S19_RUPTURE : événements en mode rupture = référence déplacée.
    ruptures = dyn.ruptures_depuis_donnees(events)
    res = dyn.simuler(variables, ref, params, liens, chocs, date_reference, k=k,
                      ruptures=ruptures or None)
    if ruptures:
        print("[snapshot] Ruptures : {} (référence déplacée) -- {}".format(
            len(ruptures), " ; ".join(sorted({r["nom"][:50] for r in ruptures}))))''',
    ),
    (
        '''            ((c["nom"], dyn.forcage(c, date_reference))
             for c in chocs if c["variable"] == v),''',
        '''            [(c["nom"], dyn.forcage(c, date_reference))
             for c in chocs if c["variable"] == v]
            + [(r["nom"], dyn.rampe_rupture(r, date_reference))
               for r in ruptures if r["variable"] == v],''',
    ),
]

# ── trace_injection.py ──────────────────────────────────────────────────
REMPLACEMENTS["trace_injection.py"] = [
    (
        '''            "propagation_via_matrice": (fm.get("propagation") or {}).get("via_matrice"),
            "acteurs_impliques": fm.get("acteurs_impliques") or [],''',
        '''            "propagation_via_matrice": (fm.get("propagation") or {}).get("via_matrice"),
            "mode": fm.get("mode"),   # PATCH_S19_RUPTURE
            "acteurs_impliques": fm.get("acteurs_impliques") or [],''',
    ),
    (
        '''            out[i["scenario"]] = [ligne(imp, i.get("propagation_via_matrice"))
                                  for imp in i.get("impact_sur_variables") or [] if isinstance(imp, dict)]''',
        '''            # PATCH_S19_RUPTURE : clé « rupture » seulement pour un événement en rupture.
            rupt = str(i.get("mode") or "").strip().lower() == "rupture"
            out[i["scenario"]] = [dict(ligne(imp, i.get("propagation_via_matrice")), **({"rupture": True} if rupt else {}))
                                  for imp in i.get("impact_sur_variables") or [] if isinstance(imp, dict)]''',
    ),
    (
        '''        chocs_avec = dyn.chocs_depuis_donnees(sc, instances, events, signals)
        chocs_sans = dyn.chocs_depuis_donnees(sc, inst_sans, ev_sans, sig_sans)
        avec = dyn.simuler(variables, ref, params, liens, chocs_avec, date_fin, echantillonner=PAS_CHRONO, k=k)
        sans = dyn.simuler(variables, ref, params, liens, chocs_sans, date_fin, echantillonner=PAS_CHRONO, k=k)

        # Chocs propres à l'élément = ceux qui disparaissent de la liste "sans"
        cles_sans = {(c["nom"], c["variable"], c["t0"]) for c in chocs_sans}
        propres = [c for c in chocs_avec if (c["nom"], c["variable"], c["t0"]) not in cles_sans]''',
        '''        chocs_avec = dyn.chocs_depuis_donnees(sc, instances, events, signals)
        chocs_sans = dyn.chocs_depuis_donnees(sc, inst_sans, ev_sans, sig_sans)
        # PATCH_S19_RUPTURE : ruptures (événements en mode rupture), avec et sans l'élément.
        rup_avec = dyn.ruptures_depuis_donnees(events)
        rup_sans = dyn.ruptures_depuis_donnees(ev_sans)
        avec = dyn.simuler(variables, ref, params, liens, chocs_avec, date_fin, echantillonner=PAS_CHRONO, k=k,
                           ruptures=rup_avec or None)
        sans = dyn.simuler(variables, ref, params, liens, chocs_sans, date_fin, echantillonner=PAS_CHRONO, k=k,
                           ruptures=rup_sans or None)

        # Chocs propres à l'élément = ceux qui disparaissent de la liste "sans"
        cles_sans = {(c["nom"], c["variable"], c["t0"]) for c in chocs_sans}
        propres = [c for c in chocs_avec if (c["nom"], c["variable"], c["t0"]) not in cles_sans]
        cles_rs = {(r["nom"], r["variable"], r["t0"]) for r in rup_sans}
        propres += [r for r in rup_avec if (r["nom"], r["variable"], r["t0"]) not in cles_rs]''',
    ),
    (
        '''                                 f"{', propagé par la matrice' if d['via_matrice'] else ', sans propagation'}")''',
        '''                                 f"{', propagé par la matrice' if d['via_matrice'] else ', sans propagation'}"
                                 + (" — **rupture** : référence du scénario déplacée pour de bon"
                                    if d.get("rupture") else ""))''',
    ),
]

# ── simuler_et_si.py ────────────────────────────────────────────────────
REMPLACEMENTS["simuler_et_si.py"] = [
    (
        '''        sans = dyn.simuler(variables, ref, params, liens, chocs_sans, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k)
        avec = dyn.simuler(variables, ref, params, liens, chocs_sans + propres, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k, ruptures=rupts or None)
        directes = {c["variable"] for c in propres + rupts}
        ref_apres = avec.get("references") or ref''',
        '''        # PATCH_S19_RUPTURE : ruptures déjà présentes dans le monde (fiches en mode rupture).
        rupt_base = dyn.ruptures_depuis_donnees(events)
        sans = dyn.simuler(variables, ref, params, liens, chocs_sans, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k, ruptures=rupt_base or None)
        avec = dyn.simuler(variables, ref, params, liens, chocs_sans + propres, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k, ruptures=(rupt_base + rupts) or None)
        directes = {c["variable"] for c in propres + rupts}
        ref_apres = avec.get("references") or ref
        ref = sans.get("references") or ref   # référence du monde actuel, ruptures existantes comprises''',
    ),
]

# ── banc_calibration.py (fichier non relu : remplacement sur la ligne seule) ──
REMPLACEMENTS["banc_calibration.py"] = [(
    '''res = dyn.simuler(VALID_VARS, niveaux_ref, params, liens, chocs, date_fin, echantillonner=0.5)''',
    '''res = dyn.simuler(VALID_VARS, niveaux_ref, params, liens, chocs, date_fin, echantillonner=0.5,
                      ruptures=dyn.ruptures_depuis_donnees(load_events_for_scenario(scenario)) or None)  # PATCH_S19_RUPTURE''',
)]
PREREQUIS = {"banc_calibration.py": ["load_events_for_scenario"]}


def main():
    apply = "--apply" in sys.argv
    if not GEN.is_dir():
        sys.exit("✗ dossier generator/ introuvable : lancer depuis la racine du coffre.")
    nouveaux, erreurs = {}, []
    for nom, reps in REMPLACEMENTS.items():
        chemin = GEN / nom
        if not chemin.exists():
            erreurs.append(f"{nom} : introuvable")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if MARQUEUR in texte:
            erreurs.append(f"{nom} : déjà patché ({MARQUEUR} présent)")
            continue
        for p in PREREQUIS.get(nom, []):
            if p not in texte:
                erreurs.append(f"{nom} : « {p} » absent du fichier")
        for n, (ancien, neuf) in enumerate(reps, 1):
            nb = texte.count(ancien)
            if nb != 1:
                erreurs.append(f"{nom} : repère n°{n} trouvé {nb} fois (attendu 1)")
                continue
            texte = texte.replace(ancien, neuf)
        try:
            compile(texte, str(chemin), "exec")
        except SyntaxError as e:
            erreurs.append(f"{nom} : erreur de syntaxe après patch ({e})")
        nouveaux[nom] = texte
    if erreurs:
        print("✗ Rien n'a été écrit :")
        for e in erreurs:
            print("  -", e)
        sys.exit(1)
    for nom in REMPLACEMENTS:
        print(f"  ✓ {nom} : {len(REMPLACEMENTS[nom])} remplacement(s) prêt(s)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    for nom, texte in nouveaux.items():
        chemin = GEN / nom
        shutil.copy2(chemin, chemin.with_name(nom + ".bak_s19"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Patch S19 (partie 1) appliqué. Sauvegardes : generator/*.bak_s19")


if __name__ == "__main__":
    main()
