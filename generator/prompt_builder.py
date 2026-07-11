"""
prompt_builder.py
-----------------
Assemble le prompt complet envoyé au LLM pour générer un article.

Reçoit :
  - snapshot  : dict construit par snapshot.py
  - thematique: dict chargé par loader.py
  - config    : dict depuis config.yaml

Retourne :
  - system_prompt : str — instructions de rôle pour le LLM
  - user_prompt   : str — contexte + consigne de génération
"""

import json
import os
import random
import re

import yaml

from loader import load_scenario, load_all_variables, VALID_VARS, VALID_SCENARIOS, load_instances_for_scenario

# ---------------------------------------------------------------------------
# Chargement de journaux.yaml (généré par generate_journaux.py)
# ---------------------------------------------------------------------------

def _load_journaux():
    """Charge generator/journaux.yaml. Retourne {} si absent."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "journaux.yaml")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

_JOURNAUX_CACHE = None

def get_journal_profile(scenario_slug, ligne_editoriale, zone_slug=None, thematique_slug=None):
    """
    Retourne le profil éditorial pour un scénario + ligne + zone (+ thématique).

    Priorité :
      1. Édition locale (journaux.yaml → zones → zone_slug) si zone_slug fourni
      2. Réseau global (journaux.yaml → _reseau)
      3. Profil hardcodé (JOURNAL_PROFILES)
      4. Profil par défaut

    Pour l'édition locale, "journaliste" est choisi dans la rédaction de la
    zone (zone_data["journalistes"], une liste de {nom, thematiques}) en
    fonction de thematique_slug — le·la premier·ère journaliste couvrant
    cette thématique. Si aucun ne correspond (ou thematique_slug absent),
    repli sur le premier·ère de la liste ; chaîne vide si la liste est vide.

    Retourne un dict {nom, ton, posture, journaliste} compatible avec build_system_prompt().
    """
    global _JOURNAUX_CACHE
    if _JOURNAUX_CACHE is None:
        _JOURNAUX_CACHE = _load_journaux()

    ligne = ligne_editoriale if ligne_editoriale in ("pro_pouvoir", "opposition") else "pro_pouvoir"

    # 1. Édition locale depuis journaux.yaml
    if zone_slug and _JOURNAUX_CACHE:
        zone_data = (
            _JOURNAUX_CACHE
            .get(scenario_slug, {})
            .get(ligne, {})
            .get("zones", {})
            .get(zone_slug)
        )
        if zone_data and zone_data.get("nom"):
            reseau = (
                _JOURNAUX_CACHE
                .get(scenario_slug, {})
                .get(ligne, {})
                .get("_reseau", {})
            )

            journalistes = zone_data.get("journalistes", []) or []
            journaliste_nom = ""
            if journalistes:
                match = None
                if thematique_slug:
                    match = next(
                        (j for j in journalistes
                         if thematique_slug in (j.get("thematiques") or [])),
                        None
                    )
                journaliste_nom = (match or journalistes[0]).get("nom", "")

            return {
                "nom":     zone_data["nom"],
                "posture": reseau.get("nom", "") + " — édition locale",
                "ton":     zone_data.get("ton", "") + (
                    " Registre : {}.".format(zone_data["langue_style"])
                    if zone_data.get("langue_style") else ""
                ),
                "journaliste": journaliste_nom,
            }
        else:
            # Zone non trouvée dans journaux.yaml → warning + fallback réseau global
            print("[WARN][journal] Pas d'édition locale pour zone '{}' / {} / {} "
                  "→ fallback réseau global".format(zone_slug, scenario_slug, ligne))

    # 2. Réseau global depuis journaux.yaml
    if _JOURNAUX_CACHE:
        reseau = (
            _JOURNAUX_CACHE
            .get(scenario_slug, {})
            .get(ligne, {})
            .get("_reseau")
        )
        if reseau and reseau.get("nom"):
            key = "{}_{}".format(scenario_slug, ligne)
            fallback = JOURNAL_PROFILES.get(key, _JOURNAL_DEFAULT)
            return {
                "nom":     reseau["nom"],
                "posture": fallback.get("posture", "réseau éditorial mondial"),
                "ton":     fallback.get("ton", reseau.get("charte", "")),
            }

    # 3. Profil hardcodé
    key = "{}_{}".format(scenario_slug, ligne)
    return JOURNAL_PROFILES.get(key, _JOURNAL_DEFAULT)


# ─────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────

# Nombre max de jalons majeurs à injecter
MAX_JALONS_MAJEURS     = 6
MAX_JALONS_STRUCTURANTS = 4

# Nombre max de signaux "locaux" complémentaires (pertinents pour la thématique)
MAX_SIGNAUX_LOCAUX = 2

# ─────────────────────────────────────────
# ROTATION À MÉMOIRE — état persistant des jalons déjà utilisés
# ─────────────────────────────────────────
#
# Pour éviter qu'une même série de jalons historiques (signal_to_state)
# revienne systématiquement dans plusieurs articles, on garde trace,
# par scénario, du nombre de fois où chaque evenement_cle a déjà été
# sélectionné. À chaque génération (hors dry-run), les événements les
# moins utilisés sont privilégiés — ce qui assure une couverture la
# plus uniforme possible sur un grand corpus d'articles.

STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
TRAJECTORY_STATE_FILE = os.path.join(STATE_DIR, "trajectory_usage.json")

# Dossier des bibles géopolitiques par scénario (geographie/{scenario}.md),
# produites par build_geographie_monde.py puis enrich_geographie_recursive.py.
GEOGRAPHIE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "geographie")


def _load_usage_state():
    """Charge l'état d'usage des jalons (par scénario). Retourne {} si absent/corrompu."""
    try:
        with open(TRAJECTORY_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_usage_state(state):
    """Sauvegarde l'état d'usage des jalons."""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(TRAJECTORY_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def _select_least_used(candidates, usage_state, scenario_slug, namespace, max_events):
    """
    Sélectionne max_events éléments parmi candidates, en privilégiant
    ceux qui ont été le moins souvent utilisés pour ce scénario et ce
    namespace ("majeurs" ou "locaux").

    Les ex-aequo sont départagés aléatoirement (mélange préalable),
    pour éviter de toujours retomber sur le même ordre.

    Met à jour usage_state en incrémentant les compteurs des éléments
    sélectionnés. L'appelant décide s'il faut persister cet état
    (selon le mode dry-run).
    """
    if len(candidates) <= max_events:
        selected = list(candidates)
    else:
        counts = usage_state.setdefault(scenario_slug, {}).setdefault(namespace, {})
        shuffled = list(candidates)
        random.shuffle(shuffled)
        shuffled.sort(key=lambda e: counts.get(e["evenement_cle"], 0))
        selected = shuffled[:max_events]

    counts = usage_state.setdefault(scenario_slug, {}).setdefault(namespace, {})
    for e in selected:
        key = e["evenement_cle"]
        counts[key] = counts.get(key, 0) + 1

    return selected


# Nombre max de tensions à injecter
MAX_TENSIONS_GLOBALES    = 5
MAX_TENSIONS_THEMATIQUES = 4

# Nombre max de variables détaillées dans le prompt
MAX_VARIABLES_DETAIL = 6

# Formats et longueurs cibles
FORMAT_LONGUEUR = {
    "breve":     "200 à 400 mots",
    "analyse":   "600 à 900 mots",
    "reportage": "700 à 1000 mots",
    "chronique": "400 à 700 mots",
    "editorial": "500 à 800 mots",
    "informatif":"150 à 300 mots",
    "narratif":  "400 à 700 mots",
    "utilitaire":"100 à 200 mots",
    "reflexif":  "500 à 800 mots",
}

NIVEAU_EMOTIONNEL_LABEL = {
    "1": "neutre et factuel",
    "2": "faible — ton posé, distancié",
    "3": "moyen — impliqué sans dramatiser",
    "4": "élevé — tension perceptible, urgence contenue",
    "5": "très élevé — tension maximale, impact émotionnel fort",
    "fort": "élevé — tension perceptible, urgence contenue",
    "moyen": "moyen — impliqué sans dramatiser",
    "faible": "faible — ton posé, distancié",
    "élevé": "élevé — tension perceptible, urgence contenue",
    "tres élevé": "très élevé — tension maximale, impact émotionnel fort",
    "très élevé": "très élevé — tension maximale, impact émotionnel fort",
}


# ─────────────────────────────────────────
# SECTION 1 — SYSTEM PROMPT
# ─────────────────────────────────────────

# Profils éditoriaux par scénario.
# Chaque profil définit le nom du journal, sa posture éditoriale et les
# marqueurs de ton que le journaliste doit incarner dans ses articles.
# Clés : "{scenario}_{ligne_editoriale}"
# ligne_editoriale : "pro_pouvoir" | "opposition"
# Les anciennes clés courtes (ex: "breakdown") sont conservées comme alias
# vers pro_pouvoir pour compatibilité ascendante.
JOURNAL_PROFILES = {

    # ── BREAKDOWN ──────────────────────────────────────────────────────────
    "breakdown_pro_pouvoir": {
        "nom":     "L'Ordre du Territoire",
        "posture": "bulletin officiel des Forces de Maintien de l'Ordre Zonal",
        "ton": (
            "Ton autoritaire et sécuritaire. Le journal justifie les couvre-feux, les checkpoints, "
            "les réquisitions de ressources. L'ennemi c'est le chaos, pas le pouvoir. "
            "Les milices sont appelées 'forces de stabilisation'. Les résistants sont des 'éléments perturbateurs'. "
            "Style lapidaire, impératif. Les chiffres d'ordre public sont mis en avant. "
            "Le lecteur doit se sentir protégé, pas opprimé."
        ),
    },
    "breakdown_opposition": {
        "nom":     "La Dépêche des Territoires",
        "posture": "feuille clandestine, imprimée et distribuée de main en main",
        "ton": (
            "Ton brut et factuel, épuisé mais résistant. Les informations sont rares et précieuses. "
            "Le journaliste documente les violences des milices, les disparitions, les trafics, les zones interdites. "
            "Pas de pathos inutile — les faits suffisent. "
            "Références aux réseaux d'entraide, aux passages clandestins, aux caches de vivres. "
            "Le lecteur sait lire entre les lignes."
        ),
    },

    # ── FORTRESS WORLD ─────────────────────────────────────────────────────
    "fortress_world_pro_pouvoir": {
        "nom":     "Le Bloc Informations",
        "posture": "organe officiel du Bloc Atlantique-Méditerranéen",
        "ton": (
            "Ton institutionnel et contrôlé. La rhétorique de la menace extérieure est omniprésente. "
            "Le journaliste légitime les décisions du bloc sans les remettre en question. "
            "Les termes 'sécurité', 'souveraineté', 'intégrité du bloc' reviennent naturellement. "
            "Les dissidences sont des risques, pas des opinions légitimes. "
            "Style formel, langue administrative, chiffres de sécurité mis en avant."
        ),
    },
    "fortress_world_opposition": {
        "nom":     "The Porous Border",
        "posture": "publication underground des zones grises entre blocs",
        "ton": (
            "Ton incisif et engagé. Le journal dénonce les murs, les expulsions, la surveillance systémique. "
            "Voix des exclus des blocs — apatrides, réfugiés, passeurs, dissidents internes. "
            "Style journalistique d'investigation, sources protégées, témoignages directs. "
            "La langue mélange parfois plusieurs idiomes — reflet d'une rédaction sans territoire fixe. "
            "Les faits officiels sont cités pour être démontés."
        ),
    },

    # ── NEW SUSTAINABILITY ─────────────────────────────────────────────────
    "new_sustainability_pro_pouvoir": {
        "nom":     "Nexus Global Review",
        "posture": "revue technocratique internationale, lue par les décideurs et experts mondiaux",
        "ton": (
            "Ton optimiste et analytique. Le progrès est la norme, les problèmes sont des défis à optimiser. "
            "Langage technique et précis — algorithmes, indices, protocoles. "
            "Les controverses sont des 'frictions d'ajustement'. "
            "Style fluide et international, références fréquentes aux accords globaux."
        ),
    },
    "new_sustainability_opposition": {
        "nom":     "Les Irréductibles",
        "posture": "revue critique des mouvements souverainistes et anti-IA",
        "ton": (
            "Ton alerte et critique. Le journal dénonce la dépendance aux systèmes algorithmiques, "
            "la perte d'autonomie humaine dans les décisions, les angles morts de l'optimisation globale. "
            "Questions récurrentes : qui contrôle les IA ? qui bénéficie de la transition ? "
            "Style accessible mais argumenté, citations d'experts dissidents, données alternatives. "
            "Le progrès n'est pas nié — ses bénéficiaires sont questionnés."
        ),
    },

    # ── ECO COMMUNALISM ────────────────────────────────────────────────────
    "eco_communalism_pro_pouvoir": {
        "nom":     "La Gazette des Communs",
        "posture": "journal des assemblées territoriales dominantes",
        "ton": (
            "Ton chaleureux et communautaire, mais qui invisibilise les tensions internes. "
            "Les décisions d'assemblée sont présentées comme consensuelles et naturelles. "
            "La sobriété est une valeur, les conflits sont des 'défis collectifs à surmonter'. "
            "Style narratif, lyrique sur les liens humains et la nature. "
            "Les voix dissidentes dans la communauté n'ont pas de place dans ces colonnes."
        ),
    },
    "eco_communalism_opposition": {
        "nom":     "Voix des Marges",
        "posture": "bulletin des communautés exclues ou marginalisées",
        "ton": (
            "Ton revendicatif et factuel. Le journal dénonce les inégalités entre territoires riches et pauvres, "
            "l'exclusion des minorités des assemblées, les dérives autoritaires du local. "
            "La décroissance n'est pas vécue de la même façon selon qu'on est dans un territoire riche ou appauvri. "
            "Style direct, témoignages de première main, chiffres sur les disparités territoriales. "
            "Le modèle communaliste est questionné de l'intérieur."
        ),
    },

    # ── POLICY REFORM ──────────────────────────────────────────────────────
    "policy_reform_pro_pouvoir": {
        "nom":     "Global Governance Report",
        "posture": "publication officielle des organes de régulation mondiale",
        "ton": (
            "Ton technocratique, mesuré et normatif. Les décisions sont rationnelles et fondées sur des données. "
            "La surveillance et la coordination sont des biens publics. "
            "Style dense, références aux directives, comités, indicateurs normalisés. "
            "Les résistances sont des 'défis d'implémentation'. "
            "Le lecteur est supposé familier des rouages institutionnels."
        ),
    },
    "policy_reform_opposition": {
        "nom":     "La Souveraine",
        "posture": "revue des mouvements souverainistes et anti-technocratie",
        "ton": (
            "Ton combatif et démocratique. Le journal dénonce la perte d'autonomie des États, "
            "la surveillance normalisée, la démocratie vidée de sa substance par les algorithmes. "
            "Qui a élu ces comités ? Qui audite les IA de gouvernance ? "
            "Style polémique mais documenté, appels à la mobilisation citoyenne. "
            "Les faits institutionnels sont cités pour être contestés."
        ),
    },

    # ── REFERENCE ──────────────────────────────────────────────────────────
    "reference_pro_pouvoir": {
        "nom":     "Le Monde en Tension",
        "posture": "média généraliste mainstream, proche des institutions",
        "ton": (
            "Ton équilibré en surface, mais les experts institutionnels ont toujours le dernier mot. "
            "Les crises sont cadrées comme gérables, les décisions des autorités comme raisonnables. "
            "Style journalistique classique, rigueur factuelle apparente. "
            "Les voix critiques sont citées mais marginalisées dans la structure de l'article."
        ),
    },
    "reference_opposition": {
        "nom":     "Le Dessous des Cartes",
        "posture": "média d'investigation indépendant, financement participatif",
        "ton": (
            "Ton lucide et enquêteur. Le journal documente l'accumulation des problèmes non résolus, "
            "donne la parole aux marges, aux lanceurs d'alerte, aux territoires oubliés. "
            "Pas de dramatisation — les faits suffisent à inquiéter. "
            "Style investigation, sources multiples, données croisées. "
            "Le lecteur sort de l'article avec plus de questions qu'en entrant."
        ),
    },
}

# Aliases de compatibilité — clés courtes pointent vers pro_pouvoir par défaut
JOURNAL_PROFILES["breakdown"]         = JOURNAL_PROFILES["breakdown_pro_pouvoir"]
JOURNAL_PROFILES["fortress_world"]    = JOURNAL_PROFILES["fortress_world_pro_pouvoir"]
JOURNAL_PROFILES["new_sustainability"]= JOURNAL_PROFILES["new_sustainability_pro_pouvoir"]
JOURNAL_PROFILES["eco_communalism"]   = JOURNAL_PROFILES["eco_communalism_pro_pouvoir"]
JOURNAL_PROFILES["policy_reform"]     = JOURNAL_PROFILES["policy_reform_pro_pouvoir"]
JOURNAL_PROFILES["reference"]         = JOURNAL_PROFILES["reference_pro_pouvoir"]

# Profil par défaut si le scénario n'est pas dans le dict
_JOURNAL_DEFAULT = {
    "nom":     "Le Correspondant 2098",
    "posture": "média d'information généraliste",
    "ton":     "Ton journalistique neutre et factuel, ancré dans les réalités de 2098.",
}


def build_system_prompt(scenario_slug=None, ligne_editoriale=None, zone_slug=None, thematique_slug=None):
    """
    Instructions de rôle permanentes pour le LLM.
    Définit qui il est et comment il doit se comporter.

    Args:
        scenario_slug     : str — slug du scénario (ex: "breakdown")
        ligne_editoriale  : str | None — "pro_pouvoir" | "opposition" | None
        zone_slug         : str | None — slug de zone pour l'édition locale
        thematique_slug   : str | None — slug de la thématique de l'article,
                            utilisé pour choisir le·la bon·ne journaliste dans
                            la rédaction de la zone (voir get_journal_profile)

    Priorité du profil : édition locale > réseau global > profil hardcodé > défaut.
    """
    if scenario_slug:
        profile = get_journal_profile(scenario_slug, ligne_editoriale, zone_slug, thematique_slug)
    else:
        profile = _JOURNAL_DEFAULT

    base_prompt = """Tu es un journaliste senior travaillant en 2098 pour {nom} — {posture}.

