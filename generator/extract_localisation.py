"""
extract_localisation.py
-----------------------
Extrait le champ `localisation` (zone / lieu / type_lieu) sur les 119 fiches riches
du vault : instances sans `statut: officialise_minimal` + toutes les event_instances.

Trois issues possibles par fiche :
  1. Lieu précis trouvé → champ extrait et écrit dans le frontmatter.
  2. Entité transnationale sans ancrage local → champ laissé vide, assumé.
  3. Ambigu → marqué `statut: review_manuelle`, jamais deviné.

Garanties :
  - --dry-run : appelle quand même l'API, mais n'écrit rien sur disque.
  - Sauvegarde .bak automatique avant toute écriture réelle.
  - Validation mécanique : le slug `zone` est vérifié contre geographie/{scenario}.md.
  - Fiches déjà traitées (localisation présent dans le frontmatter) ignorées par défaut.
      → utiliser --force pour les retraiter.

Usage :
  python3 extract_localisation.py --dry-run
  python3 extract_localisation.py
  python3 extract_localisation.py --scenario reference        # un seul scénario
  python3 extract_localisation.py --slug nexcore_reference    # une seule fiche
  python3 extract_localisation.py --force                     # retraite les déjà faits
"""

import os
import re
import sys
import json
import yaml
import shutil
import argparse
import anthropic

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

VAULT_PATH = "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098"

INSTANCES_DIR     = os.path.join(VAULT_PATH, "instances")
EVENT_INST_DIR    = os.path.join(VAULT_PATH, "event_instances")
GEOGRAPHIE_DIR    = os.path.join(VAULT_PATH, "geographie")

MODEL      = "claude-sonnet-4-6"
MAX_TOKENS = 1024

VALID_SCENARIOS = [
    "fortress_world", "new_sustainability", "breakdown",
    "eco_communalism", "policy_reform", "reference",
]

VALID_TYPE_LIEU = ["ville", "region", "infrastructure", "site_strategique"]

NEED_ACTION_DIR = os.path.join(VAULT_PATH, "documentation", "need_action")
REVIEW_REPORT   = os.path.join(NEED_ACTION_DIR, "localisation_review.md")

# ─────────────────────────────────────────────────────────────
# RAPPORT NEED_ACTION
# ─────────────────────────────────────────────────────────────

def scan_review_manuelle():
    """
    Scanne TOUT le vault (instances + event_instances) et retourne
    la liste des fiches ayant localisation.statut = review_manuelle.
    """
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
            entries.append({
                "slug":     fm.get("slug", fname.replace(".md", "")),
                "scenario": fm.get("scenario", "?"),
                "type":     ftype,
                "zone":     loc.get("zone") or "(aucune)",
                "lieu":     loc.get("lieu") or "(aucun)",
                "type_lieu":loc.get("type_lieu") or "(null)",
                "note":     loc.get("note") or "",
            })
    return entries


