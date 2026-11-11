#!/usr/bin/env python3
"""
patch_u3z_fiche_accords_2039.py — Ourrassol 2098 (U3z, 11 novembre 2026) — PONCTUEL
==================================================================================
Corrige event_instances/accords_oms_regulation_mondiale_2039_new_sustainability.md d'après
l'article du 24 mars 2098, qui dit seulement : « Depuis les accords de 2039, qui ont transformé
l'OMS en une institution dotée de pouvoirs de régulation mondiale, Genève est le cœur battant
d'une révolution médicale sans précédent. »
  - description : le paragraphe recopié (dispensaire de 2042, unités mobiles d'« aujourd'hui »,
    protocoles du CPBE) est ramené à l'événement de 2039 ;
  - réalisation : retrait de la phrase sur les réseaux et les protocoles du CPBE (2098) ;
  - nom : « Accords de Genève sur la Régulation Médicale Mondiale » (nom inventé) ->
    « Accords de 2039 sur les pouvoirs de régulation mondiale de l'OMS » ;
  - date_label : « 2039 » (au lieu de « automne 2039 ») ; portée : globale (au lieu de locale).
Les conséquences, les impacts et les acteurs sont gardés. L'archétype
(evenements/accords_oms_regulation_mondiale_2039.md) garde son ancien nom d'affichage : à
retoucher à la main si besoin.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3z_fiche_accords_2039.py            # dry-run
  python3 generator/patch_u3z_fiche_accords_2039.py --apply    # applique (.bak_u3z)
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
FICHE = RACINE / "event_instances" / "accords_oms_regulation_mondiale_2039_new_sustainability.md"
TAG = "u3z"

NOM_ANCIEN = "Accords de Genève sur la Régulation Médicale Mondiale"
NOM_NOUVEAU = "Accords de 2039 sur les pouvoirs de régulation mondiale de l'OMS"

DESC_ANCIENNE = (
    "Depuis les accords de 2039, qui ont transformé l’OMS en une institution dotée de pouvoirs de "
    "régulation mondiale, Genève est le cœur battant d’une révolution médicale sans précédent. Les Réseaux "
    "de Médecine Régénérative Universelle y ont implanté leur premier dispensaire en 2042, dans le quartier "
    "des Grottes, alors en pleine gentrification post-inondation. Aujourd’hui, leurs unités mobiles "
    "sillonnent les zones périurbaines, proposant des thérapies géniques pour inverser la fibrose pulmonaire "
    "causée par les particules fines des décennies passées, ou des greffes de peau cultivée pour les "
    "travailleurs exposés aux UV résiduels. Grâce aux protocoles de reprogrammation épigénétique développés "
    "par le Consortium Panafricain des Biotechnologies pour l’Équité (CPBE), une personne de 80 ans peut "
    "retrouver la vitalité d’un quadragénaire.")
DESC_NOUVELLE = (
    "En 2039, des accords transforment l’OMS en une institution dotée de pouvoirs de régulation mondiale. "
    "Genève devient le cœur d’une révolution médicale sans précédent.")

REAL_ANCIENNE = (
    " Genève, déjà centre institutionnel majeur, devient le cœur d'une révolution médicale pilotée par des "
    "réseaux de médecine régénérative et des protocoles biotechnologiques ouverts, notamment ceux du "
    "Consortium Panafricain des Biotechnologies pour l'Équité (CPBE).")
REAL_NOUVELLE = " Genève, déjà centre institutionnel majeur, devient le cœur d'une révolution médicale."

# (nom, ancien, nouveau, occurrences attendues)
REMPLACEMENTS = [
    ("nom (en-tête)", f"name: {NOM_ANCIEN}\n", f"name: {NOM_NOUVEAU}\n", 1),
    ("nom (titre)", f"# {NOM_ANCIEN}\n", f"# {NOM_NOUVEAU}\n", 1),
    ("date_label", "date_label: automne 2039\n", "date_label: 2039\n", 1),
    ("portée", "portee: locale\n", "portee: globale\n", 1),
    ("description", DESC_ANCIENNE, DESC_NOUVELLE, 2),
    ("réalisation", REAL_ANCIENNE, REAL_NOUVELLE, 2),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not FICHE.is_file():
        sys.exit(f"✗ introuvable : {FICHE}")
    src = FICHE.read_text(encoding="utf-8")
    if NOM_NOUVEAU in src:
        print("= déjà corrigée, rien à faire")
        return
    nouveau = src
    for nom, ancien, rempl, attendu in REMPLACEMENTS:
        n = nouveau.count(ancien)
        if n != attendu:
            sys.exit(f"✗ « {nom} » : {n} occurrence(s) trouvée(s), {attendu} attendue(s) "
                     "(fiche déjà retouchée ?) : rien modifié")
        nouveau = nouveau.replace(ancien, rempl)
        print(f"  {nom} : {n} remplacement(s)")
    m = re.match(r"^---\n(.*?)\n---\n", nouveau, re.DOTALL)
    try:
        fm = yaml.safe_load(m.group(1)) if m else None
    except yaml.YAMLError as e:
        sys.exit(f"✗ l'en-tête ne serait plus du YAML valide : {e}")
    if (not isinstance(fm, dict) or fm.get("name") != NOM_NOUVEAU
            or str(fm.get("date_label")) != "2039" or fm.get("portee") != "globale"):
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
