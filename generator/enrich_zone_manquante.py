#!/usr/bin/env python3
"""
enrich_zone_manquante.py — Ourrassol 2098
===========================================

Comble les champs narratifs vides d'une zone qui existe déjà dans
geographie/{scenario}.md mais qui n'a jamais été traitée par un LLM —
typiquement une zone créée via le split de l'onglet Carte (`✂️ scinder`),
qui initialise `tensions_internes: ""` et `periode_transition: null` sans
jamais appeler de modèle (voir _apply_split_zone() dans gui/app.py).

Contrairement à build_geographie_monde.py (étape 1, crée des zones depuis
zéro à partir de tout le corpus) et enrich_geographie_recursive.py (étape 2,
crée des SOUS-zones), ce script ne crée ni ne restructure rien : il édite
UNIQUEMENT `tensions_internes`, `periode_transition` et `evenement_transition`
d'une zone déjà existante, en laissant tout le reste (slug, nom, type,
origine_reelle, statut, relations...) strictement inchangé.

USAGE
-----
    # Une zone précise
    python3 enrich_zone_manquante.py --scenario fortress_world --slug al_hima

    # Toutes les zones du scénario qui ont au moins un des deux champs vide
    python3 enrich_zone_manquante.py --scenario fortress_world --tous-manquants

    # Aperçu sans écrire (par défaut -- il faut --force pour écrire)
    python3 enrich_zone_manquante.py --scenario fortress_world --slug al_hima --force
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from llm_client import call_llm  # même tier que build_geographie_monde.py

VAULT_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_DIR = VAULT_ROOT / "instances"
EVENT_INSTANCES_DIR = VAULT_ROOT / "event_instances"
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

ENRICH_MAX_TOKENS = 1200


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def parse_md(filepath):
    if not filepath.exists():
        return {}, ""
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not m:
        return {}, raw
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2).strip()


def load_geo_file(scenario):
    """Retourne (fm, body_brut, raw_complet) de geographie/{scenario}.md."""
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    if not path.exists():
        return None, None, None
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return None, None, None
    fm = yaml.safe_load(parts[1]) or {}
    return fm, parts[2], raw


def zone_a_completer(zone):
    """True si tensions_internes OU periode_transition est vide/absent."""
    return not (zone.get("tensions_internes") or "").strip() or not zone.get("periode_transition")


def gather_zone_context_texts(scenario, zone):
    """
    Corpus pertinent pour CETTE zone : ses sources_attestees explicites si
    elle en a (peu probable pour une zone issue d'un split, mais on les
    utilise si présentes), sinon les instances/événements dont
    localisation.zone remonte jusqu'à cette zone (chaîne de parents),
    à défaut de mieux pour une zone toute neuve sans aucune source.
    """
    slug = zone.get("slug")
    sources = set(zone.get("sources_attestees") or [])
    blocks = []

    def scan(dirpath, ftype, champs):
        if not dirpath.exists():
            return
        for path in sorted(dirpath.glob(f"*_{scenario}.md")):
            fm, _ = parse_md(path)
            if fm.get("scenario") != scenario:
                continue
            fslug = fm.get("slug", path.stem)
            loc = fm.get("localisation") or {}
            rattache = fslug in sources or loc.get("zone") == slug
            if not rattache:
                continue
            parts = [str(fm.get(c, "")).strip() for c in champs]
            text = " ".join(p for p in parts if p)
            if text:
                blocks.append(f"[{ftype.upper()}: {fslug}]\n{text}")

    scan(INSTANCES_DIR, "instance",
         ["description_journalistique", "role_dans_scenario", "tensions_narratives"])
    scan(EVENT_INSTANCES_DIR, "evenement",
         ["description", "consequences", "realisation"])
    return blocks


# ---------------------------------------------------------------------------
# Appel LLM
# ---------------------------------------------------------------------------

ENRICH_SYSTEM = """Tu travailles sur Ourrassol 2098, simulateur de presse fictive \
située en 2098. On te donne la fiche d'UNE zone géopolitique déjà définie (nom, \
type, statut, description, origine_reelle) dans un scénario précis, à laquelle il \
manque deux informations : ses tensions internes et sa période de transition \
depuis le monde réel de 2026. Éventuellement, quelques extraits d'instances ou \
d'événements déjà écrits qui la mentionnent te sont fournis comme contexte -- \
utilise-les s'ils sont pertinents, ignore-les s'ils ne disent rien d'utile.

TA TÂCHE : produire UNIQUEMENT ces trois champs, cohérents avec la description \
déjà existante de la zone (ne la contredis pas, ne la réécris pas) :

- "tensions_internes" : 1-2 lignes sur les fractures internes de cette zone \
(rivalités, inégalités, groupes en conflit) -- chaîne vide si la description \
existante ne suggère vraiment aucune tension plausible.
- "periode_transition" : période approximative (ex: "2031-2045") indiquant quand \
cette zone a pris sa forme actuelle par rapport au monde réel de 2026 -- \
estimation plausible cohérente avec la description fournie et le contexte du \
scénario.
- "evenement_transition" : slug d'un événement du contexte fourni si l'un d'eux \
documente explicitement cette transition, sinon null. N'invente jamais un slug \
qui n'est pas dans le contexte fourni.

