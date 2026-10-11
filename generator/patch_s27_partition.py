#!/usr/bin/env python3
"""
patch_s27_partition.py — Ourrassol 2098 (S27, 10 octobre 2026)
================================================================

Ajoute l'action « partition » au simulateur « et si ? » (v6 -> v7) :
un pays coupé en plusieurs parties, chacune dans une zone existante ou
nouvelle, avec son texte `portion`.

  - Modèle France par défaut : chaque partie a sa portion, le pays n'a plus
    de zone « entière » (zones_pays.json -> null).
  - `partie_principale: N` (optionnel) : la partie N garde le pays entier
    (modèle Allemagne).

Fichiers modifiés :
  - generator/simuler_et_si.py   (.bak_partition)
  - et_si/hypotheses.yaml        (en-tête documenté, .bak_partition)

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_partition.py            # aperçu, rien n'est écrit
    python3 generator/patch_s27_partition.py --apply    # écrit (avec .bak_partition)

Refuse un second passage (marqueur : `def normaliser_partition`).
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
SIMU = VAULT_ROOT / "generator" / "simuler_et_si.py"
HYPS = VAULT_ROOT / "et_si" / "hypotheses.yaml"
MARQUEUR = "def normaliser_partition"


# ---------------------------------------------------------------------------
# Code ajouté
# ---------------------------------------------------------------------------

FONCTION_NORMALISER = r'''def normaliser_partition(op, ou, erreurs):
    """V7 : contrôle d'une partition (un pays coupé en parties).
    Modèle France par défaut : chaque partie porte un texte `portion`.
    `partie_principale` (numéro, optionnel) : cette partie garde le pays entier
    (modèle Allemagne), sans portion. Ajoute les erreurs à `erreurs` et
    retourne None si la partition est invalide. Sert aussi au contrôle des
    propositions de l'IA."""
    n_err = len(erreurs)
    brutes = op.get("parties")
    if not isinstance(brutes, list) or len(brutes) < 2:
        erreurs.append(f"{ou} : `parties` doit lister au moins 2 parties")
        return None
    principale = op.get("partie_principale")
    if principale is not None:
        try:
            principale = int(principale)
        except (TypeError, ValueError):
            principale = 0
        if not 1 <= principale <= len(brutes):
            erreurs.append(f"{ou} : `partie_principale` doit être un numéro de partie (1 à {len(brutes)})")
            return None
    parties = []
    for k, p in enumerate(brutes, 1):
        ouk = f"{ou} partie {k}"
        if not isinstance(p, dict):
            erreurs.append(f"{ouk} mal formée")
            continue
        zone = str(p.get("zone") or "").strip()
        nz = p.get("nouvelle_zone")
        if bool(zone) == bool(nz):
            erreurs.append(f"{ouk} : indiquer `zone` (zone existante) OU `nouvelle_zone`, un seul des deux")
            continue
        if nz and not (isinstance(nz, dict) and nz.get("slug") and nz.get("nom")):
            erreurs.append(f"{ouk} : `nouvelle_zone` avec au moins slug et nom requis")
            continue
        portion = " ".join(str(p.get("portion") or "").split())
        if not portion and k != principale:
            erreurs.append(f"{ouk} : texte `portion` requis (quelle partie du pays)")
            continue
        parties.append({"zone": zone, "nouvelle_zone": dict(nz) if nz else None,
                        "portion": "" if k == principale else portion})
    if len(erreurs) > n_err:
        return None
    cibles = [p["zone"] or p["nouvelle_zone"]["slug"] for p in parties]
    if len(set(cibles)) != len(cibles):
        erreurs.append(f"{ou} : deux parties ne peuvent pas aller dans la même zone")
        return None
    return {"parties": parties, "partie_principale": principale}


