#!/usr/bin/env python3
"""
simuler_et_si.py — Ourrassol 2098 (S27, 9 octobre 2026)
=======================================================

Simulateur « et si ? » : mesure l'effet d'un élément HYPOTHÉTIQUE
(événement ou signal pas encore injecté) sur le monde, AVANT de l'injecter.

Lecture seule : rien n'est écrit dans le vault (seul le dernier résultat
est gardé dans generator/state/dernier_et_si.json, pour le GUI).

PRINCIPE
--------
Pour chaque scénario concerné, le moteur dynamique (dynamique.py) simule
le monde de 2025 à la date choisie :
  - SANS l'hypothèse (toutes les injections existantes, comme snapshot.py) ;
  - AVEC l'hypothèse en plus.
L'écart = ce que l'hypothèse ajouterait. Même calcul que la section
« Effet sur le monde » du Tracer (trace_injection.py), dont les fonctions
sont réutilisées. En plus : les tensions (snapshot.check_coherence)
qui apparaîtraient ou disparaîtraient.

ENTRÉE
------
Fichier `et_si/hypotheses.yaml` (racine du vault), éditable à la main ou
depuis le GUI. Une liste `hypotheses:`, chaque hypothèse avec un `id`
(voir le modèle commenté en tête du fichier).

USAGE
-----
    python3 generator/simuler_et_si.py --lister
    python3 generator/simuler_et_si.py --id invasion_bresil_2029
    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --scenario breakdown
    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --date 2060
    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --report     # écrit aussi un .md
    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --recit-ia   # récit rédigé par l'IA (payant)
    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --json
    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --consequences-ia --passe-exhaustive --report

DÉCIDER (v8.17, et_si_dossiers.py)
    python3 generator/simuler_et_si.py --dossiers
    python3 generator/simuler_et_si.py --adopter invasion_bresil_2029 --portee regionale --intensite forte --apercu
    python3 generator/simuler_et_si.py --rejeter invasion_bresil_2029 --motif "trop invraisemblable"
    python3 generator/simuler_et_si.py --annuler-decision invasion_bresil_2029
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
HYPOTHESES_PATH = VAULT_ROOT / "et_si" / "hypotheses.yaml"
REPORT_DIR = VAULT_ROOT / "documentation" / "need_action"
ETAT_PATH = SCRIPT_DIR / "state" / "dernier_et_si.json"
APPLICATION_DIR = SCRIPT_DIR / "state" / "et_si_application"   # PATCH_S27_V819 (appliquer_et_si.py)

SCENARIOS = ["breakdown", "fortress_world", "new_sustainability",
             "eco_communalism", "policy_reform", "reference"]
DELTA_MAX_CONSEILLE = 25   # plafond d'un événement custom (inject_custom_events.py)
ACTIONS_GEO = {"absorber": "absorber", "nouvelle_zone": "creer"}   # vocabulaire du fichier -> ZoneRepository
VERSION = "v8.20"            # affichée dans le rapport : permet de vérifier la version installée
MAX_LISTE = 10             # éléments listés par rubrique dans le rapport (le reste est compté)


# ---------------------------------------------------------------------------
# Lecture et contrôle de l'hypothèse
# ---------------------------------------------------------------------------

def charger_hypotheses(path=HYPOTHESES_PATH):
    if not path.exists():
        sys.exit(f"✗ Fichier introuvable : {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        sys.exit(f"✗ {path.name} illisible (YAML invalide) : {e}")
    hyps = data.get("hypotheses") or []
    return [h for h in hyps if isinstance(h, dict)]


def _racine_n1(slug, by_slug):
    """V7.1 : zone racine de niveau 1 d'une zone (elle-même si niveau 1 ou
    inconnue). Anti-cycle."""
    vus = set()
    while slug in by_slug and slug not in vus:
        vus.add(slug)
        z = by_slug[slug] or {}
        if (z.get("niveau") or 1) == 1 or not z.get("parent"):
            return slug
        slug = z["parent"]
    return slug


def normaliser_partition(op, ou, erreurs):
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


def verifier_hypothese(h, valid_vars, dyn):
    """Retourne (hypothèse normalisée, erreurs, avertissements)."""
    erreurs, avert = [], []
    hid = h.get("id") or "?"
    try:
        date = float(h.get("date"))
    except (TypeError, ValueError):
        erreurs.append("date absente ou non numérique (année, ex. 2029)")
        date = None
    if date is not None and not 2025 <= date <= 2098:
        erreurs.append(f"date {date:g} hors de la période 2025-2098")

    pers = dyn.normaliser_persistance(h.get("persistance")) or dyn.PERSISTANCE_DEFAUT
    if pers not in dyn.PERSISTANCE:
        erreurs.append(f"persistance {h.get('persistance')!r} inconnue "
                       f"(valeurs : {', '.join(dyn.PERSISTANCE)})")

    scen = h.get("scenarios") or SCENARIOS
    if isinstance(scen, str):
        scen = SCENARIOS if scen.strip() in ("tous", "all") else [scen.strip()]
    inconnus = [s for s in scen if s not in SCENARIOS]
    if inconnus:
        erreurs.append(f"scénarios inconnus : {inconnus}")
    scen = [s for s in scen if s in SCENARIOS]

    impacts = []
    for n, imp in enumerate(h.get("impacts") or [], 1):
        if not isinstance(imp, dict):
            erreurs.append(f"impact n°{n} mal formé")
            continue
        var = str(imp.get("variable", "")).strip()
        if var not in valid_vars:
            erreurs.append(f"impact n°{n} : variable inconnue {var!r}")
            continue
        try:
            force = abs(float(imp.get("delta_level")))
        except (TypeError, ValueError):
            erreurs.append(f"impact {var} : delta_level absent ou non numérique")
            continue
        if force < 1:
            erreurs.append(f"impact {var} : delta_level doit valoir au moins 1")
        if force > DELTA_MAX_CONSEILLE:
            avert.append(f"impact {var} : delta_level {force:g} au-dessus du plafond d'un "
                         f"événement custom ({DELTA_MAX_CONSEILLE})")
        pol = imp.get("polarite", 1)
        pols = {}
        for s in scen:
            v = pol.get(s) if isinstance(pol, dict) else pol
            try:
                v = int(v)
            except (TypeError, ValueError):
                v = None
            if v not in (1, -1):
                erreurs.append(f"impact {var} : polarite[{s}] doit valoir 1 ou -1 (reçu {v!r})")
                continue
            pols[s] = v
        try:
            duree = max(float(imp.get("duree") or 10), 1.0)
        except (TypeError, ValueError):
            erreurs.append(f"impact {var} : duree non numérique")
            continue
        impacts.append({"variable": var, "force": force, "polarites": pols, "duree": duree})
    if not impacts and not erreurs and not h.get("geographie"):
        erreurs.append("aucun impact ni changement de géographie déclaré")

    geo = {}
    brut_geo = h.get("geographie") or {}
    if not isinstance(brut_geo, dict):
        erreurs.append("geographie doit être un dictionnaire {scénario: [changements]}")
        brut_geo = {}
    for sc_geo, ops in brut_geo.items():
        if sc_geo not in SCENARIOS:
            erreurs.append(f"geographie : scénario inconnu {sc_geo!r}")
            continue
        for n, op in enumerate(ops or [], 1):
            ou = f"geographie[{sc_geo}] n°{n}"
            if not isinstance(op, dict) or not str(op.get("pays") or "").strip():
                erreurs.append(f"{ou} : champ `pays` requis")
                continue
            action = str(op.get("action") or "").strip()
            if action == "partition":
                part = normaliser_partition(op, ou, erreurs)
                if part is not None:
                    geo.setdefault(sc_geo, []).append({
                        "pays": str(op["pays"]).strip(), "action": "partition",
                        "zone": "", "nouvelle_zone": None, **part})
                continue
            if action == "region":
                reg = normaliser_region(op, ou, erreurs)
                if reg is not None:
                    geo.setdefault(sc_geo, []).append({
                        "pays": str(op["pays"]).strip(), "action": "region", "zone": "", **reg})
                continue
            if action not in ACTIONS_GEO:
                erreurs.append(f"{ou} : action {action!r} inconnue (absorber | nouvelle_zone | partition | region)")
                continue
            if action == "absorber" and not str(op.get("zone") or "").strip():
                erreurs.append(f"{ou} : `zone` (slug d'une zone existante) requis pour absorber")
                continue
            nz = op.get("nouvelle_zone") or {}
            if action == "nouvelle_zone" and not (isinstance(nz, dict) and nz.get("slug") and nz.get("nom")):
                erreurs.append(f"{ou} : `nouvelle_zone` avec au moins slug et nom requis")
                continue
            geo.setdefault(sc_geo, []).append({
                "pays": str(op["pays"]).strip(), "action": action,
                "zone": str(op.get("zone") or "").strip(),
                "nouvelle_zone": dict(nz) if action == "nouvelle_zone" else None,
            })

    # V6 : faits que la lecture IA doit respecter (liste de phrases, optionnelle).
    contraintes = h.get("contraintes") or []
    if isinstance(contraintes, str):
        contraintes = [contraintes]
    if not isinstance(contraintes, list) or not all(isinstance(c, (str, int, float)) for c in contraintes):
        erreurs.append("`contraintes` doit être une liste de phrases")
        contraintes = []
    contraintes = [" ".join(str(c).split()) for c in contraintes if str(c).strip()]

    # V7.3 : `carte: non` = élément sans effet territorial (choc politique, sanitaire...).
    brut_carte = h.get("carte", True)
    carte = not (brut_carte is False or str(brut_carte).strip().lower() in ("non", "no", "false", "0"))
    if not carte and geo:
        erreurs.append("`carte: non` et un bloc `geographie` rempli se contredisent")
    # V7.4 : `mode: rupture` = l'élément déplace durablement l'équilibre du scénario.
    mode = str(h.get("mode") or "choc").strip().lower()
    if mode not in ("choc", "rupture"):
        erreurs.append(f"mode {h.get('mode')!r} inconnu (choc | rupture)")
        mode = "choc"
    if mode == "rupture" and h.get("persistance") is not None:
        avert.append("`persistance` sans objet en mode rupture (le déplacement est permanent) : ignorée")
    norm = {
        "contraintes": contraintes, "carte": carte, "mode": mode,
        "id": hid, "nom": h.get("nom") or hid, "description": str(h.get("description") or "").strip(),
        "date": date, "persistance": pers, "via_matrice": bool(h.get("via_matrice", True)),
        "scenarios": scen, "impacts": impacts, "geographie": geo,
    }
    return norm, erreurs, avert


def chocs_hypothese(hyp, sc):
    """Chocs au format de dynamique.chocs_depuis_donnees(), pour un scénario."""
    return [{
        "nom": "[hypothèse] " + hyp["nom"], "type": "evenement", "variable": imp["variable"],
        "t0": hyp["date"], "duree": imp["duree"], "via_matrice": hyp["via_matrice"],
        "persistance": hyp["persistance"], "fin": None,
        "amplitude": imp["force"] * imp["polarites"][sc],
    } for imp in hyp["impacts"] if sc in imp["polarites"]]


def ruptures_hypothese(hyp, sc):
    """V7.4 : déplacements de référence au format de dynamique.simuler(ruptures=...)."""
    return [{
        "variable": imp["variable"], "t0": hyp["date"], "duree": imp["duree"],
        "amplitude": imp["force"] * imp["polarites"][sc],
    } for imp in hyp["impacts"] if sc in imp["polarites"]]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _tensions(niveaux, matrix, all_variables, check_coherence):
    etats = {v: {"level": n} for v, n in niveaux.items()}
    res = check_coherence(etats, matrix, all_variables)
    # Une seule tension par paire (source, cible) : check_coherence() garde
    # déjà la plus grave (cascade_critique) en cas de doublon.
    return {(t["source"], t["target"]): t for t in res["tensions"]}


def simuler_hypothese(hyp, date_fin, scenarios=None):
    import dynamique as dyn
    import trace_injection as ti
    from loader import load_all_variables, load_influence_matrix, load_custom_signals
    from snapshot import check_coherence

    all_variables = load_all_variables()
    matrix = load_influence_matrix()
    signals = load_custom_signals()
    resultats = {}
    for sc in scenarios or hyp["scenarios"]:
        variables, ref, params, liens, k, instances, events = ti._donnees_scenario(sc)
        chocs_sans = dyn.chocs_depuis_donnees(sc, instances, events, signals)
        rupture = hyp.get("mode") == "rupture"
        propres = [] if rupture else chocs_hypothese(hyp, sc)
        rupts = ruptures_hypothese(hyp, sc) if rupture else []
        if not propres and not rupts:
            continue
        # PATCH_S19_RUPTURE : ruptures déjà présentes dans le monde (fiches en mode rupture).
        rupt_base = dyn.ruptures_depuis_donnees(events)
        sans = dyn.simuler(variables, ref, params, liens, chocs_sans, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k, ruptures=rupt_base or None)
        avec = dyn.simuler(variables, ref, params, liens, chocs_sans + propres, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k, ruptures=(rupt_base + rupts) or None)
        directes = {c["variable"] for c in propres + rupts}
        ref_apres = avec.get("references") or ref
        ref = sans.get("references") or ref   # référence du monde actuel, ruptures existantes comprises

        effets = []
        for v in variables:
            diff = round(avec["niveaux"][v] - sans["niveaux"][v], 1)
            if abs(diff) >= ti.SEUIL_EFFET:
                effets.append({"variable": v, "reference": ref[v], "reference_apres": ref_apres[v],
                               "sans": sans["niveaux"][v],
                               "avec": avec["niveaux"][v], "effet": diff,
                               "mode": "direct" if v in directes else "propagé"})
        effets.sort(key=lambda e: -abs(e["effet"]))

        effets_traj = [(ta, {v: round(na[v] - ns[v], 2) for v in variables})
                       for (ta, na), (_, ns) in zip(avec["trajectoire"], sans["trajectoire"])]
        reperes = ti._chronologie(effets_traj, hyp["date"], directes)
        retenues = [r["variable"] for r in reperes[:ti.MAX_VARIABLES_GRAPHE]]
        chrono = {
            "apparition": hyp["date"], "date_fin": date_fin, "reperes": reperes,
            "series": {v: [[t, e[v]] for t, e in effets_traj if t >= hyp["date"] - 1] for v in retenues},
            "niveaux": {v: {"avec": [[t, n[v]] for t, n in avec["trajectoire"] if t >= hyp["date"] - 1],
                            "sans": [[t, n[v]] for t, n in sans["trajectoire"] if t >= hyp["date"] - 1],
                            "reference": ref[v]} for v in retenues},
        }

        t_sans = _tensions(sans["niveaux"], matrix, all_variables, check_coherence)
        t_avec = _tensions(avec["niveaux"], matrix, all_variables, check_coherence)
        resultats[sc] = {
            "effets": effets, "chronologie": chrono,
            "tensions_apparues": [t_avec[c] for c in t_avec if c not in t_sans],
            "tensions_disparues": [t_sans[c] for c in t_sans if c not in t_avec],
            "tensions_aggravees": [t_avec[c] for c in t_avec if c in t_sans
                                   and t_avec[c]["type"] != t_sans[c]["type"]
                                   and t_avec[c]["type"] == "cascade_critique"],
            "tensions_attenuees": [t_avec[c] for c in t_avec if c in t_sans
                                   and t_avec[c]["type"] != t_sans[c]["type"]
                                   and t_sans[c]["type"] == "cascade_critique"],
            "nb_tensions": {"sans": len(t_sans), "avec": len(t_avec)},
        }
    return resultats


# ---------------------------------------------------------------------------
# Géographie : aperçu des changements de carte (phase 2, 9 octobre 2026)
# ---------------------------------------------------------------------------

def charger_zone_repository():
    """ZoneRepository vit dans gui/ (aucune dépendance Flask) : chargé par son
    chemin, comme il charge lui-même generator/regenerer_corps_geographie.py."""
    import importlib.util
    chemin = VAULT_ROOT / "gui" / "zone_repository.py"
    if not chemin.exists():
        raise FileNotFoundError(f"{chemin} introuvable")
    spec = importlib.util.spec_from_file_location("zone_repository", chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ZoneRepository(VAULT_ROOT, VAULT_ROOT / "gui"), mod


def zones_avec_redaction(sc):
    """Zones (slugs) qui ont au moins une rédaction dans journaux.yaml."""
    path = SCRIPT_DIR / "journaux.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    zones = set()
    for ligne in (data.get(sc) or {}).values():
        if isinstance(ligne, dict) and isinstance(ligne.get("zones"), dict):
            zones |= set(ligne["zones"])
    return zones


def _a_une_redaction(slug, by_slug, redac):
    """Vrai si la zone ou un de ses parents a une rédaction (même remontée
    que la résolution du journal d'un article)."""
    vus = set()
    while slug and slug not in vus:
        if slug in redac:
            return True
        vus.add(slug)
        slug = (by_slug.get(slug) or {}).get("parent")
    return False


def _filtrer_impact_pays(impact, actuelles, by_slug):
    """V4 : impact_bascule_pays liste toutes les instances de la zone quittée et de
    la zone cible (tout un continent parfois). On ne garde que celles qui touchent
    CE pays : localisées dans une sous-zone qui le porte (ou une de ses filles), ou
    dont le texte le cite. Les autres sont seulement comptées."""
    if not impact:
        return impact
    propres = {a["slug"] for a in actuelles if (a.get("niveau") or 1) != 1}
    ajout = True
    while ajout:
        ajout = False
        for slug, z in by_slug.items():
            if z.get("parent") in propres and slug not in propres:
                propres.add(slug)
                ajout = True
    cites = {m.get("slug") for m in (impact.get("mentions_texte") or []) if isinstance(m, dict)}
    gardees, autres = [], 0
    for it in impact.get("instances_liees") or []:
        if it.get("zone") in propres or it.get("slug") in cites:
            gardees.append(it)
        else:
            autres += 1
    impact = dict(impact, instances_liees=gardees, instances_autres=autres)
    impact["rien_detecte"] = not (impact.get("sous_zones_orphelines") or gardees
                                  or impact.get("mentions_texte") or impact.get("registre_hits"))
    return impact


def evaluer_partition(repo, mod, sc, op, by_slug, redac):
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

    # V7.1 : deux parties sous la même zone de niveau 1 = pas de changement de contrôle.
    racines = {}
    for p in parties:
        r = p["cible"] if p["nouvelle"] else _racine_n1(p["cible"], by_slug)
        racines.setdefault(r, []).append(str(p["numero"]))
    for r, nums in racines.items():
        if len(nums) > 1:
            erreurs.append(f"parties {' et '.join(nums)} : même zone de niveau 1 ({r}) — le territoire "
                           f"ne change pas de mains, ce n'est pas une partition")

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


def evaluer_geographie(hyp, scenarios=None):
    """Pour chaque changement de carte déclaré : contrôles + rapport d'impact
    de la Carte (ZoneRepository.impact_bascule_pays, qui n'écrit rien dans les
    fiches -- seulement son propre rapport dans documentation/need_action/)."""
    if not hyp["geographie"]:
        return {}
    repo, mod = charger_zone_repository()
    out = {}
    for sc, ops in hyp["geographie"].items():
        if scenarios and sc not in scenarios:
            continue
        zones = repo.load_all_zones(sc)
        by_slug = {z.get("slug"): z for z in zones}
        redac = zones_avec_redaction(sc)
        resultats_sc = []
        if not zones:
            out[sc] = [{"pays": op["pays"], "action": op["action"], "cible": op["zone"] or (op["nouvelle_zone"] or {}).get("slug"),
                        "erreurs": [f"fiche geographie/{sc}.md introuvable ou sans zones"], "alertes": [],
                        "actuelles": [], "quittees": [], "redaction_cible": None, "impact": None} for op in ops]
            continue
        for op in ops:
            pays, action = op["pays"], op["action"]
            erreurs, alertes = [], []
            if action == "partition":
                resultats_sc.append(evaluer_partition(repo, mod, sc, op, by_slug, redac))
                continue
            if action == "region":
                resultats_sc.append(evaluer_region(repo, mod, sc, op, by_slug, redac))
                continue
            actuelles = repo.zones_portant_un_pays(sc, pays)
            if not actuelles:
                alertes.append(f"{pays} n'apparaît dans aucune zone de ce scénario")
            nz, cible_slug = None, op["zone"]
            if action == "absorber":
                cible = by_slug.get(cible_slug)
                if not cible:
                    erreurs.append(f"zone cible {cible_slug!r} introuvable")
                else:
                    if cible.get("niveau", 1) != 1:
                        alertes.append(f"{cible_slug} est une zone de niveau {cible.get('niveau')} "
                                       f"(la Carte rattache d'ordinaire un pays à une zone de niveau 1)")
                    # V4 : quel que soit le type de rattachement (pays entier ou portion dessinée).
                    if any(a["slug"] == cible_slug for a in actuelles):
                        erreurs.append(f"{pays} est déjà rattaché à {cible_slug} : rien ne changerait")
            else:
                nz = dict(op["nouvelle_zone"])
                cible_slug = nz.get("slug")
                if cible_slug in by_slug:
                    erreurs.append(f"le slug {cible_slug!r} existe déjà dans ce scénario")
                if nz.get("type") and nz["type"] not in mod.ZONE_TYPES:
                    if op.get("source") == "ia":
                        alertes.append(f"type {nz['type']!r} proposé par l'IA invalide : remplacé par « autre »")
                        nz["type"] = "autre"
                    else:
                        erreurs.append(f"type {nz['type']!r} invalide ({', '.join(mod.ZONE_TYPES)})")
                if nz.get("statut") and nz["statut"] not in mod.ZONE_STATUTS:
                    erreurs.append(f"statut {nz['statut']!r} invalide ({', '.join(mod.ZONE_STATUTS)})")
            impact = None
            if not erreurs:
                impact = repo.impact_bascule_pays(sc, pays, ACTIONS_GEO[action],
                                                  zone_slug=cible_slug if action == "absorber" else None,
                                                  nouvelle_zone=nz)
                impact = _filtrer_impact_pays(impact, actuelles, by_slug)
            # Zones quittées : vidées de tout territoire ? rédactions concernées ?
            quittees = []
            for a in actuelles:
                # Sous-zones : déjà couvertes par « sous-zones orphelines » du rapport de la Carte.
                if a["slug"] == cible_slug or (a.get("niveau") or 1) != 1:
                    continue
                z = by_slug.get(a["slug"]) or {}
                autres = [o for o in (z.get("origine_reelle") or []) if isinstance(o, dict)
                          and o.get("entite") and pays.lower() not in str(o.get("entite")).lower()]
                quittees.append({"slug": a["slug"], "nom": a.get("nom"), "type": a["type"],
                                 "videe": not autres,
                                 "redaction": bool(redac) and a["slug"] in redac})
            if redac is None:
                redac_cible = None
            elif action == "nouvelle_zone":
                redac_cible = False
            else:
                redac_cible = _a_une_redaction(cible_slug, by_slug, redac)
            resultats_sc.append({"pays": pays, "action": action, "cible": cible_slug,
                                 "erreurs": erreurs, "alertes": alertes, "actuelles": actuelles,
                                 "quittees": quittees, "redaction_cible": redac_cible, "impact": impact})
        out[sc] = resultats_sc
    return out


# ---------------------------------------------------------------------------
# Lecture des conséquences par l'IA (étage B, 9 octobre 2026)
# ---------------------------------------------------------------------------

TRAJECTOIRES = ["émergent", "marginal", "ascendant", "dominant", "mature", "déclinant",
                "résiduel", "transformé", "disparu", "historique", "mythifié"]
MAX_INSTANCES_CONTEXTE = 40
TYPES_ZONE = ["bloc_continental", "union_regionale", "territoire_autonome", "territoire_herite", "region",
              "ville", "infrastructure", "site_strategique", "zone_sinistree", "autre"]
PLAFONDS = {"trajectoires": 8, "alliances": 6, "geographie": 4, "zones_statut": 4, "nouvelles_entites": 3}
CACHE_CONSEQUENCES = SCRIPT_DIR / "state" / "et_si_consequences.json"


def _plie(s):
    """Minuscules sans accents ni espaces superflus (comparaison tolérante)."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c)).replace(" ", "_")


def _valeur_canonique(v, permises):
    """'declinant' -> 'déclinant', 'en_déclin' -> 'en_declin' ; None si inconnue."""
    table = {_plie(p): p for p in permises}
    return table.get(_plie(v))


def _court(texte, n):
    texte = " ".join(str(texte or "").split())
    return texte if len(texte) <= n else texte[:n].rsplit(" ", 1)[0] + "…"


def _empreinte(hyp, sc, effets):
    import hashlib
    brut = json.dumps({"h": {k: hyp.get(k) for k in ("nom", "description", "date", "impacts", "persistance",
                                                       "contraintes", "mode")
                             if k not in ("contraintes", "mode") or (hyp.get(k) and hyp.get(k) != "choc")},
                       "sc": sc, "e": [(e["variable"], e["effet"]) for e in effets[:6]]},
                      ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(brut.encode("utf-8")).hexdigest()[:16]


def _extraire_json(texte):
    texte = (texte or "").strip()
    if texte.startswith("```"):
        texte = texte.strip("`")
        texte = texte[texte.find("{"):]
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut < 0 or fin <= debut:
        raise ValueError("aucun objet JSON dans la réponse")
    return json.loads(texte[debut:fin + 1])


def _contexte_scenario(sc):
    from loader import load_scenario, load_instances_for_scenario
    scen = load_scenario(sc)
    instances = load_instances_for_scenario(sc)
    def poids(i):
        try:
            return float(i.get("impact_local") or 0) + float(i.get("impact_systemique_global") or 0)
        except (TypeError, ValueError):
            return 0.0
    instances.sort(key=lambda i: -poids(i))
    zones = []
    try:
        repo, _ = charger_zone_repository()
        zones = repo.load_all_zones(sc)
    except Exception:
        pass
    return scen, instances, zones


def lire_consequences(hyp, sc, effets, refaire=False):
    """Un appel IA (tier structured_strict) : propositions de reconfiguration du
    lore pour CE scénario, vérifiées ensuite contre le vault. Rien n'est écrit,
    sauf le cache state/et_si_consequences.json."""
    cle = f"{hyp['id']}::{sc}"
    empreinte = _empreinte(hyp, sc, effets)
    cache = {}
    if CACHE_CONSEQUENCES.exists():
        try:
            cache = json.loads(CACHE_CONSEQUENCES.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cache = {}
    scen, instances, zones = _contexte_scenario(sc)
    by_inst = {i["slug"]: i for i in instances}
    by_zone = {z.get("slug"): z for z in zones}
    # V4 : le cache garde la réponse BRUTE de l'IA et la revérifie à chaque lecture,
    # pour que les règles de contrôle à jour s'appliquent sans relancer l'IA.
    # Une entrée d'avant la v4 (sans « brut ») est relancée une fois.
    entree = cache.get(cle) or {}
    if not refaire and entree.get("empreinte") == empreinte and isinstance(entree.get("brut"), dict):
        res = verifier_consequences(entree["brut"], by_inst, by_zone)
        res["depuis_cache"] = True
        return res

    # Les 40 plus influentes, plus celles dont le texte cite un nom propre de
    # l'hypothèse (lieu, acteur) : un choc localisé touche d'abord les acteurs locaux.
    import re as _re
    noms = {m for m in _re.findall(r"\b[A-ZÉÈÀÂÎÔÛÇ][\wéèêàâîôûçë'-]{3,}", hyp["nom"] + " " + hyp["description"])
            if m not in {"Invasion", "Conflit", "Crise", "Guerre", "Effondrement"}}
    # Zones dont un territoire réel est cité par l'hypothèse (et leurs sous-zones) :
    # les instances qui y sont localisées sont les acteurs DIRECTEMENT concernés.
    zones_touchees = {z.get("slug") for z in zones
                      if any(isinstance(o, dict) and any(n in str(o.get("entite", "")) for n in noms)
                             for o in (z.get("origine_reelle") or []))}
    ajout = True
    while ajout:
        ajout = False
        for z in zones:
            if z.get("parent") in zones_touchees and z.get("slug") not in zones_touchees:
                zones_touchees.add(z.get("slug"))
                ajout = True
    def locale(i):
        texte_i = f"{i.get('name')} {i.get('role_dans_scenario')} {(i.get('localisation') or {}).get('lieu', '')}"
        return ((i.get("localisation") or {}).get("zone") in zones_touchees
                or any(n in texte_i for n in noms))
    locales = [i for i in instances if locale(i)][:30]
    choisies = list(locales)
    deja = {i["slug"] for i in choisies}
    for i in instances:
        if len(choisies) >= MAX_INSTANCES_CONTEXTE + len(locales):
            break
        if i["slug"] not in deja:
            choisies.append(i)
            deja.add(i["slug"])
    lignes_inst = []
    for i in choisies:
        zone = (i.get("localisation") or {}).get("zone") or "transnationale"
        lignes_inst.append(f"- {i['slug']} | {i.get('name')} | {i.get('trajectoire')} | zone {zone}"
                           + (" | DIRECTEMENT CONCERNÉE" if i["slug"] in {x["slug"] for x in locales} else "")
                           + " | "
                           f"{_court(i.get('role_dans_scenario'), 160)}")
    lignes_zones = []
    for z in zones:
        if (z.get("niveau") or 1) > 2:
            continue
        pays = ", ".join(str(o.get("entite")) for o in (z.get("origine_reelle") or [])[:6] if isinstance(o, dict))
        lignes_zones.append(f"- {z.get('slug')} | {z.get('nom')} | niveau {z.get('niveau')}"
                            + (f" sous {z.get('parent')}" if z.get("parent") else "")
                            + f" | {z.get('statut')} | {_court(pays, 120)}")
    lignes_effets = [f"- {e['variable']} : {e['effet']:+.1f} point(s)" for e in effets[:8]] \
        or ["- (aucun effet chiffré notable)"]
    impacts_txt = ", ".join(f"{i['variable']} (force {i['force']:g})" for i in hyp["impacts"]) or "aucun"

    bloc_contraintes = ""
    if hyp.get("contraintes"):
        bloc_contraintes = ("FAITS À RESPECTER (priment sur tes connaissances générales ; toute "
                            "proposition qui les contredit est fausse) :\n"
                            + "\n".join(f"- {c}" for c in hyp["contraintes"]) + "\n")
    if hyp.get("mode") == "rupture":
        nature = "MODE RUPTURE (déplacement permanent de l'équilibre du scénario)"
        avert_moteur = ("Effet chiffré simulé en fin de période (niveau 100 = crise) — MODE RUPTURE : l'élément\n"
                        "déplace durablement l'équilibre du scénario, ces chiffres en tiennent compte ; une variable\n"
                        "déjà proche de 100 ne peut plus monter beaucoup, juge aussi d'après la nature de l'élément :")
    else:
        nature = f"persistance {hyp['persistance']}"
        avert_moteur = ("Effet chiffré simulé en fin de période (niveau 100 = crise) — ATTENTION : le moteur\n"
                        "amortit fortement les chocs (il les fait revenir vers l'équilibre du scénario) ;\n"
                        "juge l'ampleur de la reconfiguration d'après la nature de l'élément, pas d'après ces seuls chiffres :")
    bloc_carte = ""
    if not hyp.get("carte", True):
        bloc_carte = ("CET ÉLÉMENT N'A AUCUN EFFET TERRITORIAL : réponds obligatoirement "
                      "\"geographie\": [] (aucun rattachement, aucune nouvelle zone, aucune partition), "
                      "aucune région, et aucune zone ne passe au statut disparu (en_declin au plus).\n")
    user = f"""Monde fictif Ourrassol 2098, scénario « {scen.get('name', sc)} » ({sc}).

LOGIQUE DU SCÉNARIO :
{_court(scen.get('summary'), 900)}
{_court(scen.get('system_logic'), 900)}

ÉLÉMENT PERTURBATEUR HYPOTHÉTIQUE (pas encore dans le lore) :
{hyp['nom']} — apparition en {hyp['date']:g}, {nature}.
{_court(hyp['description'], 700)}
{bloc_contraintes}Variables touchées : {impacts_txt}
{avert_moteur}
{chr(10).join(lignes_effets)}

ZONES DU SCÉNARIO (slug | nom | niveau | statut | territoires réels) :
{chr(10).join(lignes_zones)}

ENTITÉS PRINCIPALES (slug | nom | trajectoire | zone | rôle) :
{chr(10).join(lignes_inst)}

TÂCHE : dis comment le lore de CE scénario se reconfigurerait si cet élément survenait.
Reste dans la logique du scénario : un même choc ne produit pas les mêmes effets partout,
et un monde peut aussi l'encaisser sans grand bouleversement (dis-le alors, avec peu de propositions).
Utilise UNIQUEMENT les slugs listés ci-dessus. ATTENTION aux deux familles de slugs :
une ENTITÉ finit toujours par _{sc} (ex. « xxx_{sc} ») ; une ZONE n'a jamais ce suffixe.
N'utilise jamais un slug de zone comme entité, ni l'inverse.
PRIORITÉ aux entités marquées DIRECTEMENT CONCERNÉE et aux zones des territoires touchés.
Un effet lointain (autre continent) n'est proposé que s'il découle clairement du choc :
au plus 2 propositions lointaines en tout.
Relations : uniquement entre deux ENTITÉS ; "action" vaut "nouvelle" ou "rompue". Une relation
déjà présente qui se renforce ne change rien au vault : ne la propose pas.
Plafonds : {PLAFONDS['trajectoires']} trajectoires, {PLAFONDS['alliances']} relations,
{PLAFONDS['geographie']} changements de carte, {PLAFONDS['zones_statut']} statuts de zone,
{PLAFONDS['nouvelles_entites']} nouvelles entités. Chaque proposition a une raison courte (une phrase).
Trajectoire = position sur un axe ORDONNÉ (vie d'une entité) :
émergent → marginal → ascendant → dominant → mature → déclinant → résiduel → transformé
→ disparu → historique → mythifié. Une entité qui se RENFORCE avance vers ascendant/dominant ;
une entité déjà dominante qui se renforce RESTE dominante (pas de proposition) ; une entité
qui s'affaiblit va vers déclinant/résiduel/disparu.
La trajectoire ACTUELLE de chaque entité est donnée dans la liste (3e colonne) : ne propose
une trajectoire que si elle DIFFÈRE de l'actuelle. Écris les valeurs exactement comme
ci-dessus, accents compris. Même règle pour les zones : statut actuel donné, ne propose
qu'un statut différent.
Carte : ne propose un changement de carte QUE si l'élément fait changer de mains un territoire
(conquête, sécession, annexion, zone rendue inhabitable). Sinon "geographie": [] : c'est la
réponse normale pour la plupart des chocs (politiques, sanitaires, technologiques).
{bloc_carte}Carte : chaque zone liste ses territoires réels ; ne propose pas de rattacher un pays à
une zone qui le contient déjà.
Partition : quand un pays se COUPE (occupation partielle, sécession, territoire qui résiste),
utilise "action": "partition" avec 2 parties ou plus ; chaque partie va dans une zone
existante ("zone", la zone actuelle du pays est permise) ou dans une nouvelle zone
("nouvelle_zone"), avec un texte "portion" court qui dit quelle partie du pays
(ex. « la moitié nord du pays »). Une partition = un territoire qui passe sous un autre
contrôle ; une contestation sociale ou politique à l'intérieur d'un bloc n'en est pas une
(propose-la en relations ou en nouvelles entités). Deux parties ne vont jamais dans la même
zone, ni dans deux zones d'un même bloc (une zone et sa sous-zone).
Chaque partie porte SOIT "zone" (zone existante) SOIT "nouvelle_zone", jamais les deux.
Région : quand une PARTIE d'un pays prend une existence propre SANS changer de mains
(foyer de résistance, région autonome, zone sinistrée, enclave de quarantaine), utilise
"action": "region" avec "nouvelle_zone" (type conseillé : region, territoire_autonome ou
zone_sinistree), "portion" (quelle partie du pays) et, si le pays est dans plusieurs zones,
"parent" (slug de la zone actuelle du pays qui l'accueille). Le pays ne bouge pas. C'est rare :
seulement si le choc frappe un lieu précis.
Un pays ne rejoint qu'une zone voisine ou qui lui est déjà liée (frontière, mer commune,
histoire) : pas de rattachement à une zone d'un autre continent.
Statuts de zone possibles : dominant, stable, fragmenté, en_declin, disparu, emergent.
Types de zone possibles (champ "type" d'une nouvelle zone) : {', '.join(TYPES_ZONE)}.

Réponds UNIQUEMENT en JSON, format exact :
{{
  "lecture": "2 à 4 phrases : ce que le choc change dans ce scénario, et ce qu'il ne change pas",
  "ampleur": "faible | moderee | forte | bascule",
  "trajectoires": [{{"instance": "slug", "apres": "trajectoire", "raison": "..."}}],
  "relations": [{{"a": "slug", "b": "slug", "type": "alliance | opposition", "action": "nouvelle | rompue", "raison": "..."}}],
  "geographie": [{{"pays": "nom réel", "action": "absorber | nouvelle_zone | partition | region", "zone": "slug (si absorber)",
                  "parent": "slug (si region, optionnel)", "portion": "... (si region)",
                  "nouvelle_zone": {{"slug": "...", "nom": "...", "type": "...", "statut": "..."}},
                  "parties": [{{"zone": "slug d'une zone existante", "portion": "..."}},
                              {{"nouvelle_zone": {{"slug": "...", "nom": "...", "type": "...", "statut": "..."}}, "portion": "..."}}],
                  "raison": "..."}}],
  "zones_statut": [{{"zone": "slug", "apres": "statut", "raison": "..."}}],
  "nouvelles_entites": [{{"nom": "...", "role": "...", "zone": "slug", "raison": "..."}}]
}}"""
    from llm_client import call_llm
    texte = call_llm(system_prompt="Tu es l'architecte du lore d'un monde fictif. Tu proposes, tu n'inventes pas de références.",
                     user_prompt=user, max_tokens=3500, temperature=0.3, task_tier="structured_strict")
    brut = _extraire_json(texte)
    res = verifier_consequences(brut, by_inst, by_zone)
    try:
        cache[cle] = {"empreinte": empreinte, "date": datetime.now().isoformat(timespec="minutes"), "brut": brut}
        CACHE_CONSEQUENCES.parent.mkdir(parents=True, exist_ok=True)
        CACHE_CONSEQUENCES.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    return res


def verifier_consequences(brut, by_inst, by_zone):
    """Contrôle mécanique des propositions de l'IA : toute référence inconnue est
    écartée (et listée), rien n'est inventé ni corrigé en silence."""
    statuts = {"dominant", "stable", "fragmenté", "en_declin", "disparu", "emergent"}
    corrigees = []   # V7.9 : corrections automatiques, toujours listées
    ecartees, out = [], {"lecture": str(brut.get("lecture") or "").strip(),
                         "ampleur": str(brut.get("ampleur") or "").strip()}

    def liste(cle):
        v = brut.get(cle) or []
        return [x for x in v if isinstance(x, dict)][:PLAFONDS.get(cle, PLAFONDS.get("alliances"))]

    traj = []
    for t in liste("trajectoires"):
        inst = by_inst.get(t.get("instance"))
        apres = _valeur_canonique(t.get("apres"), TRAJECTOIRES) or str(t.get("apres") or "").strip()
        if not inst:
            ecartees.append(f"trajectoire : entité inconnue {t.get('instance')!r}")
        elif apres not in TRAJECTOIRES:
            ecartees.append(f"trajectoire : valeur {apres!r} invalide pour {t.get('instance')}")
        elif apres == inst.get("trajectoire"):
            ecartees.append(f"trajectoire : {t.get('instance')} déjà {apres} (aucun changement)")
        elif (inst.get("trajectoire") in TRAJECTOIRES[:4] and apres in TRAJECTOIRES[:4]
              and TRAJECTOIRES.index(apres) < TRAJECTOIRES.index(inst.get("trajectoire"))):
            # émergent → marginal → ascendant → dominant : une entité ne « redevient » pas
            # ascendante ou émergente ; un affaiblissement passe par déclinant/résiduel.
            ecartees.append(f"trajectoire : {t.get('instance')} {inst.get('trajectoire')} → {apres} "
                            f"(recul sur la phase de montée, incohérent)")
        elif (inst.get("trajectoire") in TRAJECTOIRES[4:9] and apres in TRAJECTOIRES[4:7]
              and TRAJECTOIRES.index(apres) < TRAJECTOIRES.index(inst.get("trajectoire"))):
            # V5 : mature → déclinant → résiduel → transformé → disparu. Revenir à mature,
            # déclinant ou résiduel depuis plus loin est incohérent ; une renaissance
            # (retour à émergent / ascendant) reste permise.
            ecartees.append(f"trajectoire : {t.get('instance')} {inst.get('trajectoire')} → {apres} "
                            f"(recul dans la phase de déclin, incohérent ; une renaissance irait vers ascendant)")
        else:
            traj.append({"instance": inst["slug"], "nom": inst.get("name"), "avant": inst.get("trajectoire"),
                         "apres": apres, "raison": str(t.get("raison") or "")})
    out["trajectoires"] = traj

    rel = []
    for r in brut.get("relations") or brut.get("alliances") or []:
        if not isinstance(r, dict) or len(rel) >= PLAFONDS["alliances"]:
            continue
        # V7.9 : slug sans suffixe de scénario complété (correction listée) ;
        # zone employée comme entité signalée clairement.
        corr_r = []   # V7.9.1 : listées seulement si la relation est gardée
        def _entite(slug):
            if slug in by_inst:
                return by_inst[slug]
            cands = [f"{slug}_{s}" for s in SCENARIOS if f"{slug}_{s}" in by_inst]
            if len(cands) == 1:
                corr_r.append(f"relation : {slug!r} complété en {cands[0]!r}")
                return by_inst[cands[0]]
            return None
        a, b = _entite(r.get("a")), _entite(r.get("b"))
        if not a or not b or a is b:
            zones_vues = [s for s in (r.get("a"), r.get("b")) if s in by_zone]
            if zones_vues:
                ecartees.append(f"relation {r.get('a')} / {r.get('b')} : {' et '.join(map(repr, zones_vues))} "
                                f"{'sont des zones' if len(zones_vues) > 1 else 'est une zone'} "
                                f"(une relation relie deux entités)")
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
            corr_r.append(f"relation {a['slug']} / {b['slug']} : action absente -> nouvelle")
            action = "nouvelle"
        elif action.startswith("renforc"):
            if existe:
                ecartees.append(f"relation {a['slug']} / {b['slug']} : {typ} déjà présente "
                                f"(proposée comme renforcée, rien à changer)")
                continue
            corr_r.append(f"relation {a['slug']} / {b['slug']} : renforcée -> nouvelle (absente du vault)")
            action = "nouvelle"
        if action not in ("nouvelle", "rompue"):
            ecartees.append(f"relation {a['slug']} / {b['slug']} : action {r.get('action')!r} invalide")
            continue
        if action == "nouvelle" and existe:
            ecartees.append(f"relation {a['slug']} / {b['slug']} : {typ} déjà présente")
            continue
        if action == "rompue" and not existe:
            ecartees.append(f"relation {a['slug']} / {b['slug']} : {typ} à rompre absente du vault")
            continue
        corrigees.extend(corr_r)
        rel.append({"a": a["slug"], "a_nom": a.get("name"), "b": b["slug"], "b_nom": b.get("name"),
                    "type": typ, "action": action, "raison": str(r.get("raison") or "")})
    out["relations"] = rel

    geo, pays_vus = [], set()
    for g in liste("geographie"):
        action = str(g.get("action") or "")
        pays = str(g.get("pays") or "").strip()
        if not pays or (action not in ACTIONS_GEO and action not in ("partition", "region")):
            ecartees.append(f"carte : proposition incomplète ({pays or '?'} / {action or '?'})")
            continue
        if _plie(pays) in pays_vus:
            # V5 : deux destinations pour un même pays se contredisent ; la première est gardée.
            ecartees.append(f"carte : {pays} a déjà une proposition (seconde destination "
                            f"{g.get('zone') or (g.get('nouvelle_zone') or {}).get('slug')!r} ignorée)")
            continue
        pays_vus.add(_plie(pays))
        if action == "partition":
            errs = []
            part = normaliser_partition(g, f"carte : partition de {pays}", errs)
            inconnues = [p["zone"] for p in (part or {}).get("parties", [])
                         if p["zone"] and p["zone"] not in by_zone]
            if part is None or inconnues:
                ecartees += errs or [f"carte : partition de {pays}, zone(s) inconnue(s) {inconnues}"]
                continue
            racines = [p["nouvelle_zone"]["slug"] if p["nouvelle_zone"] else _racine_n1(p["zone"], by_zone)
                       for p in part["parties"]]
            if len(set(racines)) != len(racines):
                ecartees.append(f"carte : partition de {pays} écartée, deux parties dans la même zone de "
                                f"niveau 1 (contestation interne, pas un changement de contrôle)")
                continue
            geo.append({"pays": pays, "action": "partition", "zone": "", "nouvelle_zone": None,
                        **part, "raison": str(g.get("raison") or "")})
            continue
        if action == "region":
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
        if action == "absorber" and g.get("zone") not in by_zone:
            ecartees.append(f"carte : zone {g.get('zone')!r} inconnue pour {pays}")
            continue
        nz = g.get("nouvelle_zone") if isinstance(g.get("nouvelle_zone"), dict) else None
        if action == "nouvelle_zone" and not (nz and nz.get("slug") and nz.get("nom")):
            ecartees.append(f"carte : nouvelle zone sans slug/nom pour {pays}")
            continue
        geo.append({"pays": pays, "action": action, "zone": str(g.get("zone") or ""),
                    "nouvelle_zone": nz if action == "nouvelle_zone" else None, "raison": str(g.get("raison") or "")})
    out["geographie"] = geo

    zs = []
    for z in liste("zones_statut"):
        zone = by_zone.get(z.get("zone"))
        apres = _valeur_canonique(z.get("apres"), statuts) or str(z.get("apres") or "")
        if not zone or apres not in statuts:
            ecartees.append(f"statut de zone : {z.get('zone')!r} → {apres!r} invalide")
        elif apres == zone.get("statut"):
            ecartees.append(f"statut de zone : {z.get('zone')} déjà {apres}")
        else:
            zs.append({"zone": zone.get("slug"), "nom": zone.get("nom"), "avant": zone.get("statut"),
                       "apres": apres, "raison": str(z.get("raison") or "")})
    out["zones_statut"] = zs

    ne = []
    # V8.10 : zones créées par la carte de la même lecture (nouvelle zone, région, partie d'une partition).
    zones_creees = set()
    for g in geo:
        if (g.get("nouvelle_zone") or {}).get("slug"):
            zones_creees.add(g["nouvelle_zone"]["slug"])
        for p in g.get("parties") or []:
            if (p.get("nouvelle_zone") or {}).get("slug"):
                zones_creees.add(p["nouvelle_zone"]["slug"])
    for n in liste("nouvelles_entites"):
        if not n.get("nom"):
            continue
        zone = n.get("zone")
        if zone and _plie(str(zone)).rstrip("e") == "transnational":
            zone = "transnationale"   # V7.9 : valeur normale du vault
        elif zone and zone not in by_zone and zone in zones_creees:
            corrigees.append(f"nouvelle entité {n.get('nom')} : zone {zone!r} à créer par la carte "
                             f"(à placer après sa création)")
        elif zone and zone not in by_zone:
            ecartees.append(f"nouvelle entité {n.get('nom')} : zone {zone!r} inconnue (gardée sans zone)")
            zone = None
        ne.append({"nom": str(n["nom"]), "role": str(n.get("role") or ""), "zone": zone,
                   "raison": str(n.get("raison") or "")})
    out["nouvelles_entites"] = ne
    out["ecartees"] = ecartees
    out["corrigees"] = corrigees
    return out


def ajouter_consequences(hyp, resultats, scenarios, refaire=False):
    """Étage B pour chaque scénario ; les changements de carte proposés par l'IA
    alimentent le bloc geographie quand l'utilisateur n'en a pas écrit pour ce
    scénario (une saisie manuelle reste prioritaire)."""
    out = {}
    for sc in scenarios:
        effets = (resultats.get(sc) or {}).get("effets") or []
        try:
            out[sc] = lire_consequences(hyp, sc, effets, refaire=refaire)
        except Exception as e:
            out[sc] = {"erreur": f"{type(e).__name__}: {e}"}
            continue
        if not hyp.get("carte", True) and out[sc].get("geographie"):
            out[sc]["ecartees"] = (out[sc].get("ecartees") or []) + [
                f"carte : {g['pays']} ({g['action']}) écartée, hypothèse sans effet territorial (`carte: non`)"
                for g in out[sc]["geographie"]]
            out[sc]["geographie"] = []
        # V7.5 : une zone disparue est un changement de carte déguisé.
        if not hyp.get("carte", True) and out[sc].get("zones_statut"):
            disparues = [z for z in out[sc]["zones_statut"] if z.get("apres") == "disparu"]
            if disparues:
                out[sc]["ecartees"] = (out[sc].get("ecartees") or []) + [
                    f"statut de zone : {z['zone']} → disparu écarté, hypothèse sans effet territorial (`carte: non`)"
                    for z in disparues]
                out[sc]["zones_statut"] = [z for z in out[sc]["zones_statut"] if z.get("apres") != "disparu"]
        if out[sc].get("geographie") and sc not in hyp["geographie"]:
            hyp["geographie"][sc] = [dict(g, source="ia") for g in out[sc]["geographie"]]
    return out


# ---------------------------------------------------------------------------
# Récit et rendu
# ---------------------------------------------------------------------------

def ajouter_recits(hyp, resultats, ia=False):
    import trace_injection as ti
    trace = {"slug": hyp["id"], "nom": hyp["nom"], "type": "élément hypothétique",
             "description": hyp["description"], "instances": []}
    for sc, r in resultats.items():
        if ia:
            r["recit"], r["recit_source"] = ti.recit_llm(trace, sc, r["chronologie"], None)
        else:
            r["recit"], r["recit_source"] = ti.recit_modele(hyp["nom"], sc, r["chronologie"]), "modele"


def _virgule(x, signe=True):
    return (f"{x:+.1f}" if signe else f"{x:.1f}").replace(".", ",")



def _rendre_partition(g):
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


def _rendre_region(g):
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


def _rendre_geo(ops):
    L = ["### Carte (aperçu, rien n'est modifié)", ""]
    for g in ops:
        if g["action"] == "partition":
            L += _rendre_partition(g)
            continue
        if g["action"] == "region":
            L += _rendre_region(g)
            continue
        verbe = (f"rattaché à `{g['cible']}`" if g["action"] == "absorber"
                 else f"placé dans une nouvelle zone `{g['cible']}`")
        L.append(f"**{g['pays']}** {verbe}")
        for e in g["erreurs"]:
            L.append(f"- ✗ {e}")
        for a in g["alertes"]:
            L.append(f"- ⚠ {a}")
        if g["erreurs"]:
            L.append("")
            continue
        if g["actuelles"]:
            L.append("- Aujourd'hui : " + ", ".join(
                f"`{a['slug']}`" + (" (portion dessinée)" if a["type"] == "overlay" else "")
                for a in g["actuelles"]))
        for q in g["quittees"]:
            txt = f"- Zone quittée `{q['slug']}`"
            if q["videe"]:
                txt += " : n'aurait **plus aucun territoire**"
            if q["redaction"]:
                txt += (" ; ses journaux (journaux.yaml) resteraient sans territoire" if q["videe"]
                        else " ; a ses propres journaux")
            L.append(txt)
        if g["redaction_cible"] is False:
            L.append("- Zone d'arrivée sans rédaction : journaux à créer (`generate_journaux.py --update`)")
        imp = g["impact"] or {}
        for cle, titre in (("sous_zones_orphelines", "Sous-zones qui deviendraient orphelines"),
                           ("instances_liees", "Instances et événements des sous-zones du pays"),
                           ("mentions_texte", f"Fiches qui citent {g['pays']} dans leur texte"),
                           ("registre_hits", "Lignes du registre des événements qui le citent")):
            items = imp.get(cle) or []
            if not items:
                continue
            L.append(f"- {titre} : **{len(items)}**")
            for it in items[:MAX_LISTE]:
                if isinstance(it, dict):
                    L.append(f"  - `{it.get('slug')}`" + (f" — {it.get('extrait') or it.get('zone') or it.get('origine') or ''}"))
                else:
                    L.append(f"  - {str(it)[:160]}")
            if len(items) > MAX_LISTE:
                L.append(f"  - … et {len(items) - MAX_LISTE} autre(s)")
        if imp.get("rien_detecte"):
            L.append("- Aucune fiche, sous-zone ou ligne du registre touchée.")
        if imp.get("instances_autres"):
            L.append(f"- Autres instances des zones concernées, sans lien avec {g['pays']} : "
                     f"{imp['instances_autres']} (non listées)")
        L.append("")
    return L


def _rendre_consequences(c):
    L = ["### Lecture des conséquences (IA, propositions vérifiées — rien n'est écrit)", ""]
    if c.get("erreur"):
        return L + [f"_Lecture impossible : {c['erreur']}_", ""]
    if c.get("depuis_cache"):
        L += ["_(résultat repris du cache : même hypothèse, mêmes effets — `--refaire` pour relancer)_", ""]
    if c.get("lecture"):
        L += [f"{c['lecture']}" + (f" _(ampleur : {c['ampleur']})_" if c.get("ampleur") else ""), ""]
    if c.get("trajectoires"):
        L.append("**Trajectoires d'entités**")
        for t in c["trajectoires"]:
            L.append(f"- {t['nom']} (`{t['instance']}`) : {t['avant']} → **{t['apres']}** — {t['raison']}")
        L.append("")
    if c.get("relations"):
        L.append("**Relations**")
        for r in c["relations"]:
            verbe = "nouvelle" if r["action"] == "nouvelle" else "rompue"
            L.append(f"- {r['type']} {verbe} : {r['a_nom']} ↔ {r['b_nom']} — {r['raison']}")
        L.append("")
    if c.get("zones_statut"):
        L.append("**Statut des zones**")
        for z in c["zones_statut"]:
            L.append(f"- {z['nom']} (`{z['zone']}`) : {z['avant']} → **{z['apres']}** — {z['raison']}")
        L.append("")
    if c.get("geographie"):
        L.append("**Carte** (détail de l'impact dans la section Carte ci-dessous)")
        for g in c["geographie"]:
            if g["action"] == "partition":
                cible = " + ".join(p["zone"] or (p["nouvelle_zone"] or {}).get("slug", "?") for p in g["parties"])
            else:
                cible = g["zone"] if g["action"] == "absorber" else (g["nouvelle_zone"] or {}).get("slug")
            L.append(f"- {g['pays']} : {g['action']} → `{cible}` — {g['raison']}")
        L.append("")
    if c.get("nouvelles_entites"):
        L.append("**Nouvelles entités plausibles**")
        for n in c["nouvelles_entites"]:
            L.append(f"- {n['nom']}" + (f" ({n['zone']})" if n.get("zone") else "") + f" : {n['role']} — {n['raison']}")
        L.append("")
    if c.get("corrigees"):
        L.append(f"_Corrections automatiques ({len(c['corrigees'])}) : " + " ; ".join(c["corrigees"][:8])
                 + (" …" if len(c["corrigees"]) > 8 else "") + "_")
        L.append("")
    if c.get("ecartees"):
        L.append(f"_Propositions écartées au contrôle ({len(c['ecartees'])}) : " + " ; ".join(c["ecartees"][:8])
                 + (" …" if len(c["ecartees"]) > 8 else "") + "_")
        L.append("")
    return L

def _rendre_passe(p):
    """V8.16 : section du rapport produite par et_si_exhaustif.rendre()."""
    import et_si_exhaustif as ex
    return ex.rendre(p)


def rendre_markdown(hyp, resultats, date_fin, avert, geo=None, consequences=None, application=None,
                    passe=None):
    L = [f"# Et si ? — {hyp['nom']}", "",
         f"*Simulation du {datetime.now().strftime('%Y-%m-%d %H:%M')} — lecture seule, rien n'a été injecté (simulateur {VERSION}).*", ""]
    if hyp["description"]:
        L += [hyp["description"], ""]
    if hyp.get("contraintes"):
        L += ["**Faits imposés à la lecture IA** :"] + [f"- {c}" for c in hyp["contraintes"]] + [""]
    pers_txt = ("— (mode **rupture** : l'équilibre du scénario est déplacé pour de bon)"
                if hyp.get("mode") == "rupture" else hyp["persistance"])
    L += [f"- **Apparition** : {hyp['date']:g} · **Persistance** : {pers_txt} · "
          f"**Propagation par la matrice** : {'oui' if hyp['via_matrice'] else 'non'}",
          f"- **Effet mesuré en** : {date_fin:g}"]
    if not hyp.get("carte", True):
        L.append("- **Carte** : élément déclaré sans effet territorial (`carte: non`), "
                 "aucune proposition de carte retenue")
    for imp in hyp["impacts"]:
        sens = sorted(set(imp["polarites"].values()))
        sens_txt = ("aggrave ↑" if sens == [1] else "apaise ↓" if sens == [-1] else "sens variable selon le scénario")
        L.append(f"- Déclaré : **{imp['variable']}** — force {imp['force']:g}, {sens_txt}, montée sur {imp['duree']:g} ans")
    for a in avert:
        L.append(f"- ⚠ {a}")
    L += ["", "Rappel : niveau 100 = crise maximale. Écart = niveau AVEC l'hypothèse − niveau SANS elle, "
          "toutes les injections existantes restant en place.", ""]

    geo = geo or {}
    consequences = consequences or {}
    application = application or {}
    passe = passe or {}
    for sc in SCENARIOS:
        r = resultats.get(sc)
        if not r and sc not in geo and sc not in consequences:
            continue
        L += [f"## {sc}", ""]
        if not r:
            if sc in consequences:
                L += _rendre_consequences(consequences[sc])
            if sc in passe:
                L += _rendre_passe(passe[sc])
            if sc in geo:
                L += _rendre_geo(geo[sc])
            if sc in application:
                L += _rendre_application(application[sc], hyp, sc)
            continue
        if r.get("recit"):
            L += [r["recit"], ""]
            if r.get("recit_source", "").startswith("modele"):
                L += ["_(récit construit par le script)_", ""]
        if not r["effets"]:
            L += ["Effet en fin de période : négligeable (< 0,1 point, choc absorbé ou variables à leur plafond).", ""]
        else:
            L += ["| Variable | Référence | Sans | Avec | Écart | |", "|---|---|---|---|---|---|"]
            for e in r["effets"]:
                ref_txt = _virgule(e['reference'], False)
                if abs(e.get("reference_apres", e["reference"]) - e["reference"]) >= 0.1:
                    ref_txt += f" → {_virgule(e['reference_apres'], False)}"
                L.append(f"| {e['variable']} | {ref_txt} | {_virgule(e['sans'], False)} | "
                         f"{_virgule(e['avec'], False)} | **{_virgule(e['effet'])}** | {e['mode']} |")
            L.append("")
        pics = [p for p in r["chronologie"]["reperes"] if abs(p["pic"]) >= 0.3][:4]
        if pics:
            L.append("**Repères** :")
            for p in pics:
                txt = f"- {p['variable']} ({p['mode']}) : pic {_virgule(p['pic'])} vers {p['annee_pic']:.0f}"
                if p["mode"] == "propagé" and p["retard"] is not None:
                    txt += f", réagit {p['retard']:.0f} ans après l'apparition"
                if p["contrecoup"] is not None:
                    txt += f", contrecoup {_virgule(p['contrecoup'])} vers {p['annee_contrecoup']:.0f}"
                L.append(txt)
            L.append("")
        nt = r["nb_tensions"]
        L.append(f"**Tensions** : {nt['sans']} sans l'hypothèse → {nt['avec']} avec.")
        for t in r["tensions_apparues"]:
            L.append(f"- ➕ apparaît : {t['description']}")
        for t in r["tensions_aggravees"]:
            L.append(f"- ⬆ devient une cascade critique : {t['source']} → {t['target']}")
        for t in r["tensions_disparues"]:
            L.append(f"- ➖ disparaît : {t['description']}")
        for t in r["tensions_attenuees"]:
            L.append(f"- ⬇ n'est plus une cascade critique : {t['source']} → {t['target']}")
        if nt["sans"] != nt["avec"] or r["tensions_aggravees"] or r["tensions_attenuees"]:
            L.append("_Une tension se déclenche quand un niveau franchit un seuil (60, ou 70 pour une "
                     "cascade, abaissés selon le risque de bascule de la variable) : un écart de quelques "
                     "dixièmes peut suffire si le niveau était déjà au bord._")
        L.append("")
        if sc in consequences:
            L += _rendre_consequences(consequences[sc])
        if sc in passe:
            L += _rendre_passe(passe[sc])
        if sc in geo:
            L += _rendre_geo(geo[sc])
        if sc in application:
            L += _rendre_application(application[sc], hyp, sc)
    L += _rendre_injection_commune(hyp, application)
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# Liste d'application (phase 3, v8, 10 octobre 2026 ; v8.1 à v8.14)
# ---------------------------------------------------------------------------
# Tout ce que l'hypothèse imposerait de changer, scénario par scénario, dans
# l'ordre, avec l'outil à lancer ou « à la main ». Lecture seule, aucun appel
# IA : construite à partir des résultats déjà calculés (niveaux, lecture IA
# gardée, carte évaluée) et de trois scans du vault (instances / événements
# localisés, articles, rédactions de journaux.yaml).

SECTIONS_APPLICATION = ["Carte", "Localisation des fiches", "Journaux", "Statuts de zone",
                        "Élément", "Nouvelles entités", "Trajectoires", "Relations", "Lore",
                        "Fiches à relire", "Possibles (facultatif)", "Articles et site", "Contrôles"]
TRAJ_TERMINALES = {"transformé", "disparu", "historique", "mythifié"}


def _frontmatter_fichier(path):
    import re as _re
    try:
        txt = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = _re.match(r"^---\s*\n(.*?)\n---\s*\n", txt, _re.DOTALL)
    if not m:
        return {}
    try:
        fm = yaml.safe_load(_re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))) or {}
    except yaml.YAMLError:
        return {}
    return fm if isinstance(fm, dict) else {}


def _titre_corps(path):
    """V8.1 : premier titre du corps (# Titre ou **Titre**)."""
    import re as _re
    try:
        txt = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    corps = _re.sub(r"^---\s*\n.*?\n---\s*\n", "", txt, count=1, flags=_re.DOTALL)
    for ligne in corps.splitlines():
        ligne = ligne.strip()
        m = _re.match(r"^(?:#+\s*(.+)|\*\*(.+?)\*\*)$", ligne)
        if m:
            return (m.group(1) or m.group(2)).strip()
        if ligne:
            break
    return ""


def _articles_scenario(sc):
    """Articles du scénario (racine et sous-dossiers, scénario lu dans le
    frontmatter, _index.md ignoré)."""
    racine = VAULT_ROOT / "articles"
    out = []
    if not racine.is_dir():
        return out
    for p in sorted(racine.rglob("*.md")):
        if p.name == "_index.md":
            continue
        fm = _frontmatter_fichier(p)
        if fm.get("scenario") != sc:
            continue
        try:
            texte = p.read_text(encoding="utf-8")
        except OSError:
            texte = ""
        ent = fm.get("entites_citees") or []
        out.append({"fichier": p.name, "chemin": str(p.relative_to(VAULT_ROOT)),
                    "titre": str(fm.get("titre") or _titre_corps(p) or fm.get("slug") or p.stem),
                    "zone": fm.get("zone_principale") or "",
                    "entites": [str(e) for e in ent] if isinstance(ent, list) else [],
                    "texte": _plie(texte)})   # V8.2 : pour chercher le pays cité
    return out


def _redactions_scenario(sc):
    """{zone: [{"ligne", "nom", "type_diffusion"}]} depuis journaux.yaml (None si illisible)."""
    try:
        data = yaml.safe_load((SCRIPT_DIR / "journaux.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    out = {}
    for ligne, contenu in (data.get(sc) or {}).items():
        if not isinstance(contenu, dict) or not isinstance(contenu.get("zones"), dict):
            continue
        for zone, z in contenu["zones"].items():
            z = z if isinstance(z, dict) else {}
            out.setdefault(zone, []).append({"ligne": ligne, "nom": z.get("nom") or "?",
                                             "type_diffusion": z.get("type_diffusion") or "ecrit"})
    return out


def _donnees_application(sc):
    """Les trois scans du vault ; une source illisible donne une liste vide et un avertissement."""
    d = {"instances": [], "evenements": [], "articles": [], "redactions": None, "avert": [], "zones": []}
    try:   # V8.4 : zones chargées une fois (sous-zones citées, recherche de citations)
        repo, _ = charger_zone_repository()
        d["zones"] = repo.load_all_zones(sc) or []
    except Exception as e:
        d["avert"].append(f"zones illisibles : {type(e).__name__}: {e}")
    try:
        from loader import load_instances_for_scenario, load_event_instances_for_scenario
        d["instances"] = load_instances_for_scenario(sc)
        d["evenements"] = load_event_instances_for_scenario(sc)
    except Exception as e:
        d["avert"].append(f"instances / événements illisibles : {type(e).__name__}: {e}")
    try:
        d["articles"] = _articles_scenario(sc)
    except Exception as e:
        d["avert"].append(f"articles illisibles : {type(e).__name__}: {e}")
    d["redactions"] = _redactions_scenario(sc)
    if d["redactions"] is None:
        d["avert"].append("journaux.yaml illisible : la section Journaux est incomplète")
    return d



# --- V8.3 : fiches qui citent les pays, villes ou noms propres de l'hypothèse ---
MAX_FICHES = 25            # fiches listées par type (le reste est compté)
MOTS_GENERIQUES = {"Invasion", "Conflit", "Crise", "Guerre", "Effondrement", "Percée", "Fusion",
                   "Peste", "Pandémie", "Montée", "Victoire", "Chute", "Arrivée", "Majorité",
                   "États", "Etats", "État", "Etat", "Nations", "République", "Royaume"}
# V8.14 : nom français des villes dont le nom anglais (villes_principales.json) diffère ;
# les deux noms sont cherchés.
VILLES_FR = {"Mexico City": ["Mexico"],
    "Cairo": ["Le Caire"],
    "Beijing": ["Pékin"],
    "Moscow": ["Moscou"],
    "London": ["Londres"],
    "Tehran": ["Téhéran"],
    "Bengaluru": ["Bangalore"],
    "Singapore": ["Singapour"],
    "Baghdad": ["Bagdad"],
    "Barcelona": ["Barcelone"],
    "St. Petersburg": ["Saint-Pétersbourg"],
    "Riyadh": ["Riyad"],
    "Washington, D.C.": ["Washington"],
    "Alexandria": ["Alexandrie"],
    "Rangoon": ["Rangoun"],
    "Xian": ["Xi'an"],
    "Algiers": ["Alger"],
    "Kabul": ["Kaboul"],
    "Athens": ["Athènes"],
    "Cape Town": ["Le Cap"],
    "Tel Aviv-Yafo": ["Tel-Aviv", "Tel Aviv"],
    "Addis Ababa": ["Addis-Abeba"],
    "Jeddah": ["Djeddah"],
    "Frankfurt": ["Francfort"],
    "Lisbon": ["Lisbonne"],
    "Aleppo": ["Alep"],
    "Kiev": ["Kyiv"],
    "El Giza": ["Gizeh"],
    "Damascus": ["Damas"],
    "Vienna": ["Vienne"],
    "Tashkent": ["Tachkent"],
    "Havana": ["La Havane"],
    "Santo Domingo": ["Saint-Domingue"],
    "Baku": ["Bakou"],
    "Kuwait City": ["Koweït"],
    "Ad Damman": ["Dammam"],
    "Bucharest": ["Bucarest"],
    "Beirut": ["Beyrouth"],
    "Brussels": ["Bruxelles"],
    "Warsaw": ["Varsovie"],
    "Kharkiv": ["Kharkov"],
    "The Hague": ["La Haye"],
    "Makkah": ["La Mecque"],
    "Mosul": ["Mossoul"],
    "Yekaterinburg": ["Iekaterinbourg"],
    "Shiraz": ["Chiraz"],
    "Geneva": ["Genève"],
    "Tbilisi": ["Tbilissi"],
    "Kobenhavn": ["Copenhague"],
    "Ufa": ["Oufa"],
    "Medina": ["Médine"],
    "Hims": ["Homs"],
    "Fez": ["Fès"],
    "Ndjamena": ["N'Djamena"],
    "Irbil": ["Erbil"],
    "Krasnoyarsk": ["Krasnoïarsk"],
    "Antwerpen": ["Anvers"],
    "Kathmandu": ["Katmandou"],
    "Ulaanbaatar": ["Oulan-Bator"],
    "Marrakesh": ["Marrakech"],
    "Basra": ["Bassorah"],
    "Palermo": ["Palerme"],
    "Voronezh": ["Voronej"],
    "Bishkek": ["Bichkek"],
    "Thessaloniki": ["Thessalonique"],
    "Zaporizhzhya": ["Zaporijia"],
    "Krakow": ["Cracovie"],
    "Muscat": ["Mascate"],
    "Ashgabat": ["Achgabat"],
    "Abu Dhabi": ["Abou Dabi"],
    "Valletta": ["La Valette"],
    "Bern": ["Berne"],
    "Nicosia": ["Nicosie"],
    "Velikiy Novgorod": ["Novgorod"],
    "Thimphu": ["Thimphou"],
    "Andorra": ["Andorre-la-Vieille"],
    "Vatican City": ["Vatican"],
    "San Marino": ["Saint-Marin"],
    "Mogadishu": ["Mogadiscio"],
    "Dushanbe": ["Douchanbé"],
    "Yerevan": ["Erevan"],
    "Nizhny Novgorod": ["Nijni Novgorod"],
    "Chelyabinsk": ["Tcheliabinsk"],
    "Hamburg": ["Hambourg"],
    "Ho Chi Minh City": ["Hô Chi Minh-Ville", "Saïgon"],
    "Mumbai": ["Bombay"],
    "Kolkata": ["Calcutta"],
    "Chennai": ["Madras"],
    "Guangzhou": ["Canton"],
    "Shenyeng": ["Shenyang"],
    "Nanjing": ["Nankin"],
    "Panama City": ["Panama"],
    "Philadelphia": ["Philadelphie"],
    "New Orleans": ["La Nouvelle-Orléans"],
    "Banghazi": ["Benghazi"],
    "Dhaka": ["Dacca"],
    "Chattogram": ["Chittagong"],
    "Naypyidaw": ["Naypyidaw"],
    "Seville": ["Séville"],
    "Munich": ["Munich"]}

# V8.11 : noms géographiques communs, cherchés avec le mot qui suit (« Golfe persique »,
# pas « Golfe », qui trouverait aussi le golfe de Finlande).
NOMS_GEO_COMPOSES = {"Golfe", "Mer", "Océan", "Detroit", "Détroit", "Canal", "Lac", "Baie", "Cap",
                     "Île", "Ile", "Mont", "Monts", "Plateau", "Bassin", "Delta", "Corne"}


def _plie_aligne(texte):
    """Minuscules sans accents, un caractère pour un caractère (positions conservées)."""
    import unicodedata
    out = []
    for c in str(texte or ""):
        d = unicodedata.normalize("NFKD", c.lower())
        base = next((x for x in d if not unicodedata.combining(x)), c.lower())
        out.append(base if len(base) == 1 else c.lower())
    return "".join(out)


_PAYS_CONNUS = None


def _pays_connus():
    """V8.5 : noms de pays (français) de gui/static/pays_mapping.json, en cache."""
    global _PAYS_CONNUS
    if _PAYS_CONNUS is None:
        try:
            _PAYS_CONNUS = list(json.loads((VAULT_ROOT / "gui" / "static" / "pays_mapping.json")
                                           .read_text(encoding="utf-8")))
        except (OSError, ValueError):
            _PAYS_CONNUS = []
    return _PAYS_CONNUS


def _autres_pays(entite, pays):
    """Pays (autres que `pays`) nommés dans une entrée origine_reelle ; une ville ou une
    région du même pays n'en est pas un."""
    import re as _re
    e = _plie_aligne(entite)
    pp = _plie_aligne(pays)
    # V8.6 : « États-Unis » et « États-Unis d'Amérique » désignent le même pays.
    return [p for p in _pays_connus() if _plie_aligne(p) not in pp and pp not in _plie_aligne(p)
            and _re.search(r"(?<![a-z0-9])" + _re.escape(_plie_aligne(p)) + r"(?![a-z0-9])", e)]


def _termes_hypothese(hyp, sc, geo_ops, zones=None):
    """{terme: origine} : pays dont la carte change (et leurs grandes villes), pays cités
    dans le nom ou la description, noms propres de l'hypothèse."""
    import re as _re
    termes = {}
    try:
        mapping = json.loads((VAULT_ROOT / "gui" / "static" / "pays_mapping.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        mapping = {}
    try:
        villes = json.loads((VAULT_ROOT / "gui" / "static" / "villes_principales.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        villes = []
    ops_hyp = (hyp.get("geographie") or {}).get(sc) or []
    pays_carte = [op["pays"] for op, g in zip(ops_hyp, geo_ops or []) if not g.get("erreurs")]
    for p in pays_carte:
        termes.setdefault(p, "pays dont la carte change")
        en = mapping.get(p)
        for v in villes if en else []:
            if isinstance(v, dict) and v.get("nom") and str(v.get("pays", "")) == en:
                termes.setdefault(v["nom"], f"ville ({p})")
                for fr in VILLES_FR.get(v["nom"], []):   # V8.14
                    termes.setdefault(fr, f"ville ({p})")
        # V8.14 : lieux que le vault connaît déjà pour ce pays : nom court des sous-zones qui
        # le portent (« Sertão — Nordeste Brésilien » → « Sertão »). Servent aux fiches à relire.
        pp = _plie_aligne(p)
        for z in zones or []:
            if (z.get("niveau") or 1) < 2:
                continue
            terr = " ; ".join(str(x.get("entite")) for x in (z.get("origine_reelle") or [])
                              if isinstance(x, dict) and x.get("entite"))
            if not _re.search(r"(?<![a-z0-9])" + _re.escape(pp) + r"(?![a-z0-9])", _plie_aligne(terr)):
                continue
            court = _re.split(r"\s+[—–-]\s+|\s*\(", str(z.get("nom") or ""))[0].strip()
            if (4 <= len(court) and len(court.split()) <= 3 and court not in MOTS_GENERIQUES
                    and _plie_aligne(court) != pp):
                termes.setdefault(court, f"lieu du vault ({p})")
    texte_h = f"{hyp.get('nom', '')} {hyp.get('description', '')}"
    plie_h = _plie_aligne(texte_h)
    for p in mapping:
        if _re.search(r"(?<![a-z0-9])" + _re.escape(_plie_aligne(p)) + r"(?![a-z0-9])", plie_h):
            termes.setdefault(p, "pays cité par l'hypothèse")
    for texte_part in (hyp.get("nom", ""), hyp.get("description", "")):
        for m in _re.finditer(r"\b[A-ZÉÈÀÂÎÔÛÇ][\wéèêàâîôûçë'-]{3,}", str(texte_part)):
            avant = str(texte_part)[:m.start()]
            # Un mot qui ouvre une phrase n'est pas forcément un nom propre (« Pression sur… »).
            debut_phrase = not avant.strip() or _re.search(r"[.!?:;]\s*$", avant)
            # V8.8 : second membre d'un mot composé (« pétro-États ») : pas un nom propre.
            compose = avant.endswith("-")
            if m.group(0) in NOMS_GEO_COMPOSES:
                suite = _re.match(r"\s+((?:d[eu']\s*|des\s+|de\s+la\s+)?[\wéèêàâîôûçë'-]{3,})", str(texte_part)[m.end():])
                if suite:
                    termes.setdefault(m.group(0) + " " + " ".join(suite.group(1).split()), "nom cité par l'hypothèse")
                continue
            if m.group(0) not in MOTS_GENERIQUES and not debut_phrase and not compose:
                termes.setdefault(m.group(0), "nom cité par l'hypothèse")
    # V8.8 : un même terme écrit deux fois (« Arabie Saoudite » / « Arabie saoudite ») : le premier reste ;
    # un nom propre isolé contenu dans un terme plus long (« Arabie » ⊂ « Arabie saoudite ») : retiré.
    vus, uniques = set(), {}
    for t, o in termes.items():
        k = " ".join(_plie_aligne(t).split())
        if k not in vus:
            vus.add(k)
            uniques[t] = o
    plies = {t: " ".join(_plie_aligne(t).split()) for t in uniques}
    return {t: o for t, o in uniques.items()
            if not (o == "nom cité par l'hypothèse"
                    and any(u != t and _re.search(r"(?<![a-z0-9])" + _re.escape(plies[t]) + r"(?![a-z0-9])", plies[u])
                            for u in uniques))}


def _homonymes_pays(termes):
    """V8.7 : villes qui portent aussi le nom d'un pays (Salvador / El Salvador).
    On ne les cherche pas dans une liste de territoires, où elles désignent le pays."""
    import re as _re
    pays_plies = set()
    for p in _pays_connus():
        fp = " ".join(_re.sub(r"[^a-z0-9]+", " ", _plie_aligne(p)).split())
        pays_plies.add(fp)
        # « El Salvador », « Salvador (El) », « Salvador, El » → « salvador »
        pays_plies.add(_re.sub(r"^(el|le|la|les) | (el|le|la|les)$", "", fp))
    return {t for t, o in termes.items() if str(o).startswith("ville (") and " ".join(_re.sub(r"[^a-z0-9]+", " ", _plie_aligne(t)).split()) in pays_plies}


def _trouve(texte, termes_plies):
    """Premier terme trouvé (mot entier) dans texte : (terme, extrait) ou None."""
    import re as _re
    if not texte:
        return None
    plie = _plie_aligne(texte)
    for terme, motif_re in termes_plies:
        m = motif_re.search(plie)
        if m:
            debut = max(0, m.start() - 60)
            extrait = " ".join(str(texte)[debut:m.end() + 80].split())
            return terme, ("…" if debut else "") + extrait + "…"
    return None


def fiches_citant(hyp, sc, geo_ops, donnees):
    """Instances, événements, zones et lignes du registre (après la date de l'hypothèse)
    qui citent un des termes. Retourne {type: [{"slug", "terme", "extrait"}]} et les termes."""
    import re as _re
    termes = _termes_hypothese(hyp, sc, geo_ops, donnees.get("zones"))
    if not termes:
        return {}, termes
    termes_plies = [(t, _re.compile(r"(?<![a-z0-9])" + _re.escape(_plie_aligne(t)) + r"(?![a-z0-9])"))
                    for t in sorted(termes, key=len, reverse=True)]
    homonymes = _homonymes_pays(termes)
    plies_terr = [(t, m) for t, m in termes_plies if t not in homonymes]
    out = {"Instances": [], "Événements": [], "Zones": [], "Registre (après la date)": []}

    def _ajoute(type_, slug, champs, territoires=None):
        for k, champ in enumerate(champs):
            r = _trouve(champ, plies_terr if k == territoires else termes_plies)
            if r:
                out[type_].append({"slug": slug, "terme": r[0], "extrait": r[1]})
                return

    for i in donnees["instances"]:
        _ajoute("Instances", i.get("slug"), [i.get("name"), i.get("role_dans_scenario"), i.get("responsabilites"),
                                            i.get("description_journalistique"), i.get("tensions_narratives"),
                                            i.get("signes_distinctifs"), (i.get("localisation") or {}).get("lieu")])
    for ev in donnees["evenements"]:
        _ajoute("Événements", ev.get("slug"), [ev.get("name"), ev.get("description"), ev.get("consequences"),
                                              ev.get("realisation")])
    for z in donnees.get("zones") or []:
        lieux = " ; ".join(str(l.get("nom") if isinstance(l, dict) else l)
                           for l in (z.get("lieux_emblematiques") or []))
        origines = " ; ".join(str(o.get("entite")) for o in (z.get("origine_reelle") or []) if isinstance(o, dict))
        _ajoute("Zones", z.get("slug"), [z.get("nom"), origines, z.get("description"), z.get("tensions_internes"), lieux],
                territoires=1)
    try:
        texte = (SCRIPT_DIR / "registre_evenements.md").read_text(encoding="utf-8")
        m = _re.search(r"^##\s+" + _re.escape(sc) + r"\s*$(.*?)(?=^##\s|\Z)", texte, _re.M | _re.S)
        for ligne in (m.group(1).splitlines() if m else []):
            if not ligne.startswith("|") or _re.match(r"^\|[\s:|-]+\|?$", ligne):
                continue
            annees = [int(a) for a in _re.findall(r"\b(20\d\d)\b", ligne)]
            if annees and min(annees) > hyp["date"]:
                cellules = [c.strip() for c in ligne.strip("|").split("|")]
                _ajoute("Registre (après la date)", " | ".join(c for c in cellules[:3] if c)[:90], [ligne])
    except OSError:
        donnees["avert"].append("registre_evenements.md introuvable : chronologie non vérifiée")
    return {k: v for k, v in out.items() if v}, termes

def _etape(liste, section, action, commande=None, motif=None):
    liste.append({"section": section, "action": action, "commande": commande, "motif": motif})


def liste_application(hyp, sc, res, cons, geo_ops, donnees, passe=None):
    """Étapes à valider à la main pour CE scénario. Rien n'est écrit."""
    E = []
    cons = cons if cons and not cons.get("erreur") else {}
    # V8.16 : passe exhaustive (obligatoires dans la liste, possibles prioritaires en facultatif).
    passe = passe if passe and not passe.get("erreur") else {}
    p_obl = passe.get("obligatoire") or {"trajectoires": [], "relations": [], "textes": []}
    marque = " [passe exhaustive]"
    ops_hyp = (hyp.get("geographie") or {}).get(sc) or []
    by_inst = {i.get("slug"): i for i in donnees["instances"]}
    redac = donnees["redactions"] or {}
    # V8.2 : zones_touchees = {zone: {pays perdus ou coupés}} ; zones_statut_chg à part.
    zones_mortes, zones_nouvelles, zones_touchees, traces = {}, [], {}, 0
    zones_statut_chg = set()
    redaction_a_creer, orateurs_a_creer = [], []
    # V8.4 : citations calculées d'abord (servent à la carte et à la localisation).
    cites, termes = fiches_citant(hyp, sc, geo_ops, donnees)
    by_zone = {z.get("slug"): z for z in donnees.get("zones") or []}

    def _du_pays(terme, pays):
        return terme == pays or termes.get(terme) == f"ville ({pays})"

    # 1. Carte -----------------------------------------------------------------
    for op, g in zip(ops_hyp, geo_ops or []):
        pays = g["pays"]
        if g.get("erreurs"):
            if op.get("source") != "ia":   # V8.1 : une proposition IA écartée n'est pas une étape
                _etape(E, "Carte", f"{pays} ({g['action']}) refusé au contrôle : corriger l'hypothèse avant toute application",
                       motif="; ".join(g["erreurs"][:3]))
            continue
        for a in g.get("alertes") or []:   # V8.4 : les alertes de la carte deviennent des étapes
            if "déjà partagé" in a:      # partition : déjà traité par les étapes de retrait (v8.1)
                continue
            _etape(E, "Carte", f"⚠ {pays} : {a}", motif="à trancher avant d'appliquer ce changement")
        cibles_op = ({p["cible"] for p in g.get("parties") or []} if g["action"] == "partition"
                     else ({g["cible"]} if g["action"] in ("absorber", "nouvelle_zone") else set()))
        for a in g.get("actuelles") or []:
            # V8.1 : zones qui PERDENT le pays (ou le voient coupé) ; une zone qui reçoit
            # un morceau n'a pas d'articles à relire pour autant.
            if a["slug"] not in cibles_op or g["action"] == "partition":
                zones_touchees.setdefault(a["slug"], set()).add(pays)
        if g["action"] == "absorber":
            _etape(E, "Carte", f"Rattacher {pays} à `{g['cible']}`",
                   f"Carte → clic sur {pays} → affecter à `{g['cible']}`",
                   "le pays change de mains")
        elif g["action"] == "nouvelle_zone":
            nz = op.get("nouvelle_zone") or {}
            _etape(E, "Carte", f"Créer la zone `{g['cible']}` ({nz.get('nom')}) avec {pays}",
                   f"Carte → clic sur {pays} → créer une zone (slug `{g['cible']}`, type {nz.get('type') or 'autre'}, "
                   f"statut {nz.get('statut') or 'emergent'})", "nouvelle zone de niveau 1")
            zones_nouvelles.append({"slug": g["cible"], "pays": pays})
        elif g["action"] == "partition":
            cibles = {p["cible"] for p in g["parties"]}
            for a in g.get("actuelles") or []:
                if a["slug"] not in cibles and (a.get("portion") or a["type"] == "overlay"):
                    _etape(E, "Carte", f"Retirer la portion actuelle de {pays} dans `{a['slug']}`"
                           + (f" (« {a['portion']} »)" if a.get("portion") else ""),
                           f"Carte → ✏️ éditer `{a['slug']}` → 🗑️ supprimer le masque ({pays})",
                           "la partition remplace les portions et tracés actuels")
                elif a["slug"] not in cibles and (a.get("niveau") or 1) == 1:
                    # V8.10 : zone quittée qui porte le pays entier (déjà partagé ou non) : à retirer.
                    _etape(E, "Carte", f"Retirer {pays} de `{a['slug']}` (zone quittée, pays entier)",
                           f"Carte → ✏️ éditer `{a['slug']}` : retirer l'entrée {pays}",
                           "aucune partie ne lui revient ; vérifier après les tracés si la Carte ne l'a pas déjà retirée")
                elif a["slug"] in cibles and a["type"] != "overlay" and not a.get("portion"):
                    _etape(E, "Carte", f"`{a['slug']}` porte aujourd'hui {pays} entier : il n'en gardera qu'une portion",
                           f"Carte → ✏️ éditer `{a['slug']}` : vérifier que l'entrée {pays} devient une portion",
                           "sinon la couleur pays entier reste sur tout le pays")
            for p in g["parties"]:
                if p["nouvelle"]:
                    zones_nouvelles.append({"slug": p["cible"], "pays": pays})
                    _etape(E, "Carte", f"Créer la zone `{p['cible']}` ({p.get('nom')}) pour la partie {p['numero']}",
                           "Carte → créer une zone vide (avant de dessiner les portions)",
                           "partie confiée à une nouvelle zone")
            for p in g["parties"]:
                if p["principale"]:
                    _etape(E, "Carte", f"Partie {p['numero']} : `{p['cible']}` garde {pays} entier",
                           f"Carte → clic sur {pays} → affecter à `{p['cible']}`", "modèle Allemagne")
                else:
                    traces += 1
                    _etape(E, "Carte", f"Partie {p['numero']} : dessiner « {p['portion']} » dans `{p['cible']}`",
                           f"Carte → ✏️ éditer `{p['cible']}` → ✏️ dessiner ({pays})", "tracé d'une portion")
            _etape(E, "Carte", f"Vérifier `zones_pays.json` : {pays} → "
                   + (f"`{g['zones_pays_apres']}`" if g["zones_pays_apres"] else "`null` (modèle France)"),
                   motif="la Carte l'écrit seule ; à contrôler après les tracés")
            for s in g.get("a_repartir") or []:
                if s.get("slug") in cibles:   # V8.10 : la sous-zone est elle-même une partie
                    continue
                _etape(E, "Carte", f"Répartir la sous-zone `{s['slug']}` ({s.get('nom')}) vers la partie qui la contient",
                       "Carte → arbre → ↗️ déplacer", "sous-zone du pays partagé")
        elif g["action"] == "region":
            nz = g["nouvelle_zone"]
            traces += 1
            _etape(E, "Carte", f"Créer la région `{g['cible']}` ({nz.get('nom')}) sous `{g['parent']}`",
                   f"Carte → arbre de `{g['parent']}` → ➕ sous-zone (type {nz.get('type')}, statut {nz.get('statut')}, "
                   f"lieu réel {pays}, portion « {g['portion']} »)", "le pays ne change pas de mains")
            _etape(E, "Carte", f"Dessiner le tracé de `{g['cible']}`",
                   f"Carte → ✏️ éditer → ✏️ dessiner ({pays})", "portion de la région")
            zones_nouvelles.append({"slug": g["cible"], "pays": pays, "region": True,
                                    "redaction": g.get("redaction")})
        for q in g.get("quittees") or []:
            if q["videe"]:
                zones_mortes[q["slug"]] = "vidée par la carte"
                _etape(E, "Carte", f"`{q['slug']}` n'a plus aucun territoire : la garder (vestige, exil) ou la supprimer",
                       "Carte → ✏️ éditer → Zone dangereuse (refusé tant qu'elle a des sous-zones)",
                       "zone quittée par " + pays)
        # V8.4 : jamais une sous-zone vers elle-même ; une sous-zone à plusieurs pays n'est
        # pas rattachée en bloc.
        orph = [o for o in ((g.get("impact") or {}).get("sous_zones_orphelines") or [])
                if o.get("slug") and o.get("slug") != g.get("cible")]
        simples = []
        for o in orph:
            autres = []   # V8.5 : seulement d'autres PAYS (pas une ville ou une région du pays)
            for x in ((by_zone.get(o["slug"]) or {}).get("origine_reelle") or []):
                if isinstance(x, dict) and x.get("entite") and _autres_pays(str(x["entite"]), pays):
                    autres.append(str(x["entite"]))
            if autres:
                _etape(E, "Carte", f"`{o['slug']}` porte aussi {', '.join(autres[:3])}"
                       + (" …" if len(autres) > 3 else "") + " : la répartir à la main, pas en bloc",
                       "Carte → arbre → ↗️ déplacer, ou nouvelle sous-zone pour la part de " + pays,
                       f"sous-zone de {pays} à plusieurs pays")
            else:
                simples.append(o)
        if simples and g["action"] in ("absorber", "nouvelle_zone"):
            _etape(E, "Carte", f"{len(simples)} sous-zone(s) de {pays} à rattacher à `{g['cible']}`",
                   f"python3 generator/reparenter_sous_zones_orphelines.py --scenario {sc} --zone-cible {g['cible']}",
                   ", ".join(o["slug"] for o in simples[:MAX_LISTE]))
        # V8.4-V8.8 : zones liées au pays par son nom ou une de ses villes.
        #  - sous-zone d'une zone qui perd le pays : citée n'importe où (nom, territoires, texte) ;
        #  - ailleurs (sous-zone rangée sous une autre zone, ou zone de niveau 1) : seulement si la
        #    ville figure dans son NOM ou ses TERRITOIRES réels (une description qui cite São Paulo
        #    ne fait pas d'une zone de Séoul une zone brésilienne).
        import re as _re
        deja_orph = {o["slug"] for o in orph} | {x.get("slug") for x in g.get("a_repartir") or []}
        actuelles_slugs = {a["slug"] for a in g.get("actuelles") or []}
        perdantes = {a["slug"] for a in g.get("actuelles") or []
                     if (a.get("niveau") or 1) == 1 and (a["slug"] not in cibles_op or g["action"] == "partition")}
        termes_pays = [t for t, o in termes.items() if t == pays or o == f"ville ({pays})"]
        motifs_pays = [(t, _re.compile(r"(?<![a-z0-9])" + _re.escape(_plie_aligne(t)) + r"(?![a-z0-9])"))
                       for t in sorted(termes_pays, key=len, reverse=True)]
        villes_pays = {t for t in termes_pays if t != pays}
        homonymes = _homonymes_pays(termes)
        motifs_terr = [(t, m) for t, m in motifs_pays if t not in homonymes]
        cites_zones = {it["slug"]: it for it in cites.get("Zones") or []}
        dest = (f"`{g['cible']}`" if g["action"] in ("absorber", "nouvelle_zone")
                else "la partie qui la contient" if g["action"] == "partition" else "sa zone actuelle")
        for zslug, z in (by_zone.items() if g["action"] != "region" else ()):
            # V8.11 : une région ne fait changer le pays de mains : aucune zone à déplacer.
            if not zslug or zslug in deja_orph or zslug == g.get("cible") or zslug in actuelles_slugs:
                continue
            racine = _racine_n1(zslug, by_zone)
            if racine == g.get("cible"):
                continue
            terr = " ; ".join(str(x.get("entite")) for x in (z.get("origine_reelle") or [])
                              if isinstance(x, dict) and x.get("entite"))
            # V8.7 : une ville homonyme d'un pays compte dans le nom, pas dans les territoires.
            r = _trouve(str(z.get("nom") or ""), motifs_pays) or _trouve(terr, motifs_terr)
            if (z.get("niveau") or 1) > 1:
                # V8.8 : sous-zone dont les territoires désignent un autre pays (Haïfa citant Ispahan) : pas à déplacer.
                autre_pays = not r and terr and _autres_pays(terr, pays)
                if racine in perdantes and (r or zslug in cites_zones) and not autre_pays:
                    terme = r[0] if r else cites_zones[zslug]["terme"]
                    extrait = r[1] if r else cites_zones[zslug]["extrait"]
                    if r or _du_pays(terme, pays):
                        _etape(E, "Carte", f"Sous-zone `{zslug}` (cite « {terme} ») : à déplacer avec {pays} ?",
                               f"Carte → arbre → ↗️ déplacer vers {dest}", extrait)
                elif r and r[0] in villes_pays:
                    _etape(E, "Carte", f"Sous-zone `{zslug}` (sous `{racine}`, nom ou territoire « {r[0]} ») : "
                           f"à déplacer avec {pays} ?", f"Carte → arbre → ↗️ déplacer vers {dest}",
                           "rangée hors de la zone qui perd le pays : vérifier")
            elif r and r[0] in villes_pays:
                _etape(E, "Carte", f"Zone de niveau 1 `{zslug}` (nom ou territoire « {r[0]} ») : reste à part ou "
                       f"rejoint {dest} ?", "à décider ; la rattacher = Carte → arbre → ↗️ déplacer",
                       "zone indépendante sur le territoire du pays")
        # Rédaction de la zone d'arrivée.
        nouvelle_sans_redac = (g["action"] == "nouvelle_zone"
                               or (g["action"] == "absorber" and g.get("redaction_cible") is False))
        if nouvelle_sans_redac:
            redaction_a_creer.append(g["cible"])
        if g["action"] == "partition":
            redaction_a_creer += [p["cible"] for p in g["parties"] if p.get("redaction") is False]
        if g["action"] == "region" and g.get("redaction") is False:
            redaction_a_creer.append(g["cible"])
        # Oral : la zone d'origine a-t-elle une rédaction orale ou mixte ?
        orales = [(r["ligne"], a["slug"]) for a in g.get("actuelles") or []
                  for r in redac.get(a["slug"], []) if r["type_diffusion"] in ("oral", "mixte")]
        if orales:
            orateurs_a_creer.append({"pays": pays, "origine": orales})
    for nz in zones_nouvelles:
        if nz.get("region"):
            continue
        _etape(E, "Carte", f"Relations (alliés / rivaux) de la nouvelle zone `{nz['slug']}`",
               f"à la main : geographie/{sc}.md, bloc `relations` de `{nz['slug']}`",
               "la création n'en écrit aucune")
    if zones_nouvelles:
        _etape(E, "Carte", "Continent des nouvelles zones sur le site : "
               + ", ".join(f"`{z['slug']}`" for z in zones_nouvelles),
               "python3 generator/export_revues.py --continents",
               "forcer dans generator/continents_zones.yaml si le continent deviné est faux")

    # 4. Statuts de zone (avant la localisation : une zone disparue est une zone morte)
    for z in cons.get("zones_statut") or []:
        _etape(E, "Statuts de zone", f"`{z['zone']}` ({z.get('nom')}) : {z['avant']} → {z['apres']}",
               f"à la main : geographie/{sc}.md, champ `statut` (texte mis à jour par "
               f"regenerer_corps_geographie.py --scenario {sc} --execute)", z.get("raison"))
        zones_statut_chg.add(z["zone"])
        if z["apres"] == "disparu":
            zones_mortes.setdefault(z["zone"], "statut disparu")

    # 2. Localisation des fiches -----------------------------------------------
    deja = set()
    def _localiser(slug, quoi, motif):
        if slug in deja:
            return
        deja.add(slug)
        _etape(E, "Localisation des fiches", f"{quoi} `{slug}` : {motif}",
               f"python3 generator/extract_localisation.py --scenario {sc} --slug {slug} --force",
               "puis review_localisation.py si la zone reste ambiguë")
    for i in donnees["instances"]:
        z = (i.get("localisation") or {}).get("zone")
        if z in zones_mortes:
            _localiser(i["slug"], "Instance", f"localisée dans `{z}` ({zones_mortes[z]})")
    for ev in donnees["evenements"]:
        z = (ev.get("localisation") or {}).get("zone")
        if z in zones_mortes:
            _localiser(ev.get("slug"), "Événement", f"localisé dans `{z}` ({zones_mortes[z]})")
    # V8.4 : une fiche d'une sous-zone déplacée en bloc la suit (rien à faire). En
    # partition, une fiche localisée DANS une zone coupée et qui cite le pays ou une de
    # ses villes peut tomber dans une autre portion.
    loc_inst = {i.get("slug"): (i.get("localisation") or {}).get("zone") for i in donnees["instances"]}
    loc_inst.update({ev.get("slug"): (ev.get("localisation") or {}).get("zone") for ev in donnees["evenements"]})
    for g in geo_ops or []:
        if g.get("erreurs") or g["action"] != "partition":
            continue
        coupees = {a["slug"] for a in g.get("actuelles") or []}
        for type_ in ("Instances", "Événements"):
            for it in cites.get(type_) or []:
                if loc_inst.get(it["slug"]) in coupees and _du_pays(it["terme"], g["pays"]):
                    _localiser(it["slug"], type_[:-1], f"localisé(e) dans `{loc_inst[it['slug']]}`, coupée ; "
                               f"cite « {it['terme']} » : lieu à vérifier contre les portions")

    # 3. Journaux --------------------------------------------------------------
    redaction_a_creer = list(dict.fromkeys(redaction_a_creer))
    if redaction_a_creer:
        _etape(E, "Journaux", "Créer les rédactions de : " + ", ".join(f"`{z}`" for z in redaction_a_creer),
               f"python3 generator/generate_journaux.py --scenario {sc} --update",
               "puis clean_fallback_journaux.py si un lot échoue ; une région hérite sinon de la rédaction parente")
        _etape(E, "Journaux", "Couverture des journalistes des nouvelles rédactions",
               "python3 generator/audit_couverture_journalistes.py --report",
               "inject_journaliste_custom.py --mode auto si trop de thématiques à un seul nom")
        for o in orateurs_a_creer:
            for ligne, origine in o["origine"]:
                for z in redaction_a_creer:
                    _etape(E, "Journaux", f"`{origine}` ({ligne}) est oral ou mixte : faut-il des orateurs à `{z}` ?",
                           f"python3 generator/inject_orateur_custom.py --mode convertir --scenario {sc} "
                           f"--zones {ligne}::{z}", f"territoire venu de {o['pays']}")
    for z, cause in zones_mortes.items():
        for r in redac.get(z, []):
            _etape(E, "Journaux", f"*{r['nom']}* ({r['ligne']}, `{z}`) n'a plus de territoire ({cause})",
                   "à la main : le garder (journal en exil) ou le retirer de journaux.yaml "
                   "(load_journaux / save_journaux, comme le 6 oct)",
                   "aucun outil de migration des journaux")

    # 5. Élément ---------------------------------------------------------------
    if hyp.get("mode") == "rupture":
        # PATCH_S19_CHAINE (v8.20) : la rupture passe par l'injection. Les fiches portent
        # `mode: rupture` et le moteur déplace lui-même la référence : rien à changer à la main.
        _etape(E, "Élément", f"Injecter l'événement `{hyp['id']}` en mode rupture (entrée commune en fin de rapport)",
               "python3 generator/inject_custom_events.py --mode custom",
               "une seule injection pour tous les scénarios ; mode_impose: rupture écrit `mode: rupture` dans chaque fiche")
        # PATCH_S19_RETOUCHES : références déplacées regroupées dans la vérification (rien à faire).
        deplacees, plafonnees = [], []
        for e in (res or {}).get("effets") or []:
            if abs(e.get("reference_apres", e["reference"]) - e["reference"]) >= 0.1:
                # V8.13 : une référence portée au plafond ne laisse plus de marge.
                if e["reference_apres"] >= 99.5:
                    plafonnees.append(e["variable"])
                deplacees.append(f"{e['variable']} {_virgule(e['reference'], False)} → "
                                 f"{_virgule(e['reference_apres'], False)}")
        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{i['force']:g}"
                           for i in hyp["impacts"] if sc in i["polarites"])
        _etape(E, "Élément", ("⚠ " if plafonnees else "")
               + f"Vérifier que la fiche porte `mode: rupture` et les forces simulées ({cibles})",
               f"event_instances/{hyp['id']}_{sc}.md ; "
               f"python3 generator/trace_injection.py --slug {hyp['id']} --type evenement --scenario {sc}",
               "le Tracer doit finir chaque ligne « Déclaré » par « rupture » et retrouver l'effet simulé"
               + (" ; références déplacées par le moteur (rien à faire) : " + " ; ".join(deplacees) if deplacees else "")
               + (" ; au plafond, plus aucune marge pour une autre crise : " + ", ".join(plafonnees) if plafonnees else ""))
        _etape(E, "Élément", "Nouvelle référence : vérifier la lisibilité du moteur",
               "python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05", "S19")
    elif hyp.get("impacts"):
        _etape(E, "Élément", f"Injecter l'événement `{hyp['id']}` (entrée commune en fin de rapport)",
               "python3 generator/inject_custom_events.py --mode custom",
               "une seule injection pour tous les scénarios de l'hypothèse")
        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{i['force']:g}"
                           for i in hyp["impacts"] if sc in i["polarites"])
        # V8.15 : forces, date et propagation imposées à l'injection (impacts_imposes).
        _etape(E, "Élément", f"Vérifier que la fiche porte les forces simulées ({cibles})",
               f"event_instances/{hyp['id']}_{sc}.md, bloc impact_sur_variables ; "
               f"python3 generator/trace_injection.py --slug {hyp['id']} --type evenement --scenario {sc}",
               "imposées par l'entrée commune (impacts_imposes, date_imposee) : l'effet doit "
               "correspondre à cette simulation")
        if sum(i["force"] for i in hyp["impacts"]) >= 30:
            _etape(E, "Élément", "Gros choc : vérifier la lisibilité du moteur",
                   "python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05", "S19")

    # 6. Nouvelles entités -----------------------------------------------------
    if cons.get("nouvelles_entites"):
        _etape(E, "Nouvelles entités", f"{len(cons['nouvelles_entites'])} entrée(s) prête(s) (bloc YAML ci-dessous) "
               "pour entites_custom/queue.yaml — catégorie à choisir",
               "python3 generator/create_entities_and_instances.py --mode custom",
               "la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario")

    # 7. Trajectoires ----------------------------------------------------------
    for t in (cons.get("trajectoires") or []) + [dict(x, passe=True) for x in p_obl["trajectoires"]]:
        inst = by_inst.get(t["instance"]) or {}
        notes = [t.get("raison") or ""]
        cmd = f"à la main : instances/{t['instance']}.md, champ `trajectoire`"
        if t["apres"] in TRAJ_TERMINALES and not inst.get("annee_fin"):
            cmd += " ; puis `annee_fin` (fix_annee_fin_manquant.py)"
        if (inst.get("injection") or {}).get("type") == "custom":
            notes.append("instance custom : ne régénérer qu'avec generate_instances.py --injection-custom")
        if inst.get("exclure_articles") or inst.get("priorite_forcee"):
            notes.append("marqueur exclure_articles / priorite_forcee : à reposer après toute régénération")
        # V8.12 : saut qui passe la phase « ascendant » (émergent → dominant) : gardé, signalé.
        saut = t["avant"] in ("émergent", "marginal") and t["apres"] in ("dominant", "mature")
        if saut:
            notes.insert(0, "saut d'un cran (sans passer par ascendant) : garder, ou ramener à ascendant")
        _etape(E, "Trajectoires", ("⚠ " if saut else "") + f"{t.get('nom')} (`{t['instance']}`) : {t['avant']} → {t['apres']}"
               + (marque if t.get("passe") else ""),
               cmd, " ; ".join(n for n in notes if n))

    # 8. Relations -------------------------------------------------------------
    # V8.16 : relations de la passe ; les relations rompues d'une entité qui disparaît
    # sont regroupées en une seule étape (cas Genève : 24 obligatoires).
    disparues = {t["instance"]: t.get("nom") for t in (cons.get("trajectoires") or []) + p_obl["trajectoires"]
                 if t.get("apres") == "disparu"}
    rels = list(cons.get("relations") or [])
    groupes = {}
    for r in p_obl["relations"]:
        cle = r["a"] if r["a"] in disparues else (r["b"] if r["b"] in disparues else None)
        if cle and r["action"] == "rompue":
            groupes.setdefault(cle, []).append(r)
        else:
            # V8.16.2 : rupture justifiée par une disparition que rien ne déclare.
            alerte = None
            if r["action"] == "rompue":
                traj_b = next((t["apres"] for t in (cons.get("trajectoires") or [])
                               if t["instance"] == r["b"]), (by_inst.get(r["b"]) or {}).get("trajectoire"))
                raison_pliee = _plie(r.get("raison") or "")
                if traj_b != "disparu" and any(m in raison_pliee for m in
                                               ("dispar", "detrui", "n'existe_plus", "n'existent_plus")):
                    alerte = (f"`{r['b']}` n'est déclarée disparue nulle part (trajectoire retenue : "
                              f"{traj_b or '?'}) : garder la relation, ou faire disparaître l'entité")
            rels.append(dict(r, passe=True, alerte=alerte))
    for cle, liste_r in groupes.items():
        autres = list(dict.fromkeys(r["b"] if r["a"] == cle else r["a"] for r in liste_r))
        _etape(E, "Relations", f"{disparues[cle] or cle} (`{cle}`) disparaît : retirer ses "
               f"{len(liste_r)} relation(s) rompue(s){marque}",
               f"à la main : retirer `{cle}` des alliances / oppositions de "
               + ", ".join(f"`{a}`" for a in autres[:MAX_LISTE]) + (" …" if len(autres) > MAX_LISTE else "")
               + f", puis vider celles de instances/{cle}.md",
               "regroupé sous l'entité disparue ; la réciprocité n'enlève rien")
    for r in rels:
        champ = "alliances" if r["type"] == "alliance" else "oppositions"
        if r["action"] == "nouvelle":
            _etape(E, "Relations", f"{r['type']} nouvelle : {r['a_nom']} ↔ {r['b_nom']}"
                   + (marque if r.get("passe") else ""),
                   f"à la main : ajouter `{r['b']}` dans `{champ}` de instances/{r['a']}.md", r.get("raison"))
        else:
            _etape(E, "Relations", ("⚠ " if r.get("alerte") else "")
                   + f"{r['type']} rompue : {r['a_nom']} ↔ {r['b_nom']}"
                   + (marque if r.get("passe") else ""),
                   f"à la main : retirer de `{champ}` dans les DEUX fiches ({r['a']}, {r['b']})",
                   r.get("alerte") or "la réciprocité n'enlève rien")
    if any(r["action"] == "nouvelle" for r in rels):
        _etape(E, "Relations", "Rendre les relations réciproques",
               f"python3 generator/fix_alliances_oppositions.py --scenario {sc} --reciprocite-seule --ignorer-exclus",
               "étape 2 de Relations & lore (simulation d'abord)")

    # 9. Lore ------------------------------------------------------------------
    if zones_mortes or hyp.get("contraintes"):
        sujets = [f"zone `{z}`" for z in zones_mortes] + (["faits imposés de l'hypothèse"] if hyp.get("contraintes") else [])
        _etape(E, "Lore", "Règles à ajouter pour que l'audit du lore surveille : " + ", ".join(sujets),
               f"à la main : documentation/lore_regles.yaml, section {sc}",
               "comme les zones abandonnées de fortress_world (Nordgard, Koursk)")

    # V8.16 : phrases que la passe exhaustive juge fausses (obligatoires).
    for t in p_obl["textes"]:
        dossier = "instances" if t.get("genre") == "instance" else "event_instances"
        _etape(E, "Fiches à relire", f"Corriger une phrase de `{t['slug']}`{marque}",
               f"à la main : {dossier}/{t['slug']}.md",
               f"« {_court(t['extrait'], 160)} » — contredit par : {t.get('contredit') or '?'}")

    # 9 bis. Fiches à relire (V8.3) ------------------------------------------------
    # V8.16.1 : avec la passe exhaustive, instances et événements sont déjà relus ;
    # la recherche par mots ne garde que les zones et le registre.
    cites_lus = {k: v for k, v in cites.items()
                 if not passe or k not in ("Instances", "Événements")}
    if cites_lus:
        _etape(E, "Fiches à relire", "Termes cherchés : " + ", ".join(sorted(termes)[:20])
               + (f" … (+{len(termes) - 20})" if len(termes) > 20 else ""),
               motif="mot entier, sans casse ni accents ; le registre seulement après "
               f"{hyp['date']:g} (chronologie)"
               + (" ; instances et événements relus par la passe exhaustive : seuls les zones "
                  "et le registre sont listés" if passe else ""))
        for type_, items in cites_lus.items():
            for it in items[:MAX_FICHES]:
                _etape(E, "Fiches à relire", f"{type_[:-1] if type_.endswith('s') else type_} `{it['slug']}` "
                       f"cite « {it['terme']} »", motif=it["extrait"])
            if len(items) > MAX_FICHES:
                _etape(E, "Fiches à relire", f"… et {len(items) - MAX_FICHES} autre(s) parmi : {type_.lower()}",
                       motif="liste complète : generator/state/dernier_et_si.json, clé application")
        if cites_lus.get("Instances"):
            _etape(E, "Fiches à relire", "Relecture IA ciblée d'une instance (contradictions avec l'hypothèse)",
                   f"python3 generator/audit_lore.py --scenario {sc} --llm --slug <slug>",
                   "payant (≈ 0,5 centime la fiche) ; après application de la carte et de l'événement")

    elif passe:
        _etape(E, "Fiches à relire", "Instances et événements relus par la passe exhaustive "
               "(obligatoires ci-dessus et dans les autres sections) ; aucune zone ni ligne du registre "
               "ne cite l'hypothèse")
    else:
        # V8.9 : rien à chercher par mots (hypothèse mondiale, sans pays ni nom propre) :
        # une fiche peut la contredire sans la nommer ; seule la relecture IA la trouve.
        _etape(E, "Fiches à relire", "Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche",
               motif="une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, "
               "après l'ajout des faits imposés dans lore_regles.yaml (section Lore)")
        _etape(E, "Fiches à relire", "Estimer la relecture IA des fiches de plus fort impact",
               f"python3 generator/audit_lore.py --scenario {sc} --llm --estimer --limit 10", "aucun appel")
        _etape(E, "Fiches à relire", "Relecture IA des 10 fiches de plus fort impact (contradictions avec l'hypothèse)",
               f"python3 generator/audit_lore.py --scenario {sc} --llm --limit 10",
               "payant (≈ 0,5 centime la fiche) ; après application de l'événement")
        for z in sorted(zones_statut_chg)[:MAX_LISTE]:
            _etape(E, "Fiches à relire", f"Relecture IA des fiches de la zone `{z}` (statut changé)",
                   f"python3 generator/audit_lore.py --scenario {sc} --llm --zone {z}",
                   "estimer d'abord avec --estimer ; payant")

    # V8.16 : possibles prioritaires de la passe, en étapes facultatives.
    if passe:
        import et_si_exhaustif as ex
        fiches_p = ex.grouper_possibles(passe.get("possible")
                                        or {"trajectoires": [], "relations": [], "textes": []})
        prio = [c for c in passe.get("classement") or [] if c.get("slug") in fiches_p][:ex.PRIORITE_MAX]
        for c in prio:
            f = fiches_p[c["slug"]]
            items = [(g, x) for g, x in f["items"] if not ex._disqualifie(x)] or f["items"]
            _etape(E, "Possibles (facultatif)", f"{f['nom']} (`{c['slug']}`) : "
                   + ex._resume_fiche({"items": items}) + marque, motif=c.get("pourquoi") or None)
        if len(fiches_p) > len(prio):
            _etape(E, "Possibles (facultatif)",
                   f"… et {len(fiches_p) - len(prio)} autre(s) fiche(s) avec des changements possibles",
                   motif="détail dans la section « Passe exhaustive » de ce scénario")

    # 10. Articles et site -----------------------------------------------------
    entites_changees = ({t["instance"] for t in cons.get("trajectoires") or []}
                        | {t["instance"] for t in p_obl["trajectoires"]})
    a_rezoner = [a for a in donnees["articles"] if a["zone"] in zones_mortes]
    import re as _re

    def _cite(a, pays):
        return _re.search(r"(?<![a-z0-9])" + _re.escape(_plie(pays)) + r"(?![a-z0-9])", a["texte"]) is not None

    # V8.2 : zone qui perd ou voit couper un pays -> seulement les articles qui citent ce pays.
    a_relire = [a for a in donnees["articles"] if a not in a_rezoner
                and (a["zone"] in zones_statut_chg
                     or any(_cite(a, p) for p in zones_touchees.get(a["zone"], ()))
                     or entites_changees & set(a["entites"]))]
    for a in a_rezoner[:MAX_LISTE]:
        _etape(E, "Articles et site", f"Rezoner « {a['titre']} » (`{a['zone']}`, {zones_mortes[a['zone']]})",
               f"python3 generator/rezoner_articles.py --corriger {a['fichier'][:24]}=<zone> --apply",
               "sinon non publiable sur le site ; puis reattribuer_signatures.py")
    if len(a_rezoner) > MAX_LISTE:
        _etape(E, "Articles et site", f"… et {len(a_rezoner) - MAX_LISTE} autre(s) article(s) à rezoner")
    if a_rezoner:
        _etape(E, "Articles et site", "Signatures des articles rezonés",
               "python3 generator/reattribuer_signatures.py", "aperçu, puis --apply")
    if a_relire:
        _etape(E, "Articles et site", f"{len(a_relire)} article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)",
               motif="; ".join(f"« {a['titre']} »" for a in a_relire[:MAX_LISTE])
               + (" …" if len(a_relire) > MAX_LISTE else ""))
    if E:
        _etape(E, "Articles et site", "Résumé du scénario",
               f"python3 generator/generate_resume_scenarios.py --scenario {sc}", "payant, un appel")
        _etape(E, "Articles et site", "Site des revues",
               "python3 generator/chapos_revues.py", "puis bash generator/publier_site.sh")

    # 11. Contrôles ------------------------------------------------------------
    if E:
        _etape(E, "Contrôles", "Base", "python3 generator/validate.py")
        if geo_ops:
            _etape(E, "Contrôles", "Géographie",
                   f"python3 generator/scan_geographie_complet.py --scenario {sc}"
                   + (" --check-overlays" if traces else ""),
                   f"{traces} tracé(s) dessiné(s)" if traces else None)
        _etape(E, "Contrôles", "Lore", f"python3 generator/audit_lore.py --scenario {sc}",
               "puis étapes 2 et 3 de Relations & lore si besoin")

    sources_ia = any(op.get("source") == "ia" for op in ops_hyp) or any(
        cons.get(k) for k in ("trajectoires", "relations", "zones_statut", "nouvelles_entites")) or bool(passe)
    # V8.16.2 : entités les plus touchées, pour acteurs_hint de l'entrée commune.
    poids = {}

    def _pese(slug, p):
        if slug and str(slug).endswith("_" + sc):
            poids[slug] = poids.get(slug, 0) + p
    for t in cons.get("trajectoires") or []:
        _pese(t["instance"], 2)
    for t in p_obl["trajectoires"]:
        _pese(t["instance"], 3)
    for t in p_obl["textes"]:
        if t.get("genre") == "instance":
            _pese(t["slug"], 2)
    for r in p_obl["relations"]:
        _pese(r["a"], 1)
        _pese(r["b"], 1)
    acteurs = [s for s, _ in sorted(poids.items(), key=lambda x: -x[1])][:4]
    # PATCH_S27_V818 : sort de chaque acteur du récit (et zones changées), transmis à
    # l'injection pour que le texte ne le réinvente pas à chaque tirage.
    annee = f"{hyp['date']:g}"
    sort_final = {t["instance"]: t for t in (cons.get("trajectoires") or []) + p_obl["trajectoires"]}
    faits = []
    for s in acteurs:
        inst = by_inst.get(s) or {}
        nom = inst.get("name") or s
        t = sort_final.get(s)
        if t and t["apres"] == "disparu":
            faits.append({"fait": f"{nom} ({s}) disparaît en {annee} (trajectoire {t['avant']} → disparu) : "
                                  f"après cette date, elle n'agit plus.", "slug": s, "sort": "disparait"})
        elif t:
            faits.append({"fait": f"{nom} ({s}) passe de « {t['avant']} » à « {t['apres']} » après {annee} : "
                                  f"elle existe toujours (elle peut perdre des lieux, des biens ou du pouvoir), "
                                  f"ne la décris pas comme disparue.", "slug": s, "sort": "change"})
        elif inst:
            faits.append({"fait": f"{nom} ({s}) garde sa trajectoire « {inst.get('trajectoire') or '?'} » : "
                                  f"elle survit à l'événement sans changement majeur, ne la décris ni détruite "
                                  f"ni disparue.", "slug": s, "sort": "reste"})
    for z in cons.get("zones_statut") or []:
        faits.append({"fait": f"La zone {z.get('nom') or z['zone']} ({z['zone']}) passe de « {z['avant']} » à "
                              f"« {z['apres']} »" + (" : le lieu disparaît." if z["apres"] == "disparu"
                                                     else " : le lieu subsiste."),
                      "slug": z["zone"], "sort": "zone"})
    return {"etapes": E, "avert": donnees["avert"], "sources_ia": sources_ia, "fiches_citant": cites,
            "nouvelles_entites": cons.get("nouvelles_entites") or [], "acteurs": acteurs, "faits": faits}


def construire_application(hyp, resultats, consequences, geo, scenarios, passe=None):
    out = {}
    for sc in scenarios:
        try:
            out[sc] = liste_application(hyp, sc, resultats.get(sc), consequences.get(sc),
                                        geo.get(sc), _donnees_application(sc), (passe or {}).get(sc))
        except Exception as e:  # la liste ne doit jamais empêcher le reste du rapport
            out[sc] = {"erreur": f"{type(e).__name__}: {e}", "etapes": []}
    return out


def _yaml_bloc(obj):
    return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=100).rstrip()


def _rendre_application(app, hyp, sc):
    L = ["### Liste d'application (à valider à la main — rien n'est écrit)", ""]
    if app.get("erreur"):
        return L + [f"_Liste impossible : {app['erreur']}_", ""]
    for a in app.get("avert") or []:
        L.append(f"- ⚠ {a}")
    if app.get("sources_ia") and app["etapes"]:
        L += ["_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de "
              "l'appliquer ; écarter une proposition suffit à sauter ses étapes._", ""]
    if not app["etapes"]:
        return L + ["Rien à appliquer dans ce scénario.", ""]
    n = 0
    for section in SECTIONS_APPLICATION:
        etapes = [e for e in app["etapes"] if e["section"] == section]
        if not etapes:
            continue
        L.append(f"**{section}**")
        for e in etapes:
            n += 1
            txt = f"- [ ] {n}. {e['action']}"
            if e.get("commande"):
                cmd = e["commande"]
                txt += (f"\n  - `{cmd}`" if cmd.startswith(("python3 ", "bash ")) else f"\n  - {cmd}")
            if e.get("motif"):
                txt += f"\n  - _{e['motif']}_"
            L.append(txt)
        L.append("")
    if app.get("nouvelles_entites"):
        entrees = [{"nom": ne["nom"], "category": "<à choisir>", "role": ne["role"], "etat": "émergent",
                    "scenario_ref": sc, "scenario_hint": [sc],
                    **({"zone_hint": ne["zone"]} if ne.get("zone") and ne["zone"] != "transnationale" else {}),
                    "source": f"et_si_{hyp['id']}"} for ne in app["nouvelles_entites"]]
        L += ["Entrées pour `entites_custom/queue.yaml` :", "", "```yaml", _yaml_bloc(entrees), "```", ""]
    return L


def _rendre_injection_commune(hyp, application, out=None):
    """Entrée de queue commune aux scénarios (mode choc seulement).
    V8.17 : `out` (dict) reçoit l'entrée sous la clé « entree »."""
    if not hyp.get("impacts"):
        return []
    scen = [sc for sc in hyp["scenarios"] if sc in application]
    if not scen:
        return []
    geo = any((application.get(sc) or {}).get("etapes") and hyp["geographie"].get(sc) for sc in scen)
    rupture = hyp.get("mode") == "rupture"
    partiel = [sc for sc in hyp["scenarios"] if sc not in application]
    scen = list(hyp["scenarios"])   # V8.15 : polarités connues pour tous les scénarios (S19 : rupture comprise)
    entree = {"id": hyp["id"], "description": hyp["description"] or hyp["nom"],
              "portee": "<locale | regionale | continentale | globale>" if geo else "globale",
              "date_approximative": int(hyp["date"]), "intensite": "<à choisir>",
              # PATCH_S19_RETOUCHES : en rupture, la persistance est sans objet (permanente).
              "persistance": "permanente" if rupture else (hyp["persistance"] or "permanente"), "scenarios": scen,
              "variables_hint": [i["variable"] for i in hyp["impacts"]],
              "variables_hint_count": len(hyp["impacts"]), "source": f"et_si_{hyp['id']}"}
    # V8.16.2 : entités les plus touchées (lecture IA, passe exhaustive), 4 au plus par scénario ;
    # inject_custom_events.py n'impose dans un scénario que les slugs de ce scénario.
    par_sc = {sc: (application.get(sc) or {}).get("acteurs") or [] for sc in scen}
    acteurs = list(dict.fromkeys(a for sc in scen for a in par_sc[sc]))
    if acteurs:
        entree["acteurs_hint"] = acteurs
        entree["acteurs_hint_count"] = max(len(v) for v in par_sc.values())
    # PATCH_S27_V818 : faits imposés au récit (contraintes de l'hypothèse + sort des acteurs).
    faits = {sc: list((application.get(sc) or {}).get("faits") or []) for sc in scen}
    if hyp.get("contraintes"):
        faits = {sc: [{"fait": c, "sort": "contrainte"} for c in hyp["contraintes"]] + v
                 for sc, v in faits.items()}
    faits = {sc: v for sc, v in faits.items() if v}
    if faits:
        entree["faits_imposes"] = faits
    # V8.15 : ce qui a été simulé est imposé à l'injection (patch_s27_injection_imposee.py).
    def _nombre(x):
        return int(x) if float(x) == int(x) else x
    entree["date_imposee"] = _nombre(hyp["date"])
    trop_fort = []
    if rupture:
        entree["mode_impose"] = "rupture"   # PATCH_S19_CHAINE : écrit `mode: rupture` dans les fiches
    if True:   # S19 : forces imposées aussi en mode rupture
        entree["impacts_imposes"] = {
            sc: [{"variable": i["variable"], "delta_level": _nombre(i["force"]),
                  "duree": _nombre(i["duree"]), "polarite": i["polarites"][sc]}
                 for i in hyp["impacts"] if sc in i["polarites"]]
            for sc in scen}
        entree["via_matrice_impose"] = bool(hyp["via_matrice"])
        trop_fort = [f"{i['variable']} ({i['force']:g})" for i in hyp["impacts"] if i["force"] > DELTA_MAX_CONSEILLE]
    if out is not None:
        out["entree"] = entree
    return ["## Liste d'application — injection commune", "",
            ("⚠ Simulation limitée à " + ", ".join(sc for sc in scen if sc not in partiel)
             + " : l'entrée couvre aussi " + ", ".join(partiel) + ", non simulé(s) dans ce rapport ; "
             "les simuler avant d'injecter, ou les retirer de `scenarios` et de `impacts_imposes`.\n\n"
             if partiel else "")
            + ("⚠ Force au-dessus du plafond d'un événement custom (" + str(DELTA_MAX_CONSEILLE) + ") : "
               + ", ".join(trop_fort) + ". L'injection refusera l'entrée : baisser la force et resimuler.\n\n"
               if trop_fort else "")
            + ("Mode rupture : `mode_impose: rupture` fait écrire `mode: rupture` dans chaque fiche ; le "
               "moteur déplace alors durablement la référence du scénario au lieu d'amortir un choc.\n\n"
               if hyp.get("mode") == "rupture" else "")
            + "Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). "
            + ("Forces, polarités, durées, date et propagation de cette simulation sont imposées "
               "(`impacts_imposes`, `date_imposee`, `via_matrice_impose`) : l'IA de l'injection ne les "
               "recalcule pas, elle rédige seulement le récit."), "",
            *(["`acteurs_hint` : entités les plus touchées de chaque scénario (lecture IA, passe "
               "exhaustive), 4 au plus par scénario ; chaque slug ne vaut que pour son scénario.", ""]
              if entree.get("acteurs_hint") else []),
            *(["`faits_imposes` : contraintes de l'hypothèse et sort des acteurs du récit (disparaît, "
               "change, reste) ; l'injection les donne à l'IA comme faits non négociables.", ""]
              if entree.get("faits_imposes") else []),
            "```yaml", _yaml_bloc([entree]), "```", ""]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def _decider(args, hyps):
    """V8.17 : --dossiers, --adopter, --rejeter, --annuler-decision."""
    import et_si_dossiers as ed
    if args.dossiers:
        print(f"Dossiers des hypothèses ({ed.DOSSIERS_PATH.relative_to(VAULT_ROOT)}) :")
        for ligne in ed.tableau(hyps):
            print(ligne)
        return
    hid = args.adopter or args.rejeter or args.annuler_decision
    brut = next((h for h in hyps if h.get("id") == hid), None)
    try:
        if args.adopter:
            if brut is None:
                sys.exit(f"✗ Hypothèse {hid!r} absente de {HYPOTHESES_PATH.name}.")
            entree = ed.adopter(brut, hid, args.portee, args.intensite, apercu=args.apercu)
            if args.apercu:
                print(f"Aperçu de l'entrée adoptée pour {hid} (rien écrit) :\n")
                print(_yaml_bloc([entree]))
                print("\nRelancer sans --apercu pour l'écrire dans evenements_custom/queue.yaml.")
            else:
                print(f"✓ {hid} adoptée : entrée ajoutée à evenements_custom/queue.yaml "
                      f"(sauvegarde queue.yaml.bak_et_si).\n"
                      f"  Injection à lancer à part : python3 generator/inject_custom_events.py --mode custom")
        elif args.rejeter:
            ed.rejeter(hid, args.motif)
            print(f"✓ {hid} rejetée" + (f" ({args.motif})" if args.motif else "") + ".")
        else:
            # V8.17.1 (PATCH_S27_GUI_DECIDER) : messages déjà préfixés ✓ / ⚠.
            ancien, messages = ed.annuler_decision(hid)
            print(f"✓ Décision retirée ({ancien}) : {hid} revient à « {ed.statut(hid)} ».")
            for m in messages:
                print(f"  {m}")
    except ed.DossierErreur as e:
        sys.exit(f"✗ {e}")


def _ecrire_operations(brut, hyp, portee, consequences, passe):
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
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » (lecture seule).")
    ap.add_argument("--id", help="id de l'hypothèse dans et_si/hypotheses.yaml")
    ap.add_argument("--lister", action="store_true", help="liste les hypothèses du fichier")
    ap.add_argument("--scenario", default=None, help="limite à un scénario")
    ap.add_argument("--date", type=float, default=2098.0, help="date de mesure de l'effet (défaut 2098)")
    ap.add_argument("--recit-ia", action="store_true", help="récit rédigé par l'IA (un appel par scénario)")
    ap.add_argument("--consequences-ia", action="store_true",
                    help="lecture des conséquences sur le lore par l'IA (un appel par scénario, payant)")
    ap.add_argument("--refaire", action="store_true", help="ignore le cache de la lecture des conséquences"
                    " (et de la passe exhaustive si elle est demandée)")
    ap.add_argument("--passe-exhaustive", action="store_true",
                    help="relit toutes les fiches de chaque scénario (et_si_exhaustif.py, payant : "
                         "≈ 0,05 à 0,11 $ par scénario, cache)")
    ap.add_argument("--report", action="store_true", help="écrit aussi documentation/need_action/et_si_<id>.md")
    ap.add_argument("--json", action="store_true", help="sortie JSON seule")
    ap.add_argument("--mode", choices=["simuler", "nouvelle"], default="simuler",
                    help="onglet du GUI (nouvelle = panneau d'écriture, rien à lancer)")
    # V8.17 : étape « décider » (et_si_dossiers.py).
    ap.add_argument("--dossiers", action="store_true", help="statut de chaque hypothèse")
    ap.add_argument("--adopter", metavar="ID",
                    help="écrit l'entrée de la dernière simulation complète dans evenements_custom/queue.yaml")
    ap.add_argument("--portee", help="avec --adopter : locale | regionale | continentale | globale")
    ap.add_argument("--intensite", help="avec --adopter : faible | modérée | forte | majeure")
    ap.add_argument("--apercu", action="store_true", help="avec --adopter : montre l'entrée, n'écrit rien")
    ap.add_argument("--rejeter", metavar="ID", help="marque l'hypothèse rejetée")
    ap.add_argument("--motif", help="avec --rejeter : raison du rejet")
    ap.add_argument("--annuler-decision", metavar="ID", help="retire la décision (adoptée ou rejetée)")
    args = ap.parse_args()
    if args.mode == "nouvelle":
        print("Mode « Nouvelle hypothèse » : écris l'idée dans le panneau ✨ ci-dessous, puis "
              "Proposer, Vérifier, Ajouter. Le bouton Lancer ne sert qu'en mode « Simuler ».")
        return

    hyps = charger_hypotheses()
    # V8.17 : étape « décider ».
    actions = [a for a in (args.dossiers, args.adopter, args.rejeter, args.annuler_decision) if a]
    if len(actions) > 1:
        sys.exit("✗ Une seule action à la fois : --dossiers, --adopter, --rejeter ou --annuler-decision.")
    if actions:
        _decider(args, hyps)
        return
    import et_si_dossiers as ed
    if (args.lister or not args.id) and args.json:
        # V7.8 : liste déroulante du GUI (/api/slugs?type=hypotheses_et_si).
        import dynamique as dyn
        from loader import VALID_VARS
        liste = []
        for h in hyps:
            _, err, _ = verifier_hypothese(dict(h), VALID_VARS, dyn)
            st = ed.statut(h.get("id"))
            nom = h.get("nom") or h.get("id")
            liste.append({"id": h.get("id"), "nom": nom if st == "non simulé" else f"{nom} · {st}",
                          "date": h.get("date"), "erreurs": err, "statut": st})
        print(json.dumps(liste, ensure_ascii=False, default=str))
        return
    if args.lister or not args.id:
        print(f"Hypothèses dans {HYPOTHESES_PATH.relative_to(VAULT_ROOT)} :")
        for h in hyps:
            print(f"  - {h.get('id', '?')} : {h.get('nom', '')} ({h.get('date', '?')}) · "
                  f"{ed.statut(h.get('id'))}")
        if not args.id:
            print("\nLancer avec --id <id> pour simuler.")
        return

    choix = [h for h in hyps if h.get("id") == args.id]
    if not choix:
        sys.exit(f"✗ Hypothèse {args.id!r} absente de {HYPOTHESES_PATH.name} (--lister pour voir les ids).")

    import dynamique as dyn
    from loader import VALID_VARS
    import copy
    brut = copy.deepcopy(choix[0])   # V8.17 : empreinte du bloc tel qu'écrit
    hyp, erreurs, avert = verifier_hypothese(choix[0], VALID_VARS, dyn)
    if erreurs:
        print(f"✗ Hypothèse {args.id!r} invalide, simulation non lancée :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)
    if args.scenario and args.scenario not in hyp["scenarios"]:
        sys.exit(f"✗ Scénario {args.scenario!r} non couvert par l'hypothèse ({', '.join(hyp['scenarios'])}).")
    if args.date < hyp["date"]:
        sys.exit(f"✗ --date {args.date:g} antérieure à l'apparition de l'hypothèse ({hyp['date']:g}).")

    resultats = simuler_hypothese(hyp, args.date, [args.scenario] if args.scenario else None)
    ajouter_recits(hyp, resultats, ia=args.recit_ia)
    consequences = {}
    if args.consequences_ia:
        consequences = ajouter_consequences(hyp, resultats,
                                            [args.scenario] if args.scenario else hyp["scenarios"],
                                            refaire=args.refaire)
    try:
        geo = evaluer_geographie(hyp, [args.scenario] if args.scenario else None)
    except Exception as e:  # la carte ne doit jamais empêcher le reste du rapport
        avert.append(f"aperçu de la carte impossible : {type(e).__name__}: {e}")
        geo = {}

    portee = [args.scenario] if args.scenario else hyp["scenarios"]
    # V8.16 : passe exhaustive, avant la liste d'application.
    passe = {}
    if args.passe_exhaustive:
        import et_si_exhaustif as ex
        for sc in portee:
            effets = (resultats.get(sc) or {}).get("effets") or []
            lecture = consequences.get(sc)
            if not lecture or lecture.get("erreur"):
                lecture = ex.lecture_en_cache(hyp, sc, effets)
            if lecture is None:
                avert.append(f"passe exhaustive ({sc}) : lecture IA absente, passe faite sans "
                             f"(cocher aussi la lecture IA)")
            print(f"[passe exhaustive] {sc}…", file=sys.stderr)
            try:
                passe[sc] = ex.passe_exhaustive(hyp, sc, effets, lecture, refaire=args.refaire)
            except Exception as e:  # la passe ne doit jamais empêcher le reste du rapport
                passe[sc] = {"erreur": f"{type(e).__name__}: {e}"}

    # V8 : liste d'application (phase 3), lecture seule.
    application = construire_application(hyp, resultats, consequences, geo, portee, passe)
    # V8.17 : dossier de l'hypothèse (dernière simulation, entrée d'injection commune).
    inj = {}
    _rendre_injection_commune(hyp, application, inj)
    # PATCH_S27_V819 : opérations structurées pour appliquer_et_si.py (phase 4).
    try:
        _ecrire_operations(brut, hyp, portee, consequences, passe)
    except Exception as e:  # ne doit jamais empêcher le rapport
        avert.append(f"opérations pour appliquer_et_si.py non écrites : {type(e).__name__}: {e}")
    try:
        ed.enregistrer_simulation(brut, hyp, portee, VERSION, inj.get("entree"), bool(passe),
                                  f"documentation/need_action/et_si_{hyp['id']}.md" if args.report else None)
    except Exception as e:  # le dossier ne doit jamais empêcher le rapport
        avert.append(f"dossier de l'hypothèse non mis à jour : {type(e).__name__}: {e}")
    sortie = {"hypothese": hyp, "date": args.date, "avertissements": avert,
              "resultats": resultats, "consequences": consequences, "geographie": geo,
              "application": application, "passe": passe}
    try:
        ETAT_PATH.parent.mkdir(parents=True, exist_ok=True)
        ETAT_PATH.write_text(json.dumps(sortie, ensure_ascii=False, default=str), encoding="utf-8")
    except OSError:
        pass

    if args.json:
        print(json.dumps(sortie, ensure_ascii=False, indent=2, default=str))
        return
    md = rendre_markdown(hyp, resultats, args.date, avert, geo, consequences, application, passe)
    print(md)
    if args.report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORT_DIR / f"et_si_{hyp['id']}.md"
        out.write_text(md, encoding="utf-8")
        # V7.7 : copie au nom fixe, affichée dans le panneau GUI.
        (REPORT_DIR / "et_si_dernier_lancement.md").write_text(md, encoding="utf-8")
        print(f"→ Rapport écrit : {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
