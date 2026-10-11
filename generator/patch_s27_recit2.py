#!/usr/bin/env python3
"""
patch_s27_recit2.py — Ourrassol 2098 (S27, 10 octobre 2026)

trace_injection.py, suite de patch_s27_recit.py : les fiches variables/ n'ont
pas de nom lisible (name = slug). Le récit rétablit donc les accents mot par
mot sur le slug (« frontieres du systeme » → « frontières du système »).

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_recit2.py --dry-run
    python3 generator/patch_s27_recit2.py
Sauvegarde : generator/trace_injection.py.bak_recit2. Refuse un second passage.
"""
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "trace_injection.py"
MARQUEUR = "_ACCENTS_VARIABLES"

AVANT = '''    label = _label_variable(v)
    if not label or label == v:
        return v.replace("_", " ")
'''
APRES = '''    label = _label_variable(v)
    if not label or label == v:
        # S27 : name = slug dans variables/ ; accents rétablis mot par mot.
        return " ".join(_ACCENTS_VARIABLES.get(m, m) for m in v.split("_"))
'''
AVANT2 = '''def _libelle_var(v):
'''
APRES2 = '''_ACCENTS_VARIABLES = {
    "frontieres": "frontières", "systeme": "système", "systemes": "systèmes",
    "energie": "énergie", "geopolitique": "géopolitique", "demographie": "démographie",
    "mobilite": "mobilité", "societe": "société", "securite": "sécurité",
    "sante": "santé", "ecologie": "écologie", "economie": "économie",
    "economique": "économique", "inegalites": "inégalités", "cohesion": "cohésion",
    "identite": "identité", "biodiversite": "biodiversité", "souverainete": "souveraineté",
}


def _libelle_var(v):
'''


def main():
    dry = "--dry-run" in sys.argv
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable")
    src = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in src:
        sys.exit("✗ Patch déjà appliqué : rien à faire.")
    if "# S27 (10 oct) : nom lisible de la variable" not in src:
        sys.exit("✗ Lancer d'abord patch_s27_recit.py.")
    for a in (AVANT, AVANT2):
        if src.count(a) != 1:
            sys.exit(f"✗ Ancre trouvée {src.count(a)} fois (1 attendue) :\n{a[:80]}")
    nouveau = src.replace(AVANT, APRES).replace(AVANT2, APRES2)
    try:
        compile(nouveau, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas : {e}")
    print(f"2 modifications prêtes dans {CIBLE.name} ({len(src)} → {len(nouveau)} caractères).")
    if dry:
        print("Aperçu seulement (--dry-run) : rien n'est écrit.")
        return
    sauvegarde = CIBLE.with_name(CIBLE.name + ".bak_recit2")
    sauvegarde.write_text(src, encoding="utf-8")
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"✓ {CIBLE.name} corrigé (sauvegarde : {sauvegarde.name}).")


if __name__ == "__main__":
    main()
