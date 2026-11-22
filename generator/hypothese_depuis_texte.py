#!/usr/bin/env python3
"""
hypothese_depuis_texte.py — Ourrassol 2098 (S27, 10 octobre 2026)
=================================================================

Assistant du simulateur « et si ? » : une IDÉE écrite librement devient une
hypothèse complète pour et_si/hypotheses.yaml (id, nom, description, date,
mode, carte, scénarios, contraintes, impacts).

Trois actions, le texte (idée ou bloc YAML) étant lu sur l'entrée standard :

    --proposer   un appel IA (structured_strict) -> bloc YAML proposé, contrôlé
                 par le MÊME verifier_hypothese() que le simulateur. N'écrit rien.
    --verifier   contrôle d'un bloc YAML (édité à la main). N'écrit rien.
    --ajouter    contrôle, puis ajout du bloc à la fin de et_si/hypotheses.yaml
                 (sauvegarde .bak_ajout, commentaires du fichier conservés,
                 relecture complète après écriture, retour arrière si illisible).
                 Seul chemin d'écriture de l'assistant.

La géographie (absorber, partition, région) n'est jamais proposée ici : elle
reste à la lecture IA du simulateur ou à une saisie manuelle dans le bloc.

USAGE
-----
    echo "une IA fait le travail de 60 % des emplois en 2040" | python3 hypothese_depuis_texte.py --proposer
    python3 hypothese_depuis_texte.py --verifier < bloc.yaml
    python3 hypothese_depuis_texte.py --ajouter --json < bloc.yaml        # sortie machine (GUI)
"""

import argparse
import json
import re
import shutil
import sys
import textwrap
import unicodedata

from datetime import datetime

import yaml

import dynamique as dyn
import simuler_et_si as se

