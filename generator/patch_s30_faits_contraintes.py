#!/usr/bin/env python3
"""
patch_s30_faits_contraintes.py — Ourrassol 2098 (S30, 31 octobre 2026)
======================================================================

Défaut trouvé au test réel de S30 (exemple reunification_ecosse_2070) : le
fait imposé « l'Écosse fait de nouveau partie du Royaume-Uni » a été remplacé
par une réintégration dans l'UOC, sur deux tirages, sans alerte. Le seul
contrôle des faits (verifier_faits, v8.18) regarde les entités censées
survivre (« reste ») et le mot « matrice ». À la simulation d'injection, un
fait « change » avait aussi été inversé (Consortium censé décliner, devenu
tuteur des infrastructures).

Correctif dans inject_custom_events.py :
  - verifier_contraintes() : un appel IA (tier structured_strict, ≈ 1 centime)
    demande, pour chaque fait imposé « contrainte », « change » ou « zone » du
    scénario, s'il est respecté, avec la citation qui le contredit ;
  - à la validation [3/4] : fait non respecté ⇒ UNE réécriture, par le même
    mécanisme que les autres problèmes (issues → step2_develop_instance) ;
  - toujours non respecté ensuite : alerte ⚠ (non bloquante), comme les autres
    alertes de faits. Appel en échec : alerte « relire à la main ».
  - sans faits_imposes (injection ordinaire) : aucun appel, rien ne change.

USAGE (depuis la racine du vault)
    python3 generator/patch_s30_faits_contraintes.py            # aperçu
    python3 generator/patch_s30_faits_contraintes.py --apply    # écrit (sauvegarde .bak_s30faits)
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S30_CONTRAINTES"

ANCRE_FONCTION = "def process_idea(client, idea, dry_run=False):\n"
FONCTION = r'''# PATCH_S30_CONTRAINTES (31 octobre 2026) : les faits imposés « contrainte », « change » et
# « zone » sont vérifiés par l'IA (verifier_faits ne regarde que « reste »).
SORTS_CONTROLES_S30 = ("contrainte", "change", "zone")


def verifier_contraintes(instance_data, idea, scenario):
    """Faits imposés non respectés par le récit : liste de phrases (vide si tout est
    respecté, s'il n'y a pas de fait à contrôler, ou si l'appel échoue — alors ⚠)."""
    faits = [f for f in _faits_du_scenario(idea, scenario)
             if (f.get("sort") or "contrainte") in SORTS_CONTROLES_S30]
    if not faits:
        return []
    recit = "\n\n".join(f"{k} : {' '.join(str(instance_data.get(k)).split())}"
                        for k in ("nom", "evenement_cle", "realisation", "description_complete", "consequences")
                        if instance_data.get(k))
    liste = "\n".join(f"{i}. {f['fait']}" for i, f in enumerate(faits, 1))
    system = ("Tu contrôles la cohérence d'un récit d'événement fictif avec des faits imposés. "
              "Tu réponds uniquement en JSON.")
    user = f"""FAITS IMPOSÉS :
{liste}

RÉCIT :
{recit}

Pour chaque fait, dis si le récit le respecte.
- NON respecté : le récit le contredit, ou met autre chose à sa place (autre rattachement, autre pays,
  autre institution, sens d'évolution inverse : un acteur censé décliner qui gagne du pouvoir, etc.).
- Respecté : le récit le confirme, ou n'en parle pas — sauf si le fait est le sujet même de
  l'événement : il doit alors y figurer.
Ne juge que les faits listés, ni le style ni la vraisemblance.
Réponds : {{"faits": [{{"n": 1, "respecte": true, "citation": "", "explication": ""}}]}}
- citation : passage exact du récit qui contredit le fait (vide si respecté) ;
- explication : une phrase."""
    try:
        rep = call_claude_json(None, system, user, max_tokens=1200)
    except Exception as e:
        print(f"  ⚠ [{scenario}] vérification des faits imposés impossible ({type(e).__name__}) : "
              "relire le récit à la main")
        return []
    out = []
    for r in (rep.get("faits") if isinstance(rep, dict) else None) or []:
        if not isinstance(r, dict) or str(r.get("respecte")).strip().lower() not in ("false", "non", "0"):
            continue
        try:
            f = faits[int(r.get("n")) - 1]
        except (TypeError, ValueError, IndexError):
            continue
        cit = " ".join(str(r.get("citation") or "").split())[:200]
        expl = " ".join(str(r.get("explication") or "").split())
        out.append(f"« {f['fait']} »" + (f" — {expl}" if expl else "") + (f" (récit : « {cit} »)" if cit else ""))
    print(f"  [faits imposés] {len(faits)} contrôlé(s), {len(out)} non respecté(s)")
    return out


'''

ANCRE_BOUCLE = '''            for attempt in range(MAX_FIX_ATTEMPTS + 1):
                print(f"[3/4] Validation (essai {attempt + 1})...")
                issues = validate_instance(
                    instance_data, variables, scenario, registre_text, available_actors
                )
                if not issues:
                    break
'''
BOUCLE = '''            etat_contraintes, relance_contraintes = None, False   # PATCH_S30_CONTRAINTES
            for attempt in range(MAX_FIX_ATTEMPTS + 1):
                print(f"[3/4] Validation (essai {attempt + 1})...")
                issues = validate_instance(
                    instance_data, variables, scenario, registre_text, available_actors
                )
                if not issues:   # PATCH_S30_CONTRAINTES : faits imposés, une réécriture au plus
                    etat_contraintes = verifier_contraintes(instance_data, idea, scenario)
                    if etat_contraintes and not relance_contraintes and attempt < MAX_FIX_ATTEMPTS:
                        relance_contraintes = True
                        issues = ["Fait imposé non respecté, à corriger sans rien changer d'autre : " + v
                                  for v in etat_contraintes]
                if not issues:
                    break
'''

ANCRE_ALERTE = '''            for avert in verifier_faits(instance_data, idea, scenario, available_actors):  # PATCH_S27_V818
                print(f"  ⚠ [{scenario}] {avert}")
'''
ALERTE = ANCRE_ALERTE + '''            for v in etat_contraintes or []:   # PATCH_S30_CONTRAINTES
                print(f"  ⚠ [{scenario}] fait imposé non respecté : {v}")
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fichier", default=str(Path(__file__).resolve().parent / "inject_custom_events.py"))
    a = ap.parse_args()

    cible = Path(a.fichier)
    if not cible.exists():
        sys.exit(f"✗ {cible} introuvable")
    texte = cible.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        print(f"· déjà appliqué ({MARQUEUR} présent) : rien à faire.")
        return
    for nom, ancre in (("fonction", ANCRE_FONCTION), ("boucle", ANCRE_BOUCLE), ("alerte", ANCRE_ALERTE)):
        n = texte.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (1 attendue) : fichier différent de celui analysé, rien écrit.")

    nouveau = (texte.replace(ANCRE_FONCTION, FONCTION + ANCRE_FONCTION)
                    .replace(ANCRE_BOUCLE, BOUCLE)
                    .replace(ANCRE_ALERTE, ALERTE))

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(nouveau)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ le fichier patché ne compile pas, rien écrit :\n{e}")
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    print(f"{'ÉCRITURE' if a.apply else 'APERÇU (rien écrit)'} — {cible.name}")
    print("  + verifier_contraintes (appel IA, faits « contrainte », « change », « zone »)")
    print("  + validation [3/4] : fait non respecté ⇒ une réécriture, puis ⚠ s'il l'est toujours")
    print(f"  compilation : OK ({len(texte.splitlines())} → {len(nouveau.splitlines())} lignes)")
    if not a.apply:
        print("\nRelancer avec --apply pour écrire (sauvegarde .bak_s30faits).")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_s30faits"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"\n✓ {cible.name} patché (sauvegarde {cible.name}.bak_s30faits)")


if __name__ == "__main__":
    main()
