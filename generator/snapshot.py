"""
snapshot.py
-----------
Construit le snapshot cohérent du monde 2098 pour un scénario donné.

Étapes :
  1. Charge le scénario → identifie les variables pilotes
  2. Pour chaque variable → extrait son état dans ce scénario
  3. Via la matrice → vérifie la cohérence des propagations
  4. Extrait les ruptures et jalons 2025→2098
  5. Retourne un snapshot complet prêt pour prompt_builder.py
"""

import re

from loader import (
    load_scenario,
    load_variable,
    load_influence_matrix,
    load_all_variables,
    load_instances_for_scenario,
    load_events_for_scenario,
    filter_instances_for_thematique,
    VALID_VARS,
    VALID_SCENARIOS,
)


# ─────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────

# Seuil pour identifier un lien comme structurant
STRONG_WEIGHT = 0.75
CASCADE_ROLES = {"cascade", "reinforcing"}

# Catégories de ruptures à extraire pour la trajectoire
RUPTURE_CATEGORIES = ["technological", "systemic", "political_social"]


# ─────────────────────────────────────────
# ÉTAPE 1 — VARIABLES PILOTES
# ─────────────────────────────────────────

# ─────────────────────────────────────────
# ÉTAPE 4B — TRAJECTOIRE SIGNAL_TO_STATE
# ─────────────────────────────────────────

def build_signal_trajectory(all_variables, scenario_slug, pilot_variables):
    """
    Construit la trajectoire historique à partir des signal_to_state.

    Pour chaque variable, extrait les évolutions de signaux
    pour le scénario donné, puis :
      - Regroupe les événements clés datés
      - Identifie les événements partagés (même evenement_cle)
      - Classe par importance (variables pilotes en priorité)

    Retourne une liste d'événements historiques :
    [
      {
        "evenement_cle" : str  — nom de l'événement daté
        "date_bascule"  : str  — fenêtre temporelle ex: "2041-2058"
        "date_debut"    : int  — année de début (pour tri chronologique)
        "evolutions"    : list — descriptions des évolutions par variable
        "variables"     : list — variables concernées
        "is_pilot"      : bool — implique une variable pilote
        "scope"         : str  — "majeur" | "structurant" | "local"
      }
    ]
    """
    from loader import get_signal_to_state_for_scenario

    pilot_set = set(pilot_variables)

    # Collecter tous les événements clés par variable
    event_pool = {}  # evenement_cle → données agrégées

    for var_slug, var in all_variables.items():
        signals = get_signal_to_state_for_scenario(var, scenario_slug)
        for sig in signals:
            ev_key = sig["evenement_cle"].strip().lower()
            if not ev_key:
                continue

            if ev_key not in event_pool:
                event_pool[ev_key] = {
                    "evenement_cle": sig["evenement_cle"],
                    "date_bascule":  sig["date_bascule"],
                    "evolutions":    [],
                    "variables":     [],
                    "signals":       [],
                }

            # Ajouter l'évolution de cette variable
            if var_slug not in event_pool[ev_key]["variables"]:
                event_pool[ev_key]["variables"].append(var_slug)
                event_pool[ev_key]["evolutions"].append({
                    "variable":  var_slug,
                    "signal":    sig["signal"],
                    "evolution": sig["evolution"],
                })
                event_pool[ev_key]["signals"].append(sig["signal"])

            # Garder la date_bascule la plus précise
            if sig["date_bascule"] and not event_pool[ev_key]["date_bascule"]:
                event_pool[ev_key]["date_bascule"] = sig["date_bascule"]

    # Classifier et scorer
    events = []
    for ev_key, data in event_pool.items():
        variables = data["variables"]
        nb_vars   = len(variables)
        is_pilot  = any(v in pilot_set for v in variables)

        # Majeur : partagé entre 3+ variables, OU partagé entre 2+ avec pilote,
        # OU implique une variable pilote (événement structurant du scénario)
        if nb_vars >= 3:
            scope = "majeur"
        elif nb_vars >= 2 and is_pilot:
            scope = "majeur"
        elif is_pilot:
            scope = "majeur"
        elif nb_vars == 2:
            scope = "structurant"
        else:
            scope = "local"

        # Extraire l'année de début pour tri chronologique
        date_bascule = data["date_bascule"]
        date_debut = 2025
        m = re.search(r"(\d{4})", date_bascule)
        if m:
            date_debut = int(m.group(1))

        events.append({
            "evenement_cle": data["evenement_cle"],
            "date_bascule":  date_bascule,
            "date_debut":    date_debut,
            "evolutions":    data["evolutions"],
            "variables":     variables,
            "signals":       data["signals"],
            "is_pilot":      is_pilot,
            "scope":         scope,
        })

    # Trier : scope > is_pilot > chronologique
    order = {"majeur": 0, "structurant": 1, "local": 2}
    events.sort(key=lambda x: (
        order[x["scope"]],
        0 if x["is_pilot"] else 1,
        x["date_debut"],
    ))

    return events


