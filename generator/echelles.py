"""
echelles.py — Ourrassol 2098
-----------------------------
Source unique de la convention d'échelle des variables (décidée le 27
septembre 2026, migration migrer_echelles.py) :

  - pour les 12 variables, level 0 = situation calme/stable,
    level 100 = crise/pression maximale (bloc `echelle:` de chaque fiche
    variables/*.md, champs zero/cent) ;
  - dans impact_sur_variables : delta_level = FORCE (toujours positive),
    polarite = SENS (+1 = la variable monte = aggrave/intensifie,
    -1 = la variable baisse = apaise/stabilise).

Utilisé par tous les prompts qui montrent des niveaux ou demandent un
impact chiffré (prompt_builder.py, inject_custom_events.py,
inject_custom_signals.py, enrich_minimal.py) -- pour que la convention
soit formulée à UN seul endroit.
"""

import re
from pathlib import Path

import yaml

VARIABLES_DIR = Path(__file__).resolve().parent.parent / "variables"

_cache = None


def charger_echelles():
    """Retourne {slug: {"zero": str, "cent": str}} lu dans variables/*.md.
    Variable sans bloc `echelle:` = absente du dict (jamais d'exception)."""
    global _cache
    if _cache is not None:
        return _cache
    _cache = {}
    if not VARIABLES_DIR.is_dir():
        return _cache
    for path in VARIABLES_DIR.glob("*.md"):
        try:
            raw = path.read_text(encoding="utf-8")
            m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*\n", raw, re.DOTALL)
            if not m:
                continue
            fm = yaml.safe_load(re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))) or {}
        except (OSError, yaml.YAMLError):
            continue
        ech = fm.get("echelle") or {}
        if isinstance(ech, dict) and ech.get("zero") and ech.get("cent"):
            _cache[path.stem] = {"zero": ech["zero"], "cent": ech["cent"]}
    return _cache


def texte_echelle(slug):
    """'0 = … | 100 = …' pour une variable, ou '' si pas d'échelle."""
    ech = charger_echelles().get(slug)
    if not ech:
        return ""
    return "0 = {} | 100 = {}".format(ech["zero"], ech["cent"])


CONVENTION_NIVEAUX = (
    "CONVENTION DES NIVEAUX (identique pour les 12 variables) : level 0 = "
    "situation calme et stable, level 100 = crise ou pression maximale. "
    "Un niveau élevé signifie donc toujours une situation plus tendue, "
    "jamais une situation plus favorable."
)

CONSIGNE_IMPACT = (
    "CONVENTION DES IMPACTS : delta_level est la FORCE de l'effet, TOUJOURS "
    "un nombre POSITIF (jamais de signe moins). polarite est le SENS : +1 si "
    "l'événement fait MONTER le niveau de la variable (il aggrave, intensifie, "
    "met sous pression), -1 s'il le fait BAISSER (il apaise, stabilise, "
    "résout). Raisonne avec l'échelle de chaque variable ci-dessus : par "
    "exemple une guerre, une crise ou un effondrement donnent presque "
    "toujours polarite +1 ; un accord, une réforme réussie ou une "
    "reconstruction donnent polarite -1."
)


def verifier_impact(delta_level, polarite, prefixe=""):
    """Contrôle mécanique de la convention. Retourne une liste de problèmes."""
    issues = []
    try:
        d = float(delta_level)
        if d < 0:
            issues.append(f"{prefixe}delta_level={delta_level} est négatif : la force doit "
                          f"être positive, le sens se donne uniquement avec polarite")
    except (TypeError, ValueError):
        pass  # déjà signalé par les contrôles existants de chaque script
    if polarite not in (1, -1, "1", "-1"):
        issues.append(f"{prefixe}polarite={polarite!r} invalide (attendu 1 ou -1)")
    return issues
