"""
rejouer.py — rejoue la passe exhaustive sur l'export, SANS appel IA (S27, 11 octobre 2026).

Usage (depuis la racine du vault) :
    python3 generator/rejeu/rejouer.py               # écrit generator/rejeu/sorties/*.md et *.json
    python3 generator/rejeu/evaluer.py               # compare à reference.json

Les modules loader.py et llm_client.py de ce dossier remplacent ceux du générateur :
les fiches viennent de generator/state/export_et_si.json, et tout appel IA est refusé
(compté dans « appels manquants » : il faut alors relancer la passe pour de vrai).
"""
import json, os, sys
from pathlib import Path
KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT.parent))   # générateur : simuler_et_si, et_si_exhaustif…
sys.path.insert(0, str(KIT))          # ce dossier d'abord : loader et llm_client de rejeu
import loader, llm_client, simuler_et_si as s, et_si_exhaustif as es
D = loader._D
cache_path = KIT / "cache_rejeu.json"
cache_path.write_text(json.dumps(D["cache"], ensure_ascii=False))
es.CACHE = cache_path                  # le vrai cache n'est jamais touché
out = Path(sys.argv[1]) if len(sys.argv) > 1 else KIT / "sorties"
out.mkdir(exist_ok=True)
for c in D["couples"]:
    sc = c["scenario"]
    class Repo:
        def load_all_zones(self, _sc, _z=c["zones"]): return _z
    s.charger_zone_repository = lambda: (Repo(), None)
    llm_client.APPELS.clear()
    res = es.passe_exhaustive(c["hyp"], sc, c["effets"], c["lecture"])
    (out / f"{c['hyp']['id']}.md").write_text("\n".join(es.rendre(res)), encoding="utf-8")
    (out / f"{c['hyp']['id']}.json").write_text(json.dumps(res, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"{c['hyp']['id']:28s} {sc:18s} lots en cache {res['depuis_cache']}/{res['lots']}  "
          f"appels manquants {len(llm_client.APPELS)}  obligatoires {len(es._slugs_touches(res['obligatoire']))}  "
          f"possibles {len(es._slugs_touches(res['possible']))}  classement {res.get('classement_source')}")
