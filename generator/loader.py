"""
loader.py
---------
Lit et parse les fichiers Obsidian (.md) du vault Ourrassol2098.
Extrait le frontmatter YAML et le corps markdown de chaque fiche.
"""

import os
import re
import yaml
from typing import Optional


# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

VAULT_PATH = "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098"

PATHS = {
    "scenarios":        os.path.join(VAULT_PATH, "scenarios"),
    "variables":        os.path.join(VAULT_PATH, "variables"),
    "thematiques":      os.path.join(VAULT_PATH, "thematiques"),
    "influence_matrix": os.path.join(VAULT_PATH, "influence_matrix.md"),
    "entites":          os.path.join(VAULT_PATH, "entites"),
    "instances":        os.path.join(VAULT_PATH, "instances"),
    "evenements":       os.path.join(VAULT_PATH, "evenements"),
    "event_instances":  os.path.join(VAULT_PATH, "event_instances"),
}

VALID_VARS = [
    "systeme_economique_redistribution",
    "gouvernance_institutions",
    "geopolitique_conflits",
    "valeurs_culture_tempo_sociale",
    "organisation_territoires",
    "sante_biotechnologies",
    "frontieres_du_systeme",
    "technologie_information",
    "climat_environnement_global",
    "energie_ressources_critiques",
    "demographie_mobilite_humaine",
    "systemes_productifs_travail",
]

VALID_SCENARIOS = [
    "fortress_world",
    "new_sustainability",
    "breakdown",
    "eco_communalism",
    "policy_reform",
    "reference",
]


# ─────────────────────────────────────────
# PARSING DE BASE
# ─────────────────────────────────────────

