#!/usr/bin/env python3
"""
fix_doublons_journalistes.py — Ourrassol 2098

Corrige les doublons de nom complet entre journalistes pro_pouvoir/
opposition d'une même zone (diagnostiqué le 26 août 2026, backlog
point 10 : 53 occurrences sur 145 zones existant des deux côtés, ~28%
-- un·e même journaliste, nom complet identique, qui écrirait à la
fois pour le pouvoir en place et l'opposition d'une même zone,
incohérent narrativement, hérité de la génération d'origine de
journaux.yaml).

Choix de conception (David, 26 août 2026) :
- Option retenue : renommage semi-automatisé par LLM (53 appels), plutôt
  que de laisser tel quel ou de renommer à la main.
- Toujours le côté OPPOSITION qui est renommé dans chaque paire --
  choix arbitraire mais cohérent, pour un comportement prévisible.
- Distinct des noms de famille PARTAGÉS entre les deux lignes d'une
  même zone (probablement voulu, cohérent narrativement -- même
  population locale, postures politiques opposées) : seuls les noms
  COMPLETS identiques sont corrigés ici.

Le nouveau nom est généré avec le contexte de ton/langue_style de
l'édition opposition (cohérence culturelle/linguistique), et vérifié
pour ne collisionner avec AUCUN nom déjà présent dans la zone (les
deux lignes, journalistes ET orateurs confondus) -- pas seulement une
consigne au LLM, une vraie validation après coup.

Chaque échec individuel (panne API transitoire, réponse invalide) est
non-bloquant -- les autres continuent, l'échec est loggé pour reprise
manuelle plutôt que de faire échouer tout le lot.

Sauvegarde automatique (26 août 2026, retour de David) : une copie
horodatée de journaux.yaml (journaux.yaml.backup_AAAAMMJJ_HHMMSS) est
créée juste avant toute écriture -- save_journaux() (generate_journaux.py)
écrase directement le fichier sans filet, et ce script touche
potentiellement des dizaines d'entrées en une seule passe.

Usage :
    python3 fix_doublons_journalistes.py --dry-run          # aperçu, appelle le LLM pour de vrai
    python3 fix_doublons_journalistes.py --limit 3          # teste sur 3 cas avant les 53
    python3 fix_doublons_journalistes.py                    # tous les doublons, écrit sur disque
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_journaux import load_journaux, save_journaux, JOURNAUX_PATH  # noqa: E402
from llm_client import call_llm, resolve_for_tier  # noqa: E402

TASK_TIER = "strict"

SYSTEM_PROMPT = (
    "Tu es l'assistant de worldbuilding du projet Ourrassol 2098 — "
    "simulateur de presse fictive en 2098. Tu renommes UN·E "
    "journaliste pour lever une collision de nom accidentelle. "
    "Réponds UNIQUEMENT avec un JSON valide. Pas de texte avant ou "
    "après. Pas de backticks."
)


def _detecter_doublons(data):
    """Reproduit exactement le diagnostic du 26 août 2026 -- liste de
    (scenario, zone, nom) pour chaque nom complet identique trouvé à la
    fois dans pro_pouvoir et opposition d'une même zone."""
    doublons = []
    for scenario, scenario_data in sorted(data.items()):
        if not isinstance(scenario_data, dict):
            continue
        pro = scenario_data.get("pro_pouvoir", {}).get("zones", {}) or {}
        opp = scenario_data.get("opposition", {}).get("zones", {}) or {}
        zones_communes = set(pro.keys()) & set(opp.keys())
        for zs in sorted(zones_communes):
            noms_pro = {j.get("nom") for j in (pro[zs].get("journalistes") or [])}
            noms_opp = {j.get("nom") for j in (opp[zs].get("journalistes") or [])}
            chevauchement = noms_pro & noms_opp
            for nom in sorted(n for n in chevauchement if n):
                doublons.append((scenario, zs, nom))
    return doublons


