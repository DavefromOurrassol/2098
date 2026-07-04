"""
Ourrassol 2098 — merge_pays_monde.py
Étend zones_pays.json pour couvrir tous les pays du monde (~198 entrées),
sans toucher aux affectations existantes. Backup automatique.

Usage : python3 merge_pays_monde.py
(à lancer depuis gui/, ou avec --path pour cibler un autre zones_pays.json)
"""
import json
import argparse
from pathlib import Path

NOUVEAUX_PAYS = [
    # Europe
    "Irlande", "Luxembourg", "Monaco", "Andorre", "Liechtenstein", "Saint-Marin",
    "Vatican", "Malte", "Chypre", "Croatie", "Slovénie", "Bosnie-Herzégovine",
    "Monténégro", "Macédoine du Nord", "Albanie", "Bulgarie", "Moldavie",
    "Biélorussie", "Slovaquie", "Lituanie", "Lettonie", "Estonie", "Kosovo",
    # Asie
    "Arménie", "Turkménistan", "Tadjikistan", "Afghanistan", "Népal", "Bhoutan",
    "Sri Lanka", "Maldives", "Birmanie", "Laos", "Cambodge", "Brunei",
    "Timor oriental", "Corée du Nord", "Taïwan", "Jordanie", "Oman", "Bahreïn",
    "Palestine",
    # Afrique
    "Égypte", "Libye", "Mauritanie", "Gambie", "Guinée-Bissau", "Guinée",
    "Sierra Leone", "Liberia", "Côte d'Ivoire", "Togo", "Bénin", "Cap-Vert",
    "São Tomé-et-Príncipe", "Cameroun", "République centrafricaine", "Gabon",
    "Guinée équatoriale", "République du Congo", "Angola", "Zambie", "Malawi",
    "Tanzanie", "Ouganda", "Burundi", "Djibouti", "Somalie", "Érythrée",
    "Namibie", "Botswana", "Lesotho", "Eswatini", "Comores", "Madagascar",
    "Maurice", "Seychelles",
    # Amériques
    "Cuba", "Haïti", "République dominicaine", "Jamaïque", "Bahamas", "Belize",
    "Guatemala", "Honduras", "Salvador", "Nicaragua", "Costa Rica", "Panama",
    "Trinité-et-Tobago", "Barbade", "Guyana", "Suriname", "Équateur", "Paraguay",
    "Uruguay", "Sainte-Lucie", "Grenade", "Saint-Vincent-et-les-Grenadines",
    "Antigua-et-Barbuda", "Saint-Christophe-et-Niévès", "Dominique",
    # Océanie
    "Papouasie-Nouvelle-Guinée", "Fidji", "Vanuatu", "Îles Salomon", "Samoa",
    "Tonga", "Kiribati", "Micronésie", "Palaos", "Îles Marshall", "Nauru",
    "Tuvalu",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="zones_pays.json",
                         help="Chemin vers zones_pays.json (défaut : ./zones_pays.json)")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"❌ Fichier introuvable : {target}")
        return

    data = json.loads(target.read_text(encoding="utf-8"))
    pays_liste = data.get("pays_liste", [])
    existants = set(pays_liste)

    ajoutes = [p for p in NOUVEAUX_PAYS if p not in existants]

    if not ajoutes:
        print("✓ Rien à ajouter — tous les pays sont déjà présents.")
        return

    # Backup
    bak = target.with_suffix(target.suffix + ".bak")
    bak.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"📦 Backup créé : {bak}")

    data["pays_liste"] = pays_liste + ajoutes
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"✓ {len(ajoutes)} pays ajoutés à pays_liste (total : {len(data['pays_liste'])})")
    print(f"  Aucune affectation existante n'a été modifiée.")
    print(f"  Les nouveaux pays apparaîtront comme 'non affectés' (gris) sur la carte.")

if __name__ == "__main__":
    main()
