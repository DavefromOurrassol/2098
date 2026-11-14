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


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--type", required=True, choices=["evenement", "entite"])
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
            sugg = (_evenements if a.type == "evenement" else _entites)(n, a.scenario.strip())
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
