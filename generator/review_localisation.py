"""
review_localisation.py
----------------------
Review interactive des fiches marquées `statut: review_manuelle` dans le champ
`localisation`. Affiche chaque cas un par un, liste les zones disponibles du scénario,
et applique la décision directement dans le frontmatter.

Décisions possibles par fiche :
  [V] Valider la zone candidate suggérée par Claude
  [C] Choisir une autre zone dans la liste
  [0] Passer en vide assumé (entité transnationale sans ancrage)
  [S] Skip — laisser en review_manuelle pour plus tard

Usage :
  python3 review_localisation.py
  python3 review_localisation.py --scenario reference
  python3 review_localisation.py --dry-run     # affiche sans écrire
"""

import os
import re
import sys
import yaml
import shutil
import argparse

# ─────────────────────────────────────────────────────────────
# CONFIGURATION (identique à extract_localisation.py)
# ─────────────────────────────────────────────────────────────

VAULT_PATH      = "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098"
INSTANCES_DIR   = os.path.join(VAULT_PATH, "instances")
EVENT_INST_DIR  = os.path.join(VAULT_PATH, "event_instances")
GEOGRAPHIE_DIR  = os.path.join(VAULT_PATH, "geographie")
NEED_ACTION_DIR = os.path.join(VAULT_PATH, "documentation", "need_action")
REVIEW_REPORT   = os.path.join(NEED_ACTION_DIR, "localisation_review.md")

VALID_SCENARIOS = [
    "fortress_world", "new_sustainability", "breakdown",
    "eco_communalism", "policy_reform", "reference",
]

VALID_TYPE_LIEU = ["ville", "region", "infrastructure", "site_strategique"]

# ─────────────────────────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────────────────────────

def parse_md_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
    frontmatter = {}
    body = raw
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if fm_match:
        fm_str = fm_match.group(1)
        body   = fm_match.group(2).strip()
        fm_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", fm_str)
        try:
            frontmatter = yaml.safe_load(fm_clean) or {}
        except yaml.YAMLError:
            frontmatter = {}
    return {"frontmatter": frontmatter, "body": body, "raw": raw}


# ─────────────────────────────────────────────────────────────
# GÉOGRAPHIE
# ─────────────────────────────────────────────────────────────

_geo_cache = {}

def load_zones(scenario):
    if scenario in _geo_cache:
        return _geo_cache[scenario]
    path = os.path.join(GEOGRAPHIE_DIR, f"{scenario}.md")
    if not os.path.exists(path):
        _geo_cache[scenario] = {}
        return {}
    parsed = parse_md_file(path)
    zones_list = parsed["frontmatter"].get("zones", []) or []
    zones = {z["slug"]: z for z in zones_list if isinstance(z, dict) and "slug" in z}
    _geo_cache[scenario] = zones
    return zones


# ─────────────────────────────────────────────────────────────
# COLLECTE DES FICHES À REVIEWER
# ─────────────────────────────────────────────────────────────

def collect_review_manuelle(scenario_filter=None):
    entries = []
    for dirpath, ftype in [
        (INSTANCES_DIR,  "instance"),
        (EVENT_INST_DIR, "event_instance"),
    ]:
        for fname in sorted(os.listdir(dirpath)):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                parsed = parse_md_file(path)
            except Exception:
                continue
            fm  = parsed["frontmatter"]
            loc = fm.get("localisation")
            if not isinstance(loc, dict):
                continue
            if loc.get("statut") != "review_manuelle":
                continue
            scenario = fm.get("scenario", "")
            if scenario_filter and scenario != scenario_filter:
                continue
            entries.append({
                "path":     path,
                "slug":     fm.get("slug", fname.replace(".md", "")),
                "scenario": scenario,
                "type":     ftype,
                "loc":      loc,
                "fm":       fm,
            })
    return entries


# ─────────────────────────────────────────────────────────────
# ÉCRITURE
# ─────────────────────────────────────────────────────────────

