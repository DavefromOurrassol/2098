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
  --fill-presentation : remplit la fiche publique des journaux qui n'en ont pas
                        (presentation, ville, periodicite, fondation) — utilisée
                        par le site des revues ; ne touche à rien d'autre
  --fill-presentation --force : refait la fiche de TOUS les journaux traités
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
import shutil
import sys
from datetime import datetime

import yaml

from llm_client import call_llm, resolve_for_tier

# Tier LLM : ce script génère les noms/thématiques des journalistes qui
# seront ensuite injectés (via prompt_builder.py) dans chaque article — une
# rédaction incohérente ici se propage à tous les articles en aval.
TASK_TIER = "strict"
# Fiche publique d'un journal (site des revues) : rédaction libre, pas d'identité tierce.
TASK_TIER_PRESENTATION = "creative_souple"
CHAMPS_FICHE = ("presentation", "ville", "periodicite", "fondation")
PERIODICITES = ["quotidien", "hebdomadaire", "bimensuel", "mensuel",
                "bulletin irrégulier", "radio"]

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
    THEMATIQUES = [
        "actualites_a_la_une", "politique", "economie_finance", "environnement_climat",
        "sciences_technologies", "societe", "culture", "international", "musique",
        "sports", "faits_divers", "opinions_editoriaux", "lifestyle_art_de_vivre",
        "sante", "education", "histoire_patrimoine", "medias_communication",
        "religion_spiritualite", "petites_annonces_services", "meteo",
    ]

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
L'édition doit être ancrée dans la réalité de CETTE zone précise — son nom, son ton
et son style doivent refléter la culture, la langue et les tensions de la zone
telle que décrite ci-dessous (description, statut, tensions), jamais celles d'une
zone alliée, rivale ou associée mentionnée ailleurs dans le monde.

Le français reste la langue de rédaction de tous les champs, y compris "ton".
Le champ "langue_style" ne doit indiquer une langue ou un mélange linguistique
réel (ex. créole, portugais, mandarin) QUE si la description ou les lieux
emblématiques de la zone le justifient explicitement (héritage colonial ou
migratoire documenté) — dans le doute, laisse-le vide ou décris un simple
registre de style (ex. "administratif", "oral et communautaire").

Pour chaque zone, invente aussi une petite rédaction de 6 journalistes qui signent
les articles de cette édition locale. Chaque journaliste a un nom crédible pour la
culture réelle de la zone (pas un nom géneriquement "occidental" par défaut) et se
voit attribuer une ou plusieurs thématiques de prédilection. À eux six, ils doivent
couvrir la totalité des thématiques suivantes (plusieurs thématiques peuvent aller
au même journaliste, mais chaque thématique doit être couverte par au moins un·e) :
{thematiques_liste}

