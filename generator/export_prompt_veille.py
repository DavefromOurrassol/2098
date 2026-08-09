#!/usr/bin/env python3
"""
export_prompt_veille.py — Ourrassol 2098
==========================================

Génère un prompt prêt à copier-coller dans n'importe quelle IA disposant
d'un accès web (Claude.ai, ChatGPT, etc.), pour mettre à jour UNIQUEMENT la
partie "photo du moment" (§ Situation actuelle et mouvements en cours) des
12 sections d'etat_du_monde_reel.md.

AUCUN APPEL API — script 100% local. Volontairement conçu ainsi (8 août
2026, demande de David) pour ne dépendre d'aucun fournisseur LLM
particulier : le choix du modèle utilisé pour la recherche web reste
entièrement entre les mains de David au moment du copier-coller, et rien ne
casse si un abonnement API venait à manquer.

Ce script ne modifie JAMAIS etat_du_monde_reel.md lui-même — voir le script
compagnon import_veille_etat_monde.py pour l'import du résultat.

PRINCIPE
--------
Le prompt généré injecte automatiquement :
  - le contenu actuel du paragraphe "Situation actuelle" de chacune des 12
    variables (pour que le LLM sache ce qui est déjà établi et n'ait pas à
    tout reformuler) ;
  - la date de dernière mise à jour de chaque section (peut différer d'une
    section à l'autre, si certaines n'ont pas bougé depuis plusieurs
    veilles) ;
  - une consigne explicite de SEUIL DE MATÉRIALITÉ (demande de David,
    8 août 2026) : le LLM ne doit marquer une section MODIFIÉ que si
    l'évolution est réellement significative, pas pour une simple
    reformulation ou un chiffre marginal qui bouge de quelques points. Une
    situation stable doit être signalée INCHANGÉ, pas réécrite pour le
    principe.

Ne touche JAMAIS aux sections "Perspective longue durée (~200 ans)" ni
"Trajectoire longue" — celles-ci ne sont ni lues en détail ni régénérées
ici (seuls leurs titres de section servent de repère de parsing).

USAGE
-----
    python3 export_prompt_veille.py
    python3 export_prompt_veille.py --dry-run   # affiche sans écrire

Le fichier produit est documentation/need_action/veille_prompt_a_copier.md
— à ouvrir, copier intégralement, coller dans l'IA de son choix avec accès
web, puis coller la RÉPONSE dans documentation/need_action/veille_reponse_
brute.md (via le panneau GUI de import_veille_etat_monde) avant de lancer
ce second script.

PRÉREQUIS
---------
    Aucun (pas de dépendance à llm_client.py — ce script ne fait aucun
    appel LLM). À placer dans le même dossier que les autres scripts du
    pipeline pour la cohérence VAULT_ROOT.
"""

import argparse
import re
from datetime import datetime
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Configuration (mêmes conventions que le reste du pipeline)
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
ETAT_MONDE_PATH = GENERATOR_DIR / "etat_du_monde_reel.md"
PROMPT_OUTPUT_PATH = NEED_ACTION_DIR / "veille_prompt_a_copier.md"
VARIABLES_DIR = VAULT_ROOT / "variables"

# Ordre et slugs identiques à VALID_VARS (loader.py) — ne pas réordonner
# sans mettre à jour aussi import_veille_etat_monde.py.
VARIABLES = [
    "systeme_economique_redistribution",
    "gouvernance_institutions",
    "geopolitique_conflits",
    "valeurs_culture_tempo_sociale",
    "organisation_territoires",
    "sante_biotechnologies",
    "frontieres_du_systeme",
    "technologie_information",
    "climat_environnement_global",
    "energie_ressources_critiques",
    "demographie_mobilite_humaine",
    "systemes_productifs_travail",
]

# datetime.strftime("%B") dépend de la locale système (souvent absente/non
# installée en environnement serveur) et produirait sinon un mois en
# anglais ("August") dans un fichier entièrement rédigé en français.
# Table codée en dur plutôt que de dépendre d'une locale disponible.
MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def format_date_fr(dt) -> str:
    return f"{dt.day:02d} {MOIS_FR[dt.month - 1]} {dt.year}"