def build_localisation_yaml(zone, lieu, type_lieu):
    """Construit le bloc YAML localisation propre (résolu, sans statut review)."""
    zone_val     = zone     or "null"
    lieu_val     = lieu     or "null"
    type_lieu_val= type_lieu or "null"
    note_line    = ""
    if not zone and not lieu:
        note_line = "  note: transnationale_sans_ancrage\n"
    return (
        f"localisation:\n"
        f"  zone: {zone_val}\n"
        f"  lieu: {lieu_val}\n"
        f"  type_lieu: {type_lieu_val}\n"
        f"{note_line}"
    )


def write_localisation(filepath, loc_yaml, dry_run):
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    fm_match = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)", raw, re.DOTALL)
    if not fm_match:
        print("  [WARN] Frontmatter non parseable, skip.")
        return False

    header    = fm_match.group(1)
    fm_body   = fm_match.group(2)
    separator = fm_match.group(3)
    body      = fm_match.group(4)

    # Supprimer le localisation existant (review_manuelle)
    fm_body = re.sub(
        r"\nlocalisation:.*?(?=\n\S|\Z)", "", fm_body, flags=re.DOTALL
    ).rstrip()

    # Insérer après scenario:
    lines = fm_body.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^scenario\s*:", line):
            insert_idx = i + 1
            break

    loc_lines = loc_yaml.rstrip("\n").split("\n")
    if insert_idx is not None:
        lines = lines[:insert_idx] + loc_lines + lines[insert_idx:]
    else:
        lines = lines + loc_lines

    new_raw = header + "\n".join(lines) + separator + body

    if dry_run:
        return True

    shutil.copy2(filepath, filepath + ".bak")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_raw)
    return True


# ─────────────────────────────────────────────────────────────
# MISE À JOUR DU RAPPORT
# ─────────────────────────────────────────────────────────────