'''

FONCTION_EVALUER = r'''def evaluer_partition(repo, mod, sc, op, by_slug, redac):
    """V7 : aperçu d'une partition. Mêmes contrôles qu'absorber / nouvelle_zone,
    partie par partie, puis ce que la partition change : zones actuelles,
    zones_pays.json, tracés à dessiner, sous-zones à répartir. N'écrit rien dans
    les fiches (impact_bascule_pays réécrit seulement son propre rapport
    documentation/need_action/impact_bascule_<pays>_<scénario>.md, une fois par
    partie : le fichier final est celui de la dernière partie)."""
    pays = op["pays"]
    principale = op.get("partie_principale")
    erreurs, alertes = [], []
    actuelles = repo.zones_portant_un_pays(sc, pays)
    n1_actuelles = [a for a in actuelles if (a.get("niveau") or 1) == 1]
    if not actuelles:
        alertes.append(f"{pays} n'apparaît dans aucune zone de ce scénario")
    elif len(n1_actuelles) > 1 or any(a.get("portion") or a["type"] == "overlay" for a in n1_actuelles):
        alertes.append(f"{pays} est déjà partagé aujourd'hui ("
                       + ", ".join(a["slug"] for a in n1_actuelles)
                       + ") : ses portions et tracés actuels seraient remplacés")
    parties, impacts = [], []
    for k, p in enumerate(op["parties"], 1):
        perr, nz = [], None
        if p["zone"]:
            cible_slug = p["zone"]
            cible = by_slug.get(cible_slug)
            if not cible:
                perr.append(f"zone {cible_slug!r} introuvable")
            elif (cible.get("niveau") or 1) != 1:
                alertes.append(f"partie {k} : {cible_slug} est une zone de niveau {cible.get('niveau')} "
                               f"(un pays se rattache d'ordinaire à une zone de niveau 1)")
        else:
            nz = dict(p["nouvelle_zone"])
            cible_slug = nz["slug"]
            if cible_slug in by_slug:
                perr.append(f"le slug {cible_slug!r} existe déjà dans ce scénario")
            if nz.get("type") and nz["type"] not in mod.ZONE_TYPES:
                if op.get("source") == "ia":
                    alertes.append(f"partie {k} : type {nz['type']!r} proposé par l'IA invalide : remplacé par « autre »")
                    nz["type"] = "autre"
                else:
                    perr.append(f"type {nz['type']!r} invalide ({', '.join(mod.ZONE_TYPES)})")
            if nz.get("statut") and nz["statut"] not in mod.ZONE_STATUTS:
                perr.append(f"statut {nz['statut']!r} invalide ({', '.join(mod.ZONE_STATUTS)})")
        if not perr:
            imp = repo.impact_bascule_pays(sc, pays, "creer" if nz else "absorber",
                                           zone_slug=None if nz else cible_slug, nouvelle_zone=nz)
            impacts.append(_filtrer_impact_pays(imp, actuelles, by_slug))
        if redac is None:
            redaction = None
        elif nz:
            redaction = False
        else:
            redaction = _a_une_redaction(cible_slug, by_slug, redac)
        parties.append({"numero": k, "cible": cible_slug,
                        "nom": (nz or by_slug.get(cible_slug) or {}).get("nom"),
                        "nouvelle": bool(nz), "nouvelle_zone": nz, "portion": p["portion"],
                        "principale": k == principale,
                        "zone_actuelle": any(a["slug"] == cible_slug for a in actuelles),
                        "redaction": redaction})
        erreurs += [f"partie {k} : {e}" for e in perr]

    # Zones actuelles de niveau 1 qui ne reçoivent aucune partie : quittées.
    cibles = {p["cible"] for p in parties}
    quittees = []
    for a in n1_actuelles:
        if a["slug"] in cibles:
            continue
        z = by_slug.get(a["slug"]) or {}
        autres = [o for o in (z.get("origine_reelle") or []) if isinstance(o, dict)
                  and o.get("entite") and pays.lower() not in str(o.get("entite")).lower()]
        quittees.append({"slug": a["slug"], "nom": a.get("nom"), "type": a["type"],
                         "videe": not autres, "redaction": bool(redac) and a["slug"] in redac})

    # Sous-zones actuelles qui couvrent le pays : à répartir entre les parties (à la main).
    a_repartir = {}
    for a in actuelles:
        if (a.get("niveau") or 1) != 1:
            a_repartir[a["slug"]] = {"slug": a["slug"], "nom": a.get("nom"), "niveau": a.get("niveau")}
    for imp in impacts:
        for s in imp.get("sous_zones_orphelines") or []:
            a_repartir.setdefault(s["slug"], {"slug": s["slug"], "nom": s.get("nom"), "niveau": s.get("niveau")})

    # Impact commun à toutes les parties (instances, mentions, registre).
    impact = None
    if impacts:
        vus, inst = set(), []
        for imp in impacts:
            for it in imp.get("instances_liees") or []:
                if it.get("slug") not in vus:
                    vus.add(it.get("slug"))
                    inst.append(it)
        impact = {"instances_liees": inst,
                  "mentions_texte": impacts[0].get("mentions_texte") or [],
                  "registre_hits": impacts[0].get("registre_hits") or [],
                  "instances_autres": max(imp.get("instances_autres") or 0 for imp in impacts)}

    return {"pays": pays, "action": "partition", "cible": None, "erreurs": erreurs, "alertes": alertes,
            "actuelles": actuelles, "quittees": quittees, "parties": parties,
            "a_repartir": list(a_repartir.values()), "impact": impact,
            "zones_pays_apres": next((p["cible"] for p in parties if p["principale"]), None),
            "traces_a_dessiner": sum(1 for p in parties if not p["principale"]),
            "redaction_cible": None}


