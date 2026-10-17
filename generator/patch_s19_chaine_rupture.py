#!/usr/bin/env python3
"""
patch_s19_chaine_rupture.py -- S19, partie 2 (17 octobre 2026)
================================================================
Branche la chaîne « et si ? » sur le mode rupture (le moteur le sait depuis la
partie 1, patch_s19_moteur_rupture.py, prérequis vérifié) :

  generator/simuler_et_si.py        (v8.20) en mode rupture, l'entrée de queue
        impose aussi les forces (impacts_imposes) et ajoute mode_impose: rupture ;
        les étapes « Élément » ne demandent plus de changer la référence à la main
        ni de vider le bloc d'impacts : l'injection suffit.
  generator/inject_custom_events.py lit mode_impose (choc | rupture), le dit à
        l'IA, et écrit `mode: rupture` dans chaque fiche event_instances.
  generator/appliquer_et_si.py      la phase 4 accepte le mode rupture, après
        avoir vérifié que les fiches injectées portent bien `mode: rupture`.

Une hypothèse en mode choc (Mourmansk, etc.) n'est pas touchée : sans
mode_impose dans l'entrée de queue, l'injection écrit les mêmes fiches qu'avant.

Tout ou rien, sauvegarde .bak_s19b, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s19_chaine_rupture.py            (aperçu)
    python3 generator/patch_s19_chaine_rupture.py --apply
"""
import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_S19_CHAINE"
GEN = Path.cwd() / "generator"
R = {}

