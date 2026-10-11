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

SCENARIOS = ["breakdown", "fortress_world", "new_sustainability",
             "eco_communalism", "policy_reform", "reference"]
DELTA_MAX_CONSEILLE = 25   # plafond d'un événement custom (inject_custom_events.py)
ACTIONS_GEO = {"absorber": "absorber", "nouvelle_zone": "creer"}   # vocabulaire du fichier -> ZoneRepository
VERSION = "v6"            # affichée dans le rapport : permet de vérifier la version installée
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
            if action not in ACTIONS_GEO:
                erreurs.append(f"{ou} : action {action!r} inconnue (absorber | nouvelle_zone)")
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

    norm = {
        "contraintes": contraintes,
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
        propres = chocs_hypothese(hyp, sc)
        if not propres:
            continue
        sans = dyn.simuler(variables, ref, params, liens, chocs_sans, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k)
        avec = dyn.simuler(variables, ref, params, liens, chocs_sans + propres, date_fin,
                           echantillonner=ti.PAS_CHRONO, k=k)
        directes = {c["variable"] for c in propres}

        effets = []
        for v in variables:
            diff = round(avec["niveaux"][v] - sans["niveaux"][v], 1)
            if abs(diff) >= ti.SEUIL_EFFET:
                effets.append({"variable": v, "reference": ref[v], "sans": sans["niveaux"][v],
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
    brut = json.dumps({"h": {k: hyp.get(k) for k in ("nom", "description", "date", "impacts", "persistance", "contraintes")
                             if k != "contraintes" or hyp.get(k)},
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
    user = f"""Monde fictif Ourrassol 2098, scénario « {scen.get('name', sc)} » ({sc}).

LOGIQUE DU SCÉNARIO :
{_court(scen.get('summary'), 900)}
{_court(scen.get('system_logic'), 900)}

ÉLÉMENT PERTURBATEUR HYPOTHÉTIQUE (pas encore dans le lore) :
{hyp['nom']} — apparition en {hyp['date']:g}, persistance {hyp['persistance']}.
{_court(hyp['description'], 700)}
{bloc_contraintes}Variables touchées : {impacts_txt}
Effet chiffré simulé en fin de période (niveau 100 = crise) — ATTENTION : le moteur
amortit fortement les chocs (il les fait revenir vers l'équilibre du scénario) ;
juge l'ampleur de la reconfiguration d'après la nature de l'élément, pas d'après ces seuls chiffres :
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
Carte : chaque zone liste ses territoires réels ; ne propose pas de rattacher un pays à
une zone qui le contient déjà.
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
  "geographie": [{{"pays": "nom réel", "action": "absorber | nouvelle_zone", "zone": "slug (si absorber)",
                  "nouvelle_zone": {{"slug": "...", "nom": "...", "type": "...", "statut": "..."}}, "raison": "..."}}],
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
        a, b = by_inst.get(r.get("a")), by_inst.get(r.get("b"))
        typ, action = str(r.get("type") or ""), str(r.get("action") or "")
        if not a or not b or a is b:
            ecartees.append(f"relation : entités {r.get('a')!r} / {r.get('b')!r} inconnues ou identiques")
            continue
        if typ not in ("alliance", "opposition") or action not in ("nouvelle", "rompue"):
            ecartees.append(f"relation {r.get('a')} / {r.get('b')} : type ou action invalide")
            continue
        champ = "alliances" if typ == "alliance" else "oppositions"
        existe = b["slug"] in (a.get(champ) or []) or a["slug"] in (b.get(champ) or [])
        if action == "nouvelle" and existe:
            ecartees.append(f"relation {a['slug']} / {b['slug']} : {typ} déjà présente")
            continue
        if action == "rompue" and not existe:
            ecartees.append(f"relation {a['slug']} / {b['slug']} : {typ} à rompre absente du vault")
            continue
        rel.append({"a": a["slug"], "a_nom": a.get("name"), "b": b["slug"], "b_nom": b.get("name"),
                    "type": typ, "action": action, "raison": str(r.get("raison") or "")})
    out["relations"] = rel

    geo, pays_vus = [], set()
    for g in liste("geographie"):
        action = str(g.get("action") or "")
        pays = str(g.get("pays") or "").strip()
        if not pays or action not in ACTIONS_GEO:
            ecartees.append(f"carte : proposition incomplète ({pays or '?'} / {action or '?'})")
            continue
        if _plie(pays) in pays_vus:
            # V5 : deux destinations pour un même pays se contredisent ; la première est gardée.
            ecartees.append(f"carte : {pays} a déjà une proposition (seconde destination "
                            f"{g.get('zone') or (g.get('nouvelle_zone') or {}).get('slug')!r} ignorée)")
            continue
        pays_vus.add(_plie(pays))
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
    for n in liste("nouvelles_entites"):
        if not n.get("nom"):
            continue
        zone = n.get("zone")
        if zone and zone not in by_zone:
            ecartees.append(f"nouvelle entité {n.get('nom')} : zone {zone!r} inconnue (gardée sans zone)")
            zone = None
        ne.append({"nom": str(n["nom"]), "role": str(n.get("role") or ""), "zone": zone,
                   "raison": str(n.get("raison") or "")})
    out["nouvelles_entites"] = ne
    out["ecartees"] = ecartees
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



def _rendre_geo(ops):
    L = ["### Carte (aperçu, rien n'est modifié)", ""]
    for g in ops:
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
            cible = g["zone"] if g["action"] == "absorber" else (g["nouvelle_zone"] or {}).get("slug")
            L.append(f"- {g['pays']} : {g['action']} → `{cible}` — {g['raison']}")
        L.append("")
    if c.get("nouvelles_entites"):
        L.append("**Nouvelles entités plausibles**")
        for n in c["nouvelles_entites"]:
            L.append(f"- {n['nom']}" + (f" ({n['zone']})" if n.get("zone") else "") + f" : {n['role']} — {n['raison']}")
        L.append("")
    if c.get("ecartees"):
        L.append(f"_Propositions écartées au contrôle ({len(c['ecartees'])}) : " + " ; ".join(c["ecartees"][:8])
                 + (" …" if len(c["ecartees"]) > 8 else "") + "_")
        L.append("")
    return L

def rendre_markdown(hyp, resultats, date_fin, avert, geo=None, consequences=None):
    L = [f"# Et si ? — {hyp['nom']}", "",
         f"*Simulation du {datetime.now().strftime('%Y-%m-%d %H:%M')} — lecture seule, rien n'a été injecté (simulateur {VERSION}).*", ""]
    if hyp["description"]:
        L += [hyp["description"], ""]
    if hyp.get("contraintes"):
        L += ["**Faits imposés à la lecture IA** :"] + [f"- {c}" for c in hyp["contraintes"]] + [""]
    L += [f"- **Apparition** : {hyp['date']:g} · **Persistance** : {hyp['persistance']} · "
          f"**Propagation par la matrice** : {'oui' if hyp['via_matrice'] else 'non'}",
          f"- **Effet mesuré en** : {date_fin:g}"]
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
    for sc in SCENARIOS:
        r = resultats.get(sc)
        if not r and sc not in geo and sc not in consequences:
            continue
        L += [f"## {sc}", ""]
        if not r:
            if sc in consequences:
                L += _rendre_consequences(consequences[sc])
            if sc in geo:
                L += _rendre_geo(geo[sc])
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
                L.append(f"| {e['variable']} | {_virgule(e['reference'], False)} | {_virgule(e['sans'], False)} | "
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
        if sc in geo:
            L += _rendre_geo(geo[sc])
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Simulateur « et si ? » (lecture seule).")
    ap.add_argument("--id", help="id de l'hypothèse dans et_si/hypotheses.yaml")
    ap.add_argument("--lister", action="store_true", help="liste les hypothèses du fichier")
    ap.add_argument("--scenario", default=None, help="limite à un scénario")
    ap.add_argument("--date", type=float, default=2098.0, help="date de mesure de l'effet (défaut 2098)")
    ap.add_argument("--recit-ia", action="store_true", help="récit rédigé par l'IA (un appel par scénario)")
    ap.add_argument("--consequences-ia", action="store_true",
                    help="lecture des conséquences sur le lore par l'IA (un appel par scénario, payant)")
    ap.add_argument("--refaire", action="store_true", help="ignore le cache de la lecture des conséquences")
    ap.add_argument("--report", action="store_true", help="écrit aussi documentation/need_action/et_si_<id>.md")
    ap.add_argument("--json", action="store_true", help="sortie JSON seule")
    args = ap.parse_args()

    hyps = charger_hypotheses()
    if args.lister or not args.id:
        print(f"Hypothèses dans {HYPOTHESES_PATH.relative_to(VAULT_ROOT)} :")
        for h in hyps:
            print(f"  - {h.get('id', '?')} : {h.get('nom', '')} ({h.get('date', '?')})")
        if not args.id:
            print("\nLancer avec --id <id> pour simuler.")
        return

    choix = [h for h in hyps if h.get("id") == args.id]
    if not choix:
        sys.exit(f"✗ Hypothèse {args.id!r} absente de {HYPOTHESES_PATH.name} (--lister pour voir les ids).")

    import dynamique as dyn
    from loader import VALID_VARS
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

    sortie = {"hypothese": hyp, "date": args.date, "avertissements": avert,
              "resultats": resultats, "consequences": consequences, "geographie": geo}
    try:
        ETAT_PATH.parent.mkdir(parents=True, exist_ok=True)
        ETAT_PATH.write_text(json.dumps(sortie, ensure_ascii=False, default=str), encoding="utf-8")
    except OSError:
        pass

    if args.json:
        print(json.dumps(sortie, ensure_ascii=False, indent=2, default=str))
        return
    md = rendre_markdown(hyp, resultats, args.date, avert, geo, consequences)
    print(md)
    if args.report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORT_DIR / f"et_si_{hyp['id']}.md"
        out.write_text(md, encoding="utf-8")
        print(f"→ Rapport écrit : {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
