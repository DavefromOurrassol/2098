#!/usr/bin/env python3
"""
patch_s27_localisation_pays.py — 24 octobre 2026 (S27, point 4, suite).

Après patch_s27_localisation_territoires.py, Mistral-small plaçait encore les
Veilleurs d'Ormuz (Bandar Abbas, Iran) dans la Zone Golfe Persique–Levant, alors
que la liste montrait l'Iran dans l'Arc Eurasien Central. Contrôle mécanique :

  1. l'IA renvoie aussi `pays` : le pays réel du lieu (question facile) ;
  2. extraction « extrait » : la zone choisie, ou un de ses parents, doit porter
     ce pays dans ses territoires (origine_reelle, lue par mots comme la Carte) ;
  3. sinon : corrigée vers l'UNIQUE zone N1 qui porte ce pays (⚠ affiché, raison
     gardée dans la justification) ; aucune ou plusieurs : « ambigu » (review
     manuelle, zone candidate gardée).
  Pays absent, ou inconnu de toutes les zones : rien ne change.

Cible : generator/extract_localisation.py (après patch_s27_localisation_
territoires.py ; sauvegarde .bak_s27_pays). Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_localisation_pays.py
"""

import shutil
import sys
from pathlib import Path

MARQUEUR = "def controler_pays("
PREREQUIS = "PATCH_S27_TERRITOIRES"
CIBLE = Path(__file__).resolve().parent / "extract_localisation.py"

CONTROLE = '''# ─────────────────────────────────────────────────────────────
# CONTRÔLE DU PAYS (PATCH_S27_PAYS, 24 oct 2026)
# ─────────────────────────────────────────────────────────────

def _plie_pays(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def zone_porte_pays(z, pays):
    """La zone cite-t-elle `pays` dans origine_reelle, lue par mots (« Île de Kharg, Iran »,
    « Détroit d'Ormuz (Oman/Iran) ») ?"""
    cherche = _plie_pays(pays)
    for o in (z or {}).get("origine_reelle") or []:
        if not isinstance(o, dict):
            continue
        texte = _plie_pays(o.get("entite"))
        morceaux = [re.sub(r"\\([^)]*\\)", "", texte)] + re.findall(r"\\(([^)]*)\\)", texte)
        if any(t.strip() == cherche for m in morceaux for t in re.split(r"[,/]", m)):
            return True
    return False


def controler_pays(data, scenario):
    """Corrige `data` (issue extrait) si la zone choisie ne couvre pas le pays du lieu.
    Retourne une note (str) si quelque chose a changé, sinon None."""
    pays = (data.get("pays") or "").strip()
    zone = data.get("zone")
    if data.get("issue") != "extrait" or not pays or not zone:
        return None
    zones = load_zones(scenario)
    porteuses = [s for s, z in zones.items() if zone_porte_pays(z, pays)]
    if not porteuses:
        return None   # pays inconnu de la géographie : rien à vérifier
    s, vus = zone, set()
    while s and s in zones and s not in vus:
        if zone_porte_pays(zones[s], pays):
            return None   # la zone choisie, ou un parent, couvre le pays
        vus.add(s)
        s = zones[s].get("parent")
    n1 = [s for s in porteuses if int(zones[s].get("niveau") or 1) == 1]
    if len(n1) == 1:
        data["zone"] = n1[0]
        data["justification"] = (f"{data.get('justification', '')} [zone corrigée : {zone} → {n1[0]}, "
                                 f"seule zone N1 qui porte {pays}]").strip()
        return f"zone corrigée : {zone} ne porte pas {pays} → {n1[0]}"
    data["issue"] = "ambigu"
    data["justification"] = (f"{data.get('justification', '')} [{zone} ne porte pas {pays} ; zones N1 qui le "
                             f"portent : {', '.join(n1) or 'aucune'}]").strip()
    return f"zone {zone} ne porte pas {pays} → ambigu (review manuelle)"


# ─────────────────────────────────────────────────────────────
# ÉCRITURE DU CHAMP DANS LE FRONTMATTER
# ─────────────────────────────────────────────────────────────'''

REMPLACEMENTS = [
    (
        '  "type_lieu": "ville" | "region" | "infrastructure" | "site_strategique" | null,\n',
        '  "type_lieu": "ville" | "region" | "infrastructure" | "site_strategique" | null,\n'
        '  "pays": "<pays réel où se trouve le lieu, en français, ou null>",\n',
    ),
    (
        "# ─────────────────────────────────────────────────────────────\n"
        "# ÉCRITURE DU CHAMP DANS LE FRONTMATTER\n"
        "# ─────────────────────────────────────────────────────────────",
        CONTROLE,
    ),
    (
        "    issue = data[\"issue\"]\n    if verbose:\n",
        "    note_pays = controler_pays(data, scenario)   # PATCH_S27_PAYS\n"
        "    if note_pays:\n"
        "        print(f\"  ⚠ {note_pays}\")\n"
        "    issue = data[\"issue\"]\n    if verbose:\n",
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
        print("✗ Appliquer d'abord patch_s27_localisation_territoires.py — rien fait.")
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
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s27_pays"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché ({len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_s27_pays")
    return 0


if __name__ == "__main__":
    sys.exit(main())
