#!/usr/bin/env python3
"""
migrer_echelles.py — Ourrassol 2098
------------------------------------
Migration "convention unique d'intensité" (décidée le 27 septembre 2026) :
pour les 12 variables, level 0 = situation calme/stable, level 100 =
crise/pression maximale. polarite +1 = aggrave/intensifie.

Ce script fait EN UNE FOIS les étapes 1 et 2 du plan (elles ne doivent
jamais être appliquées séparément -- niveaux inversés sans matrice
inversée = propagation dans le mauvais sens) :

  1. variables/*.md
     - ajoute un bloc `echelle:` (type, zero, cent) dans le frontmatter
       des 12 fiches (juste avant `states:`, ignoré s'il existe déjà) ;
     - réécrit les levels de gouvernance_institutions et
       frontieres_du_systeme (échelle inversée : capacité -> fragilité/
       désordre) et 2 levels de sante_biotechnologies ;
     - met à jour les mêmes levels dans le texte de la section 8
       ("- **level** : N").
  2. variables/influence_matrix.md (ou chemin trouvé automatiquement)
     - inverse la polarité des liens qui touchent EXACTEMENT UNE des deux
       variables inversées (un lien gouvernance <-> frontieres touche les
       deux : double inversion = polarité inchangée) -> 40 liens attendus ;
     - dans le frontmatter (edges) ET dans les tableaux du corps.

Par défaut : SIMULATION, rien n'est écrit. Avec --appliquer : chaque
fichier modifié est d'abord sauvegardé en .bak, puis réécrit. Chaque
fichier est relu après modification et vérifié (levels attendus, nombre
de liens inversés) -- en cas d'écart, rien n'est écrit pour ce fichier.

Usage (depuis la racine du vault) :
  python3 generator/migrer_echelles.py              # simulation
  python3 generator/migrer_echelles.py --appliquer  # écriture réelle
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
VARIABLES_DIR = VAULT_ROOT / "variables"

INVERSEES = {"gouvernance_institutions", "frontieres_du_systeme"}

NOUVEAUX_LEVELS = {
    "gouvernance_institutions": {
        "breakdown": 80, "fortress_world": 50, "reference": 40,
        "eco_communalism": 25, "policy_reform": 20, "new_sustainability": 10,
    },
    "frontieres_du_systeme": {
        "breakdown": 85, "reference": 55, "fortress_world": 70,
        "policy_reform": 55, "eco_communalism": 50, "new_sustainability": 20,
    },
    "sante_biotechnologies": {
        "new_sustainability": 30, "eco_communalism": 40,
    },
}

ECHELLES = {
    "climat_environnement_global": (
        "climat stabilisé, écosystèmes régénérés",
        "emballement climatique, basculements écologiques irréversibles"),
    "demographie_mobilite_humaine": (
        "populations stables, mobilité choisie et locale",
        "déplacements forcés massifs, crises migratoires généralisées"),
    "energie_ressources_critiques": (
        "abondance énergétique, aucune contrainte d'accès aux ressources",
        "pénurie systémique, conflits généralisés pour les ressources"),
    "geopolitique_conflits": (
        "paix structurelle, coopération internationale forte",
        "guerres multiples, effondrement de l'ordre international"),
    "organisation_territoires": (
        "territoires équilibrés, distribués et résilients",
        "effondrement des mégapoles, espaces humains fragmentés"),
    "sante_biotechnologies": (
        "systèmes de santé stables, risques sanitaires maîtrisés",
        "pandémies récurrentes, saturation et rupture des capacités de soin"),
    "systeme_economique_redistribution": (
        "économies stables et peu intégrées, faible tension financière",
        "crises financières systémiques, effondrement de la confiance monétaire"),
    "systemes_productifs_travail": (
        "production stable, travail humain préservé",
        "effondrement des chaînes productives, disparition du travail structuré"),
    "technologie_information": (
        "réseaux sobres et fiables, faible dépendance aux plateformes",
        "fragmentation des réseaux, désinformation, rupture des IA interconnectées"),
    "valeurs_culture_tempo_sociale": (
        "récits communs cohérents, temps social apaisé",
        "fragmentation extrême des valeurs, polarisation durable"),
    "gouvernance_institutions": (
        "coordination globale robuste et adaptative, légitimité institutionnelle forte",
        "effondrement de la légitimité, États fragmentés, aucune coordination"),
    "frontieres_du_systeme": (
        "espace coopératif et intégré, expansion ordonnée",
        "espace chaotique, orbites saturées et militarisées, conflits orbitaux"),
}

NB_LIENS_ATTENDUS = 40


# ─────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────

def decouper(raw):
    """Retourne (frontmatter_str, reste_du_fichier) ou (None, raw)."""
    m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*\n", raw, re.DOTALL)
    if not m:
        return None, raw
    return m.group(1), raw[m.end():]


def charger_yaml(fm_str):
    return yaml.safe_load(re.sub(r"\[\[([^\]]+)\]\]", r"\1", fm_str)) or {}


def ecrire(path, contenu, appliquer):
    """N'écrit que si le contenu change. La sauvegarde .bak n'est créée
    qu'une fois (jamais écrasée) : un second passage ne peut pas remplacer
    l'original par une version déjà migrée."""
    actuel = path.read_text(encoding="utf-8")
    if not appliquer or contenu == actuel:
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(actuel, encoding="utf-8")
    path.write_text(contenu, encoding="utf-8")


