#!/usr/bin/env python3
"""
rename_broken_slugs.py

Chantier backlog "encodage portugais cassé" (Partie 2, 8 août 2026) —
migration des 2 cas confirmés par audit_broken_slugs.py :
  - rede_paulista_de_distribuic_o_algor_tmica -> rede_paulista_de_distribuicao_algoritmica
  - frente_sert_o_livre -> frente_sertao_livre

Contrairement à fix_arctic_passage_duplicate.py (fusion de deux
entités distinctes, suppression de l'une), ce script effectue un
RENOMMAGE simple : même entité, slug corrigé. Il renomme le fichier
archétype et ses instances par scénario, met à jour leur contenu
interne (slug:, entite:), puis réécrit toute référence externe
(wikilinks, listes alliance/opposition) vers le nouveau slug, et met
à jour entites/_entities_list.json.

Ne touche pas entites_custom/processed.yaml (historique de traitement,
pas des références vivantes).

Dry-run par défaut. --execute pour appliquer. Backup .bak créé pour
chaque fichier modifié, y compris sous l'ancien nom pour les fichiers
renommés (avant suppression de l'original).

Usage :
    python3 rename_broken_slugs.py --vault-root .
    python3 rename_broken_slugs.py --vault-root . --execute
"""

import argparse
import re
from pathlib import Path

RENAMES = [
    ("rede_paulista_de_distribuic_o_algor_tmica",
     "rede_paulista_de_distribuicao_algoritmica"),
    ("frente_sert_o_livre", "frente_sertao_livre"),
]


def whole_word_pattern(slug):
    """Occurrence isolée du slug — pas une sous-chaîne d'un slug plus
    long partageant le même préfixe (ex. l'entité vs une de ses
    instances slug_scenario)."""
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(slug) + r"(?![A-Za-z0-9_])")


def find_instance_files(vault_root, old_entity_slug):
    instances_dir = vault_root / "instances"
    if not instances_dir.exists():
        return []
    return sorted(instances_dir.glob(f"{old_entity_slug}_*.md"))


def plan_renames(vault_root):
    file_renames = []       # (old_path, new_path)
    text_replacements = []  # (old_slug, new_slug)

    for old_entity_slug, new_entity_slug in RENAMES:
        entity_path = vault_root / "entites" / f"{old_entity_slug}.md"
        if entity_path.exists():
            file_renames.append(
                (entity_path, vault_root / "entites" / f"{new_entity_slug}.md")
            )

        for inst_path in find_instance_files(vault_root, old_entity_slug):
            suffix = inst_path.stem[len(old_entity_slug):]  # ex. "_breakdown"
            new_inst_path = vault_root / "instances" / f"{new_entity_slug}{suffix}.md"
            file_renames.append((inst_path, new_inst_path))
            text_replacements.append((inst_path.stem, new_entity_slug + suffix))

        text_replacements.append((old_entity_slug, new_entity_slug))

    # Plus long d'abord : les slugs d'instance (entité + suffixe scénario)
    # doivent être remplacés avant le slug d'entité nu, sinon ce dernier
    # matcherait en premier et laisserait le suffixe scénario orphelin.
    text_replacements.sort(key=lambda pair: len(pair[0]), reverse=True)
    return file_renames, text_replacements


def rewrite_text_content(text, text_replacements):
    n_changes = 0
    for old_slug, new_slug in text_replacements:
        new_text, n = whole_word_pattern(old_slug).subn(new_slug, text)
        if n:
            n_changes += n
            text = new_text
    return text, n_changes


def find_all_referencing_files(vault_root, text_replacements, file_renames):
    renamed_paths = {old for old, _ in file_renames}
    doc_dir = vault_root / "documentation"
    targets = []
    for md_file in vault_root.rglob("*.md"):
        if md_file in renamed_paths or ".bak" in md_file.suffixes:
            continue
        # documentation/ = handoffs, rapports, backlogs historiques —
        # jamais réécrits rétroactivement, même logique que
        # entites_custom/processed.yaml pour fix_arctic_passage_
        # duplicate.py (décision du 14 août 2026).
        try:
            md_file.relative_to(doc_dir)
            continue
        except ValueError:
            pass
        try:
            text = md_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(whole_word_pattern(old).search(text) for old, _ in text_replacements):
            targets.append(md_file)
    return sorted(set(targets))