def regenerate_report():
    """Relit le vault et régénère localisation_review.md."""
    from datetime import datetime
    from collections import defaultdict

    entries = collect_review_manuelle()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Localisation — Review manuelle",
        "",
        f"_Genere automatiquement par review_localisation.py — {now}_",
        f"_Source de verite : etat reel des fiches dans le vault._",
        "",
        f"**{len(entries)} fiche(s) en attente de review.**",
        "",
    ]

    if not entries:
        lines.append("OK Aucune fiche en attente — toutes les localisations sont resolues.")
    else:
        by_scenario = defaultdict(list)
        for e in entries:
            by_scenario[e["scenario"]].append(e)

        for scenario in VALID_SCENARIOS:
            if scenario not in by_scenario:
                continue
            sc_entries = by_scenario[scenario]
            lines.append(f"## {scenario} ({len(sc_entries)})")
            lines.append("")
            for e in sc_entries:
                loc  = e["loc"]
                slug = e["slug"]
                zone = loc.get("zone") or "(aucune)"
                lieu = loc.get("lieu") or "(aucun)"
                tl   = loc.get("type_lieu") or "(null)"
                note = loc.get("note") or ""
                lines.append(f"### {slug}")
                lines.append(f"- **type** : {e['type']}")
                lines.append(f"- **zone candidate** : {zone}")
                lines.append(f"- **lieu** : {lieu}")
                lines.append(f"- **type_lieu** : {tl}")
                if note:
                    lines.append(f"- **note** : {note}")
                lines.append("")

    os.makedirs(NEED_ACTION_DIR, exist_ok=True)
    with open(REVIEW_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n📋 Rapport mis à jour : documentation/need_action/localisation_review.md")
    print(f"   ({len(entries)} fiche(s) restantes)")


# ─────────────────────────────────────────────────────────────
# AFFICHAGE
# ─────────────────────────────────────────────────────────────

def display_entry(entry, index, total):
    loc      = entry["loc"]
    scenario = entry["scenario"]
    zones    = load_zones(scenario)

    print()
    print("=" * 65)
    print(f"  [{index}/{total}] {entry['slug']}")
    print(f"  scénario : {scenario}   type : {entry['type']}")
    print("=" * 65)

    zone_candidate = loc.get("zone") or "(aucune)"
    lieu           = loc.get("lieu") or "(aucun)"
    type_lieu      = loc.get("type_lieu") or "(null)"
    note           = loc.get("note") or ""

    print(f"\n  Zone candidate : {zone_candidate}")
    print(f"  Lieu           : {lieu}")
    print(f"  Type lieu      : {type_lieu}")
    if note:
        print(f"\n  Note Claude    : {note}")

    print(f"\n  Zones disponibles ({scenario}) :")
    zone_list = list(zones.items())
    for i, (slug, z) in enumerate(zone_list, 1):
        nom    = z.get("nom", slug)
        niveau = z.get("niveau", "?")
        marker = " ◀" if slug == zone_candidate else ""
        print(f"    {i:2}. {slug}{marker}")
        print(f"        {nom} (niveau {niveau})")

    return zone_list


def prompt_type_lieu(current):
    print(f"\n  Type de lieu actuel : {current}")
    print("  Types disponibles : " + " / ".join(f"[{i+1}] {t}" for i, t in enumerate(VALID_TYPE_LIEU)))
    while True:
        rep = input("  Choisir (1-4) ou Entrée pour garder : ").strip()
        if rep == "":
            return current
        try:
            idx = int(rep) - 1
            if 0 <= idx < len(VALID_TYPE_LIEU):
                return VALID_TYPE_LIEU[idx]
        except ValueError:
            pass
        print("  Saisie invalide.")


# ─────────────────────────────────────────────────────────────
# BOUCLE PRINCIPALE
# ─────────────────────────────────────────────────────────────

def run_review(entries, dry_run):
    total    = len(entries)
    resolved = 0
    skipped  = 0

    for i, entry in enumerate(entries, 1):
        zone_list = display_entry(entry, i, total)
        loc       = entry["loc"]

        zone_candidate = loc.get("zone")
        lieu_actuel    = loc.get("lieu") or "null"
        type_actuel    = loc.get("type_lieu") or "null"

        print()
        print("  [V] Valider la zone candidate")
        print("  [C] Choisir une autre zone")
        print("  [0] Vide assumé (transnationale, pas d'ancrage)")
        print("  [S] Skip — laisser en review_manuelle")
        print("  [Q] Quitter")

        while True:
            rep = input("\n  Décision > ").strip().upper()

            if rep == "Q":
                print("\n  Arrêt demandé.")
                regenerate_report()
                print(f"\n  Bilan : {resolved} résolus, {skipped} skippés, {total - i} non traités.")
                return

            elif rep == "S":
                print("  → Skippé.")
                skipped += 1
                break

            elif rep == "0":
                loc_yaml = build_localisation_yaml(None, None, None)
                if write_localisation(entry["path"], loc_yaml, dry_run):
                    tag = "[DRY-RUN] " if dry_run else ""
                    print(f"  {tag}→ Vide assumé écrit.")
                    resolved += 1
                break

            elif rep == "V":
                if not zone_candidate:
                    print("  Pas de zone candidate — utilisez [C] pour en choisir une, ou [0] pour vide.")
                    continue
                type_lieu = prompt_type_lieu(type_actuel)
                loc_yaml  = build_localisation_yaml(zone_candidate, lieu_actuel, type_lieu)
                if write_localisation(entry["path"], loc_yaml, dry_run):
                    tag = "[DRY-RUN] " if dry_run else ""
                    print(f"  {tag}→ Zone candidate validée : {zone_candidate}")
                    resolved += 1
                break

            elif rep == "C":
                print("  Entrez le numéro de la zone souhaitée :")
                while True:
                    num = input("  > ").strip()
                    try:
                        idx = int(num) - 1
                        if 0 <= idx < len(zone_list):
                            chosen_slug, chosen_zone = zone_list[idx]
                            print(f"  Zone choisie : {chosen_slug}")
                            # Lieu
                            print(f"  Lieu actuel  : {lieu_actuel}")
                            new_lieu = input("  Nouveau lieu (Entrée pour garder) : ").strip()
                            if not new_lieu:
                                new_lieu = lieu_actuel
                            # Type lieu
                            type_lieu = prompt_type_lieu(type_actuel)
                            loc_yaml  = build_localisation_yaml(chosen_slug, new_lieu, type_lieu)
                            if write_localisation(entry["path"], loc_yaml, dry_run):
                                tag = "[DRY-RUN] " if dry_run else ""
                                print(f"  {tag}→ Zone écrite : {chosen_slug}")
                                resolved += 1
                            break
                        else:
                            print(f"  Numéro hors plage (1-{len(zone_list)}).")
                    except ValueError:
                        print("  Saisie invalide.")
                break

            else:
                print("  Touche invalide — V / C / 0 / S / Q")

    regenerate_report()
    print(f"\n{'=' * 65}")
    print(f"  Terminé. {resolved} résolus, {skipped} skippés.")
    print(f"{'=' * 65}")


# ─────────────────────────────────────────────────────────────
# AUTO-RESOLVE

# ─────────────────────────────────────────────────────────────
# AUTO-RESOLVE
# ─────────────────────────────────────────────────────────────

AUTO_SYSTEM_PROMPT = """Tu es un assistant de résolution de localisations géographiques pour le projet Ourrassol 2098.
Une fiche a été marquée `statut: review_manuelle` car son ancrage géographique était ambigu lors de l'extraction initiale.
Tu disposes maintenant de la note d'hésitation originale, du contenu de la fiche, et de la liste complète des zones disponibles.

Ta tâche : trancher définitivement.

Réponds UNIQUEMENT en JSON valide, sans markdown, sans commentaire :
{
  "decision": "valider" | "choisir" | "vide",
  "zone": "<slug_exact_ou_null>",
  "lieu": "<texte_libre_ou_null>",
  "type_lieu": "ville" | "region" | "infrastructure" | "site_strategique" | null,
  "justification": "<une phrase>"
}

Règles :
- "valider" → tu confirmes la zone candidate déjà proposée. `zone` = slug candidate.
- "choisir" → tu choisis une zone différente dans la liste. `zone` = slug exact de la liste.
- "vide"    → l'entité est véritablement transnationale sans ancrage dominant. `zone`, `lieu`, `type_lieu` = null.

Le slug `zone` doit TOUJOURS être un slug exact de la liste fournie, ou null.
Ne crée jamais un slug inventé."""


def build_auto_prompt(entry):
    loc      = entry["loc"]
    scenario = entry["scenario"]
    zones    = load_zones(scenario)

    zone_candidate = loc.get("zone") or "(aucune)"
    lieu           = loc.get("lieu") or "(aucun)"
    type_lieu      = loc.get("type_lieu") or "(null)"
    note           = loc.get("note") or ""

    zones_txt = "\n".join(
        f"  - {slug} — {z.get('nom', slug)} (niveau {z.get('niveau','?')})"
        for slug, z in zones.items()
    )

    parsed   = parse_md_file(entry["path"])
    fm_txt   = yaml.dump(parsed["frontmatter"], allow_unicode=True, default_flow_style=False)
    body_txt = parsed["body"][:2000]  # limité pour ne pas exploser le contexte

    return f"""Scénario : {scenario}
Slug : {entry['slug']}

=== LOCALISATION ACTUELLE (à trancher) ===
zone candidate : {zone_candidate}
lieu           : {lieu}
type_lieu      : {type_lieu}
note d'hésitation : {note}

=== ZONES DISPONIBLES ===
{zones_txt}

=== CONTENU DE LA FICHE (extrait) ===
{fm_txt}
{body_txt}

Tranche définitivement."""


def call_auto_api(user_prompt):
    import anthropic
    import json

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        temperature=0.0,
        system=AUTO_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = message.content[0].text.strip()
    clean = re.sub(r"```json|```", "", raw).strip()
    return json.loads(clean)


def validate_auto_response(data, scenario):
    errors = []
    decision = data.get("decision")
    if decision not in ("valider", "choisir", "vide"):
        errors.append(f"decision invalide : {decision!r}")
        return False, errors

    zone = data.get("zone")
    if decision in ("valider", "choisir"):
        if not zone:
            errors.append("zone null pour decision valider/choisir")
        else:
            zones = load_zones(scenario)
            if zone not in zones:
                errors.append(f"slug inconnu : {zone!r}")
        if not data.get("type_lieu") in VALID_TYPE_LIEU:
            errors.append(f"type_lieu invalide : {data.get('type_lieu')!r}")
    elif decision == "vide":
        if zone or data.get("lieu") or data.get("type_lieu"):
            errors.append("vide mais zone/lieu/type_lieu non null")

    return len(errors) == 0, errors


def run_auto_resolve(entries, dry_run):
    total    = len(entries)
    resolved = 0
    skipped  = 0

    print(f"\n  Résolution automatique de {total} fiche(s)...\n")

    for i, entry in enumerate(entries, 1):
        slug     = entry["slug"]
        scenario = entry["scenario"]
        loc      = entry["loc"]

        print(f"  [{i}/{total}] {slug}")
        print(f"    zone candidate : {loc.get('zone') or '(aucune)'}")

        try:
            prompt = build_auto_prompt(entry)
            data   = call_auto_api(prompt)
        except Exception as e:
            print(f"    [ERREUR API] {e} → skip")
            skipped += 1
            continue

        ok, errors = validate_auto_response(data, scenario)
        if not ok:
            print(f"    [VALIDATION] {'; '.join(errors)} → skip")
            skipped += 1
            continue

        decision     = data["decision"]
        zone_finale  = data.get("zone")
        lieu_final   = data.get("lieu") or loc.get("lieu") or "null"
        type_final   = data.get("type_lieu")
        justification= data.get("justification", "")

        print(f"    décision      : {decision}")
        print(f"    zone retenue  : {zone_finale or '(vide)'}")
        print(f"    motif         : {justification}")

        if decision == "vide":
            loc_yaml = (
                "localisation:\n"
                "  zone: null\n"
                "  lieu: null\n"
                "  type_lieu: null\n"
                "  note: transnationale_sans_ancrage\n"
            )
        else:
            loc_yaml = (
                f"localisation:\n"
                f"  zone: {zone_finale}\n"
                f"  lieu: {lieu_final}\n"
                f"  type_lieu: {type_final}\n"
            )

        success = write_localisation(entry["path"], loc_yaml, dry_run)
        if success:
            tag = "[DRY-RUN] " if dry_run else ""
            print(f"    {tag}→ écrit")
            resolved += 1
        else:
            print(f"    [ERREUR] écriture échouée → skip")
            skipped += 1

        print()

    regenerate_report()
    print(f"{'=' * 65}")
    print(f"  Auto-resolve terminé.")
    print(f"  Résolus : {resolved}   Skippés/erreurs : {skipped}")
    print(f"{'=' * 65}")

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Review des localisations ambiguës — Ourrassol 2098."
    )
    parser.add_argument("--scenario", type=str, default=None,
                        help="Restreindre à un seul scénario.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche et simule sans écrire.")
    parser.add_argument("--auto-resolve", action="store_true",
                        help="Résolution automatique via Claude (sans interaction).")
    args = parser.parse_args()

    print("=" * 65)
    print("  REVIEW LOCALISATION — Ourrassol 2098")
    print("=" * 65)
    if args.dry_run:
        print("  MODE DRY-RUN : aucune écriture sur disque")
    if args.auto_resolve:
        print("  MODE AUTO-RESOLVE : résolution automatique par Claude")

    entries = collect_review_manuelle(scenario_filter=args.scenario)

    if not entries:
        print("\n  Aucune fiche en review_manuelle. Rien à faire.")
        return

    print(f"\n  {len(entries)} fiche(s) à reviewer", end="")
    if args.scenario:
        print(f" (scénario : {args.scenario})", end="")
    print()

    if args.auto_resolve:
        run_auto_resolve(entries, dry_run=args.dry_run)
    else:
        run_review(entries, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
