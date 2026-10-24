#!/usr/bin/env python3
"""
patch_s27_relecture_appliquee.py — 24 octobre 2026 (S27, point 2, suite).

Après patch_s27_relecture_articles.py, la relecture IA des articles de
pacte_tabriz_2058 relevait encore 3 faux positifs, dont un vrai bug :
  - les faits donnés à l'IA venaient de TOUTE la lecture IA, y compris les
    propositions sautées à l'étape ④ (Factions ABS → dominant, Bassin Caspien
    stable, Ormuz disparu) ;
  - l'IA discutait le rang d'entités que l'hypothèse ne touche pas ;
  - elle contestait une formulation modeste d'une entité dont le rang monte.

Correctif (sans IA) :
  1. hypothèse appliquée (journal <id>.applique.json présent) : trajectoires et
     statuts de zone retenus = ceux qui sont appliqués dans le vault (état actuel
     = résultat de la simulation). Vaut pour les faits, les états cités, les
     articles à relire, les territoires — et la relecture de la fiche d'événement ;
  2. filtre des passages d'articles : écarté si la justification ne cite que des
     entités inchangées ; écarté si elle ne porte que sur des entités dont le rang
     monte et que l'extrait ne dit ni déclin ni disparition ;
  3. VERSION_ARTICLES → v3.

Cible : generator/et_si_main.py (après patch_s27_relecture_articles.py ;
sauvegarde .bak_s27_appliquee). Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_relecture_appliquee.py
"""

import shutil
import sys
from pathlib import Path

MARQUEUR = "def retenues("
PREREQUIS = "def contradiction_article("
CIBLE = Path(__file__).resolve().parent / "et_si_main.py"

AIDES = '''_RETENUES = {}


def retenues(data):
    """PATCH_S27_APPLIQUEE : None si l'hypothèse n'est pas appliquée (toute la lecture compte) ;
    sinon {(sc, "t"|"z"): slugs} des trajectoires et statuts de zone APPLIQUÉS (état actuel = résultat)."""
    hid = data.get("id")
    if hid not in _RETENUES:
        if not (ap.APP_DIR / f"{hid}.applique.json").exists():
            _RETENUES[hid] = None
        else:
            ops, _ = ap.construire_plan(data)
            r = {}
            for o in ops:
                if o.get("alerte") == "déjà appliqué" and o["genre"] == "trajectoire":
                    r.setdefault((o["sc"], "t"), set()).add(o["instance"])
                elif o.get("alerte") == "déjà appliqué" and o["genre"] == "zone":
                    r.setdefault((o["sc"], "z"), set()).add(o["zone"])
            _RETENUES[hid] = r
    return _RETENUES[hid]


def garde_traj(data, sc, t):
    r = retenues(data)
    return r is None or t.get("instance") in r.get((sc, "t"), set())


def garde_zone(data, sc, z):
    r = retenues(data)
    return r is None or z.get("zone") in r.get((sc, "z"), set())


def _annee(data):'''

FILTRE = '''def contradiction_article(fait, extrait=None, data=None, sc=None):
    if not vraie_contradiction(fait) or CONDITIONNEL.search(_plie(fait)):
        return False
    if data is None:
        return True
    # PATCH_S27_APPLIQUEE : la justification doit porter sur une conséquence de l'hypothèse.
    pf, pe = _plie(fait), _plie(extrait)
    cite = lambda nom: bool(nom) and (_plie(nom) in pf or forme_approchee(nom, pf))
    changes = [apr for nom, av, apr in etats_entites(data, sc) if cite(nom)]
    zn = noms_de_zones(sc)
    ps = data["par_scenario"].get(sc) or {}
    zones = [z.get("zone") for z in (ps.get("lecture") or {}).get("zones_statut") or []
             if z.get("zone") and garde_zone(data, sc, z)]
    cite_zone = any(_plie(s) in pf or _plie(zn.get(s, "")) in pf for s in zones if s)
    if not changes and not cite_zone:
        if any(len(n) >= 4 and cite(n) for n in trajectoires_du_scenario(sc)):
            return False   # ne parle que d'entités inchangées
    if changes and not cite_zone and all(_plie(a) in MONTEE for a in changes) and not DECLIN.search(pe):
        return False       # rang qui monte, extrait sans déclin ni disparition
    return True


MONTEE = {"ascendant", "dominant", "mature"}
DECLIN = re.compile(r"dispar|effondr|declin|n'existe plus|detrui|dissou|marginal|agonis|moribond|eteint"
                    r"|residuel|abandonn|ruine|chute|vaincu|liquide")'''

