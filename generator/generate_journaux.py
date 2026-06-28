"""
generate_journaux.py
--------------------
Génère ou met à jour generator/journaux.yaml depuis les bibles géographiques
(geographie/{scenario}.md).

Pour chaque scénario × ligne éditoriale × zone, génère via API :
  - nom          : nom du journal local (ancré dans la zone)
  - ton          : posture éditoriale locale (2-3 phrases)
  - langue_style : marqueur linguistique/culturel éventuel

Structure de journaux.yaml :
  {scenario}:
    {ligne_editoriale}:          # pro_pouvoir | opposition
      _reseau:
        nom: str
        charte: str
      zones:
        {zone_slug}:
          nom: str
          ton: str
          langue_style: str

Modes :
  --scenario NOM    : traite un seul scénario
  --all             : traite les 6 scénarios
  --ligne pro_pouvoir|opposition|all : filtre la ligne éditoriale (défaut: all)
  --update          : ajoute uniquement les zones manquantes (ne réécrit pas)
  --dry-run         : affiche sans écrire

Usage :
  python3 generate_journaux.py --scenario breakdown
  python3 generate_journaux.py --all
  python3 generate_journaux.py --all --update
  python3 generate_journaux.py --scenario eco_communalism --ligne opposition
"""

import argparse
import json
import os
import re
import sys

import yaml

from llm_client import call_llm, LLM_MODEL, LLM_PROVIDER

# ---------------------------------------------------------------------------
# CHEMINS
# ---------------------------------------------------------------------------

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT    = os.path.dirname(SCRIPT_DIR)
GEOGRAPHIE_DIR = os.path.join(VAULT_ROOT, "geographie")
JOURNAUX_PATH  = os.path.join(SCRIPT_DIR, "journaux.yaml")

VALID_SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

LIGNES = ["pro_pouvoir", "opposition"]

# ---------------------------------------------------------------------------
# RÉSEAUX ÉDITORIAUX — nom et charte globale par scénario × ligne
# Ces valeurs sont fixes (définies une fois) ; seules les éditions locales
# sont générées par l'API.
# ---------------------------------------------------------------------------

