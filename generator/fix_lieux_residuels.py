#!/usr/bin/env python3
"""
fix_lieux_residuels.py — Ourrassol 2098
==========================================

Script PONCTUEL, à usage unique : nettoie un résidu mécanique laissé par une
version antérieure de enrich_geographie_recursive.py (avant correction de
dedupe_promoted_lieux). Cette ancienne version ne retirait un lieu_emblematique
promu QUE chez le parent désigné par le LLM (champ `parent` de la nouvelle
zone) — si ce même lieu était listé en double sur une AUTRE zone de niveau 1
dès l'étape 1 (cas réel rencontré : "Genève-Lac-Retraité" et "Nairobi" listés
à la fois sur leur zone de rattachement et sur une zone régionale englobante),
ce doublon restait visible après coup.

CE QUE FAIT CE SCRIPT
----------------------
Pour un fichier geographie/{scenario}.md DÉJÀ enrichi (donc contenant des
zones de niveau 2+ avec un champ `promu_depuis` rempli) :
1. Relit le fichier tel quel, aucun appel API.
2. Pour chaque zone de niveau 2+ ayant un `promu_depuis`, cherche ce nom EXACT
   dans `lieux_emblematiques` de TOUTES les autres zones du fichier (pas
   seulement son parent désigné — c'est précisément le trou que ce script
   comble) et le retire partout où il traîne encore. Un même lieu peut
   apparaître en résidu sur plusieurs zones distinctes (cas réel rencontré).
3. Régénère le YAML structuré ET la section markdown "## Zones" (pour que les
   deux restent cohérents — un lieu retiré du YAML mais encore visible dans
   le rendu markdown serait une incohérence silencieuse). La section
   "Vue d'ensemble" et tout ce qui suit "## Notes / zones à enrichir" sont
   préservés tels quels, jamais régénérés.
4. Réécrit le fichier avec une sauvegarde .bak automatique.

N'AJOUTE AUCUNE ZONE, NE MODIFIE AUCUN AUTRE CHAMP qu'une zone existante.
de doublons résiduels. Ce script n'a normalement plus lieu d'être pour des
fichiers générés après la correction de dedupe_promoted_lieux dans
enrich_geographie_recursive.py — gardé en archive au cas où un autre résidu
de ce type apparaîtrait sur un fichier généré avec l'ancienne version.

USAGE
-----
    python3 fix_lieux_residuels.py --scenario reference --dry-run
    python3 fix_lieux_residuels.py --scenario reference
    python3 fix_lieux_residuels.py --all
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]


def parse_md(filepath):
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not m:
        return None, None
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def find_residual_duplicates(zones):
    """Retourne la liste des retraits à effectuer :
    [(nom_du_lieu, slug_de_la_zone_promue, slug_de_la_zone_a_nettoyer), ...]
    sans rien modifier — pure détection. Un même lieu peut apparaître en
    résidu sur PLUSIEURS zones différentes (cas réel rencontré : 3 occurrences
    pour un seul lieu), donc cette fonction peut retourner plusieurs entrées
    pour un même nom de lieu."""
    promu_par = {}  # nom du lieu -> slug de la zone qui en est issue
    for z in zones:
        pd = z.get("promu_depuis")
        if pd:
            promu_par[str(pd).strip()] = z["slug"]

    a_nettoyer = []
    for z in zones:
        for lieu in (z.get("lieux_emblematiques") or []):
            nom = str(lieu.get("nom", "")).strip()
            if nom in promu_par and promu_par[nom] != z["slug"]:
                a_nettoyer.append((nom, promu_par[nom], z["slug"]))
    return a_nettoyer


def apply_cleanup(zones, residus):
    """Retire mécaniquement les lieux listés dans `residus` des zones
    concernées. Modifie `zones` en place. Retourne le nombre de retraits."""
    by_slug = {z["slug"]: z for z in zones}
    count = 0
    for nom, _zone_promue_slug, zone_a_nettoyer_slug in residus:
        zone = by_slug[zone_a_nettoyer_slug]
        lieux = zone.get("lieux_emblematiques") or []
        avant = len(lieux)
        lieux = [l for l in lieux if str(l.get("nom", "")).strip() != nom]
        zone["lieux_emblematiques"] = lieux
        count += avant - len(lieux)
    return count


def extract_vue_ensemble_and_notes(body):
    """Extrait le texte de 'Vue d'ensemble' et tout ce qui suit la section
    'Zones' (la note d'enrichissement éventuelle + 'Notes / zones à enrichir')
    pour les préserver tels quels — seule la section '## Zones' est
    régénérée par ce script, jamais le reste du corps markdown."""
    m_vue = re.search(r"## Vue d'ensemble\s*\n(.*?)(?=\n## Zones)", body, re.DOTALL)
    vue_ensemble_brut = m_vue.group(1) if m_vue else "\n"

    m_notes = re.search(r"(## Notes / zones à enrichir.*)\Z", body, re.DOTALL)
    notes_brut = m_notes.group(1) if m_notes else (
        "## Notes / zones à enrichir\n_Espace libre, jamais lu par les scripts — "
        "ajoute ici tes idées, brouillons, zones à\ncréer manuellement._\n"
    )
    return vue_ensemble_brut, notes_brut


def render_zone_md(zone):
    """Rend le bloc markdown d'UNE zone — même format que
    enrich_geographie_recursive.py::build_geographie_md, pour que le rendu
    reste identique entre les deux scripts."""
    heading = "#" * min(2 + zone.get("niveau", 1), 6)
    parent_txt = f" — sous [[{zone['parent']}]]" if zone.get("parent") else ""
    md = f"\n{heading} {zone['nom']}{parent_txt}\n\n"
    md += f"*{zone['type']} — niveau {zone.get('niveau', 1)} — statut : {zone['statut']}*\n\n"
    origine = zone.get("origine_reelle") or []
    if origine:
        parts = []
        for o in origine:
            p = o.get("entite", "?")
            if o.get("portion"):
                p += f" ({o['portion']})"
            parts.append(p)
        md += f"**Origine réelle (2026)** : {', '.join(parts)}\n\n"
    if zone.get("periode_transition"):
        evt = zone.get("evenement_transition")
        evt_txt = f" — voir [[{evt}]]" if evt else ""
        md += f"**Transition** : {zone['periode_transition']}{evt_txt}\n\n"
    md += f"{zone.get('description', '')}\n\n"
    if zone.get("tensions_internes"):
        md += f"**Tensions internes** : {zone['tensions_internes']}\n\n"
    lieux = zone.get("lieux_emblematiques") or []
    if lieux:
        md += "**Lieux emblématiques** :\n"
        for lieu in lieux:
            note = f" — {lieu.get('notes', '')}" if lieu.get("notes") else ""
            md += f"- {lieu.get('nom', '?')} ({lieu.get('type', '')}){note}\n"
        md += "\n"
    rel = zone.get("relations") or {}
    if rel.get("allies"):
        md += f"**Alliés** : {', '.join(rel['allies'])}\n\n"
    if rel.get("rivaux"):
        md += f"**Rivaux** : {', '.join(rel['rivaux'])}\n\n"
    if zone.get("sources_attestees"):
        md += f"*Sources attestées : {', '.join(zone['sources_attestees'])}*\n"
    return md


def rebuild_content(scenario, fm, vue_ensemble_brut, notes_brut, zones):
    """Reconstruit le fichier complet : frontmatter YAML mis à jour (zones
    nettoyées, date_derniere_maj actualisée) + corps markdown régénéré pour
    la section Zones uniquement, vue d'ensemble et notes préservées telles
    quelles."""
    sorted_zones = sorted(zones, key=lambda z: (z.get("niveau", 1), z.get("slug", "")))

    fm_out = dict(fm)
    fm_out["zones"] = sorted_zones
    from datetime import datetime
    fm_out["date_derniere_maj"] = datetime.now().strftime("%Y-%m-%d")

    zones_yaml = yaml.dump(sorted_zones, allow_unicode=True, sort_keys=False,
                            default_flow_style=False, width=100)
    zones_yaml_indented = "\n".join(
        ("  " + line if line.strip() else line) for line in zones_yaml.splitlines()
    )

    fm_header = (
        f"scenario: {fm_out.get('scenario', scenario)}\n"
        f"type: {fm_out.get('type', 'geographie_monde')}\n"
        f"date_creation: {fm_out.get('date_creation', '')}\n"
        f"date_derniere_maj: {fm_out['date_derniere_maj']}\n"
        f"zones:\n{zones_yaml_indented.rstrip()}"
    )

    zones_md = "".join(render_zone_md(z) for z in sorted_zones)

    content = f"""---
{fm_header}
---

# Géographie — {scenario}

## Vue d'ensemble
{vue_ensemble_brut.strip()}

## Zones
{zones_md if zones_md.strip() else "_Aucune zone identifiée — à enrichir manuellement._"}

{notes_brut}"""
    return content


def process_scenario(scenario, dry_run):
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    print(f"\n=== {scenario} ===")
    if not path.exists():
        print(f"  ✗ {path} n'existe pas — rien à nettoyer.")
        return

    fm, body = parse_md(path)
    if fm is None:
        print(f"  ✗ Frontmatter YAML introuvable ou invalide dans {path.name}.")
        return

    zones = fm.get("zones") or []
    residus = find_residual_duplicates(zones)

    if not residus:
        print("  Aucun résidu détecté — fichier déjà propre.")
        return

    print(f"  {len(residus)} résidu(s) détecté(s) :")
    for nom, zone_promue, zone_a_nettoyer in residus:
        print(f"    - '{nom}' (promu en '{zone_promue}') encore listé sur "
              f"'{zone_a_nettoyer}' — à retirer")

    if dry_run:
        print("  (--dry-run : rien n'est écrit)")
        return

    nb_retires = apply_cleanup(zones, residus)
    vue_ensemble_brut, notes_brut = extract_vue_ensemble_and_notes(body)
    new_content = rebuild_content(scenario, fm, vue_ensemble_brut, notes_brut, zones)

    backup_path = path.with_suffix(".md.bak")
    shutil.copy(path, backup_path)
    print(f"  → Sauvegarde créée : {backup_path.name}")

    path.write_text(new_content, encoding="utf-8")
    print(f"  ✓ {nb_retires} entrée(s) retirée(s) (YAML + markdown régénéré), "
          f"fichier réécrit : {path.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Nettoie les résidus de lieux_emblematiques non dédupliqués "
                     "par l'ancienne version d'enrich_geographie_recursive.py "
                     "(aucun appel API, pure correction mécanique)"
    )
    parser.add_argument("--scenario", choices=SCENARIOS,
                         help="Un seul scénario à traiter")
    parser.add_argument("--all", action="store_true",
                         help="Traiter les 6 scénarios")
    parser.add_argument("--dry-run", action="store_true",
                         help="Affiche les résidus détectés sans rien écrire")
    args = parser.parse_args()

    if not args.scenario and not args.all:
        sys.exit("Précise --scenario {nom} ou --all.")

    print("=" * 60)
    print("OURRASSOL 2098 — Nettoyage résidus lieux_emblematiques")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)")

    targets = SCENARIOS if args.all else [args.scenario]
    for scenario in targets:
        process_scenario(scenario, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("Terminé.")
    print("=" * 60)


if __name__ == "__main__":
    main()
