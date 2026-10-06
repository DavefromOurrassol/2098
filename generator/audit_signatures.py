"""
audit_signatures.py -- S23, 3 octobre 2026.
Classe les articles dont journaliste_slug est vide ou absent de la
rédaction de leur zone (après remontée N1, comme le pipeline).
À lancer depuis generator/ : python3 audit_signatures.py
"""
import collections
import functools
import glob
import re
import unicodedata

import yaml

import prompt_builder as pb

# _load_geographie() reparse geographie/{scenario}.md à chaque appel :
# cache local pour la boucle (aucun effet sur le pipeline).
pb._load_geographie = functools.lru_cache(None)(pb._load_geographie)

J = yaml.safe_load(open("journaux.yaml", encoding="utf-8"))


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


stats = collections.Counter()
ex = collections.defaultdict(list)
par_mois = collections.defaultdict(collections.Counter)
mois_tous = collections.Counter()
mois_ok = collections.Counter()
jours_aout = collections.defaultdict(collections.Counter)

for f in sorted(glob.glob("../articles/*/*.md")):
    t = open(f, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    if not m:
        continue
    fm = yaml.safe_load(m.group(1)) or {}
    sc = f.split("/")[2]
    li = fm.get("ligne_editoriale") or "pro_pouvoir"
    z = fm.get("zone_principale") or ""
    js = fm.get("journaliste_slug") or ""
    n1 = pb._resoudre_zone_n1(z, sc) if z else ""
    zd = (J.get(sc, {}).get(li, {}).get("zones") or {}).get(n1)
    personnes = ((zd or {}).get("journalistes") or []) + ((zd or {}).get("orateurs") or [])
    noms = {slug(p.get("nom", "")) for p in personnes}
    if js and js in noms:
        continue
    cle = ("N1 trouvée" if zd else "N1 absente") + " / " + ("slug vide" if not js else "slug inconnu")
    stats[cle] += 1
    ex[cle].append("{} {} {} -> {} [{}]".format(sc, li, z, n1, js))
    dg = str(fm.get("date_generation", ""))
    mois = dg[:7] or "?"
    par_mois[cle][mois] += 1
    if mois == "2026-08":
        jours_aout[cle][dg[8:10]] += 1
    if zd:
        mois_ok[mois] += 0  # garde le mois visible

# Articles BIEN signés, par mois (pour comparer)
for f in sorted(glob.glob("../articles/*/*.md")):
    t = open(f, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    if m:
        fm = yaml.safe_load(m.group(1)) or {}
        mois_tous[str(fm.get("date_generation", ""))[:7] or "?"] += 1

for k, v in stats.most_common():
    print(v, "|", k)
    for e in ex[k][:5]:
        print("    ", e)
print("TOTAL", sum(stats.values()))
print()
print("Par mois de génération (problèmes / tous articles) :")
for mois in sorted(mois_tous):
    pb_m = sum(par_mois[k][mois] for k in par_mois)
    detail = ", ".join("{} {}".format(par_mois[k][mois], k) for k in par_mois if par_mois[k][mois])
    print("  {} : {} / {}   ({})".format(mois, pb_m, mois_tous[mois], detail))
print()
print("Août, par jour (problèmes) :")
for k in jours_aout:
    print("  {} : {}".format(k, ", ".join(
        "{}:{}".format(j, n) for j, n in sorted(jours_aout[k].items()))))
