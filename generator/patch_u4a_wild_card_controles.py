#!/usr/bin/env python3
"""
patch_u4a_wild_card_controles.py — Ourrassol 2098 (U4a, 15 novembre 2026)
=========================================================================

Wild cards, premier morceau : le champ `wild_card: true` et les contrôles
mécaniques (sans IA), décidés avec David le 15 novembre :

  - une wild card est un ÉVÉNEMENT en mode RUPTURE (jamais un signal) ;
  - date entre 2030 et 2090 ;
  - 3 à 6 impacts, chacun de force 25 à 35 (au lieu de 1 à 25) ;
  - 3 wild cards au plus par scénario, espacées d'au moins 10 ans dans un même
    scénario (une wild card commune à plusieurs scénarios compte dans chacun ;
    les hypothèses rejetées ne comptent pas).

Fichiers modifiés :
  generator/simuler_et_si.py           constantes, verifier_hypothese(),
                                       controle_wild_cards(), refus de simuler,
                                       liste du GUI (champ wild_card), rapport (⚡)
  generator/hypothese_depuis_texte.py  Proposer / Vérifier / Ajouter : mêmes
                                       contrôles ; option --wild-card de --proposer ;
                                       bug latent d'annee_debut retiré

Pas encore fait (patchs suivants) : moteur (U4b), étape ① (U4c), bouton ⚡ et
case à cocher (U4d), étape ⑤ et badge (U4e). L'injection d'une wild card n'est
pas encore possible : inject_custom_events.py refuse une force au-dessus de 25.

USAGE (depuis la racine du vault)
    python3 generator/patch_u4a_wild_card_controles.py            # dry-run
    python3 generator/patch_u4a_wild_card_controles.py --apply
Sauvegardes : <fichier>.bak_u4a ; contrôle de syntaxe après écriture, retour
arrière automatique en cas d'échec.
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

VAULT = Path.cwd()
GEN = VAULT / "generator"
TAG = "U4a"

# ---------------------------------------------------------------------------
# simuler_et_si.py
# ---------------------------------------------------------------------------

SE = [
    ("constantes",
     '''DELTA_MAX_SIGNAL = 10      # plafond d'un signal (inject_custom_signals.py) -- U2b
''',
     '''DELTA_MAX_SIGNAL = 10      # plafond d'un signal (inject_custom_signals.py) -- U2b
# U4a (15 nov 2026) : wild card = événement en mode rupture marqué `wild_card: true`
WILD_CARD_QUOTA = 3            # wild cards au plus par scénario
WILD_CARD_ECART = 10           # années au moins entre deux wild cards d'un même scénario
WILD_CARD_DATES = (2030, 2090)
WILD_CARD_FORCE = (25, 35)
WILD_CARD_IMPACTS = (3, 6)
'''),
    ("est_wild_card",
     '''def verifier_hypothese(h, valid_vars, dyn):
    """Retourne (hypothèse normalisée, erreurs, avertissements)."""
''',
     '''def est_wild_card(h):
    """U4a : vrai si le bloc porte `wild_card: true` (oui / yes / 1 acceptés)."""
    v = (h or {}).get("wild_card")
    return v is True or str(v).strip().lower() in ("true", "oui", "yes", "1")


def _scenarios_de(h):
    """U4a : scénarios couverts par un bloc brut (« tous » = les 6)."""
    scen = (h or {}).get("scenarios") or "tous"
    if isinstance(scen, str):
        return set(SCENARIOS) if scen.strip() in ("tous", "all") else {scen.strip()}
    return {s for s in scen if s in SCENARIOS} if isinstance(scen, list) else set(SCENARIOS)


def controle_wild_cards(h, hyps=None):
    """U4a : quota (WILD_CARD_QUOTA par scénario) et espacement (WILD_CARD_ECART ans)
    d'une wild card, contre les autres wild cards de hypotheses.yaml (rejetées exclues).
    Retourne une liste d'erreurs (vide si `h` n'est pas une wild card)."""
    if not est_wild_card(h):
        return []
    try:
        date = int(float(h.get("date")))
    except (TypeError, ValueError):
        return []   # date illisible : déjà signalée par verifier_hypothese()
    hyps = charger_hypotheses() if hyps is None else hyps
    try:
        import et_si_dossiers as _ed
    except Exception:  # noqa: BLE001 -- sans dossiers, aucune hypothèse n'est tenue pour rejetée
        _ed = None

    def rejetee(i):
        try:
            return _ed is not None and str(_ed.statut(i)).startswith("rejet")
        except Exception:  # noqa: BLE001
            return False
    autres = [x for x in hyps if isinstance(x, dict) and est_wild_card(x)
              and x.get("id") != h.get("id") and not rejetee(x.get("id"))]
    erreurs = []
    for sc in [s for s in SCENARIOS if s in _scenarios_de(h)]:
        ici = [x for x in autres if sc in _scenarios_de(x)]
        if len(ici) >= WILD_CARD_QUOTA:
            erreurs.append(f"wild card : {sc} en a déjà {len(ici)} ("
                           + ", ".join(str(x.get("id")) for x in ici)
                           + f") ; {WILD_CARD_QUOTA} au plus par scénario")
        for x in ici:
            try:
                dx = int(float(x.get("date")))
            except (TypeError, ValueError):
                continue
            if abs(dx - date) < WILD_CARD_ECART:
                erreurs.append(f"wild card : {sc} a déjà la wild card {x.get('id')!r} en {dx}, "
                               f"à moins de {WILD_CARD_ECART} ans de {date}")
    return erreurs


def verifier_hypothese(h, valid_vars, dyn):
    """Retourne (hypothèse normalisée, erreurs, avertissements)."""
'''),
    ("verifier : wild card",
     '''                erreurs.append(f"date {date:g} : un signal commence une année entière entre {plancher} et 2097")

    impacts = []
''',
     '''                erreurs.append(f"date {date:g} : un signal commence une année entière entre {plancher} et 2097")
    wild = est_wild_card(h)   # U4a
    if wild:
        if est_signal:
            erreurs.append("une wild card est un événement, jamais un signal (retirer `wild_card` ou `type: signal`)")
        if str(h.get("mode") or "choc").strip().lower() != "rupture":
            erreurs.append("une wild card est en mode rupture (`mode: rupture`) : elle change le monde pour de bon")
        if date is not None and not WILD_CARD_DATES[0] <= int(date) <= WILD_CARD_DATES[1]:
            erreurs.append(f"date {date:g} : une wild card survient entre {WILD_CARD_DATES[0]} et "
                           f"{WILD_CARD_DATES[1]}")

    impacts = []
'''),
    ("verifier : force",
     '''        if est_signal and force > DELTA_MAX_SIGNAL:
''',
     '''        if wild and not est_signal:   # U4a
            if not WILD_CARD_FORCE[0] <= force <= WILD_CARD_FORCE[1]:
                erreurs.append(f"impact {var} : delta_level {force:g} hors de la plage d'une wild card "
                               f"({WILD_CARD_FORCE[0]} à {WILD_CARD_FORCE[1]})")
        elif est_signal and force > DELTA_MAX_SIGNAL:
'''),
    ("verifier : nombre d'impacts",
     '''    if not impacts and not erreurs and not h.get("geographie"):
        erreurs.append("aucun impact ni changement de géographie déclaré")
''',
     '''    if not impacts and not erreurs and not h.get("geographie"):
        erreurs.append("aucun impact ni changement de géographie déclaré")
    if wild and not WILD_CARD_IMPACTS[0] <= len(impacts) <= WILD_CARD_IMPACTS[1]:   # U4a
        erreurs.append(f"une wild card touche {WILD_CARD_IMPACTS[0]} à {WILD_CARD_IMPACTS[1]} variables "
                       f"({len(impacts)} impact(s) valide(s))")
'''),
    ("verifier : norm",
     '''        "scenarios": scen, "impacts": impacts, "geographie": geo,
    }
    return norm, erreurs, avert
''',
     '''        "scenarios": scen, "impacts": impacts, "geographie": geo,
        "wild_card": wild,   # U4a
    }
    return norm, erreurs, avert
'''),
    ("rapport",
     '''    for imp in hyp["impacts"]:
        sens = sorted(set(imp["polarites"].values()))
''',
     '''    if hyp.get("wild_card"):   # U4a
        L.append("- **⚡ Wild card** : rupture à faible probabilité et impact majeur ; elle peut contredire "
                 "les fiches et les tendances, jamais les règles de lore")
    for imp in hyp["impacts"]:
        sens = sorted(set(imp["polarites"].values()))
'''),
    ("liste du GUI",
     '''            _, err, _ = verifier_hypothese(dict(h), VALID_VARS, dyn)
            st = ed.statut(h.get("id"))
''',
     '''            _, err, _ = verifier_hypothese(dict(h), VALID_VARS, dyn)
            err = list(err) + controle_wild_cards(h, hyps)   # U4a
            st = ed.statut(h.get("id"))
'''),
    ("liste du GUI : champ",
     '''                          "type": str(h.get("type") or "evenement")})   # U3ao
''',
     '''                          "type": str(h.get("type") or "evenement"),   # U3ao
                          "wild_card": est_wild_card(h)})   # U4a
'''),
    ("refus de simuler",
     '''    hyp, erreurs, avert = verifier_hypothese(choix[0], VALID_VARS, dyn)
    if erreurs:
''',
     '''    hyp, erreurs, avert = verifier_hypothese(choix[0], VALID_VARS, dyn)
    erreurs = list(erreurs) + controle_wild_cards(choix[0], hyps)   # U4a
    if erreurs:
'''),
]

# ---------------------------------------------------------------------------
# hypothese_depuis_texte.py
# ---------------------------------------------------------------------------

HT = [
    ("prompt",
     '''    return f"""{ligne_type}Tu aides l'auteur du monde fictif Ourrassol 2098 (6 scénarios d'avenir, 12 variables
