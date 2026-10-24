#!/usr/bin/env python3
"""
fusionner_doublon_instance.py — Ourrassol 2098 (S24, 13 octobre 2026 ; v2 du 24 octobre 2026)
=============================================================================================

Fusionne deux instances qui décrivent la même entité : toutes les citations
de l'instance RETIRÉE sont redirigées vers l'instance GARDÉE, puis la fiche
retirée (et son archétype s'il ne sert à aucune autre instance) est mise de
côté dans _a_supprimer/ à la racine du vault. Rien n'est supprimé.

Ce qui est réécrit (fichiers .md seulement ; .bak, .zip ignorés) :
  instances/, event_instances/, evenements/, entites/, articles/, geographie/
  - slug exact (mot entier : « archives_neutres_geneve » seul, qui est aussi
    un slug de ZONE, n'est jamais touché) ;
  - doublons créés par la fusion retirés : même élément deux fois dans une
    même liste, « [[x]] · [[x]] » réduit à « [[x]] ».

Nouveau en v2 (cas vus le 24 octobre) :
  - ÉVÉNEMENT AU MÊME SLUG : si event_instances/<retirée>.md existe, ce fichier
    et son archétype evenements/<archetype>.md ne sont pas touchés (le slug y
    désigne l'événement), et le champ evenements_cites des autres fichiers est
    protégé ;
  - AUTO-RÉFÉRENCE : la fiche gardée est retirée de ses propres alliances et
    oppositions (frontmatter et sections Alliés / Opposants du corps) ;
  - CONFLIT INTERNE : une fiche qui cite la gardée à la fois en alliance et en
    opposition garde l'opposition (même règle que --resoudre-conflits).

Les alliances de la fiche retirée ne sont pas recopiées : la réciprocité
s'en charge ensuite (fix_alliances_oppositions.py --reciprocite-seule).

USAGE
    python3 generator/fusionner_doublon_instance.py --garder A --retirer B          # aperçu
    python3 generator/fusionner_doublon_instance.py --garder A --retirer B --apply  # écrit (.bak_fusion)
"""

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT = SCRIPT_DIR.parent
DOSSIERS = ["instances", "event_instances", "evenements", "entites", "articles", "geographie"]
CORBEILLE = VAULT / "_a_supprimer"
CLES_EVENEMENT = {"evenements_cites"}  # protégées quand le slug retiré est aussi un événement


def motif(slug):
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(slug) + r"(?![A-Za-z0-9_])")


def item_liste(slug):
    """Ligne de liste valant exactement slug ou [[slug]] (éventuellement entre guillemets)."""
    return re.compile(r"^\s*-\s+['\"]?(?:\[\[)?" + re.escape(slug)
                      + r"(?:\|[^\]]*)?(?:\]\])?['\"]?\s*$")


