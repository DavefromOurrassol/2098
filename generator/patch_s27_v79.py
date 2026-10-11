#!/usr/bin/env python3
"""
patch_s27_v79.py — Ourrassol 2098 (S27, 10 octobre 2026)
=========================================================

Simulateur « et si ? » v7.8 -> v7.9 : moins de bruit dans les propositions
écartées de la lecture IA. Diagnostic sur ia_majorite_travail_2040 (cache) :

1. « type ou action invalide » = action "renforcée" (relation existante qui se
   renforce) ou action absente. Désormais : renforcée + relation déjà présente
   -> écartée avec un libellé clair (rien à changer) ; renforcée + absente ->
   traitée comme « nouvelle » ; action absente -> « nouvelle ». Chaque
   correction est listée (« Corrections automatiques »), jamais en silence.
2. Slug d'entité sans son suffixe de scénario (union_africaine_resilience)
   -> complété s'il désigne une seule entité connue, correction listée.
3. Slug de ZONE employé dans une relation -> message explicite (« une relation
   relie deux entités ») au lieu de « inconnues ou identiques ».
4. Nouvelle entité de zone « transnationale » -> acceptée telle quelle (valeur
   normale du vault), plus d'alerte.
5. Consigne IA : ne pas proposer une relation déjà présente qui se renforce.

Fichier : generator/simuler_et_si.py (.bak_v79). Le cache est revérifié à
chaque lecture : relancer sans --refaire suffit (aucun appel payant).

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v79.py            # aperçu
    python3 generator/patch_s27_v79.py --apply    # écrit
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"

REMPLACEMENTS = [
    ("version", 'VERSION = "v7.8"', 'VERSION = "v7.9"'),

    ("relations : résolution des slugs et des actions",
     '''        a, b = by_inst.get(r.get("a")), by_inst.get(r.get("b"))
        typ, action = str(r.get("type") or ""), str(r.get("action") or "")
        if not a or not b or a is b:
            ecartees.append(f"relation : entités {r.get('a')!r} / {r.get('b')!r} inconnues ou identiques")
            continue
        if typ not in ("alliance", "opposition") or action not in ("nouvelle", "rompue"):
            ecartees.append(f"relation {r.get('a')} / {r.get('b')} : type ou action invalide")
            continue
        champ = "alliances" if typ == "alliance" else "oppositions"
        existe = b["slug"] in (a.get(champ) or []) or a["slug"] in (b.get(champ) or [])
        if action == "nouvelle" and existe:''',
     '''        # V7.9 : slug sans suffixe de scénario complété (correction listée) ;
        # zone employée comme entité signalée clairement.
        def _entite(slug):
            if slug in by_inst:
                return by_inst[slug]
            cands = [f"{slug}_{s}" for s in SCENARIOS if f"{slug}_{s}" in by_inst]
            if len(cands) == 1:
                corrigees.append(f"relation : {slug!r} complété en {cands[0]!r}")
                return by_inst[cands[0]]
            return None
        a, b = _entite(r.get("a")), _entite(r.get("b"))
        if not a or not b or a is b:
            zones_vues = [s for s in (r.get("a"), r.get("b")) if s in by_zone]
            if zones_vues:
                ecartees.append(f"relation {r.get('a')} / {r.get('b')} : {', '.join(map(repr, zones_vues))} "
                                f"est une zone (une relation relie deux entités)")
            else:
                ecartees.append(f"relation : entités {r.get('a')!r} / {r.get('b')!r} inconnues ou identiques")
            continue
        typ = str(r.get("type") or "").strip().lower()
        action = _plie(str(r.get("action") or "").strip())
        champ = "alliances" if typ == "alliance" else "oppositions"
        existe = b["slug"] in (a.get(champ) or []) or a["slug"] in (b.get(champ) or [])
        if typ not in ("alliance", "opposition"):
            ecartees.append(f"relation {a['slug']} / {b['slug']} : type {r.get('type')!r} invalide")
            continue
        if action in ("", "none"):
            corrigees.append(f"relation {a['slug']} / {b['slug']} : action absente -> nouvelle")
            action = "nouvelle"
        elif action.startswith("renforc"):
            if existe:
                ecartees.append(f"relation {a['slug']} / {b['slug']} : {typ} déjà présente "
                                f"(proposée comme renforcée, rien à changer)")
                continue
            corrigees.append(f"relation {a['slug']} / {b['slug']} : renforcée -> nouvelle (absente du vault)")
            action = "nouvelle"
        if action not in ("nouvelle", "rompue"):
            ecartees.append(f"relation {a['slug']} / {b['slug']} : action {r.get('action')!r} invalide")
            continue
        if action == "nouvelle" and existe:'''),

    ("liste des corrections",
     '''    ecartees, out = [], {"lecture": str(brut.get("lecture") or "").strip(),''',
     '''    corrigees = []   # V7.9 : corrections automatiques, toujours listées
    ecartees, out = [], {"lecture": str(brut.get("lecture") or "").strip(),'''),

    ("nouvelle entité transnationale acceptée",
     '''        zone = n.get("zone")
        if zone and zone not in by_zone:''',
     '''        zone = n.get("zone")
        if zone and _plie(str(zone)).rstrip("e") == "transnational":
            zone = "transnationale"   # V7.9 : valeur normale du vault
        elif zone and zone not in by_zone:'''),

    ("sortie : corrections",
     '''    out["nouvelles_entites"] = ne
    out["ecartees"] = ecartees''',
     '''    out["nouvelles_entites"] = ne
    out["ecartees"] = ecartees
    out["corrigees"] = corrigees'''),

    ("rapport : corrections automatiques",
     '''    if c.get("ecartees"):
        L.append(f"_Propositions écartées au contrôle''',
     '''    if c.get("corrigees"):
        L.append(f"_Corrections automatiques ({len(c['corrigees'])}) : " + " ; ".join(c["corrigees"][:8])
                 + (" …" if len(c["corrigees"]) > 8 else "") + "_")
        L.append("")
    if c.get("ecartees"):
        L.append(f"_Propositions écartées au contrôle'''),

    ("consigne : pas de relation « renforcée »",
     '''Plafonds : {PLAFONDS['trajectoires']} trajectoires, {PLAFONDS['alliances']} relations,''',
     '''Relations : uniquement entre deux ENTITÉS ; "action" vaut "nouvelle" ou "rompue". Une relation
déjà présente qui se renforce ne change rien au vault : ne la propose pas.
Plafonds : {PLAFONDS['trajectoires']} trajectoires, {PLAFONDS['alliances']} relations,'''),
]


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7.8 -> v7.9.")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not SIMU.exists():
        sys.exit(f"✗ Fichier introuvable : {SIMU}")
    txt = SIMU.read_text(encoding="utf-8")
    if 'VERSION = "v7.9"' in txt:
        sys.exit("✗ Patch déjà appliqué (v7.9). Rien à faire.")
    if 'VERSION = "v7.8"' not in txt:
        sys.exit("✗ La v7.8 n'est pas installée : appliquer d'abord patch_s27_v78.py.")
    erreurs = []
    print("simuler_et_si.py :")
    for libelle, ancien, nouveau in REMPLACEMENTS:
        n = txt.count(ancien)
        if n != 1:
            erreurs.append(f"{libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        txt = txt.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    try:
        compile(txt, str(SIMU), "exec")
    except SyntaxError as e:
        erreurs.append(f"ne compilerait pas : {e}")
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    shutil.copy(SIMU, SIMU.with_name(SIMU.name + ".bak_v79"))
    SIMU.write_text(txt, encoding="utf-8")
    print("→ écrit : generator/simuler_et_si.py (sauvegarde simuler_et_si.py.bak_v79)")
    print("\nSimulateur passé en v7.9.")


if __name__ == "__main__":
    main()