''',
     '''    if imposes and imposes.get("wild_card"):   # U4a
        ligne_type += ("WILD CARD IMPOSÉE PAR L'AUTEUR : rupture à faible probabilité et à impact majeur, "
                       "qu'aucun signal faible n'annonce encore. Type \\"evenement\\", mode \\"rupture\\", "
                       f"date entre {se.WILD_CARD_DATES[0]} et {se.WILD_CARD_DATES[1]}, "
                       f"{se.WILD_CARD_IMPACTS[0]} à {se.WILD_CARD_IMPACTS[1]} impacts, chacun de force "
                       f"{se.WILD_CARD_FORCE[0]} à {se.WILD_CARD_FORCE[1]} (cette règle prime sur le "
                       f"plafond de {FORCE_MAX} donné plus bas).\\n\\n")
    return f"""{ligne_type}Tu aides l'auteur du monde fictif Ourrassol 2098 (6 scénarios d'avenir, 12 variables
'''),
    ("normaliser : signature",
     '''def normaliser_proposition(brut, variables, ids_pris):
''',
     '''def normaliser_proposition(brut, variables, ids_pris, wild=False):
'''),
    ("normaliser : type",
     '''    est_signal = typ == "signal"
    if est_signal:
        h["type"] = "signal"
    if description:
''',
     '''    est_signal = typ == "signal"
    if wild:   # U4a : une wild card est toujours un événement
        if est_signal:
            av.append("une wild card est un événement : type signal -> evenement")
            typ, est_signal = "evenement", False
        h["wild_card"] = True
    if est_signal:
        h["type"] = "signal"
    if description:
'''),
    ("normaliser : date",
     '''    except (TypeError, ValueError):
        av.append(f"date {brut.get('date')!r} illisible -- à renseigner")

    mode = str(brut.get("mode") or "choc").strip().lower()
''',
     '''    except (TypeError, ValueError):
        av.append(f"date {brut.get('date')!r} illisible -- à renseigner")
    if wild and "date" in h:   # U4a
        a0, a1 = se.WILD_CARD_DATES
        if not a0 <= h["date"] <= a1:
            av.append(f"date {h['date']} hors de la fenêtre d'une wild card ({a0}-{a1}) -> ramenée dans la fenêtre")
            h["date"] = min(a1, max(a0, h["date"]))

    mode = str(brut.get("mode") or "choc").strip().lower()
'''),
    ("normaliser : mode",
     '''    h["mode"] = mode
    if mode == "choc":
        pers = dyn.normaliser_persistance(brut.get("persistance")) or dyn.PERSISTANCE_DEFAUT
''',
     '''    if wild and mode != "rupture":   # U4a
        av.append(f"mode {mode} -> rupture (une wild card change le monde pour de bon)")
        mode = "rupture"
    h["mode"] = mode
    if mode == "choc":
        pers = dyn.normaliser_persistance(brut.get("persistance")) or dyn.PERSISTANCE_DEFAUT
'''),
    ("normaliser : force",
     '''        fmax = SIGNAL_FORCE_MAX if est_signal else FORCE_MAX
        if not 1 <= force <= fmax:
            av.append(f"{var} : force {force} ramenée entre 1 et {fmax}")
            force = min(fmax, max(1, force))
''',
     '''        fmax = SIGNAL_FORCE_MAX if est_signal else FORCE_MAX
        fmin = 1
        if wild:   # U4a
            fmin, fmax = se.WILD_CARD_FORCE
        if not fmin <= force <= fmax:
            av.append(f"{var} : force {force} ramenée entre {fmin} et {fmax}")
            force = min(fmax, max(fmin, force))
'''),
    ("normaliser : nombre d'impacts",
     '''    if not impacts:
        av.append("aucun impact valide : à renseigner avant d'ajouter")
    h["impacts"] = impacts
''',
     '''    if wild and len(impacts) > se.WILD_CARD_IMPACTS[1]:   # U4a
        av.append(f"{len(impacts)} impacts, gardé les {se.WILD_CARD_IMPACTS[1]} premiers (wild card)")
        impacts = impacts[:se.WILD_CARD_IMPACTS[1]]
    if not impacts:
        av.append("aucun impact valide : à renseigner avant d'ajouter")
    h["impacts"] = impacts
'''),
    ("bug latent annee_debut",
     '''            av.append(f"annee_debut {annee!r} illisible : retirée")
            h[cle] = v
''',
     '''            av.append(f"annee_debut {annee!r} illisible : retirée")
'''),
    ("proposer",
     '''    variables = valid_vars()
    brut = _llm(construire_prompt(texte, variables, type_force, imposes))
    if not isinstance(brut, dict):
        raise ValueError("réponse de l'IA inexploitable")
    if type_force in ("evenement", "signal"):
        brut["type"] = type_force   # le choix de l'auteur l'emporte sur celui de l'IA
    h, av = normaliser_proposition(brut, variables, ids_existants())
    av += appliquer_imposes(h, imposes, h.get("type") == "signal")   # U3c
    _, erreurs, av2 = se.verifier_hypothese(dict(h), variables, dyn)
''',
     '''    wild = bool((imposes or {}).get("wild_card"))   # U4a
    if wild and type_force == "signal":
        raise ValueError("une wild card est un événement, pas un signal")
    variables = valid_vars()
    brut = _llm(construire_prompt(texte, variables, type_force, imposes))
    if not isinstance(brut, dict):
        raise ValueError("réponse de l'IA inexploitable")
    if type_force in ("evenement", "signal"):
        brut["type"] = type_force   # le choix de l'auteur l'emporte sur celui de l'IA
    h, av = normaliser_proposition(brut, variables, ids_existants(), wild=wild)
    av += appliquer_imposes(h, imposes, h.get("type") == "signal")   # U3c
    _, erreurs, av2 = se.verifier_hypothese(dict(h), variables, dyn)
    erreurs = list(erreurs) + se.controle_wild_cards(h)   # U4a
'''),
    ("verifier_bloc",
     '''    _, err2, avert = se.verifier_hypothese(dict(h), valid_vars(), dyn)
    avert = avert_dup + list(avert)
''',
     '''    _, err2, avert = se.verifier_hypothese(dict(h), valid_vars(), dyn)
    err2 = list(err2) + se.controle_wild_cards(h)   # U4a : quota et espacement
    avert = avert_dup + list(avert)
'''),
    ("option --wild-card",
     '''    ap.add_argument("--citation", default=None,
''',
     '''    ap.add_argument("--wild-card", action="store_true",   # U4a
                    help="avec --proposer : impose une wild card (événement, rupture, 2030-2090, "
                         "3 à 6 impacts de force 25 à 35)")
    ap.add_argument("--citation", default=None,
'''),
    ("option --wild-card : lecture",
     '''            if args.citation:   # U3i
                imposes["citation"] = args.citation
''',
     '''            if args.citation:   # U3i
                imposes["citation"] = args.citation
            if args.wild_card:   # U4a
                imposes["wild_card"] = True
'''),
]

FICHIERS = [(GEN / "simuler_et_si.py", SE), (GEN / "hypothese_depuis_texte.py", HT)]


def appliquer(texte, remplacements, nom):
    erreurs = []
    for libelle, avant, apres in remplacements:
        n = texte.count(avant)
        if n != 1:
            erreurs.append(f"{nom} [{libelle}] : passage trouvé {n} fois (attendu 1)")
            continue
        texte = texte.replace(avant, apres)
    return texte, erreurs


def main():
    a = argparse.ArgumentParser(description="U4a : wild cards, champ et contrôles.")
    a.add_argument("--apply", action="store_true")
    x = a.parse_args()
    if not GEN.is_dir():
        sys.exit("✗ lancer depuis la racine du vault (dossier generator/ introuvable)")
    nouveaux, erreurs = {}, []
    for chemin, remp in FICHIERS:
        if not chemin.exists():
            erreurs.append(f"{chemin.relative_to(VAULT)} introuvable")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if f"# {TAG}" in texte:
            erreurs.append(f"{chemin.name} : {TAG} déjà appliqué")
            continue
        neuf, err = appliquer(texte, remp, chemin.name)
        erreurs += err
        nouveaux[chemin] = neuf
    if erreurs:
        print("✗ Rien n'est écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
        sys.exit(1)
    # Syntaxe contrôlée sur copie avant toute écriture.
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
        print(f"{chemin.relative_to(VAULT)} : {len(remp)} modification(s)")
        for libelle, _, _ in remp:
            print(f"  · {libelle}")
    if not x.apply:
        print("\nDRY-RUN : syntaxe vérifiée sur copie, rien n'est écrit. Relancer avec --apply.")
        return
    faits = []
    try:
        for chemin, neuf in nouveaux.items():
            shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_u4a"))
            chemin.write_text(neuf, encoding="utf-8")
            faits.append(chemin)
            py_compile.compile(str(chemin), doraise=True)
    except Exception as e:  # noqa: BLE001 -- retour arrière complet
        for chemin in faits:
            shutil.copy2(chemin.with_name(chemin.name + ".bak_u4a"), chemin)
        sys.exit(f"✗ échec ({type(e).__name__}: {e}) : fichiers restaurés depuis .bak_u4a")
    print("\n✓ U4a appliqué (sauvegardes .bak_u4a). Aucun redémarrage de Flask nécessaire "
          "(scripts appelés en sous-processus).")


if __name__ == "__main__":
    main()
