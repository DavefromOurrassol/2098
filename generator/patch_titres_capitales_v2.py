#!/usr/bin/env python3
"""
patch_titres_capitales_v2.py — Ourrassol 2098 (chantier 5, 5 octobre 2026)

Met à jour normaliser_capitales() dans export_revues.py (installée par
patch_titres_capitales.py) : un mot jamais vu au milieu d'une phrase mais
toujours écrit avec une majuscule dans le corps garde sa majuscule (cas
« Occitanie », seulement présent en début de phrase ou en ligne de lieu).
Mots courts et mots-outils exclus de cette règle (« Quand », « Les »…).

Usage (depuis la racine du vault) :
    python3 generator/patch_titres_capitales_v2.py           # aperçu + tests
    python3 generator/patch_titres_capitales_v2.py --apply   # écrit (.bak_capitales2)
"""
import argparse
import re
import shutil
from collections import Counter
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "export_revues.py"
DEBUT = "def normaliser_capitales("
FIN = 'def nettoyer_corps(corps, titre_fm=""):\n'
FONCTION = """MOTS_OUTILS = {"quand", "dans", "pour", "avec", "sans", "sous", "mais", "plus", "vers", "chez",
               "entre", "contre", "comme", "après", "avant", "depuis", "pendant", "leur", "leurs",
               "cette", "notre", "votre", "nous", "vous", "elles", "tous", "toutes", "tout", "aussi",
               "encore", "alors", "ainsi", "face", "lorsque", "parce", "dont", "même"}


def normaliser_capitales(titre, corps_sans_titre):
    \"\"\"Titre écrit presque entièrement en capitales -> casse française (chantier 5,
    5 octobre 2026). Chaque mot reprend la casse qu'il a AU MILIEU d'une phrase du
    corps de l'article (noms propres, sigles : « Venelles », « ACRA ») ; un mot
    jamais vu ainsi passe en minuscules. Première lettre du titre en majuscule.
    Un titre déjà en casse normale est rendu tel quel.\"\"\"
    lettres = [c for c in titre if c.isalpha()]
    if len(lettres) < 4 or sum(c.isupper() for c in lettres) / len(lettres) <= 0.8:
        return titre
    formes = {}
    for m in re.finditer(r"[^\\W\\d_]+", corps_sans_titre):
        avant = corps_sans_titre[:m.start()].rstrip(" \\t*_")
        if not avant or not (avant[-1].isalnum() or avant[-1] in ",;(’'-"):
            continue  # début de ligne ou de phrase : casse non significative
        formes.setdefault(m.group().lower(), Counter())[m.group()] += 1
    partout = {}  # toutes les apparitions, hors capitales, même en début de phrase
    for m in re.finditer(r"[^\\W\\d_]+", corps_sans_titre):
        if not m.group().isupper():
            partout.setdefault(m.group().lower(), set()).add(m.group())
    def forme(mot):
        c = formes.get(mot.lower())
        if not c:
            vues = partout.get(mot.lower())
            if (vues and len(mot) > 3 and mot.lower() not in MOTS_OUTILS
                    and all(v[0].isupper() for v in vues)):
                return sorted(vues)[0]  # jamais en minuscules dans le texte : nom propre
            return mot.lower()
        meilleures = c.most_common()
        top = meilleures[0][1]
        candidates = [f for f, n in meilleures if n == top]
        return next((f for f in candidates if not f.isupper()), candidates[0])
    def remplacer(m):
        if m.start() and (titre[m.start() - 1].isdigit() or titre[m.start() - 1] == "°"):
            return m.group()  # unité collée à un nombre (52°C, 3D) : inchangée
        return forme(m.group())
    t = re.sub(r"[^\\W\\d_]+", remplacer, titre)
    for i, ch in enumerate(t):  # première lettre en majuscule
        if ch.isalpha():
            return t[:i] + ch.upper() + t[i + 1:]
    return t


"""

CAS = [
    ("LE CIEL EN FEU : SEUIL DES 52°C FRANCHI EN OCCITANIE",
     "**OCCITANIE —** La chaleur frappe. Occitanie-Sud suffoque.",
     "Le ciel en feu : seuil des 52°C franchi en Occitanie"),
    ("QUAND LES ALGORITHMES APPRENNENT", "Quand il pleut, rien. Les algorithmes apprennent.",
     "Quand les algorithmes apprennent"),
    ("CONVOIS FANTÔMES : LES COURTIERS DE L'OMBRE DES VENELLES",
     "**SAMARKAND —** Pour les convoyeurs des Venelles, banal. Les courtiers de l'ombre.",
     "Convois fantômes : les courtiers de l'ombre des Venelles"),
    ("L'ACRA SOUS PRESSION", "Selon l'ACRA, la pression monte.", "L'ACRA sous pression"),
    ("Kontinuum : le silence qui gouverne", "x", "Kontinuum : le silence qui gouverne"),
]


def patcher(src):
    if "MOTS_OUTILS = {" in src:
        raise SystemExit("Version 2 déjà appliquée -- rien à faire.")
    if src.count(DEBUT) != 1 or src.count(FIN) != 1:
        raise SystemExit("normaliser_capitales() absente : appliquer d'abord patch_titres_capitales.py.")
    d, f = src.index(DEBUT), src.index(FIN)
    if not d < f:
        raise SystemExit("Ordre inattendu des fonctions -- patch non appliqué.")
    src = src[:d] + FONCTION + src[f:]
    compile(src, str(CIBLE), "exec")
    return src


def tester():
    ns = {"re": re, "Counter": Counter}
    exec(compile(FONCTION, "fonction", "exec"), ns)
    ok = True
    for titre, corps, attendu in CAS:
        res = ns["normaliser_capitales"](titre, corps)
        ok &= res == attendu
        print(f"  {'✓' if res == attendu else '✗'} {titre[:55]!r:58} -> {res!r}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--cible", default=str(CIBLE), help=argparse.SUPPRESS)
    args = ap.parse_args()
    cible = Path(args.cible)
    nouveau = patcher(cible.read_text(encoding="utf-8"))
    print("Tests :")
    if not tester():
        raise SystemExit("Un test échoue -- patch non appliqué.")
    if not args.apply:
        print(f"\nAperçu OK : {cible.name} serait mis à jour. Relancer avec --apply.")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_capitales2"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"\nVersion 2 appliquée à {cible} (sauvegarde : {cible.name}.bak_capitales2).")


if __name__ == "__main__":
    main()
