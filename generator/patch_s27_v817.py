#!/usr/bin/env python3
"""
patch_s27_v817.py — Ourrassol 2098 (S27, point 3 « décider », 12 octobre 2026)
==============================================================================

simuler_et_si.py v8.16.2 -> v8.17, branché sur generator/et_si_dossiers.py
(à copier dans generator/ AVANT ce patch) :

  - chaque simulation enregistre le dossier de l'hypothèse
    (generator/state/et_si_dossiers.json) : date, version, empreinte de
    l'hypothèse, scénarios simulés, passe, rapport, entrée d'injection commune ;
  - --dossiers : statut de chaque hypothèse ;
  - --adopter <id> [--portee …] [--intensite …] [--apercu] : écrit l'entrée de
    la dernière simulation complète dans evenements_custom/queue.yaml
    (sauvegarde .bak_et_si) ; l'injection reste à lancer à part ;
  - --rejeter <id> [--motif "…"] ; --annuler-decision <id> ;
  - --lister (texte et --json) affiche le statut (liste déroulante du GUI).

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v817.py --dry-run && python3 generator/patch_s27_v817.py
Sauvegarde .bak_v817 ; refuse un second passage.
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent

REMPLACEMENTS = [
    ('VERSION = "v8.16.2"', 'VERSION = "v8.17"', 1),

    # Usage
    ('    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --consequences-ia --passe-exhaustive --report\n"""',
     '    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --consequences-ia --passe-exhaustive --report\n'
     '\n'
     'DÉCIDER (v8.17, et_si_dossiers.py)\n'
     '    python3 generator/simuler_et_si.py --dossiers\n'
     '    python3 generator/simuler_et_si.py --adopter invasion_bresil_2029 --portee regionale --intensite forte --apercu\n'
     '    python3 generator/simuler_et_si.py --rejeter invasion_bresil_2029 --motif "trop invraisemblable"\n'
     '    python3 generator/simuler_et_si.py --annuler-decision invasion_bresil_2029\n'
     '"""', 1),

    # L'entrée commune est récupérable
    ('def _rendre_injection_commune(hyp, application):\n'
     '    """Entrée de queue commune aux scénarios (mode choc seulement)."""\n',
     'def _rendre_injection_commune(hyp, application, out=None):\n'
     '    """Entrée de queue commune aux scénarios (mode choc seulement).\n'
     '    V8.17 : `out` (dict) reçoit l\'entrée sous la clé « entree »."""\n', 1),
    ('    return ["## Liste d\'application — injection commune", "",\n',
     '    if out is not None:\n'
     '        out["entree"] = entree\n'
     '    return ["## Liste d\'application — injection commune", "",\n', 1),

    # Arguments
    ('                    help="onglet du GUI (nouvelle = panneau d\'écriture, rien à lancer)")\n'
     '    args = ap.parse_args()\n',
     '                    help="onglet du GUI (nouvelle = panneau d\'écriture, rien à lancer)")\n'
     '    # V8.17 : étape « décider » (et_si_dossiers.py).\n'
     '    ap.add_argument("--dossiers", action="store_true", help="statut de chaque hypothèse")\n'
     '    ap.add_argument("--adopter", metavar="ID",\n'
     '                    help="écrit l\'entrée de la dernière simulation complète dans evenements_custom/queue.yaml")\n'
     '    ap.add_argument("--portee", help="avec --adopter : locale | regionale | continentale | globale")\n'
     '    ap.add_argument("--intensite", help="avec --adopter : faible | modérée | forte | majeure")\n'
     '    ap.add_argument("--apercu", action="store_true", help="avec --adopter : montre l\'entrée, n\'écrit rien")\n'
     '    ap.add_argument("--rejeter", metavar="ID", help="marque l\'hypothèse rejetée")\n'
     '    ap.add_argument("--motif", help="avec --rejeter : raison du rejet")\n'
     '    ap.add_argument("--annuler-decision", metavar="ID", help="retire la décision (adoptée ou rejetée)")\n'
     '    args = ap.parse_args()\n', 1),

    # Dispatch + statut dans --lister
    ('    hyps = charger_hypotheses()\n'
     '    if (args.lister or not args.id) and args.json:\n',
     '    hyps = charger_hypotheses()\n'
     '    # V8.17 : étape « décider ».\n'
     '    actions = [a for a in (args.dossiers, args.adopter, args.rejeter, args.annuler_decision) if a]\n'
     '    if len(actions) > 1:\n'
     '        sys.exit("✗ Une seule action à la fois : --dossiers, --adopter, --rejeter ou --annuler-decision.")\n'
     '    if actions:\n'
     '        _decider(args, hyps)\n'
     '        return\n'
     '    import et_si_dossiers as ed\n'
     '    if (args.lister or not args.id) and args.json:\n', 1),
    ('            liste.append({"id": h.get("id"), "nom": h.get("nom") or h.get("id"),\n'
     '                          "date": h.get("date"), "erreurs": err})\n',
     '            st = ed.statut(h.get("id"))\n'
     '            nom = h.get("nom") or h.get("id")\n'
     '            liste.append({"id": h.get("id"), "nom": nom if st == "non simulé" else f"{nom} · {st}",\n'
     '                          "date": h.get("date"), "erreurs": err, "statut": st})\n', 1),
    ('            print(f"  - {h.get(\'id\', \'?\')} : {h.get(\'nom\', \'\')} ({h.get(\'date\', \'?\')})")\n',
     '            print(f"  - {h.get(\'id\', \'?\')} : {h.get(\'nom\', \'\')} ({h.get(\'date\', \'?\')}) · "\n'
     '                  f"{ed.statut(h.get(\'id\'))}")\n', 1),

    # Hypothèse brute (empreinte), avant normalisation
    ('    hyp, erreurs, avert = verifier_hypothese(choix[0], VALID_VARS, dyn)\n',
     '    import copy\n'
     '    brut = copy.deepcopy(choix[0])   # V8.17 : empreinte du bloc tel qu\'écrit\n'
     '    hyp, erreurs, avert = verifier_hypothese(choix[0], VALID_VARS, dyn)\n', 1),

    # Enregistrement de la simulation
    ('    application = construire_application(hyp, resultats, consequences, geo, portee, passe)\n',
     '    application = construire_application(hyp, resultats, consequences, geo, portee, passe)\n'
     '    # V8.17 : dossier de l\'hypothèse (dernière simulation, entrée d\'injection commune).\n'
     '    inj = {}\n'
     '    _rendre_injection_commune(hyp, application, inj)\n'
     '    try:\n'
     '        ed.enregistrer_simulation(brut, hyp, portee, VERSION, inj.get("entree"), bool(passe),\n'
     '                                  f"documentation/need_action/et_si_{hyp[\'id\']}.md" if args.report else None)\n'
     '    except Exception as e:  # le dossier ne doit jamais empêcher le rapport\n'
     '        avert.append(f"dossier de l\'hypothèse non mis à jour : {type(e).__name__}: {e}")\n', 1),

    # Fonction _decider
    ('def main():\n'
     '    ap = argparse.ArgumentParser(description="Simulateur « et si ? » (lecture seule).")\n',
     'def _decider(args, hyps):\n'
     '    """V8.17 : --dossiers, --adopter, --rejeter, --annuler-decision."""\n'
     '    import et_si_dossiers as ed\n'
     '    if args.dossiers:\n'
     '        print(f"Dossiers des hypothèses ({ed.DOSSIERS_PATH.relative_to(VAULT_ROOT)}) :")\n'
     '        for ligne in ed.tableau(hyps):\n'
     '            print(ligne)\n'
     '        return\n'
     '    hid = args.adopter or args.rejeter or args.annuler_decision\n'
     '    brut = next((h for h in hyps if h.get("id") == hid), None)\n'
     '    try:\n'
     '        if args.adopter:\n'
     '            if brut is None:\n'
     '                sys.exit(f"✗ Hypothèse {hid!r} absente de {HYPOTHESES_PATH.name}.")\n'
     '            entree = ed.adopter(brut, hid, args.portee, args.intensite, apercu=args.apercu)\n'
     '            if args.apercu:\n'
     '                print(f"Aperçu de l\'entrée adoptée pour {hid} (rien écrit) :\\n")\n'
     '                print(_yaml_bloc([entree]))\n'
     '                print("\\nRelancer sans --apercu pour l\'écrire dans evenements_custom/queue.yaml.")\n'
     '            else:\n'
     '                print(f"✓ {hid} adoptée : entrée ajoutée à evenements_custom/queue.yaml "\n'
     '                      f"(sauvegarde queue.yaml.bak_et_si).\\n"\n'
     '                      f"  Injection à lancer à part : python3 generator/inject_custom_events.py --mode custom")\n'
     '        elif args.rejeter:\n'
     '            ed.rejeter(hid, args.motif)\n'
     '            print(f"✓ {hid} rejetée" + (f" ({args.motif})" if args.motif else "") + ".")\n'
     '        else:\n'
     '            ancien, avert = ed.annuler_decision(hid)\n'
     '            print(f"✓ Décision retirée ({ancien}) : {hid} revient à « {ed.statut(hid)} ».")\n'
     '            for a in avert:\n'
     '                print(f"  ⚠ {a}")\n'
     '    except ed.DossierErreur as e:\n'
     '        sys.exit(f"✗ {e}")\n'
     '\n'
     '\n'
     'def main():\n'
     '    ap = argparse.ArgumentParser(description="Simulateur « et si ? » (lecture seule).")\n', 1),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dossier", default=str(DOSSIER))
    args = ap.parse_args()
    d = Path(args.dossier)
    sim = d / "simuler_et_si.py"
    if not (d / "et_si_dossiers.py").exists():
        sys.exit("✗ generator/et_si_dossiers.py absent : le copier d'abord. Rien écrit.")
    texte = sim.read_text(encoding="utf-8")
    if 'VERSION = "v8.17"' in texte:
        sys.exit("✗ Patch déjà appliqué : rien à faire.")
    if 'VERSION = "v8.16.2"' not in texte:
        sys.exit("✗ simuler_et_si.py n'est pas en v8.16.2 : rien écrit.")
    for n, (avant, apres, attendu) in enumerate(REMPLACEMENTS, 1):
        compte = texte.count(avant)
        if compte != attendu:
            sys.exit(f"✗ Ancre n°{n} trouvée {compte} fois ({attendu} attendue) : rien écrit.\n"
                     f"  Début de l'ancre : {avant[:80]!r}")
        texte = texte.replace(avant, apres)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(texte)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ simuler_et_si.py patché ne compile pas, rien écrit : {e}")
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass
    if args.dry_run:
        print(f"✓ {len(REMPLACEMENTS)} remplacements possibles, compilation OK (dry-run, rien écrit).")
        return
    shutil.copy2(sim, sim.with_name(sim.name + ".bak_v817"))
    sim.write_text(texte, encoding="utf-8")
    print(f"✓ simuler_et_si.py passé en v8.17 ({len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_v817.")


if __name__ == "__main__":
    main()
