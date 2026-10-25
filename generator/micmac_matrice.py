#!/usr/bin/env python3
"""
micmac_matrice.py -- S28.1 : analyse structurelle (MICMAC) de la matrice
d'influence, telle que le moteur dynamique.py la vit.

LECTURE SEULE : n'écrit rien dans le vault, aucun appel IA.

Coefficient d'un lien source -> cible, identique à dynamique.couplages() :
    |weight × polarity × temporal_weight × CRITICITE[systemic_criticality(source)]|
  (valeur absolue : un amortisseur à −1 est une influence comme une autre)
(la table CRITICITE est importée de dynamique.py ; repli sur une copie si absent).

Pour chaque variable :
  - influence directe  = somme de sa ligne (ce qu'elle pousse sur les autres) ;
  - dépendance directe = somme de sa colonne (ce qu'elle reçoit) ;
  - indirectes : mêmes sommes sur la matrice élevée à la puissance --puissance
    (effets en plusieurs sauts ; les retards et l'amortissement du moteur sont
    ignorés : on mesure qui domine à long terme, pas la vitesse) ;
  - classe : motrice (influence ≥ moyenne, dépendance < moyenne), relais (les
    deux ≥ moyenne), dépendante, autonome.
Une variable dont la classe ou le rang change entre direct et indirect est
signalée (« levier caché »).

Diagnostic de la matrice : paires symétriques (A→B = B→A en poids), liens
négatifs (amortisseurs), variables sans criticité.

Quand le lancer : après toute retouche de influence_matrix.md ou d'une
systemic_criticality ; avant une hypothèse « et si ? » ou une grosse injection,
pour savoir si la variable visée diffuse le choc ou l'absorbe.

Usage (depuis la racine du vault ou depuis generator/) :
  python3 generator/micmac_matrice.py
  python3 generator/micmac_matrice.py --sans-criticite   # poids de la matrice seuls
  python3 generator/micmac_matrice.py --puissance 8
"""
import argparse
import re
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
GEN = ICI if (ICI / "dynamique.py").exists() else ICI / "generator"
VAULT = GEN.parent

try:
    sys.path.insert(0, str(GEN))
    from dynamique import CRITICITE, CRITICITE_DEFAUT
except Exception:
    CRITICITE = {1: 0.7, 2: 0.85, 3: 1.0, 4: 1.3, 5: 1.6}
    CRITICITE_DEFAUT = 1.0

RE_EDGE = re.compile(
    r"- source:\s*\[\[(\w+)\]\]\s+target:\s*\[\[(\w+)\]\]\s+weight:\s*([\d.]+)\s+"
    r"polarity:\s*(-?1)\s+lag:\s*[\d.]+\s+nonlinearity:\s*\w+\s+temporal_weight:\s*([\d.]+)")


def trouver_matrice():
    for p in sorted(VAULT.rglob("influence_matrix.md")):
        if "_a_supprimer" not in p.parts and ".bak" not in p.name:
            return p
    sys.exit("✗ influence_matrix.md introuvable.")


def lire_aretes(chemin):
    texte = chemin.read_text(encoding="utf-8")
    fm = texte.split("\n---", 1)[0]          # frontmatter seul : les tableaux du corps sont ignorés
    aretes = [(s, t, float(w), int(p), float(tw)) for s, t, w, p, tw in RE_EDGE.findall(fm)]
    if not aretes:
        sys.exit(f"✗ aucune arête lue dans {chemin} : format inattendu.")
    return aretes


def lire_criticites(variables):
    crit = {}
    for v in variables:
        f = VAULT / "variables" / f"{v}.md"
        val = None
        if f.exists():
            m = re.search(r"^\s*systemic_criticality:\s*(\d+)", f.read_text(encoding="utf-8"), re.M)
            val = int(m.group(1)) if m else None
        crit[v] = val
    return crit


def mat_mul(a, b):
    n = len(a)
    return [[sum(a[i][k] * b[k][j] for k in range(n)) for j in range(n)] for i in range(n)]


def puissance(m, k):
    r = m
    for _ in range(k - 1):
        r = mat_mul(r, m)
    return r


def sommes(m):
    n = len(m)
    return [sum(m[i]) for i in range(n)], [sum(m[i][j] for i in range(n)) for j in range(n)]


