#!/usr/bin/env python3
"""
patch_s27_v76.py — Ourrassol 2098 (S27, 10 octobre 2026)
=========================================================

Simulateur « et si ? » v7.5 -> v7.6 : action « region ».
Une PARTIE d'un pays prend une existence propre SANS changer de mains (foyer de
résistance, région autonome, zone sinistrée, enclave de quarantaine) : une
sous-zone est créée sous la zone du pays, le pays ne bouge pas.

    - pays: Brésil
      action: region
      parent: amazonie_pacte_vert     # optionnel : déduit si le pays n'est que dans une zone N1
      nouvelle_zone: {slug: nordeste_insurge, nom: Nordeste insurgé,
                      type: territoire_autonome, statut: emergent}   # type défaut region, statut défaut emergent
      portion: Le Nordeste, de Salvador à Fortaleza, tenu par la résistance

Contrôles : parent existant et portant le pays ; slug, type, statut validés par
ZoneRepository.creer_sous_zone() en mode aperçu (dry_run, rien n'est écrit) ;
portion obligatoire ; alerte si le pays a déjà d'autres sous-zones sous ce
parent (portions qui pourraient se chevaucher). Rapport : niveau, rédaction
héritée, tracé à dessiner, zones_pays.json inchangé.
La lecture IA peut proposer une région (consigne : rare, lieu précis). Avec
`carte: non`, une région est écartée comme toute proposition de carte.

Fichiers : generator/simuler_et_si.py, et_si/hypotheses.yaml (.bak_v76)

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v76.py            # aperçu
    python3 generator/patch_s27_v76.py --apply    # écrit
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"
HYPS = VAULT_ROOT / "et_si" / "hypotheses.yaml"

NORMALISER_REGION = '''

def normaliser_region(op, ou, erreurs):
    """V7.6 : contrôle d'une région (une partie d'un pays prend une existence
    propre sans changer de mains). Retourne {"nouvelle_zone", "parent",
    "portion"} ou None (erreurs ajoutées). Sert aussi aux propositions de l'IA."""
    nz = op.get("nouvelle_zone")
    if not (isinstance(nz, dict) and nz.get("slug") and nz.get("nom")):
        erreurs.append(f"{ou} : `nouvelle_zone` avec au moins slug et nom requis")
        return None
    portion = " ".join(str(op.get("portion") or "").split())
    if not portion:
        erreurs.append(f"{ou} : texte `portion` requis (quelle partie du pays)")
        return None
    nz = dict(nz)
    nz["slug"] = str(nz["slug"]).strip()
    nz.setdefault("type", "region")
    nz.setdefault("statut", "emergent")
    nz["type"] = nz["type"] or "region"
    nz["statut"] = nz["statut"] or "emergent"
    return {"nouvelle_zone": nz, "parent": str(op.get("parent") or "").strip(), "portion": portion}
'''

EVALUER_REGION = '''

