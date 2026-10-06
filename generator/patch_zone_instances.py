"""
patch_zone_instances.py -- S23, 3 octobre 2026.

Corrige le "lieu de l'article != zone de son journal" : quand la zone de
l'article est connue (série, manuel, generate.py avec zone), jusqu'à
ZONE_PLACES_RESERVEES des 6 places de filtered_instances sont réservées
à des instances localisées dans la zone N1 du journal ou ses sous-zones.
Sans zone fournie : comportement STRICTEMENT inchangé.

Fichiers modifiés (generator/) :
  loader.py          zones_du_journal() + zones_article dans
                     filter_instances_for_thematique()
  snapshot.py        build_snapshot(..., zone_article=None)
  generate_series.py / generate.py / generate_manual.py : transmettent
                     leur zone à build_snapshot()

Usage (depuis generator/) :
  python3 patch_zone_instances.py           # aperçu : vérifie que chaque
                                            # remplacement trouve sa cible
  python3 patch_zone_instances.py --apply   # écrit (.bak_zone_instances),
                                            # compile chaque fichier, restaure
                                            # le .bak si la compilation échoue
"""
import argparse
import py_compile
import re
import shutil
import sys


def flex(old):
    """Motif regex où tout blanc de `old` accepte n'importe quel blanc."""
    parts = re.split(r"\s+", old.strip())
    return r"\s+".join(re.escape(p) for p in parts)


# ─── loader.py ──────────────────────────────────────────────────────────

LOADER_HELPER = '''# ─────────────────────────────────────────
# ZONE DU JOURNAL (S23, 3 octobre 2026)
# ─────────────────────────────────────────
#
# Lieu de l'article != zone de son journal : filtered_instances était
# choisi par thématique à l'échelle du monde entier, sans aucun lien avec
# la zone du journal (cas réel : article du journal Maghreb Méditerranéen
# entièrement consacré au Terminal Kharg, golfe Persique). Quand la zone
# de l'article est connue, une partie des places est désormais réservée
# aux instances localisées dans la zone du JOURNAL -- zone N1 (une seule
# rédaction par N1 dans journaux.yaml) et toutes ses sous-zones.

ZONE_PLACES_RESERVEES = 3
_GEOGRAPHIE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "geographie")
_GEO_CACHE = {}


def _zones_geographie(scenario_slug):
    """Zones (frontmatter de geographie/{scenario}.md), en cache. [] si absent."""
    if scenario_slug in _GEO_CACHE:
        return _GEO_CACHE[scenario_slug]
    zones = []
    path = os.path.join(_GEOGRAPHIE_DIR, "{}.md".format(scenario_slug))
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            m = re.match(r"^---\\s*\\n(.*?)\\n---\\s*\\n", f.read(), re.DOTALL)
        if m:
            try:
                zones = (yaml.safe_load(m.group(1)) or {}).get("zones", []) or []
            except yaml.YAMLError:
                zones = []
    _GEO_CACHE[scenario_slug] = zones
    return zones


def zones_du_journal(scenario_slug, zone_slug):
    """
    Ensemble des zones couvertes par le journal d'une zone : remontée
    jusqu'à l'ancêtre niveau 1 (comme prompt_builder._resoudre_zone_n1,
    garde-fou anti-cycle), puis cet ancêtre et toutes ses sous-zones.
    Zone inconnue ou géographie absente : {zone_slug} seul.
    """
    if not zone_slug:
        return set()
    zones = _zones_geographie(scenario_slug)
    by_slug = {z["slug"]: z for z in zones if z.get("slug")}
    courant = by_slug.get(zone_slug)
    if courant is None:
        return {zone_slug}
    vus = set()
    while courant is not None and courant.get("niveau", 1) != 1:
        if courant["slug"] in vus:
            break
        vus.add(courant["slug"])
        courant = by_slug.get(courant.get("parent"))
    racine = courant["slug"] if courant else zone_slug
    enfants = {}
    for z in zones:
        if z.get("slug") and z.get("parent"):
            enfants.setdefault(z["parent"], []).append(z["slug"])
    resultat, pile = set(), [racine]
    while pile:
        s = pile.pop()
        if s in resultat:
            continue
        resultat.add(s)
        pile.extend(enfants.get(s, []))
    return resultat


def filter_instances_for_thematique(instances, thematique, scenario_slug=None, dry_run=True, zones_article=None):'''

