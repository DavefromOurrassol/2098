#!/usr/bin/env python3
"""
extraire_evenements_article.py — Ourrassol 2098 (U3f, 11 novembre 2026)
=======================================================================

Lit le TEXTE COMPLET d'un article (pas seulement son chapô) et liste les événements
dont il parle, chacun avec :
  - sa description (sans rien inventer),
  - sa date telle que l'article la donne (année, mois si écrit) et si elle est explicite,
  - une citation exacte de l'article, vérifiée mot pour mot,
  - sa nature : « propre » (l'événement que raconte l'article) ou « passe » (événement
    antérieur simplement mentionné),
  - s'il semble DÉJÀ présent dans le vault (event_instances, hypothèses, evenements_cites).

Les événements postérieurs à l'article sont écartés (rien ne peut dépasser sa date).
Un appel IA (structured_strict). N'écrit rien.

USAGE
-----
    python3 generator/extraire_evenements_article.py --fichier <nom.md> --scenario breakdown \
        --annee 2098 --mois 3 [--json]
Le fichier est lu dans articles/<scenario>/<nom.md> (racine du vault).
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import yaml

RACINE_DEFAUT = Path(__file__).resolve().parent.parent
MAX_EVENEMENTS = 8
MAX_CORPS = 14000   # caractères envoyés à l'IA


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def lire_article(chemin):
    contenu = Path(chemin).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", contenu, re.DOTALL)
    if not m:
        return {}, contenu
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return (fm if isinstance(fm, dict) else {}), m.group(2)


def _fm(chemin):
    try:
        return lire_article(chemin)[0]
    except Exception:  # noqa: BLE001
        return {}


def charger_connus(racine, scenario, evenements_cites):
    """Liste (slug, nom, date) des éléments déjà connus : event_instances du scénario,
    hypothèses de et_si/hypotheses.yaml, événements cités par l'article."""
    connus = []
    dossier = Path(racine) / "event_instances"
    if dossier.is_dir():
        for f in sorted(dossier.glob("*.md")):
            if f.name.startswith("_"):
                continue
            fm = _fm(f)
            if fm.get("scenario") == scenario:
                connus.append((str(fm.get("slug") or f.stem), str(fm.get("name") or ""),
                               str(fm.get("date_label") or fm.get("date") or "")))
    hyp = Path(racine) / "et_si" / "hypotheses.yaml"
    if hyp.exists():
        try:
            for h in (yaml.safe_load(hyp.read_text(encoding="utf-8")) or {}).get("hypotheses") or []:
                if isinstance(h, dict) and h.get("id"):
                    connus.append((f"hypothese:{h['id']}", str(h.get("nom") or ""), str(h.get("date") or "")))
        except yaml.YAMLError:
            pass
    deja = {c[0] for c in connus}
    for s in evenements_cites or []:
        if str(s) not in deja:
            connus.append((str(s), "(cité par l'article)", ""))
    return connus


# ---------------------------------------------------------------------------
# IA
# ---------------------------------------------------------------------------

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]


def construire_prompt(corps, scenario, annee, mois, connus):
    lignes_connus = "\n".join(f"- {s} : {n} ({d})" for s, n, d in connus[:80]) or "(aucun)"
    return f"""Tu lis un article d'un journal fictif du monde Ourrassol 2098 (scénario « {scenario} »).
L'article est daté de {MOIS[mois - 1]} {annee}.

TEXTE DE L'ARTICLE :
<<<
{corps[:MAX_CORPS]}
>>>

TÂCHE : liste les ÉVÉNEMENTS (faits marquants et datés) dont l'article parle, y compris ceux du
passé simplement mentionnés. Au plus {MAX_EVENEMENTS}, du plus important au moins important.

RÈGLES :
- N'invente rien : chaque événement doit être dans le texte. "description" : 1 à 2 phrases qui
  reprennent ce que dit l'article, avec ses mots (chiffres, noms, dates tels quels).
- "citation" : une phrase de l'article recopiée MOT POUR MOT (15 à 40 mots), celle qui porte
  l'événement et, si elle existe, sa date.
- Date : "annee" (entier) et "mois" (1 à 12, ou null s'il n'est pas écrit). Si l'article donne
  la date, "date_explicite" vaut true. Si tu la calcules (« il y a 54 ans » depuis {annee}) ou
  si l'événement est celui que l'article raconte sans le dater, "date_explicite" vaut false : dans
  ce dernier cas utilise la date de l'article ({annee}, mois {mois}).
- Dates relatives : « en janvier dernier » ou « le 8 mars » dans un article de {MOIS[mois - 1]} {annee}
  désignent le mois le plus récent ANTÉRIEUR à l'article (pas l'année d'avant sauf si le mois n'est
  pas encore passé dans l'année de l'article). Pour toute expression relative (« dernier », « il y
  a », « récemment »), "date_explicite" vaut false.
- "nature" : "propre" = l'événement que l'article raconte comme actuel ; "passe" = événement
  antérieur simplement mentionné. N'inclus JAMAIS un événement postérieur à l'article. Un plan,
  une réforme, un débat ou un projet « en préparation » n'est PAS un événement : ne le liste pas.
- "deja_connu" : le slug EXACT de la liste ci-dessous si c'est le même événement, sinon null.

ÉLÉMENTS DÉJÀ CONNUS DU VAULT (même scénario) :
{lignes_connus}

Réponds UNIQUEMENT en JSON valide, sans texte autour :
{{"evenements": [{{"description": "...", "citation": "...", "annee": 2044, "mois": null,
  "date_explicite": true, "nature": "passe", "deja_connu": null}}]}}"""