def get_pilot_variables(scenario):
    """
    Identifie les variables pilotes du scénario.
    Ordre de priorité :
      1. dominant_variables (définies dans la fiche scénario)
      2. reinforced_variables
    Retourne une liste ordonnée par influence décroissante.
    """
    dominant   = scenario.get("dominant_variables", [])
    reinforced = scenario.get("reinforced_variables", [])

    # Dédupliquer en gardant l'ordre
    seen = set()
    pilots = []
    for v in dominant + reinforced:
        if v in VALID_VARS and v not in seen:
            seen.add(v)
            pilots.append(v)

    return pilots


# ─────────────────────────────────────────
# ÉTAPE 2 — ÉTAT DE CHAQUE VARIABLE
# ─────────────────────────────────────────

def get_variable_state(variable, scenario_slug):
    """
    Extrait l'état d'une variable pour un scénario donné.
    Source prioritaire : fiche variable (state_logic riche)
    Source secondaire  : variable_states de la fiche scénario (level + trend)
    """
    states = variable.get("states", {})

    if scenario_slug in states:
        state = states[scenario_slug]
        return {
            "slug":              variable["slug"],
            "variable_type":     variable.get("variable_type", ""),
            "level":             state.get("level", ""),
            "volatility":        state.get("volatility", ""),
            "state_logic":       state.get("state_logic", ""),
            "dominant_dynamics": state.get("dominant_dynamics", []),
            "system_role_shift": state.get("system_role_shift", []),
            "coupling_intensity":state.get("coupling_intensity", {}),
            "source":            "variable_fiche",
        }

    # Fallback : pas de state_logic dans la fiche variable
    return {
        "slug":              variable["slug"],
        "variable_type":     variable.get("variable_type", ""),
        "level":             "",
        "volatility":        "",
        "state_logic":       "État non défini pour ce scénario.",
        "dominant_dynamics": [],
        "system_role_shift": [],
        "coupling_intensity":{},
        "source":            "undefined",
    }


# ─────────────────────────────────────────
# ÉTAPE 3 — COHÉRENCE VIA MATRICE
# ─────────────────────────────────────────

def check_coherence(variable_states, matrix):
    """
    Vérifie la cohérence des états via la matrice d'influence.
    Pour chaque paire (source, target) avec weight fort :
      - Si polarity -1 et les deux variables ont level élevé → tension détectée
      - Si polarity +1 et écart de level > 40 → incohérence potentielle

    Retourne :
      - tensions     : list de dicts (conflits détectés)
      - coherence_ok : bool (False si incohérences majeures)
    """
    tensions = []
    by_pair  = matrix["by_pair"]

    for source_slug, source_state in variable_states.items():
        for target_slug, target_state in variable_states.items():
            if source_slug == target_slug:
                continue

            edge = by_pair.get((source_slug, target_slug))
            if not edge:
                continue
            if edge["weight"] < STRONG_WEIGHT:
                continue

            s_level = source_state.get("level", "")
            t_level = target_state.get("level", "")

            if s_level == "" or t_level == "":
                continue

            s_level = float(s_level)
            t_level = float(t_level)

            # Tension : lien négatif fort entre deux variables à niveau élevé
            if edge["polarity"] == -1 and s_level > 60 and t_level > 60:
                tensions.append({
                    "type":          "tension_negative",
                    "source":        source_slug,
                    "target":        target_slug,
                    "weight":        edge["weight"],
                    "feedback_role": edge["feedback_role"],
                    "lag":           edge["lag"],
                    "description":   "{} (level {}) exerce une pression négative forte sur {} (level {})".format(
                        source_slug, int(s_level), target_slug, int(t_level)
                    ),
                })

            # Cascade critique : lien cascade + polarity -1 + lag court
            if (edge["feedback_role"] == "cascade"
                    and edge["polarity"] == -1
                    and edge["lag"] <= 2
                    and s_level > 70):
                tensions.append({
                    "type":          "cascade_critique",
                    "source":        source_slug,
                    "target":        target_slug,
                    "weight":        edge["weight"],
                    "feedback_role": "cascade",
                    "lag":           edge["lag"],
                    "description":   "CASCADE CRITIQUE : {} déclenche une cascade rapide sur {}".format(
                        source_slug, target_slug
                    ),
                })

    # Dédupliquer : une seule tension par paire (source, target)
    # Priorité : cascade_critique > tension_negative
    seen_pairs = {}
    for t in tensions:
        pair = (t["source"], t["target"])
        if pair not in seen_pairs:
            seen_pairs[pair] = t
        else:
            # Garder cascade_critique en priorité
            if t["type"] == "cascade_critique":
                seen_pairs[pair] = t

    unique_tensions = list(seen_pairs.values())

    # Trier par weight décroissant
    unique_tensions.sort(key=lambda x: -x["weight"])

    coherence_ok = len([t for t in unique_tensions if t["type"] == "cascade_critique"]) < 5

    return {
        "tensions":     unique_tensions,
        "coherence_ok": coherence_ok,
    }


