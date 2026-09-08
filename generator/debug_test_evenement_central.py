#!/usr/bin/env python3
"""
debug_test_evenement_central.py — Ourrassol 2098
==================================================

Outil de calibrage pour la consigne LLM de
detect_evenements_cites_retroactif.py (fonction _llm_confirm_events).

Contrairement au script principal (qui ne demande qu'un JSON minimal
pour rester bon marché sur des dizaines/centaines d'articles), cet
outil demande en plus une JUSTIFICATION d'une phrase par candidat --
utile pour comprendre POURQUOI le LLM confirme ou rejette un cas
précis, avant de retoucher la consigne à l'aveugle sur des batches
entiers.

Ne modifie rien sur disque -- affichage seul.

USAGE
-----
    # Teste un couple (article, événement) précis
    python3 debug_test_evenement_central.py \\
        --article "articles/new_sustainability/20260822_191246_...md" \\
        --event-slug revolution_travail_sahel_numerique_new_sustainability

    # Sans --event-slug : teste TOUS les événements custom du scénario
    # de l'article (utile pour voir si un événement auquel tu ne
    # pensais pas ressort aussi)
    python3 debug_test_evenement_central.py --article <chemin>
"""

import argparse
import os

from loader import parse_md_file, load_events_for_scenario, VAULT_PATH
from inject_custom_events import call_claude_json, get_client


def _llm_debug(client, article_body, candidats):
    """Même esprit que _llm_confirm_events() (detect_evenements_cites_
    retroactif.py) -- même consigne "sujet central, pas une simple
    référence" -- mais demande un verdict + justification PAR candidat
    plutôt qu'une liste de slugs confirmés, pour comprendre le
    raisonnement plutôt que juste le résultat."""
    events_txt = "\n".join(
        "- slug: {} | nom: {} | description: {}".format(
            ev["slug"], ev["name"], (ev.get("description") or "")[:200]
        )
        for ev in candidats
    )
    system = (
        "Tu analyses un article de fiction journalistique pour déterminer "
        "lesquels d'une liste d'événements en sont le SUJET CENTRAL -- "
        "l'article raconte, développe ou fait progresser cet événement "
        "lui-même, ce n'est pas juste une référence. REJETTE un événement "
        "s'il n'est utilisé que comme exemple, analogie, précédent "
        "historique cité en passant pour illustrer un autre sujet, ou "
        "simple toile de fond -- même si le nom et l'année sont cités "
        "explicitement, une citation de ce type ne compte PAS comme "
        "traitement central. Pour CHAQUE candidat, donne ton verdict ET "
        "une justification d'une phrase citant ce qui, dans le texte, "
        "motive ce verdict. Réponds UNIQUEMENT en JSON, sans aucun texte "
        "autour : {\"verdicts\": [{\"slug\": \"...\", \"confirme\": "
        "true/false, \"justification\": \"...\"}, ...]} -- un verdict par "
        "candidat, dans l'ordre fourni."
    )
    user = (
        "ARTICLE :\n{}\n\n"
        "ÉVÉNEMENTS CANDIDATS :\n{}\n\n"
        "Pour chacun, dis s'il est le SUJET CENTRAL de cet article (pas "
        "une simple mention, citation d'exemple ou analogie), et "
        "pourquoi.".format(article_body[:6000], events_txt)
    )
    result = call_claude_json(client, system, user, max_tokens=1000)
    return result.get("verdicts", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--article", required=True,
                         help="Chemin vers le fichier .md de l'article à tester.")
    parser.add_argument("--event-slug", default=None,
                         help="Slug d'un événement précis à tester (voir "
                              "registre_evenements.md). Si omis, teste TOUS "
                              "les événements custom du scénario de l'article.")
    args = parser.parse_args()

    article_path = args.article
    if not os.path.exists(article_path):
        # Lancé depuis generator/ (comme les autres scripts) : un chemin
        # relatif tel que "articles/{scenario}/xxx.md" ne se résout PAS
        # vers la racine du vault mais vers generator/articles/... --
        # repli sur VAULT_PATH avant d'abandonner.
        candidat = os.path.join(VAULT_PATH, args.article)
        if os.path.exists(candidat):
            article_path = candidat
        else:
            print("[erreur] Fichier introuvable, ni tel quel ni sous VAULT_PATH :")
            print("  - {}".format(args.article))
            print("  - {}".format(candidat))
            return

    parsed = parse_md_file(article_path)
    fm, body = parsed["frontmatter"], parsed["body"]
    scenario = fm.get("scenario")
    if not scenario:
        print("[erreur] Aucun champ 'scenario' dans le frontmatter de cet article.")
        return

    events = load_events_for_scenario(scenario)
    if args.event_slug:
        events = [e for e in events if e["slug"] == args.event_slug]
        if not events:
            print("[erreur] Slug {!r} introuvable parmi les événements custom "
                  "du scénario '{}'.".format(args.event_slug, scenario))
            return

    if not events:
        print("[info] Aucun événement custom trouvé pour le scénario '{}'.".format(scenario))
        return

    client = get_client()
    verdicts = _llm_debug(client, body, events)

    print("\n=== {} ===".format(article_path))
    print("Scénario : {}\n".format(scenario))
    if not verdicts:
        print("  [WARN] Aucun verdict retourné (échec de parsing JSON ?).")
        return

    valides = {ev["slug"] for ev in events}
    for v in verdicts:
        slug = v.get("slug", "?")
        if slug not in valides:
            # Trouvé en pratique le 5 septembre 2026 (article Mnemos,
            # test sans --event-slug sur les 12 candidats du scénario) :
            # le LLM peut inventer des slugs plausibles à partir des
            # éléments narratifs de l'article (ex. "panne_systemique_
            # mnemos_2098") au lieu de juger les candidats réellement
            # fournis -- surtout quand la liste de candidats est longue.
            # Signalé bruyamment plutôt qu'affiché comme un verdict
            # normal, pour ne jamais le rater silencieusement.
            print("  [SLUG INVENTÉ, ignoré] {} -- ne correspond à AUCUN "
                  "candidat réellement fourni".format(slug))
            print("      -> {}".format(v.get("justification", "")))
            continue
        badge = "CONFIRMÉ" if v.get("confirme") else "rejeté "
        print("  [{}] {}".format(badge, slug))
        print("      -> {}".format(v.get("justification", "(aucune justification fournie)")))

    manquants = valides - {v.get("slug") for v in verdicts}
    if manquants:
        print("\n  [WARN] Candidats fournis mais SANS verdict retourné "
              "(le LLM n'a pas répondu pour chacun, voir consigne "
              "'un verdict par candidat, dans l'ordre fourni') :")
        for s in sorted(manquants):
            print("    - {}".format(s))


if __name__ == "__main__":
    main()
