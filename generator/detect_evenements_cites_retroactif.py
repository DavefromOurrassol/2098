#!/usr/bin/env python3
"""
detect_evenements_cites_retroactif.py — Ourrassol 2098
=======================================================

Rattrapage rétroactif du champ `evenements_cites` sur les articles déjà
publiés — chantier "suite narrative des événements" (5 septembre 2026).
Le prospectif (nouveaux articles) est câblé directement dans
api.py::build_article_md() (mode Forcer uniquement, lien garanti par
forcer_resolu) — ce script couvre le passé, où ce lien n'a jamais
existé.

PRINCIPE (deux passages, cf. décision actée avec David)
--------------------------------------------------------
1. Passage textuel (gratuit, aucun appel LLM) : pour chaque article
   d'un scénario, repère des CANDIDATS -- soit le nom exact de
   l'événement dans le corps ("certain" au sens textuel), soit un
   acteur de l'événement ET son année, tous deux présents ("probable").
   Ni l'un ni l'autre n'est appliqué directement : un nom exact peut
   n'être qu'un exemple parmi d'autres dans un article qui traite d'un
   tout autre sujet (trouvé le 5 septembre 2026 sur un article
   Brigades de Restauration Écologique citant "la Grande Inondation
   des Veilleurs" du Congo comme un exemple parmi cinq -- pas le sujet
   de l'article). Le texte ne fait donc plus que PROPOSER des
   candidats, jamais confirmer à lui seul.
2. Passage LLM ciblé (--llm-pass), sur TOUS les articles ayant au moins
   un candidat (certain ou probable) -- demande au LLM de confirmer,
   pour CET article précis, lequel ou lesquels des candidats sont le
   SUJET CENTRAL du texte (pas une simple mention, citation d'exemple
   ou analogie -- consigne resserrée le 5 septembre 2026, voir
   _llm_confirm_events). Aucun scan LLM systématique article ×
   événement sur l'ensemble du vault (coût non justifié) -- seulement
   sur les articles ayant déjà au moins un candidat textuel.

Ne modifie JAMAIS un evenements_cites déjà présent et non vide sur un
article (respecte le prospectif déjà écrit par api.py, ou un rattrapage
déjà passé). Rien n'est écrit sur disque sans --apply.

PRÉREQUIS
---------
    Même environnement que inject_custom_events.py (llm_client
    configuré) -- uniquement nécessaire si --llm-pass est utilisé.

USAGE
-----
    python3 detect_evenements_cites_retroactif.py
        # rapport seul, tous scénarios, passage textuel uniquement

    python3 detect_evenements_cites_retroactif.py --scenario policy_reform

    python3 detect_evenements_cites_retroactif.py --llm-pass
        # ajoute la confirmation LLM sur les cas ambigus, toujours rapport seul

    python3 detect_evenements_cites_retroactif.py --llm-pass --apply
        # écrit evenements_cites dans le frontmatter des articles concernés
"""

import argparse
import os
import re

from loader import parse_md_file, load_events_for_scenario, VALID_SCENARIOS, VAULT_PATH

# Réutilisés tels quels (mêmes conventions que le mode custom
# d'inject_custom_events.py : get_client() ne fait plus qu'une chose,
# retourner None -- call_claude_json n'en a plus besoin ; conservé pour
# compatibilité de signature) -- évite de dupliquer la logique
# d'extraction JSON robuste (fences, raw_decode, repli regex) déjà
# écrite et testée là-bas.
from inject_custom_events import call_claude_json, get_client

ARTICLES_DIR = os.path.join(VAULT_PATH, "articles")

# ---------------------------------------------------------------------------
# Détection textuelle
# ---------------------------------------------------------------------------