def parse_md_file(filepath):
    """
    Parse un fichier .md Obsidian.
    Retourne un dict avec :
      - 'frontmatter' : dict YAML (ou {} si absent)
      - 'body'        : str markdown (corps après le second ---)
      - 'raw'         : str contenu brut complet
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError("Fichier introuvable : {}".format(filepath))

    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    frontmatter = {}
    body = raw

    # Extraire le frontmatter entre --- et ---
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if fm_match:
        fm_str = fm_match.group(1)
        body = fm_match.group(2).strip()
        # Nettoyer les wikilinks [[slug]] → slug dans le YAML
        fm_str_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", fm_str)
        try:
            frontmatter = yaml.safe_load(fm_str_clean) or {}
        except yaml.YAMLError as e:
            print("  Avertissement YAML dans {} : {}".format(filepath, e))
            frontmatter = {}

    return {
        "frontmatter": frontmatter,
        "body": body,
        "raw": raw,
    }


def clean_wikilinks(value):
    """Supprime les [[...]] dans une valeur string ou liste."""
    if isinstance(value, str):
        return re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)
    if isinstance(value, list):
        return [clean_wikilinks(v) for v in value]
    return value


# ─────────────────────────────────────────
# CHARGEMENT DES FICHES
# ─────────────────────────────────────────

def load_scenario(scenario_slug):
    """
    Charge une fiche scénario.
    Retourne un dict structuré avec toutes les sections utiles.
    """
    if scenario_slug not in VALID_SCENARIOS:
        raise ValueError("Scénario invalide : {}. Valides : {}".format(
            scenario_slug, VALID_SCENARIOS))

    filepath = os.path.join(PATHS["scenarios"], "{}.md".format(scenario_slug))
    parsed = parse_md_file(filepath)
    fm = parsed["frontmatter"]

    return {
        "slug":                     scenario_slug,
        "name":                     fm.get("name", scenario_slug),
        "trajectory":               fm.get("trajectory", ""),
        "state_of_system":          fm.get("state_of_system", ""),
        "tension_level":            fm.get("tension_level", ""),
        "political_regime":         fm.get("political_regime", ""),
        "dominant_region_structure":fm.get("dominant_region_structure", ""),
        "transformation_speed":     fm.get("transformation_speed", ""),
        "dominant_variables":       clean_wikilinks(fm.get("dominant_variables", [])),
        "reinforced_variables":     clean_wikilinks(fm.get("reinforced_variables", [])),
        "constrained_variables":    clean_wikilinks(fm.get("constrained_variables", [])),
        "variable_states":          fm.get("variable_states", {}),
        "triggers":                 fm.get("triggers", []),
        "system_effects":           fm.get("system_effects", {}),
        "summary":                  _extract_narrative(parsed["body"], "Résumé"),
        "system_logic":             _extract_narrative(parsed["body"], "Logique système"),
        "interpretation":           _extract_narrative(parsed["body"], "Interprétation"),
        "implications":             _extract_narrative(parsed["body"], "Implications"),
        "boucles":                  _extract_boucles_from_body(parsed["body"]),
        "signaux_faibles_scenario": _extract_signaux_faibles_scenario_from_body(parsed["body"]),
        "body":                     parsed["body"],
    }


def load_variable(variable_slug):
    """
    Charge une fiche variable.
    Retourne un dict structuré avec toutes les sections utiles.
    """
    if variable_slug not in VALID_VARS:
        raise ValueError("Variable invalide : {}. Valides : {}".format(
            variable_slug, VALID_VARS))

    filepath = os.path.join(PATHS["variables"], "{}.md".format(variable_slug))
    parsed = parse_md_file(filepath)
    fm = parsed["frontmatter"]

    # Extraire les states (un par scénario)
    states = {}
    raw_states = fm.get("states", {}) or {}
    if isinstance(raw_states, dict):
        for sc, state_data in raw_states.items():
            sc_clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(sc)).strip()
            if sc_clean in VALID_SCENARIOS and isinstance(state_data, dict):
                states[sc_clean] = {
                    "level":             state_data.get("level", ""),
                    "volatility":        state_data.get("volatility", ""),
                    "state_logic":       str(state_data.get("state_logic", "")).strip(),
                    "dominant_dynamics": state_data.get("dominant_dynamics", []) or [],
                    "system_role_shift": state_data.get("system_role_shift", []) or [],
                    "coupling_intensity": {
                        re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(k)).strip(): v
                        for k, v in (state_data.get("coupling_intensity") or {}).items()
                    },
                }

    # Scenario mapping
    sm = fm.get("scenario_mapping", {}) or {}
    dominant_scenarios   = clean_wikilinks(sm.get("dominant_scenarios", []) if isinstance(sm, dict) else [])
    reinforcing_scenarios = clean_wikilinks(sm.get("reinforcing_scenarios", []) if isinstance(sm, dict) else [])
    constrained_scenarios = clean_wikilinks(sm.get("constrained_scenarios", []) if isinstance(sm, dict) else [])

    return {
        "slug":                   variable_slug,
        "variable_type":          fm.get("variable_type", ""),
        "global_influence_level": fm.get("global_influence_level", ""),
        "domain":                 fm.get("domain", []) or [],
        "influences":             clean_wikilinks(fm.get("influences", []) or []),
        "influenced_by":          clean_wikilinks(fm.get("influenced_by", []) or []),
        "bidirectional_links":    clean_wikilinks(fm.get("bidirectional_links", []) or []),
        "direction":              fm.get("direction", ""),
        "intensity":              fm.get("intensity", ""),
        "inertia":                fm.get("inertia", ""),
        "speed":                  fm.get("speed", ""),
        "states":                 states,
        "dominant_scenarios":     dominant_scenarios,
        "reinforcing_scenarios":  reinforcing_scenarios,
        "constrained_scenarios":  constrained_scenarios,
        "ruptures":               _extract_ruptures_from_body(parsed["body"]),
        "signal_to_state":        _extract_signal_to_state_from_body(parsed["body"]),
        "simulation":             fm.get("simulation", {}) or {},
        "sub_variables":          _clean_sub_variables(fm.get("sub_variables", []) or []),
        "indicateurs":            _extract_indicateurs_from_body(parsed["body"]),
        "body":                   parsed["body"],
    }


def _extract_boucles_from_body(body):
    """
    Extrait les boucles de stabilisation/déstabilisation depuis la
    section '## 6. Dynamique systémique' du corps markdown d'une fiche
    scénario.

    La sous-catégorie **Comportements** est volontairement ignorée —
    elle recoupe largement system_effects (frontmatter), déjà utilisé.

    Structure attendue :
      ## 6. Dynamique systémique
      **Comportements**
      - ...
      **Boucles de stabilisation**
      - item1
      - item2
      **Boucles de déstabilisation**
      - item3

    Retourne un dict : {"stabilisation": [...], "destabilisation": [...]}
    (listes vides si la sous-section est absente)
    """
    result = {"stabilisation": [], "destabilisation": []}

    m = re.search(r"##\s+6\.\s+Dynamique systémique\s*\n(.*?)(?=\n##\s+|\Z)", body, re.DOTALL)
    if not m:
        return result

    block = m.group(1)

    m_stab = re.search(
        r"\*\*Boucles de stabilisation\*\*\s*\n(.*?)(?=\n\*\*\w|\Z)", block, re.DOTALL
    )
    if m_stab:
        result["stabilisation"] = [
            line.lstrip("- ").strip()
            for line in m_stab.group(1).split("\n")
            if line.strip().startswith("-")
        ]

    m_destab = re.search(
        r"\*\*Boucles de déstabilisation\*\*\s*\n(.*?)(?=\n\*\*\w|\Z)", block, re.DOTALL
    )
    if m_destab:
        result["destabilisation"] = [
            line.lstrip("- ").strip()
            for line in m_destab.group(1).split("\n")
            if line.strip().startswith("-")
        ]

    return result


def _extract_signaux_faibles_scenario_from_body(body):
    """
    Extrait uniquement la sous-catégorie **Signaux faibles** de la
    section '## 7. Indicateurs & signaux' du corps markdown d'une fiche
    scénario (les "Indicateurs" de cette même section sont volontairement
    ignorés — ils recoupent triggers/system_effects déjà utilisés).

    À ne pas confondre avec la section 7 "Signaux faibles" des fiches
    VARIABLES (réservoir de signal_to_state) — ici, ce sont des signaux
    propres au scénario dans son ensemble.

    Structure attendue :
      ## 7. Indicateurs & signaux
      **Indicateurs**
      - ...
      **Signaux faibles**
      - item1
      - item2

    Retourne une liste de str (peut être vide).
    """
    m = re.search(r"##\s+7\.\s+Indicateurs & signaux\s*\n(.*?)(?=\n##\s+|\Z)", body, re.DOTALL)
    if not m:
        return []

    block = m.group(1)

    m_signaux = re.search(
        r"\*\*Signaux faibles\*\*\s*\n(.*?)(?=\n\*\*\w|\Z)", block, re.DOTALL
    )
    if not m_signaux:
        return []

    return [
        line.lstrip("- ").strip()
        for line in m_signaux.group(1).split("\n")
        if line.strip().startswith("-")
    ]


def load_thematique(thematique_slug):
    """
    Charge une fiche thématique.
    Retourne un dict structuré.
    """
    filepath = os.path.join(PATHS["thematiques"], "{}.md".format(thematique_slug))
    parsed = parse_md_file(filepath)
    fm = parsed["frontmatter"]

    return {
        "slug":                thematique_slug,
        "name":                fm.get("name", thematique_slug),
        "variables_visibles":  clean_wikilinks(fm.get("variables_visibles", []) or []),
        "variables_secondaires": clean_wikilinks(fm.get("variables_secondaires", []) or []),
        "dependances_fortes":  clean_wikilinks(fm.get("dependances_fortes", []) or []),
        "acteurs":             fm.get("acteurs", []) or [],
        "echelle":             fm.get("echelle", ""),
        "temporalite":         fm.get("temporalite", ""),
        "style_journalistique": fm.get("style_journalistique", ""),
        "format_dominant":     fm.get("format_dominant", ""),
        "niveau_emotionnel":   fm.get("niveau_emotionnel", ""),
        "sensibilite_cascades": fm.get("sensibilite_cascades", 0),
        "types_evenements":    fm.get("types_evenements", []) or [],
        "angles_frequents":    fm.get("angles_frequents", []) or [],
        "signaux_observes":    fm.get("signaux_observes", []) or [],
        "body":                parsed["body"],
    }


def load_influence_matrix():
    """
    Charge la matrice d'influence.
    Retourne une liste de dicts (edges) et un index par source.
    """
    parsed = parse_md_file(PATHS["influence_matrix"])
    fm = parsed["frontmatter"]

    raw_edges = fm.get("edges", []) or []
    edges = []
    for e in raw_edges:
        if not isinstance(e, dict):
            continue
        source = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(e.get("source", ""))).strip()
        target = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(e.get("target", ""))).strip()
        if source in VALID_VARS and target in VALID_VARS:
            edges.append({
                "source":          source,
                "target":          target,
                "weight":          float(e.get("weight", 0)),
                "polarity":        int(e.get("polarity", 1)),
                "lag":             int(e.get("lag", 1)),
                "nonlinearity":    e.get("nonlinearity", ""),
                "temporal_weight": float(e.get("temporal_weight", 0)),
                "feedback_role":   e.get("feedback_role", ""),
            })

    # Index par source pour accès rapide
    by_source = {}
    for e in edges:
        by_source.setdefault(e["source"], []).append(e)

    # Index par paire (source, target)
    by_pair = {}
    for e in edges:
        by_pair[(e["source"], e["target"])] = e

    return {
        "edges":     edges,
        "by_source": by_source,
        "by_pair":   by_pair,
    }


def load_all_variables():
    """Charge les 12 fiches variables d'un coup."""
    return {slug: load_variable(slug) for slug in VALID_VARS}