def update_entities_list_json(vault_root, execute):
    """Remplacement de texte ciblé (pas de parse/dump JSON complet, pour
    préserver le formatage d'origine)."""
    json_path = vault_root / "entites" / "_entities_list.json"
    if not json_path.exists():
        return None, 0

    text = json_path.read_text(encoding="utf-8")
    original = text
    n_changes = 0
    for old_slug, new_slug in RENAMES:
        pattern = re.compile(r'"' + re.escape(old_slug) + r'"')
        text, n = pattern.subn(f'"{new_slug}"', text)
        n_changes += n

    if n_changes and execute:
        json_path.with_suffix(json_path.suffix + ".bak").write_text(
            original, encoding="utf-8"
        )
        json_path.write_text(text, encoding="utf-8")

    return json_path, n_changes


def main():
    parser = argparse.ArgumentParser(
        description="Renomme les 2 slugs cassés par le bug d'accents "
                     "et propage le changement à tout le vault."
    )
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    file_renames, text_replacements = plan_renames(vault_root)

    if not file_renames:
        print("Aucun fichier archétype/instance trouvé pour les slugs "
              "concernés. Rien à faire (déjà renommés, ou --vault-root "
              "incorrect).")
        return

    print(f"{'[DRY-RUN] ' if not args.execute else ''}Fichiers à renommer :\n")
    for old_path, new_path in file_renames:
        print(f"  {old_path.relative_to(vault_root)}")
        print(f"    -> {new_path.relative_to(vault_root)}")

    referencing_files = find_all_referencing_files(vault_root, text_replacements, file_renames)
    print(f"\n{len(referencing_files)} fiche(s) externe(s) référençant un slug à mettre à jour :\n")
    total_ref_changes = 0
    for md_file in referencing_files:
        text = md_file.read_text(encoding="utf-8")
        _, n = rewrite_text_content(text, text_replacements)
        total_ref_changes += n
        print(f"  {md_file.relative_to(vault_root)} — {n} référence(s)")

    json_path, n_json = update_entities_list_json(vault_root, execute=False)
    if json_path:
        print(f"\n  {json_path.relative_to(vault_root)} — {n_json} entrée(s) à mettre à jour")

    print(f"\nTotal : {len(file_renames)} fichier(s) à renommer, "
          f"{total_ref_changes} référence(s) externe(s) dans {len(referencing_files)} fiche(s), "
          f"{n_json} entrée(s) dans _entities_list.json.")

    if not args.execute:
        print("\nAucune écriture effectuée (dry-run). Relancer avec --execute "
              "pour appliquer (backup .bak créé automatiquement).")
        return

    # --- Exécution réelle ---
    for old_path, new_path in file_renames:
        text = old_path.read_text(encoding="utf-8")
        new_text, _ = rewrite_text_content(text, text_replacements)
        old_path.with_suffix(old_path.suffix + ".bak").write_text(text, encoding="utf-8")
        new_path.write_text(new_text, encoding="utf-8")
        old_path.unlink()

    for md_file in referencing_files:
        text = md_file.read_text(encoding="utf-8")
        new_text, n = rewrite_text_content(text, text_replacements)
        if n:
            md_file.with_suffix(md_file.suffix + ".bak").write_text(text, encoding="utf-8")
            md_file.write_text(new_text, encoding="utf-8")

    update_entities_list_json(vault_root, execute=True)

    print("\nModifications appliquées. Backups .bak créés (y compris sous "
          "l'ancien nom pour les fichiers renommés, avant suppression).")
    print("\nValider ensuite :")
    print("  python3 validate.py --verbose")


if __name__ == "__main__":
    main()
