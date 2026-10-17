#!/usr/bin/env python3
"""
patch_s27_v819.py — Ourrassol 2098 (S27, phase 4, 15 octobre 2026)
==================================================================

v8.19 : chaque simulation enregistre ses opérations STRUCTURÉES, pour
appliquer_et_si.py, dans generator/state/et_si_application/<id>.json :

    {id, date_simulation, version, empreinte, annee, mode, scenarios_hypothese,
     scenarios, complet,
     par_scenario: {sc: {
        lecture:  {trajectoires, relations, zones_statut, nouvelles_entites} | null,
        passe:    {trajectoires, relations, textes} (obligatoires) | null,
        erreurs:  [..]}}}

Le fichier est réécrit à chaque simulation de l'hypothèse (comme le dossier).
Rien d'autre ne change dans le rapport.

Refuse un second passage (marqueur PATCH_S27_V819) ; exige la v8.18.
Sauvegarde .bak_v819 ; syntaxe vérifiée avant écriture.

USAGE
    python3 generator/patch_s27_v819.py            # aperçu
    python3 generator/patch_s27_v819.py --apply    # écrit
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

GEN = Path(__file__).resolve().parent
MARQUEUR = "PATCH_S27_V819"

REMPLACEMENTS = [
    ('VERSION = "v8.18"', 'VERSION = "v8.19"'),

    ('''ETAT_PATH = SCRIPT_DIR / "state" / "dernier_et_si.json"
''',
     '''ETAT_PATH = SCRIPT_DIR / "state" / "dernier_et_si.json"
APPLICATION_DIR = SCRIPT_DIR / "state" / "et_si_application"   # PATCH_S27_V819 (appliquer_et_si.py)
'''),

    ('''    _rendre_injection_commune(hyp, application, inj)
''',
     '''    _rendre_injection_commune(hyp, application, inj)
    # PATCH_S27_V819 : opérations structurées pour appliquer_et_si.py (phase 4).
    try:
        _ecrire_operations(brut, hyp, portee, consequences, passe)
    except Exception as e:  # ne doit jamais empêcher le rapport
        avert.append(f"opérations pour appliquer_et_si.py non écrites : {type(e).__name__}: {e}")
'''),

    ('''def main():
''',
     '''def _ecrire_operations(brut, hyp, portee, consequences, passe):
    """PATCH_S27_V819 : données brutes de la lecture IA et des obligatoires de la passe,
    par scénario. appliquer_et_si.py en tire les opérations (numérotées) à appliquer."""
    import et_si_dossiers as _ed
    par_sc = {}
    for sc in portee:
        cons = consequences.get(sc) if isinstance(consequences, dict) else None
        p = passe.get(sc) if isinstance(passe, dict) else None
        erreurs = []
        if cons and cons.get("erreur"):
            erreurs.append(f"lecture IA : {cons['erreur']}")
            cons = None
        if p and p.get("erreur"):
            erreurs.append(f"passe exhaustive : {p['erreur']}")
            p = None
        par_sc[sc] = {
            "lecture": ({k: cons.get(k) or [] for k in ("trajectoires", "relations", "zones_statut",
                                                         "nouvelles_entites")} if cons else None),
            "passe": ({k: (p.get("obligatoire") or {}).get(k) or [] for k in ("trajectoires", "relations", "textes")}
                      if p else None),
            "erreurs": erreurs,
        }
    data = {
        "id": hyp["id"], "date_simulation": datetime.now().isoformat(timespec="minutes"),
        "version": VERSION, "empreinte": _ed.empreinte_hypothese(brut),
        "annee": hyp.get("date"), "mode": hyp.get("mode"), "contraintes": hyp.get("contraintes") or [],
        "scenarios_hypothese": list(hyp.get("scenarios") or []), "scenarios": list(portee),
        "complet": set(portee) >= set(hyp.get("scenarios") or []), "par_scenario": par_sc,
    }
    APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
    cible = APPLICATION_DIR / f"{hyp['id']}.json"
    tmp = cible.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    tmp.replace(cible)


def main():
'''),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    p = GEN / "simuler_et_si.py"
    if not p.exists():
        sys.exit(f"✗ {p.name} introuvable dans {GEN}")
    texte = p.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit("✗ simuler_et_si.py : déjà patché (v8.19), rien à faire.")
    if "PATCH_S27_V818" not in texte:
        sys.exit("✗ simuler_et_si.py : la v8.18 n'est pas installée (patch_s27_v818.py d'abord).")
    for i, (avant, apres) in enumerate(REMPLACEMENTS, 1):
        n = texte.count(avant)
        if n != 1:
            sys.exit(f"✗ ancrage n°{i} trouvé {n} fois (attendu 1) — rien écrit : {avant.strip()[:70]!r}")
        texte = texte.replace(avant, apres)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(texte)
    try:
        py_compile.compile(f.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ erreur de syntaxe après patch, rien écrit :\n{e}")
    finally:
        Path(f.name).unlink(missing_ok=True)
    print(f"  simuler_et_si.py : {len(REMPLACEMENTS)} modification(s), syntaxe OK")
    if not a.apply:
        print("APERÇU : tout s'applique proprement. Relancer avec --apply pour écrire (.bak_v819).")
        return
    shutil.copy2(p, p.with_name(p.name + ".bak_v819"))
    p.write_text(texte, encoding="utf-8")
    print("✓ v8.19 appliquée (simuler_et_si.py ; sauvegarde .bak_v819).")


if __name__ == "__main__":
    main()
