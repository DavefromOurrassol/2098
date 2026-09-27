#!/usr/bin/env python3
"""
reevaluer_polarites.py — Ourrassol 2098
----------------------------------------
Étape 6 du chantier "convention unique d'intensité" (27 septembre 2026).

Les polarités déjà stockées dans le vault ont été écrites par le LLM
AVANT la convention actuelle (level 0 = calme, 100 = crise ; polarite
+1 = aggrave, -1 = apaise ; delta_level = force positive). Elles ne sont
pas fiables : le LLM mélangeait "sens sur l'ancienne échelle" et "bon/
mauvais pour le monde". Aucune règle mécanique ne peut les corriger --
ce script redemande au LLM, fiche par fiche, le SENS de chaque impact
avec la nouvelle convention. La FORCE (|delta_level|) et la durée ne
changent jamais.

Sources :
  - event_instances/*.md  frontmatter -> impact_sur_variables
  - instances/*.md        frontmatter -> injection.impact_sur_variables
                          (uniquement injection.type = custom)
  - signaux_custom/*.md   bloc ```yaml impact_sur_variables``` (un sens
                          PAR SCÉNARIO, le récit différant d'un scénario
                          à l'autre)

DEUX TEMPS, pour pouvoir relire avant d'écrire :

  1. Sans option (ou --limit N) : SIMULATION. Appelle le LLM pour les
     fiches pas encore évaluées, garde les réponses dans
     generator/state/reevaluation_polarites.json, et écrit le rapport
     documentation/need_action/reevaluation_polarites.md. Aucune fiche
     du vault n'est modifiée. Relançable : les fiches déjà évaluées ne
     sont pas redemandées au LLM.
  2. --appliquer : AUCUN appel LLM. Écrit dans les fiches les décisions
     déjà en cache (delta_level passe en valeur absolue, polarite prend
     la valeur décidée), avec sauvegarde unique .bak_etape6, relecture et
     vérification. Une fiche modifiée depuis son évaluation est ignorée.

Usage (depuis la racine du vault) :
  python3 generator/reevaluer_polarites.py --limit 5    # essai sur 5 fiches
  python3 generator/reevaluer_polarites.py              # tout évaluer
  python3 generator/reevaluer_polarites.py --appliquer  # écrire
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

from echelles import CONVENTION_NIVEAUX, CONSIGNE_IMPACT, texte_echelle

VAULT_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = Path(__file__).resolve().parent / "state" / "reevaluation_polarites.json"
REPORT_PATH = VAULT_ROOT / "documentation" / "need_action" / "reevaluation_polarites.md"


# ─────────────────────────────────────────
# Lecture
# ─────────────────────────────────────────

def decouper(raw):
    m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*\n", raw, re.DOTALL)
    if not m:
        return None
    return m


def yaml_propre(txt):
    return yaml.safe_load(re.sub(r"\[\[([^\]]+)\]\]", r"\1", txt)) or {}


def empreinte(raw):
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def court(txt, n=600):
    txt = re.sub(r"\s+", " ", str(txt or "")).strip()
    return txt[:n] + (" …" if len(txt) > n else "")


def collecter():
    """Retourne une liste de fiches à évaluer :
    {rel, kind, raw, contexte, impacts:[{cle, variable, scenario, delta, pol}]}"""
    fiches = []

    d = VAULT_ROOT / "event_instances"
    for path in sorted(d.glob("*.md")) if d.is_dir() else []:
        raw = path.read_text(encoding="utf-8")
        m = decouper(raw)
        if not m:
            continue
        try:
            fm = yaml_propre(m.group(1))
        except yaml.YAMLError:
            continue
        imps = [i for i in (fm.get("impact_sur_variables") or []) if isinstance(i, dict)]
        if not imps or fm.get("impossible"):
            continue
        fiches.append({
            "rel": str(path.relative_to(VAULT_ROOT)), "kind": "evenement", "raw": raw,
            "contexte": (f"ÉVÉNEMENT « {fm.get('name', path.stem)} » — scénario {fm.get('scenario')}, "
                         f"{fm.get('date_label') or fm.get('date')}\n"
                         f"Description : {court(fm.get('description'))}\n"
                         f"Conséquences : {court(fm.get('consequences'))}"),
            "impacts": [{"cle": i.get("variable"), "variable": i.get("variable"), "scenario": fm.get("scenario"),
                         "delta": i.get("delta_level", 0), "pol": i.get("polarite", 1)} for i in imps],
        })

    d = VAULT_ROOT / "instances"
    for path in sorted(d.glob("*.md")) if d.is_dir() else []:
        raw = path.read_text(encoding="utf-8")
        if "impact_sur_variables" not in raw:
            continue
        m = decouper(raw)
        if not m:
            continue
        try:
            fm = yaml_propre(m.group(1))
        except yaml.YAMLError:
            continue
        inj = fm.get("injection") or {}
        if not isinstance(inj, dict) or inj.get("type") != "custom":
            continue
        imps = [i for i in (inj.get("impact_sur_variables") or []) if isinstance(i, dict)]
        if not imps:
            continue
        fiches.append({
            "rel": str(path.relative_to(VAULT_ROOT)), "kind": "entite", "raw": raw,
            "contexte": (f"ENTITÉ « {fm.get('name', path.stem)} » — scénario {fm.get('scenario')}\n"
                         f"Rôle : {court(fm.get('role_dans_scenario'))}\n"
                         f"Raison de l'impact : {court(inj.get('contexte_injection'), 300)}"),
            "impacts": [{"cle": i.get("variable"), "variable": i.get("variable"), "scenario": fm.get("scenario"),
                         "delta": i.get("delta_level", 0), "pol": i.get("polarite", 1)} for i in imps],
        })

    d = VAULT_ROOT / "signaux_custom"
    for path in sorted(d.glob("*.md")) if d.is_dir() else []:
        raw = path.read_text(encoding="utf-8")
        m = re.search(r"```yaml\nimpact_sur_variables:\n(.*?)\n```", raw, re.DOTALL)
        if not m:
            continue
        try:
            blocs = yaml_propre("impact_sur_variables:\n" + m.group(1)).get("impact_sur_variables") or []
        except yaml.YAMLError:
            continue
        idee = re.search(r"## Idée source\s*\n(.*?)(?=\n## |\Z)", raw, re.DOTALL)
        evolutions = {}
        m_traj = re.search(r"```yaml\nsignal_to_state:\n(.*?)\n```", raw, re.DOTALL)
        if m_traj:
            try:
                for e in yaml_propre("signal_to_state:\n" + m_traj.group(1)).get("signal_to_state") or []:
                    for sc, dd in (e.get("scenarios") or {}).items():
                        evolutions[sc] = f"{(dd or {}).get('evolution', '')} ({(dd or {}).get('evenement_cle', '')})"
            except yaml.YAMLError:
                pass
        impacts = []
        for b in blocs:
            if not isinstance(b, dict):
                continue
            for sc, dd in (b.get("scenarios") or {}).items():
                if isinstance(dd, dict):
                    impacts.append({"cle": f"{b.get('variable')}|{sc}", "variable": b.get("variable"),
                                    "scenario": sc, "delta": dd.get("delta_level", 0), "pol": dd.get("polarite", 1)})
        if not impacts:
            continue
        evo_txt = "\n".join(f"  - {sc} : {court(t, 200)}" for sc, t in evolutions.items())
        fiches.append({
            "rel": str(path.relative_to(VAULT_ROOT)), "kind": "signal", "raw": raw,
            "contexte": (f"SIGNAL FAIBLE « {path.stem} »\n"
                         f"Idée source : {court(idee.group(1) if idee else '', 400)}\n"
                         f"Évolution du signal selon le scénario :\n{evo_txt}"),
            "impacts": impacts,
        })
    return fiches


# ─────────────────────────────────────────
# LLM
# ─────────────────────────────────────────

def demander_llm(fiche):
    from llm_client import call_llm
    lignes = []
    for imp in fiche["impacts"]:
        sc = f" [scénario {imp['scenario']}]" if fiche["kind"] == "signal" else ""
        lignes.append(f'- cle "{imp["cle"]}" : variable {imp["variable"]}{sc}, force {abs(float(imp["delta"] or 0)):g} '
                      f'(échelle : {texte_echelle(imp["variable"]) or "non définie"})')
    user = f"""Tu réévalues le SENS des impacts chiffrés d'un élément du simulateur Ourrassol 2098.