RESEAUX = {
    "breakdown": {
        "pro_pouvoir": {
            "nom":    "Réseau de l'Ordre Zonal",
            "charte": (
                "Bulletins officiels des Forces de Maintien de l'Ordre. "
                "Chaque édition locale couvre sa zone de contrôle. "
                "Ton sécuritaire, justification de l'ordre imposé."
            ),
        },
        "opposition": {
            "nom":    "Réseau La Dépêche des Territoires",
            "charte": (
                "Feuilles clandestines distribuées de main en main. "
                "Chaque édition locale documente les violences et résistances de sa zone. "
                "Ton brut, factuel, épuisé mais résistant."
            ),
        },
    },
    "fortress_world": {
        "pro_pouvoir": {
            "nom":    "Réseau Le Bloc Informations",
            "charte": (
                "Organes officiels des blocs géopolitiques. "
                "Chaque édition couvre son territoire de bloc. "
                "Ton institutionnel, rhétorique de la souveraineté."
            ),
        },
        "opposition": {
            "nom":    "Réseau The Porous Border",
            "charte": (
                "Publications underground des zones grises entre blocs. "
                "Chaque édition donne voix aux exclus de son territoire. "
                "Ton incisif, investigation, témoignages directs."
            ),
        },
    },
    "new_sustainability": {
        "pro_pouvoir": {
            "nom":    "Réseau Nexus Global Review",
            "charte": (
                "Revues technocratiques régionales. "
                "Chaque édition couvre les dynamiques de transition de sa zone. "
                "Ton optimiste, analytique, confiance dans les institutions."
            ),
        },
        "opposition": {
            "nom":    "Réseau Les Irréductibles",
            "charte": (
                "Revues critiques des mouvements de résistance locaux. "
                "Chaque édition questionne les effets locaux de l'optimisation globale. "
                "Ton alerte, souverainiste, voix des laissés-pour-compte de la transition."
            ),
        },
    },
    "eco_communalism": {
        "pro_pouvoir": {
            "nom":    "Réseau La Gazette des Communs",
            "charte": (
                "Journaux des assemblées territoriales dominantes. "
                "Chaque édition ancre le modèle communaliste dans sa zone. "
                "Ton chaleureux, consensuel, sobriété comme valeur."
            ),
        },
        "opposition": {
            "nom":    "Réseau Voix des Marges",
            "charte": (
                "Bulletins des communautés exclues ou marginalisées. "
                "Chaque édition documente les inégalités et dérives de sa zone. "
                "Ton revendicatif, témoignages de première main."
            ),
        },
    },
    "policy_reform": {
        "pro_pouvoir": {
            "nom":    "Réseau Global Governance Report",
            "charte": (
                "Publications institutionnelles régionales. "
                "Chaque édition couvre la mise en œuvre des réformes dans sa zone. "
                "Ton technocratique, normatif, confiance dans la régulation."
            ),
        },
        "opposition": {
            "nom":    "Réseau La Souveraine",
            "charte": (
                "Revues souverainistes et anti-technocratie. "
                "Chaque édition dénonce la perte d'autonomie locale dans sa zone. "
                "Ton combatif, démocratique, appels à la mobilisation."
            ),
        },
    },
    "reference": {
        "pro_pouvoir": {
            "nom":    "Réseau Le Monde en Tension",
            "charte": (
                "Médias généralistes mainstream régionaux. "
                "Chaque édition couvre sa zone avec équilibre apparent. "
                "Ton factuel, experts institutionnels au premier plan."
            ),
        },
        "opposition": {
            "nom":    "Réseau Le Dessous des Cartes",
            "charte": (
                "Médias d'investigation indépendants régionaux. "
                "Chaque édition documente ce que les médias mainstream taisent dans sa zone. "
                "Ton lucide, enquêteur, sources protégées."
            ),
        },
    },
}

# ---------------------------------------------------------------------------
# LECTURE DES BIBLES GÉO
# ---------------------------------------------------------------------------

def parse_geographie(scenario):
    """
    Charge geographie/{scenario}.md et retourne la liste des zones.
    Retourne [] si le fichier est absent ou illisible.
    """
    path = os.path.join(GEOGRAPHIE_DIR, "{}.md".format(scenario))
    if not os.path.exists(path):
        print("  [WARN] geographie/{}.md introuvable — scénario ignoré.".format(scenario))
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    # Extraire le frontmatter YAML
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if not m:
        print("  [WARN] Pas de frontmatter dans geographie/{}.md".format(scenario))
        return []

    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError as e:
        print("  [WARN] YAML invalide dans geographie/{}.md : {}".format(scenario, e))
        return []

    zones_all = fm.get("zones", [])
    if not zones_all:
        print("  [WARN] Aucune zone dans geographie/{}.md".format(scenario))
        return []

    # Filtrer uniquement les zones de niveau 1
    zones = [z for z in zones_all if z.get("niveau") == 1]
    print("  {} zones N1 / {} zones totales".format(len(zones), len(zones_all)))
    return zones


# ---------------------------------------------------------------------------
# GÉNÉRATION VIA API
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Tu es l'assistant de worldbuilding du projet Ourrassol 2098 — simulateur de presse fictive en 2098.
Tu génères des profils de journaux locaux fictifs pour un réseau éditorial mondial.
Réponds UNIQUEMENT avec un JSON valide. Pas de texte avant ou après. Pas de backticks."""


def build_prompt(scenario, ligne, reseau, zones_batch):
    """
    Construit le prompt pour générer les journaux d'un lot de zones.
    """
    scenario_data = {
        "breakdown":        "Monde effondré, fragmentation des États, milices locales, pénuries.",
        "fortress_world":   "Blocs géopolitiques fermés, contrôle des ressources, surveillance.",
        "new_sustainability":"Transition écologique réussie, gouvernance IA, optimisation globale.",
        "eco_communalism":  "Territoires autonomes, sobriété énergétique, assemblées locales.",
        "policy_reform":    "Institutions mondiales renforcées, technocratie, régulation globale.",
        "reference":        "Équilibre fragile, crises récurrentes, adaptation permanente.",
    }

    items = []
    for i, z in enumerate(zones_batch):
        items.append({
            "index":       i,
            "zone_slug":   z["slug"],
            "zone_nom":    z.get("nom", z["slug"]),
            "description": (z.get("description", "")[:300] + "...") if len(z.get("description", "")) > 300 else z.get("description", ""),
            "statut":      z.get("statut", ""),
            "tensions":    (z.get("tensions_internes", "")[:200] + "...") if len(z.get("tensions_internes", "")) > 200 else z.get("tensions_internes", ""),
        })

    prompt = """Scénario : {scenario} — {scenario_desc}