def load_all_scenarios():
    """Charge les 6 fiches scénarios d'un coup."""
    return {slug: load_scenario(slug) for slug in VALID_SCENARIOS}


# ─────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────

def _extract_narrative(body, section_title):
    """
    Extrait le texte sous un sous-titre en gras (**Titre**) dans le corps
    markdown — utilisé pour les sous-sections de "## 9. Synthèse systémique"
    (Résumé, Logique système, Interprétation, Implications).

    Le texte s'arrête au prochain sous-titre en gras, au prochain titre ##,
    ou à la fin du document.
    """
    pattern = r"\*\*" + re.escape(section_title) + r"\*\*\s*\n(.*?)(?=\n\*\*|\n##|\Z)"
    m = re.search(pattern, body, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def _extract_signal_to_state_from_body(body):
    """
    Extrait la section signal_to_state depuis le corps markdown.

    Structure attendue :
      ## 12. Trajectoire des signaux 2025 → 2098
      ```yaml
      signal_to_state:
        - signal: nom_du_signal
          scenarios:
            breakdown:
              evolution: ...
              date_bascule: ...
              evenement_cle: ...
      ```

    Retourne un dict :
    {
      "nom_signal": {
        "breakdown": {
          "evolution": str,
          "date_bascule": str,
          "evenement_cle": str
        },
        ...
      },
      ...
    }
    """
    result = {}

    # Extraire le bloc ## 12.
    m = re.search(
        r"##\s+12\.\s+Trajectoire des signaux.*?\n.*?```yaml\s*\n(.*?)```",
        body, re.DOTALL
    )
    if not m:
        return result

    yaml_block = m.group(1).strip()

    # Nettoyer les wikilinks éventuels
    yaml_block = re.sub(r"\[\[([^\]]+)\]\]", r"\1", yaml_block)

    try:
        parsed = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return result

    if not isinstance(parsed, dict):
        return result

    raw_signals = parsed.get("signal_to_state", [])
    if not isinstance(raw_signals, list):
        return result

    for entry in raw_signals:
        if not isinstance(entry, dict):
            continue
        signal_name = entry.get("signal", "")
        if not signal_name:
            continue

        scenarios_data = entry.get("scenarios", {})
        if not isinstance(scenarios_data, dict):
            continue

        result[signal_name] = {}
        for sc, sc_data in scenarios_data.items():
            sc_clean = str(sc).strip()
            if sc_clean not in VALID_SCENARIOS:
                continue
            if not isinstance(sc_data, dict):
                continue
            result[signal_name][sc_clean] = {
                "evolution":     str(sc_data.get("evolution", "")).strip(),
                "date_bascule":  str(sc_data.get("date_bascule", "")).strip(),
                "evenement_cle": str(sc_data.get("evenement_cle", "")).strip(),
            }

    return result


def get_signal_to_state_for_scenario(variable, scenario_slug):
    """
    Retourne les évolutions de signaux pour un scénario donné.
    Utilisé par snapshot.py pour construire la trajectoire historique.

    Retourne une liste de dicts :
    [
      {
        "signal": str,
        "evolution": str,
        "date_bascule": str,
        "evenement_cle": str,
      },
      ...
    ]
    """
    s2s = variable.get("signal_to_state", {})
    results = []
    for signal_name, scenarios in s2s.items():
        if scenario_slug in scenarios:
            data = scenarios[scenario_slug]
            results.append({
                "signal":        signal_name,
                "evolution":     data.get("evolution", ""),
                "date_bascule":  data.get("date_bascule", ""),
                "evenement_cle": data.get("evenement_cle", ""),
                "variable":      variable.get("slug", ""),
            })
    return results


def _clean_sub_variables(raw_sub_variables):
    """
    Nettoie la liste sub_variables du frontmatter (sans inclure 'links',
    volontairement laissés de côté pour ne pas alourdir le prompt —
    voir discussion : valeur non démontrée par rapport aux liens déjà
    couverts par la matrice d'influence principale).

    Ne garde que name + trend, valeurs normalisées en amont dans les
    fiches sources (valeurs valides : up, down, unstable, accelerating,
    saturating, stable).

    Retourne une liste de dicts : [{"name": str, "trend": str}, ...]
    """
    cleaned = []
    for sv in raw_sub_variables:
        if not isinstance(sv, dict):
            continue
        name  = str(sv.get("name", "")).strip()
        trend = str(sv.get("trend", "")).strip()
        if name:
            cleaned.append({"name": name, "trend": trend})
    return cleaned


def _extract_indicateurs_from_body(body):
    """
    Extrait uniquement la sous-catégorie **primary** de la section
    '## 6. Indicateurs' du corps markdown d'une fiche variable.

    Les sous-catégories secondary/systemic (et les catégories
    supplémentaires propres à systeme_economique_redistribution) sont
    volontairement ignorées ici — primary suffit comme banque de
    mots-clés concrets sans alourdir excessivement le prompt.

    Structure attendue :
      ## 6. Indicateurs
      **primary**
      - item1
      - item2
      **secondary**
      - ...

    Retourne une liste de str (peut être vide).
    """
    m = re.search(r"##\s+6\.\s+Indicateurs\s*\n(.*?)(?=\n##\s+|\Z)", body, re.DOTALL)
    if not m:
        return []

    block = m.group(1)

    m_primary = re.search(r"\*\*primary\*\*\s*\n(.*?)(?=\n\*\*\w+\*\*|\Z)", block, re.DOTALL)
    if not m_primary:
        return []

    items = [
        line.lstrip("- ").strip()
        for line in m_primary.group(1).split("\n")
        if line.strip().startswith("-")
    ]
    return items


def _extract_ruptures_from_body(body):
    """
    Extrait les ruptures depuis le corps markdown.
    Structure attendue :
      ## 5. Ruptures
      **technological**
      _core_
      - item1
      _extended_
      - item2
    Retourne un dict : { "technological": {"core": [...], "extended": [...]}, ... }
    """
    ruptures = {}

    # Extraire le bloc ## 5. Ruptures
    m = re.search(r"##\s+5\.\s+Ruptures\s*\n(.*?)(?=\n##\s+|\Z)", body, re.DOTALL)
    if not m:
        return ruptures

    block = m.group(1)

    # Trouver toutes les catégories **cat** et leur contenu
    cat_pattern = re.compile(r"\*\*(\w+)\*\*\s*\n(.*?)(?=\*\*\w+\*\*|\Z)", re.DOTALL)
    for cat_match in cat_pattern.finditer(block):
        category = cat_match.group(1).strip()
        content  = cat_match.group(2)

        cat_data = {}

        # Trouver les niveaux _core_ / _extended_
        level_pattern = re.compile(r"_(\w+)_\s*\n(.*?)(?=_\w+_|\Z)", re.DOTALL)
        for level_match in level_pattern.finditer(content):
            level      = level_match.group(1).strip()
            level_body = level_match.group(2)

            items = [
                line.lstrip("- ").strip()
                for line in level_body.split("\n")
                if line.strip().startswith("-")
            ]
            if items:
                cat_data[level] = items

        if cat_data:
            ruptures[category] = cat_data

    return ruptures


def get_edges_between(matrix, var_list):
    """
    Retourne les edges entre les variables d'une liste donnée.
    Utile pour extraire les tensions d'une thématique.
    """
    var_set = set(var_list)
    return [
        e for e in matrix["edges"]
        if e["source"] in var_set and e["target"] in var_set
    ]


def get_strong_edges(matrix, var_list=None, weight_threshold=0.75):
    """
    Retourne les edges forts (weight >= seuil).
    Si var_list est fourni, filtre sur ces variables uniquement.
    """
    edges = matrix["edges"]
    if var_list:
        var_set = set(var_list)
        edges = [e for e in edges if e["source"] in var_set or e["target"] in var_set]
    return [e for e in edges if e["weight"] >= weight_threshold]


# ─────────────────────────────────────────
# CHARGEMENT DES ENTITÉS ET INSTANCES
# ─────────────────────────────────────────

def load_entity(entity_slug):
    """
    Charge une fiche entité (archétype).
    Retourne un dict structuré.
    """
    filepath = os.path.join(PATHS["entites"], "{}.md".format(entity_slug))
    parsed   = parse_md_file(filepath)
    fm       = parsed["frontmatter"]

    return {
        "slug":                   entity_slug,
        "name":                   fm.get("name", entity_slug),
        "category":               fm.get("category", ""),
        "description":            str(fm.get("description", "")).strip(),
        "tension_fondamentale":   str(fm.get("tension_fondamentale", "")).strip(),
        "variables_potentielles": clean_wikilinks(fm.get("variables_potentielles", []) or []),
        "scenarios_instances":    fm.get("scenarios_instances", []) or [],
        "body":                   parsed["body"],
    }


def load_instance(instance_slug):
    """
    Charge une fiche instance (entité × scénario).
    Retourne un dict structuré avec tous les champs.
    """
    filepath = os.path.join(PATHS["instances"], "{}.md".format(instance_slug))
    parsed   = parse_md_file(filepath)
    fm       = parsed["frontmatter"]

    # Injection temporelle
    injection_raw = fm.get("injection", {}) or {}
    injection = {
        "type":               injection_raw.get("type", "canonique"),
        "annee_injection":    injection_raw.get("annee_injection", None),
        "contexte_injection": str(injection_raw.get("contexte_injection", "") or "").strip(),
        "impact_sur_variables": injection_raw.get("impact_sur_variables", []) or [],
        "propagation":        injection_raw.get("propagation", {}) or {},
    }

    return {
        "slug":                    instance_slug,
        "name":                    fm.get("name", instance_slug),
        "entite":                  fm.get("entite", ""),
        "scenario":                fm.get("scenario", ""),
        "type_dans_scenario":      fm.get("type_dans_scenario", ""),
        "role_dans_scenario":      str(fm.get("role_dans_scenario", "") or "").strip(),
        "responsabilites":         str(fm.get("responsabilites", "") or "").strip(),
        "impact_local":            fm.get("impact_local", 0),
        "impact_systemique_global":fm.get("impact_systemique_global", 0),
        "variables_influencees":   clean_wikilinks(fm.get("variables_influencees", []) or []),
        "zone_geographique":       fm.get("zone_geographique", []) or [],
        "zone_systemique":         fm.get("zone_systemique", []) or [],
        "alliances":               clean_wikilinks(fm.get("alliances", []) or []),
        "oppositions":             clean_wikilinks(fm.get("oppositions", []) or []),
        "type_relation_dominante": fm.get("type_relation_dominante", "neutralité"),
        "annee_debut":             fm.get("annee_debut", 2026),
        "annee_fin":               fm.get("annee_fin", None),
        "etat_temporel":           fm.get("etat_temporel", "actif"),
        "age_historique":          fm.get("age_historique", "mature"),
        "generation":              fm.get("generation", ""),
        "injection":               injection,
        "description_journalistique": str(fm.get("description_journalistique", "") or "").strip(),
        "signes_distinctifs":      str(fm.get("signes_distinctifs", "") or "").strip(),
        "tensions_narratives":     str(fm.get("tensions_narratives", "") or "").strip(),
        "body":                    parsed["body"],
        "localisation":            fm.get("localisation") or {},
    }


def load_instances_for_scenario(scenario_slug):
    """
    Charge toutes les instances disponibles pour un scénario donné.
    Retourne une liste de dicts d'instances.
    """
    if not os.path.exists(PATHS["instances"]):
        return []

    instances = []
    for fname in sorted(os.listdir(PATHS["instances"])):
        if not fname.endswith(".md") or fname.startswith("_"):
            continue
        # Les instances sont nommées : {entite_slug}_{scenario_slug}.md
        if not fname.endswith("_{}.md".format(scenario_slug)):
            continue
        slug = fname.replace(".md", "")
        try:
            instance = load_instance(slug)
            if instance["scenario"] == scenario_slug:
                instances.append(instance)
        except Exception as e:
            print("  Avertissement instance {} : {}".format(slug, e))

    return instances


def load_event_instances_for_scenario(scenario_slug):
    """
    Charge toutes les instances d'événements pour un scénario donné.
    Lit depuis vault/event_instances/ — fichiers nommés {slug}_{scenario}.md
    Retourne une liste de dicts triés par date.
    """
    if not os.path.exists(PATHS["event_instances"]):
        return []

    events = []
    for fname in sorted(os.listdir(PATHS["event_instances"])):
        if not fname.endswith(".md") or fname.startswith("_") or fname.startswith("."):
            continue
        if "template" in fname.lower():
            continue
        if not fname.endswith("_{}.md".format(scenario_slug)):
            continue

        parsed = parse_md_file(os.path.join(PATHS["event_instances"], fname))
        fm     = parsed["frontmatter"]

        # Vérifier le scénario
        if fm.get("scenario") != scenario_slug:
            continue

        # Ignorer si impossible ET pas de variante
        if fm.get("impossible", False):
            continue

        # Normaliser les impacts
        impacts_raw = fm.get("impact_sur_variables", []) or []
        impacts = []
        for imp in impacts_raw:
            if not isinstance(imp, dict):
                continue
            var = re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(imp.get("variable", ""))).strip()
            if var in VALID_VARS:
                impacts.append({
                    "variable":    var,
                    "delta_level": imp.get("delta_level", 0),
                    "duree":       imp.get("duree", 20),
                    "polarite":    imp.get("polarite", 1),
                })

        acteurs_raw = fm.get("acteurs_impliques", []) or []
        acteurs = [
            re.sub(r"\[\[([^\]]+)\]\]", r"\1", str(a)).strip()
            for a in acteurs_raw
        ]

        events.append({
            "slug":         fm.get("slug", fname.replace(".md", "")),
            "name":         fm.get("name", ""),
            "archetype":    fm.get("archetype", ""),
            "type":         fm.get("type_evenement", "systemic"),
            "portee":       fm.get("portee", "globale"),
            "date":         fm.get("date", 2050),
            "date_label":   fm.get("date_label", str(fm.get("date", 2050))),
            "description":  str(fm.get("description", "")).strip(),
            "consequences": str(fm.get("consequences", "")).strip(),
            "realisation":  str(fm.get("realisation", "")).strip(),
            "impacts":      impacts,
            "acteurs":      acteurs,
            "via_matrice":  fm.get("propagation", {}).get("via_matrice", True)
                            if isinstance(fm.get("propagation"), dict) else True,
            "custom":       True,
        })

    # Trier par date
    events.sort(key=lambda x: x.get("date", 2050))
    return events