# ─────────────────────────────────────────
# Étape 1 — fiches variables
# ─────────────────────────────────────────

def bloc_echelle(slug):
    zero, cent = ECHELLES[slug]
    return (
        "echelle:\n"
        "  type: intensite\n"
        f"  zero: \"{zero}\"\n"
        f"  cent: \"{cent}\"\n"
    )


def maj_levels_frontmatter(fm_str, cibles):
    """Remplace `level: N` sous states.<scen> pour chaque scénario cible."""
    lignes = fm_str.split("\n")
    dans_states = False
    scen_courant = None
    indent_scen = None
    faits = set()
    for i, ligne in enumerate(lignes):
        if re.match(r"^states:\s*$", ligne):
            dans_states = True
            continue
        if dans_states and re.match(r"^\S", ligne):
            dans_states = False  # clé racine suivante
        if not dans_states:
            continue
        m_scen = re.match(r"^(\s+)([a-z_]+):\s*$", ligne)
        if m_scen and (indent_scen is None or len(m_scen.group(1)) == indent_scen):
            if m_scen.group(2) in ("breakdown", "fortress_world", "new_sustainability",
                                   "eco_communalism", "policy_reform", "reference"):
                indent_scen = len(m_scen.group(1))
                scen_courant = m_scen.group(2)
                continue
        m_lvl = re.match(r"^(\s+level:\s*)(\S+)(.*)$", ligne)
        if m_lvl and scen_courant in cibles and scen_courant not in faits:
            lignes[i] = f"{m_lvl.group(1)}{cibles[scen_courant]}{m_lvl.group(3)}"
            faits.add(scen_courant)
    return "\n".join(lignes), faits


def maj_levels_section8(corps, cibles):
    """Remplace '- **level** : N' sous '### [[scen]]' dans la section 8."""
    faits = set()
    for scen, val in cibles.items():
        pat = re.compile(
            r"(^###\s*\[\[" + re.escape(scen) + r"\]\]\s*\n+-\s*\*\*level\*\*\s*:\s*)(\d+(?:\.\d+)?)",
            re.M,
        )
        corps, n = pat.subn(lambda m: f"{m.group(1)}{val}", corps, count=1)
        if n:
            faits.add(scen)
    return corps, faits


