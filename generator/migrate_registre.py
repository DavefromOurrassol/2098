#!/usr/bin/env python3
"""
migrate_registre.py — Ourrassol 2098
=====================================

Script de migration À LANCER UNE SEULE FOIS pour faire évoluer
registre_evenements.md de l'ancien format (5 colonnes, signaux
uniquement) vers le nouveau format hybride (6 colonnes), qui peut
aussi accueillir les événements custom (evenements/+event_instances/).

ANCIEN FORMAT (5 colonnes) :
| date_bascule | variable | signal | pilote | evenement_cle |

NOUVEAU FORMAT (6 colonnes) :
| type | date | source | variable(s) | pilote | evenement_cle |

Règle de lecture de la colonne "date" (IMPORTANT, documentée aussi en
en-tête du registre lui-même) :
  - type=signal    -> "date" contient une FENÊTRE "AAAA-AAAA"
                       (date_bascule du signal_to_state)
  - type=evenement -> "date" contient une ANNÉE UNIQUE "AAAA"
                       (date précise de l'instance d'événement)

Pour les lignes migrées (anciens signaux) :
  - type     = "signal"
  - date     = ancienne valeur de date_bascule (fenêtre, inchangée)
  - source   = ancien nom de "signal"
  - variable(s) = ancienne "variable" (un seul slug)
  - pilote   = inchangé
  - evenement_cle = inchangé

USAGE :
    python3 migrate_registre.py            # migre en place
    python3 migrate_registre.py --dry-run  # affiche le résultat sans écrire
"""

import argparse
import re
from pathlib import Path

REGISTRE_PATH = Path(__file__).resolve().parent / "registre_evenements.md"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

NEW_HEADER = """# Registre des événements (signal_to_state + événements custom)

Généré automatiquement — liste tous les `evenement_cle` (signaux) et
toutes les instances d'événements custom existants, par scénario,
triés chronologiquement, pour éviter les collisions de noms/dates/lieux
lors de l'ajout de nouveaux signaux (section 7 → 12) ou de nouveaux
événements custom (evenements/ + event_instances/).

RÈGLE DE LECTURE DE LA COLONNE "date" :
  - type=signal    -> fenêtre "AAAA-AAAA" (date_bascule du signal_to_state)
  - type=evenement -> année unique "AAAA" (date précise de l'instance)

Total : {total} entrées ({signaux} signaux uniques × 6 scénarios + {evenements} entrées d'événements custom).

"""


def parse_old_table(body):
    """Parse les lignes '| date_bascule | variable | signal | pilote | evenement_cle |'
    (ancien format 5 colonnes) d'une section de scénario."""
    rows = []
    table_started = False
    for line in body.split("\n"):
        if line.startswith("|---"):
            table_started = True
            continue
        if table_started and line.startswith("|"):
            cols = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cols)
        elif table_started and not line.startswith("|"):
            break
    return rows


def migrate(dry_run=False):
    if not REGISTRE_PATH.exists():
        print("Aucun registre trouvé à {} — rien à migrer.".format(REGISTRE_PATH))
        return

    old_text = REGISTRE_PATH.read_text(encoding="utf-8")

    if "| type | date | source |" in old_text:
        print("Le registre est déjà au nouveau format (6 colonnes). Rien à faire.")
        return

    parts = re.split(r"\n## (" + "|".join(SCENARIOS) + r")\n", old_text)
    output_sections = []
    total_rows = 0

    for i in range(1, len(parts), 2):
        scen = parts[i]
        body = parts[i + 1]
        old_rows = parse_old_table(body)

        new_rows = []
        for cols in old_rows:
            if len(cols) < 5:
                continue
            date_bascule, variable, signal, pilote, evenement_cle = cols[:5]
            new_rows.append([
                "signal", date_bascule, signal, variable, pilote, evenement_cle,
            ])

        new_rows.sort(key=lambda r: int(r[1].split("-")[0]) if r[1].split("-")[0].isdigit() else 9999)
        total_rows += len(new_rows)

        section_lines = [
            "## {}".format(scen),
            "",
            "| type | date | source | variable(s) | pilote | evenement_cle |",
            "|---|---|---|---|---|---|",
        ]
        for r in new_rows:
            section_lines.append("| " + " | ".join(r) + " |")
        section_lines.append("")
        output_sections.append("\n".join(section_lines))

    signaux_uniques = total_rows // len(SCENARIOS)
    new_content = NEW_HEADER.format(
        total=total_rows, signaux=signaux_uniques, evenements=0,
    ) + "\n".join(output_sections)

    if dry_run:
        print(new_content[:3000])
        print("\n[...]\n")
        print("Total nouvelles lignes : {}".format(total_rows))
        print("\n--dry-run : rien écrit sur disque.")
    else:
        backup_path = REGISTRE_PATH.with_suffix(".md.bak")
        backup_path.write_text(old_text, encoding="utf-8")
        REGISTRE_PATH.write_text(new_content, encoding="utf-8")
        print("Migration terminée.")
        print("Sauvegarde de l'ancien format : {}".format(backup_path))
        print("Total : {} entrées ({} signaux uniques × 6 scénarios)".format(
            total_rows, signaux_uniques))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)