# ─────────────────────────────────────────
# ÉTAPE 4 — TRAJECTOIRE 2025 → 2098
# ─────────────────────────────────────────

def build_trajectory(all_variables, scenario_slug, pilot_variables):
    """
    Construit les jalons de la trajectoire 2025 -> 2098.

    Logique :
      - Extrait les ruptures core ET extended de TOUTES les variables
      - Identifie les recoupements semantiques (mots-cles communs)
        entre ruptures de variables differentes
      - Classe par scope selon le nombre de variables touchees
      - Priorise les jalons impliquant des variables pilotes

    Chaque jalon :
      {
        "type"      : "technological" | "systemic" | "political_social"
        "content"   : str description de la rupture
        "variables" : list des variables concernees
        "scope"     : "majeur" | "structurant" | "local"
        "is_pilot"  : bool -- implique au moins une variable pilote
        "is_core"   : bool -- rupture core (vs extended)
      }
    """
    pilot_set = set(pilot_variables)

    # Etape 1 : collecter toutes les ruptures (core + extended) de toutes les variables
    rupture_pool = {}

    for var_slug, var in all_variables.items():
        ruptures = var.get("ruptures", {})
        if not isinstance(ruptures, dict):
            continue

        for category in RUPTURE_CATEGORIES:
            cat_data = ruptures.get(category, {})
            if not isinstance(cat_data, dict):
                continue

            for level in ["core", "extended"]:
                items = cat_data.get(level, [])
                if not isinstance(items, list):
                    continue
                for item in items:
                    item_str = str(item).strip()
                    if not item_str:
                        continue

                    key = (category, item_str.lower())
                    if key not in rupture_pool:
                        rupture_pool[key] = {
                            "type":      category,
                            "content":   item_str,
                            "variables": [],
                            "level":     level,
                        }
                    if var_slug not in rupture_pool[key]["variables"]:
                        rupture_pool[key]["variables"].append(var_slug)
                    # Promouvoir en core si besoin
                    if level == "core":
                        rupture_pool[key]["level"] = "core"

    # Etape 2 : regroupement semantique par mots-cles (>= 5 chars)
    keyword_index = {}
    for key, data in rupture_pool.items():
        words = re.findall(r'\b\w{5,}\b', data["content"].lower())
        for word in words:
            keyword_index.setdefault(word, []).append(key)

    # Fusionner les ruptures liees semantiquement
    merged = {}
    processed = set()

    for key, data in rupture_pool.items():
        if key in processed:
            continue

        content   = data["content"]
        variables = set(data["variables"])
        category  = data["type"]
        level     = data["level"]

        words = re.findall(r'\b\w{5,}\b', content.lower())
        for word in words:
            for rkey in keyword_index.get(word, []):
                if rkey == key or rkey in processed:
                    continue
                rdata = rupture_pool[rkey]
                if rdata["type"] == category:
                    for v in rdata["variables"]:
                        variables.add(v)
                    if rdata["level"] == "core":
                        level = "core"

        processed.add(key)

        canonical = content.lower()
        if canonical not in merged:
            merged[canonical] = {
                "type":      category,
                "content":   content,
                "variables": list(variables),
                "level":     level,
            }
        else:
            existing = set(merged[canonical]["variables"])
            merged[canonical]["variables"] = list(existing | variables)
            if level == "core":
                merged[canonical]["level"] = "core"

    # Etape 3 : classifier et scorer
    jalons = []
    for content_key, data in merged.items():
        variables = data["variables"]
        nb_vars   = len(variables)
        is_pilot  = any(v in pilot_set for v in variables)
        is_core   = data["level"] == "core"

        if nb_vars >= 3 or (nb_vars >= 2 and is_pilot and is_core):
            scope = "majeur"
        elif nb_vars == 2 or (is_pilot and is_core):
            scope = "structurant"
        else:
            scope = "local"

        jalons.append({
            "type":      data["type"],
            "content":   data["content"],
            "variables": variables,
            "scope":     scope,
            "is_pilot":  is_pilot,
            "is_core":   is_core,
        })

    # Etape 4 : trier par scope > is_pilot > is_core > nb_variables
    order = {"majeur": 0, "structurant": 1, "local": 2}
    jalons.sort(key=lambda x: (
        order[x["scope"]],
        0 if x["is_pilot"] else 1,
        0 if x["is_core"] else 1,
        -len(x["variables"]),
    ))

    return jalons