LOADER_EDITS = [
    (
        "def filter_instances_for_thematique(instances, thematique, scenario_slug=None, dry_run=True):",
        LOADER_HELPER,
    ),
    (
        "        if score > 0 or is_custom or is_priorite_forcee:\n"
        "            scored.append((score, inst))",
        "        # S23 (3 octobre 2026) : une instance localisée dans la zone du\n"
        "        # journal reste candidate même à score thématique nul -- c'est\n"
        "        # la couleur locale qui manquait aux articles.\n"
        "        est_local = bool(zones_article) and (\n"
        "            (inst.get(\"localisation\") or {}).get(\"zone\") in zones_article)\n"
        "        if score > 0 or is_custom or is_priorite_forcee or est_local:\n"
        "            scored.append((score, inst))",
    ),
    (
        "    return _select_with_custom_guarantee(scored, scenario_slug, dry_run, MAX_INSTANCES)",
        "    # S23 (3 octobre 2026) : places réservées aux instances de la zone\n"
        "    # du journal, puis places restantes disputées comme avant. Sans\n"
        "    # zones_article (ou sans instance locale) : inchangé.\n"
        "    if zones_article:\n"
        "        locaux = [(s, i) for s, i in scored\n"
        "                  if (i.get(\"localisation\") or {}).get(\"zone\") in zones_article]\n"
        "        if locaux:\n"
        "            n_res = min(ZONE_PLACES_RESERVEES, len(locaux))\n"
        "            sel_locaux = _select_with_custom_guarantee(locaux, scenario_slug, dry_run, n_res)\n"
        "            pris = {i.get(\"slug\") for i in sel_locaux}\n"
        "            reste = [(s, i) for s, i in scored if i.get(\"slug\") not in pris]\n"
        "            sel_reste = _select_with_custom_guarantee(\n"
        "                reste, scenario_slug, dry_run, MAX_INSTANCES - len(sel_locaux))\n"
        "            print(\"[loader] Zone du journal : {} instance(s) locale(s) retenue(s) sur {} \"\n"
        "                  \"candidate(s) : {}\".format(len(sel_locaux), len(locaux),\n"
        "                  \", \".join(i.get(\"slug\", \"?\") for i in sel_locaux)))\n"
        "            return sel_locaux + sel_reste\n"
        "        print(\"[loader] Zone du journal : aucune instance localisée dans {} zone(s) \"\n"
        "              \"-- sélection habituelle\".format(len(zones_article)))\n"
        "    return _select_with_custom_guarantee(scored, scenario_slug, dry_run, MAX_INSTANCES)",
    ),
]

# ─── snapshot.py ────────────────────────────────────────────────────────

SNAPSHOT_EDITS = [
    (
        "    select_instances_by_impact,\n    resolve_forced_element,",
        "    select_instances_by_impact,\n    zones_du_journal,\n    resolve_forced_element,",
    ),
    (
        "def build_snapshot(scenario_slug, thematique=None, dry_run=True, forcer_config=None, date_edition=None):",
        "def build_snapshot(scenario_slug, thematique=None, dry_run=True, forcer_config=None, date_edition=None, zone_article=None):\n"
        "    # zone_article (S23, 3 octobre 2026) : zone de l'article quand elle\n"
        "    # est fixée par l'appelant (série, manuel, generate.py) -- réserve\n"
        "    # des places aux instances de la zone du journal, voir\n"
        "    # loader.zones_du_journal(). None = comportement inchangé.",
    ),
    (
        "        filtered_instances = filter_instances_for_thematique(\n"
        "            all_instances, thematique, scenario_slug=scenario_slug, dry_run=dry_run\n"
        "        )",
        "        filtered_instances = filter_instances_for_thematique(\n"
        "            all_instances, thematique, scenario_slug=scenario_slug, dry_run=dry_run,\n"
        "            zones_article=zones_du_journal(scenario_slug, zone_article) if zone_article else None,\n"
        "        )",
    ),
]

