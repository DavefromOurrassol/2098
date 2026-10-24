#!/usr/bin/env python3
"""
patch_s27_sauter_avant_injection.py — 24 octobre 2026 (S27, point 5).

L'entrée d'injection d'une hypothèse adoptée reprend TOUTE la lecture IA : sauter
une proposition à l'étape ④ (après l'injection) ne la retire pas des faits
imposés ni des acteurs donnés à l'IA de l'injection (cas pacte_tabriz_2058 :
« Ormuz disparaît », milices du Congo… retirés à la main par
et_si_retirer_faits.py). Le tri se fait désormais AVANT l'injection :

  et_si_injecter.py
    --plan            liste numérotée de l'étape ④ (mêmes numéros), sans IA
    --sauter 3,4,9    retire de l'entrée passée à l'injection les faits imposés et
                      les acteurs des opérations sautées (trajectoire, disparition,
                      zone) ; à l'injection réelle, les numéros sont gardés dans
                      generator/state/et_si_application/<id>.sauter.json
  appliquer_et_si.py
    sans --sauter : reprend les numéros gardés à l'étape ③ (affiché en tête).

Cibles : generator/et_si_injecter.py (.bak_s27_sauter), generator/appliquer_et_si.py
(.bak_s27_sauter). Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_sauter_avant_injection.py
"""

import shutil
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
MARQUEUR = "PATCH_S27_SAUTER"

AIDES_INJ = '''TIMEOUT = 900  # secondes : appels IA par scénario + cycle post-injection


def _plan(hid):
    """PATCH_S27_SAUTER : (data, ops) de la phase 4 — mêmes numéros qu'à l'étape ④."""
    import appliquer_et_si as ap
    src = ap.APP_DIR / f"{hid}.json"
    if not src.exists():
        sys.exit(f"✗ {src.name} absent : simuler l'hypothèse d'abord.")
    data = json.loads(src.read_text(encoding="utf-8"))
    ops, _ = ap.construire_plan(data)
    return data, ops


def _nombres(s):
    import re
    return {int(x) for x in re.findall(r"\\d+", s or "")}


def _ecartees(ops, sauter, inclure):
    """Numéros que l'étape ④ n'appliquera pas : « Sauter », plus les ⚠ non repris par « Inclure »."""
    return {o["n"] for o in ops if o["n"] in sauter
            or (o.get("alerte") and not str(o["alerte"]).startswith("déjà") and o["n"] not in inclure)}


def _retirer_sautees(entree, ops, ecartees):
    """Copie de l'entrée sans les faits imposés ni les acteurs des opérations écartées."""
    import copy
    slugs = {o.get("instance") or o.get("zone") for o in ops
             if o["n"] in ecartees and o["genre"] in ("trajectoire", "disparition", "zone")}
    slugs.discard(None)
    e = copy.deepcopy(entree)
    retires = []
    for sc, faits in (e.get("faits_imposes") or {}).items():
        garde = []
        for f in faits or []:
            if isinstance(f, dict) and f.get("slug") in slugs:
                retires.append(f"fait ({sc}) : {' '.join(str(f.get('fait')).split())[:100]}")
            else:
                garde.append(f)
        e["faits_imposes"][sc] = garde
    acteurs = e.get("acteurs_hint") or []
    retires += [f"acteur : {s}" for s in acteurs if s in slugs]
    e["acteurs_hint"] = [s for s in acteurs if s not in slugs]
    if "acteurs_hint_count" in e:
        e["acteurs_hint_count"] = len(e["acteurs_hint"])
    return e, retires'''