def classes(inf, dep):
    mi, md = sum(inf) / len(inf), sum(dep) / len(dep)
    out = []
    for a, b in zip(inf, dep):
        if a >= mi:
            out.append("relais" if b >= md else "motrice")
        else:
            out.append("dépendante" if b >= md else "autonome")
    return out


def rangs(valeurs):
    ordre = sorted(range(len(valeurs)), key=lambda i: -valeurs[i])
    r = [0] * len(valeurs)
    for pos, i in enumerate(ordre, 1):
        r[i] = pos
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--sans-criticite", action="store_true",
                    help="ignorer systemic_criticality (poids de la matrice seuls)")
    ap.add_argument("--puissance", type=int, default=6,
                    help="nombre de sauts pour l'indirect (défaut 6)")
    a = ap.parse_args()

    chemin = trouver_matrice()
    aretes = lire_aretes(chemin)
    variables = sorted({s for s, *_ in aretes} | {t for _, t, *_ in aretes})
    ix = {v: i for i, v in enumerate(variables)}
    n = len(variables)
    crit = lire_criticites(variables)

    m = [[0.0] * n for _ in range(n)]
    poids = {}
    for s, t, w, p, tw in aretes:
        if s == t:
            continue
        mult = 1.0 if a.sans_criticite else CRITICITE.get(crit[s], CRITICITE_DEFAUT)
        m[ix[s]][ix[t]] = abs(w * p * tw * mult)   # MICMAC compte la force du lien, pas son sens
        poids[(s, t)] = w

    # ── Diagnostic de la matrice
    paires = [(s, t) for (s, t) in poids if s < t and (t, s) in poids]
    sym = [pr for pr in paires if poids[pr] == poids[(pr[1], pr[0])]]
    negatifs = [(s, t) for s, t, w, p, tw in aretes if p < 0]
    sans_crit = [v for v in variables if crit[v] is None]
    print(f"Matrice : {chemin.relative_to(VAULT)} — {len(aretes)} arêtes, {n} variables")
    print(f"  paires symétriques en poids : {len(sym)} / {len(paires)}"
          + ("  ⚠ quasi symétrique : influence ≈ dépendance pour chaque variable,"
             "\n    seules la criticité et les liens négatifs créent des leviers" if paires and len(sym) / len(paires) > 0.8 else ""))
    print(f"  liens négatifs (amortisseurs) : {len(negatifs)}"
          + "".join(f"\n    {s} → {t}" for s, t in negatifs))
    if a.sans_criticite:
        print("  criticité : ignorée (--sans-criticite)")
    else:
        print("  criticité : " + (f"⚠ absente pour {', '.join(sans_crit)} (multiplicateur {CRITICITE_DEFAUT})"
                                  if sans_crit else "lue pour les 12 variables"))
    print()

    # ── MICMAC direct et indirect
    i1, d1 = sommes(m)
    ik, dk = sommes(puissance(m, a.puissance))
    tot_i, tot_d = sum(i1), sum(d1)
    ik = [x / sum(ik) * tot_i for x in ik] if sum(ik) else ik   # ramené à l'échelle directe
    dk = [x / sum(dk) * tot_d for x in dk] if sum(dk) else dk
    c1, ck = classes(i1, d1), classes(ik, dk)
    r1, rk = rangs(i1), rangs(ik)

    print(f"{'variable':36} {'crit':>4} {'infl':>6} {'dép':>6} {'écart':>6}  {'rang':>7}  classe directe → indirecte")
    for j in sorted(range(n), key=lambda j: -i1[j]):
        v = variables[j]
        cr = "—" if a.sans_criticite or crit[v] is None else str(crit[v])
        flag = "  ← levier caché" if c1[j] != ck[j] or abs(r1[j] - rk[j]) >= 2 else ""
        print(f"{v:36} {cr:>4} {i1[j]:6.2f} {d1[j]:6.2f} {i1[j] - d1[j]:+6.2f}  "
              f"{r1[j]:>2} → {rk[j]:<2}  {c1[j]:10} → {ck[j]}{flag}")
    print(f"\nMoyennes : influence {tot_i / n:.2f}, dépendance {tot_d / n:.2f}. "
          f"Indirect = matrice à la puissance {a.puissance} (retards et amortissement ignorés).")
    for nom in ("motrice", "dépendante"):
        liste = [variables[j] for j in range(n) if ck[j] == nom]
        print(f"{nom.capitalize()}s (indirect) : {', '.join(liste) if liste else 'aucune'}")


if __name__ == "__main__":
    main()
