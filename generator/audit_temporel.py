"""
audit_temporel.py -- S23, 4 octobre 2026. Lecture seule, sans LLM.

Cherche dans le texte des articles les années ANTÉRIEURES à l'année de
publication de l'article (2098) employées comme un futur -- erreur
signalée le 3 octobre : effondrement amazonien prévu « d'ici 2070 » dans
un article daté de 2098.

Deux familles de motifs :
  A. formule de futur devant l'année : « d'ici (à) 2070 », « à l'horizon
     2080 », « prévu(e)(s) pour/en/d'ici 2090 », « attendu(e)(s) en … »,
     « dès 20xx » n'est PAS retenu (souvent passé) ;
  B. année suivie dans la même phrase (60 caractères) d'un verbe au futur
     ou au conditionnel (sera, seront, devra, devrait, pourrait, aura,
     va/vont + infinitif…).
La famille B produit des faux positifs (citation d'une ancienne
prévision, discours rapporté) : le rapport est à relire, rien n'est
corrigé.

Usage (depuis generator/) :
  python3 audit_temporel.py                 # résumé + passages
  python3 audit_temporel.py --scenario X
Rapport : state/audit_temporel.md
"""
import argparse
import glob
import os
import re

import yaml

ICI = os.path.dirname(os.path.abspath(__file__))
RAPPORT = os.path.join(ICI, "state", "audit_temporel.md")

ANNEE = r"(20[2-9]\d)"
MOTIF_A = re.compile(
    r"(?i)\b(d['’]ici (?:à )?(?:l['’]an )?|à l['’]horizon (?:de )?|horizon |"
    r"prévue?s? (?:pour|en|d['’]ici|à l['’]horizon) |attendue?s? (?:pour|en) |"
    r"programmée?s? (?:pour|en) |planifiée?s? (?:pour|en) )" + ANNEE + r"\b")
FUTUR = (r"(?:sera|seront|serait|seraient|devra|devront|devrait|devraient|pourra|"
         r"pourront|pourrait|pourraient|aura|auront|aurait|auraient|ira|iront|"
         r"va\s+\w+er|vont\s+\w+er|deviendra|deviendront|atteindra|atteindront|"
         r"disparaîtra|disparaîtront)")
MOTIF_B = re.compile(r"\b" + ANNEE + r"\b([^.!?\n]{0,60}?)\b" + FUTUR + r"\b")


def annee_pub(fm, nom):
    for v in (fm.get("date_publication"), fm.get("date_evenement")):
        m = re.search(r"(20\d\d)", str(v or ""))
        if m:
            return int(m.group(1))
    m = re.search(r"(20\d\d)\.md$", nom)
    return int(m.group(1)) if m else 2098


def contexte(texte, debut, fin, marge=70):
    a, b = max(0, debut - marge), min(len(texte), fin + marge)
    return ("…" if a else "") + texte[a:b].replace("\n", " ").strip() + ("…" if b < len(texte) else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario")
    args = ap.parse_args()

    trouves = []
    n_art = 0
    for f in sorted(glob.glob(os.path.join(ICI, "..", "articles", "*", "*.md"))):
        nom = os.path.basename(f)
        if nom.startswith("_") or ".bak" in nom:
            continue
        sc = os.path.basename(os.path.dirname(f))
        if args.scenario and sc != args.scenario:
            continue
        t = open(f, encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
        fm = (yaml.safe_load(m.group(1)) or {}) if m else {}
        corps = t[m.end():] if m else t
        # Bloc de métadonnées éventuellement resté dans le corps : ignoré
        corps = corps.split("===METADONNEES_PUBLICATION===")[0]
        n_art += 1
        an = annee_pub(fm, nom)
        vus = set()
        for famille, motif, groupe in (("A", MOTIF_A, 2), ("B", MOTIF_B, 1)):
            for mm in motif.finditer(corps):
                y = int(mm.group(groupe))
                if y >= an or (mm.start(), famille) in vus:
                    continue
                if any(abs(mm.start() - s) < 40 for s, _ in vus):
                    continue  # même passage déjà relevé par l'autre famille
                vus.add((mm.start(), famille))
                trouves.append((sc, nom, an, y, famille, contexte(corps, mm.start(), mm.end())))

    par_fam = {"A": sum(1 for x in trouves if x[4] == "A"), "B": sum(1 for x in trouves if x[4] == "B")}
    articles_touches = len({(x[0], x[1]) for x in trouves})
    lignes = ["# Audit temporel — années passées employées au futur", "",
              "{} articles lus · {} passage(s) dans {} article(s) · "
              "A (formule de futur) : {} · B (verbe au futur) : {}".format(
                  n_art, len(trouves), articles_touches, par_fam["A"], par_fam["B"]), ""]
    for sc, nom, an, y, fam, ctx in trouves:
        lignes.append("- **[{}]** {} · {} (publié {}, année citée {})  \n  {}".format(
            fam, sc, nom[:60], an, y, ctx))
    os.makedirs(os.path.dirname(RAPPORT), exist_ok=True)
    open(RAPPORT, "w", encoding="utf-8").write("\n".join(lignes) + "\n")
    print("\n".join(lignes[:3]))
    print("Rapport : {}".format(RAPPORT))


if __name__ == "__main__":
    main()
