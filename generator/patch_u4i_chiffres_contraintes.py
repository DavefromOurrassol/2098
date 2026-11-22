#!/usr/bin/env python3
"""
patch_u4i_chiffres_contraintes.py — Ourrassol 2098 (22 novembre 2026)
=====================================================================

B9 « chiffres des contraintes tels quels ». Constat du 7 nov : à l'injection du
signal chatbots_guides_spirituels_2026, l'IA a écrit « captant 10-20 % des
demandes » dans `section7_annotation` et `contexte_injection`, alors que la
source disait « 1 adulte américain sur 10 (1 sur 5 chez les moins de 30 ans) ».

Cible : generator/inject_custom_signals.py
  1. CONSIGNE_CHIFFRES : un chiffre de l'annotation ou du contexte ne vient que
     de l'idée source ou des faits imposés, repris tel quel (toujours envoyée,
     avec ou sans contraintes).
  2. controle_chiffres() : contrôle MÉCANIQUE de ces deux champs. Un nombre
     absent de l'idée et des faits devient un problème de validation -> relance
     de correction (comme le nombre de mots), puis needs_review si l'IA insiste.
     Ignorés : les années (19xx-21xx), les nombres collés à un nom (G7, 5G,
     Kharg-9, COVID-19, slugs), les forces signées (+5, -1). Une fourchette
     « 10-20 » compte ses deux bornes.
  3. Consigne de correction ajoutée à la relance.

Usage (depuis la racine du vault) :
    python3 generator/patch_u4i_chiffres_contraintes.py           # dry-run
    python3 generator/patch_u4i_chiffres_contraintes.py --apply   # écrit (.bak_u4i)
"""

import argparse
import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/inject_custom_signals.py")
TAG = "u4i"

R1_ANCIEN = "MAX_DELTA_SIGNAL = 10\n"
R1_NOUVEAU = '''MAX_DELTA_SIGNAL = 10

# U4i (22 nov 2026) : chiffres de la source repris tels quels. Le 7 nov, « 1 adulte
# américain sur 10 (1 sur 5 chez les moins de 30 ans) » était devenu « 10-20 % des
# demandes » dans l'annotation et le contexte d'injection.
CONSIGNE_CHIFFRES = (
    "\\nCHIFFRES (règle stricte) : dans `section7_annotation` et `contexte_injection`, un chiffre "
    "ne peut venir que de l'idée source ou des faits imposés, repris TEL QUEL avec la population "
    "ou le champ auquel il s'applique (ex. « 1 adulte américain sur 10 (1 sur 5 chez les moins "
    "de 30 ans) »). Ne le convertis pas en pourcentage, ne l'arrondis pas, ne l'étends pas à une "
    "autre population, ne fusionne pas plusieurs chiffres en une fourchette. Si la source ne "
    "donne aucun chiffre, n'en écris aucun.\\n"
)
CHAMPS_CHIFFRES = ("section7_annotation", "contexte_injection")
_RE_NOMBRE = re.compile(r"\\d+(?:[.,]\\d+)?")


def _nombres(texte):
    """U4i : nombres d'un texte, hors années et hors nombres collés à un nom ou signés."""
    t = str(texte or "")
    res = []
    for m in _RE_NOMBRE.finditer(t):
        a, b = m.start(), m.end()
        avant = t[a - 1] if a > 0 else " "
        avant2 = t[a - 2] if a > 1 else " "
        apres = t[b] if b < len(t) else " "
        if avant.isalnum() or avant in "_.,+" or apres.isalpha() or apres == "_":
            continue   # G7, 5G, slug_2026, force +5
        if avant == "-" and not avant2.isdigit():
            continue   # Kharg-9, COVID-19, polarité -1 ; « 10-20 » garde ses deux bornes
        n = m.group(0).replace(",", ".")
        if len(n) == 4 and n[:2] in ("19", "20", "21"):
            continue   # une année : contrôlée par validate_signal_block()
        res.append(n)
    return res


def controle_chiffres(develop, sources):
    """U4i : chaque nombre de l'annotation et du contexte doit figurer dans l'idée
    source ou les faits imposés. Retourne une liste de problèmes (vide si tout va)."""
    autorises = {n for s in sources for n in _nombres(s)}
    issues = []
    for champ in CHAMPS_CHIFFRES:
        texte = re.sub(r"\\(→[^)]*\\)", " ", str((develop or {}).get(champ) or ""))
        absents = list(dict.fromkeys(n for n in _nombres(texte) if n not in autorises))
        if absents:
            issues.append(
                f"{champ} : chiffre(s) {', '.join(absents)} absent(s) de l'idée source et des "
                f"faits imposés -- reprendre le chiffre de la source tel quel, ou n'en écrire aucun"
            )
    return issues
'''

