#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suggerer_lacunes.py (U3aq) — propose des IDÉES d'événements ou d'entités à
partir des lacunes du vault. N'ÉCRIT RIEN : ni file d'attente, ni vault, ni
hypotheses.yaml. Chaque idée est un texte libre à coller dans « Nouvelle
hypothèse » (qui fait ensuite ✨ Proposer → Vérifier → Ajouter).

  python3 suggerer_lacunes.py --type evenement|entite [--n 5] [--scenario S] --json

Sortie (--json) : dernière ligne = {"ok": true, "type": ..., "suggestions":
[{"titre","texte","raison","avertissements"}]} ou {"ok": false, "error": ...}.
Un seul appel IA. Réutilise l'analyse de couverture et les consignes des
anciens modes Auto (bandes proche/moyen/lointain, concentration par année).
"""
import argparse
import contextlib
import io
import json
import sys


def _evenements(n, scenario):
    import inject_custom_events as ie
    cov = ie.analyze_vault_coverage()
    if scenario and scenario not in ie.SCENARIOS:
        raise ValueError(f"scénario inconnu : {scenario!r}")
    idees = ie.step_auto_generate_ideas(None, n, cov, scenario or None, None)
    sortie = []
    for i in (idees or [])[:n]:
        if not isinstance(i, dict) or not str(i.get("description") or "").strip():
            continue
        morceaux = [str(i["description"]).strip()]
        precis = []
        if i.get("date_approximative"):
            precis.append(f"vers {i['date_approximative']}")
        if i.get("portee"):
            precis.append(f"portée {i['portee']}")
        if i.get("intensite"):
            precis.append(f"intensité {i['intensite']}")
        if precis:
            morceaux.append(" ; ".join(precis).capitalize() + ".")
        if isinstance(i.get("scenarios"), list) and i["scenarios"]:
            morceaux.append("Scénarios : " + ", ".join(map(str, i["scenarios"])) + ".")
        sortie.append({"titre": str(i.get("id") or "événement"),
                       "texte": " ".join(morceaux),
                       "raison": str(i.get("rationale") or "").strip(),
                       "avertissements": []})
    return sortie


def _entites(n, scenario):
    """Idées d'entités. Prompt propre à ce script (U3ay) : contrairement au mode Auto
    d'origine, il demande une année de naissance `annee_debut` choisie pour combler
    les bandes temporelles sous-représentées, et la fait figurer dans le texte."""
    import create_entities_and_instances as ce
    if scenario and scenario not in ce.SCENARIOS:
        raise ValueError(f"scénario inconnu : {scenario!r}")
    cov = ce.analyze_entity_coverage()
    analyse = ce.build_entity_analysis_summary(cov, [scenario] if scenario else None)
    existantes_txt = ce.build_existing_entities_summary(cov["existing_entities"])
    var_summary = ce.build_variables_summary()
    orientation = (f"\nOrientation : privilégie le scénario de référence '{scenario}'." if scenario else "")
    prompt = f"""Tu dois proposer {n} idée(s) d'entités pour le projet Ourrassol 2098.
Chaque idée sera relue par l'auteur puis transformée en hypothèse : sois concret et sobre.

## ANALYSE DES DÉSÉQUILIBRES DU VAULT
{analyse}

## ENTITÉS DÉJÀ EXISTANTES (anti-doublon)
{existantes_txt}

## VARIABLES DISPONIBLES
{var_summary}
{orientation}

## CONSIGNE
- Compense les déséquilibres : zones géographiques sans instance, catégories peu présentes,
  bandes temporelles sous-représentées (proche/moyen/lointain ci-dessus).
- "annee_debut" : l'année (entre 2026 et 2098) où l'entité NAÎT dans son scénario de
  référence. Choisis-la pour rééquilibrer la distribution temporelle ; évite une année
  signalée comme concentrée ; varie les années d'une idée à l'autre ; avant 2036, l'idée doit
  se rattacher à une dynamique réelle déjà documentée.
- "etat" doit rester cohérent avec "annee_debut" : une entité née après 2070 ne peut pas être
  « résiduelle » (état réservé aux entités anciennes en déclin).
- Chaque entité a une fonction systémique distincte des existantes (même fonction, même niche
  narrative = doublon à éviter).
- "role" : 2-3 lignes, avec un lieu géographique explicite.