def evaluer_region(repo, mod, sc, op, by_slug, redac):
    """V7.6 : aperçu d'une région. Le pays ne bouge pas : une sous-zone est
    créée sous une zone qui le porte. Contrôle par creer_sous_zone(dry_run=True)
    (n'écrit rien)."""
    pays, nz = op["pays"], dict(op["nouvelle_zone"])
    erreurs, alertes = [], []
    actuelles = repo.zones_portant_un_pays(sc, pays)
    slugs_actuels = {a["slug"] for a in actuelles}
    parent = op.get("parent") or ""
    if not actuelles:
        erreurs.append(f"{pays} n'apparaît dans aucune zone de ce scénario : une région se crée "
                       f"sous une zone qui porte le pays")
    elif not parent:
        n1 = [a for a in actuelles if (a.get("niveau") or 1) == 1]
        if len(n1) == 1:
            parent = n1[0]["slug"]
        else:
            erreurs.append(f"{pays} est dans plusieurs zones ({', '.join(a['slug'] for a in actuelles)}) : "
                           f"préciser `parent`")
    elif parent not in by_slug:
        erreurs.append(f"zone parente {parent!r} introuvable")
    elif parent not in slugs_actuels:
        erreurs.append(f"`{parent}` ne porte pas {pays} : une région reste dans une zone du pays "
                       f"(sinon : absorber ou partition)")
    if nz.get("type") not in mod.ZONE_TYPES and op.get("source") == "ia":
        alertes.append(f"type {nz.get('type')!r} proposé par l'IA invalide : remplacé par « region »")
        nz["type"] = "region"
    niveau = None
    if parent and not erreurs:
        try:
            r = repo.creer_sous_zone(sc, parent, nz["slug"], nz["nom"], nz["type"], nz["statut"],
                                     origine_reelle=[{"entite": pays, "type_entite": "pays",
                                                      "portion": op["portion"]}],
                                     dry_run=True)
            niveau = r.get("niveau")
        except mod.ZoneRepositoryError as e:
            erreurs.append(str(e))

    # Autres sous-zones du pays sous ce parent : portions qui pourraient se chevaucher.
    voisines = []
    if parent:
        for a in actuelles:
            s, vus = (by_slug.get(a["slug"]) or {}).get("parent"), set()
            while s and s not in vus:
                if s == parent:
                    voisines.append(a)
                    break
                vus.add(s)
                s = (by_slug.get(s) or {}).get("parent")
    if voisines:
        alertes.append(f"{pays} a déjà {len(voisines)} sous-zone(s) sous `{parent}` : vérifier que les "
                       f"portions ne se chevauchent pas")

    # Rédaction qui signerait les articles de la région : celle du parent ou d'un ancêtre.
    redaction = None
    if redac is not None and parent:
        redaction, s, vus = False, parent, set()
        while s and s not in vus:
            if s in redac:
                redaction = s
                break
            vus.add(s)
            s = (by_slug.get(s) or {}).get("parent")

    return {"pays": pays, "action": "region", "cible": nz["slug"], "nouvelle_zone": nz,
            "parent": parent, "parent_nom": (by_slug.get(parent) or {}).get("nom"), "niveau": niveau,
            "portion": op["portion"], "erreurs": erreurs, "alertes": alertes, "actuelles": actuelles,
            "voisines": voisines, "redaction": redaction,
            "quittees": [], "impact": None, "redaction_cible": None}
'''

RENDRE_REGION = '''def _rendre_region(g):
    """V7.6 : rapport d'une région."""
    nz = g["nouvelle_zone"]
    L = [f"**{g['pays']}** : nouvelle région `{g['cible']}` ({nz.get('nom')})"
         + (f" dans `{g['parent']}`" if g["parent"] else "")]
    for e in g["erreurs"]:
        L.append(f"- ✗ {e}")
    for a in g["alertes"]:
        L.append(f"- ⚠ {a}")
    if g["erreurs"]:
        return L + [""]
    L.append(f"- Portion : « {g['portion']} »")
    L.append(f"- Sous-zone de niveau {g['niveau']} de `{g['parent']}` ({g.get('parent_nom')}), "
             f"type {nz.get('type')}, statut {nz.get('statut')}")
    if g["actuelles"]:
        L.append("- Aujourd'hui : " + ", ".join(
            f"`{a['slug']}`" + (" (portion dessinée)" if a["type"] == "overlay" else "")
            for a in g["actuelles"]))
    if g["voisines"]:
        L.append("- Autres sous-zones du pays sous ce parent : " + ", ".join(
            f"`{a['slug']}`" + (f" (« {a['portion']} »)" if a.get("portion") else "") for a in g["voisines"]))
    if g["redaction"]:
        L.append(f"- Articles : signés par la rédaction de `{g['redaction']}` (héritée)")
    elif g["redaction"] is False:
        L.append("- Articles : aucune rédaction au-dessus de cette région : journaux à créer "
                 "(`generate_journaux.py --update`)")
    L.append(f"- `zones_pays.json` inchangé : {g['pays']} reste où il est, aucun pays déplacé")
    L.append("- Tracé à dessiner sur la Carte : **1** (la portion)")
    L.append("")
    return L


