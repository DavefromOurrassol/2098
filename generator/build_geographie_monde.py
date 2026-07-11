#!/usr/bin/env python3
"""
build_geographie_monde.py — Ourrassol 2098
==============================================

Rétro-construit une "bible monde" géopolitique par scénario, à partir
du contenu narratif déjà existant dans le vault (instances, événements
custom) — sert ensuite de référentiel pour que les futures générations
(instances, signaux, événements, et le futur champ de localisation des
instances) réutilisent des zones/lieux cohérents au lieu d'en inventer
de nouveaux à chaque fois.

PROBLÈME TRAITÉ
----------------
Sans référentiel, le système dérive naturellement : un scan du vault
au 2026-06-20 a trouvé 33 variantes de blocs géopolitiques pour ~6
réalités distinctes (ex: "Bloc Eurasien", "Bloc Eurasien Central",
"Bloc Eurasiatique Occidental", "Union Eurasiatique"... sans qu'on
sache si ce sont des nuances voulues ou une dérive de cohérence).

CE QUE FAIT CE SCRIPT (one-shot par scénario, ré-exécutable)
---------------------------------------------------------------
Pour chaque scénario :
1. Rassemble le texte narratif pertinent : description_journalistique,
   role_dans_scenario, tensions_narratives de toutes les instances de
   ce scénario + description/consequences/realisation de tous les
   event_instances de ce scénario.
2. Envoie ce texte au LLM avec consigne de repérer toutes les
   zones/blocs/lieux géopolitiques mentionnés, de regrouper les
   variantes qui désignent la même réalité, et de synthétiser une
   bible structurée (zones avec statut, tensions, lieux emblématiques,
   relations, traçabilité des sources).
3. Écrit geographie/{scenario}.md (frontmatter YAML structuré + corps
   markdown éditable librement dans Obsidian).

IMPORTANT — ÉDITION MANUELLE PRÉSERVÉE
------------------------------------------
Ce script est pensé pour produire une ÉBAUCHE, pas un résultat figé.
Si geographie/{scenario}.md existe déjà :
  - sans --force : le script s'arrête et affiche un avertissement,
    pour ne JAMAIS écraser silencieusement tes modifications manuelles
  - avec --force : régénère entièrement le fichier (perd les éditions
    manuelles — une sauvegarde .bak est créée avant)

Le corps markdown sous le frontmatter, sections "## Vue d'ensemble"
et "## Notes / zones à enrichir", est un espace libre que ce script
ne lit jamais — tu peux y écrire ce que tu veux sans risque, MAIS il
sera quand même régénéré si tu relances avec --force (la sauvegarde
.bak est ton filet de sécurité dans ce cas).

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...

USAGE
-----
    python3 build_geographie_monde.py --scenario breakdown --dry-run
    python3 build_geographie_monde.py --scenario breakdown
    python3 build_geographie_monde.py --all                # les 6 scénarios
    python3 build_geographie_monde.py --scenario breakdown --force
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

from llm_client import call_llm  # tier structured_strict — référentiel géographique fixe


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_DIR = VAULT_ROOT / "instances"
EVENT_INSTANCES_DIR = VAULT_ROOT / "event_instances"
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"


SYNTHESIS_MAX_TOKENS = 8000

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

ZONE_TYPES = ["bloc_continental", "union_regionale", "territoire_autonome",
              "territoire_herite", "region", "ville", "infrastructure",
              "site_strategique", "zone_sinistree", "autre"]
ZONE_STATUTS = ["dominant", "stable", "fragmenté", "en_declin", "disparu", "emergent"]
LIEU_TYPES = ["ville", "region", "infrastructure", "site_strategique"]
TYPE_ENTITE_REELLE = ["pays", "etat_federe", "province", "region_administrative", "autre"]


# ---------------------------------------------------------------------------
# Lecture du vault
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


def gather_instance_texts(scenario):
    """Rassemble le texte narratif pertinent de toutes les instances
    d'un scénario. Retourne une liste de blocs texte, un par instance,
    avec le nom de l'instance en tête pour permettre au LLM de citer
    sa source dans 'sources_attestees'."""
    blocks = []
    if not INSTANCES_DIR.exists():
        return blocks
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, _ = parse_md(path)
        if fm.get("type") != "instance" or fm.get("scenario") != scenario:
            continue
        slug = fm.get("slug", path.stem)
        parts = [
            fm.get("description_journalistique", ""),
            fm.get("role_dans_scenario", ""),
            fm.get("tensions_narratives", ""),
        ]
        text = " ".join(str(p).strip() for p in parts if p)
        if text:
            blocks.append(f"[INSTANCE: {slug}]\n{text}")
    return blocks


def gather_event_texts(scenario):
    """Idem pour les event_instances du scénario."""
    blocks = []
    if not EVENT_INSTANCES_DIR.exists():
        return blocks
    for path in sorted(EVENT_INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, _ = parse_md(path)
        if fm.get("scenario") != scenario:
            continue
        slug = fm.get("slug", path.stem)
        parts = [
            fm.get("description", ""),
            fm.get("consequences", ""),
            fm.get("realisation", ""),
        ]
        text = " ".join(str(p).strip() for p in parts if p)
        if text:
            blocks.append(f"[EVENEMENT: {slug}]\n{text}")
    return blocks


# ---------------------------------------------------------------------------
# Appel LLM
# ---------------------------------------------------------------------------

def get_client():
    """Conservé pour compatibilité — retourne None, call_claude_json n'en a plus besoin."""
    return None