def _noms_existants_zone(zone_data_pro, zone_data_opp):
    """Tous les noms déjà utilisés dans cette zone, les deux lignes et
    les deux types (journalistes/orateurs) confondus -- pour valider
    qu'un nouveau nom généré ne crée pas un NOUVEAU doublon ailleurs."""
    noms = set()
    for zd in (zone_data_pro, zone_data_opp):
        for j in (zd.get("journalistes") or []):
            if j.get("nom"):
                noms.add(j["nom"])
        for o in (zd.get("orateurs") or []):
            if o.get("nom"):
                noms.add(o["nom"])
    return noms


def _build_prompt(zone_nom, ton, langue_style, ancien_nom, autres_noms):
    return """Zone : {zone_nom}
Ton éditorial de cette édition (à respecter, ne pas réinventer) : {ton}
Registre linguistique de cette édition : {langue_style}

Le/la journaliste "{ancien_nom}" de cette rédaction porte accidentellement
EXACTEMENT le même nom complet qu'un·e journaliste d'une AUTRE ligne
éditoriale de cette même zone (le pouvoir en place et l'opposition ne
devraient jamais partager le même nom de journaliste). Invente un
NOUVEAU nom complet pour remplacer "{ancien_nom}" -- culturellement et
linguistiquement cohérent avec cette zone, différent de tous les noms
déjà utilisés dans cette zone (les deux lignes confondues) : {autres_noms}.

IMPORTANT -- format du nom : n'utilise JAMAIS de guillemets doubles
ASCII (le caractère ") à l'intérieur du nom lui-même, même pour un
surnom -- ça casserait le JSON de ta réponse. Si un surnom entre
guillemets est nécessaire, utilise des guillemets français (« »)
comme dans "Prénom Nom, dit « Surnom »".

Réponds avec un objet JSON unique :
{{
  "nouveau_nom": "Prénom Nom"
}}""".format(
        zone_nom=zone_nom,
        ton=ton or "(non renseigné)",
        langue_style=langue_style or "(aucun marqueur particulier)",
        ancien_nom=ancien_nom,
        autres_noms=", ".join(sorted(autres_noms)) or "(aucun autre)",
    )