REMPL_INJ = [
    ("TIMEOUT = 900  # secondes : appels IA par scénario + cycle post-injection", AIDES_INJ),
    (
        '    ap.add_argument("--dry-run", action="store_true")\n    a = ap.parse_args()\n    hid = a.id.strip()\n',
        '    ap.add_argument("--dry-run", action="store_true")\n'
        '    ap.add_argument("--plan", action="store_true", help="liste numérotée de l\'étape ④, sans IA")   # PATCH_S27_SAUTER\n'
        '    ap.add_argument("--sauter", default="", help="numéros de l\'étape ④ à écarter dès l\'injection")\n'
        '    ap.add_argument("--inclure", default="", help="numéros ⚠ de l\'étape ④ à garder")\n'
        '    a = ap.parse_args()\n    hid = a.id.strip()\n'
        '    if a.plan:\n'
        '        _, ops = _plan(hid)\n'
        '        print(f"Liste de l\'étape ④ — {hid} (mêmes numéros ; « Sauter » ici retire aussi faits et acteurs "\n'
        '              "de l\'injection)\\n")\n'
        '        for o in ops:\n'
        '            al = f"  ⚠ {o[\'alerte\']}" if o.get("alerte") else ""\n'
        '            print(f"  {o[\'n\']:>3}. [{o[\'sc\']}] {o[\'texte\']}{al}")\n'
        '        return\n',
    ),
    (
        '    cmd = [sys.executable, str(GEN / "inject_custom_events.py"),\n'
        '           "--idea", json.dumps(entrees[0], ensure_ascii=False, default=str)]\n',
        '    entree, sauter, inclure = entrees[0], _nombres(a.sauter), _nombres(a.inclure)   # PATCH_S27_SAUTER\n'
        '    _, ops = _plan(hid)\n'
        '    ecartees = _ecartees(ops, sauter, inclure)\n'
        '    if ecartees:\n'
        '        entree, retires = _retirer_sautees(entree, ops, ecartees)\n'
        '        auto = sorted(ecartees - sauter)\n'
        '        print(f"Écartées à l\'étape ④ : {\', \'.join(map(str, sorted(ecartees)))}"\n'
        '              + (f" (dont ⚠ par défaut : {\', \'.join(map(str, auto))} ; « Inclure » pour les garder)" if auto else "")\n'
        '              + " — "\n'
        '              + (f"{len(retires)} élément(s) retiré(s) de l\'entrée" if retires else "rien à retirer de l\'entrée"))\n'
        '        for r_ in retires:\n'
        '            print(f"  − {r_}")\n'
        '        print()\n'
        '    cmd = [sys.executable, str(GEN / "inject_custom_events.py"),\n'
        '           "--idea", json.dumps(entree, ensure_ascii=False, default=str)]\n',
    ),
    (
        '    if ed._retirer_de_queue(hid):\n',
        '    if sauter or inclure:   # PATCH_S27_SAUTER : repris par défaut à l\'étape ④\n'
        '        import appliquer_et_si as ap_\n'
        '        (ap_.APP_DIR / f"{hid}.sauter.json").write_text(json.dumps(\n'
        '            {"sauter": sorted(sauter), "inclure": sorted(inclure)}, ensure_ascii=False), encoding="utf-8")\n'
        '        print(f"✓ « Sauter » / « Inclure » gardés pour l\'étape ④ : {sorted(sauter)} / {sorted(inclure)}")\n'
        '    if ed._retirer_de_queue(hid):\n',
    ),
]

REMPL_APP = [
    (
        '    sauter, inclure = nombres(a.sauter), nombres(a.inclure)\n',
        '    sauter, inclure = nombres(a.sauter), nombres(a.inclure)\n'
        '    f_sauts = APP_DIR / f"{a.id}.sauter.json"   # PATCH_S27_SAUTER : choix de l\'étape ③\n'
        '    if not sauter and not inclure and f_sauts.exists():\n'
        '        _s = json.loads(f_sauts.read_text(encoding="utf-8"))\n'
        '        sauter, inclure = set(_s.get("sauter") or []), set(_s.get("inclure") or [])\n'
        '        print(f"· repris de l\'étape ③ : Sauter {sorted(sauter)}, Inclure {sorted(inclure)}\\n")\n',
    ),
]


def patcher(cible, rempl):
    texte = cible.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        return None, f"{cible.name} : déjà patché"
    for i, (ancien, nouveau) in enumerate(rempl, 1):
        n = texte.count(ancien)
        if n != 1:
            return None, f"{cible.name} : remplacement {i}, {n} occurrence(s) au lieu d'une"
        texte = texte.replace(ancien, nouveau)
    try:
        compile(texte, str(cible), "exec")
    except SyntaxError as e:
        return None, f"{cible.name} ne compile pas ({e})"
    return texte, None


def main() -> int:
    cibles = [(GEN / "et_si_injecter.py", REMPL_INJ), (GEN / "appliquer_et_si.py", REMPL_APP)]
    prets = []
    for cible, rempl in cibles:
        if not cible.exists():
            print(f"✗ Fichier introuvable : {cible} — rien écrit.")
            return 1
        texte, err = patcher(cible, rempl)
        if err:
            print(f"✗ {err} — rien écrit.")
            return 1
        prets.append((cible, texte))
    for cible, texte in prets:   # tout ou rien
        shutil.copy2(cible, cible.with_name(cible.name + ".bak_s27_sauter"))
        cible.write_text(texte, encoding="utf-8")
        print(f"✓ {cible.name} patché ; sauvegarde .bak_s27_sauter")
    return 0


if __name__ == "__main__":
    sys.exit(main())
