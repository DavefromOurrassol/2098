#!/usr/bin/env python3
"""
patch_s22_exception_signal.py — Ourrassol 2098 (S22, 5 octobre 2026)

Corrige le « signal orphelin » de inject_custom_signals.py : une exception
pendant le traitement d'UNE variable ne fait plus partir l'idée entière en
needs_review sans fiche d'audit.

Ce que le patch change dans process_idea() :
  1. Chaque variable est traitée dans un try/except : une exception devient
     un échec de CETTE variable (status needs_review, motif « exception : … »),
     exactement comme un échec de validation. Les variables déjà injectées
     gardent leur fiche d'audit et l'entrée `idee_a_remettre_en_queue`.
  2. Avant d'écrire une variable, un instantané de sa fiche et du registre est
     pris ; si une exception survient pendant l'écriture (section 12 écrite,
     section 7 ou registre non), les deux fichiers sont RESTAURÉS. Sans ça, la
     variable resterait à moitié injectée et le garde-fou anti-doublon la
     sauterait pour toujours à la reprise.
  3. Un échec de write_custom_fiche() est signalé explicitement (outcome
     `erreur_fiche_audit` + commande de nettoyage) au lieu de remonter en
     exception générique.

Usage (depuis la racine du vault) :
    python3 generator/patch_s22_exception_signal.py            # aperçu, n'écrit rien
    python3 generator/patch_s22_exception_signal.py --apply    # écrit (.bak_s22)
"""

import argparse
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "inject_custom_signals.py"
MARQUEUR = "# S22 (5 octobre 2026)"

HELPERS = '''

# ---------------------------------------------------------------------------
# S22 (5 octobre 2026) — instantané avant écriture d'une variable
# ---------------------------------------------------------------------------

def _instantane_ecriture(variable_slug):
    """Copie en mémoire la fiche variable et le registre AVANT d'écrire, pour
    pouvoir annuler une écriture interrompue par une exception."""
    var_path = VARIABLES_DIR / f"{variable_slug}.md"
    return {
        "var_path": var_path,
        "var": var_path.read_text(encoding="utf-8"),
        "reg": REGISTRE_PATH.read_text(encoding="utf-8") if REGISTRE_PATH.exists() else None,
    }


def _restaurer_instantane(snap):
    """Remet la fiche variable et le registre dans leur état d'avant l'écriture.
    Retourne True si la restauration a réussi."""
    try:
        snap["var_path"].write_text(snap["var"], encoding="utf-8")
        if snap["reg"] is not None:
            REGISTRE_PATH.write_text(snap["reg"], encoding="utf-8")
        return True
    except Exception as e:  # restauration impossible : on le dit, sans masquer l'erreur d'origine
        print(f"  ✗✗ Restauration impossible ({e}) : vérifier {snap['var_path'].name} "
              f"et {REGISTRE_PATH.name} à la main.")
        return False
'''

ANCRE_HELPERS = "\ndef process_idea(client, idea, dry_run=False):\n"
ANCRE_BOUCLE = "    for variable_slug in variables:\n"
ANCRE_FIN_BOUCLE = '\n    injectees = [r["variable"] for r in results if r["status"] == "injected"]\n'
ANCRE_ECRITURE = (
    "        if not dry_run:\n"
    "            inject_signal_to_state(variable_slug, yaml_text)\n"
)
NOUVELLE_ECRITURE = (
    "        if not dry_run:\n"
    "            ecriture = _instantane_ecriture(variable_slug)  # S22 : annulable\n"
    "            inject_signal_to_state(variable_slug, yaml_text)\n"
)

EXCEPT_BLOC = '''        except Exception as e:
            # S22 (5 octobre 2026) : une exception sur UNE variable devient un
            # échec de cette variable (comme un échec de validation), au lieu
            # de remonter jusqu'à main() et d'envoyer l'idée entière en
            # needs_review sans fiche d'audit ni reprise possible.
            annulee = False
            if ecriture is not None:
                annulee = _restaurer_instantane(ecriture)
                registre_text = read_registre_text()
            motif = f"exception : {type(e).__name__}: {e}"
            print(f"  ✗ {variable_slug} : {motif}"
                  + (" -- écriture annulée (fiche et registre restaurés)" if annulee else ""))
            results.append({"variable": variable_slug, "status": "needs_review",
                            "issues": [motif], "exception": True,
                            "ecriture_annulee": annulee})
            continue
'''

ANCRE_FICHE_DEBUT = "            write_custom_fiche(signal_slug, idea_text, source, injectees, categorie,\n"
ANCRE_FICHE_FIN = "                                completer=bool(reprise))\n"