def call_claude_json(client, system, user_content, max_tokens=SYNTHESIS_MAX_TOKENS):
    text = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
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

    # Bug corrigé le 11 juillet 2026 (même correctif que
    # create_entities_and_instances.py) : reliquat `resp.stop_reason`
    # d'avant la migration vers llm_client.py — call_llm() ne retourne
    # qu'une string, `resp` n'existe plus.
    likely_truncated = len(text) >= max_tokens * 3  # ~3-4 car/token en français
    if likely_truncated:
        raise RuntimeError(
            f"Réponse LLM probablement tronquée (max_tokens={max_tokens}, "
            f"{len(text)} caractères reçus, aucun JSON complet trouvé) — "
            f"texte reçu: {text[:300]!r}"
        )
    raise RuntimeError(f"Aucun JSON exploitable trouvé : {text[:300]!r}")


SYNTHESIS_SYSTEM = """Tu travailles sur Ourrassol 2098, simulateur de presse fictive \
située en 2098. On te donne un corpus de textes narratifs déjà écrits pour UN scénario \
précis du monde (descriptions d'instances, événements). Ces textes mentionnent des \
zones géopolitiques, blocs, régions, villes — parfois sous des formulations légèrement \
différentes pour désigner la même réalité (ex: "Bloc Eurasien" et "Bloc Eurasien \
Central" peuvent être la même chose vue depuis deux fiches différentes, ou deux \
réalités voisines mais distinctes — à toi de juger selon le contexte).

TA TÂCHE : produire une synthèse géopolitique cohérente de ce scénario — une "bible \
monde" qui deviendra LA référence pour toutes les générations futures de ce scénario.

1. Identifie les zones géopolitiques majeures (blocs continentaux, unions régionales, \
territoires autonomes, zones sinistrées...) réellement mentionnées ou clairement \
impliquées dans le corpus. Ne sur-fragmente pas : regroupe les variantes qui désignent \
la même réalité sous UN nom canonique. Vise un nombre raisonnable de zones (5 à 10 \
selon la richesse du corpus) plutôt qu'une liste exhaustive de chaque micro-mention.

2. Pour chaque zone, indique honnêtement quelles instances/événements du corpus la \
mentionnent ou l'impliquent clairement (sources_attestees) — n'invente pas de source, \
liste seulement les slugs [INSTANCE: ...] ou [EVENEMENT: ...] réellement présents dans \
le texte qui te justifient cette zone.

3. Si le corpus est pauvre ou ne mentionne presque aucune géographie nommée (cas \
plausible pour un scénario localiste/bioterritorial), ne force RIEN : retourne une \
liste de zones courte, voire vide, plutôt que d'inventer une géopolitique qui n'est pas \
dans le texte. C'est un résultat acceptable et honnête.

4. RÈGLE STRICTE pour "relations" (allies/rivaux) : ces champs ne doivent contenir QUE \
des "slug" d'AUTRES ZONES de cette même liste "zones" que tu es en train de produire — \
jamais un slug d'instance (qui se termine typiquement par _nomDuScenario), jamais un nom \
de faction/institution/concept qui n'est pas lui-même une des zones de ta liste. Si une \
zone n'a pas de vrai allié ou rival parmi les AUTRES ZONES que tu identifies, laisse le \
champ en liste vide plutôt que d'y mettre autre chose qu'un slug de zone valide.

5. "origine_reelle" : pour CHAQUE zone, indique de quel(s) pays ou subdivision(s) \
administrative(s) RÉELLE(S) ACTUELLE(S) (2026) elle hérite ou descend — un pays peut être \
scindé entre plusieurs zones fictives, et une zone fictive peut fusionner plusieurs pays \
réels. Utilise des noms réels précis (pays, états fédérés, provinces, länder, etc. — \
celui qui est le plus pertinent selon le contexte). Ce champ est TOUJOURS renseigné, \
même de façon large/approximative — toute géographie fictive de ce monde descend \
forcément de quelque chose du monde réel de 2026, même après effondrement ou \
recomposition radicale.

6. "periode_transition" : indique, sous forme de période approximative (ex: "2031-2045"), \
QUAND cette zone a pris sa forme/son statut actuel par rapport au monde de 2026 — fondé \
sur les `evenement_cle` et dates déjà présentes dans le corpus si elles existent, sinon \
une estimation plausible cohérente avec la trajectoire générale du scénario. \
"evenement_transition" : si un événement du corpus (préfixé [EVENEMENT: ...]) documente \
explicitement cette transition, indique son slug ; sinon laisse null — n'invente jamais \
un slug d'événement qui n'existe pas dans le corpus fourni.

7. Cette synthèse reste à PLAT pour l'instant : "niveau" vaut TOUJOURS 1 et "parent" \
vaut TOUJOURS null pour toutes les zones de cette passe. Le maillage hiérarchique en \
sous-zones (territoires, régions, villes en tant que zones à part entière reliées par \
parent) sera construit dans une étape ultérieure séparée — ne l'anticipe pas ici.

Réponds UNIQUEMENT avec un objet JSON, sans aucun texte autour :
{
  "vue_ensemble": "1 paragraphe synthétisant la configuration géopolitique globale de ce scénario, fondé sur ce que le corpus révèle réellement",
  "zones": [
    {
      "slug": "slug_snake_case",
      "nom": "Nom canonique de la zone",
      "niveau": 1,
      "type": "une valeur parmi: bloc_continental, union_regionale, territoire_autonome, territoire_herite, region, ville, infrastructure, site_strategique, zone_sinistree, autre",
      "parent": null,
      "origine_reelle": [
        {"entite": "Nom du pays ou de la subdivision réelle", "type_entite": "pays|etat_federe|province|region_administrative|autre", "portion": null}
      ],
      "description": "2-3 lignes sur ce qu'est cette zone DANS ce scénario précis",
      "statut": "une valeur parmi: dominant, stable, fragmenté, en_declin, disparu, emergent",
      "tensions_internes": "1-2 lignes sur les fractures internes, ou chaîne vide si non pertinent",
      "periode_transition": "période approximative, ex: 2031-2045",
      "evenement_transition": null,
      "lieux_emblematiques": [
        {"nom": "Nom du lieu", "type": "ville|region|infrastructure|site_strategique", "notes": "courte note de contexte"}
      ],
      "relations": {"allies": ["slug_autre_zone_de_cette_liste"], "rivaux": ["slug_autre_zone_de_cette_liste"]},
      "sources_attestees": ["slug_instance_ou_evenement_1", "slug_instance_ou_evenement_2"]
    }
  ]
}"""