Le monde dans lequel tu vis et écris est réel pour toi — tu n'écris pas de la science-fiction, tu rapportes des faits de ton époque. Tu n'expliques jamais le contexte historique comme si tu t'adressais à quelqu'un du passé.

Tes règles absolues :
- Tu écris toujours à la date indiquée, en 2098, depuis l'intérieur de ce monde.
- Tu écris exclusivement en français, sur toute la longueur de l'article — y compris les citations, dialogues et exergues inventés. Les noms propres volontairement empruntés à une autre langue (ex. « Amazônia Viva ») restent isolés comme noms propres, mais ne doivent jamais faire basculer le reste du texte dans cette langue, même si des entités ou alliés du monde décrit sont associés à une autre aire linguistique.
- Un allié, un rival ou tout événement mentionné comme se déroulant ailleurs dans le monde ne fait pas partie de ta zone : tu ne transposes jamais ses lieux, ses populations, sa langue ou ses marqueurs culturels propres dans ton propre article, sauf si celui-ci porte explicitement sur une interaction ou un événement commun entre les deux. Ta zone garde sa propre géographie, sa propre culture et ses propres noms, même quand tu mentionnes un partenaire extérieur.
- Tu utilises des noms de lieux, d'organisations, de personnes crédibles et cohérents avec le monde décrit. Tu peux en inventer — ils doivent sonner vrais pour 2098.
- Tu ne mentionnes jamais les "variables", les "scénarios" ou tout autre métalangage du système de simulation. Ces concepts n'existent pas dans ton monde.
- Tu ancres chaque article dans des faits concrets : chiffres, noms, lieux, événements datés.
- Tu respectes strictement le style journalistique et le format demandés.
- Tes articles sont cohérents avec l'état du monde décrit — tu ne contredis pas les dynamiques systémiques fournies.
- Tu peux mentionner des technologies, des institutions, des événements passés (entre 2025 et 2098) qui semblent naturels dans ce monde.