def _match_events_textuel(body_lower, events, entites_citees_article=None):
    """Retourne {"certain": [...], "probable": [...]} pour un article
    donné.

    "certain" : le NOM exact de l'événement apparaît dans le corps --
    reste rare en pratique (le champ `name` est souvent un intitulé
    formel, pas la façon dont un article en parle), mais fiable quand
    il déclenche.

    "probable" : testé sur données réelles le 5 septembre 2026, à deux
    reprises -- le vocabulaire seul ET l'acteur seul se sont tous deux
    révélés bien trop bruyants pris isolément (65 puis 69 articles sur
    74 signalés sur new_sustainability). Cause commune aux deux : ce
    monde ne recycle qu'un petit pool d'acteurs canoniques et de
    vocabulaire thématique -- un acteur de l'événement (ex. le
    Consortium Amazônia Viva) apparaît dans entites_citees de presque
    TOUS les articles du scénario, pas seulement ceux qui traitent
    vraiment de cet événement précis. Un seul signal, pris seul, ne
    prouve donc rien ici.
    Corrigé : les DEUX signaux sont désormais exigés ENSEMBLE
    (intersection, pas union) -- un acteur ET l'année exacte de
    l'événement, tous deux présents. La coïncidence des deux à la fois
    est bien moins probable qu'un seul pris isolément.
    """
    entites_citees_set = set(entites_citees_article or [])
    certain, probable = [], []
    for ev in events:
        name = (ev.get("name") or "").strip().lower()
        if name and name in body_lower:
            certain.append(ev["slug"])
            continue

        acteur_overlap = bool(entites_citees_set & set(ev.get("acteurs") or []))

        annee = ev.get("date")
        annee_trouvee = bool(
            annee and re.search(r"\b{}\b".format(re.escape(str(annee))), body_lower)
        )

        if acteur_overlap and annee_trouvee:
            probable.append(ev["slug"])
    return {"certain": certain, "probable": probable}


# ---------------------------------------------------------------------------
# Confirmation LLM (cas ambigus uniquement)
# ---------------------------------------------------------------------------

def _llm_confirm_events(client, article_body, candidats):
    """Un seul appel LLM par article ambigu : fournit le texte + la liste
    des événements candidats (nom + description courte), demande
    lesquels sont le SUJET CENTRAL de l'article -- pas une simple
    mention, citation d'exemple ou analogie en passant. Retourne la
    liste des slugs confirmés (sous-ensemble de candidats), [] en cas
    d'échec de parsing (jamais de faux positif ajouté par défaut en cas
    d'erreur).

    Consigne resserrée le 5 septembre 2026 (décision actée avec David,
    après vérification manuelle de 2 échantillons confirmés) : une
    version antérieure acceptait "mentionné comme sujet ou fait
    significatif", ce qui a laissé passer un cas où l'événement n'était
    cité qu'en exemple/analogie pour argumenter sur un tout autre sujet
    (le Traité de Belém convoqué dans un article sur la santé
    algorithmique à Genève -- citation réelle, mais pas développée).
    Resserré pour aligner le rattrapage rétroactif sur ce que le mode
    Forcer garantit déjà prospectivement (forced_angle_directive impose
    toujours "sujet_central", jamais une mention secondaire) -- cohérence
    entre les deux sources du champ, utile pour le futur `developpements`
    (point C) : une citation en passant ne fait pas avancer le récit de
    l'événement, elle ne doit donc pas compter ici."""
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
        "traitement central. Réponds UNIQUEMENT en JSON, sans aucun texte "
        "autour : {\"slugs_confirmes\": [\"slug1\", \"slug2\"]} -- liste "
        "vide si aucun des candidats n'est réellement le sujet central de "
        "l'article."
    )
    user = (
        "ARTICLE :\n{}\n\n"
        "ÉVÉNEMENTS CANDIDATS (détectés par une recherche textuelle "
        "approximative, à confirmer ou infirmer) :\n{}\n\n"
        "Lequel ou lesquels de ces événements sont le SUJET CENTRAL de "
        "cet article (pas une simple mention, citation d'exemple ou "
        "analogie) ?".format(article_body[:6000], events_txt)
    )
    try:
        result = call_claude_json(client, system, user, max_tokens=500)
        slugs = result.get("slugs_confirmes", []) or []
        valides = {ev["slug"] for ev in candidats}
        return [s for s in slugs if s in valides]
    except Exception as e:
        print("  [WARN] Échec confirmation LLM : {}".format(e))
        return []


