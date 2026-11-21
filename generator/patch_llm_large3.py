#!/usr/bin/env python3
"""
patch_llm_large3.py — Ourrassol 2098 (21 nov 2026)

`mistral-large-latest` pointe désormais vers Mistral Large 4 (modèle qui raisonne avant de
répondre : plus lent, plus cher ; constaté le 21 nov, alias ['mistral-large-4', 'mistral-large-4-0']).
Large 4 n'a jamais été retenu par défaut (backlog B8). Ce patch fixe la version explicite de
Large 3, `mistral-large-2512`, pour les trois niveaux qui utilisaient l'alias :
strict, structured_strict, creative_souple. Le niveau volume (mistral-small) ne change pas.

Revenir à Large 4 : remettre « mistral-large-latest » (ou « mistral-large-4 ») dans
TASK_TIER_DEFAULTS. Un test ponctuel reste possible par LLM_PROVIDER / LLM_MODEL.

Fichier touché : generator/llm_client.py

Usage (depuis la racine du vault) :
    python3 generator/patch_llm_large3.py           # dry-run
    python3 generator/patch_llm_large3.py --apply   # écrit (.bak_large3)
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/llm_client.py")
TAG = "LARGE3"

AVANT = '''TASK_TIER_DEFAULTS = {
    "strict":            {"provider": "mistral", "model": "mistral-large-latest"},
    "structured_strict": {"provider": "mistral", "model": "mistral-large-latest"},
    "creative_souple":   {"provider": "mistral", "model": "mistral-large-latest"},
'''

APRES = '''# LARGE3 (21 nov 2026) : « mistral-large-latest » est devenu Mistral Large 4, qui raisonne avant
# de répondre (≈ 4 min par lot de la Passe exhaustive). Version explicite de Large 3 fixée ici ;
# Large 4 reste disponible sous « mistral-large-4 » (backlog B8).
TASK_TIER_DEFAULTS = {
    "strict":            {"provider": "mistral", "model": "mistral-large-2512"},
    "structured_strict": {"provider": "mistral", "model": "mistral-large-2512"},
    "creative_souple":   {"provider": "mistral", "model": "mistral-large-2512"},
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault")
    texte = CIBLE.read_text(encoding="utf-8")
    if "LARGE3" in texte:
        print(f"✓ {TAG} déjà appliqué, rien à faire")
        return
    n = texte.count(AVANT)
    if n != 1:
        sys.exit(f"✗ ancre TASK_TIER_DEFAULTS trouvée {n} fois (1 attendue) : rien n'est écrit")
    nouveau = texte.replace(AVANT, APRES)
    print(f"[{TAG}] {CIBLE} : strict, structured_strict, creative_souple -> mistral-large-2512")
    print(f"[{TAG}] {len(texte.splitlines())} -> {len(nouveau.splitlines())} lignes")
    if not args.apply:
        print(f"[{TAG}] dry-run : relancer avec --apply pour écrire")
        return
    bak = CIBLE.with_name(CIBLE.name + ".bak_large3")
    shutil.copy(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(CIBLE), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy(bak, CIBLE)
        sys.exit(f"✗ syntaxe invalide, fichier restauré : {e}")
    print(f"✓ [{TAG}] appliqué (sauvegarde {bak.name}). Relancer Flask pour le GUI.")


if __name__ == "__main__":
    main()
