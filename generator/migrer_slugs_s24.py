#!/usr/bin/env python3
"""
migrer_slugs_s24.py — S24, 31 oct 2026 (étape 2 : migration des données)

Met les fichiers en accord avec generator/slugs.py (étape 1) : les anciens
slugs où ø, æ, œ, ß, ł… étaient devenus « _ » sont remplacés par la forme
translittérée.

Trois tables ancien -> nouveau :
  1. entités : fiche de entites/ dont le slug (nom de fichier) est exactement
     l'ancien slug de son nom ; leurs instances (<slug>_<scénario>) suivent ;
  2. articles : champ `slug` recalculé depuis le titre ;
  3. journalistes : noms de generator/journaux.yaml.

Puis, dans tout le vault (.md .yaml .yml .json ; hors site/, .git,
_backups, _a_supprimer, .obsidian, documentation/Old…) :
  - remplacement de chaque ancien slug, mot entier (wikilinks, frontmatter,
    entites_citees, developpements, articles_lies…), y compris les slugs
    d'instance <ancien>_<scénario> ;
  - renommage des fichiers dont le nom est l'ancien slug (ou <ancien>_<scénario>).

Sauvegarde de chaque fichier touché dans _backups/migration_slugs_s24_<date>/.
Lecture seule sans --apply.

Usage (depuis la racine du vault) :
  python3 generator/migrer_slugs_s24.py           # aperçu complet
  python3 generator/migrer_slugs_s24.py --apply
"""

import argparse
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime

import yaml

RACINE = os.getcwd()
sys.path.insert(0, os.path.join(RACINE, "generator"))
try:
    from slugs import slugify as nouveau
except ImportError:
    sys.exit("generator/slugs.py introuvable : appliquer d'abord l'étape 1.")

EXCLUS = {"site", ".git", "_backups", "_a_supprimer", ".obsidian", "__pycache__",
          "node_modules", ".venv", "venv",
          "Old"}  # documentation/Old : archives (backlogs, handoffs), laissées telles quelles
EXTENSIONS = (".md", ".yaml", ".yml", ".json")
SCENARIOS = ["breakdown", "fortress_world", "new_sustainability",
             "eco_communalism", "policy_reform", "reference"]
SUFFIXE = "(?:_(?:{}))?".format("|".join(SCENARIOS))


