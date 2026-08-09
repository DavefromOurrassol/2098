#!/usr/bin/env python3
"""
import_veille_etat_monde.py — Ourrassol 2098
===============================================

Lit la réponse collée par David (après avoir utilisé le prompt généré par
export_prompt_veille.py dans une IA au choix, avec accès web), et applique
un patch CHIRURGICAL sur etat_du_monde_reel.md : uniquement le paragraphe
"Situation actuelle et mouvements en cours" des sections marquées MODIFIÉ.

AUCUN APPEL API — script 100% local, symétrique de export_prompt_veille.py.

Ne touche JAMAIS :
  - les sections marquées INCHANGÉ (le paragraphe ET sa date restent
    identiques — permet de savoir section par section depuis quand chaque
    "photo du monde" est à jour, plutôt qu'une seule date globale pour tout
    le fichier) ;
  - "Perspective longue durée (~200 ans)" ;
  - "Trajectoire longue" (~10-15 ans).

NORMALISATION DE L'EN-TÊTE (premier import réel uniquement)
-------------------------------------------------------------
Les 12 sections utilisaient jusqu'ici le titre fixe "Situation à l'été 2026
et mouvements en cours" (écrit à la main les 7-8 août 2026, jamais pensé
pour être réactualisé). À la première section réellement patchée, ce script
bascule ce titre vers un format daté et neutre côté saison :
"Situation actuelle (mise à jour : <date>) et mouvements en cours" — pour
que la prochaine veille (export_prompt_veille.py) puisse lire la date de
chaque section indépendamment, même si certaines n'ont jamais été
retouchées depuis.

USAGE
-----
    python3 import_veille_etat_monde.py --dry-run   # aperçu, rien écrit
    python3 import_veille_etat_monde.py              # écriture réelle

Lit documentation/need_action/veille_reponse_brute.md (à remplir via le
panneau GUI, "Éditer" -> coller -> "Sauvegarder", avant de lancer ce
script). Après un import réussi (hors dry-run), ce fichier est archivé
(horodaté, déplacé dans documentation/need_action/veille_archive/) pour
éviter une réimportation accidentelle du même contenu au run suivant.

PRÉREQUIS
---------
    Aucun (pas de dépendance à llm_client.py). À placer dans le même
    dossier que export_prompt_veille.py.
"""

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = Path(__file__).resolve().parent
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
ETAT_MONDE_PATH = GENERATOR_DIR / "etat_du_monde_reel.md"
RAW_RESPONSE_PATH = NEED_ACTION_DIR / "veille_reponse_brute.md"
ARCHIVE_DIR = NEED_ACTION_DIR / "veille_archive"
DIFF_REPORT_PATH = NEED_ACTION_DIR / "veille_etat_monde_diff.md"

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

# Même choix que export_prompt_veille.py : table codée en dur plutôt que de
# dépendre de la locale système, pour garantir un mois en français.
MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def format_date_fr(dt) -> str:
    return f"{dt.day:02d} {MOIS_FR[dt.month - 1]} {dt.year}"