# ── simuler_et_si.py ────────────────────────────────────────────────────
R["simuler_et_si.py"] = [
    ('VERSION = "v8.19"', 'VERSION = "v8.20"'),
    (
        '''    if hyp.get("mode") == "rupture":
        _etape(E, "Élément", "Mode rupture : décision S19 à prendre avant toute écriture",
               motif="l'injection réelle ne connaît que le mode choc ; appliquer la rupture = changer la référence")
        for e in (res or {}).get("effets") or []:
            if abs(e.get("reference_apres", e["reference"]) - e["reference"]) >= 0.1:
                # V8.13 : une référence portée au plafond ne laisse plus de marge.
                plafond = e["reference_apres"] >= 99.5
                _etape(E, "Élément", ("⚠ " if plafond else "") + f"{e['variable']} : référence "
                       f"{_virgule(e['reference'], False)} → {_virgule(e['reference_apres'], False)}",
                       f"à la main : variables/{e['variable']}.md, states.{sc}.level, "
                       f"puis python3 generator/synchroniser_scenarios.py",
                       "seulement si la décision S19 est oui"
                       + (" ; au plafond : plus aucune marge pour une autre crise sur cette variable" if plafond else ""))
        # V8.13 : la rupture déplace les niveaux, mais l'événement doit exister pour le récit
        # (registre, articles, journaux) ; sans impact chiffré, sinon le choc compterait deux fois.
        _etape(E, "Élément", f"Créer l'événement `{hyp['id']}` pour le récit (entrée commune en fin de rapport)",
               "python3 generator/inject_custom_events.py --mode custom",
               f"puis vider le bloc impact_sur_variables de event_instances/{hyp['id']}_{sc}.md : "
               "la rupture passe déjà par la référence, le choc compterait deux fois")
        _etape(E, "Élément", "Nouvelle référence : vérifier la lisibilité du moteur",
               "python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05", "S19")''',
        '''    if hyp.get("mode") == "rupture":
        # PATCH_S19_CHAINE (v8.20) : la rupture passe par l'injection. Les fiches portent
        # `mode: rupture` et le moteur déplace lui-même la référence : rien à changer à la main.
        _etape(E, "Élément", f"Injecter l'événement `{hyp['id']}` en mode rupture (entrée commune en fin de rapport)",
               "python3 generator/inject_custom_events.py --mode custom",
               "une seule injection pour tous les scénarios ; mode_impose: rupture écrit `mode: rupture` dans chaque fiche")
        for e in (res or {}).get("effets") or []:
            if abs(e.get("reference_apres", e["reference"]) - e["reference"]) >= 0.1:
                # V8.13 : une référence portée au plafond ne laisse plus de marge.
                plafond = e["reference_apres"] >= 99.5
                _etape(E, "Élément", ("⚠ " if plafond else "") + f"{e['variable']} : référence "
                       f"{_virgule(e['reference'], False)} → {_virgule(e['reference_apres'], False)}",
                       "aucune action : déplacée par le moteur dès l'injection",
                       "au plafond : plus aucune marge pour une autre crise sur cette variable" if plafond else None)
        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{i['force']:g}"
                           for i in hyp["impacts"] if sc in i["polarites"])
        _etape(E, "Élément", f"Vérifier que la fiche porte `mode: rupture` et les forces simulées ({cibles})",
               f"event_instances/{hyp['id']}_{sc}.md ; "
               f"python3 generator/trace_injection.py --slug {hyp['id']} --type evenement --scenario {sc}",
               "le Tracer doit finir chaque ligne « Déclaré » par « rupture »")
        _etape(E, "Élément", "Nouvelle référence : vérifier la lisibilité du moteur",
               "python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05", "S19")''',
    ),
    (
        '''    if not rupture:
        scen = list(hyp["scenarios"])   # V8.15 : polarités connues pour tous les scénarios''',
        '''    scen = list(hyp["scenarios"])   # V8.15 : polarités connues pour tous les scénarios (S19 : rupture comprise)''',
    ),
    (
        '''    trop_fort = []
    if not rupture:
        entree["impacts_imposes"] = {''',
        '''    trop_fort = []
    if rupture:
        entree["mode_impose"] = "rupture"   # PATCH_S19_CHAINE : écrit `mode: rupture` dans les fiches
    if True:   # S19 : forces imposées aussi en mode rupture
        entree["impacts_imposes"] = {''',
    ),
    (
        '''             if partiel and not rupture else "")
            + ("⚠ Simulation limitée à " + ", ".join(scen) + " : ajouter à `scenarios` les autres scénarios "
               "de l'hypothèse (" + ", ".join(partiel) + ") avant d'injecter.\\n\\n" if partiel and rupture else "")''',
        '''             if partiel else "")''',
    ),
    (
        '''            + ("Mode rupture : l'événement n'est injecté que pour le récit ; vider ensuite le bloc "
               "impact_sur_variables de chaque fiche (étape « Élément »).\\n\\n" if hyp.get("mode") == "rupture" else "")''',
        '''            + ("Mode rupture : `mode_impose: rupture` fait écrire `mode: rupture` dans chaque fiche ; le "
               "moteur déplace alors durablement la référence du scénario au lieu d'amortir un choc.\\n\\n"
               if hyp.get("mode") == "rupture" else "")''',
    ),
    (
        '''               "recalcule pas, elle rédige seulement le récit." if not rupture
               else "Seule la date est imposée (`date_imposee`)."), "",''',
        '''               "recalcule pas, elle rédige seulement le récit."), "",''',
    ),
]