FORCE_MAX = 25
SIGNAL_FORCE_MAX = 10   # plafond d'un signal (inject_custom_signals.py)
DUREE_MAX = 30
MAX_IMPACTS = 8
ARTICLE_MAX_IMPACTS = 3    # U4n : événement tiré d'un article, à la proposition
ARTICLE_FORCE_MAX = 12     # U4n
CATEGORIES_ENTITE = se.CATEGORIES_ENTITE   # U3aj


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def slugifier(texte):
    t = unicodedata.normalize("NFKD", str(texte or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")
    return t[:60].rstrip("_")


def valid_vars():
    from loader import VALID_VARS
    return list(VALID_VARS)


def ids_existants():
    return {str(h.get("id")) for h in se.charger_hypotheses() if h.get("id")}


def resume_variables(variables):
    try:
        from inject_custom_signals import build_variables_summary
        return build_variables_summary()
    except Exception:  # noqa: BLE001 -- repli : les slugs seuls
        return "\n".join(f"- {v}" for v in variables)


def resume_scenarios():
    lignes = []
    try:
        from loader import load_scenario
        for sc in se.SCENARIOS:
            s = load_scenario(sc) or {}
            lignes.append(f"- {sc} : {se._court(s.get('summary'), 220)}")
    except Exception:  # noqa: BLE001
        lignes = [f"- {sc}" for sc in se.SCENARIOS]
    return "\n".join(lignes)


def bloc_yaml(h):
    """Bloc prêt à coller sous `hypotheses:` (indentation 2)."""
    texte = yaml.dump([h], allow_unicode=True, sort_keys=False, default_flow_style=False, width=88)
    return "\n".join(("  " + l) if l.strip() else l for l in texte.splitlines()) + "\n"


# ---------------------------------------------------------------------------
# Proposition par l'IA
# ---------------------------------------------------------------------------

def construire_prompt(texte, variables, type_force=None, imposes=None):
    ligne_type = (f"TYPE IMPOSÉ PAR L'AUTEUR : {type_force} (ne le change pas).\n\n"
                  if type_force else "")
    if imposes:   # U3c : valeurs tirées de la source (article), imposées ensuite mécaniquement
        morceaux = []
        if imposes.get("date"):
            morceaux.append(f"date {imposes['date']}")
        if imposes.get("scenarios") is not None:
            morceaux.append("scénarios : " + (", ".join(imposes["scenarios"]) if imposes["scenarios"] else "tous"))
        if imposes.get("mode"):
            morceaux.append(f"mode {imposes['mode']}")
        if imposes.get("effet_plein"):
            morceaux.append("durées de montée calculées pour que l'effet soit à pleine force en 2098")
        if morceaux:
            ligne_type += "VALEURS IMPOSÉES PAR L'AUTEUR (ne les change pas) : " + " ; ".join(morceaux) + ".\n\n"
    if imposes and imposes.get("wild_card"):   # U4a
        ligne_type += ("WILD CARD IMPOSÉE PAR L'AUTEUR : rupture à faible probabilité et à impact majeur, "
                       "qu'aucun signal faible n'annonce encore. Type \"evenement\", mode \"rupture\", "
                       f"date entre {se.WILD_CARD_DATES[0]} et {se.WILD_CARD_DATES[1]}, "
                       f"{se.WILD_CARD_IMPACTS[0]} à {se.WILD_CARD_IMPACTS[1]} impacts, chacun de force "
                       f"{se.WILD_CARD_FORCE[0]} à {se.WILD_CARD_FORCE[1]} (cette règle prime sur le "
                       f"plafond de {FORCE_MAX} donné plus bas). Chaque impact est PERMANENT : ne retiens "
                       "que les domaines que l'élément change pour de bon à l'échelle du monde ; un domaine "
                       "qu'il apaise prend la polarité -1. Si l'élément frappe certains scénarios plus que "
                       "d'autres, \"delta_level\" peut être un dictionnaire par scénario (comme polarite, seulement les "
                       f"scénarios de l'hypothèse) : {se.WILD_CARD_FORCE[0]} à {se.WILD_CARD_FORCE[1]} dans au moins un scénario, "
                       f"{se.WILD_CARD_FORCE_MIN_SC} au moins dans les autres. Si l'élément vaut pour plusieurs "
                       "scénarios, ne nomme aucun acteur, lieu ou institution propre à l'un d'eux (le lore "
                       "diffère d'un monde à l'autre) : désigne-les par leur fonction.\n\n")   # U4d3 / U4f / U4l
    if imposes and imposes.get("citation") and not imposes.get("wild_card"):   # U4n
        ligne_type += ("ÉVÉNEMENT RAPPORTÉ PAR UN ARTICLE : c'est d'abord un fait local ou régional. "
                       f"Donne 2 à {ARTICLE_MAX_IMPACTS} impacts, de force 3 à 10 ; davantage seulement si "
                       "l'article décrit lui-même un effet à grande échelle (pays entier, continent, monde). "
                       f"Au-delà de {ARTICLE_FORCE_MAX}, la force sera ramenée.\n\n")
    return f"""{ligne_type}Tu aides l'auteur du monde fictif Ourrassol 2098 (6 scénarios d'avenir, 12 variables
où le niveau 100 = crise maximale) à transformer une IDÉE en HYPOTHÈSE « et si ? » testable
par son simulateur. L'hypothèse n'est jamais injectée : elle sert à mesurer ses effets.

IDÉE DE L'UTILISATEUR :
<<<
{texte.strip()}
>>>

LES 6 SCÉNARIOS :
{resume_scenarios()}

LES 12 VARIABLES (niveau 100 = crise) :
{resume_variables(variables)}

RÈGLES :
- "id" : snake_case sans accents, 2 à 4 mots + l'année (ex. « peste_pulmonaire_2043 »).
- "nom" : court et lisible. "description" : 1 à 4 phrases qui reprennent UNIQUEMENT ce que
  dit l'idée, avec ses mots (chiffres, dates, point d'arrivée tels quels). N'ajoute AUCUNE date,
  étape, durée, secteur, lieu, acteur ou chiffre absent de l'idée : une idée courte donne une
  description courte. Le développement viendra plus tard, de la lecture des conséquences.
- "date" : l'année d'apparition écrite dans l'idée ; sinon une année plausible entre 2026 et
  2097, et dis-le dans "justification".
- "type" : "evenement" (défaut) pour un fait marquant et daté ; "signal" pour une observation ou
  une tendance MINEURE à ses débuts, dont l'effet reste limité. Un signal : force {SIGNAL_FORCE_MAX} au
  plus, toujours mode "choc", "carte" "non", "scenarios" "tous", année entière à partir de
  {datetime.now().year}, polarité par scénario (dictionnaire des 6 scénarios) si le sens en dépend.
- "mode" : "rupture" si l'élément change le monde POUR DE BON (mortalité massive, travail
  remplacé par des machines, ressource épuisée, nouvelle espèce ou technologie qui redéfinit
  la société) ; "choc" si c'est une perturbation, même forte, dont le monde se remet.
- "persistance" (seulement en mode choc) : ephemere | normale | durable | permanente.
- "carte" : "non" sauf si l'idée fait changer de mains un territoire (conquête, sécession,
  annexion) ou en isole une partie ; alors "oui". Ne propose JAMAIS de bloc géographie.
- "scenarios" : "tous", sauf si l'idée se limite explicitement à certains scénarios.
- "impacts" : 2 à {MAX_IMPACTS} variables, une par domaine que l'idée touche DIRECTEMENT
  (pas les effets lointains : le simulateur les propage lui-même).
  - "delta_level" = FORCE, entier de 1 à {FORCE_MAX} ({FORCE_MAX} = choc majeur et mondial
    sur ce domaine ; 5 = effet secondaire net).
  - "polarite" : 1 si l'élément AGGRAVE la crise de ce domaine, -1 s'il l'APAISE. Si cela
    dépend du scénario (une même technologie libère un monde et opprime l'autre), donne un
    dictionnaire {{"breakdown": 1, "new_sustainability": -1, ...}} couvrant SEULEMENT les scénarios de l'hypothèse (les 6 si "tous") ; si le sens
    est le même partout, un seul nombre.
  - "duree" : années de montée jusqu'à pleine force (1 = brutal, 10 = progressif).
- "contraintes" : 0 à 4 phrases, chacune reprenant un fait ÉCRIT dans l'idée (chiffre, date,
  point d'arrivée), presque mot pour mot. Jamais un fait ajouté, ni tiré de ta description :
  la lecture des conséquences les traitera comme imposés par l'auteur. Dans le doute, aucune.
- "justification" : 2 phrases au plus (choix du mode, des forces).

Réponds UNIQUEMENT en JSON valide, sans texte autour :
{{"id": "...", "nom": "...", "type": "evenement", "description": "...", "date": 2040, "mode": "choc",
  "persistance": "normale", "carte": "non", "scenarios": "tous", "contraintes": ["..."],
  "impacts": [{{"variable": "slug", "delta_level": 15, "polarite": 1, "duree": 5}}],
  "justification": "..."}}"""


def appeler_llm(prompt):
    from llm_client import call_llm
    texte = call_llm(
        system_prompt="Tu es un assistant de world-building. Tu réponds uniquement en JSON valide.",
        user_prompt=prompt, max_tokens=3000, temperature=0.2, task_tier="structured_strict",
    ).strip()
    texte = re.sub(r"^```(?:json)?\s*", "", texte)
    texte = re.sub(r"\s*```$", "", texte)
    return json.loads(texte)


def normaliser_proposition(brut, variables, ids_pris, wild=False):
    """Remet la réponse de l'IA dans le format du fichier. Chaque correction
    est signalée (jamais en silence)."""
    av = []
    description = " ".join(str(brut.get("description") or "").split())
    id_ = slugifier(brut.get("id")) or slugifier(brut.get("nom")) or "hypothese"
    base, n = id_, 2
    while id_ in ids_pris:
        id_ = f"{base}_{n}"
        n += 1
    if id_ != base:
        av.append(f"id {base!r} déjà pris -> {id_!r}")
    h = {"id": id_, "nom": str(brut.get("nom") or id_).strip()}
    typ = str(brut.get("type") or "evenement").strip().lower()
    if typ not in ("evenement", "signal"):
        av.append(f"type {typ!r} inconnu -> evenement")
        typ = "evenement"
    est_signal = typ == "signal"
    if wild:   # U4a : une wild card est toujours un événement
        if est_signal:
            av.append("une wild card est un événement : type signal -> evenement")
            typ, est_signal = "evenement", False
        h["wild_card"] = True
    if est_signal:
        h["type"] = "signal"
    if description:
        h["description"] = description
    try:
        date = int(str(brut.get("date")).strip()[:4])
        plancher = max(2026, datetime.now().year) if est_signal else 2026
        plafond = 2097 if est_signal else 2098   # U3e : un événement peut aller jusqu'en 2098
        if not plancher <= date <= plafond:
            av.append(f"date {date} hors de {plancher}-{plafond} -> ramenée dans la plage")
            date = min(plafond, max(plancher, date))
        h["date"] = date
    except (TypeError, ValueError):
        av.append(f"date {brut.get('date')!r} illisible -- à renseigner")
    if wild and "date" in h:   # U4a
        a0, a1 = se.WILD_CARD_DATES
        if not a0 <= h["date"] <= a1:
            av.append(f"date {h['date']} hors de la fenêtre d'une wild card ({a0}-{a1}) -> ramenée dans la fenêtre")
            h["date"] = min(a1, max(a0, h["date"]))

    mode = str(brut.get("mode") or "choc").strip().lower()
    if mode not in ("choc", "rupture"):
        av.append(f"mode {mode!r} inconnu -> choc")
        mode = "choc"
    if est_signal and mode == "rupture":
        av.append("un signal n'a pas de mode rupture -> choc")
        mode = "choc"
    if wild and mode != "rupture":   # U4a
        av.append(f"mode {mode} -> rupture (une wild card change le monde pour de bon)")
        mode = "rupture"
    h["mode"] = mode
    if mode == "choc":
        pers = dyn.normaliser_persistance(brut.get("persistance")) or dyn.PERSISTANCE_DEFAUT
        if pers not in dyn.PERSISTANCE:
            av.append(f"persistance {brut.get('persistance')!r} inconnue -> {dyn.PERSISTANCE_DEFAUT}")
            pers = dyn.PERSISTANCE_DEFAUT
        h["persistance"] = pers
    carte = str(brut.get("carte", "non")).strip().lower()
    if carte in ("non", "no", "false", "0"):
        h["carte"] = "non"

    if est_signal:
        h["carte"] = "non"
    scen = brut.get("scenarios") or "tous"
    if isinstance(scen, list):
        valides = [s for s in scen if s in se.SCENARIOS]
        if len(valides) != len(scen):
            av.append(f"scénario(s) inconnu(s) retiré(s) : {[s for s in scen if s not in se.SCENARIOS]}")
        scen = valides if valides and len(valides) < len(se.SCENARIOS) else "tous"
    elif str(scen).strip() not in se.SCENARIOS:
        scen = "tous"
    if est_signal and scen != "tous":
        av.append("un signal couvre toujours les 6 scénarios -> tous")
        scen = "tous"
    h["scenarios"] = scen

    contraintes = brut.get("contraintes") or []
    if isinstance(contraintes, str):
        contraintes = [contraintes]
    contraintes = [" ".join(str(c).split()) for c in contraintes if str(c).strip()]
    gardees = []   # U4d6 : une date seule ou la ligne « Scénarios : … » n'est pas un fait imposé
    for c in contraintes:
        if re.fullmatch(r"(?i)(en|vers|dès|d[eè]s|à partir de|d'ici)?\s*\d{4}(\.\d{1,2})?\s*\.?", c) \
                or re.match(r"(?i)sc[ée]narios?\s*:", c):
            av.append(f"contrainte sans fait retirée : {c!r}")
        else:
            gardees.append(c)
    contraintes = gardees[:4]
    if contraintes:
        h["contraintes"] = contraintes

    impacts, vues = [], set()
    hors_pol = set()   # U4j : polarités données hors des scénarios de l'hypothèse
    for imp in (brut.get("impacts") or []):
        if not isinstance(imp, dict):
            continue
        var = str(imp.get("variable") or "").strip()
        if var not in variables:
            av.append(f"variable inconnue {var!r} retirée")
            continue
        if var in vues:
            av.append(f"variable {var} en double, première gardée")
            continue
        vues.add(var)
        fmax = SIGNAL_FORCE_MAX if est_signal else FORCE_MAX
        fmin = 1
        if wild:   # U4a
            fmin, fmax = se.WILD_CARD_FORCE
        dl = imp.get("delta_level")
        if isinstance(dl, dict):   # U4f : force par scénario
            couverts = se.SCENARIOS if scen == "tous" else list(scen)
            vals = {}
            for s_, v_ in dl.items():
                try:
                    if s_ in couverts:
                        vals[s_] = int(round(abs(float(v_))))
                except (TypeError, ValueError):
                    pass
            if not vals:
                av.append(f"{var} : forces par scénario illisibles -> 10")
                force = 10
            else:
                plancher = se.WILD_CARD_FORCE_MIN_SC if wild else 1
                for s_ in couverts:
                    if s_ not in vals:
                        vals[s_] = max(vals.values())
                        av.append(f"{var} : force absente pour {s_} -> {vals[s_]}")
                for s_, v_ in list(vals.items()):
                    if not plancher <= v_ <= fmax:
                        vals[s_] = min(fmax, max(plancher, v_))
                        av.append(f"{var} : force {v_} ({s_}) ramenée entre {plancher} et {fmax}")
                if max(vals.values()) < fmin:
                    s_max = max(vals, key=vals.get)
                    av.append(f"{var} : aucune force à {fmin} au moins -> {s_max} porté à {fmin}")
                    vals[s_max] = fmin
                force = vals if len(set(vals.values())) > 1 else next(iter(vals.values()))
        else:
            try:
                force = int(round(abs(float(dl))))
            except (TypeError, ValueError):
                av.append(f"{var} : force illisible -> 10")
                force = 10
            if not fmin <= force <= fmax:
                av.append(f"{var} : force {force} ramenée entre {fmin} et {fmax}")
                force = min(fmax, max(fmin, force))
        pol = imp.get("polarite", 1)
        if isinstance(pol, dict):
            couverts_pol = list(se.SCENARIOS) if scen == "tous" else list(scen)   # U4j
            hors_pol.update(s for s in pol if s in se.SCENARIOS and s not in couverts_pol)
            pol = {s: (1 if str(v).strip().lstrip("+") == "1" else -1) for s, v in pol.items() if s in couverts_pol}
            manquants = [s for s in couverts_pol if s not in pol]
            if manquants:
                av.append(f"{var} : polarité absente pour {manquants} -> 1 (aggrave)")
                pol.update({s: 1 for s in manquants})
            if len(set(pol.values())) == 1:
                pol = next(iter(pol.values()))
        else:
            pol = -1 if str(pol).strip() in ("-1", "-1.0") else 1
        try:
            duree = int(round(float(imp.get("duree") or 10)))
        except (TypeError, ValueError):
            duree = 10
        duree = min(DUREE_MAX, max(1, duree))
        impacts.append({"variable": var, "delta_level": force, "polarite": pol, "duree": duree})
    if hors_pol:   # U4j
        av.append("polarités données pour des scénarios hors de l'hypothèse, retirées : "
                  + ", ".join(s for s in se.SCENARIOS if s in hors_pol))
    if len(impacts) > MAX_IMPACTS:
        av.append(f"{len(impacts)} impacts proposés, gardé les {MAX_IMPACTS} premiers")
        impacts = impacts[:MAX_IMPACTS]
    if wild and len(impacts) > se.WILD_CARD_IMPACTS[1]:   # U4a
        av.append(f"{len(impacts)} impacts, gardé les {se.WILD_CARD_IMPACTS[1]} premiers (wild card)")
        impacts = impacts[:se.WILD_CARD_IMPACTS[1]]
    if not impacts:
        av.append("aucun impact valide : à renseigner avant d'ajouter")
    h["impacts"] = impacts
    return h, av


def plafonner_article_u4n(h):
    """U4n : événement tiré d'un article -> ARTICLE_MAX_IMPACTS impacts (les premiers),
    forces ramenées à ARTICLE_FORCE_MAX. Modifie h ; retourne les avertissements."""
    av = []
    impacts = list(h.get("impacts") or [])
    if len(impacts) > ARTICLE_MAX_IMPACTS:
        retires = [str(i.get("variable")) for i in impacts[ARTICLE_MAX_IMPACTS:]]
        av.append(f"événement d'article : {len(impacts)} impacts proposés, gardé les {ARTICLE_MAX_IMPACTS} "
                  f"premiers (retirés : {', '.join(retires)}) ; à remettre à la main si l'article le justifie")
        impacts = impacts[:ARTICLE_MAX_IMPACTS]
    for imp in impacts:
        dl = imp.get("delta_level")
        if isinstance(dl, dict):
            trop = {s: v for s, v in dl.items() if isinstance(v, (int, float)) and v > ARTICLE_FORCE_MAX}
            if trop:
                imp["delta_level"] = {s: (min(v, ARTICLE_FORCE_MAX) if isinstance(v, (int, float)) else v)
                                      for s, v in dl.items()}
                av.append(f"événement d'article : {imp.get('variable')} force "
                          + ", ".join(f"{s} {v:g}" for s, v in trop.items())
                          + f" ramenée à {ARTICLE_FORCE_MAX}")
        elif isinstance(dl, (int, float)) and dl > ARTICLE_FORCE_MAX:
            av.append(f"événement d'article : {imp.get('variable')} force {dl:g} ramenée à {ARTICLE_FORCE_MAX}")
            imp["delta_level"] = ARTICLE_FORCE_MAX
    h["impacts"] = impacts
    return av


def appliquer_imposes(h, imposes, est_signal):
    """U3c : date, scénarios et mode venant de la source (article), imposés APRÈS la réponse de
    l'IA. Chaque écart avec sa proposition est signalé. Retourne la liste d'avertissements."""
    av = []
    if not imposes:
        return av
    d = imposes.get("date")
    if d is not None:
        plancher = max(2026, datetime.now().year) if est_signal else 2026
        if est_signal:   # un signal commence une année entière (plafond 2097)
            d2 = min(2097, max(plancher, int(d)))
        else:   # U3e : un événement garde l'année et le mois (2098.03), plafond 2098.12
            d2 = round(min(2098.12, max(plancher, float(d))), 2)
            if d2 == int(d2):
                d2 = int(d2)
        if d2 != d:
            av.append(f"date imposée {d} hors de {plancher}-{2097 if est_signal else 2098} -> {d2}")
        if h.get("date") != d2:
            av.append(f"date imposée : {d2} (l'IA proposait {h.get('date')})")
        h["date"] = d2
    if imposes.get("effet_plein"):   # U3d : durée de montée = 2098 - date (au moins 1 an)
        n = max(1, 2098 - int(h.get("date") or 2098))
        change = False
        for imp in h.get("impacts") or []:
            if imp.get("duree") != n:
                imp["duree"] = n
                change = True
        if change:
            av.append(f"effet plein en 2098 : durée de montée portée à {n} an(s) sur tous les impacts")
    cit = " ".join(str(imposes.get("citation") or "").replace("*", "").split()).strip("«» ").strip()   # U3k

    def _plat(s):
        return " ".join(str(s).replace("*", "").replace("«", " ").replace("»", " ").split()).lower()
    if cit and not est_signal:   # U3i : la citation exacte de l'article devient un fait imposé
        contraintes = [" ".join(str(c).split()) for c in (h.get("contraintes") or [])]
        if not any(_plat(cit) in _plat(c) for c in contraintes):   # U3k
            contraintes = [cit] + contraintes
            if len(contraintes) > 4:
                av.append("une contrainte proposée par l'IA retirée (4 au maximum)")
            h["contraintes"] = contraintes[:4]
            av.append("citation de l'article ajoutée aux faits imposés")
    if est_signal:
        return av   # un signal couvre toujours les 6 scénarios, sans mode rupture
    sc = imposes.get("scenarios")
    if sc is not None:
        valides = [s for s in sc if s in se.SCENARIOS]
        if sc and not valides:
            av.append(f"scénario(s) imposé(s) inconnu(s), ignoré(s) : {sc}")
        else:
            if len(valides) != len(sc):
                av.append(f"scénario(s) imposé(s) inconnu(s) retiré(s) : {[s for s in sc if s not in se.SCENARIOS]}")
            cible = valides if 0 < len(valides) < len(se.SCENARIOS) else "tous"
            if h.get("scenarios") != cible:
                av.append(f"scénarios imposés : {cible} (l'IA proposait {h.get('scenarios')})")
            h["scenarios"] = cible
    mode = imposes.get("mode")
    if mode in ("choc", "rupture"):
        if h.get("mode") != mode:
            av.append(f"mode imposé : {mode} (l'IA proposait {h.get('mode')})")
        h["mode"] = mode
        if mode == "rupture":
            h.pop("persistance", None)
        else:
            h.setdefault("persistance", dyn.PERSISTANCE_DEFAUT)
    return av


# ---------------------------------------------------------------------------
# U3aj : proposition d'une ENTITÉ (pas de date, pas d'impact, pas de simulation)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# U3ak (14 nov 2026) : doublons d'entités à l'étape ① -- sans IA
# ---------------------------------------------------------------------------

ARTICLES_ENTITE = {"le", "la", "les", "l", "un", "une", "des", "du", "de", "d"}
SEUIL_SIMILAIRE = 0.85


def _slug_entite(nom):
    """Même slug que create_entities_and_instances.py (slugs.slugify)."""
    try:
        from slugs import slugify as _s
        return _s(str(nom or ""))
    except Exception:  # noqa: BLE001 -- repli : slug local
        return slugifier(nom)


def _mots(slug):
    return [m for m in slug.split("_") if m]


def _base_slug(slug):
    """Slug sans ses articles de tête : les_archives_de_la_maree -> archives_de_la_maree."""
    m = _mots(slug)
    while len(m) > 1 and m[0] in ARTICLES_ENTITE:
        m.pop(0)
    return "_".join(m)


def entites_existantes():
    """{slug: categorie} d'après le registre ET les fichiers entites/*.md."""
    import json as _json
    dossier = se.VAULT_ROOT / "entites"
    res = {}
    try:
        for e in _json.loads((dossier / "_entities_list.json").read_text(encoding="utf-8")):
            if isinstance(e, dict) and e.get("slug"):
                res[str(e["slug"])] = str(e.get("categorie") or e.get("category") or "?")
    except (OSError, ValueError):
        pass
    if dossier.is_dir():
        for f in dossier.glob("*.md"):
            if not f.name.startswith("_"):
                res.setdefault(f.stem, "?")
    return res


def controle_doublon_entite(nom, existantes=None):
    """(erreurs, avertissements) pour le nom d'une entité à créer."""
    import difflib
    erreurs, avert = [], []
    slug = _slug_entite(nom)
    if not slug:
        return ["nom inutilisable (slug vide)"], []
    existantes = entites_existantes() if existantes is None else existantes
    base = _base_slug(slug)
    if slug in existantes:
        erreurs.append(f"l'entité {slug!r} existe déjà ({existantes[slug]}) : "
                       "pour lui ajouter des instances, utiliser generate_instances.py")
    else:
        memes = [s for s in existantes if _base_slug(s) == base]
        for s in memes[:3]:
            erreurs.append(f"même nom que l'entité {s!r} ({existantes[s]}), à l'article près")
    mots = {m for m in _mots(base) if m not in ARTICLES_ENTITE}
    freq = {}
    for s in existantes:
        for m in set(_mots(s)):
            freq[m] = freq.get(m, 0) + 1
    proches = []
    for s, cat in existantes.items():
        if s == slug or _base_slug(s) == base:
            continue
        score = difflib.SequenceMatcher(None, base, _base_slug(s)).ratio()
        autres = {m for m in _mots(_base_slug(s)) if m not in ARTICLES_ENTITE}
        petit, grand = (mots, autres) if len(mots) <= len(autres) else (autres, mots)
        inclus = bool(petit) and petit <= grand
        if inclus and len(petit) < 2:
            m = next(iter(petit))
            inclus = len(m) >= 6 and freq.get(m, 0) < 4
        if score >= SEUIL_SIMILAIRE or inclus:
            proches.append((max(score, 0.9 if inclus else 0), s, cat))
    for _, s, cat in sorted(proches, reverse=True)[:5]:
        avert.append(f"entité proche : {s!r} ({cat}) -- vérifier qu'il ne s'agit pas de la même")
    if len(proches) > 5:
        avert.append(f"... et {len(proches) - 5} autre(s) entité(s) proche(s)")
    return erreurs, avert


def construire_prompt_entite(texte):
    return f"""TYPE IMPOSÉ PAR L'AUTEUR : entite (ne le change pas).

Tu aides l'auteur du monde fictif Ourrassol 2098 (6 scénarios d'avenir) à transformer une IDÉE en
fiche de départ d'une ENTITÉ du monde (une organisation, une IA, une institution, un lieu,
une personne...). L'entité sera créée puis déclinée dans les scénarios ; ici tu ne fais que
cadrer l'idée.

IDÉE DE L'UTILISATEUR :
<<<
{texte.strip()}
>>>

LES 6 SCÉNARIOS :
{resume_scenarios()}

RÈGLES :
- "nom" : le nom de l'entité tel qu'écrit dans l'idée (sinon un nom court et sobre). "id" :
  snake_case sans accents, 2 à 4 mots.
- "description" : 1 à 4 phrases qui reprennent UNIQUEMENT ce que dit l'idée, avec ses mots.
  N'ajoute AUCUN fait, date, lieu, chiffre ou acteur absent de l'idée : une idée courte donne
  une description courte.
- "categorie" : une valeur parmi {" | ".join(CATEGORIES_ENTITE)}.
- "scenario_ref" : le scénario où l'idée se situe SI elle en nomme un ; sinon "reference".
- "role" et "etat" : seulement si l'idée les dit (rôle de l'entité dans ce scénario, son état
  actuel) ; sinon null. Ne les invente pas.
- "scenarios" : "tous", sauf si l'idée limite explicitement l'entité à certains scénarios
  (liste de slugs).
- "annee_debut" : l'année (entre 2026 et 2098) où l'entité NAÎT dans le scénario de
  référence, SEULEMENT si l'idée la donne (« créée en 2082 », « née en 2061 »…) ; sinon
  null. Ne la déduis pas d'une autre date de l'idée (gouvernance, événement, déclin).
- "justification" : 2 phrases au plus (choix de la catégorie et du scénario de référence).

Réponds UNIQUEMENT en JSON valide, sans texte autour :
{{"id": "...", "nom": "...", "description": "...", "categorie": "institution",
  "scenario_ref": "reference", "role": null, "etat": null, "annee_debut": null, "scenarios": "tous",
  "justification": "..."}}"""


def normaliser_entite(brut, ids_pris):
    """Réponse de l'IA -> bloc d'entité. Chaque correction est signalée."""
    av = []
    nom = " ".join(str(brut.get("nom") or "").split())
    id_ = slugifier(brut.get("id")) or slugifier(nom) or "entite"
    base, n = id_, 2
    while id_ in ids_pris:
        id_ = f"{base}_{n}"
        n += 1
    if id_ != base:
        av.append(f"id {base!r} déjà pris -> {id_!r}")
    h = {"id": id_, "nom": nom or id_, "type": "entite"}
    description = " ".join(str(brut.get("description") or "").split())
    if description:
        h["description"] = description
    cat = str(brut.get("categorie") or "").strip()
    if cat not in CATEGORIES_ENTITE:
        av.append(f"categorie {cat!r} inconnue -- à choisir ({' | '.join(CATEGORIES_ENTITE)})")
    h["categorie"] = cat
    ref = str(brut.get("scenario_ref") or "").strip()
    if ref not in se.SCENARIOS:
        if ref:
            av.append(f"scenario_ref {ref!r} inconnu -> reference")
        ref = "reference"
    h["scenario_ref"] = ref
    for cle in ("role", "etat"):
        v = " ".join(str(brut.get(cle) or "").split())
        if v and v.lower() not in ("null", "none"):
            h[cle] = v
    annee = str(brut.get("annee_debut") or "").strip()   # U3aw
    if annee and annee.lower() not in ("null", "none"):
        try:
            a_ = int(float(annee))
            if 2026 <= a_ <= 2098:
                h["annee_debut"] = a_
            else:
                av.append(f"annee_debut {a_} hors de la période 2026-2098 : retirée")
        except ValueError:
            av.append(f"annee_debut {annee!r} illisible : retirée")
    scen = brut.get("scenarios") or "tous"
    if isinstance(scen, list):
        valides = [s for s in scen if s in se.SCENARIOS]
        if len(valides) != len(scen):
            av.append(f"scénario(s) inconnu(s) retiré(s) : {[s for s in scen if s not in se.SCENARIOS]}")
        scen = valides if valides and len(valides) < len(se.SCENARIOS) else "tous"
    elif str(scen).strip() not in se.SCENARIOS:
        scen = "tous"
    h["scenarios"] = scen
    return h, av


def proposer_entite(texte, _llm=appeler_llm):
    brut = _llm(construire_prompt_entite(texte))
    if not isinstance(brut, dict):
        raise ValueError("réponse de l'IA inexploitable")
    h, av = normaliser_entite(brut, ids_existants())
    _, erreurs, av2 = se.verifier_hypothese(dict(h), valid_vars(), dyn)
    e_dup, a_dup = controle_doublon_entite(h.get("nom"))   # U3ak
    erreurs = list(erreurs) + e_dup
    av2 = a_dup + list(av2)
    return {"ok": True, "bloc": bloc_yaml(h), "id": h["id"],
            "justification": str(brut.get("justification") or "").strip(),
            "avertissements": av + av2, "erreurs": erreurs}


def scenarios_depuis_idee(texte):
    """U4d5 : ligne « Scénarios : a, b. » écrite dans l'idée (bouton ⚡, suggestions 💡).
    Retourne [] pour « tous », une liste de slugs, ou None si aucune ligne lisible.
    Une ligne qui ne contient pas que des slugs de scénarios est ignorée (ex. la
    raison « Scénarios : pourquoi… » d'une idée ⚡)."""
    for m in re.finditer(r"Sc[ée]narios?\s*:\s*([^.\n]+)", texte or "", flags=re.I):
        brut = m.group(1).strip()
        if brut.lower() in ("tous", "tous les scénarios"):
            return []
        morceaux = [x.strip().lower() for x in re.split(r",|\bet\b", brut) if x.strip()]
        if morceaux and all(x in se.SCENARIOS for x in morceaux):
            valides = list(dict.fromkeys(morceaux))
            return [] if len(valides) == len(se.SCENARIOS) else valides
    return None


# ---------------------------------------------------------------------------
# U4l (22 nov 2026) : acteur propre à un monde dans une idée à plusieurs scénarios
# ---------------------------------------------------------------------------

_NOMS_INSTANCES_U4L = None


def _plie_u4l(texte):
    t = unicodedata.normalize("NFKD", str(texte or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _noms_par_scenario_u4l():
    """{nom plié: (nom affiché, {scénarios où une instance porte ce nom})}, en cache."""
    global _NOMS_INSTANCES_U4L
    if _NOMS_INSTANCES_U4L is None:
        from loader import load_instances_for_scenario
        noms = {}
        for sc in se.SCENARIOS:
            for i in load_instances_for_scenario(sc) or []:
                nom = " ".join(str((i or {}).get("name") or "").split())
                cle = _plie_u4l(nom)
                if len(cle) >= 6:
                    noms.setdefault(cle, (nom, set()))[1].add(sc)
        _NOMS_INSTANCES_U4L = noms
    return _NOMS_INSTANCES_U4L


def controle_acteurs_propres(h, _noms=None):
    """U4l : messages pour chaque nom d'instance cité par l'hypothèse qui n'existe pas
    dans tous ses scénarios. Liste vide si rien à signaler."""
    scen = (h or {}).get("scenarios") or "tous"
    if isinstance(scen, str):
        couverts = set(se.SCENARIOS) if scen.strip() in ("tous", "all") else {scen.strip()}
    else:
        couverts = {s for s in scen if s in se.SCENARIOS}
    if not couverts:
        return []
    contraintes = (h or {}).get("contraintes") or []
    if isinstance(contraintes, str):
        contraintes = [contraintes]
    texte = _plie_u4l(" ".join([str(h.get("nom") or ""), str(h.get("description") or "")]
                               + [str(c) for c in contraintes]))
    noms = _noms_par_scenario_u4l() if _noms is None else _noms
    msgs = []
    for cle, (nom, ou) in sorted(noms.items(), key=lambda x: -len(x[0])):
        if ou >= couverts:
            continue
        if not re.search(r"(?<![a-z0-9])" + re.escape(cle) + r"(?![a-z0-9])", texte):
            continue
        presents = [s for s in se.SCENARIOS if s in ou]
        msgs.append(f"acteur propre à un monde : « {nom} » n'existe que dans {', '.join(presents)} "
                    f"(hypothèse : {', '.join(s for s in se.SCENARIOS if s in couverts)}) -- le désigner par "
                    f"sa fonction, ou limiter les scénarios à ceux où il existe")
    return msgs


def proposer(texte, _llm=appeler_llm, type_force=None, imposes=None):
    if not texte or not texte.strip():
        raise ValueError("idée vide")
    if type_force == "entite":   # U3aj : parcours propre, sans date ni impact
        return proposer_entite(texte, _llm)
    wild = bool((imposes or {}).get("wild_card"))   # U4a
    if wild and type_force == "signal":
        raise ValueError("une wild card est un événement, pas un signal")
    av0 = []
    if type_force != "signal" and (imposes or {}).get("scenarios") is None:   # U4d5
        sc_idee = scenarios_depuis_idee(texte)
        if sc_idee is not None:
            imposes = dict(imposes or {}, scenarios=sc_idee)
            av0.append("scénarios repris de l'idée : " + (", ".join(sc_idee) if sc_idee else "tous"))
    variables = valid_vars()
    brut = _llm(construire_prompt(texte, variables, type_force, imposes))
    if not isinstance(brut, dict):
        raise ValueError("réponse de l'IA inexploitable")
    if type_force in ("evenement", "signal"):
        brut["type"] = type_force   # le choix de l'auteur l'emporte sur celui de l'IA
    sc_imp = (imposes or {}).get("scenarios")   # U4d5 : scénarios imposés posés avant la normalisation
    if sc_imp is not None and str(brut.get("type") or "").strip().lower() != "signal":
        v_ = [s for s in sc_imp if s in se.SCENARIOS]
        if v_ or not sc_imp:   # des noms tous inconnus restent signalés par appliquer_imposes()
            brut["scenarios"] = v_ if 0 < len(v_) < len(se.SCENARIOS) else "tous"
    h, av = normaliser_proposition(brut, variables, ids_existants(), wild=wild)
    av = av0 + av
    av += appliquer_imposes(h, imposes, h.get("type") == "signal")   # U3c
    if (imposes or {}).get("citation") and not wild and h.get("type") != "signal":   # U4n
        av += plafonner_article_u4n(h)
    _, erreurs, av2 = se.verifier_hypothese(dict(h), variables, dyn)
    erreurs = list(erreurs) + se.controle_wild_cards(h)   # U4a
    if wild:   # U4l
        erreurs += controle_acteurs_propres(h)
    return {"ok": True, "bloc": bloc_yaml(h), "id": h["id"],
            "justification": str(brut.get("justification") or "").strip(),
            "avertissements": av + av2, "erreurs": erreurs}


# ---------------------------------------------------------------------------
# Vérification et ajout d'un bloc
# ---------------------------------------------------------------------------

def normaliser_texte_bloc(texte):
    """Retire l'indentation commune du bloc. Rattrape un bloc dont seule la
    première ligne a perdu son indentation (copier-coller, champ « strippé »)."""
    lignes = (texte or "").replace("\t", "    ").splitlines()
    while lignes and not lignes[0].strip():
        lignes.pop(0)
    if lignes and not lignes[0].startswith(" "):
        reste = [len(l) - len(l.lstrip(" ")) for l in lignes[1:] if l.strip()]
        if reste and min(reste) >= 4:
            lignes[0] = " " * (min(reste) - 2) + lignes[0]
    return textwrap.dedent("\n".join(lignes)).strip("\n")


def lire_bloc(texte):
    """Bloc YAML -> (dict hypothèse, erreurs). Accepte « - id: … » (indenté ou
    non), un dictionnaire seul ou {hypotheses: [ … ]}."""
    texte = normaliser_texte_bloc(texte)
    if not texte.strip():
        return None, ["bloc vide"]
    try:
        data = yaml.safe_load(texte)
    except yaml.YAMLError as e:
        return None, [f"YAML illisible : {e}"]
    if isinstance(data, dict) and isinstance(data.get("hypotheses"), list):
        data = data["hypotheses"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        return None, ["le bloc doit contenir UNE hypothèse (« - id: … »)"]
    return data[0], []


def verifier_bloc(texte, pour_ajout=False):
    h, erreurs = lire_bloc(texte)
    if h is None:
        return {"ok": False, "erreurs": erreurs, "avertissements": [], "id": None}
    hid = str(h.get("id") or "")
    if not re.match(r"^[a-z0-9_]+$", hid):
        erreurs.append(f"id {hid!r} invalide (minuscules, chiffres et _ seulement)")
    elif pour_ajout and hid in ids_existants():
        erreurs.append(f"id {hid!r} déjà présent dans {se.HYPOTHESES_PATH.name}")
    if pour_ajout:
        # Garde-fou (10 octobre 2026) : la même idée ajoutée deux fois reçoit un
        # id suffixé (_2) à la seconde proposition ; on compare donc aussi le nom
        # et la description aux hypothèses déjà présentes.
        def plie(x):
            return " ".join(slugifier(x).split("_"))
        for autre in se.charger_hypotheses():
            if str(autre.get("id")) == hid:
                continue
            if plie(h.get("nom")) and plie(h.get("nom")) == plie(autre.get("nom")):
                erreurs.append(f"une hypothèse du même nom existe déjà : {autre.get('id')!r}")
            elif plie(h.get("description")) and plie(h.get("description")) == plie(autre.get("description")):
                erreurs.append(f"une hypothèse de même description existe déjà : {autre.get('id')!r}")
    if str(h.get("type") or "").strip().lower() == "entite":   # U3ak
        e_dup, a_dup = controle_doublon_entite(h.get("nom"))
        erreurs += e_dup
        avert_dup = a_dup
    else:
        avert_dup = []
    _, err2, avert = se.verifier_hypothese(dict(h), valid_vars(), dyn)
    err2 = list(err2) + se.controle_wild_cards(h)   # U4a : quota et espacement
    if se.est_wild_card(h):   # U4l
        err2 += controle_acteurs_propres(h)
    avert = avert_dup + list(avert)
    erreurs += err2
    return {"ok": not erreurs, "erreurs": erreurs, "avertissements": avert, "id": hid}


def ajouter_bloc(texte):
    res = verifier_bloc(texte, pour_ajout=True)
    if not res["ok"]:
        return res
    chemin = se.HYPOTHESES_PATH
    original = chemin.read_text(encoding="utf-8")
    lignes = original.splitlines()
    debut = next((i for i, l in enumerate(lignes) if re.match(r"^hypotheses:\s*(#.*)?$", l)), None)
    if debut is None:
        res.update(ok=False, erreurs=["`hypotheses:` (suivi d'une liste) introuvable dans le fichier"])
        return res
    if any(re.match(r"^[A-Za-z_][\w-]*:", l) for l in lignes[debut + 1:]):
        res.update(ok=False, erreurs=["`hypotheses:` n'est pas la dernière clé du fichier : ajout à la main"])
        return res
    bloc = normaliser_texte_bloc(texte)
    bloc = "\n".join(("  " + l) if l.strip() else "" for l in bloc.splitlines())
    nouveau = original.rstrip("\n") + "\n\n" + bloc + "\n"
    shutil.copy(chemin, chemin.with_name(chemin.name + ".bak_ajout"))
    chemin.write_text(nouveau, encoding="utf-8")
    try:
        ids = [h.get("id") for h in (yaml.safe_load(nouveau) or {}).get("hypotheses") or [] if isinstance(h, dict)]
        if ids.count(res["id"]) != 1:
            raise ValueError(f"l'id {res['id']!r} n'apparaît pas une seule fois après ajout")
    except Exception as e:  # noqa: BLE001 -- retour arrière
        chemin.write_text(original, encoding="utf-8")
        res.update(ok=False, erreurs=[f"ajout annulé, fichier restauré : {e}"])
        return res
    res["message"] = (f"{res['id']} ajoutée à {se.HYPOTHESES_PATH.name} "
                      f"(sauvegarde {chemin.name}.bak_ajout)")
    return res


# ---------------------------------------------------------------------------
# U4h (21 nov 2026) : modifier une hypothèse existante (extraire, remplacer)
# ---------------------------------------------------------------------------

STATUTS_MODIFIABLES = ("non simulé", "simulé", "rejeté", "vérifié")


def _statut_hyp(hid):
    try:
        import et_si_dossiers as ed
        return str(ed.statut(hid))
    except Exception as e:  # noqa: BLE001
        return f"inconnu ({type(e).__name__})"


def _bornes_bloc(lignes, hid):
    """(début, fin) du bloc `hid` : de « - id: hid » à la ligne avant l'hypothèse suivante,
    sans les lignes vides ni les commentaires de niveau 2 qui précèdent celle-ci (ils lui
    appartiennent). None si absent ou présent plusieurs fois."""
    debuts = [i for i, l in enumerate(lignes)
              if re.match(r"^\s*- id:\s*['\"]?" + re.escape(hid) + r"['\"]?\s*(#.*)?$", l)]
    if len(debuts) != 1:
        return None
    d = debuts[0]
    retrait = len(lignes[d]) - len(lignes[d].lstrip(" "))
    f = next((i for i in range(d + 1, len(lignes))
              if re.match(r"^\s*- id:", lignes[i]) and len(lignes[i]) - len(lignes[i].lstrip(" ")) == retrait),
             len(lignes))
    while f > d + 1 and (not lignes[f - 1].strip()
                         or (lignes[f - 1].lstrip().startswith("#")
                             and len(lignes[f - 1]) - len(lignes[f - 1].lstrip(" ")) <= retrait)):
        f -= 1
    return d, f


def extraire_bloc(hid):
    hid = str(hid or "").strip()
    if not re.fullmatch(r"[a-z0-9_]+", hid):
        return {"ok": False, "erreurs": [f"id {hid!r} invalide"], "avertissements": []}
    lignes = se.HYPOTHESES_PATH.read_text(encoding="utf-8").splitlines()
    b = _bornes_bloc(lignes, hid)
    if b is None:
        return {"ok": False, "erreurs": [f"{hid} introuvable (ou en double) dans {se.HYPOTHESES_PATH.name}"],
                "avertissements": []}
    st = _statut_hyp(hid)
    res = {"ok": True, "id": hid, "statut": st, "bloc": "\n".join(lignes[b[0]:b[1]]) + "\n",
           "erreurs": [], "avertissements": []}
    if st not in STATUTS_MODIFIABLES:
        res["ok"] = False
        res["erreurs"].append(f"{hid} est « {st} » : non modifiable (« Annuler la décision » d'abord, "
                              f"et seulement tant qu'elle n'est pas injectée)")
    elif st == "simulé":
        res["avertissements"].append("déjà simulée : après modification, la resimuler avant de décider")
    return res


def remplacer_bloc(texte):
    h, erreurs = lire_bloc(texte)
    if h is None:
        return {"ok": False, "erreurs": erreurs, "avertissements": [], "id": None}
    hid = str(h.get("id") or "")
    if hid not in ids_existants():
        return {"ok": False, "id": hid, "avertissements": [],
                "erreurs": [f"id {hid!r} absent de {se.HYPOTHESES_PATH.name} : l'id d'une hypothèse ne change "
                            "pas (pour un nouvel id, « Ajouter »)"]}
    st = _statut_hyp(hid)
    if st not in STATUTS_MODIFIABLES:
        return {"ok": False, "id": hid, "avertissements": [],
                "erreurs": [f"{hid} est « {st} » : non modifiable (« Annuler la décision » d'abord, "
                            f"et seulement tant qu'elle n'est pas injectée)"]}
    res = verifier_bloc(texte, pour_ajout=True)
    res["erreurs"] = [e for e in res["erreurs"] if not e.startswith(f"id {hid!r} déjà présent")]
    res["ok"] = not res["erreurs"]
    if not res["ok"]:
        return res
    chemin = se.HYPOTHESES_PATH
    original = chemin.read_text(encoding="utf-8")
    lignes = original.splitlines()
    b = _bornes_bloc(lignes, hid)
    if b is None:
        res.update(ok=False, erreurs=[f"bloc de {hid} introuvable (ou en double) dans le fichier : à la main"])
        return res
    d, f = b
    neuf = normaliser_texte_bloc(texte)
    retrait = " " * (len(lignes[d]) - len(lignes[d].lstrip(" ")))
    neuf_l = [(retrait + l) if l.strip() else "" for l in neuf.splitlines()]
    if neuf_l == lignes[d:f]:
        res["message"] = f"{hid} : aucun changement, rien n'est écrit"
        return res
    nouveau = "\n".join(lignes[:d] + neuf_l + lignes[f:]) + "\n"
    ids_avant = [x.get("id") for x in (yaml.safe_load(original) or {}).get("hypotheses") or [] if isinstance(x, dict)]
    shutil.copy(chemin, chemin.with_name(chemin.name + ".bak_remplacer"))
    chemin.write_text(nouveau, encoding="utf-8")
    try:
        data = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
        hyps = [x for x in data.get("hypotheses") or [] if isinstance(x, dict)]
        if [x.get("id") for x in hyps] != ids_avant:
            raise ValueError("ordre ou liste des hypothèses changé après réécriture")
        relu = next(x for x in hyps if x.get("id") == hid)
        if relu != h:
            raise ValueError("le bloc relu diffère du bloc envoyé")
    except Exception as e:  # noqa: BLE001 -- retour arrière
        chemin.write_text(original, encoding="utf-8")
        res.update(ok=False, erreurs=[f"remplacement annulé, fichier restauré : {e}"])
        return res
    res["message"] = (f"{hid} remplacée dans {chemin.name} (sauvegarde {chemin.name}.bak_remplacer)"
                      + (" ; sa dernière simulation est périmée : la relancer avant de décider"
                         if st == "simulé" else ""))
    return res


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("USAGE")[0].strip(),
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    action = ap.add_mutually_exclusive_group(required=True)
    action.add_argument("--proposer", action="store_true", help="idée (entrée standard) -> bloc proposé")
    action.add_argument("--verifier", action="store_true", help="contrôle d'un bloc (entrée standard)")
    action.add_argument("--ajouter", action="store_true", help="contrôle puis ajout à hypotheses.yaml")
    action.add_argument("--extraire", action="store_true",   # U4h
                        help="id (entrée standard) -> bloc de l'hypothèse tel qu'écrit, et son statut")
    action.add_argument("--remplacer", action="store_true",   # U4h
                        help="contrôle puis réécriture du bloc d'une hypothèse existante, à sa place")
    ap.add_argument("--json", action="store_true", help="sortie JSON sur une ligne (GUI)")
    ap.add_argument("--type", choices=("evenement", "signal", "entite"), default=None,
                    help="avec --proposer : impose le type (sinon l'IA décide)")
    ap.add_argument("--date", type=float, default=None, help="avec --proposer : date imposée (année, ou année.mois : 2098.03)")
    ap.add_argument("--scenarios", default=None,
                    help="avec --proposer : scénarios imposés (a,b,c) ou « tous »")
    ap.add_argument("--mode", choices=("choc", "rupture"), default=None,
                    help="avec --proposer : mode imposé (événement seulement)")
    ap.add_argument("--effet-plein", action="store_true",
                    help="avec --proposer : durées de montée calculées (2098 - date) pour un effet plein en 2098")
    ap.add_argument("--wild-card", action="store_true",   # U4a
                    help="avec --proposer : impose une wild card (événement, rupture, 2030-2090, "
                         "3 à 6 impacts de force 25 à 35)")
    ap.add_argument("--citation", default=None,
                    help="avec --proposer : citation exacte de l'article, ajoutée aux faits imposés (U3i)")
    args = ap.parse_args()
    if sys.stdin.isatty():
        print("Colle le texte puis Ctrl-D :", file=sys.stderr)
    texte = sys.stdin.read()
    try:
        if args.proposer:
            imposes = {}
            if args.date is not None:
                imposes["date"] = int(args.date) if args.date == int(args.date) else args.date
            if args.scenarios is not None:
                imposes["scenarios"] = ([] if args.scenarios.strip() in ("", "tous")
                                        else [s.strip() for s in args.scenarios.split(",") if s.strip()])
            if args.mode:
                imposes["mode"] = args.mode
            if args.effet_plein:
                imposes["effet_plein"] = True
            if args.citation:   # U3i
                imposes["citation"] = args.citation
            if args.wild_card:   # U4a
                imposes["wild_card"] = True
            res = proposer(texte, type_force=args.type, imposes=imposes or None)
        elif args.verifier:
            res = verifier_bloc(texte)
        elif args.extraire:   # U4h
            res = extraire_bloc(texte.strip())
        elif args.remplacer:   # U4h
            res = remplacer_bloc(texte)
        else:
            res = ajouter_bloc(texte)
    except Exception as e:  # noqa: BLE001
        res = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    if args.json:
        print(json.dumps(res, ensure_ascii=False))
        sys.exit(0 if res.get("ok") or "erreurs" in res else 1)
    if res.get("error"):
        sys.exit(f"✗ {res['error']}")
    if res.get("justification"):
        print(f"# Pourquoi : {res['justification']}")
    for a in res.get("avertissements") or []:
        print(f"# ⚠ {a}")
    for e in res.get("erreurs") or []:
        print(f"# ✗ {e}")
    if res.get("bloc"):
        print(res["bloc"])
    if res.get("message"):
        print(f"→ {res['message']}")
    elif args.verifier and res.get("ok"):
        print(f"✓ {res['id']} : bloc valide")


if __name__ == "__main__":
    main()
