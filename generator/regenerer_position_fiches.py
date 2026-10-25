#!/usr/bin/env python3
"""
regenerer_position_fiches.py -- S28 : la matrice d'influence est la seule
source des liens entre variables ; les fiches n'en gardent qu'une vue générée.

Pour chacune des 12 fiches de variables/ :
  1. retire de l'en-tête les listes `influences`, `influenced_by` et
     `bidirectional_links` (lues par loader.py mais jamais utilisées : il
     retombe sur une liste vide) ;
  2. remplace la section « ## 2. Position dans le système » par un tableau
     généré depuis influence_matrix.md : liens de poids ≥ --seuil (0,5 par
     défaut) sortants et entrants, avec poids et sens, plus les liens
     réciproques.
Rien d'autre n'est touché (états, coupling_intensity, sections 1 et 3 à 12).

Idempotent : relancer après toute retouche de la matrice. Aperçu par défaut ;
--apply écrit, avec une sauvegarde .bak_s28 par fiche modifiée.

Usage (depuis la racine du vault) :
  python3 generator/regenerer_position_fiches.py
  python3 generator/regenerer_position_fiches.py --apply
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
GEN = ICI if (ICI / "dynamique.py").exists() else ICI / "generator"
VAULT = GEN.parent
VARIABLES = VAULT / "variables"

RE_EDGE = re.compile(
    r"- source:\s*\[\[(\w+)\]\]\s+target:\s*\[\[(\w+)\]\]\s+weight:\s*([\d.]+)\s+polarity:\s*(-?1)")
CLES_RETIREES = ("influences", "influenced_by", "bidirectional_links")
MARQUEUR = "*Section générée depuis [[influence_matrix]]"


def trouver_matrice():
    for p in sorted(VAULT.rglob("influence_matrix.md")):
        if "_a_supprimer" not in p.parts and ".bak" not in p.name:
            return p
    sys.exit("✗ influence_matrix.md introuvable.")


def lire_aretes(chemin):
    fm = chemin.read_text(encoding="utf-8").split("\n---", 1)[0]
    return [(s, t, float(w), int(p)) for s, t, w, p in RE_EDGE.findall(fm)]


def retirer_listes(entete):
    """Retire chaque clé et ses lignes de liste (indentées), plus une ligne vide qui suit."""
    lignes = entete.split("\n")
    out, i, retirees = [], 0, []
    while i < len(lignes):
        m = re.match(r"^(\w+):\s*$", lignes[i])
        if m and m.group(1) in CLES_RETIREES:
            retirees.append(m.group(1))
            i += 1
            while i < len(lignes) and re.match(r"^\s+- ", lignes[i]):
                i += 1
            if i < len(lignes) and lignes[i].strip() == "":
                i += 1
            continue
        out.append(lignes[i])
        i += 1
    return "\n".join(out), retirees


def section2(v, aretes, seuil):
    sort = sorted([(t, w, p) for s, t, w, p in aretes if s == v and w >= seuil], key=lambda x: -x[1])
    entr = sorted([(s, w, p) for s, t, w, p in aretes if t == v and w >= seuil], key=lambda x: -x[1])
    reciproques = sorted({t for t, _, _ in sort} & {s for s, _, _ in entr})
    sens = lambda p: "aggrave (+)" if p > 0 else "amortit (−)"
    L = ["## 2. Position dans le système", "",
         f"{MARQUEUR} (liens de poids ≥ {seuil:g}) : ne pas éditer à la main, relancer "
         "`generator/regenerer_position_fiches.py`. Détail complet et liens faibles dans la matrice.*", "",
         "**Influence** (cette variable → cible)", ""]
    if sort:
        L += ["| Cible | Poids | Sens |", "|---|---|---|"]
        L += [f"| [[{t}]] | {w:.2f} | {sens(p)} |" for t, w, p in sort]
    else:
        L.append("Aucun lien sortant fort.")
    L += ["", "**Influencé par** (source → cette variable)", ""]
    if entr:
        L += ["| Source | Poids | Sens |", "|---|---|---|"]
        L += [f"| [[{s}]] | {w:.2f} | {sens(p)} |" for s, w, p in entr]
    else:
        L.append("Aucun lien entrant fort.")
    L += ["", "**Liens réciproques** (forts dans les deux sens) : "
          + (", ".join(f"[[{x}]]" for x in reciproques) if reciproques else "aucun"), ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Régénère la section 2 des fiches depuis la matrice")
    ap.add_argument("--apply", action="store_true", help="écrire (sinon aperçu)")
    ap.add_argument("--seuil", type=float, default=0.5, help="poids minimal affiché (défaut 0,5)")
    a = ap.parse_args()

    aretes = lire_aretes(trouver_matrice())
    if not aretes:
        sys.exit("✗ aucune arête lue dans la matrice : rien écrit.")
    variables = sorted({s for s, *_ in aretes} | {t for _, t, *_ in aretes})

    plan = []
    for v in variables:
        f = VARIABLES / f"{v}.md"
        if not f.exists():
            sys.exit(f"✗ fiche absente : {f.relative_to(VAULT)}. Rien écrit.")
        texte = f.read_text(encoding="utf-8")
        m = re.match(r"^(---\n.*?\n)(---\n)(.*)$", texte, re.DOTALL)
        if not m:
            sys.exit(f"✗ {f.name} : en-tête YAML introuvable. Rien écrit.")
        entete, sep, corps = m.groups()
        entete2, retirees = retirer_listes(entete)
        s = re.search(r"^## 2\. Position dans le système\n.*?(?=^## 3\.)", corps, re.DOTALL | re.MULTILINE)
        if not s:
            sys.exit(f"✗ {f.name} : section « ## 2. Position dans le système » suivie de « ## 3. » introuvable. Rien écrit.")
        corps2 = corps[:s.start()] + section2(v, aretes, a.seuil) + "\n" + corps[s.end():]
        nouveau = entete2 + sep + corps2
        n_s = len(re.findall(rf"^\| \[\[\w+\]\] \|", section2(v, aretes, a.seuil), re.M))
        plan.append((f, texte, nouveau, retirees, n_s))

    print(f"Seuil : poids ≥ {a.seuil:g}")
    for f, ancien, nouveau, retirees, n in plan:
        etat = "inchangée" if ancien == nouveau else "modifiée"
        print(f"  {f.stem:36} {etat:9}  clés retirées : {', '.join(retirees) or 'aucune'} ; "
              f"{n} liens forts dans la section 2")
    a_ecrire = [p for p in plan if p[1] != p[2]]
    if not a.apply:
        print(f"\nAPERÇU : {len(a_ecrire)} fiche(s) à modifier, rien écrit. Relancer avec --apply.")
        return
    for f, ancien, nouveau, _, _ in a_ecrire:
        shutil.copy2(f, f.with_name(f.name + ".bak_s28"))
        f.write_text(nouveau, encoding="utf-8")
    print(f"\n✓ {len(a_ecrire)} fiche(s) écrite(s) (sauvegardes .bak_s28).")


if __name__ == "__main__":
    main()
