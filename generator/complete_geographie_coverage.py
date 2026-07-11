#!/usr/bin/env python3
"""
complete_geographie_coverage.py — Ourrassol 2098
=================================================

Complète la couverture géographique de toutes les fiches
geographie/{scenario}.md pour garantir que chaque pays de la
liste 2026 (zones_pays.json) a une zone 2098 d'affectation dans
chaque scénario.

PRINCIPE
--------
Pour chaque pays null dans zones_pays.json :
  1. Montrer au LLM les zones N1 existantes + leur origine_reelle
  2. Le LLM décide :
     a. "absorber" → ajouter le pays à l'origine_reelle d'une zone existante
     b. "nouvelle_zone" → créer une zone N1 si aucune zone ne convient
  3. Mettre à jour la fiche geographie/{scenario}.md
  4. Régénérer zones_pays.json

USAGE
-----
    python3 complete_geographie_coverage.py --scenario breakdown
    python3 complete_geographie_coverage.py --all
    python3 complete_geographie_coverage.py --all --dry-run

PRÉREQUIS
---------
- zones_pays.json dans gui/ (généré par generate_zones_pays.py)
- geographie/{scenario}.md existant pour chaque scénario
- Passe par llm_client.py (tier "structured_strict") — voir TASK_TIER_DEFAULTS
  dans llm_client.py pour le modèle utilisé par défaut. LLM_PROVIDER/LLM_MODEL
  restent disponibles en override manuel total si besoin d'un test ponctuel.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

SCRIPT_DIR   = Path(__file__).parent
VAULT_ROOT   = SCRIPT_DIR.parent
GEO_DIR      = VAULT_ROOT / "geographie"
GUI_DIR      = VAULT_ROOT / "gui"
ZONES_PAYS   = GUI_DIR / "zones_pays.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference"
]

ZONE_TYPES = [
    "bloc_continental", "union_regionale", "territoire_autonome",
    "territoire_herite", "region", "ville", "infrastructure",
    "site_strategique", "zone_sinistree", "autre"
]
ZONE_STATUTS = ["dominant", "stable", "fragmenté", "en_declin", "disparu", "emergent"]
TYPE_ENTITE_REELLE = ["pays", "etat_federe", "province", "region_administrative", "autre"]

# ---------------------------------------------------------------------------
# LLM client — délégué à llm_client.py (abstraction commune Ourrassol 2098)
# ---------------------------------------------------------------------------
#
# Anomalie corrigée le 11 juillet 2026 : ce script avait sa propre fonction
# call_llm() qui appelait directement les SDK des fournisseurs, en court-
# circuitant llm_client.py — ce qui le rendait invisible au routing par
# tier (TASK_TIER_DEFAULTS) et à la logique de retry sur rate limit (429).
# Migré vers l'abstraction commune, tier "structured_strict" : ce script
# décide de l'affectation canonique des pays aux zones géographiques,
# référencée ensuite dans tout le vault.

from llm_client import call_llm as _call_llm

TASK_TIER = "structured_strict"


def call_llm(system_prompt, user_prompt, max_tokens=8000):
    return _call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=0.0,
        task_tier=TASK_TIER,
    )

# ---------------------------------------------------------------------------
# Lecture / écriture fiche géographie
# ---------------------------------------------------------------------------

def load_geo_file(scenario):
    path = GEO_DIR / f"{scenario}.md"
    if not path.exists():
        raise FileNotFoundError(f"Fiche introuvable : {path}")
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---")
    if len(parts) < 3:
        raise ValueError(f"Format inattendu dans {path}")
    fm = yaml.safe_load(parts[1]) or {}
    body = "---".join(parts[2:])
    return fm, body, path


def save_geo_file(scenario, fm, body, dry_run):
    path = GEO_DIR / f"{scenario}.md"
    if not dry_run:
        bak = path.with_suffix(".md.bak")
        shutil.copy(path, bak)
        print(f"  → Sauvegarde : {bak.name}")

    # Un seul yaml.dump sur le frontmatter complet (zones incluses) : PyYAML aligne
    # correctement le tiret de liste et les clés de chaque mapping sous "zones:".
    # (Ancienne approche : deux dumps séparés + réindentation manuelle ligne par ligne,
    # qui cassait l'alignement car seules les lignes sans espace de tête étaient
    # réindentées — d'où des "-   slug:" à une colonne différente de "    nom:".)
    fm_ordered = {k: v for k, v in fm.items() if k != "zones"}
    fm_ordered["zones"] = fm.get("zones", [])
    fm_str = yaml.dump(
        fm_ordered, allow_unicode=True, sort_keys=False,
        default_flow_style=False, indent=2,
    ).rstrip()
    content = f"---\n{fm_str}\n---{body}"

    if dry_run:
        print(f"  [dry-run] Aurait écrit {path}")
    else:
        path.write_text(content, encoding="utf-8")
        print(f"  ✓ Écrit : {path}")


# ---------------------------------------------------------------------------
# Identification des pays manquants
# ---------------------------------------------------------------------------

def load_zones_pays():
    if not ZONES_PAYS.exists():
        print(f"  ✗ {ZONES_PAYS} introuvable — génère-le d'abord.")
        sys.exit(1)
    return json.loads(ZONES_PAYS.read_text(encoding="utf-8"))


def get_missing_pays(zones_pays, scenario):
    """Retourne la liste des pays sans zone dans ce scénario.
    Se base sur pays_liste (liste complète, à jour) plutôt que sur les seules
    clés déjà présentes dans le dict du scénario : un pays ajouté à pays_liste
    par merge_pays_monde.py mais jamais écrit dans le dict d'un scénario donné
    (absent en tant que clé, pas seulement à null) doit aussi être détecté
    comme manquant — sinon il reste invisible pour ce script indéfiniment."""
    pays_liste = zones_pays.get("pays_liste", [])
    sc_data = zones_pays.get(scenario, {})
    return [pays for pays in pays_liste if sc_data.get(pays) is None]


# ---------------------------------------------------------------------------
# Prompt LLM
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Tu es un cartographe d'un monde fictif en 2098. Tu dois rattacher des pays du monde \
actuel (2026) à des zones géopolitiques de 2098 dans un scénario donné.

Pour chaque pays sans zone, tu as deux options :
1. "absorber" : le pays est intégré à une zone N1 existante (ajouter à son origine_reelle).
   Utilise cette option si une zone existante couvre géographiquement ou politiquement ce territoire.
2. "nouvelle_zone" : créer une nouvelle zone N1 si vraiment aucune zone existante ne convient.
   N'utilise cette option qu'en dernier recours.

Réponds UNIQUEMENT en JSON valide, sans markdown, sans commentaires.
Format exact :
{
  "affectations": [
    {
      "pays": "Allemagne",
      "action": "absorber",
      "zone_slug": "slug_zone_existante",
      "justification": "courte justification"
    },
    {
      "pays": "Islande",
      "action": "nouvelle_zone",
      "justification": "courte justification",
      "zone": {
        "slug": "islande_arctique_nord",
        "nom": "Islande (Forteresse Arctique)",
        "niveau": 1,
        "type": "territoire_autonome",
        "parent": null,
        "statut": "emergent",
        "description": "Description narrative en 2-3 phrases.",
        "tensions_internes": "Tensions principales.",
        "periode_transition": "2045-2080",
        "evenement_transition": null,
        "lieux_emblematiques": [],
        "relations": {"allies": [], "rivaux": []},
        "sources_attestees": [],
        "origine_reelle": [
          {"entite": "Islande", "type_entite": "pays", "portion": null}
        ]
      }
    }
  ]
}

Types de zone valides : bloc_continental, union_regionale, territoire_autonome, territoire_herite, region, ville, infrastructure, site_strategique, zone_sinistree, autre
Statuts valides : dominant, stable, fragmenté, en_declin, disparu, emergent
type_entite valides : pays, etat_federe, province, region_administrative, autre"""


