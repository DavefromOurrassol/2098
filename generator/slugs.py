"""
slugs.py — slug commun à tous les scripts (S24, 31 oct 2026)

Une seule source de vérité pour transformer un nom en slug. Remplace les
copies dupliquées (api.py, create_entities_and_instances.py, export_revues.py
slug_pipeline, etc.), qui divergeaient et transformaient ø, æ, œ, ß, ł… en
« _ » : ces lettres ne se décomposent pas en NFD, elles sont donc
translittérées d'abord.

    slugify("Bjørn Sørensen")          -> "bjorn_sorensen"
    slugify("Réseau des Métropoles-Nœuds") -> "reseau_des_metropoles_noeuds"
"""

import re
import unicodedata

TRANSLIT = {
    "ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE",
    "ß": "ss", "ẞ": "SS", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D",
    "ð": "d", "Ð": "D", "þ": "th", "Þ": "TH", "ı": "i",
}


def slugify(text):
    """Nom -> slug : translittération (ø, æ, œ, ß, ł…), puis NFD sans
    diacritiques, minuscules, tout non-alphanumérique -> « _ »."""
    s = "".join(TRANSLIT.get(c, c) for c in str(text or ""))
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")