Réponds UNIQUEMENT en JSON, sans texte autour :
{{"entites": [{{"nom": "Nom de l'entité", "category": "{'|'.join(ce.VALID_CATEGORIES)}",
  "role": "...", "etat": "{'|'.join(ce.VALID_TRAJECTOIRE)}", "scenario_ref": "nom_du_scenario",
  "annee_debut": 2061, "rationale": "Pourquoi cette entité comble un déséquilibre (1 ligne)."}}]}}"""
    resultat = ce.call_claude_json(None, "Tu es un assistant de world-building pour Ourrassol 2098.", prompt)
    idees = resultat.get("entites", []) if isinstance(resultat, dict) else []
    try:
        import hypothese_depuis_texte as hdt
        existantes = hdt.entites_existantes()
    except Exception:
        hdt, existantes = None, None
    sortie = []
    for i in (idees or [])[:n]:
        nom = str((i or {}).get("nom") or "").strip()
        if not nom:
            continue
        avert = []
        if hdt is not None:
            err, av = hdt.controle_doublon_entite(nom, existantes)
            avert = [f"doublon probable : {e}" for e in err] + list(av)
            if err:      # une entité qui existe déjà n'est pas une lacune
                continue
        try:
            annee = int(i.get("annee_debut"))
            if not 2026 <= annee <= 2098:
                annee = None
        except (TypeError, ValueError):
            annee = None
        texte = f"Entité « {nom} » ({i.get('category') or 'autre'}). {str(i.get('role') or '').strip()}"
        if annee:
            texte += f" Née en {annee}."
        if i.get("scenario_ref"):
            texte += f" Scénario de référence : {i['scenario_ref']}."
        if i.get("etat"):
            texte += f" État : {i['etat']}."
        sortie.append({"titre": f"{nom}" + (f" ({annee})" if annee else ""), "texte": texte.strip(),
                       "raison": str(i.get("rationale") or "").strip(),
                       "avertissements": avert})
    return sortie


def _wild_cards(n, scenario):
    """U4d : idées de WILD CARDS (rupture improbable, impact majeur). Un appel IA ;
    chaque idée est contrôlée (fenêtre, quota, écart) : un problème devient un ⚠."""
    import inject_custom_events as ie
    import simuler_et_si as se
    if scenario and scenario not in se.SCENARIOS:
        raise ValueError(f"scénario inconnu : {scenario!r}")
    hyps = se.charger_hypotheses()
    signaux = []
    try:
        from loader import load_custom_signals
        signaux = [str(s.get("source_fiche") or s.get("name") or "").replace(".md", "").replace("_", " ")
                   for s in load_custom_signals() or [] if isinstance(s, dict)]
    except Exception:  # noqa: BLE001 -- repli : les hypothèses de type signal
        pass
    signaux += [str(h.get("nom") or "") for h in hyps if str(h.get("type") or "") == "signal"]
    signaux = list(dict.fromkeys(s.strip() for s in signaux if s.strip()))[:80]
    regles = []
    for sc in se.SCENARIOS:
        for rid, msg in se.regles_lore_scenario(sc) or []:
            regles.append(f"- [{sc}] {msg}")
    regles = list(dict.fromkeys(regles))
    existantes = [f"- {h.get('id')} : {h.get('nom')} ({h.get('date')}, scénarios : {h.get('scenarios') or 'tous'})"
                  for h in hyps if se.est_wild_card(h)]
    a0, a1 = se.WILD_CARD_DATES
    orientation = f"\nOrientation : au moins une idée doit toucher le scénario '{scenario}'." if scenario else ""
    prompt = f"""Tu proposes {n} WILD CARDS pour le monde fictif Ourrassol 2098 (6 scénarios d'avenir, 2026-2098).
Une wild card est une rupture à FAIBLE probabilité et à IMPACT MAJEUR, qu'aucun signal faible du monde n'annonce
encore. Elle change le monde pour de bon et a le droit d'aller contre les tendances des scénarios (ruptures
technologiques, géopolitiques, sociales, sanitaires, environnementales, spatiales…).
IMPROBABLE NE VEUT PAS DIRE IMPOSSIBLE (U4d2) : chaque idée doit rester possible selon la science actuelle,
avec un mécanisme connu (physique, biologique, technique, politique) ; un expert du domaine doit pouvoir dire
« peu probable, mais ça peut arriver ». Pas de fantastique ni de science-fiction gratuite : aucune loi physique
qui change, aucune espèce éteinte qui revient seule, aucune biologie inversée à l'échelle de la planète.
CHANGER LE MONDE ENTIER POUR DE BON (U4d3) : chaque wild card touche 3 à 6 grands domaines à la fois, et
chaque effet est PERMANENT. Elle transforme durablement le monde entier, pas une région : c'est souvent une
découverte ou une percée, positive ou négative (elle peut APAISER certains domaines et en aggraver d'autres).
Exclus : une catastrophe régionale dont les effets s'estompent en quelques années (éruption, cyclone, séisme,
accident industriel).
Bon registre : gisement exploitable sur une autre planète ou un astéroïde, signe de vie extraterrestre,
molécule qui allonge la vie humaine de 30 ans, énergie quasi gratuite, intelligence artificielle qui dépasse
l'humain dans la recherche, contrôle du climat par géo-ingénierie, pathogène qui rend une partie de l'humanité
stérile, traitement qui supprime une grande maladie, effondrement définitif d'une ressource vitale.

## SCÉNARIOS
{ie.build_scenarios_summary_for_auto(None)}

