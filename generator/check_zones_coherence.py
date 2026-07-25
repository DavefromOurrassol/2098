#!/usr/bin/env python3
"""
check_zones_coherence.py — Ourrassol 2098
==========================================

Diagnostic de cohérence des fiches geographie/{scenario}.md :
  1. Parsing YAML valide (détecte une corruption d'indentation avant qu'elle
     ne casse silencieusement la carte)
  2. Pays réels (pays_liste) totalement absents de toute zone (aucune
     origine_reelle nulle part) — invisibles sur la carte, jamais proposés
     par complete_geographie_coverage.py si son propre index est désynchro.
  3. Pays réels rattachés uniquement à une sous-zone (N2/N3), sans aucune
     zone N1 — apparaissent gris/incohérents sur la carte (pas de légende,
     couleur de secours) même s'ils ont une entrée origine_reelle quelque
     part dans le fichier.
  4. Entrées de chantiers_geographie.yaml (type pays_sans_zone) qui ne correspondent plus à la réalité
     (pays qui a en fait déjà une zone N1 — entrée obsolète à nettoyer).

Ne modifie jamais rien — lecture seule, purement diagnostic.

USAGE
-----
    python3 check_zones_coherence.py --scenario reference
    python3 check_zones_coherence.py --all
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

import chantiers

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
GEO_DIR = VAULT_ROOT / "geographie"
GUI_DIR = VAULT_ROOT / "gui"
ZONES_PAYS = GUI_DIR / "zones_pays.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

# Variantes narratives connues du même pays, observées dans ce vault.
# Liste à enrichir manuellement si de nouveaux cas apparaissent (voir les
# pays encore signalés "absents" après un premier passage : vérifier au
# grep avant d'agir, certains sont peut-être juste une variante non listée
# ici plutôt qu'un vrai trou).
#
# Volontairement PAS de règle générique préfixe/suffixe : elle produirait
# des faux positifs dangereux entre pays réellement distincts qui partagent
# un mot (ex. "Guinée" matcherait à tort "Guinée équatoriale", "Congo"
# matcherait "République démocratique du Congo", "Soudan" matcherait
# "Soudan du Sud").
ALIASES = {
    "états-unis": ["états-unis d'amérique"],
    "arctique": ["arctique international"],
}


def _pays_present(pays_norm: str, entites: list) -> bool:
    """Teste si `pays_norm` est désigné par au moins une des chaînes
    `entites` (origine_reelle), en tolérant les mentions groupées
    (virgule/slash) et les variantes connues de ALIASES."""
    variantes_connues = set(ALIASES.get(pays_norm, []))
    for e in entites:
        e_clean = re.sub(r"\([^)]*\)", "", e).strip().lower()
        if e_clean in variantes_connues:
            return True
        tokens = [e_clean] + [t.strip() for t in re.split(r"[,/;]", e_clean)]
        if pays_norm in tokens:
            return True
    return False


def check_scenario(scenario: str, pays_liste_norm: set, pays_liste_original: list,
                    write_chantiers: bool = False) -> bool:
    """Vérifie un scénario. Retourne True si tout est cohérent."""
    print(f"\n=== {scenario} ===")
    geo_file = GEO_DIR / f"{scenario}.md"
    if not geo_file.exists():
        print(f"  ✗ Fiche introuvable : {geo_file}")
        return False

    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---")
    if len(parts) < 3:
        print(f"  ✗ Format de fichier inattendu (pas de frontmatter détecté)")
        return False

    # 1. Parsing YAML
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        print(f"  ✗ ERREUR DE PARSING YAML : {e}")
        print(f"    → Le fichier est corrompu. La carte affichera tout en bleu.")
        return False

    zones = fm.get("zones") or []
    n1_zones = [z for z in zones if isinstance(z, dict) and z.get("niveau", 1) == 1]
    print(f"  ✓ Parsing OK — {len(zones)} zones total, {len(n1_zones)} en niveau 1")

    ok = True

    # Regrouper les mentions par zone pour appliquer le matching pays->entités
    zones_avec_entites = []
    for z in zones:
        if not isinstance(z, dict):
            continue
        entites = [
            o.get("entite", "") for o in (z.get("origine_reelle") or [])
            if isinstance(o, dict) and o.get("entite")
        ]
        if entites:
            zones_avec_entites.append((z.get("slug", ""), z.get("niveau", 1), entites))

    # 2. Pays réels totalement absents de toute zone (aucune mention nulle part,
    #    y compris sous une variante narrative connue de ALIASES)
    absents = []
    presence = {}  # pays_norm -> liste de (slug, niveau) où il est mentionné
    for pays in pays_liste_original:
        pays_norm = pays.lower().strip()
        matches = [
            (slug, niveau) for slug, niveau, entites in zones_avec_entites
            if _pays_present(pays_norm, entites)
        ]
        if matches:
            presence[pays_norm] = matches
        else:
            absents.append(pays)

    if absents:
        ok = False
        print(f"  ✗ {len(absents)} pays totalement absent(s) de toute zone :")
        for p in sorted(absents):
            print(f"      - {p!r}")
        print(f"    (vérifier au grep avant d'agir — peut-être une variante de nom non listée dans ALIASES)")
        if write_chantiers:
            ajoutees = 0
            for p in absents:
                if chantiers.ajouter_chantier(
                    scenario=scenario, type_="pays_sans_zone", cible=p,
                    probleme=f"{p!r} n'apparaît dans aucune zone (tous niveaux) de {scenario}.",
                    source_diagnostic="zones_coherence",
                ):
                    ajoutees += 1
            if ajoutees:
                print(f"    ✓ {ajoutees} chantier(s) ajouté(s) à {chantiers.CHANTIERS_FILE.name}")
    else:
        print(f"  ✓ Tous les pays de pays_liste ont au moins une zone")

    # 3. Pays réels présents uniquement en sous-zone (aucune mention en niveau 1)
    problemes = [
        (pays, matches) for pays, matches in presence.items()
        if not any(niveau == 1 for _, niveau in matches) and pays in pays_liste_norm
    ]

    if problemes:
        ok = False
        print(f"  ⚠ {len(problemes)} pays réel(s) sans zone N1 (attaché(s) uniquement à une sous-zone) :")
        for pays, matches in sorted(problemes):
            slugs = ", ".join(f"{s} (niveau {n})" for s, n in matches)
            print(f"      - {pays!r} → {slugs}")
    else:
        print(f"  ✓ Tous les pays présents ont une zone N1")

    return ok


def check_zones_manquantes(pays_avec_n1_par_scenario: dict, marquer_resolus: bool) -> None:
    """
    Vérifie que les chantiers type="pays_sans_zone" de chantiers_geographie.yaml
    (module chantiers.py, remplace l'ancien zones_manquantes.yaml depuis le 25
    juillet 2026) ne contiennent pas d'entrées obsolètes -- un pays qui a en
    fait déjà une zone N1 correcte dans la fiche.

    --marquer-resolus (opt-in) : passe ces entrées obsolètes à statut="traite"
    directement -- contrairement au reste de ce diagnostic (lecture seule), ce
    cas précis ne demande aucun jugement narratif : si le pays a une zone N1,
    le problème d'origine n'existe objectivement plus. Sans ce flag, aperçu
    seul, comme avant.
    """
    print(f"\n=== chantiers pays_sans_zone (chantiers_geographie.yaml) ===")
    entries = chantiers.chantiers_eligibles(type_="pays_sans_zone")
    if not entries:
        print(f"  ✓ Aucun chantier pays_sans_zone actif — rien à vérifier")
        return

    obsoletes = []
    for e in entries:
        pays = (e.get("cible") or "").lower().strip()
        scenario = e.get("scenario") or ""
        pays_ok = pays_avec_n1_par_scenario.get(scenario, set())
        if pays in pays_ok:
            obsoletes.append((pays, scenario, e.get("cible"), e.get("scenario")))

    if not obsoletes:
        print(f"  ✓ {len(entries)} chantier(s) actif(s), aucun obsolète")
        return

    print(f"  ⚠ {len(obsoletes)} chantier(s) obsolète(s) (le pays a déjà une zone N1) :")
    for pays_norm, scenario_norm, pays_cible, scenario_cible in obsoletes:
        if marquer_resolus:
            chantiers.mettre_a_jour_chantier(
                scenario_cible, pays_cible, statut="traite",
                date_traitement=chantiers.date.today().isoformat(),
            )
            print(f"      - {pays_cible!r} / {scenario_cible} — marqué 'traite'")
        else:
            print(f"      - {pays_cible!r} / {scenario_cible} — relancer avec "
                  f"--marquer-resolus pour le marquer 'traite' automatiquement")


def main():
    parser = argparse.ArgumentParser(
        description="Diagnostic de cohérence des fiches géographie (lecture seule)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", help="Scénario unique à vérifier")
    group.add_argument("--all", action="store_true", help="Vérifier les 6 scénarios")
    parser.add_argument(
        "--write-chantiers", action="store_true",
        help="Ajoute à chantiers_geographie.yaml un chantier pays_sans_zone par "
             "pays totalement absent de toute zone. N'écrase jamais une entrée "
             "déjà présente. Sans ce flag, aperçu seul."
    )
    parser.add_argument(
        "--marquer-resolus", action="store_true",
        help="Marque automatiquement statut='traite' les chantiers pays_sans_zone "
             "devenus obsolètes (le pays a déjà une zone N1) -- seul cas de ce "
             "diagnostic où aucun jugement narratif n'est nécessaire. Sans ce "
             "flag, aperçu seul (comme le reste du diagnostic)."
    )
    args = parser.parse_args()

    if not ZONES_PAYS.exists():
        print(f"✗ {ZONES_PAYS} introuvable.")
        sys.exit(1)
    zones_pays = json.loads(ZONES_PAYS.read_text(encoding="utf-8"))
    pays_liste_original = zones_pays.get("pays_liste", [])
    pays_liste_norm = {p.lower().strip() for p in pays_liste_original}

    scenarios = SCENARIOS if args.all else [args.scenario]
    if args.scenario and args.scenario not in SCENARIOS:
        print(f"✗ Scénario inconnu : {args.scenario}")
        print(f"  Scénarios valides : {', '.join(SCENARIOS)}")
        sys.exit(1)

    print("=" * 60)
    print("  Diagnostic de cohérence — geographie/{scenario}.md")
    print("=" * 60)

    all_ok = True
    pays_avec_n1_par_scenario = {}
    for s in scenarios:
        ok = check_scenario(s, pays_liste_norm, pays_liste_original, args.write_chantiers)
        all_ok = all_ok and ok

        # Recalcul rapide pour la vérification des chantiers pays_sans_zone
        geo_file = GEO_DIR / f"{s}.md"
        if geo_file.exists():
            try:
                fm = yaml.safe_load(geo_file.read_text(encoding="utf-8").split("---")[1]) or {}
                zones_n1 = [
                    z for z in (fm.get("zones") or [])
                    if isinstance(z, dict) and z.get("niveau", 1) == 1
                ]
                entites_n1 = [
                    o.get("entite", "") for z in zones_n1
                    for o in (z.get("origine_reelle") or [])
                    if isinstance(o, dict) and o.get("entite")
                ]
                pays_n1 = {
                    p.lower().strip() for p in pays_liste_original
                    if _pays_present(p.lower().strip(), entites_n1)
                }
                pays_avec_n1_par_scenario[s] = pays_n1
            except Exception:
                pass

    if args.all:
        check_zones_manquantes(pays_avec_n1_par_scenario, args.marquer_resolus)

    print("\n" + "=" * 60)
    print("  Terminé — tout est cohérent." if all_ok else "  Terminé — des points d'attention ont été relevés ci-dessus.")
    print("=" * 60)


if __name__ == "__main__":
    main()
