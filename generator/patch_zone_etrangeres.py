"""
patch_zone_etrangeres.py -- S23, 3 octobre 2026 (suite de patch_zone_instances.py).

Quand une zone d'article est fixée : au plus MAX_ETRANGERES_ZONE (2)
instances localisées dans une AUTRE zone N1 que celle du journal. Les
instances transnationales (sans localisation.zone) restent libres ; les
places locales réservées (ZONE_PLACES_RESERVEES) sont inchangées. Les
places non remplies restent vides (moins d'entités, moins de bruit).
Sans zone fournie : comportement inchangé.

Usage (depuis generator/) :
  python3 patch_zone_etrangeres.py           # aperçu
  python3 patch_zone_etrangeres.py --apply   # .bak_zone_etrangeres + compilation
"""
import argparse
import py_compile
import re
import shutil
import sys


def flex(old):
    parts = re.split(r"\s+", old.strip())
    return r"\s+".join(re.escape(p) for p in parts)


ANCIEN_BLOC = '''
    if zones_article:
        locaux = [(s, i) for s, i in scored
                  if (i.get("localisation") or {}).get("zone") in zones_article]
        if locaux:
            n_res = min(ZONE_PLACES_RESERVEES, len(locaux))
            sel_locaux = _select_with_custom_guarantee(locaux, scenario_slug, dry_run, n_res)
            pris = {i.get("slug") for i in sel_locaux}
            reste = [(s, i) for s, i in scored if i.get("slug") not in pris]
            sel_reste = _select_with_custom_guarantee(
                reste, scenario_slug, dry_run, MAX_INSTANCES - len(sel_locaux))
            print("[loader] Zone du journal : {} instance(s) locale(s) retenue(s) sur {} "
                  "candidate(s) : {}".format(len(sel_locaux), len(locaux),
                  ", ".join(i.get("slug", "?") for i in sel_locaux)))
            return sel_locaux + sel_reste
        print("[loader] Zone du journal : aucune instance localisée dans {} zone(s) "
              "-- sélection habituelle".format(len(zones_article)))
    return _select_with_custom_guarantee(scored, scenario_slug, dry_run, MAX_INSTANCES)
'''

NOUVEAU_BLOC = '''if zones_article:
        def _zone(i):
            return (i.get("localisation") or {}).get("zone")

        def _etrangere(i):
            return bool(_zone(i)) and _zone(i) not in zones_article

        locaux = [(s, i) for s, i in scored if _zone(i) in zones_article]
        sel_locaux = []
        if locaux:
            sel_locaux = _select_with_custom_guarantee(
                locaux, scenario_slug, dry_run, min(ZONE_PLACES_RESERVEES, len(locaux)))
        pris = {i.get("slug") for i in sel_locaux}
        reste = [(s, i) for s, i in scored if i.get("slug") not in pris]
        etrangeres = [(s, i) for s, i in reste if _etrangere(i)]
        autres = [(s, i) for s, i in reste if not _etrangere(i)]

        places = MAX_INSTANCES - len(sel_locaux)
        sel_etr = []
        if places > 0 and etrangeres:
            sel_etr = _select_with_custom_guarantee(
                etrangeres, scenario_slug, dry_run, min(MAX_ETRANGERES_ZONE, places))
        places -= len(sel_etr)
        sel_autres = []
        if places > 0 and autres:
            sel_autres = _select_with_custom_guarantee(autres, scenario_slug, dry_run, places)

        print("[loader] Zone du journal : {} locale(s) sur {} candidate(s), {} d'autres "
              "zones (plafond {}), {} transnationale(s)/locale(s) en plus".format(
                  len(sel_locaux), len(locaux), len(sel_etr), MAX_ETRANGERES_ZONE,
                  len(sel_autres)))
        return sel_locaux + sel_etr + sel_autres
    return _select_with_custom_guarantee(scored, scenario_slug, dry_run, MAX_INSTANCES)'''

EDITS = [
    ("ZONE_PLACES_RESERVEES = 3",
     "ZONE_PLACES_RESERVEES = 3\n"
     "# Plafond d'instances localisées dans une AUTRE zone N1 quand la zone\n"
     "# de l'article est fixée (S23, 3 octobre 2026, décision de David).\n"
     "MAX_ETRANGERES_ZONE = 2"),
    (ANCIEN_BLOC, NOUVEAU_BLOC),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    nom = "loader.py"
    texte = open(nom, encoding="utf-8").read()
    if "MAX_ETRANGERES_ZONE" in texte:
        print("✗ loader.py : déjà patché, rien à faire")
        sys.exit(1)
    if "ZONE_PLACES_RESERVEES" not in texte:
        print("✗ loader.py : patch_zone_instances.py n'est pas appliqué -- à faire d'abord")
        sys.exit(1)

    for old, new in EDITS:
        motif = re.compile(flex(old))
        n = len(motif.findall(texte))
        etiquette = old.strip().split("\n")[0][:60]
        if n != 1:
            print("✗ {} occurrence(s) pour « {} » : rien n'est écrit".format(n, etiquette))
            sys.exit(1)
        texte = motif.sub(lambda m, r=new.lstrip(): r, texte, count=1)
        print("✓ « {} »".format(etiquette))

    if not args.apply:
        print("\nAperçu OK, rien n'est écrit. Relance avec --apply.")
        return
    shutil.copy2(nom, nom + ".bak_zone_etrangeres")
    open(nom, "w", encoding="utf-8").write(texte)
    try:
        py_compile.compile(nom, doraise=True)
        print("écrit + compilé : loader.py")
    except py_compile.PyCompileError as e:
        shutil.copy2(nom + ".bak_zone_etrangeres", nom)
        print("✗ compilation échouée, loader.py restauré : {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
