#!/usr/bin/env python3
"""
patch_s27_dates_contestees.py — 23 octobre 2026 (S27.3, banc de rejeu).

Passe exhaustive v9.6 (et_si_exhaustif.py), contrôle mécanique, aucun appel IA,
rejouable au banc : un « texte » obligatoire dont la justification conteste
SEULEMENT une date de la fiche (« trop tardive », « bien avant 2051 », « dès 2043,
et non 2044 ») que l'élément ne fixe pas descend en « possible », motif
« date de la fiche contestée ». Pas appliqué si la justification invoque un fait
matériel (destruction, « n'existe plus »…).

Cas d'origine : peste_pulmonaire_2043 / breakdown (NexCore 2051, RPDA 2091,
Exode du Midwest 2044), confirmés à tort par la contre-lecture.

VERSION_PROMPT / VERSION_CONTRE / VERSION_CLASSEMENT inchangés : le cache des
lots reste valable. Sauvegarde .bak_s27_dates. Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_dates_contestees.py
"""

import shutil
import sys
from pathlib import Path

MARQUEUR = "_DATE_CONTESTEE"
CIBLE = Path(__file__).resolve().parent / "et_si_exhaustif.py"

BLOC_REGLE = '''TAILLE_LOT = 15
# v9.6 (23 oct, aucun appel, rejouable au banc) : un « texte » obligatoire qui conteste seulement une
# date de la fiche (« trop tardive », « dès 2043, et non 2044 ») que l'élément ne fixe pas descend en
# possible. Pas si la justification invoque un fait matériel (destruction, « n'existe plus »).
_ANNEE = _re.compile(r"\\b(1[89]\\d\\d|2[01]\\d\\d)\\b")
_DATE_CONTESTEE = _re.compile(r"(trop tard\\w*|bien avant|plus tot|date\\w* (?:est |sont )?"
                              r"(?:fausse|incorrecte|erronee|impossible)|la date (?:de |du )?(?:1[89]|2[01])\\d\\d)")
_MATERIEL = _re.compile(r"\\b(detrui\\w*|destruction|n'existe plus|aneanti\\w*|rase\\w*)\\b")


def annees_hypothese(hyp):
    """Années que l'élément fixe lui-même (nom, description, contraintes, date)."""
    texte = " ".join([str(hyp.get("nom") or ""), str(hyp.get("description") or "")]
                     + [str(c) for c in hyp.get("contraintes") or []])
    annees = {int(a) for a in _ANNEE.findall(texte)}
    if _annee(hyp.get("date")) is not None:
        annees.add(int(_annee(hyp.get("date"))))
    return annees


def _date_contestee(extrait, juge, annees_hyp):
    """`juge` déjà plié. Vrai si la justification conteste une année de l'extrait
    que l'élément ne fixe pas, sans invoquer de fait matériel."""
    propres = {int(a) for a in _ANNEE.findall(extrait)} - set(annees_hyp)
    if not propres or _MATERIEL.search(juge):
        return False
    for y in propres:
        if str(y) not in juge:
            continue
        if _DATE_CONTESTEE.search(juge) or _re.search(rf"\\b(?:des|et non|non pas)\\s+(?:en\\s+)?{y}\\b", juge):
            return True
    return False
'''

REMPLACEMENTS = [
    ("TAILLE_LOT = 15\n", BLOC_REGLE),
    (
        "def verifier_lot(brut, lot, by_inst, by_zone, effets=None, territoires=None, variables_hyp=None, lieux=None):",
        "def verifier_lot(brut, lot, by_inst, by_zone, effets=None, territoires=None, variables_hyp=None, lieux=None,\n"
        "                 annees_hyp=None):",
    ),
    (
        "                if not trouve:\n"
        "                    motifs.append(\"extrait introuvable dans la fiche\")\n",
        "                if not trouve:\n"
        "                    motifs.append(\"extrait introuvable dans la fiche\")\n"
        "                if niveau == \"obligatoire\" and _date_contestee(extrait, juge, annees_hyp or ()):\n"
        "                    motifs.append(\"date de la fiche contestée\")   # v9.6\n",
    ),
    (
        "    lieux = lieux_nommes(hyp)\n",
        "    lieux = lieux_nommes(hyp)\n"
        "    annees_hyp = annees_hypothese(hyp)   # v9.6\n",
    ),
    (
        "        return verifier_lot(brut, lot, by_inst, by_zone, effets, territoires, variables_hyp, lieux)",
        "        return verifier_lot(brut, lot, by_inst, by_zone, effets, territoires, variables_hyp, lieux, annees_hyp)",
    ),
    (
        "\"lien territoire alors\", \"sans lien direct\", \"extrait introuvable\")",
        "\"lien territoire alors\", \"sans lien direct\", \"extrait introuvable\",\n"
        "                \"date de la fiche contestée\")",
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
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s27_dates"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché (v9.6, {len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_s27_dates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
