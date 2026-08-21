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
    load_custom_signals,
    filter_instances_for_thematique,
    select_instances_by_impact,
    resolve_forced_element,
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
# BLOC `simulation` DES FICHES VARIABLES (P22, 20 août 2026)
# ─────────────────────────────────────────
# Mapping qualitatif -> numérique pour les 3 champs rendus opérationnels
# (volatility, tipping_point_risk, systemic_criticality). predictability/
# uncertainty_level restent hors scope (point 2, mis de côté -- voir
# backlog, introduiraient de l'aléa dans un pipeline aujourd'hui
# déterministe).
#
# RÈGLE DE NON-RÉGRESSION : toute variable sans bloc `simulation` rempli,
# ou avec une valeur de champ absente/non reconnue, retombe sur la valeur
# DEFAULT ci-dessous -- qui reproduit exactement le comportement fixe
# d'avant ce chantier. Aucune variable existante ne doit changer de
# comportement du seul fait que ce mécanisme existe désormais.

# volatility -- module le facteur d'amortissement de la propagation
# matricielle (remplace le 0.5 fixe), côté variable CIBLE (une cible
# volatile réagit plus fort à une poussée reçue).
VOLATILITY_DAMPING = {
    "low":       0.3,
    "medium":    0.5,
    "high":      0.8,
    "very_high": 1.0,
}
VOLATILITY_DAMPING_DEFAULT = 0.5  # = comportement fixe d'avant ce chantier

# tipping_point_risk -- abaisse les seuils de détection de tension dans
# check_coherence() (60/70), côté variable qui PORTE le risque (source ou
# cible selon le test, jamais les deux en même temps sur un même test).
TIPPING_THRESHOLD_ADJUST = {
    "low":       0,
    "medium":    5,
    "high":      10,
    "very_high": 15,
}
TIPPING_THRESHOLD_ADJUST_DEFAULT = 0  # = pas de changement de seuil

# systemic_criticality -- multiplicateur additionnel sur le delta propagé,
# côté variable SOURCE (une variable critique qui bouge pèse plus lourd
# sur ce qu'elle influence). Échelle RÉELLE du vault = entier 1-5 (pas une
# chaîne qualitative comme les deux champs ci-dessus -- vérifié sur les
# 12 fiches variables le 20 août 2026, ex. systemic_criticality: 5).
CRITICALITY_MULTIPLIER = {
    1: 0.7,
    2: 0.85,
    3: 1.0,
    4: 1.3,
    5: 1.6,
}
CRITICALITY_MULTIPLIER_DEFAULT = 1.0  # = pas d'amplification/atténuation


def _get_simulation_param(all_variables, var_slug, field, mapping, default_value):
    """
    Lit un champ qualitatif du bloc `simulation` d'une variable et le
    convertit en valeur numérique via `mapping`.

    Retourne `default_value` si la variable est inconnue, si le bloc
    `simulation` est absent/vide, ou si le champ ne correspond à aucune
    clé du mapping -- c'est le mécanisme de non-régression : toute
    fiche variable non renseignée sur ce point se comporte exactement
    comme avant l'existence de ce mécanisme.
    """
    var = all_variables.get(var_slug, {}) or {}
    sim = var.get("simulation", {}) or {}
    raw = sim.get(field, "")
    return mapping.get(raw, default_value)


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

def check_coherence(variable_states, matrix, all_variables):
    """
    Vérifie la cohérence des états via la matrice d'influence.
    Pour chaque paire (source, target) avec weight fort :
      - Si polarity -1 et les deux variables ont level élevé → tension détectée
      - Si polarity +1 et écart de level > 40 → incohérence potentielle

    Seuils de base 60 (tension_negative) / 70 (cascade_critique), abaissés
    par variable selon son `simulation.tipping_point_risk` (P22, 20 août
    2026) -- une variable proche de sa bascule déclenche une tension à un
    niveau plus bas. Variable sans bloc `simulation` renseigné = seuils
    inchangés (voir TIPPING_THRESHOLD_ADJUST_DEFAULT).

    Retourne :
      - tensions     : list de dicts (conflits détectés)
      - coherence_ok : bool (False si incohérences majeures)
    """
    tensions = []
    by_pair  = matrix["by_pair"]

    for source_slug, source_state in variable_states.items():
        source_adjust = _get_simulation_param(
            all_variables, source_slug, "tipping_point_risk",
            TIPPING_THRESHOLD_ADJUST, TIPPING_THRESHOLD_ADJUST_DEFAULT
        )

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

            target_adjust = _get_simulation_param(
                all_variables, target_slug, "tipping_point_risk",
                TIPPING_THRESHOLD_ADJUST, TIPPING_THRESHOLD_ADJUST_DEFAULT
            )

            # Tension : lien négatif fort entre deux variables à niveau élevé
            tension_seuil_source = 60 - source_adjust
            tension_seuil_target = 60 - target_adjust
            if (edge["polarity"] == -1
                    and s_level > tension_seuil_source
                    and t_level > tension_seuil_target):
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
            cascade_seuil = 70 - source_adjust
            if (edge["feedback_role"] == "cascade"
                    and edge["polarity"] == -1
                    and edge["lag"] <= 2
                    and s_level > cascade_seuil):
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