Réponds UNIQUEMENT avec un objet JSON, sans aucun texte autour :
{
  "tensions_internes": "...",
  "periode_transition": "...",
  "evenement_transition": null
}"""


def call_llm_json(system, user_content, max_tokens=ENRICH_MAX_TOKENS):
    text = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.2,
        task_tier="structured_strict",
    ).strip()

    if not text:
        raise RuntimeError("Réponse LLM vide.")

    candidate = re.sub(r"^```(?:json)?\s*", "", text)
    candidate = re.sub(r"\s*```$", "", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    matches = re.findall(r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}", text)
    if matches:
        try:
            return json.loads(matches[-1])
        except json.JSONDecodeError:
            pass

    raise RuntimeError(f"Aucun JSON exploitable trouvé : {text[:300]!r}")


def enrich_one_zone(scenario, zone, dry_run=True, verbose=True):
    slug = zone.get("slug")
    contexte_blocks = gather_zone_context_texts(scenario, zone)
    contexte_txt = "\n\n".join(contexte_blocks) if contexte_blocks else "(aucun texte narratif existant ne mentionne cette zone pour l'instant)"

    origine_txt = ", ".join(
        f"{o.get('entite')}" + (f" ({o['portion']})" if o.get("portion") else "")
        for o in (zone.get("origine_reelle") or [])
    )

    user_content = f"""Scénario : {scenario}

Zone à compléter :
- slug : {slug}
- nom : {zone.get('nom')}
- type : {zone.get('type')}
- statut : {zone.get('statut')}
- origine_reelle : {origine_txt or '(aucune)'}
- description : {zone.get('description') or '(vide)'}

Contexte narratif disponible :
{contexte_txt}"""

    if verbose:
        print(f"\n--- {slug} ---")
        print(f"  Contexte : {len(contexte_blocks)} bloc(s) narratif(s) trouvé(s)")

    result = call_llm_json(ENRICH_SYSTEM, user_content)

    tensions = str(result.get("tensions_internes") or "").strip()
    periode = result.get("periode_transition") or None
    evenement = result.get("evenement_transition") or None

    if verbose:
        print(f"  tensions_internes  : {tensions or '(vide)'}")
        print(f"  periode_transition : {periode or '(vide)'}")
        print(f"  evenement_transition : {evenement or 'null'}")

    if not dry_run:
        zone["tensions_internes"] = tensions
        zone["periode_transition"] = periode
        zone["evenement_transition"] = evenement

    return {"slug": slug, "tensions_internes": tensions,
            "periode_transition": periode, "evenement_transition": evenement}


# ---------------------------------------------------------------------------
# Écriture
# ---------------------------------------------------------------------------

def write_geo_file(scenario, fm, body, raw_avant):
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    bak = path.with_suffix(path.suffix + ".bak")
    bak.write_text(raw_avant, encoding="utf-8")

    new_fm = yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    path.write_text("---\n" + new_fm + "---" + body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Complète tensions_internes/periode_transition/evenement_transition "
                     "d'une ou plusieurs zones existantes qui ont ces champs vides "
                     "(typiquement issues d'un split via l'onglet Carte)."
    )
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slug", help="Une seule zone, par son slug")
    group.add_argument("--tous-manquants", action="store_true",
                        help="Toutes les zones du scénario avec tensions_internes ou "
                             "periode_transition vide")
    parser.add_argument("--force", action="store_true",
                         help="Écrit réellement (avec backup .bak). Sans cette option, "
                              "affiche seulement ce qui serait généré.")
    parser.add_argument("--json", action="store_true",
                         help="Sortie JSON sur stdout (dernière ligne), pour appel depuis "
                              "gui/app.py en sous-processus. Implique --slug (une seule zone), "
                              "ignore --force -- ce mode ne génère qu'une PROPOSITION, l'écriture "
                              "réelle se fait via /api/carte/appliquer_enrichissement_zone.")
    args = parser.parse_args()

    if args.json and not args.slug:
        print(json.dumps({"ok": False, "error": "--json requiert --slug (une seule zone à la fois)"}))
        sys.exit(1)

    fm, body, raw = load_geo_file(args.scenario)
    if fm is None:
        if args.json:
            print(json.dumps({"ok": False, "error": f"geographie/{args.scenario}.md introuvable ou mal formé"}))
            sys.exit(1)
        sys.exit(f"geographie/{args.scenario}.md introuvable ou mal formé.")

    zones = fm.get("zones") or []
    by_slug = {z.get("slug"): z for z in zones if isinstance(z, dict) and z.get("slug")}

    if args.json:
        zone = by_slug.get(args.slug)
        if not zone:
            print(json.dumps({"ok": False, "error": f"Zone '{args.slug}' introuvable dans geographie/{args.scenario}.md"}))
            sys.exit(1)
        try:
            r = enrich_one_zone(args.scenario, zone, dry_run=True, verbose=False)
            print(json.dumps({"ok": True, "proposition": r}))
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e)}))
            sys.exit(1)
        return

    if args.slug:
        zone = by_slug.get(args.slug)
        if not zone:
            sys.exit(f"Zone '{args.slug}' introuvable dans geographie/{args.scenario}.md")
        cibles = [zone]
    else:
        cibles = [z for z in zones if isinstance(z, dict) and zone_a_completer(z)]
        if not cibles:
            print("Aucune zone avec un champ manquant dans ce scénario.")
            return

    print(f"{'[DRY-RUN] ' if not args.force else ''}{len(cibles)} zone(s) à traiter dans {args.scenario}.")

    resultats = []
    for zone in cibles:
        try:
            r = enrich_one_zone(args.scenario, zone, dry_run=not args.force)
            resultats.append(r)
        except Exception as e:
            print(f"  ✗ Erreur sur '{zone.get('slug')}' : {e}")

    if args.force and resultats:
        write_geo_file(args.scenario, fm, body, raw)
        print(f"\n✓ {len(resultats)} zone(s) mise(s) à jour dans geographie/{args.scenario}.md "
              f"(backup : geographie/{args.scenario}.md.bak)")
    elif not args.force:
        print("\n[DRY-RUN] Rien n'a été écrit -- relance avec --force pour appliquer.")


if __name__ == "__main__":
    main()