def frontmatter(texte):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", texte, re.S)
    if not m:
        return {}
    try:
        fm = yaml.safe_load(re.sub(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]", r"\1", m.group(1))) or {}
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else {}


def parcourir(texte):
    """Itère (ligne, dans_frontmatter, clé_frontmatter_courante, section_corps).
    section_corps : 'all' (Alliés/Alliances), 'opp' (Opposants/Oppositions/Rivaux) ou None."""
    lignes = texte.split("\n")
    in_fm = bool(lignes) and lignes[0].strip() == "---"
    cle, section = None, None
    for i, l in enumerate(lignes):
        if in_fm and i > 0 and l.strip() == "---":
            yield l, True, None, None
            in_fm = False
            continue
        if in_fm:
            m = re.match(r"^([A-Za-z_]\w*):", l)
            if m:
                cle = m.group(1)
            yield l, True, cle, None
            continue
        s = l.strip()
        if re.match(r"^(\*\*|#+\s)", s):
            if re.match(r"^(\*\*|#+\s*)Alli", s):
                section = "all"
            elif re.match(r"^(\*\*|#+\s*)(Oppos|Rivaux|Adversaires)", s):
                section = "opp"
            else:
                section = None
        yield l, False, None, section


def substituer(texte, m_old, garder, proteger_evenements):
    """Redirige les citations ; protège le champ evenements_cites si demandé. Retourne (texte, n)."""
    if not proteger_evenements:
        n = len(m_old.findall(texte))
        return m_old.sub(garder, texte), n
    out, n = [], 0
    for l, in_fm, cle, _ in parcourir(texte):
        if in_fm and cle in CLES_EVENEMENT:
            out.append(l)
            continue
        n += len(m_old.findall(l))
        out.append(m_old.sub(garder, l))
    return "\n".join(out), n


def retirer_items(texte, slug, cles_fm, sections):
    """Retire les lignes de liste valant slug sous les clés de frontmatter et
    sections du corps données. Retourne (texte, nb lignes retirées)."""
    item = item_liste(slug)
    out, n = [], 0
    for l, in_fm, cle, section in parcourir(texte):
        cible = (cle in cles_fm) if in_fm else (section in sections)
        if cible and item.match(l):
            n += 1
            continue
        out.append(l)
    return "\n".join(out), n


def dedoublonner(texte, garder):
    """Retire les doublons créés par la fusion. Retourne (texte, nb retirés)."""
    out, bloc, n = [], set(), 0
    for ligne in texte.split("\n"):
        if re.match(r"^\s*-\s+", ligne):
            cle = ligne.strip()
            if cle in bloc and garder in ligne:
                n += 1
                continue
            bloc.add(cle)
        else:
            bloc = set()
        out.append(ligne)
    texte = "\n".join(out)
    lien = r"\[\[" + re.escape(garder) + r"(?:\|[^\]]*)?\]\]"
    texte, k = re.subn(r"(" + lien + r")((?:\s*[·,]\s*" + lien + r")+)", r"\1", texte)
    return texte, n + k


def en_conflit(texte, garder):
    """True / False, ou None si le frontmatter est illisible."""
    fm = frontmatter(texte)
    if fm is None:
        return None
    al, op = fm.get("alliances") or [], fm.get("oppositions") or []
    return isinstance(al, list) and isinstance(op, list) and garder in al and garder in op


def main():
    ap = argparse.ArgumentParser(description="Fusionne deux instances doublons (aperçu par défaut).")
    ap.add_argument("--garder", required=True, help="slug de l'instance gardée")
    ap.add_argument("--retirer", required=True, help="slug de l'instance retirée")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon aperçu)")
    args = ap.parse_args()
    garder, retirer = args.garder.strip(), args.retirer.strip()
    if garder == retirer:
        sys.exit("✗ --garder et --retirer identiques.")

    f_garder = VAULT / "instances" / f"{garder}.md"
    f_retirer = VAULT / "instances" / f"{retirer}.md"
    for f in (f_garder, f_retirer):
        if not f.exists():
            sys.exit(f"✗ Fiche introuvable : {f.relative_to(VAULT)}")

    # Archétype de la fiche retirée : mis de côté seulement s'il ne sert à rien d'autre.
    fm_r = frontmatter(f_retirer.read_text(encoding="utf-8")) or {}
    fm_g = frontmatter(f_garder.read_text(encoding="utf-8")) or {}
    arch_r, arch_g = fm_r.get("entite"), fm_g.get("entite")
    arch_fichier, arch_autres = None, []
    if arch_r and arch_r != arch_g:
        arch_fichier = VAULT / "entites" / f"{arch_r}.md"
        motif_arch = re.compile(r"^entite:\s*['\"]?" + re.escape(str(arch_r)) + r"['\"]?\s*$", re.M)
        arch_autres = [p.name for p in sorted((VAULT / "instances").glob("*.md"))
                       if p != f_retirer and motif_arch.search(p.read_text(encoding="utf-8"))]
        if not arch_fichier.exists():
            arch_fichier = None

    # v2 — événement portant le même slug que l'instance retirée.
    evt_proteges = []
    f_evt = VAULT / "event_instances" / f"{retirer}.md"
    if f_evt.exists():
        evt_proteges.append(f_evt)
        arch_evt = (frontmatter(f_evt.read_text(encoding="utf-8")) or {}).get("archetype")
        if arch_evt and (VAULT / "evenements" / f"{arch_evt}.md").exists():
            evt_proteges.append(VAULT / "evenements" / f"{arch_evt}.md")
    collision_evt = bool(evt_proteges)

    m_old = motif(retirer)
    a_ecrire, rapport, a_trancher = {}, {}, []
    exclus = ({f_retirer.resolve()}
              | ({arch_fichier.resolve()} if arch_fichier and not arch_autres else set())
              | {p.resolve() for p in evt_proteges})
    for d in DOSSIERS:
        racine = VAULT / d
        if not racine.is_dir():
            continue
        for p in sorted(racine.rglob("*.md")):
            if p.resolve() in exclus or CORBEILLE in p.parents:
                continue
            try:
                texte = p.read_text(encoding="utf-8")
            except OSError:
                continue
            if not m_old.search(texte):
                continue
            nouveau, n = substituer(texte, m_old, garder, collision_evt)
            if not n:
                continue
            nouveau, nd = dedoublonner(nouveau, garder)
            notes = [f"{n} citation(s) redirigée(s)"] + ([f"{nd} doublon(s) retiré(s)"] if nd else [])
            etat = en_conflit(nouveau, garder)
            if etat is None:
                a_trancher.append(f"  ⚠ {p.relative_to(VAULT)} : frontmatter illisible après remplacement")
            elif etat:
                nouveau, nc = retirer_items(nouveau, garder, {"alliances"}, {"all"})
                notes.append(f"conflit résolu, opposition gardée ({nc} ligne(s) d'alliance retirée(s))")
                if en_conflit(nouveau, garder):
                    a_trancher.append(f"  ⚠ {p.relative_to(VAULT)} : conflit alliance/opposition non résolu")
            a_ecrire[p] = nouveau
            rapport[p] = notes

    # v2 — auto-référence de la fiche gardée.
    texte_g = a_ecrire.get(f_garder, f_garder.read_text(encoding="utf-8"))
    texte_g, na = retirer_items(texte_g, garder, {"alliances", "oppositions"}, {"all", "opp"})
    if na:
        a_ecrire[f_garder] = texte_g
        rapport.setdefault(f_garder, []).append(f"auto-référence retirée ({na} ligne(s))")

    # Liens vers l'archétype retiré (même slug qu'une zone ici) : comptés, jamais modifiés.
    liens_arch = 0
    if arch_r:
        m_lien = re.compile(r"\[\[" + re.escape(str(arch_r)) + r"(?:\|[^\]]*)?\]\]")
        for d in DOSSIERS:
            racine = VAULT / d
            if racine.is_dir():
                for p in racine.rglob("*.md"):
                    if p.resolve() not in exclus:
                        try:
                            liens_arch += len(m_lien.findall(p.read_text(encoding="utf-8")))
                        except OSError:
                            pass

    print(("ÉCRITURE" if args.apply else "APERÇU (rien n'est écrit)")
          + f" — fusion de {retirer} dans {garder}\n")
    print(f"Fichiers à réécrire : {len(a_ecrire)}")
    for p in sorted(a_ecrire, key=lambda x: str(x)):
        print(f"  {p.relative_to(VAULT)} : " + ", ".join(rapport[p]))
    if not a_ecrire:
        print("  (aucun)")
    if collision_evt:
        print(f"\n⚠ Un événement porte le même slug : "
              + ", ".join(str(p.relative_to(VAULT)) for p in evt_proteges)
              + " non modifié(s) ; champ evenements_cites protégé partout.")
    if a_trancher:
        print("\nÀ trancher à la main :")
        print("\n".join(a_trancher))
    print(f"\nMis de côté dans _a_supprimer/ : instances/{retirer}.md", end="")
    if arch_fichier and not arch_autres:
        print(f" + entites/{arch_r}.md")
    else:
        print()
        if arch_autres:
            print(f"  archétype entites/{arch_r}.md gardé : utilisé aussi par {', '.join(arch_autres)}")
    if liens_arch:
        print(f"  ⚠ {liens_arch} lien(s) [[{arch_r}]] dans le vault (archétype ou zone de même slug) : non modifiés")

    if not args.apply:
        print("\nRelancer avec --apply pour écrire (sauvegarde .bak_fusion de chaque fichier).")
        return

    for p, nouveau in a_ecrire.items():
        bak = p.with_name(p.name + ".bak_fusion")
        if not bak.exists():
            shutil.copy2(p, bak)
        p.write_text(nouveau, encoding="utf-8")
    dest = CORBEILLE / f"fusion_{retirer}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.move(str(f_retirer), str(dest / f_retirer.name))
    if arch_fichier and not arch_autres:
        shutil.move(str(arch_fichier), str(dest / arch_fichier.name))
    proteges = {p.resolve() for p in evt_proteges}
    restes = []
    for d in DOSSIERS:
        if not (VAULT / d).is_dir():
            continue
        for p in (VAULT / d).rglob("*.md"):
            if CORBEILLE in p.parents or p.resolve() in proteges:
                continue
            t = p.read_text(encoding="utf-8")
            if collision_evt:
                t = "\n".join(l for l, in_fm, cle, _ in parcourir(t) if not (in_fm and cle in CLES_EVENEMENT))
            if m_old.search(t):
                restes.append(p)
    print(f"\n✓ {len(a_ecrire)} fichier(s) réécrit(s), fiche(s) déplacée(s) dans {dest.relative_to(VAULT)}/")
    print(f"  Relecture : {len(restes)} citation(s) restante(s) de {retirer}" + (" ⚠" if restes else ""))
    print("  Ensuite : python3 generator/fix_alliances_oppositions.py --scenario <scénario> "
          "--reciprocite-seule --ignorer-exclus --resoudre-conflits, puis python3 generator/validate.py")


if __name__ == "__main__":
    main()