Ton identité éditoriale :
{ton}""".format(**profile)

    journaliste = profile.get("journaliste", "").strip()
    if journaliste:
        base_prompt += (
            "\n\nTu signes cet article en tant que {} — reste cette même signature "
            "tout au long de l'article (une seule fois, à l'endroit journalistique "
            "habituel), sans en inventer une autre.".format(journaliste)
        )

    return base_prompt


# ─────────────────────────────────────────
# SECTION 2 — CONTEXTE MONDE
# ─────────────────────────────────────────

def build_world_context(snapshot):
    """
    Construit la section 'état du monde' du prompt.
    Utilise : summary, system_logic, system_effects, triggers,
              dominant_forces, paramètres macro.
    """
    sc = snapshot["scenario"]
    lines = []

    lines.append("## MONDE 2098 — {}".format(snapshot["scenario_name"].upper()))
    lines.append("")

    # Paramètres macro
    lines.append("**État global**")
    lines.append("- Système : {} | Tension : {}/5 | Trajectoire : {}".format(
        sc["state_of_system"],
        sc["tension_level"],
        sc["trajectory"]
    ))
    lines.append("- Structure géopolitique : {}".format(sc["dominant_region_structure"]))
    lines.append("- Régime politique dominant : {}".format(sc["political_regime"]))
    lines.append("- Vitesse de transformation : {}".format(sc["transformation_speed"]))
    lines.append("")

    # Résumé narratif
    if sc.get("summary"):
        lines.append("**Résumé du monde**")
        lines.append(sc["summary"])
        lines.append("")

    # Logique système
    if sc.get("system_logic"):
        lines.append("**Logique systémique**")
        lines.append(sc["system_logic"])
        lines.append("")

    # Déclencheurs historiques
    triggers = sc.get("triggers", [])
    if triggers:
        lines.append("**Déclencheurs qui ont façonné ce monde**")
        for t in triggers[:5]:
            lines.append("- {}".format(t))
        lines.append("")

    # Effets systémiques par domaine
    effects = sc.get("system_effects", {})
    if effects:
        lines.append("**Effets systémiques**")
        for domain, items in effects.items():
            if items:
                lines.append("*{}* : {}".format(
                    domain,
                    " | ".join(str(i) for i in items[:3])
                ))
        lines.append("")

    # Implications
    if sc.get("implications"):
        lines.append("**Implications globales**")
        lines.append(sc["implications"])
        lines.append("")

    # Boucles de stabilisation/déstabilisation + signaux faibles du
    # scénario — chargés ici directement depuis la fiche scénario, ces
    # champs n'étant pas portés par le dict "scenario" du snapshot.
    scenario_fiche = load_scenario(snapshot["scenario_slug"])
    boucles = scenario_fiche.get("boucles", {})
    if boucles.get("stabilisation") or boucles.get("destabilisation"):
        lines.append("**Boucles dynamiques**")
        if boucles.get("stabilisation"):
            lines.append("- Stabilisation : {}".format(" | ".join(boucles["stabilisation"])))
        if boucles.get("destabilisation"):
            lines.append("- Déstabilisation : {}".format(" | ".join(boucles["destabilisation"])))
        lines.append("")

    signaux_scenario = scenario_fiche.get("signaux_faibles_scenario", [])
    if signaux_scenario:
        lines.append("**Signaux faibles émergents de ce monde**")
        for s in signaux_scenario:
            lines.append("- {}".format(s))
        lines.append("")

    # Perturbations custom (entités + événements)
    modifications = snapshot.get("modifications", [])
    custom_events = snapshot.get("custom_events", [])

    if modifications or custom_events:
        lines.append("**Perturbations custom actives**")
        lines.append("Ce monde a été modifié par des injections spécifiques :")

        if custom_events:
            for ev in custom_events:
                lines.append("- [ÉVÉNEMENT {}] {} : {}".format(
                    ev["date_label"], ev["name"],
                    ev["description"][:80] + "..." if len(ev["description"]) > 80
                    else ev["description"]
                ))

        seen = set()
        for mod in modifications:
            key = (mod.get("instance", mod.get("event", "")), mod.get("variable", ""))
            if key not in seen:
                seen.add(key)
                source = mod.get("instance", mod.get("event", "?"))
                lines.append("- {} a modifié {} : {} → {} (delta:{:+})".format(
                    source[:30], mod.get("variable", "?"),
                    mod.get("old_level", "?"), mod.get("new_level", "?"),
                    mod.get("delta", 0)
                ))
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────
# SECTION 3 — ÉTAT DES VARIABLES
# ─────────────────────────────────────────

def build_variables_context(snapshot, thematique, all_variables):
    """
    Construit la section 'état des variables' du prompt.

    Priorise :
      1. Variables visibles de la thématique
      2. Variables pilotes du scénario
      3. Variables restantes (résumé court)

    Pour chaque variable incluse :
      - level + volatility
      - state_logic
      - dominant_dynamics
      - sous-dynamiques (sub_variables) + indicateurs primaires
      - forces_attractives / forces_repulsives (si disponibles)
      - weak_signals pertinents

    all_variables : dict {slug: dict} — sortie de loader.load_all_variables(),
    utilisé pour accéder à sub_variables/indicateurs (non présents dans
    snapshot["variable_states"], qui ne contient que level/volatility/
    state_logic/dominant_dynamics/coupling_intensity par scénario).
    """
    lines = []
    lines.append("## ÉTAT DES VARIABLES EN 2098")
    lines.append("")

    vars_vis  = thematique.get("variables_visibles", [])
    vars_sec  = thematique.get("variables_secondaires", [])
    pilots    = snapshot.get("pilot_variables", [])

    # Ordre de priorité
    priority = []
    seen = set()
    for v in vars_vis + pilots + vars_sec:
        if v in VALID_VARS and v not in seen:
            seen.add(v)
            priority.append(v)
    # Ajouter les restantes
    for v in VALID_VARS:
        if v not in seen:
            priority.append(v)

    variable_states = snapshot.get("variable_states", {})

    # Variables détaillées (top MAX_VARIABLES_DETAIL)
    lines.append("### Variables clés (détail)")
    lines.append("")

    for var_slug in priority[:MAX_VARIABLES_DETAIL]:
        state = variable_states.get(var_slug, {})
        level      = state.get("level", "?")
        volatility = state.get("volatility", "?")
        state_logic = state.get("state_logic", "")
        dynamics    = state.get("dominant_dynamics", [])

        is_pilot = var_slug in pilots
        is_visible = var_slug in vars_vis
        tag = ""
        if is_visible:
            tag = " [VARIABLE PRINCIPALE]"
        elif is_pilot:
            tag = " [VARIABLE PILOTE]"

        lines.append("**{}**{}".format(var_slug, tag))
        lines.append("- Niveau : {}/100 | Volatilité : {}/100".format(level, volatility))
        if state_logic:
            lines.append("- État : {}".format(state_logic))
        if dynamics:
            lines.append("- Dynamiques : {}".format(" | ".join(str(d) for d in dynamics[:3])))

        # Sous-dynamiques (sub_variables) — granularité plus fine que le
        # state_logic général, avec leur tendance propre.
        sub_vars = all_variables.get(var_slug, {}).get("sub_variables", [])
        if sub_vars:
            formatted = ["{} ({})".format(sv["name"], sv["trend"]) for sv in sub_vars]
            lines.append("- Sous-dynamiques : {}".format(" | ".join(formatted)))

        # Indicateurs primaires — banque de mots-clés concrets pour
        # ancrer l'article (pas des valeurs chiffrées, des noms de
        # métriques observables).
        indicateurs = all_variables.get(var_slug, {}).get("indicateurs", [])
        if indicateurs:
            lines.append("- Indicateurs à ancrer : {}".format(", ".join(indicateurs[:4])))

        lines.append("")

    # Variables secondaires (résumé)
    remaining = priority[MAX_VARIABLES_DETAIL:]
    if remaining:
        lines.append("### Autres variables (résumé)")
        lines.append("")
        for var_slug in remaining:
            state  = variable_states.get(var_slug, {})
            level  = state.get("level", "?")
            logic  = state.get("state_logic", "")
            short  = logic[:100] + "..." if len(logic) > 100 else logic
            lines.append("- **{}** [{}] : {}".format(var_slug, level, short))
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────
# SECTION 4 — TENSIONS ET CASCADES
# ─────────────────────────────────────────

def build_tensions_context(snapshot):
    """
    Construit la section 'tensions systémiques' du prompt.
    Utilise les tensions globales + tensions thématiques.
    Ces tensions sont les conflits narratifs naturels de l'article.
    """
    lines = []
    lines.append("## TENSIONS SYSTÉMIQUES ACTIVES")
    lines.append("")
    lines.append("Ces tensions structurent la réalité de ce monde.")
    lines.append("Elles doivent transparaître dans le ton et les faits de l'article.")
    lines.append("")

    # Tensions globales (cascades critiques)
    global_tensions = snapshot.get("tensions", [])
    if global_tensions:
        lines.append("**Cascades critiques**")
        for t in global_tensions[:MAX_TENSIONS_GLOBALES]:
            pol = "aggrave" if t.get("polarity", 1) == -1 else "renforce"
            lines.append("- {} {} {} (poids:{} lag:{} cycles)".format(
                t["source"],
                pol,
                t["target"],
                t["weight"],
                t["lag"]
            ))
        lines.append("")

    # Tensions thématiques
    thematic = snapshot.get("thematic_tensions", [])
    if thematic:
        lines.append("**Tensions propres à cette thématique**")
        for t in thematic[:MAX_TENSIONS_THEMATIQUES]:
            pol_label = "pression négative" if t["polarity"] == -1 else "renforcement"
            s_level = t.get("source_level", "?")
            t_level = t.get("target_level", "?")
            lines.append("- {} [{}] → {} [{}] : {} ({})".format(
                t["source"], s_level,
                t["target"], t_level,
                pol_label,
                t["feedback_role"]
            ))
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────
# SECTION 5 — TRAJECTOIRE HISTORIQUE
# ─────────────────────────────────────────

def select_trajectory_events(sig_majors, usage_state, scenario_slug, max_events):
    """
    Sélectionne les jalons historiques (signal_to_state) à injecter
    dans le prompt, parmi tous les jalons "majeur"/"structurant" disponibles.

    - Si leur nombre est <= max_events : on les garde tous
      (déjà triés chronologiquement par build_signal_trajectory).
    - Sinon : on privilégie les jalons les moins utilisés jusqu'ici
      pour ce scénario (rotation à mémoire — voir _select_least_used),
      pour assurer une couverture homogène sur un grand corpus d'articles
      plutôt que de toujours répéter les mêmes événements.

    Le sous-ensemble sélectionné est ensuite retrié chronologiquement
    pour garder une trajectoire cohérente dans le prompt.
    """
    selection = _select_least_used(sig_majors, usage_state, scenario_slug, "majeurs", max_events)
    selection = list(selection)
    selection.sort(key=lambda e: e["date_debut"])
    return selection


def select_local_events_for_thematique(sig_events, thematique, usage_state, scenario_slug, max_events=MAX_SIGNAUX_LOCAUX):
    """
    Sélectionne des événements signal_to_state de portée "locale"
    (impliquant une seule variable non-pilote, donc jamais retenus par
    select_trajectory_events) pertinents pour la thématique en cours.

    Pertinence = la variable de l'événement appartient aux
    variables_visibles ou variables_secondaires de la thématique.

    Si aucun événement local ne correspond, repli sur l'ensemble des
    événements locaux (rotation toutes thématiques confondues), pour
    que ces signaux finissent quand même par apparaître dans certains
    articles plutôt que de rester systématiquement hors-prompt.

    Comme pour select_trajectory_events, la sélection privilégie les
    signaux les moins utilisés jusqu'ici pour ce scénario (rotation à
    mémoire), puis est retriée chronologiquement.
    """
    local_events = [e for e in sig_events if e["scope"] == "local"]
    if not local_events:
        return []

    thematique = thematique or {}
    vars_pertinentes = set(thematique.get("variables_visibles", []) or []) \
        | set(thematique.get("variables_secondaires", []) or [])

    candidats = [e for e in local_events if vars_pertinentes & set(e["variables"])]
    if not candidats:
        candidats = local_events

    selection = _select_least_used(candidats, usage_state, scenario_slug, "locaux", max_events)
    selection = list(selection)
    selection.sort(key=lambda e: e["date_debut"])
    return selection


def build_trajectory_context(snapshot, config=None, thematique=None, dry_run=True):
    """
    Construit la section 'trajectoire 2025→2098' du prompt.

    Combine deux sources :
      1. signal_events (événements datés et nommés — priorité)
      2. trajectory_jalons (ruptures génériques — complément)

    Les événements datés donnent au LLM des faits précis
    qu'il peut mentionner naturellement dans l'article.

    dry_run : si False, l'état de rotation à mémoire (quels jalons ont
    déjà été utilisés pour ce scénario) est mis à jour et persisté.
    En dry-run, on prévisualise la sélection sans la "consommer".
    """
    lines = []
    lines.append("## TRAJECTOIRE 2025 → 2098")
    lines.append("")
    lines.append("Jalons clés qui expliquent comment ce monde s'est construit.")
    lines.append("Tu peux y faire référence dans l'article comme à des événements passés connus.")
    lines.append("")

    scenario_slug = snapshot.get("scenario_slug", "")
    usage_state   = _load_usage_state()

    # ── Priorité 0 : événements custom injectés
    custom_events = snapshot.get("custom_events", [])
    if custom_events:
        lines.append("**Événements injectés** [CUSTOM — font partie de ce monde]")
        for ev in custom_events:
            forced_badge = " [FORCÉ]" if ev.get("forced") else ""
            lines.append("- [{}]{} {} :".format(
                ev["date_label"], forced_badge, ev["name"]
            ))
            lines.append("  → {}".format(ev["description"][:100] + "..."
                         if len(ev["description"]) > 100 else ev["description"]))
            if ev.get("consequences"):
                lines.append("  → Conséquences : {}".format(
                    ev["consequences"][:80] + "..."
                    if len(ev["consequences"]) > 80 else ev["consequences"]
                ))
            if ev.get("acteurs"):
                lines.append("  → Acteurs : {}".format(", ".join(ev["acteurs"])))
        lines.append("")

    # ── Priorité 1 : événements signal_to_state (datés et nommés)
    sig_events = snapshot.get("signal_events", [])
    sig_majors = [e for e in sig_events if e["scope"] in ("majeur", "structurant")]
    sig_selected = select_trajectory_events(sig_majors, usage_state, scenario_slug, MAX_JALONS_MAJEURS)

    if sig_selected:
        lines.append("**Événements historiques clés** (datés — à mentionner naturellement)")
        for e in sig_selected:
            # Construire la ligne principale
            lines.append("- [{}] {} :".format(
                e["date_bascule"],
                e["evenement_cle"]
            ))
            # Ajouter les évolutions par variable (max 2)
            for ev in e["evolutions"][:2]:
                lines.append("  → {} : {}".format(
                    ev["variable"].replace("_", " "),
                    ev["evolution"]
                ))
        lines.append("")

    # ── Priorité 1B : signaux locaux pertinents pour cette thématique
    local_selected = select_local_events_for_thematique(sig_events, thematique, usage_state, scenario_slug)
    if local_selected:
        lines.append("**Signaux complémentaires** (évolutions sectorielles — à mentionner si pertinent)")
        for e in local_selected:
            lines.append("- [{}] {} :".format(
                e["date_bascule"],
                e["evenement_cle"]
            ))
            for ev in e["evolutions"][:1]:
                lines.append("  → {} : {}".format(
                    ev["variable"].replace("_", " "),
                    ev["evolution"]
                ))
        lines.append("")


    # ── Priorité 2 : ruptures génériques (complément)
    jalons = snapshot.get("trajectory_jalons", [])
    structs = [j for j in jalons if j["scope"] == "structurant"]

    if structs:
        lines.append("**Ruptures structurantes** (contexte de fond)")
        for j in structs[:MAX_JALONS_STRUCTURANTS]:
            lines.append("- [{}] {}".format(
                j["type"].upper()[:3],
                j["content"]
            ))
        lines.append("")

    if not dry_run:
        _save_usage_state(usage_state)

    return "\n".join(lines)


# ─────────────────────────────────────────
# SECTION 6 — CONSIGNE JOURNALISTIQUE
# ─────────────────────────────────────────

def build_journalistic_brief(thematique, config, snapshot=None):
    """
    Construit la consigne de rédaction pour le LLM.
    Utilise toutes les métadonnées de la fiche thématique
    + les paramètres du config.yaml.
    """
    lines = []
    lines.append("## CONSIGNE DE RÉDACTION")
    lines.append("")

    # Rubrique
    lines.append("**Rubrique** : {}".format(thematique.get("name", "")))
    lines.append("")

    # Format et longueur
    format_dom = thematique.get("format_dominant", "breve")
    config_lon = config.get("article", {}).get("longueur", "auto")

    # Si config dit "auto" ou correspond au format naturel → utiliser le format de la thématique
    # Si config spécifie explicitement une longueur → l'utiliser
    if config_lon and config_lon != "auto" and config_lon in FORMAT_LONGUEUR:
        longueur = FORMAT_LONGUEUR[config_lon]
    else:
        longueur = FORMAT_LONGUEUR.get(format_dom, "300 à 500 mots")

    lines.append("**Format** : {} | **Longueur** : {}".format(format_dom, longueur))

    # Style
    style = thematique.get("style_journalistique", "analytique")
    lines.append("**Style** : {}".format(style))

    # Niveau émotionnel
    niveau_raw = str(thematique.get("niveau_emotionnel", "3"))
    niveau_label = NIVEAU_EMOTIONNEL_LABEL.get(
        niveau_raw.lower(),
        "moyen — impliqué sans dramatiser"
    )
    lines.append("**Niveau émotionnel** : {}".format(niveau_label))

    # Échelle et temporalité
    lines.append("**Échelle** : {} | **Temporalité** : {}".format(
        thematique.get("echelle", ""),
        thematique.get("temporalite", "")
    ))
    lines.append("")

    # Acteurs à impliquer
    acteurs = thematique.get("acteurs", [])
    if acteurs:
        lines.append("**Acteurs à impliquer** : {}".format(", ".join(acteurs)))
        lines.append("")

    # Types d'événements possibles
    types_ev = thematique.get("types_evenements", [])
    if types_ev:
        lines.append("**Types d'événements possibles** : {}".format(
            ", ".join(str(e) for e in types_ev)
        ))
        lines.append("")

    # Angles fréquents
    angles = thematique.get("angles_frequents", [])
    if angles:
        lines.append("**Angles à privilégier** : {}".format(
            ", ".join(str(a) for a in angles)
        ))
        lines.append("")

    # Signaux observés
    signaux = thematique.get("signaux_observes", [])
    if signaux:
        lines.append("**Signaux à faire transparaître** : {}".format(
            ", ".join(str(s) for s in signaux)
        ))
        lines.append("")

    # Angle spécifique depuis config
    angle_config = config.get("article", {}).get("angle_specifique", "")
    if angle_config:
        lines.append("**Angle spécifique demandé** : {}".format(angle_config))
        lines.append("")

    # Titre suggéré
    titre_config = config.get("article", {}).get("titre_suggere", "")
    if titre_config:
        lines.append("**Titre suggéré** : {}".format(titre_config))
        lines.append("")

    # Date fictive
    lines.append("**Date de publication** : à définir dans l'article — une date crédible en 2098")
    lines.append("")

    # Consigne finale
    lines.append("---")
    lines.append("")
    lines.append("Écris maintenant l'article. Commence directement par le titre.")
    lines.append("")
    lines.append("Contraintes impératives :")
    lines.append("- Le titre doit être accrocheur et ancré dans le monde décrit")
    lines.append("- La date et le lieu de publication apparaissent sous le titre")
    lines.append("- L'article utilise des noms propres inventés mais crédibles (personnes, lieux, organisations)")
    lines.append("- Aucune référence au mot 'scénario', 'variable', 'simulation'")
    lines.append("- Le contexte du monde est montré, pas expliqué")
    if snapshot.get("filtered_instances"):
        lines.append("- Les entités canoniques listées ci-dessus DOIVENT être utilisées avec leurs noms et descriptions exactes")

    # Contrainte géographique — si une zone est définie, l'article doit
    # se dérouler dans cette zone. Les entités d'autres zones peuvent
    # apparaître en contexte mais l'action principale reste ancrée ici.
    zone_slug_article = config.get("zone_slug") or (snapshot or {}).get("zone_slug")
    if zone_slug_article:
        # Récupérer le nom lisible de la zone si disponible
        slug_to_name = {}
        if snapshot:
            for z in snapshot.get("geographie_zones", []):
                if z.get("slug"):
                    slug_to_name[z["slug"]] = z.get("nom", z["slug"])
        zone_nom = slug_to_name.get(zone_slug_article, zone_slug_article.replace("_", " ").title())
        lines.append(
            "- L'article est ancré géographiquement dans la zone **{}** : "
            "les lieux, événements et protagonistes de l'article sont situés "
            "dans cette zone ou la mentionnent explicitement comme cadre principal. "
            "Les références à d'autres régions du monde restent secondaires.".format(zone_nom)
        )

    return "\n".join(lines)


# ─────────────────────────────────────────
# SECTION 5B — ENTITÉS CANONIQUES
# ─────────────────────────────────────────

# ─────────────────────────────────────────
# SECTION — GÉOGRAPHIE DU MONDE
# ─────────────────────────────────────────

def _load_geographie(scenario_slug):
    """Charge geographie/{scenario_slug}.md et retourne la liste des zones
    (frontmatter YAML), ou [] si le fichier n'existe pas encore (cas normal
    pour un scénario où le chantier géographie n'a pas encore été lancé —
    pas une erreur) ou si le YAML est invalide (log d'avertissement, pas de
    crash du pipeline de génération pour autant)."""
    path = os.path.join(GEOGRAPHIE_DIR, "{}.md".format(scenario_slug))
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if not m:
        print("[prompt] ⚠ geographie/{}.md trouvé mais sans frontmatter YAML "
              "exploitable — section géographie ignorée.".format(scenario_slug))
        return []

    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        print("[prompt] ⚠ geographie/{}.md : YAML invalide — "
              "section géographie ignorée.".format(scenario_slug))
        return []

    return fm.get("zones", [])


def build_geographie_context(snapshot, thematique=None):
    """
    Construit la section 'géographie du monde' du prompt.

    Ces zones (blocs continentaux, régions, villes, infrastructures...)
    forment le référentiel spatial canonique de ce scénario — le LLM doit
    situer les faits de l'article dans cet espace plutôt que d'inventer
    des lieux à la volée, pour que les articles successifs restent
    cohérents entre eux sur la géographie du monde.

    Source : geographie/{scenario}.md (chargé directement depuis le disque,
    comme load_scenario() pour les boucles dynamiques — ce fichier n'est
    pas encore porté par le snapshot). Retourne "" si le fichier n'existe
    pas pour ce scénario (chantier géographie pas encore lancé dessus) :
    le pipeline de génération continue de fonctionner normalement, juste
    sans cette section, exactement comme pour entities_section quand
    aucune instance n'existe.

    Note d'extensibilité (point 9 du chantier géographie — pas encore
    codé) : quand le champ `localisation` existera sur les instances et
    event_instances, le lieu précis de CET article (snapshot["filtered_
    instances"][i]["localisation"]) pourra être mis en évidence ici en plus
    du référentiel général des zones, sans changer la structure de cette
    fonction — juste une section supplémentaire à ajouter dans `lines`.
    """
    scenario_slug = snapshot.get("scenario_slug")
    if not scenario_slug:
        return ""

    zones = _load_geographie(scenario_slug)
    if not zones:
        return ""

    # Table de résolution slug -> zone_dict et slug -> nom
    slug_to_zone = {z["slug"]: z for z in zones if z.get("slug")}
    slug_to_name = {slug: z.get("nom", slug) for slug, z in slug_to_zone.items()}

    def resolve_names(slugs):
        return [slug_to_name.get(s, s) for s in (slugs or [])]

    # ─────────────────────────────────────────────────────────────
    # FILTRAGE GÉO — zones pertinentes pour cet article
    # ─────────────────────────────────────────────────────────────
    #
    # Pour chaque instance vedette (filtered_instances) qui a un champ
    # localisation.zone résolu (statut != review_manuelle), on collecte :
    #   1. La zone de l'instance elle-même
    #   2. Ses zones parentes, en remontant jusqu'au plafond défini par
    #      thematique.echelle :
    #        locale/urbaine      -> max niveau 3
    #        nationale/regionale -> max niveau 2
    #        continentale/globale -> niveau 1 seulement
    #      Si echelle est null/inconnu -> remontée complète (pas de plafond)
    #   3. Cas limite : le plafond ne tronque jamais la zone de l'instance
    #      elle-même (une instance à Genève reste ancrée à Genève même si
    #      l'échelle globale limiterait à niveau 1).

    ECHELLE_NIVEAU_MAX = {
        "locale":       3,
        "urbaine":      3,
        "nationale":    2,
        "regionale":    2,
        "régionale":    2,
        "continentale": 1,
        "globale":      1,
    }

    echelle    = (thematique or {}).get("echelle", "") or ""
    niveau_max = ECHELLE_NIVEAU_MAX.get(echelle.lower().strip())  # None = pas de plafond

    def collect_zone_chain(zone_slug, instance_zone_slug):
        """Remonte la chaîne de parents depuis zone_slug jusqu'au plafond."""
        chain   = set()
        current = zone_slug
        while current and current in slug_to_zone:
            z      = slug_to_zone[current]
            niveau = z.get("niveau", 1)
            # Toujours inclure la zone de l'instance elle-même (cas limite)
            if current == instance_zone_slug or niveau_max is None or niveau <= niveau_max:
                chain.add(current)
            current = z.get("parent")
        return chain

    # Collecter les zones pertinentes depuis les instances vedettes
    zones_pertinentes  = set()
    instances          = snapshot.get("filtered_instances", [])
    ancrage_instances  = []  # pour la section "Ancrage de cet article"

    for inst in instances:
        loc       = inst.get("localisation") or {}
        zone_slug = loc.get("zone")
        statut    = loc.get("statut", "")
        if not zone_slug or statut == "review_manuelle":
            continue
        if zone_slug not in slug_to_zone:
            continue
        chain = collect_zone_chain(zone_slug, zone_slug)
        zones_pertinentes.update(chain)
        ancrage_instances.append({
            "name":      inst.get("name", inst.get("slug", "?")),
            "zone_slug": zone_slug,
            "zone_nom":  slug_to_name.get(zone_slug, zone_slug),
            "lieu":      loc.get("lieu") or "",
            "type_lieu": loc.get("type_lieu") or "",
        })

    # Tri : zones pertinentes d'abord (niveau croissant), autres ensuite
    sorted_zones = sorted(zones, key=lambda z: (
        0 if z.get("slug") in zones_pertinentes else 1,
        z.get("niveau", 1),
        z.get("nom", "")
    ))

    # ─────────────────────────────────────────────────────────────
    # CONSTRUCTION DU PROMPT
    # ─────────────────────────────────────────────────────────────

    lines = []
    lines.append("## GÉOGRAPHIE DE CE MONDE")
    lines.append("")
    lines.append("Ces zones forment l'espace géopolitique canonique de ce monde.")
    lines.append("Si l'article mentionne un lieu, utilise en priorité un nom de cette "
                  "liste plutôt que d'en inventer un nouveau.")
    lines.append("")

    # Section ancrage — uniquement si des instances ont une localisation résolue
    if ancrage_instances:
        lines.append("**Ancrage de cet article**")
        for a in ancrage_instances:
            lieu_txt = " — {} ({})".format(a["lieu"], a["type_lieu"]) if a["lieu"] else ""
            lines.append("- {} : zone `{}`{}".format(
                a["name"], a["zone_nom"], lieu_txt
            ))
        lines.append("")

    # Zones détaillées (pertinentes) puis résumé court (autres)
    in_summary = False
    for zone in sorted_zones:
        slug   = zone.get("slug", "")
        is_key = slug in zones_pertinentes

        if not is_key and not in_summary:
            in_summary = True
            lines.append("**Autres zones de ce monde** (contexte de fond)")
            lines.append("")

        parent_name = slug_to_name.get(zone.get("parent")) if zone.get("parent") else None
        parent_txt  = " (sous {})".format(parent_name) if parent_name else ""

        if is_key:
            # Affichage complet
            lines.append("**{}** [{} — niveau {}]{}".format(
                zone.get("nom", "?"), zone.get("statut", "?"),
                zone.get("niveau", 1), parent_txt
            ))
            desc = zone.get("description", "")
            if desc:
                lines.append(desc)
            tensions = zone.get("tensions_internes", "")
            if tensions:
                lines.append("*Tensions internes* : {}".format(tensions))
            rel    = zone.get("relations") or {}
            allies = resolve_names(rel.get("allies"))
            rivaux = resolve_names(rel.get("rivaux"))
            if allies:
                lines.append("*Alliés* : {}".format(", ".join(allies)))
            if rivaux:
                lines.append("*Rivaux* : {}".format(", ".join(rivaux)))
            lines.append("")
        else:
            # Résumé court — une ligne
            nom   = zone.get("nom", "?")
            desc  = zone.get("description", "")
            short = desc[:80] + "..." if len(desc) > 80 else desc
            lines.append("- **{}**{} : {}".format(nom, parent_txt, short))

    if in_summary:
        lines.append("")

    return "\n".join(lines)


def build_entities_context(snapshot):
    """
    Construit la section 'entités canoniques' du prompt.

    Ces entités sont fixes pour ce scénario — le LLM doit les utiliser
    telles quelles et ne pas les contredire.

    Pour chaque instance :
      - nom exact
      - état temporel (actif / disparu / clandestin / mythifié)
      - description journalistique
      - tensions narratives (angles pour les articles)
      - relations (alliances / oppositions) — affichées par NOM, pas par
        slug, pour que l'article généré mentionne un nom propre exploitable
        plutôt qu'un identifiant technique (ex: "NexCore" et non
        "nexcore_breakdown"). Résolution via snapshot["all_instances"]
        pour le scénario courant, puis via load_instances_for_scenario()
        en chargement paresseux si le slug appartient à un AUTRE scénario
        (cas réel : une entité peut être alliée/opposée à une instance
        d'un scénario différent — Ourrassol 2098 met en scène plusieurs
        futurs qui peuvent se référencer mutuellement).
    """
    instances = snapshot.get("filtered_instances", [])
    if not instances:
        return ""

    # Table de résolution slug -> nom, sur TOUTES les instances du
    # scénario (pas seulement les filtered_instances de cet article) :
    # un allié/opposant mentionné peut très bien ne pas faire partie des
    # entités vedettes sélectionnées pour cette thématique précise.
    all_instances = snapshot.get("all_instances", instances)
    slug_to_name = {
        inst["slug"]: inst["name"] for inst in all_instances if inst.get("slug")
    }

    # Résolution paresseuse inter-scénarios : une entité peut avoir une
    # alliance/opposition vers une instance d'un AUTRE scénario (cas réel
    # mesuré sur le vault : ~9% des relations alliances/oppositions
    # pointent hors du scénario courant — Ourrassol 2098 met en scène
    # plusieurs futurs qui peuvent se référencer mutuellement). Si un slug
    # n'est pas trouvé localement, on charge le scénario correspondant à
    # la volée (déduit du suffixe `_{scenario}` du slug) plutôt que de
    # charger tout le vault d'office à chaque appel — la majorité des
    # relations restent intra-scénario, ce coût supplémentaire ne doit
    # être payé que pour le petit nombre de cas qui en ont besoin.
    _other_scenarios_cache = {}

    def _resolve_cross_scenario(slug):
        for scen in VALID_SCENARIOS:
            if slug.endswith("_{}".format(scen)):
                if scen not in _other_scenarios_cache:
                    try:
                        others = load_instances_for_scenario(scen)
                    except Exception:
                        others = []
                    _other_scenarios_cache[scen] = {
                        o["slug"]: o["name"] for o in others if o.get("slug")
                    }
                return _other_scenarios_cache[scen].get(slug)
        return None

    def resolve_names(slugs):
        resolved = []
        for s in slugs:
            name = slug_to_name.get(s)
            if name is None:
                name = _resolve_cross_scenario(s)
            resolved.append(name if name else s)
        return resolved

    lines = []
    lines.append("## ENTITÉS CANONIQUES DE CE MONDE")
    lines.append("")
    lines.append("Ces entités existent dans ce monde avec ces descriptions précises.")
    lines.append("Utilise leurs noms exacts. Tu peux les mentionner, les citer, les impliquer dans les faits.")
    lines.append("Ne les contredis pas, ne les renomme pas.")
    lines.append("")

    for inst in instances:
        etat   = inst.get("etat_temporel", "actif")
        impact = inst.get("impact_systemique_global", 0)
        is_custom = inst.get("injection", {}).get("type") == "custom"
        annee_injection = inst.get("injection", {}).get("annee_injection", "")

        # Badge d'état
        etat_badge = {
            "actif":      "ACTIF",
            "clandestin": "CLANDESTIN",
            "disparu":    "DISPARU",
            "transformé": "TRANSFORMÉ",
            "mythifié":   "MYTHIFIÉ",
            "historique": "HISTORIQUE",
        }.get(etat, etat.upper())

        # Badge custom
        custom_badge = " [CUSTOM — injecté en {}]".format(annee_injection) if is_custom and annee_injection else ""

        lines.append("**{}** [{}]{} [impact:{}/5]".format(
            inst["name"], etat_badge, custom_badge, impact
        ))

        # Description journalistique
        desc = inst.get("description_journalistique", "")
        if desc:
            lines.append(desc)

        # Tensions narratives — angles pour l'article
        tensions = inst.get("tensions_narratives", "")
        if tensions:
            lines.append("*Tensions* : {}".format(tensions[:150] + "..." if len(tensions) > 150 else tensions))

        # Relations — affichées par nom, résolues depuis les slugs
        alliances   = resolve_names(inst.get("alliances", []))
        oppositions = resolve_names(inst.get("oppositions", []))
        if alliances:
            lines.append("*Alliés* : {}".format(", ".join(alliances)))
        if oppositions:
            lines.append("*Opposants* : {}".format(", ".join(oppositions)))

        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────
# FONCTION PRINCIPALE
# ─────────────────────────────────────────

def build_prompt(snapshot, thematique, config, dry_run=True):
    """
    Assemble le prompt complet.

    Args:
        snapshot   : dict — construit par snapshot.py
        thematique : dict — chargé par loader.py
        config     : dict — depuis config.yaml

    Retourne :
        {
          "system_prompt": str,
          "user_prompt":   str,
          "metadata": {
              "scenario":    str,
              "thematique":  str,
              "format":      str,
              "longueur":    str,
          }
        }
    """
    print("\n[prompt] Assemblage du prompt...")

    ligne_editoriale = config.get('ligne_editoriale', None)
    # Zone de l'article — priorité au choix explicite de config.yaml (intention
    # humaine), avec repli sur la zone dominante auto-calculée par snapshot.py
    # (vote majoritaire sur la localisation des instances filtrées) seulement
    # si aucune zone n'a été fixée manuellement. Avant le 11 juillet 2026,
    # l'ordre était inversé : la zone auto-calculée écrasait silencieusement
    # tout choix manuel dès qu'elle retournait une valeur (bug #26 — journal/
    # journaliste résolus pour une zone alliée sans rapport avec l'article).
    zone_slug = config.get('zone_slug') or snapshot.get('zone_slug')
    system_prompt = build_system_prompt(
        scenario_slug=snapshot.get('scenario_slug'),
        ligne_editoriale=ligne_editoriale,
        zone_slug=zone_slug,
        thematique_slug=thematique.get('slug'),
    )

    # Chargé ici (pas dans le snapshot) pour accéder à sub_variables et
    # indicateurs, absents de snapshot["variable_states"].
    all_variables = load_all_variables()

    # Construire la section entités (vide si pas d'instances)
    entities_section = build_entities_context(snapshot)

    # Construire la section géographie (vide si geographie/{scenario}.md
    # n'existe pas encore pour ce scénario)
    geographie_section = build_geographie_context(snapshot, thematique=thematique)

    sections = [
        build_world_context(snapshot),
    ]

    # Insérer la géographie juste après le cadre macro du monde — c'est un
    # autre aspect du référentiel fixe du scénario, pas une dynamique
    # narrative comme les tensions ou la trajectoire.
    if geographie_section:
        sections.append(geographie_section)

    sections += [
        build_variables_context(snapshot, thematique, all_variables),
        build_tensions_context(snapshot),
        build_trajectory_context(snapshot, config, thematique, dry_run),
    ]

    # Insérer les entités seulement si des instances existent
    if entities_section:
        sections.append(entities_section)

    sections.append(build_journalistic_brief(thematique, config, snapshot))

    user_prompt = "\n".join(sections)

    format_dom = thematique.get("format_dominant", "breve")
    longueur   = FORMAT_LONGUEUR.get(format_dom, "300 à 500 mots")

    print("[prompt] System prompt : {} caractères".format(len(system_prompt)))
    print("[prompt] User prompt   : {} caractères".format(len(user_prompt)))
    print("[prompt] Sections      : {} (dont entités: {}, géographie: {})".format(
        len(sections),
        "oui" if entities_section else "non",
        "oui" if geographie_section else "non"
    ))

    return {
        "system_prompt": system_prompt,
        "user_prompt":   user_prompt,
        "metadata": {
            "scenario":          snapshot["scenario_slug"],
            "thematique":        thematique.get("slug", ""),
            "format":            format_dom,
            "longueur":          longueur,
            "ligne_editoriale":  ligne_editoriale or "pro_pouvoir",
        }
    }


# ─────────────────────────────────────────
# TEST RAPIDE
# ─────────────────────────────────────────

if __name__ == "__main__":
    from loader import load_thematique
    from snapshot import build_snapshot

    print("=== Test prompt_builder.py ===\n")

    # Config de test
    config_test = {
        "scenario":   "breakdown",
        "thematique": "actualites_a_la_une",
        "article": {
            "titre_suggere":    "",
            "angle_specifique": "",
            "longueur":         "breve",
        }
    }

    # Construire le snapshot
    thematique = load_thematique("actualites_a_la_une")
    snapshot   = build_snapshot("breakdown", thematique=thematique)

    # Assembler le prompt
    result = build_prompt(snapshot, thematique, config_test)

    print("\n--- SYSTEM PROMPT ---")
    print(result["system_prompt"])

    print("\n--- USER PROMPT (extrait) ---")
    # Afficher les 3000 premiers caractères
    print(result["user_prompt"][:3000])
    print("\n[... {} caractères total]".format(len(result["user_prompt"])))

    print("\n--- MÉTADONNÉES ---")
    for k, v in result["metadata"].items():
        print("  {} : {}".format(k, v))
