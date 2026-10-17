#!/usr/bin/env python3
"""
fusionner_doublon_instance.py — Ourrassol 2098 (S24, 13 octobre 2026)
====================================================================

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
Signalé sans correction : l'entité gardée à la fois en alliance et en
opposition d'une même fiche.

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


def motif(slug):
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(slug) + r"(?![A-Za-z0-9_])")


def frontmatter(texte):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", texte, re.S)
    if not m:
        return {}
    try:
        fm = yaml.safe_load(re.sub(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]", r"\1", m.group(1))) or {}
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else {}


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


def conflits(texte, garder):
    fm = frontmatter(texte)
    if fm is None:
        return ["frontmatter illisible après remplacement"]
    al, op = fm.get("alliances") or [], fm.get("oppositions") or []
    if isinstance(al, list) and isinstance(op, list) and garder in al and garder in op:
        return [f"{garder} à la fois dans alliances et oppositions"]
    return []


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

    m_old = motif(retirer)
    a_ecrire, rapport, conflits_tot = [], [], []
    exclus = {f_retirer.resolve()} | ({arch_fichier.resolve()} if arch_fichier and not arch_autres else set())
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
            n = len(m_old.findall(texte))
            if not n:
                continue
            nouveau = m_old.sub(garder, texte)
            nouveau, nd = dedoublonner(nouveau, garder)
            conf = conflits(nouveau, garder)
            a_ecrire.append((p, nouveau))
            rel = p.relative_to(VAULT)
            rapport.append(f"  {rel} : {n} citation(s) redirigée(s)" + (f", {nd} doublon(s) retiré(s)" if nd else ""))
            conflits_tot += [f"  ⚠ {rel} : {c}" for c in conf]

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
    print("\n".join(rapport) or "  (aucun)")
    if conflits_tot:
        print("\nÀ trancher à la main :")
        print("\n".join(conflits_tot))
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

    for p, nouveau in a_ecrire:
        bak = p.with_name(p.name + ".bak_fusion")
        if not bak.exists():
            shutil.copy2(p, bak)
        p.write_text(nouveau, encoding="utf-8")
    dest = CORBEILLE / f"fusion_{retirer}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.move(str(f_retirer), str(dest / f_retirer.name))
    if arch_fichier and not arch_autres:
        shutil.move(str(arch_fichier), str(dest / arch_fichier.name))
    restes = [p for d in DOSSIERS if (VAULT / d).is_dir() for p in (VAULT / d).rglob("*.md")
              if CORBEILLE not in p.parents and m_old.search(p.read_text(encoding="utf-8"))]
    print(f"\n✓ {len(a_ecrire)} fichier(s) réécrit(s), fiche(s) déplacée(s) dans {dest.relative_to(VAULT)}/")
    print(f"  Relecture : {len(restes)} citation(s) restante(s) de {retirer}" + (" ⚠" if restes else ""))
    print("  Ensuite : python3 generator/fix_alliances_oppositions.py --scenario <scénario> "
          "--reciprocite-seule --ignorer-exclus (simulation d'abord), puis python3 generator/validate.py")


if __name__ == "__main__":
    main()
