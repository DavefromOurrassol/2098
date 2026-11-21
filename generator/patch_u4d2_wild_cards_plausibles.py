#!/usr/bin/env python3
"""
patch_u4d2_wild_cards_plausibles.py — Ourrassol 2098 (U4d2, 15 novembre 2026)
=============================================================================

Premier essai réel du bouton ⚡ (15 nov) : les 3 idées étaient physiquement
impossibles (résurrection génétique spontanée, dérive de la constante alpha,
inversion chirale de la biosphère). Une wild card est IMPROBABLE, pas impossible.

  1. Consigne de suggerer_lacunes.py --type wildcard : chaque idée doit rester
     possible selon la science actuelle, avec un mécanisme connu ; le fantastique
     est exclu ; exemples du bon registre et du mauvais registre.
  2. « En 2041. » n'est plus ajouté au texte quand la description donne déjà l'année.

USAGE (depuis la racine du vault)
    python3 generator/patch_u4d2_wild_cards_plausibles.py            # dry-run
    python3 generator/patch_u4d2_wild_cards_plausibles.py --apply
Sauvegarde : suggerer_lacunes.py.bak_u4d2. Pas de relance de Flask (sous-processus).
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

CHEMIN = Path.cwd() / "generator" / "suggerer_lacunes.py"

REMP = [
    ("consigne : improbable, pas impossible",
     '''Une wild card est une rupture à FAIBLE probabilité et à IMPACT MAJEUR, qu'aucun signal faible du monde n'annonce
encore. Elle change le monde pour de bon et a le droit d'aller contre les tendances des scénarios (ruptures
technologiques, géopolitiques, sociales, sanitaires, environnementales, spatiales…).
''',
     '''Une wild card est une rupture à FAIBLE probabilité et à IMPACT MAJEUR, qu'aucun signal faible du monde n'annonce
encore. Elle change le monde pour de bon et a le droit d'aller contre les tendances des scénarios (ruptures
technologiques, géopolitiques, sociales, sanitaires, environnementales, spatiales…).
IMPROBABLE NE VEUT PAS DIRE IMPOSSIBLE (U4d2) : chaque idée doit rester possible selon la science actuelle,
avec un mécanisme connu (physique, biologique, technique, politique) ; un expert du domaine doit pouvoir dire
« peu probable, mais ça peut arriver ». Pas de fantastique ni de science-fiction gratuite : aucune loi physique
qui change, aucune espèce éteinte qui revient seule, aucune biologie inversée à l'échelle de la planète.
Bon registre : impact d'astéroïde moyen, super-éruption volcanique, tempête solaire géante qui coupe les
réseaux, pandémie d'un pathogène nouveau, effondrement brutal d'une calotte glaciaire, percée qui rend une
technologie soudain bon marché, effondrement ou unification surprise d'une grande puissance, guerre nucléaire
limitée, panne durable d'Internet, découverte qui change une ressource.
'''),
    ("texte : année non répétée",
     '''        texte = desc + (f" En {date}." if date else "")
''',
     '''        texte = desc + (f" En {date}." if date and str(date) not in desc else "")   # U4d2
'''),
]


def main():
    a = argparse.ArgumentParser(description="U4d2 : wild cards plausibles.")
    a.add_argument("--apply", action="store_true")
    x = a.parse_args()
    if not CHEMIN.exists():
        sys.exit("✗ generator/suggerer_lacunes.py introuvable : lancer depuis la racine du vault")
    texte = CHEMIN.read_text(encoding="utf-8")
    if "U4d2" in texte:
        sys.exit("✗ U4d2 déjà appliqué")
    if "_wild_cards" not in texte:
        sys.exit("✗ U4d absent : appliquer d'abord patch_u4d_wild_card_gui.py")
    erreurs = []
    for libelle, avant, apres in REMP:
        n = texte.count(avant)
        if n != 1:
            erreurs.append(f"[{libelle}] passage trouvé {n} fois (attendu 1)")
            continue
        texte = texte.replace(avant, apres)
    if erreurs:
        sys.exit("✗ Rien n'est écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(texte)
    try:
        py_compile.compile(f.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ syntaxe invalide après patch, rien n'est écrit\n{e}")
    finally:
        Path(f.name).unlink(missing_ok=True)
    print(f"generator/suggerer_lacunes.py : {len(REMP)} modification(s)")
    for libelle, _, _ in REMP:
        print(f"  · {libelle}")
    if not x.apply:
        print("\nDRY-RUN : syntaxe vérifiée sur copie, rien n'est écrit. Relancer avec --apply.")
        return
    shutil.copy2(CHEMIN, CHEMIN.with_name(CHEMIN.name + ".bak_u4d2"))
    CHEMIN.write_text(texte, encoding="utf-8")
    print("\n✓ U4d2 appliqué (sauvegarde .bak_u4d2). Pas de relance de Flask ; Cmd-Maj-R inutile.")


if __name__ == "__main__":
    main()