# ─────────────────────────────────────────
# ÉTAPE 6B — APPLICATION DES INJECTIONS CUSTOM
# ─────────────────────────────────────────

def apply_custom_injections(variable_states, instances, matrix):
    """
    Applique les deltas des entités custom injectées sur les variables.

    Pour chaque instance custom (injection.type == "custom") :
      1. Calcule la durée d'effet réelle (2098 - annee_injection)
      2. Pondère le delta par min(duree_effet, duree_declaree) / duree_declaree
      3. Applique le delta au level de la variable
      4. Si propagation.via_matrice = true, propage via les edges forts

    Retourne les variable_states modifiés + un log des modifications.
    """
    modifications = []
    states = {k: dict(v) for k, v in variable_states.items()}

    for inst in instances:
        injection = inst.get("injection", {})
        if not injection or injection.get("type") != "custom":
            continue

        annee = injection.get("annee_injection")
        if not annee:
            continue

        duree_effet = 2098 - int(annee)
        via_matrice = injection.get("propagation", {}).get("via_matrice", False)
        impacts     = injection.get("impact_sur_variables", []) or []

        if not impacts:
            continue

        print("[snapshot] Injection custom '{}' (an {}, {} ans d'effet)".format(
            inst["name"], annee, duree_effet
        ))

        for impact in impacts:
            var       = impact.get("variable", "")
            delta     = impact.get("delta_level", 0)
            duree_dec = impact.get("duree", duree_effet)
            polarite  = impact.get("polarite", 1)

            if var not in states:
                continue

            # Pondération temporelle
            facteur        = min(duree_effet, duree_dec) / max(duree_dec, 1)
            delta_applique = round(delta * facteur * polarite, 1)

            old_level = states[var].get("level", 50)
            if old_level == "" or old_level is None:
                old_level = 50

            new_level = max(0, min(100, float(old_level) + delta_applique))
            states[var]["level"]               = round(new_level, 1)
            states[var]["custom_perturbation"] = True
            states[var]["perturbation_source"] = inst["name"]

            modifications.append({
                "instance":  inst["name"],
                "variable":  var,
                "delta":     delta_applique,
                "old_level": old_level,
                "new_level": new_level,
            })
            print("  → {} : {} → {} (delta:{:+})".format(
                var, old_level, new_level, delta_applique
            ))

            # Propagation via matrice
            if via_matrice and matrix:
                edges = matrix["by_source"].get(var, [])
                for edge in edges:
                    if edge["weight"] < 0.75:
                        continue
                    target     = edge["target"]
                    prop_delta = round(
                        delta_applique * edge["weight"] * edge["polarity"] * 0.5, 1
                    )
                    if target not in states:
                        continue
                    old_t = states[target].get("level", 50)
                    if old_t == "" or old_t is None:
                        old_t = 50
                    new_t = max(0, min(100, float(old_t) + prop_delta))
                    states[target]["level"]               = round(new_t, 1)
                    states[target]["custom_perturbation"] = True
                    states[target]["perturbation_source"] = "{} (propagé)".format(inst["name"])
                    modifications.append({
                        "instance":  inst["name"] + " (propagé)",
                        "variable":  target,
                        "delta":     prop_delta,
                        "old_level": old_t,
                        "new_level": new_t,
                    })

    return states, modifications


