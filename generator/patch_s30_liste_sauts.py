#!/usr/bin/env python3
"""patch_s30_liste_sauts.py — Ourrassol 2098, 1er novembre 2026

Défaut relevé au test réel de S30 (chute_holdfast_2072) : à l'étape ③, voir
l'effet des champs « Sauter » / « Inclure » demandait la simulation
d'injection (--dry-run, appels IA réels). Le bouton « Liste » (--plan) ne
tenait pas compte des champs.

Correctif :
  1. generator/et_si_injecter.py --plan : lit --sauter / --inclure, marque
     chaque ligne ✓ (appliquée) ou – (écartée, y compris les ⚠ écartés par
     défaut), signale les numéros absents de la liste, et affiche ce qui sera
     retiré de l'entrée (faits imposés, acteurs) si elle est dans la queue.
     Sans appel IA.
  2. gui/app.py, route /api/et_si/injecter/<action> : transmet aussi
     sauter / inclure à l'action « liste ».

Après le patch : redémarrer Flask entièrement.

Usage (depuis la racine du vault) :
    python3 generator/patch_s30_liste_sauts.py
Idempotent (marqueur PATCH_S30_LISTE_SAUTS) ; sauvegardes .bak_s30liste ;
contrôle de compilation, restauration des deux fichiers si échec.
"""
import py_compile
import re
import shutil
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
VAULT = GEN.parent
INJ = GEN / "et_si_injecter.py"
APP = VAULT / "gui" / "app.py"
MARQUEUR = "PATCH_S30_LISTE_SAUTS"

INJ_AVANT = '''    if a.plan:
        _, ops = _plan(hid)
        print(f"Liste de l'étape ④ — {hid} (mêmes numéros ; « Sauter » ici retire aussi faits et acteurs "
              "de l'injection)\\n")
        for o in ops:
            al = (f"  {'·' if str(o['alerte']).startswith('déjà') else '⚠'} {o['alerte']}"
                  if o.get("alerte") else "")
            print(f"  {o['n']:>3}. [{o['sc']}] {o['texte']}{al}")
        return
'''

INJ_APRES = '''    if a.plan:
        # PATCH_S30_LISTE_SAUTS : la liste tient compte de « Sauter » / « Inclure » (sans IA).
        _, ops = _plan(hid)
        sauter, inclure = _nombres(a.sauter), _nombres(a.inclure)
        ecartees = _ecartees(ops, sauter, inclure)
        print(f"Liste de l'étape ④ — {hid} (mêmes numéros ; « Sauter » ici retire aussi faits et acteurs "
              "de l'injection)")
        print(f"Sauter [{', '.join(map(str, sorted(sauter))) or '—'}] · Inclure "
              f"[{', '.join(map(str, sorted(inclure))) or '—'}] : ✓ appliquée, – écartée "
              "(les ⚠ sont écartés par défaut)\\n")
        for o in ops:
            al = (f"  {'·' if str(o['alerte']).startswith('déjà') else '⚠'} {o['alerte']}"
                  if o.get("alerte") else "")
            marque = "–" if o["n"] in ecartees else "✓"
            print(f"  {marque} {o['n']:>3}. [{o['sc']}] {o['texte']}{al}")
        inconnus = sorted((sauter | inclure) - {o["n"] for o in ops})
        if inconnus:
            print(f"\\n⚠ numéro(s) absent(s) de cette liste : {', '.join(map(str, inconnus))}")
        entrees = [x for x in ed._liste_yaml(ed.QUEUE_PATH, "queue")
                   if x.get("id") == hid and x.get("source") == f"et_si_{hid}"]
        if len(entrees) == 1:
            _, retires = _retirer_sautees(entrees[0], ops, ecartees)
            print("\\nRetiré de l'entrée à l'injection : "
                  + (f"{len(retires)} élément(s)" if retires else "rien"))
            for r_ in retires:
                print(f"  − {r_}")
        else:
            print("\\n· entrée absente de la queue (pas encore adoptée, ou déjà injectée) : "
                  "retraits non calculés")
        return
'''

APP_AVANT = '''    if action == "liste":
        cmd.append("--plan")
    else:
        if action == "apercu":
            cmd.append("--dry-run")
        for cle in ("sauter", "inclure"):
            valeur = re.sub(r"[^0-9,]", "", str(corps.get(cle) or "")).strip(",")
            if valeur:
                cmd += [f"--{cle}", valeur]
'''

APP_APRES = '''    if action == "liste":
        cmd.append("--plan")
    elif action == "apercu":
        cmd.append("--dry-run")
    for cle in ("sauter", "inclure"):   # PATCH_S30_LISTE_SAUTS : aussi pour « Liste »
        valeur = re.sub(r"[^0-9,]", "", str(corps.get(cle) or "")).strip(",")
        if valeur:
            cmd += [f"--{cle}", valeur]
'''


def main():
    for p in (INJ, APP):
        if not p.exists():
            sys.exit(f"✗ {p} introuvable — lancer depuis la racine du vault. Rien fait.")
    s_inj, s_app = INJ.read_text(encoding="utf-8"), APP.read_text(encoding="utf-8")
    if MARQUEUR in s_inj and MARQUEUR in s_app:
        print("· déjà appliqué — rien fait.")
        return
    a_faire = []
    for p, src, avant, apres in ((INJ, s_inj, INJ_AVANT, INJ_APRES), (APP, s_app, APP_AVANT, APP_APRES)):
        if MARQUEUR in src:
            continue
        n = src.count(avant)
        if n != 1:
            sys.exit(f"✗ {p.name} : bloc attendu trouvé {n} fois (attendu 1) — rien fait.")
        a_faire.append((p, src.replace(avant, apres, 1)))

    baks = []
    for p, nouveau in a_faire:
        bak = p.with_name(p.name + ".bak_s30liste")
        shutil.copy2(p, bak)
        baks.append((p, bak))
        p.write_text(nouveau, encoding="utf-8")
    try:
        for p, _ in a_faire:
            py_compile.compile(str(p), doraise=True)
    except py_compile.PyCompileError as e:
        for p, bak in baks:
            shutil.copy2(bak, p)
        sys.exit(f"✗ compilation échouée, fichiers restaurés : {e}")
    for p, bak in baks:
        print(f"✓ {p.relative_to(VAULT)} patché (sauvegarde {bak.name})")

    # Le bouton « Liste » envoie-t-il les champs ? (lecture seule, pour information)
    trouve = False
    for f in sorted((VAULT / "gui").rglob("*")):
        if f.suffix not in (".js", ".html") or not f.is_file():
            continue
        for i, ligne in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if "et_si/injecter" in ligne:
                trouve = True
                print(f"  [gui] {f.relative_to(VAULT)}:{i}: {ligne.strip()[:160]}")
    if not trouve:
        print("  [gui] appel de /api/et_si/injecter non trouvé dans gui/ (.js, .html)")
    print("→ Redémarrer Flask entièrement.")


if __name__ == "__main__":
    main()
