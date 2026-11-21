#!/usr/bin/env python3
"""
patch_u4d5_scenarios_depuis_idee.py — Ourrassol 2098 (21 nov 2026)

U4d5 : une idée qui porte une ligne « Scénarios : a, b. » (bouton ⚡, suggestions 💡)
impose ses scénarios à ✨ Proposer, comme --scenarios. Avant : la ligne n'était
qu'une indication pour l'IA, qui l'ignorait (Shackleton : bloc en « tous »).

Fichier touché : generator/hypothese_depuis_texte.py
  1. nouvelle fonction scenarios_depuis_idee(texte) ;
  2. proposer() : si aucun --scenarios n'est donné (et pas de type signal), la ligne
     de l'idée devient un scénario imposé (avertissement « scénarios repris de
     l'idée ») ; les scénarios imposés sont posés AVANT la normalisation, pour que
     les forces par scénario (U4f) ne gardent que les scénarios couverts.

Usage (depuis la racine du vault) :
    python3 generator/patch_u4d5_scenarios_depuis_idee.py           # dry-run
    python3 generator/patch_u4d5_scenarios_depuis_idee.py --apply   # écrit (.bak_u4d5)
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/hypothese_depuis_texte.py")
TAG = "U4d5"

ANCRE_FONCTION = "def proposer(texte, _llm=appeler_llm, type_force=None, imposes=None):\n"

FONCTION = '''def scenarios_depuis_idee(texte):
    """U4d5 : ligne « Scénarios : a, b. » écrite dans l'idée (bouton ⚡, suggestions 💡).
    Retourne [] pour « tous », une liste de slugs, ou None si aucune ligne lisible.
    Une ligne qui ne contient pas que des slugs de scénarios est ignorée (ex. la
    raison « Scénarios : pourquoi… » d'une idée ⚡)."""
    for m in re.finditer(r"Sc[ée]narios?\\s*:\\s*([^.\\n]+)", texte or "", flags=re.I):
        brut = m.group(1).strip()
        if brut.lower() in ("tous", "tous les scénarios"):
            return []
        morceaux = [x.strip().lower() for x in re.split(r",|\\bet\\b", brut) if x.strip()]
        if morceaux and all(x in se.SCENARIOS for x in morceaux):
            valides = list(dict.fromkeys(morceaux))
            return [] if len(valides) == len(se.SCENARIOS) else valides
    return None


'''

AVANT = '''    wild = bool((imposes or {}).get("wild_card"))   # U4a
    if wild and type_force == "signal":
        raise ValueError("une wild card est un événement, pas un signal")
    variables = valid_vars()
    brut = _llm(construire_prompt(texte, variables, type_force, imposes))
    if not isinstance(brut, dict):
        raise ValueError("réponse de l'IA inexploitable")
    if type_force in ("evenement", "signal"):
        brut["type"] = type_force   # le choix de l'auteur l'emporte sur celui de l'IA
    h, av = normaliser_proposition(brut, variables, ids_existants(), wild=wild)
'''

APRES = '''    wild = bool((imposes or {}).get("wild_card"))   # U4a
    if wild and type_force == "signal":
        raise ValueError("une wild card est un événement, pas un signal")
    av0 = []
    if type_force != "signal" and (imposes or {}).get("scenarios") is None:   # U4d5
        sc_idee = scenarios_depuis_idee(texte)
        if sc_idee is not None:
            imposes = dict(imposes or {}, scenarios=sc_idee)
            av0.append("scénarios repris de l'idée : " + (", ".join(sc_idee) if sc_idee else "tous"))
    variables = valid_vars()
    brut = _llm(construire_prompt(texte, variables, type_force, imposes))
    if not isinstance(brut, dict):
        raise ValueError("réponse de l'IA inexploitable")
    if type_force in ("evenement", "signal"):
        brut["type"] = type_force   # le choix de l'auteur l'emporte sur celui de l'IA
    sc_imp = (imposes or {}).get("scenarios")   # U4d5 : scénarios imposés posés avant la normalisation
    if sc_imp is not None and str(brut.get("type") or "").strip().lower() != "signal":
        v_ = [s for s in sc_imp if s in se.SCENARIOS]
        if v_ or not sc_imp:   # des noms tous inconnus restent signalés par appliquer_imposes()
            brut["scenarios"] = v_ if 0 < len(v_) < len(se.SCENARIOS) else "tous"
    h, av = normaliser_proposition(brut, variables, ids_existants(), wild=wild)
    av = av0 + av
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault")
    texte = CIBLE.read_text(encoding="utf-8")
    if "def scenarios_depuis_idee(" in texte:
        sys.exit(f"✓ {TAG} déjà appliqué, rien à faire")
    for nom, ancre in (("début de proposer()", ANCRE_FONCTION), ("corps de proposer()", AVANT)):
        n = texte.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (1 attendue) : rien n'est écrit")
    nouveau = texte.replace(ANCRE_FONCTION, FONCTION + ANCRE_FONCTION).replace(AVANT, APRES)
    print(f"[{TAG}] {CIBLE} : + scenarios_depuis_idee() ; proposer() lit « Scénarios : … » de l'idée")
    print(f"[{TAG}] {len(texte.splitlines())} -> {len(nouveau.splitlines())} lignes")
    if not args.apply:
        print(f"[{TAG}] dry-run : relancer avec --apply pour écrire")
        return
    bak = CIBLE.with_name(CIBLE.name + ".bak_u4d5")
    shutil.copy(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(CIBLE), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy(bak, CIBLE)
        sys.exit(f"✗ syntaxe invalide, fichier restauré : {e}")
    print(f"✓ [{TAG}] appliqué (sauvegarde {bak.name})")


if __name__ == "__main__":
    main()