ANCRE_OVERALL = '    overall = "needs_review" if echouees else "injected"\n'
NOUVEAU_OVERALL = '''    overall = "needs_review" if (echouees or erreur_fiche) else "injected"
'''


def patcher(src):
    if MARQUEUR in src:
        raise SystemExit("Patch S22 déjà appliqué -- rien à faire.")
    for nom, ancre in (("process_idea", ANCRE_HELPERS), ("boucle", ANCRE_BOUCLE),
                       ("fin de boucle", ANCRE_FIN_BOUCLE), ("écriture", ANCRE_ECRITURE),
                       ("fiche d'audit", ANCRE_FICHE_DEBUT), ("statut final", ANCRE_OVERALL)):
        n = src.count(ancre)
        if n != 1:
            raise SystemExit(f"Ancre « {nom} » trouvée {n} fois (attendu 1) -- fichier différent "
                             f"de la version du 1er oct, patch non appliqué.")

    # 1. Helpers juste avant process_idea()
    src = src.replace(ANCRE_HELPERS, HELPERS + "\n" + ANCRE_HELPERS, 1)

    # 2. Boucle par variable enveloppée dans try/except
    debut = src.index(ANCRE_BOUCLE) + len(ANCRE_BOUCLE)
    fin = src.index(ANCRE_FIN_BOUCLE)
    corps = src[debut:fin]
    if corps.count(ANCRE_ECRITURE) != 1:
        raise SystemExit("Ancre « écriture » hors de la boucle -- patch non appliqué.")
    corps = corps.replace(ANCRE_ECRITURE, NOUVELLE_ECRITURE, 1)
    corps_indente = "".join(("    " + l) if l.strip() else l for l in corps.splitlines(True))
    nouvelle_boucle = (
        "        ecriture = None  # S22 : instantané pris juste avant d'écrire\n"
        "        try:\n" + corps_indente.rstrip("\n") + "\n" + EXCEPT_BLOC
    )
    src = src[:debut] + nouvelle_boucle + src[fin:]

    # 3. write_custom_fiche() protégée
    d = src.index(ANCRE_FICHE_DEBUT)
    f = src.index(ANCRE_FICHE_FIN, d) + len(ANCRE_FICHE_FIN)
    appel = src[d:f]
    appel_indente = "".join(("    " + l) if l.strip() else l for l in appel.splitlines(True))
    protege = (
        "            try:\n" + appel_indente +
        "            except Exception as e:\n"
        "                # S22 : le signal est écrit dans les fiches variables mais\n"
        "                # sans fiche d'audit -- on le dit clairement.\n"
        "                erreur_fiche = f\"{type(e).__name__}: {e}\"\n"
        "                print(f\"  ✗ Fiche d'audit non écrite ({erreur_fiche}). Signal présent dans \"\n"
        "                      f\"{injectees} sans fiche : nettoyer avec \"\n"
        "                      f\"undo_custom.py --slug {signal_slug} --type signal, puis remettre l'idée en queue.\")\n"
    )
    src = src[:d] + protege + src[f:]

    # 4. Initialisation + statut final
    src = src.replace(ANCRE_FIN_BOUCLE,
                      "\n    erreur_fiche = None  # S22" + ANCRE_FIN_BOUCLE, 1)
    src = src.replace(ANCRE_OVERALL, NOUVEAU_OVERALL, 1)
    src = src.replace(
        '    outcome = {"status": overall, "idea": idea, "selection": selection, "results": results}\n',
        '    outcome = {"status": overall, "idea": idea, "selection": selection, "results": results}\n'
        '    if erreur_fiche:\n'
        '        outcome["erreur_fiche_audit"] = erreur_fiche\n', 1)

    src = src.replace('import dynamique as dyn',
                      'import dynamique as dyn  ' + MARQUEUR + ' : exceptions par variable', 1) \
        if 'import dynamique as dyn  # niveaux' not in src else \
        src.replace('import dynamique as dyn  # niveaux',
                    'import dynamique as dyn  ' + MARQUEUR + ' -- niveaux', 1)
    compile(src, str(CIBLE), "exec")  # erreur de syntaxe = arrêt avant toute écriture
    return src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (.bak_s22 avant)")
    ap.add_argument("--cible", default=str(CIBLE), help=argparse.SUPPRESS)
    args = ap.parse_args()
    cible = Path(args.cible)
    nouveau = patcher(cible.read_text(encoding="utf-8"))
    if not args.apply:
        print(f"Aperçu OK : {cible.name} serait patché (syntaxe vérifiée). Relancer avec --apply.")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_s22"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"Patch S22 appliqué à {cible} (sauvegarde : {cible.name}.bak_s22).")


if __name__ == "__main__":
    main()