# ─── appelants ──────────────────────────────────────────────────────────

SERIES_EDITS = [(
    "snapshot = build_snapshot(scenario, thematique=thema_data, dry_run=dry_run, "
    "forcer_config=forcer_config, date_edition=date_edition)",
    "snapshot    = build_snapshot(scenario, thematique=thema_data, dry_run=dry_run,\n"
    "                                      forcer_config=forcer_config, date_edition=date_edition,\n"
    "                                      zone_article=article_config.get(\"zone_slug\") or None)",
)]

GENERATE_EDITS = [(
    "snapshot = build_snapshot(scenario_slug, thematique=thematique_obj, dry_run=dry_run, "
    "forcer_config=forcer_config, date_edition=date_edition)",
    "snapshot = build_snapshot(scenario_slug, thematique=thematique_obj,\n"
    "                               dry_run=dry_run, forcer_config=forcer_config,\n"
    "                               date_edition=date_edition,\n"
    "                               zone_article=config.get(\"zone_slug\") or None)",
)]

MANUAL_EDITS = [(
    "snapshot = build_snapshot(config[\"scenario\"], thematique=thema_data, date_edition=date_edition)",
    "snapshot   = build_snapshot(config[\"scenario\"], thematique=thema_data, date_edition=date_edition,\n"
    "                               zone_article=article_config.get(\"zone_slug\") or None)",
)]

# generate_series.py / generate_manual.py retirés (vérifié le 3 octobre :
# aucune zone n'y est jamais fixée -- leur zone d'article EST la zone
# dominante des instances, cohérente par construction).
FICHIERS = [
    ("loader.py", LOADER_EDITS),
    ("snapshot.py", SNAPSHOT_EDITS),
    ("generate.py", GENERATE_EDITS),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    resultats = {}
    ok_global = True
    for nom, edits in FICHIERS:
        texte = open(nom, encoding="utf-8").read()
        if "zones_du_journal" in texte or "zone_article=" in texte:
            print("✗ {} : semble déjà patché, rien à faire".format(nom))
            ok_global = False
            continue
        for old, new in edits:
            motif = re.compile(flex(old))
            n = len(motif.findall(texte))
            etiquette = old.strip().split("\n")[0][:70]
            if n != 1:
                print("✗ {} : {} occurrence(s) pour « {} »".format(nom, n, etiquette))
                ok_global = False
                continue
            # Le motif commence au premier caractère non blanc : l'indentation
            # d'origine reste en place devant, d'où new.lstrip().
            texte = motif.sub(lambda m, r=new.lstrip(): r, texte, count=1)
            print("✓ {} : « {} »".format(nom, etiquette))
        resultats[nom] = texte

    t = open("generate.py", encoding="utf-8").read()
    print("  info generate.py : « zone_slug » présent {} fois".format(t.count("zone_slug")))

    if not ok_global:
        print("\nAu moins une cible introuvable : rien n'est écrit.")
        sys.exit(1)
    if not args.apply:
        print("\nAperçu OK, rien n'est écrit. Relance avec --apply.")
        return

    for nom, texte in resultats.items():
        shutil.copy2(nom, nom + ".bak_zone_instances")
        open(nom, "w", encoding="utf-8").write(texte)
        try:
            py_compile.compile(nom, doraise=True)
            print("écrit + compilé : {}".format(nom))
        except py_compile.PyCompileError as e:
            shutil.copy2(nom + ".bak_zone_instances", nom)
            print("✗ compilation échouée, {} restauré : {}".format(nom, e))
            sys.exit(1)


if __name__ == "__main__":
    main()
