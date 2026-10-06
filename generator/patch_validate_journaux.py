"""
patch_validate_journaux.py -- S23, 3 octobre 2026.

Ajoute à validate.py une 12e section, validate_journaux() : cohérence
journaux.yaml <-> geographie/{scenario}.md, pour les 6 scénarios et les
deux lignes éditoriales. Lecture seule, sans LLM. Motivée par trois
défauts trouvés le 3 octobre, invisibles jusqu'ici à validate.py :
  - clé de zone orpheline (renommage du 26 septembre non reporté) ;
  - 9 zones N1 créées en septembre sans aucune rédaction ;
  - rédactions factices ("Édition <zone>", 0 journaliste) laissées par
    un lot échoué de generate_journaux.py --update.

Usage (depuis generator/) :
  python3 patch_validate_journaux.py           # aperçu
  python3 patch_validate_journaux.py --apply   # .bak_journaux + compilation
"""
import argparse
import py_compile
import shutil
import sys

FONCTION = '''# ─────────────────────────────────────────
# 12. JOURNAUX ↔ GÉOGRAPHIES (3 octobre 2026, S23)
# ─────────────────────────────────────────

def validate_journaux(result):
    """
    Cohérence de generator/journaux.yaml avec geographie/{scenario}.md,
    pour chaque scénario et chaque ligne éditoriale. get_journal_profile()
    (prompt_builder.py) cherche la rédaction de la zone N1 de l'article ;
    sans rédaction exploitable, l'article signe d'un nom inventé au nom du
    réseau, sans que rien ne le signale.
      ERREUR        clé de zone absente de la géographie (orpheline -- ex.
                    renommage de zone non reporté dans journaux.yaml)
      ERREUR        rédaction factice : nom vide ou « Édition … » par défaut,
                    ou aucune journaliste ni orateur·rice (lot
                    generate_journaux.py --update échoué)
      AVERTISSEMENT rédaction rattachée à une sous-zone (jamais lue : le
                    pipeline cherche toujours la N1)
      AVERTISSEMENT zone N1 sans rédaction (--update la créerait)
    """
    path = os.path.join(GENERATOR_DIR, "journaux.yaml")
    if not os.path.exists(path):
        result.warning("journaux", "journaux.yaml", "fichier absent — contrôle ignoré")
        return
    try:
        with open(path, encoding="utf-8") as f:
            journaux = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        result.error("journaux", "journaux.yaml", "YAML invalide : {}".format(str(e)[:120]))
        return

    total = 0
    for sc in VALID_SCENARIOS:
        geo_path = os.path.join(GEOGRAPHIE_DIR, "{}.md".format(sc))
        fm, _, _ = parse_md(geo_path)
        zones_geo = {z["slug"]: z for z in ((fm or {}).get("zones") or [])
                     if isinstance(z, dict) and z.get("slug")}
        if not zones_geo:
            continue
        n1 = {s for s, z in zones_geo.items() if z.get("niveau", 1) == 1}
        for ligne in ("pro_pouvoir", "opposition"):
            redac = ((journaux.get(sc) or {}).get(ligne) or {}).get("zones") or {}
            for zone, zd in redac.items():
                total += 1
                lieu = "journaux.yaml {}/{}/{}".format(sc, ligne, zone)
                if zone not in zones_geo:
                    result.error("journaux", lieu,
                        "zone absente de geographie/{}.md (clé orpheline : "
                        "renommage non reporté ?)".format(sc))
                    continue
                if zone not in n1:
                    result.warning("journaux", lieu,
                        "rédaction rattachée à une sous-zone (niveau {}) — jamais "
                        "utilisée, le pipeline cherche la N1".format(
                            zones_geo[zone].get("niveau")))
                zd = zd or {}
                nom = str(zd.get("nom") or "")
                if not nom or nom.startswith("Édition "):
                    result.error("journaux", lieu,
                        "rédaction factice (nom « {} ») — lot generate_journaux.py "
                        "échoué ? la retirer puis --update".format(nom))
                if not (zd.get("journalistes") or zd.get("orateurs")):
                    result.error("journaux", lieu,
                        "aucune journaliste ni orateur·rice — signature inventée "
                        "à chaque article")
            for zone in sorted(n1 - set(redac)):
                result.warning("journaux", "journaux.yaml {}/{}/{}".format(sc, ligne, zone),
                    "zone N1 « {} » sans rédaction — generate_journaux.py --scenario "
                    "{} --update".format(zones_geo[zone].get("nom", zone), sc))
    result.info("journaux", "{} rédactions locales contrôlées".format(total))


def run('''

APPEL = '''    print("[validate] 12/12 — Journaux ↔ géographies...")
    validate_journaux(result)

    print_results(result, verbose=verbose)

    if report:
        generate_report(result)

    # Mise à jour du timestamp'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    p = "validate.py"
    t = open(p, encoding="utf-8").read()
    if "def validate_journaux" in t:
        print("✗ validate.py : déjà patché")
        sys.exit(1)

    etapes = [
        ("def run(", FONCTION, 1),
        ("    print_results(result, verbose=verbose)\n\n    if report:\n"
         "        generate_report(result)\n\n    # Mise à jour du timestamp", APPEL, 1),
        ("/11 — ", "/12 — ", 11),
    ]
    for old, new, attendu in etapes:
        n = t.count(old)
        if n != attendu:
            print("✗ {} occurrence(s) (attendu {}) pour « {} » : rien n'est écrit".format(
                n, attendu, old.strip()[:50]))
            sys.exit(1)
        t = t.replace(old, new)
        print("✓ « {} » ({}×)".format(old.strip()[:50], attendu))

    if not args.apply:
        print("\nAperçu OK, rien n'est écrit. Relance avec --apply.")
        return
    shutil.copy2(p, p + ".bak_journaux")
    open(p, "w", encoding="utf-8").write(t)
    try:
        py_compile.compile(p, doraise=True)
        print("écrit + compilé : validate.py")
    except py_compile.PyCompileError as e:
        shutil.copy2(p + ".bak_journaux", p)
        print("✗ compilation échouée, validate.py restauré : {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
