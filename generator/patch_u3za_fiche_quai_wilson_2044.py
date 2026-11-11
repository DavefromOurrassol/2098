#!/usr/bin/env python3
"""
patch_u3za_fiche_quai_wilson_2044.py — Ourrassol 2098 (U3za, 11 novembre 2026) — PONCTUEL
========================================================================================
Corrige event_instances/reamenagement_quai_wilson_2044_new_sustainability.md d'après l'article du
24 mars 2098, qui dit seulement : « …jusqu'au quai Wilson, réaménagé après la montée des eaux de 2044. »
L'IA avait inventé : APRC développée en « Autorité Planétaire pour la Régénération Climatique »
(dans l'article, l'APRC est l'organisme d'Amara Diallo-Svensson, lié à ARIA), files d'attente
devant le Centre Régénératif (scène de 2098 transposée en 2044), digues, zones humides, port,
glaciers, migrations.

Remplace en entier (en-tête YAML ET corps) : description, réalisation, conséquences.
Gardés : nom, date, localisation, impacts, acteurs, note de cohérence.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3za_fiche_quai_wilson_2044.py            # dry-run
  python3 generator/patch_u3za_fiche_quai_wilson_2044.py --apply    # applique (.bak_u3za)
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
FICHE = RACINE / "event_instances" / "reamenagement_quai_wilson_2044_new_sustainability.md"
TAG = "u3za"

DESC = ("En 2044, la montée des eaux touche Genève. Le quai Wilson est réaménagé à la suite de "
        "cette montée des eaux.")
REAL = ("En 2044, la montée des eaux atteint les rives genevoises du Léman et conduit au "
        "réaménagement du quai Wilson.")
CONS = ("Le réaménagement du quai Wilson inscrit dans la ville la trace de la montée des eaux de "
        "2044 : l'exposition des rives du Léman devient une contrainte durable de l'aménagement de Genève.")

# (clé YAML, titre de section du corps, nouveau texte)
CHAMPS = [
    ("description", "## Description journalistique", DESC),
    ("realisation", "## Réalisation dans [[new_sustainability]]", REAL),
    ("consequences", "## Conséquences", CONS),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not FICHE.is_file():
        sys.exit(f"✗ introuvable : {FICHE}")
    src = FICHE.read_text(encoding="utf-8")
    if "APRC" not in src and DESC in src:
        print("= déjà corrigée, rien à faire")
        return
    nouveau = src
    for cle, titre, texte in CHAMPS:
        motif_yaml = re.compile(rf"^{cle}: >\n  [^\n]*\n", re.MULTILINE)
        if len(motif_yaml.findall(nouveau)) != 1:
            sys.exit(f"✗ champ YAML « {cle} » introuvable ou multiple : rien modifié")
        nouveau = motif_yaml.sub(lambda m: f"{cle}: >\n  {texte}\n", nouveau)
        motif_corps = re.compile(rf"^{re.escape(titre)}\n[^\n]*\n", re.MULTILINE)
        if len(motif_corps.findall(nouveau)) != 1:
            sys.exit(f"✗ section « {titre} » introuvable ou multiple : rien modifié")
        nouveau = motif_corps.sub(lambda m: f"{titre}\n{texte}\n", nouveau)
        print(f"  {cle} : remplacé (en-tête et corps)")
    m = re.match(r"^---\n(.*?)\n---\n", nouveau, re.DOTALL)
    try:
        fm = yaml.safe_load(m.group(1)) if m else None
    except yaml.YAMLError as e:
        sys.exit(f"✗ l'en-tête ne serait plus du YAML valide : {e}")
    if not isinstance(fm, dict) or str(fm.get("description")).strip() != DESC or "APRC" in nouveau:
        sys.exit("✗ contrôle de l'en-tête échoué : rien modifié")
    if not args.apply:
        print("dry-run : rien écrit. Relancer avec --apply.")
        return
    bak = FICHE.with_name(FICHE.name + f".bak_{TAG}")
    shutil.copy2(FICHE, bak)
    FICHE.write_text(nouveau, encoding="utf-8")
    print(f"✓ appliqué ; sauvegarde {bak.name}. Lancer validate.py.")


if __name__ == "__main__":
    main()