# Alias pour compatibilité
def load_events_for_scenario(scenario_slug):
    return load_event_instances_for_scenario(scenario_slug)


def filter_instances_for_thematique(instances, thematique):
    """
    Filtre les instances pertinentes pour une thématique donnée.

    Critères de pertinence (par ordre de priorité) :
      1. variables_influencees intersecte variables_visibles → très pertinent
      2. variables_influencees intersecte variables_secondaires → pertinent
      3. zone_systemique intersecte les domaines de la thématique → pertinent

    Retourne les instances triées par pertinence décroissante,
    limitées à MAX_INSTANCES_PAR_PROMPT.
    """
    MAX_INSTANCES = 6

    vars_vis = set(thematique.get("variables_visibles", []))
    vars_sec = set(thematique.get("variables_secondaires", []))
    vars_all = vars_vis | vars_sec

    # Mapping thématique → zones systémiques pertinentes
    THEME_ZONES = {
        "politique":              ["gouvernance", "sécurité", "société"],
        "actualites_a_la_une":    ["gouvernance", "information", "sécurité", "économie"],
        "economie_finance":       ["économie", "infrastructure", "IA"],
        "environnement_climat":   ["société", "infrastructure"],
        "sciences_technologies":  ["IA", "information", "infrastructure", "orbital"],
        "societe":                ["société", "gouvernance"],
        "culture":                ["société", "information"],
        "international":          ["gouvernance", "sécurité", "énergie"],
        "musique":                ["société", "information"],
        "sports":                 ["société"],
        "faits_divers":           ["sécurité", "société"],
        "opinions_editoriaux":    ["société", "information", "gouvernance"],
        "lifestyle_art_de_vivre": ["société"],
        "sante":                  ["société", "infrastructure"],
        "education":              ["société", "information", "IA"],
        "histoire_patrimoine":    ["société", "information"],
        "medias_communication":   ["information", "IA", "gouvernance"],
        "religion_spiritualite":  ["société"],
        "petites_annonces_services": ["économie", "infrastructure"],
        "meteo":                  ["infrastructure", "société"],
    }

    theme_slug   = thematique.get("slug", "")
    theme_zones  = set(THEME_ZONES.get(theme_slug, []))

    scored = []
    for inst in instances:
        vars_inst  = set(inst.get("variables_influencees", []))
        zones_inst = set(inst.get("zone_systemique", []))

        score = 0

        # Score 1 — intersection avec variables visibles
        score += len(vars_inst & vars_vis) * 3

        # Score 2 — intersection avec variables secondaires
        score += len(vars_inst & vars_sec) * 1

        # Score 3 — intersection zones systémiques
        score += len(zones_inst & theme_zones) * 1

        # Score 4 — impact systémique global
        score += inst.get("impact_systemique_global", 0) * 0.5

        # Exclure les instances sans pertinence
        if score > 0:
            scored.append((score, inst))

    # Trier par score décroissant
    scored.sort(key=lambda x: -x[0])

    return [inst for _, inst in scored[:MAX_INSTANCES]]