# ---------------------------------------------------------------------------
# Écriture frontmatter (édition ciblée, pas de re-sérialisation YAML complète)
# ---------------------------------------------------------------------------

def _write_evenements_cites(filepath, raw_content, slugs, source):
    """Insère/remplace le champ evenements_cites (+ evenements_cites_source)
    dans le frontmatter YAML brut du fichier, par édition de texte ciblée
    plutôt que réécriture complète (préserve le formatage existant du
    reste du frontmatter). N'écrase jamais un evenements_cites déjà
    rempli (défense en profondeur -- run() filtre déjà ce cas en amont
    via le frontmatter parsé, mais une double protection au niveau texte
    brut coûte peu et évite un écrasement accidentel si run() est un
    jour appelé autrement)."""
    fm_match = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)$", raw_content, re.DOTALL)
    if not fm_match:
        return False, "frontmatter introuvable"

    fm_str = fm_match.group(2)

    existing_filled = re.search(
        r"^evenements_cites:\s*\n(?:\s+-\s*\S.*\n?)+", fm_str, re.MULTILINE
    )
    if existing_filled:
        return False, "evenements_cites déjà rempli"

    new_block_lines = ["evenements_cites:"]
    for s in slugs:
        new_block_lines.append("  - {}".format(s))
    new_block_lines.append("evenements_cites_source: {}".format(source))
    new_block = "\n".join(new_block_lines)

    if re.search(r"^evenements_cites:\s*$", fm_str, re.MULTILINE):
        # Champ présent mais vide (écrit par api.py, aucun forçage sur
        # cet article) -- remplacé par le bloc complet.
        fm_str_new = re.sub(
            r"^evenements_cites:\s*$", new_block, fm_str, count=1, flags=re.MULTILINE
        )
    elif re.search(r"^variables_pilotes:", fm_str, re.MULTILINE):
        # Champ absent (article généré avant ce chantier) -- inséré
        # juste avant variables_pilotes, même position que dans les
        # nouveaux articles (api.py).
        fm_str_new = re.sub(
            r"^variables_pilotes:", new_block + "\nvariables_pilotes:",
            fm_str, count=1, flags=re.MULTILINE
        )
    else:
        fm_str_new = fm_str.rstrip("\n") + "\n" + new_block

    new_content = fm_match.group(1) + fm_str_new + fm_match.group(3) + fm_match.group(4)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True, "ok"


# ---------------------------------------------------------------------------
# Parcours des articles
# ---------------------------------------------------------------------------

def _find_article_files(scenario_filter=None):
    """Liste tous les articles générés, récursivement -- même convention
    que les autres scripts d'audit (articles/{scenario}/*.md, rangement
    en sous-dossier depuis le 22 août 2026)."""
    if not os.path.exists(ARTICLES_DIR):
        return []
    files = []
    for root, _dirs, fnames in os.walk(ARTICLES_DIR):
        if scenario_filter and os.path.basename(root) != scenario_filter:
            # Ne descend pas dans un sous-dossier d'un autre scénario --
            # ne bloque pas la racine articles/ elle-même (root peut être
            # ARTICLES_DIR lui-même si d'anciens fichiers traînent hors
            # sous-dossier, cas legacy pré-22-août).
            if root != ARTICLES_DIR:
                continue
        for fname in fnames:
            if not fname.endswith(".md") or fname.startswith("_") or fname.startswith("."):
                continue
            files.append(os.path.join(root, fname))
    return files