def migrer_variable(slug, appliquer, rapport):
    path = VARIABLES_DIR / f"{slug}.md"
    if not path.exists():
        rapport.append(f"  ✗ {slug} : fichier absent")
        return False
    raw = path.read_text(encoding="utf-8")
    fm_str, corps = decouper(raw)
    if fm_str is None:
        rapport.append(f"  ✗ {slug} : frontmatter introuvable")
        return False

    notes = []
    # Bloc echelle
    if re.search(r"^echelle:\s*$", fm_str, re.M):
        notes.append("échelle déjà présente (inchangée)")
    else:
        m_states = re.search(r"^states:\s*$", fm_str, re.M)
        if not m_states:
            rapport.append(f"  ✗ {slug} : clé 'states:' introuvable")
            return False
        fm_str = fm_str[:m_states.start()] + bloc_echelle(slug) + fm_str[m_states.start():]
        notes.append("échelle ajoutée")

    # Levels
    cibles = NOUVEAUX_LEVELS.get(slug, {})
    avant = {}
    if cibles:
        avant = {s: (charger_yaml(decouper(raw)[0]).get("states", {}).get(s) or {}).get("level")
                 for s in cibles}
        fm_str, faits_fm = maj_levels_frontmatter(fm_str, cibles)
        corps, faits_s8 = maj_levels_section8(corps, cibles)
        if faits_fm != set(cibles):
            rapport.append(f"  ✗ {slug} : levels frontmatter non trouvés pour {sorted(set(cibles) - faits_fm)}")
            return False
        manquants_s8 = set(cibles) - faits_s8
        if manquants_s8:
            notes.append(f"⚠ section 8 non trouvée pour {sorted(manquants_s8)} (frontmatter OK)")
        notes.append("levels : " + ", ".join(f"{s} {avant[s]}→{v}" for s, v in cibles.items()))

    # Vérification par relecture
    try:
        fm = charger_yaml(fm_str)
    except yaml.YAMLError as e:
        rapport.append(f"  ✗ {slug} : YAML invalide après modification ({e.__class__.__name__}), rien écrit")
        return False
    ech = fm.get("echelle") or {}
    if ech.get("type") != "intensite":
        rapport.append(f"  ✗ {slug} : bloc echelle illisible après modification, rien écrit")
        return False
    for s, v in cibles.items():
        lu = (fm.get("states", {}).get(s) or {}).get("level")
        if lu != v:
            rapport.append(f"  ✗ {slug} : {s} relu à {lu}, attendu {v}, rien écrit")
            return False

    ecrire(path, f"---\n{fm_str}\n---\n{corps}", appliquer)
    rapport.append(f"  ✓ {slug} : " + " ; ".join(notes))
    return True


# ─────────────────────────────────────────
# Étape 2 — matrice d'influence
# ─────────────────────────────────────────

def trouver_matrice():
    for p in [VARIABLES_DIR / "influence_matrix.md", VAULT_ROOT / "influence_matrix.md"]:
        if p.exists():
            return p
    trouves = [p for p in VAULT_ROOT.rglob("influence_matrix.md") if ".bak" not in p.name]
    return trouves[0] if trouves else None


def a_inverser(src, tgt):
    return (src in INVERSEES) != (tgt in INVERSEES)