def apply_custom_events(variable_states, events, matrix):
    """
    Applique les deltas des événements custom sur les variables.
    Similaire à apply_custom_injections mais pour les événements.

    Retourne les variable_states modifiés + un log des modifications.
    """
    modifications = []
    states = {k: dict(v) for k, v in variable_states.items()}

    for event in events:
        annee       = event.get("date", 2050)
        impacts     = event.get("impacts", []) or []
        via_matrice = event.get("via_matrice", False)

        if not impacts:
            continue

        duree_effet = 2098 - int(annee)
        print("[snapshot] Événement custom '{}' (an {}, {} ans d'effet)".format(
            event["name"], annee, duree_effet
        ))

        for impact in impacts:
            var       = impact.get("variable", "")
            delta     = impact.get("delta_level", 0)
            duree_dec = impact.get("duree", duree_effet)
            polarite  = impact.get("polarite", 1)

            if var not in states:
                continue

            facteur        = min(duree_effet, duree_dec) / max(duree_dec, 1)
            delta_applique = round(delta * facteur * polarite, 1)

            old_level = states[var].get("level", 50)
            if old_level == "" or old_level is None:
                old_level = 50

            new_level = max(0, min(100, float(old_level) + delta_applique))
            states[var]["level"]             = round(new_level, 1)
            states[var]["event_perturbation"] = True
            states[var]["event_source"]       = event["name"]

            modifications.append({
                "event":     event["name"],
                "date":      annee,
                "variable":  var,
                "delta":     delta_applique,
                "old_level": old_level,
                "new_level": new_level,
            })
            print("  → {} : {} → {} (delta:{:+})".format(
                var, old_level, new_level, delta_applique
            ))

            # Propagation via matrice
            if via_matrice and matrix:
                edges = matrix["by_source"].get(var, [])
                for edge in edges:
                    if edge["weight"] < 0.75:
                        continue
                    target     = edge["target"]
                    prop_delta = round(
                        delta_applique * edge["weight"] * edge["polarity"] * 0.5, 1
                    )
                    if target not in states:
                        continue
                    old_t = states[target].get("level", 50)
                    if old_t == "" or old_t is None:
                        old_t = 50
                    new_t = max(0, min(100, float(old_t) + prop_delta))
                    states[target]["level"]              = round(new_t, 1)
                    states[target]["event_perturbation"] = True
                    states[target]["event_source"]       = "{} (propagé)".format(event["name"])
                    modifications.append({
                        "event":     event["name"] + " (propagé)",
                        "date":      annee,
                        "variable":  target,
                        "delta":     prop_delta,
                        "old_level": old_t,
                        "new_level": new_t,
                    })

    return states, modifications


def get_thematic_tensions(thematique, matrix, variable_states):
    """
    Extrait les tensions les plus pertinentes pour une thématique donnée.
    Filtre les edges entre les variables visibles de la thématique
    et croise avec les cascades détectées dans le snapshot.
    """
    vars_vis = thematique.get("variables_visibles", [])
    vars_all = vars_vis + thematique.get("variables_secondaires", [])
    var_set  = set(v for v in vars_all if v in VALID_VARS)

    relevant_edges = []
    for edge in matrix["edges"]:
        if edge["source"] in var_set and edge["target"] in var_set:
            if edge["weight"] >= STRONG_WEIGHT:
                relevant_edges.append(edge)

    # Enrichir avec les niveaux actuels
    enriched = []
    for edge in relevant_edges:
        source_state = variable_states.get(edge["source"], {})
        target_state = variable_states.get(edge["target"], {})
        enriched.append({
            **edge,
            "source_level": source_state.get("level", ""),
            "target_level": target_state.get("level", ""),
        })

    # Trier par impact (weight × temporal_weight)
    enriched.sort(key=lambda x: -(x["weight"] * x["temporal_weight"]))

    return enriched[:8]  # Top 8 tensions pertinentes


# ─────────────────────────────────────────
# FONCTION PRINCIPALE
# ─────────────────────────────────────────

