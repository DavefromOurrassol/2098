#!/usr/bin/env python3
"""
patch_u3ad_dates_2098.py — Ourrassol 2098 (14 novembre 2026)
Dates 2098.xx (événement avec mois) dans la Passe exhaustive et la Lecture IA.

  1. et_si_exhaustif.py, ligne de commande seule : la date de mesure (2098.0 par défaut) n'était
     pas ramenée à la fin de l'année de l'apparition (2098.12) comme le fait simuler_et_si.py
     (U3g). Pour une hypothèse 2098.03, les effets étaient mesurés avant l'apparition (nuls),
     donc lus comme « choc amorti » : des obligatoires de type tendance rétrogradés à tort.
     (Passe lancée par simuler_et_si.py --passe-exhaustive : déjà correcte, la date y est ramenée.)
  2. et_si_exhaustif.charger_fiches : un événement daté « 2098 » (année entière, mois inconnu)
     est relu quand l'hypothèse est de la même année (il était écarté comme antérieur).
  3. Prompts de la passe, de la contre-lecture, du classement et de la Lecture IA : la date est
     écrite « mars 2098 (2098.03) » au lieu de « 2098.03 » (et « 2098.1 » pour octobre).
     Une date entière s'écrit comme avant : les caches existants restent valables.

Usage (racine du vault) :
    python3 generator/patch_u3ad_dates_2098.py            # dry-run
    python3 generator/patch_u3ad_dates_2098.py --apply    # écrit (.bak_u3ad pour chaque fichier)
"""
import argparse, py_compile, shutil, sys, tempfile
from pathlib import Path

EX = Path("generator/et_si_exhaustif.py")
SIM = Path("generator/simuler_et_si.py")

HELPER_EX = '''# U3ad (14 novembre 2026) : date lisible d'une date fractionnaire (2098.03 -> « mars 2098 (2098.03) »).
_MOIS_U3AD = (None, "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
              "septembre", "octobre", "novembre", "décembre")


def date_lisible_u3ad(v):
    """Date entière : écriture inchangée (« 2044 ») ; avec mois : « mars 2098 (2098.03) »."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    an = int(f)
    mois = round((f - an) * 100)
    if not 1 <= mois <= 12:
        return f"{f:g}"
    return f"{_MOIS_U3AD[mois]} {an} ({f:.2f})"


'''

HELPER_SIM = '''def _date_lisible_u3ad(v):   # U3ad : voir et_si_exhaustif.date_lisible_u3ad
    from et_si_exhaustif import date_lisible_u3ad
    return date_lisible_u3ad(v)


'''

def une_fois(texte, ancre, nouveau, nb=1):
    n = texte.count(ancre)
    if n != nb:
        raise ValueError(f"ancre trouvée {n} fois (attendu {nb}) : {ancre[:70]!r}")
    return texte.replace(ancre, nouveau)

def editer_ex(src):
    m = []
    src = une_fois(src, "def annees_hypothese(hyp):\n", HELPER_EX + "def annees_hypothese(hyp):\n")
    m.append("et_si_exhaustif : fonction date_lisible_u3ad")
    src = une_fois(src, "apparition en {hyp['date']:g}.\n", "apparition en {date_lisible_u3ad(hyp['date'])}.\n")
    src = une_fois(src, "{hyp['nom']} — {hyp['date']:g}.\\n\"", "{hyp['nom']} — {date_lisible_u3ad(hyp['date'])}.\\n\"", nb=2)
    m.append("et_si_exhaustif : date lisible dans les 3 prompts (passe, contre-lecture, classement)")
    ancre = ('                  if _annee(e.get("date")) is not None and _annee(e.get("date")) >= hyp["date"]\n')
    nouveau = ('                  if _annee(e.get("date")) is not None   # U3ad : « 2098 » entier relu si l\'hypothèse est de 2098.xx\n'
               '                  and (_annee(e.get("date")) >= hyp["date"]\n'
               '                       or (_annee(e.get("date")) == int(_annee(e.get("date")))\n'
               '                           and int(_annee(e.get("date"))) == int(hyp["date"])))\n')
    src = une_fois(src, ancre, nouveau)
    m.append("et_si_exhaustif : événements datés « année entière » relus")
    ancre = ('    scenarios = [args.scenario] if args.scenario else hyp["scenarios"]\n'
             '    resultats = s.simuler_hypothese(hyp, args.date, scenarios)\n')
    nouveau = ('    scenarios = [args.scenario] if args.scenario else hyp["scenarios"]\n'
               '    if args.date < hyp["date"] and int(args.date) == int(hyp["date"]):   # U3ad (comme U3g)\n'
               '        args.date = round(int(hyp["date"]) + 0.12, 2)\n'
               '        print(f"ℹ date de mesure ramenée à la fin de l\'année de l\'apparition : {args.date:g}", file=sys.stderr)\n'
               '    if args.date < hyp["date"]:\n'
               '        sys.exit(f"✗ --date {args.date:g} antérieure à l\'apparition de l\'hypothèse ({hyp[\'date\']:g}).")\n'
               '    resultats = s.simuler_hypothese(hyp, args.date, scenarios)\n')
    src = une_fois(src, ancre, nouveau)
    m.append("et_si_exhaustif : date de mesure ramenée (ligne de commande)")
    return src, m

def editer_sim(src):
    src = une_fois(src, "def simuler_hypothese(hyp, date_fin, scenarios=None):\n",
                   HELPER_SIM + "def simuler_hypothese(hyp, date_fin, scenarios=None):\n")
    src = une_fois(src, "{hyp['nom']} — apparition en {hyp['date']:g}, {nature}.",
                   "{hyp['nom']} — apparition en {_date_lisible_u3ad(hyp['date'])}, {nature}.")
    return src, ["simuler_et_si : date lisible dans le prompt de la Lecture IA"]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    cibles = []
    for chemin, fonction in ((EX, editer_ex), (SIM, editer_sim)):
        if not chemin.exists():
            sys.exit(f"{chemin} introuvable : lancer depuis la racine du vault.")
        src = chemin.read_text(encoding="utf-8")
        if "U3ad" in src:
            sys.exit(f"U3ad déjà appliqué dans {chemin.name} : rien à faire.")
        try:
            neuf, msgs = fonction(src)
        except ValueError as e:
            sys.exit(f"Abandon, rien écrit ({chemin.name}) : {e}")
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / chemin.name; t.write_text(neuf, encoding="utf-8")
            try: py_compile.compile(str(t), doraise=True)
            except py_compile.PyCompileError as e: sys.exit(f"Abandon, {chemin.name} ne compile pas : {e}")
        cibles.append((chemin, neuf, msgs))
    for chemin, _, msgs in cibles:
        for m in msgs: print(" ·", m)
    if not a.apply:
        print("\nDry-run : les deux fichiers compilent, rien n'est écrit. Relancer avec --apply."); return
    for chemin, neuf, _ in cibles:
        sauv = chemin.with_name(chemin.name + ".bak_u3ad")
        shutil.copy2(chemin, sauv); chemin.write_text(neuf, encoding="utf-8")
        py_compile.compile(str(chemin), doraise=True)
        print(f"Écrit : {chemin} (sauvegarde : {sauv.name}). py_compile OK.")

if __name__ == "__main__":
    main()