{fiche['contexte']}

{CONVENTION_NIVEAUX}
{CONSIGNE_IMPACT}

IMPACTS À ÉVALUER (la force est déjà fixée, tu choisis seulement le sens) :
{chr(10).join(lignes)}

Pour chaque impact, décide si cet élément fait MONTER (polarite 1) ou BAISSER
(polarite -1) le niveau de la variable, en raisonnant avec l'échelle
indiquée et avec ce qui se passe réellement dans l'élément décrit.

Réponds UNIQUEMENT en JSON, sans texte autour :
{{"impacts": [{{"cle": "...", "polarite": 1, "justification": "une phrase courte"}}]}}"""
    txt = call_llm(system_prompt="Tu es un assistant de world-building rigoureux.", user_prompt=user,
                   max_tokens=1500, temperature=0.0, task_tier="structured_strict").strip()
    txt = re.sub(r"^```(?:json)?\s*", "", txt)
    txt = re.sub(r"\s*```$", "", txt)
    data, _ = json.JSONDecoder().raw_decode(txt)
    rep = {}
    for r in data.get("impacts") or []:
        if isinstance(r, dict) and r.get("polarite") in (1, -1, "1", "-1"):
            rep[str(r.get("cle"))] = {"pol": int(r["polarite"]), "why": str(r.get("justification", ""))[:200]}
    manquants = [i["cle"] for i in fiche["impacts"] if i["cle"] not in rep]
    if manquants:
        raise ValueError(f"réponse incomplète, clés manquantes : {manquants}")
    return rep


# ─────────────────────────────────────────
# Écriture
# ─────────────────────────────────────────

def reecrire_bloc(texte, decisions_par_item):
    """Dans `texte` (YAML brut), pour chaque item '- variable: X', remplace
    toutes les lignes delta_level/polarite du bloc de l'item.
    decisions_par_item(variable, scenario_ou_None) -> polarite.
    Pour les signaux, le scénario courant est la dernière clé de scénario
    rencontrée dans le bloc."""
    scen_ok = {"breakdown", "fortress_world", "new_sustainability", "eco_communalism", "policy_reform", "reference"}
    lignes = texte.split("\n")
    i = 0
    while i < len(lignes):
        m = re.match(r"^(\s*)- variable:\s*\[*([a-z_]+)\]*\s*$", lignes[i])
        if not m:
            i += 1
            continue
        indent, var = len(m.group(1)), m.group(2)
        scen = None
        j = i + 1
        while j < len(lignes):
            l = lignes[j]
            if l.strip() and (len(l) - len(l.lstrip())) <= indent:
                break
            ms = re.match(r"^\s*([a-z_]+):\s*$", l)
            if ms and ms.group(1) in scen_ok:
                scen = ms.group(1)
            md = re.match(r"^(\s*delta_level:\s*)(-?\d+(?:\.\d+)?)\s*$", l)
            if md:
                v = abs(float(md.group(2)))
                lignes[j] = f"{md.group(1)}{int(v) if v == int(v) else v}"
            mp = re.match(r"^(\s*polarite:\s*)(-?\d+)\s*$", l)
            if mp:
                pol = decisions_par_item(var, scen)
                if pol is not None:
                    lignes[j] = f"{mp.group(1)}{pol}"
            j += 1
        i = j
    return "\n".join(lignes)


def appliquer_fiche(fiche, dec):
    raw = fiche["raw"]
    if fiche["kind"] == "signal":
        m = re.search(r"(```yaml\nimpact_sur_variables:\n)(.*?)(\n```)", raw, re.DOTALL)
        nouveau_bloc = reecrire_bloc(m.group(2), lambda v, s: dec.get(f"{v}|{s}", {}).get("pol"))
        nouveau = raw[:m.start(2)] + nouveau_bloc + raw[m.end(2):]
    else:
        m = decouper(raw)
        fm_neuf = reecrire_bloc(m.group(1), lambda v, s: dec.get(v, {}).get("pol"))
        corps = raw[m.end():]
        if fiche["kind"] == "evenement":
            # Section "Impact sur les variables" du corps : effet réel affiché
            for imp in fiche["impacts"]:
                eff = abs(float(imp["delta"] or 0)) * dec[imp["cle"]]["pol"]
                corps = re.sub(r"(- \*\*" + re.escape(imp["variable"]) + r"\*\* : delta )[+-]?\d+(?:\.\d+)?",
                               lambda mm: f"{mm.group(1)}{eff:+g}", corps, count=1)
        nouveau = raw[:m.start(1)] + fm_neuf + raw[m.end(1):m.end()] + corps
    return nouveau


def verifier(fiche, nouveau, dec):
    """Relit la fiche réécrite et vérifie delta >= 0 et polarites attendues."""
    if fiche["kind"] == "signal":
        m = re.search(r"```yaml\nimpact_sur_variables:\n(.*?)\n```", nouveau, re.DOTALL)
        blocs = yaml_propre("impact_sur_variables:\n" + m.group(1)).get("impact_sur_variables") or []
        lus = {f"{b['variable']}|{sc}": d for b in blocs for sc, d in (b.get("scenarios") or {}).items()}
    else:
        fm = yaml_propre(decouper(nouveau).group(1))
        imps = fm.get("impact_sur_variables") if fiche["kind"] == "evenement" else (fm.get("injection") or {}).get("impact_sur_variables")
        lus = {i["variable"]: i for i in imps or []}
    for imp in fiche["impacts"]:
        d = lus.get(imp["cle"])
        if not d or float(d.get("delta_level", 0)) < 0 or int(d.get("polarite", 0)) != dec[imp["cle"]]["pol"]:
            return False
    return True


# ─────────────────────────────────────────

def charger_cache():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def sauver_cache(cache):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def rapport(fiches, cache):
    lignes = ["# Réévaluation des polarités (étape 6)", "",
              "Effet = force × sens, AVANT (calcul actuel, abs(delta) × ancienne polarite) → APRÈS (décision LLM).", ""]
    n_tot = n_chg = n_eval = 0
    corps = []
    for f in fiches:
        c = cache.get(f["rel"])
        if not c or c.get("empreinte") != empreinte(f["raw"]):
            continue
        n_eval += 1
        rows = []
        for imp in f["impacts"]:
            force = abs(float(imp["delta"] or 0))
            av = force * (1 if int(imp["pol"] or 1) >= 0 else -1)
            ap = force * c["decisions"][imp["cle"]]["pol"]
            n_tot += 1
            chg = (av > 0) != (ap > 0)
            n_chg += chg
            rows.append(f"| {imp['cle']} | {av:+g} | {ap:+g} | {'**inversé**' if chg else ''} | {c['decisions'][imp['cle']]['why']} |")
        corps += [f"### {f['rel']}", "", "| Impact | Avant | Après | | Justification |", "|---|---|---|---|---|", *rows, ""]
    lignes += [f"Fiches évaluées : {n_eval} / {len(fiches)} — impacts : {n_tot}, dont **{n_chg} changent de sens**.", ""]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lignes + corps), encoding="utf-8")
    return n_eval, n_tot, n_chg


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--appliquer", action="store_true", help="Écrit les décisions en cache (aucun appel LLM)")
    ap.add_argument("--limit", type=int, default=None, help="Nombre max de NOUVELLES fiches à évaluer")
    args = ap.parse_args()

    fiches = collecter()
    cache = charger_cache()
    par_type = {k: sum(1 for f in fiches if f["kind"] == k) for k in ("evenement", "entite", "signal")}
    print(f"Fiches avec impacts : {len(fiches)} ({par_type['evenement']} événements, "
          f"{par_type['entite']} entités custom, {par_type['signal']} signaux)")

    if not args.appliquer:
        a_faire = [f for f in fiches if cache.get(f["rel"], {}).get("empreinte") != empreinte(f["raw"])]
        if args.limit is not None:
            a_faire = a_faire[:args.limit]
        print(f"À évaluer par le LLM : {len(a_faire)}")
        echecs = []
        for k, f in enumerate(a_faire, 1):
            print(f"  [{k}/{len(a_faire)}] {f['rel']}")
            rep = None
            for essai in range(2):
                try:
                    rep = demander_llm(f)
                    break
                except Exception as e:
                    print(f"      ⚠ essai {essai + 1} : {e}")
            if rep is None:
                echecs.append(f["rel"])
                continue
            cache[f["rel"]] = {"empreinte": empreinte(f["raw"]), "decisions": rep}
            sauver_cache(cache)
        n_eval, n_tot, n_chg = rapport(fiches, cache)
        print(f"\nÉvaluées au total : {n_eval}/{len(fiches)} fiches, {n_tot} impacts, {n_chg} changent de sens.")
        if echecs:
            print(f"Échecs LLM ({len(echecs)}) : relancer le script pour les réessayer.")
        print(f"Rapport : {REPORT_PATH.relative_to(VAULT_ROOT)}  (aucune fiche du vault modifiée)")
        return 0

    # --appliquer
    ecrites = ignorees = erreurs = 0
    for f in fiches:
        c = cache.get(f["rel"])
        if not c:
            continue
        if c.get("empreinte") != empreinte(f["raw"]):
            ignorees += 1
            continue
        nouveau = appliquer_fiche(f, c["decisions"])
        if not verifier(f, nouveau, c["decisions"]):
            print(f"  ✗ {f['rel']} : vérification échouée, non écrit")
            erreurs += 1
            continue
        if nouveau != f["raw"]:
            path = VAULT_ROOT / f["rel"]
            bak = path.with_suffix(path.suffix + ".bak_etape6")
            if not bak.exists():
                bak.write_text(f["raw"], encoding="utf-8")
            path.write_text(nouveau, encoding="utf-8")
            ecrites += 1
    non_eval = sum(1 for f in fiches if f["rel"] not in cache)
    print(f"Fiches écrites : {ecrites} | déjà conformes ou modifiées depuis l'évaluation : {ignorees} | "
          f"erreurs : {erreurs} | pas encore évaluées : {non_eval}")
    return 0 if not erreurs else 1


if __name__ == "__main__":
    sys.exit(main())