def build_snapshot(scenario_slug, thematique=None):
    """
    Fonction principale — construit le snapshot complet du monde 2098.

    Args:
        scenario_slug : str — slug du scénario (ex: "breakdown")
        thematique    : dict — fiche thématique chargée (optionnel)

    Retourne un dict complet prêt pour prompt_builder.py
    """
    print("\n[snapshot] Construction du monde 2098 — scénario : {}".format(scenario_slug))

    # Charger les données de base
    scenario      = load_scenario(scenario_slug)
    all_variables = load_all_variables()
    matrix        = load_influence_matrix()

    # ── Étape 1 : variables pilotes
    pilots = get_pilot_variables(scenario)
    print("[snapshot] Variables pilotes : {}".format(pilots))

    # ── Étape 2 : état de toutes les variables
    variable_states = {}
    for var_slug in VALID_VARS:
        var = all_variables[var_slug]
        variable_states[var_slug] = get_variable_state(var, scenario_slug)

    defined = sum(1 for s in variable_states.values() if s["source"] != "undefined")
    print("[snapshot] États définis : {}/{}".format(defined, len(VALID_VARS)))

    # ── Étape 3 : cohérence
    coherence = check_coherence(variable_states, matrix)
    print("[snapshot] Tensions détectées : {} | Cohérence : {}".format(
        len(coherence["tensions"]),
        "OK" if coherence["coherence_ok"] else "ATTENTION"
    ))

    # ── Étape 4 : trajectoire ruptures (jalons génériques)
    trajectory = build_trajectory(all_variables, scenario_slug, pilots)
    majors = [j for j in trajectory if j["scope"] == "majeur"]
    print("[snapshot] Jalons trajectoire : {} ({} majeurs)".format(
        len(trajectory), len(majors)
    ))

    # ── Étape 4B : trajectoire signal_to_state (événements datés)
    signal_events = build_signal_trajectory(all_variables, scenario_slug, pilots)
    signal_majors = [e for e in signal_events if e["scope"] == "majeur"]
    print("[snapshot] Événements signal_to_state : {} ({} majeurs)".format(
        len(signal_events), len(signal_majors)
    ))

    # ── Étape 5 : tensions thématiques (si thématique fournie)
    thematic_tensions = []
    if thematique:
        thematic_tensions = get_thematic_tensions(thematique, matrix, variable_states)
        print("[snapshot] Tensions thématiques : {}".format(len(thematic_tensions)))

    # ── Étape 6 : instances (entités dans ce scénario)
    all_instances = load_instances_for_scenario(scenario_slug)
    filtered_instances = []
    if thematique:
        filtered_instances = filter_instances_for_thematique(all_instances, thematique)
    else:
        # Sans thématique : garder les instances à fort impact systémique
        filtered_instances = sorted(
            all_instances,
            key=lambda x: -x.get("impact_systemique_global", 0)
        )[:6]
    print("[snapshot] Instances chargées : {} | Filtrées : {}".format(
        len(all_instances), len(filtered_instances)
    ))

    # ── Étape 6B : appliquer les injections custom sur les variables
    custom_instances = [i for i in all_instances
                        if i.get("injection", {}).get("type") == "custom"]
    if custom_instances:
        variable_states, modifications = apply_custom_injections(
            variable_states, custom_instances, matrix
        )
        print("[snapshot] Modifications custom (entités) : {} variables affectées".format(
            len(modifications)
        ))
    else:
        modifications = []

    # ── Étape 6C : charger et appliquer les événements custom
    custom_events = load_events_for_scenario(scenario_slug)
    event_modifications = []
    if custom_events:
        variable_states, event_modifications = apply_custom_events(
            variable_states, custom_events, matrix
        )
        print("[snapshot] Événements custom : {} | {} variables affectées".format(
            len(custom_events), len(event_modifications)
        ))
    else:
        print("[snapshot] Événements custom : aucun")


    # ── Assembler le snapshot
    snapshot = {
        # Métadonnées
        "scenario_slug":    scenario_slug,
        "scenario_name":    scenario["name"],
        "year":             2098,

        # Contexte global du scénario
        "scenario": {
            "trajectory":               scenario["trajectory"],
            "state_of_system":          scenario["state_of_system"],
            "tension_level":            scenario["tension_level"],
            "political_regime":         scenario["political_regime"],
            "dominant_region_structure":scenario["dominant_region_structure"],
            "transformation_speed":     scenario["transformation_speed"],
            "summary":                  scenario["summary"],
            "system_logic":             scenario["system_logic"],
            "interpretation":           scenario["interpretation"],
            "implications":             scenario["implications"],
            "triggers":                 scenario["triggers"],
            "system_effects":           scenario["system_effects"],
        },

        # Variables
        "pilot_variables":       pilots,
        "constrained_variables": scenario.get("constrained_variables", []),
        "variable_states":       variable_states,

        # Cohérence systémique
        "tensions":     coherence["tensions"],
        "coherence_ok": coherence["coherence_ok"],

        # Trajectoire historique (ruptures génériques)
        "trajectory_jalons": trajectory,
        "trajectory_majors": majors,

        # Trajectoire signal_to_state (événements datés et nommés)
        "signal_events": signal_events,
        "signal_majors": signal_majors,

        # Tensions thématiques (si fourni)
        "thematic_tensions": thematic_tensions,

        # Entités/instances
        "all_instances":       all_instances,
        "filtered_instances":  filtered_instances,
        "custom_instances":    custom_instances,
        "modifications":       modifications + event_modifications,

        # Événements custom
        "custom_events":       custom_events,
        "event_modifications": event_modifications,
    }

    return snapshot


