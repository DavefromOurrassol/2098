#!/usr/bin/env python3
"""
regenerer_corps_geographie.py — Ourrassol 2098 (26 sept 2026, S15)
===================================================================

Reconstruit, SANS IA, la section « ## Zones » du corps markdown de
geographie/{scenario}.md à partir du frontmatter actuel (la seule source
de vérité, celle que lisent tous les scripts et le GUI). Le corps n'était
jamais mis à jour quand le frontmatter changeait (Carte, renommages,
déplacements…) et finissait par le contredire.

NE TOUCHE PAS :
  - au frontmatter (recopié octet pour octet) ;
  - à « ## Vue d'ensemble », « ## Notes / zones à enrichir », ni à toute
    autre section hors « ## Zones ».

Format repris de build_geographie_monde.py / enrich_geographie_recursive.py :
titre ### (niveau 1), #### (niveau 2), ##### (niveau 3)…, « — sous
[[parent]] » pour une sous-zone, zones rangées en arbre (chaque zone suivie
de ses sous-zones).

Usage (depuis la racine du vault) :
  python3 generator/regenerer_corps_geographie.py --scenario fortress_world            # aperçu
  python3 generator/regenerer_corps_geographie.py --scenario fortress_world --execute  # écrit (.bak)
  python3 generator/regenerer_corps_geographie.py --all
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"
SCENARIOS = ["breakdown", "fortress_world", "new_sustainability",
             "eco_communalism", "policy_reform", "reference"]


def rendre_zone(z, noms):
    niveau = int(z.get("niveau") or 1)
    titre = "#" * min(2 + niveau, 6)
    parent = z.get("parent")
    L = [f"{titre} {z.get('nom', z.get('slug'))}"
         + (f" — sous [[{parent}]]" if parent else ""), ""]
    meta = [str(z.get("type") or "?")]
    if niveau > 1:
        meta.append(f"niveau {niveau}")
    meta.append(f"statut : {z.get('statut') or '?'}")
    L += [f"*{' — '.join(meta)}*", ""]

    origine = []
    for o in z.get("origine_reelle") or []:
        if isinstance(o, dict):
            p = str(o.get("entite") or "?")
            if o.get("portion"):
                p += f" ({o['portion']})"
            origine.append(p)
        else:
            origine.append(str(o))
    if origine:
        L += [f"**Origine réelle (2026)** : {', '.join(origine)}", ""]
    if z.get("periode_transition"):
        evt = z.get("evenement_transition")
        L += [f"**Transition** : {z['periode_transition']}" + (f" — voir [[{evt}]]" if evt else ""), ""]
    if z.get("description"):
        L += [" ".join(str(z["description"]).split()), ""]
    if z.get("tensions_internes"):
        L += [f"**Tensions internes** : {' '.join(str(z['tensions_internes']).split())}", ""]
    lieux = z.get("lieux_emblematiques") or []
    if lieux:
        L.append("**Lieux emblématiques** :")
        for lieu in lieux:
            if isinstance(lieu, dict):
                t = f" ({lieu['type']})" if lieu.get("type") else ""
                n = f" — {lieu['notes']}" if lieu.get("notes") else ""
                L.append(f"- {lieu.get('nom', '?')}{t}{n}")
            else:
                L.append(f"- {lieu}")
        L.append("")
    rel = z.get("relations") or {}
    for champ, lib in (("allies", "Alliés"), ("rivaux", "Rivaux")):
        if rel.get(champ):
            L += [f"**{lib}** : " + ", ".join(f"{noms.get(s, s)} ([[{s}]])" for s in rel[champ]), ""]
    if z.get("sources_attestees"):
        L += [f"*Sources attestées : {', '.join(z['sources_attestees'])}*", ""]
    return L


def rendre_zones(zones):
    noms = {z["slug"]: z.get("nom", z["slug"]) for z in zones if z.get("slug")}
    enfants = {}
    for z in zones:
        enfants.setdefault(z.get("parent"), []).append(z)
    vus, out = set(), []

    def descendre(z):
        if z.get("slug") in vus:
            return
        vus.add(z.get("slug"))
        out.extend(rendre_zone(z, noms))
        for e in enfants.get(z.get("slug"), []):
            descendre(e)

    for z in enfants.get(None, []):
        descendre(z)
    orphelines = [z for z in zones if z.get("slug") not in vus]
    if orphelines:
        out += ["> ⚠ Zones dont le parent est introuvable :", ""]
        for z in orphelines:
            descendre(z)
    return "\n".join(out).rstrip() + "\n"


def corps_regenere(corps, zones):
    """Corps markdown (tout ce qui suit le frontmatter) avec la section
    « ## Zones » reconstruite depuis `zones`. Le reste du corps est gardé tel
    quel. Fonction pure, réutilisée par gui/zone_repository.py (_save_geo) pour
    tenir le corps à jour après chaque modification faite depuis la Carte."""
    nouvelle = "## Zones\n\n" + rendre_zones(zones) + "\n"
    sec = re.search(r"(?m)^## Zones[^\n]*\n.*?(?=^## |\Z)", corps, re.DOTALL)
    if sec:
        return corps[:sec.start()] + nouvelle + corps[sec.end():], sec.group(0)
    notes = re.search(r"(?m)^## Notes", corps)
    if notes:
        return corps[:notes.start()] + nouvelle + corps[notes.start():], ""
    return corps.rstrip("\n") + "\n\n" + nouvelle, ""


def traiter(scenario, execute):
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    if not path.exists():
        print(f"=== {scenario} : pas de fichier, ignoré")
        return
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n(.*?)\n---\s*\n)(.*)$", raw, re.DOTALL)
    if not m:
        print(f"=== {scenario} : frontmatter introuvable, ignoré")
        return
    entete, fm_txt, corps = m.group(1), m.group(2), m.group(3)
    zones = (yaml.safe_load(fm_txt) or {}).get("zones") or []
    corps_neuf, ancien_bloc = corps_regenere(corps, zones)

    n_titres_avant = len(re.findall(r"(?m)^#{3,6} ", ancien_bloc))
    print(f"=== {scenario} : {len(zones)} zone(s) dans le frontmatter — section « ## Zones » : "
          f"{n_titres_avant} titre(s) de zone avant, {len(zones)} après")
    if corps_neuf == corps:
        print("  (déjà à jour)")
        return
    if not execute:
        print("  aperçu seulement — relancer avec --execute pour écrire")
        return
    shutil.copy2(path, path.with_suffix(".md.bak_corps"))
    path.write_text(entete + corps_neuf, encoding="utf-8")
    relu = path.read_text(encoding="utf-8")
    ok = relu.startswith(entete)
    print("  ✓ écrit (.bak_corps)" + ("" if ok else " — ⚠ en-tête modifié, restaurer le .bak_corps"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scenario", choices=SCENARIOS)
    g.add_argument("--all", action="store_true")
    ap.add_argument("--execute", action="store_true", help="écrit (sinon aperçu)")
    a = ap.parse_args()
    print(f"Mode : {'ÉCRITURE' if a.execute else 'APERÇU (rien écrit)'}")
    for sc in (SCENARIOS if a.all else [a.scenario]):
        traiter(sc, a.execute)


if __name__ == "__main__":
    main()