def _rendre_geo(ops):'''

REMPLACEMENTS_SIMU = [
    ("version", 'VERSION = "v7.5"', 'VERSION = "v7.6"'),

    ("fonction normaliser_region",
     '''    return {"parties": parties, "partie_principale": principale}
''',
     '''    return {"parties": parties, "partie_principale": principale}
''' + NORMALISER_REGION),

    ("lecture de l'action region (hypothèse)",
     '''            if action not in ACTIONS_GEO:
                erreurs.append(f"{ou} : action {action!r} inconnue (absorber | nouvelle_zone | partition)")''',
     '''            if action == "region":
                reg = normaliser_region(op, ou, erreurs)
                if reg is not None:
                    geo.setdefault(sc_geo, []).append({
                        "pays": str(op["pays"]).strip(), "action": "region", "zone": "", **reg})
                continue
            if action not in ACTIONS_GEO:
                erreurs.append(f"{ou} : action {action!r} inconnue (absorber | nouvelle_zone | partition | region)")'''),

    ("fonction evaluer_region",
     '''

def evaluer_geographie(hyp, scenarios=None):''',
     EVALUER_REGION + '''

def evaluer_geographie(hyp, scenarios=None):'''),

    ("aiguillage evaluer_geographie",
     '''            if action == "partition":
                resultats_sc.append(evaluer_partition(repo, mod, sc, op, by_slug, redac))
                continue''',
     '''            if action == "partition":
                resultats_sc.append(evaluer_partition(repo, mod, sc, op, by_slug, redac))
                continue
            if action == "region":
                resultats_sc.append(evaluer_region(repo, mod, sc, op, by_slug, redac))
                continue'''),

    ("contrôle IA : action region acceptée",
     '''        if not pays or (action not in ACTIONS_GEO and action != "partition"):''',
     '''        if not pays or (action not in ACTIONS_GEO and action not in ("partition", "region")):'''),

    ("contrôle IA : région",
     '''        if action == "absorber" and g.get("zone") not in by_zone:''',
     '''        if action == "region":
            errs = []
            reg = normaliser_region(g, f"carte : région de {pays}", errs)
            if reg is None:
                ecartees += errs
                continue
            if reg["parent"] and reg["parent"] not in by_zone:
                ecartees.append(f"carte : région de {pays}, zone parente {reg['parent']!r} inconnue")
                continue
            if reg["nouvelle_zone"]["slug"] in by_zone:
                ecartees.append(f"carte : région de {pays}, slug {reg['nouvelle_zone']['slug']!r} déjà pris")
                continue
            geo.append({"pays": pays, "action": "region", "zone": "", **reg,
                        "raison": str(g.get("raison") or "")})
            continue
        if action == "absorber" and g.get("zone") not in by_zone:'''),

    ("consigne : carte non, aucune région",
     '''"et aucune zone ne passe au statut disparu (en_declin au plus).\\n")''',
     '''"aucune région, et aucune zone ne passe au statut disparu (en_declin au plus).\\n")'''),

    ("consigne : la région",
     '''Un pays ne rejoint qu'une zone voisine ou qui lui est déjà liée (frontière, mer commune,''',
     '''Région : quand une PARTIE d'un pays prend une existence propre SANS changer de mains
(foyer de résistance, région autonome, zone sinistrée, enclave de quarantaine), utilise
"action": "region" avec "nouvelle_zone" (type conseillé : region, territoire_autonome ou
zone_sinistree), "portion" (quelle partie du pays) et, si le pays est dans plusieurs zones,
"parent" (slug de la zone actuelle du pays qui l'accueille). Le pays ne bouge pas. C'est rare :
seulement si le choc frappe un lieu précis.
Un pays ne rejoint qu'une zone voisine ou qui lui est déjà liée (frontière, mer commune,'''),

    ("format JSON : region",
     '''  "geographie": [{{"pays": "nom réel", "action": "absorber | nouvelle_zone | partition", "zone": "slug (si absorber)",''',
     '''  "geographie": [{{"pays": "nom réel", "action": "absorber | nouvelle_zone | partition | region", "zone": "slug (si absorber)",
                  "parent": "slug (si region, optionnel)", "portion": "... (si region)",'''),

    ("rendu de la région",
     '''def _rendre_geo(ops):''',
     RENDRE_REGION),

    ("aiguillage du rendu",
     '''        if g["action"] == "partition":
            L += _rendre_partition(g)
            continue''',
     '''        if g["action"] == "partition":
            L += _rendre_partition(g)
            continue
        if g["action"] == "region":
            L += _rendre_region(g)
            continue'''),
]

