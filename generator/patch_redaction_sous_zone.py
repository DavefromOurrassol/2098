"""
patch_redaction_sous_zone.py -- S23, 3 octobre 2026 (décision de David).

get_journal_profile() (prompt_builder.py) cherchait toujours la rédaction
de la zone N1 de l'article. Une sous-zone ayant sa propre rédaction (cas
réel : Nuuk-Forteresse, fortress_world, N1 devenue sous-zone de l'Espace
Nordique en septembre) n'était donc jamais utilisée. Désormais : remontée
depuis la zone EXACTE de l'article, première rédaction trouvée (zone
elle-même, puis ses parents, jusqu'à la N1). Zones sans rédaction propre
(quasi toutes) : résultat identique à avant.

validate.py : l'avertissement « rédaction rattachée à une sous-zone —
jamais utilisée » (section 12) est retiré, devenu faux.

Usage (depuis generator/) :
  python3 patch_redaction_sous_zone.py           # aperçu
  python3 patch_redaction_sous_zone.py --apply   # .bak_sous_zone + compilation
"""
import argparse
import py_compile
import shutil
import sys

PB_OLD = "    zone_slug_n1 = _resoudre_zone_n1(zone_slug, scenario_slug) if zone_slug else zone_slug\n"
PB_NEW = '''    # S23 (3 octobre 2026) : rédaction la plus PROCHE de la zone de
    # l'article -- zone exacte, puis ses parents, puis la N1 (voir
    # _resoudre_zone_redaction). Le nom zone_slug_n1 est conservé pour ne
    # pas toucher au reste de la fonction (namespaces de rotation, logs) :
    # il vaut désormais la zone de la rédaction retenue, N1 dans la
    # quasi-totalité des cas.
    zone_slug_n1 = (_resoudre_zone_redaction(zone_slug, scenario_slug, ligne)
                    if zone_slug else zone_slug)
'''

PB_HELPER_ANCRE = "def get_journal_profile("
PB_HELPER = '''def _resoudre_zone_redaction(zone_slug, scenario_slug, ligne):
    """
    Zone dont la rédaction doit signer l'article (S23, 3 octobre 2026) :
    première zone de la chaîne zone_slug -> parent -> ... -> N1 qui a une
    entrée dans journaux.yaml[scenario][ligne]["zones"]. Aucune trouvée :
    repli sur _resoudre_zone_n1() (comportement d'avant ce correctif, qui
    laisse get_journal_profile() gérer l'absence comme avant).
    """
    global _JOURNAUX_CACHE
    if _JOURNAUX_CACHE is None:
        _JOURNAUX_CACHE = _load_journaux()
    redac = (_JOURNAUX_CACHE.get(scenario_slug, {}).get(ligne, {}).get("zones") or {})
    by_slug = {z["slug"]: z for z in _load_geographie(scenario_slug) if z.get("slug")}
    courant, vus = zone_slug, set()
    while courant and courant not in vus:
        if courant in redac:
            return courant
        vus.add(courant)
        courant = (by_slug.get(courant) or {}).get("parent")
    return _resoudre_zone_n1(zone_slug, scenario_slug)


def get_journal_profile('''

VA_DOC_OLD = ("      AVERTISSEMENT rédaction rattachée à une sous-zone (jamais\n"
              "                    lue : le pipeline cherche toujours la N1)\n")
VA_OLD = '''                if zone not in n1:
                    result.warning("journaux", lieu,
                        "rédaction rattachée à une sous-zone (niveau {}) — jamais "
                        "utilisée, le pipeline cherche la N1".format(
                            zones_geo[zone].get("niveau")))
'''
VA_NEW = ("                # Rédaction de sous-zone : utilisée en priorité sur celle de\n"
          "                # sa N1 depuis le 3 octobre 2026 (_resoudre_zone_redaction).\n")

FICHIERS = {
    "prompt_builder.py": [(PB_OLD, PB_NEW), (PB_HELPER_ANCRE, PB_HELPER)],
    "validate.py": [(VA_DOC_OLD, ""), (VA_OLD, VA_NEW)],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    textes = {}
    for nom, edits in FICHIERS.items():
        t = open(nom, encoding="utf-8").read()
        if "_resoudre_zone_redaction" in t:
            print("✗ {} : déjà patché".format(nom))
            sys.exit(1)
        for old, new in edits:
            n = t.count(old)
            if n == 0 and old == VA_DOC_OLD:
                print("· {} : ligne de docstring introuvable, ignorée (commentaire seulement)".format(nom))
                continue
            if n != 1:
                print("✗ {} : {} occurrence(s) pour « {} » : rien n'est écrit".format(
                    nom, n, old.strip()[:60]))
                sys.exit(1)
            t = t.replace(old, new)
            print("✓ {} : « {} »".format(nom, old.strip()[:60]))
        textes[nom] = t
    if not args.apply:
        print("\nAperçu OK, rien n'est écrit. Relance avec --apply.")
        return
    for nom, t in textes.items():
        shutil.copy2(nom, nom + ".bak_sous_zone")
        open(nom, "w", encoding="utf-8").write(t)
        try:
            py_compile.compile(nom, doraise=True)
            print("écrit + compilé : {}".format(nom))
        except py_compile.PyCompileError as e:
            shutil.copy2(nom + ".bak_sous_zone", nom)
            print("✗ compilation échouée, {} restauré : {}".format(nom, e))
            sys.exit(1)


if __name__ == "__main__":
    main()