def apply_custom_injections(variable_states, instances, matrix, all_variables):
    """
    Applique les deltas des entités custom injectées sur les variables.

    Pour chaque instance custom (injection.type == "custom") :
      1. Calcule la durée d'effet réelle (2098 - annee_injection)
      2. Pondère le delta par min(duree_effet, duree_declaree) / duree_declaree
      3. Applique le delta au level de la variable
      4. Si propagation.via_matrice = true, propage via les edges forts,
         avec un facteur de propagation = volatility de la CIBLE ×
         systemic_criticality de la SOURCE (P22, 20 août 2026 -- remplace
         le facteur fixe 0.5 d'avant ce chantier ; variable sans bloc
         `simulation` renseigné = 0.5 × 1.0 = 0.5, comportement inchangé)

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
                criticality_source = _get_simulation_param(
                    all_variables, var, "systemic_criticality",
                    CRITICALITY_MULTIPLIER, CRITICALITY_MULTIPLIER_DEFAULT
                )
                edges = matrix["by_source"].get(var, [])
                for edge in edges:
                    if edge["weight"] < 0.75:
                        continue
                    target = edge["target"]
                    if target not in states:
                        continue
                    volatility_target = _get_simulation_param(
                        all_variables, target, "volatility",
                        VOLATILITY_DAMPING, VOLATILITY_DAMPING_DEFAULT
                    )
                    prop_delta = round(
                        delta_applique * edge["weight"] * edge["polarity"]
                        * volatility_target * criticality_source, 1
                    )
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


def apply_custom_events(variable_states, events, matrix, all_variables):
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
                criticality_source = _get_simulation_param(
                    all_variables, var, "systemic_criticality",
                    CRITICALITY_MULTIPLIER, CRITICALITY_MULTIPLIER_DEFAULT
                )
                edges = matrix["by_source"].get(var, [])
                for edge in edges:
                    if edge["weight"] < 0.75:
                        continue
                    target = edge["target"]
                    if target not in states:
                        continue
                    volatility_target = _get_simulation_param(
                        all_variables, target, "volatility",
                        VOLATILITY_DAMPING, VOLATILITY_DAMPING_DEFAULT
                    )
                    prop_delta = round(
                        delta_applique * edge["weight"] * edge["polarity"]
                        * volatility_target * criticality_source, 1
                    )
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


def apply_custom_signals(variable_states, signals, matrix, scenario_slug, all_variables):
    """
    Applique les deltas des signaux faibles custom sur les variables
    (chantier injection matricielle, 16 août 2026) -- même mécanique que
    apply_custom_events()/apply_custom_injections(), avec deux différences
    structurelles propres aux signaux :
      1. Chaque entrée `signals` (issue de loader.load_custom_signals())
         ne porte qu'UNE SEULE variable cible (pas une liste d'impacts) --
         un signal développe une seule variable par appel LLM, contrairement
         aux instances/événements qui peuvent en toucher plusieurs.
      2. annee_injection/duree sont PROPRES À CHAQUE SCÉNARIO (dérivés de
         `date_bascule`, qui diffère d'un scénario à l'autre pour le même
         signal) -- d'où le paramètre scenario_slug, absent des deux
         fonctions sœurs qui appliquent le même delta à tous les scénarios.

    Retourne les variable_states modifiés + un log des modifications,
    même format que les deux fonctions sœurs pour rester compatible avec
    l'affichage existant de "Perturbations custom actives".
    """
    modifications = []
    states = {k: dict(v) for k, v in variable_states.items()}

    for signal in signals:
        var = signal.get("variable", "")
        scen_data = (signal.get("scenarios") or {}).get(scenario_slug)
        if not scen_data or var not in states:
            continue

        annee       = scen_data.get("annee_injection", 2050)
        delta       = scen_data.get("delta_level", 0)
        duree_dec   = scen_data.get("duree", 15)
        polarite    = scen_data.get("polarite", 1)
        via_matrice = signal.get("propagation_via_matrice", False)

        if not delta:
            continue

        duree_effet = 2098 - int(annee)
        nom_signal = signal.get("source_fiche", "signal").replace(".md", "")
        print("[snapshot] Signal custom '{}' sur {} (an {}, {} ans d'effet)".format(
            nom_signal, var, annee, duree_effet
        ))

        facteur        = min(duree_effet, duree_dec) / max(duree_dec, 1)
        delta_applique = round(delta * facteur * polarite, 1)

        old_level = states[var].get("level", 50)
        if old_level == "" or old_level is None:
            old_level = 50

        new_level = max(0, min(100, float(old_level) + delta_applique))
        states[var]["level"]              = round(new_level, 1)
        states[var]["signal_perturbation"] = True
        states[var]["signal_source"]       = nom_signal

        modifications.append({
            "event":     "[signal] " + nom_signal,
            "date":      annee,
            "variable":  var,
            "delta":     delta_applique,
            "old_level": old_level,
            "new_level": new_level,
        })
        print("  → {} : {} → {} (delta:{:+})".format(
            var, old_level, new_level, delta_applique
        ))

        if via_matrice and matrix:
            criticality_source = _get_simulation_param(
                all_variables, var, "systemic_criticality",
                CRITICALITY_MULTIPLIER, CRITICALITY_MULTIPLIER_DEFAULT
            )
            edges = matrix["by_source"].get(var, [])
            for edge in edges:
                if edge["weight"] < 0.75:
                    continue
                target = edge["target"]
                if target not in states:
                    continue
                volatility_target = _get_simulation_param(
                    all_variables, target, "volatility",
                    VOLATILITY_DAMPING, VOLATILITY_DAMPING_DEFAULT
                )
                prop_delta = round(
                    delta_applique * edge["weight"] * edge["polarity"]
                    * volatility_target * criticality_source, 1
                )
                old_t = states[target].get("level", 50)
                if old_t == "" or old_t is None:
                    old_t = 50
                new_t = max(0, min(100, float(old_t) + prop_delta))
                states[target]["level"]              = round(new_t, 1)
                states[target]["signal_perturbation"] = True
                states[target]["signal_source"]       = "{} (propagé)".format(nom_signal)
                modifications.append({
                    "event":     "[signal] " + nom_signal + " (propagé)",
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

def _dominant_zone(instances):
    """
    Retourne le slug de zone le plus représenté parmi les instances filtrées.
    Utilise localisation.zone de chaque instance.
    Retourne None si aucune instance n'a de localisation.
    """
    from collections import Counter
    zones = []
    for inst in instances:
        loc = inst.get("localisation", {})
        if isinstance(loc, dict):
            z = loc.get("zone")
            if z:
                zones.append(z)
    if not zones:
        return None
    return Counter(zones).most_common(1)[0][0]


def build_snapshot(scenario_slug, thematique=None, dry_run=True, forcer_config=None):
    """
    Fonction principale — construit le snapshot complet du monde 2098.

    Args:
        scenario_slug : str — slug du scénario (ex: "breakdown")
        thematique    : dict — fiche thématique chargée (optionnel)
        dry_run       : bool — si False, la rotation à mémoire des
                        instances sélectionnées (voir loader.py,
                        ajouté le 2 août 2026) est persistée sur disque.
                        True par défaut : un aperçu/dry-run ne doit
                        jamais faire avancer la rotation, seule une
                        génération réelle le doit.
        forcer_config : dict|None — bloc `forcer:` de config.yaml
                        (type/slug/mode), ajouté le 2 août 2026. Résolu
                        via loader.resolve_forced_element() et appliqué
                        à la sélection d'instances/événements/signaux
                        ci-dessous. Si l'élément demandé est introuvable,
                        l'erreur est placée dans snapshot["forcer_erreur"]
                        plutôt que de faire échouer toute la génération --
                        c'est à l'appelant (generate.py) de décider s'il
                        arrête ou continue sans le forçage.

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
    coherence = check_coherence(variable_states, matrix, all_variables)
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
        filtered_instances = filter_instances_for_thematique(
            all_instances, thematique, scenario_slug=scenario_slug, dry_run=dry_run
        )
    else:
        # Sans thématique : garder les instances à fort impact systémique,
        # avec la même rotation à mémoire (ajouté le 2 août 2026 --
        # remplace l'ancien tri déterministe pur qui ne laissait jamais
        # sortir une instance à impact modéré).
        filtered_instances = select_instances_by_impact(
            all_instances, scenario_slug, dry_run=dry_run, max_n=6
        )
    print("[snapshot] Instances chargées : {} | Filtrées : {}".format(
        len(all_instances), len(filtered_instances)
    ))

    # ── Étape 6B : appliquer les injections custom sur les variables
    custom_instances = [i for i in all_instances
                        if i.get("injection", {}).get("type") == "custom"]
    if custom_instances:
        variable_states, modifications = apply_custom_injections(
            variable_states, custom_instances, matrix, all_variables
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
            variable_states, custom_events, matrix, all_variables
        )
        print("[snapshot] Événements custom : {} | {} variables affectées".format(
            len(custom_events), len(event_modifications)
        ))
    else:
        print("[snapshot] Événements custom : aucun")

    # ── Étape 6D2 : charger et appliquer les signaux faibles custom
    # (chantier injection matricielle, 16 août 2026 — troisième et dernier
    # type d'injection après entités/instances et événements)
    custom_signals = load_custom_signals()
    signal_modifications = []
    if custom_signals:
        variable_states, signal_modifications = apply_custom_signals(
            variable_states, custom_signals, matrix, scenario_slug, all_variables
        )
        print("[snapshot] Signaux custom chiffrés : {} | {} variables affectées".format(
            len(custom_signals), len(signal_modifications)
        ))
    modifications = modifications + event_modifications + signal_modifications

    # ── Étape 6D : forçage d'un élément (ajouté le 2 août 2026)
    forcer_resolu = resolve_forced_element(forcer_config, scenario_slug)
    forced_signal_event = None
    forced_angle_directive = None
    forcer_erreur = None

    if forcer_resolu:
        forcer_erreur = forcer_resolu.get("erreur")

        if forcer_erreur:
            print("[snapshot] ⚠ Forçage demandé mais impossible : {}".format(forcer_erreur))

        elif forcer_resolu["type"] == "instance":
            inst = forcer_resolu["instance"]
            deja_present = any(i["slug"] == inst["slug"] for i in filtered_instances)
            if forcer_resolu["mode"] == "sujet_central":
                # Remplace entièrement la sélection auto -- cet article
                # ne doit parler que de cette instance, pas la diluer
                # parmi 5 autres sélectionnées automatiquement.
                filtered_instances = [inst]
                print("[snapshot] Forçage instance (sujet central) : {}".format(inst["slug"]))
            elif not deja_present:
                # ingredient : garantie de présence, ajoutée en plus de
                # la sélection auto -- si ça dépasse le plafond habituel
                # de 6, on évince la moins pertinente plutôt que de
                # laisser le prompt grossir sans limite.
                filtered_instances = [inst] + filtered_instances[:5]
                print("[snapshot] Forçage instance (ingrédient) : {} ajoutée".format(inst["slug"]))
            else:
                print("[snapshot] Forçage instance (ingrédient) : {} déjà sélectionnée normalement".format(inst["slug"]))
            if forcer_resolu["mode"] == "sujet_central":
                forced_angle_directive = (
                    "Cet article DOIT être construit spécifiquement autour de {} : {}"
                ).format(inst.get("name", inst["slug"]), inst.get("role_dans_scenario", "")[:400])

        elif forcer_resolu["type"] == "evenement":
            ev = forcer_resolu["event"]
            # Déjà garanti présent dans custom_events (aucune troncature
            # sur ce chargement, voir loader.py::load_events_for_scenario)
            # -- rien à injecter, juste à confirmer et, en mode
            # sujet_central, à orienter l'angle dessus.
            print("[snapshot] Forçage événement ({}) : {} confirmé dans custom_events".format(
                forcer_resolu["mode"], ev["slug"]
            ))
            if forcer_resolu["mode"] == "sujet_central":
                forced_angle_directive = (
                    "Cet article DOIT être construit spécifiquement autour de l'événement "
                    "\"{}\" ({}) : {}"
                ).format(ev.get("name", ev["slug"]), ev.get("date_label", ""), ev.get("description", "")[:400])

        elif forcer_resolu["type"] == "signal":
            forced_signal_event = forcer_resolu["signal_event"]
            print("[snapshot] Forçage signal ({}) : {}".format(
                forcer_resolu["mode"], forced_signal_event["evenement_cle"]
            ))
            if forcer_resolu["mode"] == "sujet_central":
                forced_angle_directive = (
                    "Cet article DOIT être construit spécifiquement autour de l'événement "
                    "\"{}\" ({}) : {}"
                ).format(
                    forced_signal_event["evenement_cle"],
                    forced_signal_event["date_bascule"],
                    forced_signal_event["evolution"],
                )

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
        "modifications":       modifications,

        # Événements custom
        "custom_events":       custom_events,
        "event_modifications": event_modifications,

        # Signaux faibles custom chiffrés (16 août 2026)
        "custom_signals":       custom_signals,
        "signal_modifications": signal_modifications,

        # Zone dominante — déterminée depuis les instances filtrées
        "zone_slug":           _dominant_zone(filtered_instances),

        # Forçage d'un élément (ajouté le 2 août 2026)
        "forcer_resolu":          forcer_resolu,
        "forcer_erreur":          forcer_erreur,
        "forced_signal_event":    forced_signal_event,
        "forced_angle_directive": forced_angle_directive,
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
