#!/usr/bin/env python3
"""
patch_titres_capitales.py — Ourrassol 2098 (chantier 5, 5 octobre 2026)

Titres écrits entièrement en capitales par le LLM (14 articles au 5 oct, toutes
thématiques) : à l'export du site, export_revues.py les remet en casse française.
Chaque mot reprend la casse qu'il a au milieu d'une phrase du corps de l'article
(noms propres, sigles) ; les autres passent en minuscules. Les articles du vault
ne sont pas modifiés.

Usage (depuis la racine du vault) :
    python3 generator/patch_titres_capitales.py           # aperçu + tests
    python3 generator/patch_titres_capitales.py --apply   # écrit (.bak_capitales)
"""
import argparse
import re
import shutil
from collections import Counter
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "export_revues.py"
MARQUEUR = "def normaliser_capitales("
ANCRE_FONCTION = 'def nettoyer_corps(corps, titre_fm=""):\n'
ANCRE_APPEL = '        a["titre"], a["blocs"] = nettoyer_corps(a["corps"], "")\n'
NOUVEL_APPEL = ANCRE_APPEL + '        a["titre"] = normaliser_capitales(a["titre"], "\\n".join(a["blocs"]))\n'

FONCTION = """def normaliser_capitales(titre, corps_sans_titre):
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
    def forme(mot):
        c = formes.get(mot.lower())
        if not c:
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
    ("CONVOIS FANTÔMES : LES COURTIERS DE L'OMBRE DES VENELLES",
     "**SAMARKAND —** Pour les convoyeurs indépendants des Venelles, ce message est banal. Les courtiers de l'ombre monnayent leurs convois fantômes.",
     "Convois fantômes : les courtiers de l'ombre des Venelles"),
    ("L'ACRA SOUS PRESSION : L'AUDIT ALGORITHMIQUE OUVERT",
     "Selon l'ACRA, l'audit algorithmique ouvert inquiète. La pression monte.",
     "L'ACRA sous pression : l'audit algorithmique ouvert"),
    ("LE CIEL EN FEU : SEUIL DES 52°C FRANCHI EN OCCITANIE",
     "Le seuil a été franchi en Occitanie, à 52°C.",
     "Le ciel en feu : seuil des 52°C franchi en Occitanie"),
    ("Kontinuum : le silence qui gouverne", "texte", "Kontinuum : le silence qui gouverne"),
]


def patcher(src):
    if MARQUEUR in src:
        raise SystemExit("Patch déjà appliqué -- rien à faire.")
    for nom, ancre in (("nettoyer_corps", ANCRE_FONCTION), ("appel", ANCRE_APPEL)):
        if src.count(ancre) != 1:
            raise SystemExit(f"Ancre « {nom} » introuvable ou multiple -- patch non appliqué.")
    src = src.replace(ANCRE_FONCTION, FONCTION + ANCRE_FONCTION, 1).replace(ANCRE_APPEL, NOUVEL_APPEL, 1)
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
        print(f"\nAperçu OK : {cible.name} serait patché. Relancer avec --apply.")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_capitales"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"\nPatch appliqué à {cible} (sauvegarde : {cible.name}.bak_capitales).")


if __name__ == "__main__":
    main()