def appeler_llm(prompt):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from llm_client import call_llm
    texte = call_llm(
        system_prompt="Tu es un assistant de world-building. Tu réponds uniquement en JSON valide.",
        user_prompt=prompt, max_tokens=3000, temperature=0.2, task_tier="structured_strict",
    ).strip()
    texte = re.sub(r"^```(?:json)?\s*", "", texte)
    texte = re.sub(r"\s*```$", "", texte)
    return json.loads(texte)


# ---------------------------------------------------------------------------
# Contrôles
# ---------------------------------------------------------------------------

def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " " + re.sub(r"[^a-z0-9]+", " ", s).strip() + " "


# U3p : marqueurs d'un plan / projet / débat (texte normalisé : minuscules, sans accents)
_MARQUEURS_PROJET = (
    " en preparation ", " se prepare ", " se preparent ", " est en projet ", " en projet ",
    " projet de ", " en discussion ", " en debat ", " fait debat ", " font debat ",
    " devrait ", " devraient ", " pourrait ", " pourraient ", " envisage ", " envisagent ",
    " envisagee ", " prevu pour ", " prevue pour ", " prevus pour ", " prevues pour ",
    " d ici 20", " a l horizon ", " sera lance ", " sera lancee ", " seront lances ",
    " sera mis en place ", " sera adopte ", " sera adoptee ", " vise a ",
)
_DEBUT_PLAN = (" plan ", " programme ", " projet ", " strategie ", " feuille de route ",
               " debat ", " reforme ", " proposition ", " initiative ")
_ACCOMPLI = (" adopte", " lance ", " lancee ", " vote", " signe", " entre en vigueur",
             " entree en vigueur", " promulgue", " ratifie", " inaugure", " active ",
             " activee ", " annonce ", " annoncee ", " adoptee ")


def motif_non_evenement(description, citation, annee_article):
    """Retourne le motif d'écart (str) si le candidat ressemble à un plan, un projet ou un
    débat, sinon None."""
    import re as _re
    desc_n = _norm(description)
    cit_n = _norm(citation)
    # 0. U3r : citation tronquée (passages recollés) ou statistique de tendance
    if _re.search(r"\[\s*(\.\.\.|…)\s*\]|…|\.\.\.", str(citation or "")):
        return "citation tronquée ([...] ou …) : passages recollés"
    if (_re.search(r" (augment\w*|bondi|chute\w*|baiss\w*|progress\w*|diminu\w*|doubl\w*|tripl\w*) (de )?\d", desc_n)
            and (" depuis " in desc_n or _re.search(r" en (une decennie|dix ans|\d+ ans) ", desc_n))):
        return "statistique de tendance (évolution chiffrée sur une durée), pas un événement"
    # 1. année postérieure à l'article écrite dans la description
    for a in _re.findall(r"\b(2[01]\d\d)\b", str(description or "")):
        if int(a) > int(annee_article):
            return f"mentionne l'année {a}, postérieure à l'article"
    # 2. marqueur de projet / futur
    for m in _MARQUEURS_PROJET:
        if m in desc_n or m in cit_n:
            return f"marqueur de projet « {m.strip()} »"
    # 3. description qui s'ouvre sur un plan / programme / débat, sans verbe d'accomplissement
    debut = " " + " ".join(desc_n.split()[:4]) + " "
    for d in _DEBUT_PLAN:
        if d in debut:
            if not any(v in desc_n for v in _ACCOMPLI):
                return f"s'ouvre sur « {d.strip()} » sans fait accompli"
            break
    return None


def _nettoyer_citation(s):
    """U3q : espaces normalisés, sans astérisques, sans guillemets englobant toute la citation."""
    s = " ".join(str(s or "").replace("*", "").split())
    paires = {"«": "»", "“": "”", '"': '"'}
    while len(s) >= 2 and s[0] in paires and s[-1] == paires[s[0]]:
        interieur = s[1:-1]
        profondeur = 0
        englobant = True
        for c in interieur:
            if c in "«“":
                profondeur += 1
            elif c in "»”":
                profondeur -= 1
                if profondeur < 0:   # le guillemet fermant du début est dans le texte : pas englobant
                    englobant = False
                    break
        if not englobant or profondeur != 0:
            break
        s = interieur.strip()
    return s


