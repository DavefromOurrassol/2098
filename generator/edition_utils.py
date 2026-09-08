"""
edition_utils.py — Ourrassol 2098
----------------------------------
Module central pour la notion d'édition mensuelle (chantier "Éditions
datées", scopé le 30 août 2026, design tranché le 2 septembre 2026).

Regroupe :
  - la conversion année/mois <-> date de référence fractionnaire
    (ex. 2098 + 8 -> 2098.08), utilisée pour remplacer le "2098" en dur
    dans snapshot.py (duree_effet, year) ;
  - le tirage du jour de rédaction d'un article, à l'intérieur du mois
    de l'édition active (remplace les listes DATES_2098 figées,
    dupliquées dans generate.py/generate_series.py/generate_manual.py) ;
  - la lecture/écriture du registre state/editions.json, qui trace
    l'édition active (UNE SEULE, partagée par les 6 scénarios --
    décision explicite de David le 2 septembre : les mondes fictifs
    avancent en parallèle, pas indépendamment) et l'historique des
    éditions passées, par scénario.

IMPORTANT : toujours passer par edition_date_to_float()/
float_to_edition_date() pour construire ou lire une date de référence
-- ne jamais la construire par concaténation de chaînes (piège identifié
le 2 septembre : sans division par 100, "2098." + str(mois) casse la
comparaison flottante pour les mois à un chiffre, ex. 2098.9 > 2098.12
alors que septembre < décembre).

Seuls generate_series.py et generate_manual.py écrivent dans
state/editions.json (via enregistrer_edition()) -- generate.py (article
isolé) ne fait que LIRE l'édition active (lire_edition_active()),
jamais ne la crée ni ne l'avance. Décision explicite de David
(2 septembre 2026) : un article isolé suit l'édition en cours, il n'en
déclenche pas une nouvelle.
"""

import calendar
import json
import os
import random
from datetime import datetime

STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
EDITIONS_FILE = os.path.join(STATE_DIR, "editions.json")