def ancien(text):
    s = unicodedata.normalize("NFD", str(text or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def frontmatter(raw):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", raw, re.DOTALL)
    if not m:
        return None, raw
    try:
        fm = yaml.safe_load(re.sub(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]", r"\1", m.group(1)))
    except yaml.YAMLError:
        return None, raw[m.end():]
    return (fm if isinstance(fm, dict) else None), raw[m.end():]


def lire(chemin):
    try:
        return open(chemin, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return None


# ── tables ────────────────────────────────────────────────────────────────

def table_entites():
    table = {}
    dossier = os.path.join(RACINE, "entites")
    for f in sorted(os.listdir(dossier)) if os.path.isdir(dossier) else []:
        if not f.endswith(".md"):
            continue
        raw = lire(os.path.join(dossier, f))
        fm, _ = frontmatter(raw or "")
        if not fm:
            continue
        stem = f[:-3]
        for k, v in fm.items():
            if isinstance(v, str) and ("nom" in k.lower() or k.lower() == "name"):
                a, n = ancien(v), nouveau(v)
                if a != n and stem == a:
                    table[a] = n
    return table


def table_articles():
    table, alertes = {}, []
    for dossier, sous, fichiers in os.walk(os.path.join(RACINE, "articles")):
        sous[:] = [d for d in sous if d not in EXCLUS]
        for f in fichiers:
            if not f.endswith(".md"):
                continue
            chemin = os.path.join(dossier, f)
            raw = lire(chemin) or ""
            m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", raw, re.DOTALL)
            if not m:
                continue
            ms = re.search(r"^slug:\s*(\S+)\s*$", m.group(1), re.MULTILINE)
            if not ms:
                continue
            titre = ""
            for line in raw[m.end():].split("\n"):
                line = line.strip()
                if line:
                    mt = re.match(r"^\*\*(.+?)\*\*$", line)
                    titre = mt.group(1).strip() if mt else line
                    break
            a = ancien(titre)[:80].strip("_") or "article-sans-titre"
            n = nouveau(titre)[:80].strip("_") or "article-sans-titre"
            if a == n:
                continue
            if ms.group(1) != a:
                alertes.append("{} : slug {!r} ≠ attendu {!r} -- ignoré".format(
                    os.path.relpath(chemin, RACINE), ms.group(1), a))
                continue
            table[a] = n
    return table, alertes


def table_journalistes():
    table = {}
    chemin = os.path.join(RACINE, "generator", "journaux.yaml")
    if not os.path.exists(chemin):
        return table
    data = yaml.safe_load(open(chemin, encoding="utf-8")) or {}
    for scen in data.values():
        for ligne in (scen or {}).values() if isinstance(scen, dict) else []:
            zones = (ligne or {}).get("zones") or {} if isinstance(ligne, dict) else {}
            for zone in zones.values():
                for j in (zone or {}).get("journalistes") or [] if isinstance(zone, dict) else []:
                    nom = j.get("nom", "") if isinstance(j, dict) else ""
                    a, n = ancien(nom), nouveau(nom)
                    if nom and a != n:
                        table[a] = n
    return table


def fusion(*tables):
    tout = {}
    for t in tables:
        for a, n in t.items():
            if a in tout and tout[a] != n:
                sys.exit("ÉCHEC : {!r} a deux traductions ({!r}, {!r}). Rien modifié.".format(a, tout[a], n))
            tout[a] = n
    if len(set(tout.values())) != len(tout):
        sys.exit("ÉCHEC : deux anciens slugs donnent le même nouveau. Rien modifié.")
    return tout


# ── migration ─────────────────────────────────────────────────────────────

def fichiers_vault():
    for dossier, sous, fichiers in os.walk(RACINE):
        sous[:] = [d for d in sous if d not in EXCLUS]
        for f in fichiers:
            yield os.path.join(dossier, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    t_ent = table_entites()
    t_art, alertes = table_articles()
    t_jou = table_journalistes()
    for nom, t in (("Entités", t_ent), ("Articles", t_art), ("Journalistes", t_jou)):
        print("{} ({}) :".format(nom, len(t)))
        for a, n in sorted(t.items()):
            print("   {}  ->  {}".format(a, n))
    for al in alertes:
        print("   ⚠ " + al)
    table = fusion(t_ent, t_art, t_jou)
    if not table:
        print("\nRien à migrer.")
        return

    # entités : l'ancien slug et ses instances <ancien>_<scénario> ; autres : mot entier
    motifs = []
    for a, n in table.items():
        suffixe = SUFFIXE if a in t_ent else ""
        motifs.append((re.compile(r"(?<![a-z0-9_]){}(?={}(?![a-z0-9_]))".format(re.escape(a), suffixe)), n))

    contenus, renommages, total = {}, [], 0
    print("\nRemplacements :")
    for chemin in fichiers_vault():
        if chemin.endswith(EXTENSIONS):
            txt = lire(chemin)
            if txt is not None:
                nouveau_txt, nb = txt, 0
                for motif, n in motifs:
                    nouveau_txt, k = motif.subn(n, nouveau_txt)
                    nb += k
                if nb:
                    contenus[chemin] = nouveau_txt
                    total += nb
                    print("   {:4d}  {}".format(nb, os.path.relpath(chemin, RACINE)))
        base, ext = os.path.splitext(os.path.basename(chemin))
        for a, n in t_ent.items():
            for suf in [""] + ["_" + s for s in SCENARIOS]:
                if base == a + suf:
                    cible = os.path.join(os.path.dirname(chemin), n + suf + ext)
                    if os.path.exists(cible):
                        sys.exit("ÉCHEC : {} existe déjà. Rien modifié.".format(os.path.relpath(cible, RACINE)))
                    renommages.append((chemin, cible))
    print("   = {} remplacement(s) dans {} fichier(s)".format(total, len(contenus)))
    print("\nRenommages ({}) :".format(len(renommages)))
    for s, c in renommages:
        print("   {}  ->  {}".format(os.path.relpath(s, RACINE), os.path.basename(c)))

    if not args.apply:
        print("\nAperçu seulement. Relancer avec --apply.")
        return

    sauvegarde = os.path.join(RACINE, "_backups",
                              "migration_slugs_s24_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    for chemin in set(contenus) | {s for s, _ in renommages}:
        dest = os.path.join(sauvegarde, os.path.relpath(chemin, RACINE))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(chemin, dest)
    for chemin, txt in contenus.items():
        open(chemin, "w", encoding="utf-8").write(txt)
    for s, c in renommages:
        os.rename(s, c)
    print("\nAppliqué. Sauvegardes : {}".format(os.path.relpath(sauvegarde, RACINE)))
    print("Ensuite : validate.py, puis chapos_revues.py et publier_site.sh.")


if __name__ == "__main__":
    main()