'''

FONCTION_RENDRE = r'''def _rendre_partition(g):
    """V7 : rendu d'une partition dans la section Carte du rapport."""
    pays = g["pays"]
    L = [f"**{pays}** partagé en {len(g['parties'])} parties"]
    for e in g["erreurs"]:
        L.append(f"- ✗ {e}")
    for a in g["alertes"]:
        L.append(f"- ⚠ {a}")
    if g["erreurs"]:
        return L + [""]
    if g["actuelles"]:
        L.append("- Aujourd'hui : " + ", ".join(
            f"`{a['slug']}`" + (" (portion dessinée)" if a["type"] == "overlay" else "")
            for a in g["actuelles"]))
    for p in g["parties"]:
        txt = f"- Partie {p['numero']} → " + (f"nouvelle zone `{p['cible']}`" if p["nouvelle"] else f"`{p['cible']}`")
        if p["zone_actuelle"]:
            txt += " (zone actuelle)"
        txt += " : garde le pays entier" if p["principale"] else f" : « {p['portion']} »"
        if p["redaction"] is False:
            txt += " — sans rédaction : journaux à créer (`generate_journaux.py --update`)"
        L.append(txt)
    for q in g["quittees"]:
        txt = f"- Zone quittée `{q['slug']}`"
        if q["videe"]:
            txt += " : n'aurait **plus aucun territoire**"
        if q["redaction"]:
            txt += (" ; ses journaux (journaux.yaml) resteraient sans territoire" if q["videe"]
                    else " ; a ses propres journaux")
        L.append(txt)
    if g["zones_pays_apres"]:
        L.append(f"- `zones_pays.json` : {pays} → `{g['zones_pays_apres']}` "
                 f"(modèle Allemagne : cette zone garde la couleur du pays)")
    else:
        L.append(f"- `zones_pays.json` : {pays} → `null` (modèle France : aucune zone ne garde le pays "
                 f"entier ; sur la Carte, il n'apparaît que par ses tracés)")
    L.append(f"- Tracés à dessiner sur la Carte : **{g['traces_a_dessiner']}** (un par portion)")
    listes = [("Sous-zones actuelles qui couvrent " + pays + ", à répartir à la main entre les parties",
               [f"`{s['slug']}` ({s.get('nom')}, niveau {s.get('niveau')})" for s in g["a_repartir"]])]
    imp = g["impact"] or {}
    listes += [("Instances et événements des sous-zones du pays",
                [f"`{it.get('slug')}` — {it.get('zone') or ''}" for it in imp.get("instances_liees") or []]),
               (f"Fiches qui citent {pays} dans leur texte",
                [f"`{m.get('slug')}` — {m.get('extrait') or ''}" for m in imp.get("mentions_texte") or []]),
               ("Lignes du registre des événements qui le citent",
                [str(r)[:160] for r in imp.get("registre_hits") or []])]
    for titre, items in listes:
        if not items:
            continue
        L.append(f"- {titre} : **{len(items)}**")
        L += [f"  - {it}" for it in items[:MAX_LISTE]]
        if len(items) > MAX_LISTE:
            L.append(f"  - … et {len(items) - MAX_LISTE} autre(s)")
    if imp.get("instances_autres"):
        L.append(f"- Autres instances des zones concernées, sans lien avec {pays} : "
                 f"{imp['instances_autres']} (non listées)")
    L.append("")
    return L


