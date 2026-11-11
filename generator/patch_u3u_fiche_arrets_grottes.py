#!/usr/bin/env python3
"""
patch_u3u_fiche_arrets_grottes.py — Ourrassol 2098 (U3u, 11 novembre 2026) — PONCTUEL
=====================================================================================
Corrige à la main la fiche event_instances/arrets_dispensaire_grottes_2098_new_sustainability.md
d'après l'article du 24 mars 2098 (même démarche que U3h) :
  1. localisation : zone geneve_lacus_cgai, lieu « quartier des Grottes, Genève »
     (l'extraction avait mis afrique_continentale à cause des « communautés sahéliennes ») ;
  2. description : retire « rapporté par le Réseau d'Information Ouvert dans le cadre du scénario
     *new_sustainability* » (source inventée, nom du scénario hors fiction) et ajoute la libération
     après la pétition de 120 000 Genevois (phrase de l'article) ;
  3. réalisation : ajoute la libération après la pétition ;
  4. conséquences : retire le « débat » et l'apaisement géopolitique inventés ;
  5. note de cohérence : « l'article source » -> « le scénario ».
Les textes sont remplacés dans l'en-tête YAML ET dans le corps. Contrôle : chaque ancre doit
être trouvée le nombre de fois attendu, et l'en-tête doit rester du YAML valide.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3u_fiche_arrets_grottes.py            # dry-run
  python3 generator/patch_u3u_fiche_arrets_grottes.py --apply    # applique (.bak_u3u)
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
FICHE = RACINE / "event_instances" / "arrets_dispensaire_grottes_2098_new_sustainability.md"
TAG = "u3u"

# (nom, ancien, nouveau, occurrences attendues)
REMPLACEMENTS = [
    ("localisation",
     "  zone: afrique_continentale\n  lieu: quartier de la Jonction\n",
     "  zone: geneve_lacus_cgai\n  lieu: quartier des Grottes, Genève\n", 1),
    ("description",
     "pour « détournement de ressources médicales », un événement rapporté par le Réseau "
     "d'Information Ouvert dans le cadre du scénario *new_sustainability*.",
     "pour « détournement de ressources médicales » ; une pétition signée par 120 000 Genevois "
     "a forcé leur libération.", 2),
    ("réalisation",
     "des cliniques privées. Leur arrestation intervient",
     "des cliniques privées. Une pétition signée par 120 000 Genevois force leur libération. "
     "Leur arrestation intervient", 2),
    ("conséquences",
     "L'arrestation des trois membres du Dispensaire des Grottes suscite un débat sur les limites "
     "de la gouvernance algorithmique en matière de santé, tout en renforçant la légitimité des "
     "réseaux de médecine régénérative comme alternative aux systèmes institutionnels. Elle "
     "accentue les tensions entre les institutions technocratiques et les acteurs locaux, tout en "
     "apaisant temporairement les conflits géopolitiques liés à l'accès aux soins, les populations "
     "marginalisées trouvant un écho à leur lutte dans cette affaire.",
     "L'arrestation des trois membres du Dispensaire des Grottes, suivie de leur libération après "
     "une pétition de 120 000 Genevois, montre la force de la mobilisation locale et renforce la "
     "légitimité des réseaux de médecine régénérative face aux institutions technocratiques. Elle "
     "accentue les tensions entre ces institutions et les acteurs locaux.", 2),
    ("note de cohérence",
     "documentées dans l'article source et les niveaux actuels",
     "du scénario et les niveaux actuels", 2),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not FICHE.is_file():
        sys.exit(f"✗ introuvable : {FICHE}")
    src = FICHE.read_text(encoding="utf-8")
    if "geneve_lacus_cgai" in src and "afrique_continentale" not in src:
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
    if not isinstance(fm, dict) or (fm.get("localisation") or {}).get("zone") != "geneve_lacus_cgai":
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