# Repère le titre de sous-section "situation actuelle", sous ses deux formes
# possibles : l'ancienne ("Situation à l'été 2026 et mouvements en cours",
# écrite à la main le 7-8 août 2026) et la nouvelle, normalisée par
# import_veille_etat_monde.py à partir du premier import réel :
# "Situation actuelle (mise à jour : <date>) et mouvements en cours".
SITUATION_HEADING_RE = re.compile(
    r"\*\*Situation (?:à l'été \d{4}|actuelle \(mise à jour\s*:\s*(?P<date>[^)]+)\))"
    r" et mouvements en cours\*\*\s*:?",
    re.IGNORECASE,
)


def _section_bounds(content: str, slug: str):
    """
    Renvoie (start, end) du corps de la section '## slug' dans le fichier
    (texte entre ce titre et le prochain '## ' ou la fin du fichier).
    None si la section est introuvable (fichier non conforme).
    """
    m = re.search(rf"^##\s+{re.escape(slug)}\s*$", content, re.MULTILINE)
    if not m:
        return None
    start = m.end()
    next_m = re.search(r"^##\s+\S", content[start:], re.MULTILINE)
    end = start + next_m.start() if next_m else len(content)
    return start, end


def extract_situation(content: str, slug: str):
    """
    Extrait le paragraphe "Situation actuelle / à l'été ..." d'une section,
    ainsi que sa date de dernière mise à jour si connue (None si jamais
    passée par une veille — c'est-à-dire encore au format du 7-8 août 2026).

    Renvoie (paragraphe_texte, date_str_ou_None). Renvoie (None, None) si la
    section ou le sous-titre est introuvable.
    """
    bounds = _section_bounds(content, slug)
    if not bounds:
        return None, None
    start, end = bounds
    section_text = content[start:end]

    m = SITUATION_HEADING_RE.search(section_text)
    if not m:
        return None, None

    date_str = m.group("date")  # None si ancien format

    # Le paragraphe court du texte après le titre jusqu'au prochain "**...**"
    # de type sous-titre (heuristique : ligne commençant par ** en début de
    # paragraphe) ou jusqu'à la fin de la section.
    para_start = m.end()
    rest = section_text[para_start:]
    next_heading = re.search(r"\n\*\*[^*]+\*\*\s*(?:\(|:)", rest)
    para_end = next_heading.start() if next_heading else len(rest)
    paragraph = rest[:para_end].strip()

    return paragraph, date_str


def load_sub_variables(slug: str):
    """
    Lit les sous-variables officielles de la fiche variables/{slug}.md
    (frontmatter YAML, champ sub_variables), pour élargir explicitement le
    périmètre de recherche de la veille au-delà de ce que le paragraphe
    précédent couvrait par hasard.

    Constat de David (8 août 2026) : la première rédaction du 7-8 août ne
    couvrait, pour valeurs_culture_tempo_sociale, que le seul mouvement
    Gen Z (une des 5 sous-variables officielles : identites_culturelles) —
    rien sur systemes_de_valeurs (ex. montée du conservatisme),
    medias_et_recits_collectifs (ex. algorithmes et radicalisation en
    ligne, masculinisme), religion_et_spiritualite, ou rapport_au_temps_
    social. Sans ce garde-fou, chaque veille suivante n'aurait fait que
    prolonger le même angle déjà trop étroit, sans jamais être poussée à
    vérifier les autres dimensions prévues par la fiche elle-même.

    NOTE TECHNIQUE : le frontmatter complet n'est PAS du YAML standard —
    les blocs coupling_intensity (dans "states") utilisent des wikilinks
    Obsidian ([[slug]]) comme clés de mapping, ce que yaml.safe_load()
    refuse ("unhashable key"). loader.py a son propre parseur pour gérer
    ça ; ici, plus simple d'isoler uniquement le bloc "sub_variables:"
    (toujours bien formé, jamais de clé en wikilink) avant de le charger,
    plutôt que de parser tout le frontmatter.

    Renvoie une liste de (name, role) — [] si fiche introuvable, sans
    sous-variables, ou en cas d'erreur de parsing (résilient, n'interrompt
    jamais l'export global).
    """
    path = VARIABLES_DIR / f"{slug}.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")

    block_m = re.search(
        r"^sub_variables:\s*\n((?:[ \t]+.*\n?)+)", text, re.MULTILINE
    )
    if not block_m:
        return []

    try:
        parsed = yaml.safe_load("sub_variables:\n" + block_m.group(1))
    except yaml.YAMLError:
        return []

    raw = (parsed or {}).get("sub_variables") or []
    result = []
    for sv in raw:
        if isinstance(sv, dict) and sv.get("name"):
            result.append((sv["name"], sv.get("role", "")))
    return result