def run(scenario_filter=None, llm_pass=False, apply=False, dry_run=False):
    client = get_client() if llm_pass else None
    ecrire = apply and not dry_run

    scenarios = [scenario_filter] if scenario_filter else VALID_SCENARIOS
    compteurs = {
        "deja_rempli": 0, "llm_confirme": 0,
        "llm_rejete": 0, "aucun": 0, "ambigu_sans_llm_pass": 0,
    }

    for scenario_slug in scenarios:
        events = load_events_for_scenario(scenario_slug)
        if not events:
            continue

        articles = _find_article_files(scenario_slug)
        print("\n{} — {} événements custom, {} articles".format(
            scenario_slug, len(events), len(articles)))

        for filepath in articles:
            parsed = parse_md_file(filepath)
            fm, body = parsed["frontmatter"], parsed["body"]

            if fm.get("evenements_cites"):
                compteurs["deja_rempli"] += 1
                continue

            body_lower = body.lower()
            entites_citees_article = fm.get("entites_citees") or []
            matches = _match_events_textuel(body_lower, events, entites_citees_article)
            # "certain" (nom exact) ne suffit plus à écrire directement --
            # trouvé le 5 septembre 2026 (article Brigades/Congo) : un nom
            # exact peut n'être qu'un exemple parmi d'autres dans un
            # article qui traite d'autre chose. Les deux catégories
            # passent désormais par la MÊME vérification LLM "sujet
            # central" -- le texte ne fait plus que proposer des
            # candidats, jamais confirmer à lui seul.
            candidats_slugs = sorted(set(matches["certain"] + matches["probable"]))

            if not candidats_slugs:
                compteurs["aucun"] += 1
                continue

            if not llm_pass:
                compteurs["ambigu_sans_llm_pass"] += 1
                print("  [CANDIDATS, non vérifiés sans --llm-pass] {} -> {}".format(
                    os.path.basename(filepath), candidats_slugs))
                continue

            candidats = [ev for ev in events if ev["slug"] in candidats_slugs]
            confirmes = _llm_confirm_events(client, body, candidats)
            if not confirmes:
                compteurs["llm_rejete"] += 1
                continue

            compteurs["llm_confirme"] += 1
            source = "retroactif_llm"
            print("  {} -> {} [{}]".format(
                os.path.basename(filepath), confirmes, source))

            if ecrire:
                ok, msg = _write_evenements_cites(filepath, parsed["raw"], confirmes, source)
                if not ok:
                    print("    [skip] {}".format(msg))

    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print("  Déjà rempli (ignoré)             : {}".format(compteurs["deja_rempli"]))
    print("  Confirmé par LLM (sujet central) : {}".format(compteurs["llm_confirme"]))
    print("  Rejeté par LLM                   : {}".format(compteurs["llm_rejete"]))
    print("  Candidats, non vérifiés (--llm-pass absent) : {}".format(compteurs["ambigu_sans_llm_pass"]))
    print("  Aucun candidat textuel            : {}".format(compteurs["aucun"]))
    if not ecrire:
        print("\n  (mode rapport seul -- relancer avec --apply, sans --dry-run, "
              "pour écrire sur disque)")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=VALID_SCENARIOS, default=None,
                         help="Limiter à un scénario (défaut : tous).")
    parser.add_argument("--llm-pass", action="store_true",
                         help="Active la confirmation LLM 'sujet central' sur tout "
                              "article ayant au moins un candidat textuel (nom exact "
                              "ou acteur+année) -- aucun candidat n'est jamais écrit "
                              "sans cette confirmation. Sans ce flag, ces articles "
                              "sont listés mais jamais tranchés.")
    parser.add_argument("--apply", action="store_true",
                         help="Écrit evenements_cites (+ evenements_cites_source) dans "
                              "le frontmatter des articles concernés. Sans ce flag : "
                              "rapport seul, rien n'est écrit sur disque.")
    parser.add_argument("--dry-run", action="store_true",
                         help="Force le mode rapport même si --apply est présent -- "
                              "pour tester la détection (y compris le passage LLM) "
                              "sans risque d'écriture.")
    args = parser.parse_args()

    run(scenario_filter=args.scenario, llm_pass=args.llm_pass,
        apply=args.apply, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