def build_user_prompt(scenario, missing_pays, existing_zones):
    zones_summary = []
    for z in existing_zones:
        if z.get("niveau") != 1:
            continue
        origine = z.get("origine_reelle") or []
        pays_list = [o.get("entite", "") for o in origine if isinstance(o, dict)]
        desc = z.get("description", "")
        # Tronquer la description à 120 chars pour garder le prompt compact
        desc_short = (desc[:120] + "…") if len(desc) > 120 else desc
        zones_summary.append(
            f"  - slug: {z['slug']}\n"
            f"    nom: {z.get('nom', '')}\n"
            f"    statut: {z.get('statut', '?')}\n"
            f"    couvre_actuellement: {', '.join(pays_list) if pays_list else '(non spécifié)'}\n"
            f"    logique_narrative: {desc_short}"
        )

    return f"""SCÉNARIO : {scenario}

ZONES N1 EXISTANTES ({len(zones_summary)}) — avec leur logique narrative :
{chr(10).join(zones_summary)}

PAYS SANS ZONE À AFFECTER ({len(missing_pays)}) :
{', '.join(missing_pays)}

CONSIGNE : Pour chaque pays, choisis la zone N1 dont la logique narrative et la géographie
sont les plus cohérentes avec ce territoire en 2098. Ne mets jamais un pays européen dans
une zone africaine ou moyen-orientale sauf si la description de la zone le justifie
explicitement. En cas de doute, crée une nouvelle zone N1.

Pour chaque pays, décide de l'action (absorber ou nouvelle_zone) et génère le JSON demandé."""