def format_sub_variables_block(sub_vars: list) -> str:
    if not sub_vars:
        return ""
    lines = ["Dimensions officielles de cette variable à vérifier "
             "explicitement (ne pas se limiter à ce qui était déjà couvert "
             "précédemment) :"]
    for name, role in sub_vars:
        label = name.replace("_", " ")
        if role:
            lines.append(f"  - {label} : {role}")
        else:
            lines.append(f"  - {label}")
    return "\n".join(lines)


def build_prompt(today_str: str, extracts: dict) -> str:
    lines = []
    lines.append(f"# PROMPT DE VEILLE — état du monde réel — {today_str}")
    lines.append("")
    lines.append(
        "Copie tout ce qui suit dans une IA avec accès web (Claude.ai, "
        "ChatGPT, etc.), colle sa réponse telle quelle dans "
        "documentation/need_action/veille_reponse_brute.md (panneau GUI de "
        "import_veille_etat_monde), puis lance import_veille_etat_monde.py."
    )
    lines.append("")
    lines.append("=" * 78)
    lines.append("")
    lines.append(
        "CONSIGNE DE LIVRAISON : produis ta réponse sous la forme d'un "
        "fichier markdown téléchargeable (ex. artifact/Canvas selon "
        "l'interface), nommé veille_reponse_brute.md, plutôt qu'un simple "
        "message de chat. S'il n'est pas possible de générer un fichier "
        "téléchargeable dans cette interface, réponds normalement en chat "
        "— le contenu sera copié à la main, le format ci-dessous reste "
        "identique dans les deux cas."
    )
    lines.append("")
    lines.append(
        "Tu es chargé de mettre à jour la partie \"photo du moment\" d'un "
        "fichier de référence factuelle sur l'état du monde réel, utilisé "
        "comme ancrage pour un projet de fiction spéculative se déroulant "
        "jusqu'en 2098. Voici l'état précédent de chaque section :"
    )
    lines.append("")

    for slug in VARIABLES:
        paragraph, date_str = extracts.get(slug, (None, None))
        lines.append(f"## {slug}")
        if date_str:
            lines.append(f"(dernière mise à jour : {date_str})")
        else:
            lines.append("(jamais mis à jour par une veille — contenu initial)")
        lines.append("")
        lines.append(paragraph if paragraph else "(section vide ou introuvable)")
        sub_vars = load_sub_variables(slug)
        sub_block = format_sub_variables_block(sub_vars)
        if sub_block:
            lines.append("")
            lines.append(sub_block)
        lines.append("")

    lines.append("-" * 78)
    lines.append("")
    lines.append(f"Date d'aujourd'hui à utiliser comme référence : {today_str}")
    lines.append("")
    lines.append(
        "Fais des recherches web pour vérifier et actualiser chacune des 12 "
        "sections ci-dessus à la date d'aujourd'hui. Pour CHAQUE section :"
    )
    lines.append("")
    lines.append(
        "- COUVERTURE COMPLÈTE (important) : chaque section liste ses "
        "dimensions officielles (voir 'Dimensions officielles... à "
        "vérifier' sous chaque paragraphe). Vérifie chacune, même celles "
        "absentes du paragraphe précédent — un paragraphe déjà écrit peut "
        "avoir ignoré certaines dimensions par le passé, ne te contente "
        "pas de prolonger le même angle."
    )
    lines.append(
        "- SEUIL DE MATÉRIALITÉ (important) : ne considère une section "
        "MODIFIÉE que si un fait significatif a réellement changé, s'est "
        "confirmé ou infirmé, ou si un nouveau mouvement de fond notable "
        "est apparu depuis la dernière mise à jour. Un chiffre qui bouge de "
        "quelques points, une reformulation, ou une actualité mineure sans "
        "portée structurelle ne justifient PAS une modification — dans ce "
        "cas, garde le paragraphe précédent tel quel et marque INCHANGÉ. "
        "Le but est de suivre les évolutions réelles, pas de réécrire pour "
        "le principe à chaque passage."
    )
    lines.append(
        "- Si le paragraphe est modifié : privilégie l'ajout/la précision "
        "de ce qui est nouveau plutôt qu'une réécriture complète. Reste "
        "factuel, neutre, 150-250 mots."
    )
    lines.append(
        "- N'ajoute AUCUNE mise en perspective historique (ni \"trajectoire "
        "~10-15 ans\", ni \"~200 ans\") — uniquement le constat présent, ces "
        "deux autres niveaux existent déjà ailleurs dans le fichier et ne "
        "sont pas à toucher."
    )
    lines.append(
        "- Termine chaque section par une ligne exactement égale à "
        "\"[MODIFIÉ]\" ou \"[INCHANGÉ]\" (rien d'autre sur cette ligne)."
    )
    lines.append("")
    lines.append(
        "IMPORTANT — question hors catégories : les 12 sections ci-dessus "
        "sont des cases prédéfinies, pensées pour suivre l'évolution de "
        "thèmes déjà connus. Un événement mondial vraiment inédit "
        "(rupture, découverte majeure, premier du genre) pourrait ne "
        "coller naturellement à aucune d'entre elles, ou être mal classé "
        "si on force son entrée dans l'une d'elles. Avant de conclure, "
        "demande-toi explicitement : y a-t-il eu, depuis la dernière mise "
        "à jour, un événement mondial majeur qui NE RENTRE PAS bien dans "
        "les 12 catégories ci-dessus ? Réponds dans une 13e section dédiée "
        "(voir format ci-dessous), même si la réponse est \"rien à "
        "signaler\" — ne force jamais un événement inédit dans une des 12 "
        "catégories seulement pour respecter le format."
    )
    lines.append("")
    lines.append(
        "Format de sortie STRICT (respecte exactement ces 12 en-têtes, dans "
        "cet ordre, rien avant le premier ni entre les sections) :"
    )
    lines.append("")
    for slug in VARIABLES:
        lines.append(f"## {slug}")
        lines.append("[paragraphe actualisé ou identique]")
        lines.append("[MODIFIÉ ou INCHANGÉ]")
        lines.append("")
    lines.append("## hors_categories")
    lines.append(
        "[description brève de tout événement majeur ne collant à aucune "
        "des 12 catégories, ou \"Rien à signaler.\" si aucun]"
    )
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Affiche le prompt dans le terminal sans écrire le fichier."
    )
    args = parser.parse_args()

    if not ETAT_MONDE_PATH.exists():
        print(f"[ERREUR] Fichier introuvable : {ETAT_MONDE_PATH}")
        return

    content = ETAT_MONDE_PATH.read_text(encoding="utf-8")
    today_str = format_date_fr(datetime.now())

    extracts = {}
    missing = []
    for slug in VARIABLES:
        paragraph, date_str = extract_situation(content, slug)
        extracts[slug] = (paragraph, date_str)
        if paragraph is None:
            missing.append(slug)

    if missing:
        print(
            "[AVERTISSEMENT] Section(s) introuvable(s) ou non conforme(s), "
            "à vérifier manuellement dans etat_du_monde_reel.md :"
        )
        for slug in missing:
            print(f"  - {slug}")

    prompt_text = build_prompt(today_str, extracts)

    if args.dry_run:
        print(prompt_text)
        print(f"\n[dry-run] {len(VARIABLES) - len(missing)}/{len(VARIABLES)} "
              f"sections extraites avec succès. Rien écrit sur disque.")
        return

    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_OUTPUT_PATH.write_text(prompt_text, encoding="utf-8")
    print(f"[OK] Prompt écrit dans {PROMPT_OUTPUT_PATH}")
    print(f"     {len(VARIABLES) - len(missing)}/{len(VARIABLES)} sections extraites.")
    print("     Prochaine étape : copier ce fichier dans une IA avec accès web,")
    print("     puis coller sa réponse dans veille_reponse_brute.md (panneau GUI)")
    print("     avant de lancer import_veille_etat_monde.py.")


if __name__ == "__main__":
    main()