def synthesize_geographie(client, scenario, corpus_text):
    user_content = f"""Scénario : {scenario}

Corpus narratif ({len(corpus_text)} caractères) :

{corpus_text}"""
    return call_claude_json(client, SYNTHESIS_SYSTEM, user_content)


# ---------------------------------------------------------------------------
# Écriture du fichier
# ---------------------------------------------------------------------------

def validate_zone(zone):
    issues = []
    if not zone.get("slug") or not re.fullmatch(r"[a-z0-9_]+", zone["slug"]):
        issues.append(f"slug invalide : {zone.get('slug')!r}")
    if not zone.get("nom"):
        issues.append("nom manquant")
    if zone.get("type") not in ZONE_TYPES:
        issues.append(f"type invalide : {zone.get('type')!r}")
    if zone.get("statut") not in ZONE_STATUTS:
        issues.append(f"statut invalide : {zone.get('statut')!r}")
    origine = zone.get("origine_reelle") or []
    if not origine:
        issues.append("origine_reelle manquante (toujours requise, voir consigne)")
    else:
        for o in origine:
            if not o.get("entite"):
                issues.append("origine_reelle : 'entite' manquante sur une entrée")
            if o.get("type_entite") not in TYPE_ENTITE_REELLE:
                issues.append(f"origine_reelle : type_entite invalide : {o.get('type_entite')!r}")
    return issues