# ─────────────────────────────────────────
# UTILITAIRES D'AFFICHAGE
# ─────────────────────────────────────────

def print_snapshot_summary(snapshot):
    """Affiche un résumé lisible du snapshot dans le terminal."""
    print("\n" + "="*60)
    print("SNAPSHOT — {} — {}".format(
        snapshot["scenario_name"].upper(), snapshot["year"]))
    print("="*60)

    sc = snapshot["scenario"]
    print("\nÉtat du système : {} | Tension : {}/5 | Vitesse : {}".format(
        sc["state_of_system"], sc["tension_level"], sc["transformation_speed"]))
    print("Structure : {} | Trajectoire : {}".format(
        sc["dominant_region_structure"], sc["trajectory"]))

    print("\n--- Variables pilotes ---")
    for v in snapshot["pilot_variables"]:
        state = snapshot["variable_states"].get(v, {})
        print("  [{:>3}] {} — {}".format(
            state.get("level", "?"),
            v,
            state.get("state_logic", "")[:70] + "..."
        ))

    print("\n--- Tensions critiques (top 5) ---")
    for t in snapshot["tensions"][:5]:
        print("  [{}] {} → {} (w:{} lag:{})".format(
            t["type"][:4].upper(),
            t["source"][:25],
            t["target"][:25],
            t["weight"],
            t["lag"]
        ))

    print("\n--- Jalons majeurs 2025→2098 ---")
    for j in snapshot["trajectory_majors"][:5]:
        print("  [{}] {} ({})".format(
            j["type"][:3].upper(),
            j["content"][:70],
            ", ".join(j["variables"][:2])
        ))

    print("\n--- Événements historiques datés (top 5) ---")
    for e in snapshot.get("signal_majors", [])[:5]:
        print("  [{}] {} — {}".format(
            e["scope"][:3].upper(),
            e["evenement_cle"][:60],
            e["date_bascule"]
        ))

    if snapshot["thematic_tensions"]:
        print("\n--- Tensions thématiques (top 3) ---")
        for t in snapshot["thematic_tensions"][:3]:
            pol = "+" if t["polarity"] == 1 else "−"
            print("  {} →{} {} (w:{} {})".format(
                t["source"][:20], pol,
                t["target"][:20],
                t["weight"], t["feedback_role"]
            ))

    if snapshot.get("filtered_instances"):
        print("\n--- Entités actives dans ce monde ---")
        for inst in snapshot["filtered_instances"]:
            print("  [{}] {} — {}".format(
                inst["etat_temporel"][:3].upper(),
                inst["name"][:35],
                inst["role_dans_scenario"][:60] + "..."
            ))

    print("\n" + "="*60)


# ─────────────────────────────────────────
# TEST RAPIDE
# ─────────────────────────────────────────

if __name__ == "__main__":
    from loader import load_thematique

    print("=== Test snapshot.py ===")

    # Test sans thématique
    snapshot = build_snapshot("breakdown")
    print_snapshot_summary(snapshot)

    # Test avec thématique
    print("\n\n=== Test avec thématique : actualites_a_la_une ===")
    thematique = load_thematique("actualites_a_la_une")
    snapshot2  = build_snapshot("breakdown", thematique=thematique)
    print_snapshot_summary(snapshot2)
