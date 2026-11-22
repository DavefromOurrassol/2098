#!/usr/bin/env python3
"""
patch_u4n_forces_article.py — Ourrassol 2098 (22 novembre 2026)
===============================================================

B9 « source mince → invention, suite », volet c) : forces des événements tirés
d'un article. Le 11 nov, des faits locaux sont sortis de ✨ Proposer avec 6
variables et des forces de 15 à 22 (la portée « locale » n'est choisie qu'à
l'adoption, après la simulation). Décision de David (22 nov) : 3 impacts, force 12.

Quand ✨ Proposer reçoit une citation d'article (--citation) — jamais pour une
wild card ni pour un signal :
  1. consigne : fait d'abord local ou régional, 2 à 3 impacts de force 3 à 10,
     davantage seulement si l'article décrit lui-même un effet à grande échelle ;
  2. plafond mécanique à la proposition : ARTICLE_MAX_IMPACTS (3, les premiers
     gardés) et ARTICLE_FORCE_MAX (12) ; chaque réduction signalée par un ⚠.
Vérifier / Ajouter ne plafonnent pas : un bloc corrigé à la main garde ses forces.

Cible : generator/hypothese_depuis_texte.py (sauvegarde .bak_u4n).

Usage (depuis la racine du vault) :
    python3 generator/patch_u4n_forces_article.py           # dry-run
    python3 generator/patch_u4n_forces_article.py --apply   # écrit
"""

import argparse
import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/hypothese_depuis_texte.py")
TAG = "u4n"

REMPLACEMENTS = [
    ("constantes ARTICLE_MAX_IMPACTS / ARTICLE_FORCE_MAX",
     "MAX_IMPACTS = 8\n",
     "MAX_IMPACTS = 8\n"
     "ARTICLE_MAX_IMPACTS = 3    # U4n : événement tiré d'un article, à la proposition\n"
     "ARTICLE_FORCE_MAX = 12     # U4n\n"),
    ("prompt : consigne d'un fait d'article",
     '    return f"""{ligne_type}Tu aides l\'auteur',
     '    if imposes and imposes.get("citation") and not imposes.get("wild_card"):   # U4n\n'
     '        ligne_type += ("ÉVÉNEMENT RAPPORTÉ PAR UN ARTICLE : c\'est d\'abord un fait local ou régional. "\n'
     '                       f"Donne 2 à {ARTICLE_MAX_IMPACTS} impacts, de force 3 à 10 ; davantage seulement si "\n'
     '                       "l\'article décrit lui-même un effet à grande échelle (pays entier, continent, monde). "\n'
     '                       f"Au-delà de {ARTICLE_FORCE_MAX}, la force sera ramenée.\\n\\n")\n'
     '    return f"""{ligne_type}Tu aides l\'auteur'),
    ("✨ Proposer : plafond appliqué",
     '    av += appliquer_imposes(h, imposes, h.get("type") == "signal")   # U3c\n',
     '    av += appliquer_imposes(h, imposes, h.get("type") == "signal")   # U3c\n'
     '    if (imposes or {}).get("citation") and not wild and h.get("type") != "signal":   # U4n\n'
     '        av += plafonner_article_u4n(h)\n'),
    ("fonction plafonner_article_u4n()",
     "\n\ndef appliquer_imposes(h, imposes, est_signal):\n",
     '''

def plafonner_article_u4n(h):
    """U4n : événement tiré d'un article -> ARTICLE_MAX_IMPACTS impacts (les premiers),
    forces ramenées à ARTICLE_FORCE_MAX. Modifie h ; retourne les avertissements."""
    av = []
    impacts = list(h.get("impacts") or [])
    if len(impacts) > ARTICLE_MAX_IMPACTS:
        retires = [str(i.get("variable")) for i in impacts[ARTICLE_MAX_IMPACTS:]]
        av.append(f"événement d'article : {len(impacts)} impacts proposés, gardé les {ARTICLE_MAX_IMPACTS} "
                  f"premiers (retirés : {', '.join(retires)}) ; à remettre à la main si l'article le justifie")
        impacts = impacts[:ARTICLE_MAX_IMPACTS]
    for imp in impacts:
        dl = imp.get("delta_level")
        if isinstance(dl, dict):
            trop = {s: v for s, v in dl.items() if isinstance(v, (int, float)) and v > ARTICLE_FORCE_MAX}
            if trop:
                imp["delta_level"] = {s: (min(v, ARTICLE_FORCE_MAX) if isinstance(v, (int, float)) else v)
                                      for s, v in dl.items()}
                av.append(f"événement d'article : {imp.get('variable')} force "
                          + ", ".join(f"{s} {v:g}" for s, v in trop.items())
                          + f" ramenée à {ARTICLE_FORCE_MAX}")
        elif isinstance(dl, (int, float)) and dl > ARTICLE_FORCE_MAX:
            av.append(f"événement d'article : {imp.get('variable')} force {dl:g} ramenée à {ARTICLE_FORCE_MAX}")
            imp["delta_level"] = ARTICLE_FORCE_MAX
    h["impacts"] = impacts
    return av


def appliquer_imposes(h, imposes, est_signal):
'''),
]


def main():
    ap = argparse.ArgumentParser(description="Patch U4n : forces des événements d'article.")
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon dry-run)")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault.")
    texte = CIBLE.read_text(encoding="utf-8")
    if "plafonner_article_u4n" in texte:
        sys.exit("✗ U4n déjà appliqué : rien à faire.")
    nouveau, ok = texte, True
    for nom, ancien, neuf in REMPLACEMENTS:
        n = nouveau.count(ancien)
        if n != 1:
            print(f"✗ {nom} : ancre trouvée {n} fois (attendu 1)")
            ok = False
            continue
        nouveau = nouveau.replace(ancien, neuf)
        print(f"✓ {nom}")
    if not ok:
        sys.exit("✗ Patch non appliqué (fichier différent de celui attendu).")
    try:
        compile(nouveau, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas : {e}")
    print("✓ Le fichier patché compile.")
    if not args.apply:
        print("\n(dry-run) Rien n'est écrit. Relancer avec --apply.")
        return
    shutil.copy(CIBLE, CIBLE.with_name(CIBLE.name + f".bak_{TAG}"))
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"\n→ {CIBLE} patché (sauvegarde {CIBLE.name}.bak_{TAG}).")


if __name__ == "__main__":
    main()
