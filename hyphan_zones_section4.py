#!/usr/bin/env python3
"""
hyphan_zones_section4.py — Ourrassol 2098 (one-shot, 24 septembre 2026)

Chantier Hyphan, section 4 (zones), décisions de David du 24 sept :
  - 3 nouvelles sous-zones de Zone Euro Sud ("le Hors") : Paris, Évry
    (sous Paris), Tolosa dite Saint-Sernin-du-Désert ;
  - descriptions complétées : Zone Euro Sud ("le Hors"), Al-Hima
    ("Califat de Barcelone"), Espace Nordique et Arctique ("Euro-Nord",
    gouverné par Ergo-Wian, NAT = filiale armée).

Met à jour le frontmatter (lu par les scripts) ET le corps markdown
(sections lisibles dans Obsidian). SIMULATION PAR DÉFAUT : rien n'est écrit
sans --execute. Le frontmatter est relu après modification ; le script
refuse d'écrire si la relecture ne correspond pas exactement au résultat
attendu, ou si un texte à modifier n'est pas trouvé à l'identique.

USAGE (depuis la racine du vault)
    python3 hyphan_zones_section4.py            # simulation
    python3 hyphan_zones_section4.py --execute
"""

import argparse
import copy
import re
import sys
from pathlib import Path

import yaml

FICHIER = Path(__file__).resolve().parent / "geographie" / "fortress_world.md"

NOUVELLES_ZONES = [
    {
        "slug": "paris_hors", "nom": "Paris", "niveau": 2, "type": "ville",
        "parent": "zone_euro_sud",
        "origine_reelle": [{"entite": "Paris", "type_entite": "region_administrative", "portion": None}],
        "description": (
            "Ancienne capitale réduite à un champ de ruines habité, aux portes de la Zone "
            "Interdite de Heysham qui a englouti la basse Seine en 2044. Ses anciens quartiers "
            "résidentiels sont la principale mine de métaux du « monde d'avant » : les Recycleurs "
            "y tiennent leurs « cycles », centres de collecte où tout se revend, tandis que les "
            "raids de la Reconquête européenne frappent les communautés de déplacés, dont une "
            "importante diaspora issue des migrations de la guerre indo-arabe de 2038."),
        "statut": "en_declin",
        "tensions_internes": (
            "Guerre de rues entre Recycleurs et Reconquête européenne pour le contrôle des "
            "quartiers et du recrutement forcé ; rapts de jeunes adultes destinés à la traite ; "
            "transactions discrètes des deux factions avec Ergo-Wian."),
        "periode_transition": "2044-2060",
        "evenement_transition": None,
        "lieux_emblematiques": [],
        "relations": {"allies": [], "rivaux": []},
        "sources_attestees": [],
    },
    {
        "slug": "evry_hors", "nom": "Évry", "niveau": 3, "type": "site_strategique",
        "parent": "paris_hors",
        "origine_reelle": [{"entite": "Évry", "type_entite": "region_administrative", "portion": None}],
        "description": (
            "Ancienne ville nouvelle du sud parisien dont les laboratoires de biotechnologie "
            "abandonnés — l'ancien Génopole — servent de terrain neutre de fait : factions "
            "ennemies et émissaires d'Ergo-Wian y négocient à l'abri des regards contrats de "
            "service, livraisons de travailleurs et marchés inavouables."),
        "statut": "en_declin",
        "tensions_internes": (
            "Neutralité tacite fragile, garantie par l'intérêt commun des factions à commercer "
            "avec Ergo-Wian ; nul ne sait qui surveille qui dans les anciens laboratoires."),
        "periode_transition": "2044-2060",
        "evenement_transition": None,
        "lieux_emblematiques": [],
        "relations": {"allies": [], "rivaux": []},
        "sources_attestees": [],
    },
    {
        "slug": "tolosa_saint_sernin_du_desert", "nom": "Tolosa — Saint-Sernin-du-Désert",
        "niveau": 2, "type": "ville", "parent": "zone_euro_sud",
        "origine_reelle": [{"entite": "Toulouse", "type_entite": "region_administrative", "portion": None}],
        "description": (
            "Cité-refuge du sud du Hors, dressée au milieu d'une plaine quasi désertique où l'été "
            "approche les 50 °C. Organisée autour de l'ancienne basilique Saint-Sernin, elle vit "
            "comme un monastère du désert, à la manière des refuges cathares d'autrefois. La tribu "
            "des Cinq Nations, clan indépendant dirigé par sa cheffe-chamane, la tient hors de "
            "portée des Recycleurs comme de la Reconquête européenne. Elle entretient des liens "
            "étroits d'échange et de passage avec Al-Hima, de l'autre côté des Pyrénées, sans lui "
            "appartenir."),
        "statut": "stable",
        "tensions_internes": (
            "Convoitise des deux factions ; eau rare ; équilibre délicat entre indépendance et "
            "dépendance commerciale envers Al-Hima."),
        "periode_transition": "2050-2075",
        "evenement_transition": None,
        "lieux_emblematiques": [],
        "relations": {"allies": ["al_hima"], "rivaux": []},
        "sources_attestees": [],
    },
]