if __name__ == "__main__":
    print("=== Test loader.py ===\n")

    # Test scénario
    print("-- Scénario : breakdown --")
    try:
        sc = load_scenario("breakdown")
        print("  name            :", sc["name"])
        print("  state_of_system :", sc["state_of_system"])
        print("  tension_level   :", sc["tension_level"])
        print("  dominant_vars   :", sc["dominant_variables"])
        print("  variable_states (aperçu) :", list(sc["variable_states"].keys())[:3])
        print("  ✓")
    except Exception as e:
        print("  ✗", e)

    print()

    # Test variable
    print("-- Variable : geopolitique_conflits --")
    try:
        var = load_variable("geopolitique_conflits")
        print("  variable_type   :", var["variable_type"])
        print("  scénarios dispo :", list(var["states"].keys()))
        if "breakdown" in var["states"]:
            print("  state breakdown :", var["states"]["breakdown"]["state_logic"][:80], "...")
        # Test signal_to_state
        s2s = var.get("signal_to_state", {})
        print("  signal_to_state :", list(s2s.keys()))
        if s2s:
            first_signal = list(s2s.keys())[0]
            if "breakdown" in s2s[first_signal]:
                ev = s2s[first_signal]["breakdown"]
                print("  ex. breakdown   :", ev["evenement_cle"][:60])
        print("  ✓")
    except Exception as e:
        print("  ✗", e)

    print()

    # Test thématique
    print("-- Thématique : actualites_a_la_une --")
    try:
        th = load_thematique("actualites_a_la_une")
        print("  name             :", th["name"])
        print("  variables_vis    :", th["variables_visibles"])
        print("  style            :", th["style_journalistique"])
        print("  format           :", th["format_dominant"])
        print("  ✓")
    except Exception as e:
        print("  ✗", e)

    print()

    # Test matrice
    print("-- Matrice d'influence --")
    try:
        mx = load_influence_matrix()
        print("  total edges      :", len(mx["edges"]))
        strong = get_strong_edges(mx, weight_threshold=0.85)
        print("  edges forts(≥0.85):", len(strong))
        sample = get_edges_between(mx, ["geopolitique_conflits", "energie_ressources_critiques"])
        print("  geo→energie      :", [(e["weight"], e["feedback_role"]) for e in sample])
        print("  ✓")
    except Exception as e:
        print("  ✗", e)

    print()

    # Test entité
    print("-- Entité : le_temoin --")
    try:
        ent = load_entity("le_temoin")
        print("  name             :", ent["name"])
        print("  category         :", ent["category"])
        print("  variables        :", ent["variables_potentielles"])
        print("  scenarios        :", ent["scenarios_instances"])
        print("  ✓")
    except Exception as e:
        print("  ✗", e)

    print()

    # Test instance
    print("-- Instance : le_temoin_breakdown --")
    try:
        inst = load_instance("le_temoin_breakdown")
        print("  name             :", inst["name"])
        print("  etat_temporel    :", inst["etat_temporel"])
        print("  impact_global    :", inst["impact_systemique_global"])
        print("  variables        :", inst["variables_influencees"])
        print("  description (50c):", inst["description_journalistique"][:50], "...")
        print("  ✓")
    except Exception as e:
        print("  ✗", e)

    print()

    # Test filtrage instances pour scénario + thématique
    print("-- Instances breakdown × actualites_a_la_une --")
    try:
        th        = load_thematique("actualites_a_la_une")
        instances = load_instances_for_scenario("breakdown")
        filtered  = filter_instances_for_thematique(instances, th)
        print("  instances dispo  :", len(instances))
        print("  instances filtrées:", len(filtered))
        for inst in filtered:
            print("    - {} [impact:{}]".format(inst["name"][:35], inst["impact_systemique_global"]))
        print("  ✓")
    except Exception as e:
        print("  ✗", e)
