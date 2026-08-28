"""
loader.py
---------
Lit et parse les fichiers Obsidian (.md) du vault Ourrassol2098.
Extrait le frontmatter YAML et le corps markdown de chaque fiche.
"""

import os
import re
import json
import random
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
    "signaux_custom":   os.path.join(VAULT_PATH, "signaux_custom"),
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

    forces = _extract_forces_from_body(parsed["body"])

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
        "forces_attractives":     forces["forces_attractives"],
        "forces_repulsives":      forces["forces_repulsives"],
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
        # 23 août 2026 : même bug que garantie_selection/priorite_forcee
        # trouvé plus tôt dans la session (load_instance()) -- cette
        # fonction reconstruit aussi le dict avec une liste blanche de
        # champs connus, donc tout nouveau champ y était silencieusement
        # perdu malgré une écriture correcte sur disque. format_fige
        # (priorité longueur : override manuel vs format naturel de la
        # thématique, voir _resoudre_longueur() dans prompt_builder.py)
        # en a fait les frais -- ajouté ici pour que le correctif
        # fonctionne réellement.
        "format_fige":         fm.get("format_fige") is True,
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


def load_custom_signals():
    """
    Charge les fiches d'audit signaux_custom/*.md et en extrait le bloc
    `impact_sur_variables` (chantier injection matricielle, 16 août 2026).

    Contrairement aux instances/événements custom (bloc `injection:` dans
    le frontmatter YAML), ce bloc vit dans le corps markdown de la fiche,
    dans un bloc ```yaml``` distinct du `signal_to_state` narratif -- les
    fiches signaux_custom n'ont pas de frontmatter dédié à l'injection,
    seulement slug/source/categorie/variables_cibles/statut. On réutilise
    donc la même technique d'extraction que inject_custom_signals.py
    (dernier bloc ```yaml``` pertinent), pas parse_md_file seul.

    Retourne une liste de dicts {variable, propagation_via_matrice,
    contexte_injection, scenarios: {scen: {annee_injection, duree,
    delta_level, polarite}}} -- un par (signal, variable) injecté.
    """
    directory = PATHS.get("signaux_custom")
    if not directory or not os.path.isdir(directory):
        return []

    impacts = []
    for filename in os.listdir(directory):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = f.read()
        except OSError:
            continue

        m = re.search(r"```yaml\nimpact_sur_variables:\n(.*?)\n```", raw, re.DOTALL)
        if not m:
            continue
        try:
            parsed = yaml.safe_load("impact_sur_variables:\n" + m.group(1))
        except yaml.YAMLError as e:
            print("  Avertissement YAML (impact_sur_variables) dans {} : {}".format(filepath, e))
            continue

        for entry in (parsed or {}).get("impact_sur_variables") or []:
            if not isinstance(entry, dict):
                continue
            variable = entry.get("variable")
            if variable not in VALID_VARS:
                continue
            impacts.append({
                "variable":                variable,
                "propagation_via_matrice": bool(entry.get("propagation_via_matrice", False)),
                "contexte_injection":      entry.get("contexte_injection", ""),
                "scenarios":               entry.get("scenarios") or {},
                "source_fiche":            filename,
            })

    return impacts


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


