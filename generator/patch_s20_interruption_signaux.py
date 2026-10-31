#!/usr/bin/env python3
"""
patch_s20_interruption_signaux.py — S20, 31 oct 2026

inject_custom_signals.py : une interruption (Ctrl-C, arrêt depuis le GUI par
SIGTERM, plantage) ne crée plus de doublons ni de variable à moitié écrite.

Avant :
  - queue.yaml n'était réécrite qu'en fin de run : après une interruption, les
    idées déjà traitées restaient en queue ; au run suivant leur slug était
    suffixé (_2) et le signal injecté une seconde fois ;
  - KeyboardInterrupt n'est pas une Exception : une variable interrompue en
    pleine écriture n'était pas restaurée (garde-fou S22 contourné).

Après :
  1. queue.yaml réécrite après CHAQUE idée (seules les idées non traitées y
     restent) ;
  2. interruption pendant une variable : écriture annulée (instantané S22),
     cette variable et les suivantes passent en échec « interrompu », la fiche
     d'audit des variables déjà injectées est écrite et l'entrée
     `idee_a_remettre_en_queue` est produite (reprise du MÊME signal), puis
     le run s'arrête proprement ;
  3. interruption hors des variables (sélection, fiche) : l'idée reste en
     queue, arrêt (code 130) ;
  4. SIGTERM traité comme Ctrl-C.

Prérequis : patch_s22_exception_signal.py appliqué (c'est le cas depuis le 5 oct).

Usage (depuis la racine du projet) :
  python3 generator/patch_s20_interruption_signaux.py           # aperçu
  python3 generator/patch_s20_interruption_signaux.py --apply   # applique (.bak créé)
  option : --fichier <chemin>  (défaut : generator/inject_custom_signals.py)
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

MARQUE = "S20 (31 oct 2026)"

REMPLACEMENTS = [
    (
        "drapeau d'interruption",
        "    for variable_slug in variables:\n        ecriture = None  # S22 : instantané pris juste avant d'écrire\n",
        "    interrompu = False  # " + MARQUE + " : Ctrl-C / SIGTERM pendant les variables\n"
        "    for variable_slug in variables:\n        ecriture = None  # S22 : instantané pris juste avant d'écrire\n",
    ),
    (
        "interruption pendant une variable",
        '''            results.append({"variable": variable_slug, "status": "needs_review",
                            "issues": [motif], "exception": True,
                            "ecriture_annulee": annulee})
            continue

    erreur_fiche = None  # S22
''',
        '''            results.append({"variable": variable_slug, "status": "needs_review",
                            "issues": [motif], "exception": True,
                            "ecriture_annulee": annulee})
            continue
        except KeyboardInterrupt:
            # ''' + MARQUE + ''' : KeyboardInterrupt n'est pas une Exception,
            # le bloc S22 ne la voyait pas. On annule l'écriture en cours, on
            # marque cette variable et les suivantes « interrompu », et on
            # sort de la boucle : la suite (fiche d'audit des variables déjà
            # injectées, idee_a_remettre_en_queue) se déroule normalement.
            annulee = _restaurer_instantane(ecriture) if ecriture is not None else False
            restantes = variables[variables.index(variable_slug):]
            print(f"  ✗ Interrompu pendant {variable_slug}"
                  + (" -- écriture annulée (fiche et registre restaurés)" if annulee else "")
                  + f" ; non traitées : {restantes}")
            for v in restantes:
                results.append({"variable": v, "status": "needs_review",
                                "issues": ["interrompu"], "interrompu": True,
                                "ecriture_annulee": annulee and v == variable_slug})
            interrompu = True
            break

    erreur_fiche = None  # S22
''',
    ),
    (
        "outcome marqué interrompu",
        '''    if erreur_fiche:
        outcome["erreur_fiche_audit"] = erreur_fiche
''',
        '''    if erreur_fiche:
        outcome["erreur_fiche_audit"] = erreur_fiche
    if interrompu:
        outcome["interrompu"] = True  # ''' + MARQUE + '''
''',
    ),
    (
        "boucle principale : queue sauvée après chaque idée",
        '''    client = get_client()
    remaining = []

    for idea in queue:
        try:
            outcome = process_idea(client, idea, dry_run=args.dry_run)
        except Exception as e:
            outcome = {"status": "needs_review", "idea": idea, "error": str(e)}

        if args.dry_run:
            print(json.dumps(outcome, ensure_ascii=False, indent=2, default=str))
            remaining.append(idea)
            continue

        if outcome["status"] == "injected":
            append_yaml_list(PROCESSED_PATH, outcome, key="processed")
        else:
            append_yaml_list(NEEDS_REVIEW_PATH, outcome, key="needs_review")

    if not args.dry_run:
        save_queue_with_template(remaining)
        print(f"\\nTerminé. Voir {PROCESSED_PATH} et {NEEDS_REVIEW_PATH}.")
''',
        '''    client = get_client()
    _sigterm_comme_ctrl_c()

    for i, idea in enumerate(queue):
        try:
            outcome = process_idea(client, idea, dry_run=args.dry_run)
        except KeyboardInterrupt:
            # ''' + MARQUE + ''' : interruption hors des variables (sélection,
            # fiche d'audit) -- l'idée et les suivantes restent en queue.
            print(f"\\n✗ Interrompu sur {idea.get('id', 'sans_id')} : idée laissée en queue.")
            if not args.dry_run:
                print("  Si une variable avait déjà été écrite, vérifier la section 12 avant de relancer.")
            sys.exit(130)
        except Exception as e:
            outcome = {"status": "needs_review", "idea": idea, "error": str(e)}

        if args.dry_run:
            print(json.dumps(outcome, ensure_ascii=False, indent=2, default=str))
            if outcome.get("interrompu"):
                break
            continue

        if outcome["status"] == "injected":
            append_yaml_list(PROCESSED_PATH, outcome, key="processed")
        else:
            append_yaml_list(NEEDS_REVIEW_PATH, outcome, key="needs_review")

        # ''' + MARQUE + ''' : queue réécrite après CHAQUE idée -- une
        # interruption ne fait plus retraiter une idée déjà passée (doublon du
        # signal sous un slug suffixé _2).
        save_queue_with_template(queue[i + 1:])

        if outcome.get("interrompu"):
            print(f"\\n✗ Run interrompu après {idea.get('id', 'sans_id')} (voir needs_review.yaml, "
                  f"entrée 'idee_a_remettre_en_queue' s'il y en a une). "
                  f"{len(queue) - i - 1} idée(s) restent en queue.")
            sys.exit(130)

    if not args.dry_run:
        print(f"\\nTerminé. Voir {PROCESSED_PATH} et {NEEDS_REVIEW_PATH}.")
''',
    ),
    (
        "SIGTERM -> KeyboardInterrupt",
        "\ndef main():\n",
        '''
def _sigterm_comme_ctrl_c():
    """''' + MARQUE + ''' : un arrêt par SIGTERM (bouton Stop du GUI, kill)
    suit le même chemin propre que Ctrl-C."""
    import signal

    def _handler(signum, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _handler)
    except (ValueError, OSError):
        pass  # hors du thread principal : on garde le comportement par défaut


def main():
''',
    ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fichier", default=os.path.join("generator", "inject_custom_signals.py"))
    args = ap.parse_args()

    if not os.path.exists(args.fichier):
        sys.exit("Fichier introuvable : {}".format(args.fichier))
    with open(args.fichier, encoding="utf-8") as f:
        src = f.read()

    if MARQUE in src:
        print("Déjà appliqué : rien à faire.")
        return
    if "# S22 (5 octobre 2026)" not in src:
        sys.exit("Appliquer d'abord patch_s22_exception_signal.py.")

    for nom, old, new in REMPLACEMENTS:
        n = src.count(old)
        if n != 1:
            sys.exit("ÉCHEC « {} » : {} occurrence(s) au lieu de 1. "
                     "Rien n'a été modifié.".format(nom, n))
        src = src.replace(old, new)
        print("OK  {}".format(nom))
    compile(src, args.fichier, "exec")

    if not args.apply:
        print("\nAperçu seulement (syntaxe vérifiée). Relancer avec --apply.")
        return

    bak = "{}.bak_{}".format(args.fichier, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(args.fichier, bak)
    with open(args.fichier, "w", encoding="utf-8") as f:
        f.write(src)
    print("\nAppliqué. Sauvegarde : {}".format(bak))


if __name__ == "__main__":
    main()
