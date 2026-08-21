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

from loader import load_scenario, load_all_variables, VALID_VARS, VALID_SCENARIOS, load_instances_for_scenario, select_relevant_events

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
# Ajouté le 3 août 2026 (audit de complétude) : plafond pour les ruptures
# génériques de portée "majeur" (voir MAX_JALONS_RUPTURES_MAJEURES
# ci-dessous, docstring de build_trajectory_context pour le contexte
# complet du bug corrigé).
MAX_JALONS_RUPTURES_MAJEURES = 3

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
    "brève":     "200 à 400 mots",   # bug trouvé le 9 août 2026 : VALID_FORMATS
                                       # (validate.py) accepte les deux orthographes
                                       # pour format_dominant, mais ce dict ne
                                       # couvrait que la version sans accent — toute
                                       # thématique avec "brève" (accentué) retombait
                                       # silencieusement sur le filet de secours
                                       # générique "300 à 500 mots" au lieu de "200 à
                                       # 400 mots". Découvert via audit_longueur_
                                       # articles.py (4/4 articles "brève" du vault
                                       # portaient bien la plage de secours, jamais
                                       # la vraie plage de la catégorie).
    "analyse":   "600 à 900 mots",
    "reportage": "700 à 1000 mots",
    "chronique": "400 à 700 mots",
    "editorial": "500 à 800 mots",
    "éditorial": "500 à 800 mots",    # même bug, même correctif préventif —
                                       # jamais observé en pratique sur le vault
                                       # actuel (aucun article "éditorial" dans
                                       # l'échantillon audité), mais VALID_FORMATS
                                       # accepte cette orthographe aussi.
    "informatif":"150 à 300 mots",
    "narratif":  "400 à 700 mots",
    "utilitaire":"100 à 200 mots",
    "reflexif":  "500 à 800 mots",
    "réflexif":  "500 à 800 mots",    # idem — préventif, non observé en pratique.
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

    # Signature — corrigé le 10 août 2026 (retour de David : certains
    # articles sans signature, d'autres avec signature + nom du journal,
    # incohérent). Root cause : "journaliste" n'est peuplé que par le
    # chemin 1 (édition locale, journaux.yaml → zones). Les chemins 2
    # (réseau global) et 3 (profils hardcodés JOURNAL_PROFILES) ne le
    # fournissent jamais — l'instruction de signature était donc purement
    # et simplement absente du prompt dans ces cas, laissant au LLM le
    # choix libre de signer ou non. Corrigé : une instruction de signature
    # est désormais TOUJOURS donnée, avec un format explicite et unique
    # (nom + journal) — nom curaté si disponible (chemin 1), sinon
    # inventé par le LLM lui-même mais au même format standardisé.
    #
    # Complément du même jour, après lecture d'un batch réel : "à
    # l'endroit journalistique habituel" s'est révélé trop vague — sur 12
    # articles, la signature est apparue tantôt en haut (sous la date),
    # tantôt en bas (fin d'article), et un cas l'a même dupliquée aux
    # deux endroits malgré la consigne "une seule fois". Conforme aux
    # usages réels de la presse en ligne (byline sous le titre/date, pas
    # en pied d'article — l'usage "en bas" est plutôt celui des tribunes/
    # éditoriaux), la position est maintenant explicitement fixée en haut,
    # et la consigne "une seule fois" reformulée pour interdire toute
    # répétition ailleurs dans le texte.
    journaliste = profile.get("journaliste", "").strip()
    nom_journal = profile.get("nom", "")
    if journaliste:
        base_prompt += (
            "\n\nTu signes cet article en tant que {} — au format exact "
            "\"{} — {}\", sans en inventer une autre. Cette signature "
            "apparaît UNE SEULE FOIS dans tout l'article, immédiatement "
            "sous la date de publication (comme dans la presse en ligne) "
            "— jamais en fin d'article, jamais répétée ailleurs.".format(
                journaliste, journaliste, nom_journal
            )
        )
    else:
        base_prompt += (
            "\n\nTu signes cet article d'un nom de journaliste crédible "
            "que tu inventes toi-même, au format exact \"Prénom Nom — {}\". "
            "Cette signature apparaît UNE SEULE FOIS dans tout l'article, "
            "immédiatement sous la date de publication (comme dans la "
            "presse en ligne) — jamais en fin d'article, jamais répétée "
            "ailleurs.".format(nom_journal)
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
            # Vue d'ensemble large et volontairement peu coûteuse (une
            # ligne tronquée par événement) -- ajouté le 2 août 2026 :
            # plafonnée plus haut que la section détaillée de
            # build_trajectory_context() pour préserver la vision globale
            # du monde même quand le détail complet est filtré par
            # pertinence. Au-delà du plafond, une mention compacte
            # (dates + noms seulement) maintient quand même la présence
            # de ces événements à l'esprit du modèle, sans le coût d'une
            # ligne complète par événement.
            PLAFOND_APERCU = 25
            for ev in custom_events[:PLAFOND_APERCU]:
                lines.append("- [ÉVÉNEMENT {}] {} : {}".format(
                    ev["date_label"], ev["name"],
                    ev["description"][:80] + "..." if len(ev["description"]) > 80
                    else ev["description"]
                ))
            reste = custom_events[PLAFOND_APERCU:]
            if reste:
                lines.append("- (+ {} autres événements de ce monde : {})".format(
                    len(reste), ", ".join("{} [{}]".format(e["name"], e["date_label"]) for e in reste)
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
      - forces_attractives / forces_repulsives (section 3 du corps
        markdown, "Dynamique interne" — câblé le 15 août), avec une
        consigne de pilotage explicite. Version 1 (descriptive,
        "à parts égales") insuffisante sur 3/3 tests réels — répulsif
        systématiquement mobilisé, attractif quasi absent. Version 2
        (15 août, même session) : contrainte concrète et actionnable
        ("au moins un fait/acteur/citation illustrant une force
        attractive").
      - consigne de couverture des variables pilotes (ajoutée le
        15 août) : diagnostic sur 5/5 générations réelles montrant
        climat_environnement_global totalement absente du texte alors
        qu'elle était vérifiée présente dans le top MAX_VARIABLES_DETAIL
        à chaque fois (donc pas un problème de troncature côté code —
        le LLM reçoit la donnée en détail mais ne la mobilise pas,
        probablement un effet de position/priorité narrative de la
        thématique). Distincte de la consigne forces ci-dessus : ici
        on demande une résonance minimale de CHAQUE variable pilote
        dans le texte, pas un équilibre attractif/répulsif au sein
        d'une variable donnée.
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
    constrained = snapshot.get("constrained_variables", [])

    # Ordre de priorité
    priority = []
    seen = set()
    for v in vars_vis + pilots + constrained + vars_sec:
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
    lines.append("Pour chaque variable, les forces attractives et répulsives "
                  "listées ci-dessous sont deux dynamiques réelles et actives "
                  "de ce monde, pas de simples options.")
    lines.append("**Contrainte concrète, pas une indication approximative** : "
                  "sur l'ensemble des variables ci-dessous, au moins un fait, "
                  "un acteur ou une citation de l'article doit illustrer une "
                  "force attractive (coopération, stabilisation, innovation...) "
                  "— pas nécessairement une par variable, mais le texte ne peut "
                  "pas se limiter uniquement aux forces répulsives (tensions, "
                  "frictions, crises). Un ton d'article tendu ou critique ne "
                  "dispense pas de cette exigence : une institution peut être "
                  "contestée ET produire, dans le même article, un effet "
                  "stabilisateur concret que ses détracteurs eux-mêmes "
                  "reconnaissent.")
    lines.append("")
    lines.append("**Couverture des variables pilotes** (repérables au tag "
                  "[VARIABLE PILOTE] ci-dessous) : chacune doit trouver au "
                  "moins une résonance explicite dans l'article — un fait, un "
                  "chiffre, un acteur ou une conséquence concrète, pas "
                  "nécessairement liée à ses forces attractives/répulsives "
                  "précises — même si elle semble moins centrale à l'angle "
                  "que tu choisis. Ne laisse aucune variable pilote "
                  "totalement absente du texte sous prétexte qu'une autre se "
                  "prête mieux au récit.")
    lines.append("")
    lines.append("**Variables contraintes de ce scénario** (repérables au tag "
                  "[VARIABLE CONTRAINTE] ci-dessous) : une variable contrainte "
                  "n'est PAS une valeur figée ni un simple état défavorable — "
                  "c'est une limite structurelle sur l'espace des trajectoires "
                  "accessibles dans ce scénario précis. Elle peut évoluer, "
                  "mais son évolution reste bornée par la logique du monde "
                  "décrite plus haut (section ÉTAT DU MONDE / logique "
                  "système) : elle ne peut PAS basculer vers son extrême "
                  "opposé sans qu'une rupture structurelle majeure du "
                  "scénario le justifie explicitement. Déduis le sens de "
                  "cette borne (dans quelle direction la variable est "
                  "empêchée d'évoluer librement) depuis la logique narrative "
                  "du scénario déjà fournie, pas depuis une valeur imposée. "
                  "Exemple : dans un scénario de repli territorial, une "
                  "variable de mobilité humaine contrainte ne peut pas être "
                  "dépeinte comme en forte ouverture soudaine, même si elle "
                  "peut légèrement fluctuer — sauf événement de rupture "
                  "explicite dans le corpus.")
    lines.append("")

    for var_slug in priority[:MAX_VARIABLES_DETAIL]:
        state = variable_states.get(var_slug, {})
        level      = state.get("level", "?")
        volatility = state.get("volatility", "?")
        state_logic = state.get("state_logic", "")
        dynamics    = state.get("dominant_dynamics", [])

        is_pilot = var_slug in pilots
        is_visible = var_slug in vars_vis
        is_constrained = var_slug in constrained
        tag = ""
        if is_visible:
            tag = " [VARIABLE PRINCIPALE]"
        elif is_pilot:
            tag = " [VARIABLE PILOTE]"
        elif is_constrained:
            tag = " [VARIABLE CONTRAINTE]"

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

        # Forces attractives/répulsives — source : section 3 du corps
        # markdown ('Dynamique interne'), voir loader._extract_forces_
        # from_body. Section 4 ('Structure causale') volontairement
        # ignorée (doublon, décision du 15 août).
        forces_attractives = all_variables.get(var_slug, {}).get("forces_attractives", [])
        if forces_attractives:
            lines.append("- Forces attractives : {}".format(", ".join(forces_attractives[:4])))

        forces_repulsives = all_variables.get(var_slug, {}).get("forces_repulsives", [])
        if forces_repulsives:
            lines.append("- Forces répulsives : {}".format(", ".join(forces_repulsives[:4])))

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

    # ── Priorité -1 : signal forcé (ajouté le 2 août 2026) ──────────────
    # Contourne délibérément select_trajectory_events()/la rotation à
    # mémoire ci-dessous : un signal forcé DOIT apparaître dans cet
    # article précis, peu importe s'il a déjà été beaucoup utilisé ou
    # si d'autres jalons ont un score de priorité plus élevé. Affiché en
    # premier, dans son propre bloc, pour qu'il ne soit jamais noyé/coupé
    # si le prompt devient long.
    forced_signal = snapshot.get("forced_signal_event")
    if forced_signal:
        lines.append("**Signal forcé** [OBLIGATOIRE — doit être mentionné dans l'article]")
        lines.append("- [{}] {} :".format(
            forced_signal.get("date_bascule", ""), forced_signal.get("evenement_cle", "")
        ))
        lines.append("  → {} : {}".format(
            forced_signal.get("variable", "").replace("_", " "), forced_signal.get("evolution", "")
        ))
        lines.append("")

    # ── Priorité 0 : événements custom injectés
    # Plafonnés par pertinence + rotation à mémoire depuis le 2 août 2026
    # (voir loader.select_relevant_events -- avant, TOUS les événements
    # custom d'un scénario étaient inclus ici sans limite, grossissant
    # indéfiniment avec le vault). La vue d'ensemble complète reste
    # disponible plus haut dans le prompt, section "Perturbations custom
    # actives" (voir build_journalistic_brief) -- volontairement moins
    # coûteuse par événement (une ligne tronquée), donc plafonnée plus
    # large, pour ne jamais perdre la vision globale du monde même quand
    # le détail complet ci-dessous est filtré.
    custom_events_bruts = snapshot.get("custom_events", [])
    forced_event_slug = None
    forcer_resolu = snapshot.get("forcer_resolu")
    if forcer_resolu and forcer_resolu.get("type") == "evenement" and forcer_resolu.get("event"):
        forced_event_slug = forcer_resolu["event"].get("slug")
    custom_events = select_relevant_events(
        custom_events_bruts, thematique, scenario_slug,
        forced_event_slug=forced_event_slug, max_events=8, dry_run=dry_run,
    )
    if custom_events:
        lines.append("**Événements injectés** [CUSTOM — font partie de ce monde]"
                      + (" — {} sur {} au total, les plus pertinents pour cet article".format(
                          len(custom_events), len(custom_events_bruts))
                         if len(custom_events_bruts) > len(custom_events) else ""))
        for ev in custom_events:
            forced_badge = " [FORCÉ]" if ev.get("forced") else ""
            lines.append("- [{}]{} {} :".format(
                ev["date_label"], forced_badge, ev["name"]
            ))
            lines.append("  → {}".format(ev["description"][:100] + "..."
                         if len(ev["description"]) > 100 else ev["description"]))
            # Ajouté le 3 août 2026 (audit de complétude) : "realisation"
            # était chargé par loader.py mais jamais affiché -- décrit
            # comment l'événement s'est concrètement déroulé, distinct de
            # "description" (mise en scène narrative) et "consequences"
            # (effets en aval, déjà affichés juste après).
            if ev.get("realisation"):
                lines.append("  → Déroulement : {}".format(
                    ev["realisation"][:80] + "..."
                    if len(ev["realisation"]) > 80 else ev["realisation"]
                ))
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
    # Bug corrigé le 3 août 2026 (audit de complétude demandé par David) :
    # seules les ruptures de portée "structurant" étaient affichées ici.
    # Les ruptures "majeur" (3+ variables touchées, OU variable pilote +
    # rupture "core" -- la portée la PLUS significative dans le système de
    # classement de build_trajectory() dans snapshot.py) n'étaient jamais
    # montrées : snapshot["trajectory_majors"], calculé exprès pour ça,
    # n'était lu nulle part dans tout prompt_builder.py. Corrigé en
    # affichant ces jalons majeurs en priorité, avant les structurants.
    majeurs_generiques = snapshot.get("trajectory_majors", [])
    if majeurs_generiques:
        lines.append("**Ruptures majeures** (contexte de fond, portée large)")
        for j in majeurs_generiques[:MAX_JALONS_RUPTURES_MAJEURES]:
            lines.append("- [{}] {}".format(
                j["type"].upper()[:3],
                j["content"]
            ))
        lines.append("")

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

    # Angle spécifique depuis config -- écrasé si un forçage "sujet_central"
    # (voir snapshot.py, ajouté le 2 août 2026) a produit une directive :
    # celle-ci prime toujours sur un angle_specifique manuel, puisque le
    # forçage sujet_central est une demande plus explicite/récente.
    angle_config = config.get("article", {}).get("angle_specifique", "")
    forced_angle = (snapshot or {}).get("forced_angle_directive")
    if forced_angle:
        angle_config = forced_angle
    if angle_config:
        lines.append("**Angle spécifique demandé** : {}".format(angle_config))
        lines.append("")

    # Titre suggéré
    titre_config = config.get("article", {}).get("titre_suggere", "")
    if titre_config:
        lines.append("**Titre suggéré** : {}".format(titre_config))
        lines.append("")

    # Date fictive — corrigé le 10 août 2026 (retour de David : la date du
    # nom de fichier, calculée par generate.py/generate_series.py pour
    # espacer les articles d'une série, ne servait qu'au slug du nom de
    # fichier — jamais transmise au LLM, qui inventait donc sa propre date,
    # sans lien avec celle du nom de fichier. Convergence observée vers une
    # même date récurrente sur plusieurs articles, cohérente avec une
    # consigne trop ouverte ("une date crédible en 2098" sans ancrage).
    date_fictive_config = config.get("article", {}).get("date_fictive", "")
    if date_fictive_config:
        lines.append(
            "**Date de publication** : {} — reprends cette date exacte, "
            "ne la remplace pas par une autre.".format(date_fictive_config)
        )
    else:
        lines.append("**Date de publication** : à définir dans l'article — une date crédible en 2098")
    lines.append("")

    # Consigne finale
    lines.append("---")
    lines.append("")
    lines.append("Écris maintenant l'article. Commence directement par le titre.")
    lines.append("")
    lines.append("Contraintes impératives :")
    # Renforcement du 10 août 2026 (chantier "dérive du LLM sur la longueur
    # réelle des articles", backlog Partie 1 point 1) : la longueur était
    # déjà donnée plus haut ("**Format** : ... | **Longueur** : ..."), mais
    # seulement comme ligne de métadonnée passive, jamais reprise dans ce
    # bloc final juste avant génération — la seule série d'instructions
    # explicitement qualifiées d'"impératives". Répétée ici, reformulée en
    # contrainte dure, au même niveau que les autres règles de ce bloc.
    lines.append(
        "- **Longueur impérative : {}** — ne t'arrête pas avant la borne "
        "basse, ne dépasse pas la borne haute. C'est une contrainte dure, "
        "pas une indication approximative.".format(longueur)
    )
    lines.append("- Le titre doit être accrocheur et ancré dans le monde décrit")
    if date_fictive_config:
        lines.append(
            "- La date de publication est **{}** — reprends cette date exacte "
            "sous le titre, n'en invente pas une autre".format(date_fictive_config)
        )
    else:
        lines.append("- La date et le lieu de publication apparaissent sous le titre")
    lines.append("- L'article utilise des noms propres inventés mais crédibles (personnes, lieux, organisations)")
    lines.append(
        "- La signature du journaliste apparaît UNE SEULE FOIS, immédiatement "
        "sous la date de publication — jamais en fin d'article, jamais répétée"
    )
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


def build_geographie_context(snapshot, thematique=None, config=None):
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

    config : dict | None — ajouté le 3 août 2026. Sert uniquement à lire
    config.get("zone_slug") quand un élément est forcé (mode "forcer" de
    generate.py) : cette zone est ajoutée à zones_pertinentes même en
    l'absence de filtered_instances qui la porteraient (cas d'un événement
    ou d'un signal forcé, où filtered_instances reste générique). Optionnel
    pour rester compatible avec les appels existants qui ne le fournissent
    pas encore (ex. le bloc de test en bas de ce fichier).
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

    # Bug corrigé le 3 août 2026 (retour de David, test réel mode Forcer sur
    # un événement, policy_reform) : zones_pertinentes ne venait QUE de
    # filtered_instances (les instances auto-sélectionnées génériques,
    # totalement indépendantes de l'élément forcé pour un événement/signal --
    # contrairement à une instance forcée, qui devient elle-même la seule
    # filtered_instance). Résultat observé : consigne finale correcte
    # ("ancré dans Nuuk Knsf", déjà fixée le 2 août -- bug #8/§3.8, portée
    # par config["zone_slug"] et lue en ligne 1492 de build_prompt), mais la
    # section GÉOGRAPHIE détaillée ci-dessus affichait des zones sans rapport
    # (Genève, issues des instances génériques) et reléguait Nuuk dans la
    # liste compacte des zones non détaillées -- signal contradictoire pour
    # le LLM, qui n'a aucune description/tensions/alliés pour sa vraie zone
    # d'ancrage.
    #
    # Important : la zone forcée vit dans config["zone_slug"] (article_config
    # dans generate.py), PAS dans snapshot["zone_slug"] (qui reste la zone
    # générique auto-calculée par snapshot.py, indépendante du forçage) --
    # exactement la même distinction que déjà gérée en ligne 1492 de
    # build_prompt() pour build_system_prompt(). Nécessite donc que config
    # soit désormais passé à cette fonction (voir signature + call site
    # modifiés ci-dessous/dans build_prompt).
    zone_forcee = (config or {}).get("zone_slug") or snapshot.get("zone_slug")
    if zone_forcee and zone_forcee in slug_to_zone:
        zones_pertinentes.update(collect_zone_chain(zone_forcee, zone_forcee))

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

    # Zones détaillées (pertinentes) puis résumé court (autres) --
    # plafonné depuis le 2 août 2026 (voir docstring du module) : avant,
    # sorted_zones était parcourue en entier sans limite, grossissant
    # indéfiniment avec le vault (déjà ~60 zones sur un scénario mature).
    # Les zones pertinentes (ancrage de l'article) restent toujours
    # affichées en détail complet, sans plafond -- leur nombre est déjà
    # naturellement petit (dérivé de la chaîne de parenté de 1-2
    # instances/événements ancrés). Seul le résumé "contexte de fond" est
    # plafonné, avec une liste de noms seuls (sans description) pour le
    # reste -- préserve la vision globale du monde à coût minimal plutôt
    # que de faire disparaître ces zones entièrement.
    PLAFOND_ZONES_RESUME = 20
    in_summary = False
    n_summary_affichees = 0
    zones_hors_plafond = []
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
            # Résumé court — une ligne, plafonné
            if n_summary_affichees < PLAFOND_ZONES_RESUME:
                nom   = zone.get("nom", "?")
                desc  = zone.get("description", "")
                short = desc[:80] + "..." if len(desc) > 80 else desc
                lines.append("- **{}**{} : {}".format(nom, parent_txt, short))
                n_summary_affichees += 1
            else:
                zones_hors_plafond.append(zone.get("nom", "?"))

    if zones_hors_plafond:
        lines.append("- (+ {} autres zones de ce monde, non détaillées : {})".format(
            len(zones_hors_plafond), ", ".join(zones_hors_plafond)
        ))

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
        # Chantier trajectoire (9 août 2026) : remplace etat_temporel par
        # trajectoire (axe unique) + est_clandestin (booléen indépendant,
        # affichable EN PLUS de la position sur l'axe — auparavant
        # impossible : "clandestin" était une valeur d'etat_temporel parmi
        # d'autres, une entité ne pouvait pas être à la fois "dominant" et
        # "clandestin", par exemple).
        trajectoire = inst.get("trajectoire", "mature")
        est_clandestin = inst.get("est_clandestin", False)
        impact = inst.get("impact_systemique_global", 0)
        is_custom = inst.get("injection", {}).get("type") == "custom"
        annee_injection = inst.get("injection", {}).get("annee_injection", "")

        traj_badge = trajectoire.upper()
        clandestin_badge = " [CLANDESTIN]" if est_clandestin else ""

        # Badge custom
        custom_badge = " [CUSTOM — injecté en {}]".format(annee_injection) if is_custom and annee_injection else ""

        lines.append("**{}** [{}]{}{} [impact:{}/5]".format(
            inst["name"], traj_badge, clandestin_badge, custom_badge, impact
        ))

        # Description journalistique
        desc = inst.get("description_journalistique", "")
        if desc:
            lines.append(desc)

        # Ajouté le 3 août 2026 (audit de complétude demandé par David) :
        # responsabilites et signes_distinctifs étaient chargés par
        # loader.py mais jamais affichés dans le prompt -- pertes de
        # contenu réelles, distinctes de description_journalistique
        # (récit d'origine/statut, écrit "de l'extérieur") et de
        # tensions_narratives (déjà affiché ci-dessous) :
        #   - responsabilites : ce que l'entité FAIT concrètement (actions,
        #     leviers, méthodes -- souvent avec des noms propres et détails
        #     opérationnels absents de description_journalistique)
        #   - signes_distinctifs : détails concrets/visuels/symboliques qui
        #     la rendent reconnaissable et citable dans un article (slogans,
        #     symboles, pratiques caractéristiques)
        # Affichés en entier comme description_journalistique (pas tronqués
        # comme tensions_narratives) -- ce sont les deux champs qui
        # apportaient le plus de matière concrète et perdue.
        responsabilites = inst.get("responsabilites", "")
        if responsabilites:
            lines.append("*Responsabilités* : {}".format(responsabilites))

        signes = inst.get("signes_distinctifs", "")
        if signes:
            lines.append("*Signes distinctifs* : {}".format(signes))

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

        # Ajouté le 7 août 2026 (audit de complétude, point 1.2 du backlog) :
        # type_relation_dominante/annee_debut/annee_fin étaient chargés par
        # loader.py (fm.get(...)) et survivaient intacts jusqu'au snapshot,
        # mais jamais lus ici -- même perte silencieuse que celle corrigée le
        # 3 août pour responsabilites/signes_distinctifs, restée dans un angle
        # mort de cet audit. type_relation_dominante est UNE valeur par fiche
        # (tonalité dominante des relations de l'entité, pas un tag par allié/
        # opposant précis) -- affichée en une ligne distincte des listes
        # Alliés/Opposants ci-dessus plutôt que mélangée à chaque nom.
        relation_dominante = inst.get("type_relation_dominante", "")
        annee_debut = inst.get("annee_debut")
        annee_fin   = inst.get("annee_fin")
        if relation_dominante:
            if annee_fin:
                periode = " ({}–{})".format(annee_debut, annee_fin)
            elif annee_debut:
                periode = " (depuis {})".format(annee_debut)
            else:
                periode = ""
            lines.append("*Relation dominante* : {}{}".format(relation_dominante, periode))

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
    geographie_section = build_geographie_context(snapshot, thematique=thematique, config=config)

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

    # Bug corrigé le 3 août 2026 (retour de David, test réel mode Semi-guidé
    # sur breakdown/sciences_technologies avec --article-longueur breve) :
    # ce calcul ignorait totalement config["article"]["longueur"] et
    # recalculait la longueur uniquement depuis thematique.format_dominant
    # -- doublon divergent de la logique déjà correcte de
    # build_journalistic_brief() (ligne ~974), qui priorise bien l'override
    # de config quand il est présent et valide. Résultat : les MÉTADONNÉES
    # affichaient une longueur différente de celle réellement demandée au
    # LLM dans la CONSIGNE DE RÉDACTION -- vrai dans TOUS les cas où
    # config["article"]["longueur"] diffère du format_dominant de la
    # thématique, pas seulement sur override explicite. Comme "breve" est
    # la valeur par défaut de config.yaml (indépendante de la thématique),
    # ce décalage touchait potentiellement la majorité des articles déjà
    # générés, dès que leur thématique n'a pas elle-même format_dominant
    # == "breve". Corrigé en réutilisant exactement la même logique de
    # priorité que build_journalistic_brief().
    format_dom = thematique.get("format_dominant", "breve")
    config_lon = config.get("article", {}).get("longueur", "auto")
    if config_lon and config_lon != "auto" and config_lon in FORMAT_LONGUEUR:
        longueur = FORMAT_LONGUEUR[config_lon]
    else:
        longueur = FORMAT_LONGUEUR.get(format_dom, "300 à 500 mots")

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
