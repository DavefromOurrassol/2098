#!/usr/bin/env python3
"""
patch_s27_relecture_articles.py — 24 octobre 2026 (S27, point 2).

Relecture IA des articles (étape ⑤, et_si_main.verifier_articles) : sur
pacte_tabriz_2058, 7 passages relevés, 7 faux positifs. Trois défauts :
  - géographie confondue (Sahel, Lagos rangés dans la Zone Golfe) ;
  - statut de zone « en déclin » lu comme une disparition ;
  - rang contesté sur une formulation modeste, ou lore sans lien avec
    l'hypothèse discuté (entités « inchangées »).

Correctif, articles seulement (la relecture des phrases de la fiche d'événement
ne change pas) :
  1. le prompt donne les territoires de chaque zone dont le statut change, et
     trois règles de plus (zone limitée à ses territoires, déclin ≠ disparition,
     formulation modeste conforme ; entité inchangée jamais discutée) ;
  2. filtre sans IA : une justification au conditionnel ou par sous-entendu
     (« pourrait », « peut contredire », « sous-entend », « implicitement »,
     « minimise »…) est écartée, comme « omission » l'est déjà ;
  3. VERSION_ARTICLES v1 → v2 : la prochaine relecture refait l'appel.

Cible : generator/et_si_main.py (sauvegarde .bak_s27_relecture). Refuse un
second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_relecture_articles.py
"""

import shutil
import sys
from pathlib import Path

MARQUEUR = "def contradiction_article("
CIBLE = Path(__file__).resolve().parent / "et_si_main.py"

AJOUT = '''

# PATCH_S27_RELECTURE (24 oct 2026) : articles seulement. Justification au conditionnel ou par
# sous-entendu = pas une contradiction établie (7 faux positifs sur 7 avec pacte_tabriz_2058).
CONDITIONNEL = re.compile(r"pourrait|pourraient|peut contredire|peut evoquer|peut sembler|sous-entend"
                          r"|implicitement|suggere|laisse entendre|minimis")


def contradiction_article(fait):
    return vraie_contradiction(fait) and not CONDITIONNEL.search(_plie(fait))


def territoires_zones(data, sc, max_par_zone=25):
    """Lignes « zone : territoires » pour les zones dont l'hypothèse change le statut."""
    ps = data["par_scenario"].get(sc) or {}
    zones = [z.get("zone") for z in (ps.get("lecture") or {}).get("zones_statut") or [] if z.get("zone")]
    if not zones:
        return []
    by = {z.get("slug"): z for z in ap.zones_geo(sc)}
    lignes = []
    for slug in dict.fromkeys(zones):
        z = by.get(slug) or {}
        ents = [str(o.get("entite")) for o in z.get("origine_reelle") or [] if isinstance(o, dict) and o.get("entite")]
        if ents:
            plus = f" (+{len(ents) - max_par_zone})" if len(ents) > max_par_zone else ""
            lignes.append(f"- {z.get('nom') or slug} ({slug}) : {', '.join(ents[:max_par_zone])}{plus}")
    return lignes
'''

REMPLACEMENTS = [
    ('VERSION_ARTICLES = "v1"', 'VERSION_ARTICLES = "v2-territoires-conditionnel"   # PATCH_S27_RELECTURE'),
    (
        "def vraie_contradiction(fait):\n    return not PAS_UNE_CONTRADICTION.search(_plie(fait))\n",
        "def vraie_contradiction(fait):\n    return not PAS_UNE_CONTRADICTION.search(_plie(fait))\n" + AJOUT,
    ),
    (
        "        etats = etats_cites(data, sc, corps)\n        user = (",
        "        etats = etats_cites(data, sc, corps)\n"
        "        terr = territoires_zones(data, sc)   # PATCH_S27_RELECTURE\n"
        "        user = (",
    ),
    (
        '                   "JAMAIS une contradiction) :\\n" + "\\n".join(etats) + "\\n\\n" if etats else "")\n',
        '                   "JAMAIS une contradiction) :\\n" + "\\n".join(etats) + "\\n\\n" if etats else "")\n'
        '                + ("TERRITOIRES DES ZONES DONT LE STATUT CHANGE (un lieu absent de ces listes n\'est PAS '
        'concerné) :\\n" + "\\n".join(terr) + "\\n\\n" if terr else "")\n',
    ),
    (
        '"historique au passé est CORRECT. Une omission n\'est pas une contradiction. En cas de doute, ne "',
        '"historique au passé est CORRECT. Une omission n\'est pas une contradiction. "\n'
        '                "Un statut de zone (en déclin, fragmenté…) ne dit JAMAIS que ses lieux, ses récits ou ses '
        'acteurs cessent d\'exister. "\n'
        '                "Une entité dont le rang monte n\'est contredite que si l\'article la dit disparue, '
        'effondrée ou en déclin après la date ; une formulation modeste ou neutre est conforme. "\n'
        '                "Le rang d\'une entité « inchangé par l\'hypothèse » ne se discute JAMAIS : tu ne relis '
        'que les conséquences de l\'hypothèse. "\n'
        '                "Ne relève que ce qui est CERTAINEMENT faux, sans conditionnel. En cas de doute, ne "',
    ),
    (
        '            if m and m.search(raw) and vraie_contradiction(x.get("fait")):\n',
        '            if m and m.search(raw) and contradiction_article(x.get("fait")):   # PATCH_S27_RELECTURE\n',
    ),
]


def main() -> int:
    if not CIBLE.exists():
        print(f"✗ Fichier introuvable : {CIBLE}")
        return 1
    texte = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        print("✗ Patch déjà appliqué (marqueur présent) — rien fait.")
        return 1
    for i, (ancien, nouveau) in enumerate(REMPLACEMENTS, 1):
        n = texte.count(ancien)
        if n != 1:
            print(f"✗ Remplacement {i} : {n} occurrence(s) au lieu d'une — rien écrit.")
            return 1
        texte = texte.replace(ancien, nouveau)
    try:
        compile(texte, str(CIBLE), "exec")
    except SyntaxError as e:
        print(f"✗ Le fichier patché ne compile pas ({e}) — rien écrit.")
        return 1
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s27_relecture"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché ({len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_s27_relecture")
    return 0


if __name__ == "__main__":
    sys.exit(main())