Réponds avec une liste JSON :
[
  {{
    "index": 0,
    "nom": "Nom du journal local (original, ancré dans la culture réelle de CETTE zone)",
    "ton": "2-3 phrases décrivant le ton éditorial local spécifique à cette zone",
    "langue_style": "Marqueur culturel/linguistique UNIQUEMENT si justifié par la zone elle-même, sinon chaîne vide",
    "journalistes": [
      {{"nom": "Prénom Nom", "thematiques": ["politique", "international"]}},
      {{"nom": "Prénom Nom", "thematiques": ["economie_finance", "sciences_technologies"]}},
      ...
    ]
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
        thematiques_liste=", ".join(THEMATIQUES),
        zones=json.dumps(items, ensure_ascii=False, indent=2),
    )

    return prompt


# Correctif du 31 oct 2026 (S24, journaux) : plus aucune rédaction factice.
# Avant : un lot au JSON cassé écrivait « Édition … » vide pour chaque zone du
# lot ; en --update ces zones passaient ensuite pour présentes (jamais
# régénérées, nettoyage par clean_fallback_journaux.py) et en mode complet
# elles écrasaient un journal existant. Désormais une zone ratée reste absente
# du résultat : elle est listée en fin de lot et reprise au prochain --update.

LOGS_DIR = os.path.join(VAULT_ROOT, "gui", "logs")


def _log_echec_json(raw, contexte):
    """Garde la réponse illisible pour diagnostic (même convention que
    instance_generation_common.extraire_json : gui/logs/llm_json_echec_*)."""
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        path = os.path.join(LOGS_DIR, "llm_json_echec_journaux_{}.txt".format(
            datetime.now().strftime("%Y%m%d_%H%M%S_%f")))
        with open(path, "w", encoding="utf-8") as f:
            f.write("# {}\n\n{}".format(contexte, raw))
        print("      réponse brute gardée : {}".format(path))
    except Exception as e:
        print("      (log impossible : {})".format(e))


def _parse_liste_json(raw):
    """
    Lit une liste JSON d'objets dans une réponse LLM, avec tolérance :
    balises ```json, texte avant/après, virgules finales, et réponse tronquée
    (les objets complets avant la coupure sont récupérés).
    Retourne (liste, complete) ; complete=False si la liste a été récupérée
    partiellement ou pas du tout.
    """
    texte = re.sub(r"^```(?:json)?\s*", "", (raw or "").strip())
    texte = re.sub(r"\s*```$", "", texte).strip()
    debut = texte.find("[")
    if debut < 0:
        return [], False
    texte = texte[debut:]
    dec = json.JSONDecoder()

    for candidat in (texte, re.sub(r",(\s*[\]}])", r"\1", texte)):
        try:
            data, _ = dec.raw_decode(candidat)
            if isinstance(data, list):
                return [e for e in data if isinstance(e, dict)], True
        except ValueError:
            pass

    # Récupération objet par objet (réponse tronquée)
    objets, pos = [], 1
    while pos < len(texte):
        while pos < len(texte) and texte[pos] in " \t\r\n,":
            pos += 1
        if pos >= len(texte) or texte[pos] != "{":
            break
        try:
            obj, pos = dec.raw_decode(texte, pos)
        except ValueError:
            break
        if isinstance(obj, dict):
            objets.append(obj)
    return objets, False


def _entree_valide(entry, zone):
    """Une entrée n'est gardée que si elle a un nom de journal, autre que le
    motif factice de l'ancien fallback (« Édition <nom de la zone> »)."""
    nom = (entry.get("nom") or "").strip() if isinstance(entry, dict) else ""
    factice = "Édition {}".format(zone.get("nom", zone["slug"]))
    return bool(nom) and nom.lower() != factice.lower()


def _appel_lot(scenario, ligne, reseau, batch, etiquette):
    """Un appel LLM pour un lot ; retourne {zone_slug: entrée} (zones réussies seulement)."""
    prompt = build_prompt(scenario, ligne, reseau, batch)
    try:
        raw = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=8000,  # augmenté le 6 juillet : le schéma "journalistes"
                              # (6 par zone) produit un JSON bien plus long
                              # qu'avant — 2000 tokens tronquait systématiquement
                              # les lots de 5 zones (erreur JSON invalide).
            temperature=0.7,
            task_tier=TASK_TIER,
        )
    except Exception as e:
        print("    [WARN] {} : appel échoué ({})".format(etiquette, e))
        return {}

    data, complete = _parse_liste_json(raw)
    ok = {}
    for entry in data:
        idx = entry.get("index")
        if isinstance(idx, int) and 0 <= idx < len(batch) and _entree_valide(entry, batch[idx]):
            ok[batch[idx]["slug"]] = {
                "nom":          entry["nom"].strip(),
                "ton":          entry.get("ton", ""),
                "langue_style": entry.get("langue_style", ""),
                "journalistes": entry.get("journalistes", []) or [],
            }
    if not complete:
        print("    [WARN] {} : JSON {} ({} zone(s) récupérée(s) sur {})".format(
            etiquette, "tronqué" if data else "illisible", len(ok), len(batch)))
        _log_echec_json(raw, "{} / {} / {} — {}".format(scenario, ligne, etiquette,
                                                       ", ".join(z["slug"] for z in batch)))
    return ok


def generate_journals_for_zones(scenario, ligne, reseau, zones, batch_size=3):
    """
    Génère les profils de journaux pour toutes les zones via API (par lots).
    Retourne un dict {zone_slug: {nom, ton, langue_style, journalistes}}
    contenant UNIQUEMENT les zones réussies. Une zone absente d'un lot est
    retentée seule une fois ; si elle échoue encore, elle reste absente
    (reprise par un prochain --update), jamais remplacée par une entrée factice.
    """
    results = {}
    batches = [zones[i:i+batch_size] for i in range(0, len(zones), batch_size)]

    _provider, _model = resolve_for_tier(TASK_TIER)
    print("  → {} zones | {} lot(s) de {} | {} ({}, tier={})".format(
        len(zones), len(batches), batch_size, _provider, _model, TASK_TIER
    ))

    echecs = []
    for i, batch in enumerate(batches):
        etiquette = "Lot {}/{}".format(i + 1, len(batches))
        print("    {}...".format(etiquette))
        ok = _appel_lot(scenario, ligne, reseau, batch, etiquette)
        results.update(ok)

        manquantes = [z for z in batch if z["slug"] not in ok]
        if manquantes and len(batch) > 1:
            print("    {} zone(s) manquante(s) — nouvel essai zone par zone.".format(len(manquantes)))
            for z in manquantes:
                ok1 = _appel_lot(scenario, ligne, reseau, [z], "{} / {}".format(etiquette, z["slug"]))
                results.update(ok1)
        echecs += [z["slug"] for z in batch if z["slug"] not in results]
        print("    OK — {} journal(aux) sur {}".format(
            sum(1 for z in batch if z["slug"] in results), len(batch)))

    if echecs:
        print("  [WARN] {} zone(s) sans journal (rien écrit pour elles) : {}".format(
            len(echecs), ", ".join(echecs)))
        print("         → relancer avec --update pour les reprendre.")

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
    if os.path.exists(JOURNAUX_PATH):
        shutil.copy2(JOURNAUX_PATH, JOURNAUX_PATH + ".bak")
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

def process_scenario_fill_journalistes(scenario, ligne_filter, journaux, dry_run):
    """
    Complète UNIQUEMENT le champ "journalistes" des zones déjà présentes dans
    journaux.yaml qui ne l'ont pas encore (ex. entrées créées avant l'ajout
    de ce champ, ou créées avec l'ancien format à un seul journaliste).
    Ne touche jamais à nom/ton/langue_style déjà en place.
    """
    print("\n=== {} (fill-journalistes) ===".format(scenario.upper()))

    zones = parse_geographie(scenario)
    if not zones:
        return
    zones_by_slug = {z["slug"]: z for z in zones}

    lignes_a_traiter = [ligne_filter] if ligne_filter != "all" else LIGNES

    for ligne in lignes_a_traiter:
        print("\n  -- Ligne : {} --".format(ligne))
        reseau = RESEAUX[scenario][ligne]
        existing_zones = journaux.get(scenario, {}).get(ligne, {}).get("zones", {})

        a_completer_slugs = [
            slug for slug, z in existing_zones.items()
            if not z.get("journalistes") and slug in zones_by_slug
        ]
        if not a_completer_slugs:
            print("  Toutes les zones ont déjà une rédaction — rien à faire.")
            continue
        print("  {} zone(s) sans rédaction à compléter.".format(len(a_completer_slugs)))

        if dry_run:
            print("  [dry-run] Compléterait : {}".format(", ".join(a_completer_slugs)))
            continue

        zones_batch = [zones_by_slug[slug] for slug in a_completer_slugs]
        nouveaux = generate_journals_for_zones(scenario, ligne, reseau, zones_batch)

        # Fusion partielle : seul le champ "journalistes" est copié, le reste
        # de l'entrée existante (nom/ton/langue_style) n'est jamais touché.
        ajoutees = 0
        for slug, data in nouveaux.items():
            if slug in existing_zones and data.get("journalistes"):
                existing_zones[slug]["journalistes"] = data["journalistes"]
                ajoutees += 1

        journaux[scenario][ligne]["zones"] = existing_zones
        print("  {} rédaction(s) ajoutée(s) sur {} pour {}/{}.".format(
            ajoutees, len(a_completer_slugs), scenario, ligne
        ))


# ---------------------------------------------------------------------------
# FICHE PUBLIQUE DES JOURNAUX (--fill-presentation)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_FICHE = """Tu rédiges, pour une revue de presse internationale de l'an 2098, la fiche de présentation des journaux qu'elle reprend, à la manière des fiches « source » de Courrier International.
Réponds UNIQUEMENT avec un JSON valide. Pas de texte avant ou après. Pas de backticks."""


def build_prompt_fiche(scenario, ligne, reseau, lot):
    """lot : liste de (zone_slug, zone_geo, journal)"""
    items = []
    for i, (slug, z, j) in enumerate(lot):
        lieux = [l.get("nom") if isinstance(l, dict) else str(l)
                 for l in (z.get("lieux_emblematiques") or [])][:6]
        items.append({
            "index": i,
            "journal": j.get("nom", ""),
            "consigne_de_ton_interne": j.get("ton", ""),
            "langue_style": j.get("langue_style", ""),
            "zone": z.get("nom", slug),
            "description_zone": (z.get("description") or "")[:400],
            "periode_transition": z.get("periode_transition", ""),
            "lieux_emblematiques": lieux,
        })
    return """Scénario : {scenario}
Réseau éditorial du journal : {reseau_nom} — {charte}
Ligne : {ligne}

Pour chaque journal ci-dessous, rédige sa fiche publique :
- "presentation" : 2 phrases, 30 à 50 mots, en français, au présent, écrites pour un lecteur. Dis ce qu'est ce journal (type, lectorat, influence, positionnement) de façon neutre et concrète, comme une fiche de revue de presse. N'emploie pas les mots « ton », « registre » ni « style », ne recopie pas la consigne interne, pas de jugement péjoratif, ne parle jamais de fiction ni de scénario.
- "ville" : la ville où le journal est édité, à choisir dans la zone (lieux emblématiques ou description) ; si le journal est clandestin ou itinérant, écris "itinérant".
- "periodicite" : une valeur parmi {periodicites}.
- "fondation" : une année entre 2026 et 2097, cohérente avec l'histoire de la zone (période de transition) et avec la nature du journal (une feuille clandestine est souvent récente).

Réponds avec une liste JSON :
[{{"index": 0, "presentation": "…", "ville": "…", "periodicite": "…", "fondation": 2061}}, …]

Journaux :
{items}""".format(
        scenario=scenario, reseau_nom=reseau["nom"], charte=reseau["charte"], ligne=ligne,
        periodicites=", ".join(PERIODICITES),
        items=json.dumps(items, ensure_ascii=False, indent=2),
    )


def _valider_fiche(entry):
    fiche = {}
    pres = (entry.get("presentation") or "").strip()
    if len(pres.split()) >= 12:
        fiche["presentation"] = pres
    ville = (entry.get("ville") or "").strip()
    if ville:
        fiche["ville"] = ville
    per = (entry.get("periodicite") or "").strip().lower()
    if per in PERIODICITES:
        fiche["periodicite"] = per
    try:
        an = int(entry.get("fondation"))
        if 2026 <= an <= 2097:
            fiche["fondation"] = an
    except (TypeError, ValueError):
        pass
    return fiche


def process_scenario_fill_presentation(scenario, ligne_filter, journaux, dry_run, force, batch_size=5):
    """
    Remplit UNIQUEMENT les champs presentation/ville/periodicite/fondation.
    Sans --force : seulement les journaux qui n'ont pas encore de presentation.
    Avec --force : tous les journaux du scénario (les 4 champs sont remplacés,
    rien d'autre n'est touché).
    """
    print("\n=== {} (fill-presentation{}) ===".format(scenario.upper(), ", force" if force else ""))
    fm_zones = {}
    path = os.path.join(GEOGRAPHIE_DIR, "{}.md".format(scenario))
    if os.path.exists(path):
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", open(path, encoding="utf-8").read(), re.DOTALL)
        if m:
            fm = yaml.safe_load(re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))) or {}
            fm_zones = {z["slug"]: z for z in fm.get("zones", []) if isinstance(z, dict) and z.get("slug")}

    for ligne in ([ligne_filter] if ligne_filter != "all" else LIGNES):
        reseau = RESEAUX[scenario][ligne]
        existing = journaux.get(scenario, {}).get(ligne, {}).get("zones", {})
        cibles = [slug for slug, j in existing.items() if force or not j.get("presentation")]
        print("  -- {} : {} journal(aux) à traiter sur {}".format(ligne, len(cibles), len(existing)))
        if not cibles or dry_run:
            continue
        _p, _m = resolve_for_tier(TASK_TIER_PRESENTATION)
        lots = [cibles[i:i + batch_size] for i in range(0, len(cibles), batch_size)]
        for n, lot_slugs in enumerate(lots, 1):
            lot = [(s, fm_zones.get(s, {"nom": s}), existing[s]) for s in lot_slugs]
            try:
                raw = call_llm(system_prompt=SYSTEM_PROMPT_FICHE,
                               user_prompt=build_prompt_fiche(scenario, ligne, reseau, lot),
                               max_tokens=3000, temperature=0.6,
                               task_tier=TASK_TIER_PRESENTATION).strip()
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw).strip()
                data, _ = json.JSONDecoder().raw_decode(raw)
                faits = 0
                for entry in data:
                    idx = entry.get("index")
                    if isinstance(idx, int) and 0 <= idx < len(lot):
                        fiche = _valider_fiche(entry)
                        if "presentation" in fiche:
                            existing[lot[idx][0]].update(fiche)
                            faits += 1
                print("    Lot {}/{} ({}) : {} fiche(s)".format(n, len(lots), _m, faits))
            except Exception as e:
                print("    [WARN] Lot {}/{} échoué : {} — relancer pour reprendre".format(n, len(lots), e))


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
    parser.add_argument("--fill-journalistes", action="store_true",
                        help="Complète uniquement le champ 'journaliste' des zones "
                             "déjà présentes qui ne l'ont pas encore, sans toucher "
                             "à nom/ton/langue_style.")
    parser.add_argument("--fill-presentation", action="store_true",
                        help="Remplit la fiche publique (presentation, ville, periodicite, "
                             "fondation) des journaux qui n'en ont pas, sans toucher au reste.")
    parser.add_argument("--force", action="store_true",
                        help="Avec --fill-presentation : refait la fiche de tous les journaux.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche sans écrire.")

    return parser.parse_args()


def main():
    args = parse_args()

    scenarios = VALID_SCENARIOS if args.all else [args.scenario]

    print("=== generate_journaux.py ===")
    _p, _m = resolve_for_tier(TASK_TIER_PRESENTATION if args.fill_presentation else TASK_TIER)
    print("Tier : {} → Fournisseur : {} | Modèle : {}".format(
        TASK_TIER_PRESENTATION if args.fill_presentation else TASK_TIER, _p, _m))
    print("Scénarios   : {}".format(", ".join(scenarios)))
    print("Ligne       : {}".format(args.ligne))
    print("Mode        : {}{}".format(
        "fill-presentation" + (" --force" if args.force else "") if args.fill_presentation else
        "fill-journalistes" if args.fill_journalistes else ("update" if args.update else "complet"),
        " [dry-run]" if args.dry_run else ""
    ))

    # Charger l'existant
    journaux = load_journaux()

    # Traitement
    if args.fill_presentation and not args.dry_run and os.path.exists(JOURNAUX_PATH):
        import shutil
        shutil.copy2(JOURNAUX_PATH, JOURNAUX_PATH + ".bak_presentation")
        print("Sauvegarde : journaux.yaml.bak_presentation")

    for scenario in scenarios:
        if args.fill_presentation:
            process_scenario_fill_presentation(
                scenario=scenario,
                ligne_filter=args.ligne,
                journaux=journaux,
                dry_run=args.dry_run,
                force=args.force,
            )
        elif args.fill_journalistes:
            process_scenario_fill_journalistes(
                scenario=scenario,
                ligne_filter=args.ligne,
                journaux=journaux,
                dry_run=args.dry_run,
            )
        else:
            process_scenario(
                scenario=scenario,
                ligne_filter=args.ligne,
                journaux=journaux,
                update_mode=args.update,
                dry_run=args.dry_run,
            )

    # Sauvegarde (en --fill-presentation --dry-run, rien à afficher de plus)
    if args.fill_presentation and args.dry_run:
        print("\n[dry-run] rien n'a été appelé ni écrit.")
    else:
        save_journaux(journaux, dry_run=args.dry_run)

    print("\nTerminé.")


if __name__ == "__main__":
    main()