def clean_zone_relations(zones):
    """Filtre silencieusement, dans allies/rivaux de chaque zone, toute
    entrée qui ne correspond pas au slug d'une AUTRE zone de ce même
    batch — filet de sécurité si le LLM référence un slug d'instance
    ou un concept inventé plutôt qu'une vraie zone. Retourne la liste
    nettoyée et la liste des entrées filtrées pour log."""
    all_slugs = {z.get("slug") for z in zones if z.get("slug")}
    dropped = []
    for zone in zones:
        own_slug = zone.get("slug")
        rel = zone.get("relations") or {}
        for field in ("allies", "rivaux"):
            items = rel.get(field) or []
            kept = []
            for item in items:
                item_clean = str(item).strip()
                if item_clean in all_slugs and item_clean != own_slug:
                    kept.append(item_clean)
                else:
                    dropped.append((own_slug, field, item_clean))
            rel[field] = kept
        zone["relations"] = rel
    return zones, dropped


def build_geographie_md(scenario, synthesis, valid_sources):
    """valid_sources : set des slugs réellement présents dans le corpus,
    pour filtrer les sources_attestees hallucinées plutôt que de les
    garder telles quelles."""
    zones = synthesis.get("zones", [])
    vue_ensemble = synthesis.get("vue_ensemble", "")

    zones, dropped_relations = clean_zone_relations(zones)
    if dropped_relations:
        for zslug, field, value in dropped_relations:
            print(f"  ⚠ {field} filtrée sur '{zslug}' (pas une zone de ce scénario) : "
                  f"'{value}'")

    clean_zones = []
    for zone in zones:
        issues = validate_zone(zone)
        if issues:
            print(f"  ⚠ Zone rejetée ({zone.get('nom', '?')}) : {', '.join(issues)}")
            continue
        sources = [s for s in zone.get("sources_attestees", []) if s in valid_sources]
        zone["sources_attestees"] = sources
        evt_transition = zone.get("evenement_transition")
        if evt_transition and evt_transition not in valid_sources:
            print(f"  ⚠ evenement_transition filtré sur '{zone['slug']}' "
                  f"(pas une source du corpus) : '{evt_transition}'")
            zone["evenement_transition"] = None
        # Étape 1 (à plat) : on force niveau=1 et parent=null quoi que le LLM
        # ait pu renvoyer, conformément à la consigne — sécurité mécanique
        # en plus de la consigne textuelle.
        zone["niveau"] = 1
        zone["parent"] = None
        clean_zones.append(zone)

    zones_yaml = yaml.dump(clean_zones, allow_unicode=True, sort_keys=False,
                            default_flow_style=False, width=100)
    zones_yaml_indented = "\n".join(
        ("  " + line if line.strip() else line) for line in zones_yaml.splitlines()
    )

    zones_md = ""
    for zone in clean_zones:
        zones_md += f"\n### {zone['nom']}\n\n"
        zones_md += f"*{zone['type']} — statut : {zone['statut']}*\n\n"
        origine = zone.get("origine_reelle") or []
        if origine:
            parts = []
            for o in origine:
                p = o.get("entite", "?")
                if o.get("portion"):
                    p += f" ({o['portion']})"
                parts.append(p)
            zones_md += f"**Origine réelle (2026)** : {', '.join(parts)}\n\n"
        if zone.get("periode_transition"):
            evt = zone.get("evenement_transition")
            evt_txt = f" — voir [[{evt}]]" if evt else ""
            zones_md += f"**Transition** : {zone['periode_transition']}{evt_txt}\n\n"
        zones_md += f"{zone.get('description', '')}\n\n"
        if zone.get("tensions_internes"):
            zones_md += f"**Tensions internes** : {zone['tensions_internes']}\n\n"
        lieux = zone.get("lieux_emblematiques", [])
        if lieux:
            zones_md += "**Lieux emblématiques** :\n"
            for lieu in lieux:
                note = f" — {lieu.get('notes', '')}" if lieu.get("notes") else ""
                zones_md += f"- {lieu.get('nom', '?')} ({lieu.get('type', '')}){note}\n"
            zones_md += "\n"
        rel = zone.get("relations", {}) or {}
        if rel.get("allies"):
            zones_md += f"**Alliés** : {', '.join(rel['allies'])}\n\n"
        if rel.get("rivaux"):
            zones_md += f"**Rivaux** : {', '.join(rel['rivaux'])}\n\n"
        if zone.get("sources_attestees"):
            zones_md += f"*Sources attestées : {', '.join(zone['sources_attestees'])}*\n"

    content = f"""---
scenario: {scenario}
type: geographie_monde
date_creation: {datetime.now().strftime("%Y-%m-%d")}
date_derniere_maj: {datetime.now().strftime("%Y-%m-%d")}
zones:
{zones_yaml_indented.rstrip()}
---

# Géographie — {scenario}

## Vue d'ensemble
{vue_ensemble}

## Zones
{zones_md if zones_md else "_Aucune zone identifiée à partir du corpus existant — à enrichir manuellement._"}

## Notes / zones à enrichir
_Espace libre, jamais lu par les scripts — ajoute ici tes idées, brouillons, zones à
créer manuellement._
"""
    return content


