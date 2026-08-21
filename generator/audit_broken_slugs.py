#!/usr/bin/env python3
"""
audit_broken_slugs.py

Chantier backlog "Encodage portugais cassé dans certains slugs"
(Partie 2, repéré le 8 août 2026, jamais traité) — audit en lecture
seule des slugs déjà générés avant le correctif du 14 août 2026 sur
slugify() (create_entities_and_instances.py).

Ancienne fonction : table d'accents français en dur (é/è/ê/ë/à/â/ä/ù/
û/ü/î/ï/ô/ö/ç). Tout caractère accentué absent de cette table (portugais
ã/õ/á/í/ó/ú, espagnol ñ, allemand ü déjà couvert mais ß non, etc.)
tombait dans le re.sub générique et devenait "_" au lieu d'être
translittéré — d'où des slugs comme "rede_paulista_de_distribuic_o_
algor_tmica" au lieu de "rede_paulista_de_distribuicao_algoritmica".

Ce script ne renomme RIEN. Il scanne entites/*.md, recalcule le slug
que la fonction CORRIGÉE produirait à partir du frontmatter `name`, et
le compare au `slug` réellement enregistré sur disque. Toute différence
est un candidat à vérifier manuellement — un renommage de slug a des
répercussions en cascade (fichier, wikilinks, instances, event_
instances, alliances/oppositions d'autres fiches) et ne doit pas être
fait automatiquement sans revue.

Usage :
    python3 audit_broken_slugs.py --vault-root .
"""

import argparse
import re
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML requis : pip install pyyaml")


def slugify_fixed(text):
    """Version corrigée (14 août 2026) — normalisation Unicode générique."""
    s = unicodedata.normalize("NFD", text or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def parse_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---")
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


def main():
    parser = argparse.ArgumentParser(
        description="Audit en lecture seule des slugs potentiellement "
                     "cassés par l'ancien bug d'accents non-français."
    )
    parser.add_argument("--vault-root", default=".",
                         help="Racine du vault (défaut : répertoire courant)")
    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    entites_dir = vault_root / "entites"
    if not entites_dir.exists():
        raise SystemExit(f"Dossier introuvable : {entites_dir}")

    candidates = []
    total = 0

    for md_file in sorted(entites_dir.glob("*.md")):
        if md_file.name == "entity_template.md":
            # Gabarit, pas une vraie fiche — même principe que
            # l'exclusion d'instance_template.md dans le dashboard.
            # (nom réel sur disque : entity_template.md, en anglais —
            # à ne pas confondre avec "entite_template.md" utilisé par
            # erreur dans la doc et dans une première version de ce
            # filtre.)
            continue
        fm = parse_frontmatter(md_file)
        current_slug = fm.get("slug")
        name = fm.get("name") or fm.get("nom")
        if not current_slug or not name:
            continue
        total += 1

        expected_slug = slugify_fixed(name)
        if expected_slug != current_slug:
            # Ne garder que les cas où la différence ressemble
            # spécifiquement au bug (perte de caractère -> underscore
            # simple ou double là où la version corrigée a une lettre) —
            # on affiche tout écart pour revue manuelle, sans filtrer,
            # car un faux négatif serait pire qu'un faux positif ici.
            candidates.append((md_file.name, current_slug, expected_slug, name))

    print(f"{total} fiche(s) entités auditée(s) (avec name/nom + slug).\n")

    if not candidates:
        print("Aucun écart trouvé entre le slug enregistré et le slug "
              "recalculé avec la fonction corrigée. Rien à corriger.")
        return

    print(f"{len(candidates)} candidat(s) à vérifier manuellement "
          f"(slug actuel ≠ slug recalculé) :\n")
    for fname, current, expected, name in candidates:
        print(f"  {fname}")
        print(f"    nom            : {name}")
        print(f"    slug actuel    : {current}")
        print(f"    slug recalculé : {expected}")
        print()

    print("Rappel : ce script ne renomme rien. Chaque candidat doit être "
          "vérifié à la main — un écart peut aussi venir d'un renommage "
          "volontaire passé, pas seulement du bug d'accents. Une fois "
          "confirmés, les vrais cas nécessitent un script de migration "
          "dédié (renommage fichier + réécriture de toutes les "
          "références), sur le même principe que fix_arctic_passage_"
          "duplicate.py mais pour un renommage plutôt qu'une fusion.")


if __name__ == "__main__":
    main()