def _extract_forces_from_body(body):
    """
    Extrait forces_attractives/forces_repulsives depuis la section
    '## 3. Dynamique interne' du corps markdown d'une fiche variable.

    La section '## 4. Structure causale' contient un doublon partiel de
    ce même contenu (Forces attractives / Forces répulsives, formulation
    différente, parfois incohérente en snake_case sur 2 des 12 fiches) —
    volontairement ignorée : analyse comparative du 15 août sur les 12
    fiches confirmant que section 3 est systématiquement plus complète
    (4-8 items vs 1-5) et jamais affectée par l'artefact de formatage
    vu en section 4. Décision actée par David le 15 août.

    Structure attendue :
      ## 3. Dynamique interne
      ...
      **forces_attractives**
      - item1
      - item2
      **forces_repulsives**
      - item3

    Retourne un dict : {"forces_attractives": [...], "forces_repulsives": [...]}
    (listes vides si la section ou les sous-catégories sont absentes)
    """
    result = {"forces_attractives": [], "forces_repulsives": []}

    m = re.search(r"##\s+3\.\s+Dynamique interne\s*\n(.*?)(?=\n##\s+|\Z)", body, re.DOTALL)
    if not m:
        return result

    block = m.group(1)

    m_attract = re.search(
        r"\*\*forces_attractives\*\*\s*\n(.*?)(?=\n\*\*\w|\Z)", block, re.DOTALL
    )
    if m_attract:
        result["forces_attractives"] = [
            line.lstrip("- ").strip()
            for line in m_attract.group(1).split("\n")
            if line.strip().startswith("-")
        ]

    m_repuls = re.search(
        r"\*\*forces_repulsives\*\*\s*\n(.*?)(?=\n\*\*\w|\Z)", block, re.DOTALL
    )
    if m_repuls:
        result["forces_repulsives"] = [
            line.lstrip("- ").strip()
            for line in m_repuls.group(1).split("\n")
            if line.strip().startswith("-")
        ]

    return result


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
        # 23 août 2026 : load_instance() reconstruit ce dict avec une
        # liste blanche de clés connues -- garantie_selection (22-23
        # août, découplage garantie de présence / propagation d'impact,
        # voir set_garantie_selection.py) en était absent, silencieusement
        # perdu à chaque chargement malgré sa présence correcte sur
        # disque. Trouvé via un print de diagnostic temporaire après que
        # le correctif gelecek_meclisi n'ait eu AUCUN effet en conditions
        # réelles malgré un fichier .md correctement patché.
        "garantie_selection": injection_raw.get("garantie_selection", True),
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
        # Chantier trajectoire (9 août 2026) : etat_temporel + age_historique
        # fusionnés en un seul axe narratif continu. clandestin en sort,
        # devient un booléen indépendant est_clandestin.
        "trajectoire":    fm.get("trajectoire", "mature"),
        "est_clandestin": fm.get("est_clandestin", False),
        "generation":              fm.get("generation", ""),
        "injection":               injection,
        # 23 août 2026 : même bug que garantie_selection ci-dessus --
        # priorite_forcee (22 août 2026, mécanisme de présence garantie
        # d'une entité) était absent de cette liste blanche, donc
        # silencieusement perdu à chaque chargement malgré une écriture
        # correcte sur disque (confirmée hier par grep) et un test de
        # création/édition GUI réussi -- mais le test d'hier n'avait
        # vérifié que l'ÉCRITURE du champ, jamais sa PRISE EN COMPTE
        # réelle par une génération d'article. Le mécanisme n'avait donc
        # probablement jamais fonctionné en pratique jusqu'à ce correctif.
        "priorite_forcee":         fm.get("priorite_forcee") is True,
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
            # Ajouté le 2 août 2026 -- manquait, nécessaire pour restreindre
            # la liste de zones proposées lors du forçage d'un événement.
            "localisation": fm.get("localisation") or {},
        })

    # Trier par date
    events.sort(key=lambda x: x.get("date", 2050))
    return events


# Alias pour compatibilité
def load_events_for_scenario(scenario_slug):
    return load_event_instances_for_scenario(scenario_slug)


# ─────────────────────────────────────────
# FORÇAGE D'UN ÉLÉMENT (ajouté le 2 août 2026)
# ─────────────────────────────────────────

def resolve_forced_element(forcer_config, scenario_slug):
    """
    Résout le bloc `forcer:` de config.yaml (type/slug/mode) en un dict
    exploitable par snapshot.py/prompt_builder.py. Lecture seule, ne crée
    ni ne modifie rien -- si l'élément demandé n'existe pas pour ce
    scénario, retourne une erreur explicite plutôt que d'échouer
    silencieusement ou de générer un article sans lui.

    Retourne None si aucun forçage n'est configuré (forcer.type/slug
    absents), sinon un dict :
        {"type": ..., "slug": ..., "mode": ...,
         "instance"/"event"/"signal_event": ..., "erreur": str|None}
    """
    if not forcer_config or not forcer_config.get("type"):
        # Aucun forçage demandé -- comportement normal, silencieux.
        return None

    type_ = forcer_config["type"]

    if not forcer_config.get("slug"):
        # Type choisi mais slug manquant : intention ambiguë. Avant le
        # 2 août 2026, ce cas retombait silencieusement dans "aucun
        # forçage" -- le type choisi était perdu sans aucun avertissement,
        # l'article se générait normalement comme si rien n'avait été
        # coché. Traité maintenant comme une vraie erreur, remontée à
        # l'appelant (generate.py arrête avec un message clair) plutôt
        # que d'ignorer silencieusement un choix explicite de l'utilisateur.
        return {
            "type": type_, "slug": None, "mode": forcer_config.get("mode") or "ingredient",
            "erreur": ("Type de forçage choisi ({!r}) mais aucun élément sélectionné -- "
                       "choisis un élément dans la liste \"Élément à forcer\", ou repasse "
                       "\"Forcer un élément\" sur \"— Aucun forçage —\" pour générer sans "
                       "forçage.").format(type_),
        }

    mode  = forcer_config.get("mode") or "ingredient"
    if mode not in ("ingredient", "sujet_central"):
        mode = "ingredient"
    slug = forcer_config["slug"]

    if type_ == "instance":
        instance_slug = "{}_{}".format(slug, scenario_slug)
        try:
            instance = load_instance(instance_slug)
        except Exception:
            return {
                "type": type_, "slug": slug, "mode": mode, "instance": None,
                "erreur": "Instance introuvable : {} (fichier instances/{}.md attendu).".format(
                    slug, instance_slug),
            }
        return {"type": type_, "slug": slug, "mode": mode, "instance": instance, "erreur": None}

    if type_ == "evenement":
        events = load_events_for_scenario(scenario_slug)
        match = next((e for e in events if e.get("archetype") == slug or e.get("slug") == slug), None)
        if not match:
            return {
                "type": type_, "slug": slug, "mode": mode, "event": None,
                "erreur": ("Événement {!r} introuvable ou marqué 'impossible' pour {} -- "
                           "vérifie qu'une fiche event_instances/{}_{}.md existe et n'a pas "
                           "impossible: true.").format(slug, scenario_slug, slug, scenario_slug),
            }
        return {"type": type_, "slug": slug, "mode": mode, "event": match, "erreur": None}

    if type_ == "signal":
        all_variables = load_all_variables()
        for var in all_variables.values():
            for sig in get_signal_to_state_for_scenario(var, scenario_slug):
                if sig["signal"] == slug:
                    return {"type": type_, "slug": slug, "mode": mode, "signal_event": sig, "erreur": None}
        return {
            "type": type_, "slug": slug, "mode": mode, "signal_event": None,
            "erreur": ("Signal {!r} introuvable pour le scénario {} dans aucune variable "
                       "(vérifie qu'il a un bloc signal_to_state pour ce scénario précis -- "
                       "un signal peut exister sans avoir été décliné pour tous les "
                       "scénarios).").format(slug, scenario_slug),
        }

    return {
        "type": type_, "slug": slug, "mode": mode,
        "erreur": "Type de forçage inconnu : {!r} (attendu instance/evenement/signal).".format(type_),
    }