def generate_review_report(dry_run=False):
    """
    Genere documentation/need_action/localisation_review.md
    en scannant l etat reel du vault. Ecrasement complet a chaque appel.
    """
    if dry_run:
        return

    os.makedirs(NEED_ACTION_DIR, exist_ok=True)
    entries = scan_review_manuelle()

    from datetime import datetime
    from collections import defaultdict
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Localisation — Review manuelle",
        "",
        f"_Genere automatiquement par extract_localisation.py — {now}_",
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
                slug     = e["slug"]
                etype    = e["type"]
                zone     = e["zone"]
                lieu     = e["lieu"]
                type_lieu= e["type_lieu"]
                note     = e["note"]
                lines.append(f"### {slug}")
                lines.append(f"- **type** : {etype}")
                lines.append(f"- **zone candidate** : {zone}")
                lines.append(f"- **lieu** : {lieu}")
                lines.append(f"- **type_lieu** : {type_lieu}")
                if note:
                    lines.append(f"- **note** : {note}")
                lines.append("")

    content = "\n".join(lines)
    with open(REVIEW_REPORT, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Rapport need_action mis a jour : documentation/need_action/localisation_review.md")
    print(f"   ({len(entries)} fiche(s) en attente)")


# ─────────────────────────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────────────────────────

def parse_md_file(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")
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
        except yaml.YAMLError as e:
            print(f"  [WARN] YAML dans {filepath} : {e}")
            frontmatter = {}
    return {"frontmatter": frontmatter, "body": body, "raw": raw}


# ─────────────────────────────────────────────────────────────
# CHARGEMENT DES ZONES VALIDES PAR SCÉNARIO
# ─────────────────────────────────────────────────────────────

_geo_cache = {}

def load_zones(scenario):
    """Retourne un dict {slug: zone_dict} pour un scénario."""
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


def zones_summary(scenario):
    """Résumé textuel des zones disponibles pour le prompt Claude."""
    zones = load_zones(scenario)
    if not zones:
        return "(aucune géographie disponible pour ce scénario)"
    lines = []
    for slug, z in zones.items():
        nom    = z.get("nom", slug)
        niveau = z.get("niveau", "?")
        parent = z.get("parent") or "racine"
        desc   = (z.get("description") or "")[:120]
        lines.append(f"  - {slug} (niveau {niveau}, parent: {parent}) — {nom} : {desc}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# COLLECTE DES FICHES À TRAITER
# ─────────────────────────────────────────────────────────────

def collect_fiches(scenario_filter=None, slug_filter=None, force=False):
    """
    Retourne la liste des fiches riches à traiter.
    Format : [{"path": ..., "type": "instance"|"event_instance", "scenario": ...}]
    """
    fiches = []

    # --- instances riches (sans statut: officialise_minimal)
    for fname in sorted(os.listdir(INSTANCES_DIR)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(INSTANCES_DIR, fname)
        parsed = parse_md_file(path)
        fm = parsed["frontmatter"]

        if fm.get("statut") == "officialise_minimal":
            continue

        scenario = fm.get("scenario", "")
        if scenario not in VALID_SCENARIOS:
            continue  # ignore templates ou fichiers mal formés
        if scenario_filter and scenario != scenario_filter:
            continue
        slug = fm.get("slug", fname.replace(".md", ""))
        if slug_filter and slug != slug_filter:
            continue
        if not force and "localisation" in fm:
            continue

        fiches.append({"path": path, "type": "instance", "scenario": scenario, "slug": slug})

    # --- event_instances (toutes riches)
    for fname in sorted(os.listdir(EVENT_INST_DIR)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(EVENT_INST_DIR, fname)
        parsed = parse_md_file(path)
        fm = parsed["frontmatter"]

        scenario = fm.get("scenario", "")
        if scenario not in VALID_SCENARIOS:
            continue  # ignore templates ou fichiers mal formés
        if scenario_filter and scenario != scenario_filter:
            continue
        slug = fm.get("slug", fname.replace(".md", ""))
        if slug_filter and slug != slug_filter:
            continue
        if not force and "localisation" in fm:
            continue

        fiches.append({"path": path, "type": "event_instance", "scenario": scenario, "slug": slug})

    return fiches


# ─────────────────────────────────────────────────────────────
# APPEL API — EXTRACTION
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es un assistant d'extraction de données géographiques pour le projet Ourrassol 2098.
Tu reçois la fiche d'une entité ou d'un événement fictif situé en 2098, ainsi que la liste des zones géographiques disponibles pour ce scénario.

Ta tâche : identifier si cette entité/événement a un ancrage géographique local précis, et si oui, le mapper sur une zone existante.

Réponds UNIQUEMENT en JSON valide, sans markdown, sans commentaire, avec exactement ces clés :
{
  "issue": "extrait" | "vide" | "ambigu",
  "zone": "<slug_exact_ou_null>",
  "lieu": "<texte_libre_ou_null>",
  "type_lieu": "ville" | "region" | "infrastructure" | "site_strategique" | null,
  "justification": "<une phrase courte>"
}

Règles strictes :
- `issue: "extrait"` → tu as trouvé un lieu précis dans le texte ET tu peux le mapper sur une zone existante.
  `zone` doit être un slug EXACT de la liste fournie. `lieu` est le nom du lieu en texte libre. `type_lieu` est obligatoire.
- `issue: "vide"` → l'entité est clairement transnationale ou sans ancrage local fort (ex: institution mondiale, réseau diffus).
  `zone`, `lieu`, `type_lieu` sont tous null. C'est assumé, pas un échec.
- `issue: "ambigu"` → tu hésites : lieu trouvé mais non mappable sur une zone existante, ou plusieurs zones possibles sans évidence claire.
  Mets quand même ton meilleur candidat dans `zone` et `lieu` pour aider la review manuelle, avec `type_lieu` si pertinent.
  Ne devine jamais silencieusement : préfère `ambigu` à une extraction douteuse.

Ne crée JAMAIS un slug de zone qui ne figure pas dans la liste fournie."""


def build_user_prompt(fiche_content, scenario, fiche_type):
    zones_txt = zones_summary(scenario)
    return f"""Scénario : {scenario}
Type de fiche : {fiche_type}

=== ZONES GÉOGRAPHIQUES DISPONIBLES POUR CE SCÉNARIO ===
{zones_txt}

=== CONTENU DE LA FICHE ===
{fiche_content}

Extrais le champ `localisation` selon les règles données."""


def call_api(user_prompt):
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=0.0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text.strip()


def parse_api_response(raw):
    """Parse la réponse JSON de Claude. Retourne (dict, error_str|None)."""
    try:
        # Nettoyer éventuels backticks
        clean = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(clean)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON invalide : {e}\nRéponse brute : {raw[:300]}"


# ─────────────────────────────────────────────────────────────
# VALIDATION MÉCANIQUE
# ─────────────────────────────────────────────────────────────

def validate_extraction(data, scenario):
    """
    Vérifie mécaniquement la cohérence de la réponse Claude.
    Retourne (ok: bool, errors: list[str]).
    """
    errors = []
    issue = data.get("issue")

    if issue not in ("extrait", "vide", "ambigu"):
        errors.append(f"issue invalide : {issue!r}")
        return False, errors

    zone  = data.get("zone")
    lieu  = data.get("lieu")
    tl    = data.get("type_lieu")

    if issue == "extrait":
        if not zone:
            errors.append("issue=extrait mais zone est null")
        else:
            zones = load_zones(scenario)
            if zone not in zones:
                errors.append(f"slug zone inconnu : {zone!r} (non trouvé dans geographie/{scenario}.md)")
        if not lieu:
            errors.append("issue=extrait mais lieu est null")
        if tl not in VALID_TYPE_LIEU:
            errors.append(f"type_lieu invalide : {tl!r}")

    elif issue == "vide":
        if zone or lieu or tl:
            errors.append("issue=vide mais zone/lieu/type_lieu ne sont pas tous null")

    elif issue == "ambigu":
        # Meilleur effort — on accepte si zone est connue ou null
        if zone:
            zones = load_zones(scenario)
            if zone not in zones:
                errors.append(f"slug zone ambigu inconnu : {zone!r}")

    return len(errors) == 0, errors


# ─────────────────────────────────────────────────────────────
# ÉCRITURE DU CHAMP DANS LE FRONTMATTER
# ─────────────────────────────────────────────────────────────

def build_localisation_yaml(data):
    """Construit le bloc YAML du champ localisation."""
    issue = data["issue"]
    if issue == "vide":
        return (
            "localisation:\n"
            "  zone: null\n"
            "  lieu: null\n"
            "  type_lieu: null\n"
            "  note: transnationale_sans_ancrage\n"
        )
    elif issue == "ambigu":
        zone = data.get("zone") or "null"
        lieu = data.get("lieu") or "null"
        tl   = data.get("type_lieu") or "null"
        just = data.get("justification", "").replace('"', "'")
        return (
            f"localisation:\n"
            f"  zone: {zone}\n"
            f"  lieu: {lieu}\n"
            f"  type_lieu: {tl}\n"
            f"  statut: review_manuelle\n"
            f"  note: \"{just}\"\n"
        )
    else:  # extrait
        zone = data.get("zone") or "null"
        lieu = data.get("lieu") or "null"
        tl   = data.get("type_lieu") or "null"
        return (
            f"localisation:\n"
            f"  zone: {zone}\n"
            f"  lieu: {lieu}\n"
            f"  type_lieu: {tl}\n"
        )


def inject_localisation(filepath, localisation_yaml, dry_run):
    """
    Insère le champ localisation dans le frontmatter du fichier.
    Le champ est placé juste après `scenario:` s'il existe, sinon à la fin du frontmatter.
    Crée un .bak avant toute écriture réelle.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    fm_match = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)", raw, re.DOTALL)
    if not fm_match:
        print(f"  [WARN] Pas de frontmatter parseable dans {filepath}, skip.")
        return False

    header    = fm_match.group(1)
    fm_body   = fm_match.group(2)
    separator = fm_match.group(3)
    body      = fm_match.group(4)

    # Supprimer un éventuel localisation existant (cas --force)
    fm_body = re.sub(
        r"\nlocalisation:.*?(?=\n\S|\Z)", "", fm_body, flags=re.DOTALL
    ).rstrip()

    # Insérer après la ligne `scenario:` si présente, sinon à la fin
    lines = fm_body.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^scenario\s*:", line):
            insert_idx = i + 1
            break

    loc_lines = localisation_yaml.rstrip("\n").split("\n")
    if insert_idx is not None:
        lines = lines[:insert_idx] + loc_lines + lines[insert_idx:]
    else:
        lines = lines + loc_lines

    new_fm = "\n".join(lines)
    new_raw = header + new_fm + separator + body

    if dry_run:
        return True

    # Sauvegarde .bak
    shutil.copy2(filepath, filepath + ".bak")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_raw)
    return True


# ─────────────────────────────────────────────────────────────
# TRAITEMENT D'UNE FICHE
# ─────────────────────────────────────────────────────────────

def process_fiche(fiche, dry_run, verbose=True):
    """
    Traite une fiche : appel API → validation → écriture.
    Retourne un dict résultat.
    """
    path     = fiche["path"]
    scenario = fiche["scenario"]
    slug     = fiche["slug"]
    ftype    = fiche["type"]

    if verbose:
        print(f"\n[{ftype}] {slug}")
        print(f"  scénario : {scenario}")

    # Lire le contenu complet de la fiche
    parsed    = parse_md_file(path)
    fm        = parsed["frontmatter"]
    body      = parsed["body"]
    # Contenu utile = frontmatter YAML reformaté + body
    fm_txt    = yaml.dump(fm, allow_unicode=True, default_flow_style=False)
    full_text = f"=== FRONTMATTER ===\n{fm_txt}\n=== CORPS MARKDOWN ===\n{body}"

    # Appel API
    user_prompt = build_user_prompt(full_text, scenario, ftype)
    try:
        raw_response = call_api(user_prompt)
    except Exception as e:
        print(f"  [ERREUR API] {e}")
        return {"slug": slug, "issue": "erreur_api", "error": str(e)}

    # Parse JSON
    data, parse_err = parse_api_response(raw_response)
    if parse_err:
        print(f"  [ERREUR PARSE] {parse_err}")
        return {"slug": slug, "issue": "erreur_parse", "error": parse_err}

    # Validation mécanique
    ok, errors = validate_extraction(data, scenario)
    if not ok:
        print(f"  [VALIDATION ÉCHOUÉE] {'; '.join(errors)}")
        print(f"  Réponse Claude : {raw_response[:200]}")
        return {"slug": slug, "issue": "erreur_validation", "errors": errors, "raw": raw_response}

    issue = data["issue"]
    if verbose:
        zone = data.get("zone") or "(null)"
        lieu = data.get("lieu") or "(null)"
        just = data.get("justification", "")
        print(f"  issue     : {issue}")
        print(f"  zone      : {zone}")
        print(f"  lieu      : {lieu}")
        print(f"  motif     : {just}")

    # Construction YAML et injection
    loc_yaml = build_localisation_yaml(data)
    success  = inject_localisation(path, loc_yaml, dry_run)

    if not success:
        return {"slug": slug, "issue": "erreur_injection"}

    mode_tag = "[DRY-RUN] " if dry_run else ""
    if verbose:
        print(f"  {mode_tag}→ écrit" if not dry_run else f"  [DRY-RUN] → simulé, rien écrit")

    return {"slug": slug, "issue": issue, "zone": data.get("zone"), "lieu": data.get("lieu")}


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extraction du champ localisation sur les fiches riches d'Ourrassol 2098."
    )
    parser.add_argument("--dry-run",  action="store_true",
                        help="Appelle l'API mais n'écrit rien sur disque.")
    parser.add_argument("--scenario", type=str, default=None,
                        help="Restreindre à un seul scénario.")
    parser.add_argument("--slug",     type=str, default=None,
                        help="Traiter uniquement la fiche avec ce slug.")
    parser.add_argument("--force",    action="store_true",
                        help="Retraiter les fiches qui ont déjà un champ localisation.")
    parser.add_argument("--report-only", action="store_true",
                        help="Génère uniquement le rapport need_action sans extraction.")
    args = parser.parse_args()

    dry_run = args.dry_run

    print("=" * 60)
    print("EXTRACT_LOCALISATION — Ourrassol 2098")
    print("=" * 60)
    if dry_run:
        print("MODE DRY-RUN : aucune écriture sur disque\n")

    # Mode rapport seul
    if args.report_only:
        print("MODE REPORT-ONLY : génération du rapport need_action.\n")
        generate_review_report(dry_run=False)
        return

    # Collecte
    fiches = collect_fiches(
        scenario_filter=args.scenario,
        slug_filter=args.slug,
        force=args.force,
    )

    if not fiches:
        print("Aucune fiche à traiter (toutes déjà traitées ? Utiliser --force pour retraiter).")
        generate_review_report(dry_run=dry_run)
        return

    print(f"Fiches à traiter : {len(fiches)}")
    if args.scenario:
        print(f"  Filtre scénario : {args.scenario}")
    if args.slug:
        print(f"  Filtre slug     : {args.slug}")
    print()

    # Traitement
    results = []
    for i, fiche in enumerate(fiches, 1):
        print(f"[{i}/{len(fiches)}]", end=" ")
        r = process_fiche(fiche, dry_run=dry_run, verbose=True)
        results.append(r)

    # Récapitulatif
    print("\n" + "=" * 60)
    print("RÉCAPITULATIF")
    print("=" * 60)

    counts = {"extrait": 0, "vide": 0, "ambigu": 0, "erreur": 0}
    for r in results:
        issue = r.get("issue", "erreur")
        if issue in counts:
            counts[issue] += 1
        else:
            counts["erreur"] += 1

    print(f"  Extraits (zone trouvée)    : {counts['extrait']}")
    print(f"  Vides assumés (transnat.)  : {counts['vide']}")
    print(f"  Ambigus (review manuelle)  : {counts['ambigu']}")
    print(f"  Erreurs                    : {counts['erreur']}")
    print(f"  Total traité               : {len(results)}")

    # Détail des ambigus
    ambigus = [r for r in results if r.get("issue") == "ambigu"]
    if ambigus:
        print(f"\n  → {len(ambigus)} fiche(s) à review manuelle :")
        for r in ambigus:
            print(f"     • {r['slug']} — zone candidate : {r.get('zone') or '(aucune)'}")

    # Détail des erreurs
    erreurs = [r for r in results if r.get("issue", "").startswith("erreur")]
    if erreurs:
        print(f"\n  → {len(erreurs)} erreur(s) :")
        for r in erreurs:
            print(f"     • {r['slug']} : {r.get('error') or r.get('errors') or r['issue']}")

    if dry_run:
        print("\n[DRY-RUN] Aucun fichier modifié.")
    else:
        print(f"\nFiches modifiées : {counts['extrait'] + counts['vide'] + counts['ambigu']}")
        print("Sauvegardes .bak créées pour chaque fichier modifié.")

    # Mise à jour du rapport need_action (scan vault réel, pas seulement ce run)
    generate_review_report(dry_run=dry_run)


if __name__ == "__main__":
    main()