def extraire(fichier, scenario, annee, mois, racine=RACINE_DEFAUT, _llm=appeler_llm):
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+\.md", fichier or ""):
        raise ValueError(f"nom de fichier invalide : {fichier!r}")
    if not re.fullmatch(r"[a-z_]+", scenario or ""):
        raise ValueError(f"scénario invalide : {scenario!r}")
    chemin = Path(racine) / "articles" / scenario / fichier
    if not chemin.is_file():
        raise FileNotFoundError(f"article introuvable : articles/{scenario}/{fichier}")
    fm, corps = lire_article(chemin)
    annee, mois = int(annee), int(mois or 12)
    if not 1 <= mois <= 12:
        mois = 12
    connus = charger_connus(racine, scenario, fm.get("evenements_cites"))
    slugs_connus = {c[0]: c for c in connus}
    brut = _llm(construire_prompt(corps, scenario, annee, mois, connus))
    liste = brut.get("evenements") if isinstance(brut, dict) else None
    if not isinstance(liste, list):
        raise ValueError("réponse de l'IA inexploitable")
    corps_norm = _norm(corps)
    sortie, av, ecartes = [], [], []
    for i, ev in enumerate(liste[:MAX_EVENEMENTS], 1):
        if not isinstance(ev, dict) or not str(ev.get("description") or "").strip():
            continue
        try:
            an = int(ev.get("annee"))
        except (TypeError, ValueError):
            av.append(f"événement {i} sans année lisible : écarté")
            continue
        mo_brut = ev.get("mois")
        try:
            mo = int(mo_brut) if mo_brut not in (None, "") else None
        except (TypeError, ValueError):
            mo = None
        if mo is not None and not 1 <= mo <= 12:
            mo = None
        mois_connu = mo is not None
        if mo is None:
            mo = mois if an == annee else 1
        if (an * 100 + mo) > (annee * 100 + mois):
            av.append(f"« {str(ev['description'])[:60]}… » est postérieur à l'article : écarté")
            continue
        if not 2025 <= an <= 2098:
            av.append(f"« {str(ev['description'])[:60]}… » : année {an} hors de 2025-2098, écarté")
            continue
        motif = motif_non_evenement(ev.get("description"), ev.get("citation"), annee)
        if motif:
            av.append(f"« {str(ev['description'])[:60]}… » écarté (plan / projet / débat) : {motif}")
            ecartes.append({"description": " ".join(str(ev["description"]).split()), "motif": motif})
            continue
        cit = _nettoyer_citation(ev.get("citation"))
        cit_ok = bool(cit) and _norm(cit) in corps_norm
        # Contrôle mécanique : expression relative sans année écrite -> date déduite, à vérifier
        cn = _norm(cit)
        relative = (not str(an) in cit) and any(
            m in cn for m in (" dernier ", " derniere ", " derniers ", " dernieres ", " il y a ",
                              " recemment ", " l an passe ", " l annee derniere ", " le mois dernier "))
        explicite = bool(ev.get("date_explicite")) and not relative
        if relative:
            av.append(f"« {str(ev['description'])[:60]}… » : date relative dans le texte, à vérifier")
        nature = "propre" if str(ev.get("nature")).strip().lower() == "propre" else "passe"
        dk = ev.get("deja_connu")
        dk = dk if dk in slugs_connus else None   # un slug inventé par l'IA est ignoré
        sortie.append({
            "description": " ".join(str(ev["description"]).split()),
            "citation": cit, "citation_ok": cit_ok,
            "annee": an, "mois": mo, "mois_connu": mois_connu,
            "date_explicite": explicite, "date_relative": relative,
            "nature": nature,
            "deja_connu": dk,
            "deja_connu_nom": slugs_connus[dk][1] if dk else None,
        })
        if not cit_ok:
            av.append(f"« {str(ev['description'])[:60]}… » : citation introuvable mot pour mot, date à vérifier")
    return {"ok": True, "article": {"fichier": fichier, "scenario": scenario, "annee": annee, "mois": mois},
            "evenements": sortie, "avertissements": av, "ecartes": ecartes}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("USAGE")[0].strip(),
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fichier", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--annee", type=int, required=True)
    ap.add_argument("--mois", type=int, default=12)
    ap.add_argument("--racine", default=str(RACINE_DEFAUT))
    ap.add_argument("--json", action="store_true", help="sortie JSON sur une ligne (GUI)")
    args = ap.parse_args()
    try:
        res = extraire(args.fichier, args.scenario, args.annee, args.mois, racine=args.racine)
    except Exception as e:  # noqa: BLE001
        res = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    if args.json:
        print(json.dumps(res, ensure_ascii=False))
        sys.exit(0 if res.get("ok") else 1)
    if not res.get("ok"):
        sys.exit(f"✗ {res['error']}")
    for a in res["avertissements"]:
        print(f"⚠ {a}")
    for i, e in enumerate(res["evenements"], 1):
        d = f"{e['annee']}.{e['mois']:02d}" + ("" if e["date_explicite"] else " (déduite)")
        print(f"{i}. [{e['nature']}] {d} — {e['description']}")
        print(f"     « {e['citation']} » {'✓' if e['citation_ok'] else '✗ introuvable'}")
        if e["deja_connu"]:
            print(f"     ⚠ semble déjà connu : {e['deja_connu']} ({e['deja_connu_nom']})")


if __name__ == "__main__":
    main()