REMPLACEMENTS = [
    ('VERSION_ARTICLES = "v2-territoires-conditionnel"', 'VERSION_ARTICLES = "v3-appliquee"'),
    ("def _annee(data):", AIDES),
    # états des entités : seulement les trajectoires appliquées
    (
        "    for t in ((ps.get(\"lecture\") or {}).get(\"trajectoires\") or []) + ((ps.get(\"passe\") or {}).get(\"trajectoires\") or []):\n"
        "        if t.get(\"instance\") in vus:\n",
        "    for t in ((ps.get(\"lecture\") or {}).get(\"trajectoires\") or []) + ((ps.get(\"passe\") or {}).get(\"trajectoires\") or []):\n"
        "        if t.get(\"instance\") in vus or not garde_traj(data, sc, t):   # PATCH_S27_APPLIQUEE\n",
    ),
    # faits de l'hypothèse
    (
        "    for t in (lec.get(\"trajectoires\") or []) + (pas.get(\"trajectoires\") or []):\n"
        "        if t.get(\"instance\") in vus:\n"
        "            continue\n"
        "        vus.add(t.get(\"instance\"))\n"
        "        nom = t.get(\"nom\") or t.get(\"instance\")\n",
        "    for t in (lec.get(\"trajectoires\") or []) + (pas.get(\"trajectoires\") or []):\n"
        "        if t.get(\"instance\") in vus or not garde_traj(data, sc, t):   # PATCH_S27_APPLIQUEE\n"
        "            continue\n"
        "        vus.add(t.get(\"instance\"))\n"
        "        nom = t.get(\"nom\") or t.get(\"instance\")\n",
    ),
    (
        "    for z in lec.get(\"zones_statut\") or []:\n"
        "        faits.append(",
        "    for z in [z for z in lec.get(\"zones_statut\") or [] if garde_zone(data, sc, z)]:   # PATCH_S27_APPLIQUEE\n"
        "        faits.append(",
    ),
    # articles à relire
    (
        "                       if t.get(\"instance\")})\n"
        "        zones = {z[\"zone\"] for z in lec.get(\"zones_statut\") or [] if z.get(\"zone\")}\n",
        "                       if t.get(\"instance\") and garde_traj(data, sc, t)})   # PATCH_S27_APPLIQUEE\n"
        "        zones = {z[\"zone\"] for z in lec.get(\"zones_statut\") or [] if z.get(\"zone\") and garde_zone(data, sc, z)}\n",
    ),
    (
        "        noms = {t.get(\"nom\") for t in (lec.get(\"trajectoires\") or []) + (pas.get(\"trajectoires\") or [])}\n",
        "        noms = {t.get(\"nom\") for t in (lec.get(\"trajectoires\") or []) + (pas.get(\"trajectoires\") or [])\n"
        "                if garde_traj(data, sc, t)}   # PATCH_S27_APPLIQUEE\n",
    ),
    # territoires
    (
        "    zones = [z.get(\"zone\") for z in (ps.get(\"lecture\") or {}).get(\"zones_statut\") or [] if z.get(\"zone\")]\n"
        "    if not zones:\n",
        "    zones = [z.get(\"zone\") for z in (ps.get(\"lecture\") or {}).get(\"zones_statut\") or []\n"
        "             if z.get(\"zone\") and garde_zone(data, sc, z)]   # PATCH_S27_APPLIQUEE\n"
        "    if not zones:\n",
    ),
    # filtre
    (
        "def contradiction_article(fait):\n"
        "    return vraie_contradiction(fait) and not CONDITIONNEL.search(_plie(fait))",
        FILTRE,
    ),
    (
        "contradiction_article(x.get(\"fait\")):   # PATCH_S27_RELECTURE",
        "contradiction_article(x.get(\"fait\"), x.get(\"extrait\"), data, sc):   # PATCH_S27_RELECTURE / APPLIQUEE",
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
    if PREREQUIS not in texte:
        print("✗ Appliquer d'abord patch_s27_relecture_articles.py — rien fait.")
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
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s27_appliquee"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché ({len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_s27_appliquee")
    return 0


if __name__ == "__main__":
    sys.exit(main())