# (slug, texte existant exact ou None pour un simple ajout en fin, nouveau texte)
MODIFS_DESCRIPTION = [
    ("zone_euro_sud", None,
     " Dans la langue courante, on l'appelle simplement « le Hors » : le territoire "
     "hors-forteresse, livré aux factions armées qui s'y disputent le pouvoir et l'accès "
     "aux contrats d'Ergo-Wian."),
    ("al_hima", None,
     " Connue dans le Hors sous le nom populaire de « Califat de Barcelone », que les légendes "
     "peuplent de sorciers et de guerriers aux pouvoirs surnaturels, bien que la religion ne "
     "soit pas le fondement de l'union."),
    ("espace_nordique_arctique",
     "La Nordisk Arktisk Transitkontroll (NAT), opérateur armé sous supervision des blocs nordiques,",
     "La Nordisk Arktisk Transitkontroll (NAT), filiale armée d'Ergo-Wian,"),
    ("espace_nordique_arctique", None,
     " Surnommée « Euro-Nord » dans le Hors, la zone est de fait gouvernée par Ergo-Wian, qui y "
     "détient les pleins pouvoirs au service d'une population vieillissante protégée par ses "
     "forteresses."),
]

# Corps markdown : (texte exact à trouver, remplacement)
MODIFS_CORPS = [
    ("Espace géopolitique distinct contrôlé de facto par la Nordisk Arktisk Transitkontroll "
     "(NAT), opérateur privé armé",
     "Espace géopolitique distinct, surnommé « Euro-Nord » dans le Hors, gouverné par Ergo-Wian "
     "et contrôlé sur le terrain par sa filiale armée, la Nordisk Arktisk Transitkontroll (NAT), "
     "opérateur privé"),
]