Réseau éditorial : {reseau_nom}
Charte du réseau : {charte}
Ligne éditoriale : {ligne}

Pour chaque zone ci-dessous, génère le profil de l'édition locale de ce réseau.
L'édition doit être ancrée dans la réalité de la zone — son nom, son ton et son style
doivent refléter la culture, la langue, les tensions et le statut de cette zone.

Réponds avec une liste JSON :
[
  {{
    "index": 0,
    "nom": "Nom du journal local (original, ancré culturellement)",
    "ton": "2-3 phrases décrivant le ton éditorial local spécifique à cette zone",
    "langue_style": "Marqueur culturel/linguistique éventuel (ex: 'mélange portugais/yoruba', 'registre administratif mandarin', 'créole local') ou chaîne vide"
  }},
  ...
]

Zones :
{zones}""".format(
        scenario=scenario,
        scenario_desc=scenario_data.get(scenario, ""),
        reseau_nom=reseau["nom"],
        charte=reseau["charte"],
        ligne=ligne,
        zones=json.dumps(items, ensure_ascii=False, indent=2),
    )

    return prompt


def generate_journals_for_zones(scenario, ligne, reseau, zones, batch_size=5):
    """
    Génère les profils de journaux pour toutes les zones via API (par lots).
    Retourne un dict {zone_slug: {nom, ton, langue_style}}.
    """
    results = {}
    batches = [zones[i:i+batch_size] for i in range(0, len(zones), batch_size)]

    print("  → {} zones | {} lot(s) de {} | {} ({})".format(
        len(zones), len(batches), batch_size, LLM_PROVIDER, LLM_MODEL
    ))

    for i, batch in enumerate(batches):
        print("    Lot {}/{}...".format(i + 1, len(batches)))
        prompt = build_prompt(scenario, ligne, reseau, batch)

        try:
            raw = call_llm(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
            ).strip()

            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw).strip()
            data, _ = json.JSONDecoder().raw_decode(raw)

            for entry in data:
                idx = entry.get("index")
                if idx is not None and 0 <= idx < len(batch):
                    zone_slug = batch[idx]["slug"]
                    results[zone_slug] = {
                        "nom":          entry.get("nom", "Édition locale"),
                        "ton":          entry.get("ton", ""),
                        "langue_style": entry.get("langue_style", ""),
                    }
            print("    OK — {} journaux générés".format(len(data)))

        except Exception as e:
            print("    [WARN] Lot {} échoué : {}".format(i + 1, e))
            # Fallback : entrées vides pour les zones du lot
            for z in batch:
                results[z["slug"]] = {
                    "nom":          "Édition {}".format(z.get("nom", z["slug"])),
                    "ton":          "",
                    "langue_style": "",
                }

    return results


# ---------------------------------------------------------------------------
# CHARGEMENT / SAUVEGARDE journaux.yaml
# ---------------------------------------------------------------------------

def load_journaux():
    """Charge journaux.yaml. Retourne {} si absent."""
    if not os.path.exists(JOURNAUX_PATH):
        return {}
    with open(JOURNAUX_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_journaux(data, dry_run=False):
    """Sauvegarde journaux.yaml."""
    if dry_run:
        print("\n[dry-run] journaux.yaml — aperçu (500 premiers caractères) :")
        preview = yaml.dump(data, allow_unicode=True, sort_keys=False)
        print(preview[:500] + "\n...")
        return
    with open(JOURNAUX_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    print("\n[OK] journaux.yaml sauvegardé : {}".format(JOURNAUX_PATH))


# ---------------------------------------------------------------------------
# TRAITEMENT D'UN SCÉNARIO
# ---------------------------------------------------------------------------

def process_scenario(scenario, ligne_filter, journaux, update_mode, dry_run):
    """
    Génère les journaux pour un scénario.
    Modifie `journaux` en place.
    """
    print("\n=== {} ===".format(scenario.upper()))

    zones = parse_geographie(scenario)
    if not zones:
        return

    print("  {} zones trouvées dans la bible géo.".format(len(zones)))

    lignes_a_traiter = [ligne_filter] if ligne_filter != "all" else LIGNES

    for ligne in lignes_a_traiter:
        print("\n  -- Ligne : {} --".format(ligne))

        reseau = RESEAUX[scenario][ligne]

        # Structure cible dans journaux.yaml
        journaux.setdefault(scenario, {})
        journaux[scenario].setdefault(ligne, {
            "_reseau": reseau,
            "zones":   {},
        })
        # S'assurer que _reseau est à jour
        journaux[scenario][ligne]["_reseau"] = reseau
        existing_zones = journaux[scenario][ligne].get("zones", {})

        # Mode --update : filtrer les zones déjà présentes
        if update_mode:
            zones_a_generer = [z for z in zones if z["slug"] not in existing_zones]
            if not zones_a_generer:
                print("  Toutes les zones déjà présentes — rien à faire.")
                continue
            print("  Mode update : {} nouvelles zones à générer.".format(len(zones_a_generer)))
        else:
            zones_a_generer = zones

        if dry_run:
            print("  [dry-run] Générerait {} journaux pour {}/{}.".format(
                len(zones_a_generer), scenario, ligne
            ))
            continue

        # Génération via API
        nouveaux = generate_journals_for_zones(scenario, ligne, reseau, zones_a_generer)

        # Fusion
        existing_zones.update(nouveaux)
        journaux[scenario][ligne]["zones"] = existing_zones

        print("  {} journaux dans la base pour {}/{}.".format(
            len(existing_zones), scenario, ligne
        ))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Génère journaux.yaml depuis les bibles géographiques."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", metavar="NOM",
                       choices=VALID_SCENARIOS,
                       help="Traite un seul scénario.")
    group.add_argument("--all", action="store_true",
                       help="Traite les {} scénarios.".format(len(VALID_SCENARIOS)))

    parser.add_argument("--ligne",
                        choices=["pro_pouvoir", "opposition", "all"],
                        default="all",
                        help="Filtre la ligne éditoriale (défaut: all).")
    parser.add_argument("--update", action="store_true",
                        help="Ajoute uniquement les zones manquantes sans écraser.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche sans écrire.")

    return parser.parse_args()


def main():
    args = parse_args()

    scenarios = VALID_SCENARIOS if args.all else [args.scenario]

    print("=== generate_journaux.py ===")
    print("Fournisseur : {} | Modèle : {}".format(LLM_PROVIDER, LLM_MODEL))
    print("Scénarios   : {}".format(", ".join(scenarios)))
    print("Ligne       : {}".format(args.ligne))
    print("Mode        : {}{}".format(
        "update" if args.update else "complet",
        " [dry-run]" if args.dry_run else ""
    ))

    # Charger l'existant
    journaux = load_journaux()

    # Traitement
    for scenario in scenarios:
        process_scenario(
            scenario=scenario,
            ligne_filter=args.ligne,
            journaux=journaux,
            update_mode=args.update,
            dry_run=args.dry_run,
        )

    # Sauvegarde
    save_journaux(journaux, dry_run=args.dry_run)

    print("\nTerminé.")


if __name__ == "__main__":
    main()