def scenarios_disponibles_pour_element(type_, slug):
    """
    Retourne la liste des scénarios (parmi VALID_SCENARIOS) où l'élément
    existe réellement -- ajouté le 2 août 2026 pour le mode "forcer" de
    generate.py : le menu de sélection des scénarios doit être restreint
    à ce qui est effectivement disponible pour l'élément choisi, plutôt
    que de proposer les 6 scénarios sans distinction.
    """
    if not type_ or not slug:
        return list(VALID_SCENARIOS)

    if type_ == "instance":
        return [sc for sc in VALID_SCENARIOS
                if os.path.exists(os.path.join(PATHS["instances"], "{}_{}.md".format(slug, sc)))]

    if type_ == "evenement":
        disponibles = []
        for sc in VALID_SCENARIOS:
            events = load_events_for_scenario(sc)
            if any(e.get("archetype") == slug for e in events):
                disponibles.append(sc)
        return disponibles

    if type_ == "signal":
        disponibles = []
        all_variables = load_all_variables()
        for sc in VALID_SCENARIOS:
            for var in all_variables.values():
                if any(sig["signal"] == slug for sig in get_signal_to_state_for_scenario(var, sc)):
                    disponibles.append(sc)
                    break
        return disponibles

    return list(VALID_SCENARIOS)


def zones_disponibles_pour_element(type_, slug, scenarios):
    """
    Retourne {scenario: [zone_slug, ...]} -- les zones où l'élément est
    effectivement localisé, pour chacun des scénarios fournis. Ajouté le
    2 août 2026, même logique que ci-dessus mais pour le champ Zone.

    Un signal n'a jamais de zone (il agit sur une variable systémique, pas
    un lieu) -- retourne {} dans ce cas, sans erreur : c'est un cas normal,
    pas un échec de résolution.
    """
    zones = {}
    if not type_ or not slug:
        return zones

    if type_ == "instance":
        for sc in scenarios:
            instance_slug = "{}_{}".format(slug, sc)
            path = os.path.join(PATHS["instances"], "{}.md".format(instance_slug))
            if not os.path.exists(path):
                continue
            try:
                inst = load_instance(instance_slug)
            except Exception:
                continue
            z = (inst.get("localisation") or {}).get("zone")
            if z:
                zones.setdefault(sc, []).append(z)

    elif type_ == "evenement":
        for sc in scenarios:
            events = load_events_for_scenario(sc)
            match = next((e for e in events if e.get("archetype") == slug), None)
            if match:
                z = (match.get("localisation") or {}).get("zone")
                if z:
                    zones.setdefault(sc, []).append(z)

    # type_ == "signal" : pas de zone, zones reste {}
    return zones


# ─────────────────────────────────────────
# ROTATION À MÉMOIRE — instances (ajouté le 2 août 2026)
# ─────────────────────────────────────────
#
# Même problème identifié pour les instances que celui déjà résolu pour
# les signaux/jalons dans prompt_builder.py (voir _select_least_used
# là-bas) : filter_instances_for_thematique() ne gardait que les
# MAX_INSTANCES premières par score, sans aucune mémoire -- une instance
# à faible impact systémique ou peu pertinente pour les thématiques
# fréquemment traitées pouvait donc ne JAMAIS apparaître dans aucun
# article, indéfiniment. Même mécanisme de rotation appliqué ici,
# fichier d'état séparé (les deux rotations sont indépendantes -- rien
# n'oblige un scénario à avoir la même dynamique de couverture pour ses
# instances que pour ses jalons historiques).

INSTANCE_STATE_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
INSTANCE_USAGE_FILE  = os.path.join(INSTANCE_STATE_DIR, "instance_usage.json")