def migrer_matrice(appliquer, rapport):
    path = trouver_matrice()
    if not path:
        rapport.append("  ✗ influence_matrix.md introuvable")
        return False
    raw = path.read_text(encoding="utf-8")
    fm_str, corps = decouper(raw)
    if re.search(r"^convention_echelle:", fm_str, re.M):
        rapport.append(f"  ✓ {path.relative_to(VAULT_ROOT)} : déjà migrée (convention_echelle présente), inchangée")
        return True
    edges_avant = charger_yaml(fm_str).get("edges", []) or []

    # Frontmatter : blocs "- source: ... target: ... polarity: N"
    lignes = fm_str.split("\n")
    src = tgt = None
    nb_fm = 0
    for i, ligne in enumerate(lignes):
        m = re.match(r"^\s*-\s*source:\s*\[*([a-z_]+)\]*\s*$", ligne)
        if m:
            src, tgt = m.group(1), None
            continue
        m = re.match(r"^\s*target:\s*\[*([a-z_]+)\]*\s*$", ligne)
        if m:
            tgt = m.group(1)
            continue
        m = re.match(r"^(\s*polarity:\s*)(-?1)\s*$", ligne)
        if m and src and tgt:
            if a_inverser(src, tgt):
                lignes[i] = f"{m.group(1)}{-int(m.group(2))}"
                nb_fm += 1
            src = tgt = None
    fm_str = "\n".join(lignes)

    # Corps : tableaux. "Liens forts" = | [[src]] | [[tgt]] | w | ± | ...
    # "Détail par variable" = sous "### [[src]]" : | [[tgt]] | w | ± | ...
    inv_signe = {"+": "−", "−": "+", "-": "+"}
    lignes = corps.split("\n")
    src_section = None
    nb_corps = 0
    for i, ligne in enumerate(lignes):
        m = re.match(r"^###\s*\[\[([a-z_]+)\]\]", ligne)
        if m:
            src_section = m.group(1)
            continue
        if re.match(r"^##\s", ligne):
            src_section = None
        if not ligne.startswith("|"):
            continue
        cells = ligne.split("|")
        vals = [c.strip() for c in cells]
        liens = [re.fullmatch(r"\[\[([a-z_]+)\]\]", v) for v in vals]
        idx = [k for k, l in enumerate(liens) if l]
        if len(idx) >= 2 and idx[1] == idx[0] + 1:          # tableau "Liens forts"
            s, t, k_pol = liens[idx[0]].group(1), liens[idx[1]].group(1), idx[1] + 2
        elif len(idx) == 1 and src_section:                  # tableau de détail
            s, t, k_pol = src_section, liens[idx[0]].group(1), idx[0] + 2
        else:
            continue
        if k_pol >= len(vals) or vals[k_pol] not in inv_signe:
            continue
        if a_inverser(s, t):
            ancien = cells[k_pol]
            cells[k_pol] = ancien.replace(vals[k_pol], inv_signe[vals[k_pol]], 1)
            lignes[i] = "|".join(cells)
            nb_corps += 1
    corps = "\n".join(lignes)

    # Vérification par relecture
    edges_apres = charger_yaml(fm_str).get("edges", []) or []
    attendu = sum(1 for e in edges_avant if a_inverser(e["source"], e["target"]))
    changes = sum(1 for a, b in zip(edges_avant, edges_apres) if a["polarity"] != b["polarity"])
    faux = [e for a, e in zip(edges_avant, edges_apres)
            if (a["polarity"] != e["polarity"]) != a_inverser(e["source"], e["target"])]
    if nb_fm != attendu or changes != attendu or faux or len(edges_apres) != len(edges_avant):
        rapport.append(f"  ✗ matrice : vérification échouée (attendu {attendu}, frontmatter {nb_fm}, "
                       f"relu {changes}, anomalies {len(faux)}), rien écrit")
        return False
    if attendu != NB_LIENS_ATTENDUS:
        rapport.append(f"  ⚠ matrice : {attendu} liens concernés (prévu {NB_LIENS_ATTENDUS}) -- à vérifier")

    fm_str = fm_str.rstrip("\n") + "\nconvention_echelle: intensite_2026-09-27\n"
    ecrire(path, f"---\n{fm_str}\n---\n{corps}", appliquer)
    rapport.append(f"  ✓ {path.relative_to(VAULT_ROOT)} : {nb_fm} liens inversés dans le frontmatter, "
                   f"{nb_corps} lignes inversées dans les tableaux du corps")
    return True


# ─────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--appliquer", action="store_true", help="Écrit réellement (avec .bak)")
    args = ap.parse_args()

    print("=== MIGRATION ÉCHELLES — {} ===".format("ÉCRITURE RÉELLE" if args.appliquer else "SIMULATION (rien n'est écrit)"))
    rapport = ["", "Étape 1 — fiches variables"]
    ok = all([migrer_variable(slug, args.appliquer, rapport) for slug in ECHELLES])
    rapport += ["", "Étape 2 — matrice d'influence"]
    ok = migrer_matrice(args.appliquer, rapport) and ok
    print("\n".join(rapport))
    print("\n" + ("Tout est OK." if ok else "⚠ Au moins une erreur (✗) : voir ci-dessus."))
    if ok and not args.appliquer:
        print("Relance avec --appliquer pour écrire (sauvegardes .bak automatiques).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
