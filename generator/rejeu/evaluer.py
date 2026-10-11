"""Compare les sorties du rejeu à reference.json. Usage : python3 evaluer.py [sorties_dir]"""
import json, sys
from pathlib import Path
ref = json.load(open(Path(__file__).parent / "reference.json"))
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "sorties"
def touches(bloc):
    return ({t["instance"] for t in bloc["trajectoires"]} | {r["a"] for r in bloc["relations"]}
            | {r["b"] for r in bloc["relations"]} | {t["slug"] for t in bloc["textes"]})
ok = total = 0
ok_i = total_i = 0   # priorités : indicatif (classement IA, variable d'un passage à l'autre)
for hid, attentes in ref.items():
    f = out / f"{hid}.json"
    if not f.exists():
        print(f"{hid} : pas de sortie"); continue
    r = json.loads(f.read_text())
    ob, po = touches(r["obligatoire"]), touches(r["possible"])
    prio = {c["slug"] for c in r.get("classement") or []}
    disparus = {x["instance"] for x in r["obligatoire"]["trajectoires"] if x.get("apres") == "disparu"}
    tests = {"obligatoire": lambda s: s in ob, "pas_obligatoire": lambda s: s not in ob,
             "pas_disparu": lambda s: s not in disparus,
             "vu": lambda s: s in ob or s in po, "priorite": lambda s: s in prio,
             "pas_priorite": lambda s: s not in prio}
    ratés = []
    for cle, slugs in attentes.items():
        if cle in ("priorite", "pas_priorite") and r.get("classement_source") != "ia":
            continue
        indicatif = cle in ("priorite", "pas_priorite")
        for sl in slugs:
            bon = tests[cle](sl)
            if indicatif:
                total_i += 1; ok_i += bon
                if not bon: ratés.append(f"(indicatif) {cle} : {sl}")
            else:
                total += 1; ok += bon
                if not bon: ratés.append(f"{cle} : {sl}")
    print(f"{hid} : " + ("conforme" if not ratés else "écarts → " + " ; ".join(ratés)))
print(f"VERDICTS : {ok}/{total} conformes — PRIORITÉS (indicatif) : {ok_i}/{total_i}")