# Tolérance utilisée pour regrouper les scores "proches" en une même
# tranche de rotation (voir _select_least_used_instances). Choisie en
# fonction de la granularité naturelle du score de
# filter_instances_for_thematique() : une variable secondaire ou une
# zone systémique valent chacune 1 point, une variable visible 3 points,
# et impact_systemique_global contribue par pas de 0.5 (0 à 2.5 sur une
# échelle de 0 à 5). Une tolérance de 2.0 absorbe un écart d'impact
# systémique jusqu'à 4 points ou une différence d'une variable/zone
# secondaire, sans effacer l'écart plus significatif d'une variable
# visible (3 points) ou d'un fort delta d'impact -- à ajuster si
# l'usage réel montre qu'elle est trop large (des instances nettement
# moins pertinentes sortent) ou trop étroite (le problème d'origine
# persiste).
INSTANCE_SCORE_TOLERANCE = 2.0


def _score_bucket(score, max_score, tolerance=INSTANCE_SCORE_TOLERANCE):
    """Regroupe un score en tranche de tolérance RELATIVE au score
    maximum du lot de candidats, pour que la rotation traite comme
    "ex-aequo" des scores proches et pas seulement identiques.

    Un découpage par arrondi absolu (round(score/tolerance)) a un défaut
    de bord : deux scores très proches peuvent tomber de part et
    d'autre d'une limite de tranche par pur hasard d'arrondi (ex. 10.0
    et 9.0 avec tolerance=2.0 : round(5.0)=5 mais round(4.5)=4 --
    jamais groupés bien qu'à 1 point d'écart). En calculant la tranche
    par rapport au score maximum du lot (bucket 0 = [max-tolerance, max]),
    le meilleur score et tout ce qui est à moins de `tolerance` de lui
    sont garantis dans la même tranche. Voir _select_least_used_instances.
    """
    return int((max_score - score) // tolerance)


def _load_instance_usage_state():
    """Charge l'état d'usage des instances (par scénario). Retourne {} si absent/corrompu."""
    try:
        with open(INSTANCE_USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_instance_usage_state(state):
    """Sauvegarde l'état d'usage des instances."""
    os.makedirs(INSTANCE_STATE_DIR, exist_ok=True)
    with open(INSTANCE_USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


# Cooldown d'usage (22 août 2026, backlog 9bis) : REMPLACE la pénalité
# de score initialement conçue le même jour (retirée -- invalidée par
# test synthétique avant tout déploiement réel, voir historique ci-
# dessous). Diagnostic : plusieurs institutions "à spectre large"
# (variables_influencees génériques + impact_systemique_global élevé)
# dominent structurellement le score de filter_instances_for_thematique
# -- jamais concurrencées par la rotation à mémoire du 15 août, qui ne
# départage que des scores PROCHES (_score_bucket), pas des scores
# durablement dominants.
#
# Historique de la première tentative (retirée) : une pénalité
# proportionnelle au nombre d'usages cumulés, plafonnée, appliquée au
# score avant le calcul de tranche. Test synthétique reproduisant le
# cas réel (cluster de 5-6 institutions structurellement favorisées
# ensemble dans policy_reform, pas une seule dominante isolée) : ÉCHEC
# total, 20/20 sélections inchangées quel que soit le plafond testé
# (jusqu'à 15, largement au-dessus de l'écart réel de 5.5 points).
# Cause : des instances sélectionnées à la même fréquence accumulent la
# MÊME pénalité, donc l'écart entre elles ne bouge jamais -- un défaut
# mathématique du principe "pénaliser selon le compteur d'usage" quand
# plusieurs candidates restent à égalité de fréquence, pas un problème
# de calibration qu'un plafond différent aurait pu corriger.
#
# Mécanisme retenu à la place -- cooldown dur, indépendant du score :
# après COOLDOWN_STREAK sélections CONSÉCUTIVES pour un scénario donné,
# une instance devient inéligible pendant les COOLDOWN_DURATION
# apparitions suivantes où elle aurait autrement été candidate --
# quel que soit son score, même s'il reste dominant. Ce mécanisme ne
# compare pas les instances entre elles (donc aucun problème d'égalité
# de fréquence) -- il regarde chaque instance individuellement.
COOLDOWN_STREAK = 3
COOLDOWN_DURATION = 2

# Exemption de dominance écrasante (22 août 2026, retour de David après
# le premier test du cooldown) : le cooldown dur ci-dessus force la
# rotation de TOUTE instance après COOLDOWN_STREAK sélections
# consécutives, y compris une instance dont le score reste très
# largement devant tout le reste du lot -- ce qui peut être excessif si
# sa domination est réellement méritée plutôt qu'un artefact structurel
# comme celui diagnostiqué le 22 août (cluster de plusieurs institutions
# à peu près à égalité, pas un unique score qui écrase tout).
#
# Seuil calibré entre les deux cas testés : l'écart réel diagnostiqué
# dans le vault (directive_kontinuum vs son concurrent direct, ~5.5
# points) doit RESTER soumis au cooldown -- c'est exactement le cas que
# ce chantier corrige. Un écart largement supérieur (cas de contrôle
# synthétique à 16 points) doit en être exempté. Valeur ouverte à
# recalibrage si les scores réels du vault s'avèrent différents de ces
# deux repères une fois testé en conditions réelles.
DOMINANCE_EXEMPTION_GAP = 10.0


def _select_least_used_instances(candidates, usage_state, scenario_slug, max_n):
    """
    Sélectionne max_n instances parmi candidates (déjà triées par score
    de pertinence décroissant par l'appelant), en privilégiant celles le
    moins souvent utilisées jusqu'ici pour ce scénario -- même principe
    que _select_least_used() dans prompt_builder.py pour les jalons
    signal_to_state.

    Contrairement aux jalons (purement least-used, le score n'entre plus
    en jeu une fois qu'on rotationne), on garde ici une influence du
    score de pertinence : les candidates sont d'abord regroupées par
    "tranche de score" (voir INSTANCE_SCORE_TOLERANCE ci-dessous), et
    c'est au sein d'une même tranche que la rotation départage. Ça évite
    qu'une instance très pertinente pour la thématique en cours passe
    systématiquement après une instance à peine pertinente juste parce
    qu'elle a été moins utilisée par le passé -- la rotation n'intervient
    qu'en cas de pertinence proche, pas radicalement différente.

    Historique : la version initiale (2 août 2026) regroupait par score
    EXACT plutôt que par tranche. Diagnostic du 15 août sur le vault réel
    (entité terminal_kharg_data_haven revenant comme sujet principal sur
    3/3 générations réelles, deux scénarios différents, thématique
    actualites_a_la_une) : une instance dont le score domine légèrement
    mais systématiquement toutes les autres (impact_systemique_global
    élevé + recoupement constant avec les zones de cette thématique)
    n'est presque jamais à égalité stricte avec une autre -- la rotation
    ne se déclenchait donc jamais pour elle, malgré l'intention du
    mécanisme. Le passage à une tranche de tolérance élargit ce qui
    compte comme "pertinence proche" sans changer le principe : le score
    reste le signal dominant, seule la granularité de l'égalité change.

    Cooldown (22 août 2026, voir commentaire au-dessus de COOLDOWN_STREAK) :
    avant tout calcul de tranche, les candidates actuellement en
    cooldown sont retirées d'office du pool éligible -- exclusion
    déterministe, indépendante du score. Le cooldown décompte à chaque
    apparition en tant que candidate (pas en temps réel) ; le streak
    ne progresse que sur des sélections consécutives RÉELLES, remis à
    zéro dès qu'une instance candidate n'est pas retenue un round donné.
    Exemption de dominance écrasante (voir DOMINANCE_EXEMPTION_GAP) :
    l'instance dont le score dépasse la 2e meilleure candidate du lot
    d'au moins ce seuil échappe entièrement au mécanisme -- ni cooldown
    possible, ni accumulation de streak -- ce round-ci.
    """
    scenario_state = usage_state.setdefault(scenario_slug, {})
    counts = scenario_state.setdefault("instances", {})
    streaks = scenario_state.setdefault("streaks", {})
    cooldowns = scenario_state.setdefault("cooldowns", {})

    exempt_slug = None
    if len(candidates) >= 2:
        top_score, second_score = sorted(
            (pair[0] for pair in candidates), reverse=True
        )[:2]
        if top_score - second_score >= DOMINANCE_EXEMPTION_GAP:
            exempt_slug = next(
                inst["slug"] for score, inst in candidates if score == top_score
            )
            cooldowns[exempt_slug] = 0  # lève un cooldown résiduel éventuel

    eligibles, en_cooldown = [], []
    for pair in candidates:
        slug = pair[1]["slug"]
        if slug == exempt_slug or cooldowns.get(slug, 0) <= 0:
            eligibles.append(pair)
        else:
            en_cooldown.append(pair)

    if len(eligibles) <= max_n:
        selected = list(eligibles)
    else:
        shuffled = list(eligibles)
        random.shuffle(shuffled)
        max_score = max(pair[0] for pair in eligibles)
        # Tri stable : tranche de score croissante d'abord (0 = tranche
        # la plus haute, priorité à la pertinence), nombre d'utilisations
        # passées ensuite (départage les ex-aequo au sein d'une même
        # tranche).
        shuffled.sort(key=lambda pair: counts.get(pair[1]["slug"], 0))
        shuffled.sort(key=lambda pair: _score_bucket(pair[0], max_score))
        selected = shuffled[:max_n]

    selected_slugs = {inst["slug"] for _, inst in selected}

    # Décompte du cooldown pour les candidates qui en étaient captives ce
    # round -- décrémenté uniquement quand l'instance était candidate
    # (pas en temps réel absolu, cohérent avec le fait que cette
    # fonction n'est appelée que lorsqu'une instance est pertinente pour
    # une thématique).
    for _, inst in en_cooldown:
        slug = inst["slug"]
        cooldowns[slug] = max(0, cooldowns.get(slug, 0) - 1)

    # Mise à jour streak/compteur/déclenchement du cooldown pour les
    # candidates éligibles ce round -- sauf l'exemptée, qui n'accumule
    # jamais de streak.
    for pair in eligibles:
        slug = pair[1]["slug"]
        if slug == exempt_slug:
            if slug in selected_slugs:
                counts[slug] = counts.get(slug, 0) + 1
            continue
        if slug in selected_slugs:
            counts[slug] = counts.get(slug, 0) + 1
            streaks[slug] = streaks.get(slug, 0) + 1
            if streaks[slug] >= COOLDOWN_STREAK:
                cooldowns[slug] = COOLDOWN_DURATION
                streaks[slug] = 0
        else:
            streaks[slug] = 0

    return [inst for _, inst in selected]


def _select_with_custom_guarantee(scored, scenario_slug, dry_run, max_n):
    """
    Garantie d'inclusion des instances custom (backlog Partie 3, risque
    identifié le 3 août 2026, corrigé le 21 août 2026).

    Risque comblé : snapshot.py (apply_custom_injections) applique
    TOUJOURS les deltas de variables d'une instance custom, sans
    filtrage -- mais jusqu'ici, sa description ne parvenait au LLM que
    si elle survivait au même filtrage par pertinence thématique que
    n'importe quelle instance du socle (filter_instances_for_thematique
    / select_instances_by_impact). Une instance custom avec un score de
    pertinence faible pour la thématique en cours (peu de recoupement
    variables/zone) pouvait donc influencer le monde sans jamais être
    décrite -- décalage entre "ce qui bouge les chiffres" et "ce que le
    LLM voit".

    Principe : sépare scored (liste de tuples (score, inst)) en
    instances custom (injection.type == "custom") et non-custom. Les
    custom obtiennent une place garantie dans la limite de max_n --
    si elles sont plus nombreuses que de places disponibles, priorité
    entre elles par score décroissant (cas non rencontré à ce jour,
    vault à zéro instance custom au 21 août 2026, mais pas exclu à
    l'avenir). Les places restantes vont aux non-custom, via la même
    rotation à mémoire qu'avant ce correctif (_select_least_used_
    instances) si scenario_slug est fourni, sinon un tri déterministe
    simple (repli legacy, inchangé).

    NON-RÉGRESSION : si aucune instance custom n'est présente dans
    scored (cas de tout le vault au moment de ce correctif), le
    comportement est STRICTEMENT identique à avant -- max_n places
    toutes disputées par les non-custom, même rotation, même tri.
    """
    def _est_garanti(inst):
        # 22 août 2026 : élargi de la garantie custom (21 août) au flag
        # priorite_forcee -- deux portes d'entrée différentes vers le
        # même pool garanti (édition manuelle d'une instance existante,
        # ou case à cocher à la création). Une instance priorite_forcee
        # échappe de fait à la rotation _select_least_used_instances
        # (jamais dans noncustom ci-dessous) -- aucun conflit avec la
        # pénalité d'usage qui y est appliquée.
        #
        # 23 août 2026 : injection.garantie_selection (défaut true si
        # absent -- AUCUNE régression sur les instances custom
        # existantes) permet de découpler la garantie de présence de la
        # propagation d'impact sur les variables (apply_custom_injections,
        # snapshot.py, qui ne regarde QUE injection.type == "custom",
        # jamais ce nouveau flag -- une instance peut donc continuer
        # d'influencer la simulation du monde tout en perdant sa
        # garantie de présence dans les articles). Cas d'usage réel :
        # gelecek_meclisi, injectée en 2047 sur 4 scénarios, devenue
        # quasi-omniprésente (jusqu'à 98% des articles new_sustainability)
        # -- la garantie initiale n'avait plus de raison d'être des
        # années plus tard, mais son effet causal sur gouvernance_
        # institutions/technologie_information/organisation_territoires
        # devait être préservé.
        injection = inst.get("injection", {})
        return (
            (injection.get("type") == "custom"
             and injection.get("garantie_selection", True) is not False)
            or inst.get("priorite_forcee") is True
        )

    custom = sorted(
        [(s, i) for s, i in scored if _est_garanti(i)],
        key=lambda x: -x[0]
    )
    noncustom = [(s, i) for s, i in scored if not _est_garanti(i)]

    guaranteed = custom[:max_n]
    if len(custom) > max_n:
        exclues = ", ".join(i.get("slug", "?") for _, i in custom[max_n:])
        print("[loader] [WARN] {} instances custom en lice pour {} emplacement(s) "
              "garanti(s) -- {} exclue(s) malgré la garantie (priorité au score) : "
              "{}".format(len(custom), max_n, len(custom) - max_n, exclues))
    if guaranteed:
        noms = ", ".join(i.get("slug", "?") for _, i in guaranteed)
        print("[loader] Instance(s) custom garantie(s) dans filtered_instances : {}".format(noms))

    remaining = max_n - len(guaranteed)
    if remaining > 0 and noncustom:
        if scenario_slug:
            usage_state = _load_instance_usage_state()
            selected_noncustom = _select_least_used_instances(
                noncustom, usage_state, scenario_slug, remaining
            )
            if not dry_run:
                _save_instance_usage_state(usage_state)
        else:
            noncustom.sort(key=lambda x: -x[0])
            selected_noncustom = [inst for _, inst in noncustom[:remaining]]
    else:
        selected_noncustom = []

    result = [inst for _, inst in guaranteed] + selected_noncustom
    # Tri final par score décroissant -- ordre d'affichage cohérent
    # (les plus pertinentes/impactantes en tête), même esprit que le tri
    # déjà en place avant ce correctif.
    score_by_slug = {i["slug"]: s for s, i in scored if i.get("slug")}
    result.sort(key=lambda inst: -score_by_slug.get(inst.get("slug", ""), 0))
    return result


def select_instances_by_impact(instances, scenario_slug, dry_run=True, max_n=6):
    """
    Sélection des instances quand aucune thématique n'est fournie (repli
    utilisé par snapshot.py) -- même rotation à mémoire que
    filter_instances_for_thematique() ci-dessous, sur le score
    impact_systemique_global plutôt qu'un score de pertinence thématique.

    Garantie d'inclusion des instances custom ajoutée le 21 août 2026 --
    voir _select_with_custom_guarantee().
    """
    scored = [(inst.get("impact_systemique_global", 0), inst) for inst in instances]
    return _select_with_custom_guarantee(scored, scenario_slug, dry_run, max_n)


# ─────────────────────────────────────────
# PERTINENCE DES ÉVÉNEMENTS CUSTOM (ajouté le 2 août 2026)
# ─────────────────────────────────────────
#
# Jusqu'ici, TOUS les événements custom d'un scénario étaient inclus dans
# chaque article généré pour ce scénario, sans filtre -- ni pertinence
# thématique, ni plafond. Ça grossit indéfiniment à mesure que le vault
# grandit (13 événements aujourd'hui pour un scénario, sans limite prévue).
# Réutilise le même matériau déjà standardisé sur les fiches (voir
# VALID_PORTEES dans inject_custom_events.py) plutôt que d'inventer une
# nouvelle heuristique : portée (locale→globale), amplitude réelle des
# impact_sur_variables (delta_level, propre à ce scénario -- plus précis
# que l'intensité qualitative de l'archétype, qui n'est de toute façon
# jamais reportée sur la fiche instance), et recoupement avec les
# variables de la thématique -- exactement le même principe que
# filter_instances_for_thematique() ci-dessous pour les instances.

PORTEE_RANK = {"locale": 1, "regionale": 2, "continentale": 3, "globale": 4}

EVENT_STATE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
EVENT_USAGE_FILE = os.path.join(EVENT_STATE_DIR, "event_relevance_usage.json")


def _load_event_usage_state():
    try:
        with open(EVENT_USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_event_usage_state(state):
    os.makedirs(EVENT_STATE_DIR, exist_ok=True)
    with open(EVENT_USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def _score_evenement_pertinence(event, vars_vis, vars_sec):
    """Score de pertinence d'un événement custom -- même logique que le
    score des instances (variables_visibles pèsent plus que
    variables_secondaires), plus la portée et l'amplitude réelle des
    impacts sur les variables pour ce scénario précis."""
    score = 0
    event_vars = {imp.get("variable") for imp in (event.get("impacts") or []) if isinstance(imp, dict)}
    score += len(event_vars & vars_vis) * 3
    score += len(event_vars & vars_sec) * 1
    score += PORTEE_RANK.get(event.get("portee", "locale"), 1) * 1.5
    amplitude = sum(abs(imp.get("delta_level", 0)) for imp in (event.get("impacts") or []) if isinstance(imp, dict))
    score += min(amplitude, 40) * 0.1  # plafonné pour éviter qu'un seul événement à fort delta écrase tout le reste
    return score


def select_relevant_events(events, thematique, scenario_slug, forced_event_slug=None,
                            max_events=8, dry_run=True):
    """
    Sélectionne au plus max_events événements custom parmi ceux d'un
    scénario, par pertinence thématique + rotation à mémoire (même
    principe que _select_least_used_instances). L'événement forcé (mode
    "forcer" de generate.py), s'il y en a un, est TOUJOURS inclus en plus
    du plafond -- jamais soumis au tri, jamais évincé.

    thematique=None (pas de thématique fournie) : trie par portée +
    amplitude seules, sans le terme de recoupement variables.
    """
    if not events:
        return []

    forced = None
    reste = list(events)
    if forced_event_slug:
        forced = next((e for e in reste if e.get("slug") == forced_event_slug
                       or e.get("archetype") == forced_event_slug), None)
        if forced:
            # Bug corrigé le 3 août 2026 (retour de David, test réel sur
            # encheres_terres_rares_groenland/policy_reform) : l'événement
            # forcé était bien placé en tête de la liste retournée, mais
            # jamais marqué comme tel -- prompt_builder.py lit ev.get(
            # "forced") pour afficher le badge [FORCÉ], qui restait donc
            # toujours absent. On recrée un dict pour ne pas muter l'objet
            # original (potentiellement réutilisé ailleurs dans le pipeline,
            # ex. rotation à mémoire ou un futur appel avec un autre
            # forced_event_slug sur la même liste source).
            forced = dict(forced)
            forced["forced"] = True
            reste = [e for e in reste if e.get("slug") != forced.get("slug")
                     and e.get("archetype") != forced.get("archetype")]

    if thematique:
        vars_vis = set(thematique.get("variables_visibles", []))
        vars_sec = set(thematique.get("variables_secondaires", []))
    else:
        vars_vis, vars_sec = set(), set()

    plafond_restant = max_events - (1 if forced else 0)
    if plafond_restant < 0:
        plafond_restant = 0

    scored = [(_score_evenement_pertinence(e, vars_vis, vars_sec), e) for e in reste]

    if len(scored) <= plafond_restant:
        selected = [e for _, e in scored]
    else:
        usage_state = _load_event_usage_state()
        counts = usage_state.setdefault(scenario_slug, {})
        shuffled = list(scored)
        random.shuffle(shuffled)
        shuffled.sort(key=lambda pair: counts.get(pair[1]["slug"], 0))
        shuffled.sort(key=lambda pair: -pair[0])
        selected = [e for _, e in shuffled[:plafond_restant]]
        for e in selected:
            counts[e["slug"]] = counts.get(e["slug"], 0) + 1
        if not dry_run:
            _save_event_usage_state(usage_state)

    return ([forced] if forced else []) + selected


def filter_instances_for_thematique(instances, thematique, scenario_slug=None, dry_run=True):
    """
    Filtre les instances pertinentes pour une thématique donnée.

    Critères de pertinence (par ordre de priorité) :
      1. variables_influencees intersecte variables_visibles → très pertinent
      2. variables_influencees intersecte variables_secondaires → pertinent
      3. zone_systemique intersecte les domaines de la thématique → pertinent

    Retourne au plus MAX_INSTANCES instances. Au-delà de ce plafond, les
    ex-aequo de score sont départagés par rotation à mémoire (voir
    _select_least_used_instances ci-dessus, ajouté le 2 août 2026) plutôt
    que par un simple tri déterministe -- pour qu'une instance pertinente
    mais rarement en tête ait quand même une chance de sortir sur la
    durée. Nécessite scenario_slug pour compter l'usage par scénario ;
    sans lui, repli sur l'ancien comportement (top-N par score, sans
    rotation). dry_run=True (défaut) ne persiste pas l'incrément d'usage
    -- à mettre à False uniquement lors d'une génération réelle, jamais
    en aperçu/dry-run, sous peine de fausser la rotation avec des
    sélections qui n'ont jamais servi.
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

        # Exclure les instances sans pertinence -- SAUF une instance
        # custom à score nul (21 août 2026, backlog Partie 3) ou une
        # instance priorite_forcee (22 août 2026), qui restent
        # candidates à la garantie d'inclusion ci-dessous plutôt que
        # d'être écartées avant même d'y arriver. Sans l'un ou l'autre
        # cas (situation de tout le vault au 21 août), comportement
        # inchangé.
        #
        # 23 août 2026 : is_custom tient compte de
        # injection.garantie_selection (défaut true, voir _est_garanti
        # dans _select_with_custom_guarantee ci-dessus pour le contexte
        # complet) -- une instance custom avec garantie_selection: false
        # n'est plus exemptée de l'exclusion à score nul, exactement
        # comme une instance canonique.
        injection = inst.get("injection", {})
        is_custom = (injection.get("type") == "custom"
                     and injection.get("garantie_selection", True) is not False)
        is_priorite_forcee = inst.get("priorite_forcee") is True
        if score > 0 or is_custom or is_priorite_forcee:
            scored.append((score, inst))

    # Rotation à mémoire (ajouté le 2 août 2026) : au-delà de MAX_INSTANCES
    # candidates pertinentes, on ne garde plus bêtement les MAX_INSTANCES
    # premières par score -- la rotation départage les ex-aequo de score
    # en faveur des instances les moins utilisées jusqu'ici pour ce
    # scénario, pour qu'une instance pertinente mais rarement la plus
    # pertinente finisse quand même par sortir sur un grand corpus
    # d'articles. Sans scenario_slug (appel legacy), repli sur
    # l'ancien comportement déterministe -- pas de rotation possible sans
    # savoir sous quel scénario compter l'usage.
    #
    # Garantie d'inclusion des instances custom ajoutée le 21 août 2026
    # -- voir _select_with_custom_guarantee(). Sans instance custom,
    # comportement STRICTEMENT identique à avant ce correctif.
    return _select_with_custom_guarantee(scored, scenario_slug, dry_run, MAX_INSTANCES)

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
        print("  trajectoire      :", inst["trajectoire"])
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
