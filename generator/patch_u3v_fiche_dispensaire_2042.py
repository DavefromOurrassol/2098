#!/usr/bin/env python3
"""
patch_u3v_fiche_dispensaire_2042.py — Ourrassol 2098 (U3v, 11 novembre 2026) — PONCTUEL
======================================================================================
Corrige la fiche event_instances/ouverture_dispensaire_regeneratif_geneve_2042_new_sustainability.md
d'après l'article du 24 mars 2098 : l'article dit seulement que les Réseaux de Médecine Régénérative
Universelle ont implanté leur premier dispensaire en 2042, dans le quartier des Grottes, alors en
pleine gentrification post-inondation. Tout le reste (12 octobre, pluie, bâtiment, déclaration du
Dr Voss, patients, unité mobile, financement, mortalité -12 %, Hub Nairobi-Kigali) était inventé.

  - description et réalisation : ramenées aux faits de l'article ;
  - conséquences : sobres, sans chiffre ni acteur inventé ;
  - date_label : « 2042 » (au lieu de « automne 2042 », alors que date vaut 2042.01) ;
  - acteurs : OMS Étendue retiré (aucun lien établi avec le dispensaire dans l'article).
Textes remplacés dans l'en-tête YAML ET dans le corps ; chaque ancre doit être trouvée le nombre
de fois attendu, et l'en-tête doit rester du YAML valide.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3v_fiche_dispensaire_2042.py            # dry-run
  python3 generator/patch_u3v_fiche_dispensaire_2042.py --apply    # applique (.bak_u3v)
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
FICHE = RACINE / "event_instances" / "ouverture_dispensaire_regeneratif_geneve_2042_new_sustainability.md"
TAG = "u3v"

DESC_ANCIENNE = (
    "Ce 12 octobre 2042, sous une pluie fine typique de l'automne genevois, le quartier des Grottes a vu "
    "s'ouvrir les portes d'un bâtiment aux lignes épurées, intégrant des jardins verticaux et des panneaux "
    "solaires transparents. Le Dr. Elias Voss, directeur du Centre Régénératif du Léman, a déclaré : "
    "« Aujourd'hui, nous réparons les corps comme nous régénérons la planète. » Les premiers patients, des "
    "travailleurs exposés aux UV résiduels et des habitants souffrant de fibrose pulmonaire, ont reçu des "
    "greffes de peau cultivée et des protocoles de reprogrammation épigénétique, développés en collaboration "
    "avec le CPBE. Une unité mobile, déjà en circulation dans les zones périurbaines, étendra ces soins "
    "dès 2043.")
DESC_NOUVELLE = (
    "En 2042, les Réseaux de Médecine Régénérative Universelle implantent leur premier dispensaire à "
    "Genève, dans le quartier des Grottes, alors en pleine gentrification post-inondation.")

CONSEQ_ANCIENNES = (
    "L'ouverture du dispensaire accélère la normalisation des thérapies régénératives dans les systèmes de "
    "santé publics, tout en exacerbant les tensions entre les États souverainistes anti-réseau et les "
    "institutions technocratiques. À Genève, le taux de mortalité prématurée chute de 12 % en trois ans, "
    "mais les inégalités d'accès persistent entre les zones couvertes par le réseau et les territoires "
    "exclus. Le modèle inspire d'autres hubs urbains régénératifs, comme le Hub Nairobi-Kigali, qui lance "
    "un programme similaire en 2044.")
CONSEQ_NOUVELLES = (
    "L'implantation du premier dispensaire des Réseaux à Genève rapproche les thérapies régénératives des "
    "habitants des Grottes, dans un quartier en pleine gentrification où la question de l'accès aux soins "
    "se pose dès l'origine.")

# (nom, ancien, nouveau, occurrences attendues)
REMPLACEMENTS = [
    ("description", DESC_ANCIENNE, DESC_NOUVELLE, 2),
    ("réalisation",
     " Financé par l'OMS Étendue et le Consortium Panafricain des Biotechnologies pour l'Équité (CPBE), "
     "l'établissement propose des thérapies géniques accessibles pour inverser les séquelles des décennies "
     "de pollution, marquant une étape symbolique dans l'équité sanitaire mondiale.", "", 2),
    ("conséquences", CONSEQ_ANCIENNES, CONSEQ_NOUVELLES, 2),
    ("date_label", "date_label: automne 2042\n", "date_label: 2042\n", 1),
    ("acteur (en-tête)", "    - oms_etendue_new_sustainability\n", "", 1),
    ("acteur (corps)", "- [[oms_etendue_new_sustainability]]\n", "", 1),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not FICHE.is_file():
        sys.exit(f"✗ introuvable : {FICHE}")
    src = FICHE.read_text(encoding="utf-8")
    if "date_label: 2042\n" in src and "Elias Voss" not in src:
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
    if (not isinstance(fm, dict) or str(fm.get("date_label")) != "2042"
            or fm.get("acteurs_impliques") != ["reseaux_de_medecine_regenerative_universelle_new_sustainability"]):
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