R2_ANCIEN = '''    bloc_contraintes = ("\\nFAITS À RESPECTER (imposés par l'auteur ; priment sur tes connaissances "
                        "générales ; le récit ne doit en contredire aucun) :\\n"
                        + "\\n".join(f"- {c}" for c in contraintes) + "\\n") if contraintes else ""
'''
R2_NOUVEAU = R2_ANCIEN + "    bloc_contraintes += CONSIGNE_CHIFFRES   # U4i\n"

R3_ANCIEN = '''                    fenetres_imposees=bool(imp and imp.get("date") is not None),
                )
                if not issues:
                    break
'''
R3_NOUVEAU = '''                    fenetres_imposees=bool(imp and imp.get("date") is not None),
                )
                issues = list(issues) + controle_chiffres(develop, [idea_text] + contraintes)   # U4i
                if not issues:
                    break
'''

R4_ANCIEN = '''  +1/-1, déduit de l'`evolution` de chaque scénario ; "delta_level" est un
  entier entre 1 et {MAX_DELTA_SIGNAL}.
"""
'''
R4_NOUVEAU = '''  +1/-1, déduit de l'`evolution` de chaque scénario ; "delta_level" est un
  entier entre 1 et {MAX_DELTA_SIGNAL}.
- Si un point concerne un « chiffre absent de l'idée source » (U4i), réécris
  le champ nommé (section7_annotation ou contexte_injection) : reprends le
  chiffre de l'idée ou des faits imposés TEL QUEL, avec sa population, ou
  retire tout chiffre de ce champ.
"""
'''

REMPLACEMENTS = [
    ("1. CONSIGNE_CHIFFRES et controle_chiffres()", R1_ANCIEN, R1_NOUVEAU),
    ("2. consigne envoyée avec les faits imposés", R2_ANCIEN, R2_NOUVEAU),
    ("3. contrôle branché sur la validation", R3_ANCIEN, R3_NOUVEAU),
    ("4. consigne de la relance de correction", R4_ANCIEN, R4_NOUVEAU),
]


def main():
    ap = argparse.ArgumentParser(description="Patch U4i : chiffres des contraintes tels quels.")
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon dry-run)")
    args = ap.parse_args()

    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault.")
    texte = CIBLE.read_text(encoding="utf-8")
    if "controle_chiffres(" in texte:
        sys.exit("✗ U4i déjà appliqué (controle_chiffres présent) : rien à faire.")

    nouveau = texte
    ok = True
    for nom, ancien, neuf in REMPLACEMENTS:
        n = nouveau.count(ancien)
        if n != 1:
            print(f"✗ {nom} : ancre trouvée {n} fois (attendu 1)")
            ok = False
            continue
        nouveau = nouveau.replace(ancien, neuf)
        print(f"✓ {nom}")
    if not ok:
        sys.exit("✗ Patch non appliqué (fichier différent de celui attendu).")

    try:
        compile(nouveau, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas : {e}")
    print("✓ Le fichier patché compile.")

    if not args.apply:
        print("\n(dry-run) Rien n'est écrit. Relancer avec --apply.")
        return
    bak = CIBLE.with_name(CIBLE.name + f".bak_{TAG}")
    shutil.copy(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"\n→ {CIBLE} patché (sauvegarde {bak.name}).")


if __name__ == "__main__":
    main()
