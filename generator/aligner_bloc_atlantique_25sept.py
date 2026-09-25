#!/usr/bin/env python3
"""
Script ponctuel (25 sept 2026, suite de l'audit du lore fortress_world).

1. instances/bloc_atlantique_fortress_world.md — la fiche (juin 2026) place
   le PAPC dans des territoires qui n'appartiennent pas au Bloc Atlantique :
   Irlande (Zone Interdite de Heysham, quarantaine depuis 2044), Lisbonne et
   Maroc (Al-Hima). Décision David : Charte de Halifax.
     Charte de Dublin        -> Charte de Halifax
     siège Lisbonne-Haute    -> Halifax-Haute
     Irlande fortifiée / enclaves marocaines -> Groenland fortifié / enclaves caribéennes
2. Article du 21 juin (sciences_technologies) — activité actuelle en Écosse
   (quarantaine). Décision David : retoucher l'article.
     corridor Reykjavik-Édimbourg -> Halifax–Saint-Jean de Terre-Neuve
     hub secondaire en Écosse-Nord -> hub secondaire du Labrador

Chaque remplacement doit trouver exactement le nombre d'occurrences attendu
(frontmatter + corps pour la fiche), sinon rien n'est écrit. Frontmatter relu
par yaml.safe_load avant écriture. .bak de chaque fichier.

Usage (depuis la racine du vault) :
  python3 generator/aligner_bloc_atlantique_25sept.py            # aperçu
  python3 generator/aligner_bloc_atlantique_25sept.py --execute  # écriture
"""
import re
import shutil
import sys
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent
FICHE = VAULT / "instances" / "bloc_atlantique_fortress_world.md"
ARTICLE_NOM = "20260621_195524_fortress_world_sciences_technologies_article.md"

PLAN_FICHE = [
    ("lieu (siège)", "lieu: Bloc Atlantique (siège à Lisbonne-Haute)",
     "lieu: Bloc Atlantique (siège à Halifax-Haute)", 1),
    ("rôle (charte)", "codifiée dans la Charte de Dublin (2061)",
     "codifiée dans la Charte de Halifax (2061)", 2),
    ("description (siège)", "Depuis son siège permanent de Lisbonne-Haute",
     "Depuis son siège permanent de Halifax-Haute", 2),
    ("description (charte)", "Fondé sur la Charte de Dublin",
     "Fondé sur la Charte de Halifax", 2),
    ("description (membres)",
     "de l'Irlande fortifiée aux enclavess marocaines du Nord sous protectorat",
     "du Groenland fortifié aux enclaves caribéennes sous protectorat", 2),
]
PLAN_ARTICLE = [
    ("corridor", "sur le corridor d'approvisionnement Reykjavik-Édimbourg",
     "sur le corridor d'approvisionnement Halifax–Saint-Jean de Terre-Neuve", 1),
    ("hub", "vers un hub secondaire en Écosse-Nord",
     "vers un hub secondaire du Labrador", 1),
]
INTERDITS = ["Dublin", "Lisbonne", "Irlande", "marocaines", "Édimbourg", "Écosse"]


def frontmatter(texte):
    m = re.match(r"^---\s*\n(.*?)\n---", texte, re.DOTALL)
    if not m:
        raise ValueError("frontmatter introuvable")
    return yaml.safe_load(m.group(1))


def traiter(path, plan, erreurs):
    print(f"== {path.relative_to(VAULT)}")
    src = path.read_text(encoding="utf-8")
    txt = src
    for label, old, new, attendu in plan:
        if new in txt and old not in txt:
            print(f"  · {label} : déjà appliqué")
            continue
        n = txt.count(old)
        if n != attendu:
            print(f"  ✗ {label} : {n} occurrence(s), attendu {attendu}")
            erreurs.append(label)
            continue
        txt = txt.replace(old, new)
        print(f"  ✓ {label} ({n}×)")
    try:
        frontmatter(txt)
    except Exception as e:
        print(f"  ✗ frontmatter invalide après modification : {e}")
        erreurs.append("yaml")
    restes = [t for t in INTERDITS if t in txt]
    print(f"  {'✓' if not restes else '⚠'} termes restants : {', '.join(restes) or 'aucun'}")
    return src, txt


def main():
    execute = "--execute" in sys.argv
    print(f"Mode : {'ÉCRITURE' if execute else 'APERÇU (rien écrit)'}\n")
    erreurs = []
    articles = list((VAULT / "articles").rglob(ARTICLE_NOM))
    if len(articles) != 1:
        print(f"  ✗ article {ARTICLE_NOM} : {len(articles)} fichier(s) trouvé(s), attendu 1")
        sys.exit(1)
    if not FICHE.exists():
        print(f"  ✗ fiche introuvable : {FICHE}")
        sys.exit(1)
    resultats = [(FICHE, *traiter(FICHE, PLAN_FICHE, erreurs)),
                 (articles[0], *traiter(articles[0], PLAN_ARTICLE, erreurs))]
    if erreurs:
        print(f"\n{len(erreurs)} anomalie(s) — rien écrit. Envoie cette sortie à Claude.")
        sys.exit(1)
    a_ecrire = [(p, t) for p, s, t in resultats if s != t]
    if not a_ecrire:
        print("\nRien à faire : déjà aligné.")
        return
    if not execute:
        print(f"\n{len(a_ecrire)} fichier(s) prêts. Relance avec --execute pour écrire.")
        return
    for p, t in a_ecrire:
        shutil.copy2(p, p.with_suffix(".md.bak"))
        p.write_text(t, encoding="utf-8")
        print(f"  écrit : {p.relative_to(VAULT)} (+ .bak)")


if __name__ == "__main__":
    main()
