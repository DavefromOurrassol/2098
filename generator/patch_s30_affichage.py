#!/usr/bin/env python3
"""
patch_s30_affichage.py — Ourrassol 2098 (S30, 31 octobre 2026)
==============================================================

Défauts d'affichage relevés au test réel de S30 (sans effet sur les données) :
  1. simuler_et_si.py : titres d'articles à relire entourés de « » même quand le
     titre en a déjà (« « Murmures sous la glace » : … ») ;
  2. simuler_et_si.py : `acteurs_hint` décrit « (lecture IA, passe exhaustive) »
     même quand la passe n'a pas tourné ;
  3. appliquer_et_si.py : l'aperçu de l'étape ④ listait sao_paulo_spaar parmi les
     sous-zones « rattachées », alors qu'elle suit son parent sao_paulo_ita
     (seules 2 sont rattachées à l'écriture). Désormais : sous-zones rattachées,
     puis « (avec leurs sous-zones : …) ».

USAGE (depuis la racine du vault)
    python3 generator/patch_s30_affichage.py            # aperçu
    python3 generator/patch_s30_affichage.py --apply    # écrit (sauvegardes .bak_s30affichage)
"""

import argparse
import py_compile
import re
import shutil
import sys
import tempfile
from pathlib import Path

GEN = Path(__file__).resolve().parent
MARQUEUR = "PATCH_S30_AFFICHAGE"

TITRE_AVANT = '''motif="; ".join(f"« {a['titre']} »" for a in a_relire[:MAX_LISTE])'''
TITRE_APRES = ('''motif="; ".join(a['titre'] if str(a['titre']).lstrip().startswith("«")   # PATCH_S30_AFFICHAGE\n'''
               '''                              else f"« {a['titre']} »" for a in a_relire[:MAX_LISTE])''')

PASSE_RE = re.compile(r'(\(lecture IA, )(passe ")(\s*\n\s*")(exhaustive\))')

NOTE_AVANT = '''    if o.get("simples"):
        parts.append(f"puis sous-zone(s) rattachée(s) à `{o['cible']}` en gardant {o['pays']} : "
                     + ", ".join(o["simples"]))
'''
NOTE_APRES = '''    if o.get("simples"):   # PATCH_S30_AFFICHAGE : seules les sous-zones hautes sont rattachées
        parents = {z.get("slug"): z.get("parent") for z in zones_geo(o["sc"])}
        hautes = [s for s in o["simples"] if parents.get(s) not in o["simples"]]
        suivent = [s for s in o["simples"] if s not in hautes]
        parts.append(f"puis sous-zone(s) rattachée(s) à `{o['cible']}` en gardant {o['pays']} : "
                     + ", ".join(hautes or o["simples"])
                     + (f" (avec leurs sous-zones : {', '.join(suivent)})" if suivent and hautes else ""))
'''


def patcher_simuler(texte):
    if texte.count(TITRE_AVANT) != 1:
        return None, f"titre des articles trouvé {texte.count(TITRE_AVANT)} fois"
    texte = texte.replace(TITRE_AVANT, TITRE_APRES)
    trouves = PASSE_RE.findall(texte)
    if len(trouves) != 1:
        return None, f"libellé « lecture IA, passe exhaustive » trouvé {len(trouves)} fois"
    texte = PASSE_RE.sub(lambda m: m.group(1) + m.group(2) + m.group(3)
                         + "exhaustive si elle a tourné)", texte)
    return texte, None


def patcher_appliquer(texte):
    if texte.count(NOTE_AVANT) != 1:
        return None, f"note de carte trouvée {texte.count(NOTE_AVANT)} fois"
    return texte.replace(NOTE_AVANT, NOTE_APRES), None


def compile_ok(texte):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(texte)
    try:
        py_compile.compile(tmp.name, doraise=True)
        return None
    except py_compile.PyCompileError as e:
        return str(e)
    finally:
        Path(tmp.name).unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dossier", default=str(GEN))
    a = ap.parse_args()
    dossier = Path(a.dossier)

    plan = []
    for nom, fonction in (("simuler_et_si.py", patcher_simuler), ("appliquer_et_si.py", patcher_appliquer)):
        p = dossier / nom
        if not p.exists():
            sys.exit(f"✗ {p} introuvable")
        texte = p.read_text(encoding="utf-8")
        if MARQUEUR in texte:
            print(f"· {nom} : déjà appliqué")
            continue
        nouveau, err = fonction(texte)
        if err:
            sys.exit(f"✗ {nom} : {err} (1 attendu) : fichier différent de celui analysé, rien écrit.")
        err = compile_ok(nouveau)
        if err:
            sys.exit(f"✗ {nom} patché ne compile pas, rien écrit :\n{err}")
        plan.append((p, texte, nouveau))

    print("ÉCRITURE" if a.apply else "APERÇU (rien écrit)")
    for p, texte, nouveau in plan:
        print(f"  {p.name} : compilation OK ({len(texte.splitlines())} → {len(nouveau.splitlines())} lignes)")
    if not plan:
        print("  rien à faire")
        return
    if not a.apply:
        print("\nRelancer avec --apply pour écrire (sauvegardes .bak_s30affichage).")
        return
    for p, _, nouveau in plan:
        shutil.copy2(p, p.with_name(p.name + ".bak_s30affichage"))
        p.write_text(nouveau, encoding="utf-8")
        print(f"✓ {p.name} patché")


if __name__ == "__main__":
    main()
