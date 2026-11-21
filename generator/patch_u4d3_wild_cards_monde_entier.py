#!/usr/bin/env python3
"""
patch_u4d3_wild_cards_monde_entier.py — Ourrassol 2098 (U4d3, 15 novembre 2026)
===============================================================================

Décision de David (15 nov, option B) : la règle reste (3 à 6 variables, chacune de
force 25 à 35, mode rupture = PERMANENT). Une wild card est donc un choc qui change
le monde ENTIER pour de bon, sur plusieurs domaines à la fois -- souvent une
découverte ou une percée, pas une catastrophe régionale dont l'effet s'estompe
(essai du 15 nov : éruption VEI 6 des Champs Phlégréens, écartée).
Exemples donnés par David : gisement sur une autre planète, signe de vie
extraterrestre, molécule qui allonge la vie de 30 ans.

  1. suggerer_lacunes.py --type wildcard : le « bon registre » de U4d2 est remplacé
     par ce critère et ces exemples ; une wild card peut aussi APAISER des domaines.
  2. hypothese_depuis_texte.py (Proposer avec la case ⚡) : la consigne rappelle que
     chaque impact est permanent, qu'on ne retient que les domaines changés pour de
     bon, et qu'un domaine apaisé prend la polarité -1.

USAGE (depuis la racine du vault)
    python3 generator/patch_u4d3_wild_cards_monde_entier.py            # dry-run
    python3 generator/patch_u4d3_wild_cards_monde_entier.py --apply
Sauvegardes .bak_u4d3. Pas de relance de Flask (sous-processus). Exige U4a et U4d2.
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

GEN = Path.cwd() / "generator"
TAG = "U4d3"

SL = [
    ("suggestions : critère et exemples",
     '''Bon registre : impact d'astéroïde moyen, super-éruption volcanique, tempête solaire géante qui coupe les
réseaux, pandémie d'un pathogène nouveau, effondrement brutal d'une calotte glaciaire, percée qui rend une
technologie soudain bon marché, effondrement ou unification surprise d'une grande puissance, guerre nucléaire
limitée, panne durable d'Internet, découverte qui change une ressource.
''',
     '''CHANGER LE MONDE ENTIER POUR DE BON (U4d3) : chaque wild card touche 3 à 6 grands domaines à la fois, et
chaque effet est PERMANENT. Elle transforme durablement le monde entier, pas une région : c'est souvent une
découverte ou une percée, positive ou négative (elle peut APAISER certains domaines et en aggraver d'autres).
Exclus : une catastrophe régionale dont les effets s'estompent en quelques années (éruption, cyclone, séisme,
accident industriel).
Bon registre : gisement exploitable sur une autre planète ou un astéroïde, signe de vie extraterrestre,
molécule qui allonge la vie humaine de 30 ans, énergie quasi gratuite, intelligence artificielle qui dépasse
l'humain dans la recherche, contrôle du climat par géo-ingénierie, pathogène qui rend une partie de l'humanité
stérile, traitement qui supprime une grande maladie, effondrement définitif d'une ressource vitale.
'''),
]

HT = [
    ("proposer : effets permanents",
     '''                       f"plafond de {FORCE_MAX} donné plus bas).\\n\\n")
''',
     '''                       f"plafond de {FORCE_MAX} donné plus bas). Chaque impact est PERMANENT : ne retiens "
                       "que les domaines que l'élément change pour de bon à l'échelle du monde ; un domaine "
                       "qu'il apaise prend la polarité -1.\\n\\n")   # U4d3
'''),
]

FICHIERS = [(GEN / "suggerer_lacunes.py", SL), (GEN / "hypothese_depuis_texte.py", HT)]


def main():
    a = argparse.ArgumentParser(description="U4d3 : wild cards qui changent le monde entier.")
    a.add_argument("--apply", action="store_true")
    x = a.parse_args()
    if not GEN.is_dir():
        sys.exit("✗ lancer depuis la racine du vault (dossier generator/ introuvable)")
    nouveaux, erreurs = {}, []
    for chemin, remp in FICHIERS:
        if not chemin.exists():
            erreurs.append(f"{chemin.name} introuvable")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if TAG in texte:
            erreurs.append(f"{chemin.name} : {TAG} déjà appliqué")
            continue
        for libelle, avant, apres in remp:
            n = texte.count(avant)
            if n != 1:
                erreurs.append(f"{chemin.name} [{libelle}] : passage trouvé {n} fois (attendu 1) — U4a / U4d2 appliqués ?")
                continue
            texte = texte.replace(avant, apres)
        nouveaux[chemin] = texte
    if erreurs:
        sys.exit("✗ Rien n'est écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
    for chemin, neuf in nouveaux.items():
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(neuf)
        try:
            py_compile.compile(f.name, doraise=True)
        except py_compile.PyCompileError as e:
            sys.exit(f"✗ {chemin.name} : syntaxe invalide après patch, rien n'est écrit\n{e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
        print(f"generator/{chemin.name} : 1 modification")
    if not x.apply:
        print("\nDRY-RUN : syntaxe vérifiée sur copie, rien n'est écrit. Relancer avec --apply.")
        return
    for chemin, neuf in nouveaux.items():
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_u4d3"))
        chemin.write_text(neuf, encoding="utf-8")
    print("\n✓ U4d3 appliqué (sauvegardes .bak_u4d3). Pas de relance de Flask.")


if __name__ == "__main__":
    main()