def write_geographie_file(scenario, synthesis, valid_sources, dry_run, force):
    GEOGRAPHIE_DIR.mkdir(parents=True, exist_ok=True)
    path = GEOGRAPHIE_DIR / f"{scenario}.md"

    if path.exists() and not force and not dry_run:
        print(f"  ⚠ {path.name} existe déjà — utilise --force pour régénérer "
              f"(une sauvegarde .bak sera créée), ou édite-le manuellement.")
        return None

    content = build_geographie_md(scenario, synthesis, valid_sources)

    if dry_run:
        print(content)
        return None

    if path.exists() and force:
        backup_path = path.with_suffix(".md.bak")
        shutil.copy(path, backup_path)
        print(f"  → Sauvegarde créée : {backup_path.name}")

    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def process_scenario(client, scenario, dry_run, force):
    print(f"\n=== {scenario} ===")

    instance_blocks = gather_instance_texts(scenario)
    event_blocks = gather_event_texts(scenario)
    all_blocks = instance_blocks + event_blocks

    valid_sources = set()
    for block in all_blocks:
        m = re.match(r"\[(?:INSTANCE|EVENEMENT): ([a-z0-9_]+)\]", block)
        if m:
            valid_sources.add(m.group(1))

    corpus_text = "\n\n".join(all_blocks)
    print(f"  Corpus : {len(instance_blocks)} instance(s), {len(event_blocks)} "
          f"événement(s), ~{len(corpus_text)} caractères")

    if not corpus_text.strip():
        print("  Corpus vide — rien à synthétiser.")
        return

    print("  Synthèse en cours...")
    try:
        synthesis = synthesize_geographie(client, scenario, corpus_text)
    except Exception as e:
        print(f"  ✗ Erreur : {e}")
        return

    print(f"  → {len(synthesis.get('zones', []))} zone(s) identifiée(s)")
    result = write_geographie_file(scenario, synthesis, valid_sources, dry_run, force)
    if result:
        print(f"  ✓ Écrit : {result}")


def main():
    parser = argparse.ArgumentParser(
        description="Rétro-construit la bible géopolitique d'un ou plusieurs scénarios"
    )
    parser.add_argument("--scenario", choices=SCENARIOS,
                         help="Un seul scénario à traiter")
    parser.add_argument("--all", action="store_true",
                         help="Traiter les 6 scénarios")
    parser.add_argument("--dry-run", action="store_true",
                         help="Affiche le résultat sans rien écrire sur disque")
    parser.add_argument("--force", action="store_true",
                         help="Régénère même si geographie/{scenario}.md existe déjà "
                              "(sauvegarde .bak créée avant)")
    args = parser.parse_args()

    if not args.scenario and not args.all:
        sys.exit("Précise --scenario {nom} ou --all.")

    print("=" * 60)
    print("OURRASSOL 2098 — Construction géographie monde par scénario")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit)")

    client = get_client()
    targets = SCENARIOS if args.all else [args.scenario]

    for scenario in targets:
        process_scenario(client, scenario, dry_run=args.dry_run, force=args.force)

    print("\n" + "=" * 60)
    print("Terminé.")
    print("=" * 60)


if __name__ == "__main__":
    main()