'''


# ---------------------------------------------------------------------------
# Remplacements (ancien texte -> nouveau), chacun doit apparaître une seule fois
# ---------------------------------------------------------------------------

REMPLACEMENTS_SIMU = [
    ("version", 'VERSION = "v6"', 'VERSION = "v7"'),

    ("fonction normaliser_partition",
     "def verifier_hypothese(h, valid_vars, dyn):",
     FONCTION_NORMALISER + "def verifier_hypothese(h, valid_vars, dyn):"),

    ("lecture de l'action partition dans le YAML",
     '''            action = str(op.get("action") or "").strip()
            if action not in ACTIONS_GEO:
                erreurs.append(f"{ou} : action {action!r} inconnue (absorber | nouvelle_zone)")
                continue''',
     '''            action = str(op.get("action") or "").strip()
            if action == "partition":
                part = normaliser_partition(op, ou, erreurs)
                if part is not None:
                    geo.setdefault(sc_geo, []).append({
                        "pays": str(op["pays"]).strip(), "action": "partition",
                        "zone": "", "nouvelle_zone": None, **part})
                continue
            if action not in ACTIONS_GEO:
                erreurs.append(f"{ou} : action {action!r} inconnue (absorber | nouvelle_zone | partition)")
                continue'''),

    ("fonction evaluer_partition",
     "def evaluer_geographie(hyp, scenarios=None):",
     FONCTION_EVALUER + "def evaluer_geographie(hyp, scenarios=None):"),

    ("aiguillage dans evaluer_geographie",
     '''            pays, action = op["pays"], op["action"]
            erreurs, alertes = [], []''',
     '''            pays, action = op["pays"], op["action"]
            erreurs, alertes = [], []
            if action == "partition":
                resultats_sc.append(evaluer_partition(repo, mod, sc, op, by_slug, redac))
                continue'''),

    ("consigne partition dans le prompt",
     '''Carte : chaque zone liste ses territoires réels ; ne propose pas de rattacher un pays à
une zone qui le contient déjà.''',
     '''Carte : chaque zone liste ses territoires réels ; ne propose pas de rattacher un pays à
une zone qui le contient déjà.
Partition : quand un pays se COUPE (occupation partielle, sécession, territoire qui résiste),
utilise "action": "partition" avec 2 parties ou plus ; chaque partie va dans une zone
existante ("zone", la zone actuelle du pays est permise) ou dans une nouvelle zone
("nouvelle_zone"), avec un texte "portion" court qui dit quelle partie du pays
(ex. « le Nordeste et l'Amazonie »). Deux parties ne vont jamais dans la même zone.'''),

    ("format JSON de la partition",
     '''  "geographie": [{{"pays": "nom réel", "action": "absorber | nouvelle_zone", "zone": "slug (si absorber)",
                  "nouvelle_zone": {{"slug": "...", "nom": "...", "type": "...", "statut": "..."}}, "raison": "..."}}],''',
     '''  "geographie": [{{"pays": "nom réel", "action": "absorber | nouvelle_zone | partition", "zone": "slug (si absorber)",
                  "nouvelle_zone": {{"slug": "...", "nom": "...", "type": "...", "statut": "..."}},
                  "parties": [{{"zone": "slug (ou nouvelle_zone comme ci-dessus)", "portion": "..."}}],
                  "raison": "..."}}],'''),

    ("contrôle IA : action partition acceptée",
     '''        if not pays or action not in ACTIONS_GEO:
            ecartees.append(f"carte : proposition incomplète ({pays or '?'} / {action or '?'})")''',
     '''        if not pays or (action not in ACTIONS_GEO and action != "partition"):
            ecartees.append(f"carte : proposition incomplète ({pays or '?'} / {action or '?'})")'''),

    ("contrôle IA : vérification de la partition",
     '''        pays_vus.add(_plie(pays))
        if action == "absorber" and g.get("zone") not in by_zone:''',
     '''        pays_vus.add(_plie(pays))
        if action == "partition":
            errs = []
            part = normaliser_partition(g, f"carte : partition de {pays}", errs)
            inconnues = [p["zone"] for p in (part or {}).get("parties", [])
                         if p["zone"] and p["zone"] not in by_zone]
            if part is None or inconnues:
                ecartees += errs or [f"carte : partition de {pays}, zone(s) inconnue(s) {inconnues}"]
                continue
            geo.append({"pays": pays, "action": "partition", "zone": "", "nouvelle_zone": None,
                        **part, "raison": str(g.get("raison") or "")})
            continue
        if action == "absorber" and g.get("zone") not in by_zone:'''),

    ("fonction _rendre_partition",
     "def _rendre_geo(ops):",
     FONCTION_RENDRE + "def _rendre_geo(ops):"),

    ("aiguillage dans _rendre_geo",
     '''    for g in ops:
        verbe = (f"rattaché à `{g['cible']}`" if g["action"] == "absorber"''',
     '''    for g in ops:
        if g["action"] == "partition":
            L += _rendre_partition(g)
            continue
        verbe = (f"rattaché à `{g['cible']}`" if g["action"] == "absorber"'''),

    ("résumé de la partition dans la lecture IA",
     '''            cible = g["zone"] if g["action"] == "absorber" else (g["nouvelle_zone"] or {}).get("slug")''',
     '''            if g["action"] == "partition":
                cible = " + ".join(p["zone"] or (p["nouvelle_zone"] or {}).get("slug", "?") for p in g["parties"])
            else:
                cible = g["zone"] if g["action"] == "absorber" else (g["nouvelle_zone"] or {}).get("slug")'''),
]