# ---------------------------------------------------------------------------
# Parsing et validation de la réponse
# ---------------------------------------------------------------------------

def parse_response(text):
    text = text.strip()
    # Retirer les blocs markdown si présents
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return json.loads(text)


def validate_new_zone(zone):
    issues = []
    slug = zone.get("slug", "")
    if not slug or not re.fullmatch(r"[a-z0-9_]+", slug):
        issues.append(f"slug invalide : {slug!r}")
    if not zone.get("nom"):
        issues.append("nom manquant")
    if zone.get("type") not in ZONE_TYPES:
        issues.append(f"type invalide : {zone.get('type')!r}")
    if zone.get("statut") not in ZONE_STATUTS:
        issues.append(f"statut invalide : {zone.get('statut')!r}")
    origine = zone.get("origine_reelle") or []
    if not origine:
        issues.append("origine_reelle manquante")
    for o in origine:
        if o.get("type_entite") not in TYPE_ENTITE_REELLE:
            issues.append(f"type_entite invalide : {o.get('type_entite')!r}")
    return issues


# ---------------------------------------------------------------------------
# Application des affectations
# ---------------------------------------------------------------------------

def apply_affectations(affectations, existing_zones, scenario):
    """Applique les décisions du LLM sur les zones existantes.
    Retourne (zones_modifiees, nouvelles_zones, stats)."""

    # Slugs de TOUTES les zones (tous niveaux) : sert à détecter les collisions de
    # slug lors de la création d'une nouvelle zone N1.
    existing_slugs = {z["slug"] for z in existing_zones}
    by_slug = {z["slug"]: z for z in existing_zones}
    zones_result = list(existing_zones)

    # Slugs des zones N1 UNIQUEMENT : le LLM ne voit que ces zones dans son prompt
    # (build_user_prompt filtre sur niveau==1), donc "absorber" doit être validé
    # contre ce même périmètre. Sans cette restriction, un slug halluciné qui
    # coïncide par hasard avec une sous-zone (N2/N3) existante était accepté à
    # tort — le pays se retrouvait alors absorbé dans une sous-zone invisible
    # sur la carte (pas de couleur/légende dédiée, cf. bug légendes incohérentes).
    n1_slugs = {z["slug"] for z in existing_zones if z.get("niveau") == 1}

    stats = {"absorbés": 0, "nouvelles_zones": 0, "rejetés": 0}
    resolved_pays = []

    for aff in affectations:
        pays = aff.get("pays", "?")
        action = aff.get("action", "")

        if action == "absorber":
            target_slug = aff.get("zone_slug", "")
            if target_slug not in n1_slugs:
                print(f"  ⚠ Absorber '{pays}' → slug inconnu ou hors-N1 '{target_slug}' — ignoré")
                stats["rejetés"] += 1
                continue

            zone = by_slug[target_slug]
            origine = zone.get("origine_reelle") or []
            # Vérifier si pas déjà présent
            existing_entites = {o.get("entite", "").lower() for o in origine}
            if pays.lower() not in existing_entites:
                origine.append({"entite": pays, "type_entite": "pays", "portion": None})
                zone["origine_reelle"] = origine
                print(f"  ✓ Absorbé : {pays} → {target_slug}")
            else:
                print(f"  ~ Déjà présent : {pays} dans {target_slug}")
            stats["absorbés"] += 1
            resolved_pays.append(pays)

        elif action == "nouvelle_zone":
            zone_data = aff.get("zone")
            if not zone_data:
                print(f"  ⚠ Nouvelle zone pour '{pays}' : données manquantes — ignoré")
                stats["rejetés"] += 1
                continue

            # Assurer les champs obligatoires
            zone_data.setdefault("niveau", 1)
            zone_data.setdefault("parent", None)
            zone_data.setdefault("lieux_emblematiques", [])
            zone_data.setdefault("relations", {"allies": [], "rivaux": []})
            zone_data.setdefault("sources_attestees", [])
            zone_data.setdefault("evenement_transition", None)

            issues = validate_new_zone(zone_data)
            if issues:
                print(f"  ⚠ Zone rejetée pour '{pays}' : {'; '.join(issues)}")
                stats["rejetés"] += 1
                continue

            slug = zone_data["slug"]
            if slug in existing_slugs:
                print(f"  ⚠ Slug '{slug}' déjà existant — ignoré")
                stats["rejetés"] += 1
                continue

            zones_result.append(zone_data)
            existing_slugs.add(slug)
            by_slug[slug] = zone_data
            if zone_data.get("niveau") == 1:
                n1_slugs.add(slug)
            print(f"  ✓ Nouvelle zone N1 : {slug} ({zone_data.get('nom')})")
            stats["nouvelles_zones"] += 1
            resolved_pays.append(pays)

        else:
            print(f"  ⚠ Action inconnue '{action}' pour '{pays}' — ignoré")
            stats["rejetés"] += 1

    return zones_result, resolved_pays, stats


