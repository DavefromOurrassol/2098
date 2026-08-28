#!/usr/bin/env python3
"""
set_priorite_forcee.py — Ourrassol 2098

Active ou désactive le flag `priorite_forcee` sur une fiche instance
existante, par patch chirurgical du frontmatter (pas de réécriture
complète, pas d'appel LLM). Conçu le 22 août 2026, à la demande de
David : pouvoir forcer délibérément la présence durable d'une entité
dans les articles d'un scénario donné (ex. un événement narratif majeur
qui ferait d'une entité un acteur permanent qu'on veut voir cité
partout — cas d'usage donné : arrivée d'extraterrestres).

Portée : PAR INSTANCE (une entité peut être forcée sur un scénario mais
pas un autre) — décision actée avec David le 22 août.

Niveau de contrôle : garantie de PRÉSENCE/CITATION dans
filtered_instances (comme la garantie d'inclusion des instances custom,
21 août 2026) — PAS garantie du statut de sujet principal de chaque
article. Câblage côté sélection dans loader.py
(_select_with_custom_guarantee, filter_instances_for_thematique) :
voir le patch livré séparément le même jour.

Une instance priorite_forcee=true échappe automatiquement au mécanisme
de pénalité d'usage (voir loader.py, _select_least_used_instances) --
elle ne passe jamais par ce circuit de rotation, donc aucun conflit
entre les deux mécanismes, aucun cas particulier à gérer ici.

Utilisable en CLI (outil autonome, GUI section entites_nettoyage) ET
importable comme fonction depuis create_entities_and_instances.py
(appel automatique après la génération d'une instance custom, si
l'idée le demande).

USAGE CLI :
    python3 set_priorite_forcee.py --slug directive_kontinuum_policy_reform --value true
    python3 set_priorite_forcee.py --slug directive_kontinuum_policy_reform --value false
"""

import argparse
import re
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
INSTANCES_DIR = VAULT_ROOT / "instances"

# Même regex que celle utilisée pour isoler le frontmatter dans les
# autres scripts de patch chirurgical du projet (fix_alliances_
# oppositions.py, fix_annee_debut_placeholder.py) : bloc entre les deux
# premières lignes '---'.
_FRONTMATTER_RE = re.compile(r"^(---\n)(.*?\n)(---\n)", re.DOTALL)
_PRIORITE_LINE_RE = re.compile(r"^priorite_forcee:.*\n", re.MULTILINE)


def set_priorite_forcee(slug, value, instances_dir=None):
    """
    Active (value=True) ou désactive (value=False) priorite_forcee sur
    la fiche instance `slug` (déjà scénario-suffixé, ex.
    'directive_kontinuum_policy_reform' -- le slug d'instance EST le
    nom de fichier, pas besoin de scénario séparé).

    Retourne (bool succès, str message).
    """
    if instances_dir is None:
        instances_dir = INSTANCES_DIR

    filepath = Path(instances_dir) / f"{slug}.md"
    if not filepath.exists():
        return False, f"fiche introuvable : {filepath}"

    text = filepath.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return False, f"frontmatter introuvable ou mal formé : {filepath}"

    fm_open, fm_body, fm_close = match.groups()
    rest = text[match.end():]

    if value:
        new_line = "priorite_forcee: true\n"
        if _PRIORITE_LINE_RE.search(fm_body):
            fm_body = _PRIORITE_LINE_RE.sub(new_line, fm_body)
        else:
            if not fm_body.endswith("\n"):
                fm_body += "\n"
            fm_body += new_line
        msg = f"priorite_forcee: true — {slug}"
    else:
        if not _PRIORITE_LINE_RE.search(fm_body):
            # Rien à faire — déjà à l'état par défaut (absent = false).
            return True, f"priorite_forcee déjà absent (= false) — {slug}"
        fm_body = _PRIORITE_LINE_RE.sub("", fm_body)
        msg = f"priorite_forcee retiré (= false) — {slug}"

    new_text = fm_open + fm_body + fm_close + rest
    filepath.write_text(new_text, encoding="utf-8")
    return True, msg


def main():
    parser = argparse.ArgumentParser(
        description="Active ou désactive priorite_forcee sur une instance existante."
    )
    parser.add_argument("--slug", required=True,
                         help="Slug de l'instance (déjà scénario-suffixé, "
                              "ex: directive_kontinuum_policy_reform)")
    parser.add_argument("--scenario", required=False,
                         help="Envoyé par le GUI pour filtrer la liste "
                              "d'instances proposées -- non utilisé ici, "
                              "le scénario est déjà encodé dans --slug.")
    parser.add_argument("--value", required=True, choices=["true", "false"],
                         help="true = forcer la présence, false = retirer le forçage")
    args = parser.parse_args()

    ok, msg = set_priorite_forcee(args.slug, args.value == "true")
    if ok:
        print(f"  ✓ {msg}")
        sys.exit(0)
    else:
        print(f"  ✗ {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