## SIGNAUX FAIBLES DÉJÀ DANS LE MONDE (une wild card ne doit PAS être annoncée par l'un d'eux)
{chr(10).join("- " + s for s in signaux) or "(aucun)"}

## RÈGLES DE LORE (choix de l'auteur, INTOUCHABLES : une wild card ne les contredit jamais)
{chr(10).join(regles) or "(aucune)"}

## WILD CARDS DÉJÀ PRÉVUES (au plus {se.WILD_CARD_QUOTA} par scénario, {se.WILD_CARD_ECART} ans d'écart au moins dans un même scénario)
{chr(10).join(existantes) or "(aucune)"}
{orientation}

## CONSIGNE
- "date" : une année entre {a0} et {a1} ; respecte le plafond et l'écart ci-dessus.
- "scenarios" (U4d4) : la LISTE des scénarios où cette rupture a du sens, d'après leur logique (1 à 4 le plus
  souvent). "tous" seulement si elle frappe vraiment le monde entier, et au plus pour une idée sur trois.
  Varie les scénarios d'une idée à l'autre. "pourquoi_scenarios" : une phrase qui justifie ce choix.
- Varie les domaines d'une idée à l'autre ; aucune ne doit reprendre une wild card déjà prévue.
- "description" : 2 ou 3 phrases concrètes (ce qui arrive, où, quelle ampleur).
- "improbable" : une phrase, pourquoi c'est improbable vu d'aujourd'hui.
- "bouscule" : une phrase, quelles tendances du monde elle contredit.

Réponds UNIQUEMENT en JSON, sans texte autour :
{{"wild_cards": [{{"titre": "...", "description": "...", "date": 2061,
  "scenarios": ["new_sustainability", "eco_communalism"], "pourquoi_scenarios": "...",
  "improbable": "...", "bouscule": "..."}}]}}"""
    res = ie.call_claude_json(None, "Tu es un auteur de prospective qui imagine des ruptures crédibles.", prompt)
    idees = res.get("wild_cards", []) if isinstance(res, dict) else []
    sortie = []
    for i in (idees or [])[:n]:
        desc = " ".join(str((i or {}).get("description") or "").split())
        if not desc:
            continue
        avert = []
        try:
            date = int(float(i.get("date")))
        except (TypeError, ValueError):
            date = None
            avert.append("date illisible : à préciser dans l'idée")
        scen = i.get("scenarios") or "tous"
        if isinstance(scen, list):
            scen = [s for s in scen if s in se.SCENARIOS] or "tous"
        elif str(scen).strip() in se.SCENARIOS:
            scen = [str(scen).strip()]
        else:
            scen = "tous"
        if date is not None:
            if not a0 <= date <= a1:
                avert.append(f"date {date} hors de la fenêtre d'une wild card ({a0}-{a1})")
            avert += se.controle_wild_cards({"id": "_suggestion_u4d", "wild_card": True, "date": date,
                                             "scenarios": scen}, hyps)
        texte = desc + (f" En {date}." if date and str(date) not in desc else "")   # U4d2
        texte += " Scénarios : " + (", ".join(scen) if isinstance(scen, list) else "tous") + "."
        raison = " · ".join(x for x in (
            f"Improbable : {' '.join(str(i.get('improbable') or '').split())}" if i.get("improbable") else "",
            f"Bouscule : {' '.join(str(i.get('bouscule') or '').split())}" if i.get("bouscule") else "",
            f"Scénarios : {' '.join(str(i.get('pourquoi_scenarios') or '').split())}"
            if i.get("pourquoi_scenarios") else "") if x)   # U4d4
        titre = " ".join(str(i.get("titre") or "wild card").split())
        sortie.append({"titre": f"⚡ {titre}" + (f" ({date})" if date else ""), "texte": texte,
                       "raison": raison, "avertissements": avert})
    return sortie


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--type", required=True, choices=["evenement", "entite", "wildcard"])   # U4d
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--scenario", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    n = max(1, min(a.n, 8))
    tampon = io.StringIO()
    try:
        # les modules historiques impriment des messages de progression :
        # on les détourne pour que la dernière ligne de stdout reste le JSON
        with contextlib.redirect_stdout(tampon):
            fonction = {"evenement": _evenements, "entite": _entites, "wildcard": _wild_cards}[a.type]   # U4d
            sugg = fonction(n, a.scenario.strip())
        res = {"ok": True, "type": a.type, "suggestions": sugg}
        if not sugg:
            res = {"ok": False, "error": "aucune suggestion exploitable (réponse IA vide)"}
    except Exception as e:      # noqa: BLE001
        res = {"ok": False, "error": f"{type(e).__name__} : {e}"}
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
    elif res["ok"]:
        for s in res["suggestions"]:
            print(f"- {s['titre']}\n  {s['texte']}\n  → {s['raison']}")
    else:
        print("✗", res["error"])
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