def _extraire_nom_repli(raw):
    """Repli si json.loads() échoue (26 août 2026, trouvé en conditions
    réelles sur 2 cas sur 53 -- "Expecting ',' delimiter") : extrait
    nouveau_nom par expression régulière, tolère un JSON légèrement
    malformé (ex. guillemets ASCII non échappés à l'intérieur du nom,
    malgré la consigne du prompt qui demande de ne pas en mettre)."""
    m = re.search(r'"nouveau_nom"\s*:\s*"(.+?)"\s*[,}]', raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _generer_nouveau_nom(zone_data_opp, zone_data_pro, zone_nom, ancien_nom):
    """Jusqu'à deux appels LLM (retry si collision de nom OU échec de
    parsing -- les deux cas relancent désormais une tentative, corrigé
    le 26 août 2026 : la version précédente ne retentait qu'en cas de
    collision, un échec de parsing JSON retournait immédiatement sans
    jamais utiliser le second essai, expliquant pourquoi relancer le
    script entier retombait sur le même échec). Retourne
    (nouveau_nom_ou_None, message)."""
    autres_noms = _noms_existants_zone(zone_data_pro, zone_data_opp) - {ancien_nom}
    ton = zone_data_opp.get("ton", "")
    langue_style = zone_data_opp.get("langue_style", "")

    derniere_erreur = "raison inconnue"
    for tentative in range(2):
        prompt = _build_prompt(zone_nom, ton, langue_style, ancien_nom, autres_noms)
        try:
            raw = call_llm(
                system_prompt=SYSTEM_PROMPT, user_prompt=prompt,
                max_tokens=200, temperature=0.8, task_tier=TASK_TIER,
            ).strip()
        except Exception as e:
            derniere_erreur = "Échec appel LLM : {}".format(e)
            continue

        raw_nettoye = re.sub(r"^```(?:json)?\s*", "", raw)
        raw_nettoye = re.sub(r"\s*```$", "", raw_nettoye).strip()

        try:
            reponse = json.loads(raw_nettoye)
            nouveau_nom = (reponse.get("nouveau_nom") or "").strip()
        except Exception:
            # JSON strict a échoué -- repli par regex avant d'abandonner
            # ce tour (compte quand même comme une tentative, retry
            # possible au tour suivant si toujours en échec).
            nouveau_nom = _extraire_nom_repli(raw_nettoye) or ""
            if nouveau_nom:
                print("    (JSON strict échoué, récupéré par repli regex)")

        if not nouveau_nom:
            derniere_erreur = "Réponse LLM vide ou mal formée (ni JSON ni repli)"
            continue
        if nouveau_nom in autres_noms or nouveau_nom == ancien_nom:
            # Collision -- le nom refusé est ajouté à la liste à éviter
            # avant de retenter.
            autres_noms = autres_noms | {nouveau_nom}
            derniere_erreur = "collision avec un nom déjà existant"
            continue
        return nouveau_nom, "OK"

    return None, "Deux tentatives épuisées -- {}".format(derniere_erreur)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=None,
                         help="Limiter aux N premiers doublons (pour tester avant "
                              "de lancer sur l'ensemble)")
    parser.add_argument("--dry-run", action="store_true",
                         help="⚠️ Appelle quand même le LLM pour de vrai (coût API "
                              "réel) -- seule l'écriture sur disque est court-circuitée.")
    args = parser.parse_args()

    journaux = load_journaux()
    doublons = _detecter_doublons(journaux)

    if args.limit:
        doublons = doublons[:args.limit]

    print("{} doublon(s) à traiter{}...".format(
        len(doublons), " (limité)" if args.limit else ""
    ))
    print()

    reussis = []
    echecs = []

    for i, (scenario, zone, nom) in enumerate(doublons, 1):
        print("[{}/{}] {} / {} : {}".format(i, len(doublons), scenario, zone, nom))
        zone_data_pro = journaux[scenario]["pro_pouvoir"]["zones"][zone]
        zone_data_opp = journaux[scenario]["opposition"]["zones"][zone]
        zone_nom = zone_data_opp.get("nom", zone)

        try:
            nouveau_nom, msg = _generer_nouveau_nom(zone_data_opp, zone_data_pro, zone_nom, nom)
        except Exception as e:
            # Panne API transitoire ou autre -- non-bloquant, les
            # autres doublons continuent (vécu en réel le 26 août :
            # erreur 503 Mistral en pleine session).
            nouveau_nom, msg = None, "Exception inattendue : {}".format(e)

        if not nouveau_nom:
            print("  ✗ {}".format(msg))
            echecs.append((scenario, zone, nom, msg))
            continue

        for j in zone_data_opp.get("journalistes", []):
            if j.get("nom") == nom:
                j["nom"] = nouveau_nom
                break

        print("  ✓ {} → {}".format(nom, nouveau_nom))
        reussis.append((scenario, zone, nom, nouveau_nom))

    print()
    print("=" * 70)
    print("RÉSUMÉ -- {} renommage(s) réussi(s), {} échec(s)".format(
        len(reussis), len(echecs)))
    print("=" * 70)
    if echecs:
        print("Échecs (à traiter manuellement ou relancer plus tard) :")
        for scenario, zone, nom, msg in echecs:
            print("  {} / {} / {} -- {}".format(scenario, zone, nom, msg))

    if args.dry_run:
        print()
        print("[dry-run] Rien écrit sur disque.")
        return

    if not reussis:
        print()
        print("Aucun renommage réussi -- journaux.yaml non modifié.")
        return

    # Sauvegarde de sécurité (26 août 2026, retour de David) --
    # save_journaux() (generate_journaux.py) écrase directement le
    # fichier, sans aucune sauvegarde préalable -- vu qu'on touche
    # potentiellement des dizaines d'entrées d'un coup, une copie
    # horodatée est faite AVANT toute écriture, pour pouvoir revenir en
    # arrière si un renommage s'avère mauvais après coup.
    backup_path = JOURNAUX_PATH + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(JOURNAUX_PATH, backup_path)
    print()
    print("  ✓ Sauvegarde créée : {}".format(backup_path))

    save_journaux(journaux, dry_run=False)
    print("  ✓ journaux.yaml sauvegardé ({} renommage(s)).".format(len(reussis)))


if __name__ == "__main__":
    main()