MOIS_FR = [
    None, "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


# ─────────────────────────────────────────
# CONVERSION DATE DE RÉFÉRENCE (point 2)
# ─────────────────────────────────────────

def edition_date_to_float(annee, mois):
    """
    Construit la date de référence fractionnaire d'une édition.
    Ex. edition_date_to_float(2098, 8) -> 2098.08

    Division par 100 (pas concaténation de chaîne) : garantit le
    zéro-padding implicite du mois (8/100 = 0.08, 12/100 = 0.12),
    condition nécessaire pour que la comparaison flottante entre deux
    éditions reste correcte quel que soit le mois.
    """
    if not (1 <= int(mois) <= 12):
        raise ValueError("mois hors plage [1-12] : {!r}".format(mois))
    return int(annee) + int(mois) / 100.0


def float_to_edition_date(valeur):
    """
    Inverse de edition_date_to_float() -- retourne (annee, mois).
    round() sur la partie décimale pour absorber l'imprécision flottante
    habituelle (2098.08 peut être stocké en mémoire comme
    2098.0799999...).
    """
    annee = int(valeur)
    mois = round((valeur - annee) * 100)
    if not (1 <= mois <= 12):
        raise ValueError(
            "date de référence invalide : {!r} -> mois calculé {} hors plage".format(valeur, mois)
        )
    return annee, mois


# ─────────────────────────────────────────
# JOUR DE RÉDACTION D'UN ARTICLE (point 2)
# ─────────────────────────────────────────

def tirer_jour_edition(annee, mois):
    """
    Tire un jour au hasard dans le mois de l'édition active et retourne
    la date formatée en français, ex. "6 août 2098" -- même format
    d'affichage que l'ancien DATES_2098, pour ne rien casser en aval
    (api.py, prompt_builder.py consomment déjà ce format en texte
    libre).

    Remplace les 3 copies dupliquées de DATES_2098 (generate.py,
    generate_series.py, generate_manual.py) par un tirage dynamique
    borné au mois réel de l'édition, au lieu d'une liste figée de
    ~2 dates/mois sur toute l'année.
    """
    nb_jours = calendar.monthrange(int(annee), int(mois))[1]
    jour = random.randint(1, nb_jours)
    return "{} {} {}".format(jour, MOIS_FR[int(mois)], int(annee))


def parser_date_fictive(date_str):
    """
    Inverse de tirer_jour_edition() -- parse une date française en texte
    libre (ex. "6 août 2098", telle que stockée dans date_evenement du
    frontmatter d'un article) et retourne (jour, mois, annee), ou None
    si le format n'est pas reconnu (ex. champ vide, ancien format).
    Ajouté le 2 septembre 2026 pour audit_sujets_edition.py.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    parts = date_str.strip().split()
    if len(parts) != 3:
        return None
    jour_str, mois_str, annee_str = parts
    try:
        jour = int(jour_str)
        annee = int(annee_str)
    except ValueError:
        return None
    mois_str_normalise = mois_str.strip().lower()
    try:
        mois = MOIS_FR.index(mois_str_normalise)
    except ValueError:
        return None
    return jour, mois, annee


# ─────────────────────────────────────────
# REGISTRE state/editions.json (point 3)
# ─────────────────────────────────────────

def _charger_registre():
    """Charge editions.json, ou une structure vide si absent/corrompu --
    jamais d'exception qui bloquerait un appelant en lecture seule
    (generate.py).

    editions_connues : liste [{"numero", "annee", "mois"}] -- TOUTE
    édition qui a un jour existé, générée ou juste déclarée via
    definir_edition.py. Distinct de `historique` (qui ne compte que les
    articles RÉELLEMENT produits, par scénario) -- nécessaire pour que
    le numéro reste stable même pour une édition déclarée mais jamais
    utilisée (bug trouvé le 2 septembre 2026 : sans ce registre séparé,
    avancer deux fois de suite sans jamais générer réattribuait le même
    numéro à chaque mois "sauté", puisque rien n'était mémorisé nulle
    part entre les deux appels)."""
    if not os.path.exists(EDITIONS_FILE):
        return {"edition_active": None, "editions_connues": [], "historique": []}
    try:
        with open(EDITIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("edition_active", None)
        data.setdefault("editions_connues", [])
        data.setdefault("historique", [])
        return data
    except (json.JSONDecodeError, OSError):
        return {"edition_active": None, "editions_connues": [], "historique": []}


def _sauver_registre(data):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(EDITIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def lire_edition_active():
    """
    Retourne {"numero": int, "annee": int, "mois": int} ou None si
    aucune édition n'a jamais été enregistrée (state/editions.json
    absent/vide -- déploiement neuf ou avant le tout premier lancement
    de série).

    Lecture seule -- utilisée par generate.py pour un article isolé,
    et par audit_sujets_edition.py comme valeur par défaut de
    --annee/--mois.
    """
    return _charger_registre().get("edition_active")


def _resoudre_numero(data, annee, mois):
    """Retourne le numéro d'édition pour (annee, mois) -- réutilise celui
    déjà connu dans editions_connues (couvre à la fois les éditions
    générées ET les éditions juste déclarées), sinon en attribue un
    nouveau (max existant + 1). Factorisé le 2 septembre 2026 entre
    enregistrer_edition() et definir_edition_active(), qui partagent
    cette même logique."""
    for entree in data["editions_connues"]:
        if (entree["annee"], entree["mois"]) == (annee, mois):
            return entree["numero"]
    return max([e["numero"] for e in data["editions_connues"]], default=0) + 1


def _memoriser_edition_connue(data, numero, annee, mois):
    """Ajoute (numero, annee, mois) à editions_connues s'il n'y est pas
    déjà -- idempotent, appelé par definir_edition_active() ET
    enregistrer_edition() pour que le numéro reste stable quelle que
    soit la première des deux fonctions qui touche cette édition."""
    deja_connue = any(
        (e["annee"], e["mois"]) == (annee, mois) for e in data["editions_connues"]
    )
    if not deja_connue:
        data["editions_connues"].append({"numero": numero, "annee": annee, "mois": mois})


def definir_edition_active(annee, mois):
    """
    Fixe directement l'édition active, SANS générer aucun article ni
    toucher à l'historique/nb_articles -- ajouté le 2 septembre 2026 à
    la demande de David, pour configurer/avancer le mois de l'édition
    indépendamment d'un lancement de série (nouvel outil
    definir_edition.py). Utile par exemple pour préparer l'édition
    active AVANT de générer un article isolé via generate.py, sans avoir
    à lancer une série complète juste pour ça.

    Différence avec enregistrer_edition() : celle-ci enregistre des
    articles RÉELLEMENT produits (appelée par generate_series.py/
    generate_manual.py après une sauvegarde réelle) et incrémente
    nb_articles dans l'historique. definir_edition_active() ne fait que
    déplacer le pointeur "édition active" -- si (annee, mois) n'existe
    pas encore, un numéro est attribué mais AUCUNE entrée d'historique
    n'est créée tant qu'aucun article n'a été réellement généré pour
    cette édition (l'historique reste un décompte d'articles produits,
    pas une liste d'éditions déclarées).

    Retourne le numéro d'édition (existant ou nouvellement attribué).
    """
    data = _charger_registre()
    annee, mois = int(annee), int(mois)
    numero = _resoudre_numero(data, annee, mois)
    _memoriser_edition_connue(data, numero, annee, mois)
    data["edition_active"] = {"numero": numero, "annee": annee, "mois": mois}
    _sauver_registre(data)
    return numero


def enregistrer_edition(scenario_slug, annee, mois, nb_articles=1):
    """
    Enregistre nb_articles articles réellement sauvegardés (jamais en
    dry-run) pour (annee, mois) sur ce scénario. Appelé par
    generate_series.py (une fois par run, avec le total du lot) et
    generate_manual.py (une fois par article sauvegardé via cmd_save).

    Édition GLOBALE (décision de David, 2 septembre 2026) : le numéro
    est partagé par les 6 scénarios, pas un numéro par scénario -- si
    (annee, mois) correspond à une édition déjà connue (active ou dans
    l'historique), son numéro est réutilisé ; sinon un nouveau numéro
    est attribué (max existant + 1). L'édition touchée devient
    systématiquement l'édition active, quel que soit le scénario --
    c'est ce que generate.py lira ensuite pour un article isolé, peu
    importe sur quel scénario portait le dernier run de série.
    """
    data = _charger_registre()
    annee, mois = int(annee), int(mois)
    numero = _resoudre_numero(data, annee, mois)
    _memoriser_edition_connue(data, numero, annee, mois)

    data["edition_active"] = {"numero": numero, "annee": annee, "mois": mois}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existante = next(
        (e for e in data["historique"]
         if e["numero"] == numero and e["scenario"] == scenario_slug),
        None,
    )
    if existante:
        existante["nb_articles"] += nb_articles
        existante["date_generation"] = now
    else:
        data["historique"].append({
            "numero": numero,
            "annee": annee,
            "mois": mois,
            "scenario": scenario_slug,
            "nb_articles": nb_articles,
            "date_generation": now,
        })

    _sauver_registre(data)
    return numero