# ── inject_custom_events.py ─────────────────────────────────────────────
R["inject_custom_events.py"] = [
    (
        '''    via = idea.get("via_matrice_impose")
    if brut is None and date is None and via is None:
        return None, []''',
        '''    via = idea.get("via_matrice_impose")
    mode = idea.get("mode_impose")   # PATCH_S19_CHAINE : choc | rupture
    if brut is None and date is None and via is None and mode is None:
        return None, []''',
    ),
    (
        '''    if via is not None and not isinstance(via, bool):
        erreurs.append("via_matrice_impose doit valoir true ou false")
    if erreurs:
        return None, erreurs
    return {"impacts": impacts, "date": date, "via_matrice": via}, []''',
        '''    if via is not None and not isinstance(via, bool):
        erreurs.append("via_matrice_impose doit valoir true ou false")
    if mode is not None:
        mode = str(mode).strip().lower()
        if mode not in ("choc", "rupture"):
            erreurs.append(f"mode_impose {idea.get('mode_impose')!r} inconnu (choc | rupture)")
        elif mode == "rupture" and not impacts:
            erreurs.append("mode_impose: rupture sans impacts_imposes (la rupture a besoin de ses forces)")
    if erreurs:
        return None, erreurs
    return {"impacts": impacts, "date": date, "via_matrice": via, "mode": mode}, []''',
    ),
    (
        '''    if imp["via_matrice"] is not None:
        instance_data["propagation_via_matrice"] = imp["via_matrice"]
    if instance_data.get("impossible_dans_scenario"):''',
        '''    if imp["via_matrice"] is not None:
        instance_data["propagation_via_matrice"] = imp["via_matrice"]
    if imp.get("mode"):
        instance_data["mode"] = imp["mode"]   # PATCH_S19_CHAINE, écrit par write_instance_file()
    if instance_data.get("impossible_dans_scenario"):''',
    ),
    (
        '''    lignes.append("Écris la réalisation, la description et les conséquences pour qu'elles "
                  "correspondent à ces valeurs (ampleur, sens et date).")''',
        '''    if imp.get("mode") == "rupture":   # PATCH_S19_CHAINE
        lignes.append("- Nature : RUPTURE DURABLE -- l'événement change pour de bon l'équilibre du monde ; "
                      "ses effets ne s'estompent pas avec le temps (ce n'est pas un choc passager)")
    lignes.append("Écris la réalisation, la description et les conséquences pour qu'elles "
                  "correspondent à ces valeurs (ampleur, sens et date).")''',
    ),
    (
        '''persistance: {persistance}
acteurs_impliques:{acteurs_yaml}''',
        '''persistance: {persistance}{mode_ligne}
acteurs_impliques:{acteurs_yaml}''',
    ),
    (
        '''        persistance=idea.get("persistance") or dyn.PERSISTANCE_DEFAUT,
        acteurs_yaml=acteurs_yaml,''',
        '''        persistance=idea.get("persistance") or dyn.PERSISTANCE_DEFAUT,
        # PATCH_S19_CHAINE : `mode: rupture` (lu par loader.py) seulement si imposé.
        mode_ligne="\\nmode: rupture" if instance_data.get("mode") == "rupture" else "",
        acteurs_yaml=acteurs_yaml,''',
    ),
]

# ── appliquer_et_si.py ──────────────────────────────────────────────────
R["appliquer_et_si.py"] = [(
    '''    if data.get("mode") == "rupture":
        sys.exit("✗ mode rupture : décision S19 à prendre avant toute application.")''',
    '''    if data.get("mode") == "rupture":
        # PATCH_S19_CHAINE : la rupture est jouée par le moteur si les fiches portent `mode: rupture`.
        manque = []
        for sc in data["scenarios"]:
            p = VAULT / "event_instances" / f"{a.id}_{sc}.md"
            d = decoupe(p.read_text(encoding="utf-8")) if p.exists() else None
            fm = lire_fm(d[1]) if d else None
            if not fm or str(fm.get("mode") or "").strip().lower() != "rupture":
                manque.append(f"event_instances/{p.name}" + ("" if p.exists() else " (absente)"))
        if manque:
            sys.exit("✗ mode rupture, mais ces fiches ne portent pas `mode: rupture` : " + ", ".join(manque)
                     + ". Le moteur les jouerait comme un choc : ajouter la ligne `mode: rupture` "
                       "(sous `persistance:`) avant d'appliquer.")''',
)]

PREREQUIS = {"simuler_et_si.py": ["PATCH_S19_RUPTURE"]}


def main():
    apply = "--apply" in sys.argv
    if not GEN.is_dir():
        sys.exit("✗ dossier generator/ introuvable : lancer depuis la racine du coffre.")
    if "PATCH_S19_RUPTURE" not in (GEN / "dynamique.py").read_text(encoding="utf-8"):
        sys.exit("✗ partie 1 absente : appliquer d'abord patch_s19_moteur_rupture.py.")
    nouveaux, erreurs = {}, []
    for nom, reps in R.items():
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
                erreurs.append(f"{nom} : « {p} » absent (partie 1 non appliquée ?)")
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
    for nom in R:
        print(f"  ✓ {nom} : {len(R[nom])} remplacement(s) prêt(s)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    for nom, texte in nouveaux.items():
        chemin = GEN / nom
        shutil.copy2(chemin, chemin.with_name(nom + ".bak_s19b"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Patch S19 (partie 2) appliqué. Sauvegardes : generator/*.bak_s19b")


if __name__ == "__main__":
    main()