DOC_REGION = '''#         - pays: Brésil
#           action: region            # une partie du pays prend une existence propre
#                                     # SANS changer de mains (simulateur v7.6) : sous-zone
#           parent: <slug>            # optionnel : zone du pays qui l'accueille (déduite
#                                     # si le pays n'est que dans une zone de niveau 1)
#           nouvelle_zone: {slug: nordeste_insurge, nom: Nordeste insurgé,
#                           type: territoire_autonome, statut: emergent}
#                                     # type défaut region, statut défaut emergent
#           portion: Le Nordeste, tenu par la résistance
'''

REMPLACEMENTS_HYPS = [
    ("en-tête : action region",
     "#                  types : bloc_continental, union_regionale, territoire_autonome,",
     DOC_REGION + "#                  types : bloc_continental, union_regionale, territoire_autonome,"),
]


def appliquer(nom, texte, remplacements, erreurs):
    print(f"{nom} :")
    for libelle, ancien, nouveau in remplacements:
        n = texte.count(ancien)
        if n != 1:
            erreurs.append(f"{nom} — {libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        texte = texte.replace(ancien, nouveau)
        print(f"  ✓ {libelle}")
    return texte


def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » v7.5 -> v7.6 (action region).")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon : aperçu)")
    args = ap.parse_args()
    for f in (SIMU, HYPS):
        if not f.exists():
            sys.exit(f"✗ Fichier introuvable : {f}")
    simu, hyps = SIMU.read_text(encoding="utf-8"), HYPS.read_text(encoding="utf-8")
    if 'VERSION = "v7.6"' in simu or "def evaluer_region" in simu:
        sys.exit("✗ Patch déjà appliqué (v7.6). Rien à faire.")
    if 'VERSION = "v7.5"' not in simu:
        sys.exit("✗ La v7.5 n'est pas installée : appliquer d'abord patch_s27_v75.py.")
    erreurs = []
    simu = appliquer("simuler_et_si.py", simu, REMPLACEMENTS_SIMU, erreurs)
    hyps = appliquer("hypotheses.yaml", hyps, REMPLACEMENTS_HYPS, erreurs)
    try:
        compile(simu, str(SIMU), "exec")
    except SyntaxError as e:
        erreurs.append(f"simuler_et_si.py ne compilerait pas : {e}")
    try:
        import yaml
        yaml.safe_load(hyps)
    except Exception as e:  # noqa: BLE001
        erreurs.append(f"hypotheses.yaml modifié illisible : {e}")
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    for f, contenu in ((SIMU, simu), (HYPS, hyps)):
        shutil.copy(f, f.with_name(f.name + ".bak_v76"))
        f.write_text(contenu, encoding="utf-8")
        print(f"→ écrit : {f.relative_to(VAULT_ROOT)} (sauvegarde {f.name}.bak_v76)")
    print("\nSimulateur passé en v7.6.")


if __name__ == "__main__":
    main()