def section_corps(z, parent_nom):
    ori = ", ".join(o["entite"] for o in z["origine_reelle"])
    titre = "#" * (z["niveau"] + 2)
    lignes = [f"{titre} {z['nom']} — sous [[{z['parent']}]]", "",
              f"*{z['type']} — niveau {z['niveau']} — statut : {z['statut']}*", "",
              f"**Origine réelle (2026)** : {ori}", "",
              f"**Transition** : {z['periode_transition']}", "",
              z["description"], "",
              f"**Tensions internes** : {z['tensions_internes']}", ""]
    return "\n".join(lignes) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()
    if not FICHIER.exists():
        sys.exit(f"✗ {FICHIER} introuvable — lancer depuis la racine du vault.")
    texte = FICHIER.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", texte, re.S)
    fm_txt, corps = m.group(1), texte[m.end():]
    fm = yaml.safe_load(fm_txt)
    zones = {z["slug"]: z for z in fm["zones"]}
    erreurs = []

    # 1. descriptions (frontmatter) — modifications sur le TEXTE, validées par relecture
    attendu = copy.deepcopy(fm)
    att_z = {z["slug"]: z for z in attendu["zones"]}
    nouveau_fm_txt = fm_txt
    for slug, ancien, nouveau in MODIFS_DESCRIPTION:
        d = att_z[slug]["description"]
        if ancien is None:
            if nouveau.strip() in d:
                print(f"  = {slug} : ajout déjà présent")
                continue
            att_z[slug]["description"] = d + nouveau
        else:
            if ancien not in d and nouveau in d:
                print(f"  = {slug} : remplacement déjà fait")
                continue
            if ancien not in d:
                erreurs.append(f"{slug} : texte à remplacer introuvable : {ancien[:60]}…")
                continue
            att_z[slug]["description"] = d.replace(ancien, nouveau, 1)
        print(f"  · description {slug} : {'ajout' if ancien is None else 'remplacement'}")

    # Réécriture du bloc description de chaque zone modifiée (scalaire replié)
    for slug in {s for s, _, _ in MODIFS_DESCRIPTION}:
        mz = re.search(rf"^- slug: {slug}\n(?:  .*\n)*?  description: .*\n(?:    .*\n)*", nouveau_fm_txt + "\n", re.M)
        if not mz:
            erreurs.append(f"{slug} : bloc description introuvable")
            continue
        bloc = mz.group(0)
        md = re.search(r"^  description: .*\n(?:    .*\n)*", bloc, re.M)
        neuf = yaml.dump({"description": att_z[slug]["description"]}, allow_unicode=True, width=88)
        neuf = "".join("  " + l + "\n" for l in neuf.rstrip("\n").split("\n"))
        bloc2 = bloc[:md.start()] + neuf + bloc[md.end():]
        nouveau_fm_txt = nouveau_fm_txt.replace(bloc, bloc2, 1) if nouveau_fm_txt.count(bloc) == 1 \
            else (nouveau_fm_txt + "\n").replace(bloc, bloc2, 1).rstrip("\n")

    # 2. nouvelles zones (ajoutées en fin de liste zones, dernière clé du frontmatter)
    for z in NOUVELLES_ZONES:
        if z["slug"] in zones:
            print(f"  = zone {z['slug']} : existe déjà")
            continue
        if z["parent"] not in zones and z["parent"] not in {n["slug"] for n in NOUVELLES_ZONES}:
            erreurs.append(f"{z['slug']} : parent {z['parent']} introuvable")
            continue
        attendu["zones"].append(z)
        nouveau_fm_txt = nouveau_fm_txt.rstrip("\n") + "\n" + \
            yaml.dump([z], allow_unicode=True, sort_keys=False, width=88).rstrip("\n")
        print(f"  · nouvelle zone {z['slug']} (niveau {z['niveau']}, sous {z['parent']})")

    relu = yaml.safe_load(nouveau_fm_txt)
    if relu != attendu:
        diff = [z["slug"] for z, r in zip(attendu["zones"], relu["zones"]) if z != r]
        erreurs.append(f"relecture du frontmatter différente de l'attendu (zones : {diff[:5]})")

    # 3. corps markdown
    nouveau_corps = corps
    for ancien, nouveau in MODIFS_CORPS:
        if nouveau in nouveau_corps:
            continue
        if nouveau_corps.count(ancien) != 1:
            print(f"  ⚠ corps : texte introuvable (ignoré, frontmatter prioritaire) : {ancien[:50]}…")
            continue
        nouveau_corps = nouveau_corps.replace(ancien, nouveau, 1)
        print("  · corps : Espace Nordique mis à jour")
    ancre = "\n## Notes / zones à enrichir"
    ajout = "".join(section_corps(z, None) + "\n" for z in NOUVELLES_ZONES if z["slug"] not in zones)
    if ajout:
        if nouveau_corps.count(ancre) != 1:
            erreurs.append("corps : section '## Notes / zones à enrichir' introuvable")
        else:
            nouveau_corps = nouveau_corps.replace(ancre, "\n" + ajout.rstrip("\n") + "\n" + ancre, 1)
            print("  · corps : sections des nouvelles zones ajoutées")

    if erreurs:
        print("\n✗ RIEN N'A ÉTÉ ÉCRIT :")
        for e in erreurs:
            print("   -", e)
        sys.exit(1)
    if a.execute:
        FICHIER.write_text("---\n" + nouveau_fm_txt + "\n---\n" + nouveau_corps, encoding="utf-8")
        print("\n✓ Écrit.")
    else:
        print("\nSimulation OK — relancer avec --execute pour écrire.")


if __name__ == "__main__":
    main()