SITUATION_HEADING_RE = re.compile(
    r"\*\*Situation (?:à l'été \d{4}|actuelle \(mise à jour\s*:\s*[^)]+\))"
    r" et mouvements en cours\*\*\s*:?",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Parsing de la réponse brute collée par David
# ---------------------------------------------------------------------------

def parse_raw_response(text: str) -> dict:
    """
    Découpe la réponse en blocs '## slug' -> (paragraphe, statut).
    statut vaut "MODIFIÉ", "INCHANGÉ", ou None si la ligne de statut est
    absente/mal formée (section ignorée avec avertissement, jamais bloquant
    pour les autres — même philosophie de résilience que le reste du
    pipeline).

    Le bloc spécial '## hors_categories' (voir export_prompt_veille.py) est
    traité à part par extract_hors_categories() — il n'est jamais patché
    dans une section du fichier puisqu'il n'a par définition aucun slug de
    variable associé.
    """
    results = {}
    parts = re.split(r"^##\s+(\S+)\s*$", text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        slug = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        if slug not in VARIABLES:
            continue

        status_m = re.search(r"\[(MODIFIÉ|INCHANGÉ|MODIFIE|INCHANGE)\]", body, re.IGNORECASE)
        status = None
        if status_m:
            raw = status_m.group(1).upper()
            status = "MODIFIÉ" if raw.startswith("MODIFI") else "INCHANGÉ"
            paragraph = body[:status_m.start()].strip()
        else:
            paragraph = body.strip()

        results[slug] = (paragraph, status)

    return results


NEANT_PATTERNS = (
    "rien à signaler", "rien a signaler", "néant", "neant",
    "aucun événement", "aucun evenement", "rien de notable",
)


def extract_hors_categories(text: str):
    """
    Extrait le contenu de la section '## hors_categories', si présente.
    Renvoie None si absente, "" si présente mais vide/négative ("rien à
    signaler" et variantes), ou le texte signalé sinon.

    Le test de négation ("rien à signaler") ne doit matcher QUE quand tout
    le contenu se résume à ça, sinon un vrai texte d'alerte contenant par
    hasard un mot comme "aucune confirmation officielle" (ex. sur un fait
    non vérifié mais bien réel) serait effacé à tort. D'où la limite de
    longueur en plus du test de motif — un bug trouvé en testant le
    scénario "artefact extraterrestre" (8 août 2026, David).
    """
    m = re.search(r"^##\s+hors_categories\s*$", text, re.MULTILINE)
    if not m:
        return None
    rest = text[m.end():]
    next_heading = re.search(r"^##\s+\S", rest, re.MULTILINE)
    content = (rest[:next_heading.start()] if next_heading else rest).strip()
    if not content:
        return ""
    content_lower = content.lower()
    est_negation = len(content) < 60 and any(p in content_lower for p in NEANT_PATTERNS)
    if est_negation:
        return ""
    return content


# ---------------------------------------------------------------------------
# Patch chirurgical d'etat_du_monde_reel.md
# ---------------------------------------------------------------------------

def _section_bounds(content: str, slug: str):
    m = re.search(rf"^##\s+{re.escape(slug)}\s*$", content, re.MULTILINE)
    if not m:
        return None
    start = m.end()
    next_m = re.search(r"^##\s+\S", content[start:], re.MULTILINE)
    end = start + next_m.start() if next_m else len(content)
    return start, end


def patch_section(content: str, slug: str, new_paragraph: str, today_str: str):
    """
    Remplace le titre + le paragraphe "Situation ..." d'une section par la
    version normalisée et datée. Ne touche à rien d'autre dans la section
    (Perspective longue durée / Trajectoire longue restent identiques au
    caractère près). Renvoie le contenu patché, ou None si la section/le
    sous-titre est introuvable (échec silencieux signalé à l'appelant).
    """
    bounds = _section_bounds(content, slug)
    if not bounds:
        return None
    start, end = bounds
    section_text = content[start:end]

    m = SITUATION_HEADING_RE.search(section_text)
    if not m:
        return None

    para_start = m.end()
    rest = section_text[para_start:]
    next_heading = re.search(r"\n\*\*[^*]+\*\*\s*(?:\(|:)", rest)
    para_end = next_heading.start() if next_heading else len(rest)

    new_heading = f"**Situation actuelle (mise à jour : {today_str}) et mouvements en cours** :"
    new_section_text = (
        section_text[:m.start()]
        + new_heading
        + "\n\n" + new_paragraph.strip() + "\n"
        + rest[para_end:]
    )

    return content[:start] + new_section_text + content[end:]


# ---------------------------------------------------------------------------
# Historique des révisions (en-tête du fichier)
# ---------------------------------------------------------------------------

def append_revision_entry(content: str, today_str: str, modifiees: list, inchangees: list) -> str:
    entry = (
        f"- {today_str} (veille) : "
        f"{len(modifiees)} section(s) mise(s) à jour"
        + (f" ({', '.join(modifiees)})" if modifiees else "")
        + f", {len(inchangees)} inchangée(s)."
    )
    marker = "**Historique des révisions**"
    idx = content.find(marker)
    if idx == -1:
        return content  # pas de marqueur trouvé, on ne casse rien
    line_end = content.find("\n", idx)
    return content[:line_end + 1] + entry + "\n" + content[line_end + 1:]


def check_freshness(path: Path, today: datetime) -> tuple:
    """
    Compare la date de dernière modification de la réponse collée à la date
    du jour. Ne bloque jamais silencieusement une réponse périmée qu'on
    aurait oubliée dans le fichier depuis une veille précédente.

    Renvoie (est_frais: bool, date_modif_str: str).
    """
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    est_frais = mtime.date() == today.date()
    return est_frais, format_date_fr(mtime)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                         help="Affiche ce qui serait modifié, sans rien écrire.")
    parser.add_argument(
        "--force", action="store_true",
        help="Importe quand même si veille_reponse_brute.md n'a pas été "
             "modifié aujourd'hui (sinon le script s'arrête par sécurité)."
    )
    args = parser.parse_args()

    if not RAW_RESPONSE_PATH.exists():
        print(f"[ERREUR] {RAW_RESPONSE_PATH} introuvable — "
              "colle d'abord la réponse de la veille via le panneau GUI.")
        return
    if not ETAT_MONDE_PATH.exists():
        print(f"[ERREUR] {ETAT_MONDE_PATH} introuvable.")
        return

    now = datetime.now()
    est_frais, date_modif = check_freshness(RAW_RESPONSE_PATH, now)
    if not est_frais and not args.force:
        print(
            f"[ARRÊT] veille_reponse_brute.md a été modifié pour la dernière "
            f"fois le {date_modif}, pas aujourd'hui ({format_date_fr(now)}).\n"
            f"         C'est peut-être une réponse oubliée d'une veille "
            f"précédente plutôt que celle d'aujourd'hui.\n"
            f"         Si c'est bien volontaire, relance avec --force."
        )
        return
    if not est_frais and args.force:
        print(
            f"[AVERTISSEMENT] --force actif : import d'une réponse datée du "
            f"{date_modif} (pas aujourd'hui) malgré l'incohérence de date."
        )

    raw_text = RAW_RESPONSE_PATH.read_text(encoding="utf-8")
    parsed = parse_raw_response(raw_text)
    hors_categories = extract_hors_categories(raw_text)

    missing = [s for s in VARIABLES if s not in parsed]
    unparsed_status = [s for s, (_, st) in parsed.items() if st is None]
    if missing:
        print("[AVERTISSEMENT] Section(s) absente(s) de la réponse collée :")
        for s in missing:
            print(f"  - {s}")
    if unparsed_status:
        print("[AVERTISSEMENT] Statut [MODIFIÉ]/[INCHANGÉ] illisible, section ignorée :")
        for s in unparsed_status:
            print(f"  - {s}")

    today_str = format_date_fr(now)
    content = ETAT_MONDE_PATH.read_text(encoding="utf-8")

    modifiees, inchangees, echecs = [], [], []
    diff_lines = [f"# Diff veille état du monde — {today_str}", ""]

    for slug in VARIABLES:
        if slug not in parsed:
            continue
        paragraph, status = parsed[slug]
        if status is None:
            continue
        if status == "INCHANGÉ":
            inchangees.append(slug)
            continue

        # status == "MODIFIÉ"
        old_paragraph, _ = None, None
        bounds = _section_bounds(content, slug)
        if bounds:
            old_section = content[bounds[0]:bounds[1]]
            m = SITUATION_HEADING_RE.search(old_section)
            if m:
                old_paragraph = old_section[m.end():].strip().split("\n\n")[0]

        new_content = patch_section(content, slug, paragraph, today_str)
        if new_content is None:
            echecs.append(slug)
            continue

        diff_lines.append(f"## {slug}")
        diff_lines.append("**Avant :**")
        diff_lines.append(old_paragraph or "(introuvable)")
        diff_lines.append("")
        diff_lines.append("**Après :**")
        diff_lines.append(paragraph.strip())
        diff_lines.append("")

        content = new_content
        modifiees.append(slug)

    if echecs:
        print("[AVERTISSEMENT] Section(s) non patchée(s) — sous-titre "
              "'Situation ...' introuvable dans etat_du_monde_reel.md, "
              "à vérifier manuellement :")
        for s in echecs:
            print(f"  - {s}")

    if modifiees:
        content = append_revision_entry(content, today_str, modifiees, inchangees)

    print(f"\n[BILAN] {len(modifiees)} section(s) modifiée(s), "
          f"{len(inchangees)} inchangée(s), {len(echecs)} échec(s) de patch.")

    if hors_categories is None:
        print(
            "[AVERTISSEMENT] Section '## hors_categories' absente de la "
            "réponse — le prompt utilisé date peut-être d'avant son "
            "ajout, ou l'IA n'a pas respecté le format."
        )
    elif hors_categories:
        print(
            "\n" + "!" * 78 +
            "\n[ALERTE HORS CATÉGORIES] L'IA a signalé un événement qui ne "
            "rentre dans aucune des 12 variables suivies :\n\n"
            + hors_categories +
            "\n\nCe contenu n'est PAS auto-intégré au fichier (aucun slug "
            "de variable associé) — à examiner manuellement pour décider "
            "s'il justifie une nouvelle variable, une entité, ou une "
            "simple note.\n" + "!" * 78
        )
        diff_lines.append("## ⚠️ hors_categories (non intégré, à examiner manuellement)")
        diff_lines.append(hors_categories)
        diff_lines.append("")

    if args.dry_run:
        print("[dry-run] Rien écrit sur disque.")
        if modifiees or hors_categories:
            print("\n--- Aperçu du rapport diff ---\n")
            print("\n".join(diff_lines))
        return

    if not modifiees and not hors_categories:
        print("[OK] Aucune section modifiée, rien à signaler hors "
              "catégories — fichier laissé intact, rien à archiver.")
        return

    if modifiees:
        ETAT_MONDE_PATH.write_text(content, encoding="utf-8")
    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    DIFF_REPORT_PATH.write_text("\n".join(diff_lines), encoding="utf-8")

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_path = ARCHIVE_DIR / f"veille_reponse_brute_{timestamp}.md"
    shutil.move(str(RAW_RESPONSE_PATH), str(archived_path))

    if modifiees:
        print(f"[OK] {ETAT_MONDE_PATH} mis à jour.")
    else:
        print(f"[OK] {ETAT_MONDE_PATH} inchangé (aucune section modifiée), "
              f"mais alerte hors catégories consignée.")
    print(f"[OK] Rapport diff écrit dans {DIFF_REPORT_PATH}")
    print(f"[OK] Réponse brute archivée dans {archived_path}")


if __name__ == "__main__":
    main()