REMPLACEMENTS_HYPS = [
    ("en-tête : action partition",
     '''#                           type: territoire_autonome, statut: emergent}
#                  types :''',
     '''#                           type: territoire_autonome, statut: emergent}
#         - pays: Brésil
#           action: partition         # couper le pays en parties (simulateur v7)
#           parties:                  # 2 ou plus, chacune dans une zone différente
#             - zone: <slug>          # zone existante (la zone actuelle du pays est permise)
#               portion: Le Nordeste et l'Amazonie, occupés depuis 2029
#             - nouvelle_zone: {slug: republique_du_sud, nom: République du Sud,
#                               type: territoire_autonome, statut: emergent}
#               portion: Le Sud, de São Paulo à Porto Alegre, resté indépendant
#           partie_principale: 2      # optionnel : cette partie garde le pays entier,
#                                     # sans portion (modèle Allemagne). Absent : chaque
#                                     # partie a sa portion et aucune zone ne garde le
#                                     # pays entier (modèle France).
#                  types :'''),
]


def appliquer(texte, remplacements, nom_fichier):
    erreurs = []
    for libelle, ancien, nouveau in remplacements:
        n = texte.count(ancien)
        if n != 1:
            erreurs.append(f"{nom_fichier} — {libelle} : texte attendu trouvé {n} fois (1 attendu)")
            continue
        texte = texte.replace(ancien, nouveau)
        print(f"  ✓ {nom_fichier} — {libelle}")
    return texte, erreurs


def main():
    ap = argparse.ArgumentParser(description="Ajoute l'action « partition » au simulateur « et si ? » (v7).")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon : aperçu)")
    args = ap.parse_args()

    for f in (SIMU, HYPS):
        if not f.exists():
            sys.exit(f"✗ Fichier introuvable : {f}")
    simu = SIMU.read_text(encoding="utf-8")
    hyps = HYPS.read_text(encoding="utf-8")
    if MARQUEUR in simu:
        sys.exit("✗ Patch déjà appliqué (normaliser_partition présent dans simuler_et_si.py). Rien à faire.")

    print("Contrôle des emplacements :")
    simu2, err1 = appliquer(simu, REMPLACEMENTS_SIMU, "simuler_et_si.py")
    hyps2, err2 = appliquer(hyps, REMPLACEMENTS_HYPS, "hypotheses.yaml")
    erreurs = err1 + err2
    if erreurs:
        print("\n✗ Patch NON appliqué :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    try:
        compile(simu2, str(SIMU), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier modifié ne compilerait pas ({e}) : rien n'est écrit.")
    try:
        import yaml
        yaml.safe_load(hyps2)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"✗ hypotheses.yaml modifié illisible ({e}) : rien n'est écrit.")

    if not args.apply:
        print("\nAperçu seulement : tout est en place. Relancer avec --apply pour écrire.")
        return
    for f, contenu in ((SIMU, simu2), (HYPS, hyps2)):
        shutil.copy(f, f.with_name(f.name + ".bak_partition"))
        f.write_text(contenu, encoding="utf-8")
        print(f"→ écrit : {f.relative_to(VAULT_ROOT)} (sauvegarde {f.name}.bak_partition)")
    print("\nSimulateur passé en v7.")


if __name__ == "__main__":
    main()