# ---------------------------------------------------------------------------
# Régénération zones_pays.json
# ---------------------------------------------------------------------------

def update_zones_pays(zones_pays, scenario, resolved_pays, existing_zones):
    """Met à jour zones_pays.json pour les pays résolus."""
    by_slug = {z["slug"]: z for z in existing_zones}

    def normalise(s):
        s = s.lower().strip()
        remap = {
            "états-unis d'amérique": "états-unis",
            "russie (sibérie orientale)": "russie",
        }
        return remap.get(s, s)

    # Reconstruire l'index origine_reelle
    index = {}
    for z in existing_zones:
        slug = z.get("slug", "")
        origine = z.get("origine_reelle") or []
        for o in origine:
            n = normalise(o.get("entite", ""))
            if n and n not in index:
                index[n] = slug

    for pays in resolved_pays:
        n = normalise(pays)
        zone = index.get(n)
        if zone:
            zones_pays[scenario][pays] = zone
            print(f"    zones_pays.json : {pays} → {zone}")

    return zones_pays


# ---------------------------------------------------------------------------
# Traitement d'un scénario
# ---------------------------------------------------------------------------

BATCH_SIZE = 12  # Pays par appel LLM

# P13 (11 juillet 2026) : le délai fixe préventif de 8s entre batches (fix
# historique du bug #8) a été retiré — llm_client.py gère désormais le rate
# limiting de façon purement réactive (retry sur 429 uniquement), comme pour
# tous les autres scripts du pipeline. Un compte au palier large (ex. Scale)
# n'est donc plus ralenti artificiellement ici.


def process_scenario(scenario, zones_pays, dry_run):
    print(f"\n=== {scenario} ===")

    missing = get_missing_pays(zones_pays, scenario)
    if not missing:
        print(f"  ✓ Tous les pays ont une zone — rien à faire")
        return zones_pays

    print(f"  {len(missing)} pays sans zone : {', '.join(missing)}")

    fm, body, path = load_geo_file(scenario)
    existing_zones = list(fm.get("zones") or [])

    # Traitement par batch
    all_resolved = []
    total_stats = {"absorbés": 0, "nouvelles_zones": 0, "rejetés": 0}
    batches = [missing[i:i+BATCH_SIZE] for i in range(0, len(missing), BATCH_SIZE)]

    for batch_idx, batch in enumerate(batches):
        done = batch_idx * BATCH_SIZE
        total = len(missing)
        print(f"  Batch {batch_idx+1}/{len(batches)} [{done}/{total}] : {', '.join(batch)}")

        user_prompt = build_user_prompt(scenario, batch, existing_zones)

        try:
            text = call_llm(SYSTEM_PROMPT, user_prompt)
            parsed = parse_response(text)
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON invalide batch {batch_idx+1} : {e}")
            print(f"  Réponse brute : {text[:200]}")
            continue
        except Exception as e:
            print(f"  ✗ Erreur batch {batch_idx+1} : {e}")
            continue

        affectations = parsed.get("affectations", [])
        if not affectations:
            print(f"  ✗ Aucune affectation dans la réponse")
            continue

        updated_zones, resolved_pays, stats = apply_affectations(
            affectations, existing_zones, scenario
        )

        # Les zones mises à jour deviennent le contexte des batches suivants
        existing_zones = updated_zones
        all_resolved.extend(resolved_pays)

        for k in total_stats:
            total_stats[k] += stats[k]

        done_now = done + len(batch)
        print(f"  [{done_now}/{total}] {stats['absorbés']} absorbés, "
              f"{stats['nouvelles_zones']} nouvelles zones, "
              f"{stats['rejetés']} rejetés")

    print(f"  Total : {total_stats['absorbés']} absorbés, "
          f"{total_stats['nouvelles_zones']} nouvelles zones, "
          f"{total_stats['rejetés']} rejetés")

    if not dry_run and all_resolved:
        fm["zones"] = existing_zones
        save_geo_file(scenario, fm, body, dry_run=False)
        zones_pays = update_zones_pays(zones_pays, scenario, all_resolved, existing_zones)
    elif dry_run:
        print(f"  [dry-run] Aurait modifié {scenario}.md et zones_pays.json")

    return zones_pays



