#!/usr/bin/env python3
"""
patch_guillemets_titres.py — Ourrassol 2098 (chantier 5, 5 octobre 2026)

Corrige le guillemet orphelin dans les titres du site (export_revues.py,
nettoyer_corps()). Avant : .strip("«»\"“” ") retirait tout guillemet en
tête ou en fin de titre, même quand il n'encadrait qu'une partie du titre
(« Qui contrôle le récit » : …  ->  Qui contrôle le récit » : …).
Après : les guillemets ne sont retirés que s'ils encadrent le titre ENTIER
(même paire en tête et en fin, aucun autre guillemet de ce type à l'intérieur).

Usage (depuis la racine du vault) :
    python3 generator/patch_guillemets_titres.py           # aperçu + tests, n'écrit rien
    python3 generator/patch_guillemets_titres.py --apply   # écrit (.bak_guillemets)
"""
import argparse
import shutil
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "export_revues.py"
MARQUEUR = "def retirer_guillemets_englobants("

ANCIEN = '            titre = m.group(2).strip().strip("«»\\"“” ").strip()\n'
NOUVEAU = '            titre = retirer_guillemets_englobants(m.group(2))\n'

FONCTION = '''def retirer_guillemets_englobants(titre):
    """Retire les guillemets seulement s'ils encadrent le titre ENTIER (chantier 5,
    5 octobre 2026). « Titre » -> Titre ; mais « Citation » : suite reste intact
    (avant : le « de tête était retiré seul, laissant un » orphelin)."""
    t = titre.strip()
    for ouvre, ferme in (("«", "»"), ("“", "”"), ('"', '"')):
        if len(t) > 2 and t.startswith(ouvre) and t.endswith(ferme):
            interieur = t[len(ouvre):-len(ferme)]
            if ouvre not in interieur and ferme not in interieur:
                return interieur.strip()
    return t


'''

ANCRE_FONCTION = "def nettoyer_corps(corps, titre_fm=\"\"):\n"

CAS = [
    ("« Qui contrôle le récit » : les Veilleurs refusent", "« Qui contrôle le récit » : les Veilleurs refusent"),
    ("Les mots interdits : « isruter »", "Les mots interdits : « isruter »"),
    ("« Le Titre entier »", "Le Titre entier"),
    ('"Titre entre guillemets droits"', "Titre entre guillemets droits"),
    ("“Titre anglais”", "Titre anglais"),
    ("« A » et « B »", "« A » et « B »"),
    ("Titre sans guillemet", "Titre sans guillemet"),
]


def patcher(src):
    if MARQUEUR in src:
        raise SystemExit("Patch déjà appliqué -- rien à faire.")
    for nom, ancre in (("titre", ANCIEN), ("nettoyer_corps", ANCRE_FONCTION)):
        if src.count(ancre) != 1:
            raise SystemExit(f"Ancre « {nom} » introuvable ou multiple -- patch non appliqué.")
    src = src.replace(ANCIEN, NOUVEAU, 1).replace(ANCRE_FONCTION, FONCTION + ANCRE_FONCTION, 1)
    compile(src, str(CIBLE), "exec")
    return src


def tester(src):
    ns = {}
    exec(compile(FONCTION, "fonction", "exec"), ns)
    f = ns["retirer_guillemets_englobants"]
    ok = True
    for entree, attendu in CAS:
        res = f(entree)
        bon = res == attendu
        ok &= bon
        print(f"  {'✓' if bon else '✗'} {entree!r:58} -> {res!r}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--cible", default=str(CIBLE), help=argparse.SUPPRESS)
    args = ap.parse_args()
    cible = Path(args.cible)
    nouveau = patcher(cible.read_text(encoding="utf-8"))
    print("Tests de la nouvelle règle :")
    if not tester(nouveau):
        raise SystemExit("Un test échoue -- patch non appliqué.")
    if not args.apply:
        print(f"\nAperçu OK : {cible.name} serait patché. Relancer avec --apply.")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_guillemets"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"\nPatch appliqué à {cible} (sauvegarde : {cible.name}.bak_guillemets).")


if __name__ == "__main__":
    main()
