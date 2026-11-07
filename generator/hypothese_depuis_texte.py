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

def construire_prompt(texte, variables, type_force=None):
    ligne_type = (f"TYPE IMPOSÉ PAR L'AUTEUR : {type_force} (ne le change pas).\n\n"
                  if type_force else "")
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
    dictionnaire {{"breakdown": 1, "new_sustainability": -1, ...}} couvrant les 6 scénarios.
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


def normaliser_proposition(brut, variables, ids_pris):
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
    if est_signal:
        h["type"] = "signal"
    if description:
        h["description"] = description
    try:
        date = int(str(brut.get("date")).strip()[:4])
        plancher = max(2026, datetime.now().year) if est_signal else 2026
        if not plancher <= date <= 2097:
            av.append(f"date {date} hors de {plancher}-2097 -> ramenée dans la plage")
            date = min(2097, max(plancher, date))
        h["date"] = date
    except (TypeError, ValueError):
        av.append(f"date {brut.get('date')!r} illisible -- à renseigner")

    mode = str(brut.get("mode") or "choc").strip().lower()
    if mode not in ("choc", "rupture"):
        av.append(f"mode {mode!r} inconnu -> choc")
        mode = "choc"
    if est_signal and mode == "rupture":
        av.append("un signal n'a pas de mode rupture -> choc")
        mode = "choc"
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
    contraintes = [" ".join(str(c).split()) for c in contraintes if str(c).strip()][:4]
    if contraintes:
        h["contraintes"] = contraintes

    impacts, vues = [], set()
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
        try:
            force = int(round(abs(float(imp.get("delta_level")))))
        except (TypeError, ValueError):
            av.append(f"{var} : force illisible -> 10")
            force = 10
        fmax = SIGNAL_FORCE_MAX if est_signal else FORCE_MAX
        if not 1 <= force <= fmax:
            av.append(f"{var} : force {force} ramenée entre 1 et {fmax}")
            force = min(fmax, max(1, force))
        pol = imp.get("polarite", 1)
        if isinstance(pol, dict):
            pol = {s: (1 if str(v).strip().lstrip("+") == "1" else -1) for s, v in pol.items() if s in se.SCENARIOS}
            manquants = [s for s in se.SCENARIOS if s not in pol]
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
    if len(impacts) > MAX_IMPACTS:
        av.append(f"{len(impacts)} impacts proposés, gardé les {MAX_IMPACTS} premiers")
        impacts = impacts[:MAX_IMPACTS]
    if not impacts:
        av.append("aucun impact valide : à renseigner avant d'ajouter")
    h["impacts"] = impacts
    return h, av


def proposer(texte, _llm=appeler_llm, type_force=None):
    if not texte or not texte.strip():
        raise ValueError("idée vide")
    variables = valid_vars()
    brut = _llm(construire_prompt(texte, variables, type_force))
    if not isinstance(brut, dict):
        raise ValueError("réponse de l'IA inexploitable")
    if type_force in ("evenement", "signal"):
        brut["type"] = type_force   # le choix de l'auteur l'emporte sur celui de l'IA
    h, av = normaliser_proposition(brut, variables, ids_existants())
    _, erreurs, av2 = se.verifier_hypothese(dict(h), variables, dyn)
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
    _, err2, avert = se.verifier_hypothese(dict(h), valid_vars(), dyn)
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

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("USAGE")[0].strip(),
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    action = ap.add_mutually_exclusive_group(required=True)
    action.add_argument("--proposer", action="store_true", help="idée (entrée standard) -> bloc proposé")
    action.add_argument("--verifier", action="store_true", help="contrôle d'un bloc (entrée standard)")
    action.add_argument("--ajouter", action="store_true", help="contrôle puis ajout à hypotheses.yaml")
    ap.add_argument("--json", action="store_true", help="sortie JSON sur une ligne (GUI)")
    ap.add_argument("--type", choices=("evenement", "signal"), default=None,
                    help="avec --proposer : impose le type (sinon l'IA décide)")
    args = ap.parse_args()
    if sys.stdin.isatty():
        print("Colle le texte puis Ctrl-D :", file=sys.stderr)
    texte = sys.stdin.read()
    try:
        if args.proposer:
            res = proposer(texte, type_force=args.type)
        elif args.verifier:
            res = verifier_bloc(texte)
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