# ---------------------------------------------------------------------------
# Mode revue : génère un fichier YAML de propositions à valider manuellement
# ---------------------------------------------------------------------------

def process_scenario_review(scenario, zones_pays):
    """Génère coverage_proposals_{scenario}.yaml sans écrire dans la fiche."""
    print(f"\n=== {scenario} [mode revue] ===")

    missing = get_missing_pays(zones_pays, scenario)
    if not missing:
        print(f"  ✓ Tous les pays ont une zone — rien à faire")
        return

    print(f"  {len(missing)} pays sans zone")

    fm, body, path = load_geo_file(scenario)
    existing_zones = list(fm.get("zones") or [])

    all_affectations = []
    batches = [missing[i:i+BATCH_SIZE] for i in range(0, len(missing), BATCH_SIZE)]

    for batch_idx, batch in enumerate(batches):
        done = batch_idx * BATCH_SIZE
        total = len(missing)
        print(f"  Batch {batch_idx+1}/{len(batches)} [{done}/{total}] : {', '.join(batch)}")

        user_prompt = build_user_prompt(scenario, batch, existing_zones)
        try:
            text = call_llm(SYSTEM_PROMPT, user_prompt)
            parsed = parse_response(text)
        except Exception as e:
            print(f"  ✗ Erreur batch {batch_idx+1} : {e}")
            # Ajouter les pays du batch comme non résolus
            for pays in batch:
                all_affectations.append({
                    "pays": pays,
                    "action": "a_revoir",
                    "zone_slug": None,
                    "justification": f"Erreur LLM : {e}",
                    "valide": False,
                })
            continue

        affectations = parsed.get("affectations", [])
        # Slugs déjà connus (zones existantes en niveau 1) + slugs de nouvelles
        # zones proposées PLUS TÔT dans ce même batch. Sans ce suivi, un pays
        # groupé sous une nouvelle zone proposée juste avant lui dans la même
        # réponse (ex. "nouvelle_zone: archipel_britannique_insulaire" pour
        # l'Angleterre, puis "absorber: archipel_britannique_insulaire" pour
        # l'Écosse et le Pays de Galles) était rejeté à tort — la zone
        # n'existait pas encore dans existing_zones au moment de l'appel LLM.
        n1_slugs = {z["slug"] for z in existing_zones if z.get("niveau") == 1}
        nouvelles_zones_ce_batch = set()
        for aff in affectations:
            aff["valide"] = True  # l'utilisateur peut passer à False pour rejeter
            if aff.get("action") == "nouvelle_zone":
                nz = (aff.get("zone") or {}).get("slug")
                if nz:
                    nouvelles_zones_ce_batch.add(nz)
            elif aff.get("action") == "absorber":
                target = aff.get("zone_slug")
                if target not in n1_slugs and target not in nouvelles_zones_ce_batch:
                    aff["valide"] = False
                    aff["avertissement"] = f"Slug inconnu ou hors-N1 : {target}"
            all_affectations.append(aff)

        print(f"  [{done + len(batch)}/{total}] {len(affectations)} propositions reçues")

    # Écrire le fichier de propositions
    proposals_path = SCRIPT_DIR / f"coverage_proposals_{scenario}.yaml"
    proposals = {
        "scenario": scenario,
        "instructions": (
            "Vérifiez chaque affectation. "
            "Mettez 'valide: false' pour rejeter une proposition. "
            "Pour action: absorber, vérifiez que zone_slug est cohérente. "
            "Pour action: nouvelle_zone, vérifiez les champs de la zone. "
            "Lancez ensuite : python3 complete_geographie_coverage.py --scenario "
            f"{scenario} --apply"
        ),
        "affectations": all_affectations,
    }
    proposals_path.write_text(
        yaml.dump(proposals, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8"
    )
    print(f"  ✓ Propositions écrites : {proposals_path}")
    print(f"  → Édite le fichier, puis lance --apply")


# ---------------------------------------------------------------------------
# Mode apply : applique un fichier de propositions validé manuellement
# ---------------------------------------------------------------------------

def apply_proposals(scenario, zones_pays):
    """Applique coverage_proposals_{scenario}.yaml après validation manuelle."""
    print(f"\n=== {scenario} [mode apply] ===")

    proposals_path = SCRIPT_DIR / f"coverage_proposals_{scenario}.yaml"
    if not proposals_path.exists():
        print(f"  ✗ {proposals_path.name} introuvable — lance d'abord --review")
        return zones_pays

    proposals = yaml.safe_load(proposals_path.read_text(encoding="utf-8")) or {}
    affectations = proposals.get("affectations", [])

    # Filtrer les propositions validées
    valid = [a for a in affectations if a.get("valide") is True]
    rejected = [a for a in affectations if a.get("valide") is not True]
    print(f"  {len(valid)} propositions valides, {len(rejected)} rejetées")

    if not valid:
        print(f"  ✗ Aucune proposition valide — rien à appliquer")
        return zones_pays

    fm, body, path = load_geo_file(scenario)
    existing_zones = list(fm.get("zones") or [])

    updated_zones, resolved_pays, stats = apply_affectations(
        valid, existing_zones, scenario
    )

    print(f"  Stats : {stats['absorbés']} absorbés, "
          f"{stats['nouvelles_zones']} nouvelles zones, "
          f"{stats['rejetés']} rejetés")

    if resolved_pays:
        fm["zones"] = updated_zones
        save_geo_file(scenario, fm, body, dry_run=False)
        zones_pays = update_zones_pays(zones_pays, scenario, resolved_pays, updated_zones)

        # Archiver le fichier de propositions
        archive_path = proposals_path.with_suffix(".applied.yaml")
        proposals_path.rename(archive_path)
        print(f"  → Propositions archivées : {archive_path.name}")

    return zones_pays


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Complète la couverture géographique pour tous les pays 2026"
    )
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--scenario", choices=SCENARIOS, help="Scénario à traiter")
    grp.add_argument("--all", action="store_true", help="Traiter tous les scénarios")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simuler sans écrire")
    parser.add_argument("--review", action="store_true",
                        help="Générer coverage_proposals_{scenario}.yaml pour revue manuelle (sans écrire)")
    parser.add_argument("--apply", action="store_true",
                        help="Appliquer coverage_proposals_{scenario}.yaml déjà validé")
    args = parser.parse_args()

    scenarios = SCENARIOS if args.all else [args.scenario]

    print("=" * 60)
    print("  OURRASSOL 2098 — Couverture géographique complète")
    print("=" * 60)

    zones_pays = load_zones_pays()

    for scenario in scenarios:
        if args.apply:
            zones_pays = apply_proposals(scenario, zones_pays)
        elif args.review:
            process_scenario_review(scenario, zones_pays)
        else:
            zones_pays = process_scenario(scenario, zones_pays, args.dry_run)

    # Sauvegarder zones_pays.json mis à jour
    if not args.dry_run and not args.review:
        ZONES_PAYS.write_text(
            json.dumps(zones_pays, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n✓ zones_pays.json mis à jour : {ZONES_PAYS}")
    elif args.dry_run:
        print(f"\n[dry-run] zones_pays.json non modifié")
    elif args.review:
        print(f"\nPropositions générées — édite les fichiers coverage_proposals_*.yaml")
        print(f"puis lance : python3 complete_geographie_coverage.py --scenario X --apply")

    print("\n" + "=" * 60)
    print("  Terminé.")
    print("=" * 60)


if __name__ == "__main__":
    main()
